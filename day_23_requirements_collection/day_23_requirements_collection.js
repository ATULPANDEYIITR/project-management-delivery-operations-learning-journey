/*
 * Requirements Collection: From Beginner Concepts to an Advanced Workflow
 *
 * This standalone JavaScript file demonstrates requirements collection through
 * practical executable examples. It covers:
 * - terminology and classification
 * - stakeholders
 * - elicitation techniques
 * - user stories
 * - use cases
 * - acceptance criteria
 * - requirement quality
 * - prioritization
 * - conflict detection
 * - traceability
 * - change management
 * - versioning
 * - validation
 * - asynchronous stakeholder interviews
 * - an industry-style requirements repository
 *
 * The file uses standard JavaScript and can run in Node.js.
 */

"use strict";

console.log("=".repeat(80));
console.log("REQUIREMENTS COLLECTION");
console.log("=".repeat(80));


// ---------------------------------------------------------------------------
// 1. FUNDAMENTAL TERMINOLOGY
// ---------------------------------------------------------------------------

const terminology = {
    requirement:
        "A documented need, capability, condition, or constraint that a solution must satisfy.",
    stakeholder:
        "A person or organization affected by, using, funding, managing, or regulating the solution.",
    functionalRequirement:
        "A requirement describing what the system must do.",
    nonFunctionalRequirement:
        "A requirement describing a quality attribute, constraint, or characteristic.",
    acceptanceCriterion:
        "A condition used to determine whether a requirement has been satisfied.",
    assumption:
        "A condition treated as true for planning purposes but not fully verified.",
    constraint:
        "A limitation imposed on the solution or project.",
    dependency:
        "An external condition or component required for successful delivery.",
    traceability:
        "The ability to connect business needs to requirements, implementation, and verification."
};

for (const [term, definition] of Object.entries(terminology)) {
    console.log(`${term}: ${definition}`);
}


// ---------------------------------------------------------------------------
// 2. REQUIREMENT TYPES
// ---------------------------------------------------------------------------

const RequirementType = Object.freeze({
    BUSINESS: "Business",
    USER: "User",
    FUNCTIONAL: "Functional",
    NON_FUNCTIONAL: "Non-functional",
    SECURITY: "Security",
    DATA: "Data",
    INTERFACE: "Interface",
    REGULATORY: "Regulatory",
    CONSTRAINT: "Constraint"
});

const Priority = Object.freeze({
    MUST: "Must",
    SHOULD: "Should",
    COULD: "Could",
    WONT: "Won't"
});


// ---------------------------------------------------------------------------
// 3. REQUIREMENT OBJECT
// ---------------------------------------------------------------------------

class Requirement {
    constructor({
        id,
        title,
        description,
        type,
        priority,
        source,
        stakeholders = [],
        acceptanceCriteria = [],
        dependencies = [],
        assumptions = [],
        status = "Draft",
        version = 1
    }) {
        this.id = id;
        this.title = title;
        this.description = description;
        this.type = type;
        this.priority = priority;
        this.source = source;
        this.stakeholders = [...stakeholders];
        this.acceptanceCriteria = [...acceptanceCriteria];
        this.dependencies = [...dependencies];
        this.assumptions = [...assumptions];
        this.status = status;
        this.version = version;
    }

    isComplete() {
        return Boolean(
            this.id?.trim() &&
            this.title?.trim() &&
            this.description?.trim() &&
            this.source?.trim() &&
            this.acceptanceCriteria.length > 0
        );
    }

    clone() {
        return new Requirement({
            id: this.id,
            title: this.title,
            description: this.description,
            type: this.type,
            priority: this.priority,
            source: this.source,
            stakeholders: [...this.stakeholders],
            acceptanceCriteria: [...this.acceptanceCriteria],
            dependencies: [...this.dependencies],
            assumptions: [...this.assumptions],
            status: this.status,
            version: this.version
        });
    }
}


// ---------------------------------------------------------------------------
// 4. STAKEHOLDERS
// ---------------------------------------------------------------------------

class Stakeholder {
    constructor({
        id,
        name,
        role,
        influence,
        interest,
        needs = [],
        concerns = []
    }) {
        this.id = id;
        this.name = name;
        this.role = role;
        this.influence = influence;
        this.interest = interest;
        this.needs = needs;
        this.concerns = concerns;
    }

    engagementLevel() {
        if (this.influence >= 4 && this.interest >= 4) {
            return "Manage closely";
        }

        if (this.influence >= 4) {
            return "Keep satisfied";
        }

        if (this.interest >= 4) {
            return "Keep informed";
        }

        return "Monitor";
    }
}

const stakeholders = [
    new Stakeholder({
        id: "STK-001",
        name: "Operations Manager",
        role: "Business Owner",
        influence: 5,
        interest: 5,
        needs: ["Operational visibility", "Faster processing"],
        concerns: ["Manual errors", "Delays"]
    }),
    new Stakeholder({
        id: "STK-002",
        name: "Customer",
        role: "End User",
        influence: 3,
        interest: 5,
        needs: ["Simple workflow", "Fast service"],
        concerns: ["Complexity"]
    }),
    new Stakeholder({
        id: "STK-003",
        name: "Security Officer",
        role: "Security",
        influence: 5,
        interest: 4,
        needs: ["Access control", "Auditability"],
        concerns: ["Unauthorized access"]
    })
];

console.log("\nStakeholder engagement:");

for (const stakeholder of stakeholders) {
    console.log(
        `${stakeholder.name}: ${stakeholder.engagementLevel()}`
    );
}


// ---------------------------------------------------------------------------
// 5. ELICITATION METHODS
// ---------------------------------------------------------------------------

const elicitationMethods = {
    interview: {
        strength: "Provides deep individual understanding.",
        limitation: "Can be time-consuming and affected by participant bias."
    },
    questionnaire: {
        strength: "Can collect structured information from many people.",
        limitation: "Provides less opportunity for immediate clarification."
    },
    workshop: {
        strength: "Allows multiple stakeholders to clarify differences together.",
        limitation: "Requires skilled facilitation."
    },
    observation: {
        strength: "Can reveal actual behavior and workarounds.",
        limitation: "Observed sessions may not cover rare situations."
    },
    documentAnalysis: {
        strength: "Uses existing policies, contracts, and procedures.",
        limitation: "Existing documents may be outdated."
    },
    prototype: {
        strength: "Makes unclear interface expectations concrete.",
        limitation: "Stakeholders may focus on appearance rather than underlying requirements."
    }
};

for (const [method, information] of Object.entries(elicitationMethods)) {
    console.log(`\n${method}:`);
    console.log(`  Strength: ${information.strength}`);
    console.log(`  Limitation: ${information.limitation}`);
}


// ---------------------------------------------------------------------------
// 6. INTERVIEW QUESTION GENERATION
// ---------------------------------------------------------------------------

function generateInterviewQuestions(role) {
    const commonQuestions = [
        "What problem are you trying to solve?",
        "Who experiences this problem?",
        "What happens today?",
        "Which part of the current process causes the most difficulty?",
        "What information is required?",
        "What should happen in exceptional situations?",
        "How will success be measured?",
        "What constraints must the solution respect?"
    ];

    const roleQuestions = {
        "Business Owner": [
            "Which business outcome is most important?",
            "Which business metrics should improve?",
            "What deadlines or obligations apply?"
        ],
        "End User": [
            "Which tasks do you perform most often?",
            "Which steps are confusing or slow?",
            "What would make the workflow easier?"
        ],
        "Security": [
            "Which assets need protection?",
            "Which roles require access?",
            "What audit evidence must be retained?"
        ]
    };

    return [
        ...commonQuestions,
        ...(roleQuestions[role] ?? [])
    ];
}

console.log("\nInterview questions:");

for (const question of generateInterviewQuestions("Security")) {
    console.log(`- ${question}`);
}


// ---------------------------------------------------------------------------
// 7. USER STORIES
// ---------------------------------------------------------------------------

class UserStory {
    constructor({
        id,
        role,
        action,
        benefit,
        acceptanceCriteria = []
    }) {
        this.id = id;
        this.role = role;
        this.action = action;
        this.benefit = benefit;
        this.acceptanceCriteria = acceptanceCriteria;
    }

    format() {
        return (
            `As a ${this.role}, I want to ${this.action}, ` +
            `so that ${this.benefit}.`
        );
    }

    qualityChecks() {
        return {
            hasRole: Boolean(this.role?.trim()),
            hasAction: Boolean(this.action?.trim()),
            hasBenefit: Boolean(this.benefit?.trim()),
            hasAcceptanceCriteria: this.acceptanceCriteria.length > 0,
            testable: this.acceptanceCriteria.length > 0,
            reasonablySmall: this.action.split(/\s+/).length <= 15
        };
    }
}

const customerStory = new UserStory({
    id: "US-001",
    role: "customer",
    action: "search for an application",
    benefit: "I can quickly see its current status",
    acceptanceCriteria: [
        "Given a valid application identifier, the current status is displayed.",
        "If no application exists, a controlled not-found message is displayed."
    ]
});

console.log("\nUser story:");
console.log(customerStory.format());

console.log("User story quality:");
console.table(customerStory.qualityChecks());


// ---------------------------------------------------------------------------
// 8. USE CASE
// ---------------------------------------------------------------------------

class UseCase {
    constructor({
        id,
        name,
        primaryActor,
        preconditions,
        mainFlow,
        alternateFlows,
        postconditions
    }) {
        this.id = id;
        this.name = name;
        this.primaryActor = primaryActor;
        this.preconditions = preconditions;
        this.mainFlow = mainFlow;
        this.alternateFlows = alternateFlows;
        this.postconditions = postconditions;
    }

    validate() {
        const issues = [];

        if (!this.name?.trim()) {
            issues.push("Missing use-case name.");
        }

        if (!this.primaryActor?.trim()) {
            issues.push("Missing primary actor.");
        }

        if (!this.preconditions?.length) {
            issues.push("Missing preconditions.");
        }

        if (!this.mainFlow?.length) {
            issues.push("Missing main flow.");
        }

        if (!this.postconditions?.length) {
            issues.push("Missing postconditions.");
        }

        return issues;
    }
}

const submitApplicationUseCase = new UseCase({
    id: "UC-001",
    name: "Submit Application",
    primaryActor: "Customer",
    preconditions: [
        "Customer is authenticated.",
        "Required information is available."
    ],
    mainFlow: [
        "Customer opens the application form.",
        "System displays required fields.",
        "Customer enters information.",
        "System validates information.",
        "System stores the application.",
        "System returns a confirmation identifier."
    ],
    alternateFlows: [
        "Invalid data produces field-level validation messages.",
        "Storage failure must not produce false confirmation."
    ],
    postconditions: [
        "A valid application is stored."
    ]
});

console.log("\nUse case validation:");
console.log(submitApplicationUseCase.validate());


// ---------------------------------------------------------------------------
// 9. REQUIREMENT QUALITY ANALYSIS
// ---------------------------------------------------------------------------

const ambiguousTerms = new Set([
    "fast",
    "easy",
    "simple",
    "quick",
    "user-friendly",
    "appropriate",
    "reasonable",
    "efficient",
    "soon",
    "etc"
]);

function detectAmbiguousTerms(text) {
    const words = text
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, " ")
        .split(/\s+/)
        .filter(Boolean);

    return [...new Set(words.filter(word => ambiguousTerms.has(word)))];
}

function validateRequirement(requirement) {
    const issues = [];

    if (!requirement.id?.trim()) {
        issues.push("Missing identifier.");
    }

    if (!requirement.title?.trim()) {
        issues.push("Missing title.");
    }

    if (!requirement.description?.trim()) {
        issues.push("Missing description.");
    }

    if (!requirement.source?.trim()) {
        issues.push("Missing source.");
    }

    if (!requirement.stakeholders.length) {
        issues.push("No stakeholder linkage.");
    }

    if (!requirement.acceptanceCriteria.length) {
        issues.push("No acceptance criteria.");
    }

    const ambiguous = detectAmbiguousTerms(requirement.description);

    if (ambiguous.length) {
        issues.push(
            `Potentially ambiguous terms: ${ambiguous.join(", ")}`
        );
    }

    return issues;
}

const weakRequirement = new Requirement({
    id: "REQ-WEAK",
    title: "Fast system",
    description: "The system shall be fast and easy to use.",
    type: RequirementType.NON_FUNCTIONAL,
    priority: Priority.MUST,
    source: "Interview"
});

console.log("\nWeak requirement:");
console.log(validateRequirement(weakRequirement));

const strongRequirement = new Requirement({
    id: "REQ-STRONG",
    title: "Application search response time",
    description:
        "The system shall return application search results within " +
        "2 seconds for 95% of requests under the approved workload.",
    type: RequirementType.NON_FUNCTIONAL,
    priority: Priority.MUST,
    source: "Performance workshop",
    stakeholders: ["STK-001"],
    acceptanceCriteria: [
        "At least 95% of measured searches complete within 2 seconds.",
        "The performance test workload is documented."
    ]
});

console.log("\nStrong requirement:");
console.log(validateRequirement(strongRequirement));


// ---------------------------------------------------------------------------
// 10. REQUIREMENT REPOSITORY
// ---------------------------------------------------------------------------

class RequirementsRepository {
    constructor() {
        this.requirements = new Map();
        this.history = new Map();
    }

    add(requirement) {
        if (this.requirements.has(requirement.id)) {
            throw new Error(
                `Requirement ${requirement.id} already exists.`
            );
        }

        this.requirements.set(requirement.id, requirement);
    }

    get(id) {
        const requirement = this.requirements.get(id);

        if (!requirement) {
            throw new Error(`Requirement ${id} was not found.`);
        }

        return requirement;
    }

    updateDescription(id, newDescription) {
        const requirement = this.get(id);

        if (!this.history.has(id)) {
            this.history.set(id, []);
        }

        this.history.get(id).push(requirement.clone());

        requirement.description = newDescription;
        requirement.version += 1;
        requirement.status = "Changed";
    }

    filterByType(type) {
        return [...this.requirements.values()]
            .filter(requirement => requirement.type === type);
    }

    filterByPriority(priority) {
        return [...this.requirements.values()]
            .filter(requirement => requirement.priority === priority);
    }
}

const repository = new RequirementsRepository();

const applicationRequirement = new Requirement({
    id: "REQ-001",
    title: "Application submission",
    description:
        "The system shall allow an authenticated customer to submit " +
        "a completed application.",
    type: RequirementType.FUNCTIONAL,
    priority: Priority.MUST,
    source: "Requirements workshop",
    stakeholders: ["STK-002"],
    acceptanceCriteria: [
        "Required fields are validated before submission.",
        "A successful submission receives a unique identifier.",
        "The customer receives a confirmation."
    ]
});

const accessRequirement = new Requirement({
    id: "REQ-002",
    title: "Access protection",
    description:
        "The system shall restrict application information to " +
        "authenticated users who are authorized to access the record.",
    type: RequirementType.SECURITY,
    priority: Priority.MUST,
    source: "Security workshop",
    stakeholders: ["STK-003"],
    acceptanceCriteria: [
        "Unauthenticated requests are rejected.",
        "Unauthorized users cannot retrieve protected records."
    ]
});

repository.add(applicationRequirement);
repository.add(accessRequirement);

console.log("\nRepository:");
for (const requirement of repository.requirements.values()) {
    console.log(
        `${requirement.id}: ${requirement.title}, version ${requirement.version}`
    );
}


// ---------------------------------------------------------------------------
// 11. VERSIONING AND CHANGE MANAGEMENT
// ---------------------------------------------------------------------------

class ChangeRequest {
    constructor({
        id,
        requirementId,
        requestedBy,
        reason,
        impact
    }) {
        this.id = id;
        this.requirementId = requirementId;
        this.requestedBy = requestedBy;
        this.reason = reason;
        this.impact = impact;
        this.status = "Pending";
        this.createdAt = new Date().toISOString();
    }

    approve() {
        this.status = "Approved";
    }

    reject() {
        this.status = "Rejected";
    }
}

const changeRequest = new ChangeRequest({
    id: "CR-001",
    requirementId: "REQ-001",
    requestedBy: "Operations Manager",
    reason: "The business process has changed.",
    impact: "May require workflow and database changes."
});

changeRequest.approve();

repository.updateDescription(
    "REQ-001",
    "The system shall allow an authenticated customer to submit " +
    "a completed application and return a unique confirmation identifier."
);

console.log("\nChange management:");
console.log(changeRequest);
console.log("Current requirement version:", repository.get("REQ-001").version);
console.log(
    "Historical versions:",
    repository.history.get("REQ-001").length
);


// ---------------------------------------------------------------------------
// 12. PRIORITIZATION
// ---------------------------------------------------------------------------

class PrioritizationScore {
    constructor({
        businessValue,
        urgency,
        riskReduction,
        dependencyImpact
    }) {
        this.businessValue = businessValue;
        this.urgency = urgency;
        this.riskReduction = riskReduction;
        this.dependencyImpact = dependencyImpact;
    }

    total() {
        return (
            this.businessValue +
            this.urgency +
            this.riskReduction +
            this.dependencyImpact
        );
    }
}

const priorityScores = new Map([
    [
        "REQ-001",
        new PrioritizationScore({
            businessValue: 5,
            urgency: 5,
            riskReduction: 3,
            dependencyImpact: 4
        })
    ],
    [
        "REQ-002",
        new PrioritizationScore({
            businessValue: 5,
            urgency: 5,
            riskReduction: 5,
            dependencyImpact: 5
        })
    ]
]);

console.log("\nPrioritization:");
for (const [id, score] of priorityScores.entries()) {
    console.log(`${id}: ${score.total()}`);
}

console.log(
    "Scoring criteria should be agreed with stakeholders; numerical scores " +
    "support discussion rather than replacing judgment."
);


// ---------------------------------------------------------------------------
// 13. CONFLICT DETECTION
// ---------------------------------------------------------------------------

function detectPotentialConflict(requirementA, requirementB) {
    const textA = requirementA.description.toLowerCase();
    const textB = requirementB.description.toLowerCase();

    const accessA = textA.includes("access");
    const accessB = textB.includes("access");

    const protectionA =
        textA.includes("prevent") ||
        textA.includes("restrict") ||
        textA.includes("unauthorized");

    const protectionB =
        textB.includes("prevent") ||
        textB.includes("restrict") ||
        textB.includes("unauthorized");

    if ((accessA && protectionB) || (accessB && protectionA)) {
        return (
            "Potential access-control conflict. Clarify authorized roles, " +
            "data scope, and access conditions."
        );
    }

    return null;
}

const managerAccessRequirement = new Requirement({
    id: "REQ-003",
    title: "Manager operational access",
    description:
        "Managers shall have access to operational customer data.",
    type: RequirementType.FUNCTIONAL,
    priority: Priority.MUST,
    source: "Manager interview",
    stakeholders: ["STK-001"],
    acceptanceCriteria: [
        "Authorized managers can access required operational information."
    ]
});

console.log("\nConflict analysis:");
console.log(
    detectPotentialConflict(
        managerAccessRequirement,
        accessRequirement
    ) ?? "No potential conflict detected."
);


// ---------------------------------------------------------------------------
// 14. TRACEABILITY
// ---------------------------------------------------------------------------

class TraceabilityMatrix {
    constructor() {
        this.businessToUser = new Map();
        this.userToRequirement = new Map();
        this.requirementToTest = new Map();
    }

    addBusinessToUser(businessId, userStoryId) {
        this.businessToUser.set(businessId, userStoryId);
    }

    addUserToRequirement(userStoryId, requirementId) {
        this.userToRequirement.set(userStoryId, requirementId);
    }

    addRequirementToTest(requirementId, testId) {
        this.requirementToTest.set(requirementId, testId);
    }

    findUnverified(requirementIds) {
        return requirementIds.filter(
            id => !this.requirementToTest.has(id)
        );
    }
}

const traceability = new TraceabilityMatrix();

traceability.addBusinessToUser("BUS-001", "US-001");
traceability.addUserToRequirement("US-001", "REQ-001");
traceability.addRequirementToTest("REQ-001", "TEST-001");

console.log("\nTraceability:");
console.log(traceability);


// ---------------------------------------------------------------------------
// 15. SCOPE BOUNDARIES
// ---------------------------------------------------------------------------

class ScopeBoundary {
    constructor(inScope, outOfScope) {
        this.inScope = new Set(inScope);
        this.outOfScope = new Set(outOfScope);
    }

    classify(item) {
        if (this.inScope.has(item)) {
            return "In scope";
        }

        if (this.outOfScope.has(item)) {
            return "Out of scope";
        }

        return "Unclassified";
    }
}

const scope = new ScopeBoundary(
    [
        "Application submission",
        "Application status tracking",
        "Authentication",
        "Manager dashboard"
    ],
    [
        "Unrelated accounting replacement",
        "International expansion"
    ]
);

console.log("\nScope:");
for (const item of [
    "Application submission",
    "International expansion",
    "Unknown integration"
]) {
    console.log(`${item}: ${scope.classify(item)}`);
}


// ---------------------------------------------------------------------------
// 16. ASYNCHRONOUS REQUIREMENTS ELICITATION
// ---------------------------------------------------------------------------

function simulateStakeholderInterview(stakeholder, delayMilliseconds) {
    return new Promise(resolve => {
        setTimeout(() => {
            resolve({
                stakeholder: stakeholder.name,
                role: stakeholder.role,
                findings: [
                    `Primary needs identified for ${stakeholder.role}.`,
                    "Current pain points documented.",
                    "Potential constraints recorded."
                ]
            });
        }, delayMilliseconds);
    });
}

async function runConcurrentInterviews() {
    /*
     * Promise.all models parallel information collection.
     * Real projects still require human facilitation, validation, and
     * interpretation after information is collected.
     */
    const interviews = await Promise.all(
        stakeholders.map((stakeholder, index) =>
            simulateStakeholderInterview(stakeholder, 100 + index * 50)
        )
    );

    console.log("\nAsynchronous interview results:");
    for (const interview of interviews) {
        console.log(interview);
    }

    return interviews;
}


// ---------------------------------------------------------------------------
// 17. REQUIREMENTS METRICS
// ---------------------------------------------------------------------------

function calculateMetrics(repositoryInstance) {
    const items = [...repositoryInstance.requirements.values()];

    if (items.length === 0) {
        return {
            count: 0,
            completePercentage: 0,
            mustPercentage: 0
        };
    }

    const complete = items.filter(item => item.isComplete()).length;
    const must = items.filter(
        item => item.priority === Priority.MUST
    ).length;

    return {
        count: items.length,
        completePercentage: complete / items.length * 100,
        mustPercentage: must / items.length * 100
    };
}

console.log("\nRepository metrics:");
console.log(calculateMetrics(repository));


// ---------------------------------------------------------------------------
// 18. PERFORMANCE CONSIDERATIONS
// ---------------------------------------------------------------------------

function linearSearch(requirements, id) {
    /*
     * O(n) lookup. Suitable for small collections or scans.
     */
    return requirements.find(requirement => requirement.id === id);
}

function indexedSearch(requirementMap, id) {
    /*
     * Map lookup is approximately O(1) average-case for identifier retrieval.
     */
    return requirementMap.get(id);
}

console.log("\nPerformance:");
console.log("Array.find(): O(n) identifier lookup.");
console.log("Map.get(): approximately O(1) average-case identifier lookup.");
console.log(
    "Large repositories may require database indexes, pagination, " +
    "search indexes, caching, and access-control filtering."
);


// ---------------------------------------------------------------------------
// 19. SECURITY CONSIDERATIONS
// ---------------------------------------------------------------------------

const securityPrinciples = [
    "Restrict who can create, edit, approve, and delete requirements.",
    "Maintain an audit trail for material changes.",
    "Protect confidential business and stakeholder information.",
    "Do not place passwords, API keys, or tokens in requirement records.",
    "Validate imported requirement data.",
    "Apply authorization independently from authentication.",
    "Define retention rules for interview notes and workshop records."
];

console.log("\nSecurity considerations:");
securityPrinciples.forEach(principle => console.log(`- ${principle}`));


// ---------------------------------------------------------------------------
// 20. INDUSTRY-STYLE REQUIREMENTS COLLECTION SERVICE
// ---------------------------------------------------------------------------

class RequirementsCollectionService {
    constructor() {
        this.notes = [];
        this.repository = new RequirementsRepository();
        this.approved = new Set();
    }

    captureNote(note) {
        if (!note?.trim()) {
            throw new Error("Discovery note cannot be empty.");
        }

        this.notes.push({
            text: note.trim(),
            timestamp: new Date().toISOString()
        });
    }

    registerRequirement(requirement) {
        const issues = validateRequirement(requirement);

        if (issues.length > 0) {
            throw new Error(
                `Requirement ${requirement.id} failed validation: ` +
                issues.join(" | ")
            );
        }

        this.repository.add(requirement);
    }

    approveRequirement(id) {
        const requirement = this.repository.get(id);

        if (!requirement.isComplete()) {
            throw new Error(
                `${id} cannot be approved because it is incomplete.`
            );
        }

        requirement.status = "Approved";
        this.approved.add(id);
    }

    report() {
        return {
            discoveryNotes: this.notes.length,
            requirements: this.repository.requirements.size,
            approved: this.approved.size
        };
    }
}

async function runCaseStudy() {
    const service = new RequirementsCollectionService();

    service.captureNote(
        "Customers currently contact support because application status is difficult to find."
    );

    service.captureNote(
        "Operations staff manually compile status information."
    );

    service.captureNote(
        "Security requires authenticated and authorized access."
    );

    const caseRequirement = new Requirement({
        id: "CASE-001",
        title: "Application status search",
        description:
            "The system shall allow an authenticated customer to search " +
            "for an application using its unique identifier.",
        type: RequirementType.FUNCTIONAL,
        priority: Priority.MUST,
        source: "Customer interview",
        stakeholders: ["STK-002"],
        acceptanceCriteria: [
            "An authenticated customer can submit a valid identifier.",
            "The system displays the current application status.",
            "An invalid identifier returns a controlled not-found response."
        ]
    });

    service.registerRequirement(caseRequirement);
    service.approveRequirement("CASE-001");

    const interviews = await runConcurrentInterviews();

    console.log("\nCase study report:");
    console.log(service.report());

    return interviews;
}


// ---------------------------------------------------------------------------
// 21. EDGE CASE HANDLING
// ---------------------------------------------------------------------------

console.log("\nEdge cases:");

try {
    repository.add(applicationRequirement);
} catch (error) {
    console.log(`Duplicate requirement rejected: ${error.message}`);
}

try {
    repository.get("REQ-NOT-FOUND");
} catch (error) {
    console.log(`Missing requirement handled: ${error.message}`);
}

try {
    const invalid = new Requirement({
        id: "",
        title: "",
        description: "",
        type: RequirementType.FUNCTIONAL,
        priority: Priority.MUST,
        source: ""
    });

    const issues = validateRequirement(invalid);
    console.log("Invalid requirement issues:", issues);
} catch (error) {
    console.log(`Unexpected validation error: ${error.message}`);
}


// ---------------------------------------------------------------------------
// 22. REQUIREMENTS COLLECTION CHECKLIST
// ---------------------------------------------------------------------------

const collectionChecklist = [
    "Define the business problem.",
    "Identify stakeholders.",
    "Understand the current process.",
    "Collect goals, needs, pain points, and constraints.",
    "Identify business rules.",
    "Identify functional requirements.",
    "Identify non-functional requirements.",
    "Identify data and interface requirements.",
    "Identify security and regulatory requirements.",
    "Document assumptions and dependencies.",
    "Write clear and testable requirements.",
    "Resolve contradictions and ambiguity.",
    "Prioritize using agreed criteria.",
    "Validate with stakeholders.",
    "Create traceability.",
    "Baseline approved requirements.",
    "Control future changes."
];

console.log("\nRequirements collection checklist:");

collectionChecklist.forEach(
    (item, index) => console.log(`${String(index + 1).padStart(2, "0")}. ${item}`)
);


// ---------------------------------------------------------------------------
// 23. EXECUTION
// ---------------------------------------------------------------------------

runCaseStudy()
    .then(() => {
        console.log("\nRequirements collection demonstration completed.");
    })
    .catch(error => {
        console.error("Case study execution failed:", error.message);
        process.exitCode = 1;
    });
