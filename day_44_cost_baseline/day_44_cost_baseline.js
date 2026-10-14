"use strict";

/*
 * Cost Baseline: event-driven spending control.
 *
 * Run with Node.js 18 or later:
 *     node cost_baseline.js
 *
 * This implementation focuses on immutable baseline snapshots, asynchronous
 * cost submission, optimistic concurrency, event-driven change control,
 * approval separation, and earned-value performance evaluation.
 */

const { EventEmitter } = require("node:events");
const assert = require("node:assert/strict");

const roundMoney = (value) => {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new TypeError("Money must be a finite, non-negative number.");
  }

  // Integer paise avoids common floating-point rounding surprises.
  return Math.round((value + Number.EPSILON) * 100) / 100;
};

const validatePeriod = (period) => {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(period)) {
    throw new TypeError(`Invalid reporting period: ${period}`);
  }
  return period;
};

class Baseline {
  constructor({ id, project, revision, packages, allocations }) {
    if (!id || !project) {
      throw new TypeError("Baseline ID and project name are required.");
    }

    this.id = id;
    this.project = project;
    this.revision = revision;
    this.packages = Object.freeze(
      packages.map((item) =>
        Object.freeze({
          code: item.code,
          name: item.name,
          budget: roundMoney(item.budget),
        })
      )
    );

    this.allocations = Object.freeze(
      allocations.map((item) =>
        Object.freeze({
          period: validatePeriod(item.period),
          packageCode: item.packageCode,
          amount: roundMoney(item.amount),
        })
      )
    );

    const codes = new Set(this.packages.map((item) => item.code));

    if (codes.size !== this.packages.length) {
      throw new Error("Work package codes must be unique.");
    }

    for (const allocation of this.allocations) {
      if (!codes.has(allocation.packageCode)) {
        throw new Error(`Unknown package ${allocation.packageCode}.`);
      }
    }

    for (const item of this.packages) {
      const allocated = this.allocations
        .filter((allocation) => allocation.packageCode === item.code)
        .reduce((total, allocation) => total + allocation.amount, 0);

      if (Math.abs(allocated - item.budget) > 0.001) {
        throw new Error(`Allocation mismatch for ${item.code}.`);
      }
    }

    this.total = roundMoney(
      this.packages.reduce((total, item) => total + item.budget, 0)
    );
    this.status = "DRAFT";
    this.approvedBy = null;
  }

  approve(approver) {
    if (this.status !== "DRAFT") {
      throw new Error("Only draft baselines can be approved.");
    }
    if (!approver || !approver.trim()) {
      throw new Error("An approver is required.");
    }

    this.status = "APPROVED";
    this.approvedBy = approver;
    return this;
  }

  budgetThrough(period) {
    validatePeriod(period);
    return this.allocations
      .filter((item) => item.period <= period)
      .reduce((total, item) => total + item.amount, 0);
  }
}

class CostLedger extends EventEmitter {
  constructor(baseline) {
    super();

    if (baseline.status !== "APPROVED") {
      throw new Error("An approved baseline is required.");
    }

    this.baseline = baseline;
    this.entries = new Map();
    this.progress = new Map();
    this.pendingChanges = new Map();
    this.version = 0;
  }

  async submitCost(entry, expectedVersion = this.version) {
    // Yield to the event loop so the version check models concurrent requests.
    await new Promise((resolve) => setImmediate(resolve));

    if (expectedVersion !== this.version) {
      throw new Error(
        `Concurrent modification: expected ${expectedVersion}, current ${this.version}`
      );
    }

    if (!entry.id || this.entries.has(entry.id)) {
      throw new Error("A unique cost entry ID is required.");
    }

    validatePeriod(entry.period);
    const amount = roundMoney(entry.amount);

    if (!this.baseline.packages.some((item) => item.code === entry.packageCode)) {
      throw new Error("Unknown work package.");
    }

    const normalized = Object.freeze({
      ...entry,
      amount,
      approved: entry.approved !== false,
    });

    // Rejected or pending costs remain outside the approved ledger.
    if (!normalized.approved) {
      this.emit("cost:rejected", normalized);
      return { accepted: false, version: this.version };
    }

    this.entries.set(normalized.id, normalized);
    this.version += 1;
    this.emit("cost:recorded", normalized);
    return { accepted: true, version: this.version };
  }

  recordProgress(period, packageCode, percentage) {
    validatePeriod(period);

    if (!Number.isFinite(percentage) || percentage < 0 || percentage > 100) {
      throw new RangeError("Completion must be between 0 and 100.");
    }

    if (!this.baseline.packages.some((item) => item.code === packageCode)) {
      throw new Error("Unknown work package.");
    }

    const key = `${period}:${packageCode}`;
    const previous = this.progress.get(key);

    if (previous && percentage < previous.percentage) {
      throw new Error("Progress cannot decrease within a reporting period.");
    }

    this.progress.set(key, Object.freeze({ period, packageCode, percentage }));
  }

  cumulativeActualCost(period) {
    validatePeriod(period);
    return roundMoney(
      [...this.entries.values()]
        .filter((item) => item.period <= period && item.approved)
        .reduce((total, item) => total + item.amount, 0)
    );
  }

  earnedValue(period) {
    validatePeriod(period);

    // Use the latest reported completion for each package up to the period.
    const latest = new Map();

    for (const progress of this.progress.values()) {
      if (progress.period <= period) {
        const previous = latest.get(progress.packageCode);
        if (!previous || previous.period < progress.period) {
          latest.set(progress.packageCode, progress);
        }
      }
    }

    return roundMoney(
      this.baseline.packages.reduce((total, item) => {
        const progress = latest.get(item.code);
        return total + item.budget * (progress?.percentage ?? 0) / 100;
      }, 0)
    );
  }

  evaluate(period) {
    const pv = roundMoney(this.baseline.budgetThrough(period));
    const ev = this.earnedValue(period);
    const ac = this.cumulativeActualCost(period);

    const cpi = ac > 0 ? ev / ac : null;
    const spi = pv > 0 ? ev / pv : null;

    return Object.freeze({
      period,
      BAC: this.baseline.total,
      PV: pv,
      EV: ev,
      AC: ac,
      CV: roundMoney(Math.max(0, ev - ac)) * (ev < ac ? -1 : 1),
      SV: roundMoney(Math.max(0, ev - pv)) * (ev < pv ? -1 : 1),
      CPI: cpi,
      SPI: spi,
      EAC: cpi !== null && cpi > 0 ? roundMoney(this.baseline.total / cpi) : null,
    });
  }

  proposeChange(change) {
    if (!change.id || this.pendingChanges.has(change.id)) {
      throw new Error("Change request ID must be unique.");
    }

    if (!change.description?.trim()) {
      throw new Error("Change description is required.");
    }

    if (change.amountDelta === 0 || !Number.isFinite(change.amountDelta)) {
      throw new Error("A finite, non-zero change is required.");
    }

    validatePeriod(change.effectivePeriod);

    const request = Object.freeze({
      ...change,
      status: "PENDING",
    });

    this.pendingChanges.set(request.id, request);
    this.emit("change:proposed", request);
    return request;
  }

  decideChange(id, approver, approved, reason) {
    const request = this.pendingChanges.get(id);

    if (!request || request.status !== "PENDING") {
      throw new Error("A pending change request is required.");
    }

    if (!approver?.trim() || !reason?.trim()) {
      throw new Error("Approver and decision reason are required.");
    }

    const decision = Object.freeze({
      ...request,
      status: approved ? "APPROVED" : "REJECTED",
      decidedBy: approver,
      reason,
    });

    this.pendingChanges.set(id, decision);
    this.emit("change:decided", decision);

    // The approved change remains separate from the active baseline.
    return decision;
  }
}

function createDemonstration() {
  const baseline = new Baseline({
    id: "BASE-2026-01",
    project: "District Hospital Modernization",
    revision: 1,
    packages: [
      { code: "CIVIL", name: "Civil works", budget: 450000 },
      { code: "ELECT", name: "Electrical installation", budget: 300000 },
      { code: "TEST", name: "Testing and commissioning", budget: 250000 },
    ],
    allocations: [
      { period: "2026-01", packageCode: "CIVIL", amount: 150000 },
      { period: "2026-02", packageCode: "CIVIL", amount: 180000 },
      { period: "2026-03", packageCode: "CIVIL", amount: 120000 },
      { period: "2026-02", packageCode: "ELECT", amount: 50000 },
      { period: "2026-03", packageCode: "ELECT", amount: 150000 },
      { period: "2026-04", packageCode: "ELECT", amount: 100000 },
      { period: "2026-03", packageCode: "TEST", amount: 50000 },
      { period: "2026-04", packageCode: "TEST", amount: 100000 },
      { period: "2026-05", packageCode: "TEST", amount: 100000 },
    ],
  }).approve("Project Director");

  return new CostLedger(baseline);
}

async function main() {
  const ledger = createDemonstration();

  ledger.on("cost:recorded", (entry) => {
    console.log(`Recorded ${entry.id}: ₹${entry.amount.toLocaleString("en-IN")}`);
  });

  ledger.on("cost:rejected", (entry) => {
    console.log(`Excluded unapproved cost ${entry.id}.`);
  });

  ledger.on("change:decided", (change) => {
    console.log(`Change ${change.id}: ${change.status}`);
  });

  const costs = [
    { id: "C-101", period: "2026-01", packageCode: "CIVIL", amount: 140000 },
    { id: "C-102", period: "2026-02", packageCode: "CIVIL", amount: 200000 },
    { id: "C-103", period: "2026-02", packageCode: "ELECT", amount: 60000 },
    { id: "C-104", period: "2026-03", packageCode: "CIVIL", amount: 130000 },
    { id: "C-105", period: "2026-03", packageCode: "ELECT", amount: 140000 },
    { id: "C-106", period: "2026-03", packageCode: "TEST", amount: 30000 },
    {
      id: "C-107",
      period: "2026-03",
      packageCode: "TEST",
      amount: 25000,
      approved: false,
    },
  ];

  for (const entry of costs) {
    await ledger.submitCost(entry);
  }

  [
    ["2026-01", "CIVIL", 30],
    ["2026-02", "CIVIL", 70],
    ["2026-03", "CIVIL", 100],
    ["2026-02", "ELECT", 10],
    ["2026-03", "ELECT", 55],
    ["2026-03", "TEST", 10],
  ].forEach(([period, code, percentage]) => {
    ledger.recordProgress(period, code, percentage);
  });

  console.log("\nMarch performance:");
  console.table(ledger.evaluate("2026-03"));

  ledger.proposeChange({
    id: "CR-014",
    description: "Additional electrical safety panels",
    amountDelta: 50000,
    effectivePeriod: "2026-05",
  });

  ledger.decideChange(
    "CR-014",
    "Project Director",
    true,
    "Approved for safety compliance; baseline revision still required."
  );

  assert.equal(ledger.baseline.total, 1000000);
  assert.equal(ledger.cumulativeActualCost("2026-03"), 670000);
  assert.equal(ledger.evaluate("2026-03").EV, 770000);

  // Two concurrent requests using the same version cannot both commit.
  const version = ledger.version;
  const concurrent = await Promise.allSettled([
    ledger.submitCost({
      id: "C-108",
      period: "2026-04",
      packageCode: "ELECT",
      amount: 10000,
    }, version),
    ledger.submitCost({
      id: "C-109",
      period: "2026-04",
      packageCode: "TEST",
      amount: 10000,
    }, version),
  ]);

  assert.equal(concurrent.filter((item) => item.status === "fulfilled").length, 1);
  assert.equal(concurrent.filter((item) => item.status === "rejected").length, 1);

  console.log("\nConcurrency test passed.");
  console.log("Original approved baseline remains ₹10,00,000.");
}

main().catch((error) => {
  console.error(`Cost-control failure: ${error.message}`);
  process.exitCode = 1;
});
