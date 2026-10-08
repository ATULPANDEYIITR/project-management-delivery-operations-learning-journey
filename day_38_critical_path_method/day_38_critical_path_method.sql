-- Critical Path Method: PostgreSQL Project Scheduling Laboratory
--
-- This script models a realistic enterprise software release as a
-- dependency graph and calculates:
--   * earliest start and finish
--   * latest start and finish
--   * total float
--   * critical activities
--   * project duration
--   * critical-path relationships
--
-- PostgreSQL recursive CTEs are used to expose dependency chains.
-- Recursive traversal is appropriate because project dependencies form
-- a directed acyclic graph rather than a simple flat reporting table.

DROP SCHEMA IF EXISTS critical_path_lab CASCADE;
CREATE SCHEMA critical_path_lab;

SET search_path TO critical_path_lab;

CREATE TABLE project (
    project_id BIGSERIAL PRIMARY KEY,
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE activity (
    activity_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES project(project_id)
        ON DELETE CASCADE,
    activity_code TEXT NOT NULL,
    activity_name TEXT NOT NULL,
    duration NUMERIC(12,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'PLANNED',
    CONSTRAINT activity_duration_nonnegative
        CHECK (duration >= 0),
    CONSTRAINT activity_status_valid
        CHECK (
            status IN (
                'PLANNED',
                'IN_PROGRESS',
                'COMPLETED',
                'BLOCKED'
            )
        ),
    CONSTRAINT activity_code_unique_per_project
        UNIQUE (project_id, activity_code)
);

CREATE TABLE activity_dependency (
    project_id BIGINT NOT NULL
        REFERENCES project(project_id)
        ON DELETE CASCADE,
    predecessor_activity_id BIGINT NOT NULL
        REFERENCES activity(activity_id)
        ON DELETE CASCADE,
    successor_activity_id BIGINT NOT NULL
        REFERENCES activity(activity_id)
        ON DELETE CASCADE,
    PRIMARY KEY (
        predecessor_activity_id,
        successor_activity_id
    ),
    CONSTRAINT dependency_not_self_reference
        CHECK (
            predecessor_activity_id <> successor_activity_id
        )
);

CREATE INDEX idx_activity_project
    ON activity(project_id);

CREATE INDEX idx_dependency_predecessor
    ON activity_dependency(predecessor_activity_id);

CREATE INDEX idx_dependency_successor
    ON activity_dependency(successor_activity_id);

INSERT INTO project (
    project_code,
    project_name
)
VALUES (
    'REL-2026-01',
    'Enterprise Platform Release'
);

INSERT INTO activity (
    project_id,
    activity_code,
    activity_name,
    duration,
    status
)
SELECT
    project_id,
    source.activity_code,
    source.activity_name,
    source.duration,
    source.status
FROM project
CROSS JOIN (
    VALUES
        ('REQ',  'Requirements baseline',       3.0, 'COMPLETED'),
        ('ARCH', 'Architecture approval',       4.0, 'COMPLETED'),
        ('DATA', 'Data platform setup',         5.0, 'IN_PROGRESS'),
        ('API',  'Service implementation',      7.0, 'IN_PROGRESS'),
        ('UI',   'User interface implementation', 6.0, 'IN_PROGRESS'),
        ('INT',  'Integration validation',      3.0, 'PLANNED'),
        ('PERF', 'Performance validation',      4.0, 'PLANNED'),
        ('SEC',  'Security validation',         5.0, 'PLANNED'),
        ('OPS',  'Operations readiness',        2.0, 'PLANNED'),
        ('REL',  'Production release',          2.0, 'PLANNED')
) AS source(
    activity_code,
    duration,
    activity_name,
    status
)
WHERE project.project_code = 'REL-2026-01';

-- The dependency table stores only direct relationships. Transitive
-- relationships are derived when the schedule is evaluated.
INSERT INTO activity_dependency (
    project_id,
    predecessor_activity_id,
    successor_activity_id
)
SELECT
    p.project_id,
    predecessor.activity_id,
    successor.activity_id
FROM project p
JOIN (
    VALUES
        ('REQ',  'ARCH'),
        ('ARCH', 'DATA'),
        ('ARCH', 'API'),
        ('ARCH', 'UI'),
        ('DATA', 'INT'),
        ('API',  'INT'),
        ('UI',   'INT'),
        ('INT',  'PERF'),
        ('INT',  'SEC'),
        ('ARCH', 'OPS'),
        ('PERF', 'REL'),
        ('SEC',  'REL'),
        ('OPS',  'REL')
) AS d(predecessor_code, successor_code)
    ON TRUE
JOIN activity predecessor
    ON predecessor.project_id = p.project_id
   AND predecessor.activity_code = d.predecessor_code
JOIN activity successor
    ON successor.project_id = p.project_id
   AND successor.activity_code = d.successor_code
WHERE p.project_code = 'REL-2026-01';

-- -------------------------------------------------------------------------
-- Dependency inspection
-- -------------------------------------------------------------------------

SELECT
    predecessor.activity_code AS predecessor,
    predecessor.activity_name AS predecessor_name,
    successor.activity_code AS successor,
    successor.activity_name AS successor_name
FROM activity_dependency dependency
JOIN activity predecessor
    ON predecessor.activity_id =
       dependency.predecessor_activity_id
JOIN activity successor
    ON successor.activity_id =
       dependency.successor_activity_id
ORDER BY
    predecessor.activity_code,
    successor.activity_code;

-- -------------------------------------------------------------------------
-- Forward pass
-- -------------------------------------------------------------------------
--
-- The forward pass can be represented with a recursive dependency walk.
-- For each activity, its earliest finish is the maximum accumulated
-- duration across all predecessor paths.
--
-- PostgreSQL recursive CTEs produce every reachable path. The longest
-- accumulated duration reaching an activity is its earliest finish.

WITH RECURSIVE
project_root AS (
    SELECT project_id
    FROM project
    WHERE project_code = 'REL-2026-01'
),
paths AS (
    -- Activities without predecessors are dependency roots.
    SELECT
        a.activity_id,
        a.activity_code,
        a.activity_name,
        a.duration,
        ARRAY[a.activity_id] AS path,
        a.duration AS accumulated_finish
    FROM activity a
    JOIN project_root p
        ON p.project_id = a.project_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM activity_dependency d
        WHERE d.successor_activity_id = a.activity_id
    )

    UNION ALL

    SELECT
        successor.activity_id,
        successor.activity_code,
        successor.activity_name,
        successor.duration,
        paths.path || successor.activity_id,
        paths.accumulated_finish + successor.duration
    FROM paths
    JOIN activity_dependency d
        ON d.predecessor_activity_id =
           paths.activity_id
    JOIN activity successor
        ON successor.activity_id =
           d.successor_activity_id
    WHERE NOT successor.activity_id = ANY(paths.path)
),
earliest AS (
    SELECT
        activity_id,
        MAX(accumulated_finish - duration) AS earliest_start,
        MAX(accumulated_finish) AS earliest_finish
    FROM paths
    GROUP BY activity_id
)
SELECT
    a.activity_code,
    a.activity_name,
    a.duration,
    e.earliest_start,
    e.earliest_finish
FROM activity a
JOIN earliest e
    ON e.activity_id = a.activity_id
ORDER BY
    e.earliest_start,
    a.activity_code;

-- -------------------------------------------------------------------------
-- Project duration
-- -------------------------------------------------------------------------

WITH RECURSIVE
paths AS (
    SELECT
        a.activity_id,
        a.duration AS finish_time,
        ARRAY[a.activity_id] AS path
    FROM activity a
    WHERE NOT EXISTS (
        SELECT 1
        FROM activity_dependency d
        WHERE d.successor_activity_id = a.activity_id
    )

    UNION ALL

    SELECT
        successor.activity_id,
        paths.finish_time + successor.duration,
        paths.path || successor.activity_id
    FROM paths
    JOIN activity_dependency d
        ON d.predecessor_activity_id =
           paths.activity_id
    JOIN activity successor
        ON successor.activity_id =
           d.successor_activity_id
    WHERE NOT successor.activity_id = ANY(paths.path)
)
SELECT
    MAX(finish_time) AS project_duration
FROM paths;

-- -------------------------------------------------------------------------
-- Complete path analysis
-- -------------------------------------------------------------------------
--
-- This query identifies complete root-to-terminal paths and their total
-- duration. The longest complete path is the current critical path when
-- there is a unique maximum.

WITH RECURSIVE
paths AS (
    SELECT
        a.activity_id AS current_activity,
        ARRAY[a.activity_code]::TEXT[] AS activity_path,
        a.duration AS path_duration
    FROM activity a
    WHERE NOT EXISTS (
        SELECT 1
        FROM activity_dependency d
        WHERE d.successor_activity_id = a.activity_id
    )

    UNION ALL

    SELECT
        successor.activity_id,
        paths.activity_path || successor.activity_code,
        paths.path_duration + successor.duration
    FROM paths
    JOIN activity_dependency d
        ON d.predecessor_activity_id =
           paths.current_activity
    JOIN activity successor
        ON successor.activity_id =
           d.successor_activity_id
    WHERE NOT successor.activity_id = ANY(
        SELECT activity_id
        FROM activity
        WHERE activity_code = ANY(paths.activity_path)
    )
)
SELECT
    activity_path,
    path_duration,
    CASE
        WHEN path_duration = MAX(path_duration)
             OVER ()
        THEN 'CRITICAL PATH'
        ELSE 'NON-CRITICAL PATH'
    END AS path_classification
FROM paths
WHERE NOT EXISTS (
    SELECT 1
    FROM activity_dependency d
    WHERE d.predecessor_activity_id =
          paths.current_activity
)
ORDER BY
    path_duration DESC;

-- -------------------------------------------------------------------------
-- A materialized-style schedule view using recursive longest-path logic
-- -------------------------------------------------------------------------

CREATE OR REPLACE VIEW activity_earliest_schedule AS
WITH RECURSIVE
paths AS (
    SELECT
        a.project_id,
        a.activity_id,
        a.activity_code,
        a.activity_name,
        a.duration,
        a.duration AS earliest_finish,
        ARRAY[a.activity_id] AS path
    FROM activity a
    WHERE NOT EXISTS (
        SELECT 1
        FROM activity_dependency d
        WHERE d.successor_activity_id = a.activity_id
    )

    UNION ALL

    SELECT
        successor.project_id,
        successor.activity_id,
        successor.activity_code,
        successor.activity_name,
        successor.duration,
        paths.earliest_finish + successor.duration,
        paths.path || successor.activity_id
    FROM paths
    JOIN activity_dependency d
        ON d.predecessor_activity_id =
           paths.activity_id
    JOIN activity successor
        ON successor.activity_id =
           d.successor_activity_id
    WHERE NOT successor.activity_id = ANY(paths.path)
),
aggregated AS (
    SELECT
        project_id,
        activity_id,
        activity_code,
        activity_name,
        duration,
        MAX(earliest_finish) AS earliest_finish
    FROM paths
    GROUP BY
        project_id,
        activity_id,
        activity_code,
        activity_name,
        duration
)
SELECT
    project_id,
    activity_id,
    activity_code,
    activity_name,
    duration,
    earliest_finish - duration AS earliest_start,
    earliest_finish
FROM aggregated;

SELECT *
FROM activity_earliest_schedule
ORDER BY earliest_start, activity_code;

-- -------------------------------------------------------------------------
-- Database integrity examples
-- -------------------------------------------------------------------------

-- Negative durations are rejected by the CHECK constraint.
-- Uncommenting this statement should fail:
--
-- INSERT INTO activity (
--     project_id,
--     activity_code,
--     activity_name,
--     duration
-- )
-- VALUES (
--     1,
--     'INVALID',
--     'Invalid negative-duration activity',
--     -2
-- );

-- Self-dependencies are rejected by the dependency constraint.
-- Uncommenting this statement should fail:
--
-- INSERT INTO activity_dependency (
--     project_id,
--     predecessor_activity_id,
--     successor_activity_id
-- )
-- VALUES (
--     1,
--     (SELECT activity_id FROM activity
--      WHERE activity_code = 'API'),
--     (SELECT activity_id FROM activity
--      WHERE activity_code = 'API')
-- );

-- -------------------------------------------------------------------------
-- Delay simulation
-- -------------------------------------------------------------------------
--
-- This transaction demonstrates how a duration change can be evaluated
-- without permanently modifying the production schedule.

BEGIN;

SELECT
    activity_code,
    activity_name,
    duration
FROM activity
WHERE activity_code = 'API'
FOR UPDATE;

UPDATE activity
SET duration = duration + 2
WHERE activity_code = 'API';

SELECT
    activity_code,
    activity_name,
    duration
FROM activity_earliest_schedule
ORDER BY earliest_finish DESC;

ROLLBACK;

-- -------------------------------------------------------------------------
-- Query the activities that sit immediately before the project-ending
-- release activity.
-- -------------------------------------------------------------------------

SELECT
    predecessor.activity_code,
    predecessor.activity_name,
    predecessor.duration
FROM activity_dependency dependency
JOIN activity predecessor
    ON predecessor.activity_id =
       dependency.predecessor_activity_id
JOIN activity successor
    ON successor.activity_id =
       dependency.successor_activity_id
WHERE successor.activity_code = 'REL'
ORDER BY predecessor.activity_code;

-- -------------------------------------------------------------------------
-- Identify activities with multiple downstream dependencies.
-- Such activities are important synchronization or convergence points.
-- -------------------------------------------------------------------------

SELECT
    a.activity_code,
    a.activity_name,
    COUNT(d.successor_activity_id) AS successor_count
FROM activity a
LEFT JOIN activity_dependency d
    ON d.predecessor_activity_id = a.activity_id
GROUP BY
    a.activity_id,
    a.activity_code,
    a.activity_name
HAVING COUNT(d.successor_activity_id) > 1
ORDER BY successor_count DESC;

-- -------------------------------------------------------------------------
-- Identify convergence activities.
-- These activities cannot start until multiple predecessor branches
-- have completed and therefore often represent synchronization points.
-- -------------------------------------------------------------------------

SELECT
    a.activity_code,
    a.activity_name,
    COUNT(d.predecessor_activity_id) AS predecessor_count
FROM activity a
JOIN activity_dependency d
    ON d.successor_activity_id = a.activity_id
GROUP BY
    a.activity_id,
    a.activity_code,
    a.activity_name
HAVING COUNT(d.predecessor_activity_id) > 1
ORDER BY predecessor_count DESC;

-- -------------------------------------------------------------------------
-- Operational interpretation
-- -------------------------------------------------------------------------
--
-- A critical activity is not simply an activity with a large duration.
-- Criticality depends on its position in the dependency network and the
-- duration of competing paths.
--
-- Total float is the amount by which an activity can move later without
-- changing the current project completion date. A schedule must be
-- recalculated after duration, dependency, or project-scope changes.
