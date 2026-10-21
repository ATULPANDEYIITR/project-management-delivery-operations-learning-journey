from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


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
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class MergeStrategy(Enum):
    MERGE_COMMIT = "merge_commit"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass
class Commit:
    sha: str
    message: str
    author: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    commit_sha: str
    comment_count: int = 0
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StatusCheck:
    name: str
    state: CheckState
    commit_sha: str


@dataclass
class BranchProtection:
    branch: str
    required_reviews: int = 1
    required_checks: Set[str] = field(default_factory=set)
    dismiss_stale_reviews: bool = True
    require_conversation_resolution: bool = True
    restrict_direct_push: bool = True
    allow_force_push: bool = False
    allow_deletion: bool = False
    require_linear_history: bool = False
    allowed_merge_strategies: Set[MergeStrategy] = field(
        default_factory=lambda: {
            MergeStrategy.MERGE_COMMIT,
            MergeStrategy.SQUASH,
            MergeStrategy.REBASE,
        }
    )
    bypass_users: Set[str] = field(default_factory=set)


@dataclass
class PullRequest:
    number: int
    title: str
    source_branch: str
    target_branch: str
    author: str
    state: PRState = PRState.OPEN
    commits: List[Commit] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    checks: List[StatusCheck] = field(default_factory=list)
    unresolved_conversations: int = 0
    merge_conflicts: bool = False
    merge_strategy: MergeStrategy = MergeStrategy.SQUASH
    base_sha_at_creation: str = ""
    current_base_sha: str = ""
    closed_at: Optional[datetime] = None

    def latest_commit(self) -> Optional[Commit]:
        return self.commits[-1] if self.commits else None


class Repository:
    def __init__(self, name: str) -> None:
        self.name = name
        self.branches: Dict[str, str] = {}
        self.protections: Dict[str, BranchProtection] = {}
        self.pull_requests: Dict[int, PullRequest] = {}
        self.next_pr_number = 1

    def create_branch(self, name: str, base_sha: str) -> None:
        if not name.strip():
            raise ValueError("Branch name cannot be empty.")
        if name in self.branches:
            raise ValueError(f"Branch already exists: {name}")
        self.branches[name] = base_sha

    def update_branch(self, name: str, sha: str) -> None:
        if name not in self.branches:
            raise KeyError(f"Unknown branch: {name}")
        if not sha.strip():
            raise ValueError("Commit SHA cannot be empty.")
        self.branches[name] = sha

    def protect_branch(self, policy: BranchProtection) -> None:
        if policy.branch not in self.branches:
            raise KeyError(f"Unknown branch: {policy.branch}")
        if policy.required_reviews < 0:
            raise ValueError("Required reviews cannot be negative.")
        self.protections[policy.branch] = policy

    def create_pull_request(
        self,
        title: str,
        source_branch: str,
        target_branch: str,
        author: str,
        draft: bool = False,
    ) -> PullRequest:
        if source_branch not in self.branches:
            raise KeyError(f"Unknown source branch: {source_branch}")
        if target_branch not in self.branches:
            raise KeyError(f"Unknown target branch: {target_branch}")
        if source_branch == target_branch:
            raise ValueError("Source and target branches must differ.")
        if not title.strip():
            raise ValueError("Pull Request title cannot be empty.")
        if not author.strip():
            raise ValueError("Pull Request author cannot be empty.")

        number = self.next_pr_number
        self.next_pr_number += 1

        state = PRState.DRAFT if draft else PRState.OPEN
        base_sha = self.branches[target_branch]

        pr = PullRequest(
            number=number,
            title=title,
            source_branch=source_branch,
            target_branch=target_branch,
            author=author,
            state=state,
            base_sha_at_creation=base_sha,
            current_base_sha=base_sha,
        )
        self.pull_requests[number] = pr
        return pr

    def add_commit(self, pr_number: int, commit: Commit) -> None:
        pr = self._get_pr(pr_number)

        if pr.state not in {PRState.DRAFT, PRState.OPEN}:
            raise ValueError("Commits cannot be added to a closed or merged Pull Request.")

        if not commit.sha or not commit.message.strip():
            raise ValueError("Commit SHA and message are required.")

        pr.commits.append(commit)
        self.update_branch(pr.source_branch, commit.sha)

        # New commits may invalidate approvals and checks that belonged
        # to the previous commit.
        if pr.commits:
            latest_sha = pr.commits[-1].sha
            pr.checks = [
                check
                for check in pr.checks
                if check.commit_sha == latest_sha
            ]

    def mark_ready(self, pr_number: int) -> None:
        pr = self._get_pr(pr_number)
        if pr.state != PRState.DRAFT:
            raise ValueError("Only draft Pull Requests can be marked ready.")
        pr.state = PRState.OPEN

    def request_review(self, pr_number: int, reviewer: str) -> None:
        pr = self._get_pr(pr_number)
        if pr.state != PRState.OPEN:
            raise ValueError("Reviews can only be requested on open Pull Requests.")
        if reviewer == pr.author:
            raise ValueError("Authors cannot be their own reviewer.")

    def submit_review(
        self,
        pr_number: int,
        reviewer: str,
        state: ReviewState,
        comment_count: int = 0,
    ) -> None:
        pr = self._get_pr(pr_number)

        if pr.state != PRState.OPEN:
            raise ValueError("Reviews can only be submitted on open Pull Requests.")
        if reviewer == pr.author:
            raise ValueError("Authors cannot approve their own Pull Request.")
        if comment_count < 0:
            raise ValueError("Comment count cannot be negative.")

        latest = pr.latest_commit()
        if latest is None:
            raise ValueError("A Pull Request must contain at least one commit before review.")

        # A review is tied to the exact commit it evaluated.
        pr.reviews.append(
            Review(
                reviewer=reviewer,
                state=state,
                commit_sha=latest.sha,
                comment_count=comment_count,
            )
        )

    def set_check(
        self,
        pr_number: int,
        check_name: str,
        state: CheckState,
    ) -> None:
        pr = self._get_pr(pr_number)
        latest = pr.latest_commit()

        if latest is None:
            raise ValueError("Status checks require a commit.")
        if not check_name.strip():
            raise ValueError("Status check name cannot be empty.")

        pr.checks = [
            check
            for check in pr.checks
            if check.name != check_name
        ]
        pr.checks.append(
            StatusCheck(
                name=check_name,
                state=state,
                commit_sha=latest.sha,
            )
        )

    def synchronize_base(self, pr_number: int, new_base_sha: str) -> None:
        pr = self._get_pr(pr_number)

        if pr.state not in {PRState.DRAFT, PRState.OPEN}:
            raise ValueError("Only active Pull Requests can be synchronized.")

        pr.current_base_sha = new_base_sha

        # In a real Git implementation, conflict detection would compare
        # the actual commit graph. Here it is represented explicitly.
        pr.merge_conflicts = new_base_sha != pr.base_sha_at_creation

        if pr.merge_conflicts:
            pr.unresolved_conversations += 1

        policy = self.protections.get(pr.target_branch)
        if policy and policy.dismiss_stale_reviews:
            pr.reviews = [
                review
                for review in pr.reviews
                if review.commit_sha == pr.latest_commit().sha
            ]

    def set_merge_conflicts(self, pr_number: int, conflicts: bool) -> None:
        pr = self._get_pr(pr_number)
        pr.merge_conflicts = conflicts

    def add_conversation(self, pr_number: int) -> None:
        pr = self._get_pr(pr_number)
        pr.unresolved_conversations += 1

    def resolve_conversation(self, pr_number: int) -> None:
        pr = self._get_pr(pr_number)
        if pr.unresolved_conversations == 0:
            raise ValueError("There are no unresolved conversations.")
        pr.unresolved_conversations -= 1

    def evaluate_merge(self, pr_number: int, actor: str) -> Tuple[bool, List[str]]:
        pr = self._get_pr(pr_number)
        reasons: List[str] = []

        if pr.state != PRState.OPEN:
            reasons.append("Pull Request is not open.")

        if not pr.commits:
            reasons.append("Pull Request has no commits.")

        policy = self.protections.get(pr.target_branch)

        if policy is None:
            reasons.append("Target branch has no branch-protection policy.")
            return False, reasons

        if actor in policy.bypass_users:
            return True, ["Merge permitted through configured governance bypass."]

        if pr.merge_conflicts:
            reasons.append("Merge conflicts must be resolved.")

        if pr.merge_strategy not in policy.allowed_merge_strategies:
            reasons.append(
                f"Merge strategy {pr.merge_strategy.value} is not permitted."
            )

        latest = pr.latest_commit()
        assert latest is not None

        approvals: Dict[str, Review] = {}
        for review in pr.reviews:
            if review.commit_sha != latest.sha:
                continue
            if review.state == ReviewState.APPROVED:
                approvals[review.reviewer] = review
            elif review.state == ReviewState.CHANGES_REQUESTED:
                approvals.pop(review.reviewer, None)

        if len(approvals) < policy.required_reviews:
            reasons.append(
                f"At least {policy.required_reviews} current approval(s) required; "
                f"found {len(approvals)}."
            )

        checks_by_name = {
            check.name: check
            for check in pr.checks
            if check.commit_sha == latest.sha
        }

        for required in policy.required_checks:
            check = checks_by_name.get(required)
            if check is None:
                reasons.append(f"Required status check is missing: {required}.")
            elif check.state != CheckState.PASSED:
                reasons.append(
                    f"Required status check has not passed: {required}."
                )

        if policy.require_conversation_resolution and pr.unresolved_conversations:
            reasons.append(
                f"{pr.unresolved_conversations} conversation(s) remain unresolved."
            )

        if policy.require_linear_history and pr.merge_strategy == MergeStrategy.MERGE_COMMIT:
            reasons.append("Linear-history policy does not permit a merge commit.")

        return not reasons, reasons

    def merge(self, pr_number: int, actor: str) -> None:
        allowed, reasons = self.evaluate_merge(pr_number, actor)

        if not allowed:
            raise PermissionError("Merge blocked: " + " ".join(reasons))

        pr = self._get_pr(pr_number)
        latest = pr.latest_commit()
        assert latest is not None

        # The resulting SHA is deliberately deterministic for this simulation.
        merge_sha = (
            f"merge-{pr.number}-"
            f"{latest.sha[:8]}-"
            f"{pr.merge_strategy.value}"
        )
        self.branches[pr.target_branch] = merge_sha
        pr.state = PRState.MERGED
        pr.closed_at = datetime.now(timezone.utc)

    def close(self, pr_number: int) -> None:
        pr = self._get_pr(pr_number)
        if pr.state == PRState.MERGED:
            raise ValueError("A merged Pull Request cannot be closed again.")
        pr.state = PRState.CLOSED
        pr.closed_at = datetime.now(timezone.utc)

    def reopen(self, pr_number: int) -> None:
        pr = self._get_pr(pr_number)
        if pr.state != PRState.CLOSED:
            raise ValueError("Only closed Pull Requests can be reopened.")
        pr.state = PRState.OPEN
        pr.closed_at = None

    def _get_pr(self, number: int) -> PullRequest:
        if number not in self.pull_requests:
            raise KeyError(f"Unknown Pull Request: {number}")
        return self.pull_requests[number]


def print_evaluation(repo: Repository, pr_number: int, actor: str) -> None:
    allowed, reasons = repo.evaluate_merge(pr_number, actor)
    print(f"PR #{pr_number}: {'MERGEABLE' if allowed else 'BLOCKED'}")
    for reason in reasons:
        print(f"  - {reason}")


def main() -> None:
    repo = Repository("payments-platform")

    repo.branches["main"] = "base-100"
    repo.create_branch("feature/payment-validation", "base-100")

    repo.protect_branch(
        BranchProtection(
            branch="main",
            required_reviews=2,
            required_checks={
                "unit-tests",
                "security-scan",
            },
            dismiss_stale_reviews=True,
            require_conversation_resolution=True,
            restrict_direct_push=True,
            allow_force_push=False,
            allow_deletion=False,
            require_linear_history=True,
            allowed_merge_strategies={
                MergeStrategy.SQUASH,
                MergeStrategy.REBASE,
            },
        )
    )

    pr = repo.create_pull_request(
        title="Validate high-value payment requests",
        source_branch="feature/payment-validation",
        target_branch="main",
        author="alice",
        draft=True,
    )

    repo.add_commit(
        pr.number,
        Commit(
            sha="a1b2c3d4e5",
            message="Add payment amount validation",
            author="alice",
        ),
    )

    repo.mark_ready(pr.number)
    repo.request_review(pr.number, "bob")
    repo.request_review(pr.number, "carol")

    repo.submit_review(
        pr.number,
        "bob",
        ReviewState.APPROVED,
        comment_count=2,
    )
    repo.submit_review(
        pr.number,
        "carol",
        ReviewState.APPROVED,
        comment_count=1,
    )

    repo.set_check(pr.number, "unit-tests", CheckState.PASSED)
    repo.set_check(pr.number, "security-scan", CheckState.PASSED)

    repo.add_conversation(pr.number)
    print_evaluation(repo, pr.number, "release-manager")

    repo.resolve_conversation(pr.number)
    print_evaluation(repo, pr.number, "release-manager")

    repo.merge(pr.number, "release-manager")

    print(f"Final PR state: {pr.state.value}")
    print(f"main now points to: {repo.branches['main']}")

    # Demonstrate a stale approval after a new commit.
    repo.create_branch("feature/audit-log", repo.branches["main"])
    second = repo.create_pull_request(
        title="Add immutable audit logging",
        source_branch="feature/audit-log",
        target_branch="main",
        author="diana",
    )

    repo.add_commit(
        second.number,
        Commit("f6e7d8c9b0", "Add audit event model", "diana"),
    )
    repo.submit_review(second.number, "erin", ReviewState.APPROVED)
    repo.submit_review(second.number, "frank", ReviewState.APPROVED)
    repo.set_check(second.number, "unit-tests", CheckState.PASSED)
    repo.set_check(second.number, "security-scan", CheckState.PASSED)

    # The policy dismisses reviews that are not tied to the current commit.
    repo.add_commit(
        second.number,
        Commit("1122334455", "Handle audit persistence failure", "diana"),
    )
    repo.set_check(second.number, "unit-tests", CheckState.PASSED)
    repo.set_check(second.number, "security-scan", CheckState.PASSED)

    print_evaluation(repo, second.number, "release-manager")


if __name__ == "__main__":
    main()
