#!/usr/bin/env python3
"""
Leadership in Project Management

Demonstrates:
- Leadership styles and situational leadership
- Project team management
- Delegation and accountability
- Stakeholder engagement
- Decision-making
- Conflict resolution
- Risk ownership
- Team performance monitoring
- Leadership effectiveness evaluation
- Project governance and reporting
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import json
import logging
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("project_leadership")


class LeadershipStyle(Enum):
    AUTOCRATIC = "autocratic"
    DEMOCRATIC = "democratic"
    TRANSFORMATIONAL = "transformational"
    TRANSACTIONAL = "transactional"
    SERVANT = "servant"
    LAISSEZ_FAIRE = "laissez-faire"
    SITUATIONAL = "situational"


class SkillLevel(Enum):
    BEGINNER = 1
    DEVELOPING = 2
    COMPETENT = 3
    ADVANCED = 4
    EXPERT = 5


class TaskStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStatus(Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass
class TeamMember:
    member_id: int
    name: str
    role: str
    skill_level: SkillLevel
    workload: int = 0
    active: bool = True
    completed_tasks: int = 0
    development_goal: str = ""

    def __post_init__(self):
        if self.member_id <= 0:
            raise ValueError("Member ID must be positive.")
        if not self.name.strip():
            raise ValueError("Member name cannot be empty.")
        if not 0 <= self.workload <= 100:
            raise ValueError("Workload must be between 0 and 100.")


@dataclass
class ProjectTask:
    task_id: int
    title: str
    required_skill: SkillLevel
    estimated_hours: float
    priority: int
    status: TaskStatus = TaskStatus.NOT_STARTED
    assigned_to: Optional[int] = None
    progress: float = 0.0

    def __post_init__(self):
        if self.task_id <= 0:
            raise ValueError("Task ID must be positive.")
        if not self.title.strip():
            raise ValueError("Task title cannot be empty.")
        if self.estimated_hours <= 0:
            raise ValueError("Estimated hours must be positive.")
        if not 1 <= self.priority <= 5:
            raise ValueError("Priority must be between 1 and 5.")
        if not 0 <= self.progress <= 100:
            raise ValueError("Progress must be between 0 and 100.")


@dataclass
class Stakeholder:
    stakeholder_id: int
    name: str
    influence: int
    interest: int
    expectations: str
    communication_frequency: str = "weekly"

    def __post_init__(self):
        if not 1 <= self.influence <= 5:
            raise ValueError("Influence must be between 1 and 5.")
        if not 1 <= self.interest <= 5:
            raise ValueError("Interest must be between 1 and 5.")


@dataclass
class ProjectRisk:
    risk_id: int
    description: str
    probability: int
    impact: int
    owner_id: int
    mitigation: str
    status: str = "open"

    @property
    def exposure(self) -> int:
        return self.probability * self.impact

    @property
    def level(self) -> RiskLevel:
        score = self.exposure
        if score >= 20:
            return RiskLevel.CRITICAL
        if score >= 12:
            return RiskLevel.HIGH
        if score >= 6:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


@dataclass
class LeadershipDecision:
    decision_id: int
    title: str
    description: str
    decision_maker: str
    status: DecisionStatus = DecisionStatus.PROPOSED
    rationale: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class LeadershipError(Exception):
    """Base exception for leadership workflow errors."""


class AssignmentError(LeadershipError):
    """Raised when task assignment violates team constraints."""


class GovernanceError(LeadershipError):
    """Raised when a leadership decision violates governance rules."""


class ProjectLeadership:
    def __init__(
        self,
        project_name: str,
        leadership_style: LeadershipStyle
    ):
        if not project_name.strip():
            raise ValueError("Project name cannot be empty.")

        self.project_name = project_name
        self.leadership_style = leadership_style
        self.members: dict[int, TeamMember] = {}
        self.tasks: dict[int, ProjectTask] = {}
        self.stakeholders: dict[int, Stakeholder] = {}
        self.risks: dict[int, ProjectRisk] = {}
        self.decisions: dict[int, LeadershipDecision] = {}
        self.decision_history: list[dict] = []

    def add_member(self, member: TeamMember) -> None:
        if member.member_id in self.members:
            raise ValueError("Duplicate team member ID.")
        self.members[member.member_id] = member

    def add_task(self, task: ProjectTask) -> None:
        if task.task_id in self.tasks:
            raise ValueError("Duplicate task ID.")
        self.tasks[task.task_id] = task

    def add_stakeholder(self, stakeholder: Stakeholder) -> None:
        if stakeholder.stakeholder_id in self.stakeholders:
            raise ValueError("Duplicate stakeholder ID.")
        self.stakeholders[stakeholder.stakeholder_id] = stakeholder

    def add_risk(self, risk: ProjectRisk) -> None:
        if risk.risk_id in self.risks:
            raise ValueError("Duplicate risk ID.")

        if risk.owner_id not in self.members:
            raise ValueError("Risk owner does not exist.")

        if not 1 <= risk.probability <= 5:
            raise ValueError("Probability must be between 1 and 5.")

        if not 1 <= risk.impact <= 5:
            raise ValueError("Impact must be between 1 and 5.")

        self.risks[risk.risk_id] = risk

    def select_leadership_style(
        self,
        member: TeamMember,
        urgency: int,
        task_complexity: int
    ) -> LeadershipStyle:
        """
        Select a leadership approach based on competence and urgency.

        This is a decision-support rule, not a universal leadership law.
        """

        if not 1 <= urgency <= 5:
            raise ValueError("Urgency must be between 1 and 5.")

        if not 1 <= task_complexity <= 5:
            raise ValueError("Complexity must be between 1 and 5.")

        if urgency >= 5:
            return LeadershipStyle.AUTOCRATIC

        if member.skill_level.value <= 2:
            return LeadershipStyle.SITUATIONAL

        if member.skill_level.value >= 4 and urgency <= 2:
            return LeadershipStyle.DELEGATIVE if hasattr(
                LeadershipStyle, "DELEGATIVE"
            ) else LeadershipStyle.SERVANT

        if task_complexity >= 4:
            return LeadershipStyle.TRANSFORMATIONAL

        return LeadershipStyle.DEMOCRATIC

    def assign_task(
        self,
        task_id: int,
        member_id: int
    ) -> None:
        if task_id not in self.tasks:
            raise AssignmentError("Task does not exist.")

        if member_id not in self.members:
            raise AssignmentError("Team member does not exist.")

        task = self.tasks[task_id]
        member = self.members[member_id]

        if not member.active:
            raise AssignmentError("Inactive members cannot receive tasks.")

        if task.status == TaskStatus.COMPLETED:
            raise AssignmentError("Completed tasks cannot be reassigned.")

        if member.workload + 20 > 100:
            raise AssignmentError("Member workload would exceed 100%.")

        if member.skill_level.value < task.required_skill.value:
            raise AssignmentError(
                "Member does not meet the minimum skill requirement."
            )

        # Release the previous assignment before updating ownership.
        if task.assigned_to is not None:
            previous = self.members[task.assigned_to]
            previous.workload = max(0, previous.workload - 20)

        task.assigned_to = member_id
        task.status = TaskStatus.IN_PROGRESS
        member.workload += 20

        logger.info(
            "Task %s assigned to %s",
            task.title,
            member.name
        )

    def update_task_progress(
        self,
        task_id: int,
        progress: float
    ) -> None:
        if task_id not in self.tasks:
            raise ValueError("Task does not exist.")

        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100.")

        task = self.tasks[task_id]

        if task.status == TaskStatus.COMPLETED:
            raise ValueError("Completed tasks cannot be updated.")

        if task.assigned_to is None:
            raise AssignmentError("Task has no assigned owner.")

        if progress < task.progress:
            raise ValueError("Task progress cannot decrease.")

        task.progress = progress

        if progress == 100:
            task.status = TaskStatus.COMPLETED
            member = self.members[task.assigned_to]
            member.workload = max(0, member.workload - 20)
            member.completed_tasks += 1
        else:
            task.status = TaskStatus.IN_PROGRESS

    def delegate_task(self, task_id: int, member_id: int) -> dict:
        self.assign_task(task_id, member_id)

        task = self.tasks[task_id]
        member = self.members[member_id]

        return {
            "task": task.title,
            "owner": member.name,
            "accountability": True,
            "monitoring": "Progress reviewed at project checkpoints."
        }

    def resolve_conflict(
        self,
        issue: str,
        options: list[str],
        resolution: str
    ) -> dict:
        if not issue.strip():
            raise ValueError("Conflict description is required.")

        if len(options) < 2:
            raise ValueError("At least two options are required.")

        if resolution not in options:
            raise ValueError("Resolution must be one of the proposed options.")

        return {
            "issue": issue,
            "options": options,
            "resolution": resolution,
            "method": "Collaborative problem solving",
            "status": "resolved"
        }

    def create_decision(
        self,
        decision_id: int,
        title: str,
        description: str,
        decision_maker: str
    ) -> LeadershipDecision:
        if decision_id in self.decisions:
            raise ValueError("Duplicate decision ID.")

        if not title.strip() or not decision_maker.strip():
            raise ValueError("Decision title and decision maker are required.")

        decision = LeadershipDecision(
            decision_id=decision_id,
            title=title,
            description=description,
            decision_maker=decision_maker
        )

        self.decisions[decision_id] = decision
        return decision

    def decide(
        self,
        decision_id: int,
        status: DecisionStatus,
        rationale: str
    ) -> None:
        if decision_id not in self.decisions:
            raise GovernanceError("Decision does not exist.")

        if not rationale.strip():
            raise GovernanceError("A decision requires documented rationale.")

        decision = self.decisions[decision_id]

        if decision.status != DecisionStatus.PROPOSED:
            raise GovernanceError("Decision has already been processed.")

        decision.status = status
        decision.rationale = rationale

        self.decision_history.append({
            "decision_id": decision_id,
            "status": status.value,
            "rationale": rationale,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def stakeholder_priority(self) -> list[dict]:
        """
        Influence-interest analysis.

        High influence and high interest stakeholders receive active
        engagement and frequent communication.
        """

        results = []

        for stakeholder in self.stakeholders.values():
            score = stakeholder.influence * stakeholder.interest

            if stakeholder.influence >= 4 and stakeholder.interest >= 4:
                strategy = "Manage closely"
            elif stakeholder.influence >= 4:
                strategy = "Keep satisfied"
            elif stakeholder.interest >= 4:
                strategy = "Keep informed"
            else:
                strategy = "Monitor"

            results.append({
                "name": stakeholder.name,
                "score": score,
                "strategy": strategy
            })

        return sorted(
            results,
            key=lambda item: item["score"],
            reverse=True
        )

    def leadership_metrics(self) -> dict:
        total = len(self.tasks)
        completed = sum(
            task.status == TaskStatus.COMPLETED
            for task in self.tasks.values()
        )

        assigned = sum(
            task.assigned_to is not None
            for task in self.tasks.values()
        )

        average_progress = (
            sum(task.progress for task in self.tasks.values()) / total
            if total else 0.0
        )

        active_members = [
            member for member in self.members.values()
            if member.active
        ]

        average_workload = (
            sum(member.workload for member in active_members)
            / len(active_members)
            if active_members else 0.0
        )

        open_risks = [
            risk for risk in self.risks.values()
            if risk.status == "open"
        ]

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "assignment_rate": round(
                assigned / total * 100, 2
            ) if total else 0.0,
            "completion_rate": round(
                completed / total * 100, 2
            ) if total else 0.0,
            "average_progress": round(average_progress, 2),
            "average_team_workload": round(average_workload, 2),
            "open_risks": len(open_risks),
            "critical_risks": sum(
                risk.level == RiskLevel.CRITICAL
                for risk in open_risks
            )
        }

    def leadership_report(self) -> dict:
        return {
            "project": self.project_name,
            "leadership_style": self.leadership_style.value,
            "team": [
                {
                    "name": member.name,
                    "role": member.role,
                    "skill_level": member.skill_level.name,
                    "workload": member.workload,
                    "completed_tasks": member.completed_tasks
                }
                for member in self.members.values()
            ],
            "tasks": [
                {
                    "title": task.title,
                    "status": task.status.value,
                    "progress": task.progress,
                    "owner": (
                        self.members[task.assigned_to].name
                        if task.assigned_to else None
                    )
                }
                for task in self.tasks.values()
            ],
            "risks": [
                {
                    "description": risk.description,
                    "exposure": risk.exposure,
                    "level": risk.level.value,
                    "owner": self.members[risk.owner_id].name,
                    "status": risk.status
                }
                for risk in self.risks.values()
            ],
            "stakeholders": self.stakeholder_priority(),
            "metrics": self.leadership_metrics(),
            "decisions": [
                {
                    "title": decision.title,
                    "status": decision.status.value,
                    "rationale": decision.rationale
                }
                for decision in self.decisions.values()
            ]
        }

    def export_report(self, filename: str) -> None:
        """
        Write a report without accepting arbitrary object deserialization
        or executing user-provided content.
        """

        path = Path(filename)

        if path.suffix.lower() != ".json":
            raise ValueError("Report filename must use .json extension.")

        path.write_text(
            json.dumps(self.leadership_report(), indent=4),
            encoding="utf-8"
        )


def run_demonstration() -> None:
    project = ProjectLeadership(
        "Enterprise Digital Transformation",
        LeadershipStyle.TRANSFORMATIONAL
    )

    project.add_member(
        TeamMember(
            1, "Ananya", "Project Manager",
            SkillLevel.EXPERT, development_goal="Strategic leadership"
        )
    )

    project.add_member(
        TeamMember(
            2, "Rahul", "Technical Lead",
            SkillLevel.ADVANCED, development_goal="Team mentoring"
        )
    )

    project.add_member(
        TeamMember(
            3, "Meera", "Business Analyst",
            SkillLevel.COMPETENT, development_goal="Stakeholder management"
        )
    )

    project.add_task(
        ProjectTask(
            101, "Architecture assessment",
            SkillLevel.ADVANCED, 40, 5
        )
    )

    project.add_task(
        ProjectTask(
            102, "Business requirements analysis",
            SkillLevel.COMPETENT, 30, 4
        )
    )

    project.add_task(
        ProjectTask(
            103, "Implementation planning",
            SkillLevel.ADVANCED, 25, 5
        )
    )

    project.add_stakeholder(
        Stakeholder(
            1, "Executive Sponsor", 5, 5,
            "Deliver the project within approved scope and budget."
        )
    )

    project.add_stakeholder(
        Stakeholder(
            2, "Operations Manager", 4, 3,
            "Ensure operational continuity."
        )
    )

    project.add_stakeholder(
        Stakeholder(
            3, "End Users", 2, 5,
            "Provide a usable and reliable system."
        )
    )

    project.assign_task(101, 2)
    project.delegate_task(102, 3)

    project.update_task_progress(101, 60)
    project.update_task_progress(102, 100)

    project.add_risk(
        ProjectRisk(
            201,
            "Delay in technical integration",
            4,
            5,
            2,
            "Introduce integration checkpoints and contingency capacity."
        )
    )

    project.add_risk(
        ProjectRisk(
            202,
            "Insufficient stakeholder participation",
            2,
            3,
            1,
            "Conduct structured stakeholder consultations."
        )
    )

    decision = project.create_decision(
        301,
        "Adopt phased implementation",
        "Deliver the system through controlled implementation phases.",
        "Project Manager"
    )

    project.decide(
        decision.decision_id,
        DecisionStatus.APPROVED,
        "Phased delivery reduces implementation and operational risk."
    )

    conflict = project.resolve_conflict(
        "Disagreement over implementation priorities",
        ["Immediate full deployment", "Phased deployment"],
        "Phased deployment"
    )

    print("\nLEADERSHIP REPORT")
    print("=" * 60)
    print(json.dumps(project.leadership_report(), indent=4))

    print("\nCONFLICT RESOLUTION")
    print(json.dumps(conflict, indent=4))

    print("\nLEADERSHIP APPROACH")
    print(
        project.select_leadership_style(
            project.members[3], urgency=2, task_complexity=4
        ).value
    )

    project.export_report("leadership_report.json")
    print("\nReport exported to leadership_report.json")


if __name__ == "__main__":
    try:
        run_demonstration()
    except (ValueError, LeadershipError, OSError) as error:
        logger.error("Execution failed: %s", error)
        raise
