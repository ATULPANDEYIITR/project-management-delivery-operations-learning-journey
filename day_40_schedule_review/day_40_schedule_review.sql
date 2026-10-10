DROP SCHEMA IF EXISTS schedule_review CASCADE;

CREATE SCHEMA schedule_review;

SET search_path = schedule_review, public;

-- PostgreSQL is used because date arithmetic, generated expressions,
-- partial indexes, constraints, and transactional behavior are useful
-- for schedule-review workloads.

CREATE TYPE task_status AS ENUM (
    'planned',
    'in_progress',
    'complete',
    'blocked'
);

CREATE TYPE review_decision AS ENUM (
    'accept',
    'revise',
    'escalate'
);

CREATE TABLE resource (
    resource_id BIGSERIAL PRIMARY KEY,
    resource_name TEXT NOT NULL UNIQUE,
    weekly_capacity_hours NUMERIC(8,2) NOT NULL
        CHECK (weekly_capacity_hours >= 0)
);

CREATE TABLE schedule (
    schedule_id BIGSERIAL PRIMARY KEY,
    schedule_name TEXT NOT NULL,
    review_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE schedule_task (
    task_id BIGSERIAL PRIMARY KEY,
    schedule_id BIGINT NOT NULL
        REFERENCES schedule(schedule_id)
        ON DELETE CASCADE,
    task_code TEXT NOT NULL,
    task_name TEXT NOT NULL,
    resource_id BIGINT NOT NULL
        REFERENCES resource(resource_id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    planned_hours NUMERIC(10,2) NOT NULL
        CHECK (planned_hours >= 0),
    actual_hours NUMERIC(10,2) NOT NULL DEFAULT 0
        CHECK (actual_hours >= 0),
    progress_percent NUMERIC(5,2) NOT NULL DEFAULT 0
        CHECK (progress_percent BETWEEN 0 AND 100),
    status task_status NOT NULL DEFAULT 'planned',
    priority TEXT NOT NULL DEFAULT 'normal',
    UNIQUE(schedule_id, task_code),
    CHECK (end_date >= start_date)
);

CREATE TABLE task_dependency (
    predecessor_task_id BIGINT NOT NULL
        REFERENCES schedule_task(task_id)
        ON DELETE CASCADE,
    successor_task_id BIGINT NOT NULL
        REFERENCES schedule_task(task_id)
        ON DELETE CASCADE,
    PRIMARY KEY (predecessor_task_id, successor_task_id),
    CHECK (predecessor_task_id <> successor_task_id)
);

CREATE TABLE schedule_review (
    review_id BIGSERIAL PRIMARY KEY,
    schedule_id BIGINT NOT NULL
        REFERENCES schedule(schedule_id)
        ON DELETE CASCADE,
    decision review_decision NOT NULL,
    reviewer_name TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    findings TEXT NOT NULL DEFAULT ''
);

CREATE TABLE review_finding (
    finding_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES schedule_review(review_id)
        ON DELETE CASCADE,
    finding_type TEXT NOT NULL
        CHECK (
            finding_type IN (
                'dependency',
                'resource_conflict',
                'capacity',
                'progress',
                'cycle'
            )
        ),
    severity TEXT NOT NULL
        CHECK (severity IN ('info', 'warning', 'critical')),
    task_id BIGINT REFERENCES schedule_task(task_id),
    description TEXT NOT NULL
);

CREATE INDEX idx_schedule_task_schedule_dates
    ON schedule_task(schedule_id, start_date, end_date);

CREATE INDEX idx_schedule_task_resource_dates
    ON schedule_task(resource_id, start_date, end_date);

CREATE INDEX idx_dependency_successor
    ON task_dependency(successor_task_id);

CREATE INDEX idx_review_finding_review
    ON review_finding(review_id);

INSERT INTO resource (resource_name, weekly_capacity_hours)
VALUES
    ('Asha', 70.00),
    ('Ravi', 65.00),
    ('Meera', 40.00);

INSERT INTO schedule (schedule_name, review_date)
VALUES ('Enterprise Release Schedule', DATE '2026-10-12');

INSERT INTO schedule_task (
    schedule_id,
    task_code,
    task_name,
    resource_id,
    start_date,
    end_date,
    planned_hours,
    actual_hours,
    progress_percent,
    status,
    priority
)
SELECT
    s.schedule_id,
    x.task_code,
    x.task_name,
    r.resource_id,
    x.start_date,
    x.end_date,
    x.planned_hours,
    x.actual_hours,
    x.progress_percent,
    x.status::task_status,
    x.priority
FROM schedule s
CROSS JOIN (
    VALUES
        (
            'PLAN',
            'Planning baseline',
            'Asha',
            DATE '2026-10-01',
            DATE '2026-10-03',
            18.00,
            18.00,
            100.00,
            'complete',
            'high'
        ),
        (
            'DESIGN',
            'Architecture design',
            'Ravi',
            DATE '2026-10-04',
            DATE '2026-10-06',
            20.00,
            20.00,
            100.00,
            'complete',
            'high'
        ),
        (
            'BUILD',
            'Service implementation',
            'Ravi',
            DATE '2026-10-07',
            DATE '2026-10-12',
            36.00,
            18.00,
            55.00,
            'in_progress',
            'high'
        ),
        (
            'DATA',
            'Schedule data validation',
            'Meera',
            DATE '2026-10-08',
            DATE '2026-10-11',
            24.00,
            14.00,
            70.00,
            'in_progress',
            'normal'
        ),
        (
            'TEST',
            'Integrated testing',
            'Asha',
            DATE '2026-10-13',
            DATE '2026-10-16',
            28.00,
            0.00,
            0.00,
            'planned',
            'high'
        ),
        (
            'RELEASE',
            'Production release',
            'Asha',
            DATE '2026-10-19',
            DATE '2026-10-19',
            8.00,
            0.00,
            0.00,
            'planned',
            'high'
        )
) AS x(
    task_code,
    task_name,
    resource_name,
    start_date,
    end_date,
    planned_hours,
    actual_hours,
    progress_percent,
    status,
    priority
)
JOIN resource r
    ON r.resource_name = x.resource_name;

INSERT INTO task_dependency (
    predecessor_task_id,
    successor_task_id
)
SELECT predecessor.task_id, successor.task_id
FROM (
    VALUES
        ('PLAN', 'DESIGN'),
        ('DESIGN', 'BUILD'),
        ('DESIGN', 'DATA'),
        ('BUILD', 'TEST'),
        ('DATA', 'TEST'),
        ('TEST', 'RELEASE')
) AS dependency(predecessor_code, successor_code)
JOIN schedule_task predecessor
    ON predecessor.task_code = dependency.predecessor_code
JOIN schedule_task successor
    ON successor.task_code = dependency.successor_code;

-- The first review query identifies dependencies whose predecessor finishes
-- after the successor starts. This is a structural schedule error.
SELECT
    successor.task_code AS successor_task,
    predecessor.task_code AS predecessor_task,
    predecessor.end_date AS predecessor_end,
    successor.start_date AS successor_start
FROM task_dependency d
JOIN schedule_task predecessor
    ON predecessor.task_id = d.predecessor_task_id
JOIN schedule_task successor
    ON successor.task_id = d.successor_task_id
WHERE predecessor.end_date > successor.start_date
ORDER BY successor.start_date;

-- Resource overlap is distinct from dependency validity. Two tasks may have
-- perfectly valid dependency relationships while still competing for the
-- same person during overlapping calendar periods.
SELECT
    r.resource_name,
    a.task_code AS task_a,
    b.task_code AS task_b,
    GREATEST(a.start_date, b.start_date) AS overlap_start,
    LEAST(a.end_date, b.end_date) AS overlap_end
FROM schedule_task a
JOIN schedule_task b
    ON a.task_id < b.task_id
   AND a.resource_id = b.resource_id
   AND a.start_date <= b.end_date
   AND b.start_date <= a.end_date
JOIN resource r
    ON r.resource_id = a.resource_id
WHERE a.schedule_id = (
    SELECT schedule_id
    FROM schedule
    WHERE schedule_name = 'Enterprise Release Schedule'
)
ORDER BY r.resource_name, overlap_start;

-- Capacity review aggregates planned effort by resource. The comparison is
-- deliberately separate from calendar overlap because total workload and
-- simultaneous workload are different schedule risks.
WITH workload AS (
    SELECT
        t.resource_id,
        SUM(t.planned_hours) AS planned_hours
    FROM schedule_task t
    GROUP BY t.resource_id
)
SELECT
    r.resource_name,
    w.planned_hours,
    r.weekly_capacity_hours,
    w.planned_hours - r.weekly_capacity_hours AS excess_hours
FROM workload w
JOIN resource r
    ON r.resource_id = w.resource_id
WHERE w.planned_hours > r.weekly_capacity_hours
ORDER BY excess_hours DESC;

-- Progress variance compares expected calendar progress with reported
-- progress. It is not earned-value management and should not be interpreted
-- as cost or schedule performance index.
WITH task_timing AS (
    SELECT
        t.*,
        s.review_date,
        CASE
            WHEN s.review_date < t.start_date THEN 0
            WHEN s.review_date >= t.end_date THEN 100
            ELSE
                (
                    (
                        s.review_date - t.start_date + 1
                    )::NUMERIC
                    /
                    (t.end_date - t.start_date + 1)::NUMERIC
                ) * 100
        END AS expected_progress
    FROM schedule_task t
    JOIN schedule s
        ON s.schedule_id = t.schedule_id
)
SELECT
    task_code,
    task_name,
    ROUND(expected_progress, 2) AS expected_progress,
    progress_percent AS actual_progress,
    ROUND(progress_percent - expected_progress, 2) AS progress_variance
FROM task_timing
ORDER BY start_date;

-- A recursive CTE provides a dependency-path representation. It is useful
-- for exposing upstream schedule relationships before a review decision.
WITH RECURSIVE dependency_paths AS (
    SELECT
        t.task_id,
        t.task_code,
        t.task_code::TEXT AS path,
        1 AS depth
    FROM schedule_task t
    WHERE NOT EXISTS (
        SELECT 1
        FROM task_dependency d
        WHERE d.successor_task_id = t.task_id
    )

    UNION ALL

    SELECT
        child.task_id,
        child.task_code,
        p.path || ' -> ' || child.task_code,
        p.depth + 1
    FROM dependency_paths p
    JOIN task_dependency d
        ON d.predecessor_task_id = p.task_id
    JOIN schedule_task child
        ON child.task_id = d.successor_task_id
    WHERE p.depth < 50
)
SELECT
    task_code,
    path,
    depth
FROM dependency_paths
ORDER BY depth DESC, path;

-- A transaction demonstrates that review evidence and its decision can be
-- persisted atomically. If a later insert fails, both the decision and its
-- findings can be rolled back together.
BEGIN;

WITH review_target AS (
    SELECT schedule_id
    FROM schedule
    WHERE schedule_name = 'Enterprise Release Schedule'
)
INSERT INTO schedule_review (
    schedule_id,
    decision,
    reviewer_name,
    findings
)
SELECT
    schedule_id,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM schedule_task a
            JOIN schedule_task b
                ON a.task_id < b.task_id
               AND a.resource_id = b.resource_id
               AND a.start_date <= b.end_date
               AND b.start_date <= a.end_date
        )
        THEN 'revise'::review_decision
        ELSE 'accept'::review_decision
    END,
    'Schedule Control Office',
    'Automated schedule review evidence recorded.'
FROM review_target;

COMMIT;

-- Capture the current review findings as durable audit records.
INSERT INTO review_finding (
    review_id,
    finding_type,
    severity,
    task_id,
    description
)
SELECT
    sr.review_id,
    'resource_conflict',
    'warning',
    a.task_id,
    format(
        'Resource %s has overlapping tasks %s and %s.',
        r.resource_name,
        a.task_code,
        b.task_code
    )
FROM schedule_review sr
JOIN schedule s
    ON s.schedule_id = sr.schedule_id
JOIN schedule_task a
    ON a.schedule_id = s.schedule_id
JOIN schedule_task b
    ON b.schedule_id = s.schedule_id
   AND a.task_id < b.task_id
   AND a.resource_id = b.resource_id
   AND a.start_date <= b.end_date
   AND b.start_date <= a.end_date
JOIN resource r
    ON r.resource_id = a.resource_id
WHERE sr.review_id = (
    SELECT MAX(review_id)
    FROM schedule_review
);

-- Review history is itself useful schedule data: it permits comparison of
-- decisions across review dates rather than overwriting the previous result.
SELECT
    s.schedule_name,
    sr.review_id,
    sr.decision,
    sr.reviewer_name,
    sr.reviewed_at,
    sr.findings
FROM schedule_review sr
JOIN schedule s
    ON s.schedule_id = sr.schedule_id
ORDER BY sr.reviewed_at DESC;

-- This query gives the schedule-review dashboard a compact operational view.
SELECT
    t.task_code,
    t.task_name,
    r.resource_name,
    t.start_date,
    t.end_date,
    (t.end_date - t.start_date + 1) AS duration_days,
    t.planned_hours,
    t.progress_percent,
    t.status,
    t.priority
FROM schedule_task t
JOIN resource r
    ON r.resource_id = t.resource_id
WHERE t.schedule_id = (
    SELECT schedule_id
    FROM schedule
    WHERE schedule_name = 'Enterprise Release Schedule'
)
ORDER BY t.start_date, t.task_code;
