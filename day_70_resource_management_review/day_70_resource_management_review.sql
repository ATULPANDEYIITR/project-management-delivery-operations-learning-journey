/*
===============================================================================
RESOURCE MANAGEMENT REVIEW
Enterprise Team Management and Resource Allocation Governance
===============================================================================

PostgreSQL: 15+

Domain workflow:
Departments
    |
    +--> Employees
    |       |
    |       +--> Skills
    |       +--> Leave Records
    |       +--> Resource Allocations
    |
    +--> Projects
            |
            +--> Required Skills
            +--> Allocations

Resource Allocations
    |
    +--> Capacity Evaluation
    +--> Utilization Analysis
    +--> Workload Fairness
    +--> Risk Assessment

Resource Review
    |
    +--> Review Findings
    +--> Corrective Actions
    +--> Review Decisions
    +--> Audit History

The script creates a dedicated schema and can be rerun.
Existing objects in this schema are dropped during initialization.
*/

BEGIN;

DROP SCHEMA IF EXISTS resource_management CASCADE;

CREATE SCHEMA resource_management;

SET search_path TO resource_management, public;


-- ============================================================================
-- 1. DOMAIN TYPES
-- ============================================================================

CREATE TYPE employee_status AS ENUM (
    'ACTIVE',
    'ON_LEAVE',
    'INACTIVE'
);

CREATE TYPE project_status AS ENUM (
    'PLANNING',
    'ACTIVE',
    'ON_HOLD',
    'COMPLETED'
);

CREATE TYPE allocation_status AS ENUM (
    'PROPOSED',
    'CONFIRMED',
    'CANCELLED'
);

CREATE TYPE review_status AS ENUM (
    'DRAFT',
    'UNDER_REVIEW',
    'APPROVED',
    'REJECTED'
);

CREATE TYPE risk_level AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);

CREATE TYPE action_status AS ENUM (
    'OPEN',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED'
);


-- ============================================================================
-- 2. ORGANIZATIONAL STRUCTURE
-- ============================================================================

CREATE TABLE departments (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    department_name VARCHAR(120) NOT NULL UNIQUE,

    department_head VARCHAR(120) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(department_name)) > 0)
);


CREATE TABLE employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    employee_code VARCHAR(30) NOT NULL UNIQUE,

    full_name VARCHAR(150) NOT NULL,

    department_id BIGINT NOT NULL
        REFERENCES departments(department_id),

    job_title VARCHAR(120) NOT NULL,

    weekly_capacity NUMERIC(6,2) NOT NULL DEFAULT 40,

    status employee_status NOT NULL DEFAULT 'ACTIVE',

    date_joined DATE NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(employee_code)) > 0),

    CHECK (length(trim(full_name)) > 0),

    CHECK (weekly_capacity > 0 AND weekly_capacity <= 168)
);


-- ============================================================================
-- 3. EMPLOYEE SKILLS AND COMPETENCIES
-- ============================================================================

CREATE TABLE skills (
    skill_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    skill_name VARCHAR(100) NOT NULL UNIQUE,

    skill_category VARCHAR(100) NOT NULL,

    CHECK (length(trim(skill_name)) > 0)
);


CREATE TABLE employee_skills (
    employee_id BIGINT NOT NULL
        REFERENCES employees(employee_id) ON DELETE CASCADE,

    skill_id BIGINT NOT NULL
        REFERENCES skills(skill_id),

    competency_level SMALLINT NOT NULL,

    assessed_on DATE NOT NULL DEFAULT CURRENT_DATE,

    PRIMARY KEY (employee_id, skill_id),

    CHECK (competency_level BETWEEN 1 AND 5)
);


-- ============================================================================
-- 4. PROJECT MANAGEMENT
-- ============================================================================

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_code VARCHAR(30) NOT NULL UNIQUE,

    project_name VARCHAR(180) NOT NULL,

    department_id BIGINT NOT NULL
        REFERENCES departments(department_id),

    project_manager_id BIGINT
        REFERENCES employees(employee_id),

    priority SMALLINT NOT NULL DEFAULT 3,

    status project_status NOT NULL DEFAULT 'PLANNING',

    planned_start DATE NOT NULL,

    planned_end DATE NOT NULL,

    estimated_budget NUMERIC(14,2) NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (priority BETWEEN 1 AND 5),

    CHECK (planned_start <= planned_end),

    CHECK (estimated_budget >= 0)
);


CREATE TABLE project_required_skills (
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id) ON DELETE CASCADE,

    skill_id BIGINT NOT NULL
        REFERENCES skills(skill_id),

    minimum_level SMALLINT NOT NULL,

    PRIMARY KEY (project_id, skill_id),

    CHECK (minimum_level BETWEEN 1 AND 5)
);


-- ============================================================================
-- 5. LEAVE AND AVAILABILITY
-- ============================================================================

CREATE TABLE employee_leave (
    leave_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    employee_id BIGINT NOT NULL
        REFERENCES employees(employee_id),

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    weekly_unavailable_hours NUMERIC(6,2) NOT NULL,

    leave_reason VARCHAR(180) NOT NULL,

    approved BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (start_date <= end_date),

    CHECK (weekly_unavailable_hours >= 0)
);


-- ============================================================================
-- 6. RESOURCE ALLOCATIONS
-- ============================================================================

CREATE TABLE resource_allocations (
    allocation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    employee_id BIGINT NOT NULL
        REFERENCES employees(employee_id),

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    weekly_hours NUMERIC(6,2) NOT NULL,

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    allocation_status allocation_status NOT NULL DEFAULT 'PROPOSED',

    allocation_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (weekly_hours > 0 AND weekly_hours <= 168),

    CHECK (start_date <= end_date)
);


CREATE INDEX idx_allocations_employee_period
ON resource_allocations (
    employee_id,
    start_date,
    end_date
)
WHERE allocation_status = 'CONFIRMED';


CREATE INDEX idx_allocations_project_status
ON resource_allocations (
    project_id,
    allocation_status
);


CREATE INDEX idx_employee_department_status
ON employees (
    department_id,
    status
);


CREATE INDEX idx_employee_skills_skill
ON employee_skills (
    skill_id,
    competency_level
);


CREATE INDEX idx_leave_employee_period
ON employee_leave (
    employee_id,
    start_date,
    end_date
)
WHERE approved = TRUE;


-- ============================================================================
-- 7. RESOURCE REVIEW MANAGEMENT
-- ============================================================================

CREATE TABLE resource_reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    review_code VARCHAR(40) NOT NULL UNIQUE,

    reviewer_name VARCHAR(150) NOT NULL,

    review_period_start DATE NOT NULL,

    review_period_end DATE NOT NULL,

    status review_status NOT NULL DEFAULT 'DRAFT',

    decision_maker VARCHAR(150),

    decision_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    decided_at TIMESTAMPTZ,

    CHECK (review_period_start <= review_period_end),

    CHECK (length(trim(review_code)) > 0)
);


CREATE TABLE review_findings (
    finding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    review_id BIGINT NOT NULL
        REFERENCES resource_reviews(review_id) ON DELETE CASCADE,

    employee_id BIGINT
        REFERENCES employees(employee_id),

    project_id BIGINT
        REFERENCES projects(project_id),

    finding_type VARCHAR(80) NOT NULL,

    severity risk_level NOT NULL,

    finding_description TEXT NOT NULL,

    identified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    resolved BOOLEAN NOT NULL DEFAULT FALSE,

    CHECK (length(trim(finding_type)) > 0),

    CHECK (length(trim(finding_description)) > 0)
);


CREATE TABLE review_actions (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    review_id BIGINT NOT NULL
        REFERENCES resource_reviews(review_id),

    owner_id BIGINT NOT NULL
        REFERENCES employees(employee_id),

    description TEXT NOT NULL,

    due_date DATE NOT NULL,

    status action_status NOT NULL DEFAULT 'OPEN',

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(description)) > 0),

    CHECK (
        (status = 'COMPLETED' AND completed_at IS NOT NULL)
        OR
        (status <> 'COMPLETED' AND completed_at IS NULL)
    )
);


-- ============================================================================
-- 8. REVIEW POLICY
-- ============================================================================

CREATE TABLE review_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(120) NOT NULL UNIQUE,

    high_utilization_threshold NUMERIC(5,2) NOT NULL DEFAULT 85,

    critical_utilization_threshold NUMERIC(5,2) NOT NULL DEFAULT 95,

    underutilization_threshold NUMERIC(5,2) NOT NULL DEFAULT 40,

    block_critical_approval BOOLEAN NOT NULL DEFAULT TRUE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        underutilization_threshold >= 0
        AND underutilization_threshold < high_utilization_threshold
    ),

    CHECK (
        high_utilization_threshold > 0
        AND critical_utilization_threshold <= 100
        AND critical_utilization_threshold > high_utilization_threshold
    )
);


-- ============================================================================
-- 9. AUDIT LOG
-- ============================================================================

CREATE TABLE resource_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    event_type VARCHAR(100) NOT NULL,

    entity_type VARCHAR(100) NOT NULL,

    entity_id BIGINT,

    event_description TEXT NOT NULL,

    performed_by VARCHAR(150) NOT NULL DEFAULT CURRENT_USER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_audit_entity
ON resource_audit_log (
    entity_type,
    entity_id,
    created_at DESC
);


-- ============================================================================
-- 10. AUDIT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION log_allocation_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF TG_OP = 'INSERT' THEN

        INSERT INTO resource_audit_log (
            event_type,
            entity_type,
            entity_id,
            event_description
        )
        VALUES (
            'ALLOCATION_CREATED',
            'RESOURCE_ALLOCATION',
            NEW.allocation_id,
            format(
                'Employee %s allocated %.2f hours to project %s',
                NEW.employee_id,
                NEW.weekly_hours,
                NEW.project_id
            )
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN

        INSERT INTO resource_audit_log (
            event_type,
            entity_type,
            entity_id,
            event_description
        )
        VALUES (
            'ALLOCATION_UPDATED',
            'RESOURCE_ALLOCATION',
            NEW.allocation_id,
            format(
                'Allocation status changed from %s to %s',
                OLD.allocation_status,
                NEW.allocation_status
            )
        );

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN

        INSERT INTO resource_audit_log (
            event_type,
            entity_type,
            entity_id,
            event_description
        )
        VALUES (
            'ALLOCATION_DELETED',
            'RESOURCE_ALLOCATION',
            OLD.allocation_id,
            'Resource allocation removed.'
        );

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;


CREATE TRIGGER trg_allocation_audit
AFTER INSERT OR UPDATE OR DELETE
ON resource_allocations
FOR EACH ROW
EXECUTE FUNCTION log_allocation_change();


-- ============================================================================
-- 11. CAPACITY VALIDATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION get_available_capacity(
    p_employee_id BIGINT,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS NUMERIC(8,2)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE

    v_capacity NUMERIC(8,2);

    v_unavailable NUMERIC(8,2);

    v_allocated NUMERIC(8,2);

BEGIN

    IF p_start_date > p_end_date THEN
        RAISE EXCEPTION 'Invalid capacity date range.';
    END IF;

    SELECT weekly_capacity
    INTO v_capacity
    FROM employees
    WHERE employee_id = p_employee_id
      AND status = 'ACTIVE';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Employee % does not exist or is inactive.',
            p_employee_id;
    END IF;

    SELECT COALESCE(
        SUM(weekly_unavailable_hours),
        0
    )
    INTO v_unavailable
    FROM employee_leave
    WHERE employee_id = p_employee_id
      AND approved = TRUE
      AND start_date <= p_end_date
      AND end_date >= p_start_date;

    v_unavailable := LEAST(
        v_unavailable,
        v_capacity
    );

    SELECT COALESCE(
        SUM(weekly_hours),
        0
    )
    INTO v_allocated
    FROM resource_allocations
    WHERE employee_id = p_employee_id
      AND allocation_status = 'CONFIRMED'
      AND start_date <= p_end_date
      AND end_date >= p_start_date;

    RETURN GREATEST(
        0,
        v_capacity - v_unavailable - v_allocated
    );

END;
$$;


-- ============================================================================
-- 12. ALLOCATION INTEGRITY TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_resource_allocation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE

    v_capacity NUMERIC(8,2);

    v_allocated NUMERIC(8,2);

    v_unavailable NUMERIC(8,2);

    v_employee_status employee_status;

    v_project_status project_status;

BEGIN

    IF NEW.allocation_status <> 'CONFIRMED' THEN
        RETURN NEW;
    END IF;

    -- Lock the employee row to serialize allocation
    -- decisions for the same employee.
    SELECT weekly_capacity, status
    INTO v_capacity, v_employee_status
    FROM employees
    WHERE employee_id = NEW.employee_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Employee does not exist.';
    END IF;

    IF v_employee_status <> 'ACTIVE' THEN
        RAISE EXCEPTION 'Employee is not active.';
    END IF;

    SELECT status
    INTO v_project_status
    FROM projects
    WHERE project_id = NEW.project_id;

    IF NOT FOUND OR v_project_status <> 'ACTIVE' THEN
        RAISE EXCEPTION 'Project is not active.';
    END IF;

    SELECT COALESCE(
        SUM(weekly_unavailable_hours),
        0
    )
    INTO v_unavailable
    FROM employee_leave
    WHERE employee_id = NEW.employee_id
      AND approved = TRUE
      AND start_date <= NEW.end_date
      AND end_date >= NEW.start_date;

    v_unavailable := LEAST(
        v_unavailable,
        v_capacity
    );

    SELECT COALESCE(
        SUM(weekly_hours),
        0
    )
    INTO v_allocated
    FROM resource_allocations
    WHERE employee_id = NEW.employee_id
      AND allocation_status = 'CONFIRMED'
      AND start_date <= NEW.end_date
      AND end_date >= NEW.start_date
      AND (
          TG_OP = 'INSERT'
          OR allocation_id <> NEW.allocation_id
      );

    IF (
        v_allocated + NEW.weekly_hours >
        v_capacity - v_unavailable
    ) THEN

        RAISE EXCEPTION
            'Capacity exceeded for employee %. Available: %, Requested: %',
            NEW.employee_id,
            v_capacity - v_unavailable - v_allocated,
            NEW.weekly_hours;

    END IF;

    RETURN NEW;

END;
$$;


CREATE TRIGGER trg_validate_resource_allocation
BEFORE INSERT OR UPDATE
ON resource_allocations
FOR EACH ROW
EXECUTE FUNCTION validate_resource_allocation();


-- ============================================================================
-- 13. REVIEW DECISION VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_review_decision()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE

    v_critical_count BIGINT;

    v_block_critical BOOLEAN;

BEGIN

    IF OLD.status IN ('APPROVED', 'REJECTED') THEN

        RAISE EXCEPTION
            'Finalized review decisions cannot be changed.';

    END IF;

    IF NEW.status IN ('APPROVED', 'REJECTED') THEN

        IF NEW.decision_maker IS NULL
           OR length(trim(NEW.decision_maker)) = 0 THEN

            RAISE EXCEPTION
                'Decision maker is required.';

        END IF;

        IF NEW.decision_notes IS NULL
           OR length(trim(NEW.decision_notes)) = 0 THEN

            RAISE EXCEPTION
                'Decision notes are required.';

        END IF;

        SELECT block_critical_approval
        INTO v_block_critical
        FROM review_policies
        WHERE active = TRUE
        ORDER BY policy_id DESC
        LIMIT 1;

        SELECT COUNT(*)
        INTO v_critical_count
        FROM review_findings
        WHERE review_id = NEW.review_id
          AND severity = 'CRITICAL'
          AND resolved = FALSE;

        IF NEW.status = 'APPROVED'
           AND COALESCE(v_block_critical, TRUE)
           AND v_critical_count > 0 THEN

            RAISE EXCEPTION
                'Unresolved critical findings prevent approval.';

        END IF;

        NEW.decided_at := CURRENT_TIMESTAMP;

    END IF;

    RETURN NEW;

END;
$$;


CREATE TRIGGER trg_validate_review_decision
BEFORE UPDATE OF status
ON resource_reviews
FOR EACH ROW
EXECUTE FUNCTION validate_review_decision();


-- ============================================================================
-- 14. CAPACITY REPORT VIEW
-- ============================================================================

CREATE OR REPLACE VIEW employee_capacity_report AS

WITH approved_leave AS (

    SELECT
        employee_id,

        LEAST(
            SUM(weekly_unavailable_hours),
            MAX(weekly_capacity)
        ) AS unavailable_hours

    FROM employee_leave

    JOIN employees USING (employee_id)

    WHERE approved = TRUE

    GROUP BY employee_id

),

confirmed_allocations AS (

    SELECT
        employee_id,

        SUM(weekly_hours) AS allocated_hours

    FROM resource_allocations

    WHERE allocation_status = 'CONFIRMED'

      AND CURRENT_DATE BETWEEN start_date AND end_date

    GROUP BY employee_id

)

SELECT

    e.employee_id,

    e.employee_code,

    e.full_name,

    d.department_name,

    e.weekly_capacity,

    CASE
        WHEN e.status = 'ACTIVE'
        THEN GREATEST(
            0,
            e.weekly_capacity -
            COALESCE(l.unavailable_hours, 0)
        )
        ELSE 0
    END AS effective_capacity,

    COALESCE(a.allocated_hours, 0) AS allocated_hours,

    GREATEST(
        0,
        CASE
            WHEN e.status = 'ACTIVE'
            THEN e.weekly_capacity -
                 COALESCE(l.unavailable_hours, 0)
            ELSE 0
        END -
        COALESCE(a.allocated_hours, 0)
    ) AS available_hours,

    CASE
        WHEN e.status <> 'ACTIVE' THEN 0

        WHEN e.weekly_capacity -
             COALESCE(l.unavailable_hours, 0) <= 0
        THEN 0

        ELSE ROUND(
            COALESCE(a.allocated_hours, 0) * 100 /
            (
                e.weekly_capacity -
                COALESCE(l.unavailable_hours, 0)
            ),
            2
        )
    END AS utilization_percentage

FROM employees e

JOIN departments d
    ON d.department_id = e.department_id

LEFT JOIN approved_leave l
    ON l.employee_id = e.employee_id

LEFT JOIN confirmed_allocations a
    ON a.employee_id = e.employee_id;


-- ============================================================================
-- 15. RESOURCE RISK VIEW
-- ============================================================================

CREATE OR REPLACE VIEW employee_resource_risks AS

SELECT

    employee_id,

    employee_code,

    full_name,

    department_name,

    utilization_percentage,

    CASE

        WHEN utilization_percentage > 100
        THEN 'CRITICAL'::risk_level

        WHEN utilization_percentage >= 95
        THEN 'HIGH'::risk_level

        WHEN utilization_percentage >= 85
        THEN 'MEDIUM'::risk_level

        WHEN utilization_percentage < 40
        THEN 'MEDIUM'::risk_level

        ELSE 'LOW'::risk_level

    END AS risk_level,

    CASE

        WHEN utilization_percentage > 100
        THEN 'Workload exceeds effective capacity.'

        WHEN utilization_percentage >= 95
        THEN 'Insufficient capacity buffer.'

        WHEN utilization_percentage >= 85
        THEN 'High workload concentration.'

        WHEN utilization_percentage < 40
        THEN 'Potential resource underutilization.'

        ELSE 'Utilization within expected range.'

    END AS risk_reason

FROM employee_capacity_report;


-- ============================================================================
-- 16. PROJECT SKILL MATCHING VIEW
-- ============================================================================

CREATE OR REPLACE VIEW project_skill_match_report AS

SELECT

    p.project_id,

    p.project_code,

    p.project_name,

    e.employee_id,

    e.employee_code,

    e.full_name,

    COUNT(prs.skill_id) AS total_required_skills,

    COUNT(*) FILTER (
        WHERE COALESCE(es.competency_level, 0) >= prs.minimum_level
    ) AS matched_skills,

    COUNT(*) FILTER (
        WHERE COALESCE(es.competency_level, 0) < prs.minimum_level
    ) AS missing_skills,

    CASE

        WHEN COUNT(prs.skill_id) = 0 THEN 100

        ELSE ROUND(
            COUNT(*) FILTER (
                WHERE COALESCE(es.competency_level, 0)
                      >= prs.minimum_level
            ) * 100.0 /
            COUNT(prs.skill_id),
            2
        )

    END AS match_percentage

FROM projects p

CROSS JOIN employees e

LEFT JOIN project_required_skills prs
    ON prs.project_id = p.project_id

LEFT JOIN employee_skills es
    ON es.employee_id = e.employee_id
   AND es.skill_id = prs.skill_id

WHERE e.status = 'ACTIVE'

GROUP BY
    p.project_id,
    p.project_code,
    p.project_name,
    e.employee_id,
    e.employee_code,
    e.full_name;


-- ============================================================================
-- 17. WORKLOAD FAIRNESS VIEW
-- ============================================================================

CREATE OR REPLACE VIEW department_workload_fairness AS

SELECT

    department_name,

    COUNT(*) AS active_employee_count,

    ROUND(
        AVG(utilization_percentage),
        2
    ) AS average_utilization,

    ROUND(
        STDDEV_POP(utilization_percentage),
        2
    ) AS utilization_standard_deviation,

    MIN(utilization_percentage) AS minimum_utilization,

    MAX(utilization_percentage) AS maximum_utilization

FROM employee_capacity_report

GROUP BY department_name;


-- ============================================================================
-- 18. RESOURCE REVIEW PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE generate_resource_review(
    p_review_code VARCHAR(40),
    p_reviewer VARCHAR(150),
    p_start DATE,
    p_end DATE
)
LANGUAGE plpgsql
AS $$
DECLARE

    v_review_id BIGINT;

    v_risk RECORD;

BEGIN

    IF p_start > p_end THEN
        RAISE EXCEPTION 'Invalid review period.';
    END IF;

    INSERT INTO resource_reviews (
        review_code,
        reviewer_name,
        review_period_start,
        review_period_end,
        status
    )
    VALUES (
        p_review_code,
        p_reviewer,
        p_start,
        p_end,
        'UNDER_REVIEW'
    )
    RETURNING review_id INTO v_review_id;

    FOR v_risk IN

        SELECT *
        FROM employee_resource_risks

        WHERE risk_level IN ('HIGH', 'CRITICAL')

    LOOP

        INSERT INTO review_findings (
            review_id,
            employee_id,
            finding_type,
            severity,
            finding_description
        )
        VALUES (
            v_review_id,
            v_risk.employee_id,
            'RESOURCE_CAPACITY_RISK',
            v_risk.risk_level,
            v_risk.risk_reason
        );

    END LOOP;

    INSERT INTO resource_audit_log (
        event_type,
        entity_type,
        entity_id,
        event_description
    )
    VALUES (
        'REVIEW_CREATED',
        'RESOURCE_REVIEW',
        v_review_id,
        format(
            'Resource review %s created.',
            p_review_code
        )
    );

END;
$$;


-- ============================================================================
-- 19. REVIEW ELIGIBILITY FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION is_review_eligible(
    p_review_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE

    v_status review_status;

    v_critical_count BIGINT;

    v_block_critical BOOLEAN;

BEGIN

    SELECT status
    INTO v_status
    FROM resource_reviews
    WHERE review_id = p_review_id;

    IF NOT FOUND OR v_status <> 'UNDER_REVIEW' THEN
        RETURN FALSE;
    END IF;

    SELECT block_critical_approval
    INTO v_block_critical
    FROM review_policies
    WHERE active = TRUE
    ORDER BY policy_id DESC
    LIMIT 1;

    SELECT COUNT(*)
    INTO v_critical_count
    FROM review_findings
    WHERE review_id = p_review_id
      AND severity = 'CRITICAL'
      AND resolved = FALSE;

    RETURN NOT (
        COALESCE(v_block_critical, TRUE)
        AND v_critical_count > 0
    );

END;
$$;


-- ============================================================================
-- 20. SAMPLE DEPARTMENTS
-- ============================================================================

INSERT INTO departments (
    department_name,
    department_head
)
VALUES
    ('Engineering', 'Engineering Director'),
    ('Analytics', 'Analytics Director'),
    ('Operations', 'Operations Director');


-- ============================================================================
-- 21. SAMPLE EMPLOYEES
-- ============================================================================

INSERT INTO employees (
    employee_code,
    full_name,
    department_id,
    job_title,
    weekly_capacity,
    status,
    date_joined
)
VALUES
(
    'E101',
    'Aarav Sharma',
    (SELECT department_id FROM departments
     WHERE department_name = 'Engineering'),
    'Senior Developer',
    40,
    'ACTIVE',
    '2023-01-10'
),
(
    'E102',
    'Meera Singh',
    (SELECT department_id FROM departments
     WHERE department_name = 'Engineering'),
    'Backend Developer',
    40,
    'ACTIVE',
    '2023-06-15'
),
(
    'E103',
    'Rohan Verma',
    (SELECT department_id FROM departments
     WHERE department_name = 'Analytics'),
    'Data Analyst',
    40,
    'ACTIVE',
    '2024-02-01'
),
(
    'E104',
    'Ananya Gupta',
    (SELECT department_id FROM departments
     WHERE department_name = 'Engineering'),
    'Cloud Engineer',
    40,
    'ACTIVE',
    '2022-11-20'
);


-- ============================================================================
-- 22. SAMPLE SKILLS
-- ============================================================================

INSERT INTO skills (
    skill_name,
    skill_category
)
VALUES
    ('Python', 'Programming'),
    ('SQL', 'Database'),
    ('Cloud', 'Infrastructure'),
    ('Analytics', 'Data'),
    ('Security', 'Cybersecurity');


-- ============================================================================
-- 23. SAMPLE EMPLOYEE COMPETENCIES
-- ============================================================================

INSERT INTO employee_skills (
    employee_id,
    skill_id,
    competency_level
)
SELECT
    e.employee_id,
    s.skill_id,
    v.level

FROM (
    VALUES
        ('E101', 'Python', 5),
        ('E101', 'SQL', 4),
        ('E101', 'Cloud', 4),

        ('E102', 'Python', 4),
        ('E102', 'SQL', 5),
        ('E102', 'Cloud', 3),

        ('E103', 'Python', 3),
        ('E103', 'SQL', 4),
        ('E103', 'Analytics', 5),

        ('E104', 'Python', 3),
        ('E104', 'Cloud', 5),
        ('E104', 'Security', 4)
) AS v(employee_code, skill_name, level)

JOIN employees e
    ON e.employee_code = v.employee_code

JOIN skills s
    ON s.skill_name = v.skill_name;


-- ============================================================================
-- 24. SAMPLE PROJECT
-- ============================================================================

INSERT INTO projects (
    project_code,
    project_name,
    department_id,
    project_manager_id,
    priority,
    status,
    planned_start,
    planned_end,
    estimated_budget
)
VALUES (
    'P101',
    'Enterprise Platform Modernization',
    (
        SELECT department_id
        FROM departments
        WHERE department_name = 'Engineering'
    ),
    (
        SELECT employee_id
        FROM employees
        WHERE employee_code = 'E101'
    ),
    5,
    'ACTIVE',
    '2026-11-01',
    '2026-12-31',
    2500000
);


INSERT INTO project_required_skills (
    project_id,
    skill_id,
    minimum_level
)
SELECT
    p.project_id,
    s.skill_id,
    v.minimum_level

FROM (
    VALUES
        ('Python', 4),
        ('SQL', 4),
        ('Cloud', 4)
) AS v(skill_name, minimum_level)

JOIN projects p
    ON p.project_code = 'P101'

JOIN skills s
    ON s.skill_name = v.skill_name;


-- ============================================================================
-- 25. LEAVE RECORD
-- ============================================================================

INSERT INTO employee_leave (
    employee_id,
    start_date,
    end_date,
    weekly_unavailable_hours,
    leave_reason,
    approved
)
VALUES (
    (SELECT employee_id FROM employees
     WHERE employee_code = 'E102'),
    '2026-11-10',
    '2026-11-14',
    8,
    'Approved planned leave',
    TRUE
);


-- ============================================================================
-- 26. REVIEW POLICY CONFIGURATION
-- ============================================================================

INSERT INTO review_policies (
    policy_name,
    high_utilization_threshold,
    critical_utilization_threshold,
    underutilization_threshold,
    block_critical_approval,
    active
)
VALUES (
    'Standard Team Capacity Policy',
    85,
    95,
    40,
    TRUE,
    TRUE
);


-- ============================================================================
-- 27. VALID RESOURCE ALLOCATIONS
-- ============================================================================

INSERT INTO resource_allocations (
    employee_id,
    project_id,
    weekly_hours,
    start_date,
    end_date,
    allocation_status,
    allocation_notes
)
VALUES
(
    (SELECT employee_id FROM employees
     WHERE employee_code = 'E101'),
    (SELECT project_id FROM projects
     WHERE project_code = 'P101'),
    35,
    '2026-11-01',
    '2026-11-30',
    'CONFIRMED',
    'Technical architecture and development'
),
(
    (SELECT employee_id FROM employees
     WHERE employee_code = 'E102'),
    (SELECT project_id FROM projects
     WHERE project_code = 'P101'),
    25,
    '2026-11-01',
    '2026-11-30',
    'CONFIRMED',
    'Backend development'
),
(
    (SELECT employee_id FROM employees
     WHERE employee_code = 'E103'),
    (SELECT project_id FROM projects
     WHERE project_code = 'P101'),
    20,
    '2026-11-01',
    '2026-11-30',
    'CONFIRMED',
    'Data analysis'
),
(
    (SELECT employee_id FROM employees
     WHERE employee_code = 'E104'),
    (SELECT project_id FROM projects
     WHERE project_code = 'P101'),
    30,
    '2026-11-01',
    '2026-11-30',
    'CONFIRMED',
    'Cloud infrastructure'
);


-- ============================================================================
-- 28. REVIEW GENERATION
-- ============================================================================

CALL generate_resource_review(
    'RR-2026-001',
    'Resource Management Lead',
    '2026-11-01',
    '2026-11-30'
);


-- ============================================================================
-- 29. CORRECTIVE ACTIONS
-- ============================================================================

INSERT INTO review_actions (
    review_id,
    owner_id,
    description,
    due_date,
    status
)
SELECT
    r.review_id,
    e.employee_id,
    'Review workload and confirm capacity assumptions.',
    '2026-12-05',
    'OPEN'

FROM resource_reviews r

CROSS JOIN employees e

WHERE r.review_code = 'RR-2026-001';


-- ============================================================================
-- 30. RESOURCE RETRIEVAL
-- ============================================================================

SELECT
    employee_code,
    full_name,
    department_name,
    weekly_capacity,
    effective_capacity,
    allocated_hours,
    available_hours,
    utilization_percentage

FROM employee_capacity_report

ORDER BY utilization_percentage DESC;


-- ============================================================================
-- 31. RESOURCE RISK RETRIEVAL
-- ============================================================================

SELECT
    employee_code,
    full_name,
    utilization_percentage,
    risk_level,
    risk_reason

FROM employee_resource_risks

ORDER BY
    CASE risk_level
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        ELSE 4
    END,
    utilization_percentage DESC;


-- ============================================================================
-- 32. DEPARTMENT WORKLOAD FAIRNESS
-- ============================================================================

SELECT *
FROM department_workload_fairness
ORDER BY average_utilization DESC;


-- ============================================================================
-- 33. PROJECT SKILL MATCHING
-- ============================================================================

SELECT
    project_code,
    employee_code,
    full_name,
    total_required_skills,
    matched_skills,
    missing_skills,
    match_percentage

FROM project_skill_match_report

WHERE project_code = 'P101'

ORDER BY match_percentage DESC;


-- ============================================================================
-- 34. PROJECT RESOURCE DISTRIBUTION
-- ============================================================================

SELECT
    p.project_code,
    p.project_name,
    COUNT(DISTINCT a.employee_id) AS allocated_employees,
    SUM(a.weekly_hours) AS total_weekly_hours,
    AVG(a.weekly_hours) AS average_weekly_hours

FROM projects p

LEFT JOIN resource_allocations a
    ON a.project_id = p.project_id
   AND a.allocation_status = 'CONFIRMED'

GROUP BY
    p.project_id,
    p.project_code,
    p.project_name;


-- ============================================================================
-- 35. RESOURCE REVIEW FINDINGS
-- ============================================================================

SELECT
    r.review_code,
    r.reviewer_name,
    r.status,
    f.finding_type,
    f.severity,
    e.full_name,
    f.finding_description,
    f.resolved

FROM resource_reviews r

JOIN review_findings f
    ON f.review_id = r.review_id

LEFT JOIN employees e
    ON e.employee_id = f.employee_id

ORDER BY
    r.review_id,
    f.finding_id;


-- ============================================================================
-- 36. CORRECTIVE ACTION REPORT
-- ============================================================================

SELECT
    r.review_code,
    a.description,
    e.full_name AS action_owner,
    a.due_date,
    a.status,
    a.completed_at

FROM review_actions a

JOIN resource_reviews r
    ON r.review_id = a.review_id

JOIN employees e
    ON e.employee_id = a.owner_id

ORDER BY a.due_date;


-- ============================================================================
-- 37. REVIEW ELIGIBILITY
-- ============================================================================

SELECT
    review_code,
    status,
    is_review_eligible(review_id) AS eligible_for_approval

FROM resource_reviews;


-- ============================================================================
-- 38. REVIEW APPROVAL TRANSACTION
-- ============================================================================

BEGIN;

UPDATE resource_reviews

SET
    status = CASE

        WHEN is_review_eligible(review_id)
        THEN 'APPROVED'::review_status

        ELSE 'REJECTED'::review_status

    END,

    decision_maker = 'Department Head',

    decision_notes = CASE

        WHEN is_review_eligible(review_id)
        THEN 'Resource review passed approval eligibility.'

        ELSE 'Resource findings require corrective action.'

    END

WHERE review_code = 'RR-2026-001'
  AND status = 'UNDER_REVIEW';

COMMIT;


-- ============================================================================
-- 39. FINAL REVIEW REPORT
-- ============================================================================

SELECT
    r.review_code,
    r.reviewer_name,
    r.review_period_start,
    r.review_period_end,
    r.status,
    r.decision_maker,
    r.decision_notes,
    r.created_at,
    r.decided_at,

    COUNT(DISTINCT f.finding_id) AS total_findings,

    COUNT(DISTINCT a.action_id) AS total_actions,

    COUNT(DISTINCT a.action_id) FILTER (
        WHERE a.status = 'COMPLETED'
    ) AS completed_actions,

    COUNT(DISTINCT f.finding_id) FILTER (
        WHERE f.severity = 'CRITICAL'
          AND f.resolved = FALSE
    ) AS unresolved_critical_findings

FROM resource_reviews r

LEFT JOIN review_findings f
    ON f.review_id = r.review_id

LEFT JOIN review_actions a
    ON a.review_id = r.review_id

GROUP BY r.review_id

ORDER BY r.created_at DESC;


-- ============================================================================
-- 40. AUDIT REPORT
-- ============================================================================

SELECT
    audit_id,
    event_type,
    entity_type,
    entity_id,
    event_description,
    performed_by,
    created_at

FROM resource_audit_log

ORDER BY created_at DESC, audit_id DESC;


-- ============================================================================
-- 41. VALIDATION TEST: OVERALLOCATION
-- ============================================================================

DO $$
DECLARE

    v_employee_id BIGINT;

    v_project_id BIGINT;

BEGIN

    SELECT employee_id
    INTO v_employee_id
    FROM employees
    WHERE employee_code = 'E103';

    SELECT project_id
    INTO v_project_id
    FROM projects
    WHERE project_code = 'P101';

    BEGIN

        INSERT INTO resource_allocations (
            employee_id,
            project_id,
            weekly_hours,
            start_date,
            end_date,
            allocation_status
        )
        VALUES (
            v_employee_id,
            v_project_id,
            50,
            '2026-11-01',
            '2026-11-30',
            'CONFIRMED'
        );

        RAISE EXCEPTION
            'Expected over-allocation validation to fail.';

    EXCEPTION

        WHEN raise_exception THEN

            IF SQLERRM LIKE 'Expected over-allocation%' THEN
                RAISE;
            END IF;

            RAISE NOTICE
                'OVERALLOCATION VALIDATION PASSED: %',
                SQLERRM;

    END;

END;
$$;


-- ============================================================================
-- 42. TRANSACTIONAL ROLLBACK DEMONSTRATION
-- ============================================================================

BEGIN;

INSERT INTO resource_allocations (
    employee_id,
    project_id,
    weekly_hours,
    start_date,
    end_date,
    allocation_status,
    allocation_notes
)
VALUES (
    (SELECT employee_id FROM employees
     WHERE employee_code = 'E103'),
    (SELECT project_id FROM projects
     WHERE project_code = 'P101'),
    5,
    '2027-01-01',
    '2027-01-31',
    'PROPOSED',
    'Temporary proposed allocation for rollback demonstration'
);

ROLLBACK;


-- ============================================================================
-- 43. REVIEW ACTION STATUS VALIDATION
-- ============================================================================

DO $$
DECLARE

    v_action_id BIGINT;

BEGIN

    SELECT action_id
    INTO v_action_id
    FROM review_actions
    ORDER BY action_id
    LIMIT 1;

    IF v_action_id IS NOT NULL THEN

        UPDATE review_actions

        SET
            status = 'IN_PROGRESS',
            completed_at = NULL

        WHERE action_id = v_action_id;

        RAISE NOTICE
            'REVIEW ACTION STATUS UPDATED: %',
            v_action_id;

    END IF;

END;
$$;


-- ============================================================================
-- 44. DATABASE STATISTICS
-- ============================================================================

SELECT
    (SELECT COUNT(*) FROM employees) AS total_employees,

    (SELECT COUNT(*) FROM projects) AS total_projects,

    (SELECT COUNT(*) FROM resource_allocations
     WHERE allocation_status = 'CONFIRMED')
        AS confirmed_allocations,

    (SELECT COUNT(*) FROM resource_reviews)
        AS total_reviews,

    (SELECT COUNT(*) FROM review_findings)
        AS total_findings,

    (SELECT COUNT(*) FROM review_actions)
        AS total_actions;


COMMIT;


-- ============================================================================
-- END OF RESOURCE MANAGEMENT REVIEW DATABASE
-- ============================================================================
