"use strict";

/**
 * PROJECT RISK MANAGEMENT
 * Event-driven project risk register and assessment engine.
 *
 * Runtime: Node.js 18+
 * Execute: node project_risk_management.js
 *
 * Features:
 * - Risk identification and categorization
 * - Inherent and residual risk scoring
 * - Event-driven monitoring
 * - Response strategy evaluation
 * - Risk ownership
 * - Escalation and closure
 * - Portfolio-level risk aggregation
 * - Asynchronous persistence
 * - Validation and automated tests
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

const Category = Object.freeze({
    TECHNICAL: "Technical",
    FINANCIAL: "Financial",
    OPERATIONAL: "Operational",
    SCHEDULE: "Schedule",
    RESOURCE: "Resource",
    SECURITY: "Security",
    LEGAL: "Legal",
    QUALITY: "Quality",
    SCOPE: "Scope",
    EXTERNAL: "External"
});

const Status = Object.freeze({
    IDENTIFIED: "Identified",
    ASSESSED: "Assessed",
    PLANNED: "Response Planned",
    MONITORING: "Monitoring",
    ESCALATED: "Escalated",
    CLOSED: "Closed"
});

const Strategy = Object.freeze({
    AVOID: "Avoid",
    MITIGATE: "Mitigate",
    TRANSFER: "Transfer",
    ACCEPT: "Accept",
    EXPLOIT: "Exploit",
    ENHANCE: "Enhance",
    SHARE: "Share"
});

const LEVEL = Object.freeze({
    LOW: "Low",
    MEDIUM: "Medium",
    HIGH: "High",
    CRITICAL: "Critical"
});

const VALID_CATEGORIES = new Set(Object.values(Category));
const VALID_STRATEGIES = new Set(Object.values(Strategy));

class RiskError extends Error {
    constructor(message, code = "RISK_ERROR") {
        super(message);
        this.name = "RiskError";
        this.code = code;
    }
}

function validateScore(value, field) {
    if (
        !Number.isInteger(value) ||
        value < 1 ||
        value > 5
    ) {
        throw new RiskError(
            `${field} must be an integer between 1 and 5.`,
            "INVALID_SCORE"
        );
    }
}

function classifyRisk(score) {
    if (!Number.isInteger(score) || score < 1 || score > 25) {
        throw new RiskError("Invalid risk exposure score.");
    }

    if (score >= 20) return LEVEL.CRITICAL;
    if (score >= 12) return LEVEL.HIGH;
    if (score >= 6) return LEVEL.MEDIUM;
    return LEVEL.LOW;
}

function validateText(value, field) {
    if (typeof value !== "string" || !value.trim()) {
        throw new RiskError(`${field} is required.`);
    }

    return value.trim();
}

class Risk {
    constructor(data) {
        this.id = validateText(data.id, "Risk ID");
        this.title = validateText(data.title, "Risk title");
        this.description = validateText(
            data.description,
            "Risk description"
        );

        if (!VALID_CATEGORIES.has(data.category)) {
            throw new RiskError("Invalid risk category.");
        }

        this.category = data.category;
        this.owner = validateText(data.owner, "Risk owner");

        validateScore(data.probability, "Probability");
        validateScore(data.impact, "Impact");

        this.probability = data.probability;
        this.impact = data.impact;

        this.status = Status.IDENTIFIED;
        this.strategy = null;
        this.action = null;

        this.residual = null;

        this.responseCost = 0;
        this.contingencyReserve = 0;

        this.identifiedAt = new Date().toISOString();
        this.updatedAt = this.identifiedAt;

        this.history = [];
        this.tags = new Set(data.tags || []);

        this.record("IDENTIFIED", "Risk entered into register.");
    }

    get inherentScore() {
        return this.probability * this.impact;
    }

    get currentScore() {
        if (this.residual === null) {
            return this.inherentScore;
        }

        return (
            this.residual.probability *
            this.residual.impact
        );
    }

    get inherentLevel() {
        return classifyRisk(this.inherentScore);
    }

    get currentLevel() {
        return classifyRisk(this.currentScore);
    }

    record(event, details) {
        this.updatedAt = new Date().toISOString();

        this.history.push({
            event,
            details,
            timestamp: this.updatedAt
        });
    }

    assess() {
        this.assertOpen();

        this.status = Status.ASSESSED;

        this.record(
            "ASSESSED",
            `Inherent exposure: ${this.inherentScore}.`
        );
    }

    planResponse({
        strategy,
        action,
        responseCost = 0,
        contingencyReserve = 0
    }) {
        this.assertOpen();

        if (!VALID_STRATEGIES.has(strategy)) {
            throw new RiskError("Invalid response strategy.");
        }

        validateText(action, "Response action");

        for (const amount of [responseCost, contingencyReserve]) {
            if (!Number.isFinite(amount) || amount < 0) {
                throw new RiskError("Invalid financial amount.");
            }
        }

        this.strategy = strategy;
        this.action = action.trim();
        this.responseCost = responseCost;
        this.contingencyReserve = contingencyReserve;
        this.status = Status.PLANNED;

        this.record(
            "RESPONSE_PLANNED",
            `${strategy}: ${this.action}`
        );
    }

    updateResidual(probability, impact) {
        this.assertOpen();

        validateScore(probability, "Residual probability");
        validateScore(impact, "Residual impact");

        this.residual = {
            probability,
            impact,
            updatedAt: new Date().toISOString()
        };

        this.status = Status.MONITORING;

        this.record(
            "MONITORED",
            `Residual exposure: ${this.currentScore}.`
        );
    }

    escalate(reason) {
        this.assertOpen();

        this.status = Status.ESCALATED;

        this.record(
            "ESCALATED",
            validateText(reason, "Escalation reason")
        );
    }

    close(resolution) {
        this.assertOpen();

        this.status = Status.CLOSED;

        this.record(
            "CLOSED",
            validateText(resolution, "Closure resolution")
        );
    }

    assertOpen() {
        if (this.status === Status.CLOSED) {
            throw new RiskError("Closed risks cannot be modified.");
        }
    }

    toJSON() {
        return {
            id: this.id,
            title: this.title,
            description: this.description,
            category: this.category,
            owner: this.owner,
            probability: this.probability,
            impact: this.impact,
            inherentScore: this.inherentScore,
            inherentLevel: this.inherentLevel,
            residual: this.residual,
            currentScore: this.currentScore,
            currentLevel: this.currentLevel,
            strategy: this.strategy,
            action: this.action,
            responseCost: this.responseCost,
            contingencyReserve: this.contingencyReserve,
            status: this.status,
            identifiedAt: this.identifiedAt,
            updatedAt: this.updatedAt,
            tags: [...this.tags],
            history: this.history
        };
    }
}

class RiskRegister extends EventEmitter {
    #risks = new Map();

    constructor(project) {
        super();

        this.projectId = validateText(project.id, "Project ID");
        this.projectName = validateText(
            project.name,
            "Project name"
        );
    }

    add(data) {
        const risk = data instanceof Risk ? data : new Risk(data);

        if (this.#risks.has(risk.id)) {
            throw new RiskError(
                `Duplicate risk ID: ${risk.id}`
            );
        }

        this.#risks.set(risk.id, risk);

        this.emit("risk:identified", risk.toJSON());

        return risk;
    }

    get(id) {
        const risk = this.#risks.get(id);

        if (!risk) {
            throw new RiskError(`Risk ${id} does not exist.`);
        }

        return risk;
    }

    assess(id) {
        const risk = this.get(id);
        risk.assess();

        this.emit("risk:assessed", risk.toJSON());

        return risk;
    }

    planResponse(id, response) {
        const risk = this.get(id);
        risk.planResponse(response);

        this.emit("risk:response-planned", risk.toJSON());

        return risk;
    }

    monitor(id, probability, impact) {
        const risk = this.get(id);
        risk.updateResidual(probability, impact);

        this.emit("risk:monitored", risk.toJSON());

        if (risk.currentScore >= 20) {
            this.emit("risk:critical", risk.toJSON());
        }

        return risk;
    }

    escalate(id, reason) {
        const risk = this.get(id);
        risk.escalate(reason);

        this.emit("risk:escalated", risk.toJSON());

        return risk;
    }

    close(id, resolution) {
        const risk = this.get(id);
        risk.close(resolution);

        this.emit("risk:closed", risk.toJSON());

        return risk;
    }

    list({ status, category, owner } = {}) {
        return [...this.#risks.values()]
            .filter(risk => !status || risk.status === status)
            .filter(risk => !category || risk.category === category)
            .filter(
                risk =>
                    !owner ||
                    risk.owner.toLowerCase() === owner.toLowerCase()
            );
    }

    prioritized() {
        return this.list().sort(
            (a, b) =>
                b.currentScore - a.currentScore ||
                b.inherentScore - a.inherentScore ||
                a.id.localeCompare(b.id)
        );
    }

    getSummary() {
        const risks = this.list();

        const active = risks.filter(
            risk => risk.status !== Status.CLOSED
        );

        const levelCounts = Object.fromEntries(
            Object.values(LEVEL).map(level => [
                level,
                active.filter(
                    risk => risk.currentLevel === level
                ).length
            ])
        );

        const categoryExposure = new Map();

        for (const risk of active) {
            categoryExposure.set(
                risk.category,
                (categoryExposure.get(risk.category) || 0) +
                    risk.currentScore
            );
        }

        return {
            projectId: this.projectId,
            projectName: this.projectName,
            totalRisks: risks.length,
            activeRisks: active.length,
            closedRisks: risks.length - active.length,
            inherentExposure: active.reduce(
                (sum, risk) => sum + risk.inherentScore,
                0
            ),
            residualExposure: active.reduce(
                (sum, risk) => sum + risk.currentScore,
                0
            ),
            levelCounts,
            categoryExposure: Object.fromEntries(categoryExposure)
        };
    }

    export() {
        return {
            project: {
                id: this.projectId,
                name: this.projectName
            },
            exportedAt: new Date().toISOString(),
            risks: this.list().map(risk => risk.toJSON())
        };
    }
}

class RiskPolicy {
    constructor({
        criticalThreshold = 20,
        highThreshold = 12,
        mediumThreshold = 6,
        minimumOwner = true,
        mandatoryResponseForHigh = true
    } = {}) {
        this.criticalThreshold = criticalThreshold;
        this.highThreshold = highThreshold;
        this.mediumThreshold = mediumThreshold;
        this.minimumOwner = minimumOwner;
        this.mandatoryResponseForHigh = mandatoryResponseForHigh;

        if (
            criticalThreshold > 25 ||
            highThreshold >= criticalThreshold ||
            mediumThreshold >= highThreshold ||
            mediumThreshold < 1
        ) {
            throw new RiskError("Invalid risk policy thresholds.");
        }
    }

    evaluate(risk) {
        const violations = [];

        if (this.minimumOwner && !risk.owner) {
            violations.push("Risk owner is missing.");
        }

        if (
            this.mandatoryResponseForHigh &&
            risk.currentScore >= this.highThreshold &&
            !risk.strategy
        ) {
            violations.push(
                "A high or critical risk requires a response strategy."
            );
        }

        return {
            riskId: risk.id,
            score: risk.currentScore,
            level: classifyRisk(risk.currentScore),
            eligibleForMonitoring: violations.length === 0,
            violations
        };
    }
}

class RiskRepository {
    constructor(filename) {
        this.filename = path.resolve(filename);
    }

    async save(register) {
        const data = JSON.stringify(register.export(), null, 2);
        const temporary = `${this.filename}.${crypto.randomUUID()}.tmp`;

        try {
            await fs.writeFile(temporary, data, {
                encoding: "utf8",
                flag: "wx",
                mode: 0o600
            });

            await fs.rename(temporary, this.filename);
        } catch (error) {
            await fs.rm(temporary, { force: true }).catch(() => {});

            throw new RiskError(
                `Risk register persistence failed: ${error.message}`,
                "PERSISTENCE_ERROR"
            );
        }
    }
}

function createDemoRegister() {
    const register = new RiskRegister({
        id: "PRJ-2026-001",
        name: "Enterprise Management Platform"
    });

    const data = [
        {
            id: "R001",
            title: "Infrastructure provisioning delay",
            description: "Cloud resources may not be ready on time.",
            category: Category.SCHEDULE,
            probability: 4,
            impact: 5,
            owner: "Infrastructure Lead"
        },
        {
            id: "R002",
            title: "Unexpected project expenditure",
            description: "Licensing costs may exceed the approved budget.",
            category: Category.FINANCIAL,
            probability: 3,
            impact: 5,
            owner: "Project Manager"
        },
        {
            id: "R003",
            title: "Unauthorized data access",
            description: "Confidential data may be accessed by unauthorized users.",
            category: Category.SECURITY,
            probability: 2,
            impact: 5,
            owner: "Security Lead"
        },
        {
            id: "R004",
            title: "Key personnel unavailability",
            description: "A critical developer may become unavailable.",
            category: Category.RESOURCE,
            probability: 3,
            impact: 4,
            owner: "Engineering Manager"
        },
        {
            id: "R005",
            title: "Uncontrolled scope changes",
            description: "New requirements may affect delivery commitments.",
            category: Category.SCOPE,
            probability: 4,
            impact: 4,
            owner: "Product Owner"
        }
    ];

    for (const item of data) {
        register.add(item);
        register.assess(item.id);
    }

    register.planResponse("R001", {
        strategy: Strategy.MITIGATE,
        action: "Maintain an alternative infrastructure provider.",
        responseCost: 10000,
        contingencyReserve: 5000
    });

    register.planResponse("R002", {
        strategy: Strategy.MITIGATE,
        action: "Introduce monthly expenditure controls.",
        responseCost: 2500,
        contingencyReserve: 8000
    });

    register.planResponse("R003", {
        strategy: Strategy.AVOID,
        action: "Enforce access controls and multi-factor authentication.",
        responseCost: 4000,
        contingencyReserve: 1000
    });

    register.planResponse("R004", {
        strategy: Strategy.MITIGATE,
        action: "Cross-train team members.",
        responseCost: 3000,
        contingencyReserve: 1000
    });

    register.planResponse("R005", {
        strategy: Strategy.AVOID,
        action: "Require formal change approval.",
        responseCost: 1000,
        contingencyReserve: 1000
    });

    register.monitor("R001", 2, 4);
    register.monitor("R002", 2, 4);
    register.monitor("R003", 1, 4);
    register.monitor("R004", 2, 3);
    register.monitor("R005", 2, 3);

    return register;
}

async function runTests() {
    const risk = new Risk({
        id: "TEST-001",
        title: "Test risk",
        description: "Validation scenario.",
        category: Category.TECHNICAL,
        probability: 3,
        impact: 4,
        owner: "Test Manager"
    });

    if (risk.inherentScore !== 12) {
        throw new Error("Inherent score test failed.");
    }

    risk.planResponse({
        strategy: Strategy.MITIGATE,
        action: "Introduce automated tests."
    });

    risk.updateResidual(1, 2);

    if (risk.currentScore !== 2) {
        throw new Error("Residual score test failed.");
    }

    risk.close("Resolved.");

    try {
        risk.updateResidual(2, 2);
        throw new Error("Closed risk modification was permitted.");
    } catch (error) {
        if (!(error instanceof RiskError)) throw error;
    }

    try {
        validateScore(7, "Probability");
        throw new Error("Invalid probability was permitted.");
    } catch (error) {
        if (!(error instanceof RiskError)) throw error;
    }

    console.log("All JavaScript validation tests passed.");
}

async function main() {
    const register = createDemoRegister();

    register.on("risk:critical", risk => {
        console.error(
            `CRITICAL RISK ALERT: ${risk.id} | ${risk.title}`
        );
    });

    register.on("risk:escalated", risk => {
        console.log(`Escalation recorded: ${risk.id}`);
    });

    const policy = new RiskPolicy();

    console.log("\nPROJECT RISK REGISTER");

    console.table(
        register.prioritized().map(risk => ({
            ID: risk.id,
            Title: risk.title,
            Category: risk.category,
            Owner: risk.owner,
            Inherent: risk.inherentScore,
            Residual: risk.currentScore,
            Level: risk.currentLevel,
            Status: risk.status
        }))
    );

    console.log("\nPOLICY EVALUATION");

    for (const risk of register.list()) {
        console.log(policy.evaluate(risk));
    }

    console.log("\nPORTFOLIO SUMMARY");
    console.log(register.getSummary());

    const repository = new RiskRepository(
        "project_risk_register.json"
    );

    await repository.save(register);

    await runTests();

    console.log("\nRisk register saved successfully.");
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
