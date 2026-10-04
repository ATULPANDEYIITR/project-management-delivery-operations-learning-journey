DROP SCHEMA IF EXISTS activity_duration_estimation CASCADE;
CREATE SCHEMA activity_duration_estimation;

SET search_path TO activity_duration_estimation;

-- Activity duration is modeled separately from task sequencing.
-- This allows an estimate to describe uncertainty without confusing it
-- with dependency-driven calendar scheduling.

CREATE TYPE activity_type AS ENUM (
    'analysis',
    'implementation',
    'testing',
    'documentation',
    'integration'
);

CREATE TYPE activity_status AS ENUM (
    'planned',
    'in_progress',
    'completed',
    'cancelled'
);

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    owner_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE activities (
    activity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    activity_name TEXT NOT NULL,
    activity_type activity_type NOT NULL,
    status activity_status NOT NULL DEFAULT 'planned',
    optimistic_hours NUMERIC(10,2) NOT NULL,
    most_likely_hours NUMERIC(10,2) NOT NULL,
    pessimistic_hours NUMERIC(10,2) NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    CONSTRAINT activity_name_not_blank
        CHECK (length(trim(activity_name)) > 0),

    CONSTRAINT optimistic_nonnegative
        CHECK (optimistic_hours >= 0),

    CONSTRAINT most_likely_nonnegative
        CHECK (most_likely_hours >= 0),

    CONSTRAINT pessimistic_nonnegative
        CHECK (pessimistic_hours >= 0),

    CONSTRAINT valid_three_point_estimate
        CHECK (
            optimistic_hours <= most_likely_hours
            AND most_likely_hours <= pessimistic_hours
        ),

    CONSTRAINT valid_completion_timestamps
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        ),

    CONSTRAINT activity_unique_per_repository
        UNIQUE (repository_id, activity_name)
);

-- A dependency is a directed edge:
-- dependent_activity_id cannot start until prerequisite_activity_id finishes.
CREATE TABLE activity_dependencies (
    dependent_activity_id BIGINT NOT NULL
        REFERENCES activities(activity_id)
        ON DELETE CASCADE,
    prerequisite_activity_id BIGINT NOT NULL
        REFERENCES activities(activity_id)
        ON DELETE CASCADE,

    PRIMARY KEY (
        dependent_activity_id,
        prerequisite_activity_id
    ),

    CONSTRAINT no_self_dependency
        CHECK (
            dependent_activity_id <> prerequisite_activity_id
        )
);

CREATE TABLE historical_duration_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT
        REFERENCES repositories(repository_id)
        ON DELETE SET NULL,
    activity_type activity_type NOT NULL,
    estimated_hours NUMERIC(10,2) NOT NULL,
    actual_hours NUMERIC(10,2) NOT NULL,
    completed_at DATE NOT NULL,

    CONSTRAINT historical_estimate_positive
        CHECK (estimated_hours > 0),

    CONSTRAINT historical_actual_nonnegative
        CHECK (actual_hours >= 0)
);

CREATE INDEX idx_activity_repository
    ON activities(repository_id);

CREATE INDEX idx_activity_status
    ON activities(status);

CREATE INDEX idx_dependency_prerequisite
    ON activity_dependencies(prerequisite_activity_id);

CREATE INDEX idx_history_type
    ON historical_duration_observations(activity_type);

INSERT INTO repositories (repository_name, owner_name)
VALUES
    ('repository-governance-engine', 'engineering'),
    ('market-data-service', 'platform');

INSERT INTO activities (
    repository_id,
    activity_name,
    activity_type,
    optimistic_hours,
    most_likely_hours,
    pessimistic_hours
)
SELECT
    r.repository_id,
    v.activity_name,
    v.activity_type::activity_type,
    v.optimistic_hours,
    v.most_likely_hours,
    v.pessimistic_hours
FROM repositories r
JOIN (
    VALUES
        (
            'repository-governance-engine',
            'Requirements analysis',
            'analysis',
            3.00, 5.00, 9.00
        ),
        (
            'repository-governance-engine',
            'Backend implementation',
            'implementation',
            12.00, 18.00, 30.00
        ),
        (
            'repository-governance-engine',
            'Frontend implementation',
            'implementation',
            10.00, 15.00, 26.00
        ),
        (
            'repository-governance-engine',
            'Backend verification',
            'testing',
            5.00, 8.00, 15.00
        ),
        (
            'repository-governance-engine',
            'Frontend verification',
            'testing',
            4.00, 7.00, 13.00
        ),
        (
            'repository-governance-engine',
            'System integration',
            'integration',
            6.00, 10.00, 18.00
        ),
        (
            'market-data-service',
            'Data contract analysis',
            'analysis',
            4.00, 7.00, 12.00
        )
) AS v(
    repository_name,
    activity_name,
    activity_type,
    optimistic_hours,
    most_likely_hours,
    pessimistic_hours
)
ON r.repository_name = v.repository_name;

INSERT INTO activity_dependencies (
    dependent_activity_id,
    prerequisite_activity_id
)
SELECT
    dependent.activity_id,
    prerequisite.activity_id
FROM activities dependent
JOIN activities prerequisite
    ON (
        (dependent.activity_name = 'Backend implementation'
         AND prerequisite.activity_name = 'Requirements analysis')
        OR
        (dependent.activity_name = 'Frontend implementation'
         AND prerequisite.activity_name = 'Requirements analysis')
        OR
        (dependent.activity_name = 'Backend verification'
         AND prerequisite.activity_name = 'Backend implementation')
        OR
        (dependent.activity_name = 'Frontend verification'
         AND prerequisite.activity_name = 'Frontend implementation')
        OR
        (dependent.activity_name = 'System integration'
         AND prerequisite.activity_name IN (
             'Backend verification',
             'Frontend verification'
         ))
    )
WHERE dependent.repository_id = (
    SELECT repository_id
    FROM repositories
    WHERE repository_name = 'repository-governance-engine'
);

INSERT INTO historical_duration_observations (
    repository_id,
    activity_type,
    estimated_hours,
    actual_hours,
    completed_at
)
SELECT
    r.repository_id,
    v.activity_type::activity_type,
    v.estimated_hours,
    v.actual_hours,
    v.completed_at::DATE
FROM repositories r
JOIN (
    VALUES
        ('repository-governance-engine', 'analysis', 6.00, 8.00, '2026-08-01'),
        ('repository-governance-engine', 'analysis', 10.00, 11.00, '2026-08-07'),
        ('repository-governance-engine', 'implementation', 14.00, 19.00, '2026-08-15'),
        ('repository-governance-engine', 'implementation', 20.00, 24.00, '2026-08-22'),
        ('repository-governance-engine', 'testing', 10.00, 9.00, '2026-08-27'),
        ('repository-governance-engine', 'testing', 15.00, 18.00, '2026-09-03'),
        ('market-data-service', 'integration', 9.00, 13.00, '2026-09-10'),
        ('market-data-service', 'integration', 12.00, 16.00, '2026-09-18')
) AS v(
    repository_name,
    activity_type,
    estimated_hours,
    actual_hours,
    completed_at
)
ON r.repository_name = v.repository_name;

-- PERT expected duration is calculated at query time so source estimates
-- remain auditable and the derived value cannot become stale.
CREATE VIEW activity_duration_estimates AS
SELECT
    a.activity_id,
    r.repository_name,
    a.activity_name,
    a.activity_type,
    a.status,
    a.optimistic_hours,
    a.most_likely_hours,
    a.pessimistic_hours,
    ROUND(
        (
            a.optimistic_hours
            + 4 * a.most_likely_hours
            + a.pessimistic_hours
        ) / 6.0,
        2
    ) AS pert_expected_hours,
    ROUND(
        (
            a.pessimistic_hours - a.optimistic_hours
        ) / 6.0,
        2
    ) AS pert_standard_deviation_hours
FROM activities a
JOIN repositories r
    ON r.repository_id = a.repository_id;

-- Historical calibration factor measures whether completed activities
-- systematically took more or less time than originally estimated.
CREATE VIEW historical_calibration AS
SELECT
    activity_type,
    COUNT(*) AS observations,
    ROUND(SUM(actual_hours) / SUM(estimated_hours), 3)
        AS actual_to_estimated_factor,
    ROUND(AVG(actual_hours - estimated_hours), 2)
        AS average_signed_error_hours,
    ROUND(
        AVG(ABS(actual_hours - estimated_hours)),
        2
    ) AS mean_absolute_error_hours
FROM historical_duration_observations
GROUP BY activity_type;

-- A task-specific calibrated estimate uses historical behavior from the
-- same activity category. This is intentionally different from the raw
-- three-point estimate.
CREATE VIEW calibrated_activity_estimates AS
SELECT
    e.activity_id,
    e.repository_name,
    e.activity_name,
    e.activity_type,
    e.pert_expected_hours,
    h.actual_to_estimated_factor,
    ROUND(
        e.pert_expected_hours *
        COALESCE(h.actual_to_estimated_factor, 1.0),
        2
    ) AS calibrated_expected_hours
FROM activity_duration_estimates e
LEFT JOIN historical_calibration h
    ON h.activity_type = e.activity_type;

-- Identify activities whose uncertainty range is unusually wide.
-- A wide range is an estimation-risk signal rather than a duration itself.
SELECT
    repository_name,
    activity_name,
    optimistic_hours,
    most_likely_hours,
    pessimistic_hours,
    ROUND(
        pessimistic_hours - optimistic_hours,
        2
    ) AS uncertainty_span_hours
FROM activity_duration_estimates
ORDER BY uncertainty_span_hours DESC;

-- Measure historical bias. A positive signed error means actual duration
-- exceeded the original estimate.
SELECT
    ROUND(AVG(actual_hours - estimated_hours), 2)
        AS signed_bias_hours,
    ROUND(
        AVG(
            ABS(actual_hours - estimated_hours)
        ),
        2
    ) AS mean_absolute_error_hours,
    ROUND(
        AVG(
            CASE
                WHEN estimated_hours > 0
                THEN ABS(actual_hours - estimated_hours)
                     / estimated_hours * 100
            END
        ),
        2
    ) AS mean_absolute_percentage_error
FROM historical_duration_observations;

-- Activities ready to begin are those with no unfinished prerequisites.
-- This query evaluates scheduling eligibility, not the duration estimate.
SELECT
    a.activity_id,
    a.activity_name,
    a.status
FROM activities a
WHERE a.status = 'planned'
  AND NOT EXISTS (
      SELECT 1
      FROM activity_dependencies d
      JOIN activities prerequisite
        ON prerequisite.activity_id = d.prerequisite_activity_id
      WHERE d.dependent_activity_id = a.activity_id
        AND prerequisite.status <> 'completed'
  );

-- Calculate the expected finish position of each activity using a recursive
-- CTE. PostgreSQL recursion is used because dependency depth is not fixed.
WITH RECURSIVE dependency_paths AS (
    SELECT
        a.activity_id,
        a.activity_name,
        a.repository_id,
        0 AS dependency_depth
    FROM activities a
    WHERE NOT EXISTS (
        SELECT 1
        FROM activity_dependencies d
        WHERE d.dependent_activity_id = a.activity_id
    )

    UNION ALL

    SELECT
        dependent.activity_id,
        dependent.activity_name,
        dependent.repository_id,
        dp.dependency_depth + 1
    FROM dependency_paths dp
    JOIN activity_dependencies d
        ON d.prerequisite_activity_id = dp.activity_id
    JOIN activities dependent
        ON dependent.activity_id = d.dependent_activity_id
)
SELECT
    activity_id,
    activity_name,
    MAX(dependency_depth) AS dependency_depth
FROM dependency_paths
GROUP BY activity_id, activity_name
ORDER BY dependency_depth, activity_name;

-- Database-level integrity test.
-- The transaction demonstrates that an invalid negative duration is rejected
-- by the CHECK constraint and the failed insert does not become persistent.
BEGIN;

DO $$
BEGIN
    BEGIN
        INSERT INTO activities (
            repository_id,
            activity_name,
            activity_type,
            optimistic_hours,
            most_likely_hours,
            pessimistic_hours
        )
        VALUES (
            (
                SELECT repository_id
                FROM repositories
                WHERE repository_name = 'repository-governance-engine'
            ),
            'Invalid negative duration example',
            'implementation',
            -1,
            4,
            8
        );
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'Database correctly rejected a negative duration.';
    END;
END
$$;

ROLLBACK;

-- A transactional status update demonstrates that an activity's lifecycle
-- can be persisted atomically with its completion timestamp.
BEGIN;

UPDATE activities
SET
    status = 'in_progress',
    started_at = CURRENT_TIMESTAMP
WHERE activity_name = 'Backend implementation'
  AND repository_id = (
      SELECT repository_id
      FROM repositories
      WHERE repository_name = 'repository-governance-engine'
  )
  AND status = 'planned';

UPDATE activities
SET
    status = 'completed',
    completed_at = CURRENT_TIMESTAMP
WHERE activity_name = 'Backend implementation'
  AND repository_id = (
      SELECT repository_id
      FROM repositories
      WHERE repository_name = 'repository-governance-engine'
  )
  AND status = 'in_progress';

COMMIT;

-- Final audit query: raw estimates, calibrated estimates, and completion
-- state can be compared without modifying the source estimates.
SELECT
    repository_name,
    activity_name,
    activity_type,
    status,
    pert_expected_hours,
    calibrated_expected_hours
FROM calibrated_activity_estimates c
JOIN activities a
    ON a.activity_id = c.activity_id
ORDER BY repository_name, activity_name;
