"use strict";

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

const PRState = Object.freeze({
  DRAFT: "draft",
  OPEN: "open",
  CLOSED: "closed",
  MERGED: "merged",
});

const ReviewState = Object.freeze({
  COMMENTED: "commented",
  APPROVED: "approved",
  CHANGES_REQUESTED: "changes_requested",
  DISMISSED: "dismissed",
});

class ResourcePool {
  constructor(resources) {
    this.resources = new Map();
    this.allocations = new Map();

    for (const resource of resources) {
      if (!resource.id || resource.capacityHours <= 0 || resource.hourlyCost < 0) {
        throw new Error(`Invalid resource definition: ${resource.id}`);
      }
      this.resources.set(resource.id, Object.freeze({ ...resource }));
      this.allocations.set(resource.id, 0);
    }
  }

  allocate(resourceId, hours) {
    const resource = this.resources.get(resourceId);
    if (!resource) throw new Error(`Unknown resource: ${resourceId}`);
    if (!Number.isFinite(hours) || hours <= 0) {
      throw new Error("Allocation must be a positive finite number");
    }

    const used = this.allocations.get(resourceId);
    if (used + hours > resource.capacityHours) {
      throw new Error(
        `Capacity exceeded for ${resourceId}: ${used + hours}h > ${resource.capacityHours}h`
      );
    }

    this.allocations.set(resourceId, used + hours);
  }

  utilization(resourceId) {
    const resource = this.resources.get(resourceId);
    if (!resource) throw new Error(`Unknown resource: ${resourceId}`);
    return this.allocations.get(resourceId) / resource.capacityHours;
  }

  cost() {
    let total = 0;
    for (const [id, resource] of this.resources) {
      total += this.allocations.get(id) * resource.hourlyCost;
    }
    return total;
  }

  snapshot() {
    return [...this.resources.entries()].map(([id, resource]) => ({
      id,
      role: resource.role,
      capacityHours: resource.capacityHours,
      allocatedHours: this.allocations.get(id),
      utilization: this.utilization(id),
    }));
  }
}

class RepositoryPolicy {
  constructor({
    requiredApprovals = 1,
    requiredChecks = [],
    requireResolvedConversations = true,
    requireLinearHistory = false,
    directPushAllowed = false,
    forcePushAllowed = false,
  }) {
    this.requiredApprovals = requiredApprovals;
    this.requiredChecks = new Set(requiredChecks);
    this.requireResolvedConversations = requireResolvedConversations;
    this.requireLinearHistory = requireLinearHistory;
    this.directPushAllowed = directPushAllowed;
    this.forcePushAllowed = forcePushAllowed;
  }
}

class Repository extends EventEmitter {
  constructor(name, policy) {
    super();
    this.name = name;
    this.policy = policy;
    this.branches = new Map([["main", []]]);
    this.pullRequests = new Map();
    this.nextNumber = 1;
  }

  createBranch(name, base = "main") {
    if (this.branches.has(name)) throw new Error(`Branch exists: ${name}`);
    const baseCommits = this.branches.get(base);
    if (!baseCommits) throw new Error(`Unknown base branch: ${base}`);
    this.branches.set(name, [...baseCommits]);
  }

  commit(branch, message, author) {
    const history = this.branches.get(branch);
    if (!history) throw new Error(`Unknown branch: ${branch}`);
    if (!message.trim() || !author.trim()) {
      throw new Error("Commit message and author are required");
    }

    const sha = crypto
      .createHash("sha256")
      .update(`${branch}:${message}:${author}:${Date.now()}:${Math.random()}`)
      .digest("hex")
      .slice(0, 12);

    const commit = Object.freeze({
      sha,
      message,
      author,
      timestamp: new Date().toISOString(),
    });

    history.push(commit);
    return commit;
  }

  openPullRequest(source, target, author, draft = false) {
    const sourceHistory = this.branches.get(source);
    if (!sourceHistory || !this.branches.has(target)) {
      throw new Error("Both branches must exist");
    }
    if (source === target) throw new Error("Source and target must differ");
    if (sourceHistory.length === 0) throw new Error("No changes to propose");

    const number = this.nextNumber++;
    const pr = {
      number,
      source,
      target,
      author,
      state: draft ? PRState.DRAFT : PRState.OPEN,
      draft,
      commits: [...sourceHistory],
      reviews: [],
      comments: [],
      checks: new Map(),
      targetHead: this.branches.get(target).at(-1)?.sha ?? null,
      baseSynchronized: true,
    };

    this.pullRequests.set(number, pr);
    this.emit("pull-request.opened", { number, source, target });
    return pr;
  }

  addReview(number, reviewer, state, commitSha, comments = []) {
    const pr = this.requirePR(number);

    if (![PRState.OPEN, PRState.DRAFT].includes(pr.state)) {
      throw new Error("Review requires an active pull request");
    }
    if (reviewer === pr.author) {
      throw new Error("Self-approval is not permitted");
    }

    pr.reviews.push({
      reviewer,
      state,
      commitSha,
      timestamp: new Date().toISOString(),
    });

    for (const comment of comments) {
      pr.comments.push({
        ...comment,
        reviewer,
        resolved: false,
      });
    }

    this.emit("review.submitted", { number, reviewer, state });
  }

  resolveComment(number, index) {
    const pr = this.requirePR(number);
    const comment = pr.comments[index];
    if (!comment) throw new Error("Unknown review comment");
    comment.resolved = true;
  }

  setCheck(number, name, passed) {
    const pr = this.requirePR(number);
    pr.checks.set(name, {
      passed: Boolean(passed),
      completedAt: new Date().toISOString(),
    });
    this.emit("check.completed", { number, name, passed: Boolean(passed) });
  }

  synchronize(number) {
    const pr = this.requirePR(number);
    const target = this.branches.get(pr.target);
    pr.targetHead = target.at(-1)?.sha ?? null;
    pr.baseSynchronized = true;
  }

  markBaseChanged(number) {
    const pr = this.requirePR(number);
    pr.baseSynchronized = false;
  }

  evaluate(number) {
    const pr = this.requirePR(number);
    const failures = [];

    if (pr.state !== PRState.OPEN) failures.push("pull request is not open");
    if (pr.draft) failures.push("pull request is draft");
    if (!pr.baseSynchronized) failures.push("base branch is stale");

    const latestSha = pr.commits.at(-1)?.sha;
    const approvals = new Set();

    for (const review of pr.reviews) {
      if (
        review.state === ReviewState.APPROVED &&
        review.commitSha === latestSha &&
        pr.baseSynchronized
      ) {
        approvals.add(review.reviewer);
      }
    }

    if (approvals.size < this.policy.requiredApprovals) {
      failures.push("required approvals are missing");
    }

    for (const requiredCheck of this.policy.requiredChecks) {
      const check = pr.checks.get(requiredCheck);
      if (!check?.passed) failures.push(`required check failed: ${requiredCheck}`);
    }

    if (
      this.policy.requireResolvedConversations &&
      pr.comments.some((comment) => !comment.resolved)
    ) {
      failures.push("unresolved review conversations remain");
    }

    return {
      eligible: failures.length === 0,
      failures,
      approvals: [...approvals],
    };
  }

  merge(number, strategy = "squash") {
    const pr = this.requirePR(number);
    const result = this.evaluate(number);

    if (!result.eligible) {
      throw new Error(`Merge blocked: ${result.failures.join("; ")}`);
    }

    if (!["merge", "squash", "rebase"].includes(strategy)) {
      throw new Error(`Unsupported merge strategy: ${strategy}`);
    }

    const target = this.branches.get(pr.target);
    target.push(...pr.commits);

    pr.state = PRState.MERGED;
    pr.mergeStrategy = strategy;
    pr.mergedAt = new Date().toISOString();

    this.emit("pull-request.merged", {
      number,
      strategy,
      commitCount: pr.commits.length,
    });
  }

  requirePR(number) {
    const pr = this.pullRequests.get(number);
    if (!pr) throw new Error(`Unknown pull request #${number}`);
    return pr;
  }
}

async function runChecks(repository, prNumber) {
  const checks = [
    ["unit-tests", 40, true],
    ["security-scan", 70, true],
    ["documentation", 15, true],
  ];

  await Promise.all(
    checks.map(
      ([name, delay, result]) =>
        new Promise((resolve) => {
          setTimeout(() => {
            repository.setCheck(prNumber, name, result);
            resolve();
          }, delay);
        })
    )
  );
}

async function main() {
  const resources = new ResourcePool([
    { id: "engineer-1", role: "engineer", capacityHours: 32, hourlyCost: 85 },
    { id: "reviewer-1", role: "reviewer", capacityHours: 16, hourlyCost: 110 },
    { id: "ci", role: "automation", capacityHours: 20, hourlyCost: 20 },
  ]);

  resources.allocate("engineer-1", 12);
  resources.allocate("reviewer-1", 4);
  resources.allocate("ci", 2);

  const repository = new Repository(
    "project-resource-manager",
    new RepositoryPolicy({
      requiredApprovals: 1,
      requiredChecks: ["unit-tests", "security-scan"],
      requireResolvedConversations: true,
      requireLinearHistory: true,
      directPushAllowed: false,
      forcePushAllowed: false,
    })
  );

  repository.on("pull-request.merged", (event) => {
    console.log(
      `Merged PR #${event.number} using ${event.strategy} strategy`
    );
  });

  repository.createBranch("feature/resource-capacity");
  repository.commit(
    "feature/resource-capacity",
    "Add resource allocation rules",
    "engineer-1"
  );
  const latest = repository.commit(
    "feature/resource-capacity",
    "Reject allocations beyond capacity",
    "engineer-1"
  );

  const pr = repository.openPullRequest(
    "feature/resource-capacity",
    "main",
    "engineer-1"
  );

  repository.addReview(
    pr.number,
    "reviewer-1",
    ReviewState.CHANGES_REQUESTED,
    latest.sha,
    [
      {
        file: "resource.js",
        line: 54,
        message: "Validate fractional allocation input.",
      },
    ]
  );

  console.log("Initial eligibility:", repository.evaluate(pr.number));

  repository.resolveComment(pr.number, 0);

  repository.addReview(
    pr.number,
    "reviewer-1",
    ReviewState.APPROVED,
    latest.sha
  );

  await runChecks(repository, pr.number);

  console.log("Final eligibility:", repository.evaluate(pr.number));

  repository.merge(pr.number, "squash");

  console.table(resources.snapshot());
  console.log("Resource cost:", resources.cost().toFixed(2));

  try {
    resources.allocate("engineer-1", 25);
  } catch (error) {
    console.log("Expected resource failure:", error.message);
  }
}

main().catch((error) => {
  console.error("Execution failed:", error.message);
  process.exitCode = 1;
});
