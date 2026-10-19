DROP SCHEMA IF EXISTS resource_availability_demo CASCADE;
CREATE SCHEMA resource_availability_demo;
SET search_path TO resource_availability_demo;

-- Resource types are kept relationally so that new resource classes can be
-- introduced without changing the allocation transaction structure.
CREATE TABLE resource_types (
    resource_type_id BIGSERIAL PRIMARY KEY,
    resource_code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE resource_pools (
    resource_pool_id BIGSERIAL PRIMARY KEY,
    resource_type_id BIGINT NOT NULL
        REFERENCES resource_types(resource_type_id),
    pool_name TEXT NOT NULL UNIQUE,
    capacity BIGINT NOT NULL CHECK (capacity > 0),
    available BIGINT NOT NULL CHECK (available >= 0),
    CHECK (available <= capacity)
);

CREATE TABLE resource_consumers (
    consumer_id BIGSERIAL PRIMARY KEY,
    consumer_name TEXT NOT NULL UNIQUE,
    owner_team TEXT NOT NULL
);

CREATE TABLE workloads (
    workload_id BIGSERIAL PRIMARY KEY,
    workload_name TEXT NOT NULL UNIQUE,
    consumer_id BIGINT NOT NULL
        REFERENCES resource_consumers(consumer_id),
    priority SMALLINT NOT NULL
        CHECK (priority BETWEEN 1 AND 100),
    state TEXT NOT NULL
        CHECK (state IN ('queued', 'running', 'completed', 'rejected')),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

CREATE TABLE workload_requirements (
    workload_id BIGINT NOT NULL
        REFERENCES workloads(workload_id)
        ON DELETE CASCADE,
    resource_pool_id BIGINT NOT NULL
        REFERENCES resource_pools(resource_pool_id),
    requested_amount BIGINT NOT NULL CHECK (requested_amount > 0),
    PRIMARY KEY (workload_id, resource_pool_id)
);

CREATE TABLE allocations (
    allocation_id BIGSERIAL PRIMARY KEY,
    workload_id BIGINT NOT NULL
        REFERENCES workloads(workload_id),
    resource_pool_id BIGINT NOT NULL
        REFERENCES resource_pools(resource_pool_id),
    allocated_amount BIGINT NOT NULL CHECK (allocated_amount > 0),
    allocated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMPTZ,
    CHECK (released_at IS NULL OR released_at >= allocated_at)
);

CREATE INDEX idx_workloads_state_priority
    ON workloads (state, priority DESC);

CREATE INDEX idx_requirements_pool
    ON workload_requirements (resource_pool_id);

CREATE INDEX idx_active_allocations_pool
    ON allocations (resource_pool_id)
    WHERE released_at IS NULL;

CREATE INDEX idx_active_allocations_workload
    ON allocations (workload_id)
    WHERE released_at IS NULL;

INSERT INTO resource_types (resource_code, description)
VALUES
    ('compute', 'CPU or worker execution capacity'),
    ('memory', 'RAM capacity'),
    ('storage', 'Persistent storage capacity'),
    ('database_connections', 'Concurrent database connection capacity'),
    ('api_quota', 'External API request quota');

INSERT INTO resource_pools (
    resource_type_id,
    pool_name,
    capacity,
    available
)
SELECT
    resource_type_id,
    CASE resource_code
        WHEN 'compute' THEN 'Application Compute'
        WHEN 'memory' THEN 'Application Memory'
        WHEN 'storage' THEN 'Object Storage'
        WHEN 'database_connections' THEN 'PostgreSQL Connections'
        WHEN 'api_quota' THEN 'External API Quota'
    END,
    CASE resource_code
        WHEN 'compute' THEN 32
        WHEN 'memory' THEN 128
        WHEN 'storage' THEN 5000
        WHEN 'database_connections' THEN 40
        WHEN 'api_quota' THEN 10000
    END,
    CASE resource_code
        WHEN 'compute' THEN 32
        WHEN 'memory' THEN 128
        WHEN 'storage' THEN 5000
        WHEN 'database_connections' THEN 40
        WHEN 'api_quota' THEN 10000
    END
FROM resource_types;

INSERT INTO resource_consumers (consumer_name, owner_team)
VALUES
    ('customer-platform', 'Platform Engineering'),
    ('payments', 'Payment Operations'),
    ('analytics', 'Data Engineering'),
    ('records-team', 'Records Management');

INSERT INTO workloads (
    workload_name,
    consumer_id,
    priority,
    state
)
SELECT
    workload_name,
    consumer_id,
    priority,
    'queued'
FROM (
    VALUES
        ('customer-search', 'customer-platform', 80),
        ('payment-recovery', 'payments', 100),
        ('daily-analytics', 'analytics', 50),
        ('monthly-archive', 'records-team', 20)
) AS input(workload_name, consumer_name, priority)
JOIN resource_consumers
    USING (consumer_name);

INSERT INTO workload_requirements (
    workload_id,
    resource_pool_id,
    requested_amount
)
SELECT
    w.workload_id,
    p.resource_pool_id,
    r.requested_amount
FROM (
    VALUES
        ('customer-search', 'Application Compute', 8),
        ('customer-search', 'Application Memory', 32),
        ('customer-search', 'PostgreSQL Connections', 10),
        ('payment-recovery', 'Application Compute', 10),
        ('payment-recovery', 'Application Memory', 48),
        ('payment-recovery', 'PostgreSQL Connections', 12),
        ('daily-analytics', 'Application Compute', 6),
        ('daily-analytics', 'Application Memory', 24),
        ('monthly-archive', 'Application Compute', 12),
        ('monthly-archive', 'Object Storage', 2000)
) AS r(workload_name, pool_name, requested_amount)
JOIN workloads w
    ON w.workload_name = r.workload_name
JOIN resource_pools p
    ON p.pool_name = r.pool_name;

-- The view exposes current capacity without requiring callers to reconstruct
-- capacity from allocation history.
CREATE VIEW resource_capacity_status AS
SELECT
    p.pool_name,
    rt.resource_code,
    p.capacity,
    p.available,
    p.capacity - p.available AS allocated,
    ROUND(
        ((p.capacity - p.available)::numeric / p.capacity) * 100,
        2
    ) AS utilization_percent
FROM resource_pools p
JOIN resource_types rt
    ON rt.resource_type_id = p.resource_type_id;

-- Capacity-aware workload ranking.
SELECT
    w.workload_name,
    w.priority,
    w.state,
    c.consumer_name,
    SUM(r.requested_amount) AS total_requested_units
FROM workloads w
JOIN resource_consumers c
    ON c.consumer_id = w.consumer_id
JOIN workload_requirements r
    ON r.workload_id = w.workload_id
GROUP BY
    w.workload_id,
    w.workload_name,
    w.priority,
    w.state,
    c.consumer_name
ORDER BY
    w.priority DESC,
    w.workload_name;

-- This transaction admits payment-recovery only when every required pool has
-- enough capacity. SELECT ... FOR UPDATE serializes competing allocators
-- against the same resource rows.
BEGIN;

WITH requested AS (
    SELECT
        wr.resource_pool_id,
        SUM(wr.requested_amount) AS required_amount
    FROM workload_requirements wr
    JOIN workloads w
        ON w.workload_id = wr.workload_id
    WHERE w.workload_name = 'payment-recovery'
      AND w.state = 'queued'
    GROUP BY wr.resource_pool_id
),
locked_pools AS (
    SELECT
        p.resource_pool_id,
        p.available,
        r.required_amount
    FROM resource_pools p
    JOIN requested r
        ON r.resource_pool_id = p.resource_pool_id
    FOR UPDATE OF p
),
capacity_check AS (
    SELECT COUNT(*) AS required_pools,
           COUNT(*) FILTER (
               WHERE available >= required_amount
           ) AS sufficient_pools
    FROM locked_pools
)
SELECT *
FROM capacity_check;

-- The transaction below performs the actual admission after the preceding
-- capacity check has been evaluated. In an application, the transaction
-- should commit only when sufficient_pools equals required_pools.
WITH target AS (
    SELECT w.workload_id
    FROM workloads w
    WHERE w.workload_name = 'payment-recovery'
      AND w.state = 'queued'
),
requirements AS (
    SELECT
        wr.resource_pool_id,
        wr.requested_amount
    FROM workload_requirements wr
    JOIN target t
        ON t.workload_id = wr.workload_id
)
UPDATE resource_pools p
SET available = available - r.requested_amount
FROM requirements r
WHERE p.resource_pool_id = r.resource_pool_id
  AND p.available >= r.requested_amount;

WITH target AS (
    SELECT workload_id
    FROM workloads
    WHERE workload_name = 'payment-recovery'
      AND state = 'queued'
)
INSERT INTO allocations (
    workload_id,
    resource_pool_id,
    allocated_amount
)
SELECT
    t.workload_id,
    wr.resource_pool_id,
    wr.requested_amount
FROM target t
JOIN workload_requirements wr
    ON wr.workload_id = t.workload_id;

UPDATE workloads
SET state = 'running'
WHERE workload_name = 'payment-recovery'
  AND state = 'queued';

COMMIT;

SELECT *
FROM resource_capacity_status
ORDER BY resource_code;

-- Workloads that cannot currently be admitted can be exposed through a
-- query rather than silently discarded.
SELECT
    w.workload_name,
    rt.resource_code,
    p.available,
    SUM(wr.requested_amount) AS requested,
    p.available - SUM(wr.requested_amount) AS capacity_gap
FROM workloads w
JOIN workload_requirements wr
    ON wr.workload_id = w.workload_id
JOIN resource_pools p
    ON p.resource_pool_id = wr.resource_pool_id
JOIN resource_types rt
    ON rt.resource_type_id = p.resource_type_id
WHERE w.state = 'queued'
GROUP BY
    w.workload_name,
    rt.resource_code,
    p.available
HAVING p.available < SUM(wr.requested_amount)
ORDER BY w.priority DESC NULLS LAST;

-- Completion releases all active allocations for a workload atomically.
BEGIN;

WITH target AS (
    SELECT workload_id
    FROM workloads
    WHERE workload_name = 'payment-recovery'
      AND state = 'running'
    FOR UPDATE
),
released AS (
    UPDATE allocations a
    SET released_at = CURRENT_TIMESTAMP
    FROM target t
    WHERE a.workload_id = t.workload_id
      AND a.released_at IS NULL
    RETURNING a.resource_pool_id, a.allocated_amount
),
pool_totals AS (
    SELECT
        resource_pool_id,
        SUM(allocated_amount) AS amount
    FROM released
    GROUP BY resource_pool_id
)
UPDATE resource_pools p
SET available = p.available + t.amount
FROM pool_totals t
WHERE p.resource_pool_id = t.resource_pool_id;

UPDATE workloads
SET
    state = 'completed',
    completed_at = CURRENT_TIMESTAMP
WHERE workload_name = 'payment-recovery'
  AND state = 'running';

COMMIT;

-- Detects inconsistent capacity if data has been modified outside the
-- allocation workflow. A healthy pool has non-negative available capacity.
SELECT
    pool_name,
    capacity,
    available,
    CASE
        WHEN available < 0 THEN 'INVALID_NEGATIVE_AVAILABILITY'
        WHEN available > capacity THEN 'INVALID_OVER_CAPACITY'
        ELSE 'VALID'
    END AS integrity_state
FROM resource_pools
ORDER BY pool_name;
