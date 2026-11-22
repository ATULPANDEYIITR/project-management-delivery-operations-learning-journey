"use strict";

/*
 * Risk Analysis Engine
 *
 * Event-driven organizational risk management.
 *
 * Features:
 * - Probability and impact modeling
 * - Expected monetary loss
 * - Inherent and residual exposure
 * - Risk treatment policies
 * - Asynchronous assessment processing
 * - EventEmitter notifications
 * - Optimistic version checking
 * - Portfolio reporting
 * - Simulation of uncertain losses
 *
 * Runtime: Node.js 18+
 */

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");


class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}

class ConcurrencyError extends Error {
    constructor(message) {
        super(message);
        this.name = "ConcurrencyError";
    }
}

class RiskNotFoundError extends Error {
    constructor(id) {
        super(`Risk ${id} does not exist.`);
        this.name = "RiskNotFoundError";
    }
}


const RiskCategory = Object.freeze({
    STRATEGIC: "STRATEGIC",
    FINANCIAL: "FINANCIAL",
    OPERATIONAL: "OPERATIONAL",
    TECHNOLOGY: "TECHNOLOGY",
    SECURITY: "SECURITY",
    COMPLIANCE: "COMPLIANCE",
    REPUTATIONAL: "REPUTATIONAL"
});

const RiskStatus = Object.freeze({
    IDENTIFIED: "IDENTIFIED",
    ASSESSED: "ASSESSED",
    MITIGATING: "MITIGATING",
    ACCEPTED: "ACCEPTED",
    CLOSED: "CLOSED"
});

const Treatment = Object.freeze({
    ACCEPT: "ACCEPT",
    MITIGATE: "MITIGATE",
    TRANSFER: "TRANSFER",
    AVOID: "AVOID"
});


function validateProbability(value, name = "Probability") {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0 ||
        value > 1
    ) {
        throw new ValidationError(
            `${name} must be a finite number between 0 and 1.`
        );
    }
}

function validateImpact(value) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0
    ) {
        throw new ValidationError(
            "Impact must be a finite, non-negative monetary value."
        );
    }
}


class RiskControl {
    constructor({
        name,
        probabilityReduction,
        impactReduction
    }) {
        if (!name || !name.trim()) {
            throw new ValidationError("Control name is required.");
        }

        validateProbability(
            probabilityReduction,
            "Probability reduction"
        );

        validateProbability(
            impactReduction,
            "Impact reduction"
        );

        this.name = name.trim();
        this.probabilityReduction = probabilityReduction;
        this.impactReduction = impactReduction;

        Object.freeze(this);
    }
}


class Risk {
    constructor({
        id,
        title,
        description,
        category,
        probability,
        impact,
        owner
    }) {
        if (!id || !title || !owner) {
            throw new ValidationError(
                "Risk ID, title, and owner are required."
            );
        }

        if (!Object.values(RiskCategory).includes(category)) {
            throw new ValidationError("Unknown risk category.");
        }

        validateProbability(probability);
        validateImpact(impact);

        this.id = id;
        this.title = title;
        this.description = description || "";
        this.category = category;
        this.probability = probability;
        this.impact = impact;
        this.owner = owner;

        this.status = RiskStatus.IDENTIFIED;
        this.treatment = null;
        this.controls = [];
        this.version = 1;
        this.updatedAt = new Date().toISOString();
    }

    get inherentExposure() {
        return this.probability * this.impact;
    }

    get residualProbability() {
        return this.controls.reduce(
            (remaining, control) =>
                remaining * (1 - control.probabilityReduction),
            this.probability
        );
    }

    get residualImpact() {
        return this.controls.reduce(
            (remaining, control) =>
                remaining * (1 - control.impactReduction),
            this.impact
        );
    }

    get residualExposure() {
        return this.residualProbability * this.residualImpact;
    }

    get riskScore() {
        return this.probability * this.impact;
    }

    get level() {
        const score = this.residualExposure;

        if (score >= 100000) return "CRITICAL";
        if (score >= 25000) return "HIGH";
        if (score >= 5000) return "MODERATE";

        return "LOW";
    }

    addControl(control) {
        if (!(control instanceof RiskControl)) {
            throw new ValidationError("Invalid control object.");
        }

        if (
            this.controls.some(
                existing => existing.name === control.name
            )
        ) {
            throw new ValidationError(
                "Duplicate control name."
            );
        }

        this.controls.push(control);
        this.status = RiskStatus.MITIGATING;
        this.version++;
        this.updatedAt = new Date().toISOString();
    }

    applyTreatment(treatment) {
        if (!Object.values(Treatment).includes(treatment)) {
            throw new ValidationError("Unknown treatment strategy.");
        }

        if (
            treatment === Treatment.ACCEPT &&
            this.residualExposure > 100000
        ) {
            throw new ValidationError(
                "Critical exposure requires authorized escalation."
            );
        }

        this.treatment = treatment;

        const statusMap = {
            [Treatment.ACCEPT]: RiskStatus.ACCEPTED,
            [Treatment.MITIGATE]: RiskStatus.MITIGATING,
            [Treatment.TRANSFER]: RiskStatus.ASSESSED,
            [Treatment.AVOID]: RiskStatus.CLOSED
        };

        this.status = statusMap[treatment];
        this.version++;
        this.updatedAt = new Date().toISOString();
    }

    snapshot() {
        return {
            id: this.id,
            title: this.title,
            category: this.category,
            probability: this.probability,
            impact: this.impact,
            inherentExposure: this.inherentExposure,
            residualProbability: this.residualProbability,
            residualImpact: this.residualImpact,
            residualExposure: this.residualExposure,
            level: this.level,
            status: this.status,
            treatment: this.treatment,
            version: this.version
        };
    }
}


class RiskRepository extends EventEmitter {
    #records = new Map();

    add(risk) {
        if (!(risk instanceof Risk)) {
            throw new ValidationError("Expected a Risk instance.");
        }

        if (this.#records.has(risk.id)) {
            throw new ValidationError(
                `Duplicate risk ID: ${risk.id}`
            );
        }

        this.#records.set(risk.id, risk);

        this.emit("risk:created", risk.snapshot());
    }

    get(id) {
        const risk = this.#records.get(id);

        if (!risk) {
            throw new RiskNotFoundError(id);
        }

        return risk;
    }

    list() {
        return [...this.#records.values()];
    }

    async assess(id, assessment, expectedVersion) {
        const risk = this.get(id);

        // Optimistic concurrency prevents silent overwrites.
        if (risk.version !== expectedVersion) {
            throw new ConcurrencyError(
                `Expected version ${expectedVersion}; ` +
                `current version is ${risk.version}.`
            );
        }

        const { probability, impact } = assessment;

        validateProbability(probability);
        validateImpact(impact);

        // Yield to the event loop before committing the mutation.
        await new Promise(resolve => setImmediate(resolve));

        if (risk.version !== expectedVersion) {
            throw new ConcurrencyError(
                "Risk changed during assessment."
            );
        }

        risk.probability = probability;
        risk.impact = impact;
        risk.status = RiskStatus.ASSESSED;
        risk.version++;
        risk.updatedAt = new Date().toISOString();

        const result = risk.snapshot();

        this.emit("risk:assessed", result);

        return result;
    }

    prioritized() {
        return this.list().sort(
            (a, b) =>
                b.residualExposure - a.residualExposure
        );
    }

    portfolio() {
        const records = this.list();

        return records.reduce(
            (result, risk) => {
                result.count++;
                result.inherentExposure += risk.inherentExposure;
                result.residualExposure += risk.residualExposure;

                result.levels[risk.level] =
                    (result.levels[risk.level] || 0) + 1;

                return result;
            },
            {
                count: 0,
                inherentExposure: 0,
                residualExposure: 0,
                levels: {}
            }
        );
    }
}


class RiskPolicy {
    constructor({
        maximumAcceptableExposure = 25000,
        criticalProbability = 0.8
    } = {}) {
        validateImpact(maximumAcceptableExposure);
        validateProbability(criticalProbability);

        this.maximumAcceptableExposure =
            maximumAcceptableExposure;

        this.criticalProbability = criticalProbability;
    }

    evaluate(risk) {
        if (risk.residualExposure >
            this.maximumAcceptableExposure) {
            return {
                decision: Treatment.MITIGATE,
                reason: "Exposure exceeds the acceptance threshold."
            };
        }

        if (risk.residualProbability >=
            this.criticalProbability) {
            return {
                decision: Treatment.MITIGATE,
                reason: "Residual probability is too high."
            };
        }

        return {
            decision: Treatment.ACCEPT,
            reason: "Risk satisfies configured acceptance criteria."
        };
    }
}


class RiskSimulation {
    static run(risks, iterations = 10000, seed = 12345) {
        if (!Number.isInteger(iterations) || iterations <= 0) {
            throw new ValidationError(
                "Iterations must be a positive integer."
            );
        }

        // Deterministic pseudo-random generator for repeatable tests.
        let state = seed >>> 0;

        function random() {
            state = (1664525 * state + 1013904223) >>> 0;
            return state / 4294967296;
        }

        const losses = new Float64Array(iterations);

        for (let i = 0; i < iterations; i++) {
            let total = 0;

            for (const risk of risks) {
                if (random() < risk.residualProbability) {
                    total += risk.residualImpact;
                }
            }

            losses[i] = total;
        }

        losses.sort();

        const mean =
            losses.reduce((sum, value) => sum + value, 0) /
            iterations;

        const percentile = p =>
            losses[Math.floor((iterations - 1) * p)];

        return {
            iterations,
            expectedSimulatedLoss: mean,
            medianLoss: percentile(0.50),
            p95Loss: percentile(0.95),
            p99Loss: percentile(0.99),
            maximumLoss: losses[iterations - 1]
        };
    }
}


async function main() {
    const repository = new RiskRepository();

    repository.on("risk:created", event => {
        console.log(`[EVENT] Risk created: ${event.id}`);
    });

    repository.on("risk:assessed", event => {
        console.log(
            `[EVENT] Risk assessed: ${event.id}, ` +
            `residual exposure: ${event.residualExposure.toFixed(2)}`
        );
    });

    const securityRisk = new Risk({
        id: crypto.randomUUID(),
        title: "Unauthorized System Access",
        description: "Unauthorized access to sensitive systems.",
        category: RiskCategory.SECURITY,
        probability: 0.70,
        impact: 500000,
        owner: "Security Team"
    });

    const financialRisk = new Risk({
        id: crypto.randomUUID(),
        title: "Budget Overrun",
        description: "Unexpected project expenditure.",
        category: RiskCategory.FINANCIAL,
        probability: 0.40,
        impact: 120000,
        owner: "Finance Team"
    });

    const operationalRisk = new Risk({
        id: crypto.randomUUID(),
        title: "Infrastructure Downtime",
        description: "Critical service outage.",
        category: RiskCategory.OPERATIONAL,
        probability: 0.25,
        impact: 80000,
        owner: "Infrastructure Team"
    });

    repository.add(securityRisk);
    repository.add(financialRisk);
    repository.add(operationalRisk);

    securityRisk.addControl(
        new RiskControl({
            name: "Multi-factor Authentication",
            probabilityReduction: 0.40,
            impactReduction: 0.10
        })
    );

    securityRisk.addControl(
        new RiskControl({
            name: "Security Monitoring",
            probabilityReduction: 0.15,
            impactReduction: 0.25
        })
    );

    financialRisk.addControl(
        new RiskControl({
            name: "Budget Monitoring",
            probabilityReduction: 0.25,
            impactReduction: 0.20
        })
    );

    const policy = new RiskPolicy({
        maximumAcceptableExposure: 25000,
        criticalProbability: 0.8
    });

    console.log("\nRISK TREATMENT EVALUATION");

    for (const risk of repository.list()) {
        const result = policy.evaluate(risk);

        console.log({
            title: risk.title,
            inherentExposure: risk.inherentExposure,
            residualExposure: risk.residualExposure,
            decision: result.decision,
            reason: result.reason
        });
    }

    const initialVersion = operationalRisk.version;

    await repository.assess(
        operationalRisk.id,
        {
            probability: 0.30,
            impact: 90000
        },
        initialVersion
    );

    console.log("\nPRIORITIZED RISKS");

    for (const risk of repository.prioritized()) {
        console.log(risk.snapshot());
    }

    console.log("\nPORTFOLIO");

    console.log(repository.portfolio());

    console.log("\nMONTE CARLO SIMULATION");

    console.log(
        RiskSimulation.run(
            repository.list(),
            10000
        )
    );

    console.log("\nCONCURRENCY VALIDATION");

    try {
        await repository.assess(
            operationalRisk.id,
            {
                probability: 0.2,
                impact: 50000
            },
            initialVersion
        );
    } catch (error) {
        console.log(`${error.name}: ${error.message}`);
    }
}


main().catch(error => {
    console.error("Risk analysis failed:", error.message);
    process.exitCode = 1;
});
