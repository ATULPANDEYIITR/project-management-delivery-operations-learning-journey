#!/usr/bin/env node
"use strict";

/**
 * Event-driven repository quality gate.
 * Run with Node.js 18 or later.
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

const PRState = Object.freeze({
  OPEN: "open",
  MERGED: "merged",
  CLOSED: "closed",
});

const ReviewState = Object.freeze({
  COMMENTED: "commented",
  APPROVED: "approved",
  CHANGES_REQUESTED: "changes_requested",
  DISMISSED: "dismissed",
});

const CheckState = Object.freeze({
  PENDING: "pending",
  PASSED: "passed",
  FAILED: "failed",
});

class DomainError extends Error {
  constructor(message) {
    super(message);
    this.name = "DomainError";
  }
}

function requireText(value, field) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new DomainError(`${field} must be a non-empty string.`);
  }
}

class RepositoryBranch {
  constructor(name, commits = [], protectedBranch = false) {
    requireText(name, "Branch name");
    this.name = name;
    this.commits = [...commits];
    this.protectedBranch = protectedBranch;
  }

  get head() {
    return this.commits.length
      ? this.commits[this.commits.length - 1].id
      : null;
  }
}

class RepositoryPolicy {
  constructor({
    requiredApprovals = 2,
    requiredChecks = ["unit-tests", "security-scan"],
    requireResolvedConversations = true,
    requireLinearHistory = true,
    allowDirectPush = false,
    allowForcePush = false,
    allowDeletion = false,
    allowAdminBypass = false,
  } = {}) {
    if (!Number.isInteger(requiredApprovals) || requiredApprovals < 0) {
      throw new DomainError("requiredApprovals must be a non-negative integer.");
    }

    this.requiredApprovals = requiredApprovals;
    this.requiredChecks = new Set(requiredChecks);
    this.requireResolvedConversations = requireResolvedConversations;
    this.requireLinearHistory = requireLinearHistory;
    this.allowDirectPush = allowDirectPush;
    this.allowForcePush = allowForcePush;
    this.allowDeletion = allowDeletion;
    this.allowAdminBypass = allowAdminBypass;
  }
}

class PullRequest extends EventEmitter {
  constructor({
    number,
    author,
    source,
    target,
    eligibleReviewers,
    policy,
    draft = false,
  }) {
    super();

    if (!Number.isSafeInteger(number) || number <= 0) {
      throw new DomainError("PR number must be a positive safe integer.");
    }
    requireText(author, "Author");

    if (!(source instanceof RepositoryBranch) ||
        !(target instanceof RepositoryBranch)) {
      throw new DomainError("Source and target must be repository branches.");
    }
    if (source.name === target.name) {
      throw new DomainError("Source and target branches must differ.");
    }
    if (!(policy instanceof RepositoryPolicy)) {
      throw new DomainError("A repository policy is required.");
    }

    this.number = number;
    this.author = author;
    this.source = source;
    this.target = target;
    this.eligibleReviewers = new Set(eligibleReviewers);
    this.policy = policy;
    this.draft = Boolean(draft);
    this.state = PRState.OPEN;
    this.reviews = [];
    this.checks = new Map();
    this.conversations = new Map();
    this.baseHead = target.head;
    this.mergeRecord = null;
  }

  requireOpen() {
    if (this.state !== PRState.OPEN) {
      throw new DomainError("Operation requires an open PR.");
    }
  }

  addCommit(message, author = this.author) {
    this.requireOpen();
    requireText(message, "Commit message");
    if (author !== this.author) {
      throw new DomainError("Only the PR author may update this source branch.");
    }

    const id = crypto.createHash("sha256")
      .update(`${this.number}:${this.source.commits.length}:${message}:${author}`)
      .digest("hex")
      .slice(0, 12);

    this.source.commits.push({ id, message, author, parent: this.source.head });
    this.emit("source.updated", { number: this.number, head: id });
    return id;
  }

  markReady() {
    this.requireOpen();
    if (!this.draft) return;
    this.draft = false;
    this.emit("pr.ready", { number: this.number });
  }

  synchronizeBase() {
    this.requireOpen();
    this.baseHead = this.target.head;
    this.emit("base.synchronized", { number: this.number, baseHead: this.baseHead });
  }

  submitReview({ reviewer, state, commitId, comments = [] }) {
    this.requireOpen();
    if (this.draft) throw new DomainError("Draft PRs are not review-ready.");
    requireText(reviewer, "Reviewer");

    if (reviewer === this.author ||
        !this.eligibleReviewers.has(reviewer)) {
      throw new DomainError("Reviewer is not eligible for this PR.");
    }
    if (!Object.values(ReviewState).includes(state) ||
        state === ReviewState.DISMISSED) {
      throw new DomainError("Invalid submitted review state.");
    }
    if (commitId !== this.source.head) {
      throw new DomainError("Review must target the current source HEAD.");
    }
    if (!Array.isArray(comments) ||
        comments.some(comment => typeof comment !== "string")) {
      throw new DomainError("Review comments must be strings.");
    }

    const review = Object.freeze({
      reviewer,
      state,
      commitId,
      comments: [...comments],
      timestamp: new Date().toISOString(),
    });

    this.reviews.push(review);
    this.emit("review.submitted", { number: this.number, reviewer, state });
  }

  dismissReview(reviewer) {
    this.requireOpen();
    const index = this.reviews.findLastIndex(
      review => review.reviewer === reviewer &&
        review.state !== ReviewState.DISMISSED
    );

    if (index < 0) throw new DomainError("No active review to dismiss.");

    const old = this.reviews[index];
    this.reviews[index] = Object.freeze({
      ...old,
      state: ReviewState.DISMISSED,
      dismissedAt: new Date().toISOString(),
    });

    this.emit("review.dismissed", { number: this.number, reviewer });
  }

  recordCheck(name, state, commitId = this.source.head) {
    this.requireOpen();
    requireText(name, "Check name");
    if (!Object.values(CheckState).includes(state)) {
      throw new DomainError("Invalid check state.");
    }

    this.checks.set(`${commitId}:${name}`, { name, state, commitId });
    this.emit("check.updated", { number: this.number, name, state, commitId });
  }

  openConversation(id, file, line, text) {
    this.requireOpen();
    requireText(id, "Conversation ID");
    requireText(file, "File");
    requireText(text, "Comment");
    if (!Number.isInteger(line) || line < 1) {
      throw new DomainError("Line must be a positive integer.");
    }

    this.conversations.set(id, {
      id, file, line, text, resolved: false,
    });
    this.emit("conversation.opened", { number: this.number, id });
  }

  resolveConversation(id) {
    this.requireOpen();
    const conversation = this.conversations.get(id);
    if (!conversation || conversation.resolved) {
      throw new DomainError("Conversation is missing or already resolved.");
    }

    conversation.resolved = true;
    this.emit("conversation.resolved", { number: this.number, id });
  }

  getCurrentReviews() {
    const latest = new Map();

    for (const review of this.reviews) {
      latest.set(review.reviewer, review);
    }

    return [...latest.values()].filter(
      review => review.commitId === this.source.head
    );
  }

  evaluateMerge() {
    const blockers = [];

    if (this.state !== PRState.OPEN) {
      return { eligible: false, blockers: ["PR is not open."] };
    }

    if (this.draft) blockers.push("PR is a draft.");
    if (this.source.commits.length === 0) blockers.push("No source commits.");

    if (this.baseHead !== this.target.head) {
      blockers.push("Target branch changed; synchronize the base.");
    }

    const reviews = this.getCurrentReviews();
    const approvals = new Set(
      reviews
        .filter(review => review.state === ReviewState.APPROVED)
        .map(review => review.reviewer)
    );

    for (const review of reviews) {
      if (review.state === ReviewState.CHANGES_REQUESTED) {
        blockers.push(`${review.reviewer} requested changes.`);
      }
    }

    if (approvals.size < this.policy.requiredApprovals) {
      blockers.push(
        `Requires ${this.policy.requiredApprovals} current approvals; ` +
        `has ${approvals.size}.`
      );
    }

    for (const name of this.policy.requiredChecks) {
      const check = this.checks.get(`${this.source.head}:${name}`);
      if (!check || check.state !== CheckState.PASSED) {
        blockers.push(`Required check '${name}' has not passed.`);
      }
    }

    if (this.policy.requireResolvedConversations) {
      const unresolved = [...this.conversations.values()].filter(
        conversation => !conversation.resolved
      );
      if (unresolved.length) {
        blockers.push(`${unresolved.length} unresolved conversation(s).`);
      }
    }

    if (this.policy.requireLinearHistory) {
      const ids = new Set();
      for (const commit of this.source.commits) {
        if (ids.has(commit.id)) blockers.push("Duplicate commit ID.");
        ids.add(commit.id);
      }
    }

    return { eligible: blockers.length === 0, blockers, approvals: approvals.size };
  }

  merge(actor) {
    this.requireOpen();

    if (!this.eligibleReviewers.has(actor) && actor !== this.author) {
      throw new DomainError("Actor lacks merge permission.");
    }

    const evaluation = this.evaluateMerge();
    if (!evaluation.eligible) {
      throw new DomainError(`Merge blocked: ${evaluation.blockers.join(" ")}`);
    }

    const id = crypto.createHash("sha256")
      .update(`${this.number}:${this.source.head}:${this.target.head}:${actor}`)
      .digest("hex")
      .slice(0, 12);

    this.target.commits.push({
      id,
      message: `Merge PR #${this.number}`,
      author: actor,
      parent: this.target.head,
      sourceHead: this.source.head,
    });

    this.mergeRecord = { id, actor, mergedAt: new Date().toISOString() };
    this.state = PRState.MERGED;
    this.emit("pr.merged", { number: this.number, mergeId: id });
    return this.mergeRecord;
  }

  close() {
    this.requireOpen();
    this.state = PRState.CLOSED;
    this.emit("pr.closed", { number: this.number });
  }

  reopen() {
    if (this.state !== PRState.CLOSED) {
      throw new DomainError("Only a closed, unmerged PR can be reopened.");
    }
    this.state = PRState.OPEN;
    this.baseHead = this.target.head;
    this.emit("pr.reopened", { number: this.number });
  }
}

function attemptDirectPush(branch, commit, policy, actorIsAdmin = false) {
  if (
    branch.protectedBranch &&
    !policy.allowDirectPush &&
    !(actorIsAdmin && policy.allowAdminBypass)
  ) {
    throw new DomainError("Protected branch rejects direct pushes.");
  }
  branch.commits.push(commit);
}

function runScenario() {
  const policy = new RepositoryPolicy();
  const main = new RepositoryBranch(
    "main",
    [{ id: "base-001", message: "Initial release", author: "maintainer" }],
    true
  );
  const feature = new RepositoryBranch("feature/quality-gates");

  const pr = new PullRequest({
    number: 73,
    author: "developer",
    source: feature,
    target: main,
    eligibleReviewers: ["reviewer-a", "reviewer-b", "maintainer"],
    policy,
    draft: true,
  });

  // Events provide an auditable record without coupling the evaluator to a UI.
  pr.on("review.submitted", event => {
    console.log("Event:", event);
  });
  pr.on("pr.merged", event => {
    console.log("Event:", event);
  });

  const head = pr.addCommit("Enforce input quality checks");
  pr.markReady();
  pr.openConversation("thread-1", "src/validator.js", 18,
    "Handle empty identifiers.");
  pr.submitReview({
    reviewer: "reviewer-a",
    state: ReviewState.APPROVED,
    commitId: head,
  });
  pr.submitReview({
    reviewer: "reviewer-b",
    state: ReviewState.APPROVED,
    commitId: head,
  });

  pr.recordCheck("unit-tests", CheckState.PASSED);
  pr.recordCheck("security-scan", CheckState.PASSED);

  console.log("Before discussion resolution:", pr.evaluateMerge());
  pr.resolveConversation("thread-1");
  console.log("After discussion resolution:", pr.evaluateMerge());

  // Updating the source HEAD invalidates approvals tied to the older commit.
  const newHead = pr.addCommit("Reject malformed identifiers");
  console.log("After source update:", pr.evaluateMerge());

  pr.submitReview({
    reviewer: "reviewer-a",
    state: ReviewState.APPROVED,
    commitId: newHead,
  });
  pr.submitReview({
    reviewer: "reviewer-b",
    state: ReviewState.APPROVED,
    commitId: newHead,
  });
  pr.recordCheck("unit-tests", CheckState.PASSED);
  pr.recordCheck("security-scan", CheckState.PASSED);

  const result = pr.evaluateMerge();
  if (!result.eligible) {
    throw new DomainError(result.blockers.join("; "));
  }

  console.log("Merge record:", pr.merge("maintainer"));

  try {
    attemptDirectPush(
      main,
      { id: "unauthorized", message: "Skip review", author: "developer" },
      policy
    );
  } catch (error) {
    console.log("Security control:", error.message);
  }
}

try {
  runScenario();
} catch (error) {
  console.error(`${error.name}: ${error.message}`);
  process.exitCode = 1;
}
