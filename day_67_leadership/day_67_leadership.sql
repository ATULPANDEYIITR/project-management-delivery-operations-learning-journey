-- ============================================================
-- LEADERSHIP IN PROJECT MANAGEMENT
-- PostgreSQL Project Leadership and Governance Database
-- ============================================================

CREATE SCHEMA IF NOT EXISTS project_leadership;

SET search_path TO project_leadership, public;

-- ============================================================
-- 1. ENUMERATIONS
-- ============================================================

CREATE TYPE leadership_style AS ENUM (
    'AUTOCRATIC',
    'DEMOCRATIC',
    'TRANSFORMATIONAL',
    'TRANSACTIONAL',
    'SERVANT',
    'SITUATIONAL'
);

CREATE TYPE team_skill_level AS ENUM (
    'BEGINNER',
    'DEVELOPING',
    'COMPETENT',
    'ADVANCED',
    'EXPERT'
);

CREATE TYPE project_task_status AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'BLOCKED',
    'COMPLETED'
);

CREATE TYPE decision_status AS ENUM (
    'PROPOSED',
    'APPROVED',
    'REJECTED',
    'DEFERRED'
);

CREATE TYPE risk_status AS ENUM (
    'OPEN',
    'MITIGATING',
    'CLOSED',
    'ACCEPTED'
);

CREATE TYPE risk_level AS ENUM (
    'LOW',
    'MEDIUM',
    'HIGH',
    'CRITICAL'
);

CREATE TYPE stakeholder_strategy AS ENUM (
    'MANAGE_CLOSELY',
    'KEEP_SATISFIED',
    'KEEP_INFORMED',
    'MONITOR'
);

-- ============================================================
-- 2. CORE PROJECT TABLES
-- ============================================================

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_code VARCHAR(30) NOT NULL UNIQUE,

    project_name VARCHAR(200) NOT NULL,

    description TEXT,

    project_manager_id BIGINT,

    default_leadership_style leadership_style
        NOT NULL DEFAULT 'SITUATIONAL',

    start_date DATE NOT NULL,

    planned_end_date DATE NOT NULL,

    actual_end_date DATE,

    budget NUMERIC(14, 2) NOT NULL DEFAULT 0,

    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (planned_end_date >= start_date),

    CHECK (
        actual_end_date IS NULL OR
        actual_end_date >= start_date
    ),

    CHECK (budget >= 0),

    CHECK (
        status IN (
            'PLANNING',
            'ACTIVE',
            'ON_HOLD',
            'COMPLETED',
            'CANCELLED'
        )
    )
);

CREATE TABLE team_members (
    member_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    employee_code VARCHAR(30) NOT NULL UNIQUE,

    full_name VARCHAR(150) NOT NULL,

    role_name VARCHAR(100) NOT NULL,

    skill_level team_skill_level NOT NULL,

    workload_percentage NUMERIC(5, 2)
        NOT NULL DEFAULT 0,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    development_goal TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        workload_percentage BETWEEN 0 AND 100
    )
);

ALTER TABLE projects
ADD CONSTRAINT fk_project_manager
FOREIGN KEY (project_manager_id)
REFERENCES team_members(member_id)
ON DELETE RESTRICT;

CREATE TABLE project_team (
    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    member_id BIGINT NOT NULL
        REFERENCES team_members(member_id)
        ON DELETE RESTRICT,

    assignment_role VARCHAR(100) NOT NULL,

    allocation_percentage NUMERIC(5, 2)
        NOT NULL DEFAULT 0,

    joined_at DATE NOT NULL DEFAULT CURRENT_DATE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (project_id, member_id),

    CHECK (
        allocation_percentage BETWEEN 0 AND 100
    )
);

-- ============================================================
-- 3. LEADERSHIP TASK DELEGATION
-- ============================================================

CREATE TABLE project_tasks (
    task_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    parent_task_id BIGINT
        REFERENCES project_tasks(task_id)
        ON DELETE RESTRICT,

    task_code VARCHAR(30) NOT NULL,

    title VARCHAR(200) NOT NULL,

    description TEXT,

    required_skill team_skill_level NOT NULL,

    estimated_hours NUMERIC(10, 2) NOT NULL,

    actual_hours NUMERIC(10, 2) NOT NULL DEFAULT 0,

    priority SMALLINT NOT NULL DEFAULT 3,

    status project_task_status
        NOT NULL DEFAULT 'NOT_STARTED',

    progress NUMERIC(5, 2) NOT NULL DEFAULT 0,

    assigned_to BIGINT
        REFERENCES team_members(member_id)
        ON DELETE RESTRICT,

    delegated_by BIGINT
        REFERENCES team_members(member_id)
        ON DELETE RESTRICT,

    version INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (project_id, task_code),

    CHECK (estimated_hours > 0),

    CHECK (actual_hours >= 0),

    CHECK (priority BETWEEN 1 AND 5),

    CHECK (progress BETWEEN 0 AND 100),

    CHECK (version >= 0),

    CHECK (
        (status = 'COMPLETED' AND progress = 100)
        OR status <> 'COMPLETED'
    ),

    CHECK (
        status NOT IN ('IN_PROGRESS', 'COMPLETED')
        OR assigned_to IS NOT NULL
    )
);

CREATE INDEX idx_tasks_project_status
ON project_tasks(project_id, status);

CREATE INDEX idx_tasks_assigned_member
ON project_tasks(assigned_to)
WHERE assigned_to IS NOT NULL;

CREATE INDEX idx_tasks_priority
ON project_tasks(project_id, priority DESC);

-- ============================================================
-- 4. TASK ASSIGNMENT HISTORY
-- ============================================================

CREATE TABLE task_assignment_history (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    task_id BIGINT NOT NULL
        REFERENCES project_tasks(task_id)
        ON DELETE CASCADE,

    previous_member_id BIGINT
        REFERENCES team_members(member_id),

    new_member_id BIGINT
        REFERENCES team_members(member_id),

    assigned_by BIGINT
        REFERENCES team_members(member_id),

    assignment_reason TEXT NOT NULL,

    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 5. STAKEHOLDER MANAGEMENT
-- ============================================================

CREATE TABLE stakeholders (
    stakeholder_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    stakeholder_name VARCHAR(150) NOT NULL,

    stakeholder_role VARCHAR(100) NOT NULL,

    influence SMALLINT NOT NULL,

    interest SMALLINT NOT NULL,

    expectations TEXT NOT NULL,

    engagement_strategy stakeholder_strategy NOT NULL,

    communication_frequency VARCHAR(30)
        NOT NULL DEFAULT 'WEEKLY',

    active BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (influence BETWEEN 1 AND 5),

    CHECK (interest BETWEEN 1 AND 5),

    UNIQUE (project_id, stakeholder_name)
);

CREATE INDEX idx_stakeholder_engagement
ON stakeholders(
    project_id,
    influence DESC,
    interest DESC
);

CREATE TABLE stakeholder_communications (
    communication_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id)
        ON DELETE CASCADE,

    communicated_by BIGINT NOT NULL
        REFERENCES team_members(member_id),

    communication_type VARCHAR(30) NOT NULL,

    subject VARCHAR(200) NOT NULL,

    communication_notes TEXT,

    communication_date TIMESTAMPTZ
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        communication_type IN (
            'MEETING',
            'EMAIL',
            'REPORT',
            'WORKSHOP',
            'PRESENTATION'
        )
    )
);

-- ============================================================
-- 6. RISK OWNERSHIP AND MITIGATION
-- ============================================================

CREATE TABLE project_risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    risk_code VARCHAR(30) NOT NULL,

    description TEXT NOT NULL,

    probability SMALLINT NOT NULL,

    impact SMALLINT NOT NULL,

    owner_id BIGINT NOT NULL
        REFERENCES team_members(member_id),

    mitigation_plan TEXT NOT NULL,

    contingency_plan TEXT,

    status risk_status NOT NULL DEFAULT 'OPEN',

    identified_at TIMESTAMPTZ
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    reviewed_at TIMESTAMPTZ,

    UNIQUE (project_id, risk_code),

    CHECK (probability BETWEEN 1 AND 5),

    CHECK (impact BETWEEN 1 AND 5)
);

CREATE INDEX idx_project_risk_status
ON project_risks(project_id, status);

CREATE INDEX idx_risk_owner
ON project_risks(owner_id, status);

-- ============================================================
-- 7. LEADERSHIP DECISION MANAGEMENT
-- ============================================================

CREATE TABLE leadership_decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    decision_code VARCHAR(30) NOT NULL,

    title VARCHAR(200) NOT NULL,

    description TEXT NOT NULL,

    decision_maker BIGINT NOT NULL
        REFERENCES team_members(member_id),

    status decision_status NOT NULL DEFAULT 'PROPOSED',

    rationale TEXT,

    expected_impact TEXT,

    decided_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (project_id, decision_code),

    CHECK (
        status = 'PROPOSED'
        OR (
            rationale IS NOT NULL
            AND LENGTH(TRIM(rationale)) > 0
        )
    ),

    CHECK (
        status = 'PROPOSED'
        OR decided_at IS NOT NULL
    )
);

CREATE INDEX idx_decision_project_status
ON leadership_decisions(project_id, status);

CREATE TABLE decision_options (
    option_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    decision_id BIGINT NOT NULL
        REFERENCES leadership_decisions(decision_id)
        ON DELETE CASCADE,

    option_name VARCHAR(200) NOT NULL,

    advantages TEXT,

    disadvantages TEXT,

    estimated_cost NUMERIC(14, 2),

    estimated_duration_days INTEGER,

    selected BOOLEAN NOT NULL DEFAULT FALSE,

    CHECK (
        estimated_cost IS NULL OR estimated_cost >= 0
    ),

    CHECK (
        estimated_duration_days IS NULL
        OR estimated_duration_days >= 0
    ),

    UNIQUE (decision_id, option_name)
);

-- ============================================================
-- 8. CONFLICT MANAGEMENT
-- ============================================================

CREATE TABLE project_conflicts (
    conflict_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id)
        ON DELETE CASCADE,

    issue_title VARCHAR(200) NOT NULL,

    description TEXT NOT NULL,

    conflict_type VARCHAR(30) NOT NULL,

    resolution_method VARCHAR(30),

    proposed_resolution TEXT,

    final_resolution TEXT,

    raised_by BIGINT
        REFERENCES team_members(member_id),

    resolved_by BIGINT
        REFERENCES team_members(member_id),

    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',

    raised_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    resolved_at TIMESTAMPTZ,

    CHECK (
        conflict_type IN (
            'TASK',
            'RESOURCE',
            'COMMUNICATION',
            'PRIORITY',
            'TECHNICAL',
            'INTERPERSONAL'
        )
    ),

    CHECK (
        resolution_method IS NULL
        OR resolution_method IN (
            'COLLABORATION',
            'COMPROMISE',
            'ACCOMMODATION',
            'COMPETITION',
            'AVOIDANCE'
        )
    ),

    CHECK (
        status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'ESCALATED')
    ),

    CHECK (
        status <> 'RESOLVED'
        OR (
            final_resolution IS NOT NULL
            AND resolved_by IS NOT NULL
            AND resolved_at IS NOT NULL
        )
    )
);

-- ============================================================
-- 9. LEADERSHIP AUDIT LOG
-- ============================================================

CREATE TABLE leadership_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT
        REFERENCES projects(project_id)
        ON DELETE SET NULL,

    actor_id BIGINT
        REFERENCES team_members(member_id)
        ON DELETE SET NULL,

    event_type VARCHAR(60) NOT NULL,

    entity_type VARCHAR(60) NOT NULL,

    entity_id BIGINT,

    event_description TEXT NOT NULL,

    event_data JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ
        NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_leadership_audit_project_time
ON leadership_audit_log(project_id, created_at DESC);

-- ============================================================
-- 10. AUTOMATIC TASK VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_task_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    member_skill team_skill_level;
    member_active BOOLEAN;
    member_workload NUMERIC(5, 2);
    old_allocation NUMERIC(5, 2) := 0;
BEGIN
    IF NEW.assigned_to IS NULL THEN
        IF NEW.status IN ('IN_PROGRESS', 'COMPLETED') THEN
            RAISE EXCEPTION
                'Active or completed tasks require an owner.';
        END IF;

        RETURN NEW;
    END IF;

    SELECT skill_level, active, workload_percentage
    INTO member_skill, member_active, member_workload
    FROM team_members
    WHERE member_id = NEW.assigned_to
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Assigned team member does not exist.';
    END IF;

    IF NOT member_active THEN
        RAISE EXCEPTION 'Inactive members cannot receive assignments.';
    END IF;

    IF member_skill < NEW.required_skill THEN
        RAISE EXCEPTION
            'Assigned member does not meet the required skill level.';
    END IF;

    IF TG_OP = 'UPDATE'
       AND OLD.assigned_to IS NOT DISTINCT FROM NEW.assigned_to
    THEN
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' AND OLD.assigned_to IS NOT NULL THEN
        SELECT COALESCE(
            SUM(20), 0
        )
        INTO old_allocation
        FROM project_tasks
        WHERE assigned_to = OLD.assigned_to
          AND task_id <> OLD.task_id
          AND status IN ('IN_PROGRESS', 'BLOCKED');
    END IF;

    IF member_workload + 20 > 100 THEN
        RAISE EXCEPTION
            'Member workload exceeds the permitted allocation.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_task_assignment
BEFORE INSERT OR UPDATE OF assigned_to, required_skill, status
ON project_tasks
FOR EACH ROW
EXECUTE FUNCTION validate_task_assignment();

-- ============================================================
-- 11. ASSIGNMENT AUDIT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION record_task_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.assigned_to IS DISTINCT FROM OLD.assigned_to THEN
        INSERT INTO task_assignment_history (
            task_id,
            previous_member_id,
            new_member_id,
            assigned_by,
            assignment_reason
        )
        VALUES (
            NEW.task_id,
            OLD.assigned_to,
            NEW.assigned_to,
            NEW.delegated_by,
            'Task ownership changed.'
        );

        INSERT INTO leadership_audit_log (
            project_id,
            actor_id,
            event_type,
            entity_type,
            entity_id,
            event_description
        )
        VALUES (
            NEW.project_id,
            NEW.delegated_by,
            'TASK_REASSIGNED',
            'PROJECT_TASK',
            NEW.task_id,
            'Task assignment updated.'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_record_task_assignment
AFTER UPDATE OF assigned_to
ON project_tasks
FOR EACH ROW
WHEN (OLD.assigned_to IS DISTINCT FROM NEW.assigned_to)
EXECUTE FUNCTION record_task_assignment();

-- ============================================================
-- 12. TASK STATE AND VERSION CONTROL
-- ============================================================

CREATE OR REPLACE FUNCTION validate_task_progress()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.progress < OLD.progress THEN
        RAISE EXCEPTION 'Task progress cannot decrease.';
    END IF;

    IF NEW.actual_hours < OLD.actual_hours THEN
        RAISE EXCEPTION 'Actual hours cannot decrease.';
    END IF;

    IF OLD.status = 'COMPLETED'
       AND NEW.status <> 'COMPLETED'
    THEN
        RAISE EXCEPTION
            'Completed tasks cannot be reopened through a normal update.';
    END IF;

    IF NEW.status = 'COMPLETED' THEN
        NEW.progress := 100;
    END IF;

    NEW.version := OLD.version + 1;
    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_task_progress
BEFORE UPDATE ON project_tasks
FOR EACH ROW
EXECUTE FUNCTION validate_task_progress();

-- ============================================================
-- 13. AUTOMATIC RISK CLASSIFICATION
-- ============================================================

CREATE OR REPLACE FUNCTION classify_risk(
    p_probability SMALLINT,
    p_impact SMALLINT
)
RETURNS risk_level
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    exposure INTEGER;
BEGIN
    IF p_probability NOT BETWEEN 1 AND 5
       OR p_impact NOT BETWEEN 1 AND 5
    THEN
        RAISE EXCEPTION 'Risk values must be between 1 and 5.';
    END IF;

    exposure := p_probability * p_impact;

    IF exposure >= 20 THEN
        RETURN 'CRITICAL';
    ELSIF exposure >= 12 THEN
        RETURN 'HIGH';
    ELSIF exposure >= 6 THEN
        RETURN 'MEDIUM';
    ELSE
        RETURN 'LOW';
    END IF;
END;
$$;

-- ============================================================
-- 14. STAKEHOLDER ENGAGEMENT POLICY
-- ============================================================

CREATE OR REPLACE FUNCTION determine_stakeholder_strategy(
    p_influence SMALLINT,
    p_interest SMALLINT
)
RETURNS stakeholder_strategy
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_influence NOT BETWEEN 1 AND 5
       OR p_interest NOT BETWEEN 1 AND 5
    THEN
        RAISE EXCEPTION 'Stakeholder ratings must be 1-5.';
    END IF;

    IF p_influence >= 4 AND p_interest >= 4 THEN
        RETURN 'MANAGE_CLOSELY';
    ELSIF p_influence >= 4 THEN
        RETURN 'KEEP_SATISFIED';
    ELSIF p_interest >= 4 THEN
        RETURN 'KEEP_INFORMED';
    ELSE
        RETURN 'MONITOR';
    END IF;
END;
$$;

-- ============================================================
-- 15. DECISION PROCESSING PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE process_leadership_decision(
    p_decision_id BIGINT,
    p_status decision_status,
    p_rationale TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status decision_status;
    current_project BIGINT;
BEGIN
    IF p_rationale IS NULL OR LENGTH(TRIM(p_rationale)) = 0 THEN
        RAISE EXCEPTION 'Decision rationale is mandatory.';
    END IF;

    SELECT status, project_id
    INTO current_status, current_project
    FROM leadership_decisions
    WHERE decision_id = p_decision_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Decision does not exist.';
    END IF;

    IF current_status <> 'PROPOSED' THEN
        RAISE EXCEPTION 'Decision has already been processed.';
    END IF;

    UPDATE leadership_decisions
    SET
        status = p_status,
        rationale = p_rationale,
        decided_at = CURRENT_TIMESTAMP
    WHERE decision_id = p_decision_id;

    INSERT INTO leadership_audit_log (
        project_id,
        event_type,
        entity_type,
        entity_id,
        event_description
    )
    VALUES (
        current_project,
        'DECISION_PROCESSED',
        'LEADERSHIP_DECISION',
        p_decision_id,
        'Decision status changed to ' || p_status::TEXT
    );
END;
$$;

-- ============================================================
-- 16. PROJECT LEADERSHIP METRICS VIEW
-- ============================================================

CREATE OR REPLACE VIEW project_leadership_metrics AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,

    COUNT(t.task_id) AS total_tasks,

    COUNT(t.task_id) FILTER (
        WHERE t.status = 'COMPLETED'
    ) AS completed_tasks,

    COUNT(t.task_id) FILTER (
        WHERE t.assigned_to IS NOT NULL
    ) AS assigned_tasks,

    COALESCE(
        ROUND(AVG(t.progress), 2),
        0
    ) AS average_progress,

    COALESCE(
        ROUND(
            100.0 * COUNT(t.task_id) FILTER (
                WHERE t.status = 'COMPLETED'
            ) / NULLIF(COUNT(t.task_id), 0),
            2
        ),
        0
    ) AS completion_percentage,

    COUNT(DISTINCT r.risk_id) FILTER (
        WHERE r.status IN ('OPEN', 'MITIGATING')
    ) AS active_risks

FROM projects p

LEFT JOIN project_tasks t
    ON t.project_id = p.project_id

LEFT JOIN project_risks r
    ON r.project_id = p.project_id

GROUP BY
    p.project_id,
    p.project_code,
    p.project_name;

-- ============================================================
-- 17. TEAM PERFORMANCE VIEW
-- ============================================================

CREATE OR REPLACE VIEW team_performance AS
SELECT
    m.member_id,
    m.employee_code,
    m.full_name,
    m.role_name,
    m.skill_level,
    m.workload_percentage,

    COUNT(t.task_id) FILTER (
        WHERE t.status = 'IN_PROGRESS'
    ) AS active_tasks,

    COUNT(t.task_id) FILTER (
        WHERE t.status = 'COMPLETED'
    ) AS completed_tasks,

    COALESCE(
        ROUND(AVG(t.progress), 2),
        0
    ) AS average_task_progress

FROM team_members m

LEFT JOIN project_tasks t
    ON t.assigned_to = m.member_id

GROUP BY
    m.member_id,
    m.employee_code,
    m.full_name,
    m.role_name,
    m.skill_level,
    m.workload_percentage;

-- ============================================================
-- 18. MERGE-FREE LEADERSHIP REPORTING: RISK VIEW
-- ============================================================

CREATE OR REPLACE VIEW project_risk_register AS
SELECT
    r.risk_id,
    p.project_name,
    r.risk_code,
    r.description,
    r.probability,
    r.impact,

    r.probability * r.impact AS risk_exposure,

    classify_risk(
        r.probability,
        r.impact
    ) AS calculated_risk_level,

    m.full_name AS risk_owner,

    r.mitigation_plan,
    r.status

FROM project_risks r

JOIN projects p
    ON p.project_id = r.project_id

JOIN team_members m
    ON m.member_id = r.owner_id;

-- ============================================================
-- 19. SAMPLE PROJECT AND TEAM DATA
-- ============================================================

INSERT INTO team_members (
    employee_code,
    full_name,
    role_name,
    skill_level,
    development_goal
)
VALUES
(
    'EMP001',
    'Ananya Sharma',
    'Project Manager',
    'EXPERT',
    'Strategic leadership and governance'
),
(
    'EMP002',
    'Rahul Verma',
    'Technical Lead',
    'ADVANCED',
    'Technical leadership and mentoring'
),
(
    'EMP003',
    'Meera Singh',
    'Business Analyst',
    'COMPETENT',
    'Stakeholder engagement'
),
(
    'EMP004',
    'Arjun Kumar',
    'Junior Developer',
    'DEVELOPING',
    'Technical skill development'
);

INSERT INTO projects (
    project_code,
    project_name,
    description,
    project_manager_id,
    default_leadership_style,
    start_date,
    planned_end_date,
    budget,
    status
)
VALUES (
    'DT-2026-001',
    'Enterprise Digital Transformation',
    'Implementation of an integrated enterprise platform.',
    1,
    'TRANSFORMATIONAL',
    '2026-11-01',
    '2027-06-30',
    2500000,
    'ACTIVE'
);

INSERT INTO project_team (
    project_id,
    member_id,
    assignment_role,
    allocation_percentage
)
VALUES
(1, 1, 'Project Manager', 50),
(1, 2, 'Technical Lead', 80),
(1, 3, 'Business Analyst', 75),
(1, 4, 'Developer', 70);

-- ============================================================
-- 20. STAKEHOLDER SAMPLE DATA
-- ============================================================

INSERT INTO stakeholders (
    project_id,
    stakeholder_name,
    stakeholder_role,
    influence,
    interest,
    expectations,
    engagement_strategy
)
VALUES
(
    1,
    'Executive Sponsor',
    'Executive Management',
    5,
    5,
    'Achieve strategic project objectives.',
    'MANAGE_CLOSELY'
),
(
    1,
    'Operations Manager',
    'Operations',
    4,
    3,
    'Maintain operational continuity.',
    'KEEP_SATISFIED'
),
(
    1,
    'End Users',
    'System Users',
    2,
    5,
    'Ensure system usability.',
    'KEEP_INFORMED'
),
(
    1,
    'External Observer',
    'External Stakeholder',
    2,
    2,
    'Receive periodic progress information.',
    'MONITOR'
);

-- ============================================================
-- 21. TASK SAMPLE DATA
-- ============================================================

INSERT INTO project_tasks (
    project_id,
    task_code,
    title,
    description,
    required_skill,
    estimated_hours,
    priority,
    status,
    progress,
    assigned_to,
    delegated_by
)
VALUES
(
    1,
    'TASK-001',
    'Architecture assessment',
    'Assess the enterprise technical architecture.',
    'ADVANCED',
    40,
    5,
    'IN_PROGRESS',
    60,
    2,
    1
),
(
    1,
    'TASK-002',
    'Requirements analysis',
    'Collect and validate business requirements.',
    'COMPETENT',
    30,
    4,
    'COMPLETED',
    100,
    3,
    1
),
(
    1,
    'TASK-003',
    'Implementation planning',
    'Develop a phased implementation plan.',
    'ADVANCED',
    25,
    5,
    'NOT_STARTED',
    0,
    NULL,
    NULL
),
(
    1,
    'TASK-004',
    'Technical documentation',
    'Prepare technical documentation.',
    'DEVELOPING',
    20,
    3,
    'NOT_STARTED',
    0,
    NULL,
    NULL
);

-- ============================================================
-- 22. RISK SAMPLE DATA
-- ============================================================

INSERT INTO project_risks (
    project_id,
    risk_code,
    description,
    probability,
    impact,
    owner_id,
    mitigation_plan,
    contingency_plan,
    status
)
VALUES
(
    1,
    'RISK-001',
    'Technical integration delay',
    4,
    5,
    2,
    'Introduce weekly integration checkpoints.',
    'Use additional integration capacity.',
    'OPEN'
),
(
    1,
    'RISK-002',
    'Insufficient stakeholder participation',
    2,
    3,
    1,
    'Schedule structured stakeholder consultations.',
    'Escalate to the executive sponsor.',
    'OPEN'
),
(
    1,
    'RISK-003',
    'Resource availability',
    3,
    4,
    1,
    'Maintain a resource contingency plan.',
    'Reprioritize non-critical activities.',
    'MITIGATING'
);

-- ============================================================
-- 23. LEADERSHIP DECISION SAMPLE DATA
-- ============================================================

INSERT INTO leadership_decisions (
    project_id,
    decision_code,
    title,
    description,
    decision_maker,
    status
)
VALUES (
    1,
    'DEC-001',
    'Phased implementation strategy',
    'Implement the enterprise platform through controlled releases.',
    1,
    'PROPOSED'
);

INSERT INTO decision_options (
    decision_id,
    option_name,
    advantages,
    disadvantages,
    estimated_cost,
    estimated_duration_days,
    selected
)
VALUES
(
    1,
    'Full deployment',
    'Single implementation cycle.',
    'Higher operational disruption risk.',
    2500000,
    180,
    FALSE
),
(
    1,
    'Phased deployment',
    'Controlled risk and incremental feedback.',
    'Requires coordinated release management.',
    2400000,
    210,
    TRUE
);

-- ============================================================
-- 24. CONFLICT SAMPLE DATA
-- ============================================================

INSERT INTO project_conflicts (
    project_id,
    issue_title,
    description,
    conflict_type,
    resolution_method,
    proposed_resolution,
    raised_by,
    status
)
VALUES (
    1,
    'Deployment priority disagreement',
    'Technical and operations teams disagree about deployment timing.',
    'PRIORITY',
    'COLLABORATION',
    'Adopt a phased implementation approach.',
    2,
    'IN_PROGRESS'
);

-- ============================================================
-- 25. DECISION PROCESSING TRANSACTION
-- ============================================================

BEGIN;

CALL process_leadership_decision(
    1,
    'APPROVED',
    'Phased delivery reduces implementation risk and operational disruption.'
);

COMMIT;

-- ============================================================
-- 26. RETRIEVAL QUERIES
-- ============================================================

-- Retrieve all projects and their managers.
SELECT
    p.project_code,
    p.project_name,
    m.full_name AS project_manager,
    p.default_leadership_style,
    p.status
FROM projects p
LEFT JOIN team_members m
    ON m.member_id = p.project_manager_id;

-- Retrieve project tasks with ownership.
SELECT
    t.task_code,
    t.title,
    t.status,
    t.progress,
    m.full_name AS assigned_member
FROM project_tasks t
LEFT JOIN team_members m
    ON m.member_id = t.assigned_to
WHERE t.project_id = 1
ORDER BY t.priority DESC, t.task_id;

-- ============================================================
-- 27. VALIDATION QUERIES
-- ============================================================

-- Identify active tasks without owners.
SELECT
    task_id,
    title,
    status
FROM project_tasks
WHERE status IN ('IN_PROGRESS', 'COMPLETED')
  AND assigned_to IS NULL;

-- Identify members approaching workload capacity.
SELECT
    member_id,
    full_name,
    workload_percentage
FROM team_members
WHERE workload_percentage >= 80
ORDER BY workload_percentage DESC;

-- Identify tasks assigned below the required skill level.
SELECT
    t.task_id,
    t.title,
    t.required_skill,
    m.full_name,
    m.skill_level
FROM project_tasks t
JOIN team_members m
    ON m.member_id = t.assigned_to
WHERE
    CASE m.skill_level
        WHEN 'BEGINNER' THEN 1
        WHEN 'DEVELOPING' THEN 2
        WHEN 'COMPETENT' THEN 3
        WHEN 'ADVANCED' THEN 4
        WHEN 'EXPERT' THEN 5
    END
    <
    CASE t.required_skill
        WHEN 'BEGINNER' THEN 1
        WHEN 'DEVELOPING' THEN 2
        WHEN 'COMPETENT' THEN 3
        WHEN 'ADVANCED' THEN 4
        WHEN 'EXPERT' THEN 5
    END;

-- ============================================================
-- 28. AGGREGATION AND PERFORMANCE REPORTING
-- ============================================================

SELECT *
FROM project_leadership_metrics
ORDER BY project_id;

SELECT *
FROM team_performance
ORDER BY workload_percentage DESC;

-- ============================================================
-- 29. RISK EVALUATION
-- ============================================================

SELECT *
FROM project_risk_register
ORDER BY risk_exposure DESC;

-- ============================================================
-- 30. STAKEHOLDER ENGAGEMENT EVALUATION
-- ============================================================

SELECT
    stakeholder_name,
    influence,
    interest,
    determine_stakeholder_strategy(
        influence,
        interest
    ) AS recommended_strategy
FROM stakeholders
WHERE project_id = 1
ORDER BY influence DESC, interest DESC;

-- ============================================================
-- 31. WORKFLOW PROCESSING
-- ============================================================

-- Assign the implementation planning task to the technical lead.
-- This operation validates the member and assignment policy.

BEGIN;

UPDATE project_tasks
SET
    assigned_to = 2,
    delegated_by = 1,
    status = 'IN_PROGRESS'
WHERE task_id = 3
  AND status = 'NOT_STARTED';

COMMIT;

-- ============================================================
-- 32. RISK AND DECISION AGGREGATION
-- ============================================================

SELECT
    p.project_name,
    classify_risk(
        r.probability,
        r.impact
    ) AS risk_level,
    COUNT(*) AS risk_count
FROM project_risks r
JOIN projects p
    ON p.project_id = r.project_id
GROUP BY
    p.project_name,
    classify_risk(r.probability, r.impact)
ORDER BY p.project_name, risk_level;

SELECT
    status,
    COUNT(*) AS decision_count
FROM leadership_decisions
GROUP BY status
ORDER BY status;

-- ============================================================
-- 33. CTE-BASED LEADERSHIP PERFORMANCE ANALYSIS
-- ============================================================

WITH task_statistics AS (
    SELECT
        project_id,
        COUNT(*) AS total_tasks,
        COUNT(*) FILTER (
            WHERE status = 'COMPLETED'
        ) AS completed_tasks,
        AVG(progress) AS average_progress
    FROM project_tasks
    GROUP BY project_id
),
risk_statistics AS (
    SELECT
        project_id,
        COUNT(*) FILTER (
            WHERE status IN ('OPEN', 'MITIGATING')
        ) AS active_risks,
        COUNT(*) FILTER (
            WHERE status IN ('OPEN', 'MITIGATING')
              AND probability * impact >= 20
        ) AS critical_risks
    FROM project_risks
    GROUP BY project_id
)
SELECT
    p.project_name,
    COALESCE(t.total_tasks, 0) AS total_tasks,
    COALESCE(t.completed_tasks, 0) AS completed_tasks,
    COALESCE(
        ROUND(t.average_progress, 2),
        0
    ) AS average_progress,
    COALESCE(r.active_risks, 0) AS active_risks,
    COALESCE(r.critical_risks, 0) AS critical_risks
FROM projects p
LEFT JOIN task_statistics t
    ON t.project_id = p.project_id
LEFT JOIN risk_statistics r
    ON r.project_id = p.project_id;

-- ============================================================
-- 34. ELIGIBILITY DETERMINATION
-- ============================================================

-- A proposed leadership decision is eligible for processing
-- when its owner exists and it has at least one documented option.

SELECT
    d.decision_id,
    d.title,
    d.status,
    m.full_name AS decision_owner,
    COUNT(o.option_id) AS available_options,
    CASE
        WHEN d.status = 'PROPOSED'
         AND COUNT(o.option_id) >= 2
        THEN 'ELIGIBLE_FOR_DECISION'
        ELSE 'NOT_ELIGIBLE'
    END AS processing_eligibility
FROM leadership_decisions d
JOIN team_members m
    ON m.member_id = d.decision_maker
LEFT JOIN decision_options o
    ON o.decision_id = d.decision_id
GROUP BY
    d.decision_id,
    d.title,
    d.status,
    m.full_name;

-- ============================================================
-- 35. AUDIT REPORT
-- ============================================================

SELECT
    audit_id,
    project_id,
    actor_id,
    event_type,
    entity_type,
    entity_id,
    event_description,
    created_at
FROM leadership_audit_log
ORDER BY created_at DESC;

-- ============================================================
-- 36. DATABASE SECURITY AND PRODUCTION NOTES
-- ============================================================

-- Application roles should receive only the privileges they require.
-- Database credentials must not be stored in application source files.
-- Sensitive audit records should be protected against unauthorized changes.
-- Row-level security can be introduced when project-level isolation
-- is required by the deployment architecture.
--
-- Example role setup for a database administrator to execute:
--
-- CREATE ROLE project_leadership_reader NOLOGIN;
-- GRANT USAGE ON SCHEMA project_leadership
-- TO project_leadership_reader;
-- GRANT SELECT ON ALL TABLES IN SCHEMA project_leadership
-- TO project_leadership_reader;
--
-- CREATE ROLE project_leadership_operator NOLOGIN;
-- GRANT USAGE ON SCHEMA project_leadership
-- TO project_leadership_operator;
-- GRANT SELECT, INSERT, UPDATE ON
-- project_leadership.project_tasks
-- TO project_leadership_operator;
--
-- Sequence and procedure privileges should be granted separately
-- according to the application's operational requirements.
