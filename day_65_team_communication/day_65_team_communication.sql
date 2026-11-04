-- ================================================================
-- TEAM COMMUNICATION MANAGEMENT SYSTEM
-- PostgreSQL 15+
--
-- Models:
-- Organizations, teams, users, channels, memberships,
-- threaded messages, recipients, read receipts, acknowledgments,
-- action items, notifications, escalation policies and audit events.
--
-- Run this script in a database where the executing role can
-- create schemas, tables, functions and triggers.
-- ================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS team_communication;

SET search_path TO team_communication, public;

-- ------------------------------------------------
-- 1. ENUMERATED DOMAIN TYPES
-- ------------------------------------------------

CREATE TYPE user_role AS ENUM (
    'admin',
    'manager',
    'member',
    'observer'
);

CREATE TYPE channel_type AS ENUM (
    'general',
    'project',
    'announcement',
    'incident',
    'private'
);

CREATE TYPE message_priority AS ENUM (
    'low',
    'normal',
    'high',
    'urgent'
);

CREATE TYPE message_status AS ENUM (
    'sent',
    'acknowledged',
    'resolved',
    'archived'
);

CREATE TYPE task_status AS ENUM (
    'open',
    'in_progress',
    'blocked',
    'completed'
);

CREATE TYPE notification_status AS ENUM (
    'pending',
    'delivered',
    'failed',
    'read'
);

-- ------------------------------------------------
-- 2. ORGANIZATION AND TEAM STRUCTURE
-- ------------------------------------------------

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT organization_name_nonempty
        CHECK (LENGTH(TRIM(organization_name)) > 0)
);

CREATE TABLE teams (
    team_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    team_name VARCHAR(120) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT team_name_nonempty
        CHECK (LENGTH(TRIM(team_name)) > 0),

    CONSTRAINT unique_team_name
        UNIQUE (organization_id, team_name),

    CONSTRAINT unique_team_organization
        UNIQUE (team_id, organization_id)
);

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    role user_role NOT NULL DEFAULT 'member',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ,

    CONSTRAINT email_unique UNIQUE (email),

    CONSTRAINT valid_email
        CHECK (
            email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
        ),

    CONSTRAINT full_name_nonempty
        CHECK (LENGTH(TRIM(full_name)) > 0),

    CONSTRAINT unique_user_organization
        UNIQUE (user_id, organization_id)
);

CREATE TABLE team_memberships (
    membership_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    team_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT membership_team_fk
        FOREIGN KEY (team_id, organization_id)
        REFERENCES teams(team_id, organization_id),

    CONSTRAINT membership_user_fk
        FOREIGN KEY (user_id, organization_id)
        REFERENCES users(user_id, organization_id),

    CONSTRAINT unique_team_membership
        UNIQUE (team_id, user_id)
);

-- ------------------------------------------------
-- 3. CHANNEL MANAGEMENT
-- ------------------------------------------------

CREATE TABLE channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(team_id),
    channel_name VARCHAR(100) NOT NULL,
    channel_category channel_type NOT NULL,
    created_by BIGINT NOT NULL REFERENCES users(user_id),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT unique_channel_name
        UNIQUE (team_id, channel_name),

    CONSTRAINT channel_name_nonempty
        CHECK (LENGTH(TRIM(channel_name)) > 0)
);

CREATE TABLE channel_memberships (
    channel_membership_id BIGINT
        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_id BIGINT NOT NULL REFERENCES channels(channel_id),
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT unique_channel_membership
        UNIQUE (channel_id, user_id)
);

-- ------------------------------------------------
-- 4. MESSAGES AND THREADS
-- ------------------------------------------------

CREATE TABLE messages (
    message_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_id BIGINT NOT NULL REFERENCES channels(channel_id),
    sender_id BIGINT NOT NULL REFERENCES users(user_id),
    parent_message_id BIGINT REFERENCES messages(message_id),
    content TEXT NOT NULL,
    priority message_priority NOT NULL DEFAULT 'normal',
    status message_status NOT NULL DEFAULT 'sent',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edited_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,

    CONSTRAINT content_nonempty
        CHECK (LENGTH(TRIM(content)) > 0),

    CONSTRAINT content_length
        CHECK (LENGTH(content) <= 10000),

    CONSTRAINT no_self_parent
        CHECK (
            parent_message_id IS NULL
            OR parent_message_id <> message_id
        ),

    CONSTRAINT edit_time_valid
        CHECK (edited_at IS NULL OR edited_at >= created_at)
);

CREATE TABLE message_recipients (
    message_id BIGINT NOT NULL
        REFERENCES messages(message_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,

    PRIMARY KEY (message_id, user_id),

    CONSTRAINT valid_receipt_order
        CHECK (
            (read_at IS NULL OR delivered_at IS NULL
                OR read_at >= delivered_at)
            AND
            (acknowledged_at IS NULL OR read_at IS NOT NULL)
        )
);

-- ------------------------------------------------
-- 5. REVIEW-LIKE COMMUNICATION DISCUSSIONS
-- ------------------------------------------------

CREATE TABLE message_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id BIGINT NOT NULL
        REFERENCES messages(message_id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES users(user_id),
    parent_comment_id BIGINT
        REFERENCES message_comments(comment_id),
    comment_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edited_at TIMESTAMPTZ,

    CONSTRAINT comment_nonempty
        CHECK (LENGTH(TRIM(comment_text)) > 0),

    CONSTRAINT comment_length
        CHECK (LENGTH(comment_text) <= 5000),

    CONSTRAINT no_self_parent_comment
        CHECK (
            parent_comment_id IS NULL
            OR parent_comment_id <> comment_id
        )
);

CREATE TABLE message_reactions (
    message_id BIGINT NOT NULL
        REFERENCES messages(message_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id),
    reaction VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (message_id, user_id, reaction),

    CONSTRAINT reaction_nonempty
        CHECK (LENGTH(TRIM(reaction)) > 0)
);

-- ------------------------------------------------
-- 6. ACTION ITEMS AND ACCOUNTABILITY
-- ------------------------------------------------

CREATE TABLE action_items (
    task_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_message_id BIGINT NOT NULL
        REFERENCES messages(message_id),
    owner_id BIGINT NOT NULL REFERENCES users(user_id),
    assigned_by BIGINT NOT NULL REFERENCES users(user_id),
    task_title VARCHAR(250) NOT NULL,
    task_description TEXT,
    status task_status NOT NULL DEFAULT 'open',
    due_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT task_title_nonempty
        CHECK (LENGTH(TRIM(task_title)) > 0),

    CONSTRAINT completion_timestamp_valid
        CHECK (
            completed_at IS NULL
            OR completed_at >= created_at
        ),

    CONSTRAINT completed_state_consistency
        CHECK (
            (status = 'completed' AND completed_at IS NOT NULL)
            OR
            (status <> 'completed' AND completed_at IS NULL)
        )
);

CREATE TABLE task_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_id BIGINT NOT NULL
        REFERENCES action_items(task_id) ON DELETE CASCADE,
    changed_by BIGINT NOT NULL REFERENCES users(user_id),
    previous_status task_status,
    new_status task_status NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    change_note TEXT
);

-- ------------------------------------------------
-- 7. COMMUNICATION POLICIES
-- ------------------------------------------------

CREATE TABLE communication_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(team_id),
    policy_name VARCHAR(120) NOT NULL,
    high_priority_minutes INTEGER NOT NULL DEFAULT 240,
    urgent_priority_minutes INTEGER NOT NULL DEFAULT 15,
    require_acknowledgment BOOLEAN NOT NULL DEFAULT FALSE,
    minimum_acknowledgments INTEGER NOT NULL DEFAULT 0,
    allow_observer_posting BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_high_threshold
        CHECK (high_priority_minutes > 0),

    CONSTRAINT valid_urgent_threshold
        CHECK (urgent_priority_minutes > 0),

    CONSTRAINT valid_acknowledgment_count
        CHECK (minimum_acknowledgments >= 0),

    CONSTRAINT unique_team_policy
        UNIQUE (team_id, policy_name)
);

-- ------------------------------------------------
-- 8. NOTIFICATIONS AND AUDIT
-- ------------------------------------------------

CREATE TABLE notifications (
    notification_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recipient_id BIGINT NOT NULL REFERENCES users(user_id),
    message_id BIGINT REFERENCES messages(message_id),
    task_id BIGINT REFERENCES action_items(task_id),
    notification_type VARCHAR(50) NOT NULL,
    status notification_status NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    last_error TEXT,

    CONSTRAINT notification_target_required
        CHECK (message_id IS NOT NULL OR task_id IS NOT NULL),

    CONSTRAINT valid_attempts
        CHECK (attempts >= 0)
);

CREATE TABLE audit_events (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id BIGINT REFERENCES users(user_id),
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------
-- 9. PERFORMANCE INDEXES
-- ------------------------------------------------

CREATE INDEX idx_users_organization_active
    ON users(organization_id, active);

CREATE INDEX idx_team_memberships_user
    ON team_memberships(user_id, team_id)
    WHERE active = TRUE;

CREATE INDEX idx_channel_memberships_user
    ON channel_memberships(user_id, channel_id)
    WHERE active = TRUE;

CREATE INDEX idx_messages_channel_created
    ON messages(channel_id, created_at DESC);

CREATE INDEX idx_messages_priority_status
    ON messages(priority, status, created_at)
    WHERE priority IN ('high', 'urgent');

CREATE INDEX idx_messages_parent
    ON messages(parent_message_id)
    WHERE parent_message_id IS NOT NULL;

CREATE INDEX idx_recipients_pending
    ON message_recipients(user_id, message_id)
    WHERE acknowledged_at IS NULL;

CREATE INDEX idx_comments_message_created
    ON message_comments(message_id, created_at);

CREATE INDEX idx_action_items_owner_status
    ON action_items(owner_id, status, due_at);

CREATE INDEX idx_action_items_overdue
    ON action_items(due_at)
    WHERE status <> 'completed';

CREATE INDEX idx_notifications_pending
    ON notifications(recipient_id, created_at)
    WHERE status IN ('pending', 'failed');

CREATE INDEX idx_audit_entity
    ON audit_events(entity_type, entity_id, occurred_at DESC);

CREATE INDEX idx_audit_details
    ON audit_events USING GIN(event_details);

-- ------------------------------------------------
-- 10. AUDIT TRIGGER
-- ------------------------------------------------

CREATE OR REPLACE FUNCTION record_message_audit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_events (
            actor_id,
            event_type,
            entity_type,
            entity_id,
            event_details
        )
        VALUES (
            NEW.sender_id,
            'MESSAGE_CREATED',
            'message',
            NEW.message_id,
            jsonb_build_object(
                'channel_id', NEW.channel_id,
                'priority', NEW.priority,
                'status', NEW.status
            )
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_events (
            actor_id,
            event_type,
            entity_type,
            entity_id,
            event_details
        )
        VALUES (
            NEW.sender_id,
            'MESSAGE_UPDATED',
            'message',
            NEW.message_id,
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'content_changed', OLD.content IS DISTINCT FROM NEW.content
            )
        );

        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_message_audit
AFTER INSERT OR UPDATE ON messages
FOR EACH ROW
EXECUTE FUNCTION record_message_audit();

-- ------------------------------------------------
-- 11. TASK STATE TRANSITION TRIGGER
-- ------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_task_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status <> OLD.status THEN

        IF OLD.status = 'completed' THEN
            RAISE EXCEPTION
                'Completed tasks cannot be reopened.';
        END IF;

        IF OLD.status = 'open'
           AND NEW.status NOT IN ('in_progress', 'blocked', 'completed') THEN
            RAISE EXCEPTION 'Invalid OPEN task transition.';
        END IF;

        IF OLD.status = 'in_progress'
           AND NEW.status NOT IN ('open', 'blocked', 'completed') THEN
            RAISE EXCEPTION 'Invalid IN_PROGRESS task transition.';
        END IF;

        IF OLD.status = 'blocked'
           AND NEW.status NOT IN ('open', 'in_progress') THEN
            RAISE EXCEPTION 'Invalid BLOCKED task transition.';
        END IF;

        IF NEW.status = 'completed' THEN
            NEW.completed_at = NOW();
        ELSE
            NEW.completed_at = NULL;
        END IF;

        INSERT INTO task_history (
            task_id,
            changed_by,
            previous_status,
            new_status,
            change_note
        )
        VALUES (
            NEW.task_id,
            NEW.assigned_by,
            OLD.status,
            NEW.status,
            'Status transition recorded automatically'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_task_transition
BEFORE UPDATE OF status ON action_items
FOR EACH ROW
EXECUTE FUNCTION enforce_task_transition();

-- ------------------------------------------------
-- 12. MESSAGE RECIPIENT VALIDATION
-- ------------------------------------------------

CREATE OR REPLACE FUNCTION validate_message_recipient()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    source_channel BIGINT;
BEGIN
    SELECT channel_id
    INTO source_channel
    FROM messages
    WHERE message_id = NEW.message_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Message does not exist.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM channel_memberships cm
        WHERE cm.channel_id = source_channel
          AND cm.user_id = NEW.user_id
          AND cm.active = TRUE
    ) THEN
        RAISE EXCEPTION
            'Recipient % is not an active channel member.',
            NEW.user_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_recipient
BEFORE INSERT OR UPDATE ON message_recipients
FOR EACH ROW
EXECUTE FUNCTION validate_message_recipient();

-- ------------------------------------------------
-- 13. CHANNEL MESSAGE CREATION FUNCTION
-- ------------------------------------------------

CREATE OR REPLACE FUNCTION create_team_message(
    p_sender_id BIGINT,
    p_channel_id BIGINT,
    p_content TEXT,
    p_priority message_priority DEFAULT 'normal',
    p_parent_message_id BIGINT DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    new_message_id BIGINT;
    sender_role user_role;
    source_channel_type channel_type;
BEGIN
    IF p_content IS NULL
       OR LENGTH(TRIM(p_content)) = 0
       OR LENGTH(p_content) > 10000 THEN
        RAISE EXCEPTION 'Invalid message content.';
    END IF;

    SELECT u.role, c.channel_category
    INTO sender_role, source_channel_type
    FROM users u
    JOIN channels c
      ON c.channel_id = p_channel_id
    JOIN channel_memberships cm
      ON cm.channel_id = c.channel_id
     AND cm.user_id = u.user_id
     AND cm.active = TRUE
    WHERE u.user_id = p_sender_id
      AND u.active = TRUE
      AND c.archived = FALSE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Sender must be active and belong to the channel.';
    END IF;

    IF sender_role = 'observer' THEN
        RAISE EXCEPTION 'Observers cannot send messages.';
    END IF;

    IF source_channel_type = 'announcement'
       AND sender_role NOT IN ('admin', 'manager') THEN
        RAISE EXCEPTION
            'Only administrators and managers can publish announcements.';
    END IF;

    IF p_parent_message_id IS NOT NULL
       AND NOT EXISTS (
           SELECT 1
           FROM messages
           WHERE message_id = p_parent_message_id
             AND channel_id = p_channel_id
       ) THEN
        RAISE EXCEPTION
            'Parent message must belong to the same channel.';
    END IF;

    INSERT INTO messages (
        channel_id,
        sender_id,
        parent_message_id,
        content,
        priority
    )
    VALUES (
        p_channel_id,
        p_sender_id,
        p_parent_message_id,
        TRIM(p_content),
        p_priority
    )
    RETURNING message_id INTO new_message_id;

    INSERT INTO message_recipients (
        message_id,
        user_id
    )
    SELECT
        new_message_id,
        cm.user_id
    FROM channel_memberships cm
    WHERE cm.channel_id = p_channel_id
      AND cm.active = TRUE
      AND cm.user_id <> p_sender_id;

    INSERT INTO notifications (
        recipient_id,
        message_id,
        notification_type
    )
    SELECT
        mr.user_id,
        new_message_id,
        'NEW_MESSAGE'
    FROM message_recipients mr
    WHERE mr.message_id = new_message_id;

    RETURN new_message_id;
END;
$$;

-- ------------------------------------------------
-- 14. ACKNOWLEDGMENT FUNCTION
-- ------------------------------------------------

CREATE OR REPLACE FUNCTION acknowledge_team_message(
    p_user_id BIGINT,
    p_message_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    source_channel BIGINT;
    remaining_count BIGINT;
BEGIN
    SELECT channel_id
    INTO source_channel
    FROM messages
    WHERE message_id = p_message_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Message does not exist.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM message_recipients
        WHERE message_id = p_message_id
          AND user_id = p_user_id
    ) THEN
        RAISE EXCEPTION 'User is not a designated recipient.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM channel_memberships
        WHERE channel_id = source_channel
          AND user_id = p_user_id
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION 'Active channel membership required.';
    END IF;

    UPDATE message_recipients
    SET
        read_at = COALESCE(read_at, NOW()),
        acknowledged_at = COALESCE(acknowledged_at, NOW())
    WHERE message_id = p_message_id
      AND user_id = p_user_id;

    SELECT COUNT(*)
    INTO remaining_count
    FROM message_recipients
    WHERE message_id = p_message_id
      AND acknowledged_at IS NULL;

    IF remaining_count = 0 THEN
        UPDATE messages
        SET status = 'acknowledged'
        WHERE message_id = p_message_id
          AND status = 'sent';
    END IF;

    RETURN remaining_count = 0;
END;
$$;

-- ------------------------------------------------
-- 15. TASK ASSIGNMENT FUNCTION
-- ------------------------------------------------

CREATE OR REPLACE FUNCTION assign_communication_task(
    p_creator_id BIGINT,
    p_message_id BIGINT,
    p_owner_id BIGINT,
    p_title VARCHAR(250),
    p_due_at TIMESTAMPTZ
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    source_channel BIGINT;
    source_sender BIGINT;
    creator_role user_role;
    new_task_id BIGINT;
BEGIN
    SELECT channel_id, sender_id
    INTO source_channel, source_sender
    FROM messages
    WHERE message_id = p_message_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Source message not found.';
    END IF;

    SELECT role
    INTO creator_role
    FROM users
    WHERE user_id = p_creator_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Creator is inactive or unavailable.';
    END IF;

    IF p_creator_id <> source_sender
       AND creator_role NOT IN ('admin', 'manager') THEN
        RAISE EXCEPTION 'Task assignment permission denied.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM channel_memberships
        WHERE channel_id = source_channel
          AND user_id = p_creator_id
          AND active = TRUE
    ) OR NOT EXISTS (
        SELECT 1
        FROM channel_memberships
        WHERE channel_id = source_channel
          AND user_id = p_owner_id
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION
            'Creator and task owner must belong to the channel.';
    END IF;

    IF p_title IS NULL
       OR LENGTH(TRIM(p_title)) = 0
       OR p_due_at <= NOW() THEN
        RAISE EXCEPTION 'Invalid action item details.';
    END IF;

    INSERT INTO action_items (
        source_message_id,
        owner_id,
        assigned_by,
        task_title,
        due_at
    )
    VALUES (
        p_message_id,
        p_owner_id,
        p_creator_id,
        TRIM(p_title),
        p_due_at
    )
    RETURNING task_id INTO new_task_id;

    INSERT INTO notifications (
        recipient_id,
        task_id,
        notification_type
    )
    VALUES (
        p_owner_id,
        new_task_id,
        'TASK_ASSIGNED'
    );

    RETURN new_task_id;
END;
$$;

-- ------------------------------------------------
-- 16. TASK UPDATE PROCEDURE
-- ------------------------------------------------

CREATE OR REPLACE PROCEDURE update_action_item_status(
    p_actor_id BIGINT,
    p_task_id BIGINT,
    p_new_status task_status
)
LANGUAGE plpgsql
AS $$
DECLARE
    source_owner BIGINT;
    source_creator BIGINT;
    source_message BIGINT;
    source_sender BIGINT;
    actor_role user_role;
BEGIN
    SELECT
        ai.owner_id,
        ai.assigned_by,
        ai.source_message_id,
        m.sender_id
    INTO
        source_owner,
        source_creator,
        source_message,
        source_sender
    FROM action_items ai
    JOIN messages m
      ON m.message_id = ai.source_message_id
    WHERE ai.task_id = p_task_id
    FOR UPDATE OF ai;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Action item not found.';
    END IF;

    SELECT role
    INTO actor_role
    FROM users
    WHERE user_id = p_actor_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Actor is unavailable.';
    END IF;

    IF p_actor_id NOT IN (
        source_owner,
        source_creator,
        source_sender
    ) AND actor_role NOT IN ('admin', 'manager') THEN
        RAISE EXCEPTION 'Task update permission denied.';
    END IF;

    UPDATE action_items
    SET status = p_new_status
    WHERE task_id = p_task_id;
END;
$$;

-- ------------------------------------------------
-- 17. MESSAGE READ RECEIPT VIEW
-- ------------------------------------------------

CREATE OR REPLACE VIEW message_delivery_report AS
SELECT
    m.message_id,
    m.channel_id,
    m.sender_id,
    m.priority,
    m.status,
    m.created_at,
    COUNT(mr.user_id) AS recipient_count,
    COUNT(mr.read_at) AS read_count,
    COUNT(mr.acknowledged_at) AS acknowledged_count,
    COUNT(mr.user_id) - COUNT(mr.acknowledged_at)
        AS pending_acknowledgments,
    CASE
        WHEN COUNT(mr.user_id) = 0 THEN 1.0
        ELSE ROUND(
            COUNT(mr.acknowledged_at)::NUMERIC
            / COUNT(mr.user_id),
            3
        )
    END AS acknowledgment_rate
FROM messages m
LEFT JOIN message_recipients mr
    ON mr.message_id = m.message_id
GROUP BY
    m.message_id,
    m.channel_id,
    m.sender_id,
    m.priority,
    m.status,
    m.created_at;

-- ------------------------------------------------
-- 18. ACTION ITEM REPORT
-- ------------------------------------------------

CREATE OR REPLACE VIEW action_item_report AS
SELECT
    ai.task_id,
    ai.task_title,
    ai.owner_id,
    u.full_name AS owner_name,
    ai.assigned_by,
    ai.status,
    ai.due_at,
    ai.created_at,
    ai.completed_at,
    CASE
        WHEN ai.status <> 'completed'
         AND ai.due_at < NOW()
        THEN TRUE
        ELSE FALSE
    END AS is_overdue
FROM action_items ai
JOIN users u
    ON u.user_id = ai.owner_id;

-- ------------------------------------------------
-- 19. ESCALATION ELIGIBILITY VIEW
-- ------------------------------------------------

CREATE OR REPLACE VIEW communication_escalations AS
SELECT
    m.message_id,
    m.channel_id,
    m.sender_id,
    m.priority,
    m.created_at,
    EXTRACT(
        EPOCH FROM (NOW() - m.created_at)
    ) / 60 AS age_minutes,
    COUNT(mr.user_id) FILTER (
        WHERE mr.acknowledged_at IS NULL
    ) AS pending_recipients,
    CASE
        WHEN m.priority = 'urgent' THEN
            COALESCE(cp.urgent_priority_minutes, 15)
        WHEN m.priority = 'high' THEN
            COALESCE(cp.high_priority_minutes, 240)
        ELSE NULL
    END AS escalation_threshold_minutes
FROM messages m
JOIN channels c
    ON c.channel_id = m.channel_id
JOIN teams t
    ON t.team_id = c.team_id
LEFT JOIN communication_policies cp
    ON cp.team_id = t.team_id
   AND cp.active = TRUE
LEFT JOIN message_recipients mr
    ON mr.message_id = m.message_id
WHERE m.priority IN ('high', 'urgent')
  AND m.status NOT IN ('resolved', 'archived')
GROUP BY
    m.message_id,
    m.channel_id,
    m.sender_id,
    m.priority,
    m.created_at,
    cp.urgent_priority_minutes,
    cp.high_priority_minutes;

-- ------------------------------------------------
-- 20. SAMPLE ORGANIZATION AND USERS
-- ------------------------------------------------

INSERT INTO organizations (organization_name)
VALUES ('Technology Operations Group');

INSERT INTO teams (
    organization_id,
    team_name,
    description
)
VALUES (
    1,
    'Product Engineering',
    'Software development and delivery team'
);

INSERT INTO users (
    organization_id,
    full_name,
    email,
    role
)
VALUES
    (1, 'Project Manager', 'manager@example.com', 'manager'),
    (1, 'Software Engineer', 'engineer@example.com', 'member'),
    (1, 'Quality Analyst', 'analyst@example.com', 'member'),
    (1, 'Read Only Observer', 'observer@example.com', 'observer'),
    (1, 'System Administrator', 'admin@example.com', 'admin');

INSERT INTO team_memberships (
    team_id,
    user_id,
    organization_id
)
VALUES
    (1, 1, 1),
    (1, 2, 1),
    (1, 3, 1),
    (1, 4, 1),
    (1, 5, 1);

INSERT INTO channels (
    team_id,
    channel_name,
    channel_category,
    created_by,
    description
)
VALUES
    (
        1,
        'General',
        'general',
        1,
        'General team discussions'
    ),
    (
        1,
        'Product Delivery',
        'project',
        1,
        'Project coordination and delivery'
    ),
    (
        1,
        'Official Announcements',
        'announcement',
        1,
        'Manager-approved announcements'
    ),
    (
        1,
        'Production Incidents',
        'incident',
        1,
        'Urgent operational communication'
    );

INSERT INTO channel_memberships (
    channel_id,
    user_id
)
SELECT
    c.channel_id,
    tm.user_id
FROM channels c
JOIN team_memberships tm
    ON tm.team_id = c.team_id
WHERE c.team_id = 1
  AND c.channel_category <> 'private';

INSERT INTO communication_policies (
    team_id,
    policy_name,
    high_priority_minutes,
    urgent_priority_minutes,
    require_acknowledgment,
    minimum_acknowledgments
)
VALUES (
    1,
    'Engineering Communication Policy',
    240,
    15,
    TRUE,
    1
);

-- ------------------------------------------------
-- 21. VALID MESSAGE WORKFLOW
-- ------------------------------------------------

DO $$
DECLARE
    project_channel BIGINT;
    message_id_value BIGINT;
    task_id_value BIGINT;
BEGIN
    SELECT channel_id
    INTO project_channel
    FROM channels
    WHERE channel_name = 'Product Delivery';

    message_id_value := create_team_message(
        1,
        project_channel,
        'Complete integration testing before deployment.',
        'high',
        NULL
    );

    PERFORM acknowledge_team_message(2, message_id_value);
    PERFORM acknowledge_team_message(3, message_id_value);

    task_id_value := assign_communication_task(
        1,
        message_id_value,
        2,
        'Complete integration test suite',
        NOW() + INTERVAL '2 days'
    );

    CALL update_action_item_status(
        2,
        task_id_value,
        'in_progress'
    );
END;
$$;

-- ------------------------------------------------
-- 22. UNACKNOWLEDGED MESSAGE WORKFLOW
-- ------------------------------------------------

DO $$
DECLARE
    incident_channel BIGINT;
    message_id_value BIGINT;
BEGIN
    SELECT channel_id
    INTO incident_channel
    FROM channels
    WHERE channel_name = 'Production Incidents';

    message_id_value := create_team_message(
        1,
        incident_channel,
        'URGENT: Production API latency requires immediate investigation.',
        'urgent',
        NULL
    );

    -- Deliberately leave this message unacknowledged.
    -- It remains eligible for escalation after the configured threshold.
END;
$$;

-- ------------------------------------------------
-- 23. MESSAGE RETRIEVAL
-- ------------------------------------------------

SELECT
    m.message_id,
    c.channel_name,
    u.full_name AS sender,
    m.content,
    m.priority,
    m.status,
    m.created_at
FROM messages m
JOIN channels c
    ON c.channel_id = m.channel_id
JOIN users u
    ON u.user_id = m.sender_id
ORDER BY m.created_at DESC;

-- ------------------------------------------------
-- 24. THREAD RETRIEVAL
-- ------------------------------------------------

SELECT
    parent.message_id AS parent_id,
    parent.content AS parent_content,
    child.message_id AS reply_id,
    child.content AS reply_content,
    child.created_at AS reply_created_at
FROM messages parent
LEFT JOIN messages child
    ON child.parent_message_id = parent.message_id
ORDER BY parent.message_id, child.created_at;

-- ------------------------------------------------
-- 25. VALIDATION: ACTIVE CHANNEL MEMBERSHIP
-- ------------------------------------------------

SELECT
    c.channel_name,
    u.full_name,
    cm.active,
    CASE
        WHEN cm.active AND u.active THEN 'ELIGIBLE'
        ELSE 'INELIGIBLE'
    END AS membership_eligibility
FROM channel_memberships cm
JOIN channels c
    ON c.channel_id = cm.channel_id
JOIN users u
    ON u.user_id = cm.user_id
ORDER BY c.channel_name, u.full_name;

-- ------------------------------------------------
-- 26. ACKNOWLEDGMENT AGGREGATION
-- ------------------------------------------------

SELECT
    c.channel_name,
    COUNT(m.message_id) AS messages,
    SUM(r.recipient_count) AS recipients,
    SUM(r.acknowledged_count) AS acknowledgments,
    SUM(r.pending_acknowledgments) AS pending,
    ROUND(
        AVG(r.acknowledgment_rate),
        3
    ) AS average_acknowledgment_rate
FROM channels c
LEFT JOIN messages m
    ON m.channel_id = c.channel_id
LEFT JOIN message_delivery_report r
    ON r.message_id = m.message_id
GROUP BY c.channel_id, c.channel_name
ORDER BY c.channel_name;

-- ------------------------------------------------
-- 27. ACTION ITEM REPORTING
-- ------------------------------------------------

SELECT
    task_id,
    task_title,
    owner_name,
    status,
    due_at,
    is_overdue
FROM action_item_report
ORDER BY due_at;

-- ------------------------------------------------
-- 28. OVERDUE ACTION ITEMS
-- ------------------------------------------------

SELECT
    task_id,
    task_title,
    owner_name,
    due_at,
    NOW() - due_at AS overdue_duration
FROM action_item_report
WHERE is_overdue = TRUE
ORDER BY due_at;

-- ------------------------------------------------
-- 29. ESCALATION ELIGIBILITY
-- ------------------------------------------------

SELECT
    message_id,
    priority,
    age_minutes,
    escalation_threshold_minutes,
    pending_recipients,
    CASE
        WHEN age_minutes > escalation_threshold_minutes
         AND pending_recipients > 0
        THEN 'ESCALATE'
        ELSE 'WITHIN_THRESHOLD'
    END AS escalation_decision
FROM communication_escalations
ORDER BY age_minutes DESC;

-- ------------------------------------------------
-- 30. CTE-BASED TEAM COMMUNICATION SCORECARD
-- ------------------------------------------------

WITH message_metrics AS (
    SELECT
        c.team_id,
        COUNT(m.message_id) AS total_messages,
        COUNT(m.message_id) FILTER (
            WHERE m.status = 'acknowledged'
        ) AS acknowledged_messages
    FROM channels c
    LEFT JOIN messages m
        ON m.channel_id = c.channel_id
    GROUP BY c.team_id
),
task_metrics AS (
    SELECT
        c.team_id,
        COUNT(ai.task_id) AS total_tasks,
        COUNT(ai.task_id) FILTER (
            WHERE ai.status = 'completed'
        ) AS completed_tasks,
        COUNT(ai.task_id) FILTER (
            WHERE ai.status <> 'completed'
              AND ai.due_at < NOW()
        ) AS overdue_tasks
    FROM channels c
    LEFT JOIN messages m
        ON m.channel_id = c.channel_id
    LEFT JOIN action_items ai
        ON ai.source_message_id = m.message_id
    GROUP BY c.team_id
)
SELECT
    t.team_name,
    mm.total_messages,
    mm.acknowledged_messages,
    CASE
        WHEN mm.total_messages = 0 THEN 0
        ELSE ROUND(
            mm.acknowledged_messages::NUMERIC
            / mm.total_messages,
            3
        )
    END AS acknowledgment_ratio,
    tm.total_tasks,
    tm.completed_tasks,
    tm.overdue_tasks
FROM teams t
JOIN message_metrics mm
    ON mm.team_id = t.team_id
JOIN task_metrics tm
    ON tm.team_id = t.team_id;

-- ------------------------------------------------
-- 31. NOTIFICATION RETRIEVAL
-- ------------------------------------------------

SELECT
    n.notification_id,
    u.full_name AS recipient,
    n.notification_type,
    n.status,
    n.attempts,
    n.created_at
FROM notifications n
JOIN users u
    ON u.user_id = n.recipient_id
WHERE n.status IN ('pending', 'failed')
ORDER BY n.created_at;

-- ------------------------------------------------
-- 32. AUDIT HISTORY
-- ------------------------------------------------

SELECT
    audit_id,
    actor_id,
    event_type,
    entity_type,
    entity_id,
    event_details,
    occurred_at
FROM audit_events
ORDER BY occurred_at DESC;

-- ------------------------------------------------
-- 33. FAILURE CASE: INVALID RECIPIENT
-- ------------------------------------------------
-- The following transaction is intentionally rolled back.
-- The recipient is not a channel member, so the trigger rejects it.

DO $$
DECLARE
    message_id_value BIGINT;
    invalid_user_id BIGINT;
BEGIN
    SELECT message_id
    INTO message_id_value
    FROM messages
    ORDER BY message_id
    LIMIT 1;

    invalid_user_id := 999999;

    BEGIN
        INSERT INTO message_recipients (
            message_id,
            user_id
        )
        VALUES (
            message_id_value,
            invalid_user_id
        );
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'Expected failure: recipient user does not exist.';
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected recipient validation failure: %',
                SQLERRM;
    END;
END;
$$;

-- ------------------------------------------------
-- 34. TRANSACTIONAL TASK COMPLETION
-- ------------------------------------------------

DO $$
DECLARE
    selected_task BIGINT;
BEGIN
    SELECT task_id
    INTO selected_task
    FROM action_items
    WHERE status = 'in_progress'
    ORDER BY task_id
    LIMIT 1;

    IF selected_task IS NOT NULL THEN
        BEGIN
            CALL update_action_item_status(
                2,
                selected_task,
                'completed'
            );

            RAISE NOTICE
                'Action item % completed.',
                selected_task;
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE
                    'Task completion failed: %',
                    SQLERRM;
        END;
    END IF;
END;
$$;

-- ------------------------------------------------
-- 35. COMMUNICATION QUALITY METRICS
-- ------------------------------------------------

SELECT
    c.channel_name,
    COUNT(DISTINCT m.message_id) AS message_volume,
    COUNT(DISTINCT mr.user_id) AS recipient_interactions,
    COUNT(DISTINCT mr.user_id) FILTER (
        WHERE mr.read_at IS NOT NULL
    ) AS users_who_read,
    COUNT(DISTINCT mr.user_id) FILTER (
        WHERE mr.acknowledged_at IS NOT NULL
    ) AS users_who_acknowledged,
    COUNT(DISTINCT ai.task_id) AS assigned_actions,
    COUNT(DISTINCT ai.task_id) FILTER (
        WHERE ai.status = 'completed'
    ) AS completed_actions
FROM channels c
LEFT JOIN messages m
    ON m.channel_id = c.channel_id
LEFT JOIN message_recipients mr
    ON mr.message_id = m.message_id
LEFT JOIN action_items ai
    ON ai.source_message_id = m.message_id
GROUP BY c.channel_id, c.channel_name
ORDER BY message_volume DESC;

COMMIT;
