"use strict";

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

const ConflictType = Object.freeze({
    COMMUNICATION: "communication",
    ROLE_AMBIGUITY: "role_ambiguity",
    RESOURCE_ALLOCATION: "resource_allocation",
    PERFORMANCE: "performance",
    PERSONAL_DISAGREEMENT: "personal_disagreement",
    PRIORITY_MISMATCH: "priority_mismatch",
    WORKING_STYLE: "working_style"
});

const Severity = Object.freeze({
    LOW: 1,
    MEDIUM: 2,
    HIGH: 3,
    CRITICAL: 4
});

const Status = Object.freeze({
    REPORTED: "reported",
    ASSESSMENT: "assessment",
    DISCUSSION: "discussion",
    MEDIATION: "mediation",
    RESOLVED: "resolved",
    ESCALATED: "escalated",
    CLOSED: "closed"
});

const ResolutionMethod = Object.freeze({
    COLLABORATION: "collaboration",
    COMPROMISE: "compromise",
    ACCOMMODATION: "accommodation",
    NEGOTIATION: "negotiation",
    MANAGER_DECISION: "manager_decision",
    FORMAL_ESCALATION: "formal_escalation"
});

class ConflictError extends Error {}
class ValidationError extends ConflictError {}
class AuthorizationError extends ConflictError {}
class TransitionError extends ConflictError {}

const transitions = new Map([
    [Status.REPORTED, new Set([Status.ASSESSMENT, Status.ESCALATED])],
    [Status.ASSESSMENT, new Set([
        Status.DISCUSSION, Status.MEDIATION, Status.ESCALATED
    ])],
    [Status.DISCUSSION, new Set([
        Status.MEDIATION, Status.RESOLVED, Status.ESCALATED
    ])],
    [Status.MEDIATION, new Set([
        Status.DISCUSSION, Status.RESOLVED, Status.ESCALATED
    ])],
    [Status.RESOLVED, new Set([
        Status.CLOSED, Status.ESCALATED
    ])],
    [Status.ESCALATED, new Set([Status.CLOSED])],
    [Status.CLOSED, new Set()]
]);

function requireText(value, field) {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new ValidationError(`${field} must be a non-empty string`);
    }
}

function validateEnum(value, allowed, field) {
    if (!Object.values(allowed).includes(value)) {
        throw new ValidationError(`Invalid ${field}: ${value}`);
    }
}

class TeamMember {
    constructor({ id, name, role, department, active = true }) {
        requireText(id, "Member ID");
        requireText(name, "Name");
        requireText(role, "Role");
        requireText(department, "Department");

        this.id = id;
        this.name = name;
        this.role = role;
        this.department = department;
        this.active = active;
    }
}

class ConflictCase {
    constructor({
        id,
        title,
        description,
        type,
        severity,
        reporterId,
        participants
    }) {
        requireText(id, "Case ID");
        requireText(title, "Title");
        requireText(description, "Description");

        validateEnum(type, ConflictType, "conflict type");

        if (!Object.values(Severity).includes(severity)) {
            throw new ValidationError("Invalid severity");
        }

        if (!(participants instanceof Set) || participants.size < 2) {
            throw new ValidationError(
                "At least two participants are required"
            );
        }

        if (!participants.has(reporterId)) {
            throw new ValidationError("Reporter must be a participant");
        }

        this.id = id;
        this.title = title;
        this.description = description;
        this.type = type;
        this.severity = severity;
        this.reporterId = reporterId;
        this.participants = new Set(participants);
        this.status = Status.REPORTED;
        this.mediatorId = null;
        this.discussions = [];
        this.agreement = null;
        this.history = [];
        this.createdAt = new Date();
        this.version = 0;
    }
}

class ConflictManagementService extends EventEmitter {
    #members = new Map();
    #cases = new Map();
    #audit = [];

    constructor() {
        super();
        this.setMaxListeners(50);
    }

    registerMember(member) {
        if (!(member instanceof TeamMember)) {
            throw new ValidationError("Expected a TeamMember instance");
        }

        if (this.#members.has(member.id)) {
            throw new ValidationError("Duplicate member ID");
        }

        this.#members.set(member.id, member);
    }

    getMember(id) {
        return this.#members.get(id);
    }

    getCase(id) {
        const conflict = this.#cases.get(id);
        if (!conflict) {
            throw new ValidationError(`Case not found: ${id}`);
        }
        return conflict;
    }

    #auditEvent(caseId, actorId, action) {
        const event = Object.freeze({
            caseId,
            actorId,
            action,
            timestamp: new Date().toISOString()
        });

        this.#audit.push(event);
        this.emit("audit", event);
    }

    createCase(data) {
        const conflict = new ConflictCase(data);

        if (this.#cases.has(conflict.id)) {
            throw new ValidationError("Duplicate case ID");
        }

        for (const id of conflict.participants) {
            const member = this.#members.get(id);

            if (!member || !member.active) {
                throw new ValidationError(
                    `Participant unavailable: ${id}`
                );
            }
        }

        this.#cases.set(conflict.id, conflict);
        this.#auditEvent(conflict.id, data.reporterId, "CASE_CREATED");

        this.emit("caseCreated", {
            caseId: conflict.id,
            severity: conflict.severity
        });

        return conflict;
    }

    #authorizeActor(actorId, conflict, requireParticipant = false) {
        const member = this.#members.get(actorId);

        if (!member || !member.active) {
            throw new AuthorizationError("Actor is unavailable");
        }

        if (
            requireParticipant &&
            !conflict.participants.has(actorId) &&
            conflict.mediatorId !== actorId
        ) {
            throw new AuthorizationError("Discussion access denied");
        }

        return member;
    }

    transition(caseId, nextStatus, actorId) {
        const conflict = this.getCase(caseId);

        this.#authorizeActor(actorId, conflict);

        if (!Object.values(Status).includes(nextStatus)) {
            throw new ValidationError("Invalid status");
        }

        if (!transitions.get(conflict.status).has(nextStatus)) {
            throw new TransitionError(
                `Invalid transition: ${conflict.status} -> ${nextStatus}`
            );
        }

        const previousStatus = conflict.status;

        conflict.status = nextStatus;
        conflict.version++;

        conflict.history.push({
            previousStatus,
            nextStatus,
            actorId,
            timestamp: new Date().toISOString(),
            version: conflict.version
        });

        this.#auditEvent(
            caseId,
            actorId,
            `STATUS_CHANGED:${previousStatus}:${nextStatus}`
        );

        this.emit("statusChanged", {
            caseId,
            previousStatus,
            nextStatus
        });
    }

    assignMediator(caseId, mediatorId) {
        const conflict = this.getCase(caseId);
        const mediator = this.#members.get(mediatorId);

        if (!mediator || !mediator.active) {
            throw new ValidationError("Mediator is unavailable");
        }

        if (conflict.participants.has(mediatorId)) {
            throw new ValidationError(
                "A participant cannot mediate their own conflict"
            );
        }

        conflict.mediatorId = mediatorId;

        this.#auditEvent(caseId, mediatorId, "MEDIATOR_ASSIGNED");
    }

    addDiscussion(caseId, actorId, message) {
        const conflict = this.getCase(caseId);

        this.#authorizeActor(actorId, conflict, true);

        if (![Status.ASSESSMENT, Status.DISCUSSION,
            Status.MEDIATION].includes(conflict.status)) {
            throw new TransitionError("Discussion is not permitted");
        }

        requireText(message, "Discussion message");

        conflict.discussions.push({
            actorId,
            message: message.trim(),
            timestamp: new Date().toISOString()
        });

        this.#auditEvent(caseId, actorId, "DISCUSSION_ADDED");
        this.emit("discussionAdded", { caseId, actorId });
    }

    recommendMethod(caseId) {
        const conflict = this.getCase(caseId);

        if (conflict.severity === Severity.CRITICAL) {
            return ResolutionMethod.FORMAL_ESCALATION;
        }

        if (conflict.type === ConflictType.RESOURCE_ALLOCATION) {
            return ResolutionMethod.NEGOTIATION;
        }

        if (conflict.type === ConflictType.PRIORITY_MISMATCH) {
            return ResolutionMethod.COLLABORATION;
        }

        if (conflict.type === ConflictType.PERSONAL_DISAGREEMENT) {
            return ResolutionMethod.COLLABORATION;
        }

        return conflict.severity === Severity.HIGH
            ? ResolutionMethod.COLLABORATION
            : ResolutionMethod.COMPROMISE;
    }

    createAgreement(caseId, actorId, agreement) {
        const conflict = this.getCase(caseId);

        this.#authorizeActor(actorId, conflict);

        if (![Status.DISCUSSION, Status.MEDIATION].includes(
            conflict.status
        )) {
            throw new TransitionError(
                "Agreement requires discussion or mediation"
            );
        }

        if (!Object.values(ResolutionMethod).includes(agreement.method)) {
            throw new ValidationError("Invalid resolution method");
        }

        if (!Array.isArray(agreement.actions) ||
            agreement.actions.length === 0) {
            throw new ValidationError("Agreement actions are required");
        }

        if (!Array.isArray(agreement.successCriteria) ||
            agreement.successCriteria.length === 0) {
            throw new ValidationError("Success criteria are required");
        }

        const deadline = new Date(agreement.deadline);

        if (Number.isNaN(deadline.getTime()) ||
            deadline <= new Date()) {
            throw new ValidationError("Deadline must be in the future");
        }

        const responsible = new Set(agreement.responsibleMembers || []);

        if (responsible.size === 0 ||
            [...responsible].some(
                id => !conflict.participants.has(id)
            )) {
            throw new ValidationError(
                "Responsible members must be participants"
            );
        }

        conflict.agreement = {
            method: agreement.method,
            actions: [...agreement.actions],
            responsibleMembers: [...responsible],
            successCriteria: [...agreement.successCriteria],
            deadline: deadline.toISOString(),
            acceptedBy: new Set()
        };

        this.#auditEvent(caseId, actorId, "AGREEMENT_CREATED");
    }

    acceptAgreement(caseId, memberId) {
        const conflict = this.getCase(caseId);

        this.#authorizeActor(memberId, conflict, true);

        if (!conflict.agreement ||
            !conflict.participants.has(memberId)) {
            throw new ValidationError(
                "An agreement and participant membership are required"
            );
        }

        conflict.agreement.acceptedBy.add(memberId);

        this.#auditEvent(caseId, memberId, "AGREEMENT_ACCEPTED");
    }

    resolve(caseId, managerId) {
        const conflict = this.getCase(caseId);

        this.#authorizeActor(managerId, conflict);

        if (!conflict.agreement) {
            throw new ValidationError("No resolution agreement exists");
        }

        if (conflict.agreement.acceptedBy.size !==
            conflict.participants.size) {
            throw new ValidationError(
                "Every participant must accept the agreement"
            );
        }

        this.transition(caseId, Status.RESOLVED, managerId);
        this.emit("caseResolved", { caseId });
    }

    escalate(caseId, managerId) {
        this.transition(caseId, Status.ESCALATED, managerId);
        this.emit("caseEscalated", { caseId });
    }

    report() {
        const result = {
            total: this.#cases.size,
            byStatus: {},
            bySeverity: {}
        };

        for (const status of Object.values(Status)) {
            result.byStatus[status] = 0;
        }

        for (const severity of Object.keys(Severity)) {
            result.bySeverity[severity] = 0;
        }

        for (const conflict of this.#cases.values()) {
            result.byStatus[conflict.status]++;
            const name = Object.keys(Severity).find(
                key => Severity[key] === conflict.severity
            );
            result.bySeverity[name]++;
        }

        return result;
    }

    auditLog() {
        return this.#audit.map(event => ({ ...event }));
    }

    async exportReport(filePath) {
        const safeReport = {
            report: this.report(),
            cases: [...this.#cases.values()].map(conflict => ({
                id: conflict.id,
                title: conflict.title,
                type: conflict.type,
                severity: conflict.severity,
                status: conflict.status,
                participants: [...conflict.participants]
            }))
        };

        await fs.writeFile(
            filePath,
            JSON.stringify(safeReport, null, 2),
            { encoding: "utf8", mode: 0o600 }
        );
    }
}

async function main() {
    const service = new ConflictManagementService();

    service.on("caseCreated", event => {
        console.log("New case:", event.caseId);
    });

    service.on("statusChanged", event => {
        console.log(
            `Status: ${event.previousStatus} -> ${event.nextStatus}`
        );
    });

    service.on("caseResolved", event => {
        console.log("Resolved:", event.caseId);
    });

    service.on("audit", event => {
        console.log("Audit:", event.action);
    });

    service.registerMember(new TeamMember({
        id: "E01",
        name: "Ananya",
        role: "Developer",
        department: "Engineering"
    }));

    service.registerMember(new TeamMember({
        id: "E02",
        name: "Rahul",
        role: "Designer",
        department: "Product"
    }));

    service.registerMember(new TeamMember({
        id: "E03",
        name: "Priya",
        role: "Manager",
        department: "Management"
    }));

    service.registerMember(new TeamMember({
        id: "E04",
        name: "Arjun",
        role: "Mediator",
        department: "Human Resources"
    }));

    const conflict = service.createCase({
        id: "CF-2001",
        title: "Disagreement over release priorities",
        description: "Teams disagree about release scope and deadlines.",
        type: ConflictType.PRIORITY_MISMATCH,
        severity: Severity.MEDIUM,
        reporterId: "E01",
        participants: new Set(["E01", "E02"])
    });

    service.assignMediator(conflict.id, "E04");

    service.transition(conflict.id, Status.ASSESSMENT, "E03");
    service.transition(conflict.id, Status.DISCUSSION, "E03");

    service.addDiscussion(
        conflict.id,
        "E01",
        "Engineering requires additional testing time."
    );

    service.addDiscussion(
        conflict.id,
        "E02",
        "Product needs the core features delivered."
    );

    const agreement = {
        method: service.recommendMethod(conflict.id),
        actions: [
            "Deliver core features first.",
            "Move optional features to the next iteration.",
            "Conduct joint release-readiness testing."
        ],
        responsibleMembers: ["E01", "E02"],
        successCriteria: [
            "Core features pass acceptance testing.",
            "Both teams approve the delivery plan."
        ],
        deadline: "2026-11-20T17:00:00Z"
    };

    service.createAgreement(conflict.id, "E03", agreement);

    service.acceptAgreement(conflict.id, "E01");
    service.acceptAgreement(conflict.id, "E02");

    service.resolve(conflict.id, "E03");

    service.transition(conflict.id, Status.CLOSED, "E03");

    console.log("\nREPORT");
    console.log(JSON.stringify(service.report(), null, 2));

    console.log("\nAUDIT EVENT COUNT:", service.auditLog().length);

    try {
        service.transition(conflict.id, Status.RESOLVED, "E03");
    } catch (error) {
        console.log("Expected failure:", error.message);
    }

    await service.exportReport("conflict_management_report.json");
    console.log("Report exported.");
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
