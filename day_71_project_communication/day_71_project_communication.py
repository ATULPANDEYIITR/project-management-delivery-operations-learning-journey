"""
PROJECT COMMUNICATION MANAGEMENT
Introduction to Project Communication

A self-contained project communication management simulator.

Features:
- Stakeholder identification and classification
- Communication planning
- Communication channels and frequency
- Message creation and distribution
- Audience and confidentiality validation
- Message acknowledgements
- Meeting records and decisions
- Action-item tracking
- Escalation of overdue communication
- Communication effectiveness metrics
- JSON audit export
- Automated validation and tests

Run:
    python project_communication.py
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("project_communication")


# ============================================================
# ENUMERATIONS
# ============================================================

class StakeholderRole(Enum):
    PROJECT_MANAGER = "project_manager"
    SPONSOR = "sponsor"
    TEAM_MEMBER = "team_member"
    CLIENT = "client"
    VENDOR = "vendor"
    EXECUTIVE = "executive"


class CommunicationChannel(Enum):
    EMAIL = "email"
    MEETING = "meeting"
    CHAT = "chat"
    REPORT = "report"
    PHONE = "phone"
    PROJECT_PORTAL = "project_portal"


class CommunicationPurpose(Enum):
    INFORMATION = "information"
    STATUS_UPDATE = "status_update"
    DECISION = "decision"
    REQUEST = "request"
    ESCALATION = "escalation"
    ANNOUNCEMENT = "announcement"


class Confidentiality(Enum):
    PUBLIC = 1
    INTERNAL = 2
    CONFIDENTIAL = 3
    RESTRICTED = 4


class MessageStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    ARCHIVED = "archived"


class ActionStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


# ============================================================
# DOMAIN EXCEPTIONS
# ============================================================

class CommunicationError(Exception):
    """Base exception for communication operations."""


class ValidationError(CommunicationError):
    """Raised when communication data is invalid."""


class AuthorizationError(CommunicationError):
    """Raised when a recipient is not authorized."""


class NotFoundError(CommunicationError):
    """Raised when a requested record does not exist."""


class StateTransitionError(CommunicationError):
    """Raised when an invalid state transition is requested."""


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Stakeholder:
    stakeholder_id: str
    name: str
    email: str
    role: StakeholderRole
    influence: int
    interest: int
    confidentiality_clearance: Confidentiality
    active: bool = True

    def __post_init__(self):
        if not self.name.strip():
            raise ValidationError("Stakeholder name is required.")

        if "@" not in self.email or self.email.startswith("@"):
            raise ValidationError("A valid email address is required.")

        if not 1 <= self.influence <= 5:
            raise ValidationError("Influence must be between 1 and 5.")

        if not 1 <= self.interest <= 5:
            raise ValidationError("Interest must be between 1 and 5.")

    @property
    def engagement_priority(self) -> str:
        score = self.influence * self.interest

        if score >= 16:
            return "MANAGE_CLOSLY"
        if self.influence >= 4:
            return "KEEP_SATISFIED"
        if self.interest >= 4:
            return "KEEP_INFORMED"

        return "MONITOR"


@dataclass
class CommunicationPlan:
    plan_id: str
    stakeholder_id: str
    channel: CommunicationChannel
    frequency: str
    purpose: CommunicationPurpose
    owner_id: str
    next_communication: datetime
    active: bool = True

    def __post_init__(self):
        allowed_frequencies = {
            "daily",
            "weekly",
            "biweekly",
            "monthly",
            "milestone",
            "on_demand",
        }

        if self.frequency not in allowed_frequencies:
            raise ValidationError("Unsupported communication frequency.")

        if self.next_communication.tzinfo is None:
            raise ValidationError("Communication dates must include timezone information.")


@dataclass
class Message:
    message_id: str
    sender_id: str
    subject: str
    body: str
    channel: CommunicationChannel
    purpose: CommunicationPurpose
    confidentiality: Confidentiality
    recipient_ids: list[str]
    created_at: datetime
    status: MessageStatus = MessageStatus.DRAFT
    acknowledged_by: set[str] = field(default_factory=set)
    sent_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.subject.strip():
            raise ValidationError("Message subject cannot be empty.")

        if not self.body.strip():
            raise ValidationError("Message body cannot be empty.")

        if not self.recipient_ids:
            raise ValidationError("At least one recipient is required.")

        if len(self.recipient_ids) != len(set(self.recipient_ids)):
            raise ValidationError("Duplicate recipients are not permitted.")


@dataclass
class Meeting:
    meeting_id: str
    title: str
    organizer_id: str
    participant_ids: list[str]
    scheduled_at: datetime
    agenda: list[str]
    minutes: str = ""
    completed: bool = False

    def __post_init__(self):
        if not self.title.strip():
            raise ValidationError("Meeting title is required.")

        if not self.participant_ids:
            raise ValidationError("A meeting requires participants.")

        if self.scheduled_at.tzinfo is None:
            raise ValidationError("Meeting time must include timezone information.")


@dataclass
class Decision:
    decision_id: str
    meeting_id: str
    description: str
    owner_id: str
    decided_at: datetime
    approved: bool


@dataclass
class ActionItem:
    action_id: str
    description: str
    assigned_to: str
    created_by: str
    due_date: datetime
    status: ActionStatus = ActionStatus.OPEN
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.description.strip():
            raise ValidationError("Action description is required.")

        if self.due_date.tzinfo is None:
            raise ValidationError("Action due date must include timezone information.")


@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    entity_id: str
    actor_id: str
    timestamp: datetime
    details: dict


# ============================================================
# COMMUNICATION MANAGEMENT SYSTEM
# ============================================================

class ProjectCommunicationSystem:

    def __init__(self, project_name: str):
        if not project_name.strip():
            raise ValidationError("Project name is required.")

        self.project_name = project_name

        self.stakeholders: dict[str, Stakeholder] = {}
        self.plans: dict[str, CommunicationPlan] = {}
        self.messages: dict[str, Message] = {}
        self.meetings: dict[str, Meeting] = {}
        self.decisions: dict[str, Decision] = {}
        self.actions: dict[str, ActionItem] = {}

        self.audit_log: list[AuditEvent] = []

    @staticmethod
    def generate_id(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:12]}"

    def _audit(
        self,
        event_type: str,
        entity_id: str,
        actor_id: str,
        details: dict,
    ) -> None:
        self.audit_log.append(
            AuditEvent(
                event_id=self.generate_id("AUD"),
                event_type=event_type,
                entity_id=entity_id,
                actor_id=actor_id,
                timestamp=datetime.now(timezone.utc),
                details=details,
            )
        )

    def _get_stakeholder(self, stakeholder_id: str) -> Stakeholder:
        stakeholder = self.stakeholders.get(stakeholder_id)

        if stakeholder is None:
            raise NotFoundError(
                f"Stakeholder not found: {stakeholder_id}"
            )

        if not stakeholder.active:
            raise AuthorizationError("Stakeholder is inactive.")

        return stakeholder

    # --------------------------------------------------------
    # STAKEHOLDER MANAGEMENT
    # --------------------------------------------------------

    def add_stakeholder(self, stakeholder: Stakeholder) -> None:
        if stakeholder.stakeholder_id in self.stakeholders:
            raise ValidationError("Duplicate stakeholder ID.")

        if any(
            existing.email.lower() == stakeholder.email.lower()
            for existing in self.stakeholders.values()
        ):
            raise ValidationError("Stakeholder email already exists.")

        self.stakeholders[stakeholder.stakeholder_id] = stakeholder

        self._audit(
            "STAKEHOLDER_ADDED",
            stakeholder.stakeholder_id,
            stakeholder.stakeholder_id,
            {"role": stakeholder.role.value},
        )

    def stakeholder_register(self) -> list[dict]:
        return [
            {
                "id": stakeholder.stakeholder_id,
                "name": stakeholder.name,
                "role": stakeholder.role.value,
                "influence": stakeholder.influence,
                "interest": stakeholder.interest,
                "priority": stakeholder.engagement_priority,
            }
            for stakeholder in self.stakeholders.values()
            if stakeholder.active
        ]

    # --------------------------------------------------------
    # COMMUNICATION PLANNING
    # --------------------------------------------------------

    def add_communication_plan(
        self,
        plan: CommunicationPlan,
    ) -> None:
        self._get_stakeholder(plan.stakeholder_id)
        self._get_stakeholder(plan.owner_id)

        if plan.plan_id in self.plans:
            raise ValidationError("Duplicate communication plan ID.")

        self.plans[plan.plan_id] = plan

        self._audit(
            "COMMUNICATION_PLAN_CREATED",
            plan.plan_id,
            plan.owner_id,
            {
                "channel": plan.channel.value,
                "frequency": plan.frequency,
            },
        )

    # --------------------------------------------------------
    # MESSAGE MANAGEMENT
    # --------------------------------------------------------

    def create_message(
        self,
        sender_id: str,
        subject: str,
        body: str,
        channel: CommunicationChannel,
        purpose: CommunicationPurpose,
        confidentiality: Confidentiality,
        recipient_ids: list[str],
    ) -> Message:

        self._get_stakeholder(sender_id)

        for recipient_id in recipient_ids:
            recipient = self._get_stakeholder(recipient_id)

            if recipient.confidentiality_clearance.value < confidentiality.value:
                raise AuthorizationError(
                    f"{recipient.name} lacks required clearance."
                )

        message = Message(
            message_id=self.generate_id("MSG"),
            sender_id=sender_id,
            subject=subject,
            body=body,
            channel=channel,
            purpose=purpose,
            confidentiality=confidentiality,
            recipient_ids=recipient_ids.copy(),
            created_at=datetime.now(timezone.utc),
        )

        self.messages[message.message_id] = message

        self._audit(
            "MESSAGE_CREATED",
            message.message_id,
            sender_id,
            {"recipients": recipient_ids},
        )

        return message

    def send_message(self, message_id: str) -> Message:
        message = self.messages.get(message_id)

        if message is None:
            raise NotFoundError("Message does not exist.")

        if message.status != MessageStatus.DRAFT:
            raise StateTransitionError("Only draft messages can be sent.")

        # Revalidate clearance at dispatch time.
        for recipient_id in message.recipient_ids:
            recipient = self._get_stakeholder(recipient_id)

            if recipient.confidentiality_clearance.value < message.confidentiality.value:
                raise AuthorizationError(
                    "Recipient authorization changed before dispatch."
                )

        message.status = MessageStatus.SENT
        message.sent_at = datetime.now(timezone.utc)

        self._audit(
            "MESSAGE_SENT",
            message_id,
            message.sender_id,
            {"channel": message.channel.value},
        )

        return message

    def acknowledge_message(
        self,
        message_id: str,
        stakeholder_id: str,
    ) -> None:

        message = self.messages.get(message_id)

        if message is None:
            raise NotFoundError("Message does not exist.")

        if message.status not in {
            MessageStatus.SENT,
            MessageStatus.ACKNOWLEDGED,
        }:
            raise StateTransitionError("Message is not available for acknowledgement.")

        if stakeholder_id not in message.recipient_ids:
            raise AuthorizationError("Only intended recipients can acknowledge.")

        message.acknowledged_by.add(stakeholder_id)

        if set(message.recipient_ids) == message.acknowledged_by:
            message.status = MessageStatus.ACKNOWLEDGED

        self._audit(
            "MESSAGE_ACKNOWLEDGED",
            message_id,
            stakeholder_id,
            {},
        )

    def escalate_unacknowledged(
        self,
        message_id: str,
        maximum_wait: timedelta,
    ) -> list[str]:

        message = self.messages.get(message_id)

        if message is None:
            raise NotFoundError("Message does not exist.")

        if message.status not in {
            MessageStatus.SENT,
            MessageStatus.ESCALATED,
        }:
            return []

        if message.sent_at is None:
            return []

        if datetime.now(timezone.utc) - message.sent_at <= maximum_wait:
            return []

        pending = [
            recipient_id
            for recipient_id in message.recipient_ids
            if recipient_id not in message.acknowledged_by
        ]

        if pending:
            message.status = MessageStatus.ESCALATED

            self._audit(
                "MESSAGE_ESCALATED",
                message_id,
                message.sender_id,
                {"pending_recipients": pending},
            )

        return pending

    # --------------------------------------------------------
    # MEETINGS AND DECISIONS
    # --------------------------------------------------------

    def schedule_meeting(self, meeting: Meeting) -> None:
        self._get_stakeholder(meeting.organizer_id)

        for participant_id in meeting.participant_ids:
            self._get_stakeholder(participant_id)

        if meeting.meeting_id in self.meetings:
            raise ValidationError("Duplicate meeting ID.")

        self.meetings[meeting.meeting_id] = meeting

        self._audit(
            "MEETING_SCHEDULED",
            meeting.meeting_id,
            meeting.organizer_id,
            {"participants": meeting.participant_ids},
        )

    def complete_meeting(
        self,
        meeting_id: str,
        organizer_id: str,
        minutes: str,
    ) -> None:

        meeting = self.meetings.get(meeting_id)

        if meeting is None:
            raise NotFoundError("Meeting does not exist.")

        if meeting.organizer_id != organizer_id:
            raise AuthorizationError("Only the organizer can finalize minutes.")

        if meeting.completed:
            raise StateTransitionError("Meeting is already completed.")

        if not minutes.strip():
            raise ValidationError("Meeting minutes cannot be empty.")

        meeting.minutes = minutes
        meeting.completed = True

        self._audit(
            "MEETING_COMPLETED",
            meeting_id,
            organizer_id,
            {},
        )

    def record_decision(
        self,
        meeting_id: str,
        owner_id: str,
        description: str,
        approved: bool,
    ) -> Decision:

        meeting = self.meetings.get(meeting_id)

        if meeting is None or not meeting.completed:
            raise StateTransitionError(
                "Decisions require a completed meeting."
            )

        self._get_stakeholder(owner_id)

        if not description.strip():
            raise ValidationError("Decision description is required.")

        decision = Decision(
            decision_id=self.generate_id("DEC"),
            meeting_id=meeting_id,
            description=description,
            owner_id=owner_id,
            decided_at=datetime.now(timezone.utc),
            approved=approved,
        )

        self.decisions[decision.decision_id] = decision

        self._audit(
            "DECISION_RECORDED",
            decision.decision_id,
            owner_id,
            {"approved": approved},
        )

        return decision

    # --------------------------------------------------------
    # ACTION-ITEM MANAGEMENT
    # --------------------------------------------------------

    def create_action(self, action: ActionItem) -> None:
        self._get_stakeholder(action.assigned_to)
        self._get_stakeholder(action.created_by)

        if action.action_id in self.actions:
            raise ValidationError("Duplicate action ID.")

        self.actions[action.action_id] = action

        self._audit(
            "ACTION_CREATED",
            action.action_id,
            action.created_by,
            {"assigned_to": action.assigned_to},
        )

    def update_action(
        self,
        action_id: str,
        actor_id: str,
        new_status: ActionStatus,
    ) -> None:

        action = self.actions.get(action_id)

        if action is None:
            raise NotFoundError("Action item does not exist.")

        if actor_id not in {action.assigned_to, action.created_by}:
            raise AuthorizationError("Actor cannot update this action.")

        allowed_transitions = {
            ActionStatus.OPEN: {
                ActionStatus.IN_PROGRESS,
                ActionStatus.BLOCKED,
                ActionStatus.CANCELLED,
            },
            ActionStatus.IN_PROGRESS: {
                ActionStatus.COMPLETED,
                ActionStatus.BLOCKED,
                ActionStatus.CANCELLED,
            },
            ActionStatus.BLOCKED: {
                ActionStatus.IN_PROGRESS,
                ActionStatus.CANCELLED,
            },
            ActionStatus.COMPLETED: set(),
            ActionStatus.CANCELLED: set(),
        }

        if new_status not in allowed_transitions[action.status]:
            raise StateTransitionError(
                f"Cannot change {action.status.value} to {new_status.value}."
            )

        action.status = new_status

        if new_status == ActionStatus.COMPLETED:
            action.completed_at = datetime.now(timezone.utc)

        self._audit(
            "ACTION_STATUS_CHANGED",
            action_id,
            actor_id,
            {"new_status": new_status.value},
        )

    def overdue_actions(self) -> list[ActionItem]:
        now = datetime.now(timezone.utc)

        return [
            action
            for action in self.actions.values()
            if action.due_date < now
            and action.status not in {
                ActionStatus.COMPLETED,
                ActionStatus.CANCELLED,
            }
        ]

    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    def communication_metrics(self) -> dict:
        total = len(self.messages)

        sent = [
            message
            for message in self.messages.values()
            if message.sent_at is not None
        ]

        expected_acknowledgements = sum(
            len(message.recipient_ids)
            for message in sent
        )

        actual_acknowledgements = sum(
            len(message.acknowledged_by)
            for message in sent
        )

        acknowledgement_rate = (
            actual_acknowledgements / expected_acknowledgements * 100
            if expected_acknowledgements
            else 0.0
        )

        return {
            "project": self.project_name,
            "stakeholders": len(self.stakeholders),
            "communication_plans": len(self.plans),
            "total_messages": total,
            "sent_messages": len(sent),
            "acknowledged_recipients": actual_acknowledgements,
            "expected_acknowledgements": expected_acknowledgements,
            "acknowledgement_rate_percent": round(
                acknowledgement_rate, 2
            ),
            "overdue_actions": len(self.overdue_actions()),
            "meetings": len(self.meetings),
            "decisions": len(self.decisions),
            "audit_events": len(self.audit_log),
        }

    # --------------------------------------------------------
    # AUDIT EXPORT
    # --------------------------------------------------------

    def export_audit(self, output_path: str) -> None:
        destination = Path(output_path)

        events = [
            {
                **asdict(event),
                "timestamp": event.timestamp.isoformat(),
            }
            for event in self.audit_log
        ]

        # Restrict file creation to the selected destination.
        destination.parent.mkdir(parents=True, exist_ok=True)

        destination.write_text(
            json.dumps(events, indent=2, default=str),
            encoding="utf-8",
        )


# ============================================================
# EXECUTABLE SCENARIO
# ============================================================

def run_demo() -> None:

    system = ProjectCommunicationSystem(
        "Enterprise Project Management System"
    )

    manager = Stakeholder(
        "ST-001",
        "Project Manager",
        "manager@example.com",
        StakeholderRole.PROJECT_MANAGER,
        5,
        5,
        Confidentiality.RESTRICTED,
    )

    sponsor = Stakeholder(
        "ST-002",
        "Project Sponsor",
        "sponsor@example.com",
        StakeholderRole.SPONSOR,
        5,
        4,
        Confidentiality.CONFIDENTIAL,
    )

    developer = Stakeholder(
        "ST-003",
        "Development Lead",
        "developer@example.com",
        StakeholderRole.TEAM_MEMBER,
        3,
        5,
        Confidentiality.INTERNAL,
    )

    client = Stakeholder(
        "ST-004",
        "Client Representative",
        "client@example.com",
        StakeholderRole.CLIENT,
        4,
        5,
        Confidentiality.CONFIDENTIAL,
    )

    for stakeholder in [manager, sponsor, developer, client]:
        system.add_stakeholder(stakeholder)

    now = datetime.now(timezone.utc)

    plan = CommunicationPlan(
        plan_id="PLAN-001",
        stakeholder_id=sponsor.stakeholder_id,
        channel=CommunicationChannel.EMAIL,
        frequency="weekly",
        purpose=CommunicationPurpose.STATUS_UPDATE,
        owner_id=manager.stakeholder_id,
        next_communication=now + timedelta(days=7),
    )

    system.add_communication_plan(plan)

    message = system.create_message(
        sender_id=manager.stakeholder_id,
        subject="Weekly Project Progress",
        body=(
            "Development is 65% complete. "
            "Testing preparation is underway. "
            "The current delivery milestone remains on schedule."
        ),
        channel=CommunicationChannel.EMAIL,
        purpose=CommunicationPurpose.STATUS_UPDATE,
        confidentiality=Confidentiality.INTERNAL,
        recipient_ids=[
            sponsor.stakeholder_id,
            developer.stakeholder_id,
        ],
    )

    system.send_message(message.message_id)

    system.acknowledge_message(
        message.message_id,
        sponsor.stakeholder_id,
    )

    meeting = Meeting(
        meeting_id="MEET-001",
        title="Weekly Project Review",
        organizer_id=manager.stakeholder_id,
        participant_ids=[
            sponsor.stakeholder_id,
            developer.stakeholder_id,
            client.stakeholder_id,
        ],
        scheduled_at=now + timedelta(days=1),
        agenda=[
            "Progress review",
            "Risk assessment",
            "Resource allocation",
            "Delivery decisions",
        ],
    )

    system.schedule_meeting(meeting)

    system.complete_meeting(
        meeting.meeting_id,
        manager.stakeholder_id,
        "Development progress reviewed. "
        "Testing preparation approved. "
        "Resource allocation remains unchanged.",
    )

    system.record_decision(
        meeting.meeting_id,
        sponsor.stakeholder_id,
        "Approve the testing preparation schedule.",
        True,
    )

    action = ActionItem(
        action_id="ACT-001",
        description="Prepare the software testing plan.",
        assigned_to=developer.stakeholder_id,
        created_by=manager.stakeholder_id,
        due_date=now + timedelta(days=5),
    )

    system.create_action(action)

    system.update_action(
        action.action_id,
        developer.stakeholder_id,
        ActionStatus.IN_PROGRESS,
    )

    print("\nSTAKEHOLDER REGISTER")
    for stakeholder in system.stakeholder_register():
        print(stakeholder)

    print("\nCOMMUNICATION METRICS")
    print(json.dumps(system.communication_metrics(), indent=2))

    print("\nOVERDUE ACTIONS")
    for overdue in system.overdue_actions():
        print(overdue.action_id, overdue.description)

    system.export_audit("project_communication_audit.json")

    print("\nAudit exported to project_communication_audit.json")

    # --------------------------------------------------------
    # AUTOMATED VALIDATION
    # --------------------------------------------------------

    assert len(system.stakeholders) == 4
    assert message.status == MessageStatus.SENT
    assert sponsor.stakeholder_id in message.acknowledged_by
    assert meeting.completed
    assert len(system.decisions) == 1
    assert action.status == ActionStatus.IN_PROGRESS

    try:
        system.acknowledge_message(
            message.message_id,
            client.stakeholder_id,
        )
    except AuthorizationError:
        print("Unauthorized acknowledgement correctly rejected.")

    try:
        system.update_action(
            action.action_id,
            manager.stakeholder_id,
            ActionStatus.OPEN,
        )
    except StateTransitionError:
        print("Invalid action transition correctly rejected.")

    print("\nAll validation checks passed.")


if __name__ == "__main__":
    run_demo()
