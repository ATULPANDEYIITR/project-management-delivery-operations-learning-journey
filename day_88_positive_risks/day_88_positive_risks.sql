-- ==============================================================
-- POSITIVE RISKS: PROJECT OPPORTUNITY MANAGEMENT DATABASE
-- PostgreSQL 14+
--
-- Relational model:
-- Projects
--   -> Opportunities
--   -> Opportunity Assessments
--   -> Response Plans
--   -> Actions
--   -> Monitoring Events
--   -> Realized Benefits
--   -> Portfolio Reporting
--
-- Positive risks are uncertain events that can create benefits.
-- They are distinct from threats, which create negative outcomes.
-- ==============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS project_opportunities;

SET search_path TO project_opportunities, public;

-- --------------------------------------------------------------
-- 1. DOMAIN TYPES
-- --------------------------------------------------------------

CREATE TYPE opportunity_category AS ENUM (
    'COST',
    'SCHEDULE',
    'QUALITY',
    'TECHNOLOGY',
    'RESOURCE',
    'BUSINESS',
    'STRATEGIC'
);

CREATE TYPE response_strategy AS ENUM (
    'EXPLOIT',
    'ENHANCE',
    'SHARE',
    'ACCEPT'
);

CREATE TYPE opportunity_status AS ENUM (
    'IDENTIFIED',
    'ASSESSED',
    'PLANNED',
    'IN_PROGRESS',
    'REALIZED',
    'CLOSED'
);

CREATE TYPE event_type AS ENUM (
    'IDENTIFIED',
    'ASSESSED',
    'PLAN_CREATED',
    'EXECUTION_STARTED',
    'PROBABILITY_UPDATED',
    'BENEFIT_REALIZED',
    'CLOSED'
);

-- --------------------------------------------------------------
-- 2. PROJECT AND ORGANIZATIONAL STRUCTURE
-- --------------------------------------------------------------

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code VARCHAR(30) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    project_manager VARCHAR(120) NOT NULL,
    approved_budget NUMERIC(15,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (approved_budget >= 0),
    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE project_members (
    member_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    member_name VARCHAR(120) NOT NULL,
    role_name VARCHAR(60) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE (project_id, member_name)
);

-- --------------------------------------------------------------
-- 3. OPPORTUNITY REGISTER
-- --------------------------------------------------------------

CREATE TABLE opportunities (
    opportunity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    opportunity_code VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    category opportunity_category NOT NULL,
    strategy response_strategy NOT NULL,

    owner_id BIGINT NOT NULL
        REFERENCES project_members(member_id),

    status opportunity_status NOT NULL DEFAULT 'IDENTIFIED',

    deadline DATE,

    identified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    closed_at TIMESTAMPTZ,

    UNIQUE (project_id, opportunity_code),

    CHECK (length(trim(title)) > 0),
    CHECK (length(trim(description)) > 0),

    CHECK (
        (status = 'CLOSED' AND closed_at IS NOT NULL)
        OR
        (status <> 'CLOSED' AND closed_at IS NULL)
    )
);

CREATE INDEX idx_opportunities_project_status
    ON opportunities(project_id, status);

CREATE INDEX idx_opportunities_owner
    ON opportunities(owner_id);

CREATE INDEX idx_opportunities_category
    ON opportunities(category);

-- --------------------------------------------------------------
-- 4. OPPORTUNITY ASSESSMENTS
-- --------------------------------------------------------------

CREATE TABLE opportunity_assessments (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    opportunity_id BIGINT NOT NULL
        REFERENCES opportunities(opportunity_id),

    probability NUMERIC(5,4) NOT NULL,
    financial_impact NUMERIC(15,2) NOT NULL,
    response_cost NUMERIC(15,2) NOT NULL DEFAULT 0,
    confidence NUMERIC(5,4) NOT NULL DEFAULT 1.0,

    assumptions TEXT,
    assessment_version INTEGER NOT NULL DEFAULT 1,

    assessed_by BIGINT REFERENCES project_members(member_id),

    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (opportunity_id, assessment_version),

    CHECK (probability BETWEEN 0 AND 1),
    CHECK (financial_impact >= 0),
    CHECK (response_cost >= 0),
    CHECK (confidence > 0 AND confidence <= 1),
    CHECK (assessment_version > 0)
);

CREATE INDEX idx_assessments_opportunity_latest
    ON opportunity_assessments(
        opportunity_id,
        assessment_version DESC
    );

-- --------------------------------------------------------------
-- 5. RESPONSE PLANS
-- --------------------------------------------------------------

CREATE TABLE response_plans (
    plan_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    opportunity_id BIGINT NOT NULL
        REFERENCES opportunities(opportunity_id),

    strategy response_strategy NOT NULL,
    action_description TEXT NOT NULL,

    responsible_member_id BIGINT NOT NULL
        REFERENCES project_members(member_id),

    planned_budget NUMERIC(15,2) NOT NULL DEFAULT 0,

    target_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (planned_budget >= 0),
    CHECK (length(trim(action_description)) > 0)
);

CREATE INDEX idx_response_plans_opportunity
    ON response_plans(opportunity_id, is_active);

-- --------------------------------------------------------------
-- 6. ACTION TRACKING
-- --------------------------------------------------------------

CREATE TABLE opportunity_actions (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    plan_id BIGINT NOT NULL
        REFERENCES response_plans(plan_id),

    action_title VARCHAR(200) NOT NULL,
    assigned_to BIGINT NOT NULL
        REFERENCES project_members(member_id),

    due_date DATE,

    completed BOOLEAN NOT NULL DEFAULT FALSE,

    completed_at TIMESTAMPTZ,

    CHECK (
        (completed = TRUE AND completed_at IS NOT NULL)
        OR
        (completed = FALSE AND completed_at IS NULL)
    )
);

CREATE INDEX idx_actions_open
    ON opportunity_actions(plan_id)
    WHERE completed = FALSE;

-- --------------------------------------------------------------
-- 7. MONITORING EVENTS
-- --------------------------------------------------------------

CREATE TABLE opportunity_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    opportunity_id BIGINT NOT NULL
        REFERENCES opportunities(opportunity_id),

    event event_type NOT NULL,

    event_description TEXT NOT NULL,

    recorded_by BIGINT REFERENCES project_members(member_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_opportunity_events_history
    ON opportunity_events(opportunity_id, created_at DESC);

-- --------------------------------------------------------------
-- 8. REALIZED BENEFITS
-- --------------------------------------------------------------

CREATE TABLE realized_benefits (
    benefit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    opportunity_id BIGINT NOT NULL
        REFERENCES opportunities(opportunity_id),

    benefit_amount NUMERIC(15,2) NOT NULL,

    realization_date DATE NOT NULL,

    verification_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    verification_reference VARCHAR(100),

    CHECK (benefit_amount >= 0),

    CHECK (
        verification_status IN (
            'PENDING',
            'VERIFIED',
            'REJECTED'
        )
    ),

    CHECK (
        verification_status <> 'VERIFIED'
        OR verification_reference IS NOT NULL
    )
);

CREATE INDEX idx_benefits_opportunity
    ON realized_benefits(opportunity_id, realization_date);

-- --------------------------------------------------------------
-- 9. OPPORTUNITY POLICY
-- --------------------------------------------------------------

CREATE TABLE opportunity_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL UNIQUE
        REFERENCES projects(project_id),

    minimum_probability NUMERIC(5,4) NOT NULL DEFAULT 0,

    minimum_net_value NUMERIC(15,2) NOT NULL DEFAULT 0,

    require_positive_net_value BOOLEAN NOT NULL DEFAULT TRUE,

    allow_exploit BOOLEAN NOT NULL DEFAULT TRUE,
    allow_enhance BOOLEAN NOT NULL DEFAULT TRUE,
    allow_share BOOLEAN NOT NULL DEFAULT TRUE,
    allow_accept BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (minimum_probability BETWEEN 0 AND 1)
);

-- --------------------------------------------------------------
-- 10. AUDIT AND STATE MANAGEMENT
-- --------------------------------------------------------------

CREATE OR REPLACE FUNCTION log_opportunity_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_event event_type;
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN

        CASE NEW.status
            WHEN 'ASSESSED' THEN
                v_event := 'ASSESSED';
            WHEN 'PLANNED' THEN
                v_event := 'PLAN_CREATED';
            WHEN 'IN_PROGRESS' THEN
                v_event := 'EXECUTION_STARTED';
            WHEN 'REALIZED' THEN
                v_event := 'BENEFIT_REALIZED';
            WHEN 'CLOSED' THEN
                v_event := 'CLOSED';
            ELSE
                v_event := 'IDENTIFIED';
        END CASE;

        INSERT INTO opportunity_events (
            opportunity_id,
            event,
            event_description
        )
        VALUES (
            NEW.opportunity_id,
            v_event,
            'Status changed from ' || OLD.status || ' to ' || NEW.status
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_opportunity_status
AFTER UPDATE OF status ON opportunities
FOR EACH ROW
EXECUTE FUNCTION log_opportunity_status();

-- Prevent unauthorized status transitions through the database.
CREATE OR REPLACE FUNCTION validate_opportunity_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'IDENTIFIED' AND
            NEW.status IN ('ASSESSED', 'PLANNED', 'CLOSED'))
        OR
        (OLD.status = 'ASSESSED' AND
            NEW.status IN ('PLANNED', 'CLOSED'))
        OR
        (OLD.status = 'PLANNED' AND
            NEW.status = 'IN_PROGRESS')
        OR
        (OLD.status = 'IN_PROGRESS' AND
            NEW.status = 'REALIZED')
        OR
        (OLD.status = 'REALIZED' AND
            NEW.status = 'CLOSED')
    ) THEN
        RAISE EXCEPTION
            'Invalid opportunity transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    IF NEW.status = 'CLOSED' THEN
        NEW.closed_at := CURRENT_TIMESTAMP;
    ELSE
        NEW.closed_at := NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_transition
BEFORE UPDATE OF status ON opportunities
FOR EACH ROW
EXECUTE FUNCTION validate_opportunity_transition();

-- --------------------------------------------------------------
-- 11. COMPUTED OPPORTUNITY VALUES
-- --------------------------------------------------------------

CREATE OR REPLACE VIEW opportunity_valuation AS
WITH latest_assessments AS (
    SELECT DISTINCT ON (opportunity_id)
        opportunity_id,
        probability,
        financial_impact,
        response_cost,
        confidence,
        assessment_version
    FROM opportunity_assessments
    ORDER BY opportunity_id, assessment_version DESC
)
SELECT
    o.opportunity_id,
    o.project_id,
    o.opportunity_code,
    o.title,
    o.category,
    o.strategy,
    o.status,
    o.owner_id,

    a.probability,
    a.financial_impact,
    a.response_cost,
    a.confidence,

    ROUND(
        a.probability * a.financial_impact,
        2
    ) AS expected_monetary_value,

    ROUND(
        (a.probability * a.financial_impact)
        - a.response_cost,
        2
    ) AS net_expected_value,

    ROUND(
        (
            (a.probability * a.financial_impact)
            - a.response_cost
        ) * a.confidence,
        2
    ) AS adjusted_expected_value,

    a.assessment_version

FROM opportunities o
LEFT JOIN latest_assessments a
    ON a.opportunity_id = o.opportunity_id;

-- --------------------------------------------------------------
-- 12. ELIGIBILITY EVALUATION FUNCTION
-- --------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_opportunity(
    p_opportunity_id BIGINT
)
RETURNS TABLE (
    opportunity_id BIGINT,
    eligible BOOLEAN,
    reason TEXT,
    expected_value NUMERIC,
    net_value NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_opportunity opportunity_valuation%ROWTYPE;
    v_policy opportunity_policies%ROWTYPE;
BEGIN
    SELECT *
    INTO v_opportunity
    FROM opportunity_valuation
    WHERE opportunity_valuation.opportunity_id =
        p_opportunity_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Opportunity % not found', p_opportunity_id;
    END IF;

    SELECT p.*
    INTO v_policy
    FROM opportunity_policies p
    WHERE p.project_id = v_opportunity.project_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT
            p_opportunity_id,
            FALSE,
            'No project opportunity policy configured'::TEXT,
            v_opportunity.expected_monetary_value,
            v_opportunity.net_expected_value;
        RETURN;
    END IF;

    IF v_opportunity.probability IS NULL THEN
        RETURN QUERY SELECT
            p_opportunity_id,
            FALSE,
            'Opportunity has no assessment'::TEXT,
            NULL::NUMERIC,
            NULL::NUMERIC;
        RETURN;
    END IF;

    IF v_opportunity.probability <
        v_policy.minimum_probability THEN

        RETURN QUERY SELECT
            p_opportunity_id,
            FALSE,
            'Probability below policy threshold'::TEXT,
            v_opportunity.expected_monetary_value,
            v_opportunity.net_expected_value;
        RETURN;
    END IF;

    IF v_opportunity.net_expected_value <
        v_policy.minimum_net_value THEN

        RETURN QUERY SELECT
            p_opportunity_id,
            FALSE,
            'Net value below policy threshold'::TEXT,
            v_opportunity.expected_monetary_value,
            v_opportunity.net_expected_value;
        RETURN;
    END IF;

    IF v_policy.require_positive_net_value
        AND v_opportunity.net_expected_value <= 0 THEN

        RETURN QUERY SELECT
            p_opportunity_id,
            FALSE,
            'Positive net expected value required'::TEXT,
            v_opportunity.expected_monetary_value,
            v_opportunity.net_expected_value;
        RETURN;
    END IF;

    IF NOT CASE v_opportunity.strategy
        WHEN 'EXPLOIT' THEN v_policy.allow_exploit
        WHEN 'ENHANCE' THEN v_policy.allow_enhance
        WHEN 'SHARE' THEN v_policy.allow_share
        WHEN 'ACCEPT' THEN v_policy.allow_accept
        ELSE FALSE
    END THEN

        RETURN QUERY SELECT
            p_opportunity_id,
            FALSE,
            'Response strategy prohibited by policy'::TEXT,
            v_opportunity.expected_monetary_value,
            v_opportunity.net_expected_value;
        RETURN;
    END IF;

    RETURN QUERY SELECT
        p_opportunity_id,
        TRUE,
        'Opportunity meets project policy'::TEXT,
        v_opportunity.expected_monetary_value,
        v_opportunity.net_expected_value;
END;
$$;

-- --------------------------------------------------------------
-- 13. PROJECT PORTFOLIO REPORTING
-- --------------------------------------------------------------

CREATE OR REPLACE VIEW project_opportunity_summary AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,

    COUNT(o.opportunity_id) AS total_opportunities,

    COUNT(o.opportunity_id)
        FILTER (WHERE o.status = 'REALIZED')
        AS realized_opportunities,

    COUNT(o.opportunity_id)
        FILTER (WHERE o.status = 'IN_PROGRESS')
        AS active_opportunities,

    COALESCE(
        SUM(v.expected_monetary_value),
        0
    ) AS total_expected_value,

    COALESCE(
        SUM(v.response_cost),
        0
    ) AS total_response_cost,

    COALESCE(
        SUM(v.net_expected_value),
        0
    ) AS total_net_expected_value,

    COALESCE(
        SUM(b.verified_benefit),
        0
    ) AS verified_realized_benefits

FROM projects p

LEFT JOIN opportunities o
    ON o.project_id = p.project_id

LEFT JOIN opportunity_valuation v
    ON v.opportunity_id = o.opportunity_id

LEFT JOIN LATERAL (
    SELECT SUM(rb.benefit_amount) AS verified_benefit
    FROM realized_benefits rb
    WHERE rb.opportunity_id = o.opportunity_id
      AND rb.verification_status = 'VERIFIED'
) b ON TRUE

GROUP BY
    p.project_id,
    p.project_code,
    p.project_name;

-- --------------------------------------------------------------
-- 14. SAMPLE PROJECT DATA
-- --------------------------------------------------------------

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
    'PRJ-001',
    'Enterprise Digital Transformation',
    'Project Manager',
    5000000,
    '2026-01-01',
    '2027-12-31'
),
(
    'PRJ-002',
    'Cloud Infrastructure Modernization',
    'Technology Director',
    3000000,
    '2026-03-01',
    '2027-06-30'
);

INSERT INTO project_members (
    project_id,
    member_name,
    role_name
)
SELECT project_id, member_name, role_name
FROM (
    SELECT
        p.project_id,
        x.member_name,
        x.role_name
    FROM projects p
    CROSS JOIN (
        VALUES
            ('Project Manager', 'PROJECT_MANAGER'),
            ('Delivery Lead', 'DELIVERY_LEAD'),
            ('Business Director', 'BUSINESS_OWNER'),
            ('Cloud Architect', 'TECHNICAL_OWNER'),
            ('Project Analyst', 'ANALYST')
    ) AS x(member_name, role_name)
) members;

INSERT INTO opportunity_policies (
    project_id,
    minimum_probability,
    minimum_net_value,
    require_positive_net_value
)
SELECT
    project_id,
    0.40,
    0,
    TRUE
FROM projects;

-- --------------------------------------------------------------
-- 15. SAMPLE OPPORTUNITIES
-- --------------------------------------------------------------

INSERT INTO opportunities (
    project_id,
    opportunity_code,
    title,
    description,
    category,
    strategy,
    owner_id
)
SELECT
    p.project_id,
    x.code,
    x.title,
    x.description,
    x.category::opportunity_category,
    x.strategy::response_strategy,
    m.member_id
FROM projects p

JOIN (
    VALUES
    (
        'PRJ-001',
        'OPP-001',
        'Process Automation',
        'Automating repetitive reporting activities.',
        'COST',
        'EXPLOIT',
        'Project Manager'
    ),
    (
        'PRJ-001',
        'OPP-002',
        'Early Delivery',
        'Parallel development may reduce delivery duration.',
        'SCHEDULE',
        'ENHANCE',
        'Delivery Lead'
    ),
    (
        'PRJ-001',
        'OPP-003',
        'Strategic Partnership',
        'Joint delivery with a technology partner.',
        'STRATEGIC',
        'SHARE',
        'Business Director'
    ),
    (
        'PRJ-001',
        'OPP-004',
        'Low Value Opportunity',
        'An opportunity with an unfavorable response cost.',
        'BUSINESS',
        'ACCEPT',
        'Project Analyst'
    ),
    (
        'PRJ-002',
        'OPP-005',
        'Cloud Cost Optimization',
        'Workload optimization may reduce infrastructure costs.',
        'TECHNOLOGY',
        'EXPLOIT',
        'Cloud Architect'
    )
) AS x(
    project_code,
    code,
    title,
    description,
    category,
    strategy,
    owner_name
)
    ON p.project_code = x.project_code

JOIN project_members m
    ON m.project_id = p.project_id
   AND m.member_name = x.owner_name;

-- --------------------------------------------------------------
-- 16. ASSESSMENT RECORDS
-- --------------------------------------------------------------

INSERT INTO opportunity_assessments (
    opportunity_id,
    probability,
    financial_impact,
    response_cost,
    confidence,
    assumptions,
    assessment_version
)
SELECT
    o.opportunity_id,
    x.probability,
    x.impact,
    x.cost,
    x.confidence,
    x.assumptions,
    1
FROM opportunities o

JOIN (
    VALUES
    ('OPP-001', 0.85, 200000, 25000, 0.95,
     'Automation can reduce reporting effort.'),
    ('OPP-002', 0.70, 150000, 15000, 0.90,
     'Parallel work can shorten delivery.'),
    ('OPP-003', 0.60, 300000, 30000, 0.85,
     'Partnership creates shared delivery value.'),
    ('OPP-004', 0.20, 1000, 2000, 0.90,
     'Response investment exceeds expected benefit.'),
    ('OPP-005', 0.75, 100000, 10000, 0.95,
     'Cloud workload optimization reduces expenditure.')
) AS x(
    code,
    probability,
    impact,
    cost,
    confidence,
    assumptions
)
    ON o.opportunity_code = x.code;

-- --------------------------------------------------------------
-- 17. RESPONSE PLANS AND ACTIONS
-- --------------------------------------------------------------

INSERT INTO response_plans (
    opportunity_id,
    strategy,
    action_description,
    responsible_member_id,
    planned_budget,
    target_date
)
SELECT
    o.opportunity_id,
    o.strategy,
    CASE o.opportunity_code
        WHEN 'OPP-001'
            THEN 'Deploy reporting automation and validate savings.'
        WHEN 'OPP-002'
            THEN 'Parallelize independent development work.'
        WHEN 'OPP-003'
            THEN 'Establish a joint delivery agreement.'
        WHEN 'OPP-005'
            THEN 'Optimize cloud workloads and resource allocation.'
    END,
    o.owner_id,
    a.response_cost,
    CURRENT_DATE + 60
FROM opportunities o

JOIN opportunity_assessments a
    ON a.opportunity_id = o.opportunity_id
   AND a.assessment_version = 1

WHERE o.opportunity_code IN (
    'OPP-001',
    'OPP-002',
    'OPP-003',
    'OPP-005'
);

INSERT INTO opportunity_actions (
    plan_id,
    action_title,
    assigned_to,
    due_date
)
SELECT
    rp.plan_id,
    'Validate assumptions and measure realized benefits',
    rp.responsible_member_id,
    rp.target_date
FROM response_plans rp;

-- --------------------------------------------------------------
-- 18. SAMPLE WORKFLOW EVENTS
-- --------------------------------------------------------------

INSERT INTO opportunity_events (
    opportunity_id,
    event,
    event_description
)
SELECT
    opportunity_id,
    'IDENTIFIED',
    'Opportunity entered into the project register.'
FROM opportunities;

-- --------------------------------------------------------------
-- 19. VERIFIED AND UNVERIFIED BENEFIT DATA
-- --------------------------------------------------------------

INSERT INTO realized_benefits (
    opportunity_id,
    benefit_amount,
    realization_date,
    verification_status,
    verification_reference
)
SELECT
    opportunity_id,
    175000,
    CURRENT_DATE,
    'VERIFIED',
    'FIN-VERIFY-001'
FROM opportunities
WHERE opportunity_code = 'OPP-001';

INSERT INTO realized_benefits (
    opportunity_id,
    benefit_amount,
    realization_date,
    verification_status
)
SELECT
    opportunity_id,
    20000,
    CURRENT_DATE,
    'PENDING'
FROM opportunities
WHERE opportunity_code = 'OPP-002';

-- --------------------------------------------------------------
-- 20. WORKFLOW PROCESSING
-- --------------------------------------------------------------

-- Assess an identified opportunity.
UPDATE opportunities
SET status = 'ASSESSED'
WHERE opportunity_code = 'OPP-001'
  AND status = 'IDENTIFIED';

-- Establish its response plan.
UPDATE opportunities
SET status = 'PLANNED'
WHERE opportunity_code = 'OPP-001'
  AND status = 'ASSESSED';

-- Start execution.
UPDATE opportunities
SET status = 'IN_PROGRESS'
WHERE opportunity_code = 'OPP-001'
  AND status = 'PLANNED';

-- Record realization.
UPDATE opportunities
SET status = 'REALIZED'
WHERE opportunity_code = 'OPP-001'
  AND status = 'IN_PROGRESS';

-- --------------------------------------------------------------
-- 21. RETRIEVAL AND VALUATION
-- --------------------------------------------------------------

SELECT
    opportunity_code,
    title,
    category,
    strategy,
    status,
    probability,
    financial_impact,
    expected_monetary_value,
    response_cost,
    net_expected_value,
    adjusted_expected_value
FROM opportunity_valuation
ORDER BY adjusted_expected_value DESC NULLS LAST;

-- --------------------------------------------------------------
-- 22. OPPORTUNITY ELIGIBILITY
-- --------------------------------------------------------------

SELECT
    o.opportunity_code,
    e.eligible,
    e.reason,
    e.expected_value,
    e.net_value
FROM opportunities o
CROSS JOIN LATERAL
    evaluate_opportunity(o.opportunity_id) e
ORDER BY o.opportunity_code;

-- --------------------------------------------------------------
-- 23. PORTFOLIO AGGREGATION
-- --------------------------------------------------------------

SELECT *
FROM project_opportunity_summary
ORDER BY project_code;

-- --------------------------------------------------------------
-- 24. CATEGORY-WISE OPPORTUNITY ANALYSIS
-- --------------------------------------------------------------

SELECT
    category,
    COUNT(*) AS opportunity_count,
    ROUND(AVG(probability), 4) AS average_probability,
    ROUND(SUM(expected_monetary_value), 2) AS total_emv,
    ROUND(SUM(net_expected_value), 2) AS total_net_value
FROM opportunity_valuation
WHERE probability IS NOT NULL
GROUP BY category
ORDER BY total_net_value DESC;

-- --------------------------------------------------------------
-- 25. RESPONSE STRATEGY EFFECTIVENESS
-- --------------------------------------------------------------

SELECT
    o.strategy,
    COUNT(*) AS opportunity_count,
    ROUND(SUM(v.expected_monetary_value), 2) AS total_emv,
    ROUND(SUM(v.response_cost), 2) AS total_response_cost,
    ROUND(SUM(v.net_expected_value), 2) AS total_net_value
FROM opportunities o
JOIN opportunity_valuation v
    ON v.opportunity_id = o.opportunity_id
GROUP BY o.strategy
ORDER BY total_net_value DESC;

-- --------------------------------------------------------------
-- 26. REALIZED BENEFIT REPORT
-- --------------------------------------------------------------

SELECT
    o.opportunity_code,
    o.title,
    COUNT(b.benefit_id) AS benefit_records,
    COALESCE(
        SUM(b.benefit_amount)
            FILTER (
                WHERE b.verification_status = 'VERIFIED'
            ),
        0
    ) AS verified_benefits,
    COALESCE(
        SUM(b.benefit_amount)
            FILTER (
                WHERE b.verification_status = 'PENDING'
            ),
        0
    ) AS pending_benefits
FROM opportunities o
LEFT JOIN realized_benefits b
    ON b.opportunity_id = o.opportunity_id
GROUP BY o.opportunity_id, o.opportunity_code, o.title
ORDER BY verified_benefits DESC;

-- --------------------------------------------------------------
-- 27. AUDIT HISTORY
-- --------------------------------------------------------------

SELECT
    o.opportunity_code,
    e.event,
    e.event_description,
    e.created_at
FROM opportunity_events e
JOIN opportunities o
    ON o.opportunity_id = e.opportunity_id
ORDER BY e.created_at DESC;

-- --------------------------------------------------------------
-- 28. RESPONSE ACTION COMPLETION
-- --------------------------------------------------------------

SELECT
    o.opportunity_code,
    COUNT(a.action_id) AS total_actions,
    COUNT(a.action_id)
        FILTER (WHERE a.completed) AS completed_actions,
    COUNT(a.action_id)
        FILTER (WHERE NOT a.completed) AS outstanding_actions
FROM opportunities o
JOIN response_plans rp
    ON rp.opportunity_id = o.opportunity_id
LEFT JOIN opportunity_actions a
    ON a.plan_id = rp.plan_id
GROUP BY o.opportunity_code
ORDER BY o.opportunity_code;

-- --------------------------------------------------------------
-- 29. INVALID WORKFLOW DEMONSTRATION
-- --------------------------------------------------------------

DO $$
DECLARE
    v_opportunity_id BIGINT;
BEGIN
    SELECT opportunity_id
    INTO v_opportunity_id
    FROM opportunities
    WHERE opportunity_code = 'OPP-002';

    BEGIN
        -- Planned status cannot be reached directly from IDENTIFIED
        -- through this test's intentionally invalid transition.
        UPDATE opportunities
        SET status = 'REALIZED'
        WHERE opportunity_id = v_opportunity_id;

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Expected workflow rejection: %', SQLERRM;
    END;
END;
$$;

-- --------------------------------------------------------------
-- 30. TRANSACTIONAL BENEFIT VERIFICATION
-- --------------------------------------------------------------

-- Verification is transactional. An invalid reference or failed
-- update rolls back the complete operation.

DO $$
BEGIN
    BEGIN
        UPDATE realized_benefits
        SET
            verification_status = 'VERIFIED',
            verification_reference = 'FIN-VERIFY-002'
        WHERE verification_status = 'PENDING'
          AND opportunity_id = (
              SELECT opportunity_id
              FROM opportunities
              WHERE opportunity_code = 'OPP-002'
          );

        RAISE NOTICE 'Benefit verification transaction completed.';

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Benefit verification failed: %', SQLERRM;
        RAISE;
    END;
END;
$$;

COMMIT;
