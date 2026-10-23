from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Tuple


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
    author: str


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    commit_sha: str
    comments: List[str] = field(default_factory=list)
    dismissed: bool = False


@dataclass
class StatusCheck:
    name: str
    passed: bool
    commit_sha: str
    required: bool = True


@dataclass
class BranchProtection:
    required_reviews: int = 2
    require_conversation_resolution: bool = True
    required_status_checks: Set[str] = field(
        default_factory=lambda: {"tests", "security"}
    )
    allow_direct_push: bool = False
    allow_force_push: bool = False
    allow_deletion: bool = False
    require_linear_history: bool = False
    allow_admin_bypass: bool = False


@dataclass
class PullRequest:
    number: int
    title: str
    source_branch: str
    target_branch: str
    author: str
    state: PullRequestState = PullRequestState.DRAFT
    commits: List[Commit] = field(default_factory=list)
    reviewers_requested: Set[str] = field(default_factory=set)
    reviews: List[Review] = field(default_factory=list)
    checks: List[StatusCheck] = field(default_factory=list)
    unresolved_conversations: int = 0
    head_sha: str = ""

    def open(self) -> None:
        if self.state not in {PullRequestState.DRAFT, PullRequestState.CLOSED}:
            raise ValueError("Pull Request is not eligible to be opened.")
        self.state = PullRequestState.OPEN

    def close(self) -> None:
        if self.state == PullRequestState.MERGED:
            raise ValueError("A merged Pull Request cannot be closed.")
        self.state = PullRequestState.CLOSED

    def add_commit(self, commit: Commit) -> None:
        if self.state == PullRequestState.MERGED:
            raise ValueError("Cannot modify a merged Pull Request.")
        if any(existing.sha == commit.sha for existing in self.commits):
            raise ValueError("Duplicate commit SHA.")
        self.commits.append(commit)
        self.head_sha = commit.sha

        # New commits can invalidate approvals from older revisions.
        for review in self.reviews:
            if review.commit_sha != self.head_sha and review.state == ReviewState.APPROVED:
                review.dismissed = True

    def request_review(self, reviewer: str) -> None:
        if reviewer == self.author:
            raise ValueError("The author cannot be their own required reviewer.")
        self.reviewers_requested.add(reviewer)

    def add_review(
        self,
        reviewer: str,
        state: ReviewState,
        comments: List[str] | None = None,
    ) -> None:
        if self.state != PullRequestState.OPEN:
            raise ValueError("Reviews can only be submitted on an open Pull Request.")
        if reviewer == self.author:
            raise ValueError("Self-review is not permitted.")

        self.reviews.append(
            Review(
                reviewer=reviewer,
                state=state,
                commit_sha=self.head_sha,
                comments=comments or [],
            )
        )

    def add_check(self, name: str, passed: bool) -> None:
        self.checks = [
            check for check in self.checks
            if check.name != name
        ]
        self.checks.append(
            StatusCheck(name, passed, self.head_sha)
        )

    def resolve_conversation(self) -> None:
        if self.unresolved_conversations <= 0:
            raise ValueError("There are no unresolved conversations.")
        self.unresolved_conversations -= 1


class Repository:
    def __init__(self, name: str, protection: BranchProtection):
        self.name = name
        self.protection = protection
        self.pull_requests: Dict[int, PullRequest] = {}
        self.next_pr_number = 1

    def create_pull_request(
        self,
        title: str,
        source_branch: str,
        target_branch: str,
        author: str,
        draft: bool = True,
    ) -> PullRequest:
        if source_branch == target_branch:
            raise ValueError("Source and target branches must differ.")

        pr = PullRequest(
            number=self.next_pr_number,
            title=title,
            source_branch=source_branch,
            target_branch=target_branch,
            author=author,
            state=PullRequestState.DRAFT if draft else PullRequestState.OPEN,
        )
        self.pull_requests[pr.number] = pr
        self.next_pr_number += 1
        return pr

    def evaluate_merge(self, pr: PullRequest) -> Tuple[bool, List[str]]:
        failures: List[str] = []

        if pr.state != PullRequestState.OPEN:
            failures.append("Pull Request must be open.")

        if not pr.commits:
            failures.append("Pull Request contains no commits.")

        if not pr.head_sha:
            failures.append("Pull Request has no current head revision.")

        eligible_approvals = {
            review.reviewer
            for review in pr.reviews
            if (
                review.state == ReviewState.APPROVED
                and not review.dismissed
                and review.commit_sha == pr.head_sha
                and review.reviewer != pr.author
            )
        }

        if len(eligible_approvals) < self.protection.required_reviews:
            failures.append(
                f"At least {self.protection.required_reviews} current approval(s) required."
            )

        requested_changes = [
            review
            for review in pr.reviews
            if (
                review.state == ReviewState.CHANGES_REQUESTED
                and not review.dismissed
                and review.commit_sha == pr.head_sha
            )
        ]
        if requested_changes:
            failures.append("An active changes-requested review remains.")

        for check_name in self.protection.required_status_checks:
            matching = [
                check
                for check in pr.checks
                if check.name == check_name
                and check.commit_sha == pr.head_sha
            ]
            if not matching or not matching[-1].passed:
                failures.append(f"Required status check '{check_name}' has not passed.")

        if self.protection.require_conversation_resolution:
            if pr.unresolved_conversations > 0:
                failures.append("Unresolved review conversations remain.")

        return not failures, failures

    def merge(
        self,
        pr: PullRequest,
        strategy: MergeStrategy = MergeStrategy.SQUASH,
    ) -> str:
        eligible, failures = self.evaluate_merge(pr)
        if not eligible:
            raise RuntimeError("Merge blocked: " + "; ".join(failures))

        pr.state = PullRequestState.MERGED
        return (
            f"PR #{pr.number} merged into {pr.target_branch} "
            f"using {strategy.value} strategy."
        )

    def synchronize_base(self, pr: PullRequest, new_base_sha: str) -> None:
        if pr.state != PullRequestState.OPEN:
            raise ValueError("Only open Pull Requests can be synchronized.")

        # Synchronization represents bringing the target branch changes
        # into the feature branch. The resulting revision invalidates
        # previous approvals and status results.
        pr.head_sha = new_base_sha
        for review in pr.reviews:
            if review.state == ReviewState.APPROVED:
                review.dismissed = True
        for check in pr.checks:
            check.passed = False


def main() -> None:
    protection = BranchProtection(
        required_reviews=2,
        required_status_checks={"tests", "security"},
        require_conversation_resolution=True,
        allow_direct_push=False,
        allow_force_push=False,
        allow_deletion=False,
        require_linear_history=True,
    )

    repository = Repository("payments-service", protection)

    pr = repository.create_pull_request(
        title="Harden payment authorization",
        source_branch="feature/payment-policy",
        target_branch="main",
        author="alice",
        draft=True,
    )

    pr.add_commit(
        Commit(
            sha="a100",
            message="Add authorization policy",
            author="alice",
        )
    )

    pr.request_review("bob")
    pr.request_review("carol")
    pr.open()

    pr.add_review(
        "bob",
        ReviewState.APPROVED,
        ["Authorization rules are correctly isolated."],
    )

    pr.add_review(
        "carol",
        ReviewState.CHANGES_REQUESTED,
        ["Add a regression test for expired credentials."],
    )

    pr.unresolved_conversations = 1
    pr.add_check("tests", True)
    pr.add_check("security", True)

    eligible, failures = repository.evaluate_merge(pr)
    print("Initial merge eligibility:", eligible)
    for failure in failures:
        print(" -", failure)

    pr.add_commit(
        Commit(
            sha="a101",
            message="Add expired-credential regression test",
            author="alice",
        )
    )

    # The new revision makes the earlier approval stale.
    pr.add_review(
        "bob",
        ReviewState.APPROVED,
        ["Regression coverage is now present."],
    )
    pr.add_review(
        "carol",
        ReviewState.APPROVED,
        ["Requested change has been addressed."],
    )

    pr.resolve_conversation()
    pr.add_check("tests", True)
    pr.add_check("security", True)

    eligible, failures = repository.evaluate_merge(pr)
    print("\nAfter remediation:", eligible)
    for failure in failures:
        print(" -", failure)

    if eligible:
        print(repository.merge(pr, MergeStrategy.SQUASH))

    print("Final Pull Request state:", pr.state.value)


if __name__ == "__main__":
    main()
