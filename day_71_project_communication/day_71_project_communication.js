"use strict";

/*
 * PROJECT COMMUNICATION MANAGEMENT
 * Introduction to Project Communication
 *
 * Node.js 18+ compatible.
 *
 * Engineering perspective:
 * - Event-driven communication
 * - Stakeholder subscriptions
 * - Communication policies
 * - Asynchronous delivery
 * - Retry handling
 * - Acknowledgement tracking
 * - Meeting and decision workflows
 * - Action-item management
 * - Communication analytics
 * - Audit events
 *
 * Run:
 * node project_communication.js
 */

const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");
const fs = require("node:fs/promises");

// ============================================================
// ENUMERATIONS
// ============================================================

const Role = Object.freeze({
    PROJECT_MANAGER: "PROJECT_MANAGER",
    SPONSOR: "SPONSOR",
    DEVELOPER: "DEVELOPER",
    CLIENT: "CLIENT",
    VENDOR: "VENDOR",
    EXECUTIVE: "EXECUTIVE"
});

const Channel = Object.freeze({
    EMAIL: "EMAIL",
    MEETING: "MEETING",
    CHAT: "CHAT",
    REPORT: "REPORT",
    PHONE: "PHONE",
    PORTAL: "PORTAL"
});

const Purpose = Object.freeze({
    INFORMATION: "INFORMATION",
    STATUS_UPDATE: "STATUS_UPDATE",
    DECISION: "DECISION",
    REQUEST: "REQUEST",
    ESCALATION: "ESCALATION"
});

const Confidentiality = Object.freeze({
    PUBLIC: 1,
    INTERNAL: 2,
    CONFIDENTIAL: 3,
    RESTRICTED: 4
});

const MessageState = Object.freeze({
    DRAFT: "DRAFT",
    SENT: "SENT",
    ACKNOWLEDGED: "ACKNOWLEDGED",
    ESCALATED: "ESCALATED"
});

const ActionState = Object.freeze({
    OPEN: "OPEN",
    IN_PROGRESS: "IN_PROGRESS",
    BLOCKED: "BLOCKED",
    COMPLETED: "COMPLETED",
    CANCELLED: "CANCELLED"
});

// ============================================================
// CUSTOM ERRORS
// ============================================================

class CommunicationError extends Error {}
class ValidationError extends CommunicationError {}
class AuthorizationError extends CommunicationError {}
class NotFoundError extends CommunicationError {}
class StateTransitionError extends CommunicationError {}

// ============================================================
// VALIDATION UTILITIES
// ============================================================

function requireText(value, field) {
    if (typeof value !== "string" || !value.trim()) {
        throw new ValidationError(`${field} is required.`);
    }

    return value.trim();
}

function requireEnum(value, enumeration, field) {
    if (!Object.values(enumeration).includes(value)) {
        throw new ValidationError(`Invalid ${field}: ${value}`);
    }
}

function requireIdentifier(value, field) {
    return requireText(value, field);
}

function requireDate(value, field) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        throw new ValidationError(`Invalid ${field}.`);
    }

    return date;
}

// ============================================================
// STAKEHOLDER DOMAIN
// ============================================================

class Stakeholder {
    constructor({
        id,
        name,
        email,
        role,
        influence,
        interest,
        clearance
    }) {
        this.id = requireIdentifier(id, "Stakeholder ID");
        this.name = requireText(name, "Stakeholder name");
        this.email = requireText(email, "Email");

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.email)) {
            throw new ValidationError("Invalid email address.");
        }

        requireEnum(role, Role, "role");

        if (!Number.isInteger(influence) || influence < 1 || influence > 5) {
            throw new ValidationError("Influence must be 1-5.");
        }

        if (!Number.isInteger(interest) || interest < 1 || interest > 5) {
            throw new ValidationError("Interest must be 1-5.");
        }

        if (!Number.isInteger(clearance) || clearance < 1 || clearance > 4) {
            throw new ValidationError("Invalid confidentiality clearance.");
        }

        this.role = role;
        this.influence = influence;
        this.interest = interest;
        this.clearance = clearance;
        this.active = true;
    }

    get engagementStrategy() {
        const score = this.influence * this.interest;

        if (score >= 16) return "MANAGE_CLOSLY";
        if (this.influence >= 4) return "KEEP_SATISFIED";
        if (this.interest >= 4) return "KEEP_INFORMED";

        return "MONITOR";
    }
}

// ============================================================
// COMMUNICATION POLICY
// ============================================================

class CommunicationPolicy {
    constructor() {
        this.rules = new Map([
            [Role.PROJECT_MANAGER, new Set(Object.values(Purpose))],
            [Role.SPONSOR, new Set([
                Purpose.INFORMATION,
                Purpose.STATUS_UPDATE,
                Purpose.DECISION,
                Purpose.ESCALATION
            ])],
            [Role.DEVELOPER, new Set([
                Purpose.INFORMATION,
                Purpose.STATUS_UPDATE,
                Purpose.REQUEST
            ])],
            [Role.CLIENT, new Set([
                Purpose.INFORMATION,
                Purpose.STATUS_UPDATE,
                Purpose.DECISION,
                Purpose.REQUEST
            ])],
            [Role.VENDOR, new Set([
                Purpose.INFORMATION,
                Purpose.STATUS_UPDATE,
                Purpose.REQUEST
            ])],
            [Role.EXECUTIVE, new Set([
                Purpose.INFORMATION,
                Purpose.STATUS_UPDATE,
                Purpose.ESCALATION
            ])]
        ]);
    }

    authorizeSender(stakeholder, purpose) {
        const permitted = this.rules.get(stakeholder.role);

        if (!permitted || !permitted.has(purpose)) {
            throw new AuthorizationError(
                `${stakeholder.role} cannot send ${purpose} messages.`
            );
        }
    }

    authorizeRecipient(stakeholder, confidentiality) {
        if (!stakeholder.active) {
            throw new AuthorizationError("Inactive recipient.");
        }

        if (stakeholder.clearance < confidentiality) {
            throw new AuthorizationError(
                `${stakeholder.name} lacks sufficient clearance.`
            );
        }
    }
}

// ============================================================
// EVENT-DRIVEN COMMUNICATION SERVICE
// ============================================================

class ProjectCommunicationService extends EventEmitter {

    constructor(projectName, policy = new CommunicationPolicy()) {
        super();

        this.projectName = requireText(projectName, "Project name");
        this.policy = policy;

        this.stakeholders = new Map();
        this.messages = new Map();
        this.meetings = new Map();
        this.actions = new Map();
        this.decisions = new Map();

        this.audit = [];

        this.on("message.sent", event => {
            this.recordAudit("MESSAGE_SENT", event.messageId, event.senderId);
        });

        this.on("message.acknowledged", event => {
            this.recordAudit(
                "MESSAGE_ACKNOWLEDGED",
                event.messageId,
                event.stakeholderId
            );
        });

        this.on("message.escalated", event => {
            this.recordAudit(
                "MESSAGE_ESCALATED",
                event.messageId,
                event.senderId
            );
        });
    }

    recordAudit(type, entityId, actorId, details = {}) {
        this.audit.push({
            id: randomUUID(),
            type,
            entityId,
            actorId,
            details,
            timestamp: new Date().toISOString()
        });
    }

    getStakeholder(id) {
        const stakeholder = this.stakeholders.get(id);

        if (!stakeholder || !stakeholder.active) {
            throw new NotFoundError(`Active stakeholder not found: ${id}`);
        }

        return stakeholder;
    }

    // --------------------------------------------------------
    // STAKEHOLDER REGISTRATION
    // --------------------------------------------------------

    registerStakeholder(data) {
        const stakeholder = new Stakeholder(data);

        if (this.stakeholders.has(stakeholder.id)) {
            throw new ValidationError("Duplicate stakeholder ID.");
        }

        for (const existing of this.stakeholders.values()) {
            if (existing.email.toLowerCase() === stakeholder.email.toLowerCase()) {
                throw new ValidationError("Email already registered.");
            }
        }

        this.stakeholders.set(stakeholder.id, stakeholder);

        this.recordAudit(
            "STAKEHOLDER_REGISTERED",
            stakeholder.id,
            stakeholder.id
        );

        this.emit("stakeholder.registered", {
            stakeholderId: stakeholder.id
        });

        return stakeholder;
    }

    // --------------------------------------------------------
    // MESSAGE CREATION
    // --------------------------------------------------------

    createMessage({
        senderId,
        recipientIds,
        subject,
        body,
        channel,
        purpose,
        confidentiality
    }) {
        const sender = this.getStakeholder(senderId);

        requireEnum(channel, Channel, "channel");
        requireEnum(purpose, Purpose, "purpose");

        if (!Number.isInteger(confidentiality) ||
            confidentiality < 1 ||
            confidentiality > 4) {
            throw new ValidationError("Invalid confidentiality level.");
        }

        if (!Array.isArray(recipientIds) || recipientIds.length === 0) {
            throw new ValidationError("Recipients are required.");
        }

        if (new Set(recipientIds).size !== recipientIds.length) {
            throw new ValidationError("Duplicate recipients.");
        }

        this.policy.authorizeSender(sender, purpose);

        for (const recipientId of recipientIds) {
            this.policy.authorizeRecipient(
                this.getStakeholder(recipientId),
                confidentiality
            );
        }

        const message = {
            id: randomUUID(),
            senderId,
            recipientIds: [...recipientIds],
            subject: requireText(subject, "Subject"),
            body: requireText(body, "Body"),
            channel,
            purpose,
            confidentiality,
            state: MessageState.DRAFT,
            acknowledgements: new Set(),
            createdAt: new Date().toISOString(),
            sentAt: null
        };

        this.messages.set(message.id, message);

        this.recordAudit(
            "MESSAGE_CREATED",
            message.id,
            senderId
        );

        return message;
    }

    // --------------------------------------------------------
    // ASYNCHRONOUS MESSAGE DELIVERY
    // --------------------------------------------------------

    async dispatchMessage(messageId, transport) {
        const message = this.messages.get(messageId);

        if (!message) {
            throw new NotFoundError("Message not found.");
        }

        if (message.state !== MessageState.DRAFT) {
            throw new StateTransitionError("Message is not a draft.");
        }

        if (typeof transport !== "function") {
            throw new ValidationError("A delivery function is required.");
        }

        const sender = this.getStakeholder(message.senderId);

        this.policy.authorizeSender(sender, message.purpose);

        // Recheck access immediately before external dispatch.
        for (const recipientId of message.recipientIds) {
            this.policy.authorizeRecipient(
                this.getStakeholder(recipientId),
                message.confidentiality
            );
        }

        const results = await Promise.allSettled(
            message.recipientIds.map(async recipientId => {
                const recipient = this.getStakeholder(recipientId);

                let lastError;

                for (let attempt = 1; attempt <= 3; attempt++) {
                    try {
                        await transport({
                            messageId: message.id,
                            recipient,
                            subject: message.subject,
                            body: message.body,
                            channel: message.channel
                        });

                        return {
                            recipientId,
                            delivered: true,
                            attempts: attempt
                        };
                    } catch (error) {
                        lastError = error;

                        if (attempt < 3) {
                            await new Promise(resolve =>
                                setTimeout(resolve, attempt * 100)
                            );
                        }
                    }
                }

                return {
                    recipientId,
                    delivered: false,
                    attempts: 3,
                    error: lastError?.message || "Delivery failed"
                };
            })
        );

        const deliveries = results.map(result =>
            result.status === "fulfilled"
                ? result.value
                : {
                    delivered: false,
                    error: result.reason?.message || "Unexpected failure"
                }
        );

        message.sentAt = new Date().toISOString();

        // Partial delivery is recorded as an escalated state rather
        // than incorrectly declaring the entire message delivered.
        const allDelivered = deliveries.every(
            delivery => delivery.delivered
        );

        message.state = allDelivered
            ? MessageState.SENT
            : MessageState.ESCALATED;

        this.emit("message.sent", {
            messageId,
            senderId: message.senderId,
            deliveries
        });

        if (!allDelivered) {
            this.emit("message.escalated", {
                messageId,
                senderId: message.senderId,
                deliveries
            });
        }

        return {
            messageId,
            state: message.state,
            deliveries
        };
    }

    // --------------------------------------------------------
    // ACKNOWLEDGEMENTS
    // --------------------------------------------------------

    acknowledge(messageId, stakeholderId) {
        const message = this.messages.get(messageId);

        if (!message) {
            throw new NotFoundError("Message not found.");
        }

        if (![MessageState.SENT, MessageState.ACKNOWLEDGED].includes(message.state)) {
            throw new StateTransitionError(
                "Message cannot be acknowledged in its current state."
            );
        }

        if (!message.recipientIds.includes(stakeholderId)) {
            throw new AuthorizationError("Recipient is not authorized.");
        }

        message.acknowledgements.add(stakeholderId);

        if (message.acknowledgements.size === message.recipientIds.length) {
            message.state = MessageState.ACKNOWLEDGED;
        }

        this.emit("message.acknowledged", {
            messageId,
            stakeholderId
        });

        return message.state;
    }

    // --------------------------------------------------------
    // MEETING MANAGEMENT
    // --------------------------------------------------------

    scheduleMeeting({
        organizerId,
        participantIds,
        title,
        scheduledAt,
        agenda
    }) {
        this.getStakeholder(organizerId);

        if (!Array.isArray(participantIds) || participantIds.length === 0) {
            throw new ValidationError("Meeting participants are required.");
        }

        if (new Set(participantIds).size !== participantIds.length) {
            throw new ValidationError("Duplicate meeting participants.");
        }

        participantIds.forEach(id => this.getStakeholder(id));

        if (!Array.isArray(agenda) || agenda.length === 0) {
            throw new ValidationError("Meeting agenda is required.");
        }

        const meeting = {
            id: randomUUID(),
            organizerId,
            participantIds: [...participantIds],
            title: requireText(title, "Meeting title"),
            scheduledAt: requireDate(scheduledAt, "Meeting date"),
            agenda: agenda.map(item => requireText(item, "Agenda item")),
            minutes: null,
            completed: false
        };

        this.meetings.set(meeting.id, meeting);

        this.recordAudit(
            "MEETING_SCHEDULED",
            meeting.id,
            organizerId
        );

        return meeting;
    }

    finalizeMeeting(meetingId, organizerId, minutes) {
        const meeting = this.meetings.get(meetingId);

        if (!meeting) {
            throw new NotFoundError("Meeting not found.");
        }

        if (meeting.organizerId !== organizerId) {
            throw new AuthorizationError("Only the organizer can finalize.");
        }

        if (meeting.completed) {
            throw new StateTransitionError("Meeting already finalized.");
        }

        meeting.minutes = requireText(minutes, "Meeting minutes");
        meeting.completed = true;

        this.recordAudit(
            "MEETING_FINALIZED",
            meetingId,
            organizerId
        );
    }

    recordDecision(meetingId, ownerId, description, approved) {
        const meeting = this.meetings.get(meetingId);

        if (!meeting || !meeting.completed) {
            throw new StateTransitionError(
                "Decision requires finalized meeting minutes."
            );
        }

        this.getStakeholder(ownerId);

        if (typeof approved !== "boolean") {
            throw new ValidationError("Approval must be boolean.");
        }

        const decision = {
            id: randomUUID(),
            meetingId,
            ownerId,
            description: requireText(description, "Decision description"),
            approved,
            recordedAt: new Date().toISOString()
        };

        this.decisions.set(decision.id, decision);

        this.recordAudit(
            "DECISION_RECORDED",
            decision.id,
            ownerId
        );

        return decision;
    }

    // --------------------------------------------------------
    // ACTION MANAGEMENT
    // --------------------------------------------------------

    createAction({
        description,
        assignedTo,
        createdBy,
        dueDate
    }) {
        this.getStakeholder(assignedTo);
        this.getStakeholder(createdBy);

        const action = {
            id: randomUUID(),
            description: requireText(description, "Action description"),
            assignedTo,
            createdBy,
            dueDate: requireDate(dueDate, "Due date"),
            state: ActionState.OPEN,
            completedAt: null
        };

        this.actions.set(action.id, action);

        this.recordAudit(
            "ACTION_CREATED",
            action.id,
            createdBy
        );

        return action;
    }

    updateAction(actionId, actorId, nextState) {
        const action = this.actions.get(actionId);

        if (!action) {
            throw new NotFoundError("Action not found.");
        }

        if (![action.assignedTo, action.createdBy].includes(actorId)) {
            throw new AuthorizationError("Actor cannot update action.");
        }

        const transitions = {
            OPEN: new Set(["IN_PROGRESS", "BLOCKED", "CANCELLED"]),
            IN_PROGRESS: new Set(["COMPLETED", "BLOCKED", "CANCELLED"]),
            BLOCKED: new Set(["IN_PROGRESS", "CANCELLED"]),
            COMPLETED: new Set(),
            CANCELLED: new Set()
        };

        requireEnum(nextState, ActionState, "action state");

        if (!transitions[action.state].has(nextState)) {
            throw new StateTransitionError(
                `Invalid transition: ${action.state} -> ${nextState}`
            );
        }

        action.state = nextState;

        if (nextState === ActionState.COMPLETED) {
            action.completedAt = new Date().toISOString();
        }

        this.recordAudit(
            "ACTION_UPDATED",
            actionId,
            actorId,
            { nextState }
        );

        return action;
    }

    getOverdueActions(referenceDate = new Date()) {
        const reference = requireDate(referenceDate, "Reference date");

        return [...this.actions.values()].filter(action =>
            action.dueDate < reference &&
            ![
                ActionState.COMPLETED,
                ActionState.CANCELLED
            ].includes(action.state)
        );
    }

    // --------------------------------------------------------
    // ANALYTICS
    // --------------------------------------------------------

    getMetrics() {
        const messages = [...this.messages.values()];

        const expected = messages
            .filter(message => message.sentAt !== null)
            .reduce(
                (sum, message) => sum + message.recipientIds.length,
                0
            );

        const acknowledged = messages.reduce(
            (sum, message) => sum + message.acknowledgements.size,
            0
        );

        const sent = messages.filter(
            message => message.sentAt !== null
        ).length;

        return {
            project: this.projectName,
            stakeholderCount: this.stakeholders.size,
            messageCount: messages.length,
            sentMessageCount: sent,
            expectedAcknowledgements: expected,
            actualAcknowledgements: acknowledged,
            acknowledgementRate: expected
                ? Number((acknowledged / expected * 100).toFixed(2))
                : 0,
            escalatedMessages: messages.filter(
                message => message.state === MessageState.ESCALATED
            ).length,
            overdueActions: this.getOverdueActions().length,
            meetings: this.meetings.size,
            decisions: this.decisions.size,
            auditEvents: this.audit.length
        };
    }

    async exportAudit(filePath) {
        const content = JSON.stringify(this.audit, null, 2);

        await fs.writeFile(filePath, content, {
            encoding: "utf8",
            mode: 0o600
        });
    }
}

// ============================================================
// EXECUTABLE EXAMPLE
// ============================================================

async function main() {
    const service = new ProjectCommunicationService(
        "Enterprise Project Management"
    );

    const manager = service.registerStakeholder({
        id: "ST-001",
        name: "Project Manager",
        email: "manager@example.com",
        role: Role.PROJECT_MANAGER,
        influence: 5,
        interest: 5,
        clearance: Confidentiality.RESTRICTED
    });

    const sponsor = service.registerStakeholder({
        id: "ST-002",
        name: "Project Sponsor",
        email: "sponsor@example.com",
        role: Role.SPONSOR,
        influence: 5,
        interest: 4,
        clearance: Confidentiality.CONFIDENTIAL
    });

    const developer = service.registerStakeholder({
        id: "ST-003",
        name: "Development Lead",
        email: "developer@example.com",
        role: Role.DEVELOPER,
        influence: 3,
        interest: 5,
        clearance: Confidentiality.INTERNAL
    });

    const client = service.registerStakeholder({
        id: "ST-004",
        name: "Client Representative",
        email: "client@example.com",
        role: Role.CLIENT,
        influence: 4,
        interest: 5,
        clearance: Confidentiality.CONFIDENTIAL
    });

    const message = service.createMessage({
        senderId: manager.id,
        recipientIds: [sponsor.id, developer.id],
        subject: "Weekly Project Update",
        body: "Development is progressing according to the project schedule.",
        channel: Channel.EMAIL,
        purpose: Purpose.STATUS_UPDATE,
        confidentiality: Confidentiality.INTERNAL
    });

    const deliveryResult = await service.dispatchMessage(
        message.id,
        async ({ recipient }) => {
            // Simulated transport adapter.
            console.log(`Delivered to ${recipient.email}`);
        }
    );

    service.acknowledge(message.id, sponsor.id);
    service.acknowledge(message.id, developer.id);

    const meeting = service.scheduleMeeting({
        organizerId: manager.id,
        participantIds: [sponsor.id, developer.id, client.id],
        title: "Weekly Project Review",
        scheduledAt: new Date(Date.now() + 86400000),
        agenda: [
            "Project progress",
            "Delivery risks",
            "Testing preparation"
        ]
    });

    service.finalizeMeeting(
        meeting.id,
        manager.id,
        "Testing preparation approved. Delivery milestone unchanged."
    );

    service.recordDecision(
        meeting.id,
        sponsor.id,
        "Approve testing preparation.",
        true
    );

    const action = service.createAction({
        description: "Prepare the testing plan.",
        assignedTo: developer.id,
        createdBy: manager.id,
        dueDate: new Date(Date.now() + 5 * 86400000)
    });

    service.updateAction(
        action.id,
        developer.id,
        ActionState.IN_PROGRESS
    );

    console.log("\nDELIVERY RESULT");
    console.log(deliveryResult);

    console.log("\nCOMMUNICATION METRICS");
    console.log(service.getMetrics());

    console.log("\nOVERDUE ACTIONS");
    console.log(service.getOverdueActions());

    await service.exportAudit("project_communication_audit.json");

    // Edge-case validation.
    try {
        service.acknowledge(message.id, client.id);
    } catch (error) {
        console.log("\nUnauthorized acknowledgement rejected:", error.message);
    }

    try {
        service.updateAction(
            action.id,
            developer.id,
            ActionState.OPEN
        );
    } catch (error) {
        console.log("Invalid action transition rejected:", error.message);
    }

    console.log("\nAudit events:", service.audit.length);
    console.log("All example workflows completed.");
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
