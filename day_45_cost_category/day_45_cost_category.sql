DROP SCHEMA IF EXISTS cost_tracking CASCADE;
CREATE SCHEMA cost_tracking;

SET search_path TO cost_tracking;

CREATE TYPE expense_status AS ENUM (
    'planned',
    'committed',
    'actual',
    'cancelled'
);

CREATE TYPE expense_category AS ENUM (
    'labor',
    'cloud',
    'software',
    'equipment',
    'travel',
    'contractor',
    'materials',
    'other'
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    project_code VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    CHECK (end_date >= start_date),
    CHECK (currency_code ~ '^[A-Z]{3}$')
);

CREATE TABLE budget_lines (
    budget_line_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id)
        ON DELETE CASCADE,
    category expense_category NOT NULL,
    budget_amount NUMERIC(14,2) NOT NULL,
    UNIQUE (project_id, category),
    CHECK (budget_amount >= 0)
);

CREATE TABLE vendors (
    vendor_id BIGSERIAL PRIMARY KEY,
    vendor_name VARCHAR(200) NOT NULL UNIQUE
);

CREATE TABLE employees (
    employee_id BIGSERIAL PRIMARY KEY,
    employee_name VARCHAR(200) NOT NULL,
    approval_limit NUMERIC(14,2) NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (approval_limit >= 0)
);

CREATE TABLE expenses (
    expense_id BIGSERIAL PRIMARY KEY,
    expense_code VARCHAR(40) NOT NULL UNIQUE,
    project_id BIGINT NOT NULL REFERENCES projects(project_id)
        ON DELETE CASCADE,
    category expense_category NOT NULL,
    vendor_id BIGINT REFERENCES vendors(vendor_id),
    description VARCHAR(500) NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    expense_date DATE NOT NULL,
    status expense_status NOT NULL DEFAULT 'actual',
    invoice_number VARCHAR(100),
    entered_by BIGINT REFERENCES employees(employee_id),
    approved_by BIGINT REFERENCES employees(employee_id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (amount > 0),
    CHECK (
        status <> 'actual'
        OR entered_by IS NOT NULL
    ),
    CHECK (
        approved_at IS NULL
        OR approved_by IS NOT NULL
    )
);

CREATE UNIQUE INDEX uq_expenses_vendor_invoice
ON expenses (vendor_id, invoice_number)
WHERE invoice_number IS NOT NULL;

CREATE INDEX idx_expenses_project_date
ON expenses (project_id, expense_date);

CREATE INDEX idx_expenses_project_category
ON expenses (project_id, category);

CREATE INDEX idx_expenses_status
ON expenses (status);

CREATE TABLE approval_events (
    approval_event_id BIGSERIAL PRIMARY KEY,
    expense_id BIGINT NOT NULL REFERENCES expenses(expense_id)
        ON DELETE CASCADE,
    approver_id BIGINT NOT NULL REFERENCES employees(employee_id),
    decision VARCHAR(20) NOT NULL,
    decision_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    CHECK (decision IN ('approved', 'rejected'))
);

CREATE OR REPLACE FUNCTION validate_expense_project_date()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    project_start DATE;
    project_end DATE;
BEGIN
    SELECT start_date, end_date
    INTO project_start, project_end
    FROM projects
    WHERE project_id = NEW.project_id;

    IF project_start IS NULL THEN
        RAISE EXCEPTION 'Project % does not exist', NEW.project_id;
    END IF;

    IF NEW.expense_date < project_start
       OR NEW.expense_date > project_end THEN
        RAISE EXCEPTION
            'Expense date % is outside project period % to %',
            NEW.expense_date,
            project_start,
            project_end;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_expense_project_date
BEFORE INSERT OR UPDATE OF project_id, expense_date
ON expenses
FOR EACH ROW
EXECUTE FUNCTION validate_expense_project_date();

CREATE OR REPLACE FUNCTION validate_expense_approval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    approver_limit NUMERIC(14,2);
BEGIN
    IF NEW.approved_by IS NOT NULL THEN
        SELECT approval_limit
        INTO approver_limit
        FROM employees
        WHERE employee_id = NEW.approved_by
          AND active = TRUE;

        IF approver_limit IS NULL THEN
            RAISE EXCEPTION
                'Approver % is not an active employee',
                NEW.approved_by;
        END IF;

        IF approver_limit < NEW.amount THEN
            RAISE EXCEPTION
                'Approver limit % is below expense amount %',
                approver_limit,
                NEW.amount;
        END IF;

        IF NEW.approved_at IS NULL THEN
            NEW.approved_at = CURRENT_TIMESTAMP;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_expense_approval
BEFORE INSERT OR UPDATE OF approved_by, amount
ON expenses
FOR EACH ROW
EXECUTE FUNCTION validate_expense_approval();

CREATE OR REPLACE VIEW project_cost_summary AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    COALESCE(SUM(bl.budget_amount), 0)::NUMERIC(14,2)
        AS total_budget,
    COALESCE((
        SELECT SUM(e.amount)
        FROM expenses e
        WHERE e.project_id = p.project_id
          AND e.status = 'actual'
    ), 0)::NUMERIC(14,2) AS total_actual,
    (
        COALESCE(SUM(bl.budget_amount), 0)
        -
        COALESCE((
            SELECT SUM(e.amount)
            FROM expenses e
            WHERE e.project_id = p.project_id
              AND e.status = 'actual'
        ), 0)
    )::NUMERIC(14,2) AS budget_variance
FROM projects p
LEFT JOIN budget_lines bl
    ON bl.project_id = p.project_id
GROUP BY
    p.project_id,
    p.project_code,
    p.project_name;

CREATE OR REPLACE VIEW category_cost_analysis AS
SELECT
    p.project_code,
    bl.category,
    bl.budget_amount,
    COALESCE(SUM(
        CASE
            WHEN e.status = 'actual' THEN e.amount
            ELSE 0
        END
    ), 0)::NUMERIC(14,2) AS actual_amount,
    (
        bl.budget_amount
        -
        COALESCE(SUM(
            CASE
                WHEN e.status = 'actual' THEN e.amount
                ELSE 0
            END
        ), 0)
    )::NUMERIC(14,2) AS variance_amount
FROM projects p
JOIN budget_lines bl
    ON bl.project_id = p.project_id
LEFT JOIN expenses e
    ON e.project_id = p.project_id
   AND e.category = bl.category
GROUP BY
    p.project_code,
    bl.category,
    bl.budget_amount;

INSERT INTO projects (
    project_code,
    project_name,
    start_date,
    end_date
)
VALUES (
    'PRJ-SQL-001',
    'Digital Operations Cost Programme',
    DATE '2026-01-01',
    DATE '2026-12-31'
);

INSERT INTO vendors (vendor_name)
VALUES
    ('Internal Engineering'),
    ('Cloud Provider'),
    ('Enterprise Software Vendor'),
    ('Infrastructure Supplier'),
    ('Transformation Consultancy');

INSERT INTO employees (
    employee_name,
    approval_limit
)
VALUES
    ('Project Manager', 50000),
    ('Finance Controller', 250000),
    ('Department Head', 1000000);

INSERT INTO budget_lines (
    project_id,
    category,
    budget_amount
)
SELECT
    project_id,
    category,
    budget_amount
FROM (
    SELECT
        p.project_id,
        x.category,
        x.budget_amount
    FROM projects p
    CROSS JOIN (
        VALUES
            ('labor'::expense_category, 180000::NUMERIC),
            ('cloud'::expense_category, 60000::NUMERIC),
            ('software'::expense_category, 30000::NUMERIC),
            ('equipment'::expense_category, 40000::NUMERIC),
            ('travel'::expense_category, 15000::NUMERIC),
            ('contractor'::expense_category, 45000::NUMERIC)
    ) AS x(category, budget_amount)
    WHERE p.project_code = 'PRJ-SQL-001'
) AS budget_data;

INSERT INTO expenses (
    expense_code,
    project_id,
    category,
    vendor_id,
    description,
    amount,
    expense_date,
    status,
    invoice_number,
    entered_by,
    approved_by
)
SELECT
    x.expense_code,
    p.project_id,
    x.category,
    v.vendor_id,
    x.description,
    x.amount,
    x.expense_date,
    x.status,
    x.invoice_number,
    x.entered_by,
    x.approved_by
FROM projects p
CROSS JOIN (
    VALUES
    (
        'SQL-EXP-001',
        'labor'::expense_category,
        'Internal Engineering',
        'Engineering team allocation',
        32000::NUMERIC,
        DATE '2026-01-31',
        'actual'::expense_status,
        'LAB-SQL-001',
        1::BIGINT,
        1::BIGINT
    ),
    (
        'SQL-EXP-002',
        'cloud'::expense_category,
        'Cloud Provider',
        'January cloud consumption',
        8700::NUMERIC,
        DATE '2026-01-31',
        'actual'::expense_status,
        'CLOUD-SQL-001',
        1::BIGINT,
        1::BIGINT
    ),
    (
        'SQL-EXP-003',
        'software'::expense_category,
        'Enterprise Software Vendor',
        'Application security licensing',
        12500::NUMERIC,
        DATE '2026-02-10',
        'actual'::expense_status,
        'SW-SQL-001',
        1::BIGINT,
        2::BIGINT
    ),
    (
        'SQL-EXP-004',
        'equipment'::expense_category,
        'Infrastructure Supplier',
        'Database infrastructure equipment',
        19000::NUMERIC,
        DATE '2026-02-18',
        'actual'::expense_status,
        'EQ-SQL-001',
        1::BIGINT,
        1::BIGINT
    ),
    (
        'SQL-EXP-005',
        'contractor'::expense_category,
        'Transformation Consultancy',
        'Architecture transformation assessment',
        18000::NUMERIC,
        DATE '2026-03-12',
        'actual'::expense_status,
        'CONS-SQL-001',
        1::BIGINT,
        NULL::BIGINT
    ),
    (
        'SQL-EXP-006',
        'cloud'::expense_category,
        'Cloud Provider',
        'February cloud consumption',
        10200::NUMERIC,
        DATE '2026-02-28',
        'actual'::expense_status,
        'CLOUD-SQL-002',
        1::BIGINT,
        1::BIGINT
    ),
    (
        'SQL-EXP-007',
        'travel'::expense_category,
        'Internal Engineering',
        'Architecture workshop travel',
        5200::NUMERIC,
        DATE '2026-03-05',
        'actual'::expense_status,
        'TRAVEL-SQL-001',
        1::BIGINT,
        1::BIGINT
    )
) AS x(
    expense_code,
    category,
    vendor_name,
    description,
    amount,
    expense_date,
    status,
    invoice_number,
    entered_by,
    approved_by
)
JOIN vendors v
    ON v.vendor_name = x.vendor_name
WHERE p.project_code = 'PRJ-SQL-001';

INSERT INTO approval_events (
    expense_id,
    approver_id,
    decision,
    reason
)
SELECT
    e.expense_id,
    e.approved_by,
    'approved',
    'Expense falls within delegated approval authority.'
FROM expenses e
WHERE e.approved_by IS NOT NULL;

SELECT
    project_code,
    project_name,
    total_budget,
    total_actual,
    budget_variance,
    CASE
        WHEN total_budget = 0 THEN 0
        ELSE ROUND(
            total_actual / total_budget * 100,
            2
        )
    END AS utilization_percent
FROM project_cost_summary;

SELECT
    project_code,
    category,
    budget_amount,
    actual_amount,
    variance_amount,
    CASE
        WHEN budget_amount = 0 AND actual_amount > 0
            THEN 'UNBUDGETED'
        WHEN actual_amount > budget_amount
            THEN 'OVER_BUDGET'
        WHEN actual_amount >= budget_amount * 0.80
            THEN 'WARNING'
        ELSE 'WITHIN_PLAN'
    END AS cost_state
FROM category_cost_analysis
ORDER BY project_code, category;

WITH monthly_cost AS (
    SELECT
        p.project_code,
        DATE_TRUNC('month', e.expense_date)::DATE AS month_start,
        SUM(e.amount) AS actual_amount
    FROM projects p
    JOIN expenses e
        ON e.project_id = p.project_id
    WHERE e.status = 'actual'
    GROUP BY
        p.project_code,
        DATE_TRUNC('month', e.expense_date)
)
SELECT
    project_code,
    month_start,
    actual_amount,
    SUM(actual_amount) OVER (
        PARTITION BY project_code
        ORDER BY month_start
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_actual
FROM monthly_cost
ORDER BY project_code, month_start;

SELECT
    v.vendor_name,
    SUM(e.amount) AS actual_spend,
    COUNT(*) AS expense_count
FROM vendors v
JOIN expenses e
    ON e.vendor_id = v.vendor_id
WHERE e.status = 'actual'
GROUP BY v.vendor_name
ORDER BY actual_spend DESC;

SELECT
    e.expense_code,
    e.description,
    e.amount,
    e.vendor_id,
    e.approved_by,
    'HIGH_VALUE_WITHOUT_APPROVAL' AS control_exception
FROM expenses e
WHERE e.status = 'actual'
  AND e.amount >= 10000
  AND e.approved_by IS NULL;

WITH category_usage AS (
    SELECT
        project_code,
        category,
        budget_amount,
        actual_amount,
        CASE
            WHEN budget_amount = 0 THEN NULL
            ELSE actual_amount / budget_amount
        END AS usage_ratio
    FROM category_cost_analysis
)
SELECT
    project_code,
    category,
    budget_amount,
    actual_amount,
    ROUND(usage_ratio * 100, 2) AS utilization_percent,
    CASE
        WHEN usage_ratio IS NULL AND actual_amount > 0
            THEN 'CRITICAL'
        WHEN usage_ratio >= 1
            THEN 'CRITICAL'
        WHEN usage_ratio >= 0.80
            THEN 'WARNING'
        ELSE 'NORMAL'
    END AS alert_level
FROM category_usage
ORDER BY
    CASE
        WHEN usage_ratio IS NULL AND actual_amount > 0 THEN 0
        WHEN usage_ratio >= 1 THEN 1
        WHEN usage_ratio >= 0.80 THEN 2
        ELSE 3
    END,
    category;

BEGIN;

INSERT INTO expenses (
    expense_code,
    project_id,
    category,
    vendor_id,
    description,
    amount,
    expense_date,
    status,
    invoice_number,
    entered_by
)
SELECT
    'SQL-EXP-COMMITTED',
    p.project_id,
    'cloud',
    v.vendor_id,
    'Committed cloud capacity not yet invoiced',
    6000,
    DATE '2026-04-15',
    'committed',
    'CLOUD-SQL-COMMIT-001',
    1
FROM projects p
JOIN vendors v
    ON v.vendor_name = 'Cloud Provider'
WHERE p.project_code = 'PRJ-SQL-001';

UPDATE expenses
SET status = 'actual'
WHERE expense_code = 'SQL-EXP-COMMITTED';

COMMIT;

DO $$
BEGIN
    BEGIN
        INSERT INTO expenses (
            expense_code,
            project_id,
            category,
            vendor_id,
            description,
            amount,
            expense_date,
            status,
            invoice_number,
            entered_by
        )
        SELECT
            'SQL-EXP-INVALID-DATE',
            project_id,
            'cloud',
            (
                SELECT vendor_id
                FROM vendors
                WHERE vendor_name = 'Cloud Provider'
            ),
            'Intentional date validation test',
            1000,
            DATE '2025-12-31',
            'actual',
            'INVALID-DATE-001',
            1
        FROM projects
        WHERE project_code = 'PRJ-SQL-001';

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Invalid project-period expense rejected: %',
                SQLERRM;
    END;
END;
$$;

DO $$
BEGIN
    BEGIN
        INSERT INTO expenses (
            expense_code,
            project_id,
            category,
            vendor_id,
            description,
            amount,
            expense_date,
            status,
            invoice_number,
            entered_by
        )
        SELECT
            'SQL-EXP-DUP-INVOICE',
            project_id,
            'cloud',
            (
                SELECT vendor_id
                FROM vendors
                WHERE vendor_name = 'Cloud Provider'
            ),
            'Intentional duplicate invoice test',
            500,
            DATE '2026-04-20',
            'actual',
            'CLOUD-SQL-001',
            1
        FROM projects
        WHERE project_code = 'PRJ-SQL-001';

    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE
                'Duplicate vendor invoice rejected by unique index.';
    END;
END;
$$;

SELECT
    e.expense_code,
    e.amount,
    e.expense_date,
    e.status,
    e.invoice_number
FROM expenses e
WHERE e.project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'PRJ-SQL-001'
)
ORDER BY e.expense_date, e.expense_id;
