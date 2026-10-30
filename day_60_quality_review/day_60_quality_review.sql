-- PostgreSQL 15+
-- Repository quality review, approvals, status checks and branch protection.
-- The script is self-contained and recreates its demonstration schema.

DROP SCHEMA IF EXISTS repo_governance CASCADE;
CREATE SCHEMA repo_governance;
SET search_path TO repo_governance, public;

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    default_branch_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(repository_name)) > 0),
    CHECK (length(trim(default_branch_name)) > 0)
);

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE repository_members (
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    member_role TEXT NOT NULL
        CHECK (member_role IN ('READ', 'WRITE', 'MAINTAIN', 'ADMIN')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (repository_id, user_id)
);

-- Branch heads reference commits. The foreign key is added after commits
-- are created to handle the circular branch/commit relationship.
CREATE TABLE branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    head_commit_id BIGINT,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0)
);

CREATE TABLE commits (
    commit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_id BIGINT NOT NULL REFERENCES branches(branch_id)
        ON DELETE RESTRICT,
    commit_sha CHAR(40) NOT NULL UNIQUE,
    author_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    parent_commit_id BIGINT REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    commit_message TEXT NOT NULL,
    changed_paths TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(commit_message)) > 0),
    CHECK (array_position(changed_paths, NULL) IS NULL),
    CHECK (
        NOT EXISTS (
            SELECT 1
            FROM unnest(changed_paths) AS path
            WHERE path = ''
               OR path LIKE '/%'
               OR path ~ '(^|/)\.\.(/|$)'
        )
    )
);

ALTER TABLE branches
    ADD CONSTRAINT branches_head_commit_fk
    FOREIGN KEY (head_commit_id)
    REFERENCES commits(commit_id)
    DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX commits_repository_branch_idx
    ON commits(repository_id, branch_id, created_at DESC);

CREATE INDEX commits_parent_idx
    ON commits(parent_commit_id)
    WHERE parent_commit_id IS NOT NULL;

CREATE TABLE pull_requests (
    pull_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    author_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id)
        ON DELETE RESTRICT,
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id)
        ON DELETE RESTRICT,
    base_commit_id BIGINT NOT NULL REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    head_commit_id BIGINT NOT NULL REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    state TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (state IN ('DRAFT', 'OPEN', 'CLOSED', 'MERGED')),
    is_conflicted BOOLEAN NOT NULL DEFAULT FALSE,
    merge_strategy TEXT NOT NULL DEFAULT 'SQUASH'
        CHECK (merge_strategy IN ('MERGE', 'SQUASH', 'REBASE')),
    merged_commit_id BIGINT REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    merged_by BIGINT REFERENCES users(user_id)
        ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) > 0),
    CHECK (
        (state = 'MERGED' AND merged_commit_id IS NOT NULL
                           AND merged_by IS NOT NULL)
        OR
        (state <> 'MERGED' AND merged_commit_id IS NULL
                            AND merged_by IS NULL)
    )
);

CREATE INDEX pull_requests_target_state_idx
    ON pull_requests(target_branch_id, state, created_at DESC);

CREATE INDEX pull_requests_author_idx
    ON pull_requests(author_id, created_at DESC);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    position INTEGER NOT NULL CHECK (position > 0),
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, position)
);

CREATE TABLE review_requests (
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    requested_by BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (pull_request_id, reviewer_id)
);

CREATE TABLE reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    reviewed_commit_id BIGINT NOT NULL REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    review_state TEXT NOT NULL
        CHECK (review_state IN (
            'COMMENTED', 'APPROVED', 'CHANGES_REQUESTED',
            'DISMISSED', 'STALE'
        )),
    review_body TEXT NOT NULL DEFAULT '',
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    dismissed_by BIGINT REFERENCES users(user_id)
        ON DELETE RESTRICT,
    dismissed_at TIMESTAMPTZ,
    CHECK (
        (review_state = 'DISMISSED' AND dismissed_at IS NOT NULL)
        OR
        (review_state <> 'DISMISSED' AND dismissed_at IS NULL)
    )
);

CREATE INDEX reviews_latest_per_reviewer_idx
    ON reviews(pull_request_id, reviewer_id, submitted_at DESC, review_id DESC);

CREATE TABLE review_threads (
    thread_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by BIGINT REFERENCES users(user_id)
        ON DELETE RESTRICT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
        (is_resolved AND resolved_by IS NOT NULL AND resolved_at IS NOT NULL)
        OR
        (NOT is_resolved AND resolved_by IS NULL AND resolved_at IS NULL)
    ),
    CHECK (length(trim(file_path)) > 0)
);

CREATE INDEX review_threads_open_idx
    ON review_threads(pull_request_id)
    WHERE is_resolved = FALSE;

CREATE TABLE review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    thread_id BIGINT NOT NULL REFERENCES review_threads(thread_id)
        ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    review_id BIGINT REFERENCES reviews(review_id)
        ON DELETE SET NULL,
    comment_body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (length(trim(comment_body)) > 0)
);

CREATE INDEX review_comments_thread_idx
    ON review_comments(thread_id, created_at);

CREATE TABLE status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_context TEXT NOT NULL,
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    check_state TEXT NOT NULL
        CHECK (check_state IN ('PENDING', 'SUCCESS', 'FAILURE')),
    details TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pull_request_id, check_context, commit_id),
    CHECK (length(trim(check_context)) > 0)
);

CREATE INDEX status_checks_pr_commit_idx
    ON status_checks(pull_request_id, commit_id, check_state);

CREATE TABLE branch_protection (
    branch_id BIGINT PRIMARY KEY REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_approvals INTEGER NOT NULL DEFAULT 1
        CHECK (required_approvals >= 0),
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_discussions BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    administrators_enforced BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE required_status_checks (
    branch_id BIGINT NOT NULL REFERENCES branch_protection(branch_id)
        ON DELETE CASCADE,
    check_context TEXT NOT NULL,
    PRIMARY KEY (branch_id, check_context),
    CHECK (length(trim(check_context)) > 0)
);

-- These rules represent additional approval requirements that apply
-- to reviewers in specified repository roles.
CREATE TABLE approval_requirements (
    branch_id BIGINT NOT NULL REFERENCES branch_protection(branch_id)
        ON DELETE CASCADE,
    reviewer_role TEXT NOT NULL
        CHECK (reviewer_role IN ('WRITE', 'MAINTAIN', 'ADMIN')),
    minimum_count INTEGER NOT NULL CHECK (minimum_count >= 0),
    PRIMARY KEY (branch_id, reviewer_role)
);

CREATE TABLE branch_bypass_roles (
    branch_id BIGINT NOT NULL REFERENCES branch_protection(branch_id)
        ON DELETE CASCADE,
    member_role TEXT NOT NULL
        CHECK (member_role IN ('WRITE', 'MAINTAIN', 'ADMIN')),
    PRIMARY KEY (branch_id, member_role)
);

CREATE TABLE merge_events (
    merge_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id)
        ON DELETE RESTRICT,
    merged_commit_id BIGINT NOT NULL REFERENCES commits(commit_id)
        ON DELETE RESTRICT,
    actor_id BIGINT NOT NULL REFERENCES users(user_id)
        ON DELETE RESTRICT,
    merge_strategy TEXT NOT NULL
        CHECK (merge_strategy IN ('MERGE', 'SQUASH', 'REBASE')),
    merged_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enforce membership, reviewer eligibility, and protection boundaries.
CREATE OR REPLACE FUNCTION validate_review_submission()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    request_author BIGINT;
    reviewer_role TEXT;
    reviewer_active BOOLEAN;
BEGIN
    SELECT author_id
      INTO request_author
      FROM pull_requests
     WHERE pull_request_id = NEW.pull_request_id
       AND state = 'OPEN';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Reviews require an open Pull Request';
    END IF;

    IF NEW.reviewer_id = request_author THEN
        RAISE EXCEPTION 'Pull Request authors cannot approve their own changes';
    END IF;

    SELECT rm.member_role, u.active
      INTO reviewer_role, reviewer_active
      FROM repository_members rm
      JOIN pull_requests pr
        ON pr.repository_id = rm.repository_id
      JOIN users u
        ON u.user_id = rm.user_id
     WHERE pr.pull_request_id = NEW.pull_request_id
       AND rm.user_id = NEW.reviewer_id;

    IF NOT FOUND OR NOT reviewer_active OR reviewer_role = 'READ' THEN
        RAISE EXCEPTION 'Reviewer is not an active eligible repository member';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER reviews_validate_submission
BEFORE INSERT ON reviews
FOR EACH ROW
EXECUTE FUNCTION validate_review_submission();

CREATE OR REPLACE FUNCTION validate_branch_head_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    protected_branch BOOLEAN;
    direct_push_allowed BOOLEAN;
BEGIN
    IF NEW.head_commit_id IS NOT DISTINCT FROM OLD.head_commit_id THEN
        RETURN NEW;
    END IF;

    SELECT EXISTS (
        SELECT 1
          FROM branch_protection
         WHERE branch_id = OLD.branch_id
    ),
    COALESCE((
        SELECT allow_direct_push
          FROM branch_protection
         WHERE branch_id = OLD.branch_id
    ), TRUE)
    INTO protected_branch, direct_push_allowed;

    IF protected_branch
       AND NOT direct_push_allowed
       AND current_setting('repo_governance.merge_operation', TRUE)
           IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION 'Protected branch rejects direct head updates';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER branches_protect_head
BEFORE UPDATE OF head_commit_id ON branches
FOR EACH ROW
EXECUTE FUNCTION validate_branch_head_update();

CREATE OR REPLACE FUNCTION validate_pull_request_state_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state = NEW.state THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.state = 'DRAFT' AND NEW.state IN ('OPEN', 'CLOSED'))
        OR
        (OLD.state = 'OPEN' AND NEW.state IN ('CLOSED', 'MERGED'))
        OR
        (OLD.state = 'CLOSED' AND NEW.state = 'OPEN')
    ) THEN
        RAISE EXCEPTION 'Invalid Pull Request state transition: % -> %',
            OLD.state, NEW.state;
    END IF;

    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER pull_requests_state_transition
BEFORE UPDATE OF state ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION validate_pull_request_state_transition();

CREATE OR REPLACE FUNCTION validate_discussion_resolution()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.is_resolved AND NOT OLD.is_resolved THEN
        IF NEW.resolved_by IS NULL THEN
            RAISE EXCEPTION 'Resolving a discussion requires a responsible user';
        END IF;
        NEW.resolved_at := COALESCE(NEW.resolved_at, now());
    ELSIF NOT NEW.is_resolved THEN
        NEW.resolved_by := NULL;
        NEW.resolved_at := NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER review_threads_resolution
BEFORE UPDATE OF is_resolved ON review_threads
FOR EACH ROW
EXECUTE FUNCTION validate_discussion_resolution();

-- Return one row per merge blocker. An eligible Pull Request returns
-- one row with eligible = TRUE and blocker = NULL.
CREATE OR REPLACE FUNCTION evaluate_merge_eligibility(
    p_pull_request_id BIGINT,
    p_actor_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    blocker TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    pr pull_requests%ROWTYPE;
    protection_record branch_protection%ROWTYPE;
    actor_role TEXT;
    actor_active BOOLEAN;
    policy_bypass BOOLEAN := FALSE;
    source_head BIGINT;
    target_head BIGINT;
    approval_count BIGINT := 0;
    changes_requested_count BIGINT := 0;
    unresolved_count BIGINT := 0;
    role_requirement RECORD;
    role_approval_count BIGINT := 0;
    required_context TEXT;
    check_state TEXT;
    blockers TEXT[] := ARRAY[]::TEXT[];
BEGIN
    SELECT *
      INTO pr
      FROM pull_requests
     WHERE pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        eligible := FALSE;
        blocker := 'Pull Request does not exist';
        RETURN NEXT;
        RETURN;
    END IF;

    SELECT rm.member_role, u.active
      INTO actor_role, actor_active
      FROM repository_members rm
      JOIN users u ON u.user_id = rm.user_id
     WHERE rm.repository_id = pr.repository_id
       AND rm.user_id = p_actor_id;

    IF NOT FOUND OR NOT actor_active OR actor_role = 'READ' THEN
        eligible := FALSE;
        blocker := 'Merge actor is not an active member with write permission';
        RETURN NEXT;
        RETURN;
    END IF;

    SELECT *
      INTO protection_record
      FROM branch_protection
     WHERE branch_id = pr.target_branch_id;

    IF NOT FOUND THEN
        protection_record.required_approvals := 0;
        protection_record.dismiss_stale_approvals := TRUE;
        protection_record.require_resolved_discussions := FALSE;
        protection_record.require_linear_history := FALSE;
        protection_record.administrators_enforced := TRUE;
    END IF;

    SELECT head_commit_id
      INTO source_head
      FROM branches
     WHERE branch_id = pr.source_branch_id
       AND is_deleted = FALSE;

    IF NOT FOUND THEN
        blockers := array_append(blockers, 'Source branch is deleted or unavailable');
    END IF;

    SELECT head_commit_id
      INTO target_head
      FROM branches
     WHERE branch_id = pr.target_branch_id
       AND is_deleted = FALSE;

    IF NOT FOUND THEN
        blockers := array_append(blockers, 'Target branch is deleted or unavailable');
    END IF;

    IF pr.state <> 'OPEN' THEN
        blockers := array_append(blockers, 'Pull Request is not open');
    END IF;

    IF source_head IS DISTINCT FROM pr.head_commit_id THEN
        blockers := array_append(
            blockers,
            'Source branch has commits not represented by the Pull Request'
        );
    END IF;

    IF target_head IS DISTINCT FROM pr.base_commit_id THEN
        blockers := array_append(
            blockers,
            'Target branch has advanced; synchronize the source branch'
        );
    END IF;

    IF pr.is_conflicted THEN
        blockers := array_append(blockers, 'Merge conflicts remain unresolved');
    END IF;

    SELECT (
        (actor_role = 'ADMIN' AND NOT protection_record.administrators_enforced)
        OR EXISTS (
            SELECT 1
              FROM branch_bypass_roles bbr
             WHERE bbr.branch_id = pr.target_branch_id
               AND bbr.member_role = actor_role
        )
    )
    INTO policy_bypass;

    IF NOT policy_bypass THEN
        FOR required_context IN
            SELECT rsc.check_context
              FROM required_status_checks rsc
             WHERE rsc.branch_id = pr.target_branch_id
        LOOP
            SELECT sc.check_state
              INTO check_state
              FROM status_checks sc
             WHERE sc.pull_request_id = p_pull_request_id
               AND sc.check_context = required_context
               AND sc.commit_id = pr.head_commit_id
             ORDER BY sc.updated_at DESC, sc.status_check_id DESC
             LIMIT 1;

            IF check_state IS DISTINCT FROM 'SUCCESS' THEN
                blockers := array_append(
                    blockers,
                    format(
                        'Required status check has not succeeded: %s',
                        required_context
                    )
                );
            END IF;
        END LOOP;

        -- Select each reviewer's latest decision first. A newer changes-requested
        -- review must not be hidden by an older approval.
        WITH latest_reviews AS (
            SELECT DISTINCT ON (r.reviewer_id)
                   r.reviewer_id,
                   r.review_state,
                   r.reviewed_commit_id
              FROM reviews r
             WHERE r.pull_request_id = p_pull_request_id
             ORDER BY r.reviewer_id,
                      r.submitted_at DESC,
                      r.review_id DESC
        )
        SELECT
            COUNT(*) FILTER (
                WHERE lr.review_state = 'APPROVED'
                  AND (
                      NOT protection_record.dismiss_stale_approvals
                      OR lr.reviewed_commit_id = pr.head_commit_id
                  )
            ),
            COUNT(*) FILTER (
                WHERE lr.review_state = 'CHANGES_REQUESTED'
                  AND (
                      NOT protection_record.dismiss_stale_approvals
                      OR lr.reviewed_commit_id = pr.head_commit_id
                  )
            )
          INTO approval_count, changes_requested_count
          FROM latest_reviews lr
          JOIN repository_members rm
            ON rm.repository_id = pr.repository_id
           AND rm.user_id = lr.reviewer_id
          JOIN users u
            ON u.user_id = lr.reviewer_id
         WHERE lr.reviewer_id <> pr.author_id
           AND u.active
           AND rm.member_role IN ('WRITE', 'MAINTAIN', 'ADMIN');

        IF changes_requested_count > 0 THEN
            blockers := array_append(
                blockers,
                'One or more eligible reviewers have requested changes'
            );
        END IF;

        IF approval_count < protection_record.required_approvals THEN
            blockers := array_append(
                blockers,
                format(
                    'Approval requirement not met: %s of %s',
                    approval_count,
                    protection_record.required_approvals
                )
            );
        END IF;

        -- Enforce role-specific approval requirements independently
        -- from the repository-wide approval threshold.
        FOR role_requirement IN
            SELECT reviewer_role, minimum_count
              FROM approval_requirements
             WHERE branch_id = pr.target_branch_id
        LOOP
            WITH latest_role_reviews AS (
                SELECT DISTINCT ON (r.reviewer_id)
                       r.reviewer_id,
                       r.review_state,
                       r.reviewed_commit_id
                  FROM reviews r
                 WHERE r.pull_request_id = p_pull_request_id
                 ORDER BY r.reviewer_id,
                          r.submitted_at DESC,
                          r.review_id DESC
            )
            SELECT COUNT(*)
              INTO role_approval_count
              FROM latest_role_reviews lr
              JOIN repository_members rm
                ON rm.repository_id = pr.repository_id
               AND rm.user_id = lr.reviewer_id
              JOIN users u
                ON u.user_id = lr.reviewer_id
             WHERE lr.reviewer_id <> pr.author_id
               AND u.active
               AND rm.member_role = role_requirement.reviewer_role
               AND lr.review_state = 'APPROVED'
               AND (
                    NOT protection_record.dismiss_stale_approvals
                    OR lr.reviewed_commit_id = pr.head_commit_id
               );

            IF role_approval_count < role_requirement.minimum_count THEN
                blockers := array_append(
                    blockers,
                    format(
                        'Role-specific approval requirement not met for %s',
                        role_requirement.reviewer_role
                    )
                );
            END IF;
        END LOOP;

        IF protection_record.require_resolved_discussions THEN
            SELECT COUNT(*)
              INTO unresolved_count
              FROM review_threads
             WHERE pull_request_id = p_pull_request_id
               AND NOT is_resolved;

            IF unresolved_count > 0 THEN
                blockers := array_append(
                    blockers,
                    format('%s review discussion(s) remain unresolved', unresolved_count)
                );
            END IF;
        END IF;

        IF protection_record.require_linear_history
           AND pr.merge_strategy = 'MERGE' THEN
            blockers := array_append(
                blockers,
                'Selected merge strategy violates linear-history policy'
            );
        END IF;
    END IF;

    IF cardinality(blockers) > 0 THEN
        FOREACH blocker IN ARRAY blockers LOOP
            eligible := FALSE;
            RETURN NEXT;
        END LOOP;
    ELSE
        eligible := TRUE;
        blocker := NULL;
        RETURN NEXT;
    END IF;
END;
$$;

-- The view provides a repository-wide operational review of open requests.
CREATE OR REPLACE VIEW pull_request_quality_overview AS
SELECT
    pr.pull_request_id,
    repo.repository_name,
    pr.title,
    author.username AS author,
    source.branch_name AS source_branch,
    target.branch_name AS target_branch,
    pr.state,
    pr.merge_strategy,
    pr.is_conflicted,
    pr.base_commit_id,
    pr.head_commit_id,
    COUNT(DISTINCT r.review_id) AS submitted_review_count,
    COUNT(DISTINCT r.review_id) FILTER (
        WHERE r.review_state = 'APPROVED'
    ) AS recorded_approval_count,
    COUNT(DISTINCT rt.thread_id) FILTER (
        WHERE NOT rt.is_resolved
    ) AS unresolved_discussion_count,
    COUNT(DISTINCT sc.status_check_id) FILTER (
        WHERE sc.commit_id = pr.head_commit_id
          AND sc.check_state = 'SUCCESS'
    ) AS successful_current_head_checks
FROM pull_requests pr
JOIN repositories repo
  ON repo.repository_id = pr.repository_id
JOIN users author
  ON author.user_id = pr.author_id
JOIN branches source
  ON source.branch_id = pr.source_branch_id
JOIN branches target
  ON target.branch_id = pr.target_branch_id
LEFT JOIN reviews r
  ON r.pull_request_id = pr.pull_request_id
LEFT JOIN review_threads rt
  ON rt.pull_request_id = pr.pull_request_id
LEFT JOIN status_checks sc
  ON sc.pull_request_id = pr.pull_request_id
GROUP BY
    pr.pull_request_id,
    repo.repository_name,
    pr.title,
    author.username,
    source.branch_name,
    target.branch_name,
    pr.state,
    pr.merge_strategy,
    pr.is_conflicted,
    pr.base_commit_id,
    pr.head_commit_id;

-- The merge procedure evaluates all governance conditions within the same
-- transaction that creates the merge commit and updates the target branch.
CREATE OR REPLACE PROCEDURE merge_pull_request(
    p_pull_request_id BIGINT,
    p_actor_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    pr pull_requests%ROWTYPE;
    target_branch branches%ROWTYPE;
    actor_role TEXT;
    actor_active BOOLEAN;
    blocker_list TEXT[];
    new_commit_id BIGINT;
    new_sha CHAR(40);
    merged_paths TEXT[];
    parent_id BIGINT;
BEGIN
    SELECT *
      INTO pr
      FROM pull_requests
     WHERE pull_request_id = p_pull_request_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pull Request % does not exist', p_pull_request_id;
    END IF;

    SELECT rm.member_role, u.active
      INTO actor_role, actor_active
      FROM repository_members rm
      JOIN users u ON u.user_id = rm.user_id
     WHERE rm.repository_id = pr.repository_id
       AND rm.user_id = p_actor_id;

    IF NOT FOUND OR NOT actor_active OR actor_role = 'READ' THEN
        RAISE EXCEPTION 'Merge actor is not eligible';
    END IF;

    SELECT array_agg(blocker)
      INTO blocker_list
      FROM evaluate_merge_eligibility(p_pull_request_id, p_actor_id)
     WHERE NOT eligible;

    IF blocker_list IS NOT NULL THEN
        RAISE EXCEPTION 'Merge blocked: %', array_to_string(blocker_list, '; ');
    END IF;

    SELECT *
      INTO target_branch
      FROM branches
     WHERE branch_id = pr.target_branch_id
     FOR UPDATE;

    SELECT COALESCE(
        array_agg(DISTINCT changed_path ORDER BY changed_path),
        ARRAY[]::TEXT[]
    )
      INTO merged_paths
      FROM (
          SELECT unnest(c.changed_paths) AS changed_path
            FROM pull_request_commits pc
            JOIN commits c ON c.commit_id = pc.commit_id
           WHERE pc.pull_request_id = p_pull_request_id
      ) proposed_paths;

    parent_id := target_branch.head_commit_id;

    -- A unique SHA-shaped identifier is sufficient for this demonstration.
    -- A production service should use the actual version-control object hash.
    new_sha := (
        substr(md5(random()::TEXT || clock_timestamp()::TEXT), 1, 32) ||
        substr(md5(clock_timestamp()::TEXT || random()::TEXT), 1, 8)
    )::CHAR(40);

    INSERT INTO commits (
        repository_id,
        branch_id,
        commit_sha,
        author_id,
        parent_commit_id,
        commit_message,
        changed_paths
    )
    VALUES (
        pr.repository_id,
        pr.target_branch_id,
        new_sha,
        p_actor_id,
        parent_id,
        format('%s Pull Request #%s: %s',
            pr.merge_strategy, pr.pull_request_id, pr.title),
        merged_paths
    )
    RETURNING commit_id INTO new_commit_id;

    -- The transaction-local marker allows this controlled merge operation
    -- through the direct-push protection trigger.
    PERFORM set_config('repo_governance.merge_operation', 'on', TRUE);

    UPDATE branches
       SET head_commit_id = new_commit_id
     WHERE branch_id = pr.target_branch_id;

    UPDATE pull_requests
       SET state = 'MERGED',
           merged_commit_id = new_commit_id,
           merged_by = p_actor_id,
           updated_at = now()
     WHERE pull_request_id = p_pull_request_id;

    INSERT INTO merge_events (
        pull_request_id,
        merged_commit_id,
        actor_id,
        merge_strategy
    )
    VALUES (
        p_pull_request_id,
        new_commit_id,
        p_actor_id,
        pr.merge_strategy
    );
END;
$$;

-- -------------------------------------------------------------------------
-- Demonstration data
-- -------------------------------------------------------------------------

INSERT INTO repositories (repository_name, default_branch_name)
VALUES ('quality-review-platform', 'main');

INSERT INTO users (username)
VALUES
    ('developer'),
    ('reviewer'),
    ('administrator'),
    ('read_only_auditor');

INSERT INTO repository_members (repository_id, user_id, member_role)
SELECT 1, user_id,
       CASE username
           WHEN 'developer' THEN 'WRITE'
           WHEN 'reviewer' THEN 'MAINTAIN'
           WHEN 'administrator' THEN 'ADMIN'
           ELSE 'READ'
       END
FROM users;

INSERT INTO branches (repository_id, branch_name)
VALUES
    (1, 'main'),
    (1, 'feature/review-quality');

INSERT INTO commits (
    repository_id, branch_id, commit_sha, author_id,
    parent_commit_id, commit_message, changed_paths
)
SELECT
    1,
    (SELECT branch_id FROM branches
      WHERE repository_id = 1 AND branch_name = 'main'),
    repeat('a', 40),
    (SELECT user_id FROM users WHERE username = 'developer'),
    NULL,
    'Initial repository commit',
    ARRAY[]::TEXT[];

INSERT INTO branches (repository_id, branch_name, head_commit_id)
SELECT
    1,
    'integration/test-branch',
    commit_id
FROM commits
WHERE commit_sha = repeat('a', 40)
ON CONFLICT (repository_id, branch_name) DO NOTHING;

INSERT INTO commits (
    repository_id, branch_id, commit_sha, author_id,
    parent_commit_id, commit_message, changed_paths
)
SELECT
    1,
    (SELECT branch_id FROM branches
      WHERE repository_id = 1 AND branch_name = 'feature/review-quality'),
    repeat('b', 40),
    (SELECT user_id FROM users WHERE username = 'developer'),
    (SELECT commit_id FROM commits WHERE commit_sha = repeat('a', 40)),
    'Add review-quality policy checks',
    ARRAY[
        'src/review_quality.py',
        'tests/test_review_quality.py'
    ];

UPDATE branches
   SET head_commit_id = (
       SELECT commit_id FROM commits WHERE commit_sha = repeat('a', 40)
   )
 WHERE repository_id = 1
   AND branch_name = 'main';

UPDATE branches
   SET head_commit_id = (
       SELECT commit_id FROM commits WHERE commit_sha = repeat('b', 40)
   )
 WHERE repository_id = 1
   AND branch_name = 'feature/review-quality';

INSERT INTO branch_protection (
    branch_id,
    required_approvals,
    dismiss_stale_approvals,
    require_resolved_discussions,
    require_linear_history,
    allow_direct_push,
    allow_force_push,
    allow_deletion,
    administrators_enforced
)
SELECT
    branch_id,
    1,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    TRUE
FROM branches
WHERE repository_id = 1
  AND branch_name = 'main';

INSERT INTO required_status_checks (branch_id, check_context)
SELECT branch_id, required_context
FROM branches
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS required(required_context)
WHERE repository_id = 1
  AND branch_name = 'main';

INSERT INTO approval_requirements (branch_id, reviewer_role, minimum_count)
SELECT branch_id, 'MAINTAIN', 1
FROM branches
WHERE repository_id = 1
  AND branch_name = 'main';

-- A role-based bypass is deliberately absent from this policy.
INSERT INTO pull_requests (
    repository_id,
    title,
    description,
    author_id,
    source_branch_id,
    target_branch_id,
    base_commit_id,
    head_commit_id,
    state,
    merge_strategy
)
SELECT
    1,
    'Enforce review quality requirements',
    'Demonstrates independent review, approval, check and branch policies.',
    (SELECT user_id FROM users WHERE username = 'developer'),
    (SELECT branch_id FROM branches
      WHERE repository_id = 1 AND branch_name = 'feature/review-quality'),
    (SELECT branch_id FROM branches
      WHERE repository_id = 1 AND branch_name = 'main'),
    (SELECT commit_id FROM commits WHERE commit_sha = repeat('a', 40)),
    (SELECT commit_id FROM commits WHERE commit_sha = repeat('b', 40)),
    'OPEN',
    'SQUASH';

INSERT INTO pull_request_commits (pull_request_id, commit_id, position)
SELECT
    (SELECT pull_request_id FROM pull_requests
      WHERE title = 'Enforce review quality requirements'),
    commit_id,
    1
FROM commits
WHERE commit_sha = repeat('b', 40);

INSERT INTO review_requests (pull_request_id, reviewer_id, requested_by)
SELECT
    pr.pull_request_id,
    reviewer.user_id,
    author.user_id
FROM pull_requests pr
JOIN users reviewer ON reviewer.username = 'reviewer'
JOIN users author ON author.username = 'developer'
WHERE pr.title = 'Enforce review quality requirements';

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    reviewed_commit_id,
    review_state,
    review_body
)
SELECT
    pr.pull_request_id,
    reviewer.user_id,
    pr.head_commit_id,
    'APPROVED',
    'The review criteria are clear and the validation cases are relevant.'
FROM pull_requests pr
JOIN users reviewer ON reviewer.username = 'reviewer'
WHERE pr.title = 'Enforce review quality requirements';

INSERT INTO review_threads (
    pull_request_id,
    file_path,
    line_number,
    is_resolved
)
SELECT
    pull_request_id,
    'src/review_quality.py',
    18,
    FALSE
FROM pull_requests
WHERE title = 'Enforce review quality requirements';

INSERT INTO review_comments (
    thread_id,
    author_id,
    comment_body
)
SELECT
    rt.thread_id,
    u.user_id,
    'The stale-approval behavior is covered by the policy evaluation.'
FROM review_threads rt
JOIN pull_requests pr ON pr.pull_request_id = rt.pull_request_id
JOIN users u ON u.username = 'reviewer'
WHERE pr.title = 'Enforce review quality requirements';

UPDATE review_threads
   SET is_resolved = TRUE,
       resolved_by = (SELECT user_id FROM users WHERE username = 'developer')
 WHERE pull_request_id = (
     SELECT pull_request_id FROM pull_requests
      WHERE title = 'Enforce review quality requirements'
 );

INSERT INTO status_checks (
    pull_request_id, check_context, commit_id, check_state, details
)
SELECT
    pr.pull_request_id,
    required.check_context,
    pr.head_commit_id,
    'SUCCESS',
    'The check completed successfully on the current Pull Request head.'
FROM pull_requests pr
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS required(check_context)
WHERE pr.title = 'Enforce review quality requirements';

-- -------------------------------------------------------------------------
-- Evaluation and reporting queries
-- -------------------------------------------------------------------------

-- Pull Request, review and discussion overview.
SELECT *
FROM pull_request_quality_overview
ORDER BY pull_request_id;

-- Current-head check results only.
SELECT
    pr.pull_request_id,
    sc.check_context,
    sc.check_state,
    sc.commit_id,
    sc.updated_at
FROM pull_requests pr
JOIN status_checks sc
  ON sc.pull_request_id = pr.pull_request_id
 AND sc.commit_id = pr.head_commit_id
ORDER BY sc.check_context;

-- Latest decision from each reviewer.
WITH latest_reviews AS (
    SELECT DISTINCT ON (reviewer_id)
           reviewer_id,
           review_state,
           reviewed_commit_id,
           submitted_at
    FROM reviews
    WHERE pull_request_id = (
        SELECT pull_request_id
        FROM pull_requests
        WHERE title = 'Enforce review quality requirements'
    )
    ORDER BY reviewer_id, submitted_at DESC, review_id DESC
)
SELECT
    u.username,
    lr.review_state,
    lr.reviewed_commit_id,
    lr.submitted_at
FROM latest_reviews lr
JOIN users u ON u.user_id = lr.reviewer_id;

-- Merge eligibility is evaluated for the developer acting as merger.
SELECT
    eligible,
    blocker
FROM evaluate_merge_eligibility(
    (SELECT pull_request_id
       FROM pull_requests
      WHERE title = 'Enforce review quality requirements'),
    (SELECT user_id FROM users WHERE username = 'developer')
);

-- -------------------------------------------------------------------------
-- Negative-case records and checks
-- -------------------------------------------------------------------------

-- A pending check on the current head is not sufficient for merging.
INSERT INTO status_checks (
    pull_request_id, check_context, commit_id, check_state, details
)
SELECT
    pr.pull_request_id,
    'documentation-review',
    pr.head_commit_id,
    'PENDING',
    'Illustrative non-required check.'
FROM pull_requests pr
WHERE pr.title = 'Enforce review quality requirements';

-- The following savepoint demonstrates transactional recovery from a
-- prohibited direct protected-branch head update.
BEGIN;
SAVEPOINT before_protected_branch_update;

DO $$
DECLARE
    branch_value BIGINT;
    head_value BIGINT;
BEGIN
    SELECT branch_id, head_commit_id
      INTO branch_value, head_value
      FROM branches
     WHERE repository_id = 1
       AND branch_name = 'main';

    BEGIN
        UPDATE branches
           SET head_commit_id = (
               SELECT commit_id
                 FROM commits
                WHERE commit_sha = repeat('b', 40)
           )
         WHERE branch_id = branch_value;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Expected branch protection rejection: %', SQLERRM;
    END;
END;
$$;

ROLLBACK TO SAVEPOINT before_protected_branch_update;
COMMIT;

-- Execute the merge within a transaction. The procedure raises an exception
-- and leaves the transaction uncommitted if any required condition fails.
BEGIN;

CALL merge_pull_request(
    (SELECT pull_request_id
       FROM pull_requests
      WHERE title = 'Enforce review quality requirements'),
    (SELECT user_id FROM users WHERE username = 'developer')
);

COMMIT;

-- Final workflow state and recorded merge event.
SELECT
    pr.pull_request_id,
    pr.state,
    pr.merged_commit_id,
    merger.username AS merged_by,
    me.merge_strategy,
    me.merged_at
FROM pull_requests pr
LEFT JOIN users merger ON merger.user_id = pr.merged_by
LEFT JOIN merge_events me ON me.pull_request_id = pr.pull_request_id
WHERE pr.title = 'Enforce review quality requirements';
