/*
 * Project Management Study Program
 * Topic: Responsibilities of a Project Manager
 *
 * This self-contained JavaScript file demonstrates project management
 * responsibilities through executable examples involving:
 * - project initiation
 * - scope
 * - WBS
 * - RACI
 * - scheduling
 * - dependency management
 * - critical path
 * - budgets
 * - earned value
 * - stakeholders
 * - risk
 * - issues
 * - quality
 * - resources
 * - change control
 * - communication
 * - Agile delivery
 * - governance
 * - closure
 *
 * It uses only standard JavaScript and can run in Node.js or a modern browser.
 */

"use strict";

// -----------------------------------------------------------------------------
// 1. BASIC PROJECT REPRESENTATION
// -----------------------------------------------------------------------------

class Project {
    constructor({
        name,
        objective,
        sponsor,
        manager,
        budget,
        startDate,
        targetEndDate
    }) {
        if (!name || !objective || !manager) {
            throw new Error("Project name, objective and manager are required.");
        }

        if (budget <= 0) {
            throw new Error("Project budget must be positive.");
        }

        this.name = name;
        this.objective = objective;
        this.sponsor = sponsor;
        this.manager = manager;
        this.budget = budget;
        this.startDate = new Date(startDate);
        this.targetEndDate = new Date(targetEndDate);
        this.status = "Planned";
    }

    activate() {
        if (this.status !== "Planned") {
            throw new Error("Only planned projects can be activated.");
        }

        this.status = "Active";
    }

    complete() {
        if (this.status !== "Active") {
            throw new Error("Only active projects can be completed.");
        }

        this.status = "Completed";
    }

    get plannedDurationDays() {
        const millisecondsPerDay = 24 * 60 * 60 * 1000;
        return (
            Math.ceil(
                (this.targetEndDate - this.startDate) / millisecondsPerDay
            ) + 1
        );
    }
}

// -----------------------------------------------------------------------------
// 2. TASKS AND PROGRESS
// -----------------------------------------------------------------------------

class Task {
    constructor({
        id,
        name,
        owner,
        duration,
        cost,
        dependencies = []
    }) {
        if (duration <= 0) {
            throw new Error("Task duration must be positive.");
        }

        if (cost < 0) {
            throw new Error("Task cost cannot be negative.");
        }

        this.id = id;
        this.name = name;
        this.owner = owner;
        this.duration = duration;
        this.cost = cost;
        this.dependencies = dependencies;
        this.progress = 0;
        this.status = "Planned";
    }

    updateProgress(progress) {
        if (progress < 0 || progress > 100) {
            throw new Error("Progress must be between 0 and 100.");
        }

        this.progress = progress;

        if (progress === 100) {
            this.status = "Completed";
        } else if (progress > 0) {
            this.status = "Active";
        }
    }
}

// -----------------------------------------------------------------------------
// 3. PROJECT SCOPE
// -----------------------------------------------------------------------------

function classifyScope(scopeItems) {
    return {
        included: scopeItems
            .filter(item => item.included)
            .map(item => item.name),

        excluded: scopeItems
            .filter(item => !item.included)
            .map(item => item.name)
    };
}

// -----------------------------------------------------------------------------
// 4. DEPENDENCY GRAPH AND TOPOLOGICAL ORDER
// -----------------------------------------------------------------------------

function topologicalSort(tasks) {
    const indegree = new Map();
    const graph = new Map();

    for (const task of tasks.values()) {
        indegree.set(task.id, 0);
        graph.set(task.id, []);
    }

    for (const task of tasks.values()) {
        for (const dependency of task.dependencies) {
            if (!tasks.has(dependency)) {
                throw new Error(
                    `Task ${task.id} depends on unknown task ${dependency}.`
                );
            }

            graph.get(dependency).push(task.id);
            indegree.set(task.id, indegree.get(task.id) + 1);
        }
    }

    const queue = [];

    for (const [taskId, degree] of indegree.entries()) {
        if (degree === 0) {
            queue.push(taskId);
        }
    }

    const result = [];

    while (queue.length > 0) {
        const current = queue.shift();
        result.push(current);

        for (const successor of graph.get(current)) {
            const newDegree = indegree.get(successor) - 1;
            indegree.set(successor, newDegree);

            if (newDegree === 0) {
                queue.push(successor);
            }
        }
    }

    if (result.length !== tasks.size) {
        throw new Error("Circular dependency detected.");
    }

    return result;
}

// -----------------------------------------------------------------------------
// 5. CRITICAL PATH CALCULATION
// -----------------------------------------------------------------------------

function criticalPath(tasks) {
    const order = topologicalSort(tasks);

    const earliestStart = new Map();
    const earliestFinish = new Map();
    const predecessor = new Map();

    for (const taskId of order) {
        const task = tasks.get(taskId);

        if (task.dependencies.length === 0) {
            earliestStart.set(taskId, 0);
            predecessor.set(taskId, null);
        } else {
            let selectedDependency = task.dependencies[0];

            for (const dependency of task.dependencies) {
                if (
                    earliestFinish.get(dependency) >
                    earliestFinish.get(selectedDependency)
                ) {
                    selectedDependency = dependency;
                }
            }

            earliestStart.set(
                taskId,
                earliestFinish.get(selectedDependency)
            );

            predecessor.set(taskId, selectedDependency);
        }

        earliestFinish.set(
            taskId,
            earliestStart.get(taskId) + task.duration
        );
    }

    let finalTask = order[0];

    for (const taskId of order) {
        if (earliestFinish.get(taskId) > earliestFinish.get(finalTask)) {
            finalTask = taskId;
        }
    }

    const path = [];
    let current = finalTask;

    while (current !== null) {
        path.push(current);
        current = predecessor.get(current);
    }

    path.reverse();

    return {
        duration: earliestFinish.get(finalTask),
        path
    };
}

// -----------------------------------------------------------------------------
// 6. COST MANAGEMENT
// -----------------------------------------------------------------------------

function plannedCost(tasks) {
    let total = 0;

    for (const task of tasks.values()) {
        total += task.cost;
    }

    return total;
}

function budgetVariance(approvedBudget, actualCost) {
    if (approvedBudget < 0 || actualCost < 0) {
        throw new Error("Budget values cannot be negative.");
    }

    return approvedBudget - actualCost;
}

// -----------------------------------------------------------------------------
// 7. EARNED VALUE MANAGEMENT
// -----------------------------------------------------------------------------

function earnedValueMetrics(plannedValue, earnedValue, actualCost) {
    if (plannedValue <= 0) {
        throw new Error("Planned value must be positive.");
    }

    if (actualCost <= 0) {
        throw new Error("Actual cost must be positive.");
    }

    const CV = earnedValue - actualCost;
    const SV = earnedValue - plannedValue;
    const CPI = earnedValue / actualCost;
    const SPI = earnedValue / plannedValue;

    return { CV, SV, CPI, SPI };
}

// -----------------------------------------------------------------------------
// 8. STAKEHOLDER ANALYSIS
// -----------------------------------------------------------------------------

class Stakeholder {
    constructor(name, role, influence, interest) {
        if (
            influence < 1 ||
            influence > 5 ||
            interest < 1 ||
            interest > 5
        ) {
            throw new Error("Influence and interest must be 1 through 5.");
        }

        this.name = name;
        this.role = role;
        this.influence = influence;
        this.interest = interest;
    }

    strategy() {
        if (this.influence >= 4 && this.interest >= 4) {
            return "Manage closely";
        }

        if (this.influence >= 4 && this.interest < 4) {
            return "Keep satisfied";
        }

        if (this.influence < 4 && this.interest >= 4) {
            return "Keep informed";
        }

        return "Monitor";
    }
}

// -----------------------------------------------------------------------------
// 9. RACI VALIDATION
// -----------------------------------------------------------------------------

function validateRaci(matrix) {
    const warnings = [];

    for (const [workItem, assignments] of Object.entries(matrix)) {
        const accountable = Object.entries(assignments)
            .filter(([, role]) => role === "A")
            .map(([person]) => person);

        if (accountable.length === 0) {
            warnings.push(`${workItem}: no accountable person.`);
        }

        if (accountable.length > 1) {
            warnings.push(`${workItem}: multiple accountable people.`);
        }
    }

    return warnings;
}

// -----------------------------------------------------------------------------
// 10. RISK MANAGEMENT
// -----------------------------------------------------------------------------

class Risk {
    constructor({
        id,
        description,
        probability,
        impact,
        owner,
        response,
        contingency
    }) {
        this.id = id;
        this.description = description;
        this.probability = probability;
        this.impact = impact;
        this.owner = owner;
        this.response = response;
        this.contingency = contingency;
        this.status = "Open";
    }

    get score() {
        return this.probability * this.impact;
    }

    get severity() {
        if (this.score >= 6) return "High";
        if (this.score >= 3) return "Medium";
        return "Low";
    }
}

function prioritizeRisks(risks) {
    return [...risks].sort((a, b) => b.score - a.score);
}

// -----------------------------------------------------------------------------
// 11. ISSUE MANAGEMENT
// -----------------------------------------------------------------------------

class Issue {
    constructor({
        id,
        description,
        owner,
        severity,
        dueDate
    }) {
        this.id = id;
        this.description = description;
        this.owner = owner;
        this.severity = severity;
        this.dueDate = new Date(dueDate);
        this.status = "Open";
    }

    isOverdue(today = new Date()) {
        return (
            this.status !== "Closed" &&
            today.getTime() > this.dueDate.getTime()
        );
    }
}

// -----------------------------------------------------------------------------
// 12. RESOURCE MANAGEMENT
// -----------------------------------------------------------------------------

class Resource {
    constructor(name, role, availableHours) {
        if (availableHours < 0) {
            throw new Error("Available hours cannot be negative.");
        }

        this.name = name;
        this.role = role;
        this.availableHours = availableHours;
        this.allocatedHours = 0;
    }

    allocate(hours) {
        if (hours < 0) {
            throw new Error("Allocated hours cannot be negative.");
        }

        this.allocatedHours += hours;
    }

    get utilization() {
        if (this.availableHours === 0) {
            return Infinity;
        }

        return this.allocatedHours / this.availableHours * 100;
    }
}

// -----------------------------------------------------------------------------
// 13. CHANGE CONTROL
// -----------------------------------------------------------------------------

class ChangeRequest {
    constructor({
        id,
        description,
        reason,
        requestedBy,
        estimatedCost,
        estimatedDelayDays,
        businessValue
    }) {
        this.id = id;
        this.description = description;
        this.reason = reason;
        this.requestedBy = requestedBy;
        this.estimatedCost = estimatedCost;
        this.estimatedDelayDays = estimatedDelayDays;
        this.businessValue = businessValue;
        this.status = "Proposed";
    }
}

class ChangeControlBoard {
    constructor(budget) {
        this.remainingBudget = budget;
        this.requests = [];
    }

    submit(request) {
        request.status = "Under Review";
        this.requests.push(request);
    }

    review(request) {
        if (request.estimatedCost > this.remainingBudget) {
            request.status = "Rejected";
            return "Insufficient remaining budget.";
        }

        if (
            request.businessValue >= 8 &&
            request.estimatedDelayDays <= 5
        ) {
            request.status = "Approved";
            this.remainingBudget -= request.estimatedCost;
            return "Approved after impact review.";
        }

        request.status = "Under Review";
        return "Requires deeper impact assessment.";
    }
}

// -----------------------------------------------------------------------------
// 14. QUALITY MANAGEMENT
// -----------------------------------------------------------------------------

function qualityReport(checks) {
    const passed = checks.filter(check => check.actual === check.expected).length;

    return {
        total: checks.length,
        passed,
        failed: checks.length - passed
    };
}

// -----------------------------------------------------------------------------
// 15. STATUS REPORTING
// -----------------------------------------------------------------------------

function createStatusReport({
    reportingDate,
    accomplishments,
    nextPeriod,
    risks,
    issues,
    decisions,
    budgetVarianceValue,
    scheduleVarianceDays
}) {
    return {
        reportingDate,
        accomplishments,
        nextPeriod,
        risks,
        issues,
        decisions,
        budgetVariance: budgetVarianceValue,
        scheduleVarianceDays
    };
}

// -----------------------------------------------------------------------------
// 16. DECISION LOG
// -----------------------------------------------------------------------------

class DecisionLog {
    constructor() {
        this.decisions = [];
    }

    add(decision) {
        if (!decision.id || !decision.decision) {
            throw new Error("Decision ID and decision text are required.");
        }

        this.decisions.push(decision);
    }

    search(keyword) {
        const normalized = keyword.toLowerCase();

        return this.decisions.filter(decision =>
            JSON.stringify(decision)
                .toLowerCase()
                .includes(normalized)
        );
    }
}

// -----------------------------------------------------------------------------
// 17. AGILE BACKLOG AND SPRINT CAPACITY
// -----------------------------------------------------------------------------

class BacklogItem {
    constructor(id, title, priority, storyPoints) {
        if (storyPoints <= 0) {
            throw new Error("Story points must be positive.");
        }

        this.id = id;
        this.title = title;
        this.priority = priority;
        this.storyPoints = storyPoints;
        this.status = "To Do";
    }
}

function selectSprintItems(items, capacity) {
    const sorted = [...items].sort(
        (a, b) => a.priority - b.priority
    );

    const selected = [];
    let usedCapacity = 0;

    for (const item of sorted) {
        if (usedCapacity + item.storyPoints <= capacity) {
            selected.push(item);
            usedCapacity += item.storyPoints;
        }
    }

    return {
        selected,
        usedCapacity,
        remainingCapacity: capacity - usedCapacity
    };
}

// -----------------------------------------------------------------------------
// 18. COMMUNICATION MANAGEMENT
// -----------------------------------------------------------------------------

class CommunicationPlan {
    constructor() {
        this.entries = [];
    }

    add({
        audience,
        purpose,
        frequency,
        channel,
        owner
    }) {
        this.entries.push({
            audience,
            purpose,
            frequency,
            channel,
            owner
        });
    }
}

// -----------------------------------------------------------------------------
// 19. PROJECT CLOSURE
// -----------------------------------------------------------------------------

function closureChecklist() {
    return [
        "Deliverables accepted",
        "Acceptance criteria verified",
        "Open defects transferred",
        "Contracts closed",
        "Financial reconciliation completed",
        "Documentation archived",
        "Lessons learned recorded",
        "Operational ownership transferred",
        "Resources released",
        "Final communication completed"
    ];
}

// -----------------------------------------------------------------------------
// 20. SECURITY CONTROLS
// -----------------------------------------------------------------------------

function securityChecklist() {
    return [
        "Use least-privilege access.",
        "Protect credentials and secrets.",
        "Restrict sensitive project information.",
        "Use approved storage and communication systems.",
        "Track security risks and incidents.",
        "Do not place credentials in source code or reports.",
        "Follow retention and disposal requirements.",
        "Escalate suspected security incidents through approved channels."
    ];
}

// -----------------------------------------------------------------------------
// 21. COMPLETE CASE STUDY
// -----------------------------------------------------------------------------

function runCaseStudy() {
    console.log("=".repeat(78));
    console.log("PROJECT MANAGER RESPONSIBILITIES: JAVASCRIPT CASE STUDY");
    console.log("=".repeat(78));

    const project = new Project({
        name: "Enterprise Service Management Platform",
        objective:
            "Centralize service requests, workflow automation and reporting.",
        sponsor: "Chief Operating Officer",
        manager: "Project Manager",
        budget: 250000,
        startDate: "2026-10-01",
        targetEndDate: "2027-02-28"
    });

    project.activate();

    console.log("\nProject:");
    console.log(project);

    console.log(
        `Planned duration: ${project.plannedDurationDays} days`
    );

    const scope = classifyScope([
        { name: "Request management", included: true },
        { name: "Approval workflows", included: true },
        { name: "Management dashboard", included: true },
        { name: "Native mobile application", included: false },
        { name: "External marketplace", included: false }
    ]);

    console.log("\nIncluded scope:", scope.included);
    console.log("Excluded scope:", scope.excluded);

    const tasks = new Map([
        [
            "T1",
            new Task({
                id: "T1",
                name: "Requirements analysis",
                owner: "Business Analyst",
                duration: 10,
                cost: 18000
            })
        ],
        [
            "T2",
            new Task({
                id: "T2",
                name: "Solution architecture",
                owner: "Solution Architect",
                duration: 8,
                cost: 22000,
                dependencies: ["T1"]
            })
        ],
        [
            "T3",
            new Task({
                id: "T3",
                name: "UX design",
                owner: "UX Designer",
                duration: 7,
                cost: 12000,
                dependencies: ["T1"]
            })
        ],
        [
            "T4",
            new Task({
                id: "T4",
                name: "Backend development",
                owner: "Backend Lead",
                duration: 25,
                cost: 58000,
                dependencies: ["T2"]
            })
        ],
        [
            "T5",
            new Task({
                id: "T5",
                name: "Frontend development",
                owner: "Frontend Lead",
                duration: 20,
                cost: 42000,
                dependencies: ["T2", "T3"]
            })
        ],
        [
            "T6",
            new Task({
                id: "T6",
                name: "Integration testing",
                owner: "QA Lead",
                duration: 12,
                cost: 24000,
                dependencies: ["T4", "T5"]
            })
        ],
        [
            "T7",
            new Task({
                id: "T7",
                name: "User acceptance testing",
                owner: "Business Owner",
                duration: 8,
                cost: 14000,
                dependencies: ["T6"]
            })
        ],
        [
            "T8",
            new Task({
                id: "T8",
                name: "Production deployment",
                owner: "DevOps Lead",
                duration: 4,
                cost: 9000,
                dependencies: ["T7"]
            })
        ],
        [
            "T9",
            new Task({
                id: "T9",
                name: "Training and handover",
                owner: "Change Lead",
                duration: 6,
                cost: 11000,
                dependencies: ["T7"]
            })
        ]
    ]);

    console.log("\nDependency order:");
    console.log(topologicalSort(tasks).join(" -> "));

    const path = criticalPath(tasks);

    console.log(`\nCritical-path duration: ${path.duration} days`);
    console.log(`Critical path: ${path.path.join(" -> ")}`);

    const totalCost = plannedCost(tasks);
    console.log(`Planned task cost: ${totalCost.toLocaleString()}`);

    // RACI demonstrates accountability clarity.
    const raci = {
        Requirements: {
            "Project Manager": "A",
            "Business Analyst": "R",
            Operations: "C",
            Sponsor: "I"
        },
        Architecture: {
            "Project Manager": "A",
            "Solution Architect": "R",
            Security: "C",
            Sponsor: "I"
        },
        Deployment: {
            "Project Manager": "A",
            DevOps: "R",
            Security: "C",
            Operations: "I"
        }
    };

    console.log("\nRACI warnings:");
    console.log(validateRaci(raci));

    // Stakeholders.
    const stakeholders = [
        new Stakeholder(
            "Chief Operating Officer",
            "Executive Sponsor",
            5,
            5
        ),
        new Stakeholder(
            "Finance Director",
            "Budget Owner",
            5,
            3
        ),
        new Stakeholder(
            "Operations Team",
            "Primary Users",
            3,
            5
        ),
        new Stakeholder(
            "Security Team",
            "Control Function",
            4,
            4
        )
    ];

    console.log("\nStakeholder strategies:");

    for (const stakeholder of stakeholders) {
        console.log(
            `${stakeholder.name}: ${stakeholder.strategy()}`
        );
    }

    // Risks.
    const risks = [
        new Risk({
            id: "R1",
            description: "Integration interface changes",
            probability: 3,
            impact: 3,
            owner: "Solution Architect",
            response: "Reduce",
            contingency: "Maintain fallback adapter."
        }),
        new Risk({
            id: "R2",
            description: "Key specialist unavailable",
            probability: 2,
            impact: 3,
            owner: "Project Manager",
            response: "Mitigate",
            contingency: "Cross-train another engineer."
        }),
        new Risk({
            id: "R3",
            description: "Low training attendance",
            probability: 2,
            impact: 2,
            owner: "Change Lead",
            response: "Mitigate",
            contingency: "Provide recorded sessions."
        })
    ];

    console.log("\nPrioritized risks:");

    for (const risk of prioritizeRisks(risks)) {
        console.log(
            `${risk.id}: ${risk.description} | ` +
            `score=${risk.score} | severity=${risk.severity}`
        );
    }

    // Issues.
    const issue = new Issue({
        id: "I1",
        description: "Test environment provisioning delayed",
        owner: "DevOps Lead",
        severity: "High",
        dueDate: "2026-11-15"
    });

    console.log(
        "\nIssue overdue:",
        issue.isOverdue(new Date("2026-11-18"))
    );

    // Resource utilization.
    const backend = new Resource(
        "Backend Lead",
        "Engineering",
        320
    );

    backend.allocate(300);

    console.log(
        `\nBackend utilization: ${backend.utilization.toFixed(1)}%`
    );

    // Quality.
    const quality = qualityReport([
        { expected: "Pass", actual: "Pass" },
        { expected: "Pass", actual: "Pass" },
        { expected: "Pass", actual: "Fail" },
        { expected: "Pass", actual: "Pass" }
    ]);

    console.log("\nQuality:", quality);

    // EVM.
    const evm = earnedValueMetrics(
        100000,
        92000,
        98000
    );

    console.log("\nEarned Value Metrics:", evm);

    const forecastAtCompletion =
        project.budget / evm.CPI;

    console.log(
        "Forecast at completion:",
        forecastAtCompletion.toFixed(2)
    );

    // Change control.
    const changeBoard = new ChangeControlBoard(project.budget);

    const change = new ChangeRequest({
        id: "CR-001",
        description: "Automated executive alerting",
        reason: "Earlier visibility of critical exceptions",
        requestedBy: "Chief Operating Officer",
        estimatedCost: 12000,
        estimatedDelayDays: 4,
        businessValue: 9
    });

    changeBoard.submit(change);

    console.log(
        "\nChange decision:",
        changeBoard.review(change)
    );

    console.log("Change status:", change.status);
    console.log(
        "Remaining budget:",
        changeBoard.remainingBudget
    );

    // Communication plan.
    const communicationPlan = new CommunicationPlan();

    communicationPlan.add({
        audience: "Executive sponsor",
        purpose: "Decision and status visibility",
        frequency: "Weekly",
        channel: "Executive review",
        owner: "Project Manager"
    });

    communicationPlan.add({
        audience: "Delivery team",
        purpose: "Coordination and blockers",
        frequency: "Daily",
        channel: "Team meeting",
        owner: "Project Manager"
    });

    console.log("\nCommunication plan:");
    console.table(communicationPlan.entries);

    // Agile planning.
    const backlog = [
        new BacklogItem("P1", "Authentication", 1, 5),
        new BacklogItem("P2", "Dashboard", 2, 8),
        new BacklogItem("P3", "Audit logging", 3, 3),
        new BacklogItem("P4", "Report export", 4, 5)
    ];

    const sprint = selectSprintItems(backlog, 13);

    console.log("\nSprint planning:");
    console.log(sprint);

    // Decision log.
    const decisions = new DecisionLog();

    decisions.add({
        id: "D-001",
        subject: "Data retention",
        decision: "Retain operational audit data according to policy",
        owner: "Security",
        rationale: "Compliance and operational traceability"
    });

    console.log(
        "\nDecision search:",
        decisions.search("retention")
    );

    // Closure.
    console.log("\nClosure checklist:");

    for (const item of closureChecklist()) {
        console.log(`- ${item}`);
    }

    // Security.
    console.log("\nSecurity checklist:");

    for (const item of securityChecklist()) {
        console.log(`- ${item}`);
    }
}

// -----------------------------------------------------------------------------
// 22. EDGE CASE TESTS
// -----------------------------------------------------------------------------

function runTests() {
    console.log("\n" + "=".repeat(78));
    console.log("SELF-TESTS");
    console.log("=".repeat(78));

    const task = new Task({
        id: "TEST",
        name: "Validation",
        owner: "Developer",
        duration: 2,
        cost: 100
    });

    let validationCaught = false;

    try {
        task.updateProgress(101);
    } catch (error) {
        validationCaught = true;
    }

    console.assert(
        validationCaught,
        "Invalid progress should throw."
    );

    const circular = new Map([
        [
            "A",
            new Task({
                id: "A",
                name: "A",
                owner: "X",
                duration: 1,
                cost: 10,
                dependencies: ["B"]
            })
        ],
        [
            "B",
            new Task({
                id: "B",
                name: "B",
                owner: "Y",
                duration: 1,
                cost: 10,
                dependencies: ["A"]
            })
        ]
    ]);

    let cycleCaught = false;

    try {
        topologicalSort(circular);
    } catch (error) {
        cycleCaught = true;
    }

    console.assert(
        cycleCaught,
        "Circular dependencies should throw."
    );

    const evm = earnedValueMetrics(100, 120, 100);

    console.assert(evm.CPI === 1.2);
    console.assert(evm.SPI === 1.2);

    console.log("All tests passed.");
}

// -----------------------------------------------------------------------------
// 23. PROGRAM ENTRY POINT
// -----------------------------------------------------------------------------

function main() {
    runCaseStudy();
    runTests();

    console.log("\nProgram completed.");
}

main();
