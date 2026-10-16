DROP SCHEMA IF EXISTS cost_variance CASCADE;

CREATE SCHEMA cost_variance;

SET search_path TO cost_variance;

-- The model separates the approved baseline from actual cost postings.
-- A variance is calculated as actual_cost - planned_cost.
-- PostgreSQL NUMERIC is used instead of floating-point arithmetic because
-- financial amounts require deterministic decimal behavior.

CREATE TYPE variance_status AS ENUM (
    'FAVORABLE',
    'UNFAVORABLE',
    'ON_PLAN'
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    approved_budget NUMERIC(14, 2) NOT NULL
        CHECK (approved_budget >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_categories (
    category_id BIGSERIAL PRIMARY KEY,
    category_code TEXT NOT NULL UNIQUE,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE budget_lines (
    budget_line_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    category_id BIGINT NOT NULL
        REFERENCES cost_categories(category_id),
    planned_cost NUMERIC(14, 2) NOT NULL
        CHECK (planned_cost >= 0),
    UNIQUE (project_id, category_id)
);

CREATE TABLE cost_postings (
    posting_id BIGSERIAL PRIMARY KEY,
    budget_line_id BIGINT NOT NULL
        REFERENCES budget_lines(budget_line_id)
        ON DELETE RESTRICT,
    posting_source TEXT NOT NULL,
    description TEXT NOT NULL,
    actual_cost NUMERIC(14, 2) NOT NULL
        CHECK (actual_cost > 0),
    posted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE variance_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL UNIQUE
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    threshold_percentage NUMERIC(8, 2) NOT NULL
        CHECK (threshold_percentage >= 0)
);

CREATE INDEX idx_budget_lines_project
    ON budget_lines(project_id);

CREATE INDEX idx_cost_postings_budget_line
    ON cost_postings(budget_line_id);

CREATE INDEX idx_cost_postings_posted_at
    ON cost_postings(posted_at);

CREATE INDEX idx_cost_postings_source
    ON cost_postings(posting_source);

INSERT INTO projects (
    project_code,
    project_name,
    approved_budget
)
VALUES
    ('DIGITAL-PLATFORM', 'Digital Platform Modernization', 58500.00),
    ('DATA-QUALITY', 'Operational Data Quality Programme', 42000.00);

INSERT INTO cost_categories (
    category_code,
    category_name
)
VALUES
    ('CLOUD', 'Cloud infrastructure'),
    ('CONTRACT', 'External contractors'),
    ('TEST', 'Testing services'),
    ('SECURITY', 'Security tooling'),
    ('TRAVEL', 'Travel and workshops'),
    ('TRAINING', 'Training'),
    ('DATA', 'Data quality operations');

INSERT INTO budget_lines (
    project_id,
    category_id,
    planned_cost
)
SELECT
    p.project_id,
    c.category_id,
    v.planned_cost
FROM (
    VALUES
        ('DIGITAL-PLATFORM', 'CLOUD', 12000.00::NUMERIC),
        ('DIGITAL-PLATFORM', 'CONTRACT', 30000.00::NUMERIC),
        ('DIGITAL-PLATFORM', 'TEST', 8000.00::NUMERIC),
        ('DIGITAL-PLATFORM', 'SECURITY', 6500.00::NUMERIC),
        ('DIGITAL-PLATFORM', 'TRAVEL', 3500.00::NUMERIC),
        ('DIGITAL-PLATFORM', 'TRAINING', 5000.00::NUMERIC),
        ('DATA-QUALITY', 'DATA', 24000.00::NUMERIC),
        ('DATA-QUALITY', 'SECURITY', 7000.00::NUMERIC),
        ('DATA-QUALITY', 'TRAINING', 6000.00::NUMERIC)
) AS v(project_code, category_code, planned_cost)
JOIN projects p
    ON p.project_code = v.project_code
JOIN cost_categories c
    ON c.category_code = v.category_code;

INSERT INTO variance_policies (
    project_id,
    threshold_percentage
)
SELECT project_id, 10.00
FROM projects
WHERE project_code = 'DIGITAL-PLATFORM';

INSERT INTO variance_policies (
    project_id,
    threshold_percentage
)
SELECT project_id, 8.00
FROM projects
WHERE project_code = 'DATA-QUALITY';

INSERT INTO cost_postings (
    budget_line_id,
    posting_source,
    description,
    actual_cost,
    posted_at
)
SELECT
    bl.budget_line_id,
    v.posting_source,
    v.description,
    v.actual_cost,
    v.posted_at
FROM (
    VALUES
        ('DIGITAL-PLATFORM', 'CLOUD', 'cloud-metering',
         'Compute and storage usage', 13800.00::NUMERIC,
         '2026-10-03 10:00:00+05:30'::TIMESTAMPTZ),

        ('DIGITAL-PLATFORM', 'CONTRACT', 'accounts-payable',
         'Monthly contractor invoice', 28750.00::NUMERIC,
         '2026-10-04 11:00:00+05:30'::TIMESTAMPTZ),

        ('DIGITAL-PLATFORM', 'TEST', 'test-vendor',
         'Performance and resilience testing', 9200.00::NUMERIC,
         '2026-10-06 09:30:00+05:30'::TIMESTAMPTZ),

        ('DIGITAL-PLATFORM', 'SECURITY', 'procurement',
         'Security platform subscription', 6100.00::NUMERIC,
         '2026-10-07 15:00:00+05:30'::TIMESTAMPTZ),

        ('DIGITAL-PLATFORM', 'TRAVEL', 'expense-system',
         'Project workshops', 4200.00::NUMERIC,
         '2026-10-08 17:30:00+05:30'::TIMESTAMPTZ),

        ('DIGITAL-PLATFORM', 'TRAINING', 'learning-system',
         'Technical training', 4750.00::NUMERIC,
         '2026-10-09 14:00:00+05:30'::TIMESTAMPTZ),

        ('DATA-QUALITY', 'DATA', 'data-vendor',
         'Data remediation services', 25800.00::NUMERIC,
         '2026-10-05 12:00:00+05:30'::TIMESTAMPTZ),

        ('DATA-QUALITY', 'SECURITY', 'procurement',
         'Security monitoring', 6800.00::NUMERIC,
         '2026-10-07 13:00:00+05:30'::TIMESTAMPTZ),

        ('DATA-QUALITY', 'TRAINING', 'learning-system',
         'Analyst training', 7200.00::NUMERIC,
         '2026-10-10 16:00:00+05:30'::TIMESTAMPTZ)
) AS v(
    project_code,
    category_code,
    posting_source,
    description,
    actual_cost,
    posted_at
)
JOIN projects p
    ON p.project_code = v.project_code
JOIN cost_categories c
    ON c.category_code = v.category_code
JOIN budget_lines bl
    ON bl.project_id = p.project_id
   AND bl.category_id = c.category_id;

CREATE VIEW v_cost_variance AS
SELECT
    p.project_code,
    p.project_name,
    c.category_code,
    c.category_name,
    bl.budget_line_id,
    bl.planned_cost,
    COALESCE(SUM(cp.actual_cost), 0.00)::NUMERIC(14, 2) AS actual_cost,
    (
        COALESCE(SUM(cp.actual_cost), 0.00) - bl.planned_cost
    )::NUMERIC(14, 2) AS variance,
    CASE
        WHEN bl.planned_cost = 0 THEN NULL
        ELSE ROUND(
            (
                (
                    COALESCE(SUM(cp.actual_cost), 0.00)
                    - bl.planned_cost
                ) / bl.planned_cost
            ) * 100,
            2
        )
    END AS variance_percentage,
    CASE
        WHEN COALESCE(SUM(cp.actual_cost), 0.00) > bl.planned_cost
            THEN 'UNFAVORABLE'::variance_status
        WHEN COALESCE(SUM(cp.actual_cost), 0.00) < bl.planned_cost
            THEN 'FAVORABLE'::variance_status
        ELSE 'ON_PLAN'::variance_status
    END AS status
FROM projects p
JOIN budget_lines bl
    ON bl.project_id = p.project_id
JOIN cost_categories c
    ON c.category_id = bl.category_id
LEFT JOIN cost_postings cp
    ON cp.budget_line_id = bl.budget_line_id
GROUP BY
    p.project_code,
    p.project_name,
    c.category_code,
    c.category_name,
    bl.budget_line_id,
    bl.planned_cost;

-- Category-level variance identifies where spending is exceeding or
-- remaining below the approved baseline.
SELECT
    project_code,
    category_name,
    planned_cost,
    actual_cost,
    variance,
    variance_percentage,
    status
FROM v_cost_variance
ORDER BY project_code, ABS(variance) DESC;

-- Project-level aggregation shows whether favorable offsets compensate
-- for unfavorable individual cost lines.
SELECT
    project_code,
    MAX(project_name) AS project_name,
    SUM(planned_cost)::NUMERIC(14, 2) AS planned_total,
    SUM(actual_cost)::NUMERIC(14, 2) AS actual_total,
    SUM(variance)::NUMERIC(14, 2) AS total_variance,
    CASE
        WHEN SUM(planned_cost) = 0 THEN NULL
        ELSE ROUND(
            (SUM(variance) / SUM(planned_cost)) * 100,
            2
        )
    END AS total_variance_percentage
FROM v_cost_variance
GROUP BY project_code
ORDER BY project_code;

-- This query identifies material variances using the project-specific
-- investigation threshold rather than applying one global threshold.
SELECT
    cv.project_code,
    cv.category_name,
    cv.variance,
    cv.variance_percentage,
    vp.threshold_percentage,
    cv.status
FROM v_cost_variance cv
JOIN projects p
    ON p.project_code = cv.project_code
JOIN variance_policies vp
    ON vp.project_id = p.project_id
WHERE cv.variance_percentage IS NOT NULL
  AND ABS(cv.variance_percentage) > vp.threshold_percentage
ORDER BY ABS(cv.variance_percentage) DESC;

-- Favorable and unfavorable totals show the difference between
-- gross cost pressure and the net project variance.
SELECT
    project_code,
    SUM(
        CASE WHEN variance > 0 THEN variance ELSE 0 END
    )::NUMERIC(14, 2) AS unfavorable_amount,
    SUM(
        CASE WHEN variance < 0 THEN ABS(variance) ELSE 0 END
    )::NUMERIC(14, 2) AS favorable_amount,
    SUM(variance)::NUMERIC(14, 2) AS net_variance
FROM v_cost_variance
GROUP BY project_code
ORDER BY project_code;

-- Actual postings can be audited back to their source and description.
SELECT
    p.project_code,
    c.category_name,
    cp.posting_source,
    cp.description,
    cp.actual_cost,
    cp.posted_at
FROM cost_postings cp
JOIN budget_lines bl
    ON bl.budget_line_id = cp.budget_line_id
JOIN projects p
    ON p.project_id = bl.project_id
JOIN cost_categories c
    ON c.category_id = bl.category_id
ORDER BY cp.posted_at;

-- PostgreSQL transaction demonstrates atomic insertion of an actual
-- posting. If validation or the insert fails, the transaction can be
-- rolled back without leaving a partial cost record.
BEGIN;

INSERT INTO cost_postings (
    budget_line_id,
    posting_source,
    description,
    actual_cost
)
SELECT
    bl.budget_line_id,
    'cloud-metering',
    'Additional verified usage',
    350.00
FROM budget_lines bl
JOIN projects p
    ON p.project_id = bl.project_id
JOIN cost_categories c
    ON c.category_id = bl.category_id
WHERE p.project_code = 'DIGITAL-PLATFORM'
  AND c.category_code = 'CLOUD';

COMMIT;

-- Integrity enforcement example:
-- The following statement is intentionally not executed because the
-- CHECK constraint must reject a non-positive actual posting.
-- INSERT INTO cost_postings
--     (budget_line_id, posting_source, description, actual_cost)
-- VALUES
--     (1, 'manual-entry', 'Invalid zero cost', 0.00);

-- A zero planned amount has no meaningful percentage variance.
-- The amount-based variance remains valid and can be reported separately.
INSERT INTO projects (
    project_code,
    project_name,
    approved_budget
)
VALUES
    ('EMERGENCY-OPS', 'Unplanned Emergency Operations', 0.00);

INSERT INTO cost_categories (
    category_code,
    category_name
)
VALUES
    ('EMERGENCY', 'Unplanned emergency work');

INSERT INTO budget_lines (
    project_id,
    category_id,
    planned_cost
)
SELECT
    p.project_id,
    c.category_id,
    0.00
FROM projects p
CROSS JOIN cost_categories c
WHERE p.project_code = 'EMERGENCY-OPS'
  AND c.category_code = 'EMERGENCY';

INSERT INTO cost_postings (
    budget_line_id,
    posting_source,
    description,
    actual_cost
)
SELECT
    bl.budget_line_id,
    'operations',
    'Emergency infrastructure repair',
    250.00
FROM budget_lines bl
JOIN projects p
    ON p.project_id = bl.project_id
JOIN cost_categories c
    ON c.category_id = bl.category_id
WHERE p.project_code = 'EMERGENCY-OPS'
  AND c.category_code = 'EMERGENCY';

SELECT
    project_code,
    category_name,
    planned_cost,
    actual_cost,
    variance,
    variance_percentage,
    status
FROM v_cost_variance
WHERE project_code = 'EMERGENCY-OPS';
