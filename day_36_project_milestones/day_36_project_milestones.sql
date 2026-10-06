DROP SCHEMA IF EXISTS project_milestones CASCADE;

CREATE SCHEMA project_milestones;

SET search_path TO project_milestones;

CREATE TYPE milestone_status AS ENUM (
    'planned',
    'active',
    'completed',
    'blocked',
    'cancelled'
);

CREATE TYPE pull_request_status AS ENUM (
    'open',
    'closed',
    'merged'
);

CREATE TYPE review_state AS ENUM (
    'approved',
    'changes_requested',
    'commented'
);

CREATE TYPE event_type AS ENUM (
    'project_started',
    'requirement_approved',
    'design_completed',
    'development_started',
    'pull_request_opened',
    'code_review_completed',
    'approval_granted',
    'status_check_failed',
    'status_check_passed',
    'merged',
    'released',
    'milestone_completed',
    'milestone_blocked'
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    project_key VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    owner_name VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    CHECK (status IN ('planned', 'active', 'completed', 'cancelled'))
);

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    repository_name VARCHAR(200) NOT NULL,
    default_branch VARCHAR(120) NOT NULL DEFAULT 'main',
    UNIQUE (project_id, repository_name)
);

CREATE TABLE repository_branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    branch_name VARCHAR(120) NOT NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE project_milestones (
    milestone_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    milestone_key VARCHAR(50) NOT NULL,
    milestone_name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    target_date DATE NOT NULL,
    importance SMALLINT NOT NULL DEFAULT 3,
    status milestone_status NOT NULL DEFAULT 'planned',
    completed_at TIMESTAMPTZ,
    UNIQUE (project_id, milestone_key),
    CHECK (importance BETWEEN 1 AND 5),
    CHECK (
        (status = 'completed' AND completed_at IS NOT NULL)
        OR
        (status <> 'completed' AND completed_at IS NULL)
    )
);

CREATE TABLE milestone_dependencies (
    milestone_id BIGINT NOT NULL REFERENCES project_milestones(milestone_id),
    dependency_milestone_id BIGINT NOT NULL REFERENCES project_milestones(milestone_id),
    PRIMARY KEY (milestone_id, dependency_milestone_id),
    CHECK (milestone_id <> dependency_milestone_id)
);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    commit_hash CHAR(40) NOT NULL UNIQUE,
    author_name VARCHAR(120) NOT NULL,
    commit_message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    number INTEGER NOT NULL,
    source_branch_id BIGINT NOT NULL REFERENCES repository_branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES repository_branches(branch_id),
    milestone_id BIGINT REFERENCES project_milestones(milestone_id),
    author_name VARCHAR(120) NOT NULL,
    title VARCHAR(250) NOT NULL,
    description TEXT NOT NULL,
    status pull_request_status NOT NULL DEFAULT 'open',
    is_draft BOOLEAN NOT NULL DEFAULT TRUE,
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    merged_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (
        (status = 'merged' AND merged_at IS NOT NULL)
        OR
        (status <> 'merged')
    )
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id),
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id),
    sequence_number INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, sequence_number),
    CHECK (sequence_number > 0)
);

CREATE TABLE reviewers (
    reviewer_id BIGSERIAL PRIMARY KEY,
    reviewer_name VARCHAR(120) NOT NULL UNIQUE,
    role_name VARCHAR(120) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id),
    reviewer_id BIGINT NOT NULL REFERENCES reviewers(reviewer_id),
    state review_state NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dismissed_at TIMESTAMPTZ,
    dismissal_reason TEXT,
    UNIQUE (pull_request_id, reviewer_id, submitted_at),
    CHECK (
        (dismissed_at IS NULL AND dismissal_reason IS NULL)
        OR
        (dismissed_at IS NOT NULL AND dismissal_reason IS NOT NULL)
    )
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id),
    file_path TEXT NOT NULL,
    line_number INTEGER,
    comment_body TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,
    CHECK (line_number IS NULL OR line_number > 0),
    CHECK (
        (is_resolved = FALSE AND resolved_at IS NULL)
        OR
        (is_resolved = TRUE AND resolved_at IS NOT NULL)
    )
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id),
    check_name VARCHAR(150) NOT NULL,
    passed BOOLEAN NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES repository_branches(branch_id),
    required_approvals INTEGER NOT NULL DEFAULT 1,
    require_status_checks BOOLEAN NOT NULL DEFAULT TRUE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_direct_pushes BOOLEAN NOT NULL DEFAULT TRUE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (required_approvals >= 0)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL REFERENCES branch_protection_policies(policy_id),
    check_name VARCHAR(150) NOT NULL,
    PRIMARY KEY (policy_id, check_name)
);

CREATE TABLE project_events (
    event_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    milestone_id BIGINT REFERENCES project_milestones(milestone_id),
    pull_request_id BIGINT REFERENCES pull_requests(pull_request_id),
    event_type event_type NOT NULL,
    event_title VARCHAR(250) NOT NULL,
    actor_name VARCHAR(120) NOT NULL,
    event_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_project_events_milestone_time
    ON project_events (milestone_id, occurred_at DESC);

CREATE INDEX idx_project_events_project_time
    ON project_events (project_id, occurred_at DESC);

CREATE INDEX idx_pull_requests_milestone_status
    ON pull_requests (milestone_id, status);

CREATE INDEX idx_reviews_pull_request_state
    ON reviews (pull_request_id, state);

CREATE INDEX idx_review_comments_review_resolution
    ON review_comments (review_id, is_resolved);

CREATE INDEX idx_status_checks_pull_request
    ON status_checks (pull_request_id, check_name, passed);

CREATE INDEX idx_milestones_target_status
    ON project_milestones (target_date, status);

CREATE VIEW important_project_events AS
SELECT
    e.event_id,
    p.project_key,
    p.project_name,
    m.milestone_key,
    m.milestone_name,
    e.event_type,
    e.event_title,
    e.actor_name,
    e.occurred_at,
    e.event_details
FROM project_events e
JOIN projects p
    ON p.project_id = e.project_id
LEFT JOIN project_milestones m
    ON m.milestone_id = e.milestone_id
WHERE e.event_type IN (
    'project_started',
    'requirement_approved',
    'design_completed',
    'pull_request_opened',
    'approval_granted',
    'status_check_failed',
    'status_check_passed',
    'merged',
    'released',
    'milestone_completed',
    'milestone_blocked'
);

CREATE VIEW pull_request_review_state AS
SELECT
    pr.pull_request_id,
    pr.repository_id,
    pr.number,
    pr.title,
    pr.milestone_id,
    pr.status,
    pr.is_draft,
    pr.has_conflicts,
    COUNT(DISTINCT CASE
        WHEN r.state = 'approved'
         AND r.dismissed_at IS NULL
         AND NOT EXISTS (
             SELECT 1
             FROM review_comments rc
             WHERE rc.review_id = r.review_id
               AND rc.is_resolved = FALSE
         )
        THEN r.reviewer_id
    END) AS active_approvals,
    COUNT(DISTINCT CASE
        WHEN r.state = 'changes_requested'
         AND r.dismissed_at IS NULL
        THEN r.reviewer_id
    END) AS reviewers_requesting_changes,
    COUNT(DISTINCT rc.comment_id) FILTER (
        WHERE rc.is_resolved = FALSE
    ) AS unresolved_comments
FROM pull_requests pr
LEFT JOIN reviews r
    ON r.pull_request_id = pr.pull_request_id
LEFT JOIN review_comments rc
    ON rc.review_id = r.review_id
GROUP BY
    pr.pull_request_id,
    pr.repository_id,
    pr.number,
    pr.title,
    pr.milestone_id,
    pr.status,
    pr.is_draft,
    pr.has_conflicts;

CREATE VIEW milestone_progress AS
SELECT
    m.milestone_id,
    p.project_key,
    m.milestone_key,
    m.milestone_name,
    m.status,
    m.target_date,
    m.importance,
    COUNT(DISTINCT e.event_id) AS event_count,
    COUNT(DISTINCT pr.pull_request_id) AS pull_request_count,
    COUNT(DISTINCT pr.pull_request_id)
        FILTER (WHERE pr.status = 'merged') AS merged_pull_request_count,
    MAX(e.occurred_at) AS latest_event_at
FROM project_milestones m
JOIN projects p
    ON p.project_id = m.project_id
LEFT JOIN project_events e
    ON e.milestone_id = m.milestone_id
LEFT JOIN pull_requests pr
    ON pr.milestone_id = m.milestone_id
GROUP BY
    m.milestone_id,
    p.project_key,
    m.milestone_key,
    m.milestone_name,
    m.status,
    m.target_date,
    m.importance;

CREATE OR REPLACE FUNCTION prevent_invalid_milestone_completion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'completed' THEN
        IF EXISTS (
            SELECT 1
            FROM pull_requests pr
            WHERE pr.milestone_id = NEW.milestone_id
              AND pr.status <> 'merged'
        ) THEN
            RAISE EXCEPTION
                'Milestone % cannot be completed while related Pull Requests remain unmerged',
                NEW.milestone_id;
        END IF;

        IF NEW.completed_at IS NULL THEN
            NEW.completed_at := CURRENT_TIMESTAMP;
        END IF;
    ELSE
        NEW.completed_at := NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_milestone_completion
BEFORE INSERT OR UPDATE OF status, completed_at
ON project_milestones
FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_milestone_completion();

CREATE OR REPLACE FUNCTION evaluate_pull_request_merge(
    requested_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE sql
AS $$
WITH pr AS (
    SELECT
        pr.pull_request_id,
        pr.target_branch_id,
        pr.is_draft,
        pr.has_conflicts
    FROM pull_requests pr
    WHERE pr.pull_request_id = requested_pull_request_id
),
policy AS (
    SELECT
        bp.*,
        b.branch_id
    FROM branch_protection_policies bp
    JOIN repository_branches b
        ON b.branch_id = bp.branch_id
    WHERE b.branch_id = (SELECT target_branch_id FROM pr)
),
approval_count AS (
    SELECT
        r.pull_request_id,
        COUNT(DISTINCT r.reviewer_id) AS approvals
    FROM reviews r
    WHERE r.pull_request_id = requested_pull_request_id
      AND r.state = 'approved'
      AND r.dismissed_at IS NULL
      AND NOT EXISTS (
          SELECT 1
          FROM review_comments rc
          WHERE rc.review_id = r.review_id
            AND rc.is_resolved = FALSE
      )
    GROUP BY r.pull_request_id
),
unresolved AS (
    SELECT
        COUNT(*) AS count
    FROM review_comments rc
    JOIN reviews r
        ON r.review_id = rc.review_id
    WHERE r.pull_request_id = requested_pull_request_id
      AND rc.is_resolved = FALSE
),
failed_required_checks AS (
    SELECT COUNT(*) AS count
    FROM required_status_checks required
    JOIN policy
        ON policy.policy_id = required.policy_id
    LEFT JOIN status_checks actual
        ON actual.pull_request_id = requested_pull_request_id
       AND actual.check_name = required.check_name
       AND actual.passed = TRUE
    WHERE actual.status_check_id IS NULL
),
change_requests AS (
    SELECT COUNT(*) AS count
    FROM reviews
    WHERE pull_request_id = requested_pull_request_id
      AND state = 'changes_requested'
      AND dismissed_at IS NULL
)
SELECT
    FALSE,
    'Pull Request is still a draft'
FROM pr
WHERE pr.is_draft

UNION ALL

SELECT
    FALSE,
    'Pull Request contains merge conflicts'
FROM pr
WHERE pr.has_conflicts

UNION ALL

SELECT
    FALSE,
    'Required approvals have not been obtained'
FROM pr
CROSS JOIN policy
LEFT JOIN approval_count a
    ON a.pull_request_id = pr.pull_request_id
WHERE COALESCE(a.approvals, 0) < policy.required_approvals

UNION ALL

SELECT
    FALSE,
    'A reviewer has requested changes'
FROM change_requests
WHERE count > 0

UNION ALL

SELECT
    FALSE,
    'Required status checks have not passed'
FROM policy
CROSS JOIN failed_required_checks
WHERE policy.require_status_checks
  AND failed_required_checks.count > 0

UNION ALL

SELECT
    FALSE,
    'Review conversations remain unresolved'
FROM policy
CROSS JOIN unresolved
WHERE policy.require_conversation_resolution
  AND unresolved.count > 0

UNION ALL

SELECT
    TRUE,
    'All configured merge conditions are satisfied'
WHERE NOT EXISTS (
    SELECT 1
    FROM (
        SELECT * FROM evaluate_pull_request_merge(requested_pull_request_id)
    ) existing_failures
    WHERE existing_failures.eligible = FALSE
);
$$;

INSERT INTO projects (
    project_key,
    project_name,
    owner_name
)
VALUES (
    'BILLING-204',
    'Enterprise Billing Modernization',
    'Program Management Office'
);

INSERT INTO repositories (
    project_id,
    repository_name,
    default_branch
)
SELECT
    project_id,
    'enterprise-billing-service',
    'main'
FROM projects
WHERE project_key = 'BILLING-204';

INSERT INTO repository_branches (
    repository_id,
    branch_name,
    is_protected,
    is_default
)
SELECT
    repository_id,
    'main',
    TRUE,
    TRUE
FROM repositories
WHERE repository_name = 'enterprise-billing-service';

INSERT INTO repository_branches (
    repository_id,
    branch_name,
    is_protected,
    is_default
)
SELECT
    repository_id,
    'feature/billing-core',
    FALSE,
    FALSE
FROM repositories
WHERE repository_name = 'enterprise-billing-service';

INSERT INTO project_milestones (
    project_id,
    milestone_key,
    milestone_name,
    description,
    target_date,
    importance,
    status
)
SELECT
    project_id,
    'M1',
    'Requirements Baseline',
    'Approved billing requirements and acceptance criteria.',
    CURRENT_DATE + 7,
    5,
    'completed'
FROM projects
WHERE project_key = 'BILLING-204';

INSERT INTO project_milestones (
    project_id,
    milestone_key,
    milestone_name,
    description,
    target_date,
    importance,
    status
)
SELECT
    project_id,
    'M2',
    'Billing Core Implementation',
    'Reviewed and tested billing implementation.',
    CURRENT_DATE + 30,
    5,
    'active'
FROM projects
WHERE project_key = 'BILLING-204';

INSERT INTO project_milestones (
    project_id,
    milestone_key,
    milestone_name,
    description,
    target_date,
    importance,
    status
)
SELECT
    project_id,
    'M3',
    'Production Release',
    'Production deployment after merge governance requirements are satisfied.',
    CURRENT_DATE + 45,
    5,
    'planned'
FROM projects
WHERE project_key = 'BILLING-204';

INSERT INTO milestone_dependencies (
    milestone_id,
    dependency_milestone_id
)
SELECT
    child.milestone_id,
    parent.milestone_id
FROM project_milestones child
JOIN project_milestones parent
    ON parent.project_id = child.project_id
WHERE child.milestone_key = 'M2'
  AND parent.milestone_key = 'M1';

INSERT INTO milestone_dependencies (
    milestone_id,
    dependency_milestone_id
)
SELECT
    child.milestone_id,
    parent.milestone_id
FROM project_milestones child
JOIN project_milestones parent
    ON parent.project_id = child.project_id
WHERE child.milestone_key = 'M3'
  AND parent.milestone_key = 'M2';

INSERT INTO branch_protection_policies (
    branch_id,
    required_approvals,
    require_status_checks,
    require_conversation_resolution,
    restrict_direct_pushes,
    allow_force_push,
    allow_branch_deletion,
    require_linear_history,
    dismiss_stale_approvals
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    TRUE,
    TRUE
FROM repository_branches
WHERE branch_name = 'main';

INSERT INTO required_status_checks (
    policy_id,
    check_name
)
SELECT
    bp.policy_id,
    checks.check_name
FROM branch_protection_policies bp
JOIN repository_branches b
    ON b.branch_id = bp.branch_id
CROSS JOIN (
    VALUES
        ('unit-tests'),
        ('integration-tests'),
        ('security-scan')
) AS checks(check_name)
WHERE b.branch_name = 'main';

INSERT INTO reviewers (
    reviewer_name,
    role_name
)
VALUES
    ('Senior Engineer', 'Engineering Reviewer'),
    ('Security Reviewer', 'Security Reviewer'),
    ('Release Manager', 'Release Manager');

INSERT INTO commits (
    repository_id,
    commit_hash,
    author_name,
    commit_message,
    committed_at
)
SELECT
    repository_id,
    '1111111111111111111111111111111111111111',
    'Developer',
    'Implement invoice calculation',
    CURRENT_TIMESTAMP - INTERVAL '3 hours'
FROM repositories
WHERE repository_name = 'enterprise-billing-service';

INSERT INTO commits (
    repository_id,
    commit_hash,
    author_name,
    commit_message,
    committed_at
)
SELECT
    repository_id,
    '2222222222222222222222222222222222222222',
    'Developer',
    'Add reconciliation rules',
    CURRENT_TIMESTAMP - INTERVAL '2 hours'
FROM repositories
WHERE repository_name = 'enterprise-billing-service';

INSERT INTO commits (
    repository_id,
    commit_hash,
    author_name,
    commit_message,
    committed_at
)
SELECT
    repository_id,
    '3333333333333333333333333333333333333333',
    'Developer',
    'Add security validation',
    CURRENT_TIMESTAMP - INTERVAL '1 hour'
FROM repositories
WHERE repository_name = 'enterprise-billing-service';

INSERT INTO pull_requests (
    repository_id,
    number,
    source_branch_id,
    target_branch_id,
    milestone_id,
    author_name,
    title,
    description,
    status,
    is_draft,
    has_conflicts
)
SELECT
    r.repository_id,
    812,
    source.branch_id,
    target.branch_id,
    m.milestone_id,
    'Developer',
    'Implement billing core service',
    'Implements invoice calculation, reconciliation, and security validation.',
    'open',
    FALSE,
    FALSE
FROM repositories r
JOIN repository_branches source
    ON source.repository_id = r.repository_id
   AND source.branch_name = 'feature/billing-core'
JOIN repository_branches target
    ON target.repository_id = r.repository_id
   AND target.branch_name = 'main'
JOIN project_milestones m
    ON m.milestone_key = 'M2'
JOIN projects p
    ON p.project_id = m.project_id
   AND p.project_id = r.project_id
WHERE r.repository_name = 'enterprise-billing-service';

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_id,
    sequence_number
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    ROW_NUMBER() OVER (ORDER BY c.committed_at)
FROM pull_requests pr
JOIN repositories r
    ON r.repository_id = pr.repository_id
JOIN commits c
    ON c.repository_id = r.repository_id
WHERE pr.number = 812;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state
)
SELECT
    pr.pull_request_id,
    reviewer.reviewer_id,
    'approved'
FROM pull_requests pr
JOIN reviewers reviewer
    ON reviewer.reviewer_name = 'Senior Engineer'
WHERE pr.number = 812;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state
)
SELECT
    pr.pull_request_id,
    reviewer.reviewer_id,
    'approved'
FROM pull_requests pr
JOIN reviewers reviewer
    ON reviewer.reviewer_name = 'Security Reviewer'
WHERE pr.number = 812;

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    passed
)
SELECT
    pr.pull_request_id,
    checks.check_name,
    TRUE
FROM pull_requests pr
CROSS JOIN (
    VALUES
        ('unit-tests'),
        ('integration-tests'),
        ('security-scan')
) AS checks(check_name)
WHERE pr.number = 812;

INSERT INTO project_events (
    project_id,
    milestone_id,
    pull_request_id,
    event_type,
    event_title,
    actor_name,
    event_details
)
SELECT
    p.project_id,
    m.milestone_id,
    NULL,
    'project_started',
    'Billing modernization project started',
    'Program Manager',
    '{"importance": 5}'::jsonb
FROM projects p
JOIN project_milestones m
    ON m.project_id = p.project_id
WHERE p.project_key = 'BILLING-204'
  AND m.milestone_key = 'M1';

INSERT INTO project_events (
    project_id,
    milestone_id,
    pull_request_id,
    event_type,
    event_title,
    actor_name,
    event_details
)
SELECT
    p.project_id,
    m.milestone_id,
    pr.pull_request_id,
    'pull_request_opened',
    'Billing core Pull Request opened',
    'Developer',
    jsonb_build_object(
        'number', pr.number,
        'source_branch', source.branch_name,
        'target_branch', target.branch_name,
        'commit_count', (
            SELECT COUNT(*)
            FROM pull_request_commits pc
            WHERE pc.pull_request_id = pr.pull_request_id
        )
    )
FROM pull_requests pr
JOIN repositories r
    ON r.repository_id = pr.repository_id
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_milestones m
    ON m.milestone_id = pr.milestone_id
JOIN repository_branches source
    ON source.branch_id = pr.source_branch_id
JOIN repository_branches target
    ON target.branch_id = pr.target_branch_id
WHERE pr.number = 812;

INSERT INTO project_events (
    project_id,
    milestone_id,
    pull_request_id,
    event_type,
    event_title,
    actor_name,
    event_details
)
SELECT
    p.project_id,
    pr.milestone_id,
    pr.pull_request_id,
    'approval_granted',
    'Required Pull Request approval recorded',
    'Senior Engineer',
    '{"approval_count": 2}'::jsonb
FROM pull_requests pr
JOIN repositories r
    ON r.repository_id = pr.repository_id
JOIN projects p
    ON p.project_id = r.project_id
WHERE pr.number = 812;

INSERT INTO project_events (
    project_id,
    milestone_id,
    pull_request_id,
    event_type,
    event_title,
    actor_name,
    event_details
)
SELECT
    p.project_id,
    pr.milestone_id,
    pr.pull_request_id,
    'merged',
    'Billing core Pull Request merged',
    'Release Manager',
    '{"merge_strategy": "squash"}'::jsonb
FROM pull_requests pr
JOIN repositories r
    ON r.repository_id = pr.repository_id
JOIN projects p
    ON p.project_id = r.project_id
WHERE pr.number = 812;

UPDATE pull_requests
SET
    status = 'merged',
    merged_at = CURRENT_TIMESTAMP
WHERE number = 812;

UPDATE project_milestones
SET
    status = 'completed',
    completed_at = CURRENT_TIMESTAMP
WHERE milestone_key = 'M2';

UPDATE project_milestones
SET
    status = 'active'
WHERE milestone_key = 'M3';

INSERT INTO project_events (
    project_id,
    milestone_id,
    event_type,
    event_title,
    actor_name,
    event_details
)
SELECT
    p.project_id,
    m.milestone_id,
    'released',
    'Billing service released to production',
    'Release Manager',
    '{"version": "4.0.0", "environment": "production"}'::jsonb
FROM projects p
JOIN project_milestones m
    ON m.project_id = p.project_id
WHERE p.project_key = 'BILLING-204'
  AND m.milestone_key = 'M3';

UPDATE project_milestones
SET
    status = 'completed',
    completed_at = CURRENT_TIMESTAMP
WHERE milestone_key = 'M3';

SELECT *
FROM milestone_progress
ORDER BY importance DESC, target_date;

SELECT *
FROM important_project_events
ORDER BY occurred_at;

SELECT *
FROM pull_request_review_state
ORDER BY pull_request_id;

SELECT
    m.milestone_key,
    m.milestone_name,
    m.status,
    m.target_date,
    CASE
        WHEN m.status = 'completed' THEN 'completed'
        WHEN m.target_date < CURRENT_DATE THEN 'overdue'
        ELSE 'on_track'
    END AS schedule_state,
    COALESCE(mp.event_count, 0) AS event_count,
    COALESCE(mp.pull_request_count, 0) AS pull_request_count,
    COALESCE(mp.merged_pull_request_count, 0) AS merged_pull_request_count
FROM project_milestones m
LEFT JOIN milestone_progress mp
    ON mp.milestone_id = m.milestone_id
ORDER BY m.target_date;

SELECT
    e.event_type,
    e.event_title,
    e.actor_name,
    e.occurred_at,
    m.milestone_name
FROM project_events e
JOIN project_milestones m
    ON m.milestone_id = e.milestone_id
WHERE m.importance >= 4
ORDER BY e.occurred_at DESC;

BEGIN;

UPDATE pull_requests
SET
    status = 'merged',
    merged_at = CURRENT_TIMESTAMP
WHERE number = 812
  AND status = 'open'
  AND NOT EXISTS (
      SELECT 1
      FROM evaluate_pull_request_merge(
          (SELECT pull_request_id
           FROM pull_requests
           WHERE number = 812)
      ) decision
      WHERE decision.eligible = FALSE
  );

COMMIT;
