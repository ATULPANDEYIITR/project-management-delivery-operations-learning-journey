"""
Schedule Management: Introduction to Project Scheduling

A self-contained project scheduling engine demonstrating:
- Activities and durations
- Dependencies and dependency types
- Forward-pass scheduling
- Backward-pass scheduling
- Critical path identification
- Float/slack
- Milestones
- Schedule validation
- Resource-aware conflict detection
- Progress updates
- Schedule variance
- What-if duration analysis
- Schedule reporting

The implementation uses a small project scenario so that scheduling
mechanisms can be observed through executable behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple


class DependencyType(str, Enum):
    FINISH_TO_START = "FS"
    START_TO_START = "SS"
    FINISH_TO_FINISH = "FF"
    START_TO_FINISH = "SF"


@dataclass
class Resource:
    name: str
    capacity: int = 1


@dataclass
class Activity:
    activity_id: str
    name: str
    duration: int
    resources: List[str] = field(default_factory=list)
    milestone: bool = False
    percent_complete: float = 0.0

    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)

    early_start: int = 0
    early_finish: int = 0
    late_start: int = 0
    late_finish: int = 0
    total_float: int = 0

    actual_start: Optional[int] = None
    actual_finish: Optional[int] = None

    def validate(self) -> None:
        if not self.activity_id.strip():
            raise ValueError("Activity ID cannot be empty.")

        if not self.name.strip():
            raise ValueError(f"Activity {self.activity_id}: name cannot be empty.")

        if self.duration < 0:
            raise ValueError(
                f"Activity {self.activity_id}: duration cannot be negative."
            )

        if not 0 <= self.percent_complete <= 100:
            raise ValueError(
                f"Activity {self.activity_id}: percent_complete must be between 0 and 100."
            )

        if self.milestone and self.duration != 0:
            raise ValueError(
                f"Activity {self.activity_id}: milestones must have zero duration."
            )


@dataclass(frozen=True)
class Dependency:
    predecessor: str
    successor: str
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag: int = 0


class ScheduleError(Exception):
    """Raised when a schedule cannot be calculated safely."""


class ProjectSchedule:
    """
    Activity-on-node scheduling model.

    Time is represented as integer working-day offsets from project day zero.
    A duration of 3 means an activity occupies three schedule days.

    The engine focuses on the logical scheduling network rather than
    calendar-specific holidays or working-time calendars.
    """

    def __init__(self, project_name: str, start_date: date):
        self.project_name = project_name
        self.start_date = start_date
        self.activities: Dict[str, Activity] = {}
        self.dependencies: List[Dependency] = []
        self.resources: Dict[str, Resource] = {}

    def add_resource(self, name: str, capacity: int = 1) -> None:
        if not name.strip():
            raise ValueError("Resource name cannot be empty.")

        if capacity <= 0:
            raise ValueError("Resource capacity must be positive.")

        if name in self.resources:
            raise ValueError(f"Resource already exists: {name}")

        self.resources[name] = Resource(name=name, capacity=capacity)

    def add_activity(
        self,
        activity_id: str,
        name: str,
        duration: int,
        resources: Optional[List[str]] = None,
        milestone: bool = False,
    ) -> None:
        if activity_id in self.activities:
            raise ValueError(f"Activity already exists: {activity_id}")

        activity = Activity(
            activity_id=activity_id,
            name=name,
            duration=duration,
            resources=resources or [],
            milestone=milestone,
        )
        activity.validate()

        unknown_resources = [
            resource for resource in activity.resources
            if resource not in self.resources
        ]

        if unknown_resources:
            raise ValueError(
                f"Activity {activity_id} references unknown resources: "
                f"{unknown_resources}"
            )

        self.activities[activity_id] = activity

    def add_dependency(
        self,
        predecessor: str,
        successor: str,
        dependency_type: DependencyType = DependencyType.FINISH_TO_START,
        lag: int = 0,
    ) -> None:
        if predecessor not in self.activities:
            raise ValueError(f"Unknown predecessor activity: {predecessor}")

        if successor not in self.activities:
            raise ValueError(f"Unknown successor activity: {successor}")

        if predecessor == successor:
            raise ValueError("An activity cannot depend on itself.")

        if lag < 0:
            raise ValueError(
                "Negative lag is not supported by this introductory scheduling model."
            )

        dependency = Dependency(
            predecessor=predecessor,
            successor=successor,
            dependency_type=dependency_type,
            lag=lag,
        )

        if dependency in self.dependencies:
            raise ValueError("Duplicate dependency.")

        self.dependencies.append(dependency)
        self.activities[predecessor].successors.append(successor)
        self.activities[successor].predecessors.append(predecessor)

    def _dependency_map(self) -> Dict[str, List[Dependency]]:
        mapping = defaultdict(list)

        for dependency in self.dependencies:
            mapping[dependency.successor].append(dependency)

        return mapping

    def _topological_order(self) -> List[str]:
        """
        Returns activities in dependency order.

        A directed cycle makes a normal CPM network impossible because
        there is no valid activity ordering for the forward pass.
        """
        indegree = {activity_id: 0 for activity_id in self.activities}

        for dependency in self.dependencies:
            indegree[dependency.successor] += 1

        queue = deque(
            activity_id
            for activity_id, degree in indegree.items()
            if degree == 0
        )

        order = []

        while queue:
            current = queue.popleft()
            order.append(current)

            for successor in self.activities[current].successors:
                indegree[successor] -= 1

                if indegree[successor] == 0:
                    queue.append(successor)

        if len(order) != len(self.activities):
            raise ScheduleError(
                "Dependency cycle detected. The project network cannot be scheduled."
            )

        return order

    def validate_network(self) -> None:
        for activity in self.activities.values():
            activity.validate()

        self._topological_order()

    def _calculate_early_dates(
        self,
        activity: Activity,
        dependency_map: Dict[str, List[Dependency]],
    ) -> Tuple[int, int]:
        """
        Calculates earliest start/finish using the predecessor constraints.

        For a simple FS relationship:
            successor ES = predecessor EF + lag

        Other relationship types are handled explicitly because project
        scheduling is not limited to finish-to-start dependencies.
        """
        earliest_start = 0

        for dependency in dependency_map[activity.activity_id]:
            predecessor = self.activities[dependency.predecessor]

            if dependency.dependency_type == DependencyType.FINISH_TO_START:
                constraint = predecessor.early_finish + dependency.lag

            elif dependency.dependency_type == DependencyType.START_TO_START:
                constraint = predecessor.early_start + dependency.lag

            elif dependency.dependency_type == DependencyType.FINISH_TO_FINISH:
                constraint = (
                    predecessor.early_finish
                    + dependency.lag
                    - activity.duration
                )

            elif dependency.dependency_type == DependencyType.START_TO_FINISH:
                constraint = (
                    predecessor.early_start
                    + dependency.lag
                    - activity.duration
                )

            else:
                raise ScheduleError(
                    f"Unsupported dependency type: {dependency.dependency_type}"
                )

            earliest_start = max(earliest_start, constraint)

        return earliest_start, earliest_start + activity.duration

    def _calculate_late_dates(
        self,
        activity: Activity,
        project_finish: int,
    ) -> Tuple[int, int]:
        """
        Calculates latest dates from successor constraints.

        For FS:
            predecessor LF = successor LS - lag

        The calculation is performed in reverse dependency order.
        """
        successors = [
            dependency
            for dependency in self.dependencies
            if dependency.predecessor == activity.activity_id
        ]

        if not successors:
            return project_finish - activity.duration, project_finish

        latest_finish = project_finish

        for dependency in successors:
            successor = self.activities[dependency.successor]

            if dependency.dependency_type == DependencyType.FINISH_TO_START:
                constraint = successor.late_start - dependency.lag

            elif dependency.dependency_type == DependencyType.START_TO_START:
                constraint = successor.late_start - dependency.lag

            elif dependency.dependency_type == DependencyType.FINISH_TO_FINISH:
                constraint = successor.late_finish - dependency.lag

            elif dependency.dependency_type == DependencyType.START_TO_FINISH:
                constraint = successor.late_finish - dependency.lag

            else:
                raise ScheduleError(
                    f"Unsupported dependency type: {dependency.dependency_type}"
                )

            latest_finish = min(latest_finish, constraint)

        latest_start = latest_finish - activity.duration
        return latest_start, latest_finish

    def calculate(self) -> int:
        """
        Runs a Critical Path Method calculation.

        Returns the calculated project duration in schedule days.
        """
        self.validate_network()

        dependency_map = self._dependency_map()
        order = self._topological_order()

        for activity_id in order:
            activity = self.activities[activity_id]
            activity.early_start, activity.early_finish = (
                self._calculate_early_dates(activity, dependency_map)
            )

        project_finish = max(
            activity.early_finish
            for activity in self.activities.values()
        ) if self.activities else 0

        for activity_id in reversed(order):
            activity = self.activities[activity_id]

            (
                activity.late_start,
                activity.late_finish,
            ) = self._calculate_late_dates(
                activity,
                project_finish,
            )

            activity.total_float = (
                activity.late_start - activity.early_start
            )

        return project_finish

    def critical_activities(self) -> List[Activity]:
        self.calculate()

        return [
            activity
            for activity in self.activities.values()
            if activity.total_float == 0
        ]

    def critical_path(self) -> List[Activity]:
        """
        Returns one logical critical path.

        Multiple critical paths can exist in real schedules. This method
        follows zero-float activities through FS relationships to produce
        a representative path.
        """
        self.calculate()

        critical = {
            activity.activity_id
            for activity in self.critical_activities()
        }

        starts = [
            activity
            for activity in self.activities.values()
            if not activity.predecessors
            and activity.activity_id in critical
        ]

        if not starts:
            return []

        current = min(starts, key=lambda item: item.early_start)
        path = [current]

        while True:
            candidates = [
                self.activities[successor]
                for successor in current.successors
                if successor in critical
                and self.activities[successor].early_start == current.early_finish
            ]

            if not candidates:
                break

            current = min(candidates, key=lambda item: item.early_start)
            path.append(current)

        return path

    def day_to_date(self, offset: int) -> date:
        return self.start_date + timedelta(days=offset)

    def activity_dates(self, activity: Activity) -> Dict[str, date]:
        return {
            "early_start": self.day_to_date(activity.early_start),
            "early_finish": self.day_to_date(activity.early_finish),
            "late_start": self.day_to_date(activity.late_start),
            "late_finish": self.day_to_date(activity.late_finish),
        }

    def project_end_date(self) -> date:
        duration = self.calculate()
        return self.day_to_date(duration)

    def update_progress(
        self,
        activity_id: str,
        percent_complete: float,
        actual_start: Optional[int] = None,
        actual_finish: Optional[int] = None,
    ) -> None:
        if activity_id not in self.activities:
            raise ValueError(f"Unknown activity: {activity_id}")

        if not 0 <= percent_complete <= 100:
            raise ValueError("Progress must be between 0 and 100.")

        activity = self.activities[activity_id]
        activity.percent_complete = percent_complete
        activity.actual_start = actual_start
        activity.actual_finish = actual_finish

        if percent_complete == 100 and actual_finish is None:
            raise ValueError(
                "A completed activity should have an actual finish day."
            )

    def schedule_variance_days(
        self,
        activity_id: str,
        actual_finish: int,
    ) -> int:
        self.calculate()

        if activity_id not in self.activities:
            raise ValueError(f"Unknown activity: {activity_id}")

        activity = self.activities[activity_id]
        return actual_finish - activity.early_finish

    def resource_conflicts(self) -> List[Tuple[str, str, str]]:
        """
        Detects overlapping activities that use the same single-capacity resource.

        This is deliberately a conflict detector rather than a full resource
        leveling engine. CPM dates remain unchanged when a conflict exists.
        """
        self.calculate()

        conflicts = []

        for resource_name, resource in self.resources.items():
            if resource.capacity != 1:
                continue

            activities = [
                activity
                for activity in self.activities.values()
                if resource_name in activity.resources
                and activity.duration > 0
            ]

            for index, first in enumerate(activities):
                for second in activities[index + 1:]:
                    overlaps = (
                        first.early_start < second.early_finish
                        and second.early_start < first.early_finish
                    )

                    if overlaps:
                        conflicts.append(
                            (
                                resource_name,
                                first.activity_id,
                                second.activity_id,
                            )
                        )

        return conflicts

    def format_report(self) -> str:
        duration = self.calculate()
        critical_ids = {
            activity.activity_id
            for activity in self.critical_activities()
        }

        lines = [
            f"Project: {self.project_name}",
            f"Project start: {self.start_date.isoformat()}",
            f"Project duration: {duration} schedule days",
            f"Projected finish: {self.project_end_date().isoformat()}",
            "",
            "Activity Schedule",
            "-" * 100,
            (
                f"{'ID':<8}"
                f"{'Activity':<30}"
                f"{'ES':>5}"
                f"{'EF':>5}"
                f"{'LS':>5}"
                f"{'LF':>5}"
                f"{'Float':>7}"
                f"{'Progress':>10}"
                f"{'Critical':>10}"
            ),
            "-" * 100,
        ]

        for activity in sorted(
            self.activities.values(),
            key=lambda item: (item.early_start, item.activity_id),
        ):
            lines.append(
                f"{activity.activity_id:<8}"
                f"{activity.name[:29]:<30}"
                f"{activity.early_start:>5}"
                f"{activity.early_finish:>5}"
                f"{activity.late_start:>5}"
                f"{activity.late_finish:>5}"
                f"{activity.total_float:>7}"
                f"{activity.percent_complete:>9.0f}%"
                f"{'YES' if activity.activity_id in critical_ids else 'NO':>10}"
            )

        lines.extend(
            [
                "-" * 100,
                "",
                "Critical path:",
                " -> ".join(
                    f"{activity.activity_id} ({activity.name})"
                    for activity in self.critical_path()
                ),
            ]
        )

        conflicts = self.resource_conflicts()

        lines.append("")
        lines.append("Resource conflicts:")

        if not conflicts:
            lines.append("None detected.")
        else:
            for resource, first, second in conflicts:
                lines.append(
                    f"{resource}: {first} overlaps with {second}"
                )

        return "\n".join(lines)

    def clone_with_duration_change(
        self,
        activity_id: str,
        new_duration: int,
    ) -> "ProjectSchedule":
        """
        Creates a fresh schedule with one changed duration.

        This supports schedule what-if analysis without mutating the
        original baseline.
        """
        if activity_id not in self.activities:
            raise ValueError(f"Unknown activity: {activity_id}")

        if new_duration < 0:
            raise ValueError("New duration cannot be negative.")

        simulation = ProjectSchedule(
            project_name=f"{self.project_name} - What If",
            start_date=self.start_date,
        )

        for resource in self.resources.values():
            simulation.add_resource(resource.name, resource.capacity)

        for activity in self.activities.values():
            simulation.add_activity(
                activity_id=activity.activity_id,
                name=activity.name,
                duration=(
                    new_duration
                    if activity.activity_id == activity_id
                    else activity.duration
                ),
                resources=list(activity.resources),
                milestone=activity.milestone,
            )

        for dependency in self.dependencies:
            simulation.add_dependency(
                dependency.predecessor,
                dependency.successor,
                dependency.dependency_type,
                dependency.lag,
            )

        return simulation


def build_example_project() -> ProjectSchedule:
    """
    Builds a realistic software delivery schedule.

    The activities are intentionally connected through project-specific
    relationships so that the resulting network demonstrates scheduling
    mechanics rather than generic Python behavior.
    """
    project = ProjectSchedule(
        project_name="Customer Analytics Platform Release",
        start_date=date(2026, 10, 5),
    )

    project.add_resource("Product Manager")
    project.add_resource("Backend Engineer")
    project.add_resource("Frontend Engineer")
    project.add_resource("QA Engineer")
    project.add_resource("Security Engineer")

    project.add_activity(
        "A",
        "Requirements and acceptance criteria",
        3,
        ["Product Manager"],
    )
    project.add_activity(
        "B",
        "Architecture and API design",
        4,
        ["Backend Engineer"],
    )
    project.add_activity(
        "C",
        "Database implementation",
        5,
        ["Backend Engineer"],
    )
    project.add_activity(
        "D",
        "Backend API implementation",
        7,
        ["Backend Engineer"],
    )
    project.add_activity(
        "E",
        "Frontend dashboard implementation",
        6,
        ["Frontend Engineer"],
    )
    project.add_activity(
        "F",
        "Security review",
        3,
        ["Security Engineer"],
    )
    project.add_activity(
        "G",
        "Integration testing",
        5,
        ["QA Engineer"],
    )
    project.add_activity(
        "H",
        "User acceptance testing",
        4,
        ["Product Manager", "QA Engineer"],
    )
    project.add_activity(
        "I",
        "Production release",
        0,
        ["Backend Engineer"],
        milestone=True,
    )

    project.add_dependency("A", "B", DependencyType.FINISH_TO_START)
    project.add_dependency("B", "C", DependencyType.FINISH_TO_START)
    project.add_dependency("B", "D", DependencyType.FINISH_TO_START)
    project.add_dependency("A", "E", DependencyType.FINISH_TO_START)
    project.add_dependency("D", "F", DependencyType.FINISH_TO_START)
    project.add_dependency("C", "G", DependencyType.FINISH_TO_START)
    project.add_dependency("D", "G", DependencyType.FINISH_TO_START)
    project.add_dependency("E", "G", DependencyType.FINISH_TO_START)
    project.add_dependency("F", "G", DependencyType.FINISH_TO_START)
    project.add_dependency("G", "H", DependencyType.FINISH_TO_START)
    project.add_dependency("H", "I", DependencyType.FINISH_TO_START)

    return project


def demonstrate_dependency_types() -> None:
    """
    Demonstrates how relationship types change the schedule.

    These examples are kept separate from the main project so that the
    scheduling engine can be examined without changing the case study.
    """
    schedule = ProjectSchedule(
        "Dependency Relationship Demonstration",
        date(2026, 10, 5),
    )

    schedule.add_activity("DESIGN", "Design", 4)
    schedule.add_activity("BUILD", "Build", 6)
    schedule.add_activity("TEST", "Test", 3)

    schedule.add_dependency(
        "DESIGN",
        "BUILD",
        DependencyType.FINISH_TO_START,
    )

    schedule.add_dependency(
        "BUILD",
        "TEST",
        DependencyType.START_TO_START,
        lag=2,
    )

    schedule.calculate()

    print("\nDependency relationship example")
    print("-" * 50)

    for activity in schedule.activities.values():
        print(
            f"{activity.activity_id}: "
            f"ES={activity.early_start}, "
            f"EF={activity.early_finish}"
        )


def demonstrate_validation() -> None:
    """
    Shows schedule-network validation by deliberately constructing
    invalid dependency graphs and handling the resulting errors.
    """
    print("\nValidation examples")
    print("-" * 50)

    cyclic = ProjectSchedule(
        "Invalid Cyclic Schedule",
        date(2026, 10, 5),
    )

    cyclic.add_activity("A", "Design", 2)
    cyclic.add_activity("B", "Build", 3)
    cyclic.add_activity("C", "Test", 2)

    cyclic.add_dependency("A", "B")
    cyclic.add_dependency("B", "C")
    cyclic.add_dependency("C", "A")

    try:
        cyclic.calculate()
    except ScheduleError as error:
        print(f"Cycle rejected: {error}")

    invalid_milestone = ProjectSchedule(
        "Invalid Milestone Schedule",
        date(2026, 10, 5),
    )

    try:
        invalid_milestone.add_activity(
            "M1",
            "Release milestone",
            duration=2,
            milestone=True,
        )
    except ValueError as error:
        print(f"Invalid milestone rejected: {error}")


def demonstrate_progress_tracking(project: ProjectSchedule) -> None:
    """
    Updates project progress and calculates schedule variance for
    a completed activity.
    """
    project.update_progress(
        "A",
        percent_complete=100,
        actual_start=0,
        actual_finish=4,
    )

    project.update_progress(
        "B",
        percent_complete=50,
        actual_start=4,
    )

    variance = project.schedule_variance_days(
        "A",
        actual_finish=4,
    )

    print("\nProgress and variance")
    print("-" * 50)
    print("Requirements completion: 100%")
    print("Architecture completion: 50%")
    print(f"Requirements schedule variance: {variance} day(s)")


def demonstrate_what_if(project: ProjectSchedule) -> None:
    """
    Compares the baseline schedule with a scenario where backend API
    implementation takes longer.
    """
    baseline_duration = project.calculate()

    simulation = project.clone_with_duration_change(
        "D",
        project.activities["D"].duration + 3,
    )

    simulated_duration = simulation.calculate()

    print("\nWhat-if analysis")
    print("-" * 50)
    print(f"Baseline duration: {baseline_duration} days")
    print(f"Changed API duration: {simulation.activities['D'].duration} days")
    print(f"Simulated duration: {simulated_duration} days")
    print(
        f"Schedule impact: "
        f"{simulated_duration - baseline_duration:+d} day(s)"
    )


def main() -> None:
    project = build_example_project()

    print(project.format_report())

    demonstrate_dependency_types()
    demonstrate_validation()
    demonstrate_progress_tracking(project)
    demonstrate_what_if(project)

    print("\nCalendar dates for critical activities")
    print("-" * 50)

    for activity in project.critical_path():
        dates = project.activity_dates(activity)
        print(
            f"{activity.activity_id} - {activity.name}: "
            f"{dates['early_start']} to {dates['early_finish']}"
        )

    print("\nScheduling observations")
    print("-" * 50)
    print(
        "Critical activities have zero total float, so a delay to one "
        "of them can delay the calculated project finish."
    )
    print(
        "Non-critical activities can have scheduling flexibility, but "
        "that flexibility is limited by their calculated float."
    )
    print(
        "Resource conflicts are reported separately because a pure "
        "dependency network does not automatically perform resource leveling."
    )


if __name__ == "__main__":
    main()
