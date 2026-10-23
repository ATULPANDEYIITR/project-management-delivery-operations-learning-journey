'use strict';

/*
 * Event-driven repository governance model.
 * Pull Requests own proposal state, reviews own evaluation decisions,
 * approvals represent a subset of reviews, and branch protection determines
 * whether the repository may accept the proposed change.
 */

const { EventEmitter } = require('node:events');

const PRState = Object.freeze({
  DRAFT: 'draft',
  OPEN: 'open',
  CLOSED: 'closed',
  MERGED: 'merged'
});

const ReviewState = Object.freeze({
  COMMENTED: 'commented',
  APPROVED: 'approved',
  CHANGES_REQUESTED: 'changes_requested',
  DISMISSED: 'dismissed'
});

const MergeStrategy = Object.freeze({
  MERGE_COMMIT: 'merge_commit',
  SQUASH: 'squash',
  REBASE: 'rebase'
});

class ValidationError extends Error {}

class Review {
  constructor({ reviewer, state, commitSha, comments = [] }) {
    if (!reviewer || !commitSha) {
      throw new ValidationError('Reviewer and commit SHA are required.');
    }

    this.reviewer = reviewer;
    this.state = state;
    this.commitSha = commitSha;
    this.comments = [...comments];
    this.dismissed = false;
  }
}

class PullRequest extends EventEmitter {
  constructor({ number, title, sourceBranch, targetBranch, author, draft = true }) {
    super();

    if (!title.trim()) throw new ValidationError('Pull Request title is required.');
    if (sourceBranch === targetBranch) {
      throw new ValidationError('Source and target branches must differ.');
    }

    this.number = number;
    this.title = title;
    this.sourceBranch = sourceBranch;
    this.targetBranch = targetBranch;
    this.author = author;
    this.state = draft ? PRState.DRAFT : PRState.OPEN;
    this.commits = [];
    this.reviewersRequested = new Set();
    this.reviews = [];
    this.statusChecks = new Map();
    this.unresolvedConversations = 0;
    this.headSha = '';
  }

  open() {
    if (![PRState.DRAFT, PRState.CLOSED].includes(this.state)) {
      throw new ValidationError('Pull Request cannot be opened from its current state.');
    }
    this.state = PRState.OPEN;
    this.emit('stateChanged', this);
  }

  close() {
    if (this.state === PRState.MERGED) {
      throw new ValidationError('Merged Pull Requests cannot be closed.');
    }
    this.state = PRState.CLOSED;
    this.emit('stateChanged', this);
  }

  reopen() {
    if (this.state !== PRState.CLOSED) {
      throw new ValidationError('Only closed Pull Requests can be reopened.');
    }
    this.state = PRState.OPEN;
    this.emit('stateChanged', this);
  }

  addCommit(commit) {
    if (this.state === PRState.MERGED) {
      throw new ValidationError('Merged Pull Requests cannot receive commits.');
    }
    if (!commit.sha || !commit.author) {
      throw new ValidationError('Commit SHA and author are required.');
    }
    if (this.commits.some(existing => existing.sha === commit.sha)) {
      throw new ValidationError('Duplicate commit SHA.');
    }

    this.commits.push({ ...commit });
    this.headSha = commit.sha;

    // A review belongs to a revision. New commits make old approvals stale.
    for (const review of this.reviews) {
      if (review.commitSha !== this.headSha &&
          review.state === ReviewState.APPROVED) {
        review.dismissed = true;
      }
    }

    this.emit('commitAdded', { pr: this, commit });
  }

  requestReview(reviewer) {
    if (!reviewer || reviewer === this.author) {
      throw new ValidationError('The author cannot be a required reviewer.');
    }
    this.reviewersRequested.add(reviewer);
    this.emit('reviewRequested', { pr: this, reviewer });
  }

  submitReview(reviewer, state, comments = []) {
    if (this.state !== PRState.OPEN) {
      throw new ValidationError('Reviews require an open Pull Request.');
    }
    if (reviewer === this.author) {
      throw new ValidationError('Self-review is not allowed.');
    }
    if (!Object.values(ReviewState).includes(state)) {
      throw new ValidationError('Unknown review state.');
    }

    const review = new Review({
      reviewer,
      state,
      commitSha: this.headSha,
      comments
    });

    this.reviews.push(review);
    this.emit('reviewSubmitted', review);
  }

  setStatus(name, passed) {
    if (!this.headSha) {
      throw new ValidationError('A status check requires a Pull Request revision.');
    }

    this.statusChecks.set(name, {
      name,
      passed: Boolean(passed),
      commitSha: this.headSha
    });

    this.emit('statusChanged', {
      pr: this,
      name,
      passed: Boolean(passed)
    });
  }

  addConversation() {
    this.unresolvedConversations += 1;
    this.emit('conversationOpened', this);
  }

  resolveConversation() {
    if (this.unresolvedConversations === 0) {
      throw new ValidationError('No unresolved conversations exist.');
    }
    this.unresolvedConversations -= 1;
    this.emit('conversationResolved', this);
  }

  synchronizeBase(newHeadSha) {
    if (this.state !== PRState.OPEN) {
      throw new ValidationError('Only open Pull Requests can be synchronized.');
    }

    this.headSha = newHeadSha;

    // Synchronization changes the evaluated revision.
    for (const review of this.reviews) {
      if (review.state === ReviewState.APPROVED) {
        review.dismissed = true;
      }
    }

    for (const check of this.statusChecks.values()) {
      check.passed = false;
    }

    this.emit('baseSynchronized', this);
  }
}

class BranchProtectionPolicy {
  constructor({
    requiredReviews = 2,
    requiredChecks = [],
    requireConversationResolution = true,
    requireLinearHistory = false,
    allowDirectPush = false,
    allowForcePush = false,
    allowDeletion = false,
    allowAdminBypass = false
  } = {}) {
    this.requiredReviews = requiredReviews;
    this.requiredChecks = new Set(requiredChecks);
    this.requireConversationResolution = requireConversationResolution;
    this.requireLinearHistory = requireLinearHistory;
    this.allowDirectPush = allowDirectPush;
    this.allowForcePush = allowForcePush;
    this.allowDeletion = allowDeletion;
    this.allowAdminBypass = allowAdminBypass;
  }
}

class GovernanceEngine {
  constructor(policy) {
    this.policy = policy;
  }

  evaluate(pr) {
    const failures = [];

    if (pr.state !== PRState.OPEN) {
      failures.push('Pull Request must be open.');
    }

    if (pr.commits.length === 0) {
      failures.push('No commits are associated with the Pull Request.');
    }

    const approvals = new Set(
      pr.reviews
        .filter(review =>
          review.state === ReviewState.APPROVED &&
          !review.dismissed &&
          review.commitSha === pr.headSha &&
          review.reviewer !== pr.author
        )
        .map(review => review.reviewer)
    );

    if (approvals.size < this.policy.requiredReviews) {
      failures.push(
        `${this.policy.requiredReviews} current approval(s) are required.`
      );
    }

    const changesRequested = pr.reviews.some(review =>
      review.state === ReviewState.CHANGES_REQUESTED &&
      !review.dismissed &&
      review.commitSha === pr.headSha
    );

    if (changesRequested) {
      failures.push('An active changes-requested review blocks merging.');
    }

    for (const requiredCheck of this.policy.requiredChecks) {
      const check = pr.statusChecks.get(requiredCheck);

      if (!check || !check.passed || check.commitSha !== pr.headSha) {
        failures.push(`Required status check '${requiredCheck}' has not passed.`);
      }
    }

    if (
      this.policy.requireConversationResolution &&
      pr.unresolvedConversations > 0
    ) {
      failures.push('Review conversations remain unresolved.');
    }

    return {
      eligible: failures.length === 0,
      failures
    };
  }

  merge(pr, strategy = MergeStrategy.SQUASH) {
    const result = this.evaluate(pr);

    if (!result.eligible) {
      throw new ValidationError(
        `Merge blocked: ${result.failures.join('; ')}`
      );
    }

    pr.state = PRState.MERGED;
    pr.emit('merged', { pr, strategy });
    return `PR #${pr.number} merged using ${strategy}.`;
  }
}

function main() {
  const policy = new BranchProtectionPolicy({
    requiredReviews: 2,
    requiredChecks: ['tests', 'security'],
    requireConversationResolution: true,
    requireLinearHistory: true,
    allowDirectPush: false,
    allowForcePush: false,
    allowDeletion: false
  });

  const governance = new GovernanceEngine(policy);

  const pr = new PullRequest({
    number: 42,
    title: 'Harden payment authorization',
    sourceBranch: 'feature/payment-policy',
    targetBranch: 'main',
    author: 'alice',
    draft: true
  });

  pr.on('reviewRequested', ({ reviewer }) => {
    console.log(`Review requested from ${reviewer}`);
  });

  pr.on('reviewSubmitted', review => {
    console.log(
      `Review: ${review.reviewer} -> ${review.state} @ ${review.commitSha}`
    );
  });

  pr.on('merged', ({ strategy }) => {
    console.log(`Merge event emitted with strategy: ${strategy}`);
  });

  pr.addCommit({
    sha: 'a100',
    message: 'Add authorization policy',
    author: 'alice'
  });

  pr.requestReview('bob');
  pr.requestReview('carol');
  pr.open();

  pr.submitReview(
    'bob',
    ReviewState.APPROVED,
    ['Policy boundaries are clear.']
  );

  pr.submitReview(
    'carol',
    ReviewState.CHANGES_REQUESTED,
    ['Add a regression test for expired credentials.']
  );

  pr.addConversation();
  pr.setStatus('tests', true);
  pr.setStatus('security', true);

  let decision = governance.evaluate(pr);
  console.log('\nInitial eligibility:', decision.eligible);
  decision.failures.forEach(failure => console.log(` - ${failure}`));

  pr.addCommit({
    sha: 'a101',
    message: 'Add expired credential regression coverage',
    author: 'alice'
  });

  pr.submitReview('bob', ReviewState.APPROVED);
  pr.submitReview('carol', ReviewState.APPROVED);
  pr.resolveConversation();

  pr.setStatus('tests', true);
  pr.setStatus('security', true);

  decision = governance.evaluate(pr);
  console.log('\nFinal eligibility:', decision.eligible);

  if (decision.eligible) {
    console.log(governance.merge(pr, MergeStrategy.SQUASH));
  }
}

try {
  main();
} catch (error) {
  console.error(`Governance failure: ${error.message}`);
  process.exitCode = 1;
}
