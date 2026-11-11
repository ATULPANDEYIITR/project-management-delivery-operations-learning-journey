"use strict";

/*
 * Communication Planning and Coordination Engine
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 *
 * Focus:
 * - Event-driven communication scheduling
 * - Stakeholder segmentation
 * - Channel selection
 * - Approval policies
 * - Delivery coordination
 * - Schedule conflict detection
 * - Performance evaluation
 */

const fs = require("node:fs/promises");
const crypto = require("node:crypto");
const EventEmitter = require("node:events");

class CommunicationError extends Error {}
class ValidationError extends CommunicationError {}
class PolicyError extends CommunicationError {}
class SchedulingError extends CommunicationError {}

const CHANNELS = Object.freeze([
    "email",
    "meeting",
    "report",
    "newsletter",
    "website",
    "social_media",
    "phone",
    "workshop"
]);

const STATUSES = Object.freeze({
    PLANNED: "planned",
    APPROVED: "approved",
    SCHEDULED: "scheduled",
    IN_PROGRESS: "in_progress",
    SENT: "sent",
    COMPLETED: "completed",
    FAILED: "failed",
    CANCELLED: "cancelled"
});

const TRANSITIONS = Object.freeze({
    planned: ["approved", "cancelled"],
    approved: ["scheduled", "cancelled"],
    scheduled: ["in_progress", "cancelled"],
    in_progress: ["sent", "completed", "failed"],
    sent: ["completed", "failed"],
    failed: ["scheduled", "cancelled"],
    completed: [],
    cancelled: []
});

function requireText(value, field) {
    if (typeof value !== "string" || !value.trim()) {
        throw new ValidationError(`${field} is required.`);
    }

    return value.trim();
}

function requireDate(value, field) {
    const date = new Date(value);

    if (!Number.isFinite(date.getTime())) {
        throw new ValidationError(`${field} must be a valid date.`);
    }

    return date;
}

function requirePositiveNumber(value, field) {
    if (!Number.isFinite(value) || value < 0) {
        throw new ValidationError(`${field} must be non-negative.`);
    }

    return value;
}

class Stakeholder {
    constructor({
        name,
        audience,
        influence = 3,
        interest = 3,
        department = "",
        email = null,
        preferredChannels = []
    }) {
        this.name = requireText(name, "Stakeholder name");
        this.audience = requireText(audience, "Audience");

        if (!Number.isInteger(influence) || influence < 1 || influence > 5) {
            throw new ValidationError("Influence must be between 1 and 5.");
        }

        if (!Number.isInteger(interest) || interest < 1 || interest > 5) {
            throw new ValidationError("Interest must be between 1 and 5.");
        }

        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            throw new ValidationError("Invalid email address.");
        }

        if (!Array.isArray(preferredChannels) ||
            preferredChannels.some(channel => !CHANNELS.includes(channel))) {
            throw new ValidationError("Invalid preferred communication channel.");
        }

        this.influence = influence;
        this.interest = interest;
        this.department = department;
        this.email = email;
        this.preferredChannels = [...preferredChannels];
    }
}

class CommunicationObjective {
    constructor({
        title,
        description,
        audiences,
        outcome,
        deadline,
        priority = "medium"
    }) {
        this.id = crypto.randomUUID();
        this.title = requireText(title, "Objective title");
        this.description = requireText(description, "Description");
        this.audiences = [...new Set(audiences || [])];

        if (this.audiences.length === 0) {
            throw new ValidationError("At least one audience is required.");
        }

        this.outcome = requireText(outcome, "Desired outcome");
        this.deadline = requireDate(deadline, "Deadline");
        this.priority = priority;
        this.status = "draft";
    }

    activate() {
        if (this.status !== "draft") {
            throw new PolicyError("Only draft objectives can be activated.");
        }

        this.status = "active";
    }

    complete() {
        if (this.status !== "active") {
            throw new PolicyError("Only active objectives can be completed.");
        }

        this.status = "completed";
    }
}

class CommunicationActivity {
    constructor({
        objectiveId,
        title,
        message,
        channel,
        audience,
        owner,
        scheduledAt,
        cost = 0,
        approvalRequired = false
    }) {
        this.id = crypto.randomUUID();
        this.objectiveId = objectiveId;
        this.title = requireText(title, "Activity title");
        this.message = requireText(message, "Message");

        if (!CHANNELS.includes(channel)) {
            throw new ValidationError("Unsupported communication channel.");
        }

        this.channel = channel;
        this.audience = [...new Set(audience || [])];

        if (this.audience.length === 0) {
            throw new ValidationError("Audience cannot be empty.");
        }

        this.owner = requireText(owner, "Owner");
        this.scheduledAt = requireDate(scheduledAt, "Schedule");
        this.cost = requirePositiveNumber(cost, "Cost");
        this.approvalRequired = Boolean(approvalRequired);
        this.approvedBy = null;
        this.status = STATUSES.PLANNED;
        this.completedAt = null;
        this.deliveryAttempts = 0;
        this.feedback = [];
    }

    transition(nextStatus) {
        if (!TRANSITIONS[this.status]?.includes(nextStatus)) {
            throw new PolicyError(
                `Invalid transition ${this.status} -> ${nextStatus}`
            );
        }

        this.status = nextStatus;

        if (nextStatus === STATUSES.COMPLETED) {
            this.completedAt = new Date();
        }
    }
}

class CommunicationEngine extends EventEmitter {
    constructor({ budget, maxActivities = 10000 }) {
        super();

        this.budget = requirePositiveNumber(budget, "Budget");
        this.maxActivities = maxActivities;

        this.stakeholders = new Map();
        this.objectives = new Map();
        this.activities = new Map();

        this.channelUsage = new Map();
        this.auditLog = [];
    }

    log(event, details = {}) {
        const entry = {
            timestamp: new Date().toISOString(),
            event,
            details
        };

        this.auditLog.push(entry);
        this.emit("audit", entry);
    }

    addStakeholder(stakeholder) {
        const key = stakeholder.name.toLowerCase();

        if (this.stakeholders.has(key)) {
            throw new ValidationError("Duplicate stakeholder.");
        }

        this.stakeholders.set(key, stakeholder);
        this.log("stakeholder.created", { name: stakeholder.name });
    }

    addObjective(objective) {
        this.objectives.set(objective.id, objective);
        this.log("objective.created", { id: objective.id });
    }

    get committedCost() {
        return [...this.activities.values()]
            .filter(item => item.status !== STATUSES.CANCELLED)
            .reduce((sum, item) => sum + item.cost, 0);
    }

    get remainingBudget() {
        return this.budget - this.committedCost;
    }

    schedule(activity) {
        const objective = this.objectives.get(activity.objectiveId);

        if (!objective || objective.status !== "active") {
            throw new SchedulingError("Objective must exist and be active.");
        }

        if (activity.scheduledAt > objective.deadline) {
            throw new SchedulingError("Activity exceeds the objective deadline.");
        }

        if (this.activities.size >= this.maxActivities) {
            throw new SchedulingError("Activity capacity reached.");
        }

        if (this.activities.has(activity.id)) {
            throw new ValidationError("Duplicate activity.");
        }

        if (activity.cost > this.remainingBudget) {
            throw new SchedulingError("Insufficient budget.");
        }

        for (const audience of activity.audience) {
            if (!this.stakeholders.has(audience.toLowerCase())) {
                throw new ValidationError(`Unknown audience: ${audience}`);
            }
        }

        if (!activity.approvalRequired) {
            activity.transition(STATUSES.APPROVED);
            activity.transition(STATUSES.SCHEDULED);
        }

        this.activities.set(activity.id, activity);

        this.log("activity.scheduled", {
            id: activity.id,
            channel: activity.channel
        });

        this.emit("activityScheduled", activity);

        return activity;
    }

    approve(activityId, approver) {
        const activity = this.getActivity(activityId);

        if (!activity.approvalRequired) {
            throw new PolicyError("This activity does not require approval.");
        }

        if (activity.status !== STATUSES.PLANNED) {
            throw new PolicyError("Activity is not awaiting approval.");
        }

        activity.approvedBy = requireText(approver, "Approver");
        activity.transition(STATUSES.APPROVED);
        activity.transition(STATUSES.SCHEDULED);

        this.log("activity.approved", {
            id: activityId,
            approver
        });

        this.emit("activityApproved", activity);
    }

    getActivity(id) {
        const activity = this.activities.get(id);

        if (!activity) {
            throw new ValidationError("Activity not found.");
        }

        return activity;
    }

    start(id) {
        const activity = this.getActivity(id);
        activity.transition(STATUSES.IN_PROGRESS);

        this.log("activity.started", { id });
        this.emit("activityStarted", activity);
    }

    async execute(id, deliveryHandler) {
        const activity = this.getActivity(id);

        if (activity.status !== STATUSES.IN_PROGRESS) {
            throw new PolicyError("Activity must be in progress.");
        }

        activity.deliveryAttempts++;

        try {
            // The delivery handler can represent an email, meeting,
            // notification, or other external communication provider.
            const result = await deliveryHandler(activity);

            if (!result || result.success !== true) {
                throw new CommunicationError("Delivery was not confirmed.");
            }

            activity.transition(STATUSES.SENT);

            this.log("activity.sent", {
                id,
                attempts: activity.deliveryAttempts
            });

            this.emit("activitySent", activity);

            return result;
        } catch (error) {
            activity.transition(STATUSES.FAILED);

            this.log("activity.failed", {
                id,
                error: error.message
            });

            this.emit("activityFailed", {
                activity,
                error
            });

            throw error;
        }
    }

    complete(id) {
        const activity = this.getActivity(id);

        if (activity.status !== STATUSES.SENT &&
            activity.status !== STATUSES.IN_PROGRESS) {
            throw new PolicyError("Activity cannot be completed in its current state.");
        }

        activity.transition(STATUSES.COMPLETED);
        this.log("activity.completed", { id });
    }

    retry(id) {
        const activity = this.getActivity(id);

        if (activity.status !== STATUSES.FAILED) {
            throw new PolicyError("Only failed activities can be retried.");
        }

        activity.transition(STATUSES.SCHEDULED);
        this.log("activity.retry_scheduled", { id });
    }

    cancel(id) {
        const activity = this.getActivity(id);
        activity.transition(STATUSES.CANCELLED);
        this.log("activity.cancelled", { id });
    }

    getStakeholderMatrix() {
        const matrix = {
            manageClosely: [],
            keepSatisfied: [],
            keepInformed: [],
            monitor: []
        };

        for (const stakeholder of this.stakeholders.values()) {
            const highInfluence = stakeholder.influence >= 4;
            const highInterest = stakeholder.interest >= 4;

            if (highInfluence && highInterest) {
                matrix.manageClosely.push(stakeholder.name);
            } else if (highInfluence) {
                matrix.keepSatisfied.push(stakeholder.name);
            } else if (highInterest) {
                matrix.keepInformed.push(stakeholder.name);
            } else {
                matrix.monitor.push(stakeholder.name);
            }
        }

        return matrix;
    }

    recommendChannel(name) {
        const stakeholder = this.stakeholders.get(name.toLowerCase());

        if (!stakeholder) {
            throw new ValidationError("Stakeholder not found.");
        }

        if (stakeholder.preferredChannels.length) {
            return stakeholder.preferredChannels[0];
        }

        const defaults = {
            management: "report",
            technical: "workshop",
            public: "website",
            internal: "email",
            external: "email"
        };

        return defaults[stakeholder.audience] || "email";
    }

    scheduleConflicts() {
        const grouped = new Map();

        for (const activity of this.activities.values()) {
            const key = activity.scheduledAt.toISOString();

            if (!grouped.has(key)) {
                grouped.set(key, []);
            }

            grouped.get(key).push(activity);
        }

        return [...grouped.entries()]
            .filter(([, activities]) => activities.length > 1)
            .map(([time, activities]) => ({
                time,
                activities: activities.map(item => item.title)
            }));
    }

    addFeedback(activityId, {
        satisfaction,
        understanding,
        comment = ""
    }) {
        const activity = this.getActivity(activityId);

        if (!Number.isInteger(satisfaction) ||
            satisfaction < 1 || satisfaction > 5) {
            throw new ValidationError("Satisfaction must be 1 to 5.");
        }

        if (!Number.isInteger(understanding) ||
            understanding < 1 || understanding > 5) {
            throw new ValidationError("Understanding must be 1 to 5.");
        }

        activity.feedback.push({
            satisfaction,
            understanding,
            comment,
            timestamp: new Date().toISOString()
        });
    }

    evaluate() {
        const activities = [...this.activities.values()];

        const completed = activities.filter(
            item => item.status === STATUSES.COMPLETED
        );

        const feedback = activities.flatMap(item => item.feedback);

        const average = field => feedback.length
            ? feedback.reduce((sum, item) => sum + item[field], 0)
                / feedback.length
            : 0;

        return {
            totalActivities: activities.length,
            completedActivities: completed.length,
            failedActivities: activities.filter(
                item => item.status === STATUSES.FAILED
            ).length,
            completionRate: activities.length
                ? completed.length / activities.length * 100
                : 0,
            budget: this.budget,
            committedCost: this.committedCost,
            remainingBudget: this.remainingBudget,
            feedbackCount: feedback.length,
            averageSatisfaction: Number(average("satisfaction").toFixed(2)),
            averageUnderstanding: Number(average("understanding").toFixed(2))
        };
    }

    async export(filepath) {
        const data = {
            exportedAt: new Date().toISOString(),
            budget: this.budget,
            stakeholders: [...this.stakeholders.values()],
            objectives: [...this.objectives.values()],
            activities: [...this.activities.values()],
            auditLog: this.auditLog
        };

        // Write to a temporary file and rename after successful serialization.
        const temporaryPath = `${filepath}.tmp`;

        await fs.writeFile(
            temporaryPath,
            JSON.stringify(data, null, 2),
            { encoding: "utf8", mode: 0o600 }
        );

        await fs.rename(temporaryPath, filepath);
    }
}

async function main() {
    const engine = new CommunicationEngine({
        budget: 100000,
        maxActivities: 100
    });

    engine.on("activityScheduled", activity => {
        console.log("Scheduled:", activity.title);
    });

    engine.on("activityApproved", activity => {
        console.log("Approved:", activity.title);
    });

    engine.on("audit", event => {
        console.log("AUDIT:", event.event);
    });

    const stakeholders = [
        new Stakeholder({
            name: "Executive Management",
            audience: "management",
            influence: 5,
            interest: 5,
            preferredChannels: ["report", "meeting"]
        }),
        new Stakeholder({
            name: "Technical Team",
            audience: "technical",
            influence: 3,
            interest: 5,
            preferredChannels: ["workshop"]
        }),
        new Stakeholder({
            name: "Employees",
            audience: "internal",
            influence: 2,
            interest: 4,
            preferredChannels: ["email"]
        }),
        new Stakeholder({
            name: "External Partners",
            audience: "external",
            influence: 4,
            interest: 2,
            preferredChannels: ["email"]
        })
    ];

    stakeholders.forEach(item => engine.addStakeholder(item));

    const objective = new CommunicationObjective({
        title: "Digital Transformation",
        description: "Coordinate organizational transformation communication.",
        audiences: stakeholders.map(item => item.name),
        outcome: "Improve awareness and participation.",
        deadline: new Date(Date.now() + 30 * 86400000)
    });

    engine.addObjective(objective);
    objective.activate();

    const activity = new CommunicationActivity({
        objectiveId: objective.id,
        title: "Management briefing",
        message: "Present milestones, risks, and delivery responsibilities.",
        channel: "meeting",
        audience: ["Executive Management"],
        owner: "Project Director",
        scheduledAt: new Date(Date.now() + 2 * 86400000),
        cost: 15000,
        approvalRequired: true
    });

    engine.schedule(activity);

    engine.approve(activity.id, "Chief Operating Officer");
    engine.start(activity.id);

    await engine.execute(activity.id, async item => {
        console.log("Executing communication:", item.title);

        // Demonstration adapter. Replace with an authenticated,
        // idempotent integration when using an external delivery service.
        return {
            success: true,
            provider: "local-demonstration",
            deliveredAt: new Date().toISOString()
        };
    });

    engine.complete(activity.id);

    engine.addFeedback(activity.id, {
        satisfaction: 5,
        understanding: 4,
        comment: "The briefing was clear."
    });

    console.log("\nSTAKEHOLDER MATRIX");
    console.log(engine.getStakeholderMatrix());

    console.log("\nCHANNEL RECOMMENDATIONS");

    for (const stakeholder of stakeholders) {
        console.log(
            stakeholder.name,
            "=>",
            engine.recommendChannel(stakeholder.name)
        );
    }

    console.log("\nEVALUATION");
    console.log(engine.evaluate());

    console.log("\nSCHEDULE CONFLICTS");
    console.log(engine.scheduleConflicts());

    await engine.export("communication_plan.json");
}

if (require.main === module) {
    main().catch(error => {
        console.error("Communication planning failed:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    Stakeholder,
    CommunicationObjective,
    CommunicationActivity,
    CommunicationEngine,
    ValidationError,
    PolicyError
};
