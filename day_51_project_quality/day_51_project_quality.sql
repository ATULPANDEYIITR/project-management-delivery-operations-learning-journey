DROP SCHEMA IF EXISTS project_quality_governance CASCADE;
CREATE SCHEMA project_quality_governance;
SET search_path = project_quality_governance, public;

-- The model deliberately separates:
-- Pull Requests = proposed change workflow
-- Code Reviews = evaluation and discussion
-- Approvals = review decisions
-- Branch Protection = repository-level merge enforcement

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
    'passed',
    'failed'
);

CREATE TYPE merge_strategy AS ENUM (
    'merge_commit',
    'squash',
    'rebase'
);

CREATE TYPE conversation_state AS ENUM (
    'open',
    'resolved'
);

CREATE TABLE repository (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(repository_name)) > 0)
);

CREATE TABLE repository_member (
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    username TEXT NOT NULL,
    role_name TEXT NOT NULL CHECK (
        role_name IN ('developer', 'reviewer', 'maintainer', 'administrator')
    ),
    PRIMARY KEY (repository_id, username)
);

CREATE TABLE branch (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    head_sha TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0),
    CHECK (length(trim(head_sha)) > 0)
);

CREATE UNIQUE INDEX one_default_branch_per_repository
    ON branch(repository_id)
    WHERE is_default;

CREATE TABLE commit (
    commit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    sha TEXT NOT NULL,
    author_username TEXT NOT NULL,
    commit_message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, sha),
    CHECK (length(trim(sha)) > 0),
    CHECK (length(trim(author_username)) > 0),
    CHECK (length(trim(commit_message)) > 0)
);

CREATE TABLE pull_request (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    author_username TEXT NOT NULL,
    source_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    state pull_request_state NOT NULL DEFAULT 'draft',
    base_sha_at_creation TEXT NOT NULL,
    current_base_sha TEXT NOT NULL,
    merge_strategy merge_strategy NOT NULL DEFAULT 'squash',
    merge_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CHECK (number > 0),
    CHECK (length(trim(title)) > 0),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (
        (state IN ('closed', 'merged') AND closed_at IS NOT NULL)
        OR state IN ('draft', 'open')
    )
);

CREATE TABLE pull_request_commit (
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commit(commit_id),
    commit_sequence INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, commit_sequence),
    CHECK (commit_sequence > 0)
);

CREATE TABLE review_request (
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    reviewer_username TEXT NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pull_request_id, reviewer_username),
    CHECK (length(trim(reviewer_username)) > 0)
);

CREATE TABLE code_review (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    reviewer_username TEXT NOT NULL,
    reviewed_commit_id BIGINT NOT NULL REFERENCES commit(commit_id),
    state review_state NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dismissed_at TIMESTAMPTZ,
    dismissal_reason TEXT,
    UNIQUE (review_id, pull_request_id),
    CHECK (
        (state = 'dismissed' AND dismissed_at IS NOT NULL)
        OR state <> 'dismissed'
    )
);

CREATE TABLE review_comment (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES code_review(review_id)
        ON DELETE CASCADE,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    author_username TEXT NOT NULL,
    file_path TEXT,
    line_number INTEGER,
    body TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(author_username)) > 0),
    CHECK (length(trim(body)) > 0),
    CHECK (line_number IS NULL OR line_number > 0)
);

CREATE TABLE status_check (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    commit_id BIGINT NOT NULL REFERENCES commit(commit_id),
    state check_state NOT NULL,
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name),
    CHECK (length(trim(check_name)) > 0),
    CHECK (
        (state = 'passed' AND completed_at IS NOT NULL)
        OR state <> 'passed'
    )
);

CREATE TABLE branch_protection (
    branch_id BIGINT PRIMARY KEY REFERENCES branch(branch_id)
        ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 0,
    dismiss_stale_reviews BOOLEAN NOT NULL DEFAULT TRUE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (required_reviews >= 0)
);

CREATE TABLE protected_merge_strategy (
    branch_id BIGINT NOT NULL REFERENCES branch_protection(branch_id)
        ON DELETE CASCADE,
    strategy merge_strategy NOT NULL,
    PRIMARY KEY (branch_id, strategy)
);

CREATE TABLE required_status_check (
    branch_id BIGINT NOT NULL REFERENCES branch_protection(branch_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (branch_id, check_name),
    CHECK (length(trim(check_name)) > 0)
);

CREATE TABLE approval_requirement (
    branch_id BIGINT NOT NULL REFERENCES branch_protection(branch_id)
        ON DELETE CASCADE,
    requirement_name TEXT NOT NULL,
    required_count INTEGER NOT NULL,
    PRIMARY KEY (branch_id, requirement_name),
    CHECK (required_count > 0)
);

CREATE TABLE branch_bypass (
    branch_id BIGINT NOT NULL REFERENCES branch_protection(branch_id)
        ON DELETE CASCADE,
    username TEXT NOT NULL,
    PRIMARY KEY (branch_id, username)
);

CREATE TABLE merge_event (
    merge_event_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_request(pull_request_id),
    merged_by TEXT NOT NULL,
    strategy merge_strategy NOT NULL,
    resulting_sha TEXT NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(merged_by)) > 0),
    CHECK (length(trim(resulting_sha)) > 0)
);

-- These indexes support common governance lookups rather than every column.
CREATE INDEX idx_pr_target_state
    ON pull_request(target_branch_id, state);

CREATE INDEX idx_pr_commit_sequence
    ON pull_request_commit(pull_request_id, commit_sequence DESC);

CREATE INDEX idx_review_pr_commit_state
    ON code_review(pull_request_id, reviewed_commit_id, state);

CREATE INDEX idx_review_comments_unresolved
    ON review_comment(pull_request_id)
    WHERE is_resolved = FALSE;

CREATE INDEX idx_status_check_pr
    ON status_check(pull_request_id, check_name);

CREATE OR REPLACE FUNCTION enforce_pull_request_author()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    source_repo BIGINT;
    target_repo BIGINT;
BEGIN
    SELECT repository_id
    INTO source_repo
    FROM branch
    WHERE branch_id = NEW.source_branch_id;

    SELECT repository_id
    INTO target_repo
    FROM branch
    WHERE branch_id = NEW.target_branch_id;

    IF source_repo IS NULL OR target_repo IS NULL THEN
        RAISE EXCEPTION 'Pull Request references a missing branch';
    END IF;

    IF source_repo <> target_repo OR source_repo <> NEW.repository_id THEN
        RAISE EXCEPTION 'Source, target, and Pull Request repository must match';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM repository_member
        WHERE repository_id = NEW.repository_id
          AND username = NEW.author_username
    ) IS FALSE THEN
        RAISE EXCEPTION 'Pull Request author is not a repository member';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_pull_request
BEFORE INSERT OR UPDATE ON pull_request
FOR EACH ROW
EXECUTE FUNCTION enforce_pull_request_author();

CREATE OR REPLACE FUNCTION enforce_review_reviewer()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    pr_author TEXT;
    repository_id_value BIGINT;
BEGIN
    SELECT author_username, repository_id
    INTO pr_author, repository_id_value
    FROM pull_request
    WHERE pull_request_id = NEW.pull_request_id;

    IF pr_author = NEW.reviewer_username THEN
        RAISE EXCEPTION 'Authors cannot submit their own review';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM repository_member
        WHERE repository_id = repository_id_value
          AND username = NEW.reviewer_username
          AND role_name IN ('reviewer', 'maintainer', 'administrator')
    ) THEN
        RAISE EXCEPTION 'Reviewer is not eligible for this repository';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_review_reviewer
BEFORE INSERT OR UPDATE ON code_review
FOR EACH ROW
EXECUTE FUNCTION enforce_review_reviewer();

CREATE OR REPLACE FUNCTION enforce_review_commit_belongs_to_pr()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pull_request_commit
        WHERE pull_request_id = NEW.pull_request_id
          AND commit_id = NEW.reviewed_commit_id
    ) THEN
        RAISE EXCEPTION
            'Review must reference a commit belonging to the Pull Request';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_review_commit
BEFORE INSERT OR UPDATE ON code_review
FOR EACH ROW
EXECUTE FUNCTION enforce_review_commit_belongs_to_pr();

CREATE OR REPLACE FUNCTION merge_eligibility(
    p_pull_request_id BIGINT,
    p_actor TEXT
)
RETURNS TABLE (
    allowed BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    pr RECORD;
    protection RECORD;
    latest_commit BIGINT;
    approval_count INTEGER;
    unresolved_count INTEGER;
    failed_check_count INTEGER;
    missing_check_count INTEGER;
    strategy_allowed BOOLEAN;
    bypass_allowed BOOLEAN;
BEGIN
    SELECT *
    INTO pr
    FROM pull_request
    WHERE pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Pull Request does not exist';
        RETURN;
    END IF;

    SELECT bp.*
    INTO protection
    FROM branch_protection bp
    WHERE bp.branch_id = pr.target_branch_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Target branch is not protected';
        RETURN;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM branch_bypass
        WHERE branch_id = pr.target_branch_id
          AND username = p_actor
    )
    INTO bypass_allowed;

    IF bypass_allowed THEN
        RETURN QUERY SELECT TRUE, 'Configured governance bypass permits merge';
        RETURN;
    END IF;

    IF pr.state <> 'open' THEN
        RETURN QUERY SELECT FALSE, 'Pull Request is not open';
    END IF;

    SELECT pc.commit_id
    INTO latest_commit
    FROM pull_request_commit pc
    WHERE pc.pull_request_id = p_pull_request_id
    ORDER BY pc.commit_sequence DESC
    LIMIT 1;

    IF latest_commit IS NULL THEN
        RETURN QUERY SELECT FALSE, 'Pull Request has no commits';
    END IF;

    IF pr.merge_conflicts THEN
        RETURN QUERY SELECT FALSE, 'Merge conflicts remain unresolved';
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM protected_merge_strategy pms
        WHERE pms.branch_id = pr.target_branch_id
          AND pms.strategy = pr.merge_strategy
    )
    INTO strategy_allowed;

    IF NOT strategy_allowed THEN
        RETURN QUERY SELECT FALSE, 'Selected merge strategy is not permitted';
    END IF;

    SELECT count(DISTINCT reviewer_username)
    INTO approval_count
    FROM code_review
    WHERE pull_request_id = p_pull_request_id
      AND reviewed_commit_id = latest_commit
      AND state = 'approved'
      AND reviewer_username <> pr.author_username
      AND NOT EXISTS (
          SELECT 1
          FROM code_review newer
          WHERE newer.pull_request_id = code_review.pull_request_id
            AND newer.reviewer_username = code_review.reviewer_username
            AND newer.submitted_at > code_review.submitted_at
            AND newer.state IN ('changes_requested', 'dismissed')
      );

    IF approval_count < protection.required_reviews THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   'Required approvals: %s; current approvals: %s',
                   protection.required_reviews,
                   approval_count
               );
    END IF;

    SELECT count(*)
    INTO missing_check_count
    FROM required_status_check required_check
    WHERE required_check.branch_id = pr.target_branch_id
      AND NOT EXISTS (
          SELECT 1
          FROM status_check check_result
          WHERE check_result.pull_request_id = p_pull_request_id
            AND check_result.check_name = required_check.check_name
            AND check_result.commit_id = latest_commit
            AND check_result.state = 'passed'
      );

    IF missing_check_count > 0 THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   '%s required status check(s) missing or not passed',
                   missing_check_count
               );
    END IF;

    SELECT count(*)
    INTO unresolved_count
    FROM review_comment
    WHERE pull_request_id = p_pull_request_id
      AND is_resolved = FALSE;

    IF protection.require_conversation_resolution
       AND unresolved_count > 0 THEN
        RETURN QUERY
        SELECT FALSE,
               format(
                   '%s unresolved review conversation(s)',
                   unresolved_count
               );
    END IF;

    IF protection.require_linear_history
       AND pr.merge_strategy = 'merge_commit' THEN
        RETURN QUERY
        SELECT FALSE,
               'Merge commit violates linear-history requirement';
    END IF;

    RETURN QUERY SELECT TRUE, 'All merge-eligibility conditions satisfied';
END;
$$;

CREATE OR REPLACE FUNCTION merge_pull_request(
    p_pull_request_id BIGINT,
    p_actor TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    decision RECORD;
    pr RECORD;
    latest_sha TEXT;
    result_sha TEXT;
BEGIN
    SELECT *
    INTO decision
    FROM merge_eligibility(p_pull_request_id, p_actor)
    WHERE allowed = FALSE
    LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION 'Merge blocked: %', decision.reason;
    END IF;

    SELECT *
    INTO pr
    FROM pull_request
    WHERE pull_request_id = p_pull_request_id
    FOR UPDATE;

    SELECT c.sha
    INTO latest_sha
    FROM pull_request_commit pc
    JOIN commit c ON c.commit_id = pc.commit_id
    WHERE pc.pull_request_id = p_pull_request_id
    ORDER BY pc.commit_sequence DESC
    LIMIT 1;

    result_sha :=
        'merge-' ||
        pr.number::TEXT ||
        '-' ||
        left(latest_sha, 8) ||
        '-' ||
        pr.merge_strategy::TEXT;

    UPDATE pull_request
    SET state = 'merged',
        closed_at = CURRENT_TIMESTAMP
    WHERE pull_request_id = p_pull_request_id;

    UPDATE branch
    SET head_sha = result_sha
    WHERE branch_id = pr.target_branch_id;

    INSERT INTO merge_event (
        pull_request_id,
        merged_by,
        strategy,
        resulting_sha
    )
    VALUES (
        p_pull_request_id,
        p_actor,
        pr.merge_strategy,
        result_sha
    );

    RETURN result_sha;
END;
$$;

CREATE VIEW current_pull_request_governance AS
WITH latest_commit AS (
    SELECT DISTINCT ON (pc.pull_request_id)
        pc.pull_request_id,
        pc.commit_id
    FROM pull_request_commit pc
    ORDER BY pc.pull_request_id, pc.commit_sequence DESC
),
approval_counts AS (
    SELECT
        cr.pull_request_id,
        count(DISTINCT cr.reviewer_username) AS approvals
    FROM code_review cr
    JOIN latest_commit lc
      ON lc.pull_request_id = cr.pull_request_id
     AND lc.commit_id = cr.reviewed_commit_id
    WHERE cr.state = 'approved'
    GROUP BY cr.pull_request_id
),
unresolved AS (
    SELECT
        pull_request_id,
        count(*) AS unresolved_comments
    FROM review_comment
    WHERE NOT is_resolved
    GROUP BY pull_request_id
)
SELECT
    pr.repository_id,
    pr.pull_request_id,
    pr.number,
    pr.title,
    pr.state,
    pr.author_username,
    source.branch_name AS source_branch,
    target.branch_name AS target_branch,
    pr.merge_strategy,
    COALESCE(ac.approvals, 0) AS current_approvals,
    bp.required_reviews,
    COALESCE(u.unresolved_comments, 0) AS unresolved_comments,
    pr.merge_conflicts
FROM pull_request pr
JOIN branch source
  ON source.branch_id = pr.source_branch_id
JOIN branch target
  ON target.branch_id = pr.target_branch_id
LEFT JOIN branch_protection bp
  ON bp.branch_id = pr.target_branch_id
LEFT JOIN approval_counts ac
  ON ac.pull_request_id = pr.pull_request_id
LEFT JOIN unresolved u
  ON u.pull_request_id = pr.pull_request_id;

CREATE VIEW protected_branch_report AS
SELECT
    r.repository_name,
    b.branch_name,
    bp.required_reviews,
    bp.dismiss_stale_reviews,
    bp.require_conversation_resolution,
    bp.restrict_direct_push,
    bp.allow_force_push,
    bp.allow_deletion,
    bp.require_linear_history,
    COALESCE(
        string_agg(DISTINCT pms.strategy::TEXT, ', '),
        'none'
    ) AS permitted_merge_strategies,
    COALESCE(
        string_agg(DISTINCT rsc.check_name, ', '),
        'none'
    ) AS required_status_checks
FROM branch b
JOIN repository r
  ON r.repository_id = b.repository_id
JOIN branch_protection bp
  ON bp.branch_id = b.branch_id
LEFT JOIN protected_merge_strategy pms
  ON pms.branch_id = b.branch_id
LEFT JOIN required_status_check rsc
  ON rsc.branch_id = b.branch_id
GROUP BY
    r.repository_name,
    b.branch_name,
    bp.required_reviews,
    bp.dismiss_stale_reviews,
    bp.require_conversation_resolution,
    bp.restrict_direct_push,
    bp.allow_force_push,
    bp.allow_deletion,
    bp.require_linear_history;

INSERT INTO repository (repository_name)
VALUES ('payments-platform');

INSERT INTO repository_member (repository_id, username, role_name)
SELECT repository_id, username, role_name
FROM (
    VALUES
        ('alice', 'developer'),
        ('bob', 'reviewer'),
        ('carol', 'reviewer'),
        ('diana', 'developer'),
        ('erin', 'reviewer'),
        ('frank', 'maintainer'),
        ('release-manager', 'maintainer')
) AS members(username, role_name)
CROSS JOIN repository
WHERE repository_name = 'payments-platform';

INSERT INTO branch (
    repository_id,
    branch_name,
    head_sha,
    is_default
)
SELECT repository_id, 'main', 'base-001', TRUE
FROM repository
WHERE repository_name = 'payments-platform';

INSERT INTO branch (
    repository_id,
    branch_name,
    head_sha,
    is_default
)
SELECT repository_id, 'feature/payment-controls', 'base-001', FALSE
FROM repository
WHERE repository_name = 'payments-platform';

INSERT INTO branch (
    repository_id,
    branch_name,
    head_sha,
    is_default
)
SELECT repository_id, 'feature/audit', 'base-001', FALSE
FROM repository
WHERE repository_name = 'payments-platform';

INSERT INTO branch_protection (
    branch_id,
    required_reviews,
    dismiss_stale_reviews,
    require_conversation_resolution,
    restrict_direct_push,
    allow_force_push,
    allow_deletion,
    require_linear_history
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    TRUE
FROM branch
WHERE branch_name = 'main';

INSERT INTO protected_merge_strategy (branch_id, strategy)
SELECT branch_id, 'squash'
FROM branch
WHERE branch_name = 'main';

INSERT INTO protected_merge_strategy (branch_id, strategy)
SELECT branch_id, 'rebase'
FROM branch
WHERE branch_name = 'main';

INSERT INTO required_status_check (branch_id, check_name)
SELECT branch_id, 'unit-tests'
FROM branch
WHERE branch_name = 'main';

INSERT INTO required_status_check (branch_id, check_name)
SELECT branch_id, 'security-scan'
FROM branch
WHERE branch_name = 'main';

INSERT INTO approval_requirement (
    branch_id,
    requirement_name,
    required_count
)
SELECT
    branch_id,
    'current_commit_approvals',
    2
FROM branch
WHERE branch_name = 'main';

INSERT INTO commit (
    repository_id,
    sha,
    author_username,
    commit_message
)
SELECT repository_id, 'commit-001', 'alice',
       'Validate transaction limits'
FROM repository
WHERE repository_name = 'payments-platform';

INSERT INTO commit (
    repository_id,
    sha,
    author_username,
    commit_message
)
SELECT repository_id, 'commit-002', 'diana',
       'Create audit record model'
FROM repository
WHERE repository_name = 'payments-platform';

INSERT INTO pull_request (
    repository_id,
    number,
    title,
    author_username,
    source_branch_id,
    target_branch_id,
    state,
    base_sha_at_creation,
    current_base_sha,
    merge_strategy
)
SELECT
    r.repository_id,
    1,
    'Strengthen payment controls',
    'alice',
    source.branch_id,
    target.branch_id,
    'open',
    target.head_sha,
    target.head_sha,
    'squash'
FROM repository r
JOIN branch source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'feature/payment-controls'
JOIN branch target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
WHERE r.repository_name = 'payments-platform';

INSERT INTO pull_request_commit (
    pull_request_id,
    commit_id,
    commit_sequence
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    1
FROM pull_request pr
JOIN commit c
  ON c.sha = 'commit-001'
WHERE pr.number = 1;

INSERT INTO review_request (
    pull_request_id,
    reviewer_username
)
SELECT pull_request_id, reviewer
FROM pull_request
CROSS JOIN (
    VALUES ('bob'), ('carol')
) AS reviewers(reviewer)
WHERE number = 1;

INSERT INTO code_review (
    pull_request_id,
    reviewer_username,
    reviewed_commit_id,
    state
)
SELECT
    pr.pull_request_id,
    reviewer,
    c.commit_id,
    'approved'
FROM pull_request pr
JOIN commit c
  ON c.sha = 'commit-001'
CROSS JOIN (
    VALUES ('bob'), ('carol')
) AS reviewers(reviewer)
WHERE pr.number = 1;

INSERT INTO review_comment (
    review_id,
    pull_request_id,
    author_username,
    file_path,
    line_number,
    body,
    is_resolved
)
SELECT
    cr.review_id,
    cr.pull_request_id,
    'bob',
    'payments.py',
    42,
    'Validation boundary is correct.',
    TRUE
FROM code_review cr
JOIN pull_request pr
  ON pr.pull_request_id = cr.pull_request_id
WHERE pr.number = 1
  AND cr.reviewer_username = 'bob';

INSERT INTO status_check (
    pull_request_id,
    check_name,
    commit_id,
    state,
    completed_at
)
SELECT
    pr.pull_request_id,
    check_name,
    c.commit_id,
    'passed',
    CURRENT_TIMESTAMP
FROM pull_request pr
JOIN commit c
  ON c.sha = 'commit-001'
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS checks(check_name)
WHERE pr.number = 1;

-- The first eligibility evaluation should succeed.
SELECT *
FROM merge_eligibility(
    (SELECT pull_request_id FROM pull_request WHERE number = 1),
    'release-manager'
);

-- Transactional merge: row locks prevent concurrent governance decisions
-- from changing the Pull Request between eligibility evaluation and merge.
BEGIN;

SELECT merge_pull_request(
    (SELECT pull_request_id FROM pull_request WHERE number = 1),
    'release-manager'
);

COMMIT;

-- A second Pull Request demonstrates stale review behavior.
INSERT INTO branch (
    repository_id,
    branch_name,
    head_sha,
    is_default
)
SELECT repository_id, 'feature/audit-ready', head_sha, FALSE
FROM branch
WHERE branch_name = 'main';

INSERT INTO pull_request (
    repository_id,
    number,
    title,
    author_username,
    source_branch_id,
    target_branch_id,
    state,
    base_sha_at_creation,
    current_base_sha,
    merge_strategy
)
SELECT
    r.repository_id,
    2,
    'Add audit persistence',
    'diana',
    source.branch_id,
    target.branch_id,
    'open',
    target.head_sha,
    target.head_sha,
    'squash'
FROM repository r
JOIN branch source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'feature/audit-ready'
JOIN branch target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
WHERE r.repository_name = 'payments-platform';

INSERT INTO pull_request_commit (
    pull_request_id,
    commit_id,
    commit_sequence
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    1
FROM pull_request pr
JOIN commit c
  ON c.sha = 'commit-002'
WHERE pr.number = 2;

INSERT INTO code_review (
    pull_request_id,
    reviewer_username,
    reviewed_commit_id,
    state
)
SELECT
    pr.pull_request_id,
    reviewer,
    c.commit_id,
    'approved'
FROM pull_request pr
JOIN commit c
  ON c.sha = 'commit-002'
CROSS JOIN (
    VALUES ('erin'), ('frank')
) AS reviewers(reviewer)
WHERE pr.number = 2;

INSERT INTO status_check (
    pull_request_id,
    check_name,
    commit_id,
    state,
    completed_at
)
SELECT
    pr.pull_request_id,
    check_name,
    c.commit_id,
    'passed',
    CURRENT_TIMESTAMP
FROM pull_request pr
JOIN commit c
  ON c.sha = 'commit-002'
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS checks(check_name)
WHERE pr.number = 2;

-- A new commit makes the previous approval/check evidence stale.
INSERT INTO commit (
    repository_id,
    sha,
    author_username,
    commit_message
)
SELECT repository_id, 'commit-003', 'diana',
       'Handle audit persistence failure'
FROM repository
WHERE repository_name = 'payments-platform';

INSERT INTO pull_request_commit (
    pull_request_id,
    commit_id,
    commit_sequence
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    2
FROM pull_request pr
JOIN commit c
  ON c.sha = 'commit-003'
WHERE pr.number = 2;

-- Governance report shows why PR #2 is no longer mergeable.
SELECT *
FROM current_pull_request_governance
WHERE number = 2;

SELECT *
FROM merge_eligibility(
    (SELECT pull_request_id FROM pull_request WHERE number = 2),
    'release-manager'
);

-- Review quality reporting: unresolved comments and requested changes.
SELECT
    pr.number,
    pr.title,
    count(rc.comment_id) FILTER (
        WHERE rc.is_resolved = FALSE
    ) AS unresolved_comments,
    count(cr.review_id) FILTER (
        WHERE cr.state = 'changes_requested'
    ) AS change_requests
FROM pull_request pr
LEFT JOIN review_comment rc
  ON rc.pull_request_id = pr.pull_request_id
LEFT JOIN code_review cr
  ON cr.pull_request_id = pr.pull_request_id
GROUP BY pr.number, pr.title
ORDER BY pr.number;

-- Repository-level protection report.
SELECT *
FROM protected_branch_report
ORDER BY repository_name, branch_name;
