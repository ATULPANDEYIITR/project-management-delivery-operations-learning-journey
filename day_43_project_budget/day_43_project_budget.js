"use strict";

/*
 * Project Budgeting in JavaScript
 *
 * This implementation models a budget as an event-driven workflow.
 * It focuses on JavaScript-specific strengths: classes, Maps, Sets,
 * asynchronous event handling, immutable snapshots, validation, and
 * policy evaluation.
 *
 * Run with:
 *   node project-budget.js
 */

class BudgetValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "BudgetValidationError";
    }
}

const BudgetState = Object.freeze({
    DRAFT: "draft",
    APPROVED: "approved",
    ACTIVE: "active",
    CLOSED: "closed"
});

const ChangeState = Object.freeze({
    PROPOSED: "proposed",
    APPROVED: "approved",
    REJECTED: "rejected"
});

function currency(value) {
    if (!Number.isFinite(value)) {
        throw new BudgetValidationError("Amount must be a finite number.");
    }

    if (value < 0) {
        throw new BudgetValidationError("Amount cannot be negative.");
    }

    return Math.round((value + Number.EPSILON) * 100) / 100;
}

class EventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(eventName, handler) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }
        this.listeners.get(eventName).add(handler);
    }

    emit(eventName, payload) {
        const handlers = this.listeners.get(eventName) ?? [];

        for (const handler of handlers) {
            handler(payload);
        }
    }
}

class BudgetLine {
    constructor(category, description, plannedAmount) {
        if (!category || !description) {
            throw new BudgetValidationError(
                "Category and description are required."
            );
        }

        this.category = category;
        this.description = description;
        this.planned = currency(plannedAmount);
        this.committed = 0;
        this.actual = 0;
    }

    commit(amount) {
        amount = currency(amount);

        if (amount === 0) {
            throw new BudgetValidationError(
                "Commitment must be greater than zero."
            );
        }

        this.committed = currency(this.committed + amount);
    }

    spend(amount) {
        amount = currency(amount);

        if (amount === 0) {
            throw new BudgetValidationError(
                "Actual spending must be greater than zero."
            );
        }

        this.actual = currency(this.actual + amount);
    }

    get variance() {
        return currency(this.planned - this.actual);
    }

    get utilization() {
        return this.planned === 0
            ? 0
            : currency((this.actual / this.planned) * 100);
    }

    snapshot() {
        return Object.freeze({
            category: this.category,
            description: this.description,
            planned: this.planned,
            committed: this.committed,
            actual: this.actual,
            variance: this.variance,
            utilization: this.utilization
        });
    }
}

class ChangeRequest {
    constructor(id, description, amount) {
        if (!id || !description) {
            throw new BudgetValidationError(
                "Change request requires an ID and description."
            );
        }

        this.id = id;
        this.description = description;
        this.amount = currency(amount);

        if (this.amount === 0) {
            throw new BudgetValidationError(
                "Change request must have a positive value."
            );
        }

        this.status = ChangeState.PROPOSED;
    }

    approve() {
        if (this.status !== ChangeState.PROPOSED) {
            throw new BudgetValidationError(
                "Only proposed change requests can be approved."
            );
        }

        this.status = ChangeState.APPROVED;
    }
}

class ProjectBudget {
    constructor({ id, name, manager, contingencyRate = 0.1 }) {
        this.id = id;
        this.name = name;
        this.manager = manager;

        if (contingencyRate < 0 || contingencyRate > 1) {
            throw new BudgetValidationError(
                "Contingency rate must be between 0 and 1."
            );
        }

        this.contingencyRate = contingencyRate;
        this.state = BudgetState.DRAFT;
        this.lines = new Map();
        this.changeRequests = new Map();
        this.events = new EventBus();
    }

    addEventListener(eventName, handler) {
        this.events.on(eventName, handler);
    }

    addLine(line) {
        if (this.state !== BudgetState.DRAFT &&
            this.state !== BudgetState.ACTIVE) {
            throw new BudgetValidationError(
                "Budget lines cannot be changed in the current state."
            );
        }

        if (this.lines.has(line.category)) {
            throw new BudgetValidationError(
                `Budget category already exists: ${line.category}`
            );
        }

        this.lines.set(line.category, line);

        this.events.emit("budget.line.added", {
            category: line.category,
            amount: line.planned
        });
    }

    get directBudget() {
        return currency(
            [...this.lines.values()]
                .reduce((total, line) => total + line.planned, 0)
        );
    }

    get contingency() {
        return currency(this.directBudget * this.contingencyRate);
    }

    get approvedChanges() {
        return currency(
            [...this.changeRequests.values()]
                .filter(request => request.status === ChangeState.APPROVED)
                .reduce((total, request) => total + request.amount, 0)
        );
    }

    get authorizedBudget() {
        return currency(
            this.directBudget + this.contingency + this.approvedChanges
        );
    }

    get actualSpend() {
        return currency(
            [...this.lines.values()]
                .reduce((total, line) => total + line.actual, 0)
        );
    }

    get committedSpend() {
        return currency(
            [...this.lines.values()]
                .reduce((total, line) => total + line.committed, 0)
        );
    }

    get projectedCost() {
        /*
         * Remaining committed expenditure is added to actual expenditure.
         * This is deliberately conservative: it does not assume that
         * uncommitted future work will disappear.
         */
        const remainingCommitments = [...this.lines.values()]
            .reduce(
                (total, line) =>
                    total + Math.max(line.committed - line.actual, 0),
                0
            );

        return currency(this.actualSpend + remainingCommitments);
    }

    approve() {
        if (this.lines.size === 0) {
            throw new BudgetValidationError(
                "A budget needs at least one cost category."
            );
        }

        if (this.directBudget <= 0) {
            throw new BudgetValidationError(
                "The direct budget must be positive."
            );
        }

        this.state = BudgetState.APPROVED;
        this.events.emit("budget.approved", this.snapshot());
    }

    activate() {
        if (this.state !== BudgetState.APPROVED) {
            throw new BudgetValidationError(
                "Only approved budgets can become active."
            );
        }

        this.state = BudgetState.ACTIVE;
        this.events.emit("budget.activated", this.snapshot());
    }

    recordExpense(category, amount) {
        if (this.state !== BudgetState.ACTIVE) {
            throw new BudgetValidationError(
                "Expenses require an active budget."
            );
        }

        const line = this.lines.get(category);

        if (!line) {
            throw new BudgetValidationError(
                `Unknown budget category: ${category}`
            );
        }

        line.spend(amount);

        this.events.emit("expense.recorded", {
            category,
            amount: currency(amount),
            actualSpend: this.actualSpend
        });
    }

    recordCommitment(category, amount) {
        if (this.state !== BudgetState.ACTIVE) {
            throw new BudgetValidationError(
                "Commitments require an active budget."
            );
        }

        const line = this.lines.get(category);

        if (!line) {
            throw new BudgetValidationError(
                `Unknown budget category: ${category}`
            );
        }

        line.commit(amount);

        this.events.emit("commitment.recorded", {
            category,
            amount: currency(amount),
            committedSpend: this.committedSpend
        });
    }

    submitChangeRequest(request) {
        if (this.state !== BudgetState.ACTIVE) {
            throw new BudgetValidationError(
                "Only active budgets accept change requests."
            );
        }

        if (this.changeRequests.has(request.id)) {
            throw new BudgetValidationError(
                `Duplicate change request: ${request.id}`
            );
        }

        this.changeRequests.set(request.id, request);

        this.events.emit("change.requested", {
            id: request.id,
            amount: request.amount
        });
    }

    approveChangeRequest(id) {
        const request = this.changeRequests.get(id);

        if (!request) {
            throw new BudgetValidationError(
                `Unknown change request: ${id}`
            );
        }

        request.approve();

        this.events.emit("change.approved", {
            id,
            amount: request.amount,
            authorizedBudget: this.authorizedBudget
        });
    }

    health() {
        const utilization = this.authorizedBudget === 0
            ? 0
            : (this.actualSpend / this.authorizedBudget) * 100;

        if (this.projectedCost > this.authorizedBudget) {
            return "OVER_BUDGET";
        }

        if (utilization >= 90) {
            return "CRITICAL";
        }

        if (utilization >= 75) {
            return "WATCH";

        return "HEALTHY";
    }

    snapshot() {
        return Object.freeze({
            id: this.id,
            name: this.name,
            manager: this.manager,
            state: this.state,
            directBudget: this.directBudget,
            contingency: this.contingency,
            approvedChanges: this.approvedChanges,
            authorizedBudget: this.authorizedBudget,
            actualSpend: this.actualSpend,
            committedSpend: this.committedSpend,
            projectedCost: this.projectedCost,
            health: this.health(),
            lines: Object.freeze(
                [...this.lines.values()].map(line => line.snapshot())
            )
        });
    }
}

function printReport(snapshot) {
    console.log("\nPROJECT BUDGET DASHBOARD");
    console.log("=".repeat(72));
    console.log(`Project:            ${snapshot.name}`);
    console.log(`State:              ${snapshot.state}`);
    console.log(`Direct budget:      ${snapshot.directBudget.toFixed(2)}`);
    console.log(`Contingency:        ${snapshot.contingency.toFixed(2)}`);
    console.log(`Approved changes:   ${snapshot.approvedChanges.toFixed(2)}`);
    console.log(`Authorized budget:  ${snapshot.authorizedBudget.toFixed(2)}`);
    console.log(`Actual spending:    ${snapshot.actualSpend.toFixed(2)}`);
    console.log(`Committed spending: ${snapshot.committedSpend.toFixed(2)}`);
    console.log(`Projected cost:     ${snapshot.projectedCost.toFixed(2)}`);
    console.log(`Health:             ${snapshot.health}`);

    console.log("\nCATEGORY STATUS");

    for (const line of snapshot.lines) {
        console.log(
            `${line.category.padEnd(15)} ` +
            `planned=${line.planned.toFixed(2).padStart(12)} ` +
            `actual=${line.actual.toFixed(2).padStart(12)} ` +
            `variance=${line.variance.toFixed(2).padStart(12)}`
        );
    }
}

async function simulateOperationalEvents(budget) {
    const events = [
        ["commitment", "Engineering", 2800000],
        ["expense", "Engineering", 2100000],
        ["commitment", "Cloud", 850000],
        ["expense", "Cloud", 640000],
        ["commitment", "Security", 400000],
        ["expense", "Security", 270000],
        ["commitment", "Testing", 180000],
        ["expense", "Testing", 120000]
    ];

    for (const [type, category, amount] of events) {
        await new Promise(resolve => setTimeout(resolve, 10));

        if (type === "commitment") {
            budget.recordCommitment(category, amount);
        } else {
            budget.recordExpense(category, amount);
        }
    }
}

async function main() {
    const budget = new ProjectBudget({
        id: "PRJ-2026-042",
        name: "Enterprise Data Platform",
        manager: "Technology PMO",
        contingencyRate: 0.12
    });

    budget.addEventListener("expense.recorded", event => {
        console.log(
            `[EVENT] Expense recorded: ${event.category} = ${event.amount}`
        );
    });

    budget.addEventListener("change.approved", event => {
        console.log(
            `[EVENT] Change ${event.id} approved; ` +
            `new authorized budget = ${event.authorizedBudget}`
        );
    });

    budget.addLine(
        new BudgetLine("Engineering", "Application and data engineering", 4200000)
    );
    budget.addLine(
        new BudgetLine("Cloud", "Infrastructure and managed services", 1350000)
    );
    budget.addLine(
        new BudgetLine("Security", "Security tooling and assurance", 650000)
    );
    budget.addLine(
        new BudgetLine("Testing", "Integration and performance testing", 500000)
    );

    budget.approve();
    budget.activate();

    await simulateOperationalEvents(budget);

    const change = new ChangeRequest(
        "CR-001",
        "Expanded compliance testing",
        240000
    );

    budget.submitChangeRequest(change);
    budget.approveChangeRequest("CR-001");

    printReport(budget.snapshot());

    console.log("\nVALIDATION TEST");

    try {
        budget.recordExpense("Unknown", 5000);
    } catch (error) {
        if (error instanceof BudgetValidationError) {
            console.log(`Rejected transaction: ${error.message}`);
        } else {
            throw error;
        }
    }
}

main().catch(error => {
    console.error(`Fatal budget-processing error: ${error.message}`);
    process.exitCode = 1;
});
