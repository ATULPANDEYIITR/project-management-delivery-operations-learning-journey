"""
Escalation Management and Critical Problem Reporting System

Models incident reporting, severity classification, escalation workflows,
ownership, response deadlines, notifications, audit history and resolution.
Python 3.10+ | Standard library only.
"""

from __future__ import annotations

import json
import logging
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
logger = logging.getLogger("escalation")


class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class IncidentStatus(Enum):
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EscalationLevel(Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    EXECUTIVE = 4


class IncidentError(Exception):
    """Base exception for incident-management failures."""


class ValidationError(IncidentError):
    pass


class TransitionError(IncidentError):
    pass


class PermissionError(IncidentError):
    pass


class NotFoundError(IncidentError):
    pass


@dataclass(frozen=True)
class EscalationPolicy:
    severity: Severity
    acknowledgement_minutes: int
    resolution_minutes: int
    escalation_level: EscalationLevel

    def __post_init__(self):
        if self.acknowledgement_minutes <= 0:
            raise ValidationError("Acknowledgement deadline must be positive.")
        if self.resolution_minutes <= self.acknowledgement_minutes:
            raise ValidationError(
                "Resolution deadline must exceed acknowledgement deadline."
            )


POLICIES = {
    Severity.LOW: EscalationPolicy(
        Severity.LOW, 480, 2880, EscalationLevel.LEVEL_1
    ),
    Severity.MEDIUM: EscalationPolicy(
        Severity.MEDIUM, 120, 1440, EscalationLevel.LEVEL_1
    ),
    Severity.HIGH: EscalationPolicy(
        Severity.HIGH, 30, 240, EscalationLevel.LEVEL_2
    ),
    Severity.CRITICAL: EscalationPolicy(
        Severity.CRITICAL, 10, 60, EscalationLevel.EXECUTIVE
    ),
}


@dataclass
class Actor:
    actor_id: str
    name: str
    role: str
    department: str

    def can_manage(self, severity: Severity) -> bool:
        if self.role in {"administrator", "incident_manager"}:
            return True
        if self.role == "team_lead":
            return severity != Severity.CRITICAL
        return self.role == "responder"


@dataclass
class AuditEvent:
    timestamp: str
    actor_id: str
    action: str
    details: str


@dataclass
class Incident:
    incident_id: str
    title: str
    description: str
    category: str
    severity: Severity
    reporter_id: str
    department: str
    reported_at: datetime
    acknowledgement_deadline: datetime
    resolution_deadline: datetime
    assigned_to: Optional[str] = None
    status: IncidentStatus = IncidentStatus.REPORTED
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_1
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    parent_incident_id: Optional[str] = None
    tags: set[str] = field(default_factory=set)
    audit_log: list[AuditEvent] = field(default_factory=list)

    def overdue_acknowledgement(self, now: datetime) -> bool:
        return (
            self.acknowledged_at is None
            and now > self.acknowledgement_deadline
        )

    def overdue_resolution(self, now: datetime) -> bool:
        return (
            self.status not in {
                IncidentStatus.RESOLVED,
                IncidentStatus.CLOSED
            }
            and now > self.resolution_deadline
        )


class EscalationManager:
    VALID_TRANSITIONS = {
        IncidentStatus.REPORTED: {
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.ESCALATED,
        },
        IncidentStatus.ACKNOWLEDGED: {
            IncidentStatus.INVESTIGATING,
            IncidentStatus.ESCALATED,
        },
        IncidentStatus.INVESTIGATING: {
            IncidentStatus.ESCALATED,
            IncidentStatus.RESOLVED,
        },
        IncidentStatus.ESCALATED: {
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.INVESTIGATING,
            IncidentStatus.RESOLVED,
        },
        IncidentStatus.RESOLVED: {
            IncidentStatus.CLOSED,
            IncidentStatus.INVESTIGATING,
        },
        IncidentStatus.CLOSED: set(),
    }

    def __init__(self):
        self.incidents: dict[str, Incident] = {}
        self.actors: dict[str, Actor] = {}
        self.notification_queue: list[dict] = []
        self.idempotency_keys: set[str] = set()

    def register_actor(self, actor: Actor) -> None:
        if actor.actor_id in self.actors:
            raise ValidationError("Actor already exists.")
        self.actors[actor.actor_id] = actor

    def _actor(self, actor_id: str) -> Actor:
        actor = self.actors.get(actor_id)
        if actor is None:
            raise PermissionError("Unknown actor.")
        return actor

    def _incident(self, incident_id: str) -> Incident:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise NotFoundError("Incident does not exist.")
        return incident

    @staticmethod
    def _validate_text(value: str, field_name: str, maximum: int) -> str:
        value = value.strip()
        if not value:
            raise ValidationError(f"{field_name} cannot be empty.")
        if len(value) > maximum:
            raise ValidationError(f"{field_name} exceeds {maximum} characters.")
        return value

    def _audit(
        self,
        incident: Incident,
        actor_id: str,
        action: str,
        details: str
    ) -> None:
        incident.audit_log.append(
            AuditEvent(
                datetime.now(timezone.utc).isoformat(),
                actor_id,
                action,
                details
            )
        )

    def _notify(self, incident: Incident, event: str, recipient: str) -> None:
        self.notification_queue.append({
            "notification_id": str(uuid.uuid4()),
            "incident_id": incident.incident_id,
            "event": event,
            "recipient": recipient,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "delivery_status": "pending",
        })

    def report(
        self,
        reporter_id: str,
        title: str,
        description: str,
        category: str,
        severity: Severity,
        department: str,
        idempotency_key: Optional[str] = None,
        tags: Optional[set[str]] = None,
        parent_incident_id: Optional[str] = None,
    ) -> Incident:
        reporter = self._actor(reporter_id)

        if not isinstance(severity, Severity):
            raise ValidationError("Invalid severity.")

        if idempotency_key:
            if idempotency_key in self.idempotency_keys:
                raise ValidationError("Duplicate reporting request.")
            self.idempotency_keys.add(idempotency_key)

        title = self._validate_text(title, "Title", 160)
        description = self._validate_text(description, "Description", 5000)
        category = self._validate_text(category, "Category", 80)
        department = self._validate_text(department, "Department", 100)

        if parent_incident_id:
            self._incident(parent_incident_id)

        now = datetime.now(timezone.utc)
        policy = POLICIES[severity]

        incident = Incident(
            incident_id=str(uuid.uuid4()),
            title=title,
            description=description,
            category=category,
            severity=severity,
            reporter_id=reporter.actor_id,
            department=department,
            reported_at=now,
            acknowledgement_deadline=now + timedelta(
                minutes=policy.acknowledgement_minutes
            ),
            resolution_deadline=now + timedelta(
                minutes=policy.resolution_minutes
            ),
            escalation_level=policy.escalation_level,
            parent_incident_id=parent_incident_id,
            tags=tags or set(),
        )

        incident.audit_log.append(
            AuditEvent(
                now.isoformat(),
                reporter_id,
                "REPORTED",
                f"Incident created with severity {severity.name}"
            )
        )

        self.incidents[incident.incident_id] = incident
        self._notify(incident, "INCIDENT_REPORTED", "incident_management")

        if severity == Severity.CRITICAL:
            self._notify(incident, "CRITICAL_ALERT", "executive_team")

        logger.info(
            "Incident %s created with severity %s",
            incident.incident_id,
            severity.name
        )

        return incident

    def _authorize(self, actor_id: str, incident: Incident) -> Actor:
        actor = self._actor(actor_id)
        if not actor.can_manage(incident.severity):
            raise PermissionError(
                "Actor is not authorized for this incident severity."
            )
        return actor

    def _transition(
        self,
        incident: Incident,
        new_status: IncidentStatus,
        actor_id: str,
        details: str
    ) -> None:
        allowed = self.VALID_TRANSITIONS[incident.status]

        if new_status not in allowed:
            raise TransitionError(
                f"Cannot transition from {incident.status.value} "
                f"to {new_status.value}."
            )

        old_status = incident.status
        incident.status = new_status

        self._audit(
            incident,
            actor_id,
            "STATUS_CHANGED",
            f"{old_status.value} -> {new_status.value}: {details}"
        )

    def assign(
        self,
        incident_id: str,
        actor_id: str,
        assignee_id: str
    ) -> None:
        incident = self._incident(incident_id)
        self._authorize(actor_id, incident)

        if assignee_id not in self.actors:
            raise ValidationError("Assignee does not exist.")

        incident.assigned_to = assignee_id
        self._audit(
            incident, actor_id, "ASSIGNED", f"Assigned to {assignee_id}"
        )
        self._notify(incident, "INCIDENT_ASSIGNED", assignee_id)

    def acknowledge(self, incident_id: str, actor_id: str) -> None:
        incident = self._incident(incident_id)
        self._authorize(actor_id, incident)

        self._transition(
            incident,
            IncidentStatus.ACKNOWLEDGED,
            actor_id,
            "Incident acknowledged"
        )
        incident.acknowledged_at = datetime.now(timezone.utc)
        self._notify(incident, "INCIDENT_ACKNOWLEDGED", incident.reporter_id)

    def investigate(self, incident_id: str, actor_id: str) -> None:
        incident = self._incident(incident_id)
        self._authorize(actor_id, incident)

        if not incident.assigned_to:
            raise ValidationError("Assign an owner before investigation.")

        self._transition(
            incident,
            IncidentStatus.INVESTIGATING,
            actor_id,
            "Investigation started"
        )

    def escalate(
        self,
        incident_id: str,
        actor_id: str,
        reason: str,
        target_level: Optional[EscalationLevel] = None
    ) -> None:
        incident = self._incident(incident_id)
        self._authorize(actor_id, incident)

        reason = self._validate_text(reason, "Escalation reason", 1000)

        if incident.status in {
            IncidentStatus.RESOLVED,
            IncidentStatus.CLOSED
        }:
            raise TransitionError("Resolved incidents cannot be escalated.")

        next_level = target_level or EscalationLevel(
            min(incident.escalation_level.value + 1, 4)
        )

        if next_level.value <= incident.escalation_level.value:
            raise ValidationError("Escalation level must increase.")

        if next_level.value > 4:
            raise ValidationError("Invalid escalation level.")

        incident.escalation_level = next_level

        if incident.status != IncidentStatus.ESCALATED:
            self._transition(
                incident,
                IncidentStatus.ESCALATED,
                actor_id,
                reason
            )
        else:
            self._audit(incident, actor_id, "ESCALATED_AGAIN", reason)

        recipient = (
            "executive_team"
            if next_level == EscalationLevel.EXECUTIVE
            else f"management_level_{next_level.value}"
        )

        self._notify(incident, "INCIDENT_ESCALATED", recipient)

    def resolve(
        self,
        incident_id: str,
        actor_id: str,
        resolution_notes: str
    ) -> None:
        incident = self._incident(incident_id)
        self._authorize(actor_id, incident)

        resolution_notes = self._validate_text(
            resolution_notes, "Resolution notes", 3000
        )

        self._transition(
            incident,
            IncidentStatus.RESOLVED,
            actor_id,
            resolution_notes
        )

        incident.resolved_at = datetime.now(timezone.utc)
        incident.resolution_notes = resolution_notes

        self._notify(
            incident,
            "INCIDENT_RESOLVED",
            incident.reporter_id
        )

    def close(self, incident_id: str, actor_id: str) -> None:
        incident = self._incident(incident_id)
        self._authorize(actor_id, incident)

        if not incident.resolution_notes:
            raise ValidationError("Resolution evidence is required.")

        self._transition(
            incident,
            IncidentStatus.CLOSED,
            actor_id,
            "Administrative closure"
        )

    def reopen(
        self,
        incident_id: str,
        actor_id: str,
        reason: str
    ) -> None:
        incident = self._incident(incident_id)
        self._authorize(actor_id, incident)

        reason = self._validate_text(reason, "Reopening reason", 1000)

        self._transition(
            incident,
            IncidentStatus.INVESTIGATING,
            actor_id,
            reason
        )

        incident.resolved_at = None
        incident.resolution_notes = None
        incident.acknowledged_at = (
            incident.acknowledged_at
            or datetime.now(timezone.utc)
        )

    def evaluate_deadlines(
        self,
        now: Optional[datetime] = None
    ) -> list[Incident]:
        now = now or datetime.now(timezone.utc)
        overdue = []

        for incident in self.incidents.values():
            if incident.status in {
                IncidentStatus.RESOLVED,
                IncidentStatus.CLOSED
            }:
                continue

            if incident.overdue_acknowledgement(now):
                overdue.append(incident)
                self._notify(
                    incident,
                    "ACKNOWLEDGEMENT_DEADLINE_BREACHED",
                    "incident_manager"
                )

            elif incident.overdue_resolution(now):
                overdue.append(incident)
                self._notify(
                    incident,
                    "RESOLUTION_DEADLINE_BREACHED",
                    "incident_manager"
                )

        return overdue

    def report_statistics(self) -> dict:
        incidents = list(self.incidents.values())

        by_severity = {
            severity.name: sum(
                i.severity == severity for i in incidents
            )
            for severity in Severity
        }

        by_status = {
            status.value: sum(
                i.status == status for i in incidents
            )
            for status in IncidentStatus
        }

        return {
            "total_incidents": len(incidents),
            "severity_distribution": by_severity,
            "status_distribution": by_status,
            "open_incidents": sum(
                i.status not in {
                    IncidentStatus.RESOLVED,
                    IncidentStatus.CLOSED
                }
                for i in incidents
            ),
            "notification_count": len(self.notification_queue),
        }

    def export_json(self, filename: str) -> None:
        path = Path(filename)
        if path.suffix.lower() != ".json":
            raise ValidationError("Export filename must end in .json")

        data = []

        for incident in self.incidents.values():
            record = asdict(incident)
            record["severity"] = incident.severity.name
            record["status"] = incident.status.value
            record["escalation_level"] = incident.escalation_level.value
            record["reported_at"] = incident.reported_at.isoformat()
            record["acknowledgement_deadline"] = (
                incident.acknowledgement_deadline.isoformat()
            )
            record["resolution_deadline"] = (
                incident.resolution_deadline.isoformat()
            )
            record["tags"] = sorted(incident.tags)
            record["acknowledged_at"] = (
                incident.acknowledged_at.isoformat()
                if incident.acknowledged_at else None
            )
            record["resolved_at"] = (
                incident.resolved_at.isoformat()
                if incident.resolved_at else None
            )
            data.append(record)

        # Restrict exported records to the incident-management dataset.
        path.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8"
        )


def run_demonstration() -> None:
    manager = EscalationManager()

    manager.register_actor(
        Actor("U001", "Operations Reporter", "reporter", "Operations")
    )
    manager.register_actor(
        Actor("U002", "Incident Responder", "responder", "Technology")
    )
    manager.register_actor(
        Actor("U003", "Operations Manager", "incident_manager", "Operations")
    )
    manager.register_actor(
        Actor("U004", "Executive Director", "administrator", "Executive")
    )

    # Example 1: Critical infrastructure problem.
    critical = manager.report(
        reporter_id="U001",
        title="Production database unavailable",
        description=(
            "The primary production database is unavailable. "
            "Customer-facing transactions are failing."
        ),
        category="Infrastructure",
        severity=Severity.CRITICAL,
        department="Technology",
        idempotency_key="INCIDENT-REQUEST-001",
        tags={"database", "production", "availability"}
    )

    manager.assign(critical.incident_id, "U003", "U002")
    manager.acknowledge(critical.incident_id, "U003")
    manager.investigate(critical.incident_id, "U002")
    manager.escalate(
        critical.incident_id,
        "U003",
        "Service outage affects customer transactions.",
        EscalationLevel.EXECUTIVE
    )

    manager.resolve(
        critical.incident_id,
        "U003",
        "Database restored and transaction processing verified."
    )
    manager.close(critical.incident_id, "U003")

    # Example 2: Medium-severity operational problem.
    operational = manager.report(
        reporter_id="U001",
        title="Delayed operational report",
        description="Daily reporting pipeline is delayed.",
        category="Reporting",
        severity=Severity.MEDIUM,
        department="Operations",
        idempotency_key="INCIDENT-REQUEST-002"
    )

    manager.assign(operational.incident_id, "U003", "U002")
    manager.acknowledge(operational.incident_id, "U003")

    # Example 3: Deadline evaluation.
    expired = manager.evaluate_deadlines(
        datetime.now(timezone.utc) + timedelta(days=2)
    )

    print("\nESCALATION MANAGEMENT REPORT")
    print("=" * 55)
    print(json.dumps(manager.report_statistics(), indent=2))
    print(f"\nOverdue incidents: {len(expired)}")

    print("\nINCIDENT DETAILS")
    for incident in manager.incidents.values():
        print(
            incident.incident_id,
            incident.severity.name,
            incident.status.value,
            incident.escalation_level.name
        )

    print("\nNOTIFICATION QUEUE")
    for notification in manager.notification_queue:
        print(
            notification["event"],
            "->",
            notification["recipient"]
        )

    manager.export_json("escalation_report.json")
    print("\nReport exported to escalation_report.json")

    # Demonstrate validation and failure handling.
    try:
        manager.resolve(
            operational.incident_id,
            "U003",
            ""
        )
    except IncidentError as error:
        print(f"\nExpected validation failure: {error}")

    try:
        manager.register_actor(
            Actor("U001", "Duplicate", "reporter", "Operations")
        )
    except IncidentError as error:
        print(f"Expected registration failure: {error}")

    assert critical.status == IncidentStatus.CLOSED
    assert operational.status == IncidentStatus.ACKNOWLEDGED
    assert len(manager.incidents) == 2


if __name__ == "__main__":
    run_demonstration()
