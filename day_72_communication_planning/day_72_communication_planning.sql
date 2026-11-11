-- ============================================================
-- COMMUNICATION PLANNING AND MANAGEMENT DATABASE
-- PostgreSQL 15+
--
-- Models:
-- Organizations, stakeholders, communication objectives,
-- channels, communication activities, schedules, approvals,
-- messages, deliveries, feedback, costs, and evaluations.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS communication;

SET search_path TO communication, public;

-- ============================================================
-- 1. ORGANIZATIONAL STRUCTURE
-- ============================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(200) NOT NULL UNIQUE,
    organization_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT organization_name_nonempty
        CHECK (LENGTH(TRIM(organization_name)) > 0)
);

CREATE TABLE departments (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    department_name VARCHAR(150) NOT NULL,

    CONSTRAINT department_unique
        UNIQUE (organization_id, department_name)
);

CREATE TABLE stakeholders (
    stakeholder_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    department_id BIGINT
        REFERENCES departments(department_id),
    stakeholder_name VARCHAR(200) NOT NULL,
    email VARCHAR(254),
    audience_type VARCHAR(30) NOT NULL,
    influence_score SMALLINT NOT NULL DEFAULT 3,
    interest_score SMALLINT NOT NULL DEFAULT 3,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT stakeholder_audience_check
        CHECK (
            audience_type IN (
                'internal',
                'external',
                'management',
                'technical',
                'public'
            )
        ),

    CONSTRAINT stakeholder_influence_check
        CHECK (influence_score BETWEEN 1 AND 5),

    CONSTRAINT stakeholder_interest_check
        CHECK (interest_score BETWEEN 1 AND 5),

    CONSTRAINT stakeholder_name_nonempty
        CHECK (LENGTH(TRIM(stakeholder_name)) > 0)
);

CREATE UNIQUE INDEX stakeholder_email_unique
ON stakeholders(organization_id, LOWER(email))
WHERE email IS NOT NULL;

CREATE INDEX stakeholder_audience_idx
ON stakeholders(organization_id, audience_type, active);

-- ============================================================
-- 2. COMMUNICATION CHANNELS
-- ============================================================

CREATE TABLE communication_channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_code VARCHAR(40) NOT NULL UNIQUE,
    channel_name VARCHAR(100) NOT NULL,
    channel_type VARCHAR(30) NOT NULL,
    external_delivery BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT channel_type_check
        CHECK (
            channel_type IN (
                'synchronous',
                'asynchronous',
                'broadcast',
                'digital',
                'physical'
            )
        )
);

CREATE TABLE stakeholder_channel_preferences (
    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id) ON DELETE CASCADE,
    channel_id BIGINT NOT NULL
        REFERENCES communication_channels(channel_id),
    preference_rank SMALLINT NOT NULL DEFAULT 1,

    PRIMARY KEY (stakeholder_id, channel_id),

    CONSTRAINT preference_rank_check
        CHECK (preference_rank > 0)
);

-- ============================================================
-- 3. COMMUNICATION OBJECTIVES
-- ============================================================

CREATE TABLE communication_objectives (
    objective_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    objective_title VARCHAR(250) NOT NULL,
    objective_description TEXT NOT NULL,
    desired_outcome TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    start_at TIMESTAMPTZ,
    deadline TIMESTAMPTZ NOT NULL,
    created_by VARCHAR(150) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT objective_priority_check
        CHECK (
            priority IN ('low', 'medium', 'high', 'critical')
        ),

    CONSTRAINT objective_status_check
        CHECK (
            status IN ('draft', 'active', 'completed', 'cancelled')
        ),

    CONSTRAINT objective_deadline_check
        CHECK (
            start_at IS NULL OR deadline >= start_at
        ),

    CONSTRAINT objective_title_nonempty
        CHECK (LENGTH(TRIM(objective_title)) > 0)
);

CREATE TABLE objective_audiences (
    objective_id BIGINT NOT NULL
        REFERENCES communication_objectives(objective_id)
        ON DELETE CASCADE,
    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    PRIMARY KEY (objective_id, stakeholder_id)
);

CREATE INDEX objective_status_deadline_idx
ON communication_objectives(status, deadline);

-- ============================================================
-- 4. COMMUNICATION ACTIVITIES
-- ============================================================

CREATE TABLE communication_activities (
    activity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    objective_id BIGINT NOT NULL
        REFERENCES communication_objectives(objective_id),
    channel_id BIGINT NOT NULL
        REFERENCES communication_channels(channel_id),
    activity_title VARCHAR(250) NOT NULL,
    message_subject VARCHAR(250),
    message_content TEXT NOT NULL,
    owner_name VARCHAR(150) NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    estimated_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    actual_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'planned',
    approval_required BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by VARCHAR(150),
    approved_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT activity_cost_check
        CHECK (estimated_cost >= 0 AND actual_cost >= 0),

    CONSTRAINT activity_priority_check
        CHECK (
            priority IN ('low', 'medium', 'high', 'critical')
        ),

    CONSTRAINT activity_status_check
        CHECK (
            status IN (
                'planned',
                'approved',
                'scheduled',
                'in_progress',
                'sent',
                'completed',
                'failed',
                'cancelled'
            )
        ),

    CONSTRAINT approval_data_check
        CHECK (
            (approved_by IS NULL AND approved_at IS NULL)
            OR
            (approved_by IS NOT NULL AND approved_at IS NOT NULL)
        ),

    CONSTRAINT activity_title_nonempty
        CHECK (LENGTH(TRIM(activity_title)) > 0)
);

CREATE TABLE activity_audiences (
    activity_id BIGINT NOT NULL
        REFERENCES communication_activities(activity_id)
        ON DELETE CASCADE,
    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    PRIMARY KEY (activity_id, stakeholder_id)
);

CREATE INDEX activity_schedule_idx
ON communication_activities(scheduled_at, status);

CREATE INDEX activity_objective_idx
ON communication_activities(objective_id, status);

CREATE INDEX activity_owner_idx
ON communication_activities(owner_name, scheduled_at);

-- ============================================================
-- 5. APPROVAL WORKFLOW
-- ============================================================

CREATE TABLE activity_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activity_id BIGINT NOT NULL
        REFERENCES communication_activities(activity_id)
        ON DELETE CASCADE,
    approver_name VARCHAR(150) NOT NULL,
    decision VARCHAR(20) NOT NULL,
    comments TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT approval_decision_check
        CHECK (
            decision IN ('approved', 'rejected', 'returned')
        )
);

CREATE INDEX approval_activity_idx
ON activity_approvals(activity_id, decided_at DESC);

-- ============================================================
-- 6. COMMUNICATION DELIVERY
-- ============================================================

CREATE TABLE communication_deliveries (
    delivery_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activity_id BIGINT NOT NULL
        REFERENCES communication_activities(activity_id),
    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),
    delivery_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    delivery_reference VARCHAR(200),
    delivered_at TIMESTAMPTZ,
    error_message TEXT,
    attempt_number INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT delivery_status_check
        CHECK (
            delivery_status IN (
                'pending',
                'sent',
                'delivered',
                'failed',
                'bounced'
            )
        ),

    CONSTRAINT delivery_attempt_check
        CHECK (attempt_number > 0),

    CONSTRAINT delivery_attempt_unique
        UNIQUE (activity_id, stakeholder_id, attempt_number)
);

CREATE INDEX delivery_status_idx
ON communication_deliveries(delivery_status, activity_id);

-- ============================================================
-- 7. FEEDBACK AND EVALUATION
-- ============================================================

CREATE TABLE communication_feedback (
    feedback_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activity_id BIGINT NOT NULL
        REFERENCES communication_activities(activity_id),
    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),
    satisfaction SMALLINT NOT NULL,
    understanding SMALLINT NOT NULL,
    usefulness SMALLINT NOT NULL,
    comments TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT satisfaction_check
        CHECK (satisfaction BETWEEN 1 AND 5),

    CONSTRAINT understanding_check
        CHECK (understanding BETWEEN 1 AND 5),

    CONSTRAINT usefulness_check
        CHECK (usefulness BETWEEN 1 AND 5)
);

CREATE INDEX feedback_activity_idx
ON communication_feedback(activity_id);

-- ============================================================
-- 8. ORGANIZATIONAL COMMUNICATION POLICIES
-- ============================================================

CREATE TABLE communication_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    policy_name VARCHAR(200) NOT NULL,
    budget_limit NUMERIC(14,2) NOT NULL,
    minimum_notice_hours INTEGER NOT NULL DEFAULT 24,
    require_external_approval BOOLEAN NOT NULL DEFAULT TRUE,
    require_critical_approval BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_weekends BOOLEAN NOT NULL DEFAULT FALSE,
    maximum_activities INTEGER NOT NULL DEFAULT 1000,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT policy_budget_check
        CHECK (budget_limit >= 0),

    CONSTRAINT policy_notice_check
        CHECK (minimum_notice_hours >= 0),

    CONSTRAINT policy_activity_limit_check
        CHECK (maximum_activities > 0),

    UNIQUE (organization_id, policy_name)
);

-- ============================================================
-- 9. INTEGRITY TRIGGERS
-- ============================================================

CREATE OR REPLACE FUNCTION validate_activity_objective()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    objective_record communication_objectives%ROWTYPE;
BEGIN
    SELECT *
    INTO objective_record
    FROM communication_objectives
    WHERE objective_id = NEW.objective_id
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Communication objective does not exist.';
    END IF;

    IF objective_record.status <> 'active' THEN
        RAISE EXCEPTION 'Objective must be active.';
    END IF;

    IF NEW.scheduled_at > objective_record.deadline THEN
        RAISE EXCEPTION 'Activity exceeds objective deadline.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER activity_objective_validation
BEFORE INSERT OR UPDATE OF objective_id, scheduled_at
ON communication_activities
FOR EACH ROW
EXECUTE FUNCTION validate_activity_objective();


CREATE OR REPLACE FUNCTION validate_activity_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'planned'
            AND NEW.status IN ('approved', 'cancelled'))
        OR
        (OLD.status = 'approved'
            AND NEW.status IN ('scheduled', 'cancelled'))
        OR
        (OLD.status = 'scheduled'
            AND NEW.status IN ('in_progress', 'cancelled'))
        OR
        (OLD.status = 'in_progress'
            AND NEW.status IN ('sent', 'completed', 'failed'))
        OR
        (OLD.status = 'sent'
            AND NEW.status IN ('completed', 'failed'))
        OR
        (OLD.status = 'failed'
            AND NEW.status IN ('scheduled', 'cancelled'))
    ) THEN
        RAISE EXCEPTION
            'Invalid activity status transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    IF NEW.status = 'approved' THEN
        IF NEW.approved_by IS NULL OR NEW.approved_at IS NULL THEN
            RAISE EXCEPTION 'Approval information is required.';
        END IF;
    END IF;

    IF NEW.status = 'completed' THEN
        NEW.completed_at = COALESCE(
            NEW.completed_at,
            CURRENT_TIMESTAMP
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER activity_transition_validation
BEFORE UPDATE OF status
ON communication_activities
FOR EACH ROW
EXECUTE FUNCTION validate_activity_transition();


-- ============================================================
-- 10. BUDGET CONTROL
-- ============================================================

CREATE OR REPLACE FUNCTION enforce_communication_budget()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    organization_key BIGINT;
    budget_amount NUMERIC(14,2);
    committed_amount NUMERIC(14,2);
    policy_found BOOLEAN;
BEGIN
    SELECT o.organization_id
    INTO organization_key
    FROM communication_objectives o
    WHERE o.objective_id = NEW.objective_id;

    SELECT p.budget_limit
    INTO budget_amount
    FROM communication_policies p
    WHERE p.organization_id = organization_key
      AND p.active = TRUE
    ORDER BY p.policy_id
    LIMIT 1
    FOR UPDATE;

    policy_found := FOUND;

    IF NOT policy_found THEN
        RAISE EXCEPTION 'No active communication budget policy exists.';
    END IF;

    SELECT COALESCE(SUM(estimated_cost), 0)
    INTO committed_amount
    FROM communication_activities
    WHERE objective_id IN (
        SELECT objective_id
        FROM communication_objectives
        WHERE organization_id = organization_key
    )
      AND status <> 'cancelled'
      AND activity_id <> COALESCE(NEW.activity_id, -1);

    IF NEW.status <> 'cancelled'
       AND committed_amount + NEW.estimated_cost > budget_amount THEN
        RAISE EXCEPTION
            'Communication budget exceeded. Available budget: %',
            budget_amount - committed_amount;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER communication_budget_validation
BEFORE INSERT OR UPDATE OF estimated_cost, status, objective_id
ON communication_activities
FOR EACH ROW
EXECUTE FUNCTION enforce_communication_budget();


-- ============================================================
-- 11. ACTIVITY AUDIT
-- ============================================================

CREATE TABLE communication_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activity_id BIGINT NOT NULL
        REFERENCES communication_activities(activity_id),
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT NOT NULL DEFAULT CURRENT_USER
);

CREATE OR REPLACE FUNCTION record_activity_audit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO communication_audit (
            activity_id,
            old_status,
            new_status
        )
        VALUES (
            NEW.activity_id,
            OLD.status,
            NEW.status
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER activity_audit_trigger
AFTER UPDATE OF status
ON communication_activities
FOR EACH ROW
EXECUTE FUNCTION record_activity_audit();


-- ============================================================
-- 12. VIEWS
-- ============================================================

CREATE OR REPLACE VIEW stakeholder_engagement_matrix AS
SELECT
    stakeholder_id,
    stakeholder_name,
    audience_type,
    influence_score,
    interest_score,
    CASE
        WHEN influence_score >= 4 AND interest_score >= 4
            THEN 'manage_closely'
        WHEN influence_score >= 4
            THEN 'keep_satisfied'
        WHEN interest_score >= 4
            THEN 'keep_informed'
        ELSE 'monitor'
    END AS engagement_strategy
FROM stakeholders
WHERE active = TRUE;


CREATE OR REPLACE VIEW communication_activity_overview AS
SELECT
    a.activity_id,
    a.activity_title,
    o.objective_title,
    c.channel_name,
    a.owner_name,
    a.scheduled_at,
    a.status,
    a.estimated_cost,
    a.approval_required,
    a.approved_by,
    COUNT(DISTINCT aa.stakeholder_id) AS audience_size,
    COUNT(DISTINCT d.delivery_id) FILTER (
        WHERE d.delivery_status = 'delivered'
    ) AS delivered_count
FROM communication_activities a
JOIN communication_objectives o
    ON o.objective_id = a.objective_id
JOIN communication_channels c
    ON c.channel_id = a.channel_id
LEFT JOIN activity_audiences aa
    ON aa.activity_id = a.activity_id
LEFT JOIN communication_deliveries d
    ON d.activity_id = a.activity_id
GROUP BY
    a.activity_id,
    o.objective_title,
    c.channel_name;


CREATE OR REPLACE VIEW communication_performance AS
SELECT
    a.activity_id,
    a.activity_title,
    a.status,
    COUNT(f.feedback_id) AS feedback_count,
    ROUND(AVG(f.satisfaction), 2) AS average_satisfaction,
    ROUND(AVG(f.understanding), 2) AS average_understanding,
    ROUND(AVG(f.usefulness), 2) AS average_usefulness,
    a.estimated_cost,
    a.actual_cost
FROM communication_activities a
LEFT JOIN communication_feedback f
    ON f.activity_id = a.activity_id
GROUP BY
    a.activity_id,
    a.activity_title,
    a.status,
    a.estimated_cost,
    a.actual_cost;


-- ============================================================
-- 13. CHANNEL RECOMMENDATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION recommend_channel(
    p_stakeholder_id BIGINT
)
RETURNS VARCHAR
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    preferred_channel VARCHAR(40);
    audience VARCHAR(30);
BEGIN
    SELECT c.channel_code
    INTO preferred_channel
    FROM stakeholder_channel_preferences p
    JOIN communication_channels c
        ON c.channel_id = p.channel_id
    WHERE p.stakeholder_id = p_stakeholder_id
      AND c.active = TRUE
    ORDER BY p.preference_rank
    LIMIT 1;

    IF preferred_channel IS NOT NULL THEN
        RETURN preferred_channel;
    END IF;

    SELECT audience_type
    INTO audience
    FROM stakeholders
    WHERE stakeholder_id = p_stakeholder_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Stakeholder not found.';
    END IF;

    RETURN CASE audience
        WHEN 'management' THEN 'report'
        WHEN 'technical' THEN 'workshop'
        WHEN 'public' THEN 'website'
        ELSE 'email'
    END;
END;
$$;


-- ============================================================
-- 14. ELIGIBILITY AND SCHEDULING PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE schedule_communication(
    p_objective_id BIGINT,
    p_channel_id BIGINT,
    p_title VARCHAR,
    p_message TEXT,
    p_owner VARCHAR,
    p_scheduled_at TIMESTAMPTZ,
    p_cost NUMERIC,
    p_approval_required BOOLEAN
)
LANGUAGE plpgsql
AS $$
DECLARE
    new_activity_id BIGINT;
    required_approval BOOLEAN;
    objective_priority VARCHAR(20);
    external_audience BOOLEAN;
    external_approval BOOLEAN;
    critical_approval BOOLEAN;
BEGIN
    IF p_cost < 0 THEN
        RAISE EXCEPTION 'Cost cannot be negative.';
    END IF;

    IF p_scheduled_at <= CURRENT_TIMESTAMP THEN
        RAISE EXCEPTION 'Communication schedule must be in the future.';
    END IF;

    SELECT priority
    INTO objective_priority
    FROM communication_objectives
    WHERE objective_id = p_objective_id
      AND status = 'active';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active objective not found.';
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM objective_audiences oa
        JOIN stakeholders s
            ON s.stakeholder_id = oa.stakeholder_id
        WHERE oa.objective_id = p_objective_id
          AND s.audience_type = 'external'
    )
    INTO external_audience;

    SELECT require_external_approval, require_critical_approval
    INTO external_approval, critical_approval
    FROM communication_policies p
    JOIN communication_objectives o
        ON o.organization_id = p.organization_id
    WHERE o.objective_id = p_objective_id
      AND p.active = TRUE
    ORDER BY p.policy_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No active policy found.';
    END IF;

    required_approval :=
        p_approval_required
        OR (external_audience AND external_approval)
        OR (
            objective_priority = 'critical'
            AND critical_approval
        );

    INSERT INTO communication_activities (
        objective_id,
        channel_id,
        activity_title,
        message_content,
        owner_name,
        scheduled_at,
        estimated_cost,
        approval_required,
        status
    )
    VALUES (
        p_objective_id,
        p_channel_id,
        p_title,
        p_message,
        p_owner,
        p_scheduled_at,
        p_cost,
        required_approval,
        CASE
            WHEN required_approval THEN 'planned'
            ELSE 'scheduled'
        END
    )
    RETURNING activity_id INTO new_activity_id;

    RAISE NOTICE 'Created communication activity: %',
        new_activity_id;
END;
$$;


-- ============================================================
-- 15. SAMPLE DATA
-- ============================================================

INSERT INTO organizations (
    organization_name,
    organization_type
)
VALUES (
    'Enterprise Digital Services',
    'public_sector'
);

INSERT INTO departments (
    organization_id,
    department_name
)
SELECT organization_id, department_name
FROM organizations
CROSS JOIN (
    VALUES
        ('Administration'),
        ('Technology'),
        ('Operations'),
        ('Partnerships')
) AS d(department_name);

INSERT INTO stakeholders (
    organization_id,
    department_id,
    stakeholder_name,
    email,
    audience_type,
    influence_score,
    interest_score
)
SELECT
    o.organization_id,
    d.department_id,
    s.stakeholder_name,
    s.email,
    s.audience_type,
    s.influence_score,
    s.interest_score
FROM organizations o
JOIN (
    VALUES
        (
            'Administration',
            'Executive Management',
            'executives@example.org',
            'management',
            5,
            5
        ),
        (
            'Technology',
            'Technical Team',
            'technology@example.org',
            'technical',
            3,
            5
        ),
        (
            'Operations',
            'Employees',
            'employees@example.org',
            'internal',
            2,
            4
        ),
        (
            'Partnerships',
            'External Partners',
            'partners@example.org',
            'external',
            4,
            2
        )
) AS s(
    department_name,
    stakeholder_name,
    email,
    audience_type,
    influence_score,
    interest_score
)
    ON TRUE
JOIN departments d
    ON d.organization_id = o.organization_id
   AND d.department_name = s.department_name;

INSERT INTO communication_channels (
    channel_code,
    channel_name,
    channel_type,
    external_delivery
)
VALUES
    ('email', 'Email Communication', 'asynchronous', TRUE),
    ('meeting', 'Management Meeting', 'synchronous', FALSE),
    ('report', 'Formal Report', 'asynchronous', FALSE),
    ('newsletter', 'Internal Newsletter', 'broadcast', TRUE),
    ('website', 'Official Website', 'digital', TRUE),
    ('workshop', 'Technical Workshop', 'synchronous', FALSE),
    ('phone', 'Telephone', 'synchronous', TRUE),
    ('social_media', 'Social Media', 'broadcast', TRUE);

INSERT INTO stakeholder_channel_preferences (
    stakeholder_id,
    channel_id,
    preference_rank
)
SELECT
    s.stakeholder_id,
    c.channel_id,
    p.preference_rank
FROM (
    VALUES
        ('Executive Management', 'report', 1),
        ('Executive Management', 'meeting', 2),
        ('Technical Team', 'workshop', 1),
        ('Employees', 'email', 1),
        ('External Partners', 'email', 1)
) AS p(stakeholder_name, channel_code, preference_rank)
JOIN stakeholders s
    ON s.stakeholder_name = p.stakeholder_name
JOIN communication_channels c
    ON c.channel_code = p.channel_code;

INSERT INTO communication_policies (
    organization_id,
    policy_name,
    budget_limit,
    minimum_notice_hours,
    require_external_approval,
    require_critical_approval,
    restrict_weekends,
    maximum_activities
)
SELECT
    organization_id,
    'Standard Communication Governance',
    100000,
    24,
    TRUE,
    TRUE,
    FALSE,
    100
FROM organizations;

INSERT INTO communication_objectives (
    organization_id,
    objective_title,
    objective_description,
    desired_outcome,
    priority,
    status,
    start_at,
    deadline,
    created_by
)
SELECT
    organization_id,
    'Digital Transformation Communication',
    'Coordinate organizational digital transformation updates.',
    'Improve stakeholder awareness and participation.',
    'high',
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '30 days',
    'Project Director'
FROM organizations;

INSERT INTO objective_audiences (
    objective_id,
    stakeholder_id
)
SELECT
    o.objective_id,
    s.stakeholder_id
FROM communication_objectives o
CROSS JOIN stakeholders s;

-- ============================================================
-- 16. SAMPLE COMMUNICATION ACTIVITIES
-- ============================================================

INSERT INTO communication_activities (
    objective_id,
    channel_id,
    activity_title,
    message_subject,
    message_content,
    owner_name,
    scheduled_at,
    estimated_cost,
    priority,
    status,
    approval_required
)
SELECT
    o.objective_id,
    c.channel_id,
    x.activity_title,
    x.message_subject,
    x.message_content,
    x.owner_name,
    CURRENT_TIMESTAMP + x.days_after * INTERVAL '1 day',
    x.estimated_cost,
    x.priority,
    x.status,
    x.approval_required
FROM communication_objectives o
CROSS JOIN (
    VALUES
        (
            'meeting',
            'Management briefing',
            'Digital transformation briefing',
            'Present milestones, risks, and responsibilities.',
            'Project Director',
            2,
            15000::NUMERIC,
            'critical',
            'planned',
            TRUE
        ),
        (
            'workshop',
            'Technical workshop',
            'Implementation architecture',
            'Explain implementation responsibilities.',
            'Technical Lead',
            5,
            25000::NUMERIC,
            'high',
            'scheduled',
            FALSE
        ),
        (
            'newsletter',
            'Employee newsletter',
            'Transformation updates',
            'Share project milestones and participation details.',
            'Communications Manager',
            8,
            5000::NUMERIC,
            'medium',
            'scheduled',
            FALSE
        ),
        (
            'email',
            'Partner notification',
            'Operational changes',
            'Communicate relevant operational changes.',
            'Partnership Manager',
            10,
            2000::NUMERIC,
            'high',
            'planned',
            TRUE
        )
) AS x(
    channel_code,
    activity_title,
    message_subject,
    message_content,
    owner_name,
    days_after,
    estimated_cost,
    priority,
    status,
    approval_required
)
JOIN communication_channels c
    ON c.channel_code = x.channel_code
WHERE o.status = 'active';

INSERT INTO activity_audiences (
    activity_id,
    stakeholder_id
)
SELECT
    a.activity_id,
    s.stakeholder_id
FROM communication_activities a
JOIN (
    VALUES
        ('Management briefing', 'Executive Management'),
        ('Technical workshop', 'Technical Team'),
        ('Employee newsletter', 'Employees'),
        ('Partner notification', 'External Partners')
) AS mapping(activity_title, stakeholder_name)
    ON mapping.activity_title = a.activity_title
JOIN stakeholders s
    ON s.stakeholder_name = mapping.stakeholder_name;

-- ============================================================
-- 17. SAMPLE APPROVAL DECISIONS
-- ============================================================

INSERT INTO activity_approvals (
    activity_id,
    approver_name,
    decision,
    comments
)
SELECT
    activity_id,
    'Chief Operating Officer',
    'approved',
    'Communication content reviewed and authorized.'
FROM communication_activities
WHERE activity_title = 'Management briefing';

INSERT INTO communication_activities (
    objective_id,
    channel_id,
    activity_title,
    message_content,
    owner_name,
    scheduled_at,
    estimated_cost,
    approval_required,
    status,
    approved_by,
    approved_at
)
SELECT
    a.objective_id,
    a.channel_id,
    a.activity_title,
    a.message_content,
    a.owner_name,
    a.scheduled_at,
    a.estimated_cost,
    TRUE,
    'approved',
    'Chief Operating Officer',
    CURRENT_TIMESTAMP
FROM communication_activities a
WHERE a.activity_title = 'Management briefing';

-- The approval example above records a decision separately.
-- The original planned activity remains available for workflow
-- demonstration; the following update approves that activity.

UPDATE communication_activities
SET
    status = 'approved',
    approved_by = 'Chief Operating Officer',
    approved_at = CURRENT_TIMESTAMP
WHERE activity_title = 'Management briefing'
  AND status = 'planned';

UPDATE communication_activities
SET status = 'scheduled'
WHERE activity_title = 'Management briefing'
  AND status = 'approved';

-- ============================================================
-- 18. SAMPLE DELIVERY RECORDS
-- ============================================================

INSERT INTO communication_deliveries (
    activity_id,
    stakeholder_id,
    delivery_status,
    delivery_reference,
    delivered_at
)
SELECT
    aa.activity_id,
    aa.stakeholder_id,
    'delivered',
    'DELIVERY-' || aa.activity_id || '-' || aa.stakeholder_id,
    CURRENT_TIMESTAMP
FROM activity_audiences aa
JOIN communication_activities a
    ON a.activity_id = aa.activity_id
WHERE a.activity_title IN (
    'Management briefing',
    'Technical workshop'
);

INSERT INTO communication_feedback (
    activity_id,
    stakeholder_id,
    satisfaction,
    understanding,
    usefulness,
    comments
)
SELECT
    a.activity_id,
    s.stakeholder_id,
    5,
    4,
    5,
    'The communication was clear and useful.'
FROM communication_activities a
JOIN stakeholders s
    ON s.stakeholder_name = 'Technical Team'
WHERE a.activity_title = 'Technical workshop';


-- ============================================================
-- 19. RETRIEVAL AND REPORTING QUERIES
-- ============================================================

-- Communication schedule.
SELECT
    activity_title,
    owner_name,
    scheduled_at,
    status
FROM communication_activities
ORDER BY scheduled_at;

-- Stakeholder engagement analysis.
SELECT *
FROM stakeholder_engagement_matrix
ORDER BY influence_score DESC, interest_score DESC;

-- Channel recommendations.
SELECT
    s.stakeholder_name,
    recommend_channel(s.stakeholder_id) AS recommended_channel
FROM stakeholders s
ORDER BY s.stakeholder_name;

-- Activity and delivery overview.
SELECT *
FROM communication_activity_overview
ORDER BY scheduled_at;

-- Feedback evaluation.
SELECT *
FROM communication_performance
ORDER BY activity_id;

-- Cost aggregation.
SELECT
    o.objective_title,
    SUM(a.estimated_cost) AS planned_cost,
    SUM(a.actual_cost) AS actual_cost,
    COUNT(a.activity_id) AS activity_count
FROM communication_objectives o
LEFT JOIN communication_activities a
    ON a.objective_id = o.objective_id
GROUP BY o.objective_id, o.objective_title;

-- Channel utilization.
SELECT
    c.channel_name,
    COUNT(a.activity_id) AS activity_count,
    SUM(a.estimated_cost) AS estimated_spend
FROM communication_channels c
LEFT JOIN communication_activities a
    ON a.channel_id = c.channel_id
GROUP BY c.channel_id, c.channel_name
ORDER BY activity_count DESC;

-- CTE for objective-level execution performance.
WITH objective_metrics AS (
    SELECT
        o.objective_id,
        o.objective_title,
        COUNT(a.activity_id) AS total_activities,
        COUNT(a.activity_id) FILTER (
            WHERE a.status = 'completed'
        ) AS completed_activities,
        SUM(a.estimated_cost) AS planned_cost
    FROM communication_objectives o
    LEFT JOIN communication_activities a
        ON a.objective_id = o.objective_id
    GROUP BY o.objective_id, o.objective_title
)
SELECT
    objective_title,
    total_activities,
    completed_activities,
    ROUND(
        100.0 * completed_activities /
        NULLIF(total_activities, 0),
        2
    ) AS completion_percentage,
    COALESCE(planned_cost, 0) AS planned_cost
FROM objective_metrics;


-- ============================================================
-- 20. ELIGIBILITY VALIDATION
-- ============================================================

SELECT
    a.activity_id,
    a.activity_title,
    a.status,
    a.approval_required,
    CASE
        WHEN a.approval_required
             AND a.approved_by IS NULL
            THEN 'approval_required'
        WHEN a.scheduled_at <= CURRENT_TIMESTAMP
             AND a.status = 'planned'
            THEN 'schedule_review_required'
        WHEN a.status = 'cancelled'
            THEN 'not_eligible'
        WHEN a.status IN ('completed', 'sent')
            THEN 'already_executed'
        ELSE 'eligible_for_scheduling_review'
    END AS workflow_assessment
FROM communication_activities a
ORDER BY a.scheduled_at;


-- ============================================================
-- 21. TRANSACTIONAL WORKFLOW EXAMPLE
-- ============================================================

-- Execute an activity using row locking.
-- This example is rolled back to preserve the demonstration data.

SAVEPOINT workflow_example;

DO $$
DECLARE
    target_id BIGINT;
BEGIN
    SELECT activity_id
    INTO target_id
    FROM communication_activities
    WHERE activity_title = 'Technical workshop'
    LIMIT 1
    FOR UPDATE;

    IF target_id IS NULL THEN
        RAISE EXCEPTION 'Technical workshop not found.';
    END IF;

    UPDATE communication_activities
    SET
        status = 'in_progress',
        started_at = CURRENT_TIMESTAMP
    WHERE activity_id = target_id
      AND status = 'scheduled';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Activity is not ready to start.';
    END IF;
END;
$$;

ROLLBACK TO SAVEPOINT workflow_example;

-- ============================================================
-- 22. AUDIT RETRIEVAL
-- ============================================================

SELECT
    activity_id,
    old_status,
    new_status,
    changed_at,
    changed_by
FROM communication_audit
ORDER BY changed_at DESC;

-- ============================================================
-- 23. OPERATIONAL INDEXES AND QUERY SUPPORT
-- ============================================================

CREATE INDEX IF NOT EXISTS activity_priority_schedule_idx
ON communication_activities(priority, scheduled_at)
WHERE status IN ('planned', 'approved', 'scheduled');

CREATE INDEX IF NOT EXISTS active_stakeholder_department_idx
ON stakeholders(department_id, stakeholder_name)
WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS delivery_activity_status_idx
ON communication_deliveries(activity_id, delivery_status);

COMMIT;
