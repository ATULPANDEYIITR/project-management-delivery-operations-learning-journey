-- ============================================================
-- CONFLICT MANAGEMENT SYSTEM
-- PostgreSQL 15+
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS conflict_management;

SET search_path TO conflict_management, public;

-- ------------------------------------------------------------
-- DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE conflict_type AS ENUM (
    'communication',
    'role_ambiguity',
    'resource_allocation',
    'performance',
    'personal_disagreement',
    'priority_mismatch',
    'working_style'
);

CREATE TYPE conflict_severity AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE conflict_status AS ENUM (
    'reported',
    'assessment',
    'discussion',
    'mediation',
    'resolved',
    'escalated',
    'closed'
);

CREATE TYPE resolution_method AS ENUM (
    'collaboration',
    'compromise',
    'accommodation',
    'negotiation',
    'manager_decision',
    'formal_escalation'
);

CREATE TYPE employee_role AS ENUM (
    'employee',
    'manager',
    'hr_mediator',
    'administrator'
);

-- ------------------------------------------------------------
-- EMPLOYEE RECORDS
-- ------------------------------------------------------------

CREATE TABLE employees (
    employee_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    role employee_role NOT NULL DEFAULT 'employee',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_employee_name
        CHECK (LENGTH(TRIM(full_name)) > 0)
);

-- ------------------------------------------------------------
-- CONFLICT CASES
-- ------------------------------------------------------------

CREATE TABLE conflict_cases (
    case_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    case_reference VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    conflict_category conflict_type NOT NULL,
    severity conflict_severity NOT NULL DEFAULT 'medium',
    status conflict_status NOT NULL DEFAULT 'reported',
    reporter_id VARCHAR(20) NOT NULL
        REFERENCES employees(employee_id),
    mediator_id VARCHAR(20)
        REFERENCES employees(employee_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT valid_case_title
        CHECK (LENGTH(TRIM(title)) > 0),

    CONSTRAINT valid_case_description
        CHECK (LENGTH(TRIM(description)) > 0),

    CONSTRAINT valid_case_version
        CHECK (version >= 0),

    CONSTRAINT valid_resolution_timestamp
        CHECK (
            resolved_at IS NULL
            OR resolved_at >= created_at
        ),

    CONSTRAINT valid_closure_timestamp
        CHECK (
            closed_at IS NULL
            OR closed_at >= created_at
        )
);

-- ------------------------------------------------------------
-- CONFLICT PARTICIPANTS
-- ------------------------------------------------------------

CREATE TABLE conflict_participants (
    case_id BIGINT NOT NULL
        REFERENCES conflict_cases(case_id) ON DELETE CASCADE,
    employee_id VARCHAR(20) NOT NULL
        REFERENCES employees(employee_id),
    participation_role VARCHAR(30) NOT NULL DEFAULT 'participant',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (case_id, employee_id),

    CONSTRAINT valid_participation_role
        CHECK (
            participation_role IN (
                'participant',
                'reporter',
                'representative'
            )
        )
);

-- ------------------------------------------------------------
-- STATUS HISTORY
-- ------------------------------------------------------------

CREATE TABLE conflict_status_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    case_id BIGINT NOT NULL
        REFERENCES conflict_cases(case_id) ON DELETE CASCADE,
    previous_status conflict_status,
    new_status conflict_status NOT NULL,
    changed_by VARCHAR(20) NOT NULL
        REFERENCES employees(employee_id),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason TEXT
);

-- ------------------------------------------------------------
-- DISCUSSION RECORDS
-- ------------------------------------------------------------

CREATE TABLE conflict_discussions (
    discussion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    case_id BIGINT NOT NULL
        REFERENCES conflict_cases(case_id) ON DELETE CASCADE,
    author_id VARCHAR(20) NOT NULL
        REFERENCES employees(employee_id),
    discussion_type VARCHAR(30) NOT NULL DEFAULT 'discussion',
    content TEXT NOT NULL,
    confidential BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_discussion_type
        CHECK (
            discussion_type IN (
                'discussion',
                'mediation',
                'observation',
                'meeting_record'
            )
        ),

    CONSTRAINT valid_discussion_content
        CHECK (LENGTH(TRIM(content)) > 0)
);

-- ------------------------------------------------------------
-- RESOLUTION AGREEMENTS
-- ------------------------------------------------------------

CREATE TABLE resolution_agreements (
    agreement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    case_id BIGINT NOT NULL
        REFERENCES conflict_cases(case_id) ON DELETE CASCADE,
    method resolution_method NOT NULL,
    actions JSONB NOT NULL,
    success_criteria JSONB NOT NULL,
    deadline TIMESTAMPTZ NOT NULL,
    created_by VARCHAR(20) NOT NULL
        REFERENCES employees(employee_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_actions
        CHECK (
            jsonb_typeof(actions) = 'array'
            AND jsonb_array_length(actions) > 0
        ),

    CONSTRAINT valid_success_criteria
        CHECK (
            jsonb_typeof(success_criteria) = 'array'
            AND jsonb_array_length(success_criteria) > 0
        )
);

-- ------------------------------------------------------------
-- AGREEMENT RESPONSIBILITIES
-- ------------------------------------------------------------

CREATE TABLE agreement_responsibilities (
    agreement_id BIGINT NOT NULL
        REFERENCES resolution_agreements(agreement_id)
        ON DELETE CASCADE,
    employee_id VARCHAR(20) NOT NULL
        REFERENCES employees(employee_id),
    action_description TEXT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,

    PRIMARY KEY (agreement_id, employee_id, action_description),

    CONSTRAINT valid_action_description
        CHECK (LENGTH(TRIM(action_description)) > 0),

    CONSTRAINT completion_timestamp_consistency
        CHECK (
            (completed = FALSE AND completed_at IS NULL)
            OR
            (completed = TRUE AND completed_at IS NOT NULL)
        )
);

-- ------------------------------------------------------------
-- AGREEMENT ACCEPTANCES
-- ------------------------------------------------------------

CREATE TABLE agreement_acceptances (
    agreement_id BIGINT NOT NULL
        REFERENCES resolution_agreements(agreement_id)
        ON DELETE CASCADE,
    employee_id VARCHAR(20) NOT NULL
        REFERENCES employees(employee_id),
    accepted BOOLEAN NOT NULL DEFAULT TRUE,
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    comments TEXT,

    PRIMARY KEY (agreement_id, employee_id)
);

-- ------------------------------------------------------------
-- MANAGEMENT AUDIT LOG
-- ------------------------------------------------------------

CREATE TABLE conflict_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    case_id BIGINT
        REFERENCES conflict_cases(case_id) ON DELETE SET NULL,
    actor_id VARCHAR(20)
        REFERENCES employees(employee_id),
    action VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------

CREATE INDEX idx_conflict_status_severity
    ON conflict_cases(status, severity);

CREATE INDEX idx_conflict_created_at
    ON conflict_cases(created_at DESC);

CREATE INDEX idx_conflict_reporter
    ON conflict_cases(reporter_id);

CREATE INDEX idx_participant_employee
    ON conflict_participants(employee_id);

CREATE INDEX idx_discussion_case_time
    ON conflict_discussions(case_id, created_at DESC);

CREATE INDEX idx_agreement_deadline
    ON resolution_agreements(deadline);

CREATE INDEX idx_audit_case_time
    ON conflict_audit_log(case_id, occurred_at DESC);

CREATE INDEX idx_active_open_cases
    ON conflict_cases(severity, created_at)
    WHERE status NOT IN ('resolved', 'closed');

-- ------------------------------------------------------------
-- STATUS TRANSITION VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_conflict_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    allowed BOOLEAN := FALSE;
BEGIN
    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;

    allowed := CASE OLD.status
        WHEN 'reported' THEN
            NEW.status IN ('assessment', 'escalated')
        WHEN 'assessment' THEN
            NEW.status IN ('discussion', 'mediation', 'escalated')
        WHEN 'discussion' THEN
            NEW.status IN ('mediation', 'resolved', 'escalated')
        WHEN 'mediation' THEN
            NEW.status IN ('discussion', 'resolved', 'escalated')
        WHEN 'resolved' THEN
            NEW.status IN ('closed', 'escalated')
        WHEN 'escalated' THEN
            NEW.status = 'closed'
        WHEN 'closed' THEN
            FALSE
        ELSE FALSE
    END;

    IF NOT allowed THEN
        RAISE EXCEPTION
            'Invalid conflict transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    NEW.version := OLD.version + 1;
    NEW.updated_at := NOW();

    IF NEW.status = 'resolved' THEN
        NEW.resolved_at := NOW();
    END IF;

    IF NEW.status = 'closed' THEN
        NEW.closed_at := NOW();
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_conflict_transition
BEFORE UPDATE OF status ON conflict_cases
FOR EACH ROW
EXECUTE FUNCTION validate_conflict_transition();

-- ------------------------------------------------------------
-- AUTOMATIC STATUS HISTORY
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION record_conflict_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    actor VARCHAR(20);
BEGIN
    actor := COALESCE(
        NULLIF(current_setting('app.actor_id', TRUE), ''),
        NEW.reporter_id
    );

    IF TG_OP = 'INSERT' THEN
        INSERT INTO conflict_status_history (
            case_id,
            previous_status,
            new_status,
            changed_by,
            reason
        )
        VALUES (
            NEW.case_id,
            NULL,
            NEW.status,
            actor,
            'Initial case creation'
        );

    ELSIF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO conflict_status_history (
            case_id,
            previous_status,
            new_status,
            changed_by,
            reason
        )
        VALUES (
            NEW.case_id,
            OLD.status,
            NEW.status,
            actor,
            'Status transition'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_record_conflict_status
AFTER INSERT OR UPDATE OF status ON conflict_cases
FOR EACH ROW
EXECUTE FUNCTION record_conflict_status();

-- ------------------------------------------------------------
-- MEDIATOR INDEPENDENCE
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_mediator_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.mediator_id IS NULL THEN
        RETURN NEW;
    END IF;

    IF NEW.mediator_id = NEW.reporter_id THEN
        RAISE EXCEPTION
            'Reporter cannot mediate their own conflict';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM conflict_participants
        WHERE case_id = NEW.case_id
          AND employee_id = NEW.mediator_id
    ) THEN
        RAISE EXCEPTION
            'A participant cannot mediate their own conflict';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM employees
        WHERE employee_id = NEW.mediator_id
          AND active = TRUE
          AND role IN ('hr_mediator', 'administrator')
    ) THEN
        RAISE EXCEPTION
            'Mediator must have an eligible active role';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_mediator
BEFORE INSERT OR UPDATE OF mediator_id ON conflict_cases
FOR EACH ROW
EXECUTE FUNCTION validate_mediator_assignment();

-- ------------------------------------------------------------
-- PARTICIPANT VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_participant()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM employees
        WHERE employee_id = NEW.employee_id
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION 'Participant is inactive or unavailable';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM conflict_cases
        WHERE case_id = NEW.case_id
          AND mediator_id = NEW.employee_id
    ) THEN
        RAISE EXCEPTION
            'Mediator cannot be a conflict participant';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_participant
BEFORE INSERT ON conflict_participants
FOR EACH ROW
EXECUTE FUNCTION validate_participant();

-- ------------------------------------------------------------
-- AGREEMENT ACCEPTANCE VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_agreement_acceptance()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    target_case BIGINT;
BEGIN
    SELECT case_id
    INTO target_case
    FROM resolution_agreements
    WHERE agreement_id = NEW.agreement_id;

    IF NOT EXISTS (
        SELECT 1
        FROM conflict_participants
        WHERE case_id = target_case
          AND employee_id = NEW.employee_id
    ) THEN
        RAISE EXCEPTION
            'Only conflict participants can accept an agreement';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_acceptance
BEFORE INSERT OR UPDATE ON agreement_acceptances
FOR EACH ROW
EXECUTE FUNCTION validate_agreement_acceptance();

-- ------------------------------------------------------------
-- MERGE-FREE RESOLUTION ELIGIBILITY
-- Every participant must accept the agreement.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION can_resolve_conflict(
    target_case BIGINT
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT
        EXISTS (
            SELECT 1
            FROM conflict_cases
            WHERE case_id = target_case
              AND status IN ('discussion', 'mediation')
        )
        AND EXISTS (
            SELECT 1
            FROM resolution_agreements
            WHERE case_id = target_case
        )
        AND NOT EXISTS (
            SELECT 1
            FROM conflict_participants cp
            WHERE cp.case_id = target_case
              AND NOT EXISTS (
                  SELECT 1
                  FROM agreement_acceptances aa
                  JOIN resolution_agreements ra
                    ON ra.agreement_id = aa.agreement_id
                  WHERE ra.case_id = target_case
                    AND aa.employee_id = cp.employee_id
                    AND aa.accepted = TRUE
              )
        );
$$;

-- ------------------------------------------------------------
-- RESOLUTION ENFORCEMENT
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_resolution_acceptance()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'resolved'
       AND OLD.status IS DISTINCT FROM NEW.status THEN

        IF NOT can_resolve_conflict(NEW.case_id) THEN
            RAISE EXCEPTION
                'Resolution requires a valid agreement accepted by all participants';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_enforce_resolution
BEFORE UPDATE OF status ON conflict_cases
FOR EACH ROW
EXECUTE FUNCTION enforce_resolution_acceptance();

-- ------------------------------------------------------------
-- AUDIT EVENT FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION record_conflict_audit(
    target_case BIGINT,
    target_actor VARCHAR(20),
    target_action VARCHAR(100),
    target_data JSONB DEFAULT '{}'::JSONB
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO conflict_audit_log (
        case_id,
        actor_id,
        action,
        event_data
    )
    VALUES (
        target_case,
        target_actor,
        target_action,
        COALESCE(target_data, '{}'::JSONB)
    );
END;
$$;

-- ------------------------------------------------------------
-- BUSINESS PROCEDURE: ASSIGN MEDIATOR
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE assign_mediator(
    target_case BIGINT,
    target_mediator VARCHAR(20),
    actor VARCHAR(20)
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM employees
        WHERE employee_id = actor
          AND active = TRUE
          AND role IN ('manager', 'administrator')
    ) THEN
        RAISE EXCEPTION
            'Only an authorized manager can assign a mediator';
    END IF;

    UPDATE conflict_cases
    SET mediator_id = target_mediator
    WHERE case_id = target_case;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Conflict case not found';
    END IF;

    PERFORM record_conflict_audit(
        target_case,
        actor,
        'MEDIATOR_ASSIGNED',
        jsonb_build_object('mediator_id', target_mediator)
    );
END;
$$;

-- ------------------------------------------------------------
-- REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW conflict_case_overview AS
SELECT
    c.case_reference,
    c.title,
    c.conflict_category,
    c.severity,
    c.status,
    reporter.full_name AS reporter,
    mediator.full_name AS mediator,
    COUNT(DISTINCT cp.employee_id) AS participant_count,
    COUNT(DISTINCT d.discussion_id) AS discussion_count,
    MAX(ra.deadline) AS agreement_deadline,
    c.created_at,
    c.updated_at
FROM conflict_cases c
JOIN employees reporter
    ON reporter.employee_id = c.reporter_id
LEFT JOIN employees mediator
    ON mediator.employee_id = c.mediator_id
LEFT JOIN conflict_participants cp
    ON cp.case_id = c.case_id
LEFT JOIN conflict_discussions d
    ON d.case_id = c.case_id
LEFT JOIN resolution_agreements ra
    ON ra.case_id = c.case_id
GROUP BY
    c.case_id,
    reporter.full_name,
    mediator.full_name;

-- ------------------------------------------------------------
-- SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO employees (
    employee_id, full_name, email, department,
    job_title, role
)
VALUES
(
    'E01', 'Ananya Sharma', 'ananya@example.org',
    'Engineering', 'Software Developer', 'employee'
),
(
    'E02', 'Rahul Verma', 'rahul@example.org',
    'Product', 'Product Designer', 'employee'
),
(
    'E03', 'Priya Singh', 'priya@example.org',
    'Management', 'Engineering Manager', 'manager'
),
(
    'E04', 'Arjun Mehta', 'arjun@example.org',
    'Human Resources', 'HR Mediator', 'hr_mediator'
),
(
    'E05', 'Neha Gupta', 'neha@example.org',
    'Engineering', 'Quality Analyst', 'employee'
);

INSERT INTO conflict_cases (
    case_reference,
    title,
    description,
    conflict_category,
    severity,
    reporter_id
)
VALUES
(
    'CF-5001',
    'Release priority disagreement',
    'Engineering and Product disagree about release priorities.',
    'priority_mismatch',
    'medium',
    'E01'
),
(
    'CF-5002',
    'Resource allocation dispute',
    'Two teams need the same testing resources.',
    'resource_allocation',
    'high',
    'E05'
),
(
    'CF-5003',
    'Communication breakdown',
    'Unclear communication has affected team coordination.',
    'communication',
    'low',
    'E02'
),
(
    'CF-5004',
    'Critical workplace incident',
    'A serious workplace issue requires independent review.',
    'personal_disagreement',
    'critical',
    'E01'
);

INSERT INTO conflict_participants (
    case_id,
    employee_id,
    participation_role
)
SELECT case_id, 'E01', 'reporter'
FROM conflict_cases
WHERE case_reference IN ('CF-5001', 'CF-5004');

INSERT INTO conflict_participants (
    case_id,
    employee_id
)
SELECT case_id, 'E02'
FROM conflict_cases
WHERE case_reference = 'CF-5001';

INSERT INTO conflict_participants (
    case_id,
    employee_id
)
SELECT case_id, 'E05'
FROM conflict_cases
WHERE case_reference = 'CF-5002';

INSERT INTO conflict_participants (
    case_id,
    employee_id
)
SELECT case_id, 'E02'
FROM conflict_cases
WHERE case_reference = 'CF-5003';

-- Assign an independent mediator.
CALL assign_mediator(
    (SELECT case_id FROM conflict_cases
     WHERE case_reference = 'CF-5001'),
    'E04',
    'E03'
);

-- Record discussions.
INSERT INTO conflict_discussions (
    case_id, author_id, content, discussion_type
)
SELECT case_id, 'E01',
       'Engineering requires more testing time.',
       'discussion'
FROM conflict_cases
WHERE case_reference = 'CF-5001';

INSERT INTO conflict_discussions (
    case_id, author_id, content, discussion_type
)
SELECT case_id, 'E02',
       'Product needs core features in the current release.',
       'discussion'
FROM conflict_cases
WHERE case_reference = 'CF-5001';

-- ------------------------------------------------------------
-- TRANSACTION: CREATE A VALID RESOLUTION AGREEMENT
-- ------------------------------------------------------------

DO $$
DECLARE
    target_case BIGINT;
    target_agreement BIGINT;
BEGIN
    SELECT case_id
    INTO target_case
    FROM conflict_cases
    WHERE case_reference = 'CF-5001';

    UPDATE conflict_cases
    SET status = 'assessment'
    WHERE case_id = target_case;

    UPDATE conflict_cases
    SET status = 'discussion'
    WHERE case_id = target_case;

    INSERT INTO resolution_agreements (
        case_id,
        method,
        actions,
        success_criteria,
        deadline,
        created_by
    )
    VALUES (
        target_case,
        'collaboration',
        '[
            "Deliver core features first",
            "Move optional features to the next iteration",
            "Conduct joint acceptance testing"
        ]'::JSONB,
        '[
            "Acceptance tests pass",
            "Both teams approve the release plan"
        ]'::JSONB,
        NOW() + INTERVAL '14 days',
        'E03'
    )
    RETURNING agreement_id INTO target_agreement;

    INSERT INTO agreement_responsibilities (
        agreement_id,
        employee_id,
        action_description
    )
    VALUES
    (
        target_agreement,
        'E01',
        'Complete engineering testing'
    ),
    (
        target_agreement,
        'E02',
        'Approve product acceptance criteria'
    );

    -- Both participants explicitly accept.
    INSERT INTO agreement_acceptances (
        agreement_id,
        employee_id,
        accepted,
        comments
    )
    VALUES
    (
        target_agreement,
        'E01',
        TRUE,
        'Testing commitments accepted'
    ),
    (
        target_agreement,
        'E02',
        TRUE,
        'Release scope accepted'
    );

    -- Resolution trigger checks participant acceptance.
    UPDATE conflict_cases
    SET status = 'resolved'
    WHERE case_id = target_case;

    UPDATE conflict_cases
    SET status = 'closed'
    WHERE case_id = target_case;

    PERFORM record_conflict_audit(
        target_case,
        'E03',
        'CASE_CLOSED',
        jsonb_build_object(
            'agreement_id', target_agreement
        )
    );
END;
$$;

-- ------------------------------------------------------------
-- RETRIEVAL QUERIES
-- ------------------------------------------------------------

SELECT *
FROM conflict_case_overview
ORDER BY created_at DESC;

-- Open cases by severity.
SELECT
    case_reference,
    title,
    severity,
    status,
    created_at
FROM conflict_cases
WHERE status NOT IN ('resolved', 'closed')
ORDER BY severity DESC, created_at;

-- Participants for each case.
SELECT
    c.case_reference,
    e.full_name,
    e.department,
    cp.participation_role
FROM conflict_participants cp
JOIN conflict_cases c
    ON c.case_id = cp.case_id
JOIN employees e
    ON e.employee_id = cp.employee_id
ORDER BY c.case_reference, e.full_name;

-- ------------------------------------------------------------
-- AGGREGATION AND EVALUATION
-- ------------------------------------------------------------

SELECT
    severity,
    COUNT(*) AS total_cases
FROM conflict_cases
GROUP BY severity
ORDER BY severity;

SELECT
    conflict_category,
    COUNT(*) AS case_count,
    COUNT(*) FILTER (
        WHERE status = 'resolved'
    ) AS resolved_count,
    COUNT(*) FILTER (
        WHERE status = 'escalated'
    ) AS escalated_count
FROM conflict_cases
GROUP BY conflict_category
ORDER BY case_count DESC;

-- Resolution rate for cases eligible for closure.
SELECT
    COUNT(*) AS total_cases,
    COUNT(*) FILTER (
        WHERE status IN ('resolved', 'closed')
    ) AS resolved_cases,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE status IN ('resolved', 'closed')
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS resolution_percentage
FROM conflict_cases;

-- ------------------------------------------------------------
-- WORKFLOW ELIGIBILITY
-- ------------------------------------------------------------

SELECT
    c.case_reference,
    c.status,
    can_resolve_conflict(c.case_id) AS resolution_eligible
FROM conflict_cases c
ORDER BY c.case_reference;

-- Cases requiring escalation.
SELECT
    case_reference,
    title,
    severity,
    created_at
FROM conflict_cases
WHERE severity = 'critical'
  AND status NOT IN ('resolved', 'closed')
ORDER BY created_at;

-- ------------------------------------------------------------
-- AGREEMENT COMPLETION REPORT
-- ------------------------------------------------------------

SELECT
    c.case_reference,
    ra.agreement_id,
    ra.method,
    COUNT(ar.employee_id) AS assigned_actions,
    COUNT(ar.employee_id) FILTER (
        WHERE ar.completed = TRUE
    ) AS completed_actions,
    COUNT(aa.employee_id) FILTER (
        WHERE aa.accepted = TRUE
    ) AS acceptances,
    ra.deadline
FROM resolution_agreements ra
JOIN conflict_cases c
    ON c.case_id = ra.case_id
LEFT JOIN agreement_responsibilities ar
    ON ar.agreement_id = ra.agreement_id
LEFT JOIN agreement_acceptances aa
    ON aa.agreement_id = ra.agreement_id
GROUP BY
    c.case_reference,
    ra.agreement_id,
    ra.method,
    ra.deadline;

-- ------------------------------------------------------------
-- STATUS HISTORY REPORT
-- ------------------------------------------------------------

SELECT
    c.case_reference,
    h.previous_status,
    h.new_status,
    e.full_name AS changed_by,
    h.changed_at,
    h.reason
FROM conflict_status_history h
JOIN conflict_cases c
    ON c.case_id = h.case_id
JOIN employees e
    ON e.employee_id = h.changed_by
ORDER BY h.changed_at;

-- ------------------------------------------------------------
-- AUDIT REPORT
-- ------------------------------------------------------------

SELECT
    audit_id,
    case_id,
    actor_id,
    action,
    event_data,
    occurred_at
FROM conflict_audit_log
ORDER BY occurred_at DESC;

-- ------------------------------------------------------------
-- DEMONSTRATE FAILURE HANDLING
-- The exception is caught inside the block so execution continues.
-- ------------------------------------------------------------

DO $$
BEGIN
    BEGIN
        UPDATE conflict_cases
        SET status = 'reported'
        WHERE case_reference = 'CF-5001';

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected invalid transition rejected: %',
                SQLERRM;
    END;
END;
$$;

COMMIT;
