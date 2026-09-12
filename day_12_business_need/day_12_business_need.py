"""
BUSINESS NEED: IDENTIFYING THE REASON FOR A PROJECT

A comprehensive study script covering how to identify, analyze, validate,
prioritize, and document the business need that gives a project its reason
for existence.

The examples use Python to make project-management concepts executable.
The script is intentionally self-contained and uses only the Python standard
library.

Topics covered:
- Business need versus project idea
- Problem, symptom, opportunity, requirement, objective, and solution
- Current state and future state
- Gap analysis
- Problem statements
- Root-cause analysis
- Five Whys
- Cause-and-effect analysis
- Stakeholder perspectives
- Quantifying business impact
- Cost of inaction
- Opportunity sizing
- Need validation
- Evidence quality
- Assumptions and constraints
- Risk of solving the wrong problem
- Business need prioritization
- Weighted scoring
- Urgency, impact, strategic alignment, and feasibility
- Project versus operational problem
- Outcome versus output
- SMART objectives
- KPIs and baseline measurements
- Benefits realization
- Business case logic
- Cost-benefit analysis
- ROI and payback period
- Sensitivity analysis
- Scenario analysis
- Decision trees
- Traceability from need to project
- Requirements traceability
- Scope boundaries
- Common mistakes
- Edge cases
- Governance and decision gates
- Production-oriented validation
- A complete worked case study
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ============================================================================
# FUNDAMENTAL TERMINOLOGY
# ============================================================================

class NeedType(Enum):
    """
    Common categories of business needs.

    COMPLIANCE:
        The organization must satisfy a law, regulation, contract, policy,
        audit requirement, or mandatory standard.

    PROBLEM:
        Existing performance is below an acceptable level.

    OPPORTUNITY:
        A favorable possibility exists, but the organization is not required
        to act.

    STRATEGIC:
        A project is needed to support a strategic direction or organizational
        capability.

    CUSTOMER:
        A customer experience, service, retention, quality, or satisfaction
        issue creates the need.

    OPERATIONAL:
        Internal processes, productivity, capacity, reliability, or cost
        require improvement.

    RISK:
        A material risk requires mitigation or increased resilience.
    """

    COMPLIANCE = "Compliance"
    PROBLEM = "Problem"
    OPPORTUNITY = "Opportunity"
    STRATEGIC = "Strategic"
    CUSTOMER = "Customer"
    OPERATIONAL = "Operational"
    RISK = "Risk"


@dataclass
class BusinessNeed:
    """
    Represents the reason an organization may need to initiate a project.

    A business need should describe the underlying organizational condition,
    not prematurely prescribe a technical solution.
    """

    title: str
    description: str
    need_type: NeedType
    affected_area: str
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: str = ""
    annual_impact: float = 0.0
    strategic_alignment: float = 0.0
    urgency: float = 0.0
    confidence: float = 0.0
    feasibility: float = 0.0
    evidence: List[str] = field(default_factory=list)

    def gap(self) -> Optional[float]:
        """Return target minus baseline when both are numeric."""
        if self.baseline_value is None or self.target_value is None:
            return None
        return self.target_value - self.baseline_value

    def evidence_count(self) -> int:
        """Return the number of evidence items supporting the need."""
        return len(self.evidence)


# ============================================================================
# BASIC DISTINCTIONS
# ============================================================================

def explain_core_distinctions() -> None:
    """
    Demonstrate distinctions that prevent weak project definitions.

    The central principle is:

        Business Need -> Desired Outcome -> Project Objective -> Deliverables
        -> Activities

    A project should not begin with a preferred solution and then invent a
    justification afterward.
    """

    examples = {
        "business_need": (
            "Customer service response times are consistently above the "
            "organization's acceptable threshold."
        ),
        "problem": (
            "Average customer response time is 18 hours while the target "
            "is 4 hours."
        ),
        "symptom": (
            "Customers are submitting repeated follow-up requests."
        ),
        "opportunity": (
            "Reducing response time may improve customer retention."
        ),
        "requirement": (
            "Customer inquiries must receive an initial response within "
            "4 hours during business hours."
        ),
        "solution": (
            "Implement a new customer-service ticketing platform."
        ),
        "project_output": (
            "A configured and deployed customer-service ticketing system."
        ),
        "business_outcome": (
            "Customer response time falls from 18 hours to 4 hours."
        ),
    }

    print("\nCORE DISTINCTIONS")
    for concept, explanation in examples.items():
        print(f"{concept:18}: {explanation}")


def compare_need_and_solution() -> None:
    """
    Show why a business need should be defined independently of a solution.
    """

    weak_definition = "We need a new CRM."
    stronger_definition = (
        "Sales opportunities are being lost because customer information "
        "is fragmented across spreadsheets and disconnected systems."
    )

    print("\nNEED VS SOLUTION")
    print("Weak definition:")
    print(weak_definition)
    print("\nStronger definition:")
    print(stronger_definition)


# ============================================================================
# CURRENT STATE, FUTURE STATE, AND GAP
# ============================================================================

@dataclass
class PerformanceMetric:
    """Represents a measurable business condition."""

    name: str
    baseline: float
    target: float
    unit: str
    direction: str = "higher_is_better"

    def gap(self) -> float:
        """Calculate the raw numerical difference between target and baseline."""
        return self.target - self.baseline

    def improvement_required(self) -> float:
        """
        Calculate the relative improvement required.

        For metrics where lower is better, such as cost or processing time,
        the sign is normalized so the result represents improvement magnitude.
        """
        if self.baseline == 0:
            return float("inf")

        if self.direction == "higher_is_better":
            return (self.target - self.baseline) / abs(self.baseline)

        if self.direction == "lower_is_better":
            return (self.baseline - self.target) / abs(self.baseline)

        raise ValueError(
            "direction must be 'higher_is_better' or 'lower_is_better'"
        )


def demonstrate_gap_analysis() -> None:
    """Demonstrate how a business need can be expressed as a measurable gap."""

    metrics = [
        PerformanceMetric(
            name="Average order processing time",
            baseline=36,
            target=12,
            unit="hours",
            direction="lower_is_better",
        ),
        PerformanceMetric(
            name="Order accuracy",
            baseline=91,
            target=98,
            unit="percent",
            direction="higher_is_better",
        ),
        PerformanceMetric(
            name="Customer satisfaction",
            baseline=3.4,
            target=4.3,
            unit="score",
            direction="higher_is_better",
        ),
    ]

    print("\nGAP ANALYSIS")

    for metric in metrics:
        print(f"\nMetric: {metric.name}")
        print(f"Baseline: {metric.baseline} {metric.unit}")
        print(f"Target:   {metric.target} {metric.unit}")
        print(f"Raw gap:  {metric.gap():.2f} {metric.unit}")

        improvement = metric.improvement_required() * 100

        if isfinite(improvement):
            print(f"Required improvement: {improvement:.1f}%")
        else:
            print("Required improvement: undefined because baseline is zero")


# ============================================================================
# PROBLEM STATEMENTS
# ============================================================================

@dataclass
class ProblemStatement:
    """
    A structured problem statement.

    A useful problem statement normally identifies:
    - who or what is affected,
    - what is happening,
    - where it happens,
    - when or how often it happens,
    - measurable impact,
    - and why it matters.
    """

    affected_group: str
    current_condition: str
    context: str
    measurable_impact: str
    business_consequence: str

    def render(self) -> str:
        return (
            f"{self.affected_group} experiences {self.current_condition} "
            f"in {self.context}. The measurable impact is "
            f"{self.measurable_impact}, resulting in "
            f"{self.business_consequence}."
        )


def demonstrate_problem_statement() -> None:
    """Create a precise problem statement."""

    statement = ProblemStatement(
        affected_group="Customers",
        current_condition="long delays before receiving support responses",
        context="the digital support channel",
        measurable_impact="the average first-response time is 18 hours",
        business_consequence="higher abandonment and lower satisfaction",
    )

    print("\nPROBLEM STATEMENT")
    print(statement.render())


# ============================================================================
# ROOT-CAUSE ANALYSIS
# ============================================================================

def five_whys(problem: str, whys: Sequence[str]) -> List[str]:
    """
    Represent a Five Whys investigation.

    The Five Whys method is not literally limited to exactly five questions.
    Five is a heuristic. The investigation should stop when the team reaches
    a sufficiently actionable underlying cause supported by evidence.

    The supplied answers are returned as an ordered chain.
    """

    if not problem.strip():
        raise ValueError("Problem cannot be empty.")

    if not whys:
        raise ValueError("At least one why-answer is required.")

    return list(whys)


def demonstrate_five_whys() -> None:
    """Show a complete Five Whys example."""

    problem = "Customer support responses are too slow."

    answers = five_whys(
        problem,
        [
            "Because many requests remain in the queue for several hours.",
            "Because requests are manually assigned and prioritized.",
            "Because there is no consistent routing or priority mechanism.",
            "Because customer information and request categories are stored "
            "in separate systems.",
            "Because the current support process evolved without an integrated "
            "workflow architecture.",
        ],
    )

    print("\nFIVE WHYS")
    print(f"Initial problem: {problem}")

    for index, answer in enumerate(answers, start=1):
        print(f"Why {index}: {answer}")


@dataclass
class Cause:
    """Represents a possible contributing cause."""

    category: str
    description: str
    evidence_strength: float
    controllability: float


def rank_root_causes(causes: Sequence[Cause]) -> List[Cause]:
    """
    Rank causes using evidence strength and controllability.

    This is not a universal root-cause formula. It is an analytical aid.
    """

    return sorted(
        causes,
        key=lambda cause: (
            cause.evidence_strength * 0.6
            + cause.controllability * 0.4
        ),
        reverse=True,
    )


def demonstrate_cause_analysis() -> None:
    """Rank possible causes before deciding what to address."""

    causes = [
        Cause(
            category="Process",
            description="Manual request assignment",
            evidence_strength=9,
            controllability=9,
        ),
        Cause(
            category="Technology",
            description="Disconnected customer information",
            evidence_strength=8,
            controllability=8,
        ),
        Cause(
            category="People",
            description="Insufficient training",
            evidence_strength=4,
            controllability=7,
        ),
        Cause(
            category="Demand",
            description="Unexpected seasonal request volume",
            evidence_strength=6,
            controllability=3,
        ),
    ]

    ranked = rank_root_causes(causes)

    print("\nROOT-CAUSE PRIORITIZATION")

    for position, cause in enumerate(ranked, start=1):
        score = (
            cause.evidence_strength * 0.6
            + cause.controllability * 0.4
        )
        print(
            f"{position}. {cause.category}: {cause.description} "
            f"(score={score:.2f})"
        )


# ============================================================================
# EVIDENCE QUALITY
# ============================================================================

class EvidenceQuality(Enum):
    """A simple classification of evidence strength."""

    WEAK = 1
    MODERATE = 2
    STRONG = 3


@dataclass
class Evidence:
    """Evidence supporting a business need."""

    source: str
    description: str
    quality: EvidenceQuality
    measurable: bool
    independently_verified: bool = False

    def score(self) -> float:
        """Calculate a simple evidence-confidence score."""
        score = float(self.quality.value)

        if self.measurable:
            score += 1.0

        if self.independently_verified:
            score += 1.0

        return score


def assess_evidence(evidence_items: Sequence[Evidence]) -> float:
    """
    Calculate average evidence strength.

    This score is illustrative. Real governance systems should define their
    own evidence standards.
    """

    if not evidence_items:
        return 0.0

    return sum(item.score() for item in evidence_items) / len(evidence_items)


def demonstrate_evidence_assessment() -> None:
    """Compare evidence sources supporting a proposed business need."""

    evidence = [
        Evidence(
            source="Service analytics",
            description="Response-time dashboard",
            quality=EvidenceQuality.STRONG,
            measurable=True,
            independently_verified=True,
        ),
        Evidence(
            source="Customer survey",
            description="Customers report long waiting times",
            quality=EvidenceQuality.MODERATE,
            measurable=True,
        ),
        Evidence(
            source="Manager opinion",
            description="Support manager believes delays are increasing",
            quality=EvidenceQuality.WEAK,
            measurable=False,
        ),
    ]

    score = assess_evidence(evidence)

    print("\nEVIDENCE ASSESSMENT")

    for item in evidence:
        print(
            f"{item.source}: {item.description} "
            f"(score={item.score():.1f})"
        )

    print(f"Average evidence score: {score:.2f}")


# ============================================================================
# STAKEHOLDER ANALYSIS
# ============================================================================

@dataclass
class Stakeholder:
    """Represents a stakeholder affected by or able to influence a need."""

    name: str
    interest: int
    influence: int
    impact: int
    perspective: str

    def priority_score(self) -> float:
        """
        Prioritize stakeholder attention.

        Influence and impact are weighted more heavily than interest because
        they usually have stronger implications for decision-making.
        """

        return (
            self.interest * 0.2
            + self.influence * 0.4
            + self.impact * 0.4
        )


def rank_stakeholders(stakeholders: Sequence[Stakeholder]) -> List[Stakeholder]:
    """Return stakeholders from highest to lowest engagement priority."""

    return sorted(
        stakeholders,
        key=lambda stakeholder: stakeholder.priority_score(),
        reverse=True,
    )


def demonstrate_stakeholder_analysis() -> None:
    """Analyze different views of the same business need."""

    stakeholders = [
        Stakeholder(
            name="Customer",
            interest=10,
            influence=6,
            impact=10,
            perspective="Wants faster and more predictable support.",
        ),
        Stakeholder(
            name="Support Manager",
            interest=10,
            influence=9,
            impact=9,
            perspective="Needs better routing and workload visibility.",
        ),
        Stakeholder(
            name="Finance",
            interest=6,
            influence=9,
            impact=7,
            perspective="Needs measurable financial justification.",
        ),
        Stakeholder(
            name="Technology",
            interest=7,
            influence=8,
            impact=8,
            perspective="Needs realistic architecture and integration scope.",
        ),
    ]

    ranked = rank_stakeholders(stakeholders)

    print("\nSTAKEHOLDER ANALYSIS")

    for stakeholder in ranked:
        print(
            f"{stakeholder.name}: score={stakeholder.priority_score():.2f}; "
            f"perspective={stakeholder.perspective}"
        )


# ============================================================================
# BUSINESS IMPACT
# ============================================================================

@dataclass
class ImpactEstimate:
    """
    Quantifies a potential consequence of the current business condition.
    """

    category: str
    annual_cost: float
    confidence: float
    explanation: str

    def weighted_cost(self) -> float:
        """Adjust estimated impact by confidence."""
        return self.annual_cost * self.confidence


def calculate_total_impact(impacts: Sequence[ImpactEstimate]) -> float:
    """Calculate confidence-adjusted annual impact."""

    return sum(item.weighted_cost() for item in impacts)


def demonstrate_business_impact() -> None:
    """Estimate annual consequences of a business problem."""

    impacts = [
        ImpactEstimate(
            category="Lost productivity",
            annual_cost=180000,
            confidence=0.85,
            explanation="Time spent manually processing requests.",
        ),
        ImpactEstimate(
            category="Customer churn",
            annual_cost=250000,
            confidence=0.65,
            explanation="Estimated revenue lost from dissatisfied customers.",
        ),
        ImpactEstimate(
            category="Rework",
            annual_cost=90000,
            confidence=0.90,
            explanation="Repeated requests and duplicated processing.",
        ),
    ]

    total = calculate_total_impact(impacts)

    print("\nBUSINESS IMPACT")

    for impact in impacts:
        print(
            f"{impact.category}: estimated={impact.annual_cost:,.0f}, "
            f"confidence-adjusted={impact.weighted_cost():,.0f}"
        )

    print(f"Total confidence-adjusted annual impact: {total:,.0f}")


# ============================================================================
# COST OF INACTION
# ============================================================================

def calculate_cost_of_inaction(
    annual_impact: float,
    years: int,
    annual_growth_rate: float = 0.0,
) -> float:
    """
    Estimate cumulative cost of leaving a business problem unresolved.

    This model assumes the impact grows at a constant annual rate and does
    not discount future cash flows. A financial business case may use NPV
    instead.
    """

    if annual_impact < 0:
        raise ValueError("Annual impact cannot be negative.")

    if years < 0:
        raise ValueError("Years cannot be negative.")

    if annual_growth_rate <= -1:
        raise ValueError("Annual growth rate must be greater than -100%.")

    total = 0.0
    current_impact = annual_impact

    for _ in range(years):
        total += current_impact
        current_impact *= 1 + annual_growth_rate

    return total


def demonstrate_cost_of_inaction() -> None:
    """Calculate how an unresolved problem can accumulate financial impact."""

    annual_impact = 500_000

    print("\nCOST OF INACTION")

    for years in (1, 3, 5):
        cost = calculate_cost_of_inaction(
            annual_impact=annual_impact,
            years=years,
            annual_growth_rate=0.05,
        )
        print(f"{years}-year estimated impact: {cost:,.0f}")


# ============================================================================
# BUSINESS NEED PRIORITIZATION
# ============================================================================

@dataclass
class PriorityCandidate:
    """A candidate business need that can be compared with others."""

    name: str
    strategic_alignment: float
    business_impact: float
    urgency: float
    customer_impact: float
    regulatory_importance: float
    feasibility: float
    confidence: float

    def weighted_score(self) -> float:
        """
        Calculate a normalized prioritization score.

        Each input is expected to be on a 0-10 scale.
        """

        weights = {
            "strategic_alignment": 0.20,
            "business_impact": 0.25,
            "urgency": 0.15,
            "customer_impact": 0.15,
            "regulatory_importance": 0.10,
            "feasibility": 0.10,
            "confidence": 0.05,
        }

        values = {
            "strategic_alignment": self.strategic_alignment,
            "business_impact": self.business_impact,
            "urgency": self.urgency,
            "customer_impact": self.customer_impact,
            "regulatory_importance": self.regulatory_importance,
            "feasibility": self.feasibility,
            "confidence": self.confidence,
        }

        return sum(values[key] * weight for key, weight in weights.items())


def validate_score(value: float, name: str) -> None:
    """Ensure a prioritization value is on a 0-10 scale."""

    if not 0 <= value <= 10:
        raise ValueError(f"{name} must be between 0 and 10.")


def validate_candidate(candidate: PriorityCandidate) -> None:
    """Validate all scoring dimensions."""

    fields = [
        "strategic_alignment",
        "business_impact",
        "urgency",
        "customer_impact",
        "regulatory_importance",
        "feasibility",
        "confidence",
    ]

    for field_name in fields:
        validate_score(
            getattr(candidate, field_name),
            field_name,
        )


def prioritize_needs(
    candidates: Sequence[PriorityCandidate],
) -> List[PriorityCandidate]:
    """Return validated business needs in descending priority order."""

    for candidate in candidates:
        validate_candidate(candidate)

    return sorted(
        candidates,
        key=lambda candidate: candidate.weighted_score(),
        reverse=True,
    )


def demonstrate_prioritization() -> None:
    """Compare several possible business needs."""

    candidates = [
        PriorityCandidate(
            name="Reduce support response time",
            strategic_alignment=9,
            business_impact=9,
            urgency=8,
            customer_impact=10,
            regulatory_importance=2,
            feasibility=8,
            confidence=9,
        ),
        PriorityCandidate(
            name="Modernize internal reporting",
            strategic_alignment=7,
            business_impact=6,
            urgency=5,
            customer_impact=3,
            regulatory_importance=1,
            feasibility=9,
            confidence=8,
        ),
        PriorityCandidate(
            name="Automate compliance reporting",
            strategic_alignment=8,
            business_impact=8,
            urgency=9,
            customer_impact=4,
            regulatory_importance=10,
            feasibility=6,
            confidence=9,
        ),
    ]

    ranked = prioritize_needs(candidates)

    print("\nBUSINESS NEED PRIORITIZATION")

    for position, candidate in enumerate(ranked, start=1):
        print(
            f"{position}. {candidate.name}: "
            f"{candidate.weighted_score():.2f}/10"
        )


# ============================================================================
# OPPORTUNITY VS PROBLEM VS COMPLIANCE
# ============================================================================

def classify_business_situation(
    current_condition: str,
    mandatory: bool,
    measurable_gap_exists: bool,
    favorable_opportunity_exists: bool,
) -> NeedType:
    """
    Classify a business situation using simple decision logic.

    Mandatory conditions take precedence because compliance obligations can
    require action even when the organization cannot demonstrate an immediate
    financial opportunity.
    """

    if mandatory:
        return NeedType.COMPLIANCE

    if measurable_gap_exists:
        return NeedType.PROBLEM

    if favorable_opportunity_exists:
        return NeedType.OPPORTUNITY

    return NeedType.STRATEGIC


def demonstrate_need_classification() -> None:
    """Demonstrate classification of business situations."""

    scenarios = [
        (
            "New regulatory reporting requirement",
            True,
            False,
            False,
        ),
        (
            "Order accuracy below target",
            False,
            True,
            False,
        ),
        (
            "Untapped market segment",
            False,
            False,
            True,
        ),
        (
            "Long-term capability requirement",
            False,
            False,
            False,
        ),
    ]

    print("\nBUSINESS NEED CLASSIFICATION")

    for scenario in scenarios:
        title, mandatory, gap_exists, opportunity = scenario

        classification = classify_business_situation(
            current_condition=title,
            mandatory=mandatory,
            measurable_gap_exists=gap_exists,
            favorable_opportunity_exists=opportunity,
        )

        print(f"{title}: {classification.value}")


# ============================================================================
# PROJECT OR OPERATIONAL IMPROVEMENT?
# ============================================================================

def classify_work(
    requires_temporary_change: bool,
    creates_unique_deliverable: bool,
    has_defined_start_and_end: bool,
    requires_repeated_execution: bool,
) -> str:
    """
    Distinguish a likely project from ongoing operations.

    A real organization may use more nuanced criteria.
    """

    project_signals = sum(
        [
            requires_temporary_change,
            creates_unique_deliverable,
            has_defined_start_and_end,
        ]
    )

    if requires_repeated_execution and project_signals <= 1:
        return "Likely operational work"

    if project_signals >= 2:
        return "Likely project work"

    return "Requires further analysis"


def demonstrate_project_vs_operations() -> None:
    """Show why not every business need should become a project."""

    examples = [
        (
            "Implement a new order-management system",
            True,
            True,
            True,
            False,
        ),
        (
            "Process daily customer orders",
            False,
            False,
            False,
            True,
        ),
        (
            "Redesign warehouse workflow",
            True,
            True,
            True,
            False,
        ),
    ]

    print("\nPROJECT VS OPERATIONS")

    for example in examples:
        result = classify_work(*example[1:])
        print(f"{example[0]}: {result}")


# ============================================================================
# OUTCOME, OUTPUT, OBJECTIVE, AND DELIVERABLE
# ============================================================================

@dataclass
class Objective:
    """Represents a measurable project objective."""

    name: str
    baseline: float
    target: float
    unit: str
    deadline_days: int
    direction: str

    def is_valid(self) -> bool:
        """Validate basic objective structure."""

        if not self.name.strip():
            return False

        if self.deadline_days <= 0:
            return False

        if self.direction not in {"higher", "lower"}:
            return False

        return self.target != self.baseline


def demonstrate_outcome_structure() -> None:
    """
    Show the hierarchy from business need to measurable business result.
    """

    hierarchy = [
        (
            "Business need",
            "Customer support performance is below acceptable levels.",
        ),
        (
            "Business objective",
            "Reduce average first-response time from 18 hours to 4 hours.",
        ),
        (
            "Project",
            "Improve the customer-support workflow and supporting systems.",
        ),
        (
            "Deliverable",
            "Configured workflow, routing rules, reporting, and integrations.",
        ),
        (
            "Outcome",
            "Support requests receive faster and more consistent responses.",
        ),
        (
            "Benefit",
            "Improved customer satisfaction and reduced service-related loss.",
        ),
    ]

    print("\nNEED TO BENEFIT CHAIN")

    for level, statement in hierarchy:
        print(f"{level:18}: {statement}")


# ============================================================================
# SMART OBJECTIVES
# ============================================================================

@dataclass
class SMARTObjective:
    """Represents a testable SMART objective."""

    specific: str
    measurable: str
    achievable: str
    relevant: str
    time_bound: str

    def validate(self) -> Dict[str, bool]:
        """Return validation results for each SMART dimension."""

        return {
            "Specific": bool(self.specific.strip()),
            "Measurable": bool(self.measurable.strip()),
            "Achievable": bool(self.achievable.strip()),
            "Relevant": bool(self.relevant.strip()),
            "Time-bound": bool(self.time_bound.strip()),
        }


def demonstrate_smart_objective() -> None:
    """Build and validate a SMART business objective."""

    objective = SMARTObjective(
        specific="Reduce first-response time for digital support requests.",
        measurable="Reduce the average from 18 hours to 4 hours.",
        achievable="Based on capacity and process analysis, the target is feasible.",
        relevant="Faster responses address customer dissatisfaction and churn.",
        time_bound="Achieve the target within six months of implementation.",
    )

    print("\nSMART OBJECTIVE")

    for dimension, valid in objective.validate().items():
        print(f"{dimension:12}: {'valid' if valid else 'missing'}")


# ============================================================================
# KPI AND BASELINE DESIGN
# ============================================================================

@dataclass
class KPI:
    """A measurable indicator used to determine whether the need is being addressed."""

    name: str
    definition: str
    baseline: float
    target: float
    unit: str
    measurement_frequency: str

    def progress(
        self,
        current: float,
        lower_is_better: bool = False,
    ) -> float:
        """
        Calculate percentage progress from baseline toward target.

        The formula treats baseline as 0% progress and target as 100%.
        """

        denominator = self.target - self.baseline

        if denominator == 0:
            return 0.0

        if lower_is_better:
            numerator = self.baseline - current
        else:
            numerator = current - self.baseline

        return (numerator / abs(denominator)) * 100


def demonstrate_kpi() -> None:
    """Measure progress against a business need."""

    kpi = KPI(
        name="First-response time",
        definition="Average time between ticket creation and first human response.",
        baseline=18,
        target=4,
        unit="hours",
        measurement_frequency="weekly",
    )

    current_values = [18, 14, 10, 7, 4]

    print("\nKPI PROGRESS")

    for current in current_values:
        progress = kpi.progress(
            current=current,
            lower_is_better=True,
        )
        print(
            f"Current={current} {kpi.unit}; "
            f"progress={progress:.1f}%"
        )


# ============================================================================
# BUSINESS CASE
# ============================================================================

@dataclass
class BusinessCase:
    """
    Basic financial model for a project decision.

    This is intentionally simplified. Production investment decisions may
    require taxes, working capital, depreciation, financing, discount rates,
    risk adjustments, and scenario distributions.
    """

    implementation_cost: float
    annual_operating_cost: float
    annual_benefit: float
    useful_life_years: int

    def net_annual_benefit(self) -> float:
        return self.annual_benefit - self.annual_operating_cost

    def total_net_benefit(self) -> float:
        return (
            self.net_annual_benefit() * self.useful_life_years
            - self.implementation_cost
        )

    def roi(self) -> float:
        """
        Calculate simple total ROI.

        ROI = net gain / investment cost.
        """

        if self.implementation_cost == 0:
            raise ZeroDivisionError("Implementation cost cannot be zero.")

        return self.total_net_benefit() / self.implementation_cost

    def payback_years(self) -> Optional[float]:
        """Estimate simple payback period."""

        annual_net_benefit = self.net_annual_benefit()

        if annual_net_benefit <= 0:
            return None

        return self.implementation_cost / annual_net_benefit


def demonstrate_business_case() -> None:
    """Calculate basic investment economics."""

    case = BusinessCase(
        implementation_cost=300_000,
        annual_operating_cost=60_000,
        annual_benefit=180_000,
        useful_life_years=5,
    )

    print("\nBUSINESS CASE")

    print(f"Annual net benefit: {case.net_annual_benefit():,.0f}")
    print(f"Total net benefit:  {case.total_net_benefit():,.0f}")
    print(f"Simple ROI:         {case.roi() * 100:.1f}%")

    payback = case.payback_years()

    if payback is None:
        print("Payback:             Not achieved")
    else:
        print(f"Payback:             {payback:.2f} years")


# ============================================================================
# NET PRESENT VALUE
# ============================================================================

def calculate_npv(
    initial_investment: float,
    annual_cash_flows: Sequence[float],
    discount_rate: float,
) -> float:
    """
    Calculate Net Present Value.

    NPV includes the initial investment at time zero and discounts later
    cash flows.

    Formula:

        NPV = -Initial Investment
              + CF1/(1+r)^1
              + CF2/(1+r)^2
              + ...

    A positive NPV means the modeled cash flows exceed the required return
    under the chosen assumptions.
    """

    if discount_rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")

    npv = -initial_investment

    for year, cash_flow in enumerate(annual_cash_flows, start=1):
        npv += cash_flow / ((1 + discount_rate) ** year)

    return npv


def demonstrate_npv() -> None:
    """Demonstrate discounted investment analysis."""

    initial_investment = 300_000
    annual_cash_flows = [100_000, 120_000, 140_000, 150_000]
    discount_rate = 0.10

    npv = calculate_npv(
        initial_investment=initial_investment,
        annual_cash_flows=annual_cash_flows,
        discount_rate=discount_rate,
    )

    print("\nNET PRESENT VALUE")
    print(f"NPV: {npv:,.2f}")


# ============================================================================
# SENSITIVITY ANALYSIS
# ============================================================================

def sensitivity_analysis(
    implementation_cost: float,
    annual_benefits: Sequence[float],
    annual_operating_cost: float,
    useful_life_years: int,
) -> List[Tuple[float, float]]:
    """
    Calculate simple ROI under multiple annual-benefit assumptions.
    """

    results = []

    for benefit in annual_benefits:
        case = BusinessCase(
            implementation_cost=implementation_cost,
            annual_operating_cost=annual_operating_cost,
            annual_benefit=benefit,
            useful_life_years=useful_life_years,
        )
        results.append((benefit, case.roi()))

    return results


def demonstrate_sensitivity_analysis() -> None:
    """Show how assumptions change the financial conclusion."""

    results = sensitivity_analysis(
        implementation_cost=300_000,
        annual_benefits=[100_000, 140_000, 180_000, 220_000],
        annual_operating_cost=60_000,
        useful_life_years=5,
    )

    print("\nSENSITIVITY ANALYSIS")

    for benefit, roi in results:
        print(
            f"Annual benefit={benefit:,.0f}; "
            f"ROI={roi * 100:.1f}%"
        )


# ============================================================================
# ASSUMPTIONS AND CONSTRAINTS
# ============================================================================

@dataclass
class Assumption:
    """Represents an assumption used in a business-needs analysis."""

    statement: str
    importance: int
    uncertainty: int

    def exposure(self) -> int:
        """Higher values indicate assumptions requiring more attention."""
        return self.importance * self.uncertainty


def rank_assumptions(
    assumptions: Sequence[Assumption],
) -> List[Assumption]:
    """Rank assumptions by exposure."""

    return sorted(
        assumptions,
        key=lambda assumption: assumption.exposure(),
        reverse=True,
    )


def demonstrate_assumptions() -> None:
    """Identify assumptions that could materially change the decision."""

    assumptions = [
        Assumption(
            statement="Customer churn is partly caused by slow responses.",
            importance=10,
            uncertainty=7,
        ),
        Assumption(
            statement="The current support team can adopt the new process.",
            importance=8,
            uncertainty=5,
        ),
        Assumption(
            statement="Integration with the existing CRM is technically possible.",
            importance=9,
            uncertainty=4,
        ),
    ]

    print("\nASSUMPTION EXPOSURE")

    for assumption in rank_assumptions(assumptions):
        print(
            f"Exposure={assumption.exposure():2d}: "
            f"{assumption.statement}"
        )


# ============================================================================
# ALTERNATIVES ANALYSIS
# ============================================================================

@dataclass
class Alternative:
    """Represents an option for addressing a business need."""

    name: str
    estimated_cost: float
    expected_annual_benefit: float
    implementation_time_months: int
    risk: float
    strategic_alignment: float

    def simple_roi(self) -> float:
        """Calculate one-year benefit-to-cost ratio."""

        if self.estimated_cost <= 0:
            raise ValueError("Estimated cost must be positive.")

        return (
            self.expected_annual_benefit - self.estimated_cost
        ) / self.estimated_cost

    def decision_score(self) -> float:
        """
        Combine value, speed, risk, and strategic alignment.

        This score is an analytical aid, not a universal decision formula.
        """

        roi_component = max(min(self.simple_roi(), 2), -1)

        speed_score = max(
            0.0,
            10.0 - self.implementation_time_months,
        )

        risk_score = 10.0 - self.risk

        return (
            roi_component * 3
            + speed_score * 0.2
            + risk_score * 0.3
            + self.strategic_alignment * 0.5
        )


def demonstrate_alternatives() -> None:
    """Compare different ways to respond to the same business need."""

    alternatives = [
        Alternative(
            name="Optimize current process",
            estimated_cost=80_000,
            expected_annual_benefit=110_000,
            implementation_time_months=3,
            risk=3,
            strategic_alignment=6,
        ),
        Alternative(
            name="Implement integrated platform",
            estimated_cost=300_000,
            expected_annual_benefit=220_000,
            implementation_time_months=8,
            risk=5,
            strategic_alignment=9,
        ),
        Alternative(
            name="Outsource support operations",
            estimated_cost=180_000,
            expected_annual_benefit=160_000,
            implementation_time_months=4,
            risk=6,
            strategic_alignment=5,
        ),
    ]

    ranked = sorted(
        alternatives,
        key=lambda alternative: alternative.decision_score(),
        reverse=True,
    )

    print("\nALTERNATIVES ANALYSIS")

    for alternative in ranked:
        print(
            f"{alternative.name}: "
            f"ROI={alternative.simple_roi() * 100:.1f}%, "
            f"decision score={alternative.decision_score():.2f}"
        )


# ============================================================================
# STATUS QUO AS AN ALTERNATIVE
# ============================================================================

def compare_with_do_nothing(
    project_cost: float,
    expected_project_benefit: float,
    cost_of_inaction: float,
) -> Dict[str, float]:
    """
    Compare a project with the status quo.

    The do-nothing option is not automatically zero cost because unresolved
    problems can continue generating operational or strategic losses.
    """

    project_net_value = expected_project_benefit - project_cost

    return {
        "project_net_value": project_net_value,
        "do_nothing_cost": cost_of_inaction,
        "incremental_value_of_action": (
            project_net_value + cost_of_inaction
        ),
    }


def demonstrate_do_nothing_option() -> None:
    """Show why the status quo should be explicitly evaluated."""

    result = compare_with_do_nothing(
        project_cost=300_000,
        expected_project_benefit=850_000,
        cost_of_inaction=700_000,
    )

    print("\nDO-NOTHING ANALYSIS")

    for key, value in result.items():
        print(f"{key}: {value:,.0f}")


# ============================================================================
# DECISION GATES
# ============================================================================

class DecisionStatus(Enum):
    """Possible decision outcomes after business-need assessment."""

    PROCEED = "Proceed"
    REFINE = "Refine"
    HOLD = "Hold"
    REJECT = "Reject"


@dataclass
class DecisionGate:
    """Represents minimum evidence required before proceeding."""

    minimum_evidence_score: float
    minimum_business_value: float
    maximum_risk: float

    def evaluate(
        self,
        evidence_score: float,
        business_value: float,
        risk: float,
    ) -> DecisionStatus:
        """
        Evaluate a proposed project at an early decision gate.
        """

        if evidence_score < self.minimum_evidence_score:
            return DecisionStatus.REFINE

        if business_value < self.minimum_business_value:
            return DecisionStatus.REJECT

        if risk > self.maximum_risk:
            return DecisionStatus.HOLD

        return DecisionStatus.PROCEED


def demonstrate_decision_gate() -> None:
    """Demonstrate governance before project authorization."""

    gate = DecisionGate(
        minimum_evidence_score=4.0,
        minimum_business_value=200_000,
        maximum_risk=7.0,
    )

    cases = [
        ("Strong evidence and value", 5.0, 400_000, 5.0),
        ("Weak evidence", 2.5, 500_000, 4.0),
        ("Insufficient value", 5.0, 100_000, 4.0),
        ("High risk", 5.0, 400_000, 9.0),
    ]

    print("\nDECISION GATES")

    for name, evidence, value, risk in cases:
        status = gate.evaluate(
            evidence_score=evidence,
            business_value=value,
            risk=risk,
        )
        print(f"{name}: {status.value}")


# ============================================================================
# TRACEABILITY
# ============================================================================

@dataclass
class TraceabilityRecord:
    """
    Links a business need to the objective, deliverable, KPI, and benefit.

    Traceability prevents project teams from losing sight of why the work
    exists.
    """

    need_id: str
    need: str
    objective: str
    deliverable: str
    kpi: str
    benefit: str

    def validate(self) -> List[str]:
        """Return missing traceability links."""

        fields = {
            "need_id": self.need_id,
            "need": self.need,
            "objective": self.objective,
            "deliverable": self.deliverable,
            "kpi": self.kpi,
            "benefit": self.benefit,
        }

        return [
            field_name
            for field_name, value in fields.items()
            if not value.strip()
        ]


def demonstrate_traceability() -> None:
    """Create a complete business-to-benefit traceability chain."""

    record = TraceabilityRecord(
        need_id="BN-001",
        need="Support response times exceed customer expectations.",
        objective="Reduce average response time from 18 to 4 hours.",
        deliverable="New routing, workflow, reporting, and integration capability.",
        kpi="Average first-response time",
        benefit="Improved customer satisfaction and lower service-related loss.",
    )

    print("\nTRACEABILITY")

    missing = record.validate()

    if missing:
        print(f"Missing fields: {', '.join(missing)}")
    else:
        print("Traceability chain is complete.")


# ============================================================================
# BENEFITS REALIZATION
# ============================================================================

@dataclass
class Benefit:
    """Represents a measurable benefit expected from addressing a business need."""

    name: str
    owner: str
    baseline: float
    target: float
    current: float
    unit: str
    lower_is_better: bool = False

    def achieved_percentage(self) -> float:
        """Calculate benefit realization against the baseline-to-target gap."""

        required_change = self.target - self.baseline

        if required_change == 0:
            return 100.0

        actual_change = self.current - self.baseline

        if self.lower_is_better:
            actual_change = self.baseline - self.current
            required_change = self.baseline - self.target

        return max(
            0.0,
            min(
                100.0,
                actual_change / required_change * 100,
            ),
        )


def demonstrate_benefits_realization() -> None:
    """Measure whether the business benefit is actually being achieved."""

    benefit = Benefit(
        name="Reduced response time",
        owner="Customer Operations",
        baseline=18,
        target=4,
        current=7,
        unit="hours",
        lower_is_better=True,
    )

    print("\nBENEFITS REALIZATION")
    print(
        f"{benefit.name}: "
        f"{benefit.achieved_percentage():.1f}% of target improvement achieved"
    )


# ============================================================================
# RISK OF SOLVING THE WRONG PROBLEM
# ============================================================================

@dataclass
class ProblemHypothesis:
    """Represents a testable belief about why a business problem exists."""

    statement: str
    evidence_for: float
    evidence_against: float
    impact_if_wrong: float

    def confidence(self) -> float:
        """
        Estimate confidence from supporting versus opposing evidence.

        The formula is illustrative and should not be interpreted as a
        statistical probability.
        """

        total = self.evidence_for + self.evidence_against

        if total == 0:
            return 0.0

        return self.evidence_for / total

    def wrong_problem_exposure(self) -> float:
        """Estimate decision exposure if the hypothesis is wrong."""

        return (1 - self.confidence()) * self.impact_if_wrong


def demonstrate_wrong_problem_risk() -> None:
    """Show why causal assumptions should be tested before solution selection."""

    hypotheses = [
        ProblemHypothesis(
            statement="Slow response is primarily caused by poor routing.",
            evidence_for=8,
            evidence_against=2,
            impact_if_wrong=10,
        ),
        ProblemHypothesis(
            statement="Slow response is primarily caused by insufficient staff.",
            evidence_for=4,
            evidence_against=6,
            impact_if_wrong=9,
        ),
        ProblemHypothesis(
            statement="Customers are dissatisfied primarily because responses "
            "lack useful information.",
            evidence_for=7,
            evidence_against=3,
            impact_if_wrong=8,
        ),
    ]

    print("\nWRONG-PROBLEM RISK")

    for hypothesis in hypotheses:
        print(
            f"{hypothesis.statement}\n"
            f"  confidence indicator={hypothesis.confidence():.2f}\n"
            f"  wrong-problem exposure={hypothesis.wrong_problem_exposure():.2f}"
        )


# ============================================================================
# EDGE CASES
# ============================================================================

def handle_edge_cases() -> None:
    """
    Demonstrate situations in which ordinary project-justification logic
    needs additional care.
    """

    print("\nEDGE CASES")

    cases = {
        "No measurable baseline": (
            "A new market opportunity may have no historical performance "
            "baseline. Use estimates, comparable benchmarks, experiments, "
            "or leading indicators."
        ),
        "Mandatory compliance": (
            "A compliance project may be required even when its direct ROI "
            "is negative."
        ),
        "Conflicting stakeholders": (
            "Different stakeholder groups may experience different versions "
            "of the business need."
        ),
        "Changing environment": (
            "A valid business need can become obsolete if regulation, "
            "technology, competition, or strategy changes."
        ),
        "Intangible benefits": (
            "Brand trust, resilience, employee experience, and risk reduction "
            "may be difficult to express in direct monetary terms."
        ),
        "High urgency but weak evidence": (
            "Urgency does not automatically prove the proposed root cause."
        ),
        "Positive ROI but poor strategic fit": (
            "A financially attractive project can still consume scarce "
            "capacity needed for a more important strategic objective."
        ),
    }

    for name, explanation in cases.items():
        print(f"\n{name}")
        print(explanation)


# ============================================================================
# COMMON MISTAKES
# ============================================================================

def demonstrate_common_mistakes() -> None:
    """
    Display common business-need mistakes and their corrective principle.
    """

    mistakes = [
        (
            "Starting with the solution",
            "Define the business condition before selecting technology."
        ),
        (
            "Confusing a symptom with a root cause",
            "Investigate causal relationships using evidence."
        ),
        (
            "Using vague language",
            "Quantify the gap, frequency, impact, and affected population."
        ),
        (
            "Assuming stakeholder agreement",
            "Validate the need with the groups affected by the problem."
        ),
        (
            "Ignoring the status quo",
            "Explicitly model the cost and consequences of doing nothing."
        ),
        (
            "Treating every need as a project",
            "Determine whether the issue requires temporary project work "
            "or ongoing operational management."
        ),
        (
            "Measuring deliverables instead of outcomes",
            "Track whether the business condition actually improves."
        ),
        (
            "Using unreliable financial estimates",
            "Document assumptions, sources, confidence, and uncertainty."
        ),
        (
            "Ignoring strategic alignment",
            "Compare the need with organizational priorities and capacity."
        ),
        (
            "Failing to revisit the need",
            "Revalidate the business case when major assumptions change."
        ),
    ]

    print("\nCOMMON MISTAKES")

    for mistake, correction in mistakes:
        print(f"\nMistake: {mistake}")
        print(f"Corrective principle: {correction}")


# ============================================================================
# COMPLETE WORKED CASE STUDY
# ============================================================================

@dataclass
class ProjectNeedAssessment:
    """Complete structured assessment for a potential project."""

    need: BusinessNeed
    problem_statement: ProblemStatement
    impacts: List[ImpactEstimate]
    stakeholders: List[Stakeholder]
    alternatives: List[Alternative]
    assumptions: List[Assumption]

    def annual_impact(self) -> float:
        """Return confidence-adjusted annual impact."""

        return calculate_total_impact(self.impacts)

    def stakeholder_priority(self) -> List[Stakeholder]:
        """Return stakeholders by engagement priority."""

        return rank_stakeholders(self.stakeholders)

    def alternative_priority(self) -> List[Alternative]:
        """Return response alternatives by decision score."""

        return sorted(
            self.alternatives,
            key=lambda item: item.decision_score(),
            reverse=True,
        )

    def assumption_priority(self) -> List[Assumption]:
        """Return assumptions by exposure."""

        return rank_assumptions(self.assumptions)


def build_case_study() -> ProjectNeedAssessment:
    """
    Build a complete example.

    Scenario:
        A company receives customer requests through email and several
        disconnected channels. Response time has increased, follow-up
        requests are common, and customer satisfaction has declined.
    """

    need = BusinessNeed(
        title="Improve customer-support responsiveness",
        description=(
            "Customer requests are not consistently routed, prioritized, "
            "and tracked, resulting in excessive response times."
        ),
        need_type=NeedType.CUSTOMER,
        affected_area="Customer Operations",
        baseline_value=18,
        target_value=4,
        unit="hours",
        annual_impact=0,
        strategic_alignment=9,
        urgency=8,
        confidence=8,
        feasibility=7,
        evidence=[
            "Support response-time dashboard",
            "Customer satisfaction survey",
            "Ticket backlog analysis",
            "Escalation records",
        ],
    )

    problem_statement = ProblemStatement(
        affected_group="Customers using digital support",
        current_condition="experience long and inconsistent response times",
        context="across multiple customer-support channels",
        measurable_impact="average first-response time is 18 hours versus a 4-hour target",
        business_consequence="lower satisfaction, rework, and avoidable customer loss",
    )

    impacts = [
        ImpactEstimate(
            category="Productivity loss",
            annual_cost=180_000,
            confidence=0.85,
            explanation="Manual assignment and duplicate handling.",
        ),
        ImpactEstimate(
            category="Customer-related revenue loss",
            annual_cost=250_000,
            confidence=0.65,
            explanation="Estimated revenue impact from poor service experience.",
        ),
        ImpactEstimate(
            category="Rework",
            annual_cost=90_000,
            confidence=0.90,
            explanation="Repeated customer contacts.",
        ),
    ]

    stakeholders = [
        Stakeholder(
            name="Customers",
            interest=10,
            influence=6,
            impact=10,
            perspective="Need faster and more reliable support.",
        ),
        Stakeholder(
            name="Customer Operations",
            interest=10,
            influence=9,
            impact=10,
            perspective="Need better workload management and routing.",
        ),
        Stakeholder(
            name="Finance",
            interest=6,
            influence=9,
            impact=7,
            perspective="Needs evidence that the investment creates value.",
        ),
        Stakeholder(
            name="Technology",
            interest=8,
            influence=8,
            impact=8,
            perspective="Must validate integration and implementation feasibility.",
        ),
    ]

    alternatives = [
        Alternative(
            name="Process redesign",
            estimated_cost=80_000,
            expected_annual_benefit=130_000,
            implementation_time_months=3,
            risk=3,
            strategic_alignment=6,
        ),
        Alternative(
            name="Integrated support platform",
            estimated_cost=300_000,
            expected_annual_benefit=220_000,
            implementation_time_months=8,
            risk=5,
            strategic_alignment=9,
        ),
        Alternative(
            name="Partial outsourcing",
            estimated_cost=180_000,
            expected_annual_benefit=160_000,
            implementation_time_months=4,
            risk=6,
            strategic_alignment=5,
        ),
    ]

    assumptions = [
        Assumption(
            statement="Response time is a meaningful driver of customer satisfaction.",
            importance=10,
            uncertainty=6,
        ),
        Assumption(
            statement="Routing improvements can reduce queue delays.",
            importance=9,
            uncertainty=5,
        ),
        Assumption(
            statement="Customers will respond positively to faster service.",
            importance=9,
            uncertainty=5,
        ),
        Assumption(
            statement="The existing CRM can integrate with the selected approach.",
            importance=8,
            uncertainty=4,
        ),
    ]

    return ProjectNeedAssessment(
        need=need,
        problem_statement=problem_statement,
        impacts=impacts,
        stakeholders=stakeholders,
        alternatives=alternatives,
        assumptions=assumptions,
    )


def print_case_study(assessment: ProjectNeedAssessment) -> None:
    """Print a complete business-need assessment."""

    print("\n" + "=" * 72)
    print("COMPLETE BUSINESS NEED ASSESSMENT")
    print("=" * 72)

    print(f"\nNeed: {assessment.need.title}")
    print(f"Type: {assessment.need.need_type.value}")
    print(f"Area: {assessment.need.affected_area}")
    print(f"Description: {assessment.need.description}")

    print("\nProblem statement:")
    print(assessment.problem_statement.render())

    print("\nPerformance gap:")
    print(
        f"Baseline={assessment.need.baseline_value} "
        f"{assessment.need.unit}; "
        f"Target={assessment.need.target_value} "
        f"{assessment.need.unit}"
    )

    gap = assessment.need.gap()

    if gap is not None:
        print(f"Raw gap={gap:.2f} {assessment.need.unit}")

    print("\nEvidence:")
    for evidence in assessment.need.evidence:
        print(f"- {evidence}")

    print("\nAnnual impact:")
    print(f"{assessment.annual_impact():,.0f}")

    print("\nStakeholder priorities:")

    for stakeholder in assessment.stakeholder_priority():
        print(
            f"- {stakeholder.name}: "
            f"{stakeholder.priority_score():.2f}"
        )

    print("\nAlternatives:")

    for alternative in assessment.alternative_priority():
        print(
            f"- {alternative.name}: "
            f"ROI={alternative.simple_roi() * 100:.1f}%, "
            f"score={alternative.decision_score():.2f}"
        )

    print("\nAssumptions requiring attention:")

    for assumption in assessment.assumption_priority():
        print(
            f"- Exposure={assumption.exposure()}: "
            f"{assumption.statement}"
        )


# ============================================================================
# PROJECT JUSTIFICATION LOGIC
# ============================================================================

def create_project_justification(
    assessment: ProjectNeedAssessment,
) -> str:
    """
    Generate a concise evidence-based project justification.

    The function deliberately separates the reason for action from the
    eventual implementation approach.
    """

    annual_impact = assessment.annual_impact()

    return (
        f"The organization has a {assessment.need.need_type.value.lower()} "
        f"business need in {assessment.need.affected_area}. "
        f"{assessment.problem_statement.render()} "
        f"The confidence-adjusted estimated annual impact is "
        f"{annual_impact:,.0f}. "
        f"The need is supported by {assessment.need.evidence_count()} "
        f"evidence sources and aligns strongly with strategic priorities. "
        f"Multiple response alternatives should be evaluated before selecting "
        f"a specific project solution."
    )


def demonstrate_project_justification() -> None:
    """Generate a structured project justification."""

    assessment = build_case_study()

    print("\nPROJECT JUSTIFICATION")
    print(create_project_justification(assessment))


# ============================================================================
# VALIDATION CHECKLIST
# ============================================================================

def validate_business_need(
    assessment: ProjectNeedAssessment,
) -> Dict[str, bool]:
    """
    Validate whether the business need contains essential decision information.
    """

    need = assessment.need

    return {
        "Clear need description": bool(need.description.strip()),
        "Need classified": isinstance(need.need_type, NeedType),
        "Affected area identified": bool(need.affected_area.strip()),
        "Baseline available": need.baseline_value is not None,
        "Target available": need.target_value is not None,
        "Evidence exists": len(need.evidence) > 0,
        "Problem statement complete": (
            bool(assessment.problem_statement.affected_group.strip())
            and bool(assessment.problem_statement.current_condition.strip())
            and bool(assessment.problem_statement.context.strip())
            and bool(assessment.problem_statement.measurable_impact.strip())
            and bool(assessment.problem_statement.business_consequence.strip())
        ),
        "Stakeholders identified": len(assessment.stakeholders) > 0,
        "Alternatives considered": len(assessment.alternatives) > 0,
        "Assumptions documented": len(assessment.assumptions) > 0,
    }


def demonstrate_validation_checklist() -> None:
    """Run a business-need validation checklist."""

    assessment = build_case_study()
    validation = validate_business_need(assessment)

    print("\nBUSINESS NEED VALIDATION")

    for criterion, passed in validation.items():
        print(
            f"{'PASS' if passed else 'FAIL':4} | {criterion}"
        )


# ============================================================================
# ADVANCED: CONFIDENCE-ADJUSTED VALUE
# ============================================================================

def confidence_adjusted_value(
    expected_benefit: float,
    probability_of_success: float,
) -> float:
    """
    Calculate an expected-value estimate.

    This is useful when a benefit estimate is uncertain.

    Expected value = benefit × probability.

    The result should not be treated as a replacement for a complete risk
    model.
    """

    if expected_benefit < 0:
        raise ValueError("Expected benefit cannot be negative.")

    if not 0 <= probability_of_success <= 1:
        raise ValueError(
            "Probability of success must be between 0 and 1."
        )

    return expected_benefit * probability_of_success


def demonstrate_expected_value() -> None:
    """Compare benefit estimates under uncertainty."""

    scenarios = [
        ("Conservative", 400_000, 0.55),
        ("Base case", 600_000, 0.70),
        ("Optimistic", 850_000, 0.80),
    ]

    print("\nCONFIDENCE-ADJUSTED VALUE")

    for name, benefit, probability in scenarios:
        value = confidence_adjusted_value(
            expected_benefit=benefit,
            probability_of_success=probability,
        )

        print(
            f"{name}: benefit={benefit:,.0f}; "
            f"probability={probability:.0%}; "
            f"expected value={value:,.0f}"
        )


# ============================================================================
# ADVANCED: BREAK-EVEN ANALYSIS
# ============================================================================

def break_even_benefit(
    implementation_cost: float,
    annual_operating_cost: float,
    useful_life_years: int,
) -> float:
    """
    Calculate the minimum constant annual benefit required to break even.

    This simplified model ignores discounting and taxes.
    """

    if useful_life_years <= 0:
        raise ValueError("Useful life must be positive.")

    return (
        implementation_cost / useful_life_years
        + annual_operating_cost
    )


def demonstrate_break_even() -> None:
    """Calculate the minimum annual benefit required for break-even."""

    required_benefit = break_even_benefit(
        implementation_cost=300_000,
        annual_operating_cost=60_000,
        useful_life_years=5,
    )

    print("\nBREAK-EVEN BENEFIT")
    print(
        f"Minimum annual benefit for simple break-even: "
        f"{required_benefit:,.0f}"
    )


# ============================================================================
# ADVANCED: REQUIREMENTS TRACEABILITY
# ============================================================================

@dataclass
class Requirement:
    """Represents a requirement derived from a business objective."""

    requirement_id: str
    statement: str
    source_need_id: str
    acceptance_measure: str

    def is_traceable(self) -> bool:
        """Check whether the requirement has sufficient traceability."""

        return all(
            [
                self.requirement_id.strip(),
                self.statement.strip(),
                self.source_need_id.strip(),
                self.acceptance_measure.strip(),
            ]
        )


def demonstrate_requirements_traceability() -> None:
    """Link requirements back to the original business need."""

    requirements = [
        Requirement(
            requirement_id="REQ-001",
            statement="Support requests must be automatically categorized.",
            source_need_id="BN-001",
            acceptance_measure="At least 95% of sampled requests are correctly categorized.",
        ),
        Requirement(
            requirement_id="REQ-002",
            statement="High-priority requests must be routed within one minute.",
            source_need_id="BN-001",
            acceptance_measure="95th-percentile routing time is below one minute.",
        ),
        Requirement(
            requirement_id="REQ-003",
            statement="Managers must have visibility into response-time performance.",
            source_need_id="BN-001",
            acceptance_measure="Dashboard displays current and historical response-time KPIs.",
        ),
    ]

    print("\nREQUIREMENTS TRACEABILITY")

    for requirement in requirements:
        print(
            f"{requirement.requirement_id}: "
            f"{'traceable' if requirement.is_traceable() else 'incomplete'}"
        )


# ============================================================================
# ADVANCED: DECISION TREE
# ============================================================================

@dataclass
class DecisionNode:
    """A simple binary decision-tree node."""

    question: str
    yes_result: str
    no_result: str

    def decide(self, answer: bool) -> str:
        """Return the result associated with the answer."""

        return self.yes_result if answer else self.no_result


def demonstrate_decision_tree() -> None:
    """
    Use a simple decision tree to determine whether a business issue needs
    project-level intervention.
    """

    node = DecisionNode(
        question=(
            "Is there a material and evidence-supported business gap?"
        ),
        yes_result="Continue to root-cause and alternatives analysis.",
        no_result="Do not authorize a project until the need is validated.",
    )

    print("\nDECISION TREE")
    print(node.question)
    print(f"If YES: {node.decide(True)}")
    print(f"If NO:  {node.decide(False)}")


# ============================================================================
# ADVANCED: BUSINESS NEED MATURITY
# ============================================================================

def business_need_maturity(
    has_problem_statement: bool,
    has_baseline: bool,
    has_root_cause_evidence: bool,
    has_financial_impact: bool,
    has_stakeholder_validation: bool,
    has_alternatives: bool,
    has_benefit_owner: bool,
) -> str:
    """
    Estimate business-need maturity.

    Maturity levels:
    - Initial
    - Defined
    - Evidence-based
    - Decision-ready

    The thresholds are illustrative.
    """

    score = sum(
        [
            has_problem_statement,
            has_baseline,
            has_root_cause_evidence,
            has_financial_impact,
            has_stakeholder_validation,
            has_alternatives,
            has_benefit_owner,
        ]
    )

    if score <= 2:
        return "Initial"

    if score <= 4:
        return "Defined"

    if score <= 6:
        return "Evidence-based"

    return "Decision-ready"


def demonstrate_maturity_model() -> None:
    """Assess how mature the business-need definition is."""

    levels = [
        (
            "Idea only",
            True,
            False,
            False,
            False,
            False,
            False,
            False,
        ),
        (
            "Defined problem",
            True,
            True,
            True,
            False,
            True,
            False,
            False,
        ),
        (
            "Evidence-based",
            True,
            True,
            True,
            True,
            True,
            True,
            False,
        ),
        (
            "Decision-ready",
            True,
            True,
            True,
            True,
            True,
            True,
            True,
        ),
    ]

    print("\nBUSINESS NEED MATURITY")

    for item in levels:
        name = item[0]
        maturity = business_need_maturity(*item[1:])
        print(f"{name}: {maturity}")


# ============================================================================
# PERFORMANCE AND IMPLEMENTATION CONSIDERATIONS
# ============================================================================

def demonstrate_performance_considerations() -> None:
    """
    Explain computational considerations relevant to analytical scripts.

    The business-need process itself is usually more constrained by evidence
    quality and decision quality than by CPU performance. Still, analytical
    automation can involve large datasets, repeated scoring, and simulations.
    """

    print("\nPERFORMANCE CONSIDERATIONS")

    considerations = [
        (
            "Small decision tables",
            "Simple lists and sorting are usually sufficient."
        ),
        (
            "Large operational datasets",
            "Use efficient aggregation and avoid repeatedly scanning the same "
            "dataset when a single grouped calculation is sufficient."
        ),
        (
            "Many alternatives",
            "Weighted scoring remains inexpensive, but evidence collection "
            "usually becomes the dominant bottleneck."
        ),
        (
            "Scenario simulations",
            "Vectorization, caching, or efficient numerical methods may "
            "matter when thousands or millions of scenarios are evaluated."
        ),
        (
            "Human judgment",
            "Computational precision does not compensate for poor assumptions "
            "or unreliable business data."
        ),
    ]

    for context, principle in considerations:
        print(f"\n{context}:")
        print(principle)


# ============================================================================
# SECURITY AND GOVERNANCE CONSIDERATIONS
# ============================================================================

def demonstrate_security_considerations() -> None:
    """
    Explain security concerns when business-need analysis uses organizational
    data.

    Business-need analysis can involve sensitive customer, employee, revenue,
    operational, financial, or strategic information.
    """

    print("\nSECURITY AND GOVERNANCE CONSIDERATIONS")

    considerations = [
        (
            "Data minimization",
            "Use only the data required to establish the business need."
        ),
        (
            "Access control",
            "Restrict sensitive financial, customer, employee, and strategic "
            "information to authorized users."
        ),
        (
            "Data quality",
            "Protect the integrity of the measurements used to justify "
            "investment decisions."
        ),
        (
            "Auditability",
            "Retain the source and assumptions behind material estimates."
        ),
        (
            "Privacy",
            "Avoid exposing personally identifiable information when "
            "aggregated metrics are sufficient."
        ),
        (
            "Version control",
            "Record important changes to assumptions, targets, and business "
            "case calculations."
        ),
        (
            "Conflict of interest",
            "Separate evidence gathering from incentives to approve a "
            "preferred solution."
        ),
    ]

    for area, practice in considerations:
        print(f"\n{area}:")
        print(practice)


# ============================================================================
# TESTS
# ============================================================================

def run_assertion_tests() -> None:
    """
    Execute lightweight tests without external testing packages.

    These tests verify the core calculations used in the educational examples.
    """

    print("\nASSERTION TESTS")

    metric = PerformanceMetric(
        name="Accuracy",
        baseline=80,
        target=90,
        unit="percent",
        direction="higher_is_better",
    )

    assert metric.gap() == 10
    assert abs(metric.improvement_required() - 0.125) < 1e-9

    lower_metric = PerformanceMetric(
        name="Cost",
        baseline=100,
        target=70,
        unit="currency",
        direction="lower_is_better",
    )

    assert lower_metric.gap() == -30
    assert abs(lower_metric.improvement_required() - 0.30) < 1e-9

    assert calculate_cost_of_inaction(
        annual_impact=100,
        years=3,
        annual_growth_rate=0,
    ) == 300

    assert abs(
        calculate_npv(
            initial_investment=100,
            annual_cash_flows=[60, 60],
            discount_rate=0,
        ) - 20
    ) < 1e-9

    case = BusinessCase(
        implementation_cost=100,
        annual_operating_cost=20,
        annual_benefit=70,
        useful_life_years=3,
    )

    assert case.net_annual_benefit() == 50
    assert case.total_net_benefit() == 50

    assert confidence_adjusted_value(
        expected_benefit=1000,
        probability_of_success=0.5,
    ) == 500

    assert break_even_benefit(
        implementation_cost=100,
        annual_operating_cost=20,
        useful_life_years=4,
    ) == 45

    print("All assertion tests passed.")


# ============================================================================
# STUDY EXERCISES IMPLEMENTED AS CHECKS
# ============================================================================

def run_practical_checks() -> None:
    """
    Apply the concepts to a small fictional case.

    The purpose is to demonstrate how an analyst can move from a vague
    observation toward a defensible business need.
    """

    print("\nPRACTICAL CHECKS")

    observation = (
        "Employees complain that monthly reporting takes too long."
    )

    refined_problem = (
        "Monthly management reporting requires 8 business days because "
        "data is manually consolidated from multiple spreadsheets."
    )

    desired_outcome = (
        "Reduce reporting cycle time from 8 business days to 2."
    )

    print(f"Observation:      {observation}")
    print(f"Refined problem:  {refined_problem}")
    print(f"Desired outcome:  {desired_outcome}")

    evidence = [
        "Historical reporting timestamps",
        "Spreadsheet processing logs",
        "Interviews with report owners",
        "Error and rework records",
    ]

    print("\nEvidence to validate the need:")

    for item in evidence:
        print(f"- {item}")


# ============================================================================
# MAIN STUDY PROGRAM
# ============================================================================

def main() -> None:
    """
    Run the complete educational program.

    The sequence follows a practical progression:

        1. Understand the terminology.
        2. Separate need from solution.
        3. Define the current state.
        4. Quantify the gap.
        5. Investigate root causes.
        6. Gather evidence.
        7. Analyze stakeholders.
        8. Quantify business impact.
        9. Evaluate cost of inaction.
        10. Prioritize needs.
        11. Determine whether project work is appropriate.
        12. Define outcomes and objectives.
        13. Establish KPIs.
        14. Build a business case.
        15. Compare alternatives.
        16. Analyze assumptions and uncertainty.
        17. Establish traceability.
        18. Validate benefits.
        19. Apply governance and decision gates.
        20. Test the complete workflow with a case study.
    """

    print("=" * 72)
    print("BUSINESS NEED: IDENTIFYING THE REASON FOR A PROJECT")
    print("=" * 72)

    explain_core_distinctions()
    compare_need_and_solution()

    demonstrate_gap_analysis()
    demonstrate_problem_statement()

    demonstrate_five_whys()
    demonstrate_cause_analysis()

    demonstrate_evidence_assessment()
    demonstrate_stakeholder_analysis()

    demonstrate_business_impact()
    demonstrate_cost_of_inaction()

    demonstrate_prioritization()
    demonstrate_need_classification()
    demonstrate_project_vs_operations()

    demonstrate_outcome_structure()
    demonstrate_smart_objective()
    demonstrate_kpi()

    demonstrate_business_case()
    demonstrate_npv()
    demonstrate_sensitivity_analysis()

    demonstrate_assumptions()
    demonstrate_alternatives()
    demonstrate_do_nothing_option()

    demonstrate_decision_gate()
    demonstrate_traceability()
    demonstrate_benefits_realization()

    demonstrate_wrong_problem_risk()
    handle_edge_cases()
    demonstrate_common_mistakes()

    assessment = build_case_study()
    print_case_study(assessment)
    demonstrate_project_justification()
    demonstrate_validation_checklist()

    demonstrate_expected_value()
    demonstrate_break_even()
    demonstrate_requirements_traceability()
    demonstrate_decision_tree()
    demonstrate_maturity_model()

    demonstrate_performance_considerations()
    demonstrate_security_considerations()

    run_assertion_tests()
    run_practical_checks()

    print("\n" + "=" * 72)
    print("END OF STUDY PROGRAM")
    print("=" * 72)


if __name__ == "__main__":
    main()
