DROP SCHEMA IF EXISTS repository_governance CASCADE;
CREATE SCHEMA repository_governance;
SET search_path TO repository_governance;

CREATE TYPE pull_request_state AS ENUM (
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
    'merge_commit',
    'squash',
    'rebase'
);

CREATE TABLE repository (
    repository_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(name)) >= 2),
    CHECK (length(trim(default_branch)) >= 1)
);

CREATE TABLE developer (
    developer_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (username ~ '^[A-Za-z0-9._-]{2,39}$'),
    CHECK (length(trim(display_name)) >= 2)
);

CREATE TABLE repository_member (
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    developer_id BIGINT NOT NULL REFERENCES developer(developer_id)
        ON DELETE CASCADE,
    role_name TEXT NOT NULL CHECK (
        role_name IN ('read', 'write', 'maintain', 'admin')
    ),
    PRIMARY KEY (repository_id, developer_id)
);

CREATE TABLE branch (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) >= 1)
);

CREATE TABLE commit (
    commit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    sha VARCHAR(40) NOT NULL UNIQUE,
    author_id BIGINT NOT NULL REFERENCES developer(developer_id),
    message TEXT NOT NULL,
    changed_files INTEGER NOT NULL,
    additions INTEGER NOT NULL,
    deletions INTEGER NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (sha ~ '^[0-9a-fA-F]{7,40}$'),
    CHECK (length(trim(message)) > 0),
    CHECK (changed_files >= 0),
    CHECK (additions >= 0),
    CHECK (deletions >= 0)
);

CREATE TABLE pull_request (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    number INTEGER NOT NULL,
    source_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    author_id BIGINT NOT NULL REFERENCES developer(developer_id),
    title TEXT NOT NULL,
    state pull_request_state NOT NULL DEFAULT 'open',
    revision INTEGER NOT NULL DEFAULT 1,
    synchronized_with_base BOOLEAN NOT NULL DEFAULT TRUE,
    has_merge_conflict BOOLEAN NOT NULL DEFAULT FALSE,
    unresolved_conversations INTEGER NOT NULL DEFAULT 0,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) >= 5),
    CHECK (revision > 0),
    CHECK (unresolved_conversations >= 0),
    CHECK (
        state <> 'merged'
        OR merged_at IS NOT NULL
    )
);

CREATE TABLE pull_request_commit (
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commit(commit_id)
        ON DELETE RESTRICT,
    commit_order INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, commit_order),
    CHECK (commit_order > 0)
);

CREATE TABLE review (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES developer(developer_id),
    state review_state NOT NULL,
    revision INTEGER NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    inline_comment_count INTEGER NOT NULL DEFAULT 0,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (revision > 0),
    CHECK (inline_comment_count >= 0)
);

CREATE TABLE review_comment (
    review_comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES review(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(file_path)) > 0),
    CHECK (line_number > 0),
    CHECK (length(trim(body)) >= 3)
);

CREATE TABLE status_check (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    revision INTEGER NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pull_request_id, check_name),
    CHECK (revision > 0)
);

CREATE TABLE branch_protection (
    branch_protection_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branch(branch_id)
        ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 0,
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT TRUE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (required_approvals >= 0)
);

CREATE TABLE required_status_check (
    branch_protection_id BIGINT NOT NULL
        REFERENCES branch_protection(branch_protection_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (branch_protection_id, check_name),
    CHECK (length(trim(check_name)) > 0)
);

CREATE TABLE allowed_merge_strategy (
    branch_protection_id BIGINT NOT NULL
        REFERENCES branch_protection(branch_protection_id)
        ON DELETE CASCADE,
    strategy merge_strategy NOT NULL,
    PRIMARY KEY (branch_protection_id, strategy)
);

CREATE INDEX idx_pull_request_target_state
    ON pull_request(target_branch_id, state);

CREATE INDEX idx_review_pr_reviewer
    ON review(pull_request_id, reviewer_id, submitted_at DESC);

CREATE INDEX idx_status_check_pr_name
    ON status_check(pull_request_id, check_name);

CREATE INDEX idx_pr_commit_order
    ON pull_request_commit(pull_request_id, commit_order);

CREATE OR REPLACE FUNCTION enforce_pull_request_revision()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.revision < OLD.revision THEN
        RAISE EXCEPTION
            'Pull Request revision cannot move backwards';
    END IF;

    IF NEW.state = 'merged'
       AND OLD.state <> 'merged'
       AND NEW.merged_at IS NULL THEN
        NEW.merged_at := now();
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_pull_request_revision
BEFORE UPDATE ON pull_request
FOR EACH ROW
EXECUTE FUNCTION enforce_pull_request_revision();

CREATE OR REPLACE FUNCTION review_cost_minutes(
    p_pull_request_id BIGINT
)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT GREATEST(
        10,
        COALESCE(SUM(c.changed_files), 0)::INTEGER * 4
    )
    FROM pull_request_commit pc
    JOIN commit c ON c.commit_id = pc.commit_id
    WHERE pc.pull_request_id = p_pull_request_id;
$$;

CREATE OR REPLACE FUNCTION merge_eligibility(
    p_pull_request_id BIGINT,
    p_strategy merge_strategy
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    pr RECORD;
    policy RECORD;
    approval_count INTEGER;
    changes_requested BOOLEAN;
    missing_check TEXT;
    stale_check TEXT;
BEGIN
    SELECT
        p.*,
        bp.branch_protection_id,
        bp.required_approvals,
        bp.dismiss_stale_approvals,
        bp.require_conversation_resolution,
        bp.require_linear_history
    INTO pr
    FROM pull_request p
    JOIN branch_protection bp
      ON bp.branch_id = p.target_branch_id
    WHERE p.pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Pull Request or branch protection policy not found';
        RETURN;
    END IF;

    IF pr.state <> 'open' THEN
        RETURN QUERY
        SELECT FALSE, 'Pull Request is not open';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pull_request_commit
        WHERE pull_request_id = p_pull_request_id
    ) THEN
        RETURN QUERY
        SELECT FALSE, 'Pull Request has no commits';
    END IF;

    IF NOT pr.synchronized_with_base THEN
        RETURN QUERY
        SELECT FALSE, 'Pull Request is not synchronized with the base branch';
    END IF;

    IF pr.has_merge_conflict THEN
        RETURN QUERY
        SELECT FALSE, 'Merge conflicts remain unresolved';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM allowed_merge_strategy ams
        WHERE ams.branch_protection_id = pr.branch_protection_id
          AND ams.strategy = p_strategy
    ) THEN
        RETURN QUERY
        SELECT FALSE, 'Selected merge strategy is not allowed';
    END IF;

    SELECT COUNT(*)
    INTO approval_count
    FROM (
        SELECT DISTINCT ON (r.reviewer_id)
            r.reviewer_id,
            r.state,
            r.revision
        FROM review r
        WHERE r.pull_request_id = p_pull_request_id
        ORDER BY r.reviewer_id, r.submitted_at DESC, r.review_id DESC
    ) latest
    JOIN repository_member rm
      ON rm.developer_id = latest.reviewer_id
     AND rm.repository_id = pr.repository_id
    WHERE latest.state = 'approved'
      AND rm.role_name IN ('write', 'maintain', 'admin')
      AND (
          NOT pr.dismiss_stale_approvals
          OR latest.revision = pr.revision
      );

    IF EXISTS (
        SELECT 1
        FROM (
            SELECT DISTINCT ON (r.reviewer_id)
                r.reviewer_id,
                r.state
            FROM review r
            WHERE r.pull_request_id = p_pull_request_id
            ORDER BY r.reviewer_id, r.submitted_at DESC, r.review_id DESC
        ) latest
        JOIN repository_member rm
          ON rm.developer_id = latest.reviewer_id
         AND rm.repository_id = pr.repository_id
        WHERE latest.state = 'changes_requested'
          AND rm.role_name IN ('write', 'maintain', 'admin')
    ) THEN
        RETURN QUERY
        SELECT FALSE, 'An eligible reviewer currently requests changes';
    END IF;

    IF approval_count < pr.required_approvals THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   'Required approvals: %s; current approvals: %s',
                   pr.required_approvals,
                   approval_count
               );
    END IF;

    SELECT rsc.check_name
    INTO missing_check
    FROM required_status_check rsc
    WHERE rsc.branch_protection_id = pr.branch_protection_id
      AND NOT EXISTS (
          SELECT 1
          FROM status_check sc
          WHERE sc.pull_request_id = p_pull_request_id
            AND sc.check_name = rsc.check_name
      )
    LIMIT 1;

    IF missing_check IS NOT NULL THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   'Required status check %s is missing',
                   missing_check
               );
    END IF;

    SELECT sc.check_name
    INTO stale_check
    FROM status_check sc
    JOIN required_status_check rsc
      ON rsc.branch_protection_id = pr.branch_protection_id
     AND rsc.check_name = sc.check_name
    WHERE sc.pull_request_id = p_pull_request_id
      AND (
          NOT sc.passed
          OR sc.revision <> pr.revision
      )
    LIMIT 1;

    IF stale_check IS NOT NULL THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   'Required status check %s is failed or stale',
                   stale_check
               );
    END IF;

    IF pr.require_conversation_resolution
       AND pr.unresolved_conversations > 0 THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   '%s review conversation(s) remain unresolved',
                   pr.unresolved_conversations
               );
    END IF;

    RETURN QUERY
    SELECT TRUE, 'All repository merge conditions are satisfied';
END;
$$;

INSERT INTO repository (name, default_branch)
VALUES ('cost-resource-governance', 'main');

INSERT INTO developer (username, display_name)
VALUES
    ('alice', 'Alice Reviewer'),
    ('bob', 'Bob Reviewer'),
    ('carol', 'Carol Maintainer'),
    ('dave', 'Dave Developer');

INSERT INTO branch (repository_id, branch_name, is_default)
SELECT repository_id, 'main', TRUE
FROM repository
WHERE name = 'cost-resource-governance';

INSERT INTO branch (repository_id, branch_name)
SELECT repository_id, 'feature/resource-cost-review'
FROM repository
WHERE name = 'cost-resource-governance';

INSERT INTO branch (repository_id, branch_name)
SELECT repository_id, 'feature/governance-engine'
FROM repository
WHERE name = 'cost-resource-governance';

INSERT INTO repository_member (repository_id, developer_id, role_name)
SELECT r.repository_id, d.developer_id, roles.role_name
FROM repository r
CROSS JOIN (
    VALUES
        ('alice', 'write'),
        ('bob', 'write'),
        ('carol', 'maintain'),
        ('dave', 'read')
) AS roles(username, role_name)
JOIN developer d ON d.username = roles.username
WHERE r.name = 'cost-resource-governance';

INSERT INTO branch_protection (
    branch_id,
    required_approvals,
    dismiss_stale_approvals,
    require_conversation_resolution,
    restrict_direct_push,
    allow_force_push,
    allow_branch_deletion,
    require_linear_history
)
SELECT
    b.branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    TRUE
FROM branch b
JOIN repository r ON r.repository_id = b.repository_id
WHERE r.name = 'cost-resource-governance'
  AND b.branch_name = 'main';

INSERT INTO required_status_check (
    branch_protection_id,
    check_name
)
SELECT
    bp.branch_protection_id,
    checks.check_name
FROM branch_protection bp
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS checks(check_name)
JOIN branch b ON b.branch_id = bp.branch_id
JOIN repository r ON r.repository_id = b.repository_id
WHERE r.name = 'cost-resource-governance'
  AND b.branch_name = 'main';

INSERT INTO allowed_merge_strategy (
    branch_protection_id,
    strategy
)
SELECT branch_protection_id, 'squash'
FROM branch_protection;

INSERT INTO commit (
    repository_id,
    sha,
    author_id,
    message,
    changed_files,
    additions,
    deletions
)
SELECT
    r.repository_id,
    commits.sha,
    d.developer_id,
    commits.message,
    commits.changed_files,
    commits.additions,
    commits.deletions
FROM repository r
JOIN developer d ON d.username = 'dave'
CROSS JOIN (
    VALUES
    (
        '1234567abcdef',
        'Add resource review model',
        8,
        240,
        35
    ),
    (
        'abcdef7123456',
        'Add repository governance rules',
        5,
        150,
        20
    )
) AS commits(
    sha,
    message,
    changed_files,
    additions,
    deletions
)
WHERE r.name = 'cost-resource-governance';

INSERT INTO pull_request (
    repository_id,
    number,
    source_branch_id,
    target_branch_id,
    author_id,
    title
)
SELECT
    r.repository_id,
    42,
    source.branch_id,
    target.branch_id,
    d.developer_id,
    'Review repository cost and resource impact'
FROM repository r
JOIN branch source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'feature/resource-cost-review'
JOIN branch target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
JOIN developer d ON d.username = 'dave'
WHERE r.name = 'cost-resource-governance';

INSERT INTO pull_request_commit (
    pull_request_id,
    commit_id,
    commit_order
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    row_number() OVER (ORDER BY c.commit_id)
FROM pull_request pr
JOIN repository r ON r.repository_id = pr.repository_id
JOIN commit c ON c.repository_id = r.repository_id
WHERE pr.number = 42
  AND r.name = 'cost-resource-governance';

INSERT INTO review (
    pull_request_id,
    reviewer_id,
    state,
    revision,
    body,
    inline_comment_count
)
SELECT
    pr.pull_request_id,
    d.developer_id,
    'approved',
    pr.revision,
    'Reviewed resource impact and scope.',
    2
FROM pull_request pr
JOIN developer d ON d.username = 'alice'
WHERE pr.number = 42;

INSERT INTO review (
    pull_request_id,
    reviewer_id,
    state,
    revision,
    body,
    inline_comment_count
)
SELECT
    pr.pull_request_id,
    d.developer_id,
    'changes_requested',
    pr.revision,
    'Resolve the missing governance check.',
    3
FROM pull_request pr
JOIN developer d ON d.username = 'bob'
WHERE pr.number = 42;

INSERT INTO review_comment (
    review_id,
    file_path,
    line_number,
    body
)
SELECT
    review_id,
    'governance.py',
    87,
    'The merge gate should reject stale status checks.'
FROM review r
JOIN pull_request pr
  ON pr.pull_request_id = r.pull_request_id
JOIN developer d
  ON d.developer_id = r.reviewer_id
WHERE pr.number = 42
  AND d.username = 'bob';

INSERT INTO status_check (
    pull_request_id,
    check_name,
    passed,
    revision
)
SELECT
    pr.pull_request_id,
    checks.check_name,
    TRUE,
    pr.revision
FROM pull_request pr
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS checks(check_name)
WHERE pr.number = 42;

UPDATE pull_request
SET unresolved_conversations = 1
WHERE number = 42;

-- Review-effort query: changed files provide a concrete resource signal
-- for estimating reviewer capacity.
SELECT
    pr.number,
    pr.title,
    SUM(c.changed_files) AS changed_files,
    review_cost_minutes(pr.pull_request_id) AS estimated_review_minutes
FROM pull_request pr
JOIN pull_request_commit pc
  ON pc.pull_request_id = pr.pull_request_id
JOIN commit c
  ON c.commit_id = pc.commit_id
WHERE pr.number = 42
GROUP BY pr.number, pr.title, pr.pull_request_id;

-- Latest-review report: only the most recent decision by each reviewer
-- participates in approval evaluation.
WITH latest_reviews AS (
    SELECT DISTINCT ON (r.pull_request_id, r.reviewer_id)
        r.pull_request_id,
        r.reviewer_id,
        r.state,
        r.revision,
        r.submitted_at
    FROM review r
    ORDER BY
        r.pull_request_id,
        r.reviewer_id,
        r.submitted_at DESC,
        r.review_id DESC
)
SELECT
    pr.number,
    d.username AS reviewer,
    latest_reviews.state,
    latest_reviews.revision,
    pr.revision AS current_revision
FROM latest_reviews
JOIN pull_request pr
  ON pr.pull_request_id = latest_reviews.pull_request_id
JOIN developer d
  ON d.developer_id = latest_reviews.reviewer_id
WHERE pr.number = 42
ORDER BY d.username;

-- First evaluation demonstrates a blocked merge because Bob requested
-- changes and an unresolved conversation exists.
SELECT *
FROM merge_eligibility(
    (
        SELECT pull_request_id
        FROM pull_request
        WHERE number = 42
    ),
    'squash'
);

-- Transactional correction: resolve the review discussion and record a
-- new approval. The old review remains auditable.
BEGIN;

UPDATE pull_request
SET unresolved_conversations = 0
WHERE number = 42
  AND state = 'open';

INSERT INTO review (
    pull_request_id,
    reviewer_id,
    state,
    revision,
    body,
    inline_comment_count
)
SELECT
    pr.pull_request_id,
    d.developer_id,
    'approved',
    pr.revision,
    'Governance condition corrected and re-reviewed.',
    1
FROM pull_request pr
JOIN developer d ON d.username = 'bob'
WHERE pr.number = 42
  AND pr.state = 'open';

COMMIT;

-- The second evaluation should now pass because two eligible reviewers
-- have current approvals, required checks pass, and conversations are
-- resolved.
SELECT *
FROM merge_eligibility(
    (
        SELECT pull_request_id
        FROM pull_request
        WHERE number = 42
    ),
    'squash'
);

-- A base-branch update demonstrates stale-review protection.
BEGIN;

UPDATE pull_request
SET
    revision = revision + 1,
    synchronized_with_base = FALSE
WHERE number = 42
  AND state = 'open';

COMMIT;

SELECT *
FROM merge_eligibility(
    (
        SELECT pull_request_id
        FROM pull_request
        WHERE number = 42
    ),
    'squash'
);

-- Synchronize the PR and refresh required checks at the new revision.
BEGIN;

UPDATE pull_request
SET
    synchronized_with_base = TRUE,
    has_merge_conflict = FALSE
WHERE number = 42;

UPDATE status_check
SET revision = (
    SELECT revision
    FROM pull_request
    WHERE number = 42
)
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_request
    WHERE number = 42
);

INSERT INTO review (
    pull_request_id,
    reviewer_id,
    state,
    revision,
    body,
    inline_comment_count
)
SELECT
    pr.pull_request_id,
    d.developer_id,
    'approved',
    pr.revision,
    'Re-approved after base synchronization.',
    0
FROM pull_request pr
JOIN developer d ON d.username = 'alice'
WHERE pr.number = 42
  AND pr.state = 'open';

INSERT INTO review (
    pull_request_id,
    reviewer_id,
    state,
    revision,
    body,
    inline_comment_count
)
SELECT
    pr.pull_request_id,
    d.developer_id,
    'approved',
    pr.revision,
    'Re-approved after base synchronization.',
    0
FROM pull_request pr
JOIN developer d ON d.username = 'bob'
WHERE pr.number = 42
  AND pr.state = 'open';

COMMIT;

SELECT *
FROM merge_eligibility(
    (
        SELECT pull_request_id
        FROM pull_request
        WHERE number = 42
    ),
    'squash'
);

-- Repository-level resource report: compare review effort with reviewer
-- capacity by repository member role.
SELECT
    r.name AS repository,
    COUNT(DISTINCT pr.pull_request_id) AS open_pull_requests,
    COALESCE(SUM(review_cost_minutes(pr.pull_request_id)), 0)
        AS estimated_review_minutes
FROM repository r
LEFT JOIN pull_request pr
  ON pr.repository_id = r.repository_id
 AND pr.state = 'open'
GROUP BY r.name;

-- Branch-protection report exposes governance conditions independently
-- from individual Pull Request review decisions.
SELECT
    r.name AS repository,
    b.branch_name,
    bp.required_approvals,
    bp.dismiss_stale_approvals,
    bp.require_conversation_resolution,
    bp.restrict_direct_push,
    bp.allow_force_push,
    bp.allow_branch_deletion,
    bp.require_linear_history
FROM branch_protection bp
JOIN branch b ON b.branch_id = bp.branch_id
JOIN repository r ON r.repository_id = b.repository_id
ORDER BY r.name, b.branch_name;
