"use strict";

/*
 * EVENT-DRIVEN PROJECT RISK PRIORITIZATION
 * Node.js 18+
 *
 * Models risk registration, assessment events, prioritization,
 * mitigation decisions, and risk monitoring.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

const RiskCategory = Object.freeze({
    TECHNICAL: "TECHNICAL",
    SECURITY: "SECURITY",
    FINANCIAL: "FINANCIAL",
    OPERATIONAL: "OPERATIONAL",
    LEGAL: "LEGAL",
    SCHEDULE: "SCHEDULE",
    RESOURCE: "RESOURCE",
    EXTERNAL: "EXTERNAL"
});

const RiskStatus = Object.freeze({
    IDENTIFIED: "IDENTIFIED",
    ASSESSED: "ASSESSED",
    MITIGATING: "MITIGATING",
    MONITORING: "MONITORING",
    CLOSED: "CLOSED"
});

const PRIORITY_THRESHOLDS = Object.freeze({
    CRITICAL: 60,
    HIGH: 35,
    MEDIUM: 15,
    LOW: 0
});

class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class RiskNotFoundError extends Error {
    constructor(id) {
        super(`Risk ${id} does not exist.`);
        this.name = "RiskNotFoundError";
    }
}

class Risk {
    constructor(data) {
        const {
            id,
            title,
            category,
            probability,
            impact,
            urgency,
            detectability,
            mitigationEffectiveness,
            owner,
            deadline,
            mitigationCost = 0,
            status = RiskStatus.IDENTIFIED
        } = data;

        this.id = id;
        this.title = title;
        this.category = category;
        this.probability = probability;
        this.impact = impact;
        this.urgency = urgency;
        this.detectability = detectability;
        this.mitigationEffectiveness = mitigationEffectiveness;
        this.owner = owner;
        this.deadline = deadline;
        this.mitigationCost = mitigationCost;
        this.status = status;

        this.validate();
    }

    validate() {
        if (
            typeof this.id !== "string" ||
            !this.id.trim() ||
            typeof this.title !== "string" ||
            !this.title.trim()
        ) {
            throw new ValidationError("Risk ID and title are required.");
        }

        if (!Object.values(RiskCategory).includes(this.category)) {
            throw new ValidationError("Invalid risk category.");
        }

        const numericFields = [
            "probability",
            "impact",
            "urgency",
            "detectability",
            "mitigationEffectiveness"
        ];

        for (const field of numericFields) {
            const value = this[field];

            if (!Number.isInteger(value) || value < 1 || value > 5) {
                throw new ValidationError(
                    `${field} must be an integer from 1 to 5.`
                );
            }
        }

        if (
            typeof this.owner !== "string" ||
            !this.owner.trim()
        ) {
            throw new ValidationError("Risk owner is required.");
        }

        if (
            typeof this.deadline !== "string" ||
            !/^\d{4}-\d{2}-\d{2}$/.test(this.deadline) ||
            Number.isNaN(Date.parse(this.deadline)) ||
            new Date(this.deadline).toISOString().slice(0, 10) !==
                this.deadline
        ) {
            throw new ValidationError("Invalid ISO date deadline.");
        }

        if (
            !Number.isFinite(this.mitigationCost) ||
            this.mitigationCost < 0
        ) {
            throw new ValidationError("Invalid mitigation cost.");
        }

        if (!Object.values(RiskStatus).includes(this.status)) {
            throw new ValidationError("Invalid risk status.");
        }
    }

    get inherentScore() {
        return this.probability * this.impact * this.urgency;
    }

    get residualScore() {
        const detectionFactor =
            0.8 + (this.detectability - 1) * 0.1;

        const mitigationFactor =
            1 - this.mitigationEffectiveness * 0.12;

        return Number(
            (this.inherentScore *
                detectionFactor *
                mitigationFactor).toFixed(2)
        );
    }

    get priority() {
        const score = this.residualScore;

        if (score >= PRIORITY_THRESHOLDS.CRITICAL) {
            return "CRITICAL";
        }

        if (score >= PRIORITY_THRESHOLDS.HIGH) {
            return "HIGH";
        }

        if (score >= PRIORITY_THRESHOLDS.MEDIUM) {
            return "MEDIUM";
        }

        return "LOW";
    }

    toJSON() {
        return {
            ...this,
            inherentScore: this.inherentScore,
            residualScore: this.residualScore,
            priority: this.priority
        };
    }
}

class RiskAssessmentEngine extends EventEmitter {
    #risks = new Map();
    #auditLog = [];

    constructor(projectName) {
        super();

        if (
            typeof projectName !== "string" ||
            !projectName.trim()
        ) {
            throw new ValidationError("Project name is required.");
        }

        this.projectName = projectName;
    }

    #recordEvent(event, details) {
        const entry = Object.freeze({
            event,
            details,
            timestamp: new Date().toISOString()
        });

        this.#auditLog.push(entry);
        this.emit(event, entry);
    }

    registerRisk(data) {
        const risk = new Risk(data);

        if (this.#risks.has(risk.id)) {
            throw new ValidationError(
                `Duplicate risk ID: ${risk.id}`
            );
        }

        this.#risks.set(risk.id, risk);

        this.#recordEvent("risk:registered", {
            riskId: risk.id,
            title: risk.title
        });

        return risk.toJSON();
    }

    getRisk(id) {
        const risk = this.#risks.get(id);

        if (!risk) {
            throw new RiskNotFoundError(id);
        }

        return risk;
    }

    updateAssessment(id, changes) {
        const risk = this.getRisk(id);

        if (risk.status === RiskStatus.CLOSED) {
            throw new ValidationError(
                "Closed risks cannot be reassessed."
            );
        }

        const allowed = new Set([
            "probability",
            "impact",
            "urgency",
            "detectability",
            "mitigationEffectiveness"
        ]);

        const keys = Object.keys(changes);

        if (keys.length === 0 || keys.some(key => !allowed.has(key))) {
            throw new ValidationError(
                "Assessment contains invalid or missing fields."
            );
        }

        const updated = new Risk({
            ...risk,
            ...changes
        });

        this.#risks.set(id, updated);

        this.#recordEvent("risk:reassessed", {
            riskId: id,
            residualScore: updated.residualScore,
            priority: updated.priority
        });

        return updated.toJSON();
    }

    transitionStatus(id, nextStatus) {
        const risk = this.getRisk(id);

        const transitions = {
            IDENTIFIED: ["ASSESSED", "CLOSED"],
            ASSESSED: ["MITIGATING", "MONITORING", "CLOSED"],
            MITIGATING: ["MONITORING", "ASSESSED", "CLOSED"],
            MONITORING: ["MITIGATING", "CLOSED"],
            CLOSED: []
        };

        if (!transitions[risk.status].includes(nextStatus)) {
            throw new ValidationError(
                `Invalid transition: ${risk.status} -> ${nextStatus}`
            );
        }

        risk.status = nextStatus;

        this.#recordEvent("risk:statusChanged", {
            riskId: id,
            status: nextStatus
        });

        return risk.toJSON();
    }

    rankRisks({ includeClosed = false } = {}) {
        return [...this.#risks.values()]
            .filter(risk =>
                includeClosed || risk.status !== RiskStatus.CLOSED
            )
            .sort((a, b) =>
                b.residualScore - a.residualScore ||
                b.inherentScore - a.inherentScore ||
                a.deadline.localeCompare(b.deadline) ||
                a.id.localeCompare(b.id)
            )
            .map(risk => risk.toJSON());
    }

    getCategoryExposure() {
        const exposure = new Map();

        for (const risk of this.#risks.values()) {
            if (risk.status === RiskStatus.CLOSED) {
                continue;
            }

            exposure.set(
                risk.category,
                (exposure.get(risk.category) || 0) +
                    risk.residualScore
            );
        }

        return Object.fromEntries(
            [...exposure.entries()].sort(
                (a, b) => b[1] - a[1] ||
                    a[0].localeCompare(b[0])
            )
        );
    }

    getMitigationQueue(budget) {
        if (!Number.isFinite(budget) || budget < 0) {
            throw new ValidationError("Invalid mitigation budget.");
        }

        const candidates = this.rankRisks()
            .filter(risk =>
                ["CRITICAL", "HIGH"].includes(risk.priority)
            );

        let remaining = budget;

        return candidates.map(risk => {
            const affordable = risk.mitigationCost <= remaining;

            if (affordable) {
                remaining -= risk.mitigationCost;
            }

            return {
                riskId: risk.id,
                priority: risk.priority,
                mitigationCost: risk.mitigationCost,
                funded: affordable,
                remainingBudget: Number(remaining.toFixed(2))
            };
        });
    }

    getAuditLog() {
        return this.#auditLog.map(entry => ({
            ...entry,
            details: { ...entry.details }
        }));
    }

    getReport() {
        const risks = this.rankRisks();

        const distribution = {
            CRITICAL: 0,
            HIGH: 0,
            MEDIUM: 0,
            LOW: 0
        };

        for (const risk of risks) {
            distribution[risk.priority]++;
        }

        return {
            project: this.projectName,
            generatedAt: new Date().toISOString(),
            totalActiveRisks: risks.length,
            distribution,
            categoryExposure: this.getCategoryExposure(),
            risks
        };
    }

    async exportReport(filename) {
        const safeName = filename.trim();

        if (
            !safeName ||
            safeName.includes("/") ||
            safeName.includes("\\") ||
            safeName.includes("..")
        ) {
            throw new ValidationError("Invalid export filename.");
        }

        const content = JSON.stringify(this.getReport(), null, 2);

        await fs.writeFile(safeName, content, {
            encoding: "utf8",
            flag: "wx"
        });
    }
}

function runTests() {
    const engine = new RiskAssessmentEngine("Test Project");

    const sample = {
        id: "R001",
        title: "Database breach",
        category: RiskCategory.SECURITY,
        probability: 5,
        impact: 5,
        urgency: 5,
        detectability: 5,
        mitigationEffectiveness: 1,
        owner: "Security Lead",
        deadline: "2026-12-01",
        mitigationCost: 50000
    };

    engine.registerRisk(sample);

    const risk = engine.getRisk("R001");

    console.assert(risk.inherentScore === 125);
    console.assert(risk.residualScore === 112.5);
    console.assert(risk.priority === "CRITICAL");

    engine.transitionStatus("R001", RiskStatus.ASSESSED);
    engine.transitionStatus("R001", RiskStatus.MITIGATING);

    try {
        engine.registerRisk(sample);
        throw new Error("Duplicate validation failed.");
    } catch (error) {
        if (!(error instanceof ValidationError)) {
            throw error;
        }
    }

    console.log("JavaScript validation tests passed.");
}

async function main() {
    runTests();

    const engine = new RiskAssessmentEngine(
        "Enterprise Digital Transformation"
    );

    engine.on("risk:registered", event => {
        console.log("Registered:", event.details.riskId);
    });

    engine.on("risk:reassessed", event => {
        console.log("Reassessed:", event.details);
    });

    const today = new Date();
    const deadline = days => {
        const result = new Date(today);
        result.setDate(result.getDate() + days);
        return result.toISOString().slice(0, 10);
    };

    const samples = [
        {
            id: "R001",
            title: "Cybersecurity breach",
            category: RiskCategory.SECURITY,
            probability: 5,
            impact: 5,
            urgency: 5,
            detectability: 5,
            mitigationEffectiveness: 1,
            owner: "Security Lead",
            deadline: deadline(5),
            mitigationCost: 150000
        },
        {
            id: "R002",
            title: "Cloud migration failure",
            category: RiskCategory.TECHNICAL,
            probability: 4,
            impact: 5,
            urgency: 4,
            detectability: 3,
            mitigationEffectiveness: 2,
            owner: "Cloud Architect",
            deadline: deadline(12),
            mitigationCost: 80000
        },
        {
            id: "R003",
            title: "Budget overrun",
            category: RiskCategory.FINANCIAL,
            probability: 4,
            impact: 4,
            urgency: 4,
            detectability: 2,
            mitigationEffectiveness: 3,
            owner: "Finance Lead",
            deadline: deadline(20),
            mitigationCost: 30000
        },
        {
            id: "R004",
            title: "Vendor delivery delay",
            category: RiskCategory.SCHEDULE,
            probability: 3,
            impact: 3,
            urgency: 2,
            detectability: 2,
            mitigationEffectiveness: 4,
            owner: "Project Manager",
            deadline: deadline(40),
            mitigationCost: 10000
        }
    ];

    for (const sample of samples) {
        engine.registerRisk(sample);
    }

    engine.updateAssessment("R003", {
        probability: 5,
        urgency: 5
    });

    engine.transitionStatus("R001", RiskStatus.ASSESSED);
    engine.transitionStatus("R001", RiskStatus.MITIGATING);

    console.log("\nRISK PRIORITY RANKING");

    console.table(
        engine.rankRisks().map(risk => ({
            ID: risk.id,
            Risk: risk.title,
            Score: risk.residualScore,
            Priority: risk.priority,
            Owner: risk.owner
        }))
    );

    console.log("\nCATEGORY EXPOSURE");
    console.log(engine.getCategoryExposure());

    console.log("\nMITIGATION QUEUE");
    console.table(engine.getMitigationQueue(100000));

    console.log("\nAUDIT EVENTS:", engine.getAuditLog().length);

    await engine.exportReport("risk_report.json");

    console.log("Risk report exported.");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
