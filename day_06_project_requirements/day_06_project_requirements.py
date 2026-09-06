"""
PROJECT REQUIREMENTS: UNDERSTANDING PROJECT REQUIREMENTS
========================================================

A self-contained study and demonstration script covering project requirements
from absolute beginner concepts through advanced requirements engineering.

The examples use only Python's standard library.

Run:
    python project_requirements.py

The script is intentionally educational. It demonstrates:
- What project requirements are
- Requirements terminology
- Business, stakeholder, functional, non-functional, technical, regulatory,
  operational, data, interface, and transition requirements
- Requirement sources and elicitation
- Requirement decomposition
- Requirement quality characteristics
- SMART and testable requirements
- Ambiguity, assumptions, constraints, dependencies, risks, and exclusions
- User stories and acceptance criteria
- Use cases
- Requirement prioritization
- MoSCoW, value/effort, and risk-based prioritization
- Traceability
- Requirement validation
- Conflict detection
- Change control and versioning
- Requirement baselines
- Impact analysis
- Coverage analysis
- Simple metrics
- A small requirements repository
- A mini end-to-end requirements analysis example
- Testing requirements against acceptance criteria
- Common failure patterns and edge cases

The code is designed to be read as a tutorial as well as executed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import re
import statistics
from collections import defaultdict


# ============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# ============================================================================

def section(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def subsection(title: str) -> None:
    """Print a smaller subsection heading."""
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def explain(text: str) -> None:
    """Print educational explanatory text."""
    print(text)


def bullet(items: List[str]) -> None:
    """Print a simple bullet list."""
    for item in items:
        print(f"  • {item}")


def demonstrate_basics() -> None:
    section("1. WHAT IS A PROJECT REQUIREMENT?")

    explain(
        "A project requirement is a documented need, capability, condition, "
        "behavior, quality level, or constraint that a project is expected "
        "to satisfy."
    )

    subsection("Requirement versus project objective")
    print("Objective: Reduce customer checkout time.")
    print("Requirement: The checkout service shall complete 95% of valid")
    print("             transactions within 2 seconds.")

    subsection("Requirement versus feature")
    print("Feature: Online password reset")
    print("Requirement: A registered user shall be able to reset a password")
    print("             using a verified email address.")

    subsection("Requirement versus solution")
    print("Need: Users must be able to recover access.")
    print("Possible solution: Email-based password reset.")
    print(
        "The need is a requirement-level concern; the specific implementation "
        "is a design decision unless explicitly constrained by the project."
    )

    subsection("Requirement hierarchy")
    hierarchy = {
        "Business requirement": "Why the organization needs the project.",
        "Stakeholder requirement": "What a stakeholder needs from the outcome.",
        "Solution requirement": "What the system or product must provide.",
        "Functional requirement": "What the solution must do.",
        "Non-functional requirement": "How well or under what quality constraints it must operate.",
        "Transition requirement": "What is needed to move from the current state to the future state.",
    }

    for name, meaning in hierarchy.items():
        print(f"{name}: {meaning}")


# ============================================================================
# 2. REQUIREMENT CLASSIFICATIONS
# ============================================================================

class RequirementType(Enum):
    BUSINESS = "Business"
    STAKEHOLDER = "Stakeholder"
    FUNCTIONAL = "Functional"
    NON_FUNCTIONAL = "Non-functional"
    TECHNICAL = "Technical"
    DATA = "Data"
    INTERFACE = "Interface"
    SECURITY = "Security"
    REGULATORY = "Regulatory"
    OPERATIONAL = "Operational"
    TRANSITION = "Transition"
    CONSTRAINT = "Constraint"


@dataclass
class Requirement:
    """
    Basic representation of a project requirement.

    A requirement has an identifier so it can be traced through planning,
    implementation, testing, approval, and change management.
    """

    requirement_id: str
    title: str
    description: str
    requirement_type: RequirementType
    stakeholder: str
    priority: str = "Should"
    source: str = "Stakeholder interview"
    acceptance_criteria: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    status: str = "Draft"
    version: int = 1

    def is_testable(self) -> bool:
        """
        A simplified testability check.

        This is not a complete natural-language requirements validator.
        It checks for measurable or verifiable language and discourages
        vague terms.
        """
        vague_terms = {
            "fast",
            "easy",
            "simple",
            "user-friendly",
            "efficient",
            "appropriate",
            "reasonable",
            "quick",
            "modern",
            "good",
            "robust",
        }

        text = f"{self.title} {self.description}".lower()

        if any(term in text for term in vague_terms):
            return False

        measurable_indicators = [
            r"\b\d+\s*(second|seconds|ms|milliseconds)\b",
            r"\b\d+\s*%\b",
            r"\bwithin\b",
            r"\bshall\b",
            r"\bmust\b",
            r"\bno more than\b",
            r"\bat least\b",
            r"\bmaximum\b",
            r"\bminimum\b",
            r"\bbetween\b",
        ]

        return any(re.search(pattern, text) for pattern in measurable_indicators)

    def has_acceptance_criteria(self) -> bool:
        return len(self.acceptance_criteria) > 0

    def quality_score(self) -> int:
        """
        Very small educational quality model.

        Higher scores indicate stronger requirement definition.
        """
        score = 0

        if self.requirement_id:
            score += 1
        if self.title:
            score += 1
        if self.description:
            score += 1
        if self.stakeholder:
            score += 1
        if self.source:
            score += 1
        if self.priority:
            score += 1
        if self.has_acceptance_criteria():
            score += 2
        if self.is_testable():
            score += 2

        return score


def demonstrate_requirement_types() -> None:
    section("2. TYPES OF PROJECT REQUIREMENTS")

    examples = [
        Requirement(
            "BR-001",
            "Reduce checkout abandonment",
            "The project shall reduce checkout abandonment by at least 10%.",
            RequirementType.BUSINESS,
            "Business Sponsor",
            "Must",
        ),
        Requirement(
            "FR-001",
            "Create order",
            "The system shall create an order after successful payment authorization.",
            RequirementType.FUNCTIONAL,
            "Customer",
            "Must",
        ),
        Requirement(
            "NFR-001",
            "Checkout response time",
            "95% of checkout requests shall receive a response within 2 seconds.",
            RequirementType.NON_FUNCTIONAL,
            "Operations",
            "Must",
        ),
        Requirement(
            "SEC-001",
            "Protect payment data",
            "Payment information shall not be stored in application logs.",
            RequirementType.SECURITY,
            "Security Team",
            "Must",
        ),
        Requirement(
            "DATA-001",
            "Order retention",
            "Order records shall be retained for at least 7 years.",
            RequirementType.DATA,
            "Finance",
            "Must",
        ),
        Requirement(
            "REG-001",
            "Regulatory compliance",
            "The solution shall comply with applicable payment regulations.",
            RequirementType.REGULATORY,
            "Compliance",
            "Must",
        ),
        Requirement(
            "TR-001",
            "Customer migration",
            "Existing customer accounts shall be migrated before production launch.",
            RequirementType.TRANSITION,
            "Migration Team",
            "Should",
        ),
        Requirement(
            "CON-001",
            "Technology constraint",
            "The solution must operate within the organization's approved cloud environment.",
            RequirementType.CONSTRAINT,
            "Architecture Team",
            "Must",
        ),
    ]

    for requirement in examples:
        print(
            f"{requirement.requirement_id:9} | "
            f"{requirement.requirement_type.value:18} | "
            f"{requirement.title}"
        )


# ============================================================================
# 3. THE REQUIREMENTS LIFECYCLE
# ============================================================================

def requirements_lifecycle() -> None:
    section("3. REQUIREMENTS LIFECYCLE")

    phases = [
        ("1. Identify", "Determine who needs what and why."),
        ("2. Elicit", "Collect information through interviews, workshops, observation, documents, surveys, prototypes, and analysis."),
        ("3. Analyze", "Clarify, decompose, classify, prioritize, model, and identify conflicts."),
        ("4. Specify", "Document requirements in a precise and reviewable form."),
        ("5. Validate", "Check that requirements represent genuine needs and are feasible and testable."),
        ("6. Baseline", "Freeze an approved version for controlled execution."),
        ("7. Trace", "Connect requirements to stakeholders, design, implementation, and tests."),
        ("8. Manage change", "Evaluate and approve or reject proposed modifications."),
        ("9. Verify", "Confirm that the delivered solution satisfies specified requirements."),
        ("10. Maintain", "Keep requirements current throughout the project and product lifecycle."),
    ]

    for phase, description in phases:
        print(f"{phase:<18} {description}")


# ============================================================================
# 4. REQUIREMENT ELICITATION
# ============================================================================

@dataclass
class Stakeholder:
    name: str
    role: str
    interests: List[str]
    influence: str


def elicitation_methods() -> None:
    section("4. REQUIREMENT ELICITATION")

    stakeholders = [
        Stakeholder(
            "Maya",
            "Business Sponsor",
            ["Revenue", "Customer experience", "Time to market"],
            "High",
        ),
        Stakeholder(
            "Arjun",
            "Operations Lead",
            ["Reliability", "Monitoring", "Support workload"],
            "High",
        ),
        Stakeholder(
            "Sara",
            "Customer",
            ["Fast checkout", "Clear errors", "Easy recovery"],
            "Medium",
        ),
        Stakeholder(
            "Dev Team",
            "Engineering",
            ["Feasibility", "Maintainability", "Security"],
            "High",
        ),
    ]

    methods = {
        "Interviews": "Useful for detailed individual perspectives.",
        "Workshops": "Useful for resolving shared understanding and conflicts.",
        "Observation": "Useful when actual work differs from documented procedures.",
        "Surveys": "Useful for collecting structured feedback from many participants.",
        "Document analysis": "Useful for policies, contracts, legacy systems, and regulations.",
        "Prototyping": "Useful when users struggle to express needs without seeing a possible solution.",
        "Process modeling": "Useful for understanding workflows and handoffs.",
        "Data analysis": "Useful when requirements should be grounded in actual behavior.",
    }

    print("Stakeholders:")
    for stakeholder in stakeholders:
        print(
            f"  {stakeholder.name} | {stakeholder.role} | "
            f"Influence={stakeholder.influence}"
        )

    print("\nElicitation methods:")
    for method, use in methods.items():
        print(f"  {method}: {use}")


# ============================================================================
# 5. ASKING GOOD REQUIREMENT QUESTIONS
# ============================================================================

def requirement_questions() -> None:
    section("5. QUESTIONS FOR UNDERSTANDING A REQUIREMENT")

    questions = [
        "Who needs this?",
        "What problem is being solved?",
        "Why is this requirement necessary?",
        "What happens today?",
        "What should happen after the project?",
        "What triggers the behavior?",
        "What are the inputs?",
        "What are the outputs?",
        "Who consumes the output?",
        "What are the business rules?",
        "What happens when the normal path fails?",
        "What data is required?",
        "What are the security implications?",
        "What performance level is required?",
        "What regulations apply?",
        "What constraints exist?",
        "What assumptions are being made?",
        "What dependencies exist?",
        "How will we know the requirement is satisfied?",
        "Who has authority to approve it?",
    ]

    bullet(questions)


# ============================================================================
# 6. BAD REQUIREMENTS AND HOW TO IMPROVE THEM
# ============================================================================

def improve_requirement(
    original: str,
    improved: str,
    reason: str,
) -> None:
    print(f"Original : {original}")
    print(f"Improved : {improved}")
    print(f"Reason   : {reason}")
    print()


def demonstrate_bad_requirements() -> None:
    section("6. BAD VERSUS GOOD REQUIREMENTS")

    examples = [
        (
            "The system should be fast.",
            "95% of search requests shall return results within 2 seconds under 1,000 concurrent users.",
            "Defines measurable performance and operating conditions.",
        ),
        (
            "The application must be user-friendly.",
            "A first-time customer shall be able to complete checkout without assistance using the documented checkout workflow.",
            "Replaces subjective language with observable behavior.",
        ),
        (
            "The system should support many users.",
            "The system shall support 10,000 concurrently authenticated users while maintaining the stated response-time target.",
            "Defines capacity and connects it to performance.",
        ),
        (
            "The report should be generated quickly.",
            "The monthly report shall be generated within 30 seconds for datasets containing up to 5 million records.",
            "Defines measurable time and data volume.",
        ),
        (
            "Use modern encryption.",
            "Sensitive data shall be encrypted using the organization's approved cryptographic standards.",
            "Avoids undefined terminology and links the requirement to an approved standard.",
        ),
    ]

    for original, improved, reason in examples:
        improve_requirement(original, improved, reason)


# ============================================================================
# 7. QUALITY CHARACTERISTICS
# ============================================================================

def requirement_quality_checklist(requirement: Requirement) -> Dict[str, bool]:
    """
    Evaluate common quality dimensions.

    These checks are deliberately simple because natural-language quality
    cannot be completely determined with keyword rules.
    """
    description = requirement.description.lower()

    vague_terms = [
        "fast",
        "easy",
        "simple",
        "modern",
        "user-friendly",
        "appropriate",
        "reasonable",
    ]

    return {
        "Identifiable": bool(requirement.requirement_id),
        "Clear title": bool(requirement.title.strip()),
        "Clear description": bool(requirement.description.strip()),
        "Named stakeholder": bool(requirement.stakeholder.strip()),
        "Prioritized": bool(requirement.priority.strip()),
        "Has source": bool(requirement.source.strip()),
        "Has acceptance criteria": requirement.has_acceptance_criteria(),
        "Likely testable": requirement.is_testable(),
        "Avoids obvious vague terms": not any(
            term in description for term in vague_terms
        ),
        "Has explicit version": requirement.version >= 1,
    }


def demonstrate_quality() -> None:
    section("7. CHARACTERISTICS OF A HIGH-QUALITY REQUIREMENT")

    explain(
        "A strong requirement should be clear, necessary, feasible, "
        "unambiguous, consistent, complete enough for its purpose, "
        "verifiable, traceable, prioritized, and understandable by the "
        "relevant stakeholders."
    )

    requirement = Requirement(
        requirement_id="NFR-002",
        title="Search response time",
        description=(
            "95% of valid product-search requests shall receive a complete "
            "response within 2 seconds under 1,000 concurrent users."
        ),
        requirement_type=RequirementType.NON_FUNCTIONAL,
        stakeholder="Customer Experience Team",
        priority="Must",
        source="Performance workshop",
        acceptance_criteria=[
            "Run a load test with 1,000 concurrent users.",
            "At least 95% of valid requests complete within 2 seconds.",
            "The result is recorded in the performance test report.",
        ],
    )

    checks = requirement_quality_checklist(requirement)

    for criterion, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL':4} | {criterion}")

    print(f"\nQuality score: {requirement.quality_score()}/10")


# ============================================================================
# 8. FUNCTIONAL REQUIREMENTS
# ============================================================================

def functional_requirement_example() -> None:
    section("8. FUNCTIONAL REQUIREMENTS")

    explain(
        "Functional requirements describe behavior or capabilities. They "
        "answer questions such as what the system shall do, what inputs it "
        "accepts, what outputs it produces, and what business rules it follows."
    )

    requirement = Requirement(
        requirement_id="FR-100",
        title="Submit order",
        description=(
            "The system shall create an order when an authenticated customer "
            "submits a valid cart and payment authorization succeeds."
        ),
        requirement_type=RequirementType.FUNCTIONAL,
        stakeholder="Customer",
        priority="Must",
        acceptance_criteria=[
            "An authenticated customer submits a cart containing at least one valid item.",
            "Payment authorization succeeds.",
            "The system creates a unique order identifier.",
            "The customer receives the order identifier.",
        ],
    )

    print(requirement.description)
    print("\nAcceptance criteria:")
    bullet(requirement.acceptance_criteria)


# ============================================================================
# 9. NON-FUNCTIONAL REQUIREMENTS
# ============================================================================

def non_functional_requirement_example() -> None:
    section("9. NON-FUNCTIONAL REQUIREMENTS")

    explain(
        "Non-functional requirements define qualities, constraints, or "
        "conditions under which the solution operates. Typical areas include "
        "performance, availability, security, accessibility, scalability, "
        "maintainability, observability, usability, and reliability."
    )

    requirements = [
        (
            "Performance",
            "95% of API requests shall complete within 500 milliseconds.",
        ),
        (
            "Availability",
            "The production service shall maintain 99.9% monthly availability.",
        ),
        (
            "Security",
            "Administrative access shall require multi-factor authentication.",
        ),
        (
            "Accessibility",
            "The web interface shall support the project's approved accessibility criteria.",
        ),
        (
            "Scalability",
            "The service shall support 10,000 concurrent sessions without exceeding the defined latency target.",
        ),
        (
            "Recoverability",
            "The service shall recover from a complete application restart within 5 minutes.",
        ),
        (
            "Maintainability",
            "Production changes shall be deployable through the approved automated deployment process.",
        ),
    ]

    for category, requirement in requirements:
        print(f"{category:<18}: {requirement}")


# ============================================================================
# 10. CONSTRAINTS, ASSUMPTIONS, DEPENDENCIES, RISKS
# ============================================================================

@dataclass
class ProjectContext:
    assumptions: List[str]
    constraints: List[str]
    dependencies: List[str]
    risks: List[str]


def demonstrate_project_context() -> None:
    section("10. ASSUMPTIONS, CONSTRAINTS, DEPENDENCIES, AND RISKS")

    context = ProjectContext(
        assumptions=[
            "The payment provider will provide a stable test environment.",
            "Existing customer records contain required identifiers.",
        ],
        constraints=[
            "The project must use the organization's approved cloud environment.",
            "Production release is limited to the approved deployment window.",
        ],
        dependencies=[
            "Payment provider API",
            "Identity service",
            "Customer database",
        ],
        risks=[
            "External payment API latency may affect checkout performance.",
            "Legacy customer records may contain incomplete data.",
        ],
    )

    for category, values in [
        ("Assumptions", context.assumptions),
        ("Constraints", context.constraints),
        ("Dependencies", context.dependencies),
        ("Risks", context.risks),
    ]:
        print(f"\n{category}:")
        bullet(values)


# ============================================================================
# 11. REQUIREMENT DECOMPOSITION
# ============================================================================

@dataclass
class RequirementNode:
    identifier: str
    description: str
    children: List["RequirementNode"] = field(default_factory=list)

    def add_child(self, child: "RequirementNode") -> None:
        self.children.append(child)

    def print_tree(self, level: int = 0) -> None:
        print("  " * level + f"{self.identifier}: {self.description}")
        for child in self.children:
            child.print_tree(level + 1)


def demonstrate_decomposition() -> None:
    section("11. REQUIREMENT DECOMPOSITION")

    root = RequirementNode(
        "BR-001",
        "Customers shall be able to complete online purchases.",
    )

    checkout = RequirementNode(
        "FR-001",
        "The customer shall be able to submit a valid cart.",
    )

    payment = RequirementNode(
        "FR-002",
        "The system shall authorize payment before creating an order.",
    )

    confirmation = RequirementNode(
        "FR-003",
        "The system shall provide an order confirmation after successful order creation.",
    )

    performance = RequirementNode(
        "NFR-001",
        "95% of checkout requests shall complete within 2 seconds.",
    )

    checkout.add_child(
        RequirementNode(
            "FR-001.1",
            "The system shall validate cart item availability.",
        )
    )

    checkout.add_child(
        RequirementNode(
            "FR-001.2",
            "The system shall calculate the order total.",
        )
    )

    payment.add_child(
        RequirementNode(
            "FR-002.1",
            "The system shall send the payment authorization request.",
        )
    )

    payment.add_child(
        RequirementNode(
            "FR-002.2",
            "The system shall handle declined payment responses.",
        )
    )

    root.add_child(checkout)
    root.add_child(payment)
    root.add_child(confirmation)
    root.add_child(performance)

    root.print_tree()


# ============================================================================
# 12. USER STORIES
# ============================================================================

@dataclass
class UserStory:
    story_id: str
    role: str
    action: str
    benefit: str
    acceptance_criteria: List[str]

    def as_text(self) -> str:
        return (
            f"As a {self.role}, I want to {self.action}, "
            f"so that {self.benefit}."
        )


def demonstrate_user_story() -> None:
    section("12. USER STORIES")

    story = UserStory(
        story_id="US-001",
        role="customer",
        action="reset my password using my verified email address",
        benefit="I can regain access without contacting support",
        acceptance_criteria=[
            "A registered user can request a password reset.",
            "The reset process requires a valid verification mechanism.",
            "An expired reset token cannot be used.",
            "A successful reset invalidates the previous password.",
        ],
    )

    print(story.as_text())
    print("\nAcceptance criteria:")
    bullet(story.acceptance_criteria)


# ============================================================================
# 13. ACCEPTANCE CRITERIA
# ============================================================================

@dataclass
class AcceptanceTest:
    name: str
    condition: str
    expected_result: str

    def evaluate(self, actual_result: str) -> bool:
        """
        Demonstration-only evaluator.

        Real acceptance testing should use explicit test procedures rather
        than simple string matching.
        """
        return self.expected_result.lower() == actual_result.lower()


def demonstrate_acceptance_criteria() -> None:
    section("13. ACCEPTANCE CRITERIA")

    tests = [
        AcceptanceTest(
            "Valid checkout",
            "Valid cart and successful payment",
            "Order is created",
        ),
        AcceptanceTest(
            "Declined payment",
            "Payment provider declines authorization",
            "Order is not created",
        ),
        AcceptanceTest(
            "Empty cart",
            "Cart contains no purchasable items",
            "Validation error is shown",
        ),
    ]

    actual_results = [
        "Order is created",
        "Order is not created",
        "Validation error is shown",
    ]

    for test, actual in zip(tests, actual_results):
        passed = test.evaluate(actual)
        print(f"{test.name:<20} | {'PASS' if passed else 'FAIL'}")


# ============================================================================
# 14. GIVEN-WHEN-THEN ACCEPTANCE CRITERIA
# ============================================================================

def demonstrate_given_when_then() -> None:
    section("14. GIVEN-WHEN-THEN ACCEPTANCE CRITERIA")

    criteria = [
        (
            "Given a registered customer",
            "When the customer enters a valid reset request",
            "Then a password-reset process is initiated",
        ),
        (
            "Given an expired reset token",
            "When the customer submits the token",
            "Then the system rejects the request",
        ),
        (
            "Given a valid cart and successful payment",
            "When checkout is submitted",
            "Then an order identifier is created",
        ),
    ]

    for given, when, then in criteria:
        print(f"{given}\n{when}\n{then}\n")


# ============================================================================
# 15. USE CASES
# ============================================================================

@dataclass
class UseCase:
    use_case_id: str
    name: str
    primary_actor: str
    trigger: str
    preconditions: List[str]
    main_flow: List[str]
    alternate_flows: List[str]
    postconditions: List[str]

    def print_use_case(self) -> None:
        print(f"{self.use_case_id}: {self.name}")
        print(f"Actor: {self.primary_actor}")
        print(f"Trigger: {self.trigger}")

        print("\nPreconditions:")
        bullet(self.preconditions)

        print("\nMain flow:")
        for index, step in enumerate(self.main_flow, start=1):
            print(f"  {index}. {step}")

        print("\nAlternate flows:")
        bullet(self.alternate_flows)

        print("\nPostconditions:")
        bullet(self.postconditions)


def demonstrate_use_case() -> None:
    section("15. USE CASES")

    use_case = UseCase(
        use_case_id="UC-001",
        name="Complete checkout",
        primary_actor="Customer",
        trigger="Customer submits the checkout form.",
        preconditions=[
            "Customer is authenticated.",
            "Cart contains valid items.",
            "Required checkout information is present.",
        ],
        main_flow=[
            "Validate cart.",
            "Calculate total.",
            "Request payment authorization.",
            "Receive successful authorization.",
            "Create order.",
            "Display confirmation.",
        ],
        alternate_flows=[
            "Payment declined: display a payment failure message and do not create the order.",
            "Item unavailable: request cart correction before payment.",
            "Payment service unavailable: show retry guidance.",
        ],
        postconditions=[
            "A successful transaction has a unique order identifier.",
            "An unsuccessful transaction has not created a completed order.",
        ],
    )

    use_case.print_use_case()


# ============================================================================
# 16. REQUIREMENT PRIORITIZATION
# ============================================================================

PRIORITY_RANK = {
    "Must": 4,
    "Should": 3,
    "Could": 2,
    "Won't": 1,
}


def moscow_priority_score(priority: str) -> int:
    """Return a numeric representation for simple sorting."""
    return PRIORITY_RANK.get(priority, 0)


def demonstrate_moscow() -> None:
    section("16. MoSCoW PRIORITIZATION")

    items = [
        ("Payment authorization", "Must"),
        ("Order confirmation email", "Should"),
        ("Custom dashboard theme", "Could"),
        ("Advanced recommendation engine", "Won't"),
    ]

    for requirement, priority in sorted(
        items,
        key=lambda item: moscow_priority_score(item[1]),
        reverse=True,
    ):
        print(f"{priority:<6} | {requirement}")


# ============================================================================
# 17. VALUE/EFFORT PRIORITIZATION
# ============================================================================

@dataclass
class PrioritizationItem:
    name: str
    business_value: float
    effort: float
    risk_reduction: float = 0.0

    @property
    def value_per_effort(self) -> float:
        if self.effort <= 0:
            return float("inf")
        return self.business_value / self.effort

    @property
    def composite_score(self) -> float:
        """
        Educational scoring model.

        A real organization should define scoring criteria collaboratively
        rather than treating this formula as universally correct.
        """
        return (
            self.business_value * 0.6
            + self.risk_reduction * 0.4
        ) / max(self.effort, 0.1)


def demonstrate_value_effort() -> None:
    section("17. VALUE, EFFORT, AND RISK PRIORITIZATION")

    items = [
        PrioritizationItem("Basic checkout", 10, 4, 9),
        PrioritizationItem("Saved payment method", 7, 6, 3),
        PrioritizationItem("Custom theme", 3, 2, 1),
        PrioritizationItem("Advanced analytics", 8, 8, 2),
    ]

    ranked = sorted(items, key=lambda item: item.composite_score, reverse=True)

    for item in ranked:
        print(
            f"{item.name:<25} "
            f"Value={item.business_value:<4} "
            f"Effort={item.effort:<4} "
            f"RiskReduction={item.risk_reduction:<4} "
            f"Score={item.composite_score:.2f}"
        )


# ============================================================================
# 18. CONFLICTING REQUIREMENTS
# ============================================================================

def detect_requirement_conflict(
    requirement_a: Requirement,
    requirement_b: Requirement,
) -> List[str]:
    """
    Detect obvious numeric conflicts in performance-style requirements.

    This is intentionally conservative. Semantic conflict detection requires
    human analysis or more sophisticated domain-specific tooling.
    """
    conflicts = []

    text_a = requirement_a.description.lower()
    text_b = requirement_b.description.lower()

    if "within 2 seconds" in text_a and "within 5 seconds" in text_b:
        conflicts.append(
            "Different response-time targets are specified for apparently similar behavior."
        )

    if "must" in text_a and "must not" in text_b:
        conflicts.append("Potentially contradictory mandatory language exists.")

    return conflicts


def demonstrate_conflicts() -> None:
    section("18. REQUIREMENT CONFLICTS")

    requirement_a = Requirement(
        "NFR-010",
        "Search response",
        "Search requests shall complete within 2 seconds.",
        RequirementType.NON_FUNCTIONAL,
        "Product",
        "Must",
    )

    requirement_b = Requirement(
        "NFR-011",
        "Search response",
        "Search requests shall complete within 5 seconds.",
        RequirementType.NON_FUNCTIONAL,
        "Operations",
        "Must",
    )

    conflicts = detect_requirement_conflict(requirement_a, requirement_b)

    print("Potential conflicts:")
    if conflicts:
        bullet(conflicts)
    else:
        print("  None detected by the simplified checker.")

    explain(
        "\nImportant: absence of a machine-detected conflict does not prove "
        "that requirements are consistent. Context, scope, actors, "
        "conditions, and business rules must be examined."
    )


# ============================================================================
# 19. REQUIREMENT TRACEABILITY
# ============================================================================

@dataclass
class TraceabilityMatrix:
    """
    Links requirements to stakeholders, design elements, implementation
    elements, and tests.
    """

    requirement_to_stakeholder: Dict[str, Set[str]] = field(default_factory=dict)
    requirement_to_design: Dict[str, Set[str]] = field(default_factory=dict)
    requirement_to_implementation: Dict[str, Set[str]] = field(default_factory=dict)
    requirement_to_test: Dict[str, Set[str]] = field(default_factory=dict)

    def link(
        self,
        requirement_id: str,
        stakeholder: Optional[str] = None,
        design: Optional[str] = None,
        implementation: Optional[str] = None,
        test: Optional[str] = None,
    ) -> None:
        if stakeholder:
            self.requirement_to_stakeholder.setdefault(requirement_id, set()).add(
                stakeholder
            )

        if design:
            self.requirement_to_design.setdefault(requirement_id, set()).add(
                design
            )

        if implementation:
            self.requirement_to_implementation.setdefault(
                requirement_id, set()
            ).add(implementation)

        if test:
            self.requirement_to_test.setdefault(requirement_id, set()).add(test)

    def coverage(self, requirement_ids: List[str]) -> float:
        if not requirement_ids:
            return 100.0

        covered = sum(
            bool(self.requirement_to_test.get(requirement_id))
            for requirement_id in requirement_ids
        )

        return covered / len(requirement_ids) * 100


def demonstrate_traceability() -> None:
    section("19. REQUIREMENTS TRACEABILITY")

    matrix = TraceabilityMatrix()

    matrix.link(
        "FR-100",
        stakeholder="Customer",
        design="Checkout Service",
        implementation="OrderService.create_order",
        test="AT-001",
    )

    matrix.link(
        "NFR-002",
        stakeholder="Operations",
        design="API Gateway",
        implementation="Performance configuration",
        test="PERF-001",
    )

    matrix.link(
        "SEC-001",
        stakeholder="Security Team",
        design="Logging Policy",
        implementation="LogSanitizer",
        test="SEC-TEST-001",
    )

    requirement_ids = ["FR-100", "NFR-002", "SEC-001", "DATA-001"]

    print("Traceability:")
    for requirement_id in requirement_ids:
        print(f"\n{requirement_id}")
        print(
            f"  Stakeholders    : "
            f"{sorted(matrix.requirement_to_stakeholder.get(requirement_id, set()))}"
        )
        print(
            f"  Design          : "
            f"{sorted(matrix.requirement_to_design.get(requirement_id, set()))}"
        )
        print(
            f"  Implementation  : "
            f"{sorted(matrix.requirement_to_implementation.get(requirement_id, set()))}"
        )
        print(
            f"  Tests           : "
            f"{sorted(matrix.requirement_to_test.get(requirement_id, set()))}"
        )

    print(f"\nTest coverage: {matrix.coverage(requirement_ids):.1f}%")


# ============================================================================
# 20. REQUIREMENTS REPOSITORY
# ============================================================================

class RequirementsRepository:
    """
    Small in-memory requirements repository.

    A production repository would normally include persistent storage,
    permissions, audit history, workflow, search, and integration with
    project management and testing systems.
    """

    def __init__(self) -> None:
        self._requirements: Dict[str, Requirement] = {}

    def add(self, requirement: Requirement) -> None:
        if requirement.requirement_id in self._requirements:
            raise ValueError(
                f"Requirement {requirement.requirement_id} already exists."
            )

        self._requirements[requirement.requirement_id] = requirement

    def get(self, requirement_id: str) -> Requirement:
        try:
            return self._requirements[requirement_id]
        except KeyError as exc:
            raise KeyError(
                f"Requirement {requirement_id} was not found."
            ) from exc

    def update_description(
        self,
        requirement_id: str,
        new_description: str,
    ) -> None:
        requirement = self.get(requirement_id)
        requirement.description = new_description
        requirement.version += 1
        requirement.status = "Draft"

    def approve(self, requirement_id: str) -> None:
        requirement = self.get(requirement_id)
        requirement.status = "Approved"

    def list_by_type(
        self,
        requirement_type: RequirementType,
    ) -> List[Requirement]:
        return [
            requirement
            for requirement in self._requirements.values()
            if requirement.requirement_type == requirement_type
        ]

    def all(self) -> List[Requirement]:
        return list(self._requirements.values())


def demonstrate_repository() -> None:
    section("20. REQUIREMENTS REPOSITORY")

    repository = RequirementsRepository()

    repository.add(
        Requirement(
            "FR-200",
            "Create customer profile",
            "The system shall create a customer profile after valid registration.",
            RequirementType.FUNCTIONAL,
            "Customer",
            "Must",
            acceptance_criteria=[
                "Valid registration creates one profile.",
                "Duplicate registration is rejected.",
            ],
        )
    )

    repository.add(
        Requirement(
            "NFR-200",
            "Registration latency",
            "95% of valid registration requests shall complete within 2 seconds.",
            RequirementType.NON_FUNCTIONAL,
            "Operations",
            "Should",
            acceptance_criteria=[
                "Performance test validates the 95th percentile target.",
            ],
        )
    )

    repository.update_description(
        "FR-200",
        "The system shall create exactly one customer profile after valid registration.",
    )

    repository.approve("FR-200")

    for requirement in repository.all():
        print(
            f"{requirement.requirement_id} | "
            f"Version={requirement.version} | "
            f"Status={requirement.status} | "
            f"{requirement.description}"
        )


# ============================================================================
# 21. REQUIREMENT CHANGE MANAGEMENT
# ============================================================================

@dataclass
class ChangeRequest:
    change_id: str
    requirement_id: str
    requested_change: str
    business_reason: str
    requester: str
    impact_areas: List[str] = field(default_factory=list)
    estimated_effort: Optional[float] = None
    estimated_cost: Optional[float] = None
    status: str = "Proposed"


def analyze_change_impact(change: ChangeRequest) -> Dict[str, object]:
    """Return a simple impact-analysis result."""
    return {
        "change_id": change.change_id,
        "requirement_id": change.requirement_id,
        "impact_count": len(change.impact_areas),
        "high_impact": len(change.impact_areas) >= 4,
        "requires_effort_estimate": change.estimated_effort is None,
        "requires_cost_estimate": change.estimated_cost is None,
    }


def demonstrate_change_management() -> None:
    section("21. REQUIREMENT CHANGE MANAGEMENT")

    change = ChangeRequest(
        change_id="CR-001",
        requirement_id="FR-100",
        requested_change=(
            "Allow customers to cancel an order for up to 15 minutes after submission."
        ),
        business_reason="Reduce support contacts caused by accidental purchases.",
        requester="Customer Experience",
        impact_areas=[
            "Order service",
            "Payment service",
            "Customer interface",
            "Notifications",
            "Reporting",
        ],
        estimated_effort=13,
        estimated_cost=5000,
    )

    impact = analyze_change_impact(change)

    print(f"Change: {change.change_id}")
    print(f"Requirement: {change.requirement_id}")
    print(f"Reason: {change.business_reason}")
    print(f"Status: {change.status}")
    print(f"Impact areas: {len(change.impact_areas)}")
    print(f"High impact: {impact['high_impact']}")
    print(f"Estimated effort: {change.estimated_effort}")
    print(f"Estimated cost: {change.estimated_cost}")

    explain(
        "\nA change should not be judged only by whether it sounds useful. "
        "Impact analysis should examine scope, schedule, cost, architecture, "
        "security, data, testing, operations, dependencies, and existing "
        "approved requirements."
    )


# ============================================================================
# 22. REQUIREMENT BASELINES
# ============================================================================

@dataclass
class RequirementBaseline:
    baseline_name: str
    version: str
    requirement_ids: List[str]
    approved_by: str
    status: str = "Approved"


def demonstrate_baseline() -> None:
    section("22. REQUIREMENT BASELINES")

    baseline = RequirementBaseline(
        baseline_name="Checkout MVP",
        version="1.0",
        requirement_ids=[
            "BR-001",
            "FR-001",
            "FR-002",
            "FR-003",
            "NFR-001",
            "SEC-001",
        ],
        approved_by="Project Steering Committee",
    )

    print(f"Baseline: {baseline.baseline_name}")
    print(f"Version : {baseline.version}")
    print(f"Status  : {baseline.status}")
    print(f"Approved: {baseline.approved_by}")
    print("Requirements:")
    bullet(baseline.requirement_ids)

    explain(
        "\nA baseline establishes a controlled reference point. Changes after "
        "baseline approval should follow the project's change-control process."
    )


# ============================================================================
# 23. REQUIREMENT STATUS MODEL
# ============================================================================

REQUIREMENT_STATUSES = [
    "Draft",
    "Under Review",
    "Approved",
    "Implemented",
    "Verified",
    "Rejected",
    "Superseded",
]


def demonstrate_status_model() -> None:
    section("23. REQUIREMENT STATUS")

    print("Typical status progression:")
    print("Draft → Under Review → Approved → Implemented → Verified")

    print("\nOther possible states:")
    bullet(["Rejected", "Superseded"])


# ============================================================================
# 24. REQUIREMENT METRICS
# ============================================================================

def calculate_metrics(requirements: List[Requirement]) -> Dict[str, float]:
    if not requirements:
        return {
            "count": 0.0,
            "average_quality_score": 0.0,
            "testable_percentage": 0.0,
            "acceptance_criteria_percentage": 0.0,
            "approved_percentage": 0.0,
        }

    average_quality = statistics.mean(
        requirement.quality_score() for requirement in requirements
    )

    testable = sum(requirement.is_testable() for requirement in requirements)
    criteria = sum(
        requirement.has_acceptance_criteria() for requirement in requirements
    )
    approved = sum(requirement.status == "Approved" for requirement in requirements)

    return {
        "count": float(len(requirements)),
        "average_quality_score": average_quality,
        "testable_percentage": testable / len(requirements) * 100,
        "acceptance_criteria_percentage": criteria / len(requirements) * 100,
        "approved_percentage": approved / len(requirements) * 100,
    }


def demonstrate_metrics() -> None:
    section("24. REQUIREMENTS METRICS")

    requirements = [
        Requirement(
            "R-001",
            "Create account",
            "The system shall create an account after valid registration.",
            RequirementType.FUNCTIONAL,
            "Customer",
            acceptance_criteria=["Valid registration creates one account."],
            status="Approved",
        ),
        Requirement(
            "R-002",
            "Fast login",
            "The login process should be fast and user-friendly.",
            RequirementType.NON_FUNCTIONAL,
            "Customer",
            status="Draft",
        ),
        Requirement(
            "R-003",
            "API latency",
            "95% of login requests shall complete within 1 second.",
            RequirementType.NON_FUNCTIONAL,
            "Operations",
            acceptance_criteria=["Load test verifies 95th percentile latency."],
            status="Approved",
        ),
    ]

    metrics = calculate_metrics(requirements)

    for name, value in metrics.items():
        if name == "count":
            print(f"{name:<35}: {int(value)}")
        else:
            print(f"{name:<35}: {value:.2f}")


# ============================================================================
# 25. DUPLICATE REQUIREMENTS
# ============================================================================

def find_duplicate_requirements(
    requirements: List[Requirement],
) -> List[Tuple[str, str]]:
    """
    Find exact normalized description duplicates.

    Real duplicate detection should account for semantic equivalence,
    scope, conditions, and terminology.
    """
    groups: Dict[str, List[str]] = defaultdict(list)

    for requirement in requirements:
        normalized = re.sub(
            r"\s+",
            " ",
            requirement.description.strip().lower(),
        )
        groups[normalized].append(requirement.requirement_id)

    duplicates = []

    for ids in groups.values():
        if len(ids) > 1:
            for index in range(len(ids)):
                for other in range(index + 1, len(ids)):
                    duplicates.append((ids[index], ids[other]))

    return duplicates


def demonstrate_duplicate_detection() -> None:
    section("25. DUPLICATE REQUIREMENTS")

    requirements = [
        Requirement(
            "FR-301",
            "Create order",
            "The system shall create an order after successful payment.",
            RequirementType.FUNCTIONAL,
            "Customer",
        ),
        Requirement(
            "FR-302",
            "Create order after payment",
            "The system shall create an order after successful payment.",
            RequirementType.FUNCTIONAL,
            "Operations",
        ),
        Requirement(
            "FR-303",
            "Notify customer",
            "The system shall send an order confirmation.",
            RequirementType.FUNCTIONAL,
            "Customer",
        ),
    ]

    duplicates = find_duplicate_requirements(requirements)

    if duplicates:
        print("Potential exact duplicates:")
        bullet([f"{a} ↔ {b}" for a, b in duplicates])
    else:
        print("No exact duplicates found.")


# ============================================================================
# 26. ORPHAN REQUIREMENTS
# ============================================================================

def find_orphan_requirements(
    requirements: List[Requirement],
    traceability: TraceabilityMatrix,
) -> List[str]:
    """Find requirements without a linked test."""
    return [
        requirement.requirement_id
        for requirement in requirements
        if not traceability.requirement_to_test.get(requirement.requirement_id)
    ]


def demonstrate_orphan_detection() -> None:
    section("26. ORPHAN REQUIREMENTS")

    requirements = [
        Requirement(
            "FR-401",
            "Create order",
            "The system shall create an order after successful payment.",
            RequirementType.FUNCTIONAL,
            "Customer",
        ),
        Requirement(
            "FR-402",
            "Send confirmation",
            "The system shall send an order confirmation.",
            RequirementType.FUNCTIONAL,
            "Customer",
        ),
        Requirement(
            "NFR-401",
            "API latency",
            "95% of requests shall complete within 2 seconds.",
            RequirementType.NON_FUNCTIONAL,
            "Operations",
        ),
    ]

    matrix = TraceabilityMatrix()
    matrix.link("FR-401", test="AT-401")
    matrix.link("FR-402", test="AT-402")

    orphans = find_orphan_requirements(requirements, matrix)

    print("Requirements without linked tests:")
    bullet(orphans)


# ============================================================================
# 27. COMPLETENESS AND COVERAGE
# ============================================================================

@dataclass
class RequirementCoverage:
    requirement_id: str
    has_owner: bool
    has_source: bool
    has_acceptance_criteria: bool
    has_test: bool
    has_design_link: bool


def coverage_score(item: RequirementCoverage) -> float:
    checks = [
        item.has_owner,
        item.has_source,
        item.has_acceptance_criteria,
        item.has_test,
        item.has_design_link,
    ]

    return sum(checks) / len(checks) * 100


def demonstrate_coverage() -> None:
    section("27. REQUIREMENT COVERAGE")

    items = [
        RequirementCoverage(
            "FR-501",
            True,
            True,
            True,
            True,
            True,
        ),
        RequirementCoverage(
            "FR-502",
            True,
            True,
            True,
            False,
            True,
        ),
        RequirementCoverage(
            "NFR-501",
            True,
            True,
            False,
            False,
            False,
        ),
    ]

    for item in items:
        print(
            f"{item.requirement_id}: "
            f"{coverage_score(item):.0f}% coverage"
        )


# ============================================================================
# 28. EDGE CASES IN REQUIREMENTS
# ============================================================================

def demonstrate_edge_cases() -> None:
    section("28. REQUIREMENT EDGE CASES")

    cases = [
        (
            "Empty description",
            "",
            "A requirement without a description cannot be meaningfully reviewed.",
        ),
        (
            "Undefined actor",
            "The system shall send a notification.",
            "Identify who triggers the behavior and who receives the notification.",
        ),
        (
            "Missing failure behavior",
            "The system shall process payments.",
            "Define declined, timeout, duplicate, and unavailable-provider behavior.",
        ),
        (
            "Boundary value",
            "Users may upload files up to 10 MB.",
            "Explicitly decide whether exactly 10 MB is accepted and what happens above it.",
        ),
        (
            "Conflicting ownership",
            "Two departments independently approve the same requirement.",
            "Define decision authority and approval responsibility.",
        ),
        (
            "Hidden assumption",
            "The system shall import all customer records.",
            "Define what happens when records are malformed or incomplete.",
        ),
    ]

    for name, example, handling in cases:
        print(f"\n{name}")
        print(f"Example : {example}")
        print(f"Handling: {handling}")


# ============================================================================
# 29. BOUNDARY ANALYSIS
# ============================================================================

def validate_file_size(size_mb: float) -> str:
    """
    Example business rule:
    - 0 MB is not useful and is rejected.
    - Values up to and including 10 MB are accepted.
    - Values above 10 MB are rejected.
    """
    if size_mb <= 0:
        return "REJECT: file size must be greater than 0 MB"
    if size_mb <= 10:
        return "ACCEPT"
    return "REJECT: file exceeds 10 MB limit"


def demonstrate_boundary_analysis() -> None:
    section("29. BOUNDARY VALUE ANALYSIS")

    test_values = [0, 0.01, 9.99, 10, 10.01]

    for value in test_values:
        print(f"{value:>5} MB → {validate_file_size(value)}")

    explain(
        "\nBoundary analysis is important because requirements often fail at "
        "limits rather than in ordinary cases."
    )


# ============================================================================
# 30. BUSINESS RULES
# ============================================================================

@dataclass
class BusinessRule:
    rule_id: str
    name: str
    condition: str
    action: str


def demonstrate_business_rules() -> None:
    section("30. BUSINESS RULES")

    rules = [
        BusinessRule(
            "BRULE-001",
            "Minimum order value",
            "Order subtotal is below 500 INR",
            "Display the minimum-order validation message.",
        ),
        BusinessRule(
            "BRULE-002",
            "Free shipping",
            "Order subtotal is at least 1,000 INR",
            "Set shipping charge to zero.",
        ),
        BusinessRule(
            "BRULE-003",
            "Payment decline",
            "Payment authorization fails",
            "Do not create a completed order.",
        ),
    ]

    for rule in rules:
        print(f"{rule.rule_id}: {rule.name}")
        print(f"  IF   {rule.condition}")
        print(f"  THEN {rule.action}")


# ============================================================================
# 31. REQUIREMENT VALIDATION
# ============================================================================

def validate_requirement(requirement: Requirement) -> List[str]:
    """
    Return validation issues.

    The checks are intentionally explainable and deterministic.
    """
    issues = []

    if not requirement.requirement_id.strip():
        issues.append("Missing requirement identifier.")

    if not requirement.title.strip():
        issues.append("Missing requirement title.")

    if not requirement.description.strip():
        issues.append("Missing requirement description.")

    if not requirement.stakeholder.strip():
        issues.append("Missing stakeholder or owner.")

    if not requirement.source.strip():
        issues.append("Missing requirement source.")

    if not requirement.priority.strip():
        issues.append("Missing priority.")

    vague_terms = [
        "fast",
        "easy",
        "simple",
        "good",
        "modern",
        "user-friendly",
        "appropriate",
        "reasonable",
    ]

    lower_description = requirement.description.lower()

    for term in vague_terms:
        if term in lower_description:
            issues.append(f"Potentially vague term detected: '{term}'.")

    if requirement.requirement_type in {
        RequirementType.FUNCTIONAL,
        RequirementType.NON_FUNCTIONAL,
        RequirementType.SECURITY,
        RequirementType.DATA,
    }:
        if not requirement.acceptance_criteria:
            issues.append("No acceptance criteria provided.")

    if requirement.priority not in {
        "Must",
        "Should",
        "Could",
        "Won't",
    }:
        issues.append(
            "Priority should use the project's defined prioritization scheme."
        )

    return issues


def demonstrate_validation() -> None:
    section("31. REQUIREMENT VALIDATION")

    requirements = [
        Requirement(
            "GOOD-001",
            "Checkout response time",
            "95% of checkout requests shall complete within 2 seconds.",
            RequirementType.NON_FUNCTIONAL,
            "Operations",
            "Must",
            acceptance_criteria=[
                "Performance test verifies the 95th percentile target."
            ],
        ),
        Requirement(
            "",
            "",
            "The system should be fast and user-friendly.",
            RequirementType.FUNCTIONAL,
            "",
            "Important",
        ),
    ]

    for requirement in requirements:
        issues = validate_requirement(requirement)

        print(f"\nRequirement: {requirement.requirement_id or '[missing ID]'}")

        if issues:
            print("Issues:")
            bullet(issues)
        else:
            print("No issues detected by the simplified validator.")


# ============================================================================
# 32. REQUIREMENTS DERIVED FROM A BUSINESS PROBLEM
# ============================================================================

def derive_requirements_from_problem() -> List[Requirement]:
    """
    Convert a business problem into a small set of structured requirements.

    Business problem:
        Customers abandon checkout because the process is slow and payment
        failures are not clearly explained.
    """
    return [
        Requirement(
            "BR-700",
            "Reduce checkout abandonment",
            "The project shall reduce checkout abandonment by at least 10%.",
            RequirementType.BUSINESS,
            "Business Sponsor",
            "Must",
            source="Business case",
            acceptance_criteria=[
                "The baseline abandonment rate is documented.",
                "The post-release measurement period is defined.",
                "The target reduction is at least 10%.",
            ],
        ),
        Requirement(
            "FR-700",
            "Submit checkout",
            (
                "The system shall allow an authenticated customer to submit "
                "a valid cart for payment authorization."
            ),
            RequirementType.FUNCTIONAL,
            "Customer",
            "Must",
            source="Customer interview",
            acceptance_criteria=[
                "Authenticated customers can submit valid carts.",
                "Invalid carts are rejected before payment authorization.",
            ],
        ),
        Requirement(
            "FR-701",
            "Explain payment failure",
            (
                "The system shall display a customer-readable payment failure "
                "message when payment authorization is declined."
            ),
            RequirementType.FUNCTIONAL,
            "Customer",
            "Must",
            source="Support ticket analysis",
            acceptance_criteria=[
                "A declined payment does not create a completed order.",
                "The customer receives a clear failure message.",
            ],
        ),
        Requirement(
            "NFR-700",
            "Checkout latency",
            (
                "95% of checkout requests shall complete within 2 seconds "
                "under the agreed production load profile."
            ),
            RequirementType.NON_FUNCTIONAL,
            "Operations",
            "Must",
            source="Performance analysis",
            acceptance_criteria=[
                "The agreed load profile is documented.",
                "A performance test demonstrates the 95th percentile target.",
            ],
        ),
        Requirement(
            "SEC-700",
            "Protect payment information",
            (
                "Sensitive payment information shall not be written to "
                "application logs."
            ),
            RequirementType.SECURITY,
            "Security Team",
            "Must",
            source="Security review",
            acceptance_criteria=[
                "Log inspection shows that sensitive payment information is absent.",
                "Automated tests cover the relevant logging paths.",
            ],
        ),
    ]


def demonstrate_requirement_derivation() -> None:
    section("32. FROM BUSINESS PROBLEM TO REQUIREMENTS")

    requirements = derive_requirements_from_problem()

    print("Derived requirements:")
    for requirement in requirements:
        print(
            f"{requirement.requirement_id:<8} | "
            f"{requirement.requirement_type.value:<18} | "
            f"{requirement.title}"
        )


# ============================================================================
# 33. REQUIREMENT DEPENDENCY GRAPH
# ============================================================================

class RequirementDependencyGraph:
    def __init__(self) -> None:
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)

    def add_dependency(self, requirement_id: str, depends_on: str) -> None:
        self.dependencies[requirement_id].add(depends_on)

    def get_dependencies(self, requirement_id: str) -> Set[str]:
        return self.dependencies.get(requirement_id, set())

    def has_direct_cycle(self) -> bool:
        """
        Detect a direct two-node cycle.

        This deliberately demonstrates a simple case. Production dependency
        analysis should use a full directed-graph cycle algorithm.
        """
        for requirement, dependencies in self.dependencies.items():
            for dependency in dependencies:
                if requirement in self.dependencies.get(dependency, set()):
                    return True

        return False


def demonstrate_dependencies() -> None:
    section("33. REQUIREMENT DEPENDENCIES")

    graph = RequirementDependencyGraph()

    graph.add_dependency("FR-801", "FR-800")
    graph.add_dependency("FR-802", "FR-801")
    graph.add_dependency("NFR-800", "FR-800")

    for requirement_id in ["FR-801", "FR-802", "NFR-800"]:
        print(
            f"{requirement_id} depends on: "
            f"{sorted(graph.get_dependencies(requirement_id))}"
        )

    print(f"Direct cycle detected: {graph.has_direct_cycle()}")


# ============================================================================
# 34. SECURITY REQUIREMENT THINKING
# ============================================================================

def security_questions() -> None:
    section("34. SECURITY REQUIREMENT CONSIDERATIONS")

    questions = [
        "Who is allowed to perform the action?",
        "How is identity established?",
        "What permissions are required?",
        "What data is sensitive?",
        "What must be encrypted in transit?",
        "What must be encrypted at rest?",
        "What must never appear in logs?",
        "How long should security-relevant records be retained?",
        "What happens after repeated failed authentication attempts?",
        "How are sessions terminated?",
        "What audit events are required?",
        "What external systems or trust boundaries are involved?",
        "What happens if a security dependency is unavailable?",
    ]

    bullet(questions)


# ============================================================================
# 35. PERFORMANCE REQUIREMENT THINKING
# ============================================================================

@dataclass
class PerformanceTarget:
    metric: str
    target: float
    unit: str
    percentile: Optional[int] = None
    load: Optional[int] = None


def demonstrate_performance_requirements() -> None:
    section("35. PERFORMANCE REQUIREMENTS")

    targets = [
        PerformanceTarget(
            "API latency",
            500,
            "milliseconds",
            percentile=95,
            load=1000,
        ),
        PerformanceTarget(
            "Throughput",
            200,
            "requests/second",
            load=1000,
        ),
        PerformanceTarget(
            "Availability",
            99.9,
            "percent",
        ),
    ]

    for target in targets:
        details = f"{target.target} {target.unit}"

        if target.percentile:
            details += f", p{target.percentile}"

        if target.load:
            details += f", load={target.load}"

        print(f"{target.metric:<20}: {details}")


# ============================================================================
# 36. REQUIREMENT-TO-TEST MAPPING
# ============================================================================

@dataclass
class TestCase:
    test_id: str
    requirement_id: str
    description: str
    expected_result: str
    actual_result: Optional[str] = None

    @property
    def passed(self) -> Optional[bool]:
        if self.actual_result is None:
            return None
        return self.actual_result == self.expected_result


def demonstrate_requirement_testing() -> None:
    section("36. REQUIREMENTS VERIFICATION THROUGH TEST CASES")

    tests = [
        TestCase(
            "TC-001",
            "FR-900",
            "Submit a valid order",
            "Order created",
            "Order created",
        ),
        TestCase(
            "TC-002",
            "FR-901",
            "Submit declined payment",
            "Order not created",
            "Order created",
        ),
        TestCase(
            "TC-003",
            "NFR-900",
            "Measure API latency",
            "95th percentile <= 500 ms",
            "95th percentile <= 500 ms",
        ),
    ]

    for test in tests:
        status = "NOT RUN" if test.passed is None else (
            "PASS" if test.passed else "FAIL"
        )

        print(
            f"{test.test_id} | "
            f"{test.requirement_id} | "
            f"{status:<8} | "
            f"{test.description}"
        )


# ============================================================================
# 37. COMMON REQUIREMENT MISTAKES
# ============================================================================

def common_mistakes() -> None:
    section("37. COMMON REQUIREMENT MISTAKES")

    mistakes = [
        (
            "Starting with the solution",
            "Teams jump directly to screens, technologies, or architecture.",
            "Understand the problem, users, outcomes, and constraints first.",
        ),
        (
            "Using vague language",
            "Words such as fast, easy, robust, modern, and intuitive are left undefined.",
            "Define observable or measurable behavior.",
        ),
        (
            "Ignoring negative scenarios",
            "Only the happy path is described.",
            "Document validation failures, timeouts, duplicates, permissions, and unavailable dependencies.",
        ),
        (
            "No acceptance criteria",
            "Nobody knows how satisfaction will be demonstrated.",
            "Define objective acceptance conditions.",
        ),
        (
            "No ownership",
            "Conflicting stakeholders have no decision authority.",
            "Identify accountable stakeholders and approval authority.",
        ),
        (
            "Requirements are not prioritized",
            "Everything is treated as equally important.",
            "Use an agreed prioritization method.",
        ),
        (
            "No traceability",
            "Requirements become disconnected from implementation and testing.",
            "Maintain requirement-to-design-to-test links.",
        ),
        (
            "Uncontrolled changes",
            "Scope expands informally during execution.",
            "Use documented change requests and impact analysis.",
        ),
        (
            "Ignoring constraints",
            "A theoretically correct requirement cannot be implemented within actual project boundaries.",
            "Document technology, legal, budget, schedule, operational, and organizational constraints.",
        ),
    ]

    for mistake, problem, prevention in mistakes:
        print(f"\n{mistake}")
        print(f"  Problem   : {problem}")
        print(f"  Prevention: {prevention}")


# ============================================================================
# 38. REQUIREMENTS IN AGILE PROJECTS
# ============================================================================

def agile_requirements() -> None:
    section("38. REQUIREMENTS IN AGILE PROJECTS")

    explain(
        "Agile does not eliminate requirements. It changes how requirements "
        "are discovered, refined, prioritized, delivered, and adapted."
    )

    artifacts = [
        ("Product vision", "Desired product outcome and direction."),
        ("Epic", "Large capability or outcome that can be decomposed."),
        ("User story", "Small user-centered expression of desired capability."),
        ("Acceptance criteria", "Conditions that determine whether the story is acceptable."),
        ("Product backlog", "Ordered list of product work and requirements."),
        ("Definition of Ready", "Team-specific criteria for work entering execution."),
        ("Definition of Done", "Team-specific completion criteria."),
    ]

    for artifact, meaning in artifacts:
        print(f"{artifact:<24}: {meaning}")


# ============================================================================
# 39. AGILE STORY REFINEMENT
# ============================================================================

def demonstrate_story_refinement() -> None:
    section("39. USER STORY REFINEMENT")

    initial = UserStory(
        "US-100",
        "customer",
        "make a payment",
        "complete my purchase",
        [],
    )

    refined = UserStory(
        "US-100",
        "customer",
        "submit a valid card payment",
        "complete my purchase and receive confirmation",
        [
            "Card details are validated.",
            "Successful authorization creates an order.",
            "Declined payment does not create a completed order.",
            "The customer receives an appropriate result message.",
        ],
    )

    print("Initial:")
    print(initial.as_text())

    print("\nRefined:")
    print(refined.as_text())

    print("\nRefined acceptance criteria:")
    bullet(refined.acceptance_criteria)


# ============================================================================
# 40. WATERFALL AND AGILE REQUIREMENT MANAGEMENT
# ============================================================================

def compare_delivery_approaches() -> None:
    section("40. REQUIREMENTS IN DIFFERENT DELIVERY APPROACHES")

    rows = [
        (
            "Requirement definition",
            "Often more detailed before execution",
            "Progressively refined",
        ),
        (
            "Change handling",
            "Formal change control is often emphasized",
            "Continuous reprioritization is common",
        ),
        (
            "Delivery",
            "Often phase-oriented",
            "Incremental and iterative",
        ),
        (
            "Customer feedback",
            "Often concentrated at defined review points",
            "Frequent throughout development",
        ),
        (
            "Documentation",
            "May be comprehensive and formal",
            "Should still be sufficient, but often lightweight and evolving",
        ),
    ]

    print(f"{'Dimension':<25} | {'Plan-driven':<38} | Agile")
    print("-" * 82)

    for dimension, plan_driven, agile in rows:
        print(
            f"{dimension:<25} | "
            f"{plan_driven:<38} | "
            f"{agile}"
        )


# ============================================================================
# 41. SCOPE AND REQUIREMENTS
# ============================================================================

@dataclass
class ScopeBoundary:
    in_scope: List[str]
    out_of_scope: List[str]


def demonstrate_scope() -> None:
    section("41. REQUIREMENTS AND SCOPE")

    scope = ScopeBoundary(
        in_scope=[
            "Customer registration",
            "Authentication",
            "Checkout",
            "Payment authorization",
            "Order confirmation",
        ],
        out_of_scope=[
            "Warehouse optimization",
            "Supplier management",
            "International tax engine",
            "Loyalty program redesign",
        ],
    )

    print("In scope:")
    bullet(scope.in_scope)

    print("\nOut of scope:")
    bullet(scope.out_of_scope)

    explain(
        "\nExplicit exclusions are useful because requirements discussions "
        "often create implied scope. A requirement repository should make "
        "important boundaries visible."
    )


# ============================================================================
# 42. REQUIREMENT NEGOTIATION
# ============================================================================

def demonstrate_negotiation() -> None:
    section("42. REQUIREMENT NEGOTIATION")

    competing_needs = [
        (
            "Customers",
            "Checkout should be extremely fast.",
        ),
        (
            "Security",
            "Strong authentication and fraud checks are required.",
        ),
        (
            "Operations",
            "The service must be observable and reliable.",
        ),
        (
            "Finance",
            "Transaction records must be retained for audit.",
        ),
    ]

    print("Example competing needs:")
    for stakeholder, need in competing_needs:
        print(f"{stakeholder:<15}: {need}")

    print(
        "\nNegotiation questions:\n"
        "  1. What outcome is essential?\n"
        "  2. What constraint is mandatory?\n"
        "  3. What trade-off is acceptable?\n"
        "  4. What measurable target can satisfy the competing interests?\n"
        "  5. Who has decision authority?"
    )


# ============================================================================
# 43. REQUIREMENT FEASIBILITY
# ============================================================================

@dataclass
class FeasibilityAssessment:
    requirement_id: str
    technical: str
    operational: str
    financial: str
    legal: str
    schedule: str

    def print_assessment(self) -> None:
        print(f"Requirement: {self.requirement_id}")
        print(f"Technical  : {self.technical}")
        print(f"Operational: {self.operational}")
        print(f"Financial  : {self.financial}")
        print(f"Legal      : {self.legal}")
        print(f"Schedule   : {self.schedule}")


def demonstrate_feasibility() -> None:
    section("43. REQUIREMENT FEASIBILITY")

    assessment = FeasibilityAssessment(
        requirement_id="NFR-1000",
        technical="Feasible with current architecture.",
        operational="Requires monitoring and capacity planning.",
        financial="Within approved budget.",
        legal="Requires compliance review.",
        schedule="Possible if prioritized for the first release.",
    )

    assessment.print_assessment()


# ============================================================================
# 44. REQUIREMENT RISK
# ============================================================================

@dataclass
class RequirementRisk:
    risk_id: str
    description: str
    probability: float
    impact: float

    @property
    def exposure(self) -> float:
        return self.probability * self.impact


def demonstrate_requirement_risk() -> None:
    section("44. REQUIREMENT RISK ANALYSIS")

    risks = [
        RequirementRisk(
            "RR-001",
            "Payment provider does not support the required authorization flow.",
            0.3,
            9,
        ),
        RequirementRisk(
            "RR-002",
            "Performance target is underestimated.",
            0.5,
            7,
        ),
        RequirementRisk(
            "RR-003",
            "Stakeholder approval is delayed.",
            0.4,
            5,
        ),
    ]

    for risk in sorted(risks, key=lambda item: item.exposure, reverse=True):
        print(
            f"{risk.risk_id} | "
            f"P={risk.probability:.1f} | "
            f"I={risk.impact:.1f} | "
            f"Exposure={risk.exposure:.2f} | "
            f"{risk.description}"
        )


# ============================================================================
# 45. REQUIREMENT VERSIONING
# ============================================================================

@dataclass
class RequirementRevision:
    version: int
    changed_by: str
    reason: str
    old_text: str
    new_text: str


def demonstrate_versioning() -> None:
    section("45. REQUIREMENT VERSIONING")

    history = [
        RequirementRevision(
            1,
            "Product Owner",
            "Initial definition",
            "",
            "The system shall provide checkout.",
        ),
        RequirementRevision(
            2,
            "Product Owner",
            "Added payment condition",
            "The system shall provide checkout.",
            "The system shall allow an authenticated customer to submit a valid cart for payment authorization.",
        ),
        RequirementRevision(
            3,
            "Operations",
            "Added performance constraint",
            "The system shall allow an authenticated customer to submit a valid cart for payment authorization.",
            "95% of valid checkout requests shall complete within 2 seconds under the agreed load profile.",
        ),
    ]

    for revision in history:
        print(
            f"Version {revision.version} | "
            f"Changed by={revision.changed_by} | "
            f"Reason={revision.reason}"
        )


# ============================================================================
# 46. DOCUMENTATION STRUCTURE
# ============================================================================

def recommended_requirement_record() -> None:
    section("46. STRUCTURE OF A REQUIREMENT RECORD")

    fields = [
        "Requirement ID",
        "Title",
        "Description",
        "Type",
        "Business rationale",
        "Stakeholder / owner",
        "Source",
        "Priority",
        "Acceptance criteria",
        "Assumptions",
        "Constraints",
        "Dependencies",
        "Risks",
        "Status",
        "Version",
        "Related requirements",
        "Design references",
        "Implementation references",
        "Test references",
        "Approval information",
        "Change history",
    ]

    bullet(fields)


# ============================================================================
# 47. PRACTICAL END-TO-END REQUIREMENTS ANALYSIS
# ============================================================================

def end_to_end_analysis() -> None:
    section("47. END-TO-END REQUIREMENTS ANALYSIS")

    print("Business problem:")
    print(
        "Customers abandon an online checkout because the process is slow "
        "and payment failures are poorly communicated."
    )

    print("\nStep 1: Identify stakeholders")
    stakeholders = [
        "Business Sponsor",
        "Customer Experience",
        "Customers",
        "Engineering",
        "Operations",
        "Security",
        "Finance",
    ]
    bullet(stakeholders)

    print("\nStep 2: Define the business outcome")
    print("Reduce checkout abandonment by at least 10%.")

    print("\nStep 3: Elicit needs")
    bullet(
        [
            "Customers need a clear and responsive checkout.",
            "Support needs understandable failure messages.",
            "Operations needs measurable performance.",
            "Security needs protection of sensitive payment information.",
            "Finance needs reliable transaction records.",
        ]
    )

    print("\nStep 4: Convert needs into requirements")
    requirements = derive_requirements_from_problem()

    for requirement in requirements:
        print(
            f"{requirement.requirement_id} | "
            f"{requirement.requirement_type.value} | "
            f"{requirement.priority} | "
            f"{requirement.title}"
        )

    print("\nStep 5: Validate")
    validation_results = {}

    for requirement in requirements:
        issues = validate_requirement(requirement)
        validation_results[requirement.requirement_id] = issues

        status = "PASS" if not issues else "REVIEW"

        print(
            f"{requirement.requirement_id}: "
            f"{status}"
        )

        if issues:
            bullet(issues)

    print("\nStep 6: Establish traceability")
    matrix = TraceabilityMatrix()

    matrix.link(
        "BR-700",
        stakeholder="Business Sponsor",
        test="BUSINESS-001",
    )

    matrix.link(
        "FR-700",
        stakeholder="Customer",
        design="Checkout Service",
        implementation="CheckoutService.submit",
        test="AT-700",
    )

    matrix.link(
        "FR-701",
        stakeholder="Customer",
        design="Payment Error Handler",
        implementation="PaymentErrorHandler.handle",
        test="AT-701",
    )

    matrix.link(
        "NFR-700",
        stakeholder="Operations",
        design="API Gateway",
        implementation="Performance Configuration",
        test="PERF-700",
    )

    matrix.link(
        "SEC-700",
        stakeholder="Security Team",
        design="Logging Policy",
        implementation="LogSanitizer",
        test="SEC-700",
    )

    print(
        f"Traceability test coverage: "
        f"{matrix.coverage([r.requirement_id for r in requirements]):.1f}%"
    )

    print("\nStep 7: Prepare for implementation")
    bullet(
        [
            "Confirm unresolved questions.",
            "Confirm acceptance criteria.",
            "Confirm priority and scope.",
            "Confirm technical feasibility.",
            "Confirm dependencies.",
            "Confirm test strategy.",
            "Obtain required approval.",
        ]
    )


# ============================================================================
# 48. REQUIREMENT REVIEW WORKSHOP
# ============================================================================

def conduct_review(requirements: List[Requirement]) -> None:
    section("48. REQUIREMENT REVIEW WORKSHOP")

    print("Review participants:")
    bullet(
        [
            "Business representative",
            "Product/project representative",
            "Engineering representative",
            "Quality/test representative",
            "Security representative where relevant",
            "Operations representative where relevant",
        ]
    )

    print("\nReview questions for each requirement:")

    questions = [
        "Is the requirement necessary?",
        "Is the wording unambiguous?",
        "Is the requirement feasible?",
        "Is the requirement within scope?",
        "Is the source known?",
        "Is ownership clear?",
        "Is priority justified?",
        "Are dependencies known?",
        "Are failure and boundary conditions covered?",
        "Can acceptance be objectively demonstrated?",
        "Does the requirement conflict with another requirement?",
        "Is the requirement traceable?",
    ]

    bullet(questions)

    print(f"\nRequirements under review: {len(requirements)}")


# ============================================================================
# 49. PRODUCTION CONSIDERATIONS
# ============================================================================

def production_considerations() -> None:
    section("49. PRODUCTION REQUIREMENT CONSIDERATIONS")

    areas = {
        "Monitoring": [
            "Required metrics",
            "Logs",
            "Alerts",
            "Dashboards",
        ],
        "Reliability": [
            "Availability",
            "Failure handling",
            "Retry behavior",
            "Recovery objectives",
        ],
        "Security": [
            "Authentication",
            "Authorization",
            "Data protection",
            "Auditability",
        ],
        "Operations": [
            "Deployment",
            "Rollback",
            "Support procedures",
            "Capacity management",
        ],
        "Data": [
            "Retention",
            "Backup",
            "Recovery",
            "Migration",
            "Data quality",
        ],
    }

    for area, requirements in areas.items():
        print(f"\n{area}:")
        bullet(requirements)


# ============================================================================
# 50. REQUIREMENTS AND PROJECT MANAGEMENT
# ============================================================================

def project_management_relationships() -> None:
    section("50. REQUIREMENTS AND PROJECT MANAGEMENT")

    relationships = [
        (
            "Scope",
            "Requirements define what is included and excluded from the product or project outcome.",
        ),
        (
            "Schedule",
            "Requirement size, dependencies, and priority influence sequencing and delivery dates.",
        ),
        (
            "Cost",
            "Requirements drive implementation, infrastructure, testing, licensing, migration, and operational effort.",
        ),
        (
            "Quality",
            "Acceptance criteria and non-functional requirements establish measurable quality expectations.",
        ),
        (
            "Risk",
            "Unclear or unstable requirements create scope, technical, schedule, cost, and acceptance risks.",
        ),
        (
            "Stakeholders",
            "Stakeholder needs and decision authority influence requirement approval and prioritization.",
        ),
        (
            "Change control",
            "Changes to approved requirements can alter scope, cost, schedule, risk, and quality.",
        ),
    ]

    for area, relationship in relationships:
        print(f"{area:<16}: {relationship}")


# ============================================================================
# 51. MINI REQUIREMENT MANAGEMENT ENGINE
# ============================================================================

class RequirementManager:
    """
    Small integrated manager showing how requirement operations can be
    combined into a simple workflow.
    """

    def __init__(self) -> None:
        self.repository = RequirementsRepository()
        self.traceability = TraceabilityMatrix()
        self.change_requests: List[ChangeRequest] = []

    def register(self, requirement: Requirement) -> None:
        issues = validate_requirement(requirement)

        if issues:
            raise ValueError(
                f"Requirement {requirement.requirement_id} failed validation:\n"
                + "\n".join(f"- {issue}" for issue in issues)
            )

        self.repository.add(requirement)

    def approve(self, requirement_id: str) -> None:
        requirement = self.repository.get(requirement_id)

        if validate_requirement(requirement):
            raise ValueError(
                f"Requirement {requirement_id} cannot be approved until issues are resolved."
            )

        self.repository.approve(requirement_id)

    def link_test(
        self,
        requirement_id: str,
        test_id: str,
    ) -> None:
        self.repository.get(requirement_id)
        self.traceability.link(requirement_id, test=test_id)

    def submit_change(self, change: ChangeRequest) -> None:
        self.change_requests.append(change)

    def test_coverage(self) -> float:
        ids = [r.requirement_id for r in self.repository.all()]
        return self.traceability.coverage(ids)


def demonstrate_requirement_manager() -> None:
    section("51. MINI REQUIREMENT MANAGEMENT ENGINE")

    manager = RequirementManager()

    requirement = Requirement(
        "FR-1000",
        "Create order",
        (
            "The system shall create an order after successful payment "
            "authorization."
        ),
        RequirementType.FUNCTIONAL,
        "Customer",
        "Must",
        source="Checkout workshop",
        acceptance_criteria=[
            "Successful payment authorization creates one order.",
            "The order receives a unique identifier.",
        ],
    )

    manager.register(requirement)
    manager.approve("FR-1000")
    manager.link_test("FR-1000", "AT-1000")

    manager.submit_change(
        ChangeRequest(
            "CR-1000",
            "FR-1000",
            "Allow cancellation for 15 minutes after order creation.",
            "Reduce accidental-purchase support cases.",
            "Customer Experience",
            impact_areas=["Order service", "Payment", "UI", "Notifications"],
            estimated_effort=8,
            estimated_cost=2500,
        )
    )

    stored = manager.repository.get("FR-1000")

    print(f"ID      : {stored.requirement_id}")
    print(f"Status  : {stored.status}")
    print(f"Version : {stored.version}")
    print(f"Coverage: {manager.test_coverage():.1f}%")


# ============================================================================
# 52. ADVANCED: REQUIREMENT PRIORITY WITH MULTIPLE FACTORS
# ============================================================================

@dataclass
class AdvancedPriority:
    requirement_id: str
    business_value: float
    urgency: float
    risk_reduction: float
    regulatory_importance: float
    dependency_importance: float
    effort: float

    def score(self) -> float:
        weighted_value = (
            self.business_value * 0.30
            + self.urgency * 0.20
            + self.risk_reduction * 0.20
            + self.regulatory_importance * 0.20
            + self.dependency_importance * 0.10
        )

        return weighted_value / max(self.effort, 0.1)


def demonstrate_advanced_prioritization() -> None:
    section("52. ADVANCED PRIORITIZATION")

    priorities = [
        AdvancedPriority("FR-A", 9, 8, 5, 2, 8, 5),
        AdvancedPriority("SEC-A", 7, 8, 10, 10, 6, 4),
        AdvancedPriority("UX-A", 8, 5, 2, 0, 2, 3),
        AdvancedPriority("DATA-A", 6, 7, 8, 7, 9, 6),
    ]

    ranked = sorted(priorities, key=lambda item: item.score(), reverse=True)

    for item in ranked:
        print(
            f"{item.requirement_id}: "
            f"priority score={item.score():.2f}"
        )

    explain(
        "\nA weighted model makes prioritization more explicit, but the "
        "weights themselves are business decisions and should be reviewed "
        "with stakeholders."
    )


# ============================================================================
# 53. ADVANCED: REQUIREMENT CONSISTENCY
# ============================================================================

def detect_priority_inconsistencies(
    requirements: List[Requirement],
) -> List[str]:
    """
    Detect a simple policy violation:
    a regulatory or security requirement marked lower than Must.
    """
    issues = []

    for requirement in requirements:
        if requirement.requirement_type in {
            RequirementType.SECURITY,
            RequirementType.REGULATORY,
        } and requirement.priority != "Must":
            issues.append(
                f"{requirement.requirement_id} is {requirement.requirement_type.value} "
                f"but is prioritized as {requirement.priority}."
            )

    return issues


def demonstrate_consistency_rules() -> None:
    section("53. ADVANCED CONSISTENCY RULES")

    requirements = [
        Requirement(
            "SEC-900",
            "MFA",
            "Administrative access shall require multi-factor authentication.",
            RequirementType.SECURITY,
            "Security",
            "Should",
            acceptance_criteria=["Administrative access requires MFA."],
        ),
        Requirement(
            "FR-900",
            "Create order",
            "The system shall create an order after successful payment.",
            RequirementType.FUNCTIONAL,
            "Customer",
            "Must",
            acceptance_criteria=["Successful payment creates an order."],
        ),
    ]

    issues = detect_priority_inconsistencies(requirements)

    if issues:
        print("Potential policy inconsistencies:")
        bullet(issues)
    else:
        print("No inconsistencies detected.")


# ============================================================================
# 54. ADVANCED: REQUIREMENT COMPLETENESS CHECK
# ============================================================================

def completeness_questions(requirement: Requirement) -> List[str]:
    """
    Produce questions that reviewers can use to identify missing details.
    """
    questions = []

    if requirement.requirement_type == RequirementType.FUNCTIONAL:
        questions.extend(
            [
                "What triggers the behavior?",
                "What are valid inputs?",
                "What are invalid inputs?",
                "What is the expected output?",
                "What happens on failure?",
                "What permissions are required?",
            ]
        )

    if requirement.requirement_type == RequirementType.NON_FUNCTIONAL:
        questions.extend(
            [
                "What metric is being measured?",
                "What is the target?",
                "Under what load or conditions?",
                "What measurement method will be used?",
                "What is the acceptable threshold?",
            ]
        )

    if requirement.requirement_type == RequirementType.SECURITY:
        questions.extend(
            [
                "What asset is protected?",
                "Who can access it?",
                "What threat or risk is being addressed?",
                "What security control is required?",
                "How will compliance be verified?",
            ]
        )

    if requirement.requirement_type == RequirementType.DATA:
        questions.extend(
            [
                "What data is required?",
                "What is its source?",
                "What validation applies?",
                "How long is it retained?",
                "Who may access it?",
            ]
        )

    return questions


def demonstrate_completeness_questions() -> None:
    section("54. ADVANCED COMPLETENESS REVIEW")

    requirement = Requirement(
        "NFR-1001",
        "API performance",
        "95% of API requests shall complete within 500 milliseconds.",
        RequirementType.NON_FUNCTIONAL,
        "Operations",
        "Must",
    )

    print(requirement.description)
    print("\nReviewer questions:")
    bullet(completeness_questions(requirement))


# ============================================================================
# 55. REQUIREMENTS ANTI-PATTERNS
# ============================================================================

def requirement_anti_patterns() -> None:
    section("55. REQUIREMENTS ANTI-PATTERNS")

    anti_patterns = {
        "Solution disguised as requirement": (
            "A specific technology is mandated when the real need is a capability."
        ),
        "Everything is mandatory": (
            "No meaningful prioritization exists, making scope control difficult."
        ),
        "Hidden requirement": (
            "A stakeholder assumes a condition is obvious even though it is undocumented."
        ),
        "Ambiguous actor": (
            "A statement uses 'the user' when several user roles exist."
        ),
        "Unbounded requirement": (
            "Terms such as 'all', 'always', or 'unlimited' are used without realistic boundaries."
        ),
        "Test-last thinking": (
            "Acceptance criteria are invented only after implementation."
        ),
        "Copying old requirements blindly": (
            "Legacy requirements are reused without confirming that business conditions remain valid."
        ),
    }

    for name, meaning in anti_patterns.items():
        print(f"{name}: {meaning}")


# ============================================================================
# 56. REAL-WORLD APPLICATION AREAS
# ============================================================================

def application_domains() -> None:
    section("56. REAL-WORLD APPLICATIONS OF REQUIREMENTS")

    domains = {
        "Banking": [
            "Account opening",
            "Payments",
            "Fraud controls",
            "Regulatory reporting",
        ],
        "Healthcare": [
            "Patient workflows",
            "Clinical data",
            "Privacy",
            "Interoperability",
        ],
        "E-commerce": [
            "Catalog",
            "Checkout",
            "Payments",
            "Order management",
        ],
        "Manufacturing": [
            "Production planning",
            "Quality control",
            "Machine integration",
            "Safety requirements",
        ],
        "Software platforms": [
            "APIs",
            "Authentication",
            "Scalability",
            "Service reliability",
        ],
        "Government": [
            "Eligibility",
            "Case management",
            "Accessibility",
            "Legal compliance",
        ],
    }

    for domain, examples in domains.items():
        print(f"\n{domain}:")
        bullet(examples)


# ============================================================================
# 57. REQUIREMENTS CHECKLIST
# ============================================================================

def final_review_checklist() -> None:
    section("57. PRACTICAL REQUIREMENTS REVIEW CHECKLIST")

    checklist = [
        "The business problem is clearly stated.",
        "The intended business outcome is measurable where appropriate.",
        "Stakeholders have been identified.",
        "Requirement sources are recorded.",
        "Each important requirement has an owner.",
        "Requirements are uniquely identified.",
        "Requirement types are clear.",
        "Requirements are written in unambiguous language.",
        "Vague terms are defined or removed.",
        "Functional behavior is described clearly.",
        "Non-functional targets are measurable.",
        "Business rules are explicit.",
        "Assumptions are documented.",
        "Constraints are documented.",
        "Dependencies are documented.",
        "Risks associated with requirements are identified.",
        "Positive and negative scenarios are considered.",
        "Boundary conditions are considered.",
        "Acceptance criteria are defined.",
        "Requirements are prioritized.",
        "Conflicts and duplicates have been reviewed.",
        "Requirements are feasible.",
        "Requirements are traceable.",
        "Approved requirements are baselined.",
        "Changes follow change-control procedures.",
        "Tests trace back to requirements.",
        "Production and operational needs are addressed.",
    ]

    for index, item in enumerate(checklist, start=1):
        print(f"{index:02d}. [ ] {item}")


# ============================================================================
# 58. SELF-TESTS
# ============================================================================

def run_self_tests() -> None:
    section("58. SELF-TESTS")

    # Test the file-size business rule.
    assert validate_file_size(10) == "ACCEPT"
    assert "REJECT" in validate_file_size(10.01)
    assert "REJECT" in validate_file_size(0)

    # Test priority ordering.
    assert moscow_priority_score("Must") > moscow_priority_score("Should")
    assert moscow_priority_score("Should") > moscow_priority_score("Could")

    # Test a good requirement.
    good = Requirement(
        "TEST-001",
        "API latency",
        "95% of API requests shall complete within 1 second.",
        RequirementType.NON_FUNCTIONAL,
        "Operations",
        "Must",
        acceptance_criteria=["Performance test validates the target."],
    )

    assert good.is_testable()
    assert good.has_acceptance_criteria()
    assert not validate_requirement(good)

    # Test a bad requirement.
    bad = Requirement(
        "",
        "",
        "The system should be fast and user-friendly.",
        RequirementType.FUNCTIONAL,
        "",
        "Important",
    )

    assert validate_requirement(bad)

    # Test traceability.
    matrix = TraceabilityMatrix()
    matrix.link("TEST-001", test="TC-001")
    assert matrix.coverage(["TEST-001"]) == 100.0

    print("All self-tests passed.")


# ============================================================================
# 59. MAIN EDUCATIONAL PROGRAM
# ============================================================================

def main() -> None:
    """
    Execute the complete tutorial.

    The sequence follows a beginner-to-advanced learning progression:
    concept → classification → elicitation → quality → modeling →
    prioritization → traceability → validation → change control →
    metrics → advanced analysis → practical workflow.
    """

    demonstrate_basics()
    demonstrate_requirement_types()
    requirements_lifecycle()
    elicitation_methods()
    requirement_questions()
    demonstrate_bad_requirements()
    demonstrate_quality()
    functional_requirement_example()
    non_functional_requirement_example()
    demonstrate_project_context()
    demonstrate_decomposition()
    demonstrate_user_story()
    demonstrate_acceptance_criteria()
    demonstrate_given_when_then()
    demonstrate_use_case()
    demonstrate_moscow()
    demonstrate_value_effort()
    demonstrate_conflicts()
    demonstrate_traceability()
    demonstrate_repository()
    demonstrate_change_management()
    demonstrate_baseline()
    demonstrate_status_model()
    demonstrate_metrics()
    demonstrate_duplicate_detection()
    demonstrate_orphan_detection()
    demonstrate_coverage()
    demonstrate_edge_cases()
    demonstrate_boundary_analysis()
    demonstrate_business_rules()
    demonstrate_validation()
    demonstrate_requirement_derivation()
    demonstrate_dependencies()
    security_questions()
    demonstrate_performance_requirements()
    demonstrate_requirement_testing()
    common_mistakes()
    agile_requirements()
    demonstrate_story_refinement()
    compare_delivery_approaches()
    demonstrate_scope()
    demonstrate_negotiation()
    demonstrate_feasibility()
    demonstrate_requirement_risk()
    demonstrate_versioning()
    recommended_requirement_record()
    end_to_end_analysis()
    conduct_review(derive_requirements_from_problem())
    production_considerations()
    project_management_relationships()
    demonstrate_requirement_manager()
    demonstrate_advanced_prioritization()
    demonstrate_consistency_rules()
    demonstrate_completeness_questions()
    requirement_anti_patterns()
    application_domains()
    final_review_checklist()
    run_self_tests()


if __name__ == "__main__":
    main()
