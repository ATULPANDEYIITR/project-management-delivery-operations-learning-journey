"use strict";

const { EventEmitter } = require("node:events");

const RESPONSIBILITIES = new Set(["R", "A", "C", "I"]);

class RaciError extends Error {
    constructor(message) {
        super(message);
        this.name = "RaciError";
    }
}

class RaciWorkspace extends EventEmitter {
    constructor({ projectId, projectName, auditSink = async () => {} }) {
        super();

        if (!projectId?.trim() || !projectName?.trim()) {
            throw new RaciError("Project ID and name are required.");
        }
        if (typeof auditSink !== "function") {
            throw new RaciError("auditSink must be an asynchronous function.");
        }

        this.projectId = projectId;
        this.projectName = projectName;
        this.roles = new Map();
        this.tasks = new Map();
        this.assignments = new Map();
        this.auditSink = auditSink;
        this.status = "DRAFT";
        this.version = 1;
    }

    ensureDraft() {
        if (this.status !== "DRAFT") {
            throw new RaciError("The published matrix is read-only.");
        }
    }

    addRole(role) {
        this.ensureDraft();

        if (!role || typeof role.code !== "string" ||
            !role.code.trim() || typeof role.name !== "string" ||
            !role.name.trim()) {
            throw new RaciError("A role requires a non-empty code and name.");
        }

        if (this.roles.has(role.code)) {
            throw new RaciError(`Role already exists: ${role.code}`);
        }

        const capacity = role.maxResponsibleTasks ?? null;
        if (capacity !== null &&
            (!Number.isInteger(capacity) || capacity < 0)) {
            throw new RaciError("Role capacity must be a non-negative integer.");
        }

        this.roles.set(role.code, Object.freeze({
            code: role.code,
            name: role.name,
            department: role.department ?? "Unspecified",
            maxResponsibleTasks: capacity
        }));
    }

    addTask(task) {
        this.ensureDraft();

        if (!task || typeof task.id !== "string" || !task.id.trim() ||
            typeof task.title !== "string" || !task.title.trim()) {
            throw new RaciError("A task requires a non-empty ID and title.");
        }

        if (this.tasks.has(task.id)) {
            throw new RaciError(`Task already exists: ${task.id}`);
        }

        this.tasks.set(task.id, Object.freeze({
            id: task.id,
            title: task.title,
            securitySensitive: Boolean(task.securitySensitive)
        }));
        this.assignments.set(task.id, new Map());
    }

    applyAssignments(changes, { replace = false } = {}) {
        this.ensureDraft();

        if (!Array.isArray(changes) || changes.length === 0) {
            throw new RaciError("At least one assignment change is required.");
        }

        // Stage changes in cloned maps. A validation error leaves live state intact.
        const staged = new Map(
            [...this.assignments].map(([taskId, row]) => [
                taskId,
                new Map(row)
            ])
        );

        for (const change of changes) {
            const { taskId, roleCode, responsibility } = change ?? {};

            if (!this.tasks.has(taskId)) {
                throw new RaciError(`Unknown task: ${taskId}`);
            }
            if (!this.roles.has(roleCode)) {
                throw new RaciError(`Unknown role: ${roleCode}`);
            }
            if (!RESPONSIBILITIES.has(responsibility)) {
                throw new RaciError("Responsibility must be R, A, C, or I.");
            }

            const row = staged.get(taskId);
            if (row.has(roleCode) && !replace) {
                throw new RaciError(
                    `${roleCode} already has an assignment for ${taskId}.`
                );
            }

            row.set(roleCode, responsibility);
        }

        this.assignments = staged;

        for (const change of changes) {
            this.emit("assignment.changed", Object.freeze({
                projectId: this.projectId,
                ...change
            }));
        }
    }

    assign(taskId, roleCode, responsibility, options = {}) {
        this.applyAssignments(
            [{ taskId, roleCode, responsibility }],
            options
        );
    }

    validate() {
        const errors = [];

        if (this.tasks.size === 0) {
            errors.push("The matrix contains no tasks.");
        }

        for (const [taskId, task] of this.tasks) {
            const row = this.assignments.get(taskId) ?? new Map();
            const values = [...row.values()];
            const accountable = values.filter(code => code === "A").length;
            const responsible = values.filter(code => code === "R").length;

            if (accountable !== 1) {
                errors.push(
                    `${taskId}: exactly one Accountable assignment is required; found ${accountable}.`
                );
            }

            if (responsible < 1) {
                errors.push(`${taskId}: at least one Responsible assignment is required.`);
            }

            if (task.securitySensitive &&
                row.get("SECURITY_OFFICER") !== "C") {
                errors.push(
                    `${taskId}: SECURITY_OFFICER must be Consulted.`
                );
            }
        }

        return errors;
    }

    workloadWarnings() {
        const workload = new Map(
            [...this.roles.keys()].map(code => [code, 0])
        );

        for (const row of this.assignments.values()) {
            for (const [roleCode, responsibility] of row) {
                if (responsibility === "R") {
                    workload.set(roleCode, workload.get(roleCode) + 1);
                }
            }
        }

        const warnings = [];
        for (const [roleCode, role] of this.roles) {
            const capacity = role.maxResponsibleTasks;
            const count = workload.get(roleCode);

            if (capacity !== null && count > capacity) {
                warnings.push(
                    `${roleCode}: ${count} Responsible assignments exceed capacity ${capacity}.`
                );
            }
        }

        return warnings;
    }

    roleWorkload() {
        const result = {};

        for (const roleCode of this.roles.keys()) {
            result[roleCode] = { R: 0, A: 0, C: 0, I: 0 };

            for (const row of this.assignments.values()) {
                const responsibility = row.get(roleCode);
                if (responsibility) {
                    result[roleCode][responsibility] += 1;
                }
            }
        }

        return result;
    }

    render() {
        const roleCodes = [...this.roles.keys()];
        const headers = ["Task", ...roleCodes];
        const rows = [];

        for (const [taskId, task] of this.tasks) {
            const assignments = this.assignments.get(taskId) ?? new Map();
            rows.push([
                `${taskId}: ${task.title}`,
                ...roleCodes.map(code => assignments.get(code) ?? "-")
            ]);
        }

        const widths = headers.map((header, index) =>
            Math.max(
                header.length,
                ...rows.map(row => row[index].length)
            )
        );

        const format = values => values
            .map((value, index) => value.padEnd(widths[index]))
            .join(" | ");

        const separator = widths.map(width => "-".repeat(width)).join("-+-");
        return [format(headers), separator, ...rows.map(format)].join("\n");
    }

    async publish(actor) {
        this.ensureDraft();

        if (!actor?.trim()) {
            throw new RaciError("A publishing actor must be identified.");
        }

        const errors = this.validate();
        if (errors.length > 0) {
            throw new RaciError(
                `Publication blocked:\n${errors.map(error => `- ${error}`).join("\n")}`
            );
        }

        const event = Object.freeze({
            type: "MATRIX_PUBLISHED",
            projectId: this.projectId,
            version: this.version + 1,
            actor,
            timestamp: new Date().toISOString()
        });

        // Persist the audit event before changing the state.
        // A failed audit operation leaves the matrix in DRAFT.
        await this.auditSink(event);

        this.status = "ACTIVE";
        this.version += 1;
        this.emit("matrix.published", event);

        return event;
    }
}

function addCloudMigrationData(workspace) {
    const roles = [
        ["SPONSOR", "Project Sponsor", "Executive Office", null],
        ["PM", "Project Manager", "Program Management", null],
        ["ARCHITECT", "Cloud Architect", "Technology", 2],
        ["SECURITY_OFFICER", "Security Officer", "Information Security", null],
        ["QA", "Quality Lead", "Quality Assurance", null],
        ["OPERATIONS", "Operations Lead", "IT Operations", 2]
    ];

    for (const [code, name, department, maxResponsibleTasks] of roles) {
        workspace.addRole({
            code,
            name,
            department,
            maxResponsibleTasks
        });
    }

    const tasks = [
        { id: "T1", title: "Inventory and discovery" },
        {
            id: "T2",
            title: "Target architecture approval",
            securitySensitive: true
        },
        {
            id: "T3",
            title: "Production migration",
            securitySensitive: true
        },
        { id: "T4", title: "Acceptance testing" }
    ];

    for (const task of tasks) {
        workspace.addTask(task);
    }

    const changes = [
        ["T1", "SPONSOR", "A"],
        ["T1", "PM", "R"],
        ["T1", "ARCHITECT", "C"],
        ["T1", "SECURITY_OFFICER", "I"],
        ["T1", "QA", "I"],
        ["T1", "OPERATIONS", "C"],

        ["T2", "SPONSOR", "I"],
        ["T2", "PM", "A"],
        ["T2", "ARCHITECT", "R"],
        ["T2", "SECURITY_OFFICER", "C"],
        ["T2", "QA", "I"],
        ["T2", "OPERATIONS", "C"],

        ["T3", "SPONSOR", "I"],
        ["T3", "PM", "A"],
        ["T3", "ARCHITECT", "R"],
        ["T3", "SECURITY_OFFICER", "C"],
        ["T3", "QA", "I"],
        ["T3", "OPERATIONS", "R"],

        ["T4", "SPONSOR", "I"],
        ["T4", "PM", "A"],
        ["T4", "ARCHITECT", "I"],
        ["T4", "SECURITY_OFFICER", "I"],
        ["T4", "QA", "R"],
        ["T4", "OPERATIONS", "C"]
    ].map(([taskId, roleCode, responsibility]) => ({
        taskId,
        roleCode,
        responsibility
    }));

    workspace.applyAssignments(changes);
}

async function demonstrateInvalidMatrix() {
    const incomplete = new RaciWorkspace({
        projectId: "PRJ-200",
        projectName: "Incomplete Payment Platform"
    });

    incomplete.addRole({ code: "PM", name: "Project Manager" });
    incomplete.addRole({ code: "DEV", name: "Developer" });
    incomplete.addRole({
        code: "SECURITY_OFFICER",
        name: "Security Officer"
    });
    incomplete.addTask({
        id: "P1",
        title: "Payment security review",
        securitySensitive: true
    });

    incomplete.applyAssignments([
        { taskId: "P1", roleCode: "DEV", responsibility: "R" },
        {
            taskId: "P1",
            roleCode: "SECURITY_OFFICER",
            responsibility: "I"
        }
    ]);

    try {
        await incomplete.publish("PROJECT_MANAGER");
    } catch (error) {
        console.log("\nExpected publication failure:");
        console.log(error.message);
    }
}

async function main() {
    const auditRecords = [];

    const workspace = new RaciWorkspace({
        projectId: "PRJ-100",
        projectName: "Cloud Infrastructure Migration",
        auditSink: async event => {
            auditRecords.push(event);
        }
    });

    workspace.on("assignment.changed", event => {
        console.log(
            `Assignment event: ${event.taskId}/${event.roleCode} = ${event.responsibility}`
        );
    });

    workspace.on("matrix.published", event => {
        console.log(`Published event: version ${event.version}`);
    });

    addCloudMigrationData(workspace);

    const errors = workspace.validate();
    if (errors.length > 0) {
        throw new RaciError(errors.join("\n"));
    }

    console.log("\nRACI Matrix");
    console.log(workspace.render());

    console.log("\nWorkload warnings:");
    console.log(workspace.workloadWarnings().join("\n") || "None");

    console.log("\nRole workload:");
    console.log(JSON.stringify(workspace.roleWorkload(), null, 2));

    await workspace.publish("PROGRAM_GOVERNANCE_BOARD");

    console.log(`\nStatus: ${workspace.status}`);
    console.log(`Version: ${workspace.version}`);
    console.log(`Audit records: ${auditRecords.length}`);

    try {
        workspace.assign("T1", "PM", "A", { replace: true });
    } catch (error) {
        console.log(`\nExpected modification failure: ${error.message}`);
    }

    // Invalid batch updates are atomic: no partial assignment is committed.
    const previousCount = workspace.assignments.get("T1").size;
    try {
        const draft = new RaciWorkspace({
            projectId: "PRJ-300",
            projectName: "Atomicity demonstration"
        });
        draft.addRole({ code: "DEV", name: "Developer" });
        draft.addTask({ id: "D1", title: "Build component" });
        draft.applyAssignments([
            { taskId: "D1", roleCode: "DEV", responsibility: "R" },
            { taskId: "UNKNOWN", roleCode: "DEV", responsibility: "I" }
        ]);
    } catch (error) {
        console.log(`Atomic batch rejected: ${error.message}`);
    }
    console.log(`Published T1 assignment count remains ${previousCount}.`);

    await demonstrateInvalidMatrix();
}

if (require.main === module) {
    main().catch(error => {
        console.error(`Execution failed: ${error.message}`);
        process.exitCode = 1;
    });
}
