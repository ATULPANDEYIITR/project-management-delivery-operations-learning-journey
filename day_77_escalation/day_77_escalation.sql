-- ============================================================
-- ESCALATION MANAGEMENT AND CRITICAL PROBLEM REPORTING
-- PostgreSQL 15+
--
-- Covers:
-- Incident reporting, severity policies, ownership, escalation,
-- acknowledgements, deadlines, notifications, audit history,
-- resolution evidence, permissions and management reporting.
--
-- All timestamps use TIMESTAMPTZ.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS escalation;

SET search_path TO escalation, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE severity_level AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);

CREATE TYPE incident_status AS ENUM (
    'REPORTED',
    'ACKNOWLEDGED',
    'INVESTIGATING',
    'ESCALATED',
    'RESOLVED',
    'CLOSED'
);

CREATE TYPE escalation_level AS ENUM (
    'LEVEL_1',
    'LEVEL_2',
    'LEVEL_3',
    'EXECUTIVE'
);

CREATE TYPE actor_role AS ENUM (
    'REPORTER',
    'RESPONDER',
    'TEAM_LEAD',
    'INCIDENT_MANAGER',
    'ADMINISTRATOR'
);

CREATE TYPE notification_status AS ENUM (
    'PENDING',
    'DELIVERED',
    'FAILED',
    'RETRY'
);

-- ------------------------------------------------------------
-- 2. ACTORS AND DEPARTMENTS
-- ------------------------------------------------------------

CREATE TABLE departments (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE actors (
    actor_id VARCHAR(80) PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role actor_role NOT NULL,
    department_id BIGINT NOT NULL
        REFERENCES departments(department_id),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT actor_name_nonempty
        CHECK (LENGTH(TRIM(full_name)) > 0)
);

-- ------------------------------------------------------------
-- 3. ESCALATION POLICIES
-- ------------------------------------------------------------

CREATE TABLE escalation_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    severity severity_level NOT NULL UNIQUE,
    acknowledgement_minutes INTEGER NOT NULL,
    resolution_minutes INTEGER NOT NULL,
    initial_level escalation_level NOT NULL,
    automatic_notification BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT positive_acknowledgement
        CHECK (acknowledgement_minutes > 0),

    CONSTRAINT valid_resolution_window
        CHECK (resolution_minutes > acknowledgement_minutes)
);

INSERT INTO escalation_policies (
    severity,
    acknowledgement_minutes,
    resolution_minutes,
    initial_level
)
VALUES
    ('LOW', 480, 2880, 'LEVEL_1'),
    ('MEDIUM', 120, 1440, 'LEVEL_1'),
    ('HIGH', 30, 240, 'LEVEL_2'),
    ('CRITICAL', 10, 60, 'EXECUTIVE');

-- ------------------------------------------------------------
-- 4. INCIDENT REGISTER
-- ------------------------------------------------------------

CREATE TABLE incidents (
    incident_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    incident_reference VARCHAR(30) NOT NULL UNIQUE,

    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(80) NOT NULL,

    severity severity_level NOT NULL,
    status incident_status NOT NULL DEFAULT 'REPORTED',
    escalation_level escalation_level NOT NULL,

    department_id BIGINT NOT NULL
        REFERENCES departments(department_id),

    reporter_id VARCHAR(80) NOT NULL
        REFERENCES actors(actor_id),

    assigned_to VARCHAR(80)
        REFERENCES actors(actor_id),

    parent_incident_id BIGINT
        REFERENCES incidents(incident_id),

    reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledgement_deadline TIMESTAMPTZ NOT NULL,
    resolution_deadline TIMESTAMPTZ NOT NULL,

    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,

    resolution_notes TEXT,

    version INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT valid_title
        CHECK (LENGTH(TRIM(title)) > 0),

    CONSTRAINT valid_description
        CHECK (LENGTH(TRIM(description)) > 0),

    CONSTRAINT valid_deadlines
        CHECK (
            acknowledgement_deadline > reported_at
            AND resolution_deadline > acknowledgement_deadline
        ),

    CONSTRAINT valid_acknowledgement_time
        CHECK (
            acknowledged_at IS NULL
            OR acknowledged_at >= reported_at
        ),

    CONSTRAINT valid_resolution_time
        CHECK (
            resolved_at IS NULL
            OR resolved_at >= reported_at
        ),

    CONSTRAINT valid_closure_time
        CHECK (
            closed_at IS NULL
            OR resolved_at IS NOT NULL
        ),

    CONSTRAINT valid_resolution_evidence
        CHECK (
            status NOT IN ('RESOLVED', 'CLOSED')
            OR (
                resolved_at IS NOT NULL
                AND resolution_notes IS NOT NULL
                AND LENGTH(TRIM(resolution_notes)) > 0
            )
        )
);

CREATE INDEX idx_incidents_severity_status
    ON incidents(severity, status);

CREATE INDEX idx_incidents_reported_at
    ON incidents(reported_at DESC);

CREATE INDEX idx_incidents_assignee
    ON incidents(assigned_to, status);

CREATE INDEX idx_incidents_deadlines
    ON incidents(resolution_deadline)
    WHERE status NOT IN ('RESOLVED', 'CLOSED');

CREATE INDEX idx_incidents_department
    ON incidents(department_id, reported_at DESC);

CREATE INDEX idx_incidents_parent
    ON incidents(parent_incident_id)
    WHERE parent_incident_id IS NOT NULL;

-- ------------------------------------------------------------
-- 5. INCIDENT TAGS
-- ------------------------------------------------------------

CREATE TABLE incident_tags (
    incident_id BIGINT NOT NULL
        REFERENCES incidents(incident_id) ON DELETE CASCADE,
    tag VARCHAR(60) NOT NULL,
    PRIMARY KEY (incident_id, tag),

    CHECK (LENGTH(TRIM(tag)) > 0)
);

CREATE INDEX idx_incident_tags_tag
    ON incident_tags(tag);

-- ------------------------------------------------------------
-- 6. INCIDENT STATE TRANSITION VALIDATION
-- ------------------------------------------------------------

CREATE FUNCTION validate_incident_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'REPORTED' THEN
            RAISE EXCEPTION
                'New incidents must start in REPORTED state';
        END IF;

        RETURN NEW;
    END IF;

    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'REPORTED'
            AND NEW.status IN ('ACKNOWLEDGED', 'ESCALATED'))

        OR (OLD.status = 'ACKNOWLEDGED'
            AND NEW.status IN ('INVESTIGATING', 'ESCALATED'))

        OR (OLD.status = 'INVESTIGATING'
            AND NEW.status IN ('ESCALATED', 'RESOLVED'))

        OR (OLD.status = 'ESCALATED'
            AND NEW.status IN (
                'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED'
            ))

        OR (OLD.status = 'RESOLVED'
            AND NEW.status IN ('CLOSED', 'INVESTIGATING'))
    ) THEN
        RAISE EXCEPTION
            'Invalid incident transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    NEW.version := OLD.version + 1;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_incident_transition
BEFORE INSERT OR UPDATE OF status
ON incidents
FOR EACH ROW
EXECUTE FUNCTION validate_incident_transition();

-- ------------------------------------------------------------
-- 7. AUTOMATIC INCIDENT DEADLINE CREATION
-- ------------------------------------------------------------

CREATE FUNCTION assign_incident_deadlines()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    selected_policy escalation_policies%ROWTYPE;
BEGIN
    SELECT *
    INTO selected_policy
    FROM escalation_policies
    WHERE severity = NEW.severity
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'No active policy for severity %',
            NEW.severity;
    END IF;

    NEW.reported_at := COALESCE(NEW.reported_at, NOW());

    NEW.acknowledgement_deadline :=
        NEW.reported_at
        + make_interval(
            mins => selected_policy.acknowledgement_minutes
        );

    NEW.resolution_deadline :=
        NEW.reported_at
        + make_interval(
            mins => selected_policy.resolution_minutes
        );

    NEW.escalation_level := selected_policy.initial_level;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_assign_incident_deadlines
BEFORE INSERT
ON incidents
FOR EACH ROW
EXECUTE FUNCTION assign_incident_deadlines();

-- ------------------------------------------------------------
-- 8. AUDIT HISTORY
-- ------------------------------------------------------------

CREATE TABLE incident_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    incident_id BIGINT NOT NULL
        REFERENCES incidents(incident_id),

    actor_id VARCHAR(80)
        REFERENCES actors(actor_id),

    action VARCHAR(100) NOT NULL,
    previous_value TEXT,
    new_value TEXT,
    details TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_incident_time
    ON incident_audit(incident_id, created_at DESC);

CREATE FUNCTION record_incident_audit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_actor VARCHAR(80);
BEGIN
    current_actor := NULLIF(
        current_setting('app.actor_id', TRUE),
        ''
    );

    IF TG_OP = 'INSERT' THEN
        INSERT INTO incident_audit (
            incident_id,
            actor_id,
            action,
            new_value,
            details
        )
        VALUES (
            NEW.incident_id,
            NEW.reporter_id,
            'INCIDENT_REPORTED',
            NEW.status::TEXT,
            NEW.title
        );

        RETURN NEW;
    END IF;

    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO incident_audit (
            incident_id,
            actor_id,
            action,
            previous_value,
            new_value
        )
        VALUES (
            NEW.incident_id,
            current_actor,
            'STATUS_CHANGED',
            OLD.status::TEXT,
            NEW.status::TEXT
        );
    END IF;

    IF NEW.assigned_to IS DISTINCT FROM OLD.assigned_to THEN
        INSERT INTO incident_audit (
            incident_id,
            actor_id,
            action,
            previous_value,
            new_value
        )
        VALUES (
            NEW.incident_id,
            current_actor,
            'ASSIGNEE_CHANGED',
            OLD.assigned_to,
            NEW.assigned_to
        );
    END IF;

    IF NEW.escalation_level IS DISTINCT FROM OLD.escalation_level THEN
        INSERT INTO incident_audit (
            incident_id,
            actor_id,
            action,
            previous_value,
            new_value
        )
        VALUES (
            NEW.incident_id,
            current_actor,
            'ESCALATION_LEVEL_CHANGED',
            OLD.escalation_level::TEXT,
            NEW.escalation_level::TEXT
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_record_incident_audit
AFTER INSERT OR UPDATE
ON incidents
FOR EACH ROW
EXECUTE FUNCTION record_incident_audit();

-- ------------------------------------------------------------
-- 9. ESCALATION HISTORY
-- ------------------------------------------------------------

CREATE TABLE escalation_history (
    escalation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    incident_id BIGINT NOT NULL
        REFERENCES incidents(incident_id),

    escalated_by VARCHAR(80) NOT NULL
        REFERENCES actors(actor_id),

    previous_level escalation_level NOT NULL,
    new_level escalation_level NOT NULL,

    reason TEXT NOT NULL,
    escalated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (new_level <> previous_level),
    CHECK (LENGTH(TRIM(reason)) > 0)
);

CREATE INDEX idx_escalation_history_incident
    ON escalation_history(incident_id, escalated_at DESC);

-- ------------------------------------------------------------
-- 10. NOTIFICATION QUEUE
-- ------------------------------------------------------------

CREATE TABLE notifications (
    notification_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    incident_id BIGINT NOT NULL
        REFERENCES incidents(incident_id),

    recipient VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,

    idempotency_key VARCHAR(255) NOT NULL UNIQUE,

    delivery_status notification_status
        NOT NULL DEFAULT 'PENDING',

    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,

    CHECK (attempt_count >= 0)
);

CREATE INDEX idx_notification_pending
    ON notifications(created_at)
    WHERE delivery_status IN ('PENDING', 'RETRY');

CREATE FUNCTION queue_incident_notification(
    p_incident_id BIGINT,
    p_recipient VARCHAR,
    p_event VARCHAR
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO notifications (
        incident_id,
        recipient,
        event_type,
        idempotency_key
    )
    VALUES (
        p_incident_id,
        p_recipient,
        p_event,
        p_incident_id::TEXT || ':' || p_event || ':' || p_recipient
    )
    ON CONFLICT (idempotency_key) DO NOTHING;
END;
$$;

CREATE FUNCTION notify_new_incident()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM queue_incident_notification(
        NEW.incident_id,
        'incident_management',
        'INCIDENT_REPORTED'
    );

    IF NEW.severity = 'CRITICAL' THEN
        PERFORM queue_incident_notification(
            NEW.incident_id,
            'executive_team',
            'CRITICAL_ALERT'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_notify_new_incident
AFTER INSERT
ON incidents
FOR EACH ROW
EXECUTE FUNCTION notify_new_incident();

-- ------------------------------------------------------------
-- 11. STATUS CHECKS
-- ------------------------------------------------------------

CREATE TABLE incident_status_checks (
    check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    incident_id BIGINT NOT NULL
        REFERENCES incidents(incident_id),

    check_name VARCHAR(120) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT TRUE,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    passed BOOLEAN NOT NULL DEFAULT FALSE,

    checked_by VARCHAR(80)
        REFERENCES actors(actor_id),

    checked_at TIMESTAMPTZ,

    CHECK (LENGTH(TRIM(check_name)) > 0),

    CHECK (
        passed = FALSE OR completed = TRUE
    )
);

CREATE INDEX idx_incident_checks
    ON incident_status_checks(incident_id, required, passed);

-- ------------------------------------------------------------
-- 12. APPROVAL REQUIREMENTS
-- ------------------------------------------------------------

CREATE TABLE incident_approval_requirements (
    requirement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    severity severity_level NOT NULL UNIQUE,
    required_approvals INTEGER NOT NULL,
    require_resolution_evidence BOOLEAN NOT NULL DEFAULT TRUE,
    require_owner BOOLEAN NOT NULL DEFAULT TRUE,
    require_status_checks BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (required_approvals >= 0)
);

INSERT INTO incident_approval_requirements (
    severity,
    required_approvals
)
VALUES
    ('LOW', 0),
    ('MEDIUM', 1),
    ('HIGH', 2),
    ('CRITICAL', 2);

CREATE TABLE incident_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    incident_id BIGINT NOT NULL
        REFERENCES incidents(incident_id),

    reviewer_id VARCHAR(80) NOT NULL
        REFERENCES actors(actor_id),

    approved BOOLEAN NOT NULL,

    decision_notes TEXT NOT NULL,

    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (incident_id, reviewer_id),

    CHECK (LENGTH(TRIM(decision_notes)) > 0)
);

-- ------------------------------------------------------------
-- 13. CENTRALIZED AUTHORIZATION
-- ------------------------------------------------------------

CREATE FUNCTION actor_can_manage(
    p_actor_id VARCHAR,
    p_severity severity_level
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM actors
        WHERE actor_id = p_actor_id
          AND active = TRUE
          AND (
              role IN ('ADMINISTRATOR', 'INCIDENT_MANAGER')
              OR role = 'RESPONDER'
              OR (
                  role = 'TEAM_LEAD'
                  AND p_severity <> 'CRITICAL'
              )
          )
    );
$$;

-- ------------------------------------------------------------
-- 14. REPORTING PROCEDURE
-- ------------------------------------------------------------

CREATE PROCEDURE report_incident(
    IN p_reporter_id VARCHAR,
    IN p_title VARCHAR,
    IN p_description TEXT,
    IN p_category VARCHAR,
    IN p_severity severity_level,
    IN p_department_id BIGINT,
    IN p_reference VARCHAR,
    IN p_parent_incident_id BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    new_incident_id BIGINT;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM actors
        WHERE actor_id = p_reporter_id
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION 'Invalid reporter.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM departments
        WHERE department_id = p_department_id
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION 'Invalid department.';
    END IF;

    IF LENGTH(TRIM(p_title)) = 0 THEN
        RAISE EXCEPTION 'Incident title cannot be empty.';
    END IF;

    IF LENGTH(TRIM(p_description)) = 0 THEN
        RAISE EXCEPTION 'Incident description cannot be empty.';
    END IF;

    IF p_parent_incident_id IS NOT NULL
       AND NOT EXISTS (
           SELECT 1
           FROM incidents
           WHERE incident_id = p_parent_incident_id
       ) THEN
        RAISE EXCEPTION 'Parent incident does not exist.';
    END IF;

    INSERT INTO incidents (
        incident_reference,
        title,
        description,
        category,
        severity,
        department_id,
        reporter_id,
        parent_incident_id,
        acknowledgement_deadline,
        resolution_deadline,
        escalation_level
    )
    VALUES (
        p_reference,
        p_title,
        p_description,
        p_category,
        p_severity,
        p_department_id,
        p_reporter_id,
        p_parent_incident_id,
        NOW() + INTERVAL '1 hour',
        NOW() + INTERVAL '2 hours',
        'LEVEL_1'
    )
    RETURNING incident_id INTO new_incident_id;

    RAISE NOTICE
        'Created incident ID: %',
        new_incident_id;
END;
$$;

-- ------------------------------------------------------------
-- 15. ASSIGNMENT PROCEDURE
-- ------------------------------------------------------------

CREATE PROCEDURE assign_incident(
    IN p_incident_id BIGINT,
    IN p_actor_id VARCHAR,
    IN p_assignee_id VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    selected_severity severity_level;
BEGIN
    SELECT severity
    INTO selected_severity
    FROM incidents
    WHERE incident_id = p_incident_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incident not found.';
    END IF;

    IF NOT actor_can_manage(p_actor_id, selected_severity) THEN
        RAISE EXCEPTION 'Actor is not authorized to assign incident.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM actors
        WHERE actor_id = p_assignee_id
          AND active = TRUE
          AND role IN (
              'RESPONDER',
              'TEAM_LEAD',
              'INCIDENT_MANAGER',
              'ADMINISTRATOR'
          )
    ) THEN
        RAISE EXCEPTION 'Invalid incident assignee.';
    END IF;

    PERFORM set_config('app.actor_id', p_actor_id, TRUE);

    UPDATE incidents
    SET assigned_to = p_assignee_id
    WHERE incident_id = p_incident_id;

    PERFORM queue_incident_notification(
        p_incident_id,
        p_assignee_id,
        'INCIDENT_ASSIGNED'
    );
END;
$$;

-- ------------------------------------------------------------
-- 16. ACKNOWLEDGEMENT PROCEDURE
-- ------------------------------------------------------------

CREATE PROCEDURE acknowledge_incident(
    IN p_incident_id BIGINT,
    IN p_actor_id VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    selected_severity severity_level;
BEGIN
    SELECT severity
    INTO selected_severity
    FROM incidents
    WHERE incident_id = p_incident_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incident not found.';
    END IF;

    IF NOT actor_can_manage(p_actor_id, selected_severity) THEN
        RAISE EXCEPTION 'Unauthorized acknowledgement.';
    END IF;

    PERFORM set_config('app.actor_id', p_actor_id, TRUE);

    UPDATE incidents
    SET status = 'ACKNOWLEDGED',
        acknowledged_at = NOW()
    WHERE incident_id = p_incident_id;

    PERFORM queue_incident_notification(
        p_incident_id,
        (
            SELECT reporter_id
            FROM incidents
            WHERE incident_id = p_incident_id
        ),
        'INCIDENT_ACKNOWLEDGED'
    );
END;
$$;

-- ------------------------------------------------------------
-- 17. ESCALATION PROCEDURE
-- ------------------------------------------------------------

CREATE PROCEDURE escalate_incident(
    IN p_incident_id BIGINT,
    IN p_actor_id VARCHAR,
    IN p_new_level escalation_level,
    IN p_reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_incident incidents%ROWTYPE;
    target_level INTEGER;
    previous_level INTEGER;
    recipient VARCHAR(255);
BEGIN
    SELECT *
    INTO current_incident
    FROM incidents
    WHERE incident_id = p_incident_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incident not found.';
    END IF;

    IF NOT actor_can_manage(p_actor_id, current_incident.severity) THEN
        RAISE EXCEPTION 'Unauthorized escalation.';
    END IF;

    IF current_incident.status IN ('RESOLVED', 'CLOSED') THEN
        RAISE EXCEPTION 'Completed incident cannot be escalated.';
    END IF;

    IF LENGTH(TRIM(p_reason)) = 0 THEN
        RAISE EXCEPTION 'Escalation reason is required.';
    END IF;

    previous_level := CASE current_incident.escalation_level
        WHEN 'LEVEL_1' THEN 1
        WHEN 'LEVEL_2' THEN 2
        WHEN 'LEVEL_3' THEN 3
        WHEN 'EXECUTIVE' THEN 4
    END;

    target_level := CASE p_new_level
        WHEN 'LEVEL_1' THEN 1
        WHEN 'LEVEL_2' THEN 2
        WHEN 'LEVEL_3' THEN 3
        WHEN 'EXECUTIVE' THEN 4
    END;

    IF target_level <= previous_level THEN
        RAISE EXCEPTION 'Escalation level must increase.';
    END IF;

    PERFORM set_config('app.actor_id', p_actor_id, TRUE);

    UPDATE incidents
    SET escalation_level = p_new_level,
        status = 'ESCALATED'
    WHERE incident_id = p_incident_id;

    INSERT INTO escalation_history (
        incident_id,
        escalated_by,
        previous_level,
        new_level,
        reason
    )
    VALUES (
        p_incident_id,
        p_actor_id,
        current_incident.escalation_level,
        p_new_level,
        p_reason
    );

    recipient := CASE
        WHEN p_new_level = 'EXECUTIVE'
            THEN 'executive_team'
        ELSE 'management_level_' || target_level::TEXT
    END;

    PERFORM queue_incident_notification(
        p_incident_id,
        recipient,
        'INCIDENT_ESCALATED'
    );
END;
$$;

-- ------------------------------------------------------------
-- 18. RESOLUTION PROCEDURE
-- ------------------------------------------------------------

CREATE PROCEDURE resolve_incident(
    IN p_incident_id BIGINT,
    IN p_actor_id VARCHAR,
    IN p_resolution_notes TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    selected_severity severity_level;
    selected_reporter VARCHAR(80);
BEGIN
    SELECT severity, reporter_id
    INTO selected_severity, selected_reporter
    FROM incidents
    WHERE incident_id = p_incident_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incident not found.';
    END IF;

    IF NOT actor_can_manage(p_actor_id, selected_severity) THEN
        RAISE EXCEPTION 'Unauthorized resolution.';
    END IF;

    IF LENGTH(TRIM(p_resolution_notes)) = 0 THEN
        RAISE EXCEPTION 'Resolution evidence is required.';
    END IF;

    PERFORM set_config('app.actor_id', p_actor_id, TRUE);

    UPDATE incidents
    SET status = 'RESOLVED',
        resolved_at = NOW(),
        resolution_notes = p_resolution_notes
    WHERE incident_id = p_incident_id;

    PERFORM queue_incident_notification(
        p_incident_id,
        selected_reporter,
        'INCIDENT_RESOLVED'
    );
END;
$$;

-- ------------------------------------------------------------
-- 19. CLOSURE PROCEDURE
-- ------------------------------------------------------------

CREATE PROCEDURE close_incident(
    IN p_incident_id BIGINT,
    IN p_actor_id VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_incident incidents%ROWTYPE;
BEGIN
    SELECT *
    INTO current_incident
    FROM incidents
    WHERE incident_id = p_incident_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incident not found.';
    END IF;

    IF NOT actor_can_manage(p_actor_id, current_incident.severity) THEN
        RAISE EXCEPTION 'Unauthorized closure.';
    END IF;

    IF current_incident.status <> 'RESOLVED'
       OR current_incident.resolution_notes IS NULL THEN
        RAISE EXCEPTION
            'Incident must be resolved with evidence before closure.';
    END IF;

    PERFORM set_config('app.actor_id', p_actor_id, TRUE);

    UPDATE incidents
    SET status = 'CLOSED',
        closed_at = NOW()
    WHERE incident_id = p_incident_id;
END;
$$;

-- ------------------------------------------------------------
-- 20. REOPEN PROCEDURE
-- ------------------------------------------------------------

CREATE PROCEDURE reopen_incident(
    IN p_incident_id BIGINT,
    IN p_actor_id VARCHAR,
    IN p_reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    selected_severity severity_level;
BEGIN
    SELECT severity
    INTO selected_severity
    FROM incidents
    WHERE incident_id = p_incident_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incident not found.';
    END IF;

    IF NOT actor_can_manage(p_actor_id, selected_severity) THEN
        RAISE EXCEPTION 'Unauthorized reopening.';
    END IF;

    IF LENGTH(TRIM(p_reason)) = 0 THEN
        RAISE EXCEPTION 'Reopening reason is required.';
    END IF;

    PERFORM set_config('app.actor_id', p_actor_id, TRUE);

    UPDATE incidents
    SET status = 'INVESTIGATING',
        resolved_at = NULL,
        closed_at = NULL,
        resolution_notes = NULL
    WHERE incident_id = p_incident_id;

    INSERT INTO incident_audit (
        incident_id,
        actor_id,
        action,
        previous_value,
        new_value,
        details
    )
    VALUES (
        p_incident_id,
        p_actor_id,
        'INCIDENT_REOPENED',
        'RESOLVED_OR_CLOSED',
        'INVESTIGATING',
        p_reason
    );
END;
$$;

-- ------------------------------------------------------------
-- 21. MERGE/COMPLETION ELIGIBILITY EVALUATION
-- ------------------------------------------------------------

CREATE VIEW incident_eligibility AS
SELECT
    i.incident_id,
    i.incident_reference,
    i.severity,
    i.status,

    ar.required_approvals,

    i.assigned_to IS NOT NULL AS has_owner,

    i.resolution_notes IS NOT NULL
        AND LENGTH(TRIM(i.resolution_notes)) > 0
        AS has_resolution_evidence,

    COALESCE(checks.all_checks_passed, TRUE)
        AS all_required_checks_passed,

    COALESCE(approvals.approval_count, 0)
        AS approval_count,

    (
        i.status = 'RESOLVED'
        AND (
            NOT ar.require_owner
            OR i.assigned_to IS NOT NULL
        )
        AND (
            NOT ar.require_resolution_evidence
            OR i.resolution_notes IS NOT NULL
        )
        AND (
            NOT ar.require_status_checks
            OR COALESCE(checks.all_checks_passed, TRUE)
        )
        AND COALESCE(approvals.approval_count, 0)
            >= ar.required_approvals
    ) AS eligible

FROM incidents i

JOIN incident_approval_requirements ar
    ON ar.severity = i.severity

LEFT JOIN LATERAL (
    SELECT BOOL_AND(completed AND passed) AS all_checks_passed
    FROM incident_status_checks
    WHERE incident_id = i.incident_id
      AND required = TRUE
) checks ON TRUE

LEFT JOIN LATERAL (
    SELECT COUNT(*) AS approval_count
    FROM incident_approvals
    WHERE incident_id = i.incident_id
      AND approved = TRUE
) approvals ON TRUE;

-- ------------------------------------------------------------
-- 22. DEADLINE MONITORING VIEW
-- ------------------------------------------------------------

CREATE VIEW incident_deadline_monitor AS
SELECT
    incident_id,
    incident_reference,
    title,
    severity,
    status,
    acknowledgement_deadline,
    resolution_deadline,

    CASE
        WHEN status IN ('RESOLVED', 'CLOSED')
            THEN 'COMPLETED'
        WHEN acknowledged_at IS NULL
             AND NOW() > acknowledgement_deadline
            THEN 'ACKNOWLEDGEMENT_OVERDUE'
        WHEN NOW() > resolution_deadline
            THEN 'RESOLUTION_OVERDUE'
        ELSE 'WITHIN_DEADLINE'
    END AS deadline_state

FROM incidents;

-- ------------------------------------------------------------
-- 23. MANAGEMENT DASHBOARD
-- ------------------------------------------------------------

CREATE VIEW escalation_dashboard AS
SELECT
    COUNT(*) AS total_incidents,

    COUNT(*) FILTER (
        WHERE status NOT IN ('RESOLVED', 'CLOSED')
    ) AS open_incidents,

    COUNT(*) FILTER (
        WHERE severity = 'CRITICAL'
    ) AS critical_incidents,

    COUNT(*) FILTER (
        WHERE status = 'ESCALATED'
    ) AS escalated_incidents,

    COUNT(*) FILTER (
        WHERE status IN ('RESOLVED', 'CLOSED')
    ) AS completed_incidents,

    COUNT(*) FILTER (
        WHERE NOW() > resolution_deadline
          AND status NOT IN ('RESOLVED', 'CLOSED')
    ) AS overdue_incidents

FROM incidents;

-- ------------------------------------------------------------
-- 24. SAMPLE DEPARTMENTS AND ACTORS
-- ------------------------------------------------------------

INSERT INTO departments(department_name)
VALUES
    ('Operations'),
    ('Technology'),
    ('Executive'),
    ('Security');

INSERT INTO actors(
    actor_id,
    full_name,
    email,
    role,
    department_id
)
VALUES
(
    'U001',
    'Operations Reporter',
    'reporter@example.org',
    'REPORTER',
    (SELECT department_id FROM departments
     WHERE department_name = 'Operations')
),
(
    'U002',
    'Technical Responder',
    'responder@example.org',
    'RESPONDER',
    (SELECT department_id FROM departments
     WHERE department_name = 'Technology')
),
(
    'U003',
    'Incident Manager',
    'manager@example.org',
    'INCIDENT_MANAGER',
    (SELECT department_id FROM departments
     WHERE department_name = 'Operations')
),
(
    'U004',
    'Executive Director',
    'executive@example.org',
    'ADMINISTRATOR',
    (SELECT department_id FROM departments
     WHERE department_name = 'Executive')
),
(
    'U005',
    'Security Team Lead',
    'securitylead@example.org',
    'TEAM_LEAD',
    (SELECT department_id FROM departments
     WHERE department_name = 'Security')
);

-- ------------------------------------------------------------
-- 25. SAMPLE INCIDENTS
-- ------------------------------------------------------------

CALL report_incident(
    'U001',
    'Production database outage',
    'Primary database is unavailable and transactions are failing.',
    'Infrastructure',
    'CRITICAL',
    (SELECT department_id FROM departments
     WHERE department_name = 'Technology'),
    'INC-2026-001'
);

CALL report_incident(
    'U001',
    'Delayed daily reporting pipeline',
    'The daily operational report has not been generated.',
    'Reporting',
    'MEDIUM',
    (SELECT department_id FROM departments
     WHERE department_name = 'Operations'),
    'INC-2026-002'
);

CALL report_incident(
    'U001',
    'Unauthorized network access attempt',
    'Multiple suspicious authentication attempts were detected.',
    'Security',
    'HIGH',
    (SELECT department_id FROM departments
     WHERE department_name = 'Security'),
    'INC-2026-003'
);

-- ------------------------------------------------------------
-- 26. SAMPLE WORKFLOW EXECUTION
-- ------------------------------------------------------------

-- Critical incident assignment.
CALL assign_incident(
    (SELECT incident_id FROM incidents
     WHERE incident_reference = 'INC-2026-001'),
    'U003',
    'U002'
);

-- Critical incident acknowledgement.
CALL acknowledge_incident(
    (SELECT incident_id FROM incidents
     WHERE incident_reference = 'INC-2026-001'),
    'U003'
);

-- Critical incident escalation.
CALL escalate_incident(
    (SELECT incident_id FROM incidents
     WHERE incident_reference = 'INC-2026-001'),
    'U003',
    'EXECUTIVE',
    'Production service interruption affects customers.'
);

-- Operational incident assignment.
CALL assign_incident(
    (SELECT incident_id FROM incidents
     WHERE incident_reference = 'INC-2026-002'),
    'U003',
    'U002'
);

-- ------------------------------------------------------------
-- 27. SAMPLE STATUS CHECKS
-- ------------------------------------------------------------

INSERT INTO incident_status_checks (
    incident_id,
    check_name,
    required,
    completed,
    passed,
    checked_by,
    checked_at
)
SELECT
    incident_id,
    'Database connectivity',
    TRUE,
    TRUE,
    TRUE,
    'U003',
    NOW()
FROM incidents
WHERE incident_reference = 'INC-2026-001';

INSERT INTO incident_status_checks (
    incident_id,
    check_name,
    required,
    completed,
    passed,
    checked_by,
    checked_at
)
SELECT
    incident_id,
    'Transaction integrity',
    TRUE,
    TRUE,
    TRUE,
    'U003',
    NOW()
FROM incidents
WHERE incident_reference = 'INC-2026-001';

-- ------------------------------------------------------------
-- 28. SAMPLE RESOLUTION
-- ------------------------------------------------------------

CALL resolve_incident(
    (SELECT incident_id FROM incidents
     WHERE incident_reference = 'INC-2026-001'),
    'U003',
    'Database restored. Connectivity and transaction validation passed.'
);

-- ------------------------------------------------------------
-- 29. SAMPLE APPROVALS
-- ------------------------------------------------------------

INSERT INTO incident_approvals (
    incident_id,
    reviewer_id,
    approved,
    decision_notes
)
SELECT
    incident_id,
    'U003',
    TRUE,
    'Operational resolution evidence reviewed.'
FROM incidents
WHERE incident_reference = 'INC-2026-001';

INSERT INTO incident_approvals (
    incident_id,
    reviewer_id,
    approved,
    decision_notes
)
SELECT
    incident_id,
    'U004',
    TRUE,
    'Executive review completed.'
FROM incidents
WHERE incident_reference = 'INC-2026-001';

-- ------------------------------------------------------------
-- 30. SAMPLE CLOSURE
-- ------------------------------------------------------------

CALL close_incident(
    (SELECT incident_id FROM incidents
     WHERE incident_reference = 'INC-2026-001'),
    'U003'
);

COMMIT;

-- ============================================================
-- 31. OPERATIONAL RETRIEVAL QUERIES
-- ============================================================

-- Complete incident register.
SELECT
    i.incident_reference,
    i.title,
    i.severity,
    i.status,
    reporter.full_name AS reported_by,
    assignee.full_name AS assigned_to,
    d.department_name,
    i.reported_at
FROM incidents i
JOIN actors reporter
    ON reporter.actor_id = i.reporter_id
LEFT JOIN actors assignee
    ON assignee.actor_id = i.assigned_to
JOIN departments d
    ON d.department_id = i.department_id
ORDER BY i.reported_at DESC;

-- All unresolved critical incidents.
SELECT
    incident_reference,
    title,
    status,
    escalation_level,
    resolution_deadline
FROM incidents
WHERE severity = 'CRITICAL'
  AND status NOT IN ('RESOLVED', 'CLOSED');

-- ============================================================
-- 32. DEADLINE VALIDATION
-- ============================================================

SELECT *
FROM incident_deadline_monitor
ORDER BY resolution_deadline;

-- ============================================================
-- 33. AGGREGATION AND MANAGEMENT REPORTING
-- ============================================================

SELECT *
FROM escalation_dashboard;

SELECT
    severity,
    status,
    COUNT(*) AS incident_count
FROM incidents
GROUP BY GROUPING SETS (
    (severity, status),
    (severity),
    ()
)
ORDER BY severity NULLS LAST, status NULLS LAST;

-- Department-level performance.
SELECT
    d.department_name,
    COUNT(i.incident_id) AS total_incidents,
    COUNT(i.incident_id) FILTER (
        WHERE i.status = 'RESOLVED'
           OR i.status = 'CLOSED'
    ) AS completed_incidents,
    COUNT(i.incident_id) FILTER (
        WHERE i.status = 'ESCALATED'
    ) AS escalated_incidents
FROM departments d
LEFT JOIN incidents i
    ON i.department_id = d.department_id
GROUP BY d.department_id, d.department_name
ORDER BY total_incidents DESC;

-- ============================================================
-- 34. ESCALATION HISTORY REPORT
-- ============================================================

SELECT
    i.incident_reference,
    h.previous_level,
    h.new_level,
    a.full_name AS escalated_by,
    h.reason,
    h.escalated_at
FROM escalation_history h
JOIN incidents i
    ON i.incident_id = h.incident_id
JOIN actors a
    ON a.actor_id = h.escalated_by
ORDER BY h.escalated_at DESC;

-- ============================================================
-- 35. AUDIT REPORT
-- ============================================================

SELECT
    i.incident_reference,
    a.full_name,
    h.action,
    h.previous_value,
    h.new_value,
    h.details,
    h.created_at
FROM incident_audit h
JOIN incidents i
    ON i.incident_id = h.incident_id
LEFT JOIN actors a
    ON a.actor_id = h.actor_id
ORDER BY h.created_at DESC;

-- ============================================================
-- 36. NOTIFICATION PROCESSING
-- ============================================================

-- Claim pending notifications safely across workers.
BEGIN;

WITH selected AS (
    SELECT notification_id
    FROM notifications
    WHERE delivery_status IN ('PENDING', 'RETRY')
      AND attempt_count < 5
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 20
)
UPDATE notifications n
SET delivery_status = 'RETRY',
    attempt_count = attempt_count + 1
FROM selected
WHERE n.notification_id = selected.notification_id
RETURNING n.*;

COMMIT;

-- A transport worker should mark actual delivery only after
-- the external messaging service confirms successful delivery.

-- ============================================================
-- 37. APPROVAL AND ELIGIBILITY REPORT
-- ============================================================

SELECT
    incident_reference,
    severity,
    status,
    required_approvals,
    approval_count,
    has_owner,
    has_resolution_evidence,
    all_required_checks_passed,
    eligible
FROM incident_eligibility
ORDER BY incident_id;

-- ============================================================
-- 38. FAILURE DETECTION
-- ============================================================

-- Incidents missing an assigned owner.
SELECT
    incident_reference,
    title,
    severity
FROM incidents
WHERE assigned_to IS NULL
  AND status NOT IN ('RESOLVED', 'CLOSED');

-- Failed or incomplete required checks.
SELECT
    i.incident_reference,
    c.check_name,
    c.completed,
    c.passed
FROM incident_status_checks c
JOIN incidents i
    ON i.incident_id = c.incident_id
WHERE c.required = TRUE
  AND (c.completed = FALSE OR c.passed = FALSE);

-- Failed notifications.
SELECT
    incident_id,
    recipient,
    event_type,
    attempt_count,
    last_error
FROM notifications
WHERE delivery_status = 'FAILED';

-- ============================================================
-- 39. CTE-BASED INCIDENT PRIORITY REPORT
-- ============================================================

WITH incident_metrics AS (
    SELECT
        incident_id,
        incident_reference,
        title,
        severity,
        status,
        reported_at,
        resolution_deadline,

        CASE severity
            WHEN 'CRITICAL' THEN 100
            WHEN 'HIGH' THEN 75
            WHEN 'MEDIUM' THEN 50
            WHEN 'LOW' THEN 25
        END AS severity_score,

        CASE
            WHEN status = 'ESCALATED' THEN 30
            WHEN status = 'INVESTIGATING' THEN 15
            ELSE 0
        END AS workflow_score,

        CASE
            WHEN NOW() > resolution_deadline THEN 40
            ELSE 0
        END AS overdue_score

    FROM incidents
    WHERE status NOT IN ('RESOLVED', 'CLOSED')
)
SELECT
    incident_reference,
    title,
    severity,
    status,
    severity_score + workflow_score + overdue_score
        AS priority_score
FROM incident_metrics
ORDER BY priority_score DESC, reported_at ASC;

-- ============================================================
-- 40. OPERATIONAL SECURITY NOTES
-- ============================================================

-- Production deployments should:
-- 1. Use a dedicated application database role.
-- 2. Revoke direct incident-table UPDATE permissions.
-- 3. Grant EXECUTE on approved workflow procedures.
-- 4. Set app.actor_id from a trusted authenticated application.
-- 5. Enforce row-level security where department isolation applies.
-- 6. Protect audit and notification records against unauthorized changes.
-- 7. Use a durable external notification worker.
-- 8. Avoid storing passwords, tokens or sensitive credentials here.
-- 9. Use TLS and encrypted database backups.
-- 10. Restrict access to incident descriptions and audit records.
