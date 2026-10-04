/**
 * Project Dependencies: Understanding Task Dependencies
 *
 * Node.js executable demonstration.
 *
 * This implementation uses JavaScript's event-driven model to represent a
 * dependency-aware project scheduler. It focuses on task events, readiness,
 * dependency propagation, execution waves, asynchronous task simulation,
 * failure propagation, and policy validation.
 *
 * Run with:
 *   node project-dependencies.js
 */

"use strict";

const fs = require("node:fs/promises");

const TaskStatus = Object.freeze({
  NOT_STARTED: "not_started",
  IN_PROGRESS: "in_progress",
  COMPLETED: "completed",
  FAILED: "failed",
  BLOCKED: "blocked"
});

const PRIORITY_WEIGHT = Object.freeze({
  low: 1,
  normal: 2,
  high: 3,
  critical: 4
});

class DependencyError extends Error {
  constructor(message) {
    super(message);
    this.name = "DependencyError";
  }
}

class Project {
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
    const listeners = this.listeners.get(eventName) || [];

    for (const listener of listeners) {
      listener(payload);
    }
  }

  addTask({
    id,
    name,
    duration,
    dependencies = [],
    owner = "unassigned",
    priority = "normal"
  }) {
    if (!id || !id.trim()) {
      throw new DependencyError("Task ID is required.");
    }

    if (this.tasks.has(id)) {
      throw new DependencyError(`Task ${id} already exists.`);
    }

    if (!name || !name.trim()) {
      throw new DependencyError(`Task ${id} must have a name.`);
    }

    if (!Number.isFinite(duration) || duration <= 0) {
      throw new DependencyError(
        `Task ${id} must have a positive duration.`
      );
    }

    if (!(priority in PRIORITY_WEIGHT)) {
      throw new DependencyError(`Invalid priority: ${priority}`);
    }

    const uniqueDependencies = new Set(dependencies);

    if (uniqueDependencies.has(id)) {
      throw new DependencyError(
        `Task ${id} cannot depend on itself.`
      );
    }

    this.tasks.set(id, {
      id,
      name,
      duration,
      dependencies: uniqueDependencies,
      owner,
      priority,
      status: TaskStatus.NOT_STARTED,
      failureReason: null
    });

    try {
      this.validate();
    } catch (error) {
      this.tasks.delete(id);
      throw error;
    }

    this.emit("taskAdded", this.tasks.get(id));
  }

  validateReferences() {
    const missing = [];

    for (const task of this.tasks.values()) {
      for (const dependency of task.dependencies) {
        if (!this.tasks.has(dependency)) {
          missing.push(`${task.id} -> missing ${dependency}`);
        }
      }
    }

    if (missing.length > 0) {
      throw new DependencyError(
        `Unknown dependency references: ${missing.join(", ")}`
      );
    }
  }

  detectCycles() {
    this.validateReferences();

    const visiting = new Set();
    const visited = new Set();
    const cycles = [];

    const visit = (id, path) => {
      if (visiting.has(id)) {
        const start = path.indexOf(id);
        cycles.push([...path.slice(start), id]);
        return;
      }

      if (visited.has(id)) {
        return;
      }

      visiting.add(id);
      path.push(id);

      const task = this.tasks.get(id);

      for (const dependency of task.dependencies) {
        visit(dependency, path);
      }

      path.pop();
      visiting.delete(id);
      visited.add(id);
    };

    for (const id of this.tasks.keys()) {
      visit(id, []);
    }

    return cycles;
  }

  validate() {
    this.validateReferences();

    const cycles = this.detectCycles();

    if (cycles.length > 0) {
      const rendered = cycles
        .map(cycle => cycle.join(" -> "))
        .join("; ");

      throw new DependencyError(
        `Circular dependency detected: ${rendered}`
      );
    }
  }

  dependentsOf(id) {
    if (!this.tasks.has(id)) {
      throw new DependencyError(`Unknown task: ${id}`);
    }

    const result = [];

    for (const task of this.tasks.values()) {
      if (task.dependencies.has(id)) {
        result.push(task.id);
      }
    }

    return result.sort();
  }

  prerequisitesOf(id) {
    const task = this.tasks.get(id);

    if (!task) {
      throw new DependencyError(`Unknown task: ${id}`);
    }

    return [...task.dependencies].sort();
  }

  isReady(id) {
    const task = this.tasks.get(id);

    if (!task || task.status !== TaskStatus.NOT_STARTED) {
      return false;
    }

    return [...task.dependencies].every(
      dependency =>
        this.tasks.get(dependency).status === TaskStatus.COMPLETED
    );
  }

  readyTasks() {
    return [...this.tasks.values()]
      .filter(task => this.isReady(task.id))
      .sort((a, b) => {
        const priorityDifference =
          PRIORITY_WEIGHT[b.priority] - PRIORITY_WEIGHT[a.priority];

        return priorityDifference || a.id.localeCompare(b.id);
      });
  }

  markInProgress(id) {
    const task = this.tasks.get(id);

    if (!task) {
      throw new DependencyError(`Unknown task: ${id}`);
    }

    if (task.status !== TaskStatus.NOT_STARTED) {
      throw new DependencyError(
        `Task ${id} cannot start from ${task.status}.`
      );
    }

    const blockers = [...task.dependencies].filter(
      dependency =>
        this.tasks.get(dependency).status !== TaskStatus.COMPLETED
    );

    if (blockers.length > 0) {
      throw new DependencyError(
        `Task ${id} is blocked by ${blockers.join(", ")}.`
      );
    }

    task.status = TaskStatus.IN_PROGRESS;
    this.emit("taskStarted", task);
  }

  markCompleted(id) {
    const task = this.tasks.get(id);

    if (!task) {
      throw new DependencyError(`Unknown task: ${id}`);
    }

    if (task.status !== TaskStatus.IN_PROGRESS) {
      throw new DependencyError(
        `Task ${id} must be in progress before completion.`
      );
    }

    task.status = TaskStatus.COMPLETED;
    this.emit("taskCompleted", task);
  }

  markFailed(id, reason) {
    const task = this.tasks.get(id);

    if (!task) {
      throw new DependencyError(`Unknown task: ${id}`);
    }

    if (task.status !== TaskStatus.IN_PROGRESS) {
      throw new DependencyError(
        `Task ${id} must be in progress before it can fail.`
      );
    }

    task.status = TaskStatus.FAILED;
    task.failureReason = reason;

    this.emit("taskFailed", {
      task,
      reason
    });

    this.propagateBlockedTasks();
  }

  propagateBlockedTasks() {
    let changed = true;

    while (changed) {
      changed = false;

      for (const task of this.tasks.values()) {
        if (
          task.status !== TaskStatus.NOT_STARTED &&
          task.status !== TaskStatus.BLOCKED
        ) {
          continue;
        }

        const hasFailedPrerequisite = [...task.dependencies].some(
          dependency => {
            const dependencyTask = this.tasks.get(dependency);

            return (
              dependencyTask.status === TaskStatus.FAILED ||
              dependencyTask.status === TaskStatus.BLOCKED
            );
          }
        );

        if (hasFailedPrerequisite && task.status !== TaskStatus.BLOCKED) {
          task.status = TaskStatus.BLOCKED;
          changed = true;

          this.emit("taskBlocked", task);
        }
      }
    }
  }

  topologicalOrder() {
    this.validate();

    const indegree = new Map();

    for (const task of this.tasks.values()) {
      indegree.set(task.id, task.dependencies.size);
    }

    const dependents = new Map();

    for (const task of this.tasks.values()) {
      dependents.set(task.id, []);
    }

    for (const task of this.tasks.values()) {
      for (const dependency of task.dependencies) {
        dependents.get(dependency).push(task.id);
      }
    }

    const ready = [...indegree.entries()]
      .filter(([, count]) => count === 0)
      .map(([id]) => id)
      .sort();

    const order = [];

    while (ready.length > 0) {
      const current = ready.shift();
      order.push(current);

      for (const dependent of dependents.get(current).sort()) {
        const count = indegree.get(dependent) - 1;
        indegree.set(dependent, count);

        if (count === 0) {
          ready.push(dependent);
          ready.sort();
        }
      }
    }

    if (order.length !== this.tasks.size) {
      throw new DependencyError(
        "A complete execution order cannot be constructed."
      );
    }

    return order;
  }

  executionWaves() {
    const order = this.topologicalOrder();
    const remaining = new Map(
      [...this.tasks.values()].map(task => [
        task.id,
        task.dependencies.size
      ])
    );

    const dependents = new Map(
      [...this.tasks.keys()].map(id => [id, []])
    );

    for (const task of this.tasks.values()) {
      for (const dependency of task.dependencies) {
        dependents.get(dependency).push(task.id);
      }
    }

    let wave = order.filter(id => remaining.get(id) === 0);
    const waves = [];

    while (wave.length > 0) {
      wave.sort();
      waves.push(wave);

      const next = [];

      for (const completedId of wave) {
        for (const dependent of dependents.get(completedId)) {
          remaining.set(
            dependent,
            remaining.get(dependent) - 1
          );

          if (remaining.get(dependent) === 0) {
            next.push(dependent);
          }
        }
      }

      wave = next;
    }

    return waves;
  }

  criticalPath() {
    const order = this.topologicalOrder();
    const earliestStart = new Map();
    const earliestFinish = new Map();

    for (const id of order) {
      const task = this.tasks.get(id);

      const start =
        task.dependencies.size === 0
          ? 0
          : Math.max(
              ...[...task.dependencies].map(
                dependency => earliestFinish.get(dependency)
              )
            );

      earliestStart.set(id, start);
      earliestFinish.set(id, start + task.duration);
    }

    const projectDuration =
      order.length === 0
        ? 0
        : Math.max(...order.map(id => earliestFinish.get(id)));

    const latestFinish = new Map(
      order.map(id => [id, projectDuration])
    );
    const latestStart = new Map();

    const dependents = new Map(
      [...this.tasks.keys()].map(id => [id, []])
    );

    for (const task of this.tasks.values()) {
      for (const dependency of task.dependencies) {
        dependents.get(dependency).push(task.id);
      }
    }

    for (const id of [...order].reverse()) {
      const task = this.tasks.get(id);
      const children = dependents.get(id);

      if (children.length > 0) {
        latestFinish.set(
          id,
          Math.min(
            ...children.map(child => latestStart.get(child))
          )
        );
      }

      latestStart.set(
        id,
        latestFinish.get(id) - task.duration
      );
    }

    const slack = new Map();

    for (const id of order) {
      slack.set(
        id,
        latestStart.get(id) - earliestStart.get(id)
      );
    }

    return {
      projectDuration,
      earliestStart,
      earliestFinish,
      latestStart,
      latestFinish,
      slack,
      criticalTasks: order.filter(id => slack.get(id) === 0)
    };
  }

  async simulateTask(id, { shouldFail = false, reason = "" } = {}) {
    this.markInProgress(id);

    // setTimeout makes the dependency engine event-driven instead of
    // pretending that all project work completes synchronously.
    await new Promise(resolve => {
      setTimeout(resolve, this.tasks.get(id).duration * 20);
    });

    if (shouldFail) {
      this.markFailed(id, reason || "Simulated execution failure.");
      return false;
    }

    this.markCompleted(id);
    return true;
  }

  async runAvailableTasks({ concurrency = 2, failureTask = null } = {}) {
    if (!Number.isInteger(concurrency) || concurrency < 1) {
      throw new DependencyError(
        "Concurrency must be a positive integer."
      );
    }

    while (true) {
      const available = this.readyTasks();

      if (available.length === 0) {
        break;
      }

      const batch = available.slice(0, concurrency);

      await Promise.all(
        batch.map(task =>
          this.simulateTask(task.id, {
            shouldFail: task.id === failureTask,
            reason: `Simulated failure in ${task.name}`
          })
        )
      );

      this.propagateBlockedTasks();
    }

    return [...this.tasks.values()];
  }

  toJSON() {
    return {
      project: this.name,
      tasks: [...this.tasks.values()].map(task => ({
        id: task.id,
        name: task.name,
        duration: task.duration,
        dependencies: [...task.dependencies].sort(),
        owner: task.owner,
        priority: task.priority,
        status: task.status,
        failureReason: task.failureReason
      }))
    };
  }
}

function buildReleaseProject() {
  const project = new Project("Payments Platform Release");

  project.addTask({
    id: "REQ",
    name: "Approve payment requirements",
    duration: 2,
    owner: "product",
    priority: "critical"
  });

  project.addTask({
    id: "DESIGN",
    name: "Finalize payment service design",
    duration: 3,
    dependencies: ["REQ"],
    owner: "architecture",
    priority: "critical"
  });

  project.addTask({
    id: "DB",
    name: "Create transaction schema",
    duration: 3,
    dependencies: ["DESIGN"],
    owner: "backend",
    priority: "high"
  });

  project.addTask({
    id: "API",
    name: "Implement payment API",
    duration: 5,
    dependencies: ["DB", "DESIGN"],
    owner: "backend",
    priority: "critical"
  });

  project.addTask({
    id: "WEBHOOK",
    name: "Implement payment webhook handling",
    duration: 4,
    dependencies: ["API"],
    owner: "backend",
    priority: "high"
  });

  project.addTask({
    id: "CHECKOUT",
    name: "Integrate checkout interface",
    duration: 4,
    dependencies: ["REQ"],
    owner: "frontend",
    priority: "high"
  });

  project.addTask({
    id: "OBS",
    name: "Configure transaction monitoring",
    duration: 2,
    dependencies: ["DESIGN"],
    owner: "platform",
    priority: "normal"
  });

  project.addTask({
    id: "INTEGRATION",
    name: "Validate checkout and payment integration",
    duration: 3,
    dependencies: ["WEBHOOK", "CHECKOUT", "OBS"],
    owner: "qa",
    priority: "critical"
  });

  project.addTask({
    id: "SECURITY",
    name: "Perform payment security verification",
    duration: 3,
    dependencies: ["API", "OBS"],
    owner: "security",
    priority: "critical"
  });

  project.addTask({
    id: "RELEASE",
    name: "Release payment capability",
    duration: 1,
    dependencies: ["INTEGRATION", "SECURITY"],
    owner: "release",
    priority: "critical"
  });

  return project;
}

function attachEventLogging(project) {
  project.on("taskStarted", task => {
    console.log(`[STARTED]  ${task.id} - ${task.name}`);
  });

  project.on("taskCompleted", task => {
    console.log(`[COMPLETED] ${task.id} - ${task.name}`);
  });

  project.on("taskFailed", ({ task, reason }) => {
    console.log(`[FAILED]   ${task.id} - ${reason}`);
  });

  project.on("taskBlocked", task => {
    console.log(`[BLOCKED]  ${task.id} - ${task.name}`);
  });
}

function printGraph(project) {
  console.log("\n=== Dependency Map ===");

  for (const id of project.topologicalOrder()) {
    const task = project.tasks.get(id);
    const dependencies = [...task.dependencies].sort();

    console.log(
      `${id.padEnd(12)} | ` +
      `${task.name.padEnd(42)} | ` +
      `depends on: ${dependencies.join(", ") || "none"}`
    );
  }
}

function printWaves(project) {
  console.log("\n=== Parallel Execution Waves ===");

  project.executionWaves().forEach((wave, index) => {
    console.log(`Wave ${index + 1}: ${wave.join(", ")}`);
  });
}

function printCriticalPath(project) {
  const analysis = project.criticalPath();

  console.log("\n=== Critical Path ===");
  console.log(`Minimum duration: ${analysis.projectDuration}`);

  for (const id of project.topologicalOrder()) {
    console.log(
      `${id.padEnd(12)} ` +
      `ES=${String(analysis.earliestStart.get(id)).padStart(2)} ` +
      `EF=${String(analysis.earliestFinish.get(id)).padStart(2)} ` +
      `LS=${String(analysis.latestStart.get(id)).padStart(2)} ` +
      `LF=${String(analysis.latestFinish.get(id)).padStart(2)} ` +
      `Slack=${String(analysis.slack.get(id)).padStart(2)}`
    );
  }

  console.log(
    `Critical tasks: ${analysis.criticalTasks.join(" -> ")}`
  );
}

async function demonstrateFailurePropagation() {
  console.log("\n=== Failure Propagation ===");

  const project = buildReleaseProject();
  attachEventLogging(project);

  await project.runAvailableTasks({
    concurrency: 3,
    failureTask: "API"
  });

  console.log("\nFinal statuses:");

  for (const task of project.tasks.values()) {
    console.log(
      `${task.id.padEnd(12)} ${task.status.padEnd(12)} ${task.name}`
    );
  }
}

async function demonstrateSuccessfulExecution() {
  console.log("\n=== Successful Event-Driven Execution ===");

  const project = buildReleaseProject();
  attachEventLogging(project);

  await project.runAvailableTasks({
    concurrency: 3
  });

  const incomplete = [...project.tasks.values()].filter(
    task => task.status !== TaskStatus.COMPLETED
  );

  console.log(
    incomplete.length === 0
      ? "All dependency-constrained tasks completed."
      : `Incomplete tasks: ${incomplete.map(task => task.id).join(", ")}`
  );
}

function demonstrateValidation() {
  console.log("\n=== Dependency Validation ===");

  const project = new Project("Validation Examples");

  project.addTask({
    id: "A",
    name: "Prepare architecture",
    duration: 1
  });

  try {
    project.addTask({
      id: "B",
      name: "Build service",
      duration: 1,
      dependencies: ["UNKNOWN"]
    });
  } catch (error) {
    console.log(`Missing-reference rejection: ${error.message}`);
  }

  project.addTask({
    id: "B",
    name: "Build service",
    duration: 1,
    dependencies: ["A"]
  });

  // Deliberately corrupt the in-memory graph to demonstrate why validation
  // belongs at the graph level and should also be run before scheduling.
  project.tasks.get("A").dependencies.add("B");

  try {
    project.validate();
  } catch (error) {
    console.log(`Cycle rejection: ${error.message}`);
  }
}

async function exportPlan(project) {
  const path = "project-dependencies.json";

  await fs.writeFile(
    path,
    JSON.stringify(project.toJSON(), null, 2),
    "utf8"
  );

  console.log(`\nDependency plan written to ${path}`);
}

async function main() {
  console.log("=".repeat(76));
  console.log("PROJECT DEPENDENCIES: UNDERSTANDING TASK DEPENDENCIES");
  console.log("=".repeat(76));

  const project = buildReleaseProject();

  printGraph(project);

  console.log("\nInitially ready:");
  console.log(project.readyTasks().map(task => task.id).join(", "));

  printWaves(project);
  printCriticalPath(project);
  demonstrateValidation();

  await demonstrateFailurePropagation();
  await demonstrateSuccessfulExecution();

  await exportPlan(project);

  console.log("\nDependency modeling rules demonstrated:");
  console.log(
    "- A dependent task becomes ready only after every prerequisite completes."
  );
  console.log(
    "- A failed prerequisite propagates a blocked state to dependent work."
  );
  console.log(
    "- Independent tasks may execute concurrently when resource capacity permits."
  );
  console.log(
    "- A directed cycle prevents a valid dependency-respecting schedule."
  );
  console.log(
    "- Critical-path analysis identifies tasks with zero scheduling slack."
  );
}

main().catch(error => {
  console.error(`Fatal dependency-engine error: ${error.message}`);
  process.exitCode = 1;
});
