"use strict";

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
  SUCCESS: "success",
  FAILURE: "failure",
});

class GovernanceError extends Error {}

class RepositoryGovernance extends EventEmitter {
  constructor(name) {
    super();
    this.name = name;
    this.branches = new Map();
    this.pullRequests = new Map();
    this.policies = new Map();
    this.nextPullRequest = 1;
  }

  addBranch(name, { protectedBranch = false } = {}) {
    this.assertName(name, "branch");
    if (this.branches.has(name)) {
      throw new GovernanceError(`Branch already exists: ${name}`);
    }

    this.branches.set(name, {
      name,
      protected: protectedBranch,
      commits: [],
    });
  }

  addCommit(branchName, commit) {
    const branch = this.getBranch(branchName);

    if (!/^[a-f0-9]{7,40}$/i.test(commit.sha)) {
      throw new GovernanceError("Commit SHA must contain 7-40 hexadecimal characters");
    }

    if (!commit.message?.trim()) {
      throw new GovernanceError("Commit message cannot be empty");
    }

    if (!commit.author?.trim()) {
      throw new GovernanceError("Commit author is required");
    }

    if (branch.commits.some((existing) => existing.sha === commit.sha)) {
      throw new GovernanceError(`Duplicate commit: ${commit.sha}`);
    }

    branch.commits.push({
      sha: commit.sha,
      message: commit.message.trim(),
      author: commit.author,
    });

    this.emit("commitAdded", { branch: branchName, sha: commit.sha });
  }

  protectBranch(branchName, policy) {
    const branch = this.getBranch(branchName);

    if (!Number.isInteger(policy.requiredApprovals) || policy.requiredApprovals < 0) {
      throw new GovernanceError("requiredApprovals must be a non-negative integer");
    }

    const normalized = {
      requiredApprovals: policy.requiredApprovals,
      requiredChecks: new Set(policy.requiredChecks ?? []),
      requireResolvedConversations: policy.requireResolvedConversations ?? true,
      dismissStaleApprovals: policy.dismissStaleApprovals ?? true,
      requireLinearHistory: policy.requireLinearHistory ?? false,
      allowDirectPush: policy.allowDirectPush ?? false,
      allowForcePush: policy.allowForcePush ?? false,
    };

    branch.protected = true;
    this.policies.set(branchName, normalized);
    this.emit("policyChanged", { branch: branchName });
  }

  createPullRequest({ title, source, target, author, draft = false }) {
    if (!title?.trim()) {
      throw new GovernanceError("Pull request title is required");
    }

    if (source === target) {
      throw new GovernanceError("Source and target branches must differ");
    }

    const sourceBranch = this.getBranch(source);
    this.getBranch(target);

    if (sourceBranch.commits.length === 0) {
      throw new GovernanceError("Source branch contains no changes");
    }

    const number = this.nextPullRequest++;
    const pr = {
      number,
      title: title.trim(),
      source,
      target,
      author,
      state: draft ? PRState.DRAFT : PRState.OPEN,
      draft,
      commits: sourceBranch.commits.map((commit) => ({ ...commit })),
      reviews: [],
      checks: new Map(),
      unresolvedConversations: new Set(),
      history: [],
    };

    this.pullRequests.set(number, pr);
    this.record(pr, "created", { draft });
    this.emit("pullRequestCreated", { number });

    return pr;
  }

  addConversation(prNumber, conversationId) {
    const pr = this.getPR(prNumber);
    this.ensureActive(pr);

    if (!conversationId?.trim()) {
      throw new GovernanceError("Conversation ID is required");
    }

    pr.unresolvedConversations.add(conversationId);
    this.record(pr, "conversation_opened", { conversationId });
  }

  resolveConversation(prNumber, conversationId) {
    const pr = this.getPR(prNumber);

    if (!pr.unresolvedConversations.delete(conversationId)) {
      throw new GovernanceError(`Conversation not unresolved: ${conversationId}`);
    }

    this.record(pr, "conversation_resolved", { conversationId });
  }

  submitReview(prNumber, reviewer, state, comment = "") {
    const pr = this.getPR(prNumber);
    this.ensureActive(pr);

    if (reviewer === pr.author && state === ReviewState.APPROVED) {
      throw new GovernanceError("Authors cannot approve their own pull requests");
    }

    const head = this.head(pr);
    if (!head) {
      throw new GovernanceError("Pull request has no head commit");
    }

    if (!Object.values(ReviewState).includes(state)) {
      throw new GovernanceError(`Unsupported review state: ${state}`);
    }

    pr.reviews.push({
      reviewer,
      state,
      commitSha: head,
      comment: comment.trim(),
      submittedAt: new Date().toISOString(),
    });

    this.record(pr, "review_submitted", { reviewer, state, commitSha: head });
    this.emit("reviewSubmitted", {
      pullRequest: pr.number,
      reviewer,
      state,
    });
  }

  updateCheck(prNumber, name, state) {
    const pr = this.getPR(prNumber);
    this.ensureActive(pr);

    if (!name?.trim()) {
      throw new GovernanceError("Status check name is required");
    }

    if (!Object.values(CheckState).includes(state)) {
      throw new GovernanceError(`Unsupported check state: ${state}`);
    }

    const head = this.head(pr);
    pr.checks.set(name, {
      name,
      state,
      commitSha: head,
      updatedAt: new Date().toISOString(),
    });

    this.record(pr, "check_updated", { name, state, commitSha: head });
  }

  synchronize(prNumber) {
    const pr = this.getPR(prNumber);
    this.ensureActive(pr);

    const source = this.getBranch(pr.source);
    pr.commits = source.commits.map((commit) => ({ ...commit }));

    const policy = this.policies.get(pr.target);
    if (policy?.dismissStaleApprovals) {
      const head = this.head(pr);
      for (const review of pr.reviews) {
        if (
          review.state === ReviewState.APPROVED &&
          review.commitSha !== head
        ) {
          review.state = ReviewState.DISMISSED;
          this.record(pr, "approval_dismissed", {
            reviewer: review.reviewer,
            reason: "head_changed",
          });
        }
      }
    }

    this.record(pr, "synchronized", { head: this.head(pr) });
  }

  evaluate(prNumber) {
    const pr = this.getPR(prNumber);
    const policy = this.policies.get(pr.target) ?? {
      requiredApprovals: 0,
      requiredChecks: new Set(),
      requireResolvedConversations: false,
      dismissStaleApprovals: true,
      requireLinearHistory: false,
    };

    const reasons = [];
    const head = this.head(pr);

    if (pr.state !== PRState.OPEN) reasons.push("Pull request is not open");
    if (pr.draft) reasons.push("Pull request is still a draft");
    if (!head) reasons.push("Pull request has no head commit");

    const approvals = new Set(
      pr.reviews
        .filter(
          (review) =>
            review.state === ReviewState.APPROVED &&
            review.commitSha === head &&
            review.reviewer !== pr.author
        )
        .map((review) => review.reviewer)
    );

    if (approvals.size < policy.requiredApprovals) {
      reasons.push(
        `Required approvals: ${policy.requiredApprovals}; current approvals: ${approvals.size}`
      );
    }

    for (const checkName of policy.requiredChecks) {
      const check = pr.checks.get(checkName);
      if (!check || check.commitSha !== head || check.state !== CheckState.SUCCESS) {
        reasons.push(`Required check is not successful: ${checkName}`);
      }
    }

    if (
      policy.requireResolvedConversations &&
      pr.unresolvedConversations.size > 0
    ) {
      reasons.push(
        `${pr.unresolvedConversations.size} unresolved conversation(s)`
      );
    }

    return {
      eligible: reasons.length === 0,
      reasons,
      approvals: [...approvals],
      head,
    };
  }

  merge(prNumber) {
    const pr = this.getPR(prNumber);
    const result = this.evaluate(prNumber);

    if (!result.eligible) {
      throw new GovernanceError(`Merge blocked: ${result.reasons.join("; ")}`);
    }

    const target = this.getBranch(pr.target);
    const source = this.getBranch(pr.source);

    const existing = new Set(target.commits.map((commit) => commit.sha));
    for (const commit of source.commits) {
      if (!existing.has(commit.sha)) {
        target.commits.push({ ...commit });
      }
    }

    pr.state = PRState.MERGED;
    this.record(pr, "merged", { head: result.head });
    this.emit("merged", { pullRequest: pr.number });
  }

  close(prNumber) {
    const pr = this.getPR(prNumber);
    this.ensureActive(pr);
    pr.state = PRState.CLOSED;
    this.record(pr, "closed");
  }

  reopen(prNumber) {
    const pr = this.getPR(prNumber);
    if (pr.state !== PRState.CLOSED) {
      throw new GovernanceError("Only closed pull requests can be reopened");
    }

    pr.state = PRState.OPEN;
    this.record(pr, "reopened");
  }

  report(prNumber) {
    const pr = this.getPR(prNumber);
    const evaluation = this.evaluate(prNumber);

    return {
      repository: this.name,
      pullRequest: pr.number,
      title: pr.title,
      source: pr.source,
      target: pr.target,
      state: pr.state,
      head: evaluation.head,
      eligible: evaluation.eligible,
      reasons: evaluation.reasons,
      approvalCount: evaluation.approvals.length,
      unresolvedConversations: pr.unresolvedConversations.size,
      checks: [...pr.checks.values()].map((check) => ({
        name: check.name,
        state: check.state,
        commitSha: check.commitSha,
      })),
    };
  }

  getBranch(name) {
    const branch = this.branches.get(name);
    if (!branch) throw new GovernanceError(`Unknown branch: ${name}`);
    return branch;
  }

  getPR(number) {
    const pr = this.pullRequests.get(number);
    if (!pr) throw new GovernanceError(`Unknown pull request: ${number}`);
    return pr;
  }

  head(pr) {
    return pr.commits.at(-1)?.sha ?? null;
  }

  ensureActive(pr) {
    if (![PRState.OPEN, PRState.DRAFT].includes(pr.state)) {
      throw new GovernanceError(`Pull request is ${pr.state}`);
    }
  }

  record(pr, event, details = {}) {
    pr.history.push({
      event,
      timestamp: new Date().toISOString(),
      ...details,
    });
  }

  assertName(value, type) {
    if (!/^[A-Za-z0-9._/-]{2,100}$/.test(value)) {
      throw new GovernanceError(`Invalid ${type} name`);
    }
  }
}

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function runWorkflow() {
  const repository = new RepositoryGovernance("continuous-improvement-platform");

  repository.on("merged", ({ pullRequest }) => {
    console.log(`Event: pull request #${pullRequest} merged`);
  });

  repository.addBranch("main", { protectedBranch: true });
  repository.addBranch("process/cycle-time");
  repository.addBranch("process/review-quality");

  repository.addCommit("main", {
    sha: "a100001",
    message: "Establish development baseline",
    author: "platform",
  });

  repository.addCommit("process/cycle-time", {
    sha: "b100001",
    message: "Record pull request cycle time",
    author: "developer-1",
  });

  repository.addCommit("process/cycle-time", {
    sha: "b100002",
    message: "Expose process metrics",
    author: "developer-1",
  });

  repository.protectBranch("main", {
    requiredApprovals: 2,
    requiredChecks: ["unit-tests", "security-scan"],
    requireResolvedConversations: true,
    dismissStaleApprovals: true,
    requireLinearHistory: true,
    allowDirectPush: false,
    allowForcePush: false,
  });

  const pr = repository.createPullRequest({
    title: "Reduce pull request cycle time",
    source: "process/cycle-time",
    target: "main",
    author: "developer-1",
  });

  repository.addConversation(pr.number, "discussion-1");
  repository.submitReview(
    pr.number,
    "reviewer-1",
    ReviewState.APPROVED
  );
  repository.submitReview(
    pr.number,
    "reviewer-2",
    ReviewState.CHANGES_REQUESTED,
    "The metric must use the current head."
  );

  await delay(10);

  repository.updateCheck(pr.number, "unit-tests", CheckState.SUCCESS);
  repository.updateCheck(pr.number, "security-scan", CheckState.SUCCESS);

  console.log("Blocked state:");
  console.log(JSON.stringify(repository.report(pr.number), null, 2));

  repository.resolveConversation(pr.number, "discussion-1");
  repository.submitReview(pr.number, "reviewer-2", ReviewState.APPROVED);

  const eligible = repository.evaluate(pr.number);
  if (!eligible.eligible) {
    throw new GovernanceError(eligible.reasons.join("; "));
  }

  repository.merge(pr.number);

  console.log("\nMerged state:");
  console.log(JSON.stringify(repository.report(pr.number), null, 2));

  repository.addCommit("process/review-quality", {
    sha: "c100001",
    message: "Measure review turnaround",
    author: "developer-2",
  });

  const secondPR = repository.createPullRequest({
    title: "Measure review turnaround",
    source: "process/review-quality",
    target: "main",
    author: "developer-2",
  });

  repository.submitReview(secondPR.number, "reviewer-1", ReviewState.APPROVED);
  repository.submitReview(secondPR.number, "reviewer-2", ReviewState.APPROVED);
  repository.updateCheck(secondPR.number, "unit-tests", CheckState.SUCCESS);
  repository.updateCheck(secondPR.number, "security-scan", CheckState.SUCCESS);

  repository.addCommit("process/review-quality", {
    sha: "c100002",
    message: "Correct turnaround calculation",
    author: "developer-2",
  });

  repository.synchronize(secondPR.number);

  const staleResult = repository.evaluate(secondPR.number);
  if (staleResult.eligible) {
    throw new GovernanceError("Expected stale approvals to block the merge");
  }

  console.log("\nAfter source branch changed:");
  console.log(JSON.stringify(repository.report(secondPR.number), null, 2));
}

runWorkflow().catch((error) => {
  console.error(`Governance failure: ${error.message}`);
  process.exitCode = 1;
});
