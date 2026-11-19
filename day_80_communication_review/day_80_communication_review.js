"use strict";

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

const CommunicationType = Object.freeze({
    EMAIL: "email",
    MEETING: "meeting",
    REPORT: "report",
    PRESENTATION: "presentation",
    NOTICE: "notice",
    INSTANT_MESSAGE: "instant_message"
});

const Status = Object.freeze({
    DRAFT: "draft",
    SUBMITTED: "submitted",
    UNDER_REVIEW: "under_review",
    APPROVED: "approved",
    REJECTED: "rejected",
    REVISION_REQUIRED: "revision_required",
    PUBLISHED: "published",
    ARCHIVED: "archived"
});

const Decision = Object.freeze({
    APPROVE: "approve",
    REVISE: "revise",
    REJECT: "reject"
});

const Severity = Object.freeze({
    LOW: "low",
    MEDIUM: "medium",
    HIGH: "high",
    CRITICAL: "critical"
});

class CommunicationError extends Error {}
class ValidationError extends CommunicationError {}
class AuthorizationError extends CommunicationError {}
class WorkflowError extends CommunicationError {}

const DEFAULT_POLICY = Object.freeze({
    minimumScore: 70,
    requiredApprovals: 2,
    blockCriticalComments: true,
    requireObjectives: true,
    mandatoryCriteria: Object.freeze([
        "clarity",
        "accuracy",
        "completeness",
        "audienceAlignment",
        "timeliness",
        "actionability",
        "professionalism"
    ]),
    minimumDeliveryRate: 95,
    minimumAcknowledgementRate: 80
});

function validateText(value, field) {
    if (typeof value !== "string" || !value.trim()) {
        throw new ValidationError(`${field} is required.`);
    }
    return value.trim();
}

function validateScore(score) {
    if (typeof score !== "number" || !Number.isFinite(score)) {
        throw new ValidationError("Score must be a finite number.");
    }
    if (score < 0 || score > 100) {
        throw new ValidationError("Score must be between 0 and 100.");
    }
    return score;
}

class CommunicationReviewSystem extends EventEmitter {
    #stakeholders = new Map();
    #communications = new Map();
    #reviews = new Map();
    #comments = new Map();
    #audit = [];
    #policy;

    constructor(policy = {}) {
        super();

        this.#policy = Object.freeze({
            ...DEFAULT_POLICY,
            ...policy,
            mandatoryCriteria: Object.freeze([
                ...(policy.mandatoryCriteria ??
                    DEFAULT_POLICY.mandatoryCriteria)
            ])
        });

        if (
            !Number.isInteger(this.#policy.requiredApprovals) ||
            this.#policy.requiredApprovals < 1
        ) {
            throw new ValidationError("At least one approval is required.");
        }
    }

    #record(action, entityId, actorId) {
        const event = Object.freeze({
            id: crypto.randomUUID(),
            action,
            entityId,
            actorId,
            timestamp: new Date().toISOString()
        });

        this.#audit.push(event);
        this.emit("audit", event);
    }

    #getCommunication(id) {
        const communication = this.#communications.get(id);

        if (!communication) {
            throw new ValidationError("Communication not found.");
        }

        return communication;
    }

    #getStakeholder(id) {
        const stakeholder = this.#stakeholders.get(id);

        if (!stakeholder) {
            throw new ValidationError("Stakeholder not found.");
        }

        return stakeholder;
    }

    #transition(communication, nextStatus, actorId) {
        const transitions = {
            [Status.DRAFT]: [Status.SUBMITTED],
            [Status.SUBMITTED]: [
                Status.UNDER_REVIEW,
                Status.REJECTED
            ],
            [Status.UNDER_REVIEW]: [
                Status.APPROVED,
                Status.REJECTED,
                Status.REVISION_REQUIRED
            ],
            [Status.REVISION_REQUIRED]: [Status.SUBMITTED],
            [Status.APPROVED]: [Status.PUBLISHED],
            [Status.PUBLISHED]: [Status.ARCHIVED],
            [Status.REJECTED]: [Status.ARCHIVED],
            [Status.ARCHIVED]: []
        };

        if (!transitions[communication.status].includes(nextStatus)) {
            throw new WorkflowError(
                `Invalid transition: ${communication.status} -> ${nextStatus}`
            );
        }

        const previous = communication.status;
        communication.status = nextStatus;

        this.#record(
            `status:${previous}->${nextStatus}`,
            communication.id,
            actorId
        );

        this.emit("statusChanged", {
            communicationId: communication.id,
            previous,
            current: nextStatus
        });
    }

    registerStakeholder({ id, name, role, department, active = true }) {
        validateText(id, "Stakeholder ID");
        validateText(name, "Stakeholder name");
        validateText(role, "Role");
        validateText(department, "Department");

        if (this.#stakeholders.has(id)) {
            throw new ValidationError("Duplicate stakeholder.");
        }

        this.#stakeholders.set(id, Object.freeze({
            id,
            name,
            role,
            department,
            active: Boolean(active)
        }));
    }

    createCommunication(input) {
        const {
            title,
            type,
            senderId,
            recipients,
            subject,
            content,
            objectives = [],
            sensitivity = "internal",
            acknowledgementRequired = false
        } = input;

        validateText(title, "Title");
        validateText(subject, "Subject");
        validateText(content, "Content");

        if (!Object.values(CommunicationType).includes(type)) {
            throw new ValidationError("Invalid communication type.");
        }

        const sender = this.#getStakeholder(senderId);

        if (!sender.active) {
            throw new AuthorizationError("Inactive sender.");
        }

        if (!Array.isArray(recipients) || recipients.length === 0) {
            throw new ValidationError("Recipients are required.");
        }

        if (new Set(recipients).size !== recipients.length) {
            throw new ValidationError("Duplicate recipients detected.");
        }

        for (const id of recipients) {
            if (!this.#getStakeholder(id).active) {
                throw new ValidationError(`Inactive recipient: ${id}`);
            }
        }

        if (
            this.#policy.requireObjectives &&
            (!Array.isArray(objectives) || objectives.length === 0)
        ) {
            throw new ValidationError("Communication objectives are required.");
        }

        if (
            !["public", "internal", "confidential", "restricted"]
                .includes(sensitivity)
        ) {
            throw new ValidationError("Invalid sensitivity classification.");
        }

        const communication = {
            id: crypto.randomUUID(),
            title: title.trim(),
            type,
            senderId,
            recipients: [...recipients],
            subject: subject.trim(),
            content: content.trim(),
            objectives: [...objectives],
            sensitivity,
            acknowledgementRequired,
            status: Status.DRAFT,
            version: 1,
            createdAt: new Date().toISOString(),
            delivery: {
                delivered: 0,
                read: 0,
                acknowledged: 0
            }
        };

        this.#communications.set(communication.id, communication);
        this.#reviews.set(communication.id, new Map());
        this.#comments.set(communication.id, []);

        this.#record("communication_created", communication.id, senderId);
        this.emit("communicationCreated", { id: communication.id });

        return communication.id;
    }

    submit(id, actorId) {
        const communication = this.#getCommunication(id);

        if (communication.senderId !== actorId) {
            throw new AuthorizationError("Only the sender can submit.");
        }

        this.#transition(communication, Status.SUBMITTED, actorId);
    }

    beginReview(id, reviewerId) {
        const communication = this.#getCommunication(id);
        const reviewer = this.#getStakeholder(reviewerId);

        if (!reviewer.active) {
            throw new AuthorizationError("Inactive reviewer.");
        }

        if (reviewerId === communication.senderId) {
            throw new AuthorizationError("Self-review is prohibited.");
        }

        if (
            communication.status !== Status.SUBMITTED &&
            communication.status !== Status.UNDER_REVIEW
        ) {
            throw new WorkflowError("Communication is not reviewable.");
        }

        if (communication.status === Status.SUBMITTED) {
            this.#transition(
                communication,
                Status.UNDER_REVIEW,
                reviewerId
            );
        }
    }

    addComment(id, reviewerId, criterion, message, severity) {
        const communication = this.#getCommunication(id);

        this.#getStakeholder(reviewerId);

        if (reviewerId === communication.senderId) {
            throw new AuthorizationError("Sender cannot review own content.");
        }

        if (communication.status !== Status.UNDER_REVIEW) {
            throw new WorkflowError("No active review.");
        }

        validateText(criterion, "Criterion");
        validateText(message, "Comment");

        if (!Object.values(Severity).includes(severity)) {
            throw new ValidationError("Invalid severity.");
        }

        const comment = {
            id: crypto.randomUUID(),
            communicationId: id,
            reviewerId,
            criterion: criterion.trim(),
            message: message.trim(),
            severity,
            resolved: false,
            createdAt: new Date().toISOString()
        };

        this.#comments.get(id).push(comment);

        this.#record("comment_added", comment.id, reviewerId);
        this.emit("commentAdded", comment);

        return comment.id;
    }

    resolveComment(id, commentId, actorId) {
        const communication = this.#getCommunication(id);

        if (communication.senderId !== actorId) {
            throw new AuthorizationError("Only the owner can resolve comments.");
        }

        const comment = this.#comments.get(id).find(
            item => item.id === commentId
        );

        if (!comment) {
            throw new ValidationError("Comment not found.");
        }

        if (comment.resolved) {
            return false;
        }

        comment.resolved = true;
        this.#record("comment_resolved", commentId, actorId);

        return true;
    }

    recordReview(id, reviewerId, scores, decision, feedback) {
        const communication = this.#getCommunication(id);
        const reviewer = this.#getStakeholder(reviewerId);

        if (!reviewer.active) {
            throw new AuthorizationError("Inactive reviewer.");
        }

        if (reviewerId === communication.senderId) {
            throw new AuthorizationError("Self-review is prohibited.");
        }

        if (communication.status !== Status.UNDER_REVIEW) {
            throw new WorkflowError("Review is not active.");
        }

        if (!Object.values(Decision).includes(decision)) {
            throw new ValidationError("Invalid review decision.");
        }

        if (this.#reviews.get(id).has(reviewerId)) {
            throw new WorkflowError("Reviewer has already submitted a review.");
        }

        if (!scores || typeof scores !== "object" || Array.isArray(scores)) {
            throw new ValidationError("Scores must be an object.");
        }

        const missing = this.#policy.mandatoryCriteria.filter(
            criterion => !Object.hasOwn(scores, criterion)
        );

        if (missing.length) {
            throw new ValidationError(
                `Missing criteria: ${missing.join(", ")}`
            );
        }

        const entries = Object.entries(scores);

        if (entries.length === 0) {
            throw new ValidationError("Scores cannot be empty.");
        }

        for (const [criterion, score] of entries) {
            validateText(criterion, "Criterion");
            validateScore(score);
        }

        const average = entries.reduce(
            (sum, [, score]) => sum + score,
            0
        ) / entries.length;

        if (
            decision === Decision.APPROVE &&
            average < this.#policy.minimumScore
        ) {
            throw new ValidationError("Score does not qualify for approval.");
        }

        const review = Object.freeze({
            id: crypto.randomUUID(),
            reviewerId,
            communicationId: id,
            decision,
            scores: Object.freeze({ ...scores }),
            averageScore: Number(average.toFixed(2)),
            feedback: validateText(feedback, "Feedback"),
            version: communication.version,
            createdAt: new Date().toISOString()
        });

        this.#reviews.get(id).set(reviewerId, review);

        this.#record("review_recorded", review.id, reviewerId);
        this.emit("reviewRecorded", review);

        if (decision === Decision.REJECT) {
            this.#transition(communication, Status.REJECTED, reviewerId);
        } else if (decision === Decision.REVISE) {
            this.#transition(
                communication,
                Status.REVISION_REQUIRED,
                reviewerId
            );
        }

        return review;
    }

    evaluate(id) {
        const communication = this.#getCommunication(id);
        const reviews = [...this.#reviews.get(id).values()];
        const comments = this.#comments.get(id);

        const currentReviews = reviews.filter(
            review => review.version === communication.version
        );

        const approvals = currentReviews.filter(
            review =>
                review.decision === Decision.APPROVE &&
                review.averageScore >= this.#policy.minimumScore &&
                this.#getStakeholder(review.reviewerId).active
        );

        const unresolvedCritical = comments.filter(
            comment =>
                comment.severity === Severity.CRITICAL &&
                !comment.resolved
        );

        const rejected = currentReviews.some(
            review => review.decision === Decision.REJECT
        );

        const revisions = currentReviews.some(
            review => review.decision === Decision.REVISE
        );

        const reasons = [];

        if (approvals.length < this.#policy.requiredApprovals) {
            reasons.push("Insufficient eligible approvals.");
        }

        if (rejected) {
            reasons.push("Communication rejected.");
        }

        if (revisions) {
            reasons.push("Revision requested.");
        }

        if (
            this.#policy.blockCriticalComments &&
            unresolvedCritical.length
        ) {
            reasons.push("Unresolved critical comments.");
        }

        const averageScore = currentReviews.length
            ? currentReviews.reduce(
                (sum, review) => sum + review.averageScore,
                0
            ) / currentReviews.length
            : 0;

        return Object.freeze({
            communicationId: id,
            version: communication.version,
            approvalCount: approvals.length,
            requiredApprovals: this.#policy.requiredApprovals,
            averageScore: Number(averageScore.toFixed(2)),
            unresolvedCritical: unresolvedCritical.length,
            eligible: reasons.length === 0,
            reasons: Object.freeze(reasons)
        });
    }

    approvePublication(id, actorId) {
        const communication = this.#getCommunication(id);

        if (communication.senderId !== actorId) {
            throw new AuthorizationError("Only the sender can authorize publication.");
        }

        if (communication.status !== Status.UNDER_REVIEW) {
            throw new WorkflowError("Communication is not under review.");
        }

        const result = this.evaluate(id);

        if (!result.eligible) {
            throw new WorkflowError(result.reasons.join(" "));
        }

        this.#transition(communication, Status.APPROVED, actorId);
    }

    publish(id, actorId) {
        const communication = this.#getCommunication(id);

        if (communication.senderId !== actorId) {
            throw new AuthorizationError("Only the sender can publish.");
        }

        if (communication.status !== Status.APPROVED) {
            throw new WorkflowError("Publication requires approval.");
        }

        this.#transition(communication, Status.PUBLISHED, actorId);
        this.emit("published", { id });
    }

    updateContent(id, actorId, newContent) {
        const communication = this.#getCommunication(id);

        if (communication.senderId !== actorId) {
            throw new AuthorizationError("Only the owner can edit content.");
        }

        if (
            communication.status === Status.PUBLISHED ||
            communication.status === Status.ARCHIVED
        ) {
            throw new WorkflowError("Published content cannot be edited.");
        }

        communication.content = validateText(newContent, "Content");
        communication.version++;

        this.#reviews.get(id).clear();
        this.#transition(
            communication,
            Status.REVISION_REQUIRED,
            actorId
        );
    }

    recordDelivery(id, delivered, read, acknowledged) {
        const communication = this.#getCommunication(id);

        if (communication.status !== Status.PUBLISHED) {
            throw new WorkflowError("Communication must be published.");
        }

        const total = communication.recipients.length;

        if (
            !Number.isInteger(delivered) ||
            !Number.isInteger(read) ||
            !Number.isInteger(acknowledged) ||
            acknowledged < 0 ||
            acknowledged > read ||
            read > delivered ||
            delivered > total
        ) {
            throw new ValidationError("Invalid delivery metrics.");
        }

        communication.delivery = {
            delivered,
            read,
            acknowledged
        };

        this.#record("delivery_metrics_recorded", id, "system");

        return this.communicationMetrics(id);
    }

    communicationMetrics(id) {
        const communication = this.#getCommunication(id);
        const total = communication.recipients.length;
        const delivery = communication.delivery;

        const percentage = value =>
            total === 0 ? 0 : Number((value / total * 100).toFixed(2));

        return Object.freeze({
            recipients: total,
            deliveryRate: percentage(delivery.delivered),
            readRate: percentage(delivery.read),
            acknowledgementRate: percentage(delivery.acknowledged),
            deliverySatisfactory:
                percentage(delivery.delivered) >=
                this.#policy.minimumDeliveryRate,
            acknowledgementSatisfactory:
                !communication.acknowledgementRequired ||
                percentage(delivery.acknowledged) >=
                this.#policy.minimumAcknowledgementRate
        });
    }

    getCommunication(id) {
        const communication = this.#getCommunication(id);

        return structuredClone(communication);
    }

    managementReport() {
        const statuses = new Map();
        const types = new Map();

        for (const communication of this.#communications.values()) {
            statuses.set(
                communication.status,
                (statuses.get(communication.status) || 0) + 1
            );

            types.set(
                communication.type,
                (types.get(communication.type) || 0) + 1
            );
        }

        return {
            totalCommunications: this.#communications.size,
            totalReviews: [...this.#reviews.values()]
                .reduce((sum, map) => sum + map.size, 0),
            totalComments: [...this.#comments.values()]
                .reduce((sum, comments) => sum + comments.length, 0),
            statuses: Object.fromEntries(statuses),
            types: Object.fromEntries(types),
            auditEvents: this.#audit.length
        };
    }

    getAuditTrail() {
        return structuredClone(this.#audit);
    }
}

async function runDemonstration() {
    const system = new CommunicationReviewSystem({
        requiredApprovals: 2,
        minimumScore: 70
    });

    system.on("statusChanged", event => {
        console.log(
            `STATUS: ${event.previous} -> ${event.current}`
        );
    });

    system.on("published", event => {
        console.log(`Communication ${event.id} published.`);
    });

    system.on("audit", event => {
        console.log(`AUDIT: ${event.action}`);
    });

    system.registerStakeholder({
        id: "EMP001",
        name: "Project Manager",
        role: "manager",
        department: "Operations"
    });

    system.registerStakeholder({
        id: "EMP002",
        name: "Quality Officer",
        role: "reviewer",
        department: "Quality"
    });

    system.registerStakeholder({
        id: "EMP003",
        name: "Technical Lead",
        role: "reviewer",
        department: "Technology"
    });

    system.registerStakeholder({
        id: "EMP004",
        name: "Department Head",
        role: "recipient",
        department: "Management"
    });

    system.registerStakeholder({
        id: "EMP005",
        name: "Field Coordinator",
        role: "recipient",
        department: "Operations"
    });

    const communicationId = system.createCommunication({
        title: "Monthly Operational Review",
        type: CommunicationType.REPORT,
        senderId: "EMP001",
        recipients: ["EMP004", "EMP005"],
        subject: "Monthly Performance and Corrective Actions",
        content:
            "This report covers performance, pending activities, " +
            "operational risks, and assigned corrective actions.",
        objectives: [
            "Report performance",
            "Identify risks",
            "Assign actions"
        ],
        acknowledgementRequired: true
    });

    system.submit(communicationId, "EMP001");

    const criteria = {
        clarity: 90,
        accuracy: 95,
        completeness: 90,
        audienceAlignment: 92,
        timeliness: 90,
        actionability: 88,
        professionalism: 95
    };

    for (const reviewerId of ["EMP002", "EMP003"]) {
        system.beginReview(communicationId, reviewerId);

        system.recordReview(
            communicationId,
            reviewerId,
            criteria,
            Decision.APPROVE,
            "The communication meets the review criteria."
        );
    }

    console.log(
        "\nELIGIBILITY:",
        system.evaluate(communicationId)
    );

    system.approvePublication(communicationId, "EMP001");
    system.publish(communicationId, "EMP001");

    console.log(
        "\nDELIVERY:",
        system.recordDelivery(communicationId, 2, 2, 2)
    );

    console.log(
        "\nMANAGEMENT REPORT:",
        system.managementReport()
    );

    console.log(
        "\nAUDIT EVENTS:",
        system.getAuditTrail().length
    );
}

if (require.main === module) {
    runDemonstration().catch(error => {
        console.error("SYSTEM FAILURE:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    CommunicationReviewSystem,
    CommunicationType,
    Status,
    Decision,
    Severity,
    CommunicationError,
    ValidationError,
    AuthorizationError,
    WorkflowError
};
