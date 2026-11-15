"use strict";

/**
 * Stakeholder Communication and Engagement Engine
 *
 * Node.js 18+
 * Standard library only.
 *
 * Event-driven architecture for communication workflows,
 * stakeholder segmentation, policy evaluation, and feedback.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const crypto = require("node:crypto");

const PRIORITY = Object.freeze({
    LOW: "LOW",
    MEDIUM: "MEDIUM",
    HIGH: "HIGH",
    CRITICAL: "CRITICAL"
});

const STATUS = Object.freeze({
    DRAFT: "DRAFT",
    APPROVED: "APPROVED",
    SENT: "SENT",
    ACKNOWLEDGED: "ACKNOWLEDGED",
    ESCALATED: "ESCALATED",
    CANCELLED: "CANCELLED"
});

const REVIEW_STATE = Object.freeze({
    OPEN: "OPEN",
    IN_PROGRESS: "IN_PROGRESS",
    RESOLVED: "RESOLVED"
});

class DomainError extends Error {
    constructor(message, code = "DOMAIN_ERROR") {
        super(message);
        this.name = "DomainError";
        this.code = code;
    }
}

function requireText(value, field) {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new DomainError(`${field} is required.`, "INVALID_INPUT");
    }
    return value.trim();
}

function validateEmail(email) {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        throw new DomainError("Invalid email address.", "INVALID_EMAIL");
    }
}

class Stakeholder {
    constructor({
        id,
        name,
        role,
        department,
        email,
        influence,
        interest,
        engagement,
        preferredChannel,
        active = true
    }) {
        this.id = requireText(id, "ID");
        this.name = requireText(name, "Name");
        this.role = requireText(role, "Role");
        this.department = requireText(department, "Department");

        validateEmail(email);
        this.email = email.toLowerCase();

        const levels = new Set(["LOW", "MEDIUM", "HIGH"]);

        if (!levels.has(influence) || !levels.has(interest)) {
            throw new DomainError("Invalid influence or interest level.");
        }

        const engagements = new Set([
            "UNAWARE",
            "RESISTANT",
            "NEUTRAL",
            "SUPPORTIVE",
            "LEADING"
        ]);

        if (!engagements.has(engagement)) {
            throw new DomainError("Invalid engagement state.");
        }

        this.influence = influence;
        this.interest = interest;
        this.engagement = engagement;
        this.preferredChannel = requireText(
            preferredChannel,
            "Preferred channel"
        );
        this.active = Boolean(active);
    }

    get powerInterestCategory() {
        if (this.influence === "HIGH" && this.interest === "HIGH") {
            return "MANAGE_CLOSELY";
        }

        if (this.influence === "HIGH") {
            return "KEEP_SATISFIED";
        }

        if (this.interest === "HIGH") {
            return "KEEP_INFORMED";
        }

        return "MONITOR";
    }
}

class CommunicationPolicy {
    constructor({
        minimumPriority = "LOW",
        requireApproval = true,
        requireAcknowledgement = false,
        acknowledgementHours = 48,
        allowedChannels = ["EMAIL", "MEETING", "REPORT", "PHONE"]
    } = {}) {
        this.minimumPriority = minimumPriority;
        this.requireApproval = requireApproval;
        this.requireAcknowledgement = requireAcknowledgement;
        this.acknowledgementHours = acknowledgementHours;
        this.allowedChannels = new Set(allowedChannels);

        if (!(minimumPriority in PRIORITY)) {
            throw new DomainError("Invalid minimum priority.");
        }

        if (!Number.isInteger(acknowledgementHours) ||
            acknowledgementHours < 1) {
            throw new DomainError("Invalid acknowledgement period.");
        }
    }

    evaluate(message) {
        const reasons = [];

        if (!this.allowedChannels.has(message.channel)) {
            reasons.push("Communication channel is not permitted.");
        }

        const levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

        if (
            levels.indexOf(message.priority) <
            levels.indexOf(this.minimumPriority)
        ) {
            reasons.push("Message priority is below policy minimum.");
        }

        if (!message.subject || !message.body) {
            reasons.push("Subject and message body are required.");
        }

        return {
            permitted: reasons.length === 0,
            reasons
        };
    }
}

class StakeholderCommunicationManager extends EventEmitter {
    #stakeholders = new Map();
    #messages = new Map();
    #feedback = new Map();
    #policies = new Map();
    #audit = [];

    constructor() {
        super();

        this.on("message.sent", message => {
            this.#record("MESSAGE_SENT", message.id);
        });

        this.on("message.acknowledged", message => {
            this.#record("MESSAGE_ACKNOWLEDGED", message.id);
        });

        this.on("feedback.received", feedback => {
            this.#record("FEEDBACK_RECEIVED", feedback.id);
        });
    }

    #record(event, entityId) {
        this.#audit.push({
            event,
            entityId,
            timestamp: new Date().toISOString()
        });
    }

    addStakeholder(stakeholder) {
        if (!(stakeholder instanceof Stakeholder)) {
            throw new DomainError("Expected Stakeholder instance.");
        }

        if (this.#stakeholders.has(stakeholder.id)) {
            throw new DomainError("Duplicate stakeholder ID.");
        }

        for (const existing of this.#stakeholders.values()) {
            if (existing.email === stakeholder.email) {
                throw new DomainError("Duplicate stakeholder email.");
            }
        }

        this.#stakeholders.set(stakeholder.id, stakeholder);
        this.#record("STAKEHOLDER_CREATED", stakeholder.id);
    }

    addPolicy(stakeholderId, policy) {
        if (!this.#stakeholders.has(stakeholderId)) {
            throw new DomainError("Unknown stakeholder.");
        }

        if (!(policy instanceof CommunicationPolicy)) {
            throw new DomainError("Invalid communication policy.");
        }

        this.#policies.set(stakeholderId, policy);
    }

    createMessage({
        stakeholderId,
        subject,
        body,
        channel,
        priority,
        requiresApproval = true,
        deadline = null
    }) {
        const stakeholder = this.#stakeholders.get(stakeholderId);

        if (!stakeholder || !stakeholder.active) {
            throw new DomainError("Stakeholder unavailable.");
        }

        const message = {
            id: crypto.randomUUID(),
            stakeholderId,
            subject: requireText(subject, "Subject"),
            body: requireText(body, "Body"),
            channel: requireText(channel, "Channel"),
            priority: requireText(priority, "Priority"),
            status: STATUS.DRAFT,
            requiresApproval,
            createdAt: new Date(),
            sentAt: null,
            acknowledgedAt: null,
            deadline: deadline ? new Date(deadline) : null
        };

        if (!Object.values(PRIORITY).includes(message.priority)) {
            throw new DomainError("Invalid priority.");
        }

        if (message.deadline && Number.isNaN(message.deadline.getTime())) {
            throw new DomainError("Invalid deadline.");
        }

        const policy = this.#policies.get(stakeholderId);

        if (policy) {
            const result = policy.evaluate(message);

            if (!result.permitted) {
                throw new DomainError(result.reasons.join(" "));
            }

            message.requiresApproval ||= policy.requireApproval;
        }

        this.#messages.set(message.id, message);
        this.#record("MESSAGE_DRAFTED", message.id);

        return message;
    }

    approveMessage(messageId, approver) {
        const message = this.#getMessage(messageId);

        if (message.status !== STATUS.DRAFT) {
            throw new DomainError("Only drafts can be approved.");
        }

        message.status = STATUS.APPROVED;
        message.approvedBy = requireText(approver, "Approver");

        this.#record("MESSAGE_APPROVED", messageId);
    }

    async sendMessage(messageId, transport) {
        const message = this.#getMessage(messageId);
        const stakeholder = this.#stakeholders.get(message.stakeholderId);

        if (!stakeholder.active) {
            throw new DomainError("Stakeholder is inactive.");
        }

        if (message.status !== STATUS.DRAFT &&
            message.status !== STATUS.APPROVED) {
            throw new DomainError("Message is not eligible for delivery.");
        }

        if (message.requiresApproval &&
            message.status !== STATUS.APPROVED) {
            throw new DomainError("Approval is required before delivery.");
        }

        if (typeof transport !== "function") {
            throw new DomainError("A delivery transport is required.");
        }

        // Delivery is awaited before changing state.
        // A transport failure leaves the message retryable.
        await transport({
            recipient: stakeholder.email,
            channel: message.channel,
            subject: message.subject,
            body: message.body
        });

        message.status = STATUS.SENT;
        message.sentAt = new Date();

        this.emit("message.sent", { ...message });
        return { ...message };
    }

    acknowledge(messageId, stakeholderId) {
        const message = this.#getMessage(messageId);

        if (message.stakeholderId !== stakeholderId) {
            throw new DomainError("Acknowledgement identity mismatch.");
        }

        if (message.status !== STATUS.SENT) {
            throw new DomainError("Message must be sent first.");
        }

        message.status = STATUS.ACKNOWLEDGED;
        message.acknowledgedAt = new Date();

        this.emit("message.acknowledged", { ...message });
    }

    addFeedback({
        stakeholderId,
        messageId,
        sentiment,
        content
    }) {
        const message = this.#getMessage(messageId);

        if (message.stakeholderId !== stakeholderId) {
            throw new DomainError("Feedback ownership mismatch.");
        }

        if (![STATUS.SENT, STATUS.ACKNOWLEDGED].includes(message.status)) {
            throw new DomainError("Message has not been delivered.");
        }

        if (!["POSITIVE", "NEUTRAL", "NEGATIVE"].includes(sentiment)) {
            throw new DomainError("Invalid sentiment.");
        }

        const feedback = {
            id: crypto.randomUUID(),
            stakeholderId,
            messageId,
            sentiment,
            content: requireText(content, "Feedback"),
            state: REVIEW_STATE.OPEN,
            receivedAt: new Date(),
            resolvedAt: null
        };

        this.#feedback.set(feedback.id, feedback);
        this.emit("feedback.received", { ...feedback });

        if (sentiment === "NEGATIVE") {
            this.emit("feedback.negative", { ...feedback });
        }

        return { ...feedback };
    }

    resolveFeedback(feedbackId, resolution) {
        const feedback = this.#feedback.get(feedbackId);

        if (!feedback) {
            throw new DomainError("Feedback not found.");
        }

        if (feedback.state === REVIEW_STATE.RESOLVED) {
            throw new DomainError("Feedback is already resolved.");
        }

        feedback.resolution = requireText(resolution, "Resolution");
        feedback.state = REVIEW_STATE.RESOLVED;
        feedback.resolvedAt = new Date();

        this.#record("FEEDBACK_RESOLVED", feedbackId);
    }

    escalateOverdue(referenceTime = new Date()) {
        const now = new Date(referenceTime);

        if (Number.isNaN(now.getTime())) {
            throw new DomainError("Invalid reference time.");
        }

        const escalations = [];

        for (const message of this.#messages.values()) {
            if (
                message.status === STATUS.SENT &&
                message.deadline &&
                message.deadline < now
            ) {
                message.status = STATUS.ESCALATED;
                escalations.push(message.id);
                this.#record("MESSAGE_ESCALATED", message.id);
            }
        }

        return escalations;
    }

    getStakeholderDashboard() {
        const stakeholders = [...this.#stakeholders.values()];
        const messages = [...this.#messages.values()];
        const feedback = [...this.#feedback.values()];

        const groupBy = (items, key) => {
            const result = {};

            for (const item of items) {
                result[item[key]] = (result[item[key]] || 0) + 1;
            }

            return result;
        };

        const sent = messages.filter(m =>
            [STATUS.SENT, STATUS.ACKNOWLEDGED, STATUS.ESCALATED]
                .includes(m.status)
        ).length;

        const acknowledged = messages.filter(m =>
            m.status === STATUS.ACKNOWLEDGED
        ).length;

        return {
            stakeholderCount: stakeholders.length,
            engagementCategories: groupBy(
                stakeholders,
                "engagement"
            ),
            powerInterestCategories: stakeholders.reduce((result, s) => {
                const category = s.powerInterestCategory;
                result[category] = (result[category] || 0) + 1;
                return result;
            }, {}),
            messageStatuses: groupBy(messages, "status"),
            feedbackSentiments: groupBy(feedback, "sentiment"),
            acknowledgementRate: sent
                ? Number((acknowledged / sent * 100).toFixed(2))
                : 0,
            unresolvedNegativeFeedback: feedback.filter(f =>
                f.sentiment === "NEGATIVE" &&
                f.state !== REVIEW_STATE.RESOLVED
            ).length
        };
    }

    async exportAudit(filename) {
        const data = {
            generatedAt: new Date().toISOString(),
            audit: this.#audit
        };

        await fs.writeFile(
            filename,
            JSON.stringify(data, null, 2),
            { encoding: "utf8", mode: 0o600 }
        );
    }

    #getMessage(id) {
        const message = this.#messages.get(id);

        if (!message) {
            throw new DomainError("Message not found.");
        }

        return message;
    }
}

async function main() {
    const manager = new StakeholderCommunicationManager();

    manager.on("feedback.negative", feedback => {
        console.warn(
            "Negative stakeholder feedback requires attention:",
            feedback.id
        );
    });

    const sponsor = new Stakeholder({
        id: "S-001",
        name: "Ananya Sharma",
        role: "Project Sponsor",
        department: "Executive Management",
        email: "ananya@example.com",
        influence: "HIGH",
        interest: "HIGH",
        engagement: "SUPPORTIVE",
        preferredChannel: "MEETING"
    });

    const operationsLead = new Stakeholder({
        id: "S-002",
        name: "Rahul Verma",
        role: "Operations Lead",
        department: "Operations",
        email: "rahul@example.com",
        influence: "MEDIUM",
        interest: "HIGH",
        engagement: "NEUTRAL",
        preferredChannel: "EMAIL"
    });

    manager.addStakeholder(sponsor);
    manager.addStakeholder(operationsLead);

    manager.addPolicy("S-001", new CommunicationPolicy({
        minimumPriority: "MEDIUM",
        requireApproval: true,
        requireAcknowledgement: true,
        acknowledgementHours: 24,
        allowedChannels: ["EMAIL", "MEETING", "REPORT"]
    }));

    const message = manager.createMessage({
        stakeholderId: "S-001",
        subject: "Project Milestone and Deployment Decision",
        body: [
            "Integration testing has been completed.",
            "Three medium-priority issues remain.",
            "Sponsor approval is requested for the deployment date.",
            "Please acknowledge receipt within 24 hours."
        ].join("\n"),
        channel: "EMAIL",
        priority: PRIORITY.HIGH,
        deadline: new Date(Date.now() + 86400000)
    });

    manager.approveMessage(message.id, "Program Director");

    // Replace this transport with a verified enterprise delivery adapter.
    await manager.sendMessage(message.id, async payload => {
        if (!payload.recipient || !payload.subject) {
            throw new Error("Delivery payload is incomplete.");
        }

        console.log("\nSIMULATED DELIVERY");
        console.log("Recipient:", payload.recipient);
        console.log("Subject:", payload.subject);
    });

    manager.acknowledge(message.id, "S-001");

    const feedback = manager.addFeedback({
        stakeholderId: "S-001",
        messageId: message.id,
        sentiment: "POSITIVE",
        content: "The milestone report is clear. Include deployment risks."
    });

    manager.resolveFeedback(
        feedback.id,
        "Deployment risk assessment added to the next status report."
    );

    console.log("\nSTAKEHOLDER DASHBOARD");
    console.log(
        JSON.stringify(manager.getStakeholderDashboard(), null, 2)
    );

    await manager.exportAudit("stakeholder_audit.json");

    console.log("\nAudit exported successfully.");
}

main().catch(error => {
    console.error("Communication workflow failed:", error.message);
    process.exitCode = 1;
});
