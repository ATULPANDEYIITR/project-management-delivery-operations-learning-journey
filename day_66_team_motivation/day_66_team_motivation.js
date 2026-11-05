"use strict";

/*
 * Team Motivation Management System
 *
 * Event-driven implementation using Node.js.
 *
 * Features:
 * - Motivation assessment
 * - Self-determination theory
 * - Team engagement monitoring
 * - Goal progress events
 * - Recognition events
 * - Workload alerts
 * - Intervention recommendations
 * - Asynchronous report persistence
 * - Input validation and error handling
 *
 * Runtime: Node.js 18+
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const EventEmitter = require("node:events");

const MotivationLevel = Object.freeze({
    HIGH: "HIGH",
    MODERATE: "MODERATE",
    LOW: "LOW",
    CRITICAL: "CRITICAL"
});

const EventType = Object.freeze({
    MEMBER_ADDED: "memberAdded",
    GOAL_UPDATED: "goalUpdated",
    RECOGNITION: "recognition",
    MOTIVATION_ALERT: "motivationAlert"
});

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

function validateScore(value, field) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0 ||
        value > 100
    ) {
        throw new ValidationError(
            `${field} must be a number between 0 and 100.`
        );
    }
}

function validateText(value, field) {
    if (
        typeof value !== "string" ||
        value.trim().length === 0
    ) {
        throw new ValidationError(
            `${field} cannot be empty.`
        );
    }
}

class TeamMember {
    constructor(data) {
        if (!Number.isSafeInteger(data.id) || data.id <= 0) {
            throw new ValidationError("Invalid member ID.");
        }

        validateText(data.name, "Name");
        validateText(data.role, "Role");

        const attributes = [
            "autonomy",
            "competence",
            "relatedness",
            "workload",
            "psychologicalSafety",
            "engagement",
            "intrinsicMotivation",
            "extrinsicMotivation"
        ];

        for (const attribute of attributes) {
            validateScore(data[attribute], attribute);
        }

        this.id = data.id;
        this.name = data.name.trim();
        this.role = data.role.trim();

        for (const attribute of attributes) {
            this[attribute] = data[attribute];
        }

        this.createdAt = new Date().toISOString();
    }
}

class MotivationEngine extends EventEmitter {

    #members = new Map();
    #goals = new Map();
    #recognitions = [];
    #eventHistory = [];

    constructor() {
        super();

        // Internal event history supports auditing and debugging.
        for (const event of Object.values(EventType)) {
            this.on(event, (payload) => {
                this.#eventHistory.push({
                    event,
                    timestamp: new Date().toISOString(),
                    payload
                });
            });
        }
    }

    addMember(data) {
        const member = new TeamMember(data);

        if (this.#members.has(member.id)) {
            throw new ValidationError(
                "Member ID already exists."
            );
        }

        this.#members.set(member.id, member);

        this.emit(EventType.MEMBER_ADDED, {
            memberId: member.id
        });

        return member;
    }

    addGoal(goal) {
        if (!Number.isSafeInteger(goal.id) || goal.id <= 0) {
            throw new ValidationError("Invalid goal ID.");
        }

        if (this.#goals.has(goal.id)) {
            throw new ValidationError("Goal already exists.");
        }

        if (!this.#members.has(goal.ownerId)) {
            throw new ValidationError("Unknown goal owner.");
        }

        validateText(goal.description, "Goal description");

        if (
            !Number.isFinite(goal.target) ||
            goal.target <= 0
        ) {
            throw new ValidationError(
                "Goal target must be positive."
            );
        }

        this.#goals.set(goal.id, {
            ...goal,
            progress: 0,
            status: "NOT_STARTED"
        });
    }

    updateGoal(goalId, progress) {
        const goal = this.#goals.get(goalId);

        if (!goal) {
            throw new ValidationError("Goal not found.");
        }

        if (
            !Number.isFinite(progress) ||
            progress < 0 ||
            progress > goal.target
        ) {
            throw new ValidationError("Invalid goal progress.");
        }

        goal.progress = progress;

        goal.status =
            progress === goal.target
                ? "COMPLETED"
                : progress > 0
                    ? "IN_PROGRESS"
                    : "NOT_STARTED";

        this.emit(EventType.GOAL_UPDATED, {
            goalId,
            progress,
            status: goal.status
        });

        return { ...goal };
    }

    awardRecognition(data) {
        if (!this.#members.has(data.memberId)) {
            throw new ValidationError(
                "Recognition recipient does not exist."
            );
        }

        validateText(data.reason, "Recognition reason");

        const allowedTypes = [
            "PUBLIC",
            "PRIVATE",
            "DEVELOPMENT",
            "FINANCIAL",
            "TEAM"
        ];

        if (!allowedTypes.includes(data.type)) {
            throw new ValidationError(
                "Invalid recognition category."
            );
        }

        const recognition = Object.freeze({
            id: this.#recognitions.length + 1,
            memberId: data.memberId,
            type: data.type,
            reason: data.reason.trim(),
            timestamp: new Date().toISOString()
        });

        this.#recognitions.push(recognition);

        this.emit(EventType.RECOGNITION, {
            recognitionId: recognition.id,
            memberId: recognition.memberId
        });

        return recognition;
    }

    calculateScore(memberId) {
        const member = this.#members.get(memberId);

        if (!member) {
            throw new ValidationError("Member not found.");
        }

        const weights = {
            autonomy: 0.18,
            competence: 0.18,
            relatedness: 0.16,
            psychologicalSafety: 0.16,
            engagement: 0.14,
            intrinsicMotivation: 0.12,
            workloadBalance: 0.06
        };

        return Number((
            member.autonomy * weights.autonomy +
            member.competence * weights.competence +
            member.relatedness * weights.relatedness +
            member.psychologicalSafety *
                weights.psychologicalSafety +
            member.engagement * weights.engagement +
            member.intrinsicMotivation *
                weights.intrinsicMotivation +
            (100 - member.workload) *
                weights.workloadBalance
        ).toFixed(2));
    }

    classify(score) {
        if (score >= 80) return MotivationLevel.HIGH;
        if (score >= 65) return MotivationLevel.MODERATE;
        if (score >= 45) return MotivationLevel.LOW;

        return MotivationLevel.CRITICAL;
    }

    evaluate(memberId) {
        const member = this.#members.get(memberId);

        if (!member) {
            throw new ValidationError("Member not found.");
        }

        const score = this.calculateScore(memberId);
        const level = this.classify(score);

        const risks = [];

        if (member.workload >= 85) {
            risks.push("Potential burnout");
        }

        if (member.autonomy < 40) {
            risks.push("Insufficient autonomy");
        }

        if (member.competence < 40) {
            risks.push("Skill development required");
        }

        if (member.relatedness < 40) {
            risks.push("Weak team relationships");
        }

        if (member.psychologicalSafety < 40) {
            risks.push("Low psychological safety");
        }

        if (member.engagement < 40) {
            risks.push("Low engagement");
        }

        const actions = [];

        if (member.workload > 70) {
            actions.push("Review and rebalance workload.");
        }

        if (member.autonomy < 60) {
            actions.push("Increase ownership of decisions.");
        }

        if (member.competence < 60) {
            actions.push("Provide mentoring and training.");
        }

        if (member.relatedness < 60) {
            actions.push("Create opportunities for collaboration.");
        }

        if (member.psychologicalSafety < 60) {
            actions.push("Improve feedback and communication practices.");
        }

        if (member.engagement < 60) {
            actions.push("Conduct an individual engagement discussion.");
        }

        if (actions.length === 0) {
            actions.push("Maintain current engagement practices.");
        }

        const result = {
            memberId,
            memberName: member.name,
            score,
            level,
            risks,
            actions
        };

        if (
            level === MotivationLevel.LOW ||
            level === MotivationLevel.CRITICAL
        ) {
            this.emit(EventType.MOTIVATION_ALERT, {
                memberId,
                score,
                level
            });
        }

        return result;
    }

    teamReport() {
        const results = Array.from(
            this.#members.keys(),
            id => this.evaluate(id)
        );

        if (results.length === 0) {
            throw new ValidationError("No team members available.");
        }

        const total = results.reduce(
            (sum, result) => sum + result.score,
            0
        );

        const distribution = Object.fromEntries(
            Object.values(MotivationLevel).map(level => [
                level,
                results.filter(item => item.level === level).length
            ])
        );

        return {
            generatedAt: new Date().toISOString(),
            teamSize: results.length,
            averageScore: Number(
                (total / results.length).toFixed(2)
            ),
            distribution,
            members: results
        };
    }

    getEventHistory() {
        return this.#eventHistory.map(event => ({
            ...event,
            payload: { ...event.payload }
        }));
    }

    getGoals() {
        return Array.from(
            this.#goals.values(),
            goal => ({ ...goal })
        );
    }

    getRecognitions() {
        return this.#recognitions.map(item => ({ ...item }));
    }

    async saveReport(filename) {
        if (path.extname(filename).toLowerCase() !== ".json") {
            throw new ValidationError(
                "Report must use the JSON extension."
            );
        }

        const report = this.teamReport();

        // Exclusive creation prevents silently overwriting an existing report.
        await fs.writeFile(
            filename,
            JSON.stringify(report, null, 2),
            {
                encoding: "utf8",
                flag: "wx",
                mode: 0o600
            }
        );

        return filename;
    }
}

async function main() {

    const engine = new MotivationEngine();

    engine.on(EventType.MOTIVATION_ALERT, alert => {
        console.log(
            `ALERT: Member ${alert.memberId} requires attention.`
        );
    });

    engine.addMember({
        id: 1,
        name: "Ananya",
        role: "Software Developer",
        autonomy: 85,
        competence: 90,
        relatedness: 80,
        workload: 55,
        psychologicalSafety: 90,
        engagement: 88,
        intrinsicMotivation: 90,
        extrinsicMotivation: 65
    });

    engine.addMember({
        id: 2,
        name: "Rahul",
        role: "Business Analyst",
        autonomy: 35,
        competence: 55,
        relatedness: 45,
        workload: 90,
        psychologicalSafety: 40,
        engagement: 38,
        intrinsicMotivation: 45,
        extrinsicMotivation: 70
    });

    engine.addMember({
        id: 3,
        name: "Priya",
        role: "Project Manager",
        autonomy: 75,
        competence: 80,
        relatedness: 85,
        workload: 65,
        psychologicalSafety: 85,
        engagement: 78,
        intrinsicMotivation: 80,
        extrinsicMotivation: 75
    });

    engine.addGoal({
        id: 101,
        ownerId: 1,
        description: "Complete quarterly product release",
        target: 100
    });

    engine.updateGoal(101, 65);

    engine.awardRecognition({
        memberId: 1,
        type: "PUBLIC",
        reason: "Resolved a critical production issue."
    });

    console.log("\nINDIVIDUAL ASSESSMENTS");

    for (const id of [1, 2, 3]) {
        console.log(engine.evaluate(id));
    }

    console.log("\nTEAM REPORT");
    console.log(
        JSON.stringify(engine.teamReport(), null, 2)
    );

    console.log("\nEVENT HISTORY");
    console.log(engine.getEventHistory());

    try {
        await engine.saveReport(
            path.join(process.cwd(), "team_motivation_report.json")
        );

        console.log("Report saved successfully.");
    } catch (error) {
        console.error(
            "Report persistence failed:",
            error.message
        );
    }
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
