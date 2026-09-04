"""
PROJECT SUCCESS: FACTORS THAT DETERMINE PROJECT SUCCESS

A comprehensive, executable study file covering project success from beginner
through advanced level.

The script demonstrates:

* Project success fundamentals
* Success criteria and critical success factors
* Scope, schedule, cost, quality, benefits, and value
* Stakeholder management
* Governance and decision-making
* Leadership and team effectiveness
* Risk and issue management
* Communication
* Requirements and change management
* Planning and estimation
* Agile, predictive, and hybrid delivery
* Project performance measurement
* Earned Value Management
* Benefits realization
* Project health scoring
* Risk scoring
* Stakeholder analysis
* Dependency analysis
* Scenario simulation
* Failure analysis
* Project-success assessment
* Testing and validation
* Practical implementation patterns

The script uses only Python's standard library.
"""

from **future** import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import sqrt
from statistics import mean
from typing import Dict, List, Optional, Tuple

# ============================================================================

# 1. FUNDAMENTAL TERMINOLOGY

# ============================================================================

class ProjectLifecycle(Enum):
"""Common lifecycle structures."""
PREDICTIVE = "Predictive"
AGILE = "Agile"
HYBRID = "Hybrid"

class ProjectStatus(Enum):
"""High-level project health states."""
HEALTHY = "Healthy"
AT_RISK = "At Risk"
CRITICAL = "Critical"

class RiskResponse(Enum):
"""Typical response strategies for threats."""
AVOID = "Avoid"
MITIGATE = "Mitigate"
TRANSFER = "Transfer"
ACCEPT = "Accept"

class StakeholderInfluence(Enum):
"""Simple stakeholder influence classification."""
LOW = "Low"
MEDIUM = "Medium"
HIGH = "High"

# ============================================================================

# 2. BASIC SUCCESS CRITERIA

# ============================================================================

@dataclass
class SuccessCriteria:
"""
Defines measurable conditions used to judge whether a project succeeded.

```
Traditional project management often emphasizes:
    scope + schedule + cost + quality

Mature project evaluation also considers:
    stakeholder satisfaction + benefits + strategic value + adoption
"""

scope_met: bool
schedule_met: bool
budget_met: bool
quality_met: bool
stakeholder_satisfaction: float
benefits_realized: float
strategic_alignment: float

def validate(self) -> None:
    """Validate percentage-like fields."""
    for name, value in {
        "stakeholder_satisfaction": self.stakeholder_satisfaction,
        "benefits_realized": self.benefits_realized,
        "strategic_alignment": self.strategic_alignment,
    }.items():
        if not 0 <= value <= 100:
            raise ValueError(f"{name} must be between 0 and 100.")

def traditional_score(self) -> float:
    """Score based primarily on the classic delivery constraints."""
    binary_score = mean(
        [
            float(self.scope_met),
            float(self.schedule_met),
            float(self.budget_met),
            float(self.quality_met),
        ]
    )
    return binary_score * 100

def modern_score(self) -> float:
    """
    Broader success score.

    The weights intentionally give benefits and strategic alignment more
    importance than simple schedule/cost compliance.
    """
    self.validate()

    delivery = mean(
        [
            float(self.scope_met) * 100,
            float(self.schedule_met) * 100,
            float(self.budget_met) * 100,
            float(self.quality_met) * 100,
        ]
    )

    return (
        delivery * 0.40
        + self.stakeholder_satisfaction * 0.20
        + self.benefits_realized * 0.25
        + self.strategic_alignment * 0.15
    )
```

def demonstrate_success_criteria() -> None:
"""Show why project success is broader than the iron triangle."""
criteria = SuccessCriteria(
scope_met=True,
schedule_met=False,
budget_met=True,
quality_met=True,
stakeholder_satisfaction=92,
benefits_realized=88,
strategic_alignment=95,
)

```
print("\nSUCCESS CRITERIA")
print("-" * 70)
print(f"Traditional delivery score: {criteria.traditional_score():.1f}%")
print(f"Broader success score:      {criteria.modern_score():.1f}%")
print(
    "\nInterpretation: a project can miss one delivery constraint while "
    "still producing substantial stakeholder, business, and strategic value."
)
```

# ============================================================================

# 3. PROJECT SUCCESS FACTORS

# ============================================================================

@dataclass
class SuccessFactor:
"""
A measurable factor that influences project success.

```
weight:
    Relative importance of the factor.

rating:
    Current project performance on a 0-100 scale.
"""

name: str
weight: float
rating: float
rationale: str = ""

def __post_init__(self) -> None:
    if self.weight < 0:
        raise ValueError("Weight cannot be negative.")
    if not 0 <= self.rating <= 100:
        raise ValueError("Rating must be between 0 and 100.")

@property
def weighted_score(self) -> float:
    return self.weight * self.rating
```

@dataclass
class SuccessFactorModel:
"""Weighted model for assessing project success readiness."""

```
factors: List[SuccessFactor]

def validate(self) -> None:
    total_weight = sum(f.weight for f in self.factors)
    if total_weight <= 0:
        raise ValueError("Total factor weight must be positive.")

    if abs(total_weight - 1.0) > 0.0001:
        raise ValueError(
            f"Weights must sum to 1.0. Current total: {total_weight:.4f}"
        )

def score(self) -> float:
    self.validate()
    return sum(f.weighted_score for f in self.factors)

def ranked_factors(self) -> List[SuccessFactor]:
    return sorted(
        self.factors,
        key=lambda factor: factor.weight * (100 - factor.rating),
        reverse=True,
    )

def weakest_factors(self, count: int = 3) -> List[SuccessFactor]:
    return sorted(self.factors, key=lambda factor: factor.rating)[:count]
```

def demonstrate_success_factor_model() -> None:
factors = [
SuccessFactor(
"Clear objectives",
0.15,
90,
"Objectives define what success means."
),
SuccessFactor(
"Stakeholder engagement",
0.15,
75,
"Stakeholder commitment reduces resistance and ambiguity."
),
SuccessFactor(
"Executive sponsorship",
0.10,
70,
"Sponsors provide authority, resources, and escalation support."
),
SuccessFactor(
"Requirements quality",
0.10,
82,
"Poor requirements create rework and scope instability."
),
SuccessFactor(
"Planning and estimation",
0.10,
78,
"Realistic planning improves predictability."
),
SuccessFactor(
"Risk management",
0.10,
65,
"Early risk treatment prevents avoidable disruption."
),
SuccessFactor(
"Team capability",
0.10,
88,
"Competence and collaboration directly affect execution."
),
SuccessFactor(
"Communication",
0.10,
80,
"Information must reach the right people at the right time."
),
SuccessFactor(
"Governance",
0.05,
72,
"Governance establishes decision rights and accountability."
),
SuccessFactor(
"Benefits readiness",
0.05,
60,
"A delivered product is not automatically a realized benefit."
),
]

```
model = SuccessFactorModel(factors)

print("\nSUCCESS FACTOR MODEL")
print("-" * 70)
print(f"Weighted project success readiness: {model.score():.2f}%")

print("\nFactors with the largest risk contribution:")
for factor in model.ranked_factors()[:5]:
    gap = 100 - factor.rating
    contribution = factor.weight * gap
    print(
        f"- {factor.name:<28} "
        f"rating={factor.rating:>5.1f} "
        f"gap={gap:>5.1f} "
        f"weighted gap={contribution:.2f}"
    )

print("\nWeakest current factors:")
for factor in model.weakest_factors():
    print(f"- {factor.name}: {factor.rating:.1f}%")
```

# ============================================================================

# 4. OBJECTIVES, OUTCOMES, OUTPUTS, AND BENEFITS

# ============================================================================

@dataclass
class ProjectObjective:
"""Represents a measurable project objective."""

```
name: str
target: float
actual: float
unit: str

@property
def achievement_percentage(self) -> float:
    if self.target == 0:
        return 100.0 if self.actual == 0 else 0.0
    return (self.actual / self.target) * 100
```

@dataclass
class Benefit:
"""Represents a benefit expected from project delivery."""

```
name: str
expected_value: float
realized_value: float
unit: str

@property
def realization_percentage(self) -> float:
    if self.expected_value == 0:
        return 100.0
    return min(
        100.0,
        max(0.0, self.realized_value / self.expected_value * 100),
    )
```

def distinguish_project_terms() -> None:
"""
Explain a crucial distinction:

```
Output:
    What the project creates.

Outcome:
    What changes because stakeholders use the output.

Benefit:
    The measurable improvement produced by that change.

Value:
    The broader organizational worth produced by the benefits.
"""
print("\nOUTPUT -> OUTCOME -> BENEFIT -> VALUE")
print("-" * 70)

examples = [
    ("Output", "New customer-service application"),
    ("Outcome", "Customers increasingly use digital self-service"),
    ("Benefit", "Average support cost decreases"),
    ("Value", "Improved customer economics and competitiveness"),
]

for level, description in examples:
    print(f"{level:<10}: {description}")

objectives = [
    ProjectObjective("Application adoption", 80, 74, "%"),
    ProjectObjective("Average handling time", 10, 8.5, "minutes"),
]

for objective in objectives:
    print(
        f"{objective.name}: "
        f"{objective.actual}{objective.unit} against "
        f"target {objective.target}{objective.unit}"
    )

benefits = [
    Benefit("Annual savings", 5_000_000, 4_200_000, "INR"),
    Benefit("Customer satisfaction improvement", 15, 11, "points"),
]

for benefit in benefits:
    print(
        f"{benefit.name}: "
        f"{benefit.realization_percentage:.1f}% realized"
    )
```

# ============================================================================

# 5. SCOPE MANAGEMENT

# ============================================================================

@dataclass
class ScopeItem:
"""A project deliverable or requirement."""

```
name: str
priority: str
completed: bool = False
```

class ScopeManager:
"""Simple scope baseline and change-control model."""

```
VALID_PRIORITIES = {"Must", "Should", "Could", "Won't"}

def __init__(self, items: Optional[List[ScopeItem]] = None):
    self.items = items or []
    self.change_requests: List[str] = []

def add_item(self, item: ScopeItem) -> None:
    if item.priority not in self.VALID_PRIORITIES:
        raise ValueError(
            f"Priority must be one of {self.VALID_PRIORITIES}."
        )
    self.items.append(item)

def request_change(self, description: str) -> None:
    if not description.strip():
        raise ValueError("Change description cannot be empty.")
    self.change_requests.append(description)

def completion_rate(self) -> float:
    if not self.items:
        return 0.0
    return (
        sum(item.completed for item in self.items)
        / len(self.items)
        * 100
    )

def scope_creep_risk(self) -> str:
    if len(self.change_requests) >= 10:
        return "High"
    if len(self.change_requests) >= 5:
        return "Medium"
    return "Low"
```

def demonstrate_scope_management() -> None:
scope = ScopeManager(
[
ScopeItem("Authentication", "Must", True),
ScopeItem("Reporting", "Must", True),
ScopeItem("Analytics", "Should", False),
ScopeItem("Dark mode", "Could", False),
]
)

```
scope.request_change("Add a new reporting dimension.")
scope.request_change("Add another user role.")

print("\nSCOPE MANAGEMENT")
print("-" * 70)
print(f"Scope completion: {scope.completion_rate():.1f}%")
print(f"Scope-creep risk: {scope.scope_creep_risk()}")

print(
    "\nKey principle: a change is not automatically bad. "
    "Uncontrolled change is the problem. A legitimate change should "
    "be evaluated for impact on scope, time, cost, quality, risk, "
    "resources, and benefits."
)
```

# ============================================================================

# 6. STAKEHOLDER MANAGEMENT

# ============================================================================

@dataclass
class Stakeholder:
"""Stakeholder represented through power and interest."""

```
name: str
power: int
interest: int
current_support: int
desired_support: int

def __post_init__(self) -> None:
    for value_name, value in {
        "power": self.power,
        "interest": self.interest,
        "current_support": self.current_support,
        "desired_support": self.desired_support,
    }.items():
        if not 0 <= value <= 100:
            raise ValueError(f"{value_name} must be 0-100.")

@property
def engagement_gap(self) -> int:
    return max(0, self.desired_support - self.current_support)

@property
def strategy(self) -> str:
    if self.power >= 70 and self.interest >= 70:
        return "Manage closely"
    if self.power >= 70:
        return "Keep satisfied"
    if self.interest >= 70:
        return "Keep informed"
    return "Monitor"
```

class StakeholderRegister:
"""Stakeholder analysis and prioritization."""

```
def __init__(self, stakeholders: List[Stakeholder]):
    self.stakeholders = stakeholders

def highest_priority(self) -> Stakeholder:
    return max(
        self.stakeholders,
        key=lambda stakeholder: (
            stakeholder.power * stakeholder.interest
            + stakeholder.engagement_gap * 100
        ),
    )

def report(self) -> None:
    for stakeholder in self.stakeholders:
        print(
            f"{stakeholder.name:<22} "
            f"strategy={stakeholder.strategy:<16} "
            f"support gap={stakeholder.engagement_gap}"
        )
```

def demonstrate_stakeholder_management() -> None:
register = StakeholderRegister(
[
Stakeholder("Executive sponsor", 95, 90, 85, 95),
Stakeholder("Business owner", 90, 95, 70, 95),
Stakeholder("End users", 50, 95, 60, 90),
Stakeholder("Finance", 80, 50, 80, 80),
Stakeholder("External vendor", 40, 60, 75, 80),
]
)

```
print("\nSTAKEHOLDER MANAGEMENT")
print("-" * 70)
register.report()
print(
    f"Highest priority stakeholder: "
    f"{register.highest_priority().name}"
)
```

# ============================================================================

# 7. COMMUNICATION EFFECTIVENESS

# ============================================================================

@dataclass
class CommunicationChannel:
"""Communication channel with expected effectiveness."""

```
name: str
reach: float
clarity: float
timeliness: float

@property
def effectiveness(self) -> float:
    return mean([self.reach, self.clarity, self.timeliness])
```

def communication_effectiveness_example() -> None:
channels = [
CommunicationChannel("Weekly steering meeting", 90, 92, 75),
CommunicationChannel("Dashboard", 95, 82, 98),
CommunicationChannel("Email", 85, 70, 80),
CommunicationChannel("Informal chat", 60, 55, 95),
]

```
print("\nCOMMUNICATION EFFECTIVENESS")
print("-" * 70)

for channel in sorted(
    channels,
    key=lambda item: item.effectiveness,
    reverse=True,
):
    print(
        f"{channel.name:<25} "
        f"effectiveness={channel.effectiveness:.1f}%"
    )

print(
    "\nCommunication quality depends on the audience, message, channel, "
    "timing, feedback mechanism, and consequence of misunderstanding."
)
```

# ============================================================================

# 8. RISK MANAGEMENT

# ============================================================================

@dataclass
class Risk:
"""Quantitative representation of a project risk."""

```
name: str
probability: float
impact: float
response: RiskResponse
owner: str
mitigation_effectiveness: float = 0.0

def __post_init__(self) -> None:
    for field_name, value in {
        "probability": self.probability,
        "impact": self.impact,
        "mitigation_effectiveness": self.mitigation_effectiveness,
    }.items():
        if not 0 <= value <= 100:
            raise ValueError(f"{field_name} must be 0-100.")

@property
def inherent_score(self) -> float:
    return self.probability * self.impact / 100

@property
def residual_probability(self) -> float:
    return self.probability * (
        1 - self.mitigation_effectiveness / 100
    )

@property
def residual_score(self) -> float:
    return self.residual_probability * self.impact / 100
```

class RiskRegister:
"""Risk prioritization and treatment."""

```
def __init__(self, risks: List[Risk]):
    self.risks = risks

def expected_loss(self, monetary_impact: Dict[str, float]) -> float:
    """
    Expected Monetary Value:

        EMV = Probability * Monetary Impact

    Probability is represented as a decimal here.
    """
    total = 0.0

    for risk in self.risks:
        impact = monetary_impact.get(risk.name, 0.0)
        total += (risk.residual_probability / 100) * impact

    return total

def prioritized(self) -> List[Risk]:
    return sorted(
        self.risks,
        key=lambda risk: risk.residual_score,
        reverse=True,
    )
```

def demonstrate_risk_management() -> None:
risks = [
Risk(
"Critical vendor delay",
65,
90,
RiskResponse.MITIGATE,
"Procurement",
50,
),
Risk(
"Low user adoption",
55,
80,
RiskResponse.MITIGATE,
"Product owner",
35,
),
Risk(
"Minor reporting defect",
30,
30,
RiskResponse.ACCEPT,
"QA lead",
0,
),
]

```
register = RiskRegister(risks)

monetary_impacts = {
    "Critical vendor delay": 2_000_000,
    "Low user adoption": 3_000_000,
    "Minor reporting defect": 100_000,
}

print("\nRISK MANAGEMENT")
print("-" * 70)

for risk in register.prioritized():
    print(
        f"{risk.name:<28} "
        f"inherent={risk.inherent_score:>5.1f} "
        f"residual={risk.residual_score:>5.1f}"
    )

print(
    f"Expected residual monetary exposure: "
    f"INR {register.expected_loss(monetary_impacts):,.0f}"
)
```

# ============================================================================

# 9. ISSUE MANAGEMENT

# ============================================================================

@dataclass
class Issue:
"""An issue is a problem that has already occurred."""

```
name: str
severity: int
urgency: int
owner: str
resolved: bool = False

@property
def priority_score(self) -> int:
    return self.severity * self.urgency
```

def demonstrate_issue_management() -> None:
issues = [
Issue("Production integration failure", 95, 95, "Technical lead"),
Issue("Delayed approval", 70, 85, "Business owner"),
Issue("Minor UI defect", 25, 20, "Frontend lead"),
]

```
print("\nISSUE MANAGEMENT")
print("-" * 70)

for issue in sorted(
    issues,
    key=lambda item: item.priority_score,
    reverse=True,
):
    print(
        f"{issue.name:<32} "
        f"priority={issue.priority_score:>4} "
        f"owner={issue.owner}"
    )

print(
    "\nDistinction: a risk is an uncertain future event; "
    "an issue is a problem that has already materialized."
)
```

# ============================================================================

# 10. QUALITY MANAGEMENT

# ============================================================================

@dataclass
class QualityMetric:
"""A measurable quality attribute."""

```
name: str
target: float
actual: float
higher_is_better: bool = True

@property
def achievement(self) -> float:
    if self.target == 0:
        return 100.0

    if self.higher_is_better:
        return min(100.0, self.actual / self.target * 100)

    if self.actual <= self.target:
        return 100.0

    return max(0.0, self.target / self.actual * 100)
```

def demonstrate_quality_management() -> None:
metrics = [
QualityMetric("Automated test coverage", 85, 91),
QualityMetric("Critical defects", 0, 2, False),
QualityMetric("Availability", 99.9, 99.95),
QualityMetric("Defect escape rate", 2, 1.5, False),
]

```
print("\nQUALITY MANAGEMENT")
print("-" * 70)

for metric in metrics:
    print(
        f"{metric.name:<28} "
        f"target={metric.target:<7} "
        f"actual={metric.actual:<7} "
        f"achievement={metric.achievement:.1f}%"
    )
```

# ============================================================================

# 11. SCHEDULE MANAGEMENT

# ============================================================================

@dataclass
class Task:
"""Task with planned and actual duration."""

```
name: str
planned_days: float
actual_days: float
dependency_count: int = 0

@property
def schedule_variance(self) -> float:
    return self.planned_days - self.actual_days

@property
def delay_percentage(self) -> float:
    if self.planned_days == 0:
        return 0.0
    return max(
        0.0,
        (self.actual_days - self.planned_days)
        / self.planned_days
        * 100,
    )
```

def demonstrate_schedule_management() -> None:
tasks = [
Task("Requirements", 10, 12),
Task("Architecture", 8, 8),
Task("Development", 30, 36, 3),
Task("Testing", 15, 20, 2),
Task("Deployment", 5, 5, 1),
]

```
print("\nSCHEDULE MANAGEMENT")
print("-" * 70)

planned_total = sum(task.planned_days for task in tasks)
actual_total = sum(task.actual_days for task in tasks)

print(f"Planned duration: {planned_total:.1f} days")
print(f"Actual duration:  {actual_total:.1f} days")
print(
    f"Schedule overrun: "
    f"{actual_total - planned_total:.1f} days"
)

print("\nTask delays:")
for task in tasks:
    print(
        f"- {task.name:<18} "
        f"delay={task.delay_percentage:.1f}%"
    )
```

# ============================================================================

# 12. COST MANAGEMENT

# ============================================================================

@dataclass
class CostItem:
"""Budget line item."""

```
name: str
planned_cost: float
actual_cost: float

@property
def variance(self) -> float:
    return self.planned_cost - self.actual_cost

@property
def variance_percentage(self) -> float:
    if self.planned_cost == 0:
        return 0.0
    return (
        self.actual_cost - self.planned_cost
    ) / self.planned_cost * 100
```

def demonstrate_cost_management() -> None:
costs = [
CostItem("Engineering", 5_000_000, 5_400_000),
CostItem("Testing", 1_500_000, 1_300_000),
CostItem("Infrastructure", 1_000_000, 1_200_000),
CostItem("Training", 500_000, 400_000),
]

```
planned = sum(item.planned_cost for item in costs)
actual = sum(item.actual_cost for item in costs)

print("\nCOST MANAGEMENT")
print("-" * 70)
print(f"Planned cost: INR {planned:,.0f}")
print(f"Actual cost:  INR {actual:,.0f}")
print(f"Variance:     INR {planned - actual:,.0f}")

for item in costs:
    print(
        f"- {item.name:<18} "
        f"variance={item.variance_percentage:+.1f}%"
    )
```

# ============================================================================

# 13. RESOURCE AND TEAM EFFECTIVENESS

# ============================================================================

@dataclass
class TeamMember:
"""Simple team capability representation."""

```
name: str
skill_level: float
availability: float
collaboration: float

@property
def effectiveness(self) -> float:
    return (
        self.skill_level * 0.45
        + self.availability * 0.25
        + self.collaboration * 0.30
    )
```

def demonstrate_team_effectiveness() -> None:
team = [
TeamMember("Engineer A", 92, 90, 85),
TeamMember("Engineer B", 85, 75, 90),
TeamMember("QA Engineer", 88, 80, 94),
TeamMember("Business Analyst", 90, 95, 88),
]

```
print("\nTEAM EFFECTIVENESS")
print("-" * 70)

for member in team:
    print(
        f"{member.name:<18} "
        f"effectiveness={member.effectiveness:.1f}%"
    )

team_average = mean(member.effectiveness for member in team)
print(f"Team average effectiveness: {team_average:.1f}%")
```

# ============================================================================

# 14. GOVERNANCE

# ============================================================================

@dataclass
class Decision:
"""Governance decision record."""

```
topic: str
decision: str
owner: str
impact: str
reversible: bool
```

class GovernanceBoard:
"""Simple governance decision register."""

```
def __init__(self):
    self.decisions: List[Decision] = []

def record(self, decision: Decision) -> None:
    self.decisions.append(decision)

def high_impact_decisions(self) -> List[Decision]:
    return [
        decision
        for decision in self.decisions
        if decision.impact.lower() == "high"
    ]
```

def demonstrate_governance() -> None:
board = GovernanceBoard()

```
board.record(
    Decision(
        "Architecture",
        "Use event-driven integration",
        "Architecture Board",
        "High",
        False,
    )
)

board.record(
    Decision(
        "UI theme",
        "Use standard design system",
        "Product Owner",
        "Low",
        True,
    )
)

print("\nGOVERNANCE")
print("-" * 70)

for decision in board.decisions:
    print(
        f"{decision.topic:<15} "
        f"owner={decision.owner:<20} "
        f"impact={decision.impact:<6} "
        f"reversible={decision.reversible}"
    )

print(
    f"High-impact decisions: "
    f"{len(board.high_impact_decisions())}"
)
```

# ============================================================================

# 15. CHANGE MANAGEMENT

# ============================================================================

@dataclass
class ChangeRequest:
"""Change request with multidimensional impact."""

```
description: str
scope_impact: float
schedule_impact: float
cost_impact: float
risk_impact: float
benefit_impact: float

@property
def net_change_pressure(self) -> float:
    """
    Positive benefit can justify additional delivery pressure.

    This is an educational heuristic, not a universal financial model.
    """
    negative = (
        self.scope_impact
        + self.schedule_impact
        + self.cost_impact
        + self.risk_impact
    )
    return self.benefit_impact - negative
```

def demonstrate_change_control() -> None:
changes = [
ChangeRequest(
"Add regulatory reporting",
20,
15,
10,
5,
80,
),
ChangeRequest(
"Add cosmetic dashboard animation",
5,
10,
8,
3,
4,
),
]

```
print("\nCHANGE CONTROL")
print("-" * 70)

for change in changes:
    recommendation = (
        "Potentially justified"
        if change.net_change_pressure > 0
        else "Requires strong justification"
    )

    print(
        f"{change.description:<34} "
        f"net pressure={change.net_change_pressure:+.1f} "
        f"-> {recommendation}"
    )
```

# ============================================================================

# 16. AGILE, PREDICTIVE, AND HYBRID APPROACHES

# ============================================================================

@dataclass
class DeliveryApproach:
"""Characteristics of a delivery approach."""

```
name: str
requirement_stability: str
feedback_frequency: str
planning_horizon: str
change_tolerance: str
```

def compare_delivery_approaches() -> None:
approaches = [
DeliveryApproach(
"Predictive",
"High",
"Periodic",
"Long",
"Lower",
),
DeliveryApproach(
"Agile",
"Low to medium",
"Frequent",
"Short",
"High",
),
DeliveryApproach(
"Hybrid",
"Mixed",
"Mixed",
"Mixed",
"Medium to high",
),
]

```
print("\nDELIVERY APPROACHES")
print("-" * 70)

for approach in approaches:
    print(
        f"{approach.name:<12} "
        f"requirements={approach.requirement_stability:<15} "
        f"feedback={approach.feedback_frequency:<10} "
        f"change={approach.change_tolerance}"
    )

print(
    "\nSuccess does not come from selecting a fashionable methodology. "
    "The delivery approach should fit uncertainty, regulation, "
    "stakeholder availability, product characteristics, and organizational "
    "constraints."
)
```

# ============================================================================

# 17. EARNED VALUE MANAGEMENT

# ============================================================================

@dataclass
class EarnedValueMetrics:
"""
Core Earned Value Management metrics.

```
PV = Planned Value
EV = Earned Value
AC = Actual Cost

SV = EV - PV
CV = EV - AC

SPI = EV / PV
CPI = EV / AC

CPI/SPI above 1 generally indicates favorable performance.
"""

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
        return 0.0
    return self.earned_value / self.planned_value

@property
def cost_performance_index(self) -> float:
    if self.actual_cost == 0:
        return 0.0
    return self.earned_value / self.actual_cost
```

def demonstrate_earned_value() -> None:
evm = EarnedValueMetrics(
planned_value=8_000_000,
earned_value=7_000_000,
actual_cost=7_500_000,
)

```
print("\nEARNED VALUE MANAGEMENT")
print("-" * 70)
print(f"SV:  INR {evm.schedule_variance:,.0f}")
print(f"CV:  INR {evm.cost_variance:,.0f}")
print(f"SPI: {evm.schedule_performance_index:.3f}")
print(f"CPI: {evm.cost_performance_index:.3f}")

print(
    "\nInterpretation: EV below PV indicates schedule underperformance, "
    "while EV below AC indicates cost inefficiency."
)
```

# ============================================================================

# 18. SIMPLE FORECASTING

# ============================================================================

@dataclass
class ProjectForecast:
"""Forecast using the current cost performance index."""

```
budget_at_completion: float
cost_performance_index: float

@property
def estimate_at_completion(self) -> float:
    if self.cost_performance_index <= 0:
        raise ValueError("CPI must be positive.")
    return self.budget_at_completion / self.cost_performance_index

@property
def projected_variance(self) -> float:
    return (
        self.budget_at_completion
        - self.estimate_at_completion
    )
```

def demonstrate_forecasting() -> None:
forecast = ProjectForecast(10_000_000, 0.88)

```
print("\nPROJECT FORECASTING")
print("-" * 70)
print(
    f"Budget at completion: "
    f"INR {forecast.budget_at_completion:,.0f}"
)
print(
    f"Forecast EAC: "
    f"INR {forecast.estimate_at_completion:,.0f}"
)
print(
    f"Projected variance: "
    f"INR {forecast.projected_variance:,.0f}"
)
```

# ============================================================================

# 19. PROJECT HEALTH SCORE

# ============================================================================

@dataclass
class ProjectHealth:
"""Aggregates major project dimensions."""

```
scope: float
schedule: float
cost: float
quality: float
risk: float
stakeholder: float
team: float
benefits: float

def __post_init__(self) -> None:
    for name, value in self.__dict__.items():
        if not 0 <= value <= 100:
            raise ValueError(f"{name} must be between 0 and 100.")

@property
def score(self) -> float:
    weights = {
        "scope": 0.10,
        "schedule": 0.12,
        "cost": 0.12,
        "quality": 0.14,
        "risk": 0.12,
        "stakeholder": 0.14,
        "team": 0.10,
        "benefits": 0.16,
    }

    values = {
        "scope": self.scope,
        "schedule": self.schedule,
        "cost": self.cost,
        "quality": self.quality,
        "risk": self.risk,
        "stakeholder": self.stakeholder,
        "team": self.team,
        "benefits": self.benefits,
    }

    return sum(values[name] * weight for name, weight in weights.items())

@property
def status(self) -> ProjectStatus:
    if self.score >= 80:
        return ProjectStatus.HEALTHY
    if self.score >= 60:
        return ProjectStatus.AT_RISK
    return ProjectStatus.CRITICAL

def weakest_dimension(self) -> Tuple[str, float]:
    values = {
        "scope": self.scope,
        "schedule": self.schedule,
        "cost": self.cost,
        "quality": self.quality,
        "risk": self.risk,
        "stakeholder": self.stakeholder,
        "team": self.team,
        "benefits": self.benefits,
    }
    return min(values.items(), key=lambda item: item[1])
```

def demonstrate_project_health() -> None:
health = ProjectHealth(
scope=90,
schedule=72,
cost=78,
quality=94,
risk=65,
stakeholder=82,
team=88,
benefits=70,
)

```
print("\nPROJECT HEALTH")
print("-" * 70)
print(f"Health score: {health.score:.2f}%")
print(f"Status:       {health.status.value}")
print(
    f"Weakest dimension: "
    f"{health.weakest_dimension()[0]} "
    f"({health.weakest_dimension()[1]:.1f}%)"
)
```

# ============================================================================

# 20. ROOT CAUSE ANALYSIS

# ============================================================================

@dataclass
class RootCauseNode:
"""Node in a simplified causal chain."""

```
problem: str
causes: List[str] = field(default_factory=list)
```

def five_whys(problem: str, why_chain: List[str]) -> str:
"""
Five Whys is a structured questioning technique.

```
It should not be treated as proof that the final answer is the only
root cause. Complex failures can have multiple interacting causes.
"""
if not why_chain:
    raise ValueError("At least one why-answer is required.")

print("\nFIVE WHYS")
print("-" * 70)
print(f"Problem: {problem}")

for index, answer in enumerate(why_chain, start=1):
    print(f"Why {index}: {answer}")

return why_chain[-1]
```

def demonstrate_root_cause_analysis() -> None:
root_cause = five_whys(
"Project deployment was delayed.",
[
"The deployment environment was not ready.",
"Infrastructure provisioning started late.",
"The infrastructure request required an approval.",
"Approval ownership was unclear.",
"The governance model did not define a clear approval owner.",
],
)

```
print(f"Potential systemic root cause: {root_cause}")
```

# ============================================================================

# 21. DEPENDENCY ANALYSIS

# ============================================================================

@dataclass
class Dependency:
"""Represents a dependency between activities."""

```
predecessor: str
successor: str
criticality: int

def __post_init__(self) -> None:
    if not 0 <= self.criticality <= 100:
        raise ValueError("Criticality must be 0-100.")
```

def demonstrate_dependencies() -> None:
dependencies = [
Dependency("Architecture", "Development", 90),
Dependency("Development", "Integration testing", 95),
Dependency("Integration testing", "Deployment", 100),
Dependency("Training material", "User training", 80),
]

```
print("\nDEPENDENCY ANALYSIS")
print("-" * 70)

for dependency in sorted(
    dependencies,
    key=lambda item: item.criticality,
    reverse=True,
):
    print(
        f"{dependency.predecessor:<22} -> "
        f"{dependency.successor:<22} "
        f"criticality={dependency.criticality}"
    )
```

# ============================================================================

# 22. PROJECT FAILURE MODES

# ============================================================================

@dataclass
class FailureMode:
"""Failure mode with severity, occurrence, and detectability."""

```
name: str
severity: int
occurrence: int
detectability: int

@property
def rpn(self) -> int:
    """
    Risk Priority Number.

    RPN = Severity * Occurrence * Detectability

    This is an educational FMEA-style heuristic.
    """
    return self.severity * self.occurrence * self.detectability
```

def demonstrate_failure_modes() -> None:
failures = [
FailureMode("Unclear requirements", 8, 7, 6),
FailureMode("Late integration", 9, 6, 8),
FailureMode("Weak stakeholder adoption", 8, 7, 7),
FailureMode("Minor UI defect", 3, 8, 2),
]

```
print("\nFAILURE MODE PRIORITIZATION")
print("-" * 70)

for failure in sorted(
    failures,
    key=lambda item: item.rpn,
    reverse=True,
):
    print(
        f"{failure.name:<32} "
        f"RPN={failure.rpn}"
    )
```

# ============================================================================

# 23. DECISION QUALITY

# ============================================================================

@dataclass
class DecisionOption:
"""Option scored against multiple decision criteria."""

```
name: str
strategic_fit: float
cost: float
feasibility: float
risk: float
stakeholder_support: float

@property
def score(self) -> float:
    """
    Higher is better.

    Cost and risk are inverted because lower values are preferable.
    """
    return (
        self.strategic_fit * 0.30
        + (100 - self.cost) * 0.15
        + self.feasibility * 0.20
        + (100 - self.risk) * 0.15
        + self.stakeholder_support * 0.20
    )
```

def demonstrate_decision_analysis() -> None:
options = [
DecisionOption("Option A", 90, 60, 85, 30, 80),
DecisionOption("Option B", 80, 35, 90, 20, 85),
DecisionOption("Option C", 95, 85, 60, 50, 70),
]

```
print("\nDECISION ANALYSIS")
print("-" * 70)

for option in sorted(
    options,
    key=lambda item: item.score,
    reverse=True,
):
    print(f"{option.name}: score={option.score:.2f}")

print(
    "\nA scoring model supports structured comparison, but it should not "
    "replace judgment. The quality of the criteria and assumptions "
    "determines the quality of the decision."
)
```

# ============================================================================

# 24. PROJECT SUCCESS AS A SYSTEM

# ============================================================================

@dataclass
class ProjectSystem:
"""
Represents project success as an interacting system.

```
Success is rarely determined by a single variable. A project may have
strong technical execution and still fail because adoption, governance,
business ownership, or benefits realization is weak.
"""

strategy: float
leadership: float
people: float
process: float
technology: float
stakeholders: float
risk_management: float
change_management: float
benefits_realization: float

def success_probability_index(self) -> float:
    """
    Weighted index.

    This is an educational model, not a statistically calibrated
    probability of actual project success.
    """
    weights = {
        "strategy": 0.14,
        "leadership": 0.12,
        "people": 0.12,
        "process": 0.10,
        "technology": 0.08,
        "stakeholders": 0.13,
        "risk_management": 0.10,
        "change_management": 0.09,
        "benefits_realization": 0.12,
    }

    values = {
        key: getattr(self, key)
        for key in weights
    }

    return sum(values[key] * weights[key] for key in weights)
```

def demonstrate_systemic_success() -> None:
system = ProjectSystem(
strategy=95,
leadership=85,
people=90,
process=78,
technology=92,
stakeholders=75,
risk_management=68,
change_management=62,
benefits_realization=70,
)

```
index = system.success_probability_index()

print("\nPROJECT SUCCESS AS A SYSTEM")
print("-" * 70)
print(f"Success-readiness index: {index:.2f}%")

weakest = min(
    (
        ("strategy", system.strategy),
        ("leadership", system.leadership),
        ("people", system.people),
        ("process", system.process),
        ("technology", system.technology),
        ("stakeholders", system.stakeholders),
        ("risk management", system.risk_management),
        ("change management", system.change_management),
        ("benefits realization", system.benefits_realization),
    ),
    key=lambda item: item[1],
)

print(
    f"Most important weak area to investigate: "
    f"{weakest[0]} ({weakest[1]:.1f}%)"
)
```

# ============================================================================

# 25. SENSITIVITY ANALYSIS

# ============================================================================

def sensitivity_analysis(
model: SuccessFactorModel,
factor_name: str,
rating_changes: List[float],
) -> List[Tuple[float, float]]:
"""
Measure how changes to one factor affect the weighted score.

```
Sensitivity analysis helps identify factors with significant leverage.
"""
target = next(
    (factor for factor in model.factors if factor.name == factor_name),
    None,
)

if target is None:
    raise KeyError(f"Unknown factor: {factor_name}")

original_rating = target.rating
results = []

for new_rating in rating_changes:
    if not 0 <= new_rating <= 100:
        raise ValueError("Sensitivity ratings must be 0-100.")

    target.rating = new_rating
    results.append((new_rating, model.score()))

target.rating = original_rating
return results
```

def demonstrate_sensitivity_analysis() -> None:
model = SuccessFactorModel(
[
SuccessFactor("Leadership", 0.25, 70),
SuccessFactor("Stakeholders", 0.25, 70),
SuccessFactor("Risk", 0.25, 70),
SuccessFactor("Quality", 0.25, 70),
]
)

```
results = sensitivity_analysis(
    model,
    "Leadership",
    [50, 60, 70, 80, 90, 100],
)

print("\nSENSITIVITY ANALYSIS")
print("-" * 70)

for rating, score in results:
    print(
        f"Leadership rating={rating:>5.1f} "
        f"-> project score={score:>6.2f}"
    )
```

# ============================================================================

# 26. MONTE CARLO-STYLE SIMPLE SIMULATION

# ============================================================================

def run_project_outcome_simulation(
base_success_factors: Dict[str, float],
iterations: int = 10_000,
seed: int = 42,
) -> Dict[str, float]:
"""
Simple stochastic simulation using only the standard library.

```
Random variation models uncertainty around factor ratings.

This is not a validated statistical project-risk model. It is useful for
understanding why deterministic point estimates can hide uncertainty.
"""
import random

if iterations <= 0:
    raise ValueError("Iterations must be positive.")

random.seed(seed)

outcomes: List[float] = []

for _ in range(iterations):
    sampled_values = []

    for rating in base_success_factors.values():
        variation = random.gauss(0, 8)
        sampled_values.append(
            max(0.0, min(100.0, rating + variation))
        )

    outcomes.append(mean(sampled_values))

outcomes.sort()

def percentile(values: List[float], percentage: float) -> float:
    position = (len(values) - 1) * percentage / 100
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    fraction = position - lower
    return (
        values[lower]
        + (values[upper] - values[lower]) * fraction
    )

return {
    "mean": mean(outcomes),
    "p10": percentile(outcomes, 10),
    "p50": percentile(outcomes, 50),
    "p90": percentile(outcomes, 90),
}
```

def demonstrate_simulation() -> None:
result = run_project_outcome_simulation(
{
"Strategy": 85,
"Leadership": 80,
"Stakeholders": 75,
"Risk": 70,
"Team": 90,
}
)

```
print("\nUNCERTAINTY SIMULATION")
print("-" * 70)
print(f"P10 outcome index: {result['p10']:.2f}")
print(f"P50 outcome index: {result['p50']:.2f}")
print(f"P90 outcome index: {result['p90']:.2f}")
print(f"Mean outcome index: {result['mean']:.2f}")
```

# ============================================================================

# 27. CORRELATION BETWEEN FACTORS AND OUTCOMES

# ============================================================================

def pearson_correlation(
x_values: List[float],
y_values: List[float],
) -> float:
"""
Calculate Pearson correlation without external packages.

```
Correlation indicates association, not causation.
"""
if len(x_values) != len(y_values):
    raise ValueError("Both datasets must have equal length.")

if len(x_values) < 2:
    raise ValueError("At least two observations are required.")

x_mean = mean(x_values)
y_mean = mean(y_values)

numerator = sum(
    (x - x_mean) * (y - y_mean)
    for x, y in zip(x_values, y_values)
)

x_variation = sum((x - x_mean) ** 2 for x in x_values)
y_variation = sum((y - y_mean) ** 2 for y in y_values)

denominator = sqrt(x_variation * y_variation)

if denominator == 0:
    return 0.0

return numerator / denominator
```

def demonstrate_correlation() -> None:
stakeholder_engagement = [
40, 45, 50, 55, 60, 65, 70, 75, 80, 90
]

```
project_outcomes = [
    48, 51, 53, 59, 62, 68, 73, 77, 84, 91
]

correlation = pearson_correlation(
    stakeholder_engagement,
    project_outcomes,
)

print("\nFACTOR-OUTCOME CORRELATION")
print("-" * 70)
print(
    f"Stakeholder engagement / project outcome correlation: "
    f"{correlation:.3f}"
)

print(
    "Interpretation: correlation measures association. "
    "It does not establish that stakeholder engagement alone caused "
    "the observed project outcomes."
)
```

# ============================================================================

# 28. INTEGRATED PROJECT ASSESSMENT

# ============================================================================

@dataclass
class ProjectAssessment:
"""Comprehensive project assessment."""

```
name: str
success_factors: SuccessFactorModel
health: ProjectHealth
risks: RiskRegister
stakeholders: StakeholderRegister

def overall_index(self) -> float:
    """
    Integrated index combining complementary views.

    The components intentionally overlap to demonstrate that project
    success is multidimensional. In real organizations, weights should
    be calibrated to the portfolio and governance context.
    """
    factor_score = self.success_factors.score()
    health_score = self.health.score

    stakeholder_score = mean(
        stakeholder.current_support
        for stakeholder in self.stakeholders.stakeholders
    )

    risk_score = 100 - min(
        100,
        mean(
            risk.residual_score
            for risk in self.risks.risks
        ),
    )

    return (
        factor_score * 0.35
        + health_score * 0.35
        + stakeholder_score * 0.15
        + risk_score * 0.15
    )

def recommendations(self) -> List[str]:
    """
    Generate evidence-based improvement priorities.

    Recommendations are based on measurable weak points rather than
    generic project-management advice.
    """
    recommendations = []

    for factor in self.success_factors.weakest_factors(5):
        if factor.rating < 70:
            recommendations.append(
                f"Improve {factor.name} "
                f"(current rating: {factor.rating:.1f}%)."
            )

    weakest_name, weakest_value = self.health.weakest_dimension()

    if weakest_value < 70:
        recommendations.append(
            f"Investigate {weakest_name} performance "
            f"({weakest_value:.1f}%)."
        )

    high_risk_count = sum(
        risk.residual_score >= 50
        for risk in self.risks.risks
    )

    if high_risk_count:
        recommendations.append(
            f"Review {high_risk_count} high-residual-risk item(s)."
        )

    return recommendations
```

def demonstrate_integrated_assessment() -> None:
factors = SuccessFactorModel(
[
SuccessFactor("Objectives", 0.15, 92),
SuccessFactor("Stakeholders", 0.15, 74),
SuccessFactor("Leadership", 0.10, 85),
SuccessFactor("Requirements", 0.10, 80),
SuccessFactor("Planning", 0.10, 78),
SuccessFactor("Risk", 0.10, 62),
SuccessFactor("Team", 0.10, 90),
SuccessFactor("Communication", 0.10, 76),
SuccessFactor("Governance", 0.05, 72),
SuccessFactor("Benefits", 0.05, 58),
]
)

```
health = ProjectHealth(
    scope=90,
    schedule=74,
    cost=80,
    quality=93,
    risk=60,
    stakeholder=78,
    team=90,
    benefits=58,
)

risks = RiskRegister(
    [
        Risk(
            "Adoption failure",
            60,
            85,
            RiskResponse.MITIGATE,
            "Change lead",
            30,
        ),
        Risk(
            "Vendor delay",
            50,
            75,
            RiskResponse.MITIGATE,
            "Procurement",
            40,
        ),
    ]
)

stakeholders = StakeholderRegister(
    [
        Stakeholder("Sponsor", 95, 90, 90, 95),
        Stakeholder("Users", 50, 95, 65, 90),
        Stakeholder("Finance", 80, 60, 75, 80),
    ]
)

assessment = ProjectAssessment(
    "Enterprise Transformation",
    factors,
    health,
    risks,
    stakeholders,
)

print("\nINTEGRATED PROJECT ASSESSMENT")
print("-" * 70)
print(f"Project: {assessment.name}")
print(f"Integrated index: {assessment.overall_index():.2f}%")

print("\nPriority actions:")
for recommendation in assessment.recommendations():
    print(f"- {recommendation}")
```

# ============================================================================

# 29. EDGE CASES AND COMMON ERRORS

# ============================================================================

def demonstrate_edge_cases() -> None:
print("\nEDGE CASES")
print("-" * 70)

```
empty_scope = ScopeManager()

print(
    f"Empty project scope completion: "
    f"{empty_scope.completion_rate():.1f}%"
)

try:
    SuccessFactor("Invalid", 0.5, 120)
except ValueError as error:
    print(f"Caught invalid rating: {error}")

try:
    Risk("Invalid risk", 50, 50, RiskResponse.MITIGATE, "Owner", 110)
except ValueError as error:
    print(f"Caught invalid mitigation: {error}")

try:
    ProjectForecast(10_000_000, 0).estimate_at_completion
except ValueError as error:
    print(f"Caught invalid forecasting condition: {error}")

try:
    pearson_correlation([1], [2])
except ValueError as error:
    print(f"Caught insufficient correlation data: {error}")

print(
    "\nImportant edge cases include zero baselines, invalid percentages, "
    "empty project structures, missing owners, contradictory objectives, "
    "and metrics whose direction is not obvious."
)
```

# ============================================================================

# 30. TESTS

# ============================================================================

def run_tests() -> None:
"""Basic assertions demonstrating executable validation."""

```
criteria = SuccessCriteria(
    True, True, True, True, 100, 100, 100
)
assert criteria.traditional_score() == 100
assert criteria.modern_score() == 100

factor = SuccessFactor("Test", 1.0, 80)
model = SuccessFactorModel([factor])
assert model.score() == 80

risk = Risk(
    "Test risk",
    50,
    80,
    RiskResponse.MITIGATE,
    "Owner",
    50,
)
assert risk.inherent_score == 40
assert risk.residual_score == 20

evm = EarnedValueMetrics(100, 80, 90)
assert evm.schedule_variance == -20
assert evm.cost_variance == -10
assert evm.schedule_performance_index == 0.8
assert round(evm.cost_performance_index, 3) == 0.889

assert round(pearson_correlation([1, 2, 3], [1, 2, 3]), 3) == 1.0

health = ProjectHealth(
    100, 100, 100, 100, 100, 100, 100, 100
)
assert health.score == 100
assert health.status == ProjectStatus.HEALTHY

print("\nTESTS")
print("-" * 70)
print("All built-in tests passed.")
```

# ============================================================================

# 31. PRACTICAL PROJECT SUCCESS CHECKLIST

# ============================================================================

def project_success_checklist() -> None:
"""
Operational checklist.

```
A project should not be declared successful merely because its output
was delivered. Evaluation should include delivery, adoption, benefits,
stakeholder acceptance, and strategic alignment.
"""
checklist = {
    "Strategic alignment": True,
    "Clear measurable objectives": True,
    "Defined success criteria": True,
    "Scope baseline": True,
    "Realistic schedule": True,
    "Realistic budget": True,
    "Requirements traceability": True,
    "Stakeholder engagement": True,
    "Executive sponsorship": True,
    "Risk register": True,
    "Issue escalation process": True,
    "Quality controls": True,
    "Change control": True,
    "Governance": True,
    "Communication plan": True,
    "Benefits measurement": False,
    "Adoption measurement": False,
    "Post-delivery ownership": False,
}

completed = sum(checklist.values())
total = len(checklist)

print("\nPROJECT SUCCESS CHECKLIST")
print("-" * 70)

for item, complete in checklist.items():
    print(f"[{'X' if complete else ' '}] {item}")

print(
    f"\nReadiness: {completed}/{total} "
    f"({completed / total * 100:.1f}%)"
)
```

# ============================================================================

# 32. FINAL SYNTHESIS

# ============================================================================

def final_synthesis() -> None:
"""
Consolidated principles expressed as executable data.

```
These principles describe the causal logic behind project success.
"""

principles = [
    (
        "Define success before execution",
        "If success cannot be measured, project performance cannot "
        "be evaluated reliably."
    ),
    (
        "Connect projects to strategy",
        "A perfectly delivered project can still be a poor investment "
        "if it does not create meaningful strategic value."
    ),
    (
        "Engage stakeholders continuously",
        "Stakeholder acceptance and adoption determine whether outputs "
        "produce intended outcomes."
    ),
    (
        "Control scope deliberately",
        "Change should be evaluated rather than automatically rejected "
        "or automatically accepted."
    ),
    (
        "Manage uncertainty early",
        "Risk identification and treatment are generally more effective "
        "before threats become issues."
    ),
    (
        "Measure more than delivery constraints",
        "Schedule, cost, scope, and quality do not fully describe "
        "benefits, adoption, or strategic value."
    ),
    (
        "Treat leadership and governance as delivery mechanisms",
        "Decision rights, accountability, escalation, and sponsorship "
        "directly affect execution."
    ),
    (
        "Realize benefits after delivery",
        "The project may end before the business value is fully realized."
    ),
    (
        "Use evidence for decisions",
        "Metrics, trends, risks, forecasts, and stakeholder feedback "
        "provide stronger decision support than intuition alone."
    ),
]

print("\nCORE PROJECT SUCCESS PRINCIPLES")
print("-" * 70)

for principle, explanation in principles:
    print(f"\n{principle}")
    print(f"  {explanation}")
```

# ============================================================================

# 33. MAIN EXECUTION

# ============================================================================

def main() -> None:
"""Run the complete educational demonstration."""

```
print("=" * 78)
print("PROJECT SUCCESS: FACTORS THAT DETERMINE PROJECT SUCCESS")
print("=" * 78)

demonstrate_success_criteria()
demonstrate_success_factor_model()
distinguish_project_terms()
demonstrate_scope_management()
demonstrate_stakeholder_management()
communication_effectiveness_example()
demonstrate_risk_management()
demonstrate_issue_management()
demonstrate_quality_management()
demonstrate_schedule_management()
demonstrate_cost_management()
demonstrate_team_effectiveness()
demonstrate_governance()
demonstrate_change_control()
compare_delivery_approaches()
demonstrate_earned_value()
demonstrate_forecasting()
demonstrate_project_health()
demonstrate_root_cause_analysis()
demonstrate_dependencies()
demonstrate_failure_modes()
demonstrate_decision_analysis()
demonstrate_systemic_success()
demonstrate_sensitivity_analysis()
demonstrate_simulation()
demonstrate_correlation()
demonstrate_integrated_assessment()
demonstrate_edge_cases()
run_tests()
project_success_checklist()
final_synthesis()

print("\n" + "=" * 78)
print("END OF PROJECT SUCCESS STUDY SCRIPT")
print("=" * 78)
```

if **name** == "**main**":
main()

