-- ============================================================
-- RISK ANALYSIS AND MANAGEMENT DATABASE
-- PostgreSQL 14+
--
-- Covers:
-- 1. Risk identification
-- 2. Probability and impact assessment
-- 3. Inherent and residual exposure
-- 4. Risk controls
-- 5. Risk ownership
-- 6. Risk treatment
-- 7. Risk acceptance and approval
-- 8. Risk assessment history
-- 9. Portfolio aggregation
-- 10. Risk prioritization and reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS risk_management;

SET search_path TO risk_management, public;


-- ============================================================
-- 1. ENUMERATIONS
-- ============================================================

CREATE TYPE risk_category AS ENUM (
    'STRATEGIC',
    'FINANCIAL',
    'OPERATIONAL',
    'TECHNOLOGY',
    'SECURITY',
    'COMPLIANCE',
    'REPUTATIONAL'
);

CREATE TYPE risk_status AS ENUM (
    'IDENTIFIED',
    'ASSESSED',
    'MITIGATING',
    'PENDING_APPROVAL',
    'ACCEPTED',
    'CLOSED'
);

CREATE TYPE risk_treatment AS ENUM (
    'ACCEPT',
    'MITIGATE',
    'TRANSFER',
    'AVOID'
);

CREATE TYPE approval_status AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED'
);


-- ============================================================
-- 2. ORGANIZATIONAL USERS
-- ============================================================

CREATE TABLE risk_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_email
        CHECK (email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$')
);


-- ============================================================
-- 3. ORGANIZATIONAL RISK REGISTER
-- ============================================================

CREATE TABLE risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    category risk_category NOT NULL,

    owner_id BIGINT NOT NULL
        REFERENCES risk_users(user_id),

    status risk_status NOT NULL DEFAULT 'IDENTIFIED',

    treatment risk_treatment,

    version INTEGER NOT NULL DEFAULT 1,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_risk_code
        CHECK (risk_code ~ '^R[0-9]{3,}$'),

    CONSTRAINT valid_risk_title
        CHECK (length(trim(title)) > 0),

    CONSTRAINT valid_version
        CHECK (version > 0)
);


-- ============================================================
-- 4. RISK ASSESSMENTS
--
-- Probability:
--   0.0 = impossible under the modeled assumptions
--   1.0 = certain under the modeled assumptions
--
-- Impact:
--   Monetary loss if the risk event occurs.
--
-- Expected exposure:
--   Probability * Impact
--
-- Assessments are versioned to preserve historical decisions.
-- ============================================================

CREATE TABLE risk_assessments (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    assessment_version INTEGER NOT NULL,

    probability NUMERIC(7,6) NOT NULL,
    impact_amount NUMERIC(16,2) NOT NULL,

    assessor_id BIGINT NOT NULL
        REFERENCES risk_users(user_id),

    rationale TEXT NOT NULL,

    assessment_type VARCHAR(20) NOT NULL DEFAULT 'INHERENT',

    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_probability
        CHECK (probability BETWEEN 0 AND 1),

    CONSTRAINT valid_impact
        CHECK (impact_amount >= 0),

    CONSTRAINT valid_assessment_version
        CHECK (assessment_version > 0),

    CONSTRAINT valid_assessment_type
        CHECK (assessment_type IN ('INHERENT', 'REASSESSMENT')),

    CONSTRAINT unique_risk_assessment_version
        UNIQUE (risk_id, assessment_version),

    CONSTRAINT nonempty_rationale
        CHECK (length(trim(rationale)) > 0)
);


-- ============================================================
-- 5. RISK CONTROL REGISTER
-- ============================================================

CREATE TABLE risk_controls (
    control_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    control_code VARCHAR(30) NOT NULL UNIQUE,

    control_name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    probability_reduction NUMERIC(6,5) NOT NULL DEFAULT 0,
    impact_reduction NUMERIC(6,5) NOT NULL DEFAULT 0,

    responsible_user_id BIGINT NOT NULL
        REFERENCES risk_users(user_id),

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_probability_reduction
        CHECK (probability_reduction BETWEEN 0 AND 1),

    CONSTRAINT valid_impact_reduction
        CHECK (impact_reduction BETWEEN 0 AND 1),

    CONSTRAINT unique_control_name
        UNIQUE (control_name)
);


-- ============================================================
-- 6. RISK-CONTROL MAPPING
--
-- A risk may have multiple controls.
-- A control may address multiple risks.
--
-- Combined effectiveness assumes independent reductions.
-- ============================================================

CREATE TABLE risk_control_mapping (
    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    control_id BIGINT NOT NULL
        REFERENCES risk_controls(control_id),

    implemented BOOLEAN NOT NULL DEFAULT FALSE,

    implementation_date DATE,

    effectiveness_reviewed_at TIMESTAMPTZ,

    PRIMARY KEY (risk_id, control_id),

    CONSTRAINT implementation_date_valid
        CHECK (
            implementation_date IS NULL
            OR implemented = TRUE
        )
);


-- ============================================================
-- 7. RISK TREATMENT DECISIONS
-- ============================================================

CREATE TABLE risk_treatments (
    treatment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    treatment risk_treatment NOT NULL,

    justification TEXT NOT NULL,

    assigned_to BIGINT NOT NULL
        REFERENCES risk_users(user_id),

    target_date DATE,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT treatment_justification_required
        CHECK (length(trim(justification)) > 0),

    CONSTRAINT completion_date_valid
        CHECK (
            completed_at IS NULL
            OR completed_at >= created_at
        )
);


-- ============================================================
-- 8. RISK ACCEPTANCE APPROVALS
-- ============================================================

CREATE TABLE risk_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    approver_id BIGINT NOT NULL
        REFERENCES risk_users(user_id),

    decision approval_status NOT NULL DEFAULT 'PENDING',

    justification TEXT NOT NULL,

    decided_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT approval_justification_required
        CHECK (length(trim(justification)) > 0),

    CONSTRAINT approval_decision_timestamp
        CHECK (
            (decision = 'PENDING' AND decided_at IS NULL)
            OR
            (decision <> 'PENDING' AND decided_at IS NOT NULL)
        ),

    CONSTRAINT unique_risk_approver
        UNIQUE (risk_id, approver_id)
);


-- ============================================================
-- 9. RISK AUDIT EVENTS
-- ============================================================

CREATE TABLE risk_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    event_type VARCHAR(80) NOT NULL,

    actor_id BIGINT
        REFERENCES risk_users(user_id),

    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 10. INDEXES
-- ============================================================

CREATE INDEX idx_risks_category_status
    ON risks(category, status);

CREATE INDEX idx_risks_owner
    ON risks(owner_id);

CREATE INDEX idx_assessments_risk_time
    ON risk_assessments(risk_id, assessed_at DESC);

CREATE INDEX idx_assessments_probability
    ON risk_assessments(probability DESC);

CREATE INDEX idx_controls_active
    ON risk_controls(control_id)
    WHERE active = TRUE;

CREATE INDEX idx_control_mapping_risk
    ON risk_control_mapping(risk_id, implemented);

CREATE INDEX idx_approvals_pending
    ON risk_approvals(risk_id)
    WHERE decision = 'PENDING';

CREATE INDEX idx_audit_risk_time
    ON risk_audit_log(risk_id, created_at DESC);

CREATE INDEX idx_audit_json
    ON risk_audit_log USING GIN(event_details);


-- ============================================================
-- 11. PROBABILITY AND IMPACT CALCULATIONS
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_expected_loss(
    p_probability NUMERIC,
    p_impact NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_probability < 0 OR p_probability > 1 THEN
        RAISE EXCEPTION
            'Probability must be between 0 and 1';
    END IF;

    IF p_impact < 0 THEN
        RAISE EXCEPTION
            'Impact cannot be negative';
    END IF;

    RETURN ROUND(p_probability * p_impact, 2);
END;
$$;


-- ============================================================
-- 12. RISK CLASSIFICATION
--
-- These monetary thresholds are illustrative organizational
-- policy values, not universal risk standards.
-- ============================================================

CREATE OR REPLACE FUNCTION classify_risk(
    p_exposure NUMERIC
)
RETURNS VARCHAR
LANGUAGE sql
IMMUTABLE
STRICT
AS $$
    SELECT CASE
        WHEN p_exposure >= 100000 THEN 'CRITICAL'
        WHEN p_exposure >= 25000 THEN 'HIGH'
        WHEN p_exposure >= 5000 THEN 'MODERATE'
        ELSE 'LOW'
    END;
$$;


-- ============================================================
-- 13. CALCULATE RESIDUAL RISK
--
-- Only implemented and active controls are included.
--
-- The multiplication model assumes independent control effects.
-- It is not appropriate when controls have overlapping effects.
-- ============================================================

CREATE OR REPLACE FUNCTION get_residual_assessment(
    p_risk_id BIGINT
)
RETURNS TABLE (
    inherent_probability NUMERIC,
    inherent_impact NUMERIC,
    inherent_exposure NUMERIC,
    residual_probability NUMERIC,
    residual_impact NUMERIC,
    residual_exposure NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_probability NUMERIC;
    v_impact NUMERIC;

    v_probability_remaining NUMERIC := 1;
    v_impact_remaining NUMERIC := 1;

    v_probability_reduction NUMERIC;
    v_impact_reduction NUMERIC;
BEGIN
    SELECT a.probability, a.impact_amount
    INTO v_probability, v_impact
    FROM risk_assessments a
    WHERE a.risk_id = p_risk_id
    ORDER BY a.assessed_at DESC, a.assessment_id DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'No assessment exists for risk ID %',
            p_risk_id;
    END IF;

    SELECT
        COALESCE(
            EXP(SUM(LN(1 - c.probability_reduction)))
                FILTER (WHERE c.probability_reduction < 1),
            0
        ),
        COALESCE(
            EXP(SUM(LN(1 - c.impact_reduction)))
                FILTER (WHERE c.impact_reduction < 1),
            0
        )
    INTO
        v_probability_remaining,
        v_impact_remaining
    FROM risk_control_mapping m
    JOIN risk_controls c
        ON c.control_id = m.control_id
    WHERE m.risk_id = p_risk_id
      AND m.implemented = TRUE
      AND c.active = TRUE;

    -- A 100% effective control makes the remaining factor zero.
    IF EXISTS (
        SELECT 1
        FROM risk_control_mapping m
        JOIN risk_controls c
            ON c.control_id = m.control_id
        WHERE m.risk_id = p_risk_id
          AND m.implemented = TRUE
          AND c.active = TRUE
          AND c.probability_reduction = 1
    ) THEN
        v_probability_remaining := 0;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM risk_control_mapping m
        JOIN risk_controls c
            ON c.control_id = m.control_id
        WHERE m.risk_id = p_risk_id
          AND m.implemented = TRUE
          AND c.active = TRUE
          AND c.impact_reduction = 1
    ) THEN
        v_impact_remaining := 0;
    END IF;

    RETURN QUERY
    SELECT
        v_probability,
        v_impact,
        calculate_expected_loss(v_probability, v_impact),
        ROUND(v_probability * v_probability_remaining, 6),
        ROUND(v_impact * v_impact_remaining, 2),
        calculate_expected_loss(
            v_probability * v_probability_remaining,
            v_impact * v_impact_remaining
        );
END;
$$;


-- ============================================================
-- 14. TRIGGER: UPDATE RISK VERSION AND TIMESTAMP
-- ============================================================

CREATE OR REPLACE FUNCTION update_risk_metadata()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    NEW.version := OLD.version + 1;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_update_risk_metadata
BEFORE UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION update_risk_metadata();


-- ============================================================
-- 15. TRIGGER: AUDIT RISK STATUS CHANGES
-- ============================================================

CREATE OR REPLACE FUNCTION audit_risk_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO risk_audit_log (
            risk_id,
            event_type,
            event_details
        )
        VALUES (
            NEW.risk_id,
            'STATUS_CHANGED',
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_risk_status_audit
AFTER UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION audit_risk_status_change();


-- ============================================================
-- 16. VIEW: CURRENT RISK EXPOSURE
-- ============================================================

CREATE OR REPLACE VIEW current_risk_exposure AS
SELECT
    r.risk_id,
    r.risk_code,
    r.title,
    r.category,
    r.status,
    u.full_name AS risk_owner,

    assessment.inherent_probability,
    assessment.inherent_impact,
    assessment.inherent_exposure,

    assessment.residual_probability,
    assessment.residual_impact,
    assessment.residual_exposure,

    classify_risk(
        assessment.residual_exposure
    ) AS risk_level,

    r.version,
    r.updated_at

FROM risks r

JOIN risk_users u
    ON u.user_id = r.owner_id

CROSS JOIN LATERAL get_residual_assessment(r.risk_id)
    AS assessment;


-- ============================================================
-- 17. VIEW: RISK CONTROL EFFECTIVENESS
-- ============================================================

CREATE OR REPLACE VIEW risk_control_effectiveness AS
SELECT
    r.risk_code,
    r.title,

    COUNT(m.control_id) AS total_controls,

    COUNT(m.control_id)
        FILTER (WHERE m.implemented = TRUE)
        AS implemented_controls,

    COUNT(m.control_id)
        FILTER (
            WHERE m.implemented = TRUE
              AND c.active = TRUE
        )
        AS effective_controls,

    ROUND(
        AVG(c.probability_reduction)
            FILTER (
                WHERE m.implemented = TRUE
                  AND c.active = TRUE
            ) * 100,
        2
    ) AS average_probability_reduction_percentage

FROM risks r

LEFT JOIN risk_control_mapping m
    ON m.risk_id = r.risk_id

LEFT JOIN risk_controls c
    ON c.control_id = m.control_id

GROUP BY r.risk_id, r.risk_code, r.title;


-- ============================================================
-- 18. FUNCTION: DETERMINE ACCEPTANCE ELIGIBILITY
-- ============================================================

CREATE OR REPLACE FUNCTION is_risk_eligible_for_acceptance(
    p_risk_id BIGINT,
    p_maximum_exposure NUMERIC DEFAULT 25000,
    p_maximum_probability NUMERIC DEFAULT 0.50
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_exposure NUMERIC;
    v_probability NUMERIC;
BEGIN
    IF p_maximum_exposure < 0 THEN
        RAISE EXCEPTION 'Maximum exposure cannot be negative';
    END IF;

    IF p_maximum_probability < 0
       OR p_maximum_probability > 1 THEN
        RAISE EXCEPTION
            'Maximum probability must be between 0 and 1';
    END IF;

    SELECT residual_exposure, residual_probability
    INTO v_exposure, v_probability
    FROM current_risk_exposure
    WHERE risk_id = p_risk_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Risk ID % not found or not assessed',
            p_risk_id;
    END IF;

    RETURN
        v_exposure <= p_maximum_exposure
        AND
        v_probability <= p_maximum_probability;
END;
$$;


-- ============================================================
-- 19. PROCEDURE: REQUEST RISK ACCEPTANCE
-- ============================================================

CREATE OR REPLACE PROCEDURE request_risk_acceptance(
    p_risk_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status risk_status;
BEGIN
    SELECT status
    INTO v_status
    FROM risks
    WHERE risk_id = p_risk_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk does not exist';
    END IF;

    IF v_status = 'CLOSED' THEN
        RAISE EXCEPTION 'Closed risks cannot be accepted';
    END IF;

    IF NOT is_risk_eligible_for_acceptance(p_risk_id) THEN
        RAISE EXCEPTION
            'Risk exceeds acceptance policy; mitigation required';
    END IF;

    UPDATE risks
    SET status = 'PENDING_APPROVAL'
    WHERE risk_id = p_risk_id;
END;
$$;


-- ============================================================
-- 20. PROCEDURE: RECORD ACCEPTANCE DECISION
-- ============================================================

CREATE OR REPLACE PROCEDURE decide_risk_approval(
    p_approval_id BIGINT,
    p_decision approval_status,
    p_justification TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_risk_id BIGINT;
BEGIN
    IF p_decision = 'PENDING' THEN
        RAISE EXCEPTION
            'A final decision must be APPROVED or REJECTED';
    END IF;

    IF p_justification IS NULL
       OR length(trim(p_justification)) = 0 THEN
        RAISE EXCEPTION 'Decision justification is required';
    END IF;

    SELECT risk_id
    INTO v_risk_id
    FROM risk_approvals
    WHERE approval_id = p_approval_id
      AND decision = 'PENDING'
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Pending approval does not exist';
    END IF;

    IF p_decision = 'APPROVED'
       AND NOT is_risk_eligible_for_acceptance(v_risk_id) THEN
        RAISE EXCEPTION
            'Risk is not eligible for acceptance';
    END IF;

    UPDATE risk_approvals
    SET
        decision = p_decision,
        justification = p_justification,
        decided_at = CURRENT_TIMESTAMP
    WHERE approval_id = p_approval_id;

    UPDATE risks
    SET
        status = CASE
            WHEN p_decision = 'APPROVED' THEN 'ACCEPTED'
            ELSE 'MITIGATING'
        END,
        treatment = CASE
            WHEN p_decision = 'APPROVED' THEN 'ACCEPT'
            ELSE 'MITIGATE'
        END
    WHERE risk_id = v_risk_id;
END;
$$;


-- ============================================================
-- 21. SAMPLE ORGANIZATIONAL USERS
-- ============================================================

INSERT INTO risk_users (
    full_name,
    email,
    department,
    role_name
)
VALUES
(
    'Aarav Sharma',
    'aarav.sharma@example.com',
    'Security',
    'Risk Owner'
),
(
    'Meera Singh',
    'meera.singh@example.com',
    'Finance',
    'Risk Owner'
),
(
    'Rahul Verma',
    'rahul.verma@example.com',
    'Infrastructure',
    'Risk Owner'
),
(
    'Priya Gupta',
    'priya.gupta@example.com',
    'Compliance',
    'Risk Owner'
),
(
    'Ananya Rao',
    'ananya.rao@example.com',
    'Operations',
    'Risk Owner'
),
(
    'Vikram Mehta',
    'vikram.mehta@example.com',
    'Governance',
    'Risk Approver'
),
(
    'Neha Kapoor',
    'neha.kapoor@example.com',
    'Risk Management',
    'Risk Analyst'
);


-- ============================================================
-- 22. SAMPLE RISKS
-- ============================================================

INSERT INTO risks (
    risk_code,
    title,
    description,
    category,
    owner_id
)
VALUES
(
    'R001',
    'Cybersecurity Breach',
    'Unauthorized access to sensitive organizational systems.',
    'SECURITY',
    1
),
(
    'R002',
    'Project Budget Overrun',
    'Project implementation costs exceed approved budget.',
    'FINANCIAL',
    2
),
(
    'R003',
    'Cloud Infrastructure Outage',
    'Critical cloud services become unavailable.',
    'TECHNOLOGY',
    3
),
(
    'R004',
    'Regulatory Noncompliance',
    'Failure to meet mandatory regulatory requirements.',
    'COMPLIANCE',
    4
),
(
    'R005',
    'Employee Training Delay',
    'Mandatory operational training is delayed.',
    'OPERATIONAL',
    5
);


-- ============================================================
-- 23. SAMPLE ASSESSMENTS
-- ============================================================

INSERT INTO risk_assessments (
    risk_id,
    assessment_version,
    probability,
    impact_amount,
    assessor_id,
    rationale
)
VALUES
(
    1, 1, 0.700000, 500000,
    7, 'High threat exposure and substantial recovery cost.'
),
(
    2, 1, 0.450000, 120000,
    7, 'Historical budget deviations and supplier uncertainty.'
),
(
    3, 1, 0.300000, 80000,
    7, 'Service dependency and infrastructure availability.'
),
(
    4, 1, 0.200000, 250000,
    7, 'Potential regulatory penalties and remediation costs.'
),
(
    5, 1, 0.050000, 1000,
    7, 'Limited operational impact with low occurrence probability.'
);


-- ============================================================
-- 24. SAMPLE CONTROL REGISTER
-- ============================================================

INSERT INTO risk_controls (
    control_code,
    control_name,
    description,
    probability_reduction,
    impact_reduction,
    responsible_user_id
)
VALUES
(
    'C001',
    'Multi-factor Authentication',
    'Requires additional authentication for sensitive accounts.',
    0.40000,
    0.10000,
    1
),
(
    'C002',
    'Security Monitoring',
    'Detects and responds to suspicious activity.',
    0.15000,
    0.25000,
    1
),
(
    'C003',
    'Budget Monitoring',
    'Periodic review of expenditure and forecast deviations.',
    0.25000,
    0.20000,
    2
),
(
    'C004',
    'Disaster Recovery',
    'Recovery infrastructure and tested restoration procedures.',
    0.20000,
    0.60000,
    3
),
(
    'C005',
    'Regulatory Audit',
    'Scheduled reviews of regulatory compliance.',
    0.50000,
    0.40000,
    4
);


-- ============================================================
-- 25. ASSIGN CONTROLS
-- ============================================================

INSERT INTO risk_control_mapping (
    risk_id,
    control_id,
    implemented,
    implementation_date
)
VALUES
(1, 1, TRUE, CURRENT_DATE),
(1, 2, TRUE, CURRENT_DATE),
(2, 3, TRUE, CURRENT_DATE),
(3, 4, TRUE, CURRENT_DATE),
(4, 5, FALSE, NULL);


-- ============================================================
-- 26. SAMPLE TREATMENT DECISIONS
-- ============================================================

INSERT INTO risk_treatments (
    risk_id,
    treatment,
    justification,
    assigned_to,
    target_date
)
VALUES
(
    1,
    'MITIGATE',
    'Additional security controls are required.',
    1,
    CURRENT_DATE + 30
),
(
    2,
    'MITIGATE',
    'Budget monitoring reduces financial uncertainty.',
    2,
    CURRENT_DATE + 45
),
(
    3,
    'MITIGATE',
    'Disaster recovery arrangements are implemented.',
    3,
    CURRENT_DATE + 60
);


-- ============================================================
-- 27. AUDIT INITIAL RISK REGISTRATION
-- ============================================================

INSERT INTO risk_audit_log (
    risk_id,
    event_type,
    actor_id,
    event_details
)
SELECT
    risk_id,
    'RISK_REGISTERED',
    owner_id,
    jsonb_build_object(
        'risk_code', risk_code,
        'title', title,
        'category', category
    )
FROM risks;


COMMIT;


-- ============================================================
-- 28. RETRIEVAL: ALL CURRENT RISK ASSESSMENTS
-- ============================================================

SELECT
    risk_code,
    title,
    category,
    risk_owner,
    inherent_probability,
    inherent_impact,
    inherent_exposure,
    residual_probability,
    residual_impact,
    residual_exposure,
    risk_level,
    status
FROM current_risk_exposure
ORDER BY residual_exposure DESC;


-- ============================================================
-- 29. VALIDATION: PROBABILITY AND IMPACT
-- ============================================================

SELECT
    risk_code,
    title,
    inherent_probability,
    inherent_impact,
    calculate_expected_loss(
        inherent_probability,
        inherent_impact
    ) AS independently_calculated_exposure
FROM current_risk_exposure
WHERE inherent_probability BETWEEN 0 AND 1
  AND inherent_impact >= 0;


-- ============================================================
-- 30. AGGREGATION: PORTFOLIO EXPOSURE
-- ============================================================

SELECT
    COUNT(*) AS total_risks,

    ROUND(
        SUM(inherent_exposure),
        2
    ) AS total_inherent_exposure,

    ROUND(
        SUM(residual_exposure),
        2
    ) AS total_residual_exposure,

    ROUND(
        SUM(inherent_exposure)
        - SUM(residual_exposure),
        2
    ) AS estimated_exposure_reduction

FROM current_risk_exposure;


-- ============================================================
-- 31. CATEGORY-BASED RISK REPORT
-- ============================================================

SELECT
    category,

    COUNT(*) AS risk_count,

    ROUND(AVG(inherent_probability), 4)
        AS average_probability,

    ROUND(SUM(inherent_exposure), 2)
        AS inherent_exposure,

    ROUND(SUM(residual_exposure), 2)
        AS residual_exposure,

    ROUND(MAX(residual_exposure), 2)
        AS maximum_residual_exposure

FROM current_risk_exposure

GROUP BY category

ORDER BY residual_exposure DESC;


-- ============================================================
-- 32. RISK LEVEL DISTRIBUTION
-- ============================================================

SELECT
    risk_level,
    COUNT(*) AS number_of_risks

FROM current_risk_exposure

GROUP BY risk_level

ORDER BY
    CASE risk_level
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MODERATE' THEN 3
        WHEN 'LOW' THEN 4
    END;


-- ============================================================
-- 33. CONTROL EFFECTIVENESS REPORT
-- ============================================================

SELECT *
FROM risk_control_effectiveness
ORDER BY effective_controls DESC, risk_code;


-- ============================================================
-- 34. IDENTIFY RISKS REQUIRING MITIGATION
-- ============================================================

SELECT
    risk_code,
    title,
    residual_probability,
    residual_exposure,
    risk_level

FROM current_risk_exposure

WHERE residual_exposure > 25000
   OR residual_probability > 0.50

ORDER BY residual_exposure DESC;


-- ============================================================
-- 35. ELIGIBILITY DETERMINATION
-- ============================================================

SELECT
    risk_code,
    title,

    is_risk_eligible_for_acceptance(
        risk_id,
        25000,
        0.50
    ) AS eligible_for_acceptance

FROM current_risk_exposure;


-- ============================================================
-- 36. CTE: RISK PRIORITIZATION
-- ============================================================

WITH prioritized_risks AS (
    SELECT
        risk_code,
        title,
        category,
        residual_exposure,
        risk_level,

        ROW_NUMBER() OVER (
            ORDER BY
                residual_exposure DESC,
                inherent_exposure DESC
        ) AS priority_rank

    FROM current_risk_exposure
)

SELECT *
FROM prioritized_risks
ORDER BY priority_rank;


-- ============================================================
-- 37. CTE: RISKS WITHOUT IMPLEMENTED CONTROLS
-- ============================================================

WITH control_summary AS (
    SELECT
        r.risk_id,
        r.risk_code,
        r.title,

        COUNT(m.control_id) AS total_controls,

        COUNT(m.control_id)
            FILTER (WHERE m.implemented = TRUE)
            AS implemented_controls

    FROM risks r

    LEFT JOIN risk_control_mapping m
        ON m.risk_id = r.risk_id

    GROUP BY r.risk_id, r.risk_code, r.title
)

SELECT *
FROM control_summary
WHERE implemented_controls = 0
ORDER BY risk_code;


-- ============================================================
-- 38. SAMPLE TRANSACTION: REASSESS A RISK
-- ============================================================

BEGIN;

INSERT INTO risk_assessments (
    risk_id,
    assessment_version,
    probability,
    impact_amount,
    assessor_id,
    rationale,
    assessment_type
)
VALUES (
    3,
    2,
    0.250000,
    90000,
    7,
    'Updated assessment after infrastructure review.',
    'REASSESSMENT'
);

UPDATE risks
SET status = 'ASSESSED'
WHERE risk_id = 3;

INSERT INTO risk_audit_log (
    risk_id,
    event_type,
    actor_id,
    event_details
)
VALUES (
    3,
    'RISK_REASSESSED',
    7,
    jsonb_build_object(
        'new_probability', 0.25,
        'new_impact', 90000,
        'assessment_version', 2
    )
);

COMMIT;


-- ============================================================
-- 39. APPROVAL WORKFLOW EXAMPLE
--
-- R005 has sufficiently low exposure for acceptance.
-- ============================================================

BEGIN;

CALL request_risk_acceptance(5);

INSERT INTO risk_approvals (
    risk_id,
    approver_id,
    decision,
    justification
)
VALUES (
    5,
    6,
    'PENDING',
    'Low residual exposure submitted for committee review.'
);

COMMIT;


-- ============================================================
-- 40. RECORD AN APPROVAL DECISION
-- ============================================================

BEGIN;

CALL decide_risk_approval(
    (
        SELECT approval_id
        FROM risk_approvals
        WHERE risk_id = 5
          AND decision = 'PENDING'
    ),
    'APPROVED',
    'Residual exposure satisfies the approved risk tolerance.'
);

COMMIT;


-- ============================================================
-- 41. AUDIT TRAIL REPORT
-- ============================================================

SELECT
    a.audit_id,
    r.risk_code,
    r.title,
    a.event_type,
    u.full_name AS actor,
    a.event_details,
    a.created_at

FROM risk_audit_log a

JOIN risks r
    ON r.risk_id = a.risk_id

LEFT JOIN risk_users u
    ON u.user_id = a.actor_id

ORDER BY a.created_at DESC;


-- ============================================================
-- 42. FINAL RISK MANAGEMENT DASHBOARD
-- ============================================================

SELECT
    COUNT(*) AS total_registered_risks,

    COUNT(*) FILTER (
        WHERE status = 'ACCEPTED'
    ) AS accepted_risks,

    COUNT(*) FILTER (
        WHERE status = 'MITIGATING'
    ) AS risks_under_mitigation,

    COUNT(*) FILTER (
        WHERE status = 'PENDING_APPROVAL'
    ) AS pending_approvals,

    COUNT(*) FILTER (
        WHERE risk_level = 'CRITICAL'
    ) AS critical_risks,

    COUNT(*) FILTER (
        WHERE risk_level = 'HIGH'
    ) AS high_risks,

    ROUND(SUM(inherent_exposure), 2)
        AS portfolio_inherent_exposure,

    ROUND(SUM(residual_exposure), 2)
        AS portfolio_residual_exposure

FROM current_risk_exposure;


-- ============================================================
-- END OF RISK ANALYSIS DATABASE
-- ============================================================
