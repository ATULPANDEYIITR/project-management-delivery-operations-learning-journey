"use strict";

/**
 * Event-driven repository quality and merge-governance model.
 * Run with Node.js 18 or later. Uses only Node.js built-in modules.
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

const Role = Object.freeze({
  READ: "read",
  WRITE: "write",
  MAINTAIN: "maintain",
  ADMIN: "admin",
});

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

const CheckState = Object.freeze({
  PENDING: "pending",
  SUCCESS: "success",
  FAILURE: "failure",
});

const MergeStrategy = Object.freeze({
  MERGE: "merge",
  SQUASH: "squash",
  REBASE: "rebase",
});

class GovernanceError extends Error {
  constructor(message) {
    super(message);
    this.name = "GovernanceError";
  }
}

function validateText(value, field) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new GovernanceError(`${field} must be a non-empty string.`);
  }
  return value.trim();
}

function validatePath(path) {
  const normalized = validateText(path, "File path").replaceAll("\\", "/");
  if (
    normalized.startsWith("/") ||
    normalized.includes("\0") ||
    normalized.split("/").includes("..")
  ) {
    throw new GovernanceError(`Unsafe repository path: ${path}`);
  }
  return normalized;
}

function makePolicy(overrides = {}) {
  const policy = {
    requiredApprovals: 1,
    requiredChecks: new Set(["unit-tests", "security-scan"]),
    dismissStaleApprovals: true,
    requireResolvedThreads: true,
    requireLinearHistory: false,
    allowDirectPush: false,
    allowForcePush: false,
    allowDeletion: false,
    administratorsEnforced: true,
    bypassRoles: new Set(),
    ...overrides,
  };

  if (!Number.isInteger(policy.requiredApprovals) || policy.requiredApprovals < 0) {
    throw new GovernanceError("requiredApprovals must be a non-negative integer.");
  }

  policy.requiredChecks = new Set(policy.requiredChecks);
  policy.bypassRoles = new Set(policy.bypassRoles);
  return Object.freeze(policy);
}

class RepositoryGovernance extends EventEmitter {
  constructor(name, members) {
    super();
    this.name = validateText(name, "Repository name");
    this.members = new Map();
    this.branches = new Map();
    this.policies = new Map();
    this.pullRequests = new Map();
    this.nextPR = 1;
    this.nextReview = 1;
    this.nextThread = 1;
    this.auditSequence = 1;

    for (const member of members) {
      if (
        !member.username ||
        !Object.values(Role).includes(member.role) ||
        this.members.has(member.username)
      ) {
        throw new GovernanceError("Invalid or duplicate repository member.");
      }
      this.members.set(member.username, {
        username: member.username,
        role: member.role,
        active: member.active !== false,
      });
    }

    this.branches.set("main", {
      name: "main",
      head: this.createCommit("system", "Initial commit", []),
      deleted: false,
    });

    this.on("audit", (event) => {
      process.stdout.write(
        `[${event.sequence}] ${event.type}: ${JSON.stringify(event.data)}\n`,
      );
    });
  }

  audit(type, data) {
    this.emit("audit", {
      sequence: this.auditSequence++,
      timestamp: new Date().toISOString(),
      type,
      data,
    });
  }

  member(username) {
    const member = this.members.get(username);
    if (!member || !member.active) {
      throw new GovernanceError(`Unknown or inactive member: ${username}`);
    }
    return member;
  }

  createCommit(author, message, paths, parents = []) {
    return {
      id: crypto.randomUUID(),
      author,
      message: validateText(message, "Commit message"),
      parents: [...parents],
      changedPaths: new Set(paths.map(validatePath)),
      createdAt: new Date().toISOString(),
    };
  }

  createBranch(name, from = "main") {
    name = validateText(name, "Branch name");
    const source = this.branches.get(from);
    if (!source || source.deleted || this.branches.has(name)) {
      throw new GovernanceError("Source branch is unavailable or name already exists.");
    }

    this.branches.set(name, {
      name,
      head: source.head,
      deleted: false,
    });
    this.audit("branch.created", { name, from });
  }

  protectBranch(branchName, overrides) {
    const branch = this.branches.get(branchName);
    if (!branch || branch.deleted) {
      throw new GovernanceError("Cannot protect an unavailable branch.");
    }
    this.policies.set(branchName, makePolicy(overrides));
    this.audit("branch.protected", { branchName });
  }

  push(branchName, author, message, paths, options = {}) {
    const member = this.member(author);
    const branch = this.branches.get(branchName);

    if (!branch || branch.deleted) {
      throw new GovernanceError("Branch does not exist.");
    }
    if (![Role.WRITE, Role.MAINTAIN, Role.ADMIN].includes(member.role)) {
      throw new GovernanceError("Member does not have push permission.");
    }

    const policy = this.policies.get(branchName);
    if (policy) {
      const bypass = policy.bypassRoles.has(member.role);
      if (!policy.allowDirectPush && !bypass) {
        throw new GovernanceError("Direct push is prohibited.");
      }
      if (options.force && !policy.allowForcePush) {
        throw new GovernanceError("Force push is prohibited.");
      }
    }

    const parents = options.force ? [] : [branch.head.id];
    branch.head = this.createCommit(author, message, paths, parents);
    this.audit("commit.pushed", { branchName, commit: branch.head.id });
    return branch.head;
  }

  getPR(id) {
    const pr = this.pullRequests.get(id);
    if (!pr) throw new GovernanceError(`Pull Request #${id} does not exist.`);
    return pr;
  }

  openPullRequest({
    title,
    author,
    source,
    target = "main",
    draft = false,
    strategy = MergeStrategy.SQUASH,
  }) {
    this.member(author);
    const sourceBranch = this.branches.get(source);
    const targetBranch = this.branches.get(target);

    if (
      !sourceBranch ||
      !targetBranch ||
      sourceBranch.deleted ||
      targetBranch.deleted ||
      source === target
    ) {
      throw new GovernanceError("Invalid Pull Request branch configuration.");
    }
    if (!Object.values(MergeStrategy).includes(strategy)) {
      throw new GovernanceError("Unsupported merge strategy.");
    }
    if (sourceBranch.head.id === targetBranch.head.id) {
      throw new GovernanceError("There are no proposed changes.");
    }

    const pr = {
      id: this.nextPR++,
      title: validateText(title, "Pull Request title"),
      author,
      source,
      target,
      baseCommit: targetBranch.head.id,
      headCommit: sourceBranch.head.id,
      state: draft ? PRState.DRAFT : PRState.OPEN,
      strategy,
      upToDate: true,
      conflicted: false,
      changedPaths: new Set(sourceBranch.head.changedPaths),
      requestedReviewers: new Set(),
      reviews: [],
      threads: [],
      checks: new Map(),
      mergedCommit: null,
    };

    this.pullRequests.set(pr.id, pr);
    this.audit("pull-request.opened", { id: pr.id, state: pr.state });
    return pr;
  }

  markReady(id, actor) {
    this.member(actor);
    const pr = this.getPR(id);
    if (pr.state !== PRState.DRAFT) {
      throw new GovernanceError("Only a draft Pull Request can be marked ready.");
    }
    pr.state = PRState.OPEN;
    this.audit("pull-request.ready", { id, actor });
  }

  requestReview(id, actor, reviewer) {
    const pr = this.getPR(id);
    this.member(actor);
    const candidate = this.member(reviewer);

    if (pr.state !== PRState.OPEN || reviewer === pr.author) {
      throw new GovernanceError("Review request is not valid for this Pull Request.");
    }
    if (candidate.role === Role.READ) {
      throw new GovernanceError("Read-only members cannot review changes.");
    }

    pr.requestedReviewers.add(reviewer);
    this.audit("review.requested", { id, reviewer });
  }

  submitReview(id, reviewer, state) {
    const pr = this.getPR(id);
    const member = this.member(reviewer);

    if (pr.state !== PRState.OPEN || reviewer === pr.author) {
      throw new GovernanceError("Reviewer is not eligible for this Pull Request.");
    }
    if (member.role === Role.READ) {
      throw new GovernanceError("Read-only members cannot submit reviews.");
    }
    if (![ReviewState.COMMENTED, ReviewState.APPROVED, ReviewState.CHANGES_REQUESTED]
      .includes(state)) {
      throw new GovernanceError("Invalid submitted review state.");
    }

    const review = Object.freeze({
      id: this.nextReview++,
      reviewer,
      state,
      commit: pr.headCommit,
      submittedAt: Date.now(),
    });

    pr.reviews.push(review);
    pr.requestedReviewers.delete(reviewer);
    this.audit("review.submitted", { id, reviewer, state });
    return review;
  }

  dismissReview(id, reviewId, actor) {
    const pr = this.getPR(id);
    if (![Role.MAINTAIN, Role.ADMIN].includes(this.member(actor).role)) {
      throw new GovernanceError("Only maintainers or administrators can dismiss reviews.");
    }

    const index = pr.reviews.findIndex((review) => review.id === reviewId);
    if (index < 0) throw new GovernanceError("Review does not exist.");

    pr.reviews[index] = Object.freeze({
      ...pr.reviews[index],
      state: ReviewState.DISMISSED,
    });
    this.audit("review.dismissed", { id, reviewId, actor });
  }

  addDiscussion(id, actor, path, line, body) {
    const pr = this.getPR(id);
    const member = this.member(actor);
    const normalizedPath = validatePath(path);

    if (pr.state !== PRState.OPEN || member.role === Role.READ) {
      throw new GovernanceError("This member cannot create a discussion here.");
    }
    if (!Number.isInteger(line) || line < 1) {
      throw new GovernanceError("Discussion line must be a positive integer.");
    }
    if (!pr.changedPaths.has(normalizedPath)) {
      throw new GovernanceError("Discussion must refer to a changed file.");
    }

    const thread = {
      id: this.nextThread++,
      author: actor,
      path: normalizedPath,
      line,
      body: validateText(body, "Discussion body"),
      resolved: false,
      replies: [],
    };

    pr.threads.push(thread);
    this.audit("discussion.created", { id, thread: thread.id });
    return thread;
  }

  resolveDiscussion(id, threadId, actor) {
    const pr = this.getPR(id);
    if (this.member(actor).role === Role.READ) {
      throw new GovernanceError("Read-only members cannot resolve discussions.");
    }

    const thread = pr.threads.find((item) => item.id === threadId);
    if (!thread) throw new GovernanceError("Discussion thread does not exist.");
    thread.resolved = true;
    this.audit("discussion.resolved", { id, threadId, actor });
  }

  recordCheck(id, context, state, commit = null, details = "") {
    const pr = this.getPR(id);
    if (![PRState.OPEN, PRState.DRAFT].includes(pr.state)) {
      throw new GovernanceError("Checks cannot be recorded on a closed Pull Request.");
    }
    if (!Object.values(CheckState).includes(state)) {
      throw new GovernanceError("Invalid status-check state.");
    }

    const checkedCommit = commit || pr.headCommit;
    const key = `${context}:${checkedCommit}`;
    pr.checks.set(key, {
      context: validateText(context, "Check context"),
      state,
      commit: checkedCommit,
      details: String(details),
      updatedAt: Date.now(),
    });
    this.audit("check.updated", { id, context, state, commit: checkedCommit });
  }

  /**
   * Executes independent checks concurrently. A rejected check is recorded
   * as a failure instead of being mistaken for a successful check.
   */
  async runChecks(id, checkDefinitions) {
    const pr = this.getPR(id);
    const snapshot = Object.freeze({
      id: pr.id,
      headCommit: pr.headCommit,
      changedPaths: [...pr.changedPaths],
    });

    const results = await Promise.allSettled(
      checkDefinitions.map(async ({ context, run }) => {
        if (typeof run !== "function") {
          throw new GovernanceError(`Check '${context}' has no executable function.`);
        }
        return { context, passed: Boolean(await run(snapshot)) };
      }),
    );

    results.forEach((result, index) => {
      const definition = checkDefinitions[index];
      if (result.status === "fulfilled") {
        this.recordCheck(
          id,
          definition.context,
          result.value.passed ? CheckState.SUCCESS : CheckState.FAILURE,
          snapshot.headCommit,
          result.value.passed ? "Check passed." : "Check returned false.",
        );
      } else {
        this.recordCheck(
          id,
          definition.context,
          CheckState.FAILURE,
          snapshot.headCommit,
          result.reason instanceof Error ? result.reason.message : "Check failed.",
        );
      }
    });

    return results;
  }

  latestReviews(pr) {
    const latest = new Map();
    for (const review of pr.reviews) {
      const previous = latest.get(review.reviewer);
      if (!previous || review.submittedAt > previous.submittedAt) {
        latest.set(review.reviewer, review);
      }
    }
    return latest;
  }

  evaluateMerge(id, actor) {
    const pr = this.getPR(id);
    const actorMember = this.member(actor);
    const policy = this.policies.get(pr.target) || makePolicy({
      requiredApprovals: 0,
      requiredChecks: [],
      requireResolvedThreads: false,
    });
    const sourceBranch = this.branches.get(pr.source);
    const targetBranch = this.branches.get(pr.target);
    const blockers = [];

    if (pr.state !== PRState.OPEN) blockers.push("Pull Request is not open.");
    if (!sourceBranch || sourceBranch.deleted) blockers.push("Source branch is unavailable.");
    if (!targetBranch || targetBranch.deleted) blockers.push("Target branch is unavailable.");
    if (sourceBranch && sourceBranch.head.id !== pr.headCommit) {
      blockers.push("Source branch contains commits not represented by this Pull Request.");
    }
    if (!pr.upToDate || (targetBranch && targetBranch.head.id !== pr.baseCommit)) {
      blockers.push("Source branch must be synchronized with the target branch.");
    }
    if (pr.conflicted) blockers.push("Merge conflicts must be resolved.");

    const bypass =
      (actorMember.role === Role.ADMIN && !policy.administratorsEnforced) ||
      policy.bypassRoles.has(actorMember.role);

    if (!bypass) {
      for (const requiredContext of policy.requiredChecks) {
        const check = pr.checks.get(`${requiredContext}:${pr.headCommit}`);
        if (!check || check.state !== CheckState.SUCCESS) {
          blockers.push(`Required check '${requiredContext}' has not succeeded on the current head.`);
        }
      }

      let approvals = 0;
      for (const [reviewer, review] of this.latestReviews(pr)) {
        const member = this.members.get(reviewer);
        if (
          !member ||
          !member.active ||
          reviewer === pr.author ||
          member.role === Role.READ
        ) {
          continue;
        }

        if (policy.dismissStaleApprovals && review.commit !== pr.headCommit) continue;
        if (review.state === ReviewState.CHANGES_REQUESTED) {
          blockers.push(`${reviewer} has requested changes.`);
        } else if (review.state === ReviewState.APPROVED) {
          approvals += 1;
        }
      }

      if (approvals < policy.requiredApprovals) {
        blockers.push(`Insufficient approvals: ${approvals}/${policy.requiredApprovals}.`);
      }

      if (policy.requireResolvedThreads) {
        const unresolved = pr.threads.filter((thread) => !thread.resolved).length;
        if (unresolved > 0) {
          blockers.push(`${unresolved} discussion thread(s) remain unresolved.`);
        }
      }

      if (policy.requireLinearHistory && pr.strategy === MergeStrategy.MERGE) {
        blockers.push("Merge commits are prohibited by the linear-history policy.");
      }
    }

    return Object.freeze({
      eligible: blockers.length === 0,
      blockers: Object.freeze(blockers),
      bypassApplied: bypass,
    });
  }

  merge(id, actor) {
    const pr = this.getPR(id);
    const decision = this.evaluateMerge(id, actor);

    if (!decision.eligible) {
      throw new GovernanceError(`Merge blocked: ${decision.blockers.join(" ")}`);
    }

    const target = this.branches.get(pr.target);
    const source = this.branches.get(pr.source);
    const paths = [...pr.changedPaths];

    const commit = this.createCommit(
      actor,
      `${pr.strategy} Pull Request #${id}: ${pr.title}`,
      paths,
      pr.strategy === MergeStrategy.MERGE
        ? [target.head.id, source.head.id]
        : [target.head.id],
    );

    target.head = commit;
    pr.state = PRState.MERGED;
    pr.mergedCommit = commit.id;
    this.audit("pull-request.merged", { id, commit: commit.id, strategy: pr.strategy });
    return commit;
  }

  close(id, actor) {
    const pr = this.getPR(id);
    const member = this.member(actor);
    if (![PRState.OPEN, PRState.DRAFT].includes(pr.state)) {
      throw new GovernanceError("Pull Request cannot be closed from its current state.");
    }
    if (actor !== pr.author && member.role === Role.READ) {
      throw new GovernanceError("Actor cannot close this Pull Request.");
    }

    pr.state = PRState.CLOSED;
    this.audit("pull-request.closed", { id, actor });
  }

  reopen(id, actor) {
    const pr = this.getPR(id);
    const member = this.member(actor);
    if (pr.state !== PRState.CLOSED) {
      throw new GovernanceError("Only a closed Pull Request can be reopened.");
    }
    if (actor !== pr.author && member.role === Role.READ) {
      throw new GovernanceError("Actor cannot reopen this Pull Request.");
    }

    pr.state = PRState.OPEN;
    this.audit("pull-request.reopened", { id, actor });
  }
}

async function main() {
  const repository = new RepositoryGovernance("quality-review-service", [
    { username: "developer", role: Role.WRITE },
    { username: "reviewer", role: Role.MAINTAIN },
    { username: "admin", role: Role.ADMIN },
  ]);

  repository.protectBranch("main", {
    requiredApprovals: 1,
    requiredChecks: ["unit-tests", "security-scan"],
    dismissStaleApprovals: true,
    requireResolvedThreads: true,
    requireLinearHistory: true,
    allowDirectPush: false,
    allowForcePush: false,
    administratorsEnforced: true,
  });

  repository.createBranch("feature/review-quality");
  repository.push(
    "feature/review-quality",
    "developer",
    "Add review-quality rules",
    ["src/review-quality.js", "test/review-quality.test.js"],
  );

  const pr = repository.openPullRequest({
    title: "Add review-quality enforcement",
    author: "developer",
    source: "feature/review-quality",
    target: "main",
    strategy: MergeStrategy.SQUASH,
  });

  repository.requestReview(pr.id, "developer", "reviewer");
  repository.submitReview(pr.id, "reviewer", ReviewState.APPROVED);

  const thread = repository.addDiscussion(
    pr.id,
    "reviewer",
    "src/review-quality.js",
    18,
    "The policy covers stale approvals and unresolved discussions.",
  );
  repository.resolveDiscussion(pr.id, thread.id, "developer");

  await repository.runChecks(pr.id, [
    {
      context: "unit-tests",
      run: async ({ changedPaths }) => changedPaths.some((path) => path.startsWith("test/")),
    },
    {
      context: "security-scan",
      run: async ({ changedPaths }) => !changedPaths.some((path) => path.endsWith(".secret")),
    },
  ]);

  const decision = repository.evaluateMerge(pr.id, "developer");
  process.stdout.write(`Merge eligible: ${decision.eligible}\n`);

  if (!decision.eligible) {
    process.stdout.write(`Blockers: ${decision.blockers.join("; ")}\n`);
    process.exitCode = 1;
    return;
  }

  repository.merge(pr.id, "developer");

  try {
    repository.push("main", "developer", "Unreviewed update", ["src/unsafe.js"]);
  } catch (error) {
    process.stdout.write(`Expected governance rejection: ${error.message}\n`);
  }
}

main().catch((error) => {
  process.stderr.write(`Fatal error: ${error.message}\n`);
  process.exitCode = 1;
});
