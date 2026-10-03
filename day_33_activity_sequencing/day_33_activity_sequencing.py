"""
Activity Sequencing: Determining Activity Order

A self-contained learning and simulation program for activity sequencing in
project scheduling. It models activities, precedence relationships, validates
the dependency graph, performs topological sequencing, calculates CPM
forward/backward passes, identifies the critical path, detects parallel work,
and demonstrates how changes in dependencies affect the resulting schedule.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass
class Activity:
    activity_id: str
    name: str
    duration: float
    predecessors: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.activity_id.strip():
            raise ValueError("Activity ID cannot be empty.")
        if not self.name.strip():
            raise ValueError(f"Activity {self.activity_id}: name cannot be empty.")
        if self.duration < 0:
            raise ValueError(
                f"Activity {self.activity_id}: duration cannot be negative."
            )


class ActivityNetwork:
    """
    Represents an activity-on-node dependency network.

    An edge A -> B means B cannot start until A has finished.
    """

    def __init__(self) -> None:
        self.activities: Dict[str, Activity] = {}

    def add_activity(
        self,
        activity_id: str,
        name: str,
        duration: float,
        predecessors: Iterable[str] = (),
    ) -> None:
        if activity_id in self.activities:
            raise ValueError(f"Activity {activity_id!r} already exists.")

        predecessor_set = set(predecessors)

        if activity_id in predecessor_set:
            raise ValueError(
                f"Activity {activity_id!r} cannot depend directly on itself."
            )

        self.activities[activity_id] = Activity(
            activity_id=activity_id,
            name=name,
            duration=duration,
            predecessors=predecessor_set,
        )

    def validate(self) -> None:
        """
        Validate that every predecessor exists and that the dependency graph
        contains no cycle.
        """
        missing: Dict[str, Set[str]] = {}

        for activity in self.activities.values():
            unknown = {
                predecessor
                for predecessor in activity.predecessors
                if predecessor not in self.activities
            }
            if unknown:
                missing[activity.activity_id] = unknown

        if missing:
            details = "; ".join(
                f"{activity}: {sorted(predecessors)}"
                for activity, predecessors in missing.items()
            )
            raise ValueError(f"Unknown predecessor(s): {details}")

        self.topological_order()

    def build_successors(self) -> Dict[str, Set[str]]:
        successors = {activity_id: set() for activity_id in self.activities}

        for activity in self.activities.values():
            for predecessor in activity.predecessors:
                successors[predecessor].add(activity.activity_id)

        return successors

    def topological_order(self) -> List[str]:
        """
        Kahn's algorithm produces an order in which every predecessor appears
        before its dependent activity.

        A cycle prevents all activities from being emitted.
        """
        indegree = {
            activity_id: len(activity.predecessors)
            for activity_id, activity in self.activities.items()
        }
        successors = self.build_successors()

        ready = deque(
            sorted(
                activity_id
                for activity_id, degree in indegree.items()
                if degree == 0
            )
        )

        order: List[str] = []

        while ready:
            current = ready.popleft()
            order.append(current)

            for successor in sorted(successors[current]):
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    ready.append(successor)

        if len(order) != len(self.activities):
            remaining = sorted(
                activity_id
                for activity_id, degree in indegree.items()
                if degree > 0
            )
            raise ValueError(
                "Circular dependency detected. Activities that could not be "
                f"sequenced: {remaining}"
            )

        return order

    def activity_levels(self) -> Dict[int, List[str]]:
        """
        Group activities into dependency levels.

        Activities in the same level have no dependency on another activity
        in that same level and can potentially execute in parallel.
        """
        self.validate()

        order = self.topological_order()
        level: Dict[str, int] = {}

        for activity_id in order:
            predecessors = self.activities[activity_id].predecessors
            if not predecessors:
                level[activity_id] = 0
            else:
                level[activity_id] = (
                    max(level[predecessor] for predecessor in predecessors) + 1
                )

        grouped: Dict[int, List[str]] = defaultdict(list)
        for activity_id in order:
            grouped[level[activity_id]].append(activity_id)

        return dict(sorted(grouped.items()))

    def critical_path_analysis(self) -> Dict[str, Dict[str, float]]:
        """
        Perform CPM forward and backward passes.

        ES = earliest start
        EF = earliest finish
        LS = latest start without delaying project completion
        LF = latest finish without delaying project completion
        Float = LS - ES

        Activities with zero float form the critical-path set. In a network
        containing branching and merging, more than one critical path can
        exist.
        """
        self.validate()

        order = self.topological_order()
        successors = self.build_successors()

        es: Dict[str, float] = {}
        ef: Dict[str, float] = {}

        for activity_id in order:
            activity = self.activities[activity_id]

            if activity.predecessors:
                es[activity_id] = max(
                    ef[predecessor] for predecessor in activity.predecessors
                )
            else:
                es[activity_id] = 0.0

            ef[activity_id] = es[activity_id] + activity.duration

        project_duration = max(ef.values(), default=0.0)

        lf: Dict[str, float] = {}
        ls: Dict[str, float] = {}

        for activity_id in reversed(order):
            activity = self.activities[activity_id]

            if successors[activity_id]:
                lf[activity_id] = min(
                    ls[successor] for successor in successors[activity_id]
                )
            else:
                lf[activity_id] = project_duration

            ls[activity_id] = lf[activity_id] - activity.duration

        result: Dict[str, Dict[str, float]] = {}

        for activity_id in order:
            total_float = ls[activity_id] - es[activity_id]
            if abs(total_float) < 1e-9:
                total_float = 0.0

            result[activity_id] = {
                "ES": es[activity_id],
                "EF": ef[activity_id],
                "LS": ls[activity_id],
                "LF": lf[activity_id],
                "Float": total_float,
            }

        return result

    def critical_paths(self) -> List[List[str]]:
        """
        Enumerate zero-float paths from a source to a terminal activity.

        The method is intended for realistic instructional networks where the
        number of critical paths is manageable.
        """
        analysis = self.critical_path_analysis()
        successors = self.build_successors()

        critical = {
            activity_id
            for activity_id, values in analysis.items()
            if values["Float"] == 0.0
        }

        sources = sorted(
            activity_id
            for activity_id in critical
            if not (
                self.activities[activity_id].predecessors & critical
            )
        )

        terminals = {
            activity_id
            for activity_id in critical
            if not (successors[activity_id] & critical)
        }

        paths: List[List[str]] = []

        def walk(current: str, path: List[str]) -> None:
            if current in terminals:
                paths.append(path.copy())
                return

            for successor in sorted(successors[current]):
                if successor in critical:
                    walk(successor, path + [successor])

        for source in sources:
            walk(source, [source])

        return paths

    def possible_parallel_groups(self) -> List[List[str]]:
        """
        Identify activities that become ready at the same scheduling frontier.

        This is not a proof that activities can safely consume the same human
        or machine resource. It only reflects dependency-based parallelism.
        Resource constraints must be evaluated separately.
        """
        return [
            activities
            for activities in self.activity_levels().values()
            if len(activities) > 1
        ]

    def dependency_table(self) -> List[Tuple[str, str, str]]:
        rows = []

        for activity_id in self.topological_order():
            activity = self.activities[activity_id]
            predecessors = ", ".join(sorted(activity.predecessors)) or "None"
            rows.append((activity_id, activity.name, predecessors))

        return rows


def print_network(network: ActivityNetwork) -> None:
    print("\nActivity Dependency Network")
    print("-" * 72)

    for activity_id, name, predecessors in network.dependency_table():
        print(
            f"{activity_id:<5} | {name:<28} | "
            f"Predecessors: {predecessors}"
        )


def print_sequence(network: ActivityNetwork) -> None:
    order = network.topological_order()

    print("\nDependency-Valid Activity Sequence")
    print("-" * 72)
    print(" -> ".join(order))

    levels = network.activity_levels()
    print("\nDependency Levels")
    for level, activities in levels.items():
        print(f"Level {level}: {', '.join(activities)}")


def print_cpm(network: ActivityNetwork) -> None:
    analysis = network.critical_path_analysis()
    paths = network.critical_paths()

    print("\nCritical Path Method Analysis")
    print("-" * 72)
    print(
        f"{'ID':<5} {'ES':>6} {'EF':>6} "
        f"{'LS':>6} {'LF':>6} {'Float':>8}"
    )

    for activity_id in network.topological_order():
        values = analysis[activity_id]
        print(
            f"{activity_id:<5} "
            f"{values['ES']:>6.1f} "
            f"{values['EF']:>6.1f} "
            f"{values['LS']:>6.1f} "
            f"{values['LF']:>6.1f} "
            f"{values['Float']:>8.1f}"
        )

    project_duration = max(
        values["EF"] for values in analysis.values()
    )

    print(f"\nProject duration: {project_duration:.1f} working days")

    print("Critical path(s):")
    for path in paths:
        print(" -> ".join(path))

    parallel_groups = network.possible_parallel_groups()

    if parallel_groups:
        print("\nDependency-based parallel work:")
        for group in parallel_groups:
            print(f"  {', '.join(group)}")


def demonstrate_basic_sequencing() -> ActivityNetwork:
    """
    A product-release example demonstrates that activity order is determined
    by logical dependencies rather than by arbitrary activity IDs.
    """
    network = ActivityNetwork()

    network.add_activity(
        "A",
        "Confirm release scope",
        2,
    )
    network.add_activity(
        "B",
        "Design database changes",
        3,
        predecessors=["A"],
    )
    network.add_activity(
        "C",
        "Design API contract",
        2,
        predecessors=["A"],
    )
    network.add_activity(
        "D",
        "Implement database migration",
        4,
        predecessors=["B"],
    )
    network.add_activity(
        "E",
        "Implement API changes",
        5,
        predecessors=["C"],
    )
    network.add_activity(
        "F",
        "Integrate application",
        2,
        predecessors=["D", "E"],
    )
    network.add_activity(
        "G",
        "Run integration testing",
        3,
        predecessors=["F"],
    )
    network.add_activity(
        "H",
        "Deploy release",
        1,
        predecessors=["G"],
    )

    return network


def demonstrate_validation_failures() -> None:
    print("\nValidation and Failure Conditions")
    print("-" * 72)

    missing_dependency = ActivityNetwork()
    missing_dependency.add_activity(
        "A",
        "Prepare specification",
        2,
        predecessors=["UNKNOWN"],
    )

    try:
        missing_dependency.validate()
    except ValueError as exc:
        print(f"Missing predecessor detected: {exc}")

    circular_network = ActivityNetwork()
    circular_network.add_activity(
        "A",
        "Activity A",
        1,
        predecessors=["C"],
    )
    circular_network.add_activity(
        "B",
        "Activity B",
        1,
        predecessors=["A"],
    )
    circular_network.add_activity(
        "C",
        "Activity C",
        1,
        predecessors=["B"],
    )

    try:
        circular_network.validate()
    except ValueError as exc:
        print(f"Circular dependency detected: {exc}")

    try:
        ActivityNetwork().add_activity(
            "NEG",
            "Invalid negative duration",
            -1,
        )
    except ValueError as exc:
        print(f"Invalid duration detected: {exc}")


def demonstrate_dependency_change() -> None:
    """
    Changing a predecessor relationship changes the feasible sequence.

    This illustrates why sequencing decisions should be captured explicitly:
    a newly discovered dependency can turn previously parallel work into
    serial work and increase the critical path.
    """
    original = ActivityNetwork()
    original.add_activity("A", "Requirements", 2)
    original.add_activity("B", "UI design", 4, ["A"])
    original.add_activity("C", "Backend design", 4, ["A"])
    original.add_activity("D", "Frontend implementation", 5, ["B"])
    original.add_activity("E", "Backend implementation", 6, ["C"])
    original.add_activity("F", "System integration", 3, ["D", "E"])

    changed = ActivityNetwork()
    changed.add_activity("A", "Requirements", 2)
    changed.add_activity("B", "UI design", 4, ["A"])
    changed.add_activity("C", "Backend design", 4, ["A", "B"])
    changed.add_activity("D", "Frontend implementation", 5, ["B"])
    changed.add_activity("E", "Backend implementation", 6, ["C"])
    changed.add_activity("F", "System integration", 3, ["D", "E"])

    print("\nImpact of a New Dependency")
    print("-" * 72)

    original_analysis = original.critical_path_analysis()
    changed_analysis = changed.critical_path_analysis()

    original_duration = max(
        values["EF"] for values in original_analysis.values()
    )
    changed_duration = max(
        values["EF"] for values in changed_analysis.values()
    )

    print(
        f"Original project duration: {original_duration:.1f} days"
    )
    print(
        f"After B -> C dependency: {changed_duration:.1f} days"
    )
    print(
        "Original sequence: "
        + " -> ".join(original.topological_order())
    )
    print(
        "Changed sequence: "
        + " -> ".join(changed.topological_order())
    )


def demonstrate_resource_warning() -> None:
    """
    Logical sequencing alone does not solve resource-constrained scheduling.

    B and C are dependency-independent after A, but both require the same
    specialist in this scenario. A dependency engine can expose the
    parallelism; a resource scheduler must decide whether to serialize it.
    """
    network = ActivityNetwork()
    network.add_activity("A", "Approve requirements", 2)
    network.add_activity("B", "Security architecture review", 3, ["A"])
    network.add_activity("C", "Data architecture review", 3, ["A"])
    network.add_activity("D", "Architecture sign-off", 1, ["B", "C"])

    print("\nDependency Parallelism Versus Resource Availability")
    print("-" * 72)

    for group in network.possible_parallel_groups():
        print(
            f"These activities are dependency-independent: {', '.join(group)}"
        )
        print(
            "They may still need serialization if they require the same "
            "unavailable resource."
        )


def main() -> None:
    print("=" * 72)
    print("ACTIVITY SEQUENCING: DETERMINING ACTIVITY ORDER")
    print("=" * 72)

    network = demonstrate_basic_sequencing()

    network.validate()
    print_network(network)
    print_sequence(network)
    print_cpm(network)

    demonstrate_validation_failures()
    demonstrate_dependency_change()
    demonstrate_resource_warning()

    print("\nPractical interpretation")
    print("-" * 72)
    print(
        "The dependency graph establishes which activities must precede "
        "others. Topological sorting produces a dependency-valid order, "
        "while CPM shows which ordering constraints influence the project "
        "completion date. Parallel dependency paths can reduce elapsed time, "
        "but resource constraints may require additional scheduling rules."
    )


if __name__ == "__main__":
    main()
