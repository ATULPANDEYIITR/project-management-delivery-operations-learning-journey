"use strict";

/*
 * Project Cost Estimation Engine
 *
 * This implementation focuses on JavaScript-specific mechanisms:
 * event-driven estimate updates, immutable snapshots, validation,
 * asynchronous persistence simulation, and policy evaluation.
 */

const CostMethod = Object.freeze({
    BOTTOM_UP: "bottom_up",
    PARAMETRIC: "parametric",
    THREE_POINT: "three_point"
});

const ProjectState = Object.freeze({
    DRAFT: "draft",
    ESTIMATED: "estimated",
    APPROVED: "approved",
    FORECASTING: "forecasting",
    CLOSED: "closed"
});

class CostItem {
    constructor({ name, category, quantity, unitCost }) {
        if (!name || name.trim().length === 0) {
            throw new Error("Cost item name is required.");
        }
        if (!Number.isFinite(quantity) || quantity < 0) {
            throw new Error(`Invalid quantity for ${name}.`);
        }
        if (!Number.isFinite(unitCost) || unitCost < 0) {
            throw new Error(`Invalid unit cost for ${name}.`);
        }

        this.name = name;
        this.category = category;
        this.quantity = quantity;
        this.unitCost = unitCost;
    }

    get total() {
        return roundCurrency(this.quantity * this.unitCost);
    }
}

class RiskEvent {
    constructor({ name, probability, impact }) {
        if (!name) {
            throw new Error("Risk name is required.");
        }
        if (!Number.isFinite(probability) || probability < 0 || probability > 1) {
            throw new Error(`Invalid probability for ${name}.`);
        }
        if (!Number.isFinite(impact) || impact < 0) {
            throw new Error(`Invalid impact for ${name}.`);
        }

        this.name = name;
        this.probability = probability;
        this.impact = impact;
    }

    get expectedMonetaryValue() {
        return roundCurrency(this.probability * this.impact);
    }
}

class CostEstimate {
    constructor(projectName) {
        this.projectName = projectName;
        this.items = [];
        this.risks = [];
        this.state = ProjectState.DRAFT;
        this.version = 0;
        this.listeners = new Set();
    }

    addItem(item) {
        if (this.state === ProjectState.CLOSED) {
            throw new Error("A closed estimate cannot be modified.");
        }

        this.items.push(item);
        this.version++;
        this.emit("cost-item-added", item);
    }

    addRisk(risk) {
        if (this.state === ProjectState.CLOSED) {
            throw new Error("A closed estimate cannot be modified.");
        }

        this.risks.push(risk);
        this.version++;
        this.emit("risk-added", risk);
    }

    subscribe(listener) {
        if (typeof listener !== "function") {
            throw new TypeError("Listener must be a function.");
        }

        this.listeners.add(listener);

        return () => this.listeners.delete(listener);
    }

    emit(eventName, payload) {
        for (const listener of this.listeners) {
            listener({
                eventName,
                projectName: this.projectName,
                version: this.version,
                payload
            });
        }
    }

    get directCost() {
        return roundCurrency(
            this.items.reduce((sum, item) => sum + item.total, 0)
        );
    }

    get expectedRiskCost() {
        return roundCurrency(
            this.risks.reduce(
                (sum, risk) => sum + risk.expectedMonetaryValue,
                0
            )
        );
    }

    calculateReserve(rate = 0.05) {
        if (rate < 0 || rate > 1) {
            throw new Error("Reserve rate must be between 0 and 1.");
        }

        return roundCurrency(this.directCost * rate);
    }

    get totalEstimate() {
        return roundCurrency(
            this.directCost +
            this.expectedRiskCost +
            this.calculateReserve()
        );
    }

    markEstimated() {
        if (this.items.length === 0) {
            throw new Error("An estimate requires at least one cost item.");
        }

        this.state = ProjectState.ESTIMATED;
        this.version++;
        this.emit("estimate-completed", this.snapshot());
    }

    approve() {
        if (this.state !== ProjectState.ESTIMATED) {
            throw new Error(
                "Only an estimated project can move to approved state."
            );
        }

        this.state = ProjectState.APPROVED;
        this.version++;
        this.emit("estimate-approved", this.snapshot());
    }

    beginForecasting() {
        if (this.state !== ProjectState.APPROVED) {
            throw new Error(
                "Forecasting requires an approved cost estimate."
            );
        }

        this.state = ProjectState.FORECASTING;
        this.version++;
        this.emit("forecasting-started", this.snapshot());
    }

    close() {
        if (this.state !== ProjectState.FORECASTING) {
            throw new Error(
                "A project must be in forecasting state before closure."
            );
        }

        this.state = ProjectState.CLOSED;
        this.version++;
        this.emit("project-closed", this.snapshot());
    }

    snapshot() {
        return Object.freeze({
            projectName: this.projectName,
            state: this.state,
            version: this.version,
            directCost: this.directCost,
            expectedRiskCost: this.expectedRiskCost,
            reserve: this.calculateReserve(),
            totalEstimate: this.totalEstimate
        });
    }
}

function roundCurrency(value) {
    if (!Number.isFinite(value)) {
        throw new Error("Currency calculation produced a non-finite value.");
    }

    return Math.round((value + Number.EPSILON) * 100) / 100;
}

function parametricEstimate({
    units,
    unitCost,
    fixedCost = 0
}) {
    if (!Number.isInteger(units) || units < 0) {
        throw new Error("Units must be a non-negative integer.");
    }

    if (unitCost < 0 || fixedCost < 0) {
        throw new Error("Costs cannot be negative.");
    }

    return roundCurrency(units * unitCost + fixedCost);
}

function pertEstimate({ optimistic, mostLikely, pessimistic }) {
    if (
        optimistic < 0 ||
        mostLikely < 0 ||
        pessimistic < 0 ||
        optimistic > mostLikely ||
        mostLikely > pessimistic
    ) {
        throw new Error(
            "Three-point estimates must satisfy optimistic <= mostLikely <= pessimistic."
        );
    }

    return roundCurrency(
        (optimistic + 4 * mostLikely + pessimistic) / 6
    );
}

function calculateEarnedValueForecast({
    budgetAtCompletion,
    earnedValue,
    actualCost
}) {
    if (
        budgetAtCompletion < 0 ||
        earnedValue < 0 ||
        actualCost < 0
    ) {
        throw new Error("Earned value inputs cannot be negative.");
    }

    if (earnedValue === 0 || actualCost === 0) {
        throw new Error(
            "Earned value and actual cost must be positive for CPI forecasting."
        );
    }

    const costPerformanceIndex = earnedValue / actualCost;
    const estimateAtCompletion =
        budgetAtCompletion / costPerformanceIndex;

    return {
        costPerformanceIndex: Number(costPerformanceIndex.toFixed(4)),
        estimateAtCompletion: roundCurrency(estimateAtCompletion),
        varianceAtCompletion: roundCurrency(
            budgetAtCompletion - estimateAtCompletion
        )
    };
}

async function persistEstimate(snapshot) {
    /*
     * A Promise models asynchronous persistence without requiring
     * a third-party package or a live server.
     */
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                persistedAt: new Date().toISOString(),
                record: snapshot
            });
        }, 20);
    });
}

async function runWorkflow() {
    console.log("PROJECT COST ESTIMATION ENGINE");

    const project = new CostEstimate(
        "Regional Infrastructure Monitoring Platform"
    );

    project.subscribe((event) => {
        console.log(
            `[EVENT] ${event.eventName} | version=${event.version}`
        );
    });

    project.addItem(
        new CostItem({
            name: "Requirements analysis",
            category: "labor",
            quantity: 120,
            unitCost: 90
        })
    );

    project.addItem(
        new CostItem({
            name: "Application engineering",
            category: "labor",
            quantity: 420,
            unitCost: 72
        })
    );

    project.addItem(
        new CostItem({
            name: "Cloud environment",
            category: "infrastructure",
            quantity: 12,
            unitCost: 800
        })
    );

    project.addItem(
        new CostItem({
            name: "Security validation",
            category: "security",
            quantity: 60,
            unitCost: 105
        })
    );

    project.addRisk(
        new RiskEvent({
            name: "External integration rework",
            probability: 0.25,
            impact: 22000
        })
    );

    project.addRisk(
        new RiskEvent({
            name: "Security remediation",
            probability: 0.15,
            impact: 28000
        })
    );

    project.markEstimated();
    project.approve();
    project.beginForecasting();

    console.log("\nEstimate snapshot:");
    console.table(project.snapshot());

    const parametric = parametricEstimate({
        units: 1250,
        unitCost: 18.5,
        fixedCost: 12000
    });

    console.log(
        `\nParametric inspection estimate: ${parametric.toFixed(2)}`
    );

    const pert = pertEstimate({
        optimistic: 120000,
        mostLikely: 160000,
        pessimistic: 240000
    });

    console.log(`PERT estimate: ${pert.toFixed(2)}`);

    const forecast = calculateEarnedValueForecast({
        budgetAtCompletion: 200000,
        earnedValue: 98000,
        actualCost: 110000
    });

    console.log("\nEarned-value forecast:");
    console.table(forecast);

    const persisted = await persistEstimate(project.snapshot());

    console.log("\nAsynchronous persistence result:");
    console.dir(persisted, { depth: null });

    project.close();

    console.log("\nFinal project state:");
    console.table(project.snapshot());

    try {
        project.addItem(
            new CostItem({
                name: "Late change",
                category: "labor",
                quantity: 10,
                unitCost: 100
            })
        );
    } catch (error) {
        console.log(`Expected state error: ${error.message}`);
    }
}

runWorkflow().catch((error) => {
    console.error("Cost estimation workflow failed:", error.message);
    process.exitCode = 1;
});
