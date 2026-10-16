"use strict";

/*
 * Cost variance is modeled as:
 *     variance = actual cost - planned cost
 *
 * A positive result is unfavorable because spending exceeded the plan.
 * A negative result is favorable because spending was below the plan.
 *
 * This file uses an event-driven workflow rather than simply translating
 * the Python data model. The event stream represents operational cost
 * postings arriving during project execution.
 */

const EventEmitter = require("node:events");

const EPSILON = 0.005;

function toCents(value) {
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new TypeError(`Invalid monetary number: ${value}`);
    }
    return Math.round(value * 100);
  }

  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      throw new TypeError(`Invalid monetary value: ${value}`);
    }
    return Math.round(parsed * 100);
  }

  throw new TypeError(`Unsupported monetary value: ${String(value)}`);
}

function fromCents(cents) {
  return cents / 100;
}

function formatMoney(cents) {
  return fromCents(cents).toFixed(2);
}

function varianceStatus(plannedCents, actualCents) {
  const difference = actualCents - plannedCents;

  if (difference > 0) return "UNFAVORABLE";
  if (difference < 0) return "FAVORABLE";
  return "ON_PLAN";
}

class BudgetLine {
  constructor({ id, category, planned }) {
    if (!id || !category) {
      throw new Error("Budget line requires an id and category.");
    }

    this.id = id;
    this.category = category;
    this.plannedCents = toCents(planned);
    this.actualCents = 0;
  }

  postCost(amount, description) {
    const cents = toCents(amount);

    if (cents <= 0) {
      throw new RangeError("A cost posting must be greater than zero.");
    }

    if (!description || !description.trim()) {
      throw new Error("A cost posting requires a description.");
    }

    this.actualCents += cents;
  }

  get varianceCents() {
    return this.actualCents - this.plannedCents;
  }

  get varianceRate() {
    if (this.plannedCents === 0) return null;
    return this.varianceCents / this.plannedCents;
  }

  get status() {
    return varianceStatus(this.plannedCents, this.actualCents);
  }

  toJSON() {
    return {
      id: this.id,
      category: this.category,
      planned: formatMoney(this.plannedCents),
      actual: formatMoney(this.actualCents),
      variance: formatMoney(this.varianceCents),
      varianceRate:
        this.varianceRate === null
          ? null
          : `${(this.varianceRate * 100).toFixed(2)}%`,
      status: this.status
    };
  }
}

class CostLedger extends EventEmitter {
  constructor() {
    super();
    this.lines = new Map();
    this.events = [];
  }

  addBudgetLine(line) {
    if (this.lines.has(line.id)) {
      throw new Error(`Duplicate budget line: ${line.id}`);
    }

    this.lines.set(line.id, line);
    this.emit("budget.created", line);
  }

  recordCost({ budgetLineId, amount, description, source }) {
    const line = this.lines.get(budgetLineId);

    if (!line) {
      throw new Error(`Unknown budget line: ${budgetLineId}`);
    }

    const before = line.actualCents;
    line.postCost(amount, description);
    const after = line.actualCents;

    const event = {
      type: "cost.posted",
      budgetLineId,
      amountCents: after - before,
      description,
      source: source || "operational-system",
      timestamp: new Date().toISOString()
    };

    this.events.push(event);
    this.emit("cost.posted", event);
  }

  snapshot() {
    return [...this.lines.values()].map((line) => line.toJSON());
  }

  totals() {
    let plannedCents = 0;
    let actualCents = 0;

    for (const line of this.lines.values()) {
      plannedCents += line.plannedCents;
      actualCents += line.actualCents;
    }

    const varianceCents = actualCents - plannedCents;

    return {
      plannedCents,
      actualCents,
      varianceCents,
      varianceRate:
        plannedCents === 0
          ? null
          : varianceCents / plannedCents,
      status:
        Math.abs(varianceCents) < EPSILON
          ? "ON_PLAN"
          : varianceCents > 0
            ? "UNFAVORABLE"
            : "FAVORABLE"
    };
  }

  auditTrail() {
    return [...this.events];
  }
}

function printDashboard(ledger) {
  console.log("\nCOST VARIANCE DASHBOARD");
  console.log("=".repeat(82));
  console.log(
    `${"Category".padEnd(24)} ${"Planned".padStart(12)} ` +
    `${"Actual".padStart(12)} ${"Variance".padStart(12)} ${"Status".padStart(16)}`
  );
  console.log("-".repeat(82));

  for (const row of ledger.snapshot()) {
    console.log(
      `${row.category.padEnd(24)} ` +
      `${row.planned.padStart(12)} ` +
      `${row.actual.padStart(12)} ` +
      `${row.variance.padStart(12)} ` +
      `${row.status.padStart(16)}`
    );
  }

  const totals = ledger.totals();

  console.log("-".repeat(82));
  console.log(
    `${"TOTAL".padEnd(24)} ` +
    `${formatMoney(totals.plannedCents).padStart(12)} ` +
    `${formatMoney(totals.actualCents).padStart(12)} ` +
    `${formatMoney(totals.varianceCents).padStart(12)} ` +
    `${totals.status.padStart(16)}`
  );

  if (totals.varianceRate !== null) {
    console.log(
      `Variance rate: ${(totals.varianceRate * 100).toFixed(2)}%`
    );
  }
}

async function simulateOperationalPostings(ledger) {
  /*
   * setTimeout is used to model asynchronous cost postings from separate
   * operational sources. The Promise.all call preserves a clear completion
   * boundary while the EventEmitter records each posting as it arrives.
   */
  const postings = [
    {
      budgetLineId: "CLOUD",
      amount: 1800,
      description: "Compute and storage usage",
      source: "cloud-metering"
    },
    {
      budgetLineId: "CLOUD",
      amount: 0,
      description: "Invalid zero posting",
      source: "cloud-metering"
    },
    {
      budgetLineId: "CONTRACT",
      amount: 28750,
      description: "Monthly contractor invoice",
      source: "accounts-payable"
    },
    {
      budgetLineId: "TEST",
      amount: 9200,
      description: "External performance test",
      source: "testing-system"
    },
    {
      budgetLineId: "SECURITY",
      amount: 6100,
      description: "Security platform subscription",
      source: "procurement"
    }
  ];

  const validPostings = postings.filter((posting) => posting.amount > 0);

  await Promise.all(
    validPostings.map(
      (posting, index) =>
        new Promise((resolve) => {
          setTimeout(() => {
            ledger.recordCost(posting);
            resolve();
          }, index * 15);
        })
    )
  );
}

function demonstrateZeroBudget() {
  console.log("\nZERO-BASELINE CASE");
  console.log("=".repeat(82));

  const line = new BudgetLine({
    id: "EMERGENCY",
    category: "Unplanned emergency work",
    planned: 0
  });

  line.postCost(250, "Emergency infrastructure repair");

  console.log(JSON.stringify(line.toJSON(), null, 2));
  console.log(
    "A percentage is not produced because dividing by a zero planned baseline "
    + "would create a misleading variance rate."
  );
}

async function main() {
  const ledger = new CostLedger();

  ledger.on("budget.created", (line) => {
    console.log(
      `Budget created: ${line.category}, planned=${formatMoney(line.plannedCents)}`
    );
  });

  ledger.on("cost.posted", (event) => {
    console.log(
      `Cost posted: ${event.budgetLineId} +${formatMoney(event.amountCents)} ` +
      `from ${event.source}`
    );
  });

  ledger.addBudgetLine(
    new BudgetLine({
      id: "CLOUD",
      category: "Cloud infrastructure",
      planned: 12000
    })
  );

  ledger.addBudgetLine(
    new BudgetLine({
      id: "CONTRACT",
      category: "Contractors",
      planned: 30000
    })
  );

  ledger.addBudgetLine(
    new BudgetLine({
      id: "TEST",
      category: "Testing",
      planned: 8000
    })
  );

  ledger.addBudgetLine(
    new BudgetLine({
      id: "SECURITY",
      category: "Security tooling",
      planned: 6500
    })
  );

  ledger.recordCost({
    budgetLineId: "CLOUD",
    amount: 12000,
    description: "Initial cloud allocation",
    source: "cloud-metering"
  });

  try {
    ledger.recordCost({
      budgetLineId: "CLOUD",
      amount: -25,
      description: "Invalid reversal",
      source: "manual-entry"
    });
  } catch (error) {
    console.log(`Rejected posting: ${error.message}`);
  }

  await simulateOperationalPostings(ledger);

  printDashboard(ledger);

  console.log("\nEVENT AUDIT");
  console.log("=".repeat(82));
  for (const event of ledger.auditTrail()) {
    console.log(
      `${event.timestamp} | ${event.budgetLineId} | ` +
      `${formatMoney(event.amountCents)} | ${event.source}`
    );
  }

  demonstrateZeroBudget();
}

main().catch((error) => {
  console.error(`Cost variance processing failed: ${error.message}`);
  process.exitCode = 1;
});
