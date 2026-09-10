"""
PROJECT LIFE CYCLE
==================

A comprehensive, self-contained Python study script covering the main stages
of a project life cycle:

1. Initiation
2. Planning
3. Execution
4. Monitoring and Controlling
5. Closing

The script also demonstrates:
- Project terminology and roles
- Project charter
- Stakeholders
- SMART objectives
- Scope and requirements
- Work Breakdown Structure (WBS)
- Scheduling and dependencies
- Critical Path Method (CPM)
- Milestones
- Resource planning
- Cost estimation and budgeting
- Risk management
- Quality management
- Communication planning
- Procurement concepts
- Change control
- Earned Value Management (EVM)
- Status reporting
- Issue management
- Project governance
- Agile, Waterfall, and hybrid life cycles
- Project closure and lessons learned
- Project performance analysis
- A complete end-to-end project simulation

This file uses only Python's standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from math import ceil
from typing import Dict, List, Optional, Tuple
import statistics


# ============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# ============================================================================

class ProjectStatus(Enum):
    """Common high-level project states."""
    PROPOSED = "Proposed"
    INITIATED = "Initiated"
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class RiskStatus(Enum):
    """Lifecycle state of a project risk."""
    IDENTIFIED = "Identified"
    MITIGATED = "Mitigated"
    ACCEPTED = "Accepted"
    CLOSED = "Closed"


class ChangeStatus(Enum):
    """Lifecycle state of a change request."""
    REQUESTED = "Requested"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IMPLEMENTED = "Implemented"


@dataclass
class Project:
    """
    Represents a project at a basic level.

    A project is temporary work undertaken to create a unique product,
    service, or result. Temporary means that the project has a defined
    beginning and end.
    """
    name: str
    sponsor: str
    project_manager: str
    objective: str
    start_date: date
    target_end_date: date
    budget: float
    status: ProjectStatus = ProjectStatus.PROPOSED

    def duration_days(self) -> int:
        """Return planned calendar duration."""
        return (self.target_end_date - self.start_date).days + 1

    def display(self) -> None:
        print(f"Project: {self.name}")
        print(f"Sponsor: {self.sponsor}")
        print(f"Project Manager: {self.project_manager}")
        print(f"Objective: {self.objective}")
        print(f"Start: {self.start_date}")
        print(f"Target End: {self.target_end_date}")
        print(f"Duration: {self.duration_days()} days")
        print(f"Budget: ₹{self.budget:,.2f}")
        print(f"Status: {self.status.value}")


# ============================================================================
# 2. INITIATION STAGE
# ============================================================================

"""
INITIATION

Initiation determines whether the project should formally exist.

Typical initiation activities include:
- Identifying the business problem or opportunity
- Defining a high-level objective
- Identifying the sponsor
- Identifying major stakeholders
- Performing feasibility analysis
- Defining high-level scope
- Identifying assumptions and constraints
- Creating the project charter
- Obtaining authorization

The main question is:

    "Should this project be authorized?"

The project charter is an important initiation artifact. It formally
authorizes the project and gives the project manager authority to coordinate
project work within the organization's governance structure.
"""


@dataclass
class ProjectCharter:
    """A simplified project charter."""

    project_name: str
    business_problem: str
    business_case: str
    objective: str
    high_level_scope: List[str]
    exclusions: List[str]
    sponsor: str
    project_manager: str
    assumptions: List[str]
    constraints: List[str]
    success_criteria: List[str]

    def display(self) -> None:
        print("\nPROJECT CHARTER")
        print("=" * 70)
        print(f"Project: {self.project_name}")
        print(f"Business Problem: {self.business_problem}")
        print(f"Business Case: {self.business_case}")
        print(f"Objective: {self.objective}")
        print(f"Sponsor: {self.sponsor}")
        print(f"Project Manager: {self.project_manager}")

        print("\nHigh-Level Scope:")
        for item in self.high_level_scope:
            print(f"  - {item}")

        print("\nExclusions:")
        for item in self.exclusions:
            print(f"  - {item}")

        print("\nAssumptions:")
        for item in self.assumptions:
            print(f"  - {item}")

        print("\nConstraints:")
        for item in self.constraints:
            print(f"  - {item}")

        print("\nSuccess Criteria:")
        for item in self.success_criteria:
            print(f"  - {item}")


def evaluate_feasibility(
    technical_score: float,
    financial_score: float,
    operational_score: float,
    legal_score: float,
) -> Dict[str, float]:
    """
    Perform a simple weighted feasibility assessment.

    Scores should be between 0 and 100.
    """

    scores = {
        "Technical": technical_score,
        "Financial": financial_score,
        "Operational": operational_score,
        "Legal": legal_score,
    }

    for name, score in scores.items():
        if not 0 <= score <= 100:
            raise ValueError(f"{name} feasibility score must be between 0 and 100.")

    weights = {
        "Technical": 0.30,
        "Financial": 0.30,
        "Operational": 0.20,
        "Legal": 0.20,
    }

    weighted_score = sum(scores[name] * weights[name] for name in scores)
    scores["Weighted Total"] = weighted_score
    scores["Recommended"] = weighted_score >= 70

    return scores


def smart_objective(
    specific: str,
    measurable: str,
    achievable: str,
    relevant: str,
    time_bound: str,
) -> str:
    """
    Construct a SMART objective.

    SMART:
    S = Specific
    M = Measurable
    A = Achievable
    R = Relevant
    T = Time-bound
    """
    return (
        f"Specific: {specific}\n"
        f"Measurable: {measurable}\n"
        f"Achievable: {achievable}\n"
        f"Relevant: {relevant}\n"
        f"Time-bound: {time_bound}"
    )


# ============================================================================
# 3. STAKEHOLDER MANAGEMENT
# ============================================================================

"""
STAKEHOLDERS

A stakeholder is a person, group, or organization that can affect the
project, be affected by the project, or perceive itself as affected.

Examples:
- Sponsor
- Customer
- End user
- Project manager
- Project team
- Functional manager
- Supplier
- Regulator
- Senior management
- Operations team

Stakeholder management is not simply communication. It includes identifying
stakeholders, understanding their interests and influence, assessing their
engagement, and planning appropriate interactions.
"""


@dataclass
class Stakeholder:
    name: str
    role: str
    influence: int
    interest: int
    engagement: str = "Unknown"

    def classify_power_interest(self) -> str:
        """Classify stakeholder using a basic power-interest matrix."""
        if self.influence >= 7 and self.interest >= 7:
            return "Manage closely"
        if self.influence >= 7 and self.interest < 7:
            return "Keep satisfied"
        if self.influence < 7 and self.interest >= 7:
            return "Keep informed"
        return "Monitor"


def assess_stakeholder(stakeholder: Stakeholder) -> None:
    if not 1 <= stakeholder.influence <= 10:
        raise ValueError("Influence must be from 1 to 10.")
    if not 1 <= stakeholder.interest <= 10:
        raise ValueError("Interest must be from 1 to 10.")

    print(
        f"{stakeholder.name}: {stakeholder.role} | "
        f"Influence={stakeholder.influence}, "
        f"Interest={stakeholder.interest} | "
        f"Strategy={stakeholder.classify_power_interest()}"
    )


# ============================================================================
# 4. PLANNING STAGE: SCOPE
# ============================================================================

"""
PLANNING

Planning converts the approved project idea into a structured execution plan.

Important planning areas include:
- Scope
- Requirements
- Schedule
- Cost
- Resources
- Quality
- Risk
- Communications
- Procurement
- Stakeholder engagement
- Change management
- Governance

The central question is:

    "How will the project be delivered?"

SCOPE

Project scope defines the boundaries of the project.

Poor scope definition can lead to scope creep, where uncontrolled changes
gradually expand project work.

A useful distinction:

Product scope:
    Features and characteristics of the product, service, or result.

Project scope:
    Work required to produce that product, service, or result.
"""


@dataclass
class Requirement:
    requirement_id: str
    description: str
    priority: str
    acceptance_criteria: str
    status: str = "Not Started"


@dataclass
class ScopeBaseline:
    in_scope: List[str]
    out_of_scope: List[str]
    assumptions: List[str]
    constraints: List[str]

    def display(self) -> None:
        print("\nSCOPE BASELINE")
        print("=" * 70)

        print("In Scope:")
        for item in self.in_scope:
            print(f"  - {item}")

        print("Out of Scope:")
        for item in self.out_of_scope:
            print(f"  - {item}")

        print("Assumptions:")
        for item in self.assumptions:
            print(f"  - {item}")

        print("Constraints:")
        for item in self.constraints:
            print(f"  - {item}")


def validate_requirement(requirement: Requirement) -> bool:
    """Basic requirement quality checks."""
    if not requirement.requirement_id.strip():
        return False

    if not requirement.description.strip():
        return False

    valid_priorities = {"Low", "Medium", "High", "Critical"}
    if requirement.priority not in valid_priorities:
        return False

    if not requirement.acceptance_criteria.strip():
        return False

    return True


# ============================================================================
# 5. WORK BREAKDOWN STRUCTURE
# ============================================================================

"""
WORK BREAKDOWN STRUCTURE (WBS)

A WBS decomposes project scope into progressively smaller components.

A typical hierarchy is:

Project
    ├── Deliverable
    │      ├── Work Package
    │      └── Work Package
    └── Deliverable
           ├── Work Package
           └── Work Package

The WBS focuses on WHAT work is required rather than HOW individual people
will perform every task.

A work package is a manageable unit of work that can be estimated,
scheduled, assigned, monitored, and controlled.
"""


@dataclass
class WorkPackage:
    code: str
    name: str
    deliverable: str
    estimated_hours: float
    owner: str

    def __post_init__(self) -> None:
        if self.estimated_hours < 0:
            raise ValueError("Estimated hours cannot be negative.")


def calculate_total_work(packages: List[WorkPackage]) -> float:
    return sum(package.estimated_hours for package in packages)


# ============================================================================
# 6. SCHEDULING AND DEPENDENCIES
# ============================================================================

"""
SCHEDULE MANAGEMENT

A project schedule translates work into a time-based plan.

Important concepts:

Task:
    A unit of project work.

Duration:
    Amount of working or calendar time required.

Dependency:
    A logical relationship between activities.

Milestone:
    A significant point or event with zero duration in a schedule.

Common dependency types:

Finish-to-Start (FS):
    Task B cannot start until Task A finishes.

Start-to-Start (SS):
    Task B cannot start until Task A starts.

Finish-to-Finish (FF):
    Task B cannot finish until Task A finishes.

Start-to-Finish (SF):
    Task B cannot finish until Task A starts.

FS is the most commonly used dependency.

The Critical Path Method identifies the longest sequence of dependent tasks
that determines the shortest possible project duration.
"""


@dataclass
class Task:
    task_id: str
    name: str
    duration: int
    predecessors: List[str] = field(default_factory=list)
    cost: float = 0.0
    resource: str = ""
    completed: bool = False

    early_start: int = 0
    early_finish: int = 0
    late_start: int = 0
    late_finish: int = 0
    slack: int = 0

    def __post_init__(self) -> None:
        if self.duration < 0:
            raise ValueError("Task duration cannot be negative.")
        if self.cost < 0:
            raise ValueError("Task cost cannot be negative.")


def validate_task_dependencies(tasks: List[Task]) -> None:
    """
    Detect missing predecessors and simple circular dependencies.

    This is intentionally implemented without third-party libraries.
    """

    task_ids = {task.task_id for task in tasks}

    for task in tasks:
        for predecessor in task.predecessors:
            if predecessor not in task_ids:
                raise ValueError(
                    f"Task {task.task_id} references missing predecessor "
                    f"{predecessor}."
                )

    graph = {task.task_id: task.predecessors for task in tasks}
    visiting = set()
    visited = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise ValueError(f"Circular dependency detected involving {task_id}.")
        if task_id in visited:
            return

        visiting.add(task_id)

        for predecessor in graph[task_id]:
            visit(predecessor)

        visiting.remove(task_id)
        visited.add(task_id)

    for task in graph:
        visit(task)


def topological_order(tasks: List[Task]) -> List[str]:
    """Return tasks in dependency order."""
    validate_task_dependencies(tasks)

    task_map = {task.task_id: task for task in tasks}
    remaining = {task.task_id: set(task.predecessors) for task in tasks}
    ordered = []

    while remaining:
        available = sorted(
            task_id for task_id, dependencies in remaining.items()
            if not dependencies
        )

        if not available:
            raise ValueError("Unable to create dependency order.")

        for task_id in available:
            ordered.append(task_id)
            del remaining[task_id]

        for dependencies in remaining.values():
            dependencies.difference_update(available)

    return ordered


def calculate_critical_path(tasks: List[Task]) -> Tuple[int, List[Task]]:
    """
    Calculate project duration and critical path using CPM.

    For each task:
        Early Start (ES) = maximum Early Finish of predecessors
        Early Finish (EF) = ES + Duration

    Backward pass:
        Late Finish (LF) = minimum Late Start of successors
        Late Start (LS) = LF - Duration

    Slack:
        Slack = LS - ES

    Tasks with zero slack belong to a critical path.
    """

    validate_task_dependencies(tasks)

    task_map = {task.task_id: task for task in tasks}
    order = topological_order(tasks)

    # Forward pass.
    for task_id in order:
        task = task_map[task_id]

        if task.predecessors:
            task.early_start = max(
                task_map[p].early_finish for p in task.predecessors
            )
        else:
            task.early_start = 0

        task.early_finish = task.early_start + task.duration

    project_duration = max(task.early_finish for task in tasks) if tasks else 0

    successors: Dict[str, List[str]] = {task.task_id: [] for task in tasks}

    for task in tasks:
        for predecessor in task.predecessors:
            successors[predecessor].append(task.task_id)

    # Backward pass.
    for task_id in reversed(order):
        task = task_map[task_id]

        if successors[task_id]:
            task.late_finish = min(
                task_map[successor].late_start
                for successor in successors[task_id]
            )
        else:
            task.late_finish = project_duration

        task.late_start = task.late_finish - task.duration
        task.slack = task.late_start - task.early_start

    critical_tasks = [
        task for task in tasks
        if task.slack == 0
    ]

    return project_duration, critical_tasks


def print_schedule(tasks: List[Task]) -> None:
    print("\nPROJECT SCHEDULE")
    print("=" * 90)
    print(
        f"{'ID':<6}{'Task':<28}{'Dur.':<8}"
        f"{'ES':<6}{'EF':<6}{'LS':<6}{'LF':<6}{'Slack':<8}"
    )

    for task in sorted(tasks, key=lambda item: item.early_start):
        print(
            f"{task.task_id:<6}"
            f"{task.name[:27]:<28}"
            f"{task.duration:<8}"
            f"{task.early_start:<6}"
            f"{task.early_finish:<6}"
            f"{task.late_start:<6}"
            f"{task.late_finish:<6}"
            f"{task.slack:<8}"
        )


# ============================================================================
# 7. MILESTONES
# ============================================================================

@dataclass
class Milestone:
    name: str
    target_day: int
    achieved: bool = False

    def status(self) -> str:
        return "Achieved" if self.achieved else "Pending"


def print_milestones(milestones: List[Milestone]) -> None:
    print("\nMILESTONES")
    print("=" * 60)

    for milestone in milestones:
        print(
            f"Day {milestone.target_day:>3} | "
            f"{milestone.name:<35} | "
            f"{milestone.status()}"
        )


# ============================================================================
# 8. RESOURCE MANAGEMENT
# ============================================================================

"""
RESOURCE MANAGEMENT

Resources can include:
- People
- Equipment
- Facilities
- Materials
- Technology
- Money
- External suppliers

A resource plan identifies what is required, when it is required, and who
is responsible.

Resource constraints can cause schedule delays even when the technical
dependencies are correct.
"""


@dataclass
class Resource:
    name: str
    resource_type: str
    capacity_per_day: float
    cost_per_unit: float

    def daily_cost(self) -> float:
        return self.capacity_per_day * self.cost_per_unit


def calculate_resource_cost(resource: Resource, days: int) -> float:
    if days < 0:
        raise ValueError("Days cannot be negative.")
    return resource.daily_cost() * days


# ============================================================================
# 9. COST MANAGEMENT
# ============================================================================

"""
COST MANAGEMENT

Common cost concepts:

Estimate:
    Forecast of expected project cost.

Budget:
    Authorized amount allocated to the project.

Contingency reserve:
    Reserve for known-unknown risks or expected uncertainty, depending on
    the organization's financial governance.

Cost baseline:
    Time-phased approved budget used for performance comparison.

Actual Cost:
    Amount actually incurred.

Cost variance:
    Difference between planned and actual cost or, in EVM, between earned
    value and actual cost.
"""


@dataclass
class CostItem:
    name: str
    quantity: float
    unit_cost: float

    def total(self) -> float:
        if self.quantity < 0 or self.unit_cost < 0:
            raise ValueError("Quantity and unit cost cannot be negative.")
        return self.quantity * self.unit_cost


def calculate_budget(items: List[CostItem], contingency_rate: float = 0.0) -> Dict[str, float]:
    """
    Calculate base budget and contingency.

    Example:
        Base = ₹100,000
        Contingency = 10%
        Total = ₹110,000
    """
    if contingency_rate < 0:
        raise ValueError("Contingency rate cannot be negative.")

    base_cost = sum(item.total() for item in items)
    contingency = base_cost * contingency_rate
    total = base_cost + contingency

    return {
        "base_cost": base_cost,
        "contingency": contingency,
        "total_budget": total,
    }


# ============================================================================
# 10. RISK MANAGEMENT
# ============================================================================

"""
RISK MANAGEMENT

A risk is an uncertain event or condition that, if it occurs, can have a
positive or negative effect on project objectives.

Negative risk is commonly called a threat.
Positive risk is commonly called an opportunity.

Basic risk management cycle:

1. Identify
2. Analyze
3. Plan responses
4. Implement responses
5. Monitor

Probability-impact analysis is commonly used for prioritization.

Expected Monetary Value (EMV):

    EMV = Probability × Impact

For threats, the impact is often represented as a potential loss.
For opportunities, it may represent potential benefit.

Common threat response strategies:
- Avoid
- Mitigate
- Transfer
- Accept

Common opportunity response strategies:
- Exploit
- Enhance
- Share
- Accept
"""


@dataclass
class Risk:
    risk_id: str
    description: str
    probability: float
    impact: float
    response: str
    owner: str
    status: RiskStatus = RiskStatus.IDENTIFIED

    def __post_init__(self) -> None:
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1.")
        if self.impact < 0:
            raise ValueError("Impact cannot be negative.")

    def risk_score(self) -> float:
        return self.probability * self.impact

    def emv(self) -> float:
        return self.risk_score()


def prioritize_risks(risks: List[Risk]) -> List[Risk]:
    return sorted(risks, key=lambda risk: risk.risk_score(), reverse=True)


def risk_level(score: float) -> str:
    if score >= 50:
        return "High"
    if score >= 20:
        return "Medium"
    return "Low"


# ============================================================================
# 11. QUALITY MANAGEMENT
# ============================================================================

"""
QUALITY MANAGEMENT

Quality concerns whether the project deliverable conforms to relevant
requirements and is fit for its intended purpose.

Important distinctions:

Quality assurance:
    Process-oriented activities intended to provide confidence that
    appropriate processes are being followed.

Quality control:
    Product/output-oriented activities involving inspection, measurement,
    testing, and defect identification.

Quality is not identical to luxury or premium features. A product can have
many features and still fail to meet its required quality criteria.
"""


@dataclass
class QualityCheck:
    name: str
    target: float
    actual: float
    tolerance: float

    def passed(self) -> bool:
        return abs(self.actual - self.target) <= self.tolerance


def run_quality_checks(checks: List[QualityCheck]) -> Dict[str, int]:
    passed = sum(check.passed() for check in checks)
    failed = len(checks) - passed

    return {
        "total": len(checks),
        "passed": passed,
        "failed": failed,
    }


# ============================================================================
# 12. COMMUNICATION MANAGEMENT
# ============================================================================

"""
COMMUNICATION MANAGEMENT

Different stakeholders need different information.

A communication plan can specify:

- What information is needed
- Who receives it
- Who provides it
- When it is provided
- How it is delivered
- How detailed it should be

A senior executive may need a concise status dashboard while a developer
may need detailed technical requirements.
"""


@dataclass
class CommunicationPlan:
    stakeholder: str
    information: str
    frequency: str
    channel: str
    owner: str

    def display(self) -> None:
        print(
            f"{self.stakeholder:<20} | "
            f"{self.information:<30} | "
            f"{self.frequency:<15} | "
            f"{self.channel:<15} | "
            f"{self.owner}"
        )


# ============================================================================
# 13. PROCUREMENT
# ============================================================================

"""
PROCUREMENT

Projects may acquire products, services, or materials from external parties.

Important procurement considerations include:
- Requirement definition
- Supplier identification
- Evaluation criteria
- Contract type
- Price
- Quality
- Delivery
- Risk allocation
- Legal requirements
- Supplier performance

Simplified contract categories:

Fixed-price:
    Price is agreed for a defined scope.

Cost-reimbursable:
    Buyer pays allowable costs plus an agreed fee or incentive structure.

Time-and-materials:
    Payment is based on labor time and materials used, usually with
    agreed rates and controls.

Contract choice affects risk allocation between buyer and seller.
"""


@dataclass
class SupplierQuote:
    supplier: str
    price: float
    quality_score: float
    delivery_score: float

    def weighted_score(
        self,
        price_weight: float = 0.40,
        quality_weight: float = 0.35,
        delivery_weight: float = 0.25,
    ) -> float:
        if self.price <= 0:
            raise ValueError("Supplier price must be positive.")

        # Normalize price so lower price receives a better price score.
        # The actual normalization is performed across all suppliers.
        return (
            quality_weight * self.quality_score
            + delivery_weight * self.delivery_score
            + price_weight * (1 / self.price)
        )


def evaluate_suppliers(quotes: List[SupplierQuote]) -> List[Tuple[str, float]]:
    """
    Rank suppliers using normalized price plus quality and delivery.

    This is an educational scoring model, not a universal procurement rule.
    """
    if not quotes:
        return []

    minimum_price = min(quote.price for quote in quotes)

    results = []

    for quote in quotes:
        price_score = (minimum_price / quote.price) * 100

        score = (
            0.40 * price_score
            + 0.35 * quote.quality_score
            + 0.25 * quote.delivery_score
        )

        results.append((quote.supplier, score))

    return sorted(results, key=lambda item: item[1], reverse=True)


# ============================================================================
# 14. EXECUTION STAGE
# ============================================================================

"""
EXECUTION

Execution is the stage where the project plan is converted into actual work.

Typical execution activities include:
- Assigning and coordinating resources
- Performing project tasks
- Producing deliverables
- Managing suppliers
- Managing stakeholders
- Communicating status
- Performing quality activities
- Resolving issues
- Implementing approved changes

The project manager is responsible for coordinating the project, but
individual technical work may be performed by specialists.
"""


@dataclass
class TaskExecution:
    task_id: str
    planned_hours: float
    actual_hours: float
    completion_percentage: float

    def efficiency(self) -> float:
        if self.actual_hours == 0:
            return 0.0
        return self.planned_hours / self.actual_hours


def update_task_progress(
    execution: TaskExecution,
    additional_hours: float,
    additional_completion: float,
) -> None:
    if additional_hours < 0:
        raise ValueError("Additional hours cannot be negative.")

    new_completion = execution.completion_percentage + additional_completion

    if not 0 <= new_completion <= 100:
        raise ValueError("Completion percentage must remain between 0 and 100.")

    execution.actual_hours += additional_hours
    execution.completion_percentage = new_completion


# ============================================================================
# 15. ISSUE MANAGEMENT
# ============================================================================

"""
ISSUE MANAGEMENT

A risk is uncertain.
An issue is something that has already happened or is currently happening.

Example:

Risk:
    "The supplier may deliver late."

Issue:
    "The supplier has delivered two days late."

Issues should generally have:
- Description
- Owner
- Priority
- Due date
- Resolution
- Status
"""


@dataclass
class Issue:
    issue_id: str
    description: str
    priority: str
    owner: str
    due_date: date
    status: str = "Open"
    resolution: str = ""

    def close(self, resolution: str) -> None:
        if not resolution.strip():
            raise ValueError("A resolution description is required.")
        self.resolution = resolution
        self.status = "Closed"


# ============================================================================
# 16. CHANGE CONTROL
# ============================================================================

"""
CHANGE CONTROL

Projects frequently receive requests to modify:
- Scope
- Requirements
- Schedule
- Cost
- Quality
- Resources
- Deliverables

A controlled change process prevents informal scope expansion.

Typical change-control sequence:

1. Submit change request
2. Record the request
3. Analyze impact
4. Review alternatives
5. Obtain approval or rejection
6. Update baselines/plans if approved
7. Implement
8. Verify

A change request should not automatically be treated as approved work.
"""


@dataclass
class ChangeRequest:
    change_id: str
    description: str
    scope_impact: float
    cost_impact: float
    schedule_impact_days: int
    quality_impact: str
    status: ChangeStatus = ChangeStatus.REQUESTED

    def total_impact(self) -> Dict[str, object]:
        return {
            "scope": self.scope_impact,
            "cost": self.cost_impact,
            "schedule_days": self.schedule_impact_days,
            "quality": self.quality_impact,
        }

    def approve(self) -> None:
        self.status = ChangeStatus.APPROVED

    def reject(self) -> None:
        self.status = ChangeStatus.REJECTED

    def implement(self) -> None:
        if self.status != ChangeStatus.APPROVED:
            raise ValueError("Only approved changes can be implemented.")
        self.status = ChangeStatus.IMPLEMENTED


# ============================================================================
# 17. MONITORING AND CONTROLLING
# ============================================================================

"""
MONITORING AND CONTROLLING

Monitoring means collecting information about project performance.

Controlling means analyzing that information and taking corrective or
preventive action.

The project should be compared against approved baselines.

Typical monitoring areas:
- Scope
- Schedule
- Cost
- Quality
- Risks
- Issues
- Resources
- Stakeholders
- Procurement
- Changes

A project can be:
- On schedule but over budget
- Under budget but behind schedule
- On budget but producing poor quality
- Meeting schedule while scope is uncontrolled

Therefore, monitoring should consider multiple dimensions.
"""


@dataclass
class ProjectMetrics:
    planned_value: float
    earned_value: float
    actual_cost: float

    def schedule_variance(self) -> float:
        """SV = EV - PV."""
        return self.earned_value - self.planned_value

    def cost_variance(self) -> float:
        """CV = EV - AC."""
        return self.earned_value - self.actual_cost

    def schedule_performance_index(self) -> float:
        """SPI = EV / PV."""
        if self.planned_value == 0:
            return 0.0
        return self.earned_value / self.planned_value

    def cost_performance_index(self) -> float:
        """CPI = EV / AC."""
        if self.actual_cost == 0:
            return 0.0
        return self.earned_value / self.actual_cost

    def report(self) -> None:
        spi = self.schedule_performance_index()
        cpi = self.cost_performance_index()

        print("\nEARNED VALUE MANAGEMENT")
        print("=" * 60)
        print(f"Planned Value (PV): ₹{self.planned_value:,.2f}")
        print(f"Earned Value (EV):  ₹{self.earned_value:,.2f}")
        print(f"Actual Cost (AC):   ₹{self.actual_cost:,.2f}")
        print(f"Schedule Variance:  ₹{self.schedule_variance():,.2f}")
        print(f"Cost Variance:      ₹{self.cost_variance():,.2f}")
        print(f"SPI:                {spi:.3f}")
        print(f"CPI:                {cpi:.3f}")

        print("\nInterpretation:")
        if spi < 1:
            print("- Schedule performance indicates the project is behind plan.")
        elif spi > 1:
            print("- Schedule performance indicates progress is ahead of plan.")
        else:
            print("- Schedule performance is exactly aligned with plan.")

        if cpi < 1:
            print("- Cost performance indicates the project is spending inefficiently.")
        elif cpi > 1:
            print("- Cost performance indicates favorable cost efficiency.")
        else:
            print("- Cost performance is exactly aligned with earned value.")


def estimate_at_completion(
    budget_at_completion: float,
    actual_cost: float,
    earned_value: float,
) -> Dict[str, float]:
    """
    Calculate common EVM forecasts.

    CPI = EV / AC

    EAC using current cost performance:
        EAC = BAC / CPI

    ETC:
        ETC = EAC - AC

    VAC:
        VAC = BAC - EAC
    """
    if budget_at_completion < 0:
        raise ValueError("BAC cannot be negative.")
    if actual_cost < 0:
        raise ValueError("AC cannot be negative.")
    if earned_value < 0:
        raise ValueError("EV cannot be negative.")
    if earned_value == 0:
        raise ValueError("EV must be greater than zero for CPI forecasting.")

    cpi = earned_value / actual_cost if actual_cost else float("inf")
    eac = budget_at_completion / cpi if cpi else float("inf")
    etc = eac - actual_cost
    vac = budget_at_completion - eac

    return {
        "CPI": cpi,
        "EAC": eac,
        "ETC": etc,
        "VAC": vac,
    }


# ============================================================================
# 18. STATUS REPORTING
# ============================================================================

@dataclass
class StatusReport:
    reporting_period: str
    accomplishments: List[str]
    planned_next_period: List[str]
    risks: List[str]
    issues: List[str]
    decisions_required: List[str]
    overall_status: str

    def display(self) -> None:
        print("\nPROJECT STATUS REPORT")
        print("=" * 70)
        print(f"Reporting Period: {self.reporting_period}")
        print(f"Overall Status: {self.overall_status}")

        sections = [
            ("Accomplishments", self.accomplishments),
            ("Planned Work", self.planned_next_period),
            ("Risks", self.risks),
            ("Issues", self.issues),
            ("Decisions Required", self.decisions_required),
        ]

        for title, items in sections:
            print(f"\n{title}:")
            if items:
                for item in items:
                    print(f"  - {item}")
            else:
                print("  None")


# ============================================================================
# 19. PROJECT GOVERNANCE
# ============================================================================

"""
GOVERNANCE

Project governance establishes decision-making structures, authority,
accountability, escalation paths, and control mechanisms.

Examples:
- Steering committee
- Project sponsor
- Project manager
- Change Control Board
- Product owner
- Functional managers
- Architecture review board
- Quality authority

Governance becomes particularly important when:
- Multiple departments are involved
- The project has significant financial impact
- Regulatory requirements exist
- The project has high organizational risk
- Decisions need executive authority
"""


@dataclass
class GovernanceRole:
    role: str
    responsibilities: List[str]
    authority: str

    def display(self) -> None:
        print(f"\nRole: {self.role}")
        print(f"Authority: {self.authority}")
        print("Responsibilities:")
        for responsibility in self.responsibilities:
            print(f"  - {responsibility}")


# ============================================================================
# 20. CLOSING STAGE
# ============================================================================

"""
CLOSING

Closing formally completes the project or a project phase.

Typical closing activities:
- Obtain final acceptance
- Verify deliverables
- Complete contractual closure
- Release resources
- Archive documentation
- Record lessons learned
- Close financial records
- Transfer ownership to operations
- Confirm unresolved items and ownership
- Communicate closure

Closing is more than stopping work. It is a controlled transition from
temporary project activity to an accepted outcome and organizational record.
"""


@dataclass
class ClosureChecklist:
    final_acceptance: bool = False
    deliverables_verified: bool = False
    contracts_closed: bool = False
    resources_released: bool = False
    documentation_archived: bool = False
    lessons_recorded: bool = False
    operations_handover: bool = False

    def is_complete(self) -> bool:
        return all([
            self.final_acceptance,
            self.deliverables_verified,
            self.contracts_closed,
            self.resources_released,
            self.documentation_archived,
            self.lessons_recorded,
            self.operations_handover,
        ])

    def missing_items(self) -> List[str]:
        mapping = {
            "Final acceptance": self.final_acceptance,
            "Deliverables verified": self.deliverables_verified,
            "Contracts closed": self.contracts_closed,
            "Resources released": self.resources_released,
            "Documentation archived": self.documentation_archived,
            "Lessons recorded": self.lessons_recorded,
            "Operations handover": self.operations_handover,
        }

        return [name for name, complete in mapping.items() if not complete]


@dataclass
class LessonLearned:
    category: str
    observation: str
    impact: str
    recommendation: str


def display_lessons(lessons: List[LessonLearned]) -> None:
    print("\nLESSONS LEARNED")
    print("=" * 80)

    for index, lesson in enumerate(lessons, start=1):
        print(f"\n{index}. {lesson.category}")
        print(f"Observation: {lesson.observation}")
        print(f"Impact: {lesson.impact}")
        print(f"Recommendation: {lesson.recommendation}")


# ============================================================================
# 21. WATERFALL, AGILE, AND HYBRID LIFE CYCLES
# ============================================================================

"""
PROJECT LIFE CYCLE APPROACHES

Waterfall / Predictive:
    Work is generally planned in greater detail upfront, with sequential
    or phase-oriented delivery.

Advantages:
- Strong upfront planning
- Easier baseline comparison
- Useful where requirements are stable
- Useful where regulatory documentation is important

Limitations:
- Changes can be expensive
- Feedback may arrive late
- Uncertainty can make detailed upfront plans unreliable

Agile / Adaptive:
    Work is delivered iteratively or incrementally, with frequent feedback
    and adaptation.

Advantages:
- Frequent feedback
- Better response to changing requirements
- Earlier delivery of usable increments
- High stakeholder interaction

Limitations:
- Requires active stakeholder participation
- Scope may evolve significantly
- Long-term cost and schedule forecasting can be less deterministic

Hybrid:
    Combines predictive and adaptive practices.

Example:
    A regulated financial platform may use predictive governance and
    compliance controls while software development occurs in iterative
    increments.

Life cycle choice should depend on uncertainty, regulatory requirements,
stakeholder needs, product characteristics, organizational capability, and
the cost of change.
"""


class LifecycleApproach(Enum):
    PREDICTIVE = "Predictive"
    ADAPTIVE = "Adaptive"
    HYBRID = "Hybrid"


def compare_lifecycle_approaches() -> None:
    comparison = {
        "Predictive": {
            "planning": "Detailed upfront planning",
            "change": "Controlled and often expensive",
            "delivery": "Usually phase-oriented",
            "best_fit": "Stable requirements",
        },
        "Adaptive": {
            "planning": "Progressive and iterative",
            "change": "Expected and incorporated",
            "delivery": "Frequent increments",
            "best_fit": "High uncertainty",
        },
        "Hybrid": {
            "planning": "Combination",
            "change": "Controlled where necessary, adaptive elsewhere",
            "delivery": "Mixed",
            "best_fit": "Mixed environments",
        },
    }

    print("\nLIFE CYCLE COMPARISON")
    print("=" * 110)

    for approach, characteristics in comparison.items():
        print(f"\n{approach}")
        for key, value in characteristics.items():
            print(f"  {key.title():<12}: {value}")


# ============================================================================
# 22. PHASE GATES
# ============================================================================

"""
PHASE GATES

A phase gate is a formal decision point between phases.

Typical decisions:
- Continue
- Continue with conditions
- Replan
- Pause
- Cancel

Phase gates reduce the chance of continuing to spend resources on a project
that no longer makes business or technical sense.
"""


@dataclass
class PhaseGate:
    phase: str
    criteria: Dict[str, bool]

    def passed(self) -> bool:
        return all(self.criteria.values())

    def display(self) -> None:
        print(f"\nPhase Gate: {self.phase}")
        for criterion, result in self.criteria.items():
            print(f"  {'PASS' if result else 'FAIL'} - {criterion}")
        print(f"Decision: {'Continue' if self.passed() else 'Review Required'}")


# ============================================================================
# 23. PROJECT HEALTH SCORE
# ============================================================================

def calculate_project_health(
    scope_score: float,
    schedule_score: float,
    cost_score: float,
    quality_score: float,
    risk_score: float,
) -> float:
    """
    Produce a simple weighted project-health score.

    This is an educational model. Real organizations define their own
    governance metrics and thresholds.
    """

    scores = [
        scope_score,
        schedule_score,
        cost_score,
        quality_score,
        risk_score,
    ]

    if any(score < 0 or score > 100 for score in scores):
        raise ValueError("All health scores must be between 0 and 100.")

    weights = [0.20, 0.25, 0.20, 0.20, 0.15]

    return sum(score * weight for score, weight in zip(scores, weights))


def health_label(score: float) -> str:
    if score >= 80:
        return "Healthy"
    if score >= 60:
        return "Needs Attention"
    return "At Risk"


# ============================================================================
# 24. PERFORMANCE ANALYSIS
# ============================================================================

def calculate_completion_rate(
    completed_items: int,
    total_items: int,
) -> float:
    if total_items < 0 or completed_items < 0:
        raise ValueError("Item counts cannot be negative.")
    if completed_items > total_items:
        raise ValueError("Completed items cannot exceed total items.")
    if total_items == 0:
        return 0.0

    return (completed_items / total_items) * 100


def calculate_defect_rate(
    defects: int,
    units_inspected: int,
) -> float:
    if defects < 0 or units_inspected < 0:
        raise ValueError("Counts cannot be negative.")
    if defects > units_inspected:
        raise ValueError("Defects cannot exceed inspected units.")
    if units_inspected == 0:
        return 0.0

    return defects / units_inspected


def calculate_schedule_variance_days(
    planned_end: date,
    actual_end: date,
) -> int:
    return (actual_end - planned_end).days


# ============================================================================
# 25. MONTE CARLO-STYLE SIMPLE SCHEDULE SIMULATION
# ============================================================================

"""
ADVANCED CONCEPT: UNCERTAINTY

Real project durations are rarely perfectly deterministic.

A simple simulation can represent uncertainty by sampling task durations.

This example intentionally uses the standard library's random module.
It does not attempt to replace professional project risk simulation tools.
"""


import random


def simulate_duration(
    optimistic: int,
    most_likely: int,
    pessimistic: int,
    simulations: int = 5000,
) -> Dict[str, float]:
    """
    Use a triangular distribution to simulate an uncertain duration.

    The triangular distribution is useful for educational scenarios where
    optimistic, most-likely, and pessimistic estimates are available.
    """
    if not (
        0 <= optimistic <= most_likely <= pessimistic
    ):
        raise ValueError(
            "Duration estimates must satisfy "
            "optimistic <= most_likely <= pessimistic."
        )

    if simulations <= 0:
        raise ValueError("Simulation count must be positive.")

    results = [
        random.triangular(
            optimistic,
            pessimistic,
            most_likely,
        )
        for _ in range(simulations)
    ]

    results.sort()

    return {
        "mean": statistics.mean(results),
        "median": statistics.median(results),
        "p10": results[int(0.10 * len(results))],
        "p50": results[int(0.50 * len(results))],
        "p90": results[int(0.90 * len(results))],
        "minimum": results[0],
        "maximum": results[-1],
    }


# ============================================================================
# 26. ESCALATION AND DECISION MAKING
# ============================================================================

@dataclass
class Decision:
    decision_id: str
    description: str
    owner: str
    deadline: date
    status: str = "Pending"
    outcome: str = ""

    def approve(self, outcome: str) -> None:
        if not outcome.strip():
            raise ValueError("Decision outcome cannot be empty.")
        self.status = "Decided"
        self.outcome = outcome


def should_escalate(
    financial_impact: float,
    schedule_delay_days: int,
    authority_limit: float,
    schedule_tolerance_days: int,
) -> bool:
    """
    A simplified escalation rule.

    Real governance frameworks may use much more complex thresholds.
    """
    return (
        financial_impact > authority_limit
        or schedule_delay_days > schedule_tolerance_days
    )


# ============================================================================
# 27. END-TO-END PROJECT EXAMPLE
# ============================================================================

def build_demo_project() -> Project:
    """Create a realistic example project."""

    return Project(
        name="Customer Analytics Platform",
        sponsor="Chief Business Officer",
        project_manager="Project Manager",
        objective=(
            "Deliver a customer analytics platform that provides reliable "
            "business dashboards and validated customer insights."
        ),
        start_date=date(2026, 1, 5),
        target_end_date=date(2026, 4, 30),
        budget=1_500_000,
        status=ProjectStatus.INITIATED,
    )


def run_initiation_example() -> ProjectCharter:
    print("\n" + "=" * 90)
    print("STAGE 1: INITIATION")
    print("=" * 90)

    project = build_demo_project()
    project.display()

    feasibility = evaluate_feasibility(
        technical_score=82,
        financial_score=78,
        operational_score=74,
        legal_score=90,
    )

    print("\nFEASIBILITY ASSESSMENT")
    for key, value in feasibility.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")

    objective = smart_objective(
        specific="Launch a centralized customer analytics platform",
        measurable="Provide 10 validated dashboards with 95% data-quality compliance",
        achievable="Use approved data sources and existing technical capabilities",
        relevant="Improve management reporting and customer decision-making",
        time_bound="Complete implementation within 16 weeks",
    )

    print("\nSMART OBJECTIVE")
    print(objective)

    charter = ProjectCharter(
        project_name=project.name,
        business_problem=(
            "Business teams depend on fragmented reports and manual data preparation."
        ),
        business_case=(
            "Centralized analytics can reduce reporting effort and improve decision speed."
        ),
        objective=project.objective,
        high_level_scope=[
            "Requirements analysis",
            "Data integration",
            "Analytics platform development",
            "Dashboard development",
            "Testing",
            "User acceptance",
            "Production handover",
        ],
        exclusions=[
            "Replacement of the enterprise ERP system",
            "Major redesign of unrelated business processes",
            "Long-term operational support after handover",
        ],
        sponsor=project.sponsor,
        project_manager=project.project_manager,
        assumptions=[
            "Required data sources will remain accessible",
            "Business users will participate in validation",
            "Required infrastructure will be available",
        ],
        constraints=[
            "Fixed executive target date",
            "Approved budget ceiling",
            "Limited availability of subject-matter experts",
        ],
        success_criteria=[
            "All agreed dashboards delivered",
            "Acceptance criteria satisfied",
            "Data-quality threshold achieved",
            "Business owner accepts final deliverables",
        ],
    )

    charter.display()
    return charter


def run_stakeholder_example() -> None:
    print("\n" + "=" * 90)
    print("STAKEHOLDER ANALYSIS")
    print("=" * 90)

    stakeholders = [
        Stakeholder("Executive Sponsor", "Sponsor", 10, 8),
        Stakeholder("Business Users", "Customer", 7, 10),
        Stakeholder("Technology Lead", "Technical Lead", 8, 9),
        Stakeholder("Finance Team", "Control Function", 7, 5),
        Stakeholder("External Supplier", "Supplier", 5, 7),
        Stakeholder("General Employees", "Indirect User", 3, 4),
    ]

    for stakeholder in stakeholders:
        assess_stakeholder(stakeholder)


def run_scope_and_wbs_example() -> List[WorkPackage]:
    print("\n" + "=" * 90)
    print("STAGE 2: PLANNING - SCOPE AND WBS")
    print("=" * 90)

    scope = ScopeBaseline(
        in_scope=[
            "Business requirements",
            "Data ingestion",
            "Analytics data model",
            "Dashboard development",
            "Testing and acceptance",
            "Production deployment",
        ],
        out_of_scope=[
            "Unrelated legacy-system replacement",
            "Enterprise-wide organizational restructuring",
        ],
        assumptions=[
            "Source data is available",
            "Business stakeholders provide timely feedback",
        ],
        constraints=[
            "Budget ceiling",
            "Target delivery date",
            "Limited specialist capacity",
        ],
    )

    scope.display()

    requirements = [
        Requirement(
            "REQ-001",
            "Users shall be able to view executive sales dashboards.",
            "Critical",
            "Dashboard loads successfully and displays approved metrics.",
        ),
        Requirement(
            "REQ-002",
            "Users shall be able to filter data by business region.",
            "High",
            "Region filter changes displayed metrics correctly.",
        ),
        Requirement(
            "REQ-003",
            "Data refresh shall complete within the agreed processing window.",
            "High",
            "Refresh completes within the defined operational threshold.",
        ),
    ]

    print("\nREQUIREMENT VALIDATION")
    for requirement in requirements:
        print(
            f"{requirement.requirement_id}: "
            f"{'Valid' if validate_requirement(requirement) else 'Invalid'}"
        )

    packages = [
        WorkPackage("1.1", "Requirements Analysis", "Requirements", 80, "Business Analyst"),
        WorkPackage("1.2", "Architecture Design", "Architecture", 60, "Architect"),
        WorkPackage("2.1", "Data Integration", "Data Platform", 180, "Data Engineer"),
        WorkPackage("2.2", "Analytics Model", "Data Platform", 140, "Data Engineer"),
        WorkPackage("3.1", "Dashboard Development", "Analytics", 200, "BI Developer"),
        WorkPackage("3.2", "Testing", "Validated Platform", 120, "QA Team"),
        WorkPackage("3.3", "User Acceptance", "Accepted Platform", 80, "Business Users"),
        WorkPackage("4.1", "Production Handover", "Production System", 60, "Technology Team"),
    ]

    print(f"\nTotal estimated work: {calculate_total_work(packages):,.0f} hours")

    return packages


def run_schedule_example() -> List[Task]:
    print("\n" + "=" * 90)
    print("PLANNING - SCHEDULE AND CRITICAL PATH")
    print("=" * 90)

    tasks = [
        Task("A", "Requirements Analysis", 5, [], 80_000, "Business Analyst"),
        Task("B", "Architecture Design", 4, ["A"], 100_000, "Architect"),
        Task("C", "Data Integration", 10, ["B"], 250_000, "Data Engineer"),
        Task("D", "Analytics Model", 7, ["C"], 180_000, "Data Engineer"),
        Task("E", "Dashboard Development", 8, ["D"], 220_000, "BI Developer"),
        Task("F", "Testing", 5, ["E"], 100_000, "QA Team"),
        Task("G", "User Acceptance", 4, ["F"], 70_000, "Business Users"),
        Task("H", "Production Handover", 3, ["G"], 80_000, "Technology Team"),
        Task("I", "Documentation", 5, ["D"], 50_000, "Technical Writer"),
        Task("J", "Training", 3, ["I"], 40_000, "Training Team"),
        Task("K", "Operational Readiness", 2, ["J", "G"], 50_000, "Operations"),
        Task("L", "Final Closure", 1, ["H", "K"], 20_000, "Project Manager"),
    ]

    duration, critical_tasks = calculate_critical_path(tasks)

    print_schedule(tasks)

    print(f"\nShortest dependency-based project duration: {duration} days")
    print("\nCritical Path:")

    for task in critical_tasks:
        print(f"  {task.task_id} - {task.name}")

    return tasks


def run_resource_and_cost_example() -> None:
    print("\n" + "=" * 90)
    print("PLANNING - RESOURCES AND COST")
    print("=" * 90)

    resources = [
        Resource("Business Analyst", "Human", 8, 1_800),
        Resource("Data Engineer", "Human", 8, 2_500),
        Resource("BI Developer", "Human", 8, 2_200),
        Resource("QA Engineer", "Human", 8, 1_900),
        Resource("Cloud Environment", "Technology", 1, 4_000),
    ]

    for resource in resources:
        print(
            f"{resource.name:<25} | "
            f"Daily Cost: ₹{resource.daily_cost():,.2f} | "
            f"20-day Cost: ₹{calculate_resource_cost(resource, 20):,.2f}"
        )

    cost_items = [
        CostItem("Business Analysis", 1, 120_000),
        CostItem("Architecture", 1, 150_000),
        CostItem("Data Engineering", 1, 350_000),
        CostItem("Application Development", 1, 300_000),
        CostItem("Testing", 1, 150_000),
        CostItem("Infrastructure", 1, 120_000),
        CostItem("Training and Handover", 1, 80_000),
    ]

    budget = calculate_budget(cost_items, contingency_rate=0.10)

    print("\nBUDGET")
    for name, amount in budget.items():
        print(f"{name.replace('_', ' ').title():<20}: ₹{amount:,.2f}")


def run_risk_example() -> None:
    print("\n" + "=" * 90)
    print("PLANNING - RISK MANAGEMENT")
    print("=" * 90)

    risks = [
        Risk(
            "R-001",
            "Critical source data may become unavailable.",
            0.30,
            500_000,
            "Mitigate through backup extraction and dependency monitoring.",
            "Data Lead",
        ),
        Risk(
            "R-002",
            "Business users may provide acceptance feedback late.",
            0.50,
            150_000,
            "Schedule early review sessions and reserve decision windows.",
            "Project Manager",
        ),
        Risk(
            "R-003",
            "Cloud infrastructure costs may exceed estimate.",
            0.25,
            100_000,
            "Set budgets, alerts, and usage controls.",
            "Technology Lead",
        ),
        Risk(
            "R-004",
            "A new regulatory requirement may increase scope.",
            0.15,
            300_000,
            "Monitor regulatory changes and maintain change-control process.",
            "Compliance Lead",
        ),
    ]

    print(
        f"{'ID':<8}{'Risk':<45}{'Score':<15}"
        f"{'Level':<10}{'Response'}"
    )

    for risk in prioritize_risks(risks):
        print(
            f"{risk.risk_id:<8}"
            f"{risk.description[:44]:<45}"
            f"₹{risk.risk_score():,.0f}{'':<6}"
            f"{risk_level(risk.risk_score()):<10}"
            f"{risk.response}"
        )


def run_execution_example() -> None:
    print("\n" + "=" * 90)
    print("STAGE 3: EXECUTION")
    print("=" * 90)

    execution = TaskExecution(
        task_id="T-101",
        planned_hours=100,
        actual_hours=60,
        completion_percentage=65,
    )

    print(
        f"Initial progress: {execution.completion_percentage:.1f}% | "
        f"Actual hours: {execution.actual_hours}"
    )

    update_task_progress(
        execution,
        additional_hours=30,
        additional_completion=25,
    )

    print(
        f"Updated progress: {execution.completion_percentage:.1f}% | "
        f"Actual hours: {execution.actual_hours}"
    )

    print(f"Efficiency ratio: {execution.efficiency():.3f}")


def run_quality_example() -> None:
    print("\n" + "=" * 90)
    print("EXECUTION - QUALITY CONTROL")
    print("=" * 90)

    checks = [
        QualityCheck("Dashboard response time", 2.0, 1.8, 0.5),
        QualityCheck("Data completeness", 99.0, 98.7, 0.5),
        QualityCheck("Calculation accuracy", 100.0, 100.0, 0.0),
        QualityCheck("Accessibility score", 95.0, 91.0, 3.0),
        QualityCheck("Defect count", 0, 2, 0),
    ]

    results = run_quality_checks(checks)

    for check in checks:
        print(
            f"{check.name:<30} | "
            f"Target={check.target:<8} | "
            f"Actual={check.actual:<8} | "
            f"{'PASS' if check.passed() else 'FAIL'}"
        )

    print("\nQuality Result:")
    print(results)


def run_communication_example() -> None:
    print("\n" + "=" * 90)
    print("EXECUTION - COMMUNICATION MANAGEMENT")
    print("=" * 90)

    plans = [
        CommunicationPlan(
            "Executive Sponsor",
            "Overall health, budget, major risks",
            "Weekly",
            "Dashboard",
            "Project Manager",
        ),
        CommunicationPlan(
            "Project Team",
            "Tasks, dependencies, blockers",
            "Daily",
            "Meeting/Board",
            "Project Manager",
        ),
        CommunicationPlan(
            "Business Users",
            "Requirements and acceptance progress",
            "Weekly",
            "Workshop",
            "Business Analyst",
        ),
        CommunicationPlan(
            "Operations",
            "Deployment and readiness",
            "Biweekly",
            "Meeting",
            "Technology Lead",
        ),
    ]

    print(
        f"{'Stakeholder':<20} | "
        f"{'Information':<30} | "
        f"{'Frequency':<15} | "
        f"{'Channel':<15} | "
        f"Owner"
    )
    print("-" * 105)

    for plan in plans:
        plan.display()


def run_procurement_example() -> None:
    print("\n" + "=" * 90)
    print("EXECUTION - PROCUREMENT")
    print("=" * 90)

    quotes = [
        SupplierQuote("Supplier A", 450_000, 88, 92),
        SupplierQuote("Supplier B", 420_000, 82, 86),
        SupplierQuote("Supplier C", 500_000, 95, 94),
    ]

    print("Supplier ranking:")

    for supplier, score in evaluate_suppliers(quotes):
        print(f"{supplier:<15} | Weighted Score: {score:.2f}")


def run_monitoring_example() -> None:
    print("\n" + "=" * 90)
    print("STAGE 4: MONITORING AND CONTROLLING")
    print("=" * 90)

    metrics = ProjectMetrics(
        planned_value=900_000,
        earned_value=820_000,
        actual_cost=880_000,
    )

    metrics.report()

    forecast = estimate_at_completion(
        budget_at_completion=1_500_000,
        actual_cost=880_000,
        earned_value=820_000,
    )

    print("\nPROJECT FORECAST")
    for key, value in forecast.items():
        if key == "CPI":
            print(f"{key}: {value:.3f}")
        else:
            print(f"{key}: ₹{value:,.2f}")

    print("\nCHANGE REQUEST EXAMPLE")

    change = ChangeRequest(
        change_id="CR-001",
        description="Add an additional executive dashboard.",
        scope_impact=8.0,
        cost_impact=60_000,
        schedule_impact_days=4,
        quality_impact="No expected reduction if additional testing capacity is approved.",
    )

    print(f"Request: {change.description}")
    print(f"Status: {change.status.value}")
    print(f"Impact: {change.total_impact()}")

    change.status = ChangeStatus.UNDER_REVIEW

    # Approval is conditional on impact analysis.
    if change.cost_impact <= 100_000 and change.schedule_impact_days <= 5:
        change.approve()
        print(f"Decision: {change.status.value}")

        change.implement()
        print(f"Implementation Status: {change.status.value}")
    else:
        change.reject()
        print(f"Decision: {change.status.value}")


def run_issue_and_escalation_example() -> None:
    print("\n" + "=" * 90)
    print("MONITORING - ISSUE MANAGEMENT AND ESCALATION")
    print("=" * 90)

    issue = Issue(
        issue_id="ISS-001",
        description="Production test environment is unavailable.",
        priority="High",
        owner="Technology Lead",
        due_date=date(2026, 3, 15),
    )

    print(f"Issue: {issue.description}")
    print(f"Status: {issue.status}")

    issue.close("Infrastructure team restored the environment and validated access.")

    print(f"Status after resolution: {issue.status}")
    print(f"Resolution: {issue.resolution}")

    escalation_required = should_escalate(
        financial_impact=180_000,
        schedule_delay_days=6,
        authority_limit=100_000,
        schedule_tolerance_days=5,
    )

    print(f"\nEscalation required: {escalation_required}")


def run_status_reporting_example() -> None:
    print("\n" + "=" * 90)
    print("MONITORING - STATUS REPORT")
    print("=" * 90)

    report = StatusReport(
        reporting_period="Week 10",
        accomplishments=[
            "Completed data integration",
            "Completed first dashboard iteration",
            "Closed three high-priority defects",
        ],
        planned_next_period=[
            "Complete user acceptance testing",
            "Resolve remaining medium-priority defects",
            "Prepare production handover",
        ],
        risks=[
            "Business-user availability remains constrained",
        ],
        issues=[
            "One non-critical integration defect remains open",
        ],
        decisions_required=[
            "Confirm production deployment window",
        ],
        overall_status="Amber",
    )

    report.display()


def run_governance_example() -> None:
    print("\n" + "=" * 90)
    print("PROJECT GOVERNANCE")
    print("=" * 90)

    roles = [
        GovernanceRole(
            "Project Sponsor",
            [
                "Provide executive support",
                "Approve major decisions",
                "Resolve escalated organizational issues",
            ],
            "High",
        ),
        GovernanceRole(
            "Project Manager",
            [
                "Coordinate project delivery",
                "Manage schedule, cost, risk, and stakeholders",
                "Report project performance",
            ],
            "Operational",
        ),
        GovernanceRole(
            "Change Control Board",
            [
                "Review significant change requests",
                "Assess cross-functional impacts",
                "Approve or reject governed changes",
            ],
            "Change Authority",
        ),
    ]

    for role in roles:
        role.display()


def run_closing_example() -> None:
    print("\n" + "=" * 90)
    print("STAGE 5: CLOSING")
    print("=" * 90)

    checklist = ClosureChecklist(
        final_acceptance=True,
        deliverables_verified=True,
        contracts_closed=True,
        resources_released=True,
        documentation_archived=True,
        lessons_recorded=True,
        operations_handover=True,
    )

    print(f"Closure complete: {checklist.is_complete()}")

    if not checklist.is_complete():
        print("Missing closure items:")
        for item in checklist.missing_items():
            print(f"  - {item}")
    else:
        print("All closure activities have been completed.")

    lessons = [
        LessonLearned(
            "Requirements",
            "Early validation reduced late-stage rework.",
            "Lowered the number of acceptance defects.",
            "Schedule structured requirement reviews before development.",
        ),
        LessonLearned(
            "Stakeholders",
            "Business-user availability varied during testing.",
            "Acceptance activities required schedule adjustments.",
            "Reserve stakeholder time before the testing phase begins.",
        ),
        LessonLearned(
            "Risk",
            "Backup extraction reduced the effect of source-system instability.",
            "Data integration continued despite an availability problem.",
            "Maintain contingency mechanisms for critical dependencies.",
        ),
    ]

    display_lessons(lessons)


def run_health_example() -> None:
    print("\n" + "=" * 90)
    print("PROJECT HEALTH")
    print("=" * 90)

    score = calculate_project_health(
        scope_score=90,
        schedule_score=72,
        cost_score=78,
        quality_score=92,
        risk_score=68,
    )

    print(f"Health Score: {score:.2f}/100")
    print(f"Health Status: {health_label(score)}")


def run_simulation_example() -> None:
    print("\n" + "=" * 90)
    print("ADVANCED: SCHEDULE UNCERTAINTY SIMULATION")
    print("=" * 90)

    random.seed(42)

    simulation = simulate_duration(
        optimistic=8,
        most_likely=12,
        pessimistic=20,
        simulations=5000,
    )

    print("Estimated duration distribution:")
    for key, value in simulation.items():
        print(f"{key:<10}: {value:.2f} days")


# ============================================================================
# 28. IMPORTANT EDGE CASES
# ============================================================================

def run_edge_case_examples() -> None:
    print("\n" + "=" * 90)
    print("EDGE CASES AND EXCEPTIONS")
    print("=" * 90)

    # Zero-duration task can represent a milestone.
    milestone_task = Task(
        "M1",
        "Approval Milestone",
        0,
        [],
    )

    print(
        f"Zero-duration task: {milestone_task.name} | "
        f"Duration={milestone_task.duration}"
    )

    # A task can have multiple predecessors.
    integration = Task(
        "X",
        "Integrated Release",
        3,
        ["A", "B"],
    )

    print(
        f"Multiple predecessors: {integration.name} | "
        f"Dependencies={integration.predecessors}"
    )

    # Invalid dependency should be rejected.
    invalid_tasks = [
        Task("A", "Task A", 2, []),
        Task("B", "Task B", 3, ["UNKNOWN"]),
    ]

    try:
        validate_task_dependencies(invalid_tasks)
    except ValueError as error:
        print(f"Invalid dependency handled: {error}")

    # Circular dependencies should be rejected.
    circular_tasks = [
        Task("A", "Task A", 2, ["B"]),
        Task("B", "Task B", 3, ["A"]),
    ]

    try:
        calculate_critical_path(circular_tasks)
    except ValueError as error:
        print(f"Circular dependency handled: {error}")

    # Closure cannot be claimed complete when items are missing.
    incomplete_closure = ClosureChecklist(
        final_acceptance=True,
        deliverables_verified=True,
    )

    print(
        f"\nIncomplete closure: {incomplete_closure.is_complete()}"
    )
    print("Missing:")
    for item in incomplete_closure.missing_items():
        print(f"  - {item}")


# ============================================================================
# 29. BEST-PRACTICE CHECKLIST
# ============================================================================

def print_best_practices() -> None:
    print("\n" + "=" * 90)
    print("PROJECT LIFE CYCLE BEST PRACTICES")
    print("=" * 90)

    practices = [
        "Authorize the project using a clear business need and objective.",
        "Define measurable success criteria before significant execution begins.",
        "Identify stakeholders early and tailor engagement to their influence and interest.",
        "Define scope boundaries and explicitly document exclusions.",
        "Decompose scope into manageable work packages.",
        "Build schedules using logical dependencies rather than arbitrary dates.",
        "Identify the critical path and monitor tasks with low or zero slack.",
        "Estimate resources and costs using documented assumptions.",
        "Maintain a risk register and assign risk owners.",
        "Distinguish risks from issues and manage them differently.",
        "Establish quality criteria before deliverables are produced.",
        "Use structured communication appropriate to each stakeholder group.",
        "Control changes through impact assessment and authorization.",
        "Compare actual performance with approved baselines.",
        "Use both schedule and cost indicators rather than relying on one metric.",
        "Escalate decisions when they exceed delegated authority.",
        "Document decisions and maintain an auditable project record.",
        "Obtain formal acceptance before declaring completion.",
        "Transfer ownership to operations where applicable.",
        "Capture lessons learned while project knowledge is still fresh.",
    ]

    for index, practice in enumerate(practices, start=1):
        print(f"{index:>2}. {practice}")


# ============================================================================
# 30. MAIN PROGRAM
# ============================================================================

def main() -> None:
    """
    Run the complete learning demonstration.

    The sequence follows the project life cycle:
        Initiation
            ↓
        Planning
            ↓
        Execution
            ↓
        Monitoring and Controlling
            ↓
        Closing

    Cross-cutting disciplines such as stakeholder management, governance,
    communication, risk, quality, and change control operate across multiple
    stages rather than belonging exclusively to one stage.
    """

    print("=" * 90)
    print("PROJECT LIFE CYCLE - COMPLETE PYTHON STUDY PROGRAM")
    print("=" * 90)

    print(
        """
MAIN PROJECT LIFE CYCLE

1. Initiation
   Define the problem, business case, objectives, stakeholders, feasibility,
   high-level scope, assumptions, constraints, and authorization.

2. Planning
   Define detailed scope, requirements, WBS, schedule, resources, cost,
   quality, risk, communication, procurement, and governance arrangements.

3. Execution
   Perform the planned work, coordinate resources, produce deliverables,
   manage stakeholders, suppliers, quality, issues, and approved changes.

4. Monitoring and Controlling
   Measure performance against baselines, manage deviations, risks, issues,
   changes, quality, cost, schedule, and stakeholder expectations.

5. Closing
   Obtain acceptance, verify deliverables, complete handover, close
   contracts and financial records, release resources, archive information,
   and document lessons learned.
"""
    )

    run_initiation_example()
    run_stakeholder_example()
    run_scope_and_wbs_example()
    run_schedule_example()
    run_resource_and_cost_example()
    run_risk_example()
    run_execution_example()
    run_quality_example()
    run_communication_example()
    run_procurement_example()
    run_monitoring_example()
    run_issue_and_escalation_example()
    run_status_reporting_example()
    run_governance_example()
    compare_lifecycle_approaches()
    run_health_example()
    run_simulation_example()
    run_closing_example()
    run_edge_case_examples()
    print_best_practices()

    print("\n" + "=" * 90)
    print("END OF PROJECT LIFE CYCLE STUDY PROGRAM")
    print("=" * 90)


if __name__ == "__main__":
    main()
