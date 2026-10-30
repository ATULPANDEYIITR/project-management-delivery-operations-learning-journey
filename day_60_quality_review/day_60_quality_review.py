#!/usr/bin/env python3
"""Repository quality review and merge-governance simulation.

The model separates Pull Request workflow, review discussions, approval
decisions, automated checks, and branch-level enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class DomainError(Exception):
    """Raised when a repository operation violates a domain rule."""


class Role(str, Enum):
    READ = "read"
    WRITE = "write"
    MAINTAIN = "maintain"
    ADMIN = "admin"


class PullRequestState(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class ReviewState(str, Enum):
    COMMENTED = "commented"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    DISMISSED = "dismissed"
    STALE = "stale"


class CheckState(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"


class MergeStrategy(str, Enum):
    MERGE = "merge"
    SQUASH = "squash"
    REBASE = "rebase"


@dataclass(frozen=True)
class Member:
    username: str
    role: Role
    active: bool = True


@dataclass
class Commit:
    commit_id: str
    author: str
    message: str
    parents: tuple[str, ...]
    changed_paths: frozenset[str]


@dataclass
class Branch:
    name: str
    head: str
    protected: bool = False
    deleted: bool = False


@dataclass
class ReviewComment:
    comment_id: int
    reviewer: str
    path: str
    line: int
    body: str
    resolved: bool = False


@dataclass
class Review:
    review_id: int
    reviewer: str
    state: ReviewState
    reviewed_commit: str
    submitted_order: int


@dataclass
class StatusCheck:
    context: str
    commit_id: str
    state: CheckState
    details: str = ""


@dataclass
class ProtectionPolicy:
    required_approvals: int = 1
    required_status_checks: set[str] = field(default_factory=set)
    dismiss_stale_approvals: bool = True
    require_conversation_resolution: bool = True
    require_linear_history: bool = False
    allow_direct_push: bool = False
    allow_force_push: bool = False
    allow_deletion: bool = False
    administrators_enforced: bool = True
    bypass_roles: set[Role] = field(default_factory=set)


@dataclass
class PullRequest:
    number: int
    title: str
    author: str
    source_branch: str
    target_branch: str
    base_commit: str
    head_commit: str
    state: PullRequestState
    strategy: MergeStrategy = MergeStrategy.SQUASH
    has_conflicts: bool = False
    changed_paths: set[str] = field(default_factory=set)
    requested_reviewers: set[str] = field(default_factory=set)
    reviews: list[Review] = field(default_factory=list)
    comments: list[ReviewComment] = field(default_factory=list)
    checks: dict[tuple[str, str], StatusCheck] = field(default_factory=dict)
    merge_commit: str | None = None


class Repository:
    """In-memory repository with explicit governance and workflow rules."""

    def __init__(self, name: str, members: Iterable[Member]) -> None:
        if not name.strip():
            raise DomainError("Repository name cannot be empty.")

        self.name = name
        self.members = {member.username: member for member in members}
        self.commits: dict[str, Commit] = {}
        self.branches: dict[str, Branch] = {}
        self.pull_requests: dict[int, PullRequest] = {}
        self.protection: dict[str, ProtectionPolicy] = {}
        self._commit_sequence = 0
        self._pr_sequence = 0
        self._review_sequence = 0
        self._comment_sequence = 0

        if len(self.members) != len(list(members)):
            raise DomainError("Repository usernames must be unique.")

        root = self._new_commit(
            author="system",
            message="Initial repository commit",
            parents=(),
            paths=(),
        )
        self.branches["main"] = Branch("main", root.commit_id)

    def _member(self, username: str) -> Member:
        member = self.members.get(username)
        if member is None or not member.active:
            raise DomainError(f"Inactive or unknown repository member: {username}")
        return member

    @staticmethod
    def _validate_paths(paths: Iterable[str]) -> frozenset[str]:
        normalized = set()
        for path in paths:
            value = path.strip().replace("\\", "/")
            if (
                not value
                or value.startswith("/")
                or ".." in value.split("/")
                or "\x00" in value
            ):
                raise DomainError(f"Invalid repository path: {path!r}")
            normalized.add(value)
        return frozenset(normalized)

    def _new_commit(
        self,
        author: str,
        message: str,
        parents: tuple[str, ...],
        paths: Iterable[str],
    ) -> Commit:
        if not message.strip():
            raise DomainError("Commit message cannot be empty.")
        if any(parent not in self.commits for parent in parents):
            raise DomainError("A commit cannot reference an unknown parent.")

        self._commit_sequence += 1
        commit_id = f"c{self._commit_sequence:06d}"
        commit = Commit(
            commit_id=commit_id,
            author=author,
            message=message.strip(),
            parents=parents,
            changed_paths=self._validate_paths(paths),
        )
        self.commits[commit_id] = commit
        return commit

    def create_branch(self, name: str, from_branch: str = "main") -> Branch:
        if not name.strip() or name in self.branches:
            raise DomainError("Branch name must be non-empty and unique.")
        source = self.branches.get(from_branch)
        if source is None or source.deleted:
            raise DomainError(f"Unknown source branch: {from_branch}")

        branch = Branch(name=name, head=source.head)
        self.branches[name] = branch
        return branch

    def set_protection(self, branch_name: str, policy: ProtectionPolicy) -> None:
        branch = self.branches.get(branch_name)
        if branch is None or branch.deleted:
            raise DomainError("Cannot protect an unknown branch.")
        if policy.required_approvals < 0:
            raise DomainError("Required approvals cannot be negative.")
        if any(not context.strip() for context in policy.required_status_checks):
            raise DomainError("Status-check names cannot be empty.")

        branch.protected = True
        self.protection[branch_name] = policy

    def push_commit(
        self,
        branch_name: str,
        author: str,
        message: str,
        paths: Iterable[str],
        force: bool = False,
    ) -> Commit:
        member = self._member(author)
        if member.role not in {Role.WRITE, Role.MAINTAIN, Role.ADMIN}:
            raise DomainError("The member does not have push permission.")

        branch = self.branches.get(branch_name)
        if branch is None or branch.deleted:
            raise DomainError("Target branch does not exist.")

        policy = self.protection.get(branch_name)
        if branch.protected and policy:
            if not policy.allow_direct_push and member.role not in policy.bypass_roles:
                raise DomainError("Direct pushes are prohibited by branch protection.")
            if force and not policy.allow_force_push:
                raise DomainError("Force pushes are prohibited by branch protection.")

        parents = () if force else (branch.head,)
        commit = self._new_commit(author, message, parents, paths)
        branch.head = commit.commit_id
        return commit

    def _commits_since(self, head: str, base: str) -> list[Commit]:
        """Return first-parent commits from base-exclusive to head-inclusive."""
        result: list[Commit] = []
        cursor = head
        visited: set[str] = set()

        while cursor != base:
            if cursor in visited or cursor not in self.commits:
                raise DomainError("The requested base is not an ancestor of the branch.")
            visited.add(cursor)
            commit = self.commits[cursor]
            result.append(commit)
            if not commit.parents:
                raise DomainError("The requested base is not an ancestor of the branch.")
            cursor = commit.parents[0]

        result.reverse()
        return result

    def open_pull_request(
        self,
        title: str,
        author: str,
        source_branch: str,
        target_branch: str = "main",
        draft: bool = False,
        strategy: MergeStrategy = MergeStrategy.SQUASH,
    ) -> PullRequest:
        self._member(author)
        source = self.branches.get(source_branch)
        target = self.branches.get(target_branch)

        if source is None or target is None or source.deleted or target.deleted:
            raise DomainError("Both Pull Request branches must exist.")
        if source_branch == target_branch:
            raise DomainError("Source and target branches must differ.")
        if not title.strip():
            raise DomainError("Pull Request title cannot be empty.")
        if source.head == target.head:
            raise DomainError("There are no changes to propose.")

        commits = self._commits_since(source.head, target.head)
        self._pr_sequence += 1
        pr = PullRequest(
            number=self._pr_sequence,
            title=title.strip(),
            author=author,
            source_branch=source_branch,
            target_branch=target_branch,
            base_commit=target.head,
            head_commit=source.head,
            state=PullRequestState.DRAFT if draft else PullRequestState.OPEN,
            strategy=strategy,
            changed_paths=set().union(*(commit.changed_paths for commit in commits)),
        )
        self.pull_requests[pr.number] = pr
        return pr

    def _pull_request(self, number: int) -> PullRequest:
        pr = self.pull_requests.get(number)
        if pr is None:
            raise DomainError(f"Pull Request #{number} does not exist.")
        return pr

    def mark_ready(self, number: int, actor: str) -> None:
        self._member(actor)
        pr = self._pull_request(number)
        if pr.state != PullRequestState.DRAFT:
            raise DomainError("Only a draft Pull Request can be marked ready.")
        if actor != pr.author and self._member(actor).role == Role.READ:
            raise DomainError("The actor cannot change Pull Request workflow state.")
        pr.state = PullRequestState.OPEN

    def request_review(self, number: int, actor: str, reviewer: str) -> None:
        pr = self._pull_request(number)
        self._member(actor)
        candidate = self._member(reviewer)

        if pr.state != PullRequestState.OPEN:
            raise DomainError("Reviews can only be requested on an open Pull Request.")
        if reviewer == pr.author:
            raise DomainError("The author cannot review their own Pull Request.")
        if candidate.role == Role.READ:
            raise DomainError("A read-only member cannot be a reviewer.")

        pr.requested_reviewers.add(reviewer)

    def submit_review(
        self,
        number: int,
        reviewer: str,
        state: ReviewState,
    ) -> Review:
        pr = self._pull_request(number)
        member = self._member(reviewer)

        if pr.state != PullRequestState.OPEN:
            raise DomainError("Reviews require an open Pull Request.")
        if reviewer == pr.author or member.role == Role.READ:
            raise DomainError("The reviewer is not eligible for this Pull Request.")
        if state not in {
            ReviewState.COMMENTED,
            ReviewState.APPROVED,
            ReviewState.CHANGES_REQUESTED,
        }:
            raise DomainError("This review state cannot be submitted.")

        self._review_sequence += 1
        review = Review(
            review_id=self._review_sequence,
            reviewer=reviewer,
            state=state,
            reviewed_commit=pr.head_commit,
            submitted_order=self._review_sequence,
        )
        pr.reviews.append(review)
        pr.requested_reviewers.discard(reviewer)
        return review

    def dismiss_review(self, number: int, review_id: int, actor: str) -> None:
        pr = self._pull_request(number)
        member = self._member(actor)
        if member.role not in {Role.MAINTAIN, Role.ADMIN}:
            raise DomainError("Only maintainers or administrators can dismiss reviews.")

        for review in pr.reviews:
            if review.review_id == review_id:
                review.state = ReviewState.DISMISSED
                return
        raise DomainError("Review does not exist.")

    def add_comment(
        self,
        number: int,
        reviewer: str,
        path: str,
        line: int,
        body: str,
    ) -> ReviewComment:
        pr = self._pull_request(number)
        member = self._member(reviewer)
        normalized_path = next(iter(self._validate_paths([path])))

        if pr.state != PullRequestState.OPEN:
            raise DomainError("Discussion comments require an open Pull Request.")
        if member.role == Role.READ:
            raise DomainError("Read-only members cannot comment.")
        if line < 1 or not body.strip():
            raise DomainError("A comment requires a positive line and non-empty body.")
        if normalized_path not in pr.changed_paths:
            raise DomainError("Inline comments must refer to a changed file.")

        self._comment_sequence += 1
        comment = ReviewComment(
            comment_id=self._comment_sequence,
            reviewer=reviewer,
            path=normalized_path,
            line=line,
            body=body.strip(),
        )
        pr.comments.append(comment)
        return comment

    def resolve_comment(self, number: int, comment_id: int, actor: str) -> None:
        pr = self._pull_request(number)
        member = self._member(actor)
        if member.role == Role.READ:
            raise DomainError("Read-only members cannot resolve discussions.")

        for comment in pr.comments:
            if comment.comment_id == comment_id:
                comment.resolved = True
                return
        raise DomainError("Discussion comment does not exist.")

    def set_status_check(
        self,
        number: int,
        context: str,
        state: CheckState,
        commit_id: str | None = None,
        details: str = "",
    ) -> None:
        pr = self._pull_request(number)
        if pr.state not in {PullRequestState.OPEN, PullRequestState.DRAFT}:
            raise DomainError("Checks cannot be updated on a closed Pull Request.")
        if not context.strip():
            raise DomainError("Status-check context cannot be empty.")

        checked_commit = commit_id or pr.head_commit
        if checked_commit not in self.commits:
            raise DomainError("Status check references an unknown commit.")

        pr.checks[(context, checked_commit)] = StatusCheck(
            context=context,
            commit_id=checked_commit,
            state=state,
            details=details.strip(),
        )

    def refresh_from_source(self, number: int) -> None:
        """Adopt a newer source head and invalidate approvals when configured."""
        pr = self._pull_request(number)
        source = self.branches[pr.source_branch]

        if pr.state != PullRequestState.OPEN:
            raise DomainError("Only an open Pull Request can be refreshed.")
        if source.head == pr.head_commit:
            return

        commits = self._commits_since(source.head, pr.base_commit)
        pr.head_commit = source.head
        pr.changed_paths = set().union(*(commit.changed_paths for commit in commits))

        policy = self.protection.get(pr.target_branch)
        if policy and policy.dismiss_stale_approvals:
            for review in pr.reviews:
                if review.state == ReviewState.APPROVED:
                    review.state = ReviewState.STALE

    def synchronize_base(self, number: int) -> bool:
        """Bring the source branch up to date if changed paths do not overlap."""
        pr = self._pull_request(number)
        if pr.state != PullRequestState.OPEN:
            raise DomainError("Only an open Pull Request can be synchronized.")

        source = self.branches[pr.source_branch]
        target = self.branches[pr.target_branch]
        self.refresh_from_source(number)

        if pr.base_commit == target.head:
            pr.has_conflicts = False
            return True

        source_changes = self._commits_since(source.head, pr.base_commit)
        target_changes = self._commits_since(target.head, pr.base_commit)
        source_paths = set().union(*(c.changed_paths for c in source_changes))
        target_paths = set().union(*(c.changed_paths for c in target_changes))

        if source_paths.intersection(target_paths):
            pr.has_conflicts = True
            return False

        merge_commit = self._new_commit(
            author="system",
            message=f"Synchronize {pr.target_branch} into {pr.source_branch}",
            parents=(source.head, target.head),
            paths=(),
        )
        source.head = merge_commit.commit_id
        pr.head_commit = merge_commit.commit_id
        pr.base_commit = target.head
        pr.has_conflicts = False

        policy = self.protection.get(pr.target_branch)
        if policy and policy.dismiss_stale_approvals:
            for review in pr.reviews:
                if review.state == ReviewState.APPROVED:
                    review.state = ReviewState.STALE
        return True

    def close_pull_request(self, number: int, actor: str) -> None:
        pr = self._pull_request(number)
        member = self._member(actor)
        if pr.state not in {PullRequestState.OPEN, PullRequestState.DRAFT}:
            raise DomainError("Only an open or draft Pull Request can be closed.")
        if actor != pr.author and member.role == Role.READ:
            raise DomainError("The actor cannot close this Pull Request.")
        pr.state = PullRequestState.CLOSED

    def reopen_pull_request(self, number: int, actor: str) -> None:
        pr = self._pull_request(number)
        member = self._member(actor)
        if pr.state != PullRequestState.CLOSED:
            raise DomainError("Only a closed Pull Request can be reopened.")
        if actor != pr.author and member.role == Role.READ:
            raise DomainError("The actor cannot reopen this Pull Request.")
        pr.state = PullRequestState.OPEN

    def _latest_reviews(self, pr: PullRequest) -> dict[str, Review]:
        latest: dict[str, Review] = {}
        for review in pr.reviews:
            previous = latest.get(review.reviewer)
            if previous is None or review.submitted_order > previous.submitted_order:
                latest[review.reviewer] = review
        return latest

    def evaluate_merge(self, number: int, actor: str) -> list[str]:
        pr = self._pull_request(number)
        actor_member = self._member(actor)
        policy = self.protection.get(pr.target_branch, ProtectionPolicy())
        target = self.branches[pr.target_branch]
        source = self.branches[pr.source_branch]
        blockers: list[str] = []

        if pr.state != PullRequestState.OPEN:
            blockers.append("Pull Request is not open.")
        if source.deleted or target.deleted:
            blockers.append("Source or target branch has been deleted.")
        if source.head != pr.head_commit:
            blockers.append("Source branch has unreviewed commits; refresh the Pull Request.")
        if pr.base_commit != target.head:
            blockers.append("Target branch has advanced; synchronize the source branch.")
        if pr.has_conflicts:
            blockers.append("Merge conflicts must be resolved.")

        bypass = (
            (actor_member.role == Role.ADMIN and not policy.administrators_enforced)
            or actor_member.role in policy.bypass_roles
        )

        if not bypass:
            for context in sorted(policy.required_status_checks):
                check = pr.checks.get((context, pr.head_commit))
                if check is None:
                    blockers.append(f"Required check '{context}' has not reported on the current head.")
                elif check.state != CheckState.SUCCESS:
                    blockers.append(f"Required check '{context}' is {check.state.value}.")

            latest = self._latest_reviews(pr)
            eligible_approvals = 0

            for reviewer, review in latest.items():
                member = self.members.get(reviewer)
                if (
                    member is None
                    or not member.active
                    or reviewer == pr.author
                    or member.role == Role.READ
                ):
                    continue

                current_review = (
                    not policy.dismiss_stale_approvals
                    or review.reviewed_commit == pr.head_commit
                )
                if not current_review:
                    continue

                if review.state == ReviewState.CHANGES_REQUESTED:
                    blockers.append(f"{reviewer} has requested changes.")
                elif review.state == ReviewState.APPROVED:
                    eligible_approvals += 1

            if eligible_approvals < policy.required_approvals:
                blockers.append(
                    f"Approval requirement not met: "
                    f"{eligible_approvals}/{policy.required_approvals}."
                )

            if policy.require_conversation_resolution:
                unresolved = sum(not comment.resolved for comment in pr.comments)
                if unresolved:
                    blockers.append(f"{unresolved} review discussion(s) remain unresolved.")

            if policy.require_linear_history and pr.strategy == MergeStrategy.MERGE:
                blockers.append("The selected merge strategy violates linear-history policy.")

        return blockers

    def merge_pull_request(self, number: int, actor: str) -> Commit:
        pr = self._pull_request(number)
        blockers = self.evaluate_merge(number, actor)
        if blockers:
            raise DomainError("Merge blocked: " + "; ".join(blockers))

        target = self.branches[pr.target_branch]
        source_commits = self._commits_since(pr.head_commit, pr.base_commit)
        paths = set().union(*(commit.changed_paths for commit in source_commits))

        if pr.strategy == MergeStrategy.MERGE:
            parents = (target.head, source.head) if (
                source := self.branches[pr.source_branch]
            ) else (target.head, pr.head_commit)
            merge_commit = self._new_commit(
                actor,
                f"Merge Pull Request #{number}: {pr.title}",
                parents,
                paths,
            )
        else:
            message = (
                f"Squash Pull Request #{number}: {pr.title}"
                if pr.strategy == MergeStrategy.SQUASH
                else f"Rebase Pull Request #{number}: {pr.title}"
            )
            merge_commit = self._new_commit(
                actor,
                message,
                (target.head,),
                paths,
            )

        target.head = merge_commit.commit_id
        pr.merge_commit = merge_commit.commit_id
        pr.state = PullRequestState.MERGED
        return merge_commit


def demonstrate() -> None:
    members = [
        Member("developer", Role.WRITE),
        Member("reviewer", Role.MAINTAIN),
        Member("administrator", Role.ADMIN),
    ]
    repository = Repository("quality-engine", members)

    repository.set_protection(
        "main",
        ProtectionPolicy(
            required_approvals=1,
            required_status_checks={"unit-tests", "security-scan"},
            dismiss_stale_approvals=True,
            require_conversation_resolution=True,
            require_linear_history=True,
            allow_direct_push=False,
            allow_force_push=False,
            allow_deletion=False,
            administrators_enforced=True,
        ),
    )

    repository.create_branch("feature/review-engine")
    repository.push_commit(
        "feature/review-engine",
        "developer",
        "Add review-quality validation",
        ["src/review.py", "tests/test_review.py"],
    )

    pr = repository.open_pull_request(
        "Enforce review quality gates",
        "developer",
        "feature/review-engine",
        strategy=MergeStrategy.SQUASH,
    )
    repository.request_review(pr.number, "developer", "reviewer")
    review = repository.submit_review(
        pr.number,
        "reviewer",
        ReviewState.APPROVED,
    )

    comment = repository.add_comment(
        pr.number,
        "reviewer",
        "src/review.py",
        12,
        "The validation rule is clear and the boundary condition is covered.",
    )
    repository.resolve_comment(pr.number, comment.comment_id, "developer")

    repository.set_status_check(pr.number, "unit-tests", CheckState.SUCCESS)
    repository.set_status_check(pr.number, "security-scan", CheckState.SUCCESS)

    print(f"Repository: {repository.name}")
    print(f"Pull Request: #{pr.number} - {pr.title}")
    print(f"Review: {review.state.value}")
    print("Merge blockers:", repository.evaluate_merge(pr.number, "developer") or "none")

    merged = repository.merge_pull_request(pr.number, "developer")
    print(f"Result: {pr.state.value}")
    print(f"Merge commit: {merged.commit_id}")

    try:
        repository.push_commit(
            "main",
            "developer",
            "Attempt prohibited direct push",
            ["src/unreviewed.py"],
        )
    except DomainError as error:
        print(f"Expected protection failure: {error}")


if __name__ == "__main__":
    demonstrate()
