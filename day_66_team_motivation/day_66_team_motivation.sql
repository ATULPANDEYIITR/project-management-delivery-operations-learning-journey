-- ============================================================
-- TEAM MOTIVATION MANAGEMENT SYSTEM
-- PostgreSQL 14+
--
-- Models:
--   Organizations
--   Teams
--   Employees
--   Motivation assessments
--   Motivation dimensions
--   Team goals
--   Goal progress
--   Recognition
--   Intervention plans
--   Team reports
--
-- Includes:
--   Constraints
--   Indexes
--   Views
--   Functions
--   Procedures
--   Triggers
--   CTE reporting
--   Transaction examples
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS team_motivation;

SET search_path TO team_motivation, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE motivation_level AS ENUM (
    'HIGH',
    'MODERATE',
    'LOW',
    'CRITICAL'
);

CREATE TYPE goal_status AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'COMPLETED',
    'BLOCKED'
);

CREATE TYPE recognition_type AS ENUM (
    'PUBLIC',
    'PRIVATE',
    'DEVELOPMENT',
    'FINANCIAL',
    'TEAM'
);

CREATE TYPE intervention_status AS ENUM (
    'PLANNED',
    'ACTIVE',
    'COMPLETED',
    'CANCELLED'
);

-- ============================================================
-- 2. ORGANIZATION AND TEAM STRUCTURE
-- ============================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    organization_name VARCHAR(150) NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE teams (
    team_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id)
        ON DELETE RESTRICT,

    team_name VARCHAR(120) NOT NULL,

    department VARCHAR(120) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (organization_id, team_name)
);

CREATE TABLE employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    team_id BIGINT NOT NULL
        REFERENCES teams(team_id)
        ON DELETE RESTRICT,

    employee_name VARCHAR(120) NOT NULL,

    job_role VARCHAR(100) NOT NULL,

    email VARCHAR(255) NOT NULL UNIQUE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (LENGTH(TRIM(employee_name)) > 0),

    CHECK (LENGTH(TRIM(job_role)) > 0)
);

CREATE INDEX idx_employees_team_active
    ON employees(team_id, active);

-- ============================================================
-- 3. MOTIVATION ASSESSMENTS
-- ============================================================

CREATE TABLE motivation_assessments (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    employee_id BIGINT NOT NULL
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    assessment_date DATE NOT NULL DEFAULT CURRENT_DATE,

    autonomy NUMERIC(5,2) NOT NULL,

    competence NUMERIC(5,2) NOT NULL,

    relatedness NUMERIC(5,2) NOT NULL,

    workload NUMERIC(5,2) NOT NULL,

    psychological_safety NUMERIC(5,2) NOT NULL,

    engagement NUMERIC(5,2) NOT NULL,

    intrinsic_motivation NUMERIC(5,2) NOT NULL,

    extrinsic_motivation NUMERIC(5,2) NOT NULL,

    motivation_score NUMERIC(5,2),

    motivation_category motivation_level,

    comments TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (autonomy BETWEEN 0 AND 100),

    CHECK (competence BETWEEN 0 AND 100),

    CHECK (relatedness BETWEEN 0 AND 100),

    CHECK (workload BETWEEN 0 AND 100),

    CHECK (psychological_safety BETWEEN 0 AND 100),

    CHECK (engagement BETWEEN 0 AND 100),

    CHECK (intrinsic_motivation BETWEEN 0 AND 100),

    CHECK (extrinsic_motivation BETWEEN 0 AND 100),

    CHECK (
        motivation_score IS NULL
        OR motivation_score BETWEEN 0 AND 100
    ),

    UNIQUE(employee_id, assessment_date)
);

CREATE INDEX idx_assessments_employee_date
    ON motivation_assessments(
        employee_id,
        assessment_date DESC
    );

CREATE INDEX idx_assessments_category
    ON motivation_assessments(
        motivation_category,
        assessment_date DESC
    );

-- ============================================================
-- 4. MOTIVATION SCORE CALCULATION
-- ============================================================

CREATE FUNCTION calculate_motivation_score(
    p_autonomy NUMERIC,
    p_competence NUMERIC,
    p_relatedness NUMERIC,
    p_workload NUMERIC,
    p_psychological_safety NUMERIC,
    p_engagement NUMERIC,
    p_intrinsic NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN

    IF
        p_autonomy NOT BETWEEN 0 AND 100
        OR p_competence NOT BETWEEN 0 AND 100
        OR p_relatedness NOT BETWEEN 0 AND 100
        OR p_workload NOT BETWEEN 0 AND 100
        OR p_psychological_safety NOT BETWEEN 0 AND 100
        OR p_engagement NOT BETWEEN 0 AND 100
        OR p_intrinsic NOT BETWEEN 0 AND 100
    THEN
        RAISE EXCEPTION
            'Motivation dimensions must be between 0 and 100';
    END IF;

    RETURN ROUND(
        (
            p_autonomy * 0.18
            + p_competence * 0.18
            + p_relatedness * 0.16
            + p_psychological_safety * 0.16
            + p_engagement * 0.14
            + p_intrinsic * 0.12
            + (100 - p_workload) * 0.06
        )::NUMERIC,
        2
    );

END;
$$;

CREATE FUNCTION classify_motivation(
    p_score NUMERIC
)
RETURNS motivation_level
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN

    IF p_score NOT BETWEEN 0 AND 100 THEN
        RAISE EXCEPTION 'Invalid motivation score';
    END IF;

    RETURN CASE
        WHEN p_score >= 80 THEN 'HIGH'::motivation_level
        WHEN p_score >= 65 THEN 'MODERATE'::motivation_level
        WHEN p_score >= 45 THEN 'LOW'::motivation_level
        ELSE 'CRITICAL'::motivation_level
    END;

END;
$$;

-- Automatically calculate the score before saving an assessment.

CREATE FUNCTION set_motivation_score()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    NEW.motivation_score := calculate_motivation_score(
        NEW.autonomy,
        NEW.competence,
        NEW.relatedness,
        NEW.workload,
        NEW.psychological_safety,
        NEW.engagement,
        NEW.intrinsic_motivation
    );

    NEW.motivation_category :=
        classify_motivation(NEW.motivation_score);

    RETURN NEW;

END;
$$;

CREATE TRIGGER trg_calculate_motivation
BEFORE INSERT OR UPDATE OF
    autonomy,
    competence,
    relatedness,
    workload,
    psychological_safety,
    engagement,
    intrinsic_motivation
ON motivation_assessments
FOR EACH ROW
EXECUTE FUNCTION set_motivation_score();

-- ============================================================
-- 5. TEAM GOALS
-- ============================================================

CREATE TABLE team_goals (
    goal_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    team_id BIGINT NOT NULL
        REFERENCES teams(team_id)
        ON DELETE RESTRICT,

    owner_id BIGINT NOT NULL
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    description VARCHAR(300) NOT NULL,

    target_value NUMERIC(12,2) NOT NULL,

    current_progress NUMERIC(12,2) NOT NULL DEFAULT 0,

    status goal_status NOT NULL DEFAULT 'NOT_STARTED',

    due_date DATE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (target_value > 0),

    CHECK (
        current_progress >= 0
        AND current_progress <= target_value
    ),

    CHECK (LENGTH(TRIM(description)) > 0)
);

CREATE INDEX idx_goals_team_status
    ON team_goals(team_id, status);

CREATE TABLE goal_progress_history (
    progress_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    goal_id BIGINT NOT NULL
        REFERENCES team_goals(goal_id)
        ON DELETE RESTRICT,

    previous_progress NUMERIC(12,2) NOT NULL,

    new_progress NUMERIC(12,2) NOT NULL,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE FUNCTION validate_goal_progress()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF NEW.owner_id NOT IN (
        SELECT employee_id
        FROM employees
        WHERE team_id = NEW.team_id
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION
            'Goal owner must be an active member of the same team';
    END IF;

    IF NEW.current_progress = NEW.target_value THEN
        NEW.status := 'COMPLETED';

    ELSIF NEW.current_progress > 0
        AND NEW.status <> 'BLOCKED' THEN
        NEW.status := 'IN_PROGRESS';

    ELSIF NEW.current_progress = 0
        AND NEW.status <> 'BLOCKED' THEN
        NEW.status := 'NOT_STARTED';
    END IF;

    RETURN NEW;

END;
$$;

CREATE TRIGGER trg_validate_goal
BEFORE INSERT OR UPDATE OF
    team_id,
    owner_id,
    target_value,
    current_progress,
    status
ON team_goals
FOR EACH ROW
EXECUTE FUNCTION validate_goal_progress();

CREATE FUNCTION record_goal_progress()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF TG_OP = 'INSERT' THEN

        INSERT INTO goal_progress_history(
            goal_id,
            previous_progress,
            new_progress
        )
        VALUES (
            NEW.goal_id,
            0,
            NEW.current_progress
        );

    ELSIF NEW.current_progress <> OLD.current_progress THEN

        INSERT INTO goal_progress_history(
            goal_id,
            previous_progress,
            new_progress
        )
        VALUES (
            NEW.goal_id,
            OLD.current_progress,
            NEW.current_progress
        );

    END IF;

    RETURN NEW;

END;
$$;

CREATE TRIGGER trg_goal_history
AFTER INSERT OR UPDATE OF current_progress
ON team_goals
FOR EACH ROW
EXECUTE FUNCTION record_goal_progress();

-- ============================================================
-- 6. RECOGNITION MANAGEMENT
-- ============================================================

CREATE TABLE recognitions (
    recognition_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    employee_id BIGINT NOT NULL
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    recognition_category recognition_type NOT NULL,

    reason TEXT NOT NULL,

    awarded_by BIGINT
        REFERENCES employees(employee_id)
        ON DELETE SET NULL,

    awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (LENGTH(TRIM(reason)) > 0)
);

CREATE INDEX idx_recognition_employee
    ON recognitions(employee_id, awarded_at DESC);

-- ============================================================
-- 7. INTERVENTION MANAGEMENT
-- ============================================================

CREATE TABLE interventions (
    intervention_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    employee_id BIGINT NOT NULL
        REFERENCES employees(employee_id)
        ON DELETE RESTRICT,

    intervention_name VARCHAR(150) NOT NULL,

    intervention_description TEXT NOT NULL,

    intervention_status intervention_status
        NOT NULL DEFAULT 'PLANNED',

    assigned_to BIGINT
        REFERENCES employees(employee_id)
        ON DELETE SET NULL,

    planned_date DATE NOT NULL DEFAULT CURRENT_DATE,

    completion_date DATE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        intervention_status <> 'COMPLETED'
        OR completion_date IS NOT NULL
    )
);

CREATE INDEX idx_interventions_status_date
    ON interventions(
        intervention_status,
        planned_date
    );

-- ============================================================
-- 8. AUTOMATED MOTIVATION INTERVENTION RECOMMENDATIONS
-- ============================================================

CREATE FUNCTION recommend_interventions(
    p_employee_id BIGINT
)
RETURNS TABLE (
    recommendation TEXT,
    priority TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_assessment motivation_assessments%ROWTYPE;
BEGIN

    SELECT *
    INTO v_assessment
    FROM motivation_assessments
    WHERE employee_id = p_employee_id
    ORDER BY assessment_date DESC, assessment_id DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'No motivation assessment exists for employee %',
            p_employee_id;
    END IF;

    IF v_assessment.workload > 70 THEN
        recommendation :=
            'Review workload and redistribute responsibilities';
        priority := 'HIGH';
        RETURN NEXT;
    END IF;

    IF v_assessment.autonomy < 60 THEN
        recommendation :=
            'Increase employee autonomy and decision authority';
        priority := 'MEDIUM';
        RETURN NEXT;
    END IF;

    IF v_assessment.competence < 60 THEN
        recommendation :=
            'Provide mentoring and professional development';
        priority := 'MEDIUM';
        RETURN NEXT;
    END IF;

    IF v_assessment.relatedness < 60 THEN
        recommendation :=
            'Improve collaboration and team relationships';
        priority := 'MEDIUM';
        RETURN NEXT;
    END IF;

    IF v_assessment.psychological_safety < 60 THEN
        recommendation :=
            'Improve psychological safety and feedback practices';
        priority := 'HIGH';
        RETURN NEXT;
    END IF;

    IF v_assessment.engagement < 60 THEN
        recommendation :=
            'Conduct an individual engagement discussion';
        priority := 'HIGH';
        RETURN NEXT;
    END IF;

    IF NOT FOUND THEN
        recommendation :=
            'Maintain existing practices and review progress periodically';
        priority := 'LOW';
        RETURN NEXT;
    END IF;

END;
$$;

-- ============================================================
-- 9. TEAM MOTIVATION VIEW
-- ============================================================

CREATE VIEW employee_motivation_latest AS

SELECT DISTINCT ON (e.employee_id)

    e.employee_id,
    e.employee_name,
    e.job_role,
    t.team_id,
    t.team_name,

    a.assessment_date,
    a.autonomy,
    a.competence,
    a.relatedness,
    a.workload,
    a.psychological_safety,
    a.engagement,
    a.intrinsic_motivation,
    a.extrinsic_motivation,
    a.motivation_score,
    a.motivation_category

FROM employees e

JOIN teams t
    ON t.team_id = e.team_id

JOIN motivation_assessments a
    ON a.employee_id = e.employee_id

WHERE e.active = TRUE

ORDER BY
    e.employee_id,
    a.assessment_date DESC,
    a.assessment_id DESC;

-- ============================================================
-- 10. TEAM PERFORMANCE AND MOTIVATION REPORT
-- ============================================================

CREATE VIEW team_motivation_report AS

SELECT

    t.team_id,
    t.team_name,

    COUNT(l.employee_id) AS assessed_employees,

    ROUND(
        AVG(l.motivation_score),
        2
    ) AS average_motivation,

    COUNT(*) FILTER (
        WHERE l.motivation_category = 'HIGH'
    ) AS high_motivation_count,

    COUNT(*) FILTER (
        WHERE l.motivation_category = 'MODERATE'
    ) AS moderate_motivation_count,

    COUNT(*) FILTER (
        WHERE l.motivation_category = 'LOW'
    ) AS low_motivation_count,

    COUNT(*) FILTER (
        WHERE l.motivation_category = 'CRITICAL'
    ) AS critical_motivation_count,

    COUNT(*) FILTER (
        WHERE l.workload >= 85
    ) AS high_workload_count

FROM teams t

LEFT JOIN employee_motivation_latest l
    ON l.team_id = t.team_id

GROUP BY
    t.team_id,
    t.team_name;

-- ============================================================
-- 11. WORKFLOW PROCEDURE
-- ============================================================

CREATE PROCEDURE update_goal_progress(
    p_goal_id BIGINT,
    p_progress NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_target NUMERIC;
BEGIN

    IF p_progress < 0 THEN
        RAISE EXCEPTION 'Progress cannot be negative';
    END IF;

    SELECT target_value
    INTO v_target
    FROM team_goals
    WHERE goal_id = p_goal_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Goal not found';
    END IF;

    IF p_progress > v_target THEN
        RAISE EXCEPTION
            'Progress cannot exceed target value';
    END IF;

    UPDATE team_goals
    SET current_progress = p_progress
    WHERE goal_id = p_goal_id;

END;
$$;

-- ============================================================
-- 12. SAMPLE ORGANIZATIONAL DATA
-- ============================================================

INSERT INTO organizations(organization_name)
VALUES
    ('Technology Solutions Group');

INSERT INTO teams(
    organization_id,
    team_name,
    department
)
VALUES
    (1, 'Product Engineering', 'Technology'),
    (1, 'Business Analytics', 'Analytics');

INSERT INTO employees(
    team_id,
    employee_name,
    job_role,
    email
)
VALUES
    (1, 'Ananya', 'Software Developer', 'ananya@example.com'),
    (2, 'Rahul', 'Business Analyst', 'rahul@example.com'),
    (1, 'Priya', 'Project Manager', 'priya@example.com'),
    (1, 'Vikram', 'Quality Analyst', 'vikram@example.com');

-- ============================================================
-- 13. SAMPLE MOTIVATION ASSESSMENTS
-- ============================================================

INSERT INTO motivation_assessments(
    employee_id,
    assessment_date,
    autonomy,
    competence,
    relatedness,
    workload,
    psychological_safety,
    engagement,
    intrinsic_motivation,
    extrinsic_motivation,
    comments
)
VALUES

(
    1,
    CURRENT_DATE,
    85, 90, 80, 55, 90, 88, 90, 65,
    'High engagement and strong development opportunities.'
),

(
    2,
    CURRENT_DATE,
    35, 55, 45, 90, 40, 38, 45, 70,
    'Workload concerns and limited autonomy.'
),

(
    3,
    CURRENT_DATE,
    75, 80, 85, 65, 85, 78, 80, 75,
    'Positive collaboration and team engagement.'
),

(
    4,
    CURRENT_DATE,
    45, 50, 55, 80, 45, 50, 55, 60,
    'Requires additional development support.'
);

-- ============================================================
-- 14. SAMPLE TEAM GOALS
-- ============================================================

INSERT INTO team_goals(
    team_id,
    owner_id,
    description,
    target_value,
    current_progress,
    due_date
)
VALUES
(
    1,
    1,
    'Complete quarterly product release',
    100,
    65,
    CURRENT_DATE + 30
),

(
    2,
    2,
    'Complete customer analytics dashboard',
    100,
    30,
    CURRENT_DATE + 45
);

-- ============================================================
-- 15. SAMPLE RECOGNITION
-- ============================================================

INSERT INTO recognitions(
    employee_id,
    recognition_category,
    reason,
    awarded_by
)
VALUES

(
    1,
    'PUBLIC',
    'Resolved a critical production issue.',
    3
),

(
    3,
    'DEVELOPMENT',
    'Successfully coordinated cross-functional delivery.',
    1
);

-- ============================================================
-- 16. SAMPLE INTERVENTIONS
-- ============================================================

INSERT INTO interventions(
    employee_id,
    intervention_name,
    intervention_description,
    intervention_status,
    assigned_to,
    planned_date
)
VALUES

(
    2,
    'Workload Review',
    'Review workload allocation and establish sustainable priorities.',
    'ACTIVE',
    3,
    CURRENT_DATE
),

(
    4,
    'Skill Development',
    'Provide mentoring and targeted technical training.',
    'PLANNED',
    1,
    CURRENT_DATE + 2
);

-- ============================================================
-- 17. RETRIEVAL QUERIES
-- ============================================================

-- Latest motivation information for each employee.

SELECT *
FROM employee_motivation_latest
ORDER BY motivation_score DESC;

-- ============================================================
-- 18. VALIDATION QUERIES
-- ============================================================

-- Identify employees with potential motivation problems.

SELECT
    employee_name,
    motivation_score,
    motivation_category,
    workload,
    autonomy,
    engagement

FROM employee_motivation_latest

WHERE motivation_category IN ('LOW', 'CRITICAL')
   OR workload >= 85

ORDER BY motivation_score ASC;

-- ============================================================
-- 19. TEAM AGGREGATION
-- ============================================================

SELECT *
FROM team_motivation_report
ORDER BY average_motivation DESC NULLS LAST;

-- ============================================================
-- 20. CTE-BASED TEAM ANALYSIS
-- ============================================================

WITH latest_scores AS (

    SELECT
        team_id,
        employee_id,
        employee_name,
        motivation_score,
        motivation_category,
        workload,

        RANK() OVER (
            PARTITION BY team_id
            ORDER BY motivation_score DESC
        ) AS motivation_rank

    FROM employee_motivation_latest

),

team_statistics AS (

    SELECT
        team_id,
        ROUND(AVG(motivation_score), 2) AS average_score,
        MAX(motivation_score) AS maximum_score,
        MIN(motivation_score) AS minimum_score,
        COUNT(*) AS employee_count

    FROM latest_scores

    GROUP BY team_id

)

SELECT
    ls.employee_name,
    ls.motivation_score,
    ls.motivation_category,
    ls.motivation_rank,
    ts.average_score,
    ts.employee_count

FROM latest_scores ls

JOIN team_statistics ts
    ON ts.team_id = ls.team_id

ORDER BY ls.team_id, ls.motivation_rank;

-- ============================================================
-- 21. INTERVENTION EVALUATION
-- ============================================================

SELECT
    e.employee_name,
    i.intervention_name,
    i.intervention_status,
    i.planned_date,
    i.completion_date

FROM interventions i

JOIN employees e
    ON e.employee_id = i.employee_id

ORDER BY i.planned_date;

-- ============================================================
-- 22. RECOGNITION REPORT
-- ============================================================

SELECT
    e.employee_name,
    COUNT(r.recognition_id) AS recognition_count

FROM employees e

LEFT JOIN recognitions r
    ON r.employee_id = e.employee_id

GROUP BY
    e.employee_id,
    e.employee_name

ORDER BY recognition_count DESC;

-- ============================================================
-- 23. GOAL ELIGIBILITY AND PROGRESS
-- ============================================================

SELECT
    g.goal_id,
    g.description,
    e.employee_name,
    g.target_value,
    g.current_progress,

    ROUND(
        g.current_progress / g.target_value * 100,
        2
    ) AS completion_percentage,

    g.status

FROM team_goals g

JOIN employees e
    ON e.employee_id = g.owner_id

ORDER BY completion_percentage DESC;

-- ============================================================
-- 24. INTERVENTION RECOMMENDATION REPORT
-- ============================================================

SELECT
    e.employee_name,
    recommendation,
    priority

FROM employees e

CROSS JOIN LATERAL
    recommend_interventions(e.employee_id)

WHERE e.active = TRUE

ORDER BY
    CASE priority
        WHEN 'HIGH' THEN 1
        WHEN 'MEDIUM' THEN 2
        ELSE 3
    END;

-- ============================================================
-- 25. MOTIVATION DIMENSION AGGREGATION
-- ============================================================

SELECT
    t.team_name,

    ROUND(AVG(a.autonomy), 2) AS average_autonomy,

    ROUND(AVG(a.competence), 2) AS average_competence,

    ROUND(AVG(a.relatedness), 2) AS average_relatedness,

    ROUND(AVG(a.psychological_safety), 2)
        AS average_psychological_safety,

    ROUND(AVG(a.engagement), 2) AS average_engagement,

    ROUND(AVG(a.workload), 2) AS average_workload

FROM teams t

JOIN employees e
    ON e.team_id = t.team_id

JOIN motivation_assessments a
    ON a.employee_id = e.employee_id

GROUP BY t.team_id, t.team_name;

-- ============================================================
-- 26. TRANSACTIONAL GOAL UPDATE
-- ============================================================

-- The row lock and transaction prevent concurrent progress
-- updates from silently overwriting one another.

DO $$
BEGIN

    BEGIN

        CALL update_goal_progress(1, 75);

        RAISE NOTICE
            'Goal progress updated successfully';

    EXCEPTION
        WHEN OTHERS THEN

            RAISE NOTICE
                'Goal update failed: %',
                SQLERRM;

    END;

END;
$$;

-- ============================================================
-- 27. DATABASE INTEGRITY CHECK
-- ============================================================

-- Check that calculated scores and classifications agree.

SELECT
    assessment_id,
    employee_id,
    motivation_score,
    calculate_motivation_score(
        autonomy,
        competence,
        relatedness,
        workload,
        psychological_safety,
        engagement,
        intrinsic_motivation
    ) AS recalculated_score,

    motivation_category

FROM motivation_assessments

WHERE motivation_score IS DISTINCT FROM
    calculate_motivation_score(
        autonomy,
        competence,
        relatedness,
        workload,
        psychological_safety,
        engagement,
        intrinsic_motivation
    );

COMMIT;
