"""
Creating a Clear Project Scope
================================

A self-contained study and demonstration program covering project scope from
beginner concepts through practical and advanced scope-management techniques.

The program demonstrates:
- Scope terminology and decomposition
- In-scope and out-of-scope definition
- SMART objectives and acceptance criteria
- Assumptions, constraints, dependencies, exclusions
- Requirements and traceability
- Work Breakdown Structure (WBS)
- Scope baseline
- Change requests and impact analysis
- Scope creep detection
- Validation and acceptance
- Risk and ambiguity analysis
- Effort and schedule implications
- A realistic project-scope case study
- Automated validation and reporting

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import re
import textwrap


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

class Priority(str, Enum):
    MUST = "Must"
    SHOULD = "Should"
    COULD = "Could"
    WONT = "Won't"


class ChangeStatus(str, Enum):
    PROPOSED = "Proposed"
    ANALYZING = "Analyzing"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IMPLEMENTED = "Implemented"


@dataclass
class Objective:
    """A measurable result the project intends to achieve."""

    identifier: str
    description: str
    metric: str
    target: str

    def is_complete(self) -> bool:
        return bool(
            self.identifier.strip()
            and self.description.strip()
            and self.metric.strip()
            and self.target.strip()
        )


@dataclass
class Requirement:
    """A testable statement of something the project must deliver."""

    identifier: str
    description: str
    priority: Priority
    acceptance_criteria: List[str]
    source: str
    in_scope: bool = True

    def is_testable(self) -> bool:
        return bool(self.acceptance_criteria) and all(
            criterion.strip() for criterion in self.acceptance_criteria
        )


@dataclass
class Deliverable:
    """A tangible or verifiable output produced by the project."""

    identifier: str
    name: str
    description: str
    acceptance_criteria: List[str]
    owner: str

    def is_well_defined(self) -> bool:
        return all(
            [
                bool(self.identifier.strip()),
                bool(self.name.strip()),
                bool(self.description.strip()),
                bool(self.acceptance_criteria),
                bool(self.owner.strip()),
            ]
        )


@dataclass
class Constraint:
    """A restriction within which the project must operate."""

    description: str
    category: str


@dataclass
class Assumption:
    """A condition treated as true for planning purposes."""

    description: str
    validation_method: str
    validated: bool = False


@dataclass
class Dependency:
    """An external or internal condition required by project work."""

    name: str
    description: str
    owner: str
    required_by: str


@dataclass
class ScopeItem:
    """One node in a Work Breakdown Structure."""

    identifier: str
    name: str
    description: str
    parent_id: Optional[str] = None
    estimated_hours: float = 0.0
    children: List["ScopeItem"] = field(default_factory=list)

    def add_child(self, child: "ScopeItem") -> None:
        child.parent_id = self.identifier
        self.children.append(child)

    def total_estimated_hours(self) -> float:
        return self.estimated_hours + sum(
            child.total_estimated_hours() for child in self.children
        )


@dataclass
class ChangeRequest:
    """A controlled proposal to modify the approved scope baseline."""

    identifier: str
    description: str
    reason: str
    requested_by: str
    estimated_hours: float
    estimated_cost: float
    schedule_days: int
    affected_deliverables: List[str]
    status: ChangeStatus = ChangeStatus.PROPOSED

    def impact_score(self) -> float:
        """A simple planning score; it is not a universal industry formula."""
        return (
            self.estimated_hours * 0.4
            + self.estimated_cost * 0.001
            + self.schedule_days * 2
            + len(self.affected_deliverables) * 5
        )


# ---------------------------------------------------------------------------
# 2. SMART OBJECTIVES
# ---------------------------------------------------------------------------

def explain_smart() -> None:
    print("\nSMART OBJECTIVES")
    print("-" * 72)
    smart = {
        "Specific": "The outcome is clearly defined.",
        "Measurable": "Success can be observed or quantified.",
        "Achievable": "The target is realistic within known conditions.",
        "Relevant": "The outcome supports the project's purpose.",
        "Time-bound": "A deadline or time window is specified.",
    }

    for key, meaning in smart.items():
        print(f"{key:12} : {meaning}")

    example = Objective(
        identifier="OBJ-01",
        description="Provide an online application for employee leave requests.",
        metric="Successful leave-request submissions",
        target="At least 98% of valid requests complete successfully during UAT",
    )
    print("\nExample:")
    print(example)
    print("Complete objective:", example.is_complete())


# ---------------------------------------------------------------------------
# 3. REQUIREMENTS
# ---------------------------------------------------------------------------

def validate_requirement(requirement: Requirement) -> List[str]:
    """Return concrete quality problems instead of simply returning False."""

    problems: List[str] = []

    if not requirement.identifier.strip():
        problems.append("Missing requirement identifier.")

    if not requirement.description.strip():
        problems.append("Missing requirement description.")

    vague_words = {
        "easy",
        "fast",
        "user-friendly",
        "modern",
        "appropriate",
        "etc.",
        "and so on",
        "as soon as possible",
    }

    description_lower = requirement.description.lower()

    for vague_word in vague_words:
        if vague_word in description_lower:
            problems.append(f"Potentially vague wording: '{vague_word}'.")

    if not requirement.acceptance_criteria:
        problems.append("No acceptance criteria supplied.")

    if not requirement.source.strip():
        problems.append("Requirement source is not identified.")

    return problems


def demonstrate_requirements() -> List[Requirement]:
    requirements = [
        Requirement(
            identifier="REQ-001",
            description="Users shall submit a leave request containing "
                        "employee ID, leave type, start date, and end date.",
            priority=Priority.MUST,
            acceptance_criteria=[
                "The system rejects a request without employee ID.",
                "The system rejects an end date before the start date.",
                "A valid request receives a unique request ID.",
            ],
            source="HR process owner",
        ),
        Requirement(
            identifier="REQ-002",
            description="The system shall display the current request status "
                        "to the employee.",
            priority=Priority.MUST,
            acceptance_criteria=[
                "Submitted requests display a status.",
                "Approved requests display Approved.",
                "Rejected requests display Rejected.",
            ],
            source="HR process owner",
        ),
        Requirement(
            identifier="REQ-003",
            description="The dashboard should be attractive and modern.",
            priority=Priority.SHOULD,
            acceptance_criteria=[],
            source="Stakeholder interview",
        ),
    ]

    print("\nREQUIREMENT QUALITY")
    print("-" * 72)

    for requirement in requirements:
        problems = validate_requirement(requirement)
        print(f"\n{requirement.identifier}: {requirement.description}")
        if problems:
            print("Problems:")
            for problem in problems:
                print("  -", problem)
        else:
            print("Status: sufficiently defined for planning.")

    return requirements


# ---------------------------------------------------------------------------
# 4. SCOPE STATEMENT
# ---------------------------------------------------------------------------

@dataclass
class ScopeStatement:
    project_name: str
    purpose: str
    objectives: List[Objective]
    deliverables: List[Deliverable]
    inclusions: List[str]
    exclusions: List[str]
    assumptions: List[Assumption]
    constraints: List[Constraint]
    dependencies: List[Dependency]

    def validate(self) -> List[str]:
        problems: List[str] = []

        if not self.project_name.strip():
            problems.append("Project name is missing.")

        if not self.purpose.strip():
            problems.append("Project purpose is missing.")

        if not self.objectives:
            problems.append("No measurable objectives defined.")

        if not self.deliverables:
            problems.append("No deliverables defined.")

        if not self.inclusions:
            problems.append("No explicit inclusions defined.")

        if not self.exclusions:
            problems.append("No explicit exclusions defined.")

        for deliverable in self.deliverables:
            if not deliverable.is_well_defined():
                problems.append(
                    f"Deliverable {deliverable.identifier} is incomplete."
                )

        return problems

    def print_scope(self) -> None:
        print("\nPROJECT SCOPE STATEMENT")
        print("=" * 72)
        print("Project:", self.project_name)
        print("Purpose:", self.purpose)

        print("\nObjectives:")
        for objective in self.objectives:
            print(f"  {objective.identifier}: {objective.description}")
            print(f"    Metric: {objective.metric}")
            print(f"    Target: {objective.target}")

        print("\nDeliverables:")
        for item in self.deliverables:
            print(f"  {item.identifier}: {item.name}")
            print(f"    {item.description}")
            print(f"    Owner: {item.owner}")

        print("\nIn Scope:")
        for item in self.inclusions:
            print("  +", item)

        print("\nOut of Scope:")
        for item in self.exclusions:
            print("  -", item)

        print("\nAssumptions:")
        for item in self.assumptions:
            print("  *", item.description)

        print("\nConstraints:")
        for item in self.constraints:
            print(f"  * [{item.category}] {item.description}")

        print("\nDependencies:")
        for item in self.dependencies:
            print(f"  * {item.name}: {item.description}")


# ---------------------------------------------------------------------------
# 5. WORK BREAKDOWN STRUCTURE
# ---------------------------------------------------------------------------

def print_wbs(item: ScopeItem, level: int = 0) -> None:
    indentation = "  " * level
    print(
        f"{indentation}{item.identifier} {item.name}"
        f" [{item.estimated_hours:.1f}h]"
    )

    for child in item.children:
        print_wbs(child, level + 1)


def collect_leaf_items(item: ScopeItem) -> List[ScopeItem]:
    if not item.children:
        return [item]

    result: List[ScopeItem] = []

    for child in item.children:
        result.extend(collect_leaf_items(child))

    return result


def demonstrate_wbs() -> ScopeItem:
    root = ScopeItem(
        identifier="1.0",
        name="Employee Leave Management System",
        description="Complete project scope",
    )

    discovery = ScopeItem(
        identifier="1.1",
        name="Requirements and Discovery",
        description="Understand business requirements",
    )
    discovery.add_child(
        ScopeItem(
            identifier="1.1.1",
            name="Stakeholder interviews",
            description="Interview HR and employee representatives",
            estimated_hours=12,
        )
    )
    discovery.add_child(
        ScopeItem(
            identifier="1.1.2",
            name="Requirements specification",
            description="Document functional and non-functional requirements",
            estimated_hours=16,
        )
    )

    design = ScopeItem(
        identifier="1.2",
        name="Solution Design",
        description="Design application architecture and interface",
    )
    design.add_child(
        ScopeItem(
            identifier="1.2.1",
            name="Architecture design",
            description="Define application components and interfaces",
            estimated_hours=14,
        )
    )
    design.add_child(
        ScopeItem(
            identifier="1.2.2",
            name="User interface design",
            description="Design employee and administrator screens",
            estimated_hours=18,
        )
    )

    implementation = ScopeItem(
        identifier="1.3",
        name="Implementation",
        description="Build the approved solution",
    )
    implementation.add_child(
        ScopeItem(
            identifier="1.3.1",
            name="Request management",
            description="Implement leave request workflow",
            estimated_hours=28,
        )
    )
    implementation.add_child(
        ScopeItem(
            identifier="1.3.2",
            name="Approval workflow",
            description="Implement manager approval process",
            estimated_hours=24,
        )
    )
    implementation.add_child(
        ScopeItem(
            identifier="1.3.3",
            name="Reporting",
            description="Implement standard leave reports",
            estimated_hours=20,
        )
    )

    testing = ScopeItem(
        identifier="1.4",
        name="Testing and Acceptance",
        description="Verify and validate the system",
    )
    testing.add_child(
        ScopeItem(
            identifier="1.4.1",
            name="Functional testing",
            description="Test functional requirements",
            estimated_hours=20,
        )
    )
    testing.add_child(
        ScopeItem(
            identifier="1.4.2",
            name="User acceptance testing",
            description="Conduct business acceptance testing",
            estimated_hours=16,
        )
    )

    deployment = ScopeItem(
        identifier="1.5",
        name="Deployment",
        description="Release the approved system",
    )
    deployment.add_child(
        ScopeItem(
            identifier="1.5.1",
            name="Production deployment",
            description="Deploy approved release",
            estimated_hours=10,
        )
    )

    for section in [
        discovery,
        design,
        implementation,
        testing,
        deployment,
    ]:
        root.add_child(section)

    print("\nWORK BREAKDOWN STRUCTURE")
    print("-" * 72)
    print_wbs(root)

    leaves = collect_leaf_items(root)
    print(f"\nWork packages: {len(leaves)}")
    print(f"Estimated effort: {root.total_estimated_hours():.1f} hours")

    return root


# ---------------------------------------------------------------------------
# 6. SCOPE BASELINE
# ---------------------------------------------------------------------------

@dataclass
class ScopeBaseline:
    """Approved reference point used to control changes."""

    version: str
    approved_date: date
    scope_statement: ScopeStatement
    wbs_root: ScopeItem

    def total_hours(self) -> float:
        return self.wbs_root.total_estimated_hours()


def create_baseline(scope: ScopeStatement, wbs: ScopeItem) -> ScopeBaseline:
    return ScopeBaseline(
        version="1.0",
        approved_date=date.today(),
        scope_statement=scope,
        wbs_root=wbs,
    )


# ---------------------------------------------------------------------------
# 7. SCOPE CREEP AND CHANGE CONTROL
# ---------------------------------------------------------------------------

def normalize_text(value: str) -> str:
    """Normalize text for simple comparison."""

    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def detect_scope_creep(
    request_description: str,
    approved_scope: Sequence[str],
) -> Tuple[bool, List[str]]:
    """
    Detect likely scope creep using keyword overlap.

    This is a planning aid, not a replacement for human requirements analysis.
    """

    request_words = set(normalize_text(request_description).split())

    if not request_words:
        return False, []

    matches: List[str] = []

    for item in approved_scope:
        scope_words = set(normalize_text(item).split())
        overlap = request_words & scope_words

        if len(overlap) >= 2:
            matches.append(item)

    # If no meaningful relationship exists, the request should be investigated.
    likely_creep = len(matches) == 0

    return likely_creep, matches


def analyze_change_request(
    request: ChangeRequest,
    baseline_hours: float,
    hourly_rate: float,
) -> Dict[str, object]:
    additional_cost = request.estimated_hours * hourly_rate + request.estimated_cost
    percentage_increase = (
        request.estimated_hours / baseline_hours * 100
        if baseline_hours > 0
        else float("inf")
    )

    return {
        "change_id": request.identifier,
        "additional_hours": request.estimated_hours,
        "additional_cost": additional_cost,
        "schedule_days": request.schedule_days,
        "baseline_hours": baseline_hours,
        "percentage_effort_increase": percentage_increase,
        "impact_score": request.impact_score(),
        "affected_deliverables": request.affected_deliverables,
    }


def demonstrate_change_control(baseline: ScopeBaseline) -> None:
    change = ChangeRequest(
        identifier="CR-001",
        description="Add mobile push notifications for leave approvals.",
        reason="Stakeholders requested real-time approval alerts.",
        requested_by="HR Director",
        estimated_hours=24,
        estimated_cost=500,
        schedule_days=3,
        affected_deliverables=["DEL-003"],
    )

    analysis = analyze_change_request(
        change,
        baseline.total_hours(),
        hourly_rate=45,
    )

    print("\nCHANGE REQUEST ANALYSIS")
    print("-" * 72)

    for key, value in analysis.items():
        print(f"{key}: {value}")

    print(
        "\nDecision principle: the change should be evaluated against "
        "benefit, cost, schedule, risk, dependencies, and authorization."
    )


# ---------------------------------------------------------------------------
# 8. VALIDATION AND ACCEPTANCE
# ---------------------------------------------------------------------------

def validate_deliverable(
    deliverable: Deliverable,
    observed_results: Dict[str, bool],
) -> Tuple[bool, List[str]]:
    failures: List[str] = []

    for criterion in deliverable.acceptance_criteria:
        if not observed_results.get(criterion, False):
            failures.append(criterion)

    return not failures, failures


def demonstrate_acceptance() -> None:
    deliverable = Deliverable(
        identifier="DEL-003",
        name="Approval Workflow",
        description="Manager approval and rejection workflow.",
        acceptance_criteria=[
            "Manager can approve a pending request.",
            "Manager can reject a pending request.",
            "Employee can see the resulting status.",
        ],
        owner="Application Team",
    )

    observed = {
        "Manager can approve a pending request.": True,
        "Manager can reject a pending request.": True,
        "Employee can see the resulting status.": False,
    }

    accepted, failures = validate_deliverable(deliverable, observed)

    print("\nDELIVERABLE ACCEPTANCE")
    print("-" * 72)
    print("Accepted:", accepted)

    if failures:
        print("Failed criteria:")
        for failure in failures:
            print("  -", failure)


# ---------------------------------------------------------------------------
# 9. AMBIGUITY ANALYSIS
# ---------------------------------------------------------------------------

VAGUE_TERMS = {
    "fast",
    "easy",
    "simple",
    "modern",
    "user-friendly",
    "robust",
    "scalable",
    "secure",
    "efficient",
    "etc",
    "as soon as possible",
}


def find_ambiguity(text: str) -> List[str]:
    normalized = text.lower()
    return sorted(
        term
        for term in VAGUE_TERMS
        if re.search(r"\b" + re.escape(term) + r"\b", normalized)
    )


def demonstrate_ambiguity() -> None:
    examples = [
        "The system should be fast.",
        "The application shall return search results within 2 seconds "
        "for 95% of requests under 500 concurrent users.",
    ]

    print("\nAMBIGUITY ANALYSIS")
    print("-" * 72)

    for example in examples:
        vague = find_ambiguity(example)
        print("Statement:", example)
        print("Potentially vague terms:", vague or "None")


# ---------------------------------------------------------------------------
# 10. REQUIREMENT TRACEABILITY
# ---------------------------------------------------------------------------

@dataclass
class TraceabilityRecord:
    requirement_id: str
    deliverable_id: str
    test_id: str
    accepted: bool


def build_traceability_matrix(
    requirements: Sequence[Requirement],
    deliverables: Sequence[Deliverable],
) -> List[TraceabilityRecord]:
    records: List[TraceabilityRecord] = []

    for index, requirement in enumerate(requirements, start=1):
        if not requirement.in_scope:
            continue

        deliverable_index = min(index, len(deliverables))
        deliverable = deliverables[deliverable_index - 1]

        records.append(
            TraceabilityRecord(
                requirement_id=requirement.identifier,
                deliverable_id=deliverable.identifier,
                test_id=f"TEST-{index:03}",
                accepted=False,
            )
        )

    return records


def print_traceability(records: Sequence[TraceabilityRecord]) -> None:
    print("\nREQUIREMENT TRACEABILITY MATRIX")
    print("-" * 72)

    for record in records:
        print(
            f"{record.requirement_id:10} -> "
            f"{record.deliverable_id:10} -> "
            f"{record.test_id:10} -> "
            f"Accepted={record.accepted}"
        )


# ---------------------------------------------------------------------------
# 11. COMPLETE PROJECT CASE STUDY
# ---------------------------------------------------------------------------

def build_project_scope() -> ScopeStatement:
    objectives = [
        Objective(
            identifier="OBJ-01",
            description="Digitize employee leave submission and approval.",
            metric="Valid leave requests processed digitally",
            target="100% of pilot requests",
        ),
        Objective(
            identifier="OBJ-02",
            description="Provide traceable request status.",
            metric="Requests with visible status",
            target="100% of submitted pilot requests",
        ),
    ]

    deliverables = [
        Deliverable(
            identifier="DEL-001",
            name="Requirements Specification",
            description="Approved functional and non-functional requirements.",
            acceptance_criteria=[
                "Business owner approves the requirements.",
                "All mandatory requirements have acceptance criteria.",
            ],
            owner="Business Analyst",
        ),
        Deliverable(
            identifier="DEL-002",
            name="Leave Request Module",
            description="Employee leave request functionality.",
            acceptance_criteria=[
                "Valid requests can be submitted.",
                "Invalid dates are rejected.",
            ],
            owner="Application Team",
        ),
        Deliverable(
            identifier="DEL-003",
            name="Approval Workflow",
            description="Manager approval and rejection functionality.",
            acceptance_criteria=[
                "Managers can approve requests.",
                "Managers can reject requests.",
                "Employees can see request status.",
            ],
            owner="Application Team",
        ),
        Deliverable(
            identifier="DEL-004",
            name="Standard Reports",
            description="Approved reports for leave activity.",
            acceptance_criteria=[
                "Monthly leave report can be generated.",
                "Report filters include department and date.",
            ],
            owner="Reporting Team",
        ),
    ]

    assumptions = [
        Assumption(
            description="The HR department will provide current leave rules.",
            validation_method="Review approved HR policy document.",
        ),
        Assumption(
            description="Employees have authenticated organizational accounts.",
            validation_method="Confirm identity-provider integration.",
        ),
    ]

    constraints = [
        Constraint(
            description="Pilot implementation must remain within the approved budget.",
            category="Budget",
        ),
        Constraint(
            description="Only approved organizational identity systems may be used.",
            category="Technology",
        ),
        Constraint(
            description="Pilot must be available within 60 calendar days.",
            category="Schedule",
        ),
    ]

    dependencies = [
        Dependency(
            name="Identity Provider",
            description="Authentication must be available before user acceptance testing.",
            owner="IT Infrastructure",
            required_by="User acceptance testing",
        ),
        Dependency(
            name="HR Policy",
            description="Current leave rules are required for validation.",
            owner="HR",
            required_by="Requirements approval",
        ),
    ]

    return ScopeStatement(
        project_name="Employee Leave Management System",
        purpose=(
            "Create a controlled digital process for submitting, approving, "
            "tracking, and reporting employee leave requests."
        ),
        objectives=objectives,
        deliverables=deliverables,
        inclusions=[
            "Employee leave request submission",
            "Manager approval and rejection",
            "Request status tracking",
            "Standard leave reports",
            "Authentication through the approved identity system",
            "User acceptance testing",
            "Production deployment of the approved pilot",
        ],
        exclusions=[
            "Payroll calculation",
            "Recruitment functionality",
            "Performance management",
            "Custom mobile application",
            "Internationalization beyond the pilot language",
            "Unapproved third-party notification platforms",
        ],
        assumptions=assumptions,
        constraints=constraints,
        dependencies=dependencies,
    )


# ---------------------------------------------------------------------------
# 12. COMPARISON OF RELATED CONCEPTS
# ---------------------------------------------------------------------------

def print_comparisons() -> None:
    comparisons = [
        (
            "Scope",
            "What the project will and will not deliver.",
            "Defines boundaries.",
        ),
        (
            "Requirement",
            "A condition or capability that must be satisfied.",
            "Defines what is needed.",
        ),
        (
            "Deliverable",
            "A verifiable output produced by project work.",
            "Defines what is produced.",
        ),
        (
            "WBS",
            "Hierarchical decomposition of project work.",
            "Defines how scope is decomposed.",
        ),
        (
            "Acceptance criterion",
            "Condition used to determine whether an output is acceptable.",
            "Defines how completion is verified.",
        ),
        (
            "Constraint",
            "A limitation on project execution.",
            "Defines boundaries on planning.",
        ),
        (
            "Assumption",
            "A condition considered true for planning.",
            "Creates planning uncertainty if false.",
        ),
        (
            "Change request",
            "A controlled proposal to modify approved scope.",
            "Prevents uncontrolled scope expansion.",
        ),
    ]

    print("\nIMPORTANT DISTINCTIONS")
    print("-" * 72)

    for concept, definition, purpose in comparisons:
        print(f"{concept:22} | {definition}")
        print(f"{'':22} | {purpose}")


# ---------------------------------------------------------------------------
# 13. EDGE CASES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\nEDGE CASES")
    print("-" * 72)

    empty_scope = ScopeStatement(
        project_name="",
        purpose="",
        objectives=[],
        deliverables=[],
        inclusions=[],
        exclusions=[],
        assumptions=[],
        constraints=[],
        dependencies=[],
    )

    problems = empty_scope.validate()

    print("Empty scope statement validation:")
    for problem in problems:
        print("  -", problem)

    zero_baseline_request = ChangeRequest(
        identifier="CR-ZERO",
        description="New feature",
        reason="Business request",
        requested_by="Stakeholder",
        estimated_hours=10,
        estimated_cost=100,
        schedule_days=1,
        affected_deliverables=[],
    )

    analysis = analyze_change_request(
        zero_baseline_request,
        baseline_hours=0,
        hourly_rate=50,
    )

    print("\nZero-hour baseline percentage:")
    print(analysis["percentage_effort_increase"])

    empty_request = ChangeRequest(
        identifier="CR-EMPTY",
        description="",
        reason="",
        requested_by="",
        estimated_hours=0,
        estimated_cost=0,
        schedule_days=0,
        affected_deliverables=[],
    )

    print("Empty change impact score:", empty_request.impact_score())


# ---------------------------------------------------------------------------
# 14. PERFORMANCE AND PLANNING METRICS
# ---------------------------------------------------------------------------

def calculate_working_days(
    start: date,
    calendar_days: int,
) -> int:
    """
    Count weekdays in a date interval.

    This deliberately excludes holidays because holiday calendars are
    organization-specific and should be supplied explicitly in production.
    """

    if calendar_days <= 0:
        return 0

    working_days = 0

    for offset in range(calendar_days):
        current = start + timedelta(days=offset)

        if current.weekday() < 5:
            working_days += 1

    return working_days


def estimate_calendar_duration(
    effort_hours: float,
    team_size: int,
    productive_hours_per_day: float = 6.0,
) -> float:
    """
    A simple capacity estimate.

    Actual project schedules also depend on sequencing, dependencies,
    resource availability, review cycles, risk, and rework.
    """

    if team_size <= 0 or productive_hours_per_day <= 0:
        raise ValueError("Team size and productive hours must be positive.")

    return effort_hours / (team_size * productive_hours_per_day)


def demonstrate_planning_metrics(baseline: ScopeBaseline) -> None:
    effort = baseline.total_hours()

    print("\nPLANNING METRICS")
    print("-" * 72)
    print(f"Total work-package effort: {effort:.1f} hours")

    for team_size in [1, 2, 4]:
        duration = estimate_calendar_duration(effort, team_size)
        print(
            f"Nominal capacity duration with {team_size} "
            f"person(s): {duration:.2f} working days"
        )

    print(
        "Weekdays in a 60-calendar-day pilot window:",
        calculate_working_days(date.today(), 60),
    )


# ---------------------------------------------------------------------------
# 15. MAIN STUDY
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("CREATING A CLEAR PROJECT SCOPE")
    print("=" * 72)

    print(
        textwrap.dedent(
            """
            Project scope establishes the boundary of project work. A clear
            scope answers questions such as:

            - Why does the project exist?
            - What outcomes are required?
            - What will be delivered?
            - What work is included?
            - What work is explicitly excluded?
            - What assumptions and constraints affect delivery?
            - How will completion be verified?
            - How will proposed changes be evaluated and authorized?

            A useful scope is specific enough to support planning and flexible
            enough to permit controlled change.
            """
        ).strip()
    )

    explain_smart()

    requirements = demonstrate_requirements()

    scope = build_project_scope()
    scope.print_scope()

    problems = scope.validate()
    print("\nSCOPE QUALITY CHECK")
    print("-" * 72)

    if problems:
        for problem in problems:
            print("  -", problem)
    else:
        print("No structural scope problems detected.")

    wbs = demonstrate_wbs()

    baseline = create_baseline(scope, wbs)

    print("\nSCOPE BASELINE")
    print("-" * 72)
    print("Version:", baseline.version)
    print("Approved:", baseline.approved_date)
    print(f"Baseline effort: {baseline.total_hours():.1f} hours")

    demonstrate_change_control(baseline)
    demonstrate_acceptance()
    demonstrate_ambiguity()

    traceability = build_traceability_matrix(
        requirements=[r for r in requirements if r.in_scope],
        deliverables=scope.deliverables,
    )
    print_traceability(traceability)

    print_comparisons()
    demonstrate_edge_cases()
    demonstrate_planning_metrics(baseline)

    approved_scope = scope.inclusions

    print("\nSCOPE CREEP CHECK")
    print("-" * 72)

    proposed_work = [
        "Add payroll calculation and tax deductions.",
        "Add manager approval and rejection.",
        "Add employee leave request submission.",
    ]

    for request in proposed_work:
        creep, matches = detect_scope_creep(request, approved_scope)

        print(f"\nRequest: {request}")
        print("Likely new-scope item:", creep)
        print("Related approved scope:", matches or "No strong match")

    print("\nFINAL QUALITY PRINCIPLES")
    print("-" * 72)

    principles = [
        "Define the business purpose before defining features.",
        "State measurable objectives instead of vague aspirations.",
        "Convert stakeholder needs into testable requirements.",
        "Define both inclusions and exclusions.",
        "Make assumptions visible and assign validation methods.",
        "Document constraints and dependencies.",
        "Decompose approved scope into a WBS.",
        "Use acceptance criteria to make completion observable.",
        "Establish a scope baseline after appropriate approval.",
        "Treat new work as a change until its relationship to approved scope is clear.",
        "Assess change impact on effort, cost, schedule, quality, risk, and dependencies.",
        "Keep requirements traceable to deliverables and verification.",
        "Do not use vague language where measurable criteria are possible.",
        "Do not confuse stakeholder enthusiasm with authorization to expand scope.",
        "Keep scope control transparent and evidence-based.",
    ]

    for number, principle in enumerate(principles, start=1):
        print(f"{number:02}. {principle}")

    print("\nStudy file execution completed.")


if __name__ == "__main__":
    main()
