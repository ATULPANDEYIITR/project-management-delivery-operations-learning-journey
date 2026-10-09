"use strict";

/*
 * Gantt chart workflow model.
 * This implementation focuses on dependency-aware scheduling,
 * event-driven progress updates, critical-path calculation,
 * resource conflicts, and policy validation.
 */

const DAY_MS = 24 * 60 * 60 * 1000;

function parseDate(value) {
    const date = new Date(`${value}T00:00:00Z`);
    if (Number.isNaN(date.getTime())) {
        throw new Error(`Invalid date: ${value}`);
    }
    return date;
}

function formatDate(date) {
    return date.toISOString().slice(0, 10);
}

function addDays(date, days) {
    return new Date(date.getTime() + days * DAY_MS);
}

function daysBetween(start, end) {
    return Math.floor((end.getTime() - start.getTime()) / DAY_MS);
}

class GanttTask {
    constructor({
        id,
        name,
        start,
        end,
        dependencies = [],
        progress = 0,
        resource = null,
        milestone = false
    }) {
        this.id = id;
        this.name = name;
        this.start = parseDate(start);
        this.end = parseDate(end);
        this.dependencies = [...dependencies];
        this.progress = progress;
        this.resource = resource;
        this.milestone = milestone;

        this.validate();
    }

    get duration() {
        return daysBetween(this.start, this.end) + 1;
    }

    validate() {
        if (!this.id || !this.name) {
            throw new Error("A task requires an ID and name.");
        }

        if (this.end < this.start) {
            throw new Error(`Task ${this.id} has an invalid date range.`);
        }

        if (this.progress < 0 || this.progress > 100) {
            throw new Error(`Task ${this.id} has invalid progress.`);
        }

        if (this.milestone && this.start.getTime() !== this.end.getTime()) {
            throw new Error("Milestones must have the same start and end date.");
        }
    }
}

class GanttProject {
    constructor(name) {
        this.name = name;
        this.tasks = new Map();
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }

        this.listeners.get(eventName).push(listener);
    }

    emit(eventName, payload) {
        for (const listener of this.listeners.get(eventName) || []) {
            listener(payload);
        }
    }

    addTask(task) {
        if (this.tasks.has(task.id)) {
            throw new Error(`Duplicate task ID: ${task.id}`);
        }

        this.tasks.set(task.id, task);
        this.emit("taskAdded", task);
    }

    updateProgress(taskId, progress) {
        const task = this.getTask(taskId);

        if (progress < 0 || progress > 100) {
            throw new Error("Progress must be between 0 and 100.");
        }

        const oldProgress = task.progress;
        task.progress = progress;

        this.emit("progressChanged", {
            task,
            oldProgress,
            newProgress: progress
        });
    }

    getTask(taskId) {
        const task = this.tasks.get(taskId);

        if (!task) {
            throw new Error(`Unknown task: ${taskId}`);
        }

        return task;
    }

    validate() {
        for (const task of this.tasks.values()) {
            for (const dependencyId of task.dependencies) {
                const dependency = this.getTask(dependencyId);

                if (dependency.end >= task.start) {
                    throw new Error(
                        `Dependency violation: ${dependency.id} must finish ` +
                        `before ${task.id} starts.`
                    );
                }
            }
        }

        this.topologicalOrder();
    }

    topologicalOrder() {
        const indegree = new Map();
        const successors = new Map();

        for (const task of this.tasks.values()) {
            indegree.set(task.id, 0);
            successors.set(task.id, []);
        }

        for (const task of this.tasks.values()) {
            for (const dependencyId of task.dependencies) {
                indegree.set(task.id, indegree.get(task.id) + 1);
                successors.get(dependencyId).push(task.id);
            }
        }

        const queue = [];

        for (const [taskId, degree] of indegree.entries()) {
            if (degree === 0) {
                queue.push(taskId);
            }
        }

        const ordered = [];

        while (queue.length > 0) {
            const current = queue.shift();
            ordered.push(current);

            for (const successor of successors.get(current)) {
                indegree.set(successor, indegree.get(successor) - 1);

                if (indegree.get(successor) === 0) {
                    queue.push(successor);
                }
            }
        }

        if (ordered.length !== this.tasks.size) {
            throw new Error("The schedule contains a circular dependency.");
        }

        return ordered;
    }

    criticalPath() {
        const ordered = this.topologicalOrder();
        const finish = new Map();
        const previous = new Map();

        for (const taskId of ordered) {
            const task = this.getTask(taskId);

            if (task.dependencies.length === 0) {
                finish.set(taskId, task.duration);
                previous.set(taskId, null);
                continue;
            }

            let bestDependency = task.dependencies[0];

            for (const dependency of task.dependencies) {
                if (finish.get(dependency) > finish.get(bestDependency)) {
                    bestDependency = dependency;
                }
            }

            finish.set(
                taskId,
                finish.get(bestDependency) + task.duration
            );
            previous.set(taskId, bestDependency);
        }

        let finalTask = ordered[0];

        for (const taskId of ordered) {
            if (finish.get(taskId) > finish.get(finalTask)) {
                finalTask = taskId;
            }
        }

        const path = [];

        while (finalTask !== null) {
            path.unshift(finalTask);
            finalTask = previous.get(finalTask);
        }

        return path;
    }

    resourceConflicts() {
        const grouped = new Map();

        for (const task of this.tasks.values()) {
            if (!task.resource) {
                continue;
            }

            if (!grouped.has(task.resource)) {
                grouped.set(task.resource, []);
            }

            grouped.get(task.resource).push(task);
        }

        const conflicts = [];

        for (const [resource, tasks] of grouped.entries()) {
            tasks.sort((a, b) => a.start - b.start);

            for (let i = 0; i < tasks.length; i++) {
                for (let j = i + 1; j < tasks.length; j++) {
                    if (tasks[j].start > tasks[i].end) {
                        break;
                    }

                    conflicts.push({
                        resource,
                        firstTask: tasks[i].id,
                        secondTask: tasks[j].id
                    });
                }
            }
        }

        return conflicts;
    }

    render() {
        const tasks = [...this.tasks.values()]
            .sort((a, b) => a.start - b.start);

        if (tasks.length === 0) {
            return `${this.name}\nNo tasks.`;
        }

        const projectStart = new Date(
            Math.min(...tasks.map(task => task.start.getTime()))
        );

        const lines = [
            `GANTT CHART: ${this.name}`,
            `Start: ${formatDate(projectStart)}`,
            ""
        ];

        const labelWidth = Math.max(
            12,
            ...tasks.map(task => task.name.length + 2)
        );

        for (const task of tasks) {
            const offset = daysBetween(projectStart, task.start);
            const completed = Math.round(
                task.duration * task.progress / 100
            );

            let bar;

            if (task.milestone) {
                bar = "*";
            } else {
                bar =
                    "|".repeat(Math.min(completed, task.duration)) +
                    ".".repeat(Math.max(0, task.duration - completed));
            }

            lines.push(
                `${task.name.padEnd(labelWidth)} ` +
                `${" ".repeat(offset)}${bar} ` +
                `${formatDate(task.start)} -> ${formatDate(task.end)} ` +
                `${task.progress}%`
            );
        }

        lines.push(
            "",
            "Legend: | completed, . remaining, * milestone"
        );

        return lines.join("\n");
    }
}

function buildProject() {
    const project = new GanttProject("Customer Data Platform");

    project.on("taskAdded", task => {
        console.log(`Added task: ${task.id} - ${task.name}`);
    });

    project.on("progressChanged", event => {
        console.log(
            `Progress changed: ${event.task.id} ` +
            `${event.oldProgress}% -> ${event.newProgress}%`
        );
    });

    project.addTask(new GanttTask({
        id: "REQ",
        name: "Requirements",
        start: "2026-10-12",
        end: "2026-10-16",
        progress: 100,
        resource: "Product"
    }));

    project.addTask(new GanttTask({
        id: "DES",
        name: "Solution Design",
        start: "2026-10-19",
        end: "2026-10-23",
        dependencies: ["REQ"],
        progress: 80,
        resource: "Architecture"
    }));

    project.addTask(new GanttTask({
        id: "API",
        name: "API Development",
        start: "2026-10-26",
        end: "2026-11-06",
        dependencies: ["DES"],
        progress: 50,
        resource: "Backend"
    }));

    project.addTask(new GanttTask({
        id: "UI",
        name: "Dashboard Development",
        start: "2026-10-26",
        end: "2026-11-13",
        dependencies: ["DES"],
        progress: 30,
        resource: "Frontend"
    }));

    project.addTask(new GanttTask({
        id: "TEST",
        name: "System Testing",
        start: "2026-11-16",
        end: "2026-11-20",
        dependencies: ["API", "UI"],
        progress: 0,
        resource: "QA"
    }));

    project.addTask(new GanttTask({
        id: "GO",
        name: "Production Go-Live",
        start: "2026-11-23",
        end: "2026-11-23",
        dependencies: ["TEST"],
        progress: 0,
        resource: "Release",
        milestone: true
    }));

    return project;
}

function main() {
    const project = buildProject();

    project.validate();
    project.updateProgress("TEST", 15);

    console.log("\n" + project.render());

    console.log("\nCritical path:");
    console.log(project.criticalPath().join(" -> "));

    console.log("\nResource conflicts:");

    const conflicts = project.resourceConflicts();

    if (conflicts.length === 0) {
        console.log("No conflicts detected.");
    } else {
        console.table(conflicts);
    }

    console.log("\nSchedule validation completed successfully.");
}

main();
