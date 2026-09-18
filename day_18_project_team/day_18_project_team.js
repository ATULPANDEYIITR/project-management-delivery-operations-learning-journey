/*
 * Project Team Roles: JavaScript implementation
 *
 * This standalone file demonstrates project-team roles through an
 * application-oriented project coordination model.
 *
 * It covers:
 * - role modeling
 * - responsibilities
 * - RACI analysis
 * - skill matching
 * - workload allocation
 * - task dependencies
 * - event-driven status updates
 * - asynchronous approvals
 * - risk analysis
 * - communication channels
 * - validation
 * - project health
 * - performance considerations
 *
 * Compatible with modern Node.js.
 */

"use strict";

// ============================================================================
// 1. BASIC ROLE MODEL
// ============================================================================

const roles = {
    sponsor: {
        name: "Project Sponsor",
        category: "Governance",
        responsibilities: [
            "Strategic direction",
            "Funding support",
            "Escalation",
            "Executive sponsorship"
        ]
    },

    projectManager: {
        name: "Project Manager",
        category: "Management",
        responsibilities: [
            "Planning",
            "Coordination",
            "Risk management",
            "Schedule management",
            "Communication"
        ]
    },

    productOwner: {
        name: "Product Owner",
        category: "Product",
        responsibilities: [
            "Product priorities",
            "Backlog management",
            "Value decisions",
            "Acceptance"
        ]
    },

    businessAnalyst: {
        name: "Business Analyst",
        category: "Analysis",
        responsibilities: [
            "Requirements analysis",
            "Process analysis",
            "Business rules",
            "Stakeholder analysis"
        ]
    },

    technicalLead: {
        name: "Technical Lead",
        category: "Engineering",
        responsibilities: [
            "Architecture",
            "Technical decisions",
            "Code review",
            "Technical risk management"
        ]
    },

    developer: {
        name: "Software Developer",
        category: "Engineering",
        responsibilities: [
            "Implementation",
            "Unit testing",
            "Defect correction",
            "Maintenance"
        ]
    },

    qaEngineer: {
        name: "QA Engineer",
        category: "Quality",
        responsibilities: [
            "Test design",
            "Test execution",
            "Defect verification",
            "Quality reporting"
        ]
    },

    devOpsEngineer: {
        name: "DevOps Engineer",
        category: "Operations",
        responsibilities: [
            "CI/CD",
            "Deployment",
            "Infrastructure",
            "Monitoring"
        ]
    },

    securitySpecialist: {
        name: "Security Specialist",
        category: "Security",
        responsibilities: [
            "Threat modeling",
            "Security review",
            "Vulnerability analysis",
            "Security controls"
        ]
    }
};

console.log("PROJECT TEAM ROLES");
console.log("==================");

Object.values(roles).forEach((role) => {
    console.log(`${role.name} [${role.category}]`);
});


// ============================================================================
// 2. TEAM MEMBERS
// ============================================================================

class TeamMember {
    constructor({
        id,
        name,
        role,
        skills,
        weeklyCapacity,
        availability = 1
    }) {
        this.id = id;
        this.name = name;
        this.role = role;
        this.skills = new Set(skills.map((skill) => skill.toLowerCase()));
        this.weeklyCapacity = weeklyCapacity;
        this.availability = availability;
        this.assignedHours = 0;
    }

    get effectiveCapacity() {
        return this.weeklyCapacity * this.availability;
    }

    get remainingCapacity() {
        return this.effectiveCapacity - this.assignedHours;
    }

    hasSkill(skill) {
        return this.skills.has(skill.toLowerCase());
    }

    assignHours(hours) {
        if (hours < 0) {
            throw new Error("Assigned hours cannot be negative.");
        }

        if (hours > this.remainingCapacity) {
            throw new Error(
                `${this.name} does not have enough remaining capacity.`
            );
        }

        this.assignedHours += hours;
    }
}


const team = [
    new TeamMember({
        id: "TM01",
        name: "Priya",
        role: roles.projectManager.name,
        skills: ["planning", "risk management", "communication"],
        weeklyCapacity: 40
    }),

    new TeamMember({
        id: "TM02",
        name: "Arjun",
        role: roles.productOwner.name,
        skills: ["prioritization", "product strategy", "requirements"],
        weeklyCapacity: 35
    }),

    new TeamMember({
        id: "TM03",
        name: "Meera",
        role: roles.businessAnalyst.name,
        skills: ["requirements", "process analysis"],
        weeklyCapacity: 40
    }),

    new TeamMember({
        id: "TM04",
        name: "Rahul",
        role: roles.technicalLead.name,
        skills: ["architecture", "python", "security", "code review"],
        weeklyCapacity: 40
    }),

    new TeamMember({
        id: "TM05",
        name: "Neha",
        role: roles.developer.name,
        skills: ["python", "javascript", "api development", "testing"],
        weeklyCapacity: 40
    }),

    new TeamMember({
        id: "TM06",
        name: "Vikram",
        role: roles.qaEngineer.name,
        skills: ["testing", "automation testing"],
        weeklyCapacity: 40
    }),

    new TeamMember({
        id: "TM07",
        name: "Sara",
        role: roles.devOpsEngineer.name,
        skills: ["ci/cd", "cloud", "monitoring"],
        weeklyCapacity: 40
    }),

    new TeamMember({
        id: "TM08",
        name: "Karan",
        role: roles.securitySpecialist.name,
        skills: ["security", "threat modeling"],
        weeklyCapacity: 32
    })
];


// ============================================================================
// 3. TASK MODEL
// ============================================================================

class ProjectTask {
    constructor({
        id,
        name,
        requiredSkill,
        estimatedHours,
        priority,
        dependencies = []
    }) {
        this.id = id;
        this.name = name;
        this.requiredSkill = requiredSkill;
        this.estimatedHours = estimatedHours;
        this.priority = priority;
        this.dependencies = dependencies;
        this.owner = null;
        this.status = "Not Started";
    }
}


const tasks = [
    new ProjectTask({
        id: "T1",
        name: "Define requirements",
        requiredSkill: "requirements",
        estimatedHours: 16,
        priority: 1
    }),

    new ProjectTask({
        id: "T2",
        name: "Design architecture",
        requiredSkill: "architecture",
        estimatedHours: 20,
        priority: 1,
        dependencies: ["T1"]
    }),

    new ProjectTask({
        id: "T3",
        name: "Implement API",
        requiredSkill: "python",
        estimatedHours: 32,
        priority: 2,
        dependencies: ["T2"]
    }),

    new ProjectTask({
        id: "T4",
        name: "Build automated tests",
        requiredSkill: "testing",
        estimatedHours: 24,
        priority: 2,
        dependencies: ["T3"]
    }),

    new ProjectTask({
        id: "T5",
        name: "Configure CI/CD",
        requiredSkill: "ci/cd",
        estimatedHours: 16,
        priority: 2,
        dependencies: ["T3"]
    }),

    new ProjectTask({
        id: "T6",
        name: "Security review",
        requiredSkill: "security",
        estimatedHours: 16,
        priority: 1,
        dependencies: ["T3"]
    }),

    new ProjectTask({
        id: "T7",
        name: "Production release",
        requiredSkill: "cloud",
        estimatedHours: 12,
        priority: 1,
        dependencies: ["T4", "T5", "T6"]
    })
];


// ============================================================================
// 4. SKILL-BASED ASSIGNMENT
// ============================================================================

function findQualifiedMembers(task, members) {
    return members.filter(
        (member) =>
            member.hasSkill(task.requiredSkill) &&
            member.remainingCapacity >= task.estimatedHours
    );
}


function assignTask(task, members) {
    const qualifiedMembers = findQualifiedMembers(task, members);

    if (qualifiedMembers.length === 0) {
        return null;
    }

    // Selecting the person with the greatest remaining capacity is a simple
    // balancing strategy. Real systems can consider cost, seniority,
    // historical performance, availability calendars, and workload fairness.
    qualifiedMembers.sort(
        (a, b) => b.remainingCapacity - a.remainingCapacity
    );

    const selectedMember = qualifiedMembers[0];

    selectedMember.assignHours(task.estimatedHours);
    task.owner = selectedMember.name;
    task.status = "Assigned";

    return selectedMember;
}


console.log("\nTASK ASSIGNMENT");
console.log("===============");

tasks
    .slice()
    .sort((a, b) => a.priority - b.priority)
    .forEach((task) => {
        const assignedMember = assignTask(task, team);

        if (assignedMember) {
            console.log(
                `${task.id}: ${task.name} -> ${assignedMember.name}`
            );
        } else {
            console.log(`${task.id}: ${task.name} -> UNASSIGNED`);
        }
    });


// ============================================================================
// 5. DEPENDENCY VALIDATION
// ============================================================================

function validateDependencies(projectTasks) {
    const taskIds = new Set(projectTasks.map((task) => task.id));
    const errors = [];

    for (const task of projectTasks) {
        for (const dependency of task.dependencies) {
            if (!taskIds.has(dependency)) {
                errors.push(
                    `${task.id} depends on unknown task ${dependency}`
                );
            }

            if (dependency === task.id) {
                errors.push(`${task.id} cannot depend on itself`);
            }
        }
    }

    return errors;
}


console.log("\nDEPENDENCY VALIDATION");
console.log("=====================");

const dependencyErrors = validateDependencies(tasks);

if (dependencyErrors.length === 0) {
    console.log("Dependencies are structurally valid.");
} else {
    dependencyErrors.forEach((error) => console.log(error));
}


// ============================================================================
// 6. TOPOLOGICAL SORT
// ============================================================================

function topologicalSort(projectTasks) {
    const graph = new Map();
    const indegree = new Map();

    for (const task of projectTasks) {
        graph.set(task.id, []);
        indegree.set(task.id, 0);
    }

    for (const task of projectTasks) {
        for (const dependency of task.dependencies) {
            if (!graph.has(dependency)) {
                throw new Error(
                    `Unknown dependency ${dependency} for ${task.id}`
                );
            }

            graph.get(dependency).push(task.id);
            indegree.set(task.id, indegree.get(task.id) + 1);
        }
    }

    const queue = [];

    for (const [taskId, degree] of indegree) {
        if (degree === 0) {
            queue.push(taskId);
        }
    }

    const order = [];

    while (queue.length > 0) {
        const current = queue.shift();
        order.push(current);

        for (const dependent of graph.get(current)) {
            indegree.set(
                dependent,
                indegree.get(dependent) - 1
            );

            if (indegree.get(dependent) === 0) {
                queue.push(dependent);
            }
        }
    }

    if (order.length !== projectTasks.length) {
        throw new Error("Circular dependency detected.");
    }

    return order;
}


console.log("\nEXECUTION ORDER");
console.log("===============");

try {
    console.log(topologicalSort(tasks).join(" -> "));
} catch (error) {
    console.error(error.message);
}


// ============================================================================
// 7. RACI RESPONSIBILITY MATRIX
// ============================================================================

const RACI = Object.freeze({
    RESPONSIBLE: "R",
    ACCOUNTABLE: "A",
    CONSULTED: "C",
    INFORMED: "I"
});


const raciMatrix = {
    "Define requirements": {
        "Project Manager": RACI.ACCOUNTABLE,
        "Product Owner": RACI.CONSULTED,
        "Business Analyst": RACI.RESPONSIBLE,
        "Technical Lead": RACI.CONSULTED
    },

    "Design architecture": {
        "Project Manager": RACI.INFORMED,
        "Product Owner": RACI.CONSULTED,
        "Technical Lead": RACI.ACCOUNTABLE,
        "Software Developer": RACI.RESPONSIBLE,
        "Security Specialist": RACI.CONSULTED
    },

    "Implement API": {
        "Project Manager": RACI.INFORMED,
        "Technical Lead": RACI.ACCOUNTABLE,
        "Software Developer": RACI.RESPONSIBLE,
        "QA Engineer": RACI.CONSULTED
    },

    "Production release": {
        "Project Manager": RACI.ACCOUNTABLE,
        "Technical Lead": RACI.CONSULTED,
        "DevOps Engineer": RACI.RESPONSIBLE,
        "QA Engineer": RACI.CONSULTED,
        "Security Specialist": RACI.CONSULTED
    }
};


function validateRaci(matrix) {
    const results = [];

    for (const [taskName, assignments] of Object.entries(matrix)) {
        const values = Object.values(assignments);
        const accountableCount = values.filter(
            (value) => value === RACI.ACCOUNTABLE
        ).length;

        const responsibleCount = values.filter(
            (value) => value === RACI.RESPONSIBLE
        ).length;

        const errors = [];

        if (accountableCount !== 1) {
            errors.push(
                `Expected exactly one Accountable role, found ${accountableCount}`
            );
        }

        if (responsibleCount === 0) {
            errors.push("At least one Responsible role is required.");
        }

        results.push({
            taskName,
            valid: errors.length === 0,
            errors
        });
    }

    return results;
}


console.log("\nRACI VALIDATION");
console.log("===============");

validateRaci(raciMatrix).forEach((result) => {
    console.log(
        `${result.taskName}: ${result.valid ? "VALID" : "INVALID"}`
    );

    result.errors.forEach((error) => {
        console.log(`  ${error}`);
    });
});


// ============================================================================
// 8. EVENT-DRIVEN PROJECT STATUS
// ============================================================================

class ProjectEventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }

        this.listeners.get(eventName).push(listener);
    }

    emit(eventName, payload) {
        const listeners = this.listeners.get(eventName) || [];

        for (const listener of listeners) {
            listener(payload);
        }
    }
}


const eventBus = new ProjectEventBus();

eventBus.on("taskAssigned", (event) => {
    console.log(
        `EVENT: ${event.taskId} assigned to ${event.owner}`
    );
});

eventBus.on("riskRaised", (event) => {
    console.log(
        `EVENT: Risk ${event.riskId} raised with exposure ${event.exposure}`
    );
});

for (const task of tasks) {
    if (task.owner) {
        eventBus.emit("taskAssigned", {
            taskId: task.id,
            owner: task.owner
        });
    }
}


// ============================================================================
// 9. ASYNCHRONOUS APPROVAL WORKFLOW
// ============================================================================

function requestApproval(decision, approver) {
    return new Promise((resolve, reject) => {
        // A real application would replace this timer with a database,
        // workflow engine, API call, or organizational approval system.
        setTimeout(() => {
            if (!decision || !approver) {
                reject(
                    new Error(
                        "Approval requires both a decision and an approver."
                    )
                );
                return;
            }

            resolve({
                decision,
                approver,
                status: "Approved",
                timestamp: new Date().toISOString()
            });
        }, 20);
    });
}


async function runApprovalWorkflow() {
    try {
        const approval = await requestApproval(
            "Architecture baseline",
            "Technical Lead"
        );

        console.log("\nASYNC APPROVAL");
        console.log("==============");
        console.log(approval);
    } catch (error) {
        console.error(`Approval failed: ${error.message}`);
    }
}


// ============================================================================
// 10. RISK MODEL
// ============================================================================

class Risk {
    constructor({
        id,
        description,
        probability,
        impact,
        owner,
        mitigation
    }) {
        if (probability < 0 || probability > 1) {
            throw new Error("Probability must be between 0 and 1.");
        }

        if (impact < 0) {
            throw new Error("Impact cannot be negative.");
        }

        this.id = id;
        this.description = description;
        this.probability = probability;
        this.impact = impact;
        this.owner = owner;
        this.mitigation = mitigation;
    }

    get exposure() {
        return this.probability * this.impact;
    }
}


const risks = [
    new Risk({
        id: "R1",
        description: "Requirements ambiguity",
        probability: 0.40,
        impact: 8,
        owner: "Business Analyst",
        mitigation: "Acceptance criteria and stakeholder validation."
    }),

    new Risk({
        id: "R2",
        description: "Architecture scalability problem",
        probability: 0.25,
        impact: 9,
        owner: "Technical Lead",
        mitigation: "Architecture review and capacity analysis."
    }),

    new Risk({
        id: "R3",
        description: "Security vulnerability",
        probability: 0.20,
        impact: 10,
        owner: "Security Specialist",
        mitigation: "Threat modeling and secure review."
    }),

    new Risk({
        id: "R4",
        description: "Deployment failure",
        probability: 0.25,
        impact: 7,
        owner: "DevOps Engineer",
        mitigation: "Automated deployment and rollback."
    })
];


risks.sort((a, b) => b.exposure - a.exposure);

risks.forEach((risk) => {
    eventBus.emit("riskRaised", {
        riskId: risk.id,
        exposure: risk.exposure.toFixed(2)
    });
});


// ============================================================================
// 11. TEAM CAPABILITY ANALYSIS
// ============================================================================

function getCapabilities(members) {
    const capabilities = new Set();

    for (const member of members) {
        for (const skill of member.skills) {
            capabilities.add(skill);
        }
    }

    return capabilities;
}


const requiredCapabilities = new Set([
    "planning",
    "requirements",
    "architecture",
    "python",
    "testing",
    "ci/cd",
    "security",
    "cloud"
]);

const availableCapabilities = getCapabilities(team);

const missingCapabilities = [...requiredCapabilities].filter(
    (capability) => !availableCapabilities.has(capability)
);

console.log("\nCAPABILITY ANALYSIS");
console.log("===================");

console.log(
    `Missing capabilities: ${
        missingCapabilities.length
            ? missingCapabilities.join(", ")
            : "None"
    }`
);


// ============================================================================
// 12. WORKLOAD ANALYSIS
// ============================================================================

function workloadReport(members) {
    return members.map((member) => ({
        name: member.name,
        role: member.role,
        assignedHours: member.assignedHours,
        capacity: member.effectiveCapacity,
        utilization: member.effectiveCapacity === 0
            ? 0
            : member.assignedHours / member.effectiveCapacity
    }));
}


console.log("\nWORKLOAD REPORT");
console.log("===============");

workloadReport(team).forEach((entry) => {
    console.log(
        `${entry.name}: ${entry.assignedHours}h / ` +
        `${entry.capacity}h = ` +
        `${(entry.utilization * 100).toFixed(1)}%`
    );
});


// ============================================================================
// 13. COMMUNICATION CHANNELS
// ============================================================================

const communicationChannels = [
    {
        name: "Daily stand-up",
        participants: [
            "Project Manager",
            "Technical Lead",
            "Software Developer",
            "QA Engineer",
            "DevOps Engineer"
        ],
        purpose: "Execution coordination and blockers",
        frequency: "Daily"
    },

    {
        name: "Product review",
        participants: [
            "Project Manager",
            "Product Owner",
            "Business Analyst",
            "Technical Lead"
        ],
        purpose: "Product and requirement decisions",
        frequency: "Weekly"
    },

    {
        name: "Security review",
        participants: [
            "Technical Lead",
            "Security Specialist",
            "Software Developer",
            "DevOps Engineer"
        ],
        purpose: "Security architecture and controls",
        frequency: "Release gate"
    }
];


function communicationParticipation(channels) {
    const counts = new Map();

    for (const channel of channels) {
        for (const participant of channel.participants) {
            counts.set(
                participant,
                (counts.get(participant) || 0) + 1
            );
        }
    }

    return counts;
}


console.log("\nCOMMUNICATION PARTICIPATION");
console.log("===========================");

for (const [participant, count] of communicationParticipation(
    communicationChannels
)) {
    console.log(`${participant}: ${count} channel(s)`);
}


// ============================================================================
// 14. DECISION RIGHTS
// ============================================================================

const decisionRights = new Map([
    ["Budget approval", "Project Sponsor"],
    ["Product priority", "Product Owner"],
    ["Project schedule", "Project Manager"],
    ["Technical architecture", "Technical Lead"],
    ["Quality verification", "QA Engineer"],
    ["Deployment implementation", "DevOps Engineer"],
    ["Security control review", "Security Specialist"]
]);

console.log("\nDECISION RIGHTS");
console.log("===============");

for (const [decision, owner] of decisionRights) {
    console.log(`${decision} -> ${owner}`);
}


// ============================================================================
// 15. PROJECT HEALTH
// ============================================================================

function projectHealth(projectTasks, projectRisks, members) {
    const assignedTasks = projectTasks.filter(
        (task) => task.owner !== null
    ).length;

    const totalHours = projectTasks.reduce(
        (sum, task) => sum + task.estimatedHours,
        0
    );

    const assignedHours = projectTasks
        .filter((task) => task.owner !== null)
        .reduce((sum, task) => sum + task.estimatedHours, 0);

    const averageUtilization = members.length === 0
        ? 0
        : members.reduce(
            (sum, member) =>
                sum +
                (
                    member.effectiveCapacity === 0
                        ? 0
                        : member.assignedHours /
                          member.effectiveCapacity
                ),
            0
        ) / members.length;

    const highRiskCount = projectRisks.filter(
        (risk) => risk.exposure >= 5
    ).length;

    return {
        assignmentRate:
            projectTasks.length === 0
                ? 1
                : assignedTasks / projectTasks.length,

        workCoverage:
            totalHours === 0
                ? 1
                : assignedHours / totalHours,

        averageUtilization,
        highRiskCount
    };
}


console.log("\nPROJECT HEALTH");
console.log("==============");

const health = projectHealth(tasks, risks, team);

console.log(
    `Assignment rate: ${(health.assignmentRate * 100).toFixed(1)}%`
);
console.log(
    `Work coverage: ${(health.workCoverage * 100).toFixed(1)}%`
);
console.log(
    `Average utilization: ${(health.averageUtilization * 100).toFixed(1)}%`
);
console.log(`High-risk items: ${health.highRiskCount}`);


// ============================================================================
// 16. EDGE CASE: CIRCULAR DEPENDENCY
// ============================================================================

const circularExample = [
    new ProjectTask({
        id: "A",
        name: "Task A",
        requiredSkill: "testing",
        estimatedHours: 2,
        priority: 1,
        dependencies: ["C"]
    }),

    new ProjectTask({
        id: "B",
        name: "Task B",
        requiredSkill: "testing",
        estimatedHours: 2,
        priority: 1,
        dependencies: ["A"]
    }),

    new ProjectTask({
        id: "C",
        name: "Task C",
        requiredSkill: "testing",
        estimatedHours: 2,
        priority: 1,
        dependencies: ["B"]
    })
];


console.log("\nCIRCULAR DEPENDENCY TEST");
console.log("========================");

try {
    topologicalSort(circularExample);
} catch (error) {
    console.log(`Correctly rejected: ${error.message}`);
}


// ============================================================================
// 17. VALIDATION
// ============================================================================

function validateTeam(members) {
    const errors = [];
    const ids = new Set();
    const names = new Set();

    for (const member of members) {
        if (!member.id || !member.name || !member.role) {
            errors.push("A member is missing required identity information.");
        }

        if (ids.has(member.id)) {
            errors.push(`Duplicate member ID: ${member.id}`);
        }

        if (names.has(member.name)) {
            errors.push(`Duplicate member name: ${member.name}`);
        }

        ids.add(member.id);
        names.add(member.name);

        if (member.weeklyCapacity < 0) {
            errors.push(`${member.name}: negative capacity.`);
        }

        if (member.availability < 0 || member.availability > 1) {
            errors.push(`${member.name}: invalid availability.`);
        }
    }

    return errors;
}


console.log("\nTEAM VALIDATION");
console.log("===============");

const teamErrors = validateTeam(team);

if (teamErrors.length === 0) {
    console.log("Team data is valid.");
} else {
    teamErrors.forEach((error) => console.log(error));
}


// ============================================================================
// 18. ROLE DISTINCTIONS
// ============================================================================

const distinctions = {
    "Project Manager vs Product Owner":
        "The project manager coordinates project execution and constraints; " +
        "the product owner prioritizes product value and requirements.",

    "Product Owner vs Business Analyst":
        "The product owner owns product priorities and value decisions; " +
        "the business analyst analyzes requirements and business processes.",

    "Technical Lead vs Developer":
        "The technical lead has broader technical direction and architecture " +
        "responsibilities; developers focus strongly on implementation.",

    "Developer vs QA Engineer":
        "Developers implement functionality; QA engineers verify behavior " +
        "against quality expectations and acceptance criteria.",

    "Technical Lead vs Security Specialist":
        "The technical lead coordinates general technical architecture; " +
        "the security specialist focuses on security threats and controls."
};

console.log("\nROLE DISTINCTIONS");
console.log("=================");

Object.entries(distinctions).forEach(([comparison, explanation]) => {
    console.log(`${comparison}: ${explanation}`);
});


// ============================================================================
// 19. ASYNC EXECUTION
// ============================================================================

runApprovalWorkflow()
    .then(() => {
        console.log("\nPROJECT TEAM STUDY COMPLETE");
    })
    .catch((error) => {
        console.error(`Unexpected workflow error: ${error.message}`);
    });

/*
 * JavaScript-specific considerations:
 *
 * 1. Sets provide efficient membership checks for skills and capabilities.
 * 2. Maps are useful when keys are dynamic and are not necessarily simple
 *    object-property names.
 * 3. Promises model asynchronous approval, API, or workflow operations.
 * 4. Event-driven architecture allows independent components to react to
 *    project events without tightly coupling every component.
 * 5. In a browser application, the same domain model could support a project
 *    dashboard with forms, tables, filters, notifications, and visual reports.
 *
 * For very large task graphs, repeatedly using Array.shift() can become less
 * efficient because elements may need to be reindexed. A queue implemented
 * with an index into an array can provide better behavior.
 */
