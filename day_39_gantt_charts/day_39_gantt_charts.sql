DROP SCHEMA IF EXISTS gantt_demo CASCADE;
CREATE SCHEMA gantt_demo;

SET search_path TO gantt_demo;

CREATE TYPE task_status AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'COMPLETED',
    'BLOCKED'
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    project_name TEXT NOT NULL,
    project_code TEXT NOT NULL UNIQUE,
    planned_start DATE NOT NULL,
    planned_end DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT projects_date_range_chk
        CHECK (planned_end >= planned_start)
);

CREATE TABLE resources (
    resource_id BIGSERIAL PRIMARY KEY,
    resource_name TEXT NOT NULL UNIQUE,
    resource_type TEXT NOT NULL,
    capacity_hours NUMERIC(8,2) NOT NULL DEFAULT 40,
    CONSTRAINT resources_capacity_chk
        CHECK (capacity_hours > 0)
);

CREATE TABLE tasks (
    task_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    task_code TEXT NOT NULL,
    task_name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    progress_percent NUMERIC(5,2) NOT NULL DEFAULT 0,
    status task_status NOT NULL DEFAULT 'NOT_STARTED',
    resource_id BIGINT REFERENCES resources(resource_id),
    is_milestone BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT tasks_unique_code_per_project
        UNIQUE (project_id, task_code),
    CONSTRAINT tasks_date_range_chk
        CHECK (end_date >= start_date),
    CONSTRAINT tasks_progress_chk
        CHECK (progress_percent BETWEEN 0 AND 100),
    CONSTRAINT tasks_milestone_date_chk
        CHECK (
            NOT is_milestone
            OR start_date = end_date
        )
);

CREATE TABLE task_dependencies (
    predecessor_task_id BIGINT NOT NULL
        REFERENCES tasks(task_id)
        ON DELETE CASCADE,
    successor_task_id BIGINT NOT NULL
        REFERENCES tasks(task_id)
        ON DELETE CASCADE,
    PRIMARY KEY (predecessor_task_id, successor_task_id),
    CONSTRAINT task_dependencies_no_self_dependency
        CHECK (predecessor_task_id <> successor_task_id)
);

CREATE INDEX idx_tasks_project_dates
    ON tasks(project_id, start_date, end_date);

CREATE INDEX idx_tasks_resource_dates
    ON tasks(resource_id, start_date, end_date);

CREATE INDEX idx_task_dependencies_successor
    ON task_dependencies(successor_task_id);

CREATE INDEX idx_task_dependencies_predecessor
    ON task_dependencies(predecessor_task_id);

INSERT INTO projects (
    project_name,
    project_code,
    planned_start,
    planned_end
)
VALUES (
    'Operations Analytics Platform',
    'OAP-2026',
    DATE '2026-10-12',
    DATE '2026-11-23'
);

INSERT INTO resources (
    resource_name,
    resource_type,
    capacity_hours
)
VALUES
    ('Business Analysis', 'TEAM', 40),
    ('Architecture', 'TEAM', 40),
    ('Backend Engineering', 'TEAM', 80),
    ('Frontend Engineering', 'TEAM', 40),
    ('Quality Assurance', 'TEAM', 40),
    ('Release Management', 'TEAM', 20);

INSERT INTO tasks (
    project_id,
    task_code,
    task_name,
    start_date,
    end_date,
    progress_percent,
    status,
    resource_id,
    is_milestone
)
SELECT
    p.project_id,
    v.task_code,
    v.task_name,
    v.start_date,
    v.end_date,
    v.progress_percent,
    v.status::task_status,
    r.resource_id,
    v.is_milestone
FROM projects p
CROSS JOIN (
    VALUES
        (
            'REQ',
            'Requirements Analysis',
            DATE '2026-10-12',
            DATE '2026-10-16',
            100.00,
            'COMPLETED',
            'Business Analysis',
            FALSE
        ),
        (
            'ARCH',
            'Solution Architecture',
            DATE '2026-10-19',
            DATE '2026-10-23',
            80.00,
            'IN_PROGRESS',
            'Architecture',
            FALSE
        ),
        (
            'DB',
            'Database Development',
            DATE '2026-10-26',
            DATE '2026-10-30',
            45.00,
            'IN_PROGRESS',
            'Backend Engineering',
            FALSE
        ),
        (
            'API',
            'API Development',
            DATE '2026-10-26',
            DATE '2026-11-06',
            35.00,
            'IN_PROGRESS',
            'Backend Engineering',
            FALSE
        ),
        (
            'UI',
            'Operations Dashboard',
            DATE '2026-10-26',
            DATE '2026-11-13',
            25.00,
            'IN_PROGRESS',
            'Frontend Engineering',
            FALSE
        ),
        (
            'TEST',
            'Integration Testing',
            DATE '2026-11-16',
            DATE '2026-11-20',
            0.00,
            'NOT_STARTED',
            'Quality Assurance',
            FALSE
        ),
        (
            'LIVE',
            'Production Launch',
            DATE '2026-11-23',
            DATE '2026-11-23',
            0.00,
            'NOT_STARTED',
            'Release Management',
            TRUE
        )
) AS v(
    task_code,
    task_name,
    start_date,
    end_date,
    progress_percent,
    status,
    resource_name,
    is_milestone
)
JOIN resources r
    ON r.resource_name = v.resource_name
WHERE p.project_code = 'OAP-2026';

INSERT INTO task_dependencies (
    predecessor_task_id,
    successor_task_id
)
SELECT predecessor.task_id, successor.task_id
FROM (
    VALUES
        ('REQ', 'ARCH'),
        ('ARCH', 'DB'),
        ('ARCH', 'API'),
        ('ARCH', 'UI'),
        ('DB', 'TEST'),
        ('API', 'TEST'),
        ('UI', 'TEST'),
        ('TEST', 'LIVE')
) AS dependencies(predecessor_code, successor_code)
JOIN tasks predecessor
    ON predecessor.task_code = dependencies.predecessor_code
JOIN tasks successor
    ON successor.task_code = dependencies.successor_code
JOIN projects p1
    ON p1.project_id = predecessor.project_id
JOIN projects p2
    ON p2.project_id = successor.project_id
WHERE p1.project_code = 'OAP-2026'
  AND p2.project_code = 'OAP-2026';

CREATE VIEW task_schedule AS
SELECT
    p.project_code,
    t.task_code,
    t.task_name,
    t.start_date,
    t.end_date,
    (t.end_date - t.start_date + 1) AS duration_days,
    t.progress_percent,
    t.status,
    r.resource_name,
    t.is_milestone
FROM projects p
JOIN tasks t
    ON t.project_id = p.project_id
LEFT JOIN resources r
    ON r.resource_id = t.resource_id;

CREATE VIEW dependency_schedule_validation AS
SELECT
    predecessor.task_code AS predecessor,
    successor.task_code AS successor,
    predecessor.end_date AS predecessor_end,
    successor.start_date AS successor_start,
    CASE
        WHEN predecessor.end_date < successor.start_date
            THEN 'VALID'
        ELSE 'INVALID'
    END AS dependency_status
FROM task_dependencies d
JOIN tasks predecessor
    ON predecessor.task_id = d.predecessor_task_id
JOIN tasks successor
    ON successor.task_id = d.successor_task_id;

CREATE VIEW resource_overlap_report AS
SELECT
    r.resource_name,
    first_task.task_code AS first_task,
    second_task.task_code AS second_task,
    first_task.start_date AS first_start,
    first_task.end_date AS first_end,
    second_task.start_date AS second_start,
    second_task.end_date AS second_end
FROM tasks first_task
JOIN tasks second_task
    ON first_task.task_id < second_task.task_id
   AND first_task.resource_id = second_task.resource_id
   AND first_task.start_date <= second_task.end_date
   AND second_task.start_date <= first_task.end_date
JOIN resources r
    ON r.resource_id = first_task.resource_id;

-- The schedule view provides the rows needed by a Gantt renderer.
SELECT *
FROM task_schedule
ORDER BY start_date, task_code;

-- Every predecessor must finish strictly before its successor starts.
SELECT *
FROM dependency_schedule_validation
WHERE dependency_status = 'INVALID';

-- Overlapping assignments identify resource-loading problems
-- that a calendar-only Gantt view may hide.
SELECT *
FROM resource_overlap_report
ORDER BY resource_name, first_start;

-- A milestone query isolates zero-duration release events.
SELECT
    project_code,
    task_code,
    task_name,
    start_date AS milestone_date
FROM task_schedule
WHERE is_milestone
ORDER BY milestone_date;

-- Calculate weighted project completion from task duration.
SELECT
    project_code,
    SUM(duration_days) AS planned_task_days,
    ROUND(
        SUM(duration_days * progress_percent / 100.0),
        2
    ) AS completed_equivalent_task_days,
    ROUND(
        SUM(duration_days * progress_percent / 100.0)
        / NULLIF(SUM(duration_days), 0) * 100,
        2
    ) AS weighted_completion_percent
FROM task_schedule
GROUP BY project_code;

-- Show predecessor relationships in the order required by the schedule.
WITH RECURSIVE dependency_tree AS (
    SELECT
        t.task_id,
        t.task_code,
        t.task_name,
        0 AS dependency_depth
    FROM tasks t
    WHERE t.task_code = 'LIVE'

    UNION ALL

    SELECT
        predecessor.task_id,
        predecessor.task_code,
        predecessor.task_name,
        dependency_tree.dependency_depth + 1
    FROM dependency_tree
    JOIN task_dependencies d
        ON d.successor_task_id = dependency_tree.task_id
    JOIN tasks predecessor
        ON predecessor.task_id = d.predecessor_task_id
)
SELECT
    dependency_depth,
    task_code,
    task_name
FROM dependency_tree
ORDER BY dependency_depth DESC;

-- PostgreSQL transaction demonstrates an atomic progress update.
BEGIN;

UPDATE tasks
SET
    progress_percent = 60.00,
    status = 'IN_PROGRESS'
WHERE task_code = 'API'
  AND project_id = (
      SELECT project_id
      FROM projects
      WHERE project_code = 'OAP-2026'
  );

-- The validation query runs inside the same transaction, so downstream
-- reporting sees a consistent version of the schedule.
SELECT
    task_code,
    progress_percent,
    status
FROM tasks
WHERE task_code = 'API';

COMMIT;

-- Database-level validation exposes an intentionally impossible
-- dependency without permanently changing the schedule.
BEGIN;

UPDATE tasks
SET start_date = DATE '2026-10-15'
WHERE task_code = 'ARCH'
  AND project_id = (
      SELECT project_id
      FROM projects
      WHERE project_code = 'OAP-2026'
  );

SELECT *
FROM dependency_schedule_validation
WHERE dependency_status = 'INVALID';

ROLLBACK;

-- A Gantt chart is a visualization layer. The relational model preserves
-- dates, dependencies, resources, progress, and milestones as data that
-- other reporting or visualization systems can consume.
