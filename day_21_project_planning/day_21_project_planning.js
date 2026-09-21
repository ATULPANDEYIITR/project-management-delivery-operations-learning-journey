/*
 * Project Planning: Practical JavaScript Study Program
 *
 * This file demonstrates project planning through executable examples.
 * It focuses on data modeling, validation, dependency analysis, scheduling,
 * Agile planning, risk management, metrics, and scenario analysis.
 *
 * Runtime: modern Node.js or another modern JavaScript runtime.
 */

"use strict";

// ---------------------------------------------------------------------------
// 1. BASIC PROJECT PLANNING CONCEPTS
// ---------------------------------------------------------------------------

function printSection(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function demonstrateFundamentals() {
    printSection("1. Project Planning Fundamentals");

    const concepts = {
        Project: "A temporary effort that creates a defined result.",
        Objective: "A measurable outcome the project intends to achieve.",
        Scope: "The boundaries of what the project will and will not deliver.",
        Deliverable: "A verifiable output produced by project work.",
        Milestone: "A significant checkpoint in the project.",
        Task: "A unit of work required to produce a result.",
        Dependency: "A relationship controlling the order of work.",
        Stakeholder: "A person or organization affected by the project.",
        Constraint: "A limitation such as time, cost, or resources.",
        Risk: "An uncertain event that may affect objectives.",
        Issue: "A problem that has already happened.",
        Baseline: "An approved plan used to measure performance."
    };

    for (const [term, definition] of Object.entries(concepts)) {
        console.log(`${term}: ${definition}`);
    }
}

// ---------------------------------------------------------------------------
// 2. PROJECT CHARTER
// ---------------------------------------------------------------------------

class ProjectCharter {
    constructor({
        name,
        purpose,
        sponsor,
        projectManager,
        startDate,
        targetDate,
        budget,
        inScope,
        outOfScope
    }) {
        this.name = name;
        this.purpose = purpose;
        this.sponsor = sponsor;
        this.projectManager = projectManager;
        this.startDate = startDate;
        this.targetDate = targetDate;
        this.budget = budget;
        this.inScope = inScope;
        this.outOfScope = outOfScope;
    }

    validate() {
        const errors = [];

        if (!this.name.trim()) {
            errors.push("Project name cannot be empty.");
        }

        if (!(this.startDate instanceof Date) ||
            Number.isNaN(this.startDate.getTime())) {
            errors.push("Start date is invalid.");
        }

        if (!(this.targetDate instanceof Date) ||
            Number.isNaN(this.targetDate.getTime())) {
            errors.push("Target date is invalid.");
        }

        if (this.startDate > this.targetDate) {
            errors.push("Target date cannot precede start date.");
        }

        if (this.budget < 0) {
            errors.push("Budget cannot be negative.");
        }

        if (!Array.isArray(this.inScope) || this.inScope.length === 0) {
            errors.push("At least one scope item is required.");
        }

        return errors;
    }

    display() {
        console.log(`Project: ${this.name}`);
        console.log(`Purpose: ${this.purpose}`);
        console.log(`Sponsor: ${this.sponsor}`);
        console.log(`Project manager: ${this.projectManager}`);
        console.log(`Start: ${this.startDate.toISOString().slice(0, 10)}`);
        console.log(`Target: ${this.targetDate.toISOString().slice(0, 10)}`);
        console.log(`Budget: $${this.budget.toLocaleString()}`);

        console.log("In scope:");
        this.inScope.forEach(item => console.log(`  - ${item}`));

        console.log("Out of scope:");
        this.outOfScope.forEach(item => console.log(`  - ${item}`));
    }
}

// ---------------------------------------------------------------------------
// 3. REQUIREMENTS
// ---------------------------------------------------------------------------

const RequirementPriority = Object.freeze({
    MUST: 4,
    SHOULD: 3,
    COULD: 2,
    WONT: 1
});

class Requirement {
    constructor(id, description, priority, acceptanceCriteria) {
        this.id = id;
        this.description = description;
        this.priority = priority;
        this.acceptanceCriteria = acceptanceCriteria;
    }

    validate() {
        return (
            this.id.trim().length > 0 &&
            this.description.trim().length > 0 &&
            Array.isArray(this.acceptanceCriteria) &&
            this.acceptanceCriteria.length > 0
        );
    }
}

function demonstrateRequirements() {
    printSection("2. Requirements and Acceptance Criteria");

    const requirements = [
        new Requirement(
            "REQ-001",
            "Users can securely authenticate.",
            RequirementPriority.MUST,
            [
                "Valid credentials are accepted.",
                "Invalid credentials are rejected."
            ]
        ),
        new Requirement(
            "REQ-002",
            "Users can generate portfolio reports.",
            RequirementPriority.MUST,
            [
                "A report can be generated from holdings.",
                "The report contains a timestamp."
            ]
        ),
        new Requirement(
            "REQ-003",
            "Users can select dashboard themes.",
            RequirementPriority.COULD,
            [
                "Theme selection persists."
            ]
        )
    ];

    requirements.forEach(requirement => {
        console.log(
            `${requirement.id}: ${requirement.description} | ` +
            `valid=${requirement.validate()}`
        );

        requirement.acceptanceCriteria.forEach(criteria => {
            console.log(`  Acceptance: ${criteria}`);
        });
    });

    return requirements;
}

// ---------------------------------------------------------------------------
// 4. TASK MODEL
// ---------------------------------------------------------------------------

class Task {
    constructor(id, name, durationDays, cost, dependencies = [], resource = "Unassigned") {
        this.id = id;
        this.name = name;
        this.durationDays = durationDays;
        this.cost = cost;
        this.dependencies = dependencies;
        this.resource = resource;
    }

    validate(allTasks) {
        if (this.durationDays < 0) {
            throw new Error(`${this.id}: duration cannot be negative.`);
        }

        if (this.cost < 0) {
            throw new Error(`${this.id}: cost cannot be negative.`);
        }

        for (const dependency of this.dependencies) {
            if (!allTasks.has(dependency)) {
                throw new Error(
                    `${this.id}: dependency ${dependency} does not exist.`
                );
            }
        }
    }
}

function buildTasks() {
    return new Map([
        ["T1", new Task(
            "T1",
            "Requirements analysis",
            4,
            1800,
            [],
            "Business Analyst"
        )],
        ["T2", new Task(
            "T2",
            "Architecture design",
            5,
            3000,
            ["T1"],
            "Solution Architect"
        )],
        ["T3", new Task(
            "T3",
            "Database implementation",
            6,
            3600,
            ["T2"],
            "Database Engineer"
        )],
        ["T4", new Task(
            "T4",
            "Backend implementation",
            10,
            7200,
            ["T2"],
            "Backend Engineer"
        )],
        ["T5", new Task(
            "T5",
            "Frontend implementation",
            9,
            6300,
            ["T2"],
            "Frontend Engineer"
        )],
        ["T6", new Task(
            "T6",
            "Integration testing",
            5,
            3200,
            ["T3", "T4", "T5"],
            "QA Engineer"
        )],
        ["T7", new Task(
            "T7",
            "Security testing",
            4,
            2800,
            ["T6"],
            "Security Engineer"
        )],
        ["T8", new Task(
            "T8",
            "Production deployment",
            2,
            1600,
            ["T7"],
            "DevOps Engineer"
        )],
        ["T9", new Task(
            "T9",
            "Operational documentation",
            3,
            1200,
            ["T6"],
            "Technical Writer"
        )]
    ]);
}

// ---------------------------------------------------------------------------
// 5. DEPENDENCY VALIDATION
// ---------------------------------------------------------------------------

function validateTasks(tasks) {
    for (const task of tasks.values()) {
        task.validate(tasks);
    }
}

function topologicalSort(tasks) {
    const indegree = new Map();
    const successors = new Map();

    for (const id of tasks.keys()) {
        indegree.set(id, 0);
        successors.set(id, []);
    }

    for (const task of tasks.values()) {
        for (const dependency of task.dependencies) {
            indegree.set(task.id, indegree.get(task.id) + 1);
            successors.get(dependency).push(task.id);
        }
    }

    const queue = [...indegree.entries()]
        .filter(([, degree]) => degree === 0)
        .map(([id]) => id)
        .sort();

    const result = [];

    while (queue.length > 0) {
        const current = queue.shift();
        result.push(current);

        for (const successor of successors.get(current).sort()) {
            indegree.set(successor, indegree.get(successor) - 1);

            if (indegree.get(successor) === 0) {
                queue.push(successor);
            }
        }
    }

    if (result.length !== tasks.size) {
        throw new Error("Circular dependency detected.");
    }

    return result;
}

// ---------------------------------------------------------------------------
// 6. CRITICAL PATH METHOD
// ---------------------------------------------------------------------------

function criticalPathAnalysis(tasks) {
    const order = topologicalSort(tasks);

    const earliestStart = new Map();
    const earliestFinish = new Map();

    for (const id of order) {
        const task = tasks.get(id);

        const start = task.dependencies.length === 0
            ? 0
            : Math.max(
                ...task.dependencies.map(
                    dependency => earliestFinish.get(dependency)
                )
            );

        earliestStart.set(id, start);
        earliestFinish.set(id, start + task.durationDays);
    }

    const projectDuration = Math.max(...earliestFinish.values());

    const latestStart = new Map();
    const latestFinish = new Map();

    for (const id of [...order].reverse()) {
        const task = tasks.get(id);

        const successors = [...tasks.values()]
            .filter(candidate => candidate.dependencies.includes(id));

        const finish = successors.length === 0
            ? projectDuration
            : Math.min(
                ...successors.map(successor => latestStart.get(successor.id))
            );

        latestFinish.set(id, finish);
        latestStart.set(id, finish - task.durationDays);
    }

    const result = new Map();

    for (const id of order) {
        const floatDays = latestStart.get(id) - earliestStart.get(id);

        result.set(id, {
            earliestStart: earliestStart.get(id),
            earliestFinish: earliestFinish.get(id),
            latestStart: latestStart.get(id),
            latestFinish: latestFinish.get(id),
            floatDays,
            critical: floatDays === 0
        });
    }

    return {
        entries: result,
        duration: projectDuration
    };
}

function demonstrateCriticalPath(tasks) {
    printSection("3. Critical Path Method");

    const analysis = criticalPathAnalysis(tasks);

    for (const [id, entry] of analysis.entries) {
        console.log(
            `${id}: ES=${entry.earliestStart} ` +
            `EF=${entry.earliestFinish} ` +
            `LS=${entry.latestStart} ` +
            `LF=${entry.latestFinish} ` +
            `Float=${entry.floatDays}` +
            `${entry.critical ? " CRITICAL" : ""}`
        );
    }

    console.log(`Project duration: ${analysis.duration} working days`);

    return analysis;
}

// ---------------------------------------------------------------------------
// 7. WORKING-DAY CALENDAR
// ---------------------------------------------------------------------------

function addWorkingDays(startDate, numberOfDays) {
    if (numberOfDays < 0) {
        throw new Error("Working days cannot be negative.");
    }

    const result = new Date(startDate);
    let remaining = numberOfDays;

    while (remaining > 0) {
        result.setDate(result.getDate() + 1);

        const day = result.getDay();

        if (day !== 0 && day !== 6) {
            remaining--;
        }
    }

    return result;
}

function demonstrateCalendar(tasks, analysis) {
    printSection("4. Calendar Scheduling");

    const projectStart = new Date("2026-10-05T00:00:00Z");

    for (const [id, entry] of analysis.entries) {
        const start = addWorkingDays(projectStart, entry.earliestStart);
        const finish = addWorkingDays(projectStart, entry.earliestFinish);

        console.log(
            `${id} ${tasks.get(id).name}: ` +
            `${start.toISOString().slice(0, 10)} -> ` +
            `${finish.toISOString().slice(0, 10)}`
        );
    }
}

// ---------------------------------------------------------------------------
// 8. PERT ESTIMATION
// ---------------------------------------------------------------------------

function threePointEstimate(optimistic, likely, pessimistic) {
    if (
        optimistic < 0 ||
        likely < 0 ||
        pessimistic < 0
    ) {
        throw new Error("Estimates cannot be negative.");
    }

    if (!(optimistic <= likely && likely <= pessimistic)) {
        throw new Error("Expected ordering is optimistic <= likely <= pessimistic.");
    }

    const expected = (
        optimistic +
        4 * likely +
        pessimistic
    ) / 6;

    const standardDeviation = (
        pessimistic - optimistic
    ) / 6;

    return {
        expected,
        standardDeviation
    };
}

function demonstrateEstimation() {
    printSection("5. Three-Point Estimation");

    const estimates = [
        ["API development", 6, 10, 18],
        ["Security testing", 2, 4, 9],
        ["Deployment", 1, 2, 4]
    ];

    estimates.forEach(([name, optimistic, likely, pessimistic]) => {
        const result = threePointEstimate(
            optimistic,
            likely,
            pessimistic
        );

        console.log(
            `${name}: expected=${result.expected.toFixed(2)} ` +
            `uncertainty=${result.standardDeviation.toFixed(2)}`
        );
    });
}

// ---------------------------------------------------------------------------
// 9. COST PLANNING
// ---------------------------------------------------------------------------

function calculateTotalCost(tasks) {
    let total = 0;

    for (const task of tasks.values()) {
        total += task.cost;
    }

    return total;
}

function demonstrateCostPlanning(tasks) {
    printSection("6. Cost Planning");

    const directCost = calculateTotalCost(tasks);
    const contingency = directCost * 0.10;
    const planningBudget = directCost + contingency;

    console.log(`Direct task cost: $${directCost.toLocaleString()}`);
    console.log(`10% contingency: $${contingency.toLocaleString()}`);
    console.log(`Planning budget: $${planningBudget.toLocaleString()}`);
}

// ---------------------------------------------------------------------------
// 10. STAKEHOLDER MANAGEMENT
// ---------------------------------------------------------------------------

function stakeholderStrategy(influence, interest) {
    if (influence === "High" && interest === "High") {
        return "Manage closely";
    }

    if (influence === "High") {
        return "Keep satisfied";
    }

    if (interest === "High") {
        return "Keep informed";
    }

    return "Monitor";
}

function demonstrateStakeholders() {
    printSection("7. Stakeholder Analysis");

    const stakeholders = [
        {
            name: "Executive Sponsor",
            role: "Funding and strategic decisions",
            influence: "High",
            interest: "High"
        },
        {
            name: "Product Owner",
            role: "Prioritization and acceptance",
            influence: "High",
            interest: "High"
        },
        {
            name: "Security Team",
            role: "Security assurance",
            influence: "Medium",
            interest: "High"
        },
        {
            name: "End Users",
            role: "Feedback and usage",
            influence: "Medium",
            interest: "High"
        }
    ];

    stakeholders.forEach(stakeholder => {
        console.log(
            `${stakeholder.name}: ` +
            `${stakeholderStrategy(stakeholder.influence, stakeholder.interest)}`
        );
    });
}

// ---------------------------------------------------------------------------
// 11. RISK REGISTER
// ---------------------------------------------------------------------------

class Risk {
    constructor(id, description, probability, impact, response, mitigation) {
        this.id = id;
        this.description = description;
        this.probability = probability;
        this.impact = impact;
        this.response = response;
        this.mitigation = mitigation;
    }

    get exposure() {
        return this.probability * this.impact;
    }

    validate() {
        if (this.probability < 0 || this.probability > 1) {
            throw new Error("Probability must be between 0 and 1.");
        }

        if (this.impact < 0) {
            throw new Error("Impact cannot be negative.");
        }
    }
}

function demonstrateRiskManagement() {
    printSection("8. Risk Management");

    const risks = [
        new Risk(
            "R1",
            "External data provider becomes unavailable",
            0.30,
            8,
            "Mitigate",
            "Use caching and a fallback source."
        ),
        new Risk(
            "R2",
            "Critical security defect is discovered late",
            0.20,
            10,
            "Mitigate",
            "Perform security testing before final release."
        ),
        new Risk(
            "R3",
            "Specialist resource becomes unavailable",
            0.15,
            7,
            "Mitigate",
            "Cross-train team members."
        )
    ];

    risks.forEach(risk => {
        risk.validate();

        console.log(
            `${risk.id}: exposure=${risk.exposure.toFixed(2)}, ` +
            `response=${risk.response}, mitigation=${risk.mitigation}`
        );
    });

    return risks;
}

// ---------------------------------------------------------------------------
// 12. CHANGE CONTROL
// ---------------------------------------------------------------------------

class ChangeRequest {
    constructor(id, description, scopeImpact, scheduleImpactDays, costImpact) {
        this.id = id;
        this.description = description;
        this.scopeImpact = scopeImpact;
        this.scheduleImpactDays = scheduleImpactDays;
        this.costImpact = costImpact;
        this.approved = false;
    }

    approve() {
        this.approved = true;
    }
}

function demonstrateChangeControl() {
    printSection("9. Change Control");

    const change = new ChangeRequest(
        "CR-001",
        "Add multi-currency support",
        0.12,
        6,
        8500
    );

    console.log(`Description: ${change.description}`);
    console.log(`Scope impact: ${(change.scopeImpact * 100).toFixed(1)}%`);
    console.log(`Schedule impact: ${change.scheduleImpactDays} days`);
    console.log(`Cost impact: $${change.costImpact.toLocaleString()}`);
    console.log(`Approved: ${change.approved}`);

    change.approve();

    console.log(`Approved after evaluation: ${change.approved}`);
}

// ---------------------------------------------------------------------------
// 13. AGILE SPRINT PLANNING
// ---------------------------------------------------------------------------

class Sprint {
    constructor(number, capacityPoints) {
        this.number = number;
        this.capacityPoints = capacityPoints;
        this.items = [];
    }

    get committedPoints() {
        return this.items.reduce(
            (total, item) => total + item.storyPoints,
            0
        );
    }

    addItem(item) {
        if (
            this.committedPoints + item.storyPoints >
            this.capacityPoints
        ) {
            return false;
        }

        this.items.push(item);
        return true;
    }
}

function demonstrateSprintPlanning() {
    printSection("10. Agile Sprint Planning");

    const sprint = new Sprint(1, 20);

    const items = [
        {
            id: "US-1",
            description: "Secure login",
            storyPoints: 5,
            acceptanceCriteria: [
                "Valid users can authenticate.",
                "Invalid users are rejected."
            ]
        },
        {
            id: "US-2",
            description: "Portfolio dashboard",
            storyPoints: 8,
            acceptanceCriteria: [
                "Holdings are displayed.",
                "Calculations are correct."
            ]
        },
        {
            id: "US-3",
            description: "CSV export",
            storyPoints: 3,
            acceptanceCriteria: [
                "Required fields are exported."
            ]
        },
        {
            id: "US-4",
            description: "Custom theme",
            storyPoints: 5,
            acceptanceCriteria: [
                "Theme persists."
            ]
        }
    ];

    items.forEach(item => {
        console.log(
            `${item.id}: ` +
            `${sprint.addItem(item) ? "committed" : "not committed"}`
        );
    });

    console.log(`Committed points: ${sprint.committedPoints}`);
    console.log(
        `Remaining capacity: ${
            sprint.capacityPoints - sprint.committedPoints
        }`
    );
}

// ---------------------------------------------------------------------------
// 14. KANBAN FLOW
// ---------------------------------------------------------------------------

function demonstrateKanban() {
    printSection("11. Kanban-Style Flow");

    const items = [
        { id: "K1", name: "API authentication", state: "In Progress" },
        { id: "K2", name: "Database indexing", state: "Review" },
        { id: "K3", name: "Dashboard tests", state: "Done" },
        { id: "K4", name: "Deployment documentation", state: "To Do" }
    ];

    const counts = new Map();

    items.forEach(item => {
        console.log(`${item.id}: ${item.name} -> ${item.state}`);
        counts.set(item.state, (counts.get(item.state) || 0) + 1);
    });

    console.log("Flow counts:");

    for (const [state, count] of counts.entries()) {
        console.log(`${state}: ${count}`);
    }
}

// ---------------------------------------------------------------------------
// 15. PROJECT PERFORMANCE
// ---------------------------------------------------------------------------

class PerformanceSnapshot {
    constructor(plannedValue, earnedValue, actualCost) {
        this.plannedValue = plannedValue;
        this.earnedValue = earnedValue;
        this.actualCost = actualCost;
    }

    get scheduleVariance() {
        return this.earnedValue - this.plannedValue;
    }

    get costVariance() {
        return this.earnedValue - this.actualCost;
    }

    get schedulePerformanceIndex() {
        return this.plannedValue === 0
            ? 0
            : this.earnedValue / this.plannedValue;
    }

    get costPerformanceIndex() {
        return this.actualCost === 0
            ? 0
            : this.earnedValue / this.actualCost;
    }
}

function demonstratePerformance() {
    printSection("12. Performance Measurement");

    const snapshot = new PerformanceSnapshot(
        50000,
        45000,
        52000
    );

    console.log(`Schedule variance: $${snapshot.scheduleVariance}`);
    console.log(`Cost variance: $${snapshot.costVariance}`);
    console.log(`SPI: ${snapshot.schedulePerformanceIndex.toFixed(3)}`);
    console.log(`CPI: ${snapshot.costPerformanceIndex.toFixed(3)}`);
}

// ---------------------------------------------------------------------------
// 16. PRIORITIZATION
// ---------------------------------------------------------------------------

function calculatePriorityScore(item) {
    const denominator = Math.max(item.effort, 1);

    return (
        item.businessValue +
        item.urgency +
        item.riskReduction
    ) / denominator;
}

function demonstratePrioritization() {
    printSection("13. Prioritization");

    const backlog = [
        {
            id: "B1",
            name: "Secure authentication",
            businessValue: 10,
            urgency: 10,
            effort: 5,
            riskReduction: 10
        },
        {
            id: "B2",
            name: "Dashboard filters",
            businessValue: 7,
            urgency: 5,
            effort: 4,
            riskReduction: 2
        },
        {
            id: "B3",
            name: "CSV export",
            businessValue: 6,
            urgency: 6,
            effort: 2,
            riskReduction: 1
        },
        {
            id: "B4",
            name: "Custom themes",
            businessValue: 3,
            urgency: 2,
            effort: 5,
            riskReduction: 0
        }
    ];

    const ranked = [...backlog].sort(
        (a, b) =>
            calculatePriorityScore(b) -
            calculatePriorityScore(a)
    );

    ranked.forEach(item => {
        console.log(
            `${item.id}: ${item.name} -> ` +
            `${calculatePriorityScore(item).toFixed(2)}`
        );
    });
}

// ---------------------------------------------------------------------------
// 17. RESOURCE CAPACITY
// ---------------------------------------------------------------------------

function demonstrateResourceCapacity() {
    printSection("14. Resource Capacity");

    const resources = [
        { name: "Asha", role: "Backend", capacity: 40, assigned: 34 },
        { name: "Ravi", role: "Frontend", capacity: 40, assigned: 38 },
        { name: "Mina", role: "QA", capacity: 40, assigned: 30 },
        { name: "Dev", role: "Security", capacity: 32, assigned: 36 }
    ];

    resources.forEach(resource => {
        const utilization =
            (resource.assigned / resource.capacity) * 100;

        const status =
            resource.assigned > resource.capacity
                ? "OVER CAPACITY"
                : "Within capacity";

        console.log(
            `${resource.name}: ${resource.role}, ` +
            `${utilization.toFixed(1)}%, ${status}`
        );
    });
}

// ---------------------------------------------------------------------------
// 18. TRACEABILITY
// ---------------------------------------------------------------------------

function demonstrateTraceability() {
    printSection("15. Requirements Traceability");

    const records = [
        {
            requirement: "REQ-001",
            tasks: ["T4", "T6", "T7"],
            tests: ["TEST-101", "TEST-102"],
            status: "Accepted"
        },
        {
            requirement: "REQ-002",
            tasks: ["T3", "T4", "T5", "T6"],
            tests: ["TEST-201", "TEST-202"],
            status: "In Review"
        }
    ];

    records.forEach(record => {
        console.log(
            `${record.requirement}: ` +
            `tasks=${record.tasks.join(", ")}; ` +
            `tests=${record.tests.join(", ")}; ` +
            `status=${record.status}`
        );
    });
}

// ---------------------------------------------------------------------------
// 19. QUALITY GATES
// ---------------------------------------------------------------------------

function demonstrateQualityGates() {
    printSection("16. Quality Gates");

    const gates = [
        {
            name: "Functional testing",
            required: true,
            passed: true
        },
        {
            name: "Security review",
            required: true,
            passed: true
        },
        {
            name: "Operational documentation",
            required: true,
            passed: false
        }
    ];

    gates.forEach(gate => {
        console.log(
            `${gate.name}: ${gate.passed ? "PASS" : "FAIL"}`
        );
    });

    const canRelease = gates.every(
        gate => !gate.required || gate.passed
    );

    console.log(`Release status: ${canRelease ? "ALLOWED" : "BLOCKED"}`);
}

// ---------------------------------------------------------------------------
// 20. ASYNCHRONOUS PROJECT OPERATIONS
// ---------------------------------------------------------------------------

function simulateExternalCheck(name, delayMs, result) {
    return new Promise(resolve => {
        setTimeout(() => {
            resolve({
                name,
                result
            });
        }, delayMs);
    });
}

async function demonstrateAsyncPlanningChecks() {
    printSection("17. Asynchronous Planning Checks");

    // JavaScript promises model operations such as API calls, validation
    // services, CI checks, or remote project systems.
    const checks = await Promise.all([
        simulateExternalCheck("Requirements validation", 20, "PASS"),
        simulateExternalCheck("Security gate", 30, "PASS"),
        simulateExternalCheck("Deployment readiness", 10, "PASS")
    ]);

    checks.forEach(check => {
        console.log(`${check.name}: ${check.result}`);
    });
}

// ---------------------------------------------------------------------------
// 21. SCENARIO ANALYSIS
// ---------------------------------------------------------------------------

function createAcceleratedPlan(tasks) {
    const accelerated = new Map();

    for (const [id, task] of tasks.entries()) {
        accelerated.set(
            id,
            new Task(
                task.id,
                task.name,
                Math.max(1, Math.round(task.durationDays * 0.8)),
                task.cost * 1.2,
                [...task.dependencies],
                task.resource
            )
        );
    }

    return accelerated;
}

function demonstrateScenarioAnalysis(tasks) {
    printSection("18. Schedule and Cost Scenario Analysis");

    const baseline = criticalPathAnalysis(tasks);
    const acceleratedTasks = createAcceleratedPlan(tasks);
    const accelerated = criticalPathAnalysis(acceleratedTasks);

    const baselineCost = calculateTotalCost(tasks);
    const acceleratedCost = calculateTotalCost(acceleratedTasks);

    console.log(`Baseline duration: ${baseline.duration} days`);
    console.log(`Accelerated duration: ${accelerated.duration} days`);
    console.log(`Baseline cost: $${baselineCost.toLocaleString()}`);
    console.log(
        `Accelerated cost: $${acceleratedCost.toLocaleString()}`
    );

    console.log(
        "Acceleration may reduce duration while increasing cost."
    );
}

// ---------------------------------------------------------------------------
// 22. PROJECT HEALTH
// ---------------------------------------------------------------------------

function calculateProjectHealth({
    scheduleIndex,
    costIndex,
    openHighRisks,
    unresolvedCriticalIssues,
    requirementCompletion
}) {
    return {
        schedule:
            scheduleIndex < 0.9
                ? "Attention"
                : scheduleIndex < 1
                    ? "Monitor"
                    : "On plan or ahead",

        cost:
            costIndex < 0.9
                ? "Attention"
                : costIndex < 1
                    ? "Monitor"
                    : "Within plan",

        risk:
            openHighRisks >= 3
                ? "Attention"
                : openHighRisks > 0
                    ? "Monitor"
                    : "Controlled",

        criticalIssues:
            unresolvedCriticalIssues > 0
                ? "Attention"
                : "Controlled",

        requirements:
            requirementCompletion < 0.7
                ? "Attention"
                : requirementCompletion < 0.9
                    ? "Monitor"
                    : "Strong"
    };
}

function demonstrateProjectHealth() {
    printSection("19. Project Health");

    const health = calculateProjectHealth({
        scheduleIndex: 0.94,
        costIndex: 0.97,
        openHighRisks: 2,
        unresolvedCriticalIssues: 0,
        requirementCompletion: 0.82
    });

    Object.entries(health).forEach(([category, status]) => {
        console.log(`${category}: ${status}`);
    });
}

// ---------------------------------------------------------------------------
// 23. EDGE CASES
// ---------------------------------------------------------------------------

function demonstrateEdgeCases() {
    printSection("20. Edge Cases");

    try {
        threePointEstimate(10, 5, 20);
    } catch (error) {
        console.log(`Invalid estimate rejected: ${error.message}`);
    }

    const cyclicTasks = new Map([
        ["A", new Task("A", "A", 2, 100, ["B"])],
        ["B", new Task("B", "B", 2, 100, ["A"])]
    ]);

    try {
        validateTasks(cyclicTasks);
        topologicalSort(cyclicTasks);
    } catch (error) {
        console.log(`Circular dependency rejected: ${error.message}`);
    }

    try {
        addWorkingDays(
            new Date("2026-10-05T00:00:00Z"),
            -1
        );
    } catch (error) {
        console.log(`Negative duration rejected: ${error.message}`);
    }
}

// ---------------------------------------------------------------------------
// 24. TESTS
// ---------------------------------------------------------------------------

function runTests() {
    printSection("21. Automated Tests");

    const tasks = buildTasks();

    validateTasks(tasks);

    const order = topologicalSort(tasks);

    if (order.indexOf("T1") >= order.indexOf("T2")) {
        throw new Error("T1 must precede T2.");
    }

    if (order.indexOf("T2") >= order.indexOf("T4")) {
        throw new Error("T2 must precede T4.");
    }

    const analysis = criticalPathAnalysis(tasks);

    for (const entry of analysis.entries.values()) {
        if (entry.earliestStart > entry.earliestFinish) {
            throw new Error("Invalid earliest schedule.");
        }
    }

    const performance = new PerformanceSnapshot(100, 80, 90);

    if (performance.scheduleVariance !== -20) {
        throw new Error("Schedule variance calculation failed.");
    }

    if (performance.costVariance !== -10) {
        throw new Error("Cost variance calculation failed.");
    }

    console.log("All JavaScript tests passed.");
}

// ---------------------------------------------------------------------------
// 25. MAIN
// ---------------------------------------------------------------------------

async function main() {
    printSection("PROJECT PLANNING: JAVASCRIPT STUDY PROGRAM");

    demonstrateFundamentals();

    const charter = new ProjectCharter({
        name: "Portfolio Analytics Platform",
        purpose: "Provide secure portfolio analysis and reporting.",
        sponsor: "Chief Product Officer",
        projectManager: "Project Manager",
        startDate: new Date("2026-10-05T00:00:00Z"),
        targetDate: new Date("2026-11-30T00:00:00Z"),
        budget: 65000,
        inScope: [
            "Authentication",
            "Dashboard",
            "Reporting",
            "Security testing",
            "Production deployment"
        ],
        outOfScope: [
            "Native mobile application",
            "International tax calculations"
        ]
    });

    const charterErrors = charter.validate();

    if (charterErrors.length > 0) {
        throw new Error(charterErrors.join("; "));
    }

    charter.display();

    demonstrateRequirements();
    demonstrateStakeholders();

    const tasks = buildTasks();
    validateTasks(tasks);

    const analysis = demonstrateCriticalPath(tasks);

    demonstrateCalendar(tasks, analysis);
    demonstrateEstimation();
    demonstrateCostPlanning(tasks);
    demonstrateRiskManagement();
    demonstrateChangeControl();
    demonstrateSprintPlanning();
    demonstrateKanban();
    demonstratePerformance();
    demonstratePrioritization();
    demonstrateResourceCapacity();
    demonstrateTraceability();
    demonstrateQualityGates();
    await demonstrateAsyncPlanningChecks();
    demonstrateScenarioAnalysis(tasks);
    demonstrateProjectHealth();
    demonstrateEdgeCases();
    runTests();

    printSection("END OF JAVASCRIPT PROJECT PLANNING PROGRAM");
}

main().catch(error => {
    console.error(`Program failed: ${error.message}`);
    process.exitCode = 1;
});
