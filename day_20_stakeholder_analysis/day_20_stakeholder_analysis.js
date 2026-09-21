/*
 * Stakeholder Analysis
 * =====================
 *
 * A self-contained JavaScript implementation demonstrating stakeholder
 * identification, scoring, mapping, engagement planning, dependency
 * analysis, conflict analysis, validation, and sensitivity analysis.
 *
 * The implementation is designed to run in Node.js without external
 * packages.
 *
 * JavaScript-specific aspects demonstrated:
 * - Classes
 * - Getters
 * - Maps and Sets
 * - Array methods
 * - Functional transformations
 * - Validation
 * - Error handling
 * - Sorting and filtering
 * - JSON serialization
 * - Modular function design
 * - Event-driven stakeholder updates
 */


// -----------------------------------------------------------------------------
// 1. ENUM-LIKE CONSTANTS
// -----------------------------------------------------------------------------

const EngagementLevel = Object.freeze({
    UNAWARE: "Unaware",
    RESISTANT: "Resistant",
    NEUTRAL: "Neutral",
    SUPPORTIVE: "Supportive",
    LEADING: "Leading"
});

const StakeholderCategory = Object.freeze({
    INTERNAL: "Internal",
    EXTERNAL: "External"
});

const StakeholderType = Object.freeze({
    PRIMARY: "Primary",
    SECONDARY: "Secondary"
});


// -----------------------------------------------------------------------------
// 2. VALIDATION UTILITIES
// -----------------------------------------------------------------------------

function validateRating(value, fieldName) {
    if (!Number.isFinite(value) || value < 1 || value > 10) {
        throw new RangeError(
            `${fieldName} must be a number from 1 to 10. Received: ${value}`
        );
    }
}

function validateNonEmptyString(value, fieldName) {
    if (typeof value !== "string" || value.trim().length === 0) {
        throw new TypeError(`${fieldName} must be a non-empty string.`);
    }
}

function approximatelyEqual(a, b, tolerance = 1e-9) {
    return Math.abs(a - b) <= tolerance;
}


// -----------------------------------------------------------------------------
// 3. STAKEHOLDER CLASS
// -----------------------------------------------------------------------------

class Stakeholder {
    constructor({
        name,
        role,
        category,
        type,
        interest,
        influence,
        impact,
        urgency,
        legitimacy,
        currentEngagement,
        desiredEngagement,
        interests = [],
        concerns = [],
        communicationPreference = "Email",
        dependencies = []
    }) {
        validateNonEmptyString(name, "name");
        validateNonEmptyString(role, "role");

        const ratings = {
            interest,
            influence,
            impact,
            urgency,
            legitimacy
        };

        Object.entries(ratings).forEach(([fieldName, value]) => {
            validateRating(value, fieldName);
        });

        this.name = name.trim();
        this.role = role.trim();
        this.category = category;
        this.type = type;

        this.interest = interest;
        this.influence = influence;
        this.impact = impact;
        this.urgency = urgency;
        this.legitimacy = legitimacy;

        this.currentEngagement = currentEngagement;
        this.desiredEngagement = desiredEngagement;

        this.interests = [...interests];
        this.concerns = [...concerns];
        this.communicationPreference = communicationPreference;
        this.dependencies = [...dependencies];
    }

    get powerInterestQuadrant() {
        const highPower = this.influence >= 6;
        const highInterest = this.interest >= 6;

        if (highPower && highInterest) {
            return "Manage closely";
        }

        if (highPower && !highInterest) {
            return "Keep satisfied";
        }

        if (!highPower && highInterest) {
            return "Keep informed";
        }

        return "Monitor";
    }

    get influenceImpactQuadrant() {
        const highInfluence = this.influence >= 6;
        const highImpact = this.impact >= 6;

        if (highInfluence && highImpact) {
            return "High influence / High impact";
        }

        if (highInfluence) {
            return "High influence / Low impact";
        }

        if (highImpact) {
            return "Low influence / High impact";
        }

        return "Low influence / Low impact";
    }

    get priorityScore() {
        /*
         * Transparent weighted model:
         * 30% influence
         * 25% interest
         * 20% impact
         * 15% urgency
         * 10% legitimacy
         */
        return (
            this.influence * 0.30 +
            this.interest * 0.25 +
            this.impact * 0.20 +
            this.urgency * 0.15 +
            this.legitimacy * 0.10
        );
    }

    get salienceScore() {
        /*
         * Simplified salience calculation based on power/influence,
         * legitimacy, and urgency.
         */
        return (
            this.influence *
            this.legitimacy *
            this.urgency
        ) / 10;
    }

    get engagementGap() {
        const order = new Map([
            [EngagementLevel.UNAWARE, 0],
            [EngagementLevel.RESISTANT, 1],
            [EngagementLevel.NEUTRAL, 2],
            [EngagementLevel.SUPPORTIVE, 3],
            [EngagementLevel.LEADING, 4]
        ]);

        return (
            order.get(this.desiredEngagement) -
            order.get(this.currentEngagement)
        );
    }

    recommendedStrategy() {
        switch (this.powerInterestQuadrant) {
            case "Manage closely":
                return this.currentEngagement === EngagementLevel.RESISTANT
                    ? "Address concerns directly, involve the stakeholder in decisions, and maintain frequent two-way communication."
                    : "Involve the stakeholder in important decisions and provide frequent updates.";

            case "Keep satisfied":
                return "Provide decision-relevant information, maintain confidence, and prevent unexpected escalation.";

            case "Keep informed":
                return "Provide transparent updates, explain stakeholder impacts, and maintain feedback channels.";

            default:
                return "Monitor changes in influence, interest, impact, or urgency and communicate when relevant.";
        }
    }

    toJSON() {
        return {
            name: this.name,
            role: this.role,
            category: this.category,
            type: this.type,
            interest: this.interest,
            influence: this.influence,
            impact: this.impact,
            urgency: this.urgency,
            legitimacy: this.legitimacy,
            currentEngagement: this.currentEngagement,
            desiredEngagement: this.desiredEngagement,
            powerInterestQuadrant: this.powerInterestQuadrant,
            influenceImpactQuadrant: this.influenceImpactQuadrant,
            priorityScore: Number(this.priorityScore.toFixed(2)),
            salienceScore: Number(this.salienceScore.toFixed(2)),
            engagementGap: this.engagementGap,
            interests: this.interests,
            concerns: this.concerns,
            communicationPreference: this.communicationPreference,
            dependencies: this.dependencies
        };
    }
}


// -----------------------------------------------------------------------------
// 4. STAKEHOLDER REGISTER
// -----------------------------------------------------------------------------

class StakeholderRegister {
    constructor() {
        this.stakeholders = new Map();
    }

    normalizeName(name) {
        return name.trim().toLowerCase();
    }

    add(stakeholder) {
        const key = this.normalizeName(stakeholder.name);

        if (this.stakeholders.has(key)) {
            throw new Error(
                `Stakeholder '${stakeholder.name}' already exists.`
            );
        }

        this.stakeholders.set(key, stakeholder);
    }

    update(stakeholder) {
        const key = this.normalizeName(stakeholder.name);

        if (!this.stakeholders.has(key)) {
            throw new Error(
                `Stakeholder '${stakeholder.name}' does not exist.`
            );
        }

        this.stakeholders.set(key, stakeholder);
    }

    get(name) {
        const key = this.normalizeName(name);
        const stakeholder = this.stakeholders.get(key);

        if (!stakeholder) {
            throw new Error(`Stakeholder '${name}' was not found.`);
        }

        return stakeholder;
    }

    remove(name) {
        const key = this.normalizeName(name);

        if (!this.stakeholders.delete(key)) {
            throw new Error(`Stakeholder '${name}' was not found.`);
        }
    }

    all() {
        return [...this.stakeholders.values()];
    }

    rankedByPriority() {
        return this.all().sort(
            (a, b) => b.priorityScore - a.priorityScore
        );
    }
}


// -----------------------------------------------------------------------------
// 5. COMMUNICATION PLANNING
// -----------------------------------------------------------------------------

function buildCommunicationPlan(stakeholder, owner = "Project Manager") {
    let frequency;
    let channel;
    let objective;

    switch (stakeholder.powerInterestQuadrant) {
        case "Manage closely":
            frequency = "Weekly or more frequently during critical decisions";
            channel = "Meeting + written decision record";
            objective = "Maintain alignment and enable rapid decision-making";
            break;

        case "Keep satisfied":
            frequency = "Biweekly or at major decision points";
            channel = "Executive update";
            objective = "Maintain confidence and prevent unexpected escalation";
            break;

        case "Keep informed":
            frequency = "Weekly or biweekly";
            channel = "Dashboard / newsletter / town hall";
            objective = "Maintain transparency and collect feedback";
            break;

        default:
            frequency = "Monthly or milestone-based";
            channel = "Targeted email";
            objective = "Maintain awareness without unnecessary communication";
    }

    return {
        stakeholder: stakeholder.name,
        owner,
        objective,
        channel,
        frequency,
        messageFocus:
            "Progress, stakeholder-relevant impacts, decisions, concerns, and required actions."
    };
}


// -----------------------------------------------------------------------------
// 6. POWER-INTEREST MATRIX
// -----------------------------------------------------------------------------

function createPowerInterestMatrix(register) {
    const matrix = new Map([
        ["Manage closely", []],
        ["Keep satisfied", []],
        ["Keep informed", []],
        ["Monitor", []]
    ]);

    register.all().forEach(stakeholder => {
        matrix.get(stakeholder.powerInterestQuadrant).push(
            stakeholder.name
        );
    });

    return matrix;
}

function printPowerInterestMatrix(register) {
    console.log("\nPOWER-INTEREST MATRIX");
    console.log("=".repeat(75));

    const matrix = createPowerInterestMatrix(register);

    for (const [quadrant, names] of matrix.entries()) {
        console.log(
            `${quadrant.padEnd(20)} | ${names.join(", ") || "None"}`
        );
    }
}


// -----------------------------------------------------------------------------
// 7. DEPENDENCY ANALYSIS
// -----------------------------------------------------------------------------

function buildDependencyGraph(register) {
    return Object.fromEntries(
        register.all().map(stakeholder => [
            stakeholder.name,
            [...stakeholder.dependencies]
        ])
    );
}

function findDependencyBottlenecks(register) {
    const counts = new Map();

    register.all().forEach(stakeholder => {
        stakeholder.dependencies.forEach(dependency => {
            counts.set(
                dependency,
                (counts.get(dependency) || 0) + 1
            );
        });
    });

    return [...counts.entries()]
        .sort((a, b) => b[1] - a[1])
        .map(([name, count]) => ({ name, count }));
}


// -----------------------------------------------------------------------------
// 8. CONFLICT ANALYSIS
// -----------------------------------------------------------------------------

class StakeholderConflict {
    constructor({
        stakeholderA,
        stakeholderB,
        topic,
        severity,
        description
    }) {
        validateRating(severity, "severity");

        this.stakeholderA = stakeholderA;
        this.stakeholderB = stakeholderB;
        this.topic = topic;
        this.severity = severity;
        this.description = description;
    }
}

function calculateConflictPriority(
    conflict,
    stakeholderA,
    stakeholderB
) {
    const averageInfluence =
        (stakeholderA.influence + stakeholderB.influence) / 2;

    return conflict.severity * averageInfluence / 10;
}


// -----------------------------------------------------------------------------
// 9. WEIGHTED SCORING AND SENSITIVITY ANALYSIS
// -----------------------------------------------------------------------------

function calculateWeightedScore(stakeholder, weights) {
    const requiredFields = [
        "interest",
        "influence",
        "impact",
        "urgency",
        "legitimacy"
    ];

    const keys = Object.keys(weights).sort();
    const expected = [...requiredFields].sort();

    if (JSON.stringify(keys) !== JSON.stringify(expected)) {
        throw new Error(
            `Weights must contain exactly: ${requiredFields.join(", ")}`
        );
    }

    const totalWeight = Object.values(weights)
        .reduce((sum, value) => sum + value, 0);

    if (!approximatelyEqual(totalWeight, 1)) {
        throw new Error("Weights must sum to 1.0.");
    }

    return requiredFields.reduce(
        (total, fieldName) =>
            total + stakeholder[fieldName] * weights[fieldName],
        0
    );
}

function sensitivityAnalysis(stakeholder, scenarios) {
    return Object.entries(scenarios).map(
        ([scenarioName, weights]) => ({
            scenario: scenarioName,
            score: calculateWeightedScore(stakeholder, weights)
        })
    );
}


// -----------------------------------------------------------------------------
// 10. STAKEHOLDER EVENT STREAM
// -----------------------------------------------------------------------------

class StakeholderEventBus {
    /*
     * JavaScript is well suited to event-driven systems.
     *
     * A stakeholder-analysis application could emit events whenever:
     * - a stakeholder is added
     * - influence changes
     * - engagement changes
     * - a concern is recorded
     *
     * Other components can subscribe without tightly coupling themselves
     * to the component producing the event.
     */
    constructor() {
        this.listeners = new Map();
    }

    on(eventName, callback) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }

        this.listeners.get(eventName).push(callback);
    }

    emit(eventName, payload) {
        const callbacks = this.listeners.get(eventName) || [];

        callbacks.forEach(callback => callback(payload));
    }
}


// -----------------------------------------------------------------------------
// 11. SAMPLE DATA
// -----------------------------------------------------------------------------

function createSampleRegister() {
    const register = new StakeholderRegister();

    const stakeholders = [
        new Stakeholder({
            name: "Executive Sponsor",
            role: "Program sponsor",
            category: StakeholderCategory.INTERNAL,
            type: StakeholderType.PRIMARY,
            interest: 9,
            influence: 10,
            impact: 8,
            urgency: 8,
            legitimacy: 10,
            currentEngagement: EngagementLevel.SUPPORTIVE,
            desiredEngagement: EngagementLevel.LEADING,
            interests: ["Strategic outcomes", "Budget", "Benefits"],
            concerns: ["Schedule", "Return on investment"],
            communicationPreference: "Executive meeting"
        }),

        new Stakeholder({
            name: "Project Manager",
            role: "Delivery lead",
            category: StakeholderCategory.INTERNAL,
            type: StakeholderType.PRIMARY,
            interest: 10,
            influence: 9,
            impact: 10,
            urgency: 9,
            legitimacy: 10,
            currentEngagement: EngagementLevel.LEADING,
            desiredEngagement: EngagementLevel.LEADING,
            interests: ["Scope", "Schedule", "Quality"],
            concerns: ["Dependencies", "Resources"],
            communicationPreference: "Project dashboard",
            dependencies: ["Executive Sponsor", "IT Operations"]
        }),

        new Stakeholder({
            name: "Finance Department",
            role: "Financial control",
            category: StakeholderCategory.INTERNAL,
            type: StakeholderType.PRIMARY,
            interest: 7,
            influence: 8,
            impact: 6,
            urgency: 6,
            legitimacy: 9,
            currentEngagement: EngagementLevel.NEUTRAL,
            desiredEngagement: EngagementLevel.SUPPORTIVE,
            interests: ["Cost control", "Forecast accuracy"],
            concerns: ["Budget overrun"],
            communicationPreference: "Financial review",
            dependencies: ["Project Manager"]
        }),

        new Stakeholder({
            name: "IT Operations",
            role: "Platform operations",
            category: StakeholderCategory.INTERNAL,
            type: StakeholderType.PRIMARY,
            interest: 9,
            influence: 8,
            impact: 9,
            urgency: 8,
            legitimacy: 10,
            currentEngagement: EngagementLevel.SUPPORTIVE,
            desiredEngagement: EngagementLevel.LEADING,
            interests: ["Reliability", "Security", "Maintainability"],
            concerns: ["Operational load", "Integration"],
            communicationPreference: "Technical workshop",
            dependencies: ["Project Manager", "External Vendor"]
        }),

        new Stakeholder({
            name: "Employees",
            role: "Internal users",
            category: StakeholderCategory.INTERNAL,
            type: StakeholderType.PRIMARY,
            interest: 8,
            influence: 5,
            impact: 9,
            urgency: 6,
            legitimacy: 10,
            currentEngagement: EngagementLevel.NEUTRAL,
            desiredEngagement: EngagementLevel.SUPPORTIVE,
            interests: ["Usability", "Training"],
            concerns: ["Learning curve", "Workflow changes"],
            communicationPreference: "Town hall",
            dependencies: ["Project Manager", "IT Operations"]
        }),

        new Stakeholder({
            name: "Customers",
            role: "External service users",
            category: StakeholderCategory.EXTERNAL,
            type: StakeholderType.PRIMARY,
            interest: 8,
            influence: 6,
            impact: 9,
            urgency: 7,
            legitimacy: 10,
            currentEngagement: EngagementLevel.NEUTRAL,
            desiredEngagement: EngagementLevel.SUPPORTIVE,
            interests: ["Service quality", "Availability"],
            concerns: ["Privacy", "Usability"],
            communicationPreference: "Survey / support channel",
            dependencies: ["IT Operations"]
        }),

        new Stakeholder({
            name: "Regulator",
            role: "Regulatory oversight",
            category: StakeholderCategory.EXTERNAL,
            type: StakeholderType.SECONDARY,
            interest: 6,
            influence: 9,
            impact: 5,
            urgency: 8,
            legitimacy: 10,
            currentEngagement: EngagementLevel.NEUTRAL,
            desiredEngagement: EngagementLevel.SUPPORTIVE,
            interests: ["Compliance", "Consumer protection"],
            concerns: ["Non-compliance", "Reporting"],
            communicationPreference: "Formal submission",
            dependencies: ["Legal Department"]
        }),

        new Stakeholder({
            name: "External Vendor",
            role: "Technology supplier",
            category: StakeholderCategory.EXTERNAL,
            type: StakeholderType.PRIMARY,
            interest: 8,
            influence: 7,
            impact: 8,
            urgency: 7,
            legitimacy: 8,
            currentEngagement: EngagementLevel.SUPPORTIVE,
            desiredEngagement: EngagementLevel.SUPPORTIVE,
            interests: ["Contract delivery", "Service continuity"],
            concerns: ["Scope changes", "Payment"],
            communicationPreference: "Vendor meeting",
            dependencies: ["Project Manager"]
        }),

        new Stakeholder({
            name: "Legal Department",
            role: "Legal review",
            category: StakeholderCategory.INTERNAL,
            type: StakeholderType.SECONDARY,
            interest: 5,
            influence: 7,
            impact: 5,
            urgency: 7,
            legitimacy: 10,
            currentEngagement: EngagementLevel.NEUTRAL,
            desiredEngagement: EngagementLevel.SUPPORTIVE,
            interests: ["Contract validity", "Privacy"],
            concerns: ["Liability", "Regulatory exposure"],
            communicationPreference: "Legal review",
            dependencies: ["Project Manager"]
        })
    ];

    stakeholders.forEach(stakeholder => register.add(stakeholder));

    return register;
}


// -----------------------------------------------------------------------------
// 12. REPORTING
// -----------------------------------------------------------------------------

function printStakeholderReport(stakeholder) {
    console.log("\n" + "=".repeat(75));
    console.log(`STAKEHOLDER: ${stakeholder.name}`);
    console.log("=".repeat(75));

    console.log(`Role:                ${stakeholder.role}`);
    console.log(`Category:            ${stakeholder.category}`);
    console.log(`Type:                ${stakeholder.type}`);
    console.log(`Interest:            ${stakeholder.interest}/10`);
    console.log(`Influence:           ${stakeholder.influence}/10`);
    console.log(`Impact:              ${stakeholder.impact}/10`);
    console.log(`Urgency:             ${stakeholder.urgency}/10`);
    console.log(`Legitimacy:          ${stakeholder.legitimacy}/10`);
    console.log(
        `Priority score:      ${stakeholder.priorityScore.toFixed(2)}/10`
    );
    console.log(
        `Salience score:      ${stakeholder.salienceScore.toFixed(2)}`
    );
    console.log(
        `Power-interest:      ${stakeholder.powerInterestQuadrant}`
    );
    console.log(
        `Influence-impact:    ${stakeholder.influenceImpactQuadrant}`
    );
    console.log(
        `Current engagement:  ${stakeholder.currentEngagement}`
    );
    console.log(
        `Desired engagement:  ${stakeholder.desiredEngagement}`
    );
    console.log(`Engagement gap:      ${stakeholder.engagementGap}`);
    console.log(
        `Strategy:            ${stakeholder.recommendedStrategy()}`
    );
}


// -----------------------------------------------------------------------------
// 13. MAIN DEMONSTRATION
// -----------------------------------------------------------------------------

function main() {
    console.log("=".repeat(75));
    console.log("STAKEHOLDER ANALYSIS");
    console.log("=".repeat(75));

    const register = createSampleRegister();

    printStakeholderReport(
        register.get("Executive Sponsor")
    );

    printPowerInterestMatrix(register);

    console.log("\nPRIORITY RANKING");
    console.log("=".repeat(75));

    register.rankedByPriority().forEach((stakeholder, index) => {
        console.log(
            `${String(index + 1).padEnd(4)}` +
            `${stakeholder.name.padEnd(25)}` +
            `Influence=${stakeholder.influence.toFixed(1)}  ` +
            `Interest=${stakeholder.interest.toFixed(1)}  ` +
            `Priority=${stakeholder.priorityScore.toFixed(2)}`
        );
    });

    console.log("\nCOMMUNICATION PLANS");
    console.log("=".repeat(75));

    register.rankedByPriority().slice(0, 5).forEach(stakeholder => {
        const plan = buildCommunicationPlan(stakeholder);

        console.log(`\n${plan.stakeholder}`);
        console.log(`  Objective: ${plan.objective}`);
        console.log(`  Channel:   ${plan.channel}`);
        console.log(`  Frequency: ${plan.frequency}`);
        console.log(`  Owner:     ${plan.owner}`);
    });

    console.log("\nDEPENDENCY GRAPH");
    console.log("=".repeat(75));

    const graph = buildDependencyGraph(register);

    Object.entries(graph).forEach(([name, dependencies]) => {
        if (dependencies.length > 0) {
            console.log(
                `${name} -> ${dependencies.join(", ")}`
            );
        }
    });

    console.log("\nDEPENDENCY BOTTLENECKS");
    console.log("=".repeat(75));

    findDependencyBottlenecks(register).forEach(
        ({ name, count }) => {
            console.log(`${name}: ${count} dependency reference(s)`);
        }
    );

    console.log("\nCONFLICT ANALYSIS");
    console.log("=".repeat(75));

    const conflict = new StakeholderConflict({
        stakeholderA: "Finance Department",
        stakeholderB: "IT Operations",
        topic: "Cost control versus technical reliability",
        severity: 6,
        description:
            "Budget discipline and operational resilience may create competing priorities."
    });

    const conflictScore = calculateConflictPriority(
        conflict,
        register.get(conflict.stakeholderA),
        register.get(conflict.stakeholderB)
    );

    console.log(`Participants: ${conflict.stakeholderA} / ${conflict.stakeholderB}`);
    console.log(`Severity:     ${conflict.severity}/10`);
    console.log(`Priority:     ${conflictScore.toFixed(2)}`);

    console.log("\nSENSITIVITY ANALYSIS");
    console.log("=".repeat(75));

    const scenarios = {
        Balanced: {
            interest: 0.25,
            influence: 0.30,
            impact: 0.20,
            urgency: 0.15,
            legitimacy: 0.10
        },
        RiskFocused: {
            interest: 0.15,
            influence: 0.30,
            impact: 0.25,
            urgency: 0.20,
            legitimacy: 0.10
        },
        ImpactFocused: {
            interest: 0.20,
            influence: 0.20,
            impact: 0.35,
            urgency: 0.15,
            legitimacy: 0.10
        }
    };

    const sponsor = register.get("Executive Sponsor");

    sensitivityAnalysis(sponsor, scenarios).forEach(
        result => {
            console.log(
                `${result.scenario.padEnd(18)}: ${result.score.toFixed(2)}/10`
            );
        }
    );

    console.log("\nEVENT-DRIVEN UPDATE");
    console.log("=".repeat(75));

    const eventBus = new StakeholderEventBus();

    eventBus.on("engagementChanged", event => {
        console.log(
            `Engagement event: ${event.name} changed from ` +
            `${event.previous} to ${event.current}.`
        );
    });

    const employee = register.get("Employees");
    const previousEngagement = employee.currentEngagement;

    employee.currentEngagement = EngagementLevel.SUPPORTIVE;

    eventBus.emit("engagementChanged", {
        name: employee.name,
        previous: previousEngagement,
        current: employee.currentEngagement
    });

    console.log("\nJSON EXPORT");
    console.log("=".repeat(75));

    const exportData = register
        .rankedByPriority()
        .map(stakeholder => stakeholder.toJSON());

    console.log(
        JSON.stringify(exportData.slice(0, 2), null, 2)
    );

    console.log("\nEDGE CASE VALIDATION");
    console.log("=".repeat(75));

    try {
        new Stakeholder({
            name: "Invalid Stakeholder",
            role: "Test",
            category: StakeholderCategory.INTERNAL,
            type: StakeholderType.PRIMARY,
            interest: 15,
            influence: 5,
            impact: 5,
            urgency: 5,
            legitimacy: 5,
            currentEngagement: EngagementLevel.NEUTRAL,
            desiredEngagement: EngagementLevel.SUPPORTIVE
        });
    } catch (error) {
        console.log(`Invalid rating rejected: ${error.message}`);
    }

    try {
        register.add(register.get("Customers"));
    } catch (error) {
        console.log(`Duplicate rejected: ${error.message}`);
    }

    console.log("\nJavaScript stakeholder analysis completed.");
}


main();
