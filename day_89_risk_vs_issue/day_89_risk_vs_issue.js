"use strict";

const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");
const fs = require("node:fs/promises");

const RiskStatus = Object.freeze({
    IDENTIFIED: "IDENTIFIED",
    ASSESSED: "ASSESSED",
    MITIGATING: "MITIGATING",
    ACCEPTED: "ACCEPTED",
    CLOSED: "CLOSED"
});

const IssueStatus = Object.freeze({
    OPEN: "OPEN",
    IN_PROGRESS: "IN_PROGRESS",
    BLOCKED: "BLOCKED",
    RESOLVED: "RESOLVED",
    CLOSED: "CLOSED"
});

const Severity = Object.freeze({
    LOW: "LOW",
    MEDIUM: "MEDIUM",
    HIGH: "HIGH",
    CRITICAL: "CRITICAL"
});

const Priority = Object.freeze({
    LOW: "LOW",
    MEDIUM: "MEDIUM",
    HIGH: "HIGH",
    URGENT: "URGENT"
});

class DomainError extends Error {
    constructor(message) {
        super(message);
        this.name = "DomainError";
    }
}

function validateText(value, field) {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new DomainError(`${field} must be a non-empty string.`);
    }
}

function calculateSeverity(probability, impact) {
    const exposure = probability * impact;

    if (exposure >= 20) return Severity.CRITICAL;
    if (exposure >= 12) return Severity.HIGH;
    if (exposure >= 6) return Severity.MEDIUM;
    return Severity.LOW;
}

function severityToPriority(severity) {
    const mapping = {
        [Severity.LOW]: Priority.LOW,
        [Severity.MEDIUM]: Priority.MEDIUM,
        [Severity.HIGH]: Priority.HIGH,
        [Severity.CRITICAL]: Priority.URGENT
    };

    return mapping[severity];
}

class Risk {
    constructor({
        title,
        description,
        probability,
        impact,
        owner,
        category = "Operational",
        mitigation = "",
        contingency = ""
    }) {
        validateText(title, "Risk title");
        validateText(description, "Risk description");
        validateText(owner, "Risk owner");
        validateText(category, "Risk category");

        if (!Number.isInteger(probability) ||
            probability < 1 || probability > 5) {
            throw new DomainError("Probability must be an integer from 1 to 5.");
        }

        if (!Number.isInteger(impact) || impact < 1 || impact > 5) {
            throw new DomainError("Impact must be an integer from 1 to 5.");
        }

        this.id = crypto.randomUUID();
        this.title = title;
        this.description = description;
        this.probability = probability;
        this.impact = impact;
        this.owner = owner;
        this.category = category;
        this.mitigation = mitigation;
        this.contingency = contingency;
        this.status = RiskStatus.IDENTIFIED;
        this.createdAt = new Date().toISOString();
    }

    get exposure() {
        return this.probability * this.impact;
    }

    get severity() {
        return calculateSeverity(this.probability, this.impact);
    }

    assess() {
        if (this.status === RiskStatus.CLOSED) {
            throw new DomainError("Closed risks cannot be assessed.");
        }

        this.status = RiskStatus.ASSESSED;
    }

    startMitigation() {
        if (![RiskStatus.IDENTIFIED, RiskStatus.ASSESSED]
            .includes(this.status)) {
            throw new DomainError("Invalid mitigation transition.");
        }

        validateText(this.mitigation, "Mitigation plan");
        this.status = RiskStatus.MITIGATING;
    }

    accept() {
        if (this.status === RiskStatus.CLOSED) {
            throw new DomainError("Closed risks cannot be accepted.");
        }

        this.status = RiskStatus.ACCEPTED;
    }

    close() {
        if (![RiskStatus.MITIGATING, RiskStatus.ACCEPTED]
            .includes(this.status)) {
            throw new DomainError(
                "Risk must be mitigated or accepted before closure."
            );
        }

        this.status = RiskStatus.CLOSED;
    }
}

class Issue {
    constructor({
        title,
        description,
        severity,
        owner,
        sourceRiskId = null
    }) {
        validateText(title, "Issue title");
        validateText(description, "Issue description");
        validateText(owner, "Issue owner");

        if (!Object.values(Severity).includes(severity)) {
            throw new DomainError("Invalid issue severity.");
        }

        this.id = crypto.randomUUID();
        this.title = title;
        this.description = description;
        this.severity = severity;
        this.priority = severityToPriority(severity);
        this.owner = owner;
        this.sourceRiskId = sourceRiskId;
        this.status = IssueStatus.OPEN;
        this.resolution = null;
        this.createdAt = new Date().toISOString();
    }

    start() {
        if (this.status !== IssueStatus.OPEN) {
            throw new DomainError("Only open issues can be started.");
        }

        this.status = IssueStatus.IN_PROGRESS;
    }

    block() {
        if (![IssueStatus.OPEN, IssueStatus.IN_PROGRESS]
            .includes(this.status)) {
            throw new DomainError("Invalid blocked transition.");
        }

        this.status = IssueStatus.BLOCKED;
    }

    resolve(details) {
        if (![IssueStatus.OPEN, IssueStatus.IN_PROGRESS,
            IssueStatus.BLOCKED].includes(this.status)) {
            throw new DomainError("Issue cannot be resolved.");
        }

        validateText(details, "Resolution");
        this.resolution = details;
        this.status = IssueStatus.RESOLVED;
    }

    close() {
        if (this.status !== IssueStatus.RESOLVED) {
            throw new DomainError("Only resolved issues can be closed.");
        }

        this.status = IssueStatus.CLOSED;
    }
}

class RiskIssueManager extends EventEmitter {
    constructor() {
        super();

        this.risks = new Map();
        this.issues = new Map();
        this.eventHistory = [];
    }

    recordEvent(type, entity) {
        const event = Object.freeze({
            eventId: crypto.randomUUID(),
            type,
            entityId: entity.id,
            timestamp: new Date().toISOString()
        });

        this.eventHistory.push(event);
        this.emit("domainEvent", event);

        return event;
    }

    addRisk(risk) {
        if (!(risk instanceof Risk)) {
            throw new DomainError("Expected a Risk instance.");
        }

        if (this.risks.has(risk.id)) {
            throw new DomainError("Duplicate risk identifier.");
        }

        this.risks.set(risk.id, risk);
        this.recordEvent("RISK_CREATED", risk);
    }

    addIssue(issue) {
        if (!(issue instanceof Issue)) {
            throw new DomainError("Expected an Issue instance.");
        }

        if (this.issues.has(issue.id)) {
            throw new DomainError("Duplicate issue identifier.");
        }

        if (issue.sourceRiskId !== null &&
            !this.risks.has(issue.sourceRiskId)) {
            throw new DomainError("Referenced risk does not exist.");
        }

        this.issues.set(issue.id, issue);
        this.recordEvent("ISSUE_CREATED", issue);
    }

    materializeRisk(riskId, details) {
        const risk = this.risks.get(riskId);

        if (!risk) {
            throw new DomainError("Risk does not exist.");
        }

        const issue = new Issue({
            title: details.title,
            description: details.description,
            severity: risk.severity,
            owner: details.owner || risk.owner,
            sourceRiskId: risk.id
        });

        this.addIssue(issue);
        this.recordEvent("RISK_MATERIALIZED", issue);

        return issue;
    }

    evaluateRiskPortfolio() {
        return [...this.risks.values()]
            .filter(risk => risk.status !== RiskStatus.CLOSED)
            .map(risk => ({
                id: risk.id,
                title: risk.title,
                exposure: risk.exposure,
                severity: risk.severity,
                status: risk.status
            }))
            .sort((a, b) => b.exposure - a.exposure);
    }

    evaluateIssueBacklog() {
        const open = [...this.issues.values()]
            .filter(issue => ![
                IssueStatus.RESOLVED,
                IssueStatus.CLOSED
            ].includes(issue.status));

        return {
            total: this.issues.size,
            unresolved: open.length,
            urgent: open.filter(
                issue => issue.priority === Priority.URGENT
            ).length,
            blocked: open.filter(
                issue => issue.status === IssueStatus.BLOCKED
            ).length,
            items: open
        };
    }

    dashboard() {
        return {
            risks: {
                total: this.risks.size,
                critical: [...this.risks.values()].filter(
                    risk => risk.severity === Severity.CRITICAL &&
                        risk.status !== RiskStatus.CLOSED
                ).length
            },
            issues: {
                total: this.issues.size,
                unresolved: this.evaluateIssueBacklog().unresolved
            },
            recordedEvents: this.eventHistory.length
        };
    }

    async exportReport(filename) {
        const report = {
            generatedAt: new Date().toISOString(),
            risks: [...this.risks.values()],
            issues: [...this.issues.values()],
            events: this.eventHistory,
            dashboard: this.dashboard()
        };

        // Exclusive creation avoids overwriting an existing report.
        await fs.writeFile(
            filename,
            JSON.stringify(report, null, 2),
            { encoding: "utf8", flag: "wx", mode: 0o600 }
        );
    }
}

async function main() {
    const manager = new RiskIssueManager();

    manager.on("domainEvent", event => {
        console.log("EVENT:", event.type, event.entityId);
    });

    const deploymentRisk = new Risk({
        title: "Deployment failure",
        description: "A future release may fail during production deployment.",
        probability: 4,
        impact: 5,
        owner: "DevOps Team",
        category: "Technology",
        mitigation: "Use staged deployment and automated rollback.",
        contingency: "Restore the last stable production release."
    });

    manager.addRisk(deploymentRisk);
    deploymentRisk.assess();
    deploymentRisk.startMitigation();

    const operationalRisk = new Risk({
        title: "Third-party API unavailability",
        description: "The payment provider may become unavailable.",
        probability: 3,
        impact: 4,
        owner: "Platform Team",
        mitigation: "Configure retries and an alternative provider."
    });

    manager.addRisk(operationalRisk);
    operationalRisk.assess();

    // An actual production failure is an issue, not a potential risk.
    const productionIssue = new Issue({
        title: "Payment API returning HTTP 503",
        description: "Production payment requests are failing.",
        severity: Severity.CRITICAL,
        owner: "Platform Team"
    });

    manager.addIssue(productionIssue);
    productionIssue.start();
    productionIssue.block();

    // A potential risk has now materialized.
    const materializedIssue = manager.materializeRisk(
        deploymentRisk.id,
        {
            title: "Production deployment failed",
            description: "The deployment failed during database migration."
        }
    );

    materializedIssue.start();

    console.log("\nRISK REGISTER");
    console.table(manager.evaluateRiskPortfolio());

    console.log("\nISSUE BACKLOG");
    console.log(manager.evaluateIssueBacklog());

    console.log("\nMANAGEMENT DASHBOARD");
    console.log(manager.dashboard());

    // Validate the distinction between risks and issues.
    if (deploymentRisk.status !== RiskStatus.MITIGATING) {
        throw new Error("Risk state validation failed.");
    }

    if (materializedIssue.sourceRiskId !== deploymentRisk.id) {
        throw new Error("Risk-to-issue traceability failed.");
    }

    if (productionIssue.status !== IssueStatus.BLOCKED) {
        throw new Error("Issue state validation failed.");
    }

    console.log("\nAll domain validations passed.");

    // Uncomment to export a new report without overwriting existing files.
    // await manager.exportReport("risk-issue-report.json");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
