/*
===============================================================================
RISK IDENTIFICATION AND ASSESSMENT DATABASE
===============================================================================

Platform: PostgreSQL 14+

Implements:
- Organizational risk registers
- Risk taxonomy
- Identification sources
- Risk ownership
- Probability, impact and detectability
- Evidence traceability
- Preventive, detective and corrective controls
- Inherent and residual exposure
- Risk status transitions
- Assessment history
- Risk identification validation
- Risk prioritization
- Risk aggregation and reporting
- Risk governance policies
- Transactional workflow processing

The scoring method is a prioritization model:
Inherent Score = Probability * Impact * Detectability

All three dimensions use a 1-5 scale.

Risk thresholds:
1-14   LOW
15-39  MODERATE
40-74  HIGH
75-125 CRITICAL

Control effectiveness is modeled as independent control effectiveness.
It is a simplified assessment assumption, not a statistical guarantee.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS risk_management;

SET search_path TO risk_management, public;

-- ============================================================================
-- 1. ENUMERATED DOMAIN TYPES
-- ============================================================================

CREATE TYPE risk_category AS ENUM (
    'strategic',
    'operational',
    'financial',
    'technological',
    'cybersecurity',
    'compliance',
    'reputational',
    'environmental',
    'human_resource',
    'third_party'
);

CREATE TYPE identification_source AS ENUM (
    'workshop',
    'audit',
    'incident',
    'interview',
    'historical_data',
    'technical_analysis',
    'external_environment'
);

CREATE TYPE risk_status AS ENUM (
    'identified',
    'assessed',
    'under_review',
    'mitigated',
    'accepted',
    'closed'
);

CREATE TYPE risk_level AS ENUM (
    'low',
    'moderate',
    'high',
    'critical'
);

CREATE TYPE control_type AS ENUM (
    'preventive',
    'detective',
    'corrective'
);

-- ============================================================================
-- 2. ORGANIZATIONAL ENTITIES
-- ============================================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(200) NOT NULL UNIQUE,
    industry VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (length(trim(organization_name)) > 0)
);

CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    job_role VARCHAR(120) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (organization_id, email),
    UNIQUE (organization_id, user_id),

    CHECK (length(trim(full_name)) > 0)
);

-- ============================================================================
-- 3. RISK REGISTER
-- ============================================================================

CREATE TABLE risks (
    risk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    risk_code VARCHAR(40) NOT NULL,
    title VARCHAR(250) NOT NULL,
    description TEXT NOT NULL,
    context_description TEXT NOT NULL,

    category risk_category NOT NULL,
    source identification_source NOT NULL,

    owner_id BIGINT NOT NULL,

    probability SMALLINT NOT NULL,
    impact SMALLINT NOT NULL,
    detectability SMALLINT NOT NULL,

    status risk_status NOT NULL DEFAULT 'identified',

    identified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_reviewed_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,

    version INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (organization_id, owner_id)
        REFERENCES users(organization_id, user_id),

    UNIQUE (organization_id, risk_code),
    UNIQUE (risk_id, organization_id),

    CHECK (length(trim(title)) > 0),
    CHECK (length(trim(description)) > 0),
    CHECK (length(trim(context_description)) > 0),

    CHECK (probability BETWEEN 1 AND 5),
    CHECK (impact BETWEEN 1 AND 5),
    CHECK (detectability BETWEEN 1 AND 5),

    CHECK (version >= 1),

    CHECK (
        (status = 'closed' AND closed_at IS NOT NULL)
        OR
        (status <> 'closed' AND closed_at IS NULL)
    )
);

-- One active risk with the same normalized title and context is prevented.
CREATE UNIQUE INDEX uq_risk_active_fingerprint
ON risks (
    organization_id,
    lower(trim(title)),
    lower(trim(context_description))
)
WHERE status <> 'closed';

CREATE INDEX idx_risks_priority_dimensions
ON risks (
    organization_id,
    probability DESC,
    impact DESC,
    detectability DESC
);

CREATE INDEX idx_risks_category_status
ON risks (organization_id, category, status);

CREATE INDEX idx_risks_owner
ON risks (owner_id, status);

CREATE INDEX idx_risks_identified_at
ON risks (identified_at DESC);

-- ============================================================================
-- 4. EVIDENCE MANAGEMENT
-- ============================================================================

CREATE TABLE risk_evidence (
    evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,

    evidence_reference VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    source identification_source NOT NULL,

    collected_by BIGINT NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (risk_id, organization_id)
        REFERENCES risks(risk_id, organization_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (organization_id, collected_by)
        REFERENCES users(organization_id, user_id),

    UNIQUE (risk_id, evidence_reference),

    CHECK (length(trim(evidence_reference)) > 0),
    CHECK (length(trim(description)) > 0)
);

CREATE INDEX idx_evidence_risk
ON risk_evidence(risk_id, collected_at DESC);

-- ============================================================================
-- 5. CONTROL CATALOGUE
-- ============================================================================

CREATE TABLE controls (
    control_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    control_code VARCHAR(60) NOT NULL,
    control_name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    control_category control_type NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE (organization_id, control_code),

    CHECK (length(trim(control_name)) > 0)
);

CREATE TABLE risk_controls (
    risk_control_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL,
    organization_id BIGINT NOT NULL,
    control_id BIGINT NOT NULL,

    effectiveness NUMERIC(5,4) NOT NULL,
    implementation_status VARCHAR(30) NOT NULL DEFAULT 'implemented',

    verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMPTZ,

    FOREIGN KEY (risk_id, organization_id)
        REFERENCES risks(risk_id, organization_id),

    FOREIGN KEY (organization_id, control_id)
        REFERENCES controls(organization_id, control_id),

    UNIQUE (risk_id, control_id),

    CHECK (effectiveness BETWEEN 0 AND 1),

    CHECK (
        implementation_status IN (
            'planned',
            'in_progress',
            'implemented',
            'ineffective',
            'retired'
        )
    ),

    CHECK (
        verified = FALSE OR verified_at IS NOT NULL
    )
);

CREATE INDEX idx_risk_controls_risk
ON risk_controls(risk_id);

-- ============================================================================
-- 6. ASSESSMENT HISTORY
-- ============================================================================

CREATE TABLE risk_assessment_history (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    risk_id BIGINT NOT NULL
        REFERENCES risks(risk_id),

    assessed_by BIGINT NOT NULL
        REFERENCES users(user_id),

    probability SMALLINT NOT NULL,
    impact SMALLINT NOT NULL,
    detectability SMALLINT NOT NULL,

    assessment_reason TEXT NOT NULL,

    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (probability BETWEEN 1 AND 5),
    CHECK (impact BETWEEN 1 AND 5),
    CHECK (detectability BETWEEN 1 AND 5)
);

CREATE INDEX idx_assessment_history
ON risk_assessment_history(risk_id, assessed_at DESC);

-- ============================================================================
-- 7. GOVERNANCE POLICIES
-- ============================================================================

CREATE TABLE risk_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    policy_name VARCHAR(150) NOT NULL,

    require_evidence BOOLEAN NOT NULL DEFAULT TRUE,
    require_active_owner BOOLEAN NOT NULL DEFAULT TRUE,

    maximum_accepted_inherent_score SMALLINT NOT NULL DEFAULT 39,

    senior_review_threshold SMALLINT NOT NULL DEFAULT 40,

    require_verified_controls_for_mitigation BOOLEAN NOT NULL DEFAULT TRUE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (organization_id, policy_name),

    CHECK (maximum_accepted_inherent_score BETWEEN 1 AND 125),
    CHECK (senior_review_threshold BETWEEN 1 AND 125)
);

-- ============================================================================
-- 8. SCORING FUNCTIONS
-- ============================================================================

CREATE FUNCTION calculate_inherent_score(
    p_probability INTEGER,
    p_impact INTEGER,
    p_detectability INTEGER
)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_probability NOT BETWEEN 1 AND 5
       OR p_impact NOT BETWEEN 1 AND 5
       OR p_detectability NOT BETWEEN 1 AND 5 THEN
        RAISE EXCEPTION
            'Probability, impact and detectability must be between 1 and 5';
    END IF;

    RETURN p_probability * p_impact * p_detectability;
END;
$$;

CREATE FUNCTION classify_risk(
    p_score NUMERIC
)
RETURNS risk_level
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_score >= 75 THEN
        RETURN 'critical';
    ELSIF p_score >= 40 THEN
        RETURN 'high';
    ELSIF p_score >= 15 THEN
        RETURN 'moderate';
    ELSE
        RETURN 'low';
    END IF;
END;
$$;

-- ============================================================================
-- 9. INHERENT AND RESIDUAL EXPOSURE
-- ============================================================================

CREATE VIEW v_risk_assessment AS
SELECT
    r.risk_id,
    r.organization_id,
    r.risk_code,
    r.title,
    r.description,
    r.category,
    r.source,
    r.owner_id,
    u.full_name AS risk_owner,
    r.status,

    r.probability,
    r.impact,
    r.detectability,

    r.probability * r.impact * r.detectability
        AS inherent_score,

    classify_risk(
        r.probability * r.impact * r.detectability
    ) AS inherent_level,

    COALESCE(
        1 - EXP(
            SUM(
                CASE
                    WHEN rc.implementation_status = 'implemented'
                         AND rc.verified = TRUE
                    THEN LN(1 - rc.effectiveness)
                    WHEN rc.implementation_status = 'implemented'
                         AND rc.effectiveness = 1
                         AND rc.verified = TRUE
                    THEN '-Infinity'::DOUBLE PRECISION
                    ELSE 0
                END
            )
        ),
        0
    ) AS control_effectiveness,

    (
        r.probability * r.impact * r.detectability
    ) * (
        1 - COALESCE(
            1 - EXP(
                SUM(
                    CASE
                        WHEN rc.implementation_status = 'implemented'
                             AND rc.verified = TRUE
                        THEN LN(1 - rc.effectiveness)
                        WHEN rc.implementation_status = 'implemented'
                             AND rc.effectiveness = 1
                             AND rc.verified = TRUE
                        THEN '-Infinity'::DOUBLE PRECISION
                        ELSE 0
                    END
                )
            ),
            0
        )
    ) AS residual_score

FROM risks r
JOIN users u
    ON u.user_id = r.owner_id
LEFT JOIN risk_controls rc
    ON rc.risk_id = r.risk_id
GROUP BY
    r.risk_id,
    r.organization_id,
    r.risk_code,
    r.title,
    r.description,
    r.category,
    r.source,
    r.owner_id,
    u.full_name,
    r.status,
    r.probability,
    r.impact,
    r.detectability;

CREATE VIEW v_risk_priority AS
SELECT
    assessment.*,
    classify_risk(residual_score) AS residual_level
FROM v_risk_assessment assessment;

-- ============================================================================
-- 10. RISK STATUS TRANSITION VALIDATION
-- ============================================================================

CREATE FUNCTION enforce_risk_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status <> OLD.status THEN

        IF NOT (
            (OLD.status = 'identified'
                AND NEW.status IN (
                    'assessed', 'under_review', 'closed'
                ))
            OR
            (OLD.status = 'assessed'
                AND NEW.status IN (
                    'under_review', 'mitigated', 'accepted', 'closed'
                ))
            OR
            (OLD.status = 'under_review'
                AND NEW.status IN (
                    'assessed', 'mitigated', 'accepted', 'closed'
                ))
            OR
            (OLD.status = 'mitigated'
                AND NEW.status IN (
                    'under_review', 'closed'
                ))
            OR
            (OLD.status = 'accepted'
                AND NEW.status IN (
                    'under_review', 'closed'
                ))
        ) THEN
            RAISE EXCEPTION
                'Invalid risk transition: % to %',
                OLD.status,
                NEW.status;
        END IF;

        NEW.last_reviewed_at = CURRENT_TIMESTAMP;
        NEW.version = OLD.version + 1;

        IF NEW.status = 'closed' THEN
            NEW.closed_at = CURRENT_TIMESTAMP;
        ELSE
            NEW.closed_at = NULL;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_risk_transition
BEFORE UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION enforce_risk_transition();

-- ============================================================================
-- 11. ASSESSMENT HISTORY AUTOMATION
-- ============================================================================

CREATE FUNCTION record_assessment_history()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF
        NEW.probability IS DISTINCT FROM OLD.probability
        OR NEW.impact IS DISTINCT FROM OLD.impact
        OR NEW.detectability IS DISTINCT FROM OLD.detectability
    THEN
        INSERT INTO risk_assessment_history (
            risk_id,
            assessed_by,
            probability,
            impact,
            detectability,
            assessment_reason
        )
        VALUES (
            NEW.risk_id,
            NEW.owner_id,
            NEW.probability,
            NEW.impact,
            NEW.detectability,
            'Assessment dimensions updated.'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_assessment_history
AFTER UPDATE ON risks
FOR EACH ROW
EXECUTE FUNCTION record_assessment_history();

-- ============================================================================
-- 12. RISK ELIGIBILITY FUNCTION
-- ============================================================================

CREATE FUNCTION evaluate_risk_eligibility(
    p_risk_id BIGINT
)
RETURNS TABLE (
    risk_id BIGINT,
    eligible BOOLEAN,
    findings TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_risk risks%ROWTYPE;
    v_policy risk_policies%ROWTYPE;
    v_findings TEXT[] := ARRAY[]::TEXT[];
    v_score INTEGER;
    v_evidence_count INTEGER;
    v_verified_controls INTEGER;
    v_owner_active BOOLEAN;
BEGIN
    SELECT *
    INTO v_risk
    FROM risks
    WHERE risks.risk_id = p_risk_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Risk % does not exist', p_risk_id;
    END IF;

    SELECT *
    INTO v_policy
    FROM risk_policies
    WHERE organization_id = v_risk.organization_id
      AND active = TRUE
    ORDER BY policy_id DESC
    LIMIT 1;

    IF NOT FOUND THEN
        v_findings := array_append(
            v_findings,
            'No active governance policy exists.'
        );

        RETURN QUERY
        SELECT p_risk_id, FALSE, v_findings;

        RETURN;
    END IF;

    v_score := calculate_inherent_score(
        v_risk.probability,
        v_risk.impact,
        v_risk.detectability
    );

    SELECT COUNT(*)
    INTO v_evidence_count
    FROM risk_evidence
    WHERE risk_evidence.risk_id = p_risk_id;

    SELECT COUNT(*)
    INTO v_verified_controls
    FROM risk_controls
    WHERE risk_controls.risk_id = p_risk_id
      AND verified = TRUE
      AND implementation_status = 'implemented';

    SELECT active
    INTO v_owner_active
    FROM users
    WHERE user_id = v_risk.owner_id;

    IF v_policy.require_evidence AND v_evidence_count = 0 THEN
        v_findings := array_append(
            v_findings,
            'Supporting evidence is required.'
        );
    END IF;

    IF v_policy.require_active_owner
       AND COALESCE(v_owner_active, FALSE) = FALSE THEN
        v_findings := array_append(
            v_findings,
            'An active risk owner is required.'
        );
    END IF;

    IF v_score >= v_policy.senior_review_threshold
       AND v_risk.status NOT IN (
           'under_review',
           'mitigated',
           'accepted'
       ) THEN
        v_findings := array_append(
            v_findings,
            'Senior review is required.'
        );
    END IF;

    IF v_risk.status = 'accepted'
       AND v_score > v_policy.maximum_accepted_inherent_score THEN
        v_findings := array_append(
            v_findings,
            'Risk exceeds the permitted acceptance threshold.'
        );
    END IF;

    IF v_risk.status = 'mitigated'
       AND v_policy.require_verified_controls_for_mitigation
       AND v_verified_controls = 0 THEN
        v_findings := array_append(
            v_findings,
            'Mitigated status requires a verified implemented control.'
        );
    END IF;

    RETURN QUERY
    SELECT
        p_risk_id,
        cardinality(v_findings) = 0,
        v_findings;
END;
$$;

-- ============================================================================
-- 13. WORKFLOW PROCEDURE
-- ============================================================================

CREATE PROCEDURE reassess_risk(
    p_risk_id BIGINT,
    p_probability SMALLINT,
    p_impact SMALLINT,
    p_detectability SMALLINT,
    p_reason TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_probability NOT BETWEEN 1 AND 5
       OR p_impact NOT BETWEEN 1 AND 5
       OR p_detectability NOT BETWEEN 1 AND 5 THEN
        RAISE EXCEPTION 'Invalid risk assessment dimensions.';
    END IF;

    IF length(trim(p_reason)) = 0 THEN
        RAISE EXCEPTION 'Assessment reason is required.';
    END IF;

    UPDATE risks
    SET
        probability = p_probability,
        impact = p_impact,
        detectability = p_detectability,
        status = 'assessed'
    WHERE risk_id = p_risk_id
      AND status IN ('identified', 'assessed', 'under_review');

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Risk does not exist or cannot be reassessed in its current state.';
    END IF;

    UPDATE risk_assessment_history
    SET assessment_reason = p_reason
    WHERE assessment_id = (
        SELECT assessment_id
        FROM risk_assessment_history
        WHERE risk_id = p_risk_id
        ORDER BY assessment_id DESC
        LIMIT 1
    );
END;
$$;

-- ============================================================================
-- 14. SAMPLE ORGANIZATION AND USERS
-- ============================================================================

INSERT INTO organizations (
    organization_name,
    industry
)
VALUES (
    'Enterprise Digital Operations',
    'Information Technology'
);

INSERT INTO users (
    organization_id,
    full_name,
    email,
    job_role
)
SELECT
    organization_id,
    sample.full_name,
    sample.email,
    sample.job_role
FROM organizations
CROSS JOIN (
    VALUES
        (
            'Security Operations Manager',
            'security.manager@example.org',
            'Security Manager'
        ),
        (
            'Vendor Management Lead',
            'vendor.lead@example.org',
            'Vendor Manager'
        ),
        (
            'Compliance Officer',
            'compliance.officer@example.org',
            'Compliance Officer'
        ),
        (
            'Risk Governance Director',
            'risk.director@example.org',
            'Risk Director'
        )
) AS sample(full_name, email, job_role)
WHERE organization_name = 'Enterprise Digital Operations';

-- ============================================================================
-- 15. GOVERNANCE POLICY
-- ============================================================================

INSERT INTO risk_policies (
    organization_id,
    policy_name,
    require_evidence,
    require_active_owner,
    maximum_accepted_inherent_score,
    senior_review_threshold,
    require_verified_controls_for_mitigation
)
SELECT
    organization_id,
    'Enterprise Risk Governance Policy',
    TRUE,
    TRUE,
    39,
    40,
    TRUE
FROM organizations
WHERE organization_name = 'Enterprise Digital Operations';

-- ============================================================================
-- 16. CONTROL CATALOGUE
-- ============================================================================

INSERT INTO controls (
    organization_id,
    control_code,
    control_name,
    description,
    control_category
)
SELECT
    organization_id,
    sample.control_code,
    sample.control_name,
    sample.description,
    sample.control_category::control_type
FROM organizations
CROSS JOIN (
    VALUES
        (
            'CTRL-MFA',
            'Multi-factor authentication',
            'Enforce strong authentication for privileged accounts.',
            'preventive'
        ),
        (
            'CTRL-MON',
            'Privileged activity monitoring',
            'Monitor privileged account activity and anomalies.',
            'detective'
        ),
        (
            'CTRL-BCP',
            'Supplier continuity planning',
            'Maintain continuity and alternative supplier arrangements.',
            'corrective'
        )
) AS sample(
    control_code,
    control_name,
    description,
    control_category
)
WHERE organization_name = 'Enterprise Digital Operations';

-- ============================================================================
-- 17. SAMPLE RISK IDENTIFICATION
-- ============================================================================

INSERT INTO risks (
    organization_id,
    risk_code,
    title,
    description,
    context_description,
    category,
    source,
    owner_id,
    probability,
    impact,
    detectability
)
SELECT
    o.organization_id,
    sample.risk_code,
    sample.title,
    sample.description,
    sample.context_description,
    sample.category::risk_category,
    sample.source::identification_source,
    u.user_id,
    sample.probability,
    sample.impact,
    sample.detectability
FROM organizations o
JOIN (
    VALUES
        (
            'RISK-001',
            'Unauthorized production access',
            'Compromised credentials may expose sensitive production systems.',
            'Production infrastructure',
            'cybersecurity',
            'technical_analysis',
            'security.manager@example.org',
            4,
            5,
            4
        ),
        (
            'RISK-002',
            'Critical supplier interruption',
            'A third-party outage may interrupt essential operations.',
            'Cloud service dependencies',
            'third_party',
            'historical_data',
            'vendor.lead@example.org',
            4,
            4,
            3
        ),
        (
            'RISK-003',
            'Regulatory reporting failure',
            'Incomplete records may delay regulatory submissions.',
            'Regulatory reporting',
            'compliance',
            'interview',
            'compliance.officer@example.org',
            2,
            5,
            3
        ),
        (
            'RISK-004',
            'Operational capacity shortage',
            'Insufficient operational staffing may delay service delivery.',
            'Enterprise operations',
            'operational',
            'workshop',
            'vendor.lead@example.org',
            3,
            3,
            2
        )
) AS sample(
    risk_code,
    title,
    description,
    context_description,
    category,
    source,
    owner_email,
    probability,
    impact,
    detectability
)
    ON TRUE
JOIN users u
    ON u.organization_id = o.organization_id
   AND u.email = sample.owner_email
WHERE o.organization_name = 'Enterprise Digital Operations';

-- ============================================================================
-- 18. SUPPORTING EVIDENCE
-- ============================================================================

INSERT INTO risk_evidence (
    risk_id,
    organization_id,
    evidence_reference,
    description,
    source,
    collected_by
)
SELECT
    r.risk_id,
    r.organization_id,
    sample.evidence_reference,
    sample.description,
    sample.source::identification_source,
    u.user_id
FROM (
    VALUES
        (
            'RISK-001',
            'AUDIT-2026-014',
            'Privileged accounts lack consistent MFA enforcement.',
            'audit',
            'security.manager@example.org'
        ),
        (
            'RISK-002',
            'INCIDENT-2026-022',
            'Previous supplier outages exceeded recovery targets.',
            'incident',
            'vendor.lead@example.org'
        ),
        (
            'RISK-003',
            'INTERVIEW-2026-003',
            'Reporting dependency gaps identified in interviews.',
            'interview',
            'compliance.officer@example.org'
        )
) AS sample(
    risk_code,
    evidence_reference,
    description,
    source,
    collector_email
)
JOIN risks r
    ON r.risk_code = sample.risk_code
JOIN users u
    ON u.organization_id = r.organization_id
   AND u.email = sample.collector_email;

-- ============================================================================
-- 19. ASSIGN CONTROLS TO RISKS
-- ============================================================================

INSERT INTO risk_controls (
    risk_id,
    organization_id,
    control_id,
    effectiveness,
    implementation_status,
    verified,
    verified_at
)
SELECT
    r.risk_id,
    r.organization_id,
    c.control_id,
    sample.effectiveness,
    'implemented',
    TRUE,
    CURRENT_TIMESTAMP
FROM (
    VALUES
        ('RISK-001', 'CTRL-MFA', 0.55),
        ('RISK-001', 'CTRL-MON', 0.30),
        ('RISK-002', 'CTRL-BCP', 0.45)
) AS sample(risk_code, control_code, effectiveness)
JOIN risks r
    ON r.risk_code = sample.risk_code
JOIN controls c
    ON c.organization_id = r.organization_id
   AND c.control_code = sample.control_code;

-- ============================================================================
-- 20. INITIAL ASSESSMENT RECORDS
-- ============================================================================

INSERT INTO risk_assessment_history (
    risk_id,
    assessed_by,
    probability,
    impact,
    detectability,
    assessment_reason
)
SELECT
    r.risk_id,
    r.owner_id,
    r.probability,
    r.impact,
    r.detectability,
    'Initial risk identification and assessment.'
FROM risks r;

-- ============================================================================
-- 21. RETRIEVAL AND PRIORITIZATION
-- ============================================================================

-- Highest inherent exposure first.
SELECT
    risk_code,
    title,
    category,
    risk_owner,
    inherent_score,
    inherent_level,
    ROUND(residual_score::NUMERIC, 2) AS residual_score,
    residual_level,
    status
FROM v_risk_priority
ORDER BY inherent_score DESC, risk_code;

-- Filter cybersecurity risks.
SELECT *
FROM v_risk_priority
WHERE category = 'cybersecurity'
ORDER BY inherent_score DESC;

-- Find risks assigned to a specific owner.
SELECT
    risk_code,
    title,
    risk_owner,
    status,
    inherent_score
FROM v_risk_priority
WHERE risk_owner = 'Security Operations Manager';

-- ============================================================================
-- 22. CATEGORY AGGREGATION
-- ============================================================================

SELECT
    category,
    COUNT(*) AS total_risks,
    ROUND(AVG(inherent_score), 2) AS average_inherent_score,
    MAX(inherent_score) AS maximum_inherent_score,
    COUNT(*) FILTER (
        WHERE inherent_level IN ('high', 'critical')
    ) AS high_and_critical_risks
FROM v_risk_priority
GROUP BY category
ORDER BY total_risks DESC;

-- ============================================================================
-- 23. STATUS AGGREGATION
-- ============================================================================

SELECT
    status,
    COUNT(*) AS risk_count
FROM risks
GROUP BY status
ORDER BY risk_count DESC;

-- ============================================================================
-- 24. EVIDENCE COMPLETENESS
-- ============================================================================

SELECT
    r.risk_code,
    r.title,
    COUNT(e.evidence_id) AS evidence_count,
    CASE
        WHEN COUNT(e.evidence_id) = 0 THEN 'EVIDENCE MISSING'
        ELSE 'SUPPORTED'
    END AS evidence_status
FROM risks r
LEFT JOIN risk_evidence e
    ON e.risk_id = r.risk_id
GROUP BY r.risk_id, r.risk_code, r.title
ORDER BY evidence_count ASC;

-- ============================================================================
-- 25. CONTROL COVERAGE
-- ============================================================================

SELECT
    r.risk_code,
    r.title,
    COUNT(rc.risk_control_id) AS assigned_controls,
    COUNT(rc.risk_control_id) FILTER (
        WHERE rc.verified = TRUE
          AND rc.implementation_status = 'implemented'
    ) AS verified_controls,
    COALESCE(
        ROUND(
            AVG(rc.effectiveness) FILTER (
                WHERE rc.verified = TRUE
                  AND rc.implementation_status = 'implemented'
            ),
            3
        ),
        0
    ) AS average_verified_effectiveness
FROM risks r
LEFT JOIN risk_controls rc
    ON rc.risk_id = r.risk_id
GROUP BY r.risk_id, r.risk_code, r.title
ORDER BY r.risk_code;

-- ============================================================================
-- 26. IDENTIFICATION SOURCE ANALYSIS
-- ============================================================================

SELECT
    source,
    COUNT(*) AS identified_risks,
    COUNT(*) FILTER (
        WHERE probability * impact * detectability >= 40
    ) AS high_priority_risks,
    ROUND(
        AVG(probability * impact * detectability),
        2
    ) AS average_exposure
FROM risks
GROUP BY source
ORDER BY identified_risks DESC;

-- ============================================================================
-- 27. ELIGIBILITY EVALUATION
-- ============================================================================

SELECT
    r.risk_code,
    r.title,
    eligibility.eligible,
    eligibility.findings
FROM risks r
CROSS JOIN LATERAL evaluate_risk_eligibility(r.risk_id) eligibility
ORDER BY r.risk_code;

-- ============================================================================
-- 28. TRANSACTIONAL REASSESSMENT EXAMPLE
-- ============================================================================

-- This transaction is committed only if the reassessment succeeds.

SAVEPOINT before_reassessment;

CALL reassess_risk(
    (
        SELECT risk_id
        FROM risks
        WHERE risk_code = 'RISK-002'
    ),
    3,
    4,
    3,
    'Updated assessment following supplier continuity review.'
);

-- The procedure updates the assessment dimensions and records history.

-- Release the savepoint after successful processing.
RELEASE SAVEPOINT before_reassessment;

-- ============================================================================
-- 29. RISK IDENTIFICATION COMPLETENESS REPORT
-- ============================================================================

SELECT
    r.risk_code,
    r.title,
    r.category,
    r.source,
    r.status,

    CASE
        WHEN r.description IS NULL
             OR length(trim(r.description)) = 0
        THEN FALSE
        ELSE TRUE
    END AS description_complete,

    CASE
        WHEN r.context_description IS NULL
             OR length(trim(r.context_description)) = 0
        THEN FALSE
        ELSE TRUE
    END AS context_complete,

    EXISTS (
        SELECT 1
        FROM risk_evidence e
        WHERE e.risk_id = r.risk_id
    ) AS has_evidence,

    EXISTS (
        SELECT 1
        FROM users u
        WHERE u.user_id = r.owner_id
          AND u.active = TRUE
    ) AS has_active_owner,

    calculate_inherent_score(
        r.probability,
        r.impact,
        r.detectability
    ) AS exposure_score

FROM risks r
ORDER BY exposure_score DESC;

COMMIT;
