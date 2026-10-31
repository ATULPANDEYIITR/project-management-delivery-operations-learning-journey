from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta


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


class ResourceType(Enum):
    ENGINEER = "engineer"
    REVIEWER = "reviewer"
    CI = "ci"


@dataclass(frozen=True)
class Resource:
    name: str
    resource_type: ResourceType
    capacity_hours: float
    hourly_cost: float


@dataclass
class Commit:
    sha: str
    message: str
    author: str
    created_at: datetime


@dataclass
class ReviewComment:
    reviewer: str
    file_path: str
    line: int
    body: str
    resolved: bool = False


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    submitted_at: datetime
    comments: List[ReviewComment] = field(default_factory=list)
    commit_sha: str = ""


@dataclass
class StatusCheck:
    name: str
    passed: bool
    required: bool
    duration_seconds: float


@dataclass
class BranchProtection:
    required_reviews: int
    required_checks: Set[str]
    require_conversation_resolution: bool
    require_linear_history: bool
    allow_force_push: bool = False
    allow_deletion: bool = False
    allow_direct_push: bool = False
    allow_bypass: bool = False


@dataclass
class PullRequest:
    number: int
    source_branch: str
    target_branch: str
    state: PRState
    author: str
    commits: List[Commit]
    reviews: List[Review] = field(default_factory=list)
    status_checks: List[StatusCheck] = field(default_factory=list)
    opened_at: datetime = field(default_factory=datetime.utcnow)
    draft: bool = False
    conversations_open: int = 0
    target_head_sha: str = ""
    merged_sha: str | None = None
    base_changed_since_review: bool = False


class ResourceManager:
    """Tracks project capacity and prevents assignments beyond available hours."""

    def __init__(self, resources: List[Resource]) -> None:
        self.resources: Dict[str, Resource] = {r.name: r for r in resources}
        self.used_hours: Dict[str, float] = {r.name: 0.0 for r in resources}

    def allocate(self, name: str, hours: float) -> None:
        if name not in self.resources:
            raise ValueError(f"Unknown resource: {name}")
        if hours <= 0:
            raise ValueError("Allocation hours must be positive")

        resource = self.resources[name]
        remaining = resource.capacity_hours - self.used_hours[name]
        if hours > remaining:
            raise ValueError(
                f"{name} has only {remaining:.1f} hours remaining; "
                f"requested {hours:.1f}"
            )

        self.used_hours[name] += hours

    def remaining_hours(self, name: str) -> float:
        if name not in self.resources:
            raise ValueError(f"Unknown resource: {name}")
        return self.resources[name].capacity_hours - self.used_hours[name]

    def utilization(self, name: str) -> float:
        resource = self.resources[name]
        return self.used_hours[name] / resource.capacity_hours

    def project_cost(self) -> float:
        return sum(
            self.used_hours[name] * resource.hourly_cost
            for name, resource in self.resources.items()
        )

    def report(self) -> List[Tuple[str, float, float, float]]:
        return [
            (
                name,
                resource.capacity_hours,
                self.used_hours[name],
                self.utilization(name),
            )
            for name, resource in self.resources.items()
        ]


class Repository:
    def __init__(
        self,
        name: str,
        default_branch: str,
        protection: BranchProtection,
    ) -> None:
        self.name = name
        self.default_branch = default_branch
        self.protection = protection
        self.branches: Dict[str, List[Commit]] = {default_branch: []}
        self.pull_requests: Dict[int, PullRequest] = {}
        self.next_pr_number = 1

    def create_branch(self, name: str, base_branch: str) -> None:
        if name in self.branches:
            raise ValueError(f"Branch already exists: {name}")
        if base_branch not in self.branches:
            raise ValueError(f"Base branch does not exist: {base_branch}")
        self.branches[name] = list(self.branches[base_branch])

    def add_commit(
        self,
        branch: str,
        sha: str,
        message: str,
        author: str,
        created_at: datetime,
    ) -> None:
        if branch not in self.branches:
            raise ValueError(f"Unknown branch: {branch}")
        if not sha or len(sha) < 7:
            raise ValueError("Commit SHA must contain at least seven characters")
        self.branches[branch].append(
            Commit(sha, message, author, created_at)
        )

    def open_pr(
        self,
        source: str,
        target: str,
        author: str,
        draft: bool = False,
    ) -> PullRequest:
        if source not in self.branches or target not in self.branches:
            raise ValueError("Source and target branches must exist")
        if source == target:
            raise ValueError("A pull request cannot target the same branch")

        commits = list(self.branches[source])
        if not commits:
            raise ValueError("A pull request requires at least one commit")

        pr = PullRequest(
            number=self.next_pr_number,
            source_branch=source,
            target_branch=target,
            state=PRState.DRAFT if draft else PRState.OPEN,
            author=author,
            commits=commits,
            target_head_sha=self.branches[target][-1].sha
            if self.branches[target]
            else "",
            opened_at=datetime.utcnow(),
            draft=draft,
        )
        self.pull_requests[pr.number] = pr
        self.next_pr_number += 1
        return pr

    def add_review(
        self,
        pr_number: int,
        reviewer: str,
        state: ReviewState,
        commit_sha: str,
        comments: List[ReviewComment] | None = None,
    ) -> None:
        pr = self.pull_requests[pr_number]
        if pr.state not in {PRState.OPEN, PRState.DRAFT}:
            raise ValueError("Reviews can only be submitted on active pull requests")
        if reviewer == pr.author:
            raise ValueError("Authors cannot approve their own pull request")

        pr.reviews.append(
            Review(
                reviewer=reviewer,
                state=state,
                submitted_at=datetime.utcnow(),
                comments=comments or [],
                commit_sha=commit_sha,
            )
        )

    def add_status_check(
        self,
        pr_number: int,
        name: str,
        passed: bool,
        duration_seconds: float,
    ) -> None:
        if duration_seconds < 0:
            raise ValueError("Check duration cannot be negative")

        pr = self.pull_requests[pr_number]
        pr.status_checks = [
            check for check in pr.status_checks if check.name != name
        ]
        pr.status_checks.append(
            StatusCheck(name, passed, name in self.protection.required_checks,
                        duration_seconds)
        )

    def reopen(self, pr_number: int) -> None:
        pr = self.pull_requests[pr_number]
        if pr.state != PRState.CLOSED:
            raise ValueError("Only closed pull requests can be reopened")
        pr.state = PRState.OPEN
        pr.draft = False

    def close(self, pr_number: int) -> None:
        pr = self.pull_requests[pr_number]
        if pr.state == PRState.MERGED:
            raise ValueError("A merged pull request cannot be closed again")
        pr.state = PRState.CLOSED

    def synchronize_base(self, pr_number: int) -> None:
        pr = self.pull_requests[pr_number]
        target_commits = self.branches[pr.target_branch]
        pr.target_head_sha = target_commits[-1].sha if target_commits else ""
        pr.base_changed_since_review = True

    def unresolved_comments(self, pr: PullRequest) -> int:
        return sum(
            1
            for review in pr.reviews
            for comment in review.comments
            if not comment.resolved
        )

    def approval_count(self, pr: PullRequest) -> int:
        """Only current approvals survive a changed base or newer source commit."""
        latest_source_sha = pr.commits[-1].sha
        eligible = 0
        for review in pr.reviews:
            if review.state != ReviewState.APPROVED:
                continue
            if review.commit_sha != latest_source_sha:
                continue
            if pr.base_changed_since_review:
                continue
            eligible += 1
        return eligible

    def required_checks_passed(self, pr: PullRequest) -> bool:
        checks = {check.name: check for check in pr.status_checks}
        return all(
            name in checks and checks[name].passed
            for name in self.protection.required_checks
        )

    def merge_eligibility(self, pr_number: int) -> Tuple[bool, List[str]]:
        pr = self.pull_requests[pr_number]
        failures: List[str] = []

        if pr.state != PRState.OPEN:
            failures.append("pull request is not open")
        if pr.draft:
            failures.append("pull request is still a draft")
        if not pr.commits:
            failures.append("no commits are present")

        if self.approval_count(pr) < self.protection.required_reviews:
            failures.append("required approvals are not satisfied")

        if not self.required_checks_passed(pr):
            failures.append("required status checks are not passing")

        if (
            self.protection.require_conversation_resolution
            and self.unresolved_comments(pr) > 0
        ):
            failures.append("unresolved review conversations remain")

        if self.protection.require_linear_history:
            shas = [commit.sha for commit in pr.commits]
            if len(shas) != len(set(shas)):
                failures.append("source history is not linear")

        return not failures, failures

    def merge(self, pr_number: int, strategy: str = "squash") -> str:
        eligible, failures = self.merge_eligibility(pr_number)
        if not eligible:
            raise RuntimeError("Merge blocked: " + "; ".join(failures))

        pr = self.pull_requests[pr_number]
        if strategy not in {"merge", "squash", "rebase"}:
            raise ValueError("Unsupported merge strategy")

        if strategy == "squash":
            merged_sha = f"merge-{pr.number:04d}-squash"
        elif strategy == "rebase":
            merged_sha = f"merge-{pr.number:04d}-rebase"
        else:
            merged_sha = f"merge-{pr.number:04d}-merge"

        target = self.branches[pr.target_branch]
        target.extend(pr.commits)
        pr.merged_sha = merged_sha
        pr.state = PRState.MERGED
        return merged_sha


def demonstrate() -> None:
    resources = ResourceManager(
        [
            Resource("Asha", ResourceType.ENGINEER, 32, 80),
            Resource("Ravi", ResourceType.REVIEWER, 16, 100),
            Resource("CI-Runner", ResourceType.CI, 20, 25),
        ]
    )

    resources.allocate("Asha", 14)
    resources.allocate("Ravi", 4)
    resources.allocate("CI-Runner", 1.5)

    protection = BranchProtection(
        required_reviews=1,
        required_checks={"unit-tests", "security-scan"},
        require_conversation_resolution=True,
        require_linear_history=True,
        allow_force_push=False,
        allow_deletion=False,
        allow_direct_push=False,
    )

    repo = Repository("resource-planner", "main", protection)
    now = datetime.utcnow()

    repo.create_branch("feature/capacity", "main")
    repo.add_commit(
        "feature/capacity",
        "a1b2c3d",
        "Add capacity allocation engine",
        "Asha",
        now,
    )
    repo.add_commit(
        "feature/capacity",
        "e4f5g6h",
        "Validate resource limits",
        "Asha",
        now + timedelta(minutes=10),
    )

    pr = repo.open_pr("feature/capacity", "main", "Asha")

    comment = ReviewComment(
        reviewer="Ravi",
        file_path="resource_manager.py",
        line=112,
        body="Please verify that negative allocations are rejected.",
    )

    repo.add_review(
        pr.number,
        "Ravi",
        ReviewState.CHANGES_REQUESTED,
        "e4f5g6h",
        [comment],
    )

    eligible, failures = repo.merge_eligibility(pr.number)
    assert not eligible
    assert "required approvals are not satisfied" in failures

    comment.resolved = True

    repo.add_review(
        pr.number,
        "Ravi",
        ReviewState.APPROVED,
        "e4f5g6h",
    )
    repo.add_status_check(pr.number, "unit-tests", True, 42)
    repo.add_status_check(pr.number, "security-scan", True, 65)

    eligible, failures = repo.merge_eligibility(pr.number)
    assert eligible, failures

    merged_sha = repo.merge(pr.number, "squash")

    print("Repository:", repo.name)
    print("Pull Request:", pr.number)
    print("State:", pr.state.value)
    print("Merged commit:", merged_sha)
    print("Project resource cost:", f"${resources.project_cost():,.2f}")
    print("\nResource utilization:")
    for name, capacity, used, utilization in resources.report():
        print(
            f"  {name:12} capacity={capacity:5.1f}h "
            f"used={used:5.1f}h utilization={utilization:6.1%}"
        )

    try:
        resources.allocate("Asha", 30)
    except ValueError as exc:
        print("\nExpected allocation failure:", exc)

    try:
        repo.merge(pr.number)
    except RuntimeError as exc:
        print("Expected repeated-merge failure:", exc)


if __name__ == "__main__":
    demonstrate()
