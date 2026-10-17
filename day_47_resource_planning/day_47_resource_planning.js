from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Iterable
import csv
import json


class ResourceType(Enum):
    PERSON = "person"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    BUDGET = "budget"


class AllocationStatus(Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    RELEASED = "released"
    CONFLICT = "conflict"


class SkillLevel(Enum):
    JUNIOR = 1
    MID = 2
    SENIOR = 3
    EXPERT = 4


@dataclass(frozen=True)
class Person:
    person_id: str
    name: str
    role: str
    skills: frozenset[str]
    skill_level: SkillLevel
    capacity_hours_per_week: float
    hourly_cost: float


@dataclass(frozen=True)
class Equipment:
    equipment_id: str
    name: str
    category: str
    hourly_cost: float
    available_from: date
    available_until: date


@dataclass(frozen=True)
class SoftwareLicense:
    license_id: str
    product: str
    seats: int
    monthly_cost: float


@dataclass
class ProjectTask:
    task_id: str
    name: str
    required_skills: set[str]
    minimum_skill_level: SkillLevel
    estimated_hours: float
    start_date: date
    end_date: date
    priority: int
    assigned_people: list[str] = field(default_factory=list)

    @property
    def working_days(self) -> int:
        days = (self.end_date - self.start_date).days + 1
        return sum(
            1
            for offset in range(max(days, 0))
            if (self.start_date + timedelta(days=offset)).weekday() < 5
        )


@dataclass
class Allocation:
    resource_id: str
    resource_type: ResourceType
    task_id: str
    start_date: date
    end_date: date
    hours: float
    status: AllocationStatus = AllocationStatus.PLANNED


@dataclass
class ResourcePlan:
    project_name: str
    budget: float
    people: dict[str, Person] = field(default_factory=dict)
    equipment: dict[str, Equipment] = field(default_factory=dict)
    software: dict[str, SoftwareLicense] = field(default_factory=dict)
    tasks: dict[str, ProjectTask] = field(default_factory=dict)
    allocations: list[Allocation] = field(default_factory=list)

    def add_task(self, task: ProjectTask) -> None:
        if task.task_id in self.tasks:
            raise ValueError(f"Task already exists: {task.task_id}")
        if task.start_date > task.end_date:
            raise ValueError("Task start date cannot be after its end date.")
        if task.estimated_hours <= 0:
            raise ValueError("Task effort must be positive.")
        self.tasks[task.task_id] = task

    def candidate_people(self, task: ProjectTask) -> list[Person]:
        candidates = []
        for person in self.people.values():
            if (
                task.required_skills.issubset(person.skills)
                and person.skill_level.value >= task.minimum_skill_level.value
            ):
                candidates.append(person)

        # Prefer stronger skill matches and then lower cost.
        return sorted(
            candidates,
            key=lambda person: (
                -person.skill_level.value,
                person.hourly_cost,
                person.name,
            ),
        )

    def allocated_hours(
        self,
        resource_id: str,
        start_date: date,
        end_date: date,
        exclude_task_id: str | None = None,
    ) -> float:
        total = 0.0
        for allocation in self.allocations:
            if allocation.resource_id != resource_id:
                continue
            if exclude_task_id and allocation.task_id == exclude_task_id:
                continue
            if allocation.status == AllocationStatus.RELEASED:
                continue
            overlaps = (
                allocation.start_date <= end_date
                and allocation.end_date >= start_date
            )
            if overlaps:
                total += allocation.hours
        return total

    def has_person_conflict(
        self,
        person: Person,
        start_date: date,
        end_date: date,
        hours: float,
        exclude_task_id: str | None = None,
    ) -> bool:
        existing = self.allocated_hours(
            person.person_id,
            start_date,
            end_date,
            exclude_task_id,
        )
        working_days = max(
            1,
            sum(
                1
                for offset in range((end_date - start_date).days + 1)
                if (start_date + timedelta(days=offset)).weekday() < 5
            ),
        )
        weekly_equivalent = hours / (working_days / 5)
        return existing + weekly_equivalent > person.capacity_hours_per_week

    def assign_person(
        self,
        task_id: str,
        person_id: str,
        hours: float,
    ) -> Allocation:
        if task_id not in self.tasks:
            raise KeyError(f"Unknown task: {task_id}")
        if person_id not in self.people:
            raise KeyError(f"Unknown person: {person_id}")
        if hours <= 0:
            raise ValueError("Allocated hours must be positive.")

        task = self.tasks[task_id]
        person = self.people[person_id]

        if not task.required_skills.issubset(person.skills):
            missing = task.required_skills - person.skills
            raise ValueError(
                f"{person.name} lacks required skills: {', '.join(sorted(missing))}"
            )

        if person.skill_level.value < task.minimum_skill_level.value:
            raise ValueError(
                f"{person.name} does not meet the required skill level."
            )

        if self.has_person_conflict(
            person,
            task.start_date,
            task.end_date,
            hours,
            exclude_task_id=task_id,
        ):
            raise ValueError(
                f"Capacity conflict detected for {person.name} on {task.name}."
            )

        allocation = Allocation(
            resource_id=person.person_id,
            resource_type=ResourceType.PERSON,
            task_id=task.task_id,
            start_date=task.start_date,
            end_date=task.end_date,
            hours=hours,
        )
        self.allocations.append(allocation)
        task.assigned_people.append(person.person_id)
        return allocation

    def project_cost(self) -> float:
        personnel_cost = 0.0
        for allocation in self.allocations:
            if allocation.resource_type == ResourceType.PERSON:
                person = self.people[allocation.resource_id]
                personnel_cost += allocation.hours * person.hourly_cost

        equipment_cost = 0.0
        for allocation in self.allocations:
            if allocation.resource_type == ResourceType.EQUIPMENT:
                equipment = self.equipment[allocation.resource_id]
                equipment_cost += allocation.hours * equipment.hourly_cost

        software_cost = sum(
            license.monthly_cost for license in self.software.values()
        )

        return personnel_cost + equipment_cost + software_cost

    def budget_remaining(self) -> float:
        return self.budget - self.project_cost()

    def utilization_report(self) -> list[dict[str, object]]:
        report = []

        for person in self.people.values():
            allocated = 0.0
            for allocation in self.allocations:
                if allocation.resource_id != person.person_id:
                    continue
                if allocation.status == AllocationStatus.RELEASED:
                    continue
                allocated += allocation.hours

            report.append(
                {
                    "resource": person.name,
                    "role": person.role,
                    "allocated_hours": round(allocated, 2),
                    "capacity_reference": person.capacity_hours_per_week,
                    "utilization_percent": round(
                        allocated / person.capacity_hours_per_week * 100,
                        2,
                    ),
                }
            )

        return report

    def find_unassigned_tasks(self) -> list[ProjectTask]:
        return [
            task
            for task in self.tasks.values()
            if not task.assigned_people
        ]

    def export_json(self, output_path: Path) -> None:
        payload = {
            "project": self.project_name,
            "budget": self.budget,
            "cost": round(self.project_cost(), 2),
            "budget_remaining": round(self.budget_remaining(), 2),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "required_skills": sorted(task.required_skills),
                    "estimated_hours": task.estimated_hours,
                    "start_date": task.start_date.isoformat(),
                    "end_date": task.end_date.isoformat(),
                    "assigned_people": task.assigned_people,
                }
                for task in self.tasks.values()
            ],
            "allocations": [
                {
                    "resource_id": allocation.resource_id,
                    "resource_type": allocation.resource_type.value,
                    "task_id": allocation.task_id,
                    "start_date": allocation.start_date.isoformat(),
                    "end_date": allocation.end_date.isoformat(),
                    "hours": allocation.hours,
                    "status": allocation.status.value,
                }
                for allocation in self.allocations
            ],
        }

        output_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def export_csv(self, output_path: Path) -> None:
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "resource_id",
                    "resource_type",
                    "task_id",
                    "start_date",
                    "end_date",
                    "hours",
                    "status",
                ]
            )
            for allocation in self.allocations:
                writer.writerow(
                    [
                        allocation.resource_id,
                        allocation.resource_type.value,
                        allocation.task_id,
                        allocation.start_date,
                        allocation.end_date,
                        allocation.hours,
                        allocation.status.value,
                    ]
                )


def build_example_plan() -> ResourcePlan:
    plan = ResourcePlan(
        project_name="National Service Portal Modernization",
        budget=120_000.0,
    )

    plan.people.update(
        {
            "P001": Person(
                person_id="P001",
                name="Asha Rao",
                role="Senior Backend Engineer",
                skills=frozenset({"python", "postgresql", "api", "security"}),
                skill_level=SkillLevel.SENIOR,
                capacity_hours_per_week=40,
                hourly_cost=75,
            ),
            "P002": Person(
                person_id="P002",
                name="Vikram Singh",
                role="Frontend Engineer",
                skills=frozenset({"javascript", "typescript", "react", "api"}),
                skill_level=SkillLevel.SENIOR,
                capacity_hours_per_week=40,
                hourly_cost=68,
            ),
            "P003": Person(
                person_id="P003",
                name="Meera Shah",
                role="Security Engineer",
                skills=frozenset({"security", "cloud", "testing"}),
                skill_level=SkillLevel.EXPERT,
                capacity_hours_per_week=32,
                hourly_cost=92,
            ),
            "P004": Person(
                person_id="P004",
                name="Rohan Das",
                role="Data Engineer",
                skills=frozenset({"python", "postgresql", "data"}),
                skill_level=SkillLevel.MID,
                capacity_hours_per_week=40,
                hourly_cost=62,
            ),
        }
    )

    plan.equipment["E001"] = Equipment(
        equipment_id="E001",
        name="Load Testing Workstation",
        category="performance-testing",
        hourly_cost=12,
        available_from=date(2026, 10, 20),
        available_until=date(2026, 12, 31),
    )

    plan.software["S001"] = SoftwareLicense(
        license_id="S001",
        product="Enterprise Security Scanner",
        seats=5,
        monthly_cost=850,
    )

    plan.add_task(
        ProjectTask(
            task_id="T001",
            name="Secure API implementation",
            required_skills={"python", "api", "security"},
            minimum_skill_level=SkillLevel.SENIOR,
            estimated_hours=80,
            start_date=date(2026, 10, 19),
            end_date=date(2026, 10, 30),
            priority=1,
        )
    )

    plan.add_task(
        ProjectTask(
            task_id="T002",
            name="Citizen portal interface",
            required_skills={"javascript", "react"},
            minimum_skill_level=SkillLevel.SENIOR,
            estimated_hours=70,
            start_date=date(2026, 10, 26),
            end_date=date(2026, 11, 6),
            priority=2,
        )
    )

    plan.add_task(
        ProjectTask(
            task_id="T003",
            name="Security validation",
            required_skills={"security", "testing"},
            minimum_skill_level=SkillLevel.EXPERT,
            estimated_hours=48,
            start_date=date(2026, 11, 2),
            end_date=date(2026, 11, 13),
            priority=1,
        )
    )

    plan.add_task(
        ProjectTask(
            task_id="T004",
            name="Operational data pipeline",
            required_skills={"python", "postgresql", "data"},
            minimum_skill_level=SkillLevel.MID,
            estimated_hours=64,
            start_date=date(2026, 11, 2),
            end_date=date(2026, 11, 13),
            priority=2,
        )
    )

    plan.assign_person("T001", "P001", 80)
    plan.assign_person("T002", "P002", 70)
    plan.assign_person("T003", "P003", 48)
    plan.assign_person("T004", "P004", 64)

    return plan


def demonstrate_resource_planning() -> None:
    plan = build_example_plan()

    print("=" * 72)
    print(plan.project_name)
    print("=" * 72)

    print("\nTask-resource allocation:")
    for task in plan.tasks.values():
        people = ", ".join(
            plan.people[person_id].name
            for person_id in task.assigned_people
        )
        print(
            f"{task.task_id:<5} {task.name:<30} "
            f"{task.estimated_hours:>5.0f} h -> {people}"
        )

    print("\nResource utilization:")
    for row in plan.utilization_report():
        print(
            f"{row['resource']:<18} "
            f"{row['allocated_hours']:>6.1f} / "
            f"{row['capacity_reference']:<5.1f} hours "
            f"({row['utilization_percent']:>6.2f}%)"
        )

    print("\nCost control:")
    print(f"Planned cost:     ${plan.project_cost():,.2f}")
    print(f"Budget:           ${plan.budget:,.2f}")
    print(f"Budget remaining: ${plan.budget_remaining():,.2f}")

    print("\nSkill matching:")
    task = plan.tasks["T003"]
    candidates = plan.candidate_people(task)
    for person in candidates:
        print(
            f"{person.name}: "
            f"{person.role}, "
            f"{person.skill_level.name.lower()}, "
            f"${person.hourly_cost:.2f}/hour"
        )

    print("\nValidation example:")
    try:
        plan.assign_person("T003", "P001", 16)
    except ValueError as error:
        print(f"Rejected allocation: {error}")

    output_dir = Path("resource_plan_output")
    output_dir.mkdir(exist_ok=True)
    plan.export_json(output_dir / "resource_plan.json")
    plan.export_csv(output_dir / "resource_allocations.csv")

    print("\nExported:")
    print(output_dir / "resource_plan.json")
    print(output_dir / "resource_allocations.csv")


if __name__ == "__main__":
    demonstrate_resource_planning()
