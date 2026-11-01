DROP SCHEMA IF EXISTS team_formation CASCADE;
CREATE SCHEMA team_formation;

SET search_path = team_formation, public;

CREATE TYPE availability_status AS ENUM (
    'available',
    'partial',
    'unavailable'
);

CREATE TYPE team_state AS ENUM (
    'proposed',
    'validated',
    'approved',
    'rejected'
);

CREATE TYPE risk_level AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE decision_status AS ENUM (
    'eligible',
    'ineligible'
);

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    owner_team TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidates (
    candidate_id BIGSERIAL PRIMARY KEY,
    candidate_code TEXT NOT NULL UNIQUE,
    candidate_name TEXT NOT NULL,
    experience_years NUMERIC(5,2) NOT NULL CHECK (experience_years >= 0),
    availability availability_status NOT NULL,
    max_projects INTEGER NOT NULL DEFAULT 1
        CHECK (max_projects BETWEEN 1 AND 10)
);

CREATE TABLE roles (
    role_id BIGSERIAL PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE
);

CREATE TABLE skills (
    skill_id BIGSERIAL PRIMARY KEY,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE candidate_roles (
    candidate_id BIGINT NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    PRIMARY KEY (candidate_id, role_id)
);

CREATE TABLE candidate_skills (
    candidate_id BIGINT NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    skill_id BIGINT NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    proficiency SMALLINT NOT NULL CHECK (proficiency BETWEEN 1 AND 5),
    PRIMARY KEY (candidate_id, skill_id)
);

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT REFERENCES repositories(repository_id),
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    risk risk_level NOT NULL DEFAULT 'medium',
    minimum_team_size INTEGER NOT NULL CHECK (minimum_team_size > 0),
    maximum_team_size INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (maximum_team_size >= minimum_team_size)
);

CREATE TABLE project_required_roles (
    project_id BIGINT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(role_id),
    PRIMARY KEY (project_id, role_id)
);

CREATE TABLE project_required_skills (
    project_id BIGINT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    skill_id BIGINT NOT NULL REFERENCES skills(skill_id),
    minimum_proficiency SMALLINT NOT NULL DEFAULT 1
        CHECK (minimum_proficiency BETWEEN 1 AND 5),
    PRIMARY KEY (project_id, skill_id)
);

CREATE TABLE teams (
    team_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    team_name TEXT NOT NULL,
    state team_state NOT NULL DEFAULT 'proposed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, team_name)
);

CREATE TABLE team_members (
    team_id BIGINT NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    candidate_id BIGINT NOT NULL REFERENCES candidates(candidate_id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, candidate_id)
);

CREATE TABLE formation_decisions (
    decision_id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    decision decision_status NOT NULL,
    missing_roles INTEGER NOT NULL DEFAULT 0 CHECK (missing_roles >= 0),
    missing_skills INTEGER NOT NULL DEFAULT 0 CHECK (missing_skills >= 0),
    reasons TEXT NOT NULL DEFAULT '',
    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_candidate_roles_role
    ON candidate_roles(role_id);

CREATE INDEX idx_candidate_skills_skill
    ON candidate_skills(skill_id);

CREATE INDEX idx_team_members_candidate
    ON team_members(candidate_id);

CREATE INDEX idx_teams_project_state
    ON teams(project_id, state);

INSERT INTO repositories (repository_name, owner_team)
VALUES
    ('secure-operations-platform', 'R&D Engineering');

INSERT INTO roles (role_name)
VALUES
    ('Product Manager'),
    ('Technical Lead'),
    ('Backend Engineer'),
    ('Frontend Engineer'),
    ('QA Engineer'),
    ('DevOps Engineer'),
    ('Data Engineer'),
    ('Security Engineer'),
    ('UX Designer');

INSERT INTO skills (skill_name)
VALUES
    ('roadmapping'),
    ('stakeholder-management'),
    ('architecture'),
    ('python'),
    ('postgresql'),
    ('javascript'),
    ('testing'),
    ('docker'),
    ('security'),
    ('react'),
    ('threat-modeling'),
    ('iam'),
    ('ci-cd'),
    ('linux');

INSERT INTO candidates (
    candidate_code,
    candidate_name,
    experience_years,
    availability,
    max_projects
)
VALUES
    ('C001', 'Aarav', 7, 'available', 1),
    ('C002', 'Meera', 9, 'available', 1),
    ('C003', 'Kabir', 5, 'available', 1),
    ('C004', 'Diya', 4, 'available', 1),
    ('C005', 'Rohan', 6, 'available', 1),
    ('C006', 'Ishita', 6, 'partial', 1),
    ('C007', 'Vikram', 5, 'available', 1),
    ('C008', 'Nisha', 7, 'available', 1);

INSERT INTO candidate_roles (candidate_id, role_id)
SELECT c.candidate_id, r.role_id
FROM candidates c
JOIN roles r ON
    (c.candidate_code = 'C001' AND r.role_name = 'Product Manager')
 OR (c.candidate_code = 'C002' AND r.role_name IN ('Technical Lead', 'Backend Engineer'))
 OR (c.candidate_code = 'C003' AND r.role_name = 'Backend Engineer')
 OR (c.candidate_code = 'C004' AND r.role_name IN ('Frontend Engineer', 'UX Designer'))
 OR (c.candidate_code = 'C005' AND r.role_name = 'QA Engineer')
 OR (c.candidate_code = 'C006' AND r.role_name = 'DevOps Engineer')
 OR (c.candidate_code = 'C007' AND r.role_name = 'Data Engineer')
 OR (c.candidate_code = 'C008' AND r.role_name = 'Security Engineer');

INSERT INTO candidate_skills (candidate_id, skill_id, proficiency)
SELECT c.candidate_id, s.skill_id, 4
FROM candidates c
JOIN skills s ON
    (c.candidate_code = 'C001' AND s.skill_name IN ('roadmapping', 'stakeholder-management'))
 OR (c.candidate_code = 'C002' AND s.skill_name IN ('architecture', 'python', 'postgresql', 'security'))
 OR (c.candidate_code = 'C003' AND s.skill_name IN ('python', 'postgresql', 'testing'))
 OR (c.candidate_code = 'C004' AND s.skill_name IN ('javascript', 'react'))
 OR (c.candidate_code = 'C005' AND s.skill_name IN ('testing'))
 OR (c.candidate_code = 'C006' AND s.skill_name IN ('docker', 'ci-cd', 'linux'))
 OR (c.candidate_code = 'C007' AND s.skill_name IN ('python', 'postgresql'))
 OR (c.candidate_code = 'C008' AND s.skill_name IN ('security', 'threat-modeling', 'iam'));

INSERT INTO projects (
    repository_id,
    project_code,
    project_name,
    risk,
    minimum_team_size,
    maximum_team_size
)
SELECT
    repository_id,
    'P001',
    'Secure Operations Analytics Platform',
    'high',
    7,
    8
FROM repositories
WHERE repository_name = 'secure-operations-platform';

INSERT INTO project_required_roles (project_id, role_id)
SELECT p.project_id, r.role_id
FROM projects p
JOIN roles r ON r.role_name IN (
    'Product Manager',
    'Technical Lead',
    'Backend Engineer',
    'Frontend Engineer',
    'QA Engineer',
    'DevOps Engineer',
    'Security Engineer'
)
WHERE p.project_code = 'P001';

INSERT INTO project_required_skills (project_id, skill_id, minimum_proficiency)
SELECT p.project_id, s.skill_id, 3
FROM projects p
JOIN skills s ON s.skill_name IN (
    'roadmapping',
    'architecture',
    'python',
    'postgresql',
    'javascript',
    'testing',
    'docker',
    'security'
)
WHERE p.project_code = 'P001';

INSERT INTO teams (project_id, team_name)
SELECT project_id, 'Secure Operations Core Team'
FROM projects
WHERE project_code = 'P001';

INSERT INTO team_members (team_id, candidate_id)
SELECT t.team_id, c.candidate_id
FROM teams t
JOIN candidates c ON c.candidate_code IN (
    'C001',
    'C002',
    'C003',
    'C004',
    'C005',
    'C006',
    'C008'
)
WHERE t.team_name = 'Secure Operations Core Team';

CREATE OR REPLACE FUNCTION evaluate_team(
    p_team_id BIGINT
)
RETURNS TABLE (
    decision decision_status,
    missing_roles BIGINT,
    missing_skills BIGINT,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_project_id BIGINT;
    v_min_size INTEGER;
    v_max_size INTEGER;
    v_team_size BIGINT;
    v_missing_roles BIGINT;
    v_missing_skills BIGINT;
    v_reasons TEXT[] := ARRAY[]::TEXT[];
BEGIN
    SELECT
        p.project_id,
        p.minimum_team_size,
        p.maximum_team_size
    INTO
        v_project_id,
        v_min_size,
        v_max_size
    FROM teams t
    JOIN projects p ON p.project_id = t.project_id
    WHERE t.team_id = p_team_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Team % does not exist', p_team_id;
    END IF;

    SELECT COUNT(*)
    INTO v_team_size
    FROM team_members
    WHERE team_id = p_team_id;

    IF v_team_size < v_min_size THEN
        v_reasons := array_append(v_reasons, 'Team is below minimum size');
    END IF;

    IF v_team_size > v_max_size THEN
        v_reasons := array_append(v_reasons, 'Team exceeds maximum size');
    END IF;

    SELECT COUNT(*)
    INTO v_missing_roles
    FROM project_required_roles pr
    WHERE pr.project_id = v_project_id
      AND NOT EXISTS (
          SELECT 1
          FROM team_members tm
          JOIN candidate_roles cr
            ON cr.candidate_id = tm.candidate_id
           AND cr.role_id = pr.role_id
          WHERE tm.team_id = p_team_id
      );

    SELECT COUNT(*)
    INTO v_missing_skills
    FROM project_required_skills ps
    WHERE ps.project_id = v_project_id
      AND NOT EXISTS (
          SELECT 1
          FROM team_members tm
          JOIN candidate_skills cs
            ON cs.candidate_id = tm.candidate_id
           AND cs.skill_id = ps.skill_id
          WHERE tm.team_id = p_team_id
            AND cs.proficiency >= ps.minimum_proficiency
      );

    IF v_missing_roles > 0 THEN
        v_reasons := array_append(v_reasons, 'Mandatory roles are missing');
    END IF;

    IF v_missing_skills > 0 THEN
        v_reasons := array_append(v_reasons, 'Required skills are missing');
    END IF;

    IF cardinality(v_reasons) = 0 THEN
        decision := 'eligible';
    ELSE
        decision := 'ineligible';
    END IF;

    missing_roles := v_missing_roles;
    missing_skills := v_missing_skills;
    reason := COALESCE(array_to_string(v_reasons, '; '), 'Team satisfies formation policy');

    RETURN NEXT;
END;
$$;

CREATE OR REPLACE FUNCTION refresh_team_decision()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_decision decision_status;
    v_missing_roles BIGINT;
    v_missing_skills BIGINT;
    v_reason TEXT;
BEGIN
    SELECT
        decision,
        missing_roles,
        missing_skills,
        reason
    INTO
        v_decision,
        v_missing_roles,
        v_missing_skills,
        v_reason
    FROM evaluate_team(NEW.team_id);

    INSERT INTO formation_decisions (
        team_id,
        decision,
        missing_roles,
        missing_skills,
        reasons
    )
    VALUES (
        NEW.team_id,
        v_decision,
        v_missing_roles,
        v_missing_skills,
        v_reason
    );

    UPDATE teams
    SET state = CASE
        WHEN v_decision = 'eligible' THEN 'validated'::team_state
        ELSE 'rejected'::team_state
    END
    WHERE team_id = NEW.team_id;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_refresh_team_decision
AFTER INSERT ON team_members
FOR EACH ROW
EXECUTE FUNCTION refresh_team_decision();

BEGIN;

WITH evaluation AS (
    SELECT *
    FROM evaluate_team(
        (SELECT team_id
         FROM teams
         WHERE team_name = 'Secure Operations Core Team')
    )
)
INSERT INTO formation_decisions (
    team_id,
    decision,
    missing_roles,
    missing_skills,
    reasons
)
SELECT
    t.team_id,
    e.decision,
    e.missing_roles,
    e.missing_skills,
    e.reason
FROM teams t
CROSS JOIN evaluation e
WHERE t.team_name = 'Secure Operations Core Team';

UPDATE teams
SET state = CASE
    WHEN (
        SELECT decision
        FROM evaluate_team(teams.team_id)
    ) = 'eligible'
    THEN 'approved'::team_state
    ELSE 'rejected'::team_state
END
WHERE team_name = 'Secure Operations Core Team';

COMMIT;

-- Candidate availability and role coverage report.
SELECT
    c.candidate_code,
    c.candidate_name,
    c.availability,
    c.experience_years,
    STRING_AGG(r.role_name, ', ' ORDER BY r.role_name) AS roles
FROM candidates c
LEFT JOIN candidate_roles cr ON cr.candidate_id = c.candidate_id
LEFT JOIN roles r ON r.role_id = cr.role_id
GROUP BY
    c.candidate_id,
    c.candidate_code,
    c.candidate_name,
    c.availability,
    c.experience_years
ORDER BY c.candidate_code;

-- Team composition and skill coverage.
SELECT
    t.team_name,
    p.project_name,
    COUNT(DISTINCT tm.candidate_id) AS member_count,
    t.state,
    STRING_AGG(
        DISTINCT c.candidate_name,
        ', '
        ORDER BY c.candidate_name
    ) AS members
FROM teams t
JOIN projects p ON p.project_id = t.project_id
JOIN team_members tm ON tm.team_id = t.team_id
JOIN candidates c ON c.candidate_id = tm.candidate_id
GROUP BY
    t.team_id,
    t.team_name,
    p.project_name,
    t.state;

-- Exact eligibility evaluation.
SELECT *
FROM evaluate_team(
    (SELECT team_id
     FROM teams
     WHERE team_name = 'Secure Operations Core Team')
);

-- Missing role validation.
SELECT
    p.project_name,
    r.role_name AS missing_role
FROM projects p
JOIN project_required_roles pr
  ON pr.project_id = p.project_id
JOIN roles r
  ON r.role_id = pr.role_id
WHERE NOT EXISTS (
    SELECT 1
    FROM teams t
    JOIN team_members tm ON tm.team_id = t.team_id
    JOIN candidate_roles cr ON cr.candidate_id = tm.candidate_id
    WHERE t.project_id = p.project_id
      AND cr.role_id = r.role_id
);

-- Experience distribution by role.
SELECT
    r.role_name,
    COUNT(DISTINCT c.candidate_id) AS candidate_count,
    ROUND(AVG(c.experience_years), 2) AS average_experience
FROM roles r
JOIN candidate_roles cr ON cr.role_id = r.role_id
JOIN candidates c ON c.candidate_id = cr.candidate_id
GROUP BY r.role_id, r.role_name
ORDER BY average_experience DESC;

-- Latest formation decisions.
SELECT
    fd.decision_id,
    t.team_name,
    fd.decision,
    fd.missing_roles,
    fd.missing_skills,
    fd.reasons,
    fd.decided_at
FROM formation_decisions fd
JOIN teams t ON t.team_id = fd.team_id
ORDER BY fd.decided_at DESC;
