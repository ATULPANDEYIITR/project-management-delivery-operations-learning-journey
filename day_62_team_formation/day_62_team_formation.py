from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Tuple
from collections import Counter
import json


class Role(str, Enum):
    PRODUCT_MANAGER = "Product Manager"
    TECH_LEAD = "Technical Lead"
    BACKEND = "Backend Engineer"
    FRONTEND = "Frontend Engineer"
    QA = "QA Engineer"
    DEVOPS = "DevOps Engineer"
    DATA = "Data Engineer"
    SECURITY = "Security Engineer"
    UX = "UX Designer"


class Availability(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    name: str
    skills: frozenset[str]
    roles: frozenset[Role]
    experience_years: float
    availability: Availability
    max_projects: int = 1
    preferred_team_size: Tuple[int, int] = (4, 8)


@dataclass(frozen=True)
class Project:
    project_id: str
    name: str
    required_skills: frozenset[str]
    required_roles: frozenset[Role]
    min_team_size: int
    max_team_size: int
    risk_level: str = "medium"


@dataclass
class Team:
    project: Project
    members: List[Candidate] = field(default_factory=list)

    @property
    def skills(self) -> Set[str]:
        return set().union(*(member.skills for member in self.members)) if self.members else set()

    @property
    def roles(self) -> Set[Role]:
        return set().union(*(member.roles for member in self.members)) if self.members else set()

    def missing_skills(self) -> Set[str]:
        return set(self.project.required_skills) - self.skills

    def missing_roles(self) -> Set[Role]:
        return set(self.project.required_roles) - self.roles

    def is_size_valid(self) -> bool:
        return self.project.min_team_size <= len(self.members) <= self.project.max_team_size


class TeamFormationError(Exception):
    pass


class TeamFormationEngine:
    def __init__(self, candidates: List[Candidate]):
        self.candidates = candidates
        self._validate_candidates()

    def _validate_candidates(self) -> None:
        ids = [candidate.candidate_id for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise TeamFormationError("Candidate IDs must be unique.")

        for candidate in self.candidates:
            if candidate.experience_years < 0:
                raise TeamFormationError(
                    f"Negative experience for {candidate.candidate_id}."
                )
            if candidate.max_projects < 1:
                raise TeamFormationError(
                    f"Invalid project capacity for {candidate.candidate_id}."
                )

    @staticmethod
    def _candidate_score(candidate: Candidate, project: Project) -> float:
        skill_match = len(candidate.skills & project.required_skills)
        role_match = len(candidate.roles & project.required_roles)
        availability_score = {
            Availability.AVAILABLE: 3.0,
            Availability.PARTIAL: 1.5,
            Availability.UNAVAILABLE: -10.0,
        }[candidate.availability]

        # Experience prevents a team from being filled only by specialists
        # with little delivery history.
        experience_score = min(candidate.experience_years, 10.0) * 0.25

        return skill_match * 4 + role_match * 5 + availability_score + experience_score

    def rank_candidates(self, project: Project) -> List[Candidate]:
        eligible = [
            candidate
            for candidate in self.candidates
            if candidate.availability != Availability.UNAVAILABLE
        ]
        return sorted(
            eligible,
            key=lambda candidate: self._candidate_score(candidate, project),
            reverse=True,
        )

    def build_team(self, project: Project) -> Team:
        if project.min_team_size <= 0 or project.max_team_size < project.min_team_size:
            raise TeamFormationError("Invalid project team-size constraints.")

        team = Team(project=project)
        used_ids: Set[str] = set()

        # First pass satisfies scarce role requirements.
        for required_role in project.required_roles:
            role_candidates = [
                candidate
                for candidate in self.rank_candidates(project)
                if required_role in candidate.roles
                and candidate.candidate_id not in used_ids
            ]

            if not role_candidates:
                raise TeamFormationError(
                    f"No eligible candidate can fill role: {required_role.value}"
                )

            selected = role_candidates[0]
            team.members.append(selected)
            used_ids.add(selected.candidate_id)

        # Second pass closes important skill gaps.
        while len(team.members) < project.min_team_size:
            available = [
                candidate
                for candidate in self.rank_candidates(project)
                if candidate.candidate_id not in used_ids
            ]

            if not available:
                raise TeamFormationError(
                    "Not enough eligible candidates to reach minimum team size."
                )

            selected = max(
                available,
                key=lambda candidate: (
                    len(candidate.skills - team.skills),
                    len(candidate.skills & project.required_skills),
                    candidate.experience_years,
                ),
            )
            team.members.append(selected)
            used_ids.add(selected.candidate_id)

        # Optional members are added only when they materially improve coverage.
        while len(team.members) < project.max_team_size:
            missing_before = len(team.missing_skills()) + len(team.missing_roles())

            available = [
                candidate
                for candidate in self.rank_candidates(project)
                if candidate.candidate_id not in used_ids
            ]

            if not available:
                break

            selected = max(
                available,
                key=lambda candidate: (
                    len(candidate.skills & team.missing_skills()),
                    len(candidate.roles & team.missing_roles()),
                    candidate.experience_years,
                ),
            )

            team.members.append(selected)
            used_ids.add(selected.candidate_id)

            missing_after = len(team.missing_skills()) + len(team.missing_roles())
            if missing_after >= missing_before:
                team.members.pop()
                break

        return team

    @staticmethod
    def validate_team(team: Team) -> Dict[str, object]:
        member_ids = [member.candidate_id for member in team.members]
        duplicate_members = [
            candidate_id
            for candidate_id, count in Counter(member_ids).items()
            if count > 1
        ]

        return {
            "valid_size": team.is_size_valid(),
            "missing_roles": sorted(role.value for role in team.missing_roles()),
            "missing_skills": sorted(team.missing_skills()),
            "duplicate_members": duplicate_members,
            "available_members": sum(
                member.availability == Availability.AVAILABLE
                for member in team.members
            ),
            "partial_members": sum(
                member.availability == Availability.PARTIAL
                for member in team.members
            ),
        }


def demonstrate() -> None:
    candidates = [
        Candidate(
            "C001", "Aarav",
            frozenset({"roadmapping", "stakeholder-management", "analytics"}),
            frozenset({Role.PRODUCT_MANAGER}),
            7, Availability.AVAILABLE,
        ),
        Candidate(
            "C002", "Meera",
            frozenset({"architecture", "python", "postgresql", "security"}),
            frozenset({Role.TECH_LEAD, Role.BACKEND}),
            9, Availability.AVAILABLE,
        ),
        Candidate(
            "C003", "Kabir",
            frozenset({"python", "fastapi", "postgresql", "testing"}),
            frozenset({Role.BACKEND}),
            5, Availability.AVAILABLE,
        ),
        Candidate(
            "C004", "Diya",
            frozenset({"javascript", "react", "accessibility", "css"}),
            frozenset({Role.FRONTEND, Role.UX}),
            4, Availability.AVAILABLE,
        ),
        Candidate(
            "C005", "Rohan",
            frozenset({"pytest", "automation", "testing", "quality"}),
            frozenset({Role.QA}),
            6, Availability.AVAILABLE,
        ),
        Candidate(
            "C006", "Ishita",
            frozenset({"docker", "kubernetes", "ci-cd", "linux"}),
            frozenset({Role.DEVOPS}),
            6, Availability.PARTIAL,
        ),
        Candidate(
            "C007", "Vikram",
            frozenset({"etl", "python", "sql", "analytics"}),
            frozenset({Role.DATA}),
            5, Availability.AVAILABLE,
        ),
        Candidate(
            "C008", "Nisha",
            frozenset({"threat-modeling", "security", "iam", "python"}),
            frozenset({Role.SECURITY}),
            7, Availability.AVAILABLE,
        ),
        Candidate(
            "C009", "Arjun",
            frozenset({"javascript", "typescript", "react"}),
            frozenset({Role.FRONTEND}),
            3, Availability.UNAVAILABLE,
        ),
    ]

    project = Project(
        project_id="P001",
        name="Secure Operations Analytics Platform",
        required_skills=frozenset({
            "roadmapping",
            "architecture",
            "python",
            "postgresql",
            "javascript",
            "testing",
            "docker",
            "security",
        }),
        required_roles=frozenset({
            Role.PRODUCT_MANAGER,
            Role.TECH_LEAD,
            Role.BACKEND,
            Role.FRONTEND,
            Role.QA,
            Role.DEVOPS,
            Role.SECURITY,
        }),
        min_team_size=6,
        max_team_size=8,
        risk_level="high",
    )

    engine = TeamFormationEngine(candidates)
    team = engine.build_team(project)
    validation = engine.validate_team(team)

    output = {
        "project": project.name,
        "team": [
            {
                "id": member.candidate_id,
                "name": member.name,
                "roles": sorted(role.value for role in member.roles),
                "skills": sorted(member.skills),
                "availability": member.availability.value,
            }
            for member in team.members
        ],
        "covered_roles": sorted(role.value for role in team.roles),
        "covered_skills": sorted(team.skills),
        "validation": validation,
    }

    print(json.dumps(output, indent=2))

    assert len(team.members) >= project.min_team_size
    assert len(team.members) <= project.max_team_size
    assert not validation["duplicate_members"]
    assert not validation["missing_roles"]

    try:
        impossible_project = Project(
            "P002",
            "Impossible Security Project",
            frozenset({"quantum-hardware"}),
            frozenset({Role.SECURITY}),
            2,
            3,
        )
        engine.build_team(impossible_project)
    except TeamFormationError as exc:
        print(f"\nExpected formation failure: {exc}")


if __name__ == "__main__":
    demonstrate()
