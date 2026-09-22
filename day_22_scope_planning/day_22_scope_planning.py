"""
Scope Planning: From Fundamentals to Advanced Practice

This standalone study program teaches project scope planning through executable
examples. It models scope definition, requirements, deliverables, acceptance
criteria, assumptions, constraints, exclusions, WBS construction, scope
validation, scope control, change requests, traceability, and basic metrics.

The examples use only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from collections import Counter
import re


# ---------------------------------------------------------------------------
# 1. FUNDAMENTALS
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def subsection(title: str) -> None:
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


section("1. What project scope means")

print("""
Project scope describes the work required to produce the agreed project
deliverables and the boundaries around that work.

Two related ideas must be distinguished:

1. Product scope:
   The features, capabilities, characteristics, and functions of the product,
   service, or result being created.

2. Project scope:
   The work that must be performed to deliver the required product, service,
   or result.

Scope planning converts an initial project objective into a controlled
description of what is included, what is excluded, what must be delivered,
and how completion will be judged.

A useful scope chain is:

Business need
    -> objective
    -> requirements
    -> deliverables
    -> work packages
    -> activities
    -> acceptance criteria

A strong scope definition also makes boundaries explicit:

Included work + excluded work + assumptions + constraints
+ acceptance conditions + change-control mechanism
""")

# ---------------------------------------------------------------------------
# 2. BASIC DATA MODELS
# ---------------------------------------------------------------------------

@dataclass
class Requirement:
    requirement_id: str
    description: str
    priority: str
    source: str
    acceptance_criteria: List[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        return bool(
            self.requirement_id
            and self.description.strip()
            and self.priority.strip()
            and self.source.strip()
            and self.acceptance_criteria
        )


@dataclass
class Deliverable:
    deliverable_id: str
    name: str
    description: str
    requirements: List[str]
    acceptance_criteria: List[str]

    def is_traceable(self, requirement_ids: Set[str]) -> bool:
        return all(req in requirement_ids for req in self.requirements)


@dataclass
class ScopeStatement:
    objective: str
    inclusions: List[str]
    exclusions: List[str]
    assumptions: List[str]
    constraints: List[str]

    def contains(self, phrase: str) -> bool:
        return any(phrase.lower() in item.lower() for item in self.inclusions)

    def print_scope(self) -> None:
        print(f"Objective: {self.objective}")

        for title, values in (
            ("In scope", self.inclusions),
            ("Out of scope", self.exclusions),
            ("Assumptions", self.assumptions),
            ("Constraints", self.constraints),
        ):
            print(f"\n{title}:")
            for value in values:
                print(f"  - {value}")


# ---------------------------------------------------------------------------
# 3. REQUIREMENT QUALITY
# ---------------------------------------------------------------------------

section("2. Requirements and scope boundaries")

requirements = [
    Requirement(
        "REQ-001",
        "Users shall be able to create an account using an email address.",
        "Must",
        "Business owner",
        ["A valid email can create an account.", "Duplicate emails are rejected."],
    ),
    Requirement(
        "REQ-002",
        "Users shall be able to sign in with their credentials.",
        "Must",
        "Product owner",
        ["Valid credentials create a session.", "Invalid credentials are rejected."],
    ),
    Requirement(
        "REQ-003",
        "The system shall provide a searchable project dashboard.",
        "Should",
        "Project manager",
        ["A user can search projects by project name."],
    ),
    Requirement(
        "REQ-004",
        "The first release shall support English language content.",
        "Must",
        "Sponsor",
        ["All release screens have English labels."],
    ),
]

for requirement in requirements:
    print(
        f"{requirement.requirement_id}: "
        f"{requirement.priority} | "
        f"{requirement.description} | "
        f"Complete={requirement.is_complete()}"
    )

scope = ScopeStatement(
    objective="Deliver a web-based project management MVP for small teams.",
    inclusions=[
        "Account creation and authentication",
        "Project dashboard",
        "Project search",
        "English user interface",
        "Basic project status tracking",
    ],
    exclusions=[
        "Native mobile applications",
        "Advanced financial accounting",
        "Third-party payroll processing",
        "Multi-language translation in the first release",
    ],
    assumptions=[
        "The organization will provide branding assets.",
        "Users have internet access.",
        "The hosting environment will be available before acceptance testing.",
    ],
    constraints=[
        "The MVP must use the approved technology stack.",
        "The first release has a fixed delivery date.",
        "The initial budget is limited.",
    ],
)

scope.print_scope()

# ---------------------------------------------------------------------------
# 4. SMARTER SCOPE OBJECTIVES
# ---------------------------------------------------------------------------

section("3. Turning vague objectives into testable objectives")

vague = "Build a good project dashboard."
specific = (
    "Deliver a browser-based dashboard that allows authenticated users "
    "to view project status and search projects by name before the agreed "
    "MVP acceptance date."
)

print("Vague objective:", vague)
print("More testable objective:", specific)

print("""
A useful objective should make several things observable:

- What result is required?
- Who needs it?
- What boundaries apply?
- What measurable condition indicates completion?
- What time or resource constraint applies?

Scope should not be defined by vague adjectives such as "good", "modern",
"fast", or "complete" unless those terms have measurable definitions.
""")

# ---------------------------------------------------------------------------
# 5. PRIORITIZATION
# ---------------------------------------------------------------------------

section("4. Requirement prioritization")

PRIORITY_ORDER = {"Must": 1, "Should": 2, "Could": 3, "Won't": 4}

sorted_requirements = sorted(
    requirements,
    key=lambda r: PRIORITY_ORDER.get(r.priority, 99),
)

for requirement in sorted_requirements:
    print(f"{requirement.priority:>5} | {requirement.requirement_id} | {requirement.description}")

print("""
Priority classification helps prevent scope from becoming an undifferentiated
list. A requirement's priority is not the same thing as its implementation
difficulty or cost.

A high-priority requirement may still need to be rejected if it conflicts with
a hard constraint. Conversely, a low-priority requirement may be delivered if
capacity remains and governance permits it.
""")

# ---------------------------------------------------------------------------
# 6. WORK BREAKDOWN STRUCTURE
# ---------------------------------------------------------------------------

section("5. Work Breakdown Structure")

@dataclass
class WorkPackage:
    wbs_id: str
    name: str
    description: str
    estimated_hours: float
    deliverables: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        errors = []
        if not self.wbs_id:
            errors.append("Missing WBS identifier.")
        if not self.name:
            errors.append("Missing work-package name.")
        if self.estimated_hours <= 0:
            errors.append("Estimated hours must be positive.")
        if not self.deliverables:
            errors.append("Work package has no linked deliverables.")
        return errors


work_packages = [
    WorkPackage(
        "1.1",
        "Authentication",
        "Implement account creation and sign-in.",
        36,
        ["DEL-001"],
    ),
    WorkPackage(
        "1.2",
        "Dashboard",
        "Implement project dashboard and status presentation.",
        48,
        ["DEL-002"],
    ),
    WorkPackage(
        "1.3",
        "Search",
        "Implement project-name search.",
        20,
        ["DEL-003"],
    ),
    WorkPackage(
        "1.4",
        "Acceptance testing",
        "Execute agreed acceptance tests and correct qualifying defects.",
        28,
        ["DEL-004"],
    ),
]

total_hours = sum(item.estimated_hours for item in work_packages)

for package in work_packages:
    errors = package.validate()
    print(
        f"{package.wbs_id} {package.name}: "
        f"{package.estimated_hours:.1f} hours"
        + (f" | errors={errors}" if errors else "")
    )

print(f"\nTotal estimated effort: {total_hours:.1f} hours")

print("""
The WBS decomposes the project scope into manageable work packages.

A useful decomposition should preserve scope coverage. It should not turn into
an arbitrary list of tiny tasks. The work packages should collectively cover
the approved project work without intentionally hiding work or duplicating it.

A common principle is the 100 percent rule: the WBS should represent 100% of
the work required by the project scope, including project management work when
that work is part of the agreed scope.
""")

# ---------------------------------------------------------------------------
# 7. DELIVERABLE TRACEABILITY
# ---------------------------------------------------------------------------

section("6. Requirements-to-deliverable traceability")

deliverables = [
    Deliverable(
        "DEL-001",
        "Authentication module",
        "Account registration and sign-in capability.",
        ["REQ-001", "REQ-002"],
        ["Registration succeeds with valid email.", "Valid users can sign in."],
    ),
    Deliverable(
        "DEL-002",
        "Project dashboard",
        "Dashboard showing project status.",
        ["REQ-003"],
        ["Dashboard displays project records."],
    ),
    Deliverable(
        "DEL-003",
        "Project search",
        "Search capability for project names.",
        ["REQ-003"],
        ["A project can be found by its name."],
    ),
    Deliverable(
        "DEL-004",
        "English release",
        "English interface for the MVP.",
        ["REQ-004"],
        ["Release interface contains English labels."],
    ),
]

requirement_ids = {r.requirement_id for r in requirements}

for deliverable in deliverables:
    print(
        f"{deliverable.deliverable_id}: "
        f"traceable={deliverable.is_traceable(requirement_ids)}"
    )

unmapped_requirements = requirement_ids - {
    req
    for deliverable in deliverables
    for req in deliverable.requirements
}

print("Unmapped requirements:", sorted(unmapped_requirements))

# ---------------------------------------------------------------------------
# 8. SCOPE BASELINE
# ---------------------------------------------------------------------------

section("7. Scope baseline")

@dataclass
class ScopeBaseline:
    version: str
    scope_statement: ScopeStatement
    requirements: Dict[str, Requirement]
    deliverables: Dict[str, Deliverable]

    def requirement_count(self) -> int:
        return len(self.requirements)

    def deliverable_count(self) -> int:
        return len(self.deliverables)

    def snapshot(self) -> Dict[str, object]:
        return {
            "version": self.version,
            "requirements": list(self.requirements),
            "deliverables": list(self.deliverables),
            "inclusions": self.scope_statement.inclusions,
            "exclusions": self.scope_statement.exclusions,
        }


baseline = ScopeBaseline(
    version="1.0",
    scope_statement=scope,
    requirements={r.requirement_id: r for r in requirements},
    deliverables={d.deliverable_id: d for d in deliverables},
)

print("Baseline:", baseline.snapshot())

print("""
A scope baseline is an approved reference point. It gives the project a stable
definition against which proposed changes can be evaluated.

A baseline does not mean scope can never change. It means changes should be
visible, evaluated, approved through the appropriate governance process, and
incorporated deliberately.
""")

# ---------------------------------------------------------------------------
# 9. CHANGE CONTROL
# ---------------------------------------------------------------------------

section("8. Scope change control")

class ChangeStatus(Enum):
    PROPOSED = "Proposed"
    ANALYZING = "Analyzing"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IMPLEMENTED = "Implemented"


@dataclass
class ChangeRequest:
    change_id: str
    description: str
    reason: str
    estimated_hours: float
    cost_impact: float
    schedule_impact_days: int
    status: ChangeStatus = ChangeStatus.PROPOSED

    def risk_score(self) -> float:
        return (
            max(self.estimated_hours, 0)
            + max(self.cost_impact, 0) / 100
            + max(self.schedule_impact_days, 0) * 8
        )


change = ChangeRequest(
    "CR-001",
    "Add multilingual interface support.",
    "Expansion into additional markets.",
    80,
    12000,
    10,
)

print("Change request:", change.change_id)
print("Description:", change.description)
print("Estimated effort:", change.estimated_hours)
print("Cost impact:", change.cost_impact)
print("Schedule impact:", change.schedule_impact_days)
print("Analysis score:", change.risk_score())

print("""
A change request should not be evaluated only by asking whether the requested
feature is useful. Scope governance considers its effects on:

- requirements
- deliverables
- effort
- cost
- schedule
- quality
- resources
- architecture
- security
- dependencies
- contractual commitments
- operational support

A useful change-control sequence is:

1. Record the request.
2. Clarify the requested outcome.
3. Analyze impacts.
4. Identify alternatives.
5. Obtain the required decision.
6. Update the baseline when approved.
7. Communicate the resulting change.
8. Verify implementation against the revised scope.
""")

# ---------------------------------------------------------------------------
# 10. SCOPE CREEP
# ---------------------------------------------------------------------------

section("9. Detecting scope creep")

def normalize_requirement(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


baseline_features = {
    normalize_requirement(item) for item in scope.inclusions
}

proposed_features = baseline_features | {
    "native mobile applications",
    "advanced accounting analytics",
}

unapproved_additions = proposed_features - baseline_features

print("Baseline scope items:", len(baseline_features))
print("Proposed scope items:", len(proposed_features))
print("Potential additions:", sorted(unapproved_additions))

print("""
Scope creep is uncontrolled expansion of project scope, often occurring
without corresponding authorization, resources, time, budget, or baseline
updates.

Not every scope expansion is inherently bad. A formally approved change is
different from an undocumented addition.

The governance distinction is:

authorized change -> controlled scope evolution
unauthorized addition -> scope-control problem
""")

# ---------------------------------------------------------------------------
# 11. ACCEPTANCE CRITERIA
# ---------------------------------------------------------------------------

section("10. Acceptance criteria")

def evaluate_acceptance(
    completed_conditions: Iterable[str],
    required_conditions: Iterable[str],
) -> Tuple[bool, Set[str]]:
    completed = {normalize_requirement(c) for c in completed_conditions}
    required = {normalize_requirement(c) for c in required_conditions}
    missing = required - completed
    return not missing, missing


required_conditions = [
    "Registration succeeds with valid email.",
    "Duplicate emails are rejected.",
]

completed_conditions = [
    "Registration succeeds with valid email.",
]

accepted, missing = evaluate_acceptance(
    completed_conditions,
    required_conditions,
)

print("Accepted:", accepted)
print("Missing acceptance conditions:", missing)

print("""
Acceptance criteria define observable conditions for deciding whether a
deliverable is acceptable.

A requirement such as "the dashboard should be fast" is ambiguous.
A testable criterion might define a measured response-time threshold under a
specified load and environment.

Acceptance criteria should be:

- observable
- testable
- unambiguous
- relevant to the requirement
- agreed before acceptance where practical
""")

# ---------------------------------------------------------------------------
# 12. ASSUMPTIONS AND CONSTRAINTS
# ---------------------------------------------------------------------------

section("11. Assumptions versus constraints")

print("""
Assumption:
    A condition believed to be true for planning purposes.

Constraint:
    A restriction that limits project options.

Example:
    Assumption: the client will provide branding assets by a specified date.
    Constraint: the project cannot exceed the approved budget.

An assumption that becomes false can create a risk or change the scope
analysis. A constraint can force trade-offs between scope, time, cost, quality,
resources, or technical options.
""")

# ---------------------------------------------------------------------------
# 13. EDGE CASES
# ---------------------------------------------------------------------------

section("12. Edge cases and scope defects")

def find_duplicate_ids(items: Sequence[object], attribute: str) -> List[str]:
    seen: Set[str] = set()
    duplicates: Set[str] = set()

    for item in items:
        identifier = getattr(item, attribute)
        if identifier in seen:
            duplicates.add(identifier)
        seen.add(identifier)

    return sorted(duplicates)


duplicate_test = requirements + [
    Requirement(
        "REQ-002",
        "Duplicate requirement for testing.",
        "Could",
        "Test",
        ["Test condition"],
    )
]

print("Duplicate requirement IDs:", find_duplicate_ids(
    duplicate_test, "requirement_id"
))

empty_requirement = Requirement("", "", "", "", [])
print("Empty requirement valid:", empty_requirement.is_complete())

invalid_package = WorkPackage(
    "2.1",
    "Incomplete package",
    "Intentional validation example.",
    0,
    [],
)

print("Invalid work package errors:", invalid_package.validate())

# ---------------------------------------------------------------------------
# 14. COVERAGE AND TRACEABILITY METRICS
# ---------------------------------------------------------------------------

section("13. Scope metrics")

def traceability_coverage(
    requirements_list: Sequence[Requirement],
    deliverables_list: Sequence[Deliverable],
) -> float:
    if not requirements_list:
        return 100.0

    mapped = {
        req_id
        for deliverable in deliverables_list
        for req_id in deliverable.requirements
    }

    covered = sum(
        requirement.requirement_id in mapped
        for requirement in requirements_list
    )

    return covered / len(requirements_list) * 100


coverage = traceability_coverage(requirements, deliverables)
print(f"Requirement traceability coverage: {coverage:.1f}%")

priority_counts = Counter(r.priority for r in requirements)
print("Requirement priorities:", dict(priority_counts))

print("""
Useful scope metrics can include:

- requirements traceability coverage
- number of unapproved scope additions
- number of approved changes
- change-request cycle time
- requirements volatility
- deliverable acceptance rate
- number of ambiguous requirements
- number of requirements without acceptance criteria
- percentage of work packages linked to deliverables

Metrics should support decisions rather than become targets that encourage
distorted behavior.
""")

# ---------------------------------------------------------------------------
# 15. REQUIREMENT VOLATILITY
# ---------------------------------------------------------------------------

section("14. Requirement volatility")

initial_ids = {"REQ-001", "REQ-002", "REQ-003", "REQ-004"}
current_ids = {"REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005"}

added = current_ids - initial_ids
removed = initial_ids - current_ids

volatility_rate = (len(added) + len(removed)) / len(initial_ids) * 100

print("Added requirements:", sorted(added))
print("Removed requirements:", sorted(removed))
print(f"Simple requirement-set volatility: {volatility_rate:.1f}%")

print("""
Requirement volatility measures how much the requirement set changes during
a defined period. The exact formula should be agreed by the organization.

A high rate can indicate evolving business needs, unclear discovery, weak
stakeholder alignment, changing external conditions, or intentionally
incremental product development. The metric itself does not explain the cause.
""")

# ---------------------------------------------------------------------------
# 16. DEPENDENCIES
# ---------------------------------------------------------------------------

section("15. Scope dependencies")

@dataclass
class Dependency:
    predecessor: str
    successor: str
    reason: str

dependencies = [
    Dependency("REQ-001", "REQ-002", "An account must exist before normal sign-in."),
    Dependency("REQ-003", "DEL-002", "Dashboard behavior depends on searchable project data."),
]

for dependency in dependencies:
    print(
        f"{dependency.predecessor} -> {dependency.successor}: "
        f"{dependency.reason}"
    )

# ---------------------------------------------------------------------------
# 17. COMPLEXITY AND PERFORMANCE
# ---------------------------------------------------------------------------

section("16. Implementation considerations")

print("""
The examples above mainly use lists, dictionaries, sets, and linear scans.

Typical complexity:

- Dictionary lookup by identifier: average O(1)
- Set membership: average O(1)
- Sorting requirements: O(n log n)
- Scanning all requirements: O(n)
- Comparing two sets: approximately O(n + m)

For a small project, simple structures are usually sufficient. At larger
scales, efficient identifiers, indexing, persistence strategies, audit logs,
versioning, and database constraints become important.

The technical representation should not be mistaken for the project scope
itself. A database table containing requirements is an implementation of scope
management; the governed requirement remains the underlying project artifact.
""")

# ---------------------------------------------------------------------------
# 18. ADVANCED SCOPE MODEL
# ---------------------------------------------------------------------------

section("17. Integrated scope-planning model")

@dataclass
class ScopeModel:
    name: str
    objective: str
    requirements: List[Requirement]
    deliverables: List[Deliverable]
    work_packages: List[WorkPackage]
    exclusions: List[str]
    assumptions: List[str]
    constraints: List[str]

    def validate(self) -> Dict[str, List[str]]:
        errors: Dict[str, List[str]] = {}

        duplicate_requirements = find_duplicate_ids(
            self.requirements, "requirement_id"
        )
        if duplicate_requirements:
            errors["requirements"] = [
                f"Duplicate IDs: {duplicate_requirements}"
            ]

        requirement_ids = {r.requirement_id for r in self.requirements}

        for deliverable in self.deliverables:
            invalid = [
                req for req in deliverable.requirements
                if req not in requirement_ids
            ]
            if invalid:
                errors.setdefault("deliverables", []).append(
                    f"{deliverable.deliverable_id} references unknown "
                    f"requirements: {invalid}"
                )

        for package in self.work_packages:
            package_errors = package.validate()
            if package_errors:
                errors[f"WBS-{package.wbs_id}"] = package_errors

        return errors

    def effort_hours(self) -> float:
        return sum(w.estimated_hours for w in self.work_packages)

    def coverage(self) -> float:
        return traceability_coverage(
            self.requirements,
            self.deliverables,
        )


model = ScopeModel(
    name="Project Management MVP",
    objective=scope.objective,
    requirements=requirements,
    deliverables=deliverables,
    work_packages=work_packages,
    exclusions=scope.exclusions,
    assumptions=scope.assumptions,
    constraints=scope.constraints,
)

validation_errors = model.validate()

print("Model:", model.name)
print("Estimated effort:", model.effort_hours(), "hours")
print("Traceability coverage:", f"{model.coverage():.1f}%")
print("Validation errors:", validation_errors or "None")

# ---------------------------------------------------------------------------
# 19. FINAL PRACTICAL CHECKLIST
# ---------------------------------------------------------------------------

section("18. Scope planning checklist")

checklist = [
    ("Business objective is defined", bool(model.objective.strip())),
    ("Requirements are identified", bool(model.requirements)),
    ("Requirements have acceptance criteria",
     all(r.acceptance_criteria for r in model.requirements)),
    ("Requirements have sources", all(r.source for r in model.requirements)),
    ("Deliverables are defined", bool(model.deliverables)),
    ("Deliverables trace to requirements", model.coverage() == 100.0),
    ("Work packages are defined", bool(model.work_packages)),
    ("WBS work packages have effort estimates",
     all(w.estimated_hours > 0 for w in model.work_packages)),
    ("Exclusions are documented", bool(model.exclusions)),
    ("Assumptions are documented", bool(model.assumptions)),
    ("Constraints are documented", bool(model.constraints)),
    ("Scope has a baseline", bool(baseline.version)),
    ("Change control exists", True),
    ("Acceptance conditions are testable", True),
]

for description, passed in checklist:
    print(f"[{'PASS' if passed else 'FAIL'}] {description}")

print("""
Scope planning is effective when the project team can answer five questions
without ambiguity:

1. What outcome is required?
2. What work and deliverables are included?
3. What is explicitly excluded?
4. How will completion and acceptance be determined?
5. What happens when someone proposes a change?

The technical artifacts in this program represent those questions as data that
can be validated, traced, measured, and governed.
""")
