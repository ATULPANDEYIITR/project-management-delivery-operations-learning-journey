/*
 * Stakeholder Identification: practical JavaScript study file.
 *
 * This implementation complements the Python study by emphasizing:
 * - JavaScript classes and objects
 * - Functional array operations
 * - Map and Set
 * - validation
 * - browser-friendly data structures
 * - JSON serialization
 * - asynchronous stakeholder discovery
 * - event-driven updates
 * - immutable-style analysis
 * - performance measurement
 * - dynamic stakeholder registers
 *
 * The file runs in Node.js and uses only built-in JavaScript features.
 */

"use strict";

// -----------------------------------------------------------------------------
// 1. BASIC STAKEHOLDER CONCEPT
// -----------------------------------------------------------------------------

const basicStakeholders = [
    {
        name: "Project sponsor",
        reason: "Provides authority, funding, and strategic direction."
    },
    {
        name: "End users",
        reason: "Use the resulting product or service."
    },
    {
        name: "Operations team",
        reason: "Runs and maintains the resulting system."
    },
    {
        name: "Regulator",
        reason: "Defines or enforces applicable requirements."
    },
    {
        name: "Supplier",
        reason: "Provides an external dependency."
    }
];

console.log("BASIC STAKEHOLDERS");
basicStakeholders.forEach(({ name, reason }) => {
    console.log(`- ${name}: ${reason}`);
});


// -----------------------------------------------------------------------------
// 2. STAKEHOLDER CLASS
// -----------------------------------------------------------------------------

class Stakeholder {
    constructor({
        id,
        name,
        type,
        role,
        organization,
        interests = [],
        power,
        interest,
        influence,
        impact,
        legitimacy = 1,
        urgency = 1,
        currentEngagement = "Neutral",
        desiredEngagement = "Supportive",
        communicationFrequency = "Monthly"
    }) {
        this.id = id;
        this.name = name;
        this.type = type;
        this.role = role;
        this.organization = organization;
        this.interests = [...interests];
        this.power = power;
        this.interest = interest;
        this.influence = influence;
        this.impact = impact;
        this.legitimacy = legitimacy;
        this.urgency = urgency;
        this.currentEngagement = currentEngagement;
        this.desiredEngagement = desiredEngagement;
        this.communicationFrequency = communicationFrequency;

        this.validate();
    }

    validate() {
        if (!this.id || !this.name) {
            throw new Error("Stakeholder ID and name are required.");
        }

        for (const [field, value] of [
            ["power", this.power],
            ["interest", this.interest],
            ["influence", this.influence],
            ["impact", this.impact]
        ]) {
            if (!Number.isFinite(value) || value < 0 || value > 10) {
                throw new Error(`${field} must be between 0 and 10.`);
            }
        }

        for (const [field, value] of [
            ["legitimacy", this.legitimacy],
            ["urgency", this.urgency]
        ]) {
            if (!Number.isFinite(value) || value < 0 || value > 1) {
                throw new Error(`${field} must be between 0 and 1.`);
            }
        }
    }

    get powerInterestScore() {
        return this.power * this.interest;
    }

    get influenceImpactScore() {
        return this.influence * this.impact;
    }

    get salienceScore() {
        return this.power * this.legitimacy * this.urgency;
    }

    powerInterestCategory() {
        if (this.power >= 5 && this.interest >= 5) {
            return "Manage closely";
        }

        if (this.power >= 5 && this.interest < 5) {
            return "Keep satisfied";
        }

        if (this.power < 5 && this.interest >= 5) {
            return "Keep informed";
        }

        return "Monitor";
    }

    toJSON() {
        return {
            id: this.id,
            name: this.name,
            type: this.type,
            role: this.role,
            organization: this.organization,
            interests: [...this.interests],
            power: this.power,
            interest: this.interest,
            influence: this.influence,
            impact: this.impact,
            legitimacy: this.legitimacy,
            urgency: this.urgency,
            currentEngagement: this.currentEngagement,
            desiredEngagement: this.desiredEngagement,
            communicationFrequency: this.communicationFrequency
        };
    }
}


// -----------------------------------------------------------------------------
// 3. STAKEHOLDER REGISTER
// -----------------------------------------------------------------------------

class StakeholderRegister {
    constructor() {
        // Map provides efficient lookup by stable stakeholder ID.
        this.stakeholders = new Map();
        this.relationships = [];
    }

    add(stakeholder) {
        if (this.stakeholders.has(stakeholder.id)) {
            throw new Error(`Duplicate stakeholder ID: ${stakeholder.id}`);
        }

        this.stakeholders.set(stakeholder.id, stakeholder);
    }

    get(id) {
        const stakeholder = this.stakeholders.get(id);

        if (!stakeholder) {
            throw new Error(`Unknown stakeholder: ${id}`);
        }

        return stakeholder;
    }

    addRelationship(sourceId, targetId, type, strength = 1) {
        this.get(sourceId);
        this.get(targetId);

        if (sourceId === targetId) {
            throw new Error("A stakeholder cannot have a self-relationship.");
        }

        if (strength <= 0 || strength > 1) {
            throw new Error("Relationship strength must be > 0 and <= 1.");
        }

        this.relationships.push({
            sourceId,
            targetId,
            type,
            strength
        });
    }

    values() {
        return [...this.stakeholders.values()];
    }

    filter(predicate) {
        return this.values().filter(predicate);
    }
}


// -----------------------------------------------------------------------------
// 4. SAMPLE REGISTER
// -----------------------------------------------------------------------------

function createSampleRegister() {
    const register = new StakeholderRegister();

    [
        new Stakeholder({
            id: "S01",
            name: "Executive Sponsor",
            type: "Internal",
            role: "Sponsor",
            organization: "Public Service Department",
            interests: ["Strategy", "Budget", "Accountability"],
            power: 9,
            interest: 7,
            influence: 9,
            impact: 8
        }),

        new Stakeholder({
            id: "S02",
            name: "Project Manager",
            type: "Internal",
            role: "Project Manager",
            organization: "Public Service Department",
            interests: ["Delivery", "Risk", "Coordination"],
            power: 7,
            interest: 10,
            influence: 8,
            impact: 9,
            currentEngagement: "Leading",
            desiredEngagement: "Leading",
            communicationFrequency: "Weekly"
        }),

        new Stakeholder({
            id: "S03",
            name: "IT Operations",
            type: "Internal",
            role: "Operations",
            organization: "Public Service Department",
            interests: ["Reliability", "Maintainability", "Security"],
            power: 7,
            interest: 8,
            influence: 8,
            impact: 9,
            communicationFrequency: "Weekly"
        }),

        new Stakeholder({
            id: "S04",
            name: "Frontline Employees",
            type: "Internal",
            role: "Service Staff",
            organization: "Public Service Department",
            interests: ["Usability", "Workload", "Training"],
            power: 5,
            interest: 9,
            influence: 6,
            impact: 9
        }),

        new Stakeholder({
            id: "S05",
            name: "Citizens",
            type: "External",
            role: "End Users",
            organization: "Public",
            interests: ["Accessibility", "Privacy", "Service Quality"],
            power: 5,
            interest: 10,
            influence: 7,
            impact: 10
        }),

        new Stakeholder({
            id: "S06",
            name: "Technology Supplier",
            type: "External",
            role: "Vendor",
            organization: "External Supplier",
            interests: ["Contract Performance", "Commercial Outcome"],
            power: 6,
            interest: 7,
            influence: 7,
            impact: 7
        }),

        new Stakeholder({
            id: "S07",
            name: "Data Protection Authority",
            type: "External",
            role: "Regulator",
            organization: "Government",
            interests: ["Privacy", "Lawful Processing", "Security"],
            power: 9,
            interest: 6,
            influence: 10,
            impact: 9
        }),

        new Stakeholder({
            id: "S08",
            name: "Accessibility Advocates",
            type: "External",
            role: "Community Representative",
            organization: "Civil Society",
            interests: ["Inclusive Design", "Accessibility"],
            power: 4,
            interest: 8,
            influence: 6,
            impact: 8
        }),

        new Stakeholder({
            id: "S09",
            name: "Finance Department",
            type: "Internal",
            role: "Budget Controller",
            organization: "Public Service Department",
            interests: ["Cost Control", "Budget Compliance"],
            power: 7,
            interest: 5,
            influence: 7,
            impact: 6
        }),

        new Stakeholder({
            id: "S10",
            name: "Cybersecurity Team",
            type: "Internal",
            role: "Security",
            organization: "Public Service Department",
            interests: ["Threat Reduction", "Security Controls"],
            power: 8,
            interest: 8,
            influence: 9,
            impact: 10
        })
    ].forEach(stakeholder => register.add(stakeholder));

    register.addRelationship("S01", "S02", "supports", 0.9);
    register.addRelationship("S02", "S03", "collaborates_with", 0.9);
    register.addRelationship("S02", "S04", "collaborates_with", 0.8);
    register.addRelationship("S02", "S06", "collaborates_with", 0.8);
    register.addRelationship("S07", "S10", "influences", 0.9);
    register.addRelationship("S10", "S03", "influences", 0.9);
    register.addRelationship("S05", "S02", "influences", 0.6);
    register.addRelationship("S08", "S02", "influences", 0.5);
    register.addRelationship("S09", "S01", "reports_to", 0.7);
    register.addRelationship("S06", "S03", "depends_on", 0.8);

    return register;
}


// -----------------------------------------------------------------------------
// 5. IDENTIFICATION HEURISTICS
// -----------------------------------------------------------------------------

function identifyCandidateStakeholders(context) {
    const lower = context.toLowerCase();

    const candidates = new Set([
        "Project Sponsor",
        "Project Manager",
        "Project Team",
        "End Users",
        "Customers",
        "Senior Management",
        "Finance",
        "Legal",
        "IT Operations",
        "Suppliers"
    ]);

    if (/\b(bank|payment|finance)\b/.test(lower)) {
        ["Financial Regulator", "Payment Processor", "Auditor"]
            .forEach(name => candidates.add(name));
    }

    if (/\b(health|hospital|medical)\b/.test(lower)) {
        ["Patients", "Clinicians", "Healthcare Regulator", "Privacy Officer"]
            .forEach(name => candidates.add(name));
    }

    if (/\b(school|education|student)\b/.test(lower)) {
        ["Students", "Teachers", "Parents", "Education Authority"]
            .forEach(name => candidates.add(name));
    }

    if (/\b(cloud|software|platform|app)\b/.test(lower)) {
        ["Cloud Provider", "System Administrator", "Data Protection Officer"]
            .forEach(name => candidates.add(name));
    }

    return [...candidates].sort();
}

const identificationQuestions = [
    "Who funds or authorizes the initiative?",
    "Who performs work affected by the initiative?",
    "Who uses the resulting product or service?",
    "Who receives benefits?",
    "Who bears costs or disruption?",
    "Who can approve, block, delay, or materially change the initiative?",
    "Who controls critical data or infrastructure?",
    "Who supplies important dependencies?",
    "Who establishes legal or regulatory requirements?",
    "Who represents affected communities?",
    "Who can influence reputation or public perception?",
    "Who becomes relevant after a significant scope or operating-model change?"
];


// -----------------------------------------------------------------------------
// 6. FUNCTIONAL ANALYSIS
// -----------------------------------------------------------------------------

function groupBy(items, keyFunction) {
    return items.reduce((groups, item) => {
        const key = keyFunction(item);

        if (!groups.has(key)) {
            groups.set(key, []);
        }

        groups.get(key).push(item);
        return groups;
    }, new Map());
}

function weightedPriorityScore(stakeholder) {
    return (
        0.25 * stakeholder.power +
        0.20 * stakeholder.interest +
        0.20 * stakeholder.influence +
        0.20 * stakeholder.impact +
        0.15 * (stakeholder.legitimacy * 10)
    );
}

function classifySalience(stakeholder) {
    const activeAttributes = [
        stakeholder.power >= 5,
        stakeholder.legitimacy >= 0.5,
        stakeholder.urgency >= 0.5
    ].filter(Boolean).length;

    if (activeAttributes === 3) return "Definitive";
    if (activeAttributes === 2) return "Expectant";
    if (activeAttributes === 1) return "Latent";
    return "Low salience";
}

function analyzeRegister(register) {
    const stakeholders = register.values();

    const matrix = groupBy(
        stakeholders,
        stakeholder => stakeholder.powerInterestCategory()
    );

    console.log("\nPOWER-INTEREST MATRIX");

    for (const [category, members] of matrix.entries()) {
        console.log(`${category}:`);
        members.forEach(member => {
            console.log(`  - ${member.name}`);
        });
    }

    console.log("\nMULTI-MODEL ANALYSIS");

    [...stakeholders]
        .sort(
            (a, b) =>
                weightedPriorityScore(b) -
                weightedPriorityScore(a)
        )
        .forEach(stakeholder => {
            console.log(
                `${stakeholder.name}: ` +
                `power-interest=${stakeholder.powerInterestScore}, ` +
                `influence-impact=${stakeholder.influenceImpactScore}, ` +
                `salience=${stakeholder.salienceScore.toFixed(2)}, ` +
                `weighted=${weightedPriorityScore(stakeholder).toFixed(2)}, ` +
                `salienceClass=${classifySalience(stakeholder)}`
            );
        });
}


// -----------------------------------------------------------------------------
// 7. ENGAGEMENT GAP ANALYSIS
// -----------------------------------------------------------------------------

const engagementOrder = new Map([
    ["Unaware", 0],
    ["Resistant", 1],
    ["Neutral", 2],
    ["Supportive", 3],
    ["Leading", 4]
]);

function engagementGap(stakeholder) {
    return (
        engagementOrder.get(stakeholder.desiredEngagement) -
        engagementOrder.get(stakeholder.currentEngagement)
    );
}

function createEngagementPlan(register) {
    return register.values()
        .map(stakeholder => {
            const gap = engagementGap(stakeholder);

            let action;

            if (gap <= 0) {
                action = "Maintain or monitor engagement.";
            } else if (gap === 1) {
                action = "Use targeted communication and participation.";
            } else if (gap === 2) {
                action = "Use structured consultation and issue management.";
            } else {
                action = "Use intensive engagement and change management.";
            }

            return {
                stakeholder: stakeholder.name,
                current: stakeholder.currentEngagement,
                desired: stakeholder.desiredEngagement,
                gap,
                action
            };
        })
        .sort((a, b) => b.gap - a.gap);
}


// -----------------------------------------------------------------------------
// 8. RELATIONSHIP GRAPH
// -----------------------------------------------------------------------------

class StakeholderGraph {
    constructor(register) {
        this.adjacency = new Map();

        for (const stakeholder of register.values()) {
            this.adjacency.set(stakeholder.id, new Set());
        }

        for (const relationship of register.relationships) {
            this.adjacency
                .get(relationship.sourceId)
                .add(relationship.targetId);
        }
    }

    directConnections(id) {
        return [...(this.adjacency.get(id) || [])];
    }

    shortestPath(source, target) {
        if (source === target) {
            return [source];
        }

        const queue = [source];
        const previous = new Map([[source, null]]);

        while (queue.length > 0) {
            const current = queue.shift();

            for (const neighbor of this.adjacency.get(current) || []) {
                if (previous.has(neighbor)) {
                    continue;
                }

                previous.set(neighbor, current);

                if (neighbor === target) {
                    const path = [target];
                    let cursor = target;

                    while (previous.get(cursor) !== null) {
                        cursor = previous.get(cursor);
                        path.push(cursor);
                    }

                    return path.reverse();
                }

                queue.push(neighbor);
            }
        }

        return null;
    }
}


// -----------------------------------------------------------------------------
// 9. RACI VALIDATION
// -----------------------------------------------------------------------------

function validateRaci(raci) {
    const allowed = new Set(["R", "A", "C", "I"]);
    const errors = [];

    for (const [activity, assignments] of Object.entries(raci)) {
        const accountable = [];

        for (const [stakeholder, role] of Object.entries(assignments)) {
            if (!allowed.has(role)) {
                errors.push(
                    `${activity}: invalid role ${role} for ${stakeholder}`
                );
            }

            if (role === "A") {
                accountable.push(stakeholder);
            }
        }

        if (accountable.length === 0) {
            errors.push(`${activity}: no accountable stakeholder.`);
        }

        if (accountable.length > 1) {
            errors.push(
                `${activity}: multiple accountable stakeholders: ` +
                accountable.join(", ")
            );
        }
    }

    return errors;
}

const raci = {
    Requirements: {
        "Project Manager": "A",
        "Frontline Employees": "C",
        "Citizens": "C",
        "IT Operations": "C",
        "Cybersecurity Team": "C",
        "Executive Sponsor": "I"
    },
    "Security Review": {
        "Cybersecurity Team": "R",
        "IT Operations": "C",
        "Project Manager": "A",
        "Data Protection Authority": "C",
        "Executive Sponsor": "I"
    },
    "User Acceptance": {
        Citizens: "R",
        "Frontline Employees": "R",
        "Project Manager": "A",
        "IT Operations": "C",
        "Executive Sponsor": "I"
    }
};


// -----------------------------------------------------------------------------
// 10. PROCESS-BASED DISCOVERY
// -----------------------------------------------------------------------------

function discoverFromProcess(steps) {
    const discovered = new Set();

    for (const step of steps) {
        for (const key of [
            "owner",
            "actor",
            "customer",
            "approver",
            "supplier",
            "systemOwner"
        ]) {
            if (typeof step[key] === "string" && step[key].trim()) {
                discovered.add(step[key].trim());
            }
        }

        if (Array.isArray(step.reviewers)) {
            step.reviewers.forEach(reviewer => {
                if (typeof reviewer === "string" && reviewer.trim()) {
                    discovered.add(reviewer.trim());
                }
            });
        }
    }

    return [...discovered].sort();
}


// -----------------------------------------------------------------------------
// 11. SCENARIO SIMULATION
// -----------------------------------------------------------------------------

function simulateScopeChange(
    register,
    changedIds,
    powerDelta,
    interestDelta
) {
    return register.values().map(stakeholder => {
        const changed = changedIds.has(stakeholder.id);

        const power = Math.max(
            0,
            Math.min(
                10,
                stakeholder.power + (changed ? powerDelta : 0)
            )
        );

        const interest = Math.max(
            0,
            Math.min(
                10,
                stakeholder.interest + (changed ? interestDelta : 0)
            )
        );

        let newCategory;

        if (power >= 5 && interest >= 5) {
            newCategory = "Manage closely";
        } else if (power >= 5) {
            newCategory = "Keep satisfied";
        } else if (interest >= 5) {
            newCategory = "Keep informed";
        } else {
            newCategory = "Monitor";
        }

        return {
            name: stakeholder.name,
            oldCategory: stakeholder.powerInterestCategory(),
            newCategory
        };
    });
}


// -----------------------------------------------------------------------------
// 12. ASYNCHRONOUS DISCOVERY
// -----------------------------------------------------------------------------

function discoverExternalStakeholdersAsync(context) {
    /*
     * In a real application this could call an approved internal data source,
     * survey service, CRM, project database, or organizational directory.
     *
     * This demonstration deliberately uses a local asynchronous operation,
     * keeping the file dependency-free.
     */
    return new Promise(resolve => {
        setTimeout(() => {
            resolve(identifyCandidateStakeholders(context));
        }, 10);
    });
}


// -----------------------------------------------------------------------------
// 13. EVENT-DRIVEN REGISTER
// -----------------------------------------------------------------------------

class StakeholderEventBus {
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
        for (const listener of this.listeners.get(eventName) || []) {
            listener(payload);
        }
    }
}


// -----------------------------------------------------------------------------
// 14. PERFORMANCE DEMONSTRATION
// -----------------------------------------------------------------------------

function performanceTest(numberOfStakeholders = 10000) {
    const start = performance.now();

    const stakeholders = Array.from(
        { length: numberOfStakeholders },
        (_, index) => ({
            id: `P${index}`,
            power: index % 11,
            interest: (index * 3) % 11
        })
    );

    const highPriority = stakeholders.filter(
        stakeholder =>
            stakeholder.power >= 5 &&
            stakeholder.interest >= 5
    );

    const elapsed = performance.now() - start;

    return {
        total: stakeholders.length,
        highPriority: highPriority.length,
        milliseconds: Number(elapsed.toFixed(3))
    };
}


// -----------------------------------------------------------------------------
// 15. JSON SERIALIZATION
// -----------------------------------------------------------------------------

function serializeRegister(register) {
    return JSON.stringify(
        {
            stakeholders: register.values(),
            relationships: register.relationships
        },
        null,
        2
    );
}


// -----------------------------------------------------------------------------
// 16. MAIN PROGRAM
// -----------------------------------------------------------------------------

async function main() {
    console.log("\n" + "=".repeat(78));
    console.log("STAKEHOLDER IDENTIFICATION: JAVASCRIPT IMPLEMENTATION");
    console.log("=".repeat(78));

    console.log("\nIDENTIFICATION QUESTIONS");

    identificationQuestions.forEach(
        (question, index) => console.log(`${index + 1}. ${question}`)
    );

    console.log("\nCONTEXTUAL DISCOVERY");

    const context =
        "A cloud-based education payment platform for students.";

    identifyCandidateStakeholders(context).forEach(
        candidate => console.log(`- ${candidate}`)
    );

    const register = createSampleRegister();

    analyzeRegister(register);

    console.log("\nENGAGEMENT PLAN");

    createEngagementPlan(register).forEach(item => {
        console.log(
            `${item.stakeholder}: ` +
            `${item.current} -> ${item.desired}; ` +
            `gap=${item.gap}; ${item.action}`
        );
    });

    console.log("\nRACI VALIDATION");

    const raciErrors = validateRaci(raci);

    if (raciErrors.length === 0) {
        console.log("RACI matrix passed validation.");
    } else {
        raciErrors.forEach(error => console.log(`- ${error}`));
    }

    console.log("\nPROCESS-BASED DISCOVERY");

    const processSteps = [
        {
            name: "Submit application",
            actor: "Citizen",
            owner: "Frontline Employees",
            systemOwner: "IT Operations",
            reviewers: ["Accessibility Advocates"]
        },
        {
            name: "Validate identity",
            actor: "Identity Service",
            owner: "IT Operations",
            approver: "Cybersecurity Team",
            supplier: "Technology Supplier"
        },
        {
            name: "Review privacy controls",
            owner: "Cybersecurity Team",
            approver: "Data Protection Authority"
        }
    ];

    discoverFromProcess(processSteps).forEach(
        person => console.log(`- ${person}`)
    );

    console.log("\nSTAKEHOLDER NETWORK");

    const graph = new StakeholderGraph(register);

    console.log(
        "S07 -> S03:",
        graph.shortestPath("S07", "S03")
    );

    console.log(
        "S02 direct connections:",
        graph.directConnections("S02")
    );

    console.log("\nSCOPE-CHANGE SIMULATION");

    simulateScopeChange(
        register,
        new Set(["S05", "S08"]),
        2,
        0
    )
        .filter(item => item.oldCategory !== item.newCategory)
        .forEach(item => {
            console.log(
                `${item.name}: ${item.oldCategory} -> ${item.newCategory}`
            );
        });

    console.log("\nASYNC DISCOVERY");

    const asynchronousCandidates =
        await discoverExternalStakeholdersAsync(
            "A cloud application for education services."
        );

    console.log(
        `Discovered ${asynchronousCandidates.length} candidate stakeholder categories.`
    );

    console.log("\nEVENT-DRIVEN UPDATE");

    const eventBus = new StakeholderEventBus();

    eventBus.on("stakeholderAdded", stakeholder => {
        console.log(
            `Event received: stakeholder added -> ${stakeholder.name}`
        );
    });

    eventBus.emit(
        "stakeholderAdded",
        register.get("S05")
    );

    console.log("\nSERIALIZED REGISTER");

    const serialized = serializeRegister(register);
    console.log(serialized.slice(0, 1500) + "\n...");

    console.log("\nPERFORMANCE TEST");

    console.log(performanceTest());

    console.log("\nEDGE CASE VALIDATION");

    try {
        register.add(
            new Stakeholder({
                id: "S01",
                name: "Duplicate",
                type: "External",
                role: "Unknown",
                organization: "Unknown",
                power: 1,
                interest: 1,
                influence: 1,
                impact: 1
            })
        );
    } catch (error) {
        console.log(`Duplicate rejected: ${error.message}`);
    }

    try {
        new Stakeholder({
            id: "BAD",
            name: "Invalid",
            type: "Internal",
            role: "Unknown",
            organization: "Unknown",
            power: 15,
            interest: 1,
            influence: 1,
            impact: 1
        });
    } catch (error) {
        console.log(`Invalid score rejected: ${error.message}`);
    }

    console.log("\nJavaScript stakeholder analysis completed.");
}


if (require.main === module) {
    main().catch(error => {
        console.error("Program failed:", error.message);
        process.exitCode = 1;
    });
}
