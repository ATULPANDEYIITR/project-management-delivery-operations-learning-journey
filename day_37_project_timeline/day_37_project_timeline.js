"use strict";

/*
 * Project Timeline Engine
 *
 * This Node.js program models a project schedule as a dependency graph.
 * It focuses on timeline creation rather than treating a schedule as only
 * a collection of dates. Tasks have owners, dependencies, progress,
 * priorities, milestones, and status. The program also demonstrates
 * event-driven schedule changes, validation, critical-path calculation,
 * risk detection, and JSON export.
 */

const fs = require("node:fs/promises");
const path = require("node:path");

const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

function parseDate(value) {
  if (!DATE_PATTERN.test(value)) {
    throw new Error(`Invalid date '${value}'. Expected YYYY-MM-DD.`);
  }

  const [year, month, day] = value.split("-").map(Number);
  const result = new Date(Date.UTC(year, month - 1, day));

  if (
    result.getUTCFullYear() !== year ||
    result.getUTCMonth() !== month - 1 ||
    result.getUTCDate() !== day
  ) {
    throw new Error(`Invalid calendar date '${value}'.`);
  }

  return result;
}

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function daysBetween(start, end) {
  const milliseconds = end.getTime() - start.getTime();
  return Math.floor(milliseconds / 86400000);
}

function calendarDuration(start, end) {
  return daysBetween(start, end) + 1;
}

function addCalendarDays(start, numberOfDays) {
  const result = new Date(start.getTime());
  result.setUTCDate(result.getUTCDate() + numberOfDays);
  return result;
}

class TimelineTask {
  constructor({
    id,
    name,
    start,
    end,
    owner,
    category,
    dependencies = [],
    progress = 0,
    priority = "medium"
  }) {
    this.id = id;
    this.name = name;
    this.start = parseDate(start);
    this.end = parseDate(end);
    this.owner = owner;
    this.category = category;
    this.dependencies = [...dependencies];
    this.progress = progress;
    this.priority = priority;
    this.completed = progress === 100;

    this.validate();
  }

  validate() {
    if (!this.id || !this.name) {
      throw new Error("Every task requires an ID and name.");
    }

    if (this.end < this.start) {
      throw new Error(`Task ${this.id} ends before it starts.`);
    }

    if (!Number.isInteger(this.progress) || this.progress < 0 || this.progress > 100) {
      throw new Error(`Task ${this.id} progress must be an integer from 0 to 100.`);
    }

    if (!["low", "medium", "high", "critical"].includes(this.priority)) {
      throw new Error(`Unsupported priority '${this.priority}'.`);
    }

    if (this.dependencies.includes(this.id)) {
      throw new Error(`Task ${this.id} cannot depend on itself.`);
    }
  }

  duration() {
    return calendarDuration(this.start, this.end);
  }
}

class ProjectTimeline {
  constructor(name) {
    this.name = name;
    this.tasks = new Map();
    this.milestones = [];
    this.listeners = new Map();
  }

  on(eventName, listener) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, []);
    }

    this.listeners.get(eventName).push(listener);
  }

  emit(eventName, payload) {
    for (const listener of this.listeners.get(eventName) ?? []) {
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
    const task = this.tasks.get(taskId);

    if (!task) {
      throw new Error(`Unknown task: ${taskId}`);
    }

    if (!Number.isInteger(progress) || progress < 0 || progress > 100) {
      throw new Error("Progress must be an integer from 0 to 100.");
    }

    task.progress = progress;
    task.completed = progress === 100;

    this.emit("progressChanged", {
      taskId,
      progress,
      completed: task.completed
    });
  }

  addMilestone(name, dueDate, description = "") {
    const milestone = {
      name,
      dueDate: parseDate(dueDate),
      description,
      completed: false
    };

    this.milestones.push(milestone);
    this.emit("milestoneAdded", milestone);
  }

  validateDependencies() {
    const errors = [];

    for (const task of this.tasks.values()) {
      for (const dependencyId of task.dependencies) {
        const dependency = this.tasks.get(dependencyId);

        if (!dependency) {
          errors.push(
            `${task.id} references missing dependency ${dependencyId}.`
          );
          continue;
        }

        if (dependency.end >= task.start) {
          errors.push(
            `${task.id} starts on ${formatDate(task.start)} before ` +
            `${dependency.id} finishes on ${formatDate(dependency.end)}.`
          );
        }
      }
    }

    return errors;
  }

  hasCycle() {
    const visiting = new Set();
    const visited = new Set();

    const visit = (taskId) => {
      if (visiting.has(taskId)) {
        return true;
      }

      if (visited.has(taskId)) {
        return false;
      }

      visiting.add(taskId);

      const task = this.tasks.get(taskId);
      for (const dependencyId of task.dependencies) {
        if (this.tasks.has(dependencyId) && visit(dependencyId)) {
          return true;
        }
      }

      visiting.delete(taskId);
      visited.add(taskId);
      return false;
    };

    for (const taskId of this.tasks.keys()) {
      if (visit(taskId)) {
        return true;
      }
    }

    return false;
  }

  criticalPath() {
    const errors = this.validateDependencies();

    if (errors.length > 0) {
      throw new Error(
        `Cannot calculate critical path:\n${errors.join("\n")}`
      );
    }

    if (this.hasCycle()) {
      throw new Error("Cannot calculate critical path for a cyclic timeline.");
    }

    const tasks = [...this.tasks.values()].sort(
      (a, b) => a.end - b.end
    );

    const longestFinish = new Map();
    const previous = new Map();

    for (const task of tasks) {
      let bestFinish = 0;
      let bestPrevious = null;

      for (const dependencyId of task.dependencies) {
        const candidate = longestFinish.get(dependencyId) ?? 0;

        if (candidate > bestFinish) {
          bestFinish = candidate;
          bestPrevious = dependencyId;
        }
      }

      longestFinish.set(
        task.id,
        bestFinish + task.duration()
      );
      previous.set(task.id, bestPrevious);
    }

    let finalTask = null;
    let finalDuration = -Infinity;

    for (const [taskId, duration] of longestFinish) {
      if (duration > finalDuration) {
        finalTask = taskId;
        finalDuration = duration;
      }
    }

    const path = [];
    let current = finalTask;

    while (current !== null) {
      path.push(current);
      current = previous.get(current) ?? null;
    }

    path.reverse();

    return {
      path,
      duration: finalDuration
    };
  }

  weightedProgress() {
    let totalWeight = 0;
    let completedWeight = 0;

    for (const task of this.tasks.values()) {
      const weight = task.duration();
      totalWeight += weight;
      completedWeight += weight * task.progress;
    }

    return totalWeight === 0 ? 0 : completedWeight / totalWeight;
  }

  risks(asOf) {
    const currentDate = parseDate(asOf);
    const risks = [];

    for (const task of this.tasks.values()) {
      if (task.end < currentDate && task.progress < 100) {
        risks.push({
          type: "overdue",
          taskId: task.id,
          message: `${task.name} is overdue at ${task.progress}% progress.`
        });
      }

      if (
        task.start <= currentDate &&
        currentDate <= task.end &&
        task.progress === 0
      ) {
        risks.push({
          type: "not_started",
          taskId: task.id,
          message: `${task.name} is scheduled but has not started.`
        });
      }

      if (
        ["high", "critical"].includes(task.priority) &&
        task.progress < 50
      ) {
        risks.push({
          type: "progress",
          taskId: task.id,
          message: `${task.name} has ${task.progress}% progress with ${task.priority} priority.`
        });
      }
    }

    for (const dependencyError of this.validateDependencies()) {
      risks.push({
        type: "dependency",
        taskId: null,
        message: dependencyError
      });
    }

    return risks;
  }

  snapshot() {
    return {
      project: this.name,
      tasks: [...this.tasks.values()].map((task) => ({
        id: task.id,
        name: task.name,
        start: formatDate(task.start),
        end: formatDate(task.end),
        owner: task.owner,
        category: task.category,
        dependencies: [...task.dependencies],
        progress: task.progress,
        priority: task.priority,
        completed: task.completed
      })),
      milestones: this.milestones.map((milestone) => ({
        name: milestone.name,
        dueDate: formatDate(milestone.dueDate),
        description: milestone.description,
        completed: milestone.completed
      }))
    };
  }
}

function createTimeline() {
  const timeline = new ProjectTimeline("Operations Analytics Platform");

  timeline.addTask(
    new TimelineTask({
      id: "T01",
      name: "Project kickoff",
      start: "2026-10-12",
      end: "2026-10-13",
      owner: "Project Manager",
      category: "Initiation",
      progress: 100,
      priority: "high"
    })
  );

  timeline.addTask(
    new TimelineTask({
      id: "T02",
      name: "Requirements workshops",
      start: "2026-10-14",
      end: "2026-10-20",
      owner: "Business Analyst",
      category: "Requirements",
      dependencies: ["T01"],
      progress: 75,
      priority: "high"
    })
  );

  timeline.addTask(
    new TimelineTask({
      id: "T03",
      name: "Data architecture",
      start: "2026-10-21",
      end: "2026-10-28",
      owner: "Data Architect",
      category: "Architecture",
      dependencies: ["T02"],
      progress: 35,
      priority: "high"
    })
  );

  timeline.addTask(
    new TimelineTask({
      id: "T04",
      name: "Analytics pipeline",
      start: "2026-10-29",
      end: "2026-11-06",
      owner: "Data Engineer",
      category: "Engineering",
      dependencies: ["T03"],
      progress: 10,
      priority: "critical"
    })
  );

  timeline.addTask(
    new TimelineTask({
      id: "T05",
      name: "Operations dashboard",
      start: "2026-10-29",
      end: "2026-11-09",
      owner: "Application Engineer",
      category: "Development",
      dependencies: ["T03"],
      progress: 10,
      priority: "medium"
    })
  );

  timeline.addTask(
    new TimelineTask({
      id: "T06",
      name: "User acceptance testing",
      start: "2026-11-10",
      end: "2026-11-16",
      owner: "QA Lead",
      category: "Testing",
      dependencies: ["T04", "T05"],
      progress: 0,
      priority: "high"
    })
  );

  timeline.addTask(
    new TimelineTask({
      id: "T07",
      name: "Production handover",
      start: "2026-11-17",
      end: "2026-11-19",
      owner: "Release Manager",
      category: "Deployment",
      dependencies: ["T06"],
      progress: 0,
      priority: "critical"
    })
  );

  timeline.addMilestone(
    "Requirements baseline",
    "2026-10-20",
    "Stakeholders approve the scope baseline."
  );

  timeline.addMilestone(
    "Prototype ready",
    "2026-11-06",
    "Core analytics pipeline is available for testing."
  );

  timeline.addMilestone(
    "Production release",
    "2026-11-19",
    "Operational handover is complete."
  );

  return timeline;
}

async function main() {
  const timeline = createTimeline();

  timeline.on("taskAdded", (task) => {
    console.log(`EVENT taskAdded: ${task.id} - ${task.name}`);
  });

  timeline.on("progressChanged", (event) => {
    console.log(
      `EVENT progressChanged: ${event.taskId} -> ${event.progress}%`
    );
  });

  timeline.updateProgress("T04", 25);

  console.log("\nPROJECT TIMELINE");
  console.table(timeline.snapshot().tasks);

  console.log("\nCRITICAL PATH");
  const critical = timeline.criticalPath();
  console.log(`Path: ${critical.path.join(" -> ")}`);
  console.log(`Duration: ${critical.duration} calendar days`);

  console.log("\nPROJECT PROGRESS");
  console.log(`${timeline.weightedProgress().toFixed(1)}% weighted progress`);

  console.log("\nSCHEDULE RISKS");
  for (const risk of timeline.risks("2026-11-10")) {
    console.log(`[${risk.type}] ${risk.message}`);
  }

  console.log("\nDEPENDENCY VALIDATION");
  const dependencyErrors = timeline.validateDependencies();
  console.log(
    dependencyErrors.length === 0
      ? "No dependency errors."
      : dependencyErrors.join("\n")
  );

  const outputDirectory = path.join(process.cwd(), "timeline_output");
  await fs.mkdir(outputDirectory, { recursive: true });

  const outputFile = path.join(outputDirectory, "project_timeline.json");

  await fs.writeFile(
    outputFile,
    JSON.stringify(timeline.snapshot(), null, 2),
    "utf8"
  );

  console.log(`\nJSON exported to ${outputFile}`);

  try {
    new TimelineTask({
      id: "INVALID",
      name: "Invalid task",
      start: "2026-12-10",
      end: "2026-12-01",
      owner: "Tester",
      category: "Testing"
    });
  } catch (error) {
    console.log(`\nValidation correctly rejected invalid task: ${error.message}`);
  }
}

main().catch((error) => {
  console.error(`Fatal timeline error: ${error.message}`);
  process.exitCode = 1;
});
