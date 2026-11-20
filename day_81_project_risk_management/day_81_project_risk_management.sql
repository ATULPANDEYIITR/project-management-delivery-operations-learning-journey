/*
===============================================================================
PROJECT RISK MANAGEMENT
PostgreSQL 14+

Relational implementation of project risk management.

Includes:
- Projects
- Project members
- Risk categories
- Risk identification
- Probability and impact assessments
- Inherent and residual risk exposure
- Risk owners
- Risk response strategies
- Response plans
- Risk history
- Escalations
- Risk closure
- Risk monitoring
- Risk policies
- Portfolio reporting
- Risk prioritization
- Risk eligibility evaluation
- Transactions and integrity controls

Execution:
Run this complete script in a PostgreSQL database.

The script creates a dedicated project_risk schema.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS project_risk;

SET search_path TO project_risk, public;

-- ---------------------------------------------------------------------------
-- ENUM TYPES
-- ---------------------------------------------------------------------------

CREATE TYPE risk_status AS ENUM (
    'IDENTIFIED',
    'ASSESSED',
    'RESPONSE_PLANNED',
    'MONITORING',
    'ESCALATED',
    'CLOSED'
);

CREATE TYPE risk_level AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);

CREATE TYPE response_strategy AS ENUM (
    'AVOID',
    'MITIGATE',
    'TRANSFER',
    'ACCEPT',
    'EXPLOIT',
    'ENHANCE',
    'SHARE'
);

CREATE TYPE risk_event AS ENUM (
    'IDENTIFIED',
    'ASSESSED',
    'RESPONSE_ASSIGNED',
    'MONITORED',
    'ESCALATED',
    'CLOSED'
);

-- ---------------------------------------------------------------------------
-- PROJECTS
-- ---------------------------------------------------------------------------

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    approved_budget NUMERIC(15,2) NOT NULL DEFAULT 0,
    planned_start DATE,
    planned_end DATE,
    project_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_project_budget
        CHECK (approved_budget >= 0),

    CONSTRAINT valid_project_dates
        CHECK (
            planned_end IS NULL
            OR planned_start IS NULL
            OR planned_end >= planned_start
        ),

    CONSTRAINT valid_project_status
        CHECK (
            project_status IN (
                'PLANNED',
                'ACTIVE',
                'ON_HOLD',
                'COMPLETED',
                'CANCELLED'
            )
        )
);

-- ---------------------------------------------------------------------------
-- USERS AND PROJECT MEMBERS
-- ---------------------------------------------------------------------------

CREATE TABLE project_members (
    member_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_code VARCHAR(40) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    role_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE project_membership (
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    member_id BIGINT NOT NULL REFERENCES project_members(member_id),
    membership_role VARCHAR(50) NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (project_id, member_id),

    CONSTRAINT valid_membership_role
        CHECK (
            membership_role IN (
                'PROJECT_MANAGER',
                'RISK_OWNER',
                'TEAM_MEMBER',
                'SPONSOR',
                'OBSERVER'
            )
        )
);

-- ---------------------------------------------------------------------------
-- RISK CATEGORIES
-- ---------------------------------------------------------------------------

CREATE TABLE risk_categories (
    category_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_code VARCHAR(30) NOT NULL UNIQUE,
    category_name VARCHAR(80) NOT NULL UNIQUE,
    description TEXT
);

-- ---------------------------------------------------------------------------
-- RISK REGISTER
-- ---------------------------------------------------------------------------

CREATE TABLE risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    risk_code VARCHAR(40) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    category_id SMALLINT NOT NULL
        REFERENCES risk_categories(category_id),

    owner_id BIGINT NOT NULL
        REFERENCES project_members(member_id),

    probability SMALLINT NOT NULL,
    impact SMALLINT NOT NULL,

    inherent_score SMALLINT GENERATED ALWAYS AS (
        probability * impact
    ) STORED,

    residual_probability SMALLINT,
    residual_impact SMALLINT,

    residual_score SMALLINT GENERATED ALWAYS AS (
        COALESCE(residual_probability, probability)
        *
        COALESCE(residual_impact, impact)
    ) STORED,

    status risk_status NOT NULL DEFAULT 'IDENTIFIED',

    identified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    closed_at TIMESTAMPTZ,
    closure_reason TEXT,

    version INTEGER NOT NULL DEFAULT 1,

    UNIQUE (project_id, risk_code),

    CONSTRAINT valid_probability
        CHECK (probability BETWEEN 1 AND 5),

    CONSTRAINT valid_impact
        CHECK (impact BETWEEN 1 AND 5),

    CONSTRAINT valid_residual_probability
        CHECK (
            residual_probability IS NULL
            OR residual_probability BETWEEN 1 AND 5
        ),

    CONSTRAINT valid_residual_impact
        CHECK (
            residual_impact IS NULL
            OR residual_impact BETWEEN 1 AND 5
        ),

    CONSTRAINT residual_values_consistent
        CHECK (
            (residual_probability IS NULL AND residual_impact IS NULL)
            OR
            (residual_probability IS NOT NULL AND residual_impact IS NOT NULL)
        ),

    CONSTRAINT valid_closure_data
        CHECK (
            (status = 'CLOSED'
                AND closed_at IS NOT NULL
                AND closure_reason IS NOT NULL)
            OR
            (status <> 'CLOSED'
                AND closed_at IS NULL
                AND closure_reason IS NULL)
        )
);

-- ---------------------------------------------------------------------------
-- RESPONSE PLANS
-- ---------------------------------------------------------------------------

CREATE TABLE risk_responses (
    response_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    strategy response_strategy NOT NULL,
    action_description TEXT NOT NULL,

    response_owner_id BIGINT NOT NULL
        REFERENCES project_members(member_id),

    response_cost NUMERIC(15,2) NOT NULL DEFAULT 0,
    contingency_reserve NUMERIC(15,2) NOT NULL DEFAULT 0,

    planned_start DATE,
    target_completion DATE,

    implementation_status VARCHAR(20) NOT NULL DEFAULT 'PLANNED',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT nonnegative_response_cost
        CHECK (response_cost >= 0),

    CONSTRAINT nonnegative_contingency
        CHECK (contingency_reserve >= 0),

    CONSTRAINT valid_response_dates
        CHECK (
            target_completion IS NULL
            OR planned_start IS NULL
            OR target_completion >= planned_start
        ),

    CONSTRAINT valid_implementation_status
        CHECK (
            implementation_status IN (
                'PLANNED',
                'IN_PROGRESS',
                'COMPLETED',
                'CANCELLED'
            )
        )
);

-- ---------------------------------------------------------------------------
-- RISK ASSESSMENT HISTORY
-- ---------------------------------------------------------------------------

CREATE TABLE risk_assessments (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL REFERENCES risks(risk_id),

    probability SMALLINT NOT NULL,
    impact SMALLINT NOT NULL,

    exposure_score SMALLINT GENERATED ALWAYS AS (
        probability * impact
    ) STORED,

    assessment_type VARCHAR(15) NOT NULL,

    assessed_by BIGINT NOT NULL
        REFERENCES project_members(member_id),

    assessment_notes TEXT,

    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_assessment_probability
        CHECK (probability BETWEEN 1 AND 5),

    CONSTRAINT valid_assessment_impact
        CHECK (impact BETWEEN 1 AND 5),

    CONSTRAINT valid_assessment_type
        CHECK (
            assessment_type IN (
                'INHERENT',
                'RESIDUAL'
            )
        )
);

-- ---------------------------------------------------------------------------
-- RISK HISTORY
-- ---------------------------------------------------------------------------

CREATE TABLE risk_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL REFERENCES risks(risk_id),

    event_type risk_event NOT NULL,
    event_details TEXT NOT NULL,

    performed_by BIGINT REFERENCES project_members(member_id),

    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- ESCALATIONS
-- ---------------------------------------------------------------------------

CREATE TABLE risk_escalations (
    escalation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL REFERENCES risks(risk_id),

    escalated_by BIGINT NOT NULL
        REFERENCES project_members(member_id),

    escalated_to BIGINT NOT NULL
        REFERENCES project_members(member_id),

    reason TEXT NOT NULL,

    escalation_status VARCHAR(20) NOT NULL DEFAULT 'OPEN',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,

    CONSTRAINT valid_escalation_status
        CHECK (
            escalation_status IN (
                'OPEN',
                'IN_PROGRESS',
                'RESOLVED',
                'REJECTED'
            )
        ),

    CONSTRAINT valid_escalation_resolution
        CHECK (
            (escalation_status IN ('RESOLVED', 'REJECTED')
                AND resolved_at IS NOT NULL)
            OR
            (escalation_status IN ('OPEN', 'IN_PROGRESS')
                AND resolved_at IS NULL)
        )
);

-- ---------------------------------------------------------------------------
-- RISK GOVERNANCE POLICIES
-- ---------------------------------------------------------------------------

CREATE TABLE risk_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL REFERENCES projects(project_id),

    policy_name VARCHAR(150) NOT NULL,

    low_max SMALLINT NOT NULL DEFAULT 5,
    medium_max SMALLINT NOT NULL DEFAULT 11,
    high_max SMALLINT NOT NULL DEFAULT 19,

    minimum_review_score SMALLINT NOT NULL DEFAULT 12,

    require_response_for_high BOOLEAN NOT NULL DEFAULT TRUE,
    require_active_owner BOOLEAN NOT NULL DEFAULT TRUE,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (project_id, policy_name),

    CONSTRAINT valid_policy_thresholds
        CHECK (
            low_max >= 1
            AND medium_max > low_max
            AND high_max > medium_max
            AND high_max <= 24
            AND minimum_review_score BETWEEN 1 AND 25
        )
);

-- ---------------------------------------------------------------------------
-- INDEXES
-- ---------------------------------------------------------------------------

CREATE INDEX idx_risks_project_status
    ON risks(project_id, status);

CREATE INDEX idx_risks_priority
    ON risks(project_id, residual_score DESC)
    WHERE status <> 'CLOSED';

CREATE INDEX idx_risks_owner
    ON risks(owner_id, status);

CREATE INDEX idx_risks_category
    ON risks(category_id, project_id);

CREATE INDEX idx_risks_due_date
    ON risks(due_date)
    WHERE status <> 'CLOSED';

CREATE INDEX idx_assessments_risk_date
    ON risk_assessments(risk_id, assessed_at DESC);

CREATE INDEX idx_history_risk_time
    ON risk_history(risk_id, event_time DESC);

CREATE INDEX idx_escalations_open
    ON risk_escalations(risk_id, created_at DESC)
    WHERE escalation_status IN ('OPEN', 'IN_PROGRESS');

CREATE INDEX idx_responses_status
    ON risk_responses(implementation_status, target_completion);

-- ---------------------------------------------------------------------------
-- RISK CLASSIFICATION FUNCTION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION classify_risk(
    p_score INTEGER
)
RETURNS risk_level
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT CASE
        WHEN p_score >= 20 THEN 'CRITICAL'::risk_level
        WHEN p_score >= 12 THEN 'HIGH'::risk_level
        WHEN p_score >= 6 THEN 'MEDIUM'::risk_level
        ELSE 'LOW'::risk_level
    END;
$$;

-- ---------------------------------------------------------------------------
-- RISK HISTORY TRIGGER
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION log_risk_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN

        INSERT INTO risk_history (
            risk_id,
            event_type,
            event_details
        )
        VALUES (
            NEW.risk_id,
            'IDENTIFIED',
            'Risk entered into the project risk register.'
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN

        IF OLD.status IS DISTINCT FROM NEW.status THEN

            IF NEW.status = 'ASSESSED' THEN
                INSERT INTO risk_history (
                    risk_id,
                    event_type,
                    event_details
                )
                VALUES (
                    NEW.risk_id,
                    'ASSESSED',
                    'Risk assessment completed.'
                );

            ELSIF NEW.status = 'RESPONSE_PLANNED' THEN
                INSERT INTO risk_history (
                    risk_id,
                    event_type,
                    event_details
                )
                VALUES (
                    NEW.risk_id,
                    'RESPONSE_ASSIGNED',
                    'Risk response plan assigned.'
                );

            ELSIF NEW.status = 'MONITORING' THEN
                INSERT INTO risk_history (
                    risk_id,
                    event_type,
                    event_details
                )
                VALUES (
                    NEW.risk_id,
                    'MONITORED',
                    'Risk entered monitoring state.'
                );

            ELSIF NEW.status = 'ESCALATED' THEN
                INSERT INTO risk_history (
                    risk_id,
                    event_type,
                    event_details
                )
                VALUES (
                    NEW.risk_id,
                    'ESCALATED',
                    'Risk escalated for management attention.'
                );

            ELSIF NEW.status = 'CLOSED' THEN
                INSERT INTO risk_history (
                    risk_id,
                    event_type,
                    event_details
                )
                VALUES (
                    NEW.risk_id,
                    'CLOSED',
                    NEW.closure_reason
                );
            END IF;
        END IF;

        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_risk_history
AFTER INSERT OR UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION log_risk_changes();

-- ---------------------------------------------------------------------------
-- RISK STATE AND VERSION VALIDATION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_risk_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'CLOSED' AND NEW.status <> 'CLOSED' THEN
        RAISE EXCEPTION 'Closed risks cannot be reopened through this operation.';
    END IF;

    IF OLD.status = 'CLOSED' AND (
        NEW.probability <> OLD.probability
        OR NEW.impact <> OLD.impact
        OR NEW.residual_probability IS DISTINCT FROM OLD.residual_probability
        OR NEW.residual_impact IS DISTINCT FROM OLD.residual_impact
    ) THEN
        RAISE EXCEPTION 'Closed risk assessments cannot be modified.';
    END IF;

    IF NEW.version <> OLD.version + 1 THEN
        RAISE EXCEPTION 'Risk version must increase by exactly one.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_risk_transition
BEFORE UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION validate_risk_transition();

-- ---------------------------------------------------------------------------
-- RISK RESPONSE ASSIGNMENT FUNCTION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION assign_risk_response(
    p_risk_id BIGINT,
    p_strategy response_strategy,
    p_action TEXT,
    p_owner_id BIGINT,
    p_response_cost NUMERIC,
    p_contingency NUMERIC
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_status risk_status;
    v_response_id BIGINT;
BEGIN
    IF p_action IS NULL OR LENGTH(TRIM(p_action)) = 0 THEN
        RAISE EXCEPTION 'Response action is required.';
    END IF;

    IF p_response_cost < 0 OR p_contingency < 0 THEN
        RAISE EXCEPTION 'Response amounts cannot be negative.';
    END IF;

    SELECT status
    INTO v_status
    FROM risks
    WHERE risk_id = p_risk_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk % does not exist.', p_risk_id;
    END IF;

    IF v_status = 'CLOSED' THEN
        RAISE EXCEPTION 'Cannot assign a response to a closed risk.';
    END IF;

    INSERT INTO risk_responses (
        risk_id,
        strategy,
        action_description,
        response_owner_id,
        response_cost,
        contingency_reserve
    )
    VALUES (
        p_risk_id,
        p_strategy,
        p_action,
        p_owner_id,
        p_response_cost,
        p_contingency
    )
    RETURNING response_id INTO v_response_id;

    UPDATE risks
    SET status = 'RESPONSE_PLANNED',
        version = version + 1
    WHERE risk_id = p_risk_id;

    RETURN v_response_id;
END;
$$;

-- ---------------------------------------------------------------------------
-- RESIDUAL RISK MONITORING FUNCTION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION monitor_risk(
    p_risk_id BIGINT,
    p_probability SMALLINT,
    p_impact SMALLINT,
    p_assessor_id BIGINT,
    p_notes TEXT DEFAULT NULL
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_score INTEGER;
    v_status risk_status;
    v_project_id BIGINT;
BEGIN
    IF p_probability NOT BETWEEN 1 AND 5
       OR p_impact NOT BETWEEN 1 AND 5 THEN
        RAISE EXCEPTION 'Probability and impact must be between 1 and 5.';
    END IF;

    SELECT status, project_id
    INTO v_status, v_project_id
    FROM risks
    WHERE risk_id = p_risk_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk not found.';
    END IF;

    IF v_status = 'CLOSED' THEN
        RAISE EXCEPTION 'Closed risks cannot be monitored.';
    END IF;

    v_score := p_probability * p_impact;

    INSERT INTO risk_assessments (
        risk_id,
        probability,
        impact,
        assessment_type,
        assessed_by,
        assessment_notes
    )
    VALUES (
        p_risk_id,
        p_probability,
        p_impact,
        'RESIDUAL',
        p_assessor_id,
        p_notes
    );

    UPDATE risks
    SET residual_probability = p_probability,
        residual_impact = p_impact,
        status = 'MONITORING',
        version = version + 1
    WHERE risk_id = p_risk_id;

    RETURN v_score;
END;
$$;

-- ---------------------------------------------------------------------------
-- RISK ESCALATION PROCEDURE
-- ---------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE escalate_risk(
    p_risk_id BIGINT,
    p_escalated_by BIGINT,
    p_escalated_to BIGINT,
    p_reason TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_reason IS NULL OR LENGTH(TRIM(p_reason)) = 0 THEN
        RAISE EXCEPTION 'Escalation reason is required.';
    END IF;

    UPDATE risks
    SET status = 'ESCALATED',
        version = version + 1
    WHERE risk_id = p_risk_id
      AND status <> 'CLOSED';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk is missing or already closed.';
    END IF;

    INSERT INTO risk_escalations (
        risk_id,
        escalated_by,
        escalated_to,
        reason
    )
    VALUES (
        p_risk_id,
        p_escalated_by,
        p_escalated_to,
        p_reason
    );
END;
$$;

-- ---------------------------------------------------------------------------
-- RISK CLOSURE PROCEDURE
-- ---------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE close_risk(
    p_risk_id BIGINT,
    p_resolution TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_resolution IS NULL OR LENGTH(TRIM(p_resolution)) = 0 THEN
        RAISE EXCEPTION 'Closure resolution is required.';
    END IF;

    UPDATE risks
    SET status = 'CLOSED',
        closed_at = CURRENT_TIMESTAMP,
        closure_reason = p_resolution,
        version = version + 1
    WHERE risk_id = p_risk_id
      AND status <> 'CLOSED';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk is missing or already closed.';
    END IF;
END;
$$;

-- ---------------------------------------------------------------------------
-- VIEWS
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_risk_register AS
SELECT
    r.risk_id,
    p.project_code,
    p.project_name,
    r.risk_code,
    r.title,
    rc.category_name,
    owner.full_name AS risk_owner,
    r.probability,
    r.impact,
    r.inherent_score,
    classify_risk(r.inherent_score) AS inherent_level,
    r.residual_probability,
    r.residual_impact,
    r.residual_score,
    classify_risk(r.residual_score) AS current_level,
    r.status,
    r.identified_at,
    r.due_date
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN risk_categories rc
    ON rc.category_id = r.category_id
JOIN project_members owner
    ON owner.member_id = r.owner_id;

CREATE OR REPLACE VIEW v_risk_response_summary AS
SELECT
    r.risk_id,
    r.risk_code,
    r.title,
    rr.strategy,
    rr.action_description,
    response_owner.full_name AS response_owner,
    rr.response_cost,
    rr.contingency_reserve,
    rr.response_cost + rr.contingency_reserve AS total_planned_amount,
    rr.implementation_status
FROM risks r
JOIN risk_responses rr
    ON rr.risk_id = r.risk_id
JOIN project_members response_owner
    ON response_owner.member_id = rr.response_owner_id;

-- ---------------------------------------------------------------------------
-- PORTFOLIO RISK REPORT
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_project_risk_summary AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,

    COUNT(r.risk_id) AS total_risks,

    COUNT(r.risk_id) FILTER (
        WHERE r.status <> 'CLOSED'
    ) AS active_risks,

    COUNT(r.risk_id) FILTER (
        WHERE r.status = 'CLOSED'
    ) AS closed_risks,

    COALESCE(
        SUM(r.inherent_score) FILTER (
            WHERE r.status <> 'CLOSED'
        ),
        0
    ) AS total_inherent_exposure,

    COALESCE(
        SUM(r.residual_score) FILTER (
            WHERE r.status <> 'CLOSED'
        ),
        0
    ) AS total_residual_exposure,

    COUNT(r.risk_id) FILTER (
        WHERE r.status <> 'CLOSED'
        AND r.residual_score >= 20
    ) AS critical_risks,

    COUNT(r.risk_id) FILTER (
        WHERE r.status <> 'CLOSED'
        AND r.residual_score BETWEEN 12 AND 19
    ) AS high_risks

FROM projects p
LEFT JOIN risks r
    ON r.project_id = p.project_id
GROUP BY
    p.project_id,
    p.project_code,
    p.project_name;

-- ---------------------------------------------------------------------------
-- POLICY EVALUATION FUNCTION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_risk_policy(
    p_risk_id BIGINT
)
RETURNS TABLE (
    evaluated_risk_id BIGINT,
    exposure INTEGER,
    level risk_level,
    policy_compliant BOOLEAN,
    violation TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_risk RECORD;
    v_policy RECORD;
    v_violation TEXT;
BEGIN
    SELECT
        r.risk_id,
        r.project_id,
        r.residual_score,
        r.status,
        r.owner_id
    INTO v_risk
    FROM risks r
    WHERE r.risk_id = p_risk_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk not found.';
    END IF;

    SELECT *
    INTO v_policy
    FROM risk_policies
    WHERE project_id = v_risk.project_id
      AND is_active = TRUE
    ORDER BY policy_id DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT
            v_risk.risk_id,
            v_risk.residual_score,
            classify_risk(v_risk.residual_score),
            FALSE,
            'No active project risk policy exists.'::TEXT;

        RETURN;
    END IF;

    v_violation := NULL;

    IF v_risk.status <> 'CLOSED'
       AND v_policy.require_response_for_high
       AND v_risk.residual_score >= v_policy.minimum_review_score
       AND NOT EXISTS (
            SELECT 1
            FROM risk_responses rr
            WHERE rr.risk_id = v_risk.risk_id
              AND rr.implementation_status <> 'CANCELLED'
       ) THEN

        v_violation := 'High-risk exposure requires a response plan.';
    END IF;

    IF v_risk.status <> 'CLOSED'
       AND v_policy.require_active_owner
       AND NOT EXISTS (
            SELECT 1
            FROM project_members pm
            WHERE pm.member_id = v_risk.owner_id
              AND pm.is_active = TRUE
       ) THEN

        v_violation := CONCAT_WS(
            ' ',
            v_violation,
            'Risk owner is inactive.'
        );
    END IF;

    RETURN QUERY
    SELECT
        v_risk.risk_id,
        v_risk.residual_score,
        classify_risk(v_risk.residual_score),
        v_violation IS NULL,
        v_violation;
END;
$$;

-- ---------------------------------------------------------------------------
-- SAMPLE PROJECT DATA
-- ---------------------------------------------------------------------------

INSERT INTO projects (
    project_code,
    project_name,
    description,
    approved_budget,
    planned_start,
    planned_end
)
VALUES (
    'PRJ-2026-001',
    'Enterprise Management Platform',
    'Implementation of an enterprise project management platform.',
    2500000,
    '2026-11-01',
    '2027-06-30'
);

INSERT INTO project_members (
    employee_code,
    full_name,
    email,
    role_name
)
VALUES
(
    'EMP001',
    'Ananya Sharma',
    'ananya@example.com',
    'Project Manager'
),
(
    'EMP002',
    'Rahul Verma',
    'rahul@example.com',
    'Infrastructure Lead'
),
(
    'EMP003',
    'Priya Singh',
    'priya@example.com',
    'Security Lead'
),
(
    'EMP004',
    'Arjun Mehta',
    'arjun@example.com',
    'Engineering Manager'
),
(
    'EMP005',
    'Neha Gupta',
    'neha@example.com',
    'Product Owner'
),
(
    'EMP006',
    'Karan Rao',
    'karan@example.com',
    'Compliance Manager'
),
(
    'EMP007',
    'Vikram Das',
    'vikram@example.com',
    'Risk Analyst'
);

INSERT INTO risk_categories (
    category_code,
    category_name,
    description
)
VALUES
('TECH', 'Technical', 'Technology and system implementation risks.'),
('FIN', 'Financial', 'Budget and expenditure risks.'),
('OPS', 'Operational', 'Operational execution risks.'),
('SCHED', 'Schedule', 'Timeline and delivery risks.'),
('RES', 'Resource', 'People and resource availability risks.'),
('SEC', 'Security', 'Information security risks.'),
('LEGAL', 'Legal', 'Regulatory and legal risks.'),
('QUAL', 'Quality', 'Product and service quality risks.'),
('SCOPE', 'Scope', 'Requirements and scope management risks.'),
('EXT', 'External', 'External environmental and supplier risks.');

INSERT INTO project_membership (
    project_id,
    member_id,
    membership_role
)
SELECT
    p.project_id,
    pm.member_id,
    CASE pm.employee_code
        WHEN 'EMP001' THEN 'PROJECT_MANAGER'
        WHEN 'EMP002' THEN 'RISK_OWNER'
        WHEN 'EMP003' THEN 'RISK_OWNER'
        WHEN 'EMP004' THEN 'RISK_OWNER'
        WHEN 'EMP005' THEN 'RISK_OWNER'
        ELSE 'TEAM_MEMBER'
    END
FROM projects p
CROSS JOIN project_members pm
WHERE p.project_code = 'PRJ-2026-001';

INSERT INTO risk_policies (
    project_id,
    policy_name,
    low_max,
    medium_max,
    high_max,
    minimum_review_score,
    require_response_for_high,
    require_active_owner
)
SELECT
    project_id,
    'Standard Project Risk Policy',
    5,
    11,
    19,
    12,
    TRUE,
    TRUE
FROM projects
WHERE project_code = 'PRJ-2026-001';

-- ---------------------------------------------------------------------------
-- SAMPLE RISK IDENTIFICATION
-- ---------------------------------------------------------------------------

INSERT INTO risks (
    project_id,
    risk_code,
    title,
    description,
    category_id,
    owner_id,
    probability,
    impact,
    due_date
)
SELECT
    p.project_id,
    sample.risk_code,
    sample.title,
    sample.description,
    rc.category_id,
    pm.member_id,
    sample.probability,
    sample.impact,
    sample.due_date
FROM projects p
CROSS JOIN (
    VALUES
    (
        'R001',
        'Cloud provisioning delay',
        'Cloud infrastructure may not be available on schedule.',
        'SCHED',
        'EMP002',
        4,
        5,
        CURRENT_DATE + 10
    ),
    (
        'R002',
        'Unexpected expenditure',
        'Licensing and infrastructure expenses may exceed budget.',
        'FIN',
        'EMP001',
        3,
        5,
        CURRENT_DATE + 20
    ),
    (
        'R003',
        'Unauthorized data access',
        'Confidential project information may be exposed.',
        'SEC',
        'EMP003',
        2,
        5,
        CURRENT_DATE + 5
    ),
    (
        'R004',
        'Key developer unavailability',
        'A critical developer may become unavailable.',
        'RES',
        'EMP004',
        3,
        4,
        CURRENT_DATE + 15
    ),
    (
        'R005',
        'Uncontrolled scope expansion',
        'Unapproved requirements may increase project workload.',
        'SCOPE',
        'EMP005',
        4,
        4,
        CURRENT_DATE + 8
    ),
    (
        'R006',
        'Regulatory approval delay',
        'External approval may take longer than expected.',
        'LEGAL',
        'EMP006',
        2,
        3,
        CURRENT_DATE + 30
    )
) AS sample(
    risk_code,
    title,
    description,
    category_code,
    employee_code,
    probability,
    impact,
    due_date
)
JOIN risk_categories rc
    ON rc.category_code = sample.category_code
JOIN project_members pm
    ON pm.employee_code = sample.employee_code
WHERE p.project_code = 'PRJ-2026-001';

-- ---------------------------------------------------------------------------
-- INITIAL ASSESSMENTS
-- ---------------------------------------------------------------------------

INSERT INTO risk_assessments (
    risk_id,
    probability,
    impact,
    assessment_type,
    assessed_by,
    assessment_notes
)
SELECT
    r.risk_id,
    r.probability,
    r.impact,
    'INHERENT',
    pm.member_id,
    'Initial probability and impact assessment.'
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_members pm
    ON pm.employee_code = 'EMP007'
WHERE p.project_code = 'PRJ-2026-001';

UPDATE risks
SET status = 'ASSESSED',
    version = version + 1
WHERE project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'PRJ-2026-001'
);

-- ---------------------------------------------------------------------------
-- RESPONSE PLANS
-- ---------------------------------------------------------------------------

SELECT assign_risk_response(
    r.risk_id,
    'MITIGATE',
    'Maintain an alternative cloud infrastructure provider.',
    pm.member_id,
    10000,
    5000
)
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_members pm
    ON pm.employee_code = 'EMP002'
WHERE p.project_code = 'PRJ-2026-001'
AND r.risk_code = 'R001';

SELECT assign_risk_response(
    r.risk_id,
    'MITIGATE',
    'Introduce monthly budget forecasts and spending controls.',
    pm.member_id,
    2500,
    8000
)
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_members pm
    ON pm.employee_code = 'EMP001'
WHERE p.project_code = 'PRJ-2026-001'
AND r.risk_code = 'R002';

SELECT assign_risk_response(
    r.risk_id,
    'AVOID',
    'Enforce least privilege access and multi-factor authentication.',
    pm.member_id,
    4000,
    1000
)
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_members pm
    ON pm.employee_code = 'EMP003'
WHERE p.project_code = 'PRJ-2026-001'
AND r.risk_code = 'R003';

SELECT assign_risk_response(
    r.risk_id,
    'MITIGATE',
    'Cross-train development personnel and document critical modules.',
    pm.member_id,
    3000,
    1000
)
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_members pm
    ON pm.employee_code = 'EMP004'
WHERE p.project_code = 'PRJ-2026-001'
AND r.risk_code = 'R004';

SELECT assign_risk_response(
    r.risk_id,
    'AVOID',
    'Require formal approval for scope changes.',
    pm.member_id,
    1500,
    1000
)
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_members pm
    ON pm.employee_code = 'EMP005'
WHERE p.project_code = 'PRJ-2026-001'
AND r.risk_code = 'R005';

SELECT assign_risk_response(
    r.risk_id,
    'TRANSFER',
    'Engage a qualified compliance service provider.',
    pm.member_id,
    2500,
    1500
)
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_members pm
    ON pm.employee_code = 'EMP006'
WHERE p.project_code = 'PRJ-2026-001'
AND r.risk_code = 'R006';

-- ---------------------------------------------------------------------------
-- RESIDUAL RISK ASSESSMENTS
-- ---------------------------------------------------------------------------

SELECT
    monitor_risk(
        r.risk_id,
        sample.probability,
        sample.impact,
        assessor.member_id,
        sample.notes
    )
FROM risks r
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_members assessor
    ON assessor.employee_code = 'EMP007'
JOIN (
    VALUES
        ('R001', 2::SMALLINT, 4::SMALLINT, 'Alternative infrastructure available.'),
        ('R002', 2::SMALLINT, 4::SMALLINT, 'Budget monitoring introduced.'),
        ('R003', 1::SMALLINT, 4::SMALLINT, 'Access restrictions strengthened.'),
        ('R004', 2::SMALLINT, 3::SMALLINT, 'Backup developer identified.'),
        ('R005', 2::SMALLINT, 3::SMALLINT, 'Scope approval process implemented.'),
        ('R006', 2::SMALLINT, 3::SMALLINT, 'Approval timeline under monitoring.')
) AS sample(risk_code, probability, impact, notes)
    ON sample.risk_code = r.risk_code
WHERE p.project_code = 'PRJ-2026-001';

COMMIT;

-- ---------------------------------------------------------------------------
-- RETRIEVAL: COMPLETE RISK REGISTER
-- ---------------------------------------------------------------------------

SELECT *
FROM v_risk_register
ORDER BY residual_score DESC, risk_code;

-- ---------------------------------------------------------------------------
-- PRIORITIZATION: ACTIVE RISKS
-- ---------------------------------------------------------------------------

SELECT
    risk_code,
    title,
    risk_owner,
    probability,
    impact,
    inherent_score,
    residual_score,
    current_level,
    status
FROM v_risk_register
WHERE status <> 'CLOSED'
ORDER BY residual_score DESC, inherent_score DESC;

-- ---------------------------------------------------------------------------
-- AGGREGATION: PORTFOLIO EXPOSURE
-- ---------------------------------------------------------------------------

SELECT *
FROM v_project_risk_summary;

-- ---------------------------------------------------------------------------
-- CATEGORY EXPOSURE
-- ---------------------------------------------------------------------------

SELECT
    category_name,
    COUNT(*) AS risk_count,
    SUM(residual_score) AS total_exposure,
    AVG(residual_score)::NUMERIC(10,2) AS average_exposure,
    MAX(residual_score) AS highest_exposure
FROM v_risk_register
WHERE status <> 'CLOSED'
GROUP BY category_name
ORDER BY total_exposure DESC;

-- ---------------------------------------------------------------------------
-- OWNER WORKLOAD
-- ---------------------------------------------------------------------------

SELECT
    risk_owner,
    COUNT(*) AS assigned_risks,
    SUM(residual_score) AS assigned_exposure,
    COUNT(*) FILTER (
        WHERE current_level IN ('HIGH', 'CRITICAL')
    ) AS high_priority_risks
FROM v_risk_register
WHERE status <> 'CLOSED'
GROUP BY risk_owner
ORDER BY assigned_exposure DESC;

-- ---------------------------------------------------------------------------
-- VALIDATION: OVERDUE RISKS
-- ---------------------------------------------------------------------------

SELECT
    risk_code,
    title,
    risk_owner,
    due_date,
    CURRENT_DATE - due_date AS days_overdue,
    residual_score
FROM v_risk_register
WHERE due_date < CURRENT_DATE
AND status <> 'CLOSED'
ORDER BY days_overdue DESC;

-- ---------------------------------------------------------------------------
-- VALIDATION: HIGH RISKS WITHOUT RESPONSE PLANS
-- ---------------------------------------------------------------------------

SELECT
    r.risk_id,
    r.risk_code,
    r.title,
    r.residual_score,
    classify_risk(r.residual_score) AS risk_level
FROM risks r
WHERE r.status <> 'CLOSED'
AND r.residual_score >= 12
AND NOT EXISTS (
    SELECT 1
    FROM risk_responses rr
    WHERE rr.risk_id = r.risk_id
    AND rr.implementation_status <> 'CANCELLED'
);

-- ---------------------------------------------------------------------------
-- POLICY EVALUATION
-- ---------------------------------------------------------------------------

SELECT
    r.risk_code,
    evaluation.exposure,
    evaluation.level,
    evaluation.policy_compliant,
    evaluation.violation
FROM risks r
CROSS JOIN LATERAL evaluate_risk_policy(r.risk_id) evaluation
ORDER BY evaluation.exposure DESC;

-- ---------------------------------------------------------------------------
-- RESPONSE COST REPORT
-- ---------------------------------------------------------------------------

SELECT
    r.risk_code,
    r.title,
    SUM(rr.response_cost) AS response_cost,
    SUM(rr.contingency_reserve) AS contingency_reserve,
    SUM(
        rr.response_cost + rr.contingency_reserve
    ) AS total_planned_amount
FROM risks r
JOIN risk_responses rr
    ON rr.risk_id = r.risk_id
GROUP BY
    r.risk_code,
    r.title
ORDER BY total_planned_amount DESC;

-- ---------------------------------------------------------------------------
-- RISK HISTORY
-- ---------------------------------------------------------------------------

SELECT
    r.risk_code,
    h.event_type,
    h.event_details,
    h.event_time
FROM risk_history h
JOIN risks r
    ON r.risk_id = h.risk_id
ORDER BY h.event_time DESC;

-- ---------------------------------------------------------------------------
-- CTE: PRIORITY CLASSIFICATION
-- ---------------------------------------------------------------------------

WITH ranked_risks AS (
    SELECT
        r.risk_id,
        r.risk_code,
        r.title,
        r.residual_score,
        classify_risk(r.residual_score) AS level,
        ROW_NUMBER() OVER (
            ORDER BY r.residual_score DESC, r.risk_code
        ) AS priority_rank
    FROM risks r
    WHERE r.status <> 'CLOSED'
)
SELECT *
FROM ranked_risks
ORDER BY priority_rank;

-- ---------------------------------------------------------------------------
-- CTE: CATEGORY CONTRIBUTION
-- ---------------------------------------------------------------------------

WITH category_totals AS (
    SELECT
        rc.category_name,
        SUM(r.residual_score) AS exposure
    FROM risks r
    JOIN risk_categories rc
        ON rc.category_id = r.category_id
    WHERE r.status <> 'CLOSED'
    GROUP BY rc.category_name
)
SELECT
    category_name,
    exposure,
    ROUND(
        100.0 * exposure /
        NULLIF(SUM(exposure) OVER (), 0),
        2
    ) AS exposure_percentage
FROM category_totals
ORDER BY exposure DESC;

-- ---------------------------------------------------------------------------
-- WORKFLOW PROCESSING: ESCALATE A RISK
-- Example execution:
--
-- BEGIN;
-- CALL escalate_risk(1, 1, 3, 'Residual risk requires sponsor attention.');
-- COMMIT;
--
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- TRANSACTION EXAMPLE: CLOSE A RESOLVED RISK
-- This example is intentionally rolled back to preserve sample data.
-- ---------------------------------------------------------------------------

BEGIN;

DO $$
DECLARE
    v_risk_id BIGINT;
BEGIN
    SELECT risk_id
    INTO v_risk_id
    FROM risks
    WHERE risk_code = 'R006'
    LIMIT 1;

    IF v_risk_id IS NOT NULL THEN
        CALL close_risk(
            v_risk_id,
            'External approval completed and risk no longer exists.'
        );
    END IF;
END;
$$;

ROLLBACK;

-- ---------------------------------------------------------------------------
-- FAILURE CASE VALIDATION
-- Execute individually to observe the expected constraint errors.
-- ---------------------------------------------------------------------------

-- Invalid probability:
-- INSERT INTO risks (...) VALUES (..., 7, 3);

-- Duplicate risk code:
-- INSERT INTO risks (...) VALUES (..., 'R001', ...);

-- Negative response cost:
-- INSERT INTO risk_responses (...) VALUES (..., -100, ...);

-- Monitoring a closed risk:
-- SELECT monitor_risk(1, 2, 2, 7, 'Invalid update');

-- Assigning an empty response:
-- SELECT assign_risk_response(1, 'MITIGATE', '', 2, 100, 50);

-- ---------------------------------------------------------------------------
-- DATABASE PERFORMANCE AND OPERATIONAL NOTES
-- ---------------------------------------------------------------------------

-- Generated exposure columns avoid repeated score calculations.
-- Partial indexes reduce the size of active-risk indexes.
-- Foreign keys preserve project and ownership relationships.
-- Version numbers support optimistic concurrency control.
-- FOR UPDATE protects response assignment and monitoring operations.
-- Transactions ensure related workflow changes commit together.
-- Application roles should receive only the permissions they require.
-- Sensitive project information should not be stored in unrestricted logs.
-- Production deployments should define explicit backup and retention policies.
