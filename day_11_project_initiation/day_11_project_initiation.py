"""
PROJECT INITIATION: HOW A PROJECT BEGINS
========================================

A comprehensive standalone study script covering project initiation from
absolute beginner concepts through advanced project-management practice.

The script explains and demonstrates:

1. What a project is
2. What project initiation means
3. Project vs operations
4. Why projects are initiated
5. Project initiation lifecycle
6. Business problems, opportunities, and strategic drivers
7. Project ideas and project proposals
8. Feasibility analysis
9. Business cases
10. Benefits, outcomes, outputs, and deliverables
11. Project objectives and SMART objectives
12. Assumptions, constraints, dependencies, and risks
13. Stakeholder identification and analysis
14. Sponsor, project manager, customer, team, and governance roles
15. Project selection and prioritization
16. Scoring models
17. Cost-benefit analysis
18. ROI and payback calculations
19. High-level project estimates
20. Project scope boundaries
21. Project charters
22. Project success criteria
23. Acceptance criteria
24. Governance and decision rights
25. Project initiation gates
26. RACI concepts
27. RAID concepts
28. Risk analysis
29. Risk probability and impact
30. Risk exposure
31. Risk response strategies
32. Dependency analysis
33. Communication planning
34. Stakeholder engagement
35. Requirements discovery at initiation
36. Agile, predictive, and hybrid initiation
37. MVP thinking
38. Change control
39. Project initiation documentation
40. Common initiation mistakes
41. Edge cases and difficult situations
42. Implementation considerations
43. Testing and validation
44. A complete project-initiation simulation
45. A reusable project charter implementation
46. A project scoring engine
47. Risk register implementation
48. Stakeholder register implementation
49. Financial analysis
50. Final integrated example

The script uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import math
import statistics
from datetime import date, timedelta


# =============================================================================
# 1. BASIC CONCEPTS
# =============================================================================

print("=" * 80)
print("PROJECT INITIATION: HOW A PROJECT BEGINS")
print("=" * 80)


def explain_project() -> None:
    """
    A project is a temporary effort undertaken to create a unique product,
    service, result, or change.

    Three important characteristics are:
    - Temporary: it has a beginning and an end.
    - Unique: its result is not simply routine repetitive work.
    - Goal-oriented: it exists to achieve defined outcomes or objectives.
    """
    print("\n1. WHAT IS A PROJECT?")
    print("A project is a temporary effort undertaken to create a unique result.")
    print("Examples:")
    print("- Building a banking mobile application")
    print("- Opening a new manufacturing facility")
    print("- Implementing an ERP system")
    print("- Launching a new product")
    print("- Migrating a company to a new cloud platform")


def explain_project_vs_operations() -> None:
    """Demonstrate the distinction between projects and operational work."""
    print("\n2. PROJECTS VS OPERATIONS")

    comparison = {
        "Duration": ("Temporary", "Continuous"),
        "Purpose": ("Create/change something", "Repeat and sustain activities"),
        "Output": ("Unique result", "Consistent recurring output"),
        "Example": ("Implement a CRM", "Operate the CRM every day"),
        "Completion": ("Has a defined end", "Usually ongoing"),
    }

    for category, values in comparison.items():
        print(f"{category:12}: Project = {values[0]:35} Operations = {values[1]}")

    print(
        "\nImportant distinction: operations may continue after a project "
        "creates or changes the operational environment."
    )


def explain_project_initiation() -> None:
    """
    Project initiation is the phase in which an idea, problem, opportunity,
    requirement, or strategic need is examined and formally authorized as
    a project.

    Initiation answers questions such as:
    - Why should the project exist?
    - What problem or opportunity does it address?
    - What outcome is expected?
    - Who owns the business decision?
    - Who are the important stakeholders?
    - Is the project feasible?
    - What is approximately required?
    - What authority does the project manager have?
    """
    print("\n3. WHAT IS PROJECT INITIATION?")
    print("Project initiation transforms an idea or need into an authorized project.")
    print("\nTypical initiation questions:")
    questions = [
        "Why are we doing this?",
        "What problem or opportunity are we addressing?",
        "What business value is expected?",
        "What should the project produce?",
        "Who is affected?",
        "Who sponsors the project?",
        "Is the project feasible?",
        "What are the major risks and constraints?",
        "What is approximately required?",
        "Who has authority to approve the project?",
    ]

    for number, question in enumerate(questions, start=1):
        print(f"{number:2}. {question}")


explain_project()
explain_project_vs_operations()
explain_project_initiation()


# =============================================================================
# 2. WHY PROJECTS BEGIN
# =============================================================================

class ProjectDriver(Enum):
    """Common reasons that cause an organization to initiate a project."""

    PROBLEM = "Business problem"
    OPPORTUNITY = "Business opportunity"
    REGULATION = "Regulatory requirement"
    STRATEGY = "Strategic objective"
    CUSTOMER = "Customer requirement"
    TECHNOLOGY = "Technology change"
    EFFICIENCY = "Efficiency improvement"
    RISK = "Risk reduction"
    COMPLIANCE = "Compliance requirement"
    INNOVATION = "Innovation"


def explain_project_drivers() -> None:
    print("\n4. COMMON PROJECT INITIATION DRIVERS")

    for driver in ProjectDriver:
        print(f"- {driver.name.title():15}: {driver.value}")

    print("\nExample:")
    print(
        "If an organization has a manual loan-processing process that takes "
        "five days, the project could be initiated to reduce processing time."
    )


explain_project_drivers()


# =============================================================================
# 3. PROBLEM, OPPORTUNITY, AND ROOT CAUSE
# =============================================================================

def problem_statement(
    current_state: str,
    impact: str,
    target_state: str,
) -> str:
    """
    Build a concise problem statement.

    A strong problem statement separates:
    current condition -> consequence -> desired direction.

    It should not prematurely prescribe a technical solution.
    """
    return (
        f"Current state: {current_state}\n"
        f"Business impact: {impact}\n"
        f"Desired direction: {target_state}"
    )


print("\n5. PROBLEM STATEMENT EXAMPLE")
print(
    problem_statement(
        "Customer support requests are processed manually.",
        "Average resolution time is four business days and customers frequently escalate.",
        "Reduce resolution time while maintaining service quality.",
    )
)


def five_whys(problem: str, causes: List[str]) -> None:
    """
    Illustrative five-whys analysis.

    In practice, the five-whys technique is not required to have exactly five
    questions. The purpose is to progressively investigate causes rather than
    stopping at a visible symptom.
    """
    print("\n6. ROOT-CAUSE ANALYSIS")
    print(f"Initial problem: {problem}")

    for index, cause in enumerate(causes, start=1):
        print(f"Why {index}: {cause}")


five_whys(
    "Customer requests remain unresolved for several days.",
    [
        "Requests are manually assigned.",
        "There is no centralized queue.",
        "Teams use different tracking methods.",
        "The current workflow was designed for a much smaller customer base.",
        "Growth increased volume without a corresponding process redesign.",
    ],
)


# =============================================================================
# 4. PROJECT IDEA VS PROJECT PROPOSAL
# =============================================================================

@dataclass
class ProjectIdea:
    """An early project concept before formal authorization."""

    name: str
    problem: str
    expected_benefit: str
    proposed_solution: str
    strategic_alignment: str


@dataclass
class ProjectProposal:
    """A more structured case for deciding whether to investigate or approve."""

    name: str
    problem: str
    objective: str
    expected_benefits: List[str]
    high_level_scope: List[str]
    estimated_cost: float
    estimated_duration_months: float
    strategic_alignment_score: float
    feasibility_score: float


idea = ProjectIdea(
    name="Digital Customer Service Platform",
    problem="Customer requests are handled through disconnected manual channels.",
    expected_benefit="Faster resolution and better visibility.",
    proposed_solution="Create a centralized customer service platform.",
    strategic_alignment="Supports the organization's digital-service strategy.",
)

proposal = ProjectProposal(
    name=idea.name,
    problem=idea.problem,
    objective="Reduce average customer-resolution time by 40% within six months of launch.",
    expected_benefits=[
        "Lower resolution time",
        "Improved customer visibility",
        "Reduced manual work",
        "Better management reporting",
    ],
    high_level_scope=[
        "Requirements analysis",
        "Platform configuration",
        "Data migration",
        "Integration",
        "Training",
        "Deployment",
    ],
    estimated_cost=750000,
    estimated_duration_months=6,
    strategic_alignment_score=9,
    feasibility_score=8,
)

print("\n7. PROJECT IDEA")
print(idea)

print("\n8. PROJECT PROPOSAL")
print(proposal)


# =============================================================================
# 5. OUTPUTS, DELIVERABLES, OUTCOMES, AND BENEFITS
# =============================================================================

@dataclass
class ValueChain:
    """Represent the relationship between project output and business value."""

    output: str
    outcome: str
    benefit: str


value_chain = ValueChain(
    output="Centralized customer service platform",
    outcome="Agents can access and process requests through one workflow",
    benefit="Reduced resolution time and improved customer experience",
)

print("\n9. OUTPUT -> OUTCOME -> BENEFIT")
print(f"Output : {value_chain.output}")
print(f"Outcome: {value_chain.outcome}")
print(f"Benefit: {value_chain.benefit}")

print(
    "\nA deliverable is something produced by project work. "
    "An outcome is a change resulting from using the deliverable. "
    "A benefit is the measurable business advantage associated with that change."
)


# =============================================================================
# 6. PROJECT OBJECTIVES
# =============================================================================

@dataclass
class SMARTObjective:
    """Represent a measurable objective using SMART characteristics."""

    specific: str
    measurable: str
    achievable: str
    relevant: str
    time_bound: str

    def validate(self) -> Dict[str, bool]:
        return {
            "Specific": bool(self.specific.strip()),
            "Measurable": bool(self.measurable.strip()),
            "Achievable": bool(self.achievable.strip()),
            "Relevant": bool(self.relevant.strip()),
            "Time-bound": bool(self.time_bound.strip()),
        }

    def is_complete(self) -> bool:
        return all(self.validate().values())


objective = SMARTObjective(
    specific="Reduce average customer-resolution time.",
    measurable="Reduce the average from four days to 2.4 days.",
    achievable="Supported by process redesign and workflow automation.",
    relevant="Directly addresses the identified customer-service problem.",
    time_bound="Achieve the target within six months after launch.",
)

print("\n10. SMART OBJECTIVE")
for characteristic, valid in objective.validate().items():
    print(f"{characteristic:12}: {'Valid' if valid else 'Missing'}")

print(f"Complete SMART objective: {objective.is_complete()}")


# =============================================================================
# 7. SCOPE AND BOUNDARIES
# =============================================================================

@dataclass
class ScopeBoundary:
    """Define what belongs inside and outside the initial project scope."""

    in_scope: List[str]
    out_of_scope: List[str]

    def check_item(self, item: str) -> str:
        if item in self.in_scope:
            return "IN SCOPE"
        if item in self.out_of_scope:
            return "OUT OF SCOPE"
        return "UNDEFINED"


scope = ScopeBoundary(
    in_scope=[
        "Customer service workflow",
        "Platform configuration",
        "Data migration",
        "Training",
        "Reporting dashboard",
    ],
    out_of_scope=[
        "Replacement of the corporate ERP",
        "International expansion",
        "Unrelated marketing automation",
    ],
)

print("\n11. PROJECT SCOPE BOUNDARY")
for item in [
    "Customer service workflow",
    "Replacement of the corporate ERP",
    "Mobile application redesign",
]:
    print(f"{item:45} -> {scope.check_item(item)}")


# =============================================================================
# 8. STAKEHOLDERS
# =============================================================================

class StakeholderInfluence(Enum):
    """Stakeholder influence levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class StakeholderInterest(Enum):
    """Stakeholder interest levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Stakeholder:
    """Represent a person, group, or organization affected by a project."""

    name: str
    role: str
    influence: StakeholderInfluence
    interest: StakeholderInterest
    expectations: str
    engagement_strategy: str = ""

    def classify(self) -> str:
        if self.influence == StakeholderInfluence.HIGH:
            if self.interest == StakeholderInterest.HIGH:
                return "Manage closely"
            return "Keep satisfied"

        if self.interest == StakeholderInterest.HIGH:
            return "Keep informed"

        return "Monitor"


stakeholders = [
    Stakeholder(
        name="Executive Sponsor",
        role="Business sponsor",
        influence=StakeholderInfluence.HIGH,
        interest=StakeholderInterest.HIGH,
        expectations="Business value and strategic alignment",
    ),
    Stakeholder(
        name="Customer Service Head",
        role="Business owner",
        influence=StakeholderInfluence.HIGH,
        interest=StakeholderInterest.HIGH,
        expectations="Better operational performance",
    ),
    Stakeholder(
        name="IT Security",
        role="Control function",
        influence=StakeholderInfluence.HIGH,
        interest=StakeholderInterest.MEDIUM,
        expectations="Security and compliance",
    ),
    Stakeholder(
        name="Service Agent",
        role="End user",
        influence=StakeholderInfluence.LOW,
        interest=StakeholderInterest.HIGH,
        expectations="Easy and efficient workflow",
    ),
]

print("\n12. STAKEHOLDER ANALYSIS")
for stakeholder in stakeholders:
    stakeholder.engagement_strategy = stakeholder.classify()
    print(
        f"{stakeholder.name:22} | "
        f"Influence={stakeholder.influence.name:6} | "
        f"Interest={stakeholder.interest.name:6} | "
        f"{stakeholder.engagement_strategy}"
    )


# =============================================================================
# 9. PROJECT ROLES
# =============================================================================

@dataclass
class ProjectRole:
    """Describe a project role and its primary accountability."""

    role: str
    accountability: str


project_roles = [
    ProjectRole("Sponsor", "Authorizes the project and provides executive support."),
    ProjectRole("Project Manager", "Coordinates project work and manages delivery."),
    ProjectRole("Business Owner", "Defines business needs and expected outcomes."),
    ProjectRole("Project Team", "Performs project activities and creates deliverables."),
    ProjectRole("Customer", "Receives or uses the project's result."),
    ProjectRole("Governance Body", "Provides oversight and makes escalation decisions."),
    ProjectRole("Subject Matter Expert", "Provides specialized knowledge."),
]

print("\n13. COMMON PROJECT ROLES")
for role in project_roles:
    print(f"{role.role:20} -> {role.accountability}")


# =============================================================================
# 10. RACI
# =============================================================================

@dataclass
class RACIEntry:
    """Simple RACI matrix entry."""

    activity: str
    responsible: str
    accountable: str
    consulted: List[str]
    informed: List[str]


raci_entries = [
    RACIEntry(
        activity="Approve project charter",
        responsible="Project Manager",
        accountable="Sponsor",
        consulted=["Business Owner", "Finance"],
        informed=["Project Team"],
    ),
    RACIEntry(
        activity="Define business requirements",
        responsible="Business Analyst",
        accountable="Business Owner",
        consulted=["Users", "IT"],
        informed=["Sponsor"],
    ),
    RACIEntry(
        activity="Security assessment",
        responsible="Security Team",
        accountable="Security Manager",
        consulted=["Architect"],
        informed=["Project Manager"],
    ),
]

print("\n14. RACI EXAMPLE")
for entry in raci_entries:
    print(f"\nActivity: {entry.activity}")
    print(f"  R: {entry.responsible}")
    print(f"  A: {entry.accountable}")
    print(f"  C: {', '.join(entry.consulted)}")
    print(f"  I: {', '.join(entry.informed)}")


# =============================================================================
# 11. FEASIBILITY ANALYSIS
# =============================================================================

@dataclass
class FeasibilityAssessment:
    """Evaluate major dimensions of project feasibility."""

    technical: float
    financial: float
    operational: float
    legal: float
    schedule: float
    organizational: float

    def overall_score(self) -> float:
        scores = [
            self.technical,
            self.financial,
            self.operational,
            self.legal,
            self.schedule,
            self.organizational,
        ]
        return statistics.mean(scores)

    def decision(self) -> str:
        score = self.overall_score()

        if score >= 8:
            return "Strong feasibility"
        if score >= 6:
            return "Feasible with conditions"
        if score >= 4:
            return "Requires significant investigation"
        return "Weak feasibility"


feasibility = FeasibilityAssessment(
    technical=8.0,
    financial=7.5,
    operational=8.0,
    legal=9.0,
    schedule=7.0,
    organizational=7.5,
)

print("\n15. FEASIBILITY ASSESSMENT")
print(f"Overall feasibility score: {feasibility.overall_score():.2f}/10")
print(f"Assessment: {feasibility.decision()}")


# =============================================================================
# 12. BUSINESS CASE
# =============================================================================

@dataclass
class BusinessCase:
    """Basic financial and strategic business case."""

    investment: float
    annual_benefit: float
    annual_operating_cost: float
    project_life_years: int
    strategic_score: float

    def annual_net_benefit(self) -> float:
        return self.annual_benefit - self.annual_operating_cost

    def simple_roi(self) -> float:
        total_net_benefit = self.annual_net_benefit() * self.project_life_years
        return (total_net_benefit - self.investment) / self.investment

    def payback_years(self) -> Optional[float]:
        annual_net = self.annual_net_benefit()

        if annual_net <= 0:
            return None

        return self.investment / annual_net


business_case = BusinessCase(
    investment=750000,
    annual_benefit=500000,
    annual_operating_cost=100000,
    project_life_years=5,
    strategic_score=9,
)

print("\n16. BUSINESS CASE")
print(f"Investment: ${business_case.investment:,.2f}")
print(f"Annual net benefit: ${business_case.annual_net_benefit():,.2f}")
print(f"Simple ROI: {business_case.simple_roi() * 100:.2f}%")
print(f"Payback period: {business_case.payback_years():.2f} years")


# =============================================================================
# 13. NET PRESENT VALUE
# =============================================================================

def net_present_value(
    initial_investment: float,
    cash_flows: List[float],
    discount_rate: float,
) -> float:
    """
    Calculate NPV.

    cash_flows[0] represents the first future period rather than the initial
    investment. The initial investment is subtracted separately.

    NPV accounts for the time value of money and is more informative than a
    simple ROI calculation for multi-period investment decisions.
    """
    if discount_rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")

    present_value = -initial_investment

    for period, cash_flow in enumerate(cash_flows, start=1):
        present_value += cash_flow / ((1 + discount_rate) ** period)

    return present_value


npv = net_present_value(
    initial_investment=750000,
    cash_flows=[400000, 400000, 400000, 400000, 400000],
    discount_rate=0.10,
)

print("\n17. NET PRESENT VALUE")
print(f"NPV at 10% discount rate: ${npv:,.2f}")


# =============================================================================
# 14. COST-BENEFIT RATIO
# =============================================================================

def benefit_cost_ratio(total_benefits: float, total_costs: float) -> float:
    """Return benefits divided by costs."""
    if total_costs <= 0:
        raise ValueError("Total costs must be greater than zero.")

    return total_benefits / total_costs


bcr = benefit_cost_ratio(
    total_benefits=2500000,
    total_costs=1250000,
)

print("\n18. BENEFIT-COST RATIO")
print(f"Benefit-cost ratio: {bcr:.2f}")


# =============================================================================
# 15. ESTIMATION
# =============================================================================

@dataclass
class ThreePointEstimate:
    """
    Three-point estimate.

    Optimistic = best reasonable case
    Most likely = expected case
    Pessimistic = difficult but plausible case

    PERT expected value:
        (Optimistic + 4*Most Likely + Pessimistic) / 6
    """

    optimistic: float
    most_likely: float
    pessimistic: float

    def expected_value(self) -> float:
        if not (
            self.optimistic <= self.most_likely <= self.pessimistic
        ):
            raise ValueError(
                "Estimates must satisfy optimistic <= most_likely <= pessimistic."
            )

        return (
            self.optimistic
            + 4 * self.most_likely
            + self.pessimistic
        ) / 6

    def standard_deviation(self) -> float:
        return (self.pessimistic - self.optimistic) / 6


estimate = ThreePointEstimate(
    optimistic=4,
    most_likely=6,
    pessimistic=10,
)

print("\n19. THREE-POINT ESTIMATION")
print(f"Optimistic estimate: {estimate.optimistic} months")
print(f"Most likely estimate: {estimate.most_likely} months")
print(f"Pessimistic estimate: {estimate.pessimistic} months")
print(f"PERT expected estimate: {estimate.expected_value():.2f} months")
print(f"Approximate standard deviation: {estimate.standard_deviation():.2f}")


# =============================================================================
# 16. ASSUMPTIONS, CONSTRAINTS, DEPENDENCIES
# =============================================================================

@dataclass
class ProjectCondition:
    """Represent an assumption, constraint, or dependency."""

    category: str
    description: str
    impact_if_wrong: str


conditions = [
    ProjectCondition(
        "Assumption",
        "Business users will be available for requirements workshops.",
        "Requirements may be delayed.",
    ),
    ProjectCondition(
        "Constraint",
        "The implementation budget cannot exceed $750,000.",
        "Scope may need to be reduced.",
    ),
    ProjectCondition(
        "Dependency",
        "The security review must be completed before production deployment.",
        "Deployment cannot proceed.",
    ),
]

print("\n20. PROJECT CONDITIONS")
for condition in conditions:
    print(
        f"{condition.category:12} | "
        f"{condition.description} | "
        f"Impact: {condition.impact_if_wrong}"
    )


# =============================================================================
# 17. RISK MANAGEMENT
# =============================================================================

class RiskResponse(Enum):
    """Common response strategies for threats."""

    AVOID = "Avoid"
    MITIGATE = "Mitigate"
    TRANSFER = "Transfer"
    ACCEPT = "Accept"


@dataclass
class Risk:
    """Represent a project threat with probability and impact."""

    risk_id: str
    description: str
    probability: float
    impact: float
    response: RiskResponse
    owner: str

    def validate(self) -> None:
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1.")

        if self.impact < 0:
            raise ValueError("Impact cannot be negative.")

    def exposure(self) -> float:
        self.validate()
        return self.probability * self.impact

    def severity(self) -> str:
        exposure = self.exposure()

        if exposure >= 16:
            return "Very High"
        if exposure >= 9:
            return "High"
        if exposure >= 4:
            return "Medium"
        return "Low"


risks = [
    Risk(
        "R001",
        "Integration with the legacy system may take longer than expected.",
        probability=0.50,
        impact=8,
        response=RiskResponse.MITIGATE,
        owner="Technical Lead",
    ),
    Risk(
        "R002",
        "Key business users may be unavailable.",
        probability=0.30,
        impact=6,
        response=RiskResponse.MITIGATE,
        owner="Business Owner",
    ),
    Risk(
        "R003",
        "A regulatory interpretation may change during the project.",
        probability=0.15,
        impact=10,
        response=RiskResponse.ACCEPT,
        owner="Compliance Lead",
    ),
]

print("\n21. INITIAL RISK REGISTER")
for risk in risks:
    print(
        f"{risk.risk_id} | "
        f"Probability={risk.probability:.0%} | "
        f"Impact={risk.impact:.1f} | "
        f"Exposure={risk.exposure():.2f} | "
        f"Severity={risk.severity():9} | "
        f"Response={risk.response.value}"
    )


# =============================================================================
# 18. RISK MATRIX
# =============================================================================

def risk_matrix_level(probability: int, impact: int) -> str:
    """
    Qualitative 5x5 risk matrix.

    Both inputs are integer ratings from 1 through 5.
    """
    if not 1 <= probability <= 5:
        raise ValueError("Probability must be from 1 to 5.")

    if not 1 <= impact <= 5:
        raise ValueError("Impact must be from 1 to 5.")

    score = probability * impact

    if score >= 20:
        return "Critical"
    if score >= 12:
        return "High"
    if score >= 6:
        return "Medium"
    return "Low"


print("\n22. QUALITATIVE RISK MATRIX")
for probability, impact in [(1, 1), (2, 3), (3, 4), (5, 4), (5, 5)]:
    print(
        f"Probability={probability}, Impact={impact} "
        f"-> {risk_matrix_level(probability, impact)}"
    )


# =============================================================================
# 19. OPPORTUNITIES
# =============================================================================

@dataclass
class Opportunity:
    """Represent a positive uncertainty or potential upside."""

    description: str
    probability: float
    benefit: float

    def expected_value(self) -> float:
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1.")

        if self.benefit < 0:
            raise ValueError("Benefit should be non-negative.")

        return self.probability * self.benefit


opportunity = Opportunity(
    description="Automation could reduce processing effort more than expected.",
    probability=0.40,
    benefit=300000,
)

print("\n23. OPPORTUNITY ANALYSIS")
print(f"Opportunity: {opportunity.description}")
print(f"Expected value: ${opportunity.expected_value():,.2f}")


# =============================================================================
# 20. DEPENDENCY ANALYSIS
# =============================================================================

@dataclass
class Dependency:
    """Represent a relationship between project activities."""

    predecessor: str
    successor: str
    dependency_type: str
    description: str


dependencies = [
    Dependency(
        predecessor="Requirements approval",
        successor="Configuration",
        dependency_type="Finish-to-Start",
        description="Configuration starts after requirements are approved.",
    ),
    Dependency(
        predecessor="Security review",
        successor="Production deployment",
        dependency_type="Finish-to-Start",
        description="Deployment depends on completed security review.",
    ),
]

print("\n24. PROJECT DEPENDENCIES")
for dependency in dependencies:
    print(
        f"{dependency.predecessor} -> {dependency.successor} | "
        f"{dependency.dependency_type} | {dependency.description}"
    )


# =============================================================================
# 21. COMMUNICATION PLANNING
# =============================================================================

@dataclass
class CommunicationPlanItem:
    """Represent one planned project communication."""

    audience: str
    information: str
    frequency: str
    channel: str
    owner: str


communication_plan = [
    CommunicationPlanItem(
        audience="Executive Sponsor",
        information="Status, risks, decisions, benefits",
        frequency="Monthly",
        channel="Executive review",
        owner="Project Manager",
    ),
    CommunicationPlanItem(
        audience="Project Team",
        information="Tasks, blockers, dependencies",
        frequency="Weekly",
        channel="Team meeting",
        owner="Project Manager",
    ),
    CommunicationPlanItem(
        audience="End Users",
        information="Upcoming changes and training",
        frequency="At milestones",
        channel="Town hall and email",
        owner="Change Lead",
    ),
]

print("\n25. COMMUNICATION PLAN")
for item in communication_plan:
    print(
        f"{item.audience:18} | {item.frequency:14} | "
        f"{item.channel:22} | Owner: {item.owner}"
    )


# =============================================================================
# 22. SUCCESS CRITERIA
# =============================================================================

@dataclass
class SuccessCriterion:
    """A measurable condition used to determine project success."""

    name: str
    target: str
    measurement_method: str


success_criteria = [
    SuccessCriterion(
        "Resolution time",
        "Average resolution time <= 2.4 days",
        "Operational reporting after launch",
    ),
    SuccessCriterion(
        "System availability",
        "Availability >= 99.5%",
        "Monitoring reports",
    ),
    SuccessCriterion(
        "User adoption",
        ">= 90% of target users actively use the platform",
        "Usage analytics",
    ),
    SuccessCriterion(
        "Budget",
        "Final project cost <= approved baseline plus authorized contingency",
        "Financial reporting",
    ),
]

print("\n26. SUCCESS CRITERIA")
for criterion in success_criteria:
    print(
        f"{criterion.name:20} | Target: {criterion.target} | "
        f"Measurement: {criterion.measurement_method}"
    )


# =============================================================================
# 23. ACCEPTANCE CRITERIA
# =============================================================================

@dataclass
class AcceptanceCriterion:
    """A condition that a deliverable must satisfy before acceptance."""

    deliverable: str
    condition: str


acceptance_criteria = [
    AcceptanceCriterion(
        "Customer service platform",
        "Users can create, assign, update, and close service requests.",
    ),
    AcceptanceCriterion(
        "Reporting dashboard",
        "Dashboard displays agreed service-performance metrics accurately.",
    ),
    AcceptanceCriterion(
        "Data migration",
        "Approved migration reconciliation shows no unexplained critical data loss.",
    ),
]

print("\n27. ACCEPTANCE CRITERIA")
for criterion in acceptance_criteria:
    print(f"{criterion.deliverable:25} -> {criterion.condition}")


# =============================================================================
# 24. PROJECT CHARTER
# =============================================================================

@dataclass
class ProjectCharter:
    """
    Core initiation document.

    A charter normally gives formal authorization and establishes high-level
    direction without attempting to contain every detailed planning decision.
    """

    project_name: str
    business_need: str
    objective: str
    sponsor: str
    project_manager: str
    high_level_scope: List[str]
    major_deliverables: List[str]
    major_stakeholders: List[str]
    assumptions: List[str]
    constraints: List[str]
    major_risks: List[str]
    estimated_budget: float
    estimated_duration_months: float
    success_criteria: List[str]
    approval_status: str = "Draft"

    def authorize(self) -> None:
        self.approval_status = "Authorized"

    def summary(self) -> str:
        return (
            f"Project: {self.project_name}\n"
            f"Status: {self.approval_status}\n"
            f"Sponsor: {self.sponsor}\n"
            f"Project Manager: {self.project_manager}\n"
            f"Budget: ${self.estimated_budget:,.2f}\n"
            f"Duration: {self.estimated_duration_months:.1f} months\n"
            f"Objective: {self.objective}"
        )


charter = ProjectCharter(
    project_name="Digital Customer Service Platform",
    business_need=proposal.problem,
    objective=proposal.objective,
    sponsor="Executive Sponsor",
    project_manager="Project Manager",
    high_level_scope=proposal.high_level_scope,
    major_deliverables=[
        "Approved requirements",
        "Configured platform",
        "Migrated data",
        "Integrated systems",
        "Trained users",
        "Production deployment",
    ],
    major_stakeholders=[stakeholder.name for stakeholder in stakeholders],
    assumptions=[
        condition.description
        for condition in conditions
        if condition.category == "Assumption"
    ],
    constraints=[
        condition.description
        for condition in conditions
        if condition.category == "Constraint"
    ],
    major_risks=[risk.description for risk in risks],
    estimated_budget=proposal.estimated_cost,
    estimated_duration_months=proposal.estimated_duration_months,
    success_criteria=[criterion.target for criterion in success_criteria],
)

print("\n28. PROJECT CHARTER")
print(charter.summary())


# =============================================================================
# 25. PROJECT AUTHORIZATION
# =============================================================================

class AuthorizationDecision(Enum):
    """Possible initiation-gate decisions."""

    APPROVE = "Approve"
    REJECT = "Reject"
    DEFER = "Defer"
    REVISE = "Revise"


@dataclass
class InitiationGate:
    """A decision gate before detailed project planning."""

    business_case_ready: bool
    sponsor_identified: bool
    objective_defined: bool
    feasibility_assessed: bool
    major_risks_identified: bool
    scope_boundary_defined: bool

    def readiness_score(self) -> float:
        values = [
            self.business_case_ready,
            self.sponsor_identified,
            self.objective_defined,
            self.feasibility_assessed,
            self.major_risks_identified,
            self.scope_boundary_defined,
        ]
        return sum(values) / len(values)

    def recommended_decision(self) -> AuthorizationDecision:
        score = self.readiness_score()

        if score == 1:
            return AuthorizationDecision.APPROVE
        if score >= 0.8:
            return AuthorizationDecision.REVISE
        return AuthorizationDecision.DEFER


gate = InitiationGate(
    business_case_ready=True,
    sponsor_identified=True,
    objective_defined=True,
    feasibility_assessed=True,
    major_risks_identified=True,
    scope_boundary_defined=True,
)

print("\n29. INITIATION GATE")
print(f"Readiness: {gate.readiness_score():.0%}")
print(f"Recommended decision: {gate.recommended_decision().value}")

if gate.recommended_decision() == AuthorizationDecision.APPROVE:
    charter.authorize()

print(f"Charter status: {charter.approval_status}")


# =============================================================================
# 26. PROJECT PRIORITIZATION
# =============================================================================

@dataclass
class CandidateProject:
    """Represent a project competing for organizational resources."""

    name: str
    strategic_alignment: float
    financial_value: float
    urgency: float
    feasibility: float
    risk: float

    def weighted_score(
        self,
        strategic_weight: float = 0.30,
        financial_weight: float = 0.25,
        urgency_weight: float = 0.15,
        feasibility_weight: float = 0.20,
        risk_weight: float = 0.10,
    ) -> float:
        """
        Calculate a weighted score.

        Risk is inverted because higher risk should reduce the score.
        All input ratings are expected to be on a 0-10 scale.
        """
        weights = [
            strategic_weight,
            financial_weight,
            urgency_weight,
            feasibility_weight,
            risk_weight,
        ]

        if not math.isclose(sum(weights), 1.0):
            raise ValueError("Weights must sum to 1.0.")

        return (
            self.strategic_alignment * strategic_weight
            + self.financial_value * financial_weight
            + self.urgency * urgency_weight
            + self.feasibility * feasibility_weight
            + (10 - self.risk) * risk_weight
        )


candidate_projects = [
    CandidateProject(
        "Customer Service Platform",
        strategic_alignment=9,
        financial_value=8,
        urgency=8,
        feasibility=8,
        risk=4,
    ),
    CandidateProject(
        "Office Renovation",
        strategic_alignment=4,
        financial_value=5,
        urgency=3,
        feasibility=9,
        risk=2,
    ),
    CandidateProject(
        "Data Analytics Platform",
        strategic_alignment=10,
        financial_value=9,
        urgency=7,
        feasibility=6,
        risk=6,
    ),
]

ranked_projects = sorted(
    candidate_projects,
    key=lambda project: project.weighted_score(),
    reverse=True,
)

print("\n30. PROJECT PRIORITIZATION")
for rank, project in enumerate(ranked_projects, start=1):
    print(
        f"{rank}. {project.name:28} "
        f"Score={project.weighted_score():.2f}/10"
    )


# =============================================================================
# 27. TRADE-OFFS
# =============================================================================

def compare_tradeoffs(
    options: Dict[str, Dict[str, float]]
) -> List[Tuple[str, float]]:
    """
    Compare alternatives using normalized weighted criteria.

    This is an illustrative decision-support technique, not a replacement for
    management judgment.
    """
    results = []

    for option_name, criteria in options.items():
        score = (
            criteria["value"] * 0.40
            + criteria["feasibility"] * 0.30
            + criteria["urgency"] * 0.20
            + (10 - criteria["risk"]) * 0.10
        )
        results.append((option_name, score))

    return sorted(results, key=lambda item: item[1], reverse=True)


alternatives = {
    "Build internally": {
        "value": 9,
        "feasibility": 6,
        "urgency": 8,
        "risk": 7,
    },
    "Buy commercial solution": {
        "value": 8,
        "feasibility": 9,
        "urgency": 9,
        "risk": 4,
    },
    "Do nothing": {
        "value": 2,
        "feasibility": 10,
        "urgency": 2,
        "risk": 8,
    },
}

print("\n31. OPTION TRADE-OFF ANALYSIS")
for option, score in compare_tradeoffs(alternatives):
    print(f"{option:25} -> {score:.2f}/10")


# =============================================================================
# 28. AGILE, PREDICTIVE, AND HYBRID INITIATION
# =============================================================================

class DeliveryApproach(Enum):
    """Common project delivery approaches."""

    PREDICTIVE = "Predictive"
    AGILE = "Agile"
    HYBRID = "Hybrid"


def initiation_characteristics(approach: DeliveryApproach) -> List[str]:
    """Return typical initiation characteristics for a delivery approach."""
    if approach == DeliveryApproach.PREDICTIVE:
        return [
            "Higher emphasis on early scope definition",
            "Detailed baseline planning follows initiation",
            "Formal approval gates are common",
            "Useful when requirements are relatively stable",
        ]

    if approach == DeliveryApproach.AGILE:
        return [
            "Vision and product goals are emphasized",
            "Detailed requirements can evolve",
            "Initial backlog and product direction are established",
            "Useful when uncertainty and learning are high",
        ]

    return [
        "High-level scope and governance may be predictive",
        "Product development may use iterative delivery",
        "Useful when some requirements are fixed and others are uncertain",
    ]


print("\n32. DELIVERY APPROACHES")
for approach in DeliveryApproach:
    print(f"\n{approach.value}:")
    for characteristic in initiation_characteristics(approach):
        print(f"- {characteristic}")


# =============================================================================
# 29. AGILE PRODUCT VISION AND MVP
# =============================================================================

@dataclass
class ProductVision:
    """Represent a concise product or project vision."""

    target_user: str
    problem: str
    desired_change: str
    value: str


@dataclass
class MVP:
    """Represent a minimum viable product boundary."""

    must_have: List[str]
    intentionally_excluded: List[str]

    def scope_size(self) -> int:
        return len(self.must_have)


vision = ProductVision(
    target_user="Customer service agents",
    problem="Requests are fragmented across multiple channels.",
    desired_change="Provide one workflow for managing requests.",
    value="Faster and more consistent service.",
)

mvp = MVP(
    must_have=[
        "Request creation",
        "Assignment",
        "Status tracking",
        "Basic reporting",
    ],
    intentionally_excluded=[
        "Advanced predictive analytics",
        "Internationalization",
        "Voice automation",
    ],
)

print("\n33. AGILE-ORIENTED INITIATION")
print(f"Target user: {vision.target_user}")
print(f"Problem: {vision.problem}")
print(f"Desired change: {vision.desired_change}")
print(f"Value: {vision.value}")
print(f"MVP must-have capabilities: {mvp.scope_size()}")


# =============================================================================
# 30. REQUIREMENTS AT INITIATION
# =============================================================================

@dataclass
class HighLevelRequirement:
    """Represent an early requirement without prematurely over-specifying it."""

    requirement_id: str
    description: str
    priority: str
    source: str


requirements = [
    HighLevelRequirement(
        "REQ-001",
        "Users must be able to create service requests.",
        "Must",
        "Business Owner",
    ),
    HighLevelRequirement(
        "REQ-002",
        "Managers must be able to monitor service performance.",
        "Must",
        "Operations",
    ),
    HighLevelRequirement(
        "REQ-003",
        "The platform should support advanced predictive analytics.",
        "Could",
        "Innovation Team",
    ),
]

print("\n34. HIGH-LEVEL REQUIREMENTS")
for requirement in requirements:
    print(
        f"{requirement.requirement_id} | "
        f"{requirement.priority:5} | "
        f"{requirement.description}"
    )


# =============================================================================
# 31. PROJECT LIFECYCLE
# =============================================================================

def project_lifecycle() -> None:
    """
    A simplified lifecycle showing where initiation fits.

    Different organizations use different names and lifecycle structures.
    """
    phases = [
        ("Initiation", "Determine why the project should exist and authorize it."),
        ("Planning", "Define how the work will be performed and controlled."),
        ("Execution", "Perform project work and create deliverables."),
        ("Monitoring and Control", "Measure performance and manage changes."),
        ("Closure", "Accept results, close contracts, capture lessons, and transition."),
    ]

    print("\n35. SIMPLIFIED PROJECT LIFECYCLE")
    for index, (phase, purpose) in enumerate(phases, start=1):
        print(f"{index}. {phase}: {purpose}")


project_lifecycle()


# =============================================================================
# 32. INITIATION VS PLANNING
# =============================================================================

def initiation_vs_planning() -> None:
    """Explain the important boundary between initiation and detailed planning."""
    print("\n36. INITIATION VS PLANNING")

    rows = [
        ("Business need", "Why the project exists", "Detailed work packages"),
        ("Scope", "High-level boundaries", "Detailed scope baseline"),
        ("Schedule", "High-level duration", "Detailed schedule"),
        ("Cost", "Rough-order estimate", "Detailed cost baseline"),
        ("Risks", "Major risks", "Detailed risk responses"),
        ("Stakeholders", "Major stakeholders", "Detailed engagement plan"),
        ("Resources", "High-level resource needs", "Detailed resource allocation"),
    ]

    for category, initiation, planning in rows:
        print(f"{category:15} | Initiation: {initiation:32} | Planning: {planning}")


initiation_vs_planning()


# =============================================================================
# 33. GOVERNANCE
# =============================================================================

@dataclass
class GovernanceDecision:
    """Represent a project governance decision."""

    decision: str
    authority: str
    escalation_trigger: str


governance_decisions = [
    GovernanceDecision(
        "Approve charter",
        "Sponsor",
        "Not applicable",
    ),
    GovernanceDecision(
        "Approve major scope change",
        "Steering Committee",
        "Change exceeds delegated authority",
    ),
    GovernanceDecision(
        "Approve technical design",
        "Architecture Authority",
        "Architecture standards affected",
    ),
    GovernanceDecision(
        "Accept final deliverables",
        "Business Owner",
        "Acceptance criteria not met",
    ),
]

print("\n37. GOVERNANCE")
for decision in governance_decisions:
    print(
        f"{decision.decision:28} | "
        f"Authority: {decision.authority:22} | "
        f"Escalation: {decision.escalation_trigger}"
    )


# =============================================================================
# 34. RAID
# =============================================================================

@dataclass
class RAIDItem:
    """Represent an item in a RAID log."""

    category: str
    description: str
    owner: str
    due_date: date


raid_items = [
    RAIDItem(
        "Risk",
        "Legacy integration may require additional development.",
        "Technical Lead",
        date.today() + timedelta(days=21),
    ),
    RAIDItem(
        "Assumption",
        "Business users will attend workshops.",
        "Business Owner",
        date.today() + timedelta(days=14),
    ),
    RAIDItem(
        "Issue",
        "Current customer data contains inconsistent identifiers.",
        "Data Lead",
        date.today() + timedelta(days=10),
    ),
    RAIDItem(
        "Dependency",
        "Security review is required before production deployment.",
        "Security Lead",
        date.today() + timedelta(days=60),
    ),
]

print("\n38. RAID LOG")
for item in raid_items:
    print(
        f"{item.category:11} | "
        f"{item.owner:18} | "
        f"Due: {item.due_date.isoformat()} | "
        f"{item.description}"
    )


# =============================================================================
# 35. CHANGE CONTROL
# =============================================================================

@dataclass
class ChangeRequest:
    """Represent a proposed change to an initiated project."""

    change_id: str
    description: str
    cost_impact: float
    schedule_impact_days: int
    scope_impact: str
    reason: str
    status: str = "Pending"

    def evaluate(self, delegated_cost_limit: float = 50000) -> str:
        """
        Determine whether the project manager may approve the change.

        Real governance rules differ by organization. This is a teaching model.
        """
        if self.cost_impact < 0:
            raise ValueError("Cost impact cannot be negative.")

        if self.cost_impact <= delegated_cost_limit and self.schedule_impact_days <= 5:
            self.status = "Within delegated authority"
        else:
            self.status = "Escalate for approval"

        return self.status


change = ChangeRequest(
    change_id="CR-001",
    description="Add an additional management report.",
    cost_impact=30000,
    schedule_impact_days=3,
    scope_impact="Small reporting enhancement",
    reason="Management reporting requirement discovered during analysis.",
)

print("\n39. CHANGE REQUEST")
print(change.evaluate())


# =============================================================================
# 36. PROJECT INITIATION DOCUMENT SET
# =============================================================================

initiation_documents = {
    "Project idea": "Initial description of a problem, opportunity, or need.",
    "Business case": "Reasoned justification for investing in the project.",
    "Feasibility assessment": "Assessment of whether the proposed effort is viable.",
    "Project charter": "High-level authorization and direction.",
    "Stakeholder register": "Initial identification and analysis of stakeholders.",
    "High-level requirements": "Early understanding of required capabilities.",
    "Initial risk register": "Major threats and opportunities identified early.",
    "Initial assumptions and constraints": "Conditions that shape the project.",
    "High-level scope statement": "Initial boundaries of project work.",
    "Governance model": "Decision rights, escalation, and oversight structure.",
}

print("\n40. COMMON INITIATION DOCUMENTS")
for document, purpose in initiation_documents.items():
    print(f"{document:32} -> {purpose}")


# =============================================================================
# 37. PROJECT INITIATION CHECKLIST
# =============================================================================

def initiation_checklist() -> Dict[str, bool]:
    """Return a reusable initiation readiness checklist."""
    return {
        "Business problem or opportunity is documented": True,
        "Business value is understood": True,
        "Sponsor is identified": True,
        "Business owner is identified": True,
        "Project manager is identified": True,
        "High-level objective is defined": True,
        "High-level scope is defined": True,
        "Out-of-scope boundaries are known": True,
        "Major stakeholders are identified": True,
        "Feasibility has been considered": True,
        "Initial cost and duration are estimated": True,
        "Major risks are identified": True,
        "Assumptions are documented": True,
        "Constraints are documented": True,
        "Dependencies are identified": True,
        "Success criteria are defined": True,
        "Governance is established": True,
        "Authorization decision is documented": True,
    }


print("\n41. PROJECT INITIATION CHECKLIST")
checklist = initiation_checklist()
for item, completed in checklist.items():
    print(f"[{'X' if completed else ' '}] {item}")


# =============================================================================
# 38. PROJECT READINESS SCORE
# =============================================================================

def readiness_percentage(checklist: Dict[str, bool]) -> float:
    """Calculate the percentage of completed initiation checks."""
    if not checklist:
        return 0.0

    return sum(checklist.values()) / len(checklist) * 100


print(f"\nInitiation readiness: {readiness_percentage(checklist):.1f}%")


# =============================================================================
# 39. FINANCIAL SENSITIVITY
# =============================================================================

def sensitivity_analysis(
    investment: float,
    annual_benefit: float,
    annual_operating_cost: float,
    years: int,
    benefit_change_rates: List[float],
) -> List[Tuple[float, float, float]]:
    """
    Calculate ROI under different benefit assumptions.

    This demonstrates why a business case should be tested under multiple
    plausible conditions instead of relying on one optimistic forecast.
    """
    if investment <= 0:
        raise ValueError("Investment must be greater than zero.")

    if years <= 0:
        raise ValueError("Years must be greater than zero.")

    results = []

    for rate in benefit_change_rates:
        adjusted_benefit = annual_benefit * (1 + rate)
        net_benefit = adjusted_benefit - annual_operating_cost
        total_net_benefit = net_benefit * years
        roi = (total_net_benefit - investment) / investment
        results.append((rate, adjusted_benefit, roi))

    return results


print("\n42. BUSINESS CASE SENSITIVITY")
for rate, adjusted_benefit, roi in sensitivity_analysis(
    investment=750000,
    annual_benefit=500000,
    annual_operating_cost=100000,
    years=5,
    benefit_change_rates=[-0.30, -0.15, 0.00, 0.15, 0.30],
):
    print(
        f"Benefit change={rate:+.0%} | "
        f"Annual benefit=${adjusted_benefit:,.0f} | "
        f"ROI={roi:.1%}"
    )


# =============================================================================
# 40. BREAK-EVEN ANALYSIS
# =============================================================================

def break_even_units(
    fixed_cost: float,
    benefit_per_unit: float,
    variable_cost_per_unit: float,
) -> float:
    """
    Calculate units required to recover fixed cost.

    This concept is useful when project value depends on transaction volume,
    subscriptions, customers, or other measurable units.
    """
    contribution = benefit_per_unit - variable_cost_per_unit

    if contribution <= 0:
        raise ValueError(
            "Benefit per unit must exceed variable cost per unit."
        )

    return fixed_cost / contribution


break_even = break_even_units(
    fixed_cost=1000000,
    benefit_per_unit=100,
    variable_cost_per_unit=40,
)

print("\n43. BREAK-EVEN ANALYSIS")
print(f"Break-even volume: {break_even:,.0f} units")


# =============================================================================
# 41. RESOURCE CAPACITY
# =============================================================================

@dataclass
class Resource:
    """Represent an available resource and its capacity."""

    name: str
    monthly_capacity_hours: float
    allocated_hours: float = 0

    @property
    def remaining_capacity(self) -> float:
        return self.monthly_capacity_hours - self.allocated_hours

    def allocate(self, hours: float) -> bool:
        if hours < 0:
            raise ValueError("Hours cannot be negative.")

        if hours > self.remaining_capacity:
            return False

        self.allocated_hours += hours
        return True


resources = [
    Resource("Business Analyst", 160),
    Resource("Technical Lead", 160),
    Resource("Developer", 320),
    Resource("Security Specialist", 80),
]

allocations = {
    "Business Analyst": 120,
    "Technical Lead": 140,
    "Developer": 300,
    "Security Specialist": 70,
}

print("\n44. RESOURCE CAPACITY CHECK")
for resource in resources:
    requested = allocations.get(resource.name, 0)
    approved = resource.allocate(requested)
    print(
        f"{resource.name:20} | "
        f"Requested={requested:5.0f}h | "
        f"Approved={approved} | "
        f"Remaining={resource.remaining_capacity:5.0f}h"
    )


# =============================================================================
# 42. PROJECT COMPLEXITY
# =============================================================================

def complexity_score(
    stakeholder_count: int,
    integration_count: int,
    geographic_regions: int,
    regulatory_intensity: int,
    uncertainty: int,
) -> float:
    """
    Produce an illustrative complexity score.

    This is not a universal project-management standard. Organizations should
    calibrate their own models against historical project performance.
    """
    if any(value < 0 for value in [
        stakeholder_count,
        integration_count,
        geographic_regions,
        regulatory_intensity,
        uncertainty,
    ]):
        raise ValueError("Complexity inputs cannot be negative.")

    score = (
        min(stakeholder_count / 20, 1) * 20
        + min(integration_count / 10, 1) * 20
        + min(geographic_regions / 10, 1) * 15
        + min(regulatory_intensity / 10, 1) * 20
        + min(uncertainty / 10, 1) * 25
    )

    return min(score, 100)


print("\n45. PROJECT COMPLEXITY")
complexity = complexity_score(
    stakeholder_count=15,
    integration_count=6,
    geographic_regions=3,
    regulatory_intensity=6,
    uncertainty=7,
)
print(f"Illustrative complexity score: {complexity:.1f}/100")


# =============================================================================
# 43. DECISION QUALITY
# =============================================================================

@dataclass
class DecisionFactor:
    """Factor used in a project-initiation decision."""

    name: str
    evidence_available: bool
    confidence: float

    def validate(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1.")


decision_factors = [
    DecisionFactor("Business need", True, 0.90),
    DecisionFactor("Expected benefits", True, 0.75),
    DecisionFactor("Technical feasibility", True, 0.80),
    DecisionFactor("Cost estimate", True, 0.65),
    DecisionFactor("Schedule estimate", True, 0.60),
    DecisionFactor("Risk profile", True, 0.70),
]

print("\n46. DECISION CONFIDENCE")
for factor in decision_factors:
    factor.validate()
    print(
        f"{factor.name:25} | "
        f"Evidence={factor.evidence_available} | "
        f"Confidence={factor.confidence:.0%}"
    )


# =============================================================================
# 44. EDGE CASES
# =============================================================================

def demonstrate_edge_cases() -> None:
    """Show how initiation models should handle invalid or unusual conditions."""

    print("\n47. EDGE CASES")

    cases = [
        ("Zero-cost project", 0),
        ("Negative investment", -1000),
        ("Zero benefit", 0),
    ]

    for label, value in cases:
        try:
            result = benefit_cost_ratio(
                total_benefits=100000,
                total_costs=value,
            )
            print(f"{label}: ratio={result}")
        except ValueError as error:
            print(f"{label}: handled safely -> {error}")

    print(
        "\nImportant: A project can be strategically necessary even when "
        "its direct financial return is weak. Regulatory, safety, compliance, "
        "or risk-reduction projects may require different decision criteria."
    )


demonstrate_edge_cases()


# =============================================================================
# 45. SECURITY CONSIDERATIONS
# =============================================================================

def security_considerations() -> None:
    """
    Security should be considered during initiation rather than added only
    immediately before deployment.
    """
    print("\n48. SECURITY CONSIDERATIONS DURING INITIATION")

    considerations = [
        "Identify whether sensitive or regulated data is involved.",
        "Identify applicable privacy, security, and regulatory obligations.",
        "Determine whether security architecture review is required.",
        "Identify authentication and authorization requirements.",
        "Identify third-party and supplier security dependencies.",
        "Define security ownership and approval authority.",
        "Include security activities in high-level scope and estimates.",
        "Identify security risks in the initial risk register.",
    ]

    for item in considerations:
        print(f"- {item}")


security_considerations()


# =============================================================================
# 46. DATA AND PRIVACY CONSIDERATIONS
# =============================================================================

def data_considerations() -> None:
    print("\n49. DATA AND PRIVACY CONSIDERATIONS")

    considerations = [
        "What data will the project create, access, transform, or transfer?",
        "Who owns the data?",
        "Where will data be stored?",
        "How long must data be retained?",
        "Who is authorized to access it?",
        "Are cross-border transfers involved?",
        "Are vendors or external processors involved?",
        "Are data-quality problems likely to affect project outcomes?",
    ]

    for item in considerations:
        print(f"- {item}")


data_considerations()


# =============================================================================
# 47. PRODUCTION AND IMPLEMENTATION CONSIDERATIONS
# =============================================================================

def production_considerations() -> None:
    print("\n50. PRODUCTION AND IMPLEMENTATION CONSIDERATIONS")

    considerations = [
        "Operational ownership after project closure",
        "Support model",
        "Training requirements",
        "Deployment approach",
        "Business continuity",
        "Rollback strategy",
        "Monitoring",
        "Performance expectations",
        "Security controls",
        "Data migration",
        "Vendor support",
        "Maintenance costs",
        "Benefits measurement after launch",
        "Transition to operations",
    ]

    for item in considerations:
        print(f"- {item}")


production_considerations()


# =============================================================================
# 48. PERFORMANCE CONSIDERATIONS
# =============================================================================

def performance_considerations() -> None:
    print("\n51. PERFORMANCE CONSIDERATIONS")

    considerations = [
        "Avoid treating initial estimates as precise commitments.",
        "Use ranges when uncertainty is material.",
        "Separate project cost from recurring operational cost.",
        "Identify resource bottlenecks early.",
        "Consider integration complexity before committing to dates.",
        "Use historical data when available.",
        "Test assumptions through prototypes or discovery where appropriate.",
        "Revisit estimates as uncertainty decreases.",
    ]

    for item in considerations:
        print(f"- {item}")


performance_considerations()


# =============================================================================
# 49. COMMON INITIATION MISTAKES
# =============================================================================

def common_mistakes() -> None:
    print("\n52. COMMON PROJECT INITIATION MISTAKES")

    mistakes = {
        "Solution before problem":
            "Selecting a technology before understanding the business need.",
        "Vague objective":
            "Starting work without defining a measurable desired result.",
        "No sponsor":
            "Beginning execution without clear executive ownership.",
        "Scope ambiguity":
            "Failing to define what the project does and does not cover.",
        "False precision":
            "Presenting early estimates as if they were guaranteed values.",
        "Ignoring stakeholders":
            "Failing to understand people affected by the change.",
        "Ignoring operations":
            "Planning delivery without considering post-project ownership.",
        "Ignoring security":
            "Discovering security requirements near deployment.",
        "Optimism bias":
            "Assuming best-case conditions without sensitivity analysis.",
        "No success measures":
            "Declaring a project successful merely because it was delivered.",
        "Overplanning too early":
            "Spending excessive effort on detailed plans before authorization.",
        "Under-investigating":
            "Approving a major investment without enough evidence.",
    }

    for mistake, explanation in mistakes.items():
        print(f"\n{mistake}:")
        print(f"  {explanation}")


common_mistakes()


# =============================================================================
# 50. DECISION RULES
# =============================================================================

def initiation_decision_rule(
    strategic_alignment: float,
    feasibility: float,
    business_case_strength: float,
    risk_score: float,
    readiness: float,
) -> str:
    """
    Illustrative multi-factor initiation decision.

    Scores are 0-10. Risk score is interpreted so that a higher value means
    higher risk.
    """
    if not all(
        0 <= value <= 10
        for value in [
            strategic_alignment,
            feasibility,
            business_case_strength,
            risk_score,
            readiness,
        ]
    ):
        raise ValueError("All scores must be between 0 and 10.")

    weighted_score = (
        strategic_alignment * 0.25
        + feasibility * 0.20
        + business_case_strength * 0.25
        + (10 - risk_score) * 0.15
        + readiness * 0.15
    )

    if weighted_score >= 7.5 and readiness >= 7:
        return "Recommend approval"

    if weighted_score >= 6:
        return "Investigate or revise"

    return "Do not authorize yet"


print("\n53. INTEGRATED INITIATION DECISION")
decision = initiation_decision_rule(
    strategic_alignment=9,
    feasibility=8,
    business_case_strength=8,
    risk_score=4,
    readiness=9,
)
print(f"Decision: {decision}")


# =============================================================================
# 51. COMPLETE PROJECT INITIATION SIMULATION
# =============================================================================

@dataclass
class ProjectInitiationSimulation:
    """
    A reusable model showing how a project moves from an idea toward
    authorization.
    """

    idea: ProjectIdea
    proposal: Optional[ProjectProposal] = None
    feasibility: Optional[FeasibilityAssessment] = None
    stakeholders: List[Stakeholder] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    charter: Optional[ProjectCharter] = None

    def develop_proposal(self) -> ProjectProposal:
        self.proposal = ProjectProposal(
            name=self.idea.name,
            problem=self.idea.problem,
            objective=(
                "Reduce average customer-resolution time by 40% "
                "within six months of implementation."
            ),
            expected_benefits=[
                "Faster customer service",
                "Improved operational visibility",
                "Reduced manual effort",
            ],
            high_level_scope=[
                "Process analysis",
                "Platform implementation",
                "Integration",
                "Data migration",
                "Training",
            ],
            estimated_cost=750000,
            estimated_duration_months=6,
            strategic_alignment_score=9,
            feasibility_score=8,
        )
        return self.proposal

    def assess_feasibility(self) -> FeasibilityAssessment:
        self.feasibility = FeasibilityAssessment(
            technical=8,
            financial=8,
            operational=8,
            legal=9,
            schedule=7,
            organizational=8,
        )
        return self.feasibility

    def identify_stakeholders(self) -> List[Stakeholder]:
        self.stakeholders = [
            Stakeholder(
                "Executive Sponsor",
                "Sponsor",
                StakeholderInfluence.HIGH,
                StakeholderInterest.HIGH,
                "Strategic value",
            ),
            Stakeholder(
                "Business Owner",
                "Owner",
                StakeholderInfluence.HIGH,
                StakeholderInterest.HIGH,
                "Operational improvement",
            ),
            Stakeholder(
                "IT Lead",
                "Technical Lead",
                StakeholderInfluence.HIGH,
                StakeholderInterest.HIGH,
                "Technical feasibility",
            ),
            Stakeholder(
                "End Users",
                "Users",
                StakeholderInfluence.LOW,
                StakeholderInterest.HIGH,
                "Usable workflow",
            ),
        ]
        return self.stakeholders

    def identify_risks(self) -> List[Risk]:
        self.risks = [
            Risk(
                "R001",
                "Legacy integration complexity",
                0.50,
                8,
                RiskResponse.MITIGATE,
                "IT Lead",
            ),
            Risk(
                "R002",
                "Limited user availability",
                0.30,
                6,
                RiskResponse.MITIGATE,
                "Business Owner",
            ),
        ]
        return self.risks

    def create_charter(self) -> ProjectCharter:
        if self.proposal is None:
            raise RuntimeError("Proposal must be developed first.")

        self.charter = ProjectCharter(
            project_name=self.proposal.name,
            business_need=self.proposal.problem,
            objective=self.proposal.objective,
            sponsor="Executive Sponsor",
            project_manager="Assigned Project Manager",
            high_level_scope=self.proposal.high_level_scope,
            major_deliverables=[
                "Requirements",
                "Configured platform",
                "Integrations",
                "Migrated data",
                "Training",
                "Production deployment",
            ],
            major_stakeholders=[s.name for s in self.stakeholders],
            assumptions=[
                "Business users will be available for discovery.",
                "Required technology resources can be allocated.",
            ],
            constraints=[
                "Budget limit of $750,000.",
                "Target implementation duration of six months.",
            ],
            major_risks=[risk.description for risk in self.risks],
            estimated_budget=self.proposal.estimated_cost,
            estimated_duration_months=self.proposal.estimated_duration_months,
            success_criteria=[
                "Average resolution time reduced by 40%.",
                "Target users trained before production launch.",
                "Critical acceptance criteria satisfied.",
            ],
        )

        return self.charter

    def authorize(self) -> None:
        if self.charter is None:
            raise RuntimeError("Charter must exist before authorization.")

        if self.feasibility is None:
            raise RuntimeError("Feasibility assessment is required.")

        if not self.stakeholders:
            raise RuntimeError("Stakeholder identification is required.")

        if not self.risks:
            raise RuntimeError("Initial risk identification is required.")

        self.charter.authorize()


simulation = ProjectInitiationSimulation(
    idea=ProjectIdea(
        name="Customer Service Transformation",
        problem="Customer requests are processed through fragmented workflows.",
        expected_benefit="Faster and more consistent service.",
        proposed_solution="Implement a centralized customer service platform.",
        strategic_alignment="Supports digital transformation.",
    )
)

simulation.develop_proposal()
simulation.assess_feasibility()
simulation.identify_stakeholders()
simulation.identify_risks()
simulation.create_charter()

print("\n54. COMPLETE PROJECT INITIATION SIMULATION")
print("Before authorization:")
print(simulation.charter.summary())

simulation.authorize()

print("\nAfter authorization:")
print(simulation.charter.summary())


# =============================================================================
# 52. VALIDATION TESTS
# =============================================================================

def run_validation_tests() -> None:
    """
    Basic tests demonstrate that important calculations and validation rules
    behave correctly.
    """

    print("\n55. VALIDATION TESTS")

    # SMART objective validation.
    assert objective.is_complete()

    # Benefit-cost ratio.
    assert math.isclose(
        benefit_cost_ratio(200, 100),
        2.0,
    )

    # NPV with zero discount rate.
    assert math.isclose(
        net_present_value(
            initial_investment=100,
            cash_flows=[50, 50],
            discount_rate=0,
        ),
        0,
    )

    # PERT calculation.
    assert math.isclose(
        ThreePointEstimate(4, 6, 10).expected_value(),
        40 / 6,
    )

    # Risk exposure.
    test_risk = Risk(
        "TEST",
        "Test risk",
        probability=0.5,
        impact=10,
        response=RiskResponse.MITIGATE,
        owner="Tester",
    )
    assert math.isclose(test_risk.exposure(), 5.0)

    # Scope classification.
    assert scope.check_item("Customer service workflow") == "IN SCOPE"
    assert scope.check_item("Replacement of the corporate ERP") == "OUT OF SCOPE"
    assert scope.check_item("Unknown item") == "UNDEFINED"

    # Project prioritization.
    scores = [project.weighted_score() for project in candidate_projects]
    assert all(0 <= score <= 10 for score in scores)

    # Charter authorization.
    assert simulation.charter is not None
    assert simulation.charter.approval_status == "Authorized"

    # Invalid probability should fail.
    try:
        Risk(
            "INVALID",
            "Invalid risk",
            probability=1.5,
            impact=5,
            response=RiskResponse.ACCEPT,
            owner="Tester",
        ).exposure()
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid probability was not rejected.")

    print("All validation tests passed.")


run_validation_tests()


# =============================================================================
# 53. PRACTICAL INITIATION WORKFLOW
# =============================================================================

def practical_initiation_workflow() -> None:
    """Print a practical sequence that can be used in real project work."""

    print("\n56. PRACTICAL PROJECT INITIATION WORKFLOW")

    workflow = [
        "1. Identify a business problem, opportunity, requirement, or strategic need.",
        "2. Describe the current state and business impact.",
        "3. Investigate the problem without prematurely committing to a solution.",
        "4. Define the desired outcome and measurable objective.",
        "5. Identify the business sponsor and business owner.",
        "6. Identify major stakeholders and affected groups.",
        "7. Explore solution alternatives at an appropriate level.",
        "8. Perform high-level feasibility analysis.",
        "9. Develop a business case where investment justification is required.",
        "10. Define high-level scope and explicit boundaries.",
        "11. Identify assumptions, constraints, dependencies, and major risks.",
        "12. Estimate high-level cost, duration, and resource needs.",
        "13. Define measurable success and acceptance criteria.",
        "14. Establish governance and decision rights.",
        "15. Prepare the project charter or equivalent authorization document.",
        "16. Review the initiation package with the appropriate decision authority.",
        "17. Approve, reject, defer, or request revision.",
        "18. Once authorized, transition into detailed planning or iterative product discovery.",
    ]

    for item in workflow:
        print(item)


practical_initiation_workflow()


# =============================================================================
# 54. INITIATION QUESTIONS FOR DIFFERENT PROJECT TYPES
# =============================================================================

def project_type_questions() -> None:
    """Show how initiation questions change by project context."""

    contexts = {
        "Technology implementation": [
            "What systems must integrate?",
            "What security and architecture constraints exist?",
            "What data must be migrated?",
            "What operational support is required?",
        ],
        "Regulatory project": [
            "What regulation or obligation creates the need?",
            "What deadline applies?",
            "What evidence of compliance is required?",
            "What happens if the requirement is not met?",
        ],
        "Product development": [
            "Who is the target customer?",
            "What customer problem is being solved?",
            "What evidence supports the problem?",
            "What is the smallest valuable product?",
        ],
        "Infrastructure project": [
            "What capacity or reliability problem exists?",
            "What physical or technical dependencies exist?",
            "What downtime is acceptable?",
            "What environmental, safety, or regulatory constraints apply?",
        ],
        "Organizational change": [
            "What behavior or process must change?",
            "Who is affected?",
            "What adoption barriers exist?",
            "How will benefits be measured?",
        ],
    }

    print("\n57. INITIATION QUESTIONS BY PROJECT TYPE")

    for context, questions in contexts.items():
        print(f"\n{context}:")
        for question in questions:
            print(f"- {question}")


project_type_questions()


# =============================================================================
# 55. REAL-WORLD INITIATION CASE
# =============================================================================

def complete_real_world_case() -> None:
    """
    A compact end-to-end case study represented through executable data.

    Scenario:
    A financial-services organization wants to reduce customer onboarding time.
    """

    print("\n58. REAL-WORLD CASE: DIGITAL CUSTOMER ONBOARDING")

    case = {
        "Business problem":
            "New customers currently require multiple manual verification steps.",
        "Current performance":
            "Average onboarding time is five business days.",
        "Business impact":
            "Customer drop-off is high and operations teams spend substantial time on manual work.",
        "Desired outcome":
            "Reduce onboarding time while maintaining required controls.",
        "Potential solution":
            "Digitize and integrate onboarding workflows.",
        "Primary sponsor":
            "Chief Operations Officer",
        "Business owner":
            "Head of Customer Operations",
        "Target":
            "Reduce average onboarding time from five days to two days.",
        "Major risks":
            [
                "Regulatory interpretation",
                "Identity-data quality",
                "Integration complexity",
                "User adoption",
            ],
        "Key success measures":
            [
                "Average onboarding time",
                "Completion rate",
                "Error rate",
                "Customer satisfaction",
                "Control effectiveness",
            ],
    }

    for key, value in case.items():
        print(f"\n{key}:")
        if isinstance(value, list):
            for item in value:
                print(f"- {item}")
        else:
            print(value)


complete_real_world_case()


# =============================================================================
# 56. FINAL INTEGRATED MODEL
# =============================================================================

@dataclass
class IntegratedInitiationModel:
    """A consolidated representation of a project initiation package."""

    charter: ProjectCharter
    feasibility: FeasibilityAssessment
    business_case: BusinessCase
    stakeholders: List[Stakeholder]
    risks: List[Risk]
    dependencies: List[Dependency]
    requirements: List[HighLevelRequirement]

    def report(self) -> None:
        print("\n59. INTEGRATED INITIATION REPORT")
        print("=" * 80)

        print("\nPROJECT")
        print(self.charter.project_name)

        print("\nBUSINESS NEED")
        print(self.charter.business_need)

        print("\nOBJECTIVE")
        print(self.charter.objective)

        print("\nAUTHORIZATION")
        print(self.charter.approval_status)

        print("\nBUDGET")
        print(f"${self.charter.estimated_budget:,.2f}")

        print("\nDURATION")
        print(f"{self.charter.estimated_duration_months:.1f} months")

        print("\nFEASIBILITY")
        print(f"{self.feasibility.overall_score():.2f}/10")
        print(self.feasibility.decision())

        print("\nBUSINESS CASE")
        print(f"Simple ROI: {self.business_case.simple_roi():.1%}")
        print(
            f"Payback: "
            f"{self.business_case.payback_years():.2f} years"
            if self.business_case.payback_years() is not None
            else "Payback: Not achieved"
        )

        print("\nSTAKEHOLDERS")
        for stakeholder in self.stakeholders:
            print(
                f"- {stakeholder.name}: "
                f"{stakeholder.classify()}"
            )

        print("\nMAJOR RISKS")
        for risk in self.risks:
            print(
                f"- {risk.risk_id}: {risk.description} "
                f"(exposure={risk.exposure():.2f})"
            )

        print("\nDEPENDENCIES")
        for dependency in self.dependencies:
            print(
                f"- {dependency.predecessor} -> {dependency.successor}"
            )

        print("\nHIGH-LEVEL REQUIREMENTS")
        for requirement in self.requirements:
            print(
                f"- {requirement.requirement_id}: "
                f"{requirement.description}"
            )


integrated_model = IntegratedInitiationModel(
    charter=charter,
    feasibility=feasibility,
    business_case=business_case,
    stakeholders=stakeholders,
    risks=risks,
    dependencies=dependencies,
    requirements=requirements,
)

integrated_model.report()


# =============================================================================
# 57. KEY PRINCIPLES AS EXECUTABLE DATA
# =============================================================================

def key_principles() -> None:
    """
    The principles below capture important initiation disciplines in compact
    executable form so that the script can also function as a revision file.
    """

    principles = [
        (
            "Start with the need",
            "Define the business problem or opportunity before selecting a solution.",
        ),
        (
            "Define value",
            "Connect deliverables to outcomes and measurable benefits.",
        ),
        (
            "Authorize explicitly",
            "A project should have an identifiable decision authority.",
        ),
        (
            "Keep early estimates honest",
            "Early estimates contain uncertainty and should be treated accordingly.",
        ),
        (
            "Set boundaries",
            "High-level scope and out-of-scope areas reduce ambiguity.",
        ),
        (
            "Identify stakeholders early",
            "People affected by the project can influence feasibility and adoption.",
        ),
        (
            "Surface uncertainty",
            "Risks, assumptions, dependencies, and constraints should be visible early.",
        ),
        (
            "Plan security early",
            "Security and privacy can affect architecture, cost, schedule, and feasibility.",
        ),
        (
            "Define success",
            "Delivery of outputs alone does not guarantee business success.",
        ),
        (
            "Match governance to complexity",
            "Large, risky, regulated, or strategic projects generally need stronger governance.",
        ),
        (
            "Do not confuse initiation with detailed planning",
            "Initiation establishes authorization and direction; planning determines detailed execution.",
        ),
    ]

    print("\n60. KEY PROJECT INITIATION PRINCIPLES")

    for principle, explanation in principles:
        print(f"\n{principle}:")
        print(f"  {explanation}")


key_principles()


# =============================================================================
# 58. SCRIPT EXECUTION CHECK
# =============================================================================

def execution_check() -> None:
    """
    Final executable integrity check.

    This confirms that the major components of the study script have been
    constructed successfully.
    """
    required_objects = [
        ProjectIdea,
        ProjectProposal,
        FeasibilityAssessment,
        Stakeholder,
        Risk,
        ProjectCharter,
        BusinessCase,
        ProjectInitiationSimulation,
        IntegratedInitiationModel,
    ]

    assert all(callable(item) for item in required_objects)
    assert charter.approval_status == "Authorized"
    assert feasibility.overall_score() > 0
    assert business_case.investment > 0
    assert len(stakeholders) > 0
    assert len(risks) > 0

    print("\n61. EXECUTION CHECK")
    print("Project initiation study script executed successfully.")
    print("Core models, calculations, validation rules, and examples are operational.")


execution_check()


# =============================================================================
# 59. END
# =============================================================================

print("\n" + "=" * 80)
print("END OF PROJECT INITIATION STUDY SCRIPT")
print("=" * 80)
