#!/usr/bin/env python3
"""
Defect Management System
Models defect identification, triage, assignment, lifecycle transitions,
severity/priority, evidence, comments, validation, metrics, and audit history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class DefectStatus(str, Enum):
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    VERIFIED = "VERIFIED"
    REOPENED = "REOPENED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class Severity(str, Enum):
    BLOCKER = "BLOCKER"
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    TRIVIAL = "TRIVIAL"


class Priority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class DefectType(str, Enum):
    FUNCTIONAL = "FUNCTIONAL"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    USABILITY = "USABILITY"
    DATA = "DATA"
    COMPATIBILITY = "COMPATIBILITY"


@dataclass(frozen=True)
class User:
    user_id: int
    name: str
    role: str


@dataclass
class Comment:
    comment_id: int
    author_id: int
    body: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Defect:
    defect_id: int
    title: str
    description: str
    defect_type: DefectType
    severity: Severity
    priority: Priority
    reporter_id: int
    status: DefectStatus = DefectStatus.NEW
    assignee_id: int | None = None
    environment: str = "production"
    affected_version: str = "unknown"
    steps_to_reproduce: list[str] = field(default_factory=list)
    expected_result: str = ""
    actual_result: str = ""
    comments: list[Comment] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
    resolved_by: int | None = None
    resolution: str | None = None

    def record(self, message: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        self.history.append(f"{timestamp} | {message}")

    def add_comment(self, comment: Comment) -> None:
        if not comment.body.strip():
            raise ValueError("Comment cannot be empty.")
        self.comments.append(comment)
        self.record(f"Comment {comment.comment_id} added by user {comment.author_id}.")

    def assign(self, assignee_id: int) -> None:
        if self.status not in {
            DefectStatus.NEW,
            DefectStatus.TRIAGED,
            DefectStatus.ASSIGNED,
            DefectStatus.REOPENED,
        }:
            raise ValueError(f"Cannot assign defect in status {self.status.value}.")
        self.assignee_id = assignee_id
        self.status = DefectStatus.ASSIGNED
        self.record(f"Assigned to user {assignee_id}.")

    def start_work(self, user_id: int) -> None:
        if self.assignee_id != user_id:
            raise PermissionError("Only the assigned user can start work.")
        if self.status != DefectStatus.ASSIGNED:
            raise ValueError("Defect must be assigned before work starts.")
        self.status = DefectStatus.IN_PROGRESS
        self.record(f"Work started by user {user_id}.")

    def resolve(self, user_id: int, resolution: str) -> None:
        if self.assignee_id != user_id:
            raise PermissionError("Only the assignee can resolve the defect.")
        if self.status != DefectStatus.IN_PROGRESS:
            raise ValueError("Only an in-progress defect can be resolved.")
        if not resolution.strip():
            raise ValueError("A resolution is required.")
        self.resolved_by = user_id
        self.resolution = resolution.strip()
        self.status = DefectStatus.RESOLVED
        self.record(f"Resolved by user {user_id}: {self.resolution}")

    def verify(self, tester_id: int, passed: bool) -> None:
        if self.status != DefectStatus.RESOLVED:
            raise ValueError("Only resolved defects can be verified.")
        if passed:
            self.status = DefectStatus.VERIFIED
            self.record(f"Verification passed by user {tester_id}.")
        else:
            self.status = DefectStatus.REOPENED
            self.record(f"Verification failed; reopened by user {tester_id}.")

    def close(self, user_id: int) -> None:
        if self.status != DefectStatus.VERIFIED:
            raise ValueError("Only verified defects can be closed.")
        self.status = DefectStatus.CLOSED
        self.record(f"Closed by user {user_id}.")

    def reject(self, user_id: int, reason: str) -> None:
        if self.status not in {DefectStatus.NEW, DefectStatus.TRIAGED}:
            raise ValueError("Only new or triaged defects can be rejected.")
        if not reason.strip():
            raise ValueError("A rejection reason is required.")
        self.resolution = reason.strip()
        self.status = DefectStatus.REJECTED
        self.record(f"Rejected by user {user_id}: {reason.strip()}")


class DefectManager:
    """Application service responsible for registration, triage, and reporting."""

    SEVERITY_WEIGHT = {
        Severity.BLOCKER: 5,
        Severity.CRITICAL: 4,
        Severity.MAJOR: 3,
        Severity.MINOR: 2,
        Severity.TRIVIAL: 1,
    }

    PRIORITY_WEIGHT = {
        Priority.P0: 5,
        Priority.P1: 4,
        Priority.P2: 2,
        Priority.P3: 1,
    }

    def __init__(self) -> None:
        self.users: dict[int, User] = {}
        self.defects: dict[int, Defect] = {}
        self.next_defect_id = 1000
        self.next_comment_id = 1

    def add_user(self, user: User) -> None:
        if user.user_id in self.users:
            raise ValueError("Duplicate user ID.")
        if not user.name.strip():
            raise ValueError("User name cannot be empty.")
        self.users[user.user_id] = user

    def create_defect(
        self,
        title: str,
        description: str,
        defect_type: DefectType,
        severity: Severity,
        priority: Priority,
        reporter_id: int,
        environment: str,
        affected_version: str,
        steps_to_reproduce: Iterable[str],
        expected_result: str,
        actual_result: str,
    ) -> Defect:
        if reporter_id not in self.users:
            raise ValueError("Unknown reporter.")
        if not title.strip() or not description.strip():
            raise ValueError("Title and description are required.")
        if not expected_result.strip() or not actual_result.strip():
            raise ValueError("Expected and actual results are required.")

        steps = [step.strip() for step in steps_to_reproduce if step.strip()]
        if not steps:
            raise ValueError("At least one reproduction step is required.")

        defect = Defect(
            defect_id=self.next_defect_id,
            title=title.strip(),
            description=description.strip(),
            defect_type=defect_type,
            severity=severity,
            priority=priority,
            reporter_id=reporter_id,
            environment=environment.strip(),
            affected_version=affected_version.strip(),
            steps_to_reproduce=steps,
            expected_result=expected_result.strip(),
            actual_result=actual_result.strip(),
        )
        defect.record(f"Created by user {reporter_id}.")
        self.defects[defect.defect_id] = defect
        self.next_defect_id += 1
        return defect

    def triage(self, defect_id: int, triager_id: int) -> None:
        defect = self._get(defect_id)
        if triager_id not in self.users:
            raise ValueError("Unknown triager.")
        if self.users[triager_id].role not in {"QA", "LEAD", "MANAGER"}:
            raise PermissionError("User is not authorized to triage defects.")
        if defect.status != DefectStatus.NEW:
            raise ValueError("Only new defects can be triaged.")
        defect.status = DefectStatus.TRIAGED
        defect.record(f"Triaged by user {triager_id}.")

    def comment(self, defect_id: int, author_id: int, body: str) -> None:
        if author_id not in self.users:
            raise ValueError("Unknown comment author.")
        defect = self._get(defect_id)
        comment = Comment(self.next_comment_id, author_id, body)
        self.next_comment_id += 1
        defect.add_comment(comment)

    def _get(self, defect_id: int) -> Defect:
        try:
            return self.defects[defect_id]
        except KeyError as exc:
            raise KeyError(f"Defect {defect_id} does not exist.") from exc

    def open_defects(self) -> list[Defect]:
        terminal = {DefectStatus.CLOSED, DefectStatus.REJECTED}
        return [d for d in self.defects.values() if d.status not in terminal]

    def priority_queue(self) -> list[Defect]:
        return sorted(
            self.open_defects(),
            key=lambda d: (
                -self.SEVERITY_WEIGHT[d.severity],
                -self.PRIORITY_WEIGHT[d.priority],
                d.defect_id,
            ),
        )

    def metrics(self) -> dict[str, object]:
        defects = list(self.defects.values())
        by_status = {
            status.value: sum(d.status == status for d in defects)
            for status in DefectStatus
        }
        by_severity = {
            severity.value: sum(d.severity == severity for d in defects)
            for severity in Severity
        }
        resolved = sum(
            d.status in {
                DefectStatus.RESOLVED,
                DefectStatus.VERIFIED,
                DefectStatus.CLOSED,
            }
            for d in defects
        )
        rejected = sum(d.status == DefectStatus.REJECTED for d in defects)

        return {
            "total": len(defects),
            "open": len(self.open_defects()),
            "resolved_or_later": resolved,
            "rejected": rejected,
            "by_status": by_status,
            "by_severity": by_severity,
        }


def print_defect(defect: Defect) -> None:
    print(
        f"[{defect.defect_id}] {defect.title} | "
        f"{defect.status.value} | {defect.severity.value} | "
        f"{defect.priority.value} | assignee={defect.assignee_id}"
    )


def main() -> None:
    manager = DefectManager()

    manager.add_user(User(1, "Asha", "QA"))
    manager.add_user(User(2, "Ravi", "DEVELOPER"))
    manager.add_user(User(3, "Meera", "MANAGER"))
    manager.add_user(User(4, "Vikram", "QA"))

    defect = manager.create_defect(
        title="Checkout returns HTTP 500 for expired payment token",
        description="Checkout fails instead of requesting a fresh payment session.",
        defect_type=DefectType.FUNCTIONAL,
        severity=Severity.CRITICAL,
        priority=Priority.P1,
        reporter_id=1,
        environment="staging",
        affected_version="4.8.2",
        steps_to_reproduce=[
            "Sign in with a valid test account.",
            "Use an expired payment token.",
            "Submit an order above the minimum amount.",
        ],
        expected_result="The payment session is refreshed and checkout continues.",
        actual_result="The API returns HTTP 500.",
    )

    manager.triage(defect.defect_id, 1)
    defect.assign(2)
    defect.start_work(2)
    manager.comment(defect.defect_id, 1, "Server logs show an unhandled token-expiration exception.")
    defect.resolve(2, "Expired-token handling now requests a fresh payment session.")
    defect.verify(4, passed=True)
    defect.close(3)

    # Failure handling is deliberately exercised without corrupting the defect.
    try:
        defect.start_work(2)
    except ValueError as exc:
        print(f"Expected transition failure: {exc}")

    # A second defect demonstrates an unsuccessful verification and reopening.
    reopened = manager.create_defect(
        title="Search filter loses selected date after pagination",
        description="The selected date is reset when moving to page two.",
        defect_type=DefectType.USABILITY,
        severity=Severity.MAJOR,
        priority=Priority.P2,
        reporter_id=4,
        environment="staging",
        affected_version="4.8.2",
        steps_to_reproduce=[
            "Open the search page.",
            "Select a date range.",
            "Move to page two.",
        ],
        expected_result="The date range remains selected.",
        actual_result="The date filter is cleared.",
    )
    manager.triage(reopened.defect_id, 1)
    reopened.assign(2)
    reopened.start_work(2)
    reopened.resolve(2, "Persisted the date range in the search state.")
    reopened.verify(4, passed=False)

    print("\nDefect queue:")
    for item in manager.priority_queue():
        print_defect(item)

    print("\nMetrics:")
    for key, value in manager.metrics().items():
        print(f"{key}: {value}")

    print("\nAudit history for first defect:")
    for entry in defect.history:
        print(entry)

    # Basic invariants provide executable regression checks.
    assert defect.status == DefectStatus.CLOSED
    assert reopened.status == DefectStatus.REOPENED
    assert len(manager.defects) == 2
    assert manager.metrics()["total"] == 2


if __name__ == "__main__":
    main()
