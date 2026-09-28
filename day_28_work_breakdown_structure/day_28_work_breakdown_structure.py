"""
WORK BREAKDOWN STRUCTURE (WBS)
Breaking Work into Smaller Parts

A comprehensive standalone study and executable demonstration of Work Breakdown
Structure (WBS), progressing from fundamental concepts to advanced project
planning, validation, estimation, dependency analysis, scheduling, risk mapping,
resource planning, earned-value calculations, and quality checks.

The examples use a software-product project so that abstract WBS concepts can
be connected to realistic project-management decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple
import math
import statistics


# ============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# ============================================================================

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_subsection(title: str) -> None:
    print("\n" + "-" * 78)
    print(title)
    print("-" * 78)


print_section("1. WHAT IS A WORK BREAKDOWN STRUCTURE?")

print(
    """
A Work Breakdown Structure (WBS) is a hierarchical decomposition of the total
scope of a project into progressively smaller components.

The purpose is not simply to create a task list. A good WBS defines the complete
scope of work that must be delivered and organizes that scope into manageable
levels.

Typical hierarchy:

Project
  -> Major Deliverable
      -> Sub-deliverable
          -> Work Package
              -> Activity / Task

Important terms:

Project:
    The complete temporary effort being planned.

Deliverable:
    A measurable product, result, capability, or service produced by the project.

Work package:
    The lowest WBS component that is managed and estimated as a unit.

Activity:
    A specific action performed to produce a work-package result.

Scope:
    The total work required to produce the project's intended deliverables.

WBS dictionary:
    Supporting documentation that explains each WBS element, including scope,
    acceptance criteria, assumptions, exclusions, ownership, and estimates.

WBS code:
    A hierarchical identifier such as 1.2.3 that shows where an element sits
    within the WBS.

The central principle is the 100 percent rule:

    The WBS should represent 100 percent of the project's approved scope.

Child elements collectively describe the parent element. A parent should not
contain unrelated work, and required scope should not disappear between levels.
"""
)


# ============================================================================
# 2. BASIC WBS NODE MODEL
# ============================================================================

@dataclass
class WBSNode:
    """
    Represents one element of a Work Breakdown Structure.

    A node can be a project, deliverable, sub-deliverable, work package,
    or activity. The model intentionally keeps hierarchy separate from
    scheduling dependencies.
    """

    code: str
    name: str
    level: int
    node_type: str
    description: str = ""
    duration_days: float = 0.0
    cost: float = 0.0
    owner: str = ""
    parent_code: Optional[str] = None
    children: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        return not self.children


class WBS:
    """A hierarchical WBS container with validation and analytical methods."""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.nodes: Dict[str, WBSNode] = {}

    def add_node(self, node: WBSNode) -> None:
        if node.code in self.nodes:
            raise ValueError(f"Duplicate WBS code: {node.code}")

        if node.parent_code is not None:
            if node.parent_code not in self.nodes:
                raise ValueError(
                    f"Parent {node.parent_code} does not exist for {node.code}"
                )

            expected_level = self.nodes[node.parent_code].level + 1
            if node.level != expected_level:
                raise ValueError(
                    f"{node.code} has level {node.level}; "
                    f"expected {expected_level}"
                )

            self.nodes[node.parent_code].children.append(node.code)

        self.nodes[node.code] = node

    def get_root(self) -> WBSNode:
        roots = [
            node for node in self.nodes.values()
            if node.parent_code is None
        ]

        if len(roots) != 1:
            raise ValueError("A valid project WBS should have exactly one root.")

        return roots[0]

    def print_tree(self) -> None:
        """Display the WBS hierarchy using indentation."""

        root = self.get_root()

        def visit(code: str, prefix: str = "") -> None:
            node = self.nodes[code]
            print(
                f"{prefix}{node.code} | {node.name} "
                f"[{node.node_type}]"
            )

            for child_code in node.children:
                visit(child_code, prefix + "    ")

        visit(root.code)

    def descendants(self, code: str) -> List[WBSNode]:
        result = []

        def visit(current_code: str) -> None:
            for child_code in self.nodes[current_code].children:
                result.append(self.nodes[child_code])
                visit(child_code)

        visit(code)
        return result

    def leaves(self) -> List[WBSNode]:
        return [node for node in self.nodes.values() if node.is_leaf]

    def direct_children(self, code: str) -> List[WBSNode]:
        return [self.nodes[c] for c in self.nodes[code].children]

    def rollup_cost(self, code: str) -> float:
        """
        Roll up cost from leaves to a parent.

        If a parent has children, the child values are considered the source
        of truth. This prevents accidentally adding both parent and child
        estimates and double-counting them.
        """
        node = self.nodes[code]

        if node.is_leaf:
            return node.cost

        return sum(self.rollup_cost(child) for child in node.children)

    def rollup_duration(self, code: str) -> float:
        """
        Roll up duration for scope estimation.

        Duration is NOT generally additive for a real schedule because tasks
        can overlap. This method therefore represents scope effort aggregation
        rather than calendar duration. A separate scheduling engine is used
        later for dependency-aware calendar duration.
        """
        node = self.nodes[code]

        if node.is_leaf:
            return node.duration_days

        return sum(
            self.rollup_duration(child)
            for child in node.children
        )

    def find(self, text: str) -> List[WBSNode]:
        """Case-insensitive search by WBS code, name, or description."""
        query = text.lower()

        return [
            node
            for node in self.nodes.values()
            if query in node.code.lower()
            or query in node.name.lower()
            or query in node.description.lower()
        ]


# ============================================================================
# 3. BUILDING A PRACTICAL WBS
# ============================================================================

print_section("2. BUILDING A PRACTICAL SOFTWARE PROJECT WBS")

wbs = WBS("Enterprise Customer Portal")

wbs.add_node(
    WBSNode(
        code="1",
        name="Enterprise Customer Portal",
        level=1,
        node_type="Project",
        description="Complete customer-facing web platform."
    )
)

major_deliverables = [
    ("1.1", "Project Management", "Management and governance deliverables."),
    ("1.2", "User Experience", "Research, UX design, and interface design."),
    ("1.3", "Application Platform", "Core application capabilities."),
    ("1.4", "Security", "Security engineering and verification."),
    ("1.5", "Quality Assurance", "Testing and quality validation."),
    ("1.6", "Deployment", "Production deployment and operational readiness."),
]

for code, name, description in major_deliverables:
    wbs.add_node(
        WBSNode(
            code=code,
            name=name,
            level=2,
            node_type="Deliverable",
            description=description,
            parent_code="1"
        )
    )


# Project Management
wbs.add_node(WBSNode(
    "1.1.1", "Project Planning", 3, "Sub-deliverable",
    "Planning baseline and governance setup.", parent_code="1.1"
))
wbs.add_node(WBSNode(
    "1.1.2", "Stakeholder Management", 3, "Sub-deliverable",
    "Stakeholder identification and communication.", parent_code="1.1"
))
wbs.add_node(WBSNode(
    "1.1.3", "Progress Control", 3, "Sub-deliverable",
    "Status, metrics, and change control.", parent_code="1.1"
))

management_packages = [
    ("1.1.1.1", "Create Project Charter", 4, 2, 800),
    ("1.1.1.2", "Create Management Plan", 4, 3, 1200),
    ("1.1.2.1", "Identify Stakeholders", 4, 2, 600),
    ("1.1.2.2", "Create Communication Matrix", 4, 2, 500),
    ("1.1.3.1", "Weekly Status Reporting", 4, 20, 4000),
    ("1.1.3.2", "Change Control", 4, 10, 2500),
]

for code, name, level, duration, cost in management_packages:
    parent = ".".join(code.split(".")[:-1])
    wbs.add_node(WBSNode(
        code, name, level, "Work Package",
        duration_days=duration,
        cost=cost,
        parent_code=parent
    ))


# User Experience
wbs.add_node(WBSNode(
    "1.2.1", "User Research", 3, "Sub-deliverable",
    parent_code="1.2"
))
wbs.add_node(WBSNode(
    "1.2.2", "Interaction Design", 3, "Sub-deliverable",
    parent_code="1.2"
))
wbs.add_node(WBSNode(
    "1.2.3", "Visual Design", 3, "Sub-deliverable",
    parent_code="1.2"
))

ux_packages = [
    ("1.2.1.1", "Interview Users", 5, 5, 2000),
    ("1.2.1.2", "Analyze User Needs", 5, 4, 1800),
    ("1.2.2.1", "Create User Flows", 5, 4, 1600),
    ("1.2.2.2", "Create Wireframes", 5, 6, 2400),
    ("1.2.3.1", "Create Design System", 5, 7, 3500),
    ("1.2.3.2", "Create High-Fidelity Screens", 5, 8, 4200),
]

for code, name, level, duration, cost in ux_packages:
    parent = ".".join(code.split(".")[:-1])
    wbs.add_node(WBSNode(
        code, name, level, "Work Package",
        duration_days=duration,
        cost=cost,
        parent_code=parent
    ))


# Application Platform
application_subdeliverables = [
    ("1.3.1", "Authentication", "Identity and access capabilities."),
    ("1.3.2", "Customer Profile", "Customer information management."),
    ("1.3.3", "Dashboard", "Customer-facing dashboard."),
    ("1.3.4", "Notification Service", "Email and in-app notifications."),
]

for code, name, description in application_subdeliverables:
    wbs.add_node(WBSNode(
        code, name, 3, "Sub-deliverable",
        description=description,
        parent_code="1.3"
    ))

application_packages = [
    ("1.3.1.1", "Login and Logout", 5, 5, 4500),
    ("1.3.1.2", "Password Recovery", 5, 4, 3200),
    ("1.3.1.3", "Multi-Factor Authentication", 5, 7, 6500),
    ("1.3.2.1", "Profile API", 5, 6, 5200),
    ("1.3.2.2", "Profile Interface", 5, 5, 4100),
    ("1.3.3.1", "Dashboard API", 5, 7, 6200),
    ("1.3.3.2", "Dashboard Interface", 5, 7, 5800),
    ("1.3.4.1", "Email Notification Service", 5, 6, 5000),
    ("1.3.4.2", "In-App Notification Service", 5, 5, 4200),
]

for code, name, level, duration, cost in application_packages:
    parent = ".".join(code.split(".")[:-1])
    wbs.add_node(WBSNode(
        code, name, level, "Work Package",
        duration_days=duration,
        cost=cost,
        parent_code=parent
    ))


# Security
security_subdeliverables = [
    ("1.4.1", "Security Architecture"),
    ("1.4.2", "Application Security"),
    ("1.4.3", "Security Verification"),
]

for code, name in security_subdeliverables:
    wbs.add_node(WBSNode(
        code, name, 3, "Sub-deliverable", parent_code="1.4"
    ))

security_packages = [
    ("1.4.1.1", "Threat Modeling", 5, 5, 4000),
    ("1.4.1.2", "Security Requirements", 5, 4, 3000),
    ("1.4.2.1", "Input Validation Controls", 5, 6, 4500),
    ("1.4.2.2", "Authorization Controls", 5, 6, 5000),
    ("1.4.3.1", "Security Test Suite", 5, 7, 5500),
    ("1.4.3.2", "Vulnerability Assessment", 5, 6, 6500),
]

for code, name, level, duration, cost in security_packages:
    parent = ".".join(code.split(".")[:-1])
    wbs.add_node(WBSNode(
        code, name, level, "Work Package",
        duration_days=duration,
        cost=cost,
        parent_code=parent
    ))


# Quality Assurance
qa_subdeliverables = [
    ("1.5.1", "Test Planning"),
    ("1.5.2", "Functional Testing"),
    ("1.5.3", "Performance Testing"),
]

for code, name in qa_subdeliverables:
    wbs.add_node(WBSNode(
        code, name, 3, "Sub-deliverable", parent_code="1.5"
    ))

qa_packages = [
    ("1.5.1.1", "Test Strategy", 5, 3, 1800),
    ("1.5.1.2", "Test Cases", 5, 6, 3200),
    ("1.5.2.1", "Integration Testing", 5, 8, 6000),
    ("1.5.2.2", "System Testing", 5, 8, 6000),
    ("1.5.3.1", "Load Testing", 5, 5, 4000),
    ("1.5.3.2", "Performance Analysis", 5, 4, 3000),
]

for code, name, level, duration, cost in qa_packages:
    parent = ".".join(code.split(".")[:-1])
    wbs.add_node(WBSNode(
        code, name, level, "Work Package",
        duration_days=duration,
        cost=cost,
        parent_code=parent
    ))


# Deployment
deployment_subdeliverables = [
    ("1.6.1", "Infrastructure"),
    ("1.6.2", "Release Engineering"),
    ("1.6.3", "Operational Readiness"),
]

for code, name in deployment_subdeliverables:
    wbs.add_node(WBSNode(
        code, name, 3, "Sub-deliverable", parent_code="1.6"
    ))

deployment_packages = [
    ("1.6.1.1", "Production Infrastructure", 5, 5, 6000),
    ("1.6.1.2", "Monitoring Infrastructure", 5, 4, 3500),
    ("1.6.2.1", "CI/CD Pipeline", 5, 6, 5000),
    ("1.6.2.2", "Production Release", 5, 2, 2500),
    ("1.6.3.1", "Operations Runbook", 5, 4, 2200),
    ("1.6.3.2", "Production Readiness Review", 5, 2, 1500),
]

for code, name, level, duration, cost in deployment_packages:
    parent = ".".join(code.split(".")[:-1])
    wbs.add_node(WBSNode(
        code, name, level, "Work Package",
        duration_days=duration,
        cost=cost,
        parent_code=parent
    ))


print_subsection("WBS Hierarchy")
wbs.print_tree()


# ============================================================================
# 4. WBS STRUCTURING PRINCIPLES
# ============================================================================

print_section("3. CORE WBS PRINCIPLES")

principles = {
    "100 percent rule":
        "Children collectively represent the parent's complete scope.",
    "Deliverable orientation":
        "Decompose the project around outputs rather than arbitrary actions.",
    "Mutual exclusivity":
        "Avoid overlapping scope that causes double counting.",
    "Manageable work packages":
        "Work should become sufficiently specific to estimate and control.",
    "Progressive decomposition":
        "Break work down only as far as useful for planning and control.",
    "Stable scope baseline":
        "Approved scope should remain controlled through change management.",
    "WBS is not a schedule":
        "Hierarchy describes scope; dependencies and calendars describe schedule.",
    "WBS is not an organizational chart":
        "Hierarchy describes work, not reporting relationships.",
    "WBS is not merely a to-do list":
        "A WBS represents complete project scope and its deliverables."
}

for principle, meaning in principles.items():
    print(f"{principle}: {meaning}")


# ============================================================================
# 5. WBS LEVELS AND WORK PACKAGES
# ============================================================================

print_section("4. LEVELS AND WORK PACKAGES")

for node in sorted(wbs.nodes.values(), key=lambda n: tuple(map(int, n.code.split(".")))):
    print(
        f"{node.code:<8} Level={node.level} "
        f"Type={node.node_type:<16} Name={node.name}"
    )

print(
    """
A useful decomposition stops when further splitting no longer improves control.

A work package should generally be:

- clearly scoped,
- assignable,
- estimable,
- measurable,
- controllable,
- associated with acceptance criteria.

Decomposing too little creates vague work. Decomposing too much creates
administrative overhead and excessive tracking effort.
"""
)


# ============================================================================
# 6. COST ROLL-UP
# ============================================================================

print_section("5. COST ROLL-UP")

major_costs = {}

for node in wbs.direct_children("1"):
    major_costs[node.code] = wbs.rollup_cost(node.code)

for code, cost in major_costs.items():
    print(f"{code:<8} {wbs.nodes[code].name:<25} ${cost:,.2f}")

total_cost = wbs.rollup_cost("1")
print(f"\nTotal project cost baseline: ${total_cost:,.2f}")


# ============================================================================
# 7. EFFORT VS CALENDAR DURATION
# ============================================================================

print_section("6. EFFORT VERSUS CALENDAR DURATION")

total_effort = wbs.rollup_duration("1")

print(f"Total leaf-level estimated work: {total_effort:.1f} person-days")
print(
    """
This number is an effort aggregation, not necessarily the number of calendar
days required.

For example, two five-day work packages performed by two people can consume
10 person-days of effort while taking approximately five calendar days.

This distinction becomes essential when moving from WBS to scheduling.
"""
)


# ============================================================================
# 8. DEPENDENCY-AWARE SCHEDULING
# ============================================================================

print_section("7. DEPENDENCIES AND SCHEDULING")

# Dependencies are deliberately separate from the WBS hierarchy.
dependency_map = {
    "1.2.1.1": [],
    "1.2.1.2": ["1.2.1.1"],
    "1.2.2.1": ["1.2.1.2"],
    "1.2.2.2": ["1.2.2.1"],
    "1.2.3.1": ["1.2.2.2"],
    "1.2.3.2": ["1.2.3.1"],

    "1.3.1.1": ["1.2.2.2"],
    "1.3.1.2": ["1.3.1.1"],
    "1.3.1.3": ["1.3.1.1"],
    "1.3.2.1": ["1.2.2.2"],
    "1.3.2.2": ["1.3.2.1", "1.2.3.2"],
    "1.3.3.1": ["1.3.2.1"],
    "1.3.3.2": ["1.3.3.1", "1.2.3.2"],
    "1.3.4.1": ["1.3.1.1"],
    "1.3.4.2": ["1.3.1.1"],

    "1.4.1.1": [],
    "1.4.1.2": ["1.4.1.1"],
    "1.4.2.1": ["1.4.1.2"],
    "1.4.2.2": ["1.4.1.2"],
    "1.4.3.1": ["1.4.2.1", "1.4.2.2"],
    "1.4.3.2": ["1.4.3.1"],

    "1.5.1.1": [],
    "1.5.1.2": ["1.5.1.1"],
    "1.5.2.1": ["1.5.1.2", "1.3.2.2", "1.3.3.2"],
    "1.5.2.2": ["1.5.2.1"],
    "1.5.3.1": ["1.5.2.2"],
    "1.5.3.2": ["1.5.3.1"],

    "1.6.1.1": ["1.3.3.2"],
    "1.6.1.2": ["1.6.1.1"],
    "1.6.2.1": ["1.6.1.1"],
    "1.6.2.2": ["1.5.2.2", "1.4.3.2", "1.6.2.1"],
    "1.6.3.1": ["1.6.2.1"],
    "1.6.3.2": ["1.6.2.2", "1.6.3.1"],
}

for code, dependencies in dependency_map.items():
    wbs.nodes[code].dependencies = dependencies


def topological_sort(
    durations: Dict[str, float],
    dependencies: Dict[str, List[str]]
) -> List[str]:
    """Return tasks in dependency-safe order and detect cycles."""

    all_nodes = set(durations)
    indegree = {node: 0 for node in all_nodes}
    outgoing = defaultdict(list)

    for node, deps in dependencies.items():
        for dependency in deps:
            if dependency not in all_nodes:
                raise ValueError(
                    f"Unknown dependency {dependency} referenced by {node}"
                )
            indegree[node] += 1
            outgoing[dependency].append(node)

    queue = deque(
        sorted(node for node in all_nodes if indegree[node] == 0)
    )
    order = []

    while queue:
        current = queue.popleft()
        order.append(current)

        for successor in sorted(outgoing[current]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)

    if len(order) != len(all_nodes):
        raise ValueError("Dependency graph contains a cycle.")

    return order


leaf_durations = {
    node.code: node.duration_days
    for node in wbs.leaves()
}

leaf_dependencies = {
    code: dependency_map.get(code, [])
    for code in leaf_durations
}

schedule_order = topological_sort(leaf_durations, leaf_dependencies)

earliest_start: Dict[str, float] = {}
earliest_finish: Dict[str, float] = {}

for code in schedule_order:
    dependencies = leaf_dependencies[code]

    earliest_start[code] = (
        max(earliest_finish[dependency] for dependency in dependencies)
        if dependencies
        else 0.0
    )

    earliest_finish[code] = (
        earliest_start[code] + leaf_durations[code]
    )

project_duration = max(earliest_finish.values())

print(f"Dependency-aware project duration: {project_duration:.1f} calendar days")

for code in schedule_order:
    node = wbs.nodes[code]
    print(
        f"{code:<8} Start={earliest_start[code]:>5.1f} "
        f"Finish={earliest_finish[code]:>5.1f} "
        f"{node.name}"
    )


# ============================================================================
# 9. CRITICAL PATH
# ============================================================================

print_section("8. CRITICAL PATH")

latest_finish = {
    code: project_duration
    for code in leaf_durations
}
latest_start = {}

successors = defaultdict(list)

for task, dependencies in leaf_dependencies.items():
    for dependency in dependencies:
        successors[dependency].append(task)

for code in reversed(schedule_order):
    if successors[code]:
        latest_finish[code] = min(
            latest_start[successor]
            for successor in successors[code]
        )

    latest_start[code] = latest_finish[code] - leaf_durations[code]

float_values = {}

for code in leaf_durations:
    float_values[code] = latest_start[code] - earliest_start[code]

critical_tasks = [
    code for code in schedule_order
    if abs(float_values[code]) < 1e-9
]

print("Critical-path work packages:")

for code in critical_tasks:
    print(
        f"{code:<8} {wbs.nodes[code].name:<35} "
        f"Duration={leaf_durations[code]:.1f} days"
    )

print(
    """
Critical path is a schedule concept, not a WBS hierarchy concept.

A WBS identifies what must be delivered. Dependencies establish sequencing.
The critical path is then calculated from the resulting network.

A change to scope can change durations and dependencies, which can change
the critical path.
"""
)


# ============================================================================
# 10. WBS VALIDATION
# ============================================================================

print_section("9. WBS VALIDATION")

def validate_wbs(wbs_object: WBS) -> List[str]:
    """Perform structural and scope-oriented validation checks."""

    errors = []

    try:
        root = wbs_object.get_root()
        if root.level != 1:
            errors.append("Root should normally be level 1.")
    except ValueError as error:
        errors.append(str(error))

    for code, node in wbs_object.nodes.items():
        if node.parent_code is not None:
            if node.parent_code not in wbs_object.nodes:
                errors.append(
                    f"{code}: missing parent {node.parent_code}."
                )

        if node.level < 1:
            errors.append(f"{code}: invalid level.")

        if node.is_leaf:
            if node.duration_days < 0:
                errors.append(f"{code}: negative duration.")
            if node.cost < 0:
                errors.append(f"{code}: negative cost.")

        if node.node_type == "Work Package" and not node.is_leaf:
            errors.append(
                f"{code}: work package should not contain children."
            )

    return errors


validation_errors = validate_wbs(wbs)

if validation_errors:
    for error in validation_errors:
        print("ERROR:", error)
else:
    print("WBS validation passed.")


# ============================================================================
# 11. COMMON WBS MISTAKES
# ============================================================================

print_section("10. COMMON WBS MISTAKES")

mistakes = [
    (
        "Using vague items",
        "Example: 'Development'.",
        "Use measurable deliverables or work packages such as 'Profile API'."
    ),
    (
        "Mixing scope and schedule",
        "Example: putting 'Monday' or 'Sprint 4' into the WBS hierarchy.",
        "Keep dates and sequencing in the schedule."
    ),
    (
        "Double-counting scope",
        "The same work appears under two branches.",
        "Assign each scope component to one logical WBS location."
    ),
    (
        "Missing support work",
        "Security, testing, deployment, documentation, or governance disappears.",
        "Apply the 100 percent rule."
    ),
    (
        "Over-decomposition",
        "Every tiny action becomes a separately tracked item.",
        "Stop when further decomposition adds little control value."
    ),
    (
        "Under-decomposition",
        "Large vague components cannot be estimated or assigned.",
        "Continue decomposition until work packages are manageable."
    ),
    (
        "Organizational decomposition",
        "The WBS becomes a list of departments.",
        "Structure around project scope and deliverables."
    ),
    (
        "No acceptance criteria",
        "The team cannot objectively determine completion.",
        "Define measurable completion conditions."
    )
]

for mistake, problem, remedy in mistakes:
    print(f"\n{mistake}")
    print(f"  Problem: {problem}")
    print(f"  Better approach: {remedy}")


# ============================================================================
# 12. EDGE CASES
# ============================================================================

print_section("11. EDGE CASES AND EXCEPTIONS")

print(
    """
1. A parent with no children may be legitimate if it is itself a work package.

2. A deliverable should normally be decomposed when its scope is too broad
   to estimate, assign, or verify.

3. Parallel work does not require separate top-level WBS branches merely
   because tasks happen simultaneously.

4. A single work package can depend on several other work packages.

5. Two WBS branches may use the same person or resource. This is a resource
   scheduling issue rather than a reason to duplicate the scope.

6. Scope changes should not silently modify the baseline. Approved changes
   should be incorporated through the project's change-control process.

7. A dependency cycle is a scheduling-model error. A hierarchy can exist
   without dependencies, but a dependency network cannot contain circular
   precedence if it is to be topologically scheduled.

8. Zero-duration milestones are useful schedule events but are usually better
   represented as milestones in the schedule rather than ordinary WBS
   work packages.

9. Estimates should preserve their unit. Cost, effort, duration, and quantity
   are different measurements and should not be mixed.
"""
)


# ============================================================================
# 13. ESTIMATION TECHNIQUES
# ============================================================================

print_section("12. ESTIMATION TECHNIQUES")

def three_point_estimate(
    optimistic: float,
    most_likely: float,
    pessimistic: float
) -> Tuple[float, float]:
    """
    PERT-style expected duration and approximate variance.

    Expected value = (O + 4M + P) / 6
    Variance = ((P - O) / 6)^2
    """
    if not optimistic <= most_likely <= pessimistic:
        raise ValueError(
            "Expected ordering is optimistic <= most likely <= pessimistic."
        )

    expected = (
        optimistic + 4 * most_likely + pessimistic
    ) / 6

    variance = ((pessimistic - optimistic) / 6) ** 2

    return expected, variance


o, m, p = 4, 7, 13
expected, variance = three_point_estimate(o, m, p)

print(f"Optimistic estimate: {o} days")
print(f"Most likely estimate: {m} days")
print(f"Pessimistic estimate: {p} days")
print(f"PERT expected estimate: {expected:.2f} days")
print(f"Approximate variance: {variance:.2f}")


def analogous_estimate(similar_project_duration: float, adjustment: float) -> float:
    """Estimate based on a comparable historical project."""
    if similar_project_duration < 0:
        raise ValueError("Duration cannot be negative.")

    if adjustment < -1:
        raise ValueError("Adjustment cannot reduce duration below zero.")

    return similar_project_duration * (1 + adjustment)


print(
    "Analogous estimate:",
    analogous_estimate(100, 0.15),
    "days"
)


def bottom_up_estimate(work_package_estimates: List[float]) -> float:
    """Bottom-up estimate: sum detailed work-package estimates."""
    if any(value < 0 for value in work_package_estimates):
        raise ValueError("Estimates cannot be negative.")

    return sum(work_package_estimates)


print(
    "Bottom-up estimate:",
    bottom_up_estimate([4, 6, 8, 5, 7]),
    "person-days"
)


# ============================================================================
# 14. RISK-ADJUSTED ESTIMATION
# ============================================================================

print_section("13. RISK-ADJUSTED ESTIMATION")

@dataclass
class Risk:
    name: str
    probability: float
    impact_cost: float
    mitigation_cost: float = 0.0

    @property
    def expected_monetary_value(self) -> float:
        return self.probability * self.impact_cost


risks = [
    Risk("Third-party API instability", 0.25, 10000, 1500),
    Risk("Security remediation", 0.20, 15000, 2500),
    Risk("Performance rework", 0.30, 8000, 1200),
]

total_emv = 0.0

for risk in risks:
    emv = risk.expected_monetary_value
    total_emv += emv

    print(
        f"{risk.name:<30} "
        f"Probability={risk.probability:.0%} "
        f"EMV=${emv:,.2f}"
    )

print(f"Total expected risk exposure: ${total_emv:,.2f}")


# ============================================================================
# 15. RESOURCE ASSIGNMENT
# ============================================================================

print_section("14. RESOURCE PLANNING")

@dataclass
class Resource:
    name: str
    role: str
    capacity_percent: float
    daily_cost: float

    def validate(self) -> None:
        if not 0 < self.capacity_percent <= 100:
            raise ValueError(
                "Capacity must be greater than 0 and no greater than 100."
            )

        if self.daily_cost < 0:
            raise ValueError("Daily cost cannot be negative.")


resources = [
    Resource("Asha", "Project Manager", 80, 450),
    Resource("Ravi", "Backend Engineer", 100, 650),
    Resource("Meera", "Frontend Engineer", 100, 600),
    Resource("Kabir", "Security Engineer", 60, 700),
    Resource("Neha", "QA Engineer", 100, 500),
]

for resource in resources:
    resource.validate()
    print(
        f"{resource.name:<10} "
        f"{resource.role:<22} "
        f"Capacity={resource.capacity_percent:>3.0f}% "
        f"Daily cost=${resource.daily_cost:,.0f}"
    )


# ============================================================================
# 16. SCOPE BASELINE AND CHANGE CONTROL
# ============================================================================

print_section("15. SCOPE BASELINE AND CHANGE CONTROL")

@dataclass
class ChangeRequest:
    identifier: str
    description: str
    estimated_cost: float
    estimated_duration_days: float
    reason: str
    status: str = "Proposed"


change = ChangeRequest(
    identifier="CR-001",
    description="Add enterprise single sign-on",
    estimated_cost=12000,
    estimated_duration_days=8,
    reason="New customer requirement"
)

print(f"Change request: {change.identifier}")
print(f"Description: {change.description}")
print(f"Estimated cost impact: ${change.estimated_cost:,.2f}")
print(f"Estimated duration impact: {change.estimated_duration_days} days")
print(f"Status: {change.status}")

print(
    """
A change request should be evaluated against scope, schedule, cost, quality,
resources, security, dependencies, and operational effects before approval.

The key distinction is:

    Proposed scope != approved baseline scope

An approved change becomes part of the controlled project scope. An unapproved
request should not silently be inserted into the baseline.
"""
)


# ============================================================================
# 17. WBS DICTIONARY
# ============================================================================

print_section("16. WBS DICTIONARY")

dictionary_entry = {
    "WBS Code": "1.3.1.3",
    "Name": "Multi-Factor Authentication",
    "Description": (
        "Implement an additional authentication factor for protected "
        "customer accounts."
    ),
    "Owner": "Security Engineer",
    "Inputs": [
        "Security requirements",
        "Identity architecture"
    ],
    "Outputs": [
        "MFA implementation",
        "Configuration documentation"
    ],
    "Acceptance Criteria": [
        "Second factor is required for configured users.",
        "Recovery behavior is documented.",
        "Automated security tests pass."
    ],
    "Estimated Duration": "7 days",
    "Estimated Cost": "$6,500",
    "Dependencies": [
        "1.3.1.1 Login and Logout"
    ],
    "Exclusions": [
        "Third-party identity-provider procurement"
    ]
}

for key, value in dictionary_entry.items():
    print(f"{key}: {value}")


# ============================================================================
# 18. PERFORMANCE AND COMPLEXITY
# ============================================================================

print_section("17. PERFORMANCE CONSIDERATIONS")

print(
    """
For a WBS containing N nodes:

Tree traversal:
    O(N)

Searching every node by text:
    O(N) per search.

Cost roll-up:
    O(N) when each node is visited once.

Dependency topological sorting:
    O(V + E)
    where V = number of work packages and E = dependency relationships.

Critical-path calculation:
    O(V + E) after the dependency graph has been constructed.

For very large portfolios, indexes can be introduced for:
    - WBS code lookup,
    - owner lookup,
    - status lookup,
    - deliverable type,
    - project,
    - cost center.

The central optimization principle is to avoid repeatedly traversing an
unchanged hierarchy when the same roll-up can be cached.
"""
)


# ============================================================================
# 19. ADVANCED: CACHED ROLL-UP
# ============================================================================

print_subsection("Cached Roll-Up Example")

class CachedWBS(WBS):
    """WBS variant that caches computed roll-up costs."""

    def __init__(self, project_name: str):
        super().__init__(project_name)
        self._cost_cache: Dict[str, float] = {}

    def rollup_cost(self, code: str) -> float:
        if code in self._cost_cache:
            return self._cost_cache[code]

        value = super().rollup_cost(code)
        self._cost_cache[code] = value
        return value

    def invalidate_cost_cache(self) -> None:
        self._cost_cache.clear()


cached_wbs = CachedWBS("Cached Example")

cached_wbs.add_node(
    WBSNode("1", "Example Project", 1, "Project")
)
cached_wbs.add_node(
    WBSNode("1.1", "Deliverable", 2, "Deliverable", parent_code="1")
)
cached_wbs.add_node(
    WBSNode(
        "1.1.1",
        "Work Package A",
        3,
        "Work Package",
        cost=1000,
        parent_code="1.1"
    )
)
cached_wbs.add_node(
    WBSNode(
        "1.1.2",
        "Work Package B",
        3,
        "Work Package",
        cost=1500,
        parent_code="1.1"
    )
)

print("First calculation:", cached_wbs.rollup_cost("1"))
print("Cached calculation:", cached_wbs.rollup_cost("1"))


# ============================================================================
# 20. SECURITY CONSIDERATIONS
# ============================================================================

print_section("18. SECURITY CONSIDERATIONS")

print(
    """
A WBS may contain sensitive project information, including:

- internal project names,
- employee assignments,
- budgets,
- security work,
- vulnerabilities,
- infrastructure plans,
- customer requirements.

Therefore, production WBS systems should consider:

1. Authentication
   Only authorized users should access project data.

2. Authorization
   Users should receive the minimum access required for their responsibilities.

3. Auditability
   Changes to baseline scope should be traceable.

4. Input validation
   Codes, costs, dates, dependencies, and status values should be validated.

5. Data protection
   Sensitive project information should be encrypted where appropriate.

6. Change integrity
   Approved baselines should not be silently modified.

7. Dependency validation
   Circular or unknown dependencies should be rejected.

8. Export controls
   Reports should avoid exposing sensitive information to unauthorized users.
"""
)


# ============================================================================
# 21. QUALITY CHECKLIST
# ============================================================================

print_section("19. WBS QUALITY CHECKLIST")

checklist = [
    "Does the WBS represent the complete approved project scope?",
    "Is there one clear project root?",
    "Are parent-child relationships logically consistent?",
    "Are deliverables measurable?",
    "Are work packages assignable?",
    "Can each work package be estimated?",
    "Are acceptance criteria defined?",
    "Is scope duplicated anywhere?",
    "Is unrelated scope hidden in another branch?",
    "Are testing and quality activities represented?",
    "Are deployment and operational requirements represented?",
    "Are security requirements represented where relevant?",
    "Are cost roll-ups traceable?",
    "Are schedule dependencies maintained separately?",
    "Are change requests controlled?",
    "Can the WBS be understood by stakeholders and delivery teams?"
]

for number, item in enumerate(checklist, start=1):
    print(f"{number:02d}. [ ] {item}")


# ============================================================================
# 22. PRACTICAL COMPARISON: WBS VS OTHER PLANNING STRUCTURES
# ============================================================================

print_section("20. WBS VERSUS RELATED STRUCTURES")

comparison = [
    ("WBS", "Scope hierarchy", "What must be delivered?"),
    ("Schedule", "Time and dependency model", "When can work happen?"),
    ("Organization chart", "People hierarchy", "Who reports to whom?"),
    ("RACI matrix", "Responsibility model", "Who is responsible/accountable?"),
    ("Risk register", "Uncertainty register", "What could affect objectives?"),
    ("Product backlog", "Prioritized product work", "What product work should be prioritized?"),
    ("Roadmap", "Strategic timeline", "What outcomes are planned over time?"),
]

for structure, purpose, question in comparison:
    print(f"{structure:<22} | {purpose:<28} | {question}")


# ============================================================================
# 23. ADVANCED DESIGN: TRACEABILITY
# ============================================================================

print_section("21. REQUIREMENT-TO-WBS TRACEABILITY")

requirements = {
    "REQ-001": ["1.3.1.1", "1.3.1.2", "1.3.1.3"],
    "REQ-002": ["1.3.2.1", "1.3.2.2"],
    "REQ-003": ["1.4.2.1", "1.4.2.2"],
    "REQ-004": ["1.5.2.1", "1.5.2.2"],
}

for requirement, work_packages in requirements.items():
    print(f"{requirement}:")
    for work_package in work_packages:
        print(
            f"    -> {work_package}: "
            f"{wbs.nodes[work_package].name}"
        )

print(
    """
Traceability connects requirements to deliverables and work packages.

A useful traceability chain is:

Requirement
    -> WBS deliverable
        -> Work package
            -> Activity
                -> Test
                    -> Acceptance evidence

This reduces the chance that an approved requirement exists without planned
implementation or verification work.
"""
)


# ============================================================================
# 24. ADVANCED DESIGN: COMPLETENESS ANALYSIS
# ============================================================================

print_section("22. COMPLETENESS ANALYSIS")

required_domains = {
    "Project Management": "1.1",
    "User Experience": "1.2",
    "Application Platform": "1.3",
    "Security": "1.4",
    "Quality Assurance": "1.5",
    "Deployment": "1.6",
}

for domain, code in required_domains.items():
    exists = code in wbs.nodes
    child_count = len(wbs.nodes[code].children) if exists else 0

    print(
        f"{domain:<24} "
        f"Present={exists!s:<5} "
        f"Children={child_count}"
    )


# ============================================================================
# 25. MONTE CARLO-STYLE DURATION SIMULATION
# ============================================================================

print_section("23. PROBABILISTIC ESTIMATION")

def triangular_sample(
    low: float,
    mode: float,
    high: float,
    random_value: float
) -> float:
    """
    Deterministic implementation of inverse triangular distribution sampling.

    random_value is expected to be in [0, 1].
    """
    if not low <= mode <= high:
        raise ValueError("Require low <= mode <= high.")

    if not 0 <= random_value <= 1:
        raise ValueError("Random value must be between 0 and 1.")

    if low == high:
        return low

    split = (mode - low) / (high - low)

    if random_value < split:
        return low + math.sqrt(
            random_value * (high - low) * (mode - low)
        )

    return high - math.sqrt(
        (1 - random_value) * (high - low) * (high - mode)
    )


sample_inputs = [0.05, 0.20, 0.50, 0.80, 0.95]

for value in sample_inputs:
    sampled = triangular_sample(5, 8, 15, value)
    print(f"Probability={value:.2f} -> Estimated duration={sampled:.2f} days")

print(
    """
Probabilistic estimation recognizes that estimates are uncertain.

In a production Monte Carlo simulation, thousands of iterations would sample
uncertain durations and evaluate the resulting project completion distribution.

The result is not a single deterministic date. It is a probability distribution
from which planning confidence levels can be selected.
"""
)


# ============================================================================
# 26. EARNED VALUE MANAGEMENT CONNECTION
# ============================================================================

print_section("24. WBS AND EARNED VALUE MANAGEMENT")

@dataclass
class EarnedValueMetrics:
    planned_value: float
    earned_value: float
    actual_cost: float

    @property
    def cost_variance(self) -> float:
        return self.earned_value - self.actual_cost

    @property
    def schedule_variance(self) -> float:
        return self.earned_value - self.planned_value

    @property
    def cost_performance_index(self) -> float:
        return (
            self.earned_value / self.actual_cost
            if self.actual_cost
            else float("inf")
        )

    @property
    def schedule_performance_index(self) -> float:
        return (
            self.earned_value / self.planned_value
            if self.planned_value
            else float("inf")
        )


ev = EarnedValueMetrics(
    planned_value=50000,
    earned_value=45000,
    actual_cost=48000
)

print(f"PV = ${ev.planned_value:,.2f}")
print(f"EV = ${ev.earned_value:,.2f}")
print(f"AC = ${ev.actual_cost:,.2f}")
print(f"CV = ${ev.cost_variance:,.2f}")
print(f"SV = ${ev.schedule_variance:,.2f}")
print(f"CPI = {ev.cost_performance_index:.3f}")
print(f"SPI = {ev.schedule_performance_index:.3f}")

print(
    """
WBS elements can provide the scope structure against which planned value,
earned value, and actual cost are collected.

This creates a traceable relationship between:
    WBS -> budget -> schedule -> progress -> performance measurement
"""
)


# ============================================================================
# 27. AUTOMATED QUALITY GATES
# ============================================================================

print_section("25. AUTOMATED QUALITY GATES")

def quality_gate(wbs_object: WBS) -> Dict[str, bool]:
    root = wbs_object.get_root()
    leaf_nodes = wbs_object.leaves()

    return {
        "single_root":
            sum(
                1
                for node in wbs_object.nodes.values()
                if node.parent_code is None
            ) == 1,

        "no_negative_cost":
            all(node.cost >= 0 for node in leaf_nodes),

        "no_negative_duration":
            all(node.duration_days >= 0 for node in leaf_nodes),

        "work_packages_are_leaves":
            all(
                node.node_type != "Work Package" or node.is_leaf
                for node in wbs_object.nodes.values()
            ),

        "root_is_level_one":
            root.level == 1,

        "all_parents_exist":
            all(
                node.parent_code is None
                or node.parent_code in wbs_object.nodes
                for node in wbs_object.nodes.values()
            )
    }


quality_results = quality_gate(wbs)

for check, passed in quality_results.items():
    print(f"{check:<32}: {'PASS' if passed else 'FAIL'}")


# ============================================================================
# 28. MINI EXERCISE WITH COMPLETE SOLUTION
# ============================================================================

print_section("26. MINI PRACTICE EXAMPLE")

exercise = {
    "Project": "Online Appointment Platform",
    "Level 2 Deliverables": [
        "Patient Management",
        "Appointment Management",
        "Notifications",
        "Testing",
        "Deployment"
    ]
}

print("Project:", exercise["Project"])
print("Possible Level-2 deliverables:")

for item in exercise["Level 2 Deliverables"]:
    print("  -", item)

print(
    """
A reasonable decomposition of Appointment Management could be:

Appointment Management
    -> Availability
        -> Provider availability API
        -> Availability interface
    -> Booking
        -> Create appointment
        -> Reschedule appointment
        -> Cancel appointment
    -> Confirmation
        -> Booking confirmation
        -> Calendar integration

The important reasoning is not the exact number of levels. The important
questions are:

1. Does the decomposition cover the complete scope?
2. Are sibling elements mutually understandable?
3. Can each work package be estimated?
4. Can each work package be assigned?
5. Can completion be objectively verified?
6. Can progress and cost be tracked?
"""
)


# ============================================================================
# 29. FINAL PROGRAMMATIC REPORT
# ============================================================================

print_section("27. PROGRAMMATIC WBS REPORT")

leaf_nodes = wbs.leaves()

total_leaf_cost = sum(node.cost for node in leaf_nodes)
average_leaf_cost = (
    statistics.mean(node.cost for node in leaf_nodes)
    if leaf_nodes
    else 0
)

print(f"Project: {wbs.project_name}")
print(f"Total WBS nodes: {len(wbs.nodes)}")
print(f"Work packages: {len(leaf_nodes)}")
print(f"Major deliverables: {len(wbs.direct_children('1'))}")
print(f"Total budget: ${total_leaf_cost:,.2f}")
print(f"Average work-package budget: ${average_leaf_cost:,.2f}")
print(f"Dependency-aware duration: {project_duration:.1f} days")
print(f"Critical work packages: {len(critical_tasks)}")
print(f"Risk expected monetary value: ${total_emv:,.2f}")

print(
    """
Key implementation distinction:

WBS hierarchy:
    answers "What belongs to the project?"

Dependency graph:
    answers "What must happen before what?"

Resource model:
    answers "Who or what capacity is available?"

Cost model:
    answers "How much does the planned scope cost?"

Schedule:
    answers "When can the work be performed?"

Risk model:
    answers "What uncertainty can affect the plan?"

These structures can be integrated, but they should not be confused with
one another. Keeping their responsibilities separate produces clearer and
more maintainable project-control systems.
"""
)

print_section("28. END OF WBS STUDY PROGRAM")

print(
    "The complete example demonstrates decomposition, work packages, "
    "roll-up, dependencies, scheduling, critical path, estimation, "
    "risk, resources, traceability, validation, and performance analysis."
)
