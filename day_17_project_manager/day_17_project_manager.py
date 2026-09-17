"""
Project Management Study Program
Topic: Responsibilities of a Project Manager

This standalone Python program teaches the responsibilities of a project manager
through executable demonstrations, simulations, validation, planning models,
risk management, stakeholder management, scheduling, budgeting, quality control,
change control, communication, reporting, and project governance.

The examples use only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from collections import defaultdict, deque
from statistics import mean
from typing import Dict, List, Optional, Set, Tuple
import math
import random


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

class ProjectStatus(Enum):
    PLANNED = "Planned"
    ACTIVE = "Active"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class RiskProbability(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class RiskImpact(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ChangeStatus(Enum):
    PROPOSED = "Proposed"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IMPLEMENTED = "Implemented"


@dataclass
class Project:
    name: str
    objective: str
    sponsor: str
    manager: str
    budget: float
    start_date: date
    target_end_date: date
    status: ProjectStatus = ProjectStatus.PLANNED

    @property
    def planned_duration_days(self) -> int:
        return (self.target_end_date - self.start_date).days + 1

    def activate(self) -> None:
        if self.status == ProjectStatus.PLANNED:
            self.status = ProjectStatus.ACTIVE

    def complete(self) -> None:
        if self.status == ProjectStatus.ACTIVE:
            self.status = ProjectStatus.COMPLETED


@dataclass
class Task:
    task_id: str
    name: str
    owner: str
    duration_days: int
    estimated_cost: float
    dependencies: List[str] = field(default_factory=list)
    progress: float = 0.0
    status: ProjectStatus = ProjectStatus.PLANNED

    def update_progress(self, percentage: float) -> None:
        if not 0 <= percentage <= 100:
            raise ValueError("Progress must be between 0 and 100.")

        self.progress = percentage

        if percentage == 100:
            self.status = ProjectStatus.COMPLETED
        elif percentage > 0:
            self.status = ProjectStatus.ACTIVE


@dataclass
class Stakeholder:
    name: str
    role: str
    influence: int
    interest: int
    communication_frequency: str
    preferred_channel: str

    def category(self) -> str:
        if self.influence >= 4 and self.interest >= 4:
            return "Manage closely"
        if self.influence >= 4 and self.interest < 4:
            return "Keep satisfied"
        if self.influence < 4 and self.interest >= 4:
            return "Keep informed"
        return "Monitor"


@dataclass
class Risk:
    risk_id: str
    description: str
    probability: RiskProbability
    impact: RiskImpact
    owner: str
    response: str
    contingency: str
    status: str = "Open"

    @property
    def score(self) -> int:
        return self.probability.value * self.impact.value

    @property
    def severity(self) -> str:
        if self.score >= 6:
            return "High"
        if self.score >= 3:
            return "Medium"
        return "Low"


@dataclass
class ChangeRequest:
    change_id: str
    description: str
    reason: str
    requested_by: str
    estimated_cost: float
    estimated_delay_days: int
    business_value: float
    status: ChangeStatus = ChangeStatus.PROPOSED

    def evaluate(self, remaining_budget: float) -> str:
        if self.estimated_cost > remaining_budget:
            return "Reject or redesign: insufficient budget."

        if self.business_value >= 8 and self.estimated_delay_days <= 5:
            return "Potentially approve after impact review."

        return "Requires formal impact and stakeholder review."


# ---------------------------------------------------------------------------
# 2. RESPONSIBILITIES OF A PROJECT MANAGER
# ---------------------------------------------------------------------------

RESPONSIBILITIES = {
    "Initiation": [
        "Understand the business problem",
        "Define the project objective",
        "Clarify scope and success criteria",
        "Identify sponsor and stakeholders",
        "Assess feasibility",
        "Establish initial assumptions and constraints",
    ],
    "Planning": [
        "Create work breakdown structure",
        "Estimate effort and cost",
        "Develop schedule",
        "Assign responsibilities",
        "Plan resources",
        "Plan communications",
        "Plan risks",
        "Define quality approach",
        "Establish baseline expectations",
    ],
    "Execution": [
        "Coordinate people and resources",
        "Remove blockers",
        "Facilitate decisions",
        "Manage stakeholder communication",
        "Monitor quality",
        "Resolve conflicts",
        "Maintain project documentation",
    ],
    "Monitoring and Control": [
        "Track scope",
        "Track schedule",
        "Track cost",
        "Track quality",
        "Track risks and issues",
        "Control changes",
        "Forecast project performance",
        "Report project status",
    ],
    "Closing": [
        "Obtain acceptance",
        "Verify deliverables",
        "Close contracts",
        "Archive documentation",
        "Capture lessons learned",
        "Release resources",
        "Measure outcomes",
    ],
}


def print_responsibilities() -> None:
    print("\n=== Core Responsibilities ===")
    for phase, responsibilities in RESPONSIBILITIES.items():
        print(f"\n{phase}:")
        for item in responsibilities:
            print(f"  - {item}")


# ---------------------------------------------------------------------------
# 3. PROJECT OBJECTIVES AND SMART CRITERIA
# ---------------------------------------------------------------------------

def validate_objective(
    specific: bool,
    measurable: bool,
    achievable: bool,
    relevant: bool,
    time_bound: bool,
) -> bool:
    """
    A practical SMART-style validation model.

    A project manager should avoid objectives that sound useful but cannot be
    measured or connected to a time boundary.
    """
    return all(
        [specific, measurable, achievable, relevant, time_bound]
    )


# ---------------------------------------------------------------------------
# 4. SCOPE MANAGEMENT
# ---------------------------------------------------------------------------

@dataclass
class ScopeItem:
    name: str
    included: bool
    rationale: str


def classify_scope(items: List[ScopeItem]) -> Tuple[List[str], List[str]]:
    included = [item.name for item in items if item.included]
    excluded = [item.name for item in items if not item.included]
    return included, excluded


# ---------------------------------------------------------------------------
# 5. WORK BREAKDOWN STRUCTURE
# ---------------------------------------------------------------------------

def build_wbs() -> Dict[str, List[str]]:
    """
    A WBS decomposes project scope into manageable work packages.
    """
    return {
        "1. Initiation": [
            "1.1 Business case",
            "1.2 Project charter",
            "1.3 Stakeholder identification",
        ],
        "2. Planning": [
            "2.1 Requirements",
            "2.2 Architecture",
            "2.3 Schedule",
            "2.4 Budget",
            "2.5 Risk plan",
        ],
        "3. Execution": [
            "3.1 Development",
            "3.2 Testing",
            "3.3 Documentation",
            "3.4 Training",
        ],
        "4. Deployment": [
            "4.1 Production preparation",
            "4.2 Deployment",
            "4.3 Validation",
        ],
        "5. Closure": [
            "5.1 Acceptance",
            "5.2 Lessons learned",
            "5.3 Resource release",
            "5.4 Final report",
        ],
    }


# ---------------------------------------------------------------------------
# 6. RESPONSIBILITY ASSIGNMENT
# ---------------------------------------------------------------------------

@dataclass
class ResponsibilityMatrix:
    """
    Simplified RACI matrix.

    R = Responsible
    A = Accountable
    C = Consulted
    I = Informed
    """

    matrix: Dict[str, Dict[str, str]]

    def validate(self) -> List[str]:
        warnings = []

        for work_item, assignments in self.matrix.items():
            accountable = [
                person
                for person, role in assignments.items()
                if role == "A"
            ]

            if len(accountable) == 0:
                warnings.append(
                    f"{work_item}: no accountable person assigned."
                )
            elif len(accountable) > 1:
                warnings.append(
                    f"{work_item}: multiple accountable people assigned."
                )

        return warnings


# ---------------------------------------------------------------------------
# 7. SCHEDULING AND DEPENDENCY MANAGEMENT
# ---------------------------------------------------------------------------

def topological_schedule(tasks: Dict[str, Task]) -> List[str]:
    """
    Produces a dependency-respecting order.

    This is not a complete scheduling engine, but it demonstrates one of the
    algorithms behind dependency-aware project planning.
    """
    indegree = {task_id: 0 for task_id in tasks}
    graph: Dict[str, List[str]] = defaultdict(list)

    for task in tasks.values():
        for dependency in task.dependencies:
            if dependency not in tasks:
                raise ValueError(
                    f"Task {task.task_id} depends on unknown task {dependency}."
                )

            graph[dependency].append(task.task_id)
            indegree[task.task_id] += 1

    queue = deque(
        task_id for task_id, degree in indegree.items() if degree == 0
    )

    ordered = []

    while queue:
        current = queue.popleft()
        ordered.append(current)

        for successor in graph[current]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)

    if len(ordered) != len(tasks):
        raise ValueError("Circular dependency detected.")

    return ordered


def calculate_critical_path(tasks: Dict[str, Task]) -> Tuple[int, List[str]]:
    """
    Calculates a simple critical path using earliest finish times.

    For each task:
        earliest_start = maximum predecessor finish
        earliest_finish = earliest_start + duration

    The path with the greatest finish time determines the minimum project
    duration under the given dependency structure.
    """
    order = topological_schedule(tasks)

    earliest_start: Dict[str, int] = {}
    earliest_finish: Dict[str, int] = {}
    predecessor_choice: Dict[str, Optional[str]] = {}

    for task_id in order:
        task = tasks[task_id]

        if not task.dependencies:
            earliest_start[task_id] = 0
            predecessor_choice[task_id] = None
        else:
            predecessor = max(
                task.dependencies,
                key=lambda dependency: earliest_finish[dependency],
            )
            earliest_start[task_id] = earliest_finish[predecessor]
            predecessor_choice[task_id] = predecessor

        earliest_finish[task_id] = (
            earliest_start[task_id] + task.duration_days
        )

    final_task = max(
        earliest_finish,
        key=earliest_finish.get,
    )

    critical_path = []
    current = final_task

    while current is not None:
        critical_path.append(current)
        current = predecessor_choice[current]

    critical_path.reverse()

    return earliest_finish[final_task], critical_path


# ---------------------------------------------------------------------------
# 8. COST AND BUDGET MANAGEMENT
# ---------------------------------------------------------------------------

def calculate_budget(tasks: Dict[str, Task]) -> float:
    return sum(task.estimated_cost for task in tasks.values())


def budget_status(
    approved_budget: float,
    planned_cost: float,
    actual_cost: float,
) -> Dict[str, float]:
    variance = approved_budget - actual_cost
    remaining_planned = approved_budget - planned_cost

    return {
        "approved_budget": approved_budget,
        "planned_cost": planned_cost,
        "actual_cost": actual_cost,
        "cost_variance": variance,
        "remaining_after_actuals": variance,
        "planned_buffer": remaining_planned,
    }


# ---------------------------------------------------------------------------
# 9. EARNED VALUE MANAGEMENT
# ---------------------------------------------------------------------------

def earned_value_metrics(
    planned_value: float,
    earned_value: float,
    actual_cost: float,
) -> Dict[str, float]:
    """
    Basic EVM metrics:

    CV  = EV - AC
    SV  = EV - PV
    CPI = EV / AC
    SPI = EV / PV

    CV and SV are monetary representations of cost and schedule variance.
    CPI and SPI are efficiency ratios.
    """
    if actual_cost <= 0:
        raise ValueError("Actual cost must be positive for CPI.")

    if planned_value <= 0:
        raise ValueError("Planned value must be positive for SPI.")

    cost_variance = earned_value - actual_cost
    schedule_variance = earned_value - planned_value
    cost_performance_index = earned_value / actual_cost
    schedule_performance_index = earned_value / planned_value

    return {
        "CV": cost_variance,
        "SV": schedule_variance,
        "CPI": cost_performance_index,
        "SPI": schedule_performance_index,
    }


# ---------------------------------------------------------------------------
# 10. RISK MANAGEMENT
# ---------------------------------------------------------------------------

def prioritize_risks(risks: List[Risk]) -> List[Risk]:
    """
    Higher probability-impact scores receive earlier attention.

    This is a prioritization mechanism, not a substitute for professional
    judgment. Some low-frequency risks can still be strategically critical.
    """
    return sorted(risks, key=lambda risk: risk.score, reverse=True)


def risk_register_report(risks: List[Risk]) -> None:
    print("\n=== Risk Register ===")

    for risk in prioritize_risks(risks):
        print(
            f"{risk.risk_id}: {risk.description} | "
            f"Score={risk.score} | Severity={risk.severity} | "
            f"Owner={risk.owner} | Response={risk.response}"
        )


# ---------------------------------------------------------------------------
# 11. ISSUE MANAGEMENT
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    issue_id: str
    description: str
    owner: str
    severity: str
    due_date: date
    status: str = "Open"

    def is_overdue(self, today: date) -> bool:
        return self.status != "Closed" and today > self.due_date


# ---------------------------------------------------------------------------
# 12. STAKEHOLDER MANAGEMENT
# ---------------------------------------------------------------------------

def stakeholder_matrix(stakeholders: List[Stakeholder]) -> None:
    print("\n=== Stakeholder Analysis ===")

    for stakeholder in stakeholders:
        print(
            f"{stakeholder.name}: "
            f"influence={stakeholder.influence}, "
            f"interest={stakeholder.interest}, "
            f"strategy={stakeholder.category()}, "
            f"frequency={stakeholder.communication_frequency}"
        )


# ---------------------------------------------------------------------------
# 13. COMMUNICATION MANAGEMENT
# ---------------------------------------------------------------------------

@dataclass
class StatusReport:
    reporting_date: date
    accomplishments: List[str]
    planned_next: List[str]
    risks: List[str]
    issues: List[str]
    decisions_needed: List[str]
    budget_variance: float
    schedule_variance_days: int

    def render(self) -> str:
        lines = [
            f"Project Status Report: {self.reporting_date.isoformat()}",
            "",
            "Accomplishments:",
        ]

        lines.extend(f"- {item}" for item in self.accomplishments)

        lines.append("")
        lines.append("Next period:")
        lines.extend(f"- {item}" for item in self.planned_next)

        lines.append("")
        lines.append("Risks:")
        lines.extend(f"- {item}" for item in self.risks)

        lines.append("")
        lines.append("Issues:")
        lines.extend(f"- {item}" for item in self.issues)

        lines.append("")
        lines.append("Decisions needed:")
        lines.extend(f"- {item}" for item in self.decisions_needed)

        lines.append("")
        lines.append(
            f"Budget variance: {self.budget_variance:,.2f}"
        )
        lines.append(
            f"Schedule variance: {self.schedule_variance_days} days"
        )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 14. CHANGE CONTROL
# ---------------------------------------------------------------------------

class ChangeControlBoard:
    """
    A lightweight model of formal change governance.

    The project manager does not automatically approve every requested change.
    Impact on scope, cost, time, quality, risk, resources, and benefits should
    be evaluated before a decision.
    """

    def __init__(self, budget: float):
        self.budget = budget
        self.requests: List[ChangeRequest] = []

    def submit(self, request: ChangeRequest) -> None:
        request.status = ChangeStatus.UNDER_REVIEW
        self.requests.append(request)

    def review(self, request: ChangeRequest) -> str:
        evaluation = request.evaluate(self.budget)

        if evaluation.startswith("Potentially approve"):
            request.status = ChangeStatus.APPROVED
            self.budget -= request.estimated_cost
        elif "insufficient" in evaluation:
            request.status = ChangeStatus.REJECTED

        return evaluation


# ---------------------------------------------------------------------------
# 15. QUALITY MANAGEMENT
# ---------------------------------------------------------------------------

@dataclass
class QualityCheck:
    requirement: str
    expected: str
    actual: str

    @property
    def passed(self) -> bool:
        return self.expected == self.actual


def quality_report(checks: List[QualityCheck]) -> Dict[str, int]:
    passed = sum(check.passed for check in checks)
    failed = len(checks) - passed

    return {
        "total": len(checks),
        "passed": passed,
        "failed": failed,
    }


# ---------------------------------------------------------------------------
# 16. RESOURCE MANAGEMENT
# ---------------------------------------------------------------------------

@dataclass
class Resource:
    name: str
    role: str
    available_hours: float
    allocated_hours: float = 0.0

    @property
    def utilization(self) -> float:
        if self.available_hours <= 0:
            return math.inf

        return self.allocated_hours / self.available_hours * 100

    def allocate(self, hours: float) -> None:
        if hours < 0:
            raise ValueError("Allocation cannot be negative.")

        self.allocated_hours += hours


# ---------------------------------------------------------------------------
# 17. CONFLICT MANAGEMENT
# ---------------------------------------------------------------------------

def conflict_response(
    conflict_type: str,
    urgency: str,
    importance: str,
) -> str:
    """
    Demonstrates a practical conflict-response selection.

    The actual response should depend on context, power relationships,
    contractual constraints, safety, and organizational culture.
    """
    if conflict_type == "technical disagreement":
        if importance == "high":
            return "Facilitate evidence-based discussion and document the decision."
        return "Allow the technical owners to resolve with a defined deadline."

    if conflict_type == "resource conflict":
        return "Clarify priorities, capacity, dependencies, and escalation path."

    if conflict_type == "interpersonal":
        if urgency == "high":
            return "Stabilize the immediate work situation, then conduct a structured discussion."
        return "Meet privately with affected parties and establish agreed actions."

    return "Collect facts, identify interests, and select an appropriate resolution approach."


# ---------------------------------------------------------------------------
# 18. PROCUREMENT AND VENDOR MANAGEMENT
# ---------------------------------------------------------------------------

@dataclass
class Vendor:
    name: str
    quoted_cost: float
    delivery_days: int
    quality_score: float
    contractual_risk: float


def vendor_comparison(vendors: List[Vendor]) -> List[Vendor]:
    """
    Creates a transparent multi-factor ordering.

    The weights are illustrative and should be agreed with procurement and
    business stakeholders rather than treated as universal rules.
    """
    def score(vendor: Vendor) -> float:
        cost_component = max(0, 100 - vendor.quoted_cost / 1000)
        delivery_component = max(0, 100 - vendor.delivery_days)
        risk_component = max(0, 100 - vendor.contractual_risk)

        return (
            0.25 * cost_component
            + 0.25 * delivery_component
            + 0.35 * vendor.quality_score
            + 0.15 * risk_component
        )

    return sorted(vendors, key=score, reverse=True)


# ---------------------------------------------------------------------------
# 19. PROJECT FORECASTING
# ---------------------------------------------------------------------------

def forecast_at_completion(
    budget_at_completion: float,
    cost_performance_index: float,
) -> float:
    if cost_performance_index <= 0:
        raise ValueError("CPI must be positive.")

    return budget_at_completion / cost_performance_index


def estimate_to_complete(
    forecast_at_completion: float,
    actual_cost: float,
) -> float:
    return forecast_at_completion - actual_cost


# ---------------------------------------------------------------------------
# 20. AGILE PROJECT MANAGEMENT
# ---------------------------------------------------------------------------

@dataclass
class BacklogItem:
    item_id: str
    title: str
    priority: int
    story_points: int
    status: str = "To Do"


def sprint_capacity(items: List[BacklogItem], capacity_points: int) -> List[BacklogItem]:
    """
    Selects items in priority order until capacity is reached.

    Real product delivery also considers dependencies, skills, risk,
    operational work, technical debt, and uncertainty.
    """
    selected = []
    used = 0

    for item in sorted(items, key=lambda x: x.priority):
        if used + item.story_points <= capacity_points:
            selected.append(item)
            used += item.story_points

    return selected


# ---------------------------------------------------------------------------
# 21. PROJECT MANAGER VS PRODUCT MANAGER
# ---------------------------------------------------------------------------

def role_comparison() -> Dict[str, List[str]]:
    return {
        "Project Manager": [
            "Coordinates delivery",
            "Manages scope, schedule, cost, resources, risks and dependencies",
            "Tracks execution against agreed plans",
            "Facilitates governance and reporting",
        ],
        "Product Manager": [
            "Defines product direction",
            "Studies customer and market needs",
            "Prioritizes product outcomes",
            "Owns product vision and value decisions",
        ],
    }


# ---------------------------------------------------------------------------
# 22. AGILE VS TRADITIONAL DELIVERY
# ---------------------------------------------------------------------------

def delivery_model_comparison() -> Dict[str, Dict[str, str]]:
    return {
        "Predictive": {
            "planning": "Detailed planning before major execution",
            "change": "Formal change control",
            "use_case": "Stable requirements and regulated environments",
        },
        "Adaptive": {
            "planning": "Progressive planning",
            "change": "Frequent reprioritization",
            "use_case": "High uncertainty and evolving customer needs",
        },
        "Hybrid": {
            "planning": "Fixed governance with iterative delivery",
            "change": "Controlled flexibility",
            "use_case": "Organizations combining formal governance and agile teams",
        },
    }


# ---------------------------------------------------------------------------
# 23. PROJECT GOVERNANCE
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    decision_id: str
    subject: str
    decision: str
    owner: str
    date_made: date
    rationale: str


class DecisionLog:
    def __init__(self):
        self.decisions: List[Decision] = []

    def add(self, decision: Decision) -> None:
        self.decisions.append(decision)

    def search(self, keyword: str) -> List[Decision]:
        keyword = keyword.lower()
        return [
            decision
            for decision in self.decisions
            if keyword in decision.subject.lower()
            or keyword in decision.decision.lower()
            or keyword in decision.rationale.lower()
        ]


# ---------------------------------------------------------------------------
# 24. SECURITY AND DATA GOVERNANCE
# ---------------------------------------------------------------------------

def security_checklist() -> List[str]:
    return [
        "Limit project information to authorized personnel.",
        "Protect credentials and secrets.",
        "Avoid placing sensitive information in ordinary status reports.",
        "Use approved storage and communication systems.",
        "Track security-related risks and incidents.",
        "Apply least-privilege access where applicable.",
        "Define retention and disposal requirements.",
        "Escalate suspected security incidents through the approved process.",
    ]


# ---------------------------------------------------------------------------
# 25. PROJECT CLOSURE
# ---------------------------------------------------------------------------

def closure_checklist() -> List[str]:
    return [
        "Deliverables accepted",
        "Acceptance criteria verified",
        "Open defects transferred or resolved",
        "Contracts closed",
        "Financial reconciliation completed",
        "Documentation archived",
        "Lessons learned recorded",
        "Operational ownership transferred",
        "Resources released",
        "Final stakeholder communication completed",
    ]


# ---------------------------------------------------------------------------
# 26. COMPLETE INDUSTRY-STYLE SIMULATION
# ---------------------------------------------------------------------------

def run_project_case_study() -> None:
    print("\n" + "=" * 78)
    print("INDUSTRY-STYLE PROJECT MANAGEMENT CASE STUDY")
    print("=" * 78)

    project = Project(
        name="Enterprise Service Management Platform",
        objective=(
            "Implement a centralized platform for service requests, "
            "workflow automation, reporting, and operational visibility."
        ),
        sponsor="Chief Operating Officer",
        manager="Project Manager",
        budget=250_000,
        start_date=date(2026, 10, 1),
        target_end_date=date(2027, 2, 28),
    )

    project.activate()

    print(f"\nProject: {project.name}")
    print(f"Objective: {project.objective}")
    print(f"Sponsor: {project.sponsor}")
    print(f"Planned duration: {project.planned_duration_days} days")
    print(f"Budget: {project.budget:,.2f}")
    print(f"Status: {project.status.value}")

    # Scope definition.
    scope_items = [
        ScopeItem("Request management", True, "Core business capability"),
        ScopeItem("Approval workflows", True, "Required governance"),
        ScopeItem("Management dashboard", True, "Required reporting"),
        ScopeItem("Mobile native application", False, "Deferred to later release"),
        ScopeItem("External marketplace", False, "Outside initial business case"),
    ]

    included, excluded = classify_scope(scope_items)

    print("\nIncluded scope:")
    for item in included:
        print(f"  - {item}")

    print("\nExcluded scope:")
    for item in excluded:
        print(f"  - {item}")

    # WBS.
    print("\nWBS:")
    for level, work_packages in build_wbs().items():
        print(f"{level}")
        for work_package in work_packages:
            print(f"  {work_package}")

    # Detailed delivery tasks.
    tasks = {
        "T1": Task(
            "T1",
            "Requirements analysis",
            "Business Analyst",
            10,
            18_000,
        ),
        "T2": Task(
            "T2",
            "Solution architecture",
            "Solution Architect",
            8,
            22_000,
            ["T1"],
        ),
        "T3": Task(
            "T3",
            "UX design",
            "UX Designer",
            7,
            12_000,
            ["T1"],
        ),
        "T4": Task(
            "T4",
            "Backend development",
            "Backend Lead",
            25,
            58_000,
            ["T2"],
        ),
        "T5": Task(
            "T5",
            "Frontend development",
            "Frontend Lead",
            20,
            42_000,
            ["T2", "T3"],
        ),
        "T6": Task(
            "T6",
            "Integration testing",
            "QA Lead",
            12,
            24_000,
            ["T4", "T5"],
        ),
        "T7": Task(
            "T7",
            "User acceptance testing",
            "Business Owner",
            8,
            14_000,
            ["T6"],
        ),
        "T8": Task(
            "T8",
            "Production deployment",
            "DevOps Lead",
            4,
            9_000,
            ["T7"],
        ),
        "T9": Task(
            "T9",
            "Training and handover",
            "Change Lead",
            6,
            11_000,
            ["T7"],
        ),
    }

    schedule_order = topological_schedule(tasks)
    duration, critical_path = calculate_critical_path(tasks)
    planned_cost = calculate_budget(tasks)

    print("\nDependency-respecting execution order:")
    print(" -> ".join(schedule_order))

    print(f"\nCalculated minimum dependency duration: {duration} days")
    print(f"Critical path: {' -> '.join(critical_path)}")
    print(f"Planned task cost: {planned_cost:,.2f}")

    # Resource planning.
    resources = [
        Resource("Backend Lead", "Engineering", 320),
        Resource("Frontend Lead", "Engineering", 280),
        Resource("QA Lead", "Quality", 180),
        Resource("Business Owner", "Business", 120),
    ]

    resources[0].allocate(300)
    resources[1].allocate(240)
    resources[2].allocate(170)
    resources[3].allocate(90)

    print("\nResource utilization:")
    for resource in resources:
        print(
            f"{resource.name}: "
            f"{resource.allocated_hours}/{resource.available_hours} hours "
            f"({resource.utilization:.1f}%)"
        )

    # Stakeholder management.
    stakeholders = [
        Stakeholder(
            "Chief Operating Officer",
            "Executive sponsor",
            5,
            5,
            "Weekly",
            "Executive review",
        ),
        Stakeholder(
            "Finance Director",
            "Budget owner",
            5,
            3,
            "Biweekly",
            "Email/report",
        ),
        Stakeholder(
            "Operations Team",
            "Primary users",
            3,
            5,
            "Weekly",
            "Workshop",
        ),
        Stakeholder(
            "IT Security",
            "Control function",
            4,
            4,
            "At control gates",
            "Formal review",
        ),
    ]

    stakeholder_matrix(stakeholders)

    # RACI.
    raci = ResponsibilityMatrix(
        {
            "Requirements": {
                "Project Manager": "A",
                "Business Analyst": "R",
                "Operations": "C",
                "Sponsor": "I",
            },
            "Architecture": {
                "Project Manager": "A",
                "Solution Architect": "R",
                "Security": "C",
                "Sponsor": "I",
            },
            "Deployment": {
                "Project Manager": "A",
                "DevOps": "R",
                "Security": "C",
                "Operations": "I",
            },
        }
    )

    print("\nRACI validation:")
    warnings = raci.validate()
    if warnings:
        for warning in warnings:
            print(f"  WARNING: {warning}")
    else:
        print("  No accountability conflicts detected.")

    # Risks.
    risks = [
        Risk(
            "R1",
            "Integration interface changes",
            RiskProbability.HIGH,
            RiskImpact.HIGH,
            "Solution Architect",
            "Reduce",
            "Freeze interface version and maintain fallback adapter.",
        ),
        Risk(
            "R2",
            "Key specialist becomes unavailable",
            RiskProbability.MEDIUM,
            RiskImpact.HIGH,
            "Project Manager",
            "Mitigate",
            "Cross-train another engineer.",
        ),
        Risk(
            "R3",
            "Training attendance is low",
            RiskProbability.MEDIUM,
            RiskImpact.MEDIUM,
            "Change Lead",
            "Mitigate",
            "Provide recorded sessions and manager follow-up.",
        ),
    ]

    risk_register_report(risks)

    # Issues.
    issues = [
        Issue(
            "I1",
            "Test environment provisioning delayed",
            "DevOps Lead",
            "High",
            date(2026, 11, 15),
        ),
        Issue(
            "I2",
            "Two requirements require clarification",
            "Business Analyst",
            "Medium",
            date(2026, 11, 20),
        ),
    ]

    today = date(2026, 11, 18)

    print("\nIssue status:")
    for issue in issues:
        overdue = issue.is_overdue(today)
        print(
            f"{issue.issue_id}: {issue.description} | "
            f"overdue={overdue}"
        )

    # Quality.
    quality_checks = [
        QualityCheck("Authentication", "Pass", "Pass"),
        QualityCheck("Approval workflow", "Pass", "Pass"),
        QualityCheck("Dashboard calculation", "Pass", "Fail"),
        QualityCheck("Audit logging", "Pass", "Pass"),
    ]

    print("\nQuality report:")
    for key, value in quality_report(quality_checks).items():
        print(f"  {key}: {value}")

    # EVM.
    evm = earned_value_metrics(
        planned_value=100_000,
        earned_value=92_000,
        actual_cost=98_000,
    )

    print("\nEarned Value Management:")
    for metric, value in evm.items():
        print(f"  {metric}: {value:,.3f}")

    forecast = forecast_at_completion(project.budget, evm["CPI"])
    etc = estimate_to_complete(forecast, 98_000)

    print(f"  Forecast at completion: {forecast:,.2f}")
    print(f"  Estimate to complete: {etc:,.2f}")

    # Change control.
    board = ChangeControlBoard(project.budget)

    change = ChangeRequest(
        "CR-001",
        "Add automated executive alerting",
        "Sponsor requested earlier visibility of critical exceptions",
        "Chief Operating Officer",
        12_000,
        4,
        9,
    )

    board.submit(change)
    decision = board.review(change)

    print("\nChange control:")
    print(f"  Request: {change.description}")
    print(f"  Evaluation: {decision}")
    print(f"  Status: {change.status.value}")
    print(f"  Remaining controlled budget: {board.budget:,.2f}")

    # Status report.
    report = StatusReport(
        reporting_date=today,
        accomplishments=[
            "Requirements baseline approved",
            "Architecture review completed",
            "Backend development reached 55%",
        ],
        planned_next=[
            "Complete core API",
            "Start integration testing preparation",
        ],
        risks=[
            "Integration interface changes",
            "Specialist availability",
        ],
        issues=[
            "Test environment provisioning delay",
        ],
        decisions_needed=[
            "Confirm data retention period",
        ],
        budget_variance=250_000 - 98_000,
        schedule_variance_days=-2,
    )

    print("\n" + report.render())

    # Security.
    print("\nSecurity controls:")
    for item in security_checklist():
        print(f"  - {item}")

    # Closure.
    print("\nClosure checklist:")
    for item in closure_checklist():
        print(f"  - {item}")


# ---------------------------------------------------------------------------
# 27. EDGE CASES AND FAILURE CONDITIONS
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 78)
    print("EDGE CASES")
    print("=" * 78)

    task = Task(
        "EDGE-1",
        "Validation example",
        "Developer",
        5,
        1_000,
    )

    try:
        task.update_progress(120)
    except ValueError as error:
        print(f"Invalid progress handled: {error}")

    circular_tasks = {
        "A": Task("A", "A", "Person A", 2, 100, ["B"]),
        "B": Task("B", "B", "Person B", 2, 100, ["A"]),
    }

    try:
        topological_schedule(circular_tasks)
    except ValueError as error:
        print(f"Circular dependency handled: {error}")

    try:
        earned_value_metrics(0, 100, 50)
    except ValueError as error:
        print(f"Invalid EVM input handled: {error}")

    resource = Resource("Test", "Engineer", 0)

    print(
        "Zero-capacity resource utilization:",
        resource.utilization,
    )


# ---------------------------------------------------------------------------
# 28. TESTING PROJECT MANAGEMENT LOGIC
# ---------------------------------------------------------------------------

def run_self_tests() -> None:
    print("\n" + "=" * 78)
    print("SELF-TESTS")
    print("=" * 78)

    assert validate_objective(True, True, True, True, True)
    assert not validate_objective(True, True, False, True, True)

    tasks = {
        "A": Task("A", "A", "X", 2, 100),
        "B": Task("B", "B", "Y", 3, 100, ["A"]),
    }

    assert topological_schedule(tasks) == ["A", "B"]

    duration, path = calculate_critical_path(tasks)
    assert duration == 5
    assert path == ["A", "B"]

    evm = earned_value_metrics(100, 120, 100)
    assert evm["CPI"] == 1.2
    assert evm["SPI"] == 1.2

    risk = Risk(
        "R",
        "Example",
        RiskProbability.HIGH,
        RiskImpact.HIGH,
        "Owner",
        "Mitigate",
        "Contingency",
    )

    assert risk.score == 9
    assert risk.severity == "High"

    print("All self-tests passed.")


# ---------------------------------------------------------------------------
# 29. PRACTICAL PROJECT MANAGER WORKFLOW
# ---------------------------------------------------------------------------

def project_manager_daily_workflow() -> List[str]:
    """
    A practical daily workflow is not a rigid universal sequence.
    The PM adjusts it according to project phase and organizational context.
    """
    return [
        "Review project dashboard and critical changes.",
        "Check blockers, overdue actions, risks and issues.",
        "Confirm work against current priorities.",
        "Coordinate dependencies between teams.",
        "Resolve or escalate decisions requiring authority.",
        "Communicate material changes to affected stakeholders.",
        "Review scope-change requests.",
        "Update project records and decision logs.",
        "Prepare forecasts where trends indicate variance.",
        "Verify that urgent work has not bypassed governance.",
    ]


def print_daily_workflow() -> None:
    print("\n=== Practical Daily Workflow ===")
    for step in project_manager_daily_workflow():
        print(f"- {step}")


# ---------------------------------------------------------------------------
# 30. MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 78)
    print("PROJECT MANAGER RESPONSIBILITIES: COMPREHENSIVE PYTHON STUDY PROGRAM")
    print("=" * 78)

    print_responsibilities()

    print("\nSMART objective validation:")
    print(
        "Valid objective:",
        validate_objective(True, True, True, True, True),
    )
    print(
        "Incomplete objective:",
        validate_objective(True, True, False, True, True),
    )

    print("\nDelivery model comparison:")
    for model, details in delivery_model_comparison().items():
        print(f"\n{model}")
        for key, value in details.items():
            print(f"  {key}: {value}")

    print("\nProject Manager vs Product Manager:")
    for role, responsibilities in role_comparison().items():
        print(f"\n{role}")
        for responsibility in responsibilities:
            print(f"  - {responsibility}")

    print(
        "\nConflict response example:",
        conflict_response(
            "technical disagreement",
            "medium",
            "high",
        ),
    )

    vendors = [
        Vendor("Vendor A", 95_000, 45, 88, 15),
        Vendor("Vendor B", 82_000, 60, 91, 10),
        Vendor("Vendor C", 105_000, 35, 94, 8),
    ]

    print("\nVendor comparison:")
    for vendor in vendor_comparison(vendors):
        print(
            f"  {vendor.name}: cost={vendor.quoted_cost:,.0f}, "
            f"delivery={vendor.delivery_days} days, "
            f"quality={vendor.quality_score}, "
            f"contractual risk={vendor.contractual_risk}"
        )

    backlog = [
        BacklogItem("P1", "Authentication", 1, 5),
        BacklogItem("P2", "Dashboard", 2, 8),
        BacklogItem("P3", "Audit logging", 3, 3),
        BacklogItem("P4", "Export reports", 4, 5),
    ]

    selected = sprint_capacity(backlog, 13)

    print("\nSprint capacity example:")
    for item in selected:
        print(
            f"  {item.item_id}: {item.title} "
            f"({item.story_points} points)"
        )

    run_project_case_study()
    demonstrate_edge_cases()
    run_self_tests()
    print_daily_workflow()

    print("\nProgram completed.")


if __name__ == "__main__":
    main()
