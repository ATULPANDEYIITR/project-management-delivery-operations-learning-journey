/**
 * Scope Control: Managing Changes to Scope
 *
 * A self-contained JavaScript study and implementation demonstrating:
 * - Scope baselines
 * - Requirements and deliverables
 * - Change requests
 * - Impact analysis
 * - Governance and routing
 * - Approval and rejection
 * - Implementation
 * - Rebaselining
 * - Traceability
 * - Scope-creep detection
 * - Validation
 * - Performance considerations
 *
 * Runs with a modern JavaScript runtime such as Node.js.
 */

"use strict";

// ---------------------------------------------------------------------------
// 1. ENUM-LIKE CONSTANTS
// ---------------------------------------------------------------------------

const ScopeStatus = Object.freeze({
    PLANNED: "Planned",
    IN_PROGRESS: "In Progress",
    COMPLETED: "Completed",
    REMOVED: "Removed"
});

const ChangeStatus = Object.freeze({
    PROPOSED: "Proposed",
    UNDER_REVIEW: "Under Review",
    APPROVED: "Approved",
    REJECTED: "Rejected",
    DEFERRED: "Deferred",
    IMPLEMENTED: "Implemented"
});

const Priority = Object.freeze({
    LOW: "Low",
    MEDIUM: "Medium",
    HIGH: "High",
    CRITICAL: "Critical"
});

function printSection(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}


// ---------------------------------------------------------------------------
// 2. VALIDATION HELPERS
// ---------------------------------------------------------------------------

function requireNonEmptyString(value, fieldName) {
    if (typeof value !== "string" || value.trim() === "") {
        throw new Error(`${fieldName} must be a non-empty string.`);
    }
}

function requireNonNegativeNumber(value, fieldName) {
    if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
        throw new Error(`${fieldName} must be a finite non-negative number.`);
    }
}

function requireRisk(value, fieldName) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0 ||
        value > 10
    ) {
        throw new Error(`${fieldName} must be between 0 and 10.`);
    }
}


// ---------------------------------------------------------------------------
// 3. BASIC DOMAIN OBJECTS
// ---------------------------------------------------------------------------

class Deliverable {
    constructor({
        id,
        name,
        description,
        estimatedHours,
        estimatedCost,
        status = ScopeStatus.PLANNED,
        requirements = []
    }) {
        requireNonEmptyString(id, "Deliverable ID");
        requireNonEmptyString(name, "Deliverable name");
        requireNonNegativeNumber(estimatedHours, "Estimated hours");
        requireNonNegativeNumber(estimatedCost, "Estimated cost");

        this.id = id;
        this.name = name;
        this.description = description;
        this.estimatedHours = estimatedHours;
        this.estimatedCost = estimatedCost;
        this.status = status;
        this.requirements = new Set(requirements);
    }

    clone() {
        return new Deliverable({
            id: this.id,
            name: this.name,
            description: this.description,
            estimatedHours: this.estimatedHours,
            estimatedCost: this.estimatedCost,
            status: this.status,
            requirements: [...this.requirements]
        });
    }
}


class Requirement {
    constructor({
        id,
        title,
        description,
        priority,
        acceptanceCriteria,
        deliverableIds = []
    }) {
        requireNonEmptyString(id, "Requirement ID");
        requireNonEmptyString(title, "Requirement title");

        if (!Array.isArray(acceptanceCriteria) || acceptanceCriteria.length === 0) {
            throw new Error(`${id} requires acceptance criteria.`);
        }

        this.id = id;
        this.title = title;
        this.description = description;
        this.priority = priority;
        this.acceptanceCriteria = [...acceptanceCriteria];
        this.deliverableIds = new Set(deliverableIds);
    }

    clone() {
        return new Requirement({
            id: this.id,
            title: this.title,
            description: this.description,
            priority: this.priority,
            acceptanceCriteria: [...this.acceptanceCriteria],
            deliverableIds: [...this.deliverableIds]
        });
    }
}


class ImpactAnalysis {
    constructor({
        scopeDelta,
        scheduleDeltaDays,
        costDelta,
        resourceDeltaHours,
        qualityRisk,
        technicalRisk,
        complianceRisk,
        operationalRisk,
        dependencies = [],
        assumptions = []
    }) {
        requireNonNegativeNumber(scopeDelta, "Scope delta");
        requireNonNegativeNumber(scheduleDeltaDays, "Schedule delta");
        requireNonNegativeNumber(costDelta, "Cost delta");
        requireNonNegativeNumber(resourceDeltaHours, "Resource delta");

        requireRisk(qualityRisk, "Quality risk");
        requireRisk(technicalRisk, "Technical risk");
        requireRisk(complianceRisk, "Compliance risk");
        requireRisk(operationalRisk, "Operational risk");

        this.scopeDelta = scopeDelta;
        this.scheduleDeltaDays = scheduleDeltaDays;
        this.costDelta = costDelta;
        this.resourceDeltaHours = resourceDeltaHours;
        this.qualityRisk = qualityRisk;
        this.technicalRisk = technicalRisk;
        this.complianceRisk = complianceRisk;
        this.operationalRisk = operationalRisk;
        this.dependencies = [...dependencies];
        this.assumptions = [...assumptions];
    }

    averageRisk() {
        return (
            this.qualityRisk +
            this.technicalRisk +
            this.complianceRisk +
            this.operationalRisk
        ) / 4;
    }

    netImpactScore() {
        return (
            this.averageRisk() * 2 +
            this.scheduleDeltaDays * 0.25 +
            this.costDelta / 10000
        );
    }
}


class ChangeRequest {
    constructor({
        id,
        title,
        requester,
        description,
        reason,
        priority,
        proposedDate = new Date().toISOString().slice(0, 10),
        affectedRequirements = [],
        affectedDeliverables = []
    }) {
        requireNonEmptyString(id, "Change ID");
        requireNonEmptyString(title, "Change title");
        requireNonEmptyString(requester, "Requester");
        requireNonEmptyString(description, "Change description");

        this.id = id;
        this.title = title;
        this.requester = requester;
        this.description = description;
        this.reason = reason;
        this.priority = priority;
        this.proposedDate = proposedDate;
        this.affectedRequirements = new Set(affectedRequirements);
        this.affectedDeliverables = new Set(affectedDeliverables);

        this.impact = null;
        this.status = ChangeStatus.PROPOSED;
        this.decision = "";
        this.decisionDate = null;
        this.implementationNotes = "";
    }

    attachImpact(impact) {
        if (!(impact instanceof ImpactAnalysis)) {
            throw new Error("Impact must be an ImpactAnalysis object.");
        }

        this.impact = impact;
        this.status = ChangeStatus.UNDER_REVIEW;
    }
}


// ---------------------------------------------------------------------------
// 4. SCOPE BASELINE
// ---------------------------------------------------------------------------

class ScopeBaseline {
    constructor({
        version,
        approvedDate,
        deliverables,
        requirements
    }) {
        this.version = version;
        this.approvedDate = approvedDate;
        this.deliverables = new Map(
            Object.entries(deliverables)
        );
        this.requirements = new Map(
            Object.entries(requirements)
        );

        this.validate();
    }

    validate() {
        for (const requirement of this.requirements.values()) {
            for (const deliverableId of requirement.deliverableIds) {
                if (!this.deliverables.has(deliverableId)) {
                    throw new Error(
                        `${requirement.id} references unknown deliverable ` +
                        `${deliverableId}.`
                    );
                }
            }
        }
    }

    totalHours() {
        let total = 0;

        for (const deliverable of this.deliverables.values()) {
            if (deliverable.status !== ScopeStatus.REMOVED) {
                total += deliverable.estimatedHours;
            }
        }

        return total;
    }

    totalCost() {
        let total = 0;

        for (const deliverable of this.deliverables.values()) {
            if (deliverable.status !== ScopeStatus.REMOVED) {
                total += deliverable.estimatedCost;
            }
        }

        return total;
    }

    clone(version, approvedDate) {
        const deliverables = {};

        for (const [id, deliverable] of this.deliverables.entries()) {
            deliverables[id] = deliverable.clone();
        }

        const requirements = {};

        for (const [id, requirement] of this.requirements.entries()) {
            requirements[id] = requirement.clone();
        }

        return new ScopeBaseline({
            version,
            approvedDate,
            deliverables,
            requirements
        });
    }
}


// ---------------------------------------------------------------------------
// 5. AUDIT TRAIL
// ---------------------------------------------------------------------------

class AuditLog {
    constructor() {
        this.entries = [];
    }

    record(actor, action, objectId, details) {
        this.entries.push({
            timestamp: new Date().toISOString(),
            actor,
            action,
            objectId,
            details
        });
    }
}


// ---------------------------------------------------------------------------
// 6. SCOPE CONTROL ENGINE
// ---------------------------------------------------------------------------

class ScopeControlEngine {
    constructor({
        baseline,
        approvalCostThreshold = 5000,
        approvalScheduleThreshold = 5,
        approvalRiskThreshold = 6
    }) {
        if (!(baseline instanceof ScopeBaseline)) {
            throw new Error("A valid ScopeBaseline is required.");
        }

        this.baseline = baseline;
        this.approvalCostThreshold = approvalCostThreshold;
        this.approvalScheduleThreshold = approvalScheduleThreshold;
        this.approvalRiskThreshold = approvalRiskThreshold;

        this.changeRequests = new Map();
        this.decisions = [];
        this.auditLog = new AuditLog();

        this.auditLog.record(
            "system",
            "CREATE_BASELINE",
            baseline.version,
            "Initial baseline created."
        );
    }

    submitChange(request) {
        if (!(request instanceof ChangeRequest)) {
            throw new Error("A ChangeRequest object is required.");
        }

        if (this.changeRequests.has(request.id)) {
            throw new Error(`Change ${request.id} already exists.`);
        }

        for (const requirementId of request.affectedRequirements) {
            if (!this.baseline.requirements.has(requirementId)) {
                throw new Error(
                    `Unknown requirement: ${requirementId}`
                );
            }
        }

        for (const deliverableId of request.affectedDeliverables) {
            if (!this.baseline.deliverables.has(deliverableId)) {
                throw new Error(
                    `Unknown deliverable: ${deliverableId}`
                );
            }
        }

        this.changeRequests.set(request.id, request);

        this.auditLog.record(
            request.requester,
            "SUBMIT_CHANGE",
            request.id,
            request.title
        );
    }

    analyzeChange(changeId, impact) {
        const request = this.getChange(changeId);

        if (
            request.status !== ChangeStatus.PROPOSED &&
            request.status !== ChangeStatus.UNDER_REVIEW
        ) {
            throw new Error(
                `Cannot analyze ${changeId} in status ${request.status}.`
            );
        }

        request.attachImpact(impact);

        this.auditLog.record(
            "change_analyst",
            "ANALYZE_CHANGE",
            changeId,
            `Cost +${impact.costDelta}, schedule +${impact.scheduleDeltaDays} days`
        );
    }

    routingRecommendation(changeId) {
        const request = this.getChange(changeId);

        if (!request.impact) {
            throw new Error("Impact analysis is required.");
        }

        const impact = request.impact;

        if (
            impact.costDelta > this.approvalCostThreshold ||
            impact.scheduleDeltaDays > this.approvalScheduleThreshold ||
            impact.averageRisk() >= this.approvalRiskThreshold ||
            request.priority === Priority.CRITICAL
        ) {
            return "Change Control Board";
        }

        return "Project Manager";
    }

    approve(changeId, authority, rationale) {
        const request = this.getChange(changeId);

        if (!request.impact) {
            throw new Error("Cannot approve without impact analysis.");
        }

        if (request.status !== ChangeStatus.UNDER_REVIEW) {
            throw new Error(
                `Only changes under review can be approved. ` +
                `Current status: ${request.status}`
            );
        }

        request.status = ChangeStatus.APPROVED;
        request.decision = rationale;
        request.decisionDate = new Date().toISOString().slice(0, 10);

        this.decisions.push({
            changeId,
            decision: ChangeStatus.APPROVED,
            authority,
            rationale,
            timestamp: new Date().toISOString()
        });

        this.auditLog.record(
            authority,
            "APPROVE_CHANGE",
            changeId,
            rationale
        );
    }

    reject(changeId, authority, rationale) {
        const request = this.getChange(changeId);

        if (request.status !== ChangeStatus.UNDER_REVIEW) {
            throw new Error(
                `Only changes under review can be rejected. ` +
                `Current status: ${request.status}`
            );
        }

        request.status = ChangeStatus.REJECTED;
        request.decision = rationale;
        request.decisionDate = new Date().toISOString().slice(0, 10);

        this.decisions.push({
            changeId,
            decision: ChangeStatus.REJECTED,
            authority,
            rationale,
            timestamp: new Date().toISOString()
        });

        this.auditLog.record(
            authority,
            "REJECT_CHANGE",
            changeId,
            rationale
        );
    }

    implement(changeId, implementer) {
        const request = this.getChange(changeId);

        if (request.status !== ChangeStatus.APPROVED) {
            throw new Error(
                "Only approved changes can be implemented."
            );
        }

        request.status = ChangeStatus.IMPLEMENTED;
        request.implementationNotes =
            `Implemented by ${implementer} on ` +
            `${new Date().toISOString().slice(0, 10)}.`;

        this.auditLog.record(
            implementer,
            "IMPLEMENT_CHANGE",
            changeId,
            request.implementationNotes
        );
    }

    rebaseline(newVersion, approvedDate) {
        for (const request of this.changeRequests.values()) {
            if (request.status === ChangeStatus.APPROVED) {
                throw new Error(
                    "All approved changes must be implemented before rebaselining."
                );
            }
        }

        const nextBaseline = this.baseline.clone(
            newVersion,
            approvedDate
        );

        for (const request of this.changeRequests.values()) {
            if (
                request.status !== ChangeStatus.IMPLEMENTED ||
                !request.impact
            ) {
                continue;
            }

            const deliverableId = `CHG-${request.id}`;

            if (!nextBaseline.deliverables.has(deliverableId)) {
                nextBaseline.deliverables.set(
                    deliverableId,
                    new Deliverable({
                        id: deliverableId,
                        name: request.title,
                        description: request.description,
                        estimatedHours:
                            request.impact.resourceDeltaHours,
                        estimatedCost:
                            request.impact.costDelta
                    })
                );
            }
        }

        this.baseline = nextBaseline;

        this.auditLog.record(
            "change_control_board",
            "CREATE_BASELINE",
            newVersion,
            "New baseline created from implemented changes."
        );

        return nextBaseline;
    }

    report() {
        const statusCounts = {};

        for (const status of Object.values(ChangeStatus)) {
            statusCounts[status] = 0;
        }

        for (const request of this.changeRequests.values()) {
            statusCounts[request.status]++;
        }

        let approvedCostDelta = 0;
        let approvedScheduleDelta = 0;

        for (const request of this.changeRequests.values()) {
            if (
                request.impact &&
                (
                    request.status === ChangeStatus.APPROVED ||
                    request.status === ChangeStatus.IMPLEMENTED
                )
            ) {
                approvedCostDelta += request.impact.costDelta;
                approvedScheduleDelta +=
                    request.impact.scheduleDeltaDays;
            }
        }

        return {
            baselineVersion: this.baseline.version,
            baselineHours: this.baseline.totalHours(),
            baselineCost: this.baseline.totalCost(),
            totalChangeRequests: this.changeRequests.size,
            statusCounts,
            approvedCostDelta,
            approvedScheduleDelta,
            auditEntries: this.auditLog.entries.length
        };
    }

    getChange(changeId) {
        const request = this.changeRequests.get(changeId);

        if (!request) {
            throw new Error(`Unknown change request: ${changeId}`);
        }

        return request;
    }
}


// ---------------------------------------------------------------------------
// 7. TRACEABILITY MATRIX
// ---------------------------------------------------------------------------

class TraceabilityMatrix {
    constructor() {
        this.requirementToTests = new Map();
        this.requirementToChanges = new Map();
    }

    addTest(requirementId, testId) {
        if (!this.requirementToTests.has(requirementId)) {
            this.requirementToTests.set(requirementId, new Set());
        }

        this.requirementToTests.get(requirementId).add(testId);
    }

    addChange(requirementId, changeId) {
        if (!this.requirementToChanges.has(requirementId)) {
            this.requirementToChanges.set(requirementId, new Set());
        }

        this.requirementToChanges.get(requirementId).add(changeId);
    }

    report() {
        const ids = new Set([
            ...this.requirementToTests.keys(),
            ...this.requirementToChanges.keys()
        ]);

        const result = {};

        for (const id of [...ids].sort()) {
            const tests = this.requirementToTests.get(id) || new Set();
            const changes =
                this.requirementToChanges.get(id) || new Set();

            result[id] = {
                testCount: tests.size,
                changeCount: changes.size,
                tested: tests.size > 0
            };
        }

        return result;
    }
}


// ---------------------------------------------------------------------------
// 8. SCOPE CREEP DETECTION
// ---------------------------------------------------------------------------

function detectScopeCreep(workItems, baseline) {
    const baselineIds = new Set(baseline.deliverables.keys());

    return workItems.filter(item => (
        !item.authorized ||
        !baselineIds.has(item.baselineDeliverableId)
    ));
}


// ---------------------------------------------------------------------------
// 9. CHANGE CLASSIFICATION
// ---------------------------------------------------------------------------

function classifyChange(impact, priority) {
    if (priority === Priority.CRITICAL) {
        return "Major";
    }

    if (
        impact.costDelta > 10000 ||
        impact.scheduleDeltaDays > 10 ||
        impact.averageRisk() >= 8
    ) {
        return "Major";
    }

    if (
        impact.costDelta > 2500 ||
        impact.scheduleDeltaDays > 3 ||
        impact.averageRisk() >= 5
    ) {
        return "Significant";
    }

    return "Minor";
}


// ---------------------------------------------------------------------------
// 10. BASELINE FACTORY
// ---------------------------------------------------------------------------

function createInitialBaseline() {
    const deliverables = {
        "D-100": new Deliverable({
            id: "D-100",
            name: "Customer Web Portal",
            description: "Responsive account-management portal.",
            estimatedHours: 320,
            estimatedCost: 32000
        }),
        "D-200": new Deliverable({
            id: "D-200",
            name: "Authentication Service",
            description: "Secure identity and session management.",
            estimatedHours: 180,
            estimatedCost: 24000
        }),
        "D-300": new Deliverable({
            id: "D-300",
            name: "Reporting Module",
            description: "Operational and management reporting.",
            estimatedHours: 220,
            estimatedCost: 20000
        })
    };

    const requirements = {
        "REQ-001": new Requirement({
            id: "REQ-001",
            title: "Customer authentication",
            description: "Users must authenticate securely.",
            priority: Priority.CRITICAL,
            acceptanceCriteria: [
                "Valid credentials permit access.",
                "Invalid credentials are rejected.",
                "Sessions expire according to policy."
            ],
            deliverableIds: ["D-200"]
        }),
        "REQ-002": new Requirement({
            id: "REQ-002",
            title: "Account dashboard",
            description: "Customers can view account information.",
            priority: Priority.HIGH,
            acceptanceCriteria: [
                "Account information is displayed.",
                "Unauthorized information is not exposed."
            ],
            deliverableIds: ["D-100"]
        }),
        "REQ-003": new Requirement({
            id: "REQ-003",
            title: "Management reports",
            description: "Managers can access operational reports.",
            priority: Priority.MEDIUM,
            acceptanceCriteria: [
                "Reports can be generated.",
                "Reports use approved business metrics."
            ],
            deliverableIds: ["D-300"]
        })
    };

    for (const deliverable of Object.values(deliverables)) {
        for (const requirement of Object.values(requirements)) {
            if (
                requirement.deliverableIds.has(
                    deliverable.id
                )
            ) {
                deliverable.requirements.add(requirement.id);
            }
        }
    }

    return new ScopeBaseline({
        version: "BL-1.0",
        approvedDate: "2026-09-01",
        deliverables,
        requirements
    });
}


// ---------------------------------------------------------------------------
// 11. END-TO-END DEMONSTRATION
// ---------------------------------------------------------------------------

function runCaseStudy() {
    printSection("1. END-TO-END SCOPE CONTROL CASE STUDY");

    const engine = new ScopeControlEngine({
        baseline: createInitialBaseline()
    });

    console.log(`Initial baseline: ${engine.baseline.version}`);
    console.log(
        `Baseline effort: ${engine.baseline.totalHours()} hours`
    );
    console.log(
        `Baseline cost: $${engine.baseline.totalCost().toLocaleString()}`
    );

    const smallChange = new ChangeRequest({
        id: "CR-001",
        title: "Add customer profile photo",
        requester: "Product Owner",
        description:
            "Allow customers to upload a profile image.",
        reason: "Customer usability improvement.",
        priority: Priority.LOW,
        affectedRequirements: ["REQ-002"],
        affectedDeliverables: ["D-100"]
    });

    engine.submitChange(smallChange);

    const smallImpact = new ImpactAnalysis({
        scopeDelta: 1,
        scheduleDeltaDays: 2,
        costDelta: 1200,
        resourceDeltaHours: 16,
        qualityRisk: 2,
        technicalRisk: 2,
        complianceRisk: 1,
        operationalRisk: 2,
        dependencies: ["Image storage."],
        assumptions: ["Maximum image size is enforced."]
    });

    engine.analyzeChange("CR-001", smallImpact);

    console.log(
        `\nCR-001 classification: ` +
        classifyChange(smallImpact, smallChange.priority)
    );

    console.log(
        `CR-001 routing: ` +
        engine.routingRecommendation("CR-001")
    );

    engine.approve(
        "CR-001",
        "Project Manager",
        "Small controlled enhancement."
    );

    engine.implement(
        "CR-001",
        "Development Team"
    );

    const majorChange = new ChangeRequest({
        id: "CR-002",
        title: "Add external payment gateway",
        requester: "Business Sponsor",
        description:
            "Enable customers to pay outstanding balances online.",
        reason: "Business requirement introduced after baseline approval.",
        priority: Priority.HIGH,
        affectedRequirements: ["REQ-002"],
        affectedDeliverables: ["D-100", "D-200"]
    });

    engine.submitChange(majorChange);

    const majorImpact = new ImpactAnalysis({
        scopeDelta: 4,
        scheduleDeltaDays: 12,
        costDelta: 18000,
        resourceDeltaHours: 160,
        qualityRisk: 6,
        technicalRisk: 7,
        complianceRisk: 9,
        operationalRisk: 7,
        dependencies: [
            "Payment provider contract",
            "Security review",
            "Financial reconciliation"
        ],
        assumptions: [
            "Provider API remains available",
            "Compliance obligations are satisfied"
        ]
    });

    engine.analyzeChange("CR-002", majorImpact);

    console.log(
        `\nCR-002 classification: ` +
        classifyChange(majorImpact, majorChange.priority)
    );

    console.log(
        `CR-002 routing: ` +
        engine.routingRecommendation("CR-002")
    );

    engine.approve(
        "CR-002",
        "Change Control Board",
        "Approved after financial, schedule, security, " +
        "compliance, and operational analysis."
    );

    engine.implement(
        "CR-002",
        "Payments Workstream"
    );

    const rejectedChange = new ChangeRequest({
        id: "CR-003",
        title: "Add animated dashboard background",
        requester: "Designer",
        description:
            "Add continuously animated decorative effects.",
        reason: "Visual enhancement.",
        priority: Priority.LOW,
        affectedRequirements: ["REQ-002"],
        affectedDeliverables: ["D-100"]
    });

    engine.submitChange(rejectedChange);

    const rejectedImpact = new ImpactAnalysis({
        scopeDelta: 1,
        scheduleDeltaDays: 3,
        costDelta: 2000,
        resourceDeltaHours: 24,
        qualityRisk: 4,
        technicalRisk: 5,
        complianceRisk: 1,
        operationalRisk: 5,
        dependencies: ["Browser rendering performance"],
        assumptions: ["Target browsers support the animation."]
    });

    engine.analyzeChange("CR-003", rejectedImpact);

    engine.reject(
        "CR-003",
        "Project Manager",
        "Not required by approved objectives and adds avoidable complexity."
    );

    console.log("\nControl report:");
    console.log(engine.report());

    const newBaseline = engine.rebaseline(
        "BL-2.0",
        new Date().toISOString().slice(0, 10)
    );

    console.log(
        `\nRebaselined version: ${newBaseline.version}`
    );
    console.log(
        `New effort: ${newBaseline.totalHours()} hours`
    );
    console.log(
        `New cost: $${newBaseline.totalCost().toLocaleString()}`
    );

    return engine;
}


// ---------------------------------------------------------------------------
// 12. TRACEABILITY
// ---------------------------------------------------------------------------

function demonstrateTraceability() {
    printSection("2. REQUIREMENTS TRACEABILITY");

    const matrix = new TraceabilityMatrix();

    matrix.addTest("REQ-001", "TEST-AUTH-001");
    matrix.addTest("REQ-001", "TEST-AUTH-002");
    matrix.addTest("REQ-002", "TEST-DASH-001");

    matrix.addChange("REQ-002", "CR-001");
    matrix.addChange("REQ-002", "CR-002");

    console.log(matrix.report());
}


// ---------------------------------------------------------------------------
// 13. SCOPE CREEP
// ---------------------------------------------------------------------------

function demonstrateScopeCreep() {
    printSection("3. SCOPE CREEP DETECTION");

    const baseline = createInitialBaseline();

    const workItems = [
        {
            id: "W-001",
            name: "Build login form",
            baselineDeliverableId: "D-200",
            estimatedHours: 20,
            authorized: true
        },
        {
            id: "W-002",
            name: "Add social-media dashboard export",
            baselineDeliverableId: null,
            estimatedHours: 12,
            authorized: false
        },
        {
            id: "W-003",
            name: "Improve reporting query",
            baselineDeliverableId: "D-300",
            estimatedHours: 18,
            authorized: true
        },
        {
            id: "W-004",
            name: "Build unrequested loyalty system",
            baselineDeliverableId: null,
            estimatedHours: 80,
            authorized: false
        }
    ];

    const uncontrolled = detectScopeCreep(
        workItems,
        baseline
    );

    for (const item of uncontrolled) {
        console.log(
            `${item.id}: ${item.name} - ${item.estimatedHours} hours`
        );
    }
}


// ---------------------------------------------------------------------------
// 14. ERROR HANDLING
// ---------------------------------------------------------------------------

function demonstrateErrorHandling() {
    printSection("4. EDGE CASES AND CONTROL FAILURES");

    const engine = new ScopeControlEngine({
        baseline: createInitialBaseline()
    });

    const duplicate = new ChangeRequest({
        id: "ERR-001",
        title: "Duplicate test",
        requester: "Tester",
        description: "Testing duplicate protection.",
        reason: "Validation",
        priority: Priority.LOW
    });

    engine.submitChange(duplicate);

    try {
        engine.submitChange(duplicate);
    } catch (error) {
        console.log("Duplicate prevented:", error.message);
    }

    const invalidReference = new ChangeRequest({
        id: "ERR-002",
        title: "Invalid requirement reference",
        requester: "Tester",
        description: "Testing reference validation.",
        reason: "Validation",
        priority: Priority.LOW,
        affectedRequirements: ["REQ-999"]
    });

    try {
        engine.submitChange(invalidReference);
    } catch (error) {
        console.log(
            "Invalid requirement prevented:",
            error.message
        );
    }

    const unanalyzed = new ChangeRequest({
        id: "ERR-003",
        title: "Approval without analysis",
        requester: "Tester",
        description: "Testing governance enforcement.",
        reason: "Validation",
        priority: Priority.MEDIUM
    });

    engine.submitChange(unanalyzed);

    try {
        engine.approve(
            "ERR-003",
            "Project Manager",
            "Invalid attempt."
        );
    } catch (error) {
        console.log(
            "Approval without analysis prevented:",
            error.message
        );
    }
}


// ---------------------------------------------------------------------------
// 15. PERFORMANCE DEMONSTRATION
// ---------------------------------------------------------------------------

function performanceDemonstration() {
    printSection("5. PERFORMANCE CONSIDERATIONS");

    const count = 100_000;
    const requirements = new Map();

    for (let index = 0; index < count; index++) {
        requirements.set(
            `REQ-${index}`,
            { id: `REQ-${index}`, title: `Requirement ${index}` }
        );
    }

    const start = performance.now();

    let found = 0;

    for (let index = 0; index < count; index++) {
        if (requirements.has(`REQ-${index}`)) {
            found++;
        }
    }

    const elapsed = performance.now() - start;

    console.log(`Indexed lookups: ${found}`);
    console.log(`Elapsed time: ${elapsed.toFixed(2)} ms`);
    console.log(
        "Map membership is approximately O(1) on average. " +
        "Actual performance depends on the runtime and workload."
    );
}


// ---------------------------------------------------------------------------
// 16. SIMPLE TEST FRAMEWORK
// ---------------------------------------------------------------------------

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(
            `${message}: expected ${expected}, got ${actual}`
        );
    }
}

function assertThrows(fn, message) {
    let threw = false;

    try {
        fn();
    } catch {
        threw = true;
    }

    if (!threw) {
        throw new Error(`${message}: expected an exception.`);
    }
}

function runTests() {
    printSection("6. AUTOMATED TESTS");

    const baseline = createInitialBaseline();

    assertEqual(
        baseline.totalHours(),
        720,
        "Initial baseline hours"
    );

    assertEqual(
        baseline.totalCost(),
        76000,
        "Initial baseline cost"
    );

    const engine = new ScopeControlEngine({ baseline });

    const request = new ChangeRequest({
        id: "TEST-001",
        title: "Test change",
        requester: "Tester",
        description: "Valid test change.",
        reason: "Automated test",
        priority: Priority.LOW
    });

    engine.submitChange(request);

    assertThrows(
        () => engine.approve(
            "TEST-001",
            "Manager",
            "Should fail."
        ),
        "Approval without analysis"
    );

    const impact = new ImpactAnalysis({
        scopeDelta: 1,
        scheduleDeltaDays: 1,
        costDelta: 1000,
        resourceDeltaHours: 10,
        qualityRisk: 1,
        technicalRisk: 1,
        complianceRisk: 1,
        operationalRisk: 1
    });

    engine.analyzeChange("TEST-001", impact);
    engine.approve(
        "TEST-001",
        "Manager",
        "Approved for testing."
    );
    engine.implement("TEST-001", "Developer");

    assertEqual(
        engine.getChange("TEST-001").status,
        ChangeStatus.IMPLEMENTED,
        "Implemented change status"
    );

    console.log("All JavaScript tests passed.");
}


// ---------------------------------------------------------------------------
// 17. MAIN
// ---------------------------------------------------------------------------

function main() {
    console.log(`
SCOPE CONTROL: MANAGING CHANGES TO SCOPE
=========================================

This program demonstrates controlled scope evolution using a baseline,
requirements, deliverables, change requests, impact analysis, governance,
approval, implementation, traceability, and rebaselining.
`);

    runCaseStudy();
    demonstrateTraceability();
    demonstrateScopeCreep();
    demonstrateErrorHandling();
    performanceDemonstration();
    runTests();

    printSection("7. KEY IMPLEMENTATION PRINCIPLES");

    const principles = [
        "Baseline first; change second.",
        "Require documented change requests.",
        "Analyze impact before approval.",
        "Separate request, analysis, decision, and implementation.",
        "Use explicit authority for approval.",
        "Record both approved and rejected requests.",
        "Maintain an audit trail.",
        "Trace changes to requirements and deliverables.",
        "Detect unauthorized work early.",
        "Create a new baseline after approved changes are implemented.",
        "Protect approved baselines from silent modification."
    ];

    principles.forEach((principle, index) => {
        console.log(`${index + 1}. ${principle}`);
    });
}

main();
