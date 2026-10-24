#!/usr/bin/env python3
"""Simulate pull requests, code reviews, approvals, and branch protection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class PullRequestState(str, Enum):
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"


class ReviewState(str, Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    DISMISSED = "dismissed"


class CheckState(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


@dataclass(frozen=True)
class Commit:
    commit_id: str
    message: str
    author: str

    def __post_init__(self) -> None:
        if not self.commit_id.strip() or not self.author.strip():
            raise ValueError("Commit ID and author are required.")


@dataclass
class Branch:
    name: str
    commits: list[Commit] = field(default_factory=list)
    protected: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Branch name cannot be empty.")

    @property
    def head(self) -> str | None:
        return self.commits[-1].commit_id if self.commits else None


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    commit_id: str
    submitted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    comments: list[str] = field(default_factory=list)


@dataclass
class StatusCheck:
    name: str
    state: CheckState
    commit_id: str


@dataclass(frozen=True)
class BranchProtection:
    required_approvals: int = 2
    required_checks: frozenset[str] = frozenset(
        {"unit-tests", "security-scan"}
    )
    require_conversations_resolved: bool = True
    require_linear_history: bool = True
    allow_direct_push: bool = False
    allow_force_push: bool = False
    allow_deletion: bool = False
    allow_admin_bypass: bool = False

    def __post_init__(self) -> None:
        if self.required_approvals < 0:
            raise ValueError("Required approvals cannot be negative.")


@dataclass
class PullRequest:
    number: int
    author: str
    source: Branch
    target: Branch
    protection: BranchProtection
    eligible_reviewers: frozenset[str]
    draft: bool = False
    state: PullRequestState = PullRequestState.OPEN
    reviews: list[Review] = field(default_factory=list)
    checks: list[StatusCheck] = field(default_factory=list)
    unresolved_conversations: set[str] = field(default_factory=set)
    base_head_at_creation: str | None = None
    merge_commit: Commit | None = None

    def __post_init__(self) -> None:
        if self.number <= 0:
            raise ValueError("Pull request number must be positive.")
        if not self.author.strip():
            raise ValueError("Pull request author is required.")
        if self.source.name == self.target.name:
            raise ValueError("Source and target branches must differ.")
        if self.author in self.eligible_reviewers:
            raise ValueError("The author cannot be their own eligible reviewer.")
        self.base_head_at_creation = self.target.head

    def _require_open(self) -> None:
        if self.state != PullRequestState.OPEN:
            raise RuntimeError("Operation requires an open pull request.")

    def add_commit(self, commit: Commit) -> None:
        self._require_open()
        if commit.author != self.author:
            raise ValueError("Only the PR author may update this source branch.")
        if self.source.head == commit.commit_id:
            raise ValueError("Duplicate commit at branch head.")
        self.source.commits.append(commit)

    def synchronize_base(self) -> None:
        self._require_open()
        self.base_head_at_creation = self.target.head

    def submit_review(self, review: Review) -> None:
        self._require_open()
        if self.draft:
            raise RuntimeError("Convert the draft to a ready PR before review.")
        if review.reviewer not in self.eligible_reviewers:
            raise ValueError("Reviewer is not eligible.")
        if review.reviewer == self.author:
            raise ValueError("Self-review is prohibited.")
        if review.commit_id != self.source.head:
            raise ValueError("Review must reference the current source HEAD.")
        if review.state == ReviewState.DISMISSED:
            raise ValueError("A dismissed review cannot be newly submitted.")
        self.reviews.append(review)

    def dismiss_review(self, reviewer: str) -> None:
        self._require_open()
        for review in reversed(self.reviews):
            if (
                review.reviewer == reviewer
                and review.state != ReviewState.DISMISSED
            ):
                review.state = ReviewState.DISMISSED
                return
        raise ValueError("No active review found for reviewer.")

    def set_check(self, name: str, state: CheckState) -> None:
        self._require_open()
        if not name.strip():
            raise ValueError("Check name cannot be empty.")
        # Retain only the latest result for each check on the current HEAD.
        self.checks = [
            check for check in self.checks
            if not (check.name == name and check.commit_id == self.source.head)
        ]
        self.checks.append(StatusCheck(name, state, self.source.head or ""))

    def resolve_conversation(self, conversation_id: str) -> None:
        self._require_open()
        if conversation_id not in self.unresolved_conversations:
            raise ValueError("Conversation is not unresolved.")
        self.unresolved_conversations.remove(conversation_id)

    def set_draft(self, draft: bool) -> None:
        self._require_open()
        self.draft = draft

    def effective_approvals(self) -> set[str]:
        """Use each reviewer's latest submitted review, excluding dismissed reviews."""
        latest: dict[str, Review] = {}
        for review in self.reviews:
            latest[review.reviewer] = review

        return {
            reviewer
            for reviewer, review in latest.items()
            if review.state == ReviewState.APPROVED
            and review.commit_id == self.source.head
        }

    def merge_blockers(self) -> list[str]:
        blockers: list[str] = []

        if self.state != PullRequestState.OPEN:
            blockers.append("Pull request is not open.")
            return blockers

        if self.draft:
            blockers.append("Pull request is still a draft.")

        if not self.source.commits:
            blockers.append("Source branch has no commits.")

        if self.base_head_at_creation != self.target.head:
            blockers.append("Target branch changed; synchronize and revalidate.")

        latest_reviews: dict[str, Review] = {}
        for review in self.reviews:
            latest_reviews[review.reviewer] = review

        for reviewer, review in latest_reviews.items():
            if (
                review.state == ReviewState.CHANGES_REQUESTED
                and review.commit_id == self.source.head
            ):
                blockers.append(f"{reviewer} requested changes.")
        approvals = self.effective_approvals()
        if len(approvals) < self.protection.required_approvals:
            blockers.append(
                f"Need {self.protection.required_approvals} current approvals; "
                f"have {len(approvals)}."
            )

        for name in sorted(self.protection.required_checks):
            matching = [
                check for check in self.checks
                if check.name == name and check.commit_id == self.source.head
            ]
            if not matching or matching[-1].state != CheckState.PASSED:
                blockers.append(f"Required check '{name}' has not passed.")

        if (
            self.protection.require_conversations_resolved
            and self.unresolved_conversations
        ):
            blockers.append(
                f"{len(self.unresolved_conversations)} unresolved conversation(s)."
            )

        if self.protection.require_linear_history:
            # This simulation models linear commits only; it has no merge graph.
            if any(not commit.commit_id.strip() for commit in self.source.commits):
                blockers.append("Invalid commit history.")

        return blockers

    def merge(self, merge_commit: Commit, actor: str) -> None:
        self._require_open()
        if actor not in self.eligible_reviewers and actor != self.author:
            raise ValueError("Actor is not authorized to merge this PR.")
        blockers = self.merge_blockers()
        if blockers:
            raise RuntimeError("Merge blocked: " + " ".join(blockers))
        if merge_commit.commit_id in {
            commit.commit_id for commit in self.target.commits
        }:
            raise ValueError("Merge commit already exists on target.")
        self.target.commits.append(merge_commit)
        self.merge_commit = merge_commit
        self.state = PullRequestState.MERGED

    def close(self) -> None:
        self._require_open()
        self.state = PullRequestState.CLOSED

    def reopen(self) -> None:
        if self.state != PullRequestState.CLOSED:
            raise RuntimeError("Only a closed, unmerged PR can be reopened.")
        self.state = PullRequestState.OPEN


def direct_push(
    branch: Branch,
    commit: Commit,
    protection: BranchProtection,
    actor_is_admin: bool = False,
) -> None:
    if branch.protected and not protection.allow_direct_push:
        if not (actor_is_admin and protection.allow_admin_bypass):
            raise PermissionError("Direct push is prohibited by branch protection.")
    branch.commits.append(commit)


def main() -> None:
    author = "developer"
    reviewers = frozenset({"reviewer-a", "reviewer-b", "maintainer"})
    protection = BranchProtection()

    main_branch = Branch(
        "main",
        [Commit("c100", "Initial release", "maintainer")],
        protected=True,
    )
    feature = Branch(
        "feature/input-validation",
        [Commit("c101", "Validate request fields", author)],
    )

    pr = PullRequest(
        number=42,
        author=author,
        source=feature,
        target=main_branch,
        protection=protection,
        eligible_reviewers=reviewers,
        draft=True,
    )

    pr.set_draft(False)
    pr.unresolved_conversations.add("conversation-1")

    pr.submit_review(
        Review("reviewer-a", ReviewState.APPROVED, "c101")
    )
    pr.submit_review(
        Review(
            "reviewer-b",
            ReviewState.CHANGES_REQUESTED,
            "c101",
            comments=["Reject malformed identifiers."],
        )
    )

    for name in ("unit-tests", "security-scan"):
        pr.set_check(name, CheckState.PASSED)

    print("Initial merge blockers:")
    for blocker in pr.merge_blockers():
        print(f"- {blocker}")

    # A new commit makes previous approvals stale under this policy.
    pr.add_commit(Commit("c102", "Reject malformed identifiers", author))
    print("\nAfter source update:")
    for blocker in pr.merge_blockers():
        print(f"- {blocker}")

    pr.submit_review(
        Review("reviewer-a", ReviewState.APPROVED, "c102")
    )
    pr.submit_review(
        Review("reviewer-b", ReviewState.APPROVED, "c102")
    )
    pr.set_check("unit-tests", CheckState.PASSED)
    pr.set_check("security-scan", CheckState.PASSED)
    pr.resolve_conversation("conversation-1")

    # The target may change independently, so its HEAD is rechecked.
    pr.synchronize_base()
    print("\nFinal merge blockers:", pr.merge_blockers())

    pr.merge(
        Commit("c103", "Merge input validation", "maintainer"),
        actor="maintainer",
    )
    print("Final PR state:", pr.state.value)
    print("Target HEAD:", main_branch.head)

    try:
        direct_push(
            main_branch,
            Commit("c104", "Unreviewed production change", author),
            protection,
        )
    except PermissionError as exc:
        print("Governance enforcement:", exc)

    assert pr.state == PullRequestState.MERGED
    assert main_branch.head == "c103"


if __name__ == "__main__":
    main()
