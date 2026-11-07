from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("conflict_management")


class ConflictType(Enum):
    COMMUNICATION = "communication"
    ROLE_AMBIGUITY = "role_ambiguity"
    RESOURCE_ALLOCATION = "resource_allocation"
    PERFORMANCE = "performance"
    PERSONAL_DISAGREEMENT = "personal_disagreement"
    PRIORITY_MISMATCH = "priority_mismatch"
    WORKING_STYLE = "working_style"


class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ConflictStatus(Enum):
    REPORTED = "reported"
    ASSESSMENT = "assessment"
    DISCUSSION = "discussion"
    MEDIATION = "mediation"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class ResolutionMethod(Enum):
    COLLABORATION = "collaboration"
    COMPROMISE = "compromise"
    ACCOMMODATION = "accommodation"
    NEGOTIATION = "negotiation"
    MANAGER_DECISION = "manager_decision"
    FORMAL_ESCALATION = "formal_escalation"


class ConflictError(Exception):
    """Base exception for conflict-management failures."""


class ValidationError(ConflictError):
    pass


class TransitionError(ConflictError):
    pass


class AuthorizationError(ConflictError):
    pass


@dataclass
class TeamMember:
    member_id: str
    name: str
    role: str
    department: str
    active: bool = True

    def __post_init__(self):
        for name, value in (
            ("member_id", self.member_id),
            ("name", self.name),
            ("role", self.role),
            ("department", self.department),
        ):
            if not value or not value.strip():
                raise ValidationError(f"{name} cannot be empty")


@dataclass
class ResolutionAgreement:
    method: ResolutionMethod
    actions: list[str]
    responsible_members: list[str]
    deadline: datetime
    success_criteria: list[str]
    accepted_by: set[str] = field(default_factory=set)

    def validate(self, participants: set[str]):
        if not self.actions:
            raise ValidationError("An agreement needs at least one action")
        if not self.success_criteria:
            raise ValidationError("Success criteria are required")
        if not set(self.responsible_members).issubset(participants):
            raise ValidationError("Responsible members must be participants")
        if not self.accepted_by.issubset(participants):
            raise ValidationError("Acceptance must come from participants")
        if self.deadline.tzinfo is None:
            raise ValidationError("Deadline must include timezone information")


@dataclass
class ConflictCase:
    case_id: str
    title: str
    description: str
    conflict_type: ConflictType
    severity: Severity
    reporter_id: str
    participant_ids: set[str]
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: ConflictStatus = ConflictStatus.REPORTED
    assigned_mediator: Optional[str] = None
    evidence: list[str] = field(default_factory=list)
    discussion_notes: list[str] = field(default_factory=list)
    agreement: Optional[ResolutionAgreement] = None
    history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.case_id.strip():
            raise ValidationError("Case ID is required")
        if not self.title.strip():
            raise ValidationError("Title is required")
        if not self.description.strip():
            raise ValidationError("Description is required")
        if len(self.participant_ids) < 2:
            raise ValidationError("At least two participants are required")
        if self.reporter_id not in self.participant_ids:
            raise ValidationError("Reporter must be a participant")
        if self.created_at.tzinfo is None:
            raise ValidationError("Creation time must be timezone-aware")


class ConflictManager:
    TRANSITIONS = {
        ConflictStatus.REPORTED: {
            ConflictStatus.ASSESSMENT,
            ConflictStatus.ESCALATED,
        },
        ConflictStatus.ASSESSMENT: {
            ConflictStatus.DISCUSSION,
            ConflictStatus.MEDIATION,
            ConflictStatus.ESCALATED,
        },
        ConflictStatus.DISCUSSION: {
            ConflictStatus.MEDIATION,
            ConflictStatus.RESOLVED,
            ConflictStatus.ESCALATED,
        },
        ConflictStatus.MEDIATION: {
            ConflictStatus.DISCUSSION,
            ConflictStatus.RESOLVED,
            ConflictStatus.ESCALATED,
        },
        ConflictStatus.RESOLVED: {
            ConflictStatus.CLOSED,
            ConflictStatus.ESCALATED,
        },
        ConflictStatus.ESCALATED: {
            ConflictStatus.CLOSED,
        },
        ConflictStatus.CLOSED: set(),
    }

    def __init__(self):
        self.members: dict[str, TeamMember] = {}
        self.cases: dict[str, ConflictCase] = {}
        self.audit_log: list[dict] = []

    def register_member(self, member: TeamMember):
        if member.member_id in self.members:
            raise ValidationError("Member already exists")
        self.members[member.member_id] = member

    def create_case(
        self,
        case_id: str,
        title: str,
        description: str,
        conflict_type: ConflictType,
        severity: Severity,
        reporter_id: str,
        participant_ids: set[str],
    ) -> ConflictCase:

        if case_id in self.cases:
            raise ValidationError("Duplicate case ID")

        if reporter_id not in self.members:
            raise ValidationError("Unknown reporter")

        for member_id in participant_ids:
            member = self.members.get(member_id)
            if member is None or not member.active:
                raise ValidationError(
                    f"Unknown or inactive participant: {member_id}"
                )

        case = ConflictCase(
            case_id=case_id,
            title=title,
            description=description,
            conflict_type=conflict_type,
            severity=severity,
            reporter_id=reporter_id,
            participant_ids=participant_ids,
        )

        self.cases[case_id] = case
        self._audit(case_id, reporter_id, "CASE_CREATED")
        logger.info("Conflict case created: %s", case_id)
        return case

    def _audit(self, case_id: str, actor: str, action: str):
        self.audit_log.append({
            "case_id": case_id,
            "actor": actor,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def transition(
        self,
        case_id: str,
        new_status: ConflictStatus,
        actor_id: str,
    ):
        case = self._get_case(case_id)

        if actor_id not in self.members:
            raise AuthorizationError("Unknown actor")

        if new_status not in self.TRANSITIONS[case.status]:
            raise TransitionError(
                f"Cannot transition from {case.status.value} "
                f"to {new_status.value}"
            )

        old_status = case.status
        case.status = new_status

        case.history.append({
            "from": old_status.value,
            "to": new_status.value,
            "actor": actor_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        self._audit(
            case_id,
            actor_id,
            f"STATUS:{old_status.value}->{new_status.value}"
        )

    def assign_mediator(self, case_id: str, mediator_id: str):
        case = self._get_case(case_id)
        mediator = self.members.get(mediator_id)

        if mediator is None or not mediator.active:
            raise ValidationError("Mediator is unavailable")

        if mediator_id in case.participant_ids:
            raise ValidationError(
                "A participant cannot mediate their own conflict"
            )

        case.assigned_mediator = mediator_id
        self._audit(case_id, mediator_id, "MEDIATOR_ASSIGNED")

    def add_discussion_note(
        self,
        case_id: str,
        actor_id: str,
        note: str,
    ):
        case = self._get_case(case_id)

        if actor_id not in case.participant_ids | {
            case.assigned_mediator
        }:
            raise AuthorizationError("Actor cannot access this discussion")

        if case.status not in {
            ConflictStatus.DISCUSSION,
            ConflictStatus.MEDIATION,
            ConflictStatus.ASSESSMENT,
        }:
            raise TransitionError("Discussion is not available")

        if not note.strip():
            raise ValidationError("Discussion note cannot be empty")

        case.discussion_notes.append(note.strip())
        self._audit(case_id, actor_id, "DISCUSSION_NOTE_ADDED")

    def assess_conflict(self, case_id: str, manager_id: str):
        case = self._get_case(case_id)

        if manager_id not in self.members:
            raise AuthorizationError("Unknown manager")

        self.transition(
            case_id,
            ConflictStatus.ASSESSMENT,
            manager_id,
        )

        # Critical conflicts require immediate independent review.
        if case.severity == Severity.CRITICAL:
            self.transition(
                case_id,
                ConflictStatus.ESCALATED,
                manager_id,
            )

    def recommend_method(self, case_id: str) -> ResolutionMethod:
        case = self._get_case(case_id)

        if case.severity == Severity.CRITICAL:
            return ResolutionMethod.FORMAL_ESCALATION

        if case.conflict_type == ConflictType.RESOURCE_ALLOCATION:
            return ResolutionMethod.NEGOTIATION

        if case.conflict_type == ConflictType.PRIORITY_MISMATCH:
            return ResolutionMethod.COLLABORATION

        if case.conflict_type == ConflictType.PERSONAL_DISAGREEMENT:
            return ResolutionMethod.MEDIATION if hasattr(
                ResolutionMethod, "MEDIATION"
            ) else ResolutionMethod.COLLABORATION

        if case.severity == Severity.HIGH:
            return ResolutionMethod.COLLABORATION

        return ResolutionMethod.COMPROMISE

    def create_agreement(
        self,
        case_id: str,
        agreement: ResolutionAgreement,
        manager_id: str,
    ):
        case = self._get_case(case_id)

        if case.status not in {
            ConflictStatus.DISCUSSION,
            ConflictStatus.MEDIATION,
        }:
            raise TransitionError(
                "Agreement requires discussion or mediation"
            )

        if manager_id not in self.members:
            raise AuthorizationError("Unknown manager")

        agreement.validate(case.participant_ids)
        case.agreement = agreement
        self._audit(case_id, manager_id, "AGREEMENT_CREATED")

    def accept_agreement(self, case_id: str, member_id: str):
        case = self._get_case(case_id)

        if member_id not in case.participant_ids:
            raise AuthorizationError("Only participants can accept")

        if case.agreement is None:
            raise ValidationError("No agreement exists")

        case.agreement.accepted_by.add(member_id)
        self._audit(case_id, member_id, "AGREEMENT_ACCEPTED")

    def resolve_case(self, case_id: str, manager_id: str):
        case = self._get_case(case_id)

        if case.agreement is None:
            raise ValidationError("Resolution agreement is missing")

        if case.agreement.accepted_by != case.participant_ids:
            raise ValidationError(
                "All participants must accept the agreement"
            )

        self.transition(
            case_id,
            ConflictStatus.RESOLVED,
            manager_id,
        )

    def close_case(self, case_id: str, manager_id: str):
        case = self._get_case(case_id)

        if case.status not in {
            ConflictStatus.RESOLVED,
            ConflictStatus.ESCALATED,
        }:
            raise TransitionError(
                "Only resolved or escalated cases can be closed"
            )

        self.transition(
            case_id,
            ConflictStatus.CLOSED,
            manager_id,
        )

    def escalate_case(self, case_id: str, manager_id: str):
        case = self._get_case(case_id)

        self.transition(
            case_id,
            ConflictStatus.ESCALATED,
            manager_id,
        )

    def _get_case(self, case_id: str) -> ConflictCase:
        case = self.cases.get(case_id)
        if case is None:
            raise ValidationError(f"Case not found: {case_id}")
        return case

    def report(self) -> dict:
        counts = {
            status.value: 0 for status in ConflictStatus
        }

        severity_counts = {
            severity.name: 0 for severity in Severity
        }

        for case in self.cases.values():
            counts[case.status.value] += 1
            severity_counts[case.severity.name] += 1

        return {
            "total_cases": len(self.cases),
            "status_distribution": counts,
            "severity_distribution": severity_counts,
            "open_cases": sum(
                1 for case in self.cases.values()
                if case.status not in {
                    ConflictStatus.CLOSED,
                    ConflictStatus.RESOLVED,
                }
            ),
        }

    def export_json(self, file_path: str):
        # Do not export confidential discussion records by default.
        data = {
            "report": self.report(),
            "cases": [
                {
                    "case_id": case.case_id,
                    "title": case.title,
                    "type": case.conflict_type.value,
                    "severity": case.severity.name,
                    "status": case.status.value,
                    "participants": sorted(case.participant_ids),
                    "mediator": case.assigned_mediator,
                }
                for case in self.cases.values()
            ],
        }

        path = Path(file_path)
        path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )


def demonstrate():
    manager = ConflictManager()

    manager.register_member(
        TeamMember("E01", "Ananya", "Developer", "Engineering")
    )
    manager.register_member(
        TeamMember("E02", "Rahul", "Designer", "Product")
    )
    manager.register_member(
        TeamMember("E03", "Priya", "Manager", "Management")
    )
    manager.register_member(
        TeamMember("E04", "Arjun", "Mediator", "HR")
    )

    case = manager.create_case(
        case_id="CF-1001",
        title="Disagreement over release priorities",
        description=(
            "Engineering and Product disagree about the "
            "features to include in the next release."
        ),
        conflict_type=ConflictType.PRIORITY_MISMATCH,
        severity=Severity.MEDIUM,
        reporter_id="E01",
        participant_ids={"E01", "E02"},
    )

    manager.assign_mediator(case.case_id, "E04")

    manager.transition(
        case.case_id,
        ConflictStatus.ASSESSMENT,
        "E03",
    )

    manager.transition(
        case.case_id,
        ConflictStatus.DISCUSSION,
        "E03",
    )

    manager.add_discussion_note(
        case.case_id,
        "E01",
        "Engineering needs additional testing time.",
    )

    manager.add_discussion_note(
        case.case_id,
        "E02",
        "Product needs the core features before launch.",
    )

    agreement = ResolutionAgreement(
        method=ResolutionMethod.COLLABORATION,
        actions=[
            "Release core features first.",
            "Schedule remaining features for the next iteration.",
            "Review release readiness together.",
        ],
        responsible_members=["E01", "E02"],
        deadline=datetime(2026, 11, 20, tzinfo=timezone.utc),
        success_criteria=[
            "Core features pass acceptance testing.",
            "Both teams approve the release plan.",
        ],
    )

    manager.create_agreement(
        case.case_id,
        agreement,
        "E03",
    )

    manager.accept_agreement(case.case_id, "E01")
    manager.accept_agreement(case.case_id, "E02")

    manager.resolve_case(case.case_id, "E03")
    manager.close_case(case.case_id, "E03")

    print("\nCONFLICT MANAGEMENT REPORT")
    print(json.dumps(manager.report(), indent=2))

    print("\nRECOMMENDED RESOLUTION METHOD")
    print(manager.recommend_method(case.case_id).value)

    print("\nAUDIT EVENTS")
    for event in manager.audit_log:
        print(event)

    # Validation and failure-handling checks.
    assert case.status == ConflictStatus.CLOSED
    assert len(case.participant_ids) == 2

    try:
        manager.transition(
            case.case_id,
            ConflictStatus.RESOLVED,
            "E03",
        )
    except TransitionError as error:
        print("\nExpected transition failure:", error)

    try:
        manager.create_case(
            "CF-1002",
            "Invalid case",
            "Only one participant",
            ConflictType.COMMUNICATION,
            Severity.LOW,
            "E01",
            {"E01"},
        )
    except ValidationError as error:
        print("Expected validation failure:", error)

    manager.export_json("conflict_management_report.json")
    print("\nReport exported successfully.")


if __name__ == "__main__":
    demonstrate()
