"""
Project Team Roles: A comprehensive study through Python.

This standalone program teaches how project teams are structured, how roles
interact, how responsibilities can be modeled, and how a project-management
workflow can be implemented programmatically.

The examples progress from basic terminology to a complete project-team
simulation involving role assignment, responsibility validation, workload
analysis, dependency management, risk ownership, communication paths,
decision rights, project health, and reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from statistics import mean
from typing import Dict, List, Set, Tuple, Optional


# ============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# ============================================================================

print("=" * 78)
print("PROJECT TEAM ROLES")
print("=" * 78)

print(
    """
A project team is a group of people with complementary responsibilities
working toward defined project objectives.

Important terms:

Project sponsor:
    Provides strategic support, authority, funding, and organizational backing.

Project manager:
    Coordinates scope, schedule, resources, risks, communication, and delivery.

Product owner:
    Represents product value and helps prioritize requirements.

Business analyst:
    Elicits, analyzes, validates, and documents business requirements.

Technical lead:
    Provides technical direction and resolves significant engineering decisions.

Developer:
    Designs, implements, tests, and maintains software functionality.

UX/UI designer:
    Designs user experiences, interfaces, workflows, and interaction patterns.

QA/test engineer:
    Verifies quality, detects defects, and evaluates acceptance criteria.

DevOps/platform engineer:
    Supports environments, deployment, automation, observability, and reliability.

Security specialist:
    Identifies security requirements, threats, vulnerabilities, and controls.

Data specialist:
    Designs data structures, pipelines, analysis, quality controls, or models.

Stakeholder:
    A person or organization affected by the project or capable of influencing it.

A role describes responsibility and authority. A person may occupy several roles,
and one role may be shared by several people depending on project scale.
"""
)


# ============================================================================
# 2. BASIC ROLE CLASSIFICATION
# ============================================================================

class RoleCategory(Enum):
    GOVERNANCE = "Governance"
    MANAGEMENT = "Management"
    PRODUCT = "Product"
    ANALYSIS = "Analysis"
    DESIGN = "Design"
    ENGINEERING = "Engineering"
    QUALITY = "Quality"
    OPERATIONS = "Operations"
    SECURITY = "Security"
    DATA = "Data"
    STAKEHOLDER = "Stakeholder"


ROLE_CATEGORIES = {
    "Project Sponsor": RoleCategory.GOVERNANCE,
    "Project Manager": RoleCategory.MANAGEMENT,
    "Product Owner": RoleCategory.PRODUCT,
    "Business Analyst": RoleCategory.ANALYSIS,
    "UX/UI Designer": RoleCategory.DESIGN,
    "Technical Lead": RoleCategory.ENGINEERING,
    "Software Developer": RoleCategory.ENGINEERING,
    "QA Engineer": RoleCategory.QUALITY,
    "DevOps Engineer": RoleCategory.OPERATIONS,
    "Security Specialist": RoleCategory.SECURITY,
    "Data Engineer": RoleCategory.DATA,
    "Stakeholder": RoleCategory.STAKEHOLDER,
}

for role_name, category in ROLE_CATEGORIES.items():
    print(f"{role_name:24} -> {category.value}")


# ============================================================================
# 3. RESPONSIBILITY MODEL
# ============================================================================

class ResponsibilityType(Enum):
    RESPONSIBLE = "Responsible"
    ACCOUNTABLE = "Accountable"
    CONSULTED = "Consulted"
    INFORMED = "Informed"


@dataclass
class TeamMember:
    name: str
    role: str
    department: str
    skills: Set[str]
    weekly_capacity: float
    availability: float = 1.0

    @property
    def effective_capacity(self) -> float:
        """Available hours after accounting for availability."""
        return self.weekly_capacity * self.availability

    def can_perform(self, required_skill: str) -> bool:
        return required_skill.lower() in {skill.lower() for skill in self.skills}


@dataclass
class Task:
    task_id: str
    name: str
    required_skill: str
    estimated_hours: float
    priority: int
    owner: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    status: str = "Not Started"

    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """A task is ready only when all dependencies are complete."""
        return all(dependency in completed_tasks for dependency in self.dependencies)


# ============================================================================
# 4. CREATING A PROJECT TEAM
# ============================================================================

team = [
    TeamMember(
        name="Priya",
        role="Project Manager",
        department="PMO",
        skills={"planning", "risk management", "communication", "leadership"},
        weekly_capacity=40,
    ),
    TeamMember(
        name="Arjun",
        role="Product Owner",
        department="Product",
        skills={"product strategy", "prioritization", "requirements"},
        weekly_capacity=35,
    ),
    TeamMember(
        name="Meera",
        role="Business Analyst",
        department="Business Analysis",
        skills={"requirements", "process analysis", "stakeholder analysis"},
        weekly_capacity=40,
    ),
    TeamMember(
        name="Rahul",
        role="Technical Lead",
        department="Engineering",
        skills={"architecture", "python", "security", "code review"},
        weekly_capacity=40,
    ),
    TeamMember(
        name="Neha",
        role="Software Developer",
        department="Engineering",
        skills={"python", "javascript", "api development", "testing"},
        weekly_capacity=40,
    ),
    TeamMember(
        name="Vikram",
        role="QA Engineer",
        department="Quality",
        skills={"testing", "automation testing", "quality assurance"},
        weekly_capacity=40,
    ),
    TeamMember(
        name="Sara",
        role="DevOps Engineer",
        department="Operations",
        skills={"docker", "ci/cd", "cloud", "monitoring"},
        weekly_capacity=40,
    ),
    TeamMember(
        name="Karan",
        role="Security Specialist",
        department="Security",
        skills={"security", "threat modeling", "application security"},
        weekly_capacity=32,
    ),
]


def print_team(members: List[TeamMember]) -> None:
    print("\nPROJECT TEAM")
    print("-" * 78)
    for member in members:
        skills = ", ".join(sorted(member.skills))
        print(
            f"{member.name:10} | {member.role:22} | "
            f"{member.department:18} | {skills}"
        )


print_team(team)


# ============================================================================
# 5. ROLE RESPONSIBILITIES
# ============================================================================

ROLE_RESPONSIBILITIES: Dict[str, List[str]] = {
    "Project Sponsor": [
        "Approve strategic direction",
        "Provide organizational support",
        "Resolve escalated organizational issues",
        "Support funding decisions",
    ],
    "Project Manager": [
        "Coordinate project execution",
        "Manage schedule",
        "Manage risks and issues",
        "Coordinate communication",
        "Track delivery",
    ],
    "Product Owner": [
        "Prioritize product backlog",
        "Clarify product value",
        "Accept completed functionality",
        "Represent customer needs",
    ],
    "Business Analyst": [
        "Gather requirements",
        "Model business processes",
        "Clarify requirements",
        "Validate business rules",
    ],
    "Technical Lead": [
        "Guide technical architecture",
        "Review technical decisions",
        "Manage technical risks",
        "Mentor developers",
    ],
    "Software Developer": [
        "Implement functionality",
        "Write automated tests",
        "Fix defects",
        "Maintain code",
    ],
    "QA Engineer": [
        "Design test strategy",
        "Execute tests",
        "Report defects",
        "Validate quality criteria",
    ],
    "DevOps Engineer": [
        "Automate deployment",
        "Maintain environments",
        "Monitor systems",
        "Support operational reliability",
    ],
    "Security Specialist": [
        "Identify threats",
        "Review security controls",
        "Assess vulnerabilities",
        "Support secure design",
    ],
}

print("\nROLE RESPONSIBILITIES")
print("-" * 78)
for role, responsibilities in ROLE_RESPONSIBILITIES.items():
    print(f"\n{role}")
    for responsibility in responsibilities:
        print(f"  - {responsibility}")


# ============================================================================
# 6. RACI MODEL
# ============================================================================

@dataclass
class RaciAssignment:
    task: str
    assignments: Dict[str, ResponsibilityType]

    def validate(self) -> List[str]:
        errors = []

        accountable_count = sum(
            value == ResponsibilityType.ACCOUNTABLE
            for value in self.assignments.values()
        )

        if accountable_count == 0:
            errors.append("No Accountable role is assigned.")
        elif accountable_count > 1:
            errors.append("More than one Accountable role is assigned.")

        if not any(
            value == ResponsibilityType.RESPONSIBLE
            for value in self.assignments.values()
        ):
            errors.append("No Responsible role is assigned.")

        return errors


raci_matrix = [
    RaciAssignment(
        task="Define requirements",
        assignments={
            "Project Manager": ResponsibilityType.ACCOUNTABLE,
            "Product Owner": ResponsibilityType.CONSULTED,
            "Business Analyst": ResponsibilityType.RESPONSIBLE,
            "Technical Lead": ResponsibilityType.CONSULTED,
        },
    ),
    RaciAssignment(
        task="Design architecture",
        assignments={
            "Project Manager": ResponsibilityType.INFORMED,
            "Product Owner": ResponsibilityType.CONSULTED,
            "Technical Lead": ResponsibilityType.ACCOUNTABLE,
            "Software Developer": ResponsibilityType.RESPONSIBLE,
            "Security Specialist": ResponsibilityType.CONSULTED,
        },
    ),
    RaciAssignment(
        task="Implement feature",
        assignments={
            "Project Manager": ResponsibilityType.INFORMED,
            "Product Owner": ResponsibilityType.CONSULTED,
            "Technical Lead": ResponsibilityType.ACCOUNTABLE,
            "Software Developer": ResponsibilityType.RESPONSIBLE,
            "QA Engineer": ResponsibilityType.CONSULTED,
        },
    ),
    RaciAssignment(
        task="Release system",
        assignments={
            "Project Manager": ResponsibilityType.ACCOUNTABLE,
            "Technical Lead": ResponsibilityType.CONSULTED,
            "DevOps Engineer": ResponsibilityType.RESPONSIBLE,
            "QA Engineer": ResponsibilityType.CONSULTED,
            "Security Specialist": ResponsibilityType.CONSULTED,
        },
    ),
]

print("\nRACI VALIDATION")
print("-" * 78)

for assignment in raci_matrix:
    errors = assignment.validate()
    if errors:
        print(f"{assignment.task}: INVALID")
        for error in errors:
            print(f"  {error}")
    else:
        print(f"{assignment.task}: VALID")


# ============================================================================
# 7. PROJECT TASKS AND DEPENDENCIES
# ============================================================================

tasks = [
    Task("T1", "Collect business requirements", "requirements", 16, 1),
    Task(
        "T2",
        "Design technical architecture",
        "architecture",
        20,
        1,
        dependencies=["T1"],
    ),
    Task(
        "T3",
        "Implement API",
        "python",
        32,
        2,
        dependencies=["T2"],
    ),
    Task(
        "T4",
        "Build automated tests",
        "testing",
        24,
        2,
        dependencies=["T3"],
    ),
    Task(
        "T5",
        "Configure CI/CD",
        "ci/cd",
        16,
        2,
        dependencies=["T3"],
    ),
    Task(
        "T6",
        "Perform security review",
        "security",
        16,
        1,
        dependencies=["T3"],
    ),
    Task(
        "T7",
        "Production release",
        "cloud",
        12,
        1,
        dependencies=["T4", "T5", "T6"],
    ),
]


# ============================================================================
# 8. SKILL-BASED TASK ASSIGNMENT
# ============================================================================

def assign_task(task: Task, members: List[TeamMember]) -> Optional[TeamMember]:
    """
    Select a qualified team member with enough remaining capacity.

    The example uses a simple strategy: among qualified members, select the
    person with the greatest remaining capacity. Production systems could use
    optimization algorithms, historical performance, availability calendars,
    cost, geographic constraints, or team policies.
    """
    qualified = [
        member
        for member in members
        if member.can_perform(task.required_skill)
    ]

    if not qualified:
        return None

    return max(
        qualified,
        key=lambda member: member.effective_capacity
    )


remaining_capacity = {
    member.name: member.effective_capacity
    for member in team
}

print("\nTASK ASSIGNMENT")
print("-" * 78)

for task in sorted(tasks, key=lambda item: (item.priority, item.task_id)):
    candidates = [
        member
        for member in team
        if member.can_perform(task.required_skill)
        and remaining_capacity[member.name] >= task.estimated_hours
    ]

    if candidates:
        selected = max(
            candidates,
            key=lambda member: remaining_capacity[member.name]
        )
        task.owner = selected.name
        remaining_capacity[selected.name] -= task.estimated_hours
        task.status = "Assigned"
        print(
            f"{task.task_id} | {task.name:30} | "
            f"{selected.name:10} | {task.estimated_hours:5.1f} hours"
        )
    else:
        print(
            f"{task.task_id} | {task.name:30} | "
            f"UNASSIGNED | insufficient capacity or skill"
        )


# ============================================================================
# 9. DEPENDENCY GRAPH AND TOPOLOGICAL ORDER
# ============================================================================

def topological_order(project_tasks: List[Task]) -> List[str]:
    """
    Produce an execution order using Kahn's topological-sort algorithm.

    A directed edge A -> B means B depends on A.
    Complexity: O(V + E), where V is the number of tasks and E is the
    number of dependency relationships.
    """
    task_map = {task.task_id: task for task in project_tasks}
    indegree = {task.task_id: 0 for task in project_tasks}
    graph: Dict[str, List[str]] = defaultdict(list)

    for task in project_tasks:
        for dependency in task.dependencies:
            if dependency not in task_map:
                raise ValueError(
                    f"Task {task.task_id} depends on unknown task {dependency}."
                )
            graph[dependency].append(task.task_id)
            indegree[task.task_id] += 1

    queue = deque(
        task_id for task_id, degree in indegree.items() if degree == 0
    )
    ordered_tasks = []

    while queue:
        current = queue.popleft()
        ordered_tasks.append(current)

        for dependent in graph[current]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)

    if len(ordered_tasks) != len(project_tasks):
        raise ValueError("Circular dependency detected.")

    return ordered_tasks


print("\nTASK DEPENDENCY ORDER")
print("-" * 78)
print(" -> ".join(topological_order(tasks)))


# ============================================================================
# 10. EDGE CASE: CIRCULAR DEPENDENCY
# ============================================================================

circular_tasks = [
    Task("A", "Task A", "testing", 4, 1, dependencies=["C"]),
    Task("B", "Task B", "testing", 4, 1, dependencies=["A"]),
    Task("C", "Task C", "testing", 4, 1, dependencies=["B"]),
]

print("\nCIRCULAR DEPENDENCY TEST")
print("-" * 78)

try:
    topological_order(circular_tasks)
except ValueError as error:
    print(f"Correctly detected failure: {error}")


# ============================================================================
# 11. WORKLOAD ANALYSIS
# ============================================================================

def calculate_workload(
    project_tasks: List[Task],
) -> Dict[str, float]:
    workload = defaultdict(float)

    for task in project_tasks:
        if task.owner:
            workload[task.owner] += task.estimated_hours

    return dict(workload)


workload = calculate_workload(tasks)

print("\nWORKLOAD ANALYSIS")
print("-" * 78)

member_map = {member.name: member for member in team}

for name, hours in sorted(workload.items()):
    capacity = member_map[name].effective_capacity
    utilization = hours / capacity * 100
    print(
        f"{name:10} | planned={hours:5.1f} h | "
        f"capacity={capacity:5.1f} h | utilization={utilization:6.1f}%"
    )


# ============================================================================
# 12. RESPONSIBILITY OVERLAP
# ============================================================================

def find_raci_overlaps(
    assignments: List[RaciAssignment],
) -> Dict[str, Dict[str, int]]:
    """
    Count how often each person receives each RACI responsibility.

    This can expose over-centralization, where one person is accountable,
    responsible, consulted, and informed across too many activities.
    """
    counts: Dict[str, Dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for assignment in assignments:
        for role, responsibility in assignment.assignments.items():
            counts[role][responsibility.value] += 1

    return {
        role: dict(values)
        for role, values in counts.items()
    }


print("\nRACI DISTRIBUTION")
print("-" * 78)

raci_distribution = find_raci_overlaps(raci_matrix)

for role, distribution in raci_distribution.items():
    print(f"{role}: {distribution}")


# ============================================================================
# 13. STAKEHOLDER COMMUNICATION
# ============================================================================

@dataclass
class CommunicationChannel:
    name: str
    participants: Set[str]
    purpose: str
    frequency: str


communication_channels = [
    CommunicationChannel(
        name="Daily stand-up",
        participants={
            "Project Manager",
            "Technical Lead",
            "Software Developer",
            "QA Engineer",
            "DevOps Engineer",
        },
        purpose="Execution coordination and blockers",
        frequency="Daily",
    ),
    CommunicationChannel(
        name="Product review",
        participants={
            "Project Manager",
            "Product Owner",
            "Business Analyst",
            "Technical Lead",
        },
        purpose="Requirements and product decisions",
        frequency="Weekly",
    ),
    CommunicationChannel(
        name="Security review",
        participants={
            "Technical Lead",
            "Security Specialist",
            "Software Developer",
            "DevOps Engineer",
        },
        purpose="Threats, vulnerabilities, and controls",
        frequency="At design and release gates",
    ),
]


print("\nCOMMUNICATION STRUCTURE")
print("-" * 78)

for channel in communication_channels:
    print(
        f"{channel.name}: {channel.frequency} | "
        f"{channel.purpose} | participants={len(channel.participants)}"
    )


# ============================================================================
# 14. DECISION RIGHTS
# ============================================================================

DECISION_RIGHTS = {
    "Budget approval": "Project Sponsor",
    "Product priority": "Product Owner",
    "Technical architecture": "Technical Lead",
    "Project schedule coordination": "Project Manager",
    "Quality acceptance evidence": "QA Engineer",
    "Deployment implementation": "DevOps Engineer",
    "Security control approval": "Security Specialist",
}

print("\nDECISION RIGHTS")
print("-" * 78)

for decision, owner in DECISION_RIGHTS.items():
    print(f"{decision:32} -> {owner}")


# ============================================================================
# 15. RISK OWNERSHIP
# ============================================================================

@dataclass
class Risk:
    risk_id: str
    description: str
    probability: float
    impact: float
    owner_role: str
    mitigation: str

    @property
    def exposure(self) -> float:
        return self.probability * self.impact


risks = [
    Risk(
        "R1",
        "Unclear requirements cause rework",
        0.40,
        8,
        "Business Analyst",
        "Use acceptance criteria and stakeholder validation.",
    ),
    Risk(
        "R2",
        "Architecture does not scale",
        0.25,
        9,
        "Technical Lead",
        "Review architecture and perform load-oriented design analysis.",
    ),
    Risk(
        "R3",
        "Security vulnerability reaches production",
        0.20,
        10,
        "Security Specialist",
        "Threat modeling, secure review, and release security checks.",
    ),
    Risk(
        "R4",
        "Deployment failure",
        0.25,
        7,
        "DevOps Engineer",
        "Automated deployment and rollback procedures.",
    ),
]

print("\nRISK REGISTER")
print("-" * 78)

for risk in sorted(risks, key=lambda item: item.exposure, reverse=True):
    print(
        f"{risk.risk_id} | exposure={risk.exposure:4.2f} | "
        f"owner={risk.owner_role:20} | {risk.description}"
    )


# ============================================================================
# 16. TEAM COMMUNICATION NETWORK
# ============================================================================

def communication_degree(
    channels: List[CommunicationChannel],
) -> Dict[str, int]:
    degree = defaultdict(int)

    for channel in channels:
        for participant in channel.participants:
            degree[participant] += 1

    return dict(degree)


print("\nCOMMUNICATION NETWORK PARTICIPATION")
print("-" * 78)

degrees = communication_degree(communication_channels)

for person, count in sorted(
    degrees.items(),
    key=lambda item: item[1],
    reverse=True
):
    print(f"{person:10} participates in {count} communication channel(s)")


# ============================================================================
# 17. TEAM COVERAGE ANALYSIS
# ============================================================================

required_capabilities = {
    "planning",
    "requirements",
    "architecture",
    "python",
    "testing",
    "ci/cd",
    "security",
    "cloud",
}

available_capabilities = set()

for member in team:
    available_capabilities.update(
        capability.lower() for capability in member.skills
    )

missing_capabilities = required_capabilities - available_capabilities

print("\nCAPABILITY COVERAGE")
print("-" * 78)
print(f"Required capabilities: {sorted(required_capabilities)}")
print(f"Missing capabilities:  {sorted(missing_capabilities)}")


# ============================================================================
# 18. PROJECT HEALTH INDICATORS
# ============================================================================

def project_health(
    project_tasks: List[Task],
    project_risks: List[Risk],
) -> Dict[str, float]:
    assigned = sum(task.owner is not None for task in project_tasks)
    assignment_rate = assigned / len(project_tasks) if project_tasks else 1.0

    total_hours = sum(task.estimated_hours for task in project_tasks)
    assigned_hours = sum(
        task.estimated_hours
        for task in project_tasks
        if task.owner is not None
    )
    coverage_rate = assigned_hours / total_hours if total_hours else 1.0

    high_risk_count = sum(risk.exposure >= 5 for risk in project_risks)

    average_utilization = mean(
        [
            workload.get(member.name, 0)
            / member.effective_capacity
            for member in team
            if member.effective_capacity > 0
        ]
    )

    return {
        "assignment_rate": assignment_rate,
        "work_coverage": coverage_rate,
        "high_risk_count": high_risk_count,
        "average_utilization": average_utilization,
    }


health = project_health(tasks, risks)

print("\nPROJECT HEALTH INDICATORS")
print("-" * 78)
print(f"Task assignment rate : {health['assignment_rate'] * 100:6.1f}%")
print(f"Work coverage        : {health['work_coverage'] * 100:6.1f}%")
print(f"High-risk items      : {health['high_risk_count']}")
print(f"Average utilization  : {health['average_utilization'] * 100:6.1f}%")


# ============================================================================
# 19. ROLE COMPARISON
# ============================================================================

ROLE_DISTINCTIONS = {
    "Project Manager vs Product Owner": (
        "The project manager focuses primarily on project execution, "
        "coordination, constraints, and delivery. The product owner focuses "
        "primarily on product value, priorities, and backlog decisions."
    ),
    "Project Manager vs Technical Lead": (
        "The project manager coordinates project-level execution. "
        "The technical lead provides technical direction and engineering "
        "decision leadership."
    ),
    "Business Analyst vs Product Owner": (
        "The business analyst analyzes requirements and processes. "
        "The product owner owns product priorities and value decisions."
    ),
    "Developer vs QA Engineer": (
        "Developers build and maintain functionality. QA engineers provide "
        "independent or complementary quality verification."
    ),
    "Technical Lead vs Developer": (
        "A technical lead usually carries broader architectural and "
        "technical decision responsibility, while a developer focuses more "
        "directly on implementation."
    ),
}

print("\nIMPORTANT ROLE DISTINCTIONS")
print("-" * 78)

for comparison, explanation in ROLE_DISTINCTIONS.items():
    print(f"{comparison}:")
    print(f"  {explanation}")


# ============================================================================
# 20. COMMON MISTAKES
# ============================================================================

common_mistakes = [
    "Assigning responsibility without authority.",
    "Giving multiple people conflicting accountability for one decision.",
    "Creating roles without defining measurable responsibilities.",
    "Assuming a job title automatically defines every responsibility.",
    "Ignoring workload and availability.",
    "Failing to identify role gaps.",
    "Allowing unclear decision ownership.",
    "Excluding quality and security until the end.",
    "Using communication meetings without a defined purpose.",
    "Treating the RACI matrix as a substitute for actual collaboration.",
]

print("\nCOMMON PROJECT TEAM MISTAKES")
print("-" * 78)

for mistake in common_mistakes:
    print(f"- {mistake}")


# ============================================================================
# 21. ADVANCED DESIGN PRINCIPLES
# ============================================================================

design_principles = {
    "Clear accountability": "Each important decision should have an identifiable owner.",
    "Skill alignment": "Assign work according to demonstrated capabilities.",
    "Capacity awareness": "Planned work should be compared with realistic availability.",
    "Separation of concerns": "Different responsibilities should be separated where useful.",
    "Cross-functional collaboration": "Delivery requires coordinated business, technical, quality, and operational perspectives.",
    "Escalation paths": "Teams need explicit mechanisms for unresolved decisions and risks.",
    "Traceability": "Requirements should connect to implementation, tests, and acceptance.",
    "Adaptability": "Roles may change according to project phase and organizational context.",
}

print("\nADVANCED TEAM DESIGN PRINCIPLES")
print("-" * 78)

for principle, description in design_principles.items():
    print(f"{principle:24} | {description}")


# ============================================================================
# 22. PROJECT PHASE ROLE EMPHASIS
# ============================================================================

phase_roles = {
    "Initiation": {
        "Project Sponsor",
        "Project Manager",
        "Product Owner",
        "Key Stakeholders",
    },
    "Planning": {
        "Project Manager",
        "Product Owner",
        "Business Analyst",
        "Technical Lead",
    },
    "Design": {
        "Business Analyst",
        "UX/UI Designer",
        "Technical Lead",
        "Security Specialist",
    },
    "Implementation": {
        "Technical Lead",
        "Software Developer",
        "QA Engineer",
    },
    "Release": {
        "QA Engineer",
        "DevOps Engineer",
        "Security Specialist",
        "Project Manager",
    },
    "Operations": {
        "DevOps Engineer",
        "Security Specialist",
        "Product Owner",
        "Project Manager",
    },
}

print("\nROLE EMPHASIS BY PROJECT PHASE")
print("-" * 78)

for phase, roles in phase_roles.items():
    print(f"{phase:14} | {', '.join(sorted(roles))}")


# ============================================================================
# 23. TEAM MATURITY MODEL
# ============================================================================

maturity_levels = {
    1: "Roles are informal and responsibilities are unclear.",
    2: "Basic responsibilities are identified.",
    3: "Responsibilities, decision rights, and dependencies are documented.",
    4: "Workload, risks, capabilities, and communication are actively managed.",
    5: "Team structure is continuously optimized using measurable delivery data.",
}

print("\nTEAM MATURITY MODEL")
print("-" * 78)

for level, description in maturity_levels.items():
    print(f"Level {level}: {description}")


# ============================================================================
# 24. SECURITY AND GOVERNANCE CONSIDERATIONS
# ============================================================================

security_principles = [
    "Grant team members only the access required for their responsibilities.",
    "Separate approval authority from implementation authority when appropriate.",
    "Record significant project and security decisions.",
    "Protect confidential stakeholder and project information.",
    "Include security responsibilities during design rather than only before release.",
    "Use auditable change and deployment processes for sensitive systems.",
]

print("\nSECURITY AND GOVERNANCE")
print("-" * 78)

for principle in security_principles:
    print(f"- {principle}")


# ============================================================================
# 25. PERFORMANCE CONSIDERATIONS FOR TEAM ANALYTICS
# ============================================================================

print(
    """
PERFORMANCE CONSIDERATIONS

The project-management domain can contain thousands of people, tasks,
dependencies, risks, and communication relationships.

Useful algorithmic approaches include:

- Dictionary/set lookups for role and skill matching: average O(1) lookup.
- Topological sorting for dependency ordering: O(V + E).
- Sorting risks by exposure: O(R log R).
- Aggregating workload: O(T).
- Graph-based communication analysis: commonly O(V + E).

For large systems, project data would usually be stored in a database instead
of being maintained entirely in memory. Indexes can accelerate searches by
member, role, task status, project, and dependency identifiers.
"""
)


# ============================================================================
# 26. PRODUCTION-ORIENTED VALIDATION
# ============================================================================

def validate_team(members: List[TeamMember]) -> List[str]:
    errors = []
    names = set()

    for member in members:
        if not member.name.strip():
            errors.append("Team member has an empty name.")

        if member.name in names:
            errors.append(f"Duplicate team member: {member.name}")

        names.add(member.name)

        if member.weekly_capacity < 0:
            errors.append(
                f"{member.name} has negative weekly capacity."
            )

        if not 0 <= member.availability <= 1:
            errors.append(
                f"{member.name} has invalid availability."
            )

        if not member.skills:
            errors.append(
                f"{member.name} has no declared skills."
            )

    return errors


print("\nTEAM VALIDATION")
print("-" * 78)

team_errors = validate_team(team)

if team_errors:
    for error in team_errors:
        print(f"ERROR: {error}")
else:
    print("Team data passed validation.")


# ============================================================================
# 27. COMPLETE REPORT
# ============================================================================

def generate_project_report(
    members: List[TeamMember],
    project_tasks: List[Task],
    project_risks: List[Risk],
) -> str:
    assigned_tasks = sum(task.owner is not None for task in project_tasks)
    total_tasks = len(project_tasks)

    risk_exposure = sum(risk.exposure for risk in project_risks)

    role_counts = defaultdict(int)
    for member in members:
        role_counts[member.role] += 1

    lines = [
        "",
        "=" * 78,
        "PROJECT TEAM ROLE REPORT",
        "=" * 78,
        f"Team size: {len(members)}",
        f"Distinct roles: {len(role_counts)}",
        f"Tasks: {total_tasks}",
        f"Assigned tasks: {assigned_tasks}",
        f"Unassigned tasks: {total_tasks - assigned_tasks}",
        f"Risk items: {len(project_risks)}",
        f"Total risk exposure: {risk_exposure:.2f}",
        "",
        "Role distribution:",
    ]

    for role, count in sorted(role_counts.items()):
        lines.append(f"  {role}: {count}")

    lines.extend(
        [
            "",
            "Task ownership:",
        ]
    )

    for task in project_tasks:
        lines.append(
            f"  {task.task_id}: {task.name} -> {task.owner or 'Unassigned'}"
        )

    return "\n".join(lines)


print(generate_project_report(team, tasks, risks))


# ============================================================================
# 28. FINAL EDUCATIONAL CHECK
# ============================================================================

print(
    """
KEY CONCEPT CHECK

A strong project team does not simply consist of people with job titles.
Effective project-team design connects:

people
  -> roles
  -> responsibilities
  -> authority
  -> skills
  -> tasks
  -> dependencies
  -> communication
  -> risks
  -> decisions
  -> measurable delivery outcomes

The appropriate team structure depends on project size, complexity,
organizational context, lifecycle, regulatory environment, technology,
risk profile, and delivery model.

A role model should therefore be treated as an operating mechanism rather
than merely an organizational chart.
"""
)

print("=" * 78)
print("END OF PROJECT TEAM ROLE STUDY")
print("=" * 78)
