"use strict";

/**
 * Event-driven Enterprise Risk Register
 *
 * Models risk identification, assessment, treatment, monitoring,
 * escalation and reporting using JavaScript Maps, Sets and Events.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");

const Categories = Object.freeze([
    "Strategic",
    "Operational",
    "Financial",
    "Technological",
    "Cybersecurity",
    "Compliance",
    "Reputational",
    "Project",
    "Environmental"
]);

const Status = Object.freeze({
    IDENTIFIED: "IDENTIFIED",
    ASSESSED: "ASSESSED",
    PLANNED: "TREATMENT_PLANNED",
    IN_PROGRESS: "IN_PROGRESS",
    MONITORING: "MONITORING",
    ACCEPTED: "ACCEPTED",
    CLOSED: "CLOSED"
});

const Response = Object.freeze({
    AVOID: "AVOID",
    MITIGATE: "MITIGATE",
    TRANSFER: "TRANSFER",
    ACCEPT: "ACCEPT"
});

const ALLOWED_TRANSITIONS = new Map([
    [Status.IDENTIFIED, new Set([
        Status.ASSESSED, Status.CLOSED
    ])],
    [Status.ASSESSED, new Set([
        Status.PLANNED, Status.ACCEPTED, Status.CLOSED
    ])],
    [Status.PLANNED, new Set([
        Status.IN_PROGRESS, Status.ACCEPTED, Status.CLOSED
    ])],
    [Status.IN_PROGRESS, new Set([
        Status.MONITORING, Status.PLANNED, Status.CLOSED
    ])],
    [Status.MONITORING, new Set([
        Status.IN_PROGRESS, Status.ACCEPTED, Status.CLOSED
    ])],
    [Status.ACCEPTED, new Set([
        Status.MONITORING, Status.CLOSED
    ])],
    [Status.CLOSED, new Set([
        Status.IDENTIFIED
    ])]
]);

class RiskValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "RiskValidationError";
    }
}

class RiskNotFoundError extends Error {
    constructor(id) {
        super(`Risk ${id} was not found.`);
        this.name = "RiskNotFoundError";
    }
}

function validateScore(value, field) {
    if (!Number.isInteger(value) || value < 1 || value > 5) {
        throw new RiskValidationError(
            `${field} must be an integer between 1 and 5.`
        );
    }
}

function classifyRisk(score) {
    if (!Number.isInteger(score) || score < 1 || score > 25) {
        throw new RiskValidationError("Invalid risk score.");
    }

    if (score >= 20) return "CRITICAL";
    if (score >= 12) return "HIGH";
    if (score >= 6) return "MEDIUM";
    return "LOW";
}

function validateISODate(value, field) {
    if (
        typeof value !== "string" ||
        !/^\d{4}-\d{2}-\d{2}$/.test(value)
    ) {
        throw new RiskValidationError(`${field} must use YYYY-MM-DD.`);
    }

    const parsed = new Date(`${value}T00:00:00.000Z`);
    if (
        Number.isNaN(parsed.getTime()) ||
        parsed.toISOString().slice(0, 10) !== value
    ) {
        throw new RiskValidationError(`${field} is not a valid date.`);
    }

    return value;
}

class Risk {
    constructor(data) {
        if (!data || typeof data !== "object") {
            throw new RiskValidationError("Risk data is required.");
        }

        const required = [
            "id", "title", "description", "category", "owner"
        ];

        for (const field of required) {
            if (
                typeof data[field] !== "string" ||
                !data[field].trim()
            ) {
                throw new RiskValidationError(
                    `${field} must be a non-empty string.`
                );
            }
        }

        if (!Categories.includes(data.category)) {
            throw new RiskValidationError("Invalid risk category.");
        }

        validateScore(data.probability, "Probability");
        validateScore(data.impact, "Impact");

        this.id = data.id.trim();
        this.title = data.title.trim();
        this.description = data.description.trim();
        this.category = data.category;
        this.owner = data.owner.trim();
        this.probability = data.probability;
        this.impact = data.impact;
        this.response = data.response || Response.MITIGATE;
        this.status = Status.IDENTIFIED;
        this.mitigationPlan = data.mitigationPlan || "";
        this.mitigationOwner = data.mitigationOwner || "";
        this.controls = new Set(data.controls || []);
        this.residualProbability = null;
        this.residualImpact = null;
        this.identifiedDate = validateISODate(
            data.identifiedDate,
            "Identified date"
        );
        this.targetDate = data.targetDate
            ? validateISODate(data.targetDate, "Target date")
            : null;
        this.version = 1;
        this.history = [];
        this.validate();
    }

    validate() {
        if (!Object.values(Response).includes(this.response)) {
            throw new RiskValidationError("Invalid response strategy.");
        }

        if (
            this.targetDate &&
            this.targetDate < this.identifiedDate
        ) {
            throw new RiskValidationError(
                "Target date cannot precede identification."
            );
        }
    }

    get inherentScore() {
        return this.probability * this.impact;
    }

    get residualScore() {
        if (this.residualProbability === null) return null;
        return this.residualProbability * this.residualImpact;
    }

    get inherentLevel() {
        return classifyRisk(this.inherentScore);
    }

    get residualLevel() {
        return this.residualScore === null
            ? null
            : classifyRisk(this.residualScore);
    }

    toJSON() {
        return {
            ...this,
            controls: [...this.controls],
            inherentScore: this.inherentScore,
            inherentLevel: this.inherentLevel,
            residualScore: this.residualScore,
            residualLevel: this.residualLevel
        };
    }
}

class RiskRegister extends EventEmitter {
    #risks = new Map();
    #audit = [];
    #listenersEnabled = true;

    constructor(name) {
        super();

        if (!name || !name.trim()) {
            throw new RiskValidationError(
                "Register name is required."
            );
        }

        this.name = name.trim();

        this.on("risk:created", event => {
            this.#recordAudit("CREATE", event.id);
        });

        this.on("risk:updated", event => {
            this.#recordAudit("UPDATE", event.id);
        });

        this.on("risk:transition", event => {
            this.#recordAudit("TRANSITION", event.id);
        });

        this.on("risk:residual", event => {
            this.#recordAudit("RESIDUAL_ASSESSMENT", event.id);
        });
    }

    #recordAudit(action, id) {
        this.#audit.push({
            timestamp: new Date().toISOString(),
            action,
            riskId: id
        });
    }

    #publish(event, data) {
        if (this.#listenersEnabled) {
            this.emit(event, Object.freeze({ ...data }));
        }
    }

    add(data) {
        const risk = new Risk(data);

        if (this.#risks.has(risk.id)) {
            throw new RiskValidationError(
                `Duplicate risk ID: ${risk.id}`
            );
        }

        this.#risks.set(risk.id, risk);
        this.#publish("risk:created", { id: risk.id });

        return risk;
    }

    get(id) {
        const risk = this.#risks.get(id);
        if (!risk) throw new RiskNotFoundError(id);
        return risk;
    }

    update(id, changes) {
        const risk = this.get(id);

        const allowed = new Set([
            "title",
            "description",
            "owner",
            "probability",
            "impact",
            "response",
            "mitigationPlan",
            "mitigationOwner",
            "targetDate"
        ]);

        const unknown = Object.keys(changes).filter(
            key => !allowed.has(key)
        );

        if (unknown.length) {
            throw new RiskValidationError(
                `Unsupported fields: ${unknown.join(", ")}`
            );
        }

        const previous = { ...risk };
        const oldControls = risk.controls;

        try {
            Object.assign(risk, changes);
            risk.validate();

            validateScore(risk.probability, "Probability");
            validateScore(risk.impact, "Impact");

            risk.version++;
        } catch (error) {
            Object.assign(risk, previous);
            risk.controls = oldControls;
            throw error;
        }

        this.#publish("risk:updated", { id });
        return risk;
    }

    transition(id, nextStatus, justification) {
        const risk = this.get(id);
        const allowed = ALLOWED_TRANSITIONS.get(risk.status);

        if (!allowed || !allowed.has(nextStatus)) {
            throw new RiskValidationError(
                `Invalid transition: ${risk.status} -> ${nextStatus}`
            );
        }

        if (
            [Status.ACCEPTED, Status.CLOSED].includes(nextStatus) &&
            (!justification || !justification.trim())
        ) {
            throw new RiskValidationError(
                "A justification is required."
            );
        }

        const previous = risk.status;
        risk.status = nextStatus;
        risk.version++;

        risk.history.push({
            previous,
            current: nextStatus,
            justification: justification || "",
            timestamp: new Date().toISOString()
        });

        this.#publish("risk:transition", {
            id,
            previous,
            current: nextStatus
        });

        return risk;
    }

    assessResidual(id, probability, impact) {
        const risk = this.get(id);

        validateScore(probability, "Residual probability");
        validateScore(impact, "Residual impact");

        if (risk.status === Status.CLOSED) {
            throw new RiskValidationError(
                "Closed risks cannot be reassessed."
            );
        }

        risk.residualProbability = probability;
        risk.residualImpact = impact;
        risk.version++;

        this.#publish("risk:residual", {
            id,
            score: risk.residualScore
        });

        return risk;
    }

    search(filters = {}) {
        return [...this.#risks.values()]
            .filter(risk => {
                if (
                    filters.category &&
                    risk.category !== filters.category
                ) return false;

                if (
                    filters.level &&
                    risk.inherentLevel !== filters.level
                ) return false;

                if (
                    filters.status &&
                    risk.status !== filters.status
                ) return false;

                if (
                    filters.owner &&
                    risk.owner.toLowerCase() !==
                    filters.owner.toLowerCase()
                ) return false;

                return true;
            })
            .sort((a, b) =>
                b.inherentScore - a.inherentScore
            );
    }

    evaluateRisk(id) {
        const risk = this.get(id);
        const blockers = [];

        if (risk.inherentScore >= 20) {
            blockers.push("Critical inherent exposure requires escalation.");
        }

        if (
            risk.residualScore !== null &&
            risk.residualScore >= 20
        ) {
            blockers.push("Critical residual exposure requires escalation.");
        }

        if (
            risk.response === Response.MITIGATE &&
            !risk.mitigationPlan.trim()
        ) {
            blockers.push("Mitigation plan is missing.");
        }

        if (
            risk.response === Response.ACCEPT &&
            risk.status !== Status.ACCEPTED
        ) {
            blockers.push("Formal risk acceptance is required.");
        }

        return {
            riskId: id,
            eligibleForMonitoring: blockers.length === 0,
            blockers
        };
    }

    report() {
        const risks = [...this.#risks.values()];
        const distribution = {
            LOW: 0,
            MEDIUM: 0,
            HIGH: 0,
            CRITICAL: 0
        };

        for (const risk of risks) {
            distribution[risk.inherentLevel]++;
        }

        return {
            register: this.name,
            generatedAt: new Date().toISOString(),
            total: risks.length,
            distribution,
            open: risks.filter(
                r => r.status !== Status.CLOSED
            ).length,
            averageScore: risks.length
                ? Number((
                    risks.reduce(
                        (sum, r) => sum + r.inherentScore, 0
                    ) / risks.length
                ).toFixed(2))
                : 0,
            risks: risks
                .sort((a, b) => b.inherentScore - a.inherentScore)
                .map(r => r.toJSON()),
            audit: [...this.#audit]
        };
    }

    async save(filePath) {
        const data = JSON.stringify(this.report(), null, 2);
        const temporary = `${filePath}.tmp`;

        try {
            await fs.writeFile(temporary, data, {
                encoding: "utf8",
                mode: 0o600,
                flag: "w"
            });

            await fs.rename(temporary, filePath);
        } catch (error) {
            await fs.rm(temporary, { force: true }).catch(() => {});
            throw new Error(`Persistence failed: ${error.message}`);
        }
    }
}

async function main() {
    const register = new RiskRegister(
        "Enterprise Infrastructure Risk Register"
    );

    register.on("risk:created", ({ id }) => {
        console.log(`New risk registered: ${id}`);
    });

    register.on("risk:residual", ({ id, score }) => {
        console.log(`Residual assessment: ${id} = ${score}/25`);
    });

    register.add({
        id: "R-001",
        title: "Ransomware attack",
        description: "Malware may disrupt business-critical services.",
        category: "Cybersecurity",
        owner: "Chief Information Security Officer",
        probability: 4,
        impact: 5,
        response: Response.MITIGATE,
        mitigationPlan: "EDR, immutable backups and incident exercises.",
        mitigationOwner: "Security Operations",
        identifiedDate: "2026-11-25",
        targetDate: "2026-12-25",
        controls: ["EDR", "MFA", "Backup"]
    });

    register.add({
        id: "R-002",
        title: "Supplier delivery failure",
        description: "Critical supplier may fail to meet delivery dates.",
        category: "Operational",
        owner: "Procurement Manager",
        probability: 3,
        impact: 4,
        response: Response.MITIGATE,
        mitigationPlan: "Qualify alternative suppliers.",
        identifiedDate: "2026-11-25",
        targetDate: "2027-01-15"
    });

    register.add({
        id: "R-003",
        title: "Regulatory non-compliance",
        description: "New regulatory requirements may not be implemented.",
        category: "Compliance",
        owner: "Compliance Officer",
        probability: 3,
        impact: 5,
        response: Response.MITIGATE,
        mitigationPlan: "Maintain a regulatory obligations register.",
        identifiedDate: "2026-11-25"
    });

    register.assessResidual("R-001", 2, 3);

    register.transition(
        "R-001",
        Status.ASSESSED,
        "Initial risk assessment completed."
    );

    register.transition(
        "R-001",
        Status.PLANNED,
        "Treatment strategy approved."
    );

    register.transition(
        "R-001",
        Status.IN_PROGRESS,
        "Security controls implementation initiated."
    );

    console.log("\nPRIORITY REGISTER");

    for (const risk of register.search()) {
        console.log(
            `${risk.id} | ${risk.title} | ` +
            `${risk.inherentScore}/25 | ${risk.inherentLevel}`
        );
    }

    console.log("\nPOLICY EVALUATION");
    console.log(register.evaluateRisk("R-001"));

    console.log("\nAGGREGATE REPORT");
    console.log(JSON.stringify(register.report(), null, 2));

    await register.save("risk-register.json");

    console.log("\nRisk register saved successfully.");

    // Demonstrate invalid input handling.
    try {
        register.add({
            id: "R-INVALID",
            title: "Invalid probability",
            description: "Validation demonstration.",
            category: "Operational",
            owner: "Operations Manager",
            probability: 8,
            impact: 3,
            identifiedDate: "2026-11-25"
        });
    } catch (error) {
        console.log(`Expected validation error: ${error.message}`);
    }
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
