DROP SCHEMA IF EXISTS repository_governance CASCADE;
CREATE SCHEMA repository_governance;

SET search_path = repository_governance, public;

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

CREATE TYPE check_state AS ENUM (
    'pending',
    'passing',
    'failing'
);

CREATE TYPE merge_strategy AS ENUM (
    'merge',
    'squash',
    'rebase'
);

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    administrator_bypass_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(repository_name)) > 0)
);

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE repository_reviewers (
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE RESTRICT,
    PRIMARY KEY (repository_id, user_id)
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    allow_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    allow_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    head_commit_id BIGINT,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0)
);

CREATE TABLE commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    commit_sha TEXT NOT NULL,
    author_user_id BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE RESTRICT,
    message TEXT NOT NULL,
    parent_commit_id BIGINT
        REFERENCES commits(commit_id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, commit_sha),
    CHECK (length(commit_sha) >= 7),
    CHECK (length(trim(message)) > 0)
);

ALTER TABLE branches
    ADD CONSTRAINT fk_branch_head_commit
    FOREIGN KEY (head_commit_id)
    REFERENCES commits(commit_id)
    ON DELETE RESTRICT;

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    pull_request_number INTEGER NOT NULL,
    author_user_id BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE RESTRICT,
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id) ON DELETE RESTRICT,
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    state pull_request_state NOT NULL DEFAULT 'open',
    base_head_commit_id BIGINT
        REFERENCES commits(commit_id) ON DELETE RESTRICT,
    draft BOOLEAN NOT NULL DEFAULT FALSE,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, pull_request_number),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) > 0),
    CHECK (
        (state = 'merged' AND merged_at IS NOT NULL)
        OR state <> 'merged'
    )
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    commit_id BIGINT NOT NULL
        REFERENCES commits(commit_id) ON DELETE RESTRICT,
    commit_order INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, commit_order),
    CHECK (commit_order > 0)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer_user_id BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE RESTRICT,
    review_state review_state NOT NULL,
    reviewed_commit_id BIGINT
        REFERENCES commits(commit_id) ON DELETE RESTRICT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id) ON DELETE CASCADE,
    reviewer_user_id BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE RESTRICT,
    body TEXT NOT NULL,
    file_path TEXT,
    line_number INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(body)) > 0),
    CHECK (
        line_number IS NULL
        OR line_number > 0
    )
);

CREATE TABLE conversations (
    conversation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    created_by_user_id BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE RESTRICT,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,
    CHECK (length(trim(body)) > 0),
    CHECK (
        (resolved = TRUE AND resolved_at IS NOT NULL)
        OR resolved = FALSE
    )
);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL,
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name),
    CHECK (length(trim(check_name)) > 0)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id) ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 1,
    require_conversations_resolved BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    restrict_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_branch_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    allow_administrator_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (required_approvals >= 0)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name),
    CHECK (length(trim(check_name)) > 0)
);

CREATE TABLE merge_events (
    merge_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE RESTRICT,
    merged_by_user_id BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE RESTRICT,
    strategy merge_strategy NOT NULL,
    merge_commit_id BIGINT
        REFERENCES commits(commit_id) ON DELETE RESTRICT,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pr_target_state
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_state
    ON reviews(pull_request_id, review_state);

CREATE INDEX idx_checks_pr_state
    ON status_checks(pull_request_id, state);

CREATE INDEX idx_conversations_pr_unresolved
    ON conversations(pull_request_id, resolved)
    WHERE resolved = FALSE;

CREATE INDEX idx_pr_commits_order
    ON pull_request_commits(pull_request_id, commit_order);

CREATE OR REPLACE FUNCTION enforce_reviewer_eligibility()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    pr_repository_id BIGINT;
    reviewer_allowed BOOLEAN;
    pr_author BIGINT;
BEGIN
    SELECT repository_id, author_user_id
    INTO pr_repository_id, pr_author
    FROM pull_requests
    WHERE pull_request_id = NEW.pull_request_id;

    IF NEW.reviewer_user_id = pr_author THEN
        RAISE EXCEPTION
            'Self-review is not permitted for Pull Request %',
            NEW.pull_request_id;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM repository_reviewers rr
        JOIN users u ON u.user_id = rr.user_id
        WHERE rr.repository_id = pr_repository_id
          AND rr.user_id = NEW.reviewer_user_id
          AND u.active
    )
    INTO reviewer_allowed;

    IF NOT reviewer_allowed THEN
        RAISE EXCEPTION
            'Reviewer % is not eligible for this repository',
            NEW.reviewer_user_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_review_eligibility
BEFORE INSERT OR UPDATE ON reviews
FOR EACH ROW
EXECUTE FUNCTION enforce_reviewer_eligibility();

CREATE OR REPLACE FUNCTION prevent_direct_push_to_protected_branch()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    branch_is_protected BOOLEAN;
BEGIN
    SELECT protected
    INTO branch_is_protected
    FROM branches
    WHERE branch_id = NEW.target_branch_id;

    IF branch_is_protected THEN
        RAISE EXCEPTION
            'Protected branch cannot be modified directly through Pull Request metadata.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION mark_conversation_resolved()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.resolved AND NOT OLD.resolved THEN
        NEW.resolved_at := CURRENT_TIMESTAMP;
    ELSIF NOT NEW.resolved THEN
        NEW.resolved_at := NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_conversation_resolution
BEFORE UPDATE ON conversations
FOR EACH ROW
EXECUTE FUNCTION mark_conversation_resolved();

CREATE OR REPLACE FUNCTION evaluate_merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE sql
AS $$
WITH pr AS (
    SELECT
        p.pull_request_id,
        p.repository_id,
        p.state,
        p.draft,
        p.author_user_id,
        p.target_branch_id,
        p.base_head_commit_id
    FROM pull_requests p
    WHERE p.pull_request_id = p_pull_request_id
),
policy AS (
    SELECT
        bp.required_approvals,
        bp.require_conversations_resolved,
        bp.require_linear_history
    FROM pr
    JOIN branch_protection_policies bp
      ON bp.branch_id = pr.target_branch_id
),
approval_count AS (
    SELECT COUNT(DISTINCT r.reviewer_user_id) AS approvals
    FROM reviews r
    JOIN pr
      ON pr.pull_request_id = r.pull_request_id
    WHERE r.review_state = 'approved'
),
commit_count AS (
    SELECT COUNT(*) AS commits
    FROM pull_request_commits pc
    WHERE pc.pull_request_id = p_pull_request_id
),
blocking_reviews AS (
    SELECT COUNT(*) AS changes_requested
    FROM reviews r
    WHERE r.pull_request_id = p_pull_request_id
      AND r.review_state = 'changes_requested'
),
unresolved AS (
    SELECT COUNT(*) AS unresolved_count
    FROM conversations c
    WHERE c.pull_request_id = p_pull_request_id
      AND NOT c.resolved
),
required_checks AS (
    SELECT
        COUNT(rsc.check_name) AS required_count,
        COUNT(sc.status_check_id) FILTER (
            WHERE sc.state = 'passing'
        ) AS passing_count
    FROM pr
    JOIN policy ON TRUE
    JOIN branch_protection_policies bp
      ON bp.branch_id = pr.target_branch_id
    LEFT JOIN required_status_checks rsc
      ON rsc.policy_id = bp.policy_id
    LEFT JOIN status_checks sc
      ON sc.pull_request_id = pr.pull_request_id
     AND sc.check_name = rsc.check_name
),
base_state AS (
    SELECT
        b.head_commit_id,
        pr.base_head_commit_id
    FROM pr
    JOIN branches b
      ON b.branch_id = pr.target_branch_id
)
SELECT
    CASE
        WHEN pr.state <> 'open' THEN FALSE
        WHEN pr.draft THEN FALSE
        WHEN cc.commits = 0 THEN FALSE
        WHEN br.changes_requested > 0 THEN FALSE
        WHEN ac.approvals < policy.required_approvals THEN FALSE
        WHEN rs.required_count <> rs.passing_count THEN FALSE
        WHEN policy.require_conversations_resolved
             AND u.unresolved_count > 0 THEN FALSE
        WHEN bs.head_commit_id IS DISTINCT FROM bs.base_head_commit_id
            THEN FALSE
        ELSE TRUE
    END AS eligible,
    CASE
        WHEN pr.state <> 'open'
            THEN 'Pull Request is not open.'
        WHEN pr.draft
            THEN 'Pull Request is a draft.'
        WHEN cc.commits = 0
            THEN 'Pull Request has no commits.'
        WHEN br.changes_requested > 0
            THEN 'A reviewer requested changes.'
        WHEN ac.approvals < policy.required_approvals
            THEN 'Required approvals are missing.'
        WHEN rs.required_count <> rs.passing_count
            THEN 'Required status checks are not all passing.'
        WHEN policy.require_conversations_resolved
             AND u.unresolved_count > 0
            THEN 'Unresolved review conversations remain.'
        WHEN bs.head_commit_id IS DISTINCT FROM bs.base_head_commit_id
            THEN 'Target branch has advanced since the Pull Request was opened.'
        ELSE 'All merge conditions are satisfied.'
    END AS reason
FROM pr
CROSS JOIN policy
CROSS JOIN approval_count ac
CROSS JOIN commit_count cc
CROSS JOIN blocking_reviews br
CROSS JOIN unresolved u
CROSS JOIN required_checks rs
CROSS JOIN base_state bs;
$$;

INSERT INTO repositories(repository_name, administrator_bypass_allowed)
VALUES ('payments-service', FALSE);

INSERT INTO users(username)
VALUES
    ('developer'),
    ('alice'),
    ('bob'),
    ('carol'),
    ('release-manager');

INSERT INTO repository_reviewers(repository_id, user_id)
SELECT r.repository_id, u.user_id
FROM repositories r
JOIN users u
  ON u.username IN ('alice', 'bob', 'carol')
WHERE r.repository_name = 'payments-service';

INSERT INTO branches(
    repository_id,
    branch_name,
    protected,
    allow_direct_push,
    allow_force_push,
    allow_deletion
)
SELECT
    repository_id,
    'main',
    TRUE,
    FALSE,
    FALSE,
    FALSE
FROM repositories
WHERE repository_name = 'payments-service';

INSERT INTO branches(
    repository_id,
    branch_name,
    protected
)
SELECT
    repository_id,
    'feature/refund-validation',
    FALSE
FROM repositories
WHERE repository_name = 'payments-service';

INSERT INTO branch_protection_policies(
    branch_id,
    required_approvals,
    require_conversations_resolved,
    require_linear_history,
    restrict_direct_push,
    restrict_force_push,
    restrict_branch_deletion,
    allow_administrator_bypass
)
SELECT
    b.branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE
FROM branches b
WHERE b.branch_name = 'main';

INSERT INTO required_status_checks(policy_id, check_name)
SELECT
    bp.policy_id,
    v.check_name
FROM branch_protection_policies bp
CROSS JOIN (
    VALUES
        ('unit-tests'),
        ('security-scan')
) AS v(check_name);

INSERT INTO commits(
    repository_id,
    commit_sha,
    author_user_id,
    message
)
SELECT
    r.repository_id,
    'abcdef1234567',
    u.user_id,
    'Add refund validation'
FROM repositories r
JOIN users u ON u.username = 'developer'
WHERE r.repository_name = 'payments-service';

INSERT INTO commits(
    repository_id,
    commit_sha,
    author_user_id,
    message,
    parent_commit_id
)
SELECT
    r.repository_id,
    'abcdef7654321',
    u.user_id,
    'Add refund boundary tests',
    c.commit_id
FROM repositories r
JOIN users u ON u.username = 'developer'
JOIN commits c
  ON c.commit_sha = 'abcdef1234567'
WHERE r.repository_name = 'payments-service';

UPDATE branches b
SET head_commit_id = c.commit_id
FROM commits c
JOIN repositories r
  ON r.repository_id = c.repository_id
WHERE b.repository_id = r.repository_id
  AND b.branch_name = 'main'
  AND c.commit_sha = 'abcdef1234567';

UPDATE branches b
SET head_commit_id = c.commit_id
FROM commits c
JOIN repositories r
  ON r.repository_id = c.repository_id
WHERE b.repository_id = r.repository_id
  AND b.branch_name = 'feature/refund-validation'
  AND c.commit_sha = 'abcdef7654321';

INSERT INTO pull_requests(
    repository_id,
    pull_request_number,
    author_user_id,
    source_branch_id,
    target_branch_id,
    title,
    state,
    base_head_commit_id,
    draft
)
SELECT
    r.repository_id,
    101,
    author.user_id,
    source.branch_id,
    target.branch_id,
    'Validate refund requests',
    'open',
    target.head_commit_id,
    FALSE
FROM repositories r
JOIN users author
  ON author.username = 'developer'
JOIN branches source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'feature/refund-validation'
JOIN branches target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
WHERE r.repository_name = 'payments-service';

INSERT INTO pull_request_commits(
    pull_request_id,
    commit_id,
    commit_order
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    1
FROM pull_requests pr
JOIN commits c
  ON c.commit_sha = 'abcdef7654321'
WHERE pr.pull_request_number = 101;

INSERT INTO reviews(
    pull_request_id,
    reviewer_user_id,
    review_state,
    reviewed_commit_id
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'approved',
    c.commit_id
FROM pull_requests pr
JOIN users u
  ON u.username = 'alice'
JOIN commits c
  ON c.commit_sha = 'abcdef7654321'
WHERE pr.pull_request_number = 101;

INSERT INTO reviews(
    pull_request_id,
    reviewer_user_id,
    review_state,
    reviewed_commit_id
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'approved',
    c.commit_id
FROM pull_requests pr
JOIN users u
  ON u.username = 'bob'
JOIN commits c
  ON c.commit_sha = 'abcdef7654321'
WHERE pr.pull_request_number = 101;

INSERT INTO review_comments(
    review_id,
    reviewer_user_id,
    body,
    file_path,
    line_number
)
SELECT
    rv.review_id,
    u.user_id,
    'Boundary validation is covered by the new test.',
    'refunds.py',
    42
FROM reviews rv
JOIN users u
  ON u.username = 'alice'
WHERE rv.pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE pull_request_number = 101
)
AND rv.reviewer_user_id = u.user_id;

INSERT INTO conversations(
    pull_request_id,
    created_by_user_id,
    body,
    resolved,
    resolved_at
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'Please verify the zero-value refund boundary.',
    TRUE,
    CURRENT_TIMESTAMP
FROM pull_requests pr
JOIN users u
  ON u.username = 'alice'
WHERE pr.pull_request_number = 101;

INSERT INTO status_checks(
    pull_request_id,
    check_name,
    state,
    completed_at
)
SELECT
    pr.pull_request_id,
    v.check_name,
    'passing',
    CURRENT_TIMESTAMP
FROM pull_requests pr
CROSS JOIN (
    VALUES
        ('unit-tests'),
        ('security-scan')
) AS v(check_name)
WHERE pr.pull_request_number = 101;

-- Initial merge-eligibility report.
SELECT *
FROM evaluate_merge_eligibility(
    (
        SELECT pull_request_id
        FROM pull_requests
        WHERE pull_request_number = 101
    )
);

-- Review quality report.
SELECT
    r.review_id,
    u.username AS reviewer,
    r.review_state,
    COUNT(rc.comment_id) AS inline_comments
FROM reviews r
JOIN users u
  ON u.user_id = r.reviewer_user_id
LEFT JOIN review_comments rc
  ON rc.review_id = r.review_id
GROUP BY
    r.review_id,
    u.username,
    r.review_state
ORDER BY r.review_id;

-- Required-check compliance report.
SELECT
    pr.pull_request_number,
    rsc.check_name,
    COALESCE(sc.state::TEXT, 'missing') AS actual_state,
    CASE
        WHEN sc.state = 'passing' THEN 'satisfied'
        ELSE 'blocked'
    END AS requirement_status
FROM pull_requests pr
JOIN branches target
  ON target.branch_id = pr.target_branch_id
JOIN branch_protection_policies bp
  ON bp.branch_id = target.branch_id
JOIN required_status_checks rsc
  ON rsc.policy_id = bp.policy_id
LEFT JOIN status_checks sc
  ON sc.pull_request_id = pr.pull_request_id
 AND sc.check_name = rsc.check_name
WHERE pr.pull_request_number = 101
ORDER BY rsc.check_name;

-- Open Pull Requests with unresolved conversations.
SELECT
    pr.pull_request_number,
    pr.title,
    COUNT(c.conversation_id) AS unresolved_conversations
FROM pull_requests pr
JOIN conversations c
  ON c.pull_request_id = pr.pull_request_id
WHERE pr.state = 'open'
  AND c.resolved = FALSE
GROUP BY pr.pull_request_number, pr.title
ORDER BY pr.pull_request_number;

-- Transactional merge record.
BEGIN;

WITH eligible AS (
    SELECT eligible
    FROM evaluate_merge_eligibility(
        (
            SELECT pull_request_id
            FROM pull_requests
            WHERE pull_request_number = 101
        )
    )
    LIMIT 1
)
SELECT
    CASE
        WHEN NOT eligible THEN
            pg_catalog.raise_exception(
                'Pull Request is not eligible for merge'
            )
        ELSE TRUE
    END
FROM eligible;

INSERT INTO merge_events(
    pull_request_id,
    merged_by_user_id,
    strategy,
    merge_commit_id
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'squash',
    c.commit_id
FROM pull_requests pr
JOIN users u
  ON u.username = 'release-manager'
JOIN commits c
  ON c.commit_sha = 'abcdef7654321'
WHERE pr.pull_request_number = 101;

UPDATE pull_requests
SET
    state = 'merged',
    merged_at = CURRENT_TIMESTAMP
WHERE pull_request_number = 101;

COMMIT;

-- Final workflow state.
SELECT
    pr.pull_request_number,
    pr.title,
    pr.state,
    COUNT(DISTINCT r.review_id) AS reviews,
    COUNT(DISTINCT pc.commit_id) AS commits,
    COUNT(DISTINCT c.conversation_id)
        FILTER (WHERE NOT c.resolved) AS unresolved_conversations,
    COUNT(DISTINCT sc.status_check_id)
        FILTER (WHERE sc.state = 'passing') AS passing_checks
FROM pull_requests pr
LEFT JOIN reviews r
  ON r.pull_request_id = pr.pull_request_id
LEFT JOIN pull_request_commits pc
  ON pc.pull_request_id = pr.pull_request_id
LEFT JOIN conversations c
  ON c.pull_request_id = pr.pull_request_id
LEFT JOIN status_checks sc
  ON sc.pull_request_id = pr.pull_request_id
WHERE pr.pull_request_number = 101
GROUP BY
    pr.pull_request_number,
    pr.title,
    pr.state;
