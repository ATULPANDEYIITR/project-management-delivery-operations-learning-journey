from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Iterable


class MilestoneStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class EventType(str, Enum):
    PROJECT_STARTED = "project_started"
    REQUIREMENT_APPROVED = "requirement_approved"
    DESIGN_COMPLETED = "design_completed"
    DEVELOPMENT_STARTED = "development_started"
    PULL_REQUEST_OPENED = "pull_request_opened"
    CODE_REVIEW_COMPLETED = "code_review_completed"
    APPROVAL_GRANTED = "approval_granted"
    STATUS_CHECK_FAILED = "status_check_failed"
    STATUS_CHECK_PASSED = "status_check_passed"
    MERGED = "merged"
    RELEASED = "released"
    MILESTONE_COMPLETED = "milestone_completed"
    MILESTONE_BLOCKED = "milestone_blocked"


@dataclass(frozen=True)
class ProjectEvent:
    event_id: int
    project_id: str
    event_type: EventType
    title: str
    occurred_at: datetime
    actor: str
    milestone_id: str | None = None
    details: str = ""


@dataclass
class Milestone:
    milestone_id: str
    project_id: str
    name: str
    description: str
    target_date: date
    status: MilestoneStatus = MilestoneStatus.PLANNED
    importance: int = 3
    dependencies: set[str] = field(default_factory=set)
    completed_at: datetime | None = None

    def validate(self) -> None:
        if not self.milestone_id.strip():
            raise ValueError("Milestone ID cannot be empty.")
        if not self.name.strip():
            raise ValueError("Milestone name cannot be empty.")
        if not 1 <= self.importance <= 5:
            raise ValueError("Importance must be between 1 and 5.")

    @property
    def overdue(self) -> bool:
        return self.status not in {
            MilestoneStatus.COMPLETED,
            MilestoneStatus.CANCELLED,
        } and date.today() > self.target_date


@dataclass
class PullRequest:
    number: int
    source_branch: str
    target_branch: str
    milestone_id: str
    commits: list[str]
    draft: bool = True
    review_approved: bool = False
    changes_requested: bool = False
    status_checks_passed: bool = False
    merged: bool = False
    conflict: bool = False

    def ready_for_merge(self) -> bool:
        return (
            not self.draft
            and self.review_approved
            and not self.changes_requested
            and self.status_checks_passed
            and not self.conflict
            and not self.merged
        )


@dataclass
class Review:
    reviewer: str
    pull_request_number: int
    state: str
    submitted_at: datetime
    comment_count: int = 0
    resolved_comment_count: int = 0

    @property
    def is_approval(self) -> bool:
        return self.state.upper() == "APPROVED"

    @property
    def has_unresolved_discussion(self) -> bool:
        return self.comment_count > self.resolved_comment_count


@dataclass
class BranchProtection:
    branch_name: str
    required_approvals: int = 1
    require_status_checks: bool = True
    require_conversation_resolution: bool = True
    allow_force_push: bool = False
    allow_deletion: bool = False
    require_linear_history: bool = False
    restrict_direct_pushes: bool = True
    dismiss_stale_approvals: bool = True


class MilestoneTracker:
    """
    A self-contained project-event tracker.

    The tracker treats a milestone as an important project outcome rather
    than simply a date. Events provide evidence of progress toward that
    outcome. Repository events such as pull requests, reviews, approvals,
    status checks, and merges can therefore become milestone evidence.
    """

    def __init__(self, project_id: str, project_name: str):
        self.project_id = project_id
        self.project_name = project_name
        self.milestones: dict[str, Milestone] = {}
        self.events: list[ProjectEvent] = []
        self.pull_requests: dict[int, PullRequest] = {}
        self.reviews: list[Review] = []
        self.branch_protection: dict[str, BranchProtection] = {}
        self._next_event_id = 1

    def add_milestone(self, milestone: Milestone) -> None:
        milestone.validate()

        if milestone.project_id != self.project_id:
            raise ValueError("Milestone belongs to another project.")

        if milestone.milestone_id in self.milestones:
            raise ValueError(f"Milestone already exists: {milestone.milestone_id}")

        unknown_dependencies = milestone.dependencies - set(self.milestones)
        if unknown_dependencies:
            raise ValueError(
                f"Unknown milestone dependencies: {sorted(unknown_dependencies)}"
            )

        self.milestones[milestone.milestone_id] = milestone

    def record_event(
        self,
        event_type: EventType,
        title: str,
        actor: str,
        occurred_at: datetime | None = None,
        milestone_id: str | None = None,
        details: str = "",
    ) -> ProjectEvent:
        if milestone_id is not None and milestone_id not in self.milestones:
            raise ValueError(f"Unknown milestone: {milestone_id}")

        event = ProjectEvent(
            event_id=self._next_event_id,
            project_id=self.project_id,
            event_type=event_type,
            title=title,
            occurred_at=occurred_at or datetime.now(),
            actor=actor,
            milestone_id=milestone_id,
            details=details,
        )

        self.events.append(event)
        self._next_event_id += 1
        return event

    def activate_milestone(self, milestone_id: str, actor: str) -> None:
        milestone = self._get_milestone(milestone_id)

        incomplete_dependencies = [
            dependency
            for dependency in milestone.dependencies
            if self.milestones[dependency].status != MilestoneStatus.COMPLETED
        ]

        if incomplete_dependencies:
            raise RuntimeError(
                f"Cannot activate {milestone_id}; dependencies incomplete: "
                f"{', '.join(sorted(incomplete_dependencies))}"
            )

        if milestone.status not in {
            MilestoneStatus.PLANNED,
            MilestoneStatus.BLOCKED,
        }:
            raise RuntimeError(
                f"Milestone {milestone_id} cannot be activated from "
                f"{milestone.status.value}."
            )

        milestone.status = MilestoneStatus.ACTIVE

    def complete_milestone(
        self,
        milestone_id: str,
        actor: str,
        completion_reason: str,
    ) -> None:
        milestone = self._get_milestone(milestone_id)

        if milestone.status == MilestoneStatus.COMPLETED:
            raise RuntimeError(f"Milestone {milestone_id} is already completed.")

        if milestone.status == MilestoneStatus.CANCELLED:
            raise RuntimeError(f"Cancelled milestone {milestone_id} cannot be completed.")

        related_prs = [
            pr for pr in self.pull_requests.values() if pr.milestone_id == milestone_id
        ]

        incomplete_prs = [pr.number for pr in related_prs if not pr.merged]
        if incomplete_prs:
            raise RuntimeError(
                f"Milestone has unmerged pull requests: {incomplete_prs}"
            )

        milestone.status = MilestoneStatus.COMPLETED
        milestone.completed_at = datetime.now()

        self.record_event(
            EventType.MILESTONE_COMPLETED,
            f"Milestone completed: {milestone.name}",
            actor,
            milestone_id=milestone_id,
            details=completion_reason,
        )

    def block_milestone(self, milestone_id: str, actor: str, reason: str) -> None:
        milestone = self._get_milestone(milestone_id)

        if milestone.status == MilestoneStatus.COMPLETED:
            raise RuntimeError("A completed milestone cannot be blocked.")

        milestone.status = MilestoneStatus.BLOCKED

        self.record_event(
            EventType.MILESTONE_BLOCKED,
            f"Milestone blocked: {milestone.name}",
            actor,
            milestone_id=milestone_id,
            details=reason,
        )

    def create_pull_request(
        self,
        number: int,
        source_branch: str,
        target_branch: str,
        milestone_id: str,
        commits: Iterable[str],
        actor: str,
        draft: bool = True,
    ) -> PullRequest:
        if number in self.pull_requests:
            raise ValueError(f"Pull request #{number} already exists.")

        self._get_milestone(milestone_id)

        if source_branch == target_branch:
            raise ValueError("Source and target branches must differ.")

        commit_list = [commit.strip() for commit in commits if commit.strip()]
        if not commit_list:
            raise ValueError("A pull request must contain at least one commit.")

        pr = PullRequest(
            number=number,
            source_branch=source_branch,
            target_branch=target_branch,
            milestone_id=milestone_id,
            commits=commit_list,
            draft=draft,
        )

        self.pull_requests[number] = pr

        self.record_event(
            EventType.PULL_REQUEST_OPENED,
            f"Pull request #{number} opened",
            actor,
            milestone_id=milestone_id,
            details=(
                f"{source_branch} -> {target_branch}; "
                f"{len(commit_list)} commit(s); draft={draft}"
            ),
        )

        return pr

    def submit_review(
        self,
        reviewer: str,
        pull_request_number: int,
        state: str,
        comment_count: int = 0,
        resolved_comment_count: int = 0,
    ) -> Review:
        pr = self._get_pull_request(pull_request_number)

        normalized_state = state.upper()
        valid_states = {"APPROVED", "CHANGES_REQUESTED", "COMMENTED"}
        if normalized_state not in valid_states:
            raise ValueError(f"Unsupported review state: {state}")

        if comment_count < 0 or resolved_comment_count < 0:
            raise ValueError("Review comment counts cannot be negative.")

        if resolved_comment_count > comment_count:
            raise ValueError("Resolved comments cannot exceed total comments.")

        review = Review(
            reviewer=reviewer,
            pull_request_number=pull_request_number,
            state=normalized_state,
            submitted_at=datetime.now(),
            comment_count=comment_count,
            resolved_comment_count=resolved_comment_count,
        )
        self.reviews.append(review)

        if normalized_state == "CHANGES_REQUESTED":
            pr.changes_requested = True

        if normalized_state == "APPROVED":
            self.record_event(
                EventType.APPROVAL_GRANTED,
                f"Pull request #{pull_request_number} approved by {reviewer}",
                reviewer,
                milestone_id=pr.milestone_id,
            )

        self.record_event(
            EventType.CODE_REVIEW_COMPLETED,
            f"Review submitted for pull request #{pull_request_number}",
            reviewer,
            milestone_id=pr.milestone_id,
            details=(
                f"state={normalized_state}; "
                f"comments={comment_count}; resolved={resolved_comment_count}"
            ),
        )

        return review

    def update_status_checks(
        self,
        pull_request_number: int,
        passed: bool,
        actor: str,
        check_name: str,
    ) -> None:
        pr = self._get_pull_request(pull_request_number)
        pr.status_checks_passed = passed

        event_type = (
            EventType.STATUS_CHECK_PASSED
            if passed
            else EventType.STATUS_CHECK_FAILED
        )

        self.record_event(
            event_type,
            f"Status check {check_name}: {'passed' if passed else 'failed'}",
            actor,
            milestone_id=pr.milestone_id,
        )

    def synchronize_pull_request(
        self,
        pull_request_number: int,
        new_commit: str,
        actor: str,
    ) -> None:
        pr = self._get_pull_request(pull_request_number)

        if pr.merged:
            raise RuntimeError("A merged pull request cannot be synchronized.")

        if not new_commit.strip():
            raise ValueError("Synchronization requires a non-empty commit.")

        pr.commits.append(new_commit.strip())

        protection = self.branch_protection.get(pr.target_branch)
        if protection and protection.dismiss_stale_approvals:
            for review in self.reviews:
                if (
                    review.pull_request_number == pull_request_number
                    and review.is_approval
                ):
                    review.state = "COMMENTED"

            pr.review_approved = False

        self.record_event(
            EventType.DEVELOPMENT_STARTED,
            f"Pull request #{pull_request_number} synchronized",
            actor,
            milestone_id=pr.milestone_id,
            details=f"New commit: {new_commit}",
        )

    def configure_branch_protection(
        self,
        policy: BranchProtection,
    ) -> None:
        self.branch_protection[policy.branch_name] = policy

    def evaluate_merge_eligibility(self, pull_request_number: int) -> tuple[bool, list[str]]:
        pr = self._get_pull_request(pull_request_number)
        reasons: list[str] = []

        policy = self.branch_protection.get(pr.target_branch)
        if policy is None:
            reasons.append("Target branch has no configured protection policy.")

        if pr.draft:
            reasons.append("Pull request is still a draft.")

        if pr.conflict:
            reasons.append("Pull request contains merge conflicts.")

        if pr.changes_requested:
            reasons.append("At least one review requests changes.")

        active_approvals = {
            review.reviewer
            for review in self.reviews
            if review.pull_request_number == pr.number
            and review.is_approval
            and not review.has_unresolved_discussion
        }

        required_approvals = policy.required_approvals if policy else 1

        if len(active_approvals) < required_approvals:
            reasons.append(
                f"Requires {required_approvals} eligible approval(s); "
                f"currently has {len(active_approvals)}."
            )

        if policy and policy.require_status_checks and not pr.status_checks_passed:
            reasons.append("Required status checks have not passed.")

        unresolved = [
            review
            for review in self.reviews
            if review.pull_request_number == pr.number
            and review.has_unresolved_discussion
        ]

        if policy and policy.require_conversation_resolution and unresolved:
            reasons.append("Review conversations remain unresolved.")

        return not reasons, reasons

    def merge_pull_request(self, pull_request_number: int, actor: str) -> None:
        pr = self._get_pull_request(pull_request_number)
        eligible, reasons = self.evaluate_merge_eligibility(pull_request_number)

        if not eligible:
            raise RuntimeError(
                "Pull request cannot be merged:\n- " + "\n- ".join(reasons)
            )

        pr.merged = True
        pr.review_approved = True

        self.record_event(
            EventType.MERGED,
            f"Pull request #{pull_request_number} merged",
            actor,
            milestone_id=pr.milestone_id,
            details=f"{pr.source_branch} -> {pr.target_branch}",
        )

    def milestone_progress(self, milestone_id: str) -> dict[str, object]:
        milestone = self._get_milestone(milestone_id)
        related_events = [
            event for event in self.events if event.milestone_id == milestone_id
        ]
        related_prs = [
            pr for pr in self.pull_requests.values() if pr.milestone_id == milestone_id
        ]

        return {
            "milestone": milestone.name,
            "status": milestone.status.value,
            "target_date": milestone.target_date.isoformat(),
            "overdue": milestone.overdue,
            "event_count": len(related_events),
            "pull_requests": len(related_prs),
            "merged_pull_requests": sum(pr.merged for pr in related_prs),
            "last_event": (
                related_events[-1].title if related_events else "No events recorded"
            ),
        }

    def important_events(
        self,
        milestone_id: str | None = None,
        minimum_importance: int = 4,
    ) -> list[ProjectEvent]:
        allowed_types = {
            EventType.PROJECT_STARTED,
            EventType.REQUIREMENT_APPROVED,
            EventType.DESIGN_COMPLETED,
            EventType.PULL_REQUEST_OPENED,
            EventType.CODE_REVIEW_COMPLETED,
            EventType.APPROVAL_GRANTED,
            EventType.STATUS_CHECK_FAILED,
            EventType.MERGED,
            EventType.RELEASED,
            EventType.MILESTONE_COMPLETED,
            EventType.MILESTONE_BLOCKED,
        }

        important_milestones = {
            milestone.milestone_id
            for milestone in self.milestones.values()
            if milestone.importance >= minimum_importance
        }

        return [
            event
            for event in self.events
            if event.event_type in allowed_types
            and (milestone_id is None or event.milestone_id == milestone_id)
            and (
                event.milestone_id is None
                or event.milestone_id in important_milestones
            )
        ]

    def event_timeline(self) -> list[ProjectEvent]:
        return sorted(self.events, key=lambda event: event.occurred_at)

    def _get_milestone(self, milestone_id: str) -> Milestone:
        try:
            return self.milestones[milestone_id]
        except KeyError as exc:
            raise ValueError(f"Unknown milestone: {milestone_id}") from exc

    def _get_pull_request(self, number: int) -> PullRequest:
        try:
            return self.pull_requests[number]
        except KeyError as exc:
            raise ValueError(f"Unknown pull request #{number}") from exc


def print_timeline(tracker: MilestoneTracker) -> None:
    print("\nPROJECT EVENT TIMELINE")
    print("=" * 80)

    for event in tracker.event_timeline():
        milestone = f" [{event.milestone_id}]" if event.milestone_id else ""
        print(
            f"{event.occurred_at:%Y-%m-%d %H:%M} | "
            f"{event.event_type.value:28} | "
            f"{event.actor:12} | "
            f"{event.title}{milestone}"
        )


def demonstrate() -> None:
    tracker = MilestoneTracker(
        project_id="PRJ-204",
        project_name="Payments Platform Modernization",
    )

    today = date.today()

    tracker.add_milestone(
        Milestone(
            milestone_id="M1",
            project_id="PRJ-204",
            name="Requirements Baseline",
            description="Approved business and technical requirements.",
            target_date=today + timedelta(days=7),
            importance=5,
        )
    )

    tracker.add_milestone(
        Milestone(
            milestone_id="M2",
            project_id="PRJ-204",
            name="Payment Service Implementation",
            description="Implement the new payment service and automated tests.",
            target_date=today + timedelta(days=28),
            importance=5,
            dependencies={"M1"},
        )
    )

    tracker.add_milestone(
        Milestone(
            milestone_id="M3",
            project_id="PRJ-204",
            name="Production Release",
            description="Merge release-ready work and deploy the approved version.",
            target_date=today + timedelta(days=42),
            importance=5,
            dependencies={"M2"},
        )
    )

    tracker.record_event(
        EventType.PROJECT_STARTED,
        "Payments modernization project started",
        "project-manager",
        milestone_id="M1",
    )

    tracker.activate_milestone("M1", "project-manager")

    tracker.record_event(
        EventType.REQUIREMENT_APPROVED,
        "Payment API and reconciliation requirements approved",
        "product-owner",
        milestone_id="M1",
        details="Scope baseline accepted by product and engineering.",
    )

    tracker.complete_milestone(
        "M1",
        "product-owner",
        "Requirements were reviewed and formally accepted.",
    )

    tracker.activate_milestone("M2", "engineering-manager")

    tracker.record_event(
        EventType.DESIGN_COMPLETED,
        "Payment service architecture accepted",
        "architect",
        milestone_id="M2",
    )

    pr = tracker.create_pull_request(
        number=482,
        source_branch="feature/payment-service",
        target_branch="main",
        milestone_id="M2",
        commits=[
            "Implement payment authorization",
            "Add idempotency handling",
            "Add reconciliation tests",
        ],
        actor="developer",
        draft=True,
    )

    tracker.configure_branch_protection(
        BranchProtection(
            branch_name="main",
            required_approvals=2,
            require_status_checks=True,
            require_conversation_resolution=True,
            allow_force_push=False,
            allow_deletion=False,
            require_linear_history=True,
            restrict_direct_pushes=True,
            dismiss_stale_approvals=True,
        )
    )

    pr.draft = False

    tracker.submit_review(
        reviewer="senior-engineer",
        pull_request_number=482,
        state="APPROVED",
        comment_count=2,
        resolved_comment_count=2,
    )

    tracker.submit_review(
        reviewer="security-reviewer",
        pull_request_number=482,
        state="COMMENTED",
        comment_count=1,
        resolved_comment_count=0,
    )

    eligible, reasons = tracker.evaluate_merge_eligibility(482)
    print("\nMERGE CHECK BEFORE FINAL REVIEW")
    print("Eligible:", eligible)
    for reason in reasons:
        print(" -", reason)

    tracker.submit_review(
        reviewer="security-reviewer",
        pull_request_number=482,
        state="APPROVED",
        comment_count=1,
        resolved_comment_count=1,
    )

    tracker.update_status_checks(
        pull_request_number=482,
        passed=True,
        actor="ci-system",
        check_name="unit-and-integration-tests",
    )

    eligible, reasons = tracker.evaluate_merge_eligibility(482)
    print("\nMERGE CHECK AFTER REQUIRED CONDITIONS")
    print("Eligible:", eligible)
    if reasons:
        for reason in reasons:
            print(" -", reason)

    tracker.merge_pull_request(482, "release-manager")

    tracker.complete_milestone(
        "M2",
        "engineering-manager",
        "Implementation pull request passed review, policy checks, and merged.",
    )

    tracker.activate_milestone("M3", "release-manager")

    tracker.record_event(
        EventType.RELEASED,
        "Payment service version 2.0 deployed to production",
        "release-manager",
        milestone_id="M3",
        details="Deployment health checks passed.",
    )

    tracker.complete_milestone(
        "M3",
        "release-manager",
        "Production deployment completed successfully.",
    )

    print("\nMILESTONE PROGRESS")
    print("=" * 80)
    for milestone_id in tracker.milestones:
        print(tracker.milestone_progress(milestone_id))

    print_timeline(tracker)

    print("\nIMPORTANT PROJECT EVENTS")
    print("=" * 80)
    for event in tracker.important_events():
        print(
            f"{event.event_type.value}: {event.title} "
            f"by {event.actor}"
        )


if __name__ == "__main__":
    demonstrate()
