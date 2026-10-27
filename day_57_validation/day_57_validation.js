'use strict';

const { EventEmitter } = require('node:events');
const crypto = require('node:crypto');

const WorkItemState = Object.freeze({
    DRAFT: 'draft',
    OPEN: 'open',
    IN_REVIEW: 'in_review',
    APPROVED: 'approved',
    CHANGES_REQUESTED: 'changes_requested',
    MERGED: 'merged',
    CLOSED: 'closed'
});

const ReviewState = Object.freeze({
    COMMENTED: 'commented',
    APPROVED: 'approved',
    CHANGES_REQUESTED: 'changes_requested',
    DISMISSED: 'dismissed'
});

const CheckState = Object.freeze({
    PASS: 'pass',
    FAIL: 'fail',
    PENDING: 'pending'
});

class ValidationError extends Error {}

class ProjectChange extends EventEmitter {
    constructor({ number, title, authorId, sourceBranch, targetBranch, draft = false }) {
        super();
        this.number = number;
        this.title = title;
        this.authorId = authorId;
        this.sourceBranch = sourceBranch;
        this.targetBranch = targetBranch;
        this.draft = draft;
        this.state = draft ? WorkItemState.DRAFT : WorkItemState.OPEN;
        this.commits = [];
        this.reviews = new Map();
        this.comments = [];
        this.checks = new Map();
        this.openConversations = new Set();
        this.conflicted = false;
        this.baseSynchronized = true;
        this.revision = 0;
    }

    addCommit(message) {
        if ([WorkItemState.MERGED, WorkItemState.CLOSED].includes(this.state)) {
            throw new ValidationError('Completed changes cannot receive new commits.');
        }

        if (typeof message !== 'string' || message.trim().length < 5) {
            throw new ValidationError('Commit message is too short.');
        }

        const commit = {
            id: crypto.randomUUID(),
            message: message.trim(),
            revision: ++this.revision,
            createdAt: new Date().toISOString()
        };

        this.commits.push(commit);

        // A new revision invalidates the assumption that prior approvals
        // still describe the exact proposed state.
        for (const review of this.reviews.values()) {
            if (review.state === ReviewState.APPROVED) {
                review.stale = true;
            }
        }

        this.state = WorkItemState.OPEN;
        this.emit('commitAdded', commit);
        return commit;
    }

    markReadyForReview() {
        if (this.draft) {
            throw new ValidationError('Draft changes must be marked ready before review.');
        }

        if (this.commits.length === 0) {
            throw new ValidationError('At least one commit is required.');
        }

        this.state = WorkItemState.IN_REVIEW;
        this.emit('reviewRequested', this.number);
    }

    addReview(reviewerId, state, message = '') {
        if (reviewerId === this.authorId) {
            throw new ValidationError('Self-approval is not permitted.');
        }

        if (!Object.values(ReviewState).includes(state)) {
            throw new ValidationError('Invalid review state.');
        }

        const review = {
            reviewerId,
            state,
            message,
            stale: false,
            submittedAt: new Date().toISOString()
        };

        this.reviews.set(reviewerId, review);

        if (state === ReviewState.CHANGES_REQUESTED) {
            this.state = WorkItemState.CHANGES_REQUESTED;
        } else if (state === ReviewState.APPROVED) {
            this.state = WorkItemState.APPROVED;
        }

        this.emit('reviewSubmitted', review);
    }

    addConversation(commentId, text) {
        if (!text || text.trim().length < 3) {
            throw new ValidationError('Review conversation cannot be empty.');
        }

        this.comments.push({ commentId, text: text.trim(), resolved: false });
        this.openConversations.add(commentId);
        this.emit('conversationOpened', commentId);
    }

    resolveConversation(commentId) {
        if (!this.openConversations.has(commentId)) {
            throw new ValidationError(`Conversation ${commentId} is not open.`);
        }

        this.openConversations.delete(commentId);
        const comment = this.comments.find(item => item.commentId === commentId);
        if (comment) comment.resolved = true;

        this.emit('conversationResolved', commentId);
    }

    setStatus(name, state) {
        if (!Object.values(CheckState).includes(state)) {
            throw new ValidationError('Invalid status state.');
        }

        this.checks.set(name, { name, state });
        this.emit('statusChanged', { name, state });
    }

    setConflict(value) {
        this.conflicted = Boolean(value);
        this.baseSynchronized = !this.conflicted;
    }
}

class GovernancePolicy {
    constructor({
        requiredReviews = 2,
        requiredChecks = [],
        requireResolvedConversations = true,
        requireLinearHistory = false,
        allowAdministratorBypass = false
    } = {}) {
        this.requiredReviews = requiredReviews;
        this.requiredChecks = new Set(requiredChecks);
        this.requireResolvedConversations = requireResolvedConversations;
        this.requireLinearHistory = requireLinearHistory;
        this.allowAdministratorBypass = allowAdministratorBypass;
    }
}

class MergeEvaluator {
    constructor(users, policy) {
        this.users = users;
        this.policy = policy;
    }

    eligibleReviewers(change) {
        return new Set(
            this.users
                .filter(user =>
                    user.id !== change.authorId &&
                    ['reviewer', 'project_manager', 'maintainer'].includes(user.role)
                )
                .map(user => user.id)
        );
    }

    evaluate(change) {
        const failures = [];

        if (change.draft) failures.push('Change is still a draft.');
        if (change.commits.length === 0) failures.push('No commits exist.');
        if (change.conflicted) failures.push('Merge conflicts exist.');
        if (!change.baseSynchronized) failures.push('Base branch is not synchronized.');

        const eligible = this.eligibleReviewers(change);
        const validApprovals = [...change.reviews.values()]
            .filter(review =>
                review.state === ReviewState.APPROVED &&
                !review.stale &&
                eligible.has(review.reviewerId)
            );

        if (validApprovals.length < this.policy.requiredReviews) {
            failures.push(
                `Requires ${this.policy.requiredReviews} current eligible approval(s).`
            );
        }

        for (const check of this.policy.requiredChecks) {
            const status = change.checks.get(check);

            if (!status) {
                failures.push(`Required check '${check}' is missing.`);
            } else if (status.state !== CheckState.PASS) {
                failures.push(`Required check '${check}' has not passed.`);
            }
        }

        if (
            this.policy.requireResolvedConversations &&
            change.openConversations.size > 0
        ) {
            failures.push('Open review conversations remain.');
        }

        return {
            eligible: failures.length === 0,
            failures
        };
    }
}

async function runAsynchronousChecks(change) {
    const checks = ['scope-validation', 'risk-validation', 'quality-gate'];

    await Promise.all(
        checks.map(async (name, index) => {
            await new Promise(resolve => setTimeout(resolve, 15 + index * 10));
            change.setStatus(name, CheckState.PASS);
        })
    );
}

async function main() {
    const users = [
        { id: 'u1', name: 'Project Manager', role: 'project_manager' },
        { id: 'u2', name: 'Technical Reviewer', role: 'reviewer' },
        { id: 'u3', name: 'Quality Reviewer', role: 'reviewer' },
        { id: 'u4', name: 'Developer', role: 'developer' }
    ];

    const policy = new GovernancePolicy({
        requiredReviews: 2,
        requiredChecks: ['scope-validation', 'risk-validation', 'quality-gate'],
        requireResolvedConversations: true
    });

    const change = new ProjectChange({
        number: 501,
        title: 'Implement project risk approval workflow',
        authorId: 'u4',
        sourceBranch: 'feature/risk-workflow',
        targetBranch: 'main'
    });

    change.on('commitAdded', commit =>
        console.log(`Commit added: ${commit.id}`)
    );

    change.on('reviewSubmitted', review =>
        console.log(`Review received: ${review.reviewerId} -> ${review.state}`)
    );

    change.on('statusChanged', status =>
        console.log(`Status: ${status.name} = ${status.state}`)
    );

    change.addCommit('Implement risk scoring and approval state');
    change.markReadyForReview();

    change.addConversation('c1', 'Clarify the threshold used for high-risk work.');
    change.resolveConversation('c1');

    change.addReview('u2', ReviewState.APPROVED, 'Technical review passed.');
    change.addReview('u3', ReviewState.APPROVED, 'Quality review passed.');

    await runAsynchronousChecks(change);

    const evaluator = new MergeEvaluator(users, policy);
    const decision = evaluator.evaluate(change);

    console.log('\nMerge Eligibility');
    console.log('-----------------');
    console.log(`Eligible: ${decision.eligible}`);

    if (!decision.eligible) {
        decision.failures.forEach(reason => console.log(`- ${reason}`));
    }

    // New commits make existing approvals stale.
    change.addCommit('Correct risk threshold boundary condition');

    const afterRevision = evaluator.evaluate(change);

    console.log('\nAfter New Revision');
    console.log('------------------');
    console.log(`Eligible: ${afterRevision.eligible}`);
    afterRevision.failures.forEach(reason => console.log(`- ${reason}`));

    if (afterRevision.eligible) {
        throw new Error('Stale approvals should not satisfy the policy.');
    }
}

main().catch(error => {
    console.error(`Workflow failure: ${error.message}`);
    process.exitCode = 1;
});
