-- Quality planning model for planning, verifying, and governing
-- measurable quality requirements for a software delivery project.
--
-- PostgreSQL-specific features used here:
--   identity columns
--   domains through CHECK constraints
--   foreign keys
--   partial indexes
--   trigger-based audit enforcement
--   PL/pgSQL functions
--   CTE-based quality evaluation
--   transactional sample workflow

DROP SCHEMA IF EXISTS quality_planning CASCADE;
CREATE SCHEMA quality_planning;

SET search_path = quality_planning, public;

CREATE TYPE requirement_state AS ENUM (
    'planned',
    'verified',
    'failed',
    'deferred'
);

CREATE TYPE risk_level AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE evidence_result AS ENUM (
    'pass',
    'fail'
);

CREATE TABLE projects (
    project_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name text NOT NULL UNIQUE,
    owner_name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE quality_requirements (
    requirement_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id bigint NOT NULL REFERENCES projects(project_id)
        ON DELETE CASCADE,
    requirement_code text NOT NULL,
    description text NOT NULL,
    metric_name text NOT NULL,
    target_percent numeric(5,2) NOT NULL,
    priority smallint NOT NULL,
    verification_method text NOT NULL,
    state requirement_state NOT NULL DEFAULT 'planned',
    UNIQUE (project_id, requirement_code),
    CHECK (btrim(description) <> ''),
    CHECK (target_percent BETWEEN 0 AND 100),
    CHECK (priority BETWEEN 1 AND 5),
    CHECK (btrim(metric_name) <> ''),
    CHECK (btrim(verification_method) <> '')
);

CREATE TABLE quality_evidence (
    evidence_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    requirement_id bigint NOT NULL
        REFERENCES quality_requirements(requirement_id)
        ON DELETE CASCADE,
    observed_percent numeric(5,2) NOT NULL,
    result evidence_result NOT NULL,
    evidence_source text NOT NULL,
    checked_at timestamptz NOT NULL DEFAULT now(),
    CHECK (observed_percent BETWEEN 0 AND 100),
    CHECK (btrim(evidence_source) <> '')
);

CREATE TABLE quality_risks (
    risk_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id bigint NOT NULL REFERENCES projects(project_id)
        ON DELETE CASCADE,
    risk_code text NOT NULL,
    description text NOT NULL,
    probability numeric(5,4) NOT NULL,
    impact numeric(5,4) NOT NULL,
    mitigation text NOT NULL,
    UNIQUE (project_id, risk_code),
    CHECK (probability BETWEEN 0 AND 1),
    CHECK (impact BETWEEN 0 AND 1),
    CHECK (btrim(description) <> ''),
    CHECK (btrim(mitigation) <> '')
);

CREATE TABLE quality_gate_decisions (
    decision_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id bigint NOT NULL REFERENCES projects(project_id)
        ON DELETE CASCADE,
    decision text NOT NULL CHECK (decision IN ('pass', 'blocked')),
    readiness_score numeric(6,2) NOT NULL,
    decision_reason text NOT NULL,
    decided_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_quality_evidence_requirement_checked
    ON quality_evidence (requirement_id, checked_at DESC);

CREATE INDEX idx_quality_requirements_project_state
    ON quality_requirements (project_id, state);

CREATE INDEX idx_quality_risks_project
    ON quality_risks (project_id);

CREATE OR REPLACE FUNCTION calculate_risk_level(
    probability numeric,
    impact numeric
)
RETURNS risk_level
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    score numeric;
BEGIN
    score := probability * impact;

    IF score >= 0.75 THEN
        RETURN 'critical';
    ELSIF score >= 0.50 THEN
        RETURN 'high';
    ELSIF score >= 0.25 THEN
        RETURN 'medium';
    END IF;

    RETURN 'low';
END;
$$;

CREATE OR REPLACE FUNCTION refresh_requirement_state()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE quality_requirements qr
    SET state =
        CASE
            WHEN NEW.result = 'pass' THEN 'verified'::requirement_state
            ELSE 'failed'::requirement_state
        END
    WHERE qr.requirement_id = NEW.requirement_id;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_refresh_requirement_state
AFTER INSERT ON quality_evidence
FOR EACH ROW
EXECUTE FUNCTION refresh_requirement_state();

CREATE OR REPLACE FUNCTION evaluate_project_quality(
    p_project_id bigint
)
RETURNS TABLE (
    project_id bigint,
    readiness_score numeric,
    missing_requirements bigint,
    failed_requirements bigint,
    critical_risks bigint,
    decision text
)
LANGUAGE sql
AS $$
WITH latest_evidence AS (
    SELECT DISTINCT ON (qe.requirement_id)
        qe.requirement_id,
        qe.observed_percent,
        qe.result
    FROM quality_evidence qe
    JOIN quality_requirements qr
      ON qr.requirement_id = qe.requirement_id
    WHERE qr.project_id = p_project_id
    ORDER BY qe.requirement_id, qe.checked_at DESC, qe.evidence_id DESC
),
requirement_evaluation AS (
    SELECT
        qr.requirement_id,
        qr.priority,
        qr.target_percent,
        le.observed_percent,
        le.result,
        CASE
            WHEN le.requirement_id IS NULL THEN 1
            ELSE 0
        END AS missing_flag,
        CASE
            WHEN le.result = 'fail' THEN 1
            ELSE 0
        END AS failed_flag,
        CASE
            WHEN le.observed_percent IS NULL OR qr.target_percent = 0 THEN 0
            ELSE LEAST(le.observed_percent / qr.target_percent, 1)
        END AS achievement
    FROM quality_requirements qr
    LEFT JOIN latest_evidence le
      ON le.requirement_id = qr.requirement_id
    WHERE qr.project_id = p_project_id
),
risk_evaluation AS (
    SELECT count(*) AS critical_count
    FROM quality_risks
    WHERE project_id = p_project_id
      AND calculate_risk_level(probability, impact) = 'critical'
),
score AS (
    SELECT
        COALESCE(
            ROUND(
                (
                    SUM(achievement * priority)
                    / NULLIF(SUM(priority), 0)
                ) * 100,
                2
            ),
            0
        ) AS readiness_score,
        SUM(missing_flag)::bigint AS missing_requirements,
        SUM(failed_flag)::bigint AS failed_requirements
    FROM requirement_evaluation
)
SELECT
    p_project_id,
    score.readiness_score,
    score.missing_requirements,
    score.failed_requirements,
    risk_evaluation.critical_count,
    CASE
        WHEN score.missing_requirements = 0
         AND score.failed_requirements = 0
         AND risk_evaluation.critical_count = 0
        THEN 'pass'
        ELSE 'blocked'
    END
FROM score
CROSS JOIN risk_evaluation;
$$;

CREATE OR REPLACE VIEW quality_requirement_status AS
SELECT
    p.project_name,
    qr.requirement_code,
    qr.description,
    qr.metric_name,
    qr.target_percent,
    qr.priority,
    qr.state,
    latest.observed_percent,
    latest.result,
    latest.checked_at
FROM projects p
JOIN quality_requirements qr
  ON qr.project_id = p.project_id
LEFT JOIN LATERAL (
    SELECT
        qe.observed_percent,
        qe.result,
        qe.checked_at
    FROM quality_evidence qe
    WHERE qe.requirement_id = qr.requirement_id
    ORDER BY qe.checked_at DESC, qe.evidence_id DESC
    LIMIT 1
) latest ON true;

CREATE OR REPLACE VIEW quality_risk_register AS
SELECT
    p.project_name,
    r.risk_code,
    r.description,
    r.probability,
    r.impact,
    ROUND(r.probability * r.impact, 4) AS risk_score,
    calculate_risk_level(r.probability, r.impact) AS risk_level,
    r.mitigation
FROM quality_risks r
JOIN projects p
  ON p.project_id = r.project_id;

INSERT INTO projects (project_name, owner_name)
VALUES ('Order Fulfillment Platform', 'Platform Engineering');

INSERT INTO quality_requirements (
    project_id,
    requirement_code,
    description,
    metric_name,
    target_percent,
    priority,
    verification_method
)
SELECT
    project_id,
    values_table.requirement_code,
    values_table.description,
    values_table.metric_name,
    values_table.target_percent,
    values_table.priority,
    values_table.verification_method
FROM projects p
CROSS JOIN (
    VALUES
    (
        'QR-301',
        'Critical order workflows must have adequate automated coverage.',
        'test_coverage',
        90.00,
        5,
        'CI coverage report'
    ),
    (
        'QR-302',
        'Order APIs must meet the agreed response-time objective.',
        'latency_compliance',
        95.00,
        5,
        'Load test'
    ),
    (
        'QR-303',
        'No critical order-integrity defects may remain before release.',
        'critical_defect_free',
        100.00,
        5,
        'Defect audit'
    ),
    (
        'QR-304',
        'Security-sensitive order inputs must pass validation tests.',
        'security_validation',
        100.00,
        4,
        'Security regression suite'
    )
) AS values_table(
    requirement_code,
    description,
    metric_name,
    target_percent,
    priority,
    verification_method
)
WHERE p.project_name = 'Order Fulfillment Platform';

-- Evidence is deliberately recorded at different quality levels.
-- QR-304 demonstrates a failed requirement that blocks the quality gate.
INSERT INTO quality_evidence (
    requirement_id,
    observed_percent,
    result,
    evidence_source
)
SELECT requirement_id, 93.00, 'pass', 'CI pipeline run 1842'
FROM quality_requirements
WHERE requirement_code = 'QR-301';

INSERT INTO quality_evidence (
    requirement_id,
    observed_percent,
    result,
    evidence_source
)
SELECT requirement_id, 97.00, 'pass', 'Load test run PERF-221'
FROM quality_requirements
WHERE requirement_code = 'QR-302';

INSERT INTO quality_evidence (
    requirement_id,
    observed_percent,
    result,
    evidence_source
)
SELECT requirement_id, 100.00, 'pass', 'Release defect audit AUD-119'
FROM quality_requirements
WHERE requirement_code = 'QR-303';

INSERT INTO quality_evidence (
    requirement_id,
    observed_percent,
    result,
    evidence_source
)
SELECT requirement_id, 97.00, 'fail', 'Security regression SEC-517'
FROM quality_requirements
WHERE requirement_code = 'QR-304';

INSERT INTO quality_risks (
    project_id,
    risk_code,
    description,
    probability,
    impact,
    mitigation
)
SELECT
    project_id,
    'R-301',
    'Malformed order values may bypass boundary validation.',
    0.45,
    0.90,
    'Expand malformed-input and boundary-value test coverage.'
FROM projects
WHERE project_name = 'Order Fulfillment Platform';

INSERT INTO quality_risks (
    project_id,
    risk_code,
    description,
    probability,
    impact,
    mitigation
)
SELECT
    project_id,
    'R-302',
    'Peak traffic may increase order-processing latency.',
    0.30,
    0.70,
    'Execute load tests against every release candidate.'
FROM projects
WHERE project_name = 'Order Fulfillment Platform';

-- The transaction demonstrates atomic decision recording:
-- the quality gate result is calculated and stored as one unit.
BEGIN;

WITH evaluation AS (
    SELECT *
    FROM evaluate_project_quality(
        (
            SELECT project_id
            FROM projects
            WHERE project_name = 'Order Fulfillment Platform'
        )
    )
)
INSERT INTO quality_gate_decisions (
    project_id,
    decision,
    readiness_score,
    decision_reason
)
SELECT
    project_id,
    decision,
    readiness_score,
    CASE
        WHEN decision = 'pass'
        THEN 'All planned requirements have passing evidence and no critical quality risks exist.'
        ELSE CONCAT(
            'Quality gate blocked: ',
            missing_requirements,
            ' missing requirements, ',
            failed_requirements,
            ' failed requirements, ',
            critical_risks,
            ' critical risks.'
        )
    END
FROM evaluation;

COMMIT;

-- Requirement-level validation report.
SELECT
    project_name,
    requirement_code,
    metric_name,
    target_percent,
    observed_percent,
    result,
    state
FROM quality_requirement_status
ORDER BY project_name, requirement_code;

-- Risk aggregation identifies the highest quality threats first.
SELECT
    project_name,
    risk_code,
    risk_score,
    risk_level,
    mitigation
FROM quality_risk_register
ORDER BY risk_score DESC, risk_code;

-- Project-level readiness calculation.
SELECT *
FROM evaluate_project_quality(
    (
        SELECT project_id
        FROM projects
        WHERE project_name = 'Order Fulfillment Platform'
    )
);

-- Stored quality-gate decisions provide an auditable release-planning record.
SELECT
    p.project_name,
    qgd.decision,
    qgd.readiness_score,
    qgd.decision_reason,
    qgd.decided_at
FROM quality_gate_decisions qgd
JOIN projects p
  ON p.project_id = qgd.project_id
ORDER BY qgd.decided_at DESC;

-- Demonstrate a CTE that finds requirements whose latest evidence
-- has not achieved their planned target.
WITH latest AS (
    SELECT DISTINCT ON (qe.requirement_id)
        qe.requirement_id,
        qe.observed_percent,
        qe.result
    FROM quality_evidence qe
    ORDER BY qe.requirement_id, qe.checked_at DESC, qe.evidence_id DESC
)
SELECT
    qr.requirement_code,
    qr.metric_name,
    qr.target_percent,
    latest.observed_percent,
    latest.result
FROM quality_requirements qr
JOIN latest
  ON latest.requirement_id = qr.requirement_id
WHERE latest.observed_percent < qr.target_percent
ORDER BY qr.priority DESC, qr.requirement_code;
