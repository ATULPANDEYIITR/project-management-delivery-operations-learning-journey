/**
 * Activity Sequencing: Determining Activity Order
 *
 * This Node.js program models activity sequencing as a directed acyclic graph.
 * It demonstrates:
 * - activity dependencies
 * - event-driven sequencing
 * - topological ordering
 * - dependency levels
 * - critical-path calculations
 * - dependency validation
 * - cycle detection
 * - asynchronous execution of dependency-ready activities
 * - the distinction between logical readiness and resource availability
 *
 * Run with:
 *   node activity-sequencing.js
 */

"use strict";

class Activity {
    constructor(id, name, duration, predecessors = []) {
        if (!id || typeof id !== "string") {
            throw new TypeError("Activity ID must be a non-empty string.");
        }

        if (!name || typeof name !== "string") {
            throw new TypeError(`Activity ${id}: name must be a non-empty string.`);
        }

        if (!Number.isFinite(duration) || duration < 0) {
            throw new RangeError(
                `Activity ${id}: duration must be a non-negative number.`
            );
        }

        this.id = id;
        this.name = name;
        this.duration = duration;
        this.predecessors = new Set(predecessors);

        if (this.predecessors.has(id)) {
            throw new Error(`Activity ${id} cannot depend on itself.`);
        }
    }
}

class ActivityNetwork {
    constructor() {
        this.activities = new Map();
    }

    addActivity(id, name, duration, predecessors = []) {
        if (this.activities.has(id)) {
            throw new Error(`Activity ${id} already exists.`);
        }

        this.activities.set(
            id,
            new Activity(id, name, duration, predecessors)
        );
    }

    successors() {
        const result = new Map();

        for (const id of this.activities.keys()) {
            result.set(id, new Set());
        }

        for (const activity of this.activities.values()) {
            for (const predecessor of activity.predecessors) {
                if (!this.activities.has(predecessor)) {
                    throw new Error(
                        `Activity ${activity.id} references unknown predecessor ${predecessor}.`
                    );
                }

                result.get(predecessor).add(activity.id);
            }
        }

        return result;
    }

    topologicalOrder() {
        const successors = this.successors();

        const indegree = new Map(
            [...this.activities.entries()].map(([id, activity]) => [
                id,
                activity.predecessors.size
            ])
        );

        // A sorted queue makes the demonstration deterministic when several
        // activities become ready at the same time.
        const ready = [...this.activities.keys()]
            .filter(id => indegree.get(id) === 0)
            .sort();

        const order = [];

        while (ready.length > 0) {
            const current = ready.shift();
            order.push(current);

            const nextActivities = [...successors.get(current)].sort();

            for (const next of nextActivities) {
                indegree.set(next, indegree.get(next) - 1);

                if (indegree.get(next) === 0) {
                    ready.push(next);
                    ready.sort();
                }
            }
        }

        if (order.length !== this.activities.size) {
            const unresolved = [...this.activities.keys()]
                .filter(id => !order.includes(id));

            throw new Error(
                `Circular dependency detected. Unresolved activities: ${unresolved.join(", ")}`
            );
        }

        return order;
    }

    dependencyLevels() {
        const order = this.topologicalOrder();
        const levels = new Map();
        const levelByActivity = new Map();

        for (const id of order) {
            const activity = this.activities.get(id);

            if (activity.predecessors.size === 0) {
                levelByActivity.set(id, 0);
            } else {
                const predecessorLevels = [...activity.predecessors]
                    .map(predecessor => levelByActivity.get(predecessor));

                levelByActivity.set(
                    id,
                    Math.max(...predecessorLevels) + 1
                );
            }

            const level = levelByActivity.get(id);

            if (!levels.has(level)) {
                levels.set(level, []);
            }

            levels.get(level).push(id);
        }

        return levels;
    }

    criticalPath() {
        const order = this.topologicalOrder();
        const successors = this.successors();

        const es = new Map();
        const ef = new Map();

        for (const id of order) {
            const activity = this.activities.get(id);

            const earliestStart =
                activity.predecessors.size === 0
                    ? 0
                    : Math.max(
                        ...[...activity.predecessors].map(
                            predecessor => ef.get(predecessor)
                        )
                    );

            es.set(id, earliestStart);
            ef.set(id, earliestStart + activity.duration);
        }

        const projectDuration = Math.max(...ef.values());

        const ls = new Map();
        const lf = new Map();

        for (const id of [...order].reverse()) {
            const activity = this.activities.get(id);
            const children = [...successors.get(id)];

            const latestFinish =
                children.length === 0
                    ? projectDuration
                    : Math.min(
                        ...children.map(child => ls.get(child))
                    );

            lf.set(id, latestFinish);
            ls.set(id, latestFinish - activity.duration);
        }

        const result = new Map();

        for (const id of order) {
            const float = Math.max(0, ls.get(id) - es.get(id));

            result.set(id, {
                earliestStart: es.get(id),
                earliestFinish: ef.get(id),
                latestStart: ls.get(id),
                latestFinish: lf.get(id),
                float
            });
        }

        return {
            projectDuration,
            activities: result
        };
    }

    criticalActivities() {
        const analysis = this.criticalPath().activities;

        return [...analysis.entries()]
            .filter(([, values]) => values.float === 0)
            .map(([id]) => id);
    }

    printNetwork() {
        console.log("\nActivity Dependency Model");
        console.log("-".repeat(76));

        for (const id of this.topologicalOrder()) {
            const activity = this.activities.get(id);
            const predecessors =
                [...activity.predecessors].sort().join(", ") || "None";

            console.log(
                `${id.padEnd(5)} ${activity.name.padEnd(32)} ` +
                `duration=${String(activity.duration).padStart(3)} ` +
                `predecessors=${predecessors}`
            );
        }
    }
}

/**
 * An EventEmitter-like sequencing layer.
 *
 * JavaScript's event-driven model is useful for representing state changes:
 * when an activity completes, dependent activities are reconsidered. The
 * scheduler below uses EventTarget so listeners can observe those changes
 * without being coupled to the scheduling algorithm.
 */
class SequencingEngine extends EventTarget {
    constructor(network) {
        super();
        this.network = network;
        this.completed = new Set();
        this.started = new Set();
    }

    readyActivities() {
        return [...this.network.activities.values()]
            .filter(activity => {
                if (this.started.has(activity.id)) {
                    return false;
                }

                return [...activity.predecessors].every(
                    predecessor => this.completed.has(predecessor)
                );
            })
            .map(activity => activity.id)
            .sort();
    }

    markCompleted(activityId) {
        if (!this.network.activities.has(activityId)) {
            throw new Error(`Unknown activity: ${activityId}`);
        }

        if (!this.started.has(activityId)) {
            throw new Error(
                `Activity ${activityId} cannot complete before it starts.`
            );
        }

        this.completed.add(activityId);

        this.dispatchEvent(
            new CustomEvent("activity-completed", {
                detail: {
                    activityId,
                    newlyReady: this.readyActivities()
                }
            })
        );
    }

    start(activityId) {
        if (!this.network.activities.has(activityId)) {
            throw new Error(`Unknown activity: ${activityId}`);
        }

        if (!this.readyActivities().includes(activityId)) {
            throw new Error(
                `Activity ${activityId} is not dependency-ready.`
            );
        }

        this.started.add(activityId);

        this.dispatchEvent(
            new CustomEvent("activity-started", {
                detail: { activityId }
            })
        );
    }
}

/**
 * A dependency-driven asynchronous simulation.
 *
 * Real project work is not represented by waiting for actual days here.
 * Instead, the duration is scaled to milliseconds so the dependency events
 * can be observed without making the program slow.
 */
async function simulateParallelExecution(network) {
    const engine = new SequencingEngine(network);
    const startTimes = new Map();
    const finishTimes = new Map();

    engine.addEventListener("activity-started", event => {
        const id = event.detail.activityId;
        startTimes.set(id, Date.now());

        console.log(`[START ] ${id} - ${network.activities.get(id).name}`);
    });

    engine.addEventListener("activity-completed", event => {
        const id = event.detail.activityId;

        console.log(
            `[FINISH] ${id} - ${network.activities.get(id).name}`
        );

        finishTimes.set(id, Date.now());

        const ready = event.detail.newlyReady;

        if (ready.length > 0) {
            console.log(`         Newly dependency-ready: ${ready.join(", ")}`);
        }
    });

    const pending = new Set(network.activities.keys());

    while (pending.size > 0) {
        const ready = engine.readyActivities();

        if (ready.length === 0) {
            throw new Error(
                "Execution stopped because pending activities have unsatisfied dependencies."
            );
        }

        // All dependency-ready activities are launched together. This models
        // logical parallelism only; real resource limits could require a
        // separate dispatcher or resource-allocation policy.
        const running = [];

        for (const id of ready) {
            engine.start(id);
            pending.delete(id);

            const activity = network.activities.get(id);

            const simulatedMilliseconds =
                Math.max(20, activity.duration * 80);

            running.push(
                new Promise(resolve => {
                    setTimeout(() => {
                        engine.markCompleted(id);
                        resolve();
                    }, simulatedMilliseconds);
                })
            );
        }

        await Promise.all(running);
    }

    return {
        startTimes,
        finishTimes
    };
}

function demonstrateCycleDetection() {
    console.log("\nDependency Validation");
    console.log("-".repeat(76));

    const cyclic = new ActivityNetwork();

    cyclic.addActivity("A", "Requirements", 2, ["C"]);
    cyclic.addActivity("B", "Design", 3, ["A"]);
    cyclic.addActivity("C", "Review", 1, ["B"]);

    try {
        cyclic.topologicalOrder();
    } catch (error) {
        console.log(`Cycle correctly rejected: ${error.message}`);
    }
}

function demonstrateCriticalPath(network) {
    const analysis = network.criticalPath();

    console.log("\nCritical Path Analysis");
    console.log("-".repeat(76));

    console.log(
        "ID".padEnd(6) +
        "ES".padStart(7) +
        "EF".padStart(7) +
        "LS".padStart(7) +
        "LF".padStart(7) +
        "Float".padStart(9)
    );

    for (const id of network.topologicalOrder()) {
        const values = analysis.activities.get(id);

        console.log(
            id.padEnd(6) +
            values.earliestStart.toFixed(1).padStart(7) +
            values.earliestFinish.toFixed(1).padStart(7) +
            values.latestStart.toFixed(1).padStart(7) +
            values.latestFinish.toFixed(1).padStart(7) +
            values.float.toFixed(1).padStart(9)
        );
    }

    console.log(
        `\nDependency-constrained project duration: ${analysis.projectDuration} days`
    );

    console.log(
        `Critical activities: ${network.criticalActivities().join(" -> ")}`
    );
}

async function main() {
    console.log("=".repeat(76));
    console.log("ACTIVITY SEQUENCING: DETERMINING ACTIVITY ORDER");
    console.log("=".repeat(76));

    const network = new ActivityNetwork();

    network.addActivity("A", "Release scope definition", 2);
    network.addActivity("B", "Architecture design", 3, ["A"]);
    network.addActivity("C", "Test strategy design", 2, ["A"]);
    network.addActivity("D", "Database implementation", 4, ["B"]);
    network.addActivity("E", "Service implementation", 5, ["B"]);
    network.addActivity("F", "Test environment setup", 2, ["C"]);
    network.addActivity("G", "Integration testing", 3, ["D", "E", "F"]);
    network.addActivity("H", "Release validation", 2, ["G"]);
    network.addActivity("I", "Production deployment", 1, ["H"]);

    network.printNetwork();

    console.log("\nDependency-Valid Sequence");
    console.log("-".repeat(76));
    console.log(network.topologicalOrder().join(" -> "));

    console.log("\nDependency Levels");
    console.log("-".repeat(76));

    for (const [level, activities] of network.dependencyLevels()) {
        console.log(`Level ${level}: ${activities.join(", ")}`);
    }

    demonstrateCriticalPath(network);

    console.log("\nEvent-Driven Dependency Simulation");
    console.log("-".repeat(76));

    await simulateParallelExecution(network);

    demonstrateCycleDetection();

    console.log("\nScheduling Interpretation");
    console.log("-".repeat(76));
    console.log(
        "Dependency order determines which activities are logically eligible "
        + "to start. Activities at the same dependency frontier may execute "
        + "in parallel, but this does not guarantee resource availability. "
        + "Critical-path analysis identifies activities whose sequencing "
        + "constraints directly affect the earliest project completion date."
    );
}

main().catch(error => {
    console.error(`Fatal scheduling error: ${error.message}`);
    process.exitCode = 1;
});
