#!/usr/bin/env python3
"""
Communication Challenges: Common Communication Problems

Models communication incidents, identifies root causes, assigns corrective
actions, tracks resolution, and evaluates communication effectiveness.

Python 3.10+
Uses only the Python standard library.
"""

from __future__ import annotations

import json
import logging
import re
import unittest

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("communication_management")


class CommunicationCategory(str, Enum):
    UNCLEAR_MESSAGE = "unclear_message"
    INFORMATION_OVERLOAD = "information_overload"
    ACTIVE_LISTENING = "poor_listening"
    LANGUAGE_BARRIER = "language_barrier"
    CULTURAL_DIFFERENCE = "cultural_difference"
    WRONG_CHANNEL = "wrong_channel"
    DELAYED_RESPONSE = "delayed_response"
    MISSING_FEEDBACK = "missing_feedback"
    ASSUMPTION = "incorrect_assumption"
    TECHNICAL_FAILURE = "technical_failure"
    CONFLICT = "interpersonal_conflict"
    ROLE_AMBIGUITY = "role_ambiguity"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    ACTION_REQUIRED = "action_required"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Channel(str, Enum):
    EMAIL = "email"
    MEETING = "meeting"
    CHAT = "chat"
    PHONE = "phone"
    DOCUMENT = "document"
    VIDEO_CONFERENCE = "video_conference"
    FACE_TO_FACE = "face_to_face"


class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class CommunicationIncident:
    incident_id: int
    title: str
    category: CommunicationCategory
    severity: Severity
    channel: Channel
    department: str
    reporter: str
    description: str
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: IncidentStatus = IncidentStatus.OPEN
    assigned_to: Optional[str] = None
    corrective_action: Optional[str] = None
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    feedback_received: bool = False
    events: list[dict] = field(default_factory=list)

    def record_event(self, action: str, details: str) -> None:
        self.events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": details
        })


@dataclass(frozen=True)
class CommunicationPolicy:
    response_hours: dict[Severity, int] = field(
        default_factory=lambda: {
            Severity.LOW: 72,
            Severity.MEDIUM: 48,
            Severity.HIGH: 12,
            Severity.CRITICAL: 2
        }
    )

    def deadline(self, incident: CommunicationIncident) -> datetime:
        hours = self.response_hours[incident.severity]
        return incident.created_at + timedelta(hours=hours)


class CommunicationError(Exception):
    """Base exception for communication workflow failures."""


class ValidationError(CommunicationError):
    pass


class InvalidTransitionError(CommunicationError):
    pass


class CommunicationManager:
    ALLOWED_TRANSITIONS = {
        IncidentStatus.OPEN: {
            IncidentStatus.INVESTIGATING,
            IncidentStatus.CLOSED
        },
        IncidentStatus.INVESTIGATING: {
            IncidentStatus.ACTION_REQUIRED,
            IncidentStatus.RESOLVED,
            IncidentStatus.CLOSED
        },
        IncidentStatus.ACTION_REQUIRED: {
            IncidentStatus.INVESTIGATING,
            IncidentStatus.RESOLVED
        },
        IncidentStatus.RESOLVED: {
            IncidentStatus.CLOSED,
            IncidentStatus.INVESTIGATING
        },
        IncidentStatus.CLOSED: set()
    }

    def __init__(self, policy: Optional[CommunicationPolicy] = None):
        self.policy = policy or CommunicationPolicy()
        self.incidents: dict[int, CommunicationIncident] = {}
        self.next_id = 1

    @staticmethod
    def validate_text(value: str, field_name: str,
                      max_length: int = 500) -> str:
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be text.")

        value = value.strip()

        if not value:
            raise ValidationError(f"{field_name} cannot be empty.")

        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} exceeds {max_length} characters."
            )

        if any(ord(char) < 32 and char not in "\n\t" for char in value):
            raise ValidationError(
                f"{field_name} contains invalid control characters."
            )

        return value

    def report(
        self,
        title: str,
        category: CommunicationCategory,
        severity: Severity,
        channel: Channel,
        department: str,
        reporter: str,
        description: str
    ) -> CommunicationIncident:

        title = self.validate_text(title, "Title", 120)
        department = self.validate_text(department, "Department", 100)
        reporter = self.validate_text(reporter, "Reporter", 100)
        description = self.validate_text(description, "Description", 1000)

        if not isinstance(category, CommunicationCategory):
            raise ValidationError("Invalid communication category.")

        if not isinstance(severity, Severity):
            raise ValidationError("Invalid severity.")

        if not isinstance(channel, Channel):
            raise ValidationError("Invalid communication channel.")

        incident = CommunicationIncident(
            incident_id=self.next_id,
            title=title,
            category=category,
            severity=severity,
            channel=channel,
            department=department,
            reporter=reporter,
            description=description
        )

        incident.record_event("reported", "Communication issue registered.")

        self.incidents[self.next_id] = incident
        self.next_id += 1

        logger.info("Incident %s registered.", incident.incident_id)

        return incident

    def get_incident(self, incident_id: int) -> CommunicationIncident:
        if incident_id not in self.incidents:
            raise CommunicationError(
                f"Incident {incident_id} does not exist."
            )

        return self.incidents[incident_id]

    def assign(self, incident_id: int, employee: str) -> None:
        incident = self.get_incident(incident_id)
        employee = self.validate_text(employee, "Assignee", 100)

        if incident.status == IncidentStatus.CLOSED:
            raise InvalidTransitionError("Cannot assign a closed incident.")

        incident.assigned_to = employee
        incident.record_event("assigned", f"Assigned to {employee}.")

    def transition(
        self,
        incident_id: int,
        new_status: IncidentStatus
    ) -> None:

        incident = self.get_incident(incident_id)

        if new_status not in self.ALLOWED_TRANSITIONS[incident.status]:
            raise InvalidTransitionError(
                f"Cannot transition from {incident.status.value} "
                f"to {new_status.value}."
            )

        if new_status == IncidentStatus.RESOLVED:
            if not incident.resolution:
                raise ValidationError(
                    "A resolution description is required."
                )

        incident.status = new_status

        if new_status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now(timezone.utc)

        incident.record_event(
            "status_changed",
            f"Status changed to {new_status.value}."
        )

    def recommend_action(self, category: CommunicationCategory) -> str:
        recommendations = {
            CommunicationCategory.UNCLEAR_MESSAGE:
                "Use concise language, explicit instructions, "
                "and written confirmation.",

            CommunicationCategory.INFORMATION_OVERLOAD:
                "Prioritize essential information and divide "
                "large messages into manageable sections.",

            CommunicationCategory.ACTIVE_LISTENING:
                "Use active listening, paraphrasing, and "
                "clarifying questions.",

            CommunicationCategory.LANGUAGE_BARRIER:
                "Use plain language and provide verified translations.",

            CommunicationCategory.CULTURAL_DIFFERENCE:
                "Establish inclusive communication practices "
                "and clarify cultural expectations.",

            CommunicationCategory.WRONG_CHANNEL:
                "Select a communication channel appropriate "
                "to urgency, confidentiality, and complexity.",

            CommunicationCategory.DELAYED_RESPONSE:
                "Establish response deadlines and escalation rules.",

            CommunicationCategory.MISSING_FEEDBACK:
                "Introduce regular feedback and confirmation cycles.",

            CommunicationCategory.ASSUMPTION:
                "Verify facts and explicitly confirm shared understanding.",

            CommunicationCategory.TECHNICAL_FAILURE:
                "Check infrastructure and establish an alternative channel.",

            CommunicationCategory.CONFLICT:
                "Use structured discussion and impartial conflict resolution.",

            CommunicationCategory.ROLE_AMBIGUITY:
                "Define responsibilities, ownership, and reporting lines."
        }

        return recommendations[category]

    def prescribe_action(
        self,
        incident_id: int,
        action: Optional[str] = None
    ) -> str:

        incident = self.get_incident(incident_id)

        if incident.status == IncidentStatus.CLOSED:
            raise InvalidTransitionError("Incident is already closed.")

        if action is None:
            action = self.recommend_action(incident.category)

        incident.corrective_action = self.validate_text(
            action, "Corrective action", 1000
        )

        incident.record_event(
            "action_prescribed",
            incident.corrective_action
        )

        if incident.status in {
            IncidentStatus.OPEN,
            IncidentStatus.INVESTIGATING
        }:
            self.transition(
                incident_id,
                IncidentStatus.ACTION_REQUIRED
            )

        return incident.corrective_action

    def resolve(self, incident_id: int, resolution: str) -> None:
        incident = self.get_incident(incident_id)

        if incident.status not in {
            IncidentStatus.INVESTIGATING,
            IncidentStatus.ACTION_REQUIRED
        }:
            raise InvalidTransitionError(
                "Incident must be investigated before resolution."
            )

        if not incident.corrective_action:
            raise ValidationError(
                "A corrective action must be recorded before resolution."
            )

        incident.resolution = self.validate_text(
            resolution, "Resolution", 1000
        )

        self.transition(incident_id, IncidentStatus.RESOLVED)

    def close(self, incident_id: int) -> None:
        incident = self.get_incident(incident_id)

        if incident.status == IncidentStatus.RESOLVED:
            if not incident.feedback_received:
                raise ValidationError(
                    "Feedback confirmation is required before closure."
                )

        self.transition(incident_id, IncidentStatus.CLOSED)

    def record_feedback(self, incident_id: int) -> None:
        incident = self.get_incident(incident_id)

        if incident.status != IncidentStatus.RESOLVED:
            raise InvalidTransitionError(
                "Feedback can only confirm a resolved incident."
            )

        incident.feedback_received = True
        incident.record_event(
            "feedback_received",
            "Resolution acknowledged."
        )

    def overdue_incidents(self) -> list[CommunicationIncident]:
        now = datetime.now(timezone.utc)

        return [
            incident
            for incident in self.incidents.values()
            if incident.status not in {
                IncidentStatus.RESOLVED,
                IncidentStatus.CLOSED
            }
            and now > self.policy.deadline(incident)
        ]

    def search(
        self,
        category: Optional[CommunicationCategory] = None,
        department: Optional[str] = None,
        status: Optional[IncidentStatus] = None
    ) -> list[CommunicationIncident]:

        results = list(self.incidents.values())

        if category is not None:
            results = [
                item for item in results if item.category == category
            ]

        if department is not None:
            results = [
                item for item in results
                if item.department.casefold() == department.casefold()
            ]

        if status is not None:
            results = [
                item for item in results if item.status == status
            ]

        return sorted(results, key=lambda item: item.incident_id)

    def analytics(self) -> dict:
        incidents = list(self.incidents.values())

        category_counts = Counter(
            item.category.value for item in incidents
        )

        severity_counts = Counter(
            item.severity.value for item in incidents
        )

        status_counts = Counter(
            item.status.value for item in incidents
        )

        resolved_durations = [
            (item.resolved_at - item.created_at).total_seconds() / 3600
            for item in incidents
            if item.resolved_at is not None
        ]

        resolution_rate = (
            sum(
                item.status in {
                    IncidentStatus.RESOLVED,
                    IncidentStatus.CLOSED
                }
                for item in incidents
            ) / len(incidents) * 100
            if incidents else 0
        )

        return {
            "total_incidents": len(incidents),
            "categories": dict(category_counts),
            "severities": dict(severity_counts),
            "statuses": dict(status_counts),
            "resolution_rate_percent": round(resolution_rate, 2),
            "average_resolution_hours": round(
                sum(resolved_durations) / len(resolved_durations), 2
            ) if resolved_durations else None,
            "overdue_count": len(self.overdue_incidents())
        }

    def export_json(self, filename: str) -> None:
        records = []

        for incident in self.incidents.values():
            record = asdict(incident)

            for key in ("category", "severity", "channel", "status"):
                record[key] = getattr(incident, key).value

            for key in ("created_at", "resolved_at"):
                value = record[key]
                record[key] = value.isoformat() if value else None

            records.append(record)

        path = Path(filename)
        path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


def demonstrate() -> CommunicationManager:
    manager = CommunicationManager()

    # Scenario 1: Unclear project instructions.
    first = manager.report(
        title="Unclear project instructions",
        category=CommunicationCategory.UNCLEAR_MESSAGE,
        severity=Severity.HIGH,
        channel=Channel.EMAIL,
        department="Engineering",
        reporter="Project Manager",
        description=(
            "The development team received incomplete delivery "
            "instructions and interpreted the deadline differently."
        )
    )

    manager.assign(first.incident_id, "Communication Coordinator")
    manager.transition(first.incident_id, IncidentStatus.INVESTIGATING)
    manager.prescribe_action(first.incident_id)
    manager.resolve(
        first.incident_id,
        "A revised project brief was distributed with explicit "
        "deliverables, owners, and deadlines."
    )
    manager.record_feedback(first.incident_id)
    manager.close(first.incident_id)

    # Scenario 2: Delayed response.
    second = manager.report(
        title="Delayed customer response",
        category=CommunicationCategory.DELAYED_RESPONSE,
        severity=Severity.MEDIUM,
        channel=Channel.EMAIL,
        department="Customer Support",
        reporter="Support Supervisor",
        description="A customer inquiry remained unanswered."
    )

    manager.assign(second.incident_id, "Support Team Lead")
    manager.transition(second.incident_id, IncidentStatus.INVESTIGATING)
    manager.prescribe_action(second.incident_id)

    # Scenario 3: Information overload.
    third = manager.report(
        title="Excessive meeting information",
        category=CommunicationCategory.INFORMATION_OVERLOAD,
        severity=Severity.LOW,
        channel=Channel.MEETING,
        department="Operations",
        reporter="Operations Manager",
        description="Meeting participants received too much unstructured information."
    )

    print("\nCOMMUNICATION INCIDENT REPORT")

    for incident in manager.incidents.values():
        print(
            f"{incident.incident_id}. {incident.title} | "
            f"{incident.category.value} | "
            f"{incident.severity.value} | "
            f"{incident.status.value}"
        )

    print("\nRECOMMENDED ACTION")
    print(manager.recommend_action(third.category))

    print("\nANALYTICS")
    print(json.dumps(manager.analytics(), indent=2))

    return manager


class CommunicationTests(unittest.TestCase):

    def setUp(self):
        self.manager = CommunicationManager()

    def create_incident(self):
        return self.manager.report(
            "Test communication issue",
            CommunicationCategory.MISSING_FEEDBACK,
            Severity.MEDIUM,
            Channel.CHAT,
            "Testing",
            "Tester",
            "Feedback was not collected."
        )

    def test_incident_creation(self):
        incident = self.create_incident()
        self.assertEqual(incident.incident_id, 1)
        self.assertEqual(incident.status, IncidentStatus.OPEN)

    def test_empty_title_rejected(self):
        with self.assertRaises(ValidationError):
            self.manager.report(
                "",
                CommunicationCategory.CONFLICT,
                Severity.LOW,
                Channel.MEETING,
                "Testing",
                "Tester",
                "Description"
            )

    def test_invalid_transition(self):
        incident = self.create_incident()

        with self.assertRaises(InvalidTransitionError):
            self.manager.transition(
                incident.incident_id,
                IncidentStatus.RESOLVED
            )

    def test_resolution_workflow(self):
        incident = self.create_incident()
        incident_id = incident.incident_id

        self.manager.assign(incident_id, "Reviewer")
        self.manager.transition(
            incident_id,
            IncidentStatus.INVESTIGATING
        )
        self.manager.prescribe_action(incident_id)
        self.manager.resolve(incident_id, "Feedback process established.")
        self.manager.record_feedback(incident_id)
        self.manager.close(incident_id)

        self.assertEqual(
            incident.status,
            IncidentStatus.CLOSED
        )

    def test_analytics(self):
        self.create_incident()

        self.assertEqual(
            self.manager.analytics()["total_incidents"],
            1
        )


if __name__ == "__main__":
    demonstrate()

    print("\nRUNNING VALIDATION TESTS")
    unittest.main(argv=["communication_management"], exit=False)
