"use strict";

/*
 * Event-driven repository governance model.
 *
 * Pull Requests provide the change workflow.
 * Code review records reviewer evaluation.
 * Approvals represent review decisions.
 * Branch protection turns repository policy into merge gates.
 *
 * The resource-review dimension is represented by changed-file counts and
 * estimated review effort so that review capacity becomes an explicit
 * engineering resource rather than an informal assumption.
 */

const EventEmitter = require("node:events");

const PR_STATE = Object.freeze({
  DRAFT: "draft",
  OPEN: "open",
  CLOSED: "closed",
  MERGED: "merged",
});

const REVIEW_STATE = Object.freeze({
  COMMENTED: "commented",
  APPROVED: "approved",
  CHANGES_REQUESTED: "changes_requested",
  DISMISSED: "dismissed",
});

class ValidationError extends Error {}

class PullRequest extends EventEmitter {
  constructor({ number, source, target, title, draft = false }) {
    super();

    if (!Number.isInteger(number) || number <= 0) {
      throw new ValidationError("PR number must be a positive integer.");
    }
    if (!source || !target || source === target) {
      throw new ValidationError(
        "Source and target branches must be different non-empty values."
      );
    }
    if (!title || title.trim().length < 5) {
      throw new ValidationError("PR title is too short.");
    }

    this.number = number;
    this.source = source;
    this.target = target;
    this.title = title.trim();
    this.state = draft ? PR_STATE.DRAFT : PR_STATE.OPEN;
    this.commits = [];
    this.reviews = [];
    this.comments = [];
    this.statusChecks = new Map();
    this.unresolvedConversations = new Set();
    this.synchronized = true;
    this.hasConflicts = false;
    this.revision = 1;
  }

  open() {
    if (this.state !== PR_STATE.DRAFT) {
      throw new ValidationError("Only draft PRs can be opened.");
    }

    this.state = PR_STATE.OPEN;
    this.emit("stateChanged", {
      number: this.number,
      state: this.state,
    });
  }

  addCommit({ sha, message, changedFiles, additions, deletions }) {
    if (![PR_STATE.DRAFT, PR_STATE.OPEN].includes(this.state)) {
      throw new ValidationError("Cannot add commits to a closed or merged PR.");
    }

    if (!/^[a-f0-9]{7,40}$/i.test(sha)) {
      throw new ValidationError("Commit SHA must be 7 to 40 hexadecimal characters.");
    }

    if (!message || !message.trim()) {
      throw new ValidationError("Commit message cannot be empty.");
    }

    for (const value of [changedFiles, additions, deletions]) {
      if (!Number.isInteger(value) || value < 0) {
        throw new ValidationError("Commit statistics must be non-negative integers.");
      }
    }

    this.commits.push({
      sha,
      message: message.trim(),
      changedFiles,
      additions,
      deletions,
    });

    this.revision += 1;
    this.synchronized = true;
    this.emit("commitAdded", { number: this.number, sha });
  }

  requestReview(reviewer) {
    if (this.state !== PR_STATE.OPEN) {
      throw new ValidationError("Review requests require an open PR.");
    }

    if (!reviewer || reviewer.trim().length === 0) {
      throw new ValidationError("Reviewer name is required.");
    }

    this.emit("reviewRequested", {
      number: this.number,
      reviewer: reviewer.trim(),
    });
  }

  submitReview({ reviewer, state, body = "" }) {
    if (this.state !== PR_STATE.OPEN) {
      throw new ValidationError("Only open PRs can receive reviews.");
    }

    if (!Object.values(REVIEW_STATE).includes(state)) {
      throw new ValidationError("Unknown review state.");
    }

    this.reviews.push({
      reviewer,
      state,
      body: body.trim(),
      revision: this.revision,
      createdAt: new Date().toISOString(),
    });

    this.emit("reviewSubmitted", {
      number: this.number,
      reviewer,
      state,
    });
  }

  addComment({ reviewer, text, conversationId }) {
    if (this.state !== PR_STATE.OPEN) {
      throw new ValidationError("Comments require an open PR.");
    }

    if (!text || text.trim().length < 3) {
      throw new ValidationError("Review comment is too short.");
    }

    this.comments.push({
      reviewer,
      text: text.trim(),
      conversationId,
      createdAt: new Date().toISOString(),
    });

    this.unresolvedConversations.add(conversationId);

    this.emit("conversationOpened", {
      number: this.number,
      conversationId,
    });
  }

  resolveConversation(conversationId) {
    if (!this.unresolvedConversations.has(conversationId)) {
      throw new ValidationError("Conversation is not unresolved.");
    }

    this.unresolvedConversations.delete(conversationId);

    this.emit("conversationResolved", {
      number: this.number,
      conversationId,
    });
  }

  setStatusCheck(name, passed) {
    if (!name || typeof passed !== "boolean") {
      throw new ValidationError("Status check requires a name and boolean result.");
    }

    this.statusChecks.set(name, {
      passed,
      revision: this.revision,
      completedAt: new Date().toISOString(),
    });

    this.emit("statusChanged", {
      number: this.number,
      name,
      passed,
    });
  }

  updateFromBaseBranch({ conflicts }) {
    if (this.state !== PR_STATE.OPEN) {
      throw new ValidationError("Only open PRs can synchronize with base.");
    }

    this.synchronized = false;
    this.hasConflicts = conflicts;
    this.revision += 1;

    this.emit("baseUpdated", {
      number: this.number,
      conflicts,
    });
  }

  synchronize() {
    if (this.state !== PR_STATE.OPEN) {
      throw new ValidationError("Only open PRs can synchronize.");
    }

    this.synchronized = true;
    this.hasConflicts = false;

    this.emit("synchronized", { number: this.number });
  }

  close() {
    if (this.state === PR_STATE.MERGED) {
      throw new ValidationError("Merged PRs cannot be closed.");
    }

    this.state = PR_STATE.CLOSED;
    this.emit("stateChanged", {
      number: this.number,
      state: this.state,
    });
  }

  reopen() {
    if (this.state !== PR_STATE.CLOSED) {
      throw new ValidationError("Only closed PRs can be reopened.");
    }

    this.state = PR_STATE.OPEN;
    this.emit("stateChanged", {
      number: this.number,
      state: this.state,
    });
  }

  getChangedFiles() {
    return this.commits.reduce((sum, commit) => sum + commit.changedFiles, 0);
  }

  estimateReviewMinutes() {
    return Math.max(10, this.getChangedFiles() * 4);
  }

  latestReviews() {
    const latest = new Map();

    for (const review of this.reviews) {
      latest.set(review.reviewer, review);
    }

    return latest;
  }
}

class GovernancePolicy {
  constructor({
    requiredApprovals,
    eligibleReviewers,
    requiredChecks,
    requireResolvedConversations = true,
    dismissStaleApprovals = true,
    allowedMergeMethods = ["squash"],
  }) {
    this.requiredApprovals = requiredApprovals;
    this.eligibleReviewers = new Set(eligibleReviewers);
    this.requiredChecks = new Set(requiredChecks);
    this.requireResolvedConversations = requireResolvedConversations;
    this.dismissStaleApprovals = dismissStaleApprovals;
    this.allowedMergeMethods = new Set(allowedMergeMethods);
  }

  evaluate(pr, mergeMethod) {
    const failures = [];

    if (pr.state !== PR_STATE.OPEN) {
      failures.push("PR must be open.");
    }

    if (pr.commits.length === 0) {
      failures.push("PR must contain at least one commit.");
    }

    if (!pr.synchronized) {
      failures.push("PR must be synchronized with the base branch.");
    }

    if (pr.hasConflicts) {
      failures.push("Merge conflicts must be resolved.");
    }

    if (!this.allowedMergeMethods.has(mergeMethod)) {
      failures.push(`Merge method '${mergeMethod}' is not permitted.`);
    }

    const latestReviews = pr.latestReviews();

    let approvals = 0;
    let changesRequested = false;

    for (const [reviewer, review] of latestReviews) {
      if (!this.eligibleReviewers.has(reviewer)) {
        continue;
      }

      if (
        review.state === REVIEW_STATE.APPROVED &&
        (!this.dismissStaleApprovals || review.revision === pr.revision)
      ) {
        approvals += 1;
      }

      if (review.state === REVIEW_STATE.CHANGES_REQUESTED) {
        changesRequested = true;
      }
    }

    if (changesRequested) {
      failures.push("An eligible reviewer currently requests changes.");
    }

    if (approvals < this.requiredApprovals) {
      failures.push(
        `Approval requirement is ${this.requiredApprovals}; current count is ${approvals}.`
      );
    }

    for (const check of this.requiredChecks) {
      const result = pr.statusChecks.get(check);

      if (!result) {
        failures.push(`Required check '${check}' is missing.`);
      } else if (!result.passed) {
        failures.push(`Required check '${check}' failed.`);
      } else if (this.dismissStaleApprovals && result.revision !== pr.revision) {
        failures.push(`Required check '${check}' is stale.`);
      }
    }

    if (
      this.requireResolvedConversations &&
      pr.unresolvedConversations.size > 0
    ) {
      failures.push(
        `${pr.unresolvedConversations.size} review conversation(s) remain unresolved.`
      );
    }

    return {
      eligible: failures.length === 0,
      failures,
      approvalCount: approvals,
    };
  }
}

function attachAuditLogging(pr) {
  const events = [
    "stateChanged",
    "commitAdded",
    "reviewRequested",
    "reviewSubmitted",
    "conversationOpened",
    "conversationResolved",
    "statusChanged",
    "baseUpdated",
    "synchronized",
  ];

  for (const eventName of events) {
    pr.on(eventName, (event) => {
      console.log(`[audit] ${eventName}:`, event);
    });
  }
}

async function main() {
  const pr = new PullRequest({
    number: 305,
    source: "feature/cost-resource-review",
    target: "main",
    title: "Review repository resource usage and governance",
    draft: true,
  });

  attachAuditLogging(pr);

  pr.open();

  pr.addCommit({
    sha: "a1b2c3d4",
    message: "Add repository resource accounting",
    changedFiles: 6,
    additions: 180,
    deletions: 25,
  });

  pr.addCommit({
    sha: "b2c3d4e5",
    message: "Add merge governance checks",
    changedFiles: 4,
    additions: 130,
    deletions: 18,
  });

  pr.requestReview("alice");
  pr.requestReview("bob");

  pr.submitReview({
    reviewer: "alice",
    state: REVIEW_STATE.APPROVED,
    body: "Scope and resource impact reviewed.",
  });

  pr.submitReview({
    reviewer: "bob",
    state: REVIEW_STATE.CHANGES_REQUESTED,
    body: "Please resolve the status-check policy issue.",
  });

  pr.addComment({
    reviewer: "bob",
    text: "The required security check is missing.",
    conversationId: "conv-17",
  });

  pr.setStatusCheck("unit-tests", true);
  pr.setStatusCheck("security-scan", true);

  const policy = new GovernancePolicy({
    requiredApprovals: 2,
    eligibleReviewers: ["alice", "bob", "carol"],
    requiredChecks: ["unit-tests", "security-scan"],
    requireResolvedConversations: true,
    dismissStaleApprovals: true,
    allowedMergeMethods: ["squash"],
  });

  console.log("\nResource review:");
  console.log(`Changed files: ${pr.getChangedFiles()}`);
  console.log(`Estimated review effort: ${pr.estimateReviewMinutes()} minutes`);

  let result = policy.evaluate(pr, "squash");
  console.log("\nInitial merge evaluation:");
  console.log(result);

  pr.resolveConversation("conv-17");

  pr.submitReview({
    reviewer: "bob",
    state: REVIEW_STATE.APPROVED,
    body: "The required checks are now present.",
  });

  result = policy.evaluate(pr, "squash");
  console.log("\nAfter review resolution:");
  console.log(result);

  if (result.eligible) {
    pr.state = PR_STATE.MERGED;
    console.log(`PR #${pr.number} merged.`);
  }

  // A base-branch update changes the revision. With stale-approval dismissal
  // enabled, previous approvals are no longer sufficient until revalidated.
  if (pr.state === PR_STATE.MERGED) {
    console.log("Merged PR remains immutable under this simulation.");
  }
}

main().catch((error) => {
  console.error(`Governance evaluation failed: ${error.message}`);
  process.exitCode = 1;
});
