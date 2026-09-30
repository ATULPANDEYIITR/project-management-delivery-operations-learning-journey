"""
Scope Review: Reviewing Scope Management

A self-contained implementation of a scope-review workflow for a software
repository change. The model focuses on defining the approved scope,
checking requested changes against that scope, identifying scope creep,
tracking review findings, evaluating change requests, and producing an
audit-ready scope decision.

The implementation is intentionally separate from code-review approval
mechanics. A scope review answers: "Is this work still within the agreed
scope?" rather than simply: "Is the implementation technically correct?"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Iterable


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class ScopeStatus(str, Enum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    PARTIALLY_IN_SCOPE = "partially_in_scope"
    REQUIRES_CHANGE_CONTROL = "requires_change_control"


class FindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewDecision(str, Enum):
    ACCEPT = "accept"
    ACCEPT_WITH_NOTES = "accept_with_notes"
    REVISE_SCOPE = "revise_scope"
    REJECT = "reject"


@dataclass(frozen=True)
class ScopeItem:
    """One approved unit of work in the baseline scope."""

    item_id: str
    name: str
    description: str
    acceptance_criteria: tuple[str, ...]
    priority: str = "normal"
    excluded: bool = False


@dataclass(frozen=True)
class ChangeRequest:
    """A proposed change that may or may not belong to the approved scope."""

    request_id: str
    title: str
    description: str
    requested_by: str
    related_scope_items: tuple[str, ...]
    estimated_hours: float
    business_justification: str
    requested_at: datetime = field(default_factory=utc_now)


@dataclass
class ScopeFinding:
    """A finding produced during scope review."""

    finding_id: str
    severity: FindingSeverity
    subject: str
    description: str
    affected_scope_items: list[str]
    recommendation: str
    resolved: bool = False


@dataclass
class ScopeBaseline:
    """Approved scope against which implementation requests are evaluated."""

    project_name: str
    version: str
    objective: str
    items: dict[str, ScopeItem]
    exclusions: list[str]
    assumptions: list[str]
    approved_at: datetime = field(default_factory=utc_now)

    def contains(self, item_id: str) -> bool:
        """Return whether an identifier exists in the approved scope."""
        return item_id in self.items and not self.items[item_id].excluded

    def validate(self) -> list[str]:
        """Detect malformed baseline data before it is used for review."""
        errors: list[str] = []

        if not self.project_name.strip():
            errors.append("Project name is required.")

        if not self.version.strip():
            errors.append("Scope baseline version is required.")

        if not self.objective.strip():
            errors.append("Scope objective is required.")

        if not self.items:
            errors.append("At least one scope item is required.")

        for item_id, item in self.items.items():
            if item_id != item.item_id:
                errors.append(
                    f"Dictionary key '{item_id}' does not match item ID "
                    f"'{item.item_id}'."
                )

            if not item.name.strip():
                errors.append(f"Scope item '{item_id}' has no name.")

            if not item.description.strip():
                errors.append(f"Scope item '{item_id}' has no description.")

            if not item.acceptance_criteria:
                errors.append(
                    f"Scope item '{item_id}' has no acceptance criteria."
                )

        return errors


@dataclass
class ScopeReview:
    """Complete result of evaluating a proposed change against the baseline."""

    request: ChangeRequest
    status: ScopeStatus
    findings: list[ScopeFinding]
    matched_items: list[str]
    unmatched_scope_references: list[str]
    estimated_scope_delta_hours: float
    decision: ReviewDecision | None = None
    reviewer: str | None = None
    reviewed_at: datetime | None = None

    @property
    def has_high_risk_findings(self) -> bool:
        """High and critical findings require explicit handling."""
        return any(
            finding.severity in {
                FindingSeverity.HIGH,
                FindingSeverity.CRITICAL,
            }
            and not finding.resolved
            for finding in self.findings
        )

    def unresolved_findings(self) -> list[ScopeFinding]:
        """Return findings that still require action."""
        return [finding for finding in self.findings if not finding.resolved]


class ScopeReviewEngine:
    """
    Evaluate change requests against a scope baseline.

    The engine deliberately separates:
    - baseline membership,
    - exclusions,
    - change magnitude,
    - scope creep,
    - review findings,
    - final review decisions.

    This separation makes the scope-review process auditable.
    """

    def __init__(self, baseline: ScopeBaseline) -> None:
        errors = baseline.validate()
        if errors:
            raise ValueError(
                "Invalid scope baseline:\n- " + "\n- ".join(errors)
            )

        self.baseline = baseline
        self.review_history: list[ScopeReview] = []

    def classify(self, request: ChangeRequest) -> ScopeReview:
        """
        Classify a change request against the approved scope.

        A request may reference approved items while still expanding the
        scope through new functionality, excessive effort, or an explicit
        exclusion.
        """
        findings: list[ScopeFinding] = []
        matched_items: list[str] = []
        unmatched: list[str] = []

        if request.estimated_hours < 0:
            raise ValueError("Estimated hours cannot be negative.")

        if not request.title.strip():
            raise ValueError("Change request title is required.")

        if not request.description.strip():
            raise ValueError("Change request description is required.")

        for scope_id in request.related_scope_items:
            if self.baseline.contains(scope_id):
                matched_items.append(scope_id)
            elif scope_id in self.baseline.items:
                unmatched.append(scope_id)
                findings.append(
                    ScopeFinding(
                        finding_id=f"F-{request.request_id}-EXCLUDED",
                        severity=FindingSeverity.HIGH,
                        subject="Excluded scope item referenced",
                        description=(
                            f"Request references '{scope_id}', but that item "
                            "is explicitly excluded from the baseline."
                        ),
                        affected_scope_items=[scope_id],
                        recommendation=(
                            "Do not treat the work as baseline scope unless "
                            "the exclusion is formally changed."
                        ),
                    )
                )
            else:
                unmatched.append(scope_id)
                findings.append(
                    ScopeFinding(
                        finding_id=f"F-{request.request_id}-UNKNOWN",
                        severity=FindingSeverity.MEDIUM,
                        subject="Unknown scope reference",
                        description=(
                            f"'{scope_id}' does not exist in the approved "
                            "scope baseline."
                        ),
                        affected_scope_items=[],
                        recommendation=(
                            "Create a formal scope item or remove the "
                            "reference."
                        ),
                    )
                )

        if not request.related_scope_items:
            findings.append(
                ScopeFinding(
                    finding_id=f"F-{request.request_id}-NO-LINK",
                    severity=FindingSeverity.HIGH,
                    subject="Change is not mapped to baseline scope",
                    description=(
                        "The request does not identify an approved scope item."
                    ),
                    affected_scope_items=[],
                    recommendation=(
                        "Map the request to an existing baseline item or "
                        "submit it as a scope change."
                    ),
                )
            )

        description_lower = request.description.lower()

        expansion_signals = {
            "new": "new functionality",
            "additional": "additional functionality",
            "redesign": "redesign",
            "unrelated": "unrelated work",
            "replace": "replacement work",
            "migration": "migration work",
            "new integration": "new integration",
        }

        detected_signals = [
            label
            for signal, label in expansion_signals.items()
            if signal in description_lower
        ]

        if detected_signals:
            findings.append(
                ScopeFinding(
                    finding_id=f"F-{request.request_id}-EXPANSION",
                    severity=FindingSeverity.MEDIUM,
                    subject="Potential scope expansion",
                    description=(
                        "The request contains language associated with "
                        f"scope expansion: {', '.join(detected_signals)}."
                    ),
                    affected_scope_items=matched_items.copy(),
                    recommendation=(
                        "Confirm whether the requested work is already "
                        "covered by the baseline acceptance criteria."
                    ),
                )
            )

        if request.estimated_hours > 16:
            findings.append(
                ScopeFinding(
                    finding_id=f"F-{request.request_id}-EFFORT",
                    severity=FindingSeverity.MEDIUM,
                    subject="Material effort increase",
                    description=(
                        f"The request estimates {request.estimated_hours:.1f} "
                        "hours of work, indicating a potentially material "
                        "change to the approved delivery scope."
                    ),
                    affected_scope_items=matched_items.copy(),
                    recommendation=(
                        "Validate effort against the original estimate and "
                        "perform formal change assessment if necessary."
                    ),
                )
            )

        if matched_items and not unmatched and not detected_signals:
            status = ScopeStatus.IN_SCOPE
        elif matched_items and (unmatched or detected_signals):
            status = ScopeStatus.PARTIALLY_IN_SCOPE
        else:
            status = ScopeStatus.OUT_OF_SCOPE

        if (
            status != ScopeStatus.IN_SCOPE
            or request.estimated_hours > 16
        ):
            status = ScopeStatus.REQUIRES_CHANGE_CONTROL

        return ScopeReview(
            request=request,
            status=status,
            findings=findings,
            matched_items=matched_items,
            unmatched_scope_references=unmatched,
            estimated_scope_delta_hours=request.estimated_hours,
        )

    def finalize(
        self,
        review: ScopeReview,
        reviewer: str,
        decision: ReviewDecision,
    ) -> ScopeReview:
        """
        Record a human review decision.

        A decision is not inferred from a numerical score. The reviewer
        explicitly records the governance decision after examining findings.
        """
        if not reviewer.strip():
            raise ValueError("Reviewer name is required.")

        if decision == ReviewDecision.ACCEPT:
            unresolved = review.unresolved_findings()
            if unresolved:
                raise ValueError(
                    "A review with unresolved findings cannot be accepted."
                )

        review.reviewer = reviewer
        review.decision = decision
        review.reviewed_at = utc_now()
        self.review_history.append(review)
        return review

    def scope_delta_report(self) -> dict[str, float | int]:
        """Aggregate the change requests recorded by this engine."""
        total_hours = sum(
            review.estimated_scope_delta_hours
            for review in self.review_history
        )

        change_control_count = sum(
            review.status == ScopeStatus.REQUIRES_CHANGE_CONTROL
            for review in self.review_history
        )

        return {
            "reviewed_requests": len(self.review_history),
            "change_control_requests": change_control_count,
            "estimated_delta_hours": round(total_hours, 2),
        }


def demonstrate_baseline() -> ScopeBaseline:
    """Build a realistic product-release scope baseline."""
    baseline = ScopeBaseline(
        project_name="Release Governance Portal",
        version="2.3",
        objective=(
            "Deliver repository-based release governance with scope "
            "tracking, review findings, and controlled change requests."
        ),
        items={
            "SCOPE-101": ScopeItem(
                item_id="SCOPE-101",
                name="Release scope dashboard",
                description=(
                    "Display approved release scope items and their current "
                    "implementation state."
                ),
                acceptance_criteria=(
                    "Approved items are visible.",
                    "Each item has a stable identifier.",
                    "Current scope state can be reviewed.",
                ),
                priority="high",
            ),
            "SCOPE-102": ScopeItem(
                item_id="SCOPE-102",
                name="Scope change register",
                description=(
                    "Record proposed changes that may expand or modify "
                    "the approved release scope."
                ),
                acceptance_criteria=(
                    "Requests have unique identifiers.",
                    "Requests record business justification.",
                    "Requests can be reviewed against the baseline.",
                ),
                priority="high",
            ),
            "SCOPE-103": ScopeItem(
                item_id="SCOPE-103",
                name="Scope review findings",
                description=(
                    "Record discrepancies between proposed work and "
                    "the approved scope."
                ),
                acceptance_criteria=(
                    "Findings identify affected scope.",
                    "Findings have severity.",
                    "Findings have resolution guidance.",
                ),
                priority="normal",
            ),
            "SCOPE-104": ScopeItem(
                item_id="SCOPE-104",
                name="Legacy mobile redesign",
                description="Explicitly excluded from this release.",
                acceptance_criteria=(
                    "No redesign work is included in release 2.3.",
                ),
                priority="low",
                excluded=True,
            ),
        },
        exclusions=[
            "Full mobile UI redesign",
            "Unrelated analytics platform migration",
            "New external billing integration",
        ],
        assumptions=[
            "The existing authentication mechanism remains unchanged.",
            "The release remains within the approved governance boundary.",
        ],
    )

    return baseline


def print_review(review: ScopeReview) -> None:
    """Render a human-readable scope review record."""
    print(f"\nChange Request: {review.request.request_id}")
    print(f"Title: {review.request.title}")
    print(f"Status: {review.status.value}")
    print(
        "Matched baseline items:",
        ", ".join(review.matched_items) or "none",
    )
    print(
        "Unmatched references:",
        ", ".join(review.unmatched_scope_references) or "none",
    )
    print(
        f"Estimated scope delta: "
        f"{review.estimated_scope_delta_hours:.1f} hours"
    )

    if review.findings:
        print("Findings:")
        for finding in review.findings:
            print(
                f"  [{finding.severity.value.upper()}] "
                f"{finding.subject}: {finding.description}"
            )
            print(f"    Action: {finding.recommendation}")
    else:
        print("Findings: none")


def demonstrate_scope_review() -> None:
    """Run realistic in-scope, partial-scope, and out-of-scope reviews."""
    baseline = demonstrate_baseline()
    engine = ScopeReviewEngine(baseline)

    requests = [
        ChangeRequest(
            request_id="CR-201",
            title="Improve scope dashboard filtering",
            description=(
                "Add filtering to the existing release scope dashboard "
                "so reviewers can inspect approved items by priority."
            ),
            requested_by="release-manager",
            related_scope_items=("SCOPE-101",),
            estimated_hours=6,
            business_justification=(
                "Reviewers need to isolate high-priority scope items."
            ),
        ),
        ChangeRequest(
            request_id="CR-202",
            title="Add mobile redesign to release",
            description=(
                "Add a new mobile interface and redesign the existing "
                "mobile workflow."
            ),
            requested_by="product-team",
            related_scope_items=("SCOPE-101", "SCOPE-104"),
            estimated_hours=24,
            business_justification=(
                "Improve mobile usability before the release."
            ),
        ),
        ChangeRequest(
            request_id="CR-203",
            title="Introduce external billing integration",
            description=(
                "Add a new external billing integration to the release."
            ),
            requested_by="commercial-team",
            related_scope_items=(),
            estimated_hours=20,
            business_justification=(
                "Support a future commercial workflow."
            ),
        ),
    ]

    reviews = []

    for request in requests:
        review = engine.classify(request)
        print_review(review)
        reviews.append(review)

    # Resolve a legitimate low-risk observation before final acceptance.
    first_review = reviews[0]
    for finding in first_review.findings:
        finding.resolved = True

    engine.finalize(
        first_review,
        reviewer="scope-controller",
        decision=ReviewDecision.ACCEPT,
    )

    engine.finalize(
        reviews[1],
        reviewer="scope-controller",
        decision=ReviewDecision.REVISE_SCOPE,
    )

    engine.finalize(
        reviews[2],
        reviewer="scope-controller",
        decision=ReviewDecision.REJECT,
    )

    print("\nAudit Report")
    for key, value in engine.scope_delta_report().items():
        print(f"{key}: {value}")


def demonstrate_scope_comparison() -> None:
    """
    Show why scope review compares actual requested work with a baseline.

    The same technical implementation can be acceptable in one release and
    out of scope in another release because scope is governed by the approved
    baseline rather than by implementation difficulty alone.
    """
    baseline = ScopeBaseline(
        project_name="Repository Release",
        version="1.0",
        objective="Deliver a controlled release review workflow.",
        items={
            "SCOPE-1": ScopeItem(
                item_id="SCOPE-1",
                name="Release review record",
                description="Store release review decisions.",
                acceptance_criteria=(
                    "A review has a reviewer.",
                    "A review has a decision.",
                ),
            )
        },
        exclusions=["Repository-wide redesign"],
    )

    engine = ScopeReviewEngine(baseline)

    request = ChangeRequest(
        request_id="CR-COMPARE",
        title="Persist review records",
        description=(
            "Implement persistent storage for release review records."
        ),
        requested_by="engineering",
        related_scope_items=("SCOPE-1",),
        estimated_hours=8,
        business_justification="Prevent loss of review decisions.",
    )

    review = engine.classify(request)

    print("\nScope Comparison Example")
    print(f"Baseline: {baseline.version}")
    print(f"Requested work: {request.title}")
    print(f"Classification: {review.status.value}")

    if review.status == ScopeStatus.IN_SCOPE:
        print(
            "The requested capability maps directly to the approved "
            "baseline and does not trigger detected expansion signals."
        )


def demonstrate_edge_cases() -> None:
    """Exercise validation and failure conditions."""
    print("\nEdge Cases")

    invalid_request = ChangeRequest(
        request_id="CR-NEGATIVE",
        title="Invalid effort request",
        description="This request intentionally has invalid effort.",
        requested_by="tester",
        related_scope_items=("SCOPE-101",),
        estimated_hours=-1,
        business_justification="Test validation.",
    )

    engine = ScopeReviewEngine(demonstrate_baseline())

    try:
        engine.classify(invalid_request)
    except ValueError as exc:
        print(f"Validation prevented invalid request: {exc}")

    try:
        review = engine.classify(
            ChangeRequest(
                request_id="CR-UNRESOLVED",
                title="Unresolved finding",
                description="Add a new external billing integration.",
                requested_by="tester",
                related_scope_items=(),
                estimated_hours=4,
                business_justification="Test governance.",
            )
        )
        engine.finalize(
            review,
            reviewer="scope-controller",
            decision=ReviewDecision.ACCEPT,
        )
    except ValueError as exc:
        print(f"Governance prevented unsafe acceptance: {exc}")


def main() -> None:
    """Execute the complete scope-review demonstration."""
    print("SCOPE REVIEW AND SCOPE MANAGEMENT")
    print("=" * 42)

    demonstrate_scope_review()
    demonstrate_scope_comparison()
    demonstrate_edge_cases()

    print("\nKey implementation boundary")
    print(
        "This program evaluates whether requested work belongs to an "
        "approved scope baseline. It does not treat technical correctness "
        "as proof that the work is within scope."
    )


if __name__ == "__main__":
    main()
