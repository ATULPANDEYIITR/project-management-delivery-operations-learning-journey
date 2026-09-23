"""
Requirements Collection: From Beginner Concepts to an Advanced Requirements System

This standalone script teaches requirements collection through executable examples.
It progresses from basic terminology and requirement classification to:
- stakeholder identification
- interviews and questionnaires
- observation
- workshops
- user stories
- use cases
- acceptance criteria
- functional and non-functional requirements
- requirement validation
- prioritization
- traceability
- change management
- conflict detection
- quality scoring
- a complete requirements repository
- an industry-style requirements collection workflow

The examples use only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Set, Tuple
import re
from collections import defaultdict
from datetime import datetime


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

print("=" * 80)
print("REQUIREMENTS COLLECTION")
print("=" * 80)


def explain_fundamentals() -> None:
    """
    Basic terminology used throughout the script.

    A requirement is a documented need, capability, condition, or constraint
    that a system or project is expected to satisfy.

    Requirements collection is the systematic process of discovering,
    clarifying, documenting, validating, prioritizing, and organizing those
    requirements with relevant stakeholders.
    """
    concepts = {
        "Requirement": "A documented need, capability, condition, or constraint.",
        "Stakeholder": "A person or organization affected by, using, funding, managing, or regulating the system.",
        "Functional requirement": "Describes what the system must do.",
        "Non-functional requirement": "Describes a quality, constraint, or characteristic of the system.",
        "Business requirement": "Describes the business outcome or organizational objective.",
        "User requirement": "Describes a user need in language appropriate for users.",
        "System requirement": "Provides detailed technical behavior or constraints.",
        "Acceptance criterion": "A condition used to determine whether a requirement has been satisfied.",
        "Assumption": "Something treated as true for planning purposes but not yet fully verified.",
        "Constraint": "A limitation imposed on the solution or project.",
        "Dependency": "An external condition, component, team, or system required for delivery.",
        "Traceability": "The ability to connect business needs to requirements, implementation, and verification.",
        "Scope": "The boundaries of what the project will and will not address.",
    }

    for name, definition in concepts.items():
        print(f"{name}: {definition}")


explain_fundamentals()


# ---------------------------------------------------------------------------
# 2. REQUIREMENT CLASSIFICATION
# ---------------------------------------------------------------------------

class RequirementType(Enum):
    BUSINESS = "Business"
    USER = "User"
    FUNCTIONAL = "Functional"
    NON_FUNCTIONAL = "Non-functional"
    DATA = "Data"
    INTERFACE = "Interface"
    SECURITY = "Security"
    REGULATORY = "Regulatory"
    CONSTRAINT = "Constraint"


class Priority(Enum):
    MUST = "Must"
    SHOULD = "Should"
    COULD = "Could"
    WONT = "Won't"


@dataclass
class Requirement:
    requirement_id: str
    title: str
    description: str
    requirement_type: RequirementType
    priority: Priority
    source: str
    stakeholder_ids: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    status: str = "Draft"
    version: int = 1

    def is_complete(self) -> bool:
        """A practical completeness check."""
        return all(
            [
                self.requirement_id.strip(),
                self.title.strip(),
                self.description.strip(),
                self.source.strip(),
                bool(self.acceptance_criteria),
            ]
        )

    def display(self) -> None:
        print(f"\n[{self.requirement_id}] {self.title}")
        print(f"Type: {self.requirement_type.value}")
        print(f"Priority: {self.priority.value}")
        print(f"Source: {self.source}")
        print(f"Status: {self.status}")
        print(f"Description: {self.description}")
        print("Acceptance criteria:")
        for criterion in self.acceptance_criteria:
            print(f"  - {criterion}")


# ---------------------------------------------------------------------------
# 3. STAKEHOLDER IDENTIFICATION
# ---------------------------------------------------------------------------

@dataclass
class Stakeholder:
    stakeholder_id: str
    name: str
    role: str
    influence: int
    interest: int
    needs: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)

    def engagement_level(self) -> str:
        """
        Simple stakeholder mapping.

        Influence and interest are scored from 1 to 5.
        """
        if self.influence >= 4 and self.interest >= 4:
            return "Manage closely"
        if self.influence >= 4:
            return "Keep satisfied"
        if self.interest >= 4:
            return "Keep informed"
        return "Monitor"


stakeholders = [
    Stakeholder(
        "STK-001",
        "Operations Manager",
        "Business Owner",
        5,
        5,
        ["Faster processing", "Operational visibility"],
        ["Manual errors", "Delays"],
    ),
    Stakeholder(
        "STK-002",
        "Customer",
        "End User",
        3,
        5,
        ["Simple interface", "Fast service"],
        ["Complex workflows"],
    ),
    Stakeholder(
        "STK-003",
        "Security Officer",
        "Security",
        5,
        4,
        ["Strong authentication", "Auditability"],
        ["Unauthorized access"],
    ),
]

print("\nStakeholder analysis:")
for stakeholder in stakeholders:
    print(
        f"{stakeholder.name}: "
        f"influence={stakeholder.influence}, "
        f"interest={stakeholder.interest}, "
        f"engagement={stakeholder.engagement_level()}"
    )


# ---------------------------------------------------------------------------
# 4. REQUIREMENTS ELICITATION TECHNIQUES
# ---------------------------------------------------------------------------

def interview_questions(role: str) -> List[str]:
    """
    Generate structured interview questions.

    Interviews are useful for discovering goals, pain points, exceptions,
    constraints, current processes, and desired outcomes.
    """
    common = [
        "What problem are you trying to solve?",
        "Who experiences this problem?",
        "What happens today?",
        "What causes the greatest difficulty?",
        "What information is required?",
        "What should happen in an exceptional case?",
        "How would you determine that the solution is successful?",
        "What constraints must the solution respect?",
    ]

    role_specific = {
        "Business Owner": [
            "Which business outcome has the highest priority?",
            "Which metrics should improve?",
            "What deadlines or regulatory obligations apply?",
        ],
        "End User": [
            "Which tasks do you perform most frequently?",
            "Which steps are confusing or time-consuming?",
            "What would make the workflow easier?",
        ],
        "Security": [
            "Which assets require protection?",
            "What access controls are required?",
            "What audit evidence must be retained?",
        ],
    }

    return common + role_specific.get(role, [])


print("\nInterview questions for the business owner:")
for question in interview_questions("Business Owner"):
    print(f"- {question}")


def classify_elicitation_method(method: str) -> Tuple[str, str]:
    """
    Compare common requirements collection methods.
    """
    methods = {
        "interview": (
            "Deep individual understanding",
            "Can be time-consuming and influenced by participant bias",
        ),
        "questionnaire": (
            "Efficiently collects structured input from many people",
            "Provides less opportunity for clarification",
        ),
        "workshop": (
            "Rapidly resolves cross-stakeholder differences",
            "Requires careful facilitation",
        ),
        "observation": (
            "Reveals actual behavior and workarounds",
            "Observed behavior may differ from unusual situations",
        ),
        "document_analysis": (
            "Uses existing policies, contracts, and procedures",
            "Documents may be outdated",
        ),
        "prototype": (
            "Makes unclear interface expectations visible",
            "Users may focus on appearance rather than underlying requirements",
        ),
    }
    return methods.get(method.lower(), ("Unknown", "Unknown"))


for method in ["interview", "questionnaire", "workshop", "observation"]:
    strength, limitation = classify_elicitation_method(method)
    print(f"\n{method.title()}:")
    print(f"  Strength: {strength}")
    print(f"  Limitation: {limitation}")


# ---------------------------------------------------------------------------
# 5. TURNING RAW STAKEHOLDER STATEMENTS INTO REQUIREMENTS
# ---------------------------------------------------------------------------

raw_statements = [
    "Customers need the application to be faster.",
    "Managers want to see what is happening.",
    "Users should not have to remember complicated passwords.",
    "We cannot expose customer information to unauthorized people.",
]

def convert_statement_to_requirement(statement: str, number: int) -> Requirement:
    """
    A basic demonstration of transforming informal statements into structured
    requirement records.

    Real projects require human validation rather than blindly converting
    stakeholder statements through automation.
    """
    lower = statement.lower()

    if "faster" in lower:
        req_type = RequirementType.NON_FUNCTIONAL
        title = "Responsive customer operations"
        description = (
            "The system shall complete the defined customer operation "
            "within the agreed response-time target under the specified load."
        )
        criterion = "Response time shall be measured under an agreed workload."
    elif "see what is happening" in lower:
        req_type = RequirementType.FUNCTIONAL
        title = "Operational dashboard"
        description = (
            "The system shall provide authorized managers with an operational "
            "dashboard showing current process status."
        )
        criterion = "An authorized manager can view current operational status."
    elif "password" in lower:
        req_type = RequirementType.SECURITY
        title = "User authentication"
        description = (
            "The system shall provide an authentication mechanism that meets "
            "the organization's approved authentication policy."
        )
        criterion = "Authentication shall enforce the approved policy."
    else:
        req_type = RequirementType.SECURITY
        title = "Access control"
        description = (
            "The system shall prevent unauthorized users from accessing "
            "protected customer information."
        )
        criterion = "Unauthorized access attempts shall be denied and recorded."

    return Requirement(
        requirement_id=f"REQ-{number:03d}",
        title=title,
        description=description,
        requirement_type=req_type,
        priority=Priority.MUST,
        source="Stakeholder statement",
        acceptance_criteria=[criterion],
    )


requirements = [
    convert_statement_to_requirement(statement, index)
    for index, statement in enumerate(raw_statements, start=1)
]

for requirement in requirements:
    requirement.display()


# ---------------------------------------------------------------------------
# 6. USER STORIES AND ACCEPTANCE CRITERIA
# ---------------------------------------------------------------------------

@dataclass
class UserStory:
    story_id: str
    role: str
    action: str
    benefit: str
    acceptance_criteria: List[str]

    def format_story(self) -> str:
        return (
            f"As a {self.role}, I want to {self.action}, "
            f"so that {self.benefit}."
        )


story = UserStory(
    "US-001",
    "customer",
    "search for an existing application",
    "I can quickly find its current status",
    [
        "Given an existing application, when the customer searches by its identifier, "
        "then the current status is displayed.",
        "If no matching application exists, the system displays a clear not-found message.",
    ],
)

print("\nUser story:")
print(story.format_story())

print("Acceptance criteria:")
for criterion in story.acceptance_criteria:
    print(f"- {criterion}")


# ---------------------------------------------------------------------------
# 7. INVEST-STYLE USER STORY QUALITY CHECK
# ---------------------------------------------------------------------------

def evaluate_user_story(story: UserStory) -> Dict[str, bool]:
    """
    A practical checklist inspired by common user-story quality principles.

    The checks are intentionally heuristic. They support discussion rather
    than replacing stakeholder review.
    """
    return {
        "has_role": bool(story.role.strip()),
        "has_action": bool(story.action.strip()),
        "has_benefit": bool(story.benefit.strip()),
        "has_acceptance_criteria": bool(story.acceptance_criteria),
        "reasonably_small": len(story.action.split()) <= 15,
        "testable": len(story.acceptance_criteria) > 0,
    }


print("\nUser story quality checks:")
for check, passed in evaluate_user_story(story).items():
    print(f"{check}: {'PASS' if passed else 'FAIL'}")


# ---------------------------------------------------------------------------
# 8. USE CASE MODEL
# ---------------------------------------------------------------------------

@dataclass
class UseCase:
    use_case_id: str
    name: str
    primary_actor: str
    preconditions: List[str]
    main_flow: List[str]
    alternate_flows: List[str]
    postconditions: List[str]

    def validate(self) -> List[str]:
        errors = []

        if not self.name.strip():
            errors.append("Use case name is missing.")
        if not self.primary_actor.strip():
            errors.append("Primary actor is missing.")
        if not self.preconditions:
            errors.append("At least one precondition should be documented.")
        if not self.main_flow:
            errors.append("Main flow is missing.")
        if not self.postconditions:
            errors.append("Postconditions are missing.")

        return errors


use_case = UseCase(
    "UC-001",
    "Submit Application",
    "Customer",
    ["Customer is authenticated.", "Required application data is available."],
    [
        "Customer opens the application form.",
        "System displays required fields.",
        "Customer enters information.",
        "System validates the information.",
        "System stores the application.",
        "System returns a confirmation identifier.",
    ],
    [
        "If validation fails, the system identifies the invalid fields.",
        "If storage fails, the system does not report false success.",
    ],
    ["Application is stored with a unique identifier."],
)

print("\nUse case validation:", use_case.validate())


# ---------------------------------------------------------------------------
# 9. REQUIREMENT QUALITY VALIDATION
# ---------------------------------------------------------------------------

AMBIGUOUS_TERMS = {
    "fast",
    "easy",
    "user-friendly",
    "simple",
    "quick",
    "appropriate",
    "reasonable",
    "efficient",
    "soon",
    "etc",
    "and so on",
}

def detect_ambiguous_terms(text: str) -> Set[str]:
    normalized = re.sub(r"[^a-z0-9\s-]", " ", text.lower())
    words = set(normalized.split())
    return words.intersection(AMBIGUOUS_TERMS)


def validate_requirement(requirement: Requirement) -> List[str]:
    issues = []

    if not requirement.title.strip():
        issues.append("Missing title.")

    if len(requirement.description.split()) < 5:
        issues.append("Description may be too short.")

    ambiguous = detect_ambiguous_terms(requirement.description)
    if ambiguous:
        issues.append(
            "Potentially ambiguous terms: " + ", ".join(sorted(ambiguous))
        )

    if not requirement.acceptance_criteria:
        issues.append("No acceptance criteria.")

    if not requirement.source:
        issues.append("Missing source.")

    if not requirement.stakeholder_ids:
        issues.append("No stakeholder linkage.")

    return issues


for requirement in requirements:
    requirement.stakeholder_ids = ["STK-001"]
    issues = validate_requirement(requirement)
    print(
        f"\nQuality validation for {requirement.requirement_id}: "
        f"{'PASS' if not issues else 'REVIEW'}"
    )
    for issue in issues:
        print(f"  - {issue}")


# ---------------------------------------------------------------------------
# 10. REQUIREMENTS SHOULD BE TESTABLE AND MEASURABLE
# ---------------------------------------------------------------------------

bad_requirement = Requirement(
    "REQ-BAD",
    "Fast system",
    "The system shall be fast and easy to use.",
    RequirementType.NON_FUNCTIONAL,
    Priority.MUST,
    "Interview",
)

print("\nBad requirement validation:")
for issue in validate_requirement(bad_requirement):
    print(f"- {issue}")

good_requirement = Requirement(
    "REQ-GOOD",
    "Response time",
    "The system shall return the application search result within 2 seconds "
    "for 95% of requests under the agreed production workload.",
    RequirementType.NON_FUNCTIONAL,
    Priority.MUST,
    "Performance workshop",
    acceptance_criteria=[
        "A performance test measures at least 95% of searches at or below 2 seconds.",
        "The workload used for the test is documented.",
    ],
    stakeholder_ids=["STK-001"],
)

print("\nImproved requirement validation:")
for issue in validate_requirement(good_requirement):
    print(f"- {issue}")


# ---------------------------------------------------------------------------
# 11. PRIORITIZATION
# ---------------------------------------------------------------------------

@dataclass
class PrioritizationScore:
    value: int
    business_value: int
    urgency: int
    risk_reduction: int
    dependency_impact: int

    @property
    def total(self) -> int:
        return (
            self.business_value
            + self.urgency
            + self.risk_reduction
            + self.dependency_impact
        )


scores = {
    "REQ-001": PrioritizationScore(1, 5, 5, 3, 4),
    "REQ-002": PrioritizationScore(2, 4, 3, 2, 5),
    "REQ-003": PrioritizationScore(3, 5, 5, 5, 5),
}

print("\nPrioritization scoring:")
for requirement_id, score in scores.items():
    print(
        f"{requirement_id}: "
        f"business={score.business_value}, "
        f"urgency={score.urgency}, "
        f"risk={score.risk_reduction}, "
        f"dependency={score.dependency_impact}, "
        f"total={score.total}"
    )

print(
    "\nPrioritization scores are decision-support evidence. "
    "Stakeholders must define the scoring criteria and resolve conflicts."
)


# ---------------------------------------------------------------------------
# 12. REQUIREMENT CONFLICT DETECTION
# ---------------------------------------------------------------------------

@dataclass
class Constraint:
    constraint_id: str
    description: str


constraints = [
    Constraint("CON-001", "Customer information must be protected."),
    Constraint("CON-002", "Authorized managers require access to operational data."),
    Constraint("CON-003", "Sensitive personal information must not be visible to unauthorized roles."),
]

def detect_potential_conflict(
    requirement_a: Requirement,
    requirement_b: Requirement,
) -> Optional[str]:
    """
    Demonstrates a simple semantic conflict heuristic.

    This is not a replacement for stakeholder analysis. Natural-language
    conflict detection requires context that cannot be safely inferred from
    keywords alone.
    """
    a = requirement_a.description.lower()
    b = requirement_b.description.lower()

    access_a = "access" in a
    prevent_a = "prevent" in a or "unauthorized" in a
    access_b = "access" in b
    prevent_b = "prevent" in b or "unauthorized" in b

    if (access_a and prevent_b) or (access_b and prevent_a):
        return (
            "Potential access-control conflict. Clarify authorized roles, "
            "data scope, and conditions."
        )

    return None


r1 = Requirement(
    "REQ-A",
    "Manager access",
    "Managers shall have access to operational customer data.",
    RequirementType.FUNCTIONAL,
    Priority.MUST,
    "Manager interview",
    acceptance_criteria=["Authorized managers can access required operational data."],
)

r2 = Requirement(
    "REQ-B",
    "Customer protection",
    "The system shall prevent unauthorized access to customer data.",
    RequirementType.SECURITY,
    Priority.MUST,
    "Security policy",
    acceptance_criteria=["Unauthorized users are denied access."],
)

print("\nConflict analysis:")
print(detect_potential_conflict(r1, r2) or "No potential conflict detected.")


# ---------------------------------------------------------------------------
# 13. TRACEABILITY MATRIX
# ---------------------------------------------------------------------------

@dataclass
class TraceabilityMatrix:
    business_to_user: Dict[str, Set[str]] = field(default_factory=dict)
    user_to_system: Dict[str, Set[str]] = field(default_factory=dict)
    requirement_to_test: Dict[str, Set[str]] = field(default_factory=dict)

    def add_business_mapping(self, business_id: str, user_id: str) -> None:
        self.business_to_user.setdefault(business_id, set()).add(user_id)

    def add_user_mapping(self, user_id: str, requirement_id: str) -> None:
        self.user_to_system.setdefault(user_id, set()).add(requirement_id)

    def add_test_mapping(self, requirement_id: str, test_id: str) -> None:
        self.requirement_to_test.setdefault(requirement_id, set()).add(test_id)

    def report_unverified_requirements(
        self, requirement_ids: Iterable[str]
    ) -> List[str]:
        return [
            requirement_id
            for requirement_id in requirement_ids
            if not self.requirement_to_test.get(requirement_id)
        ]


traceability = TraceabilityMatrix()
traceability.add_business_mapping("BUS-001", "US-001")
traceability.add_user_mapping("US-001", "REQ-001")
traceability.add_test_mapping("REQ-001", "TEST-001")

print("\nTraceability:")
print(traceability.business_to_user)
print(traceability.user_to_system)
print(traceability.requirement_to_test)


# ---------------------------------------------------------------------------
# 14. REQUIREMENTS REPOSITORY
# ---------------------------------------------------------------------------

class RequirementsRepository:
    """
    In-memory requirements repository.

    A production system would normally persist records in a database or
    controlled document repository and provide authentication, authorization,
    versioning, audit history, and concurrency control.
    """

    def __init__(self) -> None:
        self.requirements: Dict[str, Requirement] = {}
        self.history: Dict[str, List[Requirement]] = defaultdict(list)

    def add(self, requirement: Requirement) -> None:
        if requirement.requirement_id in self.requirements:
            raise ValueError(
                f"Requirement {requirement.requirement_id} already exists."
            )

        self.requirements[requirement.requirement_id] = requirement

    def get(self, requirement_id: str) -> Requirement:
        try:
            return self.requirements[requirement_id]
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

        # Store a snapshot before modifying the current version.
        self.history[requirement_id].append(
            Requirement(
                requirement.requirement_id,
                requirement.title,
                requirement.description,
                requirement.requirement_type,
                requirement.priority,
                requirement.source,
                list(requirement.stakeholder_ids),
                list(requirement.acceptance_criteria),
                list(requirement.dependencies),
                list(requirement.assumptions),
                requirement.status,
                requirement.version,
            )
        )

        requirement.description = new_description
        requirement.version += 1
        requirement.status = "Changed"

    def filter_by_type(
        self,
        requirement_type: RequirementType,
    ) -> List[Requirement]:
        return [
            requirement
            for requirement in self.requirements.values()
            if requirement.requirement_type == requirement_type
        ]

    def filter_by_priority(
        self,
        priority: Priority,
    ) -> List[Requirement]:
        return [
            requirement
            for requirement in self.requirements.values()
            if requirement.priority == priority
        ]


repository = RequirementsRepository()

for requirement in requirements:
    repository.add(requirement)

print("\nRepository contents:")
for requirement in repository.requirements.values():
    print(
        f"{requirement.requirement_id}: "
        f"{requirement.title} | "
        f"{requirement.status} | "
        f"version={requirement.version}"
    )

repository.update_description(
    "REQ-001",
    "The system shall return customer operation results within "
    "2 seconds for 95% of requests under the agreed workload.",
)

print("\nVersioned change:")
changed = repository.get("REQ-001")
print(changed.description)
print("Current version:", changed.version)
print("Previous versions:", len(repository.history["REQ-001"]))


# ---------------------------------------------------------------------------
# 15. REQUIREMENTS CHANGE MANAGEMENT
# ---------------------------------------------------------------------------

@dataclass
class ChangeRequest:
    change_id: str
    requirement_id: str
    requested_by: str
    reason: str
    impact: str
    status: str = "Pending"

    def approve(self) -> None:
        self.status = "Approved"

    def reject(self) -> None:
        self.status = "Rejected"


change_request = ChangeRequest(
    "CR-001",
    "REQ-001",
    "Operations Manager",
    "Customer volume has increased and the original response target is insufficient.",
    "May require infrastructure and database optimization.",
)

print("\nChange request:")
print(change_request)
change_request.approve()
print("After review:", change_request.status)


# ---------------------------------------------------------------------------
# 16. SCOPE MANAGEMENT
# ---------------------------------------------------------------------------

@dataclass
class ScopeBoundary:
    in_scope: Set[str]
    out_of_scope: Set[str]

    def classify(self, item: str) -> str:
        if item in self.in_scope:
            return "In scope"
        if item in self.out_of_scope:
            return "Out of scope"
        return "Unclassified"


scope = ScopeBoundary(
    in_scope={
        "Customer application submission",
        "Application status tracking",
        "Manager dashboard",
        "Authentication",
    },
    out_of_scope={
        "International expansion",
        "Unrelated accounting system replacement",
    },
)

print("\nScope classification:")
for item in [
    "Customer application submission",
    "International expansion",
    "Mobile game integration",
]:
    print(f"{item}: {scope.classify(item)}")


# ---------------------------------------------------------------------------
# 17. REQUIREMENTS BASELINE
# ---------------------------------------------------------------------------

def create_baseline(
    repository: RequirementsRepository,
) -> Dict[str, Tuple[str, int, str]]:
    """
    Creates a lightweight baseline containing stable identifiers, versions,
    and descriptions.

    A formal baseline should normally be stored in controlled configuration
    management infrastructure.
    """
    return {
        requirement_id: (
            requirement.title,
            requirement.version,
            requirement.description,
        )
        for requirement_id, requirement in repository.requirements.items()
    }


baseline = create_baseline(repository)

print("\nBaseline:")
for requirement_id, record in baseline.items():
    print(requirement_id, "->", record)


# ---------------------------------------------------------------------------
# 18. REQUIREMENTS METRICS
# ---------------------------------------------------------------------------

def requirement_metrics(
    repository: RequirementsRepository,
) -> Dict[str, float]:
    items = list(repository.requirements.values())

    if not items:
        return {
            "count": 0,
            "complete_percentage": 0.0,
            "must_percentage": 0.0,
        }

    complete_count = sum(item.is_complete() for item in items)
    must_count = sum(item.priority == Priority.MUST for item in items)

    return {
        "count": float(len(items)),
        "complete_percentage": complete_count / len(items) * 100,
        "must_percentage": must_count / len(items) * 100,
    }


print("\nRequirements metrics:")
for metric, value in requirement_metrics(repository).items():
    print(f"{metric}: {value:.2f}")


# ---------------------------------------------------------------------------
# 19. ADVANCED REQUIREMENTS COLLECTION WORKFLOW
# ---------------------------------------------------------------------------

class RequirementsCollectionWorkflow:
    """
    A simplified end-to-end workflow.

    The workflow emphasizes that requirements collection is iterative rather
    than a single meeting followed by documentation.
    """

    def __init__(self) -> None:
        self.discovery_notes: List[str] = []
        self.requirements: List[Requirement] = []
        self.validated: Set[str] = set()
        self.approved: Set[str] = set()

    def capture_note(self, note: str) -> None:
        if not note.strip():
            raise ValueError("Discovery note cannot be empty.")
        self.discovery_notes.append(note.strip())

    def add_requirement(self, requirement: Requirement) -> None:
        self.requirements.append(requirement)

    def validate_all(self) -> Dict[str, List[str]]:
        results = {}

        for requirement in self.requirements:
            issues = validate_requirement(requirement)
            results[requirement.requirement_id] = issues

            if not issues:
                self.validated.add(requirement.requirement_id)

        return results

    def approve(self, requirement_id: str) -> None:
        if requirement_id not in self.validated:
            raise ValueError(
                f"{requirement_id} must pass validation before approval."
            )

        self.approved.add(requirement_id)

    def status(self) -> Dict[str, int]:
        return {
            "discovery_notes": len(self.discovery_notes),
            "requirements": len(self.requirements),
            "validated": len(self.validated),
            "approved": len(self.approved),
        }


workflow = RequirementsCollectionWorkflow()

workflow.capture_note(
    "Customers currently call support because application status is not visible."
)
workflow.capture_note(
    "Operations staff manually compile status information each morning."
)
workflow.capture_note(
    "Security requires authenticated access to customer information."
)

workflow.add_requirement(
    Requirement(
        "WF-001",
        "Application status search",
        "The system shall allow an authenticated customer to search for "
        "an application using its unique identifier.",
        RequirementType.FUNCTIONAL,
        Priority.MUST,
        "Customer interview",
        stakeholder_ids=["STK-002"],
        acceptance_criteria=[
            "An authenticated customer can submit a valid application identifier.",
            "The system displays the corresponding current status.",
            "An invalid identifier produces a controlled not-found response.",
        ],
    )
)

workflow.add_requirement(
    Requirement(
        "WF-002",
        "Access protection",
        "The system shall restrict application information to authenticated "
        "users who are authorized to access the requested record.",
        RequirementType.SECURITY,
        Priority.MUST,
        "Security workshop",
        stakeholder_ids=["STK-003"],
        acceptance_criteria=[
            "Unauthenticated requests are rejected.",
            "Authenticated users without authorization cannot retrieve protected records.",
            "Access-denied events are recorded in the audit log.",
        ],
    )
)

validation_results = workflow.validate_all()

print("\nEnd-to-end workflow:")
for requirement_id, issues in validation_results.items():
    print(
        requirement_id,
        "PASS" if not issues else f"REVIEW: {issues}",
    )

for requirement_id in sorted(workflow.validated):
    workflow.approve(requirement_id)

print("Workflow status:", workflow.status())


# ---------------------------------------------------------------------------
# 20. EDGE CASES AND FAILURE CONDITIONS
# ---------------------------------------------------------------------------

def safely_add_requirement(
    repository: RequirementsRepository,
    requirement: Requirement,
) -> str:
    try:
        repository.add(requirement)
        return "Requirement added."
    except ValueError as error:
        return f"Rejected: {error}"


duplicate = Requirement(
    "REQ-001",
    "Duplicate",
    "This requirement intentionally duplicates an existing identifier.",
    RequirementType.FUNCTIONAL,
    Priority.CANONICAL if False else Priority.MUST,
    "Test",
    acceptance_criteria=["Test criterion"],
)

print("\nDuplicate identifier handling:")
print(safely_add_requirement(repository, duplicate))


try:
    repository.get("REQ-NOT-FOUND")
except KeyError as error:
    print("\nMissing requirement handling:")
    print(error)


# ---------------------------------------------------------------------------
# 21. PERFORMANCE CONSIDERATIONS
# ---------------------------------------------------------------------------

def linear_search(
    requirements: List[Requirement],
    requirement_id: str,
) -> Optional[Requirement]:
    """
    O(n) lookup through a list.
    """
    for requirement in requirements:
        if requirement.requirement_id == requirement_id:
            return requirement
    return None


def indexed_search(
    requirements: Dict[str, Requirement],
    requirement_id: str,
) -> Optional[Requirement]:
    """
    Average O(1) lookup through a dictionary.
    """
    return requirements.get(requirement_id)


print("\nLookup comparison:")
print(
    "List-based lookup: O(n), suitable for small collections or ordered scans."
)
print(
    "Dictionary-based lookup: average O(1), preferable for identifier-based retrieval."
)
print(
    "For large repositories, database indexing, pagination, caching, and "
    "full-text search may become important."
)


# ---------------------------------------------------------------------------
# 22. SECURITY CONSIDERATIONS
# ---------------------------------------------------------------------------

security_principles = [
    "Do not store unnecessary sensitive stakeholder information.",
    "Restrict who can create, modify, approve, and delete requirements.",
    "Maintain audit history for material requirement changes.",
    "Protect requirements containing confidential business information.",
    "Separate authentication from authorization.",
    "Validate imported requirement data.",
    "Avoid placing credentials, API keys, or secrets inside requirement documents.",
    "Define retention and access policies for interview and workshop records.",
]

print("\nSecurity considerations:")
for principle in security_principles:
    print(f"- {principle}")


# ---------------------------------------------------------------------------
# 23. PRACTICAL REQUIREMENTS COLLECTION CHECKLIST
# ---------------------------------------------------------------------------

collection_checklist = [
    "Define the business problem.",
    "Identify stakeholders.",
    "Understand the current process.",
    "Collect stakeholder goals and pain points.",
    "Identify business rules.",
    "Identify functional requirements.",
    "Identify non-functional requirements.",
    "Identify data requirements.",
    "Identify integration and interface requirements.",
    "Identify legal, regulatory, and security constraints.",
    "Record assumptions and dependencies.",
    "Write testable requirements.",
    "Resolve contradictions and ambiguity.",
    "Prioritize requirements using agreed criteria.",
    "Validate requirements with stakeholders.",
    "Create traceability.",
    "Baseline approved requirements.",
    "Control subsequent changes.",
]

print("\nRequirements collection checklist:")
for number, item in enumerate(collection_checklist, start=1):
    print(f"{number:02d}. {item}")


# ---------------------------------------------------------------------------
# 24. COMPLETE MINI CASE STUDY OUTPUT
# ---------------------------------------------------------------------------

print("\n" + "=" * 80)
print("MINI CASE STUDY: DIGITAL APPLICATION MANAGEMENT SYSTEM")
print("=" * 80)

case_study_requirements = [
    Requirement(
        "CAS-001",
        "Application submission",
        "The system shall allow an authenticated customer to submit a completed application.",
        RequirementType.FUNCTIONAL,
        Priority.MUST,
        "Requirements workshop",
        stakeholder_ids=["STK-002"],
        acceptance_criteria=[
            "Required fields are validated before submission.",
            "A successful submission receives a unique identifier.",
            "The customer receives confirmation after successful submission.",
        ],
    ),
    Requirement(
        "CAS-002",
        "Status tracking",
        "The system shall allow an authenticated customer to view the current status of an application they are authorized to access.",
        RequirementType.FUNCTIONAL,
        Priority.MUST,
        "Customer interview",
        stakeholder_ids=["STK-002"],
        acceptance_criteria=[
            "The current status is displayed for an authorized application.",
            "An unauthorized application cannot be viewed.",
        ],
    ),
    Requirement(
        "CAS-003",
        "Audit logging",
        "The system shall record security-relevant access events with timestamp, actor, action, and result.",
        RequirementType.SECURITY,
        Priority.MUST,
        "Security workshop",
        stakeholder_ids=["STK-003"],
        acceptance_criteria=[
            "Successful protected-data access is logged.",
            "Denied protected-data access is logged.",
            "Each event contains timestamp, actor, action, and result.",
        ],
    ),
    Requirement(
        "CAS-004",
        "Availability",
        "The service shall provide at least 99.9% monthly availability, excluding formally defined maintenance windows.",
        RequirementType.NON_FUNCTIONAL,
        Priority.SHOULD,
        "Operations workshop",
        stakeholder_ids=["STK-001"],
        acceptance_criteria=[
            "Availability is calculated using the approved measurement definition.",
            "Approved maintenance windows are excluded.",
        ],
    ),
]

for item in case_study_requirements:
    item.display()

print("\nCase study quality results:")
for item in case_study_requirements:
    issues = validate_requirement(item)
    print(
        f"{item.requirement_id}: "
        f"{'PASS' if not issues else 'REVIEW'}"
    )
    for issue in issues:
        print(f"  - {issue}")


# ---------------------------------------------------------------------------
# 25. KEY PRINCIPLES EXPRESSED AS EXECUTABLE RULES
# ---------------------------------------------------------------------------

def requirement_principles(requirement: Requirement) -> Dict[str, bool]:
    return {
        "identified": bool(requirement.requirement_id),
        "described": bool(requirement.description),
        "sourced": bool(requirement.source),
        "prioritized": requirement.priority is not None,
        "testable": bool(requirement.acceptance_criteria),
        "stakeholder_linked": bool(requirement.stakeholder_ids),
        "not_blank": bool(requirement.title.strip()),
    }


print("\nPrinciple checks for CAS-001:")
for principle, result in requirement_principles(case_study_requirements[0]).items():
    print(f"{principle}: {'PASS' if result else 'FAIL'}")


# ---------------------------------------------------------------------------
# 26. FINAL EDUCATIONAL REFERENCE
# ---------------------------------------------------------------------------

reference = {
    "discover": [
        "Interviews",
        "Workshops",
        "Observation",
        "Questionnaires",
        "Document analysis",
        "Prototyping",
    ],
    "analyze": [
        "Classification",
        "Conflict analysis",
        "Dependency analysis",
        "Scope analysis",
        "Feasibility analysis",
    ],
    "document": [
        "Business requirements",
        "User stories",
        "Use cases",
        "Functional requirements",
        "Non-functional requirements",
        "Acceptance criteria",
    ],
    "validate": [
        "Completeness",
        "Consistency",
        "Clarity",
        "Feasibility",
        "Testability",
        "Traceability",
    ],
    "control": [
        "Prioritization",
        "Baseline",
        "Versioning",
        "Change requests",
        "Impact analysis",
        "Approval",
    ],
}

print("\nRequirements lifecycle reference:")
for stage, activities in reference.items():
    print(f"\n{stage.upper()}")
    for activity in activities:
        print(f"  - {activity}")

print("\nRequirements collection demonstration completed.")
