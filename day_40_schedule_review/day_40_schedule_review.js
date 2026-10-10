/**
 * Schedule Review Workbench
 *
 * This Node.js program models a schedule-review workflow using event-driven
 * state changes, dependency validation, resource analysis, progress variance,
 * and policy evaluation.
 *
 * It intentionally treats schedule calculation, review evidence, and the
 * review decision as separate concerns.
 */

"use strict";

const { EventEmitter } = require("node:events");
const fs = require("node:fs");

const REVIEW_DATE = "2026-10-12";

function parseDate(value) {
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value) {
    throw new Error(`Invalid ISO date: ${value}`);
  }
  return date;
}

function dateText(date) {
  return date.toISOString().slice(0, 10);
}

function addDays(date, days) {
  const result = new Date(date.getTime());
  result.setUTCDate(result.getUTCDate() + days);
  return result;
}

function inclusiveDays(start, end) {
  return Math.floor((end.getTime() - start.getTime()) / 86400000) + 1;
}

class ScheduleTask {
  constructor({
    id,
    title,
    start,
    end,
    owner,
    dependencies = [],
    status = "planned",
    progress = 0,
    plannedHours = 0,
    priority = "normal"
  }) {
    if (!id || !title || !owner) {
      throw new Error("Task requires id, title, and owner.");
    }

    this.id = id;
    this.title = title;
    this.start = parseDate(start);
    this.end = parseDate(end);
    this.owner = owner;
    this.dependencies = [...dependencies];
    this.status = status;
    this.progress = progress;
    this.plannedHours = plannedHours;
    this.priority = priority;

    if (this.end < this.start) {
      throw new Error(`Task ${id} has an invalid date range.`);
    }

    if (progress < 0 || progress > 100) {
      throw new Error(`Task ${id} has invalid progress.`);
    }

    if (plannedHours < 0) {
      throw new Error(`Task ${id} has negative planned hours.`);
    }
  }

  get durationDays() {
    return inclusiveDays(this.start, this.end);
  }

  overlaps(other) {
    return this.start <= other.end && other.start <= this.end;
  }
}

class ScheduleRepository extends EventEmitter {
  constructor(tasks = []) {
    super();
    this.tasks = new Map();

    for (const task of tasks) {
      this.add(task);
    }
  }

  add(task) {
    if (this.tasks.has(task.id)) {
      throw new Error(`Duplicate task ID: ${task.id}`);
    }

    this.tasks.set(task.id, task);
    this.emit("taskAdded", task);
  }

  get(id) {
    const task = this.tasks.get(id);
    if (!task) {
      throw new Error(`Task ${id} does not exist.`);
    }
    return task;
  }

  values() {
    return [...this.tasks.values()];
  }

  updateProgress(id, progress) {
    const task = this.get(id);

    if (progress < 0 || progress > 100) {
      throw new Error("Progress must remain between 0 and 100.");
    }

    task.progress = progress;

    if (progress === 100) {
      task.status = "complete";
    } else if (progress > 0) {
      task.status = "in_progress";
    }

    this.emit("progressChanged", {
      taskId: id,
      progress,
      status: task.status
    });
  }
}

class ScheduleAnalyzer {
  constructor(repository) {
    this.repository = repository;
  }

  dependencyIssues() {
    const issues = [];

    for (const task of this.repository.values()) {
      for (const dependencyId of task.dependencies) {
        const dependency = this.repository.tasks.get(dependencyId);

        if (!dependency) {
          issues.push({
            taskId: task.id,
            message: `Missing dependency ${dependencyId}`
          });
          continue;
        }

        if (dependency.end > task.start) {
          issues.push({
            taskId: task.id,
            message:
              `Dependency ${dependencyId} ends ${dateText(dependency.end)}, ` +
              `after task starts ${dateText(task.start)}`
          });
        }
      }
    }

    return issues;
  }

  dependencyCycle() {
    const visiting = new Set();
    const visited = new Set();
    const path = [];

    const visit = (id) => {
      if (visiting.has(id)) {
        const index = path.indexOf(id);
        return [...path.slice(index), id];
      }

      if (visited.has(id)) {
        return null;
      }

      visiting.add(id);
      path.push(id);

      const task = this.repository.tasks.get(id);
      for (const dependencyId of task.dependencies) {
        if (this.repository.tasks.has(dependencyId)) {
          const cycle = visit(dependencyId);
          if (cycle) {
            return cycle;
          }
        }
      }

      path.pop();
      visiting.delete(id);
      visited.add(id);
      return null;
    };

    for (const task of this.repository.values()) {
      const cycle = visit(task.id);
      if (cycle) {
        return cycle;
      }
    }

    return null;
  }

  resourceConflicts() {
    const byOwner = new Map();

    for (const task of this.repository.values()) {
      if (!byOwner.has(task.owner)) {
        byOwner.set(task.owner, []);
      }
      byOwner.get(task.owner).push(task);
    }

    const conflicts = [];

    for (const [owner, tasks] of byOwner.entries()) {
      tasks.sort((a, b) => a.start - b.start);

      for (let i = 0; i < tasks.length; i += 1) {
        for (let j = i + 1; j < tasks.length; j += 1) {
          if (tasks[j].start > tasks[i].end) {
            break;
          }

          if (tasks[i].overlaps(tasks[j])) {
            conflicts.push({
              owner,
              first: tasks[i].id,
              second: tasks[j].id,
              start: new Date(Math.max(tasks[i].start, tasks[j].start)),
              end: new Date(Math.min(tasks[i].end, tasks[j].end))
            });
          }
        }
      }
    }

    return conflicts;
  }

  capacityViolations(capacity) {
    const workload = new Map();

    for (const task of this.repository.values()) {
      workload.set(
        task.owner,
        (workload.get(task.owner) || 0) + task.plannedHours
      );
    }

    return [...workload.entries()]
      .filter(([owner, hours]) => capacity[owner] !== undefined && hours > capacity[owner])
      .map(([owner, hours]) => ({
        owner,
        plannedHours: hours,
        capacity: capacity[owner],
        excess: hours - capacity[owner]
      }));
  }

  progressVariance(reviewDate) {
    const review = parseDate(reviewDate);

    return this.repository.values().map((task) => {
      let expected;

      if (review < task.start) {
        expected = 0;
      } else if (review >= task.end) {
        expected = 100;
      } else {
        const elapsed = inclusiveDays(task.start, review);
        expected = (elapsed / task.durationDays) * 100;
      }

      return {
        taskId: task.id,
        expected,
        actual: task.progress,
        variance: task.progress - expected
      };
    });
  }

  longestPath() {
    const memo = new Map();

    const longest = (id) => {
      if (memo.has(id)) {
        return memo.get(id);
      }

      const task = this.repository.get(id);

      if (task.dependencies.length === 0) {
        const result = {
          duration: task.durationDays,
          path: [id]
        };
        memo.set(id, result);
        return result;
      }

      let best = { duration: 0, path: [] };

      for (const dependencyId of task.dependencies) {
        if (!this.repository.tasks.has(dependencyId)) {
          continue;
        }

        const candidate = longest(dependencyId);
        if (candidate.duration > best.duration) {
          best = candidate;
        }
      }

      const result = {
        duration: best.duration + task.durationDays,
        path: [...best.path, id]
      };

      memo.set(id, result);
      return result;
    };

    const results = this.repository.values().map((task) => longest(task.id));
    return results.reduce((best, current) =>
      current.duration > best.duration ? current : best
    );
  }
}

class ReviewPolicy {
  constructor({
    maximumResourceConflicts = 0,
    maximumCapacityExcess = 0,
    requireNoDependencyIssues = true,
    requireNoCycle = true
  } = {}) {
    this.maximumResourceConflicts = maximumResourceConflicts;
    this.maximumCapacityExcess = maximumCapacityExcess;
    this.requireNoDependencyIssues = requireNoDependencyIssues;
    this.requireNoCycle = requireNoCycle;
  }

  evaluate(evidence) {
    const failures = [];

    if (
      this.requireNoDependencyIssues &&
      evidence.dependencyIssues.length > 0
    ) {
      failures.push("Dependency timing or reference errors exist.");
    }

    if (this.requireNoCycle && evidence.cycle) {
      failures.push(`Dependency cycle detected: ${evidence.cycle.join(" -> ")}`);
    }

    if (evidence.resourceConflicts.length > this.maximumResourceConflicts) {
      failures.push("Resource overlap exceeds review policy.");
    }

    if (
      evidence.capacityViolations.some(
        (item) => item.excess > this.maximumCapacityExcess
      )
    ) {
      failures.push("Planned workload exceeds resource capacity.");
    }

    if (failures.length === 0) {
      return {
        decision: "accepted",
        failures
      };
    }

    return {
      decision: "revise",
      failures
    };
  }
}

class ScheduleReviewSession extends EventEmitter {
  constructor(repository, analyzer, policy, capacity) {
    super();
    this.repository = repository;
    this.analyzer = analyzer;
    this.policy = policy;
    this.capacity = capacity;
    this.lastReview = null;
  }

  run(reviewDate) {
    const evidence = {
      reviewDate,
      dependencyIssues: this.analyzer.dependencyIssues(),
      cycle: this.analyzer.dependencyCycle(),
      resourceConflicts: this.analyzer.resourceConflicts(),
      capacityViolations: this.analyzer.capacityViolations(this.capacity),
      progressVariance: this.analyzer.progressVariance(reviewDate),
      criticalPath: this.analyzer.longestPath()
    };

    const decision = this.policy.evaluate(evidence);

    this.lastReview = {
      evidence,
      decision
    };

    this.emit("reviewCompleted", this.lastReview);
    return this.lastReview;
  }
}

function createSchedule() {
  return [
    new ScheduleTask({
      id: "REQ",
      title: "Requirements baseline",
      start: "2026-10-01",
      end: "2026-10-03",
      owner: "Asha",
      progress: 100,
      status: "complete",
      plannedHours: 18,
      priority: "high"
    }),
    new ScheduleTask({
      id: "ARCH",
      title: "Architecture review",
      start: "2026-10-04",
      end: "2026-10-06",
      owner: "Ravi",
      dependencies: ["REQ"],
      progress: 100,
      status: "complete",
      plannedHours: 20,
      priority: "high"
    }),
    new ScheduleTask({
      id: "API",
      title: "API implementation",
      start: "2026-10-07",
      end: "2026-10-12",
      owner: "Ravi",
      dependencies: ["ARCH"],
      progress: 55,
      status: "in_progress",
      plannedHours: 36,
      priority: "high"
    }),
    new ScheduleTask({
      id: "UI",
      title: "Schedule dashboard",
      start: "2026-10-10",
      end: "2026-10-14",
      owner: "Meera",
      dependencies: ["ARCH"],
      progress: 40,
      status: "in_progress",
      plannedHours: 30
    }),
    new ScheduleTask({
      id: "TEST",
      title: "Integration testing",
      start: "2026-10-13",
      end: "2026-10-16",
      owner: "Asha",
      dependencies: ["API", "UI"],
      plannedHours: 28
    }),
    new ScheduleTask({
      id: "SEC",
      title: "Security verification",
      start: "2026-10-15",
      end: "2026-10-17",
      owner: "Ravi",
      dependencies: ["TEST"],
      plannedHours: 18,
      priority: "high"
    }),
    new ScheduleTask({
      id: "REL",
      title: "Production release",
      start: "2026-10-19",
      end: "2026-10-19",
      owner: "Asha",
      dependencies: ["SEC"],
      plannedHours: 8,
      priority: "high"
    })
  ];
}

function printReview(review) {
  const { evidence, decision } = review;

  console.log("\nSCHEDULE REVIEW");
  console.log("================");

  console.log(`Review date: ${evidence.reviewDate}`);
  console.log(`Decision: ${decision.decision.toUpperCase()}`);

  console.log("\nCritical path:");
  console.log(
    `${evidence.criticalPath.path.join(" -> ")} ` +
    `(${evidence.criticalPath.duration} calendar days)`
  );

  console.log("\nDependency findings:");
  if (evidence.dependencyIssues.length === 0) {
    console.log("None");
  } else {
    for (const issue of evidence.dependencyIssues) {
      console.log(`${issue.taskId}: ${issue.message}`);
    }
  }

  console.log("\nResource conflicts:");
  if (evidence.resourceConflicts.length === 0) {
    console.log("None");
  } else {
    for (const conflict of evidence.resourceConflicts) {
      console.log(
        `${conflict.owner}: ${conflict.first} overlaps ${conflict.second} ` +
        `from ${dateText(conflict.start)} to ${dateText(conflict.end)}`
      );
    }
  }

  console.log("\nCapacity findings:");
  if (evidence.capacityViolations.length === 0) {
    console.log("None");
  } else {
    for (const violation of evidence.capacityViolations) {
      console.log(
        `${violation.owner}: ${violation.plannedHours} planned hours, ` +
        `${violation.capacity} available, ${violation.excess} excess`
      );
    }
  }

  console.log("\nProgress variance:");
  for (const item of evidence.progressVariance) {
    console.log(
      `${item.taskId}: expected=${item.expected.toFixed(1)}%, ` +
      `actual=${item.actual.toFixed(1)}%, variance=${item.variance.toFixed(1)}%`
    );
  }

  console.log("\nPolicy findings:");
  if (decision.failures.length === 0) {
    console.log("Schedule satisfies the configured review policy.");
  } else {
    for (const failure of decision.failures) {
      console.log(failure);
    }
  }
}

function saveReviewEvidence(review, filename) {
  fs.writeFileSync(
    filename,
    JSON.stringify(review, (key, value) => {
      if (value instanceof Date) {
        return value.toISOString();
      }
      return value;
    }, 2),
    "utf8"
  );
}

function main() {
  const repository = new ScheduleRepository(createSchedule());

  repository.on("taskAdded", (task) => {
    console.log(`Loaded schedule task: ${task.id}`);
  });

  repository.on("progressChanged", (event) => {
    console.log(
      `Progress event: ${event.taskId} -> ${event.progress}% (${event.status})`
    );
  });

  repository.on("reviewCompleted", (review) => {
    console.log(`Review event emitted: ${review.decision.decision}`);
  });

  const analyzer = new ScheduleAnalyzer(repository);

  const policy = new ReviewPolicy({
    maximumResourceConflicts: 0,
    maximumCapacityExcess: 0,
    requireNoDependencyIssues: true,
    requireNoCycle: true
  });

  const capacity = {
    Asha: 70,
    Ravi: 65,
    Meera: 40
  };

  const session = new ScheduleReviewSession(
    repository,
    analyzer,
    policy,
    capacity
  );

  repository.updateProgress("API", 62);

  const review = session.run(REVIEW_DATE);
  printReview(review);
  saveReviewEvidence(review, "schedule-review-evidence.json");

  console.log("\nReview evidence written to schedule-review-evidence.json");

  const malformed = new ScheduleTask({
    id: "DEMO",
    title: "Validation example",
    start: "2026-10-20",
    end: "2026-10-21",
    owner: "Asha",
    plannedHours: 4
  });

  console.log(
    `\nValidation example accepted: ${malformed.id}, ` +
    `${malformed.durationDays} day duration`
  );
}

main();
