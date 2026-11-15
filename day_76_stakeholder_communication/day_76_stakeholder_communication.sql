-- ============================================================
-- STAKEHOLDER COMMUNICATION MANAGEMENT AND GOVERNANCE
-- PostgreSQL 14+
--
-- Models:
-- Stakeholders, communication plans, messages, reviews,
-- approvals, feedback, acknowledgement, escalation and reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS stakeholder_mgmt;

SET search_path TO stakeholder_mgmt, public;

-- ------------------------------------------------------------
-- ENUMERATED DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE influence_level AS ENUM (
    'LOW', 'MEDIUM', 'HIGH'
);

CREATE TYPE engagement_level AS ENUM (
    'UNAWARE',
    'RESISTANT',
    'NEUTRAL',
    'SUPPORTIVE',
    'LEADING'
);

CREATE TYPE communication_channel AS ENUM (
    'EMAIL',
    'MEETING',
    'REPORT',
    'PHONE',
    'COLLABORATION'
);

CREATE TYPE communication_priority AS ENUM (
    'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
);

CREATE TYPE communication_status AS ENUM (
    'DRAFT',
    'APPROVED',
    'SENT',
    'ACKNOWLEDGED',
    'ESCALATED',
    'CANCELLED'
);

CREATE TYPE review_decision AS ENUM (
    'COMMENTED',
    'APPROVED',
    'CHANGES_REQUESTED',
    'DISMISSED'
);

CREATE TYPE feedback_sentiment AS ENUM (
    'POSITIVE', 'NEUTRAL', 'NEGATIVE'
);

CREATE TYPE feedback_status AS ENUM (
    'OPEN', 'IN_PROGRESS', 'RESOLVED'
);

-- ------------------------------------------------------------
-- STAKEHOLDER REGISTRY
-- ------------------------------------------------------------

CREATE TABLE stakeholder (
    stakeholder_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    stakeholder_code VARCHAR(30) NOT NULL UNIQUE,

    full_name VARCHAR(150) NOT NULL,

    job_title VARCHAR(120) NOT NULL,

    department VARCHAR(120) NOT NULL,

    organization VARCHAR(150) NOT NULL,

    email VARCHAR(254) NOT NULL UNIQUE,

    influence influence_level NOT NULL,

    interest influence_level NOT NULL,

    engagement engagement_level NOT NULL DEFAULT 'NEUTRAL',

    preferred_channel communication_channel NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (full_name = BTRIM(full_name) AND full_name <> ''),

    CHECK (POSITION('@' IN email) > 1)
);

CREATE INDEX idx_stakeholder_department
    ON stakeholder(department);

CREATE INDEX idx_stakeholder_engagement
    ON stakeholder(engagement, active);

CREATE INDEX idx_stakeholder_influence_interest
    ON stakeholder(influence, interest);

-- ------------------------------------------------------------
-- COMMUNICATION PLANS
-- ------------------------------------------------------------

CREATE TABLE communication_plan (
    plan_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    plan_code VARCHAR(30) NOT NULL UNIQUE,

    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholder(stakeholder_id),

    objective TEXT NOT NULL,

    key_message TEXT NOT NULL,

    channel communication_channel NOT NULL,

    frequency_days INTEGER NOT NULL CHECK (frequency_days > 0),

    responsible_person VARCHAR(120) NOT NULL,

    priority communication_priority NOT NULL DEFAULT 'MEDIUM',

    next_communication TIMESTAMPTZ NOT NULL,

    success_measure TEXT NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (BTRIM(objective) <> ''),

    CHECK (BTRIM(key_message) <> '')
);

CREATE INDEX idx_plan_due
    ON communication_plan(next_communication)
    WHERE active = TRUE;

CREATE INDEX idx_plan_stakeholder
    ON communication_plan(stakeholder_id, active);

-- ------------------------------------------------------------
-- COMMUNICATION POLICY
-- ------------------------------------------------------------

CREATE TABLE communication_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(120) NOT NULL UNIQUE,

    minimum_priority communication_priority NOT NULL DEFAULT 'LOW',

    required_approvals INTEGER NOT NULL DEFAULT 1
        CHECK (required_approvals >= 0),

    acknowledgement_hours INTEGER NOT NULL DEFAULT 48
        CHECK (acknowledgement_hours > 0),

    require_resolved_discussions BOOLEAN NOT NULL DEFAULT TRUE,

    require_authorized_approver BOOLEAN NOT NULL DEFAULT TRUE,

    require_acknowledgement BOOLEAN NOT NULL DEFAULT TRUE,

    allow_confidential_email BOOLEAN NOT NULL DEFAULT FALSE,

    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE policy_channel (
    policy_id BIGINT NOT NULL
        REFERENCES communication_policy(policy_id)
        ON DELETE CASCADE,

    channel communication_channel NOT NULL,

    PRIMARY KEY (policy_id, channel)
);

CREATE TABLE stakeholder_policy (
    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholder(stakeholder_id),

    policy_id BIGINT NOT NULL
        REFERENCES communication_policy(policy_id),

    PRIMARY KEY (stakeholder_id, policy_id)
);

-- ------------------------------------------------------------
-- REVIEWER REGISTRY
-- ------------------------------------------------------------

CREATE TABLE reviewer (
    reviewer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    stakeholder_id BIGINT NOT NULL UNIQUE
        REFERENCES stakeholder(stakeholder_id),

    authorized BOOLEAN NOT NULL DEFAULT TRUE,

    review_domain VARCHAR(120) NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- COMMUNICATION RECORDS
-- ------------------------------------------------------------

CREATE TABLE communication (
    communication_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    communication_code VARCHAR(40) NOT NULL UNIQUE,

    plan_id BIGINT NOT NULL
        REFERENCES communication_plan(plan_id),

    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholder(stakeholder_id),

    subject VARCHAR(250) NOT NULL,

    body TEXT NOT NULL,

    channel communication_channel NOT NULL,

    priority communication_priority NOT NULL,

    status communication_status NOT NULL DEFAULT 'DRAFT',

    approval_required BOOLEAN NOT NULL DEFAULT TRUE,

    acknowledgement_required BOOLEAN NOT NULL DEFAULT TRUE,

    confidential BOOLEAN NOT NULL DEFAULT FALSE,

    created_by VARCHAR(120) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    approved_by VARCHAR(120),

    approved_at TIMESTAMPTZ,

    sent_at TIMESTAMPTZ,

    acknowledged_at TIMESTAMPTZ,

    deadline TIMESTAMPTZ,

    CHECK (BTRIM(subject) <> ''),

    CHECK (BTRIM(body) <> ''),

    CHECK (
        (status NOT IN ('APPROVED', 'SENT', 'ACKNOWLEDGED', 'ESCALATED'))
        OR
        (approval_required = FALSE OR approved_at IS NOT NULL)
    ),

    CHECK (
        status NOT IN ('SENT', 'ACKNOWLEDGED', 'ESCALATED')
        OR sent_at IS NOT NULL
    ),

    CHECK (
        status <> 'ACKNOWLEDGED'
        OR acknowledged_at IS NOT NULL
    )
);

CREATE INDEX idx_communication_stakeholder
    ON communication(stakeholder_id, created_at DESC);

CREATE INDEX idx_communication_status_deadline
    ON communication(status, deadline)
    WHERE status = 'SENT';

CREATE INDEX idx_communication_plan
    ON communication(plan_id);

CREATE INDEX idx_communication_created
    ON communication(created_at DESC);

-- ------------------------------------------------------------
-- COMMUNICATION REVIEW AND APPROVAL RECORDS
-- ------------------------------------------------------------

CREATE TABLE communication_review (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    communication_id BIGINT NOT NULL
        REFERENCES communication(communication_id)
        ON DELETE CASCADE,

    reviewer_id BIGINT NOT NULL
        REFERENCES reviewer(reviewer_id),

    decision review_decision NOT NULL,

    comments TEXT NOT NULL DEFAULT '',

    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    dismissed_at TIMESTAMPTZ,

    UNIQUE (communication_id, reviewer_id),

    CHECK (
        decision <> 'CHANGES_REQUESTED'
        OR BTRIM(comments) <> ''
    ),

    CHECK (
        (decision = 'DISMISSED' AND dismissed_at IS NOT NULL)
        OR
        (decision <> 'DISMISSED' AND dismissed_at IS NULL)
    )
);

CREATE INDEX idx_review_communication
    ON communication_review(communication_id, decision);

CREATE INDEX idx_review_reviewer
    ON communication_review(reviewer_id, submitted_at DESC);

-- ------------------------------------------------------------
-- INLINE COMMENTS AND DISCUSSIONS
-- ------------------------------------------------------------

CREATE TABLE review_comment (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    review_id BIGINT NOT NULL
        REFERENCES communication_review(review_id)
        ON DELETE CASCADE,

    parent_comment_id BIGINT
        REFERENCES review_comment(comment_id),

    author_stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholder(stakeholder_id),

    comment_text TEXT NOT NULL,

    resolved BOOLEAN NOT NULL DEFAULT FALSE,

    resolved_by BIGINT
        REFERENCES stakeholder(stakeholder_id),

    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (BTRIM(comment_text) <> ''),

    CHECK (
        (resolved = FALSE AND resolved_at IS NULL)
        OR
        (resolved = TRUE AND resolved_at IS NOT NULL)
    )
);

CREATE INDEX idx_review_comment_review
    ON review_comment(review_id, created_at);

CREATE INDEX idx_unresolved_comments
    ON review_comment(resolved)
    WHERE resolved = FALSE;

-- ------------------------------------------------------------
-- AUTOMATED COMMUNICATION STATUS CHECKS
-- ------------------------------------------------------------

CREATE TABLE communication_status_check (
    check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    communication_id BIGINT NOT NULL
        REFERENCES communication(communication_id)
        ON DELETE CASCADE,

    check_name VARCHAR(120) NOT NULL,

    passed BOOLEAN NOT NULL,

    result_details TEXT,

    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (communication_id, check_name)
);

CREATE INDEX idx_status_check_result
    ON communication_status_check(communication_id, passed);

-- ------------------------------------------------------------
-- FEEDBACK MANAGEMENT
-- ------------------------------------------------------------

CREATE TABLE stakeholder_feedback (
    feedback_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    communication_id BIGINT NOT NULL
        REFERENCES communication(communication_id),

    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholder(stakeholder_id),

    sentiment feedback_sentiment NOT NULL,

    content TEXT NOT NULL,

    status feedback_status NOT NULL DEFAULT 'OPEN',

    resolution TEXT,

    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    resolved_at TIMESTAMPTZ,

    CHECK (BTRIM(content) <> ''),

    CHECK (
        (status = 'RESOLVED' AND resolution IS NOT NULL
         AND resolved_at IS NOT NULL)
        OR
        (status <> 'RESOLVED' AND resolved_at IS NULL)
    )
);

CREATE INDEX idx_feedback_status
    ON stakeholder_feedback(status, received_at);

CREATE INDEX idx_feedback_sentiment
    ON stakeholder_feedback(sentiment, status);

-- ------------------------------------------------------------
-- AUDIT TRAIL
-- ------------------------------------------------------------

CREATE TABLE communication_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    entity_type VARCHAR(60) NOT NULL,

    entity_id BIGINT NOT NULL,

    action VARCHAR(100) NOT NULL,

    actor VARCHAR(120) NOT NULL,

    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_entity
    ON communication_audit(entity_type, entity_id, occurred_at DESC);

CREATE INDEX idx_audit_timestamp
    ON communication_audit(occurred_at DESC);

-- ------------------------------------------------------------
-- AUDIT TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION record_communication_audit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id BIGINT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_id := OLD.communication_id;

        INSERT INTO communication_audit(
            entity_type,
            entity_id,
            action,
            actor,
            event_details
        )
        VALUES (
            'COMMUNICATION',
            v_id,
            'DELETED',
            CURRENT_USER,
            jsonb_build_object('old_status', OLD.status)
        );

        RETURN OLD;
    END IF;

    v_id := NEW.communication_id;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO communication_audit(
            entity_type,
            entity_id,
            action,
            actor,
            event_details
        )
        VALUES (
            'COMMUNICATION',
            v_id,
            'CREATED',
            CURRENT_USER,
            jsonb_build_object('status', NEW.status)
        );

    ELSIF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO communication_audit(
            entity_type,
            entity_id,
            action,
            actor,
            event_details
        )
        VALUES (
            'COMMUNICATION',
            v_id,
            'STATUS_CHANGED',
            CURRENT_USER,
            jsonb_build_object(
                'previous_status', OLD.status,
                'new_status', NEW.status
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_communication_audit
AFTER INSERT OR UPDATE OR DELETE
ON communication
FOR EACH ROW
EXECUTE FUNCTION record_communication_audit();

-- ------------------------------------------------------------
-- COMMUNICATION STATE VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_communication_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN

        IF OLD.status IN ('ACKNOWLEDGED', 'CANCELLED') THEN
            IF NEW.status IS DISTINCT FROM OLD.status THEN
                RAISE EXCEPTION
                    'Terminal communication state cannot be changed';
            END IF;
        END IF;

        IF NEW.status = 'APPROVED'
           AND OLD.status <> 'DRAFT' THEN
            RAISE EXCEPTION
                'Only draft communications can be approved';
        END IF;

        IF NEW.status = 'SENT'
           AND OLD.status <> 'APPROVED'
           AND NOT (
               OLD.status = 'DRAFT'
               AND NEW.approval_required = FALSE
           ) THEN
            RAISE EXCEPTION
                'Communication must be approved before sending';
        END IF;

        IF NEW.status = 'ACKNOWLEDGED'
           AND OLD.status <> 'SENT' THEN
            RAISE EXCEPTION
                'Only sent communications can be acknowledged';
        END IF;

        IF NEW.status = 'ESCALATED'
           AND OLD.status <> 'SENT' THEN
            RAISE EXCEPTION
                'Only sent communications can be escalated';
        END IF;

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_communication_transition
BEFORE UPDATE ON communication
FOR EACH ROW
EXECUTE FUNCTION validate_communication_transition();

-- ------------------------------------------------------------
-- APPROVAL ELIGIBILITY FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION communication_approval_eligible(
    p_communication_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_required INTEGER;
    v_approvals INTEGER;
    v_resolved_required BOOLEAN;
    v_unresolved BIGINT;
    v_policy_id BIGINT;
BEGIN
    SELECT sp.policy_id
    INTO v_policy_id
    FROM communication c
    JOIN stakeholder_policy sp
      ON sp.stakeholder_id = c.stakeholder_id
    JOIN communication_policy cp
      ON cp.policy_id = sp.policy_id
     AND cp.active = TRUE
    WHERE c.communication_id = p_communication_id
    ORDER BY sp.policy_id
    LIMIT 1;

    IF v_policy_id IS NULL THEN
        RETURN FALSE;
    END IF;

    SELECT
        required_approvals,
        require_resolved_discussions
    INTO
        v_required,
        v_resolved_required
    FROM communication_policy
    WHERE policy_id = v_policy_id;

    SELECT COUNT(*)
    INTO v_approvals
    FROM communication_review cr
    JOIN reviewer r
      ON r.reviewer_id = cr.reviewer_id
    JOIN stakeholder s
      ON s.stakeholder_id = r.stakeholder_id
    WHERE cr.communication_id = p_communication_id
      AND cr.decision = 'APPROVED'
      AND r.active = TRUE
      AND r.authorized = TRUE
      AND s.active = TRUE
      AND r.stakeholder_id <> (
          SELECT stakeholder_id
          FROM communication
          WHERE communication_id = p_communication_id
      );

    IF v_approvals < v_required THEN
        RETURN FALSE;
    END IF;

    IF v_resolved_required THEN
        SELECT COUNT(*)
        INTO v_unresolved
        FROM review_comment rc
        JOIN communication_review cr
          ON cr.review_id = rc.review_id
        WHERE cr.communication_id = p_communication_id
          AND rc.resolved = FALSE;

        IF v_unresolved > 0 THEN
            RETURN FALSE;
        END IF;

        IF EXISTS (
            SELECT 1
            FROM communication_review
            WHERE communication_id = p_communication_id
              AND decision = 'CHANGES_REQUESTED'
        ) THEN
            RETURN FALSE;
        END IF;
    END IF;

    RETURN TRUE;
END;
$$;

-- ------------------------------------------------------------
-- COMMUNICATION APPROVAL PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE approve_communication(
    p_communication_id BIGINT,
    p_approver VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status communication_status;
    v_authorized BOOLEAN;
    v_required_authorization BOOLEAN;
    v_policy_id BIGINT;
BEGIN
    SELECT status
    INTO v_status
    FROM communication
    WHERE communication_id = p_communication_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Communication not found';
    END IF;

    IF v_status <> 'DRAFT' THEN
        RAISE EXCEPTION 'Only draft communications can be approved';
    END IF;

    SELECT cp.policy_id
    INTO v_policy_id
    FROM communication c
    JOIN stakeholder_policy sp
      ON sp.stakeholder_id = c.stakeholder_id
    JOIN communication_policy cp
      ON cp.policy_id = sp.policy_id
    WHERE c.communication_id = p_communication_id
      AND cp.active = TRUE
    ORDER BY cp.policy_id
    LIMIT 1;

    IF v_policy_id IS NULL THEN
        RAISE EXCEPTION 'No active stakeholder policy';
    END IF;

    SELECT require_authorized_approver
    INTO v_required_authorization
    FROM communication_policy
    WHERE policy_id = v_policy_id;

    SELECT EXISTS (
        SELECT 1
        FROM reviewer r
        JOIN stakeholder s
          ON s.stakeholder_id = r.stakeholder_id
        WHERE s.full_name = p_approver
          AND r.authorized = TRUE
          AND r.active = TRUE
          AND s.active = TRUE
    )
    INTO v_authorized;

    IF v_required_authorization AND NOT v_authorized THEN
        RAISE EXCEPTION 'Approver lacks authorization';
    END IF;

    IF NOT communication_approval_eligible(p_communication_id) THEN
        RAISE EXCEPTION 'Approval requirements are not satisfied';
    END IF;

    UPDATE communication
    SET status = 'APPROVED',
        approved_by = p_approver,
        approved_at = NOW()
    WHERE communication_id = p_communication_id;
END;
$$;

-- ------------------------------------------------------------
-- MESSAGE ACKNOWLEDGEMENT PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE acknowledge_communication(
    p_communication_id BIGINT,
    p_stakeholder_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE communication
    SET status = 'ACKNOWLEDGED',
        acknowledged_at = NOW()
    WHERE communication_id = p_communication_id
      AND stakeholder_id = p_stakeholder_id
      AND status = 'SENT';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Acknowledgement failed: invalid recipient or state';
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- OVERDUE COMMUNICATION ESCALATION
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE escalate_overdue_communications()
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE communication
    SET status = 'ESCALATED'
    WHERE status = 'SENT'
      AND deadline IS NOT NULL
      AND deadline < NOW();
END;
$$;

-- ------------------------------------------------------------
-- REVIEW COMMENT RESOLUTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION resolve_review_comment(
    p_comment_id BIGINT,
    p_resolver_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE review_comment
    SET resolved = TRUE,
        resolved_by = p_resolver_id,
        resolved_at = NOW()
    WHERE comment_id = p_comment_id
      AND resolved = FALSE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Comment not found or already resolved';
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- FEEDBACK RESOLUTION
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE resolve_feedback(
    p_feedback_id BIGINT,
    p_resolution TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF BTRIM(p_resolution) = '' THEN
        RAISE EXCEPTION 'Resolution cannot be empty';
    END IF;

    UPDATE stakeholder_feedback
    SET status = 'RESOLVED',
        resolution = p_resolution,
        resolved_at = NOW()
    WHERE feedback_id = p_feedback_id
      AND status <> 'RESOLVED';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Feedback not found or already resolved';
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- POWER-INTEREST STAKEHOLDER CLASSIFICATION
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW stakeholder_engagement_matrix AS
SELECT
    stakeholder_id,
    stakeholder_code,
    full_name,
    job_title,
    department,
    influence,
    interest,
    engagement,
    CASE
        WHEN influence = 'HIGH' AND interest = 'HIGH'
            THEN 'MANAGE_CLOSely'
        WHEN influence = 'HIGH'
            THEN 'KEEP_SATISFIED'
        WHEN interest = 'HIGH'
            THEN 'KEEP_INFORMED'
        ELSE 'MONITOR'
    END AS management_strategy
FROM stakeholder
WHERE active = TRUE;

-- ------------------------------------------------------------
-- COMMUNICATION DASHBOARD
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW communication_dashboard AS
SELECT
    s.stakeholder_id,
    s.stakeholder_code,
    s.full_name,
    COUNT(c.communication_id) AS total_communications,

    COUNT(c.communication_id) FILTER (
        WHERE c.status = 'DRAFT'
    ) AS drafts,

    COUNT(c.communication_id) FILTER (
        WHERE c.status = 'SENT'
    ) AS sent,

    COUNT(c.communication_id) FILTER (
        WHERE c.status = 'ACKNOWLEDGED'
    ) AS acknowledged,

    COUNT(c.communication_id) FILTER (
        WHERE c.status = 'ESCALATED'
    ) AS escalated,

    COUNT(c.communication_id) FILTER (
        WHERE c.deadline < NOW()
          AND c.status = 'SENT'
    ) AS overdue

FROM stakeholder s
LEFT JOIN communication c
    ON c.stakeholder_id = s.stakeholder_id

GROUP BY
    s.stakeholder_id,
    s.stakeholder_code,
    s.full_name;

-- ------------------------------------------------------------
-- FEEDBACK REPORT
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW feedback_dashboard AS
SELECT
    stakeholder_id,

    COUNT(*) AS feedback_count,

    COUNT(*) FILTER (
        WHERE sentiment = 'POSITIVE'
    ) AS positive_count,

    COUNT(*) FILTER (
        WHERE sentiment = 'NEUTRAL'
    ) AS neutral_count,

    COUNT(*) FILTER (
        WHERE sentiment = 'NEGATIVE'
    ) AS negative_count,

    COUNT(*) FILTER (
        WHERE status <> 'RESOLVED'
    ) AS unresolved_count

FROM stakeholder_feedback
GROUP BY stakeholder_id;

-- ------------------------------------------------------------
-- SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO stakeholder (
    stakeholder_code,
    full_name,
    job_title,
    department,
    organization,
    email,
    influence,
    interest,
    engagement,
    preferred_channel
)
VALUES
(
    'STK-001',
    'Ananya Sharma',
    'Project Sponsor',
    'Executive Management',
    'Enterprise Operations',
    'ananya@example.com',
    'HIGH',
    'HIGH',
    'SUPPORTIVE',
    'MEETING'
),
(
    'STK-002',
    'Rahul Verma',
    'Technical Lead',
    'Engineering',
    'Technology Division',
    'rahul@example.com',
    'HIGH',
    'HIGH',
    'LEADING',
    'COLLABORATION'
),
(
    'STK-003',
    'Priya Singh',
    'Business Representative',
    'Operations',
    'Operations Division',
    'priya@example.com',
    'MEDIUM',
    'HIGH',
    'NEUTRAL',
    'EMAIL'
),
(
    'STK-004',
    'Vikram Rao',
    'Compliance Officer',
    'Governance',
    'Risk and Compliance',
    'vikram@example.com',
    'HIGH',
    'MEDIUM',
    'NEUTRAL',
    'REPORT'
);

INSERT INTO communication_policy (
    policy_name,
    minimum_priority,
    required_approvals,
    acknowledgement_hours,
    require_resolved_discussions,
    require_authorized_approver,
    require_acknowledgement,
    allow_confidential_email
)
VALUES (
    'EXECUTIVE_COMMUNICATION_POLICY',
    'MEDIUM',
    1,
    24,
    TRUE,
    TRUE,
    TRUE,
    FALSE
);

INSERT INTO policy_channel(policy_id, channel)
SELECT policy_id, unnest(
    ARRAY[
        'EMAIL'::communication_channel,
        'MEETING'::communication_channel,
        'REPORT'::communication_channel
    ]
)
FROM communication_policy
WHERE policy_name = 'EXECUTIVE_COMMUNICATION_POLICY';

INSERT INTO stakeholder_policy(stakeholder_id, policy_id)
SELECT s.stakeholder_id, p.policy_id
FROM stakeholder s
CROSS JOIN communication_policy p
WHERE s.stakeholder_code = 'STK-001'
  AND p.policy_name = 'EXECUTIVE_COMMUNICATION_POLICY';

INSERT INTO reviewer(
    stakeholder_id,
    authorized,
    review_domain
)
SELECT stakeholder_id, TRUE, 'TECHNICAL'
FROM stakeholder
WHERE stakeholder_code = 'STK-002';

INSERT INTO reviewer(
    stakeholder_id,
    authorized,
    review_domain
)
SELECT stakeholder_id, TRUE, 'GOVERNANCE'
FROM stakeholder
WHERE stakeholder_code = 'STK-004';

INSERT INTO communication_plan (
    plan_code,
    stakeholder_id,
    objective,
    key_message,
    channel,
    frequency_days,
    responsible_person,
    priority,
    next_communication,
    success_measure
)
SELECT
    'PLAN-001',
    stakeholder_id,
    'Provide project status and obtain sponsor decisions.',
    'Report milestone progress, risks, and pending decisions.',
    'EMAIL',
    7,
    'Project Manager',
    'HIGH',
    NOW() + INTERVAL '7 days',
    'Acknowledgement and recorded sponsor decisions.'
FROM stakeholder
WHERE stakeholder_code = 'STK-001';

INSERT INTO communication_plan (
    plan_code,
    stakeholder_id,
    objective,
    key_message,
    channel,
    frequency_days,
    responsible_person,
    priority,
    next_communication,
    success_measure
)
SELECT
    'PLAN-002',
    stakeholder_id,
    'Collect operational readiness feedback.',
    'Confirm user readiness and unresolved issues.',
    'MEETING',
    5,
    'Business Analyst',
    'MEDIUM',
    NOW() + INTERVAL '5 days',
    'Recorded operational readiness assessment.'
FROM stakeholder
WHERE stakeholder_code = 'STK-003';

-- Valid communication in draft state.
INSERT INTO communication (
    communication_code,
    plan_id,
    stakeholder_id,
    subject,
    body,
    channel,
    priority,
    created_by,
    deadline
)
SELECT
    'COM-001',
    p.plan_id,
    p.stakeholder_id,
    'Weekly Project Status and Deployment Decision',
    'Integration testing is complete. Three issues remain. ' ||
    'Sponsor decision is requested on the deployment schedule.',
    'EMAIL',
    'HIGH',
    'PROJECT_MANAGER',
    NOW() + INTERVAL '24 hours'
FROM communication_plan p
WHERE p.plan_code = 'PLAN-001';

-- Independent technical approval.
INSERT INTO communication_review (
    communication_id,
    reviewer_id,
    decision,
    comments
)
SELECT
    c.communication_id,
    r.reviewer_id,
    'APPROVED',
    'Technical progress and deployment risks verified.'
FROM communication c
JOIN communication_plan p
  ON p.plan_id = c.plan_id
JOIN stakeholder s
  ON s.stakeholder_id = p.stakeholder_id
JOIN stakeholder reviewer_stakeholder
  ON reviewer_stakeholder.stakeholder_code = 'STK-002'
JOIN reviewer r
  ON r.stakeholder_id = reviewer_stakeholder.stakeholder_id
WHERE c.communication_code = 'COM-001';

-- Sample review discussion.
INSERT INTO review_comment (
    review_id,
    author_stakeholder_id,
    comment_text
)
SELECT
    cr.review_id,
    reviewer_stakeholder.stakeholder_id,
    'Include the final deployment risk assessment in the report.'
FROM communication_review cr
JOIN communication c
  ON c.communication_id = cr.communication_id
JOIN stakeholder reviewer_stakeholder
  ON reviewer_stakeholder.stakeholder_code = 'STK-002'
WHERE c.communication_code = 'COM-001';

-- Sample automated checks.
INSERT INTO communication_status_check (
    communication_id,
    check_name,
    passed,
    result_details
)
SELECT
    communication_id,
    'RECIPIENT_VALIDATION',
    TRUE,
    'Recipient exists and is active.'
FROM communication
WHERE communication_code = 'COM-001';

INSERT INTO communication_status_check (
    communication_id,
    check_name,
    passed,
    result_details
)
SELECT
    communication_id,
    'CONTENT_REVIEW',
    TRUE,
    'Required content fields are present.'
FROM communication
WHERE communication_code = 'COM-001';

-- Resolve discussion before formal approval.
SELECT resolve_review_comment(
    rc.comment_id,
    s.stakeholder_id
)
FROM review_comment rc
JOIN communication_review cr
  ON cr.review_id = rc.review_id
JOIN communication c
  ON c.communication_id = cr.communication_id
JOIN stakeholder s
  ON s.stakeholder_code = 'STK-002'
WHERE c.communication_code = 'COM-001';

-- Approve the communication using policy validation.
CALL approve_communication(
    (
        SELECT communication_id
        FROM communication
        WHERE communication_code = 'COM-001'
    ),
    'Rahul Verma'
);

-- Delivery is recorded as a database workflow transition.
UPDATE communication
SET status = 'SENT',
    sent_at = NOW()
WHERE communication_code = 'COM-001'
  AND status = 'APPROVED';

-- Record acknowledgement.
CALL acknowledge_communication(
    (
        SELECT communication_id
        FROM communication
        WHERE communication_code = 'COM-001'
    ),
    (
        SELECT stakeholder_id
        FROM stakeholder
        WHERE stakeholder_code = 'STK-001'
    )
);

-- Feedback from the sponsor.
INSERT INTO stakeholder_feedback (
    communication_id,
    stakeholder_id,
    sentiment,
    content
)
SELECT
    c.communication_id,
    s.stakeholder_id,
    'POSITIVE',
    'The report is clear. Include a quantified deployment risk assessment.'
FROM communication c
JOIN stakeholder s
  ON s.stakeholder_code = 'STK-001'
WHERE c.communication_code = 'COM-001';

-- A separate overdue communication demonstrates escalation.
INSERT INTO communication (
    communication_code,
    plan_id,
    stakeholder_id,
    subject,
    body,
    channel,
    priority,
    status,
    approval_required,
    created_by,
    sent_at,
    deadline
)
SELECT
    'COM-002',
    p.plan_id,
    p.stakeholder_id,
    'Operational Readiness Confirmation',
    'Please confirm readiness and outstanding operational issues.',
    'MEETING',
    'MEDIUM',
    'SENT',
    FALSE,
    'BUSINESS_ANALYST',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '1 day'
FROM communication_plan p
WHERE p.plan_code = 'PLAN-002';

-- ------------------------------------------------------------
-- TRANSACTIONAL FEEDBACK RESOLUTION
-- ------------------------------------------------------------

DO $$
DECLARE
    v_feedback_id BIGINT;
BEGIN
    SELECT feedback_id
    INTO v_feedback_id
    FROM stakeholder_feedback
    WHERE sentiment = 'POSITIVE'
    ORDER BY feedback_id
    LIMIT 1;

    IF v_feedback_id IS NOT NULL THEN
        CALL resolve_feedback(
            v_feedback_id,
            'Risk assessment incorporated into the next project report.'
        );
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- QUERY 1: STAKEHOLDER SEGMENTATION
-- ------------------------------------------------------------

SELECT *
FROM stakeholder_engagement_matrix
ORDER BY management_strategy, full_name;

-- ------------------------------------------------------------
-- QUERY 2: COMMUNICATION DASHBOARD
-- ------------------------------------------------------------

SELECT *
FROM communication_dashboard
ORDER BY stakeholder_code;

-- ------------------------------------------------------------
-- QUERY 3: APPROVAL ELIGIBILITY
-- ------------------------------------------------------------

SELECT
    c.communication_code,
    c.status,
    communication_approval_eligible(c.communication_id)
        AS approval_eligible
FROM communication c;

-- ------------------------------------------------------------
-- QUERY 4: FEEDBACK AGGREGATION
-- ------------------------------------------------------------

SELECT
    s.full_name,
    f.feedback_count,
    f.positive_count,
    f.neutral_count,
    f.negative_count,
    f.unresolved_count
FROM feedback_dashboard f
JOIN stakeholder s
  ON s.stakeholder_id = f.stakeholder_id
ORDER BY f.negative_count DESC;

-- ------------------------------------------------------------
-- QUERY 5: REQUIRED ACKNOWLEDGEMENT REPORT
-- ------------------------------------------------------------

SELECT
    communication_code,
    subject,
    status,
    sent_at,
    deadline,
    CASE
        WHEN status = 'ACKNOWLEDGED' THEN 'CONFIRMED'
        WHEN status = 'SENT' AND deadline < NOW() THEN 'OVERDUE'
        WHEN status = 'SENT' THEN 'AWAITING'
        ELSE 'NOT_SENT'
    END AS acknowledgement_state
FROM communication
WHERE acknowledgement_required = TRUE
ORDER BY deadline NULLS LAST;

-- ------------------------------------------------------------
-- QUERY 6: REVIEW AND DISCUSSION REPORT
-- ------------------------------------------------------------

SELECT
    c.communication_code,
    s.full_name AS recipient,
    COUNT(DISTINCT cr.review_id) AS total_reviews,
    COUNT(DISTINCT cr.review_id) FILTER (
        WHERE cr.decision = 'APPROVED'
    ) AS approvals,
    COUNT(DISTINCT rc.comment_id) AS total_comments,
    COUNT(DISTINCT rc.comment_id) FILTER (
        WHERE rc.resolved = FALSE
    ) AS unresolved_comments
FROM communication c
JOIN stakeholder s
  ON s.stakeholder_id = c.stakeholder_id
LEFT JOIN communication_review cr
  ON cr.communication_id = c.communication_id
LEFT JOIN review_comment rc
  ON rc.review_id = cr.review_id
GROUP BY c.communication_code, s.full_name
ORDER BY c.communication_code;

-- ------------------------------------------------------------
-- QUERY 7: OVERDUE COMMUNICATIONS USING A CTE
-- ------------------------------------------------------------

WITH overdue_messages AS (
    SELECT
        communication_id,
        communication_code,
        stakeholder_id,
        subject,
        deadline,
        NOW() - deadline AS overdue_duration
    FROM communication
    WHERE status = 'SENT'
      AND deadline < NOW()
),
ranked_overdue AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY stakeholder_id
            ORDER BY deadline
        ) AS stakeholder_sequence
    FROM overdue_messages
)
SELECT
    r.communication_code,
    s.full_name,
    r.subject,
    r.overdue_duration,
    r.stakeholder_sequence
FROM ranked_overdue r
JOIN stakeholder s
  ON s.stakeholder_id = r.stakeholder_id
ORDER BY r.overdue_duration DESC;

-- ------------------------------------------------------------
-- QUERY 8: POLICY AND CHANNEL VALIDATION
-- ------------------------------------------------------------

SELECT
    c.communication_code,
    c.channel,
    cp.policy_name,
    EXISTS (
        SELECT 1
        FROM stakeholder_policy sp
        JOIN policy_channel pc
          ON pc.policy_id = sp.policy_id
        WHERE sp.stakeholder_id = c.stakeholder_id
          AND pc.channel = c.channel
    ) AS channel_permitted
FROM communication c
LEFT JOIN stakeholder_policy sp
  ON sp.stakeholder_id = c.stakeholder_id
LEFT JOIN communication_policy cp
  ON cp.policy_id = sp.policy_id
ORDER BY c.communication_code;

-- ------------------------------------------------------------
-- WORKFLOW: ESCALATE OVERDUE COMMUNICATIONS
-- ------------------------------------------------------------

CALL escalate_overdue_communications();

SELECT
    communication_code,
    status,
    deadline
FROM communication
WHERE status = 'ESCALATED';

-- ------------------------------------------------------------
-- QUERY 9: AUDIT REPORT
-- ------------------------------------------------------------

SELECT
    entity_type,
    entity_id,
    action,
    actor,
    occurred_at,
    event_details
FROM communication_audit
ORDER BY occurred_at DESC;

-- ------------------------------------------------------------
-- QUERY 10: COMMUNICATION EFFECTIVENESS
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_messages,

    COUNT(*) FILTER (
        WHERE status IN ('SENT', 'ACKNOWLEDGED', 'ESCALATED')
    ) AS delivered_or_attempted,

    COUNT(*) FILTER (
        WHERE status = 'ACKNOWLEDGED'
    ) AS acknowledged,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE status = 'ACKNOWLEDGED'
        )
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE status IN ('SENT', 'ACKNOWLEDGED', 'ESCALATED')
            ),
            0
        ),
        2
    ) AS acknowledgement_percentage

FROM communication;

COMMIT;
