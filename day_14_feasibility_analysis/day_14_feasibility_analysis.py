"""
Feasibility Analysis: Checking Whether a Project Is Practical
===============================================================

A standalone study script that teaches project feasibility analysis from
beginner to advanced level through executable Python examples.

The script covers:
- Meaning and purpose of feasibility analysis
- Feasibility dimensions
- Assumptions, constraints, requirements, and stakeholders
- Technical feasibility
- Operational feasibility
- Economic and financial feasibility
- Schedule feasibility
- Legal and regulatory feasibility
- Market feasibility
- Resource feasibility
- Risk and dependency analysis
- Weighted scoring models
- Cost-benefit analysis
- ROI, payback period, NPV, and IRR
- Break-even analysis
- Sensitivity analysis
- Scenario analysis
- Monte Carlo simulation
- Decision gates
- Evidence quality
- Common mistakes and biases
- Practical project feasibility assessment
- Testing and validation of the analysis
- A complete integrated feasibility model

Standard library only.
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple


# =============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# =============================================================================

def print_section(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_feasibility() -> None:
    print_section("1. What Is Feasibility Analysis?")

    print(
        "Feasibility analysis is a structured evaluation of whether a proposed "
        "project can realistically be completed and whether doing so is "
        "worthwhile under stated constraints."
    )

    print("\nA feasibility study usually asks:")
    questions = [
        "Can we build or deliver it technically?",
        "Can the organization operate and support it?",
        "Can we afford it and obtain an acceptable return?",
        "Can it be completed within the required schedule?",
        "Can we obtain the required people, facilities, technology, and suppliers?",
        "Will customers or users actually adopt it?",
        "Can it comply with applicable laws, contracts, standards, and policies?",
        "Are the risks acceptable?",
    ]
    for question in questions:
        print(f"- {question}")

    print(
        "\nFeasibility is not the same as desirability. A project may be "
        "technically possible but economically unattractive. It may also be "
        "profitable but impossible to deliver within the required deadline."
    )


# =============================================================================
# 2. CORE DATA STRUCTURES
# =============================================================================

class EvidenceQuality(Enum):
    """Simple classification of evidence supporting a feasibility assumption."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Decision(Enum):
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL GO"
    NO_GO = "NO-GO"


@dataclass
class Assumption:
    """An assumption used by a feasibility model."""

    name: str
    value: object
    evidence_quality: EvidenceQuality
    rationale: str = ""


@dataclass
class Constraint:
    """A project constraint that restricts feasible solutions."""

    name: str
    description: str
    hard_constraint: bool = True


@dataclass
class FeasibilityCriterion:
    """
    A criterion used in a weighted feasibility score.

    score is normally between 0 and 100.
    weight is a relative importance value.
    """

    name: str
    score: float
    weight: float
    rationale: str = ""

    def validate(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError(f"Score for {self.name} must be between 0 and 100.")
        if self.weight < 0:
            raise ValueError(f"Weight for {self.name} cannot be negative.")


@dataclass
class CashFlow:
    """Cash-flow value associated with a particular period."""

    period: int
    amount: float


@dataclass
class Risk:
    """Risk record used by a qualitative risk model."""

    name: str
    probability: float
    impact: float
    mitigation: str = ""

    def expected_loss(self) -> float:
        return self.probability * self.impact


@dataclass
class ProjectFeasibility:
    """Integrated result of several feasibility dimensions."""

    technical: float
    operational: float
    economic: float
    schedule: float
    market: float
    legal: float
    resource: float
    risk: float

    def average_score(self) -> float:
        values = [
            self.technical,
            self.operational,
            self.economic,
            self.schedule,
            self.market,
            self.legal,
            self.resource,
            self.risk,
        ]
        return statistics.mean(values)

    def minimum_score(self) -> float:
        return min(
            self.technical,
            self.operational,
            self.economic,
            self.schedule,
            self.market,
            self.legal,
            self.resource,
            self.risk,
        )


# =============================================================================
# 3. REQUIREMENTS, ASSUMPTIONS, AND CONSTRAINTS
# =============================================================================

def requirements_example() -> None:
    print_section("2. Requirements, Assumptions, and Constraints")

    requirements = {
        "functional": [
            "Users can create accounts.",
            "Users can submit applications.",
            "Managers can review applications.",
        ],
        "non_functional": [
            "The system should support 10,000 concurrent users.",
            "Normal API responses should generally be below 500 ms.",
            "Sensitive information must be protected.",
        ],
    }

    assumptions = [
        Assumption(
            "Development team availability",
            "5 engineers",
            EvidenceQuality.HIGH,
            "Confirmed staffing plan.",
        ),
        Assumption(
            "Expected initial users",
            10000,
            EvidenceQuality.MEDIUM,
            "Based on preliminary demand estimates.",
        ),
        Assumption(
            "Cloud infrastructure cost",
            2500,
            EvidenceQuality.LOW,
            "Early vendor estimate.",
        ),
    ]

    constraints = [
        Constraint(
            "Budget",
            "Initial implementation budget cannot exceed ₹50 lakh."
        ),
        Constraint(
            "Deadline",
            "Pilot must be operational within six months."
        ),
        Constraint(
            "Compliance",
            "Required privacy and security controls must be implemented."
        ),
    ]

    print("Functional requirements:")
    for item in requirements["functional"]:
        print(f"  - {item}")

    print("\nNon-functional requirements:")
    for item in requirements["non_functional"]:
        print(f"  - {item}")

    print("\nAssumptions:")
    for assumption in assumptions:
        print(
            f"  - {assumption.name}: {assumption.value} "
            f"[evidence={assumption.evidence_quality.value}]"
        )

    print("\nConstraints:")
    for constraint in constraints:
        print(
            f"  - {constraint.name}: {constraint.description} "
            f"[hard={constraint.hard_constraint}]"
        )


# =============================================================================
# 4. TECHNICAL FEASIBILITY
# =============================================================================

def technical_feasibility_score(
    required_capabilities: Sequence[str],
    available_capabilities: Sequence[str],
) -> float:
    """
    Calculate a simple technical capability coverage score.

    This is a teaching model. Real technical feasibility normally requires
    architecture experiments, prototypes, capacity tests, security analysis,
    integration tests, and engineering estimates.
    """
    required = {item.lower() for item in required_capabilities}
    available = {item.lower() for item in available_capabilities}

    if not required:
        return 100.0

    covered = required.intersection(available)
    return len(covered) / len(required) * 100


def technical_feasibility_example() -> None:
    print_section("3. Technical Feasibility")

    required = [
        "REST API",
        "PostgreSQL",
        "Authentication",
        "Cloud deployment",
        "Real-time notifications",
        "Automated testing",
    ]

    available = [
        "REST API",
        "PostgreSQL",
        "Authentication",
        "Cloud deployment",
        "Automated testing",
    ]

    score = technical_feasibility_score(required, available)

    print(f"Required technical capabilities: {len(required)}")
    print(f"Available capabilities: {len(available)}")
    print(f"Capability coverage: {score:.1f}%")

    print(
        "\nA missing capability does not automatically mean the project is "
        "infeasible. It means the missing capability requires investigation, "
        "acquisition, prototyping, outsourcing, or architectural change."
    )

    technical_questions = [
        "Does the required technology exist and meet requirements?",
        "Can the team integrate the necessary systems?",
        "Can expected traffic and data volumes be handled?",
        "Are reliability and security requirements achievable?",
        "Are there unacceptable technology dependencies?",
        "Can the architecture be maintained after launch?",
    ]

    print("\nTechnical feasibility questions:")
    for question in technical_questions:
        print(f"- {question}")


# =============================================================================
# 5. OPERATIONAL FEASIBILITY
# =============================================================================

def operational_readiness_score(
    process_fit: float,
    user_acceptance: float,
    support_capacity: float,
    change_readiness: float,
) -> float:
    """Calculate an equally weighted operational readiness score."""
    values = [
        process_fit,
        user_acceptance,
        support_capacity,
        change_readiness,
    ]

    if any(not 0 <= value <= 100 for value in values):
        raise ValueError("Operational scores must be between 0 and 100.")

    return statistics.mean(values)


def operational_feasibility_example() -> None:
    print_section("4. Operational Feasibility")

    score = operational_readiness_score(
        process_fit=85,
        user_acceptance=70,
        support_capacity=80,
        change_readiness=65,
    )

    print(f"Operational readiness score: {score:.1f}/100")

    print("\nOperational feasibility considers whether the organization can:")
    for item in [
        "Adopt the new process.",
        "Train affected users.",
        "Operate the solution after implementation.",
        "Provide customer and technical support.",
        "Maintain required processes and controls.",
        "Handle organizational change.",
    ]:
        print(f"- {item}")


# =============================================================================
# 6. ECONOMIC AND FINANCIAL FEASIBILITY
# =============================================================================

def roi_percentage(total_benefits: float, total_costs: float) -> float:
    """
    Simple ROI.

    ROI = (Benefits - Costs) / Costs × 100
    """
    if total_costs <= 0:
        raise ValueError("Total costs must be greater than zero.")

    return (total_benefits - total_costs) / total_costs * 100


def benefit_cost_ratio(total_benefits: float, total_costs: float) -> float:
    """Benefit-cost ratio = total benefits / total costs."""
    if total_costs <= 0:
        raise ValueError("Total costs must be greater than zero.")
    return total_benefits / total_costs


def payback_period(
    initial_investment: float,
    annual_cash_flows: Sequence[float],
) -> Optional[float]:
    """
    Estimate payback period.

    Returns the fractional period in which cumulative cash flow becomes
    non-negative. Returns None if the investment is not recovered.
    """
    if initial_investment < 0:
        raise ValueError("Initial investment cannot be negative.")

    remaining = initial_investment

    for index, cash_flow in enumerate(annual_cash_flows, start=1):
        if cash_flow <= 0:
            remaining -= cash_flow
            continue

        if cash_flow >= remaining:
            fraction = remaining / cash_flow
            return (index - 1) + fraction

        remaining -= cash_flow

    return None


def npv(
    discount_rate: float,
    cash_flows: Sequence[float],
) -> float:
    """
    Calculate net present value.

    cash_flows[0] is period 0.
    """
    if discount_rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")

    return sum(
        cash_flow / ((1 + discount_rate) ** period)
        for period, cash_flow in enumerate(cash_flows)
    )


def irr(
    cash_flows: Sequence[float],
    lower: float = -0.9999,
    upper: float = 10.0,
    tolerance: float = 1e-8,
    max_iterations: int = 1000,
) -> Optional[float]:
    """
    Estimate IRR using bisection.

    The function assumes there is a root within [lower, upper].
    It returns None when the interval does not bracket a root.

    IRR can have multiple mathematical roots for cash-flow streams with
    multiple sign changes, so this simple implementation is intentionally
    conservative.
    """
    if not cash_flows:
        return None

    def value(rate: float) -> float:
        return npv(rate, cash_flows)

    low_value = value(lower)
    high_value = value(upper)

    if abs(low_value) < tolerance:
        return lower

    if abs(high_value) < tolerance:
        return upper

    if low_value * high_value > 0:
        return None

    low = lower
    high = upper

    for _ in range(max_iterations):
        middle = (low + high) / 2
        middle_value = value(middle)

        if abs(middle_value) < tolerance:
            return middle

        if low_value * middle_value <= 0:
            high = middle
            high_value = middle_value
        else:
            low = middle
            low_value = middle_value

    return (low + high) / 2


def break_even_units(
    fixed_costs: float,
    selling_price_per_unit: float,
    variable_cost_per_unit: float,
) -> float:
    """
    Calculate the number of units required to break even.
    """
    contribution_margin = selling_price_per_unit - variable_cost_per_unit

    if contribution_margin <= 0:
        raise ValueError(
            "Selling price must exceed variable cost for a finite break-even."
        )

    return fixed_costs / contribution_margin


def financial_feasibility_example() -> None:
    print_section("5. Economic and Financial Feasibility")

    total_costs = 4_000_000
    total_benefits = 6_500_000

    roi = roi_percentage(total_benefits, total_costs)
    bcr = benefit_cost_ratio(total_benefits, total_costs)

    annual_cash_flows = [1_000_000, 1_500_000, 2_000_000, 2_500_000]
    payback = payback_period(total_costs, annual_cash_flows)

    discounted_cash_flows = [
        -4_000_000,
        1_000_000,
        1_500_000,
        2_000_000,
        2_500_000,
    ]

    project_npv = npv(0.10, discounted_cash_flows)
    project_irr = irr(discounted_cash_flows)

    break_even = break_even_units(
        fixed_costs=1_000_000,
        selling_price_per_unit=1000,
        variable_cost_per_unit=400,
    )

    print(f"Simple ROI: {roi:.2f}%")
    print(f"Benefit-cost ratio: {bcr:.2f}")

    if payback is None:
        print("Payback period: not recovered")
    else:
        print(f"Payback period: {payback:.2f} years")

    print(f"NPV at 10% discount rate: ₹{project_npv:,.2f}")

    if project_irr is None:
        print("IRR: no root found in the tested interval")
    else:
        print(f"IRR: {project_irr * 100:.2f}%")

    print(f"Break-even volume: {break_even:,.0f} units")


# =============================================================================
# 7. SCHEDULE FEASIBILITY
# =============================================================================

@dataclass
class Task:
    """Task used for a simple critical-path calculation."""

    name: str
    duration: float
    dependencies: List[str] = field(default_factory=list)


def critical_path(tasks: Sequence[Task]) -> Tuple[float, List[str]]:
    """
    Calculate a simple critical path using recursive longest-path logic.

    Assumptions:
    - No circular dependencies.
    - Task names are unique.
    - Duration is non-negative.
    """
    task_map = {task.name: task for task in tasks}

    if len(task_map) != len(tasks):
        raise ValueError("Task names must be unique.")

    for task in tasks:
        if task.duration < 0:
            raise ValueError("Task duration cannot be negative.")

        for dependency in task.dependencies:
            if dependency not in task_map:
                raise ValueError(
                    f"Task '{task.name}' depends on unknown task '{dependency}'."
                )

    cache: Dict[str, Tuple[float, List[str]]] = {}
    visiting = set()

    def longest_path(task_name: str) -> Tuple[float, List[str]]:
        if task_name in cache:
            return cache[task_name]

        if task_name in visiting:
            raise ValueError("Circular dependency detected.")

        visiting.add(task_name)
        task = task_map[task_name]

        if not task.dependencies:
            result = (task.duration, [task.name])
        else:
            predecessor = max(
                (longest_path(dep) for dep in task.dependencies),
                key=lambda item: item[0],
            )
            result = (
                predecessor[0] + task.duration,
                predecessor[1] + [task.name],
            )

        visiting.remove(task_name)
        cache[task_name] = result
        return result

    return max(
        (longest_path(task.name) for task in tasks),
        key=lambda item: item[0],
    )


def schedule_feasibility_example() -> None:
    print_section("6. Schedule Feasibility and Critical Path")

    tasks = [
        Task("Requirements", 3),
        Task("Architecture", 2, ["Requirements"]),
        Task("Backend", 6, ["Architecture"]),
        Task("Frontend", 5, ["Architecture"]),
        Task("Integration", 3, ["Backend", "Frontend"]),
        Task("Testing", 4, ["Integration"]),
        Task("Deployment", 2, ["Testing"]),
    ]

    duration, path = critical_path(tasks)

    print(f"Estimated critical-path duration: {duration:.1f} weeks")
    print("Critical path:")
    print(" -> ".join(path))

    deadline = 24

    print(f"Required deadline: {deadline} weeks")

    if duration <= deadline:
        print("Schedule assessment: feasible under the current estimate.")
    else:
        print("Schedule assessment: infeasible unless the plan changes.")

    print(
        "\nA schedule can be technically possible but practically infeasible "
        "when the critical path exceeds the required deadline."
    )


# =============================================================================
# 8. RESOURCE FEASIBILITY
# =============================================================================

def resource_utilization(
    required_hours: float,
    available_hours: float,
) -> float:
    """Return resource utilization as a percentage."""
    if available_hours <= 0:
        raise ValueError("Available hours must be greater than zero.")

    return required_hours / available_hours * 100


def resource_feasibility_example() -> None:
    print_section("7. Resource Feasibility")

    required_hours = 720
    available_hours = 800

    utilization = resource_utilization(required_hours, available_hours)

    print(f"Required labor: {required_hours:.0f} hours")
    print(f"Available labor: {available_hours:.0f} hours")
    print(f"Planned utilization: {utilization:.1f}%")

    if utilization <= 100:
        print("Resource capacity: feasible in pure capacity terms.")
    else:
        print("Resource capacity: insufficient.")

    print(
        "\nCapacity feasibility should not be interpreted as unlimited "
        "availability. Staff need time for meetings, support, defects, "
        "training, leave, coordination, and unexpected work."
    )


# =============================================================================
# 9. MARKET FEASIBILITY
# =============================================================================

def serviceable_market_revenue(
    target_population: int,
    adoption_rate: float,
    annual_revenue_per_customer: float,
) -> float:
    """Estimate revenue from a target population."""
    if target_population < 0:
        raise ValueError("Population cannot be negative.")

    if not 0 <= adoption_rate <= 1:
        raise ValueError("Adoption rate must be between 0 and 1.")

    if annual_revenue_per_customer < 0:
        raise ValueError("Revenue per customer cannot be negative.")

    customers = target_population * adoption_rate
    return customers * annual_revenue_per_customer


def market_feasibility_example() -> None:
    print_section("8. Market Feasibility")

    target_population = 500_000
    expected_adoption = 0.02
    annual_revenue_per_customer = 1200

    estimated_revenue = serviceable_market_revenue(
        target_population,
        expected_adoption,
        annual_revenue_per_customer,
    )

    print(f"Target population: {target_population:,}")
    print(f"Assumed adoption: {expected_adoption * 100:.1f}%")
    print(f"Estimated customers: {target_population * expected_adoption:,.0f}")
    print(f"Estimated annual revenue: ₹{estimated_revenue:,.2f}")

    print("\nMarket feasibility should investigate:")
    for item in [
        "Problem severity",
        "Customer willingness to pay",
        "Market size",
        "Competition",
        "Customer acquisition cost",
        "Retention",
        "Pricing",
        "Distribution",
        "Substitutes",
        "Regulatory barriers",
    ]:
        print(f"- {item}")


# =============================================================================
# 10. LEGAL AND REGULATORY FEASIBILITY
# =============================================================================

def compliance_gate(
    mandatory_requirements: Sequence[bool],
) -> bool:
    """
    A conservative legal/compliance gate.

    Every mandatory requirement must be satisfied.
    """
    return all(mandatory_requirements)


def legal_feasibility_example() -> None:
    print_section("9. Legal and Regulatory Feasibility")

    mandatory_controls = {
        "Required license identified": True,
        "Contractual restrictions reviewed": True,
        "Privacy requirements addressed": True,
        "Security obligations addressed": True,
        "Industry-specific requirements addressed": False,
    }

    feasible = compliance_gate(list(mandatory_controls.values()))

    for requirement, status in mandatory_controls.items():
        print(f"{'PASS' if status else 'FAIL'}: {requirement}")

    print(f"\nLegal/compliance gate: {'PASS' if feasible else 'FAIL'}")

    print(
        "\nLegal feasibility should not be reduced to a weighted average when "
        "a particular legal requirement is mandatory. A single mandatory "
        "failure can block the project until corrected."
    )


# =============================================================================
# 11. WEIGHTED FEASIBILITY SCORING
# =============================================================================

def weighted_score(criteria: Sequence[FeasibilityCriterion]) -> float:
    """Calculate a weighted average score."""
    if not criteria:
        raise ValueError("At least one criterion is required.")

    for criterion in criteria:
        criterion.validate()

    total_weight = sum(item.weight for item in criteria)

    if total_weight <= 0:
        raise ValueError("Total weight must be greater than zero.")

    return sum(
        item.score * item.weight for item in criteria
    ) / total_weight


def weighted_score_example() -> None:
    print_section("10. Weighted Feasibility Score")

    criteria = [
        FeasibilityCriterion(
            "Technical", 85, 0.20, "Most required technology is available."
        ),
        FeasibilityCriterion(
            "Operational", 72, 0.15, "Moderate organizational change required."
        ),
        FeasibilityCriterion(
            "Economic", 78, 0.20, "Positive expected economics."
        ),
        FeasibilityCriterion(
            "Schedule", 65, 0.15, "Deadline is achievable but tight."
        ),
        FeasibilityCriterion(
            "Market", 80, 0.10, "Demand evidence is reasonably strong."
        ),
        FeasibilityCriterion(
            "Legal", 90, 0.10, "Most compliance requirements are understood."
        ),
        FeasibilityCriterion(
            "Resources", 75, 0.10, "Required staff can be allocated."
        ),
    ]

    score = weighted_score(criteria)

    print("Criterion scores:")
    for criterion in criteria:
        print(
            f"- {criterion.name:12s}: score={criterion.score:5.1f}, "
            f"weight={criterion.weight:.2f}"
        )

    print(f"\nWeighted feasibility score: {score:.2f}/100")

    if score >= 80:
        decision = Decision.GO
    elif score >= 60:
        decision = Decision.CONDITIONAL_GO
    else:
        decision = Decision.NO_GO

    print(f"Indicative decision: {decision.value}")

    print(
        "\nA weighted score is a decision-support mechanism, not proof of "
        "feasibility. Mandatory constraints and high-severity risks should "
        "be treated separately."
    )


# =============================================================================
# 12. HARD GATES AND SOFT SCORES
# =============================================================================

def gated_decision(
    weighted_feasibility: float,
    hard_gates: Sequence[bool],
    minimum_dimension_score: float,
    dimension_scores: Sequence[float],
) -> Decision:
    """
    Combine weighted scoring with hard constraints.

    A project cannot receive GO when a mandatory gate fails or when a critical
    dimension is below the minimum acceptable level.
    """
    if not hard_gates:
        raise ValueError("At least one hard gate is required.")

    if any(not isinstance(gate, bool) for gate in hard_gates):
        raise ValueError("Hard gates must be Boolean.")

    if not dimension_scores:
        raise ValueError("Dimension scores cannot be empty.")

    if not all(0 <= score <= 100 for score in dimension_scores):
        raise ValueError("Dimension scores must be between 0 and 100.")

    if not 0 <= minimum_dimension_score <= 100:
        raise ValueError("Minimum dimension score must be between 0 and 100.")

    if not all(hard_gates):
        return Decision.NO_GO

    if min(dimension_scores) < minimum_dimension_score:
        return Decision.CONDITIONAL_GO

    if weighted_feasibility >= 80:
        return Decision.GO

    if weighted_feasibility >= 60:
        return Decision.CONDITIONAL_GO

    return Decision.NO_GO


def hard_gate_example() -> None:
    print_section("11. Hard Constraints Versus Weighted Scores")

    weighted = 84
    gates = [True, True, False]

    dimension_scores = [90, 88, 82, 79, 85]

    decision = gated_decision(
        weighted_feasibility=weighted,
        hard_gates=gates,
        minimum_dimension_score=60,
        dimension_scores=dimension_scores,
    )

    print(f"Weighted score: {weighted}")
    print(f"Hard gates: {gates}")
    print(f"Decision: {decision.value}")

    print(
        "\nThis demonstrates why averaging everything into one number can be "
        "dangerous. A high score cannot compensate for an unmet mandatory "
        "regulatory or safety requirement."
    )


# =============================================================================
# 13. RISK ANALYSIS
# =============================================================================

def risk_score(probability: float, impact: float) -> float:
    """
    Simple risk exposure score.

    Probability and impact are expressed from 0 to 1.
    """
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1.")

    if impact < 0:
        raise ValueError("Impact cannot be negative.")

    return probability * impact


def classify_risk(score: float) -> str:
    """Classify normalized risk exposure."""
    if score < 0.10:
        return "Low"
    if score < 0.25:
        return "Medium"
    if score < 0.50:
        return "High"
    return "Very High"


def risk_analysis_example() -> None:
    print_section("12. Risk Analysis")

    risks = [
        Risk(
            "Vendor integration failure",
            probability=0.20,
            impact=800_000,
            mitigation="Prototype integration before full implementation.",
        ),
        Risk(
            "Lower-than-expected adoption",
            probability=0.30,
            impact=1_200_000,
            mitigation="Validate demand with a pilot.",
        ),
        Risk(
            "Critical staff departure",
            probability=0.15,
            impact=500_000,
            mitigation="Cross-train team members.",
        ),
    ]

    total_expected_loss = 0.0

    for risk in risks:
        expected_loss = risk.expected_loss()
        total_expected_loss += expected_loss

        normalized = risk_score(
            risk.probability,
            min(risk.impact / 1_500_000, 1.0),
        )

        print(f"\nRisk: {risk.name}")
        print(f"  Probability: {risk.probability:.0%}")
        print(f"  Financial impact: ₹{risk.impact:,.0f}")
        print(f"  Expected loss: ₹{expected_loss:,.0f}")
        print(f"  Risk class: {classify_risk(normalized)}")
        print(f"  Mitigation: {risk.mitigation}")

    print(f"\nTotal modeled expected loss: ₹{total_expected_loss:,.0f}")

    print(
        "\nExpected loss is useful for prioritization, but it does not capture "
        "every form of uncertainty. Reputation, safety, legal exposure, "
        "strategic consequences, and correlated risks may be difficult to "
        "express as a single monetary value."
    )


# =============================================================================
# 14. UNCERTAINTY AND CONFIDENCE
# =============================================================================

def confidence_adjusted_value(
    estimated_value: float,
    confidence: float,
) -> float:
    """Apply a simple confidence adjustment to an estimate."""
    if estimated_value < 0:
        raise ValueError("Estimated value cannot be negative.")

    if not 0 <= confidence <= 1:
        raise ValueError("Confidence must be between 0 and 1.")

    return estimated_value * confidence


def evidence_quality_example() -> None:
    print_section("13. Evidence Quality and Uncertainty")

    estimates = [
        ("Customer demand", 10_000, 0.60),
        ("Development productivity", 12_000, 0.80),
        ("Infrastructure cost", 300_000, 0.70),
    ]

    for name, estimate, confidence in estimates:
        adjusted = confidence_adjusted_value(estimate, confidence)
        print(
            f"{name:28s}: estimate={estimate:,.0f}, "
            f"confidence={confidence:.0%}, adjusted={adjusted:,.0f}"
        )

    print(
        "\nConfidence should not be treated as a mathematically precise truth "
        "unless it has been derived from a defensible statistical model. In "
        "early feasibility studies, it is often better viewed as a disciplined "
        "way to communicate evidence strength."
    )


# =============================================================================
# 15. SENSITIVITY ANALYSIS
# =============================================================================

def project_profit(
    customers: int,
    revenue_per_customer: float,
    variable_cost_per_customer: float,
    fixed_cost: float,
) -> float:
    """Calculate project operating profit."""
    return (
        customers * revenue_per_customer
        - customers * variable_cost_per_customer
        - fixed_cost
    )


def one_way_sensitivity_example() -> None:
    print_section("14. One-Way Sensitivity Analysis")

    baseline = {
        "customers": 10_000,
        "revenue_per_customer": 1000.0,
        "variable_cost_per_customer": 400.0,
        "fixed_cost": 4_000_000.0,
    }

    baseline_profit = project_profit(**baseline)

    print(f"Baseline profit: ₹{baseline_profit:,.0f}")

    for variable in [
        "customers",
        "revenue_per_customer",
        "variable_cost_per_customer",
        "fixed_cost",
    ]:
        print(f"\nSensitivity of {variable}:")

        for multiplier in [0.75, 0.90, 1.00, 1.10, 1.25]:
            scenario = baseline.copy()
            scenario[variable] *= multiplier

            profit = project_profit(**scenario)

            print(
                f"  {multiplier:>5.0%} of baseline -> "
                f"profit ₹{profit:>12,.0f}"
            )

    print(
        "\nSensitivity analysis identifies which assumptions have the greatest "
        "influence on the decision. It does not estimate how likely each "
        "change is."
    )


# =============================================================================
# 16. SCENARIO ANALYSIS
# =============================================================================

def scenario_analysis_example() -> None:
    print_section("15. Scenario Analysis")

    scenarios = {
        "Pessimistic": {
            "customers": 6_000,
            "price": 850,
            "variable_cost": 450,
            "fixed_cost": 4_500_000,
        },
        "Base": {
            "customers": 10_000,
            "price": 1000,
            "variable_cost": 400,
            "fixed_cost": 4_000_000,
        },
        "Optimistic": {
            "customers": 15_000,
            "price": 1100,
            "variable_cost": 350,
            "fixed_cost": 4_200_000,
        },
    }

    for name, scenario in scenarios.items():
        profit = project_profit(
            customers=scenario["customers"],
            revenue_per_customer=scenario["price"],
            variable_cost_per_customer=scenario["variable_cost"],
            fixed_cost=scenario["fixed_cost"],
        )

        print(f"{name:12s}: profit = ₹{profit:,.0f}")

    print(
        "\nScenario analysis changes several assumptions together. This is "
        "useful when assumptions move as a coherent business situation."
    )


# =============================================================================
# 17. MONTE CARLO SIMULATION
# =============================================================================

def monte_carlo_profit(
    iterations: int,
    customer_range: Tuple[int, int],
    price_range: Tuple[float, float],
    variable_cost_range: Tuple[float, float],
    fixed_cost_range: Tuple[float, float],
    seed: int = 42,
) -> List[float]:
    """
    Run a simple Monte Carlo simulation using uniform distributions.

    Uniform distributions are used here for transparency. Real models should
    select distributions based on empirical evidence or expert assumptions.
    """
    if iterations <= 0:
        raise ValueError("Iterations must be positive.")

    if seed is not None:
        random.seed(seed)

    results = []

    for _ in range(iterations):
        customers = random.uniform(*customer_range)
        price = random.uniform(*price_range)
        variable_cost = random.uniform(*variable_cost_range)
        fixed_cost = random.uniform(*fixed_cost_range)

        profit = project_profit(
            int(customers),
            price,
            variable_cost,
            fixed_cost,
        )

        results.append(profit)

    return results


def percentile(values: Sequence[float], percentage: float) -> float:
    """Calculate a simple interpolated percentile."""
    if not values:
        raise ValueError("Cannot calculate a percentile of an empty sequence.")

    if not 0 <= percentage <= 100:
        raise ValueError("Percentage must be between 0 and 100.")

    sorted_values = sorted(values)

    position = (len(sorted_values) - 1) * percentage / 100
    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return sorted_values[lower_index]

    fraction = position - lower_index

    return (
        sorted_values[lower_index] * (1 - fraction)
        + sorted_values[upper_index] * fraction
    )


def monte_carlo_example() -> None:
    print_section("16. Monte Carlo Feasibility Analysis")

    profits = monte_carlo_profit(
        iterations=10_000,
        customer_range=(6_000, 15_000),
        price_range=(800, 1200),
        variable_cost_range=(300, 500),
        fixed_cost_range=(3_500_000, 5_000_000),
    )

    probability_of_loss = sum(profit < 0 for profit in profits) / len(profits)

    print(f"Simulations: {len(profits):,}")
    print(f"Mean profit: ₹{statistics.mean(profits):,.0f}")
    print(f"Median profit: ₹{statistics.median(profits):,.0f}")
    print(f"5th percentile: ₹{percentile(profits, 5):,.0f}")
    print(f"95th percentile: ₹{percentile(profits, 95):,.0f}")
    print(f"Probability of loss: {probability_of_loss:.2%}")

    print(
        "\nMonte Carlo simulation models a distribution of outcomes rather "
        "than producing one deterministic forecast. Its quality depends "
        "heavily on the quality of the input distributions and relationships "
        "between variables."
    )


# =============================================================================
# 18. DECISION TREES
# =============================================================================

@dataclass
class DecisionOutcome:
    """A probabilistic outcome in a simple decision tree."""

    name: str
    probability: float
    value: float


def expected_value(outcomes: Sequence[DecisionOutcome]) -> float:
    """Calculate expected value of mutually exclusive outcomes."""
    if not outcomes:
        raise ValueError("At least one outcome is required.")

    total_probability = sum(item.probability for item in outcomes)

    if not math.isclose(total_probability, 1.0, abs_tol=1e-9):
        raise ValueError("Outcome probabilities must sum to 1.")

    if any(item.probability < 0 for item in outcomes):
        raise ValueError("Probabilities cannot be negative.")

    return sum(item.probability * item.value for item in outcomes)


def decision_tree_example() -> None:
    print_section("17. Decision Trees and Expected Value")

    build_now = [
        DecisionOutcome("High demand", 0.40, 3_000_000),
        DecisionOutcome("Moderate demand", 0.40, 1_000_000),
        DecisionOutcome("Low demand", 0.20, -2_000_000),
    ]

    delay_and_validate = [
        DecisionOutcome("High demand", 0.50, 2_500_000),
        DecisionOutcome("Moderate demand", 0.35, 800_000),
        DecisionOutcome("Low demand", 0.15, -500_000),
    ]

    value_build_now = expected_value(build_now)
    value_delay = expected_value(delay_and_validate)

    print(f"Expected value of building now: ₹{value_build_now:,.0f}")
    print(f"Expected value of delayed validation: ₹{value_delay:,.0f}")

    preferred = (
        "Build now"
        if value_build_now > value_delay
        else "Delay and validate"
    )

    print(f"Preferred option under this model: {preferred}")


# =============================================================================
# 19. OPTIONS AND PHASED INVESTMENT
# =============================================================================

def phased_investment_example() -> None:
    print_section("18. Phased Feasibility and Real Options")

    phases = [
        ("Discovery", 200_000),
        ("Prototype", 500_000),
        ("Pilot", 1_000_000),
        ("Full rollout", 4_000_000),
    ]

    cumulative = 0

    for phase, cost in phases:
        cumulative += cost
        print(f"{phase:16s}: phase cost ₹{cost:,.0f}, cumulative ₹{cumulative:,.0f}")

    print(
        "\nPhased investment can reduce uncertainty before committing the "
        "entire budget. A prototype or pilot may create an option to stop, "
        "redesign, or scale based on evidence."
    )


# =============================================================================
# 20. FEASIBILITY VERSUS VIABILITY AND DESIRABILITY
# =============================================================================

def feasibility_viability_comparison() -> None:
    print_section("19. Feasibility, Viability, and Desirability")

    comparison = [
        (
            "Feasibility",
            "Can it realistically be delivered under the constraints?"
        ),
        (
            "Viability",
            "Can it create sufficient economic or strategic value?"
        ),
        (
            "Desirability",
            "Do users or stakeholders actually want it?"
        ),
    ]

    for concept, question in comparison:
        print(f"{concept:14s}: {question}")

    examples = [
        ("Feasible but not viable", "Can be built, but costs more than it can earn."),
        ("Viable but not feasible", "Economics are attractive, but required technology is unavailable."),
        ("Feasible and viable but undesirable", "Profitable to deliver, but users do not want it."),
    ]

    print("\nImportant combinations:")
    for label, explanation in examples:
        print(f"- {label}: {explanation}")


# =============================================================================
# 21. COST ESTIMATION AND CONTINGENCY
# =============================================================================

def estimate_with_contingency(
    base_estimate: float,
    contingency_rate: float,
) -> float:
    """Add contingency to a base estimate."""
    if base_estimate < 0:
        raise ValueError("Base estimate cannot be negative.")

    if contingency_rate < 0:
        raise ValueError("Contingency rate cannot be negative.")

    return base_estimate * (1 + contingency_rate)


def cost_estimation_example() -> None:
    print_section("20. Cost Estimation and Contingency")

    cost_components = {
        "Engineering": 2_000_000,
        "Design": 500_000,
        "Infrastructure": 600_000,
        "Testing": 400_000,
        "Training": 300_000,
        "Legal and compliance": 200_000,
    }

    base = sum(cost_components.values())
    estimated_total = estimate_with_contingency(base, 0.15)

    for component, cost in cost_components.items():
        print(f"{component:24s}: ₹{cost:,.0f}")

    print(f"\nBase estimate: ₹{base:,.0f}")
    print(f"15% contingency estimate: ₹{estimated_total:,.0f}")

    print(
        "\nContingency is not a substitute for risk analysis. It is a budget "
        "provision for uncertainty. Double-counting contingency and explicit "
        "risk costs can inflate estimates."
    )


# =============================================================================
# 22. DEPENDENCY ANALYSIS
# =============================================================================

def dependency_analysis_example() -> None:
    print_section("21. Dependency Analysis")

    dependencies = {
        "Payment integration": [
            "Payment provider approval",
            "API credentials",
            "Security review",
        ],
        "Mobile launch": [
            "Production API",
            "App-store compliance",
            "Release signing",
        ],
        "Analytics": [
            "Event schema",
            "Data pipeline",
            "Dashboard infrastructure",
        ],
    }

    for deliverable, required_dependencies in dependencies.items():
        print(f"\n{deliverable}:")
        for dependency in required_dependencies:
            print(f"  -> {dependency}")

    print(
        "\nA project may fail despite having enough money and staff if a "
        "critical external dependency cannot be obtained on time."
    )


# =============================================================================
# 23. FEASIBILITY MATRIX
# =============================================================================

def build_feasibility_matrix(
    dimensions: Dict[str, float],
) -> List[Tuple[str, float, str]]:
    """
    Convert dimension scores into a simple qualitative matrix.
    """
    result = []

    for name, score in dimensions.items():
        if not 0 <= score <= 100:
            raise ValueError(f"{name} must be between 0 and 100.")

        if score >= 80:
            status = "Strong"
        elif score >= 60:
            status = "Moderate"
        else:
            status = "Weak"

        result.append((name, score, status))

    return result


def feasibility_matrix_example() -> None:
    print_section("22. Feasibility Matrix")

    dimensions = {
        "Technical": 86,
        "Operational": 72,
        "Economic": 81,
        "Schedule": 58,
        "Market": 77,
        "Legal": 92,
        "Resources": 74,
    }

    matrix = build_feasibility_matrix(dimensions)

    print(f"{'Dimension':<18} {'Score':>8} {'Status':<10}")
    print("-" * 42)

    for name, score, status in matrix:
        print(f"{name:<18} {score:>8.1f} {status:<10}")

    print(
        "\nThe schedule score is a useful warning even though the overall "
        "average might appear acceptable. Decision-makers should investigate "
        "weak dimensions rather than hiding them inside an average."
    )


# =============================================================================
# 24. ROOT-CAUSE ANALYSIS OF AN UNFEASIBLE PROJECT
# =============================================================================

def identify_feasibility_blockers(
    dimensions: Dict[str, float],
    threshold: float = 60,
) -> List[str]:
    """Return dimensions below the minimum acceptable threshold."""
    if not 0 <= threshold <= 100:
        raise ValueError("Threshold must be between 0 and 100.")

    return [
        name
        for name, score in dimensions.items()
        if score < threshold
    ]


def blocker_analysis_example() -> None:
    print_section("23. Identifying Feasibility Blockers")

    dimensions = {
        "Technical": 88,
        "Operational": 75,
        "Economic": 83,
        "Schedule": 42,
        "Market": 78,
        "Legal": 90,
        "Resources": 52,
    }

    blockers = identify_feasibility_blockers(dimensions)

    print("Potential blockers:")
    for blocker in blockers:
        print(f"- {blocker}")

    print(
        "\nA feasibility study should explain why a dimension is weak and "
        "whether a mitigation can move it above the required threshold."
    )


# =============================================================================
# 25. EDGE CASES AND EXCEPTIONS
# =============================================================================

def edge_case_examples() -> None:
    print_section("24. Edge Cases and Exceptions")

    cases = [
        (
            "Break-even with zero contribution margin",
            lambda: break_even_units(100_000, 100, 100),
        ),
        (
            "Negative discount rate below -100%",
            lambda: npv(-1.0, [-100, 120]),
        ),
        (
            "Invalid adoption rate",
            lambda: serviceable_market_revenue(1000, 1.5, 100),
        ),
        (
            "Circular project dependencies",
            lambda: critical_path(
                [
                    Task("A", 2, ["B"]),
                    Task("B", 3, ["A"]),
                ]
            ),
        ),
    ]

    for description, operation in cases:
        try:
            operation()
            print(f"{description}: unexpectedly succeeded")
        except ValueError as error:
            print(f"{description}: correctly rejected")
            print(f"  Reason: {error}")

    print(
        "\nImportant feasibility edge cases include zero or negative margins, "
        "impossible deadlines, circular dependencies, invalid assumptions, "
        "missing evidence, regulatory blockers, and estimates with extreme "
        "uncertainty."
    )


# =============================================================================
# 26. COMMON ANALYTICAL MISTAKES
# =============================================================================

def common_mistakes() -> None:
    print_section("25. Common Feasibility Analysis Mistakes")

    mistakes = [
        (
            "Treating estimates as facts",
            "Use assumptions, evidence quality, ranges, and confidence."
        ),
        (
            "Using only one financial metric",
            "Combine cash flow, NPV, payback, sensitivity, and strategic factors."
        ),
        (
            "Averaging mandatory requirements",
            "Use hard gates for legal, safety, contractual, or regulatory conditions."
        ),
        (
            "Ignoring opportunity cost",
            "Compare the project with alternative uses of scarce resources."
        ),
        (
            "Ignoring dependencies",
            "Map internal and external dependencies before committing."
        ),
        (
            "Assuming adoption",
            "Validate customer behavior rather than relying only on stated interest."
        ),
        (
            "Ignoring operational ownership",
            "Identify who will run, maintain, support, and govern the solution."
        ),
        (
            "Hiding weak dimensions in averages",
            "Inspect the minimum score and critical dimensions."
        ),
        (
            "Double-counting benefits",
            "Ensure benefits are distinct and tied to measurable outcomes."
        ),
        (
            "Ignoring uncertainty",
            "Use sensitivity, scenario, and probabilistic analysis where appropriate."
        ),
    ]

    for mistake, correction in mistakes:
        print(f"\nMistake: {mistake}")
        print(f"Better approach: {correction}")


# =============================================================================
# 27. BIAS AND GOVERNANCE
# =============================================================================

def governance_and_bias() -> None:
    print_section("26. Bias, Governance, and Decision Quality")

    biases = {
        "Optimism bias": "Underestimating cost, time, and difficulty.",
        "Anchoring": "Relying too heavily on an initial estimate.",
        "Confirmation bias": "Selecting evidence that supports a preferred decision.",
        "Sunk-cost bias": "Continuing because money has already been spent.",
        "Planning fallacy": "Underestimating the time required to complete work.",
        "Availability bias": "Overweighting memorable examples instead of representative evidence.",
    }

    for bias, explanation in biases.items():
        print(f"- {bias}: {explanation}")

    print("\nGovernance practices:")
    for practice in [
        "Document assumptions.",
        "Record evidence sources.",
        "Separate facts from estimates.",
        "Identify who owns each assumption.",
        "Use independent review for major investments.",
        "Define decision thresholds before seeing the result.",
        "Record reasons for changing assumptions.",
        "Reassess feasibility when material conditions change.",
    ]:
        print(f"- {practice}")


# =============================================================================
# 28. SECURITY AND PRIVACY CONSIDERATIONS
# =============================================================================

def security_feasibility_checklist() -> None:
    print_section("27. Security and Privacy Feasibility")

    controls = [
        "Authentication and authorization requirements identified",
        "Sensitive data identified",
        "Data retention requirements identified",
        "Encryption requirements evaluated",
        "Third-party security dependencies assessed",
        "Threat model performed where appropriate",
        "Incident response responsibilities identified",
        "Access control and audit requirements understood",
        "Regulatory privacy obligations reviewed",
    ]

    for control in controls:
        print(f"[ ] {control}")

    print(
        "\nSecurity is part of feasibility, not merely a post-development "
        "activity. A design that cannot meet required security controls may "
        "be infeasible regardless of its technical functionality."
    )


# =============================================================================
# 29. OPPORTUNITY COST
# =============================================================================

def opportunity_cost_example() -> None:
    print_section("28. Opportunity Cost")

    projects = {
        "Project A": {
            "expected_value": 5_000_000,
            "required_team_months": 24,
        },
        "Project B": {
            "expected_value": 4_500_000,
            "required_team_months": 12,
        },
        "Project C": {
            "expected_value": 3_000_000,
            "required_team_months": 8,
        },
    }

    for name, data in projects.items():
        value_per_team_month = (
            data["expected_value"] / data["required_team_months"]
        )

        print(
            f"{name}: expected value ₹{data['expected_value']:,.0f}, "
            f"value per team-month ₹{value_per_team_month:,.0f}"
        )

    print(
        "\nA project can be individually feasible but still be a poor choice "
        "when another feasible project produces greater value from the same "
        "scarce resources."
    )


# =============================================================================
# 30. MULTI-CRITERIA DECISION ANALYSIS
# =============================================================================

def rank_projects(
    projects: Dict[str, Sequence[FeasibilityCriterion]],
) -> List[Tuple[str, float]]:
    """Rank projects according to their weighted feasibility scores."""
    rankings = []

    for project_name, criteria in projects.items():
        score = weighted_score(criteria)
        rankings.append((project_name, score))

    return sorted(rankings, key=lambda item: item[1], reverse=True)


def multi_project_example() -> None:
    print_section("29. Comparing Multiple Projects")

    projects = {
        "Digital onboarding": [
            FeasibilityCriterion("Technical", 90, 0.20),
            FeasibilityCriterion("Economic", 85, 0.30),
            FeasibilityCriterion("Market", 80, 0.20),
            FeasibilityCriterion("Schedule", 75, 0.15),
            FeasibilityCriterion("Risk", 70, 0.15),
        ],
        "Warehouse automation": [
            FeasibilityCriterion("Technical", 70, 0.20),
            FeasibilityCriterion("Economic", 90, 0.30),
            FeasibilityCriterion("Market", 65, 0.20),
            FeasibilityCriterion("Schedule", 55, 0.15),
            FeasibilityCriterion("Risk", 60, 0.15),
        ],
        "Customer analytics": [
            FeasibilityCriterion("Technical", 82, 0.20),
            FeasibilityCriterion("Economic", 75, 0.30),
            FeasibilityCriterion("Market", 78, 0.20),
            FeasibilityCriterion("Schedule", 88, 0.15),
            FeasibilityCriterion("Risk", 80, 0.15),
        ],
    }

    rankings = rank_projects(projects)

    for rank, (project, score) in enumerate(rankings, start=1):
        print(f"{rank}. {project}: {score:.2f}/100")


# =============================================================================
# 31. PRODUCTION-STYLE FEASIBILITY REPORT
# =============================================================================

@dataclass
class FeasibilityReport:
    """A compact but structured feasibility report."""

    project_name: str
    objective: str
    dimensions: Dict[str, float]
    risks: List[Risk]
    assumptions: List[Assumption]
    constraints: List[Constraint]
    hard_gates_passed: bool
    financial_npv: float
    financial_irr: Optional[float]
    recommendation: Decision

    def render(self) -> str:
        lines = [
            f"Project: {self.project_name}",
            f"Objective: {self.objective}",
            "",
            "Feasibility dimensions:",
        ]

        for name, score in self.dimensions.items():
            lines.append(f"  {name}: {score:.1f}/100")

        lines.extend(
            [
                "",
                f"Hard gates passed: {self.hard_gates_passed}",
                f"NPV: ₹{self.financial_npv:,.0f}",
                (
                    f"IRR: {self.financial_irr:.2%}"
                    if self.financial_irr is not None
                    else "IRR: not available"
                ),
                f"Recommendation: {self.recommendation.value}",
            ]
        )

        return "\n".join(lines)


def production_report_example() -> None:
    print_section("30. Structured Feasibility Report")

    dimensions = {
        "Technical": 85,
        "Operational": 78,
        "Economic": 82,
        "Schedule": 72,
        "Market": 80,
        "Legal": 90,
        "Resources": 76,
        "Risk": 68,
    }

    cash_flows = [-4_000_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000]

    project_npv = npv(0.10, cash_flows)
    project_irr = irr(cash_flows)

    risks = [
        Risk(
            "Demand uncertainty",
            0.25,
            1_000_000,
            "Conduct pilot validation.",
        ),
        Risk(
            "Integration delay",
            0.20,
            700_000,
            "Complete technical prototype early.",
        ),
    ]

    assumptions = [
        Assumption(
            "Initial customer adoption",
            "10%",
            EvidenceQuality.MEDIUM,
            "Pilot and survey evidence.",
        ),
        Assumption(
            "Development team",
            "Five engineers",
            EvidenceQuality.HIGH,
            "Staffing plan approved.",
        ),
    ]

    constraints = [
        Constraint(
            "Budget",
            "Maximum initial investment of ₹5 million."
        ),
        Constraint(
            "Deadline",
            "Pilot required within six months."
        ),
    ]

    average_score = statistics.mean(dimensions.values())

    decision = gated_decision(
        weighted_feasibility=average_score,
        hard_gates=[True, True],
        minimum_dimension_score=60,
        dimension_scores=list(dimensions.values()),
    )

    report = FeasibilityReport(
        project_name="Customer application platform",
        objective="Evaluate whether a scalable customer application platform "
                  "can be delivered within the financial and schedule constraints.",
        dimensions=dimensions,
        risks=risks,
        assumptions=assumptions,
        constraints=constraints,
        hard_gates_passed=True,
        financial_npv=project_npv,
        financial_irr=project_irr,
        recommendation=decision,
    )

    print(report.render())


# =============================================================================
# 32. FEASIBILITY REVIEW GATES
# =============================================================================

def stage_gate_model() -> None:
    print_section("31. Stage-Gate Feasibility Review")

    stages = [
        (
            "Concept",
            "Problem is clearly defined and strategically relevant.",
        ),
        (
            "Discovery",
            "Demand, technical assumptions, and constraints are investigated.",
        ),
        (
            "Prototype",
            "Critical technical uncertainties are tested.",
        ),
        (
            "Pilot",
            "Real users and operational processes provide evidence.",
        ),
        (
            "Investment",
            "Economic and risk evidence supports full commitment.",
        ),
        (
            "Scale",
            "Operational capacity and long-term economics are acceptable.",
        ),
    ]

    for stage, gate in stages:
        print(f"{stage:12s}: {gate}")

    print(
        "\nStage gates reduce the cost of being wrong by making large "
        "commitments conditional on evidence from earlier, smaller investments."
    )


# =============================================================================
# 33. COMPLEXITY, TRADE-OFFS, AND LIMITATIONS
# =============================================================================

def tradeoffs_and_limitations() -> None:
    print_section("32. Trade-offs and Limitations")

    tradeoffs = [
        (
            "Speed versus evidence",
            "A fast decision may rely on weaker evidence."
        ),
        (
            "Precision versus complexity",
            "A detailed model can become difficult to understand and maintain."
        ),
        (
            "Expected value versus downside protection",
            "A high average value may hide unacceptable worst-case outcomes."
        ),
        (
            "Standardization versus project-specific judgment",
            "Templates improve consistency but cannot replace domain expertise."
        ),
        (
            "Financial optimization versus strategic value",
            "A project with lower direct returns may create important strategic capabilities."
        ),
    ]

    for topic, explanation in tradeoffs:
        print(f"\n{topic}:")
        print(f"  {explanation}")

    print("\nImportant limitations:")
    for limitation in [
        "Forecasts are uncertain.",
        "Some benefits are difficult to monetize.",
        "Probabilities can be subjective.",
        "Models may omit important variables.",
        "Correlated risks can make simple expected-value models misleading.",
        "A good feasibility study cannot guarantee project success.",
    ]:
        print(f"- {limitation}")


# =============================================================================
# 34. INTEGRATED PROJECT MODEL
# =============================================================================

def integrated_feasibility_analysis() -> None:
    print_section("33. Integrated Feasibility Analysis")

    # Project assumptions.
    project = {
        "name": "Subscription-based learning platform",
        "budget_limit": 5_000_000,
        "deadline_weeks": 26,
        "discount_rate": 0.10,
    }

    # Dimension scores should be based on evidence gathered during the study.
    criteria = [
        FeasibilityCriterion(
            "Technical",
            84,
            0.18,
            "Core architecture has been prototyped.",
        ),
        FeasibilityCriterion(
            "Operational",
            76,
            0.12,
            "Support and operating processes are defined.",
        ),
        FeasibilityCriterion(
            "Economic",
            82,
            0.20,
            "Base financial case produces positive NPV.",
        ),
        FeasibilityCriterion(
            "Schedule",
            74,
            0.15,
            "Critical path fits the deadline with limited buffer.",
        ),
        FeasibilityCriterion(
            "Market",
            79,
            0.15,
            "Early customer research supports demand.",
        ),
        FeasibilityCriterion(
            "Legal",
            90,
            0.08,
            "Known legal requirements can be satisfied.",
        ),
        FeasibilityCriterion(
            "Resources",
            77,
            0.07,
            "Required team capacity is available.",
        ),
        FeasibilityCriterion(
            "Risk",
            68,
            0.05,
            "Major risks have identified mitigations.",
        ),
    ]

    total_score = weighted_score(criteria)

    # Cost model.
    implementation_cost = 3_800_000
    operating_cost_year_1 = 900_000
    total_year_1_cost = implementation_cost + operating_cost_year_1

    if total_year_1_cost > project["budget_limit"]:
        budget_gate = False
    else:
        budget_gate = True

    # Revenue and cash flow model.
    cash_flows = [
        -implementation_cost,
        1_200_000,
        1_700_000,
        2_200_000,
        2_600_000,
    ]

    project_npv = npv(project["discount_rate"], cash_flows)
    project_irr = irr(cash_flows)

    # Schedule model.
    tasks = [
        Task("Requirements", 3),
        Task("Architecture", 2, ["Requirements"]),
        Task("Platform", 7, ["Architecture"]),
        Task("Application", 6, ["Architecture"]),
        Task("Integration", 3, ["Platform", "Application"]),
        Task("Testing", 4, ["Integration"]),
        Task("Pilot", 3, ["Testing"]),
    ]

    schedule_duration, schedule_path = critical_path(tasks)
    schedule_gate = schedule_duration <= project["deadline_weeks"]

    # Legal gate.
    legal_gate = compliance_gate(
        [
            True,   # Privacy requirements understood.
            True,   # Contractual review complete.
            True,   # Security controls planned.
            True,   # Applicable licenses identified.
        ]
    )

    hard_gates = [
        budget_gate,
        schedule_gate,
        legal_gate,
    ]

    dimension_scores = [criterion.score for criterion in criteria]

    decision = gated_decision(
        weighted_feasibility=total_score,
        hard_gates=hard_gates,
        minimum_dimension_score=60,
        dimension_scores=dimension_scores,
    )

    print(f"Project: {project['name']}")
    print(f"Weighted feasibility score: {total_score:.2f}/100")
    print(f"Implementation cost: ₹{implementation_cost:,.0f}")
    print(f"Year-1 total cost: ₹{total_year_1_cost:,.0f}")
    print(f"Budget limit: ₹{project['budget_limit']:,.0f}")
    print(f"Budget gate: {'PASS' if budget_gate else 'FAIL'}")
    print(f"Critical-path duration: {schedule_duration:.1f} weeks")
    print(f"Required deadline: {project['deadline_weeks']} weeks")
    print(f"Schedule gate: {'PASS' if schedule_gate else 'FAIL'}")
    print(f"Critical path: {' -> '.join(schedule_path)}")
    print(f"Legal gate: {'PASS' if legal_gate else 'FAIL'}")
    print(f"NPV: ₹{project_npv:,.0f}")

    if project_irr is None:
        print("IRR: unavailable")
    else:
        print(f"IRR: {project_irr:.2%}")

    print(f"Final decision: {decision.value}")

    print(
        "\nThe integrated approach combines quantitative indicators with "
        "hard constraints. The final decision should be accompanied by "
        "documented assumptions, evidence, risks, mitigations, and explicit "
        "decision thresholds."
    )


# =============================================================================
# 35. UNIT TESTS
# =============================================================================

def run_tests() -> None:
    print_section("34. Built-In Validation Tests")

    assert math.isclose(roi_percentage(150, 100), 50.0)
    assert math.isclose(benefit_cost_ratio(200, 100), 2.0)
    assert math.isclose(break_even_units(1000, 10, 5), 200.0)

    assert math.isclose(
        npv(0.0, [-100, 50, 50]),
        0.0,
    )

    assert math.isclose(
        weighted_score(
            [
                FeasibilityCriterion("A", 80, 1),
                FeasibilityCriterion("B", 60, 1),
            ]
        ),
        70.0,
    )

    assert operational_readiness_score(80, 80, 80, 80) == 80

    tasks = [
        Task("A", 2),
        Task("B", 3, ["A"]),
        Task("C", 4, ["A"]),
    ]

    duration, path = critical_path(tasks)

    assert duration == 6
    assert path == ["A", "C"]

    outcomes = [
        DecisionOutcome("Win", 0.5, 100),
        DecisionOutcome("Loss", 0.5, -20),
    ]

    assert math.isclose(expected_value(outcomes), 40.0)

    print("All validation tests passed.")


# =============================================================================
# 36. STUDY CHECKLIST
# =============================================================================

def study_checklist() -> None:
    print_section("35. Practical Feasibility Study Checklist")

    checklist = [
        "Define the project objective.",
        "Define measurable success criteria.",
        "Identify stakeholders.",
        "Document functional requirements.",
        "Document non-functional requirements.",
        "List assumptions.",
        "Rate evidence quality.",
        "List hard constraints.",
        "Assess technical feasibility.",
        "Assess operational feasibility.",
        "Assess market feasibility.",
        "Assess financial feasibility.",
        "Assess schedule feasibility.",
        "Assess resource feasibility.",
        "Assess legal and regulatory feasibility.",
        "Map dependencies.",
        "Identify risks.",
        "Define mitigation actions.",
        "Build cost and benefit estimates.",
        "Calculate appropriate financial metrics.",
        "Perform sensitivity analysis.",
        "Perform scenario analysis.",
        "Use probabilistic analysis when justified.",
        "Identify feasibility blockers.",
        "Compare opportunity costs.",
        "Define decision gates.",
        "Document the decision rationale.",
        "Define conditions that would trigger reassessment.",
    ]

    for item in checklist:
        print(f"[ ] {item}")


# =============================================================================
# 37. MAIN PROGRAM
# =============================================================================

def main() -> None:
    """
    Run the complete feasibility-analysis tutorial.

    The examples intentionally use synthetic project data so that the script
    remains self-contained and safe to execute without external systems.
    """
    explain_feasibility()
    requirements_example()
    technical_feasibility_example()
    operational_feasibility_example()
    financial_feasibility_example()
    schedule_feasibility_example()
    resource_feasibility_example()
    market_feasibility_example()
    legal_feasibility_example()
    weighted_score_example()
    hard_gate_example()
    risk_analysis_example()
    evidence_quality_example()
    one_way_sensitivity_example()
    scenario_analysis_example()
    monte_carlo_example()
    decision_tree_example()
    phased_investment_example()
    feasibility_viability_comparison()
    cost_estimation_example()
    dependency_analysis_example()
    feasibility_matrix_example()
    blocker_analysis_example()
    edge_case_examples()
    common_mistakes()
    governance_and_bias()
    security_feasibility_checklist()
    opportunity_cost_example()
    multi_project_example()
    production_report_example()
    stage_gate_model()
    tradeoffs_and_limitations()
    integrated_feasibility_analysis()
    run_tests()
    study_checklist()

    print_section("End of Feasibility Analysis Study Script")
    print(
        "The script has demonstrated how feasibility analysis moves from "
        "basic project questions to integrated quantitative and qualitative "
        "decision-making."
    )


if __name__ == "__main__":
    main()
