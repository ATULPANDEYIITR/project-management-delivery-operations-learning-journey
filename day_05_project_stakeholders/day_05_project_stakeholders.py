"""
PROJECT STAKEHOLDERS
====================

A comprehensive, self-contained Python study script covering project
stakeholders from absolute beginner to advanced level.

The examples demonstrate:
- Stakeholder definitions and terminology
- Stakeholder identification and classification
- Internal and external stakeholders
- Primary and secondary stakeholders
- Project roles and responsibilities
- Stakeholder registers
- Power-interest analysis
- Influence-impact analysis
- Stakeholder salience
- Engagement assessment
- Communication planning
- Stakeholder prioritization
- Stakeholder mapping
- RACI and responsibility relationships
- Stakeholder expectations and requirements
- Conflict management
- Negotiation
- Resistance to change
- Risk relationships
- Stakeholder engagement metrics
- Scenario analysis
- Advanced scoring models
- Data validation
- Error handling
- Testing
- Practical project-management applications

The script uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Tuple
import math
import statistics
import unittest


# ============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# ============================================================================

def print_section(title: str) -> None:
    """Print a clearly separated educational section."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


print_section("1. WHAT IS A PROJECT STAKEHOLDER?")

print(
    """
A project stakeholder is an individual, group, organization, or other entity
that can affect a project, can be affected by the project, or may perceive
itself to be affected by the project.

Examples include:
- Project sponsor
- Project manager
- Project team
- Customer
- End users
- Senior management
- Functional managers
- Suppliers
- Contractors
- Regulators
- Government agencies
- Local communities
- Investors
- Partners

Stakeholder management is not simply about keeping people informed.
It involves identifying stakeholders, understanding their interests and
influence, assessing their expectations, planning engagement, communicating
appropriately, managing relationships, and monitoring changes throughout
the project lifecycle.
"""
)


# ============================================================================
# 2. SIMPLE STAKEHOLDER EXAMPLE
# ============================================================================

print_section("2. A SIMPLE STAKEHOLDER EXAMPLE")

project_stakeholders = [
    "Project Sponsor",
    "Project Manager",
    "Development Team",
    "Customer",
    "End Users",
    "Supplier",
    "Regulatory Authority",
]

for stakeholder in project_stakeholders:
    print("-", stakeholder)


# ============================================================================
# 3. STAKEHOLDER CLASSIFICATIONS
# ============================================================================

class StakeholderType(Enum):
    """Broad stakeholder classification."""

    INTERNAL = "Internal"
    EXTERNAL = "External"


class StakeholderRelationship(Enum):
    """Relationship of the stakeholder to project execution."""

    PRIMARY = "Primary"
    SECONDARY = "Secondary"


class EngagementLevel(Enum):
    """Common engagement states used in stakeholder analysis."""

    UNAWARE = "Unaware"
    RESISTANT = "Resistant"
    NEUTRAL = "Neutral"
    SUPPORTIVE = "Supportive"
    LEADING = "Leading"


class PriorityLevel(Enum):
    """Priority categories assigned after stakeholder analysis."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class CommunicationFrequency(Enum):
    """Typical communication frequencies."""

    DAILY = "Daily"
    WEEKLY = "Weekly"
    BIWEEKLY = "Biweekly"
    MONTHLY = "Monthly"
    MILESTONE = "At Milestones"
    AS_NEEDED = "As Needed"


print_section("3. STAKEHOLDER CLASSIFICATION")

classification_examples = {
    "Internal": [
        "Project Manager",
        "Project Team",
        "Project Sponsor",
        "Functional Manager",
    ],
    "External": [
        "Customer",
        "Supplier",
        "Government Regulator",
        "Community Representative",
    ],
    "Primary": [
        "Project Sponsor",
        "Customer",
        "Project Team",
        "End Users",
    ],
    "Secondary": [
        "Local Community",
        "Industry Association",
        "Media",
        "Indirectly affected organizations",
    ],
}

for category, examples in classification_examples.items():
    print(f"\n{category} stakeholders:")
    for item in examples:
        print(f"  - {item}")


# ============================================================================
# 4. STAKEHOLDER ROLES
# ============================================================================

print_section("4. COMMON PROJECT STAKEHOLDER ROLES")

stakeholder_roles = {
    "Project Sponsor": (
        "Provides strategic support, authority, funding support, and "
        "executive-level escalation."
    ),
    "Project Manager": (
        "Coordinates planning, execution, communication, risks, resources, "
        "and stakeholder engagement."
    ),
    "Project Team": (
        "Performs the technical, operational, analytical, or administrative "
        "work required to deliver project outputs."
    ),
    "Customer": (
        "Defines business needs, validates outcomes, and may accept project "
        "deliverables."
    ),
    "End User": (
        "Uses the delivered product, service, or result and provides "
        "practical feedback."
    ),
    "Supplier": (
        "Provides goods, services, technology, expertise, or external "
        "resources."
    ),
    "Regulator": (
        "Establishes or enforces applicable legal, regulatory, safety, "
        "environmental, or compliance requirements."
    ),
}

for role, responsibility in stakeholder_roles.items():
    print(f"\n{role}:")
    print(f"  {responsibility}")


# ============================================================================
# 5. STAKEHOLDER DATA MODEL
# ============================================================================

@dataclass
class Stakeholder:
    """
    Represents a project stakeholder.

    power:
        Ability to influence project decisions or outcomes, normally 1-5.

    interest:
        Degree to which the stakeholder cares about project outcomes, 1-5.

    impact:
        Degree to which the project can affect the stakeholder, 1-5.

    urgency:
        How quickly the stakeholder's needs or concerns require attention,
        normally 1-5.

    legitimacy:
        Degree to which the stakeholder has a recognized or appropriate
        relationship with the project, normally 1-5.
    """

    name: str
    role: str
    organization: str
    stakeholder_type: StakeholderType
    relationship: StakeholderRelationship
    power: int
    interest: int
    impact: int
    urgency: int
    legitimacy: int
    current_engagement: EngagementLevel
    desired_engagement: EngagementLevel
    communication_frequency: CommunicationFrequency
    communication_method: str
    expectations: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate stakeholder scoring immediately after object creation."""
        self._validate_score("power", self.power)
        self._validate_score("interest", self.interest)
        self._validate_score("impact", self.impact)
        self._validate_score("urgency", self.urgency)
        self._validate_score("legitimacy", self.legitimacy)

    @staticmethod
    def _validate_score(name: str, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError(f"{name} must be an integer.")
        if not 1 <= value <= 5:
            raise ValueError(f"{name} must be between 1 and 5.")

    @property
    def power_interest_score(self) -> int:
        """Combined power-interest score."""
        return self.power * self.interest

    @property
    def impact_score(self) -> int:
        """Project impact score."""
        return self.impact * self.interest

    @property
    def salience_score(self) -> int:
        """
        Simplified stakeholder salience score.

        A practical educational model multiplies:
        power × legitimacy × urgency.
        """
        return self.power * self.legitimacy * self.urgency

    @property
    def priority(self) -> PriorityLevel:
        """Convert power-interest score into a management priority."""
        score = self.power_interest_score

        if score >= 20:
            return PriorityLevel.CRITICAL
        if score >= 12:
            return PriorityLevel.HIGH
        if score >= 6:
            return PriorityLevel.MEDIUM
        return PriorityLevel.LOW

    @property
    def power_interest_quadrant(self) -> str:
        """
        Place the stakeholder into a classic power-interest matrix.
        """
        high_power = self.power >= 3
        high_interest = self.interest >= 3

        if high_power and high_interest:
            return "Manage Closely"
        if high_power and not high_interest:
            return "Keep Satisfied"
        if not high_power and high_interest:
            return "Keep Informed"
        return "Monitor"

    def engagement_gap(self) -> int:
        """
        Estimate how far current engagement is from desired engagement.

        The ordering is intentional:
        Unaware < Resistant < Neutral < Supportive < Leading.
        """
        levels = {
            EngagementLevel.UNAWARE: 0,
            EngagementLevel.RESISTANT: 1,
            EngagementLevel.NEUTRAL: 2,
            EngagementLevel.SUPPORTIVE: 3,
            EngagementLevel.LEADING: 4,
        }

        return levels[self.desired_engagement] - levels[self.current_engagement]


# ============================================================================
# 6. CREATING STAKEHOLDERS
# ============================================================================

print_section("6. CREATING A STAKEHOLDER REGISTER")

stakeholders = [
    Stakeholder(
        name="Anita Sharma",
        role="Project Sponsor",
        organization="Corporate Leadership",
        stakeholder_type=StakeholderType.INTERNAL,
        relationship=StakeholderRelationship.PRIMARY,
        power=5,
        interest=4,
        impact=4,
        urgency=4,
        legitimacy=5,
        current_engagement=EngagementLevel.SUPPORTIVE,
        desired_engagement=EngagementLevel.LEADING,
        communication_frequency=CommunicationFrequency.WEEKLY,
        communication_method="Executive review meeting",
        expectations=["Strategic alignment", "Business value", "Timely delivery"],
        concerns=["Budget", "Major risks", "Schedule slippage"],
    ),
    Stakeholder(
        name="Rahul Verma",
        role="Project Manager",
        organization="PMO",
        stakeholder_type=StakeholderType.INTERNAL,
        relationship=StakeholderRelationship.PRIMARY,
        power=5,
        interest=5,
        impact=5,
        urgency=5,
        legitimacy=5,
        current_engagement=EngagementLevel.LEADING,
        desired_engagement=EngagementLevel.LEADING,
        communication_frequency=CommunicationFrequency.DAILY,
        communication_method="Project management system",
        expectations=["Predictability", "Clear decisions", "Team coordination"],
        concerns=["Dependencies", "Risks", "Resource constraints"],
    ),
    Stakeholder(
        name="Neha Singh",
        role="Product Owner",
        organization="Business Unit",
        stakeholder_type=StakeholderType.INTERNAL,
        relationship=StakeholderRelationship.PRIMARY,
        power=4,
        interest=5,
        impact=5,
        urgency=4,
        legitimacy=5,
        current_engagement=EngagementLevel.SUPPORTIVE,
        desired_engagement=EngagementLevel.LEADING,
        communication_frequency=CommunicationFrequency.WEEKLY,
        communication_method="Backlog review",
        expectations=["Business requirements", "Usability", "Customer value"],
        concerns=["Scope", "Priorities", "User adoption"],
    ),
    Stakeholder(
        name="Vikram Rao",
        role="End User Representative",
        organization="Customer Operations",
        stakeholder_type=StakeholderType.EXTERNAL,
        relationship=StakeholderRelationship.PRIMARY,
        power=2,
        interest=5,
        impact=5,
        urgency=4,
        legitimacy=4,
        current_engagement=EngagementLevel.NEUTRAL,
        desired_engagement=EngagementLevel.SUPPORTIVE,
        communication_frequency=CommunicationFrequency.BIWEEKLY,
        communication_method="User feedback sessions",
        expectations=["Ease of use", "Reliability", "Minimal disruption"],
        concerns=["Training", "Usability", "Change impact"],
    ),
    Stakeholder(
        name="SecureTech Ltd.",
        role="Technology Supplier",
        organization="External Supplier",
        stakeholder_type=StakeholderType.EXTERNAL,
        relationship=StakeholderRelationship.PRIMARY,
        power=3,
        interest=4,
        impact=4,
        urgency=3,
        legitimacy=4,
        current_engagement=EngagementLevel.SUPPORTIVE,
        desired_engagement=EngagementLevel.SUPPORTIVE,
        communication_frequency=CommunicationFrequency.WEEKLY,
        communication_method="Supplier review",
        expectations=["Clear specifications", "Timely decisions", "Payment"],
        concerns=["Requirement changes", "Delivery dependencies"],
    ),
    Stakeholder(
        name="Compliance Authority",
        role="Regulatory Reviewer",
        organization="Government Agency",
        stakeholder_type=StakeholderType.EXTERNAL,
        relationship=StakeholderRelationship.PRIMARY,
        power=5,
        interest=3,
        impact=5,
        urgency=4,
        legitimacy=5,
        current_engagement=EngagementLevel.NEUTRAL,
        desired_engagement=EngagementLevel.SUPPORTIVE,
        communication_frequency=CommunicationFrequency.MILESTONE,
        communication_method="Formal compliance submission",
        expectations=["Compliance", "Documentation", "Auditability"],
        concerns=["Non-compliance", "Missing evidence"],
    ),
]

for stakeholder in stakeholders:
    print(
        f"{stakeholder.name:22} | "
        f"Role: {stakeholder.role:25} | "
        f"Priority: {stakeholder.priority.value:8} | "
        f"Quadrant: {stakeholder.power_interest_quadrant}"
    )


# ============================================================================
# 7. STAKEHOLDER REGISTER
# ============================================================================

class StakeholderRegister:
    """Manage a collection of project stakeholders."""

    def __init__(self) -> None:
        self._stakeholders: Dict[str, Stakeholder] = {}

    def add(self, stakeholder: Stakeholder) -> None:
        """Add a stakeholder while preventing duplicate names."""
        key = stakeholder.name.strip().lower()

        if not key:
            raise ValueError("Stakeholder name cannot be empty.")

        if key in self._stakeholders:
            raise ValueError(f"Stakeholder already exists: {stakeholder.name}")

        self._stakeholders[key] = stakeholder

    def get(self, name: str) -> Stakeholder:
        """Retrieve a stakeholder by name."""
        key = name.strip().lower()

        if key not in self._stakeholders:
            raise KeyError(f"Unknown stakeholder: {name}")

        return self._stakeholders[key]

    def remove(self, name: str) -> None:
        """Remove a stakeholder from the register."""
        key = name.strip().lower()

        if key not in self._stakeholders:
            raise KeyError(f"Unknown stakeholder: {name}")

        del self._stakeholders[key]

    def all(self) -> List[Stakeholder]:
        """Return stakeholders as a list."""
        return list(self._stakeholders.values())

    def by_priority(self, priority: PriorityLevel) -> List[Stakeholder]:
        """Filter stakeholders by priority."""
        return [
            stakeholder
            for stakeholder in self._stakeholders.values()
            if stakeholder.priority == priority
        ]

    def by_quadrant(self, quadrant: str) -> List[Stakeholder]:
        """Filter stakeholders by power-interest quadrant."""
        return [
            stakeholder
            for stakeholder in self._stakeholders.values()
            if stakeholder.power_interest_quadrant == quadrant
        ]

    def search(self, keyword: str) -> List[Stakeholder]:
        """Search stakeholder names, roles, and organizations."""
        keyword = keyword.lower()

        return [
            stakeholder
            for stakeholder in self._stakeholders.values()
            if (
                keyword in stakeholder.name.lower()
                or keyword in stakeholder.role.lower()
                or keyword in stakeholder.organization.lower()
            )
        ]


register = StakeholderRegister()

for stakeholder in stakeholders:
    register.add(stakeholder)

print_section("7. REGISTER QUERIES")

print("High-priority stakeholders:")
for stakeholder in register.by_priority(PriorityLevel.HIGH):
    print(f"  - {stakeholder.name}")

print("\nManage Closely stakeholders:")
for stakeholder in register.by_quadrant("Manage Closely"):
    print(f"  - {stakeholder.name}")

print("\nSearch for technology-related stakeholders:")
for stakeholder in register.search("technology"):
    print(f"  - {stakeholder.name}")


# ============================================================================
# 8. POWER-INTEREST MATRIX
# ============================================================================

print_section("8. POWER-INTEREST MATRIX")

print(
    """
The power-interest matrix is a stakeholder mapping technique.

High power + high interest:
    Manage Closely

High power + low interest:
    Keep Satisfied

Low power + high interest:
    Keep Informed

Low power + low interest:
    Monitor
"""
)

for stakeholder in register.all():
    print(
        f"{stakeholder.name:22} "
        f"Power={stakeholder.power} "
        f"Interest={stakeholder.interest} "
        f"-> {stakeholder.power_interest_quadrant}"
    )


# ============================================================================
# 9. POWER-INTEREST MATRIX VISUALIZATION
# ============================================================================

def print_power_interest_matrix(
    stakeholder_list: Iterable[Stakeholder],
) -> None:
    """
    Display an ASCII representation of the power-interest matrix.

    This is intentionally simple so it works in any terminal.
    """
    quadrants: Dict[str, List[str]] = {
        "Manage Closely": [],
        "Keep Satisfied": [],
        "Keep Informed": [],
        "Monitor": [],
    }

    for stakeholder in stakeholder_list:
        quadrants[stakeholder.power_interest_quadrant].append(stakeholder.name)

    print("\n                    HIGH INTEREST")
    print("                         |")
    print(
        "  Keep Informed          |          Manage Closely"
    )
    print(
        "  " + ", ".join(quadrants["Keep Informed"])[:30]
        + " " * 10
        + " | "
        + ", ".join(quadrants["Manage Closely"])[:30]
    )
    print("-------------------------+--------------------------")
    print(
        "  Monitor                |          Keep Satisfied"
    )
    print(
        "  " + ", ".join(quadrants["Monitor"])[:30]
        + " " * 10
        + " | "
        + ", ".join(quadrants["Keep Satisfied"])[:30]
    )
    print("                         |")
    print("                    LOW INTEREST")
    print("      LOW POWER -------------------------- HIGH POWER")


print_power_interest_matrix(register.all())


# ============================================================================
# 10. STAKEHOLDER SALIENCE
# ============================================================================

print_section("10. STAKEHOLDER SALIENCE")

print(
    """
Stakeholder salience is concerned with which stakeholders deserve managerial
attention based on characteristics such as:

- Power
- Legitimacy
- Urgency

A common conceptual framework identifies combinations such as:
- Dormant
- Discretionary
- Demanding
- Dominant
- Dangerous
- Dependent
- Definitive

The implementation below uses the three dimensions numerically for ranking.
It is a simplified decision-support model, not a formal replacement for
managerial judgment.
"""
)


def salience_category(stakeholder: Stakeholder) -> str:
    """Classify a stakeholder using power, legitimacy, and urgency."""

    power = stakeholder.power >= 3
    legitimacy = stakeholder.legitimacy >= 3
    urgency = stakeholder.urgency >= 3

    if power and legitimacy and urgency:
        return "Definitive"
    if power and legitimacy:
        return "Dominant"
    if power and urgency:
        return "Dangerous"
    if legitimacy and urgency:
        return "Dependent"
    if power:
        return "Dormant"
    if legitimacy:
        return "Discretionary"
    if urgency:
        return "Demanding"

    return "Low-Salience"


for stakeholder in sorted(
    register.all(),
    key=lambda item: item.salience_score,
    reverse=True,
):
    print(
        f"{stakeholder.name:22} "
        f"Score={stakeholder.salience_score:3} "
        f"Category={salience_category(stakeholder)}"
    )


# ============================================================================
# 11. ENGAGEMENT ASSESSMENT
# ============================================================================

print_section("11. STAKEHOLDER ENGAGEMENT ASSESSMENT")

for stakeholder in register.all():
    gap = stakeholder.engagement_gap()

    if gap > 0:
        action = "Increase engagement"
    elif gap < 0:
        action = "Current engagement exceeds desired level"
    else:
        action = "Maintain current engagement"

    print(
        f"{stakeholder.name:22} "
        f"Current={stakeholder.current_engagement.value:10} "
        f"Desired={stakeholder.desired_engagement.value:10} "
        f"Gap={gap:+d} -> {action}"
    )


# ============================================================================
# 12. COMMUNICATION PLANNING
# ============================================================================

@dataclass
class CommunicationPlanItem:
    """Represents a stakeholder communication requirement."""

    stakeholder_name: str
    objective: str
    message: str
    frequency: CommunicationFrequency
    method: str
    owner: str
    escalation_required: bool = False


communication_plan = [
    CommunicationPlanItem(
        stakeholder_name="Anita Sharma",
        objective="Maintain executive alignment",
        message="Progress, business value, major risks, and decisions",
        frequency=CommunicationFrequency.WEEKLY,
        method="Executive review",
        owner="Project Manager",
        escalation_required=True,
    ),
    CommunicationPlanItem(
        stakeholder_name="Vikram Rao",
        objective="Build user support",
        message="Upcoming changes, demonstrations, and training impacts",
        frequency=CommunicationFrequency.BIWEEKLY,
        method="User workshop",
        owner="Product Owner",
    ),
    CommunicationPlanItem(
        stakeholder_name="Compliance Authority",
        objective="Demonstrate compliance",
        message="Required evidence, controls, approvals, and exceptions",
        frequency=CommunicationFrequency.MILESTONE,
        method="Formal submission",
        owner="Compliance Lead",
        escalation_required=True,
    ),
]

for item in communication_plan:
    print(
        f"\nStakeholder: {item.stakeholder_name}"
        f"\nObjective: {item.objective}"
        f"\nMessage: {item.message}"
        f"\nFrequency: {item.frequency.value}"
        f"\nMethod: {item.method}"
        f"\nOwner: {item.owner}"
        f"\nEscalation: {'Yes' if item.escalation_required else 'No'}"
    )


# ============================================================================
# 13. EXPECTATIONS AND REQUIREMENTS
# ============================================================================

print_section("13. STAKEHOLDER EXPECTATIONS")

for stakeholder in register.all():
    print(f"\n{stakeholder.name}")
    print("  Expectations:")
    for expectation in stakeholder.expectations:
        print(f"    - {expectation}")

    print("  Concerns:")
    for concern in stakeholder.concerns:
        print(f"    - {concern}")


# ============================================================================
# 14. REQUIREMENT TRACEABILITY
# ============================================================================

@dataclass
class StakeholderRequirement:
    """Links a stakeholder to a project requirement."""

    requirement_id: str
    stakeholder_name: str
    description: str
    priority: PriorityLevel
    acceptance_criteria: str
    status: str = "Open"


requirements = [
    StakeholderRequirement(
        requirement_id="REQ-001",
        stakeholder_name="Neha Singh",
        description="The solution must support the approved business workflow.",
        priority=PriorityLevel.CRITICAL,
        acceptance_criteria="All approved workflow scenarios pass acceptance testing.",
    ),
    StakeholderRequirement(
        requirement_id="REQ-002",
        stakeholder_name="Vikram Rao",
        description="The interface must support the core user tasks.",
        priority=PriorityLevel.HIGH,
        acceptance_criteria="Representative users complete defined tasks without critical defects.",
    ),
    StakeholderRequirement(
        requirement_id="REQ-003",
        stakeholder_name="Compliance Authority",
        description="Required audit evidence must be retained.",
        priority=PriorityLevel.CRITICAL,
        acceptance_criteria="All mandatory evidence is available for review.",
    ),
]

print_section("14. STAKEHOLDER REQUIREMENTS")

for requirement in requirements:
    print(
        f"{requirement.requirement_id}: "
        f"{requirement.stakeholder_name} | "
        f"{requirement.priority.value} | "
        f"{requirement.status}"
    )
    print(f"  {requirement.description}")
    print(f"  Acceptance: {requirement.acceptance_criteria}")


# ============================================================================
# 15. RACI MATRIX
# ============================================================================

print_section("15. RACI AND STAKEHOLDER RESPONSIBILITY")

print(
    """
RACI represents:

R = Responsible
    Person or group performing the work.

A = Accountable
    Person who owns the outcome and is ultimately answerable.

C = Consulted
    Stakeholder whose input is requested.

I = Informed
    Stakeholder who receives relevant information.

A RACI matrix helps distinguish responsibility from stakeholder influence.
A person with high power is not automatically the person who performs the
work.
"""
)

raci_matrix = {
    "Requirements": {
        "Sponsor": "A",
        "Project Manager": "C",
        "Product Owner": "R",
        "End Users": "C",
        "Supplier": "I",
    },
    "Solution Design": {
        "Sponsor": "I",
        "Project Manager": "A",
        "Product Owner": "C",
        "End Users": "C",
        "Supplier": "R",
    },
    "Acceptance": {
        "Sponsor": "A",
        "Project Manager": "C",
        "Product Owner": "R",
        "End Users": "C",
        "Supplier": "I",
    },
}

for activity, assignments in raci_matrix.items():
    print(f"\n{activity}")
    for stakeholder, role in assignments.items():
        print(f"  {stakeholder:18}: {role}")


# ============================================================================
# 16. STAKEHOLDER CONFLICT
# ============================================================================

class ConflictStyle(Enum):
    """Common approaches to conflict management."""

    COLLABORATE = "Collaborate / Problem Solve"
    COMPROMISE = "Compromise"
    ACCOMMODATE = "Accommodate"
    COMPETE = "Direct / Compete"
    AVOID = "Avoid / Withdraw"


@dataclass
class Conflict:
    """Represents a stakeholder conflict."""

    conflict_id: str
    parties: Tuple[str, str]
    issue: str
    severity: int
    urgency: int
    preferred_style: ConflictStyle
    resolution: Optional[str] = None

    def priority_score(self) -> int:
        """Calculate a simple conflict priority score."""
        return self.severity * self.urgency


conflicts = [
    Conflict(
        conflict_id="CON-001",
        parties=("Product Owner", "Supplier"),
        issue="Business requirement changes may affect supplier delivery dates.",
        severity=4,
        urgency=4,
        preferred_style=ConflictStyle.COLLABORATE,
    ),
    Conflict(
        conflict_id="CON-002",
        parties=("Project Manager", "End User Representative"),
        issue="Release timing conflicts with user training capacity.",
        severity=3,
        urgency=3,
        preferred_style=ConflictStyle.COMPROMISE,
    ),
]

print_section("16. CONFLICT PRIORITIZATION")

for conflict in sorted(
    conflicts,
    key=lambda item: item.priority_score(),
    reverse=True,
):
    print(
        f"{conflict.conflict_id}: "
        f"Score={conflict.priority_score()} | "
        f"Style={conflict.preferred_style.value}"
    )
    print(f"  Issue: {conflict.issue}")


# ============================================================================
# 17. NEGOTIATION MODEL
# ============================================================================

@dataclass
class NegotiationIssue:
    """Represents one negotiable stakeholder issue."""

    issue: str
    stakeholder_position: str
    project_position: str
    shared_interest: str
    minimum_acceptable_result: str
    preferred_result: str


negotiation_issues = [
    NegotiationIssue(
        issue="Delivery date",
        stakeholder_position="Earlier deployment",
        project_position="Realistic tested deployment",
        shared_interest="Successful production adoption",
        minimum_acceptable_result="Deployment after critical testing",
        preferred_result="Agreed date with acceptance criteria",
    ),
    NegotiationIssue(
        issue="Scope",
        stakeholder_position="Include additional features",
        project_position="Protect approved baseline",
        shared_interest="Business value",
        minimum_acceptable_result="Changes follow formal change control",
        preferred_result="Prioritized roadmap for additional scope",
    ),
]

print_section("17. NEGOTIATION")

for issue in negotiation_issues:
    print(f"\nIssue: {issue.issue}")
    print(f"  Stakeholder position: {issue.stakeholder_position}")
    print(f"  Project position: {issue.project_position}")
    print(f"  Shared interest: {issue.shared_interest}")
    print(f"  Minimum acceptable result: {issue.minimum_acceptable_result}")
    print(f"  Preferred result: {issue.preferred_result}")


# ============================================================================
# 18. CHANGE RESISTANCE
# ============================================================================

@dataclass
class ChangeAssessment:
    """Assess stakeholder reaction to a proposed change."""

    stakeholder_name: str
    perceived_benefit: int
    perceived_cost: int
    perceived_risk: int
    trust: int
    change_readiness: int

    def resistance_score(self) -> float:
        """
        Calculate a simplified resistance score.

        Higher cost and risk increase resistance.
        Higher benefit, trust, and readiness reduce resistance.
        """
        numerator = (
            self.perceived_cost
            + self.perceived_risk
            + (6 - self.trust)
            + (6 - self.change_readiness)
        )

        denominator = max(1, self.perceived_benefit)

        return numerator / denominator


change_assessments = [
    ChangeAssessment(
        stakeholder_name="Vikram Rao",
        perceived_benefit=3,
        perceived_cost=4,
        perceived_risk=4,
        trust=3,
        change_readiness=2,
    ),
    ChangeAssessment(
        stakeholder_name="Neha Singh",
        perceived_benefit=5,
        perceived_cost=2,
        perceived_risk=2,
        trust=4,
        change_readiness=5,
    ),
]

print_section("18. CHANGE RESISTANCE")

for assessment in sorted(
    change_assessments,
    key=lambda item: item.resistance_score(),
    reverse=True,
):
    print(
        f"{assessment.stakeholder_name:22} "
        f"Resistance={assessment.resistance_score():.2f}"
    )


# ============================================================================
# 19. STAKEHOLDER RISK
# ============================================================================

@dataclass
class StakeholderRisk:
    """Represents a risk associated with a stakeholder relationship."""

    risk_id: str
    stakeholder_name: str
    description: str
    probability: int
    impact: int
    mitigation: str

    def score(self) -> int:
        """Risk score = probability × impact."""
        return self.probability * self.impact


stakeholder_risks = [
    StakeholderRisk(
        risk_id="SR-001",
        stakeholder_name="Compliance Authority",
        description="Required approval may be delayed.",
        probability=3,
        impact=5,
        mitigation="Submit evidence early and maintain a compliance tracker.",
    ),
    StakeholderRisk(
        risk_id="SR-002",
        stakeholder_name="SecureTech Ltd.",
        description="Supplier dependency may delay integration.",
        probability=4,
        impact=4,
        mitigation="Track supplier milestones and maintain contingency options.",
    ),
    StakeholderRisk(
        risk_id="SR-003",
        stakeholder_name="Vikram Rao",
        description="Low user adoption may reduce realized project benefits.",
        probability=3,
        impact=4,
        mitigation="Use demonstrations, training, feedback, and pilot groups.",
    ),
]

print_section("19. STAKEHOLDER RISKS")

for risk in sorted(
    stakeholder_risks,
    key=lambda item: item.score(),
    reverse=True,
):
    print(
        f"{risk.risk_id}: {risk.stakeholder_name} | "
        f"Score={risk.score()}"
    )
    print(f"  {risk.description}")
    print(f"  Mitigation: {risk.mitigation}")


# ============================================================================
# 20. ADVANCED MULTI-FACTOR PRIORITIZATION
# ============================================================================

@dataclass
class WeightedScoringModel:
    """
    Weighted stakeholder scoring model.

    Weights must sum to 1.0.
    """

    power_weight: float = 0.25
    interest_weight: float = 0.20
    impact_weight: float = 0.20
    urgency_weight: float = 0.15
    legitimacy_weight: float = 0.10
    engagement_gap_weight: float = 0.10

    def __post_init__(self) -> None:
        weights = [
            self.power_weight,
            self.interest_weight,
            self.impact_weight,
            self.urgency_weight,
            self.legitimacy_weight,
            self.engagement_gap_weight,
        ]

        if any(weight < 0 for weight in weights):
            raise ValueError("Weights cannot be negative.")

        if not math.isclose(sum(weights), 1.0, abs_tol=1e-9):
            raise ValueError("Weights must sum to 1.0.")

    def score(self, stakeholder: Stakeholder) -> float:
        """Calculate normalized stakeholder priority."""
        gap = max(0, stakeholder.engagement_gap())
        normalized_gap = min(gap, 4)

        return (
            self.power_weight * stakeholder.power
            + self.interest_weight * stakeholder.interest
            + self.impact_weight * stakeholder.impact
            + self.urgency_weight * stakeholder.urgency
            + self.legitimacy_weight * stakeholder.legitimacy
            + self.engagement_gap_weight * normalized_gap
        )


print_section("20. WEIGHTED STAKEHOLDER PRIORITIZATION")

scoring_model = WeightedScoringModel()

weighted_scores = [
    (stakeholder, scoring_model.score(stakeholder))
    for stakeholder in register.all()
]

for stakeholder, score in sorted(
    weighted_scores,
    key=lambda item: item[1],
    reverse=True,
):
    print(f"{stakeholder.name:22} Score={score:.2f}")


# ============================================================================
# 21. STAKEHOLDER NETWORK RELATIONSHIPS
# ============================================================================

print_section("21. STAKEHOLDER RELATIONSHIPS")

stakeholder_relationships = {
    "Project Sponsor": ["Project Manager", "Product Owner"],
    "Project Manager": ["Project Sponsor", "Product Owner", "Supplier"],
    "Product Owner": ["Project Manager", "End Users", "Supplier"],
    "End Users": ["Product Owner"],
    "Supplier": ["Project Manager", "Product Owner"],
}

for stakeholder, connected_to in stakeholder_relationships.items():
    print(f"{stakeholder} -> {', '.join(connected_to)}")


def stakeholder_degree(
    relationships: Dict[str, List[str]],
    stakeholder_name: str,
) -> int:
    """Return the number of directly connected stakeholder groups."""
    return len(relationships.get(stakeholder_name, []))


print("\nStakeholder network degree:")
for name in stakeholder_relationships:
    print(f"  {name:22}: {stakeholder_degree(stakeholder_relationships, name)}")


# ============================================================================
# 22. IDENTIFYING HIDDEN STAKEHOLDERS
# ============================================================================

print_section("22. IDENTIFYING POTENTIALLY MISSED STAKEHOLDERS")

identification_questions = [
    "Who funds the project?",
    "Who authorizes major decisions?",
    "Who defines business requirements?",
    "Who will use the final product?",
    "Who supplies required resources?",
    "Who can block or delay the project?",
    "Who must approve compliance?",
    "Who will maintain the delivered solution?",
    "Who is affected by project changes?",
    "Who can influence public perception?",
    "Who owns downstream operational processes?",
    "Who controls critical dependencies?",
]

for question in identification_questions:
    print(f"- {question}")


# ============================================================================
# 23. STAKEHOLDER IDENTIFICATION ALGORITHM
# ============================================================================

def identify_candidate_stakeholders(
    stakeholder_sources: Dict[str, List[str]],
) -> List[str]:
    """
    Combine stakeholder candidates from multiple identification sources.

    Duplicate names are removed while preserving first occurrence order.
    """
    result: List[str] = []
    seen = set()

    for source, names in stakeholder_sources.items():
        if not isinstance(names, list):
            raise TypeError(
                f"Stakeholder source '{source}' must contain a list."
            )

        for name in names:
            normalized = name.strip()

            if not normalized:
                continue

            key = normalized.lower()

            if key not in seen:
                seen.add(key)
                result.append(normalized)

    return result


candidate_sources = {
    "organizational_review": [
        "Project Sponsor",
        "Project Manager",
        "Finance Manager",
    ],
    "user_analysis": [
        "End Users",
        "Customer",
        "Product Owner",
    ],
    "supplier_analysis": [
        "Technology Supplier",
        "Contract Manager",
    ],
    "regulatory_analysis": [
        "Compliance Authority",
    ],
}

candidates = identify_candidate_stakeholders(candidate_sources)

print_section("23. CANDIDATE STAKEHOLDER IDENTIFICATION")

for candidate in candidates:
    print("-", candidate)


# ============================================================================
# 24. COMMUNICATION EFFECTIVENESS
# ============================================================================

@dataclass
class CommunicationMeasurement:
    """Capture stakeholder communication performance."""

    stakeholder_name: str
    messages_sent: int
    messages_acknowledged: int
    questions_received: int
    issues_escalated: int
    satisfaction_score: float

    def acknowledgement_rate(self) -> float:
        if self.messages_sent == 0:
            return 0.0

        return self.messages_acknowledged / self.messages_sent

    def escalation_rate(self) -> float:
        if self.messages_sent == 0:
            return 0.0

        return self.issues_escalated / self.messages_sent


communication_measurements = [
    CommunicationMeasurement(
        stakeholder_name="Anita Sharma",
        messages_sent=20,
        messages_acknowledged=20,
        questions_received=6,
        issues_escalated=2,
        satisfaction_score=4.5,
    ),
    CommunicationMeasurement(
        stakeholder_name="Vikram Rao",
        messages_sent=15,
        messages_acknowledged=11,
        questions_received=10,
        issues_escalated=3,
        satisfaction_score=3.4,
    ),
]

print_section("24. COMMUNICATION METRICS")

for measurement in communication_measurements:
    print(
        f"{measurement.stakeholder_name:22} "
        f"Acknowledgement={measurement.acknowledgement_rate():.1%} "
        f"Escalation={measurement.escalation_rate():.1%} "
        f"Satisfaction={measurement.satisfaction_score:.1f}/5"
    )


# ============================================================================
# 25. ENGAGEMENT INDEX
# ============================================================================

def engagement_index(stakeholder: Stakeholder) -> float:
    """
    Produce an engagement index from current engagement and alignment.

    The result is normalized to a 0-100 scale.
    """
    level_value = {
        EngagementLevel.UNAWARE: 0,
        EngagementLevel.RESISTANT: 25,
        EngagementLevel.NEUTRAL: 50,
        EngagementLevel.SUPPORTIVE: 75,
        EngagementLevel.LEADING: 100,
    }

    current = level_value[stakeholder.current_engagement]
    desired = level_value[stakeholder.desired_engagement]

    if desired == 0:
        return 100.0

    return min(100.0, (current / desired) * 100)


print_section("25. ENGAGEMENT INDEX")

for stakeholder in register.all():
    print(
        f"{stakeholder.name:22} "
        f"Engagement Index={engagement_index(stakeholder):6.1f}%"
    )


# ============================================================================
# 26. TREND ANALYSIS
# ============================================================================

def average(values: Iterable[float]) -> float:
    """Safely calculate an average."""
    values = list(values)

    if not values:
        raise ValueError("Cannot calculate average of an empty collection.")

    return statistics.mean(values)


print_section("26. ENGAGEMENT TREND")

engagement_history = {
    "Vikram Rao": [45, 50, 55, 65, 72],
    "Neha Singh": [70, 75, 80, 85, 90],
    "Compliance Authority": [40, 45, 50, 55, 60],
}

for name, values in engagement_history.items():
    trend = values[-1] - values[0]

    print(
        f"{name:22} "
        f"Initial={values[0]:3} "
        f"Current={values[-1]:3} "
        f"Change={trend:+3} "
        f"Average={average(values):.1f}"
    )


# ============================================================================
# 27. STAKEHOLDER CHANGE DETECTION
# ============================================================================

@dataclass
class StakeholderSnapshot:
    """Historical stakeholder attributes used to detect changes."""

    power: int
    interest: int
    impact: int
    urgency: int
    engagement: EngagementLevel


def compare_snapshots(
    old: StakeholderSnapshot,
    new: StakeholderSnapshot,
) -> Dict[str, object]:
    """Return important stakeholder-state changes."""
    changes: Dict[str, object] = {}

    for attribute in ("power", "interest", "impact", "urgency"):
        old_value = getattr(old, attribute)
        new_value = getattr(new, attribute)

        if old_value != new_value:
            changes[attribute] = (old_value, new_value)

    if old.engagement != new.engagement:
        changes["engagement"] = (
            old.engagement.value,
            new.engagement.value,
        )

    return changes


old_snapshot = StakeholderSnapshot(
    power=3,
    interest=3,
    impact=4,
    urgency=2,
    engagement=EngagementLevel.NEUTRAL,
)

new_snapshot = StakeholderSnapshot(
    power=5,
    interest=5,
    impact=5,
    urgency=4,
    engagement=EngagementLevel.SUPPORTIVE,
)

print_section("27. STAKEHOLDER CHANGE DETECTION")

for attribute, values in compare_snapshots(
    old_snapshot,
    new_snapshot,
).items():
    print(f"{attribute}: {values[0]} -> {values[1]}")


# ============================================================================
# 28. DECISION-MAKING WITH STAKEHOLDER INPUT
# ============================================================================

@dataclass
class Decision:
    """Represents a project decision requiring stakeholder input."""

    decision_id: str
    description: str
    options: List[str]
    decision_owner: str
    consulted_stakeholders: List[str]
    deadline: str


decisions = [
    Decision(
        decision_id="DEC-001",
        description="Select the preferred deployment approach.",
        options=["Phased", "Big Bang", "Pilot First"],
        decision_owner="Project Sponsor",
        consulted_stakeholders=[
            "Project Manager",
            "Product Owner",
            "Technology Supplier",
        ],
        deadline="2026-10-15",
    ),
    Decision(
        decision_id="DEC-002",
        description="Prioritize additional user features.",
        options=["Feature A", "Feature B", "Feature C"],
        decision_owner="Product Owner",
        consulted_stakeholders=[
            "End User Representative",
            "Project Manager",
        ],
        deadline="2026-10-20",
    ),
]

print_section("28. STAKEHOLDER DECISIONS")

for decision in decisions:
    print(f"\n{decision.decision_id}: {decision.description}")
    print(f"  Options: {', '.join(decision.options)}")
    print(f"  Owner: {decision.decision_owner}")
    print(
        f"  Consulted: {', '.join(decision.consulted_stakeholders)}"
    )
    print(f"  Deadline: {decision.deadline}")


# ============================================================================
# 29. EDGE CASES
# ============================================================================

print_section("29. EDGE CASES")

edge_cases = {
    "High power, low interest": (
        "Do not overwhelm the stakeholder with unnecessary detail. "
        "Maintain satisfaction and provide decision-relevant information."
    ),
    "Low power, high interest": (
        "Do not ignore the stakeholder merely because formal power is low. "
        "They may influence adoption, reputation, or other stakeholders."
    ),
    "High power, high interest": (
        "Requires close and continuous management because decisions can "
        "materially affect project success."
    ),
    "Conflicting stakeholders": (
        "Separate positions from underlying interests and use structured "
        "negotiation and decision rights."
    ),
    "Stakeholder changes role": (
        "Reassess power, interest, influence, expectations, communication "
        "needs, and engagement rather than copying the old classification."
    ),
    "Previously hidden stakeholder": (
        "Add the stakeholder to the register and reassess risks, "
        "requirements, communication, and governance."
    ),
    "Stakeholder has conflicting interests": (
        "Document competing objectives and establish transparent decision "
        "criteria."
    ),
}

for case, response in edge_cases.items():
    print(f"\n{case}:")
    print(f"  {response}")


# ============================================================================
# 30. COMMON MISTAKES
# ============================================================================

print_section("30. COMMON STAKEHOLDER MANAGEMENT MISTAKES")

mistakes = [
    (
        "Treating every stakeholder identically",
        "Different stakeholders require different levels and methods of engagement.",
    ),
    (
        "Confusing power with interest",
        "A stakeholder can have substantial authority but little day-to-day interest.",
    ),
    (
        "Ignoring low-power stakeholders",
        "Low formal power does not mean low influence or low project impact.",
    ),
    (
        "Failing to reassess stakeholders",
        "Stakeholder power, interest, expectations, and attitudes can change.",
    ),
    (
        "Communicating without a purpose",
        "Communication should have a defined audience, objective, message, method, and timing.",
    ),
    (
        "Avoiding difficult stakeholders",
        "Avoidance can allow conflicts and risks to become more expensive.",
    ),
    (
        "Promising everything",
        "Stakeholder expectations must be balanced against scope, schedule, cost, quality, risk, and governance.",
    ),
    (
        "Ignoring cultural and organizational context",
        "Communication and engagement methods must fit the environment.",
    ),
]

for mistake, correction in mistakes:
    print(f"\nMistake: {mistake}")
    print(f"Correction: {correction}")


# ============================================================================
# 31. TRADE-OFFS
# ============================================================================

print_section("31. STAKEHOLDER MANAGEMENT TRADE-OFFS")

tradeoffs = [
    (
        "Frequent communication",
        "Improves visibility",
        "Can consume stakeholder and project-team time",
    ),
    (
        "Highly customized communication",
        "Improves relevance",
        "Requires more preparation",
    ),
    (
        "Broad stakeholder involvement",
        "Can increase acceptance and insight",
        "Can slow decisions",
    ),
    (
        "Centralized decision-making",
        "Can improve speed and consistency",
        "Can reduce stakeholder ownership",
    ),
    (
        "Early stakeholder involvement",
        "Can identify risks and requirements sooner",
        "Requires time before execution",
    ),
]

for approach, benefit, cost in tradeoffs:
    print(f"\n{approach}")
    print(f"  Benefit: {benefit}")
    print(f"  Trade-off: {cost}")


# ============================================================================
# 32. GOVERNANCE ESCALATION
# ============================================================================

@dataclass
class EscalationRule:
    """Defines when a stakeholder issue should be escalated."""

    condition: str
    destination: str
    maximum_response_hours: int


escalation_rules = [
    EscalationRule(
        condition="Potential regulatory non-compliance",
        destination="Compliance Lead and Sponsor",
        maximum_response_hours=4,
    ),
    EscalationRule(
        condition="Critical stakeholder conflict threatens milestone",
        destination="Project Sponsor",
        maximum_response_hours=8,
    ),
    EscalationRule(
        condition="Requirement change affects approved baseline",
        destination="Change Control Authority",
        maximum_response_hours=24,
    ),
]

print_section("32. ESCALATION GOVERNANCE")

for rule in escalation_rules:
    print(
        f"- {rule.condition} -> {rule.destination} "
        f"(response within {rule.maximum_response_hours} hours)"
    )


# ============================================================================
# 33. STAKEHOLDER ENGAGEMENT STRATEGIES
# ============================================================================

def engagement_strategy(stakeholder: Stakeholder) -> List[str]:
    """
    Produce practical engagement actions based on stakeholder position.
    """
    actions: List[str] = []

    quadrant = stakeholder.power_interest_quadrant

    if quadrant == "Manage Closely":
        actions.extend(
            [
                "Involve in important decisions.",
                "Provide timely status information.",
                "Address concerns quickly.",
                "Confirm expectations explicitly.",
            ]
        )
    elif quadrant == "Keep Satisfied":
        actions.extend(
            [
                "Provide concise decision-relevant updates.",
                "Avoid unnecessary operational detail.",
                "Monitor changes in interest.",
            ]
        )
    elif quadrant == "Keep Informed":
        actions.extend(
            [
                "Provide relevant project information.",
                "Collect feedback.",
                "Monitor whether influence increases.",
            ]
        )
    else:
        actions.extend(
            [
                "Monitor for changes.",
                "Avoid excessive communication.",
                "Reassess if circumstances change.",
            ]
        )

    if stakeholder.engagement_gap() > 0:
        actions.append("Create a targeted plan to close the engagement gap.")

    return actions


print_section("33. ENGAGEMENT STRATEGIES")

for stakeholder in register.all():
    print(f"\n{stakeholder.name}:")
    for action in engagement_strategy(stakeholder):
        print(f"  - {action}")


# ============================================================================
# 34. PROJECT PHASE CHANGES
# ============================================================================

print_section("34. STAKEHOLDER IMPORTANCE ACROSS PROJECT PHASES")

phase_stakeholders = {
    "Initiation": [
        "Sponsor",
        "Business Owner",
        "Project Manager",
    ],
    "Planning": [
        "Project Manager",
        "Product Owner",
        "Functional Managers",
        "Subject Matter Experts",
    ],
    "Execution": [
        "Project Team",
        "Supplier",
        "End Users",
        "Project Manager",
    ],
    "Monitoring and Control": [
        "Project Manager",
        "Sponsor",
        "Governance Body",
        "Compliance Authority",
    ],
    "Closing": [
        "Customer",
        "Sponsor",
        "End Users",
        "Operations Team",
    ],
}

for phase, phase_stakeholders_list in phase_stakeholders.items():
    print(f"\n{phase}:")
    for stakeholder in phase_stakeholders_list:
        print(f"  - {stakeholder}")


# ============================================================================
# 35. AGILE-SPECIFIC STAKEHOLDER EXAMPLE
# ============================================================================

print_section("35. STAKEHOLDERS IN AGILE PROJECTS")

agile_stakeholder_events = {
    "Sprint Planning": [
        "Product Owner",
        "Developers",
    ],
    "Sprint Review": [
        "Product Owner",
        "Developers",
        "Customers",
        "End Users",
        "Business Stakeholders",
    ],
    "Sprint Retrospective": [
        "Scrum Team",
    ],
    "Backlog Refinement": [
        "Product Owner",
        "Developers",
        "Subject Matter Experts",
    ],
}

for event, participants in agile_stakeholder_events.items():
    print(f"\n{event}:")
    for participant in participants:
        print(f"  - {participant}")


# ============================================================================
# 36. PREDICTIVE PROJECT EXAMPLE
# ============================================================================

print_section("36. PREDICTIVE PROJECT STAKEHOLDER EXAMPLE")

predictive_activities = {
    "Requirements Baseline": [
        "Customer",
        "Business Owner",
        "Project Manager",
    ],
    "Design Approval": [
        "Technical Lead",
        "Customer",
        "Governance Authority",
    ],
    "Implementation": [
        "Project Team",
        "Supplier",
        "Project Manager",
    ],
    "Acceptance": [
        "Customer",
        "End Users",
        "Project Sponsor",
    ],
}

for activity, participants in predictive_activities.items():
    print(f"\n{activity}: {', '.join(participants)}")


# ============================================================================
# 37. SECURITY AND CONFIDENTIALITY
# ============================================================================

print_section("37. SECURITY AND CONFIDENTIALITY CONSIDERATIONS")

print(
    """
Stakeholder information can contain sensitive organizational information.

Important controls include:
- Restrict access to stakeholder registers when appropriate.
- Avoid recording unnecessary personal information.
- Protect confidential concerns and negotiation positions.
- Apply least-privilege access.
- Maintain auditability for important governance decisions.
- Avoid exposing confidential stakeholder assessments.
- Separate factual project records from subjective opinions.
- Follow applicable privacy, contractual, and organizational requirements.

A stakeholder register should support project governance without becoming
an uncontrolled repository of sensitive personal judgments.
"""
)


# ============================================================================
# 38. PERFORMANCE CONSIDERATIONS
# ============================================================================

print_section("38. PERFORMANCE CONSIDERATIONS")

print(
    """
For small projects, a list of stakeholder objects is usually sufficient.

For larger systems:
- Use dictionaries for fast lookup by stakeholder ID.
- Avoid repeatedly scanning the complete stakeholder list.
- Cache expensive scoring calculations when appropriate.
- Normalize identifiers consistently.
- Separate storage from analysis.
- Use database indexing for large stakeholder repositories.
- Avoid excessive recalculation when only one stakeholder changed.

Python dictionary lookup is typically O(1) average-case, while a linear
search through a list is O(n).

The register implemented above uses a dictionary for stakeholder lookup.
"""
)


# ============================================================================
# 39. COMPLEXITY EXAMPLE
# ============================================================================

def linear_search(
    stakeholders_list: List[Stakeholder],
    name: str,
) -> Optional[Stakeholder]:
    """Linear search through stakeholders: O(n)."""
    normalized_name = name.lower()

    for stakeholder in stakeholders_list:
        if stakeholder.name.lower() == normalized_name:
            return stakeholder

    return None


def dictionary_search(
    stakeholders_dict: Dict[str, Stakeholder],
    name: str,
) -> Optional[Stakeholder]:
    """Dictionary lookup: O(1) average-case."""
    return stakeholders_dict.get(name.lower())


stakeholder_dictionary = {
    stakeholder.name.lower(): stakeholder
    for stakeholder in register.all()
}

print_section("39. LOOKUP COMPARISON")

print(
    "Linear search result:",
    linear_search(register.all(), "Anita Sharma").name,
)

print(
    "Dictionary search result:",
    dictionary_search(stakeholder_dictionary, "Anita Sharma").name,
)


# ============================================================================
# 40. DATA QUALITY VALIDATION
# ============================================================================

def validate_stakeholder_register(
    stakeholders_list: Iterable[Stakeholder],
) -> List[str]:
    """Validate common stakeholder-register data-quality conditions."""

    errors: List[str] = []
    names = set()

    for stakeholder in stakeholders_list:
        normalized_name = stakeholder.name.strip().lower()

        if not normalized_name:
            errors.append("A stakeholder has an empty name.")

        if normalized_name in names:
            errors.append(
                f"Duplicate stakeholder: {stakeholder.name}"
            )

        names.add(normalized_name)

        if not stakeholder.role.strip():
            errors.append(
                f"{stakeholder.name}: missing role."
            )

        if not stakeholder.organization.strip():
            errors.append(
                f"{stakeholder.name}: missing organization."
            )

        if not stakeholder.communication_method.strip():
            errors.append(
                f"{stakeholder.name}: missing communication method."
            )

    return errors


print_section("40. DATA QUALITY VALIDATION")

validation_errors = validate_stakeholder_register(register.all())

if validation_errors:
    for error in validation_errors:
        print("ERROR:", error)
else:
    print("Stakeholder register passed basic data-quality validation.")


# ============================================================================
# 41. PROJECT STAKEHOLDER DASHBOARD
# ============================================================================

def stakeholder_dashboard(
    stakeholders_list: List[Stakeholder],
) -> Dict[str, object]:
    """Create aggregate stakeholder-management metrics."""

    if not stakeholders_list:
        return {
            "total": 0,
            "average_power": 0,
            "average_interest": 0,
            "high_priority": 0,
            "engagement_gaps": 0,
        }

    return {
        "total": len(stakeholders_list),
        "average_power": average(
            stakeholder.power for stakeholder in stakeholders_list
        ),
        "average_interest": average(
            stakeholder.interest for stakeholder in stakeholders_list
        ),
        "high_priority": sum(
            stakeholder.priority
            in {PriorityLevel.HIGH, PriorityLevel.CRITICAL}
            for stakeholder in stakeholders_list
        ),
        "engagement_gaps": sum(
            stakeholder.engagement_gap() > 0
            for stakeholder in stakeholders_list
        ),
    }


print_section("41. STAKEHOLDER DASHBOARD")

dashboard = stakeholder_dashboard(register.all())

for metric, value in dashboard.items():
    if isinstance(value, float):
        print(f"{metric}: {value:.2f}")
    else:
        print(f"{metric}: {value}")


# ============================================================================
# 42. STAKEHOLDER DECISION SCORE
# ============================================================================

def decision_influence_score(stakeholder: Stakeholder) -> float:
    """
    Estimate decision influence using power, legitimacy, and interest.

    This is an analytical aid rather than a universal project-management
    formula.
    """
    return (
        stakeholder.power * 0.45
        + stakeholder.legitimacy * 0.30
        + stakeholder.interest * 0.25
    )


print_section("42. DECISION INFLUENCE SCORE")

for stakeholder in sorted(
    register.all(),
    key=decision_influence_score,
    reverse=True,
):
    print(
        f"{stakeholder.name:22} "
        f"Influence={decision_influence_score(stakeholder):.2f}"
    )


# ============================================================================
# 43. SCENARIO: A STAKEHOLDER BECOMES RESISTANT
# ============================================================================

print_section("43. SCENARIO ANALYSIS: STAKEHOLDER BECOMES RESISTANT")

scenario_stakeholder = register.get("Vikram Rao")

print(
    f"Before change: {scenario_stakeholder.current_engagement.value}"
)

scenario_stakeholder.current_engagement = EngagementLevel.RESISTANT

print(
    f"After change:  {scenario_stakeholder.current_engagement.value}"
)

print("Recommended actions:")

for action in [
    "Identify the underlying reason for resistance.",
    "Separate legitimate concerns from misinformation.",
    "Assess the effect on adoption and project outcomes.",
    "Engage the stakeholder directly.",
    "Provide evidence, demonstrations, or training where appropriate.",
    "Escalate only when authority or governance requires escalation.",
]:
    print(f"  - {action}")


# ============================================================================
# 44. SCENARIO: NEW REGULATOR ENTERS THE PROJECT
# ============================================================================

print_section("44. SCENARIO ANALYSIS: NEW REGULATORY STAKEHOLDER")

new_regulator = Stakeholder(
    name="Data Protection Office",
    role="Privacy Regulator",
    organization="Regulatory Body",
    stakeholder_type=StakeholderType.EXTERNAL,
    relationship=StakeholderRelationship.PRIMARY,
    power=5,
    interest=4,
    impact=5,
    urgency=5,
    legitimacy=5,
    current_engagement=EngagementLevel.UNAWARE,
    desired_engagement=EngagementLevel.SUPPORTIVE,
    communication_frequency=CommunicationFrequency.MILESTONE,
    communication_method="Formal regulatory communication",
    expectations=["Legal compliance", "Evidence", "Data protection"],
    concerns=["Unauthorized processing", "Insufficient controls"],
)

register.add(new_regulator)

print(
    f"Added: {new_regulator.name} "
    f"with priority {new_regulator.priority.value}"
)

print(
    f"Quadrant: {new_regulator.power_interest_quadrant}"
)

print(
    f"Salience: {salience_category(new_regulator)}"
)


# ============================================================================
# 45. STAKEHOLDER REGISTER EXPORT
# ============================================================================

def stakeholder_to_dict(stakeholder: Stakeholder) -> Dict[str, object]:
    """Convert a stakeholder into a serializable dictionary."""
    return {
        "name": stakeholder.name,
        "role": stakeholder.role,
        "organization": stakeholder.organization,
        "type": stakeholder.stakeholder_type.value,
        "relationship": stakeholder.relationship.value,
        "power": stakeholder.power,
        "interest": stakeholder.interest,
        "impact": stakeholder.impact,
        "urgency": stakeholder.urgency,
        "legitimacy": stakeholder.legitimacy,
        "current_engagement": stakeholder.current_engagement.value,
        "desired_engagement": stakeholder.desired_engagement.value,
        "priority": stakeholder.priority.value,
        "quadrant": stakeholder.power_interest_quadrant,
        "communication_frequency": stakeholder.communication_frequency.value,
        "communication_method": stakeholder.communication_method,
        "expectations": stakeholder.expectations,
        "concerns": stakeholder.concerns,
    }


print_section("45. SERIALIZABLE STAKEHOLDER RECORD")

record = stakeholder_to_dict(new_regulator)

for key, value in record.items():
    print(f"{key}: {value}")


# ============================================================================
# 46. UNIT TESTS
# ============================================================================

class StakeholderTests(unittest.TestCase):
    """Tests for stakeholder-management calculations."""

    def setUp(self) -> None:
        self.stakeholder = Stakeholder(
            name="Test Stakeholder",
            role="Tester",
            organization="Test Organization",
            stakeholder_type=StakeholderType.INTERNAL,
            relationship=StakeholderRelationship.PRIMARY,
            power=5,
            interest=5,
            impact=5,
            urgency=5,
            legitimacy=5,
            current_engagement=EngagementLevel.NEUTRAL,
            desired_engagement=EngagementLevel.LEADING,
            communication_frequency=CommunicationFrequency.WEEKLY,
            communication_method="Meeting",
        )

    def test_power_interest_score(self) -> None:
        self.assertEqual(
            self.stakeholder.power_interest_score,
            25,
        )

    def test_critical_priority(self) -> None:
        self.assertEqual(
            self.stakeholder.priority,
            PriorityLevel.CRITICAL,
        )

    def test_manage_closely_quadrant(self) -> None:
        self.assertEqual(
            self.stakeholder.power_interest_quadrant,
            "Manage Closely",
        )

    def test_salience_score(self) -> None:
        self.assertEqual(
            self.stakeholder.salience_score,
            125,
        )

    def test_engagement_gap(self) -> None:
        self.assertEqual(
            self.stakeholder.engagement_gap(),
            2,
        )

    def test_invalid_score(self) -> None:
        with self.assertRaises(ValueError):
            Stakeholder(
                name="Invalid",
                role="Tester",
                organization="Test",
                stakeholder_type=StakeholderType.INTERNAL,
                relationship=StakeholderRelationship.PRIMARY,
                power=6,
                interest=5,
                impact=5,
                urgency=5,
                legitimacy=5,
                current_engagement=EngagementLevel.NEUTRAL,
                desired_engagement=EngagementLevel.LEADING,
                communication_frequency=CommunicationFrequency.WEEKLY,
                communication_method="Meeting",
            )

    def test_register_duplicate(self) -> None:
        local_register = StakeholderRegister()
        local_register.add(self.stakeholder)

        with self.assertRaises(ValueError):
            local_register.add(self.stakeholder)


def run_tests() -> None:
    """Run unit tests without requiring an external testing package."""
    print_section("46. RUNNING UNIT TESTS")

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        StakeholderTests
    )

    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if not result.wasSuccessful():
        raise SystemExit("One or more tests failed.")


# ============================================================================
# 47. ADVANCED STAKEHOLDER PORTFOLIO ANALYSIS
# ============================================================================

def portfolio_analysis(
    stakeholders_list: List[Stakeholder],
) -> Dict[str, object]:
    """
    Analyze the overall stakeholder portfolio.

    This identifies concentrations of high power, high interest, and
    engagement gaps.
    """
    return {
        "high_power_count": sum(
            stakeholder.power >= 4
            for stakeholder in stakeholders_list
        ),
        "high_interest_count": sum(
            stakeholder.interest >= 4
            for stakeholder in stakeholders_list
        ),
        "critical_count": sum(
            stakeholder.priority == PriorityLevel.CRITICAL
            for stakeholder in stakeholders_list
        ),
        "unclosed_engagement_gaps": sum(
            stakeholder.engagement_gap() > 0
            for stakeholder in stakeholders_list
        ),
        "definitive_salience_count": sum(
            salience_category(stakeholder) == "Definitive"
            for stakeholder in stakeholders_list
        ),
    }


print_section("47. ADVANCED PORTFOLIO ANALYSIS")

portfolio = portfolio_analysis(register.all())

for metric, value in portfolio.items():
    print(f"{metric}: {value}")


# ============================================================================
# 48. PRACTICAL PROJECT WORKFLOW
# ============================================================================

print_section("48. PRACTICAL STAKEHOLDER MANAGEMENT WORKFLOW")

workflow = [
    "1. Identify people, groups, and organizations connected to the project.",
    "2. Record stakeholder roles, organizations, interests, and expectations.",
    "3. Analyze power, interest, influence, impact, urgency, and legitimacy.",
    "4. Map stakeholders using an appropriate analytical model.",
    "5. Determine current and desired engagement.",
    "6. Identify engagement gaps and stakeholder risks.",
    "7. Design communication and engagement strategies.",
    "8. Establish responsibility and decision relationships.",
    "9. Address conflicts and negotiate competing interests.",
    "10. Monitor stakeholder sentiment and project impact.",
    "11. Reassess stakeholder classifications when conditions change.",
    "12. Maintain governance records and protect sensitive information.",
]

for step in workflow:
    print(step)


# ============================================================================
# 49. END-TO-END PROJECT SCENARIO
# ============================================================================

print_section("49. END-TO-END STAKEHOLDER ANALYSIS")

scenario = register.get("Anita Sharma")

print(f"Stakeholder: {scenario.name}")
print(f"Role: {scenario.role}")
print(f"Power: {scenario.power}/5")
print(f"Interest: {scenario.interest}/5")
print(f"Impact: {scenario.impact}/5")
print(f"Urgency: {scenario.urgency}/5")
print(f"Legitimacy: {scenario.legitimacy}/5")
print(f"Priority: {scenario.priority.value}")
print(f"Quadrant: {scenario.power_interest_quadrant}")
print(f"Salience: {salience_category(scenario)}")
print(f"Salience Score: {scenario.salience_score}")
print(f"Engagement Gap: {scenario.engagement_gap()}")
print(f"Engagement Index: {engagement_index(scenario):.1f}%")

print("\nEngagement strategy:")
for action in engagement_strategy(scenario):
    print(f"  - {action}")

print("\nExpectations:")
for expectation in scenario.expectations:
    print(f"  - {expectation}")

print("\nConcerns:")
for concern in scenario.concerns:
    print(f"  - {concern}")


# ============================================================================
# 50. KEY DISTINCTIONS
# ============================================================================

print_section("50. IMPORTANT CONCEPTUAL DISTINCTIONS")

distinctions = {
    "Stakeholder vs customer": (
        "A customer may be a stakeholder, but not every stakeholder is a customer."
    ),
    "Stakeholder vs sponsor": (
        "A sponsor is a specific project role; stakeholder is the broader category."
    ),
    "Power vs interest": (
        "Power describes influence capacity; interest describes concern or attention."
    ),
    "Influence vs impact": (
        "Influence concerns the ability to affect the project; impact concerns how the project affects the stakeholder."
    ),
    "Responsible vs accountable": (
        "Responsible means performing the work; accountable means owning the outcome."
    ),
    "Communication vs engagement": (
        "Communication transfers information; engagement involves relationship, participation, alignment, and response."
    ),
    "Current vs desired engagement": (
        "Current engagement describes the stakeholder's present state; desired engagement describes the target relationship."
    ),
    "Risk vs issue": (
        "A risk is uncertain; an issue is an existing condition requiring management."
    ),
}

for concept, distinction in distinctions.items():
    print(f"\n{concept}:")
    print(f"  {distinction}")


# ============================================================================
# 51. RUN TESTS
# ============================================================================

run_tests()


# ============================================================================
# 52. FINAL EDUCATIONAL CHECKLIST
# ============================================================================

print_section("52. PROJECT STAKEHOLDER CHECKLIST")

checklist = [
    "Stakeholders have been identified.",
    "Stakeholder roles and relationships are documented.",
    "Internal and external stakeholders have been distinguished.",
    "Primary and secondary stakeholders have been considered.",
    "Power and interest have been assessed.",
    "Stakeholder impact has been considered.",
    "Urgency and legitimacy have been considered.",
    "Stakeholder priorities have been established.",
    "Current and desired engagement have been assessed.",
    "Engagement gaps have been identified.",
    "Communication methods and frequencies have been defined.",
    "Stakeholder expectations have been documented.",
    "Stakeholder concerns and risks have been identified.",
    "Decision rights and responsibilities have been clarified.",
    "Conflicts have been assessed.",
    "Change resistance has been considered.",
    "Stakeholder relationships are monitored over time.",
    "The register is maintained as project conditions change.",
    "Sensitive stakeholder information is protected.",
    "Stakeholder analysis is connected to project governance.",
]

for index, item in enumerate(checklist, start=1):
    print(f"{index:02}. {item}")


print_section("END OF PROJECT STAKEHOLDER STUDY SCRIPT")

print(
    """
The script has demonstrated stakeholder identification, classification,
analysis, prioritization, engagement, communication, governance, conflict,
risk, change, measurement, validation, performance considerations, and
advanced analytical techniques through executable Python examples.
"""
)
