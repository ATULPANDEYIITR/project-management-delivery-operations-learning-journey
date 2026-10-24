BEGIN;

CREATE SCHEMA IF NOT EXISTS repository_quality;
SET search_path TO repository_quality, public;

CREATE TYPE pr_state AS ENUM ('open', 'merged', 'closed');
CREATE TYPE review_state AS ENUM (
    'commented', 'approved', 'changes_requested', 'dismissed'
);
CREATE TYPE check_state AS ENUM ('pending', 'passed', 'failed');
CREATE TYPE merge_strategy AS ENUM ('merge_commit', 'squash', 'rebase');

CREATE TABLE repository (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(name)) > 0)
);

CREATE TABLE repository_member (
    repository_id BIGINT NOT NULL REFERENCES repository ON DELETE CASCADE,
    username TEXT NOT NULL,
    role TEXT NOT NULL CHECK (
        role IN ('developer', 'reviewer', 'maintainer', 'administrator')
    ),
    active BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY (repository_id, username),
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE branch (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository ON DELETE CASCADE,
    name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMPTZ,
    UNIQUE (repository_id, name),
    UNIQUE (repository_id, branch_id),
    CHECK (length(trim(name)) > 0)
);

CREATE TABLE commit_record (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository ON DELETE CASCADE,
    external_hash TEXT NOT NULL,
    author TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, external_hash),
    UNIQUE (repository_id, commit_id),
    CHECK (length(trim(external_hash)) > 0),
    CHECK (length(trim(author)) > 0),
    CHECK (length(trim(message)) > 0)
);

CREATE TABLE branch_commit (
    branch_id BIGINT NOT NULL REFERENCES branch ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commit_record ON DELETE RESTRICT,
    position INTEGER NOT NULL CHECK (position > 0),
    PRIMARY KEY (branch_id, position),
    UNIQUE (branch_id, commit_id)
);

CREATE TABLE pull_request (
    pr_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository ON DELETE CASCADE,
    number INTEGER NOT NULL CHECK (number > 0),
    author TEXT NOT NULL,
    source_branch_id BIGINT NOT NULL,
    target_branch_id BIGINT NOT NULL,
    state pr_state NOT NULL DEFAULT 'open',
    is_draft BOOLEAN NOT NULL DEFAULT true,
    base_head_at_creation TEXT,
    merged_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    merge_commit_id BIGINT REFERENCES commit_record ON DELETE RESTRICT,
    strategy merge_strategy,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, number),
    UNIQUE (repository_id, pr_id),
    FOREIGN KEY (repository_id, source_branch_id)
        REFERENCES branch(repository_id, branch_id),
    FOREIGN KEY (repository_id, target_branch_id)
        REFERENCES branch(repository_id, branch_id),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (
        (state = 'merged' AND merged_at IS NOT NULL AND merge_commit_id IS NOT NULL)
        OR
        (state <> 'merged' AND merged_at IS NULL AND merge_commit_id IS NULL)
    )
);

CREATE TABLE review (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL REFERENCES pull_request ON DELETE CASCADE,
    reviewer TEXT NOT NULL,
    state review_state NOT NULL,
    reviewed_external_hash TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pr_id, review_id),
    CHECK (length(trim(reviewer)) > 0),
    CHECK (length(trim(reviewed_external_hash)) > 0)
);

CREATE TABLE review_comment (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES review ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(file_path)) > 0),
    CHECK (length(trim(body)) > 0)
);

CREATE TABLE conversation (
    conversation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL REFERENCES pull_request ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER CHECK (line_number > 0),
    opened_by TEXT NOT NULL,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT false,
    resolved_by TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(file_path)) > 0),
    CHECK (length(trim(opened_by)) > 0),
    CHECK (length(trim(body)) > 0),
    CHECK (
        (resolved = false AND resolved_by IS NULL AND resolved_at IS NULL)
        OR
        (resolved = true AND resolved_by IS NOT NULL AND resolved_at IS NOT NULL)
    )
);

CREATE TABLE status_check (
    check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL REFERENCES pull_request ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    external_hash TEXT NOT NULL,
    state check_state NOT NULL,
    details TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pr_id, check_name, external_hash),
    CHECK (length(trim(check_name)) > 0),
    CHECK (length(trim(external_hash)) > 0)
);

CREATE TABLE branch_protection_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branch ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 2
        CHECK (required_approvals >= 0),
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT true,
    require_linear_history BOOLEAN NOT NULL DEFAULT true,
    allow_direct_push BOOLEAN NOT NULL DEFAULT false,
    allow_force_push BOOLEAN NOT NULL DEFAULT false,
    allow_deletion BOOLEAN NOT NULL DEFAULT false,
    allow_admin_bypass BOOLEAN NOT NULL DEFAULT false,
    require_up_to_date_base BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE required_status_check (
    policy_id BIGINT NOT NULL REFERENCES branch_protection_policy ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name),
    CHECK (length(trim(check_name)) > 0)
);

CREATE INDEX idx_pr_target_state
    ON pull_request(target_branch_id, state);

CREATE INDEX idx_review_pr_time
    ON review(pr_id, submitted_at DESC);

CREATE INDEX idx_conversation_unresolved
    ON conversation(pr_id) WHERE resolved = false;

CREATE INDEX idx_status_check_pr_name
    ON status_check(pr_id, check_name, updated_at DESC);

CREATE INDEX idx_branch_commit_commit
    ON branch_commit(commit_id);

-- Enforce active repository membership and prohibit self-approval at insertion.
CREATE OR REPLACE FUNCTION validate_review_submission()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    pr pull_request%ROWTYPE;
    source_head TEXT;
    reviewer_role TEXT;
BEGIN
    SELECT * INTO pr
    FROM pull_request
    WHERE pr_id = NEW.pr_id
    FOR UPDATE;

    IF NOT FOUND OR pr.state <> 'open' OR pr.is_draft THEN
        RAISE EXCEPTION 'Reviews require an open, review-ready PR';
    END IF;

    IF NEW.reviewer = pr.author THEN
        RAISE EXCEPTION 'Self-review is prohibited';
    END IF;

    SELECT role INTO reviewer_role
    FROM repository_member
    WHERE repository_id = pr.repository_id
      AND username = NEW.reviewer
      AND active = true;

    IF reviewer_role IS NULL OR reviewer_role NOT IN (
        'reviewer', 'maintainer', 'administrator'
    ) THEN
        RAISE EXCEPTION 'Reviewer is not eligible';
    END IF;

    SELECT c.external_hash INTO source_head
    FROM branch_commit bc
    JOIN commit_record c ON c.commit_id = bc.commit_id
    WHERE bc.branch_id = pr.source_branch_id
    ORDER BY bc.position DESC
    LIMIT 1;

    IF source_head IS NULL OR source_head <> NEW.reviewed_external_hash THEN
        RAISE EXCEPTION 'Review must reference the current source HEAD';
    END IF;

    IF NEW.state = 'dismissed' THEN
        RAISE EXCEPTION 'A dismissed review cannot be newly submitted';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_review_submission
BEFORE INSERT ON review
FOR EACH ROW EXECUTE FUNCTION validate_review_submission();

CREATE OR REPLACE FUNCTION validate_conversation_resolution()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    repository_key BIGINT;
    actor_role TEXT;
BEGIN
    IF NEW.resolved AND (
        TG_OP = 'INSERT' OR OLD.resolved = false
    ) THEN
        SELECT p.repository_id INTO repository_key
        FROM pull_request p
        WHERE p.pr_id = NEW.pr_id;

        SELECT role INTO actor_role
        FROM repository_member
        WHERE repository_id = repository_key
          AND username = NEW.resolved_by
          AND active = true;

        IF actor_role IS NULL OR actor_role NOT IN (
            'reviewer', 'maintainer', 'administrator'
        ) THEN
            RAISE EXCEPTION 'Conversation resolver is not authorized';
        END IF;

        NEW.resolved_at := now();
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_conversation_resolution
BEFORE INSERT OR UPDATE ON conversation
FOR EACH ROW EXECUTE FUNCTION validate_conversation_resolution();

-- Evaluation is advisory. The merge function below locks the PR and rechecks
-- eligibility inside a transaction to prevent stale evaluations from authorizing a merge.
CREATE OR REPLACE FUNCTION evaluate_merge(p_pr_id BIGINT)
RETURNS TABLE(blocker TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    pr pull_request%ROWTYPE;
    policy branch_protection_policy%ROWTYPE;
    source_head TEXT;
    target_head TEXT;
    approvals INTEGER;
    current_hashes TEXT[];
    required_check TEXT;
BEGIN
    SELECT * INTO pr FROM pull_request WHERE pr_id = p_pr_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT 'Pull request does not exist'::TEXT;
        RETURN;
    END IF;

    IF pr.state <> 'open' THEN
        RETURN QUERY SELECT 'Pull request is not open'::TEXT;
        RETURN;
    END IF;

    SELECT * INTO policy
    FROM branch_protection_policy
    WHERE branch_id = pr.target_branch_id;

    IF NOT FOUND THEN
        -- An unprotected target still needs the workflow's ordinary checks,
        -- but no repository-specific policy is applied.
        RETURN QUERY SELECT 'Target branch has no protection policy'::TEXT;
        RETURN;
    END IF;

    IF pr.is_draft THEN
        RETURN QUERY SELECT 'Pull request is a draft'::TEXT;
    END IF;

    SELECT c.external_hash INTO source_head
    FROM branch_commit bc
    JOIN commit_record c ON c.commit_id = bc.commit_id
    WHERE bc.branch_id = pr.source_branch_id
    ORDER BY bc.position DESC
    LIMIT 1;

    SELECT c.external_hash INTO target_head
    FROM branch_commit bc
    JOIN commit_record c ON c.commit_id = bc.commit_id
    WHERE bc.branch_id = pr.target_branch_id
    ORDER BY bc.position DESC
    LIMIT 1;

    IF source_head IS NULL THEN
        RETURN QUERY SELECT 'Source branch has no commits'::TEXT;
    END IF;

    IF policy.require_up_to_date_base
       AND pr.base_head_at_creation IS DISTINCT FROM target_head THEN
        RETURN QUERY SELECT 'Target branch changed; synchronize the base'::TEXT;
    END IF;

    SELECT count(*) INTO approvals
    FROM (
        SELECT DISTINCT ON (r.reviewer)
            r.reviewer, r.state, r.reviewed_external_hash
        FROM review r
        WHERE r.pr_id = p_pr_id
        ORDER BY r.reviewer, r.submitted_at DESC, r.review_id DESC
    ) latest
    WHERE latest.state = 'approved'
      AND latest.reviewed_external_hash = source_head;

    IF approvals < policy.required_approvals THEN
        RETURN QUERY SELECT format(
            'Requires %s current approvals; has %s',
            policy.required_approvals, approvals
        );
    END IF;

    IF EXISTS (
        SELECT 1
        FROM (
            SELECT DISTINCT ON (r.reviewer)
                r.state, r.reviewed_external_hash
            FROM review r
            WHERE r.pr_id = p_pr_id
            ORDER BY r.reviewer, r.submitted_at DESC, r.review_id DESC
        ) latest
        WHERE latest.state = 'changes_requested'
          AND latest.reviewed_external_hash = source_head
    ) THEN
        RETURN QUERY SELECT 'A current review requests changes'::TEXT;
    END IF;

    FOR required_check IN
        SELECT rsc.check_name
        FROM required_status_check rsc
        WHERE rsc.policy_id = policy.policy_id
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM status_check sc
            WHERE sc.pr_id = p_pr_id
              AND sc.check_name = required_check
              AND sc.external_hash = source_head
              AND sc.state = 'passed'
        ) THEN
            RETURN QUERY SELECT format(
                'Required check %s is absent, failed, or stale',
                required_check
            );
        END IF;
    END LOOP;

    IF policy.require_resolved_conversations AND EXISTS (
        SELECT 1 FROM conversation c
        WHERE c.pr_id = p_pr_id AND NOT c.resolved
    ) THEN
        RETURN QUERY SELECT 'Unresolved review conversations remain'::TEXT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM branch
        WHERE branch_id = pr.target_branch_id
          AND protected = true
    ) THEN
        RETURN QUERY SELECT 'Target branch is not marked protected'::TEXT;
    END IF;

    RETURN;
END;
$$;

CREATE OR REPLACE FUNCTION merge_pull_request(
    p_pr_id BIGINT,
    p_actor TEXT,
    p_strategy merge_strategy
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    pr pull_request%ROWTYPE;
    new_commit_id BIGINT;
    source_head TEXT;
    target_head TEXT;
    blockers TEXT;
    actor_role TEXT;
BEGIN
    SELECT * INTO pr
    FROM pull_request
    WHERE pr_id = p_pr_id
    FOR UPDATE;

    IF NOT FOUND OR pr.state <> 'open' THEN
        RAISE EXCEPTION 'Pull request is missing or not open';
    END IF;

    SELECT role INTO actor_role
    FROM repository_member
    WHERE repository_id = pr.repository_id
      AND username = p_actor
      AND active = true;

    IF actor_role IS NULL OR actor_role NOT IN ('maintainer', 'administrator') THEN
        RAISE EXCEPTION 'Actor is not authorized to merge';
    END IF;

    SELECT string_agg(blocker, '; ') INTO blockers
    FROM evaluate_merge(p_pr_id);

    IF blockers IS NOT NULL THEN
        RAISE EXCEPTION 'Merge blocked: %', blockers;
    END IF;

    SELECT c.external_hash INTO source_head
    FROM branch_commit bc
    JOIN commit_record c ON c.commit_id = bc.commit_id
    WHERE bc.branch_id = pr.source_branch_id
    ORDER BY bc.position DESC
    LIMIT 1;

    SELECT c.external_hash INTO target_head
    FROM branch_commit bc
    JOIN commit_record c ON c.commit_id = bc.commit_id
    WHERE bc.branch_id = pr.target_branch_id
    ORDER BY bc.position DESC
    LIMIT 1;

    INSERT INTO commit_record(repository_id, external_hash, author, message)
    VALUES (
        pr.repository_id,
        'merge-' || pr.number || '-' || txid_current(),
        p_actor,
        'Merge PR #' || pr.number || ' using ' || p_strategy
    )
    RETURNING commit_id INTO new_commit_id;

    INSERT INTO branch_commit(branch_id, commit_id, position)
    SELECT pr.target_branch_id, new_commit_id,
           COALESCE(MAX(position), 0) + 1
    FROM branch_commit
    WHERE branch_id = pr.target_branch_id;

    UPDATE pull_request
    SET state = 'merged',
        merged_at = now(),
        merge_commit_id = new_commit_id,
        strategy = p_strategy,
        updated_at = now()
    WHERE pr_id = p_pr_id;

    RETURN new_commit_id;
END;
$$;

CREATE VIEW pull_request_quality_report AS
SELECT
    p.pr_id,
    r.name AS repository_name,
    p.number,
    p.author,
    p.state,
    p.is_draft,
    source_branch.name AS source_branch,
    target_branch.name AS target_branch,
    (
        SELECT count(*)
        FROM conversation c
        WHERE c.pr_id = p.pr_id AND NOT c.resolved
    ) AS unresolved_conversations,
    (
        SELECT count(*)
        FROM (
            SELECT DISTINCT ON (rv.reviewer)
                rv.reviewer, rv.state, rv.reviewed_external_hash
            FROM review rv
            WHERE rv.pr_id = p.pr_id
            ORDER BY rv.reviewer, rv.submitted_at DESC, rv.review_id DESC
        ) latest
        WHERE latest.state = 'approved'
          AND latest.reviewed_external_hash = (
              SELECT cr.external_hash
              FROM branch_commit bc
              JOIN commit_record cr ON cr.commit_id = bc.commit_id
              WHERE bc.branch_id = p.source_branch_id
              ORDER BY bc.position DESC LIMIT 1
          )
    ) AS current_approvals
FROM pull_request p
JOIN repository r ON r.repository_id = p.repository_id
JOIN branch source_branch ON source_branch.branch_id = p.source_branch_id
JOIN branch target_branch ON target_branch.branch_id = p.target_branch_id;

-- Seed data: a protected production branch and a reviewable feature branch.
INSERT INTO repository(name) VALUES ('quality-service');

INSERT INTO repository_member(repository_id, username, role)
SELECT repository_id, username, role
FROM repository
CROSS JOIN (
    VALUES
        ('developer', 'developer'),
        ('reviewer-a', 'reviewer'),
        ('reviewer-b', 'reviewer'),
        ('maintainer', 'maintainer'),
        ('administrator', 'administrator')
) AS members(username, role)
WHERE name = 'quality-service';

INSERT INTO branch(repository_id, name, protected)
SELECT repository_id, 'main', true FROM repository
WHERE name = 'quality-service';

INSERT INTO branch(repository_id, name, protected)
SELECT repository_id, 'feature/quality-gates', false FROM repository
WHERE name = 'quality-service';

INSERT INTO branch_protection_policy(
    branch_id, required_approvals, require_resolved_conversations,
    require_linear_history, allow_direct_push, allow_force_push,
    allow_deletion, allow_admin_bypass, require_up_to_date_base
)
SELECT branch_id, 2, true, true, false, false, false, false, true
FROM branch WHERE name = 'main';

INSERT INTO required_status_check(policy_id, check_name)
SELECT policy_id, check_name
FROM branch_protection_policy
CROSS JOIN (VALUES ('unit-tests'), ('security-scan')) checks(check_name)
WHERE branch_id = (SELECT branch_id FROM branch WHERE name = 'main');

INSERT INTO commit_record(repository_id, external_hash, author, message)
SELECT repository_id, 'a100', 'maintainer', 'Initial production release'
FROM repository WHERE name = 'quality-service';

INSERT INTO branch_commit(branch_id, commit_id, position)
SELECT b.branch_id, c.commit_id, 1
FROM branch b
JOIN repository r ON r.repository_id = b.repository_id
JOIN commit_record c ON c.repository_id = r.repository_id
WHERE b.name = 'main' AND c.external_hash = 'a100';

INSERT INTO commit_record(repository_id, external_hash, author, message)
SELECT repository_id, 'f101', 'developer', 'Add request validation'
FROM repository WHERE name = 'quality-service';

INSERT INTO branch_commit(branch_id, commit_id, position)
SELECT b.branch_id, c.commit_id, 1
FROM branch b
JOIN repository r ON r.repository_id = b.repository_id
JOIN commit_record c ON c.repository_id = r.repository_id
WHERE b.name = 'feature/quality-gates' AND c.external_hash = 'f101';

INSERT INTO pull_request(
    repository_id, number, author, source_branch_id, target_branch_id,
    state, is_draft, base_head_at_creation
)
SELECT
    r.repository_id, 17, 'developer', src.branch_id, dst.branch_id,
    'open', false, 'a100'
FROM repository r
JOIN branch src ON src.repository_id = r.repository_id
JOIN branch dst ON dst.repository_id = r.repository_id
WHERE r.name = 'quality-service'
  AND src.name = 'feature/quality-gates'
  AND dst.name = 'main';

INSERT INTO review(pr_id, reviewer, state, reviewed_external_hash)
SELECT pr_id, 'reviewer-a', 'approved', 'f101'
FROM pull_request WHERE number = 17;

INSERT INTO review(pr_id, reviewer, state, reviewed_external_hash)
SELECT pr_id, 'reviewer-b', 'changes_requested', 'f101'
FROM pull_request WHERE number = 17;

INSERT INTO review_comment(review_id, file_path, line_number, body)
SELECT review_id, 'src/validator.py', 24, 'Reject blank identifiers.'
FROM review
WHERE reviewer = 'reviewer-b'
  AND pr_id = (SELECT pr_id FROM pull_request WHERE number = 17);

INSERT INTO conversation(
    pr_id, file_path, line_number, opened_by, body
)
SELECT pr_id, 'src/validator.py', 24, 'reviewer-b',
       'Please reject blank identifiers before processing.'
FROM pull_request WHERE number = 17;

INSERT INTO status_check(pr_id, check_name, external_hash, state)
SELECT pr_id, check_name, 'f101', 'passed'
FROM pull_request
CROSS JOIN (VALUES ('unit-tests'), ('security-scan')) checks(check_name)
WHERE number = 17;

-- 1. Inspect proposed changes and their current workflow state.
SELECT * FROM pull_request_quality_report;

-- 2. Inspect the exact merge blockers.
SELECT blocker FROM evaluate_merge(
    (SELECT pr_id FROM pull_request WHERE number = 17)
);

-- 3. Resolve the review discussion through an authorized repository member.
UPDATE conversation
SET resolved = true, resolved_by = 'maintainer'
WHERE pr_id = (SELECT pr_id FROM pull_request WHERE number = 17)
  AND resolved = false;

-- 4. Submit a second approval for the current source HEAD.
INSERT INTO review(pr_id, reviewer, state, reviewed_external_hash)
SELECT pr_id, 'reviewer-b', 'approved', 'f101'
FROM pull_request WHERE number = 17;

-- 5. The latest review by reviewer-b supersedes their earlier decision.
SELECT * FROM evaluate_merge(
    (SELECT pr_id FROM pull_request WHERE number = 17)
);

-- 6. Merge atomically after eligibility checks pass.
-- If any check fails, the exception aborts the transaction.
SELECT merge_pull_request(
    (SELECT pr_id FROM pull_request WHERE number = 17),
    'maintainer',
    'squash'
);

SELECT number, state, merged_at, strategy
FROM pull_request WHERE number = 17;

COMMIT;
