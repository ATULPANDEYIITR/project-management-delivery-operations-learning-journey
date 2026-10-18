"use strict";

/*
 * Resource allocation for a cloud engineering team.
 * Demonstrates event-driven requests, resource compatibility, scheduling,
 * capacity checks, dependency handling, preemption-free reservation,
 * utilization, and transactional plan replacement.
 */

const { EventEmitter } = require("node:events");

class AllocationError extends Error {}

class Resource {
  constructor({ id, type, capacity, hourlyCost = 0, tags = [] }) {
    if (!id || !type) {
      throw new AllocationError("Resource ID and type are required.");
    }
    if (!Number.isFinite(capacity) || capacity <= 0) {
      throw new AllocationError("Capacity must be a positive number.");
    }
    if (!Number.isFinite(hourlyCost) || hourlyCost < 0) {
      throw new AllocationError("Hourly cost must be non-negative.");
    }

    this.id = id;
    this.type = type;
    this.capacity = capacity;
    this.hourlyCost = hourlyCost;
    this.tags = new Set(tags);
    this.reservations = [];
  }

  canRun(task) {
    return (
      task.type === this.type &&
      task.demand <= this.capacity &&
      task.requiredTags.every((tag) => this.tags.has(tag))
    );
  }

  earliestAvailable(start, duration) {
    const reservations = [...this.reservations].sort(
      (a, b) => a.start - b.start
    );

    let candidate = start;
    for (const reservation of reservations) {
      if (candidate + duration <= reservation.start) {
        return candidate;
      }
      if (candidate < reservation.end) {
        candidate = reservation.end;
      }
    }
    return candidate;
  }

  reserve(allocation) {
    const overlaps = this.reservations.some(
      (existing) =>
        allocation.start < existing.end &&
        existing.start < allocation.end
    );
    if (overlaps) {
      throw new AllocationError(
        `Resource ${this.id} already has a reservation in that interval.`
      );
    }

    this.reservations.push(allocation);
  }
}

class Task {
  constructor({
    id,
    name,
    type,
    demand,
    duration,
    priority,
    dependencies = [],
    requiredTags = [],
    deadline = Infinity,
  }) {
    if (!id || !name || !type) {
      throw new AllocationError("Task identity and type are required.");
    }
    if (
      !Number.isFinite(demand) ||
      demand <= 0 ||
      !Number.isFinite(duration) ||
      duration <= 0
    ) {
      throw new AllocationError("Demand and duration must be positive.");
    }
    if (!Number.isFinite(priority) || priority < 0) {
      throw new AllocationError("Priority must be non-negative.");
    }
    if (dependencies.includes(id)) {
      throw new AllocationError("A task cannot depend on itself.");
    }

    this.id = id;
    this.name = name;
    this.type = type;
    this.demand = demand;
    this.duration = duration;
    this.priority = priority;
    this.dependencies = [...new Set(dependencies)];
    this.requiredTags = [...new Set(requiredTags)];
    this.deadline = deadline;
  }
}

class AllocationEngine extends EventEmitter {
  constructor(resources, tasks) {
    super();

    this.resources = new Map(resources.map((resource) => [resource.id, resource]));
    this.tasks = new Map(tasks.map((task) => [task.id, task]));

    if (this.resources.size !== resources.length) {
      throw new AllocationError("Duplicate resource IDs are not allowed.");
    }
    if (this.tasks.size !== tasks.length) {
      throw new AllocationError("Duplicate task IDs are not allowed.");
    }

    this._validateDependencyGraph();
    this.allocations = [];
    this.rejections = new Map();
  }

  _validateDependencyGraph() {
    for (const task of this.tasks.values()) {
      for (const dependency of task.dependencies) {
        if (!this.tasks.has(dependency)) {
          throw new AllocationError(
            `Task ${task.id} depends on unknown task ${dependency}.`
          );
        }
      }
    }

    const visiting = new Set();
    const visited = new Set();

    const visit = (id) => {
      if (visiting.has(id)) {
        throw new AllocationError("Dependency cycle detected.");
      }
      if (visited.has(id)) return;

      visiting.add(id);
      for (const dependency of this.tasks.get(id).dependencies) {
        visit(dependency);
      }
      visiting.delete(id);
      visited.add(id);
    };

    for (const id of this.tasks.keys()) visit(id);
  }

  allocate() {
    // Work on a private copy so a failed planning run does not leave
    // partially committed reservations in the live resource objects.
    const workingResources = [...this.resources.values()].map((resource) => {
      const copy = new Resource({
        id: resource.id,
        type: resource.type,
        capacity: resource.capacity,
        hourlyCost: resource.hourlyCost,
        tags: [...resource.tags],
      });
      copy.reservations = resource.reservations.map((item) => ({ ...item }));
      return copy;
    });
    const workingById = new Map(
      workingResources.map((resource) => [resource.id, resource])
    );

    const allocations = [];
    const rejections = new Map();
    const finishTimes = new Map();
    const pending = new Set(this.tasks.keys());

    while (pending.size) {
      const ready = [...pending]
        .map((id) => this.tasks.get(id))
        .filter((task) =>
          task.dependencies.every(
            (id) => finishTimes.has(id) || rejections.has(id)
          )
        )
        .sort(
          (a, b) =>
            b.priority - a.priority ||
            a.deadline - b.deadline ||
            a.id.localeCompare(b.id)
        );

      if (ready.length === 0) {
        for (const id of pending) {
          rejections.set(id, "Dependency could not be satisfied.");
        }
        break;
      }

      const task = ready[0];
      pending.delete(task.id);

      const failedDependency = task.dependencies.find((id) =>
        rejections.has(id)
      );
      if (failedDependency) {
        rejections.set(
          task.id,
          `Dependency ${failedDependency} was rejected.`
        );
        this.emit("rejected", {
          taskId: task.id,
          reason: rejections.get(task.id),
        });
        continue;
      }

      const dependencyFinish = Math.max(
        0,
        ...task.dependencies.map((id) => finishTimes.get(id))
      );

      const candidates = [...workingResources]
        .filter((resource) => resource.canRun(task))
        .map((resource) => ({
          resource,
          start: resource.earliestAvailable(
            dependencyFinish,
            task.duration
          ),
        }))
        .filter(({ start }) => start + task.duration <= task.deadline)
        .sort(
          (a, b) =>
            a.start - b.start ||
            a.resource.hourlyCost - b.resource.hourlyCost ||
            a.resource.id.localeCompare(b.resource.id)
        );

      if (candidates.length === 0) {
        const reason = "No compatible resource meets the deadline.";
        rejections.set(task.id, reason);
        this.emit("rejected", { taskId: task.id, reason });
        continue;
      }

      const { resource, start } = candidates[0];
      const allocation = Object.freeze({
        taskId: task.id,
        resourceId: resource.id,
        demand: task.demand,
        start,
        end: start + task.duration,
      });

      resource.reserve(allocation);
      allocations.push(allocation);
      finishTimes.set(task.id, allocation.end);

      this.emit("allocated", allocation);
    }

    // Commit the complete plan only after scheduling has finished.
    for (const resource of this.resources.values()) {
      resource.reservations = workingById.get(resource.id).reservations;
    }
    this.allocations = allocations;
    this.rejections = rejections;

    return this.report();
  }

  report() {
    const makespan = Math.max(
      0,
      ...this.allocations.map((allocation) => allocation.end)
    );

    const resourceStats = [...this.resources.values()].map((resource) => {
      const busyHours = this.allocations
        .filter((allocation) => allocation.resourceId === resource.id)
        .reduce(
          (total, allocation) => total + allocation.end - allocation.start,
          0
        );

      return {
        resourceId: resource.id,
        busyHours,
        utilization: makespan ? (busyHours / makespan) * 100 : 0,
      };
    });

    const cost = this.allocations.reduce((total, allocation) => {
      const resource = this.resources.get(allocation.resourceId);
      return (
        total +
        (allocation.end - allocation.start) * resource.hourlyCost
      );
    }, 0);

    return {
      allocations: this.allocations.map((allocation) => ({ ...allocation })),
      rejections: Object.fromEntries(this.rejections),
      resourceStats,
      makespan,
      estimatedCost: cost,
    };
  }
}

function printReport(report) {
  console.table(
    report.allocations.map((allocation) => ({
      task: allocation.taskId,
      resource: allocation.resourceId,
      start: allocation.start,
      end: allocation.end,
      demand: allocation.demand,
    }))
  );
  console.log("Rejected tasks:", report.rejections);
  console.log("Resource utilization:", report.resourceStats);
  console.log("Makespan:", report.makespan);
  console.log("Estimated cost:", report.estimatedCost);
}

function main() {
  const resources = [
    new Resource({
      id: "GPU-1",
      type: "compute",
      capacity: 16,
      hourlyCost: 18,
      tags: ["cuda", "linux"],
    }),
    new Resource({
      id: "CPU-1",
      type: "compute",
      capacity: 8,
      hourlyCost: 6,
      tags: ["linux"],
    }),
    new Resource({
      id: "DB-1",
      type: "database",
      capacity: 10,
      hourlyCost: 13,
      tags: ["postgresql", "backup-enabled"],
    }),
  ];

  const tasks = [
    new Task({
      id: "ETL",
      name: "Transform production data",
      type: "compute",
      demand: 6,
      duration: 2,
      priority: 8,
      requiredTags: ["linux"],
    }),
    new Task({
      id: "TRAIN",
      name: "Train forecasting model",
      type: "compute",
      demand: 14,
      duration: 4,
      priority: 10,
      dependencies: ["ETL"],
      requiredTags: ["cuda"],
      deadline: 9,
    }),
    new Task({
      id: "MIGRATE",
      name: "Migrate analytical database",
      type: "database",
      demand: 8,
      duration: 3,
      priority: 7,
      requiredTags: ["postgresql", "backup-enabled"],
      deadline: 8,
    }),
    new Task({
      id: "REPORT",
      name: "Build reporting dataset",
      type: "compute",
      demand: 4,
      duration: 2,
      priority: 6,
      dependencies: ["TRAIN"],
      requiredTags: ["linux"],
    }),
    new Task({
      id: "OVERSIZED",
      name: "Oversized simulation",
      type: "compute",
      demand: 32,
      duration: 5,
      priority: 2,
    }),
  ];

  const engine = new AllocationEngine(resources, tasks);

  engine.on("allocated", (allocation) => {
    console.log(
      `Allocated ${allocation.taskId} to ${allocation.resourceId}: ` +
        `[${allocation.start}, ${allocation.end})`
    );
  });

  engine.on("rejected", ({ taskId, reason }) => {
    console.log(`Rejected ${taskId}: ${reason}`);
  });

  printReport(engine.allocate());

  // A duplicate scheduling request is prevented by the committed reservations.
  console.log("\nCommitted resource reservations:");
  for (const resource of resources) {
    console.log(resource.id, resource.reservations.length);
  }
}

try {
  main();
} catch (error) {
  console.error("Allocation failed:", error.message);
  process.exitCode = 1;
}
