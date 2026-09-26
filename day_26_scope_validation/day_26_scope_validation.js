"use strict";

/*
 * Scope Validation: Checking Completed Work Against Requirements
 *
 * This executable JavaScript study demonstrates:
 * - requirements and acceptance criteria
 * - completion versus validation
 * - evidence and traceability
 * - scope boundaries
 * - validation rules
 * - edge cases
 * - asynchronous validation
 * - error handling
 * - performance-oriented indexing
 * - browser/application-oriented validation patterns
 *
 * Run with:
 *   node scope-validation.js
 */

// -----------------------------------------------------------------------------
// 1. FUNDAMENTAL DATA STRUCTURES
// -----------------------------------------------------------------------------

const RequirementType = Object.freeze({
    FUNCTIONAL: "functional",
    NON_FUNCTIONAL: "non-functional",
    COMPLIANCE: "compliance",
    CONSTRAINT: "constraint"
});

const RequirementStatus = Object.freeze({
    NOT_STARTED: "not_started",
    IN_PROGRESS: "in_progress",
    COMPLETE: "complete",
    BLOCKED: "blocked"
});

const Severity = Object.freeze({
    LOW: "low",
    MEDIUM: "medium",
    HIGH: "high",
    CRITICAL: "critical"
});

function createRequirement({
    id,
    description,
    type = RequirementType.FUNCTIONAL,
    mandatory = true,
    acceptanceCriteria = [],
    dependencies = [],
    status = RequirementStatus.NOT_STARTED
}) {
    if (!id || !description) {
        throw new Error("Requirement ID and description are required.");
    }

    return {
        id,
        description,
        type,
        mandatory,
        acceptanceCriteria,
        dependencies,
        status
    };
}

function createEvidence({
    id,
    requirementId,
    description,
    source,
    valid = true
}) {
    if (!id || !requirementId || !description || !source) {
        throw new Error("Evidence must contain an ID, requirement, description, and source.");
    }

    return {
        id,
        requirementId,
        description,
        source,
        valid
    };
}

// -----------------------------------------------------------------------------
// 2. BASIC VALIDATION
// -----------------------------------------------------------------------------

function isComplete(requirement) {
    return requirement.status === RequirementStatus.COMPLETE;
}

function findIncompleteMandatoryRequirements(requirements) {
    return requirements
        .filter(
            requirement =>
                requirement.mandatory &&
                !isComplete(requirement)
        )
        .map(requirement => requirement.id);
}

// -----------------------------------------------------------------------------
// 3. ACCEPTANCE CRITERIA
// -----------------------------------------------------------------------------

function validateAcceptanceCriteria(requirement, completedCriteria) {
    const completed = new Set(completedCriteria);

    const missing = requirement.acceptanceCriteria.filter(
        criterion => !completed.has(criterion)
    );

    return {
        passed: missing.length === 0,
        missing
    };
}

// -----------------------------------------------------------------------------
// 4. TRACEABILITY INDEX
// -----------------------------------------------------------------------------

class EvidenceIndex {
    constructor(evidence) {
        this.byRequirement = new Map();

        for (const item of evidence) {
            if (!item.valid) {
                continue;
            }

            if (!this.byRequirement.has(item.requirementId)) {
                this.byRequirement.set(item.requirementId, []);
            }

            this.byRequirement.get(item.requirementId).push(item);
        }
    }

    get(requirementId) {
        return this.byRequirement.get(requirementId) || [];
    }
}

// -----------------------------------------------------------------------------
// 5. VALIDATION ENGINE
// -----------------------------------------------------------------------------

class ScopeValidationEngine {
    constructor(requirements, evidence, rules = []) {
        this.requirements = requirements;
        this.evidence = evidence;
        this.evidenceIndex = new EvidenceIndex(evidence);
        this.rules = rules;
    }

    validate() {
        const findings = [];
        let mandatorySatisfied = 0;
        let mandatoryTotal = 0;

        for (const requirement of this.requirements) {
            const matchingEvidence = this.evidenceIndex.get(requirement.id);

            if (requirement.mandatory) {
                mandatoryTotal++;

                if (
                    requirement.status === RequirementStatus.COMPLETE &&
                    matchingEvidence.length > 0
                ) {
                    mandatorySatisfied++;
                } else if (requirement.status !== RequirementStatus.COMPLETE) {
                    findings.push({
                        requirementId: requirement.id,
                        severity: Severity.HIGH,
                        message: "Mandatory requirement is not complete.",
                        evidenceIds: []
                    });
                } else {
                    findings.push({
                        requirementId: requirement.id,
                        severity: Severity.HIGH,
                        message: "Requirement is complete but lacks valid evidence.",
                        evidenceIds: []
                    });
                }
            }

            for (const rule of this.rules) {
                const finding = rule(requirement, matchingEvidence);

                if (finding) {
                    findings.push(finding);
                }
            }
        }

        const coverage =
            mandatoryTotal === 0
                ? 100
                : (mandatorySatisfied / mandatoryTotal) * 100;

        const hasBlockingFinding = findings.some(
            finding =>
                finding.severity === Severity.CRITICAL ||
                finding.severity === Severity.HIGH
        );

        return {
            passed: mandatorySatisfied === mandatoryTotal && !hasBlockingFinding,
            coveragePercent: Number(coverage.toFixed(2)),
            mandatoryTotal,
            mandatorySatisfied,
            findings
        };
    }
}

// -----------------------------------------------------------------------------
// 6. REUSABLE VALIDATION RULES
// -----------------------------------------------------------------------------

function rejectBlockedRequirements(requirement) {
    if (requirement.status === RequirementStatus.BLOCKED) {
        return {
            requirementId: requirement.id,
            severity: requirement.mandatory
                ? Severity.CRITICAL
                : Severity.MEDIUM,
            message: "Requirement is blocked.",
            evidenceIds: []
        };
    }

    return null;
}

function requireAcceptanceCriteriaEvidence(requirement, evidence) {
    if (
        requirement.status === RequirementStatus.COMPLETE &&
        requirement.acceptanceCriteria.length > 0 &&
        evidence.length === 0
    ) {
        return {
            requirementId: requirement.id,
            severity: Severity.MEDIUM,
            message: "Acceptance criteria exist but no validation evidence is attached.",
            evidenceIds: []
        };
    }

    return null;
}

// -----------------------------------------------------------------------------
// 7. SCOPE BOUNDARY ANALYSIS
// -----------------------------------------------------------------------------

function analyzeScope(approvedScope, completedWork) {
    const approved = new Set(approvedScope);
    const completed = new Set(completedWork);

    const deliveredInScope = [...completed].filter(item => approved.has(item));
    const completedOutsideScope = [...completed].filter(item => !approved.has(item));
    const missingFromApprovedScope = [...approved].filter(item => !completed.has(item));

    return {
        deliveredInScope,
        completedOutsideScope,
        missingFromApprovedScope
    };
}

// -----------------------------------------------------------------------------
// 8. REQUIREMENT MATRIX
// -----------------------------------------------------------------------------

function buildTraceabilityMatrix(requirements, evidenceIndex) {
    return requirements.map(requirement => {
        const evidence = evidenceIndex.get(requirement.id);

        return {
            id: requirement.id,
            description: requirement.description,
            type: requirement.type,
            mandatory: requirement.mandatory,
            status: requirement.status,
            evidenceCount: evidence.length,
            traceable: evidence.length > 0
        };
    });
}

function printMatrix(matrix) {
    console.log("\nRequirement Traceability Matrix");
    console.log("-".repeat(110));

    for (const row of matrix) {
        console.log(
            `${row.id.padEnd(10)} | ` +
            `${String(row.mandatory).padEnd(9)} | ` +
            `${row.status.padEnd(12)} | ` +
            `${String(row.evidenceCount).padEnd(8)} | ` +
            `${String(row.traceable).padEnd(9)} | ` +
            row.description
        );
    }
}

// -----------------------------------------------------------------------------
// 9. ASYNCHRONOUS VALIDATION
// -----------------------------------------------------------------------------

function delay(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function validateExternalEvidence(evidence) {
    // A real application could query a CI server, test service, database,
    // document store, or audit system here.
    await delay(5);

    if (!evidence || !evidence.valid) {
        throw new Error("External evidence is invalid.");
    }

    return {
        evidenceId: evidence.id,
        verified: true,
        source: evidence.source
    };
}

async function asynchronouslyValidateEvidence(evidence) {
    const results = [];

    for (const item of evidence) {
        try {
            results.push(await validateExternalEvidence(item));
        } catch (error) {
            results.push({
                evidenceId: item.id,
                verified: false,
                error: error.message
            });
        }
    }

    return results;
}

// -----------------------------------------------------------------------------
// 10. BROWSER-SIDE VALIDATION PATTERN
// -----------------------------------------------------------------------------

function validateRenderedScope(requiredSelectors, documentObject) {
    if (!documentObject) {
        return {
            passed: false,
            missing: requiredSelectors,
            message: "A browser document is required."
        };
    }

    const missing = requiredSelectors.filter(
        selector => !documentObject.querySelector(selector)
    );

    return {
        passed: missing.length === 0,
        missing
    };
}

// -----------------------------------------------------------------------------
// 11. SECURITY-ORIENTED EVIDENCE VALIDATION
// -----------------------------------------------------------------------------

function validateEvidenceIntegrity(evidence) {
    if (!evidence || typeof evidence !== "object") {
        return false;
    }

    return Boolean(
        typeof evidence.id === "string" &&
        evidence.id.trim() &&
        typeof evidence.requirementId === "string" &&
        evidence.requirementId.trim() &&
        typeof evidence.description === "string" &&
        evidence.description.trim() &&
        typeof evidence.source === "string" &&
        evidence.source.trim() &&
        evidence.valid === true
    );
}

// -----------------------------------------------------------------------------
// 12. PERFORMANCE DEMONSTRATION
// -----------------------------------------------------------------------------

function createLargeEvidenceSet(count) {
    const evidence = [];

    for (let index = 0; index < count; index++) {
        evidence.push({
            id: `EV-${index}`,
            requirementId: `REQ-${index % 1000}`,
            description: "Automated validation evidence",
            source: "test-system",
            valid: true
        });
    }

    return evidence;
}

function benchmarkIndexing() {
    const evidence = createLargeEvidenceSet(100000);

    const start = performance.now();
    const index = new EvidenceIndex(evidence);
    const elapsed = performance.now() - start;

    console.log("\nPerformance-oriented indexing");
    console.log(`Evidence records: ${evidence.length}`);
    console.log(`Indexed requirement keys: ${index.byRequirement.size}`);
    console.log(`Index construction time: ${elapsed.toFixed(3)} ms`);
}

// -----------------------------------------------------------------------------
// 13. COMPLETE CASE STUDY
// -----------------------------------------------------------------------------

function createCaseStudy() {
    const requirements = [
        createRequirement({
            id: "REQ-001",
            description: "Users can authenticate.",
            acceptanceCriteria: [
                "valid credentials accepted",
                "invalid credentials rejected"
            ],
            status: RequirementStatus.COMPLETE
        }),
        createRequirement({
            id: "REQ-002",
            description: "Users can reset passwords.",
            acceptanceCriteria: [
                "reset token generated",
                "expired token rejected"
            ],
            status: RequirementStatus.COMPLETE
        }),
        createRequirement({
            id: "REQ-003",
            description: "Security events are audited.",
            type: RequirementType.COMPLIANCE,
            acceptanceCriteria: [
                "successful authentication is recorded"
            ],
            status: RequirementStatus.COMPLETE
        }),
        createRequirement({
            id: "REQ-004",
            description: "Dark mode is available.",
            mandatory: false,
            acceptanceCriteria: [
                "dark theme renders"
            ],
            status: RequirementStatus.COMPLETE
        }),
        createRequirement({
            id: "REQ-005",
            description: "API latency meets the agreed threshold.",
            type: RequirementType.NON_FUNCTIONAL,
            status: RequirementStatus.IN_PROGRESS
        })
    ];

    const evidence = [
        createEvidence({
            id: "EV-001",
            requirementId: "REQ-001",
            description: "Authentication acceptance tests passed.",
            source: "CI pipeline"
        }),
        createEvidence({
            id: "EV-002",
            requirementId: "REQ-002",
            description: "Password reset tests passed.",
            source: "CI pipeline"
        }),
        createEvidence({
            id: "EV-003",
            requirementId: "REQ-003",
            description: "Audit verification passed.",
            source: "compliance test"
        }),
        createEvidence({
            id: "EV-004",
            requirementId: "REQ-004",
            description: "Browser rendering test passed.",
            source: "browser test"
        })
    ];

    return { requirements, evidence };
}

// -----------------------------------------------------------------------------
// 14. RELEASE GATE
// -----------------------------------------------------------------------------

function determineReleaseDecision(validationResult) {
    if (
        validationResult.findings.some(
            finding => finding.severity === Severity.CRITICAL
        )
    ) {
        return "BLOCKED: critical finding requires resolution.";
    }

    if (!validationResult.passed) {
        return "NOT READY: mandatory scope has not been fully validated.";
    }

    return "VALIDATED: mandatory requirements have supporting evidence.";
}

// -----------------------------------------------------------------------------
// 15. ERROR HANDLING DEMONSTRATION
// -----------------------------------------------------------------------------

function demonstrateErrorHandling() {
    try {
        createRequirement({
            id: "",
            description: ""
        });
    } catch (error) {
        console.log("\nValidation input error handled:", error.message);
    }
}

// -----------------------------------------------------------------------------
// 16. MAIN
// -----------------------------------------------------------------------------

async function main() {
    console.log("=".repeat(90));
    console.log("SCOPE VALIDATION STUDY PROGRAM");
    console.log("=".repeat(90));

    const { requirements, evidence } = createCaseStudy();

    const basicFailures = findIncompleteMandatoryRequirements(requirements);

    console.log("\nIncomplete mandatory requirements:");
    console.log(basicFailures);

    const criteriaResult = validateAcceptanceCriteria(
        requirements[0],
        [
            "valid credentials accepted",
            "invalid credentials rejected"
        ]
    );

    console.log("\nAcceptance criteria result:");
    console.log(criteriaResult);

    const engine = new ScopeValidationEngine(
        requirements,
        evidence,
        [
            rejectBlockedRequirements,
            requireAcceptanceCriteriaEvidence
        ]
    );

    const validationResult = engine.validate();

    console.log("\nValidation result:");
    console.log(JSON.stringify(validationResult, null, 2));

    const matrix = buildTraceabilityMatrix(
        requirements,
        engine.evidenceIndex
    );

    printMatrix(matrix);

    const scopeResult = analyzeScope(
        [
            "authentication",
            "password reset",
            "audit logging"
        ],
        [
            "authentication",
            "password reset",
            "audit logging",
            "dark mode",
            "CSV export"
        ]
    );

    console.log("\nScope boundary analysis:");
    console.log(JSON.stringify(scopeResult, null, 2));

    const externalEvidenceResults =
        await asynchronouslyValidateEvidence(evidence);

    console.log("\nAsynchronous evidence verification:");
    console.log(externalEvidenceResults);

    console.log("\nEvidence integrity:");
    for (const item of evidence) {
        console.log(item.id, validateEvidenceIntegrity(item));
    }

    console.log("\nRelease decision:");
    console.log(determineReleaseDecision(validationResult));

    demonstrateErrorHandling();
    benchmarkIndexing();

    console.log("\nCore distinctions:");
    console.log("1. Completion describes a claimed state.");
    console.log("2. Validation tests that state against defined requirements.");
    console.log("3. Evidence establishes traceability.");
    console.log("4. Scope creep is work outside the approved boundary.");
    console.log("5. A release gate should be based on explicit validation rules.");
}

main().catch(error => {
    console.error("Fatal validation error:", error.message);
    process.exitCode = 1;
});
