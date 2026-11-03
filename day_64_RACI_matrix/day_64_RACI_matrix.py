#!/usr/bin/env python3
"""RACI matrix model with validation, workload analysis, and publication controls."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional


class Responsibility(str, Enum):
    RESPONSIBLE = "R"
    ACCOUNTABLE = "A"
    CONSULTED = "C"
    INFORMED = "I"


class MatrixStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"


class RaciError(ValueError):
    """Raised when a RACI operation violates a domain rule."""


@dataclass(frozen=True)
class Role:
    code: str
    name: str
    department: str
    max_responsible_tasks: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.name.strip():
            raise RaciError("Role code and name cannot be empty.")
        if self.max_responsible_tasks is not None:
            if self.max_responsible_tasks < 0:
                raise RaciError("Role capacity cannot be negative.")


@dataclass(frozen=True)
class WorkItem:
    task_id: str
    title: str
    security_sensitive: bool = False

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.title.strip():
            raise RaciError("Task ID and title cannot be empty.")


class RaciMatrix:
    """Maintains one responsibility code per role and work item."""

    def __init__(self, project_id: str, project_name: str) -> None:
        if not project_id.strip() or not project_name.strip():
            raise RaciError("Project ID and name are required.")

        self.project_id = project_id
        self.project_name = project_name
        self.roles: dict[str, Role] = {}
        self.tasks: dict[str, WorkItem] = {}
        self.assignments: dict[str, dict[str, Responsibility]] = defaultdict(dict)
        self.status = MatrixStatus.DRAFT
        self.version = 1
        self.audit_log: list[str] = []

    def _ensure_draft(self) -> None:
        if self.status != MatrixStatus.DRAFT:
            raise RaciError("An active matrix cannot be modified.")

    def add_role(self, role: Role) -> None:
        self._ensure_draft()
        if role.code in self.roles:
            raise RaciError(f"Duplicate role code: {role.code}")
        self.roles[role.code] = role
        self.audit_log.append(f"Role added: {role.code}")

    def add_task(self, task: WorkItem) -> None:
        self._ensure_draft()
        if task.task_id in self.tasks:
            raise RaciError(f"Duplicate task ID: {task.task_id}")
        self.tasks[task.task_id] = task
        self.assignments[task.task_id] = {}
        self.audit_log.append(f"Task added: {task.task_id}")

    def assign(
        self,
        task_id: str,
        role_code: str,
        responsibility: Responsibility | str,
        *,
        replace: bool = False,
    ) -> None:
        self._ensure_draft()

        if task_id not in self.tasks:
            raise RaciError(f"Unknown task: {task_id}")
        if role_code not in self.roles:
            raise RaciError(f"Unknown role: {role_code}")

        try:
            code = Responsibility(responsibility)
        except ValueError as exc:
            raise RaciError(
                "Responsibility must be R, A, C, or I."
            ) from exc

        row = self.assignments[task_id]
        if role_code in row and not replace:
            raise RaciError(
                f"{role_code} already has an assignment for {task_id}; "
                "use replace=True to change it."
            )

        previous = row.get(role_code)
        row[role_code] = code
        self.audit_log.append(
            f"{task_id}: {role_code} changed from "
            f"{previous.value if previous else 'UNASSIGNED'} to {code.value}"
        )

    def validate(self) -> list[str]:
        """Return blocking policy violations without changing matrix state."""
        errors: list[str] = []

        if not self.tasks:
            errors.append("The matrix contains no work items.")

        for task_id, task in self.tasks.items():
            row = self.assignments.get(task_id, {})
            accountable_count = sum(
                code == Responsibility.ACCOUNTABLE for code in row.values()
            )
            responsible_count = sum(
                code == Responsibility.RESPONSIBLE for code in row.values()
            )

            if accountable_count != 1:
                errors.append(
                    f"{task_id}: expected exactly one A; found "
                    f"{accountable_count}."
                )

            if responsible_count < 1:
                errors.append(f"{task_id}: at least one R is required.")

            if task.security_sensitive:
                security_code = row.get("SECURITY_OFFICER")
                if security_code != Responsibility.CONSULTED:
                    errors.append(
                        f"{task_id}: SECURITY_OFFICER must be assigned C."
                    )

        return errors

    def workload_warnings(self) -> list[str]:
        """Return capacity warnings; these do not automatically block publication."""
        responsible_tasks: dict[str, int] = defaultdict(int)

        for row in self.assignments.values():
            for role_code, responsibility in row.items():
                if responsibility == Responsibility.RESPONSIBLE:
                    responsible_tasks[role_code] += 1

        warnings: list[str] = []
        for role_code, role in self.roles.items():
            capacity = role.max_responsible_tasks
            workload = responsible_tasks[role_code]

            if capacity is not None and workload > capacity:
                warnings.append(
                    f"{role_code}: responsible for {workload} tasks; "
                    f"capacity is {capacity}."
                )

        return warnings

    def publish(self) -> None:
        self._ensure_draft()
        errors = self.validate()

        if errors:
            raise RaciError(
                "Publication blocked:\n- " + "\n- ".join(errors)
            )

        self.status = MatrixStatus.ACTIVE
        self.version += 1
        self.audit_log.append(f"Matrix published at version {self.version}")

    def role_workload(self) -> dict[str, dict[str, int]]:
        """Count each role's R, A, C, and I assignments."""
        result: dict[str, dict[str, int]] = {}

        for role_code in self.roles:
            counts = {code.value: 0 for code in Responsibility}
            for row in self.assignments.values():
                responsibility = row.get(role_code)
                if responsibility is not None:
                    counts[responsibility.value] += 1
            result[role_code] = counts

        return result

    def render(self) -> str:
        headers = ["Task", *[role.name for role in self.roles.values()]]
        role_codes = list(self.roles)
        rows: list[list[str]] = []

        for task_id, task in self.tasks.items():
            row = [f"{task_id}: {task.title}"]
            assignments = self.assignments.get(task_id, {})
            row.extend(
                assignments.get(role_code, Responsibility.INFORMED).value
                if role_code in assignments
                else "-"
                for role_code in role_codes
            )
            rows.append(row)

        widths = [
            max(len(headers[index]), *(len(row[index]) for row in rows))
            for index in range(len(headers))
        ]

        def format_row(values: list[str]) -> str:
            return " | ".join(
                value.ljust(widths[index])
                for index, value in enumerate(values)
            )

        separator = "-+-".join("-" * width for width in widths)
        return "\n".join(
            [format_row(headers), separator]
            + [format_row(row) for row in rows]
        )

    def to_json(self) -> str:
        payload = {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "status": self.status.value,
            "version": self.version,
            "roles": [asdict(role) for role in self.roles.values()],
            "tasks": [asdict(task) for task in self.tasks.values()],
            "assignments": [
                {
                    "task_id": task_id,
                    "role_code": role_code,
                    "responsibility": responsibility.value,
                }
                for task_id, row in self.assignments.items()
                for role_code, responsibility in row.items()
            ],
            "audit_log": self.audit_log,
        }
        return json.dumps(payload, indent=2)


def build_cloud_migration_matrix() -> RaciMatrix:
    matrix = RaciMatrix("PRJ-100", "Cloud Infrastructure Migration")

    roles = [
        Role("SPONSOR", "Project Sponsor", "Executive Office"),
        Role("PM", "Project Manager", "Program Management"),
        Role("ARCHITECT", "Cloud Architect", "Technology", 2),
        Role("SECURITY_OFFICER", "Security Officer", "Information Security"),
        Role("QA", "Quality Lead", "Quality Assurance"),
        Role("OPERATIONS", "Operations Lead", "IT Operations", 2),
    ]

    tasks = [
        WorkItem("T1", "Inventory and discovery"),
        WorkItem("T2", "Target architecture approval", True),
        WorkItem("T3", "Production migration", True),
        WorkItem("T4", "Acceptance testing"),
    ]

    for role in roles:
        matrix.add_role(role)

    for task in tasks:
        matrix.add_task(task)

    assignments = [
        ("T1", "SPONSOR", "A"),
        ("T1", "PM", "R"),
        ("T1", "ARCHITECT", "C"),
        ("T1", "SECURITY_OFFICER", "I"),
        ("T1", "QA", "I"),
        ("T1", "OPERATIONS", "C"),

        ("T2", "SPONSOR", "I"),
        ("T2", "PM", "A"),
        ("T2", "ARCHITECT", "R"),
        ("T2", "SECURITY_OFFICER", "C"),
        ("T2", "QA", "I"),
        ("T2", "OPERATIONS", "C"),

        ("T3", "SPONSOR", "I"),
        ("T3", "PM", "A"),
        ("T3", "ARCHITECT", "R"),
        ("T3", "SECURITY_OFFICER", "C"),
        ("T3", "QA", "I"),
        ("T3", "OPERATIONS", "R"),

        ("T4", "SPONSOR", "I"),
        ("T4", "PM", "A"),
        ("T4", "ARCHITECT", "I"),
        ("T4", "SECURITY_OFFICER", "I"),
        ("T4", "QA", "R"),
        ("T4", "OPERATIONS", "C"),
    ]

    for task_id, role_code, responsibility in assignments:
        matrix.assign(task_id, role_code, responsibility)

    return matrix


def demonstrate_invalid_matrix() -> None:
    incomplete = RaciMatrix("PRJ-200", "Incomplete Payment Platform")
    incomplete.add_role(Role("PM", "Project Manager", "Delivery"))
    incomplete.add_role(Role("DEV", "Developer", "Engineering"))
    incomplete.add_role(
        Role("SECURITY_OFFICER", "Security Officer", "Security")
    )
    incomplete.add_task(
        WorkItem("P1", "Payment security review", security_sensitive=True)
    )

    incomplete.assign("P1", "DEV", "R")
    incomplete.assign("P1", "SECURITY_OFFICER", "I")

    try:
        incomplete.publish()
    except RaciError as exc:
        print("\nExpected publication failure:")
        print(exc)


def main() -> None:
    matrix = build_cloud_migration_matrix()

    errors = matrix.validate()
    assert not errors, errors

    print(f"Project: {matrix.project_name}")
    print(f"Status: {matrix.status.value}")
    print("\nRACI Matrix")
    print(matrix.render())

    warnings = matrix.workload_warnings()
    print("\nWorkload warnings:")
    print("\n".join(warnings) if warnings else "None")

    matrix.publish()
    print(f"\nPublished version: {matrix.version}")
    print(f"Status: {matrix.status.value}")

    print("\nRole workload:")
    print(json.dumps(matrix.role_workload(), indent=2))

    print("\nSerialized matrix:")
    print(matrix.to_json())

    try:
        matrix.assign("T1", "PM", "A", replace=True)
    except RaciError as exc:
        print(f"\nExpected modification failure: {exc}")

    demonstrate_invalid_matrix()


if __name__ == "__main__":
    main()
