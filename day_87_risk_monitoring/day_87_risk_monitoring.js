"use strict";

/*
 * Project Risk Monitoring and Tracking Engine
 *
 * Node.js 18+
 * No external dependencies.
 *
 * Implements:
 * - Risk identification and registration
 * - Probability-impact assessment
 * - Event-driven risk monitoring
 * - Mitigation and contingency management
 * - Risk escalation
 * - Monitoring schedules
 * - Policy evaluation
 * - Portfolio reporting
 * - JSON persistence
 */

const fs = require("node:fs/promises");
const { randomUUID } = require("node:crypto");
const EventEmitter = require("node:events");

// ------------------------------------------------------------
// Enumerations
// ------------------------------------------------------------

const RiskCategory = Object.freeze({
    SCHEDULE: "schedule",
    COST: "cost",
    TECHNICAL: "technical",
    RESOURCE: "resource",
    SECURITY: "security",
    OPERATIONAL: "operational",
    LEGAL: "legal",
    EXTERNAL: "external"
});

const RiskStatus = Object.freeze({
    IDENTIFIED: "identified",
    ASSESSED: "assessed",
    MITIGATION_PLANNED: "mitigation_planned",
    MONITORING: "monitoring",
    ESCALATED: "escalated",
    MATERIALIZED: "materialized",
    CLOSED: "closed"
});

const RiskResponse = Object.freeze({
    AVOID: "avoid",
    MITIGATE: "mitigate",
    TRANSFER: "transfer",
    ACCEPT: "accept"
});

const RiskLevel = Object.freeze({
    LOW: "low",
    MEDIUM: "medium",
    HIGH: "high",
    CRITICAL: "critical"
});

// ------------------------------------------------------------
// Domain exceptions
// ------------------------------------------------------------

class RiskError extends Error {
    constructor(message) {
        super(message);
        this.name = this.constructor.name;
    }
}

class ValidationError extends RiskError {}
class NotFoundError extends RiskError {}
class InvalidStateError extends RiskError {}
class VersionConflictError extends RiskError {}

// ------------------------------------------------------------
// Validation utilities
// ------------------------------------------------------------

function validateEnum(value, enumeration, field) {
    if (!Object.values(enumeration).includes(value)) {
        throw new ValidationError(`Invalid ${field}: ${value}`);
    }
}

function validateScore(value, field) {
    if (!Number.isInteger(value) || value < 1 || value > 5) {
        throw new ValidationError(
            `${field} must be an integer between 1 and 5`
        );
    }
}

function validateText(value, field) {
    if (
        typeof value !== "string" ||
        value.trim().length === 0
    ) {
        throw new ValidationError(`${field} is required`);
    }
}

function validateDate(value, field) {
    if (
        typeof value !== "string" ||
        !/^\d{4}-\d{2}-\d{2}$/.test(value)
    ) {
        throw new ValidationError(`${field} must use YYYY-MM-DD`);
    }

    const parsed = new Date(`${value}T00:00:00.000Z`);

    if (
        Number.isNaN(parsed.getTime()) ||
        parsed.toISOString().slice(0, 10) !== value
    ) {
        throw new ValidationError(`${field} is not a valid date`);
    }
}

// ------------------------------------------------------------
// Assessment policy
// ------------------------------------------------------------

class RiskAssessmentPolicy {
    constructor({
        lowMaximum = 4,
        mediumMaximum = 9,
        highMaximum = 16
    } = {}) {
        if (
            !Number.isInteger(lowMaximum) ||
            !Number.isInteger(mediumMaximum) ||
            !Number.isInteger(highMaximum) ||
            lowMaximum < 1 ||
            lowMaximum >= mediumMaximum ||
            mediumMaximum >= highMaximum ||
            highMaximum >= 25
        ) {
            throw new ValidationError(
                "Invalid assessment thresholds"
            );
        }

        this.thresholds = Object.freeze({
            lowMaximum,
            mediumMaximum,
            highMaximum
        });
    }

    evaluate(probability, impact) {
        validateScore(probability, "Probability");
        validateScore(impact, "Impact");

        const exposure = probability * impact;
        const { lowMaximum, mediumMaximum, highMaximum } =
            this.thresholds;

        let level;

        if (exposure <= lowMaximum) {
            level = RiskLevel.LOW;
        } else if (exposure <= mediumMaximum) {
            level = RiskLevel.MEDIUM;
        } else if (exposure <= highMaximum) {
            level = RiskLevel.HIGH;
        } else {
            level = RiskLevel.CRITICAL;
        }

        return Object.freeze({
            probability,
            impact,
            exposure,
            level
        });
    }
}

// ------------------------------------------------------------
// Risk entity
// ------------------------------------------------------------

class ProjectRisk {
    constructor(data) {
        validateText(data.projectId, "Project ID");
        validateText(data.title, "Risk title");
        validateText(data.description, "Description");
        validateText(data.owner, "Owner");

        validateEnum(data.category, RiskCategory, "category");
        validateEnum(data.response, RiskResponse, "response");

        validateScore(data.probability, "Probability");
        validateScore(data.impact, "Impact");
        validateDate(data.dueDate, "Due date");

        this.id = randomUUID();
        this.projectId = data.projectId.trim();
        this.title = data.title.trim();
        this.description = data.description.trim();
        this.category = data.category;
        this.owner = data.owner.trim();
        this.probability = data.probability;
        this.impact = data.impact;
        this.dueDate = data.dueDate;

        this.response = data.response;
        this.mitigationPlan = data.mitigationPlan || "";
        this.contingencyPlan = data.contingencyPlan || "";

        this.status = RiskStatus.IDENTIFIED;
        this.version = 1;

        this.createdAt = new Date().toISOString();
        this.updatedAt = this.createdAt;
        this.lastReviewed = null;
        this.reviewCount = 0;

        this.observations = [];
        this.history = [];
    }

    snapshot() {
        return structuredClone(this);
    }
}

// ------------------------------------------------------------
// Lifecycle policy
// ------------------------------------------------------------

const TRANSITIONS = new Map([
    [RiskStatus.IDENTIFIED, new Set([
        RiskStatus.ASSESSED,
        RiskStatus.CLOSED
    ])],
    [RiskStatus.ASSESSED, new Set([
        RiskStatus.MITIGATION_PLANNED,
        RiskStatus.MONITORING,
        RiskStatus.ESCALATED,
        RiskStatus.CLOSED
    ])],
    [RiskStatus.MITIGATION_PLANNED, new Set([
        RiskStatus.MONITORING,
        RiskStatus.ESCALATED,
        RiskStatus.CLOSED
    ])],
    [RiskStatus.MONITORING, new Set([
        RiskStatus.ESCALATED,
        RiskStatus.MATERIALIZED,
        RiskStatus.CLOSED
    ])],
    [RiskStatus.ESCALATED, new Set([
        RiskStatus.MONITORING,
        RiskStatus.MATERIALIZED,
        RiskStatus.CLOSED
    ])],
    [RiskStatus.MATERIALIZED, new Set([
        RiskStatus.CLOSED
    ])],
    [RiskStatus.CLOSED, new Set()]
]);

class RiskLifecyclePolicy {
    static validateTransition(current, next, risk) {
        const allowed = TRANSITIONS.get(current);

        if (!allowed || !allowed.has(next)) {
            throw new InvalidStateError(
                `Transition ${current} -> ${next} is prohibited`
            );
        }

        if (
            next === RiskStatus.MITIGATION_PLANNED &&
            !risk.mitigationPlan.trim()
        ) {
            throw new ValidationError(
                "A mitigation plan is mandatory"
            );
        }
    }
}

// ------------------------------------------------------------
// Event-driven monitoring engine
// ------------------------------------------------------------

class RiskMonitoringEngine extends EventEmitter {
    constructor(policy = new RiskAssessmentPolicy()) {
        super();

        this.policy = policy;
        this.risks = new Map();
        this.projectIndex = new Map();

        // Prevent application-level event listeners from
        // crashing risk-management operations.
        this.on("risk:critical", event => {
            console.error(
                `[CRITICAL] ${event.title} | ${event.id}`
            );
        });

        this.on("risk:overdue", event => {
            console.warn(
                `[OVERDUE] ${event.title} | Owner: ${event.owner}`
            );
        });
    }

    register(data) {
        const risk = new ProjectRisk(data);

        this.risks.set(risk.id, risk);

        if (!this.projectIndex.has(risk.projectId)) {
            this.projectIndex.set(risk.projectId, new Set());
        }

        this.projectIndex.get(risk.projectId).add(risk.id);

        risk.history.push({
            event: "registered",
            timestamp: new Date().toISOString()
        });

        this.emit("risk:registered", risk.snapshot());

        return risk.snapshot();
    }

    get(id) {
        const risk = this.risks.get(id);

        if (!risk) {
            throw new NotFoundError(`Risk ${id} not found`);
        }

        return risk;
    }

    listByProject(projectId) {
        const ids = this.projectIndex.get(projectId);

        if (!ids) {
            return [];
        }

        return [...ids].map(id => this.get(id).snapshot());
    }

    assess(id) {
        const risk = this.get(id);

        return this.policy.evaluate(
            risk.probability,
            risk.impact
        );
    }

    transition(id, nextStatus, expectedVersion) {
        const risk = this.get(id);

        if (risk.version !== expectedVersion) {
            throw new VersionConflictError(
                "The risk was modified by another operation"
            );
        }

        validateEnum(nextStatus, RiskStatus, "status");

        RiskLifecyclePolicy.validateTransition(
            risk.status,
            nextStatus,
            risk
        );

        const previous = risk.status;

        risk.status = nextStatus;
        risk.version++;
        risk.updatedAt = new Date().toISOString();

        risk.history.push({
            event: "status_changed",
            previous,
            next: nextStatus,
            timestamp: risk.updatedAt
        });

        this.emit("risk:status_changed", {
            id,
            previous,
            next: nextStatus,
            version: risk.version
        });

        return risk.snapshot();
    }

    addMitigation(id, plan, contingency, expectedVersion) {
        validateText(plan, "Mitigation plan");
        validateText(contingency, "Contingency plan");

        const risk = this.get(id);

        if (risk.version !== expectedVersion) {
            throw new VersionConflictError("Version mismatch");
        }

        if (risk.status !== RiskStatus.ASSESSED) {
            throw new InvalidStateError(
                "Mitigation must follow risk assessment"
            );
        }

        risk.mitigationPlan = plan.trim();
        risk.contingencyPlan = contingency.trim();

        risk.version++;
        risk.updatedAt = new Date().toISOString();

        risk.history.push({
            event: "mitigation_recorded",
            timestamp: risk.updatedAt
        });

        return this.transition(
            id,
            RiskStatus.MITIGATION_PLANNED,
            risk.version
        );
    }

    observe(id, observation, expectedVersion) {
        const risk = this.get(id);

        if (risk.version !== expectedVersion) {
            throw new VersionConflictError("Version mismatch");
        }

        if (
            ![
                RiskStatus.MONITORING,
                RiskStatus.ESCALATED
            ].includes(risk.status)
        ) {
            throw new InvalidStateError(
                "Risk is not under active monitoring"
            );
        }

        validateScore(
            observation.probability,
            "Observed probability"
        );

        validateScore(
            observation.impact,
            "Observed impact"
        );

        validateText(observation.recordedBy, "Recorded by");

        const previous = this.assess(id);

        risk.probability = observation.probability;
        risk.impact = observation.impact;
        risk.reviewCount++;

        const recordedAt = new Date().toISOString();
        risk.lastReviewed = recordedAt;

        const current = this.assess(id);

        const record = {
            ...observation,
            timestamp: recordedAt,
            previousExposure: previous.exposure,
            currentExposure: current.exposure,
            previousLevel: previous.level,
            currentLevel: current.level
        };

        risk.observations.push(record);

        risk.version++;
        risk.updatedAt = recordedAt;

        risk.history.push({
            event: "observation_recorded",
            timestamp: recordedAt,
            exposure: current.exposure
        });

        if (
            current.level === RiskLevel.CRITICAL &&
            risk.status !== RiskStatus.ESCALATED
        ) {
            const oldStatus = risk.status;

            risk.status = RiskStatus.ESCALATED;

            risk.history.push({
                event: "automatic_escalation",
                previous: oldStatus,
                timestamp: recordedAt
            });

            this.emit("risk:critical", {
                id,
                title: risk.title,
                owner: risk.owner,
                exposure: current.exposure
            });
        } else if (current.level === RiskLevel.HIGH) {
            this.emit("risk:high", {
                id,
                title: risk.title,
                exposure: current.exposure
            });
        }

        this.emit("risk:observed", {
            id,
            assessment: current,
            version: risk.version
        });

        return risk.snapshot();
    }

    close(id, reason, expectedVersion) {
        validateText(reason, "Closure reason");

        const risk = this.get(id);

        if (risk.version !== expectedVersion) {
            throw new VersionConflictError("Version mismatch");
        }

        if (
            !TRANSITIONS.get(risk.status).has(RiskStatus.CLOSED)
        ) {
            throw new InvalidStateError(
                "Risk cannot be closed from its current state"
            );
        }

        risk.history.push({
            event: "closure",
            reason: reason.trim(),
            timestamp: new Date().toISOString()
        });

        return this.transition(
            id,
            RiskStatus.CLOSED,
            expectedVersion
        );
    }

    evaluateOverdue(asOf = new Date()) {
        if (Number.isNaN(asOf.getTime())) {
            throw new ValidationError("Invalid evaluation date");
        }

        const today = asOf.toISOString().slice(0, 10);

        const overdue = [];

        for (const risk of this.risks.values()) {
            if (
                risk.status !== RiskStatus.CLOSED &&
                risk.dueDate < today
            ) {
                overdue.push(risk.snapshot());

                this.emit("risk:overdue", {
                    id: risk.id,
                    title: risk.title,
                    owner: risk.owner
                });
            }
        }

        return overdue;
    }

    findStaleRisks(maximumAgeDays = 7, asOf = new Date()) {
        if (
            !Number.isInteger(maximumAgeDays) ||
            maximumAgeDays < 0
        ) {
            throw new ValidationError(
                "Maximum age must be a non-negative integer"
            );
        }

        const cutoff = asOf.getTime() -
            maximumAgeDays * 86400000;

        return [...this.risks.values()]
            .filter(risk =>
                risk.status !== RiskStatus.CLOSED &&
                (
                    !risk.lastReviewed ||
                    new Date(risk.lastReviewed).getTime() < cutoff
                )
            )
            .map(risk => risk.snapshot());
    }

    portfolioReport() {
        const levels = new Map();
        const statuses = new Map();
        const categories = new Map();

        let exposure = 0;
        let active = 0;

        for (const risk of this.risks.values()) {
            const assessment = this.assess(risk.id);

            levels.set(
                assessment.level,
                (levels.get(assessment.level) || 0) + 1
            );

            statuses.set(
                risk.status,
                (statuses.get(risk.status) || 0) + 1
            );

            categories.set(
                risk.category,
                (categories.get(risk.category) || 0) + 1
            );

            exposure += assessment.exposure;

            if (risk.status !== RiskStatus.CLOSED) {
                active++;
            }
        }

        return {
            totalRisks: this.risks.size,
            activeRisks: active,
            totalExposure: exposure,
            averageExposure: this.risks.size
                ? Number((exposure / this.risks.size).toFixed(2))
                : 0,
            levels: Object.fromEntries(levels),
            statuses: Object.fromEntries(statuses),
            categories: Object.fromEntries(categories)
        };
    }

    priorityQueue() {
        return [...this.risks.values()]
            .filter(risk => risk.status !== RiskStatus.CLOSED)
            .map(risk => ({
                id: risk.id,
                title: risk.title,
                owner: risk.owner,
                ...this.assess(risk.id)
            }))
            .sort((a, b) =>
                b.exposure - a.exposure ||
                a.id.localeCompare(b.id)
            );
    }

    async save(filePath) {
        const data = [...this.risks.values()].map(risk =>
            risk.snapshot()
        );

        await fs.writeFile(
            filePath,
            JSON.stringify(data, null, 2),
            {
                encoding: "utf8",
                mode: 0o600
            }
        );
    }

    async load(filePath) {
        const content = await fs.readFile(filePath, "utf8");
        const data = JSON.parse(content);

        if (!Array.isArray(data)) {
            throw new ValidationError(
                "Risk register must contain an array"
            );
        }

        const replacement = new Map();
        const projectIndex = new Map();

        for (const item of data) {
            validateText(item.id, "Risk identifier");
            validateText(item.projectId, "Project ID");

            validateEnum(item.category, RiskCategory, "category");
            validateEnum(item.status, RiskStatus, "status");
            validateScore(item.probability, "Probability");
            validateScore(item.impact, "Impact");
            validateDate(item.dueDate, "Due date");

            if (replacement.has(item.id)) {
                throw new ValidationError(
                    "Duplicate risk identifier in imported data"
                );
            }

            replacement.set(item.id, structuredClone(item));

            if (!projectIndex.has(item.projectId)) {
                projectIndex.set(item.projectId, new Set());
            }

            projectIndex.get(item.projectId).add(item.id);
        }

        // Replace state only after the complete file passes validation.
        this.risks = replacement;
        this.projectIndex = projectIndex;
    }
}

// ------------------------------------------------------------
// Demonstration
// ------------------------------------------------------------

async function main() {
    const engine = new RiskMonitoringEngine();

    engine.on("risk:registered", risk => {
        console.log(`Registered: ${risk.title}`);
    });

    engine.on("risk:observed", event => {
        console.log(
            `Risk ${event.id}: exposure ${event.assessment.exposure}`
        );
    });

    engine.on("risk:status_changed", event => {
        console.log(
            `Status changed: ${event.previous} -> ${event.next}`
        );
    });

    const supplier = engine.register({
        projectId: "PRJ-2026-001",
        title: "Supplier delivery delay",
        description: "Hardware delivery may miss the milestone.",
        category: RiskCategory.SCHEDULE,
        owner: "Procurement Manager",
        probability: 4,
        impact: 4,
        dueDate: "2026-12-15",
        response: RiskResponse.MITIGATE
    });

    const security = engine.register({
        projectId: "PRJ-2026-001",
        title: "Access control weakness",
        description: "Incorrect role permissions may expose data.",
        category: RiskCategory.SECURITY,
        owner: "Security Manager",
        probability: 2,
        impact: 5,
        dueDate: "2026-12-05",
        response: RiskResponse.AVOID
    });

    let current = engine.transition(
        supplier.id,
        RiskStatus.ASSESSED,
        supplier.version
    );

    current = engine.addMitigation(
        supplier.id,
        "Qualify an alternative supplier.",
        "Use approved reserve inventory.",
        current.version
    );

    current = engine.transition(
        supplier.id,
        RiskStatus.MONITORING,
        current.version
    );

    current = engine.observe(
        supplier.id,
        {
            probability: 5,
            impact: 5,
            recordedBy: "Procurement Manager",
            notes: "Supplier has reported another delay."
        },
        current.version
    );

    console.log("\nPORTFOLIO REPORT");
    console.log(
        JSON.stringify(engine.portfolioReport(), null, 2)
    );

    console.log("\nPRIORITY QUEUE");
    console.table(engine.priorityQueue());

    console.log("\nSTALE RISKS");
    console.log(engine.findStaleRisks(7).length);

    console.log("\nOVERDUE RISKS");
    console.log(engine.evaluateOverdue().length);

    console.log("\nPROJECT RISKS");
    console.log(engine.listByProject("PRJ-2026-001").length);

    await engine.save("project_risk_register.json");

    // Demonstrate optimistic concurrency failure.
    try {
        engine.transition(
            security.id,
            RiskStatus.ASSESSED,
            99
        );
    } catch (error) {
        console.error(
            `Expected concurrency error: ${error.message}`
        );
    }

    // Demonstrate invalid score handling.
    try {
        engine.policy.evaluate(8, 3);
    } catch (error) {
        console.error(
            `Expected validation error: ${error.message}`
        );
    }
}

main().catch(error => {
    console.error("Risk monitoring failed:", error.message);
    process.exitCode = 1;
});
