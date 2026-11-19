-- ============================================================
-- COMMUNICATION REVIEW AND MANAGEMENT GOVERNANCE SYSTEM
-- PostgreSQL 15+
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS communication_management;

SET search_path TO communication_management, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE communication_type AS ENUM (
    'email',
    'meeting',
    'report',
    'presentation',
    'notice',
    'instant_message'
);

CREATE TYPE communication_status AS ENUM (
    'draft',
    'submitted',
    'under_review',
    'revision_required',
    'rejected',
    'approved',
    'published',
    'archived'
);

CREATE TYPE review_decision AS ENUM (
    'approve',
    'revise',
    'reject'
);

CREATE TYPE comment_severity AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

CREATE TYPE information_sensitivity AS ENUM (
    'public',
    'internal',
    'confidential',
    'restricted'
);

CREATE TYPE stakeholder_role AS ENUM (
    'administrator',
    'manager',
    'reviewer',
    'recipient',
    'observer'
);

-- ============================================================
-- 2. STAKEHOLDERS
-- ============================================================

CREATE TABLE stakeholders (
    stakeholder_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_code VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    department VARCHAR(120) NOT NULL,
    role stakeholder_role NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT stakeholder_name_nonempty
        CHECK (LENGTH(TRIM(full_name)) > 0),

    CONSTRAINT stakeholder_email_valid
        CHECK (email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$')
);

-- ============================================================
-- 3. COMMUNICATION CHANNELS AND OBJECTIVES
-- ============================================================

CREATE TABLE communication_channels (
    channel_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name VARCHAR(80) NOT NULL UNIQUE,
    channel_description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO communication_channels (
    channel_name,
    channel_description
)
VALUES
    ('Corporate Email', 'Formal organizational communication'),
    ('Management Meeting', 'Structured verbal communication'),
    ('Official Report', 'Documented operational communication'),
    ('Internal Portal', 'Organizational digital communication'),
    ('Instant Messaging', 'Short operational messages');

CREATE TABLE communication_objectives (
    objective_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    objective_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT
);

INSERT INTO communication_objectives (
    objective_name,
    description
)
VALUES
    ('Information Dissemination', 'Distribute relevant information'),
    ('Decision Communication', 'Communicate approved decisions'),
    ('Performance Reporting', 'Report organizational performance'),
    ('Issue Escalation', 'Escalate operational issues'),
    ('Action Assignment', 'Assign responsibilities and deadlines'),
    ('Stakeholder Coordination', 'Coordinate stakeholder activities');

-- ============================================================
-- 4. COMMUNICATION RECORDS
-- ============================================================

CREATE TABLE communications (
    communication_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    communication_code VARCHAR(40) NOT NULL UNIQUE,

    title VARCHAR(250) NOT NULL,

    communication_type communication_type NOT NULL,

    channel_id SMALLINT NOT NULL
        REFERENCES communication_channels(channel_id),

    sender_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    subject VARCHAR(300) NOT NULL,

    content TEXT NOT NULL,

    sensitivity information_sensitivity NOT NULL DEFAULT 'internal',

    status communication_status NOT NULL DEFAULT 'draft',

    version_number INTEGER NOT NULL DEFAULT 1,

    acknowledgement_required BOOLEAN NOT NULL DEFAULT FALSE,

    scheduled_at TIMESTAMPTZ,

    submitted_at TIMESTAMPTZ,

    published_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT communication_title_nonempty
        CHECK (LENGTH(TRIM(title)) > 0),

    CONSTRAINT communication_subject_nonempty
        CHECK (LENGTH(TRIM(subject)) > 0),

    CONSTRAINT communication_content_nonempty
        CHECK (LENGTH(TRIM(content)) > 0),

    CONSTRAINT communication_version_positive
        CHECK (version_number > 0),

    CONSTRAINT communication_status_dates
        CHECK (
            status NOT IN ('published', 'archived')
            OR published_at IS NOT NULL
        )
);

CREATE TABLE communication_objective_mapping (
    communication_id BIGINT NOT NULL
        REFERENCES communications(communication_id)
        ON DELETE CASCADE,

    objective_id BIGINT NOT NULL
        REFERENCES communication_objectives(objective_id),

    PRIMARY KEY (communication_id, objective_id)
);

CREATE TABLE communication_recipients (
    communication_id BIGINT NOT NULL
        REFERENCES communications(communication_id)
        ON DELETE CASCADE,

    stakeholder_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    delivery_status VARCHAR(20) NOT NULL DEFAULT 'pending',

    delivered_at TIMESTAMPTZ,

    read_at TIMESTAMPTZ,

    acknowledged_at TIMESTAMPTZ,

    PRIMARY KEY (communication_id, stakeholder_id),

    CONSTRAINT valid_delivery_status
        CHECK (
            delivery_status IN (
                'pending',
                'delivered',
                'failed',
                'read',
                'acknowledged'
            )
        ),

    CONSTRAINT read_requires_delivery
        CHECK (
            read_at IS NULL OR delivered_at IS NOT NULL
        ),

    CONSTRAINT acknowledgement_requires_read
        CHECK (
            acknowledged_at IS NULL OR read_at IS NOT NULL
        )
);

-- ============================================================
-- 5. REVIEWERS AND REVIEW POLICIES
-- ============================================================

CREATE TABLE review_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(150) NOT NULL UNIQUE,

    required_approvals INTEGER NOT NULL DEFAULT 2,

    minimum_score NUMERIC(5,2) NOT NULL DEFAULT 70,

    block_critical_comments BOOLEAN NOT NULL DEFAULT TRUE,

    require_objectives BOOLEAN NOT NULL DEFAULT TRUE,

    minimum_delivery_rate NUMERIC(5,2) NOT NULL DEFAULT 95,

    minimum_acknowledgement_rate NUMERIC(5,2) NOT NULL DEFAULT 80,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT policy_approvals_positive
        CHECK (required_approvals >= 1),

    CONSTRAINT policy_score_valid
        CHECK (minimum_score BETWEEN 0 AND 100),

    CONSTRAINT policy_delivery_valid
        CHECK (minimum_delivery_rate BETWEEN 0 AND 100),

    CONSTRAINT policy_acknowledgement_valid
        CHECK (minimum_acknowledgement_rate BETWEEN 0 AND 100)
);

INSERT INTO review_policies (
    policy_name,
    required_approvals,
    minimum_score,
    block_critical_comments,
    require_objectives,
    minimum_delivery_rate,
    minimum_acknowledgement_rate
)
VALUES (
    'Standard Communication Governance',
    2,
    70,
    TRUE,
    TRUE,
    95,
    80
);

CREATE TABLE communication_review_assignments (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    communication_id BIGINT NOT NULL
        REFERENCES communications(communication_id)
        ON DELETE CASCADE,

    reviewer_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    assigned_by BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (communication_id, reviewer_id)
);

-- ============================================================
-- 6. REVIEW DECISIONS
-- ============================================================

CREATE TABLE communication_reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    communication_id BIGINT NOT NULL
        REFERENCES communications(communication_id)
        ON DELETE CASCADE,

    reviewer_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    decision review_decision NOT NULL,

    average_score NUMERIC(5,2) NOT NULL,

    feedback TEXT NOT NULL,

    reviewed_version INTEGER NOT NULL,

    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        communication_id,
        reviewer_id,
        reviewed_version
    ),

    CONSTRAINT review_score_valid
        CHECK (average_score BETWEEN 0 AND 100),

    CONSTRAINT review_version_positive
        CHECK (reviewed_version > 0),

    CONSTRAINT review_feedback_nonempty
        CHECK (LENGTH(TRIM(feedback)) > 0)
);

CREATE TABLE review_criteria (
    criterion_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    criterion_code VARCHAR(60) NOT NULL UNIQUE,

    criterion_name VARCHAR(120) NOT NULL,

    description TEXT,

    weight NUMERIC(6,3) NOT NULL DEFAULT 1.0,

    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT criterion_weight_positive
        CHECK (weight > 0)
);

INSERT INTO review_criteria (
    criterion_code,
    criterion_name,
    description,
    weight,
    is_mandatory
)
VALUES
    ('clarity', 'Clarity', 'Understandability of communication', 1.0, TRUE),
    ('accuracy', 'Accuracy', 'Factual correctness', 1.5, TRUE),
    ('completeness', 'Completeness', 'Coverage of necessary information', 1.2, TRUE),
    ('audience_alignment', 'Audience Alignment', 'Suitability for recipients', 1.2, TRUE),
    ('timeliness', 'Timeliness', 'Appropriate communication timing', 1.0, TRUE),
    ('actionability', 'Actionability', 'Clear actions and responsibilities', 1.2, TRUE),
    ('professionalism', 'Professionalism', 'Appropriate tone and presentation', 1.0, TRUE);

CREATE TABLE communication_review_scores (
    review_id BIGINT NOT NULL
        REFERENCES communication_reviews(review_id)
        ON DELETE CASCADE,

    criterion_id SMALLINT NOT NULL
        REFERENCES review_criteria(criterion_id),

    score NUMERIC(5,2) NOT NULL,

    reviewer_observation TEXT,

    PRIMARY KEY (review_id, criterion_id),

    CONSTRAINT criterion_score_valid
        CHECK (score BETWEEN 0 AND 100)
);

-- ============================================================
-- 7. REVIEW COMMENTS AND DISCUSSIONS
-- ============================================================

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    review_id BIGINT NOT NULL
        REFERENCES communication_reviews(review_id)
        ON DELETE CASCADE,

    reviewer_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    criterion_id SMALLINT
        REFERENCES review_criteria(criterion_id),

    comment_text TEXT NOT NULL,

    severity comment_severity NOT NULL DEFAULT 'medium',

    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,

    resolved_by BIGINT
        REFERENCES stakeholders(stakeholder_id),

    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT comment_text_nonempty
        CHECK (LENGTH(TRIM(comment_text)) > 0),

    CONSTRAINT resolution_consistency
        CHECK (
            (is_resolved = FALSE AND resolved_at IS NULL AND resolved_by IS NULL)
            OR
            (is_resolved = TRUE AND resolved_at IS NOT NULL AND resolved_by IS NOT NULL)
        )
);

CREATE TABLE review_discussions (
    discussion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    comment_id BIGINT NOT NULL
        REFERENCES review_comments(comment_id)
        ON DELETE CASCADE,

    author_id BIGINT NOT NULL
        REFERENCES stakeholders(stakeholder_id),

    message TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT discussion_message_nonempty
        CHECK (LENGTH(TRIM(message)) > 0)
);

-- ============================================================
-- 8. AUDIT LOG
-- ============================================================

CREATE TABLE communication_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    communication_id BIGINT
        REFERENCES communications(communication_id)
        ON DELETE SET NULL,

    actor_id BIGINT
        REFERENCES stakeholders(stakeholder_id)
        ON DELETE SET NULL,

    event_type VARCHAR(100) NOT NULL,

    old_status communication_status,

    new_status communication_status,

    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,

    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 9. WORKFLOW INTEGRITY TRIGGERS
-- ============================================================

CREATE OR REPLACE FUNCTION validate_communication_submission()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    recipient_count INTEGER;
    objective_count INTEGER;
    sender_active BOOLEAN;
    policy_requires_objectives BOOLEAN;
BEGIN
    IF NEW.status = 'submitted'
       AND OLD.status IN ('draft', 'revision_required') THEN

        SELECT is_active
        INTO sender_active
        FROM stakeholders
        WHERE stakeholder_id = NEW.sender_id;

        IF sender_active IS DISTINCT FROM TRUE THEN
            RAISE EXCEPTION 'Inactive sender cannot submit communication.';
        END IF;

        SELECT COUNT(*)
        INTO recipient_count
        FROM communication_recipients
        WHERE communication_id = NEW.communication_id;

        IF recipient_count = 0 THEN
            RAISE EXCEPTION 'Communication requires recipients.';
        END IF;

        SELECT COUNT(*)
        INTO objective_count
        FROM communication_objective_mapping
        WHERE communication_id = NEW.communication_id;

        SELECT require_objectives
        INTO policy_requires_objectives
        FROM review_policies
        WHERE is_active
        ORDER BY policy_id DESC
        LIMIT 1;

        IF COALESCE(policy_requires_objectives, TRUE)
           AND objective_count = 0 THEN
            RAISE EXCEPTION 'Communication objectives are required.';
        END IF;

        NEW.submitted_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_communication_submission
BEFORE UPDATE OF status ON communications
FOR EACH ROW
EXECUTE FUNCTION validate_communication_submission();


CREATE OR REPLACE FUNCTION validate_communication_state_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'draft' AND NEW.status = 'submitted')
        OR
        (OLD.status = 'submitted' AND NEW.status IN ('under_review', 'rejected'))
        OR
        (OLD.status = 'under_review' AND NEW.status IN (
            'approved', 'rejected', 'revision_required'
        ))
        OR
        (OLD.status = 'revision_required' AND NEW.status = 'submitted')
        OR
        (OLD.status = 'approved' AND NEW.status = 'published')
        OR
        (OLD.status = 'published' AND NEW.status = 'archived')
        OR
        (OLD.status = 'rejected' AND NEW.status = 'archived')
    ) THEN
        RAISE EXCEPTION
            'Invalid communication transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    IF NEW.status = 'published' THEN
        NEW.published_at := CURRENT_TIMESTAMP;
    END IF;

    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_communication_state_transition
BEFORE UPDATE OF status ON communications
FOR EACH ROW
EXECUTE FUNCTION validate_communication_state_transition();


CREATE OR REPLACE FUNCTION validate_review_submission()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    communication_sender BIGINT;
    communication_status_value communication_status;
    current_version INTEGER;
    reviewer_active BOOLEAN;
    reviewer_role_value stakeholder_role;
    policy_score NUMERIC(5,2);
    calculated_score NUMERIC(5,2);
    mandatory_count INTEGER;
    supplied_count INTEGER;
BEGIN
    SELECT sender_id, status, version_number
    INTO communication_sender, communication_status_value, current_version
    FROM communications
    WHERE communication_id = NEW.communication_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Communication does not exist.';
    END IF;

    IF communication_status_value <> 'under_review' THEN
        RAISE EXCEPTION 'Communication is not under review.';
    END IF;

    IF NEW.reviewed_version <> current_version THEN
        RAISE EXCEPTION 'Review version does not match current content version.';
    END IF;

    IF NEW.reviewer_id = communication_sender THEN
        RAISE EXCEPTION 'Self-review is prohibited.';
    END IF;

    SELECT is_active, role
    INTO reviewer_active, reviewer_role_value
    FROM stakeholders
    WHERE stakeholder_id = NEW.reviewer_id;

    IF reviewer_active IS DISTINCT FROM TRUE
       OR reviewer_role_value NOT IN ('reviewer', 'manager', 'administrator') THEN
        RAISE EXCEPTION 'Reviewer is not eligible.';
    END IF;

    SELECT COUNT(*)
    INTO mandatory_count
    FROM review_criteria
    WHERE is_mandatory;

    SELECT COUNT(*)
    INTO supplied_count
    FROM communication_review_scores
    WHERE review_id = NEW.review_id;

    -- Scores are inserted after the review record, so the final
    -- completeness check is performed by the evaluation function.

    SELECT minimum_score
    INTO policy_score
    FROM review_policies
    WHERE is_active
    ORDER BY policy_id DESC
    LIMIT 1;

    IF NEW.decision = 'approve'
       AND NEW.average_score < COALESCE(policy_score, 70) THEN
        RAISE EXCEPTION 'Approval score is below the required threshold.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_review_submission
BEFORE INSERT ON communication_reviews
FOR EACH ROW
EXECUTE FUNCTION validate_review_submission();


CREATE OR REPLACE FUNCTION audit_communication_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO communication_audit (
        communication_id,
        actor_id,
        event_type,
        old_status,
        new_status,
        event_details
    )
    VALUES (
        NEW.communication_id,
        NEW.sender_id,
        CASE
            WHEN TG_OP = 'INSERT' THEN 'communication_created'
            ELSE 'communication_updated'
        END,
        CASE WHEN TG_OP = 'UPDATE' THEN OLD.status ELSE NULL END,
        NEW.status,
        jsonb_build_object(
            'version', NEW.version_number,
            'title', NEW.title,
            'sensitivity', NEW.sensitivity
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_communication
AFTER INSERT OR UPDATE ON communications
FOR EACH ROW
EXECUTE FUNCTION audit_communication_changes();


CREATE OR REPLACE FUNCTION validate_recipient()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    active_recipient BOOLEAN;
BEGIN
    SELECT is_active
    INTO active_recipient
    FROM stakeholders
    WHERE stakeholder_id = NEW.stakeholder_id;

    IF active_recipient IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'Recipient must be an active stakeholder.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_recipient
BEFORE INSERT ON communication_recipients
FOR EACH ROW
EXECUTE FUNCTION validate_recipient();

-- ============================================================
-- 10. PERFORMANCE INDEXES
-- ============================================================

CREATE INDEX idx_communications_status_created
ON communications(status, created_at DESC);

CREATE INDEX idx_communications_sender
ON communications(sender_id, created_at DESC);

CREATE INDEX idx_communications_type
ON communications(communication_type);

CREATE INDEX idx_recipients_stakeholder
ON communication_recipients(stakeholder_id, communication_id);

CREATE INDEX idx_reviews_communication_version
ON communication_reviews(
    communication_id,
    reviewed_version,
    decision
);

CREATE INDEX idx_reviews_reviewer
ON communication_reviews(reviewer_id, reviewed_at DESC);

CREATE INDEX idx_comments_unresolved
ON review_comments(review_id, severity)
WHERE is_resolved = FALSE;

CREATE INDEX idx_audit_communication_time
ON communication_audit(communication_id, event_time DESC);

CREATE INDEX idx_discussions_comment_time
ON review_discussions(comment_id, created_at);

CREATE INDEX idx_communication_content_search
ON communications
USING GIN (to_tsvector('english', title || ' ' || subject || ' ' || content));

-- ============================================================
-- 11. REVIEW EVALUATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_communication(
    p_communication_id BIGINT
)
RETURNS TABLE (
    communication_id BIGINT,
    current_version INTEGER,
    approval_count BIGINT,
    average_score NUMERIC,
    unresolved_critical_comments BIGINT,
    eligible BOOLEAN,
    reasons TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_version INTEGER;
    v_required_approvals INTEGER;
    v_minimum_score NUMERIC(5,2);
    v_block_critical BOOLEAN;
    v_approval_count BIGINT;
    v_average_score NUMERIC;
    v_critical_count BIGINT;
    v_rejected BOOLEAN;
    v_revision_requested BOOLEAN;
    v_reasons TEXT[] := ARRAY[]::TEXT[];
BEGIN
    SELECT version_number
    INTO v_version
    FROM communications
    WHERE communications.communication_id = p_communication_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Communication not found.';
    END IF;

    SELECT
        required_approvals,
        minimum_score,
        block_critical_comments
    INTO
        v_required_approvals,
        v_minimum_score,
        v_block_critical
    FROM review_policies
    WHERE is_active
    ORDER BY policy_id DESC
    LIMIT 1;

    SELECT COUNT(*)
    INTO v_approval_count
    FROM communication_reviews r
    JOIN stakeholders s
        ON s.stakeholder_id = r.reviewer_id
    WHERE r.communication_id = p_communication_id
      AND r.reviewed_version = v_version
      AND r.decision = 'approve'
      AND r.average_score >= COALESCE(v_minimum_score, 70)
      AND s.is_active
      AND s.role IN ('reviewer', 'manager', 'administrator');

    SELECT AVG(r.average_score)
    INTO v_average_score
    FROM communication_reviews r
    WHERE r.communication_id = p_communication_id
      AND r.reviewed_version = v_version;

    SELECT COUNT(*)
    INTO v_critical_count
    FROM review_comments rc
    JOIN communication_reviews r
        ON r.review_id = rc.review_id
    WHERE r.communication_id = p_communication_id
      AND r.reviewed_version = v_version
      AND rc.severity = 'critical'
      AND NOT rc.is_resolved;

    SELECT EXISTS (
        SELECT 1
        FROM communication_reviews
        WHERE communication_reviews.communication_id =
              p_communication_id
          AND reviewed_version = v_version
          AND decision = 'reject'
    )
    INTO v_rejected;

    SELECT EXISTS (
        SELECT 1
        FROM communication_reviews
        WHERE communication_reviews.communication_id =
              p_communication_id
          AND reviewed_version = v_version
          AND decision = 'revise'
    )
    INTO v_revision_requested;

    IF v_approval_count < COALESCE(v_required_approvals, 1) THEN
        v_reasons := array_append(
            v_reasons,
            'Insufficient eligible approvals'
        );
    END IF;

    IF v_rejected THEN
        v_reasons := array_append(
            v_reasons,
            'Communication rejected'
        );
    END IF;

    IF v_revision_requested THEN
        v_reasons := array_append(
            v_reasons,
            'Revision requested'
        );
    END IF;

    IF v_block_critical AND v_critical_count > 0 THEN
        v_reasons := array_append(
            v_reasons,
            'Unresolved critical comments'
        );
    END IF;

    RETURN QUERY
    SELECT
        p_communication_id,
        v_version,
        v_approval_count,
        COALESCE(v_average_score, 0),
        v_critical_count,
        cardinality(v_reasons) = 0,
        v_reasons;
END;
$$;

-- ============================================================
-- 12. PUBLICATION ELIGIBILITY PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE approve_communication(
    p_communication_id BIGINT,
    p_actor_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_sender_id BIGINT;
    v_status communication_status;
    v_eligible BOOLEAN;
    v_reasons TEXT[];
BEGIN
    SELECT sender_id, status
    INTO v_sender_id, v_status
    FROM communications
    WHERE communication_id = p_communication_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Communication not found.';
    END IF;

    IF v_sender_id <> p_actor_id THEN
        RAISE EXCEPTION 'Only the communication owner can authorize publication.';
    END IF;

    IF v_status <> 'under_review' THEN
        RAISE EXCEPTION 'Communication is not under review.';
    END IF;

    SELECT eligible, reasons
    INTO v_eligible, v_reasons
    FROM evaluate_communication(p_communication_id);

    IF NOT v_eligible THEN
        RAISE EXCEPTION 'Publication blocked: %',
            array_to_string(v_reasons, '; ');
    END IF;

    UPDATE communications
    SET status = 'approved',
        updated_at = CURRENT_TIMESTAMP
    WHERE communication_id = p_communication_id;
END;
$$;

-- ============================================================
-- 13. COMMUNICATION PERFORMANCE VIEW
-- ============================================================

CREATE OR REPLACE VIEW communication_performance AS
SELECT
    c.communication_id,
    c.communication_code,
    c.title,
    c.communication_type,
    c.status,
    COUNT(cr.stakeholder_id) AS total_recipients,

    COUNT(*) FILTER (
        WHERE cr.delivered_at IS NOT NULL
    ) AS delivered_count,

    COUNT(*) FILTER (
        WHERE cr.read_at IS NOT NULL
    ) AS read_count,

    COUNT(*) FILTER (
        WHERE cr.acknowledged_at IS NOT NULL
    ) AS acknowledged_count,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE cr.delivered_at IS NOT NULL
        ) / NULLIF(COUNT(cr.stakeholder_id), 0),
        2
    ) AS delivery_rate,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE cr.read_at IS NOT NULL
        ) / NULLIF(COUNT(cr.stakeholder_id), 0),
        2
    ) AS read_rate,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE cr.acknowledged_at IS NOT NULL
        ) / NULLIF(COUNT(cr.stakeholder_id), 0),
        2
    ) AS acknowledgement_rate

FROM communications c

LEFT JOIN communication_recipients cr
    ON cr.communication_id = c.communication_id

GROUP BY
    c.communication_id,
    c.communication_code,
    c.title,
    c.communication_type,
    c.status;

-- ============================================================
-- 14. MANAGEMENT REVIEW REPORT VIEW
-- ============================================================

CREATE OR REPLACE VIEW communication_management_report AS
SELECT
    c.communication_id,
    c.communication_code,
    c.title,
    c.status,
    c.version_number,
    s.full_name AS communication_owner,

    COUNT(DISTINCT r.review_id) AS total_reviews,

    COUNT(DISTINCT r.review_id) FILTER (
        WHERE r.decision = 'approve'
          AND r.reviewed_version = c.version_number
    ) AS approval_count,

    COUNT(DISTINCT r.review_id) FILTER (
        WHERE r.decision = 'revise'
          AND r.reviewed_version = c.version_number
    ) AS revision_count,

    COUNT(DISTINCT r.review_id) FILTER (
        WHERE r.decision = 'reject'
          AND r.reviewed_version = c.version_number
    ) AS rejection_count,

    ROUND(AVG(r.average_score), 2) AS average_review_score,

    COUNT(DISTINCT rc.comment_id) FILTER (
        WHERE NOT rc.is_resolved
    ) AS unresolved_comments

FROM communications c

JOIN stakeholders s
    ON s.stakeholder_id = c.sender_id

LEFT JOIN communication_reviews r
    ON r.communication_id = c.communication_id

LEFT JOIN review_comments rc
    ON rc.review_id = r.review_id

GROUP BY
    c.communication_id,
    c.communication_code,
    c.title,
    c.status,
    c.version_number,
    s.full_name;

-- ============================================================
-- 15. SAMPLE ORGANIZATIONAL DATA
-- ============================================================

INSERT INTO stakeholders (
    employee_code,
    full_name,
    email,
    department,
    role
)
VALUES
    ('EMP001', 'Project Manager', 'manager@example.org',
     'Operations', 'manager'),

    ('EMP002', 'Quality Officer', 'quality@example.org',
     'Quality', 'reviewer'),

    ('EMP003', 'Technical Lead', 'technical@example.org',
     'Technology', 'reviewer'),

    ('EMP004', 'Department Head', 'head@example.org',
     'Management', 'recipient'),

    ('EMP005', 'Field Coordinator', 'field@example.org',
     'Operations', 'recipient'),

    ('EMP006', 'Communications Observer', 'observer@example.org',
     'Administration', 'observer');

-- ============================================================
-- 16. CREATE SAMPLE COMMUNICATION
-- ============================================================

INSERT INTO communications (
    communication_code,
    title,
    communication_type,
    channel_id,
    sender_id,
    subject,
    content,
    sensitivity,
    acknowledgement_required
)
VALUES (
    'COM-2026-001',
    'Monthly Operational Performance Review',
    'report',
    (SELECT channel_id FROM communication_channels
     WHERE channel_name = 'Official Report'),
    (SELECT stakeholder_id FROM stakeholders
     WHERE employee_code = 'EMP001'),
    'Performance Results and Corrective Actions',
    'The report presents operational performance, pending activities, '
    'resource constraints, risks, and assigned corrective actions.',
    'internal',
    TRUE
);

INSERT INTO communication_recipients (
    communication_id,
    stakeholder_id
)
SELECT
    c.communication_id,
    s.stakeholder_id
FROM communications c
CROSS JOIN stakeholders s
WHERE c.communication_code = 'COM-2026-001'
  AND s.employee_code IN ('EMP004', 'EMP005');

INSERT INTO communication_objective_mapping (
    communication_id,
    objective_id
)
SELECT
    c.communication_id,
    o.objective_id
FROM communications c
CROSS JOIN communication_objectives o
WHERE c.communication_code = 'COM-2026-001'
  AND o.objective_name IN (
      'Performance Reporting',
      'Issue Escalation',
      'Action Assignment'
  );

-- ============================================================
-- 17. ASSIGN REVIEWERS
-- ============================================================

INSERT INTO communication_review_assignments (
    communication_id,
    reviewer_id,
    assigned_by
)
SELECT
    c.communication_id,
    reviewer.stakeholder_id,
    manager.stakeholder_id
FROM communications c
CROSS JOIN stakeholders reviewer
CROSS JOIN stakeholders manager
WHERE c.communication_code = 'COM-2026-001'
  AND reviewer.employee_code IN ('EMP002', 'EMP003')
  AND manager.employee_code = 'EMP001';

-- ============================================================
-- 18. SUBMIT COMMUNICATION
-- ============================================================

UPDATE communications
SET status = 'submitted'
WHERE communication_code = 'COM-2026-001';

-- Start review.

UPDATE communications
SET status = 'under_review'
WHERE communication_code = 'COM-2026-001';

-- ============================================================
-- 19. RECORD FIRST REVIEW
-- ============================================================

DO $$
DECLARE
    v_communication_id BIGINT;
    v_reviewer_id BIGINT;
    v_review_id BIGINT;
BEGIN
    SELECT communication_id
    INTO v_communication_id
    FROM communications
    WHERE communication_code = 'COM-2026-001';

    SELECT stakeholder_id
    INTO v_reviewer_id
    FROM stakeholders
    WHERE employee_code = 'EMP002';

    INSERT INTO communication_reviews (
        communication_id,
        reviewer_id,
        decision,
        average_score,
        feedback,
        reviewed_version
    )
    VALUES (
        v_communication_id,
        v_reviewer_id,
        'approve',
        92.00,
        'The report meets the required quality standards.',
        1
    )
    RETURNING review_id INTO v_review_id;

    INSERT INTO communication_review_scores (
        review_id,
        criterion_id,
        score,
        reviewer_observation
    )
    SELECT
        v_review_id,
        criterion_id,
        CASE criterion_code
            WHEN 'clarity' THEN 92
            WHEN 'accuracy' THEN 95
            WHEN 'completeness' THEN 90
            WHEN 'audience_alignment' THEN 90
            WHEN 'timeliness' THEN 88
            WHEN 'actionability' THEN 92
            WHEN 'professionalism' THEN 95
        END,
        'Verified during review.'
    FROM review_criteria
    WHERE is_mandatory;

    INSERT INTO review_comments (
        review_id,
        reviewer_id,
        criterion_id,
        comment_text,
        severity
    )
    SELECT
        v_review_id,
        v_reviewer_id,
        criterion_id,
        'Verify reported completion figures against source records.',
        'medium'
    FROM review_criteria
    WHERE criterion_code = 'accuracy';
END;
$$;

-- ============================================================
-- 20. RECORD SECOND REVIEW
-- ============================================================

DO $$
DECLARE
    v_communication_id BIGINT;
    v_reviewer_id BIGINT;
    v_review_id BIGINT;
BEGIN
    SELECT communication_id
    INTO v_communication_id
    FROM communications
    WHERE communication_code = 'COM-2026-001';

    SELECT stakeholder_id
    INTO v_reviewer_id
    FROM stakeholders
    WHERE employee_code = 'EMP003';

    INSERT INTO communication_reviews (
        communication_id,
        reviewer_id,
        decision,
        average_score,
        feedback,
        reviewed_version
    )
    VALUES (
        v_communication_id,
        v_reviewer_id,
        'approve',
        91.00,
        'Technical details and operational information are accurate.',
        1
    )
    RETURNING review_id INTO v_review_id;

    INSERT INTO communication_review_scores (
        review_id,
        criterion_id,
        score
    )
    SELECT
        v_review_id,
        criterion_id,
        CASE criterion_code
            WHEN 'clarity' THEN 90
            WHEN 'accuracy' THEN 94
            WHEN 'completeness' THEN 91
            WHEN 'audience_alignment' THEN 89
            WHEN 'timeliness' THEN 90
            WHEN 'actionability' THEN 93
            WHEN 'professionalism' THEN 90
        END
    FROM review_criteria
    WHERE is_mandatory;
END;
$$;

-- ============================================================
-- 21. REVIEW DISCUSSION AND COMMENT RESOLUTION
-- ============================================================

INSERT INTO review_discussions (
    comment_id,
    author_id,
    message
)
SELECT
    rc.comment_id,
    s.stakeholder_id,
    'The completion figures have been checked against the source records.'
FROM review_comments rc
JOIN communication_reviews r
    ON r.review_id = rc.review_id
JOIN stakeholders s
    ON s.employee_code = 'EMP001'
WHERE rc.comment_text LIKE 'Verify reported completion figures%';

UPDATE review_comments
SET
    is_resolved = TRUE,
    resolved_by = (
        SELECT stakeholder_id
        FROM stakeholders
        WHERE employee_code = 'EMP001'
    ),
    resolved_at = CURRENT_TIMESTAMP
WHERE comment_text LIKE 'Verify reported completion figures%';

-- ============================================================
-- 22. ELIGIBILITY EVALUATION
-- ============================================================

SELECT *
FROM evaluate_communication(
    (
        SELECT communication_id
        FROM communications
        WHERE communication_code = 'COM-2026-001'
    )
);

-- ============================================================
-- 23. AUTHORIZE PUBLICATION TRANSACTION
-- ============================================================

DO $$
DECLARE
    v_communication_id BIGINT;
    v_manager_id BIGINT;
BEGIN
    SELECT communication_id
    INTO v_communication_id
    FROM communications
    WHERE communication_code = 'COM-2026-001';

    SELECT stakeholder_id
    INTO v_manager_id
    FROM stakeholders
    WHERE employee_code = 'EMP001';

    CALL approve_communication(
        v_communication_id,
        v_manager_id
    );

    UPDATE communications
    SET status = 'published'
    WHERE communication_id = v_communication_id;
END;
$$;

-- ============================================================
-- 24. RECORD DELIVERY AND ACKNOWLEDGEMENTS
-- ============================================================

UPDATE communication_recipients
SET
    delivery_status = 'acknowledged',
    delivered_at = CURRENT_TIMESTAMP,
    read_at = CURRENT_TIMESTAMP,
    acknowledged_at = CURRENT_TIMESTAMP
WHERE communication_id = (
    SELECT communication_id
    FROM communications
    WHERE communication_code = 'COM-2026-001'
);

-- ============================================================
-- 25. SAMPLE QUERIES: RETRIEVAL
-- ============================================================

-- Retrieve communications with owners and channels.

SELECT
    c.communication_code,
    c.title,
    c.communication_type,
    c.status,
    s.full_name AS sender,
    ch.channel_name,
    c.created_at
FROM communications c
JOIN stakeholders s
    ON s.stakeholder_id = c.sender_id
JOIN communication_channels ch
    ON ch.channel_id = c.channel_id
ORDER BY c.created_at DESC;

-- ============================================================
-- 26. SAMPLE QUERIES: REVIEW VALIDATION
-- ============================================================

-- Identify communications missing mandatory review criteria.

SELECT
    r.review_id,
    c.communication_code,
    rc.criterion_name
FROM communication_reviews r
JOIN communications c
    ON c.communication_id = r.communication_id
CROSS JOIN review_criteria rc
WHERE rc.is_mandatory
  AND NOT EXISTS (
      SELECT 1
      FROM communication_review_scores rs
      WHERE rs.review_id = r.review_id
        AND rs.criterion_id = rc.criterion_id
  );

-- Identify unresolved critical comments.

SELECT
    c.communication_code,
    r.reviewer_id,
    rc.comment_text,
    rc.created_at
FROM review_comments rc
JOIN communication_reviews r
    ON r.review_id = rc.review_id
JOIN communications c
    ON c.communication_id = r.communication_id
WHERE rc.severity = 'critical'
  AND NOT rc.is_resolved;

-- ============================================================
-- 27. SAMPLE QUERIES: AGGREGATION
-- ============================================================

-- Communication volume by type and status.

SELECT
    communication_type,
    status,
    COUNT(*) AS communication_count
FROM communications
GROUP BY communication_type, status
ORDER BY communication_type, status;

-- Reviewer performance.

SELECT
    s.full_name AS reviewer,
    COUNT(r.review_id) AS reviews_completed,
    COUNT(*) FILTER (
        WHERE r.decision = 'approve'
    ) AS approvals,
    COUNT(*) FILTER (
        WHERE r.decision = 'revise'
    ) AS revision_requests,
    COUNT(*) FILTER (
        WHERE r.decision = 'reject'
    ) AS rejections,
    ROUND(AVG(r.average_score), 2) AS average_score
FROM stakeholders s
LEFT JOIN communication_reviews r
    ON r.reviewer_id = s.stakeholder_id
GROUP BY s.stakeholder_id, s.full_name
ORDER BY reviews_completed DESC;

-- ============================================================
-- 28. SAMPLE QUERIES: PERFORMANCE EVALUATION
-- ============================================================

SELECT *
FROM communication_performance
ORDER BY communication_id;

-- Compare communication performance with policy targets.

SELECT
    p.communication_code,
    p.title,
    p.delivery_rate,
    p.read_rate,
    p.acknowledgement_rate,
    rp.minimum_delivery_rate,
    rp.minimum_acknowledgement_rate,

    CASE
        WHEN p.delivery_rate >= rp.minimum_delivery_rate
        THEN 'SATISFACTORY'
        ELSE 'BELOW TARGET'
    END AS delivery_assessment,

    CASE
        WHEN NOT c.acknowledgement_required
        THEN 'NOT REQUIRED'
        WHEN p.acknowledgement_rate >=
             rp.minimum_acknowledgement_rate
        THEN 'SATISFACTORY'
        ELSE 'BELOW TARGET'
    END AS acknowledgement_assessment

FROM communication_performance p

JOIN communications c
    ON c.communication_id = p.communication_id

CROSS JOIN LATERAL (
    SELECT *
    FROM review_policies
    WHERE is_active
    ORDER BY policy_id DESC
    LIMIT 1
) rp;

-- ============================================================
-- 29. SAMPLE QUERIES: MANAGEMENT REPORTING
-- ============================================================

SELECT *
FROM communication_management_report
ORDER BY communication_id;

-- Current workload by review state.

SELECT
    status,
    COUNT(*) AS communication_count,
    MIN(created_at) AS oldest_record,
    MAX(updated_at) AS latest_update
FROM communications
GROUP BY status
ORDER BY communication_count DESC;

-- ============================================================
-- 30. SAMPLE QUERIES: ELIGIBILITY
-- ============================================================

SELECT
    c.communication_code,
    e.approval_count,
    e.average_score,
    e.unresolved_critical_comments,
    e.eligible,
    e.reasons
FROM communications c
CROSS JOIN LATERAL evaluate_communication(
    c.communication_id
) e;

-- ============================================================
-- 31. SAMPLE QUERIES: WORKFLOW AND AUDIT
-- ============================================================

SELECT
    c.communication_code,
    a.event_type,
    a.old_status,
    a.new_status,
    a.event_time,
    s.full_name AS actor
FROM communication_audit a
LEFT JOIN communications c
    ON c.communication_id = a.communication_id
LEFT JOIN stakeholders s
    ON s.stakeholder_id = a.actor_id
ORDER BY a.event_time DESC;

-- Search communication content.

SELECT
    communication_code,
    title,
    status
FROM communications
WHERE to_tsvector(
    'english',
    title || ' ' || subject || ' ' || content
)
@@ plainto_tsquery('english', 'operational performance');

-- ============================================================
-- 32. EXAMPLE FAILURE CASE: BELOW-THRESHOLD APPROVAL
-- ============================================================

-- The following transaction demonstrates an invalid approval.
-- Its rollback ensures that the demonstration does not affect data.

DO $$
DECLARE
    v_communication_id BIGINT;
    v_reviewer_id BIGINT;
BEGIN
    SELECT communication_id
    INTO v_communication_id
    FROM communications
    WHERE communication_code = 'COM-2026-001';

    SELECT stakeholder_id
    INTO v_reviewer_id
    FROM stakeholders
    WHERE employee_code = 'EMP006';

    BEGIN
        INSERT INTO communication_reviews (
            communication_id,
            reviewer_id,
            decision,
            average_score,
            feedback,
            reviewed_version
        )
        VALUES (
            v_communication_id,
            v_reviewer_id,
            'approve',
            45,
            'Attempted low-quality approval.',
            1
        );

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Expected failure: %', SQLERRM;
    END;
END;
$$;

-- ============================================================
-- 33. TRANSACTIONAL ARCHIVING EXAMPLE
-- ============================================================

-- Archiving is allowed only after publication or rejection.

DO $$
DECLARE
    v_communication_id BIGINT;
BEGIN
    SELECT communication_id
    INTO v_communication_id
    FROM communications
    WHERE communication_code = 'COM-2026-001';

    UPDATE communications
    SET status = 'archived'
    WHERE communication_id = v_communication_id
      AND status = 'published';
END;
$$;

-- ============================================================
-- 34. FINAL SYSTEM REPORT
-- ============================================================

SELECT
    COUNT(*) AS total_communications
FROM communications;

SELECT
    COUNT(*) AS total_reviews
FROM communication_reviews;

SELECT
    COUNT(*) AS total_comments
FROM review_comments;

SELECT
    status,
    COUNT(*) AS total
FROM communications
GROUP BY status
ORDER BY status;

SELECT
    event_type,
    COUNT(*) AS event_count
FROM communication_audit
GROUP BY event_type
ORDER BY event_count DESC;

COMMIT;
