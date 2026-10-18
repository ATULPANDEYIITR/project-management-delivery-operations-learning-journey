-- Resource allocation management for a technology operations department.
-- PostgreSQL 15 or later.
--
-- The schema separates resource inventory, task demand, scheduling
-- reservations, and allocation outcomes. Constraints enforce local
-- invariants; a trigger prevents overlapping reservations on one resource.

BEGIN;

DROP SCHEMA IF EXISTS resource_planning CASCADE;
CREATE SCHEMA resource_planning;
SET search_path TO resource_planning, public;

CREATE TYPE resource_kind AS ENUM (
    'compute',
    'database',
    'operations',
    'storage'
);

CREATE TYPE task_status AS ENUM (
    'queued',
    'allocated',
    'running',
    'completed',
    'rejected'
);

CREATE TABLE resources (
    resource_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resource_code     TEXT NOT NULL UNIQUE,
    resource_name     TEXT NOT NULL,
    kind              resource_kind NOT NULL,
    capacity_units    NUMERIC(12,2) NOT NULL CHECK (capacity_units > 0),
    hourly_cost       NUMERIC(12,2) NOT NULL DEFAULT 0
                      CHECK (hourly_cost >= 0),
    tags              TEXT[] NOT NULL DEFAULT '{}',
    enabled           BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE tasks (
    task_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_code         TEXT NOT NULL UNIQUE,
    task_name         TEXT NOT NULL,
    required_kind     resource_kind NOT NULL,
    demand_units      NUMERIC(12,2) NOT NULL CHECK (demand_units > 0),
    duration_hours   NUMERIC(10,2) NOT NULL CHECK (duration_hours > 0),
    priority          INTEGER NOT NULL CHECK (priority >= 0),
    deadline_at       TIMESTAMPTZ,
    status            task_status NOT NULL DEFAULT 'queued',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE task_dependencies (
    task_id             BIGINT NOT NULL REFERENCES tasks(task_id)
                        ON DELETE CASCADE,
    prerequisite_task_id BIGINT NOT NULL REFERENCES tasks(task_id)
                        ON DELETE RESTRICT,
    PRIMARY KEY (task_id, prerequisite_task_id),
    CHECK (task_id <> prerequisite_task_id)
);

CREATE TABLE allocation_plans (
    plan_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_name         TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    planning_status   TEXT NOT NULL DEFAULT 'draft'
                      CHECK (planning_status IN ('draft', 'committed', 'cancelled'))
);

CREATE TABLE allocations (
    allocation_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_id           BIGINT NOT NULL REFERENCES allocation_plans(plan_id)
                      ON DELETE CASCADE,
    task_id           BIGINT NOT NULL REFERENCES tasks(task_id)
                      ON DELETE RESTRICT,
    resource_id       BIGINT NOT NULL REFERENCES resources(resource_id)
                      ON DELETE RESTRICT,
    allocated_units   NUMERIC(12,2) NOT NULL CHECK (allocated_units > 0),
    starts_at         TIMESTAMPTZ NOT NULL,
    ends_at           TIMESTAMPTZ NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (ends_at > starts_at),
    UNIQUE (plan_id, task_id)
);

CREATE TABLE allocation_events (
    event_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_id           BIGINT REFERENCES allocation_plans(plan_id)
                      ON DELETE SET NULL,
    task_id           BIGINT REFERENCES tasks(task_id)
                      ON DELETE SET NULL,
    event_type        TEXT NOT NULL CHECK (
        event_type IN (
            'candidate_evaluated',
            'allocated',
            'rejected',
            'plan_committed',
            'plan_cancelled'
        )
    ),
    details           JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_priority_deadline
    ON tasks (priority DESC, deadline_at ASC)
    WHERE status = 'queued';

CREATE INDEX idx_allocations_resource_time
    ON allocations (resource_id, starts_at, ends_at);

CREATE INDEX idx_allocations_plan
    ON allocations (plan_id);

CREATE INDEX idx_task_dependencies_prerequisite
    ON task_dependencies (prerequisite_task_id);

CREATE INDEX idx_allocation_events_details
    ON allocation_events USING GIN (details);

-- Prevent two allocations from reserving the same resource simultaneously.
-- The exclusion constraint also protects against concurrent transactions.
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE allocations
    ADD CONSTRAINT allocations_no_resource_overlap
    EXCLUDE USING gist (
        resource_id WITH =,
        tstzrange(starts_at, ends_at, '[)') WITH &&
    );

-- Check resource eligibility and dependency timing at insertion or update.
CREATE OR REPLACE FUNCTION validate_allocation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    selected_resource resources%ROWTYPE;
    selected_task tasks%ROWTYPE;
    prerequisite_finish TIMESTAMPTZ;
BEGIN
    SELECT *
    INTO selected_resource
    FROM resources
    WHERE resource_id = NEW.resource_id
    FOR SHARE;

    IF NOT FOUND OR NOT selected_resource.enabled THEN
        RAISE EXCEPTION 'Resource % does not exist or is disabled',
            NEW.resource_id;
    END IF;

    SELECT *
    INTO selected_task
    FROM tasks
    WHERE task_id = NEW.task_id
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Task % does not exist', NEW.task_id;
    END IF;

    IF selected_resource.kind <> selected_task.required_kind THEN
        RAISE EXCEPTION 'Resource type does not match task %',
            selected_task.task_code;
    END IF;

    IF NEW.allocated_units <> selected_task.demand_units THEN
        RAISE EXCEPTION 'Allocation must equal task demand for %',
            selected_task.task_code;
    END IF;

    IF NEW.allocated_units > selected_resource.capacity_units THEN
        RAISE EXCEPTION 'Demand exceeds capacity of resource %',
            selected_resource.resource_code;
    END IF;

    SELECT MAX(a.ends_at)
    INTO prerequisite_finish
    FROM task_dependencies d
    JOIN allocations a
      ON a.task_id = d.prerequisite_task_id
     AND a.plan_id = NEW.plan_id
    WHERE d.task_id = NEW.task_id;

    -- Every declared prerequisite must have an allocation in this plan.
    IF EXISTS (
        SELECT 1
        FROM task_dependencies d
        WHERE d.task_id = NEW.task_id
          AND NOT EXISTS (
              SELECT 1
              FROM allocations a
              WHERE a.plan_id = NEW.plan_id
                AND a.task_id = d.prerequisite_task_id
          )
    ) THEN
        RAISE EXCEPTION 'Task % has an unallocated prerequisite',
            selected_task.task_code;
    END IF;

    IF prerequisite_finish IS NOT NULL
       AND NEW.starts_at < prerequisite_finish THEN
        RAISE EXCEPTION 'Task % starts before its prerequisites finish',
            selected_task.task_code;
    END IF;

    IF selected_task.deadline_at IS NOT NULL
       AND NEW.ends_at > selected_task.deadline_at THEN
        RAISE EXCEPTION 'Task % misses its deadline',
            selected_task.task_code;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_allocation
BEFORE INSERT OR UPDATE ON allocations
FOR EACH ROW
EXECUTE FUNCTION validate_allocation();

CREATE OR REPLACE FUNCTION record_allocation_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO allocation_events (
        plan_id, task_id, event_type, details
    )
    VALUES (
        NEW.plan_id,
        NEW.task_id,
        'allocated',
        jsonb_build_object(
            'resource_id', NEW.resource_id,
            'allocated_units', NEW.allocated_units,
            'starts_at', NEW.starts_at,
            'ends_at', NEW.ends_at
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_allocation_audit
AFTER INSERT ON allocations
FOR EACH ROW
EXECUTE FUNCTION record_allocation_event();

INSERT INTO resources (
    resource_code, resource_name, kind, capacity_units,
    hourly_cost, tags
)
VALUES
    ('GPU-01', 'Machine Learning GPU', 'compute', 16, 18,
     ARRAY['cuda', 'linux']),
    ('CPU-01', 'General Compute Node', 'compute', 8, 6,
     ARRAY['linux']),
    ('DB-01', 'Analytics PostgreSQL Cluster', 'database', 12, 14,
     ARRAY['postgresql', 'backup']),
    ('OPS-01', 'Production Deployment Operator', 'operations', 4, 10,
     ARRAY['production']);

INSERT INTO tasks (
    task_code, task_name, required_kind, demand_units,
    duration_hours, priority, deadline_at
)
VALUES
    ('ETL', 'Prepare analytics data', 'compute', 6, 2, 8,
     '2026-10-20 10:00:00+00'),
    ('TRAIN', 'Train forecasting model', 'compute', 14, 4, 10,
     '2026-10-20 17:00:00+00'),
    ('DB-MIGRATION', 'Migrate analytics database', 'database', 8, 3, 7,
     '2026-10-20 14:00:00+00'),
    ('VERIFY', 'Verify forecasting output', 'compute', 4, 2, 6,
     '2026-10-20 19:00:00+00'),
    ('DEPLOY', 'Deploy production service', 'operations', 3, 2, 10,
     '2026-10-21 08:00:00+00'),
    ('OVERSIZED', 'Run oversized simulation', 'compute', 32, 5, 2,
     '2026-10-22 10:00:00+00');

INSERT INTO task_dependencies (task_id, prerequisite_task_id)
SELECT child.task_id, parent.task_id
FROM (
    VALUES
        ('TRAIN', 'ETL'),
        ('VERIFY', 'TRAIN'),
        ('DEPLOY', 'DB-MIGRATION'),
        ('DEPLOY', 'VERIFY')
) AS dependency(child_code, parent_code)
JOIN tasks child ON child.task_code = dependency.child_code
JOIN tasks parent ON parent.task_code = dependency.parent_code;

INSERT INTO allocation_plans (plan_name)
VALUES ('Analytics Release Allocation');

-- Reserve independent tasks first so their dependency timestamps exist.
-- Every interval uses [start, end) semantics.
INSERT INTO allocations (
    plan_id, task_id, resource_id, allocated_units, starts_at, ends_at
)
SELECT p.plan_id, t.task_id, r.resource_id, t.demand_units,
       '2026-10-20 08:00:00+00', '2026-10-20 10:00:00+00'
FROM allocation_plans p
JOIN tasks t ON t.task_code = 'ETL'
JOIN resources r ON r.resource_code = 'CPU-01'
WHERE p.plan_name = 'Analytics Release Allocation';

INSERT INTO allocations (
    plan_id, task_id, resource_id, allocated_units, starts_at, ends_at
)
SELECT p.plan_id, t.task_id, r.resource_id, t.demand_units,
       '2026-10-20 08:00:00+00', '2026-10-20 11:00:00+00'
FROM allocation_plans p
JOIN tasks t ON t.task_code = 'DB-MIGRATION'
JOIN resources r ON r.resource_code = 'DB-01'
WHERE p.plan_name = 'Analytics Release Allocation';

INSERT INTO allocations (
    plan_id, task_id, resource_id, allocated_units, starts_at, ends_at
)
SELECT p.plan_id, t.task_id, r.resource_id, t.demand_units,
       '2026-10-20 10:00:00+00', '2026-10-20 14:00:00+00'
FROM allocation_plans p
JOIN tasks t ON t.task_code = 'TRAIN'
JOIN resources r ON r.resource_code = 'GPU-01'
WHERE p.plan_name = 'Analytics Release Allocation';

INSERT INTO allocations (
    plan_id, task_id, resource_id, allocated_units, starts_at, ends_at
)
SELECT p.plan_id, t.task_id, r.resource_id, t.demand_units,
       '2026-10-20 14:00:00+00', '2026-10-20 16:00:00+00'
FROM allocation_plans p
JOIN tasks t ON t.task_code = 'VERIFY'
JOIN resources r ON r.resource_code = 'CPU-01'
WHERE p.plan_name = 'Analytics Release Allocation';

INSERT INTO allocations (
    plan_id, task_id, resource_id, allocated_units, starts_at, ends_at
)
SELECT p.plan_id, t.task_id, r.resource_id, t.demand_units,
       '2026-10-20 16:00:00+00', '2026-10-20 18:00:00+00'
FROM allocation_plans p
JOIN tasks t ON t.task_code = 'DEPLOY'
JOIN resources r ON r.resource_code = 'OPS-01'
WHERE p.plan_name = 'Analytics Release Allocation';

-- Update task status based on the committed allocation records.
UPDATE tasks t
SET status = CASE
    WHEN EXISTS (
        SELECT 1 FROM allocations a WHERE a.task_id = t.task_id
    ) THEN 'allocated'::task_status
    ELSE 'rejected'::task_status
END;

UPDATE allocation_plans
SET planning_status = 'committed'
WHERE plan_name = 'Analytics Release Allocation';

INSERT INTO allocation_events (plan_id, event_type, details)
SELECT plan_id, 'plan_committed',
       jsonb_build_object('plan_name', plan_name)
FROM allocation_plans
WHERE plan_name = 'Analytics Release Allocation';

COMMIT;

-- Allocated work, assigned resource, schedule interval, and estimated cost.
SELECT
    p.plan_name,
    t.task_code,
    t.task_name,
    r.resource_code,
    a.allocated_units,
    a.starts_at,
    a.ends_at,
    ROUND(
        EXTRACT(EPOCH FROM (a.ends_at - a.starts_at)) / 3600
        * r.hourly_cost,
        2
    ) AS estimated_cost
FROM allocations a
JOIN allocation_plans p ON p.plan_id = a.plan_id
JOIN tasks t ON t.task_id = a.task_id
JOIN resources r ON r.resource_id = a.resource_id
ORDER BY a.starts_at, t.task_code;

-- Resource utilization within the plan's overall time window.
WITH plan_window AS (
    SELECT
        plan_id,
        MIN(starts_at) AS window_start,
        MAX(ends_at) AS window_end
    FROM allocations
    GROUP BY plan_id
),
resource_busy AS (
    SELECT
        a.plan_id,
        a.resource_id,
        SUM(EXTRACT(EPOCH FROM (a.ends_at - a.starts_at)) / 3600)
            AS busy_hours
    FROM allocations a
    GROUP BY a.plan_id, a.resource_id
)
SELECT
    p.plan_name,
    r.resource_code,
    COALESCE(b.busy_hours, 0) AS busy_hours,
    ROUND(
        100.0 * COALESCE(b.busy_hours, 0)
        / NULLIF(
            EXTRACT(EPOCH FROM (w.window_end - w.window_start)) / 3600,
            0
        ),
        2
    ) AS utilization_percentage
FROM allocation_plans p
JOIN plan_window w ON w.plan_id = p.plan_id
CROSS JOIN resources r
LEFT JOIN resource_busy b
    ON b.plan_id = p.plan_id
   AND b.resource_id = r.resource_id
WHERE p.plan_name = 'Analytics Release Allocation'
ORDER BY r.resource_code;

-- Unallocated tasks and a first-pass compatibility diagnosis.
SELECT
    t.task_code,
    t.task_name,
    t.priority,
    CASE
        WHEN NOT EXISTS (
            SELECT 1
            FROM resources r
            WHERE r.enabled
              AND r.kind = t.required_kind
              AND r.capacity_units >= t.demand_units
        )
        THEN 'No enabled resource has the required type and capacity'
        ELSE 'Requires scheduling or dependency analysis'
    END AS allocation_diagnosis
FROM tasks t
WHERE NOT EXISTS (
    SELECT 1
    FROM allocations a
    WHERE a.task_id = t.task_id
)
ORDER BY t.priority DESC, t.task_code;

-- Audit history for allocations and planning outcomes.
SELECT event_type, details, recorded_at
FROM allocation_events
ORDER BY recorded_at, event_id;

-- Capacity is a per-task demand limit in this model. Resources are reserved
-- exclusively over each interval. For divisible resources, multi-tenant
-- concurrency, or time-varying capacity, model usage per interval and enforce
-- aggregate capacity across concurrent allocations.
