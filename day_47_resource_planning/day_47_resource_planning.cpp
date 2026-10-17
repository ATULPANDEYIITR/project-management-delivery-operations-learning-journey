"use strict";

/*
 * Project resource planning model.
 *
 * The implementation focuses on resource allocation, capacity, skills,
 * cost, scheduling conflicts, and policy-driven merge-style approval of
 * resource changes. JavaScript's event-driven model is used to emit
 * allocation events so an application can update dashboards or audit logs.
 */

const ResourceType = Object.freeze({
    PERSON: "person",
    EQUIPMENT: "equipment",
    SOFTWARE: "software",
});

const AllocationState = Object.freeze({
    PLANNED: "planned",
    ACTIVE: "active",
    RELEASED: "released",
});

class ResourcePlanningError extends Error {
    constructor(message) {
        super(message);
        this.name = "ResourcePlanningError";
    }
}

class Person {
    constructor({
        id,
        name,
        role,
        skills,
        weeklyCapacity,
        hourlyCost,
        availability = 1,
    }) {
        if (!id || !name || weeklyCapacity <= 0 || hourlyCost < 0) {
            throw new ResourcePlanningError("Invalid person definition.");
        }

        this.id = id;
        this.name = name;
        this.role = role;
        this.skills = new Set(skills);
        this.weeklyCapacity = weeklyCapacity;
        this.hourlyCost = hourlyCost;
        this.availability = availability;
    }

    canPerform(requiredSkills, minimumLevel, level) {
        return (
            requiredSkills.every((skill) => this.skills.has(skill)) &&
            level >= minimumLevel
        );
    }
}

class ProjectTask {
    constructor({
        id,
        name,
        requiredSkills,
        minimumSkillLevel,
        estimatedHours,
        start,
        end,
    }) {
        const startDate = new Date(start);
        const endDate = new Date(end);

        if (
            !id ||
            estimatedHours <= 0 ||
            Number.isNaN(startDate.valueOf()) ||
            Number.isNaN(endDate.valueOf()) ||
            startDate > endDate
        ) {
            throw new ResourcePlanningError(`Invalid task: ${name}`);
        }

        this.id = id;
        this.name = name;
        this.requiredSkills = requiredSkills;
        this.minimumSkillLevel = minimumSkillLevel;
        this.estimatedHours = estimatedHours;
        this.start = startDate;
        this.end = endDate;
    }
}

class ResourcePlanner extends EventTarget {
    constructor({ projectName, budget }) {
        super();

        if (!projectName || budget <= 0) {
            throw new ResourcePlanningError("Invalid project plan.");
        }

        this.projectName = projectName;
        this.budget = budget;
        this.people = new Map();
        this.tasks = new Map();
        this.allocations = [];
    }

    addPerson(person) {
        if (this.people.has(person.id)) {
            throw new ResourcePlanningError(
                `Duplicate resource ID: ${person.id}`
            );
        }

        this.people.set(person.id, person);
    }

    addTask(task) {
        if (this.tasks.has(task.id)) {
            throw new ResourcePlanningError(
                `Duplicate task ID: ${task.id}`
            );
        }

        this.tasks.set(task.id, task);
    }

    overlappingAllocations(resourceId, start, end) {
        return this.allocations.filter((allocation) => {
            if (allocation.resourceId !== resourceId) return false;
            if (allocation.state === AllocationState.RELEASED) return false;

            return (
                allocation.start <= end &&
                allocation.end >= start
            );
        });
    }

    allocatedHours(resourceId, start, end) {
        return this.overlappingAllocations(resourceId, start, end)
            .reduce((total, allocation) => total + allocation.hours, 0);
    }

    findQualifiedPeople(task) {
        return [...this.people.values()]
            .filter((person) =>
                person.canPerform(
                    task.requiredSkills,
                    task.minimumSkillLevel,
                    this.skillLevelFor(person)
                )
            )
            .sort((a, b) => a.hourlyCost - b.hourlyCost);
    }

    skillLevelFor(person) {
        if (person.role.toLowerCase().includes("senior")) return 3;
        if (person.role.toLowerCase().includes("lead")) return 4;
        return 2;
    }

    allocatePerson(taskId, personId, hours) {
        const task = this.tasks.get(taskId);
        const person = this.people.get(personId);

        if (!task || !person) {
            throw new ResourcePlanningError(
                "Task or resource does not exist."
            );
        }

        if (hours <= 0 || hours > task.estimatedHours) {
            throw new ResourcePlanningError(
                "Allocation must be positive and cannot exceed task effort."
            );
        }

        if (
            !person.canPerform(
                task.requiredSkills,
                task.minimumSkillLevel,
                this.skillLevelFor(person)
            )
        ) {
            throw new ResourcePlanningError(
                `${person.name} does not satisfy the task skill requirements.`
            );
        }

        const existing = this.allocatedHours(
            person.id,
            task.start,
            task.end
        );

        const workingDays = this.workingDays(task.start, task.end);
        const weeklyEquivalent =
            hours / Math.max(workingDays / 5, 1);

        if (existing + weeklyEquivalent > person.weeklyCapacity) {
            throw new ResourcePlanningError(
                `Capacity conflict for ${person.name}.`
            );
        }

        const allocation = {
            resourceId: person.id,
            taskId: task.id,
            type: ResourceType.PERSON,
            start: task.start,
            end: task.end,
            hours,
            state: AllocationState.PLANNED,
        };

        this.allocations.push(allocation);

        this.dispatchEvent(
            new CustomEvent("resourceAllocated", {
                detail: allocation,
            })
        );

        return allocation;
    }

    workingDays(start, end) {
        let count = 0;
        const current = new Date(start);

        while (current <= end) {
            const day = current.getDay();
            if (day !== 0 && day !== 6) count++;
            current.setDate(current.getDate() + 1);
        }

        return count;
    }

    estimateCost() {
        return this.allocations.reduce((total, allocation) => {
            if (allocation.type !== ResourceType.PERSON) {
                return total;
            }

            const person = this.people.get(allocation.resourceId);
            return total + allocation.hours * person.hourlyCost;
        }, 0);
    }

    utilization(personId) {
        const person = this.people.get(personId);

        if (!person) {
            throw new ResourcePlanningError(
                `Unknown resource: ${personId}`
            );
        }

        const hours = this.allocations
            .filter(
                (allocation) =>
                    allocation.resourceId === personId &&
                    allocation.state !== AllocationState.RELEASED
            )
            .reduce((total, allocation) => total + allocation.hours, 0);

        return {
            person: person.name,
            hours,
            capacity: person.weeklyCapacity,
            percentage: (hours / person.weeklyCapacity) * 100,
        };
    }

    budgetStatus() {
        const cost = this.estimateCost();

        return {
            budget: this.budget,
            plannedCost: cost,
            remaining: this.budget - cost,
            overBudget: cost > this.budget,
        };
    }

    generateDashboard() {
        return {
            project: this.projectName,
            budget: this.budgetStatus(),
            resources: [...this.people.keys()].map((id) =>
                this.utilization(id)
            ),
            allocations: this.allocations.map((allocation) => ({
                ...allocation,
                start: allocation.start.toISOString().slice(0, 10),
                end: allocation.end.toISOString().slice(0, 10),
            })),
        };
    }
}

function createPlan() {
    const planner = new ResourcePlanner({
        projectName: "Public Service Data Platform",
        budget: 100000,
    });

    planner.addPerson(
        new Person({
            id: "P-100",
            name: "Asha Rao",
            role: "Senior Backend Engineer",
            skills: ["python", "api", "postgresql", "security"],
            weeklyCapacity: 40,
            hourlyCost: 75,
        })
    );

    planner.addPerson(
        new Person({
            id: "P-200",
            name: "Vikram Singh",
            role: "Senior Frontend Engineer",
            skills: ["javascript", "react", "api"],
            weeklyCapacity: 40,
            hourlyCost: 68,
        })
    );

    planner.addPerson(
        new Person({
            id: "P-300",
            name: "Meera Shah",
            role: "Lead Security Engineer",
            skills: ["security", "testing", "cloud"],
            weeklyCapacity: 32,
            hourlyCost: 92,
        })
    );

    planner.addTask(
        new ProjectTask({
            id: "T-API",
            name: "Secure service layer",
            requiredSkills: ["python", "api", "security"],
            minimumSkillLevel: 3,
            estimatedHours: 72,
            start: "2026-10-19",
            end: "2026-10-30",
        })
    );

    planner.addTask(
        new ProjectTask({
            id: "T-WEB",
            name: "Citizen portal",
            requiredSkills: ["javascript", "react"],
            minimumSkillLevel: 3,
            estimatedHours: 64,
            start: "2026-10-26",
            end: "2026-11-06",
        })
    );

    planner.addTask(
        new ProjectTask({
            id: "T-SEC",
            name: "Security validation",
            requiredSkills: ["security", "testing"],
            minimumSkillLevel: 4,
            estimatedHours: 40,
            start: "2026-11-02",
            end: "2026-11-13",
        })
    );

    return planner;
}

function run() {
    const planner = createPlan();

    /*
     * EventTarget gives the planner an event-driven boundary.
     * A browser dashboard, Node.js service, or audit component can listen
     * without being coupled to the allocation implementation.
     */
    planner.addEventListener("resourceAllocated", (event) => {
        console.log(
            `Allocation created: ${event.detail.resourceId} -> ` +
            `${event.detail.taskId} (${event.detail.hours}h)`
        );
    });

    planner.allocatePerson("T-API", "P-100", 72);
    planner.allocatePerson("T-WEB", "P-200", 64);
    planner.allocatePerson("T-SEC", "P-300", 40);

    try {
        planner.allocatePerson("T-SEC", "P-100", 40);
    } catch (error) {
        console.log(`Rejected allocation: ${error.message}`);
    }

    console.log("\nResource planning dashboard:");
    console.log(
        JSON.stringify(planner.generateDashboard(), null, 2)
    );
}

run();
