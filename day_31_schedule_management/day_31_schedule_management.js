/**
 * Schedule Management: Introduction to Project Scheduling
 *
 * This Node.js program implements an event-driven project scheduling model.
 *
 * It demonstrates:
 * - Activities and milestones
 * - Dependency relationships
 * - Pull-style schedule updates through events
 * - Forward scheduling
 * - Critical-path analysis
 * - Float calculation
 * - Progress events
 * - Schedule variance
 * - Dependency-cycle validation
 * - Status reporting
 *
 * Run with:
 *   node schedule_management.js
 */

"use strict";

const EventEmitter = require("events");

const DependencyType = Object.freeze({
    FINISH_TO_START: "FS",
    START_TO_START: "SS",
    FINISH_TO_FINISH: "FF",
    START_TO_FINISH: "SF"
});

class ScheduleError extends Error {
    constructor(message) {
        super(message);
        this.name = "ScheduleError";
    }
}

class Activity {
    constructor({
        id,
        name,
        duration,
        resources = [],
        milestone = false
    }) {
        if (!id || !id.trim()) {
            throw new TypeError("Activity ID is required.");
        }

        if (!name || !name.trim()) {
            throw new TypeError(`Activity ${id}: name is required.`);
        }

        if (!Number.isInteger(duration) || duration < 0) {
            throw new TypeError(
                `Activity ${id}: duration must be a non-negative integer.`
            );
        }

        if (milestone && duration !== 0) {
            throw new TypeError(
                `Activity ${id}: milestones must have zero duration.`
            );
        }

        this.id = id;
        this.name = name;
        this.duration = duration;
        this.resources = [...resources];
        this.milestone = milestone;

        this.predecessors = new Set();
        this.successors = new Set();

        this.earlyStart = 0;
        this.earlyFinish = 0;
        this.lateStart = 0;
        this.lateFinish = 0;
        this.totalFloat = 0;

        this.percentComplete = 0;
        this.actualStart = null;
        this.actualFinish = null;
    }
}

class ProjectScheduler extends EventEmitter {
    constructor(projectName, startDate = new Date("2026-10-05T00:00:00Z")) {
        super();

        this.projectName = projectName;
        this.startDate = new Date(startDate);

        if (Number.isNaN(this.startDate.getTime())) {
            throw new TypeError("Invalid project start date.");
        }

        this.activities = new Map();
        this.dependencies = [];
        this.resources = new Map();

        /*
         * EventEmitter makes schedule changes observable without tightly
         * coupling progress tracking, reporting, and scheduling logic.
         */
        this.on("progressChanged", (event) => {
            console.log(
                `[EVENT] ${event.activityId} progress changed to ${event.percentComplete}%`
            );
        });

        this.on("scheduleCalculated", (event) => {
            console.log(
                `[EVENT] Schedule recalculated: ${event.duration} schedule day(s)`
            );
        });
    }

    addResource(name, capacity = 1) {
        if (!name || !name.trim()) {
            throw new TypeError("Resource name is required.");
        }

        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new TypeError("Resource capacity must be positive.");
        }

        if (this.resources.has(name)) {
            throw new ScheduleError(`Resource already exists: ${name}`);
        }

        this.resources.set(name, {
            name,
            capacity
        });
    }

    addActivity(config) {
        if (this.activities.has(config.id)) {
            throw new ScheduleError(
                `Activity already exists: ${config.id}`
            );
        }

        for (const resource of config.resources ?? []) {
            if (!this.resources.has(resource)) {
                throw new ScheduleError(
                    `Unknown resource ${resource} for activity ${config.id}`
                );
            }
        }

        this.activities.set(config.id, new Activity(config));
    }

    addDependency(
        predecessorId,
        successorId,
        type = DependencyType.FINISH_TO_START,
        lag = 0
    ) {
        const predecessor = this.activities.get(predecessorId);
        const successor = this.activities.get(successorId);

        if (!predecessor || !successor) {
            throw new ScheduleError(
                "Both dependency activities must exist."
            );
        }

        if (predecessorId === successorId) {
            throw new ScheduleError(
                "An activity cannot depend on itself."
            );
        }

        if (!Object.values(DependencyType).includes(type)) {
            throw new ScheduleError(`Unsupported dependency type: ${type}`);
        }

        if (!Number.isInteger(lag) || lag < 0) {
            throw new ScheduleError(
                "Lag must be a non-negative integer."
            );
        }

        const duplicate = this.dependencies.some(
            dependency =>
                dependency.predecessor === predecessorId &&
                dependency.successor === successorId &&
                dependency.type === type &&
                dependency.lag === lag
        );

        if (duplicate) {
            throw new ScheduleError("Duplicate dependency.");
        }

        const dependency = {
            predecessor: predecessorId,
            successor: successorId,
            type,
            lag
        };

        this.dependencies.push(dependency);
        predecessor.successors.add(successorId);
        successor.predecessors.add(predecessorId);
    }

    topologicalOrder() {
        const indegree = new Map();

        for (const activityId of this.activities.keys()) {
            indegree.set(activityId, 0);
        }

        for (const dependency of this.dependencies) {
            indegree.set(
                dependency.successor,
                indegree.get(dependency.successor) + 1
            );
        }

        const queue = [];

        for (const [activityId, degree] of indegree.entries()) {
            if (degree === 0) {
                queue.push(activityId);
            }
        }

        const order = [];

        while (queue.length > 0) {
            const current = queue.shift();
            order.push(current);

            for (const successorId of this.activities.get(current).successors) {
                const nextDegree = indegree.get(successorId) - 1;
                indegree.set(successorId, nextDegree);

                if (nextDegree === 0) {
                    queue.push(successorId);
                }
            }
        }

        if (order.length !== this.activities.size) {
            throw new ScheduleError(
                "Dependency cycle detected."
            );
        }

        return order;
    }

    dependencyConstraintsFor(successorId) {
        return this.dependencies.filter(
            dependency => dependency.successor === successorId
        );
    }

    calculateEarlyDates(activity) {
        let earlyStart = 0;

        for (const dependency of this.dependencyConstraintsFor(activity.id)) {
            const predecessor =
                this.activities.get(dependency.predecessor);

            let constraint;

            switch (dependency.type) {
                case DependencyType.FINISH_TO_START:
                    constraint =
                        predecessor.earlyFinish + dependency.lag;
                    break;

                case DependencyType.START_TO_START:
                    constraint =
                        predecessor.earlyStart + dependency.lag;
                    break;

                case DependencyType.FINISH_TO_FINISH:
                    constraint =
                        predecessor.earlyFinish +
                        dependency.lag -
                        activity.duration;
                    break;

                case DependencyType.START_TO_FINISH:
                    constraint =
                        predecessor.earlyStart +
                        dependency.lag -
                        activity.duration;
                    break;

                default:
                    throw new ScheduleError(
                        `Unsupported relationship: ${dependency.type}`
                    );
            }

            earlyStart = Math.max(earlyStart, constraint);
        }

        activity.earlyStart = earlyStart;
        activity.earlyFinish =
            earlyStart + activity.duration;
    }

    calculateLateDates(activity, projectFinish) {
        const successors = this.dependencies.filter(
            dependency =>
                dependency.predecessor === activity.id
        );

        if (successors.length === 0) {
            activity.lateFinish = projectFinish;
            activity.lateStart =
                projectFinish - activity.duration;
            return;
        }

        let latestFinish = projectFinish;

        for (const dependency of successors) {
            const successor =
                this.activities.get(dependency.successor);

            let constraint;

            switch (dependency.type) {
                case DependencyType.FINISH_TO_START:
                    constraint =
                        successor.lateStart - dependency.lag;
                    break;

                case DependencyType.START_TO_START:
                    constraint =
                        successor.lateStart - dependency.lag;
                    break;

                case DependencyType.FINISH_TO_FINISH:
                    constraint =
                        successor.lateFinish - dependency.lag;
                    break;

                case DependencyType.START_TO_FINISH:
                    constraint =
                        successor.lateFinish - dependency.lag;
                    break;

                default:
                    throw new ScheduleError(
                        `Unsupported relationship: ${dependency.type}`
                    );
            }

            latestFinish = Math.min(
                latestFinish,
                constraint
            );
        }

        activity.lateFinish = latestFinish;
        activity.lateStart =
            latestFinish - activity.duration;
    }

    calculate() {
        const order = this.topologicalOrder();

        for (const activityId of order) {
            this.calculateEarlyDates(
                this.activities.get(activityId)
            );
        }

        const projectFinish = Math.max(
            0,
            ...[...this.activities.values()]
                .map(activity => activity.earlyFinish)
        );

        for (const activityId of [...order].reverse()) {
            const activity = this.activities.get(activityId);

            this.calculateLateDates(
                activity,
                projectFinish
            );

            activity.totalFloat =
                activity.lateStart -
                activity.earlyStart;
        }

        this.emit("scheduleCalculated", {
            projectName: this.projectName,
            duration: projectFinish
        });

        return projectFinish;
    }

    criticalActivities() {
        this.calculate();

        return [...this.activities.values()]
            .filter(activity => activity.totalFloat === 0);
    }

    criticalPath() {
        this.calculate();

        const criticalIds = new Set(
            this.criticalActivities().map(
                activity => activity.id
            )
        );

        const starts = [...this.activities.values()]
            .filter(
                activity =>
                    activity.predecessors.size === 0 &&
                    criticalIds.has(activity.id)
            )
            .sort(
                (a, b) => a.earlyStart - b.earlyStart
            );

        if (starts.length === 0) {
            return [];
        }

        const path = [];
        let current = starts[0];

        path.push(current);

        while (true) {
            const candidates = [...current.successors]
                .map(id => this.activities.get(id))
                .filter(
                    activity =>
                        criticalIds.has(activity.id) &&
                        activity.earlyStart ===
                            current.earlyFinish
                )
                .sort(
                    (a, b) =>
                        a.earlyStart - b.earlyStart
                );

            if (candidates.length === 0) {
                break;
            }

            current = candidates[0];
            path.push(current);
        }

        return path;
    }

    updateProgress(
        activityId,
        percentComplete,
        actualStart = null,
        actualFinish = null
    ) {
        const activity = this.activities.get(activityId);

        if (!activity) {
            throw new ScheduleError(
                `Unknown activity: ${activityId}`
            );
        }

        if (
            !Number.isFinite(percentComplete) ||
            percentComplete < 0 ||
            percentComplete > 100
        ) {
            throw new TypeError(
                "Progress must be between 0 and 100."
            );
        }

        if (
            percentComplete === 100 &&
            actualFinish === null
        ) {
            throw new ScheduleError(
                "Completed activities require an actual finish."
            );
        }

        activity.percentComplete = percentComplete;
        activity.actualStart = actualStart;
        activity.actualFinish = actualFinish;

        this.emit("progressChanged", {
            activityId,
            percentComplete,
            actualStart,
            actualFinish
        });
    }

    scheduleVariance(activityId, actualFinish) {
        this.calculate();

        const activity = this.activities.get(activityId);

        if (!activity) {
            throw new ScheduleError(
                `Unknown activity: ${activityId}`
            );
        }

        return actualFinish - activity.earlyFinish;
    }

    findResourceConflicts() {
        this.calculate();

        const conflicts = [];

        for (const [resourceName, resource] of this.resources) {
            if (resource.capacity !== 1) {
                continue;
            }

            const assigned = [...this.activities.values()]
                .filter(
                    activity =>
                        activity.resources.includes(resourceName) &&
                        activity.duration > 0
                );

            for (let i = 0; i < assigned.length; i++) {
                for (let j = i + 1; j < assigned.length; j++) {
                    const first = assigned[i];
                    const second = assigned[j];

                    const overlaps =
                        first.earlyStart < second.earlyFinish &&
                        second.earlyStart < first.earlyFinish;

                    if (overlaps) {
                        conflicts.push({
                            resource: resourceName,
                            first: first.id,
                            second: second.id
                        });
                    }
                }
            }
        }

        return conflicts;
    }

    dateForOffset(offset) {
        const result = new Date(this.startDate);
        result.setUTCDate(result.getUTCDate() + offset);
        return result.toISOString().slice(0, 10);
    }

    report() {
        const duration = this.calculate();

        const rows = [...this.activities.values()]
            .sort(
                (a, b) =>
                    a.earlyStart - b.earlyStart ||
                    a.id.localeCompare(b.id)
            )
            .map(activity => ({
                id: activity.id,
                name: activity.name,
                earlyStart: activity.earlyStart,
                earlyFinish: activity.earlyFinish,
                lateStart: activity.lateStart,
                lateFinish: activity.lateFinish,
                float: activity.totalFloat,
                progress: activity.percentComplete,
                critical: activity.totalFloat === 0
            }));

        return {
            project: this.projectName,
            duration,
            startDate: this.dateForOffset(0),
            finishDate: this.dateForOffset(duration),
            activities: rows,
            criticalPath: this.criticalPath().map(
                activity => activity.id
            ),
            resourceConflicts: this.findResourceConflicts()
        };
    }
}

function buildReleaseSchedule() {
    const scheduler = new ProjectScheduler(
        "Customer Analytics Platform Release"
    );

    scheduler.addResource("Product Manager");
    scheduler.addResource("Backend Engineer");
    scheduler.addResource("Frontend Engineer");
    scheduler.addResource("QA Engineer");
    scheduler.addResource("Security Engineer");

    scheduler.addActivity({
        id: "REQ",
        name: "Requirements and acceptance criteria",
        duration: 3,
        resources: ["Product Manager"]
    });

    scheduler.addActivity({
        id: "ARCH",
        name: "Architecture and API design",
        duration: 4,
        resources: ["Backend Engineer"]
    });

    scheduler.addActivity({
        id: "DB",
        name: "Database implementation",
        duration: 5,
        resources: ["Backend Engineer"]
    });

    scheduler.addActivity({
        id: "API",
        name: "Backend API implementation",
        duration: 7,
        resources: ["Backend Engineer"]
    });

    scheduler.addActivity({
        id: "UI",
        name: "Frontend dashboard implementation",
        duration: 6,
        resources: ["Frontend Engineer"]
    });

    scheduler.addActivity({
        id: "SEC",
        name: "Security review",
        duration: 3,
        resources: ["Security Engineer"]
    });

    scheduler.addActivity({
        id: "TEST",
        name: "Integration testing",
        duration: 5,
        resources: ["QA Engineer"]
    });

    scheduler.addActivity({
        id: "UAT",
        name: "User acceptance testing",
        duration: 4,
        resources: ["Product Manager", "QA Engineer"]
    });

    scheduler.addActivity({
        id: "REL",
        name: "Production release",
        duration: 0,
        resources: ["Backend Engineer"],
        milestone: true
    });

    scheduler.addDependency("REQ", "ARCH");
    scheduler.addDependency("ARCH", "DB");
    scheduler.addDependency("ARCH", "API");
    scheduler.addDependency("REQ", "UI");
    scheduler.addDependency("API", "SEC");
    scheduler.addDependency("DB", "TEST");
    scheduler.addDependency("API", "TEST");
    scheduler.addDependency("UI", "TEST");
    scheduler.addDependency("SEC", "TEST");
    scheduler.addDependency("TEST", "UAT");
    scheduler.addDependency("UAT", "REL");

    return scheduler;
}

function demonstrateRelationshipTypes() {
    const scheduler = new ProjectScheduler(
        "Relationship Demonstration"
    );

    scheduler.addActivity({
        id: "DESIGN",
        name: "Design",
        duration: 4
    });

    scheduler.addActivity({
        id: "BUILD",
        name: "Build",
        duration: 6
    });

    scheduler.addActivity({
        id: "TEST",
        name: "Test",
        duration: 3
    });

    scheduler.addDependency(
        "DESIGN",
        "BUILD",
        DependencyType.FINISH_TO_START
    );

    scheduler.addDependency(
        "BUILD",
        "TEST",
        DependencyType.START_TO_START,
        2
    );

    scheduler.calculate();

    console.log("\nDependency relationships");

    for (const activity of scheduler.activities.values()) {
        console.log(
            `${activity.id}: ES=${activity.earlyStart}, EF=${activity.earlyFinish}`
        );
    }
}

function demonstrateProgress(scheduler) {
    scheduler.updateProgress(
        "REQ",
        100,
        0,
        4
    );

    scheduler.updateProgress(
        "API",
        50,
        4
    );

    const variance = scheduler.scheduleVariance(
        "REQ",
        4
    );

    console.log(
        `Requirements schedule variance: ${variance} day(s)`
    );
}

function demonstrateFailureHandling() {
    const invalid = new ProjectScheduler(
        "Invalid Schedule"
    );

    invalid.addActivity({
        id: "A",
        name: "Design",
        duration: 2
    });

    invalid.addActivity({
        id: "B",
        name: "Build",
        duration: 3
    });

    invalid.addDependency("A", "B");
    invalid.addDependency("B", "A");

    try {
        invalid.calculate();
    } catch (error) {
        if (error instanceof ScheduleError) {
            console.log(
                `\nInvalid schedule rejected: ${error.message}`
            );
        } else {
            throw error;
        }
    }
}

function printReport(report) {
    console.log("\nProject Schedule");
    console.log("================");

    console.log(`Project: ${report.project}`);
    console.log(`Start: ${report.startDate}`);
    console.log(`Finish: ${report.finishDate}`);
    console.log(`Duration: ${report.duration} days`);

    console.table(report.activities);

    console.log(
        `Critical path: ${report.criticalPath.join(" -> ")}`
    );

    console.log(
        "Resource conflicts:",
        report.resourceConflicts
    );
}

function main() {
    const scheduler = buildReleaseSchedule();

    const report = scheduler.report();
    printReport(report);

    demonstrateRelationshipTypes();
    demonstrateProgress(scheduler);
    demonstrateFailureHandling();

    console.log("\nSchedule management observations");
    console.log("===============================");
    console.log(
        "A dependency network establishes logical sequencing; it does not automatically solve resource contention."
    );
    console.log(
        "Critical activities have zero float under the calculated network."
    );
    console.log(
        "Progress events can notify other components when execution changes the schedule state."
    );
}

main();
