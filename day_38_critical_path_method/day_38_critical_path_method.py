"""
Critical Path Method (CPM): Understanding Critical Activities

A self-contained learning and simulation program for identifying the critical
path, critical activities, earliest/latest schedule values, float, and the
effect of delays in a project network.

The implementation uses activity-on-node representation:
    Activity -> duration -> predecessor activities

The core CPM calculations are:
    Forward pass:
        ES = maximum EF of all predecessors
        EF = ES + duration

    Backward pass:
        LF = minimum LS of all successors
        LS = LF - duration

    Total Float:
        Float = LS - ES = LF - EF

An activity is critical when its total float is zero.

The program also demonstrates:
    - dependency validation
    - cycle detection
    - multiple predecessors
    - multiple project-ending activities
    - critical path reconstruction
    - schedule impact from activity delays
    - project-level sensitivity
    - activity classification
    - human-readable schedule reporting
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Dict, Iterable, List, Optional, Set, Tuple


EPSILON = 1e-9


@dataclass(frozen=True)
class Activity:
    """A project activity and the activities that must finish before it starts."""

    id: str
    name: str
    duration: float
    predecessors: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Activity ID cannot be empty.")
        if not self.name.strip():
            raise ValueError(f"Activity {self.id!r} must have a name.")
        if self.duration < 0:
            raise ValueError(
                f"Activity {self.id!r} cannot have a negative duration."
            )


@dataclass
class ScheduleEntry:
    """Calculated CPM schedule information for one activity."""

    activity: Activity
    earliest_start: float = 0.0
    earliest_finish: float = 0.0
    latest_start: float = 0.0
    latest_finish: float = 0.0
    total_float: float = 0.0

    @property
    def is_critical(self) -> bool:
        return abs(self.total_float) <= EPSILON


class CPMProject:
    """
    Project network and CPM calculation engine.

    The graph is directed from predecessor to successor. An edge A -> B
    means B cannot start until A has finished.
    """

    def __init__(self, activities: Iterable[Activity]) -> None:
        self.activities: Dict[str, Activity] = {}

        for activity in activities:
            if activity.id in self.activities:
                raise ValueError(f"Duplicate activity ID: {activity.id}")
            self.activities[activity.id] = activity

        self.successors: Dict[str, List[str]] = defaultdict(list)
        self._validate_dependencies()
        self._build_successor_graph()

        self.order = self._topological_order()
        self.schedule: Dict[str, ScheduleEntry] = {}

    def _validate_dependencies(self) -> None:
        """Ensure every predecessor refers to an existing activity."""
        for activity in self.activities.values():
            if len(set(activity.predecessors)) != len(activity.predecessors):
                raise ValueError(
                    f"Activity {activity.id} contains duplicate predecessors."
                )

            for predecessor in activity.predecessors:
                if predecessor not in self.activities:
                    raise ValueError(
                        f"Activity {activity.id} references unknown "
                        f"predecessor {predecessor!r}."
                    )

                if predecessor == activity.id:
                    raise ValueError(
                        f"Activity {activity.id} cannot depend on itself."
                    )

    def _build_successor_graph(self) -> None:
        """Build reverse dependency information for the backward pass."""
        for activity in self.activities.values():
            self.successors.setdefault(activity.id, [])

        for activity in self.activities.values():
            for predecessor in activity.predecessors:
                self.successors[predecessor].append(activity.id)

    def _topological_order(self) -> List[str]:
        """
        Return a valid dependency order.

        Kahn's algorithm also detects circular dependencies. CPM requires a
        directed acyclic graph because an activity cannot logically wait on
        itself through a dependency cycle.
        """
        indegree = {activity_id: 0 for activity_id in self.activities}

        for activity in self.activities.values():
            for predecessor in activity.predecessors:
                indegree[activity.id] += 1

        queue = deque(
            activity_id
            for activity_id, degree in indegree.items()
            if degree == 0
        )

        order: List[str] = []

        while queue:
            current = queue.popleft()
            order.append(current)

            for successor in self.successors[current]:
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    queue.append(successor)

        if len(order) != len(self.activities):
            remaining = [
                activity_id
                for activity_id, degree in indegree.items()
                if degree > 0
            ]
            raise ValueError(
                "Project contains a dependency cycle involving: "
                + ", ".join(sorted(remaining))
            )

        return order

    def calculate(self) -> Dict[str, ScheduleEntry]:
        """
        Calculate the complete CPM schedule.

        The forward pass determines when activities can happen as early as
        possible. The backward pass determines how late each activity can
        occur without extending the project completion time.
        """
        schedule: Dict[str, ScheduleEntry] = {}

        # Forward pass.
        for activity_id in self.order:
            activity = self.activities[activity_id]

            if activity.predecessors:
                earliest_start = max(
                    schedule[pred].earliest_finish
                    for pred in activity.predecessors
                )
            else:
                earliest_start = 0.0

            earliest_finish = earliest_start + activity.duration

            schedule[activity_id] = ScheduleEntry(
                activity=activity,
                earliest_start=earliest_start,
                earliest_finish=earliest_finish,
            )

        project_duration = max(
            entry.earliest_finish for entry in schedule.values()
        )

        # Activities without successors are project-ending activities.
        terminal_activities = [
            activity_id
            for activity_id in self.activities
            if not self.successors[activity_id]
        ]

        # Backward pass.
        for activity_id in reversed(self.order):
            entry = schedule[activity_id]
            successors = self.successors[activity_id]

            if not successors:
                latest_finish = project_duration
            else:
                latest_finish = min(
                    schedule[successor].latest_start
                    for successor in successors
                )

            latest_start = latest_finish - entry.activity.duration
            total_float = latest_start - entry.earliest_start

            entry.latest_finish = latest_finish
            entry.latest_start = latest_start
            entry.total_float = max(0.0, total_float)

        self.schedule = schedule

        # A disconnected ending activity still has project-level impact if
        # it determines the maximum project completion time.
        if not terminal_activities:
            raise ValueError("Project has no terminal activity.")

        return schedule

    @property
    def project_duration(self) -> float:
        if not self.schedule:
            self.calculate()

        return max(
            entry.earliest_finish for entry in self.schedule.values()
        )

    def critical_activities(self) -> List[ScheduleEntry]:
        if not self.schedule:
            self.calculate()

        return [
            self.schedule[activity_id]
            for activity_id in self.order
            if self.schedule[activity_id].is_critical
        ]

    def critical_paths(self) -> List[List[str]]:
        """
        Reconstruct all zero-float paths from project start to project end.

        An activity can belong to a critical path only when:
        - it has zero float;
        - its timing connects exactly to a zero-float successor.
        """
        if not self.schedule:
            self.calculate()

        critical_ids = {
            activity_id
            for activity_id, entry in self.schedule.items()
            if entry.is_critical
        }

        starts = [
            activity_id
            for activity_id in self.order
            if activity_id in critical_ids
            and not any(
                predecessor in critical_ids
                for predecessor in self.activities[activity_id].predecessors
            )
        ]

        paths: List[List[str]] = []

        def walk(path: List[str]) -> None:
            current = path[-1]

            critical_successors = [
                successor
                for successor in self.successors[current]
                if successor in critical_ids
                and abs(
                    self.schedule[successor].earliest_start
                    - self.schedule[current].earliest_finish
                )
                <= EPSILON
            ]

            if not critical_successors:
                paths.append(path.copy())
                return

            for successor in critical_successors:
                walk(path + [successor])

        for start in starts:
            walk([start])

        return paths

    def delay_activity(self, activity_id: str, delay: float) -> float:
        """
        Estimate the new project duration after delaying one activity.

        This intentionally recalculates the network instead of simply adding
        the delay to project duration. An activity with available float may
        absorb some delay without changing the project completion date.
        """
        if activity_id not in self.activities:
            raise KeyError(f"Unknown activity: {activity_id}")

        if delay < 0:
            raise ValueError("Delay must be non-negative.")

        modified: List[Activity] = []

        for activity in self.activities.values():
            if activity.id == activity_id:
                modified.append(
                    Activity(
                        id=activity.id,
                        name=activity.name,
                        duration=activity.duration + delay,
                        predecessors=activity.predecessors,
                    )
                )
            else:
                modified.append(activity)

        simulation = CPMProject(modified)
        simulation.calculate()
        return simulation.project_duration

    def report(self) -> None:
        """Print a compact but detailed CPM schedule."""
        if not self.schedule:
            self.calculate()

        print("\nCRITICAL PATH METHOD SCHEDULE")
        print("=" * 100)
        print(
            f"{'ID':<8}"
            f"{'Activity':<34}"
            f"{'Dur.':>8}"
            f"{'ES':>8}"
            f"{'EF':>8}"
            f"{'LS':>8}"
            f"{'LF':>8}"
            f"{'Float':>10}"
            f"{'Status':>10}"
        )
        print("-" * 100)

        for activity_id in self.order:
            entry = self.schedule[activity_id]
            status = "CRITICAL" if entry.is_critical else "NON-CRITICAL"

            print(
                f"{activity_id:<8}"
                f"{entry.activity.name[:33]:<34}"
                f"{entry.activity.duration:>8.1f}"
                f"{entry.earliest_start:>8.1f}"
                f"{entry.earliest_finish:>8.1f}"
                f"{entry.latest_start:>8.1f}"
                f"{entry.latest_finish:>8.1f}"
                f"{entry.total_float:>10.1f}"
                f"{status:>10}"
            )

        print("-" * 100)
        print(f"Project duration: {self.project_duration:.1f} time units")

        print("\nCritical activities:")
        for entry in self.critical_activities():
            print(
                f"  {entry.activity.id}: {entry.activity.name} "
                f"(duration={entry.activity.duration:g})"
            )

        print("\nCritical path(s):")
        for path in self.critical_paths():
            names = " -> ".join(
                f"{activity_id} ({self.activities[activity_id].name})"
                for activity_id in path
            )
            print(f"  {names}")


def build_realistic_project() -> CPMProject:
    """
    Create a software-release project.

    The dependencies represent actual sequencing constraints:
    requirements must be approved before architecture, implementation
    follows architecture, integration follows implementation, and release
    depends on testing and operational readiness.
    """
    activities = [
        Activity(
            "A",
            "Requirements approval",
            3,
        ),
        Activity(
            "B",
            "Architecture design",
            4,
            ("A",),
        ),
        Activity(
            "C",
            "Database implementation",
            5,
            ("B",),
        ),
        Activity(
            "D",
            "Backend implementation",
            7,
            ("B",),
        ),
        Activity(
            "E",
            "Frontend implementation",
            6,
            ("B",),
        ),
        Activity(
            "F",
            "Integration",
            3,
            ("C", "D", "E"),
        ),
        Activity(
            "G",
            "System testing",
            5,
            ("F",),
        ),
        Activity(
            "H",
            "Security validation",
            3,
            ("F",),
        ),
        Activity(
            "I",
            "Operations readiness",
            2,
            ("B",),
        ),
        Activity(
            "J",
            "Production release",
            2,
            ("G", "H", "I"),
        ),
    ]

    return CPMProject(activities)


def demonstrate_fundamentals() -> None:
    """
    Show the meaning of ES, EF, LS, LF, and float with a small network.
    """
    print("CRITICAL PATH METHOD: FUNDAMENTAL CALCULATION")
    print("=" * 70)

    project = CPMProject(
        [
            Activity("A", "Project initiation", 2),
            Activity("B", "Planning", 3, ("A",)),
            Activity("C", "Implementation", 5, ("B",)),
            Activity("D", "Validation", 2, ("C",)),
        ]
    )

    project.calculate()

    for activity_id in project.order:
        entry = project.schedule[activity_id]
        print(
            f"{activity_id}: "
            f"ES={entry.earliest_start:g}, "
            f"EF={entry.earliest_finish:g}, "
            f"LS={entry.latest_start:g}, "
            f"LF={entry.latest_finish:g}, "
            f"Float={entry.total_float:g}"
        )


def demonstrate_float() -> None:
    """
    Demonstrate why a non-critical activity can be delayed without
    immediately delaying the whole project.
    """
    print("\nFLOAT DEMONSTRATION")
    print("=" * 70)

    project = CPMProject(
        [
            Activity("A", "Start", 2),
            Activity("B", "Critical work", 6, ("A",)),
            Activity("C", "Parallel work", 2, ("A",)),
            Activity("D", "Finish", 2, ("B", "C")),
        ]
    )
    project.calculate()

    project.report()

    c = project.schedule["C"]
    print(
        f"\nActivity C has {c.total_float:g} time units of total float. "
        "A delay within that amount does not extend the project."
    )

    original_duration = project.project_duration
    after_small_delay = project.delay_activity("C", c.total_float)
    after_large_delay = project.delay_activity("C", c.total_float + 2)

    print(f"Original duration: {original_duration:g}")
    print(
        f"Duration after using all C float: {after_small_delay:g}"
    )
    print(
        f"Duration after exceeding C float: {after_large_delay:g}"
    )


def demonstrate_delay_sensitivity(project: CPMProject) -> None:
    """
    Compare the impact of delaying every activity.

    This is useful because criticality is not merely a label. A zero-float
    activity has direct schedule sensitivity under the current network.
    """
    print("\nDELAY SENSITIVITY ANALYSIS")
    print("=" * 70)

    baseline = project.project_duration
    print(f"Baseline project duration: {baseline:g}")

    for activity_id in project.order:
        new_duration = project.delay_activity(activity_id, 1)
        impact = new_duration - baseline

        status = (
            "project duration increases"
            if impact > EPSILON
            else "project duration unchanged"
        )

        print(
            f"{activity_id} | "
            f"{project.activities[activity_id].name:<28} | "
            f"+1 duration -> project={new_duration:g} | "
            f"{status}"
        )


def demonstrate_validation() -> None:
    """Demonstrate failures that should be caught before CPM calculation."""
    print("\nNETWORK VALIDATION")
    print("=" * 70)

    try:
        CPMProject(
            [
                Activity("A", "Requirements", 2),
                Activity("B", "Implementation", 3, ("UNKNOWN",)),
            ]
        )
    except ValueError as exc:
        print(f"Unknown dependency rejected: {exc}")

    try:
        CPMProject(
            [
                Activity("A", "First activity", 2, ("B",)),
                Activity("B", "Second activity", 3, ("A",)),
            ]
        )
    except ValueError as exc:
        print(f"Circular dependency rejected: {exc}")

    try:
        Activity("A", "Invalid duration", -1)
    except ValueError as exc:
        print(f"Negative duration rejected: {exc}")


def demonstrate_multiple_critical_paths() -> None:
    """
    Show that a project can have more than one critical path.

    When two parallel branches have equal controlling durations, both can
    have zero float and both become critical.
    """
    print("\nMULTIPLE CRITICAL PATHS")
    print("=" * 70)

    project = CPMProject(
        [
            Activity("START", "Project start", 1),
            Activity("A", "Engineering branch", 5, ("START",)),
            Activity("B", "Operations branch", 5, ("START",)),
            Activity("END", "Project completion", 1, ("A", "B")),
        ]
    )

    project.calculate()
    project.report()


def demonstrate_realistic_project() -> CPMProject:
    """Run the main project case study."""
    print("\nREALISTIC SOFTWARE RELEASE CASE STUDY")
    print("=" * 70)

    project = build_realistic_project()
    project.calculate()
    project.report()

    return project


def main() -> None:
    demonstrate_fundamentals()
    demonstrate_float()

    project = demonstrate_realistic_project()

    demonstrate_delay_sensitivity(project)
    demonstrate_multiple_critical_paths()
    demonstrate_validation()

    print("\nKEY INTERPRETATION")
    print("=" * 70)
    print(
        "Critical activities are the activities with zero total float in "
        "the calculated schedule. They form one or more paths that control "
        "the current project completion date."
    )
    print(
        "A non-critical activity is not automatically unimportant. Its "
        "float represents schedule flexibility under the current network, "
        "and consuming that flexibility can make the activity critical."
    )
    print(
        "The critical path is a property of the dependency network and "
        "durations. If durations, dependencies, constraints, or actual "
        "progress change, the critical path must be recalculated."
    )


if __name__ == "__main__":
    main()
