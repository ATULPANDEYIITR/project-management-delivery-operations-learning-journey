from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable
import csv
import json
import math


DATE_FORMAT = "%Y-%m-%d"


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Expected YYYY-MM-DD.") from exc


def business_days_between(start: date, end: date) -> int:
    if end < start:
        return 0
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days


def add_business_days(start: date, number_of_days: int) -> date:
    if number_of_days < 0:
        raise ValueError("number_of_days must not be negative")

    current = start
    remaining = number_of_days

    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1

    return current


@dataclass
class Milestone:
    name: str
    due_date: date
    description: str = ""
    completed: bool = False

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Milestone name cannot be empty")


@dataclass
class Task:
    task_id: str
    name: str
    start: date
    end: date
    owner: str
    category: str
    dependencies: list[str] = field(default_factory=list)
    progress: int = 0
    priority: str = "medium"
    completed: bool = False

    def validate(self) -> None:
        if not self.task_id.strip():
            raise ValueError("Task ID cannot be empty")
        if not self.name.strip():
            raise ValueError(f"Task {self.task_id} has no name")
        if self.end < self.start:
            raise ValueError(f"Task {self.task_id} ends before it starts")
        if not 0 <= self.progress <= 100:
            raise ValueError(f"Task {self.task_id} progress must be 0-100")
        if self.priority not in {"low", "medium", "high", "critical"}:
            raise ValueError(f"Unsupported priority: {self.priority}")


@dataclass
class ProjectTimeline:
    project_name: str
    tasks: dict[str, Task] = field(default_factory=dict)
    milestones: list[Milestone] = field(default_factory=list)
    holidays: set[date] = field(default_factory=set)

    def add_task(self, task: Task) -> None:
        task.validate()
        if task.task_id in self.tasks:
            raise ValueError(f"Duplicate task ID: {task.task_id}")

        for dependency in task.dependencies:
            if dependency == task.task_id:
                raise ValueError(f"Task {task.task_id} cannot depend on itself")

        self.tasks[task.task_id] = task

    def add_milestone(self, milestone: Milestone) -> None:
        milestone.validate()
        self.milestones.append(milestone)

    def project_start(self) -> date:
        dates = [task.start for task in self.tasks.values()]
        if not dates:
            raise ValueError("Timeline contains no tasks")
        return min(dates)

    def project_end(self) -> date:
        dates = [task.end for task in self.tasks.values()]
        if not dates:
            raise ValueError("Timeline contains no tasks")
        return max(dates)

    def duration_calendar_days(self) -> int:
        return (self.project_end() - self.project_start()).days + 1

    def validate_dependencies(self) -> list[str]:
        errors: list[str] = []

        for task in self.tasks.values():
            for dependency_id in task.dependencies:
                dependency = self.tasks.get(dependency_id)
                if dependency is None:
                    errors.append(
                        f"{task.task_id} depends on missing task {dependency_id}"
                    )
                elif dependency.end >= task.start:
                    errors.append(
                        f"{task.task_id} starts on {task.start} before "
                        f"dependency {dependency_id} finishes on {dependency.end}"
                    )

        return errors

    def detect_dependency_cycle(self) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> bool:
            if task_id in visiting:
                return True
            if task_id in visited:
                return False

            visiting.add(task_id)

            for dependency_id in self.tasks[task_id].dependencies:
                if dependency_id in self.tasks and visit(dependency_id):
                    return True

            visiting.remove(task_id)
            visited.add(task_id)
            return False

        return any(visit(task_id) for task_id in self.tasks)

    def critical_path(self) -> tuple[list[str], int]:
        errors = self.validate_dependencies()
        if errors:
            raise ValueError(
                "Cannot calculate critical path with invalid dependencies:\n"
                + "\n".join(errors)
            )

        if self.detect_dependency_cycle():
            raise ValueError("Cannot calculate critical path for a cyclic timeline")

        ordered = sorted(self.tasks.values(), key=lambda task: task.end)
        longest_finish: dict[str, int] = {}
        predecessor: dict[str, str | None] = {}

        for task in ordered:
            own_duration = (task.end - task.start).days + 1
            best_previous: str | None = None
            best_finish = 0

            for dependency_id in task.dependencies:
                candidate = longest_finish[dependency_id]
                if candidate > best_finish:
                    best_finish = candidate
                    best_previous = dependency_id

            longest_finish[task.task_id] = best_finish + own_duration
            predecessor[task.task_id] = best_previous

        final_task = max(longest_finish, key=longest_finish.get)
        path: list[str] = []

        current: str | None = final_task
        while current is not None:
            path.append(current)
            current = predecessor[current]

        path.reverse()
        return path, longest_finish[final_task]

    def calculate_progress(self) -> float:
        if not self.tasks:
            return 0.0

        weighted_total = 0
        total_weight = 0

        for task in self.tasks.values():
            duration = max((task.end - task.start).days + 1, 1)
            weighted_total += task.progress * duration
            total_weight += duration

        return weighted_total / total_weight

    def resource_workload(self) -> dict[str, int]:
        workload: dict[str, int] = {}

        for task in self.tasks.values():
            days = (task.end - task.start).days + 1
            workload[task.owner] = workload.get(task.owner, 0) + days

        return workload

    def milestone_status(self, as_of: date) -> list[dict[str, object]]:
        result = []

        for milestone in sorted(self.milestones, key=lambda item: item.due_date):
            if milestone.completed:
                status = "completed"
            elif milestone.due_date < as_of:
                status = "overdue"
            elif milestone.due_date <= as_of + timedelta(days=7):
                status = "due_soon"
            else:
                status = "upcoming"

            result.append(
                {
                    "name": milestone.name,
                    "due_date": milestone.due_date.isoformat(),
                    "status": status,
                }
            )

        return result

    def identify_schedule_risks(self, as_of: date) -> list[str]:
        risks: list[str] = []

        for task in self.tasks.values():
            if task.end < as_of and task.progress < 100:
                risks.append(
                    f"Overdue task: {task.task_id} '{task.name}' "
                    f"is {task.progress}% complete."
                )

            if task.start <= as_of <= task.end and task.progress == 0:
                risks.append(
                    f"Not started: {task.task_id} '{task.name}' "
                    "is currently scheduled."
                )

            if task.priority in {"high", "critical"} and task.progress < 50:
                risks.append(
                    f"High-risk progress: {task.task_id} '{task.name}' "
                    f"has priority {task.priority} and only {task.progress}% progress."
                )

        for error in self.validate_dependencies():
            risks.append(f"Dependency risk: {error}")

        return risks

    def export_json(self, path: str | Path) -> None:
        output = {
            "project_name": self.project_name,
            "tasks": [
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "start": task.start.isoformat(),
                    "end": task.end.isoformat(),
                    "owner": task.owner,
                    "category": task.category,
                    "dependencies": task.dependencies,
                    "progress": task.progress,
                    "priority": task.priority,
                    "completed": task.completed,
                }
                for task in self.tasks.values()
            ],
            "milestones": [
                {
                    "name": milestone.name,
                    "due_date": milestone.due_date.isoformat(),
                    "description": milestone.description,
                    "completed": milestone.completed,
                }
                for milestone in self.milestones
            ],
        }

        Path(path).write_text(
            json.dumps(output, indent=2),
            encoding="utf-8",
        )

    def export_csv(self, path: str | Path) -> None:
        with Path(path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "task_id",
                    "name",
                    "start",
                    "end",
                    "owner",
                    "category",
                    "dependencies",
                    "progress",
                    "priority",
                ]
            )

            for task in self.tasks.values():
                writer.writerow(
                    [
                        task.task_id,
                        task.name,
                        task.start.isoformat(),
                        task.end.isoformat(),
                        task.owner,
                        task.category,
                        ",".join(task.dependencies),
                        task.progress,
                        task.priority,
                    ]
                )

    def render_ascii_timeline(self, width: int = 72) -> str:
        start = self.project_start()
        end = self.project_end()
        total_days = max((end - start).days + 1, 1)

        lines = [
            f"PROJECT TIMELINE: {self.project_name}",
            f"{start} -> {end} ({total_days} calendar days)",
            "",
        ]

        for task in sorted(self.tasks.values(), key=lambda item: (item.start, item.task_id)):
            offset = round((task.start - start).days / total_days * width)
            span = max(
                1,
                round(((task.end - task.start).days + 1) / total_days * width),
            )

            bar = " " * offset + "#" * min(span, width - offset)
            lines.append(
                f"{task.task_id:<7} {task.name:<30} |{bar:<{width}}| "
                f"{task.progress:>3}%"
            )

        return "\n".join(lines)


def create_realistic_timeline() -> ProjectTimeline:
    timeline = ProjectTimeline("Operations Analytics Platform")

    timeline.add_task(
        Task(
            "T01",
            "Project kickoff and scope confirmation",
            date(2026, 10, 12),
            date(2026, 10, 13),
            "Project Manager",
            "Initiation",
            progress=100,
            priority="high",
            completed=True,
        )
    )

    timeline.add_task(
        Task(
            "T02",
            "Requirements and stakeholder workshops",
            date(2026, 10, 14),
            date(2026, 10, 20),
            "Business Analyst",
            "Requirements",
            dependencies=["T01"],
            progress=75,
            priority="high",
        )
    )

    timeline.add_task(
        Task(
            "T03",
            "Data architecture and source assessment",
            date(2026, 10, 19),
            date(2026, 10, 26),
            "Data Architect",
            "Architecture",
            dependencies=["T02"],
            progress=40,
            priority="high",
        )
    )

    timeline.add_task(
        Task(
            "T04",
            "Prototype analytics pipeline",
            date(2026, 10, 27),
            date(2026, 11, 5),
            "Data Engineer",
            "Engineering",
            dependencies=["T03"],
            progress=20,
            priority="critical",
        )
    )

    timeline.add_task(
        Task(
            "T05",
            "Operational dashboard development",
            date(2026, 11, 2),
            date(2026, 11, 12),
            "Application Engineer",
            "Development",
            dependencies=["T03"],
            progress=10,
            priority="medium",
        )
    )

    timeline.add_task(
        Task(
            "T06",
            "User acceptance testing",
            date(2026, 11, 13),
            date(2026, 11, 19),
            "QA Lead",
            "Testing",
            dependencies=["T04", "T05"],
            progress=0,
            priority="high",
        )
    )

    timeline.add_task(
        Task(
            "T07",
            "Production deployment and handover",
            date(2026, 11, 20),
            date(2026, 11, 23),
            "Release Manager",
            "Deployment",
            dependencies=["T06"],
            progress=0,
            priority="critical",
        )
    )

    timeline.add_milestone(
        Milestone(
            "Scope baseline approved",
            date(2026, 10, 20),
            "Approved requirements baseline",
            completed=False,
        )
    )
    timeline.add_milestone(
        Milestone(
            "Prototype ready",
            date(2026, 11, 5),
            "Demonstrable analytics pipeline",
        )
    )
    timeline.add_milestone(
        Milestone(
            "Production release",
            date(2026, 11, 23),
            "Operational handover complete",
        )
    )

    return timeline


def demonstrate_business_day_calculation() -> None:
    print("\nBUSINESS-DAY CALCULATION")
    start = date(2026, 10, 12)
    end = date(2026, 10, 23)

    print(f"Calendar range: {start} -> {end}")
    print(f"Business days: {business_days_between(start, end)}")
    print(f"Ten business days after start: {add_business_days(start, 10)}")


def demonstrate_dependency_validation(timeline: ProjectTimeline) -> None:
    print("\nDEPENDENCY VALIDATION")
    errors = timeline.validate_dependencies()

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print("All task dependencies are temporally valid.")

    print(f"Dependency cycle detected: {timeline.detect_dependency_cycle()}")


def demonstrate_critical_path(timeline: ProjectTimeline) -> None:
    print("\nCRITICAL PATH")
    path, duration = timeline.critical_path()
    print(" -> ".join(path))
    print(f"Sequential critical-path duration: {duration} days")


def demonstrate_progress_and_risk(timeline: ProjectTimeline) -> None:
    as_of = date(2026, 11, 10)

    print("\nPROJECT HEALTH")
    print(f"Weighted schedule progress: {timeline.calculate_progress():.1f}%")

    print("\nRESOURCE WORKLOAD")
    for owner, days in sorted(timeline.resource_workload().items()):
        print(f"{owner}: {days} calendar task-days")

    print("\nMILESTONE STATUS")
    for item in timeline.milestone_status(as_of):
        print(
            f"{item['due_date']} | {item['status']:<10} | {item['name']}"
        )

    print("\nSCHEDULE RISKS")
    risks = timeline.identify_schedule_risks(as_of)
    if risks:
        for risk in risks:
            print(f"- {risk}")
    else:
        print("No schedule risks detected.")


def demonstrate_invalid_timeline() -> None:
    print("\nVALIDATION EDGE CASES")

    invalid = ProjectTimeline("Invalid Example")

    try:
        invalid.add_task(
            Task(
                "BAD1",
                "Task with invalid date range",
                date(2026, 12, 10),
                date(2026, 12, 1),
                "Engineer",
                "Development",
            )
        )
    except ValueError as exc:
        print(f"Caught invalid date range: {exc}")

    try:
        invalid.add_task(
            Task(
                "BAD2",
                "Task with invalid progress",
                date(2026, 12, 1),
                date(2026, 12, 2),
                "Engineer",
                "Development",
                progress=140,
            )
        )
    except ValueError as exc:
        print(f"Caught invalid progress: {exc}")


def main() -> None:
    timeline = create_realistic_timeline()

    print(timeline.render_ascii_timeline())
    print(f"\nProject duration: {timeline.duration_calendar_days()} calendar days")

    demonstrate_business_day_calculation()
    demonstrate_dependency_validation(timeline)
    demonstrate_critical_path(timeline)
    demonstrate_progress_and_risk(timeline)
    demonstrate_invalid_timeline()

    output_dir = Path("timeline_output")
    output_dir.mkdir(exist_ok=True)

    timeline.export_json(output_dir / "project_timeline.json")
    timeline.export_csv(output_dir / "project_timeline.csv")

    print("\nEXPORT")
    print(f"JSON: {output_dir / 'project_timeline.json'}")
    print(f"CSV:  {output_dir / 'project_timeline.csv'}")


if __name__ == "__main__":
    main()
