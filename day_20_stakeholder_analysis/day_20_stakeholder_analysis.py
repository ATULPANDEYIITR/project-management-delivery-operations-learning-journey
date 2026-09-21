"""
Stakeholder Analysis
====================

A comprehensive standalone study and implementation of stakeholder analysis.

This script teaches and demonstrates:
- Stakeholder identification
- Stakeholder definitions and terminology
- Stakeholder interests, influence, power, impact, urgency, legitimacy
- Internal and external stakeholders
- Primary and secondary stakeholders
- Stakeholder mapping
- Power-interest grids
- Influence-impact analysis
- Stakeholder salience
- Scoring and prioritization
- Engagement strategies
- Communication planning
- Conflict analysis
- Dependency analysis
- Risk-oriented stakeholder analysis
- Stakeholder registers
- Stakeholder prioritization algorithms
- Sensitivity analysis
- Edge cases and validation
- Practical project-management scenarios
- Reporting and visualization using text
- Testing and quality checks

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import math
import statistics
import textwrap


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

class EngagementLevel(Enum):
    """Typical stakeholder engagement states."""
    UNAWARE = "Unaware"
    RESISTANT = "Resistant"
    NEUTRAL = "Neutral"
    SUPPORTIVE = "Supportive"
    LEADING = "Leading"


class StakeholderCategory(Enum):
    """Broad stakeholder classifications."""
    INTERNAL = "Internal"
    EXTERNAL = "External"


class StakeholderType(Enum):
    """More specific stakeholder classifications."""
    PRIMARY = "Primary"
    SECONDARY = "Secondary"


@dataclass
class Stakeholder:
    """
    Represents one stakeholder.

    The numerical fields use a 1-10 scale:
    - interest: how strongly the stakeholder cares about the initiative
    - influence: ability to affect decisions or outcomes
    - impact: degree to which the initiative affects the stakeholder
    - urgency: time sensitivity of stakeholder claims or concerns
    - legitimacy: perceived validity of the stakeholder's relationship
                  to the initiative
    """
    name: str
    role: str
    category: StakeholderCategory
    stakeholder_type: StakeholderType
    interest: float
    influence: float
    impact: float
    urgency: float
    legitimacy: float
    current_engagement: EngagementLevel
    desired_engagement: EngagementLevel
    interests: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    communication_preference: str = "Email"
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Reject invalid stakeholder records."""
        if not self.name.strip():
            raise ValueError("Stakeholder name cannot be empty.")

        for field_name in (
            "interest",
            "influence",
            "impact",
            "urgency",
            "legitimacy",
        ):
            value = getattr(self, field_name)
            if not 1 <= value <= 10:
                raise ValueError(
                    f"{field_name} must be between 1 and 10; received {value}."
                )

    @property
    def power_interest_quadrant(self) -> str:
        """
        Classify a stakeholder using a classic power-interest matrix.

        High influence + high interest:
            Manage closely

        High influence + low interest:
            Keep satisfied

        Low influence + high interest:
            Keep informed

        Low influence + low interest:
            Monitor
        """
        high_power = self.influence >= 6
        high_interest = self.interest >= 6

        if high_power and high_interest:
            return "Manage closely"
        if high_power and not high_interest:
            return "Keep satisfied"
        if not high_power and high_interest:
            return "Keep informed"
        return "Monitor"

    @property
    def influence_impact_quadrant(self) -> str:
        """Classify stakeholders using influence and impact."""
        high_influence = self.influence >= 6
        high_impact = self.impact >= 6

        if high_influence and high_impact:
            return "High influence / High impact"
        if high_influence:
            return "High influence / Low impact"
        if high_impact:
            return "Low influence / High impact"
        return "Low influence / Low impact"

    @property
    def salience_score(self) -> float:
        """
        Calculate a simplified stakeholder salience score.

        Salience is often discussed through:
        - power
        - legitimacy
        - urgency

        This implementation uses a normalized multiplicative model.
        The multiplication makes a stakeholder with one extremely weak
        dimension less likely to receive the same score as one strong
        across all dimensions.
        """
        return (
            self.influence
            * self.legitimacy
            * self.urgency
        ) / 10.0

    @property
    def priority_score(self) -> float:
        """
        Calculate a practical project-priority score.

        This is not a universal industry formula. It is a transparent
        decision-support model:

        30% influence
        25% interest
        20% impact
        15% urgency
        10% legitimacy
        """
        return (
            self.influence * 0.30
            + self.interest * 0.25
            + self.impact * 0.20
            + self.urgency * 0.15
            + self.legitimacy * 0.10
        )

    @property
    def engagement_gap(self) -> int:
        """Measure distance between current and desired engagement."""
        order = {
            EngagementLevel.UNAWARE: 0,
            EngagementLevel.RESISTANT: 1,
            EngagementLevel.NEUTRAL: 2,
            EngagementLevel.SUPPORTIVE: 3,
            EngagementLevel.LEADING: 4,
        }
        return order[self.desired_engagement] - order[self.current_engagement]

    def recommended_strategy(self) -> str:
        """Generate an engagement strategy from stakeholder characteristics."""
        quadrant = self.power_interest_quadrant

        if quadrant == "Manage closely":
            if self.current_engagement == EngagementLevel.RESISTANT:
                return (
                    "Address concerns directly, involve the stakeholder in "
                    "decisions, and establish frequent two-way communication."
                )
            return (
                "Involve in key decisions, provide frequent updates, "
                "and actively manage expectations."
            )

        if quadrant == "Keep satisfied":
            return (
                "Provide decision-relevant information, prevent surprises, "
                "and avoid unnecessary communication overload."
            )

        if quadrant == "Keep informed":
            return (
                "Provide regular transparent updates, explain impacts, "
                "and provide channels for feedback."
            )

        return (
            "Monitor for changes in influence, interest, or project impact "
            "and communicate when relevant."
        )


# ---------------------------------------------------------------------------
# 2. STAKEHOLDER REGISTER
# ---------------------------------------------------------------------------

class StakeholderRegister:
    """
    Central repository for stakeholder records.

    A stakeholder register is useful because identification alone is not
    enough. Teams need a structured way to record relationships,
    expectations, concerns, influence, and engagement requirements.
    """

    def __init__(self) -> None:
        self._stakeholders: Dict[str, Stakeholder] = {}

    def add(self, stakeholder: Stakeholder) -> None:
        key = stakeholder.name.strip().lower()

        if key in self._stakeholders:
            raise ValueError(
                f"Stakeholder '{stakeholder.name}' already exists."
            )

        self._stakeholders[key] = stakeholder

    def update(self, stakeholder: Stakeholder) -> None:
        key = stakeholder.name.strip().lower()

        if key not in self._stakeholders:
            raise KeyError(
                f"Stakeholder '{stakeholder.name}' does not exist."
            )

        self._stakeholders[key] = stakeholder

    def remove(self, name: str) -> None:
        key = name.strip().lower()

        if key not in self._stakeholders:
            raise KeyError(f"Stakeholder '{name}' does not exist.")

        del self._stakeholders[key]

    def get(self, name: str) -> Stakeholder:
        key = name.strip().lower()

        if key not in self._stakeholders:
            raise KeyError(f"Stakeholder '{name}' does not exist.")

        return self._stakeholders[key]

    def all(self) -> List[Stakeholder]:
        return list(self._stakeholders.values())

    def ranked_by_priority(self) -> List[Stakeholder]:
        return sorted(
            self.all(),
            key=lambda stakeholder: stakeholder.priority_score,
            reverse=True,
        )

    def by_quadrant(self, quadrant: str) -> List[Stakeholder]:
        return [
            stakeholder
            for stakeholder in self.all()
            if stakeholder.power_interest_quadrant == quadrant
        ]

    def __len__(self) -> int:
        return len(self._stakeholders)


# ---------------------------------------------------------------------------
# 3. VALIDATION FUNCTIONS
# ---------------------------------------------------------------------------

def validate_scale(value: float, minimum: float = 1, maximum: float = 10) -> None:
    """Validate a rating used by the analysis."""
    if not minimum <= value <= maximum:
        raise ValueError(
            f"Rating must be between {minimum} and {maximum}; got {value}."
        )


def safe_percentage(part: float, total: float) -> float:
    """
    Convert part/total into a percentage.

    A zero denominator is handled explicitly rather than causing
    ZeroDivisionError.
    """
    if total == 0:
        return 0.0
    return part / total * 100


# ---------------------------------------------------------------------------
# 4. BASIC STAKEHOLDER IDENTIFICATION
# ---------------------------------------------------------------------------

def identify_stakeholders_from_roles(
    roles: Sequence[str],
) -> List[str]:
    """
    Convert an initial list of project roles into a clean list.

    This demonstrates that stakeholder analysis begins before scoring.
    Identification is a discovery activity, not merely a mathematical task.
    """
    cleaned = []
    seen = set()

    for role in roles:
        normalized = role.strip()

        if not normalized:
            continue

        key = normalized.casefold()

        if key not in seen:
            cleaned.append(normalized)
            seen.add(key)

    return cleaned


# ---------------------------------------------------------------------------
# 5. MATRIX DISPLAY
# ---------------------------------------------------------------------------

def print_power_interest_matrix(register: StakeholderRegister) -> None:
    """
    Display a text representation of the power-interest matrix.

    A matrix is a conceptual tool:
        High influence, high interest -> Manage closely
        High influence, low interest  -> Keep satisfied
        Low influence, high interest  -> Keep informed
        Low influence, low interest   -> Monitor
    """
    quadrants = {
        "Manage closely": [],
        "Keep satisfied": [],
        "Keep informed": [],
        "Monitor": [],
    }

    for stakeholder in register.all():
        quadrants[stakeholder.power_interest_quadrant].append(
            stakeholder.name
        )

    print("\nPOWER-INTEREST MATRIX")
    print("=" * 72)
    print(f"{'Quadrant':<20} | Stakeholders")
    print("-" * 72)

    for quadrant, names in quadrants.items():
        print(f"{quadrant:<20} | {', '.join(names) or 'None'}")


# ---------------------------------------------------------------------------
# 6. STAKEHOLDER REPORTING
# ---------------------------------------------------------------------------

def print_stakeholder_report(stakeholder: Stakeholder) -> None:
    """Print a detailed analysis for one stakeholder."""
    print("\n" + "=" * 72)
    print(f"STAKEHOLDER: {stakeholder.name}")
    print("=" * 72)
    print(f"Role:                 {stakeholder.role}")
    print(f"Category:             {stakeholder.category.value}")
    print(f"Type:                 {stakeholder.stakeholder_type.value}")
    print(f"Interest:             {stakeholder.interest:.1f}/10")
    print(f"Influence:            {stakeholder.influence:.1f}/10")
    print(f"Impact:               {stakeholder.impact:.1f}/10")
    print(f"Urgency:              {stakeholder.urgency:.1f}/10")
    print(f"Legitimacy:           {stakeholder.legitimacy:.1f}/10")
    print(f"Priority score:       {stakeholder.priority_score:.2f}/10")
    print(f"Salience score:       {stakeholder.salience_score:.2f}")
    print(f"Power-interest area:  {stakeholder.power_interest_quadrant}")
    print(f"Influence-impact:     {stakeholder.influence_impact_quadrant}")
    print(f"Current engagement:   {stakeholder.current_engagement.value}")
    print(f"Desired engagement:   {stakeholder.desired_engagement.value}")
    print(f"Engagement gap:       {stakeholder.engagement_gap:+d}")
    print(f"Communication:        {stakeholder.communication_preference}")
    print(f"Interests:            {', '.join(stakeholder.interests)}")
    print(f"Concerns:             {', '.join(stakeholder.concerns)}")
    print(f"Dependencies:         {', '.join(stakeholder.dependencies) or 'None'}")
    print(f"Recommended strategy: {stakeholder.recommended_strategy()}")


def print_priority_ranking(register: StakeholderRegister) -> None:
    """Display stakeholders ranked by the transparent priority model."""
    print("\nPRIORITY ANALYSIS")
    print("=" * 72)
    print(
        f"{'Rank':<5} {'Stakeholder':<24} "
        f"{'Influence':<11} {'Interest':<10} {'Priority':<10}"
    )
    print("-" * 72)

    for index, stakeholder in enumerate(register.ranked_by_priority(), 1):
        print(
            f"{index:<5} "
            f"{stakeholder.name:<24} "
            f"{stakeholder.influence:<11.1f} "
            f"{stakeholder.interest:<10.1f} "
            f"{stakeholder.priority_score:<10.2f}"
        )


# ---------------------------------------------------------------------------
# 7. ENGAGEMENT PLANNING
# ---------------------------------------------------------------------------

@dataclass
class CommunicationPlan:
    """Represents a communication strategy for a stakeholder."""
    stakeholder_name: str
    objective: str
    channel: str
    frequency: str
    owner: str
    message_focus: str

    def validate(self) -> None:
        required = {
            "stakeholder_name": self.stakeholder_name,
            "objective": self.objective,
            "channel": self.channel,
            "frequency": self.frequency,
            "owner": self.owner,
            "message_focus": self.message_focus,
        }

        for field_name, value in required.items():
            if not value.strip():
                raise ValueError(
                    f"Communication plan field '{field_name}' cannot be empty."
                )


def build_communication_plan(
    stakeholder: Stakeholder,
    owner: str = "Project Manager",
) -> CommunicationPlan:
    """Create a communication plan based on stakeholder characteristics."""
    quadrant = stakeholder.power_interest_quadrant

    if quadrant == "Manage closely":
        frequency = "Weekly or more frequently during critical decisions"
        channel = "Meeting + written decision record"
        objective = "Maintain alignment and enable rapid decision-making"
    elif quadrant == "Keep satisfied":
        frequency = "Biweekly or at major decision points"
        channel = "Executive update"
        objective = "Maintain confidence and prevent unexpected escalation"
    elif quadrant == "Keep informed":
        frequency = "Weekly or biweekly"
        channel = "Newsletter / dashboard / town hall"
        objective = "Maintain transparency and gather feedback"
    else:
        frequency = "Monthly or milestone-based"
        channel = "Targeted email"
        objective = "Maintain awareness without unnecessary communication"

    plan = CommunicationPlan(
        stakeholder_name=stakeholder.name,
        objective=objective,
        channel=channel,
        frequency=frequency,
        owner=owner,
        message_focus=(
            "Project progress, stakeholder-relevant impacts, "
            "open concerns, decisions, and required actions."
        ),
    )

    plan.validate()
    return plan


# ---------------------------------------------------------------------------
# 8. CONFLICT AND INTEREST ANALYSIS
# ---------------------------------------------------------------------------

@dataclass
class StakeholderConflict:
    """Models a conflict between two stakeholder interests."""
    stakeholder_a: str
    stakeholder_b: str
    topic: str
    severity: int
    description: str

    def __post_init__(self) -> None:
        if not 1 <= self.severity <= 10:
            raise ValueError("Conflict severity must be between 1 and 10.")


def conflict_priority(
    conflict: StakeholderConflict,
    stakeholder_a: Stakeholder,
    stakeholder_b: Stakeholder,
) -> float:
    """
    Estimate conflict-management priority.

    Higher severity combined with high influence means a conflict
    may have a larger effect on the project.
    """
    average_influence = (
        stakeholder_a.influence + stakeholder_b.influence
    ) / 2

    return conflict.severity * average_influence / 10


# ---------------------------------------------------------------------------
# 9. DEPENDENCY ANALYSIS
# ---------------------------------------------------------------------------

def build_dependency_graph(
    register: StakeholderRegister,
) -> Dict[str, List[str]]:
    """
    Build a simple directed stakeholder dependency graph.

    If stakeholder A depends on stakeholder B, B appears as a dependency
    of A. This can reveal bottlenecks and communication dependencies.
    """
    return {
        stakeholder.name: stakeholder.dependencies.copy()
        for stakeholder in register.all()
    }


def find_dependency_bottlenecks(
    register: StakeholderRegister,
) -> List[Tuple[str, int]]:
    """
    Find stakeholders referenced by many other stakeholders.

    A highly referenced stakeholder may be an operational bottleneck.
    """
    counts: Dict[str, int] = {}

    for stakeholder in register.all():
        for dependency in stakeholder.dependencies:
            counts[dependency] = counts.get(dependency, 0) + 1

    return sorted(
        counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )


# ---------------------------------------------------------------------------
# 10. SENSITIVITY ANALYSIS
# ---------------------------------------------------------------------------

def calculate_weighted_score(
    stakeholder: Stakeholder,
    weights: Dict[str, float],
) -> float:
    """
    Calculate a score using user-supplied weights.

    Weight totals are required to equal 1.0 within a small floating-point
    tolerance.
    """
    required_fields = {
        "interest",
        "influence",
        "impact",
        "urgency",
        "legitimacy",
    }

    if set(weights) != required_fields:
        raise ValueError(
            f"Weights must contain exactly: {sorted(required_fields)}"
        )

    if not math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9):
        raise ValueError("Weights must sum to 1.0.")

    return sum(
        getattr(stakeholder, field_name) * weight
        for field_name, weight in weights.items()
    )


def sensitivity_analysis(
    stakeholder: Stakeholder,
    scenarios: Dict[str, Dict[str, float]],
) -> List[Tuple[str, float]]:
    """Calculate stakeholder scores under multiple weighting scenarios."""
    results = []

    for scenario_name, weights in scenarios.items():
        score = calculate_weighted_score(stakeholder, weights)
        results.append((scenario_name, score))

    return results


# ---------------------------------------------------------------------------
# 11. STAKEHOLDER SEGMENTATION
# ---------------------------------------------------------------------------

def segment_by_influence(
    stakeholders: Iterable[Stakeholder],
) -> Dict[str, List[str]]:
    """
    Divide stakeholders into three influence levels.

    This is intentionally different from the four-quadrant matrix:
    segmentation and mapping answer different questions.
    """
    result = {
        "Low": [],
        "Medium": [],
        "High": [],
    }

    for stakeholder in stakeholders:
        if stakeholder.influence < 4:
            level = "Low"
        elif stakeholder.influence < 7:
            level = "Medium"
        else:
            level = "High"

        result[level].append(stakeholder.name)

    return result


# ---------------------------------------------------------------------------
# 12. QUALITY CHECKS
# ---------------------------------------------------------------------------

def check_register_quality(register: StakeholderRegister) -> List[str]:
    """
    Detect common stakeholder-analysis weaknesses.

    The function does not claim that every warning is an error.
    Some are prompts for human review.
    """
    warnings: List[str] = []

    if len(register) == 0:
        warnings.append("The stakeholder register is empty.")
        return warnings

    names = [stakeholder.name.casefold() for stakeholder in register.all()]

    if len(names) != len(set(names)):
        warnings.append("Duplicate stakeholder names were detected.")

    for stakeholder in register.all():
        if stakeholder.engagement_gap > 0:
            warnings.append(
                f"{stakeholder.name} is below the desired engagement level."
            )

        if stakeholder.current_engagement == EngagementLevel.RESISTANT:
            warnings.append(
                f"{stakeholder.name} is currently resistant and requires "
                "active engagement management."
            )

        if stakeholder.influence >= 8 and stakeholder.interest <= 3:
            warnings.append(
                f"{stakeholder.name} has high influence but low interest; "
                "loss of attention could create project risk."
            )

        if stakeholder.urgency >= 8 and stakeholder.engagement_gap > 0:
            warnings.append(
                f"{stakeholder.name} has high urgency and an engagement gap."
            )

    return warnings


# ---------------------------------------------------------------------------
# 13. STATISTICAL ANALYSIS OF THE REGISTER
# ---------------------------------------------------------------------------

def describe_register(register: StakeholderRegister) -> None:
    """Calculate descriptive statistics for the stakeholder population."""
    stakeholders = register.all()

    if not stakeholders:
        print("\nNo stakeholder data available.")
        return

    influence_values = [s.influence for s in stakeholders]
    interest_values = [s.interest for s in stakeholders]
    impact_values = [s.impact for s in stakeholders]

    print("\nREGISTER STATISTICS")
    print("=" * 72)
    print(f"Stakeholder count:       {len(stakeholders)}")
    print(
        f"Average influence:       "
        f"{statistics.mean(influence_values):.2f}"
    )
    print(
        f"Average interest:        "
        f"{statistics.mean(interest_values):.2f}"
    )
    print(
        f"Average impact:          "
        f"{statistics.mean(impact_values):.2f}"
    )

    if len(stakeholders) >= 2:
        print(
            f"Influence median:        "
            f"{statistics.median(influence_values):.2f}"
        )
        print(
            f"Interest median:         "
            f"{statistics.median(interest_values):.2f}"
        )


# ---------------------------------------------------------------------------
# 14. REALISTIC PROJECT DATA
# ---------------------------------------------------------------------------

def create_sample_register() -> StakeholderRegister:
    """
    Create a realistic digital-transformation project stakeholder register.

    Scenario:
        A large organization is implementing a digital service platform.

    The values are illustrative rather than universal measurements.
    """
    register = StakeholderRegister()

    stakeholders = [
        Stakeholder(
            name="Executive Sponsor",
            role="Program sponsor",
            category=StakeholderCategory.INTERNAL,
            stakeholder_type=StakeholderType.PRIMARY,
            interest=9,
            influence=10,
            impact=8,
            urgency=8,
            legitimacy=10,
            current_engagement=EngagementLevel.SUPPORTIVE,
            desired_engagement=EngagementLevel.LEADING,
            interests=["Strategic outcomes", "Budget control", "Benefits"],
            concerns=["Schedule", "Return on investment"],
            communication_preference="Executive meeting",
        ),
        Stakeholder(
            name="Project Manager",
            role="Delivery lead",
            category=StakeholderCategory.INTERNAL,
            stakeholder_type=StakeholderType.PRIMARY,
            interest=10,
            influence=9,
            impact=10,
            urgency=9,
            legitimacy=10,
            current_engagement=EngagementLevel.LEADING,
            desired_engagement=EngagementLevel.LEADING,
            interests=["Delivery", "Scope", "Quality"],
            concerns=["Dependencies", "Resources", "Schedule"],
            communication_preference="Project dashboard",
        ),
        Stakeholder(
            name="Finance Department",
            role="Budget and financial control",
            category=StakeholderCategory.INTERNAL,
            stakeholder_type=StakeholderType.PRIMARY,
            interest=7,
            influence=8,
            impact=6,
            urgency=6,
            legitimacy=9,
            current_engagement=EngagementLevel.NEUTRAL,
            desired_engagement=EngagementLevel.SUPPORTIVE,
            interests=["Cost control", "Forecast accuracy"],
            concerns=["Budget overruns", "Unplanned costs"],
            communication_preference="Financial review",
        ),
        Stakeholder(
            name="IT Operations",
            role="Platform operations",
            category=StakeholderCategory.INTERNAL,
            stakeholder_type=StakeholderType.PRIMARY,
            interest=9,
            influence=8,
            impact=9,
            urgency=8,
            legitimacy=10,
            current_engagement=EngagementLevel.SUPPORTIVE,
            desired_engagement=EngagementLevel.LEADING,
            interests=["Reliability", "Maintainability", "Security"],
            concerns=["Operational load", "Integration"],
            communication_preference="Technical workshop",
        ),
        Stakeholder(
            name="Employees",
            role="Internal users",
            category=StakeholderCategory.INTERNAL,
            stakeholder_type=StakeholderType.PRIMARY,
            interest=8,
            influence=5,
            impact=9,
            urgency=6,
            legitimacy=10,
            current_engagement=EngagementLevel.NEUTRAL,
            desired_engagement=EngagementLevel.SUPPORTIVE,
            interests=["Usability", "Training", "Productivity"],
            concerns=["Learning curve", "Workflow changes"],
            communication_preference="Town hall",
        ),
        Stakeholder(
            name="Customers",
            role="External service users",
            category=StakeholderCategory.EXTERNAL,
            stakeholder_type=StakeholderType.PRIMARY,
            interest=8,
            influence=6,
            impact=9,
            urgency=7,
            legitimacy=10,
            current_engagement=EngagementLevel.NEUTRAL,
            desired_engagement=EngagementLevel.SUPPORTIVE,
            interests=["Service quality", "Availability"],
            concerns=["Privacy", "Usability"],
            communication_preference="Survey / support channel",
        ),
        Stakeholder(
            name="Regulator",
            role="Regulatory oversight",
            category=StakeholderCategory.EXTERNAL,
            stakeholder_type=StakeholderType.SECONDARY,
            interest=6,
            influence=9,
            impact=5,
            urgency=8,
            legitimacy=10,
            current_engagement=EngagementLevel.NEUTRAL,
            desired_engagement=EngagementLevel.SUPPORTIVE,
            interests=["Compliance", "Consumer protection"],
            concerns=["Non-compliance", "Reporting"],
            communication_preference="Formal submission",
        ),
        Stakeholder(
            name="External Vendor",
            role="Technology supplier",
            category=StakeholderCategory.EXTERNAL,
            stakeholder_type=StakeholderType.PRIMARY,
            interest=8,
            influence=7,
            impact=8,
            urgency=7,
            legitimacy=8,
            current_engagement=EngagementLevel.SUPPORTIVE,
            desired_engagement=EngagementLevel.SUPPORTIVE,
            interests=["Contract delivery", "Service continuity"],
            concerns=["Scope changes", "Payment"],
            communication_preference="Vendor meeting",
            dependencies=["Project Manager"],
        ),
        Stakeholder(
            name="Legal Department",
            role="Legal and contractual review",
            category=StakeholderCategory.INTERNAL,
            stakeholder_type=StakeholderType.SECONDARY,
            interest=5,
            influence=7,
            impact=5,
            urgency=7,
            legitimacy=10,
            current_engagement=EngagementLevel.NEUTRAL,
            desired_engagement=EngagementLevel.SUPPORTIVE,
            interests=["Contract validity", "Privacy"],
            concerns=["Liability", "Regulatory exposure"],
            communication_preference="Legal review",
        ),
        Stakeholder(
            name="Community Group",
            role="External community representative",
            category=StakeholderCategory.EXTERNAL,
            stakeholder_type=StakeholderType.SECONDARY,
            interest=6,
            influence=3,
            impact=7,
            urgency=5,
            legitimacy=7,
            current_engagement=EngagementLevel.UNAWARE,
            desired_engagement=EngagementLevel.NEUTRAL,
            interests=["Accessibility", "Public impact"],
            concerns=["Digital exclusion"],
            communication_preference="Public consultation",
        ),
    ]

    # Add relationships after objects have been defined.
    stakeholders[1].dependencies = ["Executive Sponsor", "IT Operations"]
    stakeholders[2].dependencies = ["Project Manager"]
    stakeholders[3].dependencies = ["Project Manager", "External Vendor"]
    stakeholders[4].dependencies = ["Project Manager", "IT Operations"]
    stakeholders[5].dependencies = ["IT Operations"]
    stakeholders[6].dependencies = ["Legal Department"]
    stakeholders[8].dependencies = ["Project Manager"]

    for stakeholder in stakeholders:
        register.add(stakeholder)

    return register


# ---------------------------------------------------------------------------
# 15. CASE STUDY: DIGITAL TRANSFORMATION
# ---------------------------------------------------------------------------

def run_case_study() -> None:
    """Run the complete stakeholder-analysis demonstration."""
    print("=" * 72)
    print("STAKEHOLDER ANALYSIS STUDY AND IMPLEMENTATION")
    print("=" * 72)

    print(
        textwrap.fill(
            "Stakeholder analysis is the systematic identification, "
            "assessment, classification, and engagement of people, groups, "
            "or organizations that can affect an initiative or be affected "
            "by it.",
            width=72,
        )
    )

    # Beginner-level identification.
    possible_roles = [
        "Executive Sponsor",
        "Project Manager",
        "Customers",
        "Employees",
        "Regulator",
        "Customers",
        " ",
        "External Vendor",
    ]

    identified = identify_stakeholders_from_roles(possible_roles)

    print("\nINITIAL IDENTIFICATION")
    print("=" * 72)
    print("Candidate roles:")
    for role in identified:
        print(f"  - {role}")

    register = create_sample_register()

    print_stakeholder_report(register.get("Executive Sponsor"))
    print_stakeholder_report(register.get("Customers"))

    print_power_interest_matrix(register)
    print_priority_ranking(register)
    describe_register(register)

    # Communication plans.
    print("\nCOMMUNICATION PLANS")
    print("=" * 72)

    for stakeholder in register.ranked_by_priority()[:5]:
        plan = build_communication_plan(stakeholder)
        print(f"\n{plan.stakeholder_name}")
        print(f"  Objective: {plan.objective}")
        print(f"  Channel:   {plan.channel}")
        print(f"  Frequency: {plan.frequency}")
        print(f"  Owner:     {plan.owner}")
        print(f"  Focus:     {plan.message_focus}")

    # Segmentation.
    print("\nINFLUENCE SEGMENTATION")
    print("=" * 72)

    for level, names in segment_by_influence(register.all()).items():
        print(f"{level:<8}: {', '.join(names)}")

    # Dependency analysis.
    print("\nDEPENDENCY ANALYSIS")
    print("=" * 72)

    graph = build_dependency_graph(register)

    for stakeholder, dependencies in graph.items():
        if dependencies:
            print(f"{stakeholder} depends on: {', '.join(dependencies)}")

    bottlenecks = find_dependency_bottlenecks(register)

    print("\nPotential dependency bottlenecks:")
    for stakeholder_name, count in bottlenecks:
        print(f"  {stakeholder_name}: referenced by {count} stakeholder(s)")

    # Conflict analysis.
    conflict = StakeholderConflict(
        stakeholder_a="Finance Department",
        stakeholder_b="IT Operations",
        topic="Project investment versus technical reliability",
        severity=6,
        description=(
            "Finance may seek tighter cost control while IT Operations "
            "may require additional investment to reduce operational risk."
        ),
    )

    conflict_score = conflict_priority(
        conflict,
        register.get(conflict.stakeholder_a),
        register.get(conflict.stakeholder_b),
    )

    print("\nCONFLICT ANALYSIS")
    print("=" * 72)
    print(f"Participants: {conflict.stakeholder_a} / {conflict.stakeholder_b}")
    print(f"Topic:        {conflict.topic}")
    print(f"Severity:     {conflict.severity}/10")
    print(f"Description:  {conflict.description}")
    print(f"Priority:     {conflict_score:.2f}")

    # Sensitivity analysis.
    sponsor = register.get("Executive Sponsor")

    scenarios = {
        "Balanced": {
            "interest": 0.25,
            "influence": 0.30,
            "impact": 0.20,
            "urgency": 0.15,
            "legitimacy": 0.10,
        },
        "Risk-focused": {
            "interest": 0.15,
            "influence": 0.30,
            "impact": 0.25,
            "urgency": 0.20,
            "legitimacy": 0.10,
        },
        "Impact-focused": {
            "interest": 0.20,
            "influence": 0.20,
            "impact": 0.35,
            "urgency": 0.15,
            "legitimacy": 0.10,
        },
    }

    print("\nSENSITIVITY ANALYSIS")
    print("=" * 72)

    for scenario_name, score in sensitivity_analysis(
        sponsor,
        scenarios,
    ):
        print(f"{scenario_name:<18}: {score:.2f}/10")

    # Quality checks.
    print("\nQUALITY CHECKS")
    print("=" * 72)

    warnings = check_register_quality(register)

    if warnings:
        for warning in warnings:
            print(f"  WARNING: {warning}")
    else:
        print("  No quality warnings detected.")

    # Edge-case demonstrations.
    print("\nEDGE CASES")
    print("=" * 72)

    try:
        invalid = Stakeholder(
            name="Invalid Stakeholder",
            role="Test",
            category=StakeholderCategory.INTERNAL,
            stakeholder_type=StakeholderType.PRIMARY,
            interest=11,
            influence=5,
            impact=5,
            urgency=5,
            legitimacy=5,
            current_engagement=EngagementLevel.NEUTRAL,
            desired_engagement=EngagementLevel.SUPPORTIVE,
        )
        register.add(invalid)
    except ValueError as error:
        print(f"Invalid score correctly rejected: {error}")

    try:
        register.add(register.get("Customers"))
    except ValueError as error:
        print(f"Duplicate stakeholder correctly rejected: {error}")

    try:
        calculate_weighted_score(
            sponsor,
            {
                "interest": 0.50,
                "influence": 0.50,
                "impact": 0.10,
                "urgency": 0.10,
                "legitimacy": 0.10,
            },
        )
    except ValueError as error:
        print(f"Invalid weights correctly rejected: {error}")

    # Safe percentage edge case.
    print(
        f"Zero-total percentage safely returns: "
        f"{safe_percentage(10, 0):.1f}%"
    )


# ---------------------------------------------------------------------------
# 16. UNIT-STYLE TESTS
# ---------------------------------------------------------------------------

def run_tests() -> None:
    """Run focused correctness checks."""
    print("\n" + "=" * 72)
    print("TESTS")
    print("=" * 72)

    stakeholder = Stakeholder(
        name="Test Sponsor",
        role="Sponsor",
        category=StakeholderCategory.INTERNAL,
        stakeholder_type=StakeholderType.PRIMARY,
        interest=9,
        influence=9,
        impact=8,
        urgency=8,
        legitimacy=10,
        current_engagement=EngagementLevel.NEUTRAL,
        desired_engagement=EngagementLevel.LEADING,
    )

    assert stakeholder.power_interest_quadrant == "Manage closely"
    assert stakeholder.influence_impact_quadrant == (
        "High influence / High impact"
    )
    assert stakeholder.engagement_gap == 2
    assert stakeholder.priority_score > 8

    low_power_high_interest = Stakeholder(
        name="User Group",
        role="Users",
        category=StakeholderCategory.EXTERNAL,
        stakeholder_type=StakeholderType.PRIMARY,
        interest=9,
        influence=3,
        impact=8,
        urgency=5,
        legitimacy=8,
        current_engagement=EngagementLevel.NEUTRAL,
        desired_engagement=EngagementLevel.SUPPORTIVE,
    )

    assert (
        low_power_high_interest.power_interest_quadrant
        == "Keep informed"
    )

    register = StakeholderRegister()
    register.add(stakeholder)

    assert len(register) == 1
    assert register.get("test sponsor").name == "Test Sponsor"

    percentage = safe_percentage(25, 100)
    assert math.isclose(percentage, 25.0)

    assert safe_percentage(1, 0) == 0.0

    weights = {
        "interest": 0.20,
        "influence": 0.30,
        "impact": 0.20,
        "urgency": 0.20,
        "legitimacy": 0.10,
    }

    weighted_score = calculate_weighted_score(stakeholder, weights)

    assert 1 <= weighted_score <= 10

    print("All tests passed.")


# ---------------------------------------------------------------------------
# 17. BEGINNER CONCEPT DEMONSTRATION
# ---------------------------------------------------------------------------

def explain_core_concepts() -> None:
    """
    Present concise conceptual definitions alongside executable examples.

    The purpose is to connect the mathematical implementation with the
    underlying project-management concepts.
    """
    concepts = {
        "Stakeholder": (
            "A person, group, or organization that can affect an initiative "
            "or be affected by it."
        ),
        "Interest": (
            "How strongly the stakeholder cares about the initiative, "
            "its outcomes, or its consequences."
        ),
        "Influence": (
            "The stakeholder's ability to affect decisions, resources, "
            "scope, priorities, or outcomes."
        ),
        "Impact": (
            "The degree to which the initiative changes the stakeholder's "
            "work, rights, services, costs, risks, or outcomes."
        ),
        "Urgency": (
            "How time-sensitive the stakeholder's concerns or claims are."
        ),
        "Legitimacy": (
            "The recognized appropriateness of the stakeholder's relationship "
            "to the initiative."
        ),
        "Power-interest matrix": (
            "A mapping technique that combines stakeholder influence or "
            "power with interest to determine engagement approaches."
        ),
        "Stakeholder register": (
            "A structured record containing stakeholder characteristics, "
            "concerns, relationships, engagement, and communication needs."
        ),
    }

    print("\nCORE CONCEPTS")
    print("=" * 72)

    for term, definition in concepts.items():
        print(f"\n{term}")
        print(textwrap.fill(definition, width=72, initial_indent="  "))


# ---------------------------------------------------------------------------
# 18. MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    """Execute the educational stakeholder-analysis program."""
    explain_core_concepts()
    run_case_study()
    run_tests()

    print("\n" + "=" * 72)
    print("END OF STAKEHOLDER ANALYSIS IMPLEMENTATION")
    print("=" * 72)


if __name__ == "__main__":
    main()
