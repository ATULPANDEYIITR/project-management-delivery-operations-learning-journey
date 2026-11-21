"use strict";

/*
 * Risk Identification and Event-Driven Assessment Engine
 *
 * Node.js 18+
 * No external dependencies.
 *
 * Implements:
 * - Event-driven risk discovery
 * - Risk taxonomy
 * - Structured evidence
 * - Duplicate detection
 * - Risk scoring
 * - Control assessment
 * - Asynchronous validation
 * - Policy-based prioritization
 * - JSON reporting
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const crypto = require("node:crypto");

const Category = Object.freeze({
    STRATEGIC: "strategic",
    OPERATIONAL: "operational",
    FINANCIAL: "financial",
    TECHNOLOGICAL: "technological",
    CYBERSECURITY: "cybersecurity",
    COMPLIANCE: "compliance",
    REPUTATIONAL: "reputational",
    ENVIRONMENTAL: "environmental",
    HUMAN_RESOURCE: "human_resource",
    THIRD_PARTY: "third_party"
});

const Source = Object.freeze({
    WORKSHOP: "workshop",
    AUDIT: "audit",
    INCIDENT: "incident",
    INTERVIEW: "interview",
    HISTORICAL_DATA: "historical_data",
    TECHNICAL_ANALYSIS: "technical_analysis",
    EXTERNAL_ENVIRONMENT: "external_environment"
});

const Status = Object.freeze({
    IDENTIFIED: "identified",
    ASSESSED: "assessed",
    UNDER_REVIEW: "under_review",
    MITIGATED: "mitigated",
    ACCEPTED: "accepted",
    CLOSED: "closed"
});

const LEVELS = Object.freeze({
    LOW: "low",
    MODERATE: "moderate",
    HIGH: "high",
    CRITICAL: "critical"
});

class RiskError extends Error {
    constructor(message, code = "RISK_ERROR") {
        super(message);
        this.name = "RiskError";
        this.code = code;
    }
}

function requireText(value, field) {
    if (typeof value !== "string" || !value.trim()) {
        throw new RiskError(`${field} must be a non-empty string.`);
    }

    return value.trim();
}

function validateScale(value, field) {
    if (!Number.isInteger(value) || value < 1 || value > 5) {
        throw new RiskError(`${field} must be an integer from 1 to 5.`);
    }
}

function classify(score) {
    if (score >= 75) return LEVELS.CRITICAL;
    if (score >= 40) return LEVELS.HIGH;
    if (score >= 15) return LEVELS.MODERATE;
    return LEVELS.LOW;
}

function calculateScore(probability, impact, detectability) {
    validateScale(probability, "Probability");
    validateScale(impact, "Impact");
    validateScale(detectability, "Detectability");

    return probability * impact * detectability;
}

class Risk {
    constructor({
        title,
        description,
        category,
        source,
        owner,
        context,
        probability,
        impact,
        detectability
    }) {
        this.id = crypto.randomUUID();

        this.title = requireText(title, "Title");
        this.description = requireText(description, "Description");
        this.owner = requireText(owner, "Owner");
        this.context = requireText(context, "Context");

        if (!Object.values(Category).includes(category)) {
            throw new RiskError("Unsupported risk category.");
        }

        if (!Object.values(Source).includes(source)) {
            throw new RiskError("Unsupported identification source.");
        }

        this.category = category;
        this.source = source;

        this.probability = probability;
        this.impact = impact;
        this.detectability = detectability;

        this.inherentScore = calculateScore(
            probability,
            impact,
            detectability
        );

        this.status = Status.IDENTIFIED;
        this.evidence = new Map();
        this.controls = new Map();
        this.createdAt = new Date().toISOString();
        this.updatedAt = this.createdAt;
        this.revision = 1;
    }

    get inherentLevel() {
        return classify(this.inherentScore);
    }

    get controlEffectiveness() {
        let remaining = 1;

        for (const control of this.controls.values()) {
            remaining *= 1 - control.effectiveness;
        }

        return 1 - remaining;
    }

    get residualScore() {
        return this.inherentScore * (1 - this.controlEffectiveness);
    }

    get residualLevel() {
        return classify(this.residualScore);
    }

    addEvidence({ description, source, reference }) {
        description = requireText(description, "Evidence description");
        reference = requireText(reference, "Evidence reference");

        if (!Object.values(Source).includes(source)) {
            throw new RiskError("Invalid evidence source.");
        }

        if (this.evidence.has(reference)) {
            throw new RiskError("Duplicate evidence reference.");
        }

        this.evidence.set(reference, {
            description,
            source,
            reference,
            collectedAt: new Date().toISOString()
        });

        this.touch();
    }

    addControl({ id, description, effectiveness, preventive = true }) {
        id = requireText(id, "Control ID");
        description = requireText(description, "Control description");

        if (
            typeof effectiveness !== "number" ||
            !Number.isFinite(effectiveness) ||
            effectiveness < 0 ||
            effectiveness > 1
        ) {
            throw new RiskError(
                "Control effectiveness must be between 0 and 1."
            );
        }

        if (this.controls.has(id)) {
            throw new RiskError("Duplicate control identifier.");
        }

        this.controls.set(id, {
            id,
            description,
            effectiveness,
            preventive: Boolean(preventive)
        });

        this.touch();
    }

    reassess({ probability, impact, detectability }) {
        const score = calculateScore(
            probability,
            impact,
            detectability
        );

        this.probability = probability;
        this.impact = impact;
        this.detectability = detectability;
        this.inherentScore = score;

        this.status = Status.ASSESSED;
        this.touch();
    }

    transition(nextStatus) {
        const transitions = {
            identified: ["assessed", "under_review", "closed"],
            assessed: [
                "under_review",
                "mitigated",
                "accepted",
                "closed"
            ],
            under_review: [
                "assessed",
                "mitigated",
                "accepted",
                "closed"
            ],
            mitigated: ["under_review", "closed"],
            accepted: ["under_review", "closed"],
            closed: []
        };

        if (!Object.values(Status).includes(nextStatus)) {
            throw new RiskError("Unknown risk status.");
        }

        if (!transitions[this.status].includes(nextStatus)) {
            throw new RiskError(
                `Invalid transition from ${this.status} to ${nextStatus}.`
            );
        }

        if (nextStatus === Status.MITIGATED && this.controls.size === 0) {
            throw new RiskError(
                "A risk cannot be mitigated without recorded controls."
            );
        }

        this.status = nextStatus;
        this.touch();
    }

    touch() {
        this.updatedAt = new Date().toISOString();
        this.revision++;
    }

    toJSON() {
        return {
            id: this.id,
            title: this.title,
            description: this.description,
            category: this.category,
            source: this.source,
            owner: this.owner,
            context: this.context,
            probability: this.probability,
            impact: this.impact,
            detectability: this.detectability,
            inherentScore: this.inherentScore,
            inherentLevel: this.inherentLevel,
            controlEffectiveness: Number(
                this.controlEffectiveness.toFixed(3)
            ),
            residualScore: Number(this.residualScore.toFixed(2)),
            residualLevel: this.residualLevel,
            status: this.status,
            evidence: Array.from(this.evidence.values()),
            controls: Array.from(this.controls.values()),
            revision: this.revision,
            createdAt: this.createdAt,
            updatedAt: this.updatedAt
        };
    }
}

class RiskIdentificationEngine extends EventEmitter {
    constructor({ organization, maximumRisks = 10000 }) {
        super();

        this.organization = requireText(
            organization,
            "Organization"
        );

        if (!Number.isInteger(maximumRisks) || maximumRisks < 1) {
            throw new RiskError("Invalid risk capacity.");
        }

        this.maximumRisks = maximumRisks;
        this.risks = new Map();
        this.fingerprints = new Map();
        this.sequence = 0;
    }

    fingerprint(risk) {
        return [
            risk.title.toLowerCase(),
            risk.context.toLowerCase(),
            risk.category
        ].join("|");
    }

    identify(input) {
        if (this.risks.size >= this.maximumRisks) {
            throw new RiskError("Risk register capacity exceeded.");
        }

        const risk = new Risk(input);
        const fingerprint = this.fingerprint(risk);

        if (this.fingerprints.has(fingerprint)) {
            throw new RiskError(
                "Potential duplicate risk detected.",
                "DUPLICATE_RISK"
            );
        }

        this.risks.set(risk.id, risk);
        this.fingerprints.set(fingerprint, risk.id);

        this.sequence++;

        this.emit("risk:identified", {
            riskId: risk.id,
            sequence: this.sequence,
            timestamp: new Date().toISOString()
        });

        return risk;
    }

    get(id) {
        const risk = this.risks.get(id);

        if (!risk) {
            throw new RiskError(`Risk ${id} does not exist.`);
        }

        return risk;
    }

    assess(id, assessment) {
        const risk = this.get(id);
        const oldScore = risk.inherentScore;

        risk.reassess(assessment);

        this.emit("risk:assessed", {
            riskId: id,
            previousScore: oldScore,
            currentScore: risk.inherentScore,
            level: risk.inherentLevel
        });

        return risk;
    }

    addEvidence(id, evidence) {
        const risk = this.get(id);
        risk.addEvidence(evidence);

        this.emit("risk:evidence-added", {
            riskId: id,
            reference: evidence.reference
        });
    }

    addControl(id, control) {
        const risk = this.get(id);
        risk.addControl(control);

        this.emit("risk:control-added", {
            riskId: id,
            controlId: control.id
        });
    }

    transition(id, status) {
        const risk = this.get(id);
        const previousStatus = risk.status;

        risk.transition(status);

        this.emit("risk:status-changed", {
            riskId: id,
            previousStatus,
            newStatus: status
        });
    }

    async validateRisk(id, externalValidator) {
        const risk = this.get(id);

        if (typeof externalValidator !== "function") {
            throw new RiskError("Validator must be a function.");
        }

        const result = await externalValidator(risk.toJSON());

        if (!result || typeof result.valid !== "boolean") {
            throw new RiskError("Validator returned an invalid response.");
        }

        this.emit("risk:validated", {
            riskId: id,
            valid: result.valid,
            issues: result.issues || []
        });

        return result;
    }

    query({
        category,
        status,
        minimumScore = 0,
        owner
    } = {}) {
        if (!Number.isFinite(minimumScore) || minimumScore < 0) {
            throw new RiskError("Minimum score must be non-negative.");
        }

        return Array.from(this.risks.values())
            .filter(risk =>
                (!category || risk.category === category) &&
                (!status || risk.status === status) &&
                (!owner || risk.owner === owner) &&
                risk.inherentScore >= minimumScore
            )
            .sort((a, b) => b.inherentScore - a.inherentScore);
    }

    categoryReport() {
        const report = Object.fromEntries(
            Object.values(Category).map(category => [category, 0])
        );

        for (const risk of this.risks.values()) {
            report[risk.category]++;
        }

        return report;
    }

    dashboard() {
        const risks = Array.from(this.risks.values());

        return {
            organization: this.organization,
            generatedAt: new Date().toISOString(),
            totalRisks: risks.length,
            criticalRisks: risks.filter(
                risk => risk.inherentLevel === LEVELS.CRITICAL
            ).length,
            highRisks: risks.filter(
                risk => risk.inherentLevel === LEVELS.HIGH
            ).length,
            openRisks: risks.filter(
                risk => risk.status !== Status.CLOSED
            ).length,
            categories: this.categoryReport(),
            priorities: this.query().map(risk => risk.toJSON())
        };
    }

    async exportReport(filename) {
        const report = JSON.stringify(this.dashboard(), null, 2);

        // Exclusive creation prevents accidental replacement of reports.
        await fs.writeFile(filename, report, {
            encoding: "utf8",
            flag: "wx",
            mode: 0o600
        });
    }
}

async function main() {
    const engine = new RiskIdentificationEngine({
        organization: "Enterprise Digital Operations"
    });

    const auditEvents = [];

    engine.on("risk:identified", event => {
        auditEvents.push({
            type: "IDENTIFIED",
            ...event
        });
    });

    engine.on("risk:assessed", event => {
        auditEvents.push({
            type: "ASSESSED",
            ...event
        });
    });

    engine.on("risk:status-changed", event => {
        auditEvents.push({
            type: "STATUS_CHANGED",
            ...event
        });
    });

    const cyberRisk = engine.identify({
        title: "Unauthorized production access",
        description:
            "Compromised credentials may expose sensitive systems.",
        category: Category.CYBERSECURITY,
        source: Source.TECHNICAL_ANALYSIS,
        owner: "Security Operations Manager",
        context: "Production infrastructure",
        probability: 4,
        impact: 5,
        detectability: 4
    });

    engine.addEvidence(cyberRisk.id, {
        description: "Privileged accounts lack consistent MFA.",
        source: Source.AUDIT,
        reference: "AUDIT-2026-014"
    });

    engine.addControl(cyberRisk.id, {
        id: "MFA-001",
        description: "Enforce phishing-resistant MFA.",
        effectiveness: 0.55
    });

    engine.addControl(cyberRisk.id, {
        id: "MON-001",
        description: "Monitor privileged account activity.",
        effectiveness: 0.30
    });

    engine.assess(cyberRisk.id, {
        probability: 4,
        impact: 5,
        detectability: 4
    });

    engine.transition(cyberRisk.id, Status.UNDER_REVIEW);

    const supplierRisk = engine.identify({
        title: "Critical supplier service interruption",
        description:
            "Supplier downtime may interrupt business operations.",
        category: Category.THIRD_PARTY,
        source: Source.HISTORICAL_DATA,
        owner: "Vendor Management Lead",
        context: "Cloud service dependencies",
        probability: 3,
        impact: 4,
        detectability: 3
    });

    engine.addEvidence(supplierRisk.id, {
        description: "Previous outages exceeded recovery targets.",
        source: Source.INCIDENT,
        reference: "INCIDENT-2026-022"
    });

    // External validation is asynchronous and failure-aware.
    const validation = await engine.validateRisk(
        cyberRisk.id,
        async risk => ({
            valid:
                risk.title.length >= 5 &&
                risk.owner.length >= 3 &&
                risk.evidence.length > 0,
            issues: []
        })
    );

    console.log("External validation:", validation);
    console.log("\nRisk dashboard:");
    console.log(JSON.stringify(engine.dashboard(), null, 2));

    console.log("\nAudit events:", auditEvents.length);

    // Duplicate detection test.
    try {
        engine.identify({
            title: "Unauthorized production access",
            description: "Duplicate entry.",
            category: Category.CYBERSECURITY,
            source: Source.AUDIT,
            owner: "Security Manager",
            context: "Production infrastructure",
            probability: 2,
            impact: 2,
            detectability: 2
        });
    } catch (error) {
        console.log("Expected duplicate rejection:", error.message);
    }

    // Validation test.
    try {
        calculateScore(6, 3, 2);
    } catch (error) {
        console.log("Expected scale validation:", error.message);
    }

    console.log("\nHigh-priority risks:");

    for (const risk of engine.query({ minimumScore: 40 })) {
        console.log(
            `${risk.title}: ${risk.inherentScore} (${risk.inherentLevel})`
        );
    }

    console.log("\nRisk identification completed.");
}

main().catch(error => {
    console.error("Risk engine failure:", error.message);
    process.exitCode = 1;
});
