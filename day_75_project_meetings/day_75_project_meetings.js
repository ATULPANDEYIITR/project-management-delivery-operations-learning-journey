"use strict";

/*
 * PROJECT MEETING MANAGEMENT SYSTEM
 *
 * Event-driven implementation using Node.js standard libraries.
 * Focus: scheduling, asynchronous notifications, agenda events,
 * attendance, decisions, action ownership, and policy evaluation.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const crypto = require("node:crypto");

const MeetingStatus = Object.freeze({
    SCHEDULED: "scheduled",
    IN_PROGRESS: "in_progress",
    COMPLETED: "completed",
    CANCELLED: "cancelled"
});

const ActionStatus = Object.freeze({
    OPEN: "open",
    IN_PROGRESS: "in_progress",
    BLOCKED: "blocked",
    COMPLETED: "completed"
});

const Priority = Object.freeze({
    LOW: 1,
    MEDIUM: 2,
    HIGH: 3,
    CRITICAL: 4
});

class MeetingError extends Error {}
class ValidationError extends MeetingError {}
class StateError extends MeetingError {}
class NotFoundError extends MeetingError {}

function createId() {
    return crypto.randomUUID();
}

function requiredText(value, field) {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new ValidationError(`${field} is required.`);
    }
    return value.trim();
}

function validEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validDate(value, field) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        throw new ValidationError(`${field} must be a valid date.`);
    }
    return date;
}

class MeetingPolicy {
    constructor({
        maximumDuration = 240,
        maximumParticipants = 50,
        requireAgenda = true,
        requireMinutes = true
    } = {}) {
        this.maximumDuration = maximumDuration;
        this.maximumParticipants = maximumParticipants;
        this.requireAgenda = requireAgenda;
        this.requireMinutes = requireMinutes;
    }

    validate(meeting) {
        const errors = [];

        if (meeting.durationMinutes > this.maximumDuration) {
            errors.push("Meeting exceeds maximum duration.");
        }

        if (
            meeting.participants.size >
            this.maximumParticipants
        ) {
            errors.push("Participant limit exceeded.");
        }

        if (
            this.requireAgenda &&
            meeting.agenda.length === 0
        ) {
            errors.push("At least one agenda item is required.");
        }

        return errors;
    }

    canClose(meeting, minutes) {
        if (
            this.requireMinutes &&
            (!minutes || !minutes.trim())
        ) {
            return false;
        }
        return meeting.status === MeetingStatus.IN_PROGRESS;
    }
}

class Meeting extends EventEmitter {
    constructor({
        title,
        project,
        organizerId,
        scheduledAt,
        durationMinutes,
        location,
        participants = []
    }) {
        super();

        this.id = createId();
        this.title = requiredText(title, "Meeting title");
        this.project = requiredText(project, "Project");
        this.organizerId = requiredText(
            organizerId, "Organizer ID"
        );
        this.scheduledAt = validDate(
            scheduledAt, "Scheduled date"
        );
        this.durationMinutes = Number(durationMinutes);

        if (
            !Number.isInteger(this.durationMinutes) ||
            this.durationMinutes <= 0
        ) {
            throw new ValidationError(
                "Duration must be a positive integer."
            );
        }

        this.location = requiredText(location, "Location");
        this.status = MeetingStatus.SCHEDULED;

        this.participants = new Map();
        this.agenda = [];
        this.decisions = [];
        this.actions = [];
        this.attendance = new Set();
        this.minutes = "";
        this.revision = 0;
        this.createdAt = new Date().toISOString();

        for (const participant of participants) {
            this.addParticipant(participant, false);
        }

        if (!this.participants.has(this.organizerId)) {
            throw new ValidationError(
                "Organizer must be a meeting participant."
            );
        }
    }

    get endTime() {
        return new Date(
            this.scheduledAt.getTime() +
            this.durationMinutes * 60000
        );
    }

    get snapshot() {
        return Object.freeze({
            id: this.id,
            title: this.title,
            project: this.project,
            status: this.status,
            revision: this.revision,
            participantCount: this.participants.size,
            agendaCount: this.agenda.length,
            decisionCount: this.decisions.length,
            actionCount: this.actions.length
        });
    }

    addParticipant(data, emit = true) {
        if (this.status !== MeetingStatus.SCHEDULED) {
            throw new StateError(
                "Participants cannot be added after starting."
            );
        }

        const id = requiredText(data.id, "Participant ID");
        const name = requiredText(data.name, "Participant name");
        const email = requiredText(data.email, "Email");

        if (!validEmail(email)) {
            throw new ValidationError("Invalid email address.");
        }

        if (this.participants.has(id)) {
            throw new ValidationError("Duplicate participant.");
        }

        const participant = Object.freeze({
            id,
            name,
            email,
            role: data.role || "member"
        });

        this.participants.set(id, participant);

        if (emit) {
            this.changed("participant.added", { participantId: id });
        }

        return participant;
    }

    addAgendaItem({ title, ownerId, durationMinutes, priority }) {
        if (this.status !== MeetingStatus.SCHEDULED) {
            throw new StateError("Agenda is locked.");
        }

        if (!this.participants.has(ownerId)) {
            throw new ValidationError(
                "Agenda owner must be a participant."
            );
        }

        const duration = Number(durationMinutes);

        if (!Number.isInteger(duration) || duration <= 0) {
            throw new ValidationError("Invalid agenda duration.");
        }

        if (
            !Object.prototype.hasOwnProperty.call(
                Priority, String(priority).toUpperCase()
            )
        ) {
            throw new ValidationError("Invalid priority.");
        }

        const item = {
            id: createId(),
            title: requiredText(title, "Agenda title"),
            ownerId,
            durationMinutes: duration,
            priority: String(priority).toUpperCase(),
            completed: false,
            notes: ""
        };

        this.agenda.push(item);
        this.changed("agenda.added", { agendaId: item.id });
        return item;
    }

    markAttendance(participantId) {
        this.assertParticipant(participantId);

        if (
            this.status !== MeetingStatus.SCHEDULED &&
            this.status !== MeetingStatus.IN_PROGRESS
        ) {
            throw new StateError("Attendance is closed.");
        }

        this.attendance.add(participantId);
        this.changed("attendance.recorded", {
            participantId
        });
    }

    start(policy) {
        if (this.status !== MeetingStatus.SCHEDULED) {
            throw new StateError("Invalid start transition.");
        }

        const errors = policy.validate(this);

        if (errors.length > 0) {
            throw new ValidationError(errors.join("; "));
        }

        this.status = MeetingStatus.IN_PROGRESS;
        this.changed("meeting.started", {});
    }

    completeAgendaItem(id, notes = "") {
        this.assertInProgress();

        const item = this.agenda.find(entry => entry.id === id);

        if (!item) {
            throw new NotFoundError("Agenda item not found.");
        }

        item.completed = true;
        item.notes = notes;
        this.changed("agenda.completed", { agendaId: id });
    }

    recordDecision({ description, recordedBy, rationale = "" }) {
        this.assertInProgress();
        this.assertParticipant(recordedBy);

        const decision = Object.freeze({
            id: createId(),
            description: requiredText(description, "Decision"),
            recordedBy,
            rationale,
            recordedAt: new Date().toISOString()
        });

        this.decisions.push(decision);
        this.changed("decision.recorded", {
            decisionId: decision.id
        });

        return decision;
    }

    createAction({
        description,
        assigneeId,
        dueDate,
        priority = "MEDIUM"
    }) {
        this.assertInProgress();
        this.assertParticipant(assigneeId);

        const deadline = validDate(dueDate, "Action due date");
        const normalizedPriority = String(priority).toUpperCase();

        if (!(normalizedPriority in Priority)) {
            throw new ValidationError("Invalid action priority.");
        }

        const action = {
            id: createId(),
            description: requiredText(
                description, "Action description"
            ),
            assigneeId,
            dueDate: deadline,
            priority: normalizedPriority,
            status: ActionStatus.OPEN,
            completionNotes: ""
        };

        this.actions.push(action);
        this.changed("action.created", {
            actionId: action.id
        });

        return action;
    }

    updateAction(id, status, notes = "") {
        const action = this.actions.find(item => item.id === id);

        if (!action) {
            throw new NotFoundError("Action not found.");
        }

        if (action.status === ActionStatus.COMPLETED) {
            throw new StateError("Completed action is immutable.");
        }

        if (!Object.values(ActionStatus).includes(status)) {
            throw new ValidationError("Invalid action status.");
        }

        if (
            status === ActionStatus.COMPLETED &&
            !notes.trim()
        ) {
            throw new ValidationError(
                "Completion evidence is required."
            );
        }

        action.status = status;
        action.completionNotes = notes;

        this.changed("action.updated", {
            actionId: id,
            status
        });
    }

    close(minutes, policy) {
        if (!policy.canClose(this, minutes)) {
            throw new StateError(
                "Meeting closure requirements are not satisfied."
            );
        }

        this.minutes = requiredText(minutes, "Minutes");
        this.status = MeetingStatus.COMPLETED;
        this.changed("meeting.completed", {});
    }

    cancel(reason) {
        if (
            this.status === MeetingStatus.COMPLETED ||
            this.status === MeetingStatus.CANCELLED
        ) {
            throw new StateError("Meeting cannot be cancelled.");
        }

        this.minutes = `Cancelled: ${requiredText(reason, "Reason")}`;
        this.status = MeetingStatus.CANCELLED;
        this.changed("meeting.cancelled", {});
    }

    assertParticipant(id) {
        if (!this.participants.has(id)) {
            throw new ValidationError("Unknown participant.");
        }
    }

    assertInProgress() {
        if (this.status !== MeetingStatus.IN_PROGRESS) {
            throw new StateError("Meeting is not active.");
        }
    }

    changed(eventName, data) {
        this.revision += 1;

        this.emit("change", {
            eventName,
            meetingId: this.id,
            revision: this.revision,
            timestamp: new Date().toISOString(),
            ...data
        });
    }

    serialize() {
        return {
            id: this.id,
            title: this.title,
            project: this.project,
            organizerId: this.organizerId,
            scheduledAt: this.scheduledAt.toISOString(),
            durationMinutes: this.durationMinutes,
            endTime: this.endTime.toISOString(),
            location: this.location,
            status: this.status,
            participants: Array.from(this.participants.values()),
            attendance: Array.from(this.attendance),
            agenda: this.agenda,
            decisions: this.decisions,
            actions: this.actions.map(action => ({
                ...action,
                dueDate: action.dueDate.toISOString()
            })),
            minutes: this.minutes,
            revision: this.revision,
            createdAt: this.createdAt
        };
    }
}

class MeetingService extends EventEmitter {
    constructor(policy = new MeetingPolicy()) {
        super();
        this.policy = policy;
        this.meetings = new Map();
        this.eventHistory = [];
    }

    schedule(meeting) {
        if (this.meetings.has(meeting.id)) {
            throw new ValidationError("Duplicate meeting.");
        }

        for (const existing of this.meetings.values()) {
            if (
                existing.status !== MeetingStatus.SCHEDULED &&
                existing.status !== MeetingStatus.IN_PROGRESS
            ) {
                continue;
            }

            if (existing.organizerId !== meeting.organizerId) {
                continue;
            }

            const overlap =
                meeting.scheduledAt < existing.endTime &&
                existing.scheduledAt < meeting.endTime;

            if (overlap) {
                throw new ValidationError(
                    "Organizer scheduling conflict."
                );
            }
        }

        meeting.on("change", event => {
            this.eventHistory.push(event);
            this.emit("meeting.event", event);
        });

        this.meetings.set(meeting.id, meeting);
        this.emit("meeting.scheduled", meeting.snapshot);

        return meeting;
    }

    get(id) {
        const meeting = this.meetings.get(id);
        if (!meeting) {
            throw new NotFoundError("Meeting not found.");
        }
        return meeting;
    }

    upcoming(from = new Date()) {
        return Array.from(this.meetings.values())
            .filter(meeting =>
                meeting.status === MeetingStatus.SCHEDULED &&
                meeting.scheduledAt >= from
            )
            .sort((a, b) =>
                a.scheduledAt - b.scheduledAt
            );
    }

    overdueActions(reference = new Date()) {
        return Array.from(this.meetings.values())
            .flatMap(meeting =>
                meeting.actions
                    .filter(action =>
                        action.dueDate < reference &&
                        action.status !== ActionStatus.COMPLETED
                    )
                    .map(action => ({
                        meetingId: meeting.id,
                        meetingTitle: meeting.title,
                        ...action
                    }))
            );
    }

    projectReport(project) {
        const meetings = Array.from(this.meetings.values())
            .filter(meeting => meeting.project === project);

        const actions = meetings.flatMap(m => m.actions);

        return {
            project,
            meetingCount: meetings.length,
            completedMeetings: meetings.filter(
                m => m.status === MeetingStatus.COMPLETED
            ).length,
            cancelledMeetings: meetings.filter(
                m => m.status === MeetingStatus.CANCELLED
            ).length,
            decisions: meetings.reduce(
                (sum, m) => sum + m.decisions.length, 0
            ),
            totalActions: actions.length,
            completedActions: actions.filter(
                a => a.status === ActionStatus.COMPLETED
            ).length,
            openActions: actions.filter(
                a => a.status !== ActionStatus.COMPLETED
            ).length
        };
    }

    async exportJSON(filename) {
        const snapshot = Array.from(this.meetings.values())
            .map(meeting => meeting.serialize());

        const temporary = `${filename}.tmp`;

        try {
            await fs.writeFile(
                temporary,
                JSON.stringify(snapshot, null, 2),
                { encoding: "utf8", mode: 0o600 }
            );

            await fs.rename(temporary, filename);
        } catch (error) {
            await fs.rm(temporary, { force: true }).catch(() => {});
            throw new MeetingError(
                `Export failed: ${error.message}`
            );
        }
    }
}

async function main() {
    const service = new MeetingService(
        new MeetingPolicy({
            maximumDuration: 180,
            maximumParticipants: 30,
            requireAgenda: true,
            requireMinutes: true
        })
    );

    // Subscribe before scheduling to capture workflow events.
    service.on("meeting.event", event => {
        console.log(
            `[EVENT] ${event.eventName} | revision ${event.revision}`
        );
    });

    service.on("meeting.scheduled", event => {
        console.log("[SCHEDULED]", event.title);
    });

    const meeting = new Meeting({
        title: "Quarterly Project Review",
        project: "Enterprise Platform",
        organizerId: "P001",
        scheduledAt: new Date(Date.now() + 3600000),
        durationMinutes: 90,
        location: "Board Room",
        participants: [
            {
                id: "P001",
                name: "Project Manager",
                email: "manager@example.com",
                role: "organizer"
            },
            {
                id: "P002",
                name: "Technical Lead",
                email: "technical@example.com"
            },
            {
                id: "P003",
                name: "Business Analyst",
                email: "analyst@example.com"
            }
        ]
    });

    service.schedule(meeting);

    const agenda = meeting.addAgendaItem({
        title: "Delivery status",
        ownerId: "P001",
        durationMinutes: 20,
        priority: "HIGH"
    });

    meeting.addAgendaItem({
        title: "Technical risks",
        ownerId: "P002",
        durationMinutes: 30,
        priority: "CRITICAL"
    });

    meeting.markAttendance("P001");
    meeting.markAttendance("P002");
    meeting.markAttendance("P003");

    meeting.start(service.policy);

    meeting.completeAgendaItem(
        agenda.id,
        "Delivery milestones reviewed."
    );

    meeting.recordDecision({
        description: "Approve the revised delivery schedule.",
        recordedBy: "P001",
        rationale: "Resource availability confirmed."
    });

    const action = meeting.createAction({
        description: "Prepare technical risk mitigation plan.",
        assigneeId: "P002",
        dueDate: new Date(Date.now() + 5 * 86400000),
        priority: "HIGH"
    });

    meeting.updateAction(
        action.id,
        ActionStatus.IN_PROGRESS
    );

    meeting.close(
        "Schedule approved. Technical risk plan assigned.",
        service.policy
    );

    console.log("\nPROJECT REPORT");
    console.log(
        JSON.stringify(
            service.projectReport("Enterprise Platform"),
            null,
            2
        )
    );

    console.log("\nUPCOMING MEETINGS");
    console.log(service.upcoming().map(m => m.snapshot));

    console.log("\nOVERDUE ACTIONS");
    console.log(service.overdueActions());

    await service.exportJSON("meeting_report.json");
    console.log("\nExport completed.");

    // State transition validation.
    try {
        meeting.start(service.policy);
    } catch (error) {
        console.log("Expected protection:", error.message);
    }

    // Input validation.
    try {
        meeting.addParticipant({
            id: "P004",
            name: "Invalid User",
            email: "invalid-email"
        });
    } catch (error) {
        console.log("Expected validation:", error.message);
    }
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
