-- ============================================================
-- TEAM PERFORMANCE EVALUATION AND MANAGEMENT SYSTEM
-- PostgreSQL 15+
--
-- Includes:
-- Teams, members, objectives, performance metrics,
-- evaluation policies, historical evaluations,
-- improvement plans, action tracking and reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS team_performance;

SET search_path TO team_performance, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE performance_band AS ENUM (
    'EXCELLENT',
    'STRONG',
    'SATISFACTORY',
    'NEEDS_IMPROVEMENT',
    'CRITICAL'
);

CREATE TYPE evaluation_status AS ENUM (
    'DRAFT',
    'COMPLETED',
    'APPROVED',
    'REJECTED'
);

CREATE TYPE action_status AS ENUM (
    'OPEN',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED'
);

CREATE TYPE objective_status AS ENUM (
    'PLANNED',
    'ACTIVE',
    'COMPLETED',
    'ON_HOLD',
    'CANCELLED'
);

-- ------------------------------------------------------------
-- 2. TEAMS
-- ------------------------------------------------------------

CREATE TABLE teams (
    team_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    team_code VARCHAR(30) NOT NULL UNIQUE,

    team_name VARCHAR(150) NOT NULL,

    department VARCHAR(120) NOT NULL,

    manager_name VARCHAR(150) NOT NULL,

    member_count INTEGER NOT NULL CHECK (member_count > 0),

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 3. TEAM MEMBERS
-- ------------------------------------------------------------

CREATE TABLE team_members (
    member_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    team_id BIGINT NOT NULL
        REFERENCES teams(team_id),

    employee_code VARCHAR(40) NOT NULL UNIQUE,

    employee_name VARCHAR(150) NOT NULL,

    role_name VARCHAR(100) NOT NULL,

    joined_on DATE NOT NULL DEFAULT CURRENT_DATE,

    left_on DATE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_membership_period
        CHECK (left_on IS NULL OR left_on >= joined_on)
);

CREATE INDEX idx_members_team
ON team_members(team_id, active);

-- ------------------------------------------------------------
-- 4. TEAM OBJECTIVES
-- ------------------------------------------------------------

CREATE TABLE team_objectives (
    objective_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    team_id BIGINT NOT NULL
        REFERENCES teams(team_id),

    objective_name VARCHAR(200) NOT NULL,

    description TEXT,

    target_value NUMERIC(12,2) NOT NULL
        CHECK (target_value > 0),

    actual_value NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (actual_value >= 0),

    weight NUMERIC(5,4) NOT NULL
        CHECK (weight BETWEEN 0 AND 1),

    due_date DATE NOT NULL,

    status objective_status NOT NULL DEFAULT 'PLANNED',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_objectives_team_status
ON team_objectives(team_id, status);

-- ------------------------------------------------------------
-- 5. PERFORMANCE METRIC DEFINITIONS
-- ------------------------------------------------------------

CREATE TABLE metric_definitions (
    metric_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    metric_code VARCHAR(50) NOT NULL UNIQUE,

    metric_name VARCHAR(100) NOT NULL,

    description TEXT,

    default_weight NUMERIC(5,4) NOT NULL
        CHECK (default_weight BETWEEN 0 AND 1),

    active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO metric_definitions (
    metric_code,
    metric_name,
    description,
    default_weight
)
VALUES
(
    'GOAL_ACHIEVEMENT',
    'Goal Achievement',
    'Extent to which agreed team objectives are achieved.',
    0.25
),
(
    'PRODUCTIVITY',
    'Productivity',
    'Work output relative to available resources.',
    0.20
),
(
    'WORK_QUALITY',
    'Work Quality',
    'Accuracy and quality of completed deliverables.',
    0.20
),
(
    'COLLABORATION',
    'Collaboration',
    'Communication, knowledge sharing and teamwork.',
    0.15
),
(
    'RELIABILITY',
    'Reliability',
    'Dependability and operational consistency.',
    0.10
),
(
    'DELIVERY_CONSISTENCY',
    'Delivery Consistency',
    'Consistency in meeting agreed delivery commitments.',
    0.10
);

-- ------------------------------------------------------------
-- 6. EVALUATION POLICIES
-- ------------------------------------------------------------

CREATE TABLE evaluation_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(150) NOT NULL,

    version INTEGER NOT NULL CHECK (version > 0),

    effective_from DATE NOT NULL,

    effective_to DATE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(policy_name, version),

    CHECK (
        effective_to IS NULL OR effective_to >= effective_from
    )
);

CREATE TABLE policy_weights (
    policy_id BIGINT NOT NULL
        REFERENCES evaluation_policies(policy_id),

    metric_id SMALLINT NOT NULL
        REFERENCES metric_definitions(metric_id),

    weight NUMERIC(5,4) NOT NULL
        CHECK (weight BETWEEN 0 AND 1),

    PRIMARY KEY(policy_id, metric_id)
);

-- The evaluation function verifies the complete policy
-- and its total weight before calculating a score.

CREATE OR REPLACE FUNCTION validate_policy_weights(
    p_policy_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_total NUMERIC;
    v_count INTEGER;
    v_expected INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_expected
    FROM metric_definitions
    WHERE active = TRUE;

    SELECT
        COALESCE(SUM(pw.weight), 0),
        COUNT(*)
    INTO v_total, v_count
    FROM policy_weights pw
    JOIN metric_definitions md
        ON md.metric_id = pw.metric_id
    WHERE pw.policy_id = p_policy_id
      AND md.active = TRUE;

    IF v_count <> v_expected THEN
        RETURN FALSE;
    END IF;

    RETURN ABS(v_total - 1.0) <= 0.000001;
END;
$$;

INSERT INTO evaluation_policies (
    policy_name,
    version,
    effective_from
)
VALUES (
    'Standard Team Evaluation',
    1,
    DATE '2026-01-01'
);

INSERT INTO policy_weights (
    policy_id,
    metric_id,
    weight
)
SELECT
    1,
    metric_id,
    default_weight
FROM metric_definitions;

-- ------------------------------------------------------------
-- 7. PERFORMANCE EVALUATIONS
-- ------------------------------------------------------------

CREATE TABLE team_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    team_id BIGINT NOT NULL
        REFERENCES teams(team_id),

    policy_id BIGINT NOT NULL
        REFERENCES evaluation_policies(policy_id),

    evaluation_period VARCHAR(20) NOT NULL,

    period_start DATE NOT NULL,

    period_end DATE NOT NULL,

    evaluator_name VARCHAR(150) NOT NULL,

    total_score NUMERIC(6,2),

    band performance_band,

    status evaluation_status NOT NULL DEFAULT 'DRAFT',

    previous_score NUMERIC(6,2),

    trend VARCHAR(20),

    evaluated_at TIMESTAMPTZ,

    approved_by VARCHAR(150),

    approved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_evaluation_period
        CHECK (period_end >= period_start),

    CONSTRAINT valid_total_score
        CHECK (
            total_score IS NULL OR total_score BETWEEN 0 AND 100
        ),

    CONSTRAINT valid_previous_score
        CHECK (
            previous_score IS NULL OR previous_score BETWEEN 0 AND 100
        ),

    UNIQUE(team_id, evaluation_period),

    CHECK (
        status <> 'APPROVED'
        OR (
            total_score IS NOT NULL
            AND band IS NOT NULL
            AND approved_by IS NOT NULL
            AND approved_at IS NOT NULL
        )
    )
);

CREATE INDEX idx_evaluations_team_period
ON team_evaluations(team_id, period_start DESC);

CREATE INDEX idx_evaluations_status
ON team_evaluations(status, period_end);

-- ------------------------------------------------------------
-- 8. INDIVIDUAL EVALUATION METRICS
-- ------------------------------------------------------------

CREATE TABLE evaluation_metrics (
    evaluation_id BIGINT NOT NULL
        REFERENCES team_evaluations(evaluation_id)
        ON DELETE CASCADE,

    metric_id SMALLINT NOT NULL
        REFERENCES metric_definitions(metric_id),

    metric_score NUMERIC(5,2) NOT NULL
        CHECK (metric_score BETWEEN 0 AND 100),

    evidence_description TEXT,

    PRIMARY KEY(evaluation_id, metric_id)
);

-- ------------------------------------------------------------
-- 9. IMPROVEMENT ACTIONS
-- ------------------------------------------------------------

CREATE TABLE improvement_actions (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    evaluation_id BIGINT NOT NULL
        REFERENCES team_evaluations(evaluation_id),

    metric_id SMALLINT NOT NULL
        REFERENCES metric_definitions(metric_id),

    action_description TEXT NOT NULL,

    responsible_person VARCHAR(150) NOT NULL,

    due_date DATE NOT NULL,

    status action_status NOT NULL DEFAULT 'OPEN',

    completion_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_improvement_actions_status
ON improvement_actions(status, due_date);

CREATE INDEX idx_improvement_actions_evaluation
ON improvement_actions(evaluation_id);

-- ------------------------------------------------------------
-- 10. EVALUATION VALIDATION TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_evaluation_integrity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_metric_count INTEGER;
    v_expected_count INTEGER;
BEGIN
    IF NEW.status IN ('COMPLETED', 'APPROVED') THEN

        IF NOT validate_policy_weights(NEW.policy_id) THEN
            RAISE EXCEPTION
                'Evaluation policy has incomplete or invalid weights.';
        END IF;

        SELECT COUNT(*)
        INTO v_expected_count
        FROM metric_definitions
        WHERE active = TRUE;

        SELECT COUNT(*)
        INTO v_metric_count
        FROM evaluation_metrics em
        JOIN metric_definitions md
            ON md.metric_id = em.metric_id
        WHERE em.evaluation_id = NEW.evaluation_id
          AND md.active = TRUE;

        IF v_metric_count <> v_expected_count THEN
            RAISE EXCEPTION
                'All active performance metrics must be recorded.';
        END IF;

        IF NEW.total_score IS NULL OR NEW.band IS NULL THEN
            RAISE EXCEPTION
                'Completed evaluation requires a score and performance band.';
        END IF;

        IF NEW.evaluated_at IS NULL THEN
            NEW.evaluated_at := CURRENT_TIMESTAMP;
        END IF;
    END IF;

    IF NEW.status = 'APPROVED' THEN
        IF NEW.approved_by IS NULL OR
           NEW.approved_at IS NULL THEN
            RAISE EXCEPTION
                'Approval identity and timestamp are required.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_evaluation_integrity
BEFORE INSERT OR UPDATE
ON team_evaluations
FOR EACH ROW
EXECUTE FUNCTION enforce_evaluation_integrity();

-- ------------------------------------------------------------
-- 11. PERFORMANCE CALCULATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_team_score(
    p_evaluation_id BIGINT
)
RETURNS NUMERIC(6,2)
LANGUAGE plpgsql
AS $$
DECLARE
    v_policy_id BIGINT;
    v_score NUMERIC(10,4);
    v_count INTEGER;
    v_expected INTEGER;
BEGIN
    SELECT policy_id
    INTO v_policy_id
    FROM team_evaluations
    WHERE evaluation_id = p_evaluation_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Evaluation does not exist.';
    END IF;

    IF NOT validate_policy_weights(v_policy_id) THEN
        RAISE EXCEPTION 'Evaluation policy is invalid.';
    END IF;

    SELECT COUNT(*)
    INTO v_expected
    FROM metric_definitions
    WHERE active = TRUE;

    SELECT COUNT(*)
    INTO v_count
    FROM evaluation_metrics em
    JOIN metric_definitions md
        ON md.metric_id = em.metric_id
    WHERE em.evaluation_id = p_evaluation_id
      AND md.active = TRUE;

    IF v_count <> v_expected THEN
        RAISE EXCEPTION
            'Incomplete evaluation metrics: expected %, received %.',
            v_expected,
            v_count;
    END IF;

    SELECT SUM(
        em.metric_score * pw.weight
    )
    INTO v_score
    FROM evaluation_metrics em
    JOIN policy_weights pw
        ON pw.metric_id = em.metric_id
    JOIN metric_definitions md
        ON md.metric_id = em.metric_id
    WHERE em.evaluation_id = p_evaluation_id
      AND pw.policy_id = v_policy_id
      AND md.active = TRUE;

    RETURN ROUND(v_score, 2);
END;
$$;

-- ------------------------------------------------------------
-- 12. PERFORMANCE CLASSIFICATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION classify_performance(
    p_score NUMERIC
)
RETURNS performance_band
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_score IS NULL OR p_score < 0 OR p_score > 100 THEN
        RAISE EXCEPTION 'Score must be between 0 and 100.';
    END IF;

    RETURN CASE
        WHEN p_score >= 90 THEN 'EXCELLENT'::performance_band
        WHEN p_score >= 80 THEN 'STRONG'::performance_band
        WHEN p_score >= 70 THEN 'SATISFACTORY'::performance_band
        WHEN p_score >= 60 THEN 'NEEDS_IMPROVEMENT'::performance_band
        ELSE 'CRITICAL'::performance_band
    END;
END;
$$;

-- ------------------------------------------------------------
-- 13. EVALUATION PROCESSING PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE process_team_evaluation(
    p_evaluation_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_score NUMERIC(6,2);
    v_previous NUMERIC(6,2);
    v_team_id BIGINT;
    v_period_start DATE;
BEGIN
    SELECT team_id, period_start
    INTO v_team_id, v_period_start
    FROM team_evaluations
    WHERE evaluation_id = p_evaluation_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Evaluation not found.';
    END IF;

    v_score := calculate_team_score(p_evaluation_id);

    SELECT total_score
    INTO v_previous
    FROM team_evaluations
    WHERE team_id = v_team_id
      AND status IN ('COMPLETED', 'APPROVED')
      AND period_start < v_period_start
    ORDER BY period_start DESC
    LIMIT 1;

    UPDATE team_evaluations
    SET
        total_score = v_score,
        band = classify_performance(v_score),
        previous_score = v_previous,
        trend = CASE
            WHEN v_previous IS NULL THEN 'NOT_AVAILABLE'
            WHEN v_score > v_previous THEN 'IMPROVING'
            WHEN v_score < v_previous THEN 'DECLINING'
            ELSE 'STABLE'
        END,
        status = 'COMPLETED',
        evaluated_at = CURRENT_TIMESTAMP
    WHERE evaluation_id = p_evaluation_id;
END;
$$;

-- ------------------------------------------------------------
-- 14. PERFORMANCE REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW team_performance_report AS
SELECT
    t.team_id,
    t.team_code,
    t.team_name,
    t.department,
    t.member_count,
    e.evaluation_id,
    e.evaluation_period,
    e.total_score,
    e.band,
    e.trend,
    e.status,
    e.evaluated_at
FROM teams t
LEFT JOIN team_evaluations e
    ON e.team_id = t.team_id;

-- ------------------------------------------------------------
-- 15. TEAM METRIC DETAIL VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW team_metric_report AS
SELECT
    t.team_code,
    t.team_name,
    e.evaluation_period,
    md.metric_name,
    em.metric_score,
    pw.weight,
    ROUND(em.metric_score * pw.weight, 2) AS weighted_contribution
FROM team_evaluations e
JOIN teams t
    ON t.team_id = e.team_id
JOIN evaluation_metrics em
    ON em.evaluation_id = e.evaluation_id
JOIN metric_definitions md
    ON md.metric_id = em.metric_id
JOIN policy_weights pw
    ON pw.policy_id = e.policy_id
   AND pw.metric_id = em.metric_id;

-- ------------------------------------------------------------
-- 16. SAMPLE TEAMS
-- ------------------------------------------------------------

INSERT INTO teams (
    team_code,
    team_name,
    department,
    manager_name,
    member_count
)
VALUES
(
    'T001',
    'Engineering',
    'Technology',
    'Manager A',
    12
),
(
    'T002',
    'Customer Support',
    'Operations',
    'Manager B',
    10
),
(
    'T003',
    'Research',
    'R&D',
    'Manager C',
    8
),
(
    'T004',
    'Quality Assurance',
    'Technology',
    'Manager D',
    6
);

-- ------------------------------------------------------------
-- 17. SAMPLE TEAM MEMBERS
-- ------------------------------------------------------------

INSERT INTO team_members (
    team_id,
    employee_code,
    employee_name,
    role_name
)
VALUES
(1, 'EMP001', 'Employee A', 'Team Lead'),
(1, 'EMP002', 'Employee B', 'Software Engineer'),
(1, 'EMP003', 'Employee C', 'Software Engineer'),
(2, 'EMP004', 'Employee D', 'Support Lead'),
(2, 'EMP005', 'Employee E', 'Support Specialist'),
(3, 'EMP006', 'Employee F', 'Research Lead'),
(4, 'EMP007', 'Employee G', 'Quality Lead');

-- ------------------------------------------------------------
-- 18. SAMPLE OBJECTIVES
-- ------------------------------------------------------------

INSERT INTO team_objectives (
    team_id,
    objective_name,
    description,
    target_value,
    actual_value,
    weight,
    due_date,
    status
)
VALUES
(
    1,
    'Release Delivery',
    'Deliver planned engineering releases.',
    100,
    92,
    0.50,
    DATE '2026-12-31',
    'ACTIVE'
),
(
    1,
    'Defect Reduction',
    'Improve product quality.',
    100,
    95,
    0.50,
    DATE '2026-12-31',
    'ACTIVE'
),
(
    2,
    'Customer Resolution',
    'Meet customer support resolution targets.',
    100,
    85,
    1.00,
    DATE '2026-12-31',
    'ACTIVE'
),
(
    3,
    'Research Milestones',
    'Complete planned research milestones.',
    100,
    72,
    1.00,
    DATE '2026-12-31',
    'ACTIVE'
);

-- ------------------------------------------------------------
-- 19. CREATE EVALUATIONS
-- ------------------------------------------------------------

INSERT INTO team_evaluations (
    team_id,
    policy_id,
    evaluation_period,
    period_start,
    period_end,
    evaluator_name,
    previous_score,
    trend
)
VALUES
(1, 1, '2026-Q4', DATE '2026-10-01', DATE '2026-12-31',
 'Director A', 84, 'NOT_AVAILABLE'),
(2, 1, '2026-Q4', DATE '2026-10-01', DATE '2026-12-31',
 'Director A', 82, 'NOT_AVAILABLE'),
(3, 1, '2026-Q4', DATE '2026-10-01', DATE '2026-12-31',
 'Director B', 80, 'NOT_AVAILABLE'),
(4, 1, '2026-Q4', DATE '2026-10-01', DATE '2026-12-31',
 'Director B', 70, 'NOT_AVAILABLE');

-- ------------------------------------------------------------
-- 20. RECORD METRICS
-- ------------------------------------------------------------

INSERT INTO evaluation_metrics (
    evaluation_id,
    metric_id,
    metric_score,
    evidence_description
)
SELECT
    sample.evaluation_id,
    md.metric_id,
    sample.metric_score,
    'Quarterly team performance evidence'
FROM (
    VALUES
    (1, 'GOAL_ACHIEVEMENT', 92::NUMERIC),
    (1, 'PRODUCTIVITY', 88),
    (1, 'WORK_QUALITY', 95),
    (1, 'COLLABORATION', 85),
    (1, 'RELIABILITY', 90),
    (1, 'DELIVERY_CONSISTENCY', 87),

    (2, 'GOAL_ACHIEVEMENT', 78),
    (2, 'PRODUCTIVITY', 85),
    (2, 'WORK_QUALITY', 82),
    (2, 'COLLABORATION', 91),
    (2, 'RELIABILITY', 88),
    (2, 'DELIVERY_CONSISTENCY', 80),

    (3, 'GOAL_ACHIEVEMENT', 95),
    (3, 'PRODUCTIVITY', 72),
    (3, 'WORK_QUALITY', 90),
    (3, 'COLLABORATION', 80),
    (3, 'RELIABILITY', 75),
    (3, 'DELIVERY_CONSISTENCY', 78),

    (4, 'GOAL_ACHIEVEMENT', 65),
    (4, 'PRODUCTIVITY', 68),
    (4, 'WORK_QUALITY', 92),
    (4, 'COLLABORATION', 75),
    (4, 'RELIABILITY', 70),
    (4, 'DELIVERY_CONSISTENCY', 62)
) AS sample(
    evaluation_id,
    metric_code,
    metric_score
)
JOIN metric_definitions md
    ON md.metric_code = sample.metric_code;

-- ------------------------------------------------------------
-- 21. PROCESS EVALUATIONS
-- ------------------------------------------------------------

CALL process_team_evaluation(1);
CALL process_team_evaluation(2);
CALL process_team_evaluation(3);
CALL process_team_evaluation(4);

-- ------------------------------------------------------------
-- 22. IMPROVEMENT ACTIONS
-- ------------------------------------------------------------

INSERT INTO improvement_actions (
    evaluation_id,
    metric_id,
    action_description,
    responsible_person,
    due_date
)
SELECT
    e.evaluation_id,
    md.metric_id,
    CASE md.metric_code
        WHEN 'PRODUCTIVITY'
            THEN 'Improve workload planning and task estimation.'
        WHEN 'DELIVERY_CONSISTENCY'
            THEN 'Improve delivery scheduling and progress monitoring.'
        ELSE 'Develop a measurable improvement plan.'
    END,
    t.manager_name,
    DATE '2026-12-15'
FROM team_evaluations e
JOIN teams t
    ON t.team_id = e.team_id
JOIN metric_definitions md
    ON md.metric_code IN (
        'PRODUCTIVITY',
        'DELIVERY_CONSISTENCY'
    )
JOIN evaluation_metrics em
    ON em.evaluation_id = e.evaluation_id
   AND em.metric_id = md.metric_id
WHERE em.metric_score < 80;

-- ------------------------------------------------------------
-- 23. APPROVE ELIGIBLE EVALUATIONS
-- ------------------------------------------------------------

UPDATE team_evaluations
SET
    status = 'APPROVED',
    approved_by = 'Performance Director',
    approved_at = CURRENT_TIMESTAMP
WHERE status = 'COMPLETED'
  AND total_score >= 60;

-- ------------------------------------------------------------
-- 24. RETRIEVAL
-- ------------------------------------------------------------

SELECT
    team_code,
    team_name,
    department,
    member_count
FROM teams
WHERE active = TRUE
ORDER BY team_name;

-- ------------------------------------------------------------
-- 25. AGGREGATION AND ORGANIZATIONAL REPORTING
-- ------------------------------------------------------------

SELECT
    department,
    COUNT(DISTINCT team_id) AS evaluated_teams,
    ROUND(AVG(total_score), 2) AS average_score,
    ROUND(MIN(total_score), 2) AS lowest_score,
    ROUND(MAX(total_score), 2) AS highest_score
FROM team_performance_report
WHERE status IN ('COMPLETED', 'APPROVED')
GROUP BY department
ORDER BY average_score DESC;

-- ------------------------------------------------------------
-- 26. PERFORMANCE DISTRIBUTION
-- ------------------------------------------------------------

SELECT
    band,
    COUNT(*) AS team_count,
    ROUND(
        COUNT(*) * 100.0 /
        NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS percentage
FROM team_evaluations
WHERE status IN ('COMPLETED', 'APPROVED')
GROUP BY band
ORDER BY team_count DESC;

-- ------------------------------------------------------------
-- 27. METRIC-LEVEL EVALUATION
-- ------------------------------------------------------------

SELECT
    team_name,
    metric_name,
    metric_score,
    weight,
    weighted_contribution
FROM team_metric_report
ORDER BY team_name, weighted_contribution DESC;

-- ------------------------------------------------------------
-- 28. IDENTIFY IMPROVEMENT AREAS
-- ------------------------------------------------------------

SELECT
    t.team_name,
    md.metric_name,
    em.metric_score,
    ia.action_description,
    ia.responsible_person,
    ia.due_date,
    ia.status
FROM evaluation_metrics em
JOIN team_evaluations e
    ON e.evaluation_id = em.evaluation_id
JOIN teams t
    ON t.team_id = e.team_id
JOIN metric_definitions md
    ON md.metric_id = em.metric_id
LEFT JOIN improvement_actions ia
    ON ia.evaluation_id = e.evaluation_id
   AND ia.metric_id = em.metric_id
WHERE em.metric_score < 70
ORDER BY em.metric_score ASC;

-- ------------------------------------------------------------
-- 29. HISTORICAL PERFORMANCE AND TREND ANALYSIS
-- ------------------------------------------------------------

WITH evaluation_history AS (
    SELECT
        team_id,
        evaluation_period,
        period_start,
        total_score,
        LAG(total_score) OVER (
            PARTITION BY team_id
            ORDER BY period_start
        ) AS previous_score
    FROM team_evaluations
    WHERE status IN ('COMPLETED', 'APPROVED')
)
SELECT
    t.team_name,
    h.evaluation_period,
    h.total_score,
    h.previous_score,
    CASE
        WHEN h.previous_score IS NULL THEN 'NOT AVAILABLE'
        WHEN h.total_score > h.previous_score THEN 'IMPROVING'
        WHEN h.total_score < h.previous_score THEN 'DECLINING'
        ELSE 'STABLE'
    END AS performance_trend
FROM evaluation_history h
JOIN teams t
    ON t.team_id = h.team_id
ORDER BY t.team_name, h.period_start;

-- ------------------------------------------------------------
-- 30. OBJECTIVE ACHIEVEMENT
-- ------------------------------------------------------------

SELECT
    t.team_name,
    o.objective_name,
    o.target_value,
    o.actual_value,
    ROUND(
        LEAST(
            o.actual_value / NULLIF(o.target_value, 0) * 100,
            100
        ),
        2
    ) AS achievement_percentage,
    o.status
FROM team_objectives o
JOIN teams t
    ON t.team_id = o.team_id
ORDER BY t.team_name, achievement_percentage DESC;

-- ------------------------------------------------------------
-- 31. IMPROVEMENT ACTION MONITORING
-- ------------------------------------------------------------

SELECT
    t.team_name,
    ia.action_description,
    ia.responsible_person,
    ia.due_date,
    ia.status,
    CASE
        WHEN ia.status = 'COMPLETED' THEN 'CLOSED'
        WHEN ia.due_date < CURRENT_DATE THEN 'OVERDUE'
        ELSE 'ON SCHEDULE'
    END AS schedule_status
FROM improvement_actions ia
JOIN team_evaluations e
    ON e.evaluation_id = ia.evaluation_id
JOIN teams t
    ON t.team_id = e.team_id
ORDER BY ia.due_date;

-- ------------------------------------------------------------
-- 32. ELIGIBILITY DETERMINATION
-- ------------------------------------------------------------

SELECT
    evaluation_id,
    team_id,
    total_score,
    band,
    CASE
        WHEN status = 'APPROVED'
            THEN 'APPROVED'
        WHEN status = 'COMPLETED'
             AND total_score >= 60
            THEN 'ELIGIBLE FOR APPROVAL'
        WHEN status = 'DRAFT'
            THEN 'PENDING EVALUATION'
        ELSE 'NOT ELIGIBLE'
    END AS approval_eligibility
FROM team_evaluations
ORDER BY evaluation_id;

-- ------------------------------------------------------------
-- 33. TRANSACTIONAL IMPROVEMENT UPDATE
-- ------------------------------------------------------------

SAVEPOINT before_action_update;

UPDATE improvement_actions
SET
    status = 'IN_PROGRESS'
WHERE action_id = (
    SELECT MIN(action_id)
    FROM improvement_actions
    WHERE status = 'OPEN'
);

-- Releasing the savepoint preserves the update.
RELEASE SAVEPOINT before_action_update;

-- ------------------------------------------------------------
-- 34. DATA VALIDATION QUERIES
-- ------------------------------------------------------------

-- Inactive members still counted in team membership.
SELECT
    t.team_code,
    t.member_count,
    COUNT(tm.member_id) FILTER (
        WHERE tm.active = TRUE
    ) AS active_member_records
FROM teams t
LEFT JOIN team_members tm
    ON tm.team_id = t.team_id
GROUP BY t.team_id;

-- Incomplete evaluations.
SELECT
    e.evaluation_id,
    e.evaluation_period,
    COUNT(em.metric_id) AS recorded_metrics
FROM team_evaluations e
LEFT JOIN evaluation_metrics em
    ON em.evaluation_id = e.evaluation_id
GROUP BY e.evaluation_id, e.evaluation_period
HAVING COUNT(em.metric_id) < (
    SELECT COUNT(*)
    FROM metric_definitions
    WHERE active = TRUE
);

-- Invalid policy configuration.
SELECT
    policy_id,
    policy_name,
    validate_policy_weights(policy_id) AS policy_valid
FROM evaluation_policies;

COMMIT;

-- ------------------------------------------------------------
-- 35. SECURITY AND OPERATIONAL NOTES
-- ------------------------------------------------------------

-- In production:
-- 1. Grant SELECT access separately from evaluation write access.
-- 2. Restrict approval operations to authorized reviewers.
-- 3. Use separate database roles for reporting and administration.
-- 4. Avoid exposing employee-level information in aggregate reports.
-- 5. Audit policy changes and evaluation approvals.
-- 6. Apply row-level security when departments require isolation.
-- 7. Use transactions for evaluation processing and approval.
-- 8. Back up historical evaluation records.
--
-- Example role creation, executed by a privileged administrator:
--
-- CREATE ROLE team_performance_reader;
-- GRANT USAGE ON SCHEMA team_performance TO team_performance_reader;
-- GRANT SELECT ON ALL TABLES IN SCHEMA team_performance
-- TO team_performance_reader;
--
-- The sample member_count field is an organizational snapshot.
-- Reconcile it against active membership records in production.
-- ============================================================
