BEGIN;

CREATE SCHEMA IF NOT EXISTS quality_control;
SET LOCAL search_path TO quality_control, public;

CREATE TYPE output_status AS ENUM (
    'draft', 'inspection', 'rework', 'released', 'rejected'
);

CREATE TYPE finding_severity AS ENUM (
    'critical', 'major', 'minor', 'observation'
);

CREATE TYPE finding_status AS ENUM (
    'open', 'fixed', 'verified', 'accepted'
);

CREATE TYPE inspection_status AS ENUM (
    'passed', 'failed'
);

CREATE TABLE projects (
    project_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code text NOT NULL UNIQUE,
    project_name text NOT NULL,
    owner_name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (btrim(project_code) <> ''),
    CHECK (btrim(project_name) <> ''),
    CHECK (btrim(owner_name) <> '')
);

CREATE TABLE project_outputs (
    output_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id bigint NOT NULL REFERENCES projects(project_id),
    output_name text NOT NULL,
    version text NOT NULL,
    artifact_uri text NOT NULL,
    status output_status NOT NULL DEFAULT 'draft',
    created_at timestamptz NOT NULL DEFAULT now(),
    released_at timestamptz,
    UNIQUE (project_id, output_name, version),
    CHECK (btrim(output_name) <> ''),
    CHECK (btrim(version) <> ''),
    CHECK (btrim(artifact_uri) <> ''),
    CHECK (
        (status = 'released' AND released_at IS NOT NULL)
        OR (status <> 'released' AND released_at IS NULL)
    )
);

CREATE TABLE quality_requirements (
    requirement_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id bigint NOT NULL REFERENCES projects(project_id),
    requirement_code text NOT NULL,
    description text NOT NULL,
    mandatory boolean NOT NULL DEFAULT true,
    UNIQUE (project_id, requirement_code),
    CHECK (btrim(requirement_code) <> ''),
    CHECK (btrim(description) <> '')
);

CREATE TABLE inspections (
    inspection_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    output_id bigint NOT NULL REFERENCES project_outputs(output_id),
    inspector text NOT NULL,
    inspected_at timestamptz NOT NULL DEFAULT now(),
    status inspection_status NOT NULL,
    notes text NOT NULL DEFAULT '',
    CHECK (btrim(inspector) <> '')
);

CREATE TABLE inspection_results (
    result_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    inspection_id bigint NOT NULL REFERENCES inspections(inspection_id),
    requirement_id bigint NOT NULL REFERENCES quality_requirements(requirement_id),
    passed boolean NOT NULL,
    evidence text NOT NULL DEFAULT '',
    UNIQUE (inspection_id, requirement_id)
);

CREATE TABLE quality_findings (
    finding_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    inspection_id bigint NOT NULL REFERENCES inspections(inspection_id),
    requirement_id bigint NOT NULL REFERENCES quality_requirements(requirement_id),
    severity finding_severity NOT NULL,
    description text NOT NULL,
    evidence text NOT NULL DEFAULT '',
    status finding_status NOT NULL DEFAULT 'open',
    assigned_to text,
    created_at timestamptz NOT NULL DEFAULT now(),
    fixed_at timestamptz,
    verified_at timestamptz,
    CHECK (btrim(description) <> ''),
    CHECK (
        (status = 'verified' AND verified_at IS NOT NULL)
        OR (status <> 'verified' AND verified_at IS NULL)
    ),
    CHECK (
        (status IN ('fixed', 'verified') AND fixed_at IS NOT NULL)
        OR (status NOT IN ('fixed', 'verified') AND fixed_at IS NULL)
    )
);

CREATE TABLE quality_audit (
    audit_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    output_id bigint NOT NULL REFERENCES project_outputs(output_id),
    event_type text NOT NULL,
    actor text NOT NULL,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    CHECK (btrim(event_type) <> ''),
    CHECK (btrim(actor) <> '')
);

CREATE INDEX idx_outputs_project_status
    ON project_outputs(project_id, status);

CREATE INDEX idx_inspections_output_latest
    ON inspections(output_id, inspected_at DESC, inspection_id DESC);

CREATE INDEX idx_findings_open_severity
    ON quality_findings(inspection_id, severity)
    WHERE status = 'open';

CREATE INDEX idx_audit_output_time
    ON quality_audit(output_id, occurred_at DESC);

CREATE OR REPLACE FUNCTION enforce_finding_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'open' THEN
            RAISE EXCEPTION 'New findings must start open';
        END IF;
        RETURN NEW;
    END IF;

    IF OLD.status = 'verified' AND NEW.status <> 'verified' THEN
        RAISE EXCEPTION 'Verified findings are immutable in status';
    END IF;

    IF NEW.status <> OLD.status THEN
        IF NOT (
            (OLD.status = 'open' AND NEW.status IN ('fixed', 'accepted'))
            OR (OLD.status = 'fixed' AND NEW.status IN ('verified', 'open'))
            OR (OLD.status = 'accepted' AND NEW.status = 'open')
        ) THEN
            RAISE EXCEPTION 'Invalid finding transition: % -> %',
                OLD.status, NEW.status;
        END IF;

        IF NEW.status = 'fixed' THEN
            NEW.fixed_at := COALESCE(NEW.fixed_at, now());
        ELSIF NEW.status = 'verified' THEN
            IF OLD.status <> 'fixed' THEN
                RAISE EXCEPTION 'Only fixed findings can be verified';
            END IF;
            NEW.fixed_at := COALESCE(NEW.fixed_at, now());
            NEW.verified_at := COALESCE(NEW.verified_at, now());
        ELSIF NEW.status IN ('open', 'accepted') THEN
            NEW.fixed_at := NULL;
            NEW.verified_at := NULL;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER quality_finding_transition
BEFORE INSERT OR UPDATE OF status ON quality_findings
FOR EACH ROW EXECUTE FUNCTION enforce_finding_transition();

CREATE OR REPLACE FUNCTION enforce_output_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;

    IF OLD.status IN ('released', 'rejected') THEN
        RAISE EXCEPTION 'Terminal output state cannot be changed';
    END IF;

    IF NEW.status = 'released' THEN
        IF OLD.status <> 'inspection' THEN
            RAISE EXCEPTION 'Output must be in inspection state before release';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM inspections i
            WHERE i.output_id = NEW.output_id
              AND i.status = 'passed'
              AND (i.inspected_at, i.inspection_id) = (
                  SELECT i2.inspected_at, i2.inspection_id
                  FROM inspections i2
                  WHERE i2.output_id = NEW.output_id
                  ORDER BY i2.inspected_at DESC, i2.inspection_id DESC
                  LIMIT 1
              )
        ) THEN
            RAISE EXCEPTION 'Latest inspection must pass before release';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM inspections i
            JOIN quality_findings f USING (inspection_id)
            WHERE i.output_id = NEW.output_id
              AND f.status = 'open'
              AND f.severity IN ('critical', 'major')
        ) THEN
            RAISE EXCEPTION 'Unresolved critical or major findings block release';
        END IF;

        NEW.released_at := COALESCE(NEW.released_at, now());
    ELSE
        NEW.released_at := NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER project_output_transition
BEFORE UPDATE OF status ON project_outputs
FOR EACH ROW EXECUTE FUNCTION enforce_output_transition();

CREATE OR REPLACE FUNCTION record_output_audit()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    actor_name text;
BEGIN
    IF TG_OP = 'INSERT' THEN
        actor_name := current_user;
        INSERT INTO quality_audit(output_id, event_type, actor, details)
        VALUES (
            NEW.output_id,
            'output.created',
            actor_name,
            jsonb_build_object(
                'name', NEW.output_name,
                'version', NEW.version,
                'status', NEW.status
            )
        );
        RETURN NEW;
    END IF;

    IF NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO quality_audit(output_id, event_type, actor, details)
        VALUES (
            NEW.output_id,
            'output.status_changed',
            current_user,
            jsonb_build_object(
                'from', OLD.status,
                'to', NEW.status
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER project_output_audit
AFTER INSERT OR UPDATE OF status ON project_outputs
FOR EACH ROW EXECUTE FUNCTION record_output_audit();

-- The view exposes inspection evidence and findings without changing workflow state.
CREATE VIEW inspection_detail AS
SELECT
    p.project_code,
    o.output_id,
    o.output_name,
    o.version,
    o.status AS output_status,
    i.inspection_id,
    i.inspector,
    i.inspected_at,
    i.status AS inspection_status,
    r.requirement_code,
    r.description AS requirement_description,
    r.mandatory,
    ir.passed AS requirement_passed,
    ir.evidence AS result_evidence,
    f.finding_id,
    f.severity,
    f.status AS finding_status,
    f.description AS finding_description
FROM project_outputs o
JOIN projects p USING (project_id)
LEFT JOIN inspections i USING (output_id)
LEFT JOIN inspection_results ir USING (inspection_id)
LEFT JOIN quality_requirements r
    ON r.requirement_id = ir.requirement_id
LEFT JOIN quality_findings f
    ON f.inspection_id = i.inspection_id
   AND f.requirement_id = r.requirement_id;

CREATE OR REPLACE FUNCTION evaluate_output(p_output_id bigint)
RETURNS TABLE (
    eligible boolean,
    latest_inspection_id bigint,
    blocking_findings bigint,
    missing_mandatory_checks bigint,
    decision text
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_project_id bigint;
    v_status output_status;
    v_latest_id bigint;
    v_latest_status inspection_status;
    v_blocking bigint;
    v_missing bigint;
BEGIN
    SELECT o.project_id, o.status
    INTO v_project_id, v_status
    FROM project_outputs o
    WHERE o.output_id = p_output_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Output % does not exist', p_output_id;
    END IF;

    SELECT i.inspection_id, i.status
    INTO v_latest_id, v_latest_status
    FROM inspections i
    WHERE i.output_id = p_output_id
    ORDER BY i.inspected_at DESC, i.inspection_id DESC
    LIMIT 1;

    SELECT count(*)
    INTO v_blocking
    FROM inspections i
    JOIN quality_findings f USING (inspection_id)
    WHERE i.output_id = p_output_id
      AND f.status = 'open'
      AND f.severity IN ('critical', 'major');

    SELECT count(*)
    INTO v_missing
    FROM quality_requirements r
    WHERE r.project_id = v_project_id
      AND r.mandatory
      AND (
          v_latest_id IS NULL
          OR NOT EXISTS (
              SELECT 1
              FROM inspection_results ir
              WHERE ir.inspection_id = v_latest_id
                AND ir.requirement_id = r.requirement_id
          )
      );

    eligible := (
        v_status = 'inspection'
        AND v_latest_id IS NOT NULL
        AND v_latest_status = 'passed'
        AND v_blocking = 0
        AND v_missing = 0
    );

    latest_inspection_id := v_latest_id;
    blocking_findings := v_blocking;
    missing_mandatory_checks := v_missing;
    decision := CASE
        WHEN v_status = 'released' THEN 'Already released'
        WHEN v_status = 'rejected' THEN 'Output rejected'
        WHEN v_latest_id IS NULL THEN 'Inspection required'
        WHEN v_missing > 0 THEN 'Mandatory checks missing'
        WHEN v_blocking > 0 THEN 'Blocking findings remain open'
        WHEN v_latest_status <> 'passed' THEN 'Latest inspection failed'
        WHEN v_status <> 'inspection' THEN 'Output is not in inspection state'
        ELSE 'Eligible for release'
    END;

    RETURN NEXT;
END;
$$;

CREATE OR REPLACE FUNCTION complete_inspection(
    p_output_id bigint,
    p_inspector text,
    p_results jsonb,
    p_notes text DEFAULT ''
)
RETURNS bigint
LANGUAGE plpgsql
AS $$
DECLARE
    v_project_id bigint;
    v_inspection_id bigint;
    v_requirement record;
    v_result jsonb;
    v_passed boolean;
    v_evidence text;
    v_status inspection_status;
    v_findings integer := 0;
BEGIN
    IF p_inspector IS NULL OR btrim(p_inspector) = '' THEN
        RAISE EXCEPTION 'Inspector identity is required';
    END IF;
    IF jsonb_typeof(p_results) <> 'object' THEN
        RAISE EXCEPTION 'Inspection results must be a JSON object';
    END IF;

    SELECT project_id
    INTO v_project_id
    FROM project_outputs
    WHERE output_id = p_output_id
      AND status IN ('draft', 'inspection', 'rework')
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Output is missing or cannot be inspected';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM jsonb_object_keys(p_results) AS supplied(code)
        WHERE NOT EXISTS (
            SELECT 1
            FROM quality_requirements r
            WHERE r.project_id = v_project_id
              AND r.requirement_code = supplied.code
        )
    ) THEN
        RAISE EXCEPTION 'Results contain unknown requirement codes';
    END IF;

    INSERT INTO inspections(output_id, inspector, status, notes)
    VALUES (p_output_id, p_inspector, 'passed', COALESCE(p_notes, ''))
    RETURNING inspection_id INTO v_inspection_id;

    FOR v_requirement IN
        SELECT requirement_id, requirement_code, description, mandatory
        FROM quality_requirements
        WHERE project_id = v_project_id
        ORDER BY requirement_id
    LOOP
        v_result := p_results -> v_requirement.requirement_code;

        IF v_result IS NULL THEN
            IF v_requirement.mandatory THEN
                INSERT INTO quality_findings(
                    inspection_id, requirement_id, severity,
                    description, evidence
                )
                VALUES (
                    v_inspection_id, v_requirement.requirement_id,
                    'major', 'Mandatory requirement was not checked', ''
                );
                v_findings := v_findings + 1;
            END IF;
            CONTINUE;
        END IF;

        IF jsonb_typeof(v_result -> 'passed') <> 'boolean' THEN
            RAISE EXCEPTION 'Result for % requires a boolean passed field',
                v_requirement.requirement_code;
        END IF;

        v_passed := (v_result ->> 'passed')::boolean;
        v_evidence := COALESCE(v_result ->> 'evidence', '');

        INSERT INTO inspection_results(
            inspection_id, requirement_id, passed, evidence
        )
        VALUES (
            v_inspection_id, v_requirement.requirement_id,
            v_passed, v_evidence
        );

        IF NOT v_passed THEN
            INSERT INTO quality_findings(
                inspection_id, requirement_id, severity,
                description, evidence
            )
            VALUES (
                v_inspection_id,
                v_requirement.requirement_id,
                CASE WHEN v_requirement.mandatory THEN 'major'::finding_severity
                     ELSE 'minor'::finding_severity END,
                v_requirement.description,
                v_evidence
            );
            v_findings := v_findings + 1;
        END IF;
    END LOOP;

    IF EXISTS (
        SELECT 1
        FROM quality_findings f
        WHERE f.inspection_id = v_inspection_id
          AND f.status = 'open'
          AND f.severity IN ('critical', 'major')
    ) THEN
        v_status := 'failed';
        UPDATE project_outputs
        SET status = 'rework'
        WHERE output_id = p_output_id;
    ELSE
        v_status := 'passed';
        UPDATE project_outputs
        SET status = 'inspection'
        WHERE output_id = p_output_id;
    END IF;

    UPDATE inspections
    SET status = v_status
    WHERE inspection_id = v_inspection_id;

    INSERT INTO quality_audit(output_id, event_type, actor, details)
    VALUES (
        p_output_id,
        'inspection.completed',
        p_inspector,
        jsonb_build_object(
            'inspection_id', v_inspection_id,
            'status', v_status,
            'finding_count', v_findings
        )
    );

    RETURN v_inspection_id;
END;
$$;

INSERT INTO projects(project_code, project_name, owner_name)
VALUES
    ('OPS-2026', 'Operations Reporting Modernization', 'Operations Office'),
    ('DATA-2026', 'Data Quality Improvement', 'Data Services');

INSERT INTO project_outputs(
    project_id, output_name, version, artifact_uri
)
SELECT project_id, 'Monthly Performance Report', '1.0',
       'artifacts/monthly-performance-v1.pdf'
FROM projects WHERE project_code = 'OPS-2026';

INSERT INTO project_outputs(
    project_id, output_name, version, artifact_uri
)
SELECT project_id, 'Source Reconciliation Dataset', '1.0',
       'artifacts/reconciliation-v1.csv'
FROM projects WHERE project_code = 'DATA-2026';

INSERT INTO quality_requirements(
    project_id, requirement_code, description, mandatory
)
SELECT p.project_id, r.code, r.description, r.mandatory
FROM projects p
CROSS JOIN (
    VALUES
        ('Q1', 'Required report sections are present', true),
        ('Q2', 'Output totals reconcile with source records', true),
        ('Q3', 'Labels and units follow the style guide', true),
        ('Q4', 'Optional visual enhancement is included', false)
) AS r(code, description, mandatory)
WHERE p.project_code = 'OPS-2026';

INSERT INTO quality_requirements(
    project_id, requirement_code, description, mandatory
)
SELECT p.project_id, r.code, r.description, r.mandatory
FROM projects p
CROSS JOIN (
    VALUES
        ('D1', 'Dataset columns match the approved schema', true),
        ('D2', 'Required identifiers are unique', true)
) AS r(code, description, mandatory)
WHERE p.project_code = 'DATA-2026';

-- The first output fails reconciliation and cannot be released.
SELECT complete_inspection(
    (SELECT output_id FROM project_outputs
     WHERE output_name = 'Monthly Performance Report'),
    'quality-reviewer',
    '{
        "Q1": {"passed": true, "evidence": "Sections checklist passed"},
        "Q2": {"passed": false, "evidence": "Output total 76500; source total 76440"},
        "Q3": {"passed": true, "evidence": "Units and labels verified"},
        "Q4": {"passed": true, "evidence": "Visual checklist passed"}
    }'::jsonb,
    'Initial release inspection'
);

SELECT * FROM evaluate_output(
    (SELECT output_id FROM project_outputs
     WHERE output_name = 'Monthly Performance Report')
);

-- The second output passes all mandatory checks.
SELECT complete_inspection(
    (SELECT output_id FROM project_outputs
     WHERE output_name = 'Source Reconciliation Dataset'),
    'data-quality-reviewer',
    '{
        "D1": {"passed": true, "evidence": "Schema comparison passed"},
        "D2": {"passed": true, "evidence": "Identifier uniqueness query returned no duplicates"}
    }'::jsonb,
    'Dataset validation'
);

SELECT * FROM evaluate_output(
    (SELECT output_id FROM project_outputs
     WHERE output_name = 'Source Reconciliation Dataset')
);

-- Release only after the database evaluates all required conditions.
DO $$
DECLARE
    v_output_id bigint;
    v_decision record;
BEGIN
    SELECT output_id INTO v_output_id
    FROM project_outputs
    WHERE output_name = 'Source Reconciliation Dataset';

    SELECT * INTO v_decision FROM evaluate_output(v_output_id);

    IF NOT v_decision.eligible THEN
        RAISE EXCEPTION 'Release denied: %', v_decision.decision;
    END IF;

    UPDATE project_outputs
    SET status = 'released'
    WHERE output_id = v_output_id;
END;
$$;

-- Reporting: latest inspection per output and outstanding blocking findings.
WITH latest AS (
    SELECT DISTINCT ON (i.output_id)
        i.output_id,
        i.inspection_id,
        i.inspector,
        i.status,
        i.inspected_at
    FROM inspections i
    ORDER BY i.output_id, i.inspected_at DESC, i.inspection_id DESC
)
SELECT
    p.project_code,
    o.output_name,
    o.version,
    o.status AS output_status,
    l.inspector,
    l.status AS latest_inspection_status,
    COUNT(f.finding_id) FILTER (
        WHERE f.status = 'open'
          AND f.severity IN ('critical', 'major')
    ) AS blocking_findings
FROM project_outputs o
JOIN projects p USING (project_id)
LEFT JOIN latest l USING (output_id)
LEFT JOIN inspections all_inspections ON all_inspections.output_id = o.output_id
LEFT JOIN quality_findings f ON f.inspection_id = all_inspections.inspection_id
GROUP BY p.project_code, o.output_name, o.version, o.status,
         l.inspector, l.status
ORDER BY p.project_code, o.output_name;

-- Auditable evidence for each inspection.
SELECT *
FROM inspection_detail
ORDER BY output_id, inspected_at, inspection_id, requirement_code;

SELECT output_id, event_type, actor, details, occurred_at
FROM quality_audit
ORDER BY audit_id;

COMMIT;
