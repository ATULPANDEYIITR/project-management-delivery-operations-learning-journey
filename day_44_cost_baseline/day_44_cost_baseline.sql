-- Cost Baseline: Understanding Planned Spending
-- PostgreSQL 15+
--
-- This script models an approved time-phased budget, work-package estimates,
-- cost transactions, measured progress, earned-value metrics, and controlled
-- baseline changes. Monetary values use NUMERIC rather than floating point.

BEGIN;

DROP SCHEMA IF EXISTS cost_baseline_lab CASCADE;
CREATE SCHEMA cost_baseline_lab;
SET search_path TO cost_baseline_lab, public;

CREATE TYPE baseline_status AS ENUM ('DRAFT', 'APPROVED', 'SUPERSEDED');
CREATE TYPE cost_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED');
CREATE TYPE change_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED');

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (btrim(project_code) <> ''),
    CHECK (btrim(project_name) <> ''),
    CHECK (currency_code = 'INR')
);

CREATE TABLE project_baselines (
    baseline_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    revision_number INTEGER NOT NULL CHECK (revision_number > 0),
    baseline_name TEXT NOT NULL,
    status baseline_status NOT NULL DEFAULT 'DRAFT',
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    supersedes_baseline_id BIGINT REFERENCES project_baselines(baseline_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, revision_number),
    UNIQUE (baseline_id, project_id),
    CHECK (
        (status = 'DRAFT' AND approved_by IS NULL AND approved_at IS NULL)
        OR
        (status IN ('APPROVED', 'SUPERSEDED')
         AND approved_by IS NOT NULL AND approved_at IS NOT NULL)
    ),
    CHECK (supersedes_baseline_id IS NULL OR supersedes_baseline_id <> baseline_id)
);

-- A project can have only one currently approved baseline.
CREATE UNIQUE INDEX one_approved_baseline_per_project
    ON project_baselines(project_id)
    WHERE status = 'APPROVED';

CREATE TABLE work_packages (
    package_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    baseline_id BIGINT NOT NULL REFERENCES project_baselines(baseline_id),
    package_code TEXT NOT NULL,
    package_name TEXT NOT NULL,
    planned_estimate NUMERIC(14, 2) NOT NULL CHECK (planned_estimate >= 0),
    UNIQUE (baseline_id, package_code),
    UNIQUE (package_id, baseline_id),
    CHECK (btrim(package_code) <> ''),
    CHECK (btrim(package_name) <> '')
);

CREATE TABLE budget_allocations (
    allocation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    baseline_id BIGINT NOT NULL,
    package_id BIGINT NOT NULL,
    budget_month DATE NOT NULL,
    planned_amount NUMERIC(14, 2) NOT NULL CHECK (planned_amount >= 0),
    FOREIGN KEY (package_id, baseline_id)
        REFERENCES work_packages(package_id, baseline_id),
    UNIQUE (package_id, budget_month),
    CHECK (EXTRACT(DAY FROM budget_month) = 1)
);

CREATE TABLE cost_transactions (
    cost_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_reference TEXT NOT NULL UNIQUE,
    package_id BIGINT NOT NULL REFERENCES work_packages(package_id),
    cost_date DATE NOT NULL,
    cost_amount NUMERIC(14, 2) NOT NULL CHECK (cost_amount >= 0),
    description TEXT NOT NULL,
    status cost_status NOT NULL DEFAULT 'PENDING',
    recorded_by TEXT NOT NULL,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    CHECK (btrim(source_reference) <> ''),
    CHECK (btrim(description) <> ''),
    CHECK (btrim(recorded_by) <> ''),
    CHECK (
        (status = 'APPROVED' AND approved_by IS NOT NULL AND approved_at IS NOT NULL)
        OR
        (status <> 'APPROVED' AND approved_by IS NULL AND approved_at IS NULL)
    )
);

CREATE TABLE progress_observations (
    progress_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    package_id BIGINT NOT NULL REFERENCES work_packages(package_id),
    reporting_month DATE NOT NULL,
    completion_percent NUMERIC(5, 2) NOT NULL
        CHECK (completion_percent BETWEEN 0 AND 100),
    verified_by TEXT NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (package_id, reporting_month),
    CHECK (EXTRACT(DAY FROM reporting_month) = 1),
    CHECK (btrim(verified_by) <> '')
);

CREATE TABLE change_requests (
    change_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    baseline_id BIGINT NOT NULL REFERENCES project_baselines(baseline_id),
    request_code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    amount_delta NUMERIC(14, 2) NOT NULL CHECK (amount_delta <> 0),
    effective_month DATE NOT NULL,
    status change_status NOT NULL DEFAULT 'PENDING',
    requested_by TEXT NOT NULL,
    decided_by TEXT,
    decided_at TIMESTAMPTZ,
    decision_note TEXT,
    CHECK (EXTRACT(DAY FROM effective_month) = 1),
    CHECK (btrim(description) <> ''),
    CHECK (btrim(requested_by) <> ''),
    CHECK (
        (status = 'PENDING'
         AND decided_by IS NULL
         AND decided_at IS NULL
         AND decision_note IS NULL)
        OR
        (status IN ('APPROVED', 'REJECTED')
         AND decided_by IS NOT NULL
         AND decided_at IS NOT NULL
         AND decision_note IS NOT NULL)
    )
);

CREATE INDEX allocation_month_idx
    ON budget_allocations(baseline_id, budget_month);

CREATE INDEX approved_cost_period_idx
    ON cost_transactions(cost_date, package_id)
    WHERE status = 'APPROVED';

CREATE INDEX progress_period_idx
    ON progress_observations(reporting_month, package_id);

CREATE INDEX pending_change_idx
    ON change_requests(baseline_id, effective_month)
    WHERE status = 'PENDING';

-- Prevent approval without complete work-package allocations.
-- The validation is deferred because package and allocation rows are inserted
-- separately in the same transaction.
CREATE FUNCTION validate_baseline_allocations()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    target_baseline BIGINT;
    package_row RECORD;
    allocated NUMERIC(14, 2);
BEGIN
    target_baseline := COALESCE(NEW.baseline_id, OLD.baseline_id);

    IF NOT EXISTS (
        SELECT 1
        FROM project_baselines
        WHERE baseline_id = target_baseline
          AND status IN ('APPROVED', 'SUPERSEDED')
    ) THEN
        RETURN NULL;
    END IF;

    FOR package_row IN
        SELECT package_id, planned_estimate
        FROM work_packages
        WHERE baseline_id = target_baseline
    LOOP
        SELECT COALESCE(SUM(planned_amount), 0)
        INTO allocated
        FROM budget_allocations
        WHERE package_id = package_row.package_id;

        IF allocated <> package_row.planned_estimate THEN
            RAISE EXCEPTION
                'Allocation mismatch for package %, expected %, found %',
                package_row.package_id,
                package_row.planned_estimate,
                allocated;
        END IF;
    END LOOP;

    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER package_allocation_consistency
AFTER INSERT OR UPDATE OR DELETE ON budget_allocations
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION validate_baseline_allocations();

CREATE CONSTRAINT TRIGGER package_estimate_consistency
AFTER INSERT OR UPDATE OR DELETE ON work_packages
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION validate_baseline_allocations();

-- Approved baselines and their planned spending are historical records.
-- New spending plans should be represented by a new baseline revision.
CREATE FUNCTION prevent_approved_baseline_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    target_baseline BIGINT;
    current_status baseline_status;
BEGIN
    target_baseline := COALESCE(NEW.baseline_id, OLD.baseline_id);

    SELECT status
    INTO current_status
    FROM project_baselines
    WHERE baseline_id = target_baseline;

    IF current_status IN ('APPROVED', 'SUPERSEDED') THEN
        RAISE EXCEPTION
            'Cannot alter allocations or package definitions for a finalized baseline';
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER protect_finalized_allocations
BEFORE INSERT OR UPDATE OR DELETE ON budget_allocations
FOR EACH ROW EXECUTE FUNCTION prevent_approved_baseline_mutation();

CREATE TRIGGER protect_finalized_packages
BEFORE INSERT OR UPDATE OR DELETE ON work_packages
FOR EACH ROW EXECUTE FUNCTION prevent_approved_baseline_mutation();

-- Enforce non-decreasing verified progress across reporting periods.
CREATE FUNCTION validate_progress_sequence()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    previous_completion NUMERIC(5, 2);
BEGIN
    SELECT completion_percent
    INTO previous_completion
    FROM progress_observations
    WHERE package_id = NEW.package_id
      AND reporting_month < NEW.reporting_month
    ORDER BY reporting_month DESC
    LIMIT 1;

    IF previous_completion IS NOT NULL
       AND NEW.completion_percent < previous_completion THEN
        RAISE EXCEPTION
            'Completion for package % cannot decrease from % to %',
            NEW.package_id,
            previous_completion,
            NEW.completion_percent;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER progress_sequence_guard
BEFORE INSERT OR UPDATE ON progress_observations
FOR EACH ROW EXECUTE FUNCTION validate_progress_sequence();

-- Aggregate baseline totals by reporting month.
CREATE VIEW monthly_planned_spending AS
SELECT
    ba.baseline_id,
    ba.budget_month,
    SUM(ba.planned_amount)::NUMERIC(14, 2) AS planned_amount
FROM budget_allocations AS ba
GROUP BY ba.baseline_id, ba.budget_month;

CREATE VIEW package_budget_reconciliation AS
SELECT
    wp.baseline_id,
    wp.package_code,
    wp.planned_estimate,
    COALESCE(SUM(ba.planned_amount), 0)::NUMERIC(14, 2) AS allocated_amount,
    wp.planned_estimate
        - COALESCE(SUM(ba.planned_amount), 0)::NUMERIC(14, 2)
        AS allocation_difference
FROM work_packages AS wp
LEFT JOIN budget_allocations AS ba
    ON ba.package_id = wp.package_id
GROUP BY wp.baseline_id, wp.package_code, wp.planned_estimate;

INSERT INTO projects (project_code, project_name)
VALUES ('HOSP-2026', 'District Hospital Modernization');

INSERT INTO project_baselines (
    project_id, revision_number, baseline_name
)
SELECT project_id, 1, 'Original approved cost baseline'
FROM projects
WHERE project_code = 'HOSP-2026';

INSERT INTO work_packages (
    baseline_id, package_code, package_name, planned_estimate
)
SELECT b.baseline_id, item.package_code, item.package_name, item.planned_estimate
FROM project_baselines AS b
JOIN projects AS p ON p.project_id = b.project_id
CROSS JOIN (
    VALUES
        ('CIVIL', 'Civil works', 450000.00::NUMERIC),
        ('ELECT', 'Electrical installation', 300000.00::NUMERIC),
        ('TEST', 'Testing and commissioning', 250000.00::NUMERIC)
) AS item(package_code, package_name, planned_estimate)
WHERE p.project_code = 'HOSP-2026'
  AND b.revision_number = 1;

INSERT INTO budget_allocations (
    baseline_id, package_id, budget_month, planned_amount
)
SELECT wp.baseline_id, wp.package_id, item.budget_month, item.amount
FROM work_packages AS wp
JOIN project_baselines AS b ON b.baseline_id = wp.baseline_id
JOIN projects AS p ON p.project_id = b.project_id
JOIN (
    VALUES
        ('CIVIL', DATE '2026-01-01', 150000.00::NUMERIC),
        ('CIVIL', DATE '2026-02-01', 180000.00::NUMERIC),
        ('CIVIL', DATE '2026-03-01', 120000.00::NUMERIC),
        ('ELECT', DATE '2026-02-01', 50000.00::NUMERIC),
        ('ELECT', DATE '2026-03-01', 150000.00::NUMERIC),
        ('ELECT', DATE '2026-04-01', 100000.00::NUMERIC),
        ('TEST', DATE '2026-03-01', 50000.00::NUMERIC),
        ('TEST', DATE '2026-04-01', 100000.00::NUMERIC),
        ('TEST', DATE '2026-05-01', 100000.00::NUMERIC)
) AS item(package_code, budget_month, amount)
    ON item.package_code = wp.package_code
WHERE p.project_code = 'HOSP-2026'
  AND b.revision_number = 1;

-- Approve only after all work-package allocations are present.
UPDATE project_baselines
SET status = 'APPROVED',
    approved_by = 'Project Director',
    approved_at = TIMESTAMPTZ '2025-12-20 10:00:00+05:30'
WHERE revision_number = 1
  AND project_id = (
      SELECT project_id FROM projects WHERE project_code = 'HOSP-2026'
  );

INSERT INTO cost_transactions (
    source_reference, package_id, cost_date, cost_amount,
    description, status, recorded_by, approved_by, approved_at
)
SELECT
    item.source_reference,
    wp.package_id,
    item.cost_date,
    item.cost_amount,
    item.description,
    item.status::cost_status,
    'Cost Controller',
    CASE WHEN item.status = 'APPROVED' THEN 'Finance Controller' END,
    CASE WHEN item.status = 'APPROVED'
         THEN TIMESTAMPTZ '2026-03-31 17:00:00+05:30' END
FROM (
    VALUES
        ('INV-101', 'CIVIL', DATE '2026-01-15', 140000.00::NUMERIC,
         'Site preparation', 'APPROVED'),
        ('INV-102', 'CIVIL', DATE '2026-02-15', 200000.00::NUMERIC,
         'Structural work', 'APPROVED'),
        ('INV-103', 'ELECT', DATE '2026-02-18', 60000.00::NUMERIC,
         'Cable procurement', 'APPROVED'),
        ('INV-104', 'CIVIL', DATE '2026-03-12', 130000.00::NUMERIC,
         'Civil completion', 'APPROVED'),
        ('INV-105', 'ELECT', DATE '2026-03-18', 140000.00::NUMERIC,
         'Electrical installation', 'APPROVED'),
        ('INV-106', 'TEST', DATE '2026-03-25', 30000.00::NUMERIC,
         'Pre-commissioning tests', 'APPROVED'),
        ('INV-107', 'TEST', DATE '2026-03-27', 25000.00::NUMERIC,
         'Unapproved supplier claim', 'PENDING')
) AS item(source_reference, package_code, cost_date, cost_amount, description, status)
JOIN work_packages AS wp ON wp.package_code = item.package_code
JOIN project_baselines AS b ON b.baseline_id = wp.baseline_id
WHERE b.status = 'APPROVED';

INSERT INTO progress_observations (
    package_id, reporting_month, completion_percent, verified_by
)
SELECT
    wp.package_id,
    item.reporting_month,
    item.completion_percent,
    'Site Engineer'
FROM (
    VALUES
        ('CIVIL', DATE '2026-01-01', 30.00::NUMERIC),
        ('CIVIL', DATE '2026-02-01', 70.00::NUMERIC),
        ('CIVIL', DATE '2026-03-01', 100.00::NUMERIC),
        ('ELECT', DATE '2026-02-01', 10.00::NUMERIC),
        ('ELECT', DATE '2026-03-01', 55.00::NUMERIC),
        ('TEST', DATE '2026-03-01', 10.00::NUMERIC)
) AS item(package_code, reporting_month, completion_percent)
JOIN work_packages AS wp ON wp.package_code = item.package_code
JOIN project_baselines AS b ON b.baseline_id = wp.baseline_id
WHERE b.status = 'APPROVED';

INSERT INTO change_requests (
    baseline_id, request_code, description, amount_delta,
    effective_month, requested_by
)
SELECT
    baseline_id,
    'CR-014',
    'Additional electrical safety panels',
    50000.00,
    DATE '2026-05-01',
    'Electrical Project Manager'
FROM project_baselines
WHERE revision_number = 1;

-- Evaluate the project through March 2026.
-- EV uses the latest verified progress per package up to the reporting month.
-- PV uses the approved time-phased allocation; AC excludes pending/rejected costs.
WITH selected_baseline AS (
    SELECT b.baseline_id, b.project_id
    FROM project_baselines AS b
    JOIN projects AS p ON p.project_id = b.project_id
    WHERE p.project_code = 'HOSP-2026'
      AND b.status = 'APPROVED'
),
bac AS (
    SELECT
        wp.baseline_id,
        SUM(wp.planned_estimate)::NUMERIC(14, 2) AS bac
    FROM work_packages AS wp
    JOIN selected_baseline AS sb ON sb.baseline_id = wp.baseline_id
    GROUP BY wp.baseline_id
),
pv AS (
    SELECT
        sb.baseline_id,
        COALESCE(SUM(ba.planned_amount), 0)::NUMERIC(14, 2) AS pv
    FROM selected_baseline AS sb
    LEFT JOIN budget_allocations AS ba
        ON ba.baseline_id = sb.baseline_id
       AND ba.budget_month <= DATE '2026-03-01'
    GROUP BY sb.baseline_id
),
ac AS (
    SELECT
        sb.baseline_id,
        COALESCE(SUM(ct.cost_amount), 0)::NUMERIC(14, 2) AS ac
    FROM selected_baseline AS sb
    JOIN work_packages AS wp ON wp.baseline_id = sb.baseline_id
    LEFT JOIN cost_transactions AS ct
        ON ct.package_id = wp.package_id
       AND ct.cost_date < DATE '2026-04-01'
       AND ct.status = 'APPROVED'
    GROUP BY sb.baseline_id
),
latest_progress AS (
    SELECT DISTINCT ON (po.package_id)
        po.package_id,
        po.completion_percent
    FROM progress_observations AS po
    JOIN work_packages AS wp ON wp.package_id = po.package_id
    JOIN selected_baseline AS sb ON sb.baseline_id = wp.baseline_id
    WHERE po.reporting_month <= DATE '2026-03-01'
    ORDER BY po.package_id, po.reporting_month DESC
),
ev AS (
    SELECT
        sb.baseline_id,
        COALESCE(
            SUM(wp.planned_estimate * COALESCE(lp.completion_percent, 0) / 100),
            0
        )::NUMERIC(14, 2) AS ev
    FROM selected_baseline AS sb
    JOIN work_packages AS wp ON wp.baseline_id = sb.baseline_id
    LEFT JOIN latest_progress AS lp ON lp.package_id = wp.package_id
    GROUP BY sb.baseline_id
),
metrics AS (
    SELECT
        bac.baseline_id,
        bac.bac,
        pv.pv,
        ev.ev,
        ac.ac,
        (ev.ev - ac.ac)::NUMERIC(14, 2) AS cv,
        (ev.ev - pv.pv)::NUMERIC(14, 2) AS sv
    FROM bac
    JOIN pv USING (baseline_id)
    JOIN ev USING (baseline_id)
    JOIN ac USING (baseline_id)
)
SELECT
    baseline_id,
    bac AS budget_at_completion,
    pv AS planned_value,
    ev AS earned_value,
    ac AS actual_cost,
    cv AS cost_variance,
    sv AS schedule_variance,
    ROUND(ev / NULLIF(ac, 0), 4) AS cost_performance_index,
    ROUND(ev / NULLIF(pv, 0), 4) AS schedule_performance_index,
    ROUND(bac / NULLIF(ev / NULLIF(ac, 0), 0), 2) AS estimate_at_completion
FROM metrics;

-- Inspect whether any package has a mismatch between its estimate and allocations.
SELECT *
FROM package_budget_reconciliation
ORDER BY package_code;

-- Inspect the monthly planned-spending curve.
SELECT budget_month, planned_amount
FROM monthly_planned_spending
WHERE baseline_id = (
    SELECT baseline_id
    FROM project_baselines
    WHERE revision_number = 1
)
ORDER BY budget_month;

-- Show approved spending separately from pending and rejected claims.
SELECT
    status,
    COUNT(*) AS transaction_count,
    SUM(cost_amount)::NUMERIC(14, 2) AS amount
FROM cost_transactions
GROUP BY status
ORDER BY status;

-- Change approval does not rewrite the approved baseline.
UPDATE change_requests
SET status = 'APPROVED',
    decided_by = 'Project Director',
    decided_at = TIMESTAMPTZ '2026-04-01 10:00:00+05:30',
    decision_note = 'Approved for safety compliance; create a formal revision.'
WHERE request_code = 'CR-014'
  AND status = 'PENDING';

SELECT
    request_code,
    amount_delta,
    status,
    decision_note
FROM change_requests
WHERE request_code = 'CR-014';

-- The current baseline remains one million rupees until a new revision
-- has its own work packages, allocations, validation, and approval.
SELECT
    b.revision_number,
    b.status,
    SUM(wp.planned_estimate)::NUMERIC(14, 2) AS budget_at_completion
FROM project_baselines AS b
JOIN work_packages AS wp ON wp.baseline_id = b.baseline_id
GROUP BY b.baseline_id, b.revision_number, b.status
ORDER BY b.revision_number;

COMMIT;
