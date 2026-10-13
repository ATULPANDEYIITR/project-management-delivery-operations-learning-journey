/*
Project Budget Management
PostgreSQL-compatible SQL

The relational model separates:
  project identity
  budget baselines
  budget categories
  commitments
  actual expenses
  change requests
  approvals
  reporting

Amounts use NUMERIC rather than floating-point types because financial
calculations require deterministic decimal precision.
*/

DROP SCHEMA IF EXISTS project_budget CASCADE;
CREATE SCHEMA project_budget;

SET search_path TO project_budget;

CREATE TYPE project_status AS ENUM (
    'DRAFT',
    'APPROVED',
    'ACTIVE',
    'CLOSED'
);

CREATE TYPE change_status AS ENUM (
    'PROPOSED',
    'APPROVED',
    'REJECTED'
);

CREATE TYPE expense_status AS ENUM (
    'PENDING',
    'POSTED',
    'REJECTED'
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    project_manager VARCHAR(150) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    status project_status NOT NULL DEFAULT 'DRAFT',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    contingency_rate NUMERIC(5,4) NOT NULL DEFAULT 0.1000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT project_dates_valid
        CHECK (end_date >= start_date),

    CONSTRAINT project_currency_valid
        CHECK (currency_code ~ '^[A-Z]{3}$'),

    CONSTRAINT contingency_rate_valid
        CHECK (contingency_rate >= 0 AND contingency_rate <= 1)
);

CREATE TABLE budget_categories (
    category_id BIGSERIAL PRIMARY KEY,
    category_code VARCHAR(50) NOT NULL UNIQUE,
    category_name VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE project_budget_lines (
    budget_line_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    category_id BIGINT NOT NULL
        REFERENCES budget_categories(category_id),
    description TEXT NOT NULL,
    planned_amount NUMERIC(18,2) NOT NULL,

    CONSTRAINT planned_amount_positive
        CHECK (planned_amount > 0),

    CONSTRAINT unique_project_category
        UNIQUE (project_id, category_id)
);

CREATE TABLE commitments (
    commitment_id BIGSERIAL PRIMARY KEY,
    budget_line_id BIGINT NOT NULL
        REFERENCES project_budget_lines(budget_line_id)
        ON DELETE CASCADE,
    supplier_name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    committed_amount NUMERIC(18,2) NOT NULL,
    commitment_date DATE NOT NULL DEFAULT CURRENT_DATE,

    CONSTRAINT commitment_amount_positive
        CHECK (committed_amount > 0)
);

CREATE TABLE expenses (
    expense_id BIGSERIAL PRIMARY KEY,
    budget_line_id BIGINT NOT NULL
        REFERENCES project_budget_lines(budget_line_id)
        ON DELETE CASCADE,
    expense_date DATE NOT NULL,
    description TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    status expense_status NOT NULL DEFAULT 'PENDING',

    CONSTRAINT expense_amount_positive
        CHECK (amount > 0)
);

CREATE TABLE change_requests (
    change_request_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,
    request_code VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    requested_amount NUMERIC(18,2) NOT NULL,
    status change_status NOT NULL DEFAULT 'PROPOSED',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMPTZ,

    CONSTRAINT requested_amount_positive
        CHECK (requested_amount > 0),

    CONSTRAINT unique_project_change
        UNIQUE (project_id, request_code),

    CONSTRAINT approval_timestamp_consistent
        CHECK (
            (status = 'APPROVED' AND approved_at IS NOT NULL)
            OR
            (status <> 'APPROVED')
        )
);

CREATE TABLE reviewers (
    reviewer_id BIGSERIAL PRIMARY KEY,
    employee_code VARCHAR(50) NOT NULL UNIQUE,
    reviewer_name VARCHAR(150) NOT NULL,
    role_name VARCHAR(120) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE change_approvals (
    approval_id BIGSERIAL PRIMARY KEY,
    change_request_id BIGINT NOT NULL
        REFERENCES change_requests(change_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL
        REFERENCES reviewers(reviewer_id),
    approved BOOLEAN NOT NULL,
    decision_note TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_change_reviewer
        UNIQUE (change_request_id, reviewer_id)
);

CREATE INDEX idx_budget_lines_project
    ON project_budget_lines(project_id);

CREATE INDEX idx_commitments_budget_line
    ON commitments(budget_line_id);

CREATE INDEX idx_expenses_budget_line_date
    ON expenses(budget_line_id, expense_date);

CREATE INDEX idx_change_requests_project_status
    ON change_requests(project_id, status);

CREATE INDEX idx_change_approvals_request
    ON change_approvals(change_request_id);

INSERT INTO budget_categories
    (category_code, category_name)
VALUES
    ('PERSONNEL', 'Personnel'),
    ('CLOUD', 'Cloud Infrastructure'),
    ('SOFTWARE', 'Software'),
    ('SECURITY', 'Security'),
    ('TESTING', 'Testing'),
    ('TRAINING', 'Training');

INSERT INTO projects
    (
        project_code,
        project_name,
        project_manager,
        currency_code,
        status,
        start_date,
        end_date,
        contingency_rate
    )
VALUES
    (
        'PRJ-2026-042',
        'Enterprise Data Platform',
        'Technology PMO',
        'INR',
        'ACTIVE',
        '2026-10-01',
        '2027-03-31',
        0.1200
    );

INSERT INTO project_budget_lines
    (
        project_id,
        category_id,
        description,
        planned_amount
    )
SELECT
    p.project_id,
    c.category_id,
    v.description,
    v.planned_amount
FROM projects p
JOIN (
    VALUES
        ('PERSONNEL', 'Engineering and delivery team', 4200000.00::NUMERIC),
        ('CLOUD', 'Compute, storage, and networking', 1350000.00::NUMERIC),
        ('SOFTWARE', 'Commercial development tooling', 650000.00::NUMERIC),
        ('SECURITY', 'Security assurance and tooling', 650000.00::NUMERIC),
        ('TESTING', 'Integration and performance testing', 500000.00::NUMERIC),
        ('TRAINING', 'Technical training and transition', 300000.00::NUMERIC)
) AS v(category_code, description, planned_amount)
    ON TRUE
JOIN budget_categories c
    ON c.category_code = v.category_code
WHERE p.project_code = 'PRJ-2026-042';

INSERT INTO commitments
    (
        budget_line_id,
        supplier_name,
        description,
        committed_amount
    )
SELECT
    b.budget_line_id,
    v.supplier_name,
    v.description,
    v.committed_amount
FROM project_budget_lines b
JOIN budget_categories c
    ON c.category_id = b.category_id
JOIN (
    VALUES
        ('PERSONNEL', 'Internal Delivery Team', 'Committed engineering effort', 2800000.00::NUMERIC),
        ('CLOUD', 'Cloud Provider', 'Infrastructure reservation', 850000.00::NUMERIC),
        ('SECURITY', 'Security Vendor', 'Security tooling', 400000.00::NUMERIC),
        ('TESTING', 'Testing Partner', 'Integration testing', 180000.00::NUMERIC)
) AS v(category_code, supplier_name, description, committed_amount)
    ON v.category_code = c.category_code;

INSERT INTO expenses
    (
        budget_line_id,
        expense_date,
        description,
        amount,
        status
    )
SELECT
    b.budget_line_id,
    DATE '2026-10-12',
    v.description,
    v.amount,
    'POSTED'
FROM project_budget_lines b
JOIN budget_categories c
    ON c.category_id = b.category_id
JOIN (
    VALUES
        ('PERSONNEL', 'Engineering expenditure', 2100000.00::NUMERIC),
        ('CLOUD', 'Cloud infrastructure expenditure', 640000.00::NUMERIC),
        ('SECURITY', 'Security tooling expenditure', 270000.00::NUMERIC),
        ('TESTING', 'Integration testing expenditure', 120000.00::NUMERIC)
) AS v(category_code, description, amount)
    ON v.category_code = c.category_code;

INSERT INTO change_requests
    (
        project_id,
        request_code,
        description,
        requested_amount,
        status,
        approved_at
    )
SELECT
    project_id,
    'CR-001',
    'Expanded compliance testing',
    240000.00,
    'APPROVED',
    CURRENT_TIMESTAMP
FROM projects
WHERE project_code = 'PRJ-2026-042';

INSERT INTO reviewers
    (employee_code, reviewer_name, role_name)
VALUES
    ('EMP-1001', 'Program Director', 'Senior Approver'),
    ('EMP-1002', 'Finance Controller', 'Financial Controller');

INSERT INTO change_approvals
    (
        change_request_id,
        reviewer_id,
        approved,
        decision_note
    )
SELECT
    cr.change_request_id,
    r.reviewer_id,
    TRUE,
    'Change is justified by expanded compliance scope.'
FROM change_requests cr
JOIN reviewers r
    ON r.employee_code = 'EMP-1001'
WHERE cr.request_code = 'CR-001';

CREATE VIEW budget_line_actuals AS
SELECT
    b.budget_line_id,
    b.project_id,
    c.category_code,
    c.category_name,
    b.planned_amount,
    COALESCE(comm.committed_amount, 0.00) AS committed_amount,
    COALESCE(exp.actual_amount, 0.00) AS actual_amount,
    b.planned_amount
        - COALESCE(exp.actual_amount, 0.00) AS variance_amount
FROM project_budget_lines b
JOIN budget_categories c
    ON c.category_id = b.category_id
LEFT JOIN (
    SELECT
        budget_line_id,
        SUM(committed_amount) AS committed_amount
    FROM commitments
    GROUP BY budget_line_id
) comm
    ON comm.budget_line_id = b.budget_line_id
LEFT JOIN (
    SELECT
        budget_line_id,
        SUM(amount) AS actual_amount
    FROM expenses
    WHERE status = 'POSTED'
    GROUP BY budget_line_id
) exp
    ON exp.budget_line_id = b.budget_line_id;

CREATE VIEW project_budget_summary AS
WITH direct_budget AS (
    SELECT
        project_id,
        SUM(planned_amount) AS planned_budget
    FROM project_budget_lines
    GROUP BY project_id
),
actuals AS (
    SELECT
        b.project_id,
        SUM(e.amount) AS actual_spend
    FROM project_budget_lines b
    JOIN expenses e
        ON e.budget_line_id = b.budget_line_id
    WHERE e.status = 'POSTED'
    GROUP BY b.project_id
),
approved_changes AS (
    SELECT
        project_id,
        SUM(requested_amount) AS approved_change_amount
    FROM change_requests
    WHERE status = 'APPROVED'
    GROUP BY project_id
)
SELECT
    p.project_code,
    p.project_name,
    p.status,
    d.planned_budget,
    ROUND(
        d.planned_budget * p.contingency_rate,
        2
    ) AS contingency_amount,
    COALESCE(ac.approved_change_amount, 0.00)
        AS approved_change_amount,
    d.planned_budget
        + ROUND(
            d.planned_budget * p.contingency_rate,
            2
        )
        + COALESCE(ac.approved_change_amount, 0.00)
        AS authorized_budget,
    COALESCE(a.actual_spend, 0.00) AS actual_spend
FROM projects p
JOIN direct_budget d
    ON d.project_id = p.project_id
LEFT JOIN actuals a
    ON a.project_id = p.project_id
LEFT JOIN approved_changes ac
    ON ac.project_id = p.project_id;

-- Category-level variance analysis.
SELECT
    category_code,
    category_name,
    planned_amount,
    committed_amount,
    actual_amount,
    variance_amount,
    ROUND(
        actual_amount / NULLIF(planned_amount, 0) * 100,
        2
    ) AS utilization_percent
FROM budget_line_actuals
WHERE project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'PRJ-2026-042'
)
ORDER BY variance_amount;

-- Identify categories where actual spending exceeds the approved baseline.
SELECT
    category_code,
    category_name,
    planned_amount,
    actual_amount,
    variance_amount
FROM budget_line_actuals
WHERE actual_amount > planned_amount
ORDER BY variance_amount;

-- Determine project-level financial health.
SELECT
    project_code,
    project_name,
    planned_budget,
    contingency_amount,
    approved_change_amount,
    authorized_budget,
    actual_spend,
    authorized_budget - actual_spend AS remaining_authorization,
    ROUND(
        actual_spend / NULLIF(authorized_budget, 0) * 100,
        2
    ) AS utilization_percent,
    CASE
        WHEN actual_spend > authorized_budget
            THEN 'OVER_BUDGET'
        WHEN actual_spend >= authorized_budget * 0.90
            THEN 'CRITICAL'
        WHEN actual_spend >= authorized_budget * 0.75
            THEN 'WATCH'
        ELSE 'HEALTHY'
    END AS budget_health
FROM project_budget_summary;

-- Show approved changes and their approval evidence.
SELECT
    cr.request_code,
    cr.description,
    cr.requested_amount,
    cr.status,
    r.reviewer_name,
    r.role_name,
    ca.approved,
    ca.decision_note
FROM change_requests cr
LEFT JOIN change_approvals ca
    ON ca.change_request_id = cr.change_request_id
LEFT JOIN reviewers r
    ON r.reviewer_id = ca.reviewer_id
WHERE cr.project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'PRJ-2026-042'
);

-- A transaction makes a budget change atomic.
BEGIN;

UPDATE change_requests
SET
    status = 'APPROVED',
    approved_at = CURRENT_TIMESTAMP
WHERE request_code = 'CR-001'
  AND status = 'PROPOSED';

-- The approval evidence and status update must be treated as one unit.
-- If either operation fails in a real workflow, the transaction can roll back.
COMMIT;

-- Database-enforced failure example.
-- This statement is intentionally commented because executing it would fail:
-- INSERT INTO project_budget_lines
--     (project_id, category_id, description, planned_amount)
-- VALUES
--     (
--         (SELECT project_id FROM projects WHERE project_code = 'PRJ-2026-042'),
--         (SELECT category_id FROM budget_categories WHERE category_code = 'CLOUD'),
--         'Invalid negative allocation',
--         -5000.00
--     );

-- Forecast based on current actuals plus outstanding commitments.
WITH actuals AS (
    SELECT
        b.project_id,
        SUM(e.amount) AS actual_spend
    FROM project_budget_lines b
    JOIN expenses e
        ON e.budget_line_id = b.budget_line_id
    WHERE e.status = 'POSTED'
    GROUP BY b.project_id
),
commitments AS (
    SELECT
        b.project_id,
        SUM(c.committed_amount) AS committed_spend
    FROM project_budget_lines b
    JOIN commitments c
        ON c.budget_line_id = b.budget_line_id
    GROUP BY b.project_id
)
SELECT
    p.project_code,
    COALESCE(a.actual_spend, 0.00) AS actual_spend,
    COALESCE(c.committed_spend, 0.00) AS committed_spend,
    GREATEST(
        COALESCE(c.committed_spend, 0.00)
        - COALESCE(a.actual_spend, 0.00),
        0.00
    ) AS remaining_commitments,
    COALESCE(a.actual_spend, 0.00)
    + GREATEST(
        COALESCE(c.committed_spend, 0.00)
        - COALESCE(a.actual_spend, 0.00),
        0.00
    ) AS projected_cost
FROM projects p
LEFT JOIN actuals a
    ON a.project_id = p.project_id
LEFT JOIN commitments c
    ON c.project_id = p.project_id
WHERE p.project_code = 'PRJ-2026-042';
