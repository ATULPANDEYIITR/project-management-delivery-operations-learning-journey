"""
Scope Control: Managing Changes to Scope

A comprehensive standalone study and demonstration of scope control in
project management and software delivery.

The examples model how a project team defines a baseline, evaluates change
requests, analyzes impacts, applies approval rules, updates controlled
baselines, maintains traceability, and reports scope status.

The script intentionally uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import math
import statistics
import textwrap
import unittest


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_term(term: str, definition: str) -> None:
    print(f"\n{term}")
    print(f"  {definition}")


def demonstrate_fundamentals() -> None:
    print_section("1. FUNDAMENTAL CONCEPTS")

    terms = {
        "Scope":
            "The boundaries of what a project will and will not deliver.",
        "Product Scope":
            "The features, characteristics, functions, and outcomes of the "
            "product, service, or result being created.",
        "Project Scope":
            "The work required to produce the agreed product, service, or result.",
        "Scope Baseline":
            "The approved reference point against which scope changes are "
            "evaluated and controlled.",
        "Scope Creep":
            "Uncontrolled expansion of scope without corresponding formal "
            "evaluation and approval.",
        "Change Request":
            "A documented proposal to modify an approved requirement, "
            "deliverable, constraint, assumption, or other baseline element.",
        "Change Control":
            "The structured process used to identify, analyze, approve, "
            "reject, implement, and document changes.",
        "Traceability":
            "The ability to connect requirements to deliverables, tests, "
            "changes, decisions, and evidence.",
        "Gold Plating":
            "Adding functionality or quality beyond the agreed requirement "
            "without authorized scope change.",
        "Scope Freeze":
            "A management state in which changes require explicit formal "
            "authorization rather than informal acceptance.",
    }

    for term, definition in terms.items():
        explain_term(term, definition)


# ---------------------------------------------------------------------------
# 2. SCOPE MODEL
# ---------------------------------------------------------------------------

class ScopeStatus(Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    REMOVED = "Removed"


class ChangeStatus(Enum):
    PROPOSED = "Proposed"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    DEFERRED = "Deferred"
    IMPLEMENTED = "Implemented"


class Priority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class Deliverable:
    deliverable_id: str
    name: str
    description: str
    estimated_hours: float
    estimated_cost: float
    status: ScopeStatus = ScopeStatus.PLANNED
    requirements: Set[str] = field(default_factory=set)

    def validate(self) -> None:
        if not self.deliverable_id.strip():
            raise ValueError("Deliverable ID cannot be empty.")
        if not self.name.strip():
            raise ValueError("Deliverable name cannot be empty.")
        if self.estimated_hours < 0:
            raise ValueError("Estimated hours cannot be negative.")
        if self.estimated_cost < 0:
            raise ValueError("Estimated cost cannot be negative.")


@dataclass
class Requirement:
    requirement_id: str
    title: str
    description: str
    priority: Priority
    acceptance_criteria: List[str]
    deliverable_ids: Set[str] = field(default_factory=set)

    def validate(self) -> None:
        if not self.requirement_id.strip():
            raise ValueError("Requirement ID cannot be empty.")
        if not self.title.strip():
            raise ValueError("Requirement title cannot be empty.")
        if not self.acceptance_criteria:
            raise ValueError(
                f"{self.requirement_id} must have acceptance criteria."
            )


@dataclass
class ScopeBaseline:
    version: str
    approved_date: date
    deliverables: Dict[str, Deliverable]
    requirements: Dict[str, Requirement]

    def total_hours(self) -> float:
        return sum(
            item.estimated_hours
            for item in self.deliverables.values()
            if item.status != ScopeStatus.REMOVED
        )

    def total_cost(self) -> float:
        return sum(
            item.estimated_cost
            for item in self.deliverables.values()
            if item.status != ScopeStatus.REMOVED
        )

    def validate(self) -> None:
        for deliverable in self.deliverables.values():
            deliverable.validate()

        for requirement in self.requirements.values():
            requirement.validate()

        for requirement in self.requirements.values():
            for deliverable_id in requirement.deliverable_ids:
                if deliverable_id not in self.deliverables:
                    raise ValueError(
                        f"{requirement.requirement_id} references unknown "
                        f"deliverable {deliverable_id}."
                    )


# ---------------------------------------------------------------------------
# 3. CHANGE IMPACT MODEL
# ---------------------------------------------------------------------------

@dataclass
class ImpactAnalysis:
    scope_delta: float
    schedule_delta_days: float
    cost_delta: float
    resource_delta_hours: float
    quality_risk: float
    technical_risk: float
    compliance_risk: float
    operational_risk: float
    dependencies: List[str]
    assumptions: List[str]

    def total_risk_score(self) -> float:
        risks = [
            self.quality_risk,
            self.technical_risk,
            self.compliance_risk,
            self.operational_risk,
        ]
        return statistics.mean(risks)

    def net_impact_score(self) -> float:
        """
        A deliberately transparent scoring mechanism.

        This is not a universal project-management formula. Organizations
        should define their own governance model, thresholds, and weighting.
        """
        risk_component = self.total_risk_score() * 2.0
        schedule_component = max(0.0, self.schedule_delta_days) * 0.25
        cost_component = max(0.0, self.cost_delta) / 10000
        return risk_component + schedule_component + cost_component


@dataclass
class ChangeRequest:
    change_id: str
    title: str
    requester: str
    description: str
    reason: str
    priority: Priority
    proposed_date: date
    affected_requirements: Set[str] = field(default_factory=set)
    affected_deliverables: Set[str] = field(default_factory=set)
    impact: Optional[ImpactAnalysis] = None
    status: ChangeStatus = ChangeStatus.PROPOSED
    decision: str = ""
    decision_date: Optional[date] = None
    implementation_notes: str = ""

    def validate(self) -> None:
        if not self.change_id.strip():
            raise ValueError("Change ID cannot be empty.")
        if not self.title.strip():
            raise ValueError("Change title cannot be empty.")
        if not self.requester.strip():
            raise ValueError("Requester cannot be empty.")
        if not self.description.strip():
            raise ValueError("Change description cannot be empty.")

    def attach_impact_analysis(self, impact: ImpactAnalysis) -> None:
        self.impact = impact
        self.status = ChangeStatus.UNDER_REVIEW


@dataclass
class ChangeDecision:
    change_id: str
    decision: ChangeStatus
    authority: str
    rationale: str
    timestamp: datetime


@dataclass
class AuditEntry:
    timestamp: datetime
    actor: str
    action: str
    object_id: str
    details: str


# ---------------------------------------------------------------------------
# 4. SCOPE CONTROL ENGINE
# ---------------------------------------------------------------------------

class ScopeControlEngine:
    """
    Coordinates scope baseline, change requests, decisions, implementation,
    and audit history.

    A production system would normally persist these objects in a database
    and integrate authorization, notifications, workflow, and reporting.
    """

    def __init__(
        self,
        baseline: ScopeBaseline,
        approval_cost_threshold: float = 5000.0,
        approval_schedule_threshold: float = 5.0,
        approval_risk_threshold: float = 6.0,
    ) -> None:
        baseline.validate()
        self.baseline = baseline
        self.approval_cost_threshold = approval_cost_threshold
        self.approval_schedule_threshold = approval_schedule_threshold
        self.approval_risk_threshold = approval_risk_threshold

        self.change_requests: Dict[str, ChangeRequest] = {}
        self.decisions: List[ChangeDecision] = []
        self.audit_log: List[AuditEntry] = []

        self._audit(
            actor="system",
            action="CREATE_BASELINE",
            object_id=baseline.version,
            details=(
                f"Baseline created with {len(baseline.deliverables)} "
                f"deliverables and {len(baseline.requirements)} requirements."
            ),
        )

    def _audit(
        self,
        actor: str,
        action: str,
        object_id: str,
        details: str,
    ) -> None:
        self.audit_log.append(
            AuditEntry(
                timestamp=datetime.now(),
                actor=actor,
                action=action,
                object_id=object_id,
                details=details,
            )
        )

    def submit_change(self, request: ChangeRequest) -> None:
        request.validate()

        if request.change_id in self.change_requests:
            raise ValueError(
                f"Change request {request.change_id} already exists."
            )

        unknown_requirements = (
            request.affected_requirements - self.baseline.requirements.keys()
        )
        unknown_deliverables = (
            request.affected_deliverables - self.baseline.deliverables.keys()
        )

        if unknown_requirements:
            raise ValueError(
                f"Unknown requirements: {sorted(unknown_requirements)}"
            )

        if unknown_deliverables:
            raise ValueError(
                f"Unknown deliverables: {sorted(unknown_deliverables)}"
            )

        self.change_requests[request.change_id] = request

        self._audit(
            actor=request.requester,
            action="SUBMIT_CHANGE",
            object_id=request.change_id,
            details=request.title,
        )

    def analyze_change(
        self,
        change_id: str,
        impact: ImpactAnalysis,
    ) -> None:
        request = self._get_change(change_id)

        if request.status not in {
            ChangeStatus.PROPOSED,
            ChangeStatus.UNDER_REVIEW,
        }:
            raise ValueError(
                f"Cannot analyze change {change_id} in status "
                f"{request.status.value}."
            )

        if impact.scope_delta < 0:
            raise ValueError(
                "scope_delta must be non-negative for this change model."
            )

        for risk_name, value in {
            "quality_risk": impact.quality_risk,
            "technical_risk": impact.technical_risk,
            "compliance_risk": impact.compliance_risk,
            "operational_risk": impact.operational_risk,
        }.items():
            if not 0 <= value <= 10:
                raise ValueError(
                    f"{risk_name} must be between 0 and 10."
                )

        request.attach_impact_analysis(impact)

        self._audit(
            actor="change_analyst",
            action="ANALYZE_CHANGE",
            object_id=change_id,
            details=(
                f"Cost +{impact.cost_delta:.2f}, "
                f"schedule +{impact.schedule_delta_days:.1f} days, "
                f"risk {impact.total_risk_score():.2f}/10."
            ),
        )

    def recommend_routing(self, change_id: str) -> str:
        request = self._get_change(change_id)

        if request.impact is None:
            raise ValueError("Impact analysis is required before routing.")

        impact = request.impact

        if (
            impact.cost_delta > self.approval_cost_threshold
            or impact.schedule_delta_days > self.approval_schedule_threshold
            or impact.total_risk_score() >= self.approval_risk_threshold
            or request.priority == Priority.CRITICAL
        ):
            return "Change Control Board"

        return "Project Manager"

    def approve_change(
        self,
        change_id: str,
        authority: str,
        rationale: str,
    ) -> None:
        request = self._get_change(change_id)

        if request.impact is None:
            raise ValueError(
                "A documented impact analysis is required before approval."
            )

        if request.status != ChangeStatus.UNDER_REVIEW:
            raise ValueError(
                f"Only changes under review can be approved. "
                f"Current status: {request.status.value}."
            )

        request.status = ChangeStatus.APPROVED
        request.decision = rationale
        request.decision_date = date.today()

        self.decisions.append(
            ChangeDecision(
                change_id=change_id,
                decision=ChangeStatus.APPROVED,
                authority=authority,
                rationale=rationale,
                timestamp=datetime.now(),
            )
        )

        self._audit(
            actor=authority,
            action="APPROVE_CHANGE",
            object_id=change_id,
            details=rationale,
        )

    def reject_change(
        self,
        change_id: str,
        authority: str,
        rationale: str,
    ) -> None:
        request = self._get_change(change_id)

        if request.status != ChangeStatus.UNDER_REVIEW:
            raise ValueError(
                f"Only changes under review can be rejected. "
                f"Current status: {request.status.value}."
            )

        request.status = ChangeStatus.REJECTED
        request.decision = rationale
        request.decision_date = date.today()

        self.decisions.append(
            ChangeDecision(
                change_id=change_id,
                decision=ChangeStatus.REJECTED,
                authority=authority,
                rationale=rationale,
                timestamp=datetime.now(),
            )
        )

        self._audit(
            actor=authority,
            action="REJECT_CHANGE",
            object_id=change_id,
            details=rationale,
        )

    def implement_change(self, change_id: str, implementer: str) -> None:
        request = self._get_change(change_id)

        if request.status != ChangeStatus.APPROVED:
            raise ValueError(
                "Only approved changes can be implemented."
            )

        if request.impact is None:
            raise ValueError(
                "Approved change has no impact analysis."
            )

        # This example adds the approved cost and effort to the baseline.
        # A real project would modify actual scope artifacts and create a
        # new controlled baseline version.
        request.status = ChangeStatus.IMPLEMENTED
        request.implementation_notes = (
            f"Implemented by {implementer} on {date.today().isoformat()}."
        )

        self._audit(
            actor=implementer,
            action="IMPLEMENT_CHANGE",
            object_id=change_id,
            details=request.implementation_notes,
        )

    def create_rebaselined_version(
        self,
        new_version: str,
        effective_date: date,
    ) -> ScopeBaseline:
        """
        Create a new immutable-style baseline snapshot.

        Only implemented changes contribute to the new baseline.
        """

        if any(
            request.status == ChangeStatus.APPROVED
            for request in self.change_requests.values()
        ):
            raise ValueError(
                "Cannot rebaseline while approved changes remain unimplemented."
            )

        deliverables = {
            key: Deliverable(
                deliverable_id=value.deliverable_id,
                name=value.name,
                description=value.description,
                estimated_hours=value.estimated_hours,
                estimated_cost=value.estimated_cost,
                status=value.status,
                requirements=set(value.requirements),
            )
            for key, value in self.baseline.deliverables.items()
        }

        requirements = {
            key: Requirement(
                requirement_id=value.requirement_id,
                title=value.title,
                description=value.description,
                priority=value.priority,
                acceptance_criteria=list(value.acceptance_criteria),
                deliverable_ids=set(value.deliverable_ids),
            )
            for key, value in self.baseline.requirements.items()
        }

        implemented_changes = [
            request
            for request in self.change_requests.values()
            if request.status == ChangeStatus.IMPLEMENTED
            and request.impact is not None
        ]

        # Demonstration rule:
        # Each implemented change creates a dedicated scope extension
        # deliverable. This keeps the example auditable.
        for request in implemented_changes:
            impact = request.impact
            assert impact is not None

            new_id = f"CHG-{request.change_id}"
            if new_id in deliverables:
                continue

            deliverables[new_id] = Deliverable(
                deliverable_id=new_id,
                name=request.title,
                description=request.description,
                estimated_hours=impact.resource_delta_hours,
                estimated_cost=impact.cost_delta,
                status=ScopeStatus.PLANNED,
            )

        new_baseline = ScopeBaseline(
            version=new_version,
            approved_date=effective_date,
            deliverables=deliverables,
            requirements=requirements,
        )
        new_baseline.validate()

        self.baseline = new_baseline

        self._audit(
            actor="change_control_board",
            action="CREATE_BASELINE",
            object_id=new_version,
            details=(
                f"Rebaselined from approved changes: "
                f"{len(implemented_changes)}."
            ),
        )

        return new_baseline

    def report(self) -> Dict[str, object]:
        total_requests = len(self.change_requests)
        status_counts = {
            status.value: sum(
                1
                for request in self.change_requests.values()
                if request.status == status
            )
            for status in ChangeStatus
        }

        approved_cost = sum(
            request.impact.cost_delta
            for request in self.change_requests.values()
            if request.impact is not None
            and request.status in {
                ChangeStatus.APPROVED,
                ChangeStatus.IMPLEMENTED,
            }
        )

        approved_schedule = sum(
            request.impact.schedule_delta_days
            for request in self.change_requests.values()
            if request.impact is not None
            and request.status in {
                ChangeStatus.APPROVED,
                ChangeStatus.IMPLEMENTED,
            }
        )

        return {
            "baseline_version": self.baseline.version,
            "baseline_hours": self.baseline.total_hours(),
            "baseline_cost": self.baseline.total_cost(),
            "total_change_requests": total_requests,
            "status_counts": status_counts,
            "approved_or_implemented_cost_delta": approved_cost,
            "approved_or_implemented_schedule_delta":
                approved_schedule,
            "audit_entries": len(self.audit_log),
        }

    def _get_change(self, change_id: str) -> ChangeRequest:
        try:
            return self.change_requests[change_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown change request: {change_id}"
            ) from exc


# ---------------------------------------------------------------------------
# 5. REQUIREMENTS TRACEABILITY
# ---------------------------------------------------------------------------

@dataclass
class TraceabilityMatrix:
    """
    A lightweight requirements traceability matrix.

    Requirement -> Deliverables -> Change Requests -> Tests.
    """

    requirement_to_tests: Dict[str, Set[str]] = field(default_factory=dict)
    requirement_to_changes: Dict[str, Set[str]] = field(default_factory=dict)

    def add_test(self, requirement_id: str, test_id: str) -> None:
        self.requirement_to_tests.setdefault(
            requirement_id, set()
        ).add(test_id)

    def add_change(self, requirement_id: str, change_id: str) -> None:
        self.requirement_to_changes.setdefault(
            requirement_id, set()
        ).add(change_id)

    def coverage_report(self) -> Dict[str, Dict[str, object]]:
        requirement_ids = (
            set(self.requirement_to_tests)
            | set(self.requirement_to_changes)
        )

        report: Dict[str, Dict[str, object]] = {}

        for requirement_id in sorted(requirement_ids):
            tests = self.requirement_to_tests.get(
                requirement_id, set()
            )
            changes = self.requirement_to_changes.get(
                requirement_id, set()
            )

            report[requirement_id] = {
                "test_count": len(tests),
                "change_count": len(changes),
                "tested": bool(tests),
            }

        return report


# ---------------------------------------------------------------------------
# 6. SCOPE CREEP DETECTION
# ---------------------------------------------------------------------------

@dataclass
class WorkItem:
    work_id: str
    name: str
    baseline_deliverable_id: Optional[str]
    estimated_hours: float
    authorized: bool = True


def detect_scope_creep(
    work_items: List[WorkItem],
    baseline: ScopeBaseline,
) -> List[WorkItem]:
    """
    Detect work that is not connected to a baseline deliverable.

    This is a simplified control. Real organizations may also require
    requirement IDs, approved change IDs, contracts, acceptance criteria,
    and authorization records.
    """
    baseline_ids = set(baseline.deliverables)
    return [
        item
        for item in work_items
        if (
            not item.authorized
            or item.baseline_deliverable_id not in baseline_ids
        )
    ]


# ---------------------------------------------------------------------------
# 7. CHANGE CLASSIFICATION
# ---------------------------------------------------------------------------

def classify_change(
    impact: ImpactAnalysis,
    urgency: Priority,
) -> str:
    """
    Classify a change for routing, not for approval.

    The categories are intentionally descriptive:
      - Minor: limited cost, schedule, and risk impact.
      - Significant: material impact requiring stronger governance.
      - Major: broad or high-risk impact.
    """

    if urgency == Priority.CRITICAL:
        return "Major"

    if (
        impact.cost_delta > 10000
        or impact.schedule_delta_days > 10
        or impact.total_risk_score() >= 8
    ):
        return "Major"

    if (
        impact.cost_delta > 2500
        or impact.schedule_delta_days > 3
        or impact.total_risk_score() >= 5
    ):
        return "Significant"

    return "Minor"


# ---------------------------------------------------------------------------
# 8. COST, SCHEDULE, AND SCOPE COMPARISONS
# ---------------------------------------------------------------------------

def percentage_change(old: float, new: float) -> float:
    if old == 0:
        if new == 0:
            return 0.0
        return math.inf

    return ((new - old) / abs(old)) * 100


def demonstrate_measurement() -> None:
    print_section("2. MEASURING CHANGE IMPACT")

    original_cost = 100_000.0
    changed_cost = 112_500.0
    original_days = 120.0
    changed_days = 130.0

    print(f"Original cost:      ${original_cost:,.2f}")
    print(f"Changed cost:       ${changed_cost:,.2f}")
    print(
        f"Cost change:        "
        f"{percentage_change(original_cost, changed_cost):.2f}%"
    )

    print(f"Original duration:  {original_days:.0f} days")
    print(f"Changed duration:   {changed_days:.0f} days")
    print(
        f"Schedule change:    "
        f"{percentage_change(original_days, changed_days):.2f}%"
    )

    print("\nImportant distinction:")
    print(
        "A change request should not be evaluated only by its cost. "
        "Scope, schedule, resources, quality, dependencies, risk, "
        "compliance, operations, and contractual effects can all matter."
    )


# ---------------------------------------------------------------------------
# 9. COMPLETE CASE STUDY
# ---------------------------------------------------------------------------

def build_initial_baseline() -> ScopeBaseline:
    deliverables = {
        "D-100": Deliverable(
            deliverable_id="D-100",
            name="Customer Web Portal",
            description="Responsive portal for customer account management.",
            estimated_hours=320,
            estimated_cost=32_000,
        ),
        "D-200": Deliverable(
            deliverable_id="D-200",
            name="Authentication Service",
            description="Secure registration, login, and session management.",
            estimated_hours=180,
            estimated_cost=24_000,
        ),
        "D-300": Deliverable(
            deliverable_id="D-300",
            name="Reporting Module",
            description="Operational and management reporting.",
            estimated_hours=220,
            estimated_cost=20_000,
        ),
    }

    requirements = {
        "REQ-001": Requirement(
            requirement_id="REQ-001",
            title="Customer authentication",
            description="Users must securely authenticate.",
            priority=Priority.CRITICAL,
            acceptance_criteria=[
                "Valid users can sign in.",
                "Invalid credentials are rejected.",
                "Sessions expire according to policy.",
            ],
            deliverable_ids={"D-200"},
        ),
        "REQ-002": Requirement(
            requirement_id="REQ-002",
            title="Account dashboard",
            description="Customers can view account information.",
            priority=Priority.HIGH,
            acceptance_criteria=[
                "Account information is displayed.",
                "Unauthorized data is not exposed.",
            ],
            deliverable_ids={"D-100"},
        ),
        "REQ-003": Requirement(
            requirement_id="REQ-003",
            title="Management reports",
            description="Managers can access operational reports.",
            priority=Priority.MEDIUM,
            acceptance_criteria=[
                "Reports can be generated.",
                "Reports contain approved business metrics.",
            ],
            deliverable_ids={"D-300"},
        ),
    }

    for deliverable in deliverables.values():
        for requirement in requirements.values():
            if deliverable.deliverable_id in requirement.deliverable_ids:
                deliverable.requirements.add(requirement.requirement_id)

    return ScopeBaseline(
        version="BL-1.0",
        approved_date=date(2026, 9, 1),
        deliverables=deliverables,
        requirements=requirements,
    )


def run_case_study() -> None:
    print_section("3. END-TO-END SCOPE CONTROL CASE STUDY")

    baseline = build_initial_baseline()

    engine = ScopeControlEngine(
        baseline=baseline,
        approval_cost_threshold=5_000,
        approval_schedule_threshold=5,
        approval_risk_threshold=6,
    )

    print(
        f"Initial baseline: {engine.baseline.version}\n"
        f"Baseline effort:  {engine.baseline.total_hours():,.0f} hours\n"
        f"Baseline cost:    ${engine.baseline.total_cost():,.2f}"
    )

    # Change 1: limited visual enhancement.
    change_1 = ChangeRequest(
        change_id="CR-001",
        title="Add customer profile photo",
        requester="Product Owner",
        description=(
            "Allow customers to upload a profile image and display it "
            "on the account dashboard."
        ),
        reason="Customer usability improvement.",
        priority=Priority.LOW,
        proposed_date=date.today(),
        affected_requirements={"REQ-002"},
        affected_deliverables={"D-100"},
    )

    engine.submit_change(change_1)

    impact_1 = ImpactAnalysis(
        scope_delta=1,
        schedule_delta_days=2,
        cost_delta=1_200,
        resource_delta_hours=16,
        quality_risk=2,
        technical_risk=2,
        compliance_risk=1,
        operational_risk=2,
        dependencies=["Existing image storage configuration."],
        assumptions=["Maximum image size is controlled."],
    )

    engine.analyze_change("CR-001", impact_1)

    print(
        f"\nCR-001 classification: "
        f"{classify_change(impact_1, change_1.priority)}"
    )
    print(
        f"CR-001 routing recommendation: "
        f"{engine.recommend_routing('CR-001')}"
    )

    engine.approve_change(
        "CR-001",
        authority="Project Manager",
        rationale="Small controlled enhancement within delegated threshold.",
    )
    engine.implement_change("CR-001", "Development Team")

    # Change 2: external payment integration.
    change_2 = ChangeRequest(
        change_id="CR-002",
        title="Add external payment gateway",
        requester="Business Sponsor",
        description=(
            "Add online payment processing to allow customers to pay "
            "outstanding balances through an external gateway."
        ),
        reason="Business requirement introduced after baseline approval.",
        priority=Priority.HIGH,
        proposed_date=date.today(),
        affected_requirements={"REQ-002"},
        affected_deliverables={"D-100", "D-200"},
    )

    engine.submit_change(change_2)

    impact_2 = ImpactAnalysis(
        scope_delta=4,
        schedule_delta_days=12,
        cost_delta=18_000,
        resource_delta_hours=160,
        quality_risk=6,
        technical_risk=7,
        compliance_risk=9,
        operational_risk=7,
        dependencies=[
            "Payment provider contract",
            "Security review",
            "Financial reconciliation",
        ],
        assumptions=[
            "Provider API remains available",
            "Legal and compliance requirements are satisfied",
        ],
    )

    engine.analyze_change("CR-002", impact_2)

    print(
        f"\nCR-002 classification: "
        f"{classify_change(impact_2, change_2.priority)}"
    )
    print(
        f"CR-002 routing recommendation: "
        f"{engine.recommend_routing('CR-002')}"
    )

    engine.approve_change(
        "CR-002",
        authority="Change Control Board",
        rationale=(
            "Approved after documented schedule, cost, security, "
            "compliance, and operational analysis."
        ),
    )
    engine.implement_change("CR-002", "Payments Workstream")

    # Change 3: rejected because impact is not justified in this example.
    change_3 = ChangeRequest(
        change_id="CR-003",
        title="Add animated dashboard background",
        requester="Designer",
        description="Add continuously animated decorative dashboard effects.",
        reason="Visual enhancement.",
        priority=Priority.LOW,
        proposed_date=date.today(),
        affected_requirements={"REQ-002"},
        affected_deliverables={"D-100"},
    )

    engine.submit_change(change_3)

    impact_3 = ImpactAnalysis(
        scope_delta=1,
        schedule_delta_days=3,
        cost_delta=2_000,
        resource_delta_hours=24,
        quality_risk=4,
        technical_risk=5,
        compliance_risk=1,
        operational_risk=5,
        dependencies=["Browser rendering performance."],
        assumptions=["Animation is supported on target browsers."],
    )

    engine.analyze_change("CR-003", impact_3)

    engine.reject_change(
        "CR-003",
        authority="Project Manager",
        rationale=(
            "Not required by the approved business objectives and "
            "introduces avoidable performance complexity."
        ),
    )

    report = engine.report()

    print("\nCurrent control report:")
    for key, value in report.items():
        print(f"  {key}: {value}")

    new_baseline = engine.create_rebaselined_version(
        new_version="BL-2.0",
        effective_date=date.today(),
    )

    print(
        f"\nNew baseline:       {new_baseline.version}\n"
        f"New baseline hours: {new_baseline.total_hours():,.0f}\n"
        f"New baseline cost:  ${new_baseline.total_cost():,.2f}"
    )


# ---------------------------------------------------------------------------
# 10. SCOPE CREEP EXAMPLE
# ---------------------------------------------------------------------------

def demonstrate_scope_creep_detection() -> None:
    print_section("4. SCOPE CREEP DETECTION")

    baseline = build_initial_baseline()

    work_items = [
        WorkItem(
            work_id="W-001",
            name="Build login form",
            baseline_deliverable_id="D-200",
            estimated_hours=20,
        ),
        WorkItem(
            work_id="W-002",
            name="Add dashboard export to social media",
            baseline_deliverable_id=None,
            estimated_hours=12,
            authorized=False,
        ),
        WorkItem(
            work_id="W-003",
            name="Improve report query",
            baseline_deliverable_id="D-300",
            estimated_hours=18,
        ),
        WorkItem(
            work_id="W-004",
            name="Build unrequested loyalty system",
            baseline_deliverable_id=None,
            estimated_hours=80,
            authorized=False,
        ),
    ]

    uncontrolled = detect_scope_creep(work_items, baseline)

    print("Potentially uncontrolled work:")
    for item in uncontrolled:
        print(
            f"  {item.work_id}: {item.name} "
            f"({item.estimated_hours} hours)"
        )

    print(
        "\nControl principle: work should have a traceable authorization "
        "path to an approved requirement, deliverable, contract, or "
        "approved change."
    )


# ---------------------------------------------------------------------------
# 11. EDGE CASES AND FAILURE CONDITIONS
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print_section("5. EDGE CASES AND VALIDATION")

    baseline = build_initial_baseline()
    engine = ScopeControlEngine(baseline)

    # Duplicate request.
    duplicate = ChangeRequest(
        change_id="CR-DUP",
        title="Duplicate example",
        requester="Tester",
        description="Initial request.",
        reason="Testing.",
        priority=Priority.LOW,
        proposed_date=date.today(),
    )

    engine.submit_change(duplicate)

    try:
        engine.submit_change(duplicate)
    except ValueError as exc:
        print(f"Duplicate change prevented: {exc}")

    # Unknown requirement.
    invalid_reference = ChangeRequest(
        change_id="CR-BAD-REF",
        title="Invalid reference",
        requester="Tester",
        description="References an unknown requirement.",
        reason="Testing.",
        priority=Priority.LOW,
        proposed_date=date.today(),
        affected_requirements={"REQ-999"},
    )

    try:
        engine.submit_change(invalid_reference)
    except ValueError as exc:
        print(f"Unknown requirement prevented: {exc}")

    # Approval without analysis.
    unanalyzed = ChangeRequest(
        change_id="CR-NO-ANALYSIS",
        title="Missing analysis",
        requester="Tester",
        description="Attempts to bypass impact analysis.",
        reason="Testing.",
        priority=Priority.MEDIUM,
        proposed_date=date.today(),
    )

    engine.submit_change(unanalyzed)

    try:
        engine.approve_change(
            "CR-NO-ANALYSIS",
            "Project Manager",
            "Attempted bypass.",
        )
    except ValueError as exc:
        print(f"Approval without analysis prevented: {exc}")

    # Invalid risk value.
    try:
        ImpactAnalysis(
            scope_delta=1,
            schedule_delta_days=1,
            cost_delta=100,
            resource_delta_hours=1,
            quality_risk=11,
            technical_risk=1,
            compliance_risk=1,
            operational_risk=1,
            dependencies=[],
            assumptions=[],
        )
        engine.analyze_change(
            "CR-NO-ANALYSIS",
            ImpactAnalysis(
                scope_delta=1,
                schedule_delta_days=1,
                cost_delta=100,
                resource_delta_hours=1,
                quality_risk=11,
                technical_risk=1,
                compliance_risk=1,
                operational_risk=1,
                dependencies=[],
                assumptions=[],
            ),
        )
    except ValueError as exc:
        print(f"Invalid risk value prevented: {exc}")


# ---------------------------------------------------------------------------
# 12. TRACEABILITY DEMONSTRATION
# ---------------------------------------------------------------------------

def demonstrate_traceability() -> None:
    print_section("6. REQUIREMENTS TRACEABILITY")

    matrix = TraceabilityMatrix()

    matrix.add_test("REQ-001", "TEST-AUTH-001")
    matrix.add_test("REQ-001", "TEST-AUTH-002")
    matrix.add_test("REQ-002", "TEST-DASH-001")

    matrix.add_change("REQ-002", "CR-001")
    matrix.add_change("REQ-002", "CR-002")

    report = matrix.coverage_report()

    for requirement_id, data in report.items():
        print(
            f"{requirement_id}: "
            f"{data['test_count']} tests, "
            f"{data['change_count']} changes, "
            f"tested={data['tested']}"
        )


# ---------------------------------------------------------------------------
# 13. GOVERNANCE PRINCIPLES
# ---------------------------------------------------------------------------

def demonstrate_governance_rules() -> None:
    print_section("7. PRACTICAL GOVERNANCE RULES")

    rules = [
        "Define scope before controlling changes.",
        "Establish an approved baseline.",
        "Require a documented change request.",
        "Identify the business reason for the change.",
        "Analyze impacts before making the decision.",
        "Do not treat stakeholder pressure as approval.",
        "Use delegated authority thresholds where appropriate.",
        "Record both approvals and rejections.",
        "Do not implement unapproved scope.",
        "Update requirements and delivery artifacts after approval.",
        "Maintain traceability from change to implementation.",
        "Rebaseline only through formal control.",
        "Communicate approved baseline changes to affected parties.",
        "Monitor unauthorized work to detect scope creep early.",
    ]

    for number, rule in enumerate(rules, start=1):
        print(f"{number:02d}. {rule}")


# ---------------------------------------------------------------------------
# 14. COMPARISON OF RELATED CONCEPTS
# ---------------------------------------------------------------------------

def demonstrate_comparisons() -> None:
    print_section("8. IMPORTANT DISTINCTIONS")

    comparisons = [
        (
            "Scope change",
            "A proposed modification evaluated through change control."
        ),
        (
            "Scope creep",
            "Uncontrolled or unauthorized scope expansion."
        ),
        (
            "Gold plating",
            "Unrequested enhancement introduced by the delivery team."
        ),
        (
            "Requirement clarification",
            "Clarification that may or may not change the approved scope."
        ),
        (
            "Defect correction",
            "Work needed to make an existing deliverable conform to its "
            "approved requirements."
        ),
        (
            "Change control",
            "The governance process used to decide whether and how scope "
            "changes are incorporated."
        ),
        (
            "Rebaselining",
            "Creation of a new approved reference point after authorized "
            "changes."
        ),
    ]

    for concept, distinction in comparisons:
        print(f"\n{concept}:")
        print(textwrap.fill(distinction, width=72, initial_indent="  ",
                            subsequent_indent="  "))


# ---------------------------------------------------------------------------
# 15. PERFORMANCE AND SECURITY CONSIDERATIONS
# ---------------------------------------------------------------------------

def demonstrate_performance_and_security() -> None:
    print_section("9. PERFORMANCE AND SECURITY CONSIDERATIONS")

    print(
        """
Performance:
- Dictionary-based lookup gives approximately O(1) average access for
  requirements and deliverables by ID.
- Sets provide approximately O(1) average membership checks.
- Generating a new baseline copies the controlled scope structures and is
  approximately O(R + D), where R is the number of requirements and D is
  the number of deliverables, excluding nested collection sizes.
- A production system should use indexed database queries for very large
  portfolios rather than keeping the complete state in memory.

Security:
- Change approval should use authenticated identities.
- Authorization must be checked server-side, not only in a user interface.
- Approval roles should follow least privilege.
- Audit logs should be tamper-resistant.
- Sensitive contractual, financial, security, or customer information
  should not be exposed to unauthorized requesters.
- Every state transition should be attributable to an authenticated actor.
- Production systems should validate all externally supplied identifiers.
- Baseline versions should be immutable after approval, with subsequent
  changes represented as controlled versions rather than silent edits.
""".strip()
    )


# ---------------------------------------------------------------------------
# 16. TESTS
# ---------------------------------------------------------------------------

class ScopeControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ScopeControlEngine(build_initial_baseline())

    def test_baseline_totals(self) -> None:
        self.assertEqual(self.engine.baseline.total_hours(), 720)
        self.assertEqual(self.engine.baseline.total_cost(), 76_000)

    def test_change_requires_analysis(self) -> None:
        request = ChangeRequest(
            change_id="T-001",
            title="Test change",
            requester="Tester",
            description="A test change.",
            reason="Unit test.",
            priority=Priority.LOW,
            proposed_date=date.today(),
        )

        self.engine.submit_change(request)

        with self.assertRaises(ValueError):
            self.engine.approve_change(
                "T-001",
                "Manager",
                "Should fail.",
            )

    def test_change_can_be_approved_and_implemented(self) -> None:
        request = ChangeRequest(
            change_id="T-002",
            title="Approved change",
            requester="Tester",
            description="A valid test change.",
            reason="Unit test.",
            priority=Priority.MEDIUM,
            proposed_date=date.today(),
        )

        self.engine.submit_change(request)

        impact = ImpactAnalysis(
            scope_delta=1,
            schedule_delta_days=1,
            cost_delta=1000,
            resource_delta_hours=10,
            quality_risk=1,
            technical_risk=1,
            compliance_risk=1,
            operational_risk=1,
            dependencies=[],
            assumptions=[],
        )

        self.engine.analyze_change("T-002", impact)
        self.engine.approve_change("T-002", "Manager", "Approved.")
        self.engine.implement_change("T-002", "Developer")

        self.assertEqual(
            self.engine.change_requests["T-002"].status,
            ChangeStatus.IMPLEMENTED,
        )

    def test_unknown_requirement_is_rejected(self) -> None:
        request = ChangeRequest(
            change_id="T-003",
            title="Bad reference",
            requester="Tester",
            description="Invalid requirement reference.",
            reason="Unit test.",
            priority=Priority.LOW,
            proposed_date=date.today(),
            affected_requirements={"UNKNOWN"},
        )

        with self.assertRaises(ValueError):
            self.engine.submit_change(request)


# ---------------------------------------------------------------------------
# 17. MINI EXERCISES EXECUTED AS CODE
# ---------------------------------------------------------------------------

def demonstrate_exercises() -> None:
    print_section("10. PRACTICAL EXERCISES")

    print(
        """
Exercise 1:
A proposed change costs $2,000 and adds two days. Its average risk is
2/10. The routing engine should treat it as a limited change.

Exercise 2:
A proposed change costs $20,000 and adds fifteen days. Its average risk
is 8/10. The routing engine should send it to stronger governance.

Exercise 3:
Work without an approved requirement, deliverable, contract, or change
should be investigated as potentially uncontrolled scope.
""".strip()
    )

    low_impact = ImpactAnalysis(
        scope_delta=1,
        schedule_delta_days=2,
        cost_delta=2_000,
        resource_delta_hours=20,
        quality_risk=2,
        technical_risk=2,
        compliance_risk=2,
        operational_risk=2,
        dependencies=[],
        assumptions=[],
    )

    high_impact = ImpactAnalysis(
        scope_delta=5,
        schedule_delta_days=15,
        cost_delta=20_000,
        resource_delta_hours=200,
        quality_risk=8,
        technical_risk=8,
        compliance_risk=8,
        operational_risk=8,
        dependencies=[],
        assumptions=[],
    )

    print(
        "Exercise 1 classification:",
        classify_change(low_impact, Priority.LOW),
    )
    print(
        "Exercise 2 classification:",
        classify_change(high_impact, Priority.HIGH),
    )


# ---------------------------------------------------------------------------
# 18. MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print(
        """
SCOPE CONTROL: MANAGING CHANGES TO SCOPE
=========================================

This executable study file models scope definition, baselining, change
requests, impact analysis, governance, approval, implementation,
rebaselining, traceability, scope-creep detection, validation, and testing.
""".strip()
    )

    demonstrate_fundamentals()
    demonstrate_measurement()
    run_case_study()
    demonstrate_scope_creep_detection()
    demonstrate_edge_cases()
    demonstrate_traceability()
    demonstrate_governance_rules()
    demonstrate_comparisons()
    demonstrate_performance_and_security()
    demonstrate_exercises()

    print_section("11. AUTOMATED TESTS")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ScopeControlTests
    )
    result = unittest.TextTestRunner(
        verbosity=1,
        stream=None,
    ).run(suite)

    print(
        f"\nTests run: {result.testsRun}, "
        f"failures: {len(result.failures)}, "
        f"errors: {len(result.errors)}"
    )

    if result.wasSuccessful():
        print("All scope-control tests passed.")
    else:
        print("Some tests failed. Review the test output.")


if __name__ == "__main__":
    main()
