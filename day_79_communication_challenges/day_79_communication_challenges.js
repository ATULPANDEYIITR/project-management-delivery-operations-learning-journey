"use strict";

/*
 * Communication Challenges
 * Event-driven communication incident and policy management.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const crypto = require("node:crypto");

const Category = Object.freeze({
    UNCLEAR_MESSAGE: "unclear_message",
    INFORMATION_OVERLOAD: "information_overload",
    POOR_LISTENING: "poor_listening",
    LANGUAGE_BARRIER: "language_barrier",
    CULTURAL_DIFFERENCE: "cultural_difference",
    WRONG_CHANNEL: "wrong_channel",
    DELAYED_RESPONSE: "delayed_response",
    MISSING_FEEDBACK: "missing_feedback",
    INCORRECT_ASSUMPTION: "incorrect_assumption",
    TECHNICAL_FAILURE: "technical_failure",
    INTERPERSONAL_CONFLICT: "interpersonal_conflict",
    ROLE_AMBIGUITY: "role_ambiguity"
});

const Severity = Object.freeze({
    LOW: "low",
    MEDIUM: "medium",
    HIGH: "high",
    CRITICAL: "critical"
});

const Status = Object.freeze({
    OPEN: "open",
    INVESTIGATING: "investigating",
    ACTION_REQUIRED: "action_required",
    RESOLVED: "resolved",
    CLOSED: "closed"
});

const Channels = Object.freeze([
    "email",
    "meeting",
    "chat",
    "phone",
    "document",
    "video_conference",
    "face_to_face"
]);

const RESPONSE_LIMITS = Object.freeze({
    low: 72,
    medium: 48,
    high: 12,
    critical: 2
});

const TRANSITIONS = Object.freeze({
    open: ["investigating", "closed"],
    investigating: ["action_required", "resolved", "closed"],
    action_required: ["investigating", "resolved"],
    resolved: ["closed", "investigating"],
    closed: []
});

const RECOMMENDATIONS = Object.freeze({
    unclear_message:
        "Use concise messages, explicit instructions and confirmation.",
    information_overload:
        "Prioritize information and divide complex messages into sections.",
    poor_listening:
        "Use active listening, paraphrasing and clarifying questions.",
    language_barrier:
        "Use plain language and verified translations.",
    cultural_difference:
        "Establish inclusive communication practices.",
    wrong_channel:
        "Choose a channel based on urgency and confidentiality.",
    delayed_response:
        "Introduce response deadlines and escalation procedures.",
    missing_feedback:
        "Establish structured feedback and acknowledgement cycles.",
    incorrect_assumption:
        "Verify facts and confirm shared understanding.",
    technical_failure:
        "Check infrastructure and establish alternative channels.",
    interpersonal_conflict:
        "Use structured discussion and impartial conflict resolution.",
    role_ambiguity:
        "Define responsibilities and reporting relationships."
});

class CommunicationError extends Error {
    constructor(message, code = "COMMUNICATION_ERROR") {
        super(message);
        this.name = "CommunicationError";
        this.code = code;
    }
}

class ValidationError extends CommunicationError {
    constructor(message) {
        super(message, "VALIDATION_ERROR");
        this.name = "ValidationError";
    }
}

class StateError extends CommunicationError {
    constructor(message) {
        super(message, "INVALID_STATE");
        this.name = "StateError";
    }
}

function validateText(value, field, maxLength = 500) {
    if (typeof value !== "string") {
        throw new ValidationError(`${field} must be a string.`);
    }

    const normalized = value.trim();

    if (!normalized || normalized.length > maxLength) {
        throw new ValidationError(
            `${field} must contain 1-${maxLength} characters.`
        );
    }

    if (/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/.test(normalized)) {
        throw new ValidationError(
            `${field} contains invalid control characters.`
        );
    }

    return normalized;
}

class CommunicationIncident {
    constructor(data) {
        this.id = data.id;
        this.reference = crypto.randomUUID();
        this.title = data.title;
        this.category = data.category;
        this.severity = data.severity;
        this.channel = data.channel;
        this.department = data.department;
        this.reporter = data.reporter;
        this.description = data.description;

        this.status = Status.OPEN;
        this.assignee = null;
        this.correctiveAction = null;
        this.resolution = null;
        this.feedbackReceived = false;

        this.createdAt = new Date();
        this.resolvedAt = null;
        this.events = [];

        this.record("reported", "Incident registered.");
    }

    record(type, details) {
        this.events.push({
            type,
            details,
            timestamp: new Date().toISOString()
        });
    }

    toJSON() {
        return {
            ...this,
            events: [...this.events]
        };
    }
}

class CommunicationPolicy {
    evaluate(incident, now = new Date()) {
        const deadline = new Date(
            incident.createdAt.getTime() +
            RESPONSE_LIMITS[incident.severity] * 60 * 60 * 1000
        );

        return {
            deadline,
            overdue: now > deadline,
            severity: incident.severity
        };
    }

    canClose(incident) {
        return (
            incident.status === Status.RESOLVED &&
            incident.feedbackReceived &&
            Boolean(incident.resolution)
        );
    }

    recommend(category) {
        if (!RECOMMENDATIONS[category]) {
            throw new ValidationError("Unknown communication category.");
        }

        return RECOMMENDATIONS[category];
    }
}

class CommunicationService extends EventEmitter {
    #incidents = new Map();
    #nextId = 1;
    #policy;
    #processing = Promise.resolve();

    constructor(policy = new CommunicationPolicy()) {
        super();
        this.#policy = policy;
    }

    createIncident(data) {
        if (!Object.values(Category).includes(data.category)) {
            throw new ValidationError("Invalid incident category.");
        }

        if (!Object.values(Severity).includes(data.severity)) {
            throw new ValidationError("Invalid incident severity.");
        }

        if (!Channels.includes(data.channel)) {
            throw new ValidationError("Invalid communication channel.");
        }

        const incident = new CommunicationIncident({
            id: this.#nextId++,
            title: validateText(data.title, "Title", 120),
            category: data.category,
            severity: data.severity,
            channel: data.channel,
            department: validateText(data.department, "Department", 100),
            reporter: validateText(data.reporter, "Reporter", 100),
            description: validateText(data.description, "Description", 1000)
        });

        this.#incidents.set(incident.id, incident);

        this.emit("incident.created", incident.toJSON());

        return incident;
    }

    getIncident(id) {
        const incident = this.#incidents.get(id);

        if (!incident) {
            throw new CommunicationError(
                `Incident ${id} not found.`,
                "NOT_FOUND"
            );
        }

        return incident;
    }

    assign(id, employee) {
        const incident = this.getIncident(id);

        if (incident.status === Status.CLOSED) {
            throw new StateError("Closed incidents cannot be assigned.");
        }

        incident.assignee = validateText(employee, "Assignee", 100);

        incident.record("assigned", `Assigned to ${incident.assignee}`);

        this.emit("incident.assigned", incident.toJSON());
    }

    transition(id, nextStatus) {
        const incident = this.getIncident(id);

        if (!Object.values(Status).includes(nextStatus)) {
            throw new ValidationError("Unknown incident status.");
        }

        if (!TRANSITIONS[incident.status].includes(nextStatus)) {
            throw new StateError(
                `Transition ${incident.status} -> ${nextStatus} is forbidden.`
            );
        }

        if (
            nextStatus === Status.RESOLVED &&
            (!incident.resolution || !incident.correctiveAction)
        ) {
            throw new StateError(
                "Corrective action and resolution are required."
            );
        }

        incident.status = nextStatus;

        if (nextStatus === Status.RESOLVED) {
            incident.resolvedAt = new Date();
        }

        incident.record("status_changed", nextStatus);

        this.emit("incident.status_changed", incident.toJSON());
    }

    prescribeAction(id, action = null) {
        const incident = this.getIncident(id);

        if (incident.status === Status.CLOSED) {
            throw new StateError("Incident is already closed.");
        }

        const selectedAction = action === null
            ? this.#policy.recommend(incident.category)
            : validateText(action, "Corrective action", 1000);

        incident.correctiveAction = selectedAction;

        incident.record("action_prescribed", selectedAction);

        if (
            incident.status === Status.OPEN ||
            incident.status === Status.INVESTIGATING
        ) {
            this.transition(id, Status.ACTION_REQUIRED);
        }

        this.emit("incident.action_prescribed", incident.toJSON());

        return selectedAction;
    }

    resolve(id, resolution) {
        const incident = this.getIncident(id);

        if (
            incident.status !== Status.INVESTIGATING &&
            incident.status !== Status.ACTION_REQUIRED
        ) {
            throw new StateError(
                "Incident must be under investigation before resolution."
            );
        }

        incident.resolution = validateText(
            resolution,
            "Resolution",
            1000
        );

        this.transition(id, Status.RESOLVED);

        this.emit("incident.resolved", incident.toJSON());
    }

    acknowledgeFeedback(id) {
        const incident = this.getIncident(id);

        if (incident.status !== Status.RESOLVED) {
            throw new StateError(
                "Only resolved incidents can receive closure feedback."
            );
        }

        incident.feedbackReceived = true;
        incident.record("feedback_received", "Resolution acknowledged.");

        this.emit("incident.feedback_received", incident.toJSON());
    }

    close(id) {
        const incident = this.getIncident(id);

        if (!this.#policy.canClose(incident)) {
            throw new StateError(
                "Resolution and feedback confirmation are required."
            );
        }

        this.transition(id, Status.CLOSED);

        this.emit("incident.closed", incident.toJSON());
    }

    async processAsync(task) {
        // Serialize state-changing jobs to avoid concurrent update races.
        const operation = this.#processing.then(() => task(this));

        this.#processing = operation.catch(() => {});

        return operation;
    }

    search(filters = {}) {
        return [...this.#incidents.values()].filter(incident => {
            return (
                (!filters.category ||
                    incident.category === filters.category) &&
                (!filters.department ||
                    incident.department.toLowerCase() ===
                    filters.department.toLowerCase()) &&
                (!filters.status ||
                    incident.status === filters.status) &&
                (!filters.severity ||
                    incident.severity === filters.severity)
            );
        });
    }

    overdue(now = new Date()) {
        return [...this.#incidents.values()].filter(incident => {
            if (
                incident.status === Status.RESOLVED ||
                incident.status === Status.CLOSED
            ) {
                return false;
            }

            return this.#policy.evaluate(incident, now).overdue;
        });
    }

    analytics() {
        const incidents = [...this.#incidents.values()];

        const countBy = key => incidents.reduce((result, incident) => {
            result[incident[key]] = (result[incident[key]] || 0) + 1;
            return result;
        }, {});

        const resolved = incidents.filter(
            incident => incident.resolvedAt
        );

        const averageResolutionHours = resolved.length
            ? resolved.reduce((total, incident) => {
                return total +
                    (incident.resolvedAt - incident.createdAt) / 3600000;
            }, 0) / resolved.length
            : null;

        return {
            total: incidents.length,
            categories: countBy("category"),
            severities: countBy("severity"),
            statuses: countBy("status"),
            resolutionRate: incidents.length
                ? Number(
                    (
                        resolved.length / incidents.length * 100
                    ).toFixed(2)
                )
                : 0,
            averageResolutionHours:
                averageResolutionHours === null
                    ? null
                    : Number(averageResolutionHours.toFixed(2)),
            overdue: this.overdue().length
        };
    }

    async exportJSON(filename) {
        const records = [...this.#incidents.values()].map(
            incident => incident.toJSON()
        );

        await fs.writeFile(
            filename,
            JSON.stringify(records, null, 2),
            { encoding: "utf8", flag: "w", mode: 0o600 }
        );
    }
}

async function main() {
    const service = new CommunicationService();

    // Event-driven notifications.
    service.on("incident.created", incident => {
        console.log(`New incident registered: ${incident.id}`);
    });

    service.on("incident.resolved", incident => {
        console.log(`Resolution recorded: ${incident.title}`);
    });

    service.on("incident.closed", incident => {
        console.log(`Incident closed: ${incident.id}`);
    });

    const first = service.createIncident({
        title: "Unclear project instructions",
        category: Category.UNCLEAR_MESSAGE,
        severity: Severity.HIGH,
        channel: "email",
        department: "Engineering",
        reporter: "Project Manager",
        description: "Project requirements were interpreted differently."
    });

    await service.processAsync(async manager => {
        manager.assign(first.id, "Team Lead");
        manager.transition(first.id, Status.INVESTIGATING);
        manager.prescribeAction(first.id);

        manager.resolve(
            first.id,
            "A revised document defined requirements and responsibilities."
        );

        manager.acknowledgeFeedback(first.id);
        manager.close(first.id);
    });

    const second = service.createIncident({
        title: "Language barrier",
        category: Category.LANGUAGE_BARRIER,
        severity: Severity.MEDIUM,
        channel: "meeting",
        department: "Operations",
        reporter: "Operations Supervisor",
        description: "Instructions were misunderstood during a meeting."
    });

    service.assign(second.id, "Operations Coordinator");
    service.transition(second.id, Status.INVESTIGATING);
    service.prescribeAction(second.id);

    console.log("\nANALYTICS");
    console.log(JSON.stringify(service.analytics(), null, 2));

    console.log("\nOPEN INVESTIGATIONS");
    console.log(
        service.search({ status: Status.ACTION_REQUIRED })
            .map(item => item.title)
    );

    console.log("\nRECOMMENDED RESPONSE");
    console.log(
        new CommunicationPolicy().recommend(Category.LANGUAGE_BARRIER)
    );

    await service.exportJSON("communication-incidents.json");

    console.log("\nJSON export completed.");
}

async function runTests() {
    const service = new CommunicationService();

    const data = {
        title: "Missing feedback",
        category: Category.MISSING_FEEDBACK,
        severity: Severity.LOW,
        channel: "chat",
        department: "Testing",
        reporter: "Tester",
        description: "No acknowledgement was received."
    };

    const incident = service.createIncident(data);

    if (service.analytics().total !== 1) {
        throw new Error("Analytics test failed.");
    }

    let rejected = false;

    try {
        service.createIncident({ ...data, title: "" });
    } catch (error) {
        rejected = error instanceof ValidationError;
    }

    if (!rejected) {
        throw new Error("Input validation test failed.");
    }

    rejected = false;

    try {
        service.transition(incident.id, Status.RESOLVED);
    } catch (error) {
        rejected = error instanceof StateError;
    }

    if (!rejected) {
        throw new Error("Invalid transition test failed.");
    }

    console.log("All validation tests passed.");
}

main()
    .then(runTests)
    .catch(error => {
        console.error("Application failure:", error.message);
        process.exitCode = 1;
    });
