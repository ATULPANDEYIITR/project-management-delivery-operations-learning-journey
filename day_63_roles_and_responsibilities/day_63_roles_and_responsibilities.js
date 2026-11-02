"use strict";

const { EventEmitter } = require("node:events");

const PRState = Object.freeze({
  DRAFT: "draft",
  OPEN: "open",
  CLOSED: "closed",
  MERGED: "merged"
});

const ReviewState = Object.freeze({
  COMMENTED: "commented",
  APPROVED: "approved",
  CHANGES_REQUESTED: "changes_requested",
  DISMISSED: "dismissed"
});

const CheckState = Object.freeze({
  PASSING: "passing",
  FAILING: "failing",
  PENDING: "pending"
});

class GovernanceError extends Error {}

class RepositoryPolicy {
  constructor({
    requiredReviews = 2,
    requiredChecks = [],
    requireConversationResolution = true,
    requireLinearHistory = true,
    allowForcePush = false,
    allowDeletion = false,
    allowDirectPush = false
  }) {
    if (requiredReviews < 0) {
      throw new GovernanceError("Required review count cannot be negative.");
    }

    this.requiredReviews = requiredReviews;
    this.requiredChecks = new Set(requiredChecks);
    this.requireConversationResolution = requireConversationResolution;
    this.requireLinearHistory = requireLinearHistory;
    this.allowForcePush = allowForcePush;
    this.allowDeletion = allowDeletion;
    this.allowDirectPush = allowDirectPush;
  }
}

class PullRequest extends EventEmitter {
  constructor(number, title, author, source, target) {
    super();
    this.number = number;
    this.title = title;
    this.author = author;
    this.source = source;
    this.target = target;
    this.state = PRState.OPEN;
    this.draft = false;
    this.commits = [];
    this.reviews = [];
    this.checks = new Map();
    this.unresolvedConversations = 0;
    this.mergeable = true;
    this.baseBehindBy = 0;
  }

  addCommit(commit) {
    if (![PRState.OPEN, PRState.DRAFT].includes(this.state)) {
      throw new GovernanceError("PR is not accepting commits.");
    }
    if (!/^[a-z0-9]{7,40}$/i.test(commit.sha)) {
      throw new GovernanceError("Invalid commit identifier.");
    }
    this.commits.push(commit);
    this.emit("commitAdded", commit);
  }

  addReview(review) {
    if (review.reviewer === this.author) {
      throw new GovernanceError("Self-approval is prohibited.");
    }

    if (!this.commits.some(c => c.sha === review.commitSha)) {
      throw new GovernanceError("Review references an unknown commit.");
    }

    this.reviews.push(review);
    this.emit("reviewSubmitted", review);
  }

  setCheck(name, state) {
    if (!Object.values(CheckState).includes(state)) {
      throw new GovernanceError(`Unknown status state: ${state}`);
    }
    this.checks.set(name, { name, state });
    this.emit("checkChanged", { name, state });
  }
}

class GovernanceEngine {
  constructor(members, policies) {
    this.members = new Map(members.map(member => [member.username, member]));
    this.policies = policies;
  }

  eligibleReviewer(username, author) {
    const member = this.members.get(username);
    return Boolean(
      member &&
      username !== author &&
      (member.roles.has("reviewer") || member.roles.has("maintainer"))
    );
  }

  evaluate(pr) {
    const reasons = [];
    const policy = this.policies.get(pr.target);

    if (pr.state !== PRState.OPEN) reasons.push("PR is not open.");
    if (pr.draft) reasons.push("Draft PR cannot be merged.");
    if (pr.commits.length === 0) reasons.push("No commits are present.");
    if (!pr.mergeable) reasons.push("Merge conflicts are present.");

    if (!policy) {
      reasons.push("Target branch is not governed.");
      return { eligible: false, reasons };
    }

    const head = pr.commits.at(-1)?.sha;

    const approvals = new Set(
      pr.reviews
        .filter(r =>
          r.state === ReviewState.APPROVED &&
          r.commitSha === head &&
          this.eligibleReviewer(r.reviewer, pr.author)
        )
        .map(r => r.reviewer)
    );

    if (approvals.size < policy.requiredReviews) {
      reasons.push(
        `Requires ${policy.requiredReviews} current approval(s).`
      );
    }

    for (const required of policy.requiredChecks) {
      if (pr.checks.get(required)?.state !== CheckState.PASSING) {
        reasons.push(`Required check '${required}' is not passing.`);
      }
    }

    if (
      policy.requireConversationResolution &&
      pr.unresolvedConversations > 0
    ) {
      reasons.push("Unresolved review conversations remain.");
    }

    if (policy.requireLinearHistory && pr.baseBehindBy > 0) {
      reasons.push("Base branch synchronization is required.");
    }

    return { eligible: reasons.length === 0, reasons };
  }
}

function showDecision(engine, pr) {
  const result = engine.evaluate(pr);
  console.log(
    `PR #${pr.number}: ${pr.title} -> ` +
    `${result.eligible ? "MERGE ELIGIBLE" : "MERGE BLOCKED"}`
  );

  for (const reason of result.reasons) {
    console.log(`  - ${reason}`);
  }
}

async function main() {
  const members = [
    { username: "atul", roles: new Set(["developer"]) },
    { username: "maya", roles: new Set(["reviewer"]) },
    { username: "liam", roles: new Set(["maintainer"]) },
    { username: "nora", roles: new Set(["reviewer"]) }
  ];

  const policies = new Map([
    [
      "main",
      new RepositoryPolicy({
        requiredReviews: 2,
        requiredChecks: ["ci", "security"],
        requireConversationResolution: true,
        requireLinearHistory: true
      })
    ]
  ]);

  const engine = new GovernanceEngine(members, policies);

  const pr = new PullRequest(
    142,
    "Add transaction idempotency protection",
    "atul",
    "feature/idempotency",
    "main"
  );

  pr.on("commitAdded", commit =>
    console.log(`Event: commit ${commit.sha} added`)
  );

  pr.on("reviewSubmitted", review =>
    console.log(`Event: ${review.reviewer} submitted ${review.state}`)
  );

  pr.addCommit({
    sha: "a1b2c3d",
    message: "Add idempotency validation",
    author: "atul"
  });

  pr.setCheck("ci", CheckState.PASSING);
  pr.setCheck("security", CheckState.PASSING);

  pr.addReview({
    reviewer: "maya",
    state: ReviewState.APPROVED,
    commitSha: "a1b2c3d"
  });

  pr.addReview({
    reviewer: "liam",
    state: ReviewState.APPROVED,
    commitSha: "a1b2c3d"
  });

  showDecision(engine, pr);

  pr.addCommit({
    sha: "d4e5f6g",
    message: "Handle duplicate requests",
    author: "atul"
  });

  showDecision(engine, pr);

  pr.addReview({
    reviewer: "maya",
    state: ReviewState.APPROVED,
    commitSha: "d4e5f6g"
  });

  pr.addReview({
    reviewer: "liam",
    state: ReviewState.APPROVED,
    commitSha: "d4e5f6g"
  });

  pr.unresolvedConversations = 1;
  showDecision(engine, pr);

  pr.unresolvedConversations = 0;
  showDecision(engine, pr);

  try {
    pr.addReview({
      reviewer: "atul",
      state: ReviewState.APPROVED,
      commitSha: "d4e5f6g"
    });
  } catch (error) {
    console.log(`Validation failure: ${error.message}`);
  }
}

main().catch(error => {
  console.error(`Fatal error: ${error.message}`);
  process.exitCode = 1;
});
