from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from collections import defaultdict
from statistics import mean
from typing import Optional
import json
import logging
import re
import uuid


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("communication_review")


class CommunicationType(Enum):
    EMAIL = "email"
    MEETING = "meeting"
    REPORT = "report"
    PRESENTATION = "presentation"
    NOTICE = "notice"
    INSTANT_MESSAGE = "instant_message"


class ReviewStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewDecision(Enum):
    APPROVE = "approve"
    REVISE = "revise"
    REJECT = "reject"


@dataclass
class Stakeholder:
    stakeholder_id: str
    name: str
    role: str
    department: str
    active: bool = True


@dataclass
class Communication:
    communication_id: str
    title: str
    communication_type: CommunicationType
    sender_id: str
    recipients: list[str]
    subject: str
    content: str
    objectives: list[str]
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: ReviewStatus = ReviewStatus.DRAFT
    version: int = 1
    sensitivity: str = "internal"
    acknowledgement_required: bool = False
    acknowledgement_count: int = 0
    read_count: int = 0
    delivery_count: int = 0


@dataclass
class ReviewComment:
    comment_id: str
    communication_id: str
    reviewer_id: str
    criterion: str
    comment: str
    severity: Severity
    resolved: bool = False


@dataclass
class ReviewRecord:
    communication_id: str
    reviewer_id: str
    decision: ReviewDecision
    score: float
    feedback: str
    reviewed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class ReviewPolicy:
    minimum_score: float = 70.0
    minimum_delivery_rate: float = 95.0
    minimum_acknowledgement_rate: float = 80.0
    require_objectives: bool = True
    require_reviewer: bool = True
    block_critical_comments: bool = True
    mandatory_criteria: tuple[str, ...] = (
        "clarity",
        "accuracy",
        "completeness",
        "audience_alignment",
        "timeliness",
        "actionability",
        "professionalism",
    )


class CommunicationError(Exception):
    pass


class ValidationError(CommunicationError):
    pass


class AuthorizationError(CommunicationError):
    pass


class WorkflowError(CommunicationError):
    pass


class CommunicationManager:
    def __init__(self, policy: Optional[ReviewPolicy] = None):
        self.policy = policy or ReviewPolicy()
        self.stakeholders: dict[str, Stakeholder] = {}
        self.communications: dict[str, Communication] = {}
        self.reviews: list[ReviewRecord] = []
        self.comments: list[ReviewComment] = []
        self.audit_log: list[dict] = []

    def _audit(self, action: str, entity_id: str, actor: str):
        self.audit_log.append({
            "event_id": str(uuid.uuid4()),
            "action": action,
            "entity_id": entity_id,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def register_stakeholder(self, stakeholder: Stakeholder):
        if stakeholder.stakeholder_id in self.stakeholders:
            raise ValidationError("Stakeholder ID already exists.")

        if not stakeholder.name.strip():
            raise ValidationError("Stakeholder name is required.")

        self.stakeholders[stakeholder.stakeholder_id] = stakeholder

    def create_communication(
        self,
        title: str,
        communication_type: CommunicationType,
        sender_id: str,
        recipients: list[str],
        subject: str,
        content: str,
        objectives: list[str],
        sensitivity: str = "internal",
        acknowledgement_required: bool = False,
    ) -> Communication:

        if sender_id not in self.stakeholders:
            raise ValidationError("Unknown sender.")

        if not self.stakeholders[sender_id].active:
            raise AuthorizationError("Inactive sender.")

        if not recipients:
            raise ValidationError("At least one recipient is required.")

        if len(recipients) != len(set(recipients)):
            raise ValidationError("Duplicate recipients are not allowed.")

        for recipient in recipients:
            if recipient not in self.stakeholders:
                raise ValidationError(
                    f"Unknown recipient: {recipient}"
                )
            if not self.stakeholders[recipient].active:
                raise ValidationError(
                    f"Inactive recipient: {recipient}"
                )

        if not title.strip() or not subject.strip():
            raise ValidationError("Title and subject are required.")

        if not content.strip():
            raise ValidationError("Communication content is required.")

        if sensitivity not in {"public", "internal", "confidential", "restricted"}:
            raise ValidationError("Invalid sensitivity classification.")

        if self.policy.require_objectives and not objectives:
            raise ValidationError("At least one communication objective is required.")

        if len(content) > 100_000:
            raise ValidationError("Communication exceeds maximum content size.")

        communication = Communication(
            communication_id=str(uuid.uuid4()),
            title=title.strip(),
            communication_type=communication_type,
            sender_id=sender_id,
            recipients=recipients.copy(),
            subject=subject.strip(),
            content=content.strip(),
            objectives=objectives.copy(),
            sensitivity=sensitivity,
            acknowledgement_required=acknowledgement_required,
        )

        self.communications[communication.communication_id] = communication
        self._audit(
            "communication_created",
            communication.communication_id,
            sender_id
        )
        return communication

    def submit_for_review(self, communication_id: str, actor_id: str):
        communication = self._get_communication(communication_id)

        if communication.sender_id != actor_id:
            raise AuthorizationError("Only the sender can submit the communication.")

        if communication.status not in {
            ReviewStatus.DRAFT,
            ReviewStatus.REVISION_REQUIRED,
        }:
            raise WorkflowError("Communication cannot be submitted in its current state.")

        communication.status = ReviewStatus.SUBMITTED
        self._audit("submitted_for_review", communication_id, actor_id)

    def start_review(self, communication_id: str, reviewer_id: str):
        communication = self._get_communication(communication_id)
        reviewer = self._get_stakeholder(reviewer_id)

        if not reviewer.active:
            raise AuthorizationError("Reviewer is inactive.")

        if reviewer_id == communication.sender_id:
            raise AuthorizationError("Self-review is not permitted.")

        if communication.status not in {
            ReviewStatus.SUBMITTED,
            ReviewStatus.UNDER_REVIEW,
        }:
            raise WorkflowError("Communication is not available for review.")

        communication.status = ReviewStatus.UNDER_REVIEW
        self._audit("review_started", communication_id, reviewer_id)

    def add_comment(
        self,
        communication_id: str,
        reviewer_id: str,
        criterion: str,
        comment: str,
        severity: Severity,
    ) -> ReviewComment:

        communication = self._get_communication(communication_id)
        self._get_stakeholder(reviewer_id)

        if reviewer_id == communication.sender_id:
            raise AuthorizationError("Sender cannot review their own communication.")

        if communication.status != ReviewStatus.UNDER_REVIEW:
            raise WorkflowError("Comments require an active review.")

        if not criterion.strip() or not comment.strip():
            raise ValidationError("Criterion and comment are required.")

        review_comment = ReviewComment(
            comment_id=str(uuid.uuid4()),
            communication_id=communication_id,
            reviewer_id=reviewer_id,
            criterion=criterion.strip().lower(),
            comment=comment.strip(),
            severity=severity,
        )

        self.comments.append(review_comment)
        self._audit("review_comment_added", communication_id, reviewer_id)
        return review_comment

    def resolve_comment(self, comment_id: str, actor_id: str):
        comment = next(
            (item for item in self.comments
             if item.comment_id == comment_id),
            None
        )

        if comment is None:
            raise ValidationError("Review comment not found.")

        communication = self._get_communication(comment.communication_id)

        if actor_id != communication.sender_id:
            raise AuthorizationError("Only the communication owner can resolve comments.")

        comment.resolved = True
        self._audit("comment_resolved", comment_id, actor_id)

    @staticmethod
    def calculate_review_score(scores: dict[str, float]) -> float:
        if not scores:
            raise ValidationError("Review scores cannot be empty.")

        for criterion, score in scores.items():
            if not criterion.strip():
                raise ValidationError("Criterion names cannot be empty.")
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                raise ValidationError("Scores must be numeric.")
            if not 0 <= score <= 100:
                raise ValidationError("Scores must be between 0 and 100.")

        return round(mean(scores.values()), 2)

    def record_review(
        self,
        communication_id: str,
        reviewer_id: str,
        scores: dict[str, float],
        decision: ReviewDecision,
        feedback: str,
    ) -> ReviewRecord:

        communication = self._get_communication(communication_id)
        reviewer = self._get_stakeholder(reviewer_id)

        if not reviewer.active:
            raise AuthorizationError("Reviewer is inactive.")

        if reviewer_id == communication.sender_id:
            raise AuthorizationError("Self-review is prohibited.")

        if communication.status != ReviewStatus.UNDER_REVIEW:
            raise WorkflowError("Review is not active.")

        if any(
            review.communication_id == communication_id
            and review.reviewer_id == reviewer_id
            and review.reviewed_at
            for review in self.reviews
        ):
            raise WorkflowError("Reviewer has already submitted a decision.")

        missing = set(self.policy.mandatory_criteria) - set(scores)
        if missing:
            raise ValidationError(
                f"Missing mandatory criteria: {sorted(missing)}"
            )

        score = self.calculate_review_score(scores)

        if decision == ReviewDecision.APPROVE and score < self.policy.minimum_score:
            raise ValidationError("Approval score is below the policy threshold.")

        record = ReviewRecord(
            communication_id=communication_id,
            reviewer_id=reviewer_id,
            decision=decision,
            score=score,
            feedback=feedback.strip(),
        )

        self.reviews.append(record)
        self._audit("review_recorded", communication_id, reviewer_id)

        if decision == ReviewDecision.REJECT:
            communication.status = ReviewStatus.REJECTED
        elif decision == ReviewDecision.REVISE:
            communication.status = ReviewStatus.REVISION_REQUIRED

        return record

    def evaluate_communication(self, communication_id: str) -> dict:
        communication = self._get_communication(communication_id)

        reviews = [
            review for review in self.reviews
            if review.communication_id == communication_id
        ]

        comments = [
            comment for comment in self.comments
            if comment.communication_id == communication_id
        ]

        unresolved_critical = [
            comment for comment in comments
            if comment.severity == Severity.CRITICAL
            and not comment.resolved
        ]

        approved_reviewers = {
            review.reviewer_id
            for review in reviews
            if review.decision == ReviewDecision.APPROVE
            and review.score >= self.policy.minimum_score
            and self.stakeholders[review.reviewer_id].active
        }

        rejected = any(
            review.decision == ReviewDecision.REJECT
            for review in reviews
        )

        revision_requested = any(
            review.decision == ReviewDecision.REVISE
            for review in reviews
        )

        average_score = (
            round(mean(review.score for review in reviews), 2)
            if reviews else 0.0
        )

        reasons = []

        if not approved_reviewers and self.policy.require_reviewer:
            reasons.append("No valid reviewer approval.")

        if average_score < self.policy.minimum_score:
            reasons.append("Average review score is below threshold.")

        if rejected:
            reasons.append("A reviewer rejected the communication.")

        if revision_requested:
            reasons.append("A reviewer requested revisions.")

        if unresolved_critical and self.policy.block_critical_comments:
            reasons.append("Unresolved critical comments exist.")

        return {
            "communication_id": communication_id,
            "average_score": average_score,
            "approved_reviewers": sorted(approved_reviewers),
            "review_count": len(reviews),
            "unresolved_comments": sum(
                not comment.resolved for comment in comments
            ),
            "unresolved_critical_comments": len(unresolved_critical),
            "eligible": not reasons,
            "reasons": reasons,
        }

    def approve_publication(self, communication_id: str, actor_id: str):
        communication = self._get_communication(communication_id)

        if actor_id != communication.sender_id:
            raise AuthorizationError("Only the sender can authorize publication.")

        result = self.evaluate_communication(communication_id)

        if not result["eligible"]:
            raise WorkflowError(
                "Publication blocked: " + "; ".join(result["reasons"])
            )

        communication.status = ReviewStatus.APPROVED
        self._audit("publication_approved", communication_id, actor_id)

    def record_delivery(
        self,
        communication_id: str,
        delivered: int,
        read: int,
        acknowledged: int,
    ):
        communication = self._get_communication(communication_id)

        if communication.status != ReviewStatus.PUBLISHED:
            raise WorkflowError("Only published communications can record delivery.")

        recipient_count = len(communication.recipients)

        if not (
            0 <= acknowledged <= read <= delivered <= recipient_count
        ):
            raise ValidationError("Invalid delivery, read, or acknowledgement counts.")

        communication.delivery_count = delivered
        communication.read_count = read
        communication.acknowledgement_count = acknowledged

        self._audit(
            "delivery_metrics_recorded",
            communication_id,
            "system"
        )

    def publish(self, communication_id: str, actor_id: str):
        communication = self._get_communication(communication_id)

        if actor_id != communication.sender_id:
            raise AuthorizationError("Only the sender can publish.")

        if communication.status != ReviewStatus.APPROVED:
            raise WorkflowError("Communication must be approved before publication.")

        communication.status = ReviewStatus.PUBLISHED
        self._audit("communication_published", communication_id, actor_id)

    def update_content(
        self,
        communication_id: str,
        actor_id: str,
        content: str,
    ):
        communication = self._get_communication(communication_id)

        if actor_id != communication.sender_id:
            raise AuthorizationError("Only the sender can update content.")

        if communication.status in {
            ReviewStatus.PUBLISHED,
            ReviewStatus.ARCHIVED,
        }:
            raise WorkflowError("Published or archived content cannot be edited.")

        if not content.strip():
            raise ValidationError("Content cannot be empty.")

        communication.content = content.strip()
        communication.version += 1
        communication.status = ReviewStatus.REVISION_REQUIRED

        # Previous approvals are retained as history but cannot authorize
        # the revised version.
        self.reviews = [
            review for review in self.reviews
            if review.communication_id != communication_id
        ]

        self._audit("content_updated", communication_id, actor_id)

    def archive(self, communication_id: str, actor_id: str):
        communication = self._get_communication(communication_id)

        if actor_id != communication.sender_id:
            raise AuthorizationError("Only the sender can archive.")

        if communication.status not in {
            ReviewStatus.PUBLISHED,
            ReviewStatus.REJECTED,
        }:
            raise WorkflowError("Communication cannot be archived in this state.")

        communication.status = ReviewStatus.ARCHIVED
        self._audit("communication_archived", communication_id, actor_id)

    def communication_metrics(self, communication_id: str) -> dict:
        communication = self._get_communication(communication_id)
        recipients = len(communication.recipients)

        delivery_rate = (
            communication.delivery_count / recipients * 100
            if recipients else 0
        )

        read_rate = (
            communication.read_count / recipients * 100
            if recipients else 0
        )

        acknowledgement_rate = (
            communication.acknowledgement_count / recipients * 100
            if recipients else 0
        )

        return {
            "communication_id": communication_id,
            "recipients": recipients,
            "delivery_rate": round(delivery_rate, 2),
            "read_rate": round(read_rate, 2),
            "acknowledgement_rate": round(acknowledgement_rate, 2),
            "delivery_satisfactory": (
                delivery_rate >= self.policy.minimum_delivery_rate
            ),
            "acknowledgement_satisfactory": (
                not communication.acknowledgement_required
                or acknowledgement_rate >= self.policy.minimum_acknowledgement_rate
            ),
        }

    def management_report(self) -> dict:
        status_counts = defaultdict(int)
        type_counts = defaultdict(int)

        for communication in self.communications.values():
            status_counts[communication.status.value] += 1
            type_counts[communication.communication_type.value] += 1

        return {
            "total_communications": len(self.communications),
            "total_reviews": len(self.reviews),
            "total_comments": len(self.comments),
            "status_distribution": dict(status_counts),
            "type_distribution": dict(type_counts),
            "audit_events": len(self.audit_log),
        }

    def _get_communication(self, communication_id: str) -> Communication:
        if communication_id not in self.communications:
            raise ValidationError("Communication not found.")
        return self.communications[communication_id]

    def _get_stakeholder(self, stakeholder_id: str) -> Stakeholder:
        if stakeholder_id not in self.stakeholders:
            raise ValidationError("Stakeholder not found.")
        return self.stakeholders[stakeholder_id]


def demonstrate():
    manager = CommunicationManager()

    stakeholders = [
        Stakeholder("S001", "Project Manager", "manager", "Operations"),
        Stakeholder("S002", "Quality Officer", "reviewer", "Quality"),
        Stakeholder("S003", "Technical Lead", "reviewer", "Technology"),
        Stakeholder("S004", "Department Head", "recipient", "Management"),
        Stakeholder("S005", "Field Coordinator", "recipient", "Operations"),
    ]

    for stakeholder in stakeholders:
        manager.register_stakeholder(stakeholder)

    communication = manager.create_communication(
        title="Monthly Operational Performance",
        communication_type=CommunicationType.REPORT,
        sender_id="S001",
        recipients=["S004", "S005"],
        subject="Monthly Operational Performance Review",
        content=(
            "The monthly operational review identifies completed activities, "
            "pending actions, resource constraints, and corrective measures."
        ),
        objectives=[
            "Communicate performance",
            "Identify unresolved issues",
            "Assign corrective actions",
        ],
        acknowledgement_required=True,
    )

    communication_id = communication.communication_id

    manager.submit_for_review(communication_id, "S001")
    manager.start_review(communication_id, "S002")

    manager.add_comment(
        communication_id,
        "S002",
        "accuracy",
        "Verify the reported completion figures against source records.",
        Severity.MEDIUM,
    )

    manager.record_review(
        communication_id,
        "S002",
        {
            "clarity": 90,
            "accuracy": 95,
            "completeness": 88,
            "audience_alignment": 92,
            "timeliness": 90,
            "actionability": 85,
            "professionalism": 95,
        },
        ReviewDecision.APPROVE,
        "The report meets the required communication standards.",
    )

    manager.start_review(communication_id, "S003")

    manager.record_review(
        communication_id,
        "S003",
        {
            "clarity": 88,
            "accuracy": 92,
            "completeness": 90,
            "audience_alignment": 89,
            "timeliness": 95,
            "actionability": 90,
            "professionalism": 94,
        },
        ReviewDecision.APPROVE,
        "Technical information is sufficiently clear and actionable.",
    )

    print("\nREVIEW EVALUATION")
    print(json.dumps(
        manager.evaluate_communication(communication_id),
        indent=2
    ))

    manager.approve_publication(communication_id, "S001")
    manager.publish(communication_id, "S001")

    manager.record_delivery(
        communication_id,
        delivered=2,
        read=2,
        acknowledged=2,
    )

    print("\nCOMMUNICATION PERFORMANCE")
    print(json.dumps(
        manager.communication_metrics(communication_id),
        indent=2
    ))

    print("\nMANAGEMENT REPORT")
    print(json.dumps(manager.management_report(), indent=2))

    print("\nAUDIT EVENTS:", len(manager.audit_log))


if __name__ == "__main__":
    try:
        demonstrate()
    except CommunicationError as error:
        logger.error("Workflow failure: %s", error)
        raise
