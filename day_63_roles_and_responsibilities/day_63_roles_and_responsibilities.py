from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


class PRState(Enum):
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


@dataclass(frozen=True)
class Person:
    username: str
    role: str
    teams: Set[str] = field(default_factory=set)


@dataclass
class Commit:
    sha: str
    message: str
    author: str


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    commit_sha: str
    comment_count: int = 0


@dataclass
class StatusCheck:
    name: str
    state: CheckState


@dataclass
class BranchProtection:
    required_reviews: int = 2
    required_checks: Set[str] = field(
        default_factory=lambda: {"ci", "security"}
    )
    require_conversation_resolution: bool = True
    require_linear_history: bool = True
    allow_force_push: bool = False
    allow_deletion: bool = False
    allow_direct_push: bool = False


@dataclass
class PullRequest:
    number: int
    title: str
    author: str
    source: str
    target: str
    state: PRState = PRState.OPEN
    draft: bool = False
    commits: List[Commit] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    checks: Dict[str, StatusCheck] = field(default_factory=dict)
    unresolved_conversations: int = 0
    mergeable: bool = True
    base_behind_by: int = 0

    def add_commit(self, commit: Commit) -> None:
        if self.state not in {PRState.OPEN, PRState.DRAFT}:
            raise ValueError("Commits cannot be added to a closed or merged PR.")
        self.commits.append(commit)

    def add_review(self, review: Review) -> None:
        if review.reviewer == self.author:
            raise ValueError("Authors cannot approve their own pull request.")
        if review.commit_sha not in {c.sha for c in self.commits}:
            raise ValueError("Review must reference a commit in the pull request.")
        self.reviews.append(review)


@dataclass
class Repository:
    name: str
    default_branch: str
    protected_branches: Dict[str, BranchProtection]
    members: Dict[str, Person]

    def validate_reviewer(self, reviewer: str, author: str) -> bool:
        person = self.members.get(reviewer)
        return bool(
            person
            and reviewer != author
            and (
                "maintainer" in person.teams
                or "reviewer" in person.teams
            )
        )

    def merge_eligibility(self, pr: PullRequest) -> tuple[bool, List[str]]:
        reasons: List[str] = []
        policy = self.protected_branches.get(pr.target)

        if pr.state != PRState.OPEN:
            reasons.append("Pull request is not open.")
        if pr.draft:
            reasons.append("Draft pull requests cannot be merged.")
        if not pr.commits:
            reasons.append("Pull request contains no commits.")
        if not pr.mergeable:
            reasons.append("Pull request has merge conflicts.")
        if policy is None:
            reasons.append("Target branch has no protection policy.")
            return False, reasons

        valid_reviews = [
            r for r in pr.reviews
            if r.state == ReviewState.APPROVED
            and self.validate_reviewer(r.reviewer, pr.author)
        ]

        # An approval applies to the commit it reviewed. A later commit
        # makes that approval stale for this simplified governance model.
        head_sha = pr.commits[-1].sha
        current_approvals = {
            r.reviewer for r in valid_reviews if r.commit_sha == head_sha
        }

        if len(current_approvals) < policy.required_reviews:
            reasons.append(
                f"Requires {policy.required_reviews} current approvals."
            )

        for check_name in policy.required_checks:
            check = pr.checks.get(check_name)
            if check is None or check.state != CheckState.PASSING:
                reasons.append(f"Required check '{check_name}' is not passing.")

        if policy.require_conversation_resolution and pr.unresolved_conversations:
            reasons.append("Unresolved review conversations remain.")

        if policy.require_linear_history and pr.base_behind_by > 0:
            reasons.append("Pull request must synchronize with the base branch.")

        return not reasons, reasons


def print_decision(pr: PullRequest, repository: Repository) -> None:
    eligible, reasons = repository.merge_eligibility(pr)
    print(f"PR #{pr.number}: {pr.title}")
    print("MERGE ELIGIBLE" if eligible else "MERGE BLOCKED")
    if reasons:
        for reason in reasons:
            print(f"  - {reason}")
    print()


def main() -> None:
    members = {
        "atul": Person("atul", "developer", {"developer"}),
        "maya": Person("maya", "senior reviewer", {"reviewer"}),
        "liam": Person("liam", "maintainer", {"maintainer"}),
        "nora": Person("nora", "reviewer", {"reviewer"}),
    }

    repository = Repository(
        name="payments-service",
        default_branch="main",
        protected_branches={
            "main": BranchProtection(
                required_reviews=2,
                required_checks={"ci", "security"},
                require_conversation_resolution=True,
                require_linear_history=True,
                allow_force_push=False,
                allow_deletion=False,
                allow_direct_push=False,
            )
        },
        members=members,
    )

    pr = PullRequest(
        number=142,
        title="Add transaction idempotency protection",
        author="atul",
        source="feature/idempotency",
        target="main",
    )

    first = Commit("a1b2c3d", "Add idempotency key validation", "atul")
    pr.add_commit(first)

    pr.checks = {
        "ci": StatusCheck("ci", CheckState.PASSING),
        "security": StatusCheck("security", CheckState.PASSING),
    }

    pr.add_review(Review("maya", ReviewState.APPROVED, first.sha))
    pr.add_review(Review("liam", ReviewState.APPROVED, first.sha))
    print_decision(pr, repository)

    # A new commit makes the previous approvals stale.
    second = Commit("d4e5f6g", "Handle duplicate transaction requests", "atul")
    pr.add_commit(second)
    print_decision(pr, repository)

    pr.add_review(Review("maya", ReviewState.APPROVED, second.sha))
    pr.add_review(Review("liam", ReviewState.APPROVED, second.sha))
    pr.unresolved_conversations = 1
    print_decision(pr, repository)

    pr.unresolved_conversations = 0
    pr.base_behind_by = 0
    print_decision(pr, repository)

    # Demonstrate reviewer and state validation.
    try:
        pr.add_review(Review("atul", ReviewState.APPROVED, second.sha))
    except ValueError as exc:
        print(f"Validation failure: {exc}")


if __name__ == "__main__":
    main()
