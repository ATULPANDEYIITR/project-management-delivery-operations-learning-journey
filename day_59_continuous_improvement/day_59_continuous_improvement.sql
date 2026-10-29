DROP SCHEMA IF EXISTS continuous_improvement CASCADE;
CREATE SCHEMA continuous_improvement;

SET search_path TO continuous_improvement, public;

CREATE TYPE repository_role AS ENUM (
    'developer',
    'reviewer',
    'maintainer',
    'administrator'
);

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
    'success',
    'failure'
);

CREATE TYPE merge_strategy AS ENUM (
    'merge_commit',
    'squash',
    'rebase'
);

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(name)) BETWEEN 2 AND 100)
);

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (username ~ '^[A-Za-z0-9_.-]{2,50}$')
);

CREATE TABLE repository_members (
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE CASCADE,
    role repository_role NOT NULL,
    PRIMARY KEY (repository_id, user_id)
);

CREATE TABLE branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMPTZ,
    UNIQUE (repository_id, name),
    CHECK (length(trim(name)) BETWEEN 1 AND 255)
);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    sha VARCHAR(40) NOT NULL,
    message TEXT NOT NULL,
    author_id BIGINT NOT NULL REFERENCES users(user_id),
    parent_commit_id BIGINT REFERENCES commits(commit_id),
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (branch_id, sha),
    CHECK (sha ~ '^[A-Fa-f0-9]{7,40}$'),
    CHECK (length(trim(message)) > 0)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    author_id BIGINT NOT NULL REFERENCES users(user_id),
    state pull_request_state NOT NULL DEFAULT 'open',
    is_draft BOOLEAN NOT NULL DEFAULT false,
    head_commit_id BIGINT REFERENCES commits(commit_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) > 0),
    CHECK (
        (state = 'merged' AND merged_at IS NOT NULL)
        OR state <> 'merged'
    )
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    sequence_no INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, sequence_no),
    CHECK (sequence_no > 0)
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES users(user_id),
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id),
    state review_state NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES users(user_id),
    file_path TEXT,
    line_number INTEGER,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(body)) > 0),
    CHECK (line_number IS NULL OR line_number > 0)
);

CREATE TABLE conversations (
    conversation_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    opened_by BIGINT NOT NULL REFERENCES users(user_id),
    subject TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT false,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    CHECK (
        (resolved = false AND resolved_at IS NULL)
        OR (resolved = true AND resolved_at IS NOT NULL)
    )
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id),
    state check_state NOT NULL,
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name, commit_id)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 0,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT true,
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT true,
    require_linear_history BOOLEAN NOT NULL DEFAULT false,
    allow_direct_push BOOLEAN NOT NULL DEFAULT false,
    allow_force_push BOOLEAN NOT NULL DEFAULT false,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (required_approvals >= 0)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL REFERENCES branch_protection_policies(policy_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name)
);

CREATE TABLE merge_events (
    merge_event_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    merged_by BIGINT NOT NULL REFERENCES users(user_id),
    strategy merge_strategy NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_pr_target_state
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_commit_state
    ON reviews(pull_request_id, commit_id, state);

CREATE INDEX idx_checks_pr_commit
    ON status_checks(pull_request_id, commit_id);

CREATE INDEX idx_conversations_open
    ON conversations(pull_request_id)
    WHERE resolved = false;

CREATE INDEX idx_pr_commits_sequence
    ON pull_request_commits(pull_request_id, sequence_no);

CREATE OR REPLACE FUNCTION prevent_self_approval()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    pr_author BIGINT;
BEGIN
    SELECT author_id
    INTO pr_author
    FROM pull_requests
    WHERE pull_request_id = NEW.pull_request_id;

    IF NEW.state = 'approved' AND NEW.reviewer_id = pr_author THEN
        RAISE EXCEPTION 'Pull request authors cannot approve their own changes';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_self_approval
BEFORE INSERT OR UPDATE ON reviews
FOR EACH ROW
EXECUTE FUNCTION prevent_self_approval();

CREATE OR REPLACE FUNCTION refresh_pull_request_timestamp()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_refresh_pr_timestamp
BEFORE UPDATE ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION refresh_pull_request_timestamp();

CREATE OR REPLACE FUNCTION check_merge_state_consistency()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state = 'merged' AND NEW.head_commit_id IS NULL THEN
        RAISE EXCEPTION 'A merged pull request must have a head commit';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_merge_state_consistency
BEFORE INSERT OR UPDATE ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION check_merge_state_consistency();

CREATE OR REPLACE FUNCTION merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    pr RECORD;
    policy RECORD;
    approval_count INTEGER;
    unresolved_count INTEGER;
    missing_checks INTEGER;
BEGIN
    SELECT *
    INTO pr
    FROM pull_requests
    WHERE pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 'Pull request does not exist';
        RETURN;
    END IF;

    IF pr.state <> 'open' THEN
        RETURN QUERY SELECT false, 'Pull request is not open';
    END IF;

    IF pr.is_draft THEN
        RETURN QUERY SELECT false, 'Pull request is a draft';
    END IF;

    SELECT bp.*
    INTO policy
    FROM branch_protection_policies bp
    WHERE bp.branch_id = pr.target_branch_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT true, 'No branch protection policy blocks merge';
        RETURN;
    END IF;

    SELECT count(DISTINCT reviewer_id)
    INTO approval_count
    FROM reviews
    WHERE pull_request_id = p_pull_request_id
      AND state = 'approved'
      AND commit_id = pr.head_commit_id
      AND reviewer_id <> pr.author_id;

    IF approval_count < policy.required_approvals THEN
        RETURN QUERY SELECT
            false,
            format(
                'Required approvals: %s; current approvals: %s',
                policy.required_approvals,
                approval_count
            );
    END IF;

    SELECT count(*)
    INTO unresolved_count
    FROM conversations
    WHERE pull_request_id = p_pull_request_id
      AND resolved = false;

    IF policy.require_conversation_resolution
       AND unresolved_count > 0 THEN
        RETURN QUERY SELECT
            false,
            format(
                'Unresolved conversations: %s',
                unresolved_count
            );
    END IF;

    SELECT count(*)
    INTO missing_checks
    FROM required_status_checks rsc
    WHERE rsc.policy_id = policy.policy_id
      AND NOT EXISTS (
          SELECT 1
          FROM status_checks sc
          WHERE sc.pull_request_id = p_pull_request_id
            AND sc.check_name = rsc.check_name
            AND sc.commit_id = pr.head_commit_id
            AND sc.state = 'success'
      );

    IF missing_checks > 0 THEN
        RETURN QUERY SELECT
            false,
            format(
                'Missing or unsuccessful required checks: %s',
                missing_checks
            );
    END IF;

    RETURN QUERY SELECT true, 'All merge conditions satisfied';
END;
$$;

CREATE OR REPLACE VIEW pull_request_governance_report AS
SELECT
    pr.pull_request_id,
    r.name AS repository,
    pr.number,
    pr.title,
    sb.name AS source_branch,
    tb.name AS target_branch,
    pr.state,
    pr.is_draft,
    u.username AS author,
    pr.created_at,
    pr.updated_at,
    pr.merged_at,
    COALESCE((
        SELECT count(DISTINCT rv.reviewer_id)
        FROM reviews rv
        WHERE rv.pull_request_id = pr.pull_request_id
          AND rv.state = 'approved'
          AND rv.commit_id = pr.head_commit_id
          AND rv.reviewer_id <> pr.author_id
    ), 0) AS current_approvals,
    COALESCE((
        SELECT count(*)
        FROM conversations c
        WHERE c.pull_request_id = pr.pull_request_id
          AND c.resolved = false
    ), 0) AS unresolved_conversations,
    COALESCE((
        SELECT count(*)
        FROM status_checks sc
        WHERE sc.pull_request_id = pr.pull_request_id
          AND sc.commit_id = pr.head_commit_id
          AND sc.state = 'success'
    ), 0) AS successful_checks
FROM pull_requests pr
JOIN repositories r ON r.repository_id = pr.repository_id
JOIN branches sb ON sb.branch_id = pr.source_branch_id
JOIN branches tb ON tb.branch_id = pr.target_branch_id
JOIN users u ON u.user_id = pr.author_id;

INSERT INTO repositories (name, default_branch)
VALUES ('continuous-improvement-platform', 'main');

INSERT INTO users (username, display_name)
VALUES
    ('platform', 'Platform Engineering'),
    ('developer1', 'Developer One'),
    ('developer2', 'Developer Two'),
    ('reviewer1', 'Reviewer One'),
    ('reviewer2', 'Reviewer Two'),
    ('security', 'Security Reviewer');

INSERT INTO branches (repository_id, name, protected)
SELECT repository_id, 'main', true
FROM repositories
WHERE name = 'continuous-improvement-platform';

INSERT INTO branches (repository_id, name)
SELECT repository_id, 'improvement/cycle-time'
FROM repositories
WHERE name = 'continuous-improvement-platform';

INSERT INTO branches (repository_id, name)
SELECT repository_id, 'improvement/review-quality'
FROM repositories
WHERE name = 'continuous-improvement-platform';

INSERT INTO repository_members (repository_id, user_id, role)
SELECT r.repository_id, u.user_id, x.role
FROM repositories r
CROSS JOIN (
    VALUES
        ('platform', 'administrator'::repository_role),
        ('developer1', 'developer'::repository_role),
        ('developer2', 'developer'::repository_role),
        ('reviewer1', 'reviewer'::repository_role),
        ('reviewer2', 'reviewer'::repository_role),
        ('security', 'reviewer'::repository_role)
) AS x(username, role)
JOIN users u ON u.username = x.username
WHERE r.name = 'continuous-improvement-platform';

INSERT INTO commits (
    branch_id,
    sha,
    message,
    author_id
)
SELECT
    b.branch_id,
    'a100001',
    'Establish repository baseline',
    u.user_id
FROM branches b
JOIN users u ON u.username = 'platform'
WHERE b.name = 'main';

INSERT INTO commits (
    branch_id,
    sha,
    message,
    author_id
)
SELECT
    b.branch_id,
    'b100001',
    'Measure pull request cycle time',
    u.user_id
FROM branches b
JOIN users u ON u.username = 'developer1'
WHERE b.name = 'improvement/cycle-time';

INSERT INTO commits (
    branch_id,
    sha,
    message,
    author_id
)
SELECT
    b.branch_id,
    'b100002',
    'Add process metrics',
    u.user_id
FROM branches b
JOIN users u ON u.username = 'developer1'
WHERE b.name = 'improvement/cycle-time';

INSERT INTO commits (
    branch_id,
    sha,
    message,
    author_id
)
SELECT
    b.branch_id,
    'c100001',
    'Measure review turnaround',
    u.user_id
FROM branches b
JOIN users u ON u.username = 'developer2'
WHERE b.name = 'improvement/review-quality';

INSERT INTO branch_protection_policies (
    branch_id,
    required_approvals,
    require_conversation_resolution,
    dismiss_stale_approvals,
    require_linear_history,
    allow_direct_push,
    allow_force_push,
    allow_branch_deletion
)
SELECT
    branch_id,
    2,
    true,
    true,
    true,
    false,
    false,
    false
FROM branches
WHERE name = 'main';

INSERT INTO required_status_checks (policy_id, check_name)
SELECT policy_id, 'unit-tests'
FROM branch_protection_policies;

INSERT INTO required_status_checks (policy_id, check_name)
SELECT policy_id, 'security-scan'
FROM branch_protection_policies;

INSERT INTO pull_requests (
    repository_id,
    number,
    title,
    source_branch_id,
    target_branch_id,
    author_id,
    state,
    is_draft,
    head_commit_id
)
SELECT
    r.repository_id,
    1,
    'Reduce pull request cycle time',
    source.branch_id,
    target.branch_id,
    author.user_id,
    'open',
    false,
    head.commit_id
FROM repositories r
JOIN branches source
    ON source.repository_id = r.repository_id
   AND source.name = 'improvement/cycle-time'
JOIN branches target
    ON target.repository_id = r.repository_id
   AND target.name = 'main'
JOIN users author ON author.username = 'developer1'
JOIN commits head
    ON head.branch_id = source.branch_id
   AND head.sha = 'b100002'
WHERE r.name = 'continuous-improvement-platform';

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_id,
    sequence_no
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    row_number() OVER (ORDER BY c.committed_at)
FROM pull_requests pr
JOIN branches b ON b.branch_id = pr.source_branch_id
JOIN commits c ON c.branch_id = b.branch_id
WHERE pr.number = 1;

INSERT INTO conversations (
    pull_request_id,
    opened_by,
    subject
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'Clarify baseline metric'
FROM pull_requests pr
JOIN users u ON u.username = 'reviewer1'
WHERE pr.number = 1;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    commit_id,
    state,
    body
)
SELECT
    pr.pull_request_id,
    u.user_id,
    pr.head_commit_id,
    'approved',
    'Metrics are structurally sound.'
FROM pull_requests pr
JOIN users u ON u.username = 'reviewer1'
WHERE pr.number = 1;

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    commit_id,
    state,
    body
)
SELECT
    pr.pull_request_id,
    u.user_id,
    pr.head_commit_id,
    'changes_requested',
    'Please clarify the baseline definition.'
FROM pull_requests pr
JOIN users u ON u.username = 'reviewer2'
WHERE pr.number = 1;

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    commit_id,
    state,
    completed_at
)
SELECT
    pr.pull_request_id,
    check_name,
    pr.head_commit_id,
    'success',
    now()
FROM pull_requests pr
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS checks(check_name)
WHERE pr.number = 1;

-- Initial evaluation: one approval plus one unresolved conversation.
SELECT *
FROM merge_eligibility(
    (SELECT pull_request_id FROM pull_requests WHERE number = 1)
);

UPDATE conversations
SET resolved = true,
    resolved_at = now()
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE number = 1
);

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    commit_id,
    state,
    body
)
SELECT
    pr.pull_request_id,
    u.user_id,
    pr.head_commit_id,
    'approved',
    'Clarification accepted.'
FROM pull_requests pr
JOIN users u ON u.username = 'reviewer2'
WHERE pr.number = 1;

-- The PR now satisfies the configured approval and status-check rules.
SELECT *
FROM merge_eligibility(
    (SELECT pull_request_id FROM pull_requests WHERE number = 1)
);

-- Reporting query for process improvement metrics.
SELECT
    repository,
    target_branch,
    count(*) AS pull_requests,
    count(*) FILTER (WHERE state = 'merged') AS merged_pull_requests,
    round(
        avg(
            EXTRACT(EPOCH FROM (COALESCE(merged_at, now()) - created_at))
            / 3600
        ),
        2
    ) AS average_cycle_hours,
    avg(current_approvals)::numeric(10,2) AS average_current_approvals,
    avg(unresolved_conversations)::numeric(10,2)
        AS average_unresolved_conversations
FROM pull_request_governance_report
GROUP BY repository, target_branch;

-- Transactional merge simulation. The transaction updates the PR and records
-- the governance decision as one atomic operation.
BEGIN;

WITH eligibility AS (
    SELECT *
    FROM merge_eligibility(
        (SELECT pull_request_id
         FROM pull_requests
         WHERE number = 1)
    )
)
SELECT *
FROM eligibility;

UPDATE pull_requests
SET state = 'merged',
    merged_at = now()
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE number = 1
)
AND EXISTS (
    SELECT 1
    FROM merge_eligibility(
        (SELECT pull_request_id
         FROM pull_requests
         WHERE number = 1)
    )
    WHERE eligible
);

INSERT INTO merge_events (
    pull_request_id,
    merged_by,
    strategy
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'squash'
FROM pull_requests pr
JOIN users u ON u.username = 'platform'
WHERE pr.number = 1
  AND pr.state = 'merged'
ON CONFLICT (pull_request_id) DO NOTHING;

COMMIT;

-- Final governance state.
SELECT *
FROM pull_request_governance_report
ORDER BY pull_request_id;

-- Failure case: direct self-approval is rejected by the database trigger.
DO $$
DECLARE
    pr_id BIGINT;
    author_id BIGINT;
    head_id BIGINT;
BEGIN
    SELECT pull_request_id, author_id, head_commit_id
    INTO pr_id, author_id, head_id
    FROM pull_requests
    WHERE number = 1;

    BEGIN
        INSERT INTO reviews (
            pull_request_id,
            reviewer_id,
            commit_id,
            state,
            body
        )
        VALUES (
            pr_id,
            author_id,
            head_id,
            'approved',
            'Invalid self-approval attempt'
        );
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected validation failure: %', SQLERRM;
    END;
END;
$$;
