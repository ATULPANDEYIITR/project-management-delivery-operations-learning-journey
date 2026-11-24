"use strict";

/*
 * RISK RESPONSES: EVENT-DRIVEN RISK MANAGEMENT
 *
 * Demonstrates:
 * - Threat and opportunity response strategies.
 * - Risk assessment and response planning.
 * - Event-driven action execution.
 * - Budget enforcement.
 * - Response triggers.
 * - Residual and secondary risks.
 * - Approval and execution state transitions.
 * - Monitoring and audit events.
 *
 * Runtime: Node.js 18+
 * Dependencies: None.
 */

const { EventEmitter } = require("node:events");
const { randomUUID } = require("node:crypto");
const fs = require("node:fs/promises");

const RiskType = Object.freeze({
    THREAT: "THREAT",
    OPPORTUNITY: "OPPORTUNITY"
});

const Strategy = Object.freeze({
    AVOID: "AVOID",
    MITIGATE: "MITIGATE",
    TRANSFER: "TRANSFER",
    ACCEPT: "ACCEPT",
    EXPLOIT: "EXPLOIT",
    ENHANCE: "ENHANCE",
    SHARE: "SHARE",
    ESCALATE: "ESCALATE"
});

const RiskState = Object.freeze({
    IDENTIFIED: "IDENTIFIED",
    PLANNED: "PLANNED",
    APPROVED: "APPROVED",
    IN_PROGRESS: "IN_PROGRESS",
    MONITORING: "MONITORING",
    ESCALATED: "ESCALATED",
    CLOSED: "CLOSED"
});

const ActionState = Object.freeze({
    PENDING: "PENDING",
    IN_PROGRESS: "IN_PROGRESS",
    COMPLETED: "COMPLETED",
    BLOCKED: "BLOCKED",
    CANCELLED: "CANCELLED"
});

class RiskError extends Error {}

class RiskValidationError extends RiskError {}

class RiskBudgetError extends RiskError {}

class RiskTransitionError extends RiskError {}

function validateProbability(value, name = "Probability") {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0 ||
        value > 1
    ) {
        throw new RiskValidationError(
            `${name} must be a finite number between 0 and 1.`
        );
    }
}

function validateImpact(value) {
    if (
        !Number.isInteger(value) ||
        value < 1 ||
        value > 5
    ) {
        throw new RiskValidationError(
            "Impact must be an integer from 1 to 5."
        );
    }
}

function validateMoney(value, name) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0
    ) {
        throw new RiskValidationError(
            `${name} must be a non-negative finite number.`
        );
    }
}

class Risk {
    constructor({
        title,
        description,
        type,
        probability,
        impact,
        owner,
        category,
        responseBudget = 0,
        dueDate = null,
        trigger = null
    }) {
        if (!title?.trim() || !description?.trim()) {
            throw new RiskValidationError(
                "Risk title and description are required."
            );
        }

        if (!owner?.trim()) {
            throw new RiskValidationError("Risk owner is required.");
        }

        if (!Object.values(RiskType).includes(type)) {
            throw new RiskValidationError("Invalid risk type.");
        }

        validateProbability(probability);
        validateImpact(impact);
        validateMoney(responseBudget, "Response budget");

        this.id = randomUUID();
        this.title = title;
        this.description = description;
        this.type = type;
        this.probability = probability;
        this.impact = impact;
        this.owner = owner;
        this.category = category;
        this.responseBudget = responseBudget;
        this.dueDate = dueDate ? new Date(dueDate) : null;
        this.trigger = trigger;
        this.strategy = null;
        this.responseOwner = null;
        this.state = RiskState.IDENTIFIED;
        this.residual = null;
        this.secondaryRiskIds = [];
        this.actions = [];
        this.createdAt = new Date();
    }

    get inherentScore() {
        return this.probability * this.impact;
    }

    get residualScore() {
        return this.residual
            ? this.residual.probability * this.residual.impact
            : this.inherentScore;
    }

    get effectiveness() {
        if (this.inherentScore === 0) return 0;

        return Math.max(
            0,
            Math.min(
                100,
                ((this.inherentScore - this.residualScore) /
                    this.inherentScore) * 100
            )
        );
    }
}

class RiskAction {
    constructor({
        riskId,
        description,
        owner,
        deadline,
        cost
    }) {
        if (!description?.trim() || !owner?.trim()) {
            throw new RiskValidationError(
                "Action description and owner are required."
            );
        }

        validateMoney(cost, "Action cost");

        this.id = randomUUID();
        this.riskId = riskId;
        this.description = description;
        this.owner = owner;
        this.deadline = new Date(deadline);
        this.cost = cost;
        this.state = ActionState.PENDING;
        this.completedAt = null;

        if (Number.isNaN(this.deadline.getTime())) {
            throw new RiskValidationError("Invalid action deadline.");
        }
    }
}

class RiskManager extends EventEmitter {
    #risks = new Map();
    #auditLog = [];
    #listenersRegistered = false;

    constructor() {
        super();
        this.registerListeners();
    }

    registerListeners() {
        if (this.#listenersRegistered) return;

        this.on("risk:created", event =>
            console.log(`[EVENT] Risk created: ${event.title}`)
        );

        this.on("risk:approved", event =>
            console.log(`[EVENT] Response approved: ${event.id}`)
        );

        this.on("action:completed", event =>
            console.log(`[EVENT] Action completed: ${event.description}`)
        );

        this.on("risk:escalated", event =>
            console.log(`[EVENT] Escalated: ${event.title}`)
        );

        this.#listenersRegistered = true;
    }

    #record(riskId, event, details = {}) {
        const entry = {
            riskId,
            event,
            details,
            timestamp: new Date().toISOString()
        };

        this.#auditLog.push(entry);
        return entry;
    }

    get(riskId) {
        const risk = this.#risks.get(riskId);

        if (!risk) {
            throw new RiskValidationError(
                `Risk ${riskId} does not exist.`
            );
        }

        return risk;
    }

    createRisk(data) {
        const risk = new Risk(data);

        if (this.#risks.has(risk.id)) {
            throw new RiskValidationError("Duplicate risk identifier.");
        }

        this.#risks.set(risk.id, risk);
        this.#record(risk.id, "RISK_CREATED");

        this.emit("risk:created", {
            id: risk.id,
            title: risk.title
        });

        return risk;
    }

    planResponse(riskId, strategy, responseOwner) {
        const risk = this.get(riskId);

        const threatStrategies = [
            Strategy.AVOID,
            Strategy.MITIGATE,
            Strategy.TRANSFER,
            Strategy.ACCEPT,
            Strategy.ESCALATE
        ];

        const opportunityStrategies = [
            Strategy.EXPLOIT,
            Strategy.ENHANCE,
            Strategy.SHARE,
            Strategy.ACCEPT,
            Strategy.ESCALATE
        ];

        const allowed = risk.type === RiskType.THREAT
            ? threatStrategies
            : opportunityStrategies;

        if (!allowed.includes(strategy)) {
            throw new RiskValidationError(
                `${strategy} is invalid for ${risk.type}.`
            );
        }

        if (!responseOwner?.trim()) {
            throw new RiskValidationError(
                "Response owner is required."
            );
        }

        if (
            risk.state !== RiskState.IDENTIFIED &&
            risk.state !== RiskState.PLANNED
        ) {
            throw new RiskTransitionError(
                "Response cannot be changed in the current state."
            );
        }

        risk.strategy = strategy;
        risk.responseOwner = responseOwner;
        risk.state = RiskState.PLANNED;

        this.#record(riskId, "RESPONSE_PLANNED", {
            strategy,
            responseOwner
        });

        return risk;
    }

    approveResponse(riskId, approver) {
        const risk = this.get(riskId);

        if (risk.state !== RiskState.PLANNED) {
            throw new RiskTransitionError(
                "Only planned responses can be approved."
            );
        }

        if (!approver?.trim()) {
            throw new RiskValidationError("Approver is required.");
        }

        risk.state = RiskState.APPROVED;

        this.#record(riskId, "RESPONSE_APPROVED", { approver });

        this.emit("risk:approved", {
            id: riskId,
            approver
        });
    }

    addAction(riskId, actionData) {
        const risk = this.get(riskId);

        if (![
            RiskState.PLANNED,
            RiskState.APPROVED,
            RiskState.IN_PROGRESS
        ].includes(risk.state)) {
            throw new RiskTransitionError(
                "Risk must have a planned response."
            );
        }

        const action = new RiskAction({
            riskId,
            ...actionData
        });

        const committedCost = risk.actions
            .filter(item => item.state !== ActionState.CANCELLED)
            .reduce((sum, item) => sum + item.cost, 0);

        if (committedCost + action.cost > risk.responseBudget) {
            throw new RiskBudgetError(
                "Response action exceeds available budget."
            );
        }

        risk.actions.push(action);

        this.#record(riskId, "ACTION_ADDED", {
            actionId: action.id,
            cost: action.cost
        });

        return action;
    }

    updateAction(riskId, actionId, state) {
        const risk = this.get(riskId);

        const action = risk.actions.find(
            item => item.id === actionId
        );

        if (!action) {
            throw new RiskValidationError("Action not found.");
        }

        if (!Object.values(ActionState).includes(state)) {
            throw new RiskValidationError("Invalid action state.");
        }

        if ([
            ActionState.COMPLETED,
            ActionState.CANCELLED
        ].includes(action.state)) {
            throw new RiskTransitionError(
                "Completed or cancelled actions are immutable."
            );
        }

        action.state = state;

        if (state === ActionState.IN_PROGRESS) {
            risk.state = RiskState.IN_PROGRESS;
        }

        if (state === ActionState.COMPLETED) {
            action.completedAt = new Date();
            this.emit("action:completed", {
                description: action.description
            });
        }

        if (
            risk.actions.length > 0 &&
            risk.actions.every(
                item => [
                    ActionState.COMPLETED,
                    ActionState.CANCELLED
                ].includes(item.state)
            )
        ) {
            risk.state = RiskState.MONITORING;
        }

        this.#record(riskId, "ACTION_UPDATED", {
            actionId,
            state
        });
    }

    evaluateTrigger(riskId, observedValue) {
        const risk = this.get(riskId);

        if (typeof observedValue !== "number" ||
            !Number.isFinite(observedValue)) {
            throw new RiskValidationError(
                "Trigger observation must be numeric."
            );
        }

        // Example trigger: a supplier delay greater than 7 days.
        if (risk.trigger?.type === "GREATER_THAN") {
            const triggered = observedValue > risk.trigger.threshold;

            if (triggered) {
                this.escalate(
                    riskId,
                    `Observed value ${observedValue} exceeded threshold.`
                );
            }

            return triggered;
        }

        throw new RiskValidationError(
            "No supported numeric trigger is configured."
        );
    }

    setResidualRisk(riskId, probability, impact) {
        const risk = this.get(riskId);

        validateProbability(probability, "Residual probability");
        validateImpact(impact);

        risk.residual = {
            probability,
            impact,
            assessedAt: new Date()
        };

        this.#record(riskId, "RESIDUAL_RISK_ASSESSED", {
            probability,
            impact
        });
    }

    escalate(riskId, reason) {
        const risk = this.get(riskId);

        if (!reason?.trim()) {
            throw new RiskValidationError(
                "Escalation reason is required."
            );
        }

        risk.state = RiskState.ESCALATED;

        this.#record(riskId, "RISK_ESCALATED", { reason });

        this.emit("risk:escalated", {
            title: risk.title,
            reason
        });
    }

    addSecondaryRisk(parentRiskId, secondaryRiskId) {
        const parent = this.get(parentRiskId);
        const secondary = this.get(secondaryRiskId);

        if (parentRiskId === secondaryRiskId) {
            throw new RiskValidationError(
                "A risk cannot be its own secondary risk."
            );
        }

        if (!parent.secondaryRiskIds.includes(secondary.id)) {
            parent.secondaryRiskIds.push(secondary.id);
            this.#record(parentRiskId, "SECONDARY_RISK_LINKED", {
                secondaryRiskId
            });
        }
    }

    closeRisk(riskId, reason) {
        const risk = this.get(riskId);

        if (!reason?.trim()) {
            throw new RiskValidationError(
                "Closure reason is required."
            );
        }

        const unfinished = risk.actions.filter(
            item => ![
                ActionState.COMPLETED,
                ActionState.CANCELLED
            ].includes(item.state)
        );

        if (unfinished.length > 0) {
            throw new RiskTransitionError(
                "Outstanding actions must be completed or cancelled."
            );
        }

        risk.state = RiskState.CLOSED;

        this.#record(riskId, "RISK_CLOSED", { reason });
    }

    getAuditLog() {
        return structuredClone(this.#auditLog);
    }

    getRegister() {
        return [...this.#risks.values()];
    }

    getOverdueActions(referenceDate = new Date()) {
        return this.getRegister().flatMap(risk =>
            risk.actions.filter(action =>
                action.deadline < referenceDate &&
                ![
                    ActionState.COMPLETED,
                    ActionState.CANCELLED
                ].includes(action.state)
            )
        );
    }

    report() {
        return this.getRegister()
            .sort((a, b) => b.residualScore - a.residualScore)
            .map(risk => ({
                title: risk.title,
                type: risk.type,
                strategy: risk.strategy,
                owner: risk.owner,
                status: risk.state,
                inherentScore: risk.inherentScore,
                residualScore: risk.residualScore,
                effectiveness: Number(risk.effectiveness.toFixed(2)),
                actionCount: risk.actions.length
            }));
    }

    async exportJSON(filename) {
        const data = {
            risks: this.report(),
            audit: this.getAuditLog()
        };

        // Use a controlled filename and avoid accepting arbitrary file paths
        // from untrusted external input in production services.
        await fs.writeFile(
            filename,
            JSON.stringify(data, null, 2),
            { encoding: "utf8", flag: "w" }
        );
    }
}

function expectedMonetaryValue(probability, impact) {
    validateProbability(probability);
    validateMoney(impact, "Financial impact");

    return probability * impact;
}

function recommendStrategy(risk) {
    if (risk.type === RiskType.THREAT) {
        if (risk.inherentScore >= 3.5) return Strategy.AVOID;
        if (risk.inherentScore >= 2) return Strategy.MITIGATE;
        if (risk.inherentScore >= 1) return Strategy.TRANSFER;
        return Strategy.ACCEPT;
    }

    if (risk.inherentScore >= 3) return Strategy.EXPLOIT;
    if (risk.inherentScore >= 1.5) return Strategy.ENHANCE;

    return Strategy.ACCEPT;
}

async function main() {
    const manager = new RiskManager();

    const supplierRisk = manager.createRisk({
        title: "Supplier delivery failure",
        description: "Cloud infrastructure delivery may be delayed.",
        type: RiskType.THREAT,
        probability: 0.6,
        impact: 5,
        owner: "Project Manager",
        category: "Procurement",
        responseBudget: 15000,
        trigger: {
            type: "GREATER_THAN",
            threshold: 7
        }
    });

    manager.planResponse(
        supplierRisk.id,
        recommendStrategy(supplierRisk),
        "Procurement Lead"
    );

    manager.approveResponse(
        supplierRisk.id,
        "Project Sponsor"
    );

    const action = manager.addAction(supplierRisk.id, {
        description: "Qualify an alternative supplier.",
        owner: "Procurement Lead",
        deadline: new Date(Date.now() + 14 * 86400000),
        cost: 5000
    });

    manager.updateAction(
        supplierRisk.id,
        action.id,
        ActionState.IN_PROGRESS
    );

    manager.updateAction(
        supplierRisk.id,
        action.id,
        ActionState.COMPLETED
    );

    manager.setResidualRisk(supplierRisk.id, 0.2, 3);

    const opportunity = manager.createRisk({
        title: "Automated testing opportunity",
        description: "Automation may reduce deployment time.",
        type: RiskType.OPPORTUNITY,
        probability: 0.7,
        impact: 4,
        owner: "Engineering Manager",
        category: "Technology",
        responseBudget: 8000
    });

    manager.planResponse(
        opportunity.id,
        recommendStrategy(opportunity),
        "Automation Lead"
    );

    manager.approveResponse(
        opportunity.id,
        "Engineering Director"
    );

    console.log("\nEXPECTED MONETARY VALUE");

    console.log(
        "Inherent exposure:",
        expectedMonetaryValue(0.6, 100000)
    );

    console.log(
        "Residual exposure:",
        expectedMonetaryValue(0.2, 60000)
    );

    console.log("\nRISK REPORT");

    console.table(manager.report());

    console.log("\nOVERDUE ACTIONS");
    console.log(manager.getOverdueActions());

    console.log("\nTRIGGER TEST");

    console.log(
        "Trigger activated:",
        manager.evaluateTrigger(supplierRisk.id, 10)
    );

    console.log("\nAUDIT EVENTS:", manager.getAuditLog().length);

    // Assertions for critical domain behavior.
    if (supplierRisk.residualScore !== 0.6) {
        throw new Error("Residual risk calculation failed.");
    }

    if (supplierRisk.effectiveness !== 80) {
        throw new Error("Response effectiveness calculation failed.");
    }

    try {
        manager.planResponse(
            supplierRisk.id,
            Strategy.EXPLOIT,
            "Invalid Owner"
        );
    } catch (error) {
        console.log("\nEXPECTED ERROR:", error.message);
    }

    await manager.exportJSON("risk_response_report.json");

    console.log("\nRisk response processing completed.");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
