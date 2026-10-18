"""
Resource Allocation: Assigning limited resources to competing tasks.

Demonstrates:
- Resource capacity and task requirements
- Greedy allocation by priority
- Dependency-aware scheduling
- Resource compatibility
- Allocation validation and conflict detection
- Fairness, utilization, and unallocated demand
- Transactional allocation planning and rollback
- A simple makespan-oriented scheduling heuristic

Run with Python 3.10 or later. Uses only the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from copy import deepcopy
from typing import Optional


@dataclass(frozen=True)
class Resource:
    resource_id: str
    resource_type: str
    capacity: float
    cost_per_hour: float = 0.0
    tags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.resource_id.strip():
            raise ValueError("Resource ID cannot be empty.")
        if not self.resource_type.strip():
            raise ValueError("Resource type cannot be empty.")
        if self.capacity <= 0:
            raise ValueError("Resource capacity must be positive.")
        if self.cost_per_hour < 0:
            raise ValueError("Resource cost cannot be negative.")


@dataclass(frozen=True)
class Task:
    task_id: str
    name: str
    demand: float
    duration_hours: float
    priority: int
    required_type: str
    dependencies: tuple[str, ...] = ()
    required_tags: frozenset[str] = frozenset()
    deadline_hour: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("Task ID cannot be empty.")
        if self.demand <= 0 or self.duration_hours <= 0:
            raise ValueError("Task demand and duration must be positive.")
        if self.priority < 0:
            raise ValueError("Priority cannot be negative.")
        if self.task_id in self.dependencies:
            raise ValueError("A task cannot depend on itself.")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("Duplicate dependencies are not allowed.")


@dataclass
class Allocation:
    task_id: str
    resource_id: str
    amount: float
    start_hour: float
    end_hour: float


@dataclass
class AllocationPlan:
    allocations: list[Allocation] = field(default_factory=list)
    rejected_tasks: dict[str, str] = field(default_factory=dict)

    def allocations_for(self, task_id: str) -> list[Allocation]:
        return [a for a in self.allocations if a.task_id == task_id]


class ResourceAllocator:
    def __init__(self, resources: list[Resource], tasks: list[Task]):
        self.resources = {r.resource_id: r for r in resources}
        self.tasks = {t.task_id: t for t in tasks}
        self.plan = AllocationPlan()

        if len(self.resources) != len(resources):
            raise ValueError("Resource IDs must be unique.")
        if len(self.tasks) != len(tasks):
            raise ValueError("Task IDs must be unique.")

        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        for task in self.tasks.values():
            for dependency in task.dependencies:
                if dependency not in self.tasks:
                    raise ValueError(
                        f"Task {task.task_id} references unknown dependency "
                        f"{dependency}."
                    )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError("Task dependencies contain a cycle.")
            if task_id in visited:
                return

            visiting.add(task_id)
            for dependency in self.tasks[task_id].dependencies:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in self.tasks:
            visit(task_id)

    def _compatible(self, task: Task, resource: Resource) -> bool:
        return (
            task.required_type == resource.resource_type
            and task.required_tags.issubset(resource.tags)
            and task.demand <= resource.capacity
        )

    def allocate_by_priority(self) -> AllocationPlan:
        """Allocate each task to one compatible resource.

        Tasks that depend on other tasks are scheduled only after those
        dependencies have been successfully allocated.
        """
        self.plan = AllocationPlan()
        pending = set(self.tasks)
        finish_times: dict[str, float] = {}
        resource_free_at = {rid: 0.0 for rid in self.resources}

        while pending:
            ready = [
                self.tasks[task_id]
                for task_id in pending
                if all(dep in finish_times
                       for dep in self.tasks[task_id].dependencies)
                or any(dep in self.plan.rejected_tasks
                       for dep in self.tasks[task_id].dependencies)
            ]

            if not ready:
                break

            ready.sort(
                key=lambda task: (
                    -task.priority,
                    task.deadline_hour
                    if task.deadline_hour is not None
                    else float("inf"),
                    task.task_id,
                )
            )

            task = ready[0]
            pending.remove(task.task_id)

            failed_dependency = next(
                (dep for dep in task.dependencies
                 if dep in self.plan.rejected_tasks),
                None,
            )
            if failed_dependency:
                self.plan.rejected_tasks[task.task_id] = (
                    f"Dependency {failed_dependency} was not allocated."
                )
                continue

            dependency_ready = max(
                (finish_times[dep] for dep in task.dependencies),
                default=0.0,
            )

            candidates = [
                resource
                for resource in self.resources.values()
                if self._compatible(task, resource)
            ]

            if not candidates:
                self.plan.rejected_tasks[task.task_id] = (
                    "No compatible resource has sufficient capacity."
                )
                continue

            # Prefer the earliest feasible start, then the lowest hourly cost.
            candidates.sort(
                key=lambda resource: (
                    max(dependency_ready, resource_free_at[resource.resource_id]),
                    resource.cost_per_hour,
                    resource.resource_id,
                )
            )
            resource = candidates[0]
            start = max(
                dependency_ready,
                resource_free_at[resource.resource_id],
            )
            end = start + task.duration_hours

            if task.deadline_hour is not None and end > task.deadline_hour:
                self.plan.rejected_tasks[task.task_id] = (
                    f"Deadline missed: finish {end:.1f}, "
                    f"deadline {task.deadline_hour:.1f}."
                )
                continue

            self.plan.allocations.append(
                Allocation(
                    task_id=task.task_id,
                    resource_id=resource.resource_id,
                    amount=task.demand,
                    start_hour=start,
                    end_hour=end,
                )
            )
            resource_free_at[resource.resource_id] = end
            finish_times[task.task_id] = end

        for task_id in pending:
            self.plan.rejected_tasks[task_id] = (
                "Task could not be scheduled; check dependency outcomes."
            )

        return self.plan

    def validate_plan(self) -> list[str]:
        errors: list[str] = []
        by_resource: dict[str, list[Allocation]] = defaultdict(list)
        by_task: dict[str, list[Allocation]] = defaultdict(list)

        for allocation in self.plan.allocations:
            if allocation.resource_id not in self.resources:
                errors.append(
                    f"Unknown resource: {allocation.resource_id}"
                )
                continue
            if allocation.task_id not in self.tasks:
                errors.append(f"Unknown task: {allocation.task_id}")
                continue

            resource = self.resources[allocation.resource_id]
            task = self.tasks[allocation.task_id]

            if allocation.amount > resource.capacity:
                errors.append(
                    f"Capacity exceeded for resource {resource.resource_id}."
                )
            if allocation.amount != task.demand:
                errors.append(
                    f"Allocation amount does not match task {task.task_id}."
                )
            if not self._compatible(task, resource):
                errors.append(
                    f"Resource {resource.resource_id} is incompatible "
                    f"with task {task.task_id}."
                )
            if allocation.end_hour <= allocation.start_hour:
                errors.append(
                    f"Invalid time interval for task {task.task_id}."
                )

            by_resource[allocation.resource_id].append(allocation)
            by_task[allocation.task_id].append(allocation)

        for resource_id, assignments in by_resource.items():
            assignments.sort(key=lambda a: a.start_hour)
            for previous, current in zip(assignments, assignments[1:]):
                if current.start_hour < previous.end_hour:
                    errors.append(
                        f"Time overlap on resource {resource_id}: "
                        f"{previous.task_id} and {current.task_id}."
                    )

        for task_id, assignments in by_task.items():
            if len(assignments) > 1:
                errors.append(
                    f"Task {task_id} has multiple allocations."
                )

        finish = {
            task_id: max(a.end_hour for a in assignments)
            for task_id, assignments in by_task.items()
        }

        for task_id, assignments in by_task.items():
            task = self.tasks[task_id]
            for dependency in task.dependencies:
                if dependency not in finish:
                    errors.append(
                        f"Task {task_id} has an unallocated dependency "
                        f"{dependency}."
                    )
                elif min(a.start_hour for a in assignments) < finish[dependency]:
                    errors.append(
                        f"Task {task_id} starts before dependency "
                        f"{dependency} finishes."
                    )

        return errors

    def utilization(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for resource_id, resource in self.resources.items():
            assigned_hours = sum(
                a.end_hour - a.start_hour
                for a in self.plan.allocations
                if a.resource_id == resource_id
            )
            makespan = max(
                (a.end_hour for a in self.plan.allocations),
                default=0.0,
            )
            result[resource_id] = (
                assigned_hours / makespan * 100.0
                if makespan > 0
                else 0.0
            )
        return result

    def total_cost(self) -> float:
        return sum(
            (a.end_hour - a.start_hour)
            * self.resources[a.resource_id].cost_per_hour
            for a in self.plan.allocations
        )

    def print_report(self) -> None:
        print("\nRESOURCE ALLOCATION PLAN")
        print("-" * 90)
        print(
            f"{'Task':<10}{'Resource':<12}{'Demand':>10}"
            f"{'Start':>12}{'Finish':>12}{'Duration':>12}"
        )

        for allocation in sorted(
            self.plan.allocations,
            key=lambda a: (a.start_hour, a.task_id),
        ):
            print(
                f"{allocation.task_id:<10}"
                f"{allocation.resource_id:<12}"
                f"{allocation.amount:>10.1f}"
                f"{allocation.start_hour:>12.1f}"
                f"{allocation.end_hour:>12.1f}"
                f"{allocation.end_hour - allocation.start_hour:>12.1f}"
            )

        if self.plan.rejected_tasks:
            print("\nUNALLOCATED TASKS")
            for task_id, reason in sorted(self.plan.rejected_tasks.items()):
                print(f"- {task_id}: {reason}")

        print(f"\nTotal estimated cost: {self.total_cost():.2f}")
        print("Resource utilization over schedule makespan:")
        for resource_id, percentage in self.utilization().items():
            print(f"- {resource_id}: {percentage:.1f}%")

        errors = self.validate_plan()
        print("\nPlan validation:", "PASSED" if not errors else "FAILED")
        for error in errors:
            print(f"- {error}")


def demonstrate_transactional_planning(
    allocator: ResourceAllocator,
) -> None:
    """Restore the original plan if a proposed change fails validation."""
    original_plan = deepcopy(allocator.plan)
    try:
        if allocator.plan.allocations:
            # Deliberately introduce an invalid interval to test validation.
            allocator.plan.allocations[0].end_hour = (
                allocator.plan.allocations[0].start_hour
            )
        errors = allocator.validate_plan()
        if errors:
            raise ValueError("; ".join(errors))
    except ValueError as exc:
        allocator.plan = original_plan
        print("\nInvalid change rejected; original plan restored.")
        print(f"Reason: {exc}")


def main() -> None:
    resources = [
        Resource(
            "CPU-A", "compute", 16, 12.0,
            frozenset({"linux", "gpu-compatible"}),
        ),
        Resource(
            "CPU-B", "compute", 8, 7.0,
            frozenset({"linux"}),
        ),
        Resource(
            "DB-A", "database", 12, 15.0,
            frozenset({"postgresql", "high-availability"}),
        ),
        Resource(
            "OPS-A", "operations", 5, 9.0,
            frozenset({"production-access"}),
        ),
    ]

    tasks = [
        Task("T-101", "Data preprocessing", 6, 2, 8, "compute",
             required_tags=frozenset({"linux"}), deadline_hour=8),
        Task("T-102", "Model training", 14, 4, 10, "compute",
             dependencies=("T-101",),
             required_tags=frozenset({"gpu-compatible"}),
             deadline_hour=10),
        Task("T-103", "Database migration", 8, 3, 9, "database",
             required_tags=frozenset({"postgresql"}),
             deadline_hour=9),
        Task("T-104", "Integration tests", 4, 2, 7, "compute",
             dependencies=("T-102",),
             required_tags=frozenset({"linux"}),
             deadline_hour=12),
        Task("T-105", "Production deployment", 3, 2, 10, "operations",
             dependencies=("T-103", "T-104"),
             required_tags=frozenset({"production-access"}),
             deadline_hour=16),
        Task("T-106", "Large simulation", 20, 5, 4, "compute"),
    ]

    allocator = ResourceAllocator(resources, tasks)
    allocator.allocate_by_priority()
    allocator.print_report()
    demonstrate_transactional_planning(allocator)

    print("\nFINAL VALIDATION")
    errors = allocator.validate_plan()
    if errors:
        raise RuntimeError(f"Restored plan is invalid: {errors}")
    print("The original allocation plan remains valid.")


if __name__ == "__main__":
    main()
