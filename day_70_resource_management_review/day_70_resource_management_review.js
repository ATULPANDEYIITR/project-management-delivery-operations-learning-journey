"use strict";

/**
 * RESOURCE MANAGEMENT REVIEW
 * Team Management and Resource Allocation Review
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 *
 * Engineering focus:
 * - Event-driven resource management
 * - Immutable review decisions
 * - Map-based state management
 * - Capacity and utilization policies
 * - Skill matching
 * - Workload distribution
 * - Asynchronous review processing
 * - Audit events
 * - Action ownership and tracking
 */

const fs = require("node:fs/promises");
const path = require("node:path");
const { randomUUID } = require("node:crypto");
const EventEmitter = require("node:events");


const EmployeeStatus = Object.freeze({
    ACTIVE: "ACTIVE",
    ON_LEAVE: "ON_LEAVE",
    INACTIVE: "INACTIVE"
});

const ProjectStatus = Object.freeze({
    ACTIVE: "ACTIVE",
    ON_HOLD: "ON_HOLD",
    COMPLETED: "COMPLETED"
});

const ReviewStatus = Object.freeze({
    DRAFT: "DRAFT",
    UNDER_REVIEW: "UNDER_REVIEW",
    APPROVED: "APPROVED",
    REJECTED: "REJECTED"
});

const ActionStatus = Object.freeze({
    OPEN: "OPEN",
    IN_PROGRESS: "IN_PROGRESS",
    COMPLETED: "COMPLETED",
    CANCELLED: "CANCELLED"
});


class DomainError extends Error {
    constructor(message) {
        super(message);
        this.name = "DomainError";
    }
}


class ValidationError extends DomainError {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}


class CapacityError extends DomainError {
    constructor(message) {
        super(message);
        this.name = "CapacityError";
    }
}


class ReviewError extends DomainError {
    constructor(message) {
        super(message);
        this.name = "ReviewError";
    }
}


// ---------------------------------------------------------
// VALIDATION
// ---------------------------------------------------------

function requireText(value, field) {
    if (typeof value !== "string" || !value.trim()) {
        throw new ValidationError(`${field} is required.`);
    }
}

function requireNumber(value, field, minimum = 0) {
    if (
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < minimum
    ) {
        throw new ValidationError(`${field} is invalid.`);
    }
}

function validateDateRange(start, end) {
    const startTime = Date.parse(start);
    const endTime = Date.parse(end);

    if (
        !Number.isFinite(startTime) ||
        !Number.isFinite(endTime) ||
        startTime > endTime
    ) {
        throw new ValidationError("Invalid date range.");
    }
}

function overlaps(aStart, aEnd, bStart, bEnd) {
    return Date.parse(aStart) <= Date.parse(bEnd) &&
        Date.parse(aEnd) >= Date.parse(bStart);
}

function validateSkills(skills) {
    if (
        !skills ||
        typeof skills !== "object" ||
        Array.isArray(skills)
    ) {
        throw new ValidationError("Skills must be an object.");
    }

    for (const [name, level] of Object.entries(skills)) {
        requireText(name, "Skill name");

        if (!Number.isInteger(level) || level < 1 || level > 5) {
            throw new ValidationError(
                `Invalid competency level for ${name}.`
            );
        }
    }
}


// ---------------------------------------------------------
// DOMAIN OBJECTS
// ---------------------------------------------------------

class Employee {
    constructor({
        id,
        name,
        department,
        role,
        skills,
        weeklyCapacity = 40,
        status = EmployeeStatus.ACTIVE
    }) {
        requireText(id, "Employee ID");
        requireText(name, "Employee name");
        requireText(department, "Department");
        requireText(role, "Role");
        requireNumber(weeklyCapacity, "Weekly capacity", 0.01);
        validateSkills(skills);

        if (!Object.values(EmployeeStatus).includes(status)) {
            throw new ValidationError("Invalid employee status.");
        }

        this.id = id;
        this.name = name;
        this.department = department;
        this.role = role;
        this.skills = Object.freeze({ ...skills });
        this.weeklyCapacity = weeklyCapacity;
        this.status = status;
    }
}


class Project {
    constructor({
        id,
        name,
        requiredSkills,
        priority = 3,
        status = ProjectStatus.ACTIVE
    }) {
        requireText(id, "Project ID");
        requireText(name, "Project name");
        validateSkills(requiredSkills);

        if (!Number.isInteger(priority) || priority < 1 || priority > 5) {
            throw new ValidationError("Priority must be between 1 and 5.");
        }

        if (!Object.values(ProjectStatus).includes(status)) {
            throw new ValidationError("Invalid project status.");
        }

        this.id = id;
        this.name = name;
        this.requiredSkills = Object.freeze({ ...requiredSkills });
        this.priority = priority;
        this.status = status;
    }
}


// ---------------------------------------------------------
// RESOURCE MANAGEMENT SERVICE
// ---------------------------------------------------------

class ResourceManager extends EventEmitter {

    #employees = new Map();
    #projects = new Map();
    #allocations = new Map();
    #leave = new Map();
    #reviews = new Map();
    #audit = [];

    constructor() {
        super();

        this.on("resource.allocated", event => {
            this.#record("RESOURCE_ALLOCATED", event);
        });

        this.on("employee.status.changed", event => {
            this.#record("EMPLOYEE_STATUS_CHANGED", event);
        });

        this.on("review.decided", event => {
            this.#record("REVIEW_DECIDED", event);
        });
    }

    #record(type, payload) {
        this.#audit.push({
            id: randomUUID(),
            type,
            payload: structuredClone(payload),
            timestamp: new Date().toISOString()
        });
    }

    #employee(id) {
        const employee = this.#employees.get(id);

        if (!employee) {
            throw new ValidationError(`Unknown employee: ${id}`);
        }

        return employee;
    }

    #project(id) {
        const project = this.#projects.get(id);

        if (!project) {
            throw new ValidationError(`Unknown project: ${id}`);
        }

        return project;
    }

    addEmployee(employee) {
        if (!(employee instanceof Employee)) {
            throw new ValidationError("Invalid employee object.");
        }

        if (this.#employees.has(employee.id)) {
            throw new ValidationError("Employee ID already exists.");
        }

        this.#employees.set(employee.id, employee);

        this.#record("EMPLOYEE_CREATED", {
            employeeId: employee.id
        });
    }

    addProject(project) {
        if (!(project instanceof Project)) {
            throw new ValidationError("Invalid project object.");
        }

        if (this.#projects.has(project.id)) {
            throw new ValidationError("Project ID already exists.");
        }

        this.#projects.set(project.id, project);

        this.#record("PROJECT_CREATED", {
            projectId: project.id
        });
    }

    updateEmployeeStatus(employeeId, status) {
        const employee = this.#employee(employeeId);

        if (!Object.values(EmployeeStatus).includes(status)) {
            throw new ValidationError("Invalid status.");
        }

        const updated = new Employee({
            ...employee,
            status
        });

        this.#employees.set(employeeId, updated);

        this.emit("employee.status.changed", {
            employeeId,
            status
        });
    }

    addLeave({
        employeeId,
        start,
        end,
        unavailableHours
    }) {
        this.#employee(employeeId);
        validateDateRange(start, end);
        requireNumber(unavailableHours, "Unavailable hours");

        if (unavailableHours > 40) {
            throw new ValidationError(
                "Weekly unavailable hours cannot exceed 40."
            );
        }

        const records = this.#leave.get(employeeId) || [];

        records.push({
            start,
            end,
            unavailableHours
        });

        this.#leave.set(employeeId, records);

        this.#record("LEAVE_ADDED", { employeeId, start, end });
    }

    #unavailableHours(employeeId, start, end) {
        const records = this.#leave.get(employeeId) || [];

        return Math.min(
            this.#employee(employeeId).weeklyCapacity,
            records
                .filter(record =>
                    overlaps(start, end, record.start, record.end)
                )
                .reduce(
                    (total, record) => total + record.unavailableHours,
                    0
                )
        );
    }

    #allocatedHours(employeeId, start, end) {
        let total = 0;

        for (const allocation of this.#allocations.values()) {
            if (
                allocation.employeeId === employeeId &&
                overlaps(start, end, allocation.start, allocation.end)
            ) {
                total += allocation.weeklyHours;
            }
        }

        return total;
    }

    capacity(employeeId, start, end) {
        validateDateRange(start, end);

        const employee = this.#employee(employeeId);

        if (employee.status !== EmployeeStatus.ACTIVE) {
            return {
                gross: employee.weeklyCapacity,
                unavailable: employee.weeklyCapacity,
                allocated: 0,
                available: 0
            };
        }

        const unavailable = this.#unavailableHours(
            employeeId,
            start,
            end
        );

        const gross = employee.weeklyCapacity - unavailable;
        const allocated = this.#allocatedHours(employeeId, start, end);

        return {
            gross,
            unavailable,
            allocated,
            available: Math.max(0, gross - allocated)
        };
    }

    allocate({
        employeeId,
        projectId,
        weeklyHours,
        start,
        end
    }) {
        validateDateRange(start, end);
        requireNumber(weeklyHours, "Weekly allocation", 0.01);

        const employee = this.#employee(employeeId);
        const project = this.#project(projectId);

        if (employee.status !== EmployeeStatus.ACTIVE) {
            throw new CapacityError("Employee is not active.");
        }

        if (project.status !== ProjectStatus.ACTIVE) {
            throw new CapacityError("Project is not active.");
        }

        const available = this.capacity(
            employeeId,
            start,
            end
        ).available;

        if (weeklyHours > available) {
            throw new CapacityError(
                `Requested ${weeklyHours} hours; available ${available}.`
            );
        }

        const allocation = Object.freeze({
            id: randomUUID(),
            employeeId,
            projectId,
            weeklyHours,
            start,
            end,
            createdAt: new Date().toISOString()
        });

        this.#allocations.set(allocation.id, allocation);

        this.emit("resource.allocated", {
            allocationId: allocation.id,
            employeeId,
            projectId,
            weeklyHours
        });

        return allocation;
    }

    utilization(start, end) {
        validateDateRange(start, end);

        return [...this.#employees.values()]
            .filter(employee =>
                employee.status === EmployeeStatus.ACTIVE
            )
            .map(employee => {
                const capacity = this.capacity(
                    employee.id,
                    start,
                    end
                );

                const percentage = capacity.gross > 0
                    ? capacity.allocated / capacity.gross * 100
                    : 0;

                return {
                    employeeId: employee.id,
                    employeeName: employee.name,
                    department: employee.department,
                    effectiveCapacity: capacity.gross,
                    allocatedHours: capacity.allocated,
                    availableHours: capacity.available,
                    utilization: Number(percentage.toFixed(2)),
                    overallocated: capacity.allocated > capacity.gross
                };
            });
    }

    skillMatch(projectId) {
        const project = this.#project(projectId);

        return [...this.#employees.values()]
            .filter(employee =>
                employee.status === EmployeeStatus.ACTIVE
            )
            .map(employee => {
                const skills = Object.entries(project.requiredSkills);

                const missing = skills.filter(([skill, level]) =>
                    (employee.skills[skill] || 0) < level
                );

                return {
                    employeeId: employee.id,
                    employeeName: employee.name,
                    matchedSkills: skills.length - missing.length,
                    totalSkills: skills.length,
                    matchPercentage: skills.length
                        ? Number(
                            ((skills.length - missing.length) /
                            skills.length * 100).toFixed(2)
                        )
                        : 100,
                    gaps: missing.map(([skill, required]) => ({
                        skill,
                        required,
                        available: employee.skills[skill] || 0
                    }))
                };
            })
            .sort((a, b) =>
                b.matchPercentage - a.matchPercentage
            );
    }

    evaluateRisks(start, end) {
        return this.utilization(start, end).map(item => {
            let level;
            let reason;

            if (item.overallocated) {
                level = "CRITICAL";
                reason = "Capacity exceeded.";
            } else if (item.utilization >= 95) {
                level = "HIGH";
                reason = "Insufficient capacity buffer.";
            } else if (item.utilization >= 85) {
                level = "MEDIUM";
                reason = "High workload concentration.";
            } else if (item.utilization < 40) {
                level = "MEDIUM";
                reason = "Potential underutilization.";
            } else {
                level = "LOW";
                reason = "Capacity within expected range.";
            }

            return {
                employeeId: item.employeeId,
                utilization: item.utilization,
                level,
                reason
            };
        });
    }

    fairness(start, end) {
        const values = this.utilization(start, end)
            .map(item => item.utilization);

        if (values.length === 0) {
            return {
                average: 0,
                standardDeviation: 0,
                minimum: 0,
                maximum: 0
            };
        }

        const average = values.reduce((a, b) => a + b, 0) /
            values.length;

        const variance = values.reduce(
            (sum, value) => sum + (value - average) ** 2,
            0
        ) / values.length;

        return {
            average: Number(average.toFixed(2)),
            standardDeviation: Number(
                Math.sqrt(variance).toFixed(2)
            ),
            minimum: Math.min(...values),
            maximum: Math.max(...values)
        };
    }

    // Asynchronous review processing permits integration with
    // external approval services and reporting queues.
    async createReview({
        reviewer,
        start,
        end
    }) {
        requireText(reviewer, "Reviewer");
        validateDateRange(start, end);

        const findings = this.evaluateRisks(start, end)
            .filter(risk =>
                risk.level === "HIGH" ||
                risk.level === "CRITICAL"
            );

        const review = {
            id: randomUUID(),
            reviewer,
            start,
            end,
            status: ReviewStatus.UNDER_REVIEW,
            findings,
            actions: [],
            decision: null,
            createdAt: new Date().toISOString()
        };

        this.#reviews.set(review.id, review);

        await Promise.resolve();

        this.#record("REVIEW_CREATED", {
            reviewId: review.id,
            findingCount: findings.length
        });

        return structuredClone(review);
    }

    addAction(reviewId, {
        description,
        ownerId,
        dueDate
    }) {
        const review = this.#reviews.get(reviewId);

        if (!review) {
            throw new ReviewError("Review does not exist.");
        }

        if (review.status !== ReviewStatus.UNDER_REVIEW) {
            throw new ReviewError("Review cannot be modified.");
        }

        requireText(description, "Action description");
        this.#employee(ownerId);

        if (!Number.isFinite(Date.parse(dueDate))) {
            throw new ValidationError("Invalid action due date.");
        }

        const action = Object.freeze({
            id: randomUUID(),
            description,
            ownerId,
            dueDate,
            status: ActionStatus.OPEN
        });

        review.actions.push(action);

        this.#record("ACTION_CREATED", {
            reviewId,
            actionId: action.id
        });

        return action;
    }

    decideReview(reviewId, {
        approved,
        reviewer,
        notes
    }) {
        const review = this.#reviews.get(reviewId);

        if (!review) {
            throw new ReviewError("Review does not exist.");
        }

        if (review.status !== ReviewStatus.UNDER_REVIEW) {
            throw new ReviewError("Review is already finalized.");
        }

        requireText(reviewer, "Decision maker");
        requireText(notes, "Decision notes");

        if (typeof approved !== "boolean") {
            throw new ValidationError("Decision must be boolean.");
        }

        const critical = review.findings.some(
            finding => finding.level === "CRITICAL"
        );

        if (approved && critical) {
            throw new ReviewError(
                "Critical findings prevent review approval."
            );
        }

        review.status = approved
            ? ReviewStatus.APPROVED
            : ReviewStatus.REJECTED;

        review.decision = Object.freeze({
            reviewer,
            approved,
            notes,
            decidedAt: new Date().toISOString()
        });

        this.emit("review.decided", {
            reviewId,
            status: review.status,
            reviewer
        });

        return structuredClone(review);
    }

    getAuditLog() {
        return structuredClone(this.#audit);
    }

    getReview(reviewId) {
        const review = this.#reviews.get(reviewId);

        if (!review) {
            throw new ReviewError("Review not found.");
        }

        return structuredClone(review);
    }

    async exportReview(reviewId, outputDirectory) {
        const review = this.getReview(reviewId);

        const report = {
            review,
            utilization: this.utilization(
                review.start,
                review.end
            ),
            fairness: this.fairness(
                review.start,
                review.end
            ),
            risks: this.evaluateRisks(
                review.start,
                review.end
            ),
            auditEvents: this.getAuditLog()
        };

        await fs.mkdir(outputDirectory, { recursive: true });

        const filename = `resource-review-${reviewId}.json`;
        const outputPath = path.join(outputDirectory, filename);

        await fs.writeFile(
            outputPath,
            JSON.stringify(report, null, 2),
            { encoding: "utf8", flag: "wx" }
        );

        return outputPath;
    }
}


// ---------------------------------------------------------
// APPLICATION EXECUTION
// ---------------------------------------------------------

async function main() {
    const manager = new ResourceManager();

    manager.on("resource.allocated", event => {
        console.log("ALLOCATION EVENT:", event);
    });

    manager.on("review.decided", event => {
        console.log("REVIEW EVENT:", event);
    });

    const employees = [
        new Employee({
            id: "E101",
            name: "Aarav Sharma",
            department: "Engineering",
            role: "Senior Developer",
            skills: { python: 5, sql: 4, cloud: 4 }
        }),
        new Employee({
            id: "E102",
            name: "Meera Singh",
            department: "Engineering",
            role: "Backend Developer",
            skills: { python: 4, sql: 5, cloud: 3 }
        }),
        new Employee({
            id: "E103",
            name: "Rohan Verma",
            department: "Analytics",
            role: "Data Analyst",
            skills: { python: 3, sql: 4, analytics: 5 }
        }),
        new Employee({
            id: "E104",
            name: "Ananya Gupta",
            department: "Engineering",
            role: "Cloud Engineer",
            skills: { cloud: 5, python: 3, security: 4 }
        })
    ];

    employees.forEach(employee =>
        manager.addEmployee(employee)
    );

    manager.addProject(
        new Project({
            id: "P101",
            name: "Enterprise Platform Modernization",
            requiredSkills: {
                python: 4,
                sql: 4,
                cloud: 4
            },
            priority: 5
        })
    );

    const start = "2026-11-01";
    const end = "2026-11-30";

    manager.allocate({
        employeeId: "E101",
        projectId: "P101",
        weeklyHours: 35,
        start,
        end
    });

    manager.allocate({
        employeeId: "E102",
        projectId: "P101",
        weeklyHours: 25,
        start,
        end
    });

    manager.allocate({
        employeeId: "E103",
        projectId: "P101",
        weeklyHours: 20,
        start,
        end
    });

    manager.allocate({
        employeeId: "E104",
        projectId: "P101",
        weeklyHours: 30,
        start,
        end
    });

    manager.addLeave({
        employeeId: "E102",
        start: "2026-11-10",
        end: "2026-11-14",
        unavailableHours: 8
    });

    console.log("\nUTILIZATION");
    console.table(manager.utilization(start, end));

    console.log("\nSKILL MATCHING");
    console.table(manager.skillMatch("P101"));

    console.log("\nRISK ASSESSMENT");
    console.table(manager.evaluateRisks(start, end));

    console.log("\nWORKLOAD FAIRNESS");
    console.log(manager.fairness(start, end));

    const review = await manager.createReview({
        reviewer: "Resource Management Lead",
        start,
        end
    });

    employees.forEach(employee => {
        manager.addAction(review.id, {
            description: `Review workload for ${employee.name}`,
            ownerId: employee.id,
            dueDate: "2026-12-05"
        });
    });

    try {
        manager.decideReview(review.id, {
            approved: true,
            reviewer: "Department Head",
            notes: "Resource review completed."
        });

    } catch (error) {
        if (!(error instanceof ReviewError)) {
            throw error;
        }

        console.log("APPROVAL BLOCKED:", error.message);

        manager.decideReview(review.id, {
            approved: false,
            reviewer: "Department Head",
            notes: "Critical resource risks require correction."
        });
    }

    const reportPath = await manager.exportReview(
        review.id,
        path.resolve("resource_review_output")
    );

    console.log("\nFINAL REVIEW");
    console.log(manager.getReview(review.id));

    console.log("\nREPORT:", reportPath);
    console.log("AUDIT EVENTS:", manager.getAuditLog().length);

    // Verify that excessive allocations are rejected.
    try {
        manager.allocate({
            employeeId: "E103",
            projectId: "P101",
            weeklyHours: 50,
            start,
            end
        });

        throw new Error("Capacity validation failed.");

    } catch (error) {
        if (!(error instanceof CapacityError)) {
            throw error;
        }

        console.log("CAPACITY VALIDATION: PASSED");
    }

    console.log("\nRESOURCE MANAGEMENT REVIEW COMPLETED");
}


main().catch(error => {
    console.error("APPLICATION FAILURE:", error.message);
    process.exitCode = 1;
});
