"""
Work Packages: Understanding Manageable Units of Work

A self-contained study program covering work packages from beginner concepts
through practical planning, decomposition, estimation, dependencies, risk,
validation, progress tracking, metrics, and an advanced project-planning case.

The program uses a software-product delivery scenario to make abstract project
management concepts executable and measurable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

class WorkStatus(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    COMPLETE = "Complete"


class Priority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class Deliverable:
    """A tangible output produced by a work package."""
    name: str
    acceptance_criteria: List[str]

    def is_well_defined(self) -> bool:
        return bool(self.name.strip()) and bool(self.acceptance_criteria)


@dataclass
class WorkPackage:
    """
    A work package is a manageable unit of project work.

    It should be small enough to estimate, schedule, assign, monitor, and
    control, while remaining large enough to produce a meaningful result.
    """
    package_id: str
    name: str
    description: str
    owner: str
    estimated_hours: float
    priority: Priority
    status: WorkStatus = WorkStatus.NOT_STARTED
    dependencies: Set[str] = field(default_factory=set)
    deliverables: List[Deliverable] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    actual_hours: float = 0.0
    progress_percent: float = 0.0

    def validate(self) -> List[str]:
        errors = []

        if not self.package_id.strip():
            errors.append("Package ID is required.")

        if not self.name.strip():
            errors.append("Package name is required.")

        if not self.owner.strip():
            errors.append("An owner is required.")

        if self.estimated_hours <= 0:
            errors.append("Estimated hours must be greater than zero.")

        if not 0 <= self.progress_percent <= 100:
            errors.append("Progress must be between 0 and 100.")

        for deliverable in self.deliverables:
            if not deliverable.is_well_defined():
                errors.append(
                    f"Deliverable '{deliverable.name}' has incomplete "
                    "acceptance criteria."
                )

        return errors

    def update_progress(self, progress: float, actual_hours: float) -> None:
        """Update progress while protecting basic data invariants."""
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100.")

        if actual_hours < 0:
            raise ValueError("Actual hours cannot be negative.")

        self.progress_percent = progress
        self.actual_hours = actual_hours

        if progress == 100:
            self.status = WorkStatus.COMPLETE
        elif progress > 0:
            self.status = WorkStatus.IN_PROGRESS
        else:
            self.status = WorkStatus.NOT_STARTED

    def schedule_days(self, hours_per_day: float = 8.0) -> int:
        if hours_per_day <= 0:
            raise ValueError("hours_per_day must be positive.")
        return max(1, int((self.estimated_hours + hours_per_day - 1) // hours_per_day))

    def estimate_variance(self) -> float:
        """Positive value means actual effort exceeded the estimate."""
        return self.actual_hours - self.estimated_hours

    def is_over_budget(self) -> bool:
        return self.actual_hours > self.estimated_hours


# ---------------------------------------------------------------------------
# 2. BASIC EXAMPLE
# ---------------------------------------------------------------------------

def beginner_example() -> WorkPackage:
    package = WorkPackage(
        package_id="WP-001",
        name="Design Login Interface",
        description="Create the approved interface for user authentication.",
        owner="UI Designer",
        estimated_hours=16,
        priority=Priority.HIGH,
        deliverables=[
            Deliverable(
                name="Approved login screen",
                acceptance_criteria=[
                    "Desktop layout is responsive.",
                    "Validation states are documented.",
                    "Design is approved by the product owner.",
                ],
            )
        ],
    )

    print("\n=== BEGINNER EXAMPLE ===")
    print(f"Package: {package.name}")
    print(f"Owner: {package.owner}")
    print(f"Estimate: {package.estimated_hours} hours")
    print(f"Scheduled duration: {package.schedule_days()} working days")
    print(f"Validation errors: {package.validate()}")

    package.update_progress(50, 7)
    print(f"Status after update: {package.status.value}")
    print(f"Progress: {package.progress_percent}%")

    return package


# ---------------------------------------------------------------------------
# 3. WORK PACKAGE VS RELATED CONCEPTS
# ---------------------------------------------------------------------------

def explain_relationships() -> None:
    print("\n=== WORK STRUCTURE RELATIONSHIPS ===")

    relationships = {
        "Project": "The complete temporary effort with a defined objective.",
        "Phase": "A major stage of the project lifecycle.",
        "Workstream": "A related stream of activities, often crossing phases.",
        "Work Package": "A manageable unit that can be estimated and controlled.",
        "Activity": "A specific action performed to complete work.",
        "Task": "A detailed piece of work within an activity.",
        "Deliverable": "A measurable output produced by work.",
        "Milestone": "A significant point or event with zero work duration.",
    }

    for concept, meaning in relationships.items():
        print(f"{concept:15} -> {meaning}")


# ---------------------------------------------------------------------------
# 4. DECOMPOSITION
# ---------------------------------------------------------------------------

def decompose_project() -> List[WorkPackage]:
    """
    Decompose a product launch into manageable packages.

    Good decomposition avoids both:
    - packages that are so large that ownership and progress become unclear
    - packages that are so tiny that administration overwhelms useful work
    """
    packages = [
        WorkPackage(
            "WP-101",
            "Requirements Analysis",
            "Define functional and non-functional requirements.",
            "Business Analyst",
            24,
            Priority.CRITICAL,
            deliverables=[
                Deliverable(
                    "Requirements baseline",
                    ["Business owner approval", "Requirements traceability exists"],
                )
            ],
        ),
        WorkPackage(
            "WP-102",
            "UX Design",
            "Design user journeys and interface specifications.",
            "UX Lead",
            32,
            Priority.HIGH,
            dependencies={"WP-101"},
            deliverables=[
                Deliverable(
                    "UX specification",
                    ["User journeys approved", "Accessibility requirements documented"],
                )
            ],
        ),
        WorkPackage(
            "WP-103",
            "Backend API",
            "Implement authentication and product APIs.",
            "Backend Engineer",
            64,
            Priority.CRITICAL,
            dependencies={"WP-101"},
            deliverables=[
                Deliverable(
                    "API service",
                    ["Authentication works", "API tests pass"],
                )
            ],
        ),
        WorkPackage(
            "WP-104",
            "Frontend Implementation",
            "Implement the approved product interface.",
            "Frontend Engineer",
            56,
            Priority.HIGH,
            dependencies={"WP-102", "WP-103"},
            deliverables=[
                Deliverable(
                    "Web application",
                    ["Core journeys work", "Responsive layouts pass testing"],
                )
            ],
        ),
        WorkPackage(
            "WP-105",
            "Integration Testing",
            "Validate integrated frontend and backend behavior.",
            "QA Engineer",
            40,
            Priority.HIGH,
            dependencies={"WP-104"},
            deliverables=[
                Deliverable(
                    "Integration test report",
                    ["Critical scenarios pass", "Defects are dispositioned"],
                )
            ],
        ),
        WorkPackage(
            "WP-106",
            "Production Deployment",
            "Deploy the approved application to production.",
            "DevOps Engineer",
            16,
            Priority.CRITICAL,
            dependencies={"WP-105"},
            deliverables=[
                Deliverable(
                    "Production release",
                    ["Health checks pass", "Rollback procedure is verified"],
                )
            ],
        ),
    ]

    return packages


# ---------------------------------------------------------------------------
# 5. WORK PACKAGE QUALITY TESTS
# ---------------------------------------------------------------------------

def evaluate_package_quality(package: WorkPackage) -> Dict[str, bool]:
    """
    A practical quality checklist.

    A strong package normally has:
    - a unique identity
    - a clear output
    - one accountable owner
    - a reasonable estimate
    - acceptance criteria
    - known dependencies
    - measurable completion
    """
    return {
        "has_id": bool(package.package_id.strip()),
        "has_clear_name": bool(package.name.strip()),
        "has_owner": bool(package.owner.strip()),
        "has_positive_estimate": package.estimated_hours > 0,
        "has_deliverable": bool(package.deliverables),
        "has_acceptance_criteria": all(
            item.is_well_defined() for item in package.deliverables
        ),
        "has_valid_progress": 0 <= package.progress_percent <= 100,
    }


# ---------------------------------------------------------------------------
# 6. DEPENDENCY GRAPH AND TOPOLOGICAL ORDER
# ---------------------------------------------------------------------------

class DependencyGraph:
    """Directed graph used to model work-package dependencies."""

    def __init__(self, packages: Iterable[WorkPackage]):
        self.packages: Dict[str, WorkPackage] = {
            package.package_id: package for package in packages
        }

    def validate_references(self) -> List[str]:
        errors = []

        for package in self.packages.values():
            for dependency in package.dependencies:
                if dependency not in self.packages:
                    errors.append(
                        f"{package.package_id} references unknown dependency "
                        f"{dependency}."
                    )

        return errors

    def topological_order(self) -> List[str]:
        """Return a valid execution order or raise an error for a cycle."""
        indegree = {package_id: 0 for package_id in self.packages}
        successors: Dict[str, Set[str]] = defaultdict(set)

        for package in self.packages.values():
            for dependency in package.dependencies:
                if dependency not in self.packages:
                    raise ValueError(
                        f"Unknown dependency: {dependency}"
                    )
                successors[dependency].add(package.package_id)
                indegree[package.package_id] += 1

        queue = deque(
            package_id for package_id, degree in indegree.items() if degree == 0
        )

        order = []

        while queue:
            current = queue.popleft()
            order.append(current)

            for successor in sorted(successors[current]):
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    queue.append(successor)

        if len(order) != len(self.packages):
            raise ValueError("Dependency cycle detected.")

        return order

    def critical_path_estimate(self) -> Tuple[float, List[str]]:
        """
        Calculate the longest dependency path using package effort as duration.

        This simplified critical-path model assumes:
        - one unit of effort corresponds to one unit of scheduling duration
        - unlimited resources
        - dependencies are finish-to-start
        """
        order = self.topological_order()
        earliest_finish: Dict[str, float] = {}
        predecessor: Dict[str, Optional[str]] = {}

        for package_id in order:
            package = self.packages[package_id]

            best_finish = 0.0
            best_predecessor = None

            for dependency in package.dependencies:
                candidate = earliest_finish[dependency]
                if candidate > best_finish:
                    best_finish = candidate
                    best_predecessor = dependency

            earliest_finish[package_id] = best_finish + package.estimated_hours
            predecessor[package_id] = best_predecessor

        if not earliest_finish:
            return 0.0, []

        final_package = max(
            earliest_finish,
            key=earliest_finish.get
        )

        path = []
        current: Optional[str] = final_package

        while current is not None:
            path.append(current)
            current = predecessor[current]

        path.reverse()
        return earliest_finish[final_package], path


# ---------------------------------------------------------------------------
# 7. EFFORT, COST, AND ESTIMATION
# ---------------------------------------------------------------------------

@dataclass
class Estimate:
    optimistic_hours: float
    most_likely_hours: float
    pessimistic_hours: float

    def validate(self) -> None:
        values = (
            self.optimistic_hours,
            self.most_likely_hours,
            self.pessimistic_hours,
        )

        if any(value < 0 for value in values):
            raise ValueError("Estimates cannot be negative.")

        if not (
            self.optimistic_hours
            <= self.most_likely_hours
            <= self.pessimistic_hours
        ):
            raise ValueError(
                "Estimates must satisfy optimistic <= most likely <= pessimistic."
            )

    def pert(self) -> float:
        """Three-point PERT expected duration."""
        self.validate()
        return (
            self.optimistic_hours
            + 4 * self.most_likely_hours
            + self.pessimistic_hours
        ) / 6


def calculate_cost(hours: float, hourly_rate: float) -> float:
    if hours < 0 or hourly_rate < 0:
        raise ValueError("Hours and rates cannot be negative.")
    return hours * hourly_rate


def estimation_demo() -> None:
    print("\n=== ESTIMATION ===")

    estimate = Estimate(
        optimistic_hours=24,
        most_likely_hours=32,
        pessimistic_hours=56,
    )

    print(f"PERT estimate: {estimate.pert():.2f} hours")
    print(f"At $75/hour: ${calculate_cost(estimate.pert(), 75):,.2f}")


# ---------------------------------------------------------------------------
# 8. PROGRESS AND PERFORMANCE METRICS
# ---------------------------------------------------------------------------

def weighted_progress(packages: Iterable[WorkPackage]) -> float:
    packages = list(packages)
    total_estimate = sum(p.estimated_hours for p in packages)

    if total_estimate == 0:
        return 0.0

    weighted = sum(
        p.estimated_hours * p.progress_percent
        for p in packages
    )

    return weighted / total_estimate


def earned_value_metrics(
    planned_value: float,
    earned_value: float,
    actual_cost: float,
) -> Dict[str, float]:
    """
    Basic Earned Value Management metrics.

    PV = Planned Value
    EV = Earned Value
    AC = Actual Cost
    CPI = EV / AC
    SPI = EV / PV

    CPI < 1 indicates cost efficiency below the baseline.
    SPI < 1 indicates schedule progress below the baseline.
    """
    if planned_value < 0 or earned_value < 0 or actual_cost < 0:
        raise ValueError("EVM values cannot be negative.")

    cpi = earned_value / actual_cost if actual_cost else float("inf")
    spi = earned_value / planned_value if planned_value else float("inf")

    return {
        "planned_value": planned_value,
        "earned_value": earned_value,
        "actual_cost": actual_cost,
        "cost_performance_index": cpi,
        "schedule_performance_index": spi,
    }


# ---------------------------------------------------------------------------
# 9. RISK ANALYSIS
# ---------------------------------------------------------------------------

@dataclass
class Risk:
    risk_id: str
    description: str
    probability: float
    impact: float
    mitigation: str

    def validate(self) -> None:
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1.")
        if self.impact < 0:
            raise ValueError("Impact cannot be negative.")

    @property
    def expected_exposure(self) -> float:
        self.validate()
        return self.probability * self.impact


def risk_demo() -> None:
    print("\n=== RISK ANALYSIS ===")

    risks = [
        Risk(
            "R-01",
            "API integration takes longer than estimated.",
            0.35,
            20,
            "Prototype the highest-risk endpoint early.",
        ),
        Risk(
            "R-02",
            "Acceptance criteria change late.",
            0.20,
            30,
            "Baseline requirements and use change control.",
        ),
    ]

    for risk in risks:
        print(
            f"{risk.risk_id}: exposure={risk.expected_exposure:.2f}, "
            f"mitigation={risk.mitigation}"
        )


# ---------------------------------------------------------------------------
# 10. RESOURCE CAPACITY
# ---------------------------------------------------------------------------

def resource_load(packages: Iterable[WorkPackage]) -> Dict[str, float]:
    load: Dict[str, float] = defaultdict(float)

    for package in packages:
        load[package.owner] += package.estimated_hours

    return dict(load)


def detect_overallocation(
    packages: Iterable[WorkPackage],
    available_hours: Dict[str, float],
) -> Dict[str, float]:
    load = resource_load(packages)
    overload = {}

    for owner, hours in load.items():
        capacity = available_hours.get(owner, 0)
        if hours > capacity:
            overload[owner] = hours - capacity

    return overload


# ---------------------------------------------------------------------------
# 11. CHANGE CONTROL
# ---------------------------------------------------------------------------

@dataclass
class ChangeRequest:
    change_id: str
    description: str
    added_hours: float
    reason: str
    approved: bool = False

    def validate(self) -> None:
        if self.added_hours < 0:
            raise ValueError("Added hours cannot be negative.")
        if not self.description.strip():
            raise ValueError("Change description is required.")


def apply_change_request(
    package: WorkPackage,
    change: ChangeRequest,
) -> float:
    """
    Apply only approved changes.

    A work package baseline should not silently change because someone edits
    an estimate. Controlled changes preserve traceability.
    """
    change.validate()

    if not change.approved:
        raise ValueError("Only approved change requests may alter the baseline.")

    package.estimated_hours += change.added_hours
    return package.estimated_hours


# ---------------------------------------------------------------------------
# 12. SCHEDULING
# ---------------------------------------------------------------------------

def create_schedule(
    packages: Iterable[WorkPackage],
    start_date: date,
    hours_per_day: float = 8.0,
) -> Dict[str, Tuple[date, date]]:
    """
    Build a simple dependency-aware schedule.

    This is not a full resource-constrained scheduling algorithm. It assumes
    packages can run in parallel when dependencies permit and resources are
    available.
    """
    package_map = {p.package_id: p for p in packages}
    graph = DependencyGraph(package_map.values())
    order = graph.topological_order()

    finish_dates: Dict[str, date] = {}
    schedule = {}

    for package_id in order:
        package = package_map[package_id]

        if package.dependencies:
            dependency_finish = max(
                finish_dates[dependency]
                for dependency in package.dependencies
            )
            package_start = dependency_finish + timedelta(days=1)
        else:
            package_start = start_date

        duration_days = package.schedule_days(hours_per_day)
        package_finish = package_start + timedelta(days=duration_days - 1)

        schedule[package_id] = (package_start, package_finish)
        finish_dates[package_id] = package_finish

    return schedule


# ---------------------------------------------------------------------------
# 13. TESTING AND VALIDATION
# ---------------------------------------------------------------------------

def run_assertions(packages: List[WorkPackage]) -> None:
    """Executable checks for important invariants."""
    assert packages
    assert all(package.validate() == [] for package in packages)

    graph = DependencyGraph(packages)
    assert graph.validate_references() == []

    order = graph.topological_order()
    assert set(order) == {package.package_id for package in packages}

    progress = weighted_progress(packages)
    assert 0 <= progress <= 100

    try:
        packages[0].update_progress(101, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid progress was not rejected.")

    try:
        cyclic = [
            WorkPackage(
                "A", "A", "A", "Owner", 1, Priority.LOW, dependencies={"B"}
            ),
            WorkPackage(
                "B", "B", "B", "Owner", 1, Priority.LOW, dependencies={"A"}
            ),
        ]
        DependencyGraph(cyclic).topological_order()
    except ValueError:
        pass
    else:
        raise AssertionError("Dependency cycle was not detected.")

    print("\n=== VALIDATION TESTS ===")
    print("All assertions passed.")


# ---------------------------------------------------------------------------
# 14. ADVANCED CASE STUDY
# ---------------------------------------------------------------------------

def advanced_case_study() -> None:
    print("\n=== ADVANCED WORK PACKAGE CASE STUDY ===")

    packages = decompose_project()

    print("\nPackage register:")
    for package in packages:
        print(
            f"{package.package_id} | "
            f"{package.name:25} | "
            f"{package.owner:20} | "
            f"{package.estimated_hours:5.1f} h | "
            f"{package.priority.value}"
        )

    graph = DependencyGraph(packages)

    print("\nExecution order:")
    print(" -> ".join(graph.topological_order()))

    critical_duration, critical_path = graph.critical_path_estimate()

    print("\nLongest dependency path:")
    print(" -> ".join(critical_path))
    print(f"Estimated path effort: {critical_duration:.1f} hours")

    start = date(2026, 10, 1)
    schedule = create_schedule(packages, start)

    print("\nSchedule:")
    for package_id in graph.topological_order():
        beginning, ending = schedule[package_id]
        print(
            f"{package_id}: {beginning.isoformat()} -> {ending.isoformat()}"
        )

    # Simulate project execution.
    updates = {
        "WP-101": (100, 25),
        "WP-102": (75, 25),
        "WP-103": (60, 42),
        "WP-104": (20, 10),
        "WP-105": (0, 0),
        "WP-106": (0, 0),
    }

    for package in packages:
        progress, actual = updates[package.package_id]
        package.update_progress(progress, actual)

    print("\nProgress:")
    for package in packages:
        variance = package.estimate_variance()
        print(
            f"{package.package_id}: "
            f"{package.progress_percent:5.1f}% | "
            f"actual={package.actual_hours:5.1f}h | "
            f"variance={variance:+5.1f}h | "
            f"{package.status.value}"
        )

    print(
        f"\nWeighted project progress: "
        f"{weighted_progress(packages):.2f}%"
    )

    available_hours = {
        "Business Analyst": 40,
        "UX Lead": 40,
        "Backend Engineer": 80,
        "Frontend Engineer": 40,
        "QA Engineer": 40,
        "DevOps Engineer": 20,
    }

    overload = detect_overallocation(packages, available_hours)

    print("\nResource capacity:")
    if overload:
        for owner, excess in overload.items():
            print(f"{owner}: overloaded by {excess:.1f} hours")
    else:
        print("No capacity overload detected.")

    evm = earned_value_metrics(
        planned_value=100_000,
        earned_value=72_000,
        actual_cost=80_000,
    )

    print("\nEarned value metrics:")
    print(f"CPI: {evm['cost_performance_index']:.2f}")
    print(f"SPI: {evm['schedule_performance_index']:.2f}")


# ---------------------------------------------------------------------------
# 15. EDGE CASES AND FAILURE MODES
# ---------------------------------------------------------------------------

def edge_case_demo() -> None:
    print("\n=== EDGE CASES ===")

    cases = [
        ("Zero estimate", lambda: WorkPackage(
            "X", "Invalid", "Example", "Owner", 0, Priority.LOW
        ).validate()),
        ("Negative cost", lambda: calculate_cost(-1, 50)),
        ("Invalid probability", lambda: Risk(
            "R", "Invalid", 1.5, 10, "None"
        ).expected_exposure),
        ("Unapproved change", lambda: apply_change_request(
            WorkPackage(
                "X", "Example", "Example", "Owner", 10, Priority.LOW
            ),
            ChangeRequest("CR-1", "Extra work", 5, "New requirement"),
        )),
    ]

    for name, operation in cases:
        try:
            result = operation()
            print(f"{name}: result={result}")
        except (ValueError, TypeError) as error:
            print(f"{name}: safely rejected -> {error}")


# ---------------------------------------------------------------------------
# 16. BEST-PRACTICE CHECKLIST
# ---------------------------------------------------------------------------

def print_best_practices() -> None:
    print("\n=== BEST-PRACTICE CHECKLIST ===")

    practices = [
        "Define each package around a meaningful output.",
        "Assign one accountable owner.",
        "Use measurable acceptance criteria.",
        "Estimate effort using a consistent method.",
        "Record dependencies explicitly.",
        "Keep package boundaries understandable.",
        "Track planned versus actual effort.",
        "Control changes through a documented process.",
        "Identify risks before execution.",
        "Avoid hidden work inside supposedly complete packages.",
        "Use objective completion criteria.",
        "Review package size when estimates become unreliable.",
        "Separate work packages from milestones and deliverables.",
        "Avoid excessive decomposition that creates administrative overhead.",
        "Do not mark work complete merely because effort was spent.",
    ]

    for number, practice in enumerate(practices, 1):
        print(f"{number:02}. {practice}")


# ---------------------------------------------------------------------------
# 17. MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("WORK PACKAGES: UNDERSTANDING MANAGEABLE UNITS OF WORK")
    print("=" * 72)

    beginner_example()
    explain_relationships()

    packages = decompose_project()

    print("\n=== QUALITY CHECK ===")
    for package in packages:
        quality = evaluate_package_quality(package)
        passed = all(quality.values())
        print(f"{package.package_id}: {'PASS' if passed else 'FAIL'}")

    estimation_demo()
    risk_demo()
    advanced_case_study()
    edge_case_demo()
    run_assertions(packages)
    print_best_practices()

    print("\n=== END OF STUDY PROGRAM ===")


if __name__ == "__main__":
    main()
