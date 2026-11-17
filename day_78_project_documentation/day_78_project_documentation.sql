-- ============================================================
-- PROJECT DOCUMENTATION MANAGEMENT SYSTEM
-- PostgreSQL 15+
--
-- Relational document management, version control,
-- review workflows, approval policies, access control,
-- integrity checks, retention and audit reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS project_docs;

SET search_path TO project_docs, public;

-- ============================================================
-- 1. ENUMERATED DOMAIN TYPES
-- ============================================================

CREATE TYPE document_type AS ENUM (
    'requirements',
    'project_plan',
    'technical_specification',
    'design',
    'meeting_minutes',
    'progress_report',
    'risk_register',
    'test_report',
    'user_guide',
    'closure_report'
);

CREATE TYPE document_status AS ENUM (
    'draft',
    'under_review',
    'approved',
    'rejected',
    'archived'
);

CREATE TYPE user_role AS ENUM (
    'admin',
    'project_manager',
    'author',
    'reviewer',
    'viewer'
);

CREATE TYPE review_decision AS ENUM (
    'approved',
    'rejected',
    'changes_requested'
);

CREATE TYPE permission_type AS ENUM (
    'read',
    'write',
    'review',
    'manage'
);

-- ============================================================
-- 2. USERS
-- ============================================================

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    full_name VARCHAR(200) NOT NULL,

    email VARCHAR(254) NOT NULL UNIQUE,

    role user_role NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_user_name
        CHECK (length(trim(full_name)) > 0),

    CONSTRAINT valid_user_email
        CHECK (
            email ~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
        )
);

-- ============================================================
-- 3. PROJECTS
-- ============================================================

CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    project_name VARCHAR(200) NOT NULL,

    description TEXT,

    manager_id UUID NOT NULL REFERENCES users(user_id),

    project_status VARCHAR(30) NOT NULL DEFAULT 'active',

    start_date DATE,

    end_date DATE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_project_name
        CHECK (length(trim(project_name)) > 0),

    CONSTRAINT valid_project_status
        CHECK (
            project_status IN (
                'planning',
                'active',
                'on_hold',
                'completed',
                'cancelled'
            )
        ),

    CONSTRAINT valid_project_dates
        CHECK (
            end_date IS NULL
            OR start_date IS NULL
            OR end_date >= start_date
        )
);

-- ============================================================
-- 4. PROJECT MEMBERSHIP
-- ============================================================

CREATE TABLE project_members (
    project_id UUID NOT NULL
        REFERENCES projects(project_id) ON DELETE CASCADE,

    user_id UUID NOT NULL
        REFERENCES users(user_id),

    project_role VARCHAR(30) NOT NULL,

    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (project_id, user_id),

    CONSTRAINT valid_project_role
        CHECK (
            project_role IN (
                'manager',
                'author',
                'reviewer',
                'viewer'
            )
        )
);

-- ============================================================
-- 5. DOCUMENTS
-- ============================================================

CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    project_id UUID NOT NULL
        REFERENCES projects(project_id),

    title VARCHAR(200) NOT NULL,

    document_type document_type NOT NULL,

    owner_id UUID NOT NULL REFERENCES users(user_id),

    current_version INTEGER NOT NULL DEFAULT 1,

    status document_status NOT NULL DEFAULT 'draft',

    description TEXT,

    retention_until DATE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_document_title
        CHECK (length(trim(title)) > 0),

    CONSTRAINT positive_current_version
        CHECK (current_version >= 1)
);

-- ============================================================
-- 6. DOCUMENT VERSIONS
-- ============================================================

CREATE TABLE document_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    document_id UUID NOT NULL
        REFERENCES documents(document_id),

    version_number INTEGER NOT NULL,

    content TEXT NOT NULL,

    checksum CHAR(64) NOT NULL,

    author_id UUID NOT NULL REFERENCES users(user_id),

    change_description TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_document_version
        UNIQUE (document_id, version_number),

    CONSTRAINT positive_version_number
        CHECK (version_number > 0),

    CONSTRAINT valid_version_content
        CHECK (length(trim(content)) > 0),

    CONSTRAINT valid_checksum
        CHECK (checksum ~ '^[a-f0-9]{64}$')
);

-- The document's current version must exist.
ALTER TABLE documents
ADD CONSTRAINT current_version_reference
FOREIGN KEY (document_id, current_version)
REFERENCES document_versions(document_id, version_number)
DEFERRABLE INITIALLY DEFERRED;

-- ============================================================
-- 7. DOCUMENT TAGS
-- ============================================================

CREATE TABLE document_tags (
    document_id UUID NOT NULL
        REFERENCES documents(document_id) ON DELETE CASCADE,

    tag VARCHAR(100) NOT NULL,

    PRIMARY KEY (document_id, tag),

    CONSTRAINT valid_tag
        CHECK (length(trim(tag)) > 0)
);

-- ============================================================
-- 8. DOCUMENT ACCESS CONTROL
-- ============================================================

CREATE TABLE document_permissions (
    permission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    document_id UUID NOT NULL
        REFERENCES documents(document_id) ON DELETE CASCADE,

    user_id UUID NOT NULL REFERENCES users(user_id),

    permission permission_type NOT NULL,

    granted_by UUID NOT NULL REFERENCES users(user_id),

    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (document_id, user_id, permission)
);

-- ============================================================
-- 9. REVIEW POLICIES
-- ============================================================

CREATE TABLE approval_requirements (
    requirement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    project_id UUID NOT NULL
        REFERENCES projects(project_id) ON DELETE CASCADE,

    document_type document_type NOT NULL,

    required_approvals INTEGER NOT NULL DEFAULT 1,

    prohibit_self_approval BOOLEAN NOT NULL DEFAULT TRUE,

    require_distinct_reviewers BOOLEAN NOT NULL DEFAULT TRUE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (project_id, document_type),

    CONSTRAINT valid_approval_count
        CHECK (required_approvals >= 1)
);

-- ============================================================
-- 10. DOCUMENT REVIEWS
-- ============================================================

CREATE TABLE document_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    document_id UUID NOT NULL
        REFERENCES documents(document_id),

    version_number INTEGER NOT NULL,

    reviewer_id UUID NOT NULL REFERENCES users(user_id),

    decision review_decision NOT NULL,

    comments TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT review_version_reference
        FOREIGN KEY (document_id, version_number)
        REFERENCES document_versions(document_id, version_number),

    CONSTRAINT valid_review_comments
        CHECK (length(trim(comments)) > 0),

    CONSTRAINT unique_reviewer_per_version
        UNIQUE (document_id, version_number, reviewer_id)
);

-- ============================================================
-- 11. REVIEW COMMENTS AND DISCUSSIONS
-- ============================================================

CREATE TABLE review_comments (
    comment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    review_id UUID NOT NULL
        REFERENCES document_reviews(review_id) ON DELETE CASCADE,

    author_id UUID NOT NULL REFERENCES users(user_id),

    parent_comment_id UUID
        REFERENCES review_comments(comment_id),

    section_reference VARCHAR(200),

    comment_text TEXT NOT NULL,

    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,

    resolved_by UUID REFERENCES users(user_id),

    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_comment
        CHECK (length(trim(comment_text)) > 0),

    CONSTRAINT valid_resolution_state
        CHECK (
            (is_resolved = FALSE AND resolved_at IS NULL AND resolved_by IS NULL)
            OR
            (is_resolved = TRUE AND resolved_at IS NOT NULL AND resolved_by IS NOT NULL)
        )
);

-- ============================================================
-- 12. AUTOMATED STATUS CHECKS
-- ============================================================

CREATE TABLE document_status_checks (
    check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    document_id UUID NOT NULL
        REFERENCES documents(document_id),

    version_number INTEGER NOT NULL,

    check_name VARCHAR(150) NOT NULL,

    passed BOOLEAN NOT NULL,

    details TEXT,

    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT status_check_version_reference
        FOREIGN KEY (document_id, version_number)
        REFERENCES document_versions(document_id, version_number),

    CONSTRAINT valid_check_name
        CHECK (length(trim(check_name)) > 0)
);

-- ============================================================
-- 13. AUDIT LOG
-- ============================================================

CREATE TABLE document_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    document_id UUID NOT NULL
        REFERENCES documents(document_id),

    actor_id UUID NOT NULL REFERENCES users(user_id),

    action VARCHAR(100) NOT NULL,

    details JSONB NOT NULL DEFAULT '{}'::jsonb,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 14. INDEXES
-- ============================================================

CREATE INDEX idx_documents_project
    ON documents(project_id);

CREATE INDEX idx_documents_status
    ON documents(status);

CREATE INDEX idx_documents_type
    ON documents(document_type);

CREATE INDEX idx_documents_owner
    ON documents(owner_id);

CREATE INDEX idx_documents_updated
    ON documents(updated_at DESC);

CREATE INDEX idx_versions_document
    ON document_versions(document_id, version_number DESC);

CREATE INDEX idx_reviews_document
    ON document_reviews(document_id, version_number);

CREATE INDEX idx_reviews_reviewer
    ON document_reviews(reviewer_id);

CREATE INDEX idx_comments_review
    ON review_comments(review_id);

CREATE INDEX idx_status_checks_document
    ON document_status_checks(document_id, version_number);

CREATE INDEX idx_audit_document_time
    ON document_audit(document_id, occurred_at DESC);

CREATE INDEX idx_audit_details
    ON document_audit USING GIN(details);

CREATE INDEX idx_document_tags_tag
    ON document_tags(tag);

-- ============================================================
-- 15. DOCUMENT STATE VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_document_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;

    IF OLD.status = 'draft'
       AND NEW.status IN ('under_review', 'archived') THEN
        RETURN NEW;
    END IF;

    IF OLD.status = 'under_review'
       AND NEW.status IN ('draft', 'approved', 'rejected') THEN
        RETURN NEW;
    END IF;

    IF OLD.status IN ('approved', 'rejected')
       AND NEW.status IN ('draft', 'archived') THEN
        RETURN NEW;
    END IF;

    RAISE EXCEPTION
        'Invalid document status transition: % -> %',
        OLD.status,
        NEW.status;

END;
$$;

CREATE TRIGGER trg_validate_document_transition
BEFORE UPDATE OF status ON documents
FOR EACH ROW
EXECUTE FUNCTION validate_document_transition();

-- ============================================================
-- 16. AUTOMATIC DOCUMENT TIMESTAMP
-- ============================================================

CREATE OR REPLACE FUNCTION update_document_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    NEW.updated_at = NOW();

    RETURN NEW;

END;
$$;

CREATE TRIGGER trg_document_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION update_document_timestamp();

-- ============================================================
-- 17. AUDIT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION audit_document_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_actor UUID;
    v_action TEXT;
    v_document UUID;
    v_details JSONB;
BEGIN

    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION
            'Document deletion is disabled. Archive documents instead.';
    END IF;

    v_document := NEW.document_id;

    IF TG_OP = 'INSERT' THEN

        v_actor := NEW.owner_id;
        v_action := 'DOCUMENT_CREATED';

        v_details := jsonb_build_object(
            'title', NEW.title,
            'status', NEW.status,
            'version', NEW.current_version
        );

    ELSE

        v_actor := COALESCE(
            NULLIF(current_setting('app.actor_id', TRUE), '')::UUID,
            NEW.owner_id
        );

        v_action := 'DOCUMENT_UPDATED';

        v_details := jsonb_build_object(
            'old_status', OLD.status,
            'new_status', NEW.status,
            'old_version', OLD.current_version,
            'new_version', NEW.current_version
        );

    END IF;

    INSERT INTO document_audit (
        document_id,
        actor_id,
        action,
        details
    )
    VALUES (
        v_document,
        v_actor,
        v_action,
        v_details
    );

    RETURN NEW;

END;
$$;

CREATE TRIGGER trg_document_audit
AFTER INSERT OR UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION audit_document_changes();

-- ============================================================
-- 18. PREVENT MODIFICATION OF HISTORICAL VERSIONS
-- ============================================================

CREATE OR REPLACE FUNCTION prevent_version_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    RAISE EXCEPTION
        'Document versions are immutable. Create a new version.';

END;
$$;

CREATE TRIGGER trg_immutable_versions
BEFORE UPDATE OR DELETE ON document_versions
FOR EACH ROW
EXECUTE FUNCTION prevent_version_mutation();

-- ============================================================
-- 19. DOCUMENT CREATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION create_document(
    p_project_id UUID,
    p_title VARCHAR,
    p_type document_type,
    p_owner_id UUID,
    p_content TEXT,
    p_checksum CHAR(64),
    p_description TEXT
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_document_id UUID;
BEGIN

    IF NOT EXISTS (
        SELECT 1
        FROM projects
        WHERE project_id = p_project_id
    ) THEN
        RAISE EXCEPTION 'Project does not exist.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM users
        WHERE user_id = p_owner_id
          AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'Document owner is invalid.';
    END IF;

    IF length(trim(p_title)) = 0
       OR length(trim(p_content)) = 0 THEN
        RAISE EXCEPTION 'Document title and content are required.';
    END IF;

    IF p_checksum !~ '^[a-f0-9]{64}$' THEN
        RAISE EXCEPTION 'Invalid SHA-256 checksum.';
    END IF;

    INSERT INTO documents (
        project_id,
        title,
        document_type,
        owner_id,
        current_version,
        status
    )
    VALUES (
        p_project_id,
        p_title,
        p_type,
        p_owner_id,
        1,
        'draft'
    )
    RETURNING document_id INTO v_document_id;

    INSERT INTO document_versions (
        document_id,
        version_number,
        content,
        checksum,
        author_id,
        change_description
    )
    VALUES (
        v_document_id,
        1,
        p_content,
        p_checksum,
        p_owner_id,
        COALESCE(p_description, 'Initial creation')
    );

    RETURN v_document_id;

END;
$$;

-- ============================================================
-- 20. DOCUMENT VERSION CREATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION create_document_version(
    p_document_id UUID,
    p_actor_id UUID,
    p_expected_version INTEGER,
    p_content TEXT,
    p_checksum CHAR(64),
    p_description TEXT
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_document documents%ROWTYPE;
    v_next_version INTEGER;
    v_actor_role user_role;
BEGIN

    SELECT *
    INTO v_document
    FROM documents
    WHERE document_id = p_document_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Document not found.';
    END IF;

    SELECT role
    INTO v_actor_role
    FROM users
    WHERE user_id = p_actor_id
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Inactive or unknown user.';
    END IF;

    IF v_actor_role NOT IN (
        'admin',
        'project_manager',
        'author'
    ) THEN
        RAISE EXCEPTION 'User cannot create document versions.';
    END IF;

    IF v_actor_role = 'author'
       AND v_document.owner_id <> p_actor_id THEN
        RAISE EXCEPTION 'Authors cannot modify another owner document.';
    END IF;

    IF v_document.status = 'archived' THEN
        RAISE EXCEPTION 'Archived documents cannot be modified.';
    END IF;

    IF v_document.current_version <> p_expected_version THEN
        RAISE EXCEPTION
            'Version conflict. Expected %, actual %.',
            p_expected_version,
            v_document.current_version;
    END IF;

    IF length(trim(p_content)) = 0 THEN
        RAISE EXCEPTION 'Content cannot be empty.';
    END IF;

    IF p_checksum !~ '^[a-f0-9]{64}$' THEN
        RAISE EXCEPTION 'Invalid checksum.';
    END IF;

    v_next_version := v_document.current_version + 1;

    INSERT INTO document_versions (
        document_id,
        version_number,
        content,
        checksum,
        author_id,
        change_description
    )
    VALUES (
        p_document_id,
        v_next_version,
        p_content,
        p_checksum,
        p_actor_id,
        p_description
    );

    UPDATE documents
    SET current_version = v_next_version,
        status = CASE
            WHEN status IN (
                'approved',
                'rejected',
                'under_review'
            ) THEN 'draft'
            ELSE status
        END
    WHERE document_id = p_document_id;

    RETURN v_next_version;

END;
$$;

-- ============================================================
-- 21. REVIEW SUBMISSION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE submit_document_for_review(
    p_document_id UUID,
    p_actor_id UUID
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_document documents%ROWTYPE;
    v_role user_role;
BEGIN

    SELECT *
    INTO v_document
    FROM documents
    WHERE document_id = p_document_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Document not found.';
    END IF;

    SELECT role
    INTO v_role
    FROM users
    WHERE user_id = p_actor_id
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found or inactive.';
    END IF;

    IF v_document.owner_id <> p_actor_id
       AND v_role NOT IN ('admin', 'project_manager') THEN
        RAISE EXCEPTION 'Not authorized to submit document.';
    END IF;

    IF v_document.status <> 'draft' THEN
        RAISE EXCEPTION 'Only draft documents can be submitted.';
    END IF;

    PERFORM set_config(
        'app.actor_id',
        p_actor_id::TEXT,
        TRUE
    );

    UPDATE documents
    SET status = 'under_review'
    WHERE document_id = p_document_id;

END;
$$;

-- ============================================================
-- 22. REVIEW DECISION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION record_document_review(
    p_document_id UUID,
    p_reviewer_id UUID,
    p_decision review_decision,
    p_comments TEXT
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_document documents%ROWTYPE;
    v_role user_role;
    v_review_id UUID;
    v_new_status document_status;
BEGIN

    SELECT *
    INTO v_document
    FROM documents
    WHERE document_id = p_document_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Document not found.';
    END IF;

    SELECT role
    INTO v_role
    FROM users
    WHERE user_id = p_reviewer_id
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Reviewer is invalid or inactive.';
    END IF;

    IF v_role NOT IN (
        'admin',
        'project_manager',
        'reviewer'
    ) THEN
        RAISE EXCEPTION 'User is not eligible to review documents.';
    END IF;

    IF v_document.owner_id = p_reviewer_id THEN
        RAISE EXCEPTION 'Self-approval is prohibited.';
    END IF;

    IF v_document.status <> 'under_review' THEN
        RAISE EXCEPTION 'Document is not under review.';
    END IF;

    IF length(trim(p_comments)) = 0 THEN
        RAISE EXCEPTION 'Review comments are required.';
    END IF;

    INSERT INTO document_reviews (
        document_id,
        version_number,
        reviewer_id,
        decision,
        comments
    )
    VALUES (
        p_document_id,
        v_document.current_version,
        p_reviewer_id,
        p_decision,
        p_comments
    )
    RETURNING review_id INTO v_review_id;

    v_new_status := CASE p_decision
        WHEN 'approved' THEN 'approved'
        WHEN 'rejected' THEN 'rejected'
        WHEN 'changes_requested' THEN 'draft'
    END;

    PERFORM set_config(
        'app.actor_id',
        p_reviewer_id::TEXT,
        TRUE
    );

    UPDATE documents
    SET status = v_new_status
    WHERE document_id = p_document_id;

    RETURN v_review_id;

END;
$$;

-- ============================================================
-- 23. APPROVAL ELIGIBILITY FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION check_approval_eligibility(
    p_document_id UUID
)
RETURNS TABLE (
    document_id UUID,
    current_version INTEGER,
    required_approvals INTEGER,
    actual_approvals BIGINT,
    approval_eligible BOOLEAN
)
LANGUAGE sql
STABLE
AS $$
    WITH current_document AS (
        SELECT
            d.document_id,
            d.project_id,
            d.document_type,
            d.current_version
        FROM documents d
        WHERE d.document_id = p_document_id
    ),
    policy AS (
        SELECT
            cd.document_id,
            cd.current_version,
            COALESCE(
                ar.required_approvals,
                1
            ) AS required_approvals
        FROM current_document cd
        LEFT JOIN approval_requirements ar
            ON ar.project_id = cd.project_id
           AND ar.document_type = cd.document_type
           AND ar.active = TRUE
    ),
    approvals AS (
        SELECT
            r.document_id,
            COUNT(DISTINCT r.reviewer_id) AS actual_approvals
        FROM document_reviews r
        JOIN current_document cd
            ON cd.document_id = r.document_id
           AND cd.current_version = r.version_number
        WHERE r.decision = 'approved'
        GROUP BY r.document_id
    )
    SELECT
        p.document_id,
        p.current_version,
        p.required_approvals,
        COALESCE(a.actual_approvals, 0),
        COALESCE(a.actual_approvals, 0) >= p.required_approvals
    FROM policy p
    LEFT JOIN approvals a
        ON a.document_id = p.document_id;
$$;

-- ============================================================
-- 24. MERGE-LIKE DOCUMENT PUBLICATION ELIGIBILITY
-- ============================================================

CREATE OR REPLACE FUNCTION check_publication_eligibility(
    p_document_id UUID
)
RETURNS TABLE (
    document_id UUID,
    current_status document_status,
    approvals_satisfied BOOLEAN,
    checks_passed BOOLEAN,
    conversations_resolved BOOLEAN,
    eligible BOOLEAN
)
LANGUAGE sql
STABLE
AS $$
    WITH current_document AS (
        SELECT *
        FROM documents
        WHERE documents.document_id = p_document_id
    ),
    approval_state AS (
        SELECT *
        FROM check_approval_eligibility(p_document_id)
    ),
    check_state AS (
        SELECT
            cd.document_id,
            COUNT(sc.check_id) > 0
                AND BOOL_AND(sc.passed) AS checks_passed
        FROM current_document cd
        LEFT JOIN document_status_checks sc
            ON sc.document_id = cd.document_id
           AND sc.version_number = cd.current_version
        GROUP BY cd.document_id
    ),
    discussion_state AS (
        SELECT
            cd.document_id,
            NOT EXISTS (
                SELECT 1
                FROM review_comments rc
                JOIN document_reviews dr
                    ON dr.review_id = rc.review_id
                WHERE dr.document_id = cd.document_id
                  AND dr.version_number = cd.current_version
                  AND rc.is_resolved = FALSE
            ) AS conversations_resolved
        FROM current_document cd
    )
    SELECT
        cd.document_id,
        cd.status,
        COALESCE(a.approval_eligible, FALSE),
        COALESCE(cs.checks_passed, FALSE),
        COALESCE(ds.conversations_resolved, TRUE),
        (
            cd.status = 'approved'
            AND COALESCE(a.approval_eligible, FALSE)
            AND COALESCE(cs.checks_passed, FALSE)
            AND COALESCE(ds.conversations_resolved, TRUE)
        )
    FROM current_document cd
    LEFT JOIN approval_state a
        ON a.document_id = cd.document_id
    LEFT JOIN check_state cs
        ON cs.document_id = cd.document_id
    LEFT JOIN discussion_state ds
        ON ds.document_id = cd.document_id;
$$;

-- ============================================================
-- 25. DOCUMENT ARCHIVING PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE archive_document(
    p_document_id UUID,
    p_actor_id UUID
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_role user_role;
    v_status document_status;
BEGIN

    SELECT role
    INTO v_role
    FROM users
    WHERE user_id = p_actor_id
      AND is_active = TRUE;

    IF v_role NOT IN ('admin', 'project_manager') THEN
        RAISE EXCEPTION 'Archiving permission denied.';
    END IF;

    SELECT status
    INTO v_status
    FROM documents
    WHERE document_id = p_document_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Document not found.';
    END IF;

    IF v_status = 'under_review' THEN
        RAISE EXCEPTION
            'Documents under review cannot be archived.';
    END IF;

    PERFORM set_config(
        'app.actor_id',
        p_actor_id::TEXT,
        TRUE
    );

    UPDATE documents
    SET status = 'archived'
    WHERE document_id = p_document_id;

END;
$$;

-- ============================================================
-- 26. REPORTING VIEW
-- ============================================================

CREATE OR REPLACE VIEW project_documentation_summary AS
SELECT
    p.project_id,
    p.project_name,

    COUNT(d.document_id) AS total_documents,

    COUNT(d.document_id) FILTER (
        WHERE d.status = 'draft'
    ) AS draft_documents,

    COUNT(d.document_id) FILTER (
        WHERE d.status = 'under_review'
    ) AS documents_under_review,

    COUNT(d.document_id) FILTER (
        WHERE d.status = 'approved'
    ) AS approved_documents,

    COUNT(d.document_id) FILTER (
        WHERE d.status = 'rejected'
    ) AS rejected_documents,

    COUNT(d.document_id) FILTER (
        WHERE d.status = 'archived'
    ) AS archived_documents,

    COALESCE(SUM(d.current_version), 0)
        AS total_version_count

FROM projects p

LEFT JOIN documents d
    ON d.project_id = p.project_id

GROUP BY
    p.project_id,
    p.project_name;

-- ============================================================
-- 27. VERSION HISTORY VIEW
-- ============================================================

CREATE OR REPLACE VIEW document_version_history AS
SELECT
    d.document_id,
    d.title,
    d.document_type,
    d.status,
    dv.version_number,
    dv.checksum,
    u.full_name AS author_name,
    dv.change_description,
    dv.created_at

FROM documents d

JOIN document_versions dv
    ON dv.document_id = d.document_id

JOIN users u
    ON u.user_id = dv.author_id;

-- ============================================================
-- 28. RETENTION REPORT VIEW
-- ============================================================

CREATE OR REPLACE VIEW document_retention_report AS
SELECT
    document_id,
    project_id,
    title,
    status,
    retention_until,
    CASE
        WHEN retention_until IS NULL THEN 'not_configured'
        WHEN retention_until < CURRENT_DATE THEN 'expired'
        WHEN retention_until <= CURRENT_DATE + 30 THEN 'expiring_soon'
        ELSE 'within_retention'
    END AS retention_state
FROM documents;

-- ============================================================
-- 29. SAMPLE DATA
-- ============================================================

INSERT INTO users (
    full_name,
    email,
    role
)
VALUES
(
    'System Administrator',
    'admin@example.com',
    'admin'
),
(
    'Project Manager',
    'manager@example.com',
    'project_manager'
),
(
    'Technical Author',
    'author@example.com',
    'author'
),
(
    'Independent Reviewer',
    'reviewer@example.com',
    'reviewer'
),
(
    'Project Observer',
    'viewer@example.com',
    'viewer'
);

INSERT INTO projects (
    project_name,
    description,
    manager_id,
    project_status,
    start_date
)
SELECT
    'Enterprise Documentation Platform',
    'Centralized project document management and governance.',
    user_id,
    'active',
    CURRENT_DATE
FROM users
WHERE email = 'manager@example.com';

INSERT INTO project_members (
    project_id,
    user_id,
    project_role
)
SELECT
    p.project_id,
    u.user_id,
    CASE u.role
        WHEN 'project_manager' THEN 'manager'
        WHEN 'author' THEN 'author'
        WHEN 'reviewer' THEN 'reviewer'
        ELSE 'viewer'
    END
FROM projects p
CROSS JOIN users u
WHERE p.project_name = 'Enterprise Documentation Platform'
AND u.role <> 'admin';

INSERT INTO approval_requirements (
    project_id,
    document_type,
    required_approvals,
    prohibit_self_approval,
    require_distinct_reviewers
)
SELECT
    project_id,
    'requirements',
    1,
    TRUE,
    TRUE
FROM projects
WHERE project_name = 'Enterprise Documentation Platform';

INSERT INTO approval_requirements (
    project_id,
    document_type,
    required_approvals,
    prohibit_self_approval,
    require_distinct_reviewers
)
SELECT
    project_id,
    'technical_specification',
    2,
    TRUE,
    TRUE
FROM projects
WHERE project_name = 'Enterprise Documentation Platform';

-- ============================================================
-- 30. CREATE INITIAL DOCUMENTS
-- ============================================================

DO $$
DECLARE
    v_project UUID;
    v_author UUID;
    v_document UUID;
BEGIN

    SELECT project_id
    INTO v_project
    FROM projects
    WHERE project_name = 'Enterprise Documentation Platform';

    SELECT user_id
    INTO v_author
    FROM users
    WHERE email = 'author@example.com';

    v_document := create_document(
        v_project,
        'System Requirements',
        'requirements',
        v_author,
        'The system must provide secure storage, document versioning, controlled review and project reporting.',
        repeat('a', 64)::CHAR(64),
        'Initial requirements document'
    );

    INSERT INTO document_tags (
        document_id,
        tag
    )
    VALUES
        (v_document, 'requirements'),
        (v_document, 'security'),
        (v_document, 'governance');

    INSERT INTO document_permissions (
        document_id,
        user_id,
        permission,
        granted_by
    )
    SELECT
        v_document,
        user_id,
        'read',
        v_author
    FROM users
    WHERE email = 'viewer@example.com';

END;
$$;

-- ============================================================
-- 31. VERSION UPDATE
-- ============================================================

DO $$
DECLARE
    v_document UUID;
    v_author UUID;
    v_version INTEGER;
BEGIN

    SELECT document_id
    INTO v_document
    FROM documents
    WHERE title = 'System Requirements';

    SELECT user_id
    INTO v_author
    FROM users
    WHERE email = 'author@example.com';

    v_version := create_document_version(
        v_document,
        v_author,
        1,
        'The system must provide secure storage, version history, controlled approval workflows and audit reporting.',
        repeat('b', 64)::CHAR(64),
        'Expanded governance requirements'
    );

    RAISE NOTICE 'Created document version %', v_version;

END;
$$;

-- ============================================================
-- 32. SUBMIT FOR REVIEW
-- ============================================================

DO $$
DECLARE
    v_document UUID;
    v_author UUID;
BEGIN

    SELECT document_id
    INTO v_document
    FROM documents
    WHERE title = 'System Requirements';

    SELECT user_id
    INTO v_author
    FROM users
    WHERE email = 'author@example.com';

    CALL submit_document_for_review(
        v_document,
        v_author
    );

END;
$$;

-- ============================================================
-- 33. REVIEW AND APPROVAL
-- ============================================================

DO $$
DECLARE
    v_document UUID;
    v_reviewer UUID;
BEGIN

    SELECT document_id
    INTO v_document
    FROM documents
    WHERE title = 'System Requirements';

    SELECT user_id
    INTO v_reviewer
    FROM users
    WHERE email = 'reviewer@example.com';

    PERFORM record_document_review(
        v_document,
        v_reviewer,
        'approved',
        'The requirements are complete and suitable for project implementation.'
    );

END;
$$;

-- ============================================================
-- 34. AUTOMATED VALIDATION RESULTS
-- ============================================================

INSERT INTO document_status_checks (
    document_id,
    version_number,
    check_name,
    passed,
    details
)
SELECT
    document_id,
    current_version,
    'content_validation',
    TRUE,
    'Required document content is present.'
FROM documents
WHERE title = 'System Requirements';

INSERT INTO document_status_checks (
    document_id,
    version_number,
    check_name,
    passed,
    details
)
SELECT
    document_id,
    current_version,
    'metadata_validation',
    TRUE,
    'Document metadata is complete.'
FROM documents
WHERE title = 'System Requirements';

-- ============================================================
-- 35. REVIEW COMMENT
-- ============================================================

DO $$
DECLARE
    v_review UUID;
    v_reviewer UUID;
BEGIN

    SELECT review_id
    INTO v_review
    FROM document_reviews
    WHERE document_id = (
        SELECT document_id
        FROM documents
        WHERE title = 'System Requirements'
    );

    SELECT user_id
    INTO v_reviewer
    FROM users
    WHERE email = 'reviewer@example.com';

    INSERT INTO review_comments (
        review_id,
        author_id,
        section_reference,
        comment_text,
        is_resolved,
        resolved_by,
        resolved_at
    )
    VALUES (
        v_review,
        v_reviewer,
        'Section 2: Security Requirements',
        'Security requirements were checked against the project scope.',
        TRUE,
        v_reviewer,
        NOW()
    );

END;
$$;

-- ============================================================
-- 36. DOCUMENT RETRIEVAL
-- ============================================================

SELECT
    document_id,
    title,
    document_type,
    status,
    current_version,
    created_at,
    updated_at
FROM documents
ORDER BY updated_at DESC;

-- ============================================================
-- 37. VERSION HISTORY RETRIEVAL
-- ============================================================

SELECT *
FROM document_version_history
ORDER BY document_id, version_number;

-- ============================================================
-- 38. PROJECT AGGREGATION
-- ============================================================

SELECT *
FROM project_documentation_summary
ORDER BY project_name;

-- ============================================================
-- 39. APPROVAL ELIGIBILITY
-- ============================================================

SELECT *
FROM check_approval_eligibility(
    (
        SELECT document_id
        FROM documents
        WHERE title = 'System Requirements'
    )
);

-- ============================================================
-- 40. PUBLICATION ELIGIBILITY
-- ============================================================

SELECT *
FROM check_publication_eligibility(
    (
        SELECT document_id
        FROM documents
        WHERE title = 'System Requirements'
    )
);

-- ============================================================
-- 41. DOCUMENT SEARCH
-- ============================================================

SELECT
    d.document_id,
    d.title,
    d.status,
    dv.version_number
FROM documents d
JOIN document_versions dv
    ON dv.document_id = d.document_id
   AND dv.version_number = d.current_version
WHERE to_tsvector(
    'english',
    d.title || ' ' || dv.content
)
@@ plainto_tsquery(
    'english',
    'secure document'
);

-- ============================================================
-- 42. REVIEW REPORT
-- ============================================================

SELECT
    d.title,
    r.version_number,
    u.full_name AS reviewer,
    r.decision,
    r.comments,
    r.created_at
FROM document_reviews r
JOIN documents d
    ON d.document_id = r.document_id
JOIN users u
    ON u.user_id = r.reviewer_id
ORDER BY r.created_at DESC;

-- ============================================================
-- 43. AUDIT REPORT
-- ============================================================

SELECT
    a.audit_id,
    d.title,
    u.full_name AS actor,
    a.action,
    a.details,
    a.occurred_at
FROM document_audit a
JOIN documents d
    ON d.document_id = a.document_id
JOIN users u
    ON u.user_id = a.actor_id
ORDER BY a.occurred_at DESC;

-- ============================================================
-- 44. RETENTION MONITORING
-- ============================================================

SELECT *
FROM document_retention_report
ORDER BY retention_until NULLS LAST;

-- ============================================================
-- 45. TRANSACTIONAL FAILURE DEMONSTRATION
-- ============================================================

DO $$
DECLARE
    v_document UUID;
    v_author UUID;
BEGIN

    SELECT document_id
    INTO v_document
    FROM documents
    WHERE title = 'System Requirements';

    SELECT user_id
    INTO v_author
    FROM users
    WHERE email = 'author@example.com';

    BEGIN

        -- Deliberately use an outdated version number.
        PERFORM create_document_version(
            v_document,
            v_author,
            1,
            'This update must fail.',
            repeat('c', 64)::CHAR(64),
            'Testing optimistic concurrency'
        );

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected version conflict: %',
                SQLERRM;
    END;

END;
$$;

-- ============================================================
-- 46. FINAL INTEGRITY QUERIES
-- ============================================================

-- Detect documents without a matching current version.
SELECT
    d.document_id,
    d.title,
    d.current_version
FROM documents d
LEFT JOIN document_versions dv
    ON dv.document_id = d.document_id
   AND dv.version_number = d.current_version
WHERE dv.version_id IS NULL;

-- Detect reviews referencing outdated document versions.
SELECT
    d.document_id,
    d.title,
    r.version_number AS reviewed_version,
    d.current_version
FROM document_reviews r
JOIN documents d
    ON d.document_id = r.document_id
WHERE r.version_number <> d.current_version;

-- Detect duplicate reviewers across current approvals.
SELECT
    document_id,
    version_number,
    reviewer_id,
    COUNT(*)
FROM document_reviews
WHERE decision = 'approved'
GROUP BY
    document_id,
    version_number,
    reviewer_id
HAVING COUNT(*) > 1;

COMMIT;
