"""
Activity Identification
-----------------------
A self-contained implementation for identifying, validating, classifying, and
prioritizing project activities from project work descriptions.

The implementation moves from basic activity extraction to dependency-aware
activity identification, duplicate detection, milestone classification,
work-package grouping, risk checks, and schedule-oriented analysis.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
import re
from collections import defaultdict, deque
from typing import Iterable


class ActivityType(Enum):
    TASK = "task"
    MILESTONE = "milestone"
    DECISION = "decision"
    REVIEW = "review"
    HANDOFF = "handoff"


class ActivityStatus(Enum):
    IDENTIFIED = "identified"
    READY = "ready"
    BLOCKED = "blocked"
    COMPLETE = "complete"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Activity:
    activity_id: str
    name: str
    description: str
    activity_type: ActivityType = ActivityType.TASK
    owner: str | None = None
    duration_days: int = 1
    priority: Priority = Priority.MEDIUM
    dependencies: set[str] = field(default_factory=set)
    deliverable: str | None = None
    status: ActivityStatus = ActivityStatus.IDENTIFIED
    start_date: date | None = None
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.activity_id.strip():
            raise ValueError("Activity ID cannot be empty.")
        if not self.name.strip():
            raise ValueError("Activity name cannot be empty.")
        if self.duration_days < 0:
            raise ValueError("Duration cannot be negative.")
        if self.activity_type == ActivityType.MILESTONE and self.duration_days != 0:
            raise ValueError("Milestones must have zero duration.")

    @property
    def is_actionable(self) -> bool:
        return self.activity_type in {
            ActivityType.TASK,
            ActivityType.REVIEW,
            ActivityType.HANDOFF,
        }

    def normalized_name(self) -> str:
        return re.sub(r"[^a-z0-9]+", " ", self.name.lower()).strip()


class ActivityIdentificationError(Exception):
    """Raised when project activity identification produces an invalid model."""


class ActivityRegister:
    """
    Stores identified activities and enforces activity-level integrity.

    The register intentionally separates identification from scheduling.
    Identifying an activity means recognizing a piece of project work or a
    meaningful project event. Scheduling determines when that activity occurs.
    """

    def __init__(self) -> None:
        self._activities: dict[str, Activity] = {}

    def add(self, activity: Activity) -> None:
        if activity.activity_id in self._activities:
            raise ActivityIdentificationError(
                f"Duplicate activity ID: {activity.activity_id}"
            )

        if self._has_similar_name(activity):
            raise ActivityIdentificationError(
                f"Potential duplicate activity name: {activity.name}"
            )

        self._activities[activity.activity_id] = activity

    def get(self, activity_id: str) -> Activity:
        try:
            return self._activities[activity_id]
        except KeyError as exc:
            raise ActivityIdentificationError(
                f"Unknown activity: {activity_id}"
            ) from exc

    def all(self) -> list[Activity]:
        return list(self._activities.values())

    def _has_similar_name(self, candidate: Activity) -> bool:
        candidate_words = set(candidate.normalized_name().split())
        if not candidate_words:
            return False

        for existing in self._activities.values():
            existing_words = set(existing.normalized_name().split())
            intersection = candidate_words & existing_words
            union = candidate_words | existing_words

            similarity = len(intersection) / len(union) if union else 0
            if similarity >= 0.8:
                return True

        return False

    def validate_dependencies(self) -> list[str]:
        errors: list[str] = []

        for activity in self.all():
            for dependency in activity.dependencies:
                if dependency not in self._activities:
                    errors.append(
                        f"{activity.activity_id} depends on unknown "
                        f"activity {dependency}"
                    )

        if self._contains_cycle():
            errors.append("Dependency graph contains a cycle.")

        return errors

    def _contains_cycle(self) -> bool:
        graph = {
            activity.activity_id: set(activity.dependencies)
            for activity in self.all()
        }

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False

            visiting.add(node)
            for dependency in graph.get(node, set()):
                if dependency in graph and visit(dependency):
                    return True

            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in graph)


class ActivityExtractor:
    """
    Identifies candidate activities from natural-language project statements.

    This is deliberately rule-based. It does not pretend that every sentence
    can be perfectly converted into a schedule activity. Candidate extraction
    should be reviewed by the project team before becoming the final activity
    list.
    """

    ACTION_VERBS = {
        "analyze",
        "approve",
        "build",
        "configure",
        "design",
        "develop",
        "document",
        "evaluate",
        "implement",
        "inspect",
        "integrate",
        "migrate",
        "prepare",
        "review",
        "test",
        "validate",
        "deploy",
        "train",
        "identify",
        "collect",
        "define",
        "install",
    }

    def extract(self, text: str) -> list[str]:
        candidates: list[str] = []

        for sentence in re.split(r"[.!?]+", text):
            sentence = sentence.strip()
            if not sentence:
                continue

            words = sentence.lower().split()
            matching_verbs = [
                word.strip(",;:()")
                for word in words
                if word.strip(",;:()") in self.ACTION_VERBS
            ]

            if matching_verbs:
                candidates.append(sentence)

        return candidates


class ActivityAnalyzer:
    """Provides identification-quality analysis without creating a schedule."""

    def __init__(self, register: ActivityRegister) -> None:
        self.register = register

    def identify_orphan_activities(self) -> list[Activity]:
        referenced = {
            dependency
            for activity in self.register.all()
            for dependency in activity.dependencies
        }

        return [
            activity
            for activity in self.register.all()
            if activity.activity_id not in referenced
        ]

    def identify_activities_without_owner(self) -> list[Activity]:
        return [
            activity
            for activity in self.register.all()
            if activity.owner is None
        ]

    def identify_activities_without_deliverable(self) -> list[Activity]:
        return [
            activity
            for activity in self.register.all()
            if activity.is_actionable and not activity.deliverable
        ]

    def identify_high_risk_activities(self) -> list[Activity]:
        return [
            activity
            for activity in self.register.all()
            if (
                activity.priority in {Priority.HIGH, Priority.CRITICAL}
                or len(activity.dependencies) >= 3
            )
        ]

    def classify_by_work_package(self) -> dict[str, list[Activity]]:
        packages: dict[str, list[Activity]] = defaultdict(list)

        for activity in self.register.all():
            package = next(iter(activity.tags), "unclassified")
            packages[package].append(activity)

        return dict(packages)

    def activity_summary(self) -> dict[str, int]:
        summary: dict[str, int] = defaultdict(int)

        for activity in self.register.all():
            summary[activity.activity_type.value] += 1

        return dict(summary)


class DependencyAnalyzer:
    """Calculates dependency-aware ordering and identifies foundational work."""

    def __init__(self, register: ActivityRegister) -> None:
        self.register = register

    def topological_order(self) -> list[str]:
        errors = self.register.validate_dependencies()
        if errors:
            raise ActivityIdentificationError("; ".join(errors))

        indegree = {
            activity.activity_id: len(activity.dependencies)
            for activity in self.register.all()
        }

        successors: dict[str, set[str]] = defaultdict(set)

        for activity in self.register.all():
            for dependency in activity.dependencies:
                successors[dependency].add(activity.activity_id)

        ready = deque(
            sorted(activity_id for activity_id, degree in indegree.items() if degree == 0)
        )

        ordered: list[str] = []

        while ready:
            current = ready.popleft()
            ordered.append(current)

            for successor in sorted(successors[current]):
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    ready.append(successor)

        if len(ordered) != len(indegree):
            raise ActivityIdentificationError(
                "Unable to order activities because the dependency graph is cyclic."
            )

        return ordered

    def identify_foundational_activities(self) -> list[Activity]:
        return [
            self.register.get(activity_id)
            for activity_id in self.topological_order()
            if not self.register.get(activity_id).dependencies
        ]


class SimpleActivityScheduler:
    """
    Converts identified activities into an earliest-start schedule.

    This is intentionally a simple planning model. Real project schedules may
    include resource calendars, working-time rules, lag, leads, constraints,
    calendars, and resource leveling.
    """

    def __init__(self, register: ActivityRegister, project_start: date) -> None:
        self.register = register
        self.project_start = project_start

    def schedule(self) -> dict[str, tuple[date, date]]:
        dependency_analyzer = DependencyAnalyzer(self.register)
        order = dependency_analyzer.topological_order()

        results: dict[str, tuple[date, date]] = {}

        for activity_id in order:
            activity = self.register.get(activity_id)

            earliest_start = self.project_start

            for dependency_id in activity.dependencies:
                _, dependency_finish = results[dependency_id]
                candidate_start = dependency_finish + timedelta(days=1)
                earliest_start = max(earliest_start, candidate_start)

            if activity.duration_days == 0:
                finish = earliest_start
            else:
                finish = earliest_start + timedelta(days=activity.duration_days - 1)

            activity.start_date = earliest_start
            results[activity_id] = (earliest_start, finish)

        return results


def demonstrate_basic_identification() -> None:
    print("\n=== Activity Identification Fundamentals ===")

    project_statement = (
        "Analyze stakeholder requirements. "
        "Design the reporting workflow. "
        "Develop the reporting service. "
        "Test the reporting service. "
        "Approve the production release."
    )

    extractor = ActivityExtractor()
    candidates = extractor.extract(project_statement)

    for candidate in candidates:
        print(f"Candidate activity: {candidate}")

    print(
        "\nIdentification extracts actionable project work from a project "
        "description, but candidate activities still require validation."
    )


def build_realistic_project() -> ActivityRegister:
    register = ActivityRegister()

    activities = [
        Activity(
            "ACT-001",
            "Identify stakeholder reporting requirements",
            "Collect and validate reporting needs from finance, operations, and leadership.",
            owner="Business Analyst",
            duration_days=3,
            priority=Priority.HIGH,
            deliverable="Validated requirements register",
            tags={"requirements"},
        ),
        Activity(
            "ACT-002",
            "Define reporting data model",
            "Define the entities, relationships, dimensions, and measures required by the reporting solution.",
            owner="Data Architect",
            duration_days=4,
            priority=Priority.HIGH,
            dependencies={"ACT-001"},
            deliverable="Approved data model",
            tags={"data"},
        ),
        Activity(
            "ACT-003",
            "Design dashboard workflow",
            "Translate approved reporting requirements into dashboard navigation and interaction flows.",
            owner="Product Designer",
            duration_days=3,
            dependencies={"ACT-001"},
            deliverable="Dashboard workflow specification",
            tags={"design"},
        ),
        Activity(
            "ACT-004",
            "Develop reporting data pipeline",
            "Implement extraction, validation, transformation, and loading of reporting data.",
            owner="Data Engineer",
            duration_days=6,
            priority=Priority.HIGH,
            dependencies={"ACT-002"},
            deliverable="Validated reporting pipeline",
            tags={"data"},
        ),
        Activity(
            "ACT-005",
            "Develop dashboard interface",
            "Implement the dashboard views and interactions defined by the approved workflow.",
            owner="Frontend Engineer",
            duration_days=5,
            dependencies={"ACT-003", "ACT-004"},
            deliverable="Functional dashboard",
            tags={"development"},
        ),
        Activity(
            "ACT-006",
            "Perform integration testing",
            "Verify that the data pipeline and dashboard operate correctly together.",
            owner="QA Engineer",
            duration_days=4,
            priority=Priority.HIGH,
            dependencies={"ACT-005"},
            deliverable="Integration test report",
            tags={"quality"},
        ),
        Activity(
            "ACT-007",
            "Review production readiness",
            "Review operational, security, support, and deployment readiness before release.",
            activity_type=ActivityType.REVIEW,
            owner="Release Manager",
            duration_days=2,
            priority=Priority.CRITICAL,
            dependencies={"ACT-006"},
            deliverable="Production readiness decision",
            tags={"release"},
        ),
        Activity(
            "ACT-008",
            "Production release milestone",
            "Represents the approved point at which the reporting solution becomes operational.",
            activity_type=ActivityType.MILESTONE,
            owner="Release Manager",
            duration_days=0,
            priority=Priority.CRITICAL,
            dependencies={"ACT-007"},
            deliverable="Production release",
            tags={"release"},
        ),
    ]

    for activity in activities:
        register.add(activity)

    return register


def demonstrate_validation(register: ActivityRegister) -> None:
    print("\n=== Identification Quality Validation ===")

    errors = register.validate_dependencies()

    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Dependency references and dependency graph are valid.")

    analyzer = ActivityAnalyzer(register)

    missing_owner = analyzer.identify_activities_without_owner()
    missing_deliverable = analyzer.identify_activities_without_deliverable()
    high_risk = analyzer.identify_high_risk_activities()

    print(f"Activities without owners: {len(missing_owner)}")
    print(f"Actionable activities without deliverables: {len(missing_deliverable)}")
    print(f"High-risk or dependency-heavy activities: {len(high_risk)}")


def demonstrate_dependency_analysis(register: ActivityRegister) -> None:
    print("\n=== Dependency-Aware Activity Analysis ===")

    analyzer = DependencyAnalyzer(register)
    order = analyzer.topological_order()

    print("Dependency order:")
    for activity_id in order:
        activity = register.get(activity_id)
        dependencies = ", ".join(sorted(activity.dependencies)) or "none"
        print(f"{activity_id}: {activity.name} | depends on: {dependencies}")

    foundational = analyzer.identify_foundational_activities()

    print("\nFoundational activities:")
    for activity in foundational:
        print(f"- {activity.activity_id}: {activity.name}")


def demonstrate_schedule(register: ActivityRegister) -> None:
    print("\n=== Earliest-Start Activity Schedule ===")

    scheduler = SimpleActivityScheduler(register, date(2026, 10, 5))
    schedule = scheduler.schedule()

    for activity_id, (start, finish) in schedule.items():
        activity = register.get(activity_id)
        print(
            f"{activity_id}: {activity.name}\n"
            f"  Type: {activity.activity_type.value}\n"
            f"  Start: {start.isoformat()}\n"
            f"  Finish: {finish.isoformat()}\n"
        )


def demonstrate_failure_conditions() -> None:
    print("\n=== Failure Conditions ===")

    broken = ActivityRegister()

    broken.add(
        Activity(
            "BROKEN-001",
            "Validate requirements",
            "Validate requirements before design.",
            duration_days=2,
            deliverable="Validation report",
        )
    )

    invalid = Activity(
        "BROKEN-002",
        "Build dashboard",
        "Build dashboard without an identified prerequisite.",
        duration_days=3,
        dependencies={"MISSING-001"},
        deliverable="Dashboard",
    )

    broken.add(invalid)

    errors = broken.validate_dependencies()

    for error in errors:
        print(f"Detected: {error}")

    cyclic = ActivityRegister()

    cyclic.add(
        Activity(
            "CYCLE-A",
            "Design release workflow",
            "Design release workflow.",
            dependencies={"CYCLE-B"},
            deliverable="Workflow",
        )
    )

    cyclic.add(
        Activity(
            "CYCLE-B",
            "Validate release workflow",
            "Validate the workflow.",
            dependencies={"CYCLE-A"},
            deliverable="Validation",
        )
    )

    cycle_errors = cyclic.validate_dependencies()

    for error in cycle_errors:
        print(f"Detected: {error}")


def demonstrate_project_structure(register: ActivityRegister) -> None:
    print("\n=== Work-Package View ===")

    analyzer = ActivityAnalyzer(register)
    packages = analyzer.classify_by_work_package()

    for package, activities in sorted(packages.items()):
        print(f"\n[{package}]")
        for activity in activities:
            print(
                f"  {activity.activity_id} | "
                f"{activity.name} | "
                f"{activity.activity_type.value}"
            )

    print("\nActivity type distribution:")
    for activity_type, count in sorted(analyzer.activity_summary().items()):
        print(f"  {activity_type}: {count}")


def main() -> None:
    print("PROJECT ACTIVITY IDENTIFICATION ENGINE")
    print("Identifying project activities before detailed schedule control.")

    demonstrate_basic_identification()

    register = build_realistic_project()

    demonstrate_validation(register)
    demonstrate_dependency_analysis(register)
    demonstrate_project_structure(register)
    demonstrate_schedule(register)
    demonstrate_failure_conditions()

    print("\nActivity identification model completed successfully.")


if __name__ == "__main__":
    main()
