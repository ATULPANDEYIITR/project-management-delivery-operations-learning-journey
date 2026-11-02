DROP SCHEMA IF EXISTS repository_governance CASCADE;
CREATE SCHEMA repository_governance;
SET search_path = repository_governance, public;

CREATE TYPE pr_state AS ENUM ('draft', 'open', 'closed', 'merged');
CREATE TYPE review_state AS ENUM (
    'commented',
    'approved',
    'changes_requested',
    'dismissed'
);
CREATE TYPE check_state AS ENUM ('pending', 'passing', 'failing');

CREATE TABLE repository (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE repository_member (
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    username TEXT NOT NULL,
    role TEXT NOT NULL CHECK (
        role IN ('developer', 'reviewer', 'maintainer', 'admin')
    ),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (repository_id, username)
);

CREATE TABLE branch (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, name)
);

CREATE TABLE commit (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT REFERENCES branch(branch_id),
    sha TEXT NOT NULL UNIQUE CHECK (sha ~ '^[0-9a-fA-F]{7,40}$'),
    author_username TEXT NOT NULL,
    message TEXT NOT NULL CHECK (length(trim(message)) > 0),
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE pull_request (
    pr_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repository(repository_id)
        ON DELETE CASCADE,
    number INTEGER NOT NULL CHECK (number > 0),
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    author_username TEXT NOT NULL,
    source_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branch(branch_id),
    state pr_state NOT NULL DEFAULT 'open',
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    mergeable BOOLEAN NOT NULL DEFAULT TRUE,
    base_behind_by INTEGER NOT NULL DEFAULT 0 CHECK (base_behind_by >= 0),
    unresolved_conversations INTEGER NOT NULL DEFAULT 0
        CHECK (unresolved_conversations >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, number)
);

CREATE TABLE pull_request_commit (
    pr_id BIGINT NOT NULL REFERENCES pull_request(pr_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commit(commit_id)
        ON DELETE RESTRICT,
    commit_order INTEGER NOT NULL CHECK (commit_order > 0),
    PRIMARY KEY (pr_id, commit_id),
    UNIQUE (pr_id, commit_order)
);

CREATE TABLE review (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL REFERENCES pull_request(pr_id)
        ON DELETE CASCADE,
    reviewer_username TEXT NOT NULL,
    state review_state NOT NULL,
    reviewed_commit_id BIGINT NOT NULL REFERENCES commit(commit_id),
    body TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_comment (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES review(review_id)
        ON DELETE CASCADE,
    author_username TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER CHECK (line_number > 0),
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE status_check (
    check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL REFERENCES pull_request(pr_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL DEFAULT 'pending',
    completed_at TIMESTAMPTZ,
    UNIQUE (pr_id, check_name)
);

CREATE TABLE branch_protection (
    protection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branch(branch_id)
        ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 0 CHECK (required_reviews >= 0),
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT TRUE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE required_status_check (
    protection_id BIGINT NOT NULL
        REFERENCES branch_protection(protection_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (protection_id, check_name)
);

CREATE TABLE merge_event (
    merge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pr_id BIGINT NOT NULL REFERENCES pull_request(pr_id),
    merged_by TEXT NOT NULL,
    merge_method TEXT NOT NULL CHECK (
        merge_method IN ('merge_commit', 'squash', 'rebase')
    ),
    merged_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION validate_review_reviewer()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    pr_author TEXT;
    reviewer_role TEXT;
BEGIN
    SELECT author_username
    INTO pr_author
    FROM pull_request
    WHERE pr_id = NEW.pr_id;

    IF NEW.reviewer_username = pr_author THEN
        RAISE EXCEPTION 'Pull request authors cannot approve their own PR';
    END IF;

    SELECT role
    INTO reviewer_role
    FROM repository_member rm
    JOIN pull_request pr
      ON pr.repository_id = rm.repository_id
    WHERE pr.pr_id = NEW.pr_id
      AND rm.username = NEW.reviewer_username
      AND rm.active;

    IF reviewer_role IS NULL
       OR reviewer_role NOT IN ('reviewer', 'maintainer', 'admin') THEN
        RAISE EXCEPTION 'Reviewer is not eligible for this repository';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER review_reviewer_validation
BEFORE INSERT OR UPDATE ON review
FOR EACH ROW
EXECUTE FUNCTION validate_review_reviewer();

CREATE INDEX idx_pr_target_state
ON pull_request(target_branch_id, state);

CREATE INDEX idx_review_pr_commit
ON review(pr_id, reviewed_commit_id, state);

CREATE INDEX idx_status_check_pr_state
ON status_check(pr_id, state);

CREATE INDEX idx_review_comment_unresolved
ON review_comment(review_id)
WHERE resolved = FALSE;

CREATE VIEW merge_eligibility AS
WITH latest_commit AS (
    SELECT
        pc.pr_id,
        pc.commit_id,
        ROW_NUMBER() OVER (
            PARTITION BY pc.pr_id
            ORDER BY pc.commit_order DESC
        ) AS rn
    FROM pull_request_commit pc
),
approval_counts AS (
    SELECT
        r.pr_id,
        COUNT(DISTINCT r.reviewer_username) AS approval_count
    FROM review r
    JOIN latest_commit lc
      ON lc.pr_id = r.pr_id
     AND lc.rn = 1
     AND lc.commit_id = r.reviewed_commit_id
    JOIN pull_request pr ON pr.pr_id = r.pr_id
    JOIN repository_member rm
      ON rm.repository_id = pr.repository_id
     AND rm.username = r.reviewer_username
     AND rm.active
    WHERE r.state = 'approved'
      AND rm.role IN ('reviewer', 'maintainer', 'admin')
    GROUP BY r.pr_id
),
check_summary AS (
    SELECT
        pr.pr_id,
        COUNT(rsc.check_name) AS required_checks,
        COUNT(*) FILTER (
            WHERE sc.state = 'passing'
        ) AS passing_required_checks
    FROM pull_request pr
    JOIN branch_protection bp
      ON bp.branch_id = pr.target_branch_id
    LEFT JOIN required_status_check rsc
      ON rsc.protection_id = bp.protection_id
    LEFT JOIN status_check sc
      ON sc.pr_id = pr.pr_id
     AND sc.check_name = rsc.check_name
    GROUP BY pr.pr_id
),
unresolved AS (
    SELECT
        r.review_id,
        COUNT(rc.comment_id) FILTER (
            WHERE rc.resolved = FALSE
        ) AS unresolved_comments
    FROM review r
    LEFT JOIN review_comment rc
      ON rc.review_id = r.review_id
    GROUP BY r.review_id
),
conversation_summary AS (
    SELECT
        pr.pr_id,
        COALESCE(SUM(u.unresolved_comments), 0) AS unresolved_comments
    FROM pull_request pr
    LEFT JOIN review r ON r.pr_id = pr.pr_id
    LEFT JOIN unresolved u ON u.review_id = r.review_id
    GROUP BY pr.pr_id
)
SELECT
    pr.pr_id,
    pr.number,
    pr.title,
    pr.state,
    pr.target_branch_id,
    bp.required_reviews,
    COALESCE(ac.approval_count, 0) AS current_approvals,
    COALESCE(cs.required_checks, 0) AS required_checks,
    COALESCE(cs.passing_required_checks, 0) AS passing_required_checks,
    COALESCE(cvs.unresolved_comments, 0) AS unresolved_comments,
    pr.unresolved_conversations,
    pr.base_behind_by,
    pr.mergeable,
    (
        pr.state = 'open'
        AND NOT pr.is_draft
        AND pr.mergeable
        AND COALESCE(ac.approval_count, 0) >= bp.required_reviews
        AND COALESCE(cs.required_checks, 0)
            = COALESCE(cs.passing_required_checks, 0)
        AND (
            NOT bp.require_conversation_resolution
            OR (
                pr.unresolved_conversations = 0
                AND COALESCE(cvs.unresolved_comments, 0) = 0
            )
        )
        AND (
            NOT bp.require_linear_history
            OR pr.base_behind_by = 0
        )
    ) AS eligible
FROM pull_request pr
JOIN branch_protection bp
  ON bp.branch_id = pr.target_branch_id
LEFT JOIN approval_counts ac ON ac.pr_id = pr.pr_id
LEFT JOIN check_summary cs ON cs.pr_id = pr.pr_id
LEFT JOIN conversation_summary cvs ON cvs.pr_id = pr.pr_id;

CREATE OR REPLACE FUNCTION can_merge(p_pr_id BIGINT)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
AS $$
    SELECT eligible
    FROM merge_eligibility
    WHERE pr_id = p_pr_id;
$$;

INSERT INTO repository(name, default_branch)
VALUES ('payments-service', 'main');

INSERT INTO repository_member(repository_id, username, role)
SELECT repository_id, v.username, v.role
FROM repository r
CROSS JOIN (
    VALUES
        ('atul', 'developer'),
        ('maya', 'reviewer'),
        ('liam', 'maintainer'),
        ('nora', 'reviewer')
) AS v(username, role)
WHERE r.name = 'payments-service';

INSERT INTO branch(repository_id, name, protected)
SELECT repository_id, 'main', TRUE
FROM repository
WHERE name = 'payments-service';

INSERT INTO branch(repository_id, name, protected)
SELECT repository_id, 'feature/idempotency', FALSE
FROM repository
WHERE name = 'payments-service';

INSERT INTO branch_protection (
    branch_id,
    required_reviews,
    require_conversation_resolution,
    require_linear_history,
    allow_force_push,
    allow_branch_deletion,
    allow_direct_push
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE
FROM branch
WHERE name = 'main';

INSERT INTO required_status_check(protection_id, check_name)
SELECT protection_id, 'ci'
FROM branch_protection;

INSERT INTO required_status_check(protection_id, check_name)
SELECT protection_id, 'security'
FROM branch_protection;

INSERT INTO commit(branch_id, sha, author_username, message)
SELECT
    b.branch_id,
    'a1b2c3d',
    'atul',
    'Add idempotency validation'
FROM branch b
WHERE b.name = 'feature/idempotency';

INSERT INTO pull_request (
    repository_id,
    number,
    title,
    author_username,
    source_branch_id,
    target_branch_id
)
SELECT
    r.repository_id,
    142,
    'Add transaction idempotency protection',
    'atul',
    source.branch_id,
    target.branch_id
FROM repository r
JOIN branch source
  ON source.repository_id = r.repository_id
 AND source.name = 'feature/idempotency'
JOIN branch target
  ON target.repository_id = r.repository_id
 AND target.name = 'main'
WHERE r.name = 'payments-service';

INSERT INTO pull_request_commit(pr_id, commit_id, commit_order)
SELECT
    pr.pr_id,
    c.commit_id,
    1
FROM pull_request pr
JOIN commit c ON c.sha = 'a1b2c3d'
WHERE pr.number = 142;

INSERT INTO status_check(pr_id, check_name, state, completed_at)
SELECT pr_id, 'ci', 'passing', now()
FROM pull_request
WHERE number = 142;

INSERT INTO status_check(pr_id, check_name, state, completed_at)
SELECT pr_id, 'security', 'passing', now()
FROM pull_request
WHERE number = 142;

INSERT INTO review(pr_id, reviewer_username, state, reviewed_commit_id, body)
SELECT
    pr.pr_id,
    'maya',
    'approved',
    c.commit_id,
    'Implementation reviewed.'
FROM pull_request pr
JOIN commit c ON c.sha = 'a1b2c3d'
WHERE pr.number = 142;

INSERT INTO review(pr_id, reviewer_username, state, reviewed_commit_id, body)
SELECT
    pr.pr_id,
    'liam',
    'approved',
    c.commit_id,
    'Governance requirements satisfied.'
FROM pull_request pr
JOIN commit c ON c.sha = 'a1b2c3d'
WHERE pr.number = 142;

-- Retrieval and eligibility reporting.
SELECT *
FROM merge_eligibility
WHERE number = 142;

SELECT
    number,
    title,
    current_approvals,
    required_reviews,
    passing_required_checks,
    required_checks,
    eligible
FROM merge_eligibility
ORDER BY number;

-- Demonstrate stale approvals after a new commit.
INSERT INTO commit(branch_id, sha, author_username, message)
SELECT
    b.branch_id,
    'd4e5f6g',
    'atul',
    'Handle duplicate transaction requests'
FROM branch b
WHERE b.name = 'feature/idempotency';

INSERT INTO pull_request_commit(pr_id, commit_id, commit_order)
SELECT
    pr.pr_id,
    c.commit_id,
    2
FROM pull_request pr
JOIN commit c ON c.sha = 'd4e5f6g'
WHERE pr.number = 142;

SELECT
    number,
    current_approvals,
    required_reviews,
    eligible
FROM merge_eligibility
WHERE number = 142;

-- Current-head approvals restore approval eligibility.
INSERT INTO review(pr_id, reviewer_username, state, reviewed_commit_id)
SELECT pr.pr_id, 'maya', 'approved', c.commit_id
FROM pull_request pr
JOIN commit c ON c.sha = 'd4e5f6g'
WHERE pr.number = 142;

INSERT INTO review(pr_id, reviewer_username, state, reviewed_commit_id)
SELECT pr.pr_id, 'liam', 'approved', c.commit_id
FROM pull_request pr
JOIN commit c ON c.sha = 'd4e5f6g'
WHERE pr.number = 142;

SELECT
    number,
    current_approvals,
    eligible
FROM merge_eligibility
WHERE number = 142;

-- A transaction protects a merge decision from partial state changes.
BEGIN;

SELECT can_merge(pr_id)
FROM pull_request
WHERE number = 142
FOR UPDATE;

INSERT INTO merge_event(pr_id, merged_by, merge_method)
SELECT pr_id, 'liam', 'squash'
FROM pull_request
WHERE number = 142
  AND can_merge(pr_id);

UPDATE pull_request
SET state = 'merged'
WHERE number = 142
  AND can_merge(pr_id);

COMMIT;

SELECT number, state
FROM pull_request
WHERE number = 142;

-- Validation query for protected branches.
SELECT
    b.name,
    bp.required_reviews,
    bp.require_conversation_resolution,
    bp.require_linear_history,
    bp.allow_direct_push,
    bp.allow_force_push,
    bp.allow_branch_deletion
FROM branch b
JOIN branch_protection bp ON bp.branch_id = b.branch_id
WHERE b.protected
ORDER BY b.name;
