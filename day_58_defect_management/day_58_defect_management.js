#!/usr/bin/env node
"use strict";

/*
 * Defect Management Event and Policy Engine
 *
 * This implementation uses JavaScript-specific event-driven behavior.
 * Defect lifecycle changes emit events consumed by audit and notification
 * handlers. Policy evaluation is separated from state mutation.
 */

const EventEmitter = require("node:events");
const crypto = require("node:crypto");

const Status = Object.freeze({
  NEW: "NEW",
  TRIAGED: "TRIAGED",
  ASSIGNED: "ASSIGNED",
  IN_PROGRESS: "IN_PROGRESS",
  RESOLVED: "RESOLVED",
  VERIFIED: "VERIFIED",
  REOPENED: "REOPENED",
  CLOSED: "CLOSED",
  REJECTED: "REJECTED"
});

const Severity = Object.freeze({
  BLOCKER: "BLOCKER",
  CRITICAL: "CRITICAL",
  MAJOR: "MAJOR",
  MINOR: "MINOR",
  TRIVIAL: "TRIVIAL"
});

const Priority = Object.freeze({
  P0: "P0",
  P1: "P1",
  P2: "P2",
  P3: "P3"
});

const TERMINAL_STATUSES = new Set([Status.CLOSED, Status.REJECTED]);

class DefectError extends Error {
  constructor(message, code = "DEFECT_ERROR") {
    super(message);
    this.name = "DefectError";
    this.code = code;
  }
}

class Defect extends EventEmitter {
  constructor(data) {
    super();

    if (!data.title?.trim() || !data.description?.trim()) {
      throw new DefectError("Title and description are required.", "INVALID_INPUT");
    }

    if (!Object.values(Severity).includes(data.severity)) {
      throw new DefectError("Invalid severity.", "INVALID_SEVERITY");
    }

    if (!Object.values(Priority).includes(data.priority)) {
      throw new DefectError("Invalid priority.", "INVALID_PRIORITY");
    }

    this.id = data.id;
    this.title = data.title.trim();
    this.description = data.description.trim();
    this.severity = data.severity;
    this.priority = data.priority;
    this.reporterId = data.reporterId;
    this.assigneeId = null;
    this.status = Status.NEW;
    this.version = data.version;
    this.environment = data.environment;
    this.comments = [];
    this.history = [];
    this.resolution = null;
    this.createdAt = new Date().toISOString();

    this.record("CREATED", { reporterId: this.reporterId });
  }

  record(event, payload = {}) {
    this.history.push({
      event,
      payload: structuredClone(payload),
      timestamp: new Date().toISOString()
    });
    this.emit(event, { defect: this, payload });
  }

  transition(nextStatus, actorId, allowedStatuses) {
    if (!allowedStatuses.has(this.status)) {
      throw new DefectError(
        `Cannot transition ${this.status} to ${nextStatus}.`,
        "INVALID_TRANSITION"
      );
    }

    const previous = this.status;
    this.status = nextStatus;
    this.record("STATUS_CHANGED", {
      actorId,
      previous,
      current: nextStatus
    });
  }

  assign(actorId, assigneeId) {
    if (this.status !== Status.TRIAGED && this.status !== Status.REOPENED) {
      throw new DefectError("Only triaged or reopened defects can be assigned.");
    }
    this.assigneeId = assigneeId;
    this.transition(Status.ASSIGNED, actorId, new Set([Status.TRIAGED, Status.REOPENED]));
  }

  start(actorId) {
    if (this.assigneeId !== actorId) {
      throw new DefectError("Only the assignee can start work.", "NOT_ASSIGNEE");
    }
    this.transition(Status.IN_PROGRESS, actorId, new Set([Status.ASSIGNED]));
  }

  resolve(actorId, resolution) {
    if (this.assigneeId !== actorId) {
      throw new DefectError("Only the assignee can resolve the defect.", "NOT_ASSIGNEE");
    }
    if (!resolution?.trim()) {
      throw new DefectError("Resolution is required.", "INVALID_RESOLUTION");
    }
    this.resolution = resolution.trim();
    this.transition(Status.RESOLVED, actorId, new Set([Status.IN_PROGRESS]));
  }

  verify(actorId, passed) {
    if (this.status !== Status.RESOLVED) {
      throw new DefectError("Only resolved defects can be verified.");
    }

    if (passed) {
      this.transition(Status.VERIFIED, actorId, new Set([Status.RESOLVED]));
    } else {
      this.transition(Status.REOPENED, actorId, new Set([Status.RESOLVED]));
    }
  }

  close(actorId) {
    this.transition(Status.CLOSED, actorId, new Set([Status.VERIFIED]));
  }

  reject(actorId, reason) {
    if (!reason?.trim()) {
      throw new DefectError("Rejection reason is required.");
    }
    this.resolution = reason.trim();
    this.transition(Status.REJECTED, actorId, new Set([Status.NEW, Status.TRIAGED]));
  }

  addComment(authorId, body) {
    if (!body?.trim()) {
      throw new DefectError("Comment cannot be empty.");
    }

    const comment = {
      id: crypto.randomUUID(),
      authorId,
      body: body.trim(),
      createdAt: new Date().toISOString()
    };

    this.comments.push(comment);
    this.record("COMMENT_ADDED", { commentId: comment.id, authorId });
    return comment;
  }
}

class DefectPolicy {
  constructor({
    requiredChecks = ["unit-tests", "security-scan"],
    criticalRequiresOwner = true,
    p0RequiresManager = true
  } = {}) {
    this.requiredChecks = new Set(requiredChecks);
    this.criticalRequiresOwner = criticalRequiresOwner;
    this.p0RequiresManager = p0RequiresManager;
  }

  evaluate(defect, context) {
    const failures = [];

    if (TERMINAL_STATUSES.has(defect.status)) {
      failures.push("Defect is already in a terminal state.");
    }

    if (!context.assigneeId) {
      failures.push("No assignee exists.");
    }

    for (const check of this.requiredChecks) {
      if (context.checks.get(check) !== "PASSED") {
        failures.push(`Required check failed: ${check}.`);
      }
    }

    if (
      this.criticalRequiresOwner &&
      defect.severity === Severity.CRITICAL &&
      !context.ownerApproved
    ) {
      failures.push("Critical defect requires owner approval.");
    }

    if (
      this.p0RequiresManager &&
      defect.priority === Priority.P0 &&
      !context.managerApproved
    ) {
      failures.push("P0 defect requires manager approval.");
    }

    return {
      eligible: failures.length === 0,
      failures
    };
  }
}

class DefectRepository {
  constructor() {
    this.defects = new Map();
    this.sequence = 5000;
  }

  create(data) {
    const defect = new Defect({
      ...data,
      id: this.sequence++
    });
    this.defects.set(defect.id, defect);
    return defect;
  }

  get(id) {
    const defect = this.defects.get(id);
    if (!defect) {
      throw new DefectError(`Defect ${id} was not found.`, "NOT_FOUND");
    }
    return defect;
  }

  listOpen() {
    return [...this.defects.values()].filter(
      (defect) => !TERMINAL_STATUSES.has(defect.status)
    );
  }
}

class NotificationService {
  constructor() {
    this.messages = [];
  }

  attach(defect) {
    defect.on("STATUS_CHANGED", ({ payload }) => {
      this.messages.push({
        type: "STATUS_NOTIFICATION",
        defectId: defect.id,
        actorId: payload.actorId,
        message: `Defect ${defect.id}: ${payload.previous} -> ${payload.current}`
      });
    });

    defect.on("COMMENT_ADDED", ({ payload }) => {
      this.messages.push({
        type: "COMMENT_NOTIFICATION",
        defectId: defect.id,
        message: `New comment ${payload.commentId}`
      });
    });
  }
}

async function processDefects(defects, operation) {
  // Promise.all preserves independent asynchronous work without serializing it.
  return Promise.all(
    defects.map(
      (defect) =>
        new Promise((resolve) => {
          setImmediate(() => {
            resolve(operation(defect));
          });
        })
    )
  );
}

async function main() {
  const repository = new DefectRepository();
  const notifications = new NotificationService();
  const policy = new DefectPolicy();

  const defect = repository.create({
    title: "Inventory API accepts negative quantity",
    description: "An invalid quantity can reach persistence through the API.",
    severity: Severity.CRITICAL,
    priority: Priority.P1,
    reporterId: 101,
    version: "7.3.1",
    environment: "staging"
  });

  notifications.attach(defect);

  defect.transition(Status.TRIAGED, 201, new Set([Status.NEW]));
  defect.assign(201, 305);
  defect.start(305);

  defect.addComment(
    201,
    "Validation is missing at the API boundary. Database constraint should remain as defense in depth."
  );

  defect.resolve(
    305,
    "Added positive-integer validation and a database CHECK constraint."
  );

  const checks = new Map([
    ["unit-tests", "PASSED"],
    ["security-scan", "PASSED"]
  ]);

  let decision = policy.evaluate(defect, {
    assigneeId: defect.assigneeId,
    checks,
    ownerApproved: true,
    managerApproved: true
  });

  if (!decision.eligible) {
    throw new DefectError(decision.failures.join(" "));
  }

  defect.verify(402, true);
  defect.close(201);

  // Demonstrate a rejected invalid operation.
  try {
    defect.start(305);
  } catch (error) {
    console.log(`Expected failure [${error.code}]: ${error.message}`);
  }

  const second = repository.create({
    title: "CSV export truncates Unicode product names",
    description: "Names containing non-ASCII characters are truncated.",
    severity: Severity.MAJOR,
    priority: Priority.P2,
    reporterId: 101,
    version: "7.3.1",
    environment: "staging"
  });

  notifications.attach(second);
  second.transition(Status.TRIAGED, 201, new Set([Status.NEW]));
  second.assign(201, 306);
  second.start(306);

  const open = repository.listOpen();
  const processed = await processDefects(open, (item) => ({
    id: item.id,
    severity: item.severity,
    priority: item.priority,
    status: item.status
  }));

  console.log("\nFinal defect:");
  console.log({
    id: defect.id,
    status: defect.status,
    resolution: defect.resolution
  });

  console.log("\nOpen defects:");
  console.table(processed);

  console.log("\nEvent notifications:");
  console.table(notifications.messages);

  console.log("\nPolicy decision:");
  console.log(decision);

  // Invariant checks act as lightweight executable tests.
  if (defect.status !== Status.CLOSED) {
    throw new Error("Lifecycle invariant failed.");
  }

  if (repository.get(second.id).status !== Status.IN_PROGRESS) {
    throw new Error("Second defect lifecycle invariant failed.");
  }
}

main().catch((error) => {
  console.error(`Fatal error: ${error.message}`);
  process.exitCode = 1;
});
