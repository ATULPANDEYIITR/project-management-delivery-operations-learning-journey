DROP SCHEMA IF EXISTS project_governance CASCADE;
CREATE SCHEMA project_governance;

SET search_path TO project_governance, public;

CREATE TYPE resource_type AS ENUM (
    'engineer',
    'reviewer',
    'automation'
);

CREATE TYPE pr_state AS ENUM (
    'draft',
    'open',
    'closed',
    'merged'
);

CREATE TYPE review_state AS ENUM (
    'commented',
    'approved',
    'changes_requested',
    'dismissed'
);

CREATE TYPE merge_strategy AS ENUM (
    'merge',
    'squash',
    'rebase'
);

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE resources (
    resource_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resource_key TEXT NOT NULL UNIQUE,
    resource_type resource_type NOT NULL,
    capacity_hours NUMERIC(10,2) NOT NULL CHECK (capacity_hours > 0),
    hourly_cost NUMERIC(12,2) NOT NULL CHECK (hourly_cost >= 0),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE project_allocations (
    allocation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    resource_id BIGINT NOT NULL REFERENCES resources(resource_id),
    hours NUMERIC(10,2) NOT NULL CHECK (hours > 0),
    purpose TEXT NOT NULL,
    allocated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    head_sha TEXT,
    UNIQUE (repository_id, name)
);

CREATE TABLE commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    sha TEXT NOT NULL UNIQUE CHECK (length(sha) >= 7),
    author TEXT NOT NULL,
    message TEXT NOT NULL CHECK (length(trim(message)) > 0),
    parent_sha TEXT,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    number INTEGER NOT NULL CHECK (number > 0),
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    author TEXT NOT NULL,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    state pr_state NOT NULL DEFAULT 'open',
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    base_head_sha TEXT,
    source_head_sha TEXT,
    base_synchronized BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CHECK (source_branch_id <> target_branch_id)
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id),
    sequence_no INTEGER NOT NULL CHECK (sequence_no > 0),
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, sequence_no)
);

CREATE TABLE reviewers (
    reviewer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES reviewers(reviewer_id),
    state review_state NOT NULL,
    reviewed_commit_sha TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER CHECK (line_number > 0),
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    duration_seconds NUMERIC(12,3)
        CHECK (duration_seconds >= 0),
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL CHECK (required_reviews >= 0),
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    allow_admin_bypass BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name)
);

CREATE TABLE approval_requirements (
    requirement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id)
        ON DELETE CASCADE,
    requirement_name TEXT NOT NULL,
    minimum_count INTEGER NOT NULL CHECK (minimum_count > 0),
    UNIQUE (policy_id, requirement_name)
);

CREATE TABLE merges (
    merge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id),
    strategy merge_strategy NOT NULL,
    merged_by TEXT NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    merge_sha TEXT NOT NULL UNIQUE
);

CREATE INDEX idx_pr_repository_state
    ON pull_requests(repository_id, state);

CREATE INDEX idx_reviews_pr_state
    ON reviews(pull_request_id, state);

CREATE INDEX idx_comments_review_resolution
    ON review_comments(review_id, resolved);

CREATE INDEX idx_status_checks_pr_name
    ON status_checks(pull_request_id, check_name);

CREATE INDEX idx_allocations_repository_resource
    ON project_allocations(repository_id, resource_id);

CREATE OR REPLACE FUNCTION enforce_resource_capacity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    capacity NUMERIC(10,2);
    allocated NUMERIC(10,2);
BEGIN
    SELECT capacity_hours
    INTO capacity
    FROM resources
    WHERE resource_id = NEW.resource_id
      AND active = TRUE;

    IF capacity IS NULL THEN
        RAISE EXCEPTION 'Resource % does not exist or is inactive',
            NEW.resource_id;
    END IF;

    SELECT COALESCE(SUM(hours), 0)
    INTO allocated
    FROM project_allocations
    WHERE resource_id = NEW.resource_id
      AND allocation_id <> COALESCE(NEW.allocation_id, -1);

    IF allocated + NEW.hours > capacity THEN
        RAISE EXCEPTION
            'Resource % exceeds capacity: %.2f > %.2f hours',
            NEW.resource_id,
            allocated + NEW.hours,
            capacity;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_resource_capacity
BEFORE INSERT OR UPDATE ON project_allocations
FOR EACH ROW
EXECUTE FUNCTION enforce_resource_capacity();

CREATE OR REPLACE FUNCTION prevent_invalid_self_approval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    pr_author TEXT;
    reviewer_name TEXT;
BEGIN
    SELECT author
    INTO pr_author
    FROM pull_requests
    WHERE pull_request_id = NEW.pull_request_id;

    SELECT username
    INTO reviewer_name
    FROM reviewers
    WHERE reviewer_id = NEW.reviewer_id;

    IF reviewer_name = pr_author
       AND NEW.state = 'approved' THEN
        RAISE EXCEPTION 'Pull request authors cannot approve their own PR';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_no_self_approval
BEFORE INSERT OR UPDATE ON reviews
FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_self_approval();

CREATE OR REPLACE FUNCTION calculate_merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    approvals INTEGER,
    required_approvals INTEGER,
    required_checks_passed BOOLEAN,
    unresolved_comments INTEGER,
    base_synchronized BOOLEAN,
    reasons TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    pr_state_value pr_state;
    draft_value BOOLEAN;
    policy_branch BIGINT;
    required_check_count INTEGER;
    passed_check_count INTEGER;
    approval_count INTEGER;
    required_approval_count INTEGER;
    unresolved_count INTEGER;
    base_ok BOOLEAN;
    reason_list TEXT[] := ARRAY[]::TEXT[];
BEGIN
    SELECT
        pr.state,
        pr.is_draft,
        pr.target_branch_id,
        pr.base_synchronized
    INTO
        pr_state_value,
        draft_value,
        policy_branch,
        base_ok
    FROM pull_requests pr
    WHERE pr.pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown pull request %', p_pull_request_id;
    END IF;

    SELECT COALESCE(required_reviews, 0)
    INTO required_approval_count
    FROM branch_protection_policies
    WHERE branch_id = policy_branch;

    required_approval_count :=
        COALESCE(required_approval_count, 0);

    SELECT COUNT(DISTINCT r.reviewer_id)
    INTO approval_count
    FROM reviews r
    WHERE r.pull_request_id = p_pull_request_id
      AND r.state = 'approved'
      AND r.reviewed_commit_sha = (
          SELECT source_head_sha
          FROM pull_requests
          WHERE pull_request_id = p_pull_request_id
      )
      AND base_ok;

    SELECT COUNT(*)
    INTO required_check_count
    FROM required_status_checks rsc
    JOIN branch_protection_policies bpp
      ON bpp.policy_id = rsc.policy_id
    WHERE bpp.branch_id = policy_branch;

    SELECT COUNT(*)
    INTO passed_check_count
    FROM required_status_checks rsc
    JOIN branch_protection_policies bpp
      ON bpp.policy_id = rsc.policy_id
    JOIN status_checks sc
      ON sc.pull_request_id = p_pull_request_id
     AND sc.check_name = rsc.check_name
     AND sc.passed = TRUE
    WHERE bpp.branch_id = policy_branch;

    SELECT COUNT(*)
    INTO unresolved_count
    FROM review_comments rc
    JOIN reviews r ON r.review_id = rc.review_id
    WHERE r.pull_request_id = p_pull_request_id
      AND rc.resolved = FALSE;

    IF pr_state_value <> 'open' THEN
        reason_list := array_append(reason_list, 'PR is not open');
    END IF;

    IF draft_value THEN
        reason_list := array_append(reason_list, 'PR is a draft');
    END IF;

    IF approval_count < required_approval_count THEN
        reason_list := array_append(
            reason_list,
            'Required approvals are missing'
        );
    END IF;

    IF passed_check_count < required_check_count THEN
        reason_list := array_append(
            reason_list,
            'Required status checks are not passing'
        );
    END IF;

    IF unresolved_count > 0 THEN
        reason_list := array_append(
            reason_list,
            'Unresolved review conversations remain'
        );
    END IF;

    IF NOT base_ok THEN
        reason_list := array_append(
            reason_list,
            'Base branch is stale'
        );
    END IF;

    RETURN QUERY
    SELECT
        cardinality(reason_list) = 0,
        approval_count,
        required_approval_count,
        passed_check_count = required_check_count,
        unresolved_count,
        base_ok,
        reason_list;
END;
$$;

CREATE OR REPLACE FUNCTION mark_pull_request_merged(
    p_pull_request_id BIGINT,
    p_strategy merge_strategy,
    p_merged_by TEXT,
    p_merge_sha TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    eligibility RECORD;
BEGIN
    SELECT *
    INTO eligibility
    FROM calculate_merge_eligibility(p_pull_request_id);

    IF NOT eligibility.eligible THEN
        RAISE EXCEPTION
            'Pull request % cannot be merged: %',
            p_pull_request_id,
            array_to_string(eligibility.reasons, '; ');
    END IF;

    UPDATE pull_requests
    SET state = 'merged',
        merged_at = now()
    WHERE pull_request_id = p_pull_request_id;

    INSERT INTO merges (
        pull_request_id,
        strategy,
        merged_by,
        merge_sha
    )
    VALUES (
        p_pull_request_id,
        p_strategy,
        p_merged_by,
        p_merge_sha
    );
END;
$$;

CREATE VIEW resource_utilization AS
SELECT
    r.resource_id,
    r.resource_key,
    r.resource_type,
    r.capacity_hours,
    COALESCE(SUM(pa.hours), 0) AS allocated_hours,
    r.capacity_hours -
        COALESCE(SUM(pa.hours), 0) AS remaining_hours,
    ROUND(
        COALESCE(SUM(pa.hours), 0) / r.capacity_hours * 100,
        2
    ) AS utilization_percent,
    ROUND(
        COALESCE(SUM(pa.hours), 0) * r.hourly_cost,
        2
    ) AS allocated_cost
FROM resources r
LEFT JOIN project_allocations pa
    ON pa.resource_id = r.resource_id
GROUP BY
    r.resource_id,
    r.resource_key,
    r.resource_type,
    r.capacity_hours,
    r.hourly_cost;

CREATE VIEW pull_request_governance_report AS
SELECT
    pr.pull_request_id,
    repo.name AS repository,
    pr.number,
    pr.title,
    pr.state,
    pr.author,
    pr.source_head_sha,
    pr.base_head_sha,
    e.eligible,
    e.approvals,
    e.required_approvals,
    e.required_checks_passed,
    e.unresolved_comments,
    e.base_synchronized,
    e.reasons
FROM pull_requests pr
JOIN repositories repo
    ON repo.repository_id = pr.repository_id
CROSS JOIN LATERAL
    calculate_merge_eligibility(pr.pull_request_id) e;

INSERT INTO repositories (name)
VALUES ('project-resource-manager');

INSERT INTO resources (
    resource_key,
    resource_type,
    capacity_hours,
    hourly_cost
)
VALUES
    ('engineer-01', 'engineer', 32, 85),
    ('reviewer-01', 'reviewer', 16, 110),
    ('ci-01', 'automation', 20, 20);

INSERT INTO branches (
    repository_id,
    name,
    protected
)
SELECT repository_id, 'main', TRUE
FROM repositories
WHERE name = 'project-resource-manager';

INSERT INTO branches (
    repository_id,
    name,
    protected
)
SELECT repository_id, 'feature/resource-policy', FALSE
FROM repositories
WHERE name = 'project-resource-manager';

INSERT INTO branch_protection_policies (
    branch_id,
    required_reviews,
    require_conversation_resolution,
    require_linear_history,
    allow_direct_push,
    allow_force_push,
    allow_branch_deletion,
    allow_admin_bypass
)
SELECT
    branch_id,
    1,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    FALSE
FROM branches
WHERE name = 'main';

INSERT INTO required_status_checks (
    policy_id,
    check_name
)
SELECT
    policy_id,
    check_name
FROM branch_protection_policies,
LATERAL (
    VALUES ('unit-tests'), ('security-scan')
) AS required(check_name);

INSERT INTO approval_requirements (
    policy_id,
    requirement_name,
    minimum_count
)
SELECT
    policy_id,
    'independent-review',
    1
FROM branch_protection_policies;

INSERT INTO reviewers (username)
VALUES
    ('reviewer-01'),
    ('reviewer-02');

INSERT INTO commits (
    branch_id,
    sha,
    author,
    message,
    parent_sha
)
SELECT
    b.branch_id,
    'abc1234',
    'engineer-01',
    'Add resource capacity rules',
    NULL
FROM branches b
WHERE b.name = 'feature/resource-policy';

INSERT INTO commits (
    branch_id,
    sha,
    author,
    message,
    parent_sha
)
SELECT
    b.branch_id,
    'def5678',
    'engineer-01',
    'Enforce project allocation limits',
    'abc1234'
FROM branches b
WHERE b.name = 'feature/resource-policy';

UPDATE branches
SET head_sha = 'abc1234'
WHERE name = 'main';

UPDATE branches
SET head_sha = 'def5678'
WHERE name = 'feature/resource-policy';

INSERT INTO pull_requests (
    repository_id,
    number,
    source_branch_id,
    target_branch_id,
    author,
    title,
    state,
    is_draft,
    base_head_sha,
    source_head_sha
)
SELECT
    r.repository_id,
    1,
    source.branch_id,
    target.branch_id,
    'engineer-01',
    'Implement resource allocation governance',
    'open',
    FALSE,
    target.head_sha,
    source.head_sha
FROM repositories r
JOIN branches source
    ON source.repository_id = r.repository_id
   AND source.name = 'feature/resource-policy'
JOIN branches target
    ON target.repository_id = r.repository_id
   AND target.name = 'main'
WHERE r.name = 'project-resource-manager';

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_id,
    sequence_no
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    CASE c.sha
        WHEN 'abc1234' THEN 1
        WHEN 'def5678' THEN 2
    END
FROM pull_requests pr
JOIN commits c
    ON c.sha IN ('abc1234', 'def5678')
WHERE pr.number = 1;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    reviewed_commit_sha
)
SELECT
    pr.pull_request_id,
    r.reviewer_id,
    'changes_requested',
    'def5678'
FROM pull_requests pr
JOIN reviewers r
    ON r.username = 'reviewer-01'
WHERE pr.number = 1;

INSERT INTO review_comments (
    review_id,
    file_path,
    line_number,
    body,
    resolved
)
SELECT
    review_id,
    'resource-service.py',
    72,
    'Reject allocation requests that exceed resource capacity.',
    TRUE
FROM reviews
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE number = 1
);

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    reviewed_commit_sha
)
SELECT
    pr.pull_request_id,
    r.reviewer_id,
    'approved',
    'def5678'
FROM pull_requests pr
JOIN reviewers r
    ON r.username = 'reviewer-01'
WHERE pr.number = 1;

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    passed,
    duration_seconds
)
SELECT
    pull_request_id,
    'unit-tests',
    TRUE,
    42.5
FROM pull_requests
WHERE number = 1;

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    passed,
    duration_seconds
)
SELECT
    pull_request_id,
    'security-scan',
    TRUE,
    67.2
FROM pull_requests
WHERE number = 1;

INSERT INTO project_allocations (
    repository_id,
    resource_id,
    hours,
    purpose
)
SELECT
    repo.repository_id,
    resource.resource_id,
    allocation.hours,
    allocation.purpose
FROM repositories repo
JOIN resources resource
    ON resource.resource_key = allocation.resource_key
CROSS JOIN (
    VALUES
        ('engineer-01', 13.0, 'Implementation'),
        ('reviewer-01', 4.0, 'Code review'),
        ('ci-01', 2.0, 'Automated validation')
) AS allocation(resource_key, hours, purpose)
WHERE repo.name = 'project-resource-manager';

SELECT *
FROM resource_utilization
ORDER BY resource_key;

SELECT *
FROM pull_request_governance_report
WHERE number = 1;

SELECT
    repo.name,
    pr.number,
    pr.title,
    review.reviewer_id,
    review.state,
    review.reviewed_commit_sha
FROM pull_requests pr
JOIN repositories repo
    ON repo.repository_id = pr.repository_id
JOIN reviews review
    ON review.pull_request_id = pr.pull_request_id
ORDER BY pr.number, review.submitted_at;

SELECT
    pr.number,
    sc.check_name,
    sc.passed,
    sc.duration_seconds
FROM pull_requests pr
JOIN status_checks sc
    ON sc.pull_request_id = pr.pull_request_id
WHERE pr.number = 1
ORDER BY sc.check_name;

BEGIN;

SELECT *
FROM calculate_merge_eligibility(
    (SELECT pull_request_id
     FROM pull_requests
     WHERE number = 1)
);

SELECT mark_pull_request_merged(
    (SELECT pull_request_id
     FROM pull_requests
     WHERE number = 1),
    'squash',
    'release-manager',
    'squash-pr-1'
);

COMMIT;

SELECT
    number,
    state,
    merged_at
FROM pull_requests
WHERE number = 1;

SELECT
    m.pull_request_id,
    m.strategy,
    m.merged_by,
    m.merge_sha,
    m.merged_at
FROM merges m;
