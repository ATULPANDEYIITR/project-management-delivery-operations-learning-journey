"use strict";

/*
 * Event-driven project output quality control.
 * Run with Node.js 18 or later: node quality_control.js
 */

const { randomUUID } = require("node:crypto");
const fs = require("node:fs/promises");
const path = require("node:path");

const Severity = Object.freeze({
  CRITICAL: "critical",
  MAJOR: "major",
  MINOR: "minor",
  OBSERVATION: "observation",
});

const Status = Object.freeze({
  DRAFT: "draft",
  INSPECTION: "inspection",
  REWORK: "rework",
  RELEASED: "released",
  REJECTED: "rejected",
});

const FindingStatus = Object.freeze({
  OPEN: "open",
  FIXED: "fixed",
  VERIFIED: "verified",
  ACCEPTED: "accepted",
});

class QualityError extends Error {
  constructor(message) {
    super(message);
    this.name = "QualityError";
  }
}

class EventBus {
  #listeners = new Map();

  on(eventType, listener) {
    if (typeof listener !== "function") {
      throw new QualityError("Listener must be a function.");
    }
    if (!this.#listeners.has(eventType)) {
      this.#listeners.set(eventType, new Set());
    }
    this.#listeners.get(eventType).add(listener);
    return () => this.#listeners.get(eventType)?.delete(listener);
  }

  emit(event) {
    const listeners = this.#listeners.get(event.type);
    if (!listeners) return;
    for (const listener of [...listeners]) {
      try {
        listener(Object.freeze({ ...event }));
      } catch (error) {
        // An observer failure must not silently reverse a completed domain change.
        process.stderr.write(`Observer failure: ${error.message}\n`);
      }
    }
  }
}

class Finding {
  constructor({ requirementId, severity, message, evidence = "" }) {
    if (!Object.values(Severity).includes(severity)) {
      throw new QualityError(`Unknown severity: ${severity}`);
    }
    if (!requirementId || !message.trim()) {
      throw new QualityError("Finding requirement and message are required.");
    }
    this.id = randomUUID();
    this.requirementId = requirementId;
    this.severity = severity;
    this.message = message;
    this.evidence = evidence;
    this.status = FindingStatus.OPEN;
  }

  transition(nextStatus) {
    const allowed = {
      [FindingStatus.OPEN]: [FindingStatus.FIXED, FindingStatus.ACCEPTED],
      [FindingStatus.FIXED]: [FindingStatus.VERIFIED, FindingStatus.OPEN],
      [FindingStatus.ACCEPTED]: [FindingStatus.OPEN],
      [FindingStatus.VERIFIED]: [],
    };
    if (!allowed[this.status].includes(nextStatus)) {
      throw new QualityError(
        `Invalid finding transition: ${this.status} -> ${nextStatus}`
      );
    }
    this.status = nextStatus;
  }
}

class OutputInspector {
  constructor(requirements) {
    if (!Array.isArray(requirements) || requirements.length === 0) {
      throw new QualityError("At least one requirement is required.");
    }
    this.requirements = new Map();
    for (const requirement of requirements) {
      if (
        !requirement.id ||
        !requirement.description ||
        this.requirements.has(requirement.id)
      ) {
        throw new QualityError("Requirements must be unique and complete.");
      }
      this.requirements.set(requirement.id, Object.freeze({
        id: requirement.id,
        description: requirement.description,
        mandatory: requirement.mandatory !== false,
      }));
    }
  }

  inspect(results) {
    if (!(results instanceof Map)) {
      throw new QualityError("Inspection results must be a Map.");
    }
    for (const id of results.keys()) {
      if (!this.requirements.has(id)) {
        throw new QualityError(`Unknown requirement: ${id}`);
      }
    }

    const findings = [];
    for (const requirement of this.requirements.values()) {
      const result = results.get(requirement.id);
      if (result === undefined) {
        if (requirement.mandatory) {
          findings.push(new Finding({
            requirementId: requirement.id,
            severity: Severity.MAJOR,
            message: "Mandatory requirement was not checked.",
          }));
        }
        continue;
      }

      if (typeof result.passed !== "boolean") {
        throw new QualityError(`Invalid result for ${requirement.id}.`);
      }

      if (!result.passed) {
        findings.push(new Finding({
          requirementId: requirement.id,
          severity: requirement.mandatory ? Severity.MAJOR : Severity.MINOR,
          message: requirement.description,
          evidence: String(result.evidence ?? ""),
        }));
      }
    }
    return findings;
  }
}

class QualityWorkflow {
  constructor({ id, name, version, requirements, events = new EventBus() }) {
    if (!id || !name || !version) {
      throw new QualityError("Output ID, name, and version are required.");
    }
    this.id = id;
    this.name = name;
    this.version = version;
    this.status = Status.DRAFT;
    this.inspector = new OutputInspector(requirements);
    this.events = events;
    this.inspections = [];
    this.audit = [];
  }

  #record(type, actor, details = {}) {
    const event = {
      type,
      outputId: this.id,
      actor,
      timestamp: new Date().toISOString(),
      details,
    };
    this.audit.push(event);
    this.events.emit(event);
  }

  inspect(actor, results) {
    if ([Status.RELEASED, Status.REJECTED].includes(this.status)) {
      throw new QualityError("Terminal output cannot be reinspected.");
    }
    if (!actor?.trim()) throw new QualityError("Inspector is required.");

    const findings = this.inspector.inspect(results);
    const passed = !findings.some(
      finding =>
        finding.status === FindingStatus.OPEN &&
        [Severity.CRITICAL, Severity.MAJOR].includes(finding.severity)
    );

    const inspection = Object.freeze({
      id: randomUUID(),
      inspector: actor,
      timestamp: new Date().toISOString(),
      findings,
      passed,
    });

    this.inspections.push(inspection);
    this.status = passed ? Status.INSPECTION : Status.REWORK;
    this.#record("inspection.completed", actor, {
      inspectionId: inspection.id,
      findingCount: findings.length,
      passed,
    });
    return inspection;
  }

  release(actor) {
    if (!this.inspections.length || this.status !== Status.INSPECTION) {
      throw new QualityError("A passing latest inspection is required.");
    }
    const unresolved = this.inspections.flatMap(i => i.findings).filter(
      finding =>
        finding.status === FindingStatus.OPEN &&
        [Severity.CRITICAL, Severity.MAJOR].includes(finding.severity)
    );
    if (unresolved.length) {
      throw new QualityError("Unresolved major findings block release.");
    }

    this.status = Status.RELEASED;
    this.#record("output.released", actor, { version: this.version });
  }

  reject(actor, reason) {
    if (this.status === Status.RELEASED) {
      throw new QualityError("Released output cannot be rejected retroactively.");
    }
    if (!reason?.trim()) throw new QualityError("Rejection reason is required.");
    this.status = Status.REJECTED;
    this.#record("output.rejected", actor, { reason });
  }

  report() {
    return {
      id: this.id,
      name: this.name,
      version: this.version,
      status: this.status,
      inspections: this.inspections.map(inspection => ({
        id: inspection.id,
        inspector: inspection.inspector,
        timestamp: inspection.timestamp,
        passed: inspection.passed,
        findings: inspection.findings.map(finding => ({
          id: finding.id,
          requirementId: finding.requirementId,
          severity: finding.severity,
          message: finding.message,
          evidence: finding.evidence,
          status: finding.status,
        })),
      })),
      audit: this.audit,
    };
  }
}

function safeFilename(filename) {
  if (
    typeof filename !== "string" ||
    !filename.trim() ||
    filename === "." ||
    filename === ".." ||
    path.basename(filename) !== filename ||
    filename.includes("\0")
  ) {
    throw new QualityError("Unsafe artifact filename.");
  }
  return filename;
}

async function writeReport(workflow, destination) {
  const absolute = path.resolve(destination);
  const directory = path.dirname(absolute);
  await fs.mkdir(directory, { recursive: true });

  const temporary = `${absolute}.${randomUUID()}.tmp`;
  try {
    await fs.writeFile(
      temporary,
      JSON.stringify(workflow.report(), null, 2),
      { encoding: "utf8", flag: "wx", mode: 0o600 }
    );
    await fs.rename(temporary, absolute);
  } finally {
    await fs.rm(temporary, { force: true });
  }
}

function runTests() {
  const requirements = [
    { id: "Q1", description: "Required sections", mandatory: true },
    { id: "Q2", description: "Financial reconciliation", mandatory: true },
    { id: "Q3", description: "Visual formatting", mandatory: false },
  ];

  const inspector = new OutputInspector(requirements);
  const failed = inspector.inspect(new Map([
    ["Q1", { passed: true }],
    ["Q2", { passed: false, evidence: "Difference: 150.00" }],
    ["Q3", { passed: true }],
  ]));
  if (failed.length !== 1 || failed[0].severity !== Severity.MAJOR) {
    throw new Error("Failed inspection test.");
  }

  let rejectedUnknownRequirement = false;
  try {
    inspector.inspect(new Map([["Q404", { passed: true }]]));
  } catch (error) {
    rejectedUnknownRequirement = error instanceof QualityError;
  }
  if (!rejectedUnknownRequirement) throw new Error("Unknown ID test failed.");

  let rejectedUnsafeFilename = false;
  try {
    safeFilename("../report.pdf");
  } catch (error) {
    rejectedUnsafeFilename = error instanceof QualityError;
  }
  if (!rejectedUnsafeFilename) throw new Error("Path validation test failed.");

  process.stdout.write("Validation tests passed.\n");
}

async function main() {
  runTests();

  const events = new EventBus();
  events.on("inspection.completed", event => {
    process.stdout.write(
      `Inspection ${event.details.passed ? "passed" : "failed"}\n`
    );
  });

  const workflow = new QualityWorkflow({
    id: "OUT-2026-014",
    name: "Quarterly Operations Report",
    version: "2.0",
    requirements: [
      { id: "Q1", description: "All required sections are present" },
      { id: "Q2", description: "Figures reconcile with source data" },
      { id: "Q3", description: "File opens and is readable" },
    ],
    events,
  });

  workflow.inspect("quality-reviewer", new Map([
    ["Q1", { passed: true, evidence: "Checklist completed" }],
    ["Q2", {
      passed: false,
      evidence: "Output total 50100; source total 49950",
    }],
    ["Q3", { passed: true, evidence: "File opened successfully" }],
  ]));

  try {
    workflow.release("quality-manager");
  } catch (error) {
    process.stdout.write(`Release blocked: ${error.message}\n`);
  }

  const reportPath = path.join(
    process.cwd(),
    safeFilename("quality-report.json")
  );
  await writeReport(workflow, reportPath);
  process.stdout.write(`Status: ${workflow.status}\n`);
  process.stdout.write(`Report written to: ${reportPath}\n`);
}

main().catch(error => {
  process.stderr.write(`Fatal error: ${error.message}\n`);
  process.exitCode = 1;
});
