DROP SCHEMA IF EXISTS resource_planning CASCADE;
CREATE SCHEMA resource_planning;
SET search_path TO resource_planning;

-- Resource planning needs separate entities for resources, project work,
-- allocations, schedules, and cost controls. Keeping them separate allows
-- database constraints to prevent invalid resource assignments.

CREATE TYPE resource_type AS ENUM (
    'person',
    'equipment',
    'software'
);

CREATE TYPE task_state AS ENUM (
    'planned',
    'active',
    'blocked',
    'completed'
);

CREATE TYPE allocation_state AS ENUM (
    'planned',
    'active',
    'released'
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    budget NUMERIC(14,2) NOT NULL CHECK (budget > 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    CHECK (start_date <= end_date)
);

CREATE TABLE resources (
    resource_id BIGSERIAL PRIMARY KEY,
    resource_code VARCHAR(40) NOT NULL UNIQUE,
    resource_name VARCHAR(160) NOT NULL,
    resource_type resource_type NOT NULL,
    weekly_capacity_hours NUMERIC(8,2) NOT NULL
        CHECK (weekly_capacity_hours > 0),
    hourly_cost NUMERIC(10,2) NOT NULL
        CHECK (hourly_cost >= 0),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE resource_skills (
    resource_id BIGINT NOT NULL
        REFERENCES resources(resource_id)
        ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL,
    skill_level SMALLINT NOT NULL
        CHECK (skill_level BETWEEN 1 AND 4),
    PRIMARY KEY (resource_id, skill_name)
);

CREATE TABLE tasks (
    task_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    task_code VARCHAR(40) NOT NULL,
    task_name VARCHAR(200) NOT NULL,
    state task_state NOT NULL DEFAULT 'planned',
    estimated_hours NUMERIC(10,2) NOT NULL
        CHECK (estimated_hours > 0),
    priority SMALLINT NOT NULL
        CHECK (priority > 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    UNIQUE (project_id, task_code),
    CHECK (start_date <= end_date)
);

CREATE TABLE task_required_skills (
    task_id BIGINT NOT NULL
        REFERENCES tasks(task_id)
        ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL,
    minimum_skill_level SMALLINT NOT NULL
        CHECK (minimum_skill_level BETWEEN 1 AND 4),
    PRIMARY KEY (task_id, skill_name)
);

CREATE TABLE allocations (
    allocation_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL
        REFERENCES tasks(task_id)
        ON DELETE CASCADE,
    resource_id BIGINT NOT NULL
        REFERENCES resources(resource_id),
    allocation_start DATE NOT NULL,
    allocation_end DATE NOT NULL,
    allocated_hours NUMERIC(10,2) NOT NULL
        CHECK (allocated_hours > 0),
    state allocation_state NOT NULL DEFAULT 'planned',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (allocation_start <= allocation_end)
);

CREATE TABLE resource_absences (
    absence_id BIGSERIAL PRIMARY KEY,
    resource_id BIGINT NOT NULL
        REFERENCES resources(resource_id)
        ON DELETE CASCADE,
    absence_start DATE NOT NULL,
    absence_end DATE NOT NULL,
    reason VARCHAR(200),
    CHECK (absence_start <= absence_end)
);

CREATE INDEX idx_tasks_project_state
    ON tasks(project_id, state);

CREATE INDEX idx_allocations_resource_dates
    ON allocations(resource_id, allocation_start, allocation_end);

CREATE INDEX idx_allocations_task
    ON allocations(task_id);

CREATE INDEX idx_resource_skills_skill
    ON resource_skills(skill_name, skill_level);

CREATE INDEX idx_task_required_skills_skill
    ON task_required_skills(skill_name, minimum_skill_level);

INSERT INTO projects (
    project_code,
    project_name,
    budget,
    start_date,
    end_date
)
VALUES (
    'PSDP-2026',
    'Public Service Data Platform',
    120000.00,
    '2026-10-19',
    '2026-12-18'
);

INSERT INTO resources (
    resource_code,
    resource_name,
    resource_type,
    weekly_capacity_hours,
    hourly_cost
)
VALUES
    ('P-001', 'Asha Rao', 'person', 40, 75),
    ('P-002', 'Vikram Singh', 'person', 40, 68),
    ('P-003', 'Meera Shah', 'person', 32, 92),
    ('EQ-001', 'Performance Test Cluster', 'equipment', 80, 25);

INSERT INTO resource_skills (
    resource_id,
    skill_name,
    skill_level
)
SELECT resource_id, skill_name, skill_level
FROM (
    VALUES
        ('P-001', 'backend', 3),
        ('P-001', 'api', 3),
        ('P-001', 'security', 3),
        ('P-001', 'postgresql', 3),
        ('P-002', 'frontend', 3),
        ('P-002', 'javascript', 3),
        ('P-002', 'accessibility', 3),
        ('P-003', 'security', 4),
        ('P-003', 'testing', 4),
        ('P-003', 'cloud', 4)
) AS input(resource_code, skill_name, skill_level)
JOIN resources r
    ON r.resource_code = input.resource_code;

INSERT INTO tasks (
    project_id,
    task_code,
    task_name,
    state,
    estimated_hours,
    priority,
    start_date,
    end_date
)
SELECT
    project_id,
    input.task_code,
    input.task_name,
    input.state::task_state,
    input.estimated_hours,
    input.priority,
    input.start_date::date,
    input.end_date::date
FROM projects p
CROSS JOIN (
    VALUES
        (
            'T-API',
            'Secure service implementation',
            'planned',
            72.00,
            1,
            '2026-10-19',
            '2026-10-30'
        ),
        (
            'T-WEB',
            'Accessible public portal',
            'planned',
            64.00,
            2,
            '2026-10-26',
            '2026-11-06'
        ),
        (
            'T-SEC',
            'Security validation',
            'planned',
            40.00,
            1,
            '2026-11-02',
            '2026-11-13'
        )
) AS input(
    task_code,
    task_name,
    state,
    estimated_hours,
    priority,
    start_date,
    end_date
)
WHERE p.project_code = 'PSDP-2026';

INSERT INTO task_required_skills (
    task_id,
    skill_name,
    minimum_skill_level
)
SELECT t.task_id, input.skill_name, input.minimum_skill_level
FROM tasks t
JOIN (
    VALUES
        ('T-API', 'backend', 3),
        ('T-API', 'api', 3),
        ('T-API', 'security', 3),
        ('T-WEB', 'frontend', 3),
        ('T-WEB', 'javascript', 3),
        ('T-WEB', 'accessibility', 3),
        ('T-SEC', 'security', 4),
        ('T-SEC', 'testing', 4)
) AS input(task_code, skill_name, minimum_skill_level)
    ON input.task_code = t.task_code;

-- The allocation transaction represents a planning decision that must
-- satisfy task effort, resource capacity, and qualification requirements.
BEGIN;

INSERT INTO allocations (
    task_id,
    resource_id,
    allocation_start,
    allocation_end,
    allocated_hours
)
SELECT
    t.task_id,
    r.resource_id,
    t.start_date,
    t.end_date,
    72.00
FROM tasks t
JOIN resources r
    ON r.resource_code = 'P-001'
WHERE t.task_code = 'T-API'
  AND r.resource_type = 'person'
  AND NOT EXISTS (
      SELECT 1
      FROM allocations a
      WHERE a.resource_id = r.resource_id
        AND a.state <> 'released'
        AND a.allocation_start <= t.end_date
        AND a.allocation_end >= t.start_date
  );

INSERT INTO allocations (
    task_id,
    resource_id,
    allocation_start,
    allocation_end,
    allocated_hours
)
SELECT
    t.task_id,
    r.resource_id,
    t.start_date,
    t.end_date,
    64.00
FROM tasks t
JOIN resources r
    ON r.resource_code = 'P-002'
WHERE t.task_code = 'T-WEB';

INSERT INTO allocations (
    task_id,
    resource_id,
    allocation_start,
    allocation_end,
    allocated_hours
)
SELECT
    t.task_id,
    r.resource_id,
    t.start_date,
    t.end_date,
    40.00
FROM tasks t
JOIN resources r
    ON r.resource_code = 'P-003'
WHERE t.task_code = 'T-SEC';

COMMIT;

-- Resource utilization is calculated from allocations rather than stored
-- as a mutable value. This prevents the utilization percentage from becoming
-- stale when an allocation is released or changed.

CREATE VIEW resource_utilization AS
SELECT
    r.resource_id,
    r.resource_code,
    r.resource_name,
    r.weekly_capacity_hours,
    COALESCE(
        SUM(
            CASE
                WHEN a.state <> 'released'
                THEN a.allocated_hours
                ELSE 0
            END
        ),
        0
    ) AS allocated_hours,
    ROUND(
        COALESCE(
            SUM(
                CASE
                    WHEN a.state <> 'released'
                    THEN a.allocated_hours
                    ELSE 0
                END
            ),
            0
        ) / r.weekly_capacity_hours * 100,
        2
    ) AS utilization_percent
FROM resources r
LEFT JOIN allocations a
    ON a.resource_id = r.resource_id
GROUP BY
    r.resource_id,
    r.resource_code,
    r.resource_name,
    r.weekly_capacity_hours;

SELECT *
FROM resource_utilization
WHERE resource_type IS NULL
   OR TRUE;

-- Find tasks whose required skills have no qualifying active resource.
SELECT
    t.task_code,
    t.task_name,
    trs.skill_name,
    trs.minimum_skill_level
FROM tasks t
JOIN task_required_skills trs
    ON trs.task_id = t.task_id
WHERE NOT EXISTS (
    SELECT 1
    FROM resources r
    JOIN resource_skills rs
        ON rs.resource_id = r.resource_id
       AND rs.skill_name = trs.skill_name
       AND rs.skill_level >= trs.minimum_skill_level
    WHERE r.resource_type = 'person'
      AND r.active = TRUE
);

-- Identify resources whose planned allocation exceeds their stated capacity.
SELECT
    r.resource_code,
    r.resource_name,
    r.weekly_capacity_hours,
    SUM(a.allocated_hours) AS allocated_hours
FROM resources r
JOIN allocations a
    ON a.resource_id = r.resource_id
WHERE a.state <> 'released'
GROUP BY
    r.resource_code,
    r.resource_name,
    r.weekly_capacity_hours
HAVING SUM(a.allocated_hours) > r.weekly_capacity_hours;

-- Project cost is derived from resource rates and actual planned allocations.
SELECT
    p.project_code,
    p.project_name,
    p.budget,
    COALESCE(
        SUM(a.allocated_hours * r.hourly_cost),
        0
    ) AS planned_resource_cost,
    p.budget -
    COALESCE(
        SUM(a.allocated_hours * r.hourly_cost),
        0
    ) AS remaining_budget
FROM projects p
LEFT JOIN tasks t
    ON t.project_id = p.project_id
LEFT JOIN allocations a
    ON a.task_id = t.task_id
   AND a.state <> 'released'
LEFT JOIN resources r
    ON r.resource_id = a.resource_id
GROUP BY
    p.project_id,
    p.project_code,
    p.project_name,
    p.budget;

-- Detect allocations assigned to resources lacking one or more required skills.
SELECT DISTINCT
    a.allocation_id,
    r.resource_code,
    r.resource_name,
    t.task_code,
    trs.skill_name
FROM allocations a
JOIN resources r
    ON r.resource_id = a.resource_id
JOIN tasks t
    ON t.task_id = a.task_id
JOIN task_required_skills trs
    ON trs.task_id = t.task_id
LEFT JOIN resource_skills rs
    ON rs.resource_id = r.resource_id
   AND rs.skill_name = trs.skill_name
   AND rs.skill_level >= trs.minimum_skill_level
WHERE r.resource_type = 'person'
  AND rs.resource_id IS NULL;

-- Capacity planning can also account for approved absence periods.
SELECT
    r.resource_code,
    r.resource_name,
    SUM(
        CASE
            WHEN a.allocation_start <= ra.absence_end
             AND a.allocation_end >= ra.absence_start
            THEN a.allocated_hours
            ELSE 0
        END
    ) AS overlapping_allocated_hours
FROM resources r
JOIN resource_absences ra
    ON ra.resource_id = r.resource_id
LEFT JOIN allocations a
    ON a.resource_id = r.resource_id
GROUP BY
    r.resource_code,
    r.resource_name;

-- A database constraint protects task effort from being silently exceeded
-- by allocations. The trigger recalculates the task total whenever an
-- allocation is inserted or changed.

CREATE OR REPLACE FUNCTION enforce_task_effort()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    task_limit NUMERIC(10,2);
    allocated_total NUMERIC(10,2);
BEGIN
    SELECT estimated_hours
    INTO task_limit
    FROM tasks
    WHERE task_id = NEW.task_id;

    SELECT COALESCE(SUM(allocated_hours), 0)
    INTO allocated_total
    FROM allocations
    WHERE task_id = NEW.task_id
      AND allocation_id <> COALESCE(NEW.allocation_id, -1)
      AND state <> 'released';

    IF allocated_total + NEW.allocated_hours > task_limit
       AND NEW.state <> 'released' THEN
        RAISE EXCEPTION
            'Task % exceeds estimated effort: allocated %, limit %',
            NEW.task_id,
            allocated_total + NEW.allocated_hours,
            task_limit;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_enforce_task_effort
BEFORE INSERT OR UPDATE OF task_id, allocated_hours, state
ON allocations
FOR EACH ROW
EXECUTE FUNCTION enforce_task_effort();

-- This statement is intentionally invalid and demonstrates database-level
-- enforcement. It is wrapped in a savepoint so the rest of the session
-- remains usable after the expected exception.
BEGIN;

SAVEPOINT invalid_allocation;

DO $$
BEGIN
    BEGIN
        INSERT INTO allocations (
            task_id,
            resource_id,
            allocation_start,
            allocation_end,
            allocated_hours
        )
        SELECT
            t.task_id,
            r.resource_id,
            t.start_date,
            t.end_date,
            10.00
        FROM tasks t
        JOIN resources r
            ON r.resource_code = 'P-003'
        WHERE t.task_code = 'T-SEC';

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected invalid allocation rejected: %',
                SQLERRM;
    END;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_allocation;
COMMIT;

-- A final planning query presents work, ownership, effort, and cost together.
SELECT
    p.project_code,
    t.task_code,
    t.task_name,
    t.state,
    r.resource_code,
    r.resource_name,
    a.allocated_hours,
    r.hourly_cost,
    a.allocated_hours * r.hourly_cost AS allocation_cost
FROM projects p
JOIN tasks t
    ON t.project_id = p.project_id
JOIN allocations a
    ON a.task_id = t.task_id
JOIN resources r
    ON r.resource_id = a.resource_id
WHERE a.state <> 'released'
ORDER BY
    t.priority,
    t.start_date,
    r.resource_name;
