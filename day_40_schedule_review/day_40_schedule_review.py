"""
Schedule Review: comprehensive executable demonstration.

This module models schedule review as a technical process rather than merely
printing calendar entries. It covers schedule construction, dependency
validation, overlap detection, resource conflicts, critical-path analysis,
capacity checks, variance analysis, review decisions, and review reporting.

The examples use a software delivery schedule, but the scheduling mechanisms
apply equally to projects, operations, maintenance, training, and production.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Iterable
import csv
import json
import statistics


DATE_FORMAT = "%Y-%m-%d"


def parse_date(value: str) -> date:
    """Convert an ISO date into a date and fail clearly for invalid input."""
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Expected YYYY-MM-DD.") from exc


class TaskStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    BLOCKED = "blocked"


class ReviewDecision(Enum):
    ACCEPT = "accept"
    REVISE = "revise"
    ESCALATE = "escalate"


@dataclass
class Task:
    task_id: str
    name: str
    start: date
    end: date
    owner: str
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PLANNED
    progress: float = 0.0
    planned_hours: float = 0.0
    actual_hours: float = 0.0
    priority: str = "normal"

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"{self.task_id}: end date precedes start date.")
        if not 0 <= self.progress <= 100:
            raise ValueError(f"{self.task_id}: progress must be between 0 and 100.")
        if self.planned_hours < 0 or self.actual_hours < 0:
            raise ValueError(f"{self.task_id}: hours cannot be negative.")

    @property
    def duration_days(self) -> int:
        return (self.end - self.start).days + 1

    @property
    def variance_days(self) -> int:
        return 0

    def overlaps(self, other: "Task") -> bool:
        return self.start <= other.end and other.start <= self.end


@dataclass(frozen=True)
class DependencyIssue:
    task_id: str
    dependency_id: str
    message: str


@dataclass(frozen=True)
class ScheduleConflict:
    task_a: str
    task_b: str
    owner: str
    overlap_start: date
    overlap_end: date


@dataclass
class ScheduleReview:
    schedule_name: str
    tasks: dict[str, Task]
    review_date: date
    capacity: dict[str, float]
    issues: list[str] = field(default_factory=list)

    def task(self, task_id: str) -> Task:
        if task_id not in self.tasks:
            raise KeyError(f"Unknown task: {task_id}")
        return self.tasks[task_id]


class ScheduleEngine:
    """Performs structural and analytical checks on a schedule."""

    def __init__(self, tasks: Iterable[Task]) -> None:
        self.tasks = {task.task_id: task for task in tasks}

    def validate_dependencies(self) -> list[DependencyIssue]:
        issues: list[DependencyIssue] = []

        for task in self.tasks.values():
            for dependency_id in task.dependencies:
                dependency = self.tasks.get(dependency_id)

                if dependency is None:
                    issues.append(
                        DependencyIssue(
                            task.task_id,
                            dependency_id,
                            "Dependency does not exist.",
                        )
                    )
                    continue

                if dependency.end > task.start:
                    issues.append(
                        DependencyIssue(
                            task.task_id,
                            dependency_id,
                            (
                                f"Dependency finishes {dependency.end}, "
                                f"but task starts {task.start}."
                            ),
                        )
                    )

        return issues

    def detect_dependency_cycle(self) -> list[str]:
        """Use depth-first search to identify one dependency cycle."""
        graph = {
            task_id: list(task.dependencies)
            for task_id, task in self.tasks.items()
        }
        visiting: set[str] = set()
        visited: set[str] = set()
        path: list[str] = []

        def visit(node: str) -> list[str]:
            if node in visiting:
                if node in path:
                    index = path.index(node)
                    return path[index:] + [node]
                return [node]

            if node in visited:
                return []

            visiting.add(node)
            path.append(node)

            for dependency in graph.get(node, []):
                cycle = visit(dependency)
                if cycle:
                    return cycle

            path.pop()
            visiting.remove(node)
            visited.add(node)
            return []

        for node in graph:
            cycle = visit(node)
            if cycle:
                return cycle

        return []

    def detect_resource_conflicts(self) -> list[ScheduleConflict]:
        """Find overlapping tasks assigned to the same person."""
        by_owner: dict[str, list[Task]] = {}

        for task in self.tasks.values():
            by_owner.setdefault(task.owner, []).append(task)

        conflicts: list[ScheduleConflict] = []

        for owner, tasks in by_owner.items():
            ordered = sorted(tasks, key=lambda item: item.start)

            for index, current in enumerate(ordered):
                for following in ordered[index + 1 :]:
                    if following.start > current.end:
                        break

                    overlap_start = max(current.start, following.start)
                    overlap_end = min(current.end, following.end)

                    if overlap_start <= overlap_end:
                        conflicts.append(
                            ScheduleConflict(
                                current.task_id,
                                following.task_id,
                                owner,
                                overlap_start,
                                overlap_end,
                            )
                        )

        return conflicts

    def workload_by_owner(self) -> dict[str, float]:
        workload: dict[str, float] = {}

        for task in self.tasks.values():
            workload[task.owner] = workload.get(task.owner, 0.0) + task.planned_hours

        return workload

    def capacity_violations(self, capacity: dict[str, float]) -> dict[str, float]:
        workload = self.workload_by_owner()
        return {
            owner: workload_value - capacity[owner]
            for owner, workload_value in workload.items()
            if owner in capacity and workload_value > capacity[owner]
        }

    def calculate_critical_path(self) -> tuple[list[str], int]:
        """
        Calculate the longest dependency path.

        The schedule assumes finish-to-start dependencies. A task may begin
        on the same calendar day its predecessor finishes only if the
        predecessor is explicitly treated as complete before that day begins.
        Here we use duration arithmetic for a conservative project view.
        """
        cycle = self.detect_dependency_cycle()
        if cycle:
            raise ValueError(f"Critical-path calculation blocked by cycle: {cycle}")

        memo: dict[str, tuple[int, list[str]]] = {}

        def longest(task_id: str) -> tuple[int, list[str]]:
            if task_id in memo:
                return memo[task_id]

            task = self.tasks[task_id]

            if not task.dependencies:
                result = (task.duration_days, [task_id])
            else:
                predecessors = [
                    longest(dependency_id)
                    for dependency_id in task.dependencies
                    if dependency_id in self.tasks
                ]

                if not predecessors:
                    result = (task.duration_days, [task_id])
                else:
                    best_length, best_path = max(predecessors, key=lambda item: item[0])
                    result = (
                        best_length + task.duration_days,
                        best_path + [task_id],
                    )

            memo[task_id] = result
            return result

        candidates = [longest(task_id) for task_id in self.tasks]
        return max(candidates, key=lambda item: item[0])

    def schedule_health(self, capacity: dict[str, float]) -> dict[str, object]:
        dependency_issues = self.validate_dependencies()
        conflicts = self.detect_resource_conflicts()
        capacity_issues = self.capacity_violations(capacity)
        cycle = self.detect_dependency_cycle()

        return {
            "dependency_issues": dependency_issues,
            "resource_conflicts": conflicts,
            "capacity_violations": capacity_issues,
            "dependency_cycle": cycle,
            "task_count": len(self.tasks),
        }


class ScheduleReviewService:
    """
    Turns analytical findings into an explicit review decision.

    A review is not the same as schedule calculation. Calculation produces
    evidence; review applies governance rules to that evidence.
    """

    def __init__(self, engine: ScheduleEngine) -> None:
        self.engine = engine

    def review(self, capacity: dict[str, float]) -> tuple[ReviewDecision, list[str]]:
        health = self.engine.schedule_health(capacity)
        findings: list[str] = []

        if health["dependency_cycle"]:
            findings.append("Dependency cycle prevents reliable scheduling.")
            return ReviewDecision.ESCALATE, findings

        dependency_issues = health["dependency_issues"]
        if dependency_issues:
            findings.extend(
                f"{issue.task_id}: {issue.message}" for issue in dependency_issues
            )

        conflicts = health["resource_conflicts"]
        findings.extend(
            (
                f"Resource conflict for {conflict.owner}: "
                f"{conflict.task_a} overlaps {conflict.task_b} "
                f"from {conflict.overlap_start} to {conflict.overlap_end}."
            )
            for conflict in conflicts
        )

        for owner, excess in health["capacity_violations"].items():
            findings.append(f"{owner} exceeds planned capacity by {excess:.1f} hours.")

        if health["dependency_cycle"] or len(findings) > 2:
            return ReviewDecision.ESCALATE, findings

        if findings:
            return ReviewDecision.REVISE, findings

        return ReviewDecision.ACCEPT, ["Schedule passed the configured review rules."]


def calculate_progress_variance(task: Task, review_date: date) -> float:
    """
    Estimate schedule progress expected by the review date.

    This is a simple time-elapsed measure, not earned-value analysis.
    It intentionally treats planned calendar duration and actual completion
    as separate dimensions.
    """
    if review_date < task.start:
        expected = 0.0
    elif review_date >= task.end:
        expected = 100.0
    else:
        elapsed = (review_date - task.start).days + 1
        expected = elapsed / task.duration_days * 100

    return task.progress - expected


def generate_review_report(
    engine: ScheduleEngine,
    review_date: date,
    capacity: dict[str, float],
) -> str:
    decision, findings = ScheduleReviewService(engine).review(capacity)
    critical_path, duration = engine.calculate_critical_path()

    lines = [
        f"Schedule Review Date: {review_date}",
        f"Review Decision: {decision.value.upper()}",
        f"Task Count: {len(engine.tasks)}",
        f"Critical Path: {' -> '.join(critical_path)}",
        f"Critical Path Duration: {duration} calendar days",
        "",
        "Task Progress Variance:",
    ]

    for task in sorted(engine.tasks.values(), key=lambda item: item.start):
        variance = calculate_progress_variance(task, review_date)
        lines.append(
            f"  {task.task_id:<8} {task.name:<28} "
            f"actual={task.progress:>5.1f}% "
            f"schedule_variance={variance:>6.1f}%"
        )

    lines.append("")
    lines.append("Review Findings:")
    lines.extend(f"  - {finding}" for finding in findings)

    return "\n".join(lines)


def export_tasks_csv(tasks: Iterable[Task], path: Path) -> None:
    """Export reviewable schedule data without external dependencies."""
    fieldnames = [
        "task_id",
        "name",
        "start",
        "end",
        "owner",
        "status",
        "progress",
        "planned_hours",
        "actual_hours",
        "priority",
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for task in tasks:
            writer.writerow(
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "start": task.start.isoformat(),
                    "end": task.end.isoformat(),
                    "owner": task.owner,
                    "status": task.status.value,
                    "progress": task.progress,
                    "planned_hours": task.planned_hours,
                    "actual_hours": task.actual_hours,
                    "priority": task.priority,
                }
            )


def serialize_review(engine: ScheduleEngine, decision: ReviewDecision) -> str:
    """Produce machine-readable review evidence suitable for automation."""
    payload = {
        "decision": decision.value,
        "tasks": [
            {
                "id": task.task_id,
                "name": task.name,
                "owner": task.owner,
                "start": task.start.isoformat(),
                "end": task.end.isoformat(),
                "status": task.status.value,
                "progress": task.progress,
            }
            for task in engine.tasks.values()
        ],
    }
    return json.dumps(payload, indent=2)


def build_sample_schedule() -> list[Task]:
    """
    Construct a realistic software-release schedule.

    The dates intentionally include one resource conflict so the review
    demonstrates a revision rather than simply producing a perfect plan.
    """
    return [
        Task(
            "REQ",
            "Requirements baseline",
            parse_date("2026-10-01"),
            parse_date("2026-10-03"),
            "Asha",
            planned_hours=18,
            actual_hours=18,
            progress=100,
            status=TaskStatus.COMPLETE,
            priority="high",
        ),
        Task(
            "ARCH",
            "Architecture review",
            parse_date("2026-10-04"),
            parse_date("2026-10-06"),
            "Ravi",
            dependencies=["REQ"],
            planned_hours=20,
            actual_hours=16,
            progress=100,
            status=TaskStatus.COMPLETE,
            priority="high",
        ),
        Task(
            "API",
            "API implementation",
            parse_date("2026-10-07"),
            parse_date("2026-10-12"),
            "Ravi",
            dependencies=["ARCH"],
            planned_hours=36,
            actual_hours=18,
            progress=55,
            status=TaskStatus.IN_PROGRESS,
            priority="high",
        ),
        Task(
            "UI",
            "Review dashboard",
            parse_date("2026-10-10"),
            parse_date("2026-10-14"),
            "Meera",
            dependencies=["ARCH"],
            planned_hours=30,
            actual_hours=12,
            progress=40,
            status=TaskStatus.IN_PROGRESS,
        ),
        Task(
            "TEST",
            "Integration testing",
            parse_date("2026-10-13"),
            parse_date("2026-10-16"),
            "Asha",
            dependencies=["API", "UI"],
            planned_hours=28,
            actual_hours=0,
            progress=0,
        ),
        Task(
            "SEC",
            "Security verification",
            parse_date("2026-10-15"),
            parse_date("2026-10-17"),
            "Ravi",
            dependencies=["TEST"],
            planned_hours=18,
            actual_hours=0,
            progress=0,
            priority="high",
        ),
        Task(
            "REL",
            "Production release",
            parse_date("2026-10-19"),
            parse_date("2026-10-19"),
            "Asha",
            dependencies=["SEC"],
            planned_hours=8,
            actual_hours=0,
            progress=0,
            priority="high",
        ),
    ]


def demonstrate_validation_edge_cases() -> None:
    """Show how a review system responds to malformed scheduling data."""
    try:
        Task(
            "INVALID",
            "Impossible task",
            parse_date("2026-10-20"),
            parse_date("2026-10-19"),
            "Asha",
        )
    except ValueError as exc:
        print(f"Validation correctly rejected invalid task: {exc}")

    cycle_tasks = [
        Task(
            "A",
            "Circular planning A",
            parse_date("2026-10-01"),
            parse_date("2026-10-02"),
            "Asha",
            dependencies=["C"],
        ),
        Task(
            "B",
            "Circular planning B",
            parse_date("2026-10-03"),
            parse_date("2026-10-04"),
            "Ravi",
            dependencies=["A"],
        ),
        Task(
            "C",
            "Circular planning C",
            parse_date("2026-10-05"),
            parse_date("2026-10-06"),
            "Meera",
            dependencies=["B"],
        ),
    ]

    cycle_engine = ScheduleEngine(cycle_tasks)
    print(f"Detected dependency cycle: {cycle_engine.detect_dependency_cycle()}")


def main() -> None:
    print("=" * 78)
    print("SCHEDULE REVIEW ENGINE")
    print("=" * 78)

    tasks = build_sample_schedule()
    engine = ScheduleEngine(tasks)

    capacity = {
        "Asha": 70.0,
        "Ravi": 65.0,
        "Meera": 40.0,
    }

    health = engine.schedule_health(capacity)

    print("\nDependency Validation")
    if health["dependency_issues"]:
        for issue in health["dependency_issues"]:
            print(f"  {issue.task_id}: {issue.message}")
    else:
        print("  No dependency timing violations.")

    print("\nResource Conflicts")
    if health["resource_conflicts"]:
        for conflict in health["resource_conflicts"]:
            print(
                f"  {conflict.owner}: {conflict.task_a} and {conflict.task_b} "
                f"overlap from {conflict.overlap_start} to {conflict.overlap_end}."
            )
    else:
        print("  No overlapping assignments.")

    print("\nCapacity")
    capacity_violations = health["capacity_violations"]
    if capacity_violations:
        for owner, excess in capacity_violations.items():
            print(f"  {owner}: {excess:.1f} hours over capacity")
    else:
        print("  No capacity violations.")

    print("\nCritical Path")
    critical_path, duration = engine.calculate_critical_path()
    print(f"  {' -> '.join(critical_path)}")
    print(f"  Duration: {duration} calendar days")

    review_date = date(2026, 10, 12)
    print("\nSchedule Review")
    print(generate_review_report(engine, review_date, capacity))

    decision, _ = ScheduleReviewService(engine).review(capacity)
    print("\nMachine-readable Review Evidence")
    print(serialize_review(engine, decision))

    output_path = Path("schedule_review_tasks.csv")
    export_tasks_csv(tasks, output_path)
    print(f"\nExported schedule data to {output_path.resolve()}")

    print("\nValidation Edge Cases")
    demonstrate_validation_edge_cases()

    # statistics is used here to provide a compact schedule-duration metric.
    durations = [task.duration_days for task in tasks]
    print(
        f"\nDuration Statistics: mean={statistics.mean(durations):.2f} days, "
        f"median={statistics.median(durations):.2f} days"
    )


if __name__ == "__main__":
    main()
