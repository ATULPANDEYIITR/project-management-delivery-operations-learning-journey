/*
 * Scope Planning: From Fundamentals to Advanced Practice
 *
 * This self-contained JavaScript program demonstrates project scope planning
 * through requirements, deliverables, acceptance criteria, WBS structures,
 * traceability, baselines, change requests, validation, metrics, and a small
 * event-driven change-control workflow.
 *
 * It runs in Node.js without external packages.
 */

"use strict";

// ---------------------------------------------------------------------------
// 1. BASIC OUTPUT HELPERS
// ---------------------------------------------------------------------------

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function subsection(title) {
    console.log("\n" + "-".repeat(78));
    console.log(title);
    console.log("-".repeat(78));
}

function normalize(value) {
    return String(value).trim().replace(/\s+/g, " ").toLowerCase();
}

// ---------------------------------------------------------------------------
// 2. FUNDAMENTAL SCOPE CONCEPTS
// ---------------------------------------------------------------------------

section("1. Scope planning fundamentals");

console.log(`
Project scope defines the work required to produce the agreed project
deliverables and establishes boundaries around that work.

Product scope describes the characteristics and functions of the result.
Project scope describes the work necessary to create that result.

A practical scope model is:

Business need
  -> objective
  -> requirements
  -> deliverables
  -> work packages
  -> acceptance criteria
  -> baseline
  -> controlled changes

A scope boundary should also identify inclusions, exclusions, assumptions,
and constraints.
`);

// ---------------------------------------------------------------------------
// 3. REQUIREMENTS
// ---------------------------------------------------------------------------

class Requirement {
    constructor(id, description, priority, source, acceptanceCriteria = []) {
        this.id = id;
        this.description = description;
        this.priority = priority;
        this.source = source;
        this.acceptanceCriteria = acceptanceCriteria;
    }

    isComplete() {
        return Boolean(
            this.id &&
            this.description &&
            this.priority &&
            this.source &&
            this.acceptanceCriteria.length > 0
        );
    }
}

const requirements = [
    new Requirement(
        "REQ-001",
        "Users shall be able to create an account using an email address.",
        "Must",
        "Business owner",
        [
            "Valid email registration succeeds.",
            "Duplicate email registration is rejected."
        ]
    ),
    new Requirement(
        "REQ-002",
        "Users shall be able to sign in with their credentials.",
        "Must",
        "Product owner",
        [
            "Valid credentials create a session.",
            "Invalid credentials are rejected."
        ]
    ),
    new Requirement(
        "REQ-003",
        "The dashboard shall allow users to search projects by name.",
        "Should",
        "Project manager",
        [
            "A matching project can be found by name."
        ]
    ),
    new Requirement(
        "REQ-004",
        "The first release shall use English interface content.",
        "Must",
        "Sponsor",
        [
            "Release screens use English labels."
        ]
    )
];

subsection("Requirement validation");

for (const requirement of requirements) {
    console.log(
        `${requirement.id} | ${requirement.priority} | ` +
        `${requirement.description} | complete=${requirement.isComplete()}`
    );
}

// ---------------------------------------------------------------------------
// 4. SCOPE STATEMENT
// ---------------------------------------------------------------------------

class ScopeStatement {
    constructor(objective, inclusions, exclusions, assumptions, constraints) {
        this.objective = objective;
        this.inclusions = inclusions;
        this.exclusions = exclusions;
        this.assumptions = assumptions;
        this.constraints = constraints;
    }

    containsIncludedWork(text) {
        const target = normalize(text);
        return this.inclusions.some(item => normalize(item).includes(target));
    }
}

const scope = new ScopeStatement(
    "Deliver a browser-based project management MVP for small teams.",
    [
        "Account creation and authentication",
        "Project dashboard",
        "Project search",
        "English user interface",
        "Basic project status tracking"
    ],
    [
        "Native mobile applications",
        "Advanced financial accounting",
        "Third-party payroll processing",
        "Multi-language translation in the first release"
    ],
    [
        "Branding assets will be supplied by the organization.",
        "Users will have internet access.",
        "The hosting environment will be available before acceptance testing."
    ],
    [
        "The approved technology stack must be used.",
        "The release date is fixed.",
        "The initial budget is limited."
    ]
);

subsection("Scope boundaries");

console.log("Objective:", scope.objective);
console.log("Included:", scope.inclusions);
console.log("Excluded:", scope.exclusions);
console.log("Assumptions:", scope.assumptions);
console.log("Constraints:", scope.constraints);

// ---------------------------------------------------------------------------
// 5. DELIVERABLES AND TRACEABILITY
// ---------------------------------------------------------------------------

class Deliverable {
    constructor(id, name, description, requirementIds, acceptanceCriteria) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.requirementIds = requirementIds;
        this.acceptanceCriteria = acceptanceCriteria;
    }

    traceability(requirementIdSet) {
        return this.requirementIds.every(id => requirementIdSet.has(id));
    }
}

const deliverables = [
    new Deliverable(
        "DEL-001",
        "Authentication module",
        "Registration and sign-in capability.",
        ["REQ-001", "REQ-002"],
        [
            "Valid users can register.",
            "Valid users can sign in."
        ]
    ),
    new Deliverable(
        "DEL-002",
        "Project dashboard",
        "Dashboard showing project information.",
        ["REQ-003"],
        [
            "Dashboard displays project information."
        ]
    ),
    new Deliverable(
        "DEL-003",
        "English release",
        "English interface for the MVP.",
        ["REQ-004"],
        [
            "All release screens have English labels."
        ]
    )
];

const requirementIds = new Set(requirements.map(item => item.id));

subsection("Traceability");

for (const deliverable of deliverables) {
    console.log(
        `${deliverable.id} | ${deliverable.name} | ` +
        `traceable=${deliverable.traceability(requirementIds)}`
    );
}

const mappedRequirementIds = new Set(
    deliverables.flatMap(deliverable => deliverable.requirementIds)
);

const unmapped = requirements
    .filter(requirement => !mappedRequirementIds.has(requirement.id))
    .map(requirement => requirement.id);

console.log("Unmapped requirements:", unmapped);

// ---------------------------------------------------------------------------
// 6. WORK BREAKDOWN STRUCTURE
// ---------------------------------------------------------------------------

class WorkPackage {
    constructor(id, name, description, estimatedHours, deliverableIds) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.estimatedHours = estimatedHours;
        this.deliverableIds = deliverableIds;
    }

    validate() {
        const errors = [];

        if (!this.id) errors.push("Missing WBS identifier.");
        if (!this.name) errors.push("Missing work-package name.");
        if (this.estimatedHours <= 0) {
            errors.push("Estimated effort must be positive.");
        }
        if (this.deliverableIds.length === 0) {
            errors.push("No linked deliverables.");
        }

        return errors;
    }
}

const workPackages = [
    new WorkPackage(
        "1.1",
        "Authentication",
        "Implement account creation and sign-in.",
        36,
        ["DEL-001"]
    ),
    new WorkPackage(
        "1.2",
        "Dashboard",
        "Implement dashboard presentation.",
        48,
        ["DEL-002"]
    ),
    new WorkPackage(
        "1.3",
        "Acceptance testing",
        "Execute agreed acceptance tests.",
        28,
        ["DEL-001", "DEL-002", "DEL-003"]
    )
];

subsection("WBS validation");

for (const workPackage of workPackages) {
    console.log(
        `${workPackage.id} ${workPackage.name}: ` +
        `${workPackage.estimatedHours} hours`,
        workPackage.validate()
    );
}

const totalEffort = workPackages.reduce(
    (sum, item) => sum + item.estimatedHours,
    0
);

console.log("Total estimated effort:", totalEffort, "hours");

// ---------------------------------------------------------------------------
// 7. ACCEPTANCE CRITERIA
// ---------------------------------------------------------------------------

section("2. Acceptance and validation");

function evaluateAcceptance(completedConditions, requiredConditions) {
    const completed = new Set(completedConditions.map(normalize));
    const missing = requiredConditions.filter(
        condition => !completed.has(normalize(condition))
    );

    return {
        accepted: missing.length === 0,
        missing
    };
}

const acceptanceResult = evaluateAcceptance(
    [
        "Valid users can register."
    ],
    [
        "Valid users can register.",
        "Valid users can sign in."
    ]
);

console.log("Acceptance result:", acceptanceResult);

console.log(`
Acceptance criteria should be observable and testable. A vague statement such
as "the system should be fast" does not define a measurable boundary. A useful
criterion specifies the condition, environment, and threshold needed to decide
whether the requirement is satisfied.
`);

// ---------------------------------------------------------------------------
// 8. SCOPE BASELINE
// ---------------------------------------------------------------------------

class ScopeBaseline {
    constructor(version, scopeStatement, requirements, deliverables, workPackages) {
        this.version = version;
        this.scopeStatement = scopeStatement;
        this.requirements = requirements;
        this.deliverables = deliverables;
        this.workPackages = workPackages;
        this.createdAt = new Date();
    }

    snapshot() {
        return {
            version: this.version,
            requirementIds: this.requirements.map(item => item.id),
            deliverableIds: this.deliverables.map(item => item.id),
            workPackageIds: this.workPackages.map(item => item.id),
            createdAt: this.createdAt.toISOString()
        };
    }
}

const baseline = new ScopeBaseline(
    "1.0",
    scope,
    requirements,
    deliverables,
    workPackages
);

subsection("Baseline");

console.log(JSON.stringify(baseline.snapshot(), null, 2));

// ---------------------------------------------------------------------------
// 9. CHANGE REQUESTS
// ---------------------------------------------------------------------------

const ChangeStatus = Object.freeze({
    PROPOSED: "Proposed",
    ANALYZING: "Analyzing",
    APPROVED: "Approved",
    REJECTED: "Rejected",
    IMPLEMENTED: "Implemented"
});

class ChangeRequest {
    constructor(
        id,
        description,
        reason,
        estimatedHours,
        costImpact,
        scheduleImpactDays
    ) {
        this.id = id;
        this.description = description;
        this.reason = reason;
        this.estimatedHours = estimatedHours;
        this.costImpact = costImpact;
        this.scheduleImpactDays = scheduleImpactDays;
        this.status = ChangeStatus.PROPOSED;
    }

    impactScore() {
        return (
            Math.max(0, this.estimatedHours) +
            Math.max(0, this.costImpact) / 100 +
            Math.max(0, this.scheduleImpactDays) * 8
        );
    }

    analyze() {
        this.status = ChangeStatus.ANALYZING;

        return {
            effort: this.estimatedHours,
            cost: this.costImpact,
            scheduleDays: this.scheduleImpactDays,
            score: this.impactScore()
        };
    }
}

const change = new ChangeRequest(
    "CR-001",
    "Add multilingual interface support.",
    "Expansion into additional markets.",
    80,
    12000,
    10
);

console.log("Change analysis:", change.analyze());

// ---------------------------------------------------------------------------
// 10. EVENT-DRIVEN CHANGE CONTROL
// ---------------------------------------------------------------------------

class ChangeControl {
    constructor() {
        this.listeners = new Map();
        this.changes = [];
    }

    on(eventName, listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }
        this.listeners.get(eventName).push(listener);
    }

    emit(eventName, payload) {
        const listeners = this.listeners.get(eventName) || [];
        for (const listener of listeners) {
            listener(payload);
        }
    }

    submit(changeRequest) {
        this.changes.push(changeRequest);
        this.emit("changeSubmitted", changeRequest);
    }

    approve(changeRequest) {
        changeRequest.status = ChangeStatus.APPROVED;
        this.emit("changeApproved", changeRequest);
    }

    reject(changeRequest) {
        changeRequest.status = ChangeStatus.REJECTED;
        this.emit("changeRejected", changeRequest);
    }
}

const control = new ChangeControl();

control.on("changeSubmitted", request => {
    console.log(`Submitted: ${request.id}`);
});

control.on("changeApproved", request => {
    console.log(`Approved: ${request.id}`);
});

control.on("changeRejected", request => {
    console.log(`Rejected: ${request.id}`);
});

control.submit(change);
control.approve(change);

console.log("Final change status:", change.status);

// ---------------------------------------------------------------------------
// 11. SCOPE CREEP DETECTION
// ---------------------------------------------------------------------------

section("3. Scope creep detection");

function detectUnapprovedAdditions(baselineItems, proposedItems) {
    const baselineSet = new Set(baselineItems.map(normalize));

    return proposedItems.filter(
        item => !baselineSet.has(normalize(item))
    );
}

const proposedScope = [
    ...scope.inclusions,
    "Native mobile applications",
    "Advanced analytics"
];

const additions = detectUnapprovedAdditions(
    scope.inclusions,
    proposedScope
);

console.log("Potential unapproved additions:", additions);

console.log(`
Scope creep is uncontrolled expansion of the agreed scope. A requested
addition is not automatically scope creep: an authorized and governed change
can legitimately modify the baseline.

The key distinction is control and authorization, not whether the scope
changed.
`);

// ---------------------------------------------------------------------------
// 12. ASSUMPTIONS AND CONSTRAINTS
// ---------------------------------------------------------------------------

section("4. Assumptions and constraints");

console.log(`
An assumption is a planning condition believed to be true.

A constraint is a restriction that limits available choices.

Examples:

Assumption:
  A required data source will be available for testing.

Constraint:
  The project cannot exceed the approved budget.

If an assumption becomes false, the project may need a risk response or a
scope/change analysis. Constraints influence trade-offs among scope, time,
cost, resources, quality, and technical alternatives.
`);

// ---------------------------------------------------------------------------
// 13. PRIORITY DISTRIBUTION
// ---------------------------------------------------------------------------

section("5. Requirement analysis");

const priorityCounts = requirements.reduce((counts, requirement) => {
    counts[requirement.priority] =
        (counts[requirement.priority] || 0) + 1;
    return counts;
}, {});

console.log("Priority distribution:", priorityCounts);

const incompleteRequirements = requirements.filter(
    requirement => !requirement.isComplete()
);

console.log("Incomplete requirements:", incompleteRequirements.length);

// ---------------------------------------------------------------------------
// 14. DUPLICATE IDENTIFIER DETECTION
// ---------------------------------------------------------------------------

function duplicateIdentifiers(items) {
    const seen = new Set();
    const duplicates = new Set();

    for (const item of items) {
        if (seen.has(item.id)) {
            duplicates.add(item.id);
        }
        seen.add(item.id);
    }

    return [...duplicates];
}

const duplicateRequirementList = [
    ...requirements,
    new Requirement(
        "REQ-002",
        "Duplicate identifier for validation.",
        "Could",
        "Test",
        ["Test"]
    )
];

console.log(
    "Duplicate requirement identifiers:",
    duplicateIdentifiers(duplicateRequirementList)
);

// ---------------------------------------------------------------------------
// 15. TRACEABILITY COVERAGE
// ---------------------------------------------------------------------------

function traceabilityCoverage(requirementList, deliverableList) {
    if (requirementList.length === 0) return 100;

    const mapped = new Set(
        deliverableList.flatMap(
            deliverable => deliverable.requirementIds
        )
    );

    const covered = requirementList.filter(
        requirement => mapped.has(requirement.id)
    ).length;

    return (covered / requirementList.length) * 100;
}

const coverage = traceabilityCoverage(requirements, deliverables);

console.log(`Traceability coverage: ${coverage.toFixed(1)}%`);

// ---------------------------------------------------------------------------
// 16. REQUIREMENT VOLATILITY
// ---------------------------------------------------------------------------

function requirementVolatility(initialIds, currentIds) {
    const initial = new Set(initialIds);
    const current = new Set(currentIds);

    let additions = 0;
    let removals = 0;

    for (const id of current) {
        if (!initial.has(id)) additions++;
    }

    for (const id of initial) {
        if (!current.has(id)) removals++;
    }

    const denominator = initial.size || 1;

    return {
        additions,
        removals,
        rate: ((additions + removals) / denominator) * 100
    };
}

const volatility = requirementVolatility(
    ["REQ-001", "REQ-002", "REQ-003", "REQ-004"],
    ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005"]
);

console.log("Requirement volatility:", volatility);

// ---------------------------------------------------------------------------
// 17. INTEGRATED SCOPE MODEL
// ---------------------------------------------------------------------------

class ScopeModel {
    constructor({
        name,
        objective,
        requirements,
        deliverables,
        workPackages,
        exclusions,
        assumptions,
        constraints
    }) {
        this.name = name;
        this.objective = objective;
        this.requirements = requirements;
        this.deliverables = deliverables;
        this.workPackages = workPackages;
        this.exclusions = exclusions;
        this.assumptions = assumptions;
        this.constraints = constraints;
    }

    validate() {
        const errors = [];

        if (!this.objective.trim()) {
            errors.push("Scope objective is empty.");
        }

        const duplicateIds = duplicateIdentifiers(this.requirements);
        if (duplicateIds.length > 0) {
            errors.push(
                `Duplicate requirement IDs: ${duplicateIds.join(", ")}`
            );
        }

        const knownRequirementIds = new Set(
            this.requirements.map(item => item.id)
        );

        for (const deliverable of this.deliverables) {
            for (const requirementId of deliverable.requirementIds) {
                if (!knownRequirementIds.has(requirementId)) {
                    errors.push(
                        `${deliverable.id} references unknown ` +
                        `${requirementId}.`
                    );
                }
            }
        }

        for (const workPackage of this.workPackages) {
            errors.push(...workPackage.validate());
        }

        return errors;
    }

    totalEffort() {
        return this.workPackages.reduce(
            (sum, item) => sum + item.estimatedHours,
            0
        );
    }

    coverage() {
        return traceabilityCoverage(
            this.requirements,
            this.deliverables
        );
    }
}

section("6. Integrated validation");

const model = new ScopeModel({
    name: "Project Management MVP",
    objective: scope.objective,
    requirements,
    deliverables,
    workPackages,
    exclusions: scope.exclusions,
    assumptions: scope.assumptions,
    constraints: scope.constraints
});

console.log("Project:", model.name);
console.log("Total effort:", model.totalEffort(), "hours");
console.log("Coverage:", `${model.coverage().toFixed(1)}%`);
console.log("Validation errors:", model.validate());

// ---------------------------------------------------------------------------
// 18. PERFORMANCE AND DESIGN NOTES
// ---------------------------------------------------------------------------

section("7. Performance and implementation considerations");

console.log(`
The program uses:

Set for membership and identifier comparisons:
  Average membership is approximately O(1).

Map for event listener groups:
  Average key lookup is approximately O(1).

Array.filter, Array.map, and Array.flatMap:
  Generally O(n) over their input collections.

Sorting, if introduced for large requirement collections:
  Typically O(n log n).

For production scope systems, additional concerns include persistent storage,
transaction boundaries, optimistic concurrency, version history, audit logs,
authorization, validation at API boundaries, and immutable historical records.

A scope-management application should preserve who changed an artifact, what
changed, when it changed, why it changed, and which approval authorized it.
`);

// ---------------------------------------------------------------------------
// 19. PRACTICAL CHECKLIST
// ---------------------------------------------------------------------------

section("8. Scope planning checklist");

const checks = [
    ["Objective is defined", Boolean(model.objective)],
    ["Requirements exist", model.requirements.length > 0],
    [
        "Requirements have acceptance criteria",
        model.requirements.every(item => item.acceptanceCriteria.length > 0)
    ],
    ["Deliverables exist", model.deliverables.length > 0],
    ["Traceability is complete", model.coverage() === 100],
    [
        "Work packages contain positive effort",
        model.workPackages.every(item => item.estimatedHours > 0)
    ],
    ["Exclusions are documented", model.exclusions.length > 0],
    ["Assumptions are documented", model.assumptions.length > 0],
    ["Constraints are documented", model.constraints.length > 0],
    ["Baseline exists", Boolean(baseline.version)],
    ["Change-control mechanism exists", true]
];

for (const [description, passed] of checks) {
    console.log(`[${passed ? "PASS" : "FAIL"}] ${description}`);
}

console.log(`
A controlled scope model connects objectives, requirements, deliverables,
work packages, acceptance criteria, assumptions, constraints, baselines, and
change decisions.

The purpose of these structures is not bureaucracy for its own sake. They
provide a common reference for deciding what work belongs to the project,
whether a result satisfies the agreed requirements, and whether a proposed
change should modify the approved baseline.
`);
