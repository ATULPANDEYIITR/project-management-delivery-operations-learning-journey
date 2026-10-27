DROP SCHEMA IF EXISTS project_governance CASCADE;
CREATE SCHEMA project_governance;

SET search_path TO project_governance, public;

CREATE TYPE user_role AS ENUM (
    'developer',
    'reviewer',
    'project_manager',
    'maintainer',
    'administrator'
);

CREATE TYPE pr_state AS ENUM (
    'draft',
    'open',
    'in_review',
    'approved',
    'changes_requested',
    'merged',
    'closed'
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

CREATE TABLE app_user (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    role user_role NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE repository (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    owner_user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE branch (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id) ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    head_commit_id BIGINT,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE commit_record (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id) ON DELETE CASCADE,
    commit_hash TEXT NOT NULL,
    author_user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    message TEXT NOT NULL CHECK (length(trim(message)) >= 5),
    parent_commit_id BIGINT REFERENCES commit_record(commit_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, commit_hash)
);

ALTER TABLE branch
    ADD CONSTRAINT branch_head_fk
    FOREIGN KEY (head_commit_id)
    REFERENCES commit_record(commit_id);

CREATE TABLE pull_request (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    title TEXT NOT NULL CHECK (length(trim(title)) >= 5),
    source_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    author_user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    state pr_state NOT NULL DEFAULT 'open',
    draft BOOLEAN NOT NULL DEFAULT FALSE,
    merge_conflict BOOLEAN NOT NULL DEFAULT FALSE,
    base_synchronized BOOLEAN NOT NULL DEFAULT TRUE,
    revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CHECK (source_branch_id <> target_branch_id)
);

CREATE TABLE pull_request_commit (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_request(pull_request_id) ON DELETE CASCADE,
    commit_id BIGINT NOT NULL
        REFERENCES commit_record(commit_id),
    revision INTEGER NOT NULL CHECK (revision > 0),
    PRIMARY KEY (pull_request_id, commit_id)
);

CREATE TABLE review (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_request(pull_request_id) ON DELETE CASCADE,
    reviewer_user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    state review_state NOT NULL,
    revision_reviewed INTEGER NOT NULL CHECK (revision_reviewed > 0),
    dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_comment (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES review(review_id) ON DELETE CASCADE,
    comment_text TEXT NOT NULL CHECK (length(trim(comment_text)) >= 3),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE status_check (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_request(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branch(branch_id) ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 0
        CHECK (required_reviews >= 0),
    restrict_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_administrator_bypass BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE required_status_check (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policy(policy_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name)
);

CREATE TABLE merge_event (
    merge_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_request(pull_request_id),
    merged_by_user_id BIGINT NOT NULL REFERENCES app_user(user_id),
    merge_strategy TEXT NOT NULL
        CHECK (merge_strategy IN ('merge_commit', 'squash', 'rebase')),
    merged_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_pr_target_state
    ON pull_request(target_branch_id, state);

CREATE INDEX idx_review_pr_state_revision
    ON review(pull_request_id, state, revision_reviewed);

CREATE INDEX idx_status_check_pr_state
    ON status_check(pull_request_id, state);

CREATE INDEX idx_review_comment_unresolved
    ON review_comment(review_id)
    WHERE resolved = FALSE;

CREATE OR REPLACE FUNCTION prevent_invalid_review()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    pr_author BIGINT;
    pr_revision INTEGER;
    reviewer_role user_role;
BEGIN
    SELECT author_user_id, revision
    INTO pr_author, pr_revision
    FROM pull_request
    WHERE pull_request_id = NEW.pull_request_id;

    IF NEW.reviewer_user_id = pr_author THEN
        RAISE EXCEPTION 'A Pull Request author cannot approve their own change';
    END IF;

    SELECT role
    INTO reviewer_role
    FROM app_user
    WHERE user_id = NEW.reviewer_user_id
      AND active = TRUE;

    IF reviewer_role NOT IN (
        'reviewer',
        'project_manager',
        'maintainer',
        'administrator'
    ) THEN
        RAISE EXCEPTION 'User % is not an eligible reviewer',
            NEW.reviewer_user_id;
    END IF;

    IF NEW.revision_reviewed > pr_revision THEN
        RAISE EXCEPTION 'Review revision cannot exceed Pull Request revision';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_review
BEFORE INSERT OR UPDATE ON review
FOR EACH ROW
EXECUTE FUNCTION prevent_invalid_review();

CREATE OR REPLACE FUNCTION prevent_direct_protected_push()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.protected = TRUE
       AND NEW.head_commit_id IS DISTINCT FROM OLD.head_commit_id THEN
        RAISE EXCEPTION
            'Protected branch head cannot be changed directly through this model';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_protected_branch_head
BEFORE UPDATE ON branch
FOR EACH ROW
EXECUTE FUNCTION prevent_direct_protected_push();

CREATE OR REPLACE FUNCTION calculate_merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_target_branch BIGINT;
    v_revision INTEGER;
    v_required_reviews INTEGER;
    v_required_resolved BOOLEAN;
    v_required_check_count INTEGER;
    v_passed_check_count INTEGER;
    v_approval_count INTEGER;
    v_open_conversations INTEGER;
    v_conflict BOOLEAN;
    v_synchronized BOOLEAN;
    v_draft BOOLEAN;
BEGIN
    SELECT
        target_branch_id,
        revision,
        merge_conflict,
        base_synchronized,
        draft
    INTO
        v_target_branch,
        v_revision,
        v_conflict,
        v_synchronized,
        v_draft
    FROM pull_request
    WHERE pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Pull Request does not exist';
        RETURN;
    END IF;

    IF v_draft THEN
        RETURN QUERY SELECT FALSE, 'Pull Request is still a draft';
    END IF;

    IF v_conflict THEN
        RETURN QUERY SELECT FALSE, 'Merge conflicts exist';
    END IF;

    IF NOT v_synchronized THEN
        RETURN QUERY SELECT FALSE, 'Base branch is not synchronized';
    END IF;

    SELECT required_reviews, require_resolved_conversations
    INTO v_required_reviews, v_required_resolved
    FROM branch_protection_policy
    WHERE branch_id = v_target_branch;

    IF v_required_reviews IS NULL THEN
        v_required_reviews := 0;
        v_required_resolved := FALSE;
    END IF;

    SELECT count(DISTINCT r.reviewer_user_id)
    INTO v_approval_count
    FROM review r
    JOIN app_user u
      ON u.user_id = r.reviewer_user_id
    WHERE r.pull_request_id = p_pull_request_id
      AND r.state = 'approved'
      AND r.dismissed = FALSE
      AND r.revision_reviewed = v_revision
      AND u.active = TRUE
      AND u.role IN (
          'reviewer',
          'project_manager',
          'maintainer',
          'administrator'
      );

    IF v_approval_count < v_required_reviews THEN
        RETURN QUERY SELECT
            FALSE,
            format(
                'Required approvals: %s; current eligible approvals: %s',
                v_required_reviews,
                v_approval_count
            );
    END IF;

    SELECT count(*)
    INTO v_required_check_count
    FROM required_status_check rsc
    JOIN branch_protection_policy bpp
      ON bpp.policy_id = rsc.policy_id
    WHERE bpp.branch_id = v_target_branch;

    SELECT count(*)
    INTO v_passed_check_count
    FROM required_status_check rsc
    JOIN branch_protection_policy bpp
      ON bpp.policy_id = rsc.policy_id
    JOIN status_check sc
      ON sc.pull_request_id = p_pull_request_id
     AND sc.check_name = rsc.check_name
    WHERE bpp.branch_id = v_target_branch
      AND sc.state = 'passed';

    IF v_passed_check_count < v_required_check_count THEN
        RETURN QUERY SELECT
            FALSE,
            'One or more required status checks have not passed';
    END IF;

    SELECT count(*)
    INTO v_open_conversations
    FROM review_comment rc
    JOIN review r ON r.review_id = rc.review_id
    WHERE r.pull_request_id = p_pull_request_id
      AND rc.resolved = FALSE;

    IF v_required_resolved AND v_open_conversations > 0 THEN
        RETURN QUERY SELECT
            FALSE,
            'Unresolved review conversations remain';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM review
        WHERE pull_request_id = p_pull_request_id
    ) AND v_required_reviews > 0 THEN
        RETURN QUERY SELECT FALSE, 'No review decisions exist';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM calculate_merge_eligibility.empty_guard
    ) THEN
        RETURN QUERY SELECT TRUE, 'All merge requirements are satisfied';
    END IF;
END;
$$;

CREATE OR REPLACE VIEW merge_eligibility_report AS
SELECT
    pr.pull_request_id,
    r.repository_name,
    pr.number,
    pr.title,
    pr.state,
    b.branch_name AS target_branch,
    pr.draft,
    pr.merge_conflict,
    pr.base_synchronized,
    pr.revision,
    COALESCE(
        (
            SELECT count(DISTINCT rv.reviewer_user_id)
            FROM review rv
            JOIN app_user au ON au.user_id = rv.reviewer_user_id
            WHERE rv.pull_request_id = pr.pull_request_id
              AND rv.state = 'approved'
              AND rv.dismissed = FALSE
              AND rv.revision_reviewed = pr.revision
              AND au.active = TRUE
              AND au.role IN (
                  'reviewer',
                  'project_manager',
                  'maintainer',
                  'administrator'
              )
        ),
        0
    ) AS current_approvals,
    COALESCE(bpp.required_reviews, 0) AS required_reviews,
    (
        SELECT count(*)
        FROM review_comment rc
        JOIN review rv ON rv.review_id = rc.review_id
        WHERE rv.pull_request_id = pr.pull_request_id
          AND rc.resolved = FALSE
    ) AS unresolved_comments
FROM pull_request pr
JOIN repository r
  ON r.repository_id = pr.repository_id
JOIN branch b
  ON b.branch_id = pr.target_branch_id
LEFT JOIN branch_protection_policy bpp
  ON bpp.branch_id = b.branch_id;

INSERT INTO app_user (username, display_name, role)
VALUES
    ('project_manager', 'Project Manager', 'project_manager'),
    ('architecture_reviewer', 'Architecture Reviewer', 'reviewer'),
    ('quality_reviewer', 'Quality Reviewer', 'reviewer'),
    ('developer', 'Project Developer', 'developer'),
    ('maintainer', 'Repository Maintainer', 'maintainer');

INSERT INTO repository (repository_name, owner_user_id)
SELECT 'enterprise-project-platform', user_id
FROM app_user
WHERE username = 'project_manager';

INSERT INTO branch (
    repository_id,
    branch_name,
    protected
)
SELECT
    repository_id,
    'main',
    TRUE
FROM repository
WHERE repository_name = 'enterprise-project-platform';

INSERT INTO branch (
    repository_id,
    branch_name,
    protected
)
SELECT
    repository_id,
    'feature/risk-controls',
    FALSE
FROM repository
WHERE repository_name = 'enterprise-project-platform';

INSERT INTO branch (
    repository_id,
    branch_name,
    protected
)
SELECT
    repository_id,
    'feature/cost-controls',
    FALSE
FROM repository
WHERE repository_name = 'enterprise-project-platform';

INSERT INTO branch_protection_policy (
    branch_id,
    required_reviews,
    restrict_direct_push,
    restrict_force_push,
    restrict_deletion,
    require_resolved_conversations,
    require_linear_history,
    allow_administrator_bypass
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    FALSE
FROM branch
WHERE branch_name = 'main';

INSERT INTO required_status_check (policy_id, check_name)
SELECT
    bpp.policy_id,
    checks.check_name
FROM branch_protection_policy bpp
CROSS JOIN (
    VALUES
        ('scope-validation'),
        ('security-validation'),
        ('quality-gate')
) AS checks(check_name);

INSERT INTO pull_request (
    repository_id,
    number,
    title,
    source_branch_id,
    target_branch_id,
    author_user_id,
    state,
    draft,
    revision
)
SELECT
    r.repository_id,
    1001,
    'Implement project risk approval workflow',
    source.branch_id,
    target.branch_id,
    developer.user_id,
    'in_review',
    FALSE,
    1
FROM repository r
JOIN branch source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'feature/risk-controls'
JOIN branch target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
JOIN app_user developer
  ON developer.username = 'developer'
WHERE r.repository_name = 'enterprise-project-platform';

INSERT INTO commit_record (
    repository_id,
    commit_hash,
    author_user_id,
    message
)
SELECT
    repository_id,
    'risk-commit-001',
    user_id,
    'Implement project risk validation'
FROM repository
CROSS JOIN app_user
WHERE repository_name = 'enterprise-project-platform'
  AND username = 'developer';

INSERT INTO pull_request_commit (
    pull_request_id,
    commit_id,
    revision
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    1
FROM pull_request pr
JOIN commit_record c
  ON c.commit_hash = 'risk-commit-001'
WHERE pr.number = 1001;

UPDATE pull_request
SET revision = 1
WHERE number = 1001;

INSERT INTO status_check (
    pull_request_id,
    check_name,
    state
)
SELECT
    pull_request_id,
    check_name,
    'passed'
FROM pull_request
CROSS JOIN (
    VALUES
        ('scope-validation'),
        ('security-validation'),
        ('quality-gate')
) AS checks(check_name)
WHERE number = 1001;

INSERT INTO review (
    pull_request_id,
    reviewer_user_id,
    state,
    revision_reviewed
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'approved',
    1
FROM pull_request pr
CROSS JOIN app_user u
WHERE pr.number = 1001
  AND u.username IN (
      'architecture_reviewer',
      'quality_reviewer'
  );

INSERT INTO review_comment (
    review_id,
    comment_text,
    resolved
)
SELECT
    review_id,
    'Risk validation evidence is traceable.',
    TRUE
FROM review
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_request
    WHERE number = 1001
)
LIMIT 1;

INSERT INTO pull_request (
    repository_id,
    number,
    title,
    source_branch_id,
    target_branch_id,
    author_user_id,
    state,
    draft,
    revision
)
SELECT
    r.repository_id,
    1002,
    'Update project cost-control policy',
    source.branch_id,
    target.branch_id,
    developer.user_id,
    'in_review',
    FALSE,
    2
FROM repository r
JOIN branch source
  ON source.repository_id = r.repository_id
 AND source.branch_name = 'feature/cost-controls'
JOIN branch target
  ON target.repository_id = r.repository_id
 AND target.branch_name = 'main'
JOIN app_user developer
  ON developer.username = 'developer'
WHERE r.repository_name = 'enterprise-project-platform';

INSERT INTO review (
    pull_request_id,
    reviewer_user_id,
    state,
    revision_reviewed
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'approved',
    1
FROM pull_request pr
CROSS JOIN app_user u
WHERE pr.number = 1002
  AND u.username IN (
      'architecture_reviewer',
      'quality_reviewer'
  );

-- These approvals are intentionally stale because PR 1002 is at revision 2.
INSERT INTO status_check (
    pull_request_id,
    check_name,
    state
)
SELECT
    pull_request_id,
    check_name,
    'passed'
FROM pull_request
CROSS JOIN (
    VALUES
        ('scope-validation'),
        ('security-validation'),
        ('quality-gate')
) AS checks(check_name)
WHERE number = 1002;

-- Retrieval and reporting.
SELECT *
FROM merge_eligibility_report
ORDER BY number;

-- Review quality query: current approvals versus required approvals.
SELECT
    pull_request_id,
    number,
    title,
    current_approvals,
    required_reviews,
    unresolved_comments,
    CASE
        WHEN current_approvals >= required_reviews
         AND unresolved_comments = 0
         AND NOT draft
         AND NOT merge_conflict
         AND base_synchronized
        THEN 'review-ready'
        ELSE 'blocked'
    END AS review_decision
FROM merge_eligibility_report
ORDER BY number;

-- Status-check coverage.
SELECT
    pr.number,
    pr.title,
    sc.check_name,
    sc.state
FROM pull_request pr
JOIN status_check sc
  ON sc.pull_request_id = pr.pull_request_id
ORDER BY pr.number, sc.check_name;

-- Approval audit: identify stale approvals.
SELECT
    pr.number,
    pr.revision AS current_revision,
    rv.reviewer_user_id,
    rv.revision_reviewed,
    rv.state,
    CASE
        WHEN rv.revision_reviewed = pr.revision
        THEN 'current'
        ELSE 'stale'
    END AS approval_status
FROM pull_request pr
JOIN review rv
  ON rv.pull_request_id = pr.pull_request_id
ORDER BY pr.number, rv.reviewer_user_id;

-- Transactional merge example for PR 1001.
BEGIN;

WITH eligibility AS (
    SELECT
        pr.pull_request_id,
        pr.number,
        COUNT(DISTINCT rv.reviewer_user_id)
            FILTER (
                WHERE rv.state = 'approved'
                  AND rv.dismissed = FALSE
                  AND rv.revision_reviewed = pr.revision
            ) AS approvals,
        bpp.required_reviews
    FROM pull_request pr
    JOIN branch_protection_policy bpp
      ON bpp.branch_id = pr.target_branch_id
    LEFT JOIN review rv
      ON rv.pull_request_id = pr.pull_request_id
    WHERE pr.number = 1001
    GROUP BY
        pr.pull_request_id,
        pr.number,
        bpp.required_reviews
)
SELECT *
FROM eligibility
WHERE approvals >= required_reviews
FOR UPDATE;

UPDATE pull_request
SET state = 'merged',
    merged_at = now()
WHERE number = 1001
  AND state <> 'merged';

INSERT INTO merge_event (
    pull_request_id,
    merged_by_user_id,
    merge_strategy
)
SELECT
    pr.pull_request_id,
    u.user_id,
    'squash'
FROM pull_request pr
JOIN app_user u
  ON u.username = 'project_manager'
WHERE pr.number = 1001
  AND pr.state = 'merged';

COMMIT;

-- Final workflow state.
SELECT
    number,
    title,
    state,
    merged_at
FROM pull_request
WHERE number IN (1001, 1002)
ORDER BY number;
