"""
Project Planning: Beginner-to-Advanced Study Program
=====================================================

This self-contained program teaches project planning through executable examples.

The program models a realistic software project and demonstrates:
- project objectives and scope
- stakeholders
- requirements
- deliverables
- work breakdown structures
- task dependencies
- milestones
- estimates
- scheduling
- critical path analysis
- resource allocation
- risk management
- issue tracking
- change control
- prioritization
- progress measurement
- earned-value-style metrics
- schedule variance
- cost variance
- Agile planning
- sprint planning
- Kanban-style flow
- capacity planning
- project health indicators
- dependency analysis
- scenario analysis
- planning trade-offs
- validation
- testing
- reporting

The examples intentionally use standard-library Python only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_fundamentals() -> None:
    print_section("1. Project Planning Fundamentals")

    concepts = {
        "Project": "A temporary effort undertaken to create a defined result.",
        "Objective": "A measurable outcome the project intends to achieve.",
        "Scope": "The boundaries of what the project will and will not deliver.",
        "Deliverable": "A tangible or verifiable output produced by the project.",
        "Milestone": "A significant checkpoint with zero planned duration.",
        "Task": "A unit of work required to produce a deliverable.",
        "Dependency": "A relationship determining the order or condition of work.",
        "Stakeholder": "A person or organization affected by or able to affect the project.",
        "Constraint": "A limitation such as time, cost, resources, or technology.",
        "Risk": "An uncertain event that may affect project objectives.",
        "Issue": "A problem that has already occurred and requires action.",
        "Baseline": "An approved reference plan used to measure actual performance.",
        "Assumption": "Something treated as true for planning purposes.",
        "Acceptance criterion": "A condition that must be satisfied for a result to be accepted.",
    }

    for term, definition in concepts.items():
        print(f"{term:20} : {definition}")

    print("\nThe classic planning constraints are often represented as:")
    print("Scope <-> Time <-> Cost")
    print("Quality, resources, risk, technology, and compliance can influence all three.")


# ---------------------------------------------------------------------------
# 2. PROJECT OBJECTIVES AND SMART THINKING
# ---------------------------------------------------------------------------

@dataclass
class Objective:
    name: str
    metric: str
    target: str
    deadline: str

    def describe(self) -> str:
        return (
            f"{self.name}: measure {self.metric}, target {self.target}, "
            f"deadline {self.deadline}"
        )


def demonstrate_objectives() -> None:
    print_section("2. Project Objectives")

    objectives = [
        Objective(
            "Launch portfolio dashboard",
            "production availability",
            "99% during the first month",
            "30 June",
        ),
        Objective(
            "Improve report generation",
            "average report generation time",
            "below 5 seconds",
            "30 June",
        ),
        Objective(
            "Protect customer data",
            "critical security findings",
            "zero unresolved critical findings at release",
            "release date",
        ),
    ]

    for objective in objectives:
        print(objective.describe())

    print("\nA useful objective should identify:")
    print("- what must change")
    print("- how success will be measured")
    print("- the target value")
    print("- the relevant deadline")


# ---------------------------------------------------------------------------
# 3. PROJECT CHARTER
# ---------------------------------------------------------------------------

@dataclass
class ProjectCharter:
    project_name: str
    purpose: str
    sponsor: str
    project_manager: str
    start_date: date
    target_date: date
    budget: float
    in_scope: List[str]
    out_of_scope: List[str]
    assumptions: List[str]
    constraints: List[str]

    def validate(self) -> List[str]:
        errors: List[str] = []

        if not self.project_name.strip():
            errors.append("Project name cannot be empty.")
        if self.target_date < self.start_date:
            errors.append("Target date cannot precede start date.")
        if self.budget < 0:
            errors.append("Budget cannot be negative.")
        if not self.in_scope:
            errors.append("At least one in-scope item is required.")

        return errors

    def display(self) -> None:
        print(f"Project: {self.project_name}")
        print(f"Purpose: {self.purpose}")
        print(f"Sponsor: {self.sponsor}")
        print(f"Project manager: {self.project_manager}")
        print(f"Dates: {self.start_date} -> {self.target_date}")
        print(f"Budget: ${self.budget:,.2f}")

        print("\nIn scope:")
        for item in self.in_scope:
            print(f"  - {item}")

        print("\nOut of scope:")
        for item in self.out_of_scope:
            print(f"  - {item}")

        print("\nAssumptions:")
        for item in self.assumptions:
            print(f"  - {item}")

        print("\nConstraints:")
        for item in self.constraints:
            print(f"  - {item}")


# ---------------------------------------------------------------------------
# 4. STAKEHOLDER ANALYSIS
# ---------------------------------------------------------------------------

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
    communication_frequency: str

    def strategy(self) -> str:
        if (
            self.influence == StakeholderInfluence.HIGH
            and self.interest == StakeholderInfluence.HIGH
        ):
            return "Manage closely"
        if self.influence == StakeholderInfluence.HIGH:
            return "Keep satisfied"
        if self.interest == StakeholderInfluence.HIGH:
            return "Keep informed"
        return "Monitor"


def demonstrate_stakeholders() -> None:
    print_section("3. Stakeholder Analysis")

    stakeholders = [
        Stakeholder(
            "Executive Sponsor",
            "Funding and strategic decisions",
            StakeholderInfluence.HIGH,
            StakeholderInfluence.HIGH,
            "Weekly",
        ),
        Stakeholder(
            "Product Owner",
            "Product priorities and acceptance",
            StakeholderInfluence.HIGH,
            StakeholderInfluence.HIGH,
            "Daily",
        ),
        Stakeholder(
            "Security Team",
            "Security review",
            StakeholderInfluence.MEDIUM,
            StakeholderInfluence.HIGH,
            "At major checkpoints",
        ),
        Stakeholder(
            "End Users",
            "Product usage and feedback",
            StakeholderInfluence.MEDIUM,
            StakeholderInfluence.HIGH,
            "Sprint reviews",
        ),
    ]

    for stakeholder in stakeholders:
        print(
            f"{stakeholder.name}: {stakeholder.role}; "
            f"strategy={stakeholder.strategy()}; "
            f"communication={stakeholder.communication_frequency}"
        )


# ---------------------------------------------------------------------------
# 5. REQUIREMENTS
# ---------------------------------------------------------------------------

class RequirementPriority(Enum):
    MUST = 4
    SHOULD = 3
    COULD = 2
    WONT = 1


@dataclass
class Requirement:
    requirement_id: str
    description: str
    priority: RequirementPriority
    acceptance_criteria: List[str]
    source: str

    def is_valid(self) -> bool:
        return bool(
            self.requirement_id.strip()
            and self.description.strip()
            and self.acceptance_criteria
        )


def demonstrate_requirements() -> List[Requirement]:
    print_section("4. Requirements and Acceptance Criteria")

    requirements = [
        Requirement(
            "REQ-001",
            "Users can authenticate securely.",
            RequirementPriority.MUST,
            [
                "Valid credentials allow access.",
                "Invalid credentials are rejected.",
                "Passwords are never displayed in plain text.",
            ],
            "Security and product teams",
        ),
        Requirement(
            "REQ-002",
            "Users can create portfolio reports.",
            RequirementPriority.MUST,
            [
                "A report can be created from selected holdings.",
                "The report includes a timestamp.",
                "The report can be downloaded.",
            ],
            "Product Owner",
        ),
        Requirement(
            "REQ-003",
            "Users can configure dashboard colors.",
            RequirementPriority.COULD,
            [
                "A user can select from available themes.",
            ],
            "User feedback",
        ),
    ]

    for requirement in requirements:
        print(
            f"{requirement.requirement_id} | "
            f"{requirement.priority.name} | "
            f"{requirement.description}"
        )
        for criterion in requirement.acceptance_criteria:
            print(f"    Acceptance: {criterion}")

    assert all(requirement.is_valid() for requirement in requirements)
    return requirements


# ---------------------------------------------------------------------------
# 6. WORK BREAKDOWN STRUCTURE
# ---------------------------------------------------------------------------

@dataclass
class WorkPackage:
    code: str
    name: str
    description: str
    estimated_hours: float

    def validate(self) -> None:
        if self.estimated_hours <= 0:
            raise ValueError(f"{self.code} must have a positive estimate.")


def demonstrate_wbs() -> List[WorkPackage]:
    print_section("5. Work Breakdown Structure")

    work_packages = [
        WorkPackage("1.1", "Requirements", "Gather and validate requirements", 32),
        WorkPackage("1.2", "Architecture", "Design system architecture", 40),
        WorkPackage("2.1", "Backend", "Implement service layer and APIs", 96),
        WorkPackage("2.2", "Frontend", "Implement dashboard interface", 96),
        WorkPackage("2.3", "Database", "Design and implement database", 56),
        WorkPackage("3.1", "Testing", "Functional and integration testing", 64),
        WorkPackage("3.2", "Security", "Security testing and remediation", 40),
        WorkPackage("4.1", "Deployment", "Production deployment", 24),
        WorkPackage("4.2", "Documentation", "Operational documentation", 24),
    ]

    for package in work_packages:
        package.validate()
        print(
            f"{package.code} {package.name}: "
            f"{package.estimated_hours:.0f} hours - {package.description}"
        )

    return work_packages


# ---------------------------------------------------------------------------
# 7. TASKS AND DEPENDENCIES
# ---------------------------------------------------------------------------

@dataclass
class Task:
    task_id: str
    name: str
    duration_days: int
    cost: float
    dependencies: List[str] = field(default_factory=list)
    resource: str = "Unassigned"

    def validate(self) -> None:
        if self.duration_days < 0:
            raise ValueError(f"{self.task_id}: duration cannot be negative.")
        if self.cost < 0:
            raise ValueError(f"{self.task_id}: cost cannot be negative.")


def build_tasks() -> Dict[str, Task]:
    return {
        "T1": Task(
            "T1",
            "Requirements analysis",
            4,
            1800,
            [],
            "Business Analyst",
        ),
        "T2": Task(
            "T2",
            "Architecture design",
            5,
            3000,
            ["T1"],
            "Solution Architect",
        ),
        "T3": Task(
            "T3",
            "Database implementation",
            6,
            3600,
            ["T2"],
            "Database Engineer",
        ),
        "T4": Task(
            "T4",
            "Backend implementation",
            10,
            7200,
            ["T2"],
            "Backend Engineer",
        ),
        "T5": Task(
            "T5",
            "Frontend implementation",
            9,
            6300,
            ["T2"],
            "Frontend Engineer",
        ),
        "T6": Task(
            "T6",
            "Integration testing",
            5,
            3200,
            ["T3", "T4", "T5"],
            "QA Engineer",
        ),
        "T7": Task(
            "T7",
            "Security testing",
            4,
            2800,
            ["T6"],
            "Security Engineer",
        ),
        "T8": Task(
            "T8",
            "Production deployment",
            2,
            1600,
            ["T7"],
            "DevOps Engineer",
        ),
        "T9": Task(
            "T9",
            "Operational documentation",
            3,
            1200,
            ["T6"],
            "Technical Writer",
        ),
    }


# ---------------------------------------------------------------------------
# 8. DEPENDENCY VALIDATION AND TOPOLOGICAL SORT
# ---------------------------------------------------------------------------

def validate_dependencies(tasks: Dict[str, Task]) -> List[str]:
    errors: List[str] = []

    for task in tasks.values():
        for dependency in task.dependencies:
            if dependency not in tasks:
                errors.append(
                    f"{task.task_id} depends on unknown task {dependency}."
                )

    # Detect cycles with DFS.
    visiting: Set[str] = set()
    visited: Set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise ValueError(f"Circular dependency detected at {task_id}.")
        if task_id in visited:
            return

        visiting.add(task_id)
        for dependency in tasks[task_id].dependencies:
            if dependency in tasks:
                visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in tasks:
        visit(task_id)

    return errors


def topological_order(tasks: Dict[str, Task]) -> List[str]:
    indegree = {task_id: 0 for task_id in tasks}
    successors: Dict[str, List[str]] = defaultdict(list)

    for task in tasks.values():
        for dependency in task.dependencies:
            if dependency not in tasks:
                raise ValueError(f"Unknown dependency: {dependency}")
            indegree[task.task_id] += 1
            successors[dependency].append(task.task_id)

    queue = deque(
        sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    )
    result: List[str] = []

    while queue:
        current = queue.popleft()
        result.append(current)

        for successor in sorted(successors[current]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)

    if len(result) != len(tasks):
        raise ValueError("The dependency graph contains a cycle.")

    return result


# ---------------------------------------------------------------------------
# 9. CPM: CRITICAL PATH METHOD
# ---------------------------------------------------------------------------

@dataclass
class ScheduleEntry:
    task_id: str
    earliest_start: int
    earliest_finish: int
    latest_start: int
    latest_finish: int
    float_days: int

    @property
    def critical(self) -> bool:
        return self.float_days == 0


def critical_path_analysis(tasks: Dict[str, Task]) -> Dict[str, ScheduleEntry]:
    order = topological_order(tasks)
    earliest_start: Dict[str, int] = {}
    earliest_finish: Dict[str, int] = {}

    for task_id in order:
        task = tasks[task_id]
        if task.dependencies:
            earliest_start[task_id] = max(
                earliest_finish[dependency]
                for dependency in task.dependencies
            )
        else:
            earliest_start[task_id] = 0

        earliest_finish[task_id] = (
            earliest_start[task_id] + task.duration_days
        )

    project_duration = max(earliest_finish.values(), default=0)

    latest_finish: Dict[str, int] = {}
    latest_start: Dict[str, int] = {}

    for task_id in reversed(order):
        task = tasks[task_id]
        successors = [
            successor
            for successor in tasks
            if task_id in tasks[successor].dependencies
        ]

        if not successors:
            latest_finish[task_id] = project_duration
        else:
            latest_finish[task_id] = min(
                latest_start[successor] for successor in successors
            )

        latest_start[task_id] = (
            latest_finish[task_id] - task.duration_days
        )

    schedule: Dict[str, ScheduleEntry] = {}

    for task_id in order:
        schedule[task_id] = ScheduleEntry(
            task_id,
            earliest_start[task_id],
            earliest_finish[task_id],
            latest_start[task_id],
            latest_finish[task_id],
            latest_start[task_id] - earliest_start[task_id],
        )

    return schedule


def demonstrate_critical_path(tasks: Dict[str, Task]) -> Dict[str, ScheduleEntry]:
    print_section("6. Critical Path Method")

    schedule = critical_path_analysis(tasks)

    for task_id, entry in schedule.items():
        marker = " CRITICAL" if entry.critical else ""
        print(
            f"{task_id}: ES={entry.earliest_start:2} "
            f"EF={entry.earliest_finish:2} "
            f"LS={entry.latest_start:2} "
            f"LF={entry.latest_finish:2} "
            f"Float={entry.float_days:2}{marker}"
        )

    critical_tasks = [
        task_id for task_id, entry in schedule.items() if entry.critical
    ]

    duration = max(entry.earliest_finish for entry in schedule.values())

    print(f"\nPlanned project duration: {duration} working days")
    print("Critical-path tasks:", " -> ".join(critical_tasks))

    return schedule


# ---------------------------------------------------------------------------
# 10. CALENDAR SCHEDULING
# ---------------------------------------------------------------------------

def add_working_days(start: date, working_days: int) -> date:
    """
    Add working days while skipping Saturday and Sunday.

    A duration of zero returns the same date.
    """
    if working_days < 0:
        raise ValueError("working_days cannot be negative.")

    current = start
    remaining = working_days

    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1

    return current


def demonstrate_calendar_schedule(
    tasks: Dict[str, Task],
    schedule: Dict[str, ScheduleEntry],
) -> None:
    print_section("7. Calendar-Based Schedule")

    project_start = date(2026, 10, 5)

    for task_id, entry in schedule.items():
        start = add_working_days(project_start, entry.earliest_start)
        finish = add_working_days(project_start, entry.earliest_finish)
        print(
            f"{task_id} {tasks[task_id].name}: "
            f"{start.isoformat()} -> {finish.isoformat()}"
        )


# ---------------------------------------------------------------------------
# 11. ESTIMATION
# ---------------------------------------------------------------------------

def three_point_estimate(
    optimistic: float,
    most_likely: float,
    pessimistic: float,
) -> Tuple[float, float]:
    """
    PERT-style expected estimate:
        E = (O + 4M + P) / 6

    Approximate standard deviation:
        SD = (P - O) / 6
    """
    if not (
        optimistic >= 0
        and most_likely >= 0
        and pessimistic >= 0
    ):
        raise ValueError("Estimates cannot be negative.")

    if not (optimistic <= most_likely <= pessimistic):
        raise ValueError("Expected ordering is O <= M <= P.")

    expected = (
        optimistic + 4 * most_likely + pessimistic
    ) / 6

    standard_deviation = (pessimistic - optimistic) / 6

    return expected, standard_deviation


def demonstrate_estimation() -> None:
    print_section("8. Estimation Techniques")

    scenarios = [
        ("API development", 6, 10, 18),
        ("Security testing", 2, 4, 9),
        ("Production deployment", 1, 2, 4),
    ]

    for name, optimistic, likely, pessimistic in scenarios:
        expected, standard_deviation = three_point_estimate(
            optimistic,
            likely,
            pessimistic,
        )

        print(
            f"{name}: expected={expected:.2f} days, "
            f"uncertainty={standard_deviation:.2f}"
        )

    print("\nEstimation should represent uncertainty rather than pretend")
    print("that an early number is perfectly precise.")


# ---------------------------------------------------------------------------
# 12. COST ESTIMATION
# ---------------------------------------------------------------------------

def total_project_cost(tasks: Dict[str, Task]) -> float:
    return sum(task.cost for task in tasks.values())


def demonstrate_cost_estimation(tasks: Dict[str, Task]) -> None:
    print_section("9. Cost Estimation")

    total = total_project_cost(tasks)

    print(f"Estimated direct task cost: ${total:,.2f}")

    contingency_rate = 0.10
    contingency = total * contingency_rate
    planned_budget = total + contingency

    print(f"10% contingency: ${contingency:,.2f}")
    print(f"Planning budget: ${planned_budget:,.2f}")

    print("\nContingency is not free money.")
    print("It exists to absorb identified uncertainty and selected risks.")


# ---------------------------------------------------------------------------
# 13. RESOURCE PLANNING
# ---------------------------------------------------------------------------

@dataclass
class Resource:
    name: str
    role: str
    capacity_hours_per_week: float
    assigned_hours: float = 0.0

    @property
    def utilization(self) -> float:
        if self.capacity_hours_per_week == 0:
            return 0.0
        return self.assigned_hours / self.capacity_hours_per_week


def demonstrate_resource_planning() -> None:
    print_section("10. Resource Planning")

    resources = [
        Resource("Asha", "Backend Engineer", 40),
        Resource("Ravi", "Frontend Engineer", 40),
        Resource("Mina", "QA Engineer", 40),
        Resource("Dev", "Security Engineer", 32),
    ]

    assignments = {
        "Asha": 34,
        "Ravi": 38,
        "Mina": 30,
        "Dev": 36,
    }

    for resource in resources:
        resource.assigned_hours = assignments[resource.name]
        utilization = resource.utilization * 100

        status = (
            "OVER CAPACITY"
            if resource.assigned_hours > resource.capacity_hours_per_week
            else "Within capacity"
        )

        print(
            f"{resource.name:8} | {resource.role:20} | "
            f"{utilization:6.1f}% | {status}"
        )


# ---------------------------------------------------------------------------
# 14. RISK MANAGEMENT
# ---------------------------------------------------------------------------

class RiskResponse(Enum):
    AVOID = "Avoid"
    MITIGATE = "Mitigate"
    TRANSFER = "Transfer"
    ACCEPT = "Accept"


@dataclass
class Risk:
    risk_id: str
    description: str
    probability: float
    impact: float
    response: RiskResponse
    mitigation: str

    @property
    def exposure(self) -> float:
        return self.probability * self.impact

    def validate(self) -> None:
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1.")
        if self.impact < 0:
            raise ValueError("Impact cannot be negative.")


def demonstrate_risk_management() -> List[Risk]:
    print_section("11. Risk Management")

    risks = [
        Risk(
            "R-001",
            "Third-party API becomes unavailable",
            0.30,
            8,
            RiskResponse.MITIGATE,
            "Create a fallback data source and cache recent results.",
        ),
        Risk(
            "R-002",
            "Security review discovers critical vulnerabilities",
            0.20,
            10,
            RiskResponse.MITIGATE,
            "Perform security testing before the final release gate.",
        ),
        Risk(
            "R-003",
            "Key developer becomes unavailable",
            0.15,
            7,
            RiskResponse.MITIGATE,
            "Document critical components and cross-train team members.",
        ),
    ]

    for risk in risks:
        risk.validate()
        print(
            f"{risk.risk_id}: exposure={risk.exposure:.2f}; "
            f"response={risk.response.value}; "
            f"mitigation={risk.mitigation}"
        )

    return risks


# ---------------------------------------------------------------------------
# 15. ISSUE MANAGEMENT
# ---------------------------------------------------------------------------

class IssueStatus(Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


@dataclass
class Issue:
    issue_id: str
    description: str
    severity: int
    owner: str
    status: IssueStatus = IssueStatus.OPEN

    def resolve(self) -> None:
        self.status = IssueStatus.RESOLVED


def demonstrate_issue_management() -> None:
    print_section("12. Issues and Corrective Action")

    issue = Issue(
        "ISS-101",
        "Report export fails for empty portfolios.",
        7,
        "QA Engineer",
    )

    print(
        f"{issue.issue_id}: severity={issue.severity}, "
        f"status={issue.status.value}"
    )

    issue.resolve()

    print(
        f"{issue.issue_id}: status after correction="
        f"{issue.status.value}"
    )


# ---------------------------------------------------------------------------
# 16. CHANGE CONTROL
# ---------------------------------------------------------------------------

@dataclass
class ChangeRequest:
    change_id: str
    description: str
    scope_effect: float
    schedule_effect_days: int
    cost_effect: float
    approved: bool = False

    def approve(self) -> None:
        self.approved = True


def demonstrate_change_control() -> None:
    print_section("13. Change Control")

    change = ChangeRequest(
        "CR-001",
        "Add multi-currency portfolio support.",
        0.12,
        6,
        8500,
    )

    print(f"Change: {change.description}")
    print(f"Scope impact: {change.scope_effect * 100:.1f}%")
    print(f"Schedule impact: {change.schedule_effect_days} days")
    print(f"Cost impact: ${change.cost_effect:,.2f}")
    print(f"Approved: {change.approved}")

    change.approve()
    print(f"Approved after review: {change.approved}")

    print(
        "\nA change should be assessed against scope, schedule, cost, "
        "quality, risk, resources, and acceptance criteria."
    )


# ---------------------------------------------------------------------------
# 17. PRIORITIZATION
# ---------------------------------------------------------------------------

@dataclass
class BacklogItem:
    item_id: str
    name: str
    business_value: int
    urgency: int
    effort: int
    risk_reduction: int

    @property
    def priority_score(self) -> float:
        denominator = max(self.effort, 1)
        return (
            self.business_value
            + self.urgency
            + self.risk_reduction
        ) / denominator


def demonstrate_prioritization() -> None:
    print_section("14. Backlog Prioritization")

    backlog = [
        BacklogItem("B1", "Secure authentication", 10, 10, 5, 10),
        BacklogItem("B2", "Dashboard filters", 7, 5, 4, 2),
        BacklogItem("B3", "Export to CSV", 6, 6, 2, 1),
        BacklogItem("B4", "Custom themes", 3, 2, 5, 0),
    ]

    for item in sorted(
        backlog,
        key=lambda current: current.priority_score,
        reverse=True,
    ):
        print(
            f"{item.item_id}: {item.name:24} "
            f"score={item.priority_score:.2f}"
        )

    print(
        "\nThe score is a planning heuristic, not an objective truth. "
        "Teams should document the factors behind prioritization."
    )


# ---------------------------------------------------------------------------
# 18. AGILE SPRINT PLANNING
# ---------------------------------------------------------------------------

@dataclass
class SprintItem:
    item_id: str
    description: str
    story_points: int
    acceptance_criteria: List[str]
    done: bool = False


@dataclass
class Sprint:
    sprint_number: int
    capacity_points: int
    items: List[SprintItem] = field(default_factory=list)

    @property
    def committed_points(self) -> int:
        return sum(item.story_points for item in self.items)

    @property
    def remaining_points(self) -> int:
        return self.capacity_points - self.committed_points

    def add_item(self, item: SprintItem) -> bool:
        if self.committed_points + item.story_points > self.capacity_points:
            return False
        self.items.append(item)
        return True


def demonstrate_sprint_planning() -> None:
    print_section("15. Agile Sprint Planning")

    sprint = Sprint(1, 20)

    candidates = [
        SprintItem(
            "US-1",
            "Secure login",
            5,
            ["Valid users can sign in.", "Invalid credentials are rejected."],
        ),
        SprintItem(
            "US-2",
            "Portfolio dashboard",
            8,
            ["Holdings are displayed.", "Values are calculated correctly."],
        ),
        SprintItem(
            "US-3",
            "CSV export",
            3,
            ["CSV contains required columns."],
        ),
        SprintItem(
            "US-4",
            "Dark theme",
            5,
            ["Theme persists after refresh."],
        ),
    ]

    for item in candidates:
        accepted = sprint.add_item(item)
        print(
            f"{item.item_id}: "
            f"{'committed' if accepted else 'not committed'}"
        )

    print(f"Committed points: {sprint.committed_points}")
    print(f"Remaining capacity: {sprint.remaining_points}")


# ---------------------------------------------------------------------------
# 19. KANBAN FLOW
# ---------------------------------------------------------------------------

class WorkState(Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    REVIEW = "Review"
    DONE = "Done"


@dataclass
class KanbanItem:
    item_id: str
    name: str
    state: WorkState = WorkState.TODO


def demonstrate_kanban() -> None:
    print_section("16. Kanban-Style Flow")

    items = [
        KanbanItem("K1", "API authentication"),
        KanbanItem("K2", "Database indexing"),
        KanbanItem("K3", "Dashboard testing"),
        KanbanItem("K4", "Deployment documentation"),
    ]

    items[0].state = WorkState.IN_PROGRESS
    items[1].state = WorkState.REVIEW
    items[2].state = WorkState.DONE

    counts = defaultdict(int)

    for item in items:
        counts[item.state.value] += 1
        print(f"{item.item_id}: {item.name} -> {item.state.value}")

    print("\nWork in each state:")
    for state, count in counts.items():
        print(f"{state}: {count}")


# ---------------------------------------------------------------------------
# 20. PROJECT PERFORMANCE MEASUREMENT
# ---------------------------------------------------------------------------

@dataclass
class PerformanceSnapshot:
    planned_value: float
    earned_value: float
    actual_cost: float

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

    @property
    def schedule_variance(self) -> float:
        return self.earned_value - self.planned_value

    @property
    def cost_variance(self) -> float:
        return self.earned_value - self.actual_cost


def demonstrate_performance_metrics() -> None:
    print_section("17. Project Performance Metrics")

    snapshot = PerformanceSnapshot(
        planned_value=50000,
        earned_value=45000,
        actual_cost=52000,
    )

    print(f"Schedule variance: ${snapshot.schedule_variance:,.2f}")
    print(f"Cost variance: ${snapshot.cost_variance:,.2f}")
    print(f"SPI: {snapshot.schedule_performance_index:.3f}")
    print(f"CPI: {snapshot.cost_performance_index:.3f}")

    print(
        "\nThese metrics should be interpreted together with scope, "
        "quality, assumptions, and the measurement method."
    )


# ---------------------------------------------------------------------------
# 21. RESOURCE-CONSTRAINED SCHEDULING
# ---------------------------------------------------------------------------

def calculate_resource_load(
    tasks: Dict[str, Task],
) -> Dict[str, int]:
    load: Dict[str, int] = defaultdict(int)

    for task in tasks.values():
        load[task.resource] += task.duration_days

    return dict(load)


def demonstrate_resource_load(tasks: Dict[str, Task]) -> None:
    print_section("18. Resource Load")

    load = calculate_resource_load(tasks)

    for resource, days in sorted(load.items()):
        print(f"{resource:22}: {days:3} task-days")


# ---------------------------------------------------------------------------
# 22. SCENARIO ANALYSIS
# ---------------------------------------------------------------------------

def scenario_analysis(tasks: Dict[str, Task]) -> None:
    print_section("19. Scenario Analysis")

    baseline = critical_path_analysis(tasks)
    baseline_duration = max(
        entry.earliest_finish for entry in baseline.values()
    )

    print(f"Baseline duration: {baseline_duration} days")

    accelerated_tasks = {
        task_id: Task(
            task.task_id,
            task.name,
            max(1, round(task.duration_days * 0.8)),
            task.cost * 1.20,
            task.dependencies.copy(),
            task.resource,
        )
        for task_id, task in tasks.items()
    }

    accelerated = critical_path_analysis(accelerated_tasks)
    accelerated_duration = max(
        entry.earliest_finish for entry in accelerated.values()
    )

    baseline_cost = total_project_cost(tasks)
    accelerated_cost = total_project_cost(accelerated_tasks)

    print(f"Accelerated duration: {accelerated_duration} days")
    print(f"Baseline cost: ${baseline_cost:,.2f}")
    print(f"Accelerated cost: ${accelerated_cost:,.2f}")

    print(
        "\nThis illustrates a planning trade-off: reducing duration "
        "can require additional resources or higher cost."
    )


# ---------------------------------------------------------------------------
# 23. PROJECT HEALTH
# ---------------------------------------------------------------------------

@dataclass
class ProjectHealth:
    schedule_index: float
    cost_index: float
    open_high_risks: int
    unresolved_critical_issues: int
    requirement_completion: float

    def indicators(self) -> Dict[str, str]:
        indicators: Dict[str, str] = {}

        indicators["Schedule"] = (
            "Attention"
            if self.schedule_index < 0.90
            else "Monitor"
            if self.schedule_index < 1.00
            else "On plan or ahead"
        )

        indicators["Cost"] = (
            "Attention"
            if self.cost_index < 0.90
            else "Monitor"
            if self.cost_index < 1.00
            else "Within plan"
        )

        indicators["Risk"] = (
            "Attention"
            if self.open_high_risks >= 3
            else "Monitor"
            if self.open_high_risks > 0
            else "Controlled"
        )

        indicators["Critical issues"] = (
            "Attention"
            if self.unresolved_critical_issues > 0
            else "Controlled"
        )

        indicators["Requirements"] = (
            "Attention"
            if self.requirement_completion < 0.70
            else "Monitor"
            if self.requirement_completion < 0.90
            else "Strong"
        )

        return indicators


def demonstrate_project_health() -> None:
    print_section("20. Project Health Dashboard")

    health = ProjectHealth(
        schedule_index=0.94,
        cost_index=0.97,
        open_high_risks=2,
        unresolved_critical_issues=0,
        requirement_completion=0.82,
    )

    for category, status in health.indicators().items():
        print(f"{category:18}: {status}")


# ---------------------------------------------------------------------------
# 24. TRACEABILITY
# ---------------------------------------------------------------------------

@dataclass
class TraceabilityRecord:
    requirement_id: str
    task_ids: List[str]
    test_ids: List[str]
    acceptance_status: str


def demonstrate_traceability() -> None:
    print_section("21. Requirements Traceability")

    records = [
        TraceabilityRecord(
            "REQ-001",
            ["T4", "T6", "T7"],
            ["TEST-101", "TEST-102"],
            "Accepted",
        ),
        TraceabilityRecord(
            "REQ-002",
            ["T3", "T4", "T5", "T6"],
            ["TEST-201", "TEST-202"],
            "In review",
        ),
    ]

    for record in records:
        print(
            f"{record.requirement_id}: "
            f"tasks={record.task_ids}; "
            f"tests={record.test_ids}; "
            f"status={record.acceptance_status}"
        )


# ---------------------------------------------------------------------------
# 25. QUALITY GATES
# ---------------------------------------------------------------------------

@dataclass
class QualityGate:
    name: str
    required: bool
    passed: bool
    evidence: str

    def can_proceed(self) -> bool:
        return not self.required or self.passed


def demonstrate_quality_gates() -> None:
    print_section("22. Quality Gates")

    gates = [
        QualityGate(
            "Functional tests",
            True,
            True,
            "All required tests passed.",
        ),
        QualityGate(
            "Security review",
            True,
            True,
            "No unresolved critical findings.",
        ),
        QualityGate(
            "Documentation review",
            True,
            False,
            "Operations guide requires final update.",
        ),
    ]

    for gate in gates:
        print(
            f"{gate.name}: "
            f"{'PASS' if gate.passed else 'FAIL'}"
        )

    release_allowed = all(gate.can_proceed() for gate in gates)

    print(f"Release gate result: {'PASS' if release_allowed else 'BLOCKED'}")


# ---------------------------------------------------------------------------
# 26. PLANNING AN END-TO-END PROJECT
# ---------------------------------------------------------------------------

def build_project_charter() -> ProjectCharter:
    return ProjectCharter(
        project_name="Portfolio Analytics Platform",
        purpose="Provide secure portfolio analysis and reporting.",
        sponsor="Chief Product Officer",
        project_manager="Project Manager",
        start_date=date(2026, 10, 5),
        target_date=date(2026, 11, 30),
        budget=65000,
        in_scope=[
            "Authentication",
            "Portfolio dashboard",
            "Reporting",
            "Security testing",
            "Production deployment",
        ],
        out_of_scope=[
            "Native mobile application",
            "International tax calculations",
            "Cryptocurrency exchange execution",
        ],
        assumptions=[
            "Core team is available throughout the project.",
            "Required market data is available.",
            "Security review can be completed before release.",
        ],
        constraints=[
            "Fixed release window",
            "Limited specialist security capacity",
            "Controlled production access",
        ],
    )


def produce_project_plan() -> None:
    print_section("23. Integrated Project Plan")

    charter = build_project_charter()
    errors = charter.validate()

    if errors:
        for error in errors:
            print("Validation error:", error)
        return

    charter.display()

    tasks = build_tasks()

    dependency_errors = validate_dependencies(tasks)

    if dependency_errors:
        for error in dependency_errors:
            print("Dependency error:", error)
        return

    order = topological_order(tasks)

    print("\nExecution order:")
    print(" -> ".join(order))

    schedule = critical_path_analysis(tasks)

    print(
        f"\nProject duration from dependency model: "
        f"{max(entry.earliest_finish for entry in schedule.values())} days"
    )

    print(f"Direct estimated cost: ${total_project_cost(tasks):,.2f}")


# ---------------------------------------------------------------------------
# 27. EDGE CASES AND FAILURE CONDITIONS
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print_section("24. Edge Cases and Validation")

    try:
        three_point_estimate(10, 5, 20)
    except ValueError as error:
        print("Invalid estimate correctly rejected:", error)

    try:
        add_working_days(date(2026, 10, 5), -1)
    except ValueError as error:
        print("Negative working duration correctly rejected:", error)

    cyclic_tasks = {
        "A": Task("A", "Task A", 2, 100, ["B"]),
        "B": Task("B", "Task B", 2, 100, ["A"]),
    }

    try:
        topological_order(cyclic_tasks)
    except ValueError as error:
        print("Circular dependency correctly rejected:", error)

    missing_dependency = {
        "A": Task("A", "Task A", 2, 100, ["UNKNOWN"]),
    }

    try:
        topological_order(missing_dependency)
    except ValueError as error:
        print("Missing dependency correctly rejected:", error)


# ---------------------------------------------------------------------------
# 28. PROJECT PLANNING BEST PRACTICES
# ---------------------------------------------------------------------------

def print_best_practices() -> None:
    print_section("25. Project Planning Best Practices")

    practices = [
        "Define measurable outcomes before decomposing work.",
        "Separate project scope from implementation details.",
        "Document assumptions and constraints explicitly.",
        "Break large deliverables into manageable work packages.",
        "Represent dependencies explicitly rather than relying on memory.",
        "Estimate uncertainty rather than presenting false precision.",
        "Identify the critical path for schedule-sensitive work.",
        "Plan resource capacity before committing work.",
        "Treat risks differently from issues.",
        "Control scope changes through impact assessment.",
        "Define acceptance criteria before declaring work complete.",
        "Maintain traceability from requirements to tests.",
        "Use baselines to compare planned and actual performance.",
        "Review the plan as new information becomes available.",
        "Do not optimize schedule at the expense of security or required quality.",
        "Keep planning artifacts understandable to both technical and business stakeholders.",
    ]

    for practice in practices:
        print(f"- {practice}")


# ---------------------------------------------------------------------------
# 29. TESTS
# ---------------------------------------------------------------------------

def run_tests() -> None:
    print_section("26. Automated Validation Tests")

    assert add_working_days(date(2026, 10, 5), 0) == date(2026, 10, 5)
    assert add_working_days(date(2026, 10, 5), 5) == date(2026, 10, 12)

    expected, deviation = three_point_estimate(1, 2, 3)
    assert expected == 2
    assert deviation > 0

    tasks = build_tasks()
    order = topological_order(tasks)

    assert order.index("T1") < order.index("T2")
    assert order.index("T2") < order.index("T4")
    assert order.index("T4") < order.index("T6")

    schedule = critical_path_analysis(tasks)

    assert all(entry.earliest_start <= entry.earliest_finish
               for entry in schedule.values())

    performance = PerformanceSnapshot(100, 80, 90)
    assert performance.schedule_variance == -20
    assert performance.cost_variance == -10

    print("All tests passed.")


# ---------------------------------------------------------------------------
# 30. MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print_section("PROJECT PLANNING: COMPLETE PRACTICAL STUDY PROGRAM")

    explain_fundamentals()
    demonstrate_objectives()
    demonstrate_stakeholders()
    demonstrate_requirements()
    demonstrate_wbs()

    tasks = build_tasks()

    dependency_errors = validate_dependencies(tasks)
    assert not dependency_errors

    schedule = demonstrate_critical_path(tasks)
    demonstrate_calendar_schedule(tasks, schedule)
    demonstrate_estimation()
    demonstrate_cost_estimation(tasks)
    demonstrate_resource_planning()
    demonstrate_risk_management()
    demonstrate_issue_management()
    demonstrate_change_control()
    demonstrate_prioritization()
    demonstrate_sprint_planning()
    demonstrate_kanban()
    demonstrate_performance_metrics()
    demonstrate_resource_load(tasks)
    scenario_analysis(tasks)
    demonstrate_project_health()
    demonstrate_traceability()
    demonstrate_quality_gates()
    produce_project_plan()
    demonstrate_edge_cases()
    print_best_practices()
    run_tests()

    print_section("END OF PROJECT PLANNING STUDY PROGRAM")
    print("The program completed successfully.")


if __name__ == "__main__":
    main()
