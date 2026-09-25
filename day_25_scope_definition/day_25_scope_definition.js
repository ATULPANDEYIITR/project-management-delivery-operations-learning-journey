/*
 * Creating a Clear Project Scope
 *
 * Self-contained JavaScript study and demonstration file.
 *
 * Demonstrates:
 * - Scope statements
 * - Objectives
 * - Requirements
 * - Deliverables
 * - Acceptance criteria
 * - Assumptions and constraints
 * - Work Breakdown Structures
 * - Traceability
 * - Scope creep
 * - Change control
 * - Impact analysis
 * - Validation
 * - Asynchronous stakeholder approval
 * - Immutable-style scope updates
 * - Performance considerations
 *
 * Run with:
 *   node project-scope.js
 */

"use strict";

// -----------------------------------------------------------------------------
// 1. BASIC PROJECT SCOPE MODEL
// -----------------------------------------------------------------------------

class Requirement {
    constructor({
        id,
        description,
        priority = "Should",
        acceptanceCriteria = [],
        source = "",
        inScope = true
    }) {
        this.id = id;
        this.description = description;
        this.priority = priority;
        this.acceptanceCriteria = [...acceptanceCriteria];
        this.source = source;
        this.inScope = inScope;
    }

    validate() {
        const problems = [];

        if (!this.id.trim()) {
            problems.push("Requirement ID is missing.");
        }

        if (!this.description.trim()) {
            problems.push("Requirement description is missing.");
        }

        if (this.acceptanceCriteria.length === 0) {
            problems.push("No acceptance criteria are defined.");
        }

        if (!this.source.trim()) {
            problems.push("Requirement source is missing.");
        }

        const vagueTerms = [
            "fast",
            "easy",
            "modern",
            "user-friendly",
            "etc"
        ];

        const lowerDescription = this.description.toLowerCase();

        for (const term of vagueTerms) {
            if (lowerDescription.includes(term)) {
                problems.push(`Potentially vague term: "${term}".`);
            }
        }

        return problems;
    }
}


class Deliverable {
    constructor({
        id,
        name,
        description,
        acceptanceCriteria = [],
        owner
    }) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.acceptanceCriteria = [...acceptanceCriteria];
        this.owner = owner;
    }

    validate() {
        const problems = [];

        if (!this.id) problems.push("Missing deliverable ID.");
        if (!this.name) problems.push("Missing deliverable name.");
        if (!this.description) problems.push("Missing description.");
        if (!this.owner) problems.push("Missing owner.");

        if (this.acceptanceCriteria.length === 0) {
            problems.push("No acceptance criteria.");
        }

        return problems;
    }
}


class ScopeItem {
    constructor({
        id,
        name,
        description,
        estimatedHours = 0
    }) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.estimatedHours = estimatedHours;
        this.children = [];
    }

    addChild(child) {
        this.children.push(child);
        return this;
    }

    totalHours() {
        return this.estimatedHours +
            this.children.reduce(
                (total, child) => total + child.totalHours(),
                0
            );
    }

    isLeaf() {
        return this.children.length === 0;
    }
}


class ScopeStatement {
    constructor({
        projectName,
        purpose,
        objectives = [],
        deliverables = [],
        inScope = [],
        outOfScope = [],
        assumptions = [],
        constraints = [],
        dependencies = []
    }) {
        this.projectName = projectName;
        this.purpose = purpose;
        this.objectives = objectives;
        this.deliverables = deliverables;
        this.inScope = inScope;
        this.outOfScope = outOfScope;
        this.assumptions = assumptions;
        this.constraints = constraints;
        this.dependencies = dependencies;
    }

    validate() {
        const problems = [];

        if (!this.projectName?.trim()) {
            problems.push("Project name is missing.");
        }

        if (!this.purpose?.trim()) {
            problems.push("Project purpose is missing.");
        }

        if (this.objectives.length === 0) {
            problems.push("No objectives are defined.");
        }

        if (this.deliverables.length === 0) {
            problems.push("No deliverables are defined.");
        }

        if (this.inScope.length === 0) {
            problems.push("No included scope items are defined.");
        }

        if (this.outOfScope.length === 0) {
            problems.push("No exclusions are defined.");
        }

        for (const deliverable of this.deliverables) {
            problems.push(...deliverable.validate());
        }

        return problems;
    }
}


// -----------------------------------------------------------------------------
// 2. REQUIREMENT VALIDATION
// -----------------------------------------------------------------------------

function printRequirementValidation(requirements) {
    console.log("\nREQUIREMENT VALIDATION");
    console.log("-".repeat(72));

    for (const requirement of requirements) {
        const problems = requirement.validate();

        console.log(`${requirement.id}: ${requirement.description}`);

        if (problems.length === 0) {
            console.log("  Status: Valid enough for further planning.");
        } else {
            for (const problem of problems) {
                console.log(`  - ${problem}`);
            }
        }
    }
}


// -----------------------------------------------------------------------------
// 3. WBS FUNCTIONS
// -----------------------------------------------------------------------------

function printWbs(item, level = 0) {
    const indentation = "  ".repeat(level);

    console.log(
        `${indentation}${item.id} ${item.name} ` +
        `[${item.estimatedHours}h]`
    );

    for (const child of item.children) {
        printWbs(child, level + 1);
    }
}


function getLeafWorkPackages(item) {
    if (item.isLeaf()) {
        return [item];
    }

    return item.children.flatMap(getLeafWorkPackages);
}


// -----------------------------------------------------------------------------
// 4. TRACEABILITY
// -----------------------------------------------------------------------------

function buildTraceabilityMatrix(requirements, deliverables) {
    return requirements
        .filter(requirement => requirement.inScope)
        .map((requirement, index) => {
            const deliverable =
                deliverables[index % deliverables.length];

            return {
                requirementId: requirement.id,
                deliverableId: deliverable.id,
                testId: `TEST-${String(index + 1).padStart(3, "0")}`,
                accepted: false
            };
        });
}


function printTraceability(matrix) {
    console.log("\nREQUIREMENT TRACEABILITY");
    console.log("-".repeat(72));

    for (const record of matrix) {
        console.log(
            `${record.requirementId} -> ` +
            `${record.deliverableId} -> ` +
            `${record.testId} -> ` +
            `accepted=${record.accepted}`
        );
    }
}


// -----------------------------------------------------------------------------
// 5. VAGUENESS AND SCOPE CREEP DETECTION
// -----------------------------------------------------------------------------

const vagueTerms = new Set([
    "fast",
    "easy",
    "simple",
    "modern",
    "robust",
    "secure",
    "efficient",
    "etc"
]);


function normalizeWords(text) {
    return text
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, " ")
        .split(/\s+/)
        .filter(Boolean);
}


function findVagueTerms(text) {
    return normalizeWords(text)
        .filter(word => vagueTerms.has(word));
}


function detectScopeCreep(request, approvedScope) {
    const requestWords = new Set(normalizeWords(request));

    const matches = approvedScope.filter(scopeItem => {
        const scopeWords = new Set(normalizeWords(scopeItem));
        let overlap = 0;

        for (const word of requestWords) {
            if (scopeWords.has(word)) {
                overlap++;
            }
        }

        return overlap >= 2;
    });

    return {
        likelyNewScope: matches.length === 0,
        relatedScope: matches
    };
}


// -----------------------------------------------------------------------------
// 6. CHANGE CONTROL
// -----------------------------------------------------------------------------

class ChangeRequest {
    constructor({
        id,
        description,
        reason,
        requestedBy,
        estimatedHours,
        estimatedCost,
        scheduleDays,
        affectedDeliverables = []
    }) {
        this.id = id;
        this.description = description;
        this.reason = reason;
        this.requestedBy = requestedBy;
        this.estimatedHours = estimatedHours;
        this.estimatedCost = estimatedCost;
        this.scheduleDays = scheduleDays;
        this.affectedDeliverables = affectedDeliverables;
        this.status = "Proposed";
    }

    impactScore() {
        return (
            this.estimatedHours * 0.4 +
            this.estimatedCost * 0.001 +
            this.scheduleDays * 2 +
            this.affectedDeliverables.length * 5
        );
    }
}


function analyzeChange(change, baselineHours, hourlyRate) {
    if (baselineHours < 0) {
        throw new Error("Baseline effort cannot be negative.");
    }

    const addedLaborCost =
        change.estimatedHours * hourlyRate;

    const totalAddedCost =
        addedLaborCost + change.estimatedCost;

    const effortIncrease =
        baselineHours === 0
            ? Infinity
            : (change.estimatedHours / baselineHours) * 100;

    return {
        changeId: change.id,
        additionalHours: change.estimatedHours,
        additionalCost: totalAddedCost,
        scheduleDays: change.scheduleDays,
        effortIncreasePercent: effortIncrease,
        impactScore: change.impactScore(),
        affectedDeliverables: [...change.affectedDeliverables]
    };
}


// -----------------------------------------------------------------------------
// 7. ACCEPTANCE VALIDATION
// -----------------------------------------------------------------------------

function validateDeliverable(deliverable, observedResults) {
    const failures = [];

    for (const criterion of deliverable.acceptanceCriteria) {
        if (observedResults[criterion] !== true) {
            failures.push(criterion);
        }
    }

    return {
        accepted: failures.length === 0,
        failures
    };
}


// -----------------------------------------------------------------------------
// 8. IMMUTABLE-STYLE SCOPE CHANGE
// -----------------------------------------------------------------------------

function proposeScopeAddition(scope, newItem) {
    /*
     * Instead of silently mutating the approved scope, create a new object.
     * This makes the original baseline easier to preserve and audit.
     */
    return {
        ...scope,
        inScope: [...scope.inScope, newItem]
    };
}


// -----------------------------------------------------------------------------
// 9. ASYNCHRONOUS STAKEHOLDER APPROVAL
// -----------------------------------------------------------------------------

function requestApproval(stakeholder, decision, delayMs = 150) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (!stakeholder) {
                reject(new Error("Stakeholder identity is required."));
                return;
            }

            resolve({
                stakeholder,
                decision,
                timestamp: new Date().toISOString()
            });
        }, delayMs);
    });
}


async function demonstrateApproval() {
    const approvals = await Promise.all([
        requestApproval("HR Director", "Approved"),
        requestApproval("IT Manager", "Approved"),
        requestApproval("Project Sponsor", "Approved")
    ]);

    console.log("\nSTAKEHOLDER APPROVALS");
    console.log("-".repeat(72));

    for (const approval of approvals) {
        console.log(
            `${approval.stakeholder}: ${approval.decision} ` +
            `at ${approval.timestamp}`
        );
    }
}


// -----------------------------------------------------------------------------
// 10. REALISTIC PROJECT DATA
// -----------------------------------------------------------------------------

function buildProject() {
    const requirements = [
        new Requirement({
            id: "REQ-001",
            description:
                "Users shall submit leave requests containing employee ID, " +
                "leave type, start date, and end date.",
            priority: "Must",
            acceptanceCriteria: [
                "Employee ID is mandatory.",
                "End date cannot precede start date.",
                "Valid requests receive a unique request ID."
            ],
            source: "HR Process Owner"
        }),

        new Requirement({
            id: "REQ-002",
            description:
                "Managers shall approve or reject pending leave requests.",
            priority: "Must",
            acceptanceCriteria: [
                "Pending requests can be approved.",
                "Pending requests can be rejected.",
                "The decision is recorded."
            ],
            source: "HR Process Owner"
        }),

        new Requirement({
            id: "REQ-003",
            description:
                "Employees shall be able to view the current request status.",
            priority: "Must",
            acceptanceCriteria: [
                "Submitted status is visible.",
                "Approved status is visible.",
                "Rejected status is visible."
            ],
            source: "Employee Representative"
        }),

        new Requirement({
            id: "REQ-004",
            description:
                "The dashboard should be modern and attractive.",
            priority: "Should",
            acceptanceCriteria: [],
            source: "Stakeholder"
        })
    ];

    const deliverables = [
        new Deliverable({
            id: "DEL-001",
            name: "Requirements Specification",
            description:
                "Approved functional and non-functional requirements.",
            acceptanceCriteria: [
                "Business owner approves the requirements.",
                "Mandatory requirements have acceptance criteria."
            ],
            owner: "Business Analyst"
        }),

        new Deliverable({
            id: "DEL-002",
            name: "Leave Request Module",
            description:
                "Employee leave request functionality.",
            acceptanceCriteria: [
                "Valid requests can be submitted.",
                "Invalid date ranges are rejected."
            ],
            owner: "Application Team"
        }),

        new Deliverable({
            id: "DEL-003",
            name: "Approval Workflow",
            description:
                "Manager approval and rejection workflow.",
            acceptanceCriteria: [
                "Managers can approve requests.",
                "Managers can reject requests.",
                "Employees can see resulting status."
            ],
            owner: "Application Team"
        })
    ];

    const scope = new ScopeStatement({
        projectName: "Employee Leave Management System",
        purpose:
            "Digitize employee leave submission, approval, tracking, " +
            "and standard reporting.",
        objectives: [
            {
                id: "OBJ-001",
                description:
                    "Process all pilot leave requests digitally.",
                measure: "Percentage of pilot requests processed digitally",
                target: "100%"
            },
            {
                id: "OBJ-002",
                description:
                    "Provide traceable request status.",
                measure: "Requests with visible status",
                target: "100%"
            }
        ],
        deliverables,
        inScope: [
            "Leave request submission",
            "Manager approval and rejection",
            "Request status tracking",
            "Standard leave reports",
            "Approved authentication mechanism",
            "User acceptance testing",
            "Production deployment"
        ],
        outOfScope: [
            "Payroll processing",
            "Recruitment",
            "Performance management",
            "Custom native mobile application",
            "Unapproved external notification platforms"
        ],
        assumptions: [
            "HR provides current leave rules.",
            "Employees have organizational accounts."
        ],
        constraints: [
            "Pilot budget is fixed.",
            "Pilot target is 60 calendar days.",
            "Only approved organizational systems may be integrated."
        ],
        dependencies: [
            "Identity provider",
            "Current HR policy",
            "Production infrastructure"
        ]
    });

    return {
        requirements,
        deliverables,
        scope
    };
}


// -----------------------------------------------------------------------------
// 11. BUILD WBS
// -----------------------------------------------------------------------------

function buildWbs() {
    const root = new ScopeItem({
        id: "1.0",
        name: "Employee Leave Management System",
        description: "Complete project scope"
    });

    root
        .addChild(
            new ScopeItem({
                id: "1.1",
                name: "Requirements and Discovery",
                description: "Define approved requirements"
            })
                .addChild(
                    new ScopeItem({
                        id: "1.1.1",
                        name: "Stakeholder Interviews",
                        description: "Collect stakeholder needs",
                        estimatedHours: 12
                    })
                )
                .addChild(
                    new ScopeItem({
                        id: "1.1.2",
                        name: "Requirements Specification",
                        description: "Document requirements",
                        estimatedHours: 16
                    })
                )
        )
        .addChild(
            new ScopeItem({
                id: "1.2",
                name: "Solution Design",
                description: "Design approved solution"
            })
                .addChild(
                    new ScopeItem({
                        id: "1.2.1",
                        name: "Architecture Design",
                        description: "Define system components",
                        estimatedHours: 14
                    })
                )
                .addChild(
                    new ScopeItem({
                        id: "1.2.2",
                        name: "Interface Design",
                        description: "Design user workflows",
                        estimatedHours: 18
                    })
                )
        )
        .addChild(
            new ScopeItem({
                id: "1.3",
                name: "Implementation",
                description: "Build approved capabilities"
            })
                .addChild(
                    new ScopeItem({
                        id: "1.3.1",
                        name: "Leave Requests",
                        description: "Implement request workflow",
                        estimatedHours: 28
                    })
                )
                .addChild(
                    new ScopeItem({
                        id: "1.3.2",
                        name: "Approval Workflow",
                        description: "Implement approval",
                        estimatedHours: 24
                    })
                )
        )
        .addChild(
            new ScopeItem({
                id: "1.4",
                name: "Testing and Acceptance",
                description: "Verify deliverables"
            })
                .addChild(
                    new ScopeItem({
                        id: "1.4.1",
                        name: "Functional Testing",
                        description: "Verify requirements",
                        estimatedHours: 20
                    })
                )
                .addChild(
                    new ScopeItem({
                        id: "1.4.2",
                        name: "User Acceptance Testing",
                        description: "Business acceptance",
                        estimatedHours: 16
                    })
                )
        )
        .addChild(
            new ScopeItem({
                id: "1.5",
                name: "Deployment",
                description: "Release approved solution"
            })
                .addChild(
                    new ScopeItem({
                        id: "1.5.1",
                        name: "Production Deployment",
                        description: "Deploy approved release",
                        estimatedHours: 10
                    })
                )
        );

    return root;
}


// -----------------------------------------------------------------------------
// 12. PERFORMANCE DEMONSTRATION
// -----------------------------------------------------------------------------

function calculateDuration(effortHours, teamSize, productiveHoursPerDay = 6) {
    if (effortHours < 0) {
        throw new Error("Effort cannot be negative.");
    }

    if (teamSize <= 0) {
        throw new Error("Team size must be positive.");
    }

    if (productiveHoursPerDay <= 0) {
        throw new Error("Productive hours must be positive.");
    }

    return effortHours / (teamSize * productiveHoursPerDay);
}


function measureLookupPerformance(scopeItems) {
    const start = performance.now();

    const lookup = new Map(
        scopeItems.map(item => [item.id, item])
    );

    const result = lookup.get(scopeItems[scopeItems.length - 1].id);

    const elapsed = performance.now() - start;

    return {
        result,
        elapsedMilliseconds: elapsed
    };
}


// -----------------------------------------------------------------------------
// 13. MAIN PROGRAM
// -----------------------------------------------------------------------------

async function main() {
    console.log("=".repeat(72));
    console.log("CREATING A CLEAR PROJECT SCOPE");
    console.log("=".repeat(72));

    console.log(`
Project scope defines the boundary of project work.

A strong scope specifies:
- Purpose and measurable objectives
- Requirements
- Deliverables
- Included work
- Excluded work
- Assumptions
- Constraints
- Dependencies
- Acceptance criteria
- Change-control rules
`);

    const { requirements, deliverables, scope } = buildProject();

    console.log("\nPROJECT:", scope.projectName);
    console.log("PURPOSE:", scope.purpose);

    console.log("\nIN SCOPE:");
    scope.inScope.forEach(item => console.log(`  + ${item}`));

    console.log("\nOUT OF SCOPE:");
    scope.outOfScope.forEach(item => console.log(`  - ${item}`));

    printRequirementValidation(requirements);

    console.log("\nSCOPE VALIDATION");
    console.log("-".repeat(72));

    const scopeProblems = scope.validate();

    if (scopeProblems.length === 0) {
        console.log("No structural scope problems detected.");
    } else {
        scopeProblems.forEach(problem => {
            console.log(`- ${problem}`);
        });
    }

    const wbs = buildWbs();

    console.log("\nWORK BREAKDOWN STRUCTURE");
    console.log("-".repeat(72));
    printWbs(wbs);

    const baselineHours = wbs.totalHours();

    console.log(`\nBaseline effort: ${baselineHours} hours`);

    const workPackages = getLeafWorkPackages(wbs);
    console.log(`Work packages: ${workPackages.length}`);

    const matrix = buildTraceabilityMatrix(
        requirements,
        deliverables
    );

    printTraceability(matrix);

    console.log("\nACCEPTANCE TEST");
    console.log("-".repeat(72));

    const workflow = deliverables[2];

    const observedResults = {
        "Managers can approve requests.": true,
        "Managers can reject requests.": true,
        "Employees can see resulting status.": false
    };

    const acceptance = validateDeliverable(
        workflow,
        observedResults
    );

    console.log("Accepted:", acceptance.accepted);

    if (!acceptance.accepted) {
        console.log("Failed criteria:");

        acceptance.failures.forEach(failure => {
            console.log(`  - ${failure}`);
        });
    }

    console.log("\nAMBIGUITY CHECK");
    console.log("-".repeat(72));

    const statements = [
        "The system should be fast and user-friendly.",
        "The system shall return results within 2 seconds for 95% of requests."
    ];

    statements.forEach(statement => {
        console.log(`Statement: ${statement}`);
        console.log(
            "Vague terms:",
            findVagueTerms(statement).join(", ") || "None"
        );
    });

    console.log("\nCHANGE CONTROL");
    console.log("-".repeat(72));

    const change = new ChangeRequest({
        id: "CR-001",
        description:
            "Add mobile push notifications for leave approvals.",
        reason:
            "Stakeholders requested real-time approval alerts.",
        requestedBy: "HR Director",
        estimatedHours: 24,
        estimatedCost: 500,
        scheduleDays: 3,
        affectedDeliverables: ["DEL-003"]
    });

    const changeAnalysis = analyzeChange(
        change,
        baselineHours,
        45
    );

    console.table(changeAnalysis);

    console.log("\nSCOPE CREEP DETECTION");
    console.log("-".repeat(72));

    const proposedRequests = [
        "Add payroll calculation and tax deductions.",
        "Add manager approval and rejection.",
        "Add employee leave request submission."
    ];

    for (const request of proposedRequests) {
        const result = detectScopeCreep(
            request,
            scope.inScope
        );

        console.log(`\nRequest: ${request}`);
        console.log("Likely new scope:", result.likelyNewScope);
        console.log(
            "Related approved items:",
            result.relatedScope.join(", ") || "None"
        );
    }

    console.log("\nIMMUTABLE-STYLE CHANGE EXAMPLE");
    console.log("-".repeat(72));

    const proposedScope = proposeScopeAddition(
        scope,
        "Standard audit report"
    );

    console.log(
        "Original scope item count:",
        scope.inScope.length
    );

    console.log(
        "Proposed scope item count:",
        proposedScope.inScope.length
    );

    console.log(
        "Original scope preserved:",
        scope.inScope.length !== proposedScope.inScope.length
    );

    console.log("\nCAPACITY ESTIMATION");
    console.log("-".repeat(72));

    [1, 2, 4].forEach(teamSize => {
        const duration = calculateDuration(
            baselineHours,
            teamSize
        );

        console.log(
            `${teamSize} person(s): ${duration.toFixed(2)} nominal working days`
        );
    });

    const performanceResult = measureLookupPerformance(workPackages);

    console.log("\nMAP LOOKUP PERFORMANCE");
    console.log("-".repeat(72));
    console.log(
        "Lookup result:",
        performanceResult.result.name
    );
    console.log(
        `Lookup elapsed: ${performanceResult.elapsedMilliseconds.toFixed(4)} ms`
    );

    await demonstrateApproval();

    console.log("\nSCOPE CONTROL PRINCIPLES");
    console.log("-".repeat(72));

    const principles = [
        "Define purpose before listing features.",
        "Use measurable objectives.",
        "Make requirements testable.",
        "State inclusions and exclusions explicitly.",
        "Record assumptions and constraints.",
        "Build a WBS from approved scope.",
        "Connect requirements to deliverables and tests.",
        "Establish an approved baseline.",
        "Evaluate requested changes before implementation.",
        "Assess cost, effort, schedule, risk, and dependencies.",
        "Do not treat informal requests as automatically approved scope.",
        "Keep decisions auditable."
    ];

    principles.forEach(
        (principle, index) =>
            console.log(`${String(index + 1).padStart(2, "0")}. ${principle}`)
    );

    console.log("\nProgram completed.");
}


main().catch(error => {
    console.error("\nExecution error:", error.message);
    process.exitCode = 1;
});
