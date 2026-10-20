from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class PullRequestState(Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewState(Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    DISMISSED = "dismissed"


class MergeStrategy(Enum):
    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass(frozen=True)
class Commit:
    sha: str
    message: str
    changed_files: int
    additions: int
    deletions: int


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    submitted_at: datetime
    comment_count: int = 0


@dataclass
class StatusCheck:
    name: str
    passed: bool
    required: bool
    completed_at: datetime


@dataclass
class BranchProtection:
    required_reviews: int
    required_status_checks: Set[str]
    dismiss_stale_approvals: bool = True
    require_conversation_resolution: bool = True
    restrict_direct_push: bool = True
    allow_force_push: bool = False
    allow_deletion: bool = False
    require_linear_history: bool = False
    allowed_merge_strategies: Set[MergeStrategy] = field(
        default_factory=lambda: {
            MergeStrategy.SQUASH,
            MergeStrategy.MERGE_COMMIT,
        }
    )


@dataclass
class PullRequest:
    number: int
    source_branch: str
    target_branch: str
    title: str
    state: PullRequestState = PullRequestState.OPEN
    commits: List[Commit] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    checks: List[StatusCheck] = field(default_factory=list)
    unresolved_conversations: int = 0
    merge_conflicts: bool = False
    synchronized_with_base: bool = True
    changed_files: int = 0
    estimated_review_minutes: int = 0

    def add_commit(self, commit: Commit) -> None:
        if self.state not in {PullRequestState.DRAFT, PullRequestState.OPEN}:
            raise ValueError("Commits cannot be added after a PR is closed or merged.")
        if not commit.sha or len(commit.sha) < 7:
            raise ValueError("A commit SHA must contain at least seven characters.")
        if commit.changed_files < 0 or commit.additions < 0 or commit.deletions < 0:
            raise ValueError("Commit statistics cannot be negative.")

        self.commits.append(commit)
        self.changed_files = sum(c.changed_files for c in self.commits)
        self.synchronized_with_base = True

    def request_review(self, reviewer: str) -> None:
        if self.state != PullRequestState.OPEN:
            raise ValueError("Reviews can only be requested on an open PR.")
        if not reviewer:
            raise ValueError("Reviewer name cannot be empty.")

    def submit_review(self, review: Review) -> None:
        if self.state != PullRequestState.OPEN:
            raise ValueError("Only open PRs can receive reviews.")
        self.reviews.append(review)

    def synchronize_with_base(self) -> None:
        if self.state != PullRequestState.OPEN:
            raise ValueError("Only an open PR can be synchronized.")
        self.synchronized_with_base = True
        self.merge_conflicts = False

    def update_after_base_change(self, conflicts: bool) -> None:
        self.synchronized_with_base = False
        self.merge_conflicts = conflicts

        if conflicts:
            self.synchronized_with_base = False

    def close(self) -> None:
        if self.state == PullRequestState.MERGED:
            raise ValueError("A merged PR cannot be closed.")
        self.state = PullRequestState.CLOSED

    def reopen(self) -> None:
        if self.state != PullRequestState.CLOSED:
            raise ValueError("Only a closed PR can be reopened.")
        self.state = PullRequestState.OPEN


class RepositoryWorkflow:
    def __init__(self, protection: BranchProtection) -> None:
        self.protection = protection

    def _latest_reviews(self, pr: PullRequest) -> Dict[str, Review]:
        latest: Dict[str, Review] = {}
        for review in sorted(pr.reviews, key=lambda r: r.submitted_at):
            latest[review.reviewer] = review
        return latest

    def evaluate_merge(
        self,
        pr: PullRequest,
        eligible_reviewers: Set[str],
        merge_strategy: MergeStrategy,
    ) -> Tuple[bool, List[str]]:
        reasons: List[str] = []

        if pr.state != PullRequestState.OPEN:
            reasons.append("Pull Request is not open.")

        if not pr.source_branch or not pr.target_branch:
            reasons.append("Source and target branches are required.")

        if pr.source_branch == pr.target_branch:
            reasons.append("Source and target branches must differ.")

        if not pr.commits:
            reasons.append("Pull Request has no commits.")

        if not pr.synchronized_with_base:
            reasons.append("Pull Request is not synchronized with the base branch.")

        if pr.merge_conflicts:
            reasons.append("Merge conflicts must be resolved.")

        if merge_strategy not in self.protection.allowed_merge_strategies:
            reasons.append("Selected merge strategy is prohibited.")

        latest_reviews = self._latest_reviews(pr)

        if self.protection.dismiss_stale_approvals and not pr.synchronized_with_base:
            reasons.append("Approvals are stale because the PR changed after base-branch updates.")

        eligible_approvals = {
            reviewer
            for reviewer, review in latest_reviews.items()
            if reviewer in eligible_reviewers
            and review.state == ReviewState.APPROVED
        }

        changes_requested = {
            reviewer
            for reviewer, review in latest_reviews.items()
            if reviewer in eligible_reviewers
            and review.state == ReviewState.CHANGES_REQUESTED
        }

        if changes_requested:
            reasons.append("At least one eligible reviewer currently requests changes.")

        if len(eligible_approvals) < self.protection.required_reviews:
            reasons.append(
                f"Required approvals: {self.protection.required_reviews}; "
                f"eligible approvals: {len(eligible_approvals)}."
            )

        check_map = {check.name: check for check in pr.checks}

        for required_check in self.protection.required_status_checks:
            check = check_map.get(required_check)
            if check is None:
                reasons.append(f"Required status check '{required_check}' is missing.")
            elif not check.passed:
                reasons.append(f"Required status check '{required_check}' failed.")

        if self.protection.require_conversation_resolution and pr.unresolved_conversations:
            reasons.append(
                f"{pr.unresolved_conversations} review conversation(s) remain unresolved."
            )

        return not reasons, reasons

    def merge(
        self,
        pr: PullRequest,
        eligible_reviewers: Set[str],
        merge_strategy: MergeStrategy,
    ) -> None:
        eligible, reasons = self.evaluate_merge(
            pr, eligible_reviewers, merge_strategy
        )

        if not eligible:
            raise RuntimeError("Merge blocked: " + " ".join(reasons))

        pr.state = PullRequestState.MERGED


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def print_review_cost(pr: PullRequest) -> None:
    changed_file_factor = max(1, pr.changed_files)
    estimated_minutes = max(
        pr.estimated_review_minutes,
        changed_file_factor * 4,
    )

    print(
        f"PR #{pr.number}: {pr.changed_files} changed files, "
        f"estimated review effort: {estimated_minutes} minutes"
    )


def main() -> None:
    protection = BranchProtection(
        required_reviews=2,
        required_status_checks={"unit-tests", "security-scan"},
        dismiss_stale_approvals=True,
        require_conversation_resolution=True,
        restrict_direct_push=True,
        allow_force_push=False,
        require_linear_history=True,
        allowed_merge_strategies={MergeStrategy.SQUASH},
    )

    workflow = RepositoryWorkflow(protection)

    pr = PullRequest(
        number=142,
        source_branch="feature/resource-review",
        target_branch="main",
        title="Review repository cost and engineering resources",
        estimated_review_minutes=35,
    )

    pr.add_commit(
        Commit(
            sha="a123456789",
            message="Add resource-cost review workflow",
            changed_files=8,
            additions=240,
            deletions=35,
        )
    )
    pr.add_commit(
        Commit(
            sha="b123456789",
            message="Add governance validation",
            changed_files=4,
            additions=95,
            deletions=10,
        )
    )

    pr.request_review("alice")
    pr.request_review("bob")

    pr.submit_review(
        Review(
            reviewer="alice",
            state=ReviewState.APPROVED,
            submitted_at=utc_now(),
            comment_count=2,
        )
    )

    pr.submit_review(
        Review(
            reviewer="bob",
            state=ReviewState.CHANGES_REQUESTED,
            submitted_at=utc_now(),
            comment_count=3,
        )
    )

    pr.checks.extend(
        [
            StatusCheck("unit-tests", True, True, utc_now()),
            StatusCheck("security-scan", True, True, utc_now()),
        ]
    )

    pr.unresolved_conversations = 0

    eligible, reasons = workflow.evaluate_merge(
        pr,
        eligible_reviewers={"alice", "bob", "carol"},
        merge_strategy=MergeStrategy.SQUASH,
    )

    print_review_cost(pr)
    print(f"Merge eligible: {eligible}")

    if reasons:
        print("Blocking conditions:")
        for reason in reasons:
            print(f"- {reason}")

    # Bob resolves the requested changes by submitting a new approval.
    pr.submit_review(
        Review(
            reviewer="bob",
            state=ReviewState.APPROVED,
            submitted_at=utc_now(),
            comment_count=1,
        )
    )

    eligible, reasons = workflow.evaluate_merge(
        pr,
        eligible_reviewers={"alice", "bob", "carol"},
        merge_strategy=MergeStrategy.SQUASH,
    )

    print(f"\nAfter review update, merge eligible: {eligible}")

    if eligible:
        workflow.merge(
            pr,
            eligible_reviewers={"alice", "bob", "carol"},
            merge_strategy=MergeStrategy.SQUASH,
        )
        print(f"PR #{pr.number} merged using squash strategy.")
    else:
        for reason in reasons:
            print(f"- {reason}")

    # A closed PR can be reopened, preserving its review history.
    pr.close()
    print(f"PR state after closure: {pr.state.value}")
    pr.reopen()
    print(f"PR state after reopening: {pr.state.value}")

    # A base-branch update can invalidate approval eligibility when the
    # repository policy dismisses stale approvals.
    pr.update_after_base_change(conflicts=False)
    print(
        "Base branch changed; approvals must be re-evaluated before merging."
    )


if __name__ == "__main__":
    main()
