#!/usr/bin/env python3
"""
Communication Planning System

Models communication objectives, stakeholders, channels, schedules,
messages, responsibilities, delivery status, feedback, and evaluation.

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import json
import logging
import re
import unittest

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("communication_planner")


class CommunicationError(Exception):
    """Base exception for communication planning."""


class ValidationError(CommunicationError):
    pass


class SchedulingError(CommunicationError):
    pass


class StateTransitionError(CommunicationError):
    pass


class ObjectiveStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Channel(str, Enum):
    EMAIL = "email"
    MEETING = "meeting"
    REPORT = "report"
    NEWSLETTER = "newsletter"
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    PHONE = "phone"
    WORKSHOP = "workshop"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActivityStatus(str, Enum):
    PLANNED = "planned"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    SENT = "sent"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class AudienceType(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    MANAGEMENT = "management"
    TECHNICAL = "technical"
    PUBLIC = "public"


@dataclass
class Stakeholder:
    name: str
    audience: AudienceType
    email: Optional[str] = None
    department: str = ""
    influence: int = 3
    interest: int = 3
    preferred_channels: list[Channel] = field(default_factory=list)

    def __post_init__(self):
        self.name = self.name.strip()

        if not self.name:
            raise ValidationError("Stakeholder name is required.")

        if not 1 <= self.influence <= 5:
            raise ValidationError("Influence must be between 1 and 5.")

        if not 1 <= self.interest <= 5:
            raise ValidationError("Interest must be between 1 and 5.")

        if self.email and not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+", self.email
        ):
            raise ValidationError("Invalid stakeholder email.")


@dataclass
class Objective:
    title: str
    description: str
    target_audience: list[str]
    desired_outcome: str
    deadline: datetime
    priority: Priority = Priority.MEDIUM
    status: ObjectiveStatus = ObjectiveStatus.DRAFT
    objective_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        if not self.title.strip():
            raise ValidationError("Objective title is required.")

        if not self.description.strip():
            raise ValidationError("Objective description is required.")

        if not self.target_audience:
            raise ValidationError("At least one target audience is required.")

        if self.deadline.tzinfo is None:
            raise ValidationError("Deadline must be timezone-aware.")


@dataclass
class CommunicationActivity:
    objective_id: str
    title: str
    message: str
    channel: Channel
    audience: list[str]
    owner: str
    scheduled_at: datetime
    priority: Priority = Priority.MEDIUM
    status: ActivityStatus = ActivityStatus.PLANNED
    activity_id: str = field(default_factory=lambda: str(uuid4()))
    estimated_cost: float = 0.0
    approval_required: bool = False
    approved_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.title.strip():
            raise ValidationError("Activity title is required.")

        if not self.message.strip():
            raise ValidationError("Communication message is required.")

        if not self.owner.strip():
            raise ValidationError("Activity owner is required.")

        if not self.audience:
            raise ValidationError("Activity audience cannot be empty.")

        if self.scheduled_at.tzinfo is None:
            raise ValidationError("Schedule must be timezone-aware.")

        if self.estimated_cost < 0:
            raise ValidationError("Cost cannot be negative.")

    def transition(self, new_status: ActivityStatus):
        allowed = {
            ActivityStatus.PLANNED: {
                ActivityStatus.APPROVED,
                ActivityStatus.CANCELLED
            },
            ActivityStatus.APPROVED: {
                ActivityStatus.SCHEDULED,
                ActivityStatus.CANCELLED
            },
            ActivityStatus.SCHEDULED: {
                ActivityStatus.IN_PROGRESS,
                ActivityStatus.CANCELLED
            },
            ActivityStatus.IN_PROGRESS: {
                ActivityStatus.SENT,
                ActivityStatus.COMPLETED,
                ActivityStatus.FAILED
            },
            ActivityStatus.SENT: {
                ActivityStatus.COMPLETED,
                ActivityStatus.FAILED
            },
            ActivityStatus.FAILED: {
                ActivityStatus.SCHEDULED,
                ActivityStatus.CANCELLED
            },
            ActivityStatus.COMPLETED: set(),
            ActivityStatus.CANCELLED: set()
        }

        if new_status not in allowed[self.status]:
            raise StateTransitionError(
                f"Invalid transition: {self.status.value} "
                f"to {new_status.value}"
            )

        self.status = new_status

        if new_status == ActivityStatus.COMPLETED:
            self.completed_at = datetime.now(timezone.utc)


@dataclass
class Feedback:
    activity_id: str
    respondent: str
    satisfaction: int
    understanding: int
    comments: str = ""
    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        if not 1 <= self.satisfaction <= 5:
            raise ValidationError("Satisfaction must be between 1 and 5.")

        if not 1 <= self.understanding <= 5:
            raise ValidationError("Understanding must be between 1 and 5.")


class CommunicationPlanner:

    def __init__(self, budget: float):
        if budget < 0:
            raise ValidationError("Budget cannot be negative.")

        self.budget = budget
        self.stakeholders: dict[str, Stakeholder] = {}
        self.objectives: dict[str, Objective] = {}
        self.activities: dict[str, CommunicationActivity] = {}
        self.feedback: list[Feedback] = []

    @property
    def committed_cost(self) -> float:
        return sum(
            activity.estimated_cost
            for activity in self.activities.values()
            if activity.status != ActivityStatus.CANCELLED
        )

    @property
    def remaining_budget(self) -> float:
        return self.budget - self.committed_cost

    def add_stakeholder(self, stakeholder: Stakeholder):
        key = stakeholder.name.casefold()

        if key in self.stakeholders:
            raise ValidationError("Stakeholder already exists.")

        self.stakeholders[key] = stakeholder

    def add_objective(self, objective: Objective):
        if objective.objective_id in self.objectives:
            raise ValidationError("Duplicate objective identifier.")

        self.objectives[objective.objective_id] = objective

    def activate_objective(self, objective_id: str):
        objective = self._get_objective(objective_id)

        if objective.status != ObjectiveStatus.DRAFT:
            raise StateTransitionError("Only draft objectives can be activated.")

        objective.status = ObjectiveStatus.ACTIVE

    def _get_objective(self, objective_id: str) -> Objective:
        try:
            return self.objectives[objective_id]
        except KeyError:
            raise ValidationError("Objective does not exist.")

    def schedule_activity(self, activity: CommunicationActivity):
        objective = self._get_objective(activity.objective_id)

        if objective.status != ObjectiveStatus.ACTIVE:
            raise SchedulingError("Objective must be active.")

        if activity.scheduled_at > objective.deadline:
            raise SchedulingError("Activity exceeds objective deadline.")

        if activity.estimated_cost > self.remaining_budget:
            raise SchedulingError("Insufficient communication budget.")

        if activity.activity_id in self.activities:
            raise ValidationError("Duplicate activity identifier.")

        for audience_name in activity.audience:
            if audience_name.casefold() not in self.stakeholders:
                raise ValidationError(
                    f"Unknown stakeholder: {audience_name}"
                )

        if activity.approval_required:
            if not activity.approved_by:
                activity.status = ActivityStatus.PLANNED
            else:
                activity.status = ActivityStatus.APPROVED
        else:
            activity.status = ActivityStatus.SCHEDULED

        self.activities[activity.activity_id] = activity

        logger.info("Scheduled activity: %s", activity.title)

    def approve_activity(self, activity_id: str, approver: str):
        activity = self._get_activity(activity_id)

        if activity.status != ActivityStatus.PLANNED:
            raise StateTransitionError("Activity is not awaiting approval.")

        if not approver.strip():
            raise ValidationError("Approver is required.")

        activity.approved_by = approver
        activity.transition(ActivityStatus.APPROVED)

    def _get_activity(self, activity_id: str) -> CommunicationActivity:
        try:
            return self.activities[activity_id]
        except KeyError:
            raise ValidationError("Activity does not exist.")

    def start_activity(self, activity_id: str):
        activity = self._get_activity(activity_id)

        if activity.status == ActivityStatus.APPROVED:
            activity.transition(ActivityStatus.SCHEDULED)

        activity.transition(ActivityStatus.IN_PROGRESS)

    def complete_activity(self, activity_id: str, successful: bool = True):
        activity = self._get_activity(activity_id)

        if successful:
            activity.transition(ActivityStatus.COMPLETED)
        else:
            activity.transition(ActivityStatus.FAILED)

    def cancel_activity(self, activity_id: str):
        activity = self._get_activity(activity_id)
        activity.transition(ActivityStatus.CANCELLED)

    def add_feedback(self, feedback: Feedback):
        self._get_activity(feedback.activity_id)
        self.feedback.append(feedback)

    def stakeholder_matrix(self) -> dict:
        matrix = {
            "manage_closely": [],
            "keep_satisfied": [],
            "keep_informed": [],
            "monitor": []
        }

        for stakeholder in self.stakeholders.values():
            high_influence = stakeholder.influence >= 4
            high_interest = stakeholder.interest >= 4

            if high_influence and high_interest:
                category = "manage_closely"
            elif high_influence:
                category = "keep_satisfied"
            elif high_interest:
                category = "keep_informed"
            else:
                category = "monitor"

            matrix[category].append(stakeholder.name)

        return matrix

    def recommend_channel(self, stakeholder_name: str) -> Channel:
        stakeholder = self.stakeholders.get(stakeholder_name.casefold())

        if stakeholder is None:
            raise ValidationError("Unknown stakeholder.")

        if stakeholder.preferred_channels:
            return stakeholder.preferred_channels[0]

        if stakeholder.audience == AudienceType.MANAGEMENT:
            return Channel.REPORT

        if stakeholder.audience == AudienceType.TECHNICAL:
            return Channel.WORKSHOP

        if stakeholder.audience == AudienceType.PUBLIC:
            return Channel.WEBSITE

        return Channel.EMAIL

    def activities_for_period(
        self,
        start: datetime,
        end: datetime
    ) -> list[CommunicationActivity]:

        if start.tzinfo is None or end.tzinfo is None:
            raise ValidationError("Period boundaries must be timezone-aware.")

        if start > end:
            raise ValidationError("Start must not exceed end.")

        return sorted(
            [
                activity
                for activity in self.activities.values()
                if start <= activity.scheduled_at <= end
            ],
            key=lambda item: item.scheduled_at
        )

    def evaluate(self) -> dict:
        completed = [
            activity for activity in self.activities.values()
            if activity.status == ActivityStatus.COMPLETED
        ]

        total = len(self.activities)

        feedback_count = len(self.feedback)

        avg_satisfaction = (
            sum(item.satisfaction for item in self.feedback)
            / feedback_count
            if feedback_count else 0
        )

        avg_understanding = (
            sum(item.understanding for item in self.feedback)
            / feedback_count
            if feedback_count else 0
        )

        return {
            "total_activities": total,
            "completed": len(completed),
            "completion_rate": (
                len(completed) / total * 100 if total else 0
            ),
            "total_budget": self.budget,
            "committed_cost": self.committed_cost,
            "remaining_budget": self.remaining_budget,
            "feedback_count": feedback_count,
            "average_satisfaction": round(avg_satisfaction, 2),
            "average_understanding": round(avg_understanding, 2)
        }

    def export_json(self, filepath: str):
        data = {
            "budget": self.budget,
            "stakeholders": [
                {
                    **asdict(item),
                    "audience": item.audience.value,
                    "preferred_channels": [
                        channel.value for channel in item.preferred_channels
                    ]
                }
                for item in self.stakeholders.values()
            ],
            "objectives": [
                {
                    **asdict(item),
                    "deadline": item.deadline.isoformat(),
                    "priority": item.priority.value,
                    "status": item.status.value
                }
                for item in self.objectives.values()
            ],
            "activities": [
                {
                    **asdict(item),
                    "channel": item.channel.value,
                    "priority": item.priority.value,
                    "status": item.status.value,
                    "scheduled_at": item.scheduled_at.isoformat(),
                    "completed_at": (
                        item.completed_at.isoformat()
                        if item.completed_at else None
                    )
                }
                for item in self.activities.values()
            ],
            "feedback": [
                {
                    **asdict(item),
                    "recorded_at": item.recorded_at.isoformat()
                }
                for item in self.feedback
            ]
        }

        path = Path(filepath)

        # Exclusive permissions should also be configured at deployment.
        path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

        logger.info("Exported communication plan to %s", path)


def build_demo() -> CommunicationPlanner:
    planner = CommunicationPlanner(budget=100000)

    stakeholders = [
        Stakeholder(
            "Executive Management",
            AudienceType.MANAGEMENT,
            influence=5,
            interest=4,
            preferred_channels=[Channel.REPORT, Channel.MEETING]
        ),
        Stakeholder(
            "Technical Team",
            AudienceType.TECHNICAL,
            influence=3,
            interest=5,
            preferred_channels=[Channel.WORKSHOP]
        ),
        Stakeholder(
            "Employees",
            AudienceType.INTERNAL,
            influence=2,
            interest=4,
            preferred_channels=[Channel.EMAIL, Channel.MEETING]
        ),
        Stakeholder(
            "External Partners",
            AudienceType.EXTERNAL,
            influence=4,
            interest=2,
            preferred_channels=[Channel.EMAIL]
        )
    ]

    for stakeholder in stakeholders:
        planner.add_stakeholder(stakeholder)

    objective = Objective(
        title="Digital Transformation Communication",
        description="Communicate the organization's digital transformation.",
        target_audience=[
            "Executive Management",
            "Technical Team",
            "Employees",
            "External Partners"
        ],
        desired_outcome="Improve awareness and stakeholder participation.",
        deadline=datetime.now(timezone.utc) + timedelta(days=30),
        priority=Priority.HIGH
    )

    planner.add_objective(objective)
    planner.activate_objective(objective.objective_id)

    activities = [
        CommunicationActivity(
            objective_id=objective.objective_id,
            title="Management briefing",
            message="Present objectives, timelines, and expected outcomes.",
            channel=Channel.MEETING,
            audience=["Executive Management"],
            owner="Project Director",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
            priority=Priority.CRITICAL,
            estimated_cost=15000,
            approval_required=True
        ),
        CommunicationActivity(
            objective_id=objective.objective_id,
            title="Technical workshop",
            message="Explain implementation responsibilities and architecture.",
            channel=Channel.WORKSHOP,
            audience=["Technical Team"],
            owner="Technical Lead",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=5),
            estimated_cost=25000
        ),
        CommunicationActivity(
            objective_id=objective.objective_id,
            title="Employee newsletter",
            message="Share transformation milestones and participation details.",
            channel=Channel.NEWSLETTER,
            audience=["Employees"],
            owner="Communications Manager",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=8),
            estimated_cost=5000
        ),
        CommunicationActivity(
            objective_id=objective.objective_id,
            title="Partner notification",
            message="Communicate relevant operational changes to partners.",
            channel=Channel.EMAIL,
            audience=["External Partners"],
            owner="Partnership Manager",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=10),
            estimated_cost=2000
        )
    ]

    for activity in activities:
        planner.schedule_activity(activity)

    # Approval-dependent activity.
    management_activity = activities[0]
    planner.approve_activity(
        management_activity.activity_id,
        "Chief Operating Officer"
    )
    planner.start_activity(management_activity.activity_id)
    planner.complete_activity(management_activity.activity_id)

    # Demonstrate execution and evaluation.
    workshop = activities[1]
    planner.start_activity(workshop.activity_id)
    planner.complete_activity(workshop.activity_id)

    planner.add_feedback(
        Feedback(
            activity_id=workshop.activity_id,
            respondent="Technical Team Lead",
            satisfaction=5,
            understanding=4,
            comments="Clear technical communication."
        )
    )

    return planner


class CommunicationPlannerTests(unittest.TestCase):

    def test_stakeholder_matrix(self):
        planner = build_demo()
        matrix = planner.stakeholder_matrix()
        self.assertIn("Executive Management", matrix["manage_closely"])

    def test_budget_control(self):
        planner = CommunicationPlanner(100)
        self.assertEqual(planner.remaining_budget, 100)

    def test_invalid_stakeholder_influence(self):
        with self.assertRaises(ValidationError):
            Stakeholder("Invalid", AudienceType.INTERNAL, influence=6)

    def test_state_transition(self):
        planner = build_demo()
        activity = next(iter(planner.activities.values()))
        self.assertEqual(activity.status, ActivityStatus.COMPLETED)

    def test_feedback_validation(self):
        with self.assertRaises(ValidationError):
            Feedback("activity", "user", 8, 4)

    def test_unknown_objective(self):
        planner = CommunicationPlanner(100)
        with self.assertRaises(ValidationError):
            planner._get_objective("unknown")


def main():
    planner = build_demo()

    print("\nCOMMUNICATION PLANNING SYSTEM")
    print("=" * 55)

    print("\nSTAKEHOLDER ENGAGEMENT MATRIX")

    for category, names in planner.stakeholder_matrix().items():
        print(f"{category}: {', '.join(names)}")

    print("\nCHANNEL RECOMMENDATIONS")

    for stakeholder in planner.stakeholders.values():
        channel = planner.recommend_channel(stakeholder.name)
        print(f"{stakeholder.name}: {channel.value}")

    print("\nSCHEDULED COMMUNICATION ACTIVITIES")

    for activity in sorted(
        planner.activities.values(),
        key=lambda item: item.scheduled_at
    ):
        print(
            f"{activity.title}: "
            f"{activity.scheduled_at.isoformat()} | "
            f"{activity.channel.value} | "
            f"{activity.status.value}"
        )

    print("\nPERFORMANCE EVALUATION")

    for key, value in planner.evaluate().items():
        print(f"{key}: {value}")

    planner.export_json("communication_plan.json")

    print("\nVALIDATION TESTS")

    unittest.main(argv=["communication_planner.py"], exit=False)


if __name__ == "__main__":
    main()
