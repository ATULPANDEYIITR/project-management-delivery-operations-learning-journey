from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import csv
import json


DATE_FORMAT = "%Y-%m-%d"


@dataclass
class Task:
    task_id: str
    name: str
    start: date
    end: date
    dependencies: List[str] = field(default_factory=list)
    progress: float = 0.0
    resource: Optional[str] = None
    milestone: bool = False

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"Task {self.task_id}: end date cannot precede start date.")
        if not 0 <= self.progress <= 100:
            raise ValueError(f"Task {self.task_id}: progress must be between 0 and 100.")
        if self.milestone and self.start != self.end:
            raise ValueError("A milestone must have identical start and end dates.")

    @property
    def duration(self) -> int:
        return (self.end - self.start).days + 1

    @property
    def completed_duration(self) -> int:
        return round(self.duration * self.progress / 100)

    @property
    def remaining_duration(self) -> int:
        return self.duration - self.completed_duration


@dataclass
class GanttProject:
    name: str
    tasks: Dict[str, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        if task.task_id in self.tasks:
            raise ValueError(f"Duplicate task ID: {task.task_id}")

        for dependency in task.dependencies:
            if dependency == task.task_id:
                raise ValueError(f"Task {task.task_id} cannot depend on itself.")

        self.tasks[task.task_id] = task

    def validate_dependencies(self) -> None:
        for task in self.tasks.values():
            for dependency in task.dependencies:
                if dependency not in self.tasks:
                    raise ValueError(
                        f"Task {task.task_id} depends on unknown task {dependency}."
                    )

                predecessor = self.tasks[dependency]
                if predecessor.end >= task.start:
                    raise ValueError(
                        f"Dependency violation: {task.task_id} starts on "
                        f"{task.start}, but predecessor {dependency} ends on "
                        f"{predecessor.end}."
                    )

        self._detect_cycles()

    def _detect_cycles(self) -> None:
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError(f"Circular dependency detected at {task_id}.")
            if task_id in visited:
                return

            visiting.add(task_id)
            for dependency in self.tasks[task_id].dependencies:
                visit(dependency)

            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in self.tasks:
            visit(task_id)

    @property
    def start_date(self) -> date:
        return min(task.start for task in self.tasks.values())

    @property
    def end_date(self) -> date:
        return max(task.end for task in self.tasks.values())

    def critical_path(self) -> List[str]:
        self.validate_dependencies()

        ordered = self._topological_order()
        earliest_finish: Dict[str, int] = {}
        predecessor_for_longest: Dict[str, Optional[str]] = {}

        for task_id in ordered:
            task = self.tasks[task_id]

            if not task.dependencies:
                earliest_finish[task_id] = task.duration
                predecessor_for_longest[task_id] = None
            else:
                best_dependency = max(
                    task.dependencies,
                    key=lambda dep: earliest_finish[dep]
                )
                earliest_finish[task_id] = (
                    earliest_finish[best_dependency] + task.duration
                )
                predecessor_for_longest[task_id] = best_dependency

        final_task = max(earliest_finish, key=earliest_finish.get)
        path: List[str] = []

        while final_task is not None:
            path.append(final_task)
            final_task = predecessor_for_longest[final_task]

        return list(reversed(path))

    def _topological_order(self) -> List[str]:
        self.validate_dependencies_without_recursion()

        indegree = {task_id: 0 for task_id in self.tasks}
        successors: Dict[str, List[str]] = {
            task_id: [] for task_id in self.tasks
        }

        for task in self.tasks.values():
            for dependency in task.dependencies:
                indegree[task.task_id] += 1
                successors[dependency].append(task.task_id)

        queue = [
            task_id for task_id, degree in indegree.items() if degree == 0
        ]
        result: List[str] = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for successor in successors[current]:
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    queue.append(successor)

        if len(result) != len(self.tasks):
            raise ValueError("Cannot topologically sort a cyclic project.")

        return result

    def validate_dependencies_without_recursion(self) -> None:
        for task in self.tasks.values():
            for dependency in task.dependencies:
                if dependency not in self.tasks:
                    raise ValueError(
                        f"Task {task.task_id} depends on unknown task {dependency}."
                    )

    def resource_conflicts(self) -> Dict[str, List[str]]:
        conflicts: Dict[str, List[str]] = {}

        resources: Dict[str, List[Task]] = {}
        for task in self.tasks.values():
            if task.resource:
                resources.setdefault(task.resource, []).append(task)

        for resource, resource_tasks in resources.items():
            resource_tasks.sort(key=lambda item: item.start)

            for index, current in enumerate(resource_tasks):
                for other in resource_tasks[index + 1:]:
                    if other.start > current.end:
                        break

                    if (
                        current.start <= other.end
                        and other.start <= current.end
                    ):
                        conflicts.setdefault(resource, []).extend(
                            [current.task_id, other.task_id]
                        )

        for resource in conflicts:
            conflicts[resource] = sorted(set(conflicts[resource]))

        return conflicts

    def completion_summary(self) -> Dict[str, float]:
        total_duration = sum(task.duration for task in self.tasks.values())
        completed = sum(
            task.duration * task.progress / 100
            for task in self.tasks.values()
        )

        return {
            "planned_days": total_duration,
            "completed_equivalent_days": round(completed, 2),
            "completion_percentage": round(
                completed / total_duration * 100, 2
            ) if total_duration else 0.0,
        }

    def render_ascii(self) -> str:
        start = self.start_date
        end = self.end_date
        total_days = (end - start).days + 1

        lines = [
            f"\nGANTT CHART: {self.name}",
            f"Timeline: {start} to {end}",
            "",
        ]

        label_width = max(
            12,
            max(len(task.name) for task in self.tasks.values()) + 2
        )

        for task in sorted(self.tasks.values(), key=lambda item: item.start):
            offset = (task.start - start).days
            width = task.duration

            prefix = " " * offset
            bar = "#" * width

            if task.milestone:
                bar = "*"

            progress_marker = ""
            if not task.milestone and task.progress > 0:
                completed_width = max(
                    1, round(width * task.progress / 100)
                )
                completed_width = min(completed_width, width)
                progress_marker = "|" * completed_width

                if completed_width < width:
                    bar = progress_marker + "." * (
                        width - completed_width
                    )

            lines.append(
                f"{task.name:<{label_width}} "
                f"{prefix}{bar} "
                f"{task.start} -> {task.end} "
                f"({task.progress:.0f}%)"
            )

        lines.append("")
        lines.append(
            "Legend: # planned work, | completed portion, "
            ". remaining portion, * milestone"
        )

        if total_days > 100:
            lines.append(
                "Note: ASCII rendering is intended for compact schedules; "
                "calendar-based visualization is preferable for long projects."
            )

        return "\n".join(lines)

    def export_csv(self, filename: str) -> None:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "task_id",
                    "name",
                    "start",
                    "end",
                    "duration_days",
                    "dependencies",
                    "progress",
                    "resource",
                    "milestone",
                ]
            )

            for task in self.tasks.values():
                writer.writerow(
                    [
                        task.task_id,
                        task.name,
                        task.start.isoformat(),
                        task.end.isoformat(),
                        task.duration,
                        ",".join(task.dependencies),
                        task.progress,
                        task.resource or "",
                        task.milestone,
                    ]
                )

    def export_json(self, filename: str) -> None:
        data = {
            "project": self.name,
            "start": self.start_date.isoformat(),
            "end": self.end_date.isoformat(),
            "tasks": [
                {
                    "id": task.task_id,
                    "name": task.name,
                    "start": task.start.isoformat(),
                    "end": task.end.isoformat(),
                    "duration_days": task.duration,
                    "dependencies": task.dependencies,
                    "progress": task.progress,
                    "resource": task.resource,
                    "milestone": task.milestone,
                }
                for task in self.tasks.values()
            ],
        }

        Path(filename).write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def working_days(start: date, end: date) -> int:
    if end < start:
        raise ValueError("End date cannot precede start date.")

    current = start
    count = 0

    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)

    return count


def shift_by_working_days(start: date, number_of_days: int) -> date:
    if number_of_days < 0:
        raise ValueError("Number of working days cannot be negative.")

    current = start
    remaining = number_of_days

    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1

    return current


def build_project() -> GanttProject:
    project = GanttProject("Enterprise Analytics Platform")

    project.add_task(
        Task(
            "T01",
            "Requirements",
            date(2026, 10, 12),
            date(2026, 10, 16),
            progress=100,
            resource="Product",
        )
    )

    project.add_task(
        Task(
            "T02",
            "Architecture",
            date(2026, 10, 19),
            date(2026, 10, 23),
            ["T01"],
            progress=80,
            resource="Architecture",
        )
    )

    project.add_task(
        Task(
            "T03",
            "Database Design",
            date(2026, 10, 26),
            date(2026, 10, 30),
            ["T02"],
            progress=40,
            resource="Backend",
        )
    )

    project.add_task(
        Task(
            "T04",
            "API Development",
            date(2026, 10, 26),
            date(2026, 11, 6),
            ["T02"],
            progress=35,
            resource="Backend",
        )
    )

    project.add_task(
        Task(
            "T05",
            "Frontend Development",
            date(2026, 11, 2),
            date(2026, 11, 13),
            ["T02"],
            progress=20,
            resource="Frontend",
        )
    )

    project.add_task(
        Task(
            "T06",
            "Integration Testing",
            date(2026, 11, 16),
            date(2026, 11, 20),
            ["T03", "T04", "T05"],
            progress=0,
            resource="QA",
        )
    )

    project.add_task(
        Task(
            "T07",
            "Production Release",
            date(2026, 11, 23),
            date(2026, 11, 23),
            ["T06"],
            progress=0,
            resource="Release",
            milestone=True,
        )
    )

    return project


def demonstrate_validation() -> None:
    invalid = GanttProject("Invalid Schedule")

    invalid.add_task(
        Task(
            "A",
            "Design",
            date(2026, 10, 10),
            date(2026, 10, 15),
        )
    )

    invalid.add_task(
        Task(
            "B",
            "Implementation",
            date(2026, 10, 14),
            date(2026, 10, 20),
            ["A"],
        )
    )

    try:
        invalid.validate_dependencies()
    except ValueError as error:
        print(f"\nValidation correctly rejected the schedule: {error}")


def demonstrate_date_operations() -> None:
    start = parse_date("2026-10-12")
    end = parse_date("2026-10-23")

    print("\nCalendar calculations")
    print(f"Calendar days: {(end - start).days + 1}")
    print(f"Working days: {working_days(start, end)}")
    print(
        "Five working days after "
        f"{start}: {shift_by_working_days(start, 5)}"
    )


def main() -> None:
    project = build_project()

    project.validate_dependencies()

    print(project.render_ascii())

    print("\nCritical path")
    print(" -> ".join(project.critical_path()))

    print("\nResource conflicts")
    conflicts = project.resource_conflicts()
    if conflicts:
        for resource, tasks in conflicts.items():
            print(f"{resource}: {', '.join(tasks)}")
    else:
        print("No overlapping assignments detected.")

    print("\nCompletion")
    for key, value in project.completion_summary().items():
        print(f"{key}: {value}")

    demonstrate_date_operations()
    demonstrate_validation()

    output_directory = Path("gantt_output")
    output_directory.mkdir(exist_ok=True)

    project.export_csv(output_directory / "project_schedule.csv")
    project.export_json(output_directory / "project_schedule.json")

    print("\nExported:")
    print(output_directory / "project_schedule.csv")
    print(output_directory / "project_schedule.json")


if __name__ == "__main__":
    main()
