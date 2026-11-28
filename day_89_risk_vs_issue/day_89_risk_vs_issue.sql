-- ============================================================
-- RISK VS ISSUE MANAGEMENT SYSTEM
-- PostgreSQL relational implementation
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS governance;

SET search_path TO governance, public;

-- ------------------------------------------------------------
-- ENUMERATED DOMAIN STATES
-- ------------------------------------------------------------

CREATE TYPE risk_status AS ENUM (
    'identified',
    'assessed',
    'mitigating',
    'accepted',
    'closed'
);

CREATE TYPE issue_status AS ENUM (
    'open',
    'in_progress',
    'blocked',
    'resolved',
    'closed'
);

CREATE TYPE severity_level AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE priority_level AS ENUM (
    'low',
    'medium',
    'high',
    'urgent'
);

CREATE TYPE risk_category AS ENUM (
    'operational',
    'financial',
    'technology',
    'cybersecurity',
    'compliance',
    'strategic',
    'environmental'
);

-- ------------------------------------------------------------
-- ORGANIZATIONAL STRUCTURE
-- ------------------------------------------------------------

CREATE TABLE departments (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_name VARCHAR(120) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    department_id BIGINT NOT NULL
        REFERENCES departments(department_id),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- RISK REGISTER
-- A risk is an uncertain future event or condition.
-- ------------------------------------------------------------

CREATE TABLE risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    category risk_category NOT NULL,

    probability SMALLINT NOT NULL
        CHECK (probability BETWEEN 1 AND 5),

    impact SMALLINT NOT NULL
        CHECK (impact BETWEEN 1 AND 5),

    exposure INTEGER GENERATED ALWAYS AS
        (probability * impact) STORED,

    owner_id BIGINT NOT NULL
        REFERENCES employees(employee_id),

    mitigation_plan TEXT,
    contingency_plan TEXT,

    status risk_status NOT NULL DEFAULT 'identified',

    identified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(title)) > 0),
    CHECK (length(trim(description)) > 0)
);

-- Severity is derived from probability multiplied by impact.
CREATE VIEW risk_assessments AS
SELECT
    r.risk_id,
    r.risk_code,
    r.title,
    r.probability,
    r.impact,
    r.exposure,
    CASE
        WHEN r.exposure >= 20 THEN 'critical'
        WHEN r.exposure >= 12 THEN 'high'
        WHEN r.exposure >= 6 THEN 'medium'
        ELSE 'low'
    END AS severity,
    r.category,
    r.status,
    r.owner_id
FROM risks r;

-- ------------------------------------------------------------
-- RISK ASSESSMENT HISTORY
-- Preserves historical assessments rather than overwriting them.
-- ------------------------------------------------------------

CREATE TABLE risk_assessment_history (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    probability SMALLINT NOT NULL
        CHECK (probability BETWEEN 1 AND 5),

    impact SMALLINT NOT NULL
        CHECK (impact BETWEEN 1 AND 5),

    exposure INTEGER GENERATED ALWAYS AS
        (probability * impact) STORED,

    assessed_by BIGINT NOT NULL
        REFERENCES employees(employee_id),

    assessment_notes TEXT,

    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- ISSUE REGISTER
-- An issue is an existing problem or realized condition.
-- ------------------------------------------------------------

CREATE TABLE issues (
    issue_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    issue_code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    severity severity_level NOT NULL,
    priority priority_level NOT NULL,

    owner_id BIGINT NOT NULL
        REFERENCES employees(employee_id),

    source_risk_id BIGINT
        REFERENCES risks(risk_id),

    status issue_status NOT NULL DEFAULT 'open',

    resolution TEXT,

    reported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,

    CHECK (length(trim(title)) > 0),
    CHECK (length(trim(description)) > 0),

    CHECK (
        (status IN ('resolved', 'closed') AND resolved_at IS NOT NULL)
        OR
        (status NOT IN ('resolved', 'closed') AND resolved_at IS NULL)
    )
);

-- ------------------------------------------------------------
-- RISK MITIGATION ACTIONS
-- ------------------------------------------------------------

CREATE TABLE mitigation_actions (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    action_title VARCHAR(200) NOT NULL,
    action_description TEXT NOT NULL,

    assigned_to BIGINT NOT NULL
        REFERENCES employees(employee_id),

    due_date DATE,
    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(action_title)) > 0),

    CHECK (
        completed_at IS NULL
        OR completed_at >= created_at
    )
);

-- ------------------------------------------------------------
-- ISSUE RESOLUTION ACTIVITIES
-- ------------------------------------------------------------

CREATE TABLE issue_activities (
    activity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    issue_id BIGINT NOT NULL
        REFERENCES issues(issue_id),

    performed_by BIGINT NOT NULL
        REFERENCES employees(employee_id),

    activity_description TEXT NOT NULL,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- GOVERNANCE AUDIT LOG
-- ------------------------------------------------------------

CREATE TABLE governance_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    entity_type VARCHAR(20) NOT NULL
        CHECK (entity_type IN ('risk', 'issue')),

    entity_id BIGINT NOT NULL,

    action VARCHAR(60) NOT NULL,

    old_state TEXT,
    new_state TEXT,

    performed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------

CREATE INDEX idx_risks_exposure
    ON risks(exposure DESC)
    WHERE status <> 'closed';

CREATE INDEX idx_risks_owner_status
    ON risks(owner_id, status);

CREATE INDEX idx_risks_category
    ON risks(category);

CREATE INDEX idx_risk_history_risk_date
    ON risk_assessment_history(risk_id, assessed_at DESC);

CREATE INDEX idx_issues_status_priority
    ON issues(status, priority);

CREATE INDEX idx_issues_owner
    ON issues(owner_id, status);

CREATE INDEX idx_issues_source_risk
    ON issues(source_risk_id)
    WHERE source_risk_id IS NOT NULL;

CREATE INDEX idx_mitigation_due_date
    ON mitigation_actions(due_date)
    WHERE completed_at IS NULL;

-- ------------------------------------------------------------
-- TRIGGER: AUTOMATIC UPDATED_AT
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_risk_updated_at
BEFORE UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();

-- ------------------------------------------------------------
-- TRIGGER: AUDIT RISK CHANGES
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION audit_risk_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO governance_audit (
            entity_type,
            entity_id,
            action,
            new_state
        )
        VALUES (
            'risk',
            NEW.risk_id,
            'CREATED',
            NEW.status::TEXT
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO governance_audit (
            entity_type,
            entity_id,
            action,
            old_state,
            new_state
        )
        VALUES (
            'risk',
            NEW.risk_id,
            'UPDATED',
            ROW(
                OLD.probability,
                OLD.impact,
                OLD.status
            )::TEXT,
            ROW(
                NEW.probability,
                NEW.impact,
                NEW.status
            )::TEXT
        );

        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_audit_risk
AFTER INSERT OR UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION audit_risk_changes();

-- ------------------------------------------------------------
-- TRIGGER: AUDIT ISSUE CHANGES
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION audit_issue_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO governance_audit (
            entity_type,
            entity_id,
            action,
            new_state
        )
        VALUES (
            'issue',
            NEW.issue_id,
            'CREATED',
            NEW.status::TEXT
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO governance_audit (
            entity_type,
            entity_id,
            action,
            old_state,
            new_state
        )
        VALUES (
            'issue',
            NEW.issue_id,
            'UPDATED',
            OLD.status::TEXT,
            NEW.status::TEXT
        );

        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_audit_issue
AFTER INSERT OR UPDATE ON issues
FOR EACH ROW
EXECUTE FUNCTION audit_issue_changes();

-- ------------------------------------------------------------
-- FUNCTION: SEVERITY CALCULATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_severity(
    p_probability SMALLINT,
    p_impact SMALLINT
)
RETURNS severity_level
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_exposure INTEGER;
BEGIN
    IF p_probability NOT BETWEEN 1 AND 5
       OR p_impact NOT BETWEEN 1 AND 5 THEN
        RAISE EXCEPTION
            'Probability and impact must be between 1 and 5';
    END IF;

    v_exposure := p_probability * p_impact;

    RETURN CASE
        WHEN v_exposure >= 20 THEN 'critical'::severity_level
        WHEN v_exposure >= 12 THEN 'high'::severity_level
        WHEN v_exposure >= 6 THEN 'medium'::severity_level
        ELSE 'low'::severity_level
    END;
END;
$$;

-- ------------------------------------------------------------
-- FUNCTION: PRIORITY MAPPING
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION severity_to_priority(
    p_severity severity_level
)
RETURNS priority_level
LANGUAGE sql
IMMUTABLE
STRICT
AS $$
    SELECT CASE p_severity
        WHEN 'critical' THEN 'urgent'::priority_level
        WHEN 'high' THEN 'high'::priority_level
        WHEN 'medium' THEN 'medium'::priority_level
        ELSE 'low'::priority_level
    END;
$$;

-- ------------------------------------------------------------
-- FUNCTION: CONVERT MATERIALIZED RISK INTO ISSUE
-- The risk record is retained for historical traceability.
-- The new issue receives its own independent identifier.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION materialize_risk(
    p_risk_id BIGINT,
    p_issue_code VARCHAR(30),
    p_issue_title VARCHAR(200),
    p_issue_description TEXT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_risk RECORD;
    v_issue_id BIGINT;
    v_severity severity_level;
BEGIN
    SELECT
        r.risk_id,
        r.owner_id,
        r.probability,
        r.impact
    INTO v_risk
    FROM risks r
    WHERE r.risk_id = p_risk_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk % does not exist', p_risk_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM issues
        WHERE issue_code = p_issue_code
    ) THEN
        RAISE EXCEPTION 'Issue code already exists';
    END IF;

    IF p_issue_title IS NULL
       OR length(trim(p_issue_title)) = 0 THEN
        RAISE EXCEPTION 'Issue title is required';
    END IF;

    IF p_issue_description IS NULL
       OR length(trim(p_issue_description)) = 0 THEN
        RAISE EXCEPTION 'Issue description is required';
    END IF;

    v_severity := calculate_severity(
        v_risk.probability,
        v_risk.impact
    );

    INSERT INTO issues (
        issue_code,
        title,
        description,
        severity,
        priority,
        owner_id,
        source_risk_id
    )
    VALUES (
        p_issue_code,
        p_issue_title,
        p_issue_description,
        v_severity,
        severity_to_priority(v_severity),
        v_risk.owner_id,
        p_risk_id
    )
    RETURNING issue_id INTO v_issue_id;

    RETURN v_issue_id;
END;
$$;

-- ------------------------------------------------------------
-- PROCEDURE: RECORD RISK ASSESSMENT
-- Preserves every assessment in historical records.
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE record_risk_assessment(
    p_risk_id BIGINT,
    p_probability SMALLINT,
    p_impact SMALLINT,
    p_assessed_by BIGINT,
    p_notes TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_probability NOT BETWEEN 1 AND 5
       OR p_impact NOT BETWEEN 1 AND 5 THEN
        RAISE EXCEPTION 'Invalid probability or impact';
    END IF;

    UPDATE risks
    SET
        probability = p_probability,
        impact = p_impact,
        status = 'assessed'
    WHERE risk_id = p_risk_id
      AND status <> 'closed';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Risk not found or risk is already closed';
    END IF;

    INSERT INTO risk_assessment_history (
        risk_id,
        probability,
        impact,
        assessed_by,
        assessment_notes
    )
    VALUES (
        p_risk_id,
        p_probability,
        p_impact,
        p_assessed_by,
        p_notes
    );
END;
$$;

-- ------------------------------------------------------------
-- VIEW: OPEN ISSUE REGISTER
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW open_issue_register AS
SELECT
    i.issue_id,
    i.issue_code,
    i.title,
    i.severity,
    i.priority,
    i.status,
    e.employee_name AS owner,
    d.department_name,
    i.source_risk_id,
    i.reported_at
FROM issues i
JOIN employees e
    ON e.employee_id = i.owner_id
JOIN departments d
    ON d.department_id = e.department_id
WHERE i.status NOT IN ('resolved', 'closed');

-- ------------------------------------------------------------
-- VIEW: RISK AND ISSUE TRACEABILITY
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW risk_issue_traceability AS
SELECT
    r.risk_id,
    r.risk_code,
    r.title AS risk_title,
    r.status AS risk_status,
    i.issue_id,
    i.issue_code,
    i.title AS issue_title,
    i.status AS issue_status,
    i.severity
FROM risks r
LEFT JOIN issues i
    ON i.source_risk_id = r.risk_id;

-- ------------------------------------------------------------
-- SAMPLE DEPARTMENTS
-- ------------------------------------------------------------

INSERT INTO departments (department_name)
VALUES
    ('Infrastructure'),
    ('Cybersecurity'),
    ('Database Operations'),
    ('Finance'),
    ('Compliance');

-- ------------------------------------------------------------
-- SAMPLE EMPLOYEES
-- ------------------------------------------------------------

INSERT INTO employees (
    employee_name,
    email,
    department_id
)
SELECT
    v.employee_name,
    v.email,
    d.department_id
FROM (
    VALUES
        ('Amit Sharma', 'amit@example.org', 'Infrastructure'),
        ('Neha Verma', 'neha@example.org', 'Cybersecurity'),
        ('Rahul Singh', 'rahul@example.org', 'Database Operations'),
        ('Priya Gupta', 'priya@example.org', 'Finance'),
        ('Arjun Mehta', 'arjun@example.org', 'Compliance')
) AS v(employee_name, email, department_name)
JOIN departments d
    ON d.department_name = v.department_name;

-- ------------------------------------------------------------
-- SAMPLE RISKS
-- ------------------------------------------------------------

INSERT INTO risks (
    risk_code,
    title,
    description,
    category,
    probability,
    impact,
    owner_id,
    mitigation_plan,
    contingency_plan
)
SELECT
    v.risk_code,
    v.title,
    v.description,
    v.category::risk_category,
    v.probability,
    v.impact,
    e.employee_id,
    v.mitigation_plan,
    v.contingency_plan
FROM (
    VALUES
    (
        'RISK-001',
        'Cloud region outage',
        'The primary cloud region may become unavailable.',
        'technology',
        3::SMALLINT,
        5::SMALLINT,
        'amit@example.org',
        'Configure multi-region redundancy.',
        'Activate the secondary region.'
    ),
    (
        'RISK-002',
        'Credential compromise',
        'An attacker may obtain privileged credentials.',
        'cybersecurity',
        4::SMALLINT,
        5::SMALLINT,
        'neha@example.org',
        'Enforce MFA and privileged access management.',
        'Revoke credentials and isolate affected systems.'
    ),
    (
        'RISK-003',
        'Budget overrun',
        'Project expenditure may exceed the approved budget.',
        'financial',
        3::SMALLINT,
        3::SMALLINT,
        'priya@example.org',
        'Monitor monthly expenditure.',
        'Reallocate approved contingency funds.'
    ),
    (
        'RISK-004',
        'Regulatory reporting delay',
        'Required compliance reporting may miss its deadline.',
        'compliance',
        2::SMALLINT,
        4::SMALLINT,
        'arjun@example.org',
        'Automate reporting and introduce deadline alerts.',
        'Escalate to the compliance head.'
    )
) AS v(
    risk_code,
    title,
    description,
    category,
    probability,
    impact,
    email,
    mitigation_plan,
    contingency_plan
)
JOIN employees e
    ON e.email = v.email;

-- ------------------------------------------------------------
-- SAMPLE RISK ASSESSMENT HISTORY
-- ------------------------------------------------------------

INSERT INTO risk_assessment_history (
    risk_id,
    probability,
    impact,
    assessed_by,
    assessment_notes
)
SELECT
    r.risk_id,
    r.probability,
    r.impact,
    e.employee_id,
    'Initial management assessment'
FROM risks r
JOIN employees e
    ON e.email = 'amit@example.org'
WHERE r.risk_code = 'RISK-001';

-- ------------------------------------------------------------
-- SAMPLE ISSUES
-- ------------------------------------------------------------

INSERT INTO issues (
    issue_code,
    title,
    description,
    severity,
    priority,
    owner_id,
    source_risk_id
)
SELECT
    'ISSUE-001',
    'Production database outage',
    'The production application cannot connect to PostgreSQL.',
    'critical',
    'urgent',
    e.employee_id,
    NULL
FROM employees e
WHERE e.email = 'rahul@example.org';

INSERT INTO issues (
    issue_code,
    title,
    description,
    severity,
    priority,
    owner_id,
    source_risk_id
)
SELECT
    'ISSUE-002',
    'Unauthorized login detected',
    'Security monitoring confirmed unauthorized administrator access.',
    'critical',
    'urgent',
    e.employee_id,
    r.risk_id
FROM employees e
JOIN risks r
    ON r.risk_code = 'RISK-002'
WHERE e.email = 'neha@example.org';

-- ------------------------------------------------------------
-- SAMPLE ISSUE STATE TRANSITIONS
-- ------------------------------------------------------------

UPDATE issues
SET status = 'in_progress'
WHERE issue_code = 'ISSUE-001';

UPDATE issues
SET
    status = 'resolved',
    resolution = 'Database service restored and transaction tests passed.',
    resolved_at = CURRENT_TIMESTAMP
WHERE issue_code = 'ISSUE-001';

UPDATE issues
SET status = 'closed'
WHERE issue_code = 'ISSUE-001';

UPDATE issues
SET status = 'in_progress'
WHERE issue_code = 'ISSUE-002';

-- ------------------------------------------------------------
-- SAMPLE MITIGATION ACTIONS
-- ------------------------------------------------------------

INSERT INTO mitigation_actions (
    risk_id,
    action_title,
    action_description,
    assigned_to,
    due_date
)
SELECT
    r.risk_id,
    'Implement multi-region failover',
    'Configure and test secondary cloud region activation.',
    e.employee_id,
    CURRENT_DATE + 30
FROM risks r
JOIN employees e
    ON e.email = 'amit@example.org'
WHERE r.risk_code = 'RISK-001';

-- ------------------------------------------------------------
-- SAMPLE ISSUE ACTIVITY
-- ------------------------------------------------------------

INSERT INTO issue_activities (
    issue_id,
    performed_by,
    activity_description
)
SELECT
    i.issue_id,
    e.employee_id,
    'Reviewed security alerts and initiated incident containment.'
FROM issues i
JOIN employees e
    ON e.email = 'neha@example.org'
WHERE i.issue_code = 'ISSUE-002';

COMMIT;

-- ============================================================
-- MANAGEMENT QUERIES
-- ============================================================

-- 1. RETRIEVE THE RISK REGISTER

SELECT
    risk_code,
    title,
    probability,
    impact,
    exposure,
    severity,
    status
FROM risk_assessments
ORDER BY exposure DESC;

-- 2. RETRIEVE THE ISSUE REGISTER

SELECT
    issue_code,
    title,
    severity,
    priority,
    status,
    owner
FROM open_issue_register
ORDER BY
    CASE priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END;

-- 3. DISTINGUISH RISKS FROM EXISTING ISSUES

SELECT
    'RISK' AS record_type,
    risk_code AS reference,
    title,
    status::TEXT AS state
FROM risks
WHERE status <> 'closed'

UNION ALL

SELECT
    'ISSUE',
    issue_code,
    title,
    status::TEXT
FROM issues
WHERE status NOT IN ('resolved', 'closed');

-- 4. IDENTIFY CRITICAL RISKS

SELECT *
FROM risk_assessments
WHERE severity = 'critical'
  AND status <> 'closed'
ORDER BY exposure DESC;

-- 5. CALCULATE RISK EXPOSURE BY CATEGORY

SELECT
    category,
    COUNT(*) AS total_risks,
    ROUND(AVG(exposure), 2) AS average_exposure,
    MAX(exposure) AS highest_exposure
FROM risks
WHERE status <> 'closed'
GROUP BY category
ORDER BY average_exposure DESC;

-- 6. ISSUE BACKLOG BY PRIORITY

SELECT
    priority,
    COUNT(*) AS issue_count
FROM issues
WHERE status NOT IN ('resolved', 'closed')
GROUP BY priority
ORDER BY
    CASE priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END;

-- 7. RISK-TO-ISSUE TRACEABILITY

SELECT *
FROM risk_issue_traceability
ORDER BY risk_id, issue_id;

-- 8. IDENTIFY RISKS THAT HAVE MATERIALIZED

SELECT
    r.risk_code,
    r.title AS original_risk,
    i.issue_code,
    i.title AS realized_issue,
    i.status AS issue_status
FROM risks r
JOIN issues i
    ON i.source_risk_id = r.risk_id
ORDER BY r.risk_id;

-- 9. FIND RISKS WITHOUT MITIGATION ACTIONS

SELECT
    r.risk_code,
    r.title,
    r.exposure,
    r.status
FROM risks r
LEFT JOIN mitigation_actions m
    ON m.risk_id = r.risk_id
WHERE r.status <> 'closed'
GROUP BY
    r.risk_id,
    r.risk_code,
    r.title,
    r.exposure,
    r.status
HAVING COUNT(m.action_id) = 0;

-- 10. DEPARTMENT-WISE ISSUE ANALYSIS

SELECT
    d.department_name,
    COUNT(i.issue_id) AS total_issues,
    COUNT(i.issue_id) FILTER (
        WHERE i.status NOT IN ('resolved', 'closed')
    ) AS unresolved_issues,
    COUNT(i.issue_id) FILTER (
        WHERE i.priority = 'urgent'
          AND i.status NOT IN ('resolved', 'closed')
    ) AS urgent_issues
FROM departments d
LEFT JOIN employees e
    ON e.department_id = d.department_id
LEFT JOIN issues i
    ON i.owner_id = e.employee_id
GROUP BY d.department_id, d.department_name
ORDER BY unresolved_issues DESC;

-- 11. HISTORICAL RISK ASSESSMENTS

SELECT
    r.risk_code,
    r.title,
    h.probability,
    h.impact,
    h.exposure,
    h.assessed_at,
    e.employee_name AS assessor
FROM risk_assessment_history h
JOIN risks r
    ON r.risk_id = h.risk_id
JOIN employees e
    ON e.employee_id = h.assessed_by
ORDER BY h.assessed_at DESC;

-- 12. RISK STATUS DISTRIBUTION

SELECT
    status,
    COUNT(*) AS total
FROM risks
GROUP BY status
ORDER BY status;

-- 13. ISSUE STATUS DISTRIBUTION

SELECT
    status,
    COUNT(*) AS total
FROM issues
GROUP BY status
ORDER BY status;

-- 14. MANAGEMENT DASHBOARD

SELECT
    (SELECT COUNT(*) FROM risks) AS total_risks,

    (
        SELECT COUNT(*)
        FROM risks
        WHERE status <> 'closed'
    ) AS active_risks,

    (
        SELECT COUNT(*)
        FROM risk_assessments
        WHERE severity = 'critical'
          AND status <> 'closed'
    ) AS critical_risks,

    (SELECT COUNT(*) FROM issues) AS total_issues,

    (
        SELECT COUNT(*)
        FROM issues
        WHERE status NOT IN ('resolved', 'closed')
    ) AS unresolved_issues,

    (
        SELECT COUNT(*)
        FROM issues
        WHERE priority = 'urgent'
          AND status NOT IN ('resolved', 'closed')
    ) AS urgent_issues;

-- 15. VALIDATE ISSUE-TO-RISK REFERENCES

SELECT
    i.issue_code,
    i.source_risk_id
FROM issues i
LEFT JOIN risks r
    ON r.risk_id = i.source_risk_id
WHERE i.source_risk_id IS NOT NULL
  AND r.risk_id IS NULL;

-- An empty result indicates valid references.

-- ============================================================
-- TRANSACTIONAL WORKFLOW EXAMPLE
-- ============================================================

-- Record an updated risk assessment atomically.
-- The risk update and historical record are committed together.

BEGIN;

CALL record_risk_assessment(
    (
        SELECT risk_id
        FROM risks
        WHERE risk_code = 'RISK-003'
    ),
    4,
    4,
    (
        SELECT employee_id
        FROM employees
        WHERE email = 'priya@example.org'
    ),
    'Financial exposure increased after the quarterly review.'
);

COMMIT;

-- ============================================================
-- MATERIALIZATION WORKFLOW
-- ============================================================

-- Demonstrates conversion of a risk into a separately tracked issue.
-- The operation uses a function and can be rolled back as a unit.

BEGIN;

SELECT materialize_risk(
    (
        SELECT risk_id
        FROM risks
        WHERE risk_code = 'RISK-003'
    ),
    'ISSUE-003',
    'Project budget exceeded',
    'Actual expenditure has exceeded the approved project budget.'
) AS newly_created_issue_id;

COMMIT;

-- ============================================================
-- TRANSACTIONAL FAILURE HANDLING EXAMPLE
-- ============================================================

-- The following block deliberately attempts invalid input.
-- The exception is caught and the subtransaction is rolled back.

DO $$
BEGIN
    BEGIN
        INSERT INTO risks (
            risk_code,
            title,
            description,
            category,
            probability,
            impact,
            owner_id
        )
        VALUES (
            'RISK-INVALID',
            'Invalid probability',
            'This record must fail validation.',
            'operational',
            9,
            5,
            (
                SELECT employee_id
                FROM employees
                WHERE email = 'amit@example.org'
            )
        );

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'Expected validation failure: probability is outside the permitted range.';
    END;
END;
$$;

-- ============================================================
-- AUDIT REPORT
-- ============================================================

SELECT
    audit_id,
    entity_type,
    entity_id,
    action,
    old_state,
    new_state,
    performed_at
FROM governance_audit
ORDER BY performed_at DESC;

-- ============================================================
-- PERFORMANCE INSPECTION
-- ============================================================

EXPLAIN ANALYZE
SELECT
    risk_id,
    risk_code,
    title,
    exposure
FROM risks
WHERE status <> 'closed'
ORDER BY exposure DESC
LIMIT 10;

-- ============================================================
-- END OF RISK VS ISSUE MANAGEMENT SYSTEM
-- ============================================================
