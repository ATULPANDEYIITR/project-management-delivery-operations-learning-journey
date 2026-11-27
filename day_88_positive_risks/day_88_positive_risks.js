"use strict";

/*
 * POSITIVE RISKS: PROJECT OPPORTUNITY MANAGEMENT
 *
 * Event-driven opportunity register and evaluation engine.
 * Features:
 * - Opportunity assessment
 * - EMV and net benefit calculations
 * - Opportunity response strategies
 * - Asynchronous event processing
 * - Portfolio prioritization
 * - State transition enforcement
 * - Event history and reporting
 * - JSON persistence using Node.js
 */

const fs = require("node:fs/promises");
const EventEmitter = require("node:events");

const Category = Object.freeze({
    COST: "Cost",
    SCHEDULE: "Schedule",
    QUALITY: "Quality",
    TECHNOLOGY: "Technology",
    RESOURCE: "Resource",
    BUSINESS: "Business",
    STRATEGIC: "Strategic"
});

const Strategy = Object.freeze({
    EXPLOIT: "Exploit",
    ENHANCE: "Enhance",
    SHARE: "Share",
    ACCEPT: "Accept"
});

const Status = Object.freeze({
    IDENTIFIED: "Identified",
    ASSESSED: "Assessed",
    PLANNED: "Planned",
    IN_PROGRESS: "In Progress",
    REALIZED: "Realized",
    CLOSED: "Closed"
});

class ValidationError extends Error {}

class StateTransitionError extends Error {}

class Opportunity {
    constructor({
        id,
        title,
        description,
        category,
        probability,
        impact,
        owner,
        strategy,
        responseCost = 0,
        confidence = 1,
        responseAction = ""
    }) {
        this.id = String(id).trim();
        this.title = String(title).trim();
        this.description = String(description).trim();
        this.category = category;
        this.probability = Number(probability);
        this.impact = Number(impact);
        this.owner = String(owner).trim();
        this.strategy = strategy;
        this.responseCost = Number(responseCost);
        this.confidence = Number(confidence);
        this.responseAction = responseAction;
        this.realizedBenefit = 0;
        this.status = Status.IDENTIFIED;
        this.history = [];

        this.validate();
    }

    validate() {
        if (!this.id || !this.title || !this.owner) {
            throw new ValidationError(
                "ID, title, and owner are mandatory."
            );
        }

        if (!Object.values(Category).includes(this.category)) {
            throw new ValidationError("Invalid opportunity category.");
        }

        if (!Object.values(Strategy).includes(this.strategy)) {
            throw new ValidationError("Invalid response strategy.");
        }

        if (!Number.isFinite(this.probability) ||
            this.probability < 0 ||
            this.probability > 1) {
            throw new ValidationError(
                "Probability must be between 0 and 1."
            );
        }

        if (!Number.isFinite(this.impact) || this.impact < 0) {
            throw new ValidationError("Impact must be non-negative.");
        }

        if (!Number.isFinite(this.responseCost) ||
            this.responseCost < 0) {
            throw new ValidationError("Invalid response cost.");
        }

        if (!Number.isFinite(this.confidence) ||
            this.confidence <= 0 ||
            this.confidence > 1) {
            throw new ValidationError("Invalid confidence factor.");
        }
    }

    get emv() {
        return this.probability * this.impact;
    }

    get netValue() {
        return this.emv - this.responseCost;
    }

    get adjustedValue() {
        return this.netValue * this.confidence;
    }

    record(event) {
        this.history.push({
            event,
            timestamp: new Date().toISOString(),
            status: this.status
        });
    }
}

class OpportunityEngine extends EventEmitter {
    #register = new Map();
    #eventQueue = Promise.resolve();

    add(opportunity) {
        if (!(opportunity instanceof Opportunity)) {
            throw new ValidationError("Expected an Opportunity instance.");
        }

        if (this.#register.has(opportunity.id)) {
            throw new ValidationError("Duplicate opportunity ID.");
        }

        this.#register.set(opportunity.id, opportunity);
        opportunity.record("Opportunity identified");

        this.emit("identified", {
            id: opportunity.id,
            title: opportunity.title
        });

        return opportunity;
    }

    get(id) {
        const opportunity = this.#register.get(id);

        if (!opportunity) {
            throw new ValidationError(`Unknown opportunity: ${id}`);
        }

        return opportunity;
    }

    transition(id, expected, next, event) {
        const opportunity = this.get(id);

        if (opportunity.status !== expected) {
            throw new StateTransitionError(
                `${id}: expected ${expected}, found ${opportunity.status}`
            );
        }

        opportunity.status = next;
        opportunity.record(event);

        this.emit("statusChanged", {
            id,
            previous: expected,
            current: next,
            event
        });

        return opportunity;
    }

    assess(id) {
        const opportunity = this.get(id);
        opportunity.validate();

        return this.transition(
            id,
            Status.IDENTIFIED,
            Status.ASSESSED,
            "Opportunity assessed"
        );
    }

    plan(id, action) {
        if (typeof action !== "string" || !action.trim()) {
            throw new ValidationError("Response action is required.");
        }

        const opportunity = this.get(id);

        if (![Status.IDENTIFIED, Status.ASSESSED].includes(
            opportunity.status
        )) {
            throw new StateTransitionError("Response cannot be planned.");
        }

        opportunity.responseAction = action.trim();
        opportunity.status = Status.PLANNED;
        opportunity.record("Response plan established");

        this.emit("planned", { id, action });
    }

    execute(id) {
        return this.transition(
            id,
            Status.PLANNED,
            Status.IN_PROGRESS,
            "Response execution started"
        );
    }

    realize(id, benefit) {
        if (!Number.isFinite(benefit) || benefit < 0) {
            throw new ValidationError("Invalid realized benefit.");
        }

        const opportunity = this.get(id);
        opportunity.realizedBenefit = benefit;

        return this.transition(
            id,
            Status.IN_PROGRESS,
            Status.REALIZED,
            "Opportunity realized"
        );
    }

    close(id) {
        const opportunity = this.get(id);

        if (![Status.IDENTIFIED, Status.ASSESSED,
            Status.REALIZED].includes(opportunity.status)) {
            throw new StateTransitionError(
                "Opportunity cannot be closed in this state."
            );
        }

        const previous = opportunity.status;
        opportunity.status = Status.CLOSED;
        opportunity.record("Opportunity closed");

        this.emit("statusChanged", {
            id,
            previous,
            current: Status.CLOSED
        });
    }

    // Serialize asynchronous work to avoid conflicting state transitions.
    enqueue(operation) {
        const result = this.#eventQueue.then(operation);
        this.#eventQueue = result.catch(() => {});
        return result;
    }

    rank() {
        return [...this.#register.values()].sort(
            (a, b) => b.adjustedValue - a.adjustedValue
        );
    }

    report() {
        const opportunities = [...this.#register.values()];

        const totals = opportunities.reduce((result, item) => {
            result.emv += item.emv;
            result.cost += item.responseCost;
            result.realized += item.realizedBenefit;

            result.status[item.status] =
                (result.status[item.status] || 0) + 1;

            return result;
        }, {
            emv: 0,
            cost: 0,
            realized: 0,
            status: {}
        });

        return {
            count: opportunities.length,
            expectedValue: totals.emv,
            responseCost: totals.cost,
            netExpectedValue: totals.emv - totals.cost,
            realizedBenefit: totals.realized,
            status: totals.status
        };
    }

    async save(file) {
        const data = JSON.stringify(
            [...this.#register.values()],
            null,
            2
        );

        const temporary = `${file}.tmp`;

        await fs.writeFile(temporary, data, {
            encoding: "utf8",
            mode: 0o600
        });

        await fs.rename(temporary, file);
    }

    async load(file) {
        const data = JSON.parse(
            await fs.readFile(file, "utf8")
        );

        if (!Array.isArray(data)) {
            throw new ValidationError("Invalid register format.");
        }

        const replacement = new Map();

        for (const record of data) {
            const opportunity = new Opportunity(record);

            opportunity.status = record.status;
            opportunity.realizedBenefit = record.realizedBenefit;
            opportunity.history = record.history || [];

            if (!Object.values(Status).includes(opportunity.status)) {
                throw new ValidationError("Invalid stored status.");
            }

            if (replacement.has(opportunity.id)) {
                throw new ValidationError("Duplicate stored ID.");
            }

            replacement.set(opportunity.id, opportunity);
        }

        this.#register = replacement;
    }
}

async function main() {
    const engine = new OpportunityEngine();

    engine.on("identified", event => {
        console.log("IDENTIFIED:", event.id, event.title);
    });

    engine.on("statusChanged", event => {
        console.log(
            "STATE:",
            event.id,
            event.previous,
            "->",
            event.current
        );
    });

    const opportunities = [
        new Opportunity({
            id: "OPP-101",
            title: "Process Automation",
            description: "Automate recurring reporting.",
            category: Category.COST,
            probability: 0.85,
            impact: 200000,
            owner: "Project Manager",
            strategy: Strategy.EXPLOIT,
            responseCost: 25000,
            confidence: 0.95
        }),
        new Opportunity({
            id: "OPP-102",
            title: "Accelerated Delivery",
            description: "Parallelize independent development tasks.",
            category: Category.SCHEDULE,
            probability: 0.7,
            impact: 150000,
            owner: "Delivery Lead",
            strategy: Strategy.ENHANCE,
            responseCost: 15000
        }),
        new Opportunity({
            id: "OPP-103",
            title: "Strategic Partnership",
            description: "Jointly deliver a technology capability.",
            category: Category.STRATEGIC,
            probability: 0.6,
            impact: 300000,
            owner: "Business Director",
            strategy: Strategy.SHARE,
            responseCost: 30000
        })
    ];

    for (const opportunity of opportunities) {
        engine.add(opportunity);
    }

    await engine.enqueue(async () => {
        engine.assess("OPP-101");
        engine.plan(
            "OPP-101",
            "Automate reporting and measure realized savings."
        );
        engine.execute("OPP-101");
        engine.realize("OPP-101", 175000);
    });

    console.log("\nOPPORTUNITY PRIORITIES");

    for (const opportunity of engine.rank()) {
        console.log({
            id: opportunity.id,
            title: opportunity.title,
            EMV: opportunity.emv,
            netValue: opportunity.netValue,
            adjustedValue: opportunity.adjustedValue
        });
    }

    console.log("\nPORTFOLIO REPORT");
    console.log(engine.report());

    await engine.save("opportunity_register.json");

    try {
        engine.assess("OPP-101");
    } catch (error) {
        console.log("Expected state rejection:", error.message);
    }
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
