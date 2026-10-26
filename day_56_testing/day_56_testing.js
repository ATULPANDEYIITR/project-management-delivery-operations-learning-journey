'use strict';

/*
 * Repository governance and testing model.
 * The implementation uses events to expose important workflow transitions.
 */

const EventEmitter = require('node:events');
const crypto = require('node:crypto');

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

const CheckState = Object.freeze({
  PASSING: 'passing',
  FAILING: 'failing',
  PENDING: 'pending'
});

class DomainError extends Error {}

function assertNonEmpty(value, field) {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new DomainError(`${field} must be a non-empty string.`);
  }
}

function createId(prefix) {
  return `${prefix}-${crypto.randomBytes(6).toString('hex')}`;
}

class Repository {
  constructor(name, protection) {
    assertNonEmpty(name, 'Repository name');

    this.name = name;
    this.branches = new Map();
    this.reviewers = new Set();
    this.pullRequests = new Map();
    this.protection = structuredClone(protection);
    this.events = new EventEmitter();
  }

  addBranch(name, options = {}) {
    assertNonEmpty(name, 'Branch name');

    if (this.branches.has(name)) {
      throw new DomainError(`Branch '${name}' already exists.`);
    }

    this.branches.set(name, {
      name,
      protected: Boolean(options.protected),
      headSha: options.headSha || createId('base'),
      commits: []
    });
  }

  addReviewer(username) {
    assertNonEmpty(username, 'Reviewer');
    this.reviewers.add(username);
  }

  createPullRequest({
    number,
    author,
    sourceBranch,
    targetBranch,
    title,
    draft = false
  }) {
    if (!Number.isInteger(number) || number <= 0) {
      throw new DomainError('Pull Request number must be positive.');
    }

    assertNonEmpty(author, 'Author');
    assertNonEmpty(title, 'Title');

    if (this.pullRequests.has(number)) {
      throw new DomainError(`Pull Request #${number} already exists.`);
    }

    if (!this.branches.has(sourceBranch) || !this.branches.has(targetBranch)) {
      throw new DomainError('Source and target branches must exist.');
    }

    if (sourceBranch === targetBranch) {
      throw new DomainError('Source and target branches must differ.');
    }

    const pr = {
      number,
      author,
      sourceBranch,
      targetBranch,
      title: title.trim(),
      state: draft ? PRState.DRAFT : PRState.OPEN,
      draft,
      commits: [],
      reviews: [],
      comments: [],
      conversations: new Map(),
      checks: new Map(),
      baseShaAtOpen: this.branches.get(targetBranch).headSha
    };

    this.pullRequests.set(number, pr);
    this.events.emit('pull_request.created', pr);

    return pr;
  }

  publish(number) {
    const pr = this.getPullRequest(number);

    if (pr.state !== PRState.DRAFT) {
      throw new DomainError('Only draft Pull Requests can be published.');
    }

    pr.draft = false;
    pr.state = PRState.OPEN;
    this.events.emit('pull_request.published', pr);
  }

  addCommit(number, message, author) {
    const pr = this.getPullRequest(number);

    if (pr.state !== PRState.OPEN) {
      throw new DomainError('Commits require an open Pull Request.');
    }

    assertNonEmpty(message, 'Commit message');
    assertNonEmpty(author, 'Commit author');

    const commit = {
      sha: createId('commit'),
      message: message.trim(),
      author
    };

    pr.commits.push(commit);

    const source = this.branches.get(pr.sourceBranch);
    source.commits.push(commit);
    source.headSha = commit.sha;

    this.events.emit('commit.added', { pr, commit });
    return commit;
  }

  addReview(number, reviewer, state, commitSha) {
    const pr = this.getPullRequest(number);

    if (pr.state !== PRState.OPEN) {
      throw new DomainError('Reviews require an open Pull Request.');
    }

    if (reviewer === pr.author) {
      throw new DomainError('Self-review approval is not permitted.');
    }

    if (!this.reviewers.has(reviewer)) {
      throw new DomainError('Reviewer is not eligible.');
    }

    if (!Object.values(ReviewState).includes(state)) {
      throw new DomainError('Unknown review state.');
    }

    assertNonEmpty(commitSha, 'Review commit SHA');

    const review = {
      id: createId('review'),
      reviewer,
      state,
      commitSha,
      createdAt: new Date().toISOString()
    };

    pr.reviews.push(review);
    this.events.emit('review.submitted', { pr, review });

    return review;
  }

  addConversation(number, reviewer, body) {
    const pr = this.getPullRequest(number);

    assertNonEmpty(reviewer, 'Reviewer');
    assertNonEmpty(body, 'Conversation');

    const conversation = {
      id: createId('conversation'),
      reviewer,
      body: body.trim(),
      resolved: false
    };

    pr.conversations.set(conversation.id, conversation);
    this.events.emit('conversation.created', { pr, conversation });

    return conversation.id;
  }

  resolveConversation(number, conversationId) {
    const pr = this.getPullRequest(number);
    const conversation = pr.conversations.get(conversationId);

    if (!conversation) {
      throw new DomainError('Conversation does not exist.');
    }

    conversation.resolved = true;
    this.events.emit('conversation.resolved', { pr, conversation });
  }

  setCheck(number, name, state) {
    const pr = this.getPullRequest(number);

    assertNonEmpty(name, 'Check name');

    if (!Object.values(CheckState).includes(state)) {
      throw new DomainError('Invalid status-check state.');
    }

    pr.checks.set(name, {
      name,
      state,
      updatedAt: new Date().toISOString()
    });

    this.events.emit('check.updated', {
      pr,
      check: pr.checks.get(name)
    });
  }

  synchronizeBase(number) {
    const pr = this.getPullRequest(number);
    const target = this.branches.get(pr.targetBranch);

    pr.baseShaAtOpen = target.headSha;

    // Synchronization invalidates existing approvals because the reviewed
    // change set is no longer identical to the previously reviewed state.
    for (const review of pr.reviews) {
      if (review.state === ReviewState.APPROVED) {
        review.state = ReviewState.DISMISSED;
      }
    }

    this.events.emit('pull_request.synchronized', pr);
  }

  evaluate(number) {
    const pr = this.getPullRequest(number);
    const policy = this.protection;
    const failures = [];

    if (pr.state !== PRState.OPEN) {
      failures.push('Pull Request is not open.');
    }

    if (pr.draft) {
      failures.push('Pull Request is a draft.');
    }

    if (pr.commits.length === 0) {
      failures.push('Pull Request contains no commits.');
    }

    const latestApprovals = new Map();

    for (const review of pr.reviews) {
      if (review.state === ReviewState.APPROVED) {
        latestApprovals.set(review.reviewer, review);
      }

      if (review.state === ReviewState.CHANGES_REQUESTED) {
        failures.push(`Reviewer ${review.reviewer} requested changes.`);
      }
    }

    if (latestApprovals.size < policy.requiredApprovals) {
      failures.push(
        `Required approvals: ${policy.requiredApprovals}; current approvals: ${latestApprovals.size}.`
      );
    }

    for (const requiredCheck of policy.requiredChecks) {
      const check = pr.checks.get(requiredCheck);

      if (!check) {
        failures.push(`Required check '${requiredCheck}' is missing.`);
      } else if (check.state !== CheckState.PASSING) {
        failures.push(`Required check '${requiredCheck}' is not passing.`);
      }
    }

    if (policy.requireConversationsResolved) {
      for (const conversation of pr.conversations.values()) {
        if (!conversation.resolved) {
          failures.push(`Conversation ${conversation.id} is unresolved.`);
        }
      }
    }

    const target = this.branches.get(pr.targetBranch);

    if (target.headSha !== pr.baseShaAtOpen) {
      failures.push('Base branch changed after the Pull Request was opened.');
    }

    return {
      eligible: failures.length === 0,
      failures
    };
  }

  merge(number, strategy = 'squash') {
    const result = this.evaluate(number);

    if (!result.eligible) {
      throw new DomainError(
        `Merge blocked:\n${result.failures.map(item => `- ${item}`).join('\n')}`
      );
    }

    if (!['merge', 'squash', 'rebase'].includes(strategy)) {
      throw new DomainError('Unsupported merge strategy.');
    }

    const pr = this.getPullRequest(number);
    const target = this.branches.get(pr.targetBranch);
    const mergeSha = createId(strategy);

    target.commits.push({
      sha: mergeSha,
      message: `${strategy} PR #${number}: ${pr.title}`,
      author: pr.author
    });

    target.headSha = mergeSha;
    pr.state = PRState.MERGED;

    this.events.emit('pull_request.merged', {
      pr,
      strategy,
      mergeSha
    });

    return mergeSha;
  }

  close(number) {
    const pr = this.getPullRequest(number);

    if (pr.state === PRState.MERGED) {
      throw new DomainError('Merged Pull Requests cannot be closed.');
    }

    pr.state = PRState.CLOSED;
    this.events.emit('pull_request.closed', pr);
  }

  reopen(number) {
    const pr = this.getPullRequest(number);

    if (pr.state !== PRState.CLOSED) {
      throw new DomainError('Only closed Pull Requests can be reopened.');
    }

    pr.state = PRState.OPEN;
    this.events.emit('pull_request.reopened', pr);
  }

  getPullRequest(number) {
    const pr = this.pullRequests.get(number);

    if (!pr) {
      throw new DomainError(`Pull Request #${number} does not exist.`);
    }

    return pr;
  }
}

async function runAsyncChecks(repository, number) {
  const checks = [
    ['unit-tests', 40, CheckState.PASSING],
    ['security-scan', 60, CheckState.PASSING],
    ['integration-tests', 30, CheckState.PASSING]
  ];

  await Promise.all(
    checks.map(
      ([name, delay, state]) =>
        new Promise(resolve => {
          setTimeout(() => {
            repository.setCheck(number, name, state);
            resolve();
          }, delay);
        })
    )
  );
}

async function main() {
  const repository = new Repository('payments-service', {
    requiredApprovals: 2,
    requiredChecks: ['unit-tests', 'security-scan'],
    requireConversationsResolved: true,
    restrictDirectPush: true,
    restrictForcePush: true,
    restrictDeletion: true,
    requireLinearHistory: true
  });

  repository.addBranch('main', {
    protected: true,
    headSha: 'main-base-001'
  });

  repository.addBranch('feature/refund-validation', {
    headSha: 'feature-base-001'
  });

  repository.addReviewer('alice');
  repository.addReviewer('bob');
  repository.addReviewer('carol');

  repository.events.on('review.submitted', ({ review }) => {
    console.log(
      `[event] review=${review.id} reviewer=${review.reviewer} state=${review.state}`
    );
  });

  repository.events.on('pull_request.merged', ({ pr, strategy }) => {
    console.log(`[event] PR #${pr.number} merged using ${strategy}.`);
  });

  const pr = repository.createPullRequest({
    number: 101,
    author: 'developer',
    sourceBranch: 'feature/refund-validation',
    targetBranch: 'main',
    title: 'Validate refund requests',
    draft: true
  });

  repository.addCommit(
    pr.number,
    'Add refund amount validation',
    'developer'
  );

  const conversationId = repository.addConversation(
    pr.number,
    'alice',
    'Please verify the zero-value refund boundary.'
  );

  repository.publish(pr.number);

  const beforeReviews = repository.evaluate(pr.number);
  console.log('\nBefore reviews:', beforeReviews);

  await runAsyncChecks(repository, pr.number);

  repository.addReview(
    pr.number,
    'alice',
    ReviewState.APPROVED,
    pr.commits[0].sha
  );

  repository.addReview(
    pr.number,
    'bob',
    ReviewState.APPROVED,
    pr.commits[0].sha
  );

  repository.resolveConversation(pr.number, conversationId);

  const afterReviews = repository.evaluate(pr.number);
  console.log('\nAfter reviews:', afterReviews);

  if (afterReviews.eligible) {
    const mergeSha = repository.merge(pr.number, 'squash');
    console.log('Merge commit:', mergeSha);
  }

  console.log('Final state:', repository.getPullRequest(101).state);

  try {
    repository.reopen(101);
  } catch (error) {
    console.log('Expected state-transition failure:', error.message);
  }
}

main().catch(error => {
  console.error('Fatal workflow error:', error.message);
  process.exitCode = 1;
});
