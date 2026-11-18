-- ============================================================
-- COMMUNICATION CHALLENGES
-- Common Communication Problems Management Database
--
-- PostgreSQL 14+
--
-- Models:
--   Communication incidents
--   Departments and employees
--   Communication channels
--   Incident assignments
--   Corrective actions
--   Feedback and acknowledgement
--   Response deadlines
--   Workflow transitions
--   Status checks
--   Closure eligibility
--   Analytics and reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS communication_management;

SET search_path TO communication_management, public;

-- ============================================================
-- 1. ENUMERATED DOMAIN TYPES
-- ============================================================

CREATE TYPE communication_category AS ENUM (
    'unclear_message',
    'information_overload',
    'poor_listening',
    'language_barrier',
    'cultural_difference',
    'wrong_channel',
    'delayed_response',
    'missing_feedback',
    'incorrect_assumption',
    'technical_failure',
    'interpersonal_conflict',
    'role_ambiguity'
);

CREATE TYPE incident_severity AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE communication_channel AS ENUM (
    'email',
    'meeting',
    'chat',
    'phone',
    'document',
    'video_conference',
    'face_to_face'
);

CREATE TYPE incident_status AS ENUM (
    'open',
    'investigating',
    'action_required',
    'resolved',
    'closed'
);

CREATE TYPE feedback_decision AS ENUM (
    'pending',
    'accepted',
    'rejected'
);

CREATE TYPE check_status AS ENUM (
    'pending',
    'passed',
    'failed'
);

-- ============================================================
-- 2. ORGANIZATIONAL STRUCTURE
-- ============================================================

CREATE TABLE departments (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_name VARCHAR(120) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    department_id BIGINT NOT NULL REFERENCES departments(department_id),
    job_title VARCHAR(120) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_employee_email
        CHECK (email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$')
);

-- ============================================================
-- 3. COMMUNICATION POLICY
-- ============================================================

CREATE TABLE communication_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(120) NOT NULL UNIQUE,
    low_response_hours INTEGER NOT NULL DEFAULT 72,
    medium_response_hours INTEGER NOT NULL DEFAULT 48,
    high_response_hours INTEGER NOT NULL DEFAULT 12,
    critical_response_hours INTEGER NOT NULL DEFAULT 2,
    require_corrective_action BOOLEAN NOT NULL DEFAULT TRUE,
    require_feedback BOOLEAN NOT NULL DEFAULT TRUE,
    require_successful_checks BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT positive_response_limits CHECK (
        low_response_hours > 0
        AND medium_response_hours > 0
        AND high_response_hours > 0
        AND critical_response_hours > 0
    )
);

CREATE TABLE category_recommendations (
    category communication_category PRIMARY KEY,
    recommended_action TEXT NOT NULL,
    prevention_measure TEXT NOT NULL
);

-- ============================================================
-- 4. COMMUNICATION INCIDENTS
-- ============================================================

CREATE TABLE communication_incidents (
    incident_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    reference_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    title VARCHAR(120) NOT NULL,
    category communication_category NOT NULL,
    severity incident_severity NOT NULL,
    channel communication_channel NOT NULL,

    department_id BIGINT NOT NULL
        REFERENCES departments(department_id),

    reporter_id BIGINT NOT NULL
        REFERENCES employees(employee_id),

    assignee_id BIGINT
        REFERENCES employees(employee_id),

    policy_id BIGINT NOT NULL
        REFERENCES communication_policies(policy_id),

    description TEXT NOT NULL,

    status incident_status NOT NULL DEFAULT 'open',

    corrective_action TEXT,
    resolution TEXT,

    feedback feedback_decision NOT NULL DEFAULT 'pending',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,

    CONSTRAINT valid_incident_title
        CHECK (length(trim(title)) BETWEEN 1 AND 120),

    CONSTRAINT valid_incident_description
        CHECK (length(trim(description)) BETWEEN 1 AND 5000),

    CONSTRAINT valid_resolution_timestamp
        CHECK (
            resolved_at IS NULL
            OR resolved_at >= created_at
        ),

    CONSTRAINT valid_closure_timestamp
        CHECK (
            closed_at IS NULL
            OR (
                resolved_at IS NOT NULL
                AND closed_at >= resolved_at
            )
        )
);

-- ============================================================
-- 5. INCIDENT EVENT HISTORY
-- ============================================================

CREATE TABLE incident_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    incident_id BIGINT NOT NULL
        REFERENCES communication_incidents(incident_id),

    event_type VARCHAR(60) NOT NULL,
    event_description TEXT NOT NULL,

    performed_by BIGINT
        REFERENCES employees(employee_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_event_description
        CHECK (length(trim(event_description)) > 0)
);

-- ============================================================
-- 6. STATUS CHECKS
-- ============================================================

CREATE TABLE incident_status_checks (
    check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    incident_id BIGINT NOT NULL
        REFERENCES communication_incidents(incident_id),

    check_name VARCHAR(120) NOT NULL,
    check_status check_status NOT NULL DEFAULT 'pending',
    details TEXT,

    checked_by BIGINT
        REFERENCES employees(employee_id),

    checked_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_incident_check
        UNIQUE (incident_id, check_name),

    CONSTRAINT valid_check_timestamp
        CHECK (
            (check_status = 'pending' AND checked_at IS NULL)
            OR
            (check_status <> 'pending' AND checked_at IS NOT NULL)
        )
);

-- ============================================================
-- 7. COMMUNICATION RESPONSE AND CORRECTIVE ACTION
-- ============================================================

CREATE TABLE corrective_actions (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    incident_id BIGINT NOT NULL
        REFERENCES communication_incidents(incident_id),

    action_description TEXT NOT NULL,

    owner_id BIGINT NOT NULL
        REFERENCES employees(employee_id),

    due_at TIMESTAMPTZ NOT NULL,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_action_description
        CHECK (length(trim(action_description)) > 0),

    CONSTRAINT valid_completion_time
        CHECK (
            completed_at IS NULL
            OR completed_at >= created_at
        )
);

-- ============================================================
-- 8. INDEXES
-- ============================================================

CREATE INDEX idx_incidents_status_severity
    ON communication_incidents(status, severity);

CREATE INDEX idx_incidents_department_created
    ON communication_incidents(department_id, created_at DESC);

CREATE INDEX idx_incidents_category
    ON communication_incidents(category);

CREATE INDEX idx_incidents_assignee
    ON communication_incidents(assignee_id)
    WHERE assignee_id IS NOT NULL;

CREATE INDEX idx_incidents_open_deadlines
    ON communication_incidents(created_at, severity)
    WHERE status IN ('open', 'investigating', 'action_required');

CREATE INDEX idx_events_incident_timestamp
    ON incident_events(incident_id, created_at DESC);

CREATE INDEX idx_status_checks_incident
    ON incident_status_checks(incident_id, check_status);

CREATE INDEX idx_actions_due
    ON corrective_actions(due_at)
    WHERE completed_at IS NULL;

-- ============================================================
-- 9. AUTOMATIC UPDATED_AT MANAGEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_incident_updated_at
BEFORE UPDATE ON communication_incidents
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();

-- ============================================================
-- 10. INCIDENT EVENT AUDIT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION record_incident_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO incident_events (
            incident_id,
            event_type,
            event_description,
            performed_by
        )
        VALUES (
            NEW.incident_id,
            'reported',
            'Communication incident registered.',
            NEW.reporter_id
        );

    ELSIF OLD.status IS DISTINCT FROM NEW.status THEN

        INSERT INTO incident_events (
            incident_id,
            event_type,
            event_description,
            performed_by
        )
        VALUES (
            NEW.incident_id,
            'status_changed',
            'Status changed from '
                || OLD.status::TEXT
                || ' to '
                || NEW.status::TEXT,
            NEW.assignee_id
        );

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_incident_event_audit
AFTER INSERT OR UPDATE ON communication_incidents
FOR EACH ROW
EXECUTE FUNCTION record_incident_event();

-- ============================================================
-- 11. RESPONSE DEADLINE FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_response_deadline(
    p_incident_id BIGINT
)
RETURNS TIMESTAMPTZ
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_incident communication_incidents%ROWTYPE;
    v_hours INTEGER;
BEGIN
    SELECT *
    INTO v_incident
    FROM communication_incidents
    WHERE incident_id = p_incident_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incident % does not exist', p_incident_id;
    END IF;

    SELECT CASE v_incident.severity
        WHEN 'low' THEN low_response_hours
        WHEN 'medium' THEN medium_response_hours
        WHEN 'high' THEN high_response_hours
        WHEN 'critical' THEN critical_response_hours
    END
    INTO v_hours
    FROM communication_policies
    WHERE policy_id = v_incident.policy_id;

    RETURN v_incident.created_at
        + make_interval(hours => v_hours);
END;
$$;

-- ============================================================
-- 12. CLOSURE ELIGIBILITY FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_closure_eligibility(
    p_incident_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    failure_reason TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_incident communication_incidents%ROWTYPE;
    v_policy communication_policies%ROWTYPE;
    v_failed_check BOOLEAN;
BEGIN
    SELECT *
    INTO v_incident
    FROM communication_incidents
    WHERE incident_id = p_incident_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incident % does not exist', p_incident_id;
    END IF;

    SELECT *
    INTO v_policy
    FROM communication_policies
    WHERE policy_id = v_incident.policy_id;

    IF v_incident.status <> 'resolved' THEN
        RETURN QUERY
        SELECT FALSE, 'Incident must be resolved before closure.';
    END IF;

    IF v_policy.require_corrective_action
       AND v_incident.corrective_action IS NULL THEN

        RETURN QUERY
        SELECT FALSE, 'Corrective action is missing.';
    END IF;

    IF v_incident.resolution IS NULL THEN
        RETURN QUERY
        SELECT FALSE, 'Resolution documentation is missing.';
    END IF;

    IF v_policy.require_feedback
       AND v_incident.feedback <> 'accepted' THEN

        RETURN QUERY
        SELECT FALSE, 'Accepted feedback is required.';
    END IF;

    IF v_policy.require_successful_checks THEN

        SELECT EXISTS (
            SELECT 1
            FROM incident_status_checks
            WHERE incident_id = p_incident_id
              AND check_status <> 'passed'
        )
        INTO v_failed_check;

        IF v_failed_check THEN
            RETURN QUERY
            SELECT FALSE, 'One or more status checks have not passed.';
        END IF;

    END IF;

    IF NOT FOUND THEN
        NULL;
    END IF;

    RETURN QUERY
    SELECT TRUE, 'All closure requirements satisfied.';
END;
$$;

-- ============================================================
-- 13. CONTROLLED STATUS TRANSITION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE transition_incident(
    p_incident_id BIGINT,
    p_new_status incident_status
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current incident_status;
    v_allowed BOOLEAN := FALSE;
BEGIN
    SELECT status
    INTO v_current
    FROM communication_incidents
    WHERE incident_id = p_incident_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incident % does not exist', p_incident_id;
    END IF;

    v_allowed := CASE v_current
        WHEN 'open' THEN
            p_new_status IN ('investigating', 'closed')

        WHEN 'investigating' THEN
            p_new_status IN (
                'action_required',
                'resolved',
                'closed'
            )

        WHEN 'action_required' THEN
            p_new_status IN (
                'investigating',
                'resolved'
            )

        WHEN 'resolved' THEN
            p_new_status IN (
                'closed',
                'investigating'
            )

        WHEN 'closed' THEN FALSE
    END;

    IF NOT COALESCE(v_allowed, FALSE) THEN
        RAISE EXCEPTION
            'Invalid transition from % to %',
            v_current,
            p_new_status;
    END IF;

    IF p_new_status = 'resolved' THEN

        IF NOT EXISTS (
            SELECT 1
            FROM communication_incidents
            WHERE incident_id = p_incident_id
              AND corrective_action IS NOT NULL
              AND resolution IS NOT NULL
        ) THEN
            RAISE EXCEPTION
                'Corrective action and resolution are required.';
        END IF;

    END IF;

    IF p_new_status = 'closed' THEN

        IF NOT EXISTS (
            SELECT 1
            FROM evaluate_closure_eligibility(p_incident_id)
            WHERE eligible = TRUE
        ) THEN
            RAISE EXCEPTION
                'Incident does not satisfy closure requirements.';
        END IF;

    END IF;

    UPDATE communication_incidents
    SET
        status = p_new_status,

        resolved_at = CASE
            WHEN p_new_status = 'resolved'
                THEN CURRENT_TIMESTAMP
            WHEN p_new_status = 'investigating'
                THEN NULL
            ELSE resolved_at
        END,

        closed_at = CASE
            WHEN p_new_status = 'closed'
                THEN CURRENT_TIMESTAMP
            ELSE closed_at
        END

    WHERE incident_id = p_incident_id;
END;
$$;

-- ============================================================
-- 14. CATEGORY RECOMMENDATIONS
-- ============================================================

INSERT INTO category_recommendations (
    category,
    recommended_action,
    prevention_measure
)
VALUES
(
    'unclear_message',
    'Use explicit instructions and written confirmation.',
    'Standardize project briefs and communication templates.'
),
(
    'information_overload',
    'Prioritize essential information and structure messages.',
    'Use summaries and organized information delivery.'
),
(
    'poor_listening',
    'Use active listening and paraphrasing.',
    'Introduce structured discussion practices.'
),
(
    'language_barrier',
    'Use plain language and verified translations.',
    'Provide appropriate language support.'
),
(
    'cultural_difference',
    'Adopt inclusive communication practices.',
    'Establish cross-cultural awareness practices.'
),
(
    'wrong_channel',
    'Select a channel based on urgency and confidentiality.',
    'Define communication channel selection rules.'
),
(
    'delayed_response',
    'Establish response deadlines and escalation.',
    'Introduce ownership and response monitoring.'
),
(
    'missing_feedback',
    'Establish regular feedback and acknowledgement.',
    'Introduce confirmation checkpoints.'
),
(
    'incorrect_assumption',
    'Verify facts and confirm shared understanding.',
    'Require clarification of ambiguous instructions.'
),
(
    'technical_failure',
    'Establish backup channels and technical recovery.',
    'Monitor communication infrastructure.'
),
(
    'interpersonal_conflict',
    'Use impartial mediation and structured discussion.',
    'Introduce constructive conflict-resolution procedures.'
),
(
    'role_ambiguity',
    'Define responsibilities and reporting relationships.',
    'Maintain clear responsibility assignments.'
);

-- ============================================================
-- 15. SAMPLE ORGANIZATIONAL DATA
-- ============================================================

INSERT INTO departments (
    department_name,
    description
)
VALUES
(
    'Engineering',
    'Software development and technical operations.'
),
(
    'Customer Support',
    'Customer communication and service delivery.'
),
(
    'Operations',
    'Operational coordination and execution.'
),
(
    'Human Resources',
    'Employee relations and organizational communication.'
);

INSERT INTO employees (
    employee_name,
    email,
    department_id,
    job_title
)
VALUES
(
    'Aarav Sharma',
    'aarav@example.com',
    1,
    'Project Manager'
),
(
    'Priya Verma',
    'priya@example.com',
    1,
    'Communication Coordinator'
),
(
    'Rahul Singh',
    'rahul@example.com',
    2,
    'Support Manager'
),
(
    'Neha Gupta',
    'neha@example.com',
    2,
    'Support Team Lead'
),
(
    'Ananya Rao',
    'ananya@example.com',
    3,
    'Operations Manager'
),
(
    'Vikram Das',
    'vikram@example.com',
    4,
    'HR Manager'
);

INSERT INTO communication_policies (
    policy_name,
    low_response_hours,
    medium_response_hours,
    high_response_hours,
    critical_response_hours,
    require_corrective_action,
    require_feedback,
    require_successful_checks
)
VALUES
(
    'Standard Organizational Policy',
    72,
    48,
    12,
    2,
    TRUE,
    TRUE,
    TRUE
);

-- ============================================================
-- 16. SAMPLE COMMUNICATION INCIDENTS
-- ============================================================

INSERT INTO communication_incidents (
    title,
    category,
    severity,
    channel,
    department_id,
    reporter_id,
    assignee_id,
    policy_id,
    description,
    status,
    corrective_action,
    resolution,
    feedback,
    resolved_at,
    closed_at
)
VALUES
(
    'Unclear project instructions',
    'unclear_message',
    'high',
    'email',
    1,
    1,
    2,
    1,
    'Development teams interpreted project requirements differently.',
    'closed',
    'Publish a structured project brief.',
    'Responsibilities and deadlines were clarified.',
    'accepted',
    CURRENT_TIMESTAMP - INTERVAL '2 hours',
    CURRENT_TIMESTAMP - INTERVAL '1 hour'
),
(
    'Delayed customer response',
    'delayed_response',
    'medium',
    'email',
    2,
    3,
    4,
    1,
    'Customer inquiry remained unanswered beyond the expected period.',
    'action_required',
    'Introduce response ownership and escalation.',
    NULL,
    'pending',
    NULL,
    NULL
),
(
    'Information overload during meetings',
    'information_overload',
    'low',
    'meeting',
    3,
    5,
    NULL,
    1,
    'Meeting participants received excessive unstructured information.',
    'open',
    NULL,
    NULL,
    'pending',
    NULL,
    NULL
),
(
    'Language barrier in instructions',
    'language_barrier',
    'high',
    'video_conference',
    3,
    5,
    6,
    1,
    'Technical instructions were misunderstood due to language differences.',
    'investigating',
    NULL,
    NULL,
    'pending',
    NULL,
    NULL
),
(
    'Missing feedback on internal policy',
    'missing_feedback',
    'medium',
    'document',
    4,
    6,
    NULL,
    1,
    'Employees did not acknowledge the revised policy communication.',
    'open',
    NULL,
    NULL,
    'pending',
    NULL,
    NULL
),
(
    'Incorrect assumptions in project coordination',
    'incorrect_assumption',
    'low',
    'chat',
    1,
    1,
    NULL,
    1,
    'Tasks were assigned based on unverified assumptions.',
    'open',
    NULL,
    NULL,
    'pending',
    NULL,
    NULL
);

-- ============================================================
-- 17. STATUS CHECK EXAMPLES
-- ============================================================

INSERT INTO incident_status_checks (
    incident_id,
    check_name,
    check_status,
    details,
    checked_by,
    checked_at
)
VALUES
(
    1,
    'Revised instructions distributed',
    'passed',
    'The revised document was shared with all project teams.',
    2,
    CURRENT_TIMESTAMP - INTERVAL '3 hours'
),
(
    1,
    'Stakeholder acknowledgement',
    'passed',
    'Relevant stakeholders confirmed receipt.',
    2,
    CURRENT_TIMESTAMP - INTERVAL '2 hours'
),
(
    2,
    'Escalation ownership configured',
    'passed',
    'A responsible support lead has been assigned.',
    4,
    CURRENT_TIMESTAMP
);

-- ============================================================
-- 18. CORRECTIVE ACTION EXAMPLES
-- ============================================================

INSERT INTO corrective_actions (
    incident_id,
    action_description,
    owner_id,
    due_at,
    completed_at
)
VALUES
(
    1,
    'Standardize project instructions.',
    2,
    CURRENT_TIMESTAMP - INTERVAL '3 hours',
    CURRENT_TIMESTAMP - INTERVAL '2 hours'
),
(
    2,
    'Configure support response escalation.',
    4,
    CURRENT_TIMESTAMP + INTERVAL '24 hours',
    NULL
);

-- ============================================================
-- 19. REPORTING VIEWS
-- ============================================================

CREATE OR REPLACE VIEW incident_detail_report AS
SELECT
    i.incident_id,
    i.reference_id,
    i.title,
    i.category,
    i.severity,
    i.channel,
    d.department_name,
    reporter.employee_name AS reporter,
    assignee.employee_name AS assignee,
    i.status,
    i.created_at,
    i.updated_at,
    i.resolved_at,
    i.closed_at,
    i.feedback,
    i.corrective_action,
    i.resolution
FROM communication_incidents i
JOIN departments d
    ON d.department_id = i.department_id
JOIN employees reporter
    ON reporter.employee_id = i.reporter_id
LEFT JOIN employees assignee
    ON assignee.employee_id = i.assignee_id;

CREATE OR REPLACE VIEW communication_category_report AS
SELECT
    category,
    COUNT(*) AS incident_count,
    COUNT(*) FILTER (
        WHERE status IN ('resolved', 'closed')
    ) AS resolved_count,
    COUNT(*) FILTER (
        WHERE severity IN ('high', 'critical')
    ) AS high_priority_count
FROM communication_incidents
GROUP BY category;

CREATE OR REPLACE VIEW overdue_communication_incidents AS
SELECT
    i.incident_id,
    i.title,
    i.category,
    i.severity,
    i.status,
    i.created_at,
    calculate_response_deadline(i.incident_id) AS deadline
FROM communication_incidents i
WHERE i.status IN (
    'open',
    'investigating',
    'action_required'
)
AND CURRENT_TIMESTAMP >
    calculate_response_deadline(i.incident_id);

-- ============================================================
-- 20. VALIDATION AND RETRIEVAL QUERIES
-- ============================================================

-- Retrieve all incidents with organizational ownership.

SELECT *
FROM incident_detail_report
ORDER BY created_at DESC;

-- Find unresolved high-priority communication problems.

SELECT *
FROM incident_detail_report
WHERE severity IN ('high', 'critical')
  AND status NOT IN ('resolved', 'closed');

-- Find incidents requiring action.

SELECT
    incident_id,
    title,
    category,
    severity,
    status
FROM communication_incidents
WHERE status = 'action_required';

-- Retrieve corrective recommendations.

SELECT
    i.incident_id,
    i.title,
    r.recommended_action,
    r.prevention_measure
FROM communication_incidents i
JOIN category_recommendations r
    ON r.category = i.category;

-- ============================================================
-- 21. AGGREGATION AND PERFORMANCE REPORTING
-- ============================================================

-- Incident distribution by category and severity.

SELECT
    category,
    severity,
    COUNT(*) AS total_incidents
FROM communication_incidents
GROUP BY category, severity
ORDER BY total_incidents DESC;

-- Department-level communication performance.

SELECT
    d.department_name,
    COUNT(i.incident_id) AS total_incidents,
    COUNT(i.incident_id) FILTER (
        WHERE i.status = 'closed'
    ) AS closed_incidents,
    ROUND(
        100.0 * COUNT(i.incident_id) FILTER (
            WHERE i.status IN ('resolved', 'closed')
        ) / NULLIF(COUNT(i.incident_id), 0),
        2
    ) AS resolution_rate
FROM departments d
LEFT JOIN communication_incidents i
    ON i.department_id = d.department_id
GROUP BY d.department_id, d.department_name
ORDER BY total_incidents DESC;

-- Average resolution time.

SELECT
    department_id,
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (resolved_at - created_at))
            / 3600.0
        )::NUMERIC,
        2
    ) AS average_resolution_hours
FROM communication_incidents
WHERE resolved_at IS NOT NULL
GROUP BY department_id;

-- ============================================================
-- 22. CTE: COMMUNICATION INCIDENT PRIORITIZATION
-- ============================================================

WITH priority_scores AS (
    SELECT
        incident_id,
        title,
        category,
        severity,
        status,
        CASE severity
            WHEN 'critical' THEN 100
            WHEN 'high' THEN 75
            WHEN 'medium' THEN 40
            WHEN 'low' THEN 15
        END AS severity_score,
        EXTRACT(
            EPOCH FROM (CURRENT_TIMESTAMP - created_at)
        ) / 3600 AS age_hours
    FROM communication_incidents
    WHERE status NOT IN ('resolved', 'closed')
)
SELECT
    incident_id,
    title,
    category,
    severity,
    severity_score,
    ROUND(age_hours::NUMERIC, 2) AS age_hours,
    ROUND(
        (severity_score + LEAST(age_hours, 72))::NUMERIC,
        2
    ) AS priority_score
FROM priority_scores
ORDER BY priority_score DESC;

-- ============================================================
-- 23. CTE: DEPARTMENT COMMUNICATION BOTTLENECKS
-- ============================================================

WITH department_metrics AS (
    SELECT
        d.department_name,
        COUNT(i.incident_id) AS incident_count,
        COUNT(i.incident_id) FILTER (
            WHERE i.status IN ('open', 'investigating', 'action_required')
        ) AS unresolved_count,
        AVG(
            EXTRACT(EPOCH FROM (
                i.resolved_at - i.created_at
            )) / 3600.0
        ) FILTER (
            WHERE i.resolved_at IS NOT NULL
        ) AS average_resolution_hours
    FROM departments d
    LEFT JOIN communication_incidents i
        ON i.department_id = d.department_id
    GROUP BY d.department_id, d.department_name
)
SELECT
    department_name,
    incident_count,
    unresolved_count,
    ROUND(average_resolution_hours::NUMERIC, 2)
        AS average_resolution_hours
FROM department_metrics
ORDER BY unresolved_count DESC;

-- ============================================================
-- 24. CLOSURE ELIGIBILITY REPORT
-- ============================================================

SELECT
    i.incident_id,
    i.title,
    e.eligible,
    e.failure_reason
FROM communication_incidents i
CROSS JOIN LATERAL
    evaluate_closure_eligibility(i.incident_id) e
ORDER BY i.incident_id, e.eligible DESC;

-- ============================================================
-- 25. TRANSACTIONAL WORKFLOW EXAMPLE
-- ============================================================

-- Resolve incident 2 only after recording a corrective action
-- and a resolution. Feedback is then collected before closure.

DO $$
DECLARE
    v_incident_id BIGINT := 2;
BEGIN
    UPDATE communication_incidents
    SET
        corrective_action =
            'Introduce monitored response deadlines and escalation.',
        resolution =
            'Support ownership and response escalation were configured.'
    WHERE incident_id = v_incident_id;

    CALL transition_incident(
        v_incident_id,
        'resolved'
    );

    UPDATE communication_incidents
    SET feedback = 'accepted'
    WHERE incident_id = v_incident_id;

    CALL transition_incident(
        v_incident_id,
        'closed'
    );

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE
            'Workflow failed for incident %: %',
            v_incident_id,
            SQLERRM;
        RAISE;
END;
$$;

-- ============================================================
-- 26. TRANSACTIONAL REJECTION EXAMPLE
-- ============================================================

-- The following savepoint demonstrates rollback when an
-- invalid closure operation is attempted.

SAVEPOINT communication_validation;

DO $$
BEGIN
    BEGIN
        CALL transition_incident(
            3,
            'closed'
        );

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected closure rejection: %',
                SQLERRM;
    END;
END;
$$;

ROLLBACK TO SAVEPOINT communication_validation;

RELEASE SAVEPOINT communication_validation;

-- ============================================================
-- 27. FINAL OPERATIONAL REPORT
-- ============================================================

SELECT
    COUNT(*) AS total_incidents,

    COUNT(*) FILTER (
        WHERE status = 'open'
    ) AS open_incidents,

    COUNT(*) FILTER (
        WHERE status = 'investigating'
    ) AS under_investigation,

    COUNT(*) FILTER (
        WHERE status = 'action_required'
    ) AS action_required,

    COUNT(*) FILTER (
        WHERE status = 'resolved'
    ) AS resolved_incidents,

    COUNT(*) FILTER (
        WHERE status = 'closed'
    ) AS closed_incidents,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE status IN ('resolved', 'closed')
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS resolution_percentage

FROM communication_incidents;

COMMIT;
