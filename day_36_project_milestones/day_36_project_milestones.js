"use strict";

/*
 * Project milestone event engine.
 *
 * The implementation treats a milestone as an important project outcome
 * and project events as evidence that the outcome is progressing, blocked,
 * reviewed, approved, merged, or released.
 *
 * Pull Requests provide a change-delivery workflow.
 * Code Review evaluates the proposed changes.
 * Approvals represent review decisions.
 * Branch protection turns repository governance into merge conditions.
 * Milestones aggregate these events into meaningful project-level progress.
 */

const MilestoneStatus = Object.freeze({
  PLANNED: "planned",
  ACTIVE: "active",
  COMPLETED: "completed",
  BLOCKED: "blocked",
  CANCELLED: "cancelled",
});

const EventType = Object.freeze({
  PROJECT_STARTED: "project_started",
  REQUIREMENT_APPROVED: "requirement_approved",
  DESIGN_COMPLETED: "design_completed",
  PULL_REQUEST_OPENED: "pull_request_opened",
  REVIEW_SUBMITTED: "review_submitted",
  APPROVAL_GRANTED: "approval_granted",
  STATUS_CHECK: "status_check",
  MERGED: "merged",
  RELEASED: "released",
  MILESTONE_COMPLETED: "milestone_completed",
  MILESTONE_BLOCKED: "milestone_blocked",
});

class EventBus {
  #handlers = new Map();

  on(eventType, handler) {
    if (!this.#handlers.has(eventType)) {
      this.#handlers.set(eventType, []);
    }
    this.#handlers.get(eventType).push(handler);
  }

  emit(eventType, payload) {
    const handlers = this.#handlers.get(eventType) ?? [];
    for (const handler of handlers) {
      handler(payload);
    }
  }
}

class ProjectEvent {
  constructor({
    id,
    type,
    title,
    actor,
    timestamp = new Date(),
    milestoneId = null,
    details = {},
  }) {
    if (!id || !type || !title || !actor) {
      throw new Error("Event requires an id, type, title, and actor.");
    }

    this.id = id;
    this.type = type;
    this.title = title;
    this.actor = actor;
    this.timestamp = timestamp;
    this.milestoneId = milestoneId;
    this.details = Object.freeze({ ...details });
  }
}

class Milestone {
  constructor({
    id,
    name,
    targetDate,
    importance,
    dependencies = [],
  }) {
    if (!id || !name) {
      throw new Error("Milestone id and name are required.");
    }

    if (!Number.isInteger(importance) || importance < 1 || importance > 5) {
      throw new Error("Milestone importance must be an integer from 1 to 5.");
    }

    this.id = id;
    this.name = name;
    this.targetDate = new Date(targetDate);
    this.importance = importance;
    this.dependencies = new Set(dependencies);
    this.status = MilestoneStatus.PLANNED;
    this.completedAt = null;
  }

  isOverdue(now = new Date()) {
    return (
      ![
        MilestoneStatus.COMPLETED,
        MilestoneStatus.CANCELLED,
      ].includes(this.status) &&
      now > this.targetDate
    );
  }
}

class PullRequest {
  constructor({
    number,
    sourceBranch,
    targetBranch,
    milestoneId,
    commits,
    draft = true,
  }) {
    if (sourceBranch === targetBranch) {
      throw new Error("Source and target branches must be different.");
    }

    if (!Array.isArray(commits) || commits.length === 0) {
      throw new Error("A Pull Request requires at least one commit.");
    }

    this.number = number;
    this.sourceBranch = sourceBranch;
    this.targetBranch = targetBranch;
    this.milestoneId = milestoneId;
    this.commits = [...commits];
    this.draft = draft;
    this.conflicted = false;
    this.merged = false;
    this.statusChecks = new Map();
    this.reviews = [];
  }

  addCommit(commit) {
    if (this.merged) {
      throw new Error("Cannot add a commit to a merged Pull Request.");
    }

    if (!commit.trim()) {
      throw new Error("Commit message cannot be empty.");
    }

    this.commits.push(commit.trim());
  }

  setStatusCheck(name, passed) {
    this.statusChecks.set(name, Boolean(passed));
  }

  addReview(review) {
    this.reviews.push(review);
  }

  unresolvedReviewComments() {
    return this.reviews.reduce(
      (total, review) => total + review.unresolvedComments,
      0,
    );
  }

  hasChangesRequested() {
    return this.reviews.some(
      (review) => review.state === "CHANGES_REQUESTED",
    );
  }

  approvalCount() {
    return new Set(
      this.reviews
        .filter(
          (review) =>
            review.state === "APPROVED" &&
            review.unresolvedComments === 0,
        )
        .map((review) => review.reviewer),
    ).size;
  }
}

class Review {
  constructor({
    reviewer,
    state,
    inlineComments = [],
    resolvedComments = 0,
  }) {
    const validStates = new Set([
      "APPROVED",
      "CHANGES_REQUESTED",
      "COMMENTED",
    ]);

    if (!validStates.has(state)) {
      throw new Error(`Unsupported review state: ${state}`);
    }

    if (resolvedComments > inlineComments.length) {
      throw new Error(
        "Resolved review comments cannot exceed submitted comments.",
      );
    }

    this.reviewer = reviewer;
    this.state = state;
    this.inlineComments = [...inlineComments];
    this.resolvedComments = resolvedComments;
  }

  get unresolvedComments() {
    return this.inlineComments.length - this.resolvedComments;
  }
}

class BranchProtectionPolicy {
  constructor({
    branch,
    requiredApprovals = 1,
    requiredStatusChecks = [],
    requireConversationResolution = true,
    restrictDirectPushes = true,
    allowForcePush = false,
    allowDeletion = false,
    requireLinearHistory = false,
    dismissStaleApprovals = true,
  }) {
    this.branch = branch;
    this.requiredApprovals = requiredApprovals;
    this.requiredStatusChecks = [...requiredStatusChecks];
    this.requireConversationResolution = requireConversationResolution;
    this.restrictDirectPushes = restrictDirectPushes;
    this.allowForcePush = allowForcePush;
    this.allowDeletion = allowDeletion;
    this.requireLinearHistory = requireLinearHistory;
    this.dismissStaleApprovals = dismissStaleApprovals;
  }
}

class ProjectMilestoneEngine {
  constructor(projectId, projectName) {
    this.projectId = projectId;
    this.projectName = projectName;
    this.milestones = new Map();
    this.pullRequests = new Map();
    this.events = [];
    this.policies = new Map();
    this.eventBus = new EventBus();
    this.nextEventId = 1;

    this.eventBus.on(EventType.MERGED, (event) => {
      console.log(
        `[EVENT] ${event.title} | milestone=${event.milestoneId}`,
      );
    });

    this.eventBus.on(EventType.MILESTONE_COMPLETED, (event) => {
      console.log(`[MILESTONE] ${event.title}`);
    });
  }

  addMilestone(milestone) {
    if (this.milestones.has(milestone.id)) {
      throw new Error(`Duplicate milestone: ${milestone.id}`);
    }

    for (const dependency of milestone.dependencies) {
      if (!this.milestones.has(dependency)) {
        throw new Error(
          `Milestone ${milestone.id} depends on unknown milestone ${dependency}`,
        );
      }
    }

    this.milestones.set(milestone.id, milestone);
  }

  recordEvent(type, title, actor, milestoneId = null, details = {}) {
    if (milestoneId && !this.milestones.has(milestoneId)) {
      throw new Error(`Unknown milestone: ${milestoneId}`);
    }

    const event = new ProjectEvent({
      id: this.nextEventId++,
      type,
      title,
      actor,
      milestoneId,
      details,
    });

    this.events.push(event);
    this.eventBus.emit(type, event);
    return event;
  }

  activateMilestone(milestoneId) {
    const milestone = this.getMilestone(milestoneId);

    for (const dependency of milestone.dependencies) {
      if (
        this.getMilestone(dependency).status !== MilestoneStatus.COMPLETED
      ) {
        throw new Error(
          `Cannot activate ${milestoneId}: dependency ${dependency} is incomplete.`,
        );
      }
    }

    if (
      ![
        MilestoneStatus.PLANNED,
        MilestoneStatus.BLOCKED,
      ].includes(milestone.status)
    ) {
      throw new Error(
        `Milestone ${milestoneId} cannot be activated from ${milestone.status}.`,
      );
    }

    milestone.status = MilestoneStatus.ACTIVE;
  }

  completeMilestone(milestoneId, actor, reason) {
    const milestone = this.getMilestone(milestoneId);

    if (milestone.status === MilestoneStatus.CANCELLED) {
      throw new Error("A cancelled milestone cannot be completed.");
    }

    const unfinished = [...this.pullRequests.values()].filter(
      (pr) =>
        pr.milestoneId === milestoneId &&
        !pr.merged,
    );

    if (unfinished.length > 0) {
      throw new Error(
        `Milestone ${milestoneId} still has unmerged Pull Requests: ${unfinished
          .map((pr) => `#${pr.number}`)
          .join(", ")}`,
      );
    }

    milestone.status = MilestoneStatus.COMPLETED;
    milestone.completedAt = new Date();

    this.recordEvent(
      EventType.MILESTONE_COMPLETED,
      `Milestone completed: ${milestone.name}`,
      actor,
      milestoneId,
      { reason },
    );
  }

  createPullRequest(pr, actor) {
    if (this.pullRequests.has(pr.number)) {
      throw new Error(`Pull Request #${pr.number} already exists.`);
    }

    if (!this.milestones.has(pr.milestoneId)) {
      throw new Error(`Unknown milestone: ${pr.milestoneId}`);
    }

    this.pullRequests.set(pr.number, pr);

    this.recordEvent(
      EventType.PULL_REQUEST_OPENED,
      `Pull Request #${pr.number} opened`,
      actor,
      pr.milestoneId,
      {
        sourceBranch: pr.sourceBranch,
        targetBranch: pr.targetBranch,
        commits: pr.commits.length,
        draft: pr.draft,
      },
    );
  }

  submitReview(prNumber, review) {
    const pr = this.getPullRequest(prNumber);

    pr.addReview(review);

    this.recordEvent(
      review.state === "APPROVED"
        ? EventType.APPROVAL_GRANTED
        : EventType.REVIEW_SUBMITTED,
      `Review ${review.state.toLowerCase()} for Pull Request #${prNumber}`,
      review.reviewer,
      pr.milestoneId,
      {
        unresolvedComments: review.unresolvedComments,
      },
    );
  }

  setStatusCheck(prNumber, name, passed, actor) {
    const pr = this.getPullRequest(prNumber);
    pr.setStatusCheck(name, passed);

    this.recordEvent(
      EventType.STATUS_CHECK,
      `${name}: ${passed ? "passed" : "failed"}`,
      actor,
      pr.milestoneId,
      { pullRequest: prNumber },
    );
  }

  synchronizePullRequest(prNumber, commit, actor) {
    const pr = this.getPullRequest(prNumber);
    pr.addCommit(commit);

    const policy = this.policies.get(pr.targetBranch);

    if (policy?.dismissStaleApprovals) {
      for (const review of pr.reviews) {
        if (review.state === "APPROVED") {
          review.state = "COMMENTED";
        }
      }
    }

    this.recordEvent(
      EventType.PULL_REQUEST_OPENED,
      `Pull Request #${prNumber} synchronized`,
      actor,
      pr.milestoneId,
      { newCommit: commit },
    );
  }

  setBranchProtection(policy) {
    if (policy.requiredApprovals < 0) {
      throw new Error("Required approvals cannot be negative.");
    }

    this.policies.set(policy.branch, policy);
  }

  evaluateMerge(prNumber) {
    const pr = this.getPullRequest(prNumber);
    const policy = this.policies.get(pr.targetBranch);
    const failures = [];

    if (!policy) {
      failures.push("No branch protection policy exists for the target branch.");
    }

    if (pr.draft) {
      failures.push("Pull Request is a draft.");
    }

    if (pr.conflicted) {
      failures.push("Pull Request has merge conflicts.");
    }

    if (pr.hasChangesRequested()) {
      failures.push("A reviewer has requested changes.");
    }

    if (policy) {
      const approvals = pr.approvalCount();

      if (approvals < policy.requiredApprovals) {
        failures.push(
          `Approval requirement not satisfied: ${approvals}/${policy.requiredApprovals}.`,
        );
      }

      for (const check of policy.requiredStatusChecks) {
        if (pr.statusChecks.get(check) !== true) {
          failures.push(`Required status check failed or is missing: ${check}.`);
        }
      }

      if (
        policy.requireConversationResolution &&
        pr.unresolvedReviewComments() > 0
      ) {
        failures.push("Review conversations remain unresolved.");
      }
    }

    return {
      eligible: failures.length === 0,
      failures,
    };
  }

  mergePullRequest(prNumber, actor) {
    const pr = this.getPullRequest(prNumber);
    const result = this.evaluateMerge(prNumber);

    if (!result.eligible) {
      throw new Error(
        `Pull Request #${prNumber} is not mergeable:\n${result.failures
          .map((failure) => `- ${failure}`)
          .join("\n")}`,
      );
    }

    pr.merged = true;

    this.recordEvent(
      EventType.MERGED,
      `Pull Request #${prNumber} merged into ${pr.targetBranch}`,
      actor,
      pr.milestoneId,
    );
  }

  importantEvents(milestoneId = null) {
    const importantTypes = new Set([
      EventType.REQUIREMENT_APPROVED,
      EventType.DESIGN_COMPLETED,
      EventType.PULL_REQUEST_OPENED,
      EventType.APPROVAL_GRANTED,
      EventType.MERGED,
      EventType.RELEASED,
      EventType.MILESTONE_COMPLETED,
      EventType.MILESTONE_BLOCKED,
    ]);

    return this.events.filter(
      (event) =>
        importantTypes.has(event.type) &&
        (!milestoneId || event.milestoneId === milestoneId),
    );
  }

  milestoneReport(milestoneId) {
    const milestone = this.getMilestone(milestoneId);
    const relatedPRs = [...this.pullRequests.values()].filter(
      (pr) => pr.milestoneId === milestoneId,
    );

    const relatedEvents = this.events.filter(
      (event) => event.milestoneId === milestoneId,
    );

    return {
      id: milestone.id,
      name: milestone.name,
      status: milestone.status,
      targetDate: milestone.targetDate.toISOString(),
      overdue: milestone.isOverdue(),
      eventCount: relatedEvents.length,
      pullRequests: relatedPRs.length,
      mergedPullRequests: relatedPRs.filter((pr) => pr.merged).length,
      latestEvent: relatedEvents.at(-1)?.title ?? null,
    };
  }

  getMilestone(id) {
    const milestone = this.milestones.get(id);
    if (!milestone) {
      throw new Error(`Unknown milestone: ${id}`);
    }
    return milestone;
  }

  getPullRequest(number) {
    const pr = this.pullRequests.get(number);
    if (!pr) {
      throw new Error(`Unknown Pull Request #${number}`);
    }
    return pr;
  }
}

function runExample() {
  const engine = new ProjectMilestoneEngine(
    "PRJ-318",
    "Customer Identity Modernization",
  );

  const today = new Date();
  const dateAfter = (days) => {
    const result = new Date(today);
    result.setDate(result.getDate() + days);
    return result;
  };

  engine.addMilestone(
    new Milestone({
      id: "M-REQ",
      name: "Identity Requirements Baseline",
      targetDate: dateAfter(5),
      importance: 5,
    }),
  );

  engine.addMilestone(
    new Milestone({
      id: "M-API",
      name: "Identity API Implementation",
      targetDate: dateAfter(25),
      importance: 5,
      dependencies: ["M-REQ"],
    }),
  );

  engine.addMilestone(
    new Milestone({
      id: "M-REL",
      name: "Production Identity Release",
      targetDate: dateAfter(40),
      importance: 5,
      dependencies: ["M-API"],
    }),
  );

  engine.recordEvent(
    EventType.PROJECT_STARTED,
    "Identity modernization started",
    "program-manager",
    "M-REQ",
  );

  engine.activateMilestone("M-REQ");

  engine.recordEvent(
    EventType.REQUIREMENT_APPROVED,
    "Authentication and authorization requirements approved",
    "product-owner",
    "M-REQ",
  );

  engine.completeMilestone(
    "M-REQ",
    "product-owner",
    "Requirements baseline approved.",
  );

  engine.activateMilestone("M-API");

  engine.recordEvent(
    EventType.DESIGN_COMPLETED,
    "Identity API architecture approved",
    "architect",
    "M-API",
  );

  engine.setBranchProtection(
    new BranchProtectionPolicy({
      branch: "main",
      requiredApprovals: 2,
      requiredStatusChecks: [
        "unit-tests",
        "integration-tests",
        "security-scan",
      ],
      requireConversationResolution: true,
      restrictDirectPushes: true,
      allowForcePush: false,
      allowDeletion: false,
      requireLinearHistory: true,
      dismissStaleApprovals: true,
    }),
  );

  const pr = new PullRequest({
    number: 731,
    sourceBranch: "feature/identity-api",
    targetBranch: "main",
    milestoneId: "M-API",
    commits: [
      "Implement token validation",
      "Add authorization policy engine",
      "Add security tests",
    ],
    draft: true,
  });

  engine.createPullRequest(pr, "developer");

  pr.draft = false;

  engine.submitReview(
    731,
    new Review({
      reviewer: "senior-engineer",
      state: "APPROVED",
      inlineComments: ["Explain token expiration boundary.", "Naming is clear."],
      resolvedComments: 2,
    }),
  );

  engine.submitReview(
    731,
    new Review({
      reviewer: "security-reviewer",
      state: "COMMENTED",
      inlineComments: ["Please document the failure response."],
      resolvedComments: 0,
    }),
  );

  console.log("\nInitial merge evaluation");
  console.log(engine.evaluateMerge(731));

  engine.submitReview(
    731,
    new Review({
      reviewer: "security-reviewer",
      state: "APPROVED",
      inlineComments: ["Failure response documented."],
      resolvedComments: 1,
    }),
  );

  engine.setStatusCheck(731, "unit-tests", true, "ci");
  engine.setStatusCheck(731, "integration-tests", true, "ci");
  engine.setStatusCheck(731, "security-scan", true, "security-ci");

  console.log("\nFinal merge evaluation");
  console.log(engine.evaluateMerge(731));

  engine.mergePullRequest(731, "release-manager");

  engine.completeMilestone(
    "M-API",
    "engineering-manager",
    "Implementation merged after review, approvals, and protected-branch checks.",
  );

  engine.activateMilestone("M-REL");

  engine.recordEvent(
    EventType.RELEASED,
    "Identity API released to production",
    "release-manager",
    "M-REL",
    { deployment: "production", version: "3.2.0" },
  );

  engine.completeMilestone(
    "M-REL",
    "release-manager",
    "Production validation completed.",
  );

  console.log("\nMilestone reports");
  for (const milestoneId of engine.milestones.keys()) {
    console.log(engine.milestoneReport(milestoneId));
  }

  console.log("\nImportant project events");
  for (const event of engine.importantEvents()) {
    console.log(
      `${event.timestamp.toISOString()} | ${event.type} | ${event.title}`,
    );
  }
}

runExample();
