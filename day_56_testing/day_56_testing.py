#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


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


class CheckState(Enum):
    PASSING = "passing"
    FAILING = "failing"
    PENDING = "pending"


class MergeStrategy(Enum):
    MERGE = "merge"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass
class Commit:
    sha: str
    message: str
    author: str


@dataclass
class ReviewComment:
    comment_id: int
    reviewer: str
    body: str
    resolved: bool = False


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    commit_sha: str
    comments: List[ReviewComment] = field(default_factory=list)


@dataclass
class StatusCheck:
    name: str
    state: CheckState
    required: bool = True


@dataclass
class BranchProtection:
    required_approvals: int = 2
    required_checks: Set[str] = field(default_factory=set)
    require_conversations_resolved: bool = True
    restrict_direct_push: bool = True
    restrict_force_push: bool = True
    restrict_deletion: bool = True
    require_linear_history: bool = False
    allow_admin_bypass: bool = False


@dataclass
class Branch:
    name: str
    protected: bool = False
    head_sha: str = ""
    commits: List[Commit] = field(default_factory=list)


@dataclass
class Repository:
    name: str
    branches: Dict[str, Branch]
    reviewers: Set[str]
    protection: BranchProtection


@dataclass
class PullRequest:
    number: int
    author: str
    source_branch: str
    target_branch: str
    title: str
    state: PullRequestState = PullRequestState.OPEN
    draft: bool = False
    commits: List[Commit] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    checks: List[StatusCheck] = field(default_factory=list)
    conversations: List[ReviewComment] = field(default_factory=list)
    base_head_at_open: str = ""


class WorkflowError(Exception):
    pass


class RepositoryWorkflow:
    def __init__(self, repository: Repository):
        self.repository = repository
        self.pull_requests: Dict[int, PullRequest] = {}

    def create_pull_request(
        self,
        number: int,
        author: str,
        source: str,
        target: str,
        title: str,
        draft: bool = False,
    ) -> PullRequest:
        if number in self.pull_requests:
            raise WorkflowError("Pull Request number already exists.")
        if source not in self.repository.branches:
            raise WorkflowError("Source branch does not exist.")
        if target not in self.repository.branches:
            raise WorkflowError("Target branch does not exist.")
        if source == target:
            raise WorkflowError("Source and target branches must differ.")

        target_branch = self.repository.branches[target]

        pr = PullRequest(
            number=number,
            author=author,
            source_branch=source,
            target_branch=target,
            title=title.strip(),
            draft=draft,
            base_head_at_open=target_branch.head_sha,
        )

        if not pr.title:
            raise WorkflowError("Pull Request title cannot be empty.")

        self.pull_requests[number] = pr
        return pr

    def add_commit(self, pr_number: int, commit: Commit) -> None:
        pr = self._get_pr(pr_number)

        if pr.state != PullRequestState.OPEN:
            raise WorkflowError("Commits can only be added to an open Pull Request.")

        if not commit.sha or len(commit.sha) < 7:
            raise WorkflowError("Commit SHA is invalid.")

        if any(existing.sha == commit.sha for existing in pr.commits):
            raise WorkflowError("Duplicate commit.")

        pr.commits.append(commit)

        source_branch = self.repository.branches[pr.source_branch]
        source_branch.commits.append(commit)
        source_branch.head_sha = commit.sha

    def synchronize_base(self, pr_number: int, new_base_sha: str) -> None:
        pr = self._get_pr(pr_number)

        if pr.state != PullRequestState.OPEN:
            raise WorkflowError("Only open Pull Requests can be synchronized.")

        if not new_base_sha:
            raise WorkflowError("Base SHA cannot be empty.")

        pr.base_head_at_open = new_base_sha

        for review in pr.reviews:
            if review.state == ReviewState.APPROVED:
                review.state = ReviewState.DISMISSED

    def add_review(
        self,
        pr_number: int,
        reviewer: str,
        state: ReviewState,
        commit_sha: str,
    ) -> None:
        pr = self._get_pr(pr_number)

        if pr.state != PullRequestState.OPEN:
            raise WorkflowError("Reviews require an open Pull Request.")

        if reviewer == pr.author:
            raise WorkflowError("Self-approval is not allowed.")

        if reviewer not in self.repository.reviewers:
            raise WorkflowError("Reviewer is not eligible.")

        if not commit_sha:
            raise WorkflowError("Review must reference a commit.")

        review = Review(
            reviewer=reviewer,
            state=state,
            commit_sha=commit_sha,
        )
        pr.reviews.append(review)

    def add_conversation(
        self,
        pr_number: int,
        reviewer: str,
        body: str,
    ) -> int:
        pr = self._get_pr(pr_number)

        if not body.strip():
            raise WorkflowError("Conversation text cannot be empty.")

        comment_id = len(pr.conversations) + 1
        comment = ReviewComment(
            comment_id=comment_id,
            reviewer=reviewer,
            body=body.strip(),
        )
        pr.conversations.append(comment)
        return comment_id

    def resolve_conversation(self, pr_number: int, comment_id: int) -> None:
        pr = self._get_pr(pr_number)

        for comment in pr.conversations:
            if comment.comment_id == comment_id:
                comment.resolved = True
                return

        raise WorkflowError("Conversation not found.")

    def set_status(self, pr_number: int, name: str, state: CheckState) -> None:
        pr = self._get_pr(pr_number)

        if not name.strip():
            raise WorkflowError("Status check name cannot be empty.")

        for check in pr.checks:
            if check.name == name:
                check.state = state
                return

        pr.checks.append(StatusCheck(name=name, state=state))

    def publish(self, pr_number: int) -> None:
        pr = self._get_pr(pr_number)

        if not pr.draft:
            return

        pr.draft = False

    def eligibility(self, pr_number: int) -> tuple[bool, List[str]]:
        pr = self._get_pr(pr_number)
        policy = self.repository.protection
        reasons: List[str] = []

        if pr.state != PullRequestState.OPEN:
            reasons.append("Pull Request is not open.")

        if pr.draft:
            reasons.append("Pull Request is still a draft.")

        if not pr.commits:
            reasons.append("Pull Request contains no commits.")

        if not pr.reviews:
            reasons.append("No reviews have been submitted.")

        if any(
            review.state == ReviewState.CHANGES_REQUESTED
            for review in pr.reviews
        ):
            reasons.append("At least one reviewer requested changes.")

        latest_approved: Dict[str, Review] = {}

        for review in pr.reviews:
            if review.state == ReviewState.APPROVED:
                latest_approved[review.reviewer] = review

        if len(latest_approved) < policy.required_approvals:
            reasons.append(
                f"At least {policy.required_approvals} eligible approvals are required."
            )

        for check in pr.checks:
            if check.name in policy.required_checks and check.state != CheckState.PASSING:
                reasons.append(f"Required check '{check.name}' is not passing.")

        existing_check_names = {check.name for check in pr.checks}

        for required_check in policy.required_checks:
            if required_check not in existing_check_names:
                reasons.append(f"Required check '{required_check}' is missing.")

        if policy.require_conversations_resolved:
            unresolved = [
                c for c in pr.conversations if not c.resolved
            ]
            if unresolved:
                reasons.append("Unresolved review conversations remain.")

        target = self.repository.branches[pr.target_branch]

        if pr.base_head_at_open != target.head_sha:
            reasons.append("Pull Request base branch is out of date.")

        return not reasons, reasons

    def merge(
        self,
        pr_number: int,
        strategy: MergeStrategy = MergeStrategy.SQUASH,
    ) -> str:
        eligible, reasons = self.eligibility(pr_number)

        if not eligible:
            raise WorkflowError("Merge blocked: " + "; ".join(reasons))

        pr = self._get_pr(pr_number)
        target = self.repository.branches[pr.target_branch]

        if strategy == MergeStrategy.SQUASH:
            merge_sha = f"squash-{pr.number:04d}"
        elif strategy == MergeStrategy.MERGE:
            merge_sha = f"merge-{pr.number:04d}"
        else:
            merge_sha = f"rebase-{pr.number:04d}"

        target.head_sha = merge_sha
        target.commits.append(
            Commit(
                sha=merge_sha,
                message=f"Merge PR #{pr.number}: {pr.title}",
                author=pr.author,
            )
        )

        pr.state = PullRequestState.MERGED
        return merge_sha

    def close(self, pr_number: int) -> None:
        pr = self._get_pr(pr_number)

        if pr.state == PullRequestState.MERGED:
            raise WorkflowError("A merged Pull Request cannot be closed again.")

        pr.state = PullRequestState.CLOSED

    def reopen(self, pr_number: int) -> None:
        pr = self._get_pr(pr_number)

        if pr.state != PullRequestState.CLOSED:
            raise WorkflowError("Only closed Pull Requests can be reopened.")

        pr.state = PullRequestState.OPEN

    def _get_pr(self, number: int) -> PullRequest:
        if number not in self.pull_requests:
            raise WorkflowError(f"Pull Request #{number} does not exist.")
        return self.pull_requests[number]


def run_demo() -> None:
    protection = BranchProtection(
        required_approvals=2,
        required_checks={"unit-tests", "security-scan"},
        require_conversations_resolved=True,
        restrict_direct_push=True,
        restrict_force_push=True,
        restrict_deletion=True,
        require_linear_history=True,
        allow_admin_bypass=False,
    )

    repository = Repository(
        name="payments-service",
        branches={
            "main": Branch(
                name="main",
                protected=True,
                head_sha="base001",
            ),
            "feature/refund-validation": Branch(
                name="feature/refund-validation",
                head_sha="feature000",
            ),
        },
        reviewers={"alice", "bob", "carol"},
        protection=protection,
    )

    workflow = RepositoryWorkflow(repository)

    pr = workflow.create_pull_request(
        number=42,
        author="developer",
        source="feature/refund-validation",
        target="main",
        title="Validate refund requests",
        draft=True,
    )

    workflow.add_commit(
        pr.number,
        Commit(
            sha="abc1234567",
            message="Add refund validation",
            author="developer",
        ),
    )

    workflow.add_conversation(
        pr.number,
        "alice",
        "Please add a boundary test for zero-value refunds.",
    )

    workflow.set_status(pr.number, "unit-tests", CheckState.PASSING)
    workflow.set_status(pr.number, "security-scan", CheckState.PASSING)

    workflow.publish(pr.number)

    eligible, reasons = workflow.eligibility(pr.number)

    print("Initial merge eligibility:", eligible)
    for reason in reasons:
        print("  BLOCKED:", reason)

    workflow.add_review(
        pr.number,
        "alice",
        ReviewState.APPROVED,
        "abc1234567",
    )

    workflow.add_review(
        pr.number,
        "bob",
        ReviewState.APPROVED,
        "abc1234567",
    )

    workflow.resolve_conversation(pr.number, 1)

    eligible, reasons = workflow.eligibility(pr.number)

    print("\nAfter approvals and resolution:")
    print("Merge eligible:", eligible)

    if eligible:
        merge_sha = workflow.merge(pr.number, MergeStrategy.SQUASH)
        print("Merged with commit:", merge_sha)

    print("Final PR state:", pr.state.value)
    print("Protected branch head:", repository.branches["main"].head_sha)

    # A closed Pull Request can be reopened, but a merged one cannot.
    try:
        workflow.reopen(pr.number)
    except WorkflowError as exc:
        print("Expected failure:", exc)


if __name__ == "__main__":
    run_demo()
