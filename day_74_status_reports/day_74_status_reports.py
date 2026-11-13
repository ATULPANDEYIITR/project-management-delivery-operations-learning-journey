#!/usr/bin/env python3
"""
Project Status Reporting and Repository Governance System

Features:
- Project status report generation
- Milestone, task, risk, and issue tracking
- Schedule and budget health evaluation
- Pull Request lifecycle monitoring
- Code review and approval tracking
- Branch protection and merge eligibility
- JSON persistence and report export
- Validation and automated tests

Python 3.10+
Standard-library dependencies only.
"""

from __future__ import annotations

import json
import logging
import statistics
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("project_reporting")


class ValidationError(ValueError):
    pass


class ProjectStatus(str, Enum):
    NOT_STARTED = "not_started"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    DELAYED = "delayed"
    COMPLETED = "completed"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class RiskStatus(str, Enum):
    OPEN = "open"
    MITIGATING = "mitigating"
    CLOSED = "closed"


class ReviewState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    COMMENTED = "commented"
    DISMISSED = "dismissed"


class PRState(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"


class MergeStrategy(str, Enum):
    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass
class Task:
    task_id: str
    title: str
    owner: str
    status: TaskStatus
    priority: Priority
    estimated_hours: float
    actual_hours: float = 0.0

    def __post_init__(self):
        if not self.task_id or not self.title or not self.owner:
            raise ValidationError("Task identifiers and ownership are required.")
        if self.estimated_hours <= 0 or self.actual_hours < 0:
            raise ValidationError("Invalid task hours.")
        if self.actual_hours > 100000:
            raise ValidationError("Actual hours exceed the allowed limit.")


@dataclass
class Milestone:
    milestone_id: str
    name: str
    due_date: date
    completed: bool = False


@dataclass
class Risk:
    risk_id: str
    description: str
    probability: int
    impact: int
    owner: str
    mitigation: str
    status: RiskStatus = RiskStatus.OPEN

    def __post_init__(self):
        if not 1 <= self.probability <= 5:
            raise ValidationError("Risk probability must be between 1 and 5.")
        if not 1 <= self.impact <= 5:
            raise ValidationError("Risk impact must be between 1 and 5.")

    @property
    def exposure(self) -> int:
        return self.probability * self.impact


@dataclass
class StatusCheck:
    name: str
    passed: bool
    required: bool = True


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    eligible: bool = True
    dismissed: bool = False


@dataclass
class PullRequest:
    pr_id: str
    title: str
    source_branch: str
    target_branch: str
    state: PRState
    draft: bool = False
    commits: int = 1
    reviews: list[Review] = field(default_factory=list)
    checks: list[StatusCheck] = field(default_factory=list)
    conversations_resolved: bool = True
    base_synchronized: bool = True
    conflicts: bool = False
    merge_strategy: MergeStrategy = MergeStrategy.SQUASH

    def __post_init__(self):
        if not all((self.pr_id, self.title, self.source_branch, self.target_branch)):
            raise ValidationError("Pull Request fields cannot be empty.")
        if self.source_branch == self.target_branch:
            raise ValidationError("Source and target branches must differ.")
        if self.commits < 0:
            raise ValidationError("Commit count cannot be negative.")

    def approval_count(self) -> int:
        return sum(
            1 for review in self.reviews
            if review.eligible
            and not review.dismissed
            and review.state == ReviewState.APPROVED
        )


@dataclass
class BranchProtection:
    branch_name: str
    required_approvals: int = 2
    required_checks: set[str] = field(default_factory=set)
    require_conversations: bool = True
    require_up_to_date: bool = True
    require_linear_history: bool = False
    allow_direct_push: bool = False
    allow_force_push: bool = False
    allow_deletion: bool = False
    allow_administrator_bypass: bool = False

    def __post_init__(self):
        if self.required_approvals < 0:
            raise ValidationError("Required approvals cannot be negative.")


@dataclass
class Project:
    project_id: str
    name: str
    manager: str
    start_date: date
    target_date: date
    budget: float
    actual_cost: float = 0.0
    tasks: list[Task] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    pull_requests: list[PullRequest] = field(default_factory=list)

    def __post_init__(self):
        if not all((self.project_id, self.name, self.manager)):
            raise ValidationError("Project identification is required.")
        if self.target_date < self.start_date:
            raise ValidationError("Target date precedes start date.")
        if self.budget <= 0 or self.actual_cost < 0:
            raise ValidationError("Invalid project budget.")
        if self.actual_cost > 1_000_000_000:
            raise ValidationError("Actual cost exceeds the permitted limit.")


@dataclass
class GovernanceResult:
    pr_id: str
    eligible: bool
    reasons: list[str]


class GovernanceEngine:
    """Evaluates merge eligibility independently of review decisions."""

    def evaluate(
        self,
        pr: PullRequest,
        protection: BranchProtection
    ) -> GovernanceResult:

        reasons = []

        if pr.state != PRState.OPEN:
            reasons.append("Pull Request is not open.")

        if pr.draft:
            reasons.append("Draft Pull Requests cannot be merged.")

        if pr.target_branch != protection.branch_name:
            reasons.append("Target branch does not match protection policy.")

        if pr.commits == 0:
            reasons.append("No commits are available.")

        if pr.conflicts:
            reasons.append("Merge conflicts must be resolved.")

        if protection.require_up_to_date and not pr.base_synchronized:
            reasons.append("Source branch must be synchronized with target.")

        if protection.require_conversations and not pr.conversations_resolved:
            reasons.append("Unresolved review conversations exist.")

        approvals = pr.approval_count()

        if approvals < protection.required_approvals:
            reasons.append(
                f"Insufficient approvals: {approvals}/"
                f"{protection.required_approvals}."
            )

        checks = {
            check.name: check.passed
            for check in pr.checks
        }

        for required in protection.required_checks:
            if not checks.get(required, False):
                reasons.append(f"Required check failed or missing: {required}.")

        if protection.require_linear_history:
            if pr.merge_strategy == MergeStrategy.MERGE_COMMIT:
                reasons.append("Merge commits violate linear-history policy.")

        return GovernanceResult(
            pr_id=pr.pr_id,
            eligible=len(reasons) == 0,
            reasons=reasons
        )


class StatusReportService:

    def __init__(self, project: Project):
        self.project = project

    def completion_percentage(self) -> float:
        tasks = self.project.tasks

        if not tasks:
            return 0.0

        completed = sum(
            task.status == TaskStatus.COMPLETED
            for task in tasks
        )

        return round(completed / len(tasks) * 100, 2)

    def milestone_completion(self) -> float:
        milestones = self.project.milestones

        if not milestones:
            return 0.0

        completed = sum(m.completed for m in milestones)

        return round(completed / len(milestones) * 100, 2)

    def budget_variance(self) -> float:
        return round(
            self.project.actual_cost - self.project.budget,
            2
        )

    def budget_utilization(self) -> float:
        return round(
            self.project.actual_cost / self.project.budget * 100,
            2
        )

    def schedule_variance_days(self) -> int:
        return (self.project.target_date - date.today()).days

    def calculate_status(self) -> ProjectStatus:

        if self.completion_percentage() == 100:
            return ProjectStatus.COMPLETED

        if not self.project.tasks:
            return ProjectStatus.NOT_STARTED

        if self.budget_utilization() > 100:
            return ProjectStatus.DELAYED

        if any(
            task.status == TaskStatus.BLOCKED
            and task.priority in (Priority.HIGH, Priority.CRITICAL)
            for task in self.project.tasks
        ):
            return ProjectStatus.AT_RISK

        if self.schedule_variance_days() < 0:
            return ProjectStatus.DELAYED

        if any(
            risk.exposure >= 15 and risk.status != RiskStatus.CLOSED
            for risk in self.project.risks
        ):
            return ProjectStatus.AT_RISK

        return ProjectStatus.ON_TRACK

    def risk_report(self) -> dict:

        active = [
            risk for risk in self.project.risks
            if risk.status != RiskStatus.CLOSED
        ]

        return {
            "total": len(self.project.risks),
            "active": len(active),
            "high_exposure": sum(r.exposure >= 15 for r in active),
            "average_exposure": round(
                statistics.mean(r.exposure for r in active), 2
            ) if active else 0,
            "items": [
                {
                    "id": r.risk_id,
                    "description": r.description,
                    "exposure": r.exposure,
                    "owner": r.owner,
                    "status": r.status.value,
                    "mitigation": r.mitigation
                }
                for r in sorted(
                    active,
                    key=lambda item: item.exposure,
                    reverse=True
                )
            ]
        }

    def governance_report(self) -> dict:

        return {
            "total_pull_requests": len(self.project.pull_requests),
            "open": sum(
                pr.state == PRState.OPEN
                for pr in self.project.pull_requests
            ),
            "draft": sum(
                pr.draft for pr in self.project.pull_requests
            ),
            "merged": sum(
                pr.state == PRState.MERGED
                for pr in self.project.pull_requests
            ),
            "closed": sum(
                pr.state == PRState.CLOSED
                for pr in self.project.pull_requests
            ),
            "review_approvals": sum(
                pr.approval_count()
                for pr in self.project.pull_requests
            )
        }

    def generate(self) -> dict:

        tasks = self.project.tasks

        completed_hours = sum(
            t.actual_hours for t in tasks
            if t.status == TaskStatus.COMPLETED
        )

        total_estimated = sum(t.estimated_hours for t in tasks)

        return {
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "project_id": self.project.project_id,
                "project_name": self.project.name,
                "manager": self.project.manager
            },
            "executive_status": self.calculate_status().value,
            "schedule": {
                "start_date": self.project.start_date.isoformat(),
                "target_date": self.project.target_date.isoformat(),
                "remaining_days": self.schedule_variance_days(),
                "completion_percentage": self.completion_percentage(),
                "milestone_completion_percentage": self.milestone_completion()
            },
            "financials": {
                "budget": self.project.budget,
                "actual_cost": self.project.actual_cost,
                "variance": self.budget_variance(),
                "utilization_percentage": self.budget_utilization()
            },
            "delivery": {
                "total_tasks": len(tasks),
                "completed": sum(
                    t.status == TaskStatus.COMPLETED for t in tasks
                ),
                "in_progress": sum(
                    t.status == TaskStatus.IN_PROGRESS for t in tasks
                ),
                "blocked": sum(
                    t.status == TaskStatus.BLOCKED for t in tasks
                ),
                "estimated_hours": total_estimated,
                "completed_actual_hours": completed_hours
            },
            "risks": self.risk_report(),
            "repository_governance": self.governance_report()
        }


class ReportExporter:

    @staticmethod
    def save_json(report: dict, destination: str) -> None:

        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)

        temporary = path.with_suffix(path.suffix + ".tmp")

        try:
            temporary.write_text(
                json.dumps(report, indent=4, ensure_ascii=False),
                encoding="utf-8"
            )
            temporary.replace(path)

        except OSError:
            temporary.unlink(missing_ok=True)
            raise

    @staticmethod
    def save_markdown(report: dict, destination: str) -> None:

        metadata = report["report_metadata"]
        schedule = report["schedule"]
        financials = report["financials"]
        delivery = report["delivery"]
        risks = report["risks"]

        lines = [
            f"# Project Status Report: {metadata['project_name']}",
            "",
            f"**Project ID:** {metadata['project_id']}",
            f"**Manager:** {metadata['manager']}",
            f"**Generated:** {metadata['generated_at']}",
            f"**Status:** {report['executive_status'].upper()}",
            "",
            "## Schedule",
            f"- Start: {schedule['start_date']}",
            f"- Target: {schedule['target_date']}",
            f"- Remaining days: {schedule['remaining_days']}",
            f"- Completion: {schedule['completion_percentage']}%",
            f"- Milestones completed: {schedule['milestone_completion_percentage']}%",
            "",
            "## Financials",
            f"- Budget: {financials['budget']:.2f}",
            f"- Actual cost: {financials['actual_cost']:.2f}",
            f"- Variance: {financials['variance']:.2f}",
            f"- Utilization: {financials['utilization_percentage']}%",
            "",
            "## Delivery",
            f"- Total tasks: {delivery['total_tasks']}",
            f"- Completed: {delivery['completed']}",
            f"- In progress: {delivery['in_progress']}",
            f"- Blocked: {delivery['blocked']}",
            "",
            "## Risks",
            f"- Active risks: {risks['active']}",
            f"- High exposure: {risks['high_exposure']}",
            "",
            "| Risk | Description | Exposure | Owner |",
            "|---|---|---:|---|"
        ]

        for risk in risks["items"]:
            description = risk["description"].replace("|", "\\|")
            lines.append(
                f"| {risk['id']} | {description} | "
                f"{risk['exposure']} | {risk['owner']} |"
            )

        lines.extend([
            "",
            "## Repository Governance",
            f"- Pull Requests: {report['repository_governance']['total_pull_requests']}",
            f"- Open: {report['repository_governance']['open']}",
            f"- Draft: {report['repository_governance']['draft']}",
            f"- Merged: {report['repository_governance']['merged']}",
            f"- Closed: {report['repository_governance']['closed']}",
            ""
        ])

        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")


def create_demo_project() -> Project:

    project = Project(
        project_id="PRJ-2026-001",
        name="Enterprise Project Reporting Platform",
        manager="Project Manager",
        start_date=date(2026, 9, 1),
        target_date=date(2027, 2, 28),
        budget=500000,
        actual_cost=185000
    )

    project.tasks.extend([
        Task(
            "T001", "Requirements analysis", "Analyst",
            TaskStatus.COMPLETED, Priority.HIGH, 80, 76
        ),
        Task(
            "T002", "Database implementation", "Developer",
            TaskStatus.COMPLETED, Priority.HIGH, 120, 130
        ),
        Task(
            "T003", "Reporting engine", "Developer",
            TaskStatus.IN_PROGRESS, Priority.HIGH, 160, 70
        ),
        Task(
            "T004", "Security testing", "Security Lead",
            TaskStatus.BLOCKED, Priority.CRITICAL, 60, 15
        ),
        Task(
            "T005", "Deployment preparation", "Operations",
            TaskStatus.TODO, Priority.MEDIUM, 50
        )
    ])

    project.milestones.extend([
        Milestone("M001", "Requirements approved", date(2026, 10, 1), True),
        Milestone("M002", "Database completed", date(2026, 11, 20), True),
        Milestone("M003", "System testing", date(2027, 1, 15)),
        Milestone("M004", "Production deployment", date(2027, 2, 28))
    ])

    project.risks.extend([
        Risk(
            "R001",
            "Security testing environment unavailable",
            4, 5,
            "Security Lead",
            "Provision isolated testing infrastructure"
        ),
        Risk(
            "R002",
            "Reporting data quality issues",
            3, 3,
            "Data Lead",
            "Introduce automated validation",
            RiskStatus.MITIGATING
        ),
        Risk(
            "R003",
            "Requirements clarification completed",
            1, 2,
            "Analyst",
            "Document approved requirements",
            RiskStatus.CLOSED
        )
    ])

    project.pull_requests.append(
        PullRequest(
            pr_id="PR-101",
            title="Add reporting API",
            source_branch="feature/reporting-api",
            target_branch="main",
            state=PRState.OPEN,
            commits=4,
            reviews=[
                Review("reviewer-a", ReviewState.APPROVED),
                Review("reviewer-b", ReviewState.APPROVED)
            ],
            checks=[
                StatusCheck("unit-tests", True),
                StatusCheck("security-scan", True),
                StatusCheck("lint", True)
            ]
        )
    )

    project.pull_requests.append(
        PullRequest(
            pr_id="PR-102",
            title="Implement security controls",
            source_branch="feature/security",
            target_branch="main",
            state=PRState.OPEN,
            draft=True,
            commits=2,
            reviews=[
                Review("reviewer-c", ReviewState.CHANGES_REQUESTED)
            ],
            checks=[
                StatusCheck("unit-tests", True),
                StatusCheck("security-scan", False)
            ],
            conversations_resolved=False
        )
    )

    return project


def run_tests() -> None:

    project = create_demo_project()
    service = StatusReportService(project)

    assert service.completion_percentage() == 40.0
    assert service.risk_report()["high_exposure"] == 1

    protection = BranchProtection(
        branch_name="main",
        required_approvals=2,
        required_checks={"unit-tests", "security-scan", "lint"}
    )

    engine = GovernanceEngine()

    result = engine.evaluate(
        project.pull_requests[0],
        protection
    )

    assert result.eligible is True

    blocked = engine.evaluate(
        project.pull_requests[1],
        protection
    )

    assert blocked.eligible is False

    try:
        Task(
            "INVALID", "Invalid task", "User",
            TaskStatus.TODO, Priority.HIGH, -5
        )
        raise AssertionError("Invalid task was accepted.")
    except ValidationError:
        pass

    logger.info("All validation tests passed.")


def main() -> None:

    run_tests()

    project = create_demo_project()
    service = StatusReportService(project)

    report = service.generate()

    ReportExporter.save_json(
        report,
        "output/project_status.json"
    )

    ReportExporter.save_markdown(
        report,
        "output/project_status.md"
    )

    protection = BranchProtection(
        branch_name="main",
        required_approvals=2,
        required_checks={"unit-tests", "security-scan", "lint"},
        require_conversations=True,
        require_up_to_date=True,
        require_linear_history=True
    )

    engine = GovernanceEngine()

    print("\nPROJECT STATUS REPORT")
    print("=" * 55)
    print(f"Project: {project.name}")
    print(f"Status: {report['executive_status'].upper()}")
    print(f"Completion: {report['schedule']['completion_percentage']}%")
    print(f"Budget utilization: {report['financials']['utilization_percentage']}%")
    print(f"Active risks: {report['risks']['active']}")

    print("\nPULL REQUEST MERGE ELIGIBILITY")
    print("=" * 55)

    for pr in project.pull_requests:

        result = engine.evaluate(pr, protection)

        print(f"\n{pr.pr_id}: {pr.title}")
        print(f"Eligible: {result.eligible}")

        for reason in result.reasons:
            print(f"  - {reason}")

    print("\nReports saved in output/.")


if __name__ == "__main__":
    main()
