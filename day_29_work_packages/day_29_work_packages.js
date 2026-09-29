/*
 * Work Packages: Understanding Manageable Units of Work
 *
 * This self-contained JavaScript program demonstrates work packages through
 * project decomposition, validation, dependencies, scheduling, estimation,
 * risk, capacity, progress tracking, change control, and performance metrics.
 *
 * Run with:
 *   node work_packages.js
 */

"use strict";

// ============================================================================
// 1. FUNDAMENTAL ENUMERATIONS
// ============================================================================

const WorkStatus = Object.freeze({
    NOT_STARTED: "Not Started",
    IN_PROGRESS: "In Progress",
    BLOCKED: "Blocked",
    COMPLETE: "Complete"
});

const Priority = Object.freeze({
    LOW: "Low",
    MEDIUM: "Medium",
    HIGH: "High",
    CRITICAL: "Critical"
});


// ============================================================================
// 2. BASIC DATA MODELS
// ============================================================================

class Deliverable {
    constructor(name, acceptanceCriteria = []) {
        this.name = name;
        this.acceptanceCriteria = [...acceptanceCriteria];
    }

    isWellDefined() {
        return (
            typeof this.name === "string" &&
            this.name.trim().length > 0 &&
            this.acceptanceCriteria.length > 0
        );
    }
}

class WorkPackage {
    constructor({
        id,
        name,
        description,
        owner,
        estimatedHours,
        priority = Priority.MEDIUM,
        dependencies = [],
        deliverables = [],
        risks = []
    }) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.owner = owner;
        this.estimatedHours = estimatedHours;
        this.priority = priority;
        this.status = WorkStatus.NOT_STARTED;
        this.dependencies = new Set(dependencies);
        this.deliverables = deliverables;
        this.risks = [...risks];
        this.actualHours = 0;
        this.progressPercent = 0;
    }

    validate() {
        const errors = [];

        if (!this.id?.trim()) {
            errors.push("Package ID is required.");
        }

        if (!this.name?.trim()) {
            errors.push("Package name is required.");
        }

        if (!this.owner?.trim()) {
            errors.push("An owner is required.");
        }

        if (!Number.isFinite(this.estimatedHours) || this.estimatedHours <= 0) {
            errors.push("Estimated hours must be greater than zero.");
        }

        if (this.progressPercent < 0 || this.progressPercent > 100) {
            errors.push("Progress must be between 0 and 100.");
        }

        for (const deliverable of this.deliverables) {
            if (!deliverable.isWellDefined()) {
                errors.push(`Deliverable "${deliverable.name}" is incomplete.`);
            }
        }

        return errors;
    }

    updateProgress(progressPercent, actualHours) {
        if (!Number.isFinite(progressPercent) ||
            progressPercent < 0 ||
            progressPercent > 100) {
            throw new Error("Progress must be between 0 and 100.");
        }

        if (!Number.isFinite(actualHours) || actualHours < 0) {
            throw new Error("Actual hours cannot be negative.");
        }

        this.progressPercent = progressPercent;
        this.actualHours = actualHours;

        if (progressPercent === 100) {
            this.status = WorkStatus.COMPLETE;
        } else if (progressPercent > 0) {
            this.status = WorkStatus.IN_PROGRESS;
        } else {
            this.status = WorkStatus.NOT_STARTED;
        }
    }

    scheduleDays(hoursPerDay = 8) {
        if (hoursPerDay <= 0) {
            throw new Error("Hours per day must be positive.");
        }

        return Math.max(1, Math.ceil(this.estimatedHours / hoursPerDay));
    }

    variance() {
        return this.actualHours - this.estimatedHours;
    }
}


// ============================================================================
// 3. BEGINNER EXAMPLE
// ============================================================================

function beginnerExample() {
    const packageItem = new WorkPackage({
        id: "WP-001",
        name: "Design Login Interface",
        description: "Create the approved authentication interface.",
        owner: "UI Designer",
        estimatedHours: 16,
        priority: Priority.HIGH,
        deliverables: [
            new Deliverable(
                "Approved login screen",
                [
                    "Responsive layout",
                    "Validation states documented",
                    "Product owner approval"
                ]
            )
        ]
    });

    console.log("\n=== BEGINNER EXAMPLE ===");
    console.log("Package:", packageItem.name);
    console.log("Owner:", packageItem.owner);
    console.log("Estimate:", packageItem.estimatedHours, "hours");
    console.log("Duration:", packageItem.scheduleDays(), "working days");
    console.log("Validation:", packageItem.validate());

    packageItem.updateProgress(50, 7);

    console.log("Status:", packageItem.status);
    console.log("Progress:", `${packageItem.progressPercent}%`);

    return packageItem;
}


// ============================================================================
// 4. WORK PACKAGE DECOMPOSITION
// ============================================================================

function createProjectPackages() {
    return [
        new WorkPackage({
            id: "WP-101",
            name: "Requirements Analysis",
            description: "Define functional and non-functional requirements.",
            owner: "Business Analyst",
            estimatedHours: 24,
            priority: Priority.CRITICAL,
            deliverables: [
                new Deliverable(
                    "Requirements baseline",
                    [
                        "Business approval exists",
                        "Requirements traceability exists"
                    ]
                )
            ]
        }),

        new WorkPackage({
            id: "WP-102",
            name: "UX Design",
            description: "Design user journeys and interface specifications.",
            owner: "UX Lead",
            estimatedHours: 32,
            priority: Priority.HIGH,
            dependencies: ["WP-101"],
            deliverables: [
                new Deliverable(
                    "UX specification",
                    [
                        "User journeys approved",
                        "Accessibility requirements documented"
                    ]
                )
            ]
        }),

        new WorkPackage({
            id: "WP-103",
            name: "Backend API",
            description: "Implement authentication and product APIs.",
            owner: "Backend Engineer",
            estimatedHours: 64,
            priority: Priority.CRITICAL,
            dependencies: ["WP-101"],
            deliverables: [
                new Deliverable(
                    "API service",
                    [
                        "Authentication works",
                        "API tests pass"
                    ]
                )
            ]
        }),

        new WorkPackage({
            id: "WP-104",
            name: "Frontend Implementation",
            description: "Implement the approved product interface.",
            owner: "Frontend Engineer",
            estimatedHours: 56,
            priority: Priority.HIGH,
            dependencies: ["WP-102", "WP-103"],
            deliverables: [
                new Deliverable(
                    "Web application",
                    [
                        "Core journeys work",
                        "Responsive layouts pass testing"
                    ]
                )
            ]
        }),

        new WorkPackage({
            id: "WP-105",
            name: "Integration Testing",
            description: "Validate integrated frontend and backend behavior.",
            owner: "QA Engineer",
            estimatedHours: 40,
            priority: Priority.HIGH,
            dependencies: ["WP-104"],
            deliverables: [
                new Deliverable(
                    "Integration test report",
                    [
                        "Critical scenarios pass",
                        "Defects are dispositioned"
                    ]
                )
            ]
        }),

        new WorkPackage({
            id: "WP-106",
            name: "Production Deployment",
            description: "Deploy the approved application.",
            owner: "DevOps Engineer",
            estimatedHours: 16,
            priority: Priority.CRITICAL,
            dependencies: ["WP-105"],
            deliverables: [
                new Deliverable(
                    "Production release",
                    [
                        "Health checks pass",
                        "Rollback procedure is verified"
                    ]
                )
            ]
        })
    ];
}


// ============================================================================
// 5. PACKAGE QUALITY
// ============================================================================

function evaluatePackageQuality(packageItem) {
    return {
        hasId: Boolean(packageItem.id?.trim()),
        hasName: Boolean(packageItem.name?.trim()),
        hasOwner: Boolean(packageItem.owner?.trim()),
        hasPositiveEstimate: packageItem.estimatedHours > 0,
        hasDeliverable: packageItem.deliverables.length > 0,
        hasAcceptanceCriteria: packageItem.deliverables.every(
            deliverable => deliverable.isWellDefined()
        ),
        validProgress:
            packageItem.progressPercent >= 0 &&
            packageItem.progressPercent <= 100
    };
}


// ============================================================================
// 6. DEPENDENCY GRAPH
// ============================================================================

class DependencyGraph {
    constructor(packages) {
        this.packages = new Map(
            packages.map(packageItem => [packageItem.id, packageItem])
        );
    }

    validateReferences() {
        const errors = [];

        for (const packageItem of this.packages.values()) {
            for (const dependency of packageItem.dependencies) {
                if (!this.packages.has(dependency)) {
                    errors.push(
                        `${packageItem.id} references unknown dependency ${dependency}.`
                    );
                }
            }
        }

        return errors;
    }

    topologicalOrder() {
        const indegree = new Map();

        for (const id of this.packages.keys()) {
            indegree.set(id, 0);
        }

        const successors = new Map();

        for (const id of this.packages.keys()) {
            successors.set(id, new Set());
        }

        for (const packageItem of this.packages.values()) {
            for (const dependency of packageItem.dependencies) {
                if (!this.packages.has(dependency)) {
                    throw new Error(`Unknown dependency: ${dependency}`);
                }

                successors.get(dependency).add(packageItem.id);
                indegree.set(
                    packageItem.id,
                    indegree.get(packageItem.id) + 1
                );
            }
        }

        const queue = [];

        for (const [id, degree] of indegree.entries()) {
            if (degree === 0) {
                queue.push(id);
            }
        }

        queue.sort();

        const order = [];

        while (queue.length > 0) {
            const current = queue.shift();
            order.push(current);

            const nextPackages = [...successors.get(current)].sort();

            for (const successor of nextPackages) {
                const newDegree = indegree.get(successor) - 1;
                indegree.set(successor, newDegree);

                if (newDegree === 0) {
                    queue.push(successor);
                    queue.sort();
                }
            }
        }

        if (order.length !== this.packages.size) {
            throw new Error("Dependency cycle detected.");
        }

        return order;
    }

    longestDependencyPath() {
        const order = this.topologicalOrder();
        const earliestFinish = new Map();
        const predecessor = new Map();

        for (const id of order) {
            const packageItem = this.packages.get(id);

            let bestFinish = 0;
            let bestPredecessor = null;

            for (const dependency of packageItem.dependencies) {
                const candidate = earliestFinish.get(dependency);

                if (candidate > bestFinish) {
                    bestFinish = candidate;
                    bestPredecessor = dependency;
                }
            }

            earliestFinish.set(id, bestFinish + packageItem.estimatedHours);
            predecessor.set(id, bestPredecessor);
        }

        let finalId = null;
        let maximum = -Infinity;

        for (const [id, value] of earliestFinish.entries()) {
            if (value > maximum) {
                maximum = value;
                finalId = id;
            }
        }

        const path = [];
        let current = finalId;

        while (current !== null) {
            path.push(current);
            current = predecessor.get(current);
        }

        path.reverse();

        return {
            hours: maximum,
            path
        };
    }
}


// ============================================================================
// 7. ESTIMATION
// ============================================================================

class ThreePointEstimate {
    constructor(optimistic, mostLikely, pessimistic) {
        this.optimistic = optimistic;
        this.mostLikely = mostLikely;
        this.pessimistic = pessimistic;
        this.validate();
    }

    validate() {
        if (
            this.optimistic < 0 ||
            this.mostLikely < 0 ||
            this.pessimistic < 0
        ) {
            throw new Error("Estimates cannot be negative.");
        }

        if (!(
            this.optimistic <=
            this.mostLikely &&
            this.mostLikely <=
            this.pessimistic
        )) {
            throw new Error(
                "Expected optimistic <= most likely <= pessimistic."
            );
        }
    }

    pert() {
        return (
            this.optimistic +
            4 * this.mostLikely +
            this.pessimistic
        ) / 6;
    }
}

function calculateCost(hours, hourlyRate) {
    if (hours < 0 || hourlyRate < 0) {
        throw new Error("Hours and rate cannot be negative.");
    }

    return hours * hourlyRate;
}


// ============================================================================
// 8. PROGRESS METRICS
// ============================================================================

function weightedProgress(packages) {
    const totalEstimate = packages.reduce(
        (sum, item) => sum + item.estimatedHours,
        0
    );

    if (totalEstimate === 0) {
        return 0;
    }

    const weighted = packages.reduce(
        (sum, item) =>
            sum + item.estimatedHours * item.progressPercent,
        0
    );

    return weighted / totalEstimate;
}

function earnedValueMetrics(plannedValue, earnedValue, actualCost) {
    if (plannedValue < 0 || earnedValue < 0 || actualCost < 0) {
        throw new Error("EVM values cannot be negative.");
    }

    return {
        plannedValue,
        earnedValue,
        actualCost,
        CPI: actualCost === 0 ? Infinity : earnedValue / actualCost,
        SPI: plannedValue === 0 ? Infinity : earnedValue / plannedValue
    };
}


// ============================================================================
// 9. RISK ANALYSIS
// ============================================================================

class Risk {
    constructor(id, description, probability, impact, mitigation) {
        this.id = id;
        this.description = description;
        this.probability = probability;
        this.impact = impact;
        this.mitigation = mitigation;
    }

    get expectedExposure() {
        if (this.probability < 0 || this.probability > 1) {
            throw new Error("Probability must be between 0 and 1.");
        }

        if (this.impact < 0) {
            throw new Error("Impact cannot be negative.");
        }

        return this.probability * this.impact;
    }
}


// ============================================================================
// 10. RESOURCE CAPACITY
// ============================================================================

function calculateResourceLoad(packages) {
    const load = new Map();

    for (const packageItem of packages) {
        const current = load.get(packageItem.owner) || 0;
        load.set(
            packageItem.owner,
            current + packageItem.estimatedHours
        );
    }

    return load;
}

function detectOverAllocation(packages, capacity) {
    const load = calculateResourceLoad(packages);
    const overload = new Map();

    for (const [owner, hours] of load.entries()) {
        const available = capacity.get(owner) || 0;

        if (hours > available) {
            overload.set(owner, hours - available);
        }
    }

    return overload;
}


// ============================================================================
// 11. CHANGE CONTROL
// ============================================================================

class ChangeRequest {
    constructor(id, description, addedHours, reason, approved = false) {
        this.id = id;
        this.description = description;
        this.addedHours = addedHours;
        this.reason = reason;
        this.approved = approved;
    }

    validate() {
        if (!this.description?.trim()) {
            throw new Error("Change description is required.");
        }

        if (this.addedHours < 0) {
            throw new Error("Added hours cannot be negative.");
        }
    }
}

function applyChangeRequest(packageItem, changeRequest) {
    changeRequest.validate();

    if (!changeRequest.approved) {
        throw new Error(
            "An unapproved change cannot alter the baseline."
        );
    }

    packageItem.estimatedHours += changeRequest.addedHours;

    return packageItem.estimatedHours;
}


// ============================================================================
// 12. SIMPLE SCHEDULING
// ============================================================================

function addWorkingDays(startDate, durationDays) {
    let current = new Date(startDate);
    let remaining = durationDays - 1;

    while (remaining > 0) {
        current.setDate(current.getDate() + 1);

        const day = current.getDay();

        if (day !== 0 && day !== 6) {
            remaining--;
        }
    }

    return current;
}

function schedulePackages(packages, startDate = new Date("2026-10-01")) {
    const graph = new DependencyGraph(packages);
    const order = graph.topologicalOrder();

    const finishDates = new Map();
    const schedule = new Map();

    for (const id of order) {
        const packageItem = graph.packages.get(id);

        let packageStart = new Date(startDate);

        for (const dependency of packageItem.dependencies) {
            const dependencyFinish = finishDates.get(dependency);

            if (dependencyFinish >= packageStart) {
                packageStart = new Date(dependencyFinish);
                packageStart.setDate(packageStart.getDate() + 1);
            }
        }

        const finish = addWorkingDays(
            packageStart,
            packageItem.scheduleDays()
        );

        schedule.set(id, {
            start: packageStart,
            finish
        });

        finishDates.set(id, finish);
    }

    return schedule;
}


// ============================================================================
// 13. ASYNCHRONOUS EXECUTION SIMULATION
// ============================================================================

function delay(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function validatePackageAsynchronously(packageItem) {
    // Async behavior is useful when real systems validate external APIs,
    // databases, services, or remote approval systems.
    await delay(10);

    return {
        id: packageItem.id,
        valid: packageItem.validate().length === 0
    };
}

async function asynchronousValidation(packages) {
    const results = await Promise.all(
        packages.map(validatePackageAsynchronously)
    );

    console.log("\n=== ASYNCHRONOUS VALIDATION ===");

    for (const result of results) {
        console.log(
            `${result.id}: ${result.valid ? "PASS" : "FAIL"}`
        );
    }
}


// ============================================================================
// 14. REALISTIC CASE STUDY
// ============================================================================

async function runCaseStudy() {
    console.log("=".repeat(72));
    console.log("WORK PACKAGES: MANAGEABLE UNITS OF WORK");
    console.log("=".repeat(72));

    beginnerExample();

    const packages = createProjectPackages();

    console.log("\n=== PACKAGE REGISTER ===");

    for (const packageItem of packages) {
        console.log(
            `${packageItem.id} | ` +
            `${packageItem.name.padEnd(25)} | ` +
            `${packageItem.owner.padEnd(20)} | ` +
            `${String(packageItem.estimatedHours).padStart(3)}h | ` +
            `${packageItem.priority}`
        );
    }

    console.log("\n=== QUALITY CHECK ===");

    for (const packageItem of packages) {
        const quality = evaluatePackageQuality(packageItem);
        const passed = Object.values(quality).every(Boolean);

        console.log(
            `${packageItem.id}: ${passed ? "PASS" : "FAIL"}`
        );
    }

    const graph = new DependencyGraph(packages);

    console.log("\n=== DEPENDENCY ORDER ===");
    console.log(graph.topologicalOrder().join(" -> "));

    const criticalPath = graph.longestDependencyPath();

    console.log("\n=== LONGEST DEPENDENCY PATH ===");
    console.log(criticalPath.path.join(" -> "));
    console.log(
        `Path effort: ${criticalPath.hours.toFixed(1)} hours`
    );

    const estimate = new ThreePointEstimate(24, 32, 56);

    console.log("\n=== ESTIMATION ===");
    console.log(`PERT: ${estimate.pert().toFixed(2)} hours`);
    console.log(
        `Cost at $75/hour: $${calculateCost(
            estimate.pert(),
            75
        ).toFixed(2)}`
    );

    console.log("\n=== RISK ===");

    const risks = [
        new Risk(
            "R-01",
            "API integration delay",
            0.35,
            20,
            "Prototype high-risk interfaces early."
        ),
        new Risk(
            "R-02",
            "Late requirement change",
            0.20,
            30,
            "Baseline requirements and use change control."
        )
    ];

    for (const risk of risks) {
        console.log(
            `${risk.id}: exposure=${risk.expectedExposure.toFixed(2)}`
        );
    }

    const capacity = new Map([
        ["Business Analyst", 40],
        ["UX Lead", 40],
        ["Backend Engineer", 80],
        ["Frontend Engineer", 40],
        ["QA Engineer", 40],
        ["DevOps Engineer", 20]
    ]);

    console.log("\n=== RESOURCE CAPACITY ===");

    const overload = detectOverAllocation(packages, capacity);

    if (overload.size === 0) {
        console.log("No overload detected.");
    } else {
        for (const [owner, hours] of overload.entries()) {
            console.log(
                `${owner}: overloaded by ${hours} hours`
            );
        }
    }

    console.log("\n=== SCHEDULE ===");

    const schedule = schedulePackages(packages);

    for (const id of graph.topologicalOrder()) {
        const item = schedule.get(id);

        console.log(
            `${id}: ${item.start.toISOString().slice(0, 10)} ` +
            `-> ${item.finish.toISOString().slice(0, 10)}`
        );
    }

    const updates = {
        "WP-101": [100, 25],
        "WP-102": [75, 25],
        "WP-103": [60, 42],
        "WP-104": [20, 10],
        "WP-105": [0, 0],
        "WP-106": [0, 0]
    };

    for (const packageItem of packages) {
        const [progress, actual] = updates[packageItem.id];
        packageItem.updateProgress(progress, actual);
    }

    console.log("\n=== PROGRESS ===");

    for (const packageItem of packages) {
        console.log(
            `${packageItem.id}: ` +
            `${packageItem.progressPercent}% | ` +
            `actual=${packageItem.actualHours}h | ` +
            `variance=${packageItem.variance().toFixed(1)}h | ` +
            `${packageItem.status}`
        );
    }

    console.log(
        `\nWeighted progress: ${weightedProgress(packages).toFixed(2)}%`
    );

    console.log("\n=== EARNED VALUE ===");

    const evm = earnedValueMetrics(
        100000,
        72000,
        80000
    );

    console.log(`CPI: ${evm.CPI.toFixed(2)}`);
    console.log(`SPI: ${evm.SPI.toFixed(2)}`);

    console.log("\n=== CHANGE CONTROL ===");

    const change = new ChangeRequest(
        "CR-001",
        "Add audit logging",
        12,
        "New compliance requirement",
        true
    );

    const affectedPackage = packages.find(
        packageItem => packageItem.id === "WP-103"
    );

    console.log(
        `New WP-103 estimate: ${applyChangeRequest(
            affectedPackage,
            change
        )} hours`
    );

    await asynchronousValidation(packages);

    console.log("\n=== EDGE CASE TESTS ===");

    try {
        packages[0].updateProgress(101, 1);
    } catch (error) {
        console.log("Invalid progress rejected:", error.message);
    }

    try {
        const cyclicPackages = [
            new WorkPackage({
                id: "A",
                name: "A",
                description: "Cycle A",
                owner: "Owner",
                estimatedHours: 1,
                dependencies: ["B"]
            }),
            new WorkPackage({
                id: "B",
                name: "B",
                description: "Cycle B",
                owner: "Owner",
                estimatedHours: 1,
                dependencies: ["A"]
            })
        ];

        new DependencyGraph(cyclicPackages).topologicalOrder();
    } catch (error) {
        console.log("Dependency cycle rejected:", error.message);
    }

    console.log("\n=== PROGRAM COMPLETE ===");
}

runCaseStudy().catch(error => {
    console.error("Fatal error:", error.message);
    process.exitCode = 1;
});
