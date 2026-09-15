"""
Project Charter: Understanding Project Authorization

A self-contained study program that teaches project charters and project
authorization from beginner to advanced level.

The program uses executable examples to demonstrate:
- What a project charter is
- Why project authorization matters
- Project vs. operations
- Charter components
- Business case and strategic alignment
- Objectives and SMART criteria
- Scope boundaries
- Deliverables, milestones, assumptions, constraints, risks
- Stakeholders and governance
- Roles and authority
- Sponsor, project manager, and steering committee responsibilities
- Acceptance criteria
- Change control
- Risk scoring
- Stakeholder analysis
- Charter validation
- Authorization decisions
- Traceability
- Versioning and auditability
- A complete project authorization workflow

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Tuple
import math


# ---------------------------------------------------------------------------
# 1. FOUNDATIONAL CONCEPTS
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


print_section("1. What Is a Project Charter?")

print(
    """
A project charter is a formal document that authorizes a project to exist.
It establishes the project's purpose, high-level objectives, boundaries,
major stakeholders, authority structure, assumptions, constraints, risks,
success criteria, and governance expectations.

The charter is normally created before detailed project planning.

A useful distinction is:

Project charter
    Authorizes the project and establishes high-level direction.

Project management plan
    Explains in detail how the authorized project will be executed,
    monitored, controlled, and closed.

The charter answers questions such as:
    Why are we doing this?
    What problem or opportunity justifies it?
    What outcomes are expected?
    Who sponsors the work?
    Who has authority to manage it?
    What is initially inside and outside the project?
    What constraints and major risks exist?
    What constitutes success?
"""
)


# ---------------------------------------------------------------------------
# 2. PROJECTS VS OPERATIONS
# ---------------------------------------------------------------------------

print_section("2. Project vs. Operations")

project_characteristics = {
    "Project": [
        "Temporary",
        "Creates a unique product, service, result, or change",
        "Has an intended start and completion",
        "Uses a defined authorization and governance structure",
    ],
    "Operations": [
        "Ongoing",
        "Repeated or continuous",
        "Maintains organizational capabilities",
        "Usually governed through operational procedures",
    ],
}

for category, characteristics in project_characteristics.items():
    print(f"\n{category}:")
    for characteristic in characteristics:
        print(f"  - {characteristic}")


def classify_work(is_temporary: bool, produces_unique_result: bool) -> str:
    """A simple educational classifier."""
    if is_temporary and produces_unique_result:
        return "Project"
    return "Likely operational work"


examples = [
    (True, True, "Implementing a new banking application"),
    (False, False, "Processing daily customer transactions"),
    (True, True, "Constructing a new office"),
    (False, False, "Running a monthly payroll process"),
]

for temporary, unique, name in examples:
    print(f"{name}: {classify_work(temporary, unique)}")


# ---------------------------------------------------------------------------
# 3. CORE CHARTER TERMINOLOGY
# ---------------------------------------------------------------------------

print_section("3. Core Project Charter Terminology")

terms = {
    "Sponsor": "Person or group that provides organizational support and authorization.",
    "Project Manager": "Person responsible for directing and coordinating project work.",
    "Business Case": "Reasoned justification for investing organizational resources.",
    "Objective": "Specific result the project intends to achieve.",
    "Deliverable": "A verifiable output produced by the project.",
    "Scope": "The boundaries of what the project will and will not address.",
    "Milestone": "A significant point or event used to measure progress.",
    "Assumption": "A condition treated as true for planning purposes.",
    "Constraint": "A known limitation imposed on the project.",
    "Risk": "An uncertain event or condition that can affect objectives.",
    "Stakeholder": "A person, group, or organization that can affect or be affected by the project.",
    "Governance": "The structure through which decisions, authority, oversight, and accountability operate.",
    "Acceptance Criteria": "Conditions that must be satisfied for a deliverable or result to be accepted.",
    "Authorization": "Formal approval to initiate and allocate organizational resources to the project.",
}

for term, definition in terms.items():
    print(f"{term:20} | {definition}")


# ---------------------------------------------------------------------------
# 4. SMART OBJECTIVES
# ---------------------------------------------------------------------------

print_section("4. SMART Objectives")

@dataclass
class Objective:
    description: str
    specific: bool
    measurable: bool
    achievable: bool
    relevant: bool
    time_bound: bool

    @property
    def smart(self) -> bool:
        return all([
            self.specific,
            self.measurable,
            self.achievable,
            self.relevant,
            self.time_bound,
        ])

    def score(self) -> int:
        return sum([
            self.specific,
            self.measurable,
            self.achievable,
            self.relevant,
            self.time_bound,
        ])


weak_objective = Objective(
    "Improve customer service",
    False, False, True, True, False
)

strong_objective = Objective(
    "Reduce average customer-support response time from 12 hours to 4 hours "
    "within six months",
    True, True, True, True, True
)

for objective in [weak_objective, strong_objective]:
    print(f"\nObjective: {objective.description}")
    print(f"SMART score: {objective.score()}/5")
    print(f"Qualifies as SMART: {objective.smart}")


# ---------------------------------------------------------------------------
# 5. PROJECT CHARTER DATA MODEL
# ---------------------------------------------------------------------------

print_section("5. Building a Project Charter")

class AuthorizationStatus(Enum):
    DRAFT = "Draft"
    UNDER_REVIEW = "Under Review"
    AUTHORIZED = "Authorized"
    REJECTED = "Rejected"
    SUSPENDED = "Suspended"


class DecisionType(Enum):
    APPROVE = "Approve"
    REJECT = "Reject"
    REQUEST_REVISION = "Request Revision"


@dataclass
class Stakeholder:
    name: str
    role: str
    influence: int
    interest: int
    communication_need: str

    def priority(self) -> str:
        if self.influence >= 4 and self.interest >= 4:
            return "Manage closely"
        if self.influence >= 4:
            return "Keep satisfied"
        if self.interest >= 4:
            return "Keep informed"
        return "Monitor"


@dataclass
class Risk:
    identifier: str
    description: str
    probability: float
    impact: float
    response: str

    @property
    def exposure(self) -> float:
        return self.probability * self.impact

    @property
    def severity(self) -> str:
        if self.exposure >= 16:
            return "Critical"
        if self.exposure >= 9:
            return "High"
        if self.exposure >= 4:
            return "Medium"
        return "Low"


@dataclass
class Milestone:
    name: str
    target_date: date


@dataclass
class ProjectCharter:
    project_id: str
    title: str
    sponsor: str
    project_manager: str
    purpose: str
    business_case: str
    strategic_alignment: List[str]
    objectives: List[Objective]
    in_scope: List[str]
    out_of_scope: List[str]
    deliverables: List[str]
    milestones: List[Milestone]
    assumptions: List[str]
    constraints: List[str]
    risks: List[Risk]
    stakeholders: List[Stakeholder]
    acceptance_criteria: List[str]
    budget_ceiling: float
    status: AuthorizationStatus = AuthorizationStatus.DRAFT
    version: int = 1

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate minimum authorization readiness."""
        errors: List[str] = []

        if not self.project_id.strip():
            errors.append("Project ID is missing.")

        if not self.title.strip():
            errors.append("Project title is missing.")

        if not self.sponsor.strip():
            errors.append("Sponsor is missing.")

        if not self.project_manager.strip():
            errors.append("Project manager is missing.")

        if not self.purpose.strip():
            errors.append("Project purpose is missing.")

        if not self.business_case.strip():
            errors.append("Business case is missing.")

        if not self.objectives:
            errors.append("At least one objective is required.")
        elif not all(objective.smart for objective in self.objectives):
            errors.append("All authorization-level objectives should be SMART.")

        if not self.in_scope:
            errors.append("At least one in-scope item is required.")

        if not self.out_of_scope:
            errors.append("Explicit out-of-scope boundaries are recommended.")

        if not self.deliverables:
            errors.append("At least one deliverable is required.")

        if not self.milestones:
            errors.append("At least one milestone is required.")

        if not self.acceptance_criteria:
            errors.append("Acceptance criteria are missing.")

        if self.budget_ceiling <= 0:
            errors.append("Budget ceiling must be greater than zero.")

        if not self.stakeholders:
            errors.append("Stakeholder identification is missing.")

        return len(errors) == 0, errors

    def authorize(self) -> bool:
        valid, errors = self.validate()

        if not valid:
            self.status = AuthorizationStatus.UNDER_REVIEW
            print("\nAuthorization failed validation:")
            for error in errors:
                print(f"  - {error}")
            return False

        self.status = AuthorizationStatus.AUTHORIZED
        return True

    def revise(self) -> None:
        self.version += 1
        self.status = AuthorizationStatus.DRAFT

    def risk_register(self) -> List[Dict[str, object]]:
        return [
            {
                "id": risk.identifier,
                "severity": risk.severity,
                "exposure": risk.exposure,
                "description": risk.description,
            }
            for risk in sorted(
                self.risks,
                key=lambda item: item.exposure,
                reverse=True,
            )
        ]


charter = ProjectCharter(
    project_id="PRJ-001",
    title="Customer Support Response Transformation",
    sponsor="Chief Customer Officer",
    project_manager="Program Delivery Manager",
    purpose="Reduce customer waiting time and improve support service quality.",
    business_case=(
        "High response times increase customer dissatisfaction, operational "
        "cost, and service escalation volume."
    ),
    strategic_alignment=[
        "Improve customer experience",
        "Reduce avoidable operating cost",
        "Increase digital service efficiency",
    ],
    objectives=[strong_objective],
    in_scope=[
        "Support workflow redesign",
        "Customer support dashboard",
        "Response-time measurement",
        "Agent notification rules",
    ],
    out_of_scope=[
        "Replacing the enterprise CRM",
        "Changing customer pricing",
        "Redesigning unrelated sales workflows",
    ],
    deliverables=[
        "Approved process design",
        "Operational dashboard",
        "Notification mechanism",
        "Training package",
    ],
    milestones=[
        Milestone("Charter authorization", date(2026, 10, 1)),
        Milestone("Process design approved", date(2026, 11, 1)),
        Milestone("Pilot completed", date(2026, 12, 15)),
        Milestone("Production rollout", date(2027, 1, 15)),
    ],
    assumptions=[
        "Business users will provide timely requirements.",
        "Existing support data is sufficiently reliable.",
        "Required technical teams will be available.",
    ],
    constraints=[
        "Budget cannot exceed the approved ceiling.",
        "The existing CRM cannot be replaced.",
        "Customer-facing disruption must be minimized.",
    ],
    risks=[
        Risk(
            "R-001",
            "Legacy data may be incomplete.",
            0.6,
            8,
            "Perform data-quality assessment before implementation.",
        ),
        Risk(
            "R-002",
            "Operational teams may resist process changes.",
            0.5,
            7,
            "Use stakeholder workshops and structured training.",
        ),
        Risk(
            "R-003",
            "Integration work may take longer than estimated.",
            0.4,
            9,
            "Prototype critical integrations early.",
        ),
    ],
    stakeholders=[
        Stakeholder(
            "Chief Customer Officer",
            "Sponsor",
            5,
            5,
            "Executive status and decision reporting",
        ),
        Stakeholder(
            "Support Operations Lead",
            "Business Owner",
            5,
            5,
            "Weekly operational decisions",
        ),
        Stakeholder(
            "Support Agents",
            "Users",
            3,
            5,
            "Training and process communication",
        ),
        Stakeholder(
            "Finance",
            "Control Function",
            4,
            3,
            "Budget and benefit reporting",
        ),
    ],
    acceptance_criteria=[
        "Target response-time measurement is operational.",
        "Pilot users can complete the redesigned workflow.",
        "Dashboard results reconcile with approved source data.",
        "Sponsor accepts the final rollout package.",
    ],
    budget_ceiling=250000.00,
)


print(f"Project: {charter.title}")
print(f"Status before authorization: {charter.status.value}")

valid, validation_errors = charter.validate()
print(f"Validation result: {valid}")

if charter.authorize():
    print(f"Status after authorization: {charter.status.value}")
else:
    print(f"Status after validation failure: {charter.status.value}")


# ---------------------------------------------------------------------------
# 6. STAKEHOLDER ANALYSIS
# ---------------------------------------------------------------------------

print_section("6. Stakeholder Analysis")

for stakeholder in charter.stakeholders:
    print(
        f"{stakeholder.name:28} "
        f"influence={stakeholder.influence} "
        f"interest={stakeholder.interest} "
        f"priority={stakeholder.priority()}"
    )


# ---------------------------------------------------------------------------
# 7. RISK ANALYSIS
# ---------------------------------------------------------------------------

print_section("7. Risk Analysis")

for risk in charter.risks:
    print(
        f"{risk.identifier}: {risk.description}\n"
        f"  Probability: {risk.probability:.1f}\n"
        f"  Impact:      {risk.impact:.1f}\n"
        f"  Exposure:    {risk.exposure:.1f}\n"
        f"  Severity:    {risk.severity}\n"
        f"  Response:    {risk.response}\n"
    )


# ---------------------------------------------------------------------------
# 8. AUTHORIZATION LOGIC
# ---------------------------------------------------------------------------

print_section("8. Authorization Decision Model")

@dataclass
class AuthorizationDecision:
    decision: DecisionType
    decision_maker: str
    rationale: str
    date_recorded: date


def evaluate_authorization(
    project_charter: ProjectCharter,
    decision_maker: str,
    minimum_quality_score: int = 8,
) -> AuthorizationDecision:
    """
    Illustrative governance logic.

    This is not a universal project-management standard. Organizations
    define their own approval thresholds and governance rules.
    """
    valid, errors = project_charter.validate()

    score = 0

    if project_charter.purpose:
        score += 1
    if project_charter.business_case:
        score += 1
    if project_charter.strategic_alignment:
        score += 1
    if project_charter.objectives and all(
        objective.smart for objective in project_charter.objectives
    ):
        score += 1
    if project_charter.in_scope and project_charter.out_of_scope:
        score += 1
    if project_charter.deliverables:
        score += 1
    if project_charter.milestones:
        score += 1
    if project_charter.stakeholders:
        score += 1
    if project_charter.acceptance_criteria:
        score += 1
    if project_charter.budget_ceiling > 0:
        score += 1

    if not valid:
        return AuthorizationDecision(
            DecisionType.REQUEST_REVISION,
            decision_maker,
            "Required charter information is incomplete: "
            + "; ".join(errors),
            date.today(),
        )

    if score < minimum_quality_score:
        return AuthorizationDecision(
            DecisionType.REQUEST_REVISION,
            decision_maker,
            f"Charter quality score {score} is below threshold "
            f"{minimum_quality_score}.",
            date.today(),
        )

    return AuthorizationDecision(
        DecisionType.APPROVE,
        decision_maker,
        f"Charter passed validation with quality score {score}/10.",
        date.today(),
    )


decision = evaluate_authorization(
    charter,
    decision_maker="Executive Sponsor",
)

print(f"Decision: {decision.decision.value}")
print(f"Decision maker: {decision.decision_maker}")
print(f"Rationale: {decision.rationale}")


# ---------------------------------------------------------------------------
# 9. CHANGE CONTROL
# ---------------------------------------------------------------------------

print_section("9. Charter Changes and Version Control")

@dataclass
class CharterChange:
    change_id: str
    description: str
    reason: str
    requested_by: str
    impact_on_scope: str
    impact_on_budget: float
    impact_on_schedule_days: int
    approved: bool = False


def assess_charter_change(change: CharterChange) -> Dict[str, object]:
    """Identify whether a requested change is significant."""
    significant = (
        abs(change.impact_on_budget) > 0
        or change.impact_on_schedule_days != 0
        or change.impact_on_scope.lower() not in {"none", "low"}
    )

    return {
        "change_id": change.change_id,
        "significant": significant,
        "requires_governance_review": significant,
        "budget_impact": change.impact_on_budget,
        "schedule_impact_days": change.impact_on_schedule_days,
    }


change = CharterChange(
    change_id="CR-001",
    description="Add a second customer-support channel to the project.",
    reason="Business leadership requested broader service coverage.",
    requested_by="Support Operations Lead",
    impact_on_scope="High",
    impact_on_budget=40000,
    impact_on_schedule_days=20,
)

assessment = assess_charter_change(change)
for key, value in assessment.items():
    print(f"{key}: {value}")


# ---------------------------------------------------------------------------
# 10. TRACEABILITY
# ---------------------------------------------------------------------------

print_section("10. Strategic-to-Deliverable Traceability")

@dataclass
class TraceabilityLink:
    strategic_goal: str
    objective: str
    deliverable: str
    acceptance_criterion: str


traceability = [
    TraceabilityLink(
        "Improve customer experience",
        strong_objective.description,
        "Operational dashboard",
        "Dashboard results reconcile with approved source data.",
    ),
    TraceabilityLink(
        "Reduce avoidable operating cost",
        strong_objective.description,
        "Notification mechanism",
        "Target response-time measurement is operational.",
    ),
]

for link in traceability:
    print(f"Strategic goal: {link.strategic_goal}")
    print(f"  -> Objective: {link.objective}")
    print(f"  -> Deliverable: {link.deliverable}")
    print(f"  -> Acceptance: {link.acceptance_criterion}\n")


# ---------------------------------------------------------------------------
# 11. EDGE CASES AND VALIDATION
# ---------------------------------------------------------------------------

print_section("11. Edge Cases")

def demonstrate_invalid_charter() -> None:
    invalid = ProjectCharter(
        project_id="",
        title="",
        sponsor="",
        project_manager="",
        purpose="",
        business_case="",
        strategic_alignment=[],
        objectives=[],
        in_scope=[],
        out_of_scope=[],
        deliverables=[],
        milestones=[],
        assumptions=[],
        constraints=[],
        risks=[],
        stakeholders=[],
        acceptance_criteria=[],
        budget_ceiling=0,
    )

    valid, errors = invalid.validate()

    print(f"Valid: {valid}")
    print("Errors:")
    for error in errors:
        print(f"  - {error}")


demonstrate_invalid_charter()


# ---------------------------------------------------------------------------
# 12. DECISION TRADE-OFFS
# ---------------------------------------------------------------------------

print_section("12. Authorization Trade-Offs")

trade_offs = [
    (
        "High strategic value",
        "Low feasibility",
        "Do not authorize automatically; investigate feasibility."
    ),
    (
        "Low strategic value",
        "High feasibility",
        "Easy to execute does not necessarily justify investment."
    ),
    (
        "High value",
        "High feasibility",
        "Strong candidate for authorization."
    ),
    (
        "Unclear value",
        "Unclear feasibility",
        "Request a stronger business case before authorization."
    ),
]

for value, feasibility, recommendation in trade_offs:
    print(f"{value} + {feasibility} -> {recommendation}")


# ---------------------------------------------------------------------------
# 13. PERFORMANCE AND QUALITY CONSIDERATIONS
# ---------------------------------------------------------------------------

print_section("13. Implementation and Quality Considerations")

print(
    """
A project charter is primarily a governance artifact, not a detailed
execution schedule.

Quality considerations:
    - Keep authorization information at the correct level of detail.
    - Make objectives measurable.
    - Define scope boundaries.
    - Identify material assumptions and constraints.
    - Record meaningful risks rather than creating a long generic list.
    - Make authority explicit.
    - Connect project objectives to organizational strategy.
    - Define acceptance at an outcome or deliverable level.
    - Record approval decisions and dates.
    - Control revisions after authorization.

A charter that is too vague can cause uncontrolled interpretation.
A charter that is excessively detailed can duplicate the project
management plan and become difficult to maintain.

The appropriate level of detail depends on organizational governance,
project complexity, risk, regulatory requirements, and decision authority.
"""
)


# ---------------------------------------------------------------------------
# 14. SIMPLE COMPLEXITY ANALYSIS
# ---------------------------------------------------------------------------

print_section("14. Complexity of Programmatic Charter Validation")

def validation_complexity(charter_to_check: ProjectCharter) -> str:
    """
    Most validation operations inspect each major collection once.

    If:
        O = number of objectives
        R = number of risks
        S = number of stakeholders
        M = number of milestones

    A straightforward validation pass is approximately:
        O(O + R + S + M)

    The number of fields is small and usually bounded, so real-world
    performance is dominated by the quality and governance of the data,
    not CPU cost.
    """
    counts = {
        "objectives": len(charter_to_check.objectives),
        "risks": len(charter_to_check.risks),
        "stakeholders": len(charter_to_check.stakeholders),
        "milestones": len(charter_to_check.milestones),
    }

    return str(counts)


print(validation_complexity(charter))


# ---------------------------------------------------------------------------
# 15. MINI TEST SUITE
# ---------------------------------------------------------------------------

print_section("15. Embedded Tests")

def test_smart_objective() -> None:
    assert strong_objective.smart is True
    assert weak_objective.smart is False


def test_risk_exposure() -> None:
    risk = Risk("T-1", "Test", 0.5, 10, "Mitigate")
    assert math.isclose(risk.exposure, 5.0)


def test_valid_charter() -> None:
    valid, errors = charter.validate()
    assert valid is True
    assert errors == []


def test_authorization() -> None:
    test_charter = ProjectCharter(
        project_id="T-001",
        title="Test Project",
        sponsor="Sponsor",
        project_manager="Manager",
        purpose="Test purpose",
        business_case="Test business case",
        strategic_alignment=["Goal"],
        objectives=[strong_objective],
        in_scope=["Feature"],
        out_of_scope=["Unrelated feature"],
        deliverables=["Deliverable"],
        milestones=[Milestone("Start", date(2026, 10, 1))],
        assumptions=["Resource available"],
        constraints=["Budget"],
        risks=[],
        stakeholders=[
            Stakeholder("Sponsor", "Sponsor", 5, 5, "Reports")
        ],
        acceptance_criteria=["Meets requirements"],
        budget_ceiling=1000,
    )

    assert test_charter.authorize() is True
    assert test_charter.status == AuthorizationStatus.AUTHORIZED


test_smart_objective()
test_risk_exposure()
test_valid_charter()
test_authorization()

print("All embedded tests passed.")


# ---------------------------------------------------------------------------
# 16. COMPLETE AUTHORIZATION WORKFLOW
# ---------------------------------------------------------------------------

print_section("16. Complete Project Authorization Workflow")

workflow = [
    "Identify business problem or opportunity",
    "Develop the business case",
    "Assess strategic alignment",
    "Identify preliminary objectives",
    "Define high-level scope boundaries",
    "Identify major deliverables and milestones",
    "Identify sponsor and initial project manager",
    "Identify key stakeholders",
    "Document assumptions and constraints",
    "Identify material risks",
    "Define high-level acceptance criteria",
    "Establish authorization-level budget or funding boundary",
    "Draft the project charter",
    "Review the charter with relevant stakeholders",
    "Resolve material gaps",
    "Obtain formal authorization",
    "Record decision, authority, date, and version",
    "Transition from authorization into detailed planning",
]

for number, step in enumerate(workflow, start=1):
    print(f"{number:2}. {step}")


# ---------------------------------------------------------------------------
# 17. FINAL AUTHORIZED CHARTER SNAPSHOT
# ---------------------------------------------------------------------------

print_section("17. Authorized Charter Snapshot")

print(f"Project ID:       {charter.project_id}")
print(f"Title:            {charter.title}")
print(f"Sponsor:          {charter.sponsor}")
print(f"Project Manager:  {charter.project_manager}")
print(f"Status:           {charter.status.value}")
print(f"Version:          {charter.version}")
print(f"Budget Ceiling:   {charter.budget_ceiling:,.2f}")

print("\nObjectives:")
for objective in charter.objectives:
    print(f"  - {objective.description}")

print("\nDeliverables:")
for deliverable in charter.deliverables:
    print(f"  - {deliverable}")

print("\nMilestones:")
for milestone in charter.milestones:
    print(f"  - {milestone.name}: {milestone.target_date.isoformat()}")

print("\nHighest-risk items:")
for item in charter.risk_register():
    print(
        f"  - {item['id']}: {item['severity']} "
        f"(exposure={item['exposure']:.1f})"
    )

print(
    """
The key governance principle demonstrated by this program is that
authorization is a decision, not merely the completion of a document.

The charter provides the information required to make that decision.
Formal authorization gives the project legitimacy, establishes authority,
and creates a baseline for subsequent project planning and governance.
"""
)
