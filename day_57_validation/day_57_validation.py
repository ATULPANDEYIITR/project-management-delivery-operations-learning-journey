from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Set


class WorkItemState(Enum):
    DRAFT = "draft"
    OPEN = "open"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    MERGED = "merged"
    CLOSED = "closed"


class ReviewState(Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    DISMISSED = "dismissed"


class CheckState(Enum):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"


@dataclass(frozen=True)
class User:
    user_id: str
    name: str
    role: str


@dataclass
class Commit:
    commit_id: str
    message: str
    author_id: str
    created_at: datetime


@dataclass
class ReviewComment:
    comment_id: str
    reviewer_id: str
    text: str
    resolved: bool = False


@dataclass
class Review:
    review_id: str
    reviewer_id: str
    state: ReviewState
    submitted_at: datetime
    comments: List[ReviewComment] = field(default_factory=list)


@dataclass
class StatusCheck:
    name: str
    state: CheckState
    mandatory: bool = True


@dataclass
class BranchProtectionPolicy:
    required_reviews: int = 2
    required_status_checks: Set[str] = field(default_factory=set)
    restrict_direct_push: bool = True
    restrict_force_push: bool = True
    restrict_deletion: bool = True
    require_resolved_conversations: bool = True
    require_linear_history: bool = False
    allow_administrator_bypass: bool = False


@dataclass
class Branch:
    name: str
    protected: bool = False
    commit_ids: List[str] = field(default_factory=list)


@dataclass
class PullRequest:
    number: int
    title: str
    source_branch: str
    target_branch: str
    author_id: str
    state: WorkItemState = WorkItemState.OPEN
    draft: bool = False
    commits: List[Commit] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    status_checks: Dict[str, StatusCheck] = field(default_factory=dict)
    conversations_open: int = 0
    merge_conflicts: bool = False
    base_synchronized: bool = True
    approval_epoch: int = 0
    latest_commit_epoch: int = 0

    def add_commit(self, commit: Commit) -> None:
        if self.state in {WorkItemState.MERGED, WorkItemState.CLOSED}:
            raise ValueError("Cannot add commits to a completed Pull Request.")
        self.commits.append(commit)
        self.latest_commit_epoch += 1
        self.approval_epoch += 1
        self.state = WorkItemState.OPEN

    def request_review(self) -> None:
        if self.draft:
            raise ValueError("Draft Pull Requests cannot enter final review.")
        if not self.commits:
            raise ValueError("A Pull Request must contain at least one commit.")
        self.state = WorkItemState.IN_REVIEW

    def submit_review(self, review: Review) -> None:
        if review.reviewer_id == self.author_id:
            raise PermissionError("A contributor cannot approve their own Pull Request.")
        if self.state in {WorkItemState.MERGED, WorkItemState.CLOSED}:
            raise ValueError("Reviews cannot be submitted after completion.")
        self.reviews.append(review)
        if review.state == ReviewState.CHANGES_REQUESTED:
            self.state = WorkItemState.CHANGES_REQUESTED
        elif review.state == ReviewState.APPROVED:
            self.state = WorkItemState.APPROVED

    def resolve_conversation(self) -> None:
        if self.conversations_open > 0:
            self.conversations_open -= 1

    def synchronize_base(self) -> None:
        self.base_synchronized = True
        self.merge_conflicts = False
        self.approval_epoch += 1

    def mark_conflicted(self) -> None:
        self.merge_conflicts = True
        self.base_synchronized = False

    def successful_approvals(self) -> Set[str]:
        return {
            review.reviewer_id
            for review in self.reviews
            if review.state == ReviewState.APPROVED
        }


class GovernanceEngine:
    def __init__(self, users: Dict[str, User]):
        self.users = users

    def eligible_reviewers(self, pr: PullRequest) -> Set[str]:
        return {
            user_id
            for user_id, user in self.users.items()
            if user_id != pr.author_id
            and user.role in {"reviewer", "maintainer", "project_manager"}
        }

    def merge_eligibility(
        self,
        pr: PullRequest,
        target: Branch,
        policy: BranchProtectionPolicy,
    ) -> tuple[bool, List[str]]:
        reasons: List[str] = []

        if pr.state == WorkItemState.CLOSED:
            reasons.append("Pull Request is closed.")
        if pr.state == WorkItemState.MERGED:
            reasons.append("Pull Request is already merged.")
        if pr.draft:
            reasons.append("Pull Request is still a draft.")
        if not pr.commits:
            reasons.append("No proposed changes exist.")
        if pr.merge_conflicts:
            reasons.append("Source and target branches have merge conflicts.")
        if not pr.base_synchronized:
            reasons.append("Source branch is not synchronized with the target branch.")

        eligible = self.eligible_reviewers(pr)
        approvals = pr.successful_approvals() & eligible

        if len(approvals) < policy.required_reviews:
            reasons.append(
                f"At least {policy.required_reviews} eligible approval(s) are required."
            )

        for check_name in policy.required_status_checks:
            check = pr.status_checks.get(check_name)
            if check is None:
                reasons.append(f"Required status check '{check_name}' is missing.")
            elif check.state != CheckState.PASS:
                reasons.append(f"Required status check '{check_name}' has not passed.")

        if policy.require_resolved_conversations and pr.conversations_open:
            reasons.append("All review conversations must be resolved.")

        if target.protected and target.name == pr.target_branch:
            if pr.author_id not in self.users:
                reasons.append("Pull Request author is not a known repository user.")

        return not reasons, reasons

    def merge(
        self,
        pr: PullRequest,
        target: Branch,
        policy: BranchProtectionPolicy,
    ) -> None:
        allowed, reasons = self.merge_eligibility(pr, target, policy)
        if not allowed:
            raise RuntimeError("Merge blocked: " + " ".join(reasons))

        target.commit_ids.extend(commit.commit_id for commit in pr.commits)
        pr.state = WorkItemState.MERGED


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_demo_project() -> tuple[Dict[str, User], Branch, PullRequest, BranchProtectionPolicy]:
    users = {
        "u1": User("u1", "Project Lead", "project_manager"),
        "u2": User("u2", "Technical Reviewer", "reviewer"),
        "u3": User("u3", "Quality Reviewer", "reviewer"),
        "u4": User("u4", "Developer", "developer"),
    }

    main = Branch("main", protected=True)

    pr = PullRequest(
        number=42,
        title="Implement project risk dashboard",
        source_branch="feature/risk-dashboard",
        target_branch="main",
        author_id="u4",
    )

    pr.add_commit(
        Commit(
            commit_id="c101",
            message="Add risk aggregation workflow",
            author_id="u4",
            created_at=utc_now(),
        )
    )

    pr.request_review()

    pr.status_checks = {
        "unit-tests": StatusCheck("unit-tests", CheckState.PASS),
        "security-scan": StatusCheck("security-scan", CheckState.PASS),
        "project-validation": StatusCheck("project-validation", CheckState.PASS),
    }

    pr.reviews.extend(
        [
            Review(
                "r1",
                "u2",
                ReviewState.APPROVED,
                utc_now(),
                [ReviewComment("cm1", "u2", "Risk calculation is traceable.", True)],
            ),
            Review(
                "r2",
                "u3",
                ReviewState.APPROVED,
                utc_now(),
                [ReviewComment("cm2", "u3", "Validation evidence is sufficient.", True)],
            ),
        ]
    )

    policy = BranchProtectionPolicy(
        required_reviews=2,
        required_status_checks={
            "unit-tests",
            "security-scan",
            "project-validation",
        },
        restrict_direct_push=True,
        restrict_force_push=True,
        require_resolved_conversations=True,
    )

    return users, main, pr, policy


def main() -> None:
    users, main_branch, pr, policy = create_demo_project()
    engine = GovernanceEngine(users)

    allowed, reasons = engine.merge_eligibility(pr, main_branch, policy)

    print("Project Management Change-Control Simulation")
    print("=" * 48)
    print(f"PR #{pr.number}: {pr.title}")
    print(f"Source: {pr.source_branch}")
    print(f"Target: {pr.target_branch}")
    print(f"Eligible for merge: {allowed}")

    if reasons:
        for reason in reasons:
            print(f"- {reason}")
    else:
        engine.merge(pr, main_branch, policy)
        print(f"Final state: {pr.state.value}")
        print(f"Target branch commits: {len(main_branch.commit_ids)}")

    # Failure scenario: a new commit makes earlier approvals stale.
    second_pr = PullRequest(
        number=43,
        title="Update project cost controls",
        source_branch="feature/cost-controls",
        target_branch="main",
        author_id="u4",
    )
    second_pr.add_commit(
        Commit("c201", "Add cost threshold validation", "u4", utc_now())
    )
    second_pr.request_review()
    second_pr.status_checks = {
        "unit-tests": StatusCheck("unit-tests", CheckState.PASS),
        "security-scan": StatusCheck("security-scan", CheckState.PASS),
        "project-validation": StatusCheck("project-validation", CheckState.PASS),
    }
    second_pr.reviews.append(
        Review("r3", "u2", ReviewState.APPROVED, utc_now())
    )
    second_pr.add_commit(
        Commit("c202", "Fix boundary condition", "u4", utc_now())
    )

    allowed, reasons = engine.merge_eligibility(second_pr, main_branch, policy)
    print("\nStale Approval Scenario")
    print("-" * 25)
    print(f"Eligible for merge: {allowed}")
    for reason in reasons:
        print(f"- {reason}")

    assert not allowed
    assert second_pr.state == WorkItemState.OPEN


if __name__ == "__main__":
    main()
