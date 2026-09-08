"""
PROJECT DELIVERABLES
====================
Topic: Outputs produced by a project

A comprehensive, executable study script covering project deliverables from
absolute beginner concepts through advanced project, product, governance,
quality, acceptance, traceability, change control, and production considerations.

The script uses only Python's standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Optional
import json
import re
import statistics
import tempfile
import unittest


# =============================================================================
# 1. FOUNDATIONS
# =============================================================================

def section(title: str) -> None:
    """Print a consistent educational section heading."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


print("PROJECT DELIVERABLES")
print("Outputs produced by a project")


# A project deliverable is a distinct, verifiable output produced by project
# work. A deliverable can be tangible, digital, documentary, technical,
# operational, or organizational.
#
# Important distinction:
#   Activity: work performed.
#   Milestone: significant point or event.
#   Deliverable: output produced.
#   Outcome: change or result enabled by the deliverable.
#   Benefit: value realized from the outcome.
#
# Example:
#   Activity  -> Develop authentication module
#   Deliverable -> Tested authentication module
#   Milestone -> Authentication module accepted
#   Outcome -> Users can securely authenticate
#   Benefit -> Reduced unauthorized access and support effort


@dataclass
class BasicProjectExample:
    activity: str
    deliverable: str
    milestone: str
    outcome: str
    benefit: str


example = BasicProjectExample(
    activity="Develop authentication module",
    deliverable="Tested authentication module",
    milestone="Authentication module accepted",
    outcome="Users can authenticate securely",
    benefit="Reduced unauthorized access risk",
)

print("\nBasic distinction:")
for field_name, value in vars(example).items():
    print(f"{field_name.capitalize():12}: {value}")


# =============================================================================
# 2. DELIVERABLE CLASSIFICATION
# =============================================================================

class DeliverableType(Enum):
    PRODUCT = "Product"
    SERVICE = "Service"
    DOCUMENT = "Document"
    DATA = "Data"
    SOFTWARE = "Software"
    INFRASTRUCTURE = "Infrastructure"
    TRAINING = "Training"
    PROCESS = "Process"
    DESIGN = "Design"
    TRANSITION = "Transition"
    GOVERNANCE = "Governance"


class DeliverableStatus(Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    READY_FOR_REVIEW = "Ready for Review"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    BASELINED = "Baselined"
    RELEASED = "Released"
    CLOSED = "Closed"


class QualityStatus(Enum):
    NOT_ASSESSED = "Not Assessed"
    PASSED = "Passed"
    FAILED = "Failed"
    CONDITIONALLY_PASSED = "Conditionally Passed"


@dataclass
class AcceptanceCriterion:
    criterion_id: str
    description: str
    mandatory: bool = True
    verification_method: str = "Inspection"
    passed: bool = False


@dataclass
class Deliverable:
    deliverable_id: str
    name: str
    description: str
    deliverable_type: DeliverableType
    owner: str
    version: str = "1.0"
    status: DeliverableStatus = DeliverableStatus.PLANNED
    quality_status: QualityStatus = QualityStatus.NOT_ASSESSED
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    accepted_at: Optional[datetime] = None
    checksum: Optional[str] = None

    def add_acceptance_criterion(
        self,
        criterion_id: str,
        description: str,
        mandatory: bool = True,
        verification_method: str = "Inspection",
    ) -> None:
        self.acceptance_criteria.append(
            AcceptanceCriterion(
                criterion_id=criterion_id,
                description=description,
                mandatory=mandatory,
                verification_method=verification_method,
            )
        )

    def mark_criterion_passed(self, criterion_id: str) -> None:
        for criterion in self.acceptance_criteria:
            if criterion.criterion_id == criterion_id:
                criterion.passed = True
                return
        raise KeyError(f"Acceptance criterion not found: {criterion_id}")

    def can_be_accepted(self) -> bool:
        """All mandatory acceptance criteria must pass."""
        return all(
            criterion.passed
            for criterion in self.acceptance_criteria
            if criterion.mandatory
        )

    def accept(self) -> None:
        if not self.can_be_accepted():
            raise ValueError(
                f"Deliverable {self.deliverable_id} cannot be accepted: "
                "one or more mandatory criteria have not passed."
            )

        if self.quality_status == QualityStatus.FAILED:
            raise ValueError(
                f"Deliverable {self.deliverable_id} failed quality assessment."
            )

        self.status = DeliverableStatus.ACCEPTED
        self.accepted_at = datetime.now()

    def calculate_checksum(self, content: str) -> str:
        """
        Generate a SHA-256 checksum for content associated with a deliverable.

        A checksum can help detect accidental or unauthorized content changes.
        It does not replace access control, digital signatures, or encryption.
        """
        self.checksum = sha256(content.encode("utf-8")).hexdigest()
        return self.checksum


section("1. Deliverable Classification")

deliverables = [
    Deliverable(
        "D-001",
        "Requirements Specification",
        "Approved functional and non-functional requirements",
        DeliverableType.DOCUMENT,
        "Business Analyst",
    ),
    Deliverable(
        "D-002",
        "Solution Architecture",
        "Approved architecture and technical design",
        DeliverableType.DESIGN,
        "Solution Architect",
    ),
    Deliverable(
        "D-003",
        "Application Build",
        "Tested software implementing approved requirements",
        DeliverableType.SOFTWARE,
        "Engineering Lead",
    ),
    Deliverable(
        "D-004",
        "Training Package",
        "Training materials and exercises for users",
        DeliverableType.TRAINING,
        "Training Lead",
    ),
    Deliverable(
        "D-005",
        "Production Release",
        "Deployed and operational solution",
        DeliverableType.TRANSITION,
        "Release Manager",
    ),
]

for item in deliverables:
    print(
        f"{item.deliverable_id}: {item.name:25} "
        f"{item.deliverable_type.value:15} {item.status.value}"
    )


# =============================================================================
# 3. DELIVERABLE CHARACTERISTICS
# =============================================================================

section("2. Characteristics of a Good Deliverable")

good_deliverable_characteristics = {
    "Specific": "The output is clearly defined.",
    "Verifiable": "Its existence and properties can be objectively checked.",
    "Measurable": "Quality and completion can be evaluated.",
    "Traceable": "It can be linked to requirements and project objectives.",
    "Accepted": "An authorized party formally approves it.",
    "Versioned": "Changes can be identified and controlled.",
    "Owned": "Responsibility for creation and maintenance is assigned.",
    "Usable": "It is fit for its intended purpose.",
    "Consistent": "It complies with applicable standards and constraints.",
    "Controlled": "Changes are managed through an appropriate process.",
}

for characteristic, meaning in good_deliverable_characteristics.items():
    print(f"{characteristic:15}: {meaning}")


# =============================================================================
# 4. DELIVERABLE HIERARCHY
# =============================================================================

@dataclass
class WorkPackage:
    work_package_id: str
    name: str
    activities: list[str]
    deliverables: list[str]


@dataclass
class Project:
    project_id: str
    name: str
    objective: str
    work_packages: list[WorkPackage] = field(default_factory=list)
    deliverables: dict[str, Deliverable] = field(default_factory=dict)

    def add_work_package(self, work_package: WorkPackage) -> None:
        self.work_packages.append(work_package)

    def add_deliverable(self, deliverable: Deliverable) -> None:
        if deliverable.deliverable_id in self.deliverables:
            raise ValueError(
                f"Duplicate deliverable ID: {deliverable.deliverable_id}"
            )
        self.deliverables[deliverable.deliverable_id] = deliverable

    def get_deliverable(self, deliverable_id: str) -> Deliverable:
        try:
            return self.deliverables[deliverable_id]
        except KeyError:
            raise KeyError(f"Unknown deliverable: {deliverable_id}") from None


section("3. Work Breakdown and Deliverable Hierarchy")

project = Project(
    project_id="PRJ-001",
    name="Customer Portal Implementation",
    objective="Implement a secure self-service customer portal.",
)

project.add_work_package(
    WorkPackage(
        "WP-01",
        "Requirements",
        ["Conduct interviews", "Analyze current process", "Validate requirements"],
        ["D-001"],
    )
)

project.add_work_package(
    WorkPackage(
        "WP-02",
        "Solution Design",
        ["Design architecture", "Review security", "Approve technical design"],
        ["D-002"],
    )
)

project.add_work_package(
    WorkPackage(
        "WP-03",
        "Development",
        ["Develop modules", "Integrate components", "Perform code review"],
        ["D-003"],
    )
)

for package in project.work_packages:
    print(f"\n{package.work_package_id} - {package.name}")
    print("Activities:")
    for activity in package.activities:
        print(f"  - {activity}")
    print("Deliverables:")
    for deliverable_id in package.deliverables:
        print(f"  - {deliverable_id}")


# =============================================================================
# 5. DELIVERABLE LIFE CYCLE
# =============================================================================

class DeliverableLifecycle:
    """
    A simplified lifecycle:
        Planned
            |
        In Progress
            |
        Ready for Review
            |
        Quality Verification
            |
        Acceptance
            |
        Released / Baselined
    """

    VALID_TRANSITIONS = {
        DeliverableStatus.PLANNED: {
            DeliverableStatus.IN_PROGRESS
        },
        DeliverableStatus.IN_PROGRESS: {
            DeliverableStatus.READY_FOR_REVIEW
        },
        DeliverableStatus.READY_FOR_REVIEW: {
            DeliverableStatus.ACCEPTED,
            DeliverableStatus.REJECTED,
        },
        DeliverableStatus.ACCEPTED: {
            DeliverableStatus.BASELINED,
            DeliverableStatus.RELEASED,
        },
        DeliverableStatus.BASELINED: {
            DeliverableStatus.RELEASED,
        },
        DeliverableStatus.RELEASED: set(),
        DeliverableStatus.REJECTED: {
            DeliverableStatus.IN_PROGRESS
        },
        DeliverableStatus.CLOSED: set(),
    }

    @classmethod
    def transition(
        cls,
        deliverable: Deliverable,
        new_status: DeliverableStatus,
    ) -> None:
        allowed = cls.VALID_TRANSITIONS.get(deliverable.status, set())

        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {deliverable.status.value} -> "
                f"{new_status.value}"
            )

        deliverable.status = new_status


section("4. Deliverable Lifecycle")

lifecycle_demo = Deliverable(
    "D-LIFE",
    "Lifecycle Demonstration",
    "Demonstration of controlled status transitions",
    DeliverableType.DOCUMENT,
    "Project Manager",
)

print("Initial:", lifecycle_demo.status.value)

for new_status in [
    DeliverableStatus.IN_PROGRESS,
    DeliverableStatus.READY_FOR_REVIEW,
]:
    DeliverableLifecycle.transition(lifecycle_demo, new_status)
    print("After transition:", lifecycle_demo.status.value)

try:
    DeliverableLifecycle.transition(
        lifecycle_demo,
        DeliverableStatus.RELEASED,
    )
except ValueError as error:
    print("Blocked invalid transition:", error)


# =============================================================================
# 6. ACCEPTANCE CRITERIA
# =============================================================================

section("5. Acceptance Criteria")

software_deliverable = Deliverable(
    "D-SOFT",
    "Customer Portal",
    "Production-ready customer portal",
    DeliverableType.SOFTWARE,
    "Engineering Lead",
)

software_deliverable.add_acceptance_criterion(
    "AC-01",
    "Users can authenticate with valid credentials.",
    verification_method="Functional test",
)

software_deliverable.add_acceptance_criterion(
    "AC-02",
    "Invalid credentials are rejected.",
    verification_method="Functional test",
)

software_deliverable.add_acceptance_criterion(
    "AC-03",
    "Critical security findings are resolved.",
    verification_method="Security assessment",
)

software_deliverable.add_acceptance_criterion(
    "AC-04",
    "Required documentation is included.",
    verification_method="Inspection",
    mandatory=False,
)

print("Can accept before verification:", software_deliverable.can_be_accepted())

for criterion in software_deliverable.acceptance_criteria:
    print(
        f"{criterion.criterion_id}: "
        f"{criterion.description} | passed={criterion.passed}"
    )

for criterion in software_deliverable.acceptance_criteria:
    if criterion.mandatory:
        software_deliverable.mark_criterion_passed(criterion.criterion_id)

software_deliverable.quality_status = QualityStatus.PASSED

print("Can accept after mandatory criteria pass:",
      software_deliverable.can_be_accepted())

software_deliverable.accept()
print("Status:", software_deliverable.status.value)


# =============================================================================
# 7. REQUIREMENTS TRACEABILITY
# =============================================================================

@dataclass
class Requirement:
    requirement_id: str
    description: str
    priority: str
    source: str


@dataclass
class TraceabilityMatrix:
    requirement_to_deliverables: dict[str, set[str]] = field(default_factory=dict)

    def link(self, requirement_id: str, deliverable_id: str) -> None:
        self.requirement_to_deliverables.setdefault(
            requirement_id, set()
        ).add(deliverable_id)

    def get_deliverables(self, requirement_id: str) -> set[str]:
        return self.requirement_to_deliverables.get(requirement_id, set())

    def orphan_requirements(
        self,
        requirements: Iterable[Requirement],
    ) -> list[Requirement]:
        return [
            requirement
            for requirement in requirements
            if not self.get_deliverables(requirement.requirement_id)
        ]


section("6. Requirements Traceability")

requirements = [
    Requirement("REQ-001", "Users shall log in securely.", "High", "Customer"),
    Requirement("REQ-002", "Users shall view account information.", "High", "Customer"),
    Requirement("REQ-003", "Administrators shall generate reports.", "Medium", "Operations"),
    Requirement("REQ-004", "The portal shall support accessibility requirements.", "High", "Compliance"),
]

traceability = TraceabilityMatrix()

traceability.link("REQ-001", "D-SOFT")
traceability.link("REQ-002", "D-SOFT")
traceability.link("REQ-003", "D-REPORT")
traceability.link("REQ-004", "D-SOFT")

for requirement in requirements:
    print(
        requirement.requirement_id,
        "->",
        sorted(traceability.get_deliverables(requirement.requirement_id)),
    )

print("Orphan requirements:",
      [r.requirement_id for r in traceability.orphan_requirements(requirements)])


# =============================================================================
# 8. QUALITY CONTROL
# =============================================================================

@dataclass
class QualityCheck:
    check_id: str
    description: str
    result: bool
    severity_if_failed: str = "Major"


def evaluate_quality(
    deliverable: Deliverable,
    checks: Iterable[QualityCheck],
) -> QualityStatus:
    checks = list(checks)

    if not checks:
        return QualityStatus.NOT_ASSESSED

    failed_checks = [check for check in checks if not check.result]

    if not failed_checks:
        return QualityStatus.PASSED

    critical_failure = any(
        check.severity_if_failed.lower() == "critical"
        for check in failed_checks
    )

    if critical_failure:
        return QualityStatus.FAILED

    return QualityStatus.CONDITIONALLY_PASSED


section("7. Quality Verification")

quality_checks = [
    QualityCheck("QC-01", "Functional requirements tested", True),
    QualityCheck("QC-02", "Documentation reviewed", True),
    QualityCheck("QC-03", "Security assessment passed", True),
    QualityCheck("QC-04", "Performance target achieved", True),
]

software_deliverable.quality_status = evaluate_quality(
    software_deliverable,
    quality_checks,
)

print("Quality status:", software_deliverable.quality_status.value)


# =============================================================================
# 9. DELIVERABLES VS MILESTONES, OUTCOMES, AND BENEFITS
# =============================================================================

section("8. Deliverable vs Milestone vs Outcome vs Benefit")

comparison = [
    ("Deliverable", "A produced output", "Completed portal"),
    ("Milestone", "A significant project event", "Portal accepted"),
    ("Outcome", "A change resulting from use", "Customers self-serve"),
    ("Benefit", "Value created by the outcome", "Lower support costs"),
]

print(f"{'Concept':15} | {'Meaning':35} | Example")
print("-" * 80)

for concept, meaning, example_text in comparison:
    print(f"{concept:15} | {meaning:35} | {example_text}")


# =============================================================================
# 10. PROJECT MANAGEMENT DELIVERABLE REGISTER
# =============================================================================

@dataclass
class DeliverableRegister:
    items: dict[str, Deliverable] = field(default_factory=dict)

    def add(self, deliverable: Deliverable) -> None:
        if deliverable.deliverable_id in self.items:
            raise ValueError(
                f"Deliverable already exists: {deliverable.deliverable_id}"
            )
        self.items[deliverable.deliverable_id] = deliverable

    def update_status(
        self,
        deliverable_id: str,
        status: DeliverableStatus,
    ) -> None:
        self.items[deliverable_id].status = status

    def by_status(self, status: DeliverableStatus) -> list[Deliverable]:
        return [
            deliverable
            for deliverable in self.items.values()
            if deliverable.status == status
        ]

    def by_type(self, deliverable_type: DeliverableType) -> list[Deliverable]:
        return [
            deliverable
            for deliverable in self.items.values()
            if deliverable.deliverable_type == deliverable_type
        ]

    def completion_percentage(self) -> float:
        if not self.items:
            return 0.0

        completed = sum(
            deliverable.status
            in {
                DeliverableStatus.ACCEPTED,
                DeliverableStatus.BASELINED,
                DeliverableStatus.RELEASED,
                DeliverableStatus.CLOSED,
            }
            for deliverable in self.items.values()
        )

        return completed / len(self.items) * 100


section("9. Deliverable Register")

register = DeliverableRegister()

for deliverable in deliverables:
    register.add(deliverable)

register.add(software_deliverable)

for item in register.items.values():
    print(
        f"{item.deliverable_id:10} | "
        f"{item.name:30} | "
        f"{item.status.value}"
    )

print(f"Completion: {register.completion_percentage():.1f}%")


# =============================================================================
# 11. VERSION CONTROL AND BASELINES
# =============================================================================

@dataclass
class DeliverableVersion:
    version: str
    created_at: datetime
    author: str
    change_description: str
    checksum: str


@dataclass
class VersionHistory:
    deliverable_id: str
    versions: list[DeliverableVersion] = field(default_factory=list)

    def add_version(
        self,
        version: str,
        author: str,
        change_description: str,
        content: str,
    ) -> DeliverableVersion:
        checksum = sha256(content.encode("utf-8")).hexdigest()

        version_record = DeliverableVersion(
            version=version,
            created_at=datetime.now(),
            author=author,
            change_description=change_description,
            checksum=checksum,
        )

        self.versions.append(version_record)
        return version_record

    def latest(self) -> Optional[DeliverableVersion]:
        return self.versions[-1] if self.versions else None


section("10. Versioning and Baselines")

version_history = VersionHistory("D-001")

version_history.add_version(
    "1.0",
    "Business Analyst",
    "Initial approved requirements",
    "requirements version 1.0",
)

version_history.add_version(
    "1.1",
    "Business Analyst",
    "Clarified authentication requirements",
    "requirements version 1.1",
)

latest_version = version_history.latest()

print("Latest version:", latest_version.version if latest_version else "None")
print("Checksum:", latest_version.checksum if latest_version else "None")


# =============================================================================
# 12. CHANGE CONTROL
# =============================================================================

@dataclass
class ChangeRequest:
    change_id: str
    deliverable_id: str
    description: str
    impact_cost: float
    impact_days: int
    impact_scope: str
    risk_level: str
    approved: bool = False


class ChangeControl:
    """Basic change-control decision logic."""

    @staticmethod
    def evaluate(change: ChangeRequest) -> str:
        if change.impact_scope.lower() == "major":
            return "Formal change authority review required."

        if change.risk_level.lower() == "high":
            return "Formal risk and change review required."

        if change.impact_cost > 10000 or change.impact_days > 10:
            return "Formal impact assessment required."

        return "May follow delegated change procedure."


section("11. Change Control")

change = ChangeRequest(
    change_id="CR-001",
    deliverable_id="D-SOFT",
    description="Add multi-factor authentication",
    impact_cost=15000,
    impact_days=8,
    impact_scope="Moderate",
    risk_level="High",
)

print(ChangeControl.evaluate(change))


# =============================================================================
# 13. DEPENDENCIES
# =============================================================================

@dataclass
class DependencyGraph:
    dependencies: dict[str, set[str]] = field(default_factory=dict)

    def add_dependency(self, deliverable: str, depends_on: str) -> None:
        self.dependencies.setdefault(deliverable, set()).add(depends_on)

    def dependencies_of(self, deliverable: str) -> set[str]:
        return self.dependencies.get(deliverable, set())

    def has_direct_cycle(self, deliverable: str, depends_on: str) -> bool:
        return deliverable == depends_on


section("12. Deliverable Dependencies")

dependency_graph = DependencyGraph()

dependency_graph.add_dependency("D-002", "D-001")
dependency_graph.add_dependency("D-003", "D-002")
dependency_graph.add_dependency("D-004", "D-003")
dependency_graph.add_dependency("D-005", "D-003")
dependency_graph.add_dependency("D-005", "D-004")

for deliverable_id, dependencies in dependency_graph.dependencies.items():
    print(f"{deliverable_id} depends on {sorted(dependencies)}")

print(
    "Self-dependency detected:",
    dependency_graph.has_direct_cycle("D-003", "D-003"),
)


# =============================================================================
# 14. DELIVERABLE SCHEDULING
# =============================================================================

@dataclass
class ScheduledDeliverable:
    deliverable_id: str
    planned_start: date
    planned_finish: date
    actual_start: Optional[date] = None
    actual_finish: Optional[date] = None

    @property
    def planned_duration_days(self) -> int:
        return (self.planned_finish - self.planned_start).days + 1

    @property
    def actual_duration_days(self) -> Optional[int]:
        if self.actual_start is None or self.actual_finish is None:
            return None
        return (self.actual_finish - self.actual_start).days + 1

    def schedule_variance_days(self) -> Optional[int]:
        if self.actual_finish is None:
            return None
        return (self.actual_finish - self.planned_finish).days


section("13. Deliverable Scheduling")

scheduled = ScheduledDeliverable(
    "D-003",
    date(2026, 9, 1),
    date(2026, 9, 20),
    date(2026, 9, 3),
    date(2026, 9, 23),
)

print("Planned duration:", scheduled.planned_duration_days, "days")
print("Actual duration:", scheduled.actual_duration_days, "days")
print("Finish variance:", scheduled.schedule_variance_days(), "days")


# =============================================================================
# 15. EFFORT, COST, AND PRODUCTIVITY
# =============================================================================

@dataclass
class DeliveryMetrics:
    planned_hours: float
    actual_hours: float
    planned_cost: float
    actual_cost: float

    @property
    def effort_variance_hours(self) -> float:
        return self.actual_hours - self.planned_hours

    @property
    def cost_variance(self) -> float:
        return self.actual_cost - self.planned_cost

    @property
    def effort_variance_percentage(self) -> float:
        if self.planned_hours == 0:
            return float("inf")
        return (
            (self.actual_hours - self.planned_hours)
            / self.planned_hours
            * 100
        )

    @property
    def cost_variance_percentage(self) -> float:
        if self.planned_cost == 0:
            return float("inf")
        return (
            (self.actual_cost - self.planned_cost)
            / self.planned_cost
            * 100
        )


section("14. Deliverable Performance Metrics")

metrics = DeliveryMetrics(
    planned_hours=800,
    actual_hours=920,
    planned_cost=100000,
    actual_cost=112000,
)

print("Effort variance:", metrics.effort_variance_hours, "hours")
print("Effort variance %:", f"{metrics.effort_variance_percentage:.2f}%")
print("Cost variance:", metrics.cost_variance)
print("Cost variance %:", f"{metrics.cost_variance_percentage:.2f}%")


# =============================================================================
# 16. EARNED VALUE CONCEPTS
# =============================================================================

@dataclass
class EarnedValueMetrics:
    planned_value: float
    earned_value: float
    actual_cost: float

    @property
    def schedule_performance_index(self) -> Optional[float]:
        if self.planned_value == 0:
            return None
        return self.earned_value / self.planned_value

    @property
    def cost_performance_index(self) -> Optional[float]:
        if self.actual_cost == 0:
            return None
        return self.earned_value / self.actual_cost

    @property
    def schedule_variance(self) -> float:
        return self.earned_value - self.planned_value

    @property
    def cost_variance(self) -> float:
        return self.earned_value - self.actual_cost


section("15. Earned Value Applied to Deliverables")

ev = EarnedValueMetrics(
    planned_value=60000,
    earned_value=54000,
    actual_cost=50000,
)

print("Schedule Performance Index:", f"{ev.schedule_performance_index:.2f}")
print("Cost Performance Index:", f"{ev.cost_performance_index:.2f}")
print("Schedule Variance:", ev.schedule_variance)
print("Cost Variance:", ev.cost_variance)


# =============================================================================
# 17. RACI-STYLE ACCOUNTABILITY
# =============================================================================

@dataclass
class ResponsibilityMatrix:
    matrix: dict[str, dict[str, str]] = field(default_factory=dict)

    def assign(self, deliverable_id: str, role: str, responsibility: str) -> None:
        self.matrix.setdefault(deliverable_id, {})[role] = responsibility

    def responsibilities_for(self, deliverable_id: str) -> dict[str, str]:
        return self.matrix.get(deliverable_id, {})


section("16. Responsibility Assignment")

responsibility_matrix = ResponsibilityMatrix()

responsibility_matrix.assign("D-001", "Business Analyst", "R")
responsibility_matrix.assign("D-001", "Project Manager", "A")
responsibility_matrix.assign("D-001", "Customer", "C")
responsibility_matrix.assign("D-001", "Engineering Lead", "I")

for role, responsibility in responsibility_matrix.responsibilities_for("D-001").items():
    print(f"{role:20}: {responsibility}")


# =============================================================================
# 18. STAKEHOLDER ACCEPTANCE
# =============================================================================

@dataclass
class Stakeholder:
    stakeholder_id: str
    name: str
    influence: str
    interest: str


@dataclass
class AcceptanceRecord:
    deliverable_id: str
    stakeholder_id: str
    accepted: bool
    comments: str
    timestamp: datetime = field(default_factory=datetime.now)


section("17. Stakeholder Acceptance")

stakeholders = [
    Stakeholder("S-001", "Business Owner", "High", "High"),
    Stakeholder("S-002", "Compliance", "High", "High"),
    Stakeholder("S-003", "Operations", "Medium", "High"),
]

acceptance_records = [
    AcceptanceRecord(
        "D-SOFT",
        "S-001",
        True,
        "Business requirements satisfied.",
    ),
    AcceptanceRecord(
        "D-SOFT",
        "S-002",
        True,
        "Required controls verified.",
    ),
    AcceptanceRecord(
        "D-SOFT",
        "S-003",
        True,
        "Operational readiness confirmed.",
    ),
]

for record in acceptance_records:
    print(
        record.deliverable_id,
        record.stakeholder_id,
        "Accepted" if record.accepted else "Rejected",
        "-",
        record.comments,
    )


# =============================================================================
# 19. DOCUMENTATION DELIVERABLES
# =============================================================================

@dataclass
class DocumentMetadata:
    title: str
    author: str
    version: str
    classification: str
    approval_status: str
    effective_date: date
    review_date: date

    def validate(self) -> list[str]:
        errors = []

        if not self.title.strip():
            errors.append("Title is required.")

        if not self.author.strip():
            errors.append("Author is required.")

        if not re.fullmatch(r"\d+\.\d+", self.version):
            errors.append("Version should follow a simple major.minor format.")

        if self.review_date < self.effective_date:
            errors.append("Review date cannot precede effective date.")

        return errors


section("18. Document Deliverable Controls")

metadata = DocumentMetadata(
    title="Requirements Specification",
    author="Business Analyst",
    version="1.0",
    classification="Internal",
    approval_status="Approved",
    effective_date=date(2026, 9, 1),
    review_date=date(2027, 3, 1),
)

print("Metadata validation:", metadata.validate())


# =============================================================================
# 20. DIGITAL FILE DELIVERABLES
# =============================================================================

def write_deliverable_file(
    directory: Path,
    filename: str,
    content: str,
) -> Path:
    """
    Safely write a deliverable to a designated directory.

    Path resolution is checked to prevent accidental traversal outside the
    intended directory.
    """
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)

    target = (directory / filename).resolve()

    if directory not in target.parents:
        raise ValueError("Target path escapes the deliverable directory.")

    target.write_text(content, encoding="utf-8")
    return target


section("19. File-Based Deliverable")

with tempfile.TemporaryDirectory() as temporary_directory:
    output_directory = Path(temporary_directory) / "deliverables"

    content = """
Customer Portal Requirements
============================
Version: 1.0
Status: Approved

REQ-001: Users shall authenticate securely.
REQ-002: Users shall view account information.
""".strip()

    path = write_deliverable_file(
        output_directory,
        "requirements.txt",
        content,
    )

    print("Created:", path.name)
    print("Content:")
    print(path.read_text(encoding="utf-8"))


# =============================================================================
# 21. DATA DELIVERABLES
# =============================================================================

def validate_records(
    records: list[dict[str, Any]],
    required_fields: set[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    valid = []
    errors = []

    for index, record in enumerate(records, start=1):
        missing = required_fields - record.keys()

        if missing:
            errors.append(
                f"Record {index}: missing fields {sorted(missing)}"
            )
            continue

        valid.append(record)

    return valid, errors


section("20. Data Deliverable Validation")

customer_data = [
    {"customer_id": "C001", "name": "Customer A", "status": "Active"},
    {"customer_id": "C002", "name": "Customer B", "status": "Active"},
    {"customer_id": "C003", "status": "Inactive"},
]

valid_records, validation_errors = validate_records(
    customer_data,
    {"customer_id", "name", "status"},
)

print("Valid records:", len(valid_records))
print("Validation errors:")
for error in validation_errors:
    print(" ", error)


# =============================================================================
# 22. SOFTWARE DELIVERABLE TESTING
# =============================================================================

def calculate_discounted_price(
    price: float,
    discount_percentage: float,
) -> float:
    """
    Calculate a discounted price.

    Business rules:
    - Price cannot be negative.
    - Discount must be between 0 and 100 inclusive.
    """
    if price < 0:
        raise ValueError("Price cannot be negative.")

    if not 0 <= discount_percentage <= 100:
        raise ValueError("Discount must be between 0 and 100.")

    return round(price * (1 - discount_percentage / 100), 2)


section("21. Software Deliverable Example")

for price, discount in [
    (1000, 10),
    (500, 0),
    (800, 100),
]:
    print(
        f"Price={price}, discount={discount}% -> "
        f"{calculate_discounted_price(price, discount)}"
    )

try:
    calculate_discounted_price(-100, 10)
except ValueError as error:
    print("Edge case:", error)

try:
    calculate_discounted_price(100, 120)
except ValueError as error:
    print("Edge case:", error)


# =============================================================================
# 23. TESTING PYRAMID CONCEPTS
# =============================================================================

class TestDiscountFunction(unittest.TestCase):
    def test_no_discount(self):
        self.assertEqual(calculate_discounted_price(100, 0), 100)

    def test_ten_percent_discount(self):
        self.assertEqual(calculate_discounted_price(100, 10), 90)

    def test_full_discount(self):
        self.assertEqual(calculate_discounted_price(100, 100), 0)

    def test_negative_price(self):
        with self.assertRaises(ValueError):
            calculate_discounted_price(-1, 10)

    def test_invalid_discount(self):
        with self.assertRaises(ValueError):
            calculate_discounted_price(100, 101)


section("22. Automated Acceptance Tests")

test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(
    TestDiscountFunction
)

test_result = unittest.TextTestRunner(verbosity=1).run(test_suite)

print(
    "Tests passed:",
    test_result.testsRun - len(test_result.failures) - len(test_result.errors),
    "/",
    test_result.testsRun,
)


# =============================================================================
# 24. DEFECT MANAGEMENT
# =============================================================================

class DefectSeverity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DefectStatus(Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    FIXED = "Fixed"
    VERIFIED = "Verified"
    CLOSED = "Closed"
    REOPENED = "Reopened"


@dataclass
class Defect:
    defect_id: str
    deliverable_id: str
    description: str
    severity: DefectSeverity
    status: DefectStatus = DefectStatus.OPEN
    discovered_by: str = ""
    resolution: Optional[str] = None

    def close(self) -> None:
        if self.status != DefectStatus.VERIFIED:
            raise ValueError(
                "A defect must be verified before it can be closed."
            )
        self.status = DefectStatus.CLOSED


section("23. Defect Management")

defect = Defect(
    "BUG-001",
    "D-SOFT",
    "Password reset link expires incorrectly.",
    DefectSeverity.HIGH,
    discovered_by="QA",
)

print("Initial defect status:", defect.status.value)

defect.status = DefectStatus.IN_PROGRESS
defect.status = DefectStatus.FIXED
defect.status = DefectStatus.VERIFIED
defect.resolution = "Corrected expiration calculation."

defect.close()

print("Final defect status:", defect.status.value)


# =============================================================================
# 25. DEFINITION OF DONE VS ACCEPTANCE
# =============================================================================

section("24. Definition of Done vs Acceptance Criteria")

distinction = {
    "Definition of Done":
        "Internal completion standard indicating that work is complete.",
    "Acceptance Criteria":
        "Specific conditions that a deliverable must satisfy to be accepted.",
    "Quality Standard":
        "Required characteristics or thresholds used to assess quality.",
    "Exit Criteria":
        "Conditions that must be satisfied before a stage or release can proceed.",
}

for concept, explanation in distinction.items():
    print(f"{concept:25}: {explanation}")


# =============================================================================
# 26. AGILE AND ITERATIVE DELIVERABLES
# =============================================================================

@dataclass
class Increment:
    increment_id: str
    sprint: str
    deliverables: list[str]
    potentially_releasable: bool
    accepted: bool = False

    def accept(self) -> None:
        if not self.potentially_releasable:
            raise ValueError(
                "Increment is not potentially releasable."
            )
        self.accepted = True


section("25. Iterative and Agile Deliverables")

increment = Increment(
    "INC-01",
    "Sprint 4",
    ["Login module", "Password reset", "Audit logging"],
    potentially_releasable=True,
)

print("Increment:", increment.increment_id)
print("Sprint:", increment.sprint)
print("Deliverables:", increment.deliverables)

increment.accept()
print("Accepted:", increment.accepted)


# =============================================================================
# 27. PRODUCT VS PROJECT DELIVERABLES
# =============================================================================

section("26. Project vs Product Perspective")

project_product_comparison = {
    "Project deliverable":
        "A specific output produced as part of project work.",
    "Product increment":
        "A usable addition or improvement to a product.",
    "Operational output":
        "An output required to run or support a service.",
    "Project management deliverable":
        "A management artifact such as a plan, report, register, or decision record.",
}

for concept, meaning in project_product_comparison.items():
    print(f"{concept:28}: {meaning}")


# =============================================================================
# 28. INTERNAL VS EXTERNAL DELIVERABLES
# =============================================================================

section("27. Internal and External Deliverables")

internal_external = [
    ("Internal", "Project status report", "Supports governance and decision-making"),
    ("Internal", "Risk register", "Supports risk management"),
    ("Internal", "Issue log", "Tracks problems requiring resolution"),
    ("External", "Customer portal", "Delivered to customer"),
    ("External", "Training package", "Provided to users"),
    ("External", "Operations manual", "Transferred to operational teams"),
]

for audience, name, purpose in internal_external:
    print(f"{audience:10} | {name:25} | {purpose}")


# =============================================================================
# 29. DELIVERABLE READINESS CHECKLIST
# =============================================================================

@dataclass
class ReadinessChecklist:
    requirements_complete: bool
    quality_verified: bool
    documentation_complete: bool
    security_review_complete: bool
    dependencies_resolved: bool
    acceptance_ready: bool
    operational_readiness: bool

    def is_ready(self) -> bool:
        return all(vars(self).values())

    def failed_items(self) -> list[str]:
        return [
            field_name
            for field_name, value in vars(self).items()
            if not value
        ]


section("28. Deliverable Readiness")

readiness = ReadinessChecklist(
    requirements_complete=True,
    quality_verified=True,
    documentation_complete=True,
    security_review_complete=True,
    dependencies_resolved=True,
    acceptance_ready=True,
    operational_readiness=False,
)

print("Ready for release:", readiness.is_ready())
print("Outstanding checks:", readiness.failed_items())


# =============================================================================
# 30. RELEASE MANAGEMENT
# =============================================================================

@dataclass
class Release:
    release_id: str
    version: str
    deliverables: list[str]
    release_date: date
    rollback_plan: str
    approved: bool = False

    def validate(self) -> list[str]:
        errors = []

        if not self.version:
            errors.append("Release version is required.")

        if not self.deliverables:
            errors.append("At least one deliverable is required.")

        if not self.rollback_plan.strip():
            errors.append("Rollback plan is required.")

        return errors


section("29. Release Deliverables")

release = Release(
    release_id="REL-001",
    version="2.0.0",
    deliverables=["D-SOFT", "D-004"],
    release_date=date(2026, 10, 1),
    rollback_plan="Restore the previous production release.",
)

print("Release validation:", release.validate())


# =============================================================================
# 31. SECURITY CONSIDERATIONS
# =============================================================================

section("30. Security Considerations")

security_principles = [
    "Apply least privilege to deliverable repositories.",
    "Control access to confidential project artifacts.",
    "Protect sensitive data contained in deliverables.",
    "Maintain audit trails for important approvals and changes.",
    "Verify integrity using appropriate controls such as checksums or signatures.",
    "Avoid embedding secrets, passwords, API keys, or credentials in deliverables.",
    "Classify information according to organizational requirements.",
    "Securely dispose of obsolete sensitive artifacts.",
]

for principle in security_principles:
    print("-", principle)


# =============================================================================
# 32. RISK-BASED ACCEPTANCE
# =============================================================================

@dataclass
class Risk:
    risk_id: str
    description: str
    probability: float
    impact: float
    mitigation: str

    @property
    def score(self) -> float:
        return self.probability * self.impact


section("31. Risk-Based Deliverable Assessment")

risks = [
    Risk(
        "R-001",
        "Critical security vulnerability remains unresolved.",
        0.2,
        10,
        "Resolve before production release.",
    ),
    Risk(
        "R-002",
        "Minor formatting defect in report.",
        0.8,
        1,
        "Correct during document cleanup.",
    ),
]

for risk in risks:
    print(
        f"{risk.risk_id}: score={risk.score:.1f} | "
        f"{risk.description}"
    )


# =============================================================================
# 33. PERFORMANCE AND SCALABILITY
# =============================================================================

def count_deliverables_by_type(
    deliverable_collection: Iterable[Deliverable],
) -> dict[DeliverableType, int]:
    counts: dict[DeliverableType, int] = {}

    for deliverable in deliverable_collection:
        counts[deliverable.deliverable_type] = (
            counts.get(deliverable.deliverable_type, 0) + 1
        )

    return counts


section("32. Performance Considerations")

many_deliverables = [
    Deliverable(
        f"D-{index:05}",
        f"Deliverable {index}",
        "Generated demonstration deliverable",
        DeliverableType.DOCUMENT,
        "Owner",
    )
    for index in range(1, 1001)
]

counts = count_deliverables_by_type(many_deliverables)

print("Number of deliverables:", len(many_deliverables))
print("Counts by type:", {key.value: value for key, value in counts.items()})

print(
    "Lookup by dictionary ID is approximately O(1) average case, "
    "whereas scanning a list is O(n)."
)


# =============================================================================
# 34. QUALITY METRICS
# =============================================================================

@dataclass
class QualityMetrics:
    total_deliverables: int
    accepted_deliverables: int
    defects_found: int
    defects_closed: int
    rework_hours: float

    @property
    def acceptance_rate(self) -> float:
        if self.total_deliverables == 0:
            return 0.0
        return self.accepted_deliverables / self.total_deliverables * 100

    @property
    def defect_closure_rate(self) -> float:
        if self.defects_found == 0:
            return 100.0
        return self.defects_closed / self.defects_found * 100

    @property
    def defects_per_deliverable(self) -> float:
        if self.total_deliverables == 0:
            return 0.0
        return self.defects_found / self.total_deliverables


section("33. Quality Metrics")

quality_metrics = QualityMetrics(
    total_deliverables=20,
    accepted_deliverables=17,
    defects_found=12,
    defects_closed=10,
    rework_hours=64,
)

print("Acceptance rate:", f"{quality_metrics.acceptance_rate:.2f}%")
print("Defect closure rate:", f"{quality_metrics.defect_closure_rate:.2f}%")
print("Defects per deliverable:",
      f"{quality_metrics.defects_per_deliverable:.2f}")
print("Rework hours:", quality_metrics.rework_hours)


# =============================================================================
# 35. PROCESS CAPABILITY AND REWORK
# =============================================================================

@dataclass
class ReworkAnalysis:
    original_hours: float
    rework_hours: float

    @property
    def rework_percentage(self) -> float:
        total = self.original_hours + self.rework_hours

        if total == 0:
            return 0.0

        return self.rework_hours / total * 100


section("34. Rework Analysis")

rework = ReworkAnalysis(
    original_hours=1000,
    rework_hours=120,
)

print("Rework percentage:", f"{rework.rework_percentage:.2f}%")


# =============================================================================
# 36. VALUE AND PRIORITIZATION
# =============================================================================

@dataclass
class PrioritizedDeliverable:
    deliverable: Deliverable
    business_value: float
    urgency: float
    risk_reduction: float
    effort: float

    @property
    def priority_score(self) -> float:
        if self.effort <= 0:
            return float("inf")

        return (
            self.business_value
            + self.urgency
            + self.risk_reduction
        ) / self.effort


section("35. Deliverable Prioritization")

priority_items = [
    PrioritizedDeliverable(
        deliverables[0],
        business_value=8,
        urgency=7,
        risk_reduction=6,
        effort=5,
    ),
    PrioritizedDeliverable(
        deliverables[1],
        business_value=9,
        urgency=5,
        risk_reduction=8,
        effort=8,
    ),
    PrioritizedDeliverable(
        deliverables[2],
        business_value=10,
        urgency=9,
        risk_reduction=9,
        effort=12,
    ),
]

for item in sorted(
    priority_items,
    key=lambda item: item.priority_score,
    reverse=True,
):
    print(
        f"{item.deliverable.name:30} "
        f"score={item.priority_score:.2f}"
    )


# =============================================================================
# 37. DELIVERABLE COMPLEXITY
# =============================================================================

def estimate_complexity(
    dependencies: int,
    acceptance_criteria: int,
    stakeholders: int,
    risk_count: int,
) -> str:
    score = (
        dependencies * 2
        + acceptance_criteria
        + stakeholders
        + risk_count * 2
    )

    if score <= 5:
        return "Low"
    if score <= 12:
        return "Medium"
    if score <= 20:
        return "High"
    return "Very High"


section("36. Deliverable Complexity")

complexity = estimate_complexity(
    dependencies=3,
    acceptance_criteria=8,
    stakeholders=5,
    risk_count=4,
)

print("Estimated complexity:", complexity)


# =============================================================================
# 38. PRODUCTION HANDOVER
# =============================================================================

@dataclass
class HandoverPackage:
    deliverable_id: str
    technical_documentation: bool
    user_documentation: bool
    support_procedure: bool
    monitoring_configuration: bool
    ownership_transfer: bool
    training_completed: bool

    def is_complete(self) -> bool:
        return all(vars(self).values())


section("37. Operational Handover")

handover = HandoverPackage(
    deliverable_id="D-SOFT",
    technical_documentation=True,
    user_documentation=True,
    support_procedure=True,
    monitoring_configuration=True,
    ownership_transfer=True,
    training_completed=False,
)

print("Handover complete:", handover.is_complete())
print(
    "Training is mandatory in this example:",
    not handover.training_completed,
)


# =============================================================================
# 39. KNOWLEDGE TRANSFER
# =============================================================================

@dataclass
class KnowledgeTransferRecord:
    subject: str
    trainer: str
    audience: list[str]
    session_date: date
    material_reference: str
    completed: bool


section("38. Knowledge Transfer")

knowledge_transfer = KnowledgeTransferRecord(
    subject="Production Support Procedures",
    trainer="Technical Lead",
    audience=["Support Team", "Operations Team"],
    session_date=date(2026, 9, 25),
    material_reference="KT-001",
    completed=True,
)

print("Knowledge transfer completed:", knowledge_transfer.completed)


# =============================================================================
# 40. CLOSURE
# =============================================================================

@dataclass
class ClosureAssessment:
    deliverables_accepted: bool
    outstanding_defects_resolved: bool
    documentation_archived: bool
    ownership_transferred: bool
    lessons_recorded: bool
    contracts_or_procurements_closed: bool

    def is_project_ready_for_closure(self) -> bool:
        return all(vars(self).values())


section("39. Project Closure Readiness")

closure = ClosureAssessment(
    deliverables_accepted=True,
    outstanding_defects_resolved=True,
    documentation_archived=True,
    ownership_transferred=True,
    lessons_recorded=True,
    contracts_or_procurements_closed=True,
)

print(
    "Project closure readiness:",
    closure.is_project_ready_for_closure(),
)


# =============================================================================
# 41. SERIALIZATION
# =============================================================================

def deliverable_to_dict(deliverable: Deliverable) -> dict[str, Any]:
    return {
        "deliverable_id": deliverable.deliverable_id,
        "name": deliverable.name,
        "description": deliverable.description,
        "type": deliverable.deliverable_type.value,
        "owner": deliverable.owner,
        "version": deliverable.version,
        "status": deliverable.status.value,
        "quality_status": deliverable.quality_status.value,
        "dependencies": deliverable.dependencies,
        "stakeholders": deliverable.stakeholders,
        "risks": deliverable.risks,
        "acceptance_criteria": [
            {
                "criterion_id": criterion.criterion_id,
                "description": criterion.description,
                "mandatory": criterion.mandatory,
                "verification_method": criterion.verification_method,
                "passed": criterion.passed,
            }
            for criterion in deliverable.acceptance_criteria
        ],
        "checksum": deliverable.checksum,
    }


section("40. Structured Deliverable Records")

serialized = deliverable_to_dict(software_deliverable)
print(json.dumps(serialized, indent=2))


# =============================================================================
# 42. PORTFOLIO-LEVEL REPORTING
# =============================================================================

@dataclass
class ProjectPortfolio:
    projects: list[Project] = field(default_factory=list)

    def total_deliverables(self) -> int:
        return sum(len(project.deliverables) for project in self.projects)

    def accepted_deliverables(self) -> int:
        return sum(
            sum(
                deliverable.status
                in {
                    DeliverableStatus.ACCEPTED,
                    DeliverableStatus.BASELINED,
                    DeliverableStatus.RELEASED,
                    DeliverableStatus.CLOSED,
                }
                for deliverable in project.deliverables.values()
            )
            for project in self.projects
        )

    def acceptance_rate(self) -> float:
        total = self.total_deliverables()

        if total == 0:
            return 0.0

        return self.accepted_deliverables() / total * 100


section("41. Portfolio-Level Deliverable Reporting")

project.add_deliverable(software_deliverable)

portfolio = ProjectPortfolio([project])

print("Portfolio deliverables:", portfolio.total_deliverables())
print("Accepted deliverables:", portfolio.accepted_deliverables())
print("Acceptance rate:", f"{portfolio.acceptance_rate():.2f}%")


# =============================================================================
# 43. COMMON FAILURE MODES
# =============================================================================

section("42. Common Deliverable Failure Modes")

failure_modes = {
    "Vague definition":
        "Nobody can objectively determine what must be produced.",
    "No owner":
        "Responsibility for creation or approval is unclear.",
    "No acceptance criteria":
        "Completion becomes subjective and disputes increase.",
    "Uncontrolled changes":
        "The delivered output diverges from the approved baseline.",
    "Missing traceability":
        "It becomes difficult to demonstrate which requirements were satisfied.",
    "Weak quality control":
        "Defects are discovered late or by the customer.",
    "Premature acceptance":
        "A deliverable is accepted before required verification.",
    "No version control":
        "Teams cannot reliably identify which artifact is current.",
    "No operational handover":
        "The output may work technically but fail in real operation.",
    "Ignoring dependencies":
        "A deliverable may be completed but unusable because prerequisite outputs are incomplete.",
}

for failure, consequence in failure_modes.items():
    print(f"{failure:25}: {consequence}")


# =============================================================================
# 44. ADVANCED EDGE CASES
# =============================================================================

section("43. Edge Cases")

# Zero-value denominator.
zero_metrics = DeliveryMetrics(
    planned_hours=0,
    actual_hours=10,
    planned_cost=0,
    actual_cost=100,
)

print(
    "Zero planned hours variance:",
    zero_metrics.effort_variance_percentage,
)

print(
    "Zero planned cost variance:",
    zero_metrics.cost_variance_percentage,
)

# Empty deliverable register.
empty_register = DeliverableRegister()
print(
    "Empty register completion:",
    empty_register.completion_percentage(),
)

# Deliverable without acceptance criteria.
no_criteria = Deliverable(
    "D-EDGE",
    "No Criteria Example",
    "Illustrates an important governance edge case",
    DeliverableType.DOCUMENT,
    "Owner",
)

print(
    "No-criteria deliverable can be accepted:",
    no_criteria.can_be_accepted(),
)

# A deliverable with no mandatory criteria can pass the logical test, but
# organizations may deliberately prohibit this. The implementation should
# reflect the organization's governance policy rather than assuming that
# absence of criteria automatically means acceptance is appropriate.


# =============================================================================
# 45. GOVERNANCE POLICY
# =============================================================================

@dataclass
class DeliverableGovernancePolicy:
    require_owner: bool = True
    require_acceptance_criteria: bool = True
    require_quality_assessment: bool = True
    require_version: bool = True
    require_traceability: bool = True

    def validate(self, deliverable: Deliverable) -> list[str]:
        violations = []

        if self.require_owner and not deliverable.owner.strip():
            violations.append("Deliverable owner is missing.")

        if (
            self.require_acceptance_criteria
            and not deliverable.acceptance_criteria
        ):
            violations.append("Acceptance criteria are missing.")

        if (
            self.require_quality_assessment
            and deliverable.quality_status
            == QualityStatus.NOT_ASSESSED
        ):
            violations.append("Quality assessment is incomplete.")

        if self.require_version and not deliverable.version.strip():
            violations.append("Version is missing.")

        return violations


section("44. Governance Policy Validation")

policy = DeliverableGovernancePolicy()

governance_violations = policy.validate(no_criteria)

print("Governance violations:")
for violation in governance_violations:
    print("-", violation)


# =============================================================================
# 46. PRACTICAL END-TO-END EXAMPLE
# =============================================================================

section("45. End-to-End Deliverable Example")

end_to_end = Deliverable(
    deliverable_id="D-E2E",
    name="Customer Analytics Dashboard",
    description="A validated dashboard for customer performance analysis.",
    deliverable_type=DeliverableType.SOFTWARE,
    owner="Analytics Team",
    version="1.0",
    stakeholders=["Business Owner", "Finance", "Operations"],
    dependencies=["D-001"],
    risks=["Incorrect KPI definitions", "Unauthorized data access"],
)

end_to_end.add_acceptance_criterion(
    "AC-E2E-01",
    "All approved KPIs are displayed correctly.",
    verification_method="Data validation",
)

end_to_end.add_acceptance_criterion(
    "AC-E2E-02",
    "Authorized users can access the dashboard.",
    verification_method="Access-control test",
)

end_to_end.add_acceptance_criterion(
    "AC-E2E-03",
    "Unauthorized users cannot access restricted information.",
    verification_method="Security test",
)

print("1. Planned")
print("   Status:", end_to_end.status.value)

DeliverableLifecycle.transition(
    end_to_end,
    DeliverableStatus.IN_PROGRESS,
)

print("2. Work performed")
print("   Status:", end_to_end.status.value)

for criterion in end_to_end.acceptance_criteria:
    end_to_end.mark_criterion_passed(criterion.criterion_id)

end_to_end.quality_status = QualityStatus.PASSED

DeliverableLifecycle.transition(
    end_to_end,
    DeliverableStatus.READY_FOR_REVIEW,
)

print("3. Verification complete")
print("   Quality:", end_to_end.quality_status.value)
print("   Criteria satisfied:", end_to_end.can_be_accepted())

end_to_end.accept()

print("4. Accepted")
print("   Status:", end_to_end.status.value)
print("   Accepted at:", end_to_end.accepted_at)

checksum = end_to_end.calculate_checksum(
    "Customer Analytics Dashboard version 1.0"
)

print("5. Integrity checksum:", checksum)

DeliverableLifecycle.transition(
    end_to_end,
    DeliverableStatus.RELEASED,
)

print("6. Released")
print("   Status:", end_to_end.status.value)


# =============================================================================
# 47. FINAL VALIDATION ENGINE
# =============================================================================

@dataclass
class DeliverableValidationResult:
    deliverable_id: str
    passed: bool
    errors: list[str]
    warnings: list[str]


class DeliverableValidator:
    """
    Central validation component.

    This intentionally distinguishes errors from warnings:
    - Errors prevent acceptance.
    - Warnings may require review but do not necessarily prevent acceptance.
    """

    def validate(
        self,
        deliverable: Deliverable,
    ) -> DeliverableValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not deliverable.deliverable_id.strip():
            errors.append("Deliverable ID is missing.")

        if not deliverable.name.strip():
            errors.append("Deliverable name is missing.")

        if not deliverable.description.strip():
            warnings.append("Deliverable description is empty.")

        if not deliverable.owner.strip():
            errors.append("Deliverable owner is missing.")

        if not deliverable.acceptance_criteria:
            errors.append("No acceptance criteria have been defined.")

        if deliverable.quality_status == QualityStatus.NOT_ASSESSED:
            errors.append("Quality assessment has not been completed.")

        if deliverable.status == DeliverableStatus.ACCEPTED:
            if not deliverable.can_be_accepted():
                errors.append(
                    "Deliverable is marked accepted without satisfying "
                    "mandatory acceptance criteria."
                )

        return DeliverableValidationResult(
            deliverable_id=deliverable.deliverable_id,
            passed=not errors,
            errors=errors,
            warnings=warnings,
        )


section("46. Final Validation Engine")

validator = DeliverableValidator()

validation_result = validator.validate(end_to_end)

print("Validation passed:", validation_result.passed)
print("Errors:", validation_result.errors)
print("Warnings:", validation_result.warnings)


# =============================================================================
# 48. KEY PRINCIPLES AS EXECUTABLE DATA
# =============================================================================

section("47. Core Principles")

core_principles = [
    "Define deliverables before execution where practical.",
    "Make deliverables objectively verifiable.",
    "Assign clear ownership.",
    "Define acceptance criteria before evaluation.",
    "Trace deliverables to requirements and objectives.",
    "Control changes after baseline approval.",
    "Use appropriate quality assurance and quality control.",
    "Version important artifacts.",
    "Record formal acceptance.",
    "Protect sensitive deliverables.",
    "Plan dependencies and handoffs.",
    "Verify operational readiness before transition.",
    "Measure quality, schedule, cost, and rework where useful.",
    "Archive records according to governance requirements.",
]

for number, principle in enumerate(core_principles, start=1):
    print(f"{number:2}. {principle}")


# =============================================================================
# 49. KNOWLEDGE CHECK
# =============================================================================

section("48. Knowledge Check")

questions = [
    (
        "What is a deliverable?",
        "A distinct, verifiable output produced by project work.",
    ),
    (
        "How is a deliverable different from an activity?",
        "An activity is work performed; a deliverable is an output produced.",
    ),
    (
        "Why are acceptance criteria important?",
        "They establish objective conditions for determining whether a deliverable is acceptable.",
    ),
    (
        "Why is traceability important?",
        "It connects requirements to outputs and provides evidence of coverage.",
    ),
    (
        "Why is version control important?",
        "It identifies artifact revisions and supports controlled change management.",
    ),
    (
        "Can a completed activity guarantee an accepted deliverable?",
        "No. Completion of work does not automatically prove quality or acceptance.",
    ),
    (
        "What is a milestone?",
        "A significant project event or checkpoint, not necessarily an output.",
    ),
    (
        "What is an outcome?",
        "A change or result enabled by the use of project outputs.",
    ),
]

for question, answer in questions:
    print(f"\nQ: {question}")
    print(f"A: {answer}")


# =============================================================================
# 50. SCRIPT COMPLETION
# =============================================================================

section("49. Script Execution Complete")

print(
    "The examples above demonstrate project deliverables from basic "
    "definition and classification through acceptance, quality, "
    "traceability, change control, security, release, handover, "
    "measurement, governance, and closure."
)
