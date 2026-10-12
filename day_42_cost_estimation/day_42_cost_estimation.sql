DROP SCHEMA IF EXISTS project_cost_estimation CASCADE;

CREATE SCHEMA project_cost_estimation;

SET search_path TO project_cost_estimation;

CREATE TYPE project_status AS ENUM (
    'draft',
    'estimated',
    'approved',
    'in_progress',
    'forecasting',
    'closed'
);

CREATE TYPE cost_category AS ENUM (
    'labor',
    'infrastructure',
    'security',
    'training',
    'external'
);

CREATE TYPE risk_status AS ENUM (
    'open',
    'mitigated',
    'occurred',
    'closed'
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    approved_budget NUMERIC(14,2) NOT NULL CHECK (approved_budget >= 0),
    reserve_rate NUMERIC(6,5) NOT NULL DEFAULT 0.05000
        CHECK (reserve_rate >= 0 AND reserve_rate <= 1),
    status project_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_items (
    cost_item_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    description TEXT NOT NULL,
    category cost_category NOT NULL,
    quantity NUMERIC(14,3) NOT NULL CHECK (quantity >= 0),
    unit_cost NUMERIC(14,2) NOT NULL CHECK (unit_cost >= 0),
    confidence NUMERIC(5,4) NOT NULL DEFAULT 0.80
        CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, description)
);

CREATE TABLE project_risks (
    risk_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    risk_name TEXT NOT NULL,
    probability NUMERIC(6,5) NOT NULL
        CHECK (probability >= 0 AND probability <= 1),
    impact NUMERIC(14,2) NOT NULL CHECK (impact >= 0),
    status risk_status NOT NULL DEFAULT 'open',
    UNIQUE(project_id, risk_name)
);

CREATE TABLE actual_costs (
    actual_cost_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    cost_date DATE NOT NULL,
    category cost_category NOT NULL,
    description TEXT NOT NULL,
    amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0)
);

CREATE TABLE monthly_forecasts (
    forecast_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    forecast_month DATE NOT NULL,
    forecast_amount NUMERIC(14,2) NOT NULL CHECK (forecast_amount >= 0),
    UNIQUE(project_id, forecast_month)
);

CREATE INDEX idx_cost_items_project_category
    ON cost_items(project_id, category);

CREATE INDEX idx_project_risks_project_status
    ON project_risks(project_id, status);

CREATE INDEX idx_actual_costs_project_date
    ON actual_costs(project_id, cost_date);

CREATE INDEX idx_forecasts_project_month
    ON monthly_forecasts(project_id, forecast_month);

INSERT INTO projects (
    project_code,
    project_name,
    approved_budget,
    reserve_rate,
    status
)
VALUES (
    'PIM-2026',
    'Public Infrastructure Monitoring Platform',
    200000.00,
    0.05000,
    'approved'
);

INSERT INTO cost_items (
    project_id,
    description,
    category,
    quantity,
    unit_cost,
    confidence
)
SELECT
    project_id,
    source.description,
    source.category,
    source.quantity,
    source.unit_cost,
    source.confidence
FROM projects
CROSS JOIN (
    VALUES
        (
            'Requirements analysis',
            'labor'::cost_category,
            120.000,
            90.00,
            0.90
        ),
        (
            'Application engineering',
            'labor'::cost_category,
            420.000,
            72.00,
            0.85
        ),
        (
            'Testing and quality assurance',
            'labor'::cost_category,
            180.000,
            58.00,
            0.88
        ),
        (
            'Security validation',
            'security'::cost_category,
            60.000,
            105.00,
            0.76
        ),
        (
            'Cloud environment',
            'infrastructure'::cost_category,
            12.000,
            800.00,
            0.82
        ),
        (
            'User training',
            'training'::cost_category,
            10.000,
            650.00,
            0.90
        )
) AS source(description, category, quantity, unit_cost, confidence)
WHERE project_code = 'PIM-2026';

INSERT INTO project_risks (
    project_id,
    risk_name,
    probability,
    impact,
    status
)
SELECT
    project_id,
    source.risk_name,
    source.probability,
    source.impact,
    source.status
FROM projects
CROSS JOIN (
    VALUES
        (
            'External integration rework',
            0.25000,
            22000.00,
            'open'::risk_status
        ),
        (
            'Security remediation',
            0.15000,
            28000.00,
            'open'::risk_status
        ),
        (
            'Infrastructure consumption increase',
            0.20000,
            15000.00,
            'mitigated'::risk_status
        )
) AS source(risk_name, probability, impact, status)
WHERE project_code = 'PIM-2026';

INSERT INTO actual_costs (
    project_id,
    cost_date,
    category,
    description,
    amount
)
SELECT
    project_id,
    DATE '2026-09-05',
    'labor',
    'Requirements and architecture work',
    26000.00
FROM projects
WHERE project_code = 'PIM-2026';

INSERT INTO actual_costs (
    project_id,
    cost_date,
    category,
    description,
    amount
)
SELECT
    project_id,
    DATE '2026-09-25',
    'labor',
    'Application engineering',
    41000.00
FROM projects
WHERE project_code = 'PIM-2026';

INSERT INTO actual_costs (
    project_id,
    cost_date,
    category,
    description,
    amount
)
SELECT
    project_id,
    DATE '2026-10-03',
    'infrastructure',
    'Cloud services',
    9000.00
FROM projects
WHERE project_code = 'PIM-2026';

INSERT INTO monthly_forecasts (
    project_id,
    forecast_month,
    forecast_amount
)
SELECT
    project_id,
    source.forecast_month,
    source.forecast_amount
FROM projects
CROSS JOIN (
    VALUES
        (DATE '2026-10-01', 31000.00),
        (DATE '2026-11-01', 35000.00),
        (DATE '2026-12-01', 28000.00)
) AS source(forecast_month, forecast_amount)
WHERE project_code = 'PIM-2026';

CREATE VIEW project_cost_summary AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    p.approved_budget,
    p.reserve_rate,
    COALESCE(ci.direct_cost, 0)::NUMERIC(14,2) AS direct_cost,
    COALESCE(r.expected_risk_cost, 0)::NUMERIC(14,2)
        AS expected_risk_cost,
    (
        COALESCE(ci.direct_cost, 0)
        * p.reserve_rate
    )::NUMERIC(14,2) AS management_reserve,
    (
        COALESCE(ci.direct_cost, 0)
        + COALESCE(r.expected_risk_cost, 0)
        + (
            COALESCE(ci.direct_cost, 0)
            * p.reserve_rate
        )
    )::NUMERIC(14,2) AS estimated_total
FROM projects p
LEFT JOIN (
    SELECT
        project_id,
        SUM(quantity * unit_cost) AS direct_cost
    FROM cost_items
    GROUP BY project_id
) ci
    ON ci.project_id = p.project_id
LEFT JOIN (
    SELECT
        project_id,
        SUM(probability * impact) AS expected_risk_cost
    FROM project_risks
    WHERE status <> 'closed'
    GROUP BY project_id
) r
    ON r.project_id = p.project_id;

SELECT
    project_code,
    project_name,
    approved_budget,
    direct_cost,
    expected_risk_cost,
    management_reserve,
    estimated_total,
    (
        approved_budget - estimated_total
    )::NUMERIC(14,2) AS budget_variance,
    CASE
        WHEN estimated_total <= approved_budget
            THEN 'WITHIN_BUDGET'
        ELSE 'OVER_BUDGET'
    END AS budget_status
FROM project_cost_summary;

SELECT
    p.project_code,
    ci.category,
    SUM(ci.quantity * ci.unit_cost)::NUMERIC(14,2)
        AS category_cost,
    ROUND(
        100.0
        * SUM(ci.quantity * ci.unit_cost)
        / NULLIF(
            SUM(SUM(ci.quantity * ci.unit_cost))
            OVER (PARTITION BY p.project_id),
            0
        ),
        2
    ) AS percentage_of_direct_cost
FROM projects p
JOIN cost_items ci
    ON ci.project_id = p.project_id
WHERE p.project_code = 'PIM-2026'
GROUP BY
    p.project_id,
    p.project_code,
    ci.category
ORDER BY category_cost DESC;

SELECT
    p.project_code,
    SUM(r.probability * r.impact)::NUMERIC(14,2)
        AS expected_risk_cost,
    COUNT(*) AS open_risk_count
FROM projects p
JOIN project_risks r
    ON r.project_id = p.project_id
WHERE p.project_code = 'PIM-2026'
  AND r.status <> 'closed'
GROUP BY p.project_code;

WITH actuals AS (
    SELECT
        project_id,
        SUM(amount) AS actual_cost
    FROM actual_costs
    GROUP BY project_id
),
remaining_forecast AS (
    SELECT
        project_id,
        SUM(forecast_amount) AS forecast_cost
    FROM monthly_forecasts
    WHERE forecast_month >= DATE '2026-10-01'
    GROUP BY project_id
)
SELECT
    p.project_code,
    COALESCE(a.actual_cost, 0)::NUMERIC(14,2) AS actual_cost_to_date,
    COALESCE(f.forecast_cost, 0)::NUMERIC(14,2)
        AS remaining_forecast,
    (
        COALESCE(a.actual_cost, 0)
        + COALESCE(f.forecast_cost, 0)
    )::NUMERIC(14,2) AS estimate_at_completion,
    (
        p.approved_budget
        - (
            COALESCE(a.actual_cost, 0)
            + COALESCE(f.forecast_cost, 0)
        )
    )::NUMERIC(14,2) AS forecast_variance
FROM projects p
LEFT JOIN actuals a
    ON a.project_id = p.project_id
LEFT JOIN remaining_forecast f
    ON f.project_id = p.project_id
WHERE p.project_code = 'PIM-2026';

BEGIN;

UPDATE projects
SET status = 'forecasting'
WHERE project_code = 'PIM-2026'
  AND status = 'approved';

-- The update is intentionally transactional so a caller can inspect
-- the affected row before deciding whether to commit the state change.

SELECT
    project_code,
    status
FROM projects
WHERE project_code = 'PIM-2026';

COMMIT;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM cost_items
        WHERE quantity < 0
           OR unit_cost < 0
    ) THEN
        RAISE EXCEPTION
            'Invalid negative cost data exists.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM project_risks
        WHERE probability < 0
           OR probability > 1
    ) THEN
        RAISE EXCEPTION
            'Invalid risk probability exists.';
    END IF;
END
$$;

SELECT
    project_code,
    project_name,
    approved_budget,
    direct_cost,
    expected_risk_cost,
    management_reserve,
    estimated_total,
    CASE
        WHEN estimated_total <= approved_budget
            THEN 'APPROVED BUDGET COVERS CURRENT ESTIMATE'
        WHEN estimated_total <= approved_budget * 1.10
            THEN 'MINOR FUNDING PRESSURE'
        ELSE 'MATERIAL FUNDING PRESSURE'
    END AS management_assessment
FROM project_cost_summary
WHERE project_code = 'PIM-2026';
