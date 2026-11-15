#!/usr/bin/env python3
"""
Stakeholder Communication Management System

Models stakeholder relationships, communication planning, message delivery,
acknowledgements, feedback, escalation, risk monitoring, and reporting.

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("stakeholder_communication")


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Influence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Engagement(str, Enum):
    UNAWARE = "unaware"
    RESISTANT = "resistant"
    NEUTRAL = "neutral"
    SUPPORTIVE = "supportive"
    LEADING = "leading"


class Channel(str, Enum):
    EMAIL = "email"
    MEETING = "meeting"
    REPORT = "report"
    PHONE = "phone"
    COLLABORATION = "collaboration"


class MessageStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class FeedbackSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class Stakeholder:
    stakeholder_id: str
    name: str
    role: str
    organization: str
    email: str
    influence: Influence
    interest: Influence
    engagement: Engagement
    preferred_channel: Channel
    communication_frequency_days: int = 7
    active: bool = True

    def __post_init__(self):
        if not self.name.strip() or not self.role.strip():
            raise ValueError("Stakeholder name and role are required.")

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", self.email):
            raise ValueError(f"Invalid email address: {self.email}")

        if self.communication_frequency_days < 1:
            raise ValueError("Communication frequency must be positive.")

    @property
    def power_interest_category(self) -> str:
        if self.influence == Influence.HIGH and self.interest == Influence.HIGH:
            return "manage_closely"

        if self.influence == Influence.HIGH:
            return "keep_satisfied"

        if self.interest == Influence.HIGH:
            return "keep_informed"

        return "monitor"


@dataclass
class CommunicationPlan:
    plan_id: str
    stakeholder_id: str
    objective: str
    key_message: str
    channel: Channel
    frequency_days: int
    responsible_person: str
    next_communication: datetime
    priority: Priority
    success_measure: str
    active: bool = True

    def __post_init__(self):
        if not self.objective.strip() or not self.key_message.strip():
            raise ValueError("Communication objective and message are required.")

        if self.frequency_days < 1:
            raise ValueError("Frequency must be at least one day.")


@dataclass
class Communication:
    communication_id: str
    stakeholder_id: str
    plan_id: str
    subject: str
    body: str
    channel: Channel
    priority: Priority
    status: MessageStatus = MessageStatus.DRAFT
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    attachments: list[str] = field(default_factory=list)


@dataclass
class Feedback:
    feedback_id: str
    stakeholder_id: str
    communication_id: str
    sentiment: FeedbackSentiment
    content: str
    received_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    resolved: bool = False


class StakeholderSystem:
    def __init__(self):
        self.stakeholders: dict[str, Stakeholder] = {}
        self.plans: dict[str, CommunicationPlan] = {}
        self.communications: dict[str, Communication] = {}
        self.feedback: dict[str, Feedback] = {}
        self.audit_log: list[dict] = []

    def _audit(self, action: str, entity_id: str, details: str):
        self.audit_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "entity_id": entity_id,
            "details": details
        })

    def add_stakeholder(self, stakeholder: Stakeholder):
        if stakeholder.stakeholder_id in self.stakeholders:
            raise ValueError("Duplicate stakeholder ID.")

        if any(
            s.email.lower() == stakeholder.email.lower()
            for s in self.stakeholders.values()
        ):
            raise ValueError("Stakeholder email already exists.")

        self.stakeholders[stakeholder.stakeholder_id] = stakeholder
        self._audit("STAKEHOLDER_CREATED", stakeholder.stakeholder_id,
                    stakeholder.name)

    def create_plan(self, plan: CommunicationPlan):
        stakeholder = self.stakeholders.get(plan.stakeholder_id)

        if stakeholder is None or not stakeholder.active:
            raise ValueError("Stakeholder does not exist or is inactive.")

        if plan.plan_id in self.plans:
            raise ValueError("Duplicate communication plan ID.")

        self.plans[plan.plan_id] = plan
        self._audit("PLAN_CREATED", plan.plan_id, plan.objective)

    def create_communication(
        self,
        stakeholder_id: str,
        plan_id: str,
        subject: str,
        body: str,
        priority: Priority,
        deadline: Optional[datetime] = None
    ) -> Communication:

        stakeholder = self.stakeholders.get(stakeholder_id)
        plan = self.plans.get(plan_id)

        if stakeholder is None or not stakeholder.active:
            raise ValueError("Invalid or inactive stakeholder.")

        if plan is None or not plan.active:
            raise ValueError("Invalid or inactive communication plan.")

        if plan.stakeholder_id != stakeholder_id:
            raise ValueError("Plan does not belong to this stakeholder.")

        if not subject.strip() or not body.strip():
            raise ValueError("Subject and body cannot be empty.")

        if deadline and deadline.tzinfo is None:
            raise ValueError("Deadline must be timezone-aware.")

        communication = Communication(
            communication_id=str(uuid.uuid4()),
            stakeholder_id=stakeholder_id,
            plan_id=plan_id,
            subject=subject.strip(),
            body=body.strip(),
            channel=plan.channel,
            priority=priority,
            deadline=deadline
        )

        self.communications[communication.communication_id] = communication

        self._audit(
            "COMMUNICATION_DRAFTED",
            communication.communication_id,
            subject
        )

        return communication

    def approve_communication(self, communication_id: str):
        communication = self._get_communication(communication_id)

        if communication.status != MessageStatus.DRAFT:
            raise ValueError("Only draft communications can be approved.")

        communication.status = MessageStatus.APPROVED

        self._audit("COMMUNICATION_APPROVED", communication_id, "Approved")

    def send_communication(self, communication_id: str):
        communication = self._get_communication(communication_id)

        if communication.status != MessageStatus.APPROVED:
            raise ValueError("Communication requires approval before sending.")

        stakeholder = self.stakeholders[communication.stakeholder_id]

        if not stakeholder.active:
            raise ValueError("Cannot contact inactive stakeholder.")

        # This simulator records delivery intent; it does not send real email.
        communication.status = MessageStatus.SENT
        communication.sent_at = datetime.now(timezone.utc)

        self._audit(
            "COMMUNICATION_SENT",
            communication_id,
            f"Channel={communication.channel.value}"
        )

    def acknowledge(self, communication_id: str):
        communication = self._get_communication(communication_id)

        if communication.status != MessageStatus.SENT:
            raise ValueError("Only sent communications can be acknowledged.")

        communication.status = MessageStatus.ACKNOWLEDGED
        communication.acknowledged_at = datetime.now(timezone.utc)

        self._audit("ACKNOWLEDGED", communication_id, "Receipt confirmed")

    def add_feedback(
        self,
        stakeholder_id: str,
        communication_id: str,
        sentiment: FeedbackSentiment,
        content: str
    ) -> Feedback:

        communication = self._get_communication(communication_id)

        if communication.stakeholder_id != stakeholder_id:
            raise ValueError("Feedback stakeholder does not match communication.")

        if communication.status not in (
            MessageStatus.SENT,
            MessageStatus.ACKNOWLEDGED
        ):
            raise ValueError("Feedback requires a sent communication.")

        if not content.strip():
            raise ValueError("Feedback content cannot be empty.")

        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            stakeholder_id=stakeholder_id,
            communication_id=communication_id,
            sentiment=sentiment,
            content=content.strip()
        )

        self.feedback[feedback.feedback_id] = feedback

        self._audit("FEEDBACK_RECEIVED", feedback.feedback_id,
                    sentiment.value)

        if sentiment == FeedbackSentiment.NEGATIVE:
            self._audit(
                "NEGATIVE_FEEDBACK_FLAGGED",
                feedback.feedback_id,
                "Requires review and response"
            )

        return feedback

    def escalate_overdue(self, reference_time: Optional[datetime] = None):
        now = reference_time or datetime.now(timezone.utc)

        if now.tzinfo is None:
            raise ValueError("Reference time must be timezone-aware.")

        escalated = []

        for communication in self.communications.values():
            if (
                communication.deadline
                and communication.deadline < now
                and communication.status == MessageStatus.SENT
            ):
                communication.status = MessageStatus.ESCALATED
                escalated.append(communication.communication_id)

                self._audit(
                    "COMMUNICATION_ESCALATED",
                    communication.communication_id,
                    "Acknowledgement deadline exceeded"
                )

        return escalated

    def generate_engagement_report(self) -> dict:
        active_stakeholders = [
            s for s in self.stakeholders.values() if s.active
        ]

        statuses = {
            status.value: sum(
                c.status == status
                for c in self.communications.values()
            )
            for status in MessageStatus
        }

        sentiments = {
            sentiment.value: sum(
                f.sentiment == sentiment
                for f in self.feedback.values()
            )
            for sentiment in FeedbackSentiment
        }

        categories = {}

        for stakeholder in active_stakeholders:
            category = stakeholder.power_interest_category
            categories[category] = categories.get(category, 0) + 1

        sent = sum(
            c.sent_at is not None
            for c in self.communications.values()
        )

        acknowledged = sum(
            c.acknowledged_at is not None
            for c in self.communications.values()
        )

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "active_stakeholders": len(active_stakeholders),
            "power_interest_distribution": categories,
            "communication_status": statuses,
            "feedback_sentiment": sentiments,
            "acknowledgement_rate": (
                round(acknowledged / sent * 100, 2)
                if sent else 0.0
            ),
            "unresolved_negative_feedback": sum(
                f.sentiment == FeedbackSentiment.NEGATIVE and not f.resolved
                for f in self.feedback.values()
            )
        }

    def save(self, filename: str):
        """Write a complete JSON snapshot using atomic replacement."""

        destination = Path(filename)
        temporary = destination.with_suffix(destination.suffix + ".tmp")

        snapshot = {
            "stakeholders": [
                asdict(s) for s in self.stakeholders.values()
            ],
            "plans": [
                asdict(p) for p in self.plans.values()
            ],
            "communications": [
                asdict(c) for c in self.communications.values()
            ],
            "feedback": [
                asdict(f) for f in self.feedback.values()
            ],
            "audit_log": self.audit_log
        }

        def encode(value):
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, datetime):
                return value.isoformat()
            raise TypeError(f"Unsupported JSON value: {type(value)}")

        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            with temporary.open("w", encoding="utf-8") as file:
                json.dump(snapshot, file, indent=2, default=encode)
                file.flush()

            temporary.replace(destination)

        except OSError:
            temporary.unlink(missing_ok=True)
            raise

    def _get_communication(self, communication_id: str) -> Communication:
        communication = self.communications.get(communication_id)

        if communication is None:
            raise KeyError(f"Communication not found: {communication_id}")

        return communication


def build_demo() -> StakeholderSystem:
    system = StakeholderSystem()

    stakeholders = [
        Stakeholder(
            "STK-001",
            "Ananya Sharma",
            "Project Sponsor",
            "Enterprise Operations",
            "ananya@example.com",
            Influence.HIGH,
            Influence.HIGH,
            Engagement.SUPPORTIVE,
            Channel.MEETING,
            7
        ),
        Stakeholder(
            "STK-002",
            "Rahul Verma",
            "Technical Lead",
            "Engineering",
            "rahul@example.com",
            Influence.HIGH,
            Influence.HIGH,
            Engagement.LEADING,
            Channel.COLLABORATION,
            3
        ),
        Stakeholder(
            "STK-003",
            "Priya Singh",
            "Business User",
            "Operations",
            "priya@example.com",
            Influence.MEDIUM,
            Influence.HIGH,
            Engagement.NEUTRAL,
            Channel.EMAIL,
            5
        ),
        Stakeholder(
            "STK-004",
            "Vikram Rao",
            "Compliance Officer",
            "Governance",
            "vikram@example.com",
            Influence.HIGH,
            Influence.MEDIUM,
            Engagement.NEUTRAL,
            Channel.REPORT,
            14
        )
    ]

    for stakeholder in stakeholders:
        system.add_stakeholder(stakeholder)

    plan = CommunicationPlan(
        plan_id="PLAN-001",
        stakeholder_id="STK-001",
        objective="Provide project progress and obtain sponsor decisions.",
        key_message="The project has completed its integration milestone.",
        channel=Channel.EMAIL,
        frequency_days=7,
        responsible_person="Project Manager",
        next_communication=datetime.now(timezone.utc) + timedelta(days=7),
        priority=Priority.HIGH,
        success_measure="Sponsor acknowledgement and recorded decisions."
    )

    system.create_plan(plan)

    return system


def main():
    system = build_demo()

    communication = system.create_communication(
        stakeholder_id="STK-001",
        plan_id="PLAN-001",
        subject="Weekly Project Status",
        body=(
            "Integration testing has been completed. "
            "Three issues remain under investigation. "
            "A sponsor decision is requested on the deployment date."
        ),
        priority=Priority.HIGH,
        deadline=datetime.now(timezone.utc) + timedelta(days=1)
    )

    system.approve_communication(communication.communication_id)
    system.send_communication(communication.communication_id)

    system.acknowledge(communication.communication_id)

    system.add_feedback(
        "STK-001",
        communication.communication_id,
        FeedbackSentiment.POSITIVE,
        "Progress is satisfactory. Confirm the deployment risk assessment."
    )

    report = system.generate_engagement_report()

    print("\nSTAKEHOLDER COMMUNICATION REPORT")
    print(json.dumps(report, indent=2))

    print("\nCOMMUNICATION RECORD")
    print(json.dumps(
        asdict(communication),
        indent=2,
        default=lambda x: x.value if isinstance(x, Enum)
        else x.isoformat() if isinstance(x, datetime)
        else str(x)
    ))

    system.save("stakeholder_communication.json")
    print("\nSnapshot saved to stakeholder_communication.json")

    # Validate important lifecycle and reporting invariants.
    assert communication.status == MessageStatus.ACKNOWLEDGED
    assert report["active_stakeholders"] == 4
    assert report["acknowledgement_rate"] == 100.0

    print("All demonstration assertions passed.")


if __name__ == "__main__":
    main()
