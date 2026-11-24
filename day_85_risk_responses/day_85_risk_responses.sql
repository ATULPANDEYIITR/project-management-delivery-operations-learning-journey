/*
===============================================================================
RISK RESPONSES: PLANNING AND GOVERNANCE OF PROJECT RISKS
===============================================================================

PostgreSQL 15+

Domain:
  Projects
    -> Risks
      -> Response plans
        -> Response actions
        -> Action assignments
        -> Residual assessments
        -> Secondary risks
      -> Approvals
      -> Monitoring events
      -> Escalations

Threat strategies:
  AVOID, MITIGATE, TRANSFER, ACCEPT, ESCALATE

Opportunity strategies:
  EXPLOIT, ENHANCE, SHARE, ACCEPT, ESCALATE

The database distinguishes:
  Inherent risk
  Planned response
  Approved response
  Executed response actions
  Residual risk
  Secondary risk
  Final risk status

Run in a dedicated development database.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS risk_management;

SET search_path TO risk_management, public;

-- ---------------------------------------------------------------------------
-- ENUMERATED DOMAIN TYPES
-- ---------------------------------------------------------------------------

CREATE TYPE risk_type AS ENUM (
    'THREAT',
    'OPPORTUNITY'
);

CREATE TYPE risk_status AS ENUM (
    'IDENTIFIED',
    'PLANNED',
    'APPROVED',
    'IN_PROGRESS',
    'MONITORING',
    'ESCALATED',
    'CLOSED'
);

CREATE TYPE response_strategy AS ENUM (
    'AVOID',
    'MITIGATE',
    'TRANSFER',
    'ACCEPT',
    'EXPLOIT',
    'ENHANCE',
    'SHARE',
    'ESCALATE'
);

CREATE TYPE action_status AS ENUM (
    'PENDING',
    'IN_PROGRESS',
    'COMPLETED',
    'BLOCKED',
    'CANCELLED'
);

CREATE TYPE approval_decision AS ENUM (
    'APPROVED',
    'REJECTED'
);

CREATE TYPE event_type AS ENUM (
    'RISK_IDENTIFIED',
    'RESPONSE_PLANNED',
    'RESPONSE_APPROVED',
    'ACTION_STARTED',
    'ACTION_COMPLETED',
    'ACTION_BLOCKED',
    'RESIDUAL_ASSESSED',
    'RISK_ESCALATED',
    'RISK_CLOSED',
    'TRIGGER_ACTIVATED'
);

-- ---------------------------------------------------------------------------
-- PROJECTS
-- ---------------------------------------------------------------------------

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code VARCHAR(30) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    project_manager VARCHAR(150) NOT NULL,
    approved_budget NUMERIC(15,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT project_budget_nonnegative
        CHECK (approved_budget >= 0),

    CONSTRAINT project_dates_valid
        CHECK (end_date IS NULL OR end_date >= start_date)
);

-- ---------------------------------------------------------------------------
-- PROJECT PARTICIPANTS AND AUTHORIZED RESPONSIBILITIES
-- ---------------------------------------------------------------------------

CREATE TABLE project_participants (
    participant_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id) ON DELETE RESTRICT,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    role_name VARCHAR(80) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT participant_email_unique
        UNIQUE (project_id, email),

    CONSTRAINT participant_role_nonempty
        CHECK (LENGTH(TRIM(role_name)) > 0)
);

CREATE INDEX idx_participants_project_active
    ON project_participants(project_id, is_active);

-- ---------------------------------------------------------------------------
-- RISK REGISTER
-- ---------------------------------------------------------------------------

CREATE TABLE risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id) ON DELETE RESTRICT,

    risk_code VARCHAR(40) NOT NULL,
    title VARCHAR(250) NOT NULL,
    description TEXT NOT NULL,

    type risk_type NOT NULL,
    category VARCHAR(100) NOT NULL,

    probability NUMERIC(5,4) NOT NULL,
    impact SMALLINT NOT NULL,

    risk_owner_id BIGINT NOT NULL
        REFERENCES project_participants(participant_id)
        ON DELETE RESTRICT,

    response_owner_id BIGINT
        REFERENCES project_participants(participant_id)
        ON DELETE RESTRICT,

    status risk_status NOT NULL DEFAULT 'IDENTIFIED',

    trigger_description TEXT,
    identified_on DATE NOT NULL DEFAULT CURRENT_DATE,
    target_resolution_date DATE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT risk_code_unique
        UNIQUE (project_id, risk_code),

    CONSTRAINT risk_title_nonempty
        CHECK (LENGTH(TRIM(title)) > 0),

    CONSTRAINT risk_probability_valid
        CHECK (probability BETWEEN 0 AND 1),

    CONSTRAINT risk_impact_valid
        CHECK (impact BETWEEN 1 AND 5),

    CONSTRAINT risk_resolution_date_valid
        CHECK (
            target_resolution_date IS NULL
            OR target_resolution_date >= identified_on
        )
);

CREATE INDEX idx_risks_project_status
    ON risks(project_id, status);

CREATE INDEX idx_risks_owner
    ON risks(risk_owner_id);

CREATE INDEX idx_risks_type_probability
    ON risks(type, probability DESC);

-- ---------------------------------------------------------------------------
-- RISK RESPONSE PLANS
-- ---------------------------------------------------------------------------

CREATE TABLE response_plans (
    response_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id) ON DELETE RESTRICT,

    strategy response_strategy NOT NULL,
    response_description TEXT NOT NULL,

    response_owner_id BIGINT NOT NULL
        REFERENCES project_participants(participant_id)
        ON DELETE RESTRICT,

    allocated_budget NUMERIC(15,2) NOT NULL DEFAULT 0,

    contingency_plan TEXT,
    trigger_condition TEXT,

    planned_start_date DATE,
    planned_completion_date DATE,

    version INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT response_budget_nonnegative
        CHECK (allocated_budget >= 0),

    CONSTRAINT response_version_positive
        CHECK (version > 0),

    CONSTRAINT response_dates_valid
        CHECK (
            planned_completion_date IS NULL
            OR planned_start_date IS NULL
            OR planned_completion_date >= planned_start_date
        )
);

CREATE UNIQUE INDEX uq_current_response_per_risk
    ON response_plans(risk_id)
    WHERE is_current = TRUE;

CREATE INDEX idx_response_owner
    ON response_plans(response_owner_id);

-- ---------------------------------------------------------------------------
-- RESPONSE APPROVALS
-- ---------------------------------------------------------------------------

CREATE TABLE response_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    response_id BIGINT NOT NULL
        REFERENCES response_plans(response_id) ON DELETE RESTRICT,

    approver_id BIGINT NOT NULL
        REFERENCES project_participants(participant_id)
        ON DELETE RESTRICT,

    decision approval_decision NOT NULL,
    comments TEXT,

    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_response_approver
        UNIQUE (response_id, approver_id)
);

CREATE INDEX idx_approvals_response_decision
    ON response_approvals(response_id, decision);

-- ---------------------------------------------------------------------------
-- RESPONSE ACTIONS
-- ---------------------------------------------------------------------------

CREATE TABLE response_actions (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    response_id BIGINT NOT NULL
        REFERENCES response_plans(response_id) ON DELETE RESTRICT,

    description TEXT NOT NULL,

    assigned_to BIGINT NOT NULL
        REFERENCES project_participants(participant_id)
        ON DELETE RESTRICT,

    estimated_cost NUMERIC(15,2) NOT NULL DEFAULT 0,

    deadline DATE NOT NULL,

    status action_status NOT NULL DEFAULT 'PENDING',

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT action_cost_nonnegative
        CHECK (estimated_cost >= 0),

    CONSTRAINT action_description_nonempty
        CHECK (LENGTH(TRIM(description)) > 0),

    CONSTRAINT action_completion_valid
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        ),

    CONSTRAINT action_status_timestamps_valid
        CHECK (
            status <> 'COMPLETED'
            OR completed_at IS NOT NULL
        )
);

CREATE INDEX idx_actions_response_status
    ON response_actions(response_id, status);

CREATE INDEX idx_actions_deadline
    ON response_actions(deadline)
    WHERE status IN ('PENDING', 'IN_PROGRESS', 'BLOCKED');

CREATE INDEX idx_actions_assignee
    ON response_actions(assigned_to, status);

-- ---------------------------------------------------------------------------
-- RESIDUAL RISK ASSESSMENTS
-- ---------------------------------------------------------------------------

CREATE TABLE residual_assessments (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id) ON DELETE RESTRICT,

    response_id BIGINT NOT NULL
        REFERENCES response_plans(response_id) ON DELETE RESTRICT,

    probability NUMERIC(5,4) NOT NULL,
    impact SMALLINT NOT NULL,

    assessment_notes TEXT NOT NULL,

    assessed_by BIGINT NOT NULL
        REFERENCES project_participants(participant_id)
        ON DELETE RESTRICT,

    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT residual_probability_valid
        CHECK (probability BETWEEN 0 AND 1),

    CONSTRAINT residual_impact_valid
        CHECK (impact BETWEEN 1 AND 5)
);

CREATE INDEX idx_residual_risk_date
    ON residual_assessments(risk_id, assessed_at DESC);

-- ---------------------------------------------------------------------------
-- SECONDARY RISK RELATIONSHIPS
-- ---------------------------------------------------------------------------

CREATE TABLE secondary_risk_links (
    parent_risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id) ON DELETE RESTRICT,

    secondary_risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id) ON DELETE RESTRICT,

    relationship_description TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (parent_risk_id, secondary_risk_id),

    CONSTRAINT no_self_referencing_risk
        CHECK (parent_risk_id <> secondary_risk_id)
);

-- ---------------------------------------------------------------------------
-- RISK MONITORING EVENTS
-- ---------------------------------------------------------------------------

CREATE TABLE risk_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id) ON DELETE RESTRICT,

    event event_type NOT NULL,

    event_description TEXT NOT NULL,

    actor_id BIGINT
        REFERENCES project_participants(participant_id)
        ON DELETE RESTRICT,

    event_data JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_events_history
    ON risk_events(risk_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- STRATEGY VALIDATION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_response_strategy()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_type risk_type;
    participant_project BIGINT;
    risk_project BIGINT;
BEGIN
    SELECT r.type, r.project_id
    INTO current_type, risk_project
    FROM risks r
    WHERE r.risk_id = NEW.risk_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Referenced risk does not exist.';
    END IF;

    IF current_type = 'THREAT'
       AND NEW.strategy NOT IN (
           'AVOID', 'MITIGATE', 'TRANSFER', 'ACCEPT', 'ESCALATE'
       ) THEN
        RAISE EXCEPTION
            'Strategy % is not valid for a threat.',
            NEW.strategy;
    END IF;

    IF current_type = 'OPPORTUNITY'
       AND NEW.strategy NOT IN (
           'EXPLOIT', 'ENHANCE', 'SHARE', 'ACCEPT', 'ESCALATE'
       ) THEN
        RAISE EXCEPTION
            'Strategy % is not valid for an opportunity.',
            NEW.strategy;
    END IF;

    SELECT project_id
    INTO participant_project
    FROM project_participants
    WHERE participant_id = NEW.response_owner_id
      AND is_active = TRUE;

    IF NOT FOUND OR participant_project <> risk_project THEN
        RAISE EXCEPTION
            'Response owner must be active in the same project.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_response_strategy
BEFORE INSERT OR UPDATE OF strategy, response_owner_id, risk_id
ON response_plans
FOR EACH ROW
EXECUTE FUNCTION validate_response_strategy();

-- ---------------------------------------------------------------------------
-- RESPONSE ACTION BUDGET ENFORCEMENT
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_response_budget()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    allocated NUMERIC(15,2);
    committed NUMERIC(15,2);
    target_response BIGINT;
BEGIN
    target_response := NEW.response_id;

    SELECT allocated_budget
    INTO allocated
    FROM response_plans
    WHERE response_id = target_response
      AND is_current = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'An action requires a current response plan.';
    END IF;

    SELECT COALESCE(SUM(estimated_cost), 0)
    INTO committed
    FROM response_actions
    WHERE response_id = target_response
      AND status <> 'CANCELLED'
      AND (
          TG_OP = 'INSERT'
          OR action_id <> NEW.action_id
      );

    IF NEW.status <> 'CANCELLED' THEN
        committed := committed + NEW.estimated_cost;
    END IF;

    IF committed > allocated THEN
        RAISE EXCEPTION
            'Response budget exceeded. Committed: %, allocated: %',
            committed,
            allocated;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_response_action_budget
BEFORE INSERT OR UPDATE OF estimated_cost, status, response_id
ON response_actions
FOR EACH ROW
EXECUTE FUNCTION enforce_response_budget();

-- ---------------------------------------------------------------------------
-- RESPONSE APPROVAL VALIDATION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_response_approval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    risk_project BIGINT;
    approver_project BIGINT;
    approver_role TEXT;
    response_owner BIGINT;
BEGIN
    SELECT r.project_id, rp.response_owner_id
    INTO risk_project, response_owner
    FROM response_plans rp
    JOIN risks r ON r.risk_id = rp.risk_id
    WHERE rp.response_id = NEW.response_id
      AND rp.is_current = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Current response plan not found.';
    END IF;

    SELECT project_id, role_name
    INTO approver_project, approver_role
    FROM project_participants
    WHERE participant_id = NEW.approver_id
      AND is_active = TRUE;

    IF NOT FOUND OR approver_project <> risk_project THEN
        RAISE EXCEPTION
            'Approver must be an active project participant.';
    END IF;

    IF NEW.approver_id = response_owner THEN
        RAISE EXCEPTION
            'Response owner cannot approve their own response.';
    END IF;

    IF approver_role NOT IN (
        'PROJECT_MANAGER',
        'PROJECT_SPONSOR',
        'RISK_MANAGER'
    ) THEN
        RAISE EXCEPTION
            'Participant role is not authorized to approve responses.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_response_approval
BEFORE INSERT OR UPDATE ON response_approvals
FOR EACH ROW
EXECUTE FUNCTION validate_response_approval();

-- ---------------------------------------------------------------------------
-- AUTOMATIC RISK EVENT RECORDING
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION record_risk_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_event event_type;
BEGIN
    IF TG_OP = 'INSERT' THEN
        current_event := 'RISK_IDENTIFIED';

        INSERT INTO risk_events (
            risk_id,
            event,
            event_description
        )
        VALUES (
            NEW.risk_id,
            current_event,
            'Risk added to the project risk register.'
        );

        RETURN NEW;
    END IF;

    IF OLD.status IS DISTINCT FROM NEW.status THEN
        current_event := CASE NEW.status
            WHEN 'PLANNED' THEN 'RESPONSE_PLANNED'
            WHEN 'APPROVED' THEN 'RESPONSE_APPROVED'
            WHEN 'ESCALATED' THEN 'RISK_ESCALATED'
            WHEN 'CLOSED' THEN 'RISK_CLOSED'
            ELSE 'RISK_IDENTIFIED'
        END;

        INSERT INTO risk_events (
            risk_id,
            event,
            event_description
        )
        VALUES (
            NEW.risk_id,
            current_event,
            'Risk state changed from ' ||
            OLD.status || ' to ' || NEW.status
        );
    END IF;

    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_record_risk_event
AFTER INSERT OR UPDATE OF status
ON risks
FOR EACH ROW
EXECUTE FUNCTION record_risk_event();

-- ---------------------------------------------------------------------------
-- RESIDUAL ASSESSMENT RISK VALIDATION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_residual_assessment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    response_risk BIGINT;
    assessment_project BIGINT;
    assessor_project BIGINT;
BEGIN
    SELECT risk_id
    INTO response_risk
    FROM response_plans
    WHERE response_id = NEW.response_id
      AND is_current = TRUE;

    IF NOT FOUND OR response_risk <> NEW.risk_id THEN
        RAISE EXCEPTION
            'Residual assessment must reference the current response for the same risk.';
    END IF;

    SELECT project_id
    INTO assessment_project
    FROM risks
    WHERE risk_id = NEW.risk_id;

    SELECT project_id
    INTO assessor_project
    FROM project_participants
    WHERE participant_id = NEW.assessed_by
      AND is_active = TRUE;

    IF NOT FOUND OR assessment_project <> assessor_project THEN
        RAISE EXCEPTION
            'Assessor must belong to the risk project.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_residual_assessment
BEFORE INSERT OR UPDATE
ON residual_assessments
FOR EACH ROW
EXECUTE FUNCTION validate_residual_assessment();

-- ---------------------------------------------------------------------------
-- VIEWS
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_risk_exposure AS
SELECT
    r.risk_id,
    r.project_id,
    r.risk_code,
    r.title,
    r.type,
    r.category,
    r.status,
    r.risk_owner_id,
    r.probability AS inherent_probability,
    r.impact AS inherent_impact,

    ROUND(
        r.probability * r.impact,
        4
    ) AS inherent_score,

    latest.probability AS residual_probability,
    latest.impact AS residual_impact,

    ROUND(
        COALESCE(latest.probability, r.probability)
        * COALESCE(latest.impact, r.impact),
        4
    ) AS residual_score,

    CASE
        WHEN latest.assessment_id IS NULL THEN NULL
        WHEN r.probability * r.impact = 0 THEN 0
        ELSE ROUND(
            (
                r.probability * r.impact
                -
                latest.probability * latest.impact
            ) / (r.probability * r.impact) * 100,
            2
        )
    END AS response_effectiveness_percentage

FROM risks r

LEFT JOIN LATERAL (
    SELECT
        ra.assessment_id,
        ra.probability,
        ra.impact
    FROM residual_assessments ra
    WHERE ra.risk_id = r.risk_id
    ORDER BY ra.assessed_at DESC, ra.assessment_id DESC
    LIMIT 1
) latest ON TRUE;

CREATE OR REPLACE VIEW v_response_execution AS
SELECT
    rp.response_id,
    rp.risk_id,
    rp.strategy,
    rp.allocated_budget,

    COALESCE(
        SUM(
            CASE
                WHEN a.status <> 'CANCELLED'
                THEN a.estimated_cost
                ELSE 0
            END
        ),
        0
    ) AS committed_budget,

    COALESCE(
        SUM(
            CASE
                WHEN a.status = 'COMPLETED'
                THEN a.estimated_cost
                ELSE 0
            END
        ),
        0
    ) AS completed_action_cost,

    COUNT(a.action_id) AS total_actions,

    COUNT(a.action_id) FILTER (
        WHERE a.status = 'COMPLETED'
    ) AS completed_actions,

    COUNT(a.action_id) FILTER (
        WHERE a.status IN ('PENDING', 'IN_PROGRESS', 'BLOCKED')
    ) AS outstanding_actions

FROM response_plans rp

LEFT JOIN response_actions a
    ON a.response_id = rp.response_id

WHERE rp.is_current = TRUE

GROUP BY
    rp.response_id,
    rp.risk_id,
    rp.strategy,
    rp.allocated_budget;

-- ---------------------------------------------------------------------------
-- STRATEGY ELIGIBILITY FUNCTION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_strategy_valid(
    p_type risk_type,
    p_strategy response_strategy
)
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT CASE
        WHEN p_type = 'THREAT' THEN
            p_strategy IN (
                'AVOID', 'MITIGATE', 'TRANSFER',
                'ACCEPT', 'ESCALATE'
            )
        WHEN p_type = 'OPPORTUNITY' THEN
            p_strategy IN (
                'EXPLOIT', 'ENHANCE', 'SHARE',
                'ACCEPT', 'ESCALATE'
            )
        ELSE FALSE
    END;
$$;

-- ---------------------------------------------------------------------------
-- MERGE-FREE RESPONSE ELIGIBILITY
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION response_is_eligible(
    p_response_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_risk_id BIGINT;
    v_project_id BIGINT;
    v_owner BIGINT;
    v_budget NUMERIC(15,2);
    v_committed NUMERIC(15,2);
    v_strategy response_strategy;
    v_approval_count INTEGER;
    v_action_count INTEGER;
    v_invalid_action_count INTEGER;
BEGIN
    SELECT
        rp.risk_id,
        r.project_id,
        rp.response_owner_id,
        rp.allocated_budget,
        rp.strategy
    INTO
        v_risk_id,
        v_project_id,
        v_owner,
        v_budget,
        v_strategy
    FROM response_plans rp
    JOIN risks r ON r.risk_id = rp.risk_id
    WHERE rp.response_id = p_response_id
      AND rp.is_current = TRUE;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF NOT is_strategy_valid(
        (SELECT type FROM risks WHERE risk_id = v_risk_id),
        v_strategy
    ) THEN
        RETURN FALSE;
    END IF;

    SELECT COUNT(*)
    INTO v_approval_count
    FROM response_approvals
    WHERE response_id = p_response_id
      AND decision = 'APPROVED';

    IF v_approval_count = 0 THEN
        RETURN FALSE;
    END IF;

    SELECT
        COALESCE(SUM(estimated_cost), 0),
        COUNT(*),
        COUNT(*) FILTER (
            WHERE status = 'BLOCKED'
        )
    INTO
        v_committed,
        v_action_count,
        v_invalid_action_count
    FROM response_actions
    WHERE response_id = p_response_id
      AND status <> 'CANCELLED';

    IF v_committed > v_budget THEN
        RETURN FALSE;
    END IF;

    IF v_invalid_action_count > 0 THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$;

-- ---------------------------------------------------------------------------
-- RISK RESPONSE PLANNING PROCEDURE
-- ---------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE plan_risk_response(
    p_risk_id BIGINT,
    p_strategy response_strategy,
    p_response_owner BIGINT,
    p_description TEXT,
    p_budget NUMERIC(15,2)
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_risk_type risk_type;
    v_risk_status risk_status;
BEGIN
    SELECT type, status
    INTO v_risk_type, v_risk_status
    FROM risks
    WHERE risk_id = p_risk_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk % not found.', p_risk_id;
    END IF;

    IF v_risk_status NOT IN ('IDENTIFIED', 'PLANNED') THEN
        RAISE EXCEPTION
            'Risk cannot be planned from state %.',
            v_risk_status;
    END IF;

    IF NOT is_strategy_valid(v_risk_type, p_strategy) THEN
        RAISE EXCEPTION
            'Strategy % does not match risk type %.',
            p_strategy,
            v_risk_type;
    END IF;

    IF p_budget < 0 THEN
        RAISE EXCEPTION 'Response budget cannot be negative.';
    END IF;

    UPDATE response_plans
    SET is_current = FALSE
    WHERE risk_id = p_risk_id
      AND is_current = TRUE;

    INSERT INTO response_plans (
        risk_id,
        strategy,
        response_description,
        response_owner_id,
        allocated_budget,
        version,
        is_current
    )
    VALUES (
        p_risk_id,
        p_strategy,
        p_description,
        p_response_owner,
        p_budget,
        COALESCE(
            (
                SELECT MAX(version) + 1
                FROM response_plans
                WHERE risk_id = p_risk_id
            ),
            1
        ),
        TRUE
    );

    UPDATE risks
    SET
        response_owner_id = p_response_owner,
        status = 'PLANNED'
    WHERE risk_id = p_risk_id;
END;
$$;

-- ---------------------------------------------------------------------------
-- SAMPLE PROJECT AND PARTICIPANTS
-- ---------------------------------------------------------------------------

INSERT INTO projects (
    project_code,
    project_name,
    project_manager,
    approved_budget,
    start_date,
    end_date
)
VALUES (
    'PRJ-2026-001',
    'Enterprise Cloud Migration',
    'Ananya Sharma',
    2500000,
    DATE '2026-11-01',
    DATE '2027-06-30'
);

INSERT INTO project_participants (
    project_id,
    full_name,
    email,
    role_name
)
VALUES
(
    1,
    'Ananya Sharma',
    'ananya@example.org',
    'PROJECT_MANAGER'
),
(
    1,
    'Rahul Verma',
    'rahul@example.org',
    'RISK_MANAGER'
),
(
    1,
    'Priya Singh',
    'priya@example.org',
    'PROCUREMENT_LEAD'
),
(
    1,
    'Arjun Mehta',
    'arjun@example.org',
    'PROJECT_SPONSOR'
),
(
    1,
    'Neha Gupta',
    'neha@example.org',
    'ENGINEERING_LEAD'
),
(
    1,
    'Karan Das',
    'karan@example.org',
    'ENGINEERING_LEAD'
);

-- ---------------------------------------------------------------------------
-- SAMPLE THREATS AND OPPORTUNITIES
-- ---------------------------------------------------------------------------

INSERT INTO risks (
    project_id,
    risk_code,
    title,
    description,
    type,
    category,
    probability,
    impact,
    risk_owner_id,
    target_resolution_date,
    trigger_description
)
VALUES
(
    1,
    'RISK-001',
    'Cloud supplier delivery delay',
    'Infrastructure supplier may miss the deployment milestone.',
    'THREAT',
    'PROCUREMENT',
    0.6000,
    5,
    1,
    CURRENT_DATE + 30,
    'Supplier delivery is more than seven days late.'
),
(
    1,
    'RISK-002',
    'Cybersecurity configuration weakness',
    'Incorrect cloud permissions may expose sensitive resources.',
    'THREAT',
    'CYBERSECURITY',
    0.4000,
    5,
    2,
    CURRENT_DATE + 20,
    'Critical security finding remains unresolved.'
),
(
    1,
    'RISK-003',
    'Automated testing opportunity',
    'Automated testing could reduce release cycle time.',
    'OPPORTUNITY',
    'TECHNOLOGY',
    0.7000,
    4,
    5,
    CURRENT_DATE + 45,
    'Automation prototype achieves agreed coverage.'
),
(
    1,
    'RISK-004',
    'Knowledge transfer opportunity',
    'Joint delivery with an experienced technology partner may improve skills.',
    'OPPORTUNITY',
    'CAPABILITY',
    0.5000,
    3,
    5,
    CURRENT_DATE + 60,
    'Partner confirms resource availability.'
);

-- ---------------------------------------------------------------------------
-- PLAN RESPONSE STRATEGIES
-- ---------------------------------------------------------------------------

CALL plan_risk_response(
    1,
    'MITIGATE',
    3,
    'Qualify a secondary cloud infrastructure supplier.',
    15000
);

CALL plan_risk_response(
    2,
    'AVOID',
    2,
    'Prevent production release until critical permissions are corrected.',
    12000
);

CALL plan_risk_response(
    3,
    'EXPLOIT',
    5,
    'Implement automated testing in the release pipeline.',
    8000
);

CALL plan_risk_response(
    4,
    'SHARE',
    5,
    'Establish a joint knowledge transfer arrangement.',
    6000
);

-- ---------------------------------------------------------------------------
-- RESPONSE APPROVALS
-- ---------------------------------------------------------------------------

INSERT INTO response_approvals (
    response_id,
    approver_id,
    decision,
    comments
)
VALUES
(1, 4, 'APPROVED', 'Alternative supplier qualification authorized.'),
(2, 1, 'APPROVED', 'Security remediation required before release.'),
(3, 4, 'APPROVED', 'Automation pilot authorized.'),
(4, 1, 'APPROVED', 'Joint capability initiative authorized.');

-- ---------------------------------------------------------------------------
-- RESPONSE ACTIONS
-- ---------------------------------------------------------------------------

INSERT INTO response_actions (
    response_id,
    description,
    assigned_to,
    estimated_cost,
    deadline,
    status,
    started_at,
    completed_at
)
VALUES
(
    1,
    'Evaluate alternative cloud supplier.',
    3,
    4000,
    CURRENT_DATE + 10,
    'COMPLETED',
    CURRENT_TIMESTAMP - INTERVAL '5 days',
    CURRENT_TIMESTAMP - INTERVAL '1 day'
),
(
    1,
    'Conduct alternative supplier infrastructure test.',
    5,
    6000,
    CURRENT_DATE + 20,
    'IN_PROGRESS',
    CURRENT_TIMESTAMP,
    NULL
),
(
    2,
    'Review cloud IAM permissions.',
    2,
    3000,
    CURRENT_DATE + 7,
    'IN_PROGRESS',
    CURRENT_TIMESTAMP,
    NULL
),
(
    3,
    'Develop automated regression test suite.',
    5,
    5000,
    CURRENT_DATE + 20,
    'PENDING',
    NULL,
    NULL
),
(
    4,
    'Conduct joint technical knowledge sessions.',
    5,
    3000,
    CURRENT_DATE + 25,
    'PENDING',
    NULL,
    NULL
);

-- ---------------------------------------------------------------------------
-- RESIDUAL RISK ASSESSMENTS
-- ---------------------------------------------------------------------------

INSERT INTO residual_assessments (
    risk_id,
    response_id,
    probability,
    impact,
    assessment_notes,
    assessed_by
)
VALUES
(
    1,
    1,
    0.2000,
    3,
    'Alternative supplier reduces probability and potential delay.',
    2
),
(
    2,
    2,
    0.1000,
    4,
    'Access-control remediation substantially reduces exposure.',
    2
);

-- ---------------------------------------------------------------------------
-- SECONDARY RISK RELATIONSHIPS
-- ---------------------------------------------------------------------------

INSERT INTO secondary_risk_links (
    parent_risk_id,
    secondary_risk_id,
    relationship_description
)
VALUES
(
    1,
    3,
    'Supplier delay may create an opportunity to accelerate automated testing.'
);

-- ---------------------------------------------------------------------------
-- TRANSACTIONAL RISK STATE UPDATES
-- ---------------------------------------------------------------------------

UPDATE risks
SET status = 'APPROVED'
WHERE risk_id IN (1, 2, 3, 4);

UPDATE risks
SET status = 'IN_PROGRESS'
WHERE risk_id IN (1, 2);

COMMIT;

-- ---------------------------------------------------------------------------
-- QUERY 1: INHERENT AND RESIDUAL RISK EXPOSURE
-- ---------------------------------------------------------------------------

SELECT
    risk_code,
    title,
    type,
    status,
    inherent_probability,
    inherent_impact,
    inherent_score,
    residual_probability,
    residual_impact,
    residual_score,
    response_effectiveness_percentage
FROM v_risk_exposure
ORDER BY residual_score DESC;

-- ---------------------------------------------------------------------------
-- QUERY 2: RESPONSE BUDGET UTILIZATION
-- ---------------------------------------------------------------------------

SELECT
    rp.response_id,
    r.risk_code,
    r.title,
    rp.strategy,
    rp.allocated_budget,
    ve.committed_budget,
    ve.completed_action_cost,

    ROUND(
        100 * ve.committed_budget /
        NULLIF(rp.allocated_budget, 0),
        2
    ) AS budget_utilization_percentage,

    ve.total_actions,
    ve.completed_actions,
    ve.outstanding_actions

FROM response_plans rp

JOIN risks r
    ON r.risk_id = rp.risk_id

JOIN v_response_execution ve
    ON ve.response_id = rp.response_id

WHERE rp.is_current = TRUE
ORDER BY budget_utilization_percentage DESC NULLS LAST;

-- ---------------------------------------------------------------------------
-- QUERY 3: APPROVAL AND RESPONSE ELIGIBILITY
-- ---------------------------------------------------------------------------

SELECT
    rp.response_id,
    r.risk_code,
    rp.strategy,
    response_is_eligible(rp.response_id) AS eligible_for_execution,

    COUNT(ra.approval_id) FILTER (
        WHERE ra.decision = 'APPROVED'
    ) AS approvals,

    COUNT(ra.approval_id) FILTER (
        WHERE ra.decision = 'REJECTED'
    ) AS rejections

FROM response_plans rp

JOIN risks r
    ON r.risk_id = rp.risk_id

LEFT JOIN response_approvals ra
    ON ra.response_id = rp.response_id

WHERE rp.is_current = TRUE

GROUP BY
    rp.response_id,
    r.risk_code,
    rp.strategy

ORDER BY rp.response_id;

-- ---------------------------------------------------------------------------
-- QUERY 4: ACTIONS REQUIRING ATTENTION
-- ---------------------------------------------------------------------------

SELECT
    r.risk_code,
    r.title,
    a.description,
    p.full_name AS assigned_owner,
    a.deadline,
    a.status,

    CASE
        WHEN a.deadline < CURRENT_DATE THEN 'OVERDUE'
        WHEN a.deadline = CURRENT_DATE THEN 'DUE TODAY'
        ELSE 'UPCOMING'
    END AS deadline_condition

FROM response_actions a

JOIN response_plans rp
    ON rp.response_id = a.response_id

JOIN risks r
    ON r.risk_id = rp.risk_id

JOIN project_participants p
    ON p.participant_id = a.assigned_to

WHERE rp.is_current = TRUE
  AND a.status IN ('PENDING', 'IN_PROGRESS', 'BLOCKED')

ORDER BY a.deadline;

-- ---------------------------------------------------------------------------
-- QUERY 5: RISK DISTRIBUTION BY CATEGORY
-- ---------------------------------------------------------------------------

SELECT
    category,
    type,
    COUNT(*) AS risk_count,
    ROUND(AVG(probability * impact), 3) AS average_inherent_score,
    ROUND(MAX(probability * impact), 3) AS maximum_inherent_score

FROM risks

GROUP BY category, type

ORDER BY category, type;

-- ---------------------------------------------------------------------------
-- QUERY 6: RISK RESPONSE AND SECONDARY RISK RELATIONSHIPS
-- ---------------------------------------------------------------------------

SELECT
    parent.risk_code AS parent_risk,
    parent.title AS parent_title,
    secondary.risk_code AS secondary_risk,
    secondary.title AS secondary_title,
    link.relationship_description

FROM secondary_risk_links link

JOIN risks parent
    ON parent.risk_id = link.parent_risk_id

JOIN risks secondary
    ON secondary.risk_id = link.secondary_risk_id;

-- ---------------------------------------------------------------------------
-- QUERY 7: EXPECTED MONETARY VALUE
-- ---------------------------------------------------------------------------

SELECT
    r.risk_code,
    r.title,
    r.probability,
    financial.estimated_loss,

    ROUND(
        r.probability * financial.estimated_loss,
        2
    ) AS expected_monetary_value

FROM risks r

CROSS JOIN (
    VALUES
        (100000::NUMERIC)
) AS financial(estimated_loss)

WHERE r.type = 'THREAT'
ORDER BY expected_monetary_value DESC;

-- ---------------------------------------------------------------------------
-- QUERY 8: RESPONSE ACTION COMPLETION
-- ---------------------------------------------------------------------------

SELECT
    r.risk_code,
    r.title,

    COUNT(a.action_id) AS total_actions,

    COUNT(a.action_id) FILTER (
        WHERE a.status = 'COMPLETED'
    ) AS completed_actions,

    ROUND(
        100.0 * COUNT(a.action_id) FILTER (
            WHERE a.status = 'COMPLETED'
        ) /
        NULLIF(COUNT(a.action_id), 0),
        2
    ) AS completion_percentage

FROM risks r

JOIN response_plans rp
    ON rp.risk_id = r.risk_id
   AND rp.is_current = TRUE

LEFT JOIN response_actions a
    ON a.response_id = rp.response_id

GROUP BY r.risk_id, r.risk_code, r.title
ORDER BY completion_percentage DESC NULLS LAST;

-- ---------------------------------------------------------------------------
-- QUERY 9: RISK MONITORING HISTORY
-- ---------------------------------------------------------------------------

SELECT
    r.risk_code,
    e.event,
    e.event_description,
    e.created_at

FROM risk_events e

JOIN risks r
    ON r.risk_id = e.risk_id

ORDER BY e.created_at DESC;

-- ---------------------------------------------------------------------------
-- QUERY 10: STRATEGY DISTRIBUTION
-- ---------------------------------------------------------------------------

SELECT
    r.type,
    rp.strategy,
    COUNT(*) AS strategy_count

FROM response_plans rp

JOIN risks r
    ON r.risk_id = rp.risk_id

WHERE rp.is_current = TRUE

GROUP BY r.type, rp.strategy
ORDER BY r.type, strategy_count DESC;

-- ---------------------------------------------------------------------------
-- QUERY 11: INCOMPLETE RESPONSE ACTIONS
-- ---------------------------------------------------------------------------

SELECT
    r.risk_code,
    r.title,
    a.description,
    a.status,
    a.deadline

FROM response_actions a

JOIN response_plans rp
    ON rp.response_id = a.response_id

JOIN risks r
    ON r.risk_id = rp.risk_id

WHERE rp.is_current = TRUE
  AND a.status NOT IN ('COMPLETED', 'CANCELLED')

ORDER BY a.deadline;

-- ---------------------------------------------------------------------------
-- QUERY 12: STRATEGY VALIDATION
-- ---------------------------------------------------------------------------

SELECT
    r.risk_code,
    r.type,
    rp.strategy,

    is_strategy_valid(
        r.type,
        rp.strategy
    ) AS strategy_valid

FROM risks r

JOIN response_plans rp
    ON rp.risk_id = r.risk_id

WHERE rp.is_current = TRUE;

-- ---------------------------------------------------------------------------
-- FAILURE CASE: INVALID STRATEGY
-- Run separately because the statement is expected to fail.
-- ---------------------------------------------------------------------------

-- CALL plan_risk_response(
--     1,
--     'EXPLOIT',
--     3,
--     'Invalid opportunity strategy for a threat.',
--     1000
-- );

-- ---------------------------------------------------------------------------
-- FAILURE CASE: EXCEEDING RESPONSE BUDGET
-- Run separately because the statement is expected to fail.
-- ---------------------------------------------------------------------------

-- INSERT INTO response_actions (
--     response_id,
--     description,
--     assigned_to,
--     estimated_cost,
--     deadline
-- )
-- VALUES (
--     1,
--     'Expensive additional supplier test.',
--     3,
--     50000,
--     CURRENT_DATE + 15
-- );

-- ---------------------------------------------------------------------------
-- FAILURE CASE: SELF-APPROVAL
-- Run separately because the statement is expected to fail.
-- ---------------------------------------------------------------------------

-- INSERT INTO response_approvals (
--     response_id,
--     approver_id,
--     decision
-- )
-- VALUES (
--     1,
--     3,
--     'APPROVED'
-- );

-- ---------------------------------------------------------------------------
-- PERFORMANCE AND OPERATIONAL NOTES
-- ---------------------------------------------------------------------------

-- 1. The partial unique index permits historical response versions
--    while enforcing one current plan per risk.
--
-- 2. The risk exposure view uses a lateral query to retrieve the
--    latest residual assessment.
--
-- 3. Composite indexes support project dashboards, action queues
--    and chronological risk history.
--
-- 4. The response budget trigger checks committed action costs.
--    Concurrent budget changes in high-volume systems should be
--    serialized by locking the corresponding response plan.
--
-- 5. Approval and response execution are separate decisions.
--
-- 6. Residual assessments are append-only historical observations
--    rather than replacements for inherent risk.
--
-- 7. Financial EMV is meaningful only when impact is expressed
--    in a consistent monetary unit.
--
-- 8. Production systems should enforce participant authorization
--    at the application or database security layer, use restricted
--    database roles, and maintain immutable audit records.
--
-- 9. This script uses illustrative approval and risk scoring rules.
--    Organization-specific delegations and tolerances must be
--    configured through governed policy.
