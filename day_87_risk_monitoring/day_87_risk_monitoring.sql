-- ============================================================
-- PROJECT RISK MONITORING AND TRACKING DATABASE
-- PostgreSQL 15+
--
-- Implements:
-- 1. Project and repository-level risk registers
-- 2. Risk categories and ownership
-- 3. Probability-impact assessment
-- 4. Risk response and mitigation plans
-- 5. Risk lifecycle and audit history
-- 6. Monitoring observations
-- 7. Escalation and overdue identification
-- 8. Risk portfolio reporting
-- 9. Review schedules
-- 10. Transactional risk-management operations
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS project_risk;

SET search_path TO project_risk, public;

-- ============================================================
-- 1. ENUMERATIONS
-- ============================================================

CREATE TYPE risk_category AS ENUM (
    'schedule',
    'cost',
    'technical',
    'resource',
    'security',
    'operational',
    'legal',
    'external'
);

CREATE TYPE risk_status AS ENUM (
    'identified',
    'assessed',
    'mitigation_planned',
    'monitoring',
    'escalated',
    'materialized',
    'closed'
);

CREATE TYPE risk_response AS ENUM (
    'avoid',
    'mitigate',
    'transfer',
    'accept'
);

CREATE TYPE risk_level AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE risk_event_type AS ENUM (
    'registered',
    'assessed',
    'mitigation_recorded',
    'observation_recorded',
    'status_changed',
    'escalated',
    'materialized',
    'closed'
);

-- ============================================================
-- 2. PROJECTS
-- ============================================================

CREATE TABLE projects (
    project_id VARCHAR(30) PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    project_manager VARCHAR(150) NOT NULL,
    start_date DATE NOT NULL,
    planned_end_date DATE NOT NULL,
    approved_budget NUMERIC(15,2) NOT NULL,
    project_status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_project_dates
        CHECK (planned_end_date >= start_date),

    CONSTRAINT valid_project_budget
        CHECK (approved_budget >= 0),

    CONSTRAINT valid_project_status
        CHECK (
            project_status IN (
                'planning',
                'active',
                'on_hold',
                'completed',
                'cancelled'
            )
        )
);

-- ============================================================
-- 3. USERS AND RISK OWNERS
-- ============================================================

CREATE TABLE project_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    role_name VARCHAR(80) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 4. RISK ASSESSMENT POLICIES
-- ============================================================

CREATE TABLE assessment_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(100) NOT NULL UNIQUE,
    low_maximum SMALLINT NOT NULL DEFAULT 4,
    medium_maximum SMALLINT NOT NULL DEFAULT 9,
    high_maximum SMALLINT NOT NULL DEFAULT 16,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_policy_thresholds
        CHECK (
            low_maximum >= 1
            AND low_maximum < medium_maximum
            AND medium_maximum < high_maximum
            AND high_maximum < 25
        )
);

INSERT INTO assessment_policies (
    policy_name,
    low_maximum,
    medium_maximum,
    high_maximum
)
VALUES (
    'STANDARD_5X5',
    4,
    9,
    16
);

-- ============================================================
-- 5. RISK REGISTER
-- ============================================================

CREATE TABLE risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id VARCHAR(30) NOT NULL
        REFERENCES projects(project_id),

    risk_code VARCHAR(40) NOT NULL,
    title VARCHAR(250) NOT NULL,
    description TEXT NOT NULL,

    category risk_category NOT NULL,
    owner_id BIGINT NOT NULL
        REFERENCES project_users(user_id),

    probability SMALLINT NOT NULL,
    impact SMALLINT NOT NULL,

    response risk_response NOT NULL DEFAULT 'mitigate',

    status risk_status NOT NULL DEFAULT 'identified',

    mitigation_plan TEXT,
    contingency_plan TEXT,

    due_date DATE NOT NULL,

    identified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_reviewed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    review_count INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,

    closed_at TIMESTAMPTZ,
    closure_reason TEXT,

    CONSTRAINT unique_project_risk_code
        UNIQUE (project_id, risk_code),

    CONSTRAINT valid_probability
        CHECK (probability BETWEEN 1 AND 5),

    CONSTRAINT valid_impact
        CHECK (impact BETWEEN 1 AND 5),

    CONSTRAINT valid_review_count
        CHECK (review_count >= 0),

    CONSTRAINT valid_version
        CHECK (version >= 1),

    CONSTRAINT valid_risk_title
        CHECK (LENGTH(TRIM(title)) > 0),

    CONSTRAINT valid_risk_description
        CHECK (LENGTH(TRIM(description)) > 0),

    CONSTRAINT valid_mitigation_state
        CHECK (
            status <> 'mitigation_planned'
            OR (
                mitigation_plan IS NOT NULL
                AND LENGTH(TRIM(mitigation_plan)) > 0
            )
        ),

    CONSTRAINT valid_closed_state
        CHECK (
            status <> 'closed'
            OR (
                closed_at IS NOT NULL
                AND closure_reason IS NOT NULL
                AND LENGTH(TRIM(closure_reason)) > 0
            )
        )
);

-- ============================================================
-- 6. RISK ASSESSMENT FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_risk_level(
    p_probability INTEGER,
    p_impact INTEGER,
    p_policy_id BIGINT DEFAULT 1
)
RETURNS risk_level
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_exposure INTEGER;
    v_low INTEGER;
    v_medium INTEGER;
    v_high INTEGER;
BEGIN
    IF p_probability NOT BETWEEN 1 AND 5
       OR p_impact NOT BETWEEN 1 AND 5 THEN
        RAISE EXCEPTION
            'Probability and impact must be between 1 and 5';
    END IF;

    SELECT
        low_maximum,
        medium_maximum,
        high_maximum
    INTO
        v_low,
        v_medium,
        v_high
    FROM assessment_policies
    WHERE policy_id = p_policy_id
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active assessment policy not found';
    END IF;

    v_exposure := p_probability * p_impact;

    IF v_exposure <= v_low THEN
        RETURN 'low';
    ELSIF v_exposure <= v_medium THEN
        RETURN 'medium';
    ELSIF v_exposure <= v_high THEN
        RETURN 'high';
    ELSE
        RETURN 'critical';
    END IF;
END;
$$;

-- ============================================================
-- 7. RISK AUDIT HISTORY
-- ============================================================

CREATE TABLE risk_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    event_type risk_event_type NOT NULL,

    previous_status risk_status,
    new_status risk_status,

    previous_probability SMALLINT,
    previous_impact SMALLINT,

    new_probability SMALLINT,
    new_impact SMALLINT,

    actor_id BIGINT
        REFERENCES project_users(user_id),

    event_description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 8. MONITORING OBSERVATIONS
-- ============================================================

CREATE TABLE risk_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    observed_probability SMALLINT NOT NULL,
    observed_impact SMALLINT NOT NULL,

    observed_exposure SMALLINT GENERATED ALWAYS AS (
        observed_probability * observed_impact
    ) STORED,

    notes TEXT NOT NULL,
    recorded_by BIGINT NOT NULL
        REFERENCES project_users(user_id),

    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_observed_probability
        CHECK (observed_probability BETWEEN 1 AND 5),

    CONSTRAINT valid_observed_impact
        CHECK (observed_impact BETWEEN 1 AND 5),

    CONSTRAINT valid_observation_notes
        CHECK (LENGTH(TRIM(notes)) > 0)
);

-- ============================================================
-- 9. RISK REVIEW SCHEDULE
-- ============================================================

CREATE TABLE risk_review_schedule (
    schedule_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    reviewer_id BIGINT NOT NULL
        REFERENCES project_users(user_id),

    review_date DATE NOT NULL,

    review_completed BOOLEAN NOT NULL DEFAULT FALSE,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (risk_id, review_date),

    CONSTRAINT valid_review_completion
        CHECK (
            review_completed = FALSE
            OR completed_at IS NOT NULL
        )
);

-- ============================================================
-- 10. STATUS TRANSITION VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_risk_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN

        IF OLD.status = 'identified'
           AND NEW.status NOT IN ('assessed', 'closed') THEN
            RAISE EXCEPTION 'Invalid transition from identified';
        END IF;

        IF OLD.status = 'assessed'
           AND NEW.status NOT IN (
               'mitigation_planned',
               'monitoring',
               'escalated',
               'closed'
           ) THEN
            RAISE EXCEPTION 'Invalid transition from assessed';
        END IF;

        IF OLD.status = 'mitigation_planned'
           AND NEW.status NOT IN (
               'monitoring',
               'escalated',
               'closed'
           ) THEN
            RAISE EXCEPTION
                'Invalid transition from mitigation planned';
        END IF;

        IF OLD.status = 'monitoring'
           AND NEW.status NOT IN (
               'escalated',
               'materialized',
               'closed'
           ) THEN
            RAISE EXCEPTION 'Invalid transition from monitoring';
        END IF;

        IF OLD.status = 'escalated'
           AND NEW.status NOT IN (
               'monitoring',
               'materialized',
               'closed'
           ) THEN
            RAISE EXCEPTION 'Invalid transition from escalated';
        END IF;

        IF OLD.status = 'materialized'
           AND NEW.status <> 'closed' THEN
            RAISE EXCEPTION
                'Materialized risks can only be closed';
        END IF;

        IF OLD.status = 'closed' THEN
            RAISE EXCEPTION
                'Closed risks cannot be reopened through ordinary updates';
        END IF;
    END IF;

    IF NEW.status = 'closed' THEN
        IF NEW.closed_at IS NULL THEN
            NEW.closed_at := NOW();
        END IF;

        IF NEW.closure_reason IS NULL
           OR LENGTH(TRIM(NEW.closure_reason)) = 0 THEN
            RAISE EXCEPTION 'Closure reason is required';
        END IF;
    END IF;

    IF NEW.version <> OLD.version + 1 THEN
        RAISE EXCEPTION
            'Every risk update must increment version by one';
    END IF;

    NEW.updated_at := NOW();

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_risk_transition
BEFORE UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION validate_risk_transition();

-- ============================================================
-- 11. AUTOMATIC AUDIT HISTORY
-- ============================================================

CREATE OR REPLACE FUNCTION record_risk_history()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN

        INSERT INTO risk_history (
            risk_id,
            event_type,
            new_status,
            new_probability,
            new_impact,
            event_description
        )
        VALUES (
            NEW.risk_id,
            'registered',
            NEW.status,
            NEW.probability,
            NEW.impact,
            'Risk registered'
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN

        INSERT INTO risk_history (
            risk_id,
            event_type,
            previous_status,
            new_status,
            previous_probability,
            previous_impact,
            new_probability,
            new_impact,
            event_description
        )
        VALUES (
            NEW.risk_id,
            CASE
                WHEN OLD.status <> NEW.status
                    THEN 'status_changed'::risk_event_type
                ELSE 'observation_recorded'::risk_event_type
            END,
            OLD.status,
            NEW.status,
            OLD.probability,
            OLD.impact,
            NEW.probability,
            NEW.impact,
            'Risk record updated'
        );

        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_record_risk_history
AFTER INSERT OR UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION record_risk_history();

-- ============================================================
-- 12. PERFORMANCE INDEXES
-- ============================================================

CREATE INDEX idx_risks_project
    ON risks(project_id);

CREATE INDEX idx_risks_owner
    ON risks(owner_id);

CREATE INDEX idx_risks_status
    ON risks(status);

CREATE INDEX idx_risks_category
    ON risks(category);

CREATE INDEX idx_risks_due_date
    ON risks(due_date)
    WHERE status <> 'closed';

CREATE INDEX idx_risks_active_priority
    ON risks(
        (probability * impact) DESC,
        due_date ASC
    )
    WHERE status <> 'closed';

CREATE INDEX idx_risk_history_risk_date
    ON risk_history(risk_id, created_at DESC);

CREATE INDEX idx_observations_risk_date
    ON risk_observations(risk_id, observed_at DESC);

CREATE INDEX idx_review_schedule_pending
    ON risk_review_schedule(review_date, reviewer_id)
    WHERE review_completed = FALSE;

-- ============================================================
-- 13. REPORTING VIEWS
-- ============================================================

CREATE VIEW v_risk_register AS
SELECT
    r.risk_id,
    r.project_id,
    p.project_name,
    r.risk_code,
    r.title,
    r.description,
    r.category,
    u.full_name AS risk_owner,
    r.probability,
    r.impact,
    r.probability * r.impact AS exposure,
    calculate_risk_level(
        r.probability,
        r.impact,
        1
    ) AS risk_level,
    r.response,
    r.status,
    r.mitigation_plan,
    r.contingency_plan,
    r.due_date,
    r.last_reviewed_at,
    r.review_count,
    r.version
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_users u
    ON u.user_id = r.owner_id;

CREATE VIEW v_active_risks AS
SELECT *
FROM v_risk_register
WHERE status <> 'closed';

CREATE VIEW v_overdue_risks AS
SELECT *
FROM v_active_risks
WHERE due_date < CURRENT_DATE;

CREATE VIEW v_critical_risks AS
SELECT *
FROM v_active_risks
WHERE risk_level = 'critical';

CREATE VIEW v_stale_risks AS
SELECT
    r.*,
    CASE
        WHEN last_reviewed_at IS NULL THEN NULL
        ELSE CURRENT_DATE - last_reviewed_at::DATE
    END AS days_since_review
FROM v_active_risks r
WHERE last_reviewed_at IS NULL
   OR last_reviewed_at < NOW() - INTERVAL '7 days';

-- ============================================================
-- 14. RISK REGISTRATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION register_project_risk(
    p_project_id VARCHAR(30),
    p_risk_code VARCHAR(40),
    p_title VARCHAR(250),
    p_description TEXT,
    p_category risk_category,
    p_owner_id BIGINT,
    p_probability SMALLINT,
    p_impact SMALLINT,
    p_due_date DATE,
    p_response risk_response
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_risk_id BIGINT;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM projects
        WHERE project_id = p_project_id
          AND project_status = 'active'
    ) THEN
        RAISE EXCEPTION
            'Project does not exist or is not active';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM project_users
        WHERE user_id = p_owner_id
          AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION
            'Risk owner is not an active project user';
    END IF;

    PERFORM calculate_risk_level(
        p_probability,
        p_impact,
        1
    );

    INSERT INTO risks (
        project_id,
        risk_code,
        title,
        description,
        category,
        owner_id,
        probability,
        impact,
        due_date,
        response
    )
    VALUES (
        p_project_id,
        p_risk_code,
        p_title,
        p_description,
        p_category,
        p_owner_id,
        p_probability,
        p_impact,
        p_due_date,
        p_response
    )
    RETURNING risk_id INTO v_risk_id;

    RETURN v_risk_id;
END;
$$;

-- ============================================================
-- 15. MONITORING PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE record_risk_observation(
    p_risk_id BIGINT,
    p_probability SMALLINT,
    p_impact SMALLINT,
    p_notes TEXT,
    p_recorded_by BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_risk risks%ROWTYPE;
    v_level risk_level;
BEGIN
    SELECT *
    INTO v_risk
    FROM risks
    WHERE risk_id = p_risk_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk % not found', p_risk_id;
    END IF;

    IF v_risk.status NOT IN ('monitoring', 'escalated') THEN
        RAISE EXCEPTION
            'Only actively monitored risks can be observed';
    END IF;

    PERFORM calculate_risk_level(
        p_probability,
        p_impact,
        1
    );

    INSERT INTO risk_observations (
        risk_id,
        observed_probability,
        observed_impact,
        notes,
        recorded_by
    )
    VALUES (
        p_risk_id,
        p_probability,
        p_impact,
        p_notes,
        p_recorded_by
    );

    v_level := calculate_risk_level(
        p_probability,
        p_impact,
        1
    );

    UPDATE risks
    SET
        probability = p_probability,
        impact = p_impact,
        review_count = review_count + 1,
        last_reviewed_at = NOW(),
        status = CASE
            WHEN v_level = 'critical' THEN 'escalated'
            ELSE status
        END,
        version = version + 1
    WHERE risk_id = p_risk_id;

    IF v_level = 'critical' THEN
        RAISE NOTICE
            'Risk % automatically escalated to critical status',
            p_risk_id;
    END IF;
END;
$$;

-- ============================================================
-- 16. MITIGATION RECORDING PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE record_mitigation(
    p_risk_id BIGINT,
    p_mitigation TEXT,
    p_contingency TEXT,
    p_expected_version INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_risk risks%ROWTYPE;
BEGIN
    SELECT *
    INTO v_risk
    FROM risks
    WHERE risk_id = p_risk_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk not found';
    END IF;

    IF v_risk.version <> p_expected_version THEN
        RAISE EXCEPTION
            'Concurrent update detected';
    END IF;

    IF v_risk.status <> 'assessed' THEN
        RAISE EXCEPTION
            'Risk must be assessed before mitigation planning';
    END IF;

    IF p_mitigation IS NULL
       OR LENGTH(TRIM(p_mitigation)) = 0 THEN
        RAISE EXCEPTION 'Mitigation plan is required';
    END IF;

    IF p_contingency IS NULL
       OR LENGTH(TRIM(p_contingency)) = 0 THEN
        RAISE EXCEPTION 'Contingency plan is required';
    END IF;

    UPDATE risks
    SET
        mitigation_plan = p_mitigation,
        contingency_plan = p_contingency,
        status = 'mitigation_planned',
        version = version + 1
    WHERE risk_id = p_risk_id;
END;
$$;

-- ============================================================
-- 17. LIFECYCLE TRANSITION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION change_risk_status(
    p_risk_id BIGINT,
    p_new_status risk_status,
    p_expected_version INTEGER,
    p_closure_reason TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_risk risks%ROWTYPE;
BEGIN
    SELECT *
    INTO v_risk
    FROM risks
    WHERE risk_id = p_risk_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk not found';
    END IF;

    IF v_risk.version <> p_expected_version THEN
        RAISE EXCEPTION
            'Version conflict: expected %, found %',
            p_expected_version,
            v_risk.version;
    END IF;

    IF p_new_status = 'closed' THEN
        IF p_closure_reason IS NULL
           OR LENGTH(TRIM(p_closure_reason)) = 0 THEN
            RAISE EXCEPTION
                'Closure reason is mandatory';
        END IF;
    END IF;

    UPDATE risks
    SET
        status = p_new_status,
        closure_reason = CASE
            WHEN p_new_status = 'closed'
                THEN p_closure_reason
            ELSE closure_reason
        END,
        closed_at = CASE
            WHEN p_new_status = 'closed'
                THEN NOW()
            ELSE closed_at
        END,
        version = version + 1
    WHERE risk_id = p_risk_id;
END;
$$;

-- ============================================================
-- 18. PORTFOLIO REPORT FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION project_risk_report(
    p_project_id VARCHAR(30)
)
RETURNS TABLE (
    risk_level risk_level,
    total_risks BIGINT,
    active_risks BIGINT,
    average_exposure NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        calculate_risk_level(
            r.probability,
            r.impact,
            1
        ) AS risk_level,

        COUNT(*) AS total_risks,

        COUNT(*) FILTER (
            WHERE r.status <> 'closed'
        ) AS active_risks,

        ROUND(
            AVG(r.probability * r.impact),
            2
        ) AS average_exposure

    FROM risks r

    WHERE r.project_id = p_project_id

    GROUP BY 1
    ORDER BY 1;
$$;

-- ============================================================
-- 19. SAMPLE PROJECTS
-- ============================================================

INSERT INTO projects (
    project_id,
    project_name,
    project_manager,
    start_date,
    planned_end_date,
    approved_budget
)
VALUES
(
    'PRJ-2026-001',
    'Enterprise Technology Modernization',
    'Project Director',
    '2026-01-01',
    '2027-03-31',
    5000000
),
(
    'PRJ-2026-002',
    'Cybersecurity Infrastructure Upgrade',
    'Security Director',
    '2026-02-01',
    '2027-01-31',
    2500000
);

-- ============================================================
-- 20. SAMPLE USERS
-- ============================================================

INSERT INTO project_users (
    full_name,
    email,
    role_name
)
VALUES
(
    'Amit Sharma',
    'amit.sharma@example.org',
    'Project Manager'
),
(
    'Neha Verma',
    'neha.verma@example.org',
    'Procurement Manager'
),
(
    'Rahul Singh',
    'rahul.singh@example.org',
    'Security Manager'
),
(
    'Priya Gupta',
    'priya.gupta@example.org',
    'Project Controller'
),
(
    'Arjun Mehta',
    'arjun.mehta@example.org',
    'Technical Lead'
);

-- ============================================================
-- 21. SAMPLE RISK REGISTRATION
-- ============================================================

SELECT register_project_risk(
    'PRJ-2026-001',
    'RISK-001',
    'Critical supplier delivery delay',
    'Primary hardware supplier may miss the delivery milestone.',
    'schedule',
    2,
    4,
    5,
    CURRENT_DATE + 15,
    'mitigate'
);

SELECT register_project_risk(
    'PRJ-2026-001',
    'RISK-002',
    'Unexpected implementation cost',
    'Additional implementation expenses may exceed budget.',
    'cost',
    4,
    3,
    4,
    CURRENT_DATE + 30,
    'mitigate'
);

SELECT register_project_risk(
    'PRJ-2026-001',
    'RISK-003',
    'Unauthorized system access',
    'Incorrect access permissions may expose sensitive records.',
    'security',
    3,
    2,
    5,
    CURRENT_DATE + 5,
    'avoid'
);

SELECT register_project_risk(
    'PRJ-2026-002',
    'RISK-004',
    'Specialist resource shortage',
    'Insufficient specialist availability may delay deployment.',
    'resource',
    5,
    3,
    3,
    CURRENT_DATE + 20,
    'mitigate'
);

-- ============================================================
-- 22. WORKFLOW PROCESSING
-- ============================================================

-- Assess the supplier risk.
SELECT change_risk_status(
    risk_id,
    'assessed',
    version
)
FROM risks
WHERE risk_code = 'RISK-001';

-- Record mitigation and contingency plans.
CALL record_mitigation(
    (
        SELECT risk_id
        FROM risks
        WHERE risk_code = 'RISK-001'
    ),
    'Qualify a secondary supplier and confirm delivery capacity.',
    'Use approved reserve inventory.',
    (
        SELECT version
        FROM risks
        WHERE risk_code = 'RISK-001'
    )
);

-- Start monitoring.
SELECT change_risk_status(
    risk_id,
    'monitoring',
    version
)
FROM risks
WHERE risk_code = 'RISK-001';

-- Start monitoring the remaining assessed risks.
SELECT change_risk_status(
    risk_id,
    'assessed',
    version
)
FROM risks
WHERE risk_code IN ('RISK-002', 'RISK-003', 'RISK-004');

-- ============================================================
-- 23. MONITORING OBSERVATION
-- ============================================================

CALL record_risk_observation(
    (
        SELECT risk_id
        FROM risks
        WHERE risk_code = 'RISK-001'
    ),
    5,
    5,
    'Supplier confirmed a further delivery delay.',
    2
);

-- ============================================================
-- 24. REVIEW SCHEDULE SAMPLE
-- ============================================================

INSERT INTO risk_review_schedule (
    risk_id,
    reviewer_id,
    review_date
)
SELECT
    r.risk_id,
    r.owner_id,
    CURRENT_DATE + 7
FROM risks r
WHERE r.status <> 'closed';

-- ============================================================
-- 25. RETRIEVAL QUERIES
-- ============================================================

-- Complete risk register.
SELECT *
FROM v_risk_register
ORDER BY exposure DESC;

-- Active project risks.
SELECT *
FROM v_active_risks
WHERE project_id = 'PRJ-2026-001'
ORDER BY exposure DESC;

-- Critical risks requiring management attention.
SELECT *
FROM v_critical_risks
ORDER BY due_date;

-- Risks grouped by category.
SELECT
    category,
    COUNT(*) AS risk_count,
    SUM(exposure) AS cumulative_exposure
FROM v_risk_register
GROUP BY category
ORDER BY cumulative_exposure DESC;

-- Risks grouped by responsible owner.
SELECT
    risk_owner,
    COUNT(*) AS assigned_risks,
    ROUND(AVG(exposure), 2) AS average_exposure,
    MAX(exposure) AS maximum_exposure
FROM v_risk_register
GROUP BY risk_owner
ORDER BY maximum_exposure DESC;

-- ============================================================
-- 26. VALIDATION QUERIES
-- ============================================================

-- Missing mitigation plans.
SELECT
    risk_id,
    risk_code,
    title,
    status
FROM risks
WHERE status = 'mitigation_planned'
  AND (
      mitigation_plan IS NULL
      OR LENGTH(TRIM(mitigation_plan)) = 0
  );

-- Missing risk observations.
SELECT
    r.risk_id,
    r.risk_code,
    r.title,
    r.last_reviewed_at
FROM risks r
WHERE r.status IN ('monitoring', 'escalated')
  AND r.last_reviewed_at IS NULL;

-- Review schedule completion validation.
SELECT
    schedule_id,
    risk_id,
    review_date,
    reviewer_id
FROM risk_review_schedule
WHERE review_completed = FALSE
ORDER BY review_date;

-- ============================================================
-- 27. CTE-BASED RISK PRIORITIZATION
-- ============================================================

WITH ranked_risks AS (
    SELECT
        r.risk_id,
        r.project_id,
        r.risk_code,
        r.title,
        r.owner_id,
        r.probability,
        r.impact,
        r.probability * r.impact AS exposure,
        r.status,
        r.due_date,

        ROW_NUMBER() OVER (
            PARTITION BY r.project_id
            ORDER BY
                r.probability * r.impact DESC,
                r.due_date ASC
        ) AS priority_rank

    FROM risks r

    WHERE r.status <> 'closed'
)
SELECT *
FROM ranked_risks
WHERE priority_rank <= 5
ORDER BY project_id, priority_rank;

-- ============================================================
-- 28. RISK TREND ANALYSIS
-- ============================================================

WITH observation_history AS (
    SELECT
        ro.risk_id,
        ro.observed_at,
        ro.observed_exposure,

        LAG(ro.observed_exposure) OVER (
            PARTITION BY ro.risk_id
            ORDER BY ro.observed_at
        ) AS previous_exposure

    FROM risk_observations ro
)
SELECT
    risk_id,
    observed_at,
    previous_exposure,
    observed_exposure,

    CASE
        WHEN previous_exposure IS NULL
            THEN 'INITIAL'
        WHEN observed_exposure > previous_exposure
            THEN 'INCREASING'
        WHEN observed_exposure < previous_exposure
            THEN 'DECREASING'
        ELSE 'UNCHANGED'
    END AS exposure_trend

FROM observation_history
ORDER BY risk_id, observed_at;

-- ============================================================
-- 29. AGGREGATED PROJECT REPORT
-- ============================================================

SELECT *
FROM project_risk_report('PRJ-2026-001');

-- ============================================================
-- 30. OVERDUE AND STALE RISK REPORTING
-- ============================================================

SELECT *
FROM v_overdue_risks
ORDER BY exposure DESC;

SELECT *
FROM v_stale_risks
ORDER BY days_since_review DESC NULLS LAST;

-- ============================================================
-- 31. PENDING REVIEW WORKLOAD
-- ============================================================

SELECT
    u.full_name,
    COUNT(*) AS pending_reviews,
    MIN(s.review_date) AS next_review_date
FROM risk_review_schedule s
JOIN project_users u
    ON u.user_id = s.reviewer_id
WHERE s.review_completed = FALSE
GROUP BY u.full_name
ORDER BY pending_reviews DESC;

-- ============================================================
-- 32. AUDIT HISTORY
-- ============================================================

SELECT
    h.history_id,
    r.risk_code,
    h.event_type,
    h.previous_status,
    h.new_status,
    h.previous_probability,
    h.previous_impact,
    h.new_probability,
    h.new_impact,
    h.event_description,
    h.created_at
FROM risk_history h
JOIN risks r
    ON r.risk_id = h.risk_id
ORDER BY h.created_at DESC;

-- ============================================================
-- 33. TRANSACTIONAL WORKFLOW DEMONSTRATION
-- ============================================================

-- This transaction demonstrates an atomic risk closure.
-- It commits only when the expected version is valid.

DO $$
DECLARE
    v_risk_id BIGINT;
    v_version INTEGER;
BEGIN
    SELECT risk_id, version
    INTO v_risk_id, v_version
    FROM risks
    WHERE risk_code = 'RISK-002'
    FOR UPDATE;

    IF FOUND THEN
        change_risk_status(
            v_risk_id,
            'closed',
            v_version,
            'Cost contingency was approved and the exposure resolved.'
        );
    END IF;
END;
$$;

-- ============================================================
-- 34. POST-WORKFLOW VALIDATION
-- ============================================================

-- Current portfolio state.
SELECT
    status,
    COUNT(*) AS total_risks,
    SUM(probability * impact) AS total_exposure
FROM risks
GROUP BY status
ORDER BY status;

-- Final active risk priorities.
SELECT
    risk_code,
    title,
    risk_owner,
    exposure,
    risk_level,
    status,
    due_date
FROM v_active_risks
ORDER BY
    exposure DESC,
    due_date ASC;

COMMIT;

-- ============================================================
-- OPERATIONAL NOTES
-- ============================================================
--
-- Risk exposure is calculated as probability multiplied by impact.
--
-- Risk observations are separate historical records. The risks table
-- contains the latest accepted assessment.
--
-- risk_history records lifecycle and assessment changes.
--
-- Optimistic concurrency is enforced through the version column.
--
-- SELECT ... FOR UPDATE serializes competing monitoring operations.
--
-- The sample policy uses fixed thresholds. Multi-policy reporting
-- should explicitly associate each risk with its assessment policy.
--
-- Database roles and GRANT statements should be configured separately
-- for production deployments.
--
-- Sensitive descriptions and audit data require appropriate access
-- controls, retention policies, and backup protection.
--
-- Indexes should be evaluated with EXPLAIN (ANALYZE, BUFFERS) against
-- actual project volumes and query workloads.
-- ============================================================
