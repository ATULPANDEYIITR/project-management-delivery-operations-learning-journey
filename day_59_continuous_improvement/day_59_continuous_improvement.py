from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
import json


class PRState(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewState(str, Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    DISMISSED = "dismissed"


class CheckState(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class Commit:
    sha: str
    message: str
    author: str


@dataclass
class Branch:
    name: str
    protected: bool = False
    commits: List[str] = field(default_factory=list)


@dataclass
class Review:
    reviewer: str
    state: ReviewState
    commit_sha: str
    submitted_at: datetime
    comments: List[str] = field(default_factory=list)


@dataclass
class StatusCheck:
    name: str
    state: CheckState
    commit_sha: str


@dataclass
class ProtectionPolicy:
    required_approvals: int = 1
    required_checks: Set[str] = field(default_factory=set)
    require_conversations_resolved: bool = True
    allow_direct_push: bool = False
    allow_force_push: bool = False
    allow_branch_deletion: bool = False
    require_linear_history: bool = False
    dismiss_stale_approvals: bool = True


@dataclass
class PullRequest:
    number: int
    title: str
    source_branch: str
    target_branch: str
    author: str
    state: PRState = PRState.OPEN
    draft: bool = False
    commits: List[str] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    checks: List[StatusCheck] = field(default_factory=list)
    unresolved_conversations: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def head(self) -> Optional[str]:
        return self.commits[-1] if self.commits else None


class RepositoryError(Exception):
    pass


class Repository:
    def __init__(self, name: str):
        self.name = name
        self.branches: Dict[str, Branch] = {}
        self.commits: Dict[str, Commit] = {}
        self.pull_requests: Dict[int, PullRequest] = {}
        self.policy_by_branch: Dict[str, ProtectionPolicy] = {}
        self.next_pr_number = 1

    def add_branch(self, name: str, protected: bool = False) -> None:
        if name in self.branches:
            raise RepositoryError(f"Branch already exists: {name}")
        self.branches[name] = Branch(name=name, protected=protected)

    def add_commit(self, branch: str, sha: str, message: str, author: str) -> None:
        if branch not in self.branches:
            raise RepositoryError(f"Unknown branch: {branch}")
        if sha in self.commits:
            raise RepositoryError(f"Duplicate commit: {sha}")
        if not sha or len(sha) < 7:
            raise RepositoryError("Commit SHA must contain at least seven characters")

        self.commits[sha] = Commit(sha, message, author)
        self.branches[branch].commits.append(sha)

    def protect_branch(self, branch: str, policy: ProtectionPolicy) -> None:
        if branch not in self.branches:
            raise RepositoryError(f"Unknown branch: {branch}")
        if policy.required_approvals < 0:
            raise RepositoryError("Approval requirement cannot be negative")
        self.branches[branch].protected = True
        self.policy_by_branch[branch] = policy

    def create_pull_request(
        self,
        title: str,
        source: str,
        target: str,
        author: str,
        draft: bool = False,
    ) -> PullRequest:
        if source not in self.branches or target not in self.branches:
            raise RepositoryError("Source and target branches must exist")
        if source == target:
            raise RepositoryError("Source and target branches must differ")
        if not self.branches[source].commits:
            raise RepositoryError("Source branch must contain at least one commit")

        pr = PullRequest(
            number=self.next_pr_number,
            title=title.strip(),
            source_branch=source,
            target_branch=target,
            author=author,
            state=PRState.DRAFT if draft else PRState.OPEN,
            draft=draft,
            commits=list(self.branches[source].commits),
        )
        if not pr.title:
            raise RepositoryError("Pull request title cannot be empty")

        self.pull_requests[pr.number] = pr
        self.next_pr_number += 1
        return pr

    def synchronize(self, pr_number: int) -> None:
        pr = self.get_pr(pr_number)
        self._ensure_open(pr)
        pr.commits = list(self.branches[pr.source_branch].commits)
        pr.updated_at = datetime.now(timezone.utc)

        policy = self.policy_by_branch.get(pr.target_branch)
        if policy and policy.dismiss_stale_approvals:
            head = pr.head()
            for review in pr.reviews:
                if review.state == ReviewState.APPROVED and review.commit_sha != head:
                    review.state = ReviewState.DISMISSED

    def add_review(
        self,
        pr_number: int,
        reviewer: str,
        state: ReviewState,
        comments: Optional[List[str]] = None,
    ) -> None:
        pr = self.get_pr(pr_number)
        self._ensure_open(pr)

        if reviewer == pr.author:
            raise RepositoryError("Pull request authors cannot approve their own changes")
        if not pr.head():
            raise RepositoryError("Cannot review a pull request without a commit")

        review = Review(
            reviewer=reviewer,
            state=state,
            commit_sha=pr.head(),
            submitted_at=datetime.now(timezone.utc),
            comments=comments or [],
        )
        pr.reviews.append(review)
        pr.updated_at = datetime.now(timezone.utc)

    def add_check(self, pr_number: int, name: str, state: CheckState) -> None:
        pr = self.get_pr(pr_number)
        self._ensure_open(pr)
        if not name.strip():
            raise RepositoryError("Status check name cannot be empty")
        if not pr.head():
            raise RepositoryError("Cannot run a check without a commit")

        pr.checks = [
            c for c in pr.checks
            if not (c.name == name and c.commit_sha == pr.head())
        ]
        pr.checks.append(StatusCheck(name, state, pr.head()))
        pr.updated_at = datetime.now(timezone.utc)

    def add_conversation(self, pr_number: int) -> None:
        pr = self.get_pr(pr_number)
        self._ensure_open(pr)
        pr.unresolved_conversations += 1

    def resolve_conversation(self, pr_number: int) -> None:
        pr = self.get_pr(pr_number)
        if pr.unresolved_conversations == 0:
            raise RepositoryError("No unresolved conversations exist")
        pr.unresolved_conversations -= 1

    def mark_ready(self, pr_number: int) -> None:
        pr = self.get_pr(pr_number)
        self._ensure_open(pr)
        pr.draft = False
        pr.state = PRState.OPEN
        pr.updated_at = datetime.now(timezone.utc)

    def evaluate_merge(self, pr_number: int) -> Tuple[bool, List[str]]:
        pr = self.get_pr(pr_number)
        reasons: List[str] = []

        if pr.state != PRState.OPEN:
            reasons.append("Pull request is not open")
        if pr.draft:
            reasons.append("Pull request is still a draft")
        if not pr.commits:
            reasons.append("No commits are proposed")

        policy = self.policy_by_branch.get(pr.target_branch)
        if policy is None:
            policy = ProtectionPolicy(
                required_approvals=0,
                required_checks=set(),
                require_conversations_resolved=False,
            )

        head = pr.head()

        valid_approvals = {
            review.reviewer
            for review in pr.reviews
            if review.state == ReviewState.APPROVED
            and review.commit_sha == head
            and review.reviewer != pr.author
        }

        if len(valid_approvals) < policy.required_approvals:
            reasons.append(
                f"Need {policy.required_approvals} current approval(s), "
                f"have {len(valid_approvals)}"
            )

        checks = {
            check.name: check.state
            for check in pr.checks
            if check.commit_sha == head
        }

        for required in policy.required_checks:
            if checks.get(required) != CheckState.SUCCESS:
                reasons.append(f"Required check failed or missing: {required}")

        if policy.require_conversations_resolved and pr.unresolved_conversations:
            reasons.append(
                f"{pr.unresolved_conversations} conversation(s) remain unresolved"
            )

        return not reasons, reasons

    def merge(self, pr_number: int) -> None:
        pr = self.get_pr(pr_number)
        eligible, reasons = self.evaluate_merge(pr_number)
        if not eligible:
            raise RepositoryError("Merge blocked: " + "; ".join(reasons))

        target = self.branches[pr.target_branch]
        source = self.branches[pr.source_branch]

        for sha in source.commits:
            if sha not in target.commits:
                target.commits.append(sha)

        pr.state = PRState.MERGED
        pr.updated_at = datetime.now(timezone.utc)

    def close(self, pr_number: int) -> None:
        pr = self.get_pr(pr_number)
        self._ensure_open(pr)
        pr.state = PRState.CLOSED
        pr.updated_at = datetime.now(timezone.utc)

    def reopen(self, pr_number: int) -> None:
        pr = self.get_pr(pr_number)
        if pr.state != PRState.CLOSED:
            raise RepositoryError("Only closed pull requests can be reopened")
        pr.state = PRState.OPEN
        pr.updated_at = datetime.now(timezone.utc)

    def get_pr(self, pr_number: int) -> PullRequest:
        try:
            return self.pull_requests[pr_number]
        except KeyError as exc:
            raise RepositoryError(f"Unknown pull request: {pr_number}") from exc

    @staticmethod
    def _ensure_open(pr: PullRequest) -> None:
        if pr.state not in {PRState.OPEN, PRState.DRAFT}:
            raise RepositoryError(f"Pull request is {pr.state.value}")


def print_report(repo: Repository, pr_number: int) -> None:
    pr = repo.get_pr(pr_number)
    eligible, reasons = repo.evaluate_merge(pr_number)

    report = {
        "repository": repo.name,
        "pull_request": pr.number,
        "title": pr.title,
        "source": pr.source_branch,
        "target": pr.target_branch,
        "state": pr.state.value,
        "head": pr.head(),
        "merge_eligible": eligible,
        "blocking_reasons": reasons,
        "reviews": [
            {
                "reviewer": r.reviewer,
                "state": r.state.value,
                "commit": r.commit_sha,
            }
            for r in pr.reviews
        ],
        "checks": [
            {
                "name": c.name,
                "state": c.state.value,
                "commit": c.commit_sha,
            }
            for c in pr.checks
        ],
    }
    print(json.dumps(report, indent=2))


def main() -> None:
    repo = Repository("continuous-improvement-platform")
    repo.add_branch("main", protected=True)
    repo.add_branch("improvement/lead-time")
    repo.add_branch("improvement/review-quality")

    repo.add_commit(
        "main", "a100001", "Establish baseline development workflow", "platform"
    )
    repo.add_commit(
        "improvement/lead-time",
        "b100001",
        "Measure pull request cycle time",
        "developer-1",
    )
    repo.add_commit(
        "improvement/lead-time",
        "b100002",
        "Add process metrics",
        "developer-1",
    )

    repo.protect_branch(
        "main",
        ProtectionPolicy(
            required_approvals=2,
            required_checks={"unit-tests", "security-scan"},
            require_conversations_resolved=True,
            allow_direct_push=False,
            allow_force_push=False,
            allow_branch_deletion=False,
            require_linear_history=True,
            dismiss_stale_approvals=True,
        ),
    )

    pr = repo.create_pull_request(
        "Reduce pull request cycle time",
        "improvement/lead-time",
        "main",
        "developer-1",
    )

    repo.add_conversation(pr.number)
    repo.add_review(pr.number, "reviewer-1", ReviewState.APPROVED)
    repo.add_review(pr.number, "reviewer-2", ReviewState.CHANGES_REQUESTED)
    repo.add_check(pr.number, "unit-tests", CheckState.SUCCESS)
    repo.add_check(pr.number, "security-scan", CheckState.SUCCESS)

    print("Initial eligibility:")
    print_report(repo, pr.number)

    repo.resolve_conversation(pr.number)
    repo.add_review(pr.number, "reviewer-2", ReviewState.APPROVED)

    eligible, reasons = repo.evaluate_merge(pr.number)
    assert eligible, reasons
    repo.merge(pr.number)

    print("\nAfter approval and merge:")
    print_report(repo, pr.number)

    # Demonstrate stale approval handling after a new source commit.
    repo.add_commit(
        "improvement/review-quality",
        "c100001",
        "Add review quality metrics",
        "developer-2",
    )
    pr2 = repo.create_pull_request(
        "Improve review quality measurement",
        "improvement/review-quality",
        "main",
        "developer-2",
    )
    repo.add_review(pr2.number, "reviewer-1", ReviewState.APPROVED)
    repo.add_review(pr2.number, "reviewer-2", ReviewState.APPROVED)
    repo.add_check(pr2.number, "unit-tests", CheckState.SUCCESS)
    repo.add_check(pr2.number, "security-scan", CheckState.SUCCESS)

    repo.add_commit(
        "improvement/review-quality",
        "c100002",
        "Fix review metric calculation",
        "developer-2",
    )
    repo.synchronize(pr2.number)

    eligible, reasons = repo.evaluate_merge(pr2.number)
    assert not eligible
    assert any("approval" in reason.lower() for reason in reasons)

    print("\nAfter source branch changes invalidate approvals:")
    print_report(repo, pr2.number)


if __name__ == "__main__":
    main()
