"""
Team Motivation Management System

Demonstrates:
- Intrinsic and extrinsic motivation
- Self-determination theory
- Autonomy, competence, and relatedness
- Goal setting and progress tracking
- Recognition and feedback
- Workload and burnout risk
- Psychological safety
- Team motivation scoring
- Personalized intervention planning
- Reporting and JSON persistence

Python 3.10+
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from statistics import mean
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class MotivationLevel(Enum):
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    CRITICAL = "Critical"


class RecognitionType(Enum):
    PRIVATE = "Private"
    PUBLIC = "Public"
    DEVELOPMENT = "Development"
    FINANCIAL = "Financial"
    TEAM = "Team"


class GoalStatus(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"


@dataclass
class TeamMember:
    member_id: int
    name: str
    role: str
    autonomy: float
    competence: float
    relatedness: float
    workload: float
    psychological_safety: float
    engagement: float
    intrinsic_motivation: float
    extrinsic_motivation: float

    def __post_init__(self):
        if self.member_id <= 0:
            raise ValueError("Member ID must be positive.")

        if not self.name.strip() or not self.role.strip():
            raise ValueError("Name and role cannot be empty.")

        for attribute in (
            "autonomy",
            "competence",
            "relatedness",
            "workload",
            "psychological_safety",
            "engagement",
            "intrinsic_motivation",
            "extrinsic_motivation",
        ):
            value = getattr(self, attribute)

            if not 0 <= value <= 100:
                raise ValueError(
                    f"{attribute} must be between 0 and 100."
                )


@dataclass
class TeamGoal:
    goal_id: int
    description: str
    owner_id: int
    target: float
    progress: float = 0
    status: GoalStatus = GoalStatus.NOT_STARTED

    def update_progress(self, value: float):
        if not 0 <= value <= self.target:
            raise ValueError("Progress must be between 0 and target.")

        self.progress = value

        if value == self.target:
            self.status = GoalStatus.COMPLETED
        elif value > 0:
            self.status = GoalStatus.IN_PROGRESS
        else:
            self.status = GoalStatus.NOT_STARTED


@dataclass
class Recognition:
    recognition_id: int
    member_id: int
    category: RecognitionType
    reason: str
    awarded_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )


class MotivationManager:

    def __init__(self):
        self.members: dict[int, TeamMember] = {}
        self.goals: dict[int, TeamGoal] = {}
        self.recognitions: list[Recognition] = []

    def add_member(self, member: TeamMember):
        if member.member_id in self.members:
            raise ValueError("Member already exists.")

        self.members[member.member_id] = member

    def add_goal(self, goal: TeamGoal):
        if goal.goal_id in self.goals:
            raise ValueError("Goal already exists.")

        if goal.owner_id not in self.members:
            raise ValueError("Goal owner does not exist.")

        if goal.target <= 0:
            raise ValueError("Goal target must be positive.")

        self.goals[goal.goal_id] = goal

    def recognize(
        self,
        recognition: Recognition
    ):
        if recognition.member_id not in self.members:
            raise ValueError("Unknown team member.")

        if not recognition.reason.strip():
            raise ValueError("Recognition reason is required.")

        self.recognitions.append(recognition)

    def calculate_motivation(
        self,
        member_id: int
    ) -> float:

        member = self.members[member_id]

        # Workload is treated as a potential source of friction.
        workload_balance = 100 - member.workload

        score = (
            member.autonomy * 0.18
            + member.competence * 0.18
            + member.relatedness * 0.16
            + member.psychological_safety * 0.16
            + member.engagement * 0.14
            + member.intrinsic_motivation * 0.12
            + workload_balance * 0.06
        )

        return round(max(0, min(100, score)), 2)

    def classify_motivation(
        self,
        member_id: int
    ) -> MotivationLevel:

        score = self.calculate_motivation(member_id)

        if score >= 80:
            return MotivationLevel.HIGH
        elif score >= 65:
            return MotivationLevel.MODERATE
        elif score >= 45:
            return MotivationLevel.LOW

        return MotivationLevel.CRITICAL

    def identify_risks(
        self,
        member_id: int
    ) -> list[str]:

        member = self.members[member_id]
        risks = []

        if member.workload >= 85:
            risks.append("High workload and potential burnout")

        if member.autonomy < 40:
            risks.append("Limited decision-making autonomy")

        if member.competence < 40:
            risks.append("Skill development or training required")

        if member.relatedness < 40:
            risks.append("Weak team relationships")

        if member.psychological_safety < 40:
            risks.append("Low psychological safety")

        if member.engagement < 40:
            risks.append("Low engagement")

        return risks

    def recommend_actions(
        self,
        member_id: int
    ) -> list[str]:

        member = self.members[member_id]
        actions = []

        if member.autonomy < 60:
            actions.append(
                "Increase ownership and decision-making authority."
            )

        if member.competence < 60:
            actions.append(
                "Provide mentoring, training, and skill development."
            )

        if member.relatedness < 60:
            actions.append(
                "Improve collaboration and peer interaction."
            )

        if member.workload > 70:
            actions.append(
                "Review workload and redistribute responsibilities."
            )

        if member.psychological_safety < 60:
            actions.append(
                "Establish safe feedback and open communication practices."
            )

        if member.engagement < 60:
            actions.append(
                "Conduct a one-to-one discussion to identify barriers."
            )

        if not actions:
            actions.append(
                "Maintain current practices and provide meaningful growth opportunities."
            )

        return actions

    def team_report(self) -> dict:

        if not self.members:
            raise ValueError("No team members available.")

        scores = {
            member_id: self.calculate_motivation(member_id)
            for member_id in self.members
        }

        return {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "team_size": len(self.members),
            "average_motivation": round(
                mean(scores.values()), 2
            ),
            "motivation_distribution": {
                level.value: sum(
                    1
                    for member_id in self.members
                    if self.classify_motivation(member_id) == level
                )
                for level in MotivationLevel
            },
            "members": [
                {
                    "member": self.members[mid].name,
                    "score": scores[mid],
                    "level": self.classify_motivation(mid).value,
                    "risks": self.identify_risks(mid),
                    "actions": self.recommend_actions(mid),
                }
                for mid in self.members
            ],
        }

    def save_report(self, filename: str):
        path = Path(filename)

        if path.suffix.lower() != ".json":
            raise ValueError("Report filename must end in .json.")

        report = self.team_report()

        # Prevent accidental exposure through overly broad file permissions
        # where supported by the operating system.
        path.write_text(
            json.dumps(report, indent=4),
            encoding="utf-8"
        )

        logger.info("Report saved to %s", path)


def demonstrate():

    manager = MotivationManager()

    manager.add_member(
        TeamMember(
            1, "Ananya", "Developer",
            85, 90, 80, 55, 90, 88, 90, 65
        )
    )

    manager.add_member(
        TeamMember(
            2, "Rahul", "Analyst",
            35, 55, 45, 90, 40, 38, 45, 70
        )
    )

    manager.add_member(
        TeamMember(
            3, "Priya", "Project Manager",
            75, 80, 85, 65, 85, 78, 80, 75
        )
    )

    manager.add_goal(
        TeamGoal(
            101,
            "Complete quarterly product release",
            1,
            100
        )
    )

    manager.goals[101].update_progress(65)

    manager.recognize(
        Recognition(
            1,
            1,
            RecognitionType.PUBLIC,
            "Successfully resolved a critical production issue."
        )
    )

    manager.recognize(
        Recognition(
            2,
            3,
            RecognitionType.DEVELOPMENT,
            "Successfully coordinated cross-functional delivery."
        )
    )

    print("\nINDIVIDUAL MOTIVATION REPORT")

    for member_id, member in manager.members.items():
        print(f"\nMember: {member.name}")
        print(
            "Score:",
            manager.calculate_motivation(member_id)
        )
        print(
            "Level:",
            manager.classify_motivation(member_id).value
        )
        print("Risks:", manager.identify_risks(member_id))
        print("Actions:", manager.recommend_actions(member_id))

    print("\nTEAM REPORT")

    report = manager.team_report()
    print(json.dumps(report, indent=4))

    # Demonstrate validation.
    try:
        TeamMember(
            4, "Test", "Intern",
            120, 50, 50, 50, 50, 50, 50, 50
        )
    except ValueError as error:
        print("\nValidation example:", error)

    manager.save_report("team_motivation_report.json")


if __name__ == "__main__":
    demonstrate()
