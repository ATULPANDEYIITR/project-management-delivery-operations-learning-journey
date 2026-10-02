/**
 * Activity Identification
 * -----------------------
 * A self-contained Node.js implementation that models identification of
 * project activities, dependency relationships, work packages, milestones,
 * validation, and event-driven changes to an identified activity register.
 *
 * Run with:
 *   node activity-identification.js
 *
 * No npm dependencies are required.
 */

"use strict";

const ActivityType = Object.freeze({
  TASK: "task",
  MILESTONE: "milestone",
  REVIEW: "review",
  HANDOFF: "handoff",
});

const Priority = Object.freeze({
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  CRITICAL: "critical",
});

class ActivityValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "ActivityValidationError";
  }
}

class Activity {
  constructor({
    id,
    name,
    description,
    type = ActivityType.TASK,
    owner = null,
    durationDays = 1,
    priority = Priority.MEDIUM,
    dependencies = [],
    deliverable = null,
    tags = [],
  }) {
    if (!id || !id.trim()) {
      throw new ActivityValidationError("Activity ID is required.");
    }

    if (!name || !name.trim()) {
      throw new ActivityValidationError("Activity name is required.");
    }

    if (durationDays < 0) {
      throw new ActivityValidationError(
        `Duration cannot be negative for ${id}.`
      );
    }

    if (type === ActivityType.MILESTONE && durationDays !== 0) {
      throw new ActivityValidationError(
        `Milestone ${id} must have zero duration.`
      );
    }

    this.id = id;
    this.name = name;
    this.description = description;
    this.type = type;
    this.owner = owner;
    this.durationDays = durationDays;
    this.priority = priority;
    this.dependencies = new Set(dependencies);
    this.deliverable = deliverable;
    this.tags = new Set(tags);
  }

  normalizedName() {
    return this.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  isActionable() {
    return [
      ActivityType.TASK,
      ActivityType.REVIEW,
      ActivityType.HANDOFF,
    ].includes(this.type);
  }
}

class ActivityRegister {
  constructor() {
    this.activities = new Map();
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

  add(activity) {
    if (this.activities.has(activity.id)) {
      throw new ActivityValidationError(
        `Activity ID ${activity.id} already exists.`
      );
    }

    for (const existing of this.activities.values()) {
      if (this.similarNames(existing, activity)) {
        throw new ActivityValidationError(
          `Activity ${activity.id} appears to duplicate ${existing.id}.`
        );
      }
    }

    this.activities.set(activity.id, activity);
    this.emit("activityAdded", activity);
  }

  similarNames(first, second) {
    const a = new Set(first.normalizedName().split(/\s+/));
    const b = new Set(second.normalizedName().split(/\s+/));

    const intersection = [...a].filter((word) => b.has(word)).length;
    const union = new Set([...a, ...b]).size;

    return union > 0 && intersection / union >= 0.8;
  }

  get(id) {
    const activity = this.activities.get(id);

    if (!activity) {
      throw new ActivityValidationError(`Unknown activity: ${id}`);
    }

    return activity;
  }

  values() {
    return [...this.activities.values()];
  }

  validate() {
    const errors = [];

    for (const activity of this.activities.values()) {
      for (const dependency of activity.dependencies) {
        if (!this.activities.has(dependency)) {
          errors.push(
            `${activity.id} references unknown dependency ${dependency}.`
          );
        }
      }
    }

    if (this.hasCycle()) {
      errors.push("Activity dependency graph contains a cycle.");
    }

    return errors;
  }

  hasCycle() {
    const visiting = new Set();
    const visited = new Set();

    const visit = (id) => {
      if (visiting.has(id)) return true;
      if (visited.has(id)) return false;

      visiting.add(id);

      const activity = this.activities.get(id);

      for (const dependency of activity.dependencies) {
        if (this.activities.has(dependency) && visit(dependency)) {
          return true;
        }
      }

      visiting.delete(id);
      visited.add(id);
      return false;
    };

    for (const id of this.activities.keys()) {
      if (visit(id)) return true;
    }

    return false;
  }
}

class ActivityCandidateExtractor {
  constructor() {
    this.actionVerbs = new Set([
      "analyze",
      "approve",
      "build",
      "configure",
      "design",
      "develop",
      "document",
      "evaluate",
      "implement",
      "inspect",
      "integrate",
      "migrate",
      "prepare",
      "review",
      "test",
      "validate",
      "deploy",
      "train",
      "identify",
      "collect",
      "define",
      "install",
    ]);
  }

  extract(text) {
    return text
      .split(/[.!?]+/)
      .map((sentence) => sentence.trim())
      .filter(Boolean)
      .filter((sentence) => {
        const words = sentence
          .toLowerCase()
          .split(/\s+/)
          .map((word) => word.replace(/[,;:()[\]]/g, ""));

        return words.some((word) => this.actionVerbs.has(word));
      });
  }
}

class ActivityEventLog {
  constructor() {
    this.events = [];
  }

  record(eventName, activity) {
    this.events.push({
      eventName,
      activityId: activity.id,
      activityName: activity.name,
      timestamp: new Date().toISOString(),
    });
  }

  print() {
    console.log("\n=== Event Log ===");

    for (const event of this.events) {
      console.log(
        `${event.timestamp} | ${event.eventName} | ` +
          `${event.activityId} | ${event.activityName}`
      );
    }
  }
}

class ActivityAnalyzer {
  constructor(register) {
    this.register = register;
  }

  withoutOwners() {
    return this.register.values().filter((activity) => !activity.owner);
  }

  withoutDeliverables() {
    return this.register.values().filter(
      (activity) => activity.isActionable() && !activity.deliverable
    );
  }

  highAttentionActivities() {
    return this.register.values().filter(
      (activity) =>
        activity.priority === Priority.HIGH ||
        activity.priority === Priority.CRITICAL ||
        activity.dependencies.size >= 3
    );
  }

  byWorkPackage() {
    const groups = new Map();

    for (const activity of this.register.values()) {
      const packageName = [...activity.tags][0] || "unclassified";

      if (!groups.has(packageName)) {
        groups.set(packageName, []);
      }

      groups.get(packageName).push(activity);
    }

    return groups;
  }
}

class DependencyPlanner {
  constructor(register) {
    this.register = register;
  }

  topologicalOrder() {
    const errors = this.register.validate();

    if (errors.length > 0) {
      throw new ActivityValidationError(errors.join(" "));
    }

    const indegree = new Map();

    for (const activity of this.register.values()) {
      indegree.set(activity.id, activity.dependencies.size);
    }

    const successors = new Map();

    for (const activity of this.register.values()) {
      for (const dependency of activity.dependencies) {
        if (!successors.has(dependency)) {
          successors.set(dependency, []);
        }

        successors.get(dependency).push(activity.id);
      }
    }

    const ready = [...indegree.entries()]
      .filter(([, degree]) => degree === 0)
      .map(([id]) => id)
      .sort();

    const result = [];

    while (ready.length > 0) {
      const current = ready.shift();
      result.push(current);

      for (const successor of successors.get(current) || []) {
        indegree.set(successor, indegree.get(successor) - 1);

        if (indegree.get(successor) === 0) {
          ready.push(successor);
          ready.sort();
        }
      }
    }

    if (result.length !== indegree.size) {
      throw new ActivityValidationError(
        "Dependency ordering failed because a cycle exists."
      );
    }

    return result;
  }
}

function createProjectActivities() {
  return [
    new Activity({
      id: "ACT-101",
      name: "Identify customer reporting needs",
      description:
        "Collect and validate reporting requirements from business stakeholders.",
      owner: "Business Analyst",
      durationDays: 3,
      priority: Priority.HIGH,
      deliverable: "Validated requirements register",
      tags: ["requirements"],
    }),

    new Activity({
      id: "ACT-102",
      name: "Define analytical data structure",
      description:
        "Define the entities, dimensions, measures, and relationships required for reporting.",
      owner: "Data Architect",
      durationDays: 4,
      priority: Priority.HIGH,
      dependencies: ["ACT-101"],
      deliverable: "Approved data structure",
      tags: ["data"],
    }),

    new Activity({
      id: "ACT-103",
      name: "Design dashboard interaction flow",
      description:
        "Define how users navigate reports, filters, drill-downs, and operational views.",
      owner: "Product Designer",
      durationDays: 3,
      dependencies: ["ACT-101"],
      deliverable: "Dashboard interaction specification",
      tags: ["design"],
    }),

    new Activity({
      id: "ACT-104",
      name: "Implement reporting data pipeline",
      description:
        "Build data extraction, validation, transformation, and loading processes.",
      owner: "Data Engineer",
      durationDays: 6,
      priority: Priority.HIGH,
      dependencies: ["ACT-102"],
      deliverable: "Validated reporting pipeline",
      tags: ["data"],
    }),

    new Activity({
      id: "ACT-105",
      name: "Implement reporting dashboard",
      description:
        "Build the dashboard interface using the approved interaction model and data pipeline.",
      owner: "Frontend Engineer",
      durationDays: 5,
      dependencies: ["ACT-103", "ACT-104"],
      deliverable: "Functional dashboard",
      tags: ["development"],
    }),

    new Activity({
      id: "ACT-106",
      name: "Execute integration validation",
      description:
        "Validate the complete reporting flow from source data through the user interface.",
      type: ActivityType.REVIEW,
      owner: "QA Engineer",
      durationDays: 4,
      priority: Priority.HIGH,
      dependencies: ["ACT-105"],
      deliverable: "Integration validation report",
      tags: ["quality"],
    }),

    new Activity({
      id: "ACT-107",
      name: "Approve production readiness",
      description:
        "Review operational and release readiness before production deployment.",
      type: ActivityType.REVIEW,
      owner: "Release Manager",
      durationDays: 2,
      priority: Priority.CRITICAL,
      dependencies: ["ACT-106"],
      deliverable: "Production readiness decision",
      tags: ["release"],
    }),

    new Activity({
      id: "ACT-108",
      name: "Production readiness milestone",
      description:
        "Marks the identified project event representing production readiness.",
      type: ActivityType.MILESTONE,
      owner: "Release Manager",
      durationDays: 0,
      priority: Priority.CRITICAL,
      dependencies: ["ACT-107"],
      deliverable: "Production readiness milestone",
      tags: ["release"],
    }),
  ];
}

function demonstrateCandidateIdentification() {
  console.log("=== Candidate Activity Identification ===");

  const statement = `
    Identify customer reporting needs.
    Define the analytical data structure.
    Design the dashboard interaction flow.
    Implement the reporting data pipeline.
    Validate the integrated dashboard.
  `;

  const extractor = new ActivityCandidateExtractor();

  for (const candidate of extractor.extract(statement)) {
    console.log(`Candidate: ${candidate}`);
  }
}

function demonstrateEventDrivenRegistration(register) {
  const eventLog = new ActivityEventLog();

  register.on("activityAdded", (activity) => {
    eventLog.record("activity-added", activity);
  });

  const newActivity = new Activity({
    id: "ACT-109",
    name: "Conduct operational handoff",
    description:
      "Transfer operational ownership information to the support function.",
    type: ActivityType.HANDOFF,
    owner: "Operations Lead",
    durationDays: 2,
    priority: Priority.MEDIUM,
    dependencies: ["ACT-107"],
    deliverable: "Operational handoff record",
    tags: ["release"],
  });

  register.add(newActivity);
  eventLog.print();
}

function printRegisterAnalysis(register) {
  console.log("\n=== Activity Identification Analysis ===");

  const analyzer = new ActivityAnalyzer(register);

  console.log(
    `Activities without owners: ${analyzer.withoutOwners().length}`
  );

  console.log(
    `Actionable activities without deliverables: ` +
      `${analyzer.withoutDeliverables().length}`
  );

  console.log(
    `High-attention activities: ${analyzer.highAttentionActivities().length}`
  );

  console.log("\nWork-package distribution:");

  for (const [packageName, activities] of analyzer.byWorkPackage()) {
    console.log(`  ${packageName}: ${activities.length} activities`);
  }
}

function printDependencyOrder(register) {
  console.log("\n=== Dependency-Aware Identification Order ===");

  const planner = new DependencyPlanner(register);

  for (const id of planner.topologicalOrder()) {
    const activity = register.get(id);

    console.log(
      `${id} | ${activity.name} | ` +
        `dependencies: ${[...activity.dependencies].join(", ") || "none"}`
    );
  }
}

function demonstrateFailureDetection() {
  console.log("\n=== Identification Failure Detection ===");

  const invalidRegister = new ActivityRegister();

  invalidRegister.add(
    new Activity({
      id: "FAIL-001",
      name: "Build analytics dashboard",
      description: "Build the dashboard.",
      dependencies: ["MISSING-001"],
      deliverable: "Dashboard",
    })
  );

  const errors = invalidRegister.validate();

  for (const error of errors) {
    console.log(`Detected: ${error}`);
  }

  const cycleRegister = new ActivityRegister();

  cycleRegister.add(
    new Activity({
      id: "CYCLE-A",
      name: "Define release workflow",
      description: "Define release workflow.",
      dependencies: ["CYCLE-B"],
      deliverable: "Workflow",
    })
  );

  cycleRegister.add(
    new Activity({
      id: "CYCLE-B",
      name: "Validate release workflow",
      description: "Validate release workflow.",
      dependencies: ["CYCLE-A"],
      deliverable: "Validation",
    })
  );

  for (const error of cycleRegister.validate()) {
    console.log(`Detected: ${error}`);
  }
}

function main() {
  console.log("PROJECT ACTIVITY IDENTIFICATION MODEL");
  console.log("====================================");

  demonstrateCandidateIdentification();

  const register = new ActivityRegister();

  for (const activity of createProjectActivities()) {
    register.add(activity);
  }

  demonstrateEventDrivenRegistration(register);
  printRegisterAnalysis(register);
  printDependencyOrder(register);
  demonstrateFailureDetection();

  console.log("\nActivity identification processing completed.");
}

main();
