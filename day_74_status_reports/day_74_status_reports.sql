/*
 * PROJECT STATUS REPORTING AND REPOSITORY GOVERNANCE
 * PostgreSQL 15+
 *
 * Models:
 *   Projects
 *   Project members
 *   Tasks
 *   Milestones
 *   Risks
 *   Status reports
 *   Pull Requests
 *   Commits
 *   Reviewers
 *   Code reviews
 *   Review comments and conversations
 *   Approval requirements
 *   Status checks
 *   Branch protection
 *   Merge eligibility
 *   Merge history
 *
 * The script is repeatable and uses a dedicated schema.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS project_reporting;

SET search_path TO project_reporting, public;

-- ============================================================
-- ENUMERATED DOMAIN TYPES
-- ============================================================

CREATE TYPE project_state AS ENUM (
    'not_started',
    'on_track',
    'at_risk',
    'delayed',
    'completed'
);

CREATE TYPE task_state AS ENUM (
    'todo',
    'in_progress',
    'blocked',
    'completed'
);

CREATE TYPE priority_level AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE risk_state AS ENUM (
    'open',
    'mitigating',
    'closed'
);

CREATE TYPE pull_request_state AS ENUM (
    'draft',
    'open',
    'merged',
    'closed'
);

CREATE TYPE review_state AS ENUM (
    'pending',
    'approved',
    'changes_requested',
    'commented',
    'dismissed'
);

CREATE TYPE merge_strategy AS ENUM (
    'merge_commit',
    'squash',
    'rebase'
);

-- ============================================================
-- PROJECT MASTER DATA
-- ============================================================

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    project_manager VARCHAR(150) NOT NULL,
    start_date DATE NOT NULL,
    target_date DATE NOT NULL,
    budget NUMERIC(14,2) NOT NULL,
    actual_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    state project_state NOT NULL DEFAULT 'not_started',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_project_dates
        CHECK (target_date >= start_date),

    CONSTRAINT positive_project_budget
        CHECK (budget > 0),

    CONSTRAINT nonnegative_project_cost
        CHECK (actual_cost >= 0)
);

CREATE TABLE project_members (
    member_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    member_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role_name VARCHAR(80) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE(project_id, email)
);

-- ============================================================
-- TASK MANAGEMENT
-- ============================================================

CREATE TABLE tasks (
    task_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    task_code VARCHAR(40) NOT NULL,
    title VARCHAR(250) NOT NULL,
    description TEXT,
    owner_id BIGINT REFERENCES project_members(member_id),
    state task_state NOT NULL DEFAULT 'todo',
    priority priority_level NOT NULL DEFAULT 'medium',
    estimated_hours NUMERIC(10,2) NOT NULL,
    actual_hours NUMERIC(10,2) NOT NULL DEFAULT 0,
    start_date DATE,
    due_date DATE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, task_code),

    CHECK (estimated_hours > 0),
    CHECK (actual_hours >= 0),
    CHECK (due_date IS NULL OR start_date IS NULL OR due_date >= start_date)
);

CREATE INDEX idx_tasks_project_state
    ON tasks(project_id, state);

CREATE INDEX idx_tasks_owner
    ON tasks(owner_id, state);

CREATE INDEX idx_tasks_due_date
    ON tasks(due_date)
    WHERE state <> 'completed';

-- ============================================================
-- MILESTONES
-- ============================================================

CREATE TABLE milestones (
    milestone_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    milestone_code VARCHAR(40) NOT NULL,
    milestone_name VARCHAR(200) NOT NULL,
    due_date DATE NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,

    UNIQUE(project_id, milestone_code),

    CHECK (
        (completed = FALSE AND completed_at IS NULL)
        OR
        (completed = TRUE AND completed_at IS NOT NULL)
    )
);

CREATE INDEX idx_milestones_project_due
    ON milestones(project_id, due_date);

-- ============================================================
-- RISK REGISTER
-- ============================================================

CREATE TABLE project_risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    risk_code VARCHAR(40) NOT NULL,
    description TEXT NOT NULL,
    probability SMALLINT NOT NULL,
    impact SMALLINT NOT NULL,
    owner_id BIGINT REFERENCES project_members(member_id),
    mitigation TEXT NOT NULL,
    state risk_state NOT NULL DEFAULT 'open',
    identified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,

    UNIQUE(project_id, risk_code),

    CHECK (probability BETWEEN 1 AND 5),
    CHECK (impact BETWEEN 1 AND 5),
    CHECK (
        (state = 'closed' AND closed_at IS NOT NULL)
        OR
        (state <> 'closed' AND closed_at IS NULL)
    )
);

CREATE INDEX idx_risks_project_state
    ON project_risks(project_id, state);

CREATE INDEX idx_risks_exposure
    ON project_risks((probability * impact) DESC)
    WHERE state <> 'closed';

-- ============================================================
-- REPOSITORY AND BRANCHES
-- ============================================================

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    repository_name VARCHAR(150) NOT NULL,
    default_branch VARCHAR(120) NOT NULL DEFAULT 'main',
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',

    UNIQUE(project_id, repository_name),

    CHECK (visibility IN ('private', 'public', 'internal'))
);

CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    branch_name VARCHAR(200) NOT NULL,
    head_commit_sha VARCHAR(64),
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(repository_id, branch_name)
);

-- ============================================================
-- REVIEWER DIRECTORY
-- ============================================================

CREATE TABLE reviewers (
    reviewer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    reviewer_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    can_approve BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE(repository_id, email)
);

-- ============================================================
-- BRANCH PROTECTION POLICY
-- ============================================================

CREATE TABLE branch_protection_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branches(branch_id),
    required_approvals INTEGER NOT NULL DEFAULT 2,
    require_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    require_up_to_date BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    allow_administrator_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (required_approvals >= 0)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id)
        ON DELETE CASCADE,
    check_name VARCHAR(150) NOT NULL,

    PRIMARY KEY(policy_id, check_name)
);

-- ============================================================
-- PULL REQUESTS
-- ============================================================

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    author_id BIGINT REFERENCES project_members(member_id),
    pr_number INTEGER NOT NULL,
    title VARCHAR(250) NOT NULL,
    description TEXT,
    state pull_request_state NOT NULL DEFAULT 'open',
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    has_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    base_synchronized BOOLEAN NOT NULL DEFAULT TRUE,
    conversations_resolved BOOLEAN NOT NULL DEFAULT TRUE,
    merge_strategy merge_strategy,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    merged_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,

    UNIQUE(repository_id, pr_number),

    CHECK (source_branch_id <> target_branch_id),

    CHECK (
        (state = 'merged' AND merged_at IS NOT NULL)
        OR
        (state <> 'merged' AND merged_at IS NULL)
    ),

    CHECK (
        (state = 'closed' AND closed_at IS NOT NULL)
        OR
        (state <> 'closed' AND closed_at IS NULL)
    )
);

CREATE INDEX idx_pr_repository_state
    ON pull_requests(repository_id, state);

CREATE INDEX idx_pr_target_branch
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_pr_created
    ON pull_requests(created_at DESC);

-- ============================================================
-- COMMITS
-- ============================================================

CREATE TABLE commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_sha VARCHAR(64) NOT NULL,
    author_name VARCHAR(150) NOT NULL,
    commit_message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL,

    UNIQUE(pull_request_id, commit_sha)
);

CREATE INDEX idx_commits_pr
    ON commits(pull_request_id);

-- ============================================================
-- CODE REVIEWS
-- ============================================================

CREATE TABLE code_reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id),
    reviewer_id BIGINT NOT NULL REFERENCES reviewers(reviewer_id),
    state review_state NOT NULL DEFAULT 'pending',
    submitted_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    summary TEXT,

    UNIQUE(pull_request_id, reviewer_id),

    CHECK (
        state <> 'approved'
        OR submitted_at IS NOT NULL
    )
);

CREATE INDEX idx_reviews_pr_state
    ON code_reviews(pull_request_id, state);

-- ============================================================
-- INLINE COMMENTS AND CONVERSATIONS
-- ============================================================

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES code_reviews(review_id)
        ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    line_number INTEGER,
    comment_body TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (line_number IS NULL OR line_number > 0)
);

CREATE INDEX idx_comments_review_resolution
    ON review_comments(review_id, is_resolved);

-- ============================================================
-- AUTOMATED STATUS CHECKS
-- ============================================================

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name VARCHAR(150) NOT NULL,
    passed BOOLEAN NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT,

    UNIQUE(pull_request_id, check_name)
);

CREATE INDEX idx_checks_pr
    ON status_checks(pull_request_id, check_name);

-- ============================================================
-- MERGE HISTORY
-- ============================================================

CREATE TABLE merge_history (
    merge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id),
    merged_by VARCHAR(150) NOT NULL,
    strategy merge_strategy NOT NULL,
    merge_commit_sha VARCHAR(64) NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- STATUS REPORTS
-- ============================================================

CREATE TABLE status_reports (
    report_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    reporting_period_start DATE NOT NULL,
    reporting_period_end DATE NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    overall_status project_state NOT NULL,
    completion_percentage NUMERIC(6,2) NOT NULL,
    milestone_completion_percentage NUMERIC(6,2) NOT NULL,
    budget_utilization NUMERIC(8,2) NOT NULL,
    budget_variance NUMERIC(14,2) NOT NULL,
    total_tasks INTEGER NOT NULL,
    completed_tasks INTEGER NOT NULL,
    blocked_tasks INTEGER NOT NULL,
    active_risks INTEGER NOT NULL,
    critical_risks INTEGER NOT NULL,
    executive_summary TEXT,

    CHECK (reporting_period_end >= reporting_period_start),
    CHECK (completion_percentage BETWEEN 0 AND 100),
    CHECK (milestone_completion_percentage BETWEEN 0 AND 100),
    CHECK (total_tasks >= 0),
    CHECK (completed_tasks BETWEEN 0 AND total_tasks),
    CHECK (blocked_tasks BETWEEN 0 AND total_tasks),
    CHECK (active_risks >= 0),
    CHECK (critical_risks BETWEEN 0 AND active_risks)
);

CREATE INDEX idx_reports_project_period
    ON status_reports(project_id, reporting_period_end DESC);

-- ============================================================
-- AUTOMATIC TIMESTAMP MANAGEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION update_project_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_project_timestamp
BEFORE UPDATE ON projects
FOR EACH ROW
EXECUTE FUNCTION update_project_timestamp();

-- ============================================================
-- APPROVAL VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_review_submission()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_active BOOLEAN;
    v_can_approve BOOLEAN;
    v_repository BIGINT;
    v_pr_repository BIGINT;
BEGIN
    SELECT active, can_approve, repository_id
    INTO v_active, v_can_approve, v_repository
    FROM reviewers
    WHERE reviewer_id = NEW.reviewer_id;

    SELECT repository_id
    INTO v_pr_repository
    FROM pull_requests
    WHERE pull_request_id = NEW.pull_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pull Request does not exist.';
    END IF;

    IF v_repository <> v_pr_repository THEN
        RAISE EXCEPTION 'Reviewer belongs to another repository.';
    END IF;

    IF NEW.state = 'approved' THEN
        IF NOT v_active OR NOT v_can_approve THEN
            RAISE EXCEPTION 'Reviewer is not eligible to approve.';
        END IF;

        IF NEW.submitted_at IS NULL THEN
            NEW.submitted_at := CURRENT_TIMESTAMP;
        END IF;
    END IF;

    IF NEW.state = 'dismissed' THEN
        NEW.dismissed_at := COALESCE(
            NEW.dismissed_at,
            CURRENT_TIMESTAMP
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_review_validation
BEFORE INSERT OR UPDATE ON code_reviews
FOR EACH ROW
EXECUTE FUNCTION validate_review_submission();

-- ============================================================
-- MERGE ELIGIBILITY FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reasons TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_pr pull_requests%ROWTYPE;
    v_policy branch_protection_policies%ROWTYPE;
    v_approvals INTEGER;
    v_reasons TEXT[] := ARRAY[]::TEXT[];
    v_required TEXT;
    v_passed BOOLEAN;
    v_policy_exists BOOLEAN;
BEGIN

    SELECT *
    INTO v_pr
    FROM pull_requests
    WHERE pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pull Request % not found.', p_pull_request_id;
    END IF;

    IF v_pr.state <> 'open' THEN
        v_reasons := array_append(
            v_reasons,
            'Pull Request is not open.'
        );
    END IF;

    IF v_pr.is_draft THEN
        v_reasons := array_append(
            v_reasons,
            'Draft Pull Request cannot be merged.'
        );
    END IF;

    IF v_pr.has_conflicts THEN
        v_reasons := array_append(
            v_reasons,
            'Merge conflicts must be resolved.'
        );
    END IF;

    SELECT *
    INTO v_policy
    FROM branch_protection_policies
    WHERE branch_id = v_pr.target_branch_id
      AND active = TRUE;

    v_policy_exists := FOUND;

    IF NOT v_policy_exists THEN
        RETURN QUERY
        SELECT
            array_length(v_reasons, 1) IS NULL,
            v_reasons;
        RETURN;
    END IF;

    SELECT COUNT(DISTINCT reviewer_id)::INTEGER
    INTO v_approvals
    FROM code_reviews
    WHERE pull_request_id = p_pull_request_id
      AND state = 'approved'
      AND dismissed_at IS NULL
      AND submitted_at IS NOT NULL;

    IF v_approvals < v_policy.required_approvals THEN
        v_reasons := array_append(
            v_reasons,
            format(
                'Insufficient approvals: %s/%s.',
                v_approvals,
                v_policy.required_approvals
            )
        );
    END IF;

    IF v_policy.require_up_to_date
       AND NOT v_pr.base_synchronized THEN
        v_reasons := array_append(
            v_reasons,
            'Source branch must be synchronized.'
        );
    END IF;

    IF v_policy.require_conversations
       AND (
           NOT v_pr.conversations_resolved
           OR EXISTS (
               SELECT 1
               FROM review_comments rc
               JOIN code_reviews cr
                 ON cr.review_id = rc.review_id
               WHERE cr.pull_request_id = p_pull_request_id
                 AND NOT rc.is_resolved
           )
       ) THEN
        v_reasons := array_append(
            v_reasons,
            'Unresolved review conversations exist.'
        );
    END IF;

    IF v_policy.require_linear_history
       AND v_pr.merge_strategy = 'merge_commit' THEN
        v_reasons := array_append(
            v_reasons,
            'Merge commit violates linear-history policy.'
        );
    END IF;

    FOR v_required IN
        SELECT check_name
        FROM required_status_checks
        WHERE policy_id = v_policy.policy_id
    LOOP

        SELECT sc.passed
        INTO v_passed
        FROM status_checks sc
        WHERE sc.pull_request_id = p_pull_request_id
          AND sc.check_name = v_required;

        IF NOT FOUND OR NOT COALESCE(v_passed, FALSE) THEN
            v_reasons := array_append(
                v_reasons,
                'Required check failed or missing: ' || v_required
            );
        END IF;

    END LOOP;

    RETURN QUERY
    SELECT
        COALESCE(array_length(v_reasons, 1), 0) = 0,
        v_reasons;
END;
$$;

-- ============================================================
-- CONTROLLED MERGE PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE merge_pull_request(
    p_pull_request_id BIGINT,
    p_merged_by VARCHAR,
    p_strategy merge_strategy,
    p_merge_sha VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_eligible BOOLEAN;
    v_reasons TEXT[];
    v_pr pull_requests%ROWTYPE;
BEGIN

    SELECT *
    INTO v_pr
    FROM pull_requests
    WHERE pull_request_id = p_pull_request_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pull Request not found.';
    END IF;

    IF v_pr.state <> 'open' OR v_pr.is_draft THEN
        RAISE EXCEPTION 'Pull Request is not mergeable.';
    END IF;

    SELECT e.eligible, e.reasons
    INTO v_eligible, v_reasons
    FROM evaluate_merge_eligibility(p_pull_request_id) e;

    IF NOT v_eligible THEN
        RAISE EXCEPTION 'Merge rejected: %', array_to_string(v_reasons, '; ');
    END IF;

    IF p_merged_by IS NULL OR btrim(p_merged_by) = ''
       OR p_merge_sha IS NULL OR btrim(p_merge_sha) = '' THEN
        RAISE EXCEPTION 'Merge actor and commit SHA are required.';
    END IF;

    UPDATE pull_requests
    SET state = 'merged',
        merge_strategy = p_strategy,
        merged_at = CURRENT_TIMESTAMP
    WHERE pull_request_id = p_pull_request_id;

    INSERT INTO merge_history (
        pull_request_id,
        merged_by,
        strategy,
        merge_commit_sha
    )
    VALUES (
        p_pull_request_id,
        p_merged_by,
        p_strategy,
        p_merge_sha
    );

END;
$$;

-- ============================================================
-- REPORTING VIEWS
-- ============================================================

CREATE OR REPLACE VIEW project_delivery_summary AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    COUNT(t.task_id) AS total_tasks,
    COUNT(t.task_id) FILTER (
        WHERE t.state = 'completed'
    ) AS completed_tasks,
    COUNT(t.task_id) FILTER (
        WHERE t.state = 'in_progress'
    ) AS in_progress_tasks,
    COUNT(t.task_id) FILTER (
        WHERE t.state = 'blocked'
    ) AS blocked_tasks,
    ROUND(
        100.0 * COUNT(t.task_id) FILTER (
            WHERE t.state = 'completed'
        ) / NULLIF(COUNT(t.task_id), 0),
        2
    ) AS completion_percentage
FROM projects p
LEFT JOIN tasks t
    ON t.project_id = p.project_id
GROUP BY
    p.project_id,
    p.project_code,
    p.project_name;

CREATE OR REPLACE VIEW project_risk_summary AS
SELECT
    p.project_id,
    p.project_name,
    COUNT(r.risk_id) FILTER (
        WHERE r.state <> 'closed'
    ) AS active_risks,
    COUNT(r.risk_id) FILTER (
        WHERE r.state <> 'closed'
          AND r.probability * r.impact >= 15
    ) AS critical_risks,
    COALESCE(
        MAX(r.probability * r.impact) FILTER (
            WHERE r.state <> 'closed'
        ),
        0
    ) AS maximum_exposure
FROM projects p
LEFT JOIN project_risks r
    ON r.project_id = p.project_id
GROUP BY p.project_id, p.project_name;

CREATE OR REPLACE VIEW pull_request_reporting AS
SELECT
    pr.pull_request_id,
    pr.pr_number,
    pr.title,
    pr.state,
    pr.is_draft,
    COUNT(DISTINCT c.commit_id) AS commit_count,
    COUNT(DISTINCT cr.reviewer_id) FILTER (
        WHERE cr.state = 'approved'
          AND cr.dismissed_at IS NULL
    ) AS approval_count,
    COUNT(DISTINCT sc.status_check_id) FILTER (
        WHERE sc.passed
    ) AS passed_checks,
    COUNT(DISTINCT sc.status_check_id) FILTER (
        WHERE NOT sc.passed
    ) AS failed_checks
FROM pull_requests pr
LEFT JOIN commits c
    ON c.pull_request_id = pr.pull_request_id
LEFT JOIN code_reviews cr
    ON cr.pull_request_id = pr.pull_request_id
LEFT JOIN status_checks sc
    ON sc.pull_request_id = pr.pull_request_id
GROUP BY
    pr.pull_request_id,
    pr.pr_number,
    pr.title,
    pr.state,
    pr.is_draft;

-- ============================================================
-- REPORT GENERATION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE generate_project_status_report(
    p_project_id BIGINT,
    p_period_start DATE,
    p_period_end DATE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_budget NUMERIC(14,2);
    v_actual NUMERIC(14,2);
    v_completion NUMERIC(6,2);
    v_milestone_completion NUMERIC(6,2);
    v_total INTEGER;
    v_completed INTEGER;
    v_blocked INTEGER;
    v_active_risks INTEGER;
    v_critical_risks INTEGER;
    v_status project_state;
BEGIN

    IF p_period_end < p_period_start THEN
        RAISE EXCEPTION 'Invalid reporting period.';
    END IF;

    SELECT budget, actual_cost
    INTO v_budget, v_actual
    FROM projects
    WHERE project_id = p_project_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Project not found.';
    END IF;

    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE state = 'completed'),
        COUNT(*) FILTER (WHERE state = 'blocked')
    INTO
        v_total,
        v_completed,
        v_blocked
    FROM tasks
    WHERE project_id = p_project_id;

    v_completion := COALESCE(
        ROUND(100.0 * v_completed / NULLIF(v_total, 0), 2),
        0
    );

    SELECT COALESCE(
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE completed)
            / NULLIF(COUNT(*), 0),
            2
        ),
        0
    )
    INTO v_milestone_completion
    FROM milestones
    WHERE project_id = p_project_id;

    SELECT
        COUNT(*) FILTER (WHERE state <> 'closed'),
        COUNT(*) FILTER (
            WHERE state <> 'closed'
              AND probability * impact >= 15
        )
    INTO v_active_risks, v_critical_risks
    FROM project_risks
    WHERE project_id = p_project_id;

    IF v_total > 0 AND v_completed = v_total THEN
        v_status := 'completed';

    ELSIF v_actual > v_budget THEN
        v_status := 'delayed';

    ELSIF EXISTS (
        SELECT 1
        FROM tasks
        WHERE project_id = p_project_id
          AND state = 'blocked'
          AND priority IN ('high', 'critical')
    ) THEN
        v_status := 'at_risk';

    ELSIF v_critical_risks > 0 THEN
        v_status := 'at_risk';

    ELSE
        v_status := CASE
            WHEN v_total = 0 THEN 'not_started'
            ELSE 'on_track'
        END;
    END IF;

    INSERT INTO status_reports (
        project_id,
        reporting_period_start,
        reporting_period_end,
        overall_status,
        completion_percentage,
        milestone_completion_percentage,
        budget_utilization,
        budget_variance,
        total_tasks,
        completed_tasks,
        blocked_tasks,
        active_risks,
        critical_risks,
        executive_summary
    )
    VALUES (
        p_project_id,
        p_period_start,
        p_period_end,
        v_status,
        v_completion,
        v_milestone_completion,
        ROUND(v_actual / v_budget * 100, 2),
        v_actual - v_budget,
        v_total,
        v_completed,
        v_blocked,
        v_active_risks,
        v_critical_risks,
        format(
            'Project health: %s. Delivery completion: %s%%. Active risks: %s.',
            v_status,
            v_completion,
            v_active_risks
        )
    );

END;
$$;

-- ============================================================
-- SAMPLE PROJECT DATA
-- ============================================================

INSERT INTO projects (
    project_code,
    project_name,
    project_manager,
    start_date,
    target_date,
    budget,
    actual_cost
)
VALUES (
    'PRJ-2026-001',
    'Enterprise Project Reporting Platform',
    'Project Manager',
    '2026-09-01',
    '2027-02-28',
    500000,
    185000
);

INSERT INTO project_members (
    project_id,
    member_name,
    email,
    role_name
)
SELECT
    project_id,
    member_name,
    email,
    role_name
FROM projects
CROSS JOIN (
    VALUES
        ('Project Manager', 'manager@example.org', 'project_manager'),
        ('Developer One', 'developer1@example.org', 'developer'),
        ('Developer Two', 'developer2@example.org', 'developer'),
        ('Security Lead', 'security@example.org', 'security_lead'),
        ('Data Lead', 'data@example.org', 'data_lead'),
        ('Analyst', 'analyst@example.org', 'analyst'),
        ('Operations Lead', 'operations@example.org', 'operations')
) AS members(member_name, email, role_name)
WHERE project_code = 'PRJ-2026-001';

INSERT INTO tasks (
    project_id,
    task_code,
    title,
    owner_id,
    state,
    priority,
    estimated_hours,
    actual_hours,
    start_date,
    due_date
)
SELECT
    p.project_id,
    data.task_code,
    data.title,
    m.member_id,
    data.state::task_state,
    data.priority::priority_level,
    data.estimated_hours,
    data.actual_hours,
    data.start_date,
    data.due_date
FROM projects p
CROSS JOIN (
    VALUES
    (
        'T001', 'Requirements analysis',
        'analyst@example.org',
        'completed', 'high', 80.00, 76.00,
        DATE '2026-09-01', DATE '2026-10-01'
    ),
    (
        'T002', 'Database implementation',
        'developer1@example.org',
        'completed', 'high', 120.00, 130.00,
        DATE '2026-10-02', DATE '2026-11-20'
    ),
    (
        'T003', 'Reporting engine',
        'developer2@example.org',
        'in_progress', 'high', 160.00, 70.00,
        DATE '2026-11-01', DATE '2027-01-10'
    ),
    (
        'T004', 'Security testing',
        'security@example.org',
        'blocked', 'critical', 60.00, 15.00,
        DATE '2026-11-05', DATE '2027-01-15'
    ),
    (
        'T005', 'Deployment preparation',
        'operations@example.org',
        'todo', 'medium', 50.00, 0.00,
        DATE '2027-01-15', DATE '2027-02-28'
    )
) AS data(
    task_code,
    title,
    owner_email,
    state,
    priority,
    estimated_hours,
    actual_hours,
    start_date,
    due_date
)
JOIN project_members m
    ON m.project_id = p.project_id
   AND m.email = data.owner_email
WHERE p.project_code = 'PRJ-2026-001';

INSERT INTO milestones (
    project_id,
    milestone_code,
    milestone_name,
    due_date,
    completed,
    completed_at
)
SELECT
    project_id,
    data.code,
    data.name,
    data.due_date,
    data.completed,
    data.completed_at
FROM projects
CROSS JOIN (
    VALUES
    (
        'M001',
        'Requirements approved',
        DATE '2026-10-01',
        TRUE,
        TIMESTAMPTZ '2026-10-01 12:00:00+05:30'
    ),
    (
        'M002',
        'Database completed',
        DATE '2026-11-20',
        TRUE,
        TIMESTAMPTZ '2026-11-20 12:00:00+05:30'
    ),
    (
        'M003',
        'System testing',
        DATE '2027-01-15',
        FALSE,
        NULL::TIMESTAMPTZ
    ),
    (
        'M004',
        'Production deployment',
        DATE '2027-02-28',
        FALSE,
        NULL::TIMESTAMPTZ
    )
) AS data(code, name, due_date, completed, completed_at)
WHERE project_code = 'PRJ-2026-001';

INSERT INTO project_risks (
    project_id,
    risk_code,
    description,
    probability,
    impact,
    owner_id,
    mitigation,
    state,
    closed_at
)
SELECT
    p.project_id,
    data.code,
    data.description,
    data.probability,
    data.impact,
    m.member_id,
    data.mitigation,
    data.state::risk_state,
    data.closed_at
FROM projects p
CROSS JOIN (
    VALUES
    (
        'R001',
        'Security testing environment unavailable',
        4, 5,
        'security@example.org',
        'Provision isolated testing infrastructure',
        'open',
        NULL::TIMESTAMPTZ
    ),
    (
        'R002',
        'Reporting data quality issues',
        3, 3,
        'data@example.org',
        'Introduce automated validation',
        'mitigating',
        NULL::TIMESTAMPTZ
    ),
    (
        'R003',
        'Requirements clarification completed',
        1, 2,
        'analyst@example.org',
        'Maintain approved requirements',
        'closed',
        TIMESTAMPTZ '2026-10-05 12:00:00+05:30'
    )
) AS data(
    code, description, probability, impact,
    owner_email, mitigation, state, closed_at
)
JOIN project_members m
    ON m.project_id = p.project_id
   AND m.email = data.owner_email
WHERE p.project_code = 'PRJ-2026-001';

-- ============================================================
-- REPOSITORY SAMPLE DATA
-- ============================================================

INSERT INTO repositories (
    project_id,
    repository_name,
    default_branch,
    visibility
)
SELECT
    project_id,
    'project-reporting-platform',
    'main',
    'private'
FROM projects
WHERE project_code = 'PRJ-2026-001';

INSERT INTO branches (
    repository_id,
    branch_name,
    head_commit_sha,
    protected
)
SELECT
    repository_id,
    branch_name,
    sha,
    branch_name = 'main'
FROM repositories
CROSS JOIN (
    VALUES
        ('main', 'a1b2c3d4e5f6'),
        ('feature/reporting', 'b2c3d4e5f6a1'),
        ('feature/security', 'c3d4e5f6a1b2')
) AS branch_data(branch_name, sha)
WHERE repository_name = 'project-reporting-platform';

INSERT INTO reviewers (
    repository_id,
    reviewer_name,
    email,
    active,
    can_approve
)
SELECT
    repository_id,
    data.name,
    data.email,
    TRUE,
    TRUE
FROM repositories
CROSS JOIN (
    VALUES
        ('Reviewer A', 'reviewer-a@example.org'),
        ('Reviewer B', 'reviewer-b@example.org'),
        ('Reviewer C', 'reviewer-c@example.org')
) AS data(name, email)
WHERE repository_name = 'project-reporting-platform';

INSERT INTO branch_protection_policies (
    branch_id,
    required_approvals,
    require_conversations,
    require_up_to_date,
    require_linear_history,
    allow_direct_push,
    allow_force_push,
    allow_deletion,
    allow_administrator_bypass
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    FALSE
FROM branches
WHERE branch_name = 'main';

INSERT INTO required_status_checks (
    policy_id,
    check_name
)
SELECT
    policy_id,
    check_name
FROM branch_protection_policies
CROSS JOIN (
    VALUES
        ('unit-tests'),
        ('security-scan'),
        ('lint')
) AS checks(check_name);

-- ============================================================
-- PULL REQUEST SAMPLE DATA
-- ============================================================

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    author_id,
    pr_number,
    title,
    description,
    state,
    is_draft,
    has_conflicts,
    base_synchronized,
    conversations_resolved
)
SELECT
    r.repository_id,
    source.branch_id,
    target.branch_id,
    author.member_id,
    data.pr_number,
    data.title,
    data.description,
    data.state::pull_request_state,
    data.is_draft,
    data.has_conflicts,
    data.base_synchronized,
    data.conversations_resolved
FROM repositories r
CROSS JOIN (
    VALUES
    (
        101,
        'Implement reporting API',
        'Add reporting endpoints and validation.',
        'open',
        FALSE,
        FALSE,
        TRUE,
        TRUE,
        'feature/reporting',
        'manager@example.org'
    ),
    (
        102,
        'Implement security controls',
        'Add access control and security validation.',
        'open',
        TRUE,
        FALSE,
        TRUE,
        FALSE,
        'feature/security',
        'manager@example.org'
    )
) AS data(
    pr_number,
    title,
    description,
    state,
    is_draft,
    has_conflicts,
    base_synchronized,
    conversations_resolved,
    source_branch,
    author_email
)
JOIN branches source
    ON source.repository_id = r.repository_id
   AND source.branch_name = data.source_branch
JOIN branches target
    ON target.repository_id = r.repository_id
   AND target.branch_name = 'main'
JOIN projects p
    ON p.project_id = r.project_id
JOIN project_members author
    ON author.project_id = p.project_id
   AND author.email = data.author_email
WHERE r.repository_name = 'project-reporting-platform';

INSERT INTO commits (
    pull_request_id,
    commit_sha,
    author_name,
    commit_message,
    committed_at
)
SELECT
    pr.pull_request_id,
    'commit-' || pr.pr_number || '-' || n.number,
    'Developer',
    'Implement reporting functionality',
    CURRENT_TIMESTAMP - (n.number * INTERVAL '1 day')
FROM pull_requests pr
CROSS JOIN LATERAL generate_series(
    1,
    CASE WHEN pr.pr_number = 101 THEN 4 ELSE 2 END
) AS n(number);

-- ============================================================
-- CODE REVIEW AND APPROVAL SAMPLE DATA
-- ============================================================

INSERT INTO code_reviews (
    pull_request_id,
    reviewer_id,
    state,
    submitted_at,
    summary
)
SELECT
    pr.pull_request_id,
    r.reviewer_id,
    'approved',
    CURRENT_TIMESTAMP,
    'Reviewed implementation and validation.'
FROM pull_requests pr
JOIN repositories repo
    ON repo.repository_id = pr.repository_id
JOIN reviewers r
    ON r.repository_id = repo.repository_id
WHERE pr.pr_number = 101
  AND r.email IN (
      'reviewer-a@example.org',
      'reviewer-b@example.org'
  );

INSERT INTO code_reviews (
    pull_request_id,
    reviewer_id,
    state,
    submitted_at,
    summary
)
SELECT
    pr.pull_request_id,
    r.reviewer_id,
    'changes_requested',
    CURRENT_TIMESTAMP,
    'Additional security validation is required.'
FROM pull_requests pr
JOIN repositories repo
    ON repo.repository_id = pr.repository_id
JOIN reviewers r
    ON r.repository_id = repo.repository_id
WHERE pr.pr_number = 102
  AND r.email = 'reviewer-c@example.org';

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    passed,
    details
)
SELECT
    pr.pull_request_id,
    data.check_name,
    data.passed,
    data.details
FROM pull_requests pr
CROSS JOIN (
    VALUES
        (101, 'unit-tests', TRUE, 'All tests passed.'),
        (101, 'security-scan', TRUE, 'No blocking findings.'),
        (101, 'lint', TRUE, 'No lint errors.'),
        (102, 'unit-tests', TRUE, 'All tests passed.'),
        (102, 'security-scan', FALSE, 'Security findings detected.')
) AS data(pr_number, check_name, passed, details)
WHERE pr.pr_number = data.pr_number;

-- ============================================================
-- REVIEW COMMENT FAILURE EXAMPLE
-- ============================================================

INSERT INTO review_comments (
    review_id,
    file_path,
    line_number,
    comment_body,
    is_resolved
)
SELECT
    cr.review_id,
    'src/security/access_control.py',
    42,
    'Validate authorization before processing the request.',
    FALSE
FROM code_reviews cr
JOIN pull_requests pr
    ON pr.pull_request_id = cr.pull_request_id
WHERE pr.pr_number = 102;

-- ============================================================
-- TRANSACTIONAL REPORT GENERATION
-- ============================================================

CALL generate_project_status_report(
    (
        SELECT project_id
        FROM projects
        WHERE project_code = 'PRJ-2026-001'
    ),
    DATE '2026-11-01',
    DATE '2026-11-13'
);

COMMIT;

-- ============================================================
-- RETRIEVAL: PROJECT STATUS
-- ============================================================

SELECT
    p.project_code,
    p.project_name,
    p.project_manager,
    p.state,
    p.budget,
    p.actual_cost,
    ROUND(p.actual_cost / p.budget * 100, 2)
        AS budget_utilization
FROM projects p
WHERE p.project_code = 'PRJ-2026-001';

-- ============================================================
-- DELIVERY AGGREGATION
-- ============================================================

SELECT *
FROM project_delivery_summary
ORDER BY project_name;

-- ============================================================
-- TASK VALIDATION AND EXCEPTION REPORT
-- ============================================================

SELECT
    task_code,
    title,
    priority,
    state,
    owner_id,
    due_date,
    estimated_hours,
    actual_hours,
    actual_hours - estimated_hours AS hours_variance
FROM tasks
WHERE actual_hours > estimated_hours
   OR state = 'blocked'
ORDER BY priority DESC, due_date;

-- ============================================================
-- MILESTONE REPORT
-- ============================================================

SELECT
    milestone_code,
    milestone_name,
    due_date,
    completed,
    CASE
        WHEN completed THEN 'COMPLETED'
        WHEN due_date < CURRENT_DATE THEN 'OVERDUE'
        ELSE 'PENDING'
    END AS milestone_status
FROM milestones
WHERE project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'PRJ-2026-001'
)
ORDER BY due_date;

-- ============================================================
-- RISK EVALUATION
-- ============================================================

SELECT
    risk_code,
    description,
    probability,
    impact,
    probability * impact AS exposure,
    owner_id,
    state,
    CASE
        WHEN state = 'closed' THEN 'CLOSED'
        WHEN probability * impact >= 15 THEN 'CRITICAL'
        WHEN probability * impact >= 8 THEN 'HIGH'
        WHEN probability * impact >= 4 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_level
FROM project_risks
ORDER BY exposure DESC;

-- ============================================================
-- EXECUTIVE STATUS REPORT RETRIEVAL
-- ============================================================

SELECT
    sr.generated_at,
    p.project_name,
    sr.reporting_period_start,
    sr.reporting_period_end,
    sr.overall_status,
    sr.completion_percentage,
    sr.milestone_completion_percentage,
    sr.budget_utilization,
    sr.budget_variance,
    sr.active_risks,
    sr.critical_risks,
    sr.executive_summary
FROM status_reports sr
JOIN projects p
    ON p.project_id = sr.project_id
ORDER BY sr.generated_at DESC;

-- ============================================================
-- PULL REQUEST REPORT
-- ============================================================

SELECT
    pr.pr_number,
    pr.title,
    pr.state,
    pr.is_draft,
    pr.commit_count,
    pr.approval_count,
    pr.passed_checks,
    pr.failed_checks
FROM pull_request_reporting pr
ORDER BY pr.pr_number;

-- ============================================================
-- MERGE ELIGIBILITY EVALUATION
-- ============================================================

SELECT
    pr.pr_number,
    pr.title,
    eligibility.eligible,
    eligibility.reasons
FROM pull_requests pr
CROSS JOIN LATERAL
    evaluate_merge_eligibility(pr.pull_request_id) eligibility
ORDER BY pr.pr_number;

-- ============================================================
-- APPROVAL AUDIT
-- ============================================================

SELECT
    pr.pr_number,
    rv.reviewer_name,
    cr.state,
    cr.submitted_at,
    cr.dismissed_at,
    rv.active,
    rv.can_approve
FROM code_reviews cr
JOIN pull_requests pr
    ON pr.pull_request_id = cr.pull_request_id
JOIN reviewers rv
    ON rv.reviewer_id = cr.reviewer_id
ORDER BY pr.pr_number, rv.reviewer_name;

-- ============================================================
-- UNRESOLVED REVIEW CONVERSATIONS
-- ============================================================

SELECT
    pr.pr_number,
    pr.title,
    rc.file_path,
    rc.line_number,
    rc.comment_body,
    rc.created_at
FROM review_comments rc
JOIN code_reviews cr
    ON cr.review_id = rc.review_id
JOIN pull_requests pr
    ON pr.pull_request_id = cr.pull_request_id
WHERE rc.is_resolved = FALSE
ORDER BY rc.created_at;

-- ============================================================
-- CTE: EXECUTIVE PROJECT HEALTH
-- ============================================================

WITH delivery AS (
    SELECT
        project_id,
        COUNT(*) AS total_tasks,
        COUNT(*) FILTER (
            WHERE state = 'completed'
        ) AS completed_tasks,
        COUNT(*) FILTER (
            WHERE state = 'blocked'
        ) AS blocked_tasks
    FROM tasks
    GROUP BY project_id
),
risk AS (
    SELECT
        project_id,
        COUNT(*) FILTER (
            WHERE state <> 'closed'
        ) AS active_risks,
        COUNT(*) FILTER (
            WHERE state <> 'closed'
              AND probability * impact >= 15
        ) AS critical_risks
    FROM project_risks
    GROUP BY project_id
)
SELECT
    p.project_code,
    p.project_name,
    COALESCE(d.total_tasks, 0) AS total_tasks,
    COALESCE(d.completed_tasks, 0) AS completed_tasks,
    COALESCE(d.blocked_tasks, 0) AS blocked_tasks,
    COALESCE(r.active_risks, 0) AS active_risks,
    COALESCE(r.critical_risks, 0) AS critical_risks,
    p.budget,
    p.actual_cost,
    CASE
        WHEN p.actual_cost > p.budget THEN 'DELAYED'
        WHEN COALESCE(r.critical_risks, 0) > 0 THEN 'AT RISK'
        WHEN COALESCE(d.blocked_tasks, 0) > 0 THEN 'REVIEW REQUIRED'
        ELSE 'ON TRACK'
    END AS operational_indicator
FROM projects p
LEFT JOIN delivery d ON d.project_id = p.project_id
LEFT JOIN risk r ON r.project_id = p.project_id;

-- ============================================================
-- REPORTING HISTORY AND PERIOD COMPARISON
-- ============================================================

SELECT
    project_id,
    reporting_period_start,
    reporting_period_end,
    overall_status,
    completion_percentage,
    budget_utilization,
    LAG(completion_percentage) OVER (
        PARTITION BY project_id
        ORDER BY reporting_period_end
    ) AS previous_completion,
    completion_percentage - LAG(completion_percentage) OVER (
        PARTITION BY project_id
        ORDER BY reporting_period_end
    ) AS completion_change
FROM status_reports
ORDER BY project_id, reporting_period_end;

-- ============================================================
-- ADMINISTRATIVE SECURITY NOTES
-- ============================================================

-- In production:
-- 1. Grant application roles only the permissions they require.
-- 2. Do not grant arbitrary users permission to execute merge procedures.
-- 3. Use a controlled database role for merge operations.
-- 4. Restrict access to reviewer identity and audit records.
-- 5. Use immutable external audit storage for regulated workflows.
-- 6. Configure row-level security where project-level isolation is required.
-- 7. Run report generation under a consistent transaction snapshot.
-- 8. Retain historical report records instead of overwriting them.
