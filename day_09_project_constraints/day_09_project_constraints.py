"""
PROJECT CONSTRAINTS: TIME, COST, SCOPE, QUALITY, AND RESOURCES
================================================================

A comprehensive executable study file covering project constraints from
absolute beginner through advanced project-management practice.

The script uses only Python's standard library.

Core constraint model:
    Time      -> when the project must be completed
    Cost      -> how much the project may consume
    Scope     -> what the project must deliver
    Quality   -> how well the deliverables must perform
    Resources -> people, equipment, materials, technology, facilities, etc.

Important principle:
    Project constraints are interdependent. Changing one constraint often
    changes one or more of the others.

This script demonstrates:
    1. Fundamental terminology
    2. The classic constraint triangle and its extension
    3. Time management and scheduling
    4. Cost estimation and budgeting
    5. Scope definition and scope control
    6. Quality requirements and quality trade-offs
    7. Resource planning and capacity
    8. Constraint interactions
    9. Constraint prioritization
    10. Change requests and impact analysis
    11. Trade-off scoring
    12. Risk and uncertainty
    13. Critical path analysis
    14. Resource leveling concepts
    15. Earned Value Management
    16. Scenario analysis
    17. Feasibility analysis
    18. Constraint optimization
    19. Edge cases and common mistakes
    20. Validation, testing, and production-oriented practices

Run:
    python project_constraints.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from math import ceil
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ============================================================================
# SECTION 1: FUNDAMENTAL TERMINOLOGY
# ============================================================================

def print_title(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_subtitle(title: str) -> None:
    """Print a smaller heading."""
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


def explain_basic_terminology() -> None:
    """
    Introduce the basic vocabulary used in project constraint management.
    """
    print_title("1. FUNDAMENTAL TERMINOLOGY")

    terminology = {
        "Project": (
            "A temporary effort undertaken to create a unique product, "
            "service, result, or outcome."
        ),
        "Constraint": (
            "A limitation or condition that restricts project choices, "
            "execution, or outcomes."
        ),
        "Time": (
            "The temporal boundary of the project, including milestones, "
            "activities, dependencies, and deadlines."
        ),
        "Cost": (
            "The financial resources required to execute and complete the "
            "project."
        ),
        "Scope": (
            "The work and deliverables that are included in the project, "
            "including explicit boundaries around what is excluded."
        ),
        "Quality": (
            "The degree to which project deliverables and processes satisfy "
            "specified requirements and fitness-for-purpose expectations."
        ),
        "Resource": (
            "A person, team, facility, machine, material, software system, "
            "budget allocation, or other input required to perform work."
        ),
        "Baseline": (
            "An approved reference version of a plan used to compare actual "
            "performance against expectations."
        ),
        "Trade-off": (
            "A deliberate choice in which improving one constraint dimension "
            "causes or accepts a change in another."
        ),
        "Assumption": (
            "A condition believed to be true for planning purposes without "
            "being fully verified."
        ),
        "Dependency": (
            "A relationship in which one activity, deliverable, or decision "
            "depends on another."
        ),
        "Milestone": (
            "A significant point or event in a project schedule, normally "
            "representing completion or approval rather than duration."
        ),
        "Risk": (
            "An uncertain event or condition that, if it occurs, can affect "
            "project objectives positively or negatively."
        ),
        "Issue": (
            "A current problem or condition requiring action, rather than a "
            "future uncertain event."
        ),
    }

    for term, definition in terminology.items():
        print(f"{term:15} : {definition}")


# ============================================================================
# SECTION 2: THE CONSTRAINT MODEL
# ============================================================================

class ConstraintPriority(Enum):
    """
    Priority levels indicate how strongly a constraint should be protected.

    FIXED:
        The constraint is effectively non-negotiable.

    HIGH:
        Changes require significant approval or compensation.

    MEDIUM:
        Changes are possible with normal governance.

    LOW:
        The constraint can be adjusted relatively easily.
    """

    FIXED = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


@dataclass
class ProjectConstraints:
    """
    Represents the major project constraint dimensions.

    Values are intentionally generic:
        time_days: maximum planned duration
        cost: maximum planned budget
        scope_units: normalized amount of work or functionality
        quality_score: required quality level from 0 to 100
        resources: available resource units
    """

    time_days: float
    cost: float
    scope_units: float
    quality_score: float
    resources: float

    def validate(self) -> None:
        """Reject impossible or nonsensical constraint values."""
        if self.time_days <= 0:
            raise ValueError("time_days must be greater than zero.")

        if self.cost < 0:
            raise ValueError("cost cannot be negative.")

        if self.scope_units < 0:
            raise ValueError("scope_units cannot be negative.")

        if not 0 <= self.quality_score <= 100:
            raise ValueError("quality_score must be between 0 and 100.")

        if self.resources < 0:
            raise ValueError("resources cannot be negative.")

    def as_dict(self) -> Dict[str, float]:
        """Return constraints in a dictionary for reporting or analysis."""
        return {
            "time_days": self.time_days,
            "cost": self.cost,
            "scope_units": self.scope_units,
            "quality_score": self.quality_score,
            "resources": self.resources,
        }


def demonstrate_constraint_triangle() -> None:
    """
    Explain the traditional scope-time-cost model.

    The traditional project-management triangle treats scope, schedule, and
    cost as closely connected. Quality is often affected by changes to these
    variables even when quality is not drawn as a triangle corner.
    """
    print_title("2. THE PROJECT CONSTRAINT TRIANGLE")

    print(
        """
The traditional constraint triangle is commonly described as:

                    SCOPE
                   /     \\
                  /       \\
                 /         \\
              TIME ------- COST

A change to one side can create pressure on the others.

Examples:
    - Reduce time without reducing scope:
        More resources, overtime, automation, or higher cost may be needed.

    - Reduce cost without reducing scope:
        The schedule may become longer or resource capacity may decrease.

    - Increase scope without changing time:
        More people, technology, budget, or reduced quality margins may be
        required.

Quality is closely connected to all three:
    - Unrealistic deadlines can increase defects.
    - Insufficient budget can reduce testing.
    - Excessive scope can reduce attention per deliverable.

Resources are a practical capacity constraint because people, machines,
facilities, and specialist skills are finite.
"""
    )


# ============================================================================
# SECTION 3: CONSTRAINT PRIORITIZATION
# ============================================================================

@dataclass
class ConstraintPolicy:
    """Defines how strongly each constraint is protected."""

    time: ConstraintPriority
    cost: ConstraintPriority
    scope: ConstraintPriority
    quality: ConstraintPriority
    resources: ConstraintPriority

    def as_dict(self) -> Dict[str, int]:
        return {
            "time": self.time.value,
            "cost": self.cost.value,
            "scope": self.scope.value,
            "quality": self.quality.value,
            "resources": self.resources.value,
        }


def demonstrate_constraint_priorities() -> None:
    print_title("3. CONSTRAINT PRIORITIZATION")

    policy = ConstraintPolicy(
        time=ConstraintPriority.FIXED,
        cost=ConstraintPriority.HIGH,
        scope=ConstraintPriority.HIGH,
        quality=ConstraintPriority.FIXED,
        resources=ConstraintPriority.MEDIUM,
    )

    print("Example project constraint priorities:")
    for name, priority in policy.as_dict().items():
        print(f"  {name:10} -> priority score {priority}")

    print(
        """
Constraint priority matters because not every project can maximize every
dimension simultaneously.

For example:

    Fixed deadline + fixed quality
        -> scope may need to decrease or cost may need to increase.

    Fixed budget + fixed scope
        -> schedule may need to increase or quality margins may be pressured.

    Fixed scope + fixed schedule + fixed budget
        -> resource productivity and delivery risk become critical.

A good project manager does not simply say "everything is a priority."
They identify which constraints are truly fixed and which are negotiable.
"""
    )


# ============================================================================
# SECTION 4: TIME CONSTRAINTS
# ============================================================================

@dataclass
class Activity:
    """
    Represents a project activity.

    duration:
        Duration in working-time units.

    predecessors:
        Activity names that must finish before this activity begins.

    resource_demand:
        Number of resource units required while the activity executes.

    cost:
        Direct planned cost of performing the activity.

    quality_risk:
        A normalized indicator used by this educational simulation.
    """

    name: str
    duration: float
    predecessors: List[str] = field(default_factory=list)
    resource_demand: float = 1.0
    cost: float = 0.0
    quality_risk: float = 0.0

    def validate(self) -> None:
        if self.duration < 0:
            raise ValueError(f"Activity {self.name} has negative duration.")

        if self.resource_demand < 0:
            raise ValueError(f"Activity {self.name} has negative resources.")

        if self.cost < 0:
            raise ValueError(f"Activity {self.name} has negative cost.")

        if not 0 <= self.quality_risk <= 100:
            raise ValueError(
                f"Activity {self.name} quality_risk must be between 0 and 100."
            )


def validate_activity_network(activities: Sequence[Activity]) -> None:
    """
    Validate an activity dependency graph.

    Detects:
        - duplicate names
        - missing predecessors
        - circular dependencies
    """
    names = [activity.name for activity in activities]

    if len(names) != len(set(names)):
        raise ValueError("Activity names must be unique.")

    name_set = set(names)

    for activity in activities:
        activity.validate()

        for predecessor in activity.predecessors:
            if predecessor not in name_set:
                raise ValueError(
                    f"{activity.name} references missing predecessor "
                    f"{predecessor}."
                )

    # Depth-first search for cycles.
    state: Dict[str, int] = {name: 0 for name in names}
    activity_map = {activity.name: activity for activity in activities}

    def visit(name: str) -> None:
        if state[name] == 1:
            raise ValueError("Circular dependency detected.")

        if state[name] == 2:
            return

        state[name] = 1

        for predecessor in activity_map[name].predecessors:
            visit(predecessor)

        state[name] = 2

    for name in names:
        visit(name)


def calculate_critical_path(
    activities: Sequence[Activity],
) -> Tuple[float, List[str], Dict[str, float], Dict[str, float]]:
    """
    Calculate a simple CPM schedule.

    Returns:
        project_duration
        one critical path
        earliest finish for each activity
        latest finish for each activity

    The implementation assumes:
        - deterministic activity durations
        - finish-to-start dependencies
        - unlimited resources
        - no calendars or holidays
    """
    validate_activity_network(activities)

    activity_map = {activity.name: activity for activity in activities}

    earliest_start: Dict[str, float] = {}
    earliest_finish: Dict[str, float] = {}

    def calculate_early_times(name: str) -> None:
        if name in earliest_finish:
            return

        activity = activity_map[name]

        for predecessor in activity.predecessors:
            calculate_early_times(predecessor)

        earliest_start[name] = max(
            (earliest_finish[p] for p in activity.predecessors),
            default=0.0,
        )
        earliest_finish[name] = (
            earliest_start[name] + activity.duration
        )

    for activity in activities:
        calculate_early_times(activity.name)

    project_duration = max(earliest_finish.values(), default=0.0)

    successors: Dict[str, List[str]] = {
        activity.name: [] for activity in activities
    }

    for activity in activities:
        for predecessor in activity.predecessors:
            successors[predecessor].append(activity.name)

    latest_finish: Dict[str, float] = {}
    latest_start: Dict[str, float] = {}

    # Process activities in reverse topological order using repeated
    # dependency resolution.
    remaining = set(activity_map)

    while remaining:
        ready = [
            name
            for name in remaining
            if all(successor not in remaining for successor in successors[name])
        ]

        if not ready:
            raise ValueError("Unable to resolve activity network.")

        for name in ready:
            if successors[name]:
                latest_finish[name] = min(
                    latest_start[successor]
                    for successor in successors[name]
                )
            else:
                latest_finish[name] = project_duration

            latest_start[name] = (
                latest_finish[name] - activity_map[name].duration
            )

        remaining.difference_update(ready)

    slack = {
        name: latest_start[name] - earliest_start[name]
        for name in activity_map
    }

    # Identify one critical path by following zero-slack dependencies.
    end_activities = [
        name
        for name in activity_map
        if not successors[name] and abs(slack[name]) < 1e-9
    ]

    if not end_activities:
        return project_duration, [], earliest_finish, latest_finish

    current = end_activities[0]
    path_reversed = [current]

    while True:
        critical_predecessors = [
            predecessor
            for predecessor in activity_map[current].predecessors
            if abs(slack[predecessor]) < 1e-9
            and abs(
                earliest_finish[predecessor] - earliest_start[current]
            ) < 1e-9
        ]

        if not critical_predecessors:
            break

        current = critical_predecessors[0]
        path_reversed.append(current)

    path = list(reversed(path_reversed))

    return project_duration, path, earliest_finish, latest_finish


def demonstrate_time_constraints() -> None:
    print_title("4. TIME CONSTRAINTS AND CRITICAL PATH")

    activities = [
        Activity("Requirements", 3, cost=3000),
        Activity(
            "Architecture",
            4,
            predecessors=["Requirements"],
            cost=5000,
        ),
        Activity(
            "Development",
            8,
            predecessors=["Architecture"],
            resource_demand=3,
            cost=18000,
        ),
        Activity(
            "Testing",
            4,
            predecessors=["Development"],
            resource_demand=2,
            cost=7000,
        ),
        Activity(
            "Deployment",
            2,
            predecessors=["Testing"],
            resource_demand=2,
            cost=3000,
        ),
        Activity(
            "Documentation",
            3,
            predecessors=["Architecture"],
            resource_demand=1,
            cost=2000,
        ),
    ]

    duration, path, earliest_finish, latest_finish = calculate_critical_path(
        activities
    )

    print(f"Project duration: {duration:.1f} days")
    print(f"One critical path: {' -> '.join(path)}")

    print("\nActivity schedule:")
    for activity in activities:
        print(
            f"  {activity.name:15} "
            f"EF={earliest_finish[activity.name]:5.1f} "
            f"LF={latest_finish[activity.name]:5.1f}"
        )

    print(
        """
Critical Path Method (CPM):
    1. Model activities.
    2. Estimate activity durations.
    3. Establish dependencies.
    4. Calculate earliest start/finish.
    5. Calculate latest start/finish.
    6. Calculate float/slack.
    7. Identify activities with zero float.

A delay on a critical-path activity can delay the project unless the schedule
is recovered.

Important limitation:
    A CPM calculation without resource constraints assumes resources are
    available whenever required. Real projects often need resource leveling
    after the initial network schedule.
"""
    )


# ============================================================================
# SECTION 5: TIME COMPRESSION
# ============================================================================

@dataclass
class CompressionOption:
    """
    Represents a schedule-compression choice.

    normal_duration:
        Baseline duration.

    compressed_duration:
        Minimum practical duration.

    normal_cost:
        Baseline cost.

    compressed_cost:
        Cost at compressed duration.

    technique:
        Crashing or fast-tracking.
    """

    activity: str
    normal_duration: float
    compressed_duration: float
    normal_cost: float
    compressed_cost: float
    technique: str

    @property
    def time_saved(self) -> float:
        return self.normal_duration - self.compressed_duration

    @property
    def extra_cost(self) -> float:
        return self.compressed_cost - self.normal_cost

    @property
    def cost_per_day_saved(self) -> float:
        if self.time_saved <= 0:
            return float("inf")
        return self.extra_cost / self.time_saved


def demonstrate_schedule_compression() -> None:
    print_title("5. SCHEDULE COMPRESSION: CRASHING AND FAST-TRACKING")

    options = [
        CompressionOption(
            "Development",
            normal_duration=8,
            compressed_duration=6,
            normal_cost=18000,
            compressed_cost=22000,
            technique="Crashing",
        ),
        CompressionOption(
            "Testing",
            normal_duration=4,
            compressed_duration=3,
            normal_cost=7000,
            compressed_cost=9000,
            technique="Crashing",
        ),
    ]

    for option in options:
        print(
            f"{option.activity:15} "
            f"time saved={option.time_saved:.1f} days, "
            f"extra cost=${option.extra_cost:,.0f}, "
            f"cost/day=${option.cost_per_day_saved:,.0f}"
        )

    print(
        """
Crashing:
    Add resources, overtime, specialist support, automation, or other
    capacity to shorten duration. It generally increases cost.

Fast-tracking:
    Perform activities that were originally sequential partly in parallel.
    It can shorten the schedule without the same direct labor-cost increase,
    but it generally increases coordination and rework risk.

Schedule compression should be applied carefully:
    - Compress activities with meaningful schedule impact.
    - Protect quality-critical activities.
    - Verify dependencies before overlapping work.
    - Quantify additional cost and risk.
"""
    )


# ============================================================================
# SECTION 6: COST CONSTRAINTS
# ============================================================================

@dataclass
class CostItem:
    """Represents a planned project cost."""

    name: str
    amount: float
    category: str
    mandatory: bool = True

    def validate(self) -> None:
        if self.amount < 0:
            raise ValueError("Cost amount cannot be negative.")


def calculate_budget(
    cost_items: Sequence[CostItem],
    contingency_rate: float = 0.0,
) -> Dict[str, float]:
    """
    Calculate direct cost, contingency, and total budget.

    contingency_rate is expressed as a decimal:
        0.10 = 10%
    """
    if contingency_rate < 0:
        raise ValueError("Contingency rate cannot be negative.")

    for item in cost_items:
        item.validate()

    direct_cost = sum(item.amount for item in cost_items)
    contingency = direct_cost * contingency_rate

    return {
        "direct_cost": direct_cost,
        "contingency": contingency,
        "total_budget": direct_cost + contingency,
    }


def demonstrate_cost_constraints() -> None:
    print_title("6. COST CONSTRAINTS AND BUDGETING")

    costs = [
        CostItem("Project management", 8000, "Labor"),
        CostItem("Development", 25000, "Labor"),
        CostItem("Testing", 10000, "Labor"),
        CostItem("Cloud infrastructure", 5000, "Technology"),
        CostItem("Software licenses", 4000, "Technology"),
        CostItem("Training", 3000, "Training"),
    ]

    budget = calculate_budget(costs, contingency_rate=0.10)

    for key, value in budget.items():
        print(f"{key:15}: ${value:,.2f}")

    print(
        """
Budget structure:

    Direct costs
        + Contingency
        = Project budget

A useful distinction is between:
    - Cost estimate: forecast of what the work is expected to cost.
    - Budget: authorized funding allocated to the project.
    - Actual cost: what has actually been spent.
    - Forecast at completion: expected final cost.

Cost control compares actual and forecast values with the approved baseline.
"""
    )


# ============================================================================
# SECTION 7: FIXED, VARIABLE, DIRECT, INDIRECT, AND OPPORTUNITY COST
# ============================================================================

def classify_project_costs() -> None:
    print_title("7. COST CLASSIFICATIONS")

    examples = [
        ("Dedicated developer salary", "Direct", "Labor directly assigned"),
        ("Project office rent", "Indirect", "Shared organizational cost"),
        ("Cloud usage per transaction", "Variable", "Changes with usage"),
        ("Annual software license", "Fixed", "Stable within contract period"),
        ("Specialist contractor", "Direct", "Directly attributable"),
        ("Delayed market launch", "Opportunity", "Value sacrificed by delay"),
    ]

    print(f"{'Example':35} {'Type':12} Explanation")
    print("-" * 78)

    for example, category, explanation in examples:
        print(f"{example:35} {category:12} {explanation}")

    print(
        """
Important distinctions:

Fixed cost:
    Does not materially change with the relevant activity volume in the
    selected planning range.

Variable cost:
    Changes with activity, volume, usage, or output.

Direct cost:
    Can be directly attributed to the project or deliverable.

Indirect cost:
    Supports multiple projects or organizational activities and may require
    allocation.

Opportunity cost:
    The value of the best alternative that is forgone by choosing a given
    option.

A project can be under budget while still being economically unattractive if
its opportunity cost is high.
"""
    )


# ============================================================================
# SECTION 8: SCOPE CONSTRAINTS
# ============================================================================

@dataclass
class ScopeItem:
    """Represents a scope element or deliverable."""

    name: str
    effort: float
    value: float
    mandatory: bool = False
    priority: int = 1
    quality_requirement: float = 80.0

    def validate(self) -> None:
        if self.effort < 0:
            raise ValueError("Scope effort cannot be negative.")

        if self.value < 0:
            raise ValueError("Scope value cannot be negative.")

        if self.priority < 1:
            raise ValueError("Scope priority must be at least 1.")

        if not 0 <= self.quality_requirement <= 100:
            raise ValueError(
                "quality_requirement must be between 0 and 100."
            )


def prioritize_scope(
    scope_items: Sequence[ScopeItem],
    available_effort: float,
) -> List[ScopeItem]:
    """
    Select scope under a simple effort constraint.

    Mandatory items are selected first. Remaining items are selected using
    value density (value per unit of effort), with priority as a secondary
    criterion.

    This is an educational heuristic, not a universal scope-selection rule.
    """
    if available_effort < 0:
        raise ValueError("available_effort cannot be negative.")

    for item in scope_items:
        item.validate()

    mandatory = [item for item in scope_items if item.mandatory]
    optional = [item for item in scope_items if not item.mandatory]

    mandatory_effort = sum(item.effort for item in mandatory)

    if mandatory_effort > available_effort:
        raise ValueError(
            "Mandatory scope exceeds available effort. "
            "The project is infeasible under this constraint set."
        )

    remaining = available_effort - mandatory_effort

    optional_sorted = sorted(
        optional,
        key=lambda item: (
            item.value / item.effort if item.effort else float("inf"),
            item.priority,
        ),
        reverse=True,
    )

    selected = list(mandatory)

    for item in optional_sorted:
        if item.effort <= remaining:
            selected.append(item)
            remaining -= item.effort

    return selected


def demonstrate_scope_management() -> None:
    print_title("8. SCOPE MANAGEMENT AND SCOPE TRADE-OFFS")

    scope = [
        ScopeItem("Core authentication", 5, 100, mandatory=True, priority=5),
        ScopeItem("Core reporting", 8, 120, mandatory=True, priority=5),
        ScopeItem("Advanced dashboard", 10, 100, priority=4),
        ScopeItem("Mobile application", 15, 140, priority=3),
        ScopeItem("Export to PDF", 3, 60, priority=4),
        ScopeItem("Custom themes", 4, 30, priority=2),
        ScopeItem("AI recommendations", 12, 110, priority=3),
    ]

    selected = prioritize_scope(scope, available_effort=30)

    print("Selected scope under 30 effort units:")
    for item in selected:
        print(
            f"  {item.name:25} effort={item.effort:4.1f} "
            f"value={item.value:5.1f}"
        )

    total_effort = sum(item.effort for item in selected)
    total_value = sum(item.value for item in selected)

    print(f"\nTotal selected effort: {total_effort:.1f}")
    print(f"Total estimated value: {total_value:.1f}")

    print(
        """
Scope management involves:

    Scope definition
        -> scope baseline
        -> requirements
        -> deliverables
        -> acceptance criteria
        -> scope validation
        -> scope control

Scope creep:
    Uncontrolled expansion of project work without corresponding approval,
    budget, schedule, or resource adjustment.

Scope change:
    A formally considered change to approved project scope.

A legitimate change request is not automatically bad. The problem is
uncontrolled change that bypasses impact analysis and governance.
"""
    )


# ============================================================================
# SECTION 9: QUALITY CONSTRAINTS
# ============================================================================

@dataclass
class QualityRequirement:
    """Represents a measurable quality requirement."""

    name: str
    target: float
    unit: str
    mandatory: bool = True
    tolerance: float = 0.0

    def is_satisfied(self, actual: float, higher_is_better: bool = True) -> bool:
        """
        Check whether actual performance satisfies the requirement.

        For metrics where lower is better, set higher_is_better=False.
        """
        if higher_is_better:
            return actual + 1e-9 >= self.target - self.tolerance

        return actual <= self.target + self.tolerance


def demonstrate_quality_constraints() -> None:
    print_title("9. QUALITY CONSTRAINTS")

    quality_requirements = [
        QualityRequirement("Test coverage", 90, "%", True, tolerance=0),
        QualityRequirement("Availability", 99.9, "%", True, tolerance=0),
        QualityRequirement("Response time", 500, "ms", True, tolerance=0),
        QualityRequirement("Defect escape rate", 2, "%", True, tolerance=0),
    ]

    actual_values = {
        "Test coverage": (92, True),
        "Availability": (99.95, True),
        "Response time": (420, False),
        "Defect escape rate": (3, False),
    }

    for requirement in quality_requirements:
        actual, higher_is_better = actual_values[requirement.name]
        satisfied = requirement.is_satisfied(
            actual,
            higher_is_better=higher_is_better,
        )

        status = "PASS" if satisfied else "FAIL"

        print(
            f"{requirement.name:25} "
            f"target={requirement.target}{requirement.unit:4} "
            f"actual={actual}{requirement.unit:4} "
            f"{status}"
        )

    print(
        """
Quality has two related dimensions:

Quality assurance (QA):
    Process-oriented activities intended to build confidence that the
    appropriate processes are being followed.

Quality control (QC):
    Product-oriented activities that inspect or test outputs against
    requirements.

Examples of measurable quality criteria:
    - Defect rate
    - Availability
    - Response time
    - Test coverage
    - Accuracy
    - Reliability
    - Conformance
    - Customer acceptance rate

Quality should be specified through measurable acceptance criteria where
possible. A vague requirement such as "make it high quality" is difficult to
plan, test, and govern.
"""
    )


# ============================================================================
# SECTION 10: QUALITY-COST RELATIONSHIP
# ============================================================================

def estimate_quality_costs(
    base_cost: float,
    prevention_rate: float,
    appraisal_rate: float,
    internal_failure_rate: float,
    external_failure_rate: float,
) -> Dict[str, float]:
    """
    Illustrative Cost of Quality model.

    Prevention:
        Training, process design, automation, standards.

    Appraisal:
        Inspection, testing, audits.

    Internal failure:
        Rework and scrap detected before delivery.

    External failure:
        Warranty, support, reputation damage, remediation after release.
    """
    rates = [
        prevention_rate,
        appraisal_rate,
        internal_failure_rate,
        external_failure_rate,
    ]

    if any(rate < 0 for rate in rates):
        raise ValueError("Quality cost rates cannot be negative.")

    prevention = base_cost * prevention_rate
    appraisal = base_cost * appraisal_rate
    internal_failure = base_cost * internal_failure_rate
    external_failure = base_cost * external_failure_rate

    total = (
        prevention
        + appraisal
        + internal_failure
        + external_failure
    )

    return {
        "prevention": prevention,
        "appraisal": appraisal,
        "internal_failure": internal_failure,
        "external_failure": external_failure,
        "total_quality_cost": total,
    }


def demonstrate_cost_of_quality() -> None:
    print_title("10. COST OF QUALITY")

    low_prevention = estimate_quality_costs(
        base_cost=100000,
        prevention_rate=0.02,
        appraisal_rate=0.03,
        internal_failure_rate=0.08,
        external_failure_rate=0.12,
    )

    high_prevention = estimate_quality_costs(
        base_cost=100000,
        prevention_rate=0.06,
        appraisal_rate=0.05,
        internal_failure_rate=0.03,
        external_failure_rate=0.04,
    )

    print("Illustrative low-prevention scenario:")
    for key, value in low_prevention.items():
        print(f"  {key:20}: ${value:,.2f}")

    print("\nIllustrative high-prevention scenario:")
    for key, value in high_prevention.items():
        print(f"  {key:20}: ${value:,.2f}")

    print(
        """
Increasing prevention and appraisal spending can sometimes reduce failure
costs. The relationship is not automatically linear.

The important management question is not:
    "How can we spend the least on quality?"

It is:
    "What level of quality investment minimizes total lifecycle cost while
     satisfying business and customer requirements?"

The model above is illustrative rather than a universal cost function.
"""
    )


# ============================================================================
# SECTION 11: RESOURCE CONSTRAINTS
# ============================================================================

@dataclass
class Resource:
    """Represents a resource pool."""

    name: str
    capacity: float
    unit_cost_per_day: float

    def validate(self) -> None:
        if self.capacity < 0:
            raise ValueError("Resource capacity cannot be negative.")

        if self.unit_cost_per_day < 0:
            raise ValueError("Resource cost cannot be negative.")


def calculate_resource_cost(
    resource: Resource,
    units_used: float,
    duration_days: float,
) -> float:
    """Calculate resource cost for a period."""
    resource.validate()

    if units_used < 0:
        raise ValueError("units_used cannot be negative.")

    if units_used > resource.capacity:
        raise ValueError(
            f"Requested {units_used} units of {resource.name}, "
            f"but only {resource.capacity} are available."
        )

    if duration_days < 0:
        raise ValueError("duration_days cannot be negative.")

    return units_used * resource.unit_cost_per_day * duration_days


def demonstrate_resource_constraints() -> None:
    print_title("11. RESOURCE CONSTRAINTS")

    developers = Resource(
        name="Developers",
        capacity=5,
        unit_cost_per_day=500,
    )

    analysts = Resource(
        name="Business analysts",
        capacity=2,
        unit_cost_per_day=450,
    )

    developer_cost = calculate_resource_cost(
        developers,
        units_used=4,
        duration_days=20,
    )

    analyst_cost = calculate_resource_cost(
        analysts,
        units_used=2,
        duration_days=10,
    )

    print(f"Developer cost: ${developer_cost:,.2f}")
    print(f"Analyst cost:   ${analyst_cost:,.2f}")

    print(
        """
Resource constraints can involve:

Human resources:
    - Number of people
    - Skills
    - Experience
    - Availability
    - Location
    - Shift schedules

Physical resources:
    - Machines
    - Facilities
    - Equipment
    - Materials

Technical resources:
    - Servers
    - Cloud capacity
    - Licenses
    - APIs
    - Storage
    - Network capacity

A project can have sufficient total headcount but still be resource
constrained because the required specialist skill is scarce.
"""
    )


# ============================================================================
# SECTION 12: RESOURCE LEVELING
# ============================================================================

def demonstrate_resource_leveling() -> None:
    print_title("12. RESOURCE LEVELING")

    activities = [
        Activity("A", 4, resource_demand=3),
        Activity("B", 4, resource_demand=3),
        Activity("C", 3, predecessors=["A"], resource_demand=2),
        Activity("D", 2, predecessors=["B"], resource_demand=2),
    ]

    resource_capacity = 4

    print(f"Available resource capacity: {resource_capacity} units")

    print("\nInitial demand assumptions:")
    for activity in activities:
        print(
            f"  Activity {activity.name}: "
            f"duration={activity.duration}, "
            f"demand={activity.resource_demand}"
        )

    print(
        """
If A and B are scheduled simultaneously:

    A demand = 3
    B demand = 3
    ----------------
    Total    = 6

Available capacity = 4

The schedule is resource-infeasible even though the dependency network itself
may be logically valid.

Resource leveling may delay one activity to keep resource demand within
capacity.

This creates an important distinction:

    Logical schedule
        = respects activity dependencies.

    Resource-feasible schedule
        = respects dependencies AND resource availability.

Resource leveling can increase project duration because scarce resources
cannot perform all desired work simultaneously.
"""
    )


# ============================================================================
# SECTION 13: CONSTRAINT INTERACTIONS
# ============================================================================

@dataclass
class ProjectScenario:
    """Represents a simplified project scenario."""

    name: str
    duration_days: float
    cost: float
    scope_units: float
    quality_score: float
    resource_units: float

    def feasibility(
        self,
        constraints: ProjectConstraints,
    ) -> Dict[str, bool]:
        """
        Evaluate whether this scenario satisfies the project's constraints.
        """
        return {
            "time": self.duration_days <= constraints.time_days,
            "cost": self.cost <= constraints.cost,
            "scope": self.scope_units >= constraints.scope_units,
            "quality": self.quality_score >= constraints.quality_score,
            "resources": self.resource_units <= constraints.resources,
        }

    def is_feasible(self, constraints: ProjectConstraints) -> bool:
        return all(self.feasibility(constraints).values())


def demonstrate_constraint_interactions() -> None:
    print_title("13. INTERACTION BETWEEN CONSTRAINTS")

    constraints = ProjectConstraints(
        time_days=100,
        cost=100000,
        scope_units=100,
        quality_score=90,
        resources=10,
    )

    scenarios = [
        ProjectScenario(
            "Baseline",
            duration_days=100,
            cost=100000,
            scope_units=100,
            quality_score=90,
            resource_units=8,
        ),
        ProjectScenario(
            "Fast delivery",
            duration_days=80,
            cost=120000,
            scope_units=100,
            quality_score=90,
            resource_units=12,
        ),
        ProjectScenario(
            "Lower cost",
            duration_days=120,
            cost=85000,
            scope_units=100,
            quality_score=90,
            resource_units=7,
        ),
        ProjectScenario(
            "Reduced scope",
            duration_days=80,
            cost=80000,
            scope_units=75,
            quality_score=92,
            resource_units=8,
        ),
        ProjectScenario(
            "Quality pressure",
            duration_days=80,
            cost=90000,
            scope_units=100,
            quality_score=82,
            resource_units=8,
        ),
    ]

    for scenario in scenarios:
        result = scenario.feasibility(constraints)
        print(f"\n{scenario.name}:")
        print(
            "  "
            + ", ".join(
                f"{key}={'PASS' if value else 'FAIL'}"
                for key, value in result.items()
            )
        )
        print(f"  Feasible: {scenario.is_feasible(constraints)}")

    print(
        """
The scenarios demonstrate a central project-management reality:

    A project is not defined by one variable.

A decision that appears beneficial from one perspective can violate another
constraint.

Example:
    Adding developers may reduce schedule duration, but:
        - labor cost increases,
        - onboarding time may increase,
        - communication overhead may increase,
        - quality can temporarily decrease,
        - management effort can increase.

This is why constraint decisions require impact analysis rather than
single-variable optimization.
"""
    )


# ============================================================================
# SECTION 14: CHANGE REQUEST IMPACT ANALYSIS
# ============================================================================

@dataclass
class ChangeRequest:
    """Represents a proposed project change."""

    description: str
    scope_delta: float
    time_delta_days: float
    cost_delta: float
    quality_delta: float
    resource_delta: float


def analyze_change_request(
    baseline: ProjectConstraints,
    change: ChangeRequest,
) -> Dict[str, float]:
    """
    Apply a change to a baseline.

    Positive time_delta means more time required.
    Positive cost_delta means more cost.
    Positive scope_delta means additional scope.
    Positive quality_delta means higher expected quality.
    Positive resource_delta means more resources required.
    """
    return {
        "time": baseline.time_days + change.time_delta_days,
        "cost": baseline.cost + change.cost_delta,
        "scope": baseline.scope_units + change.scope_delta,
        "quality": baseline.quality_score + change.quality_delta,
        "resources": baseline.resources + change.resource_delta,
    }


def demonstrate_change_control() -> None:
    print_title("14. CHANGE CONTROL AND IMPACT ANALYSIS")

    baseline = ProjectConstraints(
        time_days=120,
        cost=150000,
        scope_units=100,
        quality_score=90,
        resources=10,
    )

    change = ChangeRequest(
        description="Add advanced reporting",
        scope_delta=15,
        time_delta_days=15,
        cost_delta=18000,
        quality_delta=2,
        resource_delta=2,
    )

    result = analyze_change_request(baseline, change)

    print(f"Change: {change.description}")

    for key, value in result.items():
        print(f"  {key:10}: {value}")

    print(
        """
A disciplined change-control process commonly includes:

    1. Identify the requested change.
    2. Clarify the business reason.
    3. Analyze scope impact.
    4. Analyze schedule impact.
    5. Analyze cost impact.
    6. Analyze resource impact.
    7. Analyze quality impact.
    8. Analyze risks and dependencies.
    9. Identify alternatives.
    10. Obtain the appropriate approval.
    11. Update affected baselines and plans.
    12. Communicate the decision.

A change should not be approved simply because the requested feature is
valuable. The project must remain feasible and economically justified.
"""
    )


# ============================================================================
# SECTION 15: TRADE-OFF SCORING
# ============================================================================

@dataclass
class WeightedCriteria:
    """Weights for evaluating project scenarios."""

    time: float
    cost: float
    scope: float
    quality: float
    resources: float

    def validate(self) -> None:
        weights = self.__dict__.values()

        if any(weight < 0 for weight in weights):
            raise ValueError("Weights cannot be negative.")

        if sum(weights) == 0:
            raise ValueError("At least one weight must be positive.")

    def normalized(self) -> Dict[str, float]:
        self.validate()

        total = sum(self.__dict__.values())

        return {
            key: value / total
            for key, value in self.__dict__.items()
        }


def score_scenario(
    scenario: ProjectScenario,
    constraints: ProjectConstraints,
    weights: WeightedCriteria,
) -> float:
    """
    Calculate an illustrative weighted score.

    Higher score is better.

    Metrics are normalized against project constraints. Values above the
    requirement are capped at 1.0. Cost, time, and resource usage are treated
    as "lower is better"; scope and quality are "higher is better."
    """
    normalized_weights = weights.normalized()

    time_score = min(
        1.0,
        constraints.time_days / scenario.duration_days
        if scenario.duration_days > 0
        else 0.0,
    )

    cost_score = min(
        1.0,
        constraints.cost / scenario.cost
        if scenario.cost > 0
        else 1.0,
    )

    scope_score = min(
        1.0,
        scenario.scope_units / constraints.scope_units
        if constraints.scope_units > 0
        else 1.0,
    )

    quality_score = min(
        1.0,
        scenario.quality_score / constraints.quality_score
        if constraints.quality_score > 0
        else 1.0,
    )

    resource_score = min(
        1.0,
        constraints.resources / scenario.resource_units
        if scenario.resource_units > 0
        else 1.0,
    )

    return (
        normalized_weights["time"] * time_score
        + normalized_weights["cost"] * cost_score
        + normalized_weights["scope"] * scope_score
        + normalized_weights["quality"] * quality_score
        + normalized_weights["resources"] * resource_score
    )


def demonstrate_tradeoff_scoring() -> None:
    print_title("15. MULTI-CRITERIA TRADE-OFF ANALYSIS")

    constraints = ProjectConstraints(
        time_days=100,
        cost=100000,
        scope_units=100,
        quality_score=90,
        resources=10,
    )

    scenarios = [
        ProjectScenario("Balanced", 100, 100000, 100, 90, 8),
        ProjectScenario("Fast", 75, 130000, 100, 91, 12),
        ProjectScenario("Economical", 125, 80000, 100, 90, 7),
        ProjectScenario("Lean scope", 85, 75000, 80, 92, 7),
    ]

    weights = WeightedCriteria(
        time=0.25,
        cost=0.20,
        scope=0.25,
        quality=0.25,
        resources=0.05,
    )

    print("Scenario scores:")
    for scenario in scenarios:
        score = score_scenario(scenario, constraints, weights)
        print(f"  {scenario.name:15}: {score:.4f}")

    print(
        """
Weighted scoring is useful when several criteria matter simultaneously.

The weights represent decision-maker priorities.

For example:
    Time       25%
    Cost       20%
    Scope      25%
    Quality    25%
    Resources   5%

The numerical result should support judgment, not replace it.

Potential weaknesses:
    - Scores can create false precision.
    - Weight selection can be subjective.
    - Poor normalization can distort comparisons.
    - Mandatory constraints should not always be treated as ordinary
      weighted criteria.

A fixed regulatory requirement should normally be modeled as a hard
constraint rather than simply receiving a high weight.
"""
    )


# ============================================================================
# SECTION 16: HARD CONSTRAINTS VS SOFT CONSTRAINTS
# ============================================================================

def demonstrate_hard_and_soft_constraints() -> None:
    print_title("16. HARD CONSTRAINTS VS SOFT CONSTRAINTS")

    examples = [
        ("Regulatory compliance", "Hard", "Must be satisfied"),
        ("Contractual launch date", "Hard", "May require formal renegotiation"),
        ("Budget ceiling", "Hard", "Cannot exceed without approval"),
        ("Preferred technology", "Soft", "Can change if justified"),
        ("Preferred team size", "Soft", "Can change with planning"),
        ("Nice-to-have feature", "Soft", "Can be removed"),
    ]

    for name, kind, explanation in examples:
        print(f"{name:28} {kind:6} {explanation}")

    print(
        """
Hard constraint:
    A condition that must be satisfied for the project or solution to be
    accepted.

Soft constraint:
    A preference that should be respected when practical but can be traded
    away.

This distinction is essential for decision quality.

Bad approach:
    Give every requirement a numerical weight and select the highest score.

Better approach:
    1. Filter out infeasible options using hard constraints.
    2. Rank remaining feasible options using soft criteria.
"""
    )


# ============================================================================
# SECTION 17: FEASIBILITY ANALYSIS
# ============================================================================

def identify_constraint_violations(
    scenario: ProjectScenario,
    constraints: ProjectConstraints,
) -> List[str]:
    """Return human-readable constraint violations."""
    violations: List[str] = []

    if scenario.duration_days > constraints.time_days:
        violations.append(
            f"Time exceeds limit by "
            f"{scenario.duration_days - constraints.time_days:.1f} days."
        )

    if scenario.cost > constraints.cost:
        violations.append(
            f"Cost exceeds budget by "
            f"${scenario.cost - constraints.cost:,.2f}."
        )

    if scenario.scope_units < constraints.scope_units:
        violations.append(
            f"Scope is short by "
            f"{constraints.scope_units - scenario.scope_units:.1f} units."
        )

    if scenario.quality_score < constraints.quality_score:
        violations.append(
            f"Quality is below target by "
            f"{constraints.quality_score - scenario.quality_score:.1f} points."
        )

    if scenario.resource_units > constraints.resources:
        violations.append(
            f"Resource demand exceeds capacity by "
            f"{scenario.resource_units - constraints.resources:.1f} units."
        )

    return violations


def demonstrate_feasibility_analysis() -> None:
    print_title("17. FEASIBILITY ANALYSIS")

    constraints = ProjectConstraints(
        time_days=90,
        cost=90000,
        scope_units=100,
        quality_score=90,
        resources=8,
    )

    scenario = ProjectScenario(
        "Proposed solution",
        duration_days=105,
        cost=95000,
        scope_units=100,
        quality_score=88,
        resource_units=10,
    )

    violations = identify_constraint_violations(
        scenario,
        constraints,
    )

    print("Constraint violations:")

    for violation in violations:
        print(f"  - {violation}")

    if not violations:
        print("  None. Scenario is feasible.")

    print(
        """
Feasibility analysis answers:

    "Can this project configuration satisfy the current constraints?"

It should happen before detailed execution planning and whenever a major
change is proposed.

If the configuration is infeasible, possible responses include:
    - Reduce scope
    - Increase budget
    - Extend schedule
    - Increase resource capacity
    - Improve productivity
    - Reduce unnecessary quality requirements
    - Change technology
    - Change delivery strategy
    - Re-negotiate contractual conditions

The correct response depends on which constraints are actually negotiable.
"""
    )


# ============================================================================
# SECTION 18: EARNED VALUE MANAGEMENT
# ============================================================================

@dataclass
class EarnedValueMetrics:
    """
    Simplified Earned Value Management metrics.

    PV = Planned Value
    EV = Earned Value
    AC = Actual Cost

    CPI = EV / AC
    SPI = EV / PV

    CPI < 1:
        Cost efficiency is unfavorable.

    CPI > 1:
        Cost efficiency is favorable.

    SPI < 1:
        Progress is behind the planned schedule.

    SPI > 1:
        Progress is ahead of the planned schedule.
    """

    planned_value: float
    earned_value: float
    actual_cost: float

    def validate(self) -> None:
        if self.planned_value < 0:
            raise ValueError("Planned value cannot be negative.")

        if self.earned_value < 0:
            raise ValueError("Earned value cannot be negative.")

        if self.actual_cost < 0:
            raise ValueError("Actual cost cannot be negative.")

    @property
    def cost_variance(self) -> float:
        return self.earned_value - self.actual_cost

    @property
    def schedule_variance(self) -> float:
        return self.earned_value - self.planned_value

    @property
    def cost_performance_index(self) -> Optional[float]:
        if self.actual_cost == 0:
            return None

        return self.earned_value / self.actual_cost

    @property
    def schedule_performance_index(self) -> Optional[float]:
        if self.planned_value == 0:
            return None

        return self.earned_value / self.planned_value


def demonstrate_earned_value() -> None:
    print_title("18. EARNED VALUE MANAGEMENT")

    metrics = EarnedValueMetrics(
        planned_value=60000,
        earned_value=50000,
        actual_cost=55000,
    )

    metrics.validate()

    print(f"PV:  ${metrics.planned_value:,.2f}")
    print(f"EV:  ${metrics.earned_value:,.2f}")
    print(f"AC:  ${metrics.actual_cost:,.2f}")
    print(f"CV:  ${metrics.cost_variance:,.2f}")
    print(f"SV:  ${metrics.schedule_variance:,.2f}")
    print(f"CPI: {metrics.cost_performance_index:.3f}")
    print(f"SPI: {metrics.schedule_performance_index:.3f}")

    print(
        """
Earned Value Management connects scope, schedule, and cost.

PV (Planned Value):
    Budgeted value of work that was planned to be completed.

EV (Earned Value):
    Budgeted value of work actually completed.

AC (Actual Cost):
    Actual amount spent for the completed work.

Cost Variance:
    CV = EV - AC

Schedule Variance:
    SV = EV - PV

Cost Performance Index:
    CPI = EV / AC

Schedule Performance Index:
    SPI = EV / PV

Interpretation for this example:
    CPI < 1 -> spending is inefficient relative to earned value.
    SPI < 1 -> progress is behind the planned value curve.

EVM does not literally measure calendar days in the SPI formula. It compares
earned value with planned value, so schedule interpretation requires context.
"""
    )


# ============================================================================
# SECTION 19: FORECASTING COST
# ============================================================================

def forecast_at_completion(
    budget_at_completion: float,
    earned_value: float,
    actual_cost: float,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate a simplified EAC and ETC.

    EAC using current cost efficiency:
        EAC = BAC / CPI

    ETC:
        ETC = EAC - AC

    Returns:
        EAC, ETC
    """
    if budget_at_completion < 0:
        raise ValueError("BAC cannot be negative.")

    if earned_value < 0:
        raise ValueError("EV cannot be negative.")

    if actual_cost < 0:
        raise ValueError("AC cannot be negative.")

    if actual_cost == 0 or earned_value == 0:
        return None, None

    cpi = earned_value / actual_cost

    if cpi == 0:
        return None, None

    eac = budget_at_completion / cpi
    etc = eac - actual_cost

    return eac, etc


def demonstrate_forecasting() -> None:
    print_title("19. COST FORECASTING")

    bac = 200000
    ev = 80000
    ac = 100000

    eac, etc = forecast_at_completion(
        budget_at_completion=bac,
        earned_value=ev,
        actual_cost=ac,
    )

    print(f"Budget at Completion (BAC): ${bac:,.2f}")
    print(f"Earned Value (EV):          ${ev:,.2f}")
    print(f"Actual Cost (AC):           ${ac:,.2f}")
    print(f"Forecast EAC:               ${eac:,.2f}")
    print(f"Estimated ETC:              ${etc:,.2f}")

    print(
        """
A simplified EAC forecast based on current CPI is:

    EAC = BAC / CPI

This assumes current cost efficiency is representative of future performance.

Real forecasting can be more sophisticated and may incorporate:
    - Remaining work estimates
    - Known future changes
    - Management judgment
    - Resource changes
    - Different cost behavior
    - Risk exposure

A mathematical forecast should be treated as a model, not a guarantee.
"""
    )


# ============================================================================
# SECTION 20: UNCERTAINTY AND CONTINGENCY
# ============================================================================

def expected_value(
    outcomes: Sequence[Tuple[float, float]],
) -> float:
    """
    Calculate expected value.

    Each tuple contains:
        probability, outcome_value

    Probabilities must sum to approximately 1.
    """
    if not outcomes:
        raise ValueError("At least one outcome is required.")

    probability_total = sum(probability for probability, _ in outcomes)

    if abs(probability_total - 1.0) > 1e-9:
        raise ValueError("Probabilities must sum to 1.")

    if any(probability < 0 for probability, _ in outcomes):
        raise ValueError("Probabilities cannot be negative.")

    return sum(
        probability * value
        for probability, value in outcomes
    )


def demonstrate_uncertainty() -> None:
    print_title("20. UNCERTAINTY, RISK, AND CONTINGENCY")

    duration_outcomes = [
        (0.20, 80),
        (0.50, 100),
        (0.30, 130),
    ]

    expected_duration = expected_value(duration_outcomes)

    print(f"Expected duration: {expected_duration:.1f} days")

    print(
        """
Planning under uncertainty requires separating:

Estimate:
    A forecast of the likely amount of time, cost, or resources required.

Risk:
    An uncertain event or condition that may affect objectives.

Contingency:
    Time, cost, or other capacity deliberately reserved for identified
    uncertainty or risk exposure.

Management reserve:
    Organizationally controlled reserve for unforeseen work within the
    project's overall management framework.

Expected value:
    A probability-weighted mathematical representation of uncertain
    outcomes.

Important:
    Expected value is not a prediction that the exact average outcome will
    occur. It is a decision-analysis construct.
"""
    )


# ============================================================================
# SECTION 21: MONTE CARLO-STYLE SIMULATION WITHOUT EXTERNAL PACKAGES
# ============================================================================

import random


def simulate_project_duration(
    activity_duration_ranges: Dict[str, Tuple[float, float]],
    dependencies: Dict[str, List[str]],
    simulations: int = 5000,
    seed: int = 42,
) -> Dict[str, float]:
    """
    Simulate project duration using uniformly sampled activity durations.

    This is intentionally simple for educational purposes.

    Assumptions:
        - Each activity duration is uniformly distributed between min and max.
        - Dependencies are finish-to-start.
        - Activity durations are sampled independently.
        - Resources are assumed unlimited.
    """
    if simulations <= 0:
        raise ValueError("simulations must be positive.")

    rng = random.Random(seed)

    names = set(activity_duration_ranges)

    if set(dependencies) != names:
        raise ValueError(
            "Every activity must have a dependency entry and vice versa."
        )

    for name, bounds in activity_duration_ranges.items():
        minimum, maximum = bounds

        if minimum < 0 or maximum < 0:
            raise ValueError("Durations cannot be negative.")

        if minimum > maximum:
            raise ValueError("Minimum duration cannot exceed maximum duration.")

        for predecessor in dependencies[name]:
            if predecessor not in names:
                raise ValueError(
                    f"Missing predecessor {predecessor} for {name}."
                )

    # Validate graph using Activity objects.
    activities = [
        Activity(
            name=name,
            duration=0,
            predecessors=dependencies[name],
        )
        for name in names
    ]
    validate_activity_network(activities)

    simulated_durations: List[float] = []

    for _ in range(simulations):
        sampled = {
            name: rng.uniform(*bounds)
            for name, bounds in activity_duration_ranges.items()
        }

        earliest_finish: Dict[str, float] = {}

        def finish_time(name: str) -> float:
            if name in earliest_finish:
                return earliest_finish[name]

            predecessor_finish = [
                finish_time(predecessor)
                for predecessor in dependencies[name]
            ]

            start = max(predecessor_finish, default=0.0)
            earliest_finish[name] = start + sampled[name]

            return earliest_finish[name]

        for name in names:
            finish_time(name)

        simulated_durations.append(max(earliest_finish.values()))

    simulated_durations.sort()

    def percentile(percent: float) -> float:
        index = int(
            round((percent / 100) * (len(simulated_durations) - 1))
        )
        return simulated_durations[index]

    mean = sum(simulated_durations) / len(simulated_durations)

    return {
        "mean": mean,
        "p50": percentile(50),
        "p80": percentile(80),
        "p90": percentile(90),
        "p95": percentile(95),
        "minimum": simulated_durations[0],
        "maximum": simulated_durations[-1],
    }


def demonstrate_schedule_simulation() -> None:
    print_title("21. PROBABILISTIC SCHEDULE SIMULATION")

    duration_ranges = {
        "Requirements": (3, 6),
        "Design": (4, 8),
        "Development": (8, 15),
        "Testing": (4, 8),
        "Deployment": (1, 3),
    }

    dependencies = {
        "Requirements": [],
        "Design": ["Requirements"],
        "Development": ["Design"],
        "Testing": ["Development"],
        "Deployment": ["Testing"],
    }

    result = simulate_project_duration(
        duration_ranges,
        dependencies,
        simulations=5000,
    )

    for key, value in result.items():
        print(f"{key:10}: {value:.2f} days")

    print(
        """
Deterministic planning might say:
    "The project takes 20 days."

Probabilistic planning asks:
    "What is the probability distribution of possible completion dates?"

Percentiles are useful for planning confidence.

For example:
    P50 means approximately half of simulated outcomes are at or below
    that duration.

    P90 means approximately 90% of simulated outcomes are at or below
    that duration.

The simulation is intentionally simplified. Production-grade quantitative
risk analysis may use distributions, correlations, calendars, resource
constraints, historical data, and validated statistical models.
"""
    )


# ============================================================================
# SECTION 22: CONSTRAINT NEGOTIATION
# ============================================================================

@dataclass
class NegotiationProposal:
    """Represents a proposed adjustment to constraints."""

    name: str
    time_change: float
    cost_change: float
    scope_change: float
    quality_change: float
    resource_change: float

    def apply(
        self,
        baseline: ProjectConstraints,
    ) -> ProjectConstraints:
        """
        Apply deltas to the baseline.

        Positive quality_change increases quality requirement.
        Positive scope_change increases required scope.
        """
        result = ProjectConstraints(
            time_days=baseline.time_days + self.time_change,
            cost=baseline.cost + self.cost_change,
            scope_units=baseline.scope_units + self.scope_change,
            quality_score=baseline.quality_score + self.quality_change,
            resources=baseline.resources + self.resource_change,
        )

        result.validate()
        return result


def demonstrate_constraint_negotiation() -> None:
    print_title("22. CONSTRAINT NEGOTIATION")

    baseline = ProjectConstraints(
        time_days=60,
        cost=50000,
        scope_units=100,
        quality_score=90,
        resources=5,
    )

    proposals = [
        NegotiationProposal(
            "Extend deadline",
            time_change=15,
            cost_change=0,
            scope_change=0,
            quality_change=0,
            resource_change=0,
        ),
        NegotiationProposal(
            "Increase budget",
            time_change=0,
            cost_change=15000,
            scope_change=0,
            quality_change=0,
            resource_change=2,
        ),
        NegotiationProposal(
            "Reduce scope",
            time_change=-5,
            cost_change=-5000,
            scope_change=-15,
            quality_change=0,
            resource_change=-1,
        ),
    ]

    for proposal in proposals:
        adjusted = proposal.apply(baseline)

        print(f"\n{proposal.name}:")
        for key, value in adjusted.as_dict().items():
            print(f"  {key:12}: {value}")

    print(
        """
Constraint negotiation is a structured process rather than an argument over
which team should absorb the problem.

A useful negotiation sequence is:

    Problem
        -> constraint causing the conflict
        -> options
        -> quantified impacts
        -> stakeholder priorities
        -> decision
        -> updated baseline

The goal is not to eliminate trade-offs. Trade-offs are inherent in finite
projects. The goal is to make them explicit and governed.
"""
    )


# ============================================================================
# SECTION 23: PROGRESSIVE ELABORATION
# ============================================================================

def demonstrate_progressive_elaboration() -> None:
    print_title("23. PROGRESSIVE ELABORATION")

    planning_stages = [
        (
            "Concept",
            "High-level business outcome, rough duration and cost range.",
        ),
        (
            "Initiation",
            "Initial scope, stakeholders, assumptions, constraints and risks.",
        ),
        (
            "Planning",
            "Detailed work packages, schedule, budget, resources and quality.",
        ),
        (
            "Execution",
            "Actual performance data, changes, issues and corrective action.",
        ),
        (
            "Closing",
            "Acceptance, final cost, final schedule and lessons learned.",
        ),
    ]

    for stage, description in planning_stages:
        print(f"{stage:12}: {description}")

    print(
        """
Early estimates often contain greater uncertainty.

Progressive elaboration means the project plan becomes more detailed as
information becomes available.

It does NOT mean:
    "Planning can be ignored until execution."

It means:
    "Planning should be appropriate to the information and decision
     maturity available at each point in the project."
"""
    )


# ============================================================================
# SECTION 24: BASELINES AND CONTROL
# ============================================================================

@dataclass
class ProjectBaseline:
    """Stores approved project reference values."""

    approved_time_days: float
    approved_cost: float
    approved_scope_units: float
    approved_quality_score: float
    approved_resources: float

    def validate(self) -> None:
        ProjectConstraints(
            time_days=self.approved_time_days,
            cost=self.approved_cost,
            scope_units=self.approved_scope_units,
            quality_score=self.approved_quality_score,
            resources=self.approved_resources,
        ).validate()


@dataclass
class ActualPerformance:
    """Stores actual or current project performance."""

    elapsed_days: float
    actual_cost: float
    delivered_scope_units: float
    actual_quality_score: float
    resources_used: float


def compare_against_baseline(
    baseline: ProjectBaseline,
    actual: ActualPerformance,
) -> Dict[str, float]:
    """
    Compare current performance with the approved baseline.

    Positive variance generally indicates:
        - time: more elapsed time than baseline
        - cost: more cost than baseline
        - scope: more delivered scope than baseline
        - quality: higher quality
        - resources: more resources used

    Interpretation depends on project context.
    """
    baseline.validate()

    return {
        "time_variance": (
            actual.elapsed_days - baseline.approved_time_days
        ),
        "cost_variance": (
            actual.actual_cost - baseline.approved_cost
        ),
        "scope_variance": (
            actual.delivered_scope_units
            - baseline.approved_scope_units
        ),
        "quality_variance": (
            actual.actual_quality_score
            - baseline.approved_quality_score
        ),
        "resource_variance": (
            actual.resources_used
            - baseline.approved_resources
        ),
    }


def demonstrate_baseline_control() -> None:
    print_title("24. BASELINES AND PERFORMANCE CONTROL")

    baseline = ProjectBaseline(
        approved_time_days=100,
        approved_cost=100000,
        approved_scope_units=100,
        approved_quality_score=90,
        approved_resources=8,
    )

    actual = ActualPerformance(
        elapsed_days=108,
        actual_cost=106000,
        delivered_scope_units=100,
        actual_quality_score=93,
        resources_used=9,
    )

    variance = compare_against_baseline(
        baseline,
        actual,
    )

    for key, value in variance.items():
        print(f"{key:20}: {value:+.2f}")

    print(
        """
A baseline provides a controlled reference point.

Without a baseline:
    "We spent $106,000."

With a baseline:
    "We spent $106,000 against an approved $100,000 baseline."

The second statement is more useful for control.

Baseline changes should be governed. If every change immediately changes
the baseline without approval, the project can appear to perform well simply
because its target was continuously moved.
"""
    )


# ============================================================================
# SECTION 25: QUALITY, SCOPE, AND ACCEPTANCE CRITERIA
# ============================================================================

@dataclass
class AcceptanceCriterion:
    """A measurable criterion used for deliverable acceptance."""

    description: str
    target: float
    actual: float
    tolerance: float = 0.0
    higher_is_better: bool = True

    def passed(self) -> bool:
        if self.higher_is_better:
            return self.actual >= self.target - self.tolerance

        return self.actual <= self.target + self.tolerance


def validate_deliverable(
    criteria: Sequence[AcceptanceCriterion],
) -> Tuple[bool, List[str]]:
    """Evaluate all acceptance criteria."""
    failures: List[str] = []

    for criterion in criteria:
        if not criterion.passed():
            failures.append(criterion.description)

    return len(failures) == 0, failures


def demonstrate_acceptance_criteria() -> None:
    print_title("25. ACCEPTANCE CRITERIA")

    criteria = [
        AcceptanceCriterion(
            "At least 95% of transactions succeed",
            target=95,
            actual=97,
        ),
        AcceptanceCriterion(
            "Response time is at most 500 ms",
            target=500,
            actual=430,
            higher_is_better=False,
        ),
        AcceptanceCriterion(
            "Critical defects equal zero",
            target=0,
            actual=1,
            higher_is_better=False,
        ),
    ]

    passed, failures = validate_deliverable(criteria)

    print(f"Deliverable accepted: {passed}")

    if failures:
        print("Failed criteria:")
        for failure in failures:
            print(f"  - {failure}")

    print(
        """
Acceptance criteria connect scope and quality.

A deliverable is not necessarily complete because the team has finished the
work. It is complete when the agreed acceptance conditions are satisfied.

This distinction prevents:
    "We finished development"

from being incorrectly interpreted as:
    "The deliverable has been accepted."
"""
    )


# ============================================================================
# SECTION 26: CONSTRAINT ESCALATION
# ============================================================================

def escalation_level(
    variance_percent: float,
    warning_threshold: float = 5.0,
    critical_threshold: float = 10.0,
) -> str:
    """
    Classify a percentage variance.

    Absolute variance is used because both positive and negative deviations
    can require attention.
    """
    if warning_threshold < 0 or critical_threshold < warning_threshold:
        raise ValueError("Invalid escalation thresholds.")

    magnitude = abs(variance_percent)

    if magnitude >= critical_threshold:
        return "CRITICAL"

    if magnitude >= warning_threshold:
        return "WARNING"

    return "NORMAL"


def demonstrate_escalation() -> None:
    print_title("26. VARIANCE THRESHOLDS AND ESCALATION")

    examples = [-2, 4, 7, 11, 18]

    for variance in examples:
        level = escalation_level(variance)
        print(f"Variance {variance:+5.1f}% -> {level}")

    print(
        """
Thresholds convert raw monitoring data into management action.

Example:
    0-5%     -> normal monitoring
    5-10%    -> warning and investigation
    10%+     -> critical escalation

These thresholds are illustrative. Real thresholds should reflect:
    - contract requirements
    - organizational governance
    - risk appetite
    - project size
    - criticality
    - regulatory requirements
"""
    )


# ============================================================================
# SECTION 27: PRODUCTIVITY AND CAPACITY
# ============================================================================

def calculate_required_resources(
    work_units: float,
    productivity_per_person_per_day: float,
    available_days: float,
) -> int:
    """
    Estimate the minimum number of people required.

    Formula:
        people = ceiling(work / productivity / available_days)
    """
    if work_units < 0:
        raise ValueError("work_units cannot be negative.")

    if productivity_per_person_per_day <= 0:
        raise ValueError(
            "productivity_per_person_per_day must be positive."
        )

    if available_days <= 0:
        raise ValueError("available_days must be positive.")

    required = work_units / (
        productivity_per_person_per_day * available_days
    )

    return ceil(required)


def demonstrate_capacity_planning() -> None:
    print_title("27. CAPACITY AND PRODUCTIVITY")

    required_people = calculate_required_resources(
        work_units=1200,
        productivity_per_person_per_day=6,
        available_days=40,
    )

    print(f"Required people: {required_people}")

    print(
        """
A simple capacity model is:

    Capacity = number of resources
               × productive units per resource per time
               × available time

This model is useful for rough planning but can be misleading if productivity
is treated as perfectly linear.

Adding people does not necessarily multiply productivity because of:
    - communication overhead
    - onboarding
    - coordination
    - dependencies
    - management overhead
    - scarce specialist skills
    - shared infrastructure
    - rework

This is one reason schedule compression has diminishing returns.
"""
    )


# ============================================================================
# SECTION 28: LAW OF DIMINISHING RETURNS IN SCHEDULE COMPRESSION
# ============================================================================

def productivity_gain(
    additional_resources: float,
    base_productivity: float,
    diminishing_factor: float = 0.12,
) -> float:
    """
    Illustrative nonlinear productivity model.

    productivity = base + additional * base * diminishing_factor-adjusted
    contribution.

    The model intentionally demonstrates diminishing returns rather than
    claiming a universal production equation.
    """
    if additional_resources < 0:
        raise ValueError("additional_resources cannot be negative.")

    if base_productivity <= 0:
        raise ValueError("base_productivity must be positive.")

    if not 0 < diminishing_factor <= 1:
        raise ValueError("diminishing_factor must be in (0, 1].")

    return base_productivity * (
        1 + (additional_resources ** 0.7) * diminishing_factor
    )


def demonstrate_diminishing_returns() -> None:
    print_title("28. DIMINISHING RETURNS FROM ADDITIONAL RESOURCES")

    base_productivity = 100

    for additional in range(0, 11, 2):
        productivity = productivity_gain(
            additional,
            base_productivity,
        )
        print(
            f"Additional resources={additional:2d} "
            f"estimated productivity={productivity:7.2f}"
        )

    print(
        """
The example uses a deliberately simplified nonlinear relationship.

The important concept is structural:
    More resources can increase capacity, but the increase may not be
    proportional.

A project manager should therefore evaluate:
    marginal productivity
    versus
    marginal cost
    versus
    coordination and quality risk.
"""
    )


# ============================================================================
# SECTION 29: REAL-WORLD APPLICATIONS
# ============================================================================

def demonstrate_real_world_applications() -> None:
    print_title("29. REAL-WORLD APPLICATIONS")

    applications = {
        "Software development": [
            "release deadline",
            "feature scope",
            "engineering capacity",
            "test quality",
            "cloud and license cost",
        ],
        "Construction": [
            "completion date",
            "materials budget",
            "design scope",
            "safety and quality",
            "labor and equipment",
        ],
        "Healthcare implementation": [
            "go-live deadline",
            "implementation cost",
            "clinical functionality",
            "patient safety",
            "specialist availability",
        ],
        "Manufacturing": [
            "production schedule",
            "unit cost",
            "product configuration",
            "defect rate",
            "machine capacity",
        ],
        "Consulting": [
            "client deadline",
            "fee ceiling",
            "deliverables",
            "analytical quality",
            "consultant availability",
        ],
    }

    for industry, constraints in applications.items():
        print(f"\n{industry}:")
        for constraint in constraints:
            print(f"  - {constraint}")

    print(
        """
The constraint framework is domain-independent, but the actual constraints
and quality definitions vary substantially by industry.

For safety-critical, regulated, or contractual projects, some constraints
may be absolute rather than negotiable.
"""
    )


# ============================================================================
# SECTION 30: EDGE CASES
# ============================================================================

def demonstrate_edge_cases() -> None:
    print_title("30. IMPORTANT EDGE CASES")

    edge_cases = [
        (
            "Zero scope",
            "A project can theoretically have zero deliverable scope, but "
            "such a project requires a clear reason to exist."
        ),
        (
            "Zero resources",
            "No execution capacity means positive-duration work cannot "
            "normally be completed."
        ),
        (
            "Zero cost",
            "A project may have no incremental monetary cost if existing "
            "resources are used, but this does not imply zero economic cost."
        ),
        (
            "Very high quality target",
            "A 100% quality target may be unrealistic depending on how "
            "quality is measured and the nature of the system."
        ),
        (
            "Negative float",
            "Negative schedule float can occur when required dates are "
            "earlier than what the current network can support."
        ),
        (
            "Mandatory scope exceeds capacity",
            "The project is infeasible unless a constraint changes."
        ),
        (
            "Multiple critical paths",
            "More than one path may have zero or near-zero float, increasing "
            "schedule sensitivity."
        ),
        (
            "Shared specialist",
            "A project may appear adequately staffed until two activities "
            "simultaneously require the same scarce skill."
        ),
    ]

    for name, explanation in edge_cases:
        print(f"\n{name}:")
        print(f"  {explanation}")


# ============================================================================
# SECTION 31: COMMON MISTAKES
# ============================================================================

def demonstrate_common_mistakes() -> None:
    print_title("31. COMMON PROJECT-CONSTRAINT MISTAKES")

    mistakes = [
        (
            "Treating every constraint as fixed",
            "If everything is fixed, there may be no feasible adjustment when "
            "conditions change."
        ),
        (
            "Ignoring scope boundaries",
            "Unclear boundaries create uncontrolled work and unreliable "
            "schedule and cost estimates."
        ),
        (
            "Compressing every activity",
            "Only schedule-relevant activities should normally be candidates "
            "for expensive compression."
        ),
        (
            "Adding people as the only recovery strategy",
            "Additional resources can introduce coordination and onboarding "
            "costs."
        ),
        (
            "Using budget as a success metric alone",
            "Being under budget while delivering late or incomplete scope is "
            "not necessarily project success."
        ),
        (
            "Treating quality as an optional afterthought",
            "Quality defects can create rework, delays, and lifecycle cost."
        ),
        (
            "Ignoring resource calendars",
            "A resource may exist but not be available at the required time."
        ),
        (
            "Changing baselines without governance",
            "Repeatedly changing targets can conceal actual performance."
        ),
        (
            "Using weighted scoring for hard requirements",
            "An infeasible option should not win simply because it has a "
            "higher weighted score elsewhere."
        ),
        (
            "Confusing estimates with commitments",
            "An estimate describes expected effort or cost; a commitment "
            "represents an agreed obligation."
        ),
    ]

    for mistake, explanation in mistakes:
        print(f"\n{mistake}:")
        print(f"  {explanation}")


# ============================================================================
# SECTION 32: SECURITY AND GOVERNANCE CONSIDERATIONS
# ============================================================================

def demonstrate_security_and_governance() -> None:
    print_title("32. SECURITY AND GOVERNANCE CONSIDERATIONS")

    controls = [
        (
            "Access control",
            "Ensure only authorized people can modify project plans, budgets, "
            "requirements, and approvals."
        ),
        (
            "Change authorization",
            "Require appropriate approval for material scope, budget, "
            "schedule, or quality changes."
        ),
        (
            "Auditability",
            "Maintain records of decisions, approvals, baseline changes, and "
            "significant assumptions."
        ),
        (
            "Data integrity",
            "Protect cost, schedule, resource, and quality data from accidental "
            "or unauthorized modification."
        ),
        (
            "Separation of duties",
            "Where appropriate, separate request, approval, and execution "
            "responsibilities."
        ),
        (
            "Confidentiality",
            "Protect commercially sensitive budgets, vendor rates, staffing "
            "information, and contractual terms."
        ),
    ]

    for control, explanation in controls:
        print(f"\n{control}:")
        print(f"  {explanation}")

    print(
        """
Project constraint management is partly a governance problem.

If stakeholders can freely alter scope, deadlines, budgets, or quality
criteria without traceability, performance data becomes unreliable and
decision-making becomes difficult.

For technology projects, project controls should also respect:
    - credential security
    - least privilege
    - protection of production systems
    - secure change management
    - privacy requirements
    - vendor and third-party risk
"""
    )


# ============================================================================
# SECTION 33: IMPLEMENTATION CONSIDERATIONS FOR PROJECT SYSTEMS
# ============================================================================

@dataclass
class ConstraintRecord:
    """
    Machine-readable project constraint record.

    This structure illustrates how a project-management application might
    represent constraint data.
    """

    name: str
    baseline: float
    current: float
    unit: str
    tolerance: float = 0.0

    @property
    def variance(self) -> float:
        return self.current - self.baseline

    @property
    def variance_percent(self) -> Optional[float]:
        if self.baseline == 0:
            return None

        return (self.variance / self.baseline) * 100

    def status(self) -> str:
        percentage = self.variance_percent

        if percentage is None:
            return "UNDEFINED_BASELINE"

        return escalation_level(abs(percentage))


def demonstrate_constraint_records() -> None:
    print_title("33. IMPLEMENTING CONSTRAINT MONITORING")

    records = [
        ConstraintRecord("Schedule", 100, 108, "days"),
        ConstraintRecord("Cost", 100000, 106000, "USD"),
        ConstraintRecord("Scope", 100, 100, "units"),
        ConstraintRecord("Quality", 90, 93, "score"),
        ConstraintRecord("Resources", 8, 9, "people"),
    ]

    print(
        f"{'Constraint':15} {'Baseline':>12} {'Current':>12} "
        f"{'Variance %':>12} {'Status':>15}"
    )
    print("-" * 78)

    for record in records:
        variance = record.variance_percent

        variance_text = (
            f"{variance:+.2f}%"
            if variance is not None
            else "N/A"
        )

        print(
            f"{record.name:15} "
            f"{record.baseline:12.2f} "
            f"{record.current:12.2f} "
            f"{variance_text:>12} "
            f"{record.status():>15}"
        )

    print(
        """
A production project-control system should normally distinguish:

    Raw data
        -> validated measurements
        -> baseline comparison
        -> threshold evaluation
        -> alerts
        -> decision
        -> approved action
        -> updated plan

Good systems preserve historical records rather than overwriting previous
values.
"""
    )


# ============================================================================
# SECTION 34: TESTING PROJECT-CONSTRAINT LOGIC
# ============================================================================

def run_assertion_tests() -> None:
    print_title("34. BUILT-IN TESTS")

    # Constraint validation.
    constraints = ProjectConstraints(
        time_days=10,
        cost=1000,
        scope_units=20,
        quality_score=90,
        resources=5,
    )

    constraints.validate()
    assert constraints.as_dict()["cost"] == 1000

    # Quality testing.
    requirement = QualityRequirement(
        "Coverage",
        target=90,
        unit="%",
    )

    assert requirement.is_satisfied(95)
    assert not requirement.is_satisfied(80)

    # Cost calculation.
    budget = calculate_budget(
        [CostItem("Labor", 1000, "Labor")],
        contingency_rate=0.10,
    )

    assert budget["total_budget"] == 1100

    # Critical path.
    activities = [
        Activity("A", 3),
        Activity("B", 5, predecessors=["A"]),
    ]

    duration, path, _, _ = calculate_critical_path(activities)

    assert duration == 8
    assert path == ["A", "B"]

    # Feasibility.
    scenario = ProjectScenario(
        "Test",
        duration_days=10,
        cost=1000,
        scope_units=20,
        quality_score=90,
        resource_units=5,
    )

    assert scenario.is_feasible(constraints)

    # EVM.
    evm = EarnedValueMetrics(
        planned_value=100,
        earned_value=80,
        actual_cost=90,
    )

    assert evm.cost_performance_index < 1
    assert evm.schedule_performance_index < 1

    # Acceptance criteria.
    passed, failures = validate_deliverable(
        [
            AcceptanceCriterion(
                "Minimum score",
                target=90,
                actual=95,
            )
        ]
    )

    assert passed
    assert not failures

    print("All assertion tests passed.")


# ============================================================================
# SECTION 35: INTEGRATED PROJECT CASE
# ============================================================================

def integrated_project_case() -> None:
    print_title("35. INTEGRATED PROJECT-CONSTRAINT CASE STUDY")

    print(
        """
Case:
    A company is implementing a customer-service platform.

Approved constraints:
    Time      = 120 days
    Cost      = $250,000
    Scope     = 100 functional units
    Quality   = minimum 92/100
    Resources = maximum 12 concurrent resource units

Current forecast:
    Time      = 135 days
    Cost      = $275,000
    Scope     = 100 units
    Quality   = 94/100
    Resources = 14 units

The project is currently infeasible because:
    - schedule is late,
    - cost exceeds budget,
    - resource demand exceeds capacity.

Quality is above the required threshold.

Possible responses:
    A. Reduce scope.
    B. Increase budget.
    C. Extend deadline.
    D. Increase productivity.
    E. Change architecture or delivery approach.
    F. Reprioritize scope into releases.
    G. Combine multiple responses.
"""
    )

    baseline = ProjectConstraints(
        time_days=120,
        cost=250000,
        scope_units=100,
        quality_score=92,
        resources=12,
    )

    forecast = ProjectScenario(
        "Current forecast",
        duration_days=135,
        cost=275000,
        scope_units=100,
        quality_score=94,
        resource_units=14,
    )

    print("Current violations:")
    for violation in identify_constraint_violations(
        forecast,
        baseline,
    ):
        print(f"  - {violation}")

    options = [
        ProjectScenario(
            "Reduce scope",
            duration_days=118,
            cost=235000,
            scope_units=90,
            quality_score=94,
            resource_units=12,
        ),
        ProjectScenario(
            "Increase budget and resources",
            duration_days=110,
            cost=285000,
            scope_units=100,
            quality_score=94,
            resource_units=12,
        ),
        ProjectScenario(
            "Extend deadline",
            duration_days=135,
            cost=245000,
            scope_units=100,
            quality_score=94,
            resource_units=11,
        ),
        ProjectScenario(
            "Replan delivery",
            duration_days=120,
            cost=248000,
            scope_units=100,
            quality_score=93,
            resource_units=12,
        ),
    ]

    print("\nCandidate responses:")
    for option in options:
        feasible = option.is_feasible(baseline)
        print(
            f"  {option.name:32} "
            f"feasible={feasible}"
        )

    print(
        """
The case demonstrates why constraint management is a decision system.

A manager should ask:
    - Which constraints are truly fixed?
    - Which constraint is driving the problem?
    - What is the cheapest acceptable recovery?
    - What risks are introduced by each option?
    - What quality consequences exist?
    - What stakeholder approval is required?
    - Does the proposed solution create a new constraint problem?

The best option is not necessarily the one that optimizes one metric. It is
the one that provides an acceptable project outcome under the organization's
actual priorities and governance rules.
"""
    )


# ============================================================================
# SECTION 36: DECISION FRAMEWORK
# ============================================================================

def constraint_decision_framework() -> None:
    print_title("36. PRACTICAL CONSTRAINT DECISION FRAMEWORK")

    steps = [
        "1. Define the project outcome and measurable deliverables.",
        "2. Identify time, cost, scope, quality, and resource constraints.",
        "3. Classify each constraint as hard, high, medium, or flexible.",
        "4. Establish approved baselines.",
        "5. Identify assumptions and dependencies.",
        "6. Build the schedule and resource model.",
        "7. Estimate cost and contingency.",
        "8. Define measurable quality and acceptance criteria.",
        "9. Monitor actual performance against baselines.",
        "10. Detect variance and emerging constraint conflicts.",
        "11. Analyze root causes rather than only symptoms.",
        "12. Generate multiple recovery or trade-off options.",
        "13. Quantify impacts on every major constraint.",
        "14. Reject infeasible options.",
        "15. Evaluate feasible options using stakeholder priorities.",
        "16. Obtain appropriate approval.",
        "17. Update plans and baselines through controlled change.",
        "18. Monitor the consequences of the decision.",
    ]

    for step in steps:
        print(step)


# ============================================================================
# SECTION 37: ADVANCED PRINCIPLES
# ============================================================================

def demonstrate_advanced_principles() -> None:
    print_title("37. ADVANCED PRINCIPLES")

    principles = [
        (
            "Constraint coupling",
            "Constraints interact rather than operating independently."
        ),
        (
            "Constraint migration",
            "Solving one constraint can create pressure in another."
        ),
        (
            "Bottleneck management",
            "The most limiting capacity can dominate system throughput."
        ),
        (
            "Marginal analysis",
            "Compare the incremental benefit of a decision with its incremental "
            "cost and risk."
        ),
        (
            "Feasibility before optimization",
            "Do not rank infeasible alternatives as if they were acceptable."
        ),
        (
            "Baseline integrity",
            "Controlled baselines preserve meaningful performance measurement."
        ),
        (
            "Uncertainty awareness",
            "Point estimates can conceal material variability."
        ),
        (
            "Quality as a system property",
            "Quality is affected by requirements, design, process, testing, "
            "resources, schedule pressure, and operating conditions."
        ),
        (
            "Lifecycle perspective",
            "The lowest project cost may not produce the lowest total lifecycle "
            "cost."
        ),
        (
            "Decision latency",
            "Slow stakeholder decisions can become schedule and resource "
            "constraints themselves."
        ),
    ]

    for principle, explanation in principles:
        print(f"\n{principle}:")
        print(f"  {explanation}")


# ============================================================================
# SECTION 38: FINAL KNOWLEDGE CHECK
# ============================================================================

def knowledge_check() -> None:
    print_title("38. KNOWLEDGE CHECK")

    questions = [
        (
            "What happens when scope increases while time and quality remain fixed?",
            "The project normally needs additional resources, higher cost, "
            "greater productivity, reduced flexibility, or some combination."
        ),
        (
            "What is the critical path?",
            "The longest dependency path determining the minimum project "
            "duration under the modeled assumptions."
        ),
        (
            "What is scope creep?",
            "Uncontrolled expansion of project work without corresponding "
            "approved adjustment."
        ),
        (
            "Why is quality a constraint?",
            "Because deliverables must satisfy defined requirements and "
            "acceptance conditions."
        ),
        (
            "Why can adding resources fail to solve a delay?",
            "Because coordination, onboarding, dependencies, or bottlenecks "
            "can limit the productivity gained."
        ),
        (
            "Why should hard constraints be treated differently from soft ones?",
            "A hard constraint defines feasibility; a soft constraint defines "
            "preference."
        ),
        (
            "What does CPI below 1 mean?",
            "Earned value is lower than actual cost, indicating unfavorable "
            "cost efficiency."
        ),
        (
            "What does SPI below 1 indicate in EVM?",
            "Earned value is below planned value, indicating progress is behind "
            "the planned value curve."
        ),
    ]

    for question, answer in questions:
        print(f"\nQ: {question}")
        print(f"A: {answer}")


# ============================================================================
# SECTION 39: MAIN PROGRAM
# ============================================================================

def main() -> None:
    """
    Execute the complete educational demonstration.

    Every section is independent enough to study separately while the
    integrated sequence builds a coherent understanding of project
    constraints.
    """
    explain_basic_terminology()
    demonstrate_constraint_triangle()
    demonstrate_constraint_priorities()
    demonstrate_time_constraints()
    demonstrate_schedule_compression()
    demonstrate_cost_constraints()
    classify_project_costs()
    demonstrate_scope_management()
    demonstrate_quality_constraints()
    demonstrate_cost_of_quality()
    demonstrate_resource_constraints()
    demonstrate_resource_leveling()
    demonstrate_constraint_interactions()
    demonstrate_change_control()
    demonstrate_tradeoff_scoring()
    demonstrate_hard_and_soft_constraints()
    demonstrate_feasibility_analysis()
    demonstrate_earned_value()
    demonstrate_forecasting()
    demonstrate_uncertainty()
    demonstrate_schedule_simulation()
    demonstrate_constraint_negotiation()
    demonstrate_progressive_elaboration()
    demonstrate_baseline_control()
    demonstrate_acceptance_criteria()
    demonstrate_escalation()
    demonstrate_capacity_planning()
    demonstrate_diminishing_returns()
    demonstrate_real_world_applications()
    demonstrate_edge_cases()
    demonstrate_common_mistakes()
    demonstrate_security_and_governance()
    demonstrate_constraint_records()
    run_assertion_tests()
    integrated_project_case()
    constraint_decision_framework()
    demonstrate_advanced_principles()
    knowledge_check()

    print_title("END OF PROJECT CONSTRAINTS STUDY SCRIPT")
    print(
        "The script has completed all demonstrations, calculations, "
        "simulations, and built-in tests."
    )


if __name__ == "__main__":
    main()
