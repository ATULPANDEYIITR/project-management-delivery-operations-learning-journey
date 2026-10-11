"use strict";

/*
 * Project Cost Management
 *
 * This Node.js program models a project cost ledger, budget controls,
 * commitments, forecasts, variance analysis, and earned-value metrics.
 *
 * It intentionally uses JavaScript-specific mechanisms such as Map,
 * async file operations, object validation, and event-driven cost alerts.
 */

const fs = require("node:fs/promises");
const EventEmitter = require("node:events");

const COST_TYPES = Object.freeze({
  LABOR: "labor",
  MATERIAL: "material",
  EQUIPMENT: "equipment",
  SOFTWARE: "software",
  TRAVEL: "travel",
  SUBCONTRACT: "subcontract",
  OVERHEAD: "overhead",
  CONTINGENCY: "contingency",
});

const CLASSIFICATIONS = Object.freeze({
  DIRECT: "direct",
  INDIRECT: "indirect",
});

const roundMoney = (value) =>
  Math.round((Number(value) + Number.EPSILON) * 100) / 100;

function assertNonNegative(value, fieldName) {
  if (!Number.isFinite(value) || value < 0) {
    throw new RangeError(`${fieldName} must be a finite non-negative number.`);
  }
}

function createCostItem({
  name,
  type,
  classification,
  planned,
  actual,
  committed = 0,
}) {
  if (!name || typeof name !== "string") {
    throw new TypeError("Cost item name is required.");
  }

  if (!Object.values(COST_TYPES).includes(type)) {
    throw new TypeError(`Unsupported cost type: ${type}`);
  }

  if (!Object.values(CLASSIFICATIONS).includes(classification)) {
    throw new TypeError(`Unsupported classification: ${classification}`);
  }

  for (const [field, value] of Object.entries({
    planned,
    actual,
    committed,
  })) {
    assertNonNegative(value, field);
  }

  return Object.freeze({
    name,
    type,
    classification,
    planned: roundMoney(planned),
    actual: roundMoney(actual),
    committed: roundMoney(committed),
  });
}

class CostAlertBus extends EventEmitter {}

class ProjectCostManager {
  constructor({ projectName, approvedBudget, managementReserve = 0 }) {
    if (!projectName) {
      throw new TypeError("Project name is required.");
    }

    assertNonNegative(approvedBudget, "approvedBudget");
    assertNonNegative(managementReserve, "managementReserve");

    this.projectName = projectName;
    this.approvedBudget = roundMoney(approvedBudget);
    this.managementReserve = roundMoney(managementReserve);
    this.costItems = [];
    this.alerts = new CostAlertBus();

    this.alerts.on("thresholdExceeded", (event) => {
      console.log(
        `[COST ALERT] ${event.project}: ${event.utilization.toFixed(2)}% ` +
          `of approved budget has been consumed.`
      );
    });

    this.alerts.on("forecastRisk", (event) => {
      console.log(
        `[FORECAST ALERT] Expected completion cost ${event.forecast.toFixed(
          2
        )} exceeds the approved budget by ${event.excess.toFixed(2)}.`
      );
    });
  }

  addCostItem(item) {
    this.costItems.push(item);
    this.evaluateControls();
  }

  get plannedCost() {
    return roundMoney(
      this.costItems.reduce((total, item) => total + item.planned, 0)
    );
  }

  get actualCost() {
    return roundMoney(
      this.costItems.reduce((total, item) => total + item.actual, 0)
    );
  }

  get committedCost() {
    return roundMoney(
      this.costItems.reduce((total, item) => total + item.committed, 0)
    );
  }

  get forecastAtCompletion() {
    return roundMoney(this.actualCost + this.committedCost);
  }

  get remainingBudget() {
    return roundMoney(this.approvedBudget - this.actualCost);
  }

  get variance() {
    return roundMoney(this.approvedBudget - this.actualCost);
  }

  get utilization() {
    if (this.approvedBudget === 0) return 0;
    return (this.actualCost / this.approvedBudget) * 100;
  }

  costByType() {
    const totals = new Map();

    for (const item of this.costItems) {
      totals.set(
        item.type,
        roundMoney((totals.get(item.type) ?? 0) + item.actual)
      );
    }

    return Object.fromEntries(totals);
  }

  directAndIndirectCosts() {
    return this.costItems.reduce(
      (result, item) => {
        result[item.classification] = roundMoney(
          result[item.classification] + item.actual
        );
        return result;
      },
      {
        [CLASSIFICATIONS.DIRECT]: 0,
        [CLASSIFICATIONS.INDIRECT]: 0,
      }
    );
  }

  evaluateControls() {
    const utilization = this.utilization;

    if (utilization >= 90) {
      this.alerts.emit("thresholdExceeded", {
        project: this.projectName,
        utilization,
      });
    }

    if (this.forecastAtCompletion > this.approvedBudget) {
      this.alerts.emit("forecastRisk", {
        project: this.projectName,
        forecast: this.forecastAtCompletion,
        excess: this.forecastAtCompletion - this.approvedBudget,
      });
    }
  }

  get status() {
    if (this.actualCost > this.approvedBudget) return "OVER_BUDGET";
    if (this.forecastAtCompletion > this.approvedBudget) {
      return "FORECAST_OVER_BUDGET";
    }
    if (this.utilization >= 90) return "HIGH_UTILIZATION";
    if (this.utilization >= 75) return "WATCH";
    return "WITHIN_PLAN";
  }

  report() {
    return {
      projectName: this.projectName,
      approvedBudget: this.approvedBudget,
      managementReserve: this.managementReserve,
      plannedCost: this.plannedCost,
      actualCost: this.actualCost,
      committedCost: this.committedCost,
      forecastAtCompletion: this.forecastAtCompletion,
      remainingBudget: this.remainingBudget,
      variance: this.variance,
      utilizationPercent: roundMoney(this.utilization),
      status: this.status,
      costByType: this.costByType(),
      directAndIndirect: this.directAndIndirectCosts(),
    };
  }
}

function earnedValue({
  budgetAtCompletion,
  plannedValue,
  earnedValue,
  actualCost,
}) {
  assertNonNegative(budgetAtCompletion, "budgetAtCompletion");
  assertNonNegative(plannedValue, "plannedValue");
  assertNonNegative(earnedValue, "earnedValue");
  assertNonNegative(actualCost, "actualCost");

  const cpi = actualCost === 0 ? null : earnedValue / actualCost;
  const spi = plannedValue === 0 ? null : earnedValue / plannedValue;
  const eac = cpi && cpi > 0 ? budgetAtCompletion / cpi : null;

  return {
    bac: roundMoney(budgetAtCompletion),
    pv: roundMoney(plannedValue),
    ev: roundMoney(earnedValue),
    ac: roundMoney(actualCost),
    cpi: cpi === null ? null : roundMoney(cpi),
    spi: spi === null ? null : roundMoney(spi),
    eac: eac === null ? null : roundMoney(eac),
    vac: eac === null ? null : roundMoney(budgetAtCompletion - eac),
  };
}

function createExampleProject() {
  const manager = new ProjectCostManager({
    projectName: "Enterprise Reporting Platform",
    approvedBudget: 250000,
    managementReserve: 20000,
  });

  manager.addCostItem(
    createCostItem({
      name: "Project management",
      type: COST_TYPES.LABOR,
      classification: CLASSIFICATIONS.DIRECT,
      planned: 30000,
      actual: 28000,
      committed: 2000,
    })
  );

  manager.addCostItem(
    createCostItem({
      name: "Application development",
      type: COST_TYPES.LABOR,
      classification: CLASSIFICATIONS.DIRECT,
      planned: 90000,
      actual: 96000,
      committed: 12000,
    })
  );

  manager.addCostItem(
    createCostItem({
      name: "Cloud platform",
      type: COST_TYPES.EQUIPMENT,
      classification: CLASSIFICATIONS.DIRECT,
      planned: 42000,
      actual: 39000,
      committed: 7000,
    })
  );

  manager.addCostItem(
    createCostItem({
      name: "Database subscription",
      type: COST_TYPES.SOFTWARE,
      classification: CLASSIFICATIONS.DIRECT,
      planned: 28000,
      actual: 30000,
      committed: 0,
    })
  );

  manager.addCostItem(
    createCostItem({
      name: "Implementation partner",
      type: COST_TYPES.SUBCONTRACT,
      classification: CLASSIFICATIONS.DIRECT,
      planned: 32000,
      actual: 27000,
      committed: 15000,
    })
  );

  manager.addCostItem(
    createCostItem({
      name: "Corporate overhead",
      type: COST_TYPES.OVERHEAD,
      classification: CLASSIFICATIONS.INDIRECT,
      planned: 12000,
      actual: 10500,
      committed: 0,
    })
  );

  return manager;
}

async function persistReport(manager) {
  const outputDirectory = "./cost-management-output";
  await fs.mkdir(outputDirectory, { recursive: true });

  const report = manager.report();

  await fs.writeFile(
    `${outputDirectory}/cost-report.json`,
    JSON.stringify(report, null, 2),
    "utf8"
  );

  const csvRows = [
    "name,type,classification,planned,actual,committed,variance",
    ...manager.costItems.map((item) =>
      [
        item.name,
        item.type,
        item.classification,
        item.planned,
        item.actual,
        item.committed,
        roundMoney(item.planned - item.actual),
      ]
        .map((value) => `"${String(value).replaceAll('"', '""')}"`)
        .join(",")
    ),
  ];

  await fs.writeFile(
    `${outputDirectory}/cost-items.csv`,
    csvRows.join("\n"),
    "utf8"
  );
}

async function main() {
  const manager = createExampleProject();

  console.log("\n=== PROJECT COST MANAGEMENT ===");
  console.table(manager.report());

  console.log("\n=== COST DISTRIBUTION ===");
  console.table(manager.costByType());

  console.log("\n=== EARNED VALUE ===");
  console.table(
    earnedValue({
      budgetAtCompletion: manager.approvedBudget,
      plannedValue: 130000,
      earnedValue: 118000,
      actualCost: manager.actualCost,
    })
  );

  try {
    createCostItem({
      name: "Invalid expense",
      type: COST_TYPES.TRAVEL,
      classification: CLASSIFICATIONS.DIRECT,
      planned: -100,
      actual: 0,
    });
  } catch (error) {
    console.log(`Validation rejected invalid cost: ${error.message}`);
  }

  await persistReport(manager);
  console.log("\nReports saved in ./cost-management-output/");
}

main().catch((error) => {
  console.error("Cost management run failed:", error.message);
  process.exitCode = 1;
});
