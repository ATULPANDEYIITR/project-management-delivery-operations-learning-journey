DROP SCHEMA IF EXISTS project_timeline CASCADE;

CREATE SCHEMA project_timeline;

SET search_path TO project_timeline;

CREATE TYPE task_priority AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE task_status AS ENUM (
    'planned',
    'in_progress',
    'completed',
    'blocked',
    'cancelled'
);

CREATE TYPE milestone_status AS ENUM (
    'upcoming',
    'due_soon',
    'completed',
    'overdue'
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    planned_start DATE NOT NULL,
    planned_end DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (planned_end >= planned_start)
);

CREATE TABLE project_members (
    member_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    member_name VARCHAR(150) NOT NULL,
    role_name VARCHAR(100) NOT NULL,
    email VARCHAR(320),
    UNIQUE (project_id, member_name),
    UNIQUE (project_id, email)
);

CREATE TABLE tasks (
    task_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    task_code VARCHAR(40) NOT NULL,
    task_name VARCHAR(250) NOT NULL,
    owner_member_id BIGINT REFERENCES project_members(member_id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    priority task_priority NOT NULL DEFAULT 'medium',
    status task_status NOT NULL DEFAULT 'planned',
    progress_percent INTEGER NOT NULL DEFAULT 0,
    estimated_effort_hours NUMERIC(10,2) NOT NULL DEFAULT 0,
    actual_effort_hours NUMERIC(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, task_code),
    CHECK (end_date >= start_date),
    CHECK (progress_percent BETWEEN 0 AND 100),
    CHECK (estimated_effort_hours >= 0),
    CHECK (actual_effort_hours >= 0),
    CHECK (
        (status = 'completed' AND progress_percent = 100)
        OR
        (status <> 'completed')
    )
);

CREATE TABLE task_dependencies (
    predecessor_task_id BIGINT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    successor_task_id BIGINT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    PRIMARY KEY (predecessor_task_id, successor_task_id),
    CHECK (predecessor_task_id <> successor_task_id)
);

CREATE TABLE milestones (
    milestone_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    milestone_name VARCHAR(250) NOT NULL,
    due_date DATE NOT NULL,
    description TEXT,
    status milestone_status NOT NULL DEFAULT 'upcoming',
    completed_at TIMESTAMPTZ,
    UNIQUE (project_id, milestone_name)
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    check_name VARCHAR(200) NOT NULL,
    passed BOOLEAN NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

CREATE INDEX idx_tasks_project_dates
    ON tasks(project_id, start_date, end_date);

CREATE INDEX idx_tasks_owner
    ON tasks(owner_member_id);

CREATE INDEX idx_task_dependencies_successor
    ON task_dependencies(successor_task_id);

CREATE INDEX idx_milestones_project_due
    ON milestones(project_id, due_date);

CREATE INDEX idx_status_checks_task
    ON status_checks(task_id, checked_at DESC);

CREATE OR REPLACE FUNCTION validate_task_dependency_dates()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    predecessor_end DATE;
    successor_start DATE;
BEGIN
    SELECT end_date
    INTO predecessor_end
    FROM tasks
    WHERE task_id = NEW.predecessor_task_id;

    SELECT start_date
    INTO successor_start
    FROM tasks
    WHERE task_id = NEW.successor_task_id;

    IF predecessor_end IS NULL OR successor_start IS NULL THEN
        RETURN NEW;
    END IF;

    IF predecessor_end >= successor_start THEN
        RAISE EXCEPTION
            'Invalid dependency: predecessor task % ends on %, but successor task % starts on %',
            NEW.predecessor_task_id,
            predecessor_end,
            NEW.successor_task_id,
            successor_start;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_task_dependency_dates
BEFORE INSERT OR UPDATE ON task_dependencies
FOR EACH ROW
EXECUTE FUNCTION validate_task_dependency_dates();

CREATE OR REPLACE FUNCTION refresh_milestone_status(
    p_project_id BIGINT,
    p_as_of DATE
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE milestones
    SET status =
        CASE
            WHEN completed_at IS NOT NULL THEN 'completed'::milestone_status
            WHEN due_date < p_as_of THEN 'overdue'::milestone_status
            WHEN due_date <= p_as_of + 7 THEN 'due_soon'::milestone_status
            ELSE 'upcoming'::milestone_status
        END
    WHERE project_id = p_project_id;
END;
$$;

CREATE VIEW project_task_timeline AS
SELECT
    p.project_code,
    p.project_name,
    t.task_code,
    t.task_name,
    t.start_date,
    t.end_date,
    (t.end_date - t.start_date) + 1 AS calendar_days,
    t.priority,
    t.status,
    t.progress_percent,
    m.member_name AS owner
FROM projects p
JOIN tasks t
    ON t.project_id = p.project_id
LEFT JOIN project_members m
    ON m.member_id = t.owner_member_id;

CREATE VIEW project_schedule_health AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    MIN(t.start_date) AS actual_task_start,
    MAX(t.end_date) AS actual_task_end,
    ROUND(
        SUM(
            ((t.end_date - t.start_date) + 1)
            * t.progress_percent
        )::NUMERIC
        /
        NULLIF(
            SUM((t.end_date - t.start_date) + 1),
            0
        ),
        2
    ) AS weighted_progress_percent,
    COUNT(*) FILTER (
        WHERE t.status <> 'completed'
          AND t.end_date < CURRENT_DATE
    ) AS overdue_tasks,
    COUNT(*) FILTER (
        WHERE t.priority IN ('high', 'critical')
          AND t.progress_percent < 50
    ) AS high_risk_tasks
FROM projects p
JOIN tasks t
    ON t.project_id = p.project_id
GROUP BY p.project_id, p.project_code, p.project_name;

INSERT INTO projects (
    project_code,
    project_name,
    planned_start,
    planned_end
)
VALUES (
    'OPS-AN-2026',
    'Operations Analytics Platform',
    DATE '2026-10-12',
    DATE '2026-11-20'
);

INSERT INTO project_members (
    project_id,
    member_name,
    role_name,
    email
)
SELECT
    project_id,
    member_name,
    role_name,
    email
FROM projects
CROSS JOIN (
    VALUES
        ('Anita Rao', 'Project Manager', 'anita@example.org'),
        ('Rahul Mehta', 'Business Analyst', 'rahul@example.org'),
        ('Neha Singh', 'Data Architect', 'neha@example.org'),
        ('Vikram Shah', 'Data Engineer', 'vikram@example.org'),
        ('Priya Nair', 'QA Lead', 'priya@example.org'),
        ('Arjun Kumar', 'Release Manager', 'arjun@example.org')
) AS members(member_name, role_name, email)
WHERE project_code = 'OPS-AN-2026';

INSERT INTO tasks (
    project_id,
    task_code,
    task_name,
    owner_member_id,
    start_date,
    end_date,
    priority,
    status,
    progress_percent,
    estimated_effort_hours
)
SELECT
    p.project_id,
    task_data.task_code,
    task_data.task_name,
    member.member_id,
    task_data.start_date,
    task_data.end_date,
    task_data.priority::task_priority,
    task_data.status::task_status,
    task_data.progress_percent,
    task_data.estimated_effort_hours
FROM projects p
JOIN (
    VALUES
        (
            'T01',
            'Project kickoff and scope baseline',
            'Anita Rao',
            DATE '2026-10-12',
            DATE '2026-10-13',
            'high',
            'completed',
            100,
            16.0
        ),
        (
            'T02',
            'Requirements workshops',
            'Rahul Mehta',
            DATE '2026-10-14',
            DATE '2026-10-20',
            'high',
            'in_progress',
            75,
            40.0
        ),
        (
            'T03',
            'Data architecture assessment',
            'Neha Singh',
            DATE '2026-10-21',
            DATE '2026-10-28',
            'high',
            'in_progress',
            35,
            56.0
        ),
        (
            'T04',
            'Analytics pipeline implementation',
            'Vikram Shah',
            DATE '2026-10-29',
            DATE '2026-11-06',
            'critical',
            'in_progress',
            25,
            72.0
        ),
        (
            'T05',
            'Integration and acceptance testing',
            'Priya Nair',
            DATE '2026-11-09',
            DATE '2026-11-13',
            'high',
            'planned',
            0,
            40.0
        ),
        (
            'T06',
            'Production handover',
            'Arjun Kumar',
            DATE '2026-11-16',
            DATE '2026-11-20',
            'critical',
            'planned',
            0,
            24.0
        )
) AS task_data(
    task_code,
    task_name,
    owner_name,
    start_date,
    end_date,
    priority,
    status,
    progress_percent,
    estimated_effort_hours
)
    ON TRUE
JOIN project_members member
    ON member.project_id = p.project_id
   AND member.member_name = task_data.owner_name
WHERE p.project_code = 'OPS-AN-2026';

INSERT INTO task_dependencies (
    predecessor_task_id,
    successor_task_id
)
SELECT predecessor.task_id, successor.task_id
FROM tasks predecessor
JOIN tasks successor
    ON predecessor.project_id = successor.project_id
WHERE predecessor.project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'OPS-AN-2026'
)
AND (
    (predecessor.task_code = 'T01' AND successor.task_code = 'T02')
    OR
    (predecessor.task_code = 'T02' AND successor.task_code = 'T03')
    OR
    (predecessor.task_code = 'T03' AND successor.task_code = 'T04')
    OR
    (predecessor.task_code = 'T04' AND successor.task_code = 'T05')
    OR
    (predecessor.task_code = 'T05' AND successor.task_code = 'T06')
);

INSERT INTO milestones (
    project_id,
    milestone_name,
    due_date,
    description,
    status
)
SELECT
    project_id,
    milestone_data.milestone_name,
    milestone_data.due_date,
    milestone_data.description,
    milestone_data.status::milestone_status
FROM projects
CROSS JOIN (
    VALUES
        (
            'Scope baseline approved',
            DATE '2026-10-20',
            'Requirements baseline accepted by stakeholders',
            'completed'
        ),
        (
            'Prototype ready',
            DATE '2026-11-06',
            'Analytics pipeline available for acceptance testing',
            'upcoming'
        ),
        (
            'Production release',
            DATE '2026-11-20',
            'Operational handover completed',
            'upcoming'
        )
) AS milestone_data(
    milestone_name,
    due_date,
    description,
    status
)
WHERE project_code = 'OPS-AN-2026';

INSERT INTO status_checks (
    task_id,
    check_name,
    passed,
    details
)
SELECT
    task_id,
    checks.check_name,
    checks.passed,
    checks.details
FROM tasks
CROSS JOIN (
    VALUES
        (
            'Source data availability',
            TRUE,
            'Required operational source tables are available'
        ),
        (
            'Architecture review',
            TRUE,
            'Architecture baseline accepted'
        ),
        (
            'Pipeline integration test',
            FALSE,
            'Two source mappings remain unresolved'
        )
) AS checks(check_name, passed, details)
WHERE task_code = 'T04';

SELECT *
FROM project_task_timeline
WHERE project_code = 'OPS-AN-2026'
ORDER BY start_date, task_code;

SELECT *
FROM project_schedule_health
WHERE project_code = 'OPS-AN-2026';

SELECT
    predecessor.task_code AS predecessor,
    predecessor.task_name AS predecessor_name,
    successor.task_code AS successor,
    successor.task_name AS successor_name,
    predecessor.end_date AS predecessor_end,
    successor.start_date AS successor_start
FROM task_dependencies d
JOIN tasks predecessor
    ON predecessor.task_id = d.predecessor_task_id
JOIN tasks successor
    ON successor.task_id = d.successor_task_id
ORDER BY predecessor.start_date;

SELECT
    m.milestone_name,
    m.due_date,
    m.status,
    m.description
FROM milestones m
JOIN projects p
    ON p.project_id = m.project_id
WHERE p.project_code = 'OPS-AN-2026'
ORDER BY m.due_date;

SELECT
    t.task_code,
    t.task_name,
    t.priority,
    t.progress_percent,
    t.end_date,
    CASE
        WHEN t.end_date < DATE '2026-11-10'
             AND t.status <> 'completed'
            THEN 'overdue'
        WHEN t.priority IN ('high', 'critical')
             AND t.progress_percent < 50
            THEN 'high_progress_risk'
        WHEN t.status = 'planned'
             AND t.start_date <= DATE '2026-11-10'
            THEN 'not_started'
        ELSE 'normal'
    END AS schedule_risk
FROM tasks t
JOIN projects p
    ON p.project_id = t.project_id
WHERE p.project_code = 'OPS-AN-2026'
ORDER BY
    CASE
        WHEN t.end_date < DATE '2026-11-10'
             AND t.status <> 'completed' THEN 1
        WHEN t.priority IN ('high', 'critical')
             AND t.progress_percent < 50 THEN 2
        ELSE 3
    END,
    t.start_date;

BEGIN;

UPDATE tasks
SET
    progress_percent = 100,
    status = 'completed',
    actual_effort_hours = 44
WHERE task_code = 'T02'
  AND project_id = (
      SELECT project_id
      FROM projects
      WHERE project_code = 'OPS-AN-2026'
  );

UPDATE milestones
SET
    status = 'completed',
    completed_at = CURRENT_TIMESTAMP
WHERE milestone_name = 'Scope baseline approved'
  AND project_id = (
      SELECT project_id
      FROM projects
      WHERE project_code = 'OPS-AN-2026'
  );

COMMIT;

SELECT
    task_code,
    task_name,
    status,
    progress_percent,
    actual_effort_hours
FROM tasks
WHERE project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'OPS-AN-2026'
)
ORDER BY start_date;

DO $$
BEGIN
    BEGIN
        INSERT INTO tasks (
            project_id,
            task_code,
            task_name,
            start_date,
            end_date,
            priority,
            status,
            progress_percent
        )
        SELECT
            project_id,
            'INVALID-01',
            'Invalid schedule example',
            DATE '2026-12-10',
            DATE '2026-12-01',
            'medium',
            'planned',
            0
        FROM projects
        WHERE project_code = 'OPS-AN-2026';

        EXCEPTION
            WHEN check_violation THEN
                RAISE NOTICE
                    'Database correctly rejected a task whose end date precedes its start date.';
    END;
END;
$$;

SELECT
    task_code,
    task_name,
    start_date,
    end_date,
    EXTRACT(DAY FROM end_date - start_date) + 1 AS calendar_days,
    ROUND(
        (
            EXTRACT(DAY FROM end_date - start_date) + 1
        )::NUMERIC / 7,
        2
    ) AS approximate_weeks
FROM tasks
WHERE project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'OPS-AN-2026'
)
ORDER BY start_date;

SELECT
    member.member_name,
    member.role_name,
    COUNT(task.task_id) AS assigned_tasks,
    SUM((task.end_date - task.start_date) + 1) AS assigned_calendar_days,
    ROUND(
        AVG(task.progress_percent),
        2
    ) AS average_progress
FROM project_members member
LEFT JOIN tasks task
    ON task.owner_member_id = member.member_id
WHERE member.project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'OPS-AN-2026'
)
GROUP BY member.member_id, member.member_name, member.role_name
ORDER BY assigned_calendar_days DESC NULLS LAST;

SELECT
    t.task_code,
    t.task_name,
    COUNT(sc.status_check_id) AS checks_run,
    COUNT(*) FILTER (WHERE sc.passed) AS checks_passed,
    COUNT(*) FILTER (WHERE NOT sc.passed) AS checks_failed
FROM tasks t
LEFT JOIN status_checks sc
    ON sc.task_id = t.task_id
WHERE t.project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'OPS-AN-2026'
)
GROUP BY t.task_id, t.task_code, t.task_name
ORDER BY t.task_code;
