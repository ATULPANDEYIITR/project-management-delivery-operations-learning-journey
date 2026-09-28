/**
 * WORK BREAKDOWN STRUCTURE (WBS)
 * Breaking Work into Smaller Parts
 *
 * A self-contained JavaScript study implementation covering:
 * - WBS hierarchy
 * - deliverables and work packages
 * - decomposition
 * - validation
 * - cost roll-up
 * - dependency graphs
 * - topological sorting
 * - critical path
 * - estimation
 * - risk analysis
 * - resource planning
 * - requirements traceability
 * - earned value
 * - reporting
 *
 * Run with:
 *     node wbs.js
 *
 * No external packages are required.
 */

"use strict";

// ============================================================================
// 1. BASIC OUTPUT HELPERS
// ============================================================================

function printSection(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function printSubsection(title) {
    console.log("\n" + "-".repeat(78));
    console.log(title);
    console.log("-".repeat(78));
}

function formatCurrency(value) {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD"
    }).format(value);
}


// ============================================================================
// 2. WBS NODE
// ============================================================================

class WBSNode {
    constructor({
        code,
        name,
        level,
        type,
        description = "",
        durationDays = 0,
        cost = 0,
        owner = "",
        parentCode = null,
        acceptanceCriteria = []
    }) {
        this.code = code;
        this.name = name;
        this.level = level;
        this.type = type;
        this.description = description;
        this.durationDays = durationDays;
        this.cost = cost;
        this.owner = owner;
        this.parentCode = parentCode;
        this.children = [];
        this.dependencies = [];
        this.acceptanceCriteria = acceptanceCriteria;
    }

    get isLeaf() {
        return this.children.length === 0;
    }
}


// ============================================================================
// 3. WBS CONTAINER
// ============================================================================

class WBS {
    constructor(projectName) {
        this.projectName = projectName;
        this.nodes = new Map();
    }

    addNode(node) {
        if (this.nodes.has(node.code)) {
            throw new Error(`Duplicate WBS code: ${node.code}`);
        }

        if (node.parentCode !== null) {
            const parent = this.nodes.get(node.parentCode);

            if (!parent) {
                throw new Error(
                    `Parent ${node.parentCode} does not exist for ${node.code}`
                );
            }

            const expectedLevel = parent.level + 1;

            if (node.level !== expectedLevel) {
                throw new Error(
                    `${node.code}: expected level ${expectedLevel}, ` +
                    `received ${node.level}`
                );
            }

            parent.children.push(node.code);
        }

        this.nodes.set(node.code, node);
    }

    getNode(code) {
        const node = this.nodes.get(code);

        if (!node) {
            throw new Error(`Unknown WBS code: ${code}`);
        }

        return node;
    }

    getRoot() {
        const roots = [...this.nodes.values()]
            .filter(node => node.parentCode === null);

        if (roots.length !== 1) {
            throw new Error(
                `Expected one root, found ${roots.length}`
            );
        }

        return roots[0];
    }

    directChildren(code) {
        return this.getNode(code)
            .children
            .map(childCode => this.getNode(childCode));
    }

    leaves() {
        return [...this.nodes.values()]
            .filter(node => node.isLeaf);
    }

    descendants(code) {
        const result = [];

        const visit = currentCode => {
            const node = this.getNode(currentCode);

            for (const childCode of node.children) {
                result.push(this.getNode(childCode));
                visit(childCode);
            }
        };

        visit(code);
        return result;
    }

    printTree() {
        const root = this.getRoot();

        const visit = (code, prefix = "") => {
            const node = this.getNode(code);

            console.log(
                `${prefix}${node.code} | ${node.name} [${node.type}]`
            );

            for (const childCode of node.children) {
                visit(childCode, prefix + "    ");
            }
        };

        visit(root.code);
    }

    rollupCost(code) {
        const node = this.getNode(code);

        if (node.isLeaf) {
            return node.cost;
        }

        return node.children.reduce(
            (sum, childCode) => sum + this.rollupCost(childCode),
            0
        );
    }

    rollupEffort(code) {
        const node = this.getNode(code);

        if (node.isLeaf) {
            return node.durationDays;
        }

        return node.children.reduce(
            (sum, childCode) => sum + this.rollupEffort(childCode),
            0
        );
    }

    search(query) {
        const normalizedQuery = query.toLowerCase();

        return [...this.nodes.values()].filter(node =>
            node.code.toLowerCase().includes(normalizedQuery) ||
            node.name.toLowerCase().includes(normalizedQuery) ||
            node.description.toLowerCase().includes(normalizedQuery)
        );
    }
}


// ============================================================================
// 4. CREATE THE WBS
// ============================================================================

printSection("1. WORK BREAKDOWN STRUCTURE");

const wbs = new WBS("Enterprise Customer Portal");

wbs.addNode(new WBSNode({
    code: "1",
    name: "Enterprise Customer Portal",
    level: 1,
    type: "Project",
    description: "Complete customer-facing web platform."
}));

const deliverables = [
    ["1.1", "Project Management", "Management and governance"],
    ["1.2", "User Experience", "Research and interface design"],
    ["1.3", "Application Platform", "Core software capabilities"],
    ["1.4", "Security", "Security engineering and verification"],
    ["1.5", "Quality Assurance", "Testing and quality validation"],
    ["1.6", "Deployment", "Production readiness and release"]
];

for (const [code, name, description] of deliverables) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 2,
        type: "Deliverable",
        description,
        parentCode: "1"
    }));
}


// Project Management
for (const [code, name] of [
    ["1.1.1", "Project Planning"],
    ["1.1.2", "Stakeholder Management"],
    ["1.1.3", "Progress Control"]
]) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 3,
        type: "Sub-deliverable",
        parentCode: "1.1"
    }));
}

const managementPackages = [
    ["1.1.1.1", "Create Project Charter", 2, 800],
    ["1.1.1.2", "Create Management Plan", 3, 1200],
    ["1.1.2.1", "Identify Stakeholders", 2, 600],
    ["1.1.2.2", "Create Communication Matrix", 2, 500],
    ["1.1.3.1", "Weekly Status Reporting", 20, 4000],
    ["1.1.3.2", "Change Control", 10, 2500]
];

for (const [code, name, durationDays, cost] of managementPackages) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 4,
        type: "Work Package",
        durationDays,
        cost,
        parentCode: code.substring(0, code.lastIndexOf("."))
    }));
}


// User Experience
for (const [code, name] of [
    ["1.2.1", "User Research"],
    ["1.2.2", "Interaction Design"],
    ["1.2.3", "Visual Design"]
]) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 3,
        type: "Sub-deliverable",
        parentCode: "1.2"
    }));
}

const uxPackages = [
    ["1.2.1.1", "Interview Users", 5, 2000],
    ["1.2.1.2", "Analyze User Needs", 4, 1800],
    ["1.2.2.1", "Create User Flows", 4, 1600],
    ["1.2.2.2", "Create Wireframes", 6, 2400],
    ["1.2.3.1", "Create Design System", 7, 3500],
    ["1.2.3.2", "Create High-Fidelity Screens", 8, 4200]
];

for (const [code, name, durationDays, cost] of uxPackages) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 4,
        type: "Work Package",
        durationDays,
        cost,
        parentCode: code.substring(0, code.lastIndexOf("."))
    }));
}


// Application Platform
for (const [code, name] of [
    ["1.3.1", "Authentication"],
    ["1.3.2", "Customer Profile"],
    ["1.3.3", "Dashboard"],
    ["1.3.4", "Notification Service"]
]) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 3,
        type: "Sub-deliverable",
        parentCode: "1.3"
    }));
}

const applicationPackages = [
    ["1.3.1.1", "Login and Logout", 5, 4500],
    ["1.3.1.2", "Password Recovery", 4, 3200],
    ["1.3.1.3", "Multi-Factor Authentication", 7, 6500],
    ["1.3.2.1", "Profile API", 6, 5200],
    ["1.3.2.2", "Profile Interface", 5, 4100],
    ["1.3.3.1", "Dashboard API", 7, 6200],
    ["1.3.3.2", "Dashboard Interface", 7, 5800],
    ["1.3.4.1", "Email Notification Service", 6, 5000],
    ["1.3.4.2", "In-App Notification Service", 5, 4200]
];

for (const [code, name, durationDays, cost] of applicationPackages) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 4,
        type: "Work Package",
        durationDays,
        cost,
        parentCode: code.substring(0, code.lastIndexOf("."))
    }));
}


// Security
for (const [code, name] of [
    ["1.4.1", "Security Architecture"],
    ["1.4.2", "Application Security"],
    ["1.4.3", "Security Verification"]
]) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 3,
        type: "Sub-deliverable",
        parentCode: "1.4"
    }));
}

const securityPackages = [
    ["1.4.1.1", "Threat Modeling", 5, 4000],
    ["1.4.1.2", "Security Requirements", 4, 3000],
    ["1.4.2.1", "Input Validation Controls", 6, 4500],
    ["1.4.2.2", "Authorization Controls", 6, 5000],
    ["1.4.3.1", "Security Test Suite", 7, 5500],
    ["1.4.3.2", "Vulnerability Assessment", 6, 6500]
];

for (const [code, name, durationDays, cost] of securityPackages) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 4,
        type: "Work Package",
        durationDays,
        cost,
        parentCode: code.substring(0, code.lastIndexOf("."))
    }));
}


// Quality Assurance
for (const [code, name] of [
    ["1.5.1", "Test Planning"],
    ["1.5.2", "Functional Testing"],
    ["1.5.3", "Performance Testing"]
]) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 3,
        type: "Sub-deliverable",
        parentCode: "1.5"
    }));
}

const qaPackages = [
    ["1.5.1.1", "Test Strategy", 3, 1800],
    ["1.5.1.2", "Test Cases", 6, 3200],
    ["1.5.2.1", "Integration Testing", 8, 6000],
    ["1.5.2.2", "System Testing", 8, 6000],
    ["1.5.3.1", "Load Testing", 5, 4000],
    ["1.5.3.2", "Performance Analysis", 4, 3000]
];

for (const [code, name, durationDays, cost] of qaPackages) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 4,
        type: "Work Package",
        durationDays,
        cost,
        parentCode: code.substring(0, code.lastIndexOf("."))
    }));
}


// Deployment
for (const [code, name] of [
    ["1.6.1", "Infrastructure"],
    ["1.6.2", "Release Engineering"],
    ["1.6.3", "Operational Readiness"]
]) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 3,
        type: "Sub-deliverable",
        parentCode: "1.6"
    }));
}

const deploymentPackages = [
    ["1.6.1.1", "Production Infrastructure", 5, 6000],
    ["1.6.1.2", "Monitoring Infrastructure", 4, 3500],
    ["1.6.2.1", "CI/CD Pipeline", 6, 5000],
    ["1.6.2.2", "Production Release", 2, 2500],
    ["1.6.3.1", "Operations Runbook", 4, 2200],
    ["1.6.3.2", "Production Readiness Review", 2, 1500]
];

for (const [code, name, durationDays, cost] of deploymentPackages) {
    wbs.addNode(new WBSNode({
        code,
        name,
        level: 4,
        type: "Work Package",
        durationDays,
        cost,
        parentCode: code.substring(0, code.lastIndexOf("."))
    }));
}

wbs.printTree();


// ============================================================================
// 5. COST AND EFFORT ROLL-UP
// ============================================================================

printSection("2. COST AND EFFORT ROLL-UP");

for (const node of wbs.directChildren("1")) {
    console.log(
        `${node.code.padEnd(8)} ` +
        `${node.name.padEnd(26)} ` +
        `${formatCurrency(wbs.rollupCost(node.code))}`
    );
}

const totalCost = wbs.rollupCost("1");
const totalEffort = wbs.rollupEffort("1");

console.log(`\nTotal cost: ${formatCurrency(totalCost)}`);
console.log(`Total estimated person-days: ${totalEffort}`);

console.log(
    "\nEffort aggregation is not the same as calendar duration. " +
    "Parallel work can reduce elapsed project time."
);


// ============================================================================
// 6. DEPENDENCY GRAPH
// ============================================================================

printSection("3. DEPENDENCY MODEL");

const dependencyMap = {
    "1.2.1.1": [],
    "1.2.1.2": ["1.2.1.1"],
    "1.2.2.1": ["1.2.1.2"],
    "1.2.2.2": ["1.2.2.1"],
    "1.2.3.1": ["1.2.2.2"],
    "1.2.3.2": ["1.2.3.1"],

    "1.3.1.1": ["1.2.2.2"],
    "1.3.1.2": ["1.3.1.1"],
    "1.3.1.3": ["1.3.1.1"],
    "1.3.2.1": ["1.2.2.2"],
    "1.3.2.2": ["1.3.2.1", "1.2.3.2"],
    "1.3.3.1": ["1.3.2.1"],
    "1.3.3.2": ["1.3.3.1", "1.2.3.2"],
    "1.3.4.1": ["1.3.1.1"],
    "1.3.4.2": ["1.3.1.1"],

    "1.4.1.1": [],
    "1.4.1.2": ["1.4.1.1"],
    "1.4.2.1": ["1.4.1.2"],
    "1.4.2.2": ["1.4.1.2"],
    "1.4.3.1": ["1.4.2.1", "1.4.2.2"],
    "1.4.3.2": ["1.4.3.1"],

    "1.5.1.1": [],
    "1.5.1.2": ["1.5.1.1"],
    "1.5.2.1": ["1.5.1.2", "1.3.2.2", "1.3.3.2"],
    "1.5.2.2": ["1.5.2.1"],
    "1.5.3.1": ["1.5.2.2"],
    "1.5.3.2": ["1.5.3.1"],

    "1.6.1.1": ["1.3.3.2"],
    "1.6.1.2": ["1.6.1.1"],
    "1.6.2.1": ["1.6.1.1"],
    "1.6.2.2": ["1.5.2.2", "1.4.3.2", "1.6.2.1"],
    "1.6.3.1": ["1.6.2.1"],
    "1.6.3.2": ["1.6.2.2", "1.6.3.1"]
};

for (const [code, dependencies] of Object.entries(dependencyMap)) {
    wbs.getNode(code).dependencies = dependencies;
}


// ============================================================================
// 7. TOPOLOGICAL SORT
// ============================================================================

function topologicalSort(tasks, dependencies) {
    const taskSet = new Set(tasks);
    const indegree = new Map();
    const outgoing = new Map();

    for (const task of taskSet) {
        indegree.set(task, 0);
        outgoing.set(task, []);
    }

    for (const [task, dependencyList] of Object.entries(dependencies)) {
        if (!taskSet.has(task)) {
            continue;
        }

        for (const dependency of dependencyList) {
            if (!taskSet.has(dependency)) {
                throw new Error(
                    `Unknown dependency ${dependency} for ${task}`
                );
            }

            indegree.set(
                task,
                indegree.get(task) + 1
            );

            outgoing.get(dependency).push(task);
        }
    }

    const queue = [...taskSet]
        .filter(task => indegree.get(task) === 0)
        .sort();

    const result = [];

    while (queue.length > 0) {
        const current = queue.shift();
        result.push(current);

        for (const successor of outgoing.get(current).sort()) {
            indegree.set(
                successor,
                indegree.get(successor) - 1
            );

            if (indegree.get(successor) === 0) {
                queue.push(successor);
                queue.sort();
            }
        }
    }

    if (result.length !== taskSet.size) {
        throw new Error(
            "Dependency graph contains a cycle."
        );
    }

    return result;
}


// ============================================================================
// 8. EARLIEST SCHEDULE
// ============================================================================

printSection("4. DEPENDENCY-AWARE SCHEDULE");

const leafNodes = wbs.leaves();

const durations = Object.fromEntries(
    leafNodes.map(node => [node.code, node.durationDays])
);

const leafDependencyMap = Object.fromEntries(
    leafNodes.map(node => [
        node.code,
        dependencyMap[node.code] || []
    ])
);

const scheduleOrder = topologicalSort(
    leafNodes.map(node => node.code),
    leafDependencyMap
);

const earliestStart = {};
const earliestFinish = {};

for (const code of scheduleOrder) {
    const dependencies = leafDependencyMap[code];

    earliestStart[code] = dependencies.length > 0
        ? Math.max(
            ...dependencies.map(
                dependency => earliestFinish[dependency]
            )
        )
        : 0;

    earliestFinish[code] =
        earliestStart[code] + durations[code];
}

const projectDuration = Math.max(
    ...Object.values(earliestFinish)
);

for (const code of scheduleOrder) {
    console.log(
        `${code.padEnd(8)} ` +
        `Start=${earliestStart[code].toFixed(1).padStart(5)} ` +
        `Finish=${earliestFinish[code].toFixed(1).padStart(5)} ` +
        wbs.getNode(code).name
    );
}

console.log(
    `\nDependency-aware duration: ${projectDuration.toFixed(1)} days`
);


// ============================================================================
// 9. CRITICAL PATH
// ============================================================================

printSection("5. CRITICAL PATH");

const successors = new Map();

for (const code of scheduleOrder) {
    successors.set(code, []);
}

for (const [task, dependencies] of Object.entries(leafDependencyMap)) {
    for (const dependency of dependencies) {
        successors.get(dependency).push(task);
    }
}

const latestFinish = {};
const latestStart = {};

for (const code of scheduleOrder) {
    latestFinish[code] = projectDuration;
}

for (const code of [...scheduleOrder].reverse()) {
    const taskSuccessors = successors.get(code);

    if (taskSuccessors.length > 0) {
        latestFinish[code] = Math.min(
            ...taskSuccessors.map(
                successor => latestStart[successor]
            )
        );
    }

    latestStart[code] =
        latestFinish[code] - durations[code];
}

const taskFloat = {};

for (const code of scheduleOrder) {
    taskFloat[code] =
        latestStart[code] - earliestStart[code];
}

const criticalPath = scheduleOrder.filter(
    code => Math.abs(taskFloat[code]) < 1e-9
);

for (const code of criticalPath) {
    console.log(
        `${code.padEnd(8)} ` +
        `${wbs.getNode(code).name.padEnd(35)} ` +
        `Float=${taskFloat[code].toFixed(1)}`
    );
}


// ============================================================================
// 10. VALIDATION
// ============================================================================

printSection("6. WBS VALIDATION");

function validateWBS(project) {
    const errors = [];

    let rootCount = 0;

    for (const node of project.nodes.values()) {
        if (node.parentCode === null) {
            rootCount++;
        }

        if (node.parentCode !== null &&
            !project.nodes.has(node.parentCode)) {
            errors.push(
                `${node.code}: parent ${node.parentCode} does not exist`
            );
        }

        if (node.level < 1) {
            errors.push(
                `${node.code}: invalid level`
            );
        }

        if (node.cost < 0) {
            errors.push(
                `${node.code}: negative cost`
            );
        }

        if (node.durationDays < 0) {
            errors.push(
                `${node.code}: negative duration`
            );
        }

        if (node.type === "Work Package" &&
            !node.isLeaf) {
            errors.push(
                `${node.code}: work package has children`
            );
        }
    }

    if (rootCount !== 1) {
        errors.push(
            `Expected exactly one root, found ${rootCount}`
        );
    }

    return errors;
}

const validationErrors = validateWBS(wbs);

if (validationErrors.length === 0) {
    console.log("WBS validation passed.");
} else {
    for (const error of validationErrors) {
        console.log("ERROR:", error);
    }
}


// ============================================================================
// 11. WBS DICTIONARY
// ============================================================================

printSection("7. WBS DICTIONARY");

const wbsDictionary = {
    code: "1.3.1.3",
    name: "Multi-Factor Authentication",
    description:
        "Implement an additional authentication factor for protected accounts.",
    owner: "Security Engineer",
    inputs: [
        "Security requirements",
        "Identity architecture"
    ],
    outputs: [
        "MFA implementation",
        "Configuration documentation"
    ],
    acceptanceCriteria: [
        "Second factor is required for configured users.",
        "Recovery behavior is documented.",
        "Automated security tests pass."
    ],
    estimatedDurationDays: 7,
    estimatedCost: 6500,
    dependencies: [
        "1.3.1.1"
    ]
};

console.log(JSON.stringify(wbsDictionary, null, 2));


// ============================================================================
// 12. THREE-POINT ESTIMATION
// ============================================================================

printSection("8. THREE-POINT ESTIMATION");

function threePointEstimate(optimistic, mostLikely, pessimistic) {
    if (
        optimistic > mostLikely ||
        mostLikely > pessimistic
    ) {
        throw new Error(
            "Expected optimistic <= most likely <= pessimistic."
        );
    }

    const expected =
        (optimistic + 4 * mostLikely + pessimistic) / 6;

    const variance =
        Math.pow((pessimistic - optimistic) / 6, 2);

    return {
        expected,
        variance
    };
}

const estimate = threePointEstimate(4, 7, 13);

console.log(
    `Expected duration: ${estimate.expected.toFixed(2)} days`
);
console.log(
    `Variance: ${estimate.variance.toFixed(2)}`
);


// ============================================================================
// 13. RISK ANALYSIS
// ============================================================================

printSection("9. RISK ANALYSIS");

class Risk {
    constructor(name, probability, impactCost, mitigationCost = 0) {
        if (probability < 0 || probability > 1) {
            throw new Error(
                "Probability must be between 0 and 1."
            );
        }

        if (impactCost < 0 || mitigationCost < 0) {
            throw new Error(
                "Costs cannot be negative."
            );
        }

        this.name = name;
        this.probability = probability;
        this.impactCost = impactCost;
        this.mitigationCost = mitigationCost;
    }

    get expectedMonetaryValue() {
        return this.probability * this.impactCost;
    }
}

const risks = [
    new Risk(
        "Third-party API instability",
        0.25,
        10000,
        1500
    ),
    new Risk(
        "Security remediation",
        0.20,
        15000,
        2500
    ),
    new Risk(
        "Performance rework",
        0.30,
        8000,
        1200
    )
];

let totalRiskExposure = 0;

for (const risk of risks) {
    const emv = risk.expectedMonetaryValue;
    totalRiskExposure += emv;

    console.log(
        `${risk.name}: ` +
        `Probability=${(risk.probability * 100).toFixed(0)}%, ` +
        `EMV=${formatCurrency(emv)}`
    );
}

console.log(
    `Total expected risk exposure: ` +
    `${formatCurrency(totalRiskExposure)}`
);


// ============================================================================
// 14. RESOURCE MODEL
// ============================================================================

printSection("10. RESOURCE PLANNING");

class Resource {
    constructor(name, role, capacityPercent, dailyCost) {
        if (capacityPercent <= 0 || capacityPercent > 100) {
            throw new Error(
                "Capacity must be greater than 0 and at most 100."
            );
        }

        if (dailyCost < 0) {
            throw new Error(
                "Daily cost cannot be negative."
            );
        }

        this.name = name;
        this.role = role;
        this.capacityPercent = capacityPercent;
        this.dailyCost = dailyCost;
    }
}

const resources = [
    new Resource("Asha", "Project Manager", 80, 450),
    new Resource("Ravi", "Backend Engineer", 100, 650),
    new Resource("Meera", "Frontend Engineer", 100, 600),
    new Resource("Kabir", "Security Engineer", 60, 700),
    new Resource("Neha", "QA Engineer", 100, 500)
];

for (const resource of resources) {
    console.log(
        `${resource.name.padEnd(10)} ` +
        `${resource.role.padEnd(22)} ` +
        `${resource.capacityPercent}% capacity ` +
        `${formatCurrency(resource.dailyCost)}/day`
    );
}


// ============================================================================
// 15. REQUIREMENT TRACEABILITY
// ============================================================================

printSection("11. REQUIREMENT TRACEABILITY");

const requirements = {
    "REQ-001": ["1.3.1.1", "1.3.1.2", "1.3.1.3"],
    "REQ-002": ["1.3.2.1", "1.3.2.2"],
    "REQ-003": ["1.4.2.1", "1.4.2.2"],
    "REQ-004": ["1.5.2.1", "1.5.2.2"]
};

for (const [requirement, workPackages] of Object.entries(requirements)) {
    console.log(requirement);

    for (const workPackage of workPackages) {
        console.log(
            `    -> ${workPackage}: ` +
            wbs.getNode(workPackage).name
        );
    }
}


// ============================================================================
// 16. EARNED VALUE
// ============================================================================

printSection("12. EARNED VALUE MANAGEMENT");

class EarnedValue {
    constructor(plannedValue, earnedValue, actualCost) {
        if (
            plannedValue < 0 ||
            earnedValue < 0 ||
            actualCost < 0
        ) {
            throw new Error(
                "Earned-value inputs cannot be negative."
            );
        }

        this.plannedValue = plannedValue;
        this.earnedValue = earnedValue;
        this.actualCost = actualCost;
    }

    get costVariance() {
        return this.earnedValue - this.actualCost;
    }

    get scheduleVariance() {
        return this.earnedValue - this.plannedValue;
    }

    get costPerformanceIndex() {
        return this.actualCost === 0
            ? Infinity
            : this.earnedValue / this.actualCost;
    }

    get schedulePerformanceIndex() {
        return this.plannedValue === 0
            ? Infinity
            : this.earnedValue / this.plannedValue;
    }
}

const earnedValue = new EarnedValue(
    50000,
    45000,
    48000
);

console.log(
    `PV: ${formatCurrency(earnedValue.plannedValue)}`
);
console.log(
    `EV: ${formatCurrency(earnedValue.earnedValue)}`
);
console.log(
    `AC: ${formatCurrency(earnedValue.actualCost)}`
);
console.log(
    `CV: ${formatCurrency(earnedValue.costVariance)}`
);
console.log(
    `SV: ${formatCurrency(earnedValue.scheduleVariance)}`
);
console.log(
    `CPI: ${earnedValue.costPerformanceIndex.toFixed(3)}`
);
console.log(
    `SPI: ${earnedValue.schedulePerformanceIndex.toFixed(3)}`
);


// ============================================================================
// 17. CHANGE CONTROL
// ============================================================================

printSection("13. CHANGE CONTROL");

class ChangeRequest {
    constructor({
        id,
        description,
        estimatedCost,
        estimatedDurationDays,
        reason,
        status = "Proposed"
    }) {
        this.id = id;
        this.description = description;
        this.estimatedCost = estimatedCost;
        this.estimatedDurationDays = estimatedDurationDays;
        this.reason = reason;
        this.status = status;
    }
}

const changeRequest = new ChangeRequest({
    id: "CR-001",
    description: "Add enterprise single sign-on",
    estimatedCost: 12000,
    estimatedDurationDays: 8,
    reason: "New customer requirement"
});

console.log(changeRequest);

console.log(
    "\nA proposed scope change should be evaluated before it becomes " +
    "part of the approved baseline."
);


// ============================================================================
// 18. SEARCHING THE WBS
// ============================================================================

printSection("14. WBS SEARCH");

const securityResults = wbs.search("security");

for (const node of securityResults) {
    console.log(
        `${node.code}: ${node.name}`
    );
}


// ============================================================================
// 19. PERFORMANCE CONSIDERATIONS
// ============================================================================

printSection("15. PERFORMANCE CONSIDERATIONS");

console.log(`
Tree traversal: O(N)
Linear text search: O(N)
Cost roll-up: O(N) when every node is visited once
Topological sorting: O(V + E)
Critical-path processing: O(V + E)

N represents WBS nodes.
V represents dependency-graph vertices.
E represents dependency relationships.

For large systems, Maps provide efficient direct lookup by WBS code.
Additional indexes can be maintained for owner, status, project, cost center,
or deliverable type when repeated filtered queries are required.
`);


// ============================================================================
// 20. CACHED COST ROLL-UP
// ============================================================================

printSubsection("Cached Roll-Up");

class CachedWBS extends WBS {
    constructor(projectName) {
        super(projectName);
        this.costCache = new Map();
    }

    rollupCost(code) {
        if (this.costCache.has(code)) {
            return this.costCache.get(code);
        }

        const value = super.rollupCost(code);
        this.costCache.set(code, value);
        return value;
    }

    invalidateCostCache() {
        this.costCache.clear();
    }
}

const cached = new CachedWBS("Cache Demonstration");

cached.addNode(new WBSNode({
    code: "1",
    name: "Example Project",
    level: 1,
    type: "Project"
}));

cached.addNode(new WBSNode({
    code: "1.1",
    name: "Deliverable",
    level: 2,
    type: "Deliverable",
    parentCode: "1"
}));

cached.addNode(new WBSNode({
    code: "1.1.1",
    name: "Work Package A",
    level: 3,
    type: "Work Package",
    cost: 1000,
    parentCode: "1.1"
}));

cached.addNode(new WBSNode({
    code: "1.1.2",
    name: "Work Package B",
    level: 3,
    type: "Work Package",
    cost: 1500,
    parentCode: "1.1"
}));

console.log(
    "First calculation:",
    formatCurrency(cached.rollupCost("1"))
);

console.log(
    "Cached calculation:",
    formatCurrency(cached.rollupCost("1"))
);


// ============================================================================
// 21. SECURITY CONSIDERATIONS
// ============================================================================

printSection("16. SECURITY CONSIDERATIONS");

console.log(`
A production WBS platform can contain sensitive budgets, personnel information,
security architecture, vulnerabilities, customer requirements, and deployment
details.

Important controls include:
- authentication,
- authorization,
- least-privilege access,
- audit logging,
- input validation,
- protected baseline changes,
- encrypted transport and storage where appropriate,
- dependency validation,
- controlled exports,
- traceable approval history.
`);


// ============================================================================
// 22. WBS VS RELATED STRUCTURES
// ============================================================================

printSection("17. WBS VERSUS RELATED STRUCTURES");

const comparison = [
    ["WBS", "Scope hierarchy", "What must be delivered?"],
    ["Schedule", "Time and dependency model", "When can work happen?"],
    ["Organization chart", "People hierarchy", "Who reports to whom?"],
    ["RACI", "Responsibility model", "Who is responsible or accountable?"],
    ["Risk register", "Uncertainty model", "What could affect objectives?"],
    ["Product backlog", "Prioritized product work", "What should be prioritized?"],
    ["Roadmap", "Strategic timeline", "What outcomes are planned over time?"]
];

for (const [structure, purpose, question] of comparison) {
    console.log(
        `${structure.padEnd(22)} | ` +
        `${purpose.padEnd(28)} | ` +
        question
    );
}


// ============================================================================
// 23. QUALITY GATES
// ============================================================================

printSection("18. AUTOMATED QUALITY GATES");

function qualityGate(project) {
    const rootCount = [...project.nodes.values()]
        .filter(node => node.parentCode === null)
        .length;

    const allCostsValid = [...project.nodes.values()]
        .every(node => node.cost >= 0);

    const allDurationsValid = [...project.nodes.values()]
        .every(node => node.durationDays >= 0);

    const workPackagesAreLeaves = [...project.nodes.values()]
        .every(node =>
            node.type !== "Work Package" || node.isLeaf
        );

    const allParentsExist = [...project.nodes.values()]
        .every(node =>
            node.parentCode === null ||
            project.nodes.has(node.parentCode)
        );

    return {
        singleRoot: rootCount === 1,
        nonNegativeCosts: allCostsValid,
        nonNegativeDurations: allDurationsValid,
        workPackagesAreLeaves,
        allParentsExist
    };
}

const gates = qualityGate(wbs);

for (const [name, passed] of Object.entries(gates)) {
    console.log(
        `${name.padEnd(28)}: ${passed ? "PASS" : "FAIL"}`
    );
}


// ============================================================================
// 24. PRACTICAL MINI-EXAMPLE
// ============================================================================

printSection("19. MINI DECOMPOSITION EXAMPLE");

const appointmentPlatform = {
    project: "Online Appointment Platform",
    deliverables: [
        "Patient Management",
        "Appointment Management",
        "Notifications",
        "Testing",
        "Deployment"
    ]
};

console.log(appointmentPlatform.project);

for (const deliverable of appointmentPlatform.deliverables) {
    console.log(`  - ${deliverable}`);
}

console.log(`
Example decomposition:

Appointment Management
    User Availability
        Provider availability API
        Availability interface
    Booking
        Create appointment
        Reschedule appointment
        Cancel appointment
    Confirmation
        Booking confirmation
        Calendar integration

The quality test is whether the decomposition completely and unambiguously
represents the intended scope while remaining manageable for estimation,
assignment, control, and acceptance.
`);


// ============================================================================
// 25. FINAL REPORT
// ============================================================================

printSection("20. FINAL WBS REPORT");

console.log(`Project: ${wbs.projectName}`);
console.log(`WBS nodes: ${wbs.nodes.size}`);
console.log(`Major deliverables: ${wbs.directChildren("1").length}`);
console.log(`Work packages: ${wbs.leaves().length}`);
console.log(`Budget: ${formatCurrency(totalCost)}`);
console.log(`Estimated person-days: ${totalEffort}`);
console.log(`Dependency-aware duration: ${projectDuration} days`);
console.log(`Critical work packages: ${criticalPath.length}`);
console.log(
    `Expected risk exposure: ${formatCurrency(totalRiskExposure)}`
);

console.log(`
The WBS answers the scope question: "What must be delivered?"

The schedule answers the timing question: "When can the work occur?"

The resource model answers the capacity question: "Who or what capacity is
available?"

The cost model answers the financial question: "What does the planned scope
cost?"

The risk model answers the uncertainty question: "What could affect the plan?"

Keeping these concepts related but distinct produces a clearer project-control
system.
`);
