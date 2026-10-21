"use strict";

/*
 * Interactive repository-governance model.
 *
 * The implementation uses an event-driven design: repository mutations emit
 * events, while policy evaluation remains a separate deterministic operation.
 * This keeps workflow events distinct from the rules that decide whether
 * a Pull Request can merge.
 */

const { EventEmitter } = require("node:events");

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
  PASSED: "passed",
  FAILED: "failed",
});

const MergeStrategy = Object.freeze({
  MERGE_COMMIT: "merge_commit",
  SQUASH: "squash",
  REBASE: "rebase",
});

class ValidationError extends Error {}
class GovernanceError extends Error {}

function requiredString(value, fieldName) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new ValidationError(`${fieldName} must be a non-empty string`);
  }
  return value.trim();
}

class Repository extends EventEmitter {
  constructor(name) {
    super();
    this.name = requiredString(name, "Repository name");
    this.branches = new Map();
    this.protections = new Map();
    this.pullRequests = new Map();
    this.nextPrNumber = 1;
  }

  createBranch(name, sha) {
    requiredString(name, "Branch name");
    requiredString(sha, "Branch SHA");

    if (this.branches.has(name)) {
      throw new GovernanceError(`Branch already exists: ${name}`);
    }

    this.branches.set(name, sha);
    this.emit("branch.created", { branch: name, sha });
  }

  updateBranch(name, sha) {
    requiredString(sha, "Branch SHA");

    if (!this.branches.has(name)) {
      throw new GovernanceError(`Unknown branch: ${name}`);
    }

    this.branches.set(name, sha);
    this.emit("branch.updated", { branch: name, sha });
  }

  protectBranch(policy) {
    if (!this.branches.has(policy.branch)) {
      throw new GovernanceError(`Cannot protect unknown branch: ${policy.branch}`);
    }

    if (!Number.isInteger(policy.requiredReviews) || policy.requiredReviews < 0) {
      throw new ValidationError("requiredReviews must be a non-negative integer");
    }

    const normalized = {
      branch: policy.branch,
      requiredReviews: policy.requiredReviews,
      requiredChecks: new Set(policy.requiredChecks ?? []),
      dismissStaleReviews: policy.dismissStaleReviews ?? true,
      requireConversationResolution:
        policy.requireConversationResolution ?? true,
      restrictDirectPush: policy.restrictDirectPush ?? true,
      allowForcePush: policy.allowForcePush ?? false,
      allowDeletion: policy.allowDeletion ?? false,
      requireLinearHistory: policy.requireLinearHistory ?? false,
      allowedMergeStrategies: new Set(
        policy.allowedMergeStrategies ?? [
          MergeStrategy.SQUASH,
          MergeStrategy.REBASE,
        ]
      ),
      bypassUsers: new Set(policy.bypassUsers ?? []),
    };

    this.protections.set(policy.branch, normalized);
    this.emit("branch.protected", { policy: normalized });
  }

  createPullRequest({
    title,
    sourceBranch,
    targetBranch,
    author,
    draft = false,
  }) {
    requiredString(title, "Pull Request title");
    requiredString(sourceBranch, "Source branch");
    requiredString(targetBranch, "Target branch");
    requiredString(author, "Author");

    if (!this.branches.has(sourceBranch)) {
      throw new GovernanceError(`Unknown source branch: ${sourceBranch}`);
    }

    if (!this.branches.has(targetBranch)) {
      throw new GovernanceError(`Unknown target branch: ${targetBranch}`);
    }

    if (sourceBranch === targetBranch) {
      throw new ValidationError("Source and target branches must differ");
    }

    const number = this.nextPrNumber++;
    const baseSha = this.branches.get(targetBranch);

    const pr = {
      number,
      title,
      sourceBranch,
      targetBranch,
      author,
      state: draft ? PRState.DRAFT : PRState.OPEN,
      commits: [],
      reviews: [],
      checks: new Map(),
      conversations: new Map(),
      mergeConflicts: false,
      mergeStrategy: MergeStrategy.SQUASH,
      baseShaAtCreation: baseSha,
      currentBaseSha: baseSha,
    };

    this.pullRequests.set(number, pr);
    this.emit("pull_request.created", { number, state: pr.state });

    return pr;
  }

  addCommit(number, commit) {
    const pr = this.getPullRequest(number);

    if (![PRState.DRAFT, PRState.OPEN].includes(pr.state)) {
      throw new GovernanceError("Cannot modify an inactive Pull Request");
    }

    requiredString(commit.sha, "Commit SHA");
    requiredString(commit.message, "Commit message");
    requiredString(commit.author, "Commit author");

    pr.commits.push({
      sha: commit.sha,
      message: commit.message,
      author: commit.author,
    });

    this.updateBranch(pr.sourceBranch, commit.sha);

    if (this.protections.get(pr.targetBranch)?.dismissStaleReviews) {
      pr.reviews = pr.reviews.filter(
        (review) => review.commitSha === commit.sha
      );
    }

    // Status checks are also commit-specific. A new commit requires new results.
    pr.checks.clear();

    this.emit("pull_request.commit_added", {
      number,
      sha: commit.sha,
    });
  }

  requestReview(number, reviewer) {
    const pr = this.getPullRequest(number);
    requiredString(reviewer, "Reviewer");

    if (pr.state !== PRState.OPEN) {
      throw new GovernanceError("Review requests require an open Pull Request");
    }

    if (reviewer === pr.author) {
      throw new GovernanceError("An author cannot review their own Pull Request");
    }

    this.emit("review.requested", { number, reviewer });
  }

  submitReview(number, { reviewer, state, commentCount = 0 }) {
    const pr = this.getPullRequest(number);
    const latest = this.latestCommit(pr);

    requiredString(reviewer, "Reviewer");

    if (!Object.values(ReviewState).includes(state)) {
      throw new ValidationError(`Invalid review state: ${state}`);
    }

    if (reviewer === pr.author) {
      throw new GovernanceError("Self-review is not permitted");
    }

    if (!latest) {
      throw new GovernanceError("A review requires at least one commit");
    }

    if (!Number.isInteger(commentCount) || commentCount < 0) {
      throw new ValidationError("commentCount must be a non-negative integer");
    }

    pr.reviews.push({
      reviewer,
      state,
      commentCount,
      commitSha: latest.sha,
    });

    this.emit("review.submitted", {
      number,
      reviewer,
      state,
      commitSha: latest.sha,
    });
  }

  setStatusCheck(number, name, state) {
    const pr = this.getPullRequest(number);
    const latest = this.latestCommit(pr);

    requiredString(name, "Status check name");

    if (!latest) {
      throw new GovernanceError("Status checks require a commit");
    }

    if (!Object.values(CheckState).includes(state)) {
      throw new ValidationError(`Invalid check state: ${state}`);
    }

    pr.checks.set(name, {
      name,
      state,
      commitSha: latest.sha,
    });

    this.emit("status_check.updated", { number, name, state });
  }

  addConversation(number, conversationId) {
    const pr = this.getPullRequest(number);

    requiredString(conversationId, "Conversation ID");

    pr.conversations.set(conversationId, {
      resolved: false,
    });

    this.emit("conversation.opened", {
      number,
      conversationId,
    });
  }

  resolveConversation(number, conversationId) {
    const pr = this.getPullRequest(number);
    const conversation = pr.conversations.get(conversationId);

    if (!conversation) {
      throw new GovernanceError(`Unknown conversation: ${conversationId}`);
    }

    conversation.resolved = true;

    this.emit("conversation.resolved", {
      number,
      conversationId,
    });
  }

  synchronizeBase(number, newBaseSha) {
    const pr = this.getPullRequest(number);
    requiredString(newBaseSha, "New base SHA");

    pr.currentBaseSha = newBaseSha;
    pr.mergeConflicts = newBaseSha !== pr.baseShaAtCreation;

    if (this.protections.get(pr.targetBranch)?.dismissStaleReviews) {
      const latest = this.latestCommit(pr);
      pr.reviews = latest
        ? pr.reviews.filter((review) => review.commitSha === latest.sha)
        : [];
    }

    this.emit("pull_request.synchronized", {
      number,
      newBaseSha,
      mergeConflicts: pr.mergeConflicts,
    });
  }

  setMergeStrategy(number, strategy) {
    const pr = this.getPullRequest(number);

    if (!Object.values(MergeStrategy).includes(strategy)) {
      throw new ValidationError(`Invalid merge strategy: ${strategy}`);
    }

    pr.mergeStrategy = strategy;
  }

  evaluateMerge(number, actor) {
    const pr = this.getPullRequest(number);
    const policy = this.protections.get(pr.targetBranch);
    const reasons = [];

    requiredString(actor, "Merge actor");

    if (!policy) {
      reasons.push("Target branch has no protection policy");
      return { allowed: false, reasons };
    }

    if (policy.bypassUsers.has(actor)) {
      return {
        allowed: true,
        reasons: ["Configured governance bypass applies to this actor"],
      };
    }

    if (pr.state !== PRState.OPEN) {
      reasons.push("Pull Request is not open");
    }

    const latest = this.latestCommit(pr);

    if (!latest) {
      reasons.push("Pull Request has no commits");
    }

    if (pr.mergeConflicts) {
      reasons.push("Merge conflicts are unresolved");
    }

    if (!policy.allowedMergeStrategies.has(pr.mergeStrategy)) {
      reasons.push(
        `Merge strategy ${pr.mergeStrategy} is not permitted`
      );
    }

    const approvals = new Map();

    if (latest) {
      for (const review of pr.reviews) {
        if (review.commitSha !== latest.sha) continue;

        if (review.state === ReviewState.APPROVED) {
          approvals.set(review.reviewer, review);
        }

        if (review.state === ReviewState.CHANGES_REQUESTED) {
          approvals.delete(review.reviewer);
        }
      }
    }

    if (approvals.size < policy.requiredReviews) {
      reasons.push(
        `Required approvals: ${policy.requiredReviews}; current approvals: ${approvals.size}`
      );
    }

    for (const requiredCheck of policy.requiredChecks) {
      const check = pr.checks.get(requiredCheck);

      if (!check) {
        reasons.push(`Missing required check: ${requiredCheck}`);
      } else if (check.commitSha !== latest?.sha) {
        reasons.push(`Stale required check: ${requiredCheck}`);
      } else if (check.state !== CheckState.PASSED) {
        reasons.push(`Required check did not pass: ${requiredCheck}`);
      }
    }

    if (policy.requireConversationResolution) {
      const unresolved = [...pr.conversations.values()].filter(
        (conversation) => !conversation.resolved
      ).length;

      if (unresolved > 0) {
        reasons.push(`${unresolved} unresolved review conversation(s)`);
      }
    }

    if (
      policy.requireLinearHistory &&
      pr.mergeStrategy === MergeStrategy.MERGE_COMMIT
    ) {
      reasons.push("Merge commits violate the linear-history policy");
    }

    return {
      allowed: reasons.length === 0,
      reasons,
    };
  }

  merge(number, actor) {
    const result = this.evaluateMerge(number, actor);

    if (!result.allowed) {
      throw new GovernanceError(
        `Merge blocked: ${result.reasons.join("; ")}`
      );
    }

    const pr = this.getPullRequest(number);
    const latest = this.latestCommit(pr);

    pr.state = PRState.MERGED;

    const resultingSha =
      `merge-${number}-${latest.sha.slice(0, 8)}-${pr.mergeStrategy}`;

    this.branches.set(pr.targetBranch, resultingSha);

    this.emit("pull_request.merged", {
      number,
      actor,
      strategy: pr.mergeStrategy,
      resultingSha,
    });

    return resultingSha;
  }

  close(number) {
    const pr = this.getPullRequest(number);

    if (pr.state === PRState.MERGED) {
      throw new GovernanceError("Merged Pull Requests cannot be closed");
    }

    pr.state = PRState.CLOSED;
    this.emit("pull_request.closed", { number });
  }

  reopen(number) {
    const pr = this.getPullRequest(number);

    if (pr.state !== PRState.CLOSED) {
      throw new GovernanceError("Only closed Pull Requests can be reopened");
    }

    pr.state = PRState.OPEN;
    this.emit("pull_request.reopened", { number });
  }

  latestCommit(pr) {
    return pr.commits.at(-1) ?? null;
  }

  getPullRequest(number) {
    const pr = this.pullRequests.get(number);

    if (!pr) {
      throw new GovernanceError(`Unknown Pull Request: ${number}`);
    }

    return pr;
  }
}

function printDecision(repository, number, actor) {
  const decision = repository.evaluateMerge(number, actor);

  console.log(
    `PR #${number}: ${decision.allowed ? "MERGEABLE" : "BLOCKED"}`
  );

  for (const reason of decision.reasons) {
    console.log(`  - ${reason}`);
  }
}

async function main() {
  const repository = new Repository("payments-platform");

  repository.on("pull_request.merged", (event) => {
    console.log(
      `Event: PR #${event.number} merged with ${event.strategy}`
    );
  });

  repository.on("review.submitted", (event) => {
    console.log(
      `Event: ${event.reviewer} submitted ${event.state} for PR #${event.number}`
    );
  });

  repository.branches.set("main", "base-001");
  repository.createBranch("feature/payment-controls", "base-001");

  repository.protectBranch({
    branch: "main",
    requiredReviews: 2,
    requiredChecks: ["unit-tests", "security-scan"],
    dismissStaleReviews: true,
    requireConversationResolution: true,
    restrictDirectPush: true,
    allowForcePush: false,
    allowDeletion: false,
    requireLinearHistory: true,
    allowedMergeStrategies: [
      MergeStrategy.SQUASH,
      MergeStrategy.REBASE,
    ],
  });

  const pr = repository.createPullRequest({
    title: "Strengthen payment controls",
    sourceBranch: "feature/payment-controls",
    targetBranch: "main",
    author: "alice",
    draft: true,
  });

  repository.addCommit(pr.number, {
    sha: "commit-001",
    message: "Validate transaction limits",
    author: "alice",
  });

  pr.state = PRState.OPEN;

  repository.requestReview(pr.number, "bob");
  repository.requestReview(pr.number, "carol");

  repository.submitReview(pr.number, {
    reviewer: "bob",
    state: ReviewState.APPROVED,
    commentCount: 1,
  });

  repository.submitReview(pr.number, {
    reviewer: "carol",
    state: ReviewState.APPROVED,
    commentCount: 2,
  });

  repository.setStatusCheck(
    pr.number,
    "unit-tests",
    CheckState.PASSED
  );

  repository.setStatusCheck(
    pr.number,
    "security-scan",
    CheckState.PASSED
  );

  repository.addConversation(pr.number, "review-42");

  printDecision(repository, pr.number, "release-manager");

  repository.resolveConversation(pr.number, "review-42");

  printDecision(repository, pr.number, "release-manager");

  repository.merge(pr.number, "release-manager");

  repository.createBranch("feature/audit", repository.branches.get("main"));

  const secondPr = repository.createPullRequest({
    title: "Add audit records",
    sourceBranch: "feature/audit",
    targetBranch: "main",
    author: "diana",
  });

  repository.addCommit(secondPr.number, {
    sha: "commit-002",
    message: "Create audit record model",
    author: "diana",
  });

  repository.submitReview(secondPr.number, {
    reviewer: "erin",
    state: ReviewState.APPROVED,
  });

  repository.submitReview(secondPr.number, {
    reviewer: "frank",
    state: ReviewState.APPROVED,
  });

  repository.setStatusCheck(
    secondPr.number,
    "unit-tests",
    CheckState.PASSED
  );

  repository.setStatusCheck(
    secondPr.number,
    "security-scan",
    CheckState.PASSED
  );

  // New code invalidates commit-specific approvals and checks.
  repository.addCommit(secondPr.number, {
    sha: "commit-003",
    message: "Handle audit persistence errors",
    author: "diana",
  });

  printDecision(repository, secondPr.number, "release-manager");

  // Demonstrate a requested-change review blocking an otherwise healthy PR.
  repository.submitReview(secondPr.number, {
    reviewer: "erin",
    state: ReviewState.CHANGES_REQUESTED,
  });

  repository.setStatusCheck(
    secondPr.number,
    "unit-tests",
    CheckState.PASSED
  );

  repository.setStatusCheck(
    secondPr.number,
    "security-scan",
    CheckState.PASSED
  );

  printDecision(repository, secondPr.number, "release-manager");
}

main().catch((error) => {
  console.error(`Governance failure: ${error.message}`);
  process.exitCode = 1;
});
