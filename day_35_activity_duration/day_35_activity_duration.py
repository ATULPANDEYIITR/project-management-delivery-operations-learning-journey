"""
Activity Duration Estimation for Task Planning

This executable script demonstrates progressively richer ways to estimate how
long a repository-development task may take. It uses deterministic historical
data, three-point estimates, PERT expected duration, uncertainty analysis,
velocity-based calibration, dependency-aware scheduling, Monte Carlo
simulation, and estimation diagnostics.

The domain examples are software-development tasks, but the estimation
mechanisms are general task-duration techniques.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
import math
import random
import statistics
from typing import Iterable


class TaskType(Enum):
    ANALYSIS = "analysis"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    INTEGRATION = "integration"


@dataclass(frozen=True)
class HistoricalTask:
    name: str
    task_type: TaskType
    estimated_hours: float
    actual_hours: float


@dataclass(frozen=True)
class ThreePointEstimate:
    optimistic: float
    most_likely: float
    pessimistic: float

    def validate(self) -> None:
        values = (self.optimistic, self.most_likely, self.pessimistic)
        if any(value < 0 for value in values):
            raise ValueError("Duration estimates cannot be negative.")
        if not (
            self.optimistic <= self.most_likely <= self.pessimistic
        ):
            raise ValueError(
                "Three-point estimates must satisfy "
                "optimistic <= most_likely <= pessimistic."
            )

    @property
    def simple_average(self) -> float:
        self.validate()
        return (
            self.optimistic
            + self.most_likely
            + self.pessimistic
        ) / 3

    @property
    def pert_expected(self) -> float:
        """PERT gives four times as much weight to the most-likely estimate."""
        self.validate()
        return (
            self.optimistic
            + 4 * self.most_likely
            + self.pessimistic
        ) / 6

    @property
    def standard_deviation(self) -> float:
        """The PERT approximation uses (P - O) / 6 as the uncertainty."""
        self.validate()
        return (self.pessimistic - self.optimistic) / 6


@dataclass
class Task:
    name: str
    task_type: TaskType
    estimate: ThreePointEstimate
    dependencies: list[str] = field(default_factory=list)

    def expected_hours(self) -> float:
        return self.estimate.pert_expected


@dataclass
class ScheduledTask:
    task: Task
    start_hour: float
    finish_hour: float


def print_title(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def demonstrate_basic_estimation() -> None:
    print_title("Basic Activity Duration Estimation")

    planned_hours = 12.0
    actual_hours = 15.5

    variance = actual_hours - planned_hours
    error_percentage = (variance / planned_hours) * 100

    print(f"Planned duration : {planned_hours:.1f} hours")
    print(f"Actual duration  : {actual_hours:.1f} hours")
    print(f"Absolute error   : {variance:+.1f} hours")
    print(f"Relative error   : {error_percentage:+.1f}%")

    if actual_hours > planned_hours:
        print("Diagnosis        : the task took longer than estimated.")
    elif actual_hours < planned_hours:
        print("Diagnosis        : the task finished faster than estimated.")
    else:
        print("Diagnosis        : the estimate matched the actual duration.")


def demonstrate_three_point_estimation() -> None:
    print_title("Three-Point Duration Estimation")

    estimate = ThreePointEstimate(
        optimistic=6,
        most_likely=10,
        pessimistic=18,
    )

    print(f"Optimistic duration : {estimate.optimistic:.1f} h")
    print(f"Most-likely duration: {estimate.most_likely:.1f} h")
    print(f"Pessimistic duration: {estimate.pessimistic:.1f} h")
    print(f"Simple average      : {estimate.simple_average:.2f} h")
    print(f"PERT expected       : {estimate.pert_expected:.2f} h")
    print(f"PERT uncertainty    : ±{estimate.standard_deviation:.2f} h")

    try:
        ThreePointEstimate(12, 8, 20).validate()
    except ValueError as exc:
        print(f"Validation caught invalid estimate: {exc}")


def build_historical_dataset() -> list[HistoricalTask]:
    return [
        HistoricalTask("API contract analysis", TaskType.ANALYSIS, 8, 9),
        HistoricalTask("Authentication service", TaskType.IMPLEMENTATION, 20, 25),
        HistoricalTask("Database migration tests", TaskType.TESTING, 12, 10),
        HistoricalTask("Deployment documentation", TaskType.DOCUMENTATION, 6, 8),
        HistoricalTask("Service integration", TaskType.INTEGRATION, 16, 21),
        HistoricalTask("Data validation rules", TaskType.IMPLEMENTATION, 14, 15),
        HistoricalTask("Regression suite", TaskType.TESTING, 18, 22),
        HistoricalTask("Architecture notes", TaskType.DOCUMENTATION, 5, 4),
    ]


def calculate_bias(historical_tasks: Iterable[HistoricalTask]) -> float:
    """
    Returns actual / estimated.

    A factor above 1 means estimates have historically been too optimistic.
    A factor below 1 means estimates have historically been conservative.
    """
    tasks = list(historical_tasks)
    if not tasks:
        raise ValueError("Historical data cannot be empty.")

    estimated = sum(task.estimated_hours for task in tasks)
    actual = sum(task.actual_hours for task in tasks)

    if estimated <= 0:
        raise ValueError("Historical estimated duration must be positive.")

    return actual / estimated


def calculate_type_bias(
    historical_tasks: Iterable[HistoricalTask],
) -> dict[TaskType, float]:
    grouped: dict[TaskType, list[HistoricalTask]] = {}

    for task in historical_tasks:
        grouped.setdefault(task.task_type, []).append(task)

    factors: dict[TaskType, float] = {}

    for task_type, tasks in grouped.items():
        estimated = sum(task.estimated_hours for task in tasks)
        actual = sum(task.actual_hours for task in tasks)

        if estimated > 0:
            factors[task_type] = actual / estimated

    return factors


def demonstrate_historical_calibration() -> None:
    print_title("Historical Calibration")

    history = build_historical_dataset()
    global_bias = calculate_bias(history)
    type_bias = calculate_type_bias(history)

    print(f"Historical duration factor: {global_bias:.3f}")

    for task_type in TaskType:
        if task_type in type_bias:
            print(
                f"{task_type.value:16s}: "
                f"{type_bias[task_type]:.3f} actual/estimated"
            )

    new_estimate = 10.0
    calibrated = new_estimate * global_bias

    print(f"\nRaw new estimate : {new_estimate:.2f} h")
    print(f"Calibrated        : {calibrated:.2f} h")


def calculate_confidence_interval(
    estimate: ThreePointEstimate,
    z_score: float = 1.645,
) -> tuple[float, float]:
    """
    Approximate a confidence interval around the PERT expected duration.

    1.645 is commonly used for an approximate 90% two-sided interval under
    a normal approximation. This is an approximation, not a guarantee.
    """
    expected = estimate.pert_expected
    uncertainty = estimate.standard_deviation

    lower = max(0.0, expected - z_score * uncertainty)
    upper = expected + z_score * uncertainty
    return lower, upper


def demonstrate_uncertainty() -> None:
    print_title("Uncertainty and Confidence Range")

    estimate = ThreePointEstimate(8, 12, 24)
    expected = estimate.pert_expected
    low, high = calculate_confidence_interval(estimate)

    print(f"Expected duration : {expected:.2f} h")
    print(f"Approximate 90% range: {low:.2f} h to {high:.2f} h")
    print(
        "The range is wider because the pessimistic scenario is "
        "substantially larger than the optimistic scenario."
    )


def estimate_task_with_history(
    task: Task,
    historical_tasks: list[HistoricalTask],
) -> float:
    type_bias = calculate_type_bias(historical_tasks)
    factor = type_bias.get(task.task_type, calculate_bias(historical_tasks))
    return task.expected_hours() * factor


def demonstrate_category_specific_estimation() -> None:
    print_title("Category-Aware Estimation")

    history = build_historical_dataset()

    task = Task(
        name="Implement service integration",
        task_type=TaskType.INTEGRATION,
        estimate=ThreePointEstimate(10, 16, 26),
    )

    raw = task.expected_hours()
    calibrated = estimate_task_with_history(task, history)

    print(f"Task                : {task.name}")
    print(f"Raw PERT estimate   : {raw:.2f} h")
    print(f"History-calibrated  : {calibrated:.2f} h")


def topological_order(tasks: list[Task]) -> list[Task]:
    by_name = {task.name: task for task in tasks}
    state: dict[str, int] = {}
    ordered: list[Task] = []

    def visit(name: str) -> None:
        current = state.get(name, 0)

        if current == 1:
            raise ValueError(f"Circular dependency detected at '{name}'.")

        if current == 2:
            return

        if name not in by_name:
            raise ValueError(f"Unknown dependency: '{name}'.")

        state[name] = 1

        for dependency in by_name[name].dependencies:
            visit(dependency)

        state[name] = 2
        ordered.append(by_name[name])

    for task in tasks:
        visit(task.name)

    return ordered


def schedule_sequential_tasks(
    tasks: list[Task],
    history: list[HistoricalTask],
) -> list[ScheduledTask]:
    ordered = topological_order(tasks)
    finish_times: dict[str, float] = {}
    schedule: list[ScheduledTask] = []

    for task in ordered:
        dependency_finish = max(
            (finish_times[name] for name in task.dependencies),
            default=0.0,
        )

        duration = estimate_task_with_history(task, history)
        start = dependency_finish
        finish = start + duration

        finish_times[task.name] = finish
        schedule.append(
            ScheduledTask(
                task=task,
                start_hour=start,
                finish_hour=finish,
            )
        )

    return schedule


def demonstrate_dependency_aware_duration() -> None:
    print_title("Dependency-Aware Task Duration")

    history = build_historical_dataset()

    tasks = [
        Task(
            "Requirements clarification",
            TaskType.ANALYSIS,
            ThreePointEstimate(3, 5, 8),
        ),
        Task(
            "Implementation",
            TaskType.IMPLEMENTATION,
            ThreePointEstimate(12, 18, 28),
            ["Requirements clarification"],
        ),
        Task(
            "Integration testing",
            TaskType.TESTING,
            ThreePointEstimate(8, 12, 20),
            ["Implementation"],
        ),
        Task(
            "Release documentation",
            TaskType.DOCUMENTATION,
            ThreePointEstimate(3, 5, 7),
            ["Implementation"],
        ),
        Task(
            "Production integration",
            TaskType.INTEGRATION,
            ThreePointEstimate(6, 10, 16),
            ["Integration testing", "Release documentation"],
        ),
    ]

    schedule = schedule_sequential_tasks(tasks, history)

    for item in schedule:
        print(
            f"{item.task.name:28s} "
            f"start={item.start_hour:6.2f} h "
            f"finish={item.finish_hour:6.2f} h"
        )

    print(
        f"\nEstimated elapsed duration: "
        f"{schedule[-1].finish_hour:.2f} hours"
    )


def aggregate_independent_estimates(
    estimates: list[ThreePointEstimate],
) -> tuple[float, float]:
    """
    For independent activities, expected durations add and variances add.

    This is different from simply adding standard deviations.
    """
    expected = sum(item.pert_expected for item in estimates)
    variance = sum(item.standard_deviation ** 2 for item in estimates)
    return expected, math.sqrt(variance)


def demonstrate_aggregate_uncertainty() -> None:
    print_title("Combined Activity Uncertainty")

    estimates = [
        ThreePointEstimate(4, 6, 10),
        ThreePointEstimate(8, 11, 17),
        ThreePointEstimate(3, 5, 9),
    ]

    expected, combined_sd = aggregate_independent_estimates(estimates)

    print(f"Combined expected duration: {expected:.2f} h")
    print(f"Combined standard deviation: {combined_sd:.2f} h")
    print(f"Approximate 90% upper range: {expected + 1.645 * combined_sd:.2f} h")


def monte_carlo_duration(
    estimate: ThreePointEstimate,
    simulations: int = 20_000,
    seed: int = 42,
) -> list[float]:
    """
    Simulates task durations with a triangular distribution.

    The triangular distribution uses the three estimates directly and is
    useful when historical distributions are unavailable.
    """
    estimate.validate()

    if simulations <= 0:
        raise ValueError("Simulation count must be positive.")

    rng = random.Random(seed)

    return [
        rng.triangular(
            estimate.optimistic,
            estimate.pessimistic,
            estimate.most_likely,
        )
        for _ in range(simulations)
    ]


def percentile(values: list[float], percentage: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile from empty data.")

    if not 0 <= percentage <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    ordered = sorted(values)
    position = (len(ordered) - 1) * percentage / 100
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower
    return ordered[lower] + (
        ordered[upper] - ordered[lower]
    ) * fraction


def demonstrate_monte_carlo() -> None:
    print_title("Monte Carlo Activity-Duration Simulation")

    estimate = ThreePointEstimate(8, 14, 30)
    simulations = monte_carlo_duration(estimate)

    print(f"Simulations: {len(simulations):,}")
    print(f"Mean simulated duration: {statistics.mean(simulations):.2f} h")
    print(f"Median: {percentile(simulations, 50):.2f} h")
    print(f"80th percentile: {percentile(simulations, 80):.2f} h")
    print(f"90th percentile: {percentile(simulations, 90):.2f} h")
    print(f"95th percentile: {percentile(simulations, 95):.2f} h")


def simulate_project_duration(
    tasks: list[Task],
    simulations: int = 10_000,
    seed: int = 7,
) -> list[float]:
    """
    Simulates a dependency graph.

    Each task receives a triangularly distributed duration. Tasks can begin
    when all dependencies have finished. Because there is no resource
    constraint in this model, independent branches may execute concurrently.
    """
    topological = topological_order(tasks)
    rng = random.Random(seed)
    results: list[float] = []

    for _ in range(simulations):
        finish_times: dict[str, float] = {}

        for task in topological:
            start = max(
                (finish_times[name] for name in task.dependencies),
                default=0.0,
            )

            duration = rng.triangular(
                task.estimate.optimistic,
                task.estimate.pessimistic,
                task.estimate.most_likely,
            )

            finish_times[task.name] = start + duration

        results.append(max(finish_times.values(), default=0.0))

    return results


def demonstrate_project_risk() -> None:
    print_title("Project-Level Duration Risk")

    tasks = [
        Task(
            "Specification",
            TaskType.ANALYSIS,
            ThreePointEstimate(4, 6, 10),
        ),
        Task(
            "Backend implementation",
            TaskType.IMPLEMENTATION,
            ThreePointEstimate(12, 18, 30),
            ["Specification"],
        ),
        Task(
            "Frontend implementation",
            TaskType.IMPLEMENTATION,
            ThreePointEstimate(10, 16, 26),
            ["Specification"],
        ),
        Task(
            "Backend testing",
            TaskType.TESTING,
            ThreePointEstimate(6, 10, 18),
            ["Backend implementation"],
        ),
        Task(
            "Frontend testing",
            TaskType.TESTING,
            ThreePointEstimate(5, 8, 15),
            ["Frontend implementation"],
        ),
        Task(
            "System integration",
            TaskType.INTEGRATION,
            ThreePointEstimate(6, 10, 18),
            ["Backend testing", "Frontend testing"],
        ),
    ]

    results = simulate_project_duration(tasks)

    print(f"Median project duration : {percentile(results, 50):.2f} h")
    print(f"80% completion threshold: {percentile(results, 80):.2f} h")
    print(f"90% completion threshold: {percentile(results, 90):.2f} h")
    print(f"95% completion threshold: {percentile(results, 95):.2f} h")


def working_days_from_hours(hours: float, hours_per_day: float = 8) -> int:
    if hours < 0:
        raise ValueError("Hours cannot be negative.")
    if hours_per_day <= 0:
        raise ValueError("Hours per day must be positive.")

    return math.ceil(hours / hours_per_day)


def demonstrate_calendar_conversion() -> None:
    print_title("Duration Versus Calendar Time")

    effort_hours = 28
    working_days = working_days_from_hours(effort_hours)

    start = date(2026, 10, 5)
    current = start
    remaining_days = working_days

    while remaining_days > 0:
        if current.weekday() < 5:
            remaining_days -= 1
        if remaining_days:
            current += timedelta(days=1)

    print(f"Estimated effort : {effort_hours} working hours")
    print(f"Working days     : {working_days}")
    print(f"Start date       : {start}")
    print(f"Estimated finish : {current}")

    print(
        "Calendar duration is not identical to effort duration: "
        "weekends and non-working periods change the elapsed date."
    )


def calculate_estimation_metrics(
    planned: list[float],
    actual: list[float],
) -> dict[str, float]:
    if len(planned) != len(actual) or not planned:
        raise ValueError("Planned and actual samples must have equal non-zero length.")

    absolute_errors = [abs(a - p) for p, a in zip(planned, actual)]
    percentage_errors = [
        abs(a - p) / p
        for p, a in zip(planned, actual)
        if p > 0
    ]

    if not percentage_errors:
        raise ValueError("At least one planned duration must be positive.")

    return {
        "mae_hours": statistics.mean(absolute_errors),
        "mape": statistics.mean(percentage_errors) * 100,
        "bias_hours": statistics.mean(
            actual_value - planned_value
            for planned_value, actual_value in zip(planned, actual)
        ),
    }


def demonstrate_estimation_quality() -> None:
    print_title("Measuring Estimation Quality")

    planned = [8, 12, 16, 10, 20, 14]
    actual = [9, 15, 13, 11, 24, 12]

    metrics = calculate_estimation_metrics(planned, actual)

    print(f"Mean absolute error : {metrics['mae_hours']:.2f} h")
    print(f"Mean absolute percentage error: {metrics['mape']:.2f}%")
    print(f"Average signed bias : {metrics['bias_hours']:+.2f} h")

    if metrics["bias_hours"] > 0:
        print("The sample shows systematic underestimation.")
    elif metrics["bias_hours"] < 0:
        print("The sample shows systematic overestimation.")
    else:
        print("The sample has no average signed bias.")


def validate_task_graph(tasks: list[Task]) -> None:
    names = [task.name for task in tasks]

    if len(names) != len(set(names)):
        raise ValueError("Task names must be unique.")

    for task in tasks:
        if not task.name.strip():
            raise ValueError("Task names cannot be empty.")
        task.estimate.validate()

    topological_order(tasks)


def demonstrate_failure_conditions() -> None:
    print_title("Failure Conditions and Validation")

    invalid_graph = [
        Task(
            "A",
            TaskType.IMPLEMENTATION,
            ThreePointEstimate(2, 4, 6),
            ["B"],
        ),
        Task(
            "B",
            TaskType.TESTING,
            ThreePointEstimate(2, 4, 6),
            ["A"],
        ),
    ]

    try:
        validate_task_graph(invalid_graph)
    except ValueError as exc:
        print(f"Dependency validation: {exc}")

    try:
        ThreePointEstimate(-1, 4, 7).validate()
    except ValueError as exc:
        print(f"Duration validation: {exc}")

    try:
        ThreePointEstimate(10, 5, 20).validate()
    except ValueError as exc:
        print(f"Ordering validation: {exc}")


def main() -> None:
    demonstrate_basic_estimation()
    demonstrate_three_point_estimation()
    demonstrate_historical_calibration()
    demonstrate_category_specific_estimation()
    demonstrate_uncertainty()
    demonstrate_dependency_aware_duration()
    demonstrate_aggregate_uncertainty()
    demonstrate_monte_carlo()
    demonstrate_project_risk()
    demonstrate_calendar_conversion()
    demonstrate_estimation_quality()
    demonstrate_failure_conditions()

    print_title("Production Estimation Principles")
    print(
        "Use historical task durations to calibrate estimates rather than "
        "assuming estimates are unbiased."
    )
    print(
        "Separate effort from elapsed calendar time when people, dependencies, "
        "working hours, or parallel work affect completion."
    )
    print(
        "Represent uncertainty explicitly when a single duration would hide "
        "meaningful variability."
    )
    print(
        "Treat unusually wide optimistic-to-pessimistic ranges as a signal "
        "that the task may need decomposition or further discovery."
    )


if __name__ == "__main__":
    main()
