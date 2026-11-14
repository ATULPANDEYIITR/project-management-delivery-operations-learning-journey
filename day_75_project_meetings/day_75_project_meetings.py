from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4


# PROJECT MEETING MANAGEMENT SYSTEM
# Standard-library implementation with lifecycle, agenda,
# attendance, decisions, action tracking, and reporting.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("project_meetings")


class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class ParticipantRole(str, Enum):
    ORGANIZER = "organizer"
    CHAIRPERSON = "chairperson"
    MEMBER = "member"
    OBSERVER = "observer"


class MeetingError(Exception):
    """Base exception for meeting operations."""


class ValidationError(MeetingError):
    pass


class StateTransitionError(MeetingError):
    pass


class ResourceNotFoundError(MeetingError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty.")
    return value.strip()


@dataclass
class Participant:
    participant_id: str
    name: str
    email: str
    role: ParticipantRole
    attended: bool = False

    def __post_init__(self):
        self.name = validate_text(self.name, "Participant name")
        self.email = validate_text(self.email, "Email")
        if "@" not in self.email:
            raise ValidationError("Invalid participant email.")


@dataclass
class AgendaItem:
    item_id: str
    title: str
    owner_id: str
    duration_minutes: int
    priority: Priority
    discussion_notes: str = ""
    completed: bool = False

    def __post_init__(self):
        self.title = validate_text(self.title, "Agenda title")
        if self.duration_minutes <= 0:
            raise ValidationError("Agenda duration must be positive.")


@dataclass
class Decision:
    decision_id: str
    description: str
    recorded_by: str
    recorded_at: str
    rationale: str = ""
    status: str = "approved"


@dataclass
class ActionItem:
    action_id: str
    description: str
    assignee_id: str
    due_date: datetime
    priority: Priority
    status: ActionStatus = ActionStatus.OPEN
    completion_notes: str = ""

    def __post_init__(self):
        self.description = validate_text(
            self.description, "Action description"
        )
        if self.due_date.tzinfo is None:
            raise ValidationError("Action due date must be timezone-aware.")


@dataclass
class Meeting:
    meeting_id: str
    title: str
    project: str
    organizer_id: str
    scheduled_at: datetime
    duration_minutes: int
    location: str
    status: MeetingStatus = MeetingStatus.SCHEDULED
    participants: dict[str, Participant] = field(default_factory=dict)
    agenda: list[AgendaItem] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    actions: list[ActionItem] = field(default_factory=list)
    minutes: str = ""
    created_at: str = field(
        default_factory=lambda: utc_now().isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: utc_now().isoformat()
    )

    def __post_init__(self):
        self.title = validate_text(self.title, "Meeting title")
        self.project = validate_text(self.project, "Project")
        self.location = validate_text(self.location, "Location")

        if self.scheduled_at.tzinfo is None:
            raise ValidationError("Meeting time must include a timezone.")

        if self.duration_minutes <= 0:
            raise ValidationError("Meeting duration must be positive.")

        if self.organizer_id not in self.participants:
            raise ValidationError("Organizer must be a participant.")

    @property
    def end_time(self) -> datetime:
        return self.scheduled_at + timedelta(
            minutes=self.duration_minutes
        )

    def add_participant(self, participant: Participant):
        if self.status != MeetingStatus.SCHEDULED:
            raise StateTransitionError(
                "Participants can only be added before the meeting starts."
            )
        if participant.participant_id in self.participants:
            raise ValidationError("Participant already exists.")
        self.participants[participant.participant_id] = participant
        self.touch()

    def add_agenda_item(self, item: AgendaItem):
        if self.status != MeetingStatus.SCHEDULED:
            raise StateTransitionError(
                "Agenda cannot be modified after the meeting starts."
            )
        if item.owner_id not in self.participants:
            raise ValidationError("Agenda owner is not a participant.")
        if any(x.item_id == item.item_id for x in self.agenda):
            raise ValidationError("Duplicate agenda item.")
        self.agenda.append(item)
        self.touch()

    def mark_attendance(self, participant_id: str, attended: bool):
        self.require_participant(participant_id)
        if self.status not in (
            MeetingStatus.SCHEDULED,
            MeetingStatus.IN_PROGRESS
        ):
            raise StateTransitionError("Attendance is already closed.")
        self.participants[participant_id].attended = attended
        self.touch()

    def require_participant(self, participant_id: str):
        if participant_id not in self.participants:
            raise ResourceNotFoundError("Participant not found.")

    def start(self):
        if self.status != MeetingStatus.SCHEDULED:
            raise StateTransitionError("Meeting cannot be started.")
        self.status = MeetingStatus.IN_PROGRESS
        self.touch()
        logger.info("Meeting started: %s", self.title)

    def record_decision(
        self,
        description: str,
        recorded_by: str,
        rationale: str = ""
    ):
        if self.status != MeetingStatus.IN_PROGRESS:
            raise StateTransitionError(
                "Decisions must be recorded during a meeting."
            )

        self.require_participant(recorded_by)

        decision = Decision(
            decision_id=str(uuid4()),
            description=validate_text(description, "Decision"),
            recorded_by=recorded_by,
            recorded_at=utc_now().isoformat(),
            rationale=rationale
        )
        self.decisions.append(decision)
        self.touch()
        return decision

    def create_action(
        self,
        description: str,
        assignee_id: str,
        due_date: datetime,
        priority: Priority
    ):
        if self.status != MeetingStatus.IN_PROGRESS:
            raise StateTransitionError(
                "Actions must be assigned during an active meeting."
            )

        self.require_participant(assignee_id)

        action = ActionItem(
            action_id=str(uuid4()),
            description=description,
            assignee_id=assignee_id,
            due_date=due_date,
            priority=priority
        )
        self.actions.append(action)
        self.touch()
        return action

    def update_action(
        self,
        action_id: str,
        new_status: ActionStatus,
        completion_notes: str = ""
    ):
        action = next(
            (a for a in self.actions if a.action_id == action_id),
            None
        )

        if action is None:
            raise ResourceNotFoundError("Action item not found.")

        if action.status == ActionStatus.COMPLETED:
            raise StateTransitionError(
                "Completed actions cannot be reopened."
            )

        if (
            new_status == ActionStatus.COMPLETED
            and not completion_notes.strip()
        ):
            raise ValidationError(
                "Completion notes are required."
            )

        action.status = new_status
        action.completion_notes = completion_notes
        self.touch()

    def complete_agenda_item(self, item_id: str):
        if self.status != MeetingStatus.IN_PROGRESS:
            raise StateTransitionError("Meeting is not active.")

        item = next(
            (x for x in self.agenda if x.item_id == item_id),
            None
        )
        if item is None:
            raise ResourceNotFoundError("Agenda item not found.")

        item.completed = True
        self.touch()

    def close(self, minutes: str):
        if self.status != MeetingStatus.IN_PROGRESS:
            raise StateTransitionError("Only active meetings can close.")

        self.minutes = validate_text(minutes, "Meeting minutes")
        self.status = MeetingStatus.COMPLETED
        self.touch()
        logger.info("Meeting completed: %s", self.title)

    def cancel(self, reason: str):
        if self.status in (
            MeetingStatus.COMPLETED,
            MeetingStatus.CANCELLED
        ):
            raise StateTransitionError(
                "Meeting cannot be cancelled in its current state."
            )

        self.minutes = f"Cancellation reason: {validate_text(reason, 'Reason')}"
        self.status = MeetingStatus.CANCELLED
        self.touch()

    def touch(self):
        self.updated_at = utc_now().isoformat()


class MeetingManager:
    """Application service responsible for meeting coordination."""

    def __init__(self):
        self.meetings: dict[str, Meeting] = {}

    def schedule_meeting(self, meeting: Meeting):
        if meeting.meeting_id in self.meetings:
            raise ValidationError("Meeting ID already exists.")

        for existing in self.meetings.values():
            if existing.status not in (
                MeetingStatus.SCHEDULED,
                MeetingStatus.IN_PROGRESS
            ):
                continue

            if existing.organizer_id != meeting.organizer_id:
                continue

            overlaps = (
                meeting.scheduled_at < existing.end_time
                and existing.scheduled_at < meeting.end_time
            )

            if overlaps:
                raise ValidationError(
                    "Organizer has an overlapping meeting."
                )

        self.meetings[meeting.meeting_id] = meeting
        logger.info("Meeting scheduled: %s", meeting.title)

    def get_meeting(self, meeting_id: str) -> Meeting:
        meeting = self.meetings.get(meeting_id)
        if meeting is None:
            raise ResourceNotFoundError("Meeting not found.")
        return meeting

    def upcoming_meetings(self, reference: Optional[datetime] = None):
        reference = reference or utc_now()

        return sorted(
            [
                m for m in self.meetings.values()
                if m.status == MeetingStatus.SCHEDULED
                and m.scheduled_at >= reference
            ],
            key=lambda m: m.scheduled_at
        )

    def overdue_actions(self, reference: Optional[datetime] = None):
        reference = reference or utc_now()

        return [
            action
            for meeting in self.meetings.values()
            for action in meeting.actions
            if action.due_date < reference
            and action.status != ActionStatus.COMPLETED
        ]

    def project_report(self, project: str) -> dict:
        meetings = [
            m for m in self.meetings.values()
            if m.project == project
        ]

        actions = [
            action
            for meeting in meetings
            for action in meeting.actions
        ]

        return {
            "project": project,
            "meeting_count": len(meetings),
            "completed_meetings": sum(
                m.status == MeetingStatus.COMPLETED for m in meetings
            ),
            "cancelled_meetings": sum(
                m.status == MeetingStatus.CANCELLED for m in meetings
            ),
            "decision_count": sum(
                len(m.decisions) for m in meetings
            ),
            "total_actions": len(actions),
            "completed_actions": sum(
                a.status == ActionStatus.COMPLETED for a in actions
            ),
            "open_actions": sum(
                a.status != ActionStatus.COMPLETED for a in actions
            ),
            "overdue_actions": sum(
                a.due_date < utc_now()
                and a.status != ActionStatus.COMPLETED
                for a in actions
            )
        }

    def export_json(self, output_file: str):
        """Export a consistent snapshot without serializing Python objects."""
        payload = []

        for meeting in self.meetings.values():
            record = {
                "meeting_id": meeting.meeting_id,
                "title": meeting.title,
                "project": meeting.project,
                "organizer_id": meeting.organizer_id,
                "scheduled_at": meeting.scheduled_at.isoformat(),
                "end_time": meeting.end_time.isoformat(),
                "duration_minutes": meeting.duration_minutes,
                "location": meeting.location,
                "status": meeting.status.value,
                "participants": [
                    {
                        **asdict(p),
                        "role": p.role.value
                    }
                    for p in meeting.participants.values()
                ],
                "agenda": [
                    {
                        **asdict(a),
                        "priority": a.priority.value
                    }
                    for a in meeting.agenda
                ],
                "decisions": [
                    asdict(d) for d in meeting.decisions
                ],
                "actions": [
                    {
                        **asdict(a),
                        "priority": a.priority.value,
                        "status": a.status.value,
                        "due_date": a.due_date.isoformat()
                    }
                    for a in meeting.actions
                ],
                "minutes": meeting.minutes,
                "created_at": meeting.created_at,
                "updated_at": meeting.updated_at
            }
            payload.append(record)

        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")

        try:
            temporary.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8"
            )
            temporary.replace(path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise


def run_demo():
    manager = MeetingManager()

    organizer = Participant(
        "P001", "Project Manager", "manager@example.com",
        ParticipantRole.ORGANIZER
    )
    developer = Participant(
        "P002", "Technical Lead", "technical@example.com",
        ParticipantRole.MEMBER
    )
    analyst = Participant(
        "P003", "Business Analyst", "analyst@example.com",
        ParticipantRole.MEMBER
    )

    meeting = Meeting(
        meeting_id="M001",
        title="Project Sprint Planning",
        project="Enterprise Portal",
        organizer_id="P001",
        scheduled_at=utc_now() + timedelta(hours=1),
        duration_minutes=60,
        location="Conference Room A",
        participants={
            "P001": organizer,
            "P002": developer,
            "P003": analyst
        }
    )

    manager.schedule_meeting(meeting)

    meeting.add_agenda_item(
        AgendaItem(
            "A001", "Sprint objectives", "P001",
            15, Priority.HIGH
        )
    )
    meeting.add_agenda_item(
        AgendaItem(
            "A002", "Technical dependencies", "P002",
            20, Priority.CRITICAL
        )
    )
    meeting.add_agenda_item(
        AgendaItem(
            "A003", "Requirements clarification", "P003",
            15, Priority.MEDIUM
        )
    )

    meeting.mark_attendance("P001", True)
    meeting.mark_attendance("P002", True)
    meeting.mark_attendance("P003", True)

    meeting.start()

    meeting.complete_agenda_item("A001")
    meeting.complete_agenda_item("A002")

    meeting.record_decision(
        "Adopt the revised sprint scope.",
        "P001",
        "Technical capacity and delivery deadlines."
    )

    action = meeting.create_action(
        "Complete API integration assessment.",
        "P002",
        utc_now() + timedelta(days=5),
        Priority.HIGH
    )

    meeting.update_action(
        action.action_id,
        ActionStatus.IN_PROGRESS
    )

    meeting.close(
        "Sprint scope approved. API integration assessment assigned."
    )

    print("\nPROJECT MEETING REPORT")
    print(json.dumps(
        manager.project_report("Enterprise Portal"),
        indent=2
    ))

    print("\nUPCOMING MEETINGS")
    for item in manager.upcoming_meetings():
        print(item.title, item.scheduled_at.isoformat())

    manager.export_json("meeting_data.json")
    print("\nMeeting data exported to meeting_data.json")

    # Validation test: duplicate scheduling must fail.
    try:
        manager.schedule_meeting(meeting)
    except ValidationError as error:
        print("Expected validation:", error)

    # Validation test: a completed meeting cannot restart.
    try:
        meeting.start()
    except StateTransitionError as error:
        print("Expected state protection:", error)


if __name__ == "__main__":
    run_demo()
