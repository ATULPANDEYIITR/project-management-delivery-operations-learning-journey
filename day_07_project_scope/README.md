"""
Project Scope: What Is Included and Excluded

A comprehensive, self-contained study script covering project scope from
absolute beginner concepts through advanced project-management applications.

The script demonstrates:
- Scope definitions and terminology
- Product scope versus project scope
- Scope inclusions and exclusions
- Requirements and deliverables
- Scope boundaries
- Assumptions and constraints
- Acceptance criteria
- Work Breakdown Structures
- Scope statements
- Validation and change control
- Scope creep and gold plating
- Dependency and boundary analysis
- Stakeholder perspectives
- Risk implications
- Practical project examples
- Automated scope validation
- Testing and production considerations

Run directly with:
    python project_scope_tutorial.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import difflib


# ============================================================================
# 1. FUNDAMENTAL CONCEPTS
# ============================================================================

def section(title: str) -> None:
    """Print a visually distinct section heading."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


section("1. FUNDAMENTAL CONCEPTS")


PROJECT_SCOPE_DEFINITION = """
Project scope defines the boundaries of a project.

It answers two essential questions:

1. What work, deliverables, features, services, and responsibilities ARE
   included in the project?

2. What work, deliverables, features, services, and responsibilities are
   explicitly NOT included in the project?

A clear scope prevents misunderstanding between stakeholders and provides a
reference point for planning, execution, acceptance, and change control.
"""

print(PROJECT_SCOPE_DEFINITION)


# ============================================================================
# 2. INCLUDED AND EXCLUDED WORK
# ============================================================================

section("2. WHAT IS INCLUDED AND EXCLUDED?")


@dataclass
class ScopeItem:
    """
    Represents one item that belongs either inside or outside project scope.

    Examples:
        - Included: Build user registration functionality.
        - Excluded: Provide 24/7 customer support after project completion.
    """

    name: str
    description: str
    rationale: str = ""


@dataclass
class BasicScope:
    """A simple representation of project scope boundaries."""

    project_name: str
    included: List[ScopeItem] = field(default_factory=list)
    excluded: List[ScopeItem] = field(default_factory=list)

    def add_included(
        self,
        name: str,
        description: str,
        rationale: str = "",
    ) -> None:
        self.included.append(ScopeItem(name, description, rationale))

    def add_excluded(
        self,
        name: str,
        description: str,
        rationale: str = "",
    ) -> None:
        self.excluded.append(ScopeItem(name, description, rationale))

    def print_scope(self) -> None:
        print(f"\nProject: {self.project_name}")

        print("\nINCLUDED:")
        for item in self.included:
            print(f"- {item.name}: {item.description}")
            if item.rationale:
                print(f"  Reason: {item.rationale}")

        print("\nEXCLUDED:")
        for item in self.excluded:
            print(f"- {item.name}: {item.description}")
            if item.rationale:
                print(f"  Reason: {item.rationale}")


website_scope = BasicScope("Company Website Development")

website_scope.add_included(
    "Public Website",
    "Design and develop the public-facing company website.",
)

website_scope.add_included(
    "Contact Form",
    "Implement a form allowing visitors to send inquiries.",
)

website_scope.add_included(
    "Responsive Design",
    "Support desktop, tablet, and mobile layouts.",
)

website_scope.add_excluded(
    "Native Mobile Application",
    "Development of Android or iOS applications.",
    "The approved project is limited to a website.",
)

website_scope.add_excluded(
    "Ongoing Content Creation",
    "Writing new articles after website delivery.",
    "The project covers implementation rather than long-term content operations.",
)

website_scope.print_scope()


# ============================================================================
# 3. PROJECT SCOPE VERSUS PRODUCT SCOPE
# ============================================================================

section("3. PROJECT SCOPE VS PRODUCT SCOPE")


@dataclass
class ScopeComparison:
    category: str
    project_scope: str
    product_scope: str


comparisons = [
    ScopeComparison(
        "Primary Question",
        "What work must the project perform?",
        "What characteristics must the final product have?",
    ),
    ScopeComparison(
        "Focus",
        "Work and activities.",
        "Features and characteristics.",
    ),
    ScopeComparison(
        "Example",
        "Design, develop, test, and deploy a login system.",
        "The login system supports email and password authentication.",
    ),
    ScopeComparison(
        "Measurement",
        "Completion of planned project work.",
        "Compliance with product requirements.",
    ),
]

for comparison in comparisons:
    print(f"\nCategory: {comparison.category}")
    print(f"Project Scope: {comparison.project_scope}")
    print(f"Product Scope: {comparison.product_scope}")


# ============================================================================
# 4. SCOPE BOUNDARIES
# ============================================================================

section("4. UNDERSTANDING SCOPE BOUNDARIES")


class ScopeStatus(Enum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    UNCLEAR = "unclear"


@dataclass
class ScopeBoundary:
    """
    Determines whether a requested activity belongs to the approved scope.

    Exact string matching is intentionally simple here. Real systems often use
    structured requirements, identifiers, workflows, and human approval.
    """

    included_items: Set[str]
    excluded_items: Set[str]

    def classify(self, request: str) -> ScopeStatus:
        normalized_request = request.strip().lower()

        included = {item.lower() for item in self.included_items}
        excluded = {item.lower() for item in self.excluded_items}

        if normalized_request in included:
            return ScopeStatus.INCLUDED

        if normalized_request in excluded:
            return ScopeStatus.EXCLUDED

        return ScopeStatus.UNCLEAR


boundary = ScopeBoundary(
    included_items={
        "website development",
        "responsive design",
        "contact form",
        "basic search engine optimization",
    },
    excluded_items={
        "mobile application",
        "social media management",
        "24 hour customer support",
    },
)

sample_requests = [
    "website development",
    "mobile application",
    "payment gateway integration",
]

for request in sample_requests:
    print(f"Request: {request}")
    print(f"Classification: {boundary.classify(request).value}\n")


# ============================================================================
# 5. WHY EXCLUSIONS ARE IMPORTANT
# ============================================================================

section("5. WHY EXCLUSIONS ARE AS IMPORTANT AS INCLUSIONS")

EXCLUSION_EXPLANATION = """
A project may contain a detailed list of included work and still suffer from
scope disputes if exclusions are unclear.

Example:

Included statement:
    "Develop an e-commerce website."

A stakeholder may reasonably assume this includes:
    - Payment processing
    - Product photography
    - Inventory management
    - Warehouse integration
    - Customer support
    - Marketing automation
    - Mobile applications

The phrase alone does not establish reliable boundaries.

Explicit exclusions reduce ambiguity:

Excluded:
    - Product photography
    - Warehouse management integration
    - Mobile application development
    - Ongoing marketing operations
    - Customer support operations
"""

print(EXCLUSION_EXPLANATION)


# ============================================================================
# 6. REQUIREMENTS, DELIVERABLES, AND ACTIVITIES
# ============================================================================

section("6. REQUIREMENTS, DELIVERABLES, AND ACTIVITIES")


@dataclass
class Requirement:
    identifier: str
    description: str
    acceptance_criteria: List[str]
    priority: str = "Medium"


@dataclass
class Deliverable:
    name: str
    description: str
    requirements: List[str] = field(default_factory=list)


@dataclass
class ProjectActivity:
    name: str
    purpose: str
    related_deliverable: str


requirements = [
    Requirement(
        "REQ-001",
        "Users can create an account using email and password.",
        [
            "Email address is validated.",
            "Password meets configured security requirements.",
            "A successful registration creates a user account.",
        ],
        "High",
    ),
    Requirement(
        "REQ-002",
        "Users can log into the system.",
        [
            "Valid credentials provide access.",
            "Invalid credentials are rejected.",
            "Authentication failures do not expose passwords.",
        ],
        "High",
    ),
]

deliverable = Deliverable(
    "User Authentication Module",
    "A functional account registration and login module.",
    ["REQ-001", "REQ-002"],
)

activities = [
    ProjectActivity(
        "Design Authentication Flow",
        "Define registration and login behavior.",
        "User Authentication Module",
    ),
    ProjectActivity(
        "Implement Authentication Logic",
        "Build required application functionality.",
        "User Authentication Module",
    ),
    ProjectActivity(
        "Test Authentication",
        "Verify requirements and acceptance criteria.",
        "User Authentication Module",
    ),
]

for requirement in requirements:
    print(f"\n{requirement.identifier}: {requirement.description}")
    print(f"Priority: {requirement.priority}")
    print("Acceptance Criteria:")
    for criterion in requirement.acceptance_criteria:
        print(f"- {criterion}")

print(f"\nDeliverable: {deliverable.name}")
print(deliverable.description)

print("\nActivities:")
for activity in activities:
    print(f"- {activity.name}: {activity.purpose}")


# ============================================================================
# 7. IN-SCOPE WORK MUST BE SPECIFIC
# ============================================================================

section("7. SPECIFIC VS AMBIGUOUS SCOPE")


def evaluate_scope_statement(statement: str) -> List[str]:
    """
    Detect common ambiguity patterns.

    This is a teaching example, not a complete natural-language analysis
    system. Ambiguity must often be resolved through stakeholder discussion.
    """

    warnings = []

    vague_words = {
        "modern": "The term 'modern' is subjective.",
        "fast": "The term 'fast' should be replaced with measurable performance criteria.",
        "user-friendly": "The term 'user-friendly' should be supported by measurable usability criteria.",
        "high-quality": "The term 'high-quality' should be defined using measurable standards.",
        "advanced": "The term 'advanced' does not define specific functionality.",
        "appropriate": "The term 'appropriate' may produce different interpretations.",
    }

    normalized = statement.lower()

    for word, warning in vague_words.items():
        if word in normalized:
            warnings.append(warning)

    return warnings


ambiguous_statement = "Build a modern, fast, user-friendly website."

print(f"Statement: {ambiguous_statement}")

warnings = evaluate_scope_statement(ambiguous_statement)

for warning in warnings:
    print(f"Warning: {warning}")

specific_statement = """
Develop a responsive website supporting screen widths from 320 to 1920 pixels,
with the homepage loading its primary content within three seconds under the
defined test environment.
"""

print("\nMore Specific Statement:")
print(specific_statement)


# ============================================================================
# 8. SCOPE STATEMENT
# ============================================================================

section("8. BUILDING A PROJECT SCOPE STATEMENT")


@dataclass
class ScopeStatement:
    project_name: str
    objective: str
    deliverables: List[str]
    inclusions: List[str]
    exclusions: List[str]
    acceptance_criteria: List[str]
    assumptions: List[str]
    constraints: List[str]

    def display(self) -> None:
        print(f"\nPROJECT: {self.project_name}")
        print(f"\nOBJECTIVE:\n{self.objective}")

        categories = [
            ("DELIVERABLES", self.deliverables),
            ("INCLUDED", self.inclusions),
            ("EXCLUDED", self.exclusions),
            ("ACCEPTANCE CRITERIA", self.acceptance_criteria),
            ("ASSUMPTIONS", self.assumptions),
            ("CONSTRAINTS", self.constraints),
        ]

        for heading, items in categories:
            print(f"\n{heading}:")
            for item in items:
                print(f"- {item}")


scope_statement = ScopeStatement(
    project_name="Online Course Platform MVP",
    objective=(
        "Deliver a minimum viable web platform allowing students to register, "
        "purchase approved courses, and access course content."
    ),
    deliverables=[
        "Responsive web application",
        "Student registration and authentication",
        "Course catalog",
        "Payment integration",
        "Student learning dashboard",
    ],
    inclusions=[
        "Web application development",
        "Student authentication",
        "Course browsing",
        "Payment processing integration",
        "Basic administrative course management",
        "Functional testing",
    ],
    exclusions=[
        "Native Android application",
        "Native iOS application",
        "Live video teaching platform",
        "24-hour customer support operations",
        "Marketing campaign management",
        "Creation of course content",
    ],
    acceptance_criteria=[
        "Students can create and access accounts.",
        "Students can browse approved courses.",
        "Students can complete supported payments.",
        "Successful purchasers can access purchased courses.",
        "Critical acceptance tests pass before delivery.",
    ],
    assumptions=[
        "Course content will be provided by the content team.",
        "A payment provider account will be available.",
        "Required product decisions will be provided within agreed timelines.",
    ],
    constraints=[
        "The first release must be completed within the approved schedule.",
        "The project must remain within the approved budget.",
        "Only agreed web technologies may be used.",
    ],
)

scope_statement.display()


# ============================================================================
# 9. ASSUMPTIONS VS CONSTRAINTS
# ============================================================================

section("9. ASSUMPTIONS VS CONSTRAINTS")


@dataclass
class PlanningCondition:
    description: str
    condition_type: str


conditions = [
    PlanningCondition(
        "The client will provide approved branding assets.",
        "Assumption",
    ),
    PlanningCondition(
        "The project budget cannot exceed the approved amount.",
        "Constraint",
    ),
    PlanningCondition(
        "Subject matter experts will be available for review.",
        "Assumption",
    ),
    PlanningCondition(
        "The system must be released before the contractual deadline.",
        "Constraint",
    ),
]

for condition in conditions:
    print(f"{condition.condition_type}: {condition.description}")


# ============================================================================
# 10. WORK BREAKDOWN STRUCTURE
# ============================================================================

section("10. WORK BREAKDOWN STRUCTURE")


@dataclass
class WBSNode:
    """
    A simplified Work Breakdown Structure node.

    A WBS decomposes project scope into smaller, manageable components.
    """

    identifier: str
    name: str
    children: List["WBSNode"] = field(default_factory=list)

    def print_tree(self, level: int = 0) -> None:
        indentation = "    " * level
        print(f"{indentation}{self.identifier} - {self.name}")

        for child in self.children:
            child.print_tree(level + 1)

    def collect_leaf_nodes(self) -> List["WBSNode"]:
        if not self.children:
            return [self]

        leaves = []

        for child in self.children:
            leaves.extend(child.collect_leaf_nodes())

        return leaves


course_platform_wbs = WBSNode(
    "1.0",
    "Online Course Platform",
    children=[
        WBSNode(
            "1.1",
            "User Management",
            children=[
                WBSNode("1.1.1", "Registration"),
                WBSNode("1.1.2", "Login"),
                WBSNode("1.1.3", "Password Security"),
            ],
        ),
        WBSNode(
            "1.2",
            "Course Management",
            children=[
                WBSNode("1.2.1", "Course Catalog"),
                WBSNode("1.2.2", "Course Details"),
                WBSNode("1.2.3", "Course Access"),
            ],
        ),
        WBSNode(
            "1.3",
            "Payments",
            children=[
                WBSNode("1.3.1", "Payment Provider Integration"),
                WBSNode("1.3.2", "Payment Confirmation"),
            ],
        ),
        WBSNode(
            "1.4",
            "Testing",
            children=[
                WBSNode("1.4.1", "Functional Testing"),
                WBSNode("1.4.2", "Acceptance Testing"),
            ],
        ),
    ],
)

print("WBS Structure:")
course_platform_wbs.print_tree()

print("\nLowest-Level Work Components:")
for node in course_platform_wbs.collect_leaf_nodes():
    print(f"- {node.identifier}: {node.name}")


# ============================================================================
# 11. THE 100 PERCENT PRINCIPLE
# ============================================================================

section("11. THE 100 PERCENT PRINCIPLE")

PRINCIPLE = """
The 100 Percent Principle states that the Work Breakdown Structure should
represent 100 percent of the approved project scope.

This has two important implications:

1. Required scope should not be missing.
2. Unapproved work should not be included.

If a team performs work outside the approved WBS without authorization, the
team may be performing scope that has not been formally approved.
"""

print(PRINCIPLE)


def compare_scope_to_wbs(
    approved_scope: Set[str],
    planned_work: Set[str],
) -> Tuple[Set[str], Set[str]]:
    """
    Return:
        missing_work: approved scope not represented in planned work
        extra_work: planned work not represented in approved scope
    """

    missing_work = approved_scope - planned_work
    extra_work = planned_work - approved_scope

    return missing_work, extra_work


approved_scope = {
    "registration",
    "login",
    "course catalog",
    "payment integration",
    "testing",
}

planned_work = {
    "registration",
    "login",
    "course catalog",
    "payment integration",
    "testing",
    "mobile application prototype",
}

missing, extra = compare_scope_to_wbs(approved_scope, planned_work)

print("Missing Approved Work:", missing)
print("Potential Unapproved Work:", extra)


# ============================================================================
# 12. SCOPE BASELINE
# ============================================================================

section("12. SCOPE BASELINE")

SCOPE_BASELINE = """
A scope baseline is the approved reference used to evaluate whether project
work and deliverables remain aligned with authorized scope.

A practical scope baseline commonly includes:

- Approved scope statement
- Approved requirements
- Work Breakdown Structure
- WBS dictionary or detailed work descriptions

The baseline should be controlled. Once approved, changes should be evaluated
rather than silently incorporated.
"""

print(SCOPE_BASELINE)


# ============================================================================
# 13. INCLUSIONS, EXCLUSIONS, AND DEPENDENCIES
# ============================================================================

section("13. DEPENDENCY ANALYSIS")


@dataclass
class ScopedFeature:
    name: str
    included: bool
    dependencies: List[str] = field(default_factory=list)


features = [
    ScopedFeature(
        "Student Dashboard",
        True,
        ["Authentication", "Course Access"],
    ),
    ScopedFeature(
        "Course Access",
        True,
        ["Authentication", "Payment Confirmation"],
    ),
    ScopedFeature(
        "Payment Confirmation",
        True,
        ["Payment Provider"],
    ),
    ScopedFeature(
        "Payment Provider",
        False,
        [],
    ),
]


def validate_dependencies(features: List[ScopedFeature]) -> List[str]:
    """
    Detect included features that depend on excluded features.

    This is a critical scope-design problem because an inclusion may be
    impossible to deliver if a required dependency is excluded.
    """

    status = {
        feature.name.lower(): feature.included
        for feature in features
    }

    problems = []

    for feature in features:
        if not feature.included:
            continue

        for dependency in feature.dependencies:
            dependency_status = status.get(dependency.lower())

            if dependency_status is False:
                problems.append(
                    f"'{feature.name}' is included but depends on excluded "
                    f"component '{dependency}'."
                )

            elif dependency_status is None:
                problems.append(
                    f"'{feature.name}' depends on '{dependency}', but the "
                    "dependency is not defined in the scope model."
                )

    return problems


dependency_problems = validate_dependencies(features)

for problem in dependency_problems:
    print(f"Dependency Problem: {problem}")


# ============================================================================
# 14. SCOPE CREEP
# ============================================================================

section("14. SCOPE CREEP")


@dataclass
class ScopeRequest:
    request_id: str
    description: str
    requested_by: str
    approved: bool = False


class ScopeManager:
    """
    Maintains approved scope and evaluates new requests.

    Scope creep occurs when requirements or work expand without appropriate
    authorization or adjustment of project constraints.
    """

    def __init__(self, approved_items: Optional[Set[str]] = None):
        self.approved_items = approved_items or set()
        self.change_log: List[ScopeRequest] = []

    def is_in_scope(self, item: str) -> bool:
        return item.lower() in {
            approved.lower()
            for approved in self.approved_items
        }

    def request_change(self, request: ScopeRequest) -> None:
        self.change_log.append(request)

    def approve_change(self, request_id: str) -> bool:
        for request in self.change_log:
            if request.request_id == request_id:
                request.approved = True
                self.approved_items.add(request.description)
                return True

        return False


scope_manager = ScopeManager(
    {
        "Student registration",
        "Student login",
        "Course catalog",
    }
)

change_request = ScopeRequest(
    request_id="CR-001",
    description="Gamification system with achievement badges",
    requested_by="Marketing Team",
)

scope_manager.request_change(change_request)

print(
    "Before Approval:",
    scope_manager.is_in_scope(
        "Gamification system with achievement badges"
    ),
)

scope_manager.approve_change("CR-001")

print(
    "After Approval:",
    scope_manager.is_in_scope(
        "Gamification system with achievement badges"
    ),
)


# ============================================================================
# 15. SCOPE CREEP VS APPROVED SCOPE CHANGE
# ============================================================================

section("15. SCOPE CREEP VS APPROVED SCOPE CHANGE")

COMPARISON = """
Scope Creep:
    Work expands without appropriate evaluation or authorization.

Approved Scope Change:
    A proposed change is identified, analyzed, approved, documented, and
    incorporated into relevant plans and baselines.

Not every scope expansion is scope creep.

A project may legitimately change when business conditions, regulations,
customer requirements, technology, or strategic priorities change.
The distinction is controlled authorization.
"""

print(COMPARISON)


# ============================================================================
# 16. GOLD PLATING
# ============================================================================

section("16. GOLD PLATING")

GOLD_PLATING = """
Gold plating occurs when project teams add features or functionality that were
not requested or approved.

Example:

Requirement:
    "Users can download a report as PDF."

Gold plating:
    The team also adds:
    - Interactive dashboards
    - Spreadsheet export
    - Automated email reports
    - Custom report themes

These additions may appear valuable, but they can increase:
    - Cost
    - Schedule duration
    - Complexity
    - Testing requirements
    - Maintenance requirements
    - Security exposure

Delivering unapproved features is not necessarily good scope management.
"""

print(GOLD_PLATING)


# ============================================================================
# 17. ACCEPTANCE CRITERIA
# ============================================================================

section("17. ACCEPTANCE CRITERIA")


@dataclass
class AcceptanceTest:
    name: str
    expected_result: str
    actual_result: str

    def passed(self) -> bool:
        return self.expected_result == self.actual_result


acceptance_tests = [
    AcceptanceTest(
        "Valid registration",
        "Account created",
        "Account created",
    ),
    AcceptanceTest(
        "Invalid email",
        "Registration rejected",
        "Registration rejected",
    ),
    AcceptanceTest(
        "Weak password",
        "Registration rejected",
        "Account created",
    ),
]

for test in acceptance_tests:
    result = "PASS" if test.passed() else "FAIL"

    print(f"{test.name}: {result}")
    print(f"Expected: {test.expected_result}")
    print(f"Actual:   {test.actual_result}\n")


# ============================================================================
# 18. SCOPE VALIDATION
# ============================================================================

section("18. SCOPE VALIDATION")


@dataclass
class DeliverableReview:
    deliverable_name: str
    requirements: Dict[str, bool]

    def is_accepted(self) -> bool:
        return all(self.requirements.values())

    def failed_requirements(self) -> List[str]:
        return [
            requirement
            for requirement, passed in self.requirements.items()
            if not passed
        ]


review = DeliverableReview(
    "Authentication Module",
    {
        "User registration works": True,
        "Login works": True,
        "Invalid credentials are rejected": True,
        "Password policy is enforced": False,
    },
)

print("Deliverable:", review.deliverable_name)
print("Accepted:", review.is_accepted())
print("Failed Requirements:", review.failed_requirements())


# ============================================================================
# 19. SCOPE CHANGE IMPACT ANALYSIS
# ============================================================================

section("19. SCOPE CHANGE IMPACT ANALYSIS")


@dataclass
class ChangeImpact:
    scope_change: str
    cost_change: float
    schedule_change_days: int
    risk_change: str
    resource_change: str
    recommendation: str


def analyze_change(
    description: str,
    estimated_cost: float,
    estimated_days: int,
    risk_level: str,
    resource_requirement: str,
    budget_remaining: float,
    schedule_remaining_days: int,
) -> ChangeImpact:
    """
    A simplified impact analysis.

    Real projects may also consider contracts, quality, procurement,
    architecture, operations, compliance, security, and stakeholder impacts.
    """

    if estimated_cost > budget_remaining:
        recommendation = "Reject or re-plan because budget impact exceeds available budget."

    elif estimated_days > schedule_remaining_days:
        recommendation = "Reject, defer, or renegotiate the schedule."

    elif risk_level.lower() == "high":
        recommendation = "Perform detailed risk analysis before approval."

    else:
        recommendation = "Suitable for formal approval if stakeholders agree."

    return ChangeImpact(
        scope_change=description,
        cost_change=estimated_cost,
        schedule_change_days=estimated_days,
        risk_change=risk_level,
        resource_change=resource_requirement,
        recommendation=recommendation,
    )


impact = analyze_change(
    description="Add multilingual user interface support",
    estimated_cost=50000,
    estimated_days=15,
    risk_level="Medium",
    resource_requirement="One additional localization specialist",
    budget_remaining=100000,
    schedule_remaining_days=20,
)

print("Change:", impact.scope_change)
print("Cost Impact:", impact.cost_change)
print("Schedule Impact:", impact.schedule_change_days, "days")
print("Risk:", impact.risk_change)
print("Resources:", impact.resource_change)
print("Recommendation:", impact.recommendation)


# ============================================================================
# 20. SCOPE PRIORITIZATION
# ============================================================================

section("20. PRIORITIZING SCOPE")


class MoSCoWPriority(Enum):
    MUST = "Must Have"
    SHOULD = "Should Have"
    COULD = "Could Have"
    WONT = "Will Not Have in This Release"


@dataclass
class PrioritizedRequirement:
    identifier: str
    description: str
    priority: MoSCoWPriority


prioritized_requirements = [
    PrioritizedRequirement(
        "REQ-001",
        "Users can register.",
        MoSCoWPriority.MUST,
    ),
    PrioritizedRequirement(
        "REQ-002",
        "Users can purchase courses.",
        MoSCoWPriority.MUST,
    ),
    PrioritizedRequirement(
        "REQ-003",
        "Users can save favorite courses.",
        MoSCoWPriority.SHOULD,
    ),
    PrioritizedRequirement(
        "REQ-004",
        "Users can customize interface themes.",
        MoSCoWPriority.COULD,
    ),
    PrioritizedRequirement(
        "REQ-005",
        "Native mobile applications.",
        MoSCoWPriority.WONT,
    ),
]

for requirement in prioritized_requirements:
    print(
        f"{requirement.identifier}: "
        f"{requirement.priority.value} - "
        f"{requirement.description}"
    )


# ============================================================================
# 21. STAKEHOLDER SCOPE PERSPECTIVES
# ============================================================================

section("21. STAKEHOLDER PERSPECTIVES")


@dataclass
class Stakeholder:
    name: str
    role: str
    scope_interest: str


stakeholders = [
    Stakeholder(
        "Sponsor",
        "Project Sponsor",
        "Business value, budget, and strategic alignment.",
    ),
    Stakeholder(
        "Customer",
        "End Customer",
        "Required features and expected outcomes.",
    ),
    Stakeholder(
        "Project Manager",
        "Project Management",
        "Clear boundaries, planning, and controlled execution.",
    ),
    Stakeholder(
        "Development Team",
        "Implementation",
        "Technical requirements and implementation boundaries.",
    ),
    Stakeholder(
        "Operations Team",
        "Operations",
        "Deployment, maintainability, monitoring, and support implications.",
    ),
]

for stakeholder in stakeholders:
    print(
        f"{stakeholder.name} ({stakeholder.role}): "
        f"{stakeholder.scope_interest}"
    )


# ============================================================================
# 22. FUZZY MATCHING FOR UNCLEAR REQUESTS
# ============================================================================

section("22. IDENTIFYING POSSIBLE RELATED SCOPE ITEMS")


class ScopeSimilarityChecker:
    """
    Uses Python's standard library to find scope items similar to a request.

    This does not replace stakeholder judgment. It is useful for identifying
    potential relationships when terminology differs.
    """

    def __init__(self, scope_items: List[str]):
        self.scope_items = scope_items

    def find_similar(
        self,
        request: str,
        cutoff: float = 0.45,
    ) -> List[str]:
        return difflib.get_close_matches(
            request,
            self.scope_items,
            n=5,
            cutoff=cutoff,
        )


checker = ScopeSimilarityChecker(
    [
        "User registration",
        "User login",
        "Course catalog",
        "Payment processing",
        "Course access",
    ]
)

request = "User account signup"

similar_items = checker.find_similar(request)

print("Request:", request)
print("Potentially Related Scope Items:", similar_items)


# ============================================================================
# 23. EXCLUSIONS DO NOT ALWAYS MEAN IGNORING A TOPIC
# ============================================================================

section("23. SUBTLE BOUNDARY: EXCLUDED RESPONSIBILITY VS DEPENDENCY")

EXCLUDED_DEPENDENCY = """
An activity can be excluded from project responsibility while still affecting
project execution.

Example:

The project excludes:
    "Creation of course content."

The project may still require:
    - Course content to be available before testing.
    - Content owners to approve uploaded materials.
    - Content availability to support launch.

Therefore, excluded work may still represent:
    - An external dependency
    - An assumption
    - A stakeholder responsibility
    - A project risk

"Excluded from our responsibility" does not necessarily mean "irrelevant to
project success."
"""

print(EXCLUDED_DEPENDENCY)


# ============================================================================
# 24. RESPONSIBILITY BOUNDARIES
# ============================================================================

section("24. RESPONSIBILITY BOUNDARIES")


class Responsibility(Enum):
    RESPONSIBLE = "Responsible"
    ACCOUNTABLE = "Accountable"
    CONSULTED = "Consulted"
    INFORMED = "Informed"


@dataclass
class ResponsibilityAssignment:
    activity: str
    stakeholder: str
    responsibility: Responsibility


assignments = [
    ResponsibilityAssignment(
        "Develop website",
        "Development Team",
        Responsibility.RESPONSIBLE,
    ),
    ResponsibilityAssignment(
        "Approve scope",
        "Project Sponsor",
        Responsibility.ACCOUNTABLE,
    ),
    ResponsibilityAssignment(
        "Review branding",
        "Marketing Team",
        Responsibility.CONSULTED,
    ),
    ResponsibilityAssignment(
        "Receive release update",
        "Operations Team",
        Responsibility.INFORMED,
    ),
]

for assignment in assignments:
    print(
        f"{assignment.activity} | "
        f"{assignment.stakeholder} | "
        f"{assignment.responsibility.value}"
    )


# ============================================================================
# 25. COMMON SCOPE MISTAKES
# ============================================================================

section("25. COMMON SCOPE MISTAKES")

COMMON_MISTAKES = [
    (
        "Vague inclusions",
        "Terms such as 'fast' or 'professional' are used without measurable definitions.",
    ),
    (
        "Missing exclusions",
        "Stakeholders assume work is included because it was never explicitly excluded.",
    ),
    (
        "Confusing deliverables and activities",
        "Teams describe work performed instead of defining expected outputs.",
    ),
    (
        "Ignoring dependencies",
        "Included features depend on excluded or undefined components.",
    ),
    (
        "Accepting informal changes",
        "New requirements are implemented without evaluating cost or schedule impact.",
    ),
    (
        "Gold plating",
        "Teams add unapproved functionality because they believe it will be useful.",
    ),
    (
        "Missing acceptance criteria",
        "Stakeholders disagree because completion was never objectively defined.",
    ),
    (
        "Uncontrolled terminology",
        "Different stakeholders use the same term with different meanings.",
    ),
]

for mistake, explanation in COMMON_MISTAKES:
    print(f"\nMistake: {mistake}")
    print(f"Explanation: {explanation}")


# ============================================================================
# 26. SCOPE VALIDATION RULES
# ============================================================================

section("26. AUTOMATED SCOPE QUALITY CHECKING")


@dataclass
class ScopeQualityReport:
    errors: List[str]
    warnings: List[str]

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0


def validate_scope_quality(
    scope: ScopeStatement,
) -> ScopeQualityReport:
    """
    Perform basic automated quality checks.

    Human review remains necessary because software cannot fully determine
    whether scope statements accurately reflect business intent.
    """

    errors = []
    warnings = []

    if not scope.objective.strip():
        errors.append("Project objective is missing.")

    if not scope.deliverables:
        errors.append("No deliverables are defined.")

    if not scope.inclusions:
        errors.append("No included work is defined.")

    if not scope.exclusions:
        warnings.append(
            "No exclusions are defined. Scope boundaries may be unclear."
        )

    if not scope.acceptance_criteria:
        warnings.append(
            "No acceptance criteria are defined."
        )

    normalized_inclusions = {
        item.strip().lower()
        for item in scope.inclusions
    }

    normalized_exclusions = {
        item.strip().lower()
        for item in scope.exclusions
    }

    overlap = normalized_inclusions & normalized_exclusions

    if overlap:
        errors.append(
            "Items appear in both included and excluded scope: "
            + ", ".join(sorted(overlap))
        )

    return ScopeQualityReport(
        errors=errors,
        warnings=warnings,
    )


quality_report = validate_scope_quality(scope_statement)

print("Scope Valid:", quality_report.valid)

print("\nErrors:")
for error in quality_report.errors:
    print("-", error)

print("\nWarnings:")
for warning in quality_report.warnings:
    print("-", warning)


# ============================================================================
# 27. EDGE CASE: PARTIALLY INCLUDED FEATURES
# ============================================================================

section("27. PARTIALLY INCLUDED FEATURES")

PARTIAL_SCOPE = """
Scope is not always binary.

A feature may be partially included.

Example:

Included:
    "Payment processing through the approved provider."

Excluded:
    "Support for additional payment providers."

Included:
    "English user interface."

Excluded:
    "Multilingual localization."

The broader category exists in scope, but its boundary is limited.

The scope statement should describe the exact boundary rather than merely using
a broad category name such as "payments" or "internationalization."
"""

print(PARTIAL_SCOPE)


@dataclass
class FeatureBoundary:
    feature: str
    included_capabilities: Set[str]
    excluded_capabilities: Set[str]

    def capability_status(
        self,
        capability: str,
    ) -> ScopeStatus:
        normalized = capability.lower()

        if normalized in {
            item.lower()
            for item in self.included_capabilities
        }:
            return ScopeStatus.INCLUDED

        if normalized in {
            item.lower()
            for item in self.excluded_capabilities
        }:
            return ScopeStatus.EXCLUDED

        return ScopeStatus.UNCLEAR


payment_boundary = FeatureBoundary(
    "Payment Processing",
    included_capabilities={
        "Approved payment provider",
        "Payment confirmation",
    },
    excluded_capabilities={
        "Additional payment providers",
        "Cryptocurrency payments",
        "Installment financing",
    },
)

for capability in [
    "Approved payment provider",
    "Cryptocurrency payments",
    "International bank transfer",
]:
    print(
        capability,
        "->",
        payment_boundary.capability_status(capability).value,
    )


# ============================================================================
# 28. SCOPE AND RISK
# ============================================================================

section("28. SCOPE AND RISK")


@dataclass
class ScopeRisk:
    description: str
    probability: int
    impact: int

    def score(self) -> int:
        return self.probability * self.impact

    def level(self) -> str:
        score = self.score()

        if score >= 15:
            return "High"

        if score >= 6:
            return "Medium"

        return "Low"


scope_risks = [
    ScopeRisk(
        "Stakeholders interpret excluded mobile applications as future included work.",
        4,
        4,
    ),
    ScopeRisk(
        "External payment provider is unavailable during integration testing.",
        3,
        5,
    ),
    ScopeRisk(
        "Minor terminology differences cause requirement ambiguity.",
        2,
        2,
    ),
]

for risk in scope_risks:
    print("\nRisk:", risk.description)
    print("Score:", risk.score())
    print("Level:", risk.level())


# ============================================================================
# 29. SCOPE AND AGILE DELIVERY
# ============================================================================

section("29. SCOPE IN PREDICTIVE AND AGILE ENVIRONMENTS")

AGILE_SCOPE = """
Predictive projects often establish detailed scope earlier and manage changes
against an approved baseline.

Agile projects may intentionally allow detailed requirements to evolve. This
does not mean that project boundaries do not exist.

Agile scope still requires clarity about:
    - Product vision
    - Release boundaries
    - Priorities
    - Budget constraints
    - Time constraints
    - Definition of Done
    - Acceptance criteria

A backlog can evolve while the project or product still operates within
strategic and delivery boundaries.

Agility is controlled adaptation, not unlimited uncontrolled expansion.
"""

print(AGILE_SCOPE)


@dataclass
class ProductBacklogItem:
    identifier: str
    description: str
    story_points: int
    priority: int
    approved: bool = True


backlog = [
    ProductBacklogItem(
        "PB-001",
        "Student registration",
        3,
        1,
    ),
    ProductBacklogItem(
        "PB-002",
        "Course purchase",
        5,
        2,
    ),
    ProductBacklogItem(
        "PB-003",
        "Favorite courses",
        2,
        3,
    ),
    ProductBacklogItem(
        "PB-004",
        "Virtual reality classroom",
        21,
        4,
        approved=False,
    ),
]

release_capacity = 10

selected_items = []
used_capacity = 0

for item in sorted(backlog, key=lambda item: item.priority):
    if (
        item.approved
        and used_capacity + item.story_points <= release_capacity
    ):
        selected_items.append(item)
        used_capacity += item.story_points

print("Release Capacity:", release_capacity)
print("Used Capacity:", used_capacity)
print("Selected Scope:")

for item in selected_items:
    print(f"- {item.identifier}: {item.description}")


# ============================================================================
# 30. SCOPE AND SECURITY
# ============================================================================

section("30. SECURITY AS A SCOPE CONSIDERATION")

SECURITY_SCOPE = """
Security can be both a project requirement and a scope boundary.

Poor scope definition may create dangerous ambiguity.

Example:

Weak statement:
    "Make the application secure."

More specific scope:
    - Passwords must not be stored in plaintext.
    - Sensitive communications must use approved encrypted transport.
    - Access control must restrict administrative functions.
    - Authentication failures must not reveal sensitive information.

Security requirements should be sufficiently specific to support design,
implementation, testing, acceptance, and accountability.
"""

print(SECURITY_SCOPE)


def validate_password_security(password: str) -> Tuple[bool, List[str]]:
    """
    Demonstrates a simple requirement-oriented validation approach.

    Production password systems should also follow organizational security
    policies and use established password hashing mechanisms.
    """

    errors = []

    if len(password) < 12:
        errors.append("Password must contain at least 12 characters.")

    if not any(character.isupper() for character in password):
        errors.append("Password must contain an uppercase character.")

    if not any(character.islower() for character in password):
        errors.append("Password must contain a lowercase character.")

    if not any(character.isdigit() for character in password):
        errors.append("Password must contain a digit.")

    return len(errors) == 0, errors


for password in [
    "short",
    "LongPassword",
    "LongPassword123",
]:
    valid, password_errors = validate_password_security(password)

    print(f"\nPassword: {password}")
    print("Valid:", valid)

    for error in password_errors:
        print("-", error)


# ============================================================================
# 31. PERFORMANCE AS A SCOPE REQUIREMENT
# ============================================================================

section("31. PERFORMANCE BOUNDARIES")

PERFORMANCE_SCOPE = """
Performance requirements should define measurable boundaries.

Ambiguous:
    "The application must be fast."

Measurable:
    "Under the defined test environment, 95 percent of approved requests must
     complete within two seconds."

Performance requirements must define their context. A response time without
information about workload, environment, and measurement conditions may still
be ambiguous.
"""

print(PERFORMANCE_SCOPE)


def calculate_percentile(values: List[float], percentile: float) -> float:
    """
    Calculate a simple nearest-rank percentile.

    Edge cases:
    - Empty input raises ValueError.
    - Percentile must be between 0 and 100.
    """

    if not values:
        raise ValueError("Cannot calculate percentile for an empty list.")

    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    ordered = sorted(values)

    if percentile == 0:
        return ordered[0]

    rank = int(
        (percentile / 100) * len(ordered)
    )

    rank = max(1, rank)

    return ordered[rank - 1]


response_times = [
    0.8,
    0.9,
    1.0,
    1.1,
    1.2,
    1.4,
    1.6,
    1.9,
    2.0,
    2.5,
]

p95 = calculate_percentile(response_times, 95)

print("95th Percentile Response Time:", p95)
print("Meets Two-Second Requirement:", p95 <= 2.0)


# ============================================================================
# 32. SCOPE TRACEABILITY
# ============================================================================

section("32. REQUIREMENTS TRACEABILITY")


@dataclass
class TraceabilityRecord:
    requirement_id: str
    requirement: str
    deliverable: str
    test: str
    status: str


traceability_matrix = [
    TraceabilityRecord(
        "REQ-001",
        "User registration",
        "Authentication Module",
        "Registration Acceptance Test",
        "Implemented",
    ),
    TraceabilityRecord(
        "REQ-002",
        "User login",
        "Authentication Module",
        "Login Acceptance Test",
        "Implemented",
    ),
    TraceabilityRecord(
        "REQ-003",
        "Course purchase",
        "Payment Module",
        "Payment Acceptance Test",
        "In Progress",
    ),
]

for record in traceability_matrix:
    print(
        f"{record.requirement_id} | "
        f"{record.requirement} | "
        f"{record.deliverable} | "
        f"{record.test} | "
        f"{record.status}"
    )


# ============================================================================
# 33. DETECTING UNTRACED REQUIREMENTS
# ============================================================================

section("33. TRACEABILITY VALIDATION")


def find_untraced_requirements(
    approved_requirement_ids: Set[str],
    traceability_records: List[TraceabilityRecord],
) -> Set[str]:
    traced = {
        record.requirement_id
        for record in traceability_records
    }

    return approved_requirement_ids - traced


approved_requirement_ids = {
    "REQ-001",
    "REQ-002",
    "REQ-003",
    "REQ-004",
}

untraced = find_untraced_requirements(
    approved_requirement_ids,
    traceability_matrix,
)

print("Untraced Requirements:", untraced)


# ============================================================================
# 34. REAL-WORLD EXAMPLE: BUILDING A PROJECT SCOPE MODEL
# ============================================================================

section("34. COMPLETE PRACTICAL EXAMPLE")


@dataclass
class ProjectScopeModel:
    name: str
    objective: str
    included: Set[str]
    excluded: Set[str]
    assumptions: Set[str]
    constraints: Set[str]
    acceptance_criteria: Set[str]

    def classify_work(self, work_item: str) -> ScopeStatus:
        normalized = work_item.strip().lower()

        included = {
            item.lower()
            for item in self.included
        }

        excluded = {
            item.lower()
            for item in self.excluded
        }

        if normalized in included:
            return ScopeStatus.INCLUDED

        if normalized in excluded:
            return ScopeStatus.EXCLUDED

        return ScopeStatus.UNCLEAR


inventory_project = ProjectScopeModel(
    name="Small Business Inventory Management System",
    objective=(
        "Develop a web-based inventory system for tracking products, "
        "stock quantities, and stock movements."
    ),
    included={
        "User authentication",
        "Product management",
        "Stock quantity tracking",
        "Stock movement recording",
        "Inventory reports",
        "Web application deployment",
    },
    excluded={
        "Native mobile application",
        "Warehouse robotics",
        "Accounting software replacement",
        "Physical barcode hardware procurement",
        "24 hour support center",
    },
    assumptions={
        "The customer will provide initial product data.",
        "Existing infrastructure can host the application.",
    },
    constraints={
        "Maximum project duration is six months.",
        "The project must use the approved technology stack.",
    },
    acceptance_criteria={
        "Authorized users can create products.",
        "Authorized users can record stock movements.",
        "Stock balances are updated correctly.",
        "Approved reports can be generated.",
    },
)

print("Project:", inventory_project.name)
print("Objective:", inventory_project.objective)

work_requests = [
    "Product management",
    "Native mobile application",
    "Machine learning demand forecasting",
    "Inventory reports",
]

for work in work_requests:
    print(
        f"{work}: "
        f"{inventory_project.classify_work(work).value}"
    )


# ============================================================================
# 35. ADVANCED IMPLEMENTATION: SCOPE CHANGE WORKFLOW
# ============================================================================

section("35. ADVANCED SCOPE CHANGE WORKFLOW")


class ChangeState(Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IMPLEMENTED = "Implemented"


@dataclass
class ManagedChangeRequest:
    identifier: str
    description: str
    requester: str
    state: ChangeState = ChangeState.SUBMITTED
    impact_notes: List[str] = field(default_factory=list)


class ChangeControlBoard:
    """
    Simplified change-control workflow.

    Valid transitions protect against logically inconsistent states.
    """

    allowed_transitions = {
        ChangeState.SUBMITTED: {
            ChangeState.UNDER_REVIEW,
        },
        ChangeState.UNDER_REVIEW: {
            ChangeState.APPROVED,
            ChangeState.REJECTED,
        },
        ChangeState.APPROVED: {
            ChangeState.IMPLEMENTED,
        },
        ChangeState.REJECTED: set(),
        ChangeState.IMPLEMENTED: set(),
    }

    def transition(
        self,
        request: ManagedChangeRequest,
        new_state: ChangeState,
    ) -> None:
        allowed = self.allowed_transitions[request.state]

        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition from {request.state.value} "
                f"to {new_state.value}."
            )

        request.state = new_state


change_board = ChangeControlBoard()

managed_change = ManagedChangeRequest(
    "CR-100",
    "Add downloadable inventory reports in spreadsheet format.",
    "Operations Manager",
)

print("Initial State:", managed_change.state.value)

change_board.transition(
    managed_change,
    ChangeState.UNDER_REVIEW,
)

managed_change.impact_notes.extend(
    [
        "Requires report export development.",
        "Requires additional testing.",
        "Estimated schedule impact: 3 days.",
    ]
)

change_board.transition(
    managed_change,
    ChangeState.APPROVED,
)

change_board.transition(
    managed_change,
    ChangeState.IMPLEMENTED,
)

print("Final State:", managed_change.state.value)


# ============================================================================
# 36. TESTING SCOPE MANAGEMENT LOGIC
# ============================================================================

section("36. TESTING SCOPE MANAGEMENT LOGIC")


def test_scope_boundary() -> None:
    boundary = ScopeBoundary(
        included_items={"A"},
        excluded_items={"B"},
    )

    assert boundary.classify("A") == ScopeStatus.INCLUDED
    assert boundary.classify("B") == ScopeStatus.EXCLUDED
    assert boundary.classify("C") == ScopeStatus.UNCLEAR


def test_scope_overlap_detection() -> None:
    scope = ScopeStatement(
        project_name="Test Project",
        objective="Test scope validation.",
        deliverables=["Deliverable"],
        inclusions=["Feature A"],
        exclusions=["Feature A"],
        acceptance_criteria=["Feature works"],
        assumptions=[],
        constraints=[],
    )

    report = validate_scope_quality(scope)

    assert report.valid is False
    assert len(report.errors) == 1


def test_dependency_validation() -> None:
    features = [
        ScopedFeature(
            "Feature A",
            True,
            ["Feature B"],
        ),
        ScopedFeature(
            "Feature B",
            False,
        ),
    ]

    problems = validate_dependencies(features)

    assert len(problems) == 1


def test_change_workflow() -> None:
    board = ChangeControlBoard()

    request = ManagedChangeRequest(
        "TEST-001",
        "Test Change",
        "Tester",
    )

    board.transition(
        request,
        ChangeState.UNDER_REVIEW,
    )

    board.transition(
        request,
        ChangeState.APPROVED,
    )

    assert request.state == ChangeState.APPROVED


tests = [
    test_scope_boundary,
    test_scope_overlap_detection,
    test_dependency_validation,
    test_change_workflow,
]

passed_tests = 0

for test in tests:
    try:
        test()
        print(f"PASS: {test.__name__}")
        passed_tests += 1
    except AssertionError:
        print(f"FAIL: {test.__name__}")

print(f"\nTests Passed: {passed_tests}/{len(tests)}")


# ============================================================================
# 37. PRODUCTION CONSIDERATIONS
# ============================================================================

section("37. PRODUCTION CONSIDERATIONS")

PRODUCTION_CONSIDERATIONS = """
Production scope management requires more than maintaining a list of features.

Important considerations include:

1. Version Control
   Scope documents, requirements, and change records should be versioned.

2. Authorization
   Only authorized stakeholders should approve significant scope changes.

3. Traceability
   Requirements should be traceable to implementation and validation.

4. Auditability
   Important scope decisions should have documented rationale.

5. Operational Boundaries
   The project should clarify what happens after delivery, including ownership,
   maintenance, support, monitoring, and incident responsibilities.

6. Security and Compliance
   Security, privacy, regulatory, and contractual responsibilities must be
   explicitly assigned where relevant.

7. Dependency Management
   External systems and teams may affect delivery even when their work is
   excluded from the project team's responsibilities.

8. Change Discipline
   Informal agreements should not silently alter commitments involving cost,
   schedule, quality, risk, or contractual obligations.
"""

print(PRODUCTION_CONSIDERATIONS)


# ============================================================================
# 38. FINAL PRACTICAL CHECKLIST IMPLEMENTED AS DATA
# ============================================================================

section("38. PROJECT SCOPE QUALITY CHECKLIST")


scope_checklist = {
    "Objective Defined": bool(scope_statement.objective.strip()),
    "Deliverables Defined": bool(scope_statement.deliverables),
    "Inclusions Defined": bool(scope_statement.inclusions),
    "Exclusions Defined": bool(scope_statement.exclusions),
    "Acceptance Criteria Defined": bool(scope_statement.acceptance_criteria),
    "Assumptions Identified": bool(scope_statement.assumptions),
    "Constraints Identified": bool(scope_statement.constraints),
    "No Inclusion/Exclusion Conflict": quality_report.valid,
}

for item, complete in scope_checklist.items():
    status = "COMPLETE" if complete else "REVIEW REQUIRED"
    print(f"{item}: {status}")


# ============================================================================
# 39. KEY DISTINCTIONS
# ============================================================================

section("39. KEY DISTINCTIONS")

DISTINCTIONS = [
    (
        "Included Scope",
        "Work or deliverables the project is authorized to perform or provide.",
    ),
    (
        "Excluded Scope",
        "Work or deliverables explicitly outside project responsibility.",
    ),
    (
        "Assumption",
        "A planning condition believed to be true without complete certainty.",
    ),
    (
        "Constraint",
        "A limitation affecting available choices, such as budget or deadline.",
    ),
    (
        "Requirement",
        "A defined need or condition that a deliverable must satisfy.",
    ),
    (
        "Deliverable",
        "A verifiable output produced by the project.",
    ),
    (
        "Acceptance Criterion",
        "A measurable condition used to determine whether work is acceptable.",
    ),
    (
        "Scope Creep",
        "Uncontrolled expansion of work or requirements.",
    ),
    (
        "Approved Scope Change",
        "Authorized modification evaluated through an appropriate process.",
    ),
    (
        "Gold Plating",
        "Adding unrequested or unapproved functionality.",
    ),
]

for term, definition in DISTINCTIONS:
    print(f"\n{term}:")
    print(definition)


# ============================================================================
# END OF SCRIPT
# ============================================================================
