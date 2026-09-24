/*
 * Requirements Documentation
 * ===========================
 *
 * A self-contained JavaScript study program for documenting software
 * requirements from fundamental concepts through advanced practices.
 *
 * Demonstrates:
 *   - requirement classification
 *   - stakeholders
 *   - user stories
 *   - acceptance criteria
 *   - validation
 *   - prioritization
 *   - traceability
 *   - dependencies
 *   - change management
 *   - conflict detection
 *   - quality metrics
 *   - document generation
 *   - a realistic service-request case study
 *
 * Runtime: Node.js 18+ recommended.
 */


// ---------------------------------------------------------------------------
// 1. Enumerations
// ---------------------------------------------------------------------------

const RequirementType = Object.freeze({
    BUSINESS: "Business",
    USER: "User",
    FUNCTIONAL: "Functional",
    NON_FUNCTIONAL: "Non-functional",
    DATA: "Data",
    INTERFACE: "Interface",
    REGULATORY: "Regulatory",
    SECURITY: "Security"
});

const Priority = Object.freeze({
    MUST: "Must",
    SHOULD: "Should",
    COULD: "Could",
    WONT: "Won't"
});

const RequirementStatus = Object.freeze({
    PROPOSED: "Proposed",
    APPROVED: "Approved",
    IMPLEMENTED: "Implemented",
    VERIFIED: "Verified",
    REJECTED: "Rejected"
});


// ---------------------------------------------------------------------------
// 2. Acceptance criteria
// ---------------------------------------------------------------------------

class AcceptanceCriterion {
    constructor(id, description, expectedResult, testable = true) {
        this.id = id;
        this.description = description;
        this.expectedResult = expectedResult;
        this.testable = testable;
    }

    validate() {
        const errors = [];

        if (!this.id.trim()) {
            errors.push("Acceptance criterion ID is missing.");
        }

        if (!this.description.trim()) {
            errors.push("Acceptance criterion description is missing.");
        }

        if (!this.expectedResult.trim()) {
            errors.push("Expected result is missing.");
        }

        return errors;
    }
}


// ---------------------------------------------------------------------------
// 3. Stakeholders
// ---------------------------------------------------------------------------

class Stakeholder {
    constructor(id, name, role, influence, interest) {
        this.id = id;
        this.name = name;
        this.role = role;
        this.influence = influence;
        this.interest = interest;
    }

    getPriorityScore() {
        return this.influence * this.interest;
    }
}


// ---------------------------------------------------------------------------
// 4. Requirements
// ---------------------------------------------------------------------------

class Requirement {
    constructor({
        id,
        title,
        description,
        type,
        priority,
        status = RequirementStatus.PROPOSED,
        source = "",
        rationale = "",
        owner = "",
        acceptanceCriteria = [],
        stakeholderIds = [],
        dependencies = [],
        relatedRequirements = [],
        tags = [],
        assumptions = [],
        constraints = [],
        risks = [],
        version = 1
    }) {
        this.id = id;
        this.title = title;
        this.description = description;
        this.type = type;
        this.priority = priority;
        this.status = status;
        this.source = source;
        this.rationale = rationale;
        this.owner = owner;
        this.acceptanceCriteria = acceptanceCriteria;
        this.stakeholderIds = new Set(stakeholderIds);
        this.dependencies = new Set(dependencies);
        this.relatedRequirements = new Set(relatedRequirements);
        this.tags = new Set(tags);
        this.assumptions = assumptions;
        this.constraints = constraints;
        this.risks = risks;
        this.version = version;
        this.createdAt = new Date().toISOString();
    }

    validate() {
        const errors = [];

        if (!this.id.trim()) {
            errors.push("Missing requirement ID.");
        }

        if (!this.title.trim()) {
            errors.push("Missing requirement title.");
        }

        if (!this.description.trim()) {
            errors.push("Missing requirement description.");
        }

        if (this.description.trim().split(/\s+/).length < 5) {
            errors.push("Description is probably too short.");
        }

        const vagueWords = [
            "easy",
            "fast",
            "user-friendly",
            "appropriate",
            "reasonable",
            "simple",
            "etc",
            "soon",
            "adequate"
        ];

        const lower = this.description.toLowerCase();
        const foundVagueWords = vagueWords.filter(word =>
            new RegExp(`\\b${escapeRegExp(word)}\\b`, "i").test(lower)
        );

        if (foundVagueWords.length > 0) {
            errors.push(
                `Potentially vague terms: ${foundVagueWords.join(", ")}`
            );
        }

        if (
            [
                RequirementType.FUNCTIONAL,
                RequirementType.SECURITY,
                RequirementType.NON_FUNCTIONAL
            ].includes(this.type) &&
            this.acceptanceCriteria.length === 0
        ) {
            errors.push("Requirement has no acceptance criteria.");
        }

        if (!this.source.trim()) {
            errors.push("Requirement has no documented source.");
        }

        if (!this.rationale.trim()) {
            errors.push("Requirement has no documented rationale.");
        }

        for (const criterion of this.acceptanceCriteria) {
            errors.push(...criterion.validate());
        }

        return errors;
    }

    isVerifiable() {
        return (
            this.acceptanceCriteria.length > 0 &&
            this.acceptanceCriteria.every(criterion => criterion.testable)
        );
    }
}

function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}


// ---------------------------------------------------------------------------
// 5. Repository
// ---------------------------------------------------------------------------

class RequirementsRepository {
    constructor() {
        this.requirements = new Map();
        this.stakeholders = new Map();
        this.changes = new Map();
    }

    addStakeholder(stakeholder) {
        if (this.stakeholders.has(stakeholder.id)) {
            throw new Error(`Duplicate stakeholder ID: ${stakeholder.id}`);
        }

        this.stakeholders.set(stakeholder.id, stakeholder);
    }

    addRequirement(requirement) {
        if (this.requirements.has(requirement.id)) {
            throw new Error(`Duplicate requirement ID: ${requirement.id}`);
        }

        for (const stakeholderId of requirement.stakeholderIds) {
            if (!this.stakeholders.has(stakeholderId)) {
                throw new Error(
                    `Unknown stakeholder ID: ${stakeholderId}`
                );
            }
        }

        this.requirements.set(requirement.id, requirement);
    }

    get(id) {
        const requirement = this.requirements.get(id);

        if (!requirement) {
            throw new Error(`Requirement not found: ${id}`);
        }

        return requirement;
    }

    search(query) {
        const needle = query.toLowerCase();

        return [...this.requirements.values()].filter(requirement =>
            requirement.id.toLowerCase().includes(needle) ||
            requirement.title.toLowerCase().includes(needle) ||
            requirement.description.toLowerCase().includes(needle) ||
            [...requirement.tags].some(tag =>
                tag.toLowerCase().includes(needle)
            )
        );
    }

    filterByType(type) {
        return [...this.requirements.values()].filter(
            requirement => requirement.type === type
        );
    }

    updateRequirement(id, changes) {
        const requirement = this.get(id);

        if (changes.description !== undefined) {
            requirement.description = changes.description;
        }

        if (changes.priority !== undefined) {
            requirement.priority = changes.priority;
        }

        if (changes.acceptanceCriteria !== undefined) {
            requirement.acceptanceCriteria = changes.acceptanceCriteria;
        }

        requirement.version += 1;

        return requirement;
    }
}


// ---------------------------------------------------------------------------
// 6. Traceability
// ---------------------------------------------------------------------------

class TraceabilityMatrix {
    constructor() {
        this.design = new Map();
        this.code = new Map();
        this.tests = new Map();
    }

    addLink(map, requirementId, artifactId) {
        if (!map.has(requirementId)) {
            map.set(requirementId, new Set());
        }

        map.get(requirementId).add(artifactId);
    }

    linkDesign(requirementId, designId) {
        this.addLink(this.design, requirementId, designId);
    }

    linkCode(requirementId, codeId) {
        this.addLink(this.code, requirementId, codeId);
    }

    linkTest(requirementId, testId) {
        this.addLink(this.tests, requirementId, testId);
    }

    hasLink(map, requirementId) {
        return map.has(requirementId) && map.get(requirementId).size > 0;
    }

    coverage(requirementIds) {
        const ids = [...requirementIds];

        if (ids.length === 0) {
            return {
                design: 0,
                code: 0,
                tests: 0,
                complete: 0
            };
        }

        const design = ids.filter(id => this.hasLink(this.design, id)).length;
        const code = ids.filter(id => this.hasLink(this.code, id)).length;
        const tests = ids.filter(id => this.hasLink(this.tests, id)).length;

        const complete = ids.filter(id =>
            this.hasLink(this.design, id) &&
            this.hasLink(this.code, id) &&
            this.hasLink(this.tests, id)
        ).length;

        const percentage = value => value / ids.length * 100;

        return {
            design: percentage(design),
            code: percentage(code),
            tests: percentage(tests),
            complete: percentage(complete)
        };
    }
}


// ---------------------------------------------------------------------------
// 7. Change management
// ---------------------------------------------------------------------------

class ChangeRequest {
    constructor(
        id,
        requirementId,
        requestedBy,
        description,
        businessReason,
        impact
    ) {
        this.id = id;
        this.requirementId = requirementId;
        this.requestedBy = requestedBy;
        this.description = description;
        this.businessReason = businessReason;
        this.impact = impact;
        this.status = "Proposed";
        this.oldVersion = 1;
        this.newVersion = null;
    }

    approve(currentVersion) {
        this.status = "Approved";
        this.oldVersion = currentVersion;
        this.newVersion = currentVersion + 1;
    }
}


// ---------------------------------------------------------------------------
// 8. Analyzer
// ---------------------------------------------------------------------------

class RequirementsAnalyzer {
    constructor(repository, traceability) {
        this.repository = repository;
        this.traceability = traceability;
    }

    validateAll() {
        const result = new Map();

        for (const requirement of this.repository.requirements.values()) {
            result.set(requirement.id, requirement.validate());
        }

        return result;
    }

    priorityDistribution() {
        const distribution = {
            [Priority.MUST]: 0,
            [Priority.SHOULD]: 0,
            [Priority.COULD]: 0,
            [Priority.WONT]: 0
        };

        for (const requirement of this.repository.requirements.values()) {
            distribution[requirement.priority]++;
        }

        return distribution;
    }

    qualityMetrics() {
        const requirements = [...this.repository.requirements.values()];

        if (requirements.length === 0) {
            return {};
        }

        const percentage = predicate =>
            requirements.filter(predicate).length /
            requirements.length *
            100;

        const validationErrors = requirements.reduce(
            (total, requirement) =>
                total + requirement.validate().length,
            0
        );

        return {
            totalRequirements: requirements.length,
            acceptanceCriteriaCoverage: percentage(
                requirement =>
                    requirement.acceptanceCriteria.length > 0
            ),
            sourceCoverage: percentage(
                requirement =>
                    requirement.source.trim().length > 0
            ),
            rationaleCoverage: percentage(
                requirement =>
                    requirement.rationale.trim().length > 0
            ),
            verifiability: percentage(
                requirement =>
                    requirement.isVerifiable()
            ),
            validationErrors
        };
    }

    stakeholderImpact() {
        return [...this.repository.stakeholders.values()]
            .map(stakeholder => ({
                name: stakeholder.name,
                score: stakeholder.getPriorityScore()
            }))
            .sort((a, b) => b.score - a.score);
    }

    findSimilarRequirements(threshold = 55) {
        const requirements =
            [...this.repository.requirements.values()];
        const results = [];

        for (let i = 0; i < requirements.length; i++) {
            for (let j = i + 1; j < requirements.length; j++) {
                const score = lexicalSimilarity(
                    requirements[i].description,
                    requirements[j].description
                );

                if (score >= threshold) {
                    results.push({
                        first: requirements[i].id,
                        second: requirements[j].id,
                        similarity: score
                    });
                }
            }
        }

        return results;
    }
}


function wordSet(text) {
    return new Set(
        text
            .toLowerCase()
            .match(/[a-z0-9]+/g)
            ?.filter(word => word.length > 2) ?? []
    );
}


function lexicalSimilarity(firstText, secondText) {
    const first = wordSet(firstText);
    const second = wordSet(secondText);

    if (first.size === 0 || second.size === 0) {
        return 0;
    }

    const intersection = [...first].filter(word =>
        second.has(word)
    ).length;

    const union = new Set([...first, ...second]).size;

    return intersection / union * 100;
}


// ---------------------------------------------------------------------------
// 9. User stories
// ---------------------------------------------------------------------------

function createUserStory(actor, action, benefit) {
    if (![actor, action, benefit].every(value => value.trim())) {
        throw new Error("User-story fields cannot be empty.");
    }

    return (
        `As a ${actor}, I want ${action}, ` +
        `so that ${benefit}.`
    );
}


function createAcceptanceCriterion(
    id,
    condition,
    behavior,
    expectedResult
) {
    return new AcceptanceCriterion(
        id,
        `Given ${condition}, when ${behavior}`,
        expectedResult
    );
}


// ---------------------------------------------------------------------------
// 10. Requirements document generator
// ---------------------------------------------------------------------------

function generateMarkdownDocument(repository, traceability) {
    const lines = [
        "# Digital Service Request Platform Requirements",
        "",
        "## Stakeholders",
        "",
        "| ID | Stakeholder | Role | Influence | Interest |",
        "|---|---|---|---:|---:|"
    ];

    for (const stakeholder of repository.stakeholders.values()) {
        lines.push(
            `| ${stakeholder.id} | ${stakeholder.name} | ` +
            `${stakeholder.role} | ${stakeholder.influence} | ` +
            `${stakeholder.interest} |`
        );
    }

    lines.push(
        "",
        "## Requirements",
        "",
        "| ID | Type | Priority | Status | Title |",
        "|---|---|---|---|---|"
    );

    for (const requirement of repository.requirements.values()) {
        lines.push(
            `| ${requirement.id} | ${requirement.type} | ` +
            `${requirement.priority} | ${requirement.status} | ` +
            `${requirement.title} |`
        );
    }

    for (const requirement of repository.requirements.values()) {
        lines.push(
            "",
            `### ${requirement.id}: ${requirement.title}`,
            "",
            `**Description:** ${requirement.description}`,
            "",
            `**Source:** ${requirement.source}`,
            "",
            `**Rationale:** ${requirement.rationale}`,
            "",
            "**Acceptance criteria:**",
            ""
        );

        for (const criterion of requirement.acceptanceCriteria) {
            lines.push(
                `- ${criterion.id}: ${criterion.description}. ` +
                `Expected result: ${criterion.expectedResult}`
            );
        }
    }

    lines.push(
        "",
        "## Traceability",
        "",
        "| Requirement | Design | Code | Tests |",
        "|---|---|---|---|"
    );

    for (const requirement of repository.requirements.values()) {
        const design = [...(
            traceability.design.get(requirement.id) ?? []
        )].join(", ") || "Not linked";

        const code = [...(
            traceability.code.get(requirement.id) ?? []
        )].join(", ") || "Not linked";

        const tests = [...(
            traceability.tests.get(requirement.id) ?? []
        )].join(", ") || "Not linked";

        lines.push(
            `| ${requirement.id} | ${design} | ${code} | ${tests} |`
        );
    }

    return lines.join("\n");
}


// ---------------------------------------------------------------------------
// 11. Case study
// ---------------------------------------------------------------------------

function buildCaseStudy() {
    const repository = new RequirementsRepository();
    const traceability = new TraceabilityMatrix();

    const stakeholders = [
        new Stakeholder(
            "STK-001",
            "Service Customer",
            "Primary user",
            4,
            5
        ),
        new Stakeholder(
            "STK-002",
            "Operations Manager",
            "Business owner",
            5,
            5
        ),
        new Stakeholder(
            "STK-003",
            "Support Agent",
            "Operational user",
            4,
            4
        ),
        new Stakeholder(
            "STK-004",
            "Security Officer",
            "Security governance",
            5,
            4
        ),
        new Stakeholder(
            "STK-005",
            "Compliance Officer",
            "Regulatory governance",
            5,
            3
        )
    ];

    stakeholders.forEach(stakeholder =>
        repository.addStakeholder(stakeholder)
    );

    repository.addRequirement(new Requirement({
        id: "BR-001",
        title: "Digital service requests",
        description:
            "The platform shall provide a digital channel for customers " +
            "to submit service requests without contacting an agent.",
        type: RequirementType.BUSINESS,
        priority: Priority.MUST,
        status: RequirementStatus.APPROVED,
        source: "Operations workshop",
        rationale:
            "The organization wants to reduce manual request handling " +
            "and provide a measurable digital service channel.",
        owner: "Operations Manager",
        stakeholderIds: ["STK-001", "STK-002"],
        tags: ["business", "digital-service"]
    }));

    repository.addRequirement(new Requirement({
        id: "FR-001",
        title: "Create a service request",
        description:
            "The system shall allow an authenticated customer to create " +
            "a service request by selecting a category, entering a " +
            "description, and submitting the request.",
        type: RequirementType.FUNCTIONAL,
        priority: Priority.MUST,
        status: RequirementStatus.APPROVED,
        source: "Customer interview",
        rationale:
            "Request creation is the primary customer workflow.",
        owner: "Product Owner",
        stakeholderIds: ["STK-001", "STK-002"],
        dependencies: ["BR-001"],
        tags: ["customer", "request", "core"],
        acceptanceCriteria: [
            createAcceptanceCriterion(
                "AC-001",
                "the customer is authenticated",
                "the customer provides a valid category and description",
                "a unique request ID is created and displayed"
            ),
            createAcceptanceCriterion(
                "AC-002",
                "the description is empty",
                "the customer attempts submission",
                "the request is rejected with a validation message"
            )
        ]
    }));

    repository.addRequirement(new Requirement({
        id: "FR-002",
        title: "Track request status",
        description:
            "The system shall allow customers to view the current " +
            "status and status history of their submitted requests.",
        type: RequirementType.FUNCTIONAL,
        priority: Priority.MUST,
        status: RequirementStatus.APPROVED,
        source: "Customer interview",
        rationale:
            "Customers need visibility into progress after submission.",
        owner: "Product Owner",
        stakeholderIds: ["STK-001", "STK-003"],
        dependencies: ["FR-001"],
        tags: ["customer", "tracking"],
        acceptanceCriteria: [
            createAcceptanceCriterion(
                "AC-003",
                "the customer owns the request",
                "the customer opens the request details",
                "the current status and chronological status history are shown"
            )
        ]
    }));

    repository.addRequirement(new Requirement({
        id: "FR-003",
        title: "Agent request queue",
        description:
            "The system shall provide authorized support agents with " +
            "a queue containing requests assigned to their operational team.",
        type: RequirementType.FUNCTIONAL,
        priority: Priority.MUST,
        status: RequirementStatus.APPROVED,
        source: "Operations workshop",
        rationale:
            "Agents require a controlled operational work queue.",
        owner: "Operations Manager",
        stakeholderIds: ["STK-002", "STK-003"],
        dependencies: ["FR-001"],
        tags: ["agent", "operations"],
        acceptanceCriteria: [
            createAcceptanceCriterion(
                "AC-004",
                "the user has the support-agent role",
                "the user opens the request queue",
                "only requests accessible to that operational team are shown"
            )
        ]
    }));

    repository.addRequirement(new Requirement({
        id: "NFR-001",
        title: "Request response time",
        description:
            "The service shall return a successful request-status query " +
            "within 2 seconds for at least 95 percent of requests under " +
            "the defined normal operating load.",
        type: RequirementType.NON_FUNCTIONAL,
        priority: Priority.SHOULD,
        status: RequirementStatus.APPROVED,
        source: "Performance workshop",
        rationale:
            "Response-time expectations affect customer usability.",
        owner: "Engineering",
        stakeholderIds: ["STK-001", "STK-002"],
        tags: ["performance", "latency"],
        constraints: [
            "Normal operating load must be defined before performance testing."
        ],
        acceptanceCriteria: [
            createAcceptanceCriterion(
                "AC-005",
                "the system is under normal operating load",
                "1000 status queries are executed",
                "at least 950 complete within 2 seconds"
            )
        ]
    }));

    repository.addRequirement(new Requirement({
        id: "SEC-001",
        title: "Role-based access control",
        description:
            "The system shall enforce role-based authorization so that " +
            "customers, support agents, managers, and administrators can " +
            "access only operations permitted for their roles.",
        type: RequirementType.SECURITY,
        priority: Priority.MUST,
        status: RequirementStatus.APPROVED,
        source: "Security architecture review",
        rationale:
            "Authorization prevents unauthorized access to service data.",
        owner: "Security Officer",
        stakeholderIds: ["STK-004", "STK-003"],
        dependencies: ["FR-001"],
        tags: ["security", "authorization"],
        acceptanceCriteria: [
            createAcceptanceCriterion(
                "AC-006",
                "a customer attempts to access another customer's request",
                "the authorization check executes",
                "access is denied and the event is recorded"
            ),
            createAcceptanceCriterion(
                "AC-007",
                "an agent accesses an authorized team request",
                "the authorization check executes",
                "the request is displayed"
            )
        ]
    }));

    repository.addRequirement(new Requirement({
        id: "DATA-001",
        title: "Request audit history",
        description:
            "The system shall record creation, assignment, status changes, " +
            "and closure events for each service request with event time, " +
            "actor identifier, and event type.",
        type: RequirementType.DATA,
        priority: Priority.MUST,
        status: RequirementStatus.APPROVED,
        source: "Compliance workshop",
        rationale:
            "Auditable history supports accountability and investigation.",
        owner: "Compliance Officer",
        stakeholderIds: ["STK-005", "STK-004"],
        tags: ["audit", "compliance", "data"],
        constraints: [
            "Audit records must not be editable through normal application operations."
        ],
        acceptanceCriteria: [
            createAcceptanceCriterion(
                "AC-008",
                "a request status changes",
                "the transaction completes",
                "an immutable audit event exists with actor and timestamp"
            )
        ]
    }));

    traceability.linkDesign("BR-001", "ARCH-001");
    traceability.linkDesign("FR-001", "DESIGN-REQ-API");
    traceability.linkDesign("FR-002", "DESIGN-REQUEST-VIEW");
    traceability.linkDesign("FR-003", "DESIGN-AGENT-QUEUE");
    traceability.linkDesign("NFR-001", "DESIGN-PERFORMANCE");
    traceability.linkDesign("SEC-001", "DESIGN-AUTHZ");
    traceability.linkDesign("DATA-001", "DESIGN-AUDIT");

    traceability.linkCode("FR-001", "RequestService.create");
    traceability.linkCode("FR-002", "RequestService.getStatus");
    traceability.linkCode("FR-003", "AgentQueue.list");
    traceability.linkCode("SEC-001", "AuthorizationPolicy");
    traceability.linkCode("DATA-001", "AuditRepository");

    traceability.linkTest("FR-001", "TEST-REQ-CREATE-001");
    traceability.linkTest("FR-002", "TEST-REQ-STATUS-001");
    traceability.linkTest("FR-003", "TEST-QUEUE-001");
    traceability.linkTest("NFR-001", "TEST-PERF-001");
    traceability.linkTest("SEC-001", "TEST-AUTHZ-001");
    traceability.linkTest("DATA-001", "TEST-AUDIT-001");

    return { repository, traceability };
}


// ---------------------------------------------------------------------------
// 12. Demonstrations
// ---------------------------------------------------------------------------

function printSection(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}


function demonstrateBasics() {
    printSection("FUNDAMENTALS");

    const concepts = {
        Requirement:
            "A documented need, capability, condition, or constraint.",
        Elicitation:
            "Discovering requirements from stakeholders, evidence, and context.",
        Specification:
            "Expressing requirements in a structured, reviewable form.",
        Validation:
            "Checking whether requirements are suitable, clear, feasible, and verifiable.",
        Verification:
            "Checking whether an implemented system satisfies its requirements.",
        Traceability:
            "Connecting requirements to sources, designs, code, and tests.",
        AcceptanceCriterion:
            "A testable condition used to determine satisfaction."
    };

    for (const [name, definition] of Object.entries(concepts)) {
        console.log(`${name}: ${definition}`);
    }
}


function demonstrateUserStory() {
    printSection("USER STORY");

    const story = createUserStory(
        "customer",
        "view the status of my service request",
        "know whether action is still required from me"
    );

    console.log(story);

    const criterion = createAcceptanceCriterion(
        "AC-DEMO-001",
        "the request belongs to the authenticated customer",
        "the customer opens the request",
        "the current status and history are displayed"
    );

    console.log(`${criterion.id}: ${criterion.description}`);
    console.log(`Expected: ${criterion.expectedResult}`);
}


function demonstrateQuality() {
    printSection("REQUIREMENT QUALITY");

    const weak = new Requirement({
        id: "BAD-001",
        title: "Fast system",
        description: "The system should be fast and user-friendly.",
        type: RequirementType.NON_FUNCTIONAL,
        priority: Priority.SHOULD
    });

    const strong = new Requirement({
        id: "GOOD-001",
        title: "Measured response time",
        description:
            "The system shall return the account dashboard within " +
            "2 seconds for at least 95 percent of requests under " +
            "the defined normal operating load.",
        type: RequirementType.NON_FUNCTIONAL,
        priority: Priority.MUST,
        source: "Performance specification",
        rationale:
            "Defines measurable customer-facing performance.",
        acceptanceCriteria: [
            new AcceptanceCriterion(
                "AC-GOOD-001",
                "Given normal operating load, when 1000 dashboard requests are submitted",
                "at least 950 requests complete within 2 seconds"
            )
        ]
    });

    for (const requirement of [weak, strong]) {
        const errors = requirement.validate();

        console.log(`\n${requirement.id}: ${requirement.title}`);

        if (errors.length === 0) {
            console.log("No automated quality issues detected.");
        } else {
            errors.forEach(error => console.log(`- ${error}`));
        }
    }
}


function demonstrateCaseStudy() {
    const { repository, traceability } = buildCaseStudy();
    const analyzer = new RequirementsAnalyzer(
        repository,
        traceability
    );

    printSection("CASE STUDY VALIDATION");

    for (const requirement of repository.requirements.values()) {
        const errors = requirement.validate();
        const state = errors.length === 0 ? "PASS" : "REVIEW";

        console.log(
            `${requirement.id.padEnd(10)} ` +
            `${state.padEnd(7)} ` +
            requirement.title
        );

        errors.forEach(error =>
            console.log(`    - ${error}`)
        );
    }

    printSection("PRIORITY DISTRIBUTION");

    console.table(analyzer.priorityDistribution());

    printSection("QUALITY METRICS");

    console.table(analyzer.qualityMetrics());

    printSection("TRACEABILITY COVERAGE");

    console.table(
        traceability.coverage(repository.requirements.keys())
    );

    printSection("STAKEHOLDER IMPACT");

    console.table(analyzer.stakeholderImpact());

    printSection("SEARCH");

    repository.search("status").forEach(requirement =>
        console.log(`${requirement.id}: ${requirement.title}`)
    );

    printSection("GENERATED DOCUMENT");

    const markdown = generateMarkdownDocument(
        repository,
        traceability
    );

    console.log(
        markdown
            .split("\n")
            .slice(0, 32)
            .join("\n")
    );

    console.log("\n[Document output truncated for console demonstration.]");

    printSection("CHANGE CONTROL");

    const change = new ChangeRequest(
        "CR-001",
        "FR-002",
        "Operations Manager",
        "Display estimated completion time.",
        "Customers need more precise service timing.",
        "Requires an API field, business rule, UI element, and tests."
    );

    repository.changes.set(change.id, change);
    change.approve(repository.get(change.requirementId).version);

    repository.updateRequirement("FR-002", {
        description:
            "The system shall allow customers to view the current " +
            "status, status history, and estimated completion time " +
            "of their submitted requests."
    });

    console.log(
        `${change.id}: ${change.status}, ` +
        `approved version ${change.oldVersion} -> ${change.newVersion}`
    );

    console.log(
        `FR-002 current version: ${repository.get("FR-002").version}`
    );
}


// ---------------------------------------------------------------------------
// 13. Self-tests
// ---------------------------------------------------------------------------

function runSelfTests() {
    const { repository, traceability } = buildCaseStudy();

    if (repository.get("FR-001").title !== "Create a service request") {
        throw new Error("Requirement retrieval test failed.");
    }

    if (!repository.get("FR-001").isVerifiable()) {
        throw new Error("Verifiability test failed.");
    }

    if (repository.search("authentication").length === 0) {
        throw new Error("Search test failed.");
    }

    const coverage =
        traceability.coverage(repository.requirements.keys());

    if (coverage.tests <= 0) {
        throw new Error("Traceability test failed.");
    }

    const story = createUserStory(
        "administrator",
        "review audit records",
        "investigate operational events"
    );

    if (!story.startsWith("As an administrator")) {
        throw new Error("User story test failed.");
    }

    try {
        repository.addRequirement(new Requirement({
            id: "FR-001",
            title: "Duplicate",
            description: "Duplicate requirement test.",
            type: RequirementType.FUNCTIONAL,
            priority: Priority.MUST
        }));

        throw new Error("Duplicate IDs were not rejected.");
    } catch (error) {
        if (!error.message.includes("Duplicate requirement ID")) {
            throw error;
        }
    }

    console.log("All self-tests passed.");
}


// ---------------------------------------------------------------------------
// 14. Main
// ---------------------------------------------------------------------------

function main() {
    console.log(
        "REQUIREMENTS DOCUMENTATION STUDY PROGRAM\n" +
        "=========================================\n" +
        "Executable examples covering requirement documentation from " +
        "fundamentals through change control and traceability."
    );

    demonstrateBasics();
    demonstrateUserStory();
    demonstrateQuality();
    demonstrateCaseStudy();

    printSection("SELF-TESTS");
    runSelfTests();

    printSection("IMPORTANT DISTINCTIONS");

    const distinctions = [
        [
            "Business requirement",
            "Why the organization needs an outcome."
        ],
        [
            "User requirement",
            "What a user needs to accomplish."
        ],
        [
            "Functional requirement",
            "What the system must do."
        ],
        [
            "Non-functional requirement",
            "A measurable quality or constraint."
        ],
        [
            "Acceptance criterion",
            "A condition used to determine satisfaction."
        ],
        [
            "Validation",
            "Whether the requirement itself is suitable."
        ],
        [
            "Verification",
            "Whether implementation satisfies the requirement."
        ],
        [
            "Traceability",
            "Relationships connecting lifecycle artifacts."
        ]
    ];

    distinctions.forEach(([term, meaning]) =>
        console.log(`${term.padEnd(25)}: ${meaning}`)
    );
}


main();
