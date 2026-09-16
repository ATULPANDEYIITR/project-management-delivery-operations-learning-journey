"""
Project Sponsor and the Role of the Project Sponsor

A self-contained study program covering project sponsorship from beginner
through advanced level, with executable demonstrations of governance,
decision-making, stakeholder management, escalation, benefits realization,
risk oversight, project controls, and sponsor effectiveness.

The examples use a fictional enterprise project so that the program can be
executed without external files or packages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import math
import statistics
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# 1. FUNDAMENTALS
# ---------------------------------------------------------------------------

print("=" * 78)
print("PROJECT SPONSOR: ROLE, RESPONSIBILITIES, GOVERNANCE AND PRACTICE")
print("=" * 78)


def explain_fundamentals() -> None:
    """
    Print the fundamental concepts while keeping the explanations close to
    executable examples.
    """
    concepts = {
        "Project": (
            "A temporary undertaking created to deliver a defined product, "
            "service, capability, or result."
        ),
        "Project sponsor": (
            "A senior individual who provides organizational ownership, "
            "strategic direction, authority, resources, and executive support "
            "for a project."
        ),
        "Project manager": (
            "The person responsible for day-to-day project management and "
            "coordination within the authority delegated by governance."
        ),
        "Stakeholder": (
            "An individual, group, or organization that can affect, be "
            "affected by, or perceive itself affected by the project."
        ),
        "Governance": (
            "The framework through which decisions, accountability, "
            "escalation, oversight, and control are established."
        ),
        "Business case": (
            "The structured justification for undertaking a project, "
            "including expected value, costs, risks, alternatives, and "
            "strategic alignment."
        ),
        "Benefits": (
            "Measurable improvements or advantages expected from project "
            "outputs and their adoption."
        ),
        "Escalation": (
            "The controlled transfer of a decision, issue, risk, or exception "
            "to a level with appropriate authority."
        ),
    }

    for term, definition in concepts.items():
        print(f"\n{term}")
        print(f"  {definition}")


explain_fundamentals()


# ---------------------------------------------------------------------------
# 2. SPONSOR RESPONSIBILITIES
# ---------------------------------------------------------------------------

SPONSOR_RESPONSIBILITIES = [
    "Champion the project at executive level",
    "Confirm strategic alignment",
    "Approve or sponsor the business case",
    "Secure organizational commitment and resources",
    "Establish governance and decision rights",
    "Appoint or support appointment of the project manager",
    "Provide timely executive decisions",
    "Remove organizational barriers",
    "Manage senior stakeholder relationships",
    "Review major risks and issues",
    "Approve significant scope or funding changes",
    "Protect the project's strategic purpose",
    "Monitor benefits realization",
    "Support organizational adoption and change",
    "Authorize closure when appropriate",
]

print("\n" + "=" * 78)
print("CORE RESPONSIBILITIES OF A PROJECT SPONSOR")
print("=" * 78)

for number, responsibility in enumerate(SPONSOR_RESPONSIBILITIES, start=1):
    print(f"{number:02d}. {responsibility}")


# ---------------------------------------------------------------------------
# 3. WHAT THE SPONSOR DOES NOT NORMALLY DO
# ---------------------------------------------------------------------------

SPONSOR_BOUNDARIES = {
    "Normally sponsor-owned": [
        "Strategic direction",
        "Executive stakeholder alignment",
        "Funding authorization",
        "Major scope decisions",
        "Governance",
        "Benefits ownership",
        "Organizational escalation",
        "Executive-level risk decisions",
    ],
    "Normally project-manager-owned": [
        "Day-to-day planning",
        "Task coordination",
        "Detailed schedule management",
        "Routine status reporting",
        "Team coordination",
        "Detailed issue tracking",
        "Operational project controls",
    ],
}

print("\n" + "=" * 78)
print("SPONSOR AND PROJECT MANAGER BOUNDARIES")
print("=" * 78)

for category, responsibilities in SPONSOR_BOUNDARIES.items():
    print(f"\n{category}:")
    for item in responsibilities:
        print(f"  - {item}")


# ---------------------------------------------------------------------------
# 4. ENUMERATIONS AND DOMAIN MODELS
# ---------------------------------------------------------------------------

class ProjectStatus(Enum):
    INITIATING = "Initiating"
    PLANNING = "Planning"
    EXECUTING = "Executing"
    AT_RISK = "At Risk"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class DecisionType(Enum):
    ROUTINE = "Routine"
    MAJOR = "Major"
    STRATEGIC = "Strategic"
    EMERGENCY = "Emergency"


class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class StakeholderInfluence(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@dataclass
class Stakeholder:
    name: str
    role: str
    influence: StakeholderInfluence
    interest: StakeholderInfluence
    engagement_level: int = 50

    def engagement_category(self) -> str:
        if self.engagement_level >= 80:
            return "Highly engaged"
        if self.engagement_level >= 60:
            return "Engaged"
        if self.engagement_level >= 40:
            return "Neutral"
        return "Needs attention"


@dataclass
class Risk:
    risk_id: str
    description: str
    probability: float
    impact: float
    owner: str
    mitigation: str
    status: str = "Open"

    @property
    def exposure(self) -> float:
        return self.probability * self.impact

    @property
    def level(self) -> RiskLevel:
        if self.exposure >= 20:
            return RiskLevel.CRITICAL
        if self.exposure >= 12:
            return RiskLevel.HIGH
        if self.exposure >= 6:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


@dataclass
class Benefit:
    benefit_id: str
    description: str
    baseline: float
    target: float
    current: float
    unit: str
    owner: str

    @property
    def progress_percentage(self) -> float:
        denominator = self.target - self.baseline
        if denominator == 0:
            return 100.0 if self.current >= self.target else 0.0
        progress = ((self.current - self.baseline) / denominator) * 100
        return max(0.0, min(100.0, progress))


@dataclass
class Decision:
    decision_id: str
    description: str
    decision_type: DecisionType
    required_by: date
    owner: str
    decided: bool = False
    outcome: Optional[str] = None


@dataclass
class Project:
    project_id: str
    name: str
    strategic_objective: str
    sponsor_name: str
    project_manager_name: str
    approved_budget: float
    current_forecast: float
    status: ProjectStatus = ProjectStatus.INITIATING
    scope_baseline: str = ""
    stakeholders: List[Stakeholder] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    benefits: List[Benefit] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)

    @property
    def budget_variance(self) -> float:
        return self.approved_budget - self.current_forecast

    @property
    def budget_variance_percentage(self) -> float:
        if self.approved_budget == 0:
            return 0.0
        return (self.budget_variance / self.approved_budget) * 100

    @property
    def critical_risks(self) -> List[Risk]:
        return [risk for risk in self.risks if risk.level == RiskLevel.CRITICAL]

    @property
    def overdue_decisions(self) -> List[Decision]:
        today = date.today()
        return [
            decision
            for decision in self.decisions
            if not decision.decided and decision.required_by < today
        ]

    @property
    def average_benefit_progress(self) -> float:
        if not self.benefits:
            return 0.0
        return statistics.mean(
            benefit.progress_percentage for benefit in self.benefits
        )


# ---------------------------------------------------------------------------
# 5. SPONSOR CLASS
# ---------------------------------------------------------------------------

@dataclass
class ProjectSponsor:
    name: str
    title: str
    authority_limit: float
    strategic_priorities: List[str]
    active_projects: List[Project] = field(default_factory=list)

    def sponsor_project(self, project: Project) -> None:
        if project.sponsor_name != self.name:
            raise ValueError(
                f"{self.name} is not recorded as sponsor of {project.name}."
            )
        if project not in self.active_projects:
            self.active_projects.append(project)
        project.status = ProjectStatus.INITIATING
        print(f"\nSponsor {self.name} formally sponsors '{project.name}'.")

    def confirm_alignment(self, project: Project) -> bool:
        alignment = any(
            priority.lower() in project.strategic_objective.lower()
            or project.strategic_objective.lower() in priority.lower()
            for priority in self.strategic_priorities
        )
        print(
            f"Strategic alignment for '{project.name}': "
            f"{'Aligned' if alignment else 'Requires review'}"
        )
        return alignment

    def approve_funding(
        self,
        project: Project,
        requested_amount: float,
    ) -> bool:
        if requested_amount < 0:
            raise ValueError("Requested funding cannot be negative.")

        if requested_amount <= self.authority_limit:
            project.approved_budget = requested_amount
            project.current_forecast = requested_amount
            print(
                f"Funding of {requested_amount:,.2f} approved by "
                f"{self.name}."
            )
            return True

        print(
            f"Funding request of {requested_amount:,.2f} exceeds "
            f"authority limit of {self.authority_limit:,.2f}."
        )
        return False

    def make_decision(
        self,
        project: Project,
        decision_id: str,
        outcome: str,
    ) -> bool:
        for decision in project.decisions:
            if decision.decision_id == decision_id:
                decision.decided = True
                decision.outcome = outcome
                print(
                    f"Sponsor decision {decision_id}: {outcome}"
                )
                return True

        print(f"Decision {decision_id} was not found.")
        return False

    def remove_barrier(
        self,
        project: Project,
        barrier: str,
    ) -> None:
        print(
            f"Executive action by {self.name}: barrier removed -> {barrier}"
        )

    def approve_major_change(
        self,
        project: Project,
        change_cost: float,
        strategic_alignment: bool,
    ) -> bool:
        if change_cost < 0:
            raise ValueError("Change cost cannot be negative.")

        if not strategic_alignment:
            print("Major change rejected: insufficient strategic alignment.")
            return False

        if change_cost > self.authority_limit:
            print("Major change escalated: outside sponsor authority.")
            return False

        project.current_forecast += change_cost
        print(
            f"Major change approved. Forecast increased by "
            f"{change_cost:,.2f}."
        )
        return True

    def review_risks(self, project: Project) -> List[Risk]:
        critical = project.critical_risks
        print(
            f"Sponsor risk review: {len(critical)} critical risk(s) "
            f"require executive attention."
        )
        return critical

    def review_benefits(self, project: Project) -> float:
        progress = project.average_benefit_progress
        print(
            f"Average benefit realization for '{project.name}': "
            f"{progress:.1f}%"
        )
        return progress

    def authorize_closure(self, project: Project) -> bool:
        if project.status not in {
            ProjectStatus.COMPLETED,
            ProjectStatus.CANCELLED,
        }:
            print("Closure not authorized because the project is still active.")
            return False

        print(f"Closure authorized for '{project.name}'.")
        return True


# ---------------------------------------------------------------------------
# 6. CREATE A REALISTIC PROJECT
# ---------------------------------------------------------------------------

project = Project(
    project_id="PRJ-001",
    name="Enterprise Customer Service Modernization",
    strategic_objective="Digital transformation and customer service improvement",
    sponsor_name="Anita Sharma",
    project_manager_name="Rahul Mehta",
    approved_budget=5_000_000,
    current_forecast=4_850_000,
    scope_baseline=(
        "Implement a unified customer service platform, migrate approved "
        "customer data, integrate selected channels, train service teams, "
        "and establish measurable service-performance improvements."
    ),
)

sponsor = ProjectSponsor(
    name="Anita Sharma",
    title="Chief Customer Officer",
    authority_limit=750_000,
    strategic_priorities=[
        "Digital transformation",
        "Customer service improvement",
        "Operational efficiency",
    ],
)

project.stakeholders = [
    Stakeholder(
        "Chief Executive Officer",
        "Executive stakeholder",
        StakeholderInfluence.HIGH,
        StakeholderInfluence.HIGH,
        80,
    ),
    Stakeholder(
        "Chief Information Officer",
        "Technology executive",
        StakeholderInfluence.HIGH,
        StakeholderInfluence.HIGH,
        75,
    ),
    Stakeholder(
        "Customer Service Director",
        "Business owner",
        StakeholderInfluence.HIGH,
        StakeholderInfluence.HIGH,
        90,
    ),
    Stakeholder(
        "Service Agents",
        "End users",
        StakeholderInfluence.MEDIUM,
        StakeholderInfluence.HIGH,
        55,
    ),
    Stakeholder(
        "Finance Controller",
        "Control function",
        StakeholderInfluence.MEDIUM,
        StakeholderInfluence.MEDIUM,
        65,
    ),
]

project.risks = [
    Risk(
        "R-001",
        "Legacy customer data may contain inconsistent records.",
        0.7,
        8,
        "Data Migration Lead",
        "Data profiling, cleansing and reconciliation.",
    ),
    Risk(
        "R-002",
        "Business users may resist the new operating model.",
        0.6,
        9,
        "Change Lead",
        "Training, communication and user involvement.",
    ),
    Risk(
        "R-003",
        "Critical integration may miss the planned release window.",
        0.4,
        10,
        "Technical Lead",
        "Early interface testing and contingency planning.",
    ),
    Risk(
        "R-004",
        "Unapproved scope growth could increase total cost.",
        0.5,
        7,
        "Project Manager",
        "Formal change control and sponsor governance.",
    ),
]

project.benefits = [
    Benefit(
        "B-001",
        "Reduce average customer response time.",
        24,
        12,
        17,
        "hours",
        "Customer Service Director",
    ),
    Benefit(
        "B-002",
        "Increase first-contact resolution.",
        62,
        80,
        72,
        "%",
        "Customer Service Director",
    ),
    Benefit(
        "B-003",
        "Reduce manual service processing effort.",
        100,
        70,
        82,
        "index",
        "Operations Director",
    ),
]

project.decisions = [
    Decision(
        "D-001",
        "Approve integration architecture exception.",
        DecisionType.MAJOR,
        date.today() - timedelta(days=2),
        sponsor.name,
    ),
    Decision(
        "D-002",
        "Select phased versus single-release deployment.",
        DecisionType.STRATEGIC,
        date.today() + timedelta(days=3),
        sponsor.name,
    ),
]


# ---------------------------------------------------------------------------
# 7. SPONSORSHIP WORKFLOW
# ---------------------------------------------------------------------------

print("\n" + "=" * 78)
print("SPONSORSHIP WORKFLOW")
print("=" * 78)

sponsor.sponsor_project(project)
sponsor.confirm_alignment(project)

print("\nBusiness case perspective:")
print(f"  Project: {project.name}")
print(f"  Strategic objective: {project.strategic_objective}")
print(f"  Sponsor: {project.sponsor_name}")
print(f"  Project manager: {project.project_manager_name}")
print(f"  Budget: {project.approved_budget:,.2f}")

project.status = ProjectStatus.PLANNING
print(f"  Status: {project.status.value}")


# ---------------------------------------------------------------------------
# 8. RISK HEAT MAP LOGIC
# ---------------------------------------------------------------------------

print("\n" + "=" * 78)
print("RISK REVIEW")
print("=" * 78)

for risk in project.risks:
    print(
        f"{risk.risk_id} | exposure={risk.exposure:5.2f} | "
        f"level={risk.level.value:8s} | {risk.description}"
    )

critical_risks = sponsor.review_risks(project)

for risk in critical_risks:
    print(f"  Executive attention: {risk.risk_id} -> {risk.mitigation}")


# ---------------------------------------------------------------------------
# 9. DECISION GOVERNANCE
# ---------------------------------------------------------------------------

print("\n" + "=" * 78)
print("DECISION GOVERNANCE")
print("=" * 78)

for decision in project.decisions:
    state = "Decided" if decision.decided else "Pending"
    print(
        f"{decision.decision_id} | {decision.decision_type.value:10s} | "
        f"{state:8s} | due={decision.required_by}"
    )

if project.overdue_decisions:
    print("\nOverdue decisions:")
    for decision in project.overdue_decisions:
        print(f"  - {decision.decision_id}: {decision.description}")
        sponsor.make_decision(
            project,
            decision.decision_id,
            "Approved with controlled implementation.",
        )


# ---------------------------------------------------------------------------
# 10. STAKEHOLDER ENGAGEMENT
# ---------------------------------------------------------------------------

print("\n" + "=" * 78)
print("STAKEHOLDER ENGAGEMENT")
print("=" * 78)

for stakeholder in project.stakeholders:
    print(
        f"{stakeholder.name:25s} | "
        f"influence={stakeholder.influence.value:6s} | "
        f"interest={stakeholder.interest.value:6s} | "
        f"engagement={stakeholder.engagement_category()}"
    )


def engagement_action(stakeholder: Stakeholder) -> str:
    """
    A simple power-interest interpretation.

    High influence/high interest stakeholders require close management.
    High influence/low interest stakeholders generally require sufficient
    executive communication without unnecessary operational involvement.
    """
    if (
        stakeholder.influence == StakeholderInfluence.HIGH
        and stakeholder.interest == StakeholderInfluence.HIGH
    ):
        return "Manage closely"
    if (
        stakeholder.influence == StakeholderInfluence.HIGH
        and stakeholder.interest == StakeholderInfluence.LOW
    ):
        return "Keep satisfied"
    if (
        stakeholder.influence == StakeholderInfluence.LOW
        and stakeholder.interest == StakeholderInfluence.HIGH
    ):
        return "Keep informed"
    return "Monitor"


print("\nRecommended engagement approach:")
for stakeholder in project.stakeholders:
    print(
        f"  {stakeholder.name:25s} -> "
        f"{engagement_action(stakeholder)}"
    )


# ---------------------------------------------------------------------------
# 11. BENEFITS REALIZATION
# ---------------------------------------------------------------------------

print("\n" + "=" * 78)
print("BENEFITS REALIZATION")
print("=" * 78)

for benefit in project.benefits:
    print(
        f"{benefit.benefit_id} | {benefit.description} | "
        f"baseline={benefit.baseline:g}{benefit.unit} | "
        f"target={benefit.target:g}{benefit.unit} | "
        f"current={benefit.current:g}{benefit.unit} | "
        f"progress={benefit.progress_percentage:.1f}%"
    )

sponsor.review_benefits(project)


# ---------------------------------------------------------------------------
# 12. CHANGE CONTROL
# ---------------------------------------------------------------------------

print("\n" + "=" * 78)
print("CHANGE CONTROL")
print("=" * 78)

requested_change = 450_000
sponsor.approve_major_change(
    project,
    change_cost=requested_change,
    strategic_alignment=True,
)

print(
    f"Updated forecast: {project.current_forecast:,.2f}\n"
    f"Budget variance: {project.budget_variance:,.2f}\n"
    f"Variance percentage: {project.budget_variance_percentage:.2f}%"
)


# ---------------------------------------------------------------------------
# 13. ESCALATION MODEL
# ---------------------------------------------------------------------------

@dataclass
class Escalation:
    item_id: str
    description: str
    current_owner: str
    required_authority: str
    deadline: date
    impact: str

    def requires_sponsor(self) -> bool:
        sponsor_keywords = (
            "funding",
            "strategic",
            "executive",
            "major scope",
            "organizational",
            "regulatory",
        )
        text = f"{self.description} {self.impact}".lower()
        return any(keyword in text for keyword in sponsor_keywords)


escalations = [
    Escalation(
        "E-001",
        "Funding increase required for strategic integration.",
        "Project Manager",
        "Executive sponsor",
        date.today() + timedelta(days=2),
        "Potential delay without decision.",
    ),
    Escalation(
        "E-002",
        "Team needs clarification on routine test execution.",
        "Technical Lead",
        "Project Manager",
        date.today() + timedelta(days=1),
        "Limited operational impact.",
    ),
]

print("\n" + "=" * 78)
print("ESCALATION ANALYSIS")
print("=" * 78)

for escalation in escalations:
    destination = (
        "Project Sponsor"
        if escalation.requires_sponsor()
        else "Project Manager / Functional Lead"
    )
    print(
        f"{escalation.item_id} -> {destination} | "
        f"{escalation.description}"
    )


# ---------------------------------------------------------------------------
# 14. SPONSOR EFFECTIVENESS METRICS
# ---------------------------------------------------------------------------

@dataclass
class SponsorEffectiveness:
    decision_timeliness_score: float
    strategic_alignment_score: float
    stakeholder_support_score: float
    risk_governance_score: float
    benefits_ownership_score: float

    def overall_index(self) -> float:
        """
        A weighted governance indicator.

        This is a management diagnostic, not a universal industry standard.
        """
        weights = {
            "decision": 0.25,
            "alignment": 0.20,
            "stakeholder": 0.20,
            "risk": 0.15,
            "benefits": 0.20,
        }

        return (
            self.decision_timeliness_score * weights["decision"]
            + self.strategic_alignment_score * weights["alignment"]
            + self.stakeholder_support_score * weights["stakeholder"]
            + self.risk_governance_score * weights["risk"]
            + self.benefits_ownership_score * weights["benefits"]
        )


effectiveness = SponsorEffectiveness(
    decision_timeliness_score=88,
    strategic_alignment_score=94,
    stakeholder_support_score=86,
    risk_governance_score=82,
    benefits_ownership_score=79,
)

print("\n" + "=" * 78)
print("SPONSOR EFFECTIVENESS INDICATOR")
print("=" * 78)
print(f"Decision timeliness:      {effectiveness.decision_timeliness_score:.1f}")
print(f"Strategic alignment:      {effectiveness.strategic_alignment_score:.1f}")
print(f"Stakeholder support:      {effectiveness.stakeholder_support_score:.1f}")
print(f"Risk governance:          {effectiveness.risk_governance_score:.1f}")
print(f"Benefits ownership:       {effectiveness.benefits_ownership_score:.1f}")
print(f"Weighted indicator:       {effectiveness.overall_index():.1f}")


# ---------------------------------------------------------------------------
# 15. EARNED VALUE INTERPRETATION
# ---------------------------------------------------------------------------

@dataclass
class EarnedValue:
    planned_value: float
    earned_value: float
    actual_cost: float

    @property
    def schedule_variance(self) -> float:
        return self.earned_value - self.planned_value

    @property
    def cost_variance(self) -> float:
        return self.earned_value - self.actual_cost

    @property
    def schedule_performance_index(self) -> float:
        if self.planned_value == 0:
            return math.nan
        return self.earned_value / self.planned_value

    @property
    def cost_performance_index(self) -> float:
        if self.actual_cost == 0:
            return math.nan
        return self.earned_value / self.actual_cost


ev = EarnedValue(
    planned_value=3_000_000,
    earned_value=2_700_000,
    actual_cost=2_900_000,
)

print("\n" + "=" * 78)
print("EXECUTIVE PROJECT CONTROL INDICATORS")
print("=" * 78)
print(f"Planned value (PV): {ev.planned_value:,.0f}")
print(f"Earned value (EV):  {ev.earned_value:,.0f}")
print(f"Actual cost (AC):   {ev.actual_cost:,.0f}")
print(f"Schedule variance:  {ev.schedule_variance:,.0f}")
print(f"Cost variance:      {ev.cost_variance:,.0f}")
print(f"SPI:                {ev.schedule_performance_index:.3f}")
print(f"CPI:                {ev.cost_performance_index:.3f}")

if ev.schedule_performance_index < 1:
    print("Schedule interpretation: progress is behind the planned value.")

if ev.cost_performance_index < 1:
    print("Cost interpretation: earned value is below actual cost.")


# ---------------------------------------------------------------------------
# 16. SPONSOR DECISION MATRIX
# ---------------------------------------------------------------------------

def decision_authority(
    impact: str,
    cost: float,
    strategic_change: bool,
    sponsor_limit: float,
) -> str:
    """
    Simplified decision-rights model.

    In real organizations, the governance framework, delegated authority,
    policies, contracts, and regulatory requirements determine the actual
    authority boundary.
    """
    if strategic_change:
        return "Sponsor or governing body"
    if cost > sponsor_limit:
        return "Escalate to higher authority"
    if impact == "low":
        return "Project manager"
    if impact == "medium":
        return "Project manager with governance review"
    return "Sponsor"


print("\n" + "=" * 78)
print("DECISION AUTHORITY EXAMPLES")
print("=" * 78)

decision_examples = [
    ("low", 20_000, False),
    ("medium", 100_000, False),
    ("high", 400_000, True),
    ("high", 1_200_000, False),
]

for impact, cost, strategic_change in decision_examples:
    authority = decision_authority(
        impact,
        cost,
        strategic_change,
        sponsor.authority_limit,
    )
    print(
        f"impact={impact:6s} | cost={cost:9,.0f} | "
        f"strategic_change={str(strategic_change):5s} | {authority}"
    )


# ---------------------------------------------------------------------------
# 17. COMMON SPONSOR FAILURE MODES
# ---------------------------------------------------------------------------

FAILURE_MODES = {
    "Rubber-stamp sponsorship":
        "Approving the project but providing little active executive support.",
    "Micromanagement":
        "Taking over detailed project-manager responsibilities.",
    "Delayed decisions":
        "Allowing unresolved decisions to block project progress.",
    "Scope drift":
        "Allowing strategic objectives to become diluted by uncontrolled additions.",
    "Benefits neglect":
        "Treating delivery of outputs as the end of value realization.",
    "Weak stakeholder alignment":
        "Failing to resolve conflicts among powerful organizational stakeholders.",
    "Unclear authority":
        "Creating ambiguity about who can approve funding, scope, risk, or policy exceptions.",
    "Optimism bias":
        "Accepting schedules, costs, or benefits without adequate challenge.",
}

print("\n" + "=" * 78)
print("COMMON SPONSOR FAILURE MODES")
print("=" * 78)

for failure, explanation in FAILURE_MODES.items():
    print(f"\n{failure}")
    print(f"  {explanation}")


# ---------------------------------------------------------------------------
# 18. SPONSOR DECISION CHECKLIST
# ---------------------------------------------------------------------------

def sponsor_decision_checklist(
    strategic_alignment: bool,
    benefits_defined: bool,
    funding_available: bool,
    major_risks_understood: bool,
    governance_defined: bool,
    accountable_owner_identified: bool,
) -> Tuple[bool, List[str]]:
    checks = {
        "Strategic alignment": strategic_alignment,
        "Benefits defined": benefits_defined,
        "Funding available": funding_available,
        "Major risks understood": major_risks_understood,
        "Governance defined": governance_defined,
        "Accountable owner identified": accountable_owner_identified,
    }

    missing = [name for name, passed in checks.items() if not passed]
    return len(missing) == 0, missing


ready, missing_items = sponsor_decision_checklist(
    strategic_alignment=True,
    benefits_defined=True,
    funding_available=True,
    major_risks_understood=True,
    governance_defined=True,
    accountable_owner_identified=True,
)

print("\n" + "=" * 78)
print("PROJECT AUTHORIZATION READINESS")
print("=" * 78)
print(f"Ready: {ready}")

if missing_items:
    print("Missing:")
    for item in missing_items:
        print(f"  - {item}")
else:
    print("All required governance checks passed.")


# ---------------------------------------------------------------------------
# 19. PROJECT LIFECYCLE AND SPONSOR INVOLVEMENT
# ---------------------------------------------------------------------------

lifecycle = {
    "Initiation": [
        "Validate strategic rationale",
        "Support business case",
        "Identify sponsor-level stakeholders",
        "Establish governance",
    ],
    "Planning": [
        "Confirm scope boundaries",
        "Validate funding and major assumptions",
        "Confirm decision rights",
        "Review major risks",
    ],
    "Execution": [
        "Remove organizational barriers",
        "Resolve escalated decisions",
        "Maintain executive stakeholder support",
        "Monitor strategic alignment",
    ],
    "Monitoring and control": [
        "Review major deviations",
        "Challenge material forecasts",
        "Monitor risk exposure",
        "Protect benefits",
    ],
    "Closure": [
        "Confirm acceptance",
        "Confirm transition to operations",
        "Review benefits ownership",
        "Authorize formal closure",
    ],
}

print("\n" + "=" * 78)
print("SPONSOR INVOLVEMENT ACROSS THE PROJECT LIFECYCLE")
print("=" * 78)

for phase, activities in lifecycle.items():
    print(f"\n{phase}")
    for activity in activities:
        print(f"  - {activity}")


# ---------------------------------------------------------------------------
# 20. EDGE CASES
# ---------------------------------------------------------------------------

print("\n" + "=" * 78)
print("EDGE CASES")
print("=" * 78)

edge_cases = [
    (
        "Sponsor changes role",
        "Governance should appoint and document a successor rather than leaving "
        "decision authority ambiguous.",
    ),
    (
        "Project manager and sponsor disagree",
        "Use the documented governance model, evidence, business case, and "
        "decision rights rather than informal authority.",
    ),
    (
        "Benefits are achieved before delivery closes",
        "Record realized benefits while retaining formal closure controls.",
    ),
    (
        "Budget is available but strategic alignment disappears",
        "Funding availability does not by itself justify continuation.",
    ),
    (
        "A major risk becomes an actual issue",
        "Move the item from risk management into issue management and assign "
        "an accountable owner.",
    ),
    (
        "Sponsor lacks sufficient authority",
        "Escalate through the defined governance structure rather than making "
        "an unauthorized commitment.",
    ),
    (
        "Project is technically successful but benefits are absent",
        "Delivery success and business-value realization are different measures.",
    ),
]

for case, handling in edge_cases:
    print(f"\n{case}")
    print(f"  {handling}")


# ---------------------------------------------------------------------------
# 21. FINAL EXECUTIVE REPORT
# ---------------------------------------------------------------------------

def generate_executive_report(
    project: Project,
    sponsor: ProjectSponsor,
) -> str:
    critical_count = len(project.critical_risks)
    overdue_count = len(project.overdue_decisions)
    benefit_progress = project.average_benefit_progress

    return (
        "\n"
        "EXECUTIVE SPONSOR REPORT\n"
        f"Project: {project.name}\n"
        f"Sponsor: {sponsor.name}\n"
        f"Status: {project.status.value}\n"
        f"Approved budget: {project.approved_budget:,.2f}\n"
        f"Current forecast: {project.current_forecast:,.2f}\n"
        f"Budget variance: {project.budget_variance:,.2f}\n"
        f"Critical risks: {critical_count}\n"
        f"Overdue decisions: {overdue_count}\n"
        f"Average benefit realization: {benefit_progress:.1f}%\n"
    )


print("\n" + "=" * 78)
print(generate_executive_report(project, sponsor))

print("=" * 78)
print("END OF PROJECT SPONSOR STUDY PROGRAM")
print("=" * 78)
