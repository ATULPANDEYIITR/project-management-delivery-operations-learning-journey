"use strict";

/*
 * Leadership in Project Management
 *
 * Event-driven project leadership and team coordination model.
 *
 * Features:
 * - Situational leadership
 * - Team delegation
 * - Capacity management
 * - Stakeholder engagement
 * - Leadership decision records
 * - Risk evaluation
 * - Conflict resolution
 * - Asynchronous event processing
 * - Policy-based governance
 * - Performance reporting
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

const LeadershipStyle = Object.freeze({
    AUTOCRATIC: "autocratic",
    DEMOCRATIC: "democratic",
    TRANSFORMATIONAL: "transformational",
    TRANSACTIONAL: "transactional",
    SERVANT: "servant",
    SITUATIONAL: "situational"
});

const TaskStatus = Object.freeze({
    NOT_STARTED: "not_started",
    IN_PROGRESS: "in_progress",
    BLOCKED: "blocked",
    COMPLETED: "completed"
});

const DecisionStatus = Object.freeze({
    PROPOSED: "proposed",
    APPROVED: "approved",
    REJECTED: "rejected",
    DEFERRED: "deferred"
});

class LeadershipError extends Error {
    constructor(message) {
        super(message);
        this.name = "LeadershipError";
    }
}

class ValidationError extends LeadershipError {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class ProjectEventBus extends EventEmitter {
    constructor() {
        super({ captureRejections: true });
        this.setMaxListeners(50);

        this.on("error", error => {
            console.error("Event processing error:", error.message);
        });
    }

    async publish(eventName, payload) {
        const listeners = this.listeners(eventName);

        // Await asynchronous listeners so failures are visible to callers.
        const results = await Promise.allSettled(
            listeners.map(listener => listener(payload))
        );

        const failures = results.filter(
            result => result.status === "rejected"
        );

        if (failures.length > 0) {
            throw new LeadershipError(
                `${failures.length} event listener(s) failed.`
            );
        }
    }
}

class TeamMember {
    constructor({
        id,
        name,
        role,
        skillLevel,
        workload = 0,
        active = true
    }) {
        if (!Number.isInteger(id) || id <= 0) {
            throw new ValidationError("Invalid member ID.");
        }

        if (!name || !name.trim()) {
            throw new ValidationError("Member name is required.");
        }

        if (!Number.isInteger(skillLevel) ||
            skillLevel < 1 || skillLevel > 5) {
            throw new ValidationError("Skill level must be 1-5.");
        }

        if (!Number.isInteger(workload) ||
            workload < 0 || workload > 100) {
            throw new ValidationError("Invalid workload.");
        }

        this.id = id;
        this.name = name.trim();
        this.role = role;
        this.skillLevel = skillLevel;
        this.workload = workload;
        this.active = active;
        this.completedTasks = 0;
    }
}

class ProjectTask {
    constructor({
        id,
        title,
        requiredSkill,
        estimatedHours,
        priority
    }) {
        if (!Number.isInteger(id) || id <= 0) {
            throw new ValidationError("Invalid task ID.");
        }

        if (!title || !title.trim()) {
            throw new ValidationError("Task title is required.");
        }

        if (!Number.isFinite(estimatedHours) ||
            estimatedHours <= 0) {
            throw new ValidationError("Invalid estimated hours.");
        }

        if (!Number.isInteger(requiredSkill) ||
            requiredSkill < 1 || requiredSkill > 5) {
            throw new ValidationError("Required skill must be 1-5.");
        }

        if (!Number.isInteger(priority) ||
            priority < 1 || priority > 5) {
            throw new ValidationError("Priority must be 1-5.");
        }

        this.id = id;
        this.title = title.trim();
        this.requiredSkill = requiredSkill;
        this.estimatedHours = estimatedHours;
        this.priority = priority;
        this.status = TaskStatus.NOT_STARTED;
        this.assignedTo = null;
        this.progress = 0;
        this.version = 0;
    }
}

class LeadershipPolicy {
    static selectStyle({ skillLevel, urgency, complexity }) {
        for (const value of [urgency, complexity]) {
            if (!Number.isInteger(value) || value < 1 || value > 5) {
                throw new ValidationError(
                    "Urgency and complexity must be 1-5."
                );
            }
        }

        if (!Number.isInteger(skillLevel) ||
            skillLevel < 1 || skillLevel > 5) {
            throw new ValidationError("Invalid skill level.");
        }

        if (urgency >= 5) {
            return LeadershipStyle.AUTOCRATIC;
        }

        if (skillLevel <= 2) {
            return LeadershipStyle.SITUATIONAL;
        }

        if (complexity >= 4) {
            return LeadershipStyle.TRANSFORMATIONAL;
        }

        if (skillLevel >= 4) {
            return LeadershipStyle.SERVANT;
        }

        return LeadershipStyle.DEMOCRATIC;
    }

    static stakeholderStrategy(influence, interest) {
        if (
            !Number.isInteger(influence) ||
            !Number.isInteger(interest) ||
            influence < 1 || influence > 5 ||
            interest < 1 || interest > 5
        ) {
            throw new ValidationError(
                "Influence and interest must be 1-5."
            );
        }

        if (influence >= 4 && interest >= 4) {
            return "manage_closely";
        }

        if (influence >= 4) {
            return "keep_satisfied";
        }

        if (interest >= 4) {
            return "keep_informed";
        }

        return "monitor";
    }
}

class ProjectLeadership {
    constructor(name, style) {
        if (!name || !name.trim()) {
            throw new ValidationError("Project name is required.");
        }

        if (!Object.values(LeadershipStyle).includes(style)) {
            throw new ValidationError("Unsupported leadership style.");
        }

        this.name = name.trim();
        this.style = style;

        this.members = new Map();
        this.tasks = new Map();
        this.stakeholders = new Map();
        this.risks = new Map();
        this.decisions = new Map();

        this.events = new ProjectEventBus();
        this.auditLog = [];

        this.events.on("task.assigned", event => {
            this.audit("task.assigned", event);
        });

        this.events.on("task.completed", event => {
            this.audit("task.completed", event);
        });

        this.events.on("decision.approved", event => {
            this.audit("decision.approved", event);
        });
    }

    audit(type, payload) {
        this.auditLog.push({
            type,
            payload: structuredClone(payload),
            timestamp: new Date().toISOString()
        });
    }

    addMember(member) {
        if (!(member instanceof TeamMember)) {
            throw new ValidationError("Invalid team member.");
        }

        if (this.members.has(member.id)) {
            throw new ValidationError("Duplicate member ID.");
        }

        this.members.set(member.id, member);
    }

    addTask(task) {
        if (!(task instanceof ProjectTask)) {
            throw new ValidationError("Invalid task.");
        }

        if (this.tasks.has(task.id)) {
            throw new ValidationError("Duplicate task ID.");
        }

        this.tasks.set(task.id, task);
    }

    addStakeholder(stakeholder) {
        if (this.stakeholders.has(stakeholder.id)) {
            throw new ValidationError("Duplicate stakeholder ID.");
        }

        stakeholder.strategy = LeadershipPolicy.stakeholderStrategy(
            stakeholder.influence,
            stakeholder.interest
        );

        this.stakeholders.set(stakeholder.id, {
            ...stakeholder
        });
    }

    addRisk(risk) {
        if (this.risks.has(risk.id)) {
            throw new ValidationError("Duplicate risk ID.");
        }

        if (!this.members.has(risk.ownerId)) {
            throw new ValidationError("Risk owner does not exist.");
        }

        for (const field of ["probability", "impact"]) {
            if (
                !Number.isInteger(risk[field]) ||
                risk[field] < 1 ||
                risk[field] > 5
            ) {
                throw new ValidationError(
                    `${field} must be between 1 and 5.`
                );
            }
        }

        this.risks.set(risk.id, {
            ...risk,
            exposure: risk.probability * risk.impact,
            status: "open"
        });
    }

    async assignTask(taskId, memberId) {
        const task = this.tasks.get(taskId);
        const member = this.members.get(memberId);

        if (!task || !member) {
            throw new ValidationError(
                "Task or team member does not exist."
            );
        }

        if (!member.active) {
            throw new LeadershipError(
                "Inactive members cannot receive assignments."
            );
        }

        if (task.status === TaskStatus.COMPLETED) {
            throw new LeadershipError(
                "Completed tasks cannot be reassigned."
            );
        }

        if (member.skillLevel < task.requiredSkill) {
            throw new LeadershipError(
                "Insufficient member skill level."
            );
        }

        const allocation = 20;
        const previousMember = task.assignedTo === null
            ? null
            : this.members.get(task.assignedTo);

        const previousWorkload = previousMember?.workload ?? 0;

        const availableCapacity =
            member.workload -
            (previousMember?.id === member.id ? allocation : 0);

        if (availableCapacity + allocation > 100) {
            throw new LeadershipError("Team member is overloaded.");
        }

        // Validate first, then commit all related state changes.
        if (previousMember) {
            previousMember.workload = Math.max(
                0,
                previousMember.workload - allocation
            );
        }

        member.workload += allocation;
        task.assignedTo = memberId;
        task.status = TaskStatus.IN_PROGRESS;
        task.version++;

        try {
            await this.events.publish("task.assigned", {
                taskId,
                memberId,
                version: task.version
            });
        } catch (error) {
            // Restore the state if synchronous event processing fails.
            member.workload -= allocation;

            if (previousMember) {
                previousMember.workload = previousWorkload;
            }

            task.assignedTo = previousMember?.id ?? null;
            task.status = previousMember
                ? TaskStatus.IN_PROGRESS
                : TaskStatus.NOT_STARTED;
            task.version--;

            throw error;
        }
    }

    async updateProgress(taskId, progress, expectedVersion) {
        const task = this.tasks.get(taskId);

        if (!task) {
            throw new ValidationError("Task does not exist.");
        }

        if (
            !Number.isFinite(progress) ||
            progress < 0 ||
            progress > 100
        ) {
            throw new ValidationError("Progress must be 0-100.");
        }

        if (task.version !== expectedVersion) {
            throw new LeadershipError(
                "Concurrent modification detected."
            );
        }

        if (task.status === TaskStatus.COMPLETED) {
            throw new LeadershipError("Task is already completed.");
        }

        if (task.assignedTo === null) {
            throw new LeadershipError("Task has no owner.");
        }

        if (progress < task.progress) {
            throw new ValidationError(
                "Progress cannot decrease."
            );
        }

        const member = this.members.get(task.assignedTo);

        task.progress = progress;
        task.version++;

        if (progress === 100) {
            task.status = TaskStatus.COMPLETED;
            member.workload = Math.max(0, member.workload - 20);
            member.completedTasks++;

            await this.events.publish("task.completed", {
                taskId,
                memberId: member.id
            });
        }

        return task.version;
    }

    createDecision({ id, title, description, owner }) {
        if (this.decisions.has(id)) {
            throw new ValidationError("Duplicate decision ID.");
        }

        if (!title?.trim() || !owner?.trim()) {
            throw new ValidationError(
                "Decision title and owner are required."
            );
        }

        const decision = {
            id,
            title,
            description,
            owner,
            status: DecisionStatus.PROPOSED,
            rationale: null,
            createdAt: new Date().toISOString()
        };

        this.decisions.set(id, decision);
        return decision;
    }

    async processDecision(id, status, rationale) {
        const decision = this.decisions.get(id);

        if (!decision) {
            throw new ValidationError("Decision does not exist.");
        }

        if (decision.status !== DecisionStatus.PROPOSED) {
            throw new LeadershipError(
                "Decision has already been processed."
            );
        }

        if (!Object.values(DecisionStatus).includes(status)) {
            throw new ValidationError("Invalid decision status.");
        }

        if (!rationale?.trim()) {
            throw new ValidationError(
                "Decision rationale is mandatory."
            );
        }

        decision.status = status;
        decision.rationale = rationale;

        if (status === DecisionStatus.APPROVED) {
            await this.events.publish("decision.approved", {
                decisionId: id,
                owner: decision.owner
            });
        }

        return decision;
    }

    resolveConflict({ issue, options, selectedOption }) {
        if (!issue?.trim()) {
            throw new ValidationError("Conflict issue is required.");
        }

        if (!Array.isArray(options) || options.length < 2) {
            throw new ValidationError(
                "At least two resolution options are required."
            );
        }

        if (!options.includes(selectedOption)) {
            throw new ValidationError(
                "Selected resolution is not an available option."
            );
        }

        return {
            issue,
            options,
            selectedOption,
            approach: "collaborative",
            status: "resolved"
        };
    }

    getMetrics() {
        const tasks = [...this.tasks.values()];
        const members = [...this.members.values()];
        const risks = [...this.risks.values()];

        const completed = tasks.filter(
            task => task.status === TaskStatus.COMPLETED
        ).length;

        const activeMembers = members.filter(member => member.active);

        const averageWorkload = activeMembers.length
            ? activeMembers.reduce(
                (sum, member) => sum + member.workload, 0
            ) / activeMembers.length
            : 0;

        return {
            totalTasks: tasks.length,
            completedTasks: completed,
            completionRate: tasks.length
                ? Number((completed / tasks.length * 100).toFixed(2))
                : 0,
            averageProgress: tasks.length
                ? Number((
                    tasks.reduce((sum, task) => sum + task.progress, 0) /
                    tasks.length
                ).toFixed(2))
                : 0,
            averageTeamWorkload: Number(averageWorkload.toFixed(2)),
            highRisks: risks.filter(
                risk => risk.status === "open" && risk.exposure >= 12
            ).length
        };
    }

    report() {
        return {
            project: this.name,
            leadershipStyle: this.style,
            team: [...this.members.values()].map(member => ({
                id: member.id,
                name: member.name,
                role: member.role,
                workload: member.workload,
                completedTasks: member.completedTasks
            })),
            tasks: [...this.tasks.values()].map(task => ({
                id: task.id,
                title: task.title,
                status: task.status,
                progress: task.progress,
                assignedTo: task.assignedTo
            })),
            stakeholders: [...this.stakeholders.values()],
            risks: [...this.risks.values()],
            decisions: [...this.decisions.values()],
            metrics: this.getMetrics(),
            auditLog: this.auditLog
        };
    }

    async exportReport(filename) {
        if (!filename.endsWith(".json")) {
            throw new ValidationError(
                "Report must use the .json extension."
            );
        }

        await fs.writeFile(
            filename,
            JSON.stringify(this.report(), null, 2),
            { encoding: "utf8", flag: "w", mode: 0o600 }
        );
    }
}

async function main() {
    const project = new ProjectLeadership(
        "Digital Transformation Programme",
        LeadershipStyle.TRANSFORMATIONAL
    );

    project.addMember(new TeamMember({
        id: 1,
        name: "Ananya",
        role: "Project Manager",
        skillLevel: 5
    }));

    project.addMember(new TeamMember({
        id: 2,
        name: "Rahul",
        role: "Technical Lead",
        skillLevel: 4
    }));

    project.addMember(new TeamMember({
        id: 3,
        name: "Meera",
        role: "Business Analyst",
        skillLevel: 3
    }));

    project.addTask(new ProjectTask({
        id: 101,
        title: "Architecture assessment",
        requiredSkill: 4,
        estimatedHours: 40,
        priority: 5
    }));

    project.addTask(new ProjectTask({
        id: 102,
        title: "Requirements analysis",
        requiredSkill: 3,
        estimatedHours: 30,
        priority: 4
    }));

    project.addStakeholder({
        id: 1,
        name: "Executive Sponsor",
        influence: 5,
        interest: 5
    });

    project.addStakeholder({
        id: 2,
        name: "Operations Manager",
        influence: 4,
        interest: 3
    });

    project.addRisk({
        id: 201,
        description: "Integration delay",
        probability: 4,
        impact: 5,
        ownerId: 2,
        mitigation: "Weekly technical integration checkpoints"
    });

    await project.assignTask(101, 2);
    await project.assignTask(102, 3);

    const version = project.tasks.get(101).version;

    await project.updateProgress(101, 65, version);
    await project.updateProgress(102, 100, 1);

    project.createDecision({
        id: 301,
        title: "Phased implementation",
        description: "Deliver functionality in controlled phases.",
        owner: "Project Manager"
    });

    await project.processDecision(
        301,
        DecisionStatus.APPROVED,
        "Reduces operational disruption and delivery risk."
    );

    const conflict = project.resolveConflict({
        issue: "Disagreement over deployment timing",
        options: ["Full deployment", "Phased deployment"],
        selectedOption: "Phased deployment"
    });

    console.log("LEADERSHIP REPORT");
    console.log(JSON.stringify(project.report(), null, 2));

    console.log("\nCONFLICT RESOLUTION");
    console.log(conflict);

    console.log("\nSITUATIONAL LEADERSHIP");
    console.log(
        LeadershipPolicy.selectStyle({
            skillLevel: 3,
            urgency: 2,
            complexity: 4
        })
    );

    await project.exportReport("leadership_report.json");
    console.log("\nReport saved successfully.");
}

main().catch(error => {
    console.error("Project leadership execution failed:", error.message);
    process.exitCode = 1;
});
