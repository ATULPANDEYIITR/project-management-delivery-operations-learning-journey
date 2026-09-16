/*
 * Project Sponsor and the Role of the Project Sponsor
 *
 * Self-contained JavaScript study program demonstrating project sponsorship,
 * governance, decision rights, stakeholder management, risk oversight,
 * benefits realization, escalation, change control, and executive reporting.
 *
 * Compatible with modern Node.js.
 */

"use strict";

console.log("=".repeat(78));
console.log("PROJECT SPONSOR: GOVERNANCE AND EXECUTIVE OVERSIGHT");
console.log("=".repeat(78));


// ---------------------------------------------------------------------------
// 1. FUNDAMENTAL CONCEPTS
// ---------------------------------------------------------------------------

const fundamentalConcepts = {
    project:
        "A temporary undertaking created to deliver a defined product, service, capability, or result.",

    projectSponsor:
        "A senior organizational representative who provides strategic ownership, authority, resources, governance, and executive support.",

    projectManager:
        "The person responsible for day-to-day project management within delegated authority.",

    stakeholder:
        "An individual, group, or organization that can affect, be affected by, or perceive itself affected by the project.",

    governance:
        "The framework defining accountability, decision rights, escalation, oversight, and control.",

    businessCase:
        "The structured justification for investment, including value, cost, risks, alternatives, and strategic alignment.",

    benefit:
        "A measurable improvement or advantage expected from the use of project outputs.",
};

for (const [term, definition] of Object.entries(fundamentalConcepts)) {
    console.log(`\n${term}`);
    console.log(`  ${definition}`);
}


// ---------------------------------------------------------------------------
// 2. ENUM-LIKE CONSTANTS
// ---------------------------------------------------------------------------

const ProjectStatus = Object.freeze({
    INITIATING: "Initiating",
    PLANNING: "Planning",
    EXECUTING: "Executing",
    AT_RISK: "At Risk",
    ON_HOLD: "On Hold",
    COMPLETED: "Completed",
    CANCELLED: "Cancelled",
});

const DecisionType = Object.freeze({
    ROUTINE: "Routine",
    MAJOR: "Major",
    STRATEGIC: "Strategic",
    EMERGENCY: "Emergency",
});

const RiskLevel = Object.freeze({
    LOW: "Low",
    MEDIUM: "Medium",
    HIGH: "High",
    CRITICAL: "Critical",
});


// ---------------------------------------------------------------------------
// 3. VALIDATION HELPERS
// ---------------------------------------------------------------------------

function assertNonNegativeNumber(value, fieldName) {
    if (!Number.isFinite(value) || value < 0) {
        throw new RangeError(`${fieldName} must be a non-negative number.`);
    }
}

function assertProbability(value) {
    if (!Number.isFinite(value) || value < 0 || value > 1) {
        throw new RangeError("Probability must be between 0 and 1.");
    }
}


// ---------------------------------------------------------------------------
// 4. STAKEHOLDER
// ---------------------------------------------------------------------------

class Stakeholder {
    constructor(name, role, influence, interest, engagementLevel = 50) {
        if (!name || !role) {
            throw new Error("Stakeholder name and role are required.");
        }

        if (engagementLevel < 0 || engagementLevel > 100) {
            throw new RangeError("Engagement must be between 0 and 100.");
        }

        this.name = name;
        this.role = role;
        this.influence = influence;
        this.interest = interest;
        this.engagementLevel = engagementLevel;
    }

    engagementCategory() {
        if (this.engagementLevel >= 80) return "Highly engaged";
        if (this.engagementLevel >= 60) return "Engaged";
        if (this.engagementLevel >= 40) return "Neutral";
        return "Needs attention";
    }
}


// ---------------------------------------------------------------------------
// 5. RISK
// ---------------------------------------------------------------------------

class Risk {
    constructor(
        riskId,
        description,
        probability,
        impact,
        owner,
        mitigation,
    ) {
        assertProbability(probability);
        assertNonNegativeNumber(impact, "Impact");

        this.riskId = riskId;
        this.description = description;
        this.probability = probability;
        this.impact = impact;
        this.owner = owner;
        this.mitigation = mitigation;
        this.status = "Open";
    }

    get exposure() {
        return this.probability * this.impact;
    }

    get level() {
        if (this.exposure >= 20) return RiskLevel.CRITICAL;
        if (this.exposure >= 12) return RiskLevel.HIGH;
        if (this.exposure >= 6) return RiskLevel.MEDIUM;
        return RiskLevel.LOW;
    }
}


// ---------------------------------------------------------------------------
// 6. BENEFIT
// ---------------------------------------------------------------------------

class Benefit {
    constructor(
        benefitId,
        description,
        baseline,
        target,
        current,
        unit,
        owner,
    ) {
        this.benefitId = benefitId;
        this.description = description;
        this.baseline = baseline;
        this.target = target;
        this.current = current;
        this.unit = unit;
        this.owner = owner;
    }

    get progressPercentage() {
        const denominator = this.target - this.baseline;

        if (denominator === 0) {
            return this.current >= this.target ? 100 : 0;
        }

        const progress =
            ((this.current - this.baseline) / denominator) * 100;

        return Math.max(0, Math.min(100, progress));
    }
}


// ---------------------------------------------------------------------------
// 7. DECISION
// ---------------------------------------------------------------------------

class Decision {
    constructor(
        decisionId,
        description,
        type,
        requiredBy,
        owner,
    ) {
        this.decisionId = decisionId;
        this.description = description;
        this.type = type;
        this.requiredBy = new Date(requiredBy);
        this.owner = owner;
        this.decided = false;
        this.outcome = null;
    }

    make(outcome) {
        if (!outcome || !outcome.trim()) {
            throw new Error("Decision outcome cannot be empty.");
        }

        this.decided = true;
        this.outcome = outcome;
    }

    isOverdue(referenceDate = new Date()) {
        return !this.decided && this.requiredBy < referenceDate;
    }
}


// ---------------------------------------------------------------------------
// 8. PROJECT
// ---------------------------------------------------------------------------

class Project {
    constructor({
        projectId,
        name,
        strategicObjective,
        sponsorName,
        projectManagerName,
        approvedBudget,
        currentForecast,
        scopeBaseline,
    }) {
        assertNonNegativeNumber(approvedBudget, "Approved budget");
        assertNonNegativeNumber(currentForecast, "Current forecast");

        this.projectId = projectId;
        this.name = name;
        this.strategicObjective = strategicObjective;
        this.sponsorName = sponsorName;
        this.projectManagerName = projectManagerName;
        this.approvedBudget = approvedBudget;
        this.currentForecast = currentForecast;
        this.scopeBaseline = scopeBaseline;
        this.status = ProjectStatus.INITIATING;

        this.stakeholders = [];
        this.risks = [];
        this.benefits = [];
        this.decisions = [];
    }

    get budgetVariance() {
        return this.approvedBudget - this.currentForecast;
    }

    get budgetVariancePercentage() {
        if (this.approvedBudget === 0) return 0;

        return (this.budgetVariance / this.approvedBudget) * 100;
    }

    get criticalRisks() {
        return this.risks.filter(
            (risk) => risk.level === RiskLevel.CRITICAL,
        );
    }

    get overdueDecisions() {
        return this.decisions.filter((decision) => decision.isOverdue());
    }

    get averageBenefitProgress() {
        if (this.benefits.length === 0) return 0;

        const total = this.benefits.reduce(
            (sum, benefit) => sum + benefit.progressPercentage,
            0,
        );

        return total / this.benefits.length;
    }
}


// ---------------------------------------------------------------------------
// 9. PROJECT SPONSOR
// ---------------------------------------------------------------------------

class ProjectSponsor {
    constructor({
        name,
        title,
        authorityLimit,
        strategicPriorities,
    }) {
        assertNonNegativeNumber(authorityLimit, "Authority limit");

        this.name = name;
        this.title = title;
        this.authorityLimit = authorityLimit;
        this.strategicPriorities = strategicPriorities;
        this.activeProjects = [];
    }

    sponsorProject(project) {
        if (project.sponsorName !== this.name) {
            throw new Error(
                `${this.name} is not the recorded sponsor of ${project.name}.`,
            );
        }

        if (!this.activeProjects.includes(project)) {
            this.activeProjects.push(project);
        }

        project.status = ProjectStatus.INITIATING;

        console.log(
            `\n${this.name} is sponsoring '${project.name}'.`,
        );
    }

    confirmAlignment(project) {
        const objective = project.strategicObjective.toLowerCase();

        const aligned = this.strategicPriorities.some(
            (priority) => objective.includes(priority.toLowerCase()),
        );

        console.log(
            `Strategic alignment: ${aligned ? "Aligned" : "Requires review"}`,
        );

        return aligned;
    }

    approveFunding(project, amount) {
        assertNonNegativeNumber(amount, "Funding amount");

        if (amount > this.authorityLimit) {
            console.log(
                `Funding request ${amount.toLocaleString()} exceeds ` +
                `sponsor authority of ${this.authorityLimit.toLocaleString()}.`,
            );

            return false;
        }

        project.approvedBudget = amount;
        project.currentForecast = amount;

        console.log(
            `Funding approved: ${amount.toLocaleString()}`,
        );

        return true;
    }

    makeDecision(project, decisionId, outcome) {
        const decision = project.decisions.find(
            (item) => item.decisionId === decisionId,
        );

        if (!decision) {
            console.log(`Decision ${decisionId} was not found.`);
            return false;
        }

        decision.make(outcome);

        console.log(
            `Sponsor decision ${decisionId}: ${outcome}`,
        );

        return true;
    }

    removeBarrier(project, barrier) {
        console.log(
            `Executive action for '${project.name}': ${barrier}`,
        );
    }

    approveMajorChange(project, changeCost, strategicAlignment) {
        assertNonNegativeNumber(changeCost, "Change cost");

        if (!strategicAlignment) {
            console.log(
                "Change rejected because strategic alignment is insufficient.",
            );
            return false;
        }

        if (changeCost > this.authorityLimit) {
            console.log(
                "Change requires escalation because it exceeds sponsor authority.",
            );
            return false;
        }

        project.currentForecast += changeCost;

        console.log(
            `Change approved. Forecast increased by ${changeCost.toLocaleString()}.`,
        );

        return true;
    }

    reviewRisks(project) {
        const critical = project.criticalRisks;

        console.log(
            `Critical risks requiring executive attention: ${critical.length}`,
        );

        return critical;
    }

    reviewBenefits(project) {
        const progress = project.averageBenefitProgress;

        console.log(
            `Average benefit realization: ${progress.toFixed(1)}%`,
        );

        return progress;
    }

    authorizeClosure(project) {
        const closable =
            project.status === ProjectStatus.COMPLETED ||
            project.status === ProjectStatus.CANCELLED;

        if (!closable) {
            console.log(
                "Closure cannot be authorized while the project is active.",
            );
            return false;
        }

        console.log(`Closure authorized for '${project.name}'.`);
        return true;
    }
}


// ---------------------------------------------------------------------------
// 10. CREATE PROJECT AND SPONSOR
// ---------------------------------------------------------------------------

const project = new Project({
    projectId: "PRJ-001",
    name: "Enterprise Customer Service Modernization",
    strategicObjective:
        "Digital transformation and customer service improvement",
    sponsorName: "Anita Sharma",
    projectManagerName: "Rahul Mehta",
    approvedBudget: 5_000_000,
    currentForecast: 4_850_000,
    scopeBaseline:
        "Implement a unified service platform, migrate approved data, " +
        "integrate selected channels, train service teams, and measure " +
        "service improvements.",
});

const sponsor = new ProjectSponsor({
    name: "Anita Sharma",
    title: "Chief Customer Officer",
    authorityLimit: 750_000,
    strategicPriorities: [
        "Digital transformation",
        "Customer service improvement",
        "Operational efficiency",
    ],
});


// ---------------------------------------------------------------------------
// 11. STAKEHOLDERS
// ---------------------------------------------------------------------------

project.stakeholders.push(
    new Stakeholder(
        "Chief Executive Officer",
        "Executive stakeholder",
        "High",
        "High",
        80,
    ),
    new Stakeholder(
        "Chief Information Officer",
        "Technology executive",
        "High",
        "High",
        75,
    ),
    new Stakeholder(
        "Customer Service Director",
        "Business owner",
        "High",
        "High",
        90,
    ),
    new Stakeholder(
        "Service Agents",
        "End users",
        "Medium",
        "High",
        55,
    ),
    new Stakeholder(
        "Finance Controller",
        "Control function",
        "Medium",
        "Medium",
        65,
    ),
);


// ---------------------------------------------------------------------------
// 12. RISKS
// ---------------------------------------------------------------------------

project.risks.push(
    new Risk(
        "R-001",
        "Legacy data contains inconsistent records.",
        0.7,
        8,
        "Data Migration Lead",
        "Profile, cleanse, reconcile, and validate migration data.",
    ),
    new Risk(
        "R-002",
        "Business users resist the new operating model.",
        0.6,
        9,
        "Change Lead",
        "Use training, communication, demonstrations, and user involvement.",
    ),
    new Risk(
        "R-003",
        "Critical integration misses the release window.",
        0.4,
        10,
        "Technical Lead",
        "Start interface testing early and maintain contingency capacity.",
    ),
    new Risk(
        "R-004",
        "Uncontrolled scope growth increases total cost.",
        0.5,
        7,
        "Project Manager",
        "Use formal change control and sponsor-level governance.",
    ),
);


// ---------------------------------------------------------------------------
// 13. BENEFITS
// ---------------------------------------------------------------------------

project.benefits.push(
    new Benefit(
        "B-001",
        "Reduce average customer response time.",
        24,
        12,
        17,
        "hours",
        "Customer Service Director",
    ),
    new Benefit(
        "B-002",
        "Increase first-contact resolution.",
        62,
        80,
        72,
        "%",
        "Customer Service Director",
    ),
    new Benefit(
        "B-003",
        "Reduce manual service effort.",
        100,
        70,
        82,
        "index",
        "Operations Director",
    ),
);


// ---------------------------------------------------------------------------
// 14. DECISIONS
// ---------------------------------------------------------------------------

const today = new Date();
const yesterday = new Date(today);
yesterday.setDate(yesterday.getDate() - 2);

const futureDate = new Date(today);
futureDate.setDate(futureDate.getDate() + 3);

project.decisions.push(
    new Decision(
        "D-001",
        "Approve integration architecture exception.",
        DecisionType.MAJOR,
        yesterday,
        sponsor.name,
    ),
    new Decision(
        "D-002",
        "Select phased versus single-release deployment.",
        DecisionType.STRATEGIC,
        futureDate,
        sponsor.name,
    ),
);


// ---------------------------------------------------------------------------
// 15. EXECUTIVE GOVERNANCE FLOW
// ---------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("EXECUTIVE GOVERNANCE FLOW");
console.log("=".repeat(78));

sponsor.sponsorProject(project);
sponsor.confirmAlignment(project);

project.status = ProjectStatus.PLANNING;

console.log(`Project status: ${project.status}`);
console.log(`Sponsor: ${project.sponsorName}`);
console.log(`Project manager: ${project.projectManagerName}`);
console.log(`Approved budget: ${project.approvedBudget.toLocaleString()}`);


// ---------------------------------------------------------------------------
// 16. RISK REVIEW
// ---------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("RISK REVIEW");
console.log("=".repeat(78));

for (const risk of project.risks) {
    console.log(
        `${risk.riskId} | exposure=${risk.exposure.toFixed(2)} | ` +
        `level=${risk.level} | ${risk.description}`,
    );
}

sponsor.reviewRisks(project);


// ---------------------------------------------------------------------------
// 17. DECISION REVIEW
// ---------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("DECISION REVIEW");
console.log("=".repeat(78));

for (const decision of project.decisions) {
    console.log(
        `${decision.decisionId} | ${decision.type} | ` +
        `${decision.decided ? "Decided" : "Pending"}`,
    );

    if (decision.isOverdue()) {
        sponsor.makeDecision(
            project,
            decision.decisionId,
            "Approved with controlled implementation.",
        );
    }
}


// ---------------------------------------------------------------------------
// 18. STAKEHOLDER MANAGEMENT
// ---------------------------------------------------------------------------

function engagementAction(stakeholder) {
    if (
        stakeholder.influence === "High" &&
        stakeholder.interest === "High"
    ) {
        return "Manage closely";
    }

    if (
        stakeholder.influence === "High" &&
        stakeholder.interest === "Low"
    ) {
        return "Keep satisfied";
    }

    if (
        stakeholder.influence === "Low" &&
        stakeholder.interest === "High"
    ) {
        return "Keep informed";
    }

    return "Monitor";
}

console.log("\n" + "=".repeat(78));
console.log("STAKEHOLDER MANAGEMENT");
console.log("=".repeat(78));

for (const stakeholder of project.stakeholders) {
    console.log(
        `${stakeholder.name.padEnd(25)} | ` +
        `${stakeholder.engagementCategory().padEnd(18)} | ` +
        `${engagementAction(stakeholder)}`,
    );
}


// ---------------------------------------------------------------------------
// 19. BENEFITS REVIEW
// ---------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("BENEFITS REVIEW");
console.log("=".repeat(78));

for (const benefit of project.benefits) {
    console.log(
        `${benefit.benefitId} | ${benefit.description} | ` +
        `progress=${benefit.progressPercentage.toFixed(1)}%`,
    );
}

sponsor.reviewBenefits(project);


// ---------------------------------------------------------------------------
// 20. CHANGE CONTROL
// ---------------------------------------------------------------------------

console.log("\n" + "=".repeat(78));
console.log("CHANGE CONTROL");
console.log("=".repeat(78));

sponsor.approveMajorChange(
    project,
    450_000,
    true,
);

console.log(
    `Forecast: ${project.currentForecast.toLocaleString()}`,
);

console.log(
    `Variance: ${project.budgetVariance.toLocaleString()} ` +
    `(${project.budgetVariancePercentage.toFixed(2)}%)`,
);


// ---------------------------------------------------------------------------
// 21. ESCALATION
// ---------------------------------------------------------------------------

function escalationDestination({
    description,
    impact,
    cost,
    strategicChange,
    sponsorAuthority,
}) {
    const text = `${description} ${impact}`.toLowerCase();

    const sponsorTerms = [
        "funding",
        "strategic",
        "executive",
        "major scope",
        "organizational",
        "regulatory",
    ];

    if (
        strategicChange ||
        sponsorTerms.some((term) => text.includes(term))
    ) {
        if (cost > sponsorAuthority) {
            return "Higher governing authority";
        }

        return "Project sponsor";
    }

    return "Project manager or functional lead";
}

console.log("\n" + "=".repeat(78));
console.log("ESCALATION");
console.log("=".repeat(78));

const escalationItems = [
    {
        description: "Funding increase required for strategic integration.",
        impact: "Potential delay without decision.",
        cost: 400_000,
        strategicChange: true,
    },
    {
        description: "Routine test execution clarification required.",
        impact: "Limited operational impact.",
        cost: 10_000,
        strategicChange: false,
    },
    {
        description: "Strategic expansion requires additional enterprise funding.",
        impact: "Material organizational impact.",
        cost: 1_500_000,
        strategicChange: true,
    },
];

for (const item of escalationItems) {
    console.log(
        `${item.description} -> ${escalationDestination({
            ...item,
            sponsorAuthority: sponsor.authorityLimit,
        })}`,
    );
}


// ---------------------------------------------------------------------------
// 22. EARNED VALUE
// ---------------------------------------------------------------------------

class EarnedValue {
    constructor(plannedValue, earnedValue, actualCost) {
        assertNonNegativeNumber(plannedValue, "Planned value");
        assertNonNegativeNumber(earnedValue, "Earned value");
        assertNonNegativeNumber(actualCost, "Actual cost");

        this.plannedValue = plannedValue;
        this.earnedValue = earnedValue;
        this.actualCost = actualCost;
    }

    get scheduleVariance() {
        return this.earnedValue - this.plannedValue;
    }

    get costVariance() {
        return this.earnedValue - this.actualCost;
    }

    get schedulePerformanceIndex() {
        if (this.plannedValue === 0) return Number.NaN;
        return this.earnedValue / this.plannedValue;
    }

    get costPerformanceIndex() {
        if (this.actualCost === 0) return Number.NaN;
        return this.earnedValue / this.actualCost;
    }
}

const earnedValue = new EarnedValue(
    3_000_000,
    2_700_000,
    2_900_000,
);

console.log("\n" + "=".repeat(78));
console.log("EXECUTIVE PROJECT CONTROL");
console.log("=".repeat(78));

console.log(`PV:  ${earnedValue.plannedValue.toLocaleString()}`);
console.log(`EV:  ${earnedValue.earnedValue.toLocaleString()}`);
console.log(`AC:  ${earnedValue.actualCost.toLocaleString()}`);
console.log(`SV:  ${earnedValue.scheduleVariance.toLocaleString()}`);
console.log(`CV:  ${earnedValue.costVariance.toLocaleString()}`);
console.log(`SPI: ${earnedValue.schedulePerformanceIndex.toFixed(3)}`);
console.log(`CPI: ${earnedValue.costPerformanceIndex.toFixed(3)}`);


// ---------------------------------------------------------------------------
// 23. DECISION AUTHORITY
// ---------------------------------------------------------------------------

function decisionAuthority({
    impact,
    cost,
    strategicChange,
    sponsorLimit,
}) {
    assertNonNegativeNumber(cost, "Decision cost");

    if (strategicChange) {
        return cost > sponsorLimit
            ? "Higher governing authority"
            : "Sponsor or governing body";
    }

    if (cost > sponsorLimit) {
        return "Escalate to higher authority";
    }

    if (impact === "low") {
        return "Project manager";
    }

    if (impact === "medium") {
        return "Project manager with governance review";
    }

    return "Project sponsor";
}

console.log("\n" + "=".repeat(78));
console.log("DECISION RIGHTS");
console.log("=".repeat(78));

const decisions = [
    {
        impact: "low",
        cost: 20_000,
        strategicChange: false,
    },
    {
        impact: "medium",
        cost: 100_000,
        strategicChange: false,
    },
    {
        impact: "high",
        cost: 400_000,
        strategicChange: true,
    },
    {
        impact: "high",
        cost: 1_200_000,
        strategicChange: false,
    },
];

for (const decision of decisions) {
    console.log(
        JSON.stringify({
            ...decision,
            authority: decisionAuthority({
                ...decision,
                sponsorLimit: sponsor.authorityLimit,
            }),
        }),
    );
}


// ---------------------------------------------------------------------------
// 24. EVENT-DRIVEN GOVERNANCE
// ---------------------------------------------------------------------------

class GovernanceEventBus {
    constructor() {
        this.handlers = new Map();
    }

    on(eventName, handler) {
        if (!this.handlers.has(eventName)) {
            this.handlers.set(eventName, []);
        }

        this.handlers.get(eventName).push(handler);
    }

    emit(eventName, payload) {
        const handlers = this.handlers.get(eventName) || [];

        for (const handler of handlers) {
            handler(payload);
        }
    }
}

const eventBus = new GovernanceEventBus();

eventBus.on("critical-risk", (risk) => {
    console.log(
        `EVENT -> Critical risk escalation: ${risk.riskId}`,
    );
});

eventBus.on("major-decision", (decision) => {
    console.log(
        `EVENT -> Sponsor decision required: ${decision.decisionId}`,
    );
});

for (const risk of project.risks) {
    if (risk.level === RiskLevel.CRITICAL) {
        eventBus.emit("critical-risk", risk);
    }
}

for (const decision of project.decisions) {
    if (!decision.decided && decision.type === DecisionType.STRATEGIC) {
        eventBus.emit("major-decision", decision);
    }
}


// ---------------------------------------------------------------------------
// 25. ASYNCHRONOUS EXECUTIVE REPORTING
// ---------------------------------------------------------------------------

function delay(milliseconds) {
    return new Promise((resolve) => {
        setTimeout(resolve, milliseconds);
    });
}

async function generateExecutiveReport(project, sponsor) {
    // Async functions model reporting systems that retrieve information
    // from multiple sources such as project controls, risk registers, and
    // benefits systems.
    await delay(10);

    return {
        project: project.name,
        sponsor: sponsor.name,
        status: project.status,
        budget: project.approvedBudget,
        forecast: project.currentForecast,
        budgetVariance: project.budgetVariance,
        criticalRisks: project.criticalRisks.length,
        overdueDecisions: project.overdueDecisions.length,
        averageBenefitProgress:
            Number(project.averageBenefitProgress.toFixed(2)),
        generatedAt: new Date().toISOString(),
    };
}

async function main() {
    console.log("\n" + "=".repeat(78));
    console.log("ASYNC EXECUTIVE REPORT");
    console.log("=".repeat(78));

    const report = await generateExecutiveReport(project, sponsor);

    console.log(JSON.stringify(report, null, 2));

    // A production system would persist this report and send it through
    // controlled enterprise channels rather than printing sensitive data.
    console.log("\nGovernance demonstration completed.");
}

main().catch((error) => {
    console.error("Fatal execution error:", error.message);
    process.exitCode = 1;
});
