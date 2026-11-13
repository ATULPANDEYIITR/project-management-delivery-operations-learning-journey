"use strict";

/*
 * Project Status Reporting and Event-Driven Governance
 * Runtime: Node.js 18+
 *
 * Includes:
 * - Event-driven project tracking
 * - Asynchronous report generation
 * - Task and milestone monitoring
 * - Risk and financial evaluation
 * - Pull Request and review tracking
 * - Approval and branch protection policies
 * - Merge eligibility evaluation
 * - JSON report persistence
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const EventEmitter = require("node:events");
const crypto = require("node:crypto");

class DomainError extends Error {
    constructor(message) {
        super(message);
        this.name = "DomainError";
    }
}

const TaskState = Object.freeze({
    TODO: "todo",
    IN_PROGRESS: "in_progress",
    BLOCKED: "blocked",
    COMPLETED: "completed"
});

const PRState = Object.freeze({
    DRAFT: "draft",
    OPEN: "open",
    MERGED: "merged",
    CLOSED: "closed"
});

const ReviewState = Object.freeze({
    APPROVED: "approved",
    CHANGES_REQUESTED: "changes_requested",
    COMMENTED: "commented",
    DISMISSED: "dismissed"
});

const RiskState = Object.freeze({
    OPEN: "open",
    MITIGATING: "mitigating",
    CLOSED: "closed"
});

function requireText(value, field) {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new DomainError(`${field} must be a non-empty string.`);
    }
}

function requireNonNegative(value, field) {
    if (!Number.isFinite(value) || value < 0) {
        throw new DomainError(`${field} must be a non-negative number.`);
    }
}

function requirePositive(value, field) {
    if (!Number.isFinite(value) || value <= 0) {
        throw new DomainError(`${field} must be positive.`);
    }
}

class Task {
    constructor({
        id, title, owner, state,
        priority, estimatedHours, actualHours = 0
    }) {
        requireText(id, "Task ID");
        requireText(title, "Task title");
        requireText(owner, "Task owner");
        requirePositive(estimatedHours, "Estimated hours");
        requireNonNegative(actualHours, "Actual hours");

        if (!Object.values(TaskState).includes(state)) {
            throw new DomainError("Invalid task state.");
        }

        if (!["low", "medium", "high", "critical"].includes(priority)) {
            throw new DomainError("Invalid task priority.");
        }

        this.id = id;
        this.title = title;
        this.owner = owner;
        this.state = state;
        this.priority = priority;
        this.estimatedHours = estimatedHours;
        this.actualHours = actualHours;
    }
}

class Milestone {
    constructor({ id, name, dueDate, completed = false }) {
        requireText(id, "Milestone ID");
        requireText(name, "Milestone name");

        if (!Number.isFinite(Date.parse(dueDate))) {
            throw new DomainError("Invalid milestone date.");
        }

        this.id = id;
        this.name = name;
        this.dueDate = dueDate;
        this.completed = Boolean(completed);
    }
}

class Risk {
    constructor({
        id, description, probability, impact,
        owner, mitigation, state = RiskState.OPEN
    }) {
        requireText(id, "Risk ID");
        requireText(description, "Risk description");
        requireText(owner, "Risk owner");
        requireText(mitigation, "Mitigation");

        if (
            !Number.isInteger(probability) ||
            probability < 1 || probability > 5 ||
            !Number.isInteger(impact) ||
            impact < 1 || impact > 5
        ) {
            throw new DomainError("Risk probability and impact must be 1-5.");
        }

        this.id = id;
        this.description = description;
        this.probability = probability;
        this.impact = impact;
        this.owner = owner;
        this.mitigation = mitigation;
        this.state = state;
    }

    get exposure() {
        return this.probability * this.impact;
    }
}

class Review {
    constructor({ reviewer, state, eligible = true, dismissed = false }) {
        requireText(reviewer, "Reviewer");

        if (!Object.values(ReviewState).includes(state)) {
            throw new DomainError("Invalid review state.");
        }

        this.reviewer = reviewer;
        this.state = state;
        this.eligible = Boolean(eligible);
        this.dismissed = Boolean(dismissed);
    }
}

class PullRequest {
    constructor({
        id, title, source, target,
        state = PRState.OPEN,
        draft = false,
        commits = 1,
        reviews = [],
        checks = [],
        conversationsResolved = true,
        synchronized = true,
        conflicts = false,
        strategy = "squash"
    }) {
        for (const [value, field] of [
            [id, "PR ID"],
            [title, "PR title"],
            [source, "Source branch"],
            [target, "Target branch"]
        ]) {
            requireText(value, field);
        }

        if (source === target) {
            throw new DomainError("Source and target branches must differ.");
        }

        if (!Object.values(PRState).includes(state)) {
            throw new DomainError("Invalid PR state.");
        }

        if (!Number.isInteger(commits) || commits < 0) {
            throw new DomainError("Invalid commit count.");
        }

        this.id = id;
        this.title = title;
        this.source = source;
        this.target = target;
        this.state = state;
        this.draft = Boolean(draft);
        this.commits = commits;
        this.reviews = reviews;
        this.checks = checks;
        this.conversationsResolved = Boolean(conversationsResolved);
        this.synchronized = Boolean(synchronized);
        this.conflicts = Boolean(conflicts);
        this.strategy = strategy;
    }
}

class BranchPolicy {
    constructor({
        branch,
        approvals = 2,
        requiredChecks = [],
        conversations = true,
        synchronized = true,
        linearHistory = false,
        directPush = false,
        forcePush = false,
        deletion = false,
        administratorBypass = false
    }) {
        requireText(branch, "Protected branch");

        if (!Number.isInteger(approvals) || approvals < 0) {
            throw new DomainError("Invalid approval requirement.");
        }

        this.branch = branch;
        this.approvals = approvals;
        this.requiredChecks = new Set(requiredChecks);
        this.conversations = conversations;
        this.synchronized = synchronized;
        this.linearHistory = linearHistory;
        this.directPush = directPush;
        this.forcePush = forcePush;
        this.deletion = deletion;
        this.administratorBypass = administratorBypass;
    }
}

class Project {
    constructor({
        id, name, manager, startDate,
        targetDate, budget, actualCost = 0
    }) {
        requireText(id, "Project ID");
        requireText(name, "Project name");
        requireText(manager, "Project manager");
        requirePositive(budget, "Budget");
        requireNonNegative(actualCost, "Actual cost");

        if (
            !Number.isFinite(Date.parse(startDate)) ||
            !Number.isFinite(Date.parse(targetDate)) ||
            Date.parse(targetDate) < Date.parse(startDate)
        ) {
            throw new DomainError("Invalid project date range.");
        }

        this.id = id;
        this.name = name;
        this.manager = manager;
        this.startDate = startDate;
        this.targetDate = targetDate;
        this.budget = budget;
        this.actualCost = actualCost;

        this.tasks = new Map();
        this.milestones = new Map();
        this.risks = new Map();
        this.pullRequests = new Map();
    }

    add(collection, item) {
        if (collection.has(item.id)) {
            throw new DomainError(`Duplicate identifier: ${item.id}`);
        }

        collection.set(item.id, item);
    }
}

class ProjectEventBus extends EventEmitter {
    publish(type, payload) {
        this.emit(type, Object.freeze({
            eventId: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
            payload
        }));
    }
}

class GovernanceService {

    evaluate(pr, policy) {
        const reasons = [];

        if (pr.state !== PRState.OPEN) {
            reasons.push("Pull Request is not open.");
        }

        if (pr.draft) {
            reasons.push("Draft Pull Request cannot be merged.");
        }

        if (pr.target !== policy.branch) {
            reasons.push("Incorrect protected target branch.");
        }

        if (pr.commits === 0) {
            reasons.push("Pull Request contains no commits.");
        }

        if (pr.conflicts) {
            reasons.push("Merge conflicts exist.");
        }

        if (policy.synchronized && !pr.synchronized) {
            reasons.push("Base branch synchronization required.");
        }

        if (policy.conversations && !pr.conversationsResolved) {
            reasons.push("Review conversations remain unresolved.");
        }

        const approvedReviewers = new Set(
            pr.reviews
                .filter(review =>
                    review.eligible &&
                    !review.dismissed &&
                    review.state === ReviewState.APPROVED
                )
                .map(review => review.reviewer)
        );

        if (approvedReviewers.size < policy.approvals) {
            reasons.push(
                `Approval requirement not met: ${approvedReviewers.size}/${policy.approvals}.`
            );
        }

        const checks = new Map(
            pr.checks.map(check => [check.name, check.passed])
        );

        for (const required of policy.requiredChecks) {
            if (checks.get(required) !== true) {
                reasons.push(`Missing or failed check: ${required}`);
            }
        }

        if (
            policy.linearHistory &&
            pr.strategy === "merge_commit"
        ) {
            reasons.push("Merge commit violates linear-history policy.");
        }

        return {
            pullRequestId: pr.id,
            eligible: reasons.length === 0,
            reasons
        };
    }
}

class ReportService {

    constructor(project, eventBus) {
        this.project = project;
        this.events = eventBus;
    }

    completion() {
        const tasks = [...this.project.tasks.values()];

        if (tasks.length === 0) return 0;

        return Number((
            tasks.filter(t => t.state === TaskState.COMPLETED).length /
            tasks.length * 100
        ).toFixed(2));
    }

    scheduleHealth() {
        const remainingDays = Math.ceil(
            (Date.parse(this.project.targetDate) - Date.now()) /
            86400000
        );

        return {
            remainingDays,
            targetDate: this.project.targetDate,
            completion: this.completion()
        };
    }

    financialHealth() {
        const variance = this.project.actualCost - this.project.budget;

        return {
            budget: this.project.budget,
            actualCost: this.project.actualCost,
            variance,
            utilization: Number((
                this.project.actualCost / this.project.budget * 100
            ).toFixed(2))
        };
    }

    calculateStatus() {
        const tasks = [...this.project.tasks.values()];
        const risks = [...this.project.risks.values()];

        if (tasks.length > 0 && tasks.every(
            task => task.state === TaskState.COMPLETED
        )) {
            return "completed";
        }

        if (this.financialHealth().utilization > 100) {
            return "delayed";
        }

        if (this.scheduleHealth().remainingDays < 0) {
            return "delayed";
        }

        if (tasks.some(
            task => task.state === TaskState.BLOCKED &&
                ["high", "critical"].includes(task.priority)
        )) {
            return "at_risk";
        }

        if (risks.some(
            risk => risk.state !== RiskState.CLOSED &&
                risk.exposure >= 15
        )) {
            return "at_risk";
        }

        return tasks.length ? "on_track" : "not_started";
    }

    riskMetrics() {
        const active = [...this.project.risks.values()]
            .filter(risk => risk.state !== RiskState.CLOSED)
            .sort((a, b) => b.exposure - a.exposure);

        return {
            total: this.project.risks.size,
            active: active.length,
            highExposure: active.filter(r => r.exposure >= 15).length,
            items: active.map(risk => ({
                id: risk.id,
                description: risk.description,
                owner: risk.owner,
                exposure: risk.exposure,
                mitigation: risk.mitigation
            }))
        };
    }

    deliveryMetrics() {
        const tasks = [...this.project.tasks.values()];

        return {
            total: tasks.length,
            completed: tasks.filter(
                t => t.state === TaskState.COMPLETED
            ).length,
            inProgress: tasks.filter(
                t => t.state === TaskState.IN_PROGRESS
            ).length,
            blocked: tasks.filter(
                t => t.state === TaskState.BLOCKED
            ).length,
            estimatedHours: tasks.reduce(
                (sum, t) => sum + t.estimatedHours, 0
            ),
            actualHours: tasks.reduce(
                (sum, t) => sum + t.actualHours, 0
            )
        };
    }

    repositoryMetrics() {
        const prs = [...this.project.pullRequests.values()];

        return {
            total: prs.length,
            open: prs.filter(p => p.state === PRState.OPEN).length,
            draft: prs.filter(p => p.draft).length,
            merged: prs.filter(p => p.state === PRState.MERGED).length,
            closed: prs.filter(p => p.state === PRState.CLOSED).length,
            approvals: prs.reduce(
                (sum, pr) => sum + new Set(
                    pr.reviews
                        .filter(r => r.eligible && !r.dismissed &&
                            r.state === ReviewState.APPROVED)
                        .map(r => r.reviewer)
                ).size,
                0
            )
        };
    }

    async generate() {
        // Yield control so report generation can participate in async workflows.
        await new Promise(resolve => setImmediate(resolve));

        const report = {
            metadata: {
                reportId: crypto.randomUUID(),
                generatedAt: new Date().toISOString(),
                projectId: this.project.id,
                projectName: this.project.name,
                manager: this.project.manager
            },
            status: this.calculateStatus(),
            schedule: this.scheduleHealth(),
            finances: this.financialHealth(),
            delivery: this.deliveryMetrics(),
            risks: this.riskMetrics(),
            repository: this.repositoryMetrics()
        };

        this.events.publish("report.generated", report);

        return report;
    }
}

class ReportRepository {

    constructor(directory = "output") {
        this.directory = directory;
    }

    async save(report) {
        await fs.mkdir(this.directory, { recursive: true });

        const safeName = report.metadata.projectId.replace(
            /[^a-zA-Z0-9_-]/g, "_"
        );

        const destination = path.join(
            this.directory,
            `${safeName}_status.json`
        );

        const temporary = `${destination}.${crypto.randomUUID()}.tmp`;

        try {
            await fs.writeFile(
                temporary,
                JSON.stringify(report, null, 2),
                { encoding: "utf8", flag: "wx", mode: 0o600 }
            );

            await fs.rename(temporary, destination);

            return destination;
        } catch (error) {
            await fs.rm(temporary, { force: true });
            throw error;
        }
    }
}

function buildProject() {
    const project = new Project({
        id: "PRJ-2026-001",
        name: "Enterprise Status Reporting Platform",
        manager: "Project Manager",
        startDate: "2026-09-01",
        targetDate: "2027-02-28",
        budget: 500000,
        actualCost: 185000
    });

    const tasks = [
        new Task({
            id: "T001",
            title: "Requirements analysis",
            owner: "Analyst",
            state: TaskState.COMPLETED,
            priority: "high",
            estimatedHours: 80,
            actualHours: 76
        }),
        new Task({
            id: "T002",
            title: "Database development",
            owner: "Developer",
            state: TaskState.COMPLETED,
            priority: "high",
            estimatedHours: 120,
            actualHours: 130
        }),
        new Task({
            id: "T003",
            title: "Reporting engine",
            owner: "Developer",
            state: TaskState.IN_PROGRESS,
            priority: "high",
            estimatedHours: 160,
            actualHours: 70
        }),
        new Task({
            id: "T004",
            title: "Security validation",
            owner: "Security Lead",
            state: TaskState.BLOCKED,
            priority: "critical",
            estimatedHours: 60,
            actualHours: 15
        }),
        new Task({
            id: "T005",
            title: "Deployment",
            owner: "Operations",
            state: TaskState.TODO,
            priority: "medium",
            estimatedHours: 50
        })
    ];

    tasks.forEach(task => project.add(project.tasks, task));

    project.add(project.milestones, new Milestone({
        id: "M001",
        name: "Requirements approved",
        dueDate: "2026-10-01",
        completed: true
    }));

    project.add(project.milestones, new Milestone({
        id: "M002",
        name: "Database completed",
        dueDate: "2026-11-20",
        completed: true
    }));

    project.add(project.risks, new Risk({
        id: "R001",
        description: "Security testing environment unavailable",
        probability: 4,
        impact: 5,
        owner: "Security Lead",
        mitigation: "Provision an isolated testing environment"
    }));

    project.add(project.risks, new Risk({
        id: "R002",
        description: "Reporting data quality issues",
        probability: 3,
        impact: 3,
        owner: "Data Lead",
        mitigation: "Introduce validation controls",
        state: RiskState.MITIGATING
    }));

    const pr = new PullRequest({
        id: "PR-101",
        title: "Implement reporting API",
        source: "feature/reporting",
        target: "main",
        state: PRState.OPEN,
        commits: 4,
        reviews: [
            new Review({
                reviewer: "reviewer-a",
                state: ReviewState.APPROVED
            }),
            new Review({
                reviewer: "reviewer-b",
                state: ReviewState.APPROVED
            })
        ],
        checks: [
            { name: "unit-tests", passed: true },
            { name: "security-scan", passed: true },
            { name: "lint", passed: true }
        ]
    });

    project.add(project.pullRequests, pr);

    const blockedPR = new PullRequest({
        id: "PR-102",
        title: "Add security controls",
        source: "feature/security",
        target: "main",
        draft: true,
        commits: 2,
        reviews: [
            new Review({
                reviewer: "reviewer-c",
                state: ReviewState.CHANGES_REQUESTED
            })
        ],
        checks: [
            { name: "unit-tests", passed: true },
            { name: "security-scan", passed: false }
        ],
        conversationsResolved: false
    });

    project.add(project.pullRequests, blockedPR);

    return project;
}

async function main() {
    const events = new ProjectEventBus();

    events.on("report.generated", report => {
        console.log(
            `Report event received: ${report.metadata.reportId}`
        );
    });

    const project = buildProject();
    const reports = new ReportService(project, events);
    const repository = new ReportRepository();

    const report = await reports.generate();

    const savedPath = await repository.save(report);

    const policy = new BranchPolicy({
        branch: "main",
        approvals: 2,
        requiredChecks: [
            "unit-tests",
            "security-scan",
            "lint"
        ],
        conversations: true,
        synchronized: true,
        linearHistory: true
    });

    const governance = new GovernanceService();

    console.log("\nPROJECT STATUS");
    console.log("============================");
    console.log("Project:", report.metadata.projectName);
    console.log("Status:", report.status);
    console.log("Completion:", report.schedule.completion + "%");
    console.log("Budget utilization:", report.finances.utilization + "%");
    console.log("Active risks:", report.risks.active);

    console.log("\nMERGE ELIGIBILITY");

    for (const pr of project.pullRequests.values()) {
        const result = governance.evaluate(pr, policy);

        console.log(`\n${pr.id}: ${result.eligible ? "ELIGIBLE" : "BLOCKED"}`);

        result.reasons.forEach(reason => {
            console.log(" -", reason);
        });
    }

    console.log("\nSaved report:", savedPath);

    if (report.delivery.total !== 5) {
        throw new DomainError("Unexpected delivery task count.");
    }

    if (report.status !== "at_risk") {
        throw new DomainError("Unexpected project health classification.");
    }

    console.log("Validation successful.");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
