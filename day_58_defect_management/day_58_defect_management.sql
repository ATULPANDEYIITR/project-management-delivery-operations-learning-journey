DROP SCHEMA IF EXISTS defect_management CASCADE;
CREATE SCHEMA defect_management;

SET search_path TO defect_management, public;

-- The relational model separates defect facts, workflow decisions,
-- verification evidence, and repository-level configuration.

CREATE TYPE defect_status AS ENUM (
    'NEW',
    'TRIAGED',
    'ASSIGNED',
    'IN_PROGRESS',
    'RESOLVED',
    'VERIFIED',
    'REOPENED',
    'CLOSED',
    'REJECTED'
);

CREATE TYPE defect_severity AS ENUM (
    'BLOCKER',
    'CRITICAL',
    'MAJOR',
    'MINOR',
    'TRIVIAL'
);

CREATE TYPE defect_priority AS ENUM ('P0', 'P1', 'P2', 'P3');

CREATE TYPE defect_type AS ENUM (
    'FUNCTIONAL',
    'PERFORMANCE',
    'SECURITY',
    'USABILITY',
    'DATA',
    'COMPATIBILITY'
);

CREATE TYPE resolution_type AS ENUM (
    'FIXED',
    'DUPLICATE',
    'NOT_REPRODUCIBLE',
    'WONT_FIX',
    'INVALID'
);

CREATE TABLE app_user (
    user_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username text NOT NULL UNIQUE,
    display_name text NOT NULL,
    role_name text NOT NULL CHECK (
        role_name IN ('REPORTER', 'DEVELOPER', 'QA', 'LEAD', 'MANAGER')
    ),
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE repository (
    repository_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name text NOT NULL UNIQUE,
    default_branch text NOT NULL DEFAULT 'main',
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE branch (
    branch_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id bigint NOT NULL REFERENCES repository(repository_id),
    branch_name text NOT NULL,
    protected boolean NOT NULL DEFAULT false,
    head_commit text,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE defect (
    defect_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id bigint NOT NULL REFERENCES repository(repository_id),
    reporter_id bigint NOT NULL REFERENCES app_user(user_id),
    assignee_id bigint REFERENCES app_user(user_id),
    title text NOT NULL CHECK (length(trim(title)) >= 5),
    description text NOT NULL CHECK (length(trim(description)) >= 10),
    defect_type defect_type NOT NULL,
    severity defect_severity NOT NULL,
    priority defect_priority NOT NULL,
    status defect_status NOT NULL DEFAULT 'NEW',
    environment text NOT NULL,
    affected_version text NOT NULL,
    steps_to_reproduce text[] NOT NULL CHECK (cardinality(steps_to_reproduce) > 0),
    expected_result text NOT NULL,
    actual_result text NOT NULL,
    resolution resolution_type,
    resolution_notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz,
    closed_at timestamptz,
    CHECK (
        status NOT IN ('RESOLVED', 'VERIFIED', 'CLOSED')
        OR resolution IS NOT NULL
    )
);

CREATE TABLE defect_comment (
    comment_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    defect_id bigint NOT NULL REFERENCES defect(defect_id) ON DELETE CASCADE,
    author_id bigint NOT NULL REFERENCES app_user(user_id),
    body text NOT NULL CHECK (length(trim(body)) > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz
);

CREATE TABLE defect_history (
    history_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    defect_id bigint NOT NULL REFERENCES defect(defect_id) ON DELETE CASCADE,
    actor_id bigint REFERENCES app_user(user_id),
    previous_status defect_status,
    new_status defect_status NOT NULL,
    event_note text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE status_check (
    check_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    defect_id bigint NOT NULL REFERENCES defect(defect_id) ON DELETE CASCADE,
    check_name text NOT NULL,
    status text NOT NULL CHECK (status IN ('PENDING', 'PASSED', 'FAILED')),
    completed_at timestamptz,
    UNIQUE (defect_id, check_name)
);

CREATE TABLE verification (
    verification_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    defect_id bigint NOT NULL REFERENCES defect(defect_id) ON DELETE CASCADE,
    tester_id bigint NOT NULL REFERENCES app_user(user_id),
    passed boolean NOT NULL,
    evidence text NOT NULL,
    verified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE defect_tag (
    defect_id bigint NOT NULL REFERENCES defect(defect_id) ON DELETE CASCADE,
    tag text NOT NULL,
    PRIMARY KEY (defect_id, tag)
);

CREATE TABLE defect_policy (
    policy_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id bigint NOT NULL REFERENCES repository(repository_id),
    required_approvals integer NOT NULL CHECK (required_approvals >= 0),
    require_all_checks boolean NOT NULL DEFAULT true,
    require_verification boolean NOT NULL DEFAULT true,
    critical_requires_manager boolean NOT NULL DEFAULT true,
    active boolean NOT NULL DEFAULT true
);

CREATE INDEX idx_defect_status_priority
    ON defect(status, priority, severity);

CREATE INDEX idx_defect_assignee_status
    ON defect(assignee_id, status);

CREATE INDEX idx_defect_repository_version
    ON defect(repository_id, affected_version);

CREATE INDEX idx_comment_defect
    ON defect_comment(defect_id, created_at);

CREATE INDEX idx_status_check_defect_status
    ON status_check(defect_id, status);

CREATE OR REPLACE FUNCTION validate_defect_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'CLOSED' AND NEW.status <> 'CLOSED' THEN
        RAISE EXCEPTION 'Closed defects cannot transition to another state';
    END IF;

    IF OLD.status = 'NEW' AND NEW.status NOT IN ('NEW', 'TRIAGED', 'REJECTED') THEN
        RAISE EXCEPTION 'NEW defect can only become TRIAGED or REJECTED';
    END IF;

    IF OLD.status = 'TRIAGED'
       AND NEW.status NOT IN ('TRIAGED', 'ASSIGNED', 'REJECTED') THEN
        RAISE EXCEPTION 'TRIAGED defect has an invalid transition';
    END IF;

    IF OLD.status = 'ASSIGNED'
       AND NEW.status NOT IN ('ASSIGNED', 'IN_PROGRESS') THEN
        RAISE EXCEPTION 'ASSIGNED defect has an invalid transition';
    END IF;

    IF OLD.status = 'IN_PROGRESS'
       AND NEW.status NOT IN ('IN_PROGRESS', 'RESOLVED') THEN
        RAISE EXCEPTION 'IN_PROGRESS defect has an invalid transition';
    END IF;

    IF OLD.status = 'RESOLVED'
       AND NEW.status NOT IN ('RESOLVED', 'VERIFIED', 'REOPENED') THEN
        RAISE EXCEPTION 'RESOLVED defect has an invalid transition';
    END IF;

    IF OLD.status = 'VERIFIED'
       AND NEW.status NOT IN ('VERIFIED', 'CLOSED') THEN
        RAISE EXCEPTION 'VERIFIED defect has an invalid transition';
    END IF;

    IF OLD.status = 'REOPENED'
       AND NEW.status NOT IN ('REOPENED', 'ASSIGNED') THEN
        RAISE EXCEPTION 'REOPENED defect has an invalid transition';
    END IF;

    IF NEW.status IN ('ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'VERIFIED', 'REOPENED')
       AND NEW.assignee_id IS NULL THEN
        RAISE EXCEPTION 'This state requires an assignee';
    END IF;

    IF NEW.status = 'RESOLVED' AND NEW.resolution IS NULL THEN
        RAISE EXCEPTION 'Resolved defect requires a resolution';
    END IF;

    IF NEW.status = 'CLOSED' AND NEW.resolution IS NULL THEN
        RAISE EXCEPTION 'Closed defect requires a resolution';
    END IF;

    IF NEW.status = 'RESOLVED' AND OLD.status <> 'RESOLVED' THEN
        NEW.resolved_at := COALESCE(NEW.resolved_at, now());
    END IF;

    IF NEW.status = 'CLOSED' AND OLD.status <> 'CLOSED' THEN
        NEW.closed_at := COALESCE(NEW.closed_at, now());
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_defect_transition
BEFORE UPDATE OF status, assignee_id, resolution
ON defect
FOR EACH ROW
EXECUTE FUNCTION validate_defect_transition();

CREATE OR REPLACE FUNCTION audit_defect_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO defect_history (
            defect_id,
            actor_id,
            previous_status,
            new_status,
            event_note
        )
        VALUES (
            NEW.defect_id,
            NEW.assignee_id,
            OLD.status,
            NEW.status,
            'Workflow status changed'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_defect_transition
AFTER UPDATE OF status
ON defect
FOR EACH ROW
EXECUTE FUNCTION audit_defect_transition();

INSERT INTO app_user (username, display_name, role_name)
VALUES
    ('asha.qa', 'Asha Rao', 'QA'),
    ('ravi.dev', 'Ravi Kumar', 'DEVELOPER'),
    ('meera.manager', 'Meera Singh', 'MANAGER'),
    ('vikram.qa', 'Vikram Shah', 'QA'),
    ('leena.lead', 'Leena Das', 'LEAD');

INSERT INTO repository (repository_name, default_branch)
VALUES
    ('commerce-platform', 'main'),
    ('analytics-platform', 'main');

INSERT INTO branch (repository_id, branch_name, protected, head_commit)
SELECT repository_id, 'main', true, '9f0a11c'
FROM repository
WHERE repository_name = 'commerce-platform';

INSERT INTO branch (repository_id, branch_name, protected, head_commit)
SELECT repository_id, 'release/7.4', true, '8a72bc4'
FROM repository
WHERE repository_name = 'commerce-platform';

INSERT INTO defect (
    repository_id,
    reporter_id,
    title,
    description,
    defect_type,
    severity,
    priority,
    environment,
    affected_version,
    steps_to_reproduce,
    expected_result,
    actual_result
)
SELECT
    r.repository_id,
    u.user_id,
    'Authorization succeeds after account deactivation',
    'Protected API endpoints continue accepting a session after the account is disabled.',
    'SECURITY',
    'CRITICAL',
    'P0',
    'staging',
    '7.4.0',
    ARRAY[
        'Create a test account',
        'Authenticate and obtain a session',
        'Deactivate the account',
        'Call a protected endpoint'
    ],
    'The request is denied.',
    'The request succeeds with HTTP 200.'
FROM repository r
CROSS JOIN app_user u
WHERE r.repository_name = 'commerce-platform'
  AND u.username = 'asha.qa';

INSERT INTO defect (
    repository_id,
    reporter_id,
    title,
    description,
    defect_type,
    severity,
    priority,
    environment,
    affected_version,
    steps_to_reproduce,
    expected_result,
    actual_result
)
SELECT
    r.repository_id,
    u.user_id,
    'Dashboard date filter disappears after pagination',
    'A selected date range is lost when the user moves to another result page.',
    'USABILITY',
    'MAJOR',
    'P2',
    'staging',
    '7.4.0',
    ARRAY[
        'Open dashboard search',
        'Select a date range',
        'Navigate to page two'
    ],
    'The selected date range remains active.',
    'The date range is cleared.'
FROM repository r
CROSS JOIN app_user u
WHERE r.repository_name = 'commerce-platform'
  AND u.username = 'vikram.qa';

INSERT INTO defect (
    repository_id,
    reporter_id,
    title,
    description,
    defect_type,
    severity,
    priority,
    environment,
    affected_version,
    steps_to_reproduce,
    expected_result,
    actual_result,
    status,
    resolution,
    resolution_notes,
    assignee_id
)
SELECT
    r.repository_id,
    qa.user_id,
    'CSV export truncates Unicode names',
    'Exported product names lose characters outside the basic ASCII range.',
    'DATA',
    'MAJOR',
    'P1',
    'staging',
    '7.3.2',
    ARRAY[
        'Create a product with a Unicode name',
        'Export products to CSV',
        'Open the resulting file'
    ],
    'The complete product name is preserved.',
    'Characters are truncated.',
    'VERIFIED',
    'FIXED',
    'UTF-8 output handling corrected.',
    dev.user_id
FROM repository r
JOIN app_user qa ON qa.username = 'asha.qa'
JOIN app_user dev ON dev.username = 'ravi.dev'
WHERE r.repository_name = 'commerce-platform';

INSERT INTO defect_tag (defect_id, tag)
SELECT defect_id, 'security'
FROM defect
WHERE title = 'Authorization succeeds after account deactivation';

INSERT INTO defect_tag (defect_id, tag)
SELECT defect_id, 'release-7.4'
FROM defect;

INSERT INTO status_check (defect_id, check_name, status, completed_at)
SELECT defect_id, 'unit-tests', 'PASSED', now()
FROM defect
WHERE title = 'CSV export truncates Unicode names';

INSERT INTO status_check (defect_id, check_name, status, completed_at)
SELECT defect_id, 'security-scan', 'PASSED', now()
FROM defect
WHERE title = 'CSV export truncates Unicode names';

INSERT INTO status_check (defect_id, check_name, status)
SELECT defect_id, 'integration-tests', 'PENDING'
FROM defect
WHERE title = 'Authorization succeeds after account deactivation';

INSERT INTO verification (defect_id, tester_id, passed, evidence)
SELECT
    d.defect_id,
    u.user_id,
    true,
    'Regression test confirmed complete Unicode preservation.'
FROM defect d
JOIN app_user u ON u.username = 'vikram.qa'
WHERE d.title = 'CSV export truncates Unicode names';

INSERT INTO defect_policy (
    repository_id,
    required_approvals,
    require_all_checks,
    require_verification,
    critical_requires_manager
)
SELECT repository_id, 2, true, true, true
FROM repository
WHERE repository_name = 'commerce-platform';

-- Triage and assignment of the security defect.
UPDATE defect
SET status = 'TRIAGED'
WHERE title = 'Authorization succeeds after account deactivation';

UPDATE defect
SET
    status = 'ASSIGNED',
    assignee_id = (SELECT user_id FROM app_user WHERE username = 'ravi.dev')
WHERE title = 'Authorization succeeds after account deactivation';

UPDATE defect
SET status = 'IN_PROGRESS'
WHERE title = 'Authorization succeeds after account deactivation';

UPDATE defect
SET
    status = 'RESOLVED',
    resolution = 'FIXED',
    resolution_notes = 'Authorization now checks account state for every protected request.'
WHERE title = 'Authorization succeeds after account deactivation';

-- This intentionally records an unresolved verification condition.
INSERT INTO verification (defect_id, tester_id, passed, evidence)
SELECT
    d.defect_id,
    u.user_id,
    false,
    'Regression test still reproduced the stale-session authorization path.'
FROM defect d
JOIN app_user u ON u.username = 'vikram.qa'
WHERE d.title = 'Authorization succeeds after account deactivation';

UPDATE defect
SET status = 'REOPENED'
WHERE title = 'Authorization succeeds after account deactivation';

-- Evaluation view separates operational defect state from policy decision.
CREATE OR REPLACE VIEW defect_merge_eligibility AS
WITH check_state AS (
    SELECT
        d.defect_id,
        count(sc.check_id) FILTER (WHERE sc.status = 'FAILED') AS failed_checks,
        count(sc.check_id) FILTER (WHERE sc.status = 'PENDING') AS pending_checks
    FROM defect d
    LEFT JOIN status_check sc ON sc.defect_id = d.defect_id
    GROUP BY d.defect_id
),
verification_state AS (
    SELECT
        defect_id,
        bool_or(passed) AS verified
    FROM verification
    GROUP BY defect_id
),
approval_policy AS (
    SELECT
        r.repository_id,
        dp.required_approvals,
        dp.require_all_checks,
        dp.require_verification,
        dp.critical_requires_manager
    FROM repository r
    JOIN defect_policy dp
      ON dp.repository_id = r.repository_id
     AND dp.active
)
SELECT
    d.defect_id,
    d.title,
    d.severity,
    d.priority,
    d.status,
    CASE
        WHEN d.status <> 'VERIFIED'
            THEN false
        WHEN cs.failed_checks > 0
            THEN false
        WHEN ap.require_all_checks AND cs.pending_checks > 0
            THEN false
        WHEN ap.require_verification AND COALESCE(vs.verified, false) = false
            THEN false
        WHEN d.severity IN ('BLOCKER', 'CRITICAL')
            AND ap.critical_requires_manager
            THEN false
        ELSE true
    END AS eligible_for_release_workflow
FROM defect d
JOIN check_state cs ON cs.defect_id = d.defect_id
JOIN approval_policy ap ON ap.repository_id = d.repository_id
LEFT JOIN verification_state vs ON vs.defect_id = d.defect_id;

-- Retrieval of active defects by severity and priority.
SELECT
    defect_id,
    title,
    status,
    severity,
    priority,
    assignee_id
FROM defect
WHERE status NOT IN ('CLOSED', 'REJECTED')
ORDER BY
    CASE severity
        WHEN 'BLOCKER' THEN 1
        WHEN 'CRITICAL' THEN 2
        WHEN 'MAJOR' THEN 3
        WHEN 'MINOR' THEN 4
        WHEN 'TRIVIAL' THEN 5
    END,
    CASE priority
        WHEN 'P0' THEN 1
        WHEN 'P1' THEN 2
        WHEN 'P2' THEN 3
        WHEN 'P3' THEN 4
    END,
    defect_id;

-- Defect distribution by severity.
SELECT
    severity,
    count(*) AS defect_count,
    count(*) FILTER (
        WHERE status NOT IN ('CLOSED', 'REJECTED')
    ) AS open_count
FROM defect
GROUP BY severity
ORDER BY defect_count DESC;

-- Verification quality: identify reopened defects.
SELECT
    d.defect_id,
    d.title,
    d.status,
    v.verified_at,
    v.evidence
FROM defect d
JOIN verification v ON v.defect_id = d.defect_id
WHERE d.status = 'REOPENED'
ORDER BY v.verified_at DESC;

-- Current policy evaluation.
SELECT *
FROM defect_merge_eligibility
ORDER BY defect_id;

-- Audit trail for lifecycle transitions.
SELECT
    h.defect_id,
    h.previous_status,
    h.new_status,
    h.event_note,
    h.occurred_at
FROM defect_history h
ORDER BY h.defect_id, h.occurred_at;

-- Transactional example: a complete resolution update either commits
-- together or leaves the defect unchanged.
BEGIN;

UPDATE defect
SET
    status = 'IN_PROGRESS'
WHERE title = 'Dashboard date filter disappears after pagination'
  AND status = 'NEW';

UPDATE defect
SET
    status = 'RESOLVED',
    assignee_id = (SELECT user_id FROM app_user WHERE username = 'ravi.dev'),
    resolution = 'FIXED',
    resolution_notes = 'Persisted date range in server-side search state.'
WHERE title = 'Dashboard date filter disappears after pagination'
  AND status = 'IN_PROGRESS';

COMMIT;

-- Reporting query combining ownership, lifecycle, and resolution state.
SELECT
    d.defect_id,
    d.title,
    r.repository_name,
    reporter.display_name AS reporter,
    assignee.display_name AS assignee,
    d.severity,
    d.priority,
    d.status,
    d.resolution,
    d.created_at,
    d.resolved_at,
    d.closed_at
FROM defect d
JOIN repository r ON r.repository_id = d.repository_id
JOIN app_user reporter ON reporter.user_id = d.reporter_id
LEFT JOIN app_user assignee ON assignee.user_id = d.assignee_id
ORDER BY d.created_at DESC;
