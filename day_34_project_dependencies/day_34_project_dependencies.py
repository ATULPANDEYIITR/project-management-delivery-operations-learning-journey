"""
Project Dependencies: Understanding Task Dependencies

A self-contained executable learning model for task dependency graphs.

The program progresses from:
- representing tasks and dependency relationships,
- validating dependency references,
- detecting circular dependencies,
- producing a valid execution order,
- identifying parallel execution opportunities,
- calculating critical-path timing,
- simulating failures and blocked tasks,
- updating task state,
- exporting a dependency-aware project plan.

The central model is a directed graph:
    prerequisite -> dependent task

For example:
    Database schema -> Backend API -> Integration tests -> Release

A task cannot start until all of its prerequisites satisfy the
required completion condition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import csv
import json
from typing import Iterable


class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class Task:
    task_id: str
    name: str
    duration: int
    dependencies: set[str] = field(default_factory=set)
    status: TaskStatus = TaskStatus.NOT_STARTED
    owner: str = "unassigned"
    priority: str = "normal"

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("Task ID cannot be empty.")
        if not self.name.strip():
            raise ValueError("Task name cannot be empty.")
        if self.duration <= 0:
            raise ValueError("Task duration must be greater than zero.")
        if self.priority not in {"low", "normal", "high", "critical"}:
            raise ValueError(f"Unsupported priority: {self.priority}")


class DependencyError(Exception):
    """Raised when the dependency graph violates project rules."""


class ProjectDependencyGraph:
    """
    Directed acyclic graph used to model project task dependencies.

    Edge direction:
        prerequisite -> dependent

    This direction makes graph traversal intuitive:
    when a prerequisite finishes, its outgoing neighbors become
    candidates for execution.
    """

    def __init__(self, project_name: str) -> None:
        self.project_name = project_name
        self.tasks: dict[str, Task] = {}

    def add_task(
        self,
        task_id: str,
        name: str,
        duration: int,
        dependencies: Iterable[str] = (),
        owner: str = "unassigned",
        priority: str = "normal",
    ) -> None:
        if task_id in self.tasks:
            raise DependencyError(f"Task {task_id!r} already exists.")

        dependency_set = set(dependencies)

        if task_id in dependency_set:
            raise DependencyError(
                f"Task {task_id!r} cannot depend on itself."
            )

        task = Task(
            task_id=task_id,
            name=name,
            duration=duration,
            dependencies=dependency_set,
            owner=owner,
            priority=priority,
        )

        self.tasks[task_id] = task

        try:
            self.validate()
        except Exception:
            del self.tasks[task_id]
            raise

    def remove_task(self, task_id: str) -> None:
        if task_id not in self.tasks:
            raise DependencyError(f"Unknown task: {task_id}")

        for task in self.tasks.values():
            task.dependencies.discard(task_id)

        del self.tasks[task_id]

    def validate_references(self) -> None:
        """Ensure every dependency points to an existing task."""
        missing: list[tuple[str, str]] = []

        for task in self.tasks.values():
            for dependency in task.dependencies:
                if dependency not in self.tasks:
                    missing.append((task.task_id, dependency))

        if missing:
            details = ", ".join(
                f"{task} -> missing {dependency}"
                for task, dependency in missing
            )
            raise DependencyError(f"Invalid dependency references: {details}")

    def adjacency(self) -> dict[str, set[str]]:
        """
        Build prerequisite -> dependent adjacency lists.

        Dependencies stored on each task are naturally expressed as:
            task -> prerequisites

        Execution algorithms also need the reverse direction, so this
        method constructs the graph used for traversal.
        """
        self.validate_references()

        graph = {task_id: set() for task_id in self.tasks}

        for task in self.tasks.values():
            for dependency in task.dependencies:
                graph[dependency].add(task.task_id)

        return graph

    def indegrees(self) -> dict[str, int]:
        """
        Calculate the number of unfinished prerequisite relationships
        represented by each node in the dependency graph.
        """
        self.validate_references()

        return {
            task_id: len(task.dependencies)
            for task_id, task in self.tasks.items()
        }

    def detect_cycles(self) -> list[list[str]]:
        """
        Detect directed cycles using depth-first traversal.

        A dependency cycle such as:
            API -> Database -> Migration -> API

        means no task can satisfy all prerequisites, so the project
        cannot have a valid complete execution order.
        """
        self.validate_references()

        graph = {
            task_id: set(task.dependencies)
            for task_id, task in self.tasks.items()
        }

        visiting: set[str] = set()
        visited: set[str] = set()
        cycles: list[list[str]] = []

        def dfs(node: str, path: list[str]) -> None:
            visiting.add(node)
            path.append(node)

            for prerequisite in graph[node]:
                if prerequisite in visiting:
                    cycle_start = path.index(prerequisite)
                    cycles.append(path[cycle_start:] + [prerequisite])
                elif prerequisite not in visited:
                    dfs(prerequisite, path)

            path.pop()
            visiting.remove(node)
            visited.add(node)

        for task_id in graph:
            if task_id not in visited:
                dfs(task_id, [])

        return cycles

    def validate(self) -> None:
        self.validate_references()

        cycles = self.detect_cycles()
        if cycles:
            formatted = "; ".join(" -> ".join(cycle) for cycle in cycles)
            raise DependencyError(
                f"Circular dependency detected: {formatted}"
            )

    def topological_order(self) -> list[str]:
        """
        Produce an execution order using Kahn's topological-sort algorithm.

        Tasks with zero prerequisites are initially executable.
        Completing/removing each such task decreases the dependency count
        of its dependents.
        """
        self.validate()

        remaining_dependencies = self.indegrees()
        ready = deque(
            sorted(
                task_id
                for task_id, count in remaining_dependencies.items()
                if count == 0
            )
        )

        graph = self.adjacency()
        order: list[str] = []

        while ready:
            current = ready.popleft()
            order.append(current)

            for dependent in sorted(graph[current]):
                remaining_dependencies[dependent] -= 1
                if remaining_dependencies[dependent] == 0:
                    ready.append(dependent)

        if len(order) != len(self.tasks):
            raise DependencyError(
                "No complete execution order exists because the graph "
                "contains a cycle."
            )

        return order

    def predecessors(self, task_id: str) -> set[str]:
        if task_id not in self.tasks:
            raise DependencyError(f"Unknown task: {task_id}")
        return set(self.tasks[task_id].dependencies)

    def successors(self, task_id: str) -> set[str]:
        if task_id not in self.tasks:
            raise DependencyError(f"Unknown task: {task_id}")
        return self.adjacency()[task_id]

    def ready_tasks(self) -> list[Task]:
        """
        A task is ready only when every prerequisite is completed.

        Failed or blocked prerequisites intentionally prevent readiness.
        """
        ready: list[Task] = []

        for task in self.tasks.values():
            if task.status != TaskStatus.NOT_STARTED:
                continue

            if all(
                self.tasks[dependency].status == TaskStatus.COMPLETED
                for dependency in task.dependencies
            ):
                ready.append(task)

        return sorted(
            ready,
            key=lambda task: (
                -self.priority_value(task.priority),
                task.task_id,
            ),
        )

    @staticmethod
    def priority_value(priority: str) -> int:
        return {
            "critical": 4,
            "high": 3,
            "normal": 2,
            "low": 1,
        }[priority]

    def mark_started(self, task_id: str) -> None:
        task = self.tasks.get(task_id)
        if task is None:
            raise DependencyError(f"Unknown task: {task_id}")

        if task.status != TaskStatus.NOT_STARTED:
            raise DependencyError(
                f"Task {task_id} cannot start from {task.status.value}."
            )

        blocked_by = [
            dependency
            for dependency in task.dependencies
            if self.tasks[dependency].status != TaskStatus.COMPLETED
        ]

        if blocked_by:
            raise DependencyError(
                f"Task {task_id} is blocked by: {', '.join(sorted(blocked_by))}"
            )

        task.status = TaskStatus.IN_PROGRESS

    def mark_completed(self, task_id: str) -> None:
        task = self.tasks.get(task_id)
        if task is None:
            raise DependencyError(f"Unknown task: {task_id}")

        if task.status != TaskStatus.IN_PROGRESS:
            raise DependencyError(
                f"Task {task_id} must be in progress before completion."
            )

        task.status = TaskStatus.COMPLETED

    def mark_failed(self, task_id: str) -> None:
        task = self.tasks.get(task_id)
        if task is None:
            raise DependencyError(f"Unknown task: {task_id}")

        if task.status not in {
            TaskStatus.IN_PROGRESS,
            TaskStatus.READY,
        }:
            raise DependencyError(
                f"Task {task_id} cannot fail from {task.status.value}."
            )

        task.status = TaskStatus.FAILED
        self.propagate_blocked_status()

    def propagate_blocked_status(self) -> None:
        """
        A task becomes blocked if any prerequisite is failed or blocked.

        This is different from a task merely being not ready: a task with
        incomplete prerequisites may eventually become executable, whereas
        a task with an irrecoverably failed prerequisite requires intervention.
        """
        changed = True

        while changed:
            changed = False

            for task in self.tasks.values():
                if task.status in {
                    TaskStatus.COMPLETED,
                    TaskStatus.IN_PROGRESS,
                    TaskStatus.FAILED,
                    TaskStatus.BLOCKED,
                }:
                    continue

                if any(
                    self.tasks[dependency].status
                    in {TaskStatus.FAILED, TaskStatus.BLOCKED}
                    for dependency in task.dependencies
                ):
                    task.status = TaskStatus.BLOCKED
                    changed = True

    def execution_waves(self) -> list[list[str]]:
        """
        Group tasks into dependency levels.

        Tasks within a wave have no dependency relationship requiring one
        to wait for another inside that wave. They can therefore be candidates
        for parallel execution if sufficient resources are available.
        """
        self.validate()

        remaining = self.indegrees()
        graph = self.adjacency()

        current = sorted(
            task_id
            for task_id, count in remaining.items()
            if count == 0
        )

        waves: list[list[str]] = []

        while current:
            waves.append(current)
            next_wave: list[str] = []

            for task_id in current:
                for dependent in graph[task_id]:
                    remaining[dependent] -= 1
                    if remaining[dependent] == 0:
                        next_wave.append(dependent)

            current = sorted(next_wave)

        if sum(len(wave) for wave in waves) != len(self.tasks):
            raise DependencyError("Cannot calculate waves for a cyclic graph.")

        return waves

    def critical_path(self) -> dict[str, object]:
        """
        Calculate earliest start/finish values and identify the critical path.

        Duration is treated as elapsed project time units. The longest
        prerequisite chain determines the minimum project completion time
        when unlimited execution capacity is assumed.
        """
        order = self.topological_order()

        earliest_start = {task_id: 0 for task_id in order}
        earliest_finish: dict[str, int] = {}

        for task_id in order:
            task = self.tasks[task_id]

            if task.dependencies:
                earliest_start[task_id] = max(
                    earliest_finish[dependency]
                    for dependency in task.dependencies
                )

            earliest_finish[task_id] = (
                earliest_start[task_id] + task.duration
            )

        project_duration = max(earliest_finish.values(), default=0)

        latest_finish = {
            task_id: project_duration
            for task_id in order
        }
        latest_start: dict[str, int] = {}

        graph = self.adjacency()

        for task_id in reversed(order):
            successors = graph[task_id]

            if successors:
                latest_finish[task_id] = min(
                    latest_start[successor]
                    for successor in successors
                )

            latest_start[task_id] = (
                latest_finish[task_id] - self.tasks[task_id].duration
            )

        slack = {
            task_id: latest_start[task_id] - earliest_start[task_id]
            for task_id in order
        }

        critical = [
            task_id
            for task_id in order
            if slack[task_id] == 0
        ]

        return {
            "earliest_start": earliest_start,
            "earliest_finish": earliest_finish,
            "latest_start": latest_start,
            "latest_finish": latest_finish,
            "slack": slack,
            "critical_tasks": critical,
            "project_duration": project_duration,
        }

    def export_json(self, path: str | Path) -> None:
        """Persist the dependency graph in a readable JSON representation."""
        payload = {
            "project": self.project_name,
            "tasks": [
                {
                    "id": task.task_id,
                    "name": task.name,
                    "duration": task.duration,
                    "dependencies": sorted(task.dependencies),
                    "status": task.status.value,
                    "owner": task.owner,
                    "priority": task.priority,
                }
                for task in self.tasks.values()
            ],
        }

        Path(path).write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def export_csv(self, path: str | Path) -> None:
        """Export tasks as rows suitable for spreadsheet-based planning."""
        with Path(path).open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "id",
                    "name",
                    "duration",
                    "dependencies",
                    "status",
                    "owner",
                    "priority",
                ],
            )
            writer.writeheader()

            for task in self.tasks.values():
                writer.writerow(
                    {
                        "id": task.task_id,
                        "name": task.name,
                        "duration": task.duration,
                        "dependencies": ",".join(sorted(task.dependencies)),
                        "status": task.status.value,
                        "owner": task.owner,
                        "priority": task.priority,
                    }
                )

    def print_dependency_map(self) -> None:
        print(f"\nDependency map: {self.project_name}")
        print("-" * 72)

        for task_id in self.topological_order():
            task = self.tasks[task_id]
            dependencies = ", ".join(sorted(task.dependencies)) or "none"

            print(
                f"{task_id:12} | "
                f"{task.name:32} | "
                f"depends on: {dependencies}"
            )

    def print_status(self) -> None:
        print("\nCurrent task status")
        print("-" * 72)

        for task in sorted(self.tasks.values(), key=lambda item: item.task_id):
            print(
                f"{task.task_id:12} | "
                f"{task.status.value:12} | "
                f"{task.owner:12} | "
                f"{task.name}"
            )


def build_realistic_project() -> ProjectDependencyGraph:
    """
    Construct a software-release project.

    The dependencies intentionally represent actual delivery relationships:
    infrastructure must exist before deployment configuration can be validated,
    the schema must exist before backend persistence can be integrated, and
    API and UI work converge before end-to-end testing.
    """
    project = ProjectDependencyGraph("Customer Portal Release")

    project.add_task(
        "DISCOVERY",
        "Finalize product and acceptance requirements",
        2,
        owner="product",
        priority="critical",
    )

    project.add_task(
        "ARCH",
        "Approve service architecture and API boundaries",
        2,
        dependencies={"DISCOVERY"},
        owner="architecture",
        priority="critical",
    )

    project.add_task(
        "SCHEMA",
        "Create and validate production database schema",
        3,
        dependencies={"ARCH"},
        owner="backend",
        priority="high",
    )

    project.add_task(
        "INFRA",
        "Provision application infrastructure",
        3,
        dependencies={"ARCH"},
        owner="platform",
        priority="high",
    )

    project.add_task(
        "API",
        "Implement backend API and persistence layer",
        5,
        dependencies={"SCHEMA", "ARCH"},
        owner="backend",
        priority="critical",
    )

    project.add_task(
        "UI",
        "Implement customer portal interface",
        4,
        dependencies={"DISCOVERY"},
        owner="frontend",
        priority="high",
    )

    project.add_task(
        "OBS",
        "Configure logs, metrics, and deployment monitoring",
        2,
        dependencies={"INFRA"},
        owner="platform",
        priority="normal",
    )

    project.add_task(
        "INTEGRATION",
        "Connect UI with the production-shaped API",
        3,
        dependencies={"API", "UI"},
        owner="fullstack",
        priority="critical",
    )

    project.add_task(
        "SECURITY",
        "Perform authentication and authorization verification",
        3,
        dependencies={"API", "INFRA"},
        owner="security",
        priority="critical",
    )

    project.add_task(
        "E2E",
        "Run end-to-end acceptance tests",
        3,
        dependencies={"INTEGRATION", "SECURITY", "OBS"},
        owner="qa",
        priority="critical",
    )

    project.add_task(
        "RELEASE",
        "Deploy approved release to production",
        1,
        dependencies={"E2E"},
        owner="release",
        priority="critical",
    )

    return project


def demonstrate_basic_graph() -> None:
    print("\n=== Dependency Graph Fundamentals ===")

    project = build_realistic_project()
    project.print_dependency_map()

    print("\nValid execution order:")
    print(" -> ".join(project.topological_order()))

    print("\nDependency waves:")
    for index, wave in enumerate(project.execution_waves(), start=1):
        print(f"Wave {index}: {', '.join(wave)}")

    ready = project.ready_tasks()
    print("\nInitially executable tasks:")
    for task in ready:
        print(f"- {task.task_id}: {task.name}")


def demonstrate_critical_path() -> None:
    print("\n=== Critical Path Analysis ===")

    project = build_realistic_project()
    analysis = project.critical_path()

    print(f"Minimum project duration: {analysis['project_duration']} time units")

    print("\nSchedule analysis:")
    for task_id in project.topological_order():
        task = project.tasks[task_id]

        print(
            f"{task_id:12} "
            f"ES={analysis['earliest_start'][task_id]:2} "
            f"EF={analysis['earliest_finish'][task_id]:2} "
            f"LS={analysis['latest_start'][task_id]:2} "
            f"LF={analysis['latest_finish'][task_id]:2} "
            f"Slack={analysis['slack'][task_id]:2}"
        )

    print(
        "\nCritical tasks: "
        + " -> ".join(analysis["critical_tasks"])
    )

    print(
        "\nInterpretation: a critical task has zero scheduling slack. "
        "Delaying it without recovering time elsewhere delays the project "
        "completion date under the modeled assumptions."
    )


def demonstrate_state_machine() -> None:
    print("\n=== Dependency-Aware Task State ===")

    project = build_realistic_project()

    print("Initial ready tasks:")
    print([task.task_id for task in project.ready_tasks()])

    project.mark_started("DISCOVERY")
    project.mark_completed("DISCOVERY")

    print("\nAfter completing DISCOVERY:")
    print([task.task_id for task in project.ready_tasks()])

    project.mark_started("ARCH")
    project.mark_completed("ARCH")

    print("\nAfter completing ARCH:")
    print([task.task_id for task in project.ready_tasks()])

    project.mark_started("SCHEMA")
    project.mark_completed("SCHEMA")

    project.mark_started("INFRA")
    project.mark_completed("INFRA")

    print("\nAfter completing SCHEMA and INFRA:")
    print([task.task_id for task in project.ready_tasks()])

    project.mark_started("API")
    project.mark_failed("API")

    print("\nAfter API failure:")
    project.print_status()

    print(
        "\nThe API failure blocks dependent integration work. "
        "Independent work is not automatically blocked."
    )


def demonstrate_cycle_detection() -> None:
    print("\n=== Circular Dependency Detection ===")

    project = ProjectDependencyGraph("Invalid Release")

    project.add_task("A", "Define API contract", 1)
    project.add_task("B", "Implement service", 1, dependencies={"A"})

    # A cycle cannot be created through add_task because validation is
    # intentionally enforced at the graph boundary. We demonstrate the
    # detector against a deliberately corrupted in-memory graph instead.
    project.tasks["A"].dependencies.add("B")

    try:
        project.validate()
    except DependencyError as error:
        print(f"Rejected graph: {error}")


def demonstrate_invalid_reference() -> None:
    print("\n=== Missing Dependency Validation ===")

    project = ProjectDependencyGraph("Invalid Dependency Reference")
    project.tasks["PAYMENT"] = Task(
        task_id="PAYMENT",
        name="Implement payment processing",
        duration=4,
        dependencies={"NON_EXISTENT_TASK"},
    )

    try:
        project.validate()
    except DependencyError as error:
        print(f"Rejected graph: {error}")


def demonstrate_exports() -> None:
    print("\n=== Dependency Plan Export ===")

    project = build_realistic_project()

    output_dir = Path("dependency_demo_output")
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / "project_dependencies.json"
    csv_path = output_dir / "project_dependencies.csv"

    project.export_json(json_path)
    project.export_csv(csv_path)

    print(f"JSON plan written to: {json_path}")
    print(f"CSV plan written to:  {csv_path}")

    print("\nJSON preview:")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "project": payload["project"],
                "task_count": len(payload["tasks"]),
            },
            indent=2,
        )
    )


def demonstrate_dependency_queries() -> None:
    print("\n=== Dependency Queries ===")

    project = build_realistic_project()

    task_id = "E2E"

    print(f"Prerequisites of {task_id}:")
    print(sorted(project.predecessors(task_id)))

    print("\nTasks directly dependent on E2E:")
    print(sorted(project.successors(task_id)))

    print("\nTasks directly dependent on API:")
    print(sorted(project.successors("API")))


def run_edge_case_tests() -> None:
    print("\n=== Executable Edge-Case Checks ===")

    try:
        Task("BAD", "Invalid duration", 0)
    except ValueError as error:
        print(f"Duration validation passed: {error}")

    project = ProjectDependencyGraph("Edge Cases")

    try:
        project.add_task(
            "SELF",
            "Self-dependent task",
            1,
            dependencies={"SELF"},
        )
    except DependencyError as error:
        print(f"Self-dependency validation passed: {error}")

    project.add_task("A", "Independent task", 1)

    try:
        project.add_task(
            "A",
            "Duplicate task",
            1,
        )
    except DependencyError as error:
        print(f"Duplicate-ID validation passed: {error}")

    try:
        project.mark_completed("A")
    except DependencyError as error:
        print(f"State-transition validation passed: {error}")


def main() -> None:
    print("=" * 72)
    print("PROJECT DEPENDENCIES: UNDERSTANDING TASK DEPENDENCIES")
    print("=" * 72)

    demonstrate_basic_graph()
    demonstrate_critical_path()
    demonstrate_state_machine()
    demonstrate_dependency_queries()
    demonstrate_cycle_detection()
    demonstrate_invalid_reference()
    run_edge_case_tests()
    demonstrate_exports()

    print("\n=== Production Design Considerations ===")
    print(
        "A dependency graph should reject unknown task references and cycles "
        "before execution planning begins."
    )
    print(
        "A scheduling engine should distinguish an unfinished prerequisite "
        "from a failed prerequisite because their operational consequences differ."
    )
    print(
        "Parallel execution is constrained not only by dependencies but also "
        "by real resource limits such as people, environments, and deployment capacity."
    )
    print(
        "Critical-path analysis describes schedule sensitivity; it does not "
        "automatically account for uncertainty, resource contention, or risk."
    )
    print(
        "Persisted dependency data should be validated when loaded rather than "
        "trusted merely because it was previously generated by the system."
    )


if __name__ == "__main__":
    main()
