"""
Business Case: Understanding Why a Project Should Be Undertaken

This standalone study script teaches how to construct and evaluate a business
case for a project. It progresses from basic concepts to quantitative analysis,
risk assessment, strategic alignment, option comparison, sensitivity analysis,
scenario analysis, and a structured investment recommendation.

The examples are intentionally implemented in Python so that the analytical
logic can be executed, inspected, modified, and tested.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import pow
from typing import Dict, List, Optional, Tuple


# =============================================================================
# 1. BUSINESS CASE FUNDAMENTALS
# =============================================================================

print("=" * 80)
print("BUSINESS CASE: UNDERSTANDING WHY A PROJECT SHOULD BE UNDERTAKEN")
print("=" * 80)


def explain_business_case() -> None:
    """
    A business case explains why an organization should invest in a proposed
    project and what value is expected from that investment.

    A business case normally answers questions such as:
        - What problem or opportunity exists?
        - Why should the organization act?
        - What happens if nothing is done?
        - What options are available?
        - What will each option cost?
        - What benefits are expected?
        - What risks exist?
        - Does the project support strategy?
        - Is the investment financially and operationally justified?
        - Which option should decision-makers select?
    """
    concepts = {
        "Business case": (
            "A structured argument for undertaking an investment, project, "
            "or change initiative."
        ),
        "Problem statement": (
            "A precise description of the business problem that requires action."
        ),
        "Opportunity": (
            "A condition that can potentially create additional value or "
            "competitive advantage."
        ),
        "Benefits": (
            "Measurable or non-measurable improvements expected from the project."
        ),
        "Cost": (
            "Resources consumed to deliver, operate, maintain, or eventually "
            "retire the solution."
        ),
        "Risk": (
            "An uncertain event or condition that could affect objectives."
        ),
        "Assumption": (
            "A statement treated as true for planning purposes even though it "
            "may not yet be fully proven."
        ),
        "Constraint": (
            "A limitation such as budget, time, regulation, capacity, or technology."
        ),
        "Baseline": (
            "The current state against which future performance is compared."
        ),
        "Do nothing": (
            "The reference option in which the organization does not undertake "
            "the proposed intervention."
        ),
    }

    for term, definition in concepts.items():
        print(f"\n{term}:")
        print(f"  {definition}")


explain_business_case()


# =============================================================================
# 2. THE LOGIC OF A STRONG BUSINESS CASE
# =============================================================================

print("\n" + "=" * 80)
print("2. THE BUSINESS CASE LOGIC")
print("=" * 80)

business_case_logic = [
    "Current situation",
    "Problem or opportunity",
    "Consequences of the current situation",
    "Objectives",
    "Alternative options",
    "Preferred option",
    "Costs",
    "Benefits",
    "Risks",
    "Strategic alignment",
    "Financial evaluation",
    "Implementation feasibility",
    "Recommendation",
]

for number, item in enumerate(business_case_logic, start=1):
    print(f"{number:2}. {item}")

print(
    "\nThe central reasoning chain is:\n"
    "Problem/opportunity -> Need for change -> Options -> Value -> Risk -> "
    "Investment decision"
)


# =============================================================================
# 3. PROBLEM VERSUS SOLUTION
# =============================================================================

print("\n" + "=" * 80)
print("3. PROBLEM STATEMENT VERSUS SOLUTION")
print("=" * 80)

problem = (
    "Customer support requests are taking too long to resolve, causing "
    "high operating costs and customer dissatisfaction."
)

weak_solution_statement = "We should build a new customer support application."

strong_problem_statement = (
    "Average support resolution time is 48 hours against a target of 12 hours. "
    "The delay contributes to customer dissatisfaction, repeated contacts, "
    "and avoidable support costs."
)

print("Weak solution-oriented statement:")
print(f"  {weak_solution_statement}")

print("\nStronger problem-oriented statement:")
print(f"  {strong_problem_statement}")

print(
    "\nA business case should establish the need before assuming that a "
    "particular solution is the correct answer."
)


# =============================================================================
# 4. CURRENT STATE AND BASELINE
# =============================================================================

print("\n" + "=" * 80)
print("4. CURRENT STATE AND BASELINE")
print("=" * 80)


@dataclass
class CurrentState:
    annual_transactions: int
    average_cost_per_transaction: float
    annual_revenue: float
    customer_complaints: int
    average_processing_hours: float

    @property
    def annual_operating_cost(self) -> float:
        return self.annual_transactions * self.average_cost_per_transaction


current_state = CurrentState(
    annual_transactions=120_000,
    average_cost_per_transaction=8.50,
    annual_revenue=18_000_000,
    customer_complaints=9_500,
    average_processing_hours=48.0,
)

print(f"Annual transactions: {current_state.annual_transactions:,}")
print(f"Cost per transaction: ${current_state.average_cost_per_transaction:,.2f}")
print(f"Annual operating cost: ${current_state.annual_operating_cost:,.2f}")
print(f"Annual revenue: ${current_state.annual_revenue:,.2f}")
print(f"Customer complaints: {current_state.customer_complaints:,}")
print(f"Average processing time: {current_state.average_processing_hours:.1f} hours")


# =============================================================================
# 5. OBJECTIVES AND SUCCESS MEASURES
# =============================================================================

print("\n" + "=" * 80)
print("5. OBJECTIVES AND SUCCESS MEASURES")
print("=" * 80)


@dataclass
class Objective:
    name: str
    baseline: float
    target: float
    unit: str
    direction: str  # "increase" or "decrease"

    def target_achieved(self, actual: float) -> bool:
        if self.direction == "increase":
            return actual >= self.target
        if self.direction == "decrease":
            return actual <= self.target
        raise ValueError("direction must be 'increase' or 'decrease'")


objectives = [
    Objective(
        "Average resolution time",
        baseline=48,
        target=12,
        unit="hours",
        direction="decrease",
    ),
    Objective(
        "Annual support cost",
        baseline=1_020_000,
        target=750_000,
        unit="USD",
        direction="decrease",
    ),
    Objective(
        "Customer satisfaction score",
        baseline=68,
        target=85,
        unit="points",
        direction="increase",
    ),
]

for objective in objectives:
    print(
        f"{objective.name}: "
        f"{objective.baseline} -> {objective.target} {objective.unit}"
    )


# =============================================================================
# 6. OPTIONS ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("6. OPTIONS ANALYSIS")
print("=" * 80)

print(
    """
A business case should normally compare alternatives rather than treating the
first proposed solution as automatically correct.

Typical options include:
    1. Do nothing.
    2. Improve the existing process.
    3. Purchase an existing solution.
    4. Build a custom solution.
    5. Use a phased or hybrid approach.
"""
)


@dataclass
class ProjectOption:
    name: str
    implementation_cost: float
    annual_operating_cost: float
    annual_benefit: float
    implementation_months: int
    risk_score: float
    strategic_alignment: float
    qualitative_value: float

    def first_year_net_value(self) -> float:
        return self.annual_benefit - (
            self.implementation_cost + self.annual_operating_cost
        )

    def simple_roi(self) -> float:
        total_cost = self.implementation_cost + self.annual_operating_cost
        if total_cost == 0:
            return float("inf")
        return (self.annual_benefit - total_cost) / total_cost


options = [
    ProjectOption(
        name="Do nothing",
        implementation_cost=0,
        annual_operating_cost=1_020_000,
        annual_benefit=0,
        implementation_months=0,
        risk_score=3,
        strategic_alignment=2,
        qualitative_value=1,
    ),
    ProjectOption(
        name="Process improvement",
        implementation_cost=180_000,
        annual_operating_cost=700_000,
        annual_benefit=350_000,
        implementation_months=4,
        risk_score=2,
        strategic_alignment=6,
        qualitative_value=5,
    ),
    ProjectOption(
        name="Purchase SaaS platform",
        implementation_cost=420_000,
        annual_operating_cost=520_000,
        annual_benefit=780_000,
        implementation_months=6,
        risk_score=3,
        strategic_alignment=8,
        qualitative_value=8,
    ),
    ProjectOption(
        name="Custom platform",
        implementation_cost=1_100_000,
        annual_operating_cost=430_000,
        annual_benefit=1_050_000,
        implementation_months=12,
        risk_score=5,
        strategic_alignment=10,
        qualitative_value=10,
    ),
]

for option in options:
    print(f"\n{option.name}")
    print(f"  Implementation cost: ${option.implementation_cost:,.0f}")
    print(f"  Annual operating cost: ${option.annual_operating_cost:,.0f}")
    print(f"  Annual benefit: ${option.annual_benefit:,.0f}")
    print(f"  Implementation time: {option.implementation_months} months")
    print(f"  Risk score: {option.risk_score}/5")
    print(f"  Strategic alignment: {option.strategic_alignment}/10")


# =============================================================================
# 7. BENEFITS CLASSIFICATION
# =============================================================================

print("\n" + "=" * 80)
print("7. BENEFITS CLASSIFICATION")
print("=" * 80)

benefit_types = {
    "Financial": "Benefits that can be directly represented in monetary terms.",
    "Operational": "Improvements in efficiency, quality, capacity, or productivity.",
    "Customer": "Improvements in satisfaction, retention, experience, or service.",
    "Strategic": "Benefits supporting long-term organizational direction.",
    "Compliance": "Benefits from satisfying legal, regulatory, or policy requirements.",
    "Risk reduction": "Avoided losses, failures, incidents, or disruptions.",
    "Intangible": "Benefits such as reputation, trust, morale, or organizational learning.",
}

for benefit_type, definition in benefit_types.items():
    print(f"{benefit_type}: {definition}")


@dataclass
class Benefit:
    name: str
    annual_value: float
    measurable: bool
    category: str

    def value_for_period(self, years: int) -> float:
        return self.annual_value * years


benefits = [
    Benefit(
        "Reduced support labor",
        annual_value=360_000,
        measurable=True,
        category="Financial",
    ),
    Benefit(
        "Reduced customer churn",
        annual_value=250_000,
        measurable=True,
        category="Customer",
    ),
    Benefit(
        "Higher employee productivity",
        annual_value=180_000,
        measurable=True,
        category="Operational",
    ),
    Benefit(
        "Improved customer experience",
        annual_value=0,
        measurable=False,
        category="Intangible",
    ),
]

for benefit in benefits:
    value = "quantified" if benefit.measurable else "not directly quantified"
    print(f"{benefit.name}: {benefit.category}, {value}")


# =============================================================================
# 8. COST CLASSIFICATION
# =============================================================================

print("\n" + "=" * 80)
print("8. COST CLASSIFICATION")
print("=" * 80)

cost_categories = {
    "Capital expenditure": "Initial investment in assets or implementation.",
    "Operating expenditure": "Recurring costs required to operate the solution.",
    "Transition cost": "Temporary cost incurred while moving from current to future state.",
    "Training cost": "Cost of preparing users and support teams.",
    "Maintenance cost": "Cost of maintaining, updating, and supporting the solution.",
    "Decommissioning cost": "Cost associated with retiring the solution.",
    "Opportunity cost": "Value of the best alternative use of constrained resources.",
}

for category, definition in cost_categories.items():
    print(f"{category}: {definition}")


# =============================================================================
# 9. SIMPLE ROI
# =============================================================================

print("\n" + "=" * 80)
print("9. RETURN ON INVESTMENT")
print("=" * 80)


def roi(initial_investment: float, net_gain: float) -> float:
    """Calculate simple ROI as net gain divided by investment."""
    if initial_investment <= 0:
        raise ValueError("Initial investment must be greater than zero.")
    return net_gain / initial_investment


investment = 500_000
annual_net_benefit = 200_000
simple_roi = roi(investment, annual_net_benefit)

print(f"Investment: ${investment:,.0f}")
print(f"Annual net benefit: ${annual_net_benefit:,.0f}")
print(f"Simple ROI: {simple_roi:.2%}")

print(
    "\nSimple ROI is useful for quick comparison but does not properly account "
    "for the timing of cash flows."
)


# =============================================================================
# 10. PAYBACK PERIOD
# =============================================================================

print("\n" + "=" * 80)
print("10. PAYBACK PERIOD")
print("=" * 80)


def payback_period(initial_investment: float, annual_cash_benefit: float) -> float:
    """
    Calculate simple payback period.

    This assumes a constant annual cash benefit and ignores discounting.
    """
    if initial_investment < 0:
        raise ValueError("Initial investment cannot be negative.")
    if annual_cash_benefit <= 0:
        return float("inf")
    return initial_investment / annual_cash_benefit


payback = payback_period(1_000_000, 250_000)
print(f"Payback period: {payback:.2f} years")

print(
    "\nA shorter payback generally means faster recovery of the initial "
    "investment, but payback ignores cash flows after the recovery point."
)


# =============================================================================
# 11. NET PRESENT VALUE
# =============================================================================

print("\n" + "=" * 80)
print("11. NET PRESENT VALUE")
print("=" * 80)


def present_value(cash_flow: float, discount_rate: float, period: int) -> float:
    """Discount a future cash flow to its present value."""
    if discount_rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")
    return cash_flow / pow(1 + discount_rate, period)


def npv(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
) -> float:
    """
    Calculate NPV.

    cash_flows[0] represents the first future period rather than time zero.
    """
    if discount_rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")

    total = -initial_investment

    for period, cash_flow in enumerate(cash_flows, start=1):
        total += present_value(cash_flow, discount_rate, period)

    return total


cash_flows = [250_000, 300_000, 350_000, 400_000, 450_000]
discount_rate = 0.10

project_npv = npv(
    initial_investment=1_000_000,
    cash_flows=cash_flows,
    discount_rate=discount_rate,
)

print(f"Initial investment: $1,000,000")
print(f"Discount rate: {discount_rate:.1%}")
print(f"NPV: ${project_npv:,.2f}")

if project_npv > 0:
    print("Financial interpretation: positive NPV under the stated assumptions.")
elif project_npv < 0:
    print("Financial interpretation: negative NPV under the stated assumptions.")
else:
    print("Financial interpretation: NPV is approximately zero.")


# =============================================================================
# 12. DISCOUNT RATE AND TIME VALUE OF MONEY
# =============================================================================

print("\n" + "=" * 80)
print("12. TIME VALUE OF MONEY")
print("=" * 80)

future_amount = 1_000_000

for rate in [0.05, 0.10, 0.15]:
    pv = present_value(future_amount, rate, 5)
    print(
        f"${future_amount:,.0f} received in 5 years at {rate:.0%} "
        f"discount rate has present value ${pv:,.2f}"
    )

print(
    "\nThe same nominal cash flow can have different economic value depending "
    "on when it is received and the discount rate used."
)


# =============================================================================
# 13. INTERNAL RATE OF RETURN
# =============================================================================

print("\n" + "=" * 80)
print("13. INTERNAL RATE OF RETURN")
print("=" * 80)


def npv_with_rate(initial_investment: float, cash_flows: List[float], rate: float) -> float:
    return npv(initial_investment, cash_flows, rate)


def approximate_irr(
    initial_investment: float,
    cash_flows: List[float],
    lower_rate: float = -0.99,
    upper_rate: float = 10.0,
    iterations: int = 200,
) -> Optional[float]:
    """
    Approximate IRR using bisection.

    This implementation is intentionally simple and assumes that a single
    economically meaningful sign change permits a useful solution.
    """
    low = lower_rate
    high = upper_rate

    npv_low = npv_with_rate(initial_investment, cash_flows, low)
    npv_high = npv_with_rate(initial_investment, cash_flows, high)

    if npv_low == 0:
        return low

    if npv_high == 0:
        return high

    if npv_low * npv_high > 0:
        return None

    for _ in range(iterations):
        middle = (low + high) / 2
        npv_middle = npv_with_rate(initial_investment, cash_flows, middle)

        if abs(npv_middle) < 1e-8:
            return middle

        if npv_low * npv_middle <= 0:
            high = middle
            npv_high = npv_middle
        else:
            low = middle
            npv_low = npv_middle

    return (low + high) / 2


irr = approximate_irr(1_000_000, cash_flows)

if irr is not None:
    print(f"Approximate IRR: {irr:.2%}")
else:
    print("IRR could not be established for the supplied cash flows.")


# =============================================================================
# 14. BENEFIT-COST RATIO
# =============================================================================

print("\n" + "=" * 80)
print("14. BENEFIT-COST RATIO")
print("=" * 80)


def benefit_cost_ratio(
    discounted_benefits: float,
    discounted_costs: float,
) -> float:
    if discounted_costs <= 0:
        raise ValueError("Discounted costs must be greater than zero.")
    return discounted_benefits / discounted_costs


discounted_benefits = sum(
    present_value(value, 0.10, year)
    for year, value in enumerate(cash_flows, start=1)
)

discounted_costs = 1_000_000

bcr = benefit_cost_ratio(discounted_benefits, discounted_costs)

print(f"Discounted benefits: ${discounted_benefits:,.2f}")
print(f"Discounted costs: ${discounted_costs:,.2f}")
print(f"Benefit-cost ratio: {bcr:.2f}")


# =============================================================================
# 15. TOTAL COST OF OWNERSHIP
# =============================================================================

print("\n" + "=" * 80)
print("15. TOTAL COST OF OWNERSHIP")
print("=" * 80)


def total_cost_of_ownership(
    implementation_cost: float,
    annual_operating_cost: float,
    annual_maintenance_cost: float,
    annual_training_cost: float,
    years: int,
    exit_cost: float = 0,
) -> float:
    """
    Calculate a simple undiscounted TCO.

    TCO can be extended to include inflation, discounting, licenses,
    infrastructure, support, migration, and decommissioning.
    """
    if years < 0:
        raise ValueError("Years cannot be negative.")

    recurring = (
        annual_operating_cost
        + annual_maintenance_cost
        + annual_training_cost
    ) * years

    return implementation_cost + recurring + exit_cost


tco = total_cost_of_ownership(
    implementation_cost=600_000,
    annual_operating_cost=300_000,
    annual_maintenance_cost=80_000,
    annual_training_cost=20_000,
    years=5,
    exit_cost=50_000,
)

print(f"Five-year TCO: ${tco:,.2f}")


# =============================================================================
# 16. CASH FLOW MODEL
# =============================================================================

print("\n" + "=" * 80)
print("16. YEAR-BY-YEAR CASH FLOW MODEL")
print("=" * 80)


@dataclass
class CashFlowYear:
    year: int
    benefits: float
    operating_costs: float
    capital_costs: float

    @property
    def net_cash_flow(self) -> float:
        return self.benefits - self.operating_costs - self.capital_costs


cash_flow_plan = [
    CashFlowYear(0, 0, 0, 1_000_000),
    CashFlowYear(1, 700_000, 300_000, 0),
    CashFlowYear(2, 850_000, 320_000, 0),
    CashFlowYear(3, 950_000, 340_000, 0),
    CashFlowYear(4, 1_000_000, 350_000, 0),
    CashFlowYear(5, 1_050_000, 360_000, 0),
]

cumulative = 0.0

print(
    f"{'Year':>4} {'Benefits':>15} {'Operating':>15} "
    f"{'Capital':>15} {'Net Cash Flow':>18} {'Cumulative':>18}"
)

for row in cash_flow_plan:
    cumulative += row.net_cash_flow
    print(
        f"{row.year:>4} "
        f"${row.benefits:>14,.0f} "
        f"${row.operating_costs:>14,.0f} "
        f"${row.capital_costs:>14,.0f} "
        f"${row.net_cash_flow:>17,.0f} "
        f"${cumulative:>17,.0f}"
    )


# =============================================================================
# 17. RISK MANAGEMENT
# =============================================================================

print("\n" + "=" * 80)
print("17. RISK MANAGEMENT")
print("=" * 80)


@dataclass
class Risk:
    name: str
    probability: float
    impact: float
    response: str
    owner: str

    @property
    def expected_loss(self) -> float:
        return self.probability * self.impact

    def validate(self) -> None:
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1.")
        if self.impact < 0:
            raise ValueError("Impact cannot be negative.")


risks = [
    Risk(
        name="Implementation delay",
        probability=0.25,
        impact=300_000,
        response="Phase delivery and maintain schedule contingency",
        owner="Project Manager",
    ),
    Risk(
        name="User adoption below target",
        probability=0.30,
        impact=220_000,
        response="Training, change management, and adoption monitoring",
        owner="Business Owner",
    ),
    Risk(
        name="Vendor dependency",
        probability=0.15,
        impact=400_000,
        response="Contract controls and exit planning",
        owner="Procurement Lead",
    ),
]

total_expected_loss = 0.0

for risk in risks:
    risk.validate()
    total_expected_loss += risk.expected_loss

    print(f"\nRisk: {risk.name}")
    print(f"  Probability: {risk.probability:.0%}")
    print(f"  Impact: ${risk.impact:,.0f}")
    print(f"  Expected loss: ${risk.expected_loss:,.0f}")
    print(f"  Response: {risk.response}")
    print(f"  Owner: {risk.owner}")

print(f"\nTotal expected risk exposure: ${total_expected_loss:,.0f}")


# =============================================================================
# 18. RISK SCORE MATRIX
# =============================================================================

print("\n" + "=" * 80)
print("18. PROBABILITY-IMPACT RISK SCORE")
print("=" * 80)


def risk_score(probability_score: int, impact_score: int) -> int:
    if not 1 <= probability_score <= 5:
        raise ValueError("Probability score must be 1 to 5.")
    if not 1 <= impact_score <= 5:
        raise ValueError("Impact score must be 1 to 5.")
    return probability_score * impact_score


risk_examples = [
    ("Low-probability, low-impact", 1, 2),
    ("Medium risk", 3, 3),
    ("High-probability, high-impact", 5, 5),
]

for name, probability_score, impact_score in risk_examples:
    score = risk_score(probability_score, impact_score)
    print(f"{name}: {probability_score} x {impact_score} = {score}")


# =============================================================================
# 19. EXPECTED MONETARY VALUE
# =============================================================================

print("\n" + "=" * 80)
print("19. EXPECTED MONETARY VALUE")
print("=" * 80)


@dataclass
class Scenario:
    name: str
    probability: float
    outcome: float


def expected_monetary_value(scenarios: List[Scenario]) -> float:
    total_probability = sum(s.probability for s in scenarios)

    if abs(total_probability - 1.0) > 1e-9:
        raise ValueError("Scenario probabilities must sum to 1.")

    return sum(s.probability * s.outcome for s in scenarios)


scenarios = [
    Scenario("Best case", 0.20, 1_500_000),
    Scenario("Most likely", 0.60, 900_000),
    Scenario("Worst case", 0.20, -300_000),
]

emv = expected_monetary_value(scenarios)

for scenario in scenarios:
    print(
        f"{scenario.name}: probability={scenario.probability:.0%}, "
        f"outcome=${scenario.outcome:,.0f}"
    )

print(f"Expected monetary value: ${emv:,.2f}")


# =============================================================================
# 20. SENSITIVITY ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("20. SENSITIVITY ANALYSIS")
print("=" * 80)


def project_npv_for_assumptions(
    investment: float,
    annual_benefit: float,
    annual_cost: float,
    years: int,
    discount_rate: float,
) -> float:
    annual_net_cash_flow = annual_benefit - annual_cost
    return npv(
        investment,
        [annual_net_cash_flow] * years,
        discount_rate,
    )


base_investment = 1_000_000
base_benefit = 700_000
base_cost = 300_000
base_years = 5
base_discount_rate = 0.10

print("Base-case NPV:")
base_npv = project_npv_for_assumptions(
    base_investment,
    base_benefit,
    base_cost,
    base_years,
    base_discount_rate,
)
print(f"  ${base_npv:,.2f}")

print("\nBenefit sensitivity:")

for multiplier in [0.70, 0.85, 1.00, 1.15, 1.30]:
    adjusted_benefit = base_benefit * multiplier
    sensitivity_npv = project_npv_for_assumptions(
        base_investment,
        adjusted_benefit,
        base_cost,
        base_years,
        base_discount_rate,
    )
    print(
        f"  Benefit multiplier {multiplier:.0%}: "
        f"NPV = ${sensitivity_npv:,.2f}"
    )

print(
    "\nSensitivity analysis identifies assumptions that have a strong influence "
    "on the investment decision."
)


# =============================================================================
# 21. SCENARIO ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("21. SCENARIO ANALYSIS")
print("=" * 80)


@dataclass
class ProjectScenario:
    name: str
    benefit_multiplier: float
    cost_multiplier: float
    probability: float

    def calculate_npv(
        self,
        investment: float,
        annual_benefit: float,
        annual_cost: float,
        years: int,
        discount_rate: float,
    ) -> float:
        adjusted_benefit = annual_benefit * self.benefit_multiplier
        adjusted_cost = annual_cost * self.cost_multiplier

        return project_npv_for_assumptions(
            investment,
            adjusted_benefit,
            adjusted_cost,
            years,
            discount_rate,
        )


project_scenarios = [
    ProjectScenario("Optimistic", 1.30, 0.90, 0.20),
    ProjectScenario("Base case", 1.00, 1.00, 0.60),
    ProjectScenario("Pessimistic", 0.70, 1.25, 0.20),
]

for scenario in project_scenarios:
    scenario_npv = scenario.calculate_npv(
        base_investment,
        base_benefit,
        base_cost,
        base_years,
        base_discount_rate,
    )

    print(
        f"{scenario.name}: "
        f"NPV=${scenario_npv:,.2f}, "
        f"probability={scenario.probability:.0%}"
    )


# =============================================================================
# 22. STRATEGIC ALIGNMENT
# =============================================================================

print("\n" + "=" * 80)
print("22. STRATEGIC ALIGNMENT")
print("=" * 80)


@dataclass
class StrategicCriterion:
    name: str
    weight: float
    score: float

    @property
    def weighted_score(self) -> float:
        return self.weight * self.score


strategic_criteria = [
    StrategicCriterion("Revenue growth", 0.25, 8),
    StrategicCriterion("Customer experience", 0.20, 9),
    StrategicCriterion("Operational efficiency", 0.20, 8),
    StrategicCriterion("Risk reduction", 0.15, 7),
    StrategicCriterion("Technology modernization", 0.10, 9),
    StrategicCriterion("Regulatory readiness", 0.10, 6),
]

weighted_strategic_score = sum(
    criterion.weighted_score for criterion in strategic_criteria
)

for criterion in strategic_criteria:
    print(
        f"{criterion.name}: weight={criterion.weight:.0%}, "
        f"score={criterion.score:.1f}, "
        f"weighted={criterion.weighted_score:.2f}"
    )

print(f"\nStrategic alignment score: {weighted_strategic_score:.2f}/10")


# =============================================================================
# 23. WEIGHTED OPTION SCORING
# =============================================================================

print("\n" + "=" * 80)
print("23. WEIGHTED OPTION SCORING")
print("=" * 80)


@dataclass
class EvaluationCriterion:
    name: str
    weight: float


evaluation_criteria = [
    EvaluationCriterion("Financial value", 0.30),
    EvaluationCriterion("Strategic alignment", 0.20),
    EvaluationCriterion("Customer value", 0.15),
    EvaluationCriterion("Implementation feasibility", 0.15),
    EvaluationCriterion("Risk profile", 0.10),
    EvaluationCriterion("Time to value", 0.10),
]

option_scores: Dict[str, Dict[str, float]] = {
    "Process improvement": {
        "Financial value": 6,
        "Strategic alignment": 6,
        "Customer value": 5,
        "Implementation feasibility": 9,
        "Risk profile": 8,
        "Time to value": 9,
    },
    "Purchase SaaS platform": {
        "Financial value": 8,
        "Strategic alignment": 8,
        "Customer value": 8,
        "Implementation feasibility": 8,
        "Risk profile": 7,
        "Time to value": 7,
    },
    "Custom platform": {
        "Financial value": 7,
        "Strategic alignment": 10,
        "Customer value": 10,
        "Implementation feasibility": 5,
        "Risk profile": 5,
        "Time to value": 4,
    },
}


def weighted_option_score(
    scores: Dict[str, float],
    criteria: List[EvaluationCriterion],
) -> float:
    total = 0.0

    for criterion in criteria:
        if criterion.name not in scores:
            raise KeyError(f"Missing score for {criterion.name}")

        score = scores[criterion.name]

        if not 0 <= score <= 10:
            raise ValueError("Scores must be between 0 and 10.")

        total += criterion.weight * score

    return total


option_weighted_results: Dict[str, float] = {}

for option_name, scores in option_scores.items():
    score = weighted_option_score(scores, evaluation_criteria)
    option_weighted_results[option_name] = score
    print(f"{option_name}: {score:.2f}/10")

best_scored_option = max(
    option_weighted_results,
    key=option_weighted_results.get,
)

print(f"\nHighest weighted score: {best_scored_option}")


# =============================================================================
# 24. FINANCIAL VERSUS STRATEGIC VALUE
# =============================================================================

print("\n" + "=" * 80)
print("24. FINANCIAL VALUE VERSUS STRATEGIC VALUE")
print("=" * 80)

print(
    """
A project can be strategically important even when its direct financial return
is limited. Conversely, a project can have attractive financial metrics but
still be inappropriate because of regulatory, ethical, operational, security,
or strategic concerns.

A sound business case therefore considers multiple dimensions:
    Financial value
    Strategic value
    Customer value
    Operational value
    Risk reduction
    Compliance
    Feasibility
"""
)


# =============================================================================
# 25. COST OF DOING NOTHING
# =============================================================================

print("\n" + "=" * 80)
print("25. COST OF DOING NOTHING")
print("=" * 80)


@dataclass
class DoNothingAnalysis:
    current_annual_cost: float
    annual_cost_growth_rate: float
    years: int

    def projected_cost(self) -> float:
        total = 0.0

        for year in range(self.years):
            total += self.current_annual_cost * (
                (1 + self.annual_cost_growth_rate) ** year
            )

        return total


do_nothing = DoNothingAnalysis(
    current_annual_cost=1_020_000,
    annual_cost_growth_rate=0.06,
    years=5,
)

cost_of_doing_nothing = do_nothing.projected_cost()

print(
    f"Five-year cost of continuing the current state: "
    f"${cost_of_doing_nothing:,.2f}"
)

print(
    "\nThe do-nothing option is not necessarily cost-free. "
    "Inaction can create rising operating costs, lost revenue, customer "
    "attrition, compliance exposure, technical debt, or missed opportunities."
)


# =============================================================================
# 26. OPPORTUNITY COST
# =============================================================================

print("\n" + "=" * 80)
print("26. OPPORTUNITY COST")
print("=" * 80)


def opportunity_cost(
    chosen_return: float,
    best_alternative_return: float,
) -> float:
    return best_alternative_return - chosen_return


chosen_project_return = 900_000
alternative_return = 1_100_000

lost_value = opportunity_cost(chosen_project_return, alternative_return)

print(f"Chosen project return: ${chosen_project_return:,.0f}")
print(f"Best alternative return: ${alternative_return:,.0f}")
print(f"Opportunity cost: ${lost_value:,.0f}")


# =============================================================================
# 27. CONSTRAINTS AND FEASIBILITY
# =============================================================================

print("\n" + "=" * 80)
print("27. FEASIBILITY")
print("=" * 80)


@dataclass
class FeasibilityAssessment:
    technical: float
    operational: float
    financial: float
    legal: float
    organizational: float

    def average_score(self) -> float:
        values = [
            self.technical,
            self.operational,
            self.financial,
            self.legal,
            self.organizational,
        ]
        return sum(values) / len(values)

    def is_feasible(self, minimum_score: float = 6.0) -> bool:
        values = [
            self.technical,
            self.operational,
            self.financial,
            self.legal,
            self.organizational,
        ]
        return all(value >= minimum_score for value in values)


feasibility = FeasibilityAssessment(
    technical=8,
    operational=7,
    financial=8,
    legal=9,
    organizational=6,
)

print(f"Average feasibility score: {feasibility.average_score():.2f}/10")
print(f"Passes minimum feasibility threshold: {feasibility.is_feasible()}")


# =============================================================================
# 28. ASSUMPTIONS REGISTER
# =============================================================================

print("\n" + "=" * 80)
print("28. ASSUMPTIONS")
print("=" * 80)


@dataclass
class Assumption:
    statement: str
    confidence: str
    validation_method: str


assumptions = [
    Assumption(
        "Annual transaction volume will remain approximately stable.",
        "Medium",
        "Review historical transaction trends.",
    ),
    Assumption(
        "At least 70% of users will adopt the new workflow.",
        "Medium",
        "Pilot adoption measurement.",
    ),
    Assumption(
        "Implementation can be completed within 12 months.",
        "Medium",
        "Detailed delivery plan and dependency analysis.",
    ),
    Assumption(
        "Expected labor savings can be converted into measurable economic value.",
        "Low",
        "Validate workforce capacity and redeployment assumptions.",
    ),
]

for assumption in assumptions:
    print(f"\nStatement: {assumption.statement}")
    print(f"Confidence: {assumption.confidence}")
    print(f"Validation: {assumption.validation_method}")


# =============================================================================
# 29. SENSITIVITY TO ADOPTION
# =============================================================================

print("\n" + "=" * 80)
print("29. BENEFIT REALIZATION AND USER ADOPTION")
print("=" * 80)


def realized_benefit(
    theoretical_benefit: float,
    adoption_rate: float,
    realization_rate: float,
) -> float:
    if not 0 <= adoption_rate <= 1:
        raise ValueError("Adoption rate must be between 0 and 1.")
    if not 0 <= realization_rate <= 1:
        raise ValueError("Realization rate must be between 0 and 1.")

    return theoretical_benefit * adoption_rate * realization_rate


theoretical_benefit = 1_000_000

for adoption in [0.50, 0.70, 0.85, 1.00]:
    benefit = realized_benefit(
        theoretical_benefit,
        adoption_rate=adoption,
        realization_rate=0.90,
    )
    print(f"Adoption {adoption:.0%}: realized benefit ${benefit:,.0f}")


# =============================================================================
# 30. BENEFIT REALIZATION VERSUS BENEFIT ESTIMATION
# =============================================================================

print("\n" + "=" * 80)
print("30. BENEFIT REALIZATION")
print("=" * 80)

print(
    """
A business case forecast is not the same as a realized benefit.

Forecast benefit:
    The value expected when the investment is approved.

Realized benefit:
    The value actually achieved after implementation.

Benefit realization requires:
    - A baseline
    - A measurable target
    - A benefit owner
    - A measurement method
    - A measurement date
    - Clear attribution rules
"""
)


# =============================================================================
# 31. BREAK-EVEN ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("31. BREAK-EVEN ANALYSIS")
print("=" * 80)


def break_even_units(
    fixed_cost: float,
    revenue_per_unit: float,
    variable_cost_per_unit: float,
) -> float:
    contribution_margin = revenue_per_unit - variable_cost_per_unit

    if contribution_margin <= 0:
        return float("inf")

    return fixed_cost / contribution_margin


fixed_cost = 500_000
revenue_per_unit = 100
variable_cost_per_unit = 60

break_even = break_even_units(
    fixed_cost,
    revenue_per_unit,
    variable_cost_per_unit,
)

print(f"Fixed cost: ${fixed_cost:,.0f}")
print(f"Revenue per unit: ${revenue_per_unit:,.2f}")
print(f"Variable cost per unit: ${variable_cost_per_unit:,.2f}")
print(f"Break-even units: {break_even:,.0f}")


# =============================================================================
# 32. MARGINAL ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("32. MARGINAL ANALYSIS")
print("=" * 80)


def marginal_value(additional_benefit: float, additional_cost: float) -> float:
    return additional_benefit - additional_cost


additional_benefit = 180_000
additional_cost = 120_000

marginal_net_value = marginal_value(
    additional_benefit,
    additional_cost,
)

print(f"Additional benefit: ${additional_benefit:,.0f}")
print(f"Additional cost: ${additional_cost:,.0f}")
print(f"Marginal net value: ${marginal_net_value:,.0f}")


# =============================================================================
# 33. DECISION GATES
# =============================================================================

print("\n" + "=" * 80)
print("33. INVESTMENT DECISION GATES")
print("=" * 80)


@dataclass
class DecisionGate:
    name: str
    passed: bool
    reason: str


decision_gates = [
    DecisionGate(
        "Problem is material",
        True,
        "Current operating cost and customer impact are significant.",
    ),
    DecisionGate(
        "Strategic alignment",
        True,
        "The initiative supports customer and efficiency objectives.",
    ),
    DecisionGate(
        "Financial case",
        True,
        "Base-case NPV is positive.",
    ),
    DecisionGate(
        "Technical feasibility",
        True,
        "Required technology is available.",
    ),
    DecisionGate(
        "Risk acceptable",
        True,
        "Major risks have defined mitigation strategies.",
    ),
    DecisionGate(
        "Organizational readiness",
        False,
        "Change capacity requires additional planning.",
    ),
]

for gate in decision_gates:
    status = "PASS" if gate.passed else "FAIL"
    print(f"[{status}] {gate.name}: {gate.reason}")


# =============================================================================
# 34. INVESTMENT DECISION LOGIC
# =============================================================================

print("\n" + "=" * 80)
print("34. STRUCTURED INVESTMENT DECISION")
print("=" * 80)


@dataclass
class BusinessCaseDecision:
    problem_materiality: bool
    strategic_alignment_score: float
    npv_value: float
    risk_score: float
    feasibility_score: float
    benefits_measurable: bool

    def approve_recommendation(self) -> bool:
        """
        A simplified decision rule for educational purposes.

        Real organizations normally use governance-specific approval criteria.
        """
        return (
            self.problem_materiality
            and self.strategic_alignment_score >= 6
            and self.npv_value > 0
            and self.risk_score <= 4
            and self.feasibility_score >= 6
            and self.benefits_measurable
        )


decision = BusinessCaseDecision(
    problem_materiality=True,
    strategic_alignment_score=8.2,
    npv_value=project_npv,
    risk_score=3.5,
    feasibility_score=feasibility.average_score(),
    benefits_measurable=True,
)

print(f"Problem materiality: {decision.problem_materiality}")
print(f"Strategic alignment: {decision.strategic_alignment_score:.2f}/10")
print(f"NPV: ${decision.npv_value:,.2f}")
print(f"Risk score: {decision.risk_score:.2f}/5")
print(f"Feasibility: {decision.feasibility_score:.2f}/10")
print(f"Benefits measurable: {decision.benefits_measurable}")
print(f"Investment rule result: {decision.approve_recommendation()}")


# =============================================================================
# 35. GATED APPROACH FOR HIGH-UNCERTAINTY PROJECTS
# =============================================================================

print("\n" + "=" * 80)
print("35. PHASED INVESTMENT AND STAGE GATES")
print("=" * 80)

print(
    """
When uncertainty is high, an organization does not always need to commit the
entire investment immediately.

A staged approach can be:

    Discovery
        |
        v
    Prototype / pilot
        |
        v
    Evidence review
        |
        v
    Limited rollout
        |
        v
    Full implementation

Each gate can require evidence about cost, demand, feasibility, risk, adoption,
or benefit realization before additional funds are committed.
"""
)


@dataclass
class StageGate:
    name: str
    required_evidence: List[str]
    passed: bool


stage_gates = [
    StageGate(
        "Discovery",
        ["Validated problem", "Baseline data", "Stakeholder agreement"],
        True,
    ),
    StageGate(
        "Pilot",
        ["Technical proof", "User adoption evidence", "Updated cost estimate"],
        True,
    ),
    StageGate(
        "Scale",
        ["Positive business results", "Risk controls", "Implementation capacity"],
        False,
    ),
]

for gate in stage_gates:
    print(f"\n{gate.name}: {'PASS' if gate.passed else 'HOLD'}")
    for evidence in gate.required_evidence:
        print(f"  - {evidence}")


# =============================================================================
# 36. REAL OPTIONS THINKING
# =============================================================================

print("\n" + "=" * 80)
print("36. REAL OPTIONS")
print("=" * 80)

print(
    """
Some projects create strategic flexibility that is not fully captured by
traditional NPV.

Examples:
    - A pilot can create the option to scale later.
    - A modular platform can enable future products.
    - A technology foundation can reduce future implementation time.
    - A small initial investment can generate information that improves a
      later investment decision.

The value of flexibility is especially important when uncertainty is high and
the organization can defer, expand, abandon, or change direction.
"""
)


# =============================================================================
# 37. SUNK COSTS AND FUTURE DECISIONS
# =============================================================================

print("\n" + "=" * 80)
print("37. SUNK COSTS")
print("=" * 80)

print(
    """
A sunk cost is a cost that has already been incurred and cannot be recovered.

Investment decisions should normally focus on:
    - Future costs
    - Future benefits
    - Avoidable costs
    - Opportunity costs
    - Risks

A project should not automatically continue merely because a large amount of
money has already been spent.
"""
)


# =============================================================================
# 38. STRATEGIC NECESSITY
# =============================================================================

print("\n" + "=" * 80)
print("38. PROJECTS THAT ARE NOT PURELY ROI-DRIVEN")
print("=" * 80)

strategic_necessity_examples = [
    "Regulatory compliance",
    "Cybersecurity risk reduction",
    "Critical infrastructure replacement",
    "Safety requirements",
    "Business continuity",
    "Mandatory contractual requirements",
]

for item in strategic_necessity_examples:
    print(f"- {item}")

print(
    "\nA project may be justified because failing to act creates unacceptable "
    "risk, even when direct financial returns are difficult to quantify."
)


# =============================================================================
# 39. SECURITY CONSIDERATIONS
# =============================================================================

print("\n" + "=" * 80)
print("39. SECURITY CONSIDERATIONS")
print("=" * 80)

security_questions = [
    "Does the proposed solution introduce new attack surfaces?",
    "Will sensitive data be processed or stored?",
    "Are identity and access controls adequate?",
    "Are third-party dependencies trustworthy?",
    "What is the cost of a security failure?",
    "Are security requirements included in project costs?",
    "Is regulatory exposure appropriately assessed?",
    "Are incident response and business continuity requirements addressed?",
]

for question in security_questions:
    print(f"- {question}")


# =============================================================================
# 40. DATA QUALITY AND BUSINESS CASE RISK
# =============================================================================

print("\n" + "=" * 80)
print("40. DATA QUALITY")
print("=" * 80)


@dataclass
class DataQualityCheck:
    metric_name: str
    source_known: bool
    current: float
    target: float
    confidence: float

    def is_reliable(self, threshold: float = 0.70) -> bool:
        return (
            self.source_known
            and 0 <= self.confidence <= 1
            and self.confidence >= threshold
        )


data_checks = [
    DataQualityCheck("Annual support cost", True, 1_020_000, 750_000, 0.90),
    DataQualityCheck("Customer complaints", True, 9_500, 6_000, 0.85),
    DataQualityCheck("Expected productivity gain", False, 20, 30, 0.45),
]

for check in data_checks:
    print(
        f"{check.metric_name}: confidence={check.confidence:.0%}, "
        f"reliable={check.is_reliable()}"
    )


# =============================================================================
# 41. COMMON BUSINESS CASE MISTAKES
# =============================================================================

print("\n" + "=" * 80)
print("41. COMMON BUSINESS CASE MISTAKES")
print("=" * 80)

mistakes = {
    "Starting with the solution": "Assuming a technology or product is needed before validating the problem.",
    "Ignoring the do-nothing option": "Failing to establish the baseline and cost of inaction.",
    "Overstating benefits": "Using optimistic assumptions without evidence.",
    "Underestimating total cost": "Ignoring maintenance, training, migration, support, or retirement.",
    "Ignoring opportunity cost": "Treating constrained resources as if they were unlimited.",
    "Ignoring risk": "Presenting only expected returns without uncertainty.",
    "Double-counting benefits": "Counting the same economic improvement more than once.",
    "Confusing revenue with profit": "Treating additional revenue as equivalent to additional cash value.",
    "Ignoring adoption": "Assuming a delivered capability automatically creates business value.",
    "Using inappropriate discount rates": "Applying a rate without understanding the organization's financial framework.",
    "Using poor baselines": "Comparing future performance against an inaccurate current state.",
    "Sunk-cost thinking": "Continuing because money has already been spent.",
}

for mistake, explanation in mistakes.items():
    print(f"\n{mistake}")
    print(f"  {explanation}")


# =============================================================================
# 42. DOUBLE-COUNTING EXAMPLE
# =============================================================================

print("\n" + "=" * 80)
print("42. DOUBLE-COUNTING BENEFITS")
print("=" * 80)

labor_savings = 300_000
productivity_value = 250_000

incorrect_total = labor_savings + productivity_value

print(f"Potential labor savings: ${labor_savings:,.0f}")
print(f"Potential productivity value: ${productivity_value:,.0f}")
print(f"Naive total: ${incorrect_total:,.0f}")

print(
    "\nBefore adding benefits, verify whether the productivity improvement is "
    "already represented by the labor-saving calculation. If so, adding both "
    "would overstate project value."
)


# =============================================================================
# 43. REVENUE, PROFIT, AND CASH FLOW DISTINCTION
# =============================================================================

print("\n" + "=" * 80)
print("43. REVENUE VERSUS PROFIT VERSUS CASH FLOW")
print("=" * 80)

additional_revenue = 2_000_000
additional_cost = 1_500_000
tax_and_other_cash_effects = 100_000

operating_profit = additional_revenue - additional_cost
simplified_cash_effect = operating_profit - tax_and_other_cash_effects

print(f"Additional revenue: ${additional_revenue:,.0f}")
print(f"Additional operating cost: ${additional_cost:,.0f}")
print(f"Operating profit contribution: ${operating_profit:,.0f}")
print(f"Simplified cash effect: ${simplified_cash_effect:,.0f}")

print(
    "\nRevenue alone does not establish project value. Costs, taxes, working "
    "capital, investment timing, and other cash effects may materially change "
    "the economic result."
)


# =============================================================================
# 44. BENEFIT REALIZATION SCORECARD
# =============================================================================

print("\n" + "=" * 80)
print("44. BENEFIT REALIZATION SCORECARD")
print("=" * 80)


@dataclass
class BenefitMetric:
    name: str
    baseline: float
    target: float
    actual: float
    owner: str

    def achievement_percentage(self) -> float:
        if self.target == self.baseline:
            return 100.0

        progress = (
            (self.actual - self.baseline)
            / (self.target - self.baseline)
        )

        return max(0.0, min(1.0, progress)) * 100

    def status(self) -> str:
        percentage = self.achievement_percentage()

        if percentage >= 100:
            return "Target achieved"
        if percentage >= 80:
            return "On track"
        if percentage >= 50:
            return "Needs attention"
        return "Off track"


benefit_metrics = [
    BenefitMetric(
        "Resolution time",
        baseline=48,
        target=12,
        actual=16,
        owner="Operations",
    ),
    BenefitMetric(
        "Customer satisfaction",
        baseline=68,
        target=85,
        actual=81,
        owner="Customer Experience",
    ),
    BenefitMetric(
        "Support cost",
        baseline=1_020_000,
        target=750_000,
        actual=790_000,
        owner="Finance",
    ),
]

for metric in benefit_metrics:
    print(
        f"{metric.name}: "
        f"baseline={metric.baseline}, "
        f"target={metric.target}, "
        f"actual={metric.actual}, "
        f"achievement={metric.achievement_percentage():.1f}%, "
        f"status={metric.status()}"
    )


# =============================================================================
# 45. GOVERNANCE AND ACCOUNTABILITY
# =============================================================================

print("\n" + "=" * 80)
print("45. GOVERNANCE")
print("=" * 80)

governance_roles = {
    "Executive sponsor": "Owns strategic sponsorship and major investment decisions.",
    "Business owner": "Owns the business outcome and benefit realization.",
    "Project manager": "Coordinates delivery, schedule, resources, and risks.",
    "Finance": "Reviews financial assumptions and investment economics.",
    "Risk/compliance": "Assesses material risk and regulatory exposure.",
    "Technology": "Assesses technical architecture, security, and feasibility.",
    "Users": "Provide operational requirements and adoption feedback.",
}

for role, responsibility in governance_roles.items():
    print(f"{role}: {responsibility}")


# =============================================================================
# 46. BUSINESS CASE STRUCTURE
# =============================================================================

print("\n" + "=" * 80)
print("46. BUSINESS CASE STRUCTURE")
print("=" * 80)

recommended_structure = [
    "Executive decision required",
    "Problem or opportunity",
    "Current state and baseline",
    "Strategic context",
    "Objectives and success measures",
    "Options considered",
    "Preferred option",
    "Scope and assumptions",
    "Benefits",
    "Costs and TCO",
    "Financial analysis",
    "Risk analysis",
    "Dependencies and constraints",
    "Implementation approach",
    "Governance",
    "Benefit realization plan",
    "Decision and approval criteria",
]

for section in recommended_structure:
    print(f"- {section}")


# =============================================================================
# 47. EXECUTIVE DECISION TEST
# =============================================================================

print("\n" + "=" * 80)
print("47. EXECUTIVE DECISION TEST")
print("=" * 80)


def executive_decision_questions() -> List[str]:
    return [
        "Is the problem important enough to justify action?",
        "Is the proposed change aligned with organizational strategy?",
        "Are credible alternatives evaluated?",
        "Is the preferred option superior under reasonable assumptions?",
        "Are costs complete and realistic?",
        "Are benefits measurable and owned?",
        "Is the financial case sufficiently attractive?",
        "What happens if the assumptions are wrong?",
        "What is the cost of doing nothing?",
        "Are major risks understood and manageable?",
        "Is the organization capable of delivering the change?",
        "What evidence should be required before full investment?",
    ]


for question in executive_decision_questions():
    print(f"- {question}")


# =============================================================================
# 48. COMPLETE BUSINESS CASE EXAMPLE
# =============================================================================

print("\n" + "=" * 80)
print("48. COMPLETE BUSINESS CASE EXAMPLE")
print("=" * 80)


@dataclass
class CompleteBusinessCase:
    project_name: str
    problem_statement: str
    strategic_objective: str
    initial_investment: float
    annual_benefit: float
    annual_operating_cost: float
    years: int
    discount_rate: float
    implementation_months: int
    risk_exposure: float

    def annual_net_benefit(self) -> float:
        return self.annual_benefit - self.annual_operating_cost

    def calculate_npv(self) -> float:
        return npv(
            self.initial_investment,
            [self.annual_net_benefit()] * self.years,
            self.discount_rate,
        )

    def calculate_payback(self) -> float:
        return payback_period(
            self.initial_investment,
            self.annual_net_benefit(),
        )

    def simple_roi(self) -> float:
        total_net_benefit = self.annual_net_benefit() * self.years
        return roi(self.initial_investment, total_net_benefit)

    def financial_case_is_positive(self) -> bool:
        return self.calculate_npv() > 0


complete_case = CompleteBusinessCase(
    project_name="Customer Support Transformation",
    problem_statement=(
        "Support resolution time and operating costs are materially above "
        "target levels."
    ),
    strategic_objective=(
        "Improve customer experience while increasing operating efficiency."
    ),
    initial_investment=1_000_000,
    annual_benefit=850_000,
    annual_operating_cost=300_000,
    years=5,
    discount_rate=0.10,
    implementation_months=9,
    risk_exposure=250_000,
)

print(f"Project: {complete_case.project_name}")
print(f"Problem: {complete_case.problem_statement}")
print(f"Strategic objective: {complete_case.strategic_objective}")
print(f"Initial investment: ${complete_case.initial_investment:,.0f}")
print(f"Annual benefit: ${complete_case.annual_benefit:,.0f}")
print(f"Annual operating cost: ${complete_case.annual_operating_cost:,.0f}")
print(f"Annual net benefit: ${complete_case.annual_net_benefit():,.0f}")
print(f"NPV: ${complete_case.calculate_npv():,.2f}")
print(f"Payback: {complete_case.calculate_payback():.2f} years")
print(f"Five-year simple ROI: {complete_case.simple_roi():.2%}")
print(f"Risk exposure: ${complete_case.risk_exposure:,.0f}")

print(
    "\nFinancial case positive:",
    complete_case.financial_case_is_positive(),
)


# =============================================================================
# 49. EDGE CASES
# =============================================================================

print("\n" + "=" * 80)
print("49. EDGE CASES")
print("=" * 80)

print("\nCase 1: No annual benefit")
print(f"Payback: {payback_period(100_000, 0)}")

print("\nCase 2: Negative annual cash benefit")
print(f"Payback: {payback_period(100_000, -50_000)}")

print("\nCase 3: Zero implementation investment")
print(f"ROI denominator must not be zero; this is handled by validation.")

try:
    roi(0, 100)
except ValueError as error:
    print(f"Handled error: {error}")

print("\nCase 4: Invalid risk probability")

try:
    invalid_risk = Risk(
        name="Invalid risk",
        probability=1.5,
        impact=100_000,
        response="None",
        owner="Unknown",
    )
    invalid_risk.validate()
except ValueError as error:
    print(f"Handled error: {error}")

print("\nCase 5: Invalid scenario probabilities")

try:
    expected_monetary_value(
        [
            Scenario("A", 0.60, 100),
            Scenario("B", 0.60, 200),
        ]
    )
except ValueError as error:
    print(f"Handled error: {error}")


# =============================================================================
# 50. COMPARISON OF COMMON FINANCIAL METRICS
# =============================================================================

print("\n" + "=" * 80)
print("50. FINANCIAL METRIC COMPARISON")
print("=" * 80)

metric_comparison = {
    "ROI": "Simple return relative to investment; easy to communicate.",
    "Payback": "Time required to recover the initial investment.",
    "NPV": "Present value of future cash flows less initial investment.",
    "IRR": "Discount rate at which NPV becomes zero.",
    "Benefit-cost ratio": "Discounted benefits divided by discounted costs.",
    "TCO": "Total cost of owning and operating a solution over a defined period.",
}

for metric, description in metric_comparison.items():
    print(f"{metric}: {description}")


# =============================================================================
# 51. LIMITATIONS OF FINANCIAL METRICS
# =============================================================================

print("\n" + "=" * 80)
print("51. LIMITATIONS OF FINANCIAL METRICS")
print("=" * 80)

limitations = [
    "Financial forecasts depend on assumptions.",
    "Intangible benefits can be difficult to monetize.",
    "Strategic flexibility may not be fully represented.",
    "Risk estimates may be uncertain.",
    "Cash-flow timing can be difficult to forecast.",
    "Different projects may have different strategic purposes.",
    "A positive NPV does not guarantee successful execution.",
    "A negative direct ROI does not automatically mean a project should be rejected.",
]

for limitation in limitations:
    print(f"- {limitation}")


# =============================================================================
# 52. PERFORMANCE AND IMPLEMENTATION CONSIDERATIONS
# =============================================================================

print("\n" + "=" * 80)
print("52. IMPLEMENTATION CONSIDERATIONS")
print("=" * 80)

implementation_considerations = [
    "Scope clarity",
    "Resource availability",
    "Delivery dependencies",
    "Procurement lead time",
    "Technology readiness",
    "Data migration",
    "Integration complexity",
    "Security requirements",
    "Training and change management",
    "Operational support",
    "Vendor management",
    "Benefits tracking",
]

for consideration in implementation_considerations:
    print(f"- {consideration}")


# =============================================================================
# 53. BUSINESS CASE QUALITY CHECK
# =============================================================================

print("\n" + "=" * 80)
print("53. BUSINESS CASE QUALITY CHECK")
print("=" * 80)


@dataclass
class BusinessCaseQuality:
    problem_defined: bool
    baseline_available: bool
    alternatives_evaluated: bool
    benefits_quantified: bool
    costs_complete: bool
    risks_assessed: bool
    strategic_alignment_defined: bool
    implementation_feasible: bool
    benefit_owner_defined: bool

    def score(self) -> float:
        checks = [
            self.problem_defined,
            self.baseline_available,
            self.alternatives_evaluated,
            self.benefits_quantified,
            self.costs_complete,
            self.risks_assessed,
            self.strategic_alignment_defined,
            self.implementation_feasible,
            self.benefit_owner_defined,
        ]

        return sum(checks) / len(checks) * 100

    def passed(self, minimum: float = 80) -> bool:
        return self.score() >= minimum


quality = BusinessCaseQuality(
    problem_defined=True,
    baseline_available=True,
    alternatives_evaluated=True,
    benefits_quantified=True,
    costs_complete=True,
    risks_assessed=True,
    strategic_alignment_defined=True,
    implementation_feasible=True,
    benefit_owner_defined=True,
)

print(f"Business case quality score: {quality.score():.1f}%")
print(f"Quality threshold passed: {quality.passed()}")


# =============================================================================
# 54. TESTS
# =============================================================================

print("\n" + "=" * 80)
print("54. BASIC VALIDATION TESTS")
print("=" * 80)


def run_tests() -> None:
    """Run simple assertions to verify the analytical functions."""

    assert abs(present_value(110, 0.10, 1) - 100) < 1e-9

    assert abs(payback_period(1_000, 200) - 5) < 1e-9

    assert abs(roi(100, 25) - 0.25) < 1e-9

    assert abs(
        expected_monetary_value(
            [
                Scenario("A", 0.5, 100),
                Scenario("B", 0.5, 200),
            ]
        )
        - 150
    ) < 1e-9

    assert abs(
        weighted_option_score(
            {"Financial": 8, "Strategic": 6},
            [
                EvaluationCriterion("Financial", 0.5),
                EvaluationCriterion("Strategic", 0.5),
            ],
        )
        - 7
    ) < 1e-9

    assert complete_case.calculate_npv() > 0

    print("All tests passed.")


run_tests()


# =============================================================================
# 55. FINAL DECISION FRAMEWORK
# =============================================================================

print("\n" + "=" * 80)
print("55. FINAL DECISION FRAMEWORK")
print("=" * 80)

decision_framework = [
    ("1. Need", "Is there a material problem or opportunity?"),
    ("2. Evidence", "Is the current state supported by credible data?"),
    ("3. Objectives", "Are the desired outcomes specific and measurable?"),
    ("4. Alternatives", "Have credible options, including doing nothing, been considered?"),
    ("5. Value", "Do expected benefits justify the required investment?"),
    ("6. Economics", "Do NPV, ROI, payback, or related metrics support the case?"),
    ("7. Risk", "Are uncertainty and downside risks understood?"),
    ("8. Strategy", "Does the initiative support organizational priorities?"),
    ("9. Feasibility", "Can the organization actually deliver and operate it?"),
    ("10. Benefits", "Are benefits measurable, owned, and tracked?"),
    ("11. Governance", "Are decision rights and approval gates clear?"),
    ("12. Recommendation", "Is there sufficient evidence to make an investment decision?"),
]

for stage, question in decision_framework:
    print(f"{stage}: {question}")


# =============================================================================
# 56. CONCEPTUAL DECISION EXAMPLE
# =============================================================================

print("\n" + "=" * 80)
print("56. CONCEPTUAL DECISION EXAMPLE")
print("=" * 80)

financial_npv = complete_case.calculate_npv()
financial_positive = financial_npv > 0
strategic_positive = weighted_strategic_score >= 6
feasibility_positive = feasibility.is_feasible()
risk_acceptable = decision.risk_score <= 4
benefits_measurable = decision.benefits_measurable

print(f"Positive financial NPV: {financial_positive}")
print(f"Acceptable strategic alignment: {strategic_positive}")
print(f"Feasible: {feasibility_positive}")
print(f"Risk within threshold: {risk_acceptable}")
print(f"Benefits measurable: {benefits_measurable}")

recommendation = (
    "Proceed to the next investment gate."
    if all(
        [
            financial_positive,
            strategic_positive,
            feasibility_positive,
            risk_acceptable,
            benefits_measurable,
        ]
    )
    else "Do not approve full investment yet; address failed decision criteria."
)

print(f"\nRecommendation: {recommendation}")


# =============================================================================
# 57. IMPORTANT DISTINCTION: BUSINESS CASE VERSUS PROJECT PLAN
# =============================================================================

print("\n" + "=" * 80)
print("57. BUSINESS CASE VERSUS PROJECT PLAN")
print("=" * 80)

comparison = {
    "Business case": (
        "Explains why the investment should be made and what value is expected."
    ),
    "Project charter": (
        "Authorizes and defines the project at a high level."
    ),
    "Project plan": (
        "Explains how the approved project will be delivered."
    ),
    "Benefits realization plan": (
        "Explains how expected benefits will be measured and achieved."
    ),
}

for artifact, purpose in comparison.items():
    print(f"{artifact}: {purpose}")


# =============================================================================
# 58. IMPORTANT DISTINCTION: OUTPUTS, OUTCOMES, AND BENEFITS
# =============================================================================

print("\n" + "=" * 80)
print("58. OUTPUTS, OUTCOMES, AND BENEFITS")
print("=" * 80)

print(
    """
Output:
    Something produced by the project.

Outcome:
    A change resulting from use of the project output.

Benefit:
    A measurable advantage resulting from the outcome.

Example:

    Output:
        New customer-support platform.

    Outcome:
        Support employees resolve requests faster.

    Benefit:
        Lower support cost and improved customer satisfaction.
"""
)


# =============================================================================
# 59. PRODUCTION-QUALITY BUSINESS CASE PRINCIPLES
# =============================================================================

print("\n" + "=" * 80)
print("59. BEST PRACTICES")
print("=" * 80)

best_practices = [
    "Start with the business problem rather than a preferred technology.",
    "Use a credible baseline.",
    "Separate assumptions from verified facts.",
    "Include the do-nothing option.",
    "Compare multiple realistic alternatives.",
    "Quantify benefits where credible evidence exists.",
    "Avoid double-counting benefits.",
    "Include the full lifecycle cost.",
    "Account for adoption and benefit realization.",
    "Use appropriate financial evaluation methods.",
    "Test assumptions through sensitivity and scenario analysis.",
    "Make risk ownership explicit.",
    "Consider strategic and non-financial value.",
    "Use stage gates when uncertainty is high.",
    "Define measurable success criteria.",
    "Assign benefit owners.",
    "Update the business case when material assumptions change.",
    "Treat the business case as a decision instrument, not merely a funding form.",
]

for practice in best_practices:
    print(f"- {practice}")


# =============================================================================
# 60. END-TO-END BUSINESS CASE CHECKLIST
# =============================================================================

print("\n" + "=" * 80)
print("60. END-TO-END BUSINESS CASE CHECKLIST")
print("=" * 80)

checklist = [
    "Problem or opportunity clearly defined",
    "Current-state baseline documented",
    "Consequences of inaction identified",
    "Strategic objectives identified",
    "Measurable objectives established",
    "Alternative options identified",
    "Do-nothing option assessed",
    "Preferred option justified",
    "Costs identified across the lifecycle",
    "Benefits identified and categorized",
    "Benefits quantified where appropriate",
    "Benefits owners assigned",
    "Assumptions documented",
    "Constraints documented",
    "Risks identified",
    "Risk responses defined",
    "Financial model prepared",
    "ROI considered where useful",
    "Payback considered where useful",
    "NPV considered where appropriate",
    "IRR considered where appropriate",
    "TCO assessed",
    "Sensitivity analysis completed",
    "Scenario analysis completed",
    "Technical feasibility assessed",
    "Operational feasibility assessed",
    "Organizational readiness assessed",
    "Security and compliance considered",
    "Implementation approach defined",
    "Governance defined",
    "Decision gates defined",
    "Recommendation supported by evidence",
]

completed_items = 0

for item in checklist:
    completed_items += 1
    print(f"[x] {item}")

print(
    f"\nBusiness case checklist demonstrated: "
    f"{completed_items}/{len(checklist)} analytical areas."
)


# =============================================================================
# 61. KEY RELATIONSHIPS IN A BUSINESS CASE
# =============================================================================

print("\n" + "=" * 80)
print("61. KEY RELATIONSHIPS")
print("=" * 80)

relationships = [
    "Problem severity influences the urgency of action.",
    "Baseline quality influences benefit credibility.",
    "Option selection influences both value and risk.",
    "Scope influences cost, schedule, and benefit potential.",
    "Adoption influences benefit realization.",
    "Risk influences the probability of achieving expected value.",
    "Timing influences present value.",
    "Strategic alignment influences organizational priority.",
    "Feasibility influences whether the expected value can actually be delivered.",
    "Governance influences whether investment remains justified as circumstances change.",
]

for relationship in relationships:
    print(f"- {relationship}")


# =============================================================================
# 62. COMPLETION MESSAGE
# =============================================================================

print("\n" + "=" * 80)
print("END OF BUSINESS CASE STUDY SCRIPT")
print("=" * 80)

print(
    """
The calculations and examples in this script demonstrate how a business case
connects business need, alternatives, costs, benefits, risk, strategy,
financial evaluation, feasibility, and governance into a structured investment
decision.
"""
)
