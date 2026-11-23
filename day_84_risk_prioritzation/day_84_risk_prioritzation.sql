-- ============================================================
-- PROJECT RISK PRIORITIZATION AND MANAGEMENT DATABASE
-- PostgreSQL 15+
--
-- Implements:
-- Risk registration, assessment, ownership, mitigation,
-- status transitions, priority ranking, and reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS risk_management;

SET search_path TO risk_management, public;

-- ------------------------------------------------------------
-- ENUMERATED DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE risk_category AS ENUM (
    'TECHNICAL',
    'SECURITY',
    'FINANCIAL',
    'OPERATIONAL',
    'SCHEDULE',
    'LEGAL',
    'RESOURCE',
    'EXTERNAL'
);

CREATE TYPE risk_status AS ENUM (
    'IDENTIFIED',
    'ASSESSED',
    'MITIGATING',
    'MONITORING',
    'CLOSED'
);

CREATE TYPE priority_level AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);

-- ------------------------------------------------------------
-- PROJECTS
-- ------------------------------------------------------------

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code VARCHAR(30) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    project_manager VARCHAR(150) NOT NULL,
    approved_budget NUMERIC(15,2) NOT NULL DEFAULT 0,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_project_budget
        CHECK (approved_budget >= 0),

    CONSTRAINT valid_project_dates
        CHECK (end_date IS NULL OR end_date >= start_date)
);

-- ------------------------------------------------------------
-- RISK OWNERS
-- ------------------------------------------------------------

CREATE TABLE risk_owners (
    owner_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_name VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- ------------------------------------------------------------
-- RISK REGISTER
-- ------------------------------------------------------------

CREATE TABLE risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    risk_code VARCHAR(30) NOT NULL,
    title VARCHAR(250) NOT NULL,
    description TEXT NOT NULL,

    category risk_category NOT NULL,

    probability SMALLINT NOT NULL,
    impact SMALLINT NOT NULL,
    urgency SMALLINT NOT NULL,
    detectability SMALLINT NOT NULL,

    mitigation_effectiveness SMALLINT NOT NULL DEFAULT 0,

    owner_id BIGINT NOT NULL
        REFERENCES risk_owners(owner_id),

    deadline DATE NOT NULL,

    mitigation_cost NUMERIC(15,2) NOT NULL DEFAULT 0,

    status risk_status NOT NULL DEFAULT 'IDENTIFIED',

    identified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (project_id, risk_code),

    CONSTRAINT valid_probability
        CHECK (probability BETWEEN 1 AND 5),

    CONSTRAINT valid_impact
        CHECK (impact BETWEEN 1 AND 5),

    CONSTRAINT valid_urgency
        CHECK (urgency BETWEEN 1 AND 5),

    CONSTRAINT valid_detectability
        CHECK (detectability BETWEEN 1 AND 5),

    CONSTRAINT valid_mitigation_effectiveness
        CHECK (mitigation_effectiveness BETWEEN 0 AND 5),

    CONSTRAINT valid_mitigation_cost
        CHECK (mitigation_cost >= 0)
);

-- ------------------------------------------------------------
-- ASSESSMENT HISTORY
-- ------------------------------------------------------------

CREATE TABLE risk_assessments (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    probability SMALLINT NOT NULL CHECK (probability BETWEEN 1 AND 5),
    impact SMALLINT NOT NULL CHECK (impact BETWEEN 1 AND 5),
    urgency SMALLINT NOT NULL CHECK (urgency BETWEEN 1 AND 5),
    detectability SMALLINT NOT NULL CHECK (detectability BETWEEN 1 AND 5),

    mitigation_effectiveness SMALLINT NOT NULL
        CHECK (mitigation_effectiveness BETWEEN 0 AND 5),

    assessment_reason TEXT NOT NULL,

    assessed_by VARCHAR(150) NOT NULL,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- MITIGATION ACTIONS
-- ------------------------------------------------------------

CREATE TABLE mitigation_actions (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    action_title VARCHAR(250) NOT NULL,
    action_description TEXT NOT NULL,

    assigned_to BIGINT NOT NULL
        REFERENCES risk_owners(owner_id),

    estimated_cost NUMERIC(15,2) NOT NULL DEFAULT 0,
    actual_cost NUMERIC(15,2) NOT NULL DEFAULT 0,

    due_date DATE NOT NULL,

    completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (estimated_cost >= 0),
    CHECK (actual_cost >= 0)
);

-- ------------------------------------------------------------
-- RISK STATUS AUDIT
-- ------------------------------------------------------------

CREATE TABLE risk_status_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    previous_status risk_status,
    new_status risk_status NOT NULL,

    changed_by VARCHAR(150) NOT NULL,
    reason TEXT,

    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- RISK STATUS TRANSITION ENFORCEMENT
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_risk_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN

        IF NOT (
            (OLD.status = 'IDENTIFIED'
                AND NEW.status IN ('ASSESSED', 'CLOSED'))
            OR
            (OLD.status = 'ASSESSED'
                AND NEW.status IN (
                    'MITIGATING', 'MONITORING', 'CLOSED'
                ))
            OR
            (OLD.status = 'MITIGATING'
                AND NEW.status IN (
                    'ASSESSED', 'MONITORING', 'CLOSED'
                ))
            OR
            (OLD.status = 'MONITORING'
                AND NEW.status IN ('MITIGATING', 'CLOSED'))
        ) THEN
            RAISE EXCEPTION
                'Invalid risk status transition: % -> %',
                OLD.status, NEW.status;
        END IF;

    END IF;

    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER enforce_risk_transition
BEFORE UPDATE OF status ON risks
FOR EACH ROW
EXECUTE FUNCTION validate_risk_transition();

-- ------------------------------------------------------------
-- STATUS CHANGE AUDIT
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION record_risk_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO risk_status_history (
            risk_id,
            previous_status,
            new_status,
            changed_by,
            reason
        )
        VALUES (
            NEW.risk_id,
            OLD.status,
            NEW.status,
            COALESCE(
                NULLIF(current_setting('app.actor', TRUE), ''),
                session_user
            ),
            'Recorded automatically by status trigger'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER audit_risk_status_change
AFTER UPDATE OF status ON risks
FOR EACH ROW
EXECUTE FUNCTION record_risk_status_change();

-- ------------------------------------------------------------
-- RISK SCORING FUNCTIONS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_inherent_score(
    p_probability INTEGER,
    p_impact INTEGER,
    p_urgency INTEGER
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_probability NOT BETWEEN 1 AND 5
       OR p_impact NOT BETWEEN 1 AND 5
       OR p_urgency NOT BETWEEN 1 AND 5 THEN
        RAISE EXCEPTION 'Risk ratings must be between 1 and 5';
    END IF;

    RETURN p_probability * p_impact * p_urgency;
END;
$$;

CREATE OR REPLACE FUNCTION calculate_residual_score(
    p_probability INTEGER,
    p_impact INTEGER,
    p_urgency INTEGER,
    p_detectability INTEGER,
    p_mitigation_effectiveness INTEGER
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_inherent NUMERIC;
    v_detection_factor NUMERIC;
    v_mitigation_factor NUMERIC;
BEGIN
    IF p_detectability NOT BETWEEN 1 AND 5
       OR p_mitigation_effectiveness NOT BETWEEN 0 AND 5 THEN
        RAISE EXCEPTION 'Invalid residual risk parameters';
    END IF;

    v_inherent := calculate_inherent_score(
        p_probability,
        p_impact,
        p_urgency
    );

    v_detection_factor :=
        0.8 + (p_detectability - 1) * 0.1;

    v_mitigation_factor :=
        1 - p_mitigation_effectiveness * 0.12;

    RETURN ROUND(
        v_inherent *
        v_detection_factor *
        v_mitigation_factor,
        2
    );
END;
$$;

CREATE OR REPLACE FUNCTION classify_priority(
    p_score NUMERIC
)
RETURNS priority_level
LANGUAGE sql
IMMUTABLE
STRICT
AS $$
    SELECT CASE
        WHEN p_score >= 60 THEN 'CRITICAL'::priority_level
        WHEN p_score >= 35 THEN 'HIGH'::priority_level
        WHEN p_score >= 15 THEN 'MEDIUM'::priority_level
        ELSE 'LOW'::priority_level
    END;
$$;

-- ------------------------------------------------------------
-- RISK RANKING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW ranked_risks AS
SELECT
    r.risk_id,
    p.project_code,
    p.project_name,
    r.risk_code,
    r.title,
    r.category,

    o.owner_name,
    o.department,

    r.probability,
    r.impact,
    r.urgency,
    r.detectability,
    r.mitigation_effectiveness,

    calculate_inherent_score(
        r.probability,
        r.impact,
        r.urgency
    ) AS inherent_score,

    calculate_residual_score(
        r.probability,
        r.impact,
        r.urgency,
        r.detectability,
        r.mitigation_effectiveness
    ) AS residual_score,

    classify_priority(
        calculate_residual_score(
            r.probability,
            r.impact,
            r.urgency,
            r.detectability,
            r.mitigation_effectiveness
        )
    ) AS priority,

    r.deadline,
    r.mitigation_cost,
    r.status,

    CASE
        WHEN r.deadline < CURRENT_DATE
         AND r.status <> 'CLOSED'
        THEN TRUE
        ELSE FALSE
    END AS overdue

FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN risk_owners o
    ON o.owner_id = r.owner_id;

-- ------------------------------------------------------------
-- PERFORMANCE INDEXES
-- ------------------------------------------------------------

CREATE INDEX idx_risks_project_status
    ON risks(project_id, status);

CREATE INDEX idx_risks_owner
    ON risks(owner_id);

CREATE INDEX idx_risks_category
    ON risks(category);

CREATE INDEX idx_risks_deadline
    ON risks(deadline)
    WHERE status <> 'CLOSED';

CREATE INDEX idx_assessments_risk_time
    ON risk_assessments(risk_id, assessed_at DESC);

CREATE INDEX idx_mitigation_actions_pending
    ON mitigation_actions(risk_id, due_date)
    WHERE completed = FALSE;

CREATE INDEX idx_status_history_risk_time
    ON risk_status_history(risk_id, changed_at DESC);

-- ------------------------------------------------------------
-- SAMPLE PROJECTS
-- ------------------------------------------------------------

INSERT INTO projects (
    project_code,
    project_name,
    project_manager,
    approved_budget,
    start_date,
    end_date
)
VALUES
(
    'PRJ001',
    'Enterprise Digital Transformation',
    'Project Director',
    2500000,
    CURRENT_DATE,
    CURRENT_DATE + 365
),
(
    'PRJ002',
    'Cloud Security Modernization',
    'Technology Director',
    1500000,
    CURRENT_DATE,
    CURRENT_DATE + 240
);

-- ------------------------------------------------------------
-- SAMPLE RISK OWNERS
-- ------------------------------------------------------------

INSERT INTO risk_owners (
    owner_name,
    department,
    email
)
VALUES
(
    'Security Lead',
    'Cybersecurity',
    'security@example.com'
),
(
    'Cloud Architect',
    'Technology',
    'cloud@example.com'
),
(
    'Finance Lead',
    'Finance',
    'finance@example.com'
),
(
    'Project Manager',
    'Project Management',
    'project@example.com'
),
(
    'Compliance Officer',
    'Compliance',
    'compliance@example.com'
),
(
    'Operations Manager',
    'Operations',
    'operations@example.com'
);

-- ------------------------------------------------------------
-- SAMPLE RISK RECORDS
-- ------------------------------------------------------------

INSERT INTO risks (
    project_id,
    risk_code,
    title,
    description,
    category,
    probability,
    impact,
    urgency,
    detectability,
    mitigation_effectiveness,
    owner_id,
    deadline,
    mitigation_cost,
    status
)
SELECT
    p.project_id,
    sample.risk_code,
    sample.title,
    sample.description,
    sample.category::risk_category,
    sample.probability,
    sample.impact,
    sample.urgency,
    sample.detectability,
    sample.mitigation_effectiveness,
    o.owner_id,
    CURRENT_DATE + sample.deadline_days,
    sample.mitigation_cost,
    'ASSESSED'::risk_status
FROM (
    VALUES
    (
        'PRJ001', 'R001', 'Cybersecurity breach',
        'Unauthorized access to sensitive project information.',
        'SECURITY', 5, 5, 5, 5, 1,
        'security@example.com', 5, 150000::NUMERIC
    ),
    (
        'PRJ001', 'R002', 'Cloud migration failure',
        'Critical infrastructure migration may fail.',
        'TECHNICAL', 4, 5, 4, 3, 2,
        'cloud@example.com', 12, 80000::NUMERIC
    ),
    (
        'PRJ001', 'R003', 'Budget overrun',
        'Unexpected implementation expenditure.',
        'FINANCIAL', 4, 4, 4, 2, 3,
        'finance@example.com', 20, 30000::NUMERIC
    ),
    (
        'PRJ001', 'R004', 'Vendor delivery delay',
        'External vendor may miss delivery milestones.',
        'SCHEDULE', 3, 3, 2, 2, 4,
        'project@example.com', 40, 10000::NUMERIC
    ),
    (
        'PRJ001', 'R005', 'Regulatory non-compliance',
        'Failure to satisfy applicable compliance requirements.',
        'LEGAL', 3, 5, 5, 4, 1,
        'compliance@example.com', 7, 45000::NUMERIC
    ),
    (
        'PRJ002', 'R006', 'Operational service disruption',
        'Service interruption during security modernization.',
        'OPERATIONAL', 3, 4, 3, 3, 2,
        'operations@example.com', 15, 25000::NUMERIC
    )
) AS sample(
    project_code,
    risk_code,
    title,
    description,
    category,
    probability,
    impact,
    urgency,
    detectability,
    mitigation_effectiveness,
    owner_email,
    deadline_days,
    mitigation_cost
)
JOIN projects p
    ON p.project_code = sample.project_code
JOIN risk_owners o
    ON o.email = sample.owner_email;

-- ------------------------------------------------------------
-- ASSESSMENT HISTORY
-- ------------------------------------------------------------

INSERT INTO risk_assessments (
    risk_id,
    probability,
    impact,
    urgency,
    detectability,
    mitigation_effectiveness,
    assessment_reason,
    assessed_by
)
SELECT
    risk_id,
    probability,
    impact,
    urgency,
    detectability,
    mitigation_effectiveness,
    'Initial project risk assessment',
    'Project Risk Analyst'
FROM risks;

-- ------------------------------------------------------------
-- SAMPLE MITIGATION ACTIONS
-- ------------------------------------------------------------

INSERT INTO mitigation_actions (
    risk_id,
    action_title,
    action_description,
    assigned_to,
    estimated_cost,
    due_date
)
SELECT
    r.risk_id,
    'Implement security controls',
    'Strengthen access controls, monitoring, and incident response.',
    o.owner_id,
    50000,
    CURRENT_DATE + 4
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN risk_owners o
    ON o.email = 'security@example.com'
WHERE r.risk_code = 'R001';

INSERT INTO mitigation_actions (
    risk_id,
    action_title,
    action_description,
    assigned_to,
    estimated_cost,
    due_date
)
SELECT
    r.risk_id,
    'Validate migration recovery',
    'Conduct migration testing and recovery rehearsals.',
    o.owner_id,
    25000,
    CURRENT_DATE + 10
FROM risks r
JOIN risk_owners o
    ON o.email = 'cloud@example.com'
WHERE r.risk_code = 'R002';

COMMIT;

-- ============================================================
-- REPORTING AND OPERATIONAL QUERIES
-- ============================================================

-- 1. Complete ranked risk register.

SELECT *
FROM ranked_risks
ORDER BY
    CASE priority
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END,
    residual_score DESC,
    deadline ASC,
    risk_id ASC;

-- 2. Priority distribution.

SELECT
    project_code,
    priority,
    COUNT(*) AS risk_count
FROM ranked_risks
WHERE status <> 'CLOSED'
GROUP BY project_code, priority
ORDER BY project_code, priority;

-- 3. Category exposure.

SELECT
    project_code,
    category,
    COUNT(*) AS risk_count,
    ROUND(SUM(residual_score), 2) AS total_exposure,
    ROUND(AVG(residual_score), 2) AS average_exposure,
    MAX(residual_score) AS highest_exposure
FROM ranked_risks
WHERE status <> 'CLOSED'
GROUP BY project_code, category
ORDER BY total_exposure DESC;

-- 4. Risks requiring immediate management attention.

SELECT
    risk_code,
    title,
    priority,
    residual_score,
    owner_name,
    deadline
FROM ranked_risks
WHERE priority IN ('CRITICAL', 'HIGH')
  AND status <> 'CLOSED'
ORDER BY residual_score DESC;

-- 5. Overdue risks.

SELECT
    risk_code,
    title,
    owner_name,
    deadline,
    priority
FROM ranked_risks
WHERE overdue = TRUE
ORDER BY deadline;

-- 6. Risks grouped by ownership.

SELECT
    owner_name,
    department,
    COUNT(*) AS assigned_risks,
    ROUND(SUM(residual_score), 2) AS total_exposure
FROM ranked_risks
WHERE status <> 'CLOSED'
GROUP BY owner_name, department
ORDER BY total_exposure DESC;

-- 7. Mitigation progress.

SELECT
    r.risk_code,
    r.title,
    COUNT(a.action_id) AS total_actions,
    COUNT(a.action_id) FILTER (
        WHERE a.completed = TRUE
    ) AS completed_actions,
    COALESCE(SUM(a.estimated_cost), 0) AS estimated_cost,
    COALESCE(SUM(a.actual_cost), 0) AS actual_cost
FROM risks r
LEFT JOIN mitigation_actions a
    ON a.risk_id = r.risk_id
GROUP BY r.risk_id, r.risk_code, r.title
ORDER BY r.risk_code;

-- 8. Historical assessment comparison.

SELECT
    r.risk_code,
    a.assessment_id,
    a.assessed_at,
    calculate_residual_score(
        a.probability,
        a.impact,
        a.urgency,
        a.detectability,
        a.mitigation_effectiveness
    ) AS historical_score,
    classify_priority(
        calculate_residual_score(
            a.probability,
            a.impact,
            a.urgency,
            a.detectability,
            a.mitigation_effectiveness
        )
    ) AS historical_priority
FROM risk_assessments a
JOIN risks r
    ON r.risk_id = a.risk_id
ORDER BY r.risk_code, a.assessed_at DESC;

-- 9. Identify inactive risk owners.

SELECT
    o.owner_id,
    o.owner_name,
    COUNT(r.risk_id) AS assigned_open_risks
FROM risk_owners o
LEFT JOIN risks r
    ON r.owner_id = o.owner_id
   AND r.status <> 'CLOSED'
WHERE o.active = FALSE
GROUP BY o.owner_id, o.owner_name
HAVING COUNT(r.risk_id) > 0;

-- 10. Mitigation eligibility under a project budget.
-- This is a greedy priority-first allocation, not a global
-- cost-optimization algorithm.

WITH candidates AS (
    SELECT
        risk_id,
        risk_code,
        priority,
        residual_score,
        mitigation_cost
    FROM ranked_risks
    WHERE priority IN ('CRITICAL', 'HIGH')
      AND status <> 'CLOSED'
),
ordered_candidates AS (
    SELECT
        *,
        SUM(mitigation_cost) OVER (
            ORDER BY
                residual_score DESC,
                risk_id ASC
        ) AS cumulative_cost
    FROM candidates
)
SELECT
    risk_code,
    priority,
    residual_score,
    mitigation_cost,
    cumulative_cost,
    cumulative_cost <= 100000 AS funded
FROM ordered_candidates
ORDER BY residual_score DESC;

-- 11. CTE-based project risk dashboard.

WITH project_metrics AS (
    SELECT
        project_code,
        COUNT(*) AS total_risks,
        COUNT(*) FILTER (
            WHERE priority = 'CRITICAL'
        ) AS critical_risks,
        COUNT(*) FILTER (
            WHERE priority = 'HIGH'
        ) AS high_risks,
        ROUND(SUM(residual_score), 2) AS total_exposure,
        COUNT(*) FILTER (
            WHERE overdue = TRUE
        ) AS overdue_risks
    FROM ranked_risks
    WHERE status <> 'CLOSED'
    GROUP BY project_code
)
SELECT *
FROM project_metrics
ORDER BY total_exposure DESC;

-- 12. Risk assessment validation query.

SELECT
    risk_code,
    probability,
    impact,
    urgency,
    detectability,
    mitigation_effectiveness,
    residual_score
FROM ranked_risks
WHERE probability NOT BETWEEN 1 AND 5
   OR impact NOT BETWEEN 1 AND 5
   OR urgency NOT BETWEEN 1 AND 5
   OR detectability NOT BETWEEN 1 AND 5;

-- ============================================================
-- WORKFLOW PROCESSING
-- ============================================================

-- Change the application actor for audit attribution.
SET app.actor = 'Risk Management Administrator';

-- Assess and start mitigation for the cloud migration risk.
BEGIN;

UPDATE risks
SET status = 'MITIGATING'
WHERE risk_code = 'R002'
  AND status = 'ASSESSED';

COMMIT;

-- Update a risk assessment while preserving its history.
BEGIN;

WITH updated AS (
    UPDATE risks
    SET
        probability = 5,
        impact = 4,
        urgency = 5,
        detectability = 2,
        mitigation_effectiveness = 3
    WHERE risk_code = 'R003'
    RETURNING *
)
INSERT INTO risk_assessments (
    risk_id,
    probability,
    impact,
    urgency,
    detectability,
    mitigation_effectiveness,
    assessment_reason,
    assessed_by
)
SELECT
    risk_id,
    probability,
    impact,
    urgency,
    detectability,
    mitigation_effectiveness,
    'Probability and urgency increased after project review.',
    'Risk Management Administrator'
FROM updated;

COMMIT;

-- 13. Verify workflow audit records.

SELECT
    r.risk_code,
    h.previous_status,
    h.new_status,
    h.changed_by,
    h.reason,
    h.changed_at
FROM risk_status_history h
JOIN risks r
    ON r.risk_id = h.risk_id
ORDER BY h.changed_at DESC;

-- 14. Retrieve active mitigation actions.

SELECT
    r.risk_code,
    r.title,
    a.action_title,
    o.owner_name AS assigned_owner,
    a.due_date,
    a.estimated_cost,
    a.completed
FROM mitigation_actions a
JOIN risks r
    ON r.risk_id = a.risk_id
JOIN risk_owners o
    ON o.owner_id = a.assigned_to
WHERE a.completed = FALSE
ORDER BY a.due_date;

-- 15. Final risk register.

SELECT
    risk_code,
    title,
    residual_score,
    priority,
    owner_name,
    status,
    overdue
FROM ranked_risks
ORDER BY residual_score DESC, risk_code;
