-- ============================================================
-- ENTERPRISE RISK REGISTER MANAGEMENT SYSTEM
-- PostgreSQL 15+
--
-- Scope:
-- Risk identification, assessment, treatment, residual risk,
-- ownership, controls, reviews, escalation and reporting.
--
-- Risk score = Probability * Impact
-- Probability and Impact range from 1 to 5.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS risk_management;

SET search_path TO risk_management, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE risk_category AS ENUM (
    'STRATEGIC',
    'OPERATIONAL',
    'FINANCIAL',
    'TECHNOLOGICAL',
    'CYBERSECURITY',
    'COMPLIANCE',
    'REPUTATIONAL',
    'PROJECT',
    'ENVIRONMENTAL'
);

CREATE TYPE risk_status AS ENUM (
    'IDENTIFIED',
    'ASSESSED',
    'TREATMENT_PLANNED',
    'IN_PROGRESS',
    'MONITORING',
    'ACCEPTED',
    'CLOSED'
);

CREATE TYPE risk_response AS ENUM (
    'AVOID',
    'MITIGATE',
    'TRANSFER',
    'ACCEPT'
);

CREATE TYPE risk_level AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);

CREATE TYPE review_type AS ENUM (
    'PERIODIC',
    'EVENT_DRIVEN',
    'POST_INCIDENT'
);

-- ------------------------------------------------------------
-- 2. ORGANISATIONAL STRUCTURE
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
    job_title VARCHAR(120) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_employees_department
    ON employees(department_id);

-- ------------------------------------------------------------
-- 3. RISK REGISTER
-- ------------------------------------------------------------

CREATE TABLE risk_registers (
    register_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    register_name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    register_owner BIGINT REFERENCES employees(employee_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    register_id BIGINT NOT NULL
        REFERENCES risk_registers(register_id),

    risk_code VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    category risk_category NOT NULL,
    status risk_status NOT NULL DEFAULT 'IDENTIFIED',
    response_strategy risk_response NOT NULL DEFAULT 'MITIGATE',

    risk_owner BIGINT NOT NULL
        REFERENCES employees(employee_id),

    identified_date DATE NOT NULL DEFAULT CURRENT_DATE,
    target_date DATE,
    closed_at TIMESTAMPTZ,

    version INTEGER NOT NULL DEFAULT 1,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_risk_register_code
        UNIQUE (register_id, risk_code),

    CONSTRAINT chk_risk_target_date
        CHECK (
            target_date IS NULL OR target_date >= identified_date
        ),

    CONSTRAINT chk_risk_version
        CHECK (version > 0),

    CONSTRAINT chk_risk_closure
        CHECK (
            (status = 'CLOSED' AND closed_at IS NOT NULL)
            OR
            (status <> 'CLOSED' AND closed_at IS NULL)
        )
);

CREATE INDEX idx_risks_register
    ON risks(register_id);

CREATE INDEX idx_risks_owner_status
    ON risks(risk_owner, status);

CREATE INDEX idx_risks_category
    ON risks(category);

CREATE INDEX idx_risks_open_target
    ON risks(target_date)
    WHERE status <> 'CLOSED';

CREATE INDEX idx_risks_priority
    ON risks(register_id, status, risk_code);

-- ------------------------------------------------------------
-- 4. RISK ASSESSMENTS
-- ------------------------------------------------------------

CREATE TABLE risk_assessments (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    assessment_type VARCHAR(12) NOT NULL
        CHECK (assessment_type IN ('INHERENT', 'RESIDUAL')),

    probability SMALLINT NOT NULL
        CHECK (probability BETWEEN 1 AND 5),

    impact SMALLINT NOT NULL
        CHECK (impact BETWEEN 1 AND 5),

    risk_score INTEGER GENERATED ALWAYS AS
        (probability * impact) STORED,

    risk_level risk_level GENERATED ALWAYS AS (
        CASE
            WHEN probability * impact >= 20 THEN 'CRITICAL'::risk_level
            WHEN probability * impact >= 12 THEN 'HIGH'::risk_level
            WHEN probability * impact >= 6 THEN 'MEDIUM'::risk_level
            ELSE 'LOW'::risk_level
        END
    ) STORED,

    assessed_by BIGINT NOT NULL
        REFERENCES employees(employee_id),

    assessment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    rationale TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assessments_risk_type_date
    ON risk_assessments(
        risk_id,
        assessment_type,
        assessment_date DESC,
        assessment_id DESC
    );

CREATE INDEX idx_assessments_score
    ON risk_assessments(risk_level, risk_score);

-- ------------------------------------------------------------
-- 5. RISK TREATMENT PLANS
-- ------------------------------------------------------------

CREATE TABLE treatment_plans (
    treatment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    treatment_strategy risk_response NOT NULL,

    treatment_description TEXT NOT NULL,

    treatment_owner BIGINT NOT NULL
        REFERENCES employees(employee_id),

    planned_start_date DATE,
    target_completion_date DATE,

    completion_percentage NUMERIC(5,2) NOT NULL DEFAULT 0
        CHECK (completion_percentage BETWEEN 0 AND 100),

    implementation_status VARCHAR(20) NOT NULL DEFAULT 'PLANNED'
        CHECK (
            implementation_status IN (
                'PLANNED',
                'IN_PROGRESS',
                'COMPLETED',
                'CANCELLED'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_treatment_dates
        CHECK (
            planned_start_date IS NULL
            OR target_completion_date IS NULL
            OR target_completion_date >= planned_start_date
        ),

    CONSTRAINT chk_treatment_completion
        CHECK (
            implementation_status <> 'COMPLETED'
            OR completion_percentage = 100
        )
);

CREATE INDEX idx_treatment_owner_status
    ON treatment_plans(treatment_owner, implementation_status);

CREATE INDEX idx_treatment_risk
    ON treatment_plans(risk_id);

-- ------------------------------------------------------------
-- 6. RISK CONTROLS
-- ------------------------------------------------------------

CREATE TABLE controls (
    control_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    control_code VARCHAR(40) NOT NULL UNIQUE,
    control_name VARCHAR(180) NOT NULL,
    description TEXT,
    control_owner BIGINT REFERENCES employees(employee_id),

    control_type VARCHAR(20) NOT NULL
        CHECK (
            control_type IN (
                'PREVENTIVE',
                'DETECTIVE',
                'CORRECTIVE',
                'COMPENSATING'
            )
        ),

    effectiveness_rating SMALLINT
        CHECK (effectiveness_rating BETWEEN 1 AND 5),

    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE risk_controls (
    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    control_id BIGINT NOT NULL
        REFERENCES controls(control_id),

    implementation_status VARCHAR(20) NOT NULL DEFAULT 'PLANNED'
        CHECK (
            implementation_status IN (
                'PLANNED',
                'IMPLEMENTED',
                'INEFFECTIVE',
                'RETIRED'
            )
        ),

    implemented_date DATE,
    effectiveness_notes TEXT,

    PRIMARY KEY (risk_id, control_id)
);

CREATE INDEX idx_risk_controls_control
    ON risk_controls(control_id, implementation_status);

-- ------------------------------------------------------------
-- 7. RISK REVIEWS
-- ------------------------------------------------------------

CREATE TABLE risk_reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    reviewer_id BIGINT NOT NULL
        REFERENCES employees(employee_id),

    review_category review_type NOT NULL,

    review_date DATE NOT NULL DEFAULT CURRENT_DATE,

    findings TEXT NOT NULL,
    recommendations TEXT,

    next_review_date DATE,

    CONSTRAINT chk_review_schedule
        CHECK (
            next_review_date IS NULL
            OR next_review_date >= review_date
        )
);

CREATE INDEX idx_reviews_risk_date
    ON risk_reviews(risk_id, review_date DESC);

-- ------------------------------------------------------------
-- 8. RISK ACCEPTANCE AND APPROVAL
-- ------------------------------------------------------------

CREATE TABLE risk_acceptances (
    acceptance_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    requested_by BIGINT NOT NULL
        REFERENCES employees(employee_id),

    approved_by BIGINT
        REFERENCES employees(employee_id),

    justification TEXT NOT NULL,

    approval_status VARCHAR(15) NOT NULL DEFAULT 'PENDING'
        CHECK (
            approval_status IN (
                'PENDING',
                'APPROVED',
                'REJECTED',
                'REVOKED'
            )
        ),

    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMPTZ,

    CONSTRAINT chk_acceptance_decision
        CHECK (
            (approval_status = 'PENDING'
                AND decided_at IS NULL
                AND approved_by IS NULL)
            OR
            (approval_status <> 'PENDING'
                AND decided_at IS NOT NULL
                AND approved_by IS NOT NULL)
        ),

    CONSTRAINT chk_acceptance_approver
        CHECK (requested_by <> approved_by OR approved_by IS NULL)
);

CREATE INDEX idx_acceptance_risk_status
    ON risk_acceptances(risk_id, approval_status);

-- ------------------------------------------------------------
-- 9. AUDIT LOG
-- ------------------------------------------------------------

CREATE TABLE risk_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL REFERENCES risks(risk_id),

    action VARCHAR(40) NOT NULL,
    previous_status risk_status,
    new_status risk_status,

    performed_by BIGINT REFERENCES employees(employee_id),

    details JSONB NOT NULL DEFAULT '{}'::JSONB,

    performed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_risk_time
    ON risk_audit_log(risk_id, performed_at DESC);

-- ------------------------------------------------------------
-- 10. STATUS VALIDATION AND AUDIT TRIGGER
-- ------------------------------------------------------------

CREATE FUNCTION validate_risk_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN

        IF OLD.status = 'CLOSED'
           AND NEW.status <> 'IDENTIFIED' THEN
            RAISE EXCEPTION
                'Closed risks can only be reopened as IDENTIFIED.';
        END IF;

        IF NEW.status <> OLD.status THEN
            IF NOT (
                (OLD.status = 'IDENTIFIED'
                    AND NEW.status IN ('ASSESSED', 'CLOSED'))
                OR
                (OLD.status = 'ASSESSED'
                    AND NEW.status IN (
                        'TREATMENT_PLANNED', 'ACCEPTED', 'CLOSED'
                    ))
                OR
                (OLD.status = 'TREATMENT_PLANNED'
                    AND NEW.status IN (
                        'IN_PROGRESS', 'ACCEPTED', 'CLOSED'
                    ))
                OR
                (OLD.status = 'IN_PROGRESS'
                    AND NEW.status IN (
                        'MONITORING', 'TREATMENT_PLANNED', 'CLOSED'
                    ))
                OR
                (OLD.status = 'MONITORING'
                    AND NEW.status IN (
                        'IN_PROGRESS', 'ACCEPTED', 'CLOSED'
                    ))
                OR
                (OLD.status = 'ACCEPTED'
                    AND NEW.status IN ('MONITORING', 'CLOSED'))
                OR
                (OLD.status = 'CLOSED'
                    AND NEW.status = 'IDENTIFIED')
            ) THEN
                RAISE EXCEPTION
                    'Invalid risk status transition: % -> %',
                    OLD.status, NEW.status;
            END IF;
        END IF;

        NEW.version := OLD.version + 1;
        NEW.updated_at := CURRENT_TIMESTAMP;

        IF NEW.status = 'CLOSED' THEN
            NEW.closed_at := CURRENT_TIMESTAMP;
        ELSE
            NEW.closed_at := NULL;
        END IF;

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_risk_status
BEFORE UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION validate_risk_status();

CREATE FUNCTION audit_risk_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    old_status risk_status;
    new_status risk_status;
    current_risk_id BIGINT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        current_risk_id := NEW.risk_id;
        new_status := NEW.status;
        old_status := NULL;

    ELSIF TG_OP = 'UPDATE' THEN
        current_risk_id := NEW.risk_id;
        new_status := NEW.status;
        old_status := OLD.status;
    END IF;

    INSERT INTO risk_audit_log (
        risk_id,
        action,
        previous_status,
        new_status,
        details
    )
    VALUES (
        current_risk_id,
        TG_OP,
        old_status,
        new_status,
        jsonb_build_object(
            'risk_code', NEW.risk_code,
            'title', NEW.title,
            'category', NEW.category,
            'version', NEW.version
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_risk_audit
AFTER INSERT OR UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION audit_risk_changes();

-- ------------------------------------------------------------
-- 11. GOVERNANCE POLICIES
-- ------------------------------------------------------------

CREATE TABLE governance_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    register_id BIGINT NOT NULL UNIQUE
        REFERENCES risk_registers(register_id),

    minimum_treatment_score INTEGER NOT NULL DEFAULT 12
        CHECK (minimum_treatment_score BETWEEN 1 AND 25),

    critical_escalation_score INTEGER NOT NULL DEFAULT 20
        CHECK (critical_escalation_score BETWEEN 1 AND 25),

    require_treatment_plan BOOLEAN NOT NULL DEFAULT TRUE,

    require_residual_assessment BOOLEAN NOT NULL DEFAULT TRUE,

    require_approval_for_acceptance BOOLEAN NOT NULL DEFAULT TRUE,

    require_active_control_for_mitigation BOOLEAN NOT NULL DEFAULT FALSE,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        critical_escalation_score >= minimum_treatment_score
    )
);

-- ------------------------------------------------------------
-- 12. HELPER FUNCTIONS
-- ------------------------------------------------------------

CREATE FUNCTION get_latest_risk_score(
    p_risk_id BIGINT,
    p_assessment_type VARCHAR
)
RETURNS INTEGER
LANGUAGE SQL
STABLE
AS $$
    SELECT risk_score
    FROM risk_assessments
    WHERE risk_id = p_risk_id
      AND assessment_type = p_assessment_type
    ORDER BY assessment_date DESC, assessment_id DESC
    LIMIT 1;
$$;

CREATE FUNCTION evaluate_risk_eligibility(
    p_risk_id BIGINT
)
RETURNS TABLE (
    evaluated_risk_id BIGINT,
    inherent_score INTEGER,
    residual_score INTEGER,
    eligibility_status TEXT,
    blockers TEXT[]
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_risk risks%ROWTYPE;
    v_policy governance_policies%ROWTYPE;
    v_inherent INTEGER;
    v_residual INTEGER;
    v_blockers TEXT[] := ARRAY[]::TEXT[];
    v_approval BOOLEAN;
    v_control BOOLEAN;
BEGIN
    SELECT *
    INTO v_risk
    FROM risks
    WHERE risk_id = p_risk_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk % not found.', p_risk_id;
    END IF;

    SELECT *
    INTO v_policy
    FROM governance_policies
    WHERE register_id = v_risk.register_id;

    v_inherent := get_latest_risk_score(
        p_risk_id, 'INHERENT'
    );

    v_residual := get_latest_risk_score(
        p_risk_id, 'RESIDUAL'
    );

    IF v_inherent IS NULL THEN
        v_blockers := array_append(
            v_blockers,
            'Initial inherent assessment is missing.'
        );
    END IF;

    IF v_inherent IS NOT NULL
       AND v_inherent >= v_policy.critical_escalation_score THEN
        v_blockers := array_append(
            v_blockers,
            'Critical inherent risk requires escalation.'
        );
    END IF;

    IF v_inherent IS NOT NULL
       AND v_inherent >= v_policy.minimum_treatment_score
       AND v_risk.response_strategy = 'MITIGATE'
       AND v_policy.require_treatment_plan
       AND NOT EXISTS (
            SELECT 1
            FROM treatment_plans tp
            WHERE tp.risk_id = p_risk_id
              AND tp.implementation_status <> 'CANCELLED'
       ) THEN
        v_blockers := array_append(
            v_blockers,
            'A valid mitigation plan is required.'
        );
    END IF;

    IF v_policy.require_residual_assessment
       AND v_risk.status = 'MONITORING'
       AND v_residual IS NULL THEN
        v_blockers := array_append(
            v_blockers,
            'Residual assessment is required.'
        );
    END IF;

    IF v_risk.response_strategy = 'ACCEPT' THEN
        SELECT EXISTS (
            SELECT 1
            FROM risk_acceptances ra
            WHERE ra.risk_id = p_risk_id
              AND ra.approval_status = 'APPROVED'
        )
        INTO v_approval;

        IF v_policy.require_approval_for_acceptance
           AND NOT v_approval THEN
            v_blockers := array_append(
                v_blockers,
                'Formal risk acceptance approval is missing.'
            );
        END IF;
    END IF;

    IF v_policy.require_active_control_for_mitigation
       AND v_risk.response_strategy = 'MITIGATE' THEN

        SELECT EXISTS (
            SELECT 1
            FROM risk_controls rc
            JOIN controls c
              ON c.control_id = rc.control_id
            WHERE rc.risk_id = p_risk_id
              AND rc.implementation_status = 'IMPLEMENTED'
              AND c.is_active
        )
        INTO v_control;

        IF NOT v_control THEN
            v_blockers := array_append(
                v_blockers,
                'At least one active implemented control is required.'
            );
        END IF;
    END IF;

    RETURN QUERY
    SELECT
        p_risk_id,
        v_inherent,
        v_residual,
        CASE
            WHEN cardinality(v_blockers) = 0
                THEN 'ELIGIBLE'
            ELSE 'BLOCKED'
        END,
        v_blockers;
END;
$$;

-- ------------------------------------------------------------
-- 13. RISK REGISTER REPORTING VIEW
-- ------------------------------------------------------------

CREATE VIEW risk_register_report AS
SELECT
    r.risk_id,
    rr.register_name,
    r.risk_code,
    r.title,
    r.category,
    r.status,
    r.response_strategy,
    e.employee_name AS risk_owner,

    inherent.risk_score AS inherent_score,
    inherent.risk_level AS inherent_level,

    residual.risk_score AS residual_score,
    residual.risk_level AS residual_level,

    latest_plan.treatment_description,
    latest_plan.completion_percentage,
    treatment_owner.employee_name AS treatment_owner,

    r.target_date,
    r.version,
    r.created_at,
    r.updated_at

FROM risks r

JOIN risk_registers rr
    ON rr.register_id = r.register_id

JOIN employees e
    ON e.employee_id = r.risk_owner

LEFT JOIN LATERAL (
    SELECT a.risk_score, a.risk_level
    FROM risk_assessments a
    WHERE a.risk_id = r.risk_id
      AND a.assessment_type = 'INHERENT'
    ORDER BY a.assessment_date DESC, a.assessment_id DESC
    LIMIT 1
) inherent ON TRUE

LEFT JOIN LATERAL (
    SELECT a.risk_score, a.risk_level
    FROM risk_assessments a
    WHERE a.risk_id = r.risk_id
      AND a.assessment_type = 'RESIDUAL'
    ORDER BY a.assessment_date DESC, a.assessment_id DESC
    LIMIT 1
) residual ON TRUE

LEFT JOIN LATERAL (
    SELECT
        tp.treatment_description,
        tp.completion_percentage,
        tp.treatment_owner
    FROM treatment_plans tp
    WHERE tp.risk_id = r.risk_id
      AND tp.implementation_status <> 'CANCELLED'
    ORDER BY tp.created_at DESC, tp.treatment_id DESC
    LIMIT 1
) latest_plan ON TRUE

LEFT JOIN employees treatment_owner
    ON treatment_owner.employee_id = latest_plan.treatment_owner;

-- ------------------------------------------------------------
-- 14. SAMPLE ORGANISATION
-- ------------------------------------------------------------

INSERT INTO departments (department_name)
VALUES
    ('Information Security'),
    ('Operations'),
    ('Finance'),
    ('Compliance'),
    ('Project Management');

INSERT INTO employees (
    employee_name,
    email,
    department_id,
    job_title
)
SELECT
    sample.employee_name,
    sample.email,
    d.department_id,
    sample.job_title
FROM (
    VALUES
        ('Aarav Sharma', 'aarav@example.org',
            'Information Security', 'Security Director'),
        ('Meera Verma', 'meera@example.org',
            'Operations', 'Operations Manager'),
        ('Rahul Singh', 'rahul@example.org',
            'Finance', 'Finance Controller'),
        ('Ananya Gupta', 'ananya@example.org',
            'Compliance', 'Compliance Officer'),
        ('Vikram Rao', 'vikram@example.org',
            'Project Management', 'Project Manager')
) AS sample(employee_name, email, department_name, job_title)
JOIN departments d
    ON d.department_name = sample.department_name;

INSERT INTO risk_registers (
    register_name,
    description,
    register_owner
)
SELECT
    'Enterprise Technology Risk Register',
    'Central register for enterprise technology and operational risks.',
    employee_id
FROM employees
WHERE email = 'aarav@example.org';

INSERT INTO governance_policies (register_id)
SELECT register_id
FROM risk_registers
WHERE register_name = 'Enterprise Technology Risk Register';

-- ------------------------------------------------------------
-- 15. SAMPLE RISKS
-- ------------------------------------------------------------

INSERT INTO risks (
    register_id,
    risk_code,
    title,
    description,
    category,
    response_strategy,
    risk_owner,
    identified_date,
    target_date
)
SELECT
    rr.register_id,
    sample.risk_code,
    sample.title,
    sample.description,
    sample.category::risk_category,
    sample.response::risk_response,
    e.employee_id,
    DATE '2026-11-25',
    sample.target_date
FROM (
    VALUES
        (
            'R-001',
            'Ransomware attack',
            'Malware may disrupt business-critical infrastructure.',
            'CYBERSECURITY',
            'MITIGATE',
            'aarav@example.org',
            DATE '2026-12-25'
        ),
        (
            'R-002',
            'Supplier delivery failure',
            'A critical supplier may fail to meet delivery commitments.',
            'OPERATIONAL',
            'MITIGATE',
            'meera@example.org',
            DATE '2027-01-15'
        ),
        (
            'R-003',
            'Budget overrun',
            'Unplanned expenditure may exceed approved budget.',
            'FINANCIAL',
            'TRANSFER',
            'rahul@example.org',
            DATE '2027-01-25'
        ),
        (
            'R-004',
            'Regulatory non-compliance',
            'Regulatory changes may not be reflected in operational policies.',
            'COMPLIANCE',
            'MITIGATE',
            'ananya@example.org',
            DATE '2026-12-20'
        )
) AS sample(
    risk_code,
    title,
    description,
    category,
    response,
    owner_email,
    target_date
)
JOIN risk_registers rr
    ON rr.register_name = 'Enterprise Technology Risk Register'
JOIN employees e
    ON e.email = sample.owner_email;

-- ------------------------------------------------------------
-- 16. SAMPLE ASSESSMENTS
-- ------------------------------------------------------------

INSERT INTO risk_assessments (
    risk_id,
    assessment_type,
    probability,
    impact,
    assessed_by,
    assessment_date,
    rationale
)
SELECT
    r.risk_id,
    sample.assessment_type,
    sample.probability,
    sample.impact,
    e.employee_id,
    DATE '2026-11-25',
    sample.rationale
FROM (
    VALUES
        ('R-001', 'INHERENT', 4, 5,
            'aarav@example.org', 'High impact on confidentiality and availability.'),
        ('R-001', 'RESIDUAL', 2, 3,
            'aarav@example.org', 'Controls reduce likelihood and impact.'),
        ('R-002', 'INHERENT', 3, 4,
            'meera@example.org', 'Supplier dependency may delay operations.'),
        ('R-003', 'INHERENT', 3, 3,
            'rahul@example.org', 'Financial exposure from unexpected expenditure.'),
        ('R-004', 'INHERENT', 3, 5,
            'ananya@example.org', 'Potential regulatory and legal consequences.')
) AS sample(
    risk_code,
    assessment_type,
    probability,
    impact,
    assessor_email,
    rationale
)
JOIN risks r
    ON r.risk_code = sample.risk_code
JOIN employees e
    ON e.email = sample.assessor_email;

-- ------------------------------------------------------------
-- 17. TREATMENT PLANS
-- ------------------------------------------------------------

INSERT INTO treatment_plans (
    risk_id,
    treatment_strategy,
    treatment_description,
    treatment_owner,
    planned_start_date,
    target_completion_date,
    completion_percentage,
    implementation_status
)
SELECT
    r.risk_id,
    'MITIGATE',
    'Deploy endpoint detection, MFA and immutable backups.',
    e.employee_id,
    DATE '2026-11-25',
    DATE '2026-12-25',
    40,
    'IN_PROGRESS'
FROM risks r
JOIN employees e
    ON e.email = 'aarav@example.org'
WHERE r.risk_code = 'R-001';

INSERT INTO treatment_plans (
    risk_id,
    treatment_strategy,
    treatment_description,
    treatment_owner,
    planned_start_date,
    target_completion_date,
    completion_percentage,
    implementation_status
)
SELECT
    r.risk_id,
    'MITIGATE',
    'Qualify alternative suppliers and establish service agreements.',
    e.employee_id,
    DATE '2026-11-25',
    DATE '2027-01-15',
    10,
    'IN_PROGRESS'
FROM risks r
JOIN employees e
    ON e.email = 'meera@example.org'
WHERE r.risk_code = 'R-002';

-- ------------------------------------------------------------
-- 18. CONTROLS AND RISK ASSOCIATIONS
-- ------------------------------------------------------------

INSERT INTO controls (
    control_code,
    control_name,
    description,
    control_owner,
    control_type,
    effectiveness_rating
)
SELECT
    sample.control_code,
    sample.control_name,
    sample.description,
    e.employee_id,
    sample.control_type,
    sample.effectiveness
FROM (
    VALUES
        ('CTRL-001', 'Multi-factor authentication',
            'Enforces additional authentication factors.',
            'aarav@example.org', 'PREVENTIVE', 4),
        ('CTRL-002', 'Endpoint detection',
            'Detects malicious endpoint behaviour.',
            'aarav@example.org', 'DETECTIVE', 4),
        ('CTRL-003', 'Immutable backups',
            'Protects backup copies against unauthorised alteration.',
            'aarav@example.org', 'CORRECTIVE', 5)
) AS sample(
    control_code,
    control_name,
    description,
    owner_email,
    control_type,
    effectiveness
)
JOIN employees e
    ON e.email = sample.owner_email;

INSERT INTO risk_controls (
    risk_id,
    control_id,
    implementation_status,
    implemented_date,
    effectiveness_notes
)
SELECT
    r.risk_id,
    c.control_id,
    'IMPLEMENTED',
    DATE '2026-11-25',
    'Control deployment verified during the security review.'
FROM risks r
CROSS JOIN controls c
WHERE r.risk_code = 'R-001'
AND c.control_code IN ('CTRL-001', 'CTRL-002', 'CTRL-003');

-- ------------------------------------------------------------
-- 19. SAMPLE REVIEWS
-- ------------------------------------------------------------

INSERT INTO risk_reviews (
    risk_id,
    reviewer_id,
    review_category,
    review_date,
    findings,
    recommendations,
    next_review_date
)
SELECT
    r.risk_id,
    e.employee_id,
    'PERIODIC',
    DATE '2026-11-25',
    'Security control implementation reviewed.',
    'Verify backup restoration and MFA coverage.',
    DATE '2026-12-25'
FROM risks r
JOIN employees e
    ON e.email = 'aarav@example.org'
WHERE r.risk_code = 'R-001';

-- ------------------------------------------------------------
-- 20. STATUS TRANSITIONS
-- ------------------------------------------------------------

UPDATE risks
SET status = 'ASSESSED'
WHERE risk_code = 'R-001';

UPDATE risks
SET status = 'TREATMENT_PLANNED'
WHERE risk_code = 'R-001';

UPDATE risks
SET status = 'IN_PROGRESS'
WHERE risk_code = 'R-001';

UPDATE risks
SET status = 'MONITORING'
WHERE risk_code = 'R-001';

UPDATE risks
SET status = 'ASSESSED'
WHERE risk_code = 'R-002';

UPDATE risks
SET status = 'TREATMENT_PLANNED'
WHERE risk_code = 'R-002';

UPDATE risks
SET status = 'IN_PROGRESS'
WHERE risk_code = 'R-002';

-- ------------------------------------------------------------
-- 21. TRANSACTIONAL RISK ASSESSMENT PROCEDURE
-- ------------------------------------------------------------

CREATE PROCEDURE record_risk_assessment(
    p_risk_id BIGINT,
    p_type VARCHAR,
    p_probability INTEGER,
    p_impact INTEGER,
    p_assessor BIGINT,
    p_rationale TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_type NOT IN ('INHERENT', 'RESIDUAL') THEN
        RAISE EXCEPTION 'Invalid assessment type.';
    END IF;

    IF p_probability NOT BETWEEN 1 AND 5
       OR p_impact NOT BETWEEN 1 AND 5 THEN
        RAISE EXCEPTION
            'Probability and impact must be between 1 and 5.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM risks WHERE risk_id = p_risk_id
    ) THEN
        RAISE EXCEPTION 'Risk does not exist.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM employees
        WHERE employee_id = p_assessor
          AND is_active
    ) THEN
        RAISE EXCEPTION 'Assessor is inactive or does not exist.';
    END IF;

    IF p_rationale IS NULL OR btrim(p_rationale) = '' THEN
        RAISE EXCEPTION 'Assessment rationale is required.';
    END IF;

    INSERT INTO risk_assessments (
        risk_id,
        assessment_type,
        probability,
        impact,
        assessed_by,
        rationale
    )
    VALUES (
        p_risk_id,
        p_type,
        p_probability,
        p_impact,
        p_assessor,
        p_rationale
    );
END;
$$;

-- ------------------------------------------------------------
-- 22. RETRIEVAL AND PRIORITISATION
-- ------------------------------------------------------------

SELECT
    risk_code,
    title,
    category,
    risk_owner,
    inherent_score,
    inherent_level,
    status
FROM risk_register_report
ORDER BY
    inherent_score DESC NULLS LAST,
    risk_code;

-- ------------------------------------------------------------
-- 23. AGGREGATE RISK DISTRIBUTION
-- ------------------------------------------------------------

SELECT
    inherent_level,
    COUNT(*) AS risk_count,
    ROUND(AVG(inherent_score), 2) AS average_score
FROM risk_register_report
WHERE status <> 'CLOSED'
GROUP BY inherent_level
ORDER BY
    CASE inherent_level
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END;

-- ------------------------------------------------------------
-- 24. INHERENT VERSUS RESIDUAL RISK
-- ------------------------------------------------------------

SELECT
    risk_code,
    title,
    inherent_score,
    residual_score,
    inherent_score - residual_score AS score_reduction,
    inherent_level,
    residual_level
FROM risk_register_report
WHERE inherent_score IS NOT NULL
ORDER BY inherent_score DESC;

-- ------------------------------------------------------------
-- 25. OVERDUE RISK REPORT
-- ------------------------------------------------------------

SELECT
    risk_code,
    title,
    risk_owner,
    target_date,
    CURRENT_DATE - target_date AS days_overdue,
    status
FROM risk_register_report
WHERE target_date < CURRENT_DATE
  AND status <> 'CLOSED'
ORDER BY target_date;

-- ------------------------------------------------------------
-- 26. TREATMENT IMPLEMENTATION REPORT
-- ------------------------------------------------------------

SELECT
    r.risk_code,
    r.title,
    tp.treatment_description,
    tp.implementation_status,
    tp.completion_percentage,
    e.employee_name AS treatment_owner
FROM risks r
JOIN treatment_plans tp
    ON tp.risk_id = r.risk_id
JOIN employees e
    ON e.employee_id = tp.treatment_owner
ORDER BY tp.completion_percentage ASC;

-- ------------------------------------------------------------
-- 27. CONTROL COVERAGE
-- ------------------------------------------------------------

SELECT
    r.risk_code,
    r.title,
    COUNT(rc.control_id) AS total_associated_controls,
    COUNT(*) FILTER (
        WHERE rc.implementation_status = 'IMPLEMENTED'
    ) AS implemented_controls,
    COUNT(*) FILTER (
        WHERE rc.implementation_status = 'INEFFECTIVE'
    ) AS ineffective_controls
FROM risks r
LEFT JOIN risk_controls rc
    ON rc.risk_id = r.risk_id
GROUP BY r.risk_id, r.risk_code, r.title
ORDER BY r.risk_code;

-- ------------------------------------------------------------
-- 28. GOVERNANCE ELIGIBILITY REPORT
-- ------------------------------------------------------------

SELECT
    r.risk_code,
    r.title,
    evaluation.inherent_score,
    evaluation.residual_score,
    evaluation.eligibility_status,
    evaluation.blockers
FROM risks r
CROSS JOIN LATERAL
    evaluate_risk_eligibility(r.risk_id) evaluation
ORDER BY r.risk_code;

-- ------------------------------------------------------------
-- 29. CTE: HIGH-PRIORITY RISK DASHBOARD
-- ------------------------------------------------------------

WITH ranked_risks AS (
    SELECT
        r.risk_id,
        r.risk_code,
        r.title,
        a.risk_score,
        a.risk_level,
        ROW_NUMBER() OVER (
            ORDER BY a.risk_score DESC, r.risk_code
        ) AS priority_rank
    FROM risks r
    JOIN LATERAL (
        SELECT risk_score, risk_level
        FROM risk_assessments
        WHERE risk_id = r.risk_id
          AND assessment_type = 'INHERENT'
        ORDER BY assessment_date DESC, assessment_id DESC
        LIMIT 1
    ) a ON TRUE
    WHERE r.status <> 'CLOSED'
)
SELECT *
FROM ranked_risks
WHERE risk_level IN ('HIGH', 'CRITICAL')
ORDER BY priority_rank;

-- ------------------------------------------------------------
-- 30. AUDIT HISTORY
-- ------------------------------------------------------------

SELECT
    a.audit_id,
    r.risk_code,
    a.action,
    a.previous_status,
    a.new_status,
    a.details,
    a.performed_at
FROM risk_audit_log a
JOIN risks r
    ON r.risk_id = a.risk_id
ORDER BY a.performed_at DESC, a.audit_id DESC;

-- ------------------------------------------------------------
-- 31. TRANSACTIONAL ASSESSMENT EXAMPLE
-- ------------------------------------------------------------

DO $$
DECLARE
    v_risk_id BIGINT;
    v_assessor BIGINT;
BEGIN
    SELECT risk_id
    INTO v_risk_id
    FROM risks
    WHERE risk_code = 'R-002';

    SELECT employee_id
    INTO v_assessor
    FROM employees
    WHERE email = 'meera@example.org';

    CALL record_risk_assessment(
        v_risk_id,
        'RESIDUAL',
        2,
        3,
        v_assessor,
        'Supplier alternatives and contractual controls reduce exposure.'
    );
END;
$$;

-- ------------------------------------------------------------
-- 32. DATA QUALITY VALIDATION
-- ------------------------------------------------------------

-- Risks without inherent assessments.
SELECT r.risk_code, r.title
FROM risks r
WHERE NOT EXISTS (
    SELECT 1
    FROM risk_assessments a
    WHERE a.risk_id = r.risk_id
      AND a.assessment_type = 'INHERENT'
);

-- Mitigation risks without active treatment plans.
SELECT r.risk_code, r.title
FROM risks r
WHERE r.response_strategy = 'MITIGATE'
AND NOT EXISTS (
    SELECT 1
    FROM treatment_plans tp
    WHERE tp.risk_id = r.risk_id
      AND tp.implementation_status <> 'CANCELLED'
);

-- Risks with ineffective controls.
SELECT
    r.risk_code,
    r.title,
    c.control_name
FROM risks r
JOIN risk_controls rc
    ON rc.risk_id = r.risk_id
JOIN controls c
    ON c.control_id = rc.control_id
WHERE rc.implementation_status = 'INEFFECTIVE';

-- ------------------------------------------------------------
-- 33. TRANSACTION COMPLETION
-- ------------------------------------------------------------

COMMIT;

-- Production deployment considerations:
-- 1. Restrict table writes through role-based database privileges.
-- 2. Separate risk creation, approval and closure permissions.
-- 3. Record authenticated actor identity in audit records.
-- 4. Use transactions for multi-step risk lifecycle operations.
-- 5. Back up risk assessments and audit history.
-- 6. Review indexes using EXPLAIN (ANALYZE, BUFFERS).
-- 7. Use immutable audit storage where regulatory retention applies.
