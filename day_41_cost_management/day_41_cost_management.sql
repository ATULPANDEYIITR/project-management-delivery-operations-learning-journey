DROP SCHEMA IF EXISTS project_cost_management CASCADE;
CREATE SCHEMA project_cost_management;
SET search_path TO project_cost_management;

CREATE TYPE cost_type AS ENUM (
    'labor',
    'material',
    'equipment',
    'software',
    'travel',
    'subcontract',
    'overhead',
    'contingency'
);

CREATE TYPE cost_classification AS ENUM (
    'direct',
    'indirect'
);

CREATE TYPE project_status AS ENUM (
    'planned',
    'active',
    'closed'
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(30) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    approved_budget NUMERIC(14,2) NOT NULL CHECK (approved_budget >= 0),
    management_reserve NUMERIC(14,2) NOT NULL DEFAULT 0
        CHECK (management_reserve >= 0),
    status project_status NOT NULL DEFAULT 'planned',
    start_date DATE NOT NULL,
    end_date DATE,
    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE cost_categories (
    category_id BIGSERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE cost_items (
    cost_item_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    category_id BIGINT NOT NULL
        REFERENCES cost_categories(category_id),
    cost_name VARCHAR(200) NOT NULL,
    cost_type cost_type NOT NULL,
    classification cost_classification NOT NULL,
    planned_amount NUMERIC(14,2) NOT NULL
        CHECK (planned_amount >= 0),
    actual_amount NUMERIC(14,2) NOT NULL DEFAULT 0
        CHECK (actual_amount >= 0),
    committed_amount NUMERIC(14,2) NOT NULL DEFAULT 0
        CHECK (committed_amount >= 0),
    incurred_date DATE NOT NULL,
    UNIQUE (project_id, cost_name)
);

CREATE TABLE cost_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    cost_item_id BIGINT NOT NULL
        REFERENCES cost_items(cost_item_id)
        ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    amount NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    transaction_reference VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE budget_change_requests (
    change_request_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    requested_amount NUMERIC(14,2) NOT NULL
        CHECK (requested_amount <> 0),
    reason TEXT NOT NULL,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cost_items_project
    ON cost_items(project_id);

CREATE INDEX idx_cost_items_project_type
    ON cost_items(project_id, cost_type);

CREATE INDEX idx_cost_transactions_item_date
    ON cost_transactions(cost_item_id, transaction_date);

INSERT INTO cost_categories (category_name, description) VALUES
('People', 'Internal labor required to execute project work'),
('Technology', 'Software, infrastructure, and technical equipment'),
('External Services', 'Third-party implementation and specialist services'),
('Travel', 'Travel and site-related project expenditure'),
('Corporate Allocation', 'Indirect organizational overhead assigned to the project');

INSERT INTO projects (
    project_code,
    project_name,
    approved_budget,
    management_reserve,
    status,
    start_date,
    end_date
)
VALUES (
    'PRJ-OPS-001',
    'Operations Analytics Platform',
    300000.00,
    20000.00,
    'active',
    DATE '2026-01-15',
    DATE '2026-12-20'
);

INSERT INTO cost_items (
    project_id,
    category_id,
    cost_name,
    cost_type,
    classification,
    planned_amount,
    actual_amount,
    committed_amount,
    incurred_date
)
SELECT
    p.project_id,
    c.category_id,
    x.cost_name,
    x.cost_type::cost_type,
    x.classification::cost_classification,
    x.planned_amount,
    x.actual_amount,
    x.committed_amount,
    x.incurred_date
FROM projects p
CROSS JOIN LATERAL (
    VALUES
    (
        'Data engineering labor',
        1,
        'labor',
        'direct',
        95000.00,
        88000.00,
        7000.00,
        DATE '2026-08-31'
    ),
    (
        'Cloud infrastructure',
        2,
        'equipment',
        'direct',
        50000.00,
        47000.00,
        8000.00,
        DATE '2026-09-05'
    ),
    (
        'Analytics software',
        2,
        'software',
        'direct',
        40000.00,
        43000.00,
        2000.00,
        DATE '2026-09-10'
    ),
    (
        'Implementation partner',
        3,
        'subcontract',
        'direct',
        65000.00,
        58000.00,
        14000.00,
        DATE '2026-09-15'
    ),
    (
        'Site travel',
        4,
        'travel',
        'direct',
        15000.00,
        9000.00,
        1000.00,
        DATE '2026-09-18'
    ),
    (
        'Corporate allocation',
        5,
        'overhead',
        'indirect',
        20000.00,
        16000.00,
        0.00,
        DATE '2026-09-30'
    )
) AS x(
    cost_name,
    category_id,
    cost_type,
    classification,
    planned_amount,
    actual_amount,
    committed_amount,
    incurred_date
)
JOIN cost_categories c
    ON c.category_id = x.category_id
WHERE p.project_code = 'PRJ-OPS-001';

INSERT INTO cost_transactions (
    cost_item_id,
    transaction_date,
    amount,
    transaction_reference,
    description
)
SELECT
    ci.cost_item_id,
    DATE '2026-09-30',
    12500.00,
    'TXN-LAB-001',
    'September data engineering payroll allocation'
FROM cost_items ci
WHERE ci.cost_name = 'Data engineering labor';

INSERT INTO cost_transactions (
    cost_item_id,
    transaction_date,
    amount,
    transaction_reference,
    description
)
SELECT
    ci.cost_item_id,
    DATE '2026-09-30',
    9500.00,
    'TXN-CLD-001',
    'September cloud infrastructure usage'
FROM cost_items ci
WHERE ci.cost_name = 'Cloud infrastructure';

CREATE VIEW project_cost_summary AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    p.approved_budget,
    p.management_reserve,
    COALESCE(SUM(ci.planned_amount), 0)::NUMERIC(14,2)
        AS planned_cost,
    COALESCE(SUM(ci.actual_amount), 0)::NUMERIC(14,2)
        AS actual_cost,
    COALESCE(SUM(ci.committed_amount), 0)::NUMERIC(14,2)
        AS committed_cost,
    (
        COALESCE(SUM(ci.actual_amount), 0)
        + COALESCE(SUM(ci.committed_amount), 0)
    )::NUMERIC(14,2) AS forecast_at_completion,
    (
        p.approved_budget
        - COALESCE(SUM(ci.actual_amount), 0)
    )::NUMERIC(14,2) AS remaining_budget
FROM projects p
LEFT JOIN cost_items ci
    ON ci.project_id = p.project_id
GROUP BY
    p.project_id,
    p.project_code,
    p.project_name,
    p.approved_budget,
    p.management_reserve;

SELECT *
FROM project_cost_summary
WHERE project_code = 'PRJ-OPS-001';

SELECT
    p.project_code,
    ci.cost_type,
    SUM(ci.planned_amount)::NUMERIC(14,2) AS planned,
    SUM(ci.actual_amount)::NUMERIC(14,2) AS actual,
    SUM(ci.committed_amount)::NUMERIC(14,2) AS committed,
    (
        SUM(ci.planned_amount) - SUM(ci.actual_amount)
    )::NUMERIC(14,2) AS current_variance
FROM projects p
JOIN cost_items ci
    ON ci.project_id = p.project_id
WHERE p.project_code = 'PRJ-OPS-001'
GROUP BY p.project_code, ci.cost_type
ORDER BY actual DESC;

SELECT
    ci.cost_name,
    ci.cost_type,
    ci.planned_amount,
    ci.actual_amount,
    ci.committed_amount,
    (
        ci.actual_amount + ci.committed_amount
    )::NUMERIC(14,2) AS forecast,
    (
        ci.planned_amount - ci.actual_amount
    )::NUMERIC(14,2) AS variance
FROM cost_items ci
JOIN projects p
    ON p.project_id = ci.project_id
WHERE p.project_code = 'PRJ-OPS-001'
ORDER BY variance ASC;

SELECT
    p.project_code,
    ROUND(
        (
            SUM(ci.actual_amount)
            / NULLIF(p.approved_budget, 0)
        ) * 100,
        2
    ) AS budget_utilization_percent,
    CASE
        WHEN SUM(ci.actual_amount) > p.approved_budget
            THEN 'OVER_BUDGET'
        WHEN SUM(ci.actual_amount) + SUM(ci.committed_amount)
             > p.approved_budget
            THEN 'FORECAST_OVER_BUDGET'
        WHEN (
            SUM(ci.actual_amount) / NULLIF(p.approved_budget, 0)
        ) >= 0.90
            THEN 'HIGH_UTILIZATION'
        WHEN (
            SUM(ci.actual_amount) / NULLIF(p.approved_budget, 0)
        ) >= 0.75
            THEN 'WATCH'
        ELSE 'WITHIN_PLAN'
    END AS cost_status
FROM projects p
JOIN cost_items ci
    ON ci.project_id = p.project_id
WHERE p.project_code = 'PRJ-OPS-001'
GROUP BY p.project_code, p.approved_budget;

WITH cost_rollup AS (
    SELECT
        project_id,
        SUM(planned_amount) AS planned,
        SUM(actual_amount) AS actual,
        SUM(committed_amount) AS committed
    FROM cost_items
    GROUP BY project_id
)
SELECT
    p.project_code,
    p.approved_budget AS bac,
    cr.planned AS pv,
    cr.actual AS ac,
    (cr.actual * 0.95)::NUMERIC(14,2) AS illustrative_ev,
    ROUND(
        ((cr.actual * 0.95) / NULLIF(cr.actual, 0))::NUMERIC,
        2
    ) AS illustrative_cpi
FROM projects p
JOIN cost_rollup cr
    ON cr.project_id = p.project_id
WHERE p.project_code = 'PRJ-OPS-001';

BEGIN;

INSERT INTO budget_change_requests (
    project_id,
    requested_amount,
    reason
)
SELECT
    project_id,
    12000.00,
    'Unexpected integration effort identified during implementation'
FROM projects
WHERE project_code = 'PRJ-OPS-001';

UPDATE budget_change_requests
SET approved = TRUE
WHERE change_request_id = (
    SELECT MAX(change_request_id)
    FROM budget_change_requests
);

COMMIT;

CREATE OR REPLACE FUNCTION prevent_excessive_cost_transaction()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    project_budget NUMERIC(14,2);
    current_actual NUMERIC(14,2);
    current_committed NUMERIC(14,2);
    project_id_value BIGINT;
BEGIN
    SELECT ci.project_id
    INTO project_id_value
    FROM cost_items ci
    WHERE ci.cost_item_id = NEW.cost_item_id;

    SELECT approved_budget
    INTO project_budget
    FROM projects
    WHERE project_id = project_id_value;

    SELECT
        COALESCE(SUM(actual_amount), 0),
        COALESCE(SUM(committed_amount), 0)
    INTO current_actual, current_committed
    FROM cost_items
    WHERE project_id = project_id_value;

    IF current_actual + current_committed + NEW.amount
       > project_budget * 1.50 THEN
        RAISE EXCEPTION
            'Transaction rejected: forecast exceeds 150%% of approved budget';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_cost_transaction_control
BEFORE INSERT ON cost_transactions
FOR EACH ROW
EXECUTE FUNCTION prevent_excessive_cost_transaction();

SELECT
    p.project_code,
    p.project_name,
    c.category_name,
    ci.cost_name,
    ci.classification,
    ci.actual_amount
FROM projects p
JOIN cost_items ci
    ON ci.project_id = p.project_id
JOIN cost_categories c
    ON c.category_id = ci.category_id
WHERE ci.actual_amount > ci.planned_amount
ORDER BY ci.actual_amount - ci.planned_amount DESC;

SELECT
    p.project_code,
    SUM(
        CASE
            WHEN ci.classification = 'direct'
            THEN ci.actual_amount
            ELSE 0
        END
    )::NUMERIC(14,2) AS direct_cost,
    SUM(
        CASE
            WHEN ci.classification = 'indirect'
            THEN ci.actual_amount
            ELSE 0
        END
    )::NUMERIC(14,2) AS indirect_cost
FROM projects p
JOIN cost_items ci
    ON ci.project_id = p.project_id
WHERE p.project_code = 'PRJ-OPS-001'
GROUP BY p.project_code;

SELECT
    p.project_code,
    p.approved_budget,
    s.forecast_at_completion,
    (
        s.forecast_at_completion - p.approved_budget
    )::NUMERIC(14,2) AS forecast_overrun,
    p.management_reserve,
    CASE
        WHEN s.forecast_at_completion <= p.approved_budget
            THEN 'NO_RESERVE_REQUIRED'
        WHEN s.forecast_at_completion
             <= p.approved_budget + p.management_reserve
            THEN 'RESERVE_CAN_COVER_FORECAST'
        ELSE 'RESERVE_INSUFFICIENT'
    END AS reserve_assessment
FROM projects p
JOIN project_cost_summary s
    ON s.project_id = p.project_id
WHERE p.project_code = 'PRJ-OPS-001';
