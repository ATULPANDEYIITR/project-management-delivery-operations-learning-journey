/*
===============================================================================
PROJECT COMMUNICATION MANAGEMENT
Introduction to Project Communication
PostgreSQL 15+

Relational implementation covering:
- Projects and stakeholders
- Stakeholder engagement
- Communication plans
- Communication messages
- Message recipients and acknowledgements
- Meetings and meeting participants
- Decisions
- Action items
- Audit history
- Communication policies
- Reporting and communication effectiveness
- Transactional message dispatch
- Integrity enforcement through constraints and triggers

Execution:
    psql -U postgres -d your_database -f project_communication.sql

The script creates and populates its own schema.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS project_comms;

SET search_path TO project_comms, public;

-- ============================================================================
-- 1. ENUMERATED DOMAIN TYPES
-- ============================================================================

CREATE TYPE stakeholder_role AS ENUM (
    'PROJECT_MANAGER',
    'SPONSOR',
    'TEAM_MEMBER',
    'CLIENT',
    'VENDOR',
    'EXECUTIVE'
);

CREATE TYPE communication_channel AS ENUM (
    'EMAIL',
    'MEETING',
    'CHAT',
    'REPORT',
    'PHONE',
    'PROJECT_PORTAL'
);

CREATE TYPE communication_purpose AS ENUM (
    'INFORMATION',
    'STATUS_UPDATE',
    'DECISION',
    'REQUEST',
    'ESCALATION',
    'ANNOUNCEMENT'
);

CREATE TYPE confidentiality_level AS ENUM (
    'PUBLIC',
    'INTERNAL',
    'CONFIDENTIAL',
    'RESTRICTED'
);

CREATE TYPE message_state AS ENUM (
    'DRAFT',
    'SENT',
    'ACKNOWLEDGED',
    'ESCALATED',
    'ARCHIVED'
);

CREATE TYPE action_state AS ENUM (
    'OPEN',
    'IN_PROGRESS',
    'BLOCKED',
    'COMPLETED',
    'CANCELLED'
);

CREATE TYPE decision_state AS ENUM (
    'PROPOSED',
    'APPROVED',
    'REJECTED',
    'DEFERRED'
);

-- ============================================================================
-- 2. PROJECTS
-- ============================================================================

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_code VARCHAR(30) NOT NULL UNIQUE,

    project_name VARCHAR(200) NOT NULL,

    description TEXT,

    start_date DATE NOT NULL,

    target_end_date DATE,

    project_status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT project_name_not_empty
        CHECK (length(trim(project_name)) > 0),

    CONSTRAINT project_dates_valid
        CHECK (
            target_end_date IS NULL
            OR target_end_date >= start_date
        ),

    CONSTRAINT project_status_valid
        CHECK (
            project_status IN (
                'PLANNING',
                'ACTIVE',
                'ON_HOLD',
                'COMPLETED',
                'CANCELLED'
            )
        )
);

-- ============================================================================
-- 3. STAKEHOLDERS
-- ============================================================================

CREATE TABLE stakeholders (
    stakeholder_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    full_name VARCHAR(150) NOT NULL,

    email VARCHAR(254) NOT NULL,

    role stakeholder_role NOT NULL,

    influence SMALLINT NOT NULL,

    interest SMALLINT NOT NULL,

    confidentiality_clearance confidentiality_level
        NOT NULL DEFAULT 'INTERNAL',

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT stakeholder_name_not_empty
        CHECK (length(trim(full_name)) > 0),

    CONSTRAINT stakeholder_email_valid
        CHECK (
            email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
        ),

    CONSTRAINT stakeholder_influence_valid
        CHECK (influence BETWEEN 1 AND 5),

    CONSTRAINT stakeholder_interest_valid
        CHECK (interest BETWEEN 1 AND 5),

    CONSTRAINT unique_project_stakeholder_email
        UNIQUE (project_id, email),

    CONSTRAINT unique_project_stakeholder
        UNIQUE (project_id, stakeholder_id)
);

CREATE INDEX idx_stakeholders_project_role
    ON stakeholders(project_id, role);

CREATE INDEX idx_stakeholders_engagement
    ON stakeholders(project_id, influence DESC, interest DESC);

-- ============================================================================
-- 4. STAKEHOLDER ENGAGEMENT CLASSIFICATION
-- ============================================================================

CREATE VIEW stakeholder_engagement_view AS
SELECT
    stakeholder_id,
    project_id,
    full_name,
    role,
    influence,
    interest,
    influence * interest AS engagement_score,

    CASE
        WHEN influence * interest >= 16
            THEN 'MANAGE_CLOSely'
        WHEN influence >= 4
            THEN 'KEEP_SATISFIED'
        WHEN interest >= 4
            THEN 'KEEP_INFORMED'
        ELSE 'MONITOR'
    END AS engagement_strategy,

    active

FROM stakeholders;

-- ============================================================================
-- 5. COMMUNICATION PLANS
-- ============================================================================

CREATE TABLE communication_plans (
    plan_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL,

    stakeholder_id BIGINT NOT NULL,

    owner_id BIGINT NOT NULL,

    channel communication_channel NOT NULL,

    purpose communication_purpose NOT NULL,

    frequency VARCHAR(20) NOT NULL,

    next_communication_at TIMESTAMPTZ NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT plan_project_stakeholder_fk
        FOREIGN KEY (project_id, stakeholder_id)
        REFERENCES stakeholders(project_id, stakeholder_id),

    CONSTRAINT plan_project_owner_fk
        FOREIGN KEY (project_id, owner_id)
        REFERENCES stakeholders(project_id, stakeholder_id),

    CONSTRAINT communication_frequency_valid
        CHECK (
            frequency IN (
                'DAILY',
                'WEEKLY',
                'BIWEEKLY',
                'MONTHLY',
                'MILESTONE',
                'ON_DEMAND'
            )
        )
);

CREATE INDEX idx_communication_plans_schedule
    ON communication_plans(next_communication_at)
    WHERE active = TRUE;

CREATE INDEX idx_communication_plans_stakeholder
    ON communication_plans(project_id, stakeholder_id);

-- ============================================================================
-- 6. COMMUNICATION MESSAGES
-- ============================================================================

CREATE TABLE messages (
    message_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    sender_id BIGINT NOT NULL,

    subject VARCHAR(250) NOT NULL,

    message_body TEXT NOT NULL,

    channel communication_channel NOT NULL,

    purpose communication_purpose NOT NULL,

    confidentiality confidentiality_level
        NOT NULL DEFAULT 'INTERNAL',

    state message_state NOT NULL DEFAULT 'DRAFT',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    sent_at TIMESTAMPTZ,

    CONSTRAINT message_subject_not_empty
        CHECK (length(trim(subject)) > 0),

    CONSTRAINT message_body_not_empty
        CHECK (length(trim(message_body)) > 0),

    CONSTRAINT message_sent_time_valid
        CHECK (
            (state = 'DRAFT' AND sent_at IS NULL)
            OR
            (state <> 'DRAFT' AND sent_at IS NOT NULL)
        ),

    CONSTRAINT message_project_sender_fk
        FOREIGN KEY (project_id, sender_id)
        REFERENCES stakeholders(project_id, stakeholder_id)
);

CREATE INDEX idx_messages_project_created
    ON messages(project_id, created_at DESC);

CREATE INDEX idx_messages_project_state
    ON messages(project_id, state);

CREATE INDEX idx_messages_sent_time
    ON messages(sent_at)
    WHERE sent_at IS NOT NULL;

-- ============================================================================
-- 7. MESSAGE RECIPIENTS
-- ============================================================================

CREATE TABLE message_recipients (
    message_id BIGINT NOT NULL
        REFERENCES messages(message_id),

    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    delivery_attempts INTEGER NOT NULL DEFAULT 0,

    delivered_at TIMESTAMPTZ,

    acknowledged_at TIMESTAMPTZ,

    delivery_error TEXT,

    PRIMARY KEY (message_id, stakeholder_id),

    CONSTRAINT delivery_attempts_nonnegative
        CHECK (delivery_attempts >= 0),

    CONSTRAINT acknowledgement_requires_delivery
        CHECK (
            acknowledged_at IS NULL
            OR delivered_at IS NOT NULL
        )
);

CREATE INDEX idx_message_recipients_pending
    ON message_recipients(message_id)
    WHERE acknowledged_at IS NULL;

CREATE INDEX idx_message_recipients_stakeholder
    ON message_recipients(stakeholder_id);

-- ============================================================================
-- 8. MEETINGS
-- ============================================================================

CREATE TABLE meetings (
    meeting_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    organizer_id BIGINT NOT NULL,

    title VARCHAR(250) NOT NULL,

    scheduled_at TIMESTAMPTZ NOT NULL,

    agenda TEXT NOT NULL,

    minutes TEXT,

    completed BOOLEAN NOT NULL DEFAULT FALSE,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT meeting_title_not_empty
        CHECK (length(trim(title)) > 0),

    CONSTRAINT meeting_completion_consistent
        CHECK (
            (
                completed = FALSE
                AND completed_at IS NULL
                AND minutes IS NULL
            )
            OR
            (
                completed = TRUE
                AND completed_at IS NOT NULL
                AND minutes IS NOT NULL
                AND length(trim(minutes)) > 0
            )
        ),

    CONSTRAINT meeting_project_organizer_fk
        FOREIGN KEY (project_id, organizer_id)
        REFERENCES stakeholders(project_id, stakeholder_id)
);

CREATE INDEX idx_meetings_project_schedule
    ON meetings(project_id, scheduled_at);

-- ============================================================================
-- 9. MEETING PARTICIPANTS
-- ============================================================================

CREATE TABLE meeting_participants (
    meeting_id BIGINT NOT NULL
        REFERENCES meetings(meeting_id),

    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    attendance_status VARCHAR(20) NOT NULL DEFAULT 'INVITED',

    PRIMARY KEY (meeting_id, stakeholder_id),

    CONSTRAINT attendance_status_valid
        CHECK (
            attendance_status IN (
                'INVITED',
                'ACCEPTED',
                'DECLINED',
                'ATTENDED',
                'ABSENT'
            )
        )
);

-- ============================================================================
-- 10. PROJECT DECISIONS
-- ============================================================================

CREATE TABLE project_decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    meeting_id BIGINT
        REFERENCES meetings(meeting_id),

    owner_id BIGINT NOT NULL,

    description TEXT NOT NULL,

    decision_status decision_state NOT NULL DEFAULT 'PROPOSED',

    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT decision_description_not_empty
        CHECK (length(trim(description)) > 0),

    CONSTRAINT decision_project_owner_fk
        FOREIGN KEY (project_id, owner_id)
        REFERENCES stakeholders(project_id, stakeholder_id)
);

CREATE INDEX idx_decisions_project_status
    ON project_decisions(project_id, decision_status);

-- ============================================================================
-- 11. ACTION ITEMS
-- ============================================================================

CREATE TABLE action_items (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    meeting_id BIGINT
        REFERENCES meetings(meeting_id),

    description TEXT NOT NULL,

    assigned_to BIGINT NOT NULL,

    created_by BIGINT NOT NULL,

    due_date TIMESTAMPTZ NOT NULL,

    state action_state NOT NULL DEFAULT 'OPEN',

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT action_description_not_empty
        CHECK (length(trim(description)) > 0),

    CONSTRAINT action_completion_consistent
        CHECK (
            (state = 'COMPLETED' AND completed_at IS NOT NULL)
            OR
            (state <> 'COMPLETED' AND completed_at IS NULL)
        ),

    CONSTRAINT action_project_assignee_fk
        FOREIGN KEY (project_id, assigned_to)
        REFERENCES stakeholders(project_id, stakeholder_id),

    CONSTRAINT action_project_creator_fk
        FOREIGN KEY (project_id, created_by)
        REFERENCES stakeholders(project_id, stakeholder_id)
);

CREATE INDEX idx_action_items_due
    ON action_items(due_date)
    WHERE state NOT IN ('COMPLETED', 'CANCELLED');

CREATE INDEX idx_action_items_assignee_state
    ON action_items(assigned_to, state);

-- ============================================================================
-- 12. COMMUNICATION POLICY
-- ============================================================================

CREATE TABLE communication_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    role stakeholder_role NOT NULL,

    purpose communication_purpose NOT NULL,

    can_send BOOLEAN NOT NULL DEFAULT FALSE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE(project_id, role, purpose)
);

-- ============================================================================
-- 13. AUDIT HISTORY
-- ============================================================================

CREATE TABLE communication_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    actor_id BIGINT,

    entity_type VARCHAR(50) NOT NULL,

    entity_id BIGINT NOT NULL,

    event_type VARCHAR(80) NOT NULL,

    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT audit_event_type_not_empty
        CHECK (length(trim(event_type)) > 0),

    CONSTRAINT audit_details_object
        CHECK (jsonb_typeof(event_details) = 'object'),

    CONSTRAINT audit_project_actor_fk
        FOREIGN KEY (project_id, actor_id)
        REFERENCES stakeholders(project_id, stakeholder_id)
);

CREATE INDEX idx_audit_project_created
    ON communication_audit(project_id, created_at DESC);

CREATE INDEX idx_audit_event_type
    ON communication_audit(event_type);

CREATE INDEX idx_audit_details
    ON communication_audit USING GIN(event_details);

-- ============================================================================
-- 14. CONFIDENTIALITY VALIDATION
-- ============================================================================

CREATE FUNCTION confidentiality_rank(
    p_level confidentiality_level
)
RETURNS INTEGER
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT CASE p_level
        WHEN 'PUBLIC' THEN 1
        WHEN 'INTERNAL' THEN 2
        WHEN 'CONFIDENTIAL' THEN 3
        WHEN 'RESTRICTED' THEN 4
    END;
$$;

-- ============================================================================
-- 15. COMMUNICATION POLICY EVALUATION
-- ============================================================================

CREATE FUNCTION can_send_communication(
    p_project_id BIGINT,
    p_sender_id BIGINT,
    p_purpose communication_purpose
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM stakeholders s
        JOIN communication_policies cp
          ON cp.project_id = s.project_id
         AND cp.role = s.role
        WHERE s.project_id = p_project_id
          AND s.stakeholder_id = p_sender_id
          AND s.active = TRUE
          AND cp.purpose = p_purpose
          AND cp.active = TRUE
          AND cp.can_send = TRUE
    );
$$;

-- ============================================================================
-- 16. MESSAGE RECIPIENT AUTHORIZATION TRIGGER
-- ============================================================================

CREATE FUNCTION validate_message_recipient()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_project_id BIGINT;
    v_confidentiality confidentiality_level;
    v_recipient_project BIGINT;
    v_clearance confidentiality_level;
    v_active BOOLEAN;
BEGIN
    SELECT
        project_id,
        confidentiality
    INTO
        v_project_id,
        v_confidentiality
    FROM messages
    WHERE message_id = NEW.message_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Message % does not exist', NEW.message_id;
    END IF;

    SELECT
        project_id,
        confidentiality_clearance,
        active
    INTO
        v_recipient_project,
        v_clearance,
        v_active
    FROM stakeholders
    WHERE stakeholder_id = NEW.stakeholder_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Recipient does not exist';
    END IF;

    IF v_project_id <> v_recipient_project THEN
        RAISE EXCEPTION
            'Cross-project message recipients are not permitted';
    END IF;

    IF NOT v_active THEN
        RAISE EXCEPTION 'Inactive recipients cannot receive messages';
    END IF;

    IF confidentiality_rank(v_clearance)
       < confidentiality_rank(v_confidentiality) THEN
        RAISE EXCEPTION
            'Recipient clearance is insufficient for this message';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_message_recipient
BEFORE INSERT OR UPDATE OF message_id, stakeholder_id
ON message_recipients
FOR EACH ROW
EXECUTE FUNCTION validate_message_recipient();

-- ============================================================================
-- 17. MESSAGE STATE TRANSITION VALIDATION
-- ============================================================================

CREATE FUNCTION validate_message_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state = NEW.state THEN
        RETURN NEW;
    END IF;

    IF OLD.state = 'DRAFT' AND NEW.state = 'SENT' THEN
        IF NEW.sent_at IS NULL THEN
            RAISE EXCEPTION 'Sent messages require sent_at';
        END IF;

        RETURN NEW;
    END IF;

    IF OLD.state = 'SENT'
       AND NEW.state IN ('ACKNOWLEDGED', 'ESCALATED', 'ARCHIVED') THEN
        RETURN NEW;
    END IF;

    IF OLD.state = 'ESCALATED'
       AND NEW.state IN ('ACKNOWLEDGED', 'ARCHIVED') THEN
        RETURN NEW;
    END IF;

    IF OLD.state = 'ACKNOWLEDGED'
       AND NEW.state = 'ARCHIVED' THEN
        RETURN NEW;
    END IF;

    RAISE EXCEPTION
        'Invalid message transition: % -> %',
        OLD.state,
        NEW.state;
END;
$$;

CREATE TRIGGER trg_message_state_transition
BEFORE UPDATE OF state
ON messages
FOR EACH ROW
EXECUTE FUNCTION validate_message_transition();

-- ============================================================================
-- 18. ACTION-ITEM STATE TRANSITION VALIDATION
-- ============================================================================

CREATE FUNCTION validate_action_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state = NEW.state THEN
        RETURN NEW;
    END IF;

    IF OLD.state = 'OPEN'
       AND NEW.state IN ('IN_PROGRESS', 'BLOCKED', 'CANCELLED') THEN
        RETURN NEW;
    END IF;

    IF OLD.state = 'IN_PROGRESS'
       AND NEW.state IN ('COMPLETED', 'BLOCKED', 'CANCELLED') THEN
        RETURN NEW;
    END IF;

    IF OLD.state = 'BLOCKED'
       AND NEW.state IN ('IN_PROGRESS', 'CANCELLED') THEN
        RETURN NEW;
    END IF;

    RAISE EXCEPTION
        'Invalid action transition: % -> %',
        OLD.state,
        NEW.state;
END;
$$;

CREATE TRIGGER trg_action_state_transition
BEFORE UPDATE OF state
ON action_items
FOR EACH ROW
EXECUTE FUNCTION validate_action_transition();

-- ============================================================================
-- 19. AUTOMATIC COMPLETION TIMESTAMP
-- ============================================================================

CREATE FUNCTION set_action_completion_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state = 'COMPLETED' THEN
        NEW.completed_at = COALESCE(
            NEW.completed_at,
            CURRENT_TIMESTAMP
        );
    ELSE
        NEW.completed_at = NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_action_completion_timestamp
BEFORE INSERT OR UPDATE OF state
ON action_items
FOR EACH ROW
EXECUTE FUNCTION set_action_completion_timestamp();

-- ============================================================================
-- 20. AUDIT TRIGGER FOR MESSAGE CHANGES
-- ============================================================================

CREATE FUNCTION audit_message_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_event_type TEXT;
    v_actor BIGINT;
    v_project BIGINT;
    v_entity BIGINT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_event_type := 'MESSAGE_CREATED';
        v_actor := NEW.sender_id;
        v_project := NEW.project_id;
        v_entity := NEW.message_id;

    ELSIF TG_OP = 'UPDATE' THEN
        v_event_type := 'MESSAGE_UPDATED';
        v_actor := NEW.sender_id;
        v_project := NEW.project_id;
        v_entity := NEW.message_id;
    END IF;

    INSERT INTO communication_audit (
        project_id,
        actor_id,
        entity_type,
        entity_id,
        event_type,
        event_details
    )
    VALUES (
        v_project,
        v_actor,
        'MESSAGE',
        v_entity,
        v_event_type,
        jsonb_build_object(
            'state', NEW.state,
            'channel', NEW.channel,
            'purpose', NEW.purpose
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_message
AFTER INSERT OR UPDATE
ON messages
FOR EACH ROW
EXECUTE FUNCTION audit_message_change();

-- ============================================================================
-- 21. COMMUNICATION DISPATCH PROCEDURE
-- ============================================================================

CREATE PROCEDURE dispatch_message(
    p_message_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_project_id BIGINT;
    v_sender_id BIGINT;
    v_purpose communication_purpose;
    v_state message_state;
    v_recipient_count INTEGER;
BEGIN
    SELECT
        project_id,
        sender_id,
        purpose,
        state
    INTO
        v_project_id,
        v_sender_id,
        v_purpose,
        v_state
    FROM messages
    WHERE message_id = p_message_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Message % not found', p_message_id;
    END IF;

    IF v_state <> 'DRAFT' THEN
        RAISE EXCEPTION 'Only draft messages can be dispatched';
    END IF;

    IF NOT can_send_communication(
        v_project_id,
        v_sender_id,
        v_purpose
    ) THEN
        RAISE EXCEPTION 'Sender is not authorized for this purpose';
    END IF;

    SELECT COUNT(*)
    INTO v_recipient_count
    FROM message_recipients
    WHERE message_id = p_message_id;

    IF v_recipient_count = 0 THEN
        RAISE EXCEPTION 'Message requires at least one recipient';
    END IF;

    -- The recipient trigger has already validated clearance.
    -- Dispatch state and timestamp are changed atomically.
    UPDATE messages
    SET
        state = 'SENT',
        sent_at = CURRENT_TIMESTAMP
    WHERE message_id = p_message_id;

    UPDATE message_recipients
    SET delivery_attempts = delivery_attempts + 1,
        delivered_at = CURRENT_TIMESTAMP,
        delivery_error = NULL
    WHERE message_id = p_message_id;

END;
$$;

-- ============================================================================
-- 22. ACKNOWLEDGEMENT PROCEDURE
-- ============================================================================

CREATE PROCEDURE acknowledge_message(
    p_message_id BIGINT,
    p_stakeholder_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_state message_state;
    v_remaining INTEGER;
BEGIN
    SELECT state
    INTO v_state
    FROM messages
    WHERE message_id = p_message_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Message not found';
    END IF;

    IF v_state NOT IN ('SENT', 'ACKNOWLEDGED', 'ESCALATED') THEN
        RAISE EXCEPTION 'Message cannot be acknowledged in this state';
    END IF;

    UPDATE message_recipients
    SET acknowledged_at = COALESCE(
        acknowledged_at,
        CURRENT_TIMESTAMP
    )
    WHERE message_id = p_message_id
      AND stakeholder_id = p_stakeholder_id
      AND delivered_at IS NOT NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Recipient is invalid or message was not delivered';
    END IF;

    SELECT COUNT(*)
    INTO v_remaining
    FROM message_recipients
    WHERE message_id = p_message_id
      AND acknowledged_at IS NULL;

    IF v_remaining = 0 THEN
        UPDATE messages
        SET state = 'ACKNOWLEDGED'
        WHERE message_id = p_message_id
          AND state IN ('SENT', 'ESCALATED');
    END IF;
END;
$$;

-- ============================================================================
-- 23. MESSAGE ESCALATION FUNCTION
-- ============================================================================

CREATE FUNCTION escalate_unacknowledged_messages(
    p_project_id BIGINT,
    p_wait_interval INTERVAL
)
RETURNS TABLE (
    escalated_message_id BIGINT,
    pending_recipient_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_wait_interval < INTERVAL '0 seconds' THEN
        RAISE EXCEPTION 'Wait interval cannot be negative';
    END IF;

    RETURN QUERY
    WITH eligible_messages AS (
        SELECT m.message_id
        FROM messages m
        WHERE m.project_id = p_project_id
          AND m.state = 'SENT'
          AND m.sent_at < CURRENT_TIMESTAMP - p_wait_interval
        FOR UPDATE
    ),
    escalated AS (
        UPDATE messages m
        SET state = 'ESCALATED'
        FROM eligible_messages e
        WHERE m.message_id = e.message_id
        RETURNING m.message_id
    )
    SELECT
        e.message_id,
        COUNT(r.stakeholder_id)
    FROM escalated e
    JOIN message_recipients r
      ON r.message_id = e.message_id
    WHERE r.acknowledged_at IS NULL
    GROUP BY e.message_id;
END;
$$;

-- ============================================================================
-- 24. MEETING COMPLETION PROCEDURE
-- ============================================================================

CREATE PROCEDURE complete_meeting(
    p_meeting_id BIGINT,
    p_organizer_id BIGINT,
    p_minutes TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_organizer BIGINT;
    v_completed BOOLEAN;
BEGIN
    SELECT organizer_id, completed
    INTO v_organizer, v_completed
    FROM meetings
    WHERE meeting_id = p_meeting_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Meeting not found';
    END IF;

    IF v_organizer <> p_organizer_id THEN
        RAISE EXCEPTION 'Only the meeting organizer can finalize minutes';
    END IF;

    IF v_completed THEN
        RAISE EXCEPTION 'Meeting already completed';
    END IF;

    IF p_minutes IS NULL OR length(trim(p_minutes)) = 0 THEN
        RAISE EXCEPTION 'Meeting minutes are required';
    END IF;

    UPDATE meetings
    SET
        minutes = p_minutes,
        completed = TRUE,
        completed_at = CURRENT_TIMESTAMP
    WHERE meeting_id = p_meeting_id;
END;
$$;

-- ============================================================================
-- 25. REPORTING VIEWS
-- ============================================================================

CREATE VIEW message_acknowledgement_view AS
SELECT
    m.project_id,
    m.message_id,
    m.subject,
    m.channel,
    m.purpose,
    m.state,
    m.created_at,
    m.sent_at,

    COUNT(r.stakeholder_id) AS recipient_count,

    COUNT(r.acknowledged_at) AS acknowledged_count,

    COUNT(r.stakeholder_id)
        - COUNT(r.acknowledged_at) AS pending_count,

    CASE
        WHEN COUNT(r.stakeholder_id) = 0 THEN 0
        ELSE ROUND(
            100.0 * COUNT(r.acknowledged_at)
            / COUNT(r.stakeholder_id),
            2
        )
    END AS acknowledgement_percentage

FROM messages m
LEFT JOIN message_recipients r
    ON r.message_id = m.message_id

GROUP BY
    m.project_id,
    m.message_id,
    m.subject,
    m.channel,
    m.purpose,
    m.state,
    m.created_at,
    m.sent_at;

CREATE VIEW overdue_action_items_view AS
SELECT
    a.action_id,
    a.project_id,
    a.description,
    a.assigned_to,
    s.full_name AS assignee_name,
    a.due_date,
    a.state,
    CURRENT_TIMESTAMP - a.due_date AS overdue_duration

FROM action_items a
JOIN stakeholders s
    ON s.stakeholder_id = a.assigned_to

WHERE a.due_date < CURRENT_TIMESTAMP
  AND a.state NOT IN ('COMPLETED', 'CANCELLED');

CREATE VIEW project_communication_dashboard AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,

    COUNT(DISTINCT s.stakeholder_id) AS stakeholder_count,

    COUNT(DISTINCT m.message_id) AS message_count,

    COUNT(DISTINCT CASE
        WHEN m.state = 'SENT' THEN m.message_id
    END) AS sent_message_count,

    COUNT(DISTINCT mt.meeting_id) AS meeting_count,

    COUNT(DISTINCT a.action_id) AS action_count,

    COUNT(DISTINCT CASE
        WHEN a.due_date < CURRENT_TIMESTAMP
         AND a.state NOT IN ('COMPLETED', 'CANCELLED')
        THEN a.action_id
    END) AS overdue_action_count

FROM projects p

LEFT JOIN stakeholders s
    ON s.project_id = p.project_id

LEFT JOIN messages m
    ON m.project_id = p.project_id

LEFT JOIN meetings mt
    ON mt.project_id = p.project_id

LEFT JOIN action_items a
    ON a.project_id = p.project_id

GROUP BY
    p.project_id,
    p.project_code,
    p.project_name;

-- ============================================================================
-- 26. SAMPLE PROJECT
-- ============================================================================

INSERT INTO projects (
    project_code,
    project_name,
    description,
    start_date,
    target_end_date,
    project_status
)
VALUES (
    'PRJ-COMM-001',
    'Enterprise Project Management System',
    'Implementation of an enterprise project management platform.',
    CURRENT_DATE - 30,
    CURRENT_DATE + 180,
    'ACTIVE'
);

-- ============================================================================
-- 27. SAMPLE STAKEHOLDERS
-- ============================================================================

INSERT INTO stakeholders (
    project_id,
    full_name,
    email,
    role,
    influence,
    interest,
    confidentiality_clearance
)
SELECT
    p.project_id,
    x.full_name,
    x.email,
    x.role::stakeholder_role,
    x.influence,
    x.interest,
    x.clearance::confidentiality_level

FROM projects p

CROSS JOIN (
    VALUES
    (
        'Project Manager',
        'manager@example.com',
        'PROJECT_MANAGER',
        5,
        5,
        'RESTRICTED'
    ),
    (
        'Project Sponsor',
        'sponsor@example.com',
        'SPONSOR',
        5,
        4,
        'CONFIDENTIAL'
    ),
    (
        'Development Lead',
        'developer@example.com',
        'TEAM_MEMBER',
        3,
        5,
        'INTERNAL'
    ),
    (
        'Client Representative',
        'client@example.com',
        'CLIENT',
        4,
        5,
        'CONFIDENTIAL'
    ),
    (
        'External Vendor',
        'vendor@example.com',
        'VENDOR',
        2,
        3,
        'INTERNAL'
    ),
    (
        'Executive Director',
        'executive@example.com',
        'EXECUTIVE',
        5,
        3,
        'CONFIDENTIAL'
    )
) AS x(full_name, email, role, influence, interest, clearance)

WHERE p.project_code = 'PRJ-COMM-001';

-- ============================================================================
-- 28. SAMPLE COMMUNICATION POLICIES
-- ============================================================================

INSERT INTO communication_policies (
    project_id,
    role,
    purpose,
    can_send
)
SELECT
    p.project_id,
    x.role::stakeholder_role,
    x.purpose::communication_purpose,
    TRUE

FROM projects p

CROSS JOIN (
    VALUES
    ('PROJECT_MANAGER', 'INFORMATION'),
    ('PROJECT_MANAGER', 'STATUS_UPDATE'),
    ('PROJECT_MANAGER', 'DECISION'),
    ('PROJECT_MANAGER', 'REQUEST'),
    ('PROJECT_MANAGER', 'ESCALATION'),
    ('PROJECT_MANAGER', 'ANNOUNCEMENT'),

    ('SPONSOR', 'INFORMATION'),
    ('SPONSOR', 'STATUS_UPDATE'),
    ('SPONSOR', 'DECISION'),
    ('SPONSOR', 'ESCALATION'),

    ('TEAM_MEMBER', 'INFORMATION'),
    ('TEAM_MEMBER', 'STATUS_UPDATE'),
    ('TEAM_MEMBER', 'REQUEST'),

    ('CLIENT', 'INFORMATION'),
    ('CLIENT', 'STATUS_UPDATE'),
    ('CLIENT', 'DECISION'),
    ('CLIENT', 'REQUEST'),

    ('VENDOR', 'INFORMATION'),
    ('VENDOR', 'STATUS_UPDATE'),
    ('VENDOR', 'REQUEST'),

    ('EXECUTIVE', 'INFORMATION'),
    ('EXECUTIVE', 'STATUS_UPDATE'),
    ('EXECUTIVE', 'ESCALATION')
) AS x(role, purpose)

WHERE p.project_code = 'PRJ-COMM-001';

-- ============================================================================
-- 29. SAMPLE COMMUNICATION PLANS
-- ============================================================================

INSERT INTO communication_plans (
    project_id,
    stakeholder_id,
    owner_id,
    channel,
    purpose,
    frequency,
    next_communication_at
)
SELECT
    p.project_id,
    sponsor.stakeholder_id,
    manager.stakeholder_id,
    'EMAIL',
    'STATUS_UPDATE',
    'WEEKLY',
    CURRENT_TIMESTAMP + INTERVAL '7 days'

FROM projects p

JOIN stakeholders manager
    ON manager.project_id = p.project_id
   AND manager.role = 'PROJECT_MANAGER'

JOIN stakeholders sponsor
    ON sponsor.project_id = p.project_id
   AND sponsor.role = 'SPONSOR'

WHERE p.project_code = 'PRJ-COMM-001';

-- ============================================================================
-- 30. SAMPLE MESSAGE AND RECIPIENTS
-- ============================================================================

INSERT INTO messages (
    project_id,
    sender_id,
    subject,
    message_body,
    channel,
    purpose,
    confidentiality
)
SELECT
    p.project_id,
    manager.stakeholder_id,
    'Weekly Project Progress',
    'Development is 65 percent complete. Testing preparation is underway.',
    'EMAIL',
    'STATUS_UPDATE',
    'INTERNAL'

FROM projects p

JOIN stakeholders manager
    ON manager.project_id = p.project_id
   AND manager.role = 'PROJECT_MANAGER'

WHERE p.project_code = 'PRJ-COMM-001';

INSERT INTO message_recipients (
    message_id,
    stakeholder_id
)
SELECT
    m.message_id,
    s.stakeholder_id

FROM messages m

JOIN stakeholders s
    ON s.project_id = m.project_id

WHERE m.subject = 'Weekly Project Progress'
  AND s.role IN ('SPONSOR', 'TEAM_MEMBER');

-- ============================================================================
-- 31. TRANSACTIONAL MESSAGE DISPATCH
-- ============================================================================

DO $$
DECLARE
    v_message_id BIGINT;
BEGIN
    SELECT message_id
    INTO v_message_id
    FROM messages
    WHERE subject = 'Weekly Project Progress'
    ORDER BY message_id DESC
    LIMIT 1;

    CALL dispatch_message(v_message_id);
END;
$$;

-- ============================================================================
-- 32. SAMPLE ACKNOWLEDGEMENT
-- ============================================================================

DO $$
DECLARE
    v_message_id BIGINT;
    v_sponsor_id BIGINT;
BEGIN
    SELECT message_id
    INTO v_message_id
    FROM messages
    WHERE subject = 'Weekly Project Progress'
    ORDER BY message_id DESC
    LIMIT 1;

    SELECT stakeholder_id
    INTO v_sponsor_id
    FROM stakeholders
    WHERE email = 'sponsor@example.com';

    CALL acknowledge_message(
        v_message_id,
        v_sponsor_id
    );
END;
$$;

-- ============================================================================
-- 33. SAMPLE MEETING
-- ============================================================================

INSERT INTO meetings (
    project_id,
    organizer_id,
    title,
    scheduled_at,
    agenda
)
SELECT
    p.project_id,
    manager.stakeholder_id,
    'Weekly Project Review',
    CURRENT_TIMESTAMP + INTERVAL '1 day',
    '1. Project progress; 2. Risks; 3. Resource allocation; 4. Testing'

FROM projects p

JOIN stakeholders manager
    ON manager.project_id = p.project_id
   AND manager.role = 'PROJECT_MANAGER'

WHERE p.project_code = 'PRJ-COMM-001';

INSERT INTO meeting_participants (
    meeting_id,
    stakeholder_id,
    attendance_status
)
SELECT
    m.meeting_id,
    s.stakeholder_id,
    'INVITED'

FROM meetings m

JOIN stakeholders s
    ON s.project_id = m.project_id

WHERE m.title = 'Weekly Project Review'
  AND s.role IN ('SPONSOR', 'TEAM_MEMBER', 'CLIENT');

-- ============================================================================
-- 34. COMPLETE MEETING
-- ============================================================================

DO $$
DECLARE
    v_meeting_id BIGINT;
    v_organizer_id BIGINT;
BEGIN
    SELECT
        meeting_id,
        organizer_id
    INTO
        v_meeting_id,
        v_organizer_id
    FROM meetings
    WHERE title = 'Weekly Project Review'
    ORDER BY meeting_id DESC
    LIMIT 1;

    CALL complete_meeting(
        v_meeting_id,
        v_organizer_id,
        'Testing preparation approved. Delivery milestone remains unchanged.'
    );
END;
$$;

-- ============================================================================
-- 35. SAMPLE DECISION
-- ============================================================================

INSERT INTO project_decisions (
    project_id,
    meeting_id,
    owner_id,
    description,
    decision_status
)
SELECT
    m.project_id,
    m.meeting_id,
    sponsor.stakeholder_id,
    'Approve the testing preparation schedule.',
    'APPROVED'

FROM meetings m

JOIN stakeholders sponsor
    ON sponsor.project_id = m.project_id
   AND sponsor.role = 'SPONSOR'

WHERE m.title = 'Weekly Project Review'
  AND m.completed = TRUE;

-- ============================================================================
-- 36. SAMPLE ACTION ITEMS
-- ============================================================================

INSERT INTO action_items (
    project_id,
    meeting_id,
    description,
    assigned_to,
    created_by,
    due_date,
    state
)
SELECT
    m.project_id,
    m.meeting_id,
    'Prepare the software testing plan.',
    developer.stakeholder_id,
    manager.stakeholder_id,
    CURRENT_TIMESTAMP + INTERVAL '5 days',
    'IN_PROGRESS'

FROM meetings m

JOIN stakeholders developer
    ON developer.project_id = m.project_id
   AND developer.role = 'TEAM_MEMBER'

JOIN stakeholders manager
    ON manager.project_id = m.project_id
   AND manager.role = 'PROJECT_MANAGER'

WHERE m.title = 'Weekly Project Review'
  AND m.completed = TRUE;

-- ============================================================================
-- 37. SAMPLE OVERDUE ACTION
-- ============================================================================

INSERT INTO action_items (
    project_id,
    description,
    assigned_to,
    created_by,
    due_date,
    state
)
SELECT
    p.project_id,
    'Submit the initial risk assessment.',
    developer.stakeholder_id,
    manager.stakeholder_id,
    CURRENT_TIMESTAMP - INTERVAL '2 days',
    'OPEN'

FROM projects p

JOIN stakeholders developer
    ON developer.project_id = p.project_id
   AND developer.role = 'TEAM_MEMBER'

JOIN stakeholders manager
    ON manager.project_id = p.project_id
   AND manager.role = 'PROJECT_MANAGER'

WHERE p.project_code = 'PRJ-COMM-001';

-- ============================================================================
-- 38. COMMUNICATION RETRIEVAL
-- ============================================================================

SELECT
    m.message_id,
    m.subject,
    m.channel,
    m.purpose,
    m.state,
    sender.full_name AS sender_name,
    m.created_at

FROM messages m

JOIN stakeholders sender
    ON sender.stakeholder_id = m.sender_id

WHERE m.project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'PRJ-COMM-001'
)

ORDER BY m.created_at DESC;

-- ============================================================================
-- 39. COMMUNICATION RECIPIENT REPORT
-- ============================================================================

SELECT
    m.subject,
    s.full_name AS recipient,
    r.delivered_at,
    r.acknowledged_at,

    CASE
        WHEN r.acknowledged_at IS NOT NULL THEN 'ACKNOWLEDGED'
        WHEN r.delivered_at IS NOT NULL THEN 'AWAITING ACKNOWLEDGEMENT'
        ELSE 'NOT DELIVERED'
    END AS recipient_status

FROM message_recipients r

JOIN messages m
    ON m.message_id = r.message_id

JOIN stakeholders s
    ON s.stakeholder_id = r.stakeholder_id

ORDER BY m.message_id, s.full_name;

-- ============================================================================
-- 40. COMMUNICATION VALIDATION
-- ============================================================================

SELECT
    message_id,
    subject,
    recipient_count,
    acknowledged_count,
    pending_count,
    acknowledgement_percentage

FROM message_acknowledgement_view

ORDER BY message_id;

-- ============================================================================
-- 41. STAKEHOLDER ENGAGEMENT REPORT
-- ============================================================================

SELECT
    full_name,
    role,
    influence,
    interest,
    engagement_score,
    engagement_strategy

FROM stakeholder_engagement_view

WHERE project_id = (
    SELECT project_id
    FROM projects
    WHERE project_code = 'PRJ-COMM-001'
)

ORDER BY engagement_score DESC;

-- ============================================================================
-- 42. AGGREGATION BY CHANNEL
-- ============================================================================

SELECT
    channel,
    COUNT(*) AS total_messages,

    COUNT(*) FILTER (
        WHERE state = 'SENT'
    ) AS sent_messages,

    COUNT(*) FILTER (
        WHERE state = 'ACKNOWLEDGED'
    ) AS acknowledged_messages,

    COUNT(*) FILTER (
        WHERE state = 'ESCALATED'
    ) AS escalated_messages

FROM messages

GROUP BY channel

ORDER BY total_messages DESC;

-- ============================================================================
-- 43. OVERDUE ACTION REPORT
-- ============================================================================

SELECT
    action_id,
    description,
    assignee_name,
    due_date,
    state,
    overdue_duration

FROM overdue_action_items_view

ORDER BY overdue_duration DESC;

-- ============================================================================
-- 44. CTE-BASED COMMUNICATION EFFECTIVENESS
-- ============================================================================

WITH message_statistics AS (
    SELECT
        project_id,
        COUNT(*) AS message_count
    FROM messages
    GROUP BY project_id
),

recipient_statistics AS (
    SELECT
        m.project_id,
        COUNT(*) AS total_recipients,
        COUNT(r.acknowledged_at) AS acknowledged_recipients

    FROM messages m

    JOIN message_recipients r
        ON r.message_id = m.message_id

    GROUP BY m.project_id
),

action_statistics AS (
    SELECT
        project_id,

        COUNT(*) FILTER (
            WHERE state = 'COMPLETED'
        ) AS completed_actions,

        COUNT(*) FILTER (
            WHERE state NOT IN ('COMPLETED', 'CANCELLED')
              AND due_date < CURRENT_TIMESTAMP
        ) AS overdue_actions

    FROM action_items

    GROUP BY project_id
)

SELECT
    p.project_name,
    COALESCE(ms.message_count, 0) AS message_count,
    COALESCE(rs.total_recipients, 0) AS total_recipients,
    COALESCE(rs.acknowledged_recipients, 0) AS acknowledged_recipients,

    CASE
        WHEN COALESCE(rs.total_recipients, 0) = 0 THEN 0
        ELSE ROUND(
            100.0 * rs.acknowledged_recipients
            / rs.total_recipients,
            2
        )
    END AS acknowledgement_rate,

    COALESCE(a.completed_actions, 0) AS completed_actions,
    COALESCE(a.overdue_actions, 0) AS overdue_actions

FROM projects p

LEFT JOIN message_statistics ms
    ON ms.project_id = p.project_id

LEFT JOIN recipient_statistics rs
    ON rs.project_id = p.project_id

LEFT JOIN action_statistics a
    ON a.project_id = p.project_id;

-- ============================================================================
-- 45. ELIGIBILITY DETERMINATION
-- ============================================================================

CREATE VIEW message_dispatch_eligibility AS
SELECT
    m.message_id,
    m.subject,
    m.state,

    can_send_communication(
        m.project_id,
        m.sender_id,
        m.purpose
    ) AS sender_authorized,

    COUNT(r.stakeholder_id) AS recipient_count,

    CASE
        WHEN m.state <> 'DRAFT' THEN FALSE
        WHEN NOT can_send_communication(
            m.project_id,
            m.sender_id,
            m.purpose
        ) THEN FALSE
        WHEN COUNT(r.stakeholder_id) = 0 THEN FALSE
        ELSE TRUE
    END AS eligible_for_dispatch

FROM messages m

LEFT JOIN message_recipients r
    ON r.message_id = m.message_id

GROUP BY
    m.message_id,
    m.subject,
    m.state,
    m.project_id,
    m.sender_id,
    m.purpose;

SELECT *
FROM message_dispatch_eligibility;

-- ============================================================================
-- 46. ESCALATION WORKFLOW
-- ============================================================================

SELECT *
FROM escalate_unacknowledged_messages(
    (
        SELECT project_id
        FROM projects
        WHERE project_code = 'PRJ-COMM-001'
    ),
    INTERVAL '24 hours'
);

-- ============================================================================
-- 47. PROJECT COMMUNICATION DASHBOARD
-- ============================================================================

SELECT *
FROM project_communication_dashboard
WHERE project_code = 'PRJ-COMM-001';

-- ============================================================================
-- 48. AUDIT REPORT
-- ============================================================================

SELECT
    audit_id,
    entity_type,
    entity_id,
    event_type,
    actor_id,
    event_details,
    created_at

FROM communication_audit

ORDER BY created_at DESC;

-- ============================================================================
-- 49. INVALID OPERATION TESTS
-- ============================================================================

-- These tests intentionally fail inside isolated subtransactions.
-- Their failures do not interrupt the remaining SQL script.

DO $$
DECLARE
    v_message_id BIGINT;
    v_client_id BIGINT;
BEGIN
    SELECT message_id
    INTO v_message_id
    FROM messages
    WHERE subject = 'Weekly Project Progress'
    ORDER BY message_id DESC
    LIMIT 1;

    SELECT stakeholder_id
    INTO v_client_id
    FROM stakeholders
    WHERE email = 'client@example.com';

    -- The client was not an intended recipient.
    BEGIN
        CALL acknowledge_message(
            v_message_id,
            v_client_id
        );

        RAISE EXCEPTION
            'Expected invalid acknowledgement to fail';

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Invalid acknowledgement rejected: %',
                SQLERRM;
    END;

    -- A restricted message must not be delivered to an
    -- insufficiently authorized recipient.
    BEGIN
        INSERT INTO messages (
            project_id,
            sender_id,
            subject,
            message_body,
            channel,
            purpose,
            confidentiality
        )
        SELECT
            p.project_id,
            manager.stakeholder_id,
            'Restricted Test',
            'Restricted communication validation.',
            'EMAIL',
            'STATUS_UPDATE',
            'RESTRICTED'

        FROM projects p

        JOIN stakeholders manager
            ON manager.project_id = p.project_id
           AND manager.role = 'PROJECT_MANAGER'

        WHERE p.project_code = 'PRJ-COMM-001';

        INSERT INTO message_recipients (
            message_id,
            stakeholder_id
        )
        SELECT
            m.message_id,
            s.stakeholder_id

        FROM messages m

        JOIN stakeholders s
            ON s.project_id = m.project_id

        WHERE m.subject = 'Restricted Test'
          AND s.role = 'TEAM_MEMBER';

        RAISE EXCEPTION
            'Expected confidentiality validation to fail';

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Confidentiality validation rejected: %',
                SQLERRM;
    END;
END;
$$;

-- ============================================================================
-- 50. TRANSACTION COMPLETION
-- ============================================================================

COMMIT;

-- ============================================================================
-- END OF PROJECT COMMUNICATION MANAGEMENT SCRIPT
-- ============================================================================
