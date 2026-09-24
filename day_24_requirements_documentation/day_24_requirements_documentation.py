"""
Requirements Documentation
===========================

A self-contained study and demonstration program for documenting software
requirements from beginner concepts through advanced practices.

The program models:
    - stakeholders and personas
    - business, functional, non-functional, and regulatory requirements
    - requirement identifiers and metadata
    - acceptance criteria
    - assumptions, constraints, dependencies, risks, and open questions
    - requirements validation
    - traceability matrices
    - prioritization using MoSCoW
    - change requests and versioning
    - conflict detection
    - coverage analysis
    - requirement quality metrics
    - document generation
    - a realistic requirements-documentation case study

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime
import re
import textwrap
import statistics
from typing import Dict, Iterable, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# 1. Fundamental terminology
# ---------------------------------------------------------------------------

class RequirementType(Enum):
    BUSINESS = "Business"
    USER = "User"
    FUNCTIONAL = "Functional"
    NON_FUNCTIONAL = "Non-functional"
    DATA = "Data"
    INTERFACE = "Interface"
    REGULATORY = "Regulatory"
    SECURITY = "Security"


class Priority(Enum):
    MUST = "Must"
    SHOULD = "Should"
    COULD = "Could"
    WON_T = "Won't"


class RequirementStatus(Enum):
    PROPOSED = "Proposed"
    APPROVED = "Approved"
    IMPLEMENTED = "Implemented"
    VERIFIED = "Verified"
    REJECTED = "Rejected"


class ChangeStatus(Enum):
    PROPOSED = "Proposed"
    ANALYZING = "Analyzing"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IMPLEMENTED = "Implemented"


# ---------------------------------------------------------------------------
# 2. Core requirement objects
# ---------------------------------------------------------------------------

@dataclass
class AcceptanceCriterion:
    criterion_id: str
    description: str
    expected_result: str
    testable: bool = True

    def validate(self) -> List[str]:
        errors = []
        if not self.criterion_id.strip():
            errors.append("Acceptance criterion ID is missing.")
        if not self.description.strip():
            errors.append("Acceptance criterion description is missing.")
        if not self.expected_result.strip():
            errors.append("Acceptance criterion expected result is missing.")
        return errors


@dataclass
class Stakeholder:
    stakeholder_id: str
    name: str
    role: str
    influence: int
    interest: int

    def priority_score(self) -> int:
        return self.influence * self.interest


@dataclass
class Requirement:
    requirement_id: str
    title: str
    description: str
    requirement_type: RequirementType
    priority: Priority
    status: RequirementStatus = RequirementStatus.PROPOSED
    source: str = ""
    rationale: str = ""
    owner: str = ""
    acceptance_criteria: List[AcceptanceCriterion] = field(default_factory=list)
    stakeholder_ids: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    related_requirements: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    assumptions: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    version: int = 1
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def validate(self) -> List[str]:
        """
        Requirement-quality checks.

        Good requirements should be:
            - uniquely identifiable
            - clear
            - necessary
            - feasible
            - verifiable
            - consistent
            - traceable

        Automated checks cannot prove quality, but they can identify common
        documentation problems.
        """
        errors = []

        if not self.requirement_id.strip():
            errors.append("Missing requirement ID.")

        if not self.title.strip():
            errors.append("Missing requirement title.")

        if not self.description.strip():
            errors.append("Missing requirement description.")

        if len(self.description.split()) < 5:
            errors.append("Description is probably too short.")

        vague_words = {
            "easy", "fast", "user-friendly", "appropriate",
            "reasonable", "simple", "etc", "soon", "adequate"
        }
        lower_description = self.description.lower()
        found_vague = [
            word for word in vague_words
            if re.search(rf"\b{re.escape(word)}\b", lower_description)
        ]
        if found_vague:
            errors.append(
                "Potentially vague terms found: " + ", ".join(sorted(found_vague))
            )

        if self.requirement_type in {
            RequirementType.FUNCTIONAL,
            RequirementType.SECURITY,
            RequirementType.NON_FUNCTIONAL,
        } and not self.acceptance_criteria:
            errors.append("Requirement has no acceptance criteria.")

        if not self.source.strip():
            errors.append("Requirement has no documented source.")

        if not self.rationale.strip():
            errors.append("Requirement has no documented rationale.")

        for criterion in self.acceptance_criteria:
            errors.extend(
                f"{criterion.criterion_id}: {error}"
                for error in criterion.validate()
            )

        return errors

    def is_verifiable(self) -> bool:
        return bool(self.acceptance_criteria) and all(
            criterion.testable for criterion in self.acceptance_criteria
        )

    def priority_weight(self) -> int:
        return {
            Priority.MUST: 4,
            Priority.SHOULD: 3,
            Priority.COULD: 2,
            Priority.WON_T: 1,
        }[self.priority]


# ---------------------------------------------------------------------------
# 3. Change requests
# ---------------------------------------------------------------------------

@dataclass
class ChangeRequest:
    change_id: str
    requirement_id: str
    requested_by: str
    description: str
    business_reason: str
    impact: str
    status: ChangeStatus = ChangeStatus.PROPOSED
    old_version: int = 1
    new_version: Optional[int] = None

    def approve(self, current_version: int) -> None:
        self.status = ChangeStatus.APPROVED
        self.old_version = current_version
        self.new_version = current_version + 1


# ---------------------------------------------------------------------------
# 4. Requirements repository
# ---------------------------------------------------------------------------

class RequirementsRepository:
    """
    Stores and manages requirements.

    A repository gives a requirements document structure instead of treating
    requirements as unstructured paragraphs.
    """

    def __init__(self) -> None:
        self.requirements: Dict[str, Requirement] = {}
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.changes: Dict[str, ChangeRequest] = {}

    def add_stakeholder(self, stakeholder: Stakeholder) -> None:
        if stakeholder.stakeholder_id in self.stakeholders:
            raise ValueError(
                f"Duplicate stakeholder ID: {stakeholder.stakeholder_id}"
            )
        self.stakeholders[stakeholder.stakeholder_id] = stakeholder

    def add_requirement(self, requirement: Requirement) -> None:
        if requirement.requirement_id in self.requirements:
            raise ValueError(
                f"Duplicate requirement ID: {requirement.requirement_id}"
            )

        unknown = (
            requirement.stakeholder_ids
            - set(self.stakeholders.keys())
        )
        if unknown:
            raise ValueError(
                f"Unknown stakeholder IDs: {sorted(unknown)}"
            )

        self.requirements[requirement.requirement_id] = requirement

    def get(self, requirement_id: str) -> Requirement:
        try:
            return self.requirements[requirement_id]
        except KeyError as exc:
            raise KeyError(
                f"Requirement not found: {requirement_id}"
            ) from exc

    def update_requirement(
        self,
        requirement_id: str,
        *,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        acceptance_criteria: Optional[List[AcceptanceCriterion]] = None,
    ) -> Requirement:
        requirement = self.get(requirement_id)

        if description is not None:
            requirement.description = description

        if priority is not None:
            requirement.priority = priority

        if acceptance_criteria is not None:
            requirement.acceptance_criteria = acceptance_criteria

        requirement.version += 1
        return requirement

    def search(self, text: str) -> List[Requirement]:
        needle = text.lower()
        return [
            requirement
            for requirement in self.requirements.values()
            if needle in requirement.title.lower()
            or needle in requirement.description.lower()
            or needle in requirement.requirement_id.lower()
            or any(needle in tag.lower() for tag in requirement.tags)
        ]

    def filter_by_type(
        self, requirement_type: RequirementType
    ) -> List[Requirement]:
        return [
            requirement
            for requirement in self.requirements.values()
            if requirement.requirement_type == requirement_type
        ]

    def filter_by_priority(self, priority: Priority) -> List[Requirement]:
        return [
            requirement
            for requirement in self.requirements.values()
            if requirement.priority == priority
        ]

    def register_change(self, change: ChangeRequest) -> None:
        if change.change_id in self.changes:
            raise ValueError(f"Duplicate change ID: {change.change_id}")
        if change.requirement_id not in self.requirements:
            raise ValueError(
                f"Cannot change unknown requirement: {change.requirement_id}"
            )
        self.changes[change.change_id] = change


# ---------------------------------------------------------------------------
# 5. Traceability
# ---------------------------------------------------------------------------

@dataclass
class TraceabilityMatrix:
    """
    Maps requirements to design, implementation, and test artifacts.

    This is especially useful in regulated or high-risk systems where the
    team must demonstrate that requirements are implemented and verified.
    """

    requirement_to_design: Dict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    requirement_to_code: Dict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    requirement_to_tests: Dict[str, Set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )

    def link_design(self, requirement_id: str, design_id: str) -> None:
        self.requirement_to_design[requirement_id].add(design_id)

    def link_code(self, requirement_id: str, code_id: str) -> None:
        self.requirement_to_code[requirement_id].add(code_id)

    def link_test(self, requirement_id: str, test_id: str) -> None:
        self.requirement_to_tests[requirement_id].add(test_id)

    def coverage(self, requirement_ids: Iterable[str]) -> Dict[str, float]:
        ids = list(requirement_ids)
        if not ids:
            return {
                "design": 0.0,
                "code": 0.0,
                "test": 0.0,
                "complete": 0.0,
            }

        design = sum(bool(self.requirement_to_design[r]) for r in ids)
        code = sum(bool(self.requirement_to_code[r]) for r in ids)
        tests = sum(bool(self.requirement_to_tests[r]) for r in ids)

        complete = sum(
            bool(self.requirement_to_design[r])
            and bool(self.requirement_to_code[r])
            and bool(self.requirement_to_tests[r])
            for r in ids
        )

        total = len(ids)
        return {
            "design": design / total * 100,
            "code": code / total * 100,
            "test": tests / total * 100,
            "complete": complete / total * 100,
        }


# ---------------------------------------------------------------------------
# 6. Requirement analysis
# ---------------------------------------------------------------------------

class RequirementsAnalyzer:
    def __init__(
        self,
        repository: RequirementsRepository,
        traceability: TraceabilityMatrix,
    ) -> None:
        self.repository = repository
        self.traceability = traceability

    def validate_all(self) -> Dict[str, List[str]]:
        return {
            requirement.requirement_id: requirement.validate()
            for requirement in self.repository.requirements.values()
        }

    def duplicate_similarity(
        self, first: Requirement, second: Requirement
    ) -> float:
        """
        Simple Jaccard similarity over normalized words.

        This is not semantic NLP. It is a transparent heuristic useful for
        finding suspiciously similar requirement statements.
        """
        normalize = lambda text: {
            word.lower()
            for word in re.findall(r"[A-Za-z0-9]+", text)
            if len(word) > 2
        }

        first_words = normalize(first.description)
        second_words = normalize(second.description)

        if not first_words or not second_words:
            return 0.0

        return (
            len(first_words & second_words)
            / len(first_words | second_words)
        ) * 100

    def find_similar_requirements(
        self, threshold: float = 55.0
    ) -> List[Tuple[str, str, float]]:
        requirements = list(self.repository.requirements.values())
        matches = []

        for index, first in enumerate(requirements):
            for second in requirements[index + 1:]:
                similarity = self.duplicate_similarity(first, second)
                if similarity >= threshold:
                    matches.append(
                        (
                            first.requirement_id,
                            second.requirement_id,
                            similarity,
                        )
                    )

        return matches

    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Depth-first search identifies dependency cycles.

        A cycle can make sequencing impossible or indicate that requirements
        are coupled too tightly.
        """
        graph = {
            requirement.requirement_id: set(requirement.dependencies)
            for requirement in self.repository.requirements.values()
        }

        cycles: List[List[str]] = []
        visited: Set[str] = set()
        active: List[str] = []

        def visit(node: str) -> None:
            if node in active:
                start = active.index(node)
                cycles.append(active[start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            active.append(node)

            for dependency in graph.get(node, set()):
                if dependency in graph:
                    visit(dependency)

            active.pop()

        for node in graph:
            visit(node)

        return cycles

    def quality_metrics(self) -> Dict[str, float]:
        requirements = list(self.repository.requirements.values())

        if not requirements:
            return {}

        with_acceptance = sum(
            bool(r.acceptance_criteria) for r in requirements
        )
        with_source = sum(bool(r.source.strip()) for r in requirements)
        with_rationale = sum(bool(r.rationale.strip()) for r in requirements)
        verifiable = sum(r.is_verifiable() for r in requirements)

        validation_error_count = sum(
            len(r.validate()) for r in requirements
        )

        return {
            "total_requirements": float(len(requirements)),
            "acceptance_criteria_coverage": (
                with_acceptance / len(requirements) * 100
            ),
            "source_coverage": with_source / len(requirements) * 100,
            "rationale_coverage": with_rationale / len(requirements) * 100,
            "verifiability": verifiable / len(requirements) * 100,
            "validation_errors": float(validation_error_count),
        }

    def priority_distribution(self) -> Dict[str, int]:
        distribution = {priority.value: 0 for priority in Priority}
        for requirement in self.repository.requirements.values():
            distribution[requirement.priority.value] += 1
        return distribution

    def stakeholder_impact(self) -> List[Tuple[str, int]]:
        return sorted(
            (
                (stakeholder.name, stakeholder.priority_score())
                for stakeholder in self.repository.stakeholders.values()
            ),
            key=lambda item: item[1],
            reverse=True,
        )


# ---------------------------------------------------------------------------
# 7. Requirements document generator
# ---------------------------------------------------------------------------

class RequirementsDocument:
    def __init__(
        self,
        project_name: str,
        version: str,
        repository: RequirementsRepository,
        traceability: TraceabilityMatrix,
    ) -> None:
        self.project_name = project_name
        self.version = version
        self.repository = repository
        self.traceability = traceability

    def generate(self) -> str:
        lines = [
            f"# {self.project_name} Requirements Specification",
            "",
            f"Document version: {self.version}",
            "",
            "## 1. Purpose",
            "",
            (
                "This document defines the documented business, user, "
                "functional, non-functional, data, interface, security, "
                "and regulatory requirements for the system."
            ),
            "",
            "## 2. Stakeholders",
            "",
            "| ID | Stakeholder | Role | Influence | Interest |",
            "|---|---|---|---:|---:|",
        ]

        for stakeholder in self.repository.stakeholders.values():
            lines.append(
                f"| {stakeholder.stakeholder_id} | "
                f"{stakeholder.name} | {stakeholder.role} | "
                f"{stakeholder.influence} | {stakeholder.interest} |"
            )

        lines.extend(
            [
                "",
                "## 3. Requirements",
                "",
                "| ID | Type | Priority | Status | Title |",
                "|---|---|---|---|---|",
            ]
        )

        for requirement in self.repository.requirements.values():
            lines.append(
                f"| {requirement.requirement_id} | "
                f"{requirement.requirement_type.value} | "
                f"{requirement.priority.value} | "
                f"{requirement.status.value} | "
                f"{requirement.title} |"
            )

        for requirement in self.repository.requirements.values():
            lines.extend(
                [
                    "",
                    f"### {requirement.requirement_id}: {requirement.title}",
                    "",
                    f"**Type:** {requirement.requirement_type.value}",
                    "",
                    f"**Priority:** {requirement.priority.value}",
                    "",
                    f"**Description:** {requirement.description}",
                    "",
                    f"**Source:** {requirement.source}",
                    "",
                    f"**Rationale:** {requirement.rationale}",
                    "",
                    "#### Acceptance criteria",
                    "",
                ]
            )

            for criterion in requirement.acceptance_criteria:
                lines.append(
                    f"- **{criterion.criterion_id}:** "
                    f"{criterion.description} "
                    f"Expected result: {criterion.expected_result}"
                )

            if requirement.dependencies:
                lines.extend(
                    [
                        "",
                        "#### Dependencies",
                        "",
                        ", ".join(sorted(requirement.dependencies)),
                    ]
                )

            if requirement.constraints:
                lines.extend(
                    [
                        "",
                        "#### Constraints",
                        "",
                    ]
                )
                lines.extend(
                    f"- {constraint}"
                    for constraint in requirement.constraints
                )

        lines.extend(
            [
                "",
                "## 4. Traceability",
                "",
                "| Requirement | Design | Code | Tests |",
                "|---|---|---|---|",
            ]
        )

        for requirement in self.repository.requirements.values():
            rid = requirement.requirement_id
            design = ", ".join(
                sorted(self.traceability.requirement_to_design[rid])
            ) or "Not linked"
            code = ", ".join(
                sorted(self.traceability.requirement_to_code[rid])
            ) or "Not linked"
            tests = ", ".join(
                sorted(self.traceability.requirement_to_tests[rid])
            ) or "Not linked"

            lines.append(f"| {rid} | {design} | {code} | {tests} |")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 8. Requirement elicitation and normalization
# ---------------------------------------------------------------------------

def normalize_user_story(
    actor: str,
    action: str,
    benefit: str,
) -> str:
    """
    Standard user-story structure:
        As a <actor>, I want <action>, so that <benefit>.
    """
    if not all(value.strip() for value in (actor, action, benefit)):
        raise ValueError("User-story fields cannot be empty.")

    return (
        f"As a {actor.strip()}, I want {action.strip()}, "
        f"so that {benefit.strip()}."
    )


def make_acceptance_criterion(
    criterion_id: str,
    condition: str,
    behavior: str,
    expected_result: str,
) -> AcceptanceCriterion:
    """
    A lightweight Given/When/Then-style transformation.
    """
    description = f"Given {condition}, when {behavior}"
    return AcceptanceCriterion(
        criterion_id=criterion_id,
        description=description,
        expected_result=expected_result,
    )


# ---------------------------------------------------------------------------
# 9. Conflict and consistency checks
# ---------------------------------------------------------------------------

def find_conflicting_requirements(
    repository: RequirementsRepository,
) -> List[Tuple[str, str, str]]:
    """
    Detects a small set of explicit lexical conflict patterns.

    Real requirements engineering needs human review because many conflicts
    depend on business context and cannot be reliably solved with keywords.
    """
    requirements = list(repository.requirements.values())
    conflicts = []

    opposing_pairs = [
        ("must allow", "must prevent"),
        ("allow guest", "require authentication"),
        ("public", "private"),
        ("unlimited", "maximum"),
        ("delete", "retain"),
    ]

    for index, first in enumerate(requirements):
        first_text = (
            first.title + " " + first.description
        ).lower()

        for second in requirements[index + 1:]:
            second_text = (
                second.title + " " + second.description
            ).lower()

            for phrase_a, phrase_b in opposing_pairs:
                if (
                    (phrase_a in first_text and phrase_b in second_text)
                    or
                    (phrase_b in first_text and phrase_a in second_text)
                ):
                    conflicts.append(
                        (
                            first.requirement_id,
                            second.requirement_id,
                            f"Possible conflict: '{phrase_a}' vs '{phrase_b}'",
                        )
                    )

    return conflicts


# ---------------------------------------------------------------------------
# 10. Worked case study: digital service request platform
# ---------------------------------------------------------------------------

def build_case_study() -> Tuple[
    RequirementsRepository,
    TraceabilityMatrix
]:
    repository = RequirementsRepository()

    # Stakeholder analysis is part of elicitation because requirements are
    # derived from stakeholder needs, constraints, and business objectives.
    repository.add_stakeholder(
        Stakeholder(
            stakeholder_id="STK-001",
            name="Service Customer",
            role="Primary user",
            influence=4,
            interest=5,
        )
    )

    repository.add_stakeholder(
        Stakeholder(
            stakeholder_id="STK-002",
            name="Operations Manager",
            role="Business owner",
            influence=5,
            interest=5,
        )
    )

    repository.add_stakeholder(
        Stakeholder(
            stakeholder_id="STK-003",
            name="Support Agent",
            role="Operational user",
            influence=4,
            interest=4,
        )
    )

    repository.add_stakeholder(
        Stakeholder(
            stakeholder_id="STK-004",
            name="Security Officer",
            role="Security governance",
            influence=5,
            interest=4,
        )
    )

    repository.add_stakeholder(
        Stakeholder(
            stakeholder_id="STK-005",
            name="Compliance Officer",
            role="Regulatory governance",
            influence=5,
            interest=3,
        )
    )

    repository.add_requirement(
        Requirement(
            requirement_id="BR-001",
            title="Digital service requests",
            description=(
                "The platform shall provide a digital channel for customers "
                "to submit service requests without contacting an agent."
            ),
            requirement_type=RequirementType.BUSINESS,
            priority=Priority.MUST,
            status=RequirementStatus.APPROVED,
            source="Operations workshop",
            rationale=(
                "The organization wants to reduce manual request handling "
                "and provide a measurable digital service channel."
            ),
            owner="Operations Manager",
            stakeholder_ids={"STK-002", "STK-001"},
            tags={"business", "digital-service"},
        )
    )

    repository.add_requirement(
        Requirement(
            requirement_id="FR-001",
            title="Create a service request",
            description=(
                "The system shall allow an authenticated customer to create "
                "a service request by selecting a category, entering a "
                "description, and submitting the request."
            ),
            requirement_type=RequirementType.FUNCTIONAL,
            priority=Priority.MUST,
            status=RequirementStatus.APPROVED,
            source="Customer interview",
            rationale="Request creation is the primary customer workflow.",
            owner="Product Owner",
            stakeholder_ids={"STK-001", "STK-002"},
            acceptance_criteria=[
                make_acceptance_criterion(
                    "AC-001",
                    "the customer is authenticated",
                    "the customer provides a valid category and description",
                    "a unique request ID is created and displayed",
                ),
                make_acceptance_criterion(
                    "AC-002",
                    "the description is empty",
                    "the customer attempts submission",
                    "the request is rejected with a validation message",
                ),
            ],
            dependencies={"BR-001"},
            tags={"customer", "request", "core"},
        )
    )

    repository.add_requirement(
        Requirement(
            requirement_id="FR-002",
            title="Track request status",
            description=(
                "The system shall allow customers to view the current "
                "status and status history of their submitted requests."
            ),
            requirement_type=RequirementType.FUNCTIONAL,
            priority=Priority.MUST,
            status=RequirementStatus.APPROVED,
            source="Customer interview",
            rationale=(
                "Customers need visibility into progress after submission."
            ),
            owner="Product Owner",
            stakeholder_ids={"STK-001", "STK-003"},
            acceptance_criteria=[
                make_acceptance_criterion(
                    "AC-003",
                    "the customer owns the request",
                    "the customer opens the request details",
                    "the current status and chronological status history are shown",
                )
            ],
            dependencies={"FR-001"},
            tags={"customer", "tracking"},
        )
    )

    repository.add_requirement(
        Requirement(
            requirement_id="FR-003",
            title="Agent request queue",
            description=(
                "The system shall provide authorized support agents with a "
                "queue containing requests assigned to their operational team."
            ),
            requirement_type=RequirementType.FUNCTIONAL,
            priority=Priority.MUST,
            status=RequirementStatus.APPROVED,
            source="Operations workshop",
            rationale="Agents require a controlled operational work queue.",
            owner="Operations Manager",
            stakeholder_ids={"STK-002", "STK-003"},
            acceptance_criteria=[
                make_acceptance_criterion(
                    "AC-004",
                    "the user has the support-agent role",
                    "the user opens the request queue",
                    "only requests accessible to that operational team are shown",
                )
            ],
            dependencies={"FR-001"},
            tags={"agent", "operations", "authorization"},
        )
    )

    repository.add_requirement(
        Requirement(
            requirement_id="NFR-001",
            title="Request response time",
            description=(
                "The service shall return a successful request-status query "
                "within 2 seconds for at least 95 percent of requests under "
                "the defined normal operating load."
            ),
            requirement_type=RequirementType.NON_FUNCTIONAL,
            priority=Priority.SHOULD,
            status=RequirementStatus.APPROVED,
            source="Performance workshop",
            rationale="Response-time expectations affect customer usability.",
            owner="Engineering",
            stakeholder_ids={"STK-001", "STK-002"},
            acceptance_criteria=[
                make_acceptance_criterion(
                    "AC-005",
                    "the system is under normal operating load",
                    "1000 status queries are executed",
                    "at least 950 complete within 2 seconds",
                )
            ],
            constraints=[
                "Normal operating load must be defined before performance testing."
            ],
            tags={"performance", "latency"},
        )
    )

    repository.add_requirement(
        Requirement(
            requirement_id="SEC-001",
            title="Role-based access control",
            description=(
                "The system shall enforce role-based authorization so that "
                "customers, support agents, managers, and administrators can "
                "access only operations permitted for their roles."
            ),
            requirement_type=RequirementType.SECURITY,
            priority=Priority.MUST,
            status=RequirementStatus.APPROVED,
            source="Security architecture review",
            rationale="Authorization prevents unauthorized access to service data.",
            owner="Security Officer",
            stakeholder_ids={"STK-004", "STK-003"},
            acceptance_criteria=[
                make_acceptance_criterion(
                    "AC-006",
                    "a customer attempts to access another customer's request",
                    "the authorization check executes",
                    "access is denied and the event is recorded",
                ),
                make_acceptance_criterion(
                    "AC-007",
                    "an agent accesses an authorized team request",
                    "the authorization check executes",
                    "the request is displayed",
                ),
            ],
            dependencies={"FR-001"},
            risks=[
                "Incorrect authorization rules could expose customer information."
            ],
            tags={"security", "authorization", "privacy"},
        )
    )

    repository.add_requirement(
        Requirement(
            requirement_id="DATA-001",
            title="Request audit history",
            description=(
                "The system shall record creation, assignment, status changes, "
                "and closure events for each service request with event time, "
                "actor identifier, and event type."
            ),
            requirement_type=RequirementType.DATA,
            priority=Priority.MUST,
            status=RequirementStatus.APPROVED,
            source="Compliance workshop",
            rationale="Auditable history supports accountability and investigation.",
            owner="Compliance Officer",
            stakeholder_ids={"STK-005", "STK-004"},
            acceptance_criteria=[
                make_acceptance_criterion(
                    "AC-008",
                    "a request status changes",
                    "the transaction completes",
                    "an immutable audit event exists with actor and timestamp",
                )
            ],
            dependencies={"FR-001"},
            constraints=[
                "Audit records must not be editable through normal application operations."
            ],
            tags={"audit", "compliance", "data"},
        )
    )

    traceability = TraceabilityMatrix()

    traceability.link_design("BR-001", "ARCH-001")
    traceability.link_design("FR-001", "DESIGN-REQ-API")
    traceability.link_design("FR-002", "DESIGN-REQUEST-VIEW")
    traceability.link_design("FR-003", "DESIGN-AGENT-QUEUE")
    traceability.link_design("NFR-001", "DESIGN-CACHE")
    traceability.link_design("SEC-001", "DESIGN-AUTHZ")
    traceability.link_design("DATA-001", "DESIGN-AUDIT")

    traceability.link_code("FR-001", "RequestService.create")
    traceability.link_code("FR-002", "RequestService.get_status")
    traceability.link_code("FR-003", "AgentQueue.list_requests")
    traceability.link_code("SEC-001", "AuthorizationPolicy")
    traceability.link_code("DATA-001", "AuditRepository")

    traceability.link_test("FR-001", "TEST-REQ-CREATE-001")
    traceability.link_test("FR-002", "TEST-REQ-STATUS-001")
    traceability.link_test("FR-003", "TEST-QUEUE-001")
    traceability.link_test("NFR-001", "TEST-PERF-001")
    traceability.link_test("SEC-001", "TEST-AUTHZ-001")
    traceability.link_test("DATA-001", "TEST-AUDIT-001")

    return repository, traceability


# ---------------------------------------------------------------------------
# 11. Practical demonstrations
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def demonstrate_terminology() -> None:
    print_section("FUNDAMENTALS: REQUIREMENTS DOCUMENTATION")

    definitions = {
        "Requirement": (
            "A documented need, capability, condition, or constraint "
            "that a system or organization must satisfy."
        ),
        "Elicitation": (
            "The process of discovering requirements from stakeholders, "
            "documents, observations, data, and domain knowledge."
        ),
        "Specification": (
            "The structured expression of requirements in a form that "
            "stakeholders and delivery teams can review."
        ),
        "Validation": (
            "Checking whether requirements are correct, complete, feasible, "
            "consistent, understandable, and verifiable."
        ),
        "Verification": (
            "Checking an implemented system or artifact against a requirement."
        ),
        "Traceability": (
            "Maintaining relationships between requirements and their sources, "
            "design elements, implementation elements, and tests."
        ),
        "Acceptance Criterion": (
            "A specific condition used to determine whether a requirement "
            "has been satisfied."
        ),
        "Baseline": (
            "A formally approved version of requirements that changes through "
            "controlled change management."
        ),
    }

    for term, definition in definitions.items():
        print(f"\n{term}: {definition}")

    print("\nCommon classification:")
    for requirement_type in RequirementType:
        print(f"  - {requirement_type.value}")


def demonstrate_user_story() -> None:
    print_section("USER STORY AND ACCEPTANCE CRITERIA")

    story = normalize_user_story(
        "customer",
        "view the status of my service request",
        "know whether action is still required from me",
    )

    print(story)

    criterion = make_acceptance_criterion(
        "AC-DEMO-001",
        "the request belongs to the authenticated customer",
        "the customer opens the request",
        "the current status and history are displayed",
    )

    print(f"{criterion.criterion_id}: {criterion.description}")
    print(f"Expected: {criterion.expected_result}")


def demonstrate_case_study() -> None:
    repository, traceability = build_case_study()
    analyzer = RequirementsAnalyzer(repository, traceability)

    print_section("CASE STUDY: DIGITAL SERVICE REQUEST PLATFORM")

    for requirement in repository.requirements.values():
        errors = requirement.validate()
        status = "PASS" if not errors else "REVIEW"
        print(
            f"{requirement.requirement_id:<10} "
            f"{status:<7} "
            f"{requirement.title}"
        )
        for error in errors:
            print(f"    - {error}")

    print_section("PRIORITY DISTRIBUTION")
    for priority, count in analyzer.priority_distribution().items():
        print(f"{priority:<8}: {count}")

    print_section("QUALITY METRICS")
    metrics = analyzer.quality_metrics()
    for metric, value in metrics.items():
        if metric.endswith("coverage") or metric == "verifiability":
            print(f"{metric:<32}: {value:.1f}%")
        else:
            print(f"{metric:<32}: {value:.1f}")

    print_section("TRACEABILITY COVERAGE")
    coverage = traceability.coverage(repository.requirements.keys())
    for artifact_type, percentage in coverage.items():
        print(f"{artifact_type:<10}: {percentage:.1f}%")

    print_section("STAKEHOLDER IMPACT")
    for name, score in analyzer.stakeholder_impact():
        print(f"{name:<25}: influence × interest = {score}")

    print_section("DEPENDENCY CYCLES")
    cycles = analyzer.detect_circular_dependencies()
    print("None detected." if not cycles else cycles)

    print_section("SIMILARITY CHECK")
    similar = analyzer.find_similar_requirements()
    if not similar:
        print("No suspiciously similar requirements detected.")
    else:
        for first, second, percentage in similar:
            print(
                f"{first} <-> {second}: "
                f"{percentage:.1f}% lexical similarity"
            )

    print_section("CONFLICT CHECK")
    conflicts = find_conflicting_requirements(repository)
    if not conflicts:
        print("No lexical conflict patterns detected.")
    else:
        for first, second, reason in conflicts:
            print(f"{first} <-> {second}: {reason}")

    print_section("SEARCH")
    results = repository.search("status")
    for result in results:
        print(f"{result.requirement_id}: {result.title}")

    print_section("GENERATED REQUIREMENTS DOCUMENT")
    document = RequirementsDocument(
        "Digital Service Request Platform",
        "1.0",
        repository,
        traceability,
    )
    generated = document.generate()

    # Print only a controlled portion so the study program remains readable.
    print(textwrap.indent("\n".join(generated.splitlines()[:35]), ""))
    print("\n[Document output truncated for console demonstration.]")

    print_section("CHANGE CONTROL")

    change = ChangeRequest(
        change_id="CR-001",
        requirement_id="FR-002",
        requested_by="Operations Manager",
        description=(
            "Display an estimated completion time alongside the request status."
        ),
        business_reason=(
            "Customers need more precise information about expected service timing."
        ),
        impact=(
            "Requires a new response field, business rule, UI element, and tests."
        ),
    )

    repository.register_change(change)
    change.approve(repository.get(change.requirement_id).version)

    print(
        f"{change.change_id}: {change.status.value}, "
        f"version {change.old_version} -> {change.new_version}"
    )

    repository.update_requirement(
        "FR-002",
        description=(
            "The system shall allow customers to view the current status, "
            "status history, and estimated completion time of their submitted "
            "requests."
        ),
    )

    print(
        f"FR-002 revised document version: "
        f"{repository.get('FR-002').version}"
    )


# ---------------------------------------------------------------------------
# 12. Requirement-quality teaching examples
# ---------------------------------------------------------------------------

def demonstrate_good_and_bad_requirements() -> None:
    print_section("QUALITY COMPARISON")

    examples = [
        Requirement(
            requirement_id="BAD-001",
            title="Fast system",
            description="The system should be fast and user-friendly.",
            requirement_type=RequirementType.NON_FUNCTIONAL,
            priority=Priority.SHOULD,
        ),
        Requirement(
            requirement_id="GOOD-001",
            title="Measured response time",
            description=(
                "The system shall return the account dashboard within "
                "2 seconds for at least 95 percent of requests under the "
                "defined normal operating load."
            ),
            requirement_type=RequirementType.NON_FUNCTIONAL,
            priority=Priority.MUST,
            source="Performance specification",
            rationale="Defines measurable customer-facing performance.",
            acceptance_criteria=[
                AcceptanceCriterion(
                    criterion_id="AC-GOOD-001",
                    description=(
                        "Given normal operating load, when 1000 dashboard "
                        "requests are submitted"
                    ),
                    expected_result=(
                        "at least 950 requests complete within 2 seconds"
                    ),
                )
            ],
        ),
    ]

    for requirement in examples:
        errors = requirement.validate()
        print(f"\n{requirement.requirement_id}: {requirement.title}")
        if errors:
            print("Issues:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("No automated quality issues detected.")


def demonstrate_priority_and_tradeoffs() -> None:
    print_section("PRIORITIZATION AND TRADE-OFFS")

    candidates = [
        ("Core request submission", Priority.MUST),
        ("Request status history", Priority.MUST),
        ("Advanced analytics", Priority.SHOULD),
        ("Custom dashboard themes", Priority.COULD),
        ("Experimental voice control", Priority.WON_T),
    ]

    for feature, priority in candidates:
        print(
            f"{feature:<30} "
            f"{priority.value:<8} "
            f"weight={priority.value}"
        )

    print(
        "\nMoSCoW is a prioritization communication mechanism, not a "
        "substitute for feasibility, cost, risk, architecture, or compliance analysis."
    )


# ---------------------------------------------------------------------------
# 13. Testing the documentation model
# ---------------------------------------------------------------------------

def run_self_tests() -> None:
    """
    Small executable tests ensure that the educational implementation itself
    behaves predictably.
    """
    repository, traceability = build_case_study()

    assert repository.get("FR-001").title == "Create a service request"
    assert repository.get("FR-001").is_verifiable()

    results = repository.search("authentication")
    assert any(
        result.requirement_id == "FR-001"
        for result in results
    )

    coverage = traceability.coverage(repository.requirements.keys())
    assert coverage["test"] > 0

    cycle_free = RequirementsAnalyzer(
        repository, traceability
    ).detect_circular_dependencies()
    assert not cycle_free

    story = normalize_user_story(
        "administrator",
        "review audit records",
        "investigate operational events",
    )
    assert story.startswith("As an administrator")

    try:
        repository.add_requirement(
            Requirement(
                requirement_id="FR-001",
                title="Duplicate",
                description="This should fail because the ID already exists.",
                requirement_type=RequirementType.FUNCTIONAL,
                priority=Priority.MUST,
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate requirement IDs must be rejected.")

    print("All self-tests passed.")


# ---------------------------------------------------------------------------
# 14. Main program
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        "REQUIREMENTS DOCUMENTATION STUDY PROGRAM\n"
        "========================================\n"
        "This executable file demonstrates requirements engineering concepts "
        "through a complete documentation model."
    )

    demonstrate_terminology()
    demonstrate_user_story()
    demonstrate_good_and_bad_requirements()
    demonstrate_priority_and_tradeoffs()
    demonstrate_case_study()

    print_section("SELF-TESTS")
    run_self_tests()

    print_section("IMPORTANT DISTINCTIONS")
    distinctions = [
        (
            "Business requirement",
            "Why the organization needs a capability or outcome."
        ),
        (
            "User requirement",
            "What a user needs to accomplish."
        ),
        (
            "Functional requirement",
            "What the system must do."
        ),
        (
            "Non-functional requirement",
            "A measurable quality, constraint, or operational property."
        ),
        (
            "Acceptance criterion",
            "A concrete condition used to determine satisfaction."
        ),
        (
            "Requirement validation",
            "Whether the requirement itself is suitable and well-formed."
        ),
        (
            "Requirement verification",
            "Whether implementation satisfies the requirement."
        ),
        (
            "Traceability",
            "The relationships connecting requirements to their lifecycle artifacts."
        ),
    ]

    for term, meaning in distinctions:
        print(f"{term:<30}: {meaning}")


if __name__ == "__main__":
    main()
