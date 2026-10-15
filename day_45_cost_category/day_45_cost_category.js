"use strict";

/*
 * Cost tracking is modeled here as an event-driven workflow.
 * The implementation focuses on JavaScript-specific behavior:
 * immutable snapshots, event listeners, asynchronous persistence,
 * validation, and policy evaluation.
 */

const CostCategory = Object.freeze({
  LABOR: "labor",
  CLOUD: "cloud",
  SOFTWARE: "software",
  EQUIPMENT: "equipment",
  TRAVEL: "travel",
  CONTRACTOR: "contractor",
  MATERIALS: "materials",
  OTHER: "other"
});

class CostValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = "CostValidationError";
  }
}

function parseMoney(value) {
  const amount = Number(value);

  if (!Number.isFinite(amount) || amount <= 0) {
    throw new CostValidationError(`Invalid positive monetary value: ${value}`);
  }

  return Math.round((amount + Number.EPSILON) * 100) / 100;
}

function parseDate(value) {
  const parsed = new Date(`${value}T00:00:00Z`);

  if (Number.isNaN(parsed.getTime())) {
    throw new CostValidationError(`Invalid date: ${value}`);
  }

  return parsed;
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR"
  }).format(value);
}

class Expense {
  constructor({
    id,
    projectId,
    category,
    description,
    amount,
    expenseDate,
    vendor,
    approved = false,
    invoiceNumber = null
  }) {
    if (!id || !projectId || !description || !vendor) {
      throw new CostValidationError(
        "Expense requires an ID, project, description, and vendor."
      );
    }

    if (!Object.values(CostCategory).includes(category)) {
      throw new CostValidationError(`Unsupported category: ${category}`);
    }

    this.id = id;
    this.projectId = projectId;
    this.category = category;
    this.description = description;
    this.amount = parseMoney(amount);
    this.expenseDate = parseDate(expenseDate);
    this.vendor = vendor;
    this.approved = Boolean(approved);
    this.invoiceNumber = invoiceNumber;
    Object.freeze(this);
  }
}

class ProjectCostTracker {
  constructor(project) {
    this.project = Object.freeze({
      ...project,
      budget: { ...project.budget }
    });

    this.expenses = new Map();
    this.listeners = new Map();
  }

  on(eventName, listener) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, []);
    }

    this.listeners.get(eventName).push(listener);
  }

  emit(eventName, payload) {
    for (const listener of this.listeners.get(eventName) ?? []) {
      listener(payload);
    }
  }

  recordExpense(expense) {
    if (expense.projectId !== this.project.id) {
      throw new CostValidationError(
        "Expense belongs to a different project."
      );
    }

    if (this.expenses.has(expense.id)) {
      throw new CostValidationError(
        `Duplicate expense ID: ${expense.id}`
      );
    }

    const projectStart = parseDate(this.project.startDate);
    const projectEnd = parseDate(this.project.endDate);

    if (
      expense.expenseDate < projectStart ||
      expense.expenseDate > projectEnd
    ) {
      throw new CostValidationError(
        `Expense ${expense.id} falls outside the project period.`
      );
    }

    this.expenses.set(expense.id, expense);
    this.emit("expenseRecorded", expense);
  }

  actualByCategory() {
    const totals = Object.fromEntries(
      Object.values(CostCategory).map(category => [category, 0])
    );

    for (const expense of this.expenses.values()) {
      totals[expense.category] += expense.amount;
    }

    return totals;
  }

  getTotalBudget() {
    return Object.values(this.project.budget).reduce(
      (sum, value) => sum + value,
      0
    );
  }

  getTotalActual() {
    return [...this.expenses.values()].reduce(
      (sum, expense) => sum + expense.amount,
      0
    );
  }

  getVariance() {
    return this.getTotalBudget() - this.getTotalActual();
  }

  getUtilization() {
    const budget = this.getTotalBudget();

    if (budget === 0) {
      return 0;
    }

    return this.getTotalActual() / budget * 100;
  }

  evaluateBudgetPolicy(threshold = 0.8) {
    const actual = this.actualByCategory();
    const alerts = [];

    for (const [category, budget] of Object.entries(this.project.budget)) {
      const spent = actual[category] ?? 0;

      if (budget === 0 && spent > 0) {
        alerts.push({
          severity: "critical",
          category,
          message: `${category} has spending without a budget.`
        });
        continue;
      }

      if (budget > 0 && spent / budget >= threshold) {
        alerts.push({
          severity: spent > budget ? "critical" : "warning",
          category,
          utilization: spent / budget * 100,
          message: `${category} has consumed ${(
            spent / budget * 100
          ).toFixed(1)}% of its budget.`
        });
      }
    }

    return alerts;
  }

  monthlySpend() {
    const totals = new Map();

    for (const expense of this.expenses.values()) {
      const year = expense.expenseDate.getUTCFullYear();
      const month = String(
        expense.expenseDate.getUTCMonth() + 1
      ).padStart(2, "0");
      const key = `${year}-${month}`;

      totals.set(key, (totals.get(key) ?? 0) + expense.amount);
    }

    return Object.fromEntries(
      [...totals.entries()].sort(([a], [b]) => a.localeCompare(b))
    );
  }

  vendorExposure() {
    const totals = new Map();

    for (const expense of this.expenses.values()) {
      totals.set(
        expense.vendor,
        (totals.get(expense.vendor) ?? 0) + expense.amount
      );
    }

    return Object.fromEntries(
      [...totals.entries()].sort(([, a], [, b]) => b - a)
    );
  }

  findDataQualityProblems() {
    const problems = [];
    const invoices = new Set();

    for (const expense of this.expenses.values()) {
      if (expense.amount >= 10000 && !expense.approved) {
        problems.push(
          `${expense.id}: high-value expense is not approved.`
        );
      }

      if (expense.invoiceNumber) {
        if (invoices.has(expense.invoiceNumber)) {
          problems.push(
            `${expense.id}: duplicate invoice ${expense.invoiceNumber}.`
          );
        }
        invoices.add(expense.invoiceNumber);
      }
    }

    return problems;
  }

  async persistSnapshot() {
    /*
     * Promise-based persistence models an asynchronous Node.js or
     * browser storage boundary without introducing an external package.
     */
    await new Promise(resolve => setTimeout(resolve, 10));

    return JSON.stringify({
      project: this.project,
      expenses: [...this.expenses.values()]
    }, null, 2);
  }

  dashboard() {
    return {
      project: this.project.name,
      budget: this.getTotalBudget(),
      actual: this.getTotalActual(),
      variance: this.getVariance(),
      utilizationPercent: this.getUtilization(),
      byCategory: this.actualByCategory(),
      monthly: this.monthlySpend(),
      vendorExposure: this.vendorExposure(),
      alerts: this.evaluateBudgetPolicy(),
      dataQualityProblems: this.findDataQualityProblems()
    };
  }
}

async function main() {
  const tracker = new ProjectCostTracker({
    id: "PRJ-2026-002",
    name: "Secure Analytics Modernization",
    startDate: "2026-01-01",
    endDate: "2026-12-31",
    budget: {
      [CostCategory.LABOR]: 160000,
      [CostCategory.CLOUD]: 70000,
      [CostCategory.SOFTWARE]: 35000,
      [CostCategory.EQUIPMENT]: 30000,
      [CostCategory.TRAVEL]: 15000,
      [CostCategory.CONTRACTOR]: 45000
    }
  });

  tracker.on("expenseRecorded", expense => {
    console.log(
      `Recorded ${expense.id}: ${formatMoney(expense.amount)} ` +
      `for ${expense.category}`
    );
  });

  const expenses = [
    new Expense({
      id: "EXP-JS-001",
      projectId: "PRJ-2026-002",
      category: CostCategory.LABOR,
      description: "Data engineering allocation",
      amount: 24000,
      expenseDate: "2026-01-31",
      vendor: "Internal Engineering",
      approved: true
    }),
    new Expense({
      id: "EXP-JS-002",
      projectId: "PRJ-2026-002",
      category: CostCategory.CLOUD,
      description: "Analytics compute consumption",
      amount: 9200,
      expenseDate: "2026-01-31",
      vendor: "Cloud Provider",
      approved: true,
      invoiceNumber: "CLOUD-JS-001"
    }),
    new Expense({
      id: "EXP-JS-003",
      projectId: "PRJ-2026-002",
      category: CostCategory.SOFTWARE,
      description: "Security scanning subscriptions",
      amount: 12800,
      expenseDate: "2026-02-15",
      vendor: "Security Software Vendor",
      approved: true,
      invoiceNumber: "SEC-JS-001"
    }),
    new Expense({
      id: "EXP-JS-004",
      projectId: "PRJ-2026-002",
      category: CostCategory.CONTRACTOR,
      description: "Cloud architecture review",
      amount: 15000,
      expenseDate: "2026-03-10",
      vendor: "Architecture Consultancy",
      approved: false,
      invoiceNumber: "ARCH-JS-001"
    }),
    new Expense({
      id: "EXP-JS-005",
      projectId: "PRJ-2026-002",
      category: CostCategory.CLOUD,
      description: "Data warehouse workload",
      amount: 11800,
      expenseDate: "2026-02-28",
      vendor: "Cloud Provider",
      approved: true,
      invoiceNumber: "CLOUD-JS-002"
    })
  ];

  for (const expense of expenses) {
    tracker.recordExpense(expense);
  }

  console.log("\n=== JAVASCRIPT COST DASHBOARD ===");
  const dashboard = tracker.dashboard();

  console.log(`Project: ${dashboard.project}`);
  console.log(`Budget: ${formatMoney(dashboard.budget)}`);
  console.log(`Actual: ${formatMoney(dashboard.actual)}`);
  console.log(`Variance: ${formatMoney(dashboard.variance)}`);
  console.log(
    `Utilization: ${dashboard.utilizationPercent.toFixed(2)}%`
  );

  console.log("\nCategory spending:");
  for (const [category, amount] of Object.entries(
    dashboard.byCategory
  )) {
    if (amount > 0) {
      console.log(`  ${category}: ${formatMoney(amount)}`);
    }
  }

  console.log("\nMonthly spending:");
  for (const [month, amount] of Object.entries(dashboard.monthly)) {
    console.log(`  ${month}: ${formatMoney(amount)}`);
  }

  console.log("\nBudget alerts:");
  for (const alert of dashboard.alerts) {
    console.log(
      `  [${alert.severity}] ${alert.message}`
    );
  }

  console.log("\nData quality:");
  for (const problem of dashboard.dataQualityProblems) {
    console.log(`  ${problem}`);
  }

  const snapshot = await tracker.persistSnapshot();
  console.log(`\nAsynchronous snapshot size: ${snapshot.length} bytes`);

  try {
    tracker.recordExpense(
      new Expense({
        id: "EXP-JS-006",
        projectId: "PRJ-2026-002",
        category: CostCategory.CLOUD,
        description: "Invalid negative adjustment",
        amount: -100,
        expenseDate: "2026-04-01",
        vendor: "Cloud Provider"
      })
    );
  } catch (error) {
    if (error instanceof CostValidationError) {
      console.log(`\nValidation correctly rejected input: ${error.message}`);
    } else {
      throw error;
    }
  }
}

main().catch(error => {
  console.error(`Cost tracking execution failed: ${error.message}`);
  process.exitCode = 1;
});
