/*
 * Project Charter: Understanding Project Authorization
 *
 * Self-contained JavaScript study program.
 *
 * The examples complement the Python implementation by emphasizing:
 * - JavaScript data modeling
 * - Objects and classes
 * - Functional array processing
 * - Validation
 * - Event-driven authorization decisions
 * - Promise-based asynchronous governance simulation
 * - JSON serialization
 * - Error handling
 * - Change requests
 * - Traceability
 * - Browser-compatible concepts
 *
 * Run with:
 *     node project-charter.js
 */

// -----------------------------------------------------------------------------
// 1. BEGINNER LEVEL: BASIC CHARTER CONCEPTS
// -----------------------------------------------------------------------------

console.log("=".repeat(78));
console.log("PROJECT CHARTER: UNDERSTANDING PROJECT AUTHORIZATION");
console.log("=".repeat(78));

const projectVsOperations = {
    project: {
        temporary: true,
        uniqueResult: true,
        example: "Implement a new customer-support platform"
    },
    operations: {
        temporary: false,
        uniqueResult: false,
        example: "Process customer-support tickets every day"
    }
};

function classifyWork(work) {
    if (work.temporary && work.uniqueResult) {
        return "Project";
    }
    return "Operational work";
}

console.log("\nWork classification:");
console.log(
    projectVsOperations.project.example,
    "=>",
    classifyWork(projectVsOperations.project)
);
console.log(
    projectVsOperations.operations.example,
    "=>",
    classifyWork(projectVsOperations.operations)
);


// -----------------------------------------------------------------------------
// 2. OBJECT-BASED CHARTER MODEL
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("2. PROJECT CHARTER DATA MODEL");
console.log("=".repeat(78));

class Objective {
    constructor(description, criteria = {}) {
        this.description = description;
        this.specific = Boolean(criteria.specific);
        this.measurable = Boolean(criteria.measurable);
        this.achievable = Boolean(criteria.achievable);
        this.relevant = Boolean(criteria.relevant);
        this.timeBound = Boolean(criteria.timeBound);
    }

    get smart() {
        return (
            this.specific &&
            this.measurable &&
            this.achievable &&
            this.relevant &&
            this.timeBound
        );
    }

    get score() {
        return [
            this.specific,
            this.measurable,
            this.achievable,
            this.relevant,
            this.timeBound
        ].filter(Boolean).length;
    }
}

class Risk {
    constructor(id, description, probability, impact, response) {
        this.id = id;
        this.description = description;
        this.probability = probability;
        this.impact = impact;
        this.response = response;
    }

    get exposure() {
        return this.probability * this.impact;
    }

    get severity() {
        if (this.exposure >= 16) return "Critical";
        if (this.exposure >= 9) return "High";
        if (this.exposure >= 4) return "Medium";
        return "Low";
    }
}

class Stakeholder {
    constructor(name, role, influence, interest) {
        this.name = name;
        this.role = role;
        this.influence = influence;
        this.interest = interest;
    }

    get engagementStrategy() {
        if (this.influence >= 4 && this.interest >= 4) {
            return "Manage closely";
        }
        if (this.influence >= 4) {
            return "Keep satisfied";
        }
        if (this.interest >= 4) {
            return "Keep informed";
        }
        return "Monitor";
    }
}

class ProjectCharter {
    constructor(data) {
        Object.assign(this, data);
        this.status = "Draft";
        this.version = 1;
    }

    validate() {
        const errors = [];

        const requiredText = [
            ["projectId", this.projectId],
            ["title", this.title],
            ["sponsor", this.sponsor],
            ["projectManager", this.projectManager],
            ["purpose", this.purpose],
            ["businessCase", this.businessCase]
        ];

        for (const [field, value] of requiredText) {
            if (typeof value !== "string" || value.trim() === "") {
                errors.push(`${field} is missing.`);
            }
        }

        if (!Array.isArray(this.objectives) || this.objectives.length === 0) {
            errors.push("At least one objective is required.");
        } else if (!this.objectives.every(objective => objective.smart)) {
            errors.push("Every authorization-level objective should be SMART.");
        }

        if (!this.inScope?.length) {
            errors.push("In-scope boundaries are missing.");
        }

        if (!this.outOfScope?.length) {
            errors.push("Out-of-scope boundaries are missing.");
        }

        if (!this.deliverables?.length) {
            errors.push("Deliverables are missing.");
        }

        if (!this.milestones?.length) {
            errors.push("Milestones are missing.");
        }

        if (!this.stakeholders?.length) {
            errors.push("Stakeholders are missing.");
        }

        if (!this.acceptanceCriteria?.length) {
            errors.push("Acceptance criteria are missing.");
        }

        if (!Number.isFinite(this.budgetCeiling) || this.budgetCeiling <= 0) {
            errors.push("Budget ceiling must be greater than zero.");
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    authorize() {
        const result = this.validate();

        if (!result.valid) {
            this.status = "Under Review";
            return {
                approved: false,
                reason: result.errors
            };
        }

        this.status = "Authorized";

        return {
            approved: true,
            reason: ["All minimum authorization conditions passed."]
        };
    }

    revise() {
        this.version += 1;
        this.status = "Draft";
    }

    toJSON() {
        return {
            projectId: this.projectId,
            title: this.title,
            sponsor: this.sponsor,
            projectManager: this.projectManager,
            purpose: this.purpose,
            businessCase: this.businessCase,
            status: this.status,
            version: this.version,
            budgetCeiling: this.budgetCeiling
        };
    }
}


// -----------------------------------------------------------------------------
// 3. BUILD A REALISTIC CHARTER
// -----------------------------------------------------------------------------

const responseTimeObjective = new Objective(
    "Reduce average customer-support response time from 12 hours to 4 hours within six months.",
    {
        specific: true,
        measurable: true,
        achievable: true,
        relevant: true,
        timeBound: true
    }
);

const charter = new ProjectCharter({
    projectId: "PRJ-JS-001",
    title: "Customer Support Response Transformation",
    sponsor: "Chief Customer Officer",
    projectManager: "Project Delivery Manager",
    purpose: "Reduce customer waiting time and improve service quality.",
    businessCase:
        "Long response times increase customer dissatisfaction and operating cost.",
    strategicAlignment: [
        "Improve customer experience",
        "Reduce avoidable service cost",
        "Increase operational efficiency"
    ],
    objectives: [responseTimeObjective],
    inScope: [
        "Support workflow redesign",
        "Response-time dashboard",
        "Notification rules"
    ],
    outOfScope: [
        "Replacing the enterprise CRM",
        "Changing product pricing",
        "Redesigning unrelated sales workflows"
    ],
    deliverables: [
        "Approved workflow design",
        "Operational dashboard",
        "Notification mechanism",
        "Training package"
    ],
    milestones: [
        { name: "Charter authorization", targetDate: "2026-10-01" },
        { name: "Process design", targetDate: "2026-11-01" },
        { name: "Pilot", targetDate: "2026-12-15" },
        { name: "Production rollout", targetDate: "2027-01-15" }
    ],
    assumptions: [
        "Business users provide timely requirements.",
        "Existing source data is usable."
    ],
    constraints: [
        "Budget ceiling cannot be exceeded.",
        "Existing CRM remains in place."
    ],
    risks: [
        new Risk(
            "R-001",
            "Legacy data may be incomplete.",
            0.6,
            8,
            "Perform data-quality assessment."
        ),
        new Risk(
            "R-002",
            "Users may resist process changes.",
            0.5,
            7,
            "Use training and stakeholder workshops."
        ),
        new Risk(
            "R-003",
            "Integration work may take longer than expected.",
            0.4,
            9,
            "Prototype critical integrations early."
        )
    ],
    stakeholders: [
        new Stakeholder("Chief Customer Officer", "Sponsor", 5, 5),
        new Stakeholder("Support Operations Lead", "Business Owner", 5, 5),
        new Stakeholder("Support Agents", "Users", 3, 5),
        new Stakeholder("Finance", "Control Function", 4, 3)
    ],
    acceptanceCriteria: [
        "Response-time measurement is operational.",
        "Pilot users can execute the redesigned process.",
        "Dashboard results reconcile with source data.",
        "Sponsor accepts the rollout package."
    ],
    budgetCeiling: 250000
});

console.log("\nCharter validation:");
console.log(charter.validate());

const authorizationResult = charter.authorize();

console.log("\nAuthorization result:");
console.log(authorizationResult);
console.log("Current status:", charter.status);


// -----------------------------------------------------------------------------
// 4. FUNCTIONAL PROGRAMMING FOR RISK ANALYSIS
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("4. RISK ANALYSIS USING JAVASCRIPT ARRAY METHODS");
console.log("=".repeat(78));

const riskRegister = charter.risks
    .map(risk => ({
        id: risk.id,
        description: risk.description,
        exposure: risk.exposure,
        severity: risk.severity,
        response: risk.response
    }))
    .sort((a, b) => b.exposure - a.exposure);

for (const risk of riskRegister) {
    console.log(
        `${risk.id}: ${risk.severity}, exposure=${risk.exposure.toFixed(2)}`
    );
}

const highRisks = riskRegister.filter(
    risk => risk.severity === "High" || risk.severity === "Critical"
);

console.log("\nHigh or critical risks:");
for (const risk of highRisks) {
    console.log(`- ${risk.id}: ${risk.description}`);
}


// -----------------------------------------------------------------------------
// 5. STAKEHOLDER PRIORITIZATION
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("5. STAKEHOLDER PRIORITIZATION");
console.log("=".repeat(78));

const stakeholdersByStrategy = charter.stakeholders.reduce(
    (groups, stakeholder) => {
        const strategy = stakeholder.engagementStrategy;

        if (!groups[strategy]) {
            groups[strategy] = [];
        }

        groups[strategy].push(stakeholder.name);
        return groups;
    },
    {}
);

console.log(JSON.stringify(stakeholdersByStrategy, null, 2));


// -----------------------------------------------------------------------------
// 6. STRATEGIC TRACEABILITY
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("6. STRATEGIC TRACEABILITY");
console.log("=".repeat(78));

const traceability = charter.objectives.flatMap(objective =>
    charter.deliverables.map(deliverable => ({
        objective: objective.description,
        deliverable,
        relationship: "Deliverable contributes to objective"
    }))
);

console.log(traceability.slice(0, 4));


// -----------------------------------------------------------------------------
// 7. CHANGE REQUEST EVALUATION
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("7. CHANGE REQUEST EVALUATION");
console.log("=".repeat(78));

function evaluateChangeRequest(change) {
    const significant =
        change.budgetImpact !== 0 ||
        change.scheduleImpactDays !== 0 ||
        change.scopeImpact !== "None";

    return {
        ...change,
        significant,
        governanceReviewRequired: significant
    };
}

const changeRequest = {
    id: "CR-001",
    description: "Add a second customer-support channel.",
    requestedBy: "Support Operations Lead",
    scopeImpact: "High",
    budgetImpact: 40000,
    scheduleImpactDays: 20
};

console.log(evaluateChangeRequest(changeRequest));


// -----------------------------------------------------------------------------
// 8. ASYNCHRONOUS GOVERNANCE SIMULATION
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("8. ASYNCHRONOUS AUTHORIZATION WORKFLOW");
console.log("=".repeat(78));

function submitForGovernance(projectCharter) {
    return new Promise((resolve, reject) => {
        // Promise represents work that completes asynchronously, such as
        // an approval API, workflow system, or governance platform.
        setTimeout(() => {
            const validation = projectCharter.validate();

            if (!validation.valid) {
                reject(
                    new Error(
                        "Governance review failed: " +
                        validation.errors.join("; ")
                    )
                );
                return;
            }

            resolve({
                decision: "Approved",
                approvedBy: projectCharter.sponsor,
                recordedAt: new Date().toISOString()
            });
        }, 100);
    });
}

submitForGovernance(charter)
    .then(decision => {
        console.log("Governance decision:", decision);
    })
    .catch(error => {
        console.error("Governance error:", error.message);
    });


// -----------------------------------------------------------------------------
// 9. JSON SERIALIZATION
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("9. SERIALIZING AN AUTHORIZED CHARTER");
console.log("=".repeat(78));

const serializedCharter = JSON.stringify(charter, null, 2);
console.log(serializedCharter);


// -----------------------------------------------------------------------------
// 10. ERROR HANDLING AND EDGE CASES
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("10. EDGE CASES AND ERROR HANDLING");
console.log("=".repeat(78));

const invalidCharter = new ProjectCharter({
    projectId: "",
    title: "",
    sponsor: "",
    projectManager: "",
    purpose: "",
    businessCase: "",
    strategicAlignment: [],
    objectives: [],
    inScope: [],
    outOfScope: [],
    deliverables: [],
    milestones: [],
    assumptions: [],
    constraints: [],
    risks: [],
    stakeholders: [],
    acceptanceCriteria: [],
    budgetCeiling: 0
});

try {
    const result = invalidCharter.authorize();

    if (!result.approved) {
        throw new Error(
            "Authorization cannot proceed: " +
            result.reason.join("; ")
        );
    }
} catch (error) {
    console.log("Handled authorization error:");
    console.log(error.message);
}


// -----------------------------------------------------------------------------
// 11. BROWSER-SIDE CONCEPT
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("11. BROWSER-SIDE APPLICATION PATTERN");
console.log("=".repeat(78));

function createAuthorizationButtonHandler(projectCharter) {
    // This function can be connected to a browser button:
    //
    // document
    //     .querySelector("#authorize")
    //     .addEventListener("click", handler);
    //
    // It is kept executable in Node by returning the event handler rather
    // than directly accessing document.
    return function handleAuthorizationClick() {
        const result = projectCharter.authorize();

        return {
            status: projectCharter.status,
            result
        };
    };
}

const authorizationHandler = createAuthorizationButtonHandler(charter);
console.log(authorizationHandler());


// -----------------------------------------------------------------------------
// 12. PERFORMANCE CONSIDERATIONS
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("12. PERFORMANCE CONSIDERATIONS");
console.log("=".repeat(78));

function estimateRiskAnalysisCost(numberOfRisks) {
    /*
     * map() and sort() are useful for a risk register.
     *
     * Mapping is O(n).
     * Sorting is O(n log n) in typical comparison-based implementations.
     *
     * For normal project-charter sizes, this cost is negligible.
     * Performance becomes relevant only if governance data is processed
     * at organizational scale.
     */
    if (!Number.isInteger(numberOfRisks) || numberOfRisks < 0) {
        throw new RangeError("numberOfRisks must be a non-negative integer.");
    }

    if (numberOfRisks <= 1) return "Approximately O(n)";
    return "Approximately O(n log n) because ranking requires sorting.";
}

console.log(estimateRiskAnalysisCost(charter.risks.length));


// -----------------------------------------------------------------------------
// 13. SIMPLE TESTS
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("13. TESTS");
console.log("=".repeat(78));

function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

assert(responseTimeObjective.smart, "Objective should be SMART.");
assert(responseTimeObjective.score === 5, "SMART score should be five.");
assert(charter.status === "Authorized", "Charter should be authorized.");
assert(charter.risks[0].exposure === 4.8, "Risk exposure should equal 4.8.");
assert(highRisks.length === 1, "One risk should be classified as High.");

const invalidValidation = invalidCharter.validate();
assert(
    invalidValidation.valid === false,
    "Invalid charter should fail validation."
);

console.log("All tests passed.");


// -----------------------------------------------------------------------------
// 14. COMPLETE GOVERNANCE SEQUENCE
// -----------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("14. AUTHORIZATION GOVERNANCE SEQUENCE");
console.log("=".repeat(78));

const governanceSequence = [
    "Identify business problem or opportunity",
    "Develop business case",
    "Confirm strategic alignment",
    "Define preliminary objectives",
    "Define high-level scope",
    "Identify deliverables and milestones",
    "Identify sponsor and project manager",
    "Identify major stakeholders",
    "Document assumptions and constraints",
    "Identify material risks",
    "Define acceptance criteria",
    "Establish funding boundary",
    "Draft charter",
    "Review charter",
    "Resolve material gaps",
    "Obtain formal authorization",
    "Record approval and version",
    "Begin detailed project planning"
];

governanceSequence.forEach((step, index) => {
    console.log(`${String(index + 1).padStart(2, " ")}. ${step}`);
});

console.log("\nFinal charter status:", charter.status);
console.log("Final charter version:", charter.version);
console.log("Budget ceiling:", charter.budgetCeiling.toLocaleString("en-IN"));

console.log(
    "\nThe implementation demonstrates that a project charter is not merely " +
    "documentation. It is an authorization and governance mechanism that " +
    "establishes purpose, authority, boundaries, accountability, and the " +
    "basis for moving into detailed project planning."
);
