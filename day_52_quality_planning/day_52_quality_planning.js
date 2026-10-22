"use strict";

/*
 * Quality Planning model for a software delivery project.
 * The implementation separates:
 * - quality requirements: what quality must be achieved
 * - quality checks: evidence showing whether requirements are met
 * - quality risks: threats to planned quality
 * - quality gates: rules deciding whether the release is ready
 *
 * Run with Node.js 18+:
 * node quality-planning.js
 */

const fs = require("node:fs/promises");

const RequirementStatus = Object.freeze({
  PLANNED: "planned",
  VALIDATED: "validated",
  FAILED: "failed",
  DEFERRED: "deferred"
});

const RiskLevel = Object.freeze({
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  CRITICAL: "critical"
});

class ValidationError extends Error {}

class QualityRequirement {
  constructor({ id, description, metric, target, priority, verificationMethod }) {
    if (!id || !description || !metric || !verificationMethod) {
      throw new ValidationError("Requirement fields cannot be empty.");
    }
    if (!Number.isFinite(target) || target < 0 || target > 100) {
      throw new ValidationError("Requirement target must be between 0 and 100.");
    }
    if (!Number.isInteger(priority) || priority < 1 || priority > 5) {
      throw new ValidationError("Priority must be an integer from 1 to 5.");
    }

    this.id = id;
    this.description = description;
    this.metric = metric;
    this.target = target;
    this.priority = priority;
    this.verificationMethod = verificationMethod;
  }
}

class QualityCheck {
  constructor({ requirementId, observedValue, passed, evidence }) {
    if (!requirementId || !evidence) {
      throw new ValidationError("A check requires a requirement ID and evidence.");
    }
    if (!Number.isFinite(observedValue) || observedValue < 0 || observedValue > 100) {
      throw new ValidationError("Observed quality value must be between 0 and 100.");
    }

    this.requirementId = requirementId;
    this.observedValue = observedValue;
    this.passed = Boolean(passed);
    this.evidence = evidence;
    this.checkedAt = new Date().toISOString();
  }
}

class QualityRisk {
  constructor({ id, description, probability, impact, mitigation }) {
    if (!id || !description || !mitigation) {
      throw new ValidationError("Risk fields cannot be empty.");
    }
    if (![probability, impact].every(Number.isFinite)) {
      throw new ValidationError("Risk probability and impact must be numeric.");
    }
    if (probability < 0 || probability > 1 || impact < 0 || impact > 1) {
      throw new ValidationError("Risk probability and impact must be between 0 and 1.");
    }

    this.id = id;
    this.description = description;
    this.probability = probability;
    this.impact = impact;
    this.mitigation = mitigation;
  }

  get score() {
    return this.probability * this.impact;
  }

  get level() {
    if (this.score >= 0.75) return RiskLevel.CRITICAL;
    if (this.score >= 0.50) return RiskLevel.HIGH;
    if (this.score >= 0.25) return RiskLevel.MEDIUM;
    return RiskLevel.LOW;
  }
}

class QualityPlanningEngine {
  #requirements = new Map();
  #checks = [];
  #risks = [];

  constructor(projectName) {
    if (!projectName?.trim()) {
      throw new ValidationError("Project name is required.");
    }
    this.projectName = projectName;
  }

  addRequirement(requirement) {
    if (this.#requirements.has(requirement.id)) {
      throw new ValidationError(`Duplicate requirement: ${requirement.id}`);
    }
    this.#requirements.set(requirement.id, requirement);
  }

  recordCheck(check) {
    if (!this.#requirements.has(check.requirementId)) {
      throw new ValidationError(
        `Cannot record evidence for unknown requirement ${check.requirementId}`
      );
    }
    this.#checks.push(check);
  }

  addRisk(risk) {
    this.#risks.push(risk);
  }

  latestCheck(requirementId) {
    const matches = this.#checks
      .filter(check => check.requirementId === requirementId)
      .sort((a, b) => b.checkedAt.localeCompare(a.checkedAt));

    return matches[0] ?? null;
  }

  evaluate() {
    if (this.#requirements.size === 0) {
      return {
        ready: false,
        score: 0,
        reason: "No quality requirements have been planned."
      };
    }

    let weightedScore = 0;
    let totalWeight = 0;
    const missing = [];
    const failed = [];

    for (const requirement of this.#requirements.values()) {
      const check = this.latestCheck(requirement.id);

      if (!check) {
        missing.push(requirement.id);
        continue;
      }

      const achievement = Math.min(
        check.observedValue / requirement.target,
        1
      );

      weightedScore += achievement * requirement.priority;
      totalWeight += requirement.priority;

      if (!check.passed) {
        failed.push(requirement.id);
      }
    }

    const criticalRisks = this.#risks
      .filter(risk => risk.level === RiskLevel.CRITICAL)
      .map(risk => risk.id);

    const score = totalWeight === 0
      ? 0
      : Number(((weightedScore / totalWeight) * 100).toFixed(2));

    return {
      ready: missing.length === 0 &&
             failed.length === 0 &&
             criticalRisks.length === 0,
      score,
      missing,
      failed,
      criticalRisks
    };
  }

  toJSON() {
    return {
      project: this.projectName,
      requirements: [...this.#requirements.values()],
      checks: this.#checks,
      risks: this.#risks.map(risk => ({
        id: risk.id,
        description: risk.description,
        probability: risk.probability,
        impact: risk.impact,
        score: Number(risk.score.toFixed(3)),
        level: risk.level,
        mitigation: risk.mitigation
      }))
    };
  }

  async save(filePath) {
    await fs.writeFile(
      filePath,
      JSON.stringify(this.toJSON(), null, 2),
      "utf8"
    );
  }
}

function buildQualityPlan() {
  const engine = new QualityPlanningEngine("Payment Reconciliation Service");

  [
    new QualityRequirement({
      id: "QR-101",
      description: "Critical reconciliation paths have sufficient automated test coverage.",
      metric: "coverage_percent",
      target: 90,
      priority: 5,
      verificationMethod: "CI coverage report"
    }),
    new QualityRequirement({
      id: "QR-102",
      description: "Reconciliation operations meet the agreed response-time objective.",
      metric: "latency_compliance_percent",
      target: 95,
      priority: 5,
      verificationMethod: "Load test"
    }),
    new QualityRequirement({
      id: "QR-103",
      description: "No unresolved critical data-integrity defects remain.",
      metric: "critical_defect_free_percent",
      target: 100,
      priority: 5,
      verificationMethod: "Defect audit"
    }),
    new QualityRequirement({
      id: "QR-104",
      description: "Financial input validation passes all security-focused tests.",
      metric: "validation_pass_percent",
      target: 100,
      priority: 4,
      verificationMethod: "Security regression suite"
    })
  ].forEach(requirement => engine.addRequirement(requirement));

  [
    new QualityCheck({
      requirementId: "QR-101",
      observedValue: 93,
      passed: true,
      evidence: "CI run 6021 reported 93% coverage."
    }),
    new QualityCheck({
      requirementId: "QR-102",
      observedValue: 96,
      passed: true,
      evidence: "Load test achieved target latency for 96% of requests."
    }),
    new QualityCheck({
      requirementId: "QR-103",
      observedValue: 100,
      passed: true,
      evidence: "Release audit found no critical integrity defects."
    }),
    new QualityCheck({
      requirementId: "QR-104",
      observedValue: 97,
      passed: false,
      evidence: "Three malformed financial payload tests failed."
    })
  ].forEach(check => engine.recordCheck(check));

  [
    new QualityRisk({
      id: "R-101",
      description: "Boundary-value validation may fail for unusual transaction amounts.",
      probability: 0.45,
      impact: 0.90,
      mitigation: "Expand boundary and malformed-input test cases."
    }),
    new QualityRisk({
      id: "R-102",
      description: "Peak reconciliation volume may increase processing latency.",
      probability: 0.30,
      impact: 0.70,
      mitigation: "Execute load tests against release candidates."
    })
  ].forEach(risk => engine.addRisk(risk));

  return engine;
}

async function main() {
  const engine = buildQualityPlan();
  const evaluation = engine.evaluate();

  console.log(`Project: ${engine.projectName}`);
  console.log(`Quality score: ${evaluation.score}%`);
  console.log(`Quality gate: ${evaluation.ready ? "PASS" : "BLOCKED"}`);

  if (evaluation.missing.length) {
    console.log(`Missing evidence: ${evaluation.missing.join(", ")}`);
  }

  if (evaluation.failed.length) {
    console.log(`Failed requirements: ${evaluation.failed.join(", ")}`);
  }

  if (evaluation.criticalRisks.length) {
    console.log(`Critical risks: ${evaluation.criticalRisks.join(", ")}`);
  }

  const outputFile = "quality-plan.json";
  await engine.save(outputFile);
  console.log(`Plan written to ${outputFile}`);

  console.log("\nRisk evaluation:");
  engine.toJSON().risks
    .sort((a, b) => b.score - a.score)
    .forEach(risk => {
      console.log(
        `${risk.id}: ${risk.level.toUpperCase()} ` +
        `(score ${risk.score}) - ${risk.mitigation}`
      );
    });
}

main().catch(error => {
  console.error(`Quality planning failed: ${error.message}`);
  process.exitCode = 1;
});
