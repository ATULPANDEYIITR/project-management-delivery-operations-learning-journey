"""
RESOURCE MANAGEMENT REVIEW
Team Management and Resource Allocation Review System

Features:
- Team and employee management
- Skills and competency tracking
- Resource capacity calculations
- Workload and utilization analysis
- Project allocation management
- Availability and leave tracking
- Allocation conflict detection
- Workload fairness assessment
- Skill-gap identification
- Resource risk assessment
- Review decisions and action tracking
- JSON reporting and audit logging

Python 3.10+
Uses only the Python standard library.
"""

from __future__ import annotations

import json
import logging
import statistics
import uuid

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("resource_review")

OUTPUT_DIRECTORY = Path("resource_review_output")
OUTPUT_DIRECTORY.mkdir(exist_ok=True)


# ---------------------------------------------------------
# DOMAIN ENUMS
# ---------------------------------------------------------

class EmployeeStatus(Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    INACTIVE = "inactive"


class ProjectStatus(Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"


class ReviewStatus(Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------
# CUSTOM EXCEPTIONS
# ---------------------------------------------------------

class ResourceManagementError(Exception):
    pass


class ValidationError(ResourceManagementError):
    pass


class AllocationError(ResourceManagementError):
    pass


class ReviewError(ResourceManagementError):
    pass


# ---------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------

@dataclass
class Employee:
    employee_id: str
    name: str
    department: str
    role: str
    skills: dict[str, int]
    weekly_capacity: float = 40.0
    status: EmployeeStatus = EmployeeStatus.ACTIVE

    def __post_init__(self):
        if not self.employee_id.strip():
            raise ValidationError("Employee ID is required.")

        if not self.name.strip():
            raise ValidationError("Employee name is required.")

        if self.weekly_capacity <= 0:
            raise ValidationError("Weekly capacity must be positive.")

        for skill, level in self.skills.items():
            if not skill.strip() or not 1 <= level <= 5:
                raise ValidationError(
                    "Skill levels must be between 1 and 5."
                )


@dataclass
class Project:
    project_id: str
    name: str
    department: str
    required_skills: dict[str, int]
    priority: int
    status: ProjectStatus = ProjectStatus.ACTIVE

    def __post_init__(self):
        if not self.project_id or not self.name:
            raise ValidationError("Project identity is required.")

        if not 1 <= self.priority <= 5:
            raise ValidationError("Priority must be between 1 and 5.")

        for skill, level in self.required_skills.items():
            if not skill.strip() or not 1 <= level <= 5:
                raise ValidationError("Invalid project skill requirement.")


@dataclass
class Allocation:
    allocation_id: str
    employee_id: str
    project_id: str
    weekly_hours: float
    start_date: date
    end_date: date

    def __post_init__(self):
        if self.weekly_hours <= 0:
            raise ValidationError("Allocation hours must be positive.")

        if self.start_date > self.end_date:
            raise ValidationError("Invalid allocation date range.")


@dataclass
class LeaveRecord:
    employee_id: str
    start_date: date
    end_date: date
    weekly_unavailable_hours: float

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValidationError("Invalid leave date range.")

        if self.weekly_unavailable_hours < 0:
            raise ValidationError("Unavailable hours cannot be negative.")


@dataclass
class ReviewAction:
    action_id: str
    description: str
    owner_id: str
    due_date: date
    status: ActionStatus = ActionStatus.OPEN


@dataclass
class ResourceReview:
    review_id: str
    review_date: date
    reviewer: str
    period_start: date
    period_end: date
    status: ReviewStatus = ReviewStatus.DRAFT
    findings: list[dict] = field(default_factory=list)
    actions: list[ReviewAction] = field(default_factory=list)
    decision_notes: str = ""


# ---------------------------------------------------------
# RESOURCE MANAGEMENT ENGINE
# ---------------------------------------------------------

class ResourceManagementSystem:

    def __init__(self):
        self.employees: dict[str, Employee] = {}
        self.projects: dict[str, Project] = {}
        self.allocations: dict[str, Allocation] = {}
        self.leave_records: list[LeaveRecord] = []
        self.reviews: dict[str, ResourceReview] = {}
        self.audit_log: list[dict] = []

    def _audit(self, operation: str, details: dict):
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        })

    # -----------------------------------------------------
    # EMPLOYEE MANAGEMENT
    # -----------------------------------------------------

    def add_employee(self, employee: Employee):
        if employee.employee_id in self.employees:
            raise ValidationError("Employee already exists.")

        self.employees[employee.employee_id] = employee

        self._audit("EMPLOYEE_ADDED", {
            "employee_id": employee.employee_id
        })

    def update_employee_status(
        self,
        employee_id: str,
        status: EmployeeStatus
    ):
        employee = self._get_employee(employee_id)
        employee.status = status

        self._audit("EMPLOYEE_STATUS_UPDATED", {
            "employee_id": employee_id,
            "status": status.value
        })

    def _get_employee(self, employee_id: str) -> Employee:
        employee = self.employees.get(employee_id)

        if employee is None:
            raise ValidationError(
                f"Employee {employee_id} does not exist."
            )

        return employee

    def _get_project(self, project_id: str) -> Project:
        project = self.projects.get(project_id)

        if project is None:
            raise ValidationError(
                f"Project {project_id} does not exist."
            )

        return project

    # -----------------------------------------------------
    # PROJECT MANAGEMENT
    # -----------------------------------------------------

    def add_project(self, project: Project):
        if project.project_id in self.projects:
            raise ValidationError("Project already exists.")

        self.projects[project.project_id] = project

        self._audit("PROJECT_ADDED", {
            "project_id": project.project_id
        })

    # -----------------------------------------------------
    # LEAVE MANAGEMENT
    # -----------------------------------------------------

    def add_leave(self, leave: LeaveRecord):
        self._get_employee(leave.employee_id)

        self.leave_records.append(leave)

        self._audit("LEAVE_RECORDED", {
            "employee_id": leave.employee_id,
            "start": leave.start_date.isoformat(),
            "end": leave.end_date.isoformat()
        })

    def unavailable_hours(
        self,
        employee_id: str,
        start: date,
        end: date
    ) -> float:
        total = 0.0

        for leave in self.leave_records:
            if leave.employee_id != employee_id:
                continue

            if leave.start_date <= end and leave.end_date >= start:
                total += leave.weekly_unavailable_hours

        employee = self._get_employee(employee_id)

        return min(total, employee.weekly_capacity)

    # -----------------------------------------------------
    # ALLOCATION MANAGEMENT
    # -----------------------------------------------------

    def allocated_hours(
        self,
        employee_id: str,
        start: date,
        end: date
    ) -> float:
        return sum(
            allocation.weekly_hours
            for allocation in self.allocations.values()
            if allocation.employee_id == employee_id
            and allocation.start_date <= end
            and allocation.end_date >= start
        )

    def available_capacity(
        self,
        employee_id: str,
        start: date,
        end: date
    ) -> float:
        employee = self._get_employee(employee_id)

        if employee.status != EmployeeStatus.ACTIVE:
            return 0.0

        capacity = (
            employee.weekly_capacity
            - self.unavailable_hours(employee_id, start, end)
        )

        return max(
            0.0,
            capacity - self.allocated_hours(employee_id, start, end)
        )

    def allocate_resource(self, allocation: Allocation):
        employee = self._get_employee(allocation.employee_id)
        project = self._get_project(allocation.project_id)

        if allocation.allocation_id in self.allocations:
            raise AllocationError("Allocation ID already exists.")

        if employee.status != EmployeeStatus.ACTIVE:
            raise AllocationError("Employee is not active.")

        if project.status != ProjectStatus.ACTIVE:
            raise AllocationError("Project is not active.")

        if allocation.start_date > allocation.end_date:
            raise AllocationError("Invalid allocation period.")

        available = self.available_capacity(
            employee.employee_id,
            allocation.start_date,
            allocation.end_date
        )

        if allocation.weekly_hours > available:
            raise AllocationError(
                f"Insufficient capacity for {employee.name}. "
                f"Available: {available:.2f} hours, "
                f"requested: {allocation.weekly_hours:.2f} hours."
            )

        self.allocations[allocation.allocation_id] = allocation

        self._audit("RESOURCE_ALLOCATED", {
            "allocation_id": allocation.allocation_id,
            "employee_id": allocation.employee_id,
            "project_id": allocation.project_id,
            "hours": allocation.weekly_hours
        })

    def remove_allocation(self, allocation_id: str):
        if allocation_id not in self.allocations:
            raise AllocationError("Allocation does not exist.")

        del self.allocations[allocation_id]

        self._audit("ALLOCATION_REMOVED", {
            "allocation_id": allocation_id
        })

    # -----------------------------------------------------
    # UTILIZATION ANALYSIS
    # -----------------------------------------------------

    def utilization_report(
        self,
        start: date,
        end: date
    ) -> list[dict]:

        report = []

        for employee in self.employees.values():
            if employee.status != EmployeeStatus.ACTIVE:
                continue

            unavailable = self.unavailable_hours(
                employee.employee_id, start, end
            )

            effective_capacity = max(
                0.0,
                employee.weekly_capacity - unavailable
            )

            allocated = self.allocated_hours(
                employee.employee_id, start, end
            )

            utilization = (
                allocated / effective_capacity * 100
                if effective_capacity > 0
                else 0.0
            )

            report.append({
                "employee_id": employee.employee_id,
                "name": employee.name,
                "department": employee.department,
                "capacity": effective_capacity,
                "allocated_hours": allocated,
                "available_hours": max(
                    0.0, effective_capacity - allocated
                ),
                "utilization_percentage": round(utilization, 2),
                "overallocated": allocated > effective_capacity
            })

        return report

    # -----------------------------------------------------
    # SKILL MATCHING
    # -----------------------------------------------------

    def skill_gap_report(self, project_id: str) -> dict:
        project = self._get_project(project_id)

        candidates = []

        for employee in self.employees.values():
            if employee.status != EmployeeStatus.ACTIVE:
                continue

            gaps = {}
            matched = 0

            for skill, required_level in project.required_skills.items():
                available_level = employee.skills.get(skill, 0)

                if available_level >= required_level:
                    matched += 1
                else:
                    gaps[skill] = {
                        "required": required_level,
                        "available": available_level
                    }

            total = len(project.required_skills)

            score = (
                matched / total * 100
                if total else 100.0
            )

            candidates.append({
                "employee_id": employee.employee_id,
                "name": employee.name,
                "skill_match_percentage": round(score, 2),
                "skill_gaps": gaps
            })

        candidates.sort(
            key=lambda item: item["skill_match_percentage"],
            reverse=True
        )

        return {
            "project_id": project_id,
            "required_skills": project.required_skills,
            "candidates": candidates
        }

    # -----------------------------------------------------
    # WORKLOAD FAIRNESS
    # -----------------------------------------------------

    def fairness_report(
        self,
        start: date,
        end: date
    ) -> dict:

        report = self.utilization_report(start, end)

        values = [
            item["utilization_percentage"]
            for item in report
        ]

        if not values:
            return {
                "average_utilization": 0,
                "standard_deviation": 0,
                "highest_utilization": 0,
                "lowest_utilization": 0
            }

        return {
            "average_utilization": round(
                statistics.mean(values), 2
            ),
            "standard_deviation": round(
                statistics.pstdev(values), 2
            ),
            "highest_utilization": max(values),
            "lowest_utilization": min(values)
        }

    # -----------------------------------------------------
    # RISK ASSESSMENT
    # -----------------------------------------------------

    def risk_assessment(
        self,
        start: date,
        end: date
    ) -> list[dict]:

        risks = []

        for item in self.utilization_report(start, end):

            utilization = item["utilization_percentage"]

            if item["overallocated"]:
                level = RiskLevel.CRITICAL
                reason = "Allocated workload exceeds available capacity."

            elif utilization >= 95:
                level = RiskLevel.HIGH
                reason = "Very limited remaining capacity."

            elif utilization >= 85:
                level = RiskLevel.MEDIUM
                reason = "Reduced capacity buffer."

            elif utilization < 40:
                level = RiskLevel.MEDIUM
                reason = "Potentially underutilized resource."

            else:
                level = RiskLevel.LOW
                reason = "Utilization within the operating range."

            risks.append({
                "employee_id": item["employee_id"],
                "name": item["name"],
                "utilization": utilization,
                "risk_level": level.value,
                "reason": reason
            })

        return risks

    # -----------------------------------------------------
    # RESOURCE REVIEW
    # -----------------------------------------------------

    def create_review(
        self,
        reviewer: str,
        start: date,
        end: date
    ) -> ResourceReview:

        if start > end:
            raise ReviewError("Review period is invalid.")

        review = ResourceReview(
            review_id=str(uuid.uuid4()),
            review_date=date.today(),
            reviewer=reviewer,
            period_start=start,
            period_end=end,
            status=ReviewStatus.UNDER_REVIEW
        )

        utilization = self.utilization_report(start, end)
        risks = self.risk_assessment(start, end)

        for item in utilization:
            if item["overallocated"]:
                review.findings.append({
                    "type": "OVERALLOCATION",
                    "employee_id": item["employee_id"],
                    "severity": "CRITICAL",
                    "details": "Workload exceeds effective capacity."
                })

        for risk in risks:
            if risk["risk_level"] in {
                RiskLevel.HIGH.value,
                RiskLevel.CRITICAL.value
            }:
                review.findings.append({
                    "type": "CAPACITY_RISK",
                    "employee_id": risk["employee_id"],
                    "severity": risk["risk_level"].upper(),
                    "details": risk["reason"]
                })

        self.reviews[review.review_id] = review

        self._audit("REVIEW_CREATED", {
            "review_id": review.review_id,
            "reviewer": reviewer
        })

        return review

    def add_review_action(
        self,
        review_id: str,
        description: str,
        owner_id: str,
        due_date: date
    ):
        review = self.reviews.get(review_id)

        if review is None:
            raise ReviewError("Review does not exist.")

        if review.status != ReviewStatus.UNDER_REVIEW:
            raise ReviewError("Review is not editable.")

        self._get_employee(owner_id)

        if not description.strip():
            raise ValidationError("Action description is required.")

        action = ReviewAction(
            action_id=str(uuid.uuid4()),
            description=description,
            owner_id=owner_id,
            due_date=due_date
        )

        review.actions.append(action)

        self._audit("REVIEW_ACTION_CREATED", {
            "review_id": review_id,
            "action_id": action.action_id
        })

    def decide_review(
        self,
        review_id: str,
        approved: bool,
        reviewer: str,
        notes: str
    ):
        review = self.reviews.get(review_id)

        if review is None:
            raise ReviewError("Review does not exist.")

        if review.status != ReviewStatus.UNDER_REVIEW:
            raise ReviewError("Review has already been decided.")

        if not reviewer.strip() or not notes.strip():
            raise ReviewError("Reviewer and decision notes are required.")

        if approved and any(
            finding["severity"] == "CRITICAL"
            for finding in review.findings
        ):
            raise ReviewError(
                "Critical resource risks must be resolved before approval."
            )

        review.status = (
            ReviewStatus.APPROVED
            if approved else ReviewStatus.REJECTED
        )

        review.decision_notes = notes

        self._audit("REVIEW_DECIDED", {
            "review_id": review_id,
            "decision": review.status.value,
            "reviewer": reviewer
        })

    # -----------------------------------------------------
    # REPORT EXPORT
    # -----------------------------------------------------

    def export_report(
        self,
        review_id: str,
        start: date,
        end: date
    ) -> Path:

        review = self.reviews.get(review_id)

        if review is None:
            raise ReviewError("Review does not exist.")

        data = {
            "review": {
                "review_id": review.review_id,
                "reviewer": review.reviewer,
                "review_date": review.review_date.isoformat(),
                "period_start": review.period_start.isoformat(),
                "period_end": review.period_end.isoformat(),
                "status": review.status.value,
                "findings": review.findings,
                "actions": [
                    {
                        **asdict(action),
                        "due_date": action.due_date.isoformat(),
                        "status": action.status.value
                    }
                    for action in review.actions
                ],
                "decision_notes": review.decision_notes
            },
            "utilization": self.utilization_report(start, end),
            "fairness": self.fairness_report(start, end),
            "risks": self.risk_assessment(start, end),
            "generated_at": datetime.now().isoformat()
        }

        filename = f"review_{review_id}.json"
        output_path = OUTPUT_DIRECTORY / filename

        # Fixed output directory and generated filename prevent
        # arbitrary user-controlled file path writes.
        output_path.write_text(
            json.dumps(data, indent=4),
            encoding="utf-8"
        )

        return output_path


# ---------------------------------------------------------
# DEMONSTRATION AND VALIDATION
# ---------------------------------------------------------

def main():

    system = ResourceManagementSystem()

    period_start = date(2026, 11, 1)
    period_end = date(2026, 11, 30)

    employees = [
        Employee(
            "E101",
            "Aarav Sharma",
            "Engineering",
            "Senior Developer",
            {"python": 5, "sql": 4, "cloud": 4}
        ),
        Employee(
            "E102",
            "Meera Singh",
            "Engineering",
            "Backend Developer",
            {"python": 4, "sql": 5, "cloud": 3}
        ),
        Employee(
            "E103",
            "Rohan Verma",
            "Analytics",
            "Data Analyst",
            {"python": 3, "sql": 4, "analytics": 5}
        ),
        Employee(
            "E104",
            "Ananya Gupta",
            "Engineering",
            "Cloud Engineer",
            {"cloud": 5, "python": 3, "security": 4}
        )
    ]

    for employee in employees:
        system.add_employee(employee)

    project = Project(
        "P101",
        "Enterprise Platform Modernization",
        "Engineering",
        {
            "python": 4,
            "sql": 4,
            "cloud": 4
        },
        priority=5
    )

    system.add_project(project)

    allocations = [
        Allocation(
            "A101", "E101", "P101", 35,
            period_start, period_end
        ),
        Allocation(
            "A102", "E102", "P101", 25,
            period_start, period_end
        ),
        Allocation(
            "A103", "E103", "P101", 20,
            period_start, period_end
        ),
        Allocation(
            "A104", "E104", "P101", 30,
            period_start, period_end
        )
    ]

    for allocation in allocations:
        system.allocate_resource(allocation)

    system.add_leave(
        LeaveRecord(
            "E102",
            date(2026, 11, 10),
            date(2026, 11, 14),
            8
        )
    )

    print("\nRESOURCE UTILIZATION")

    for item in system.utilization_report(
        period_start, period_end
    ):
        print(item)

    print("\nWORKLOAD FAIRNESS")
    print(system.fairness_report(period_start, period_end))

    print("\nSKILL MATCHING")
    print(system.skill_gap_report("P101"))

    print("\nRESOURCE RISKS")

    for risk in system.risk_assessment(
        period_start, period_end
    ):
        print(risk)

    review = system.create_review(
        "Resource Management Lead",
        period_start,
        period_end
    )

    for employee in employees:
        if employee.status == EmployeeStatus.ACTIVE:
            system.add_review_action(
                review.review_id,
                f"Review workload and capacity for {employee.name}",
                employee.employee_id,
                date(2026, 12, 5)
            )

    try:
        system.decide_review(
            review.review_id,
            approved=True,
            reviewer="Department Head",
            notes="Resource allocation reviewed."
        )

    except ReviewError as error:
        print("\nREVIEW DECISION BLOCKED:", error)

        system.decide_review(
            review.review_id,
            approved=False,
            reviewer="Department Head",
            notes="Critical resource findings require corrective action."
        )

    report_path = system.export_report(
        review.review_id,
        period_start,
        period_end
    )

    print("\nREVIEW STATUS:", review.status.value)
    print("REPORT:", report_path)
    print("AUDIT EVENTS:", len(system.audit_log))

    # Verify important domain invariants.
    assert len(system.employees) == 4
    assert len(system.projects) == 1
    assert len(system.allocations) == 4
    assert review.status in {
        ReviewStatus.APPROVED,
        ReviewStatus.REJECTED
    }

    # An allocation that exceeds capacity must be rejected.
    try:
        system.allocate_resource(
            Allocation(
                "A999",
                "E103",
                "P101",
                50,
                period_start,
                period_end
            )
        )
        raise AssertionError("Over-allocation was not rejected.")

    except AllocationError:
        print("OVERALLOCATION VALIDATION: PASSED")

    print("\nRESOURCE MANAGEMENT REVIEW COMPLETED")


if __name__ == "__main__":
    main()
