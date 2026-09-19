"""
Stakeholder Identification: A comprehensive practical study program.

This standalone script teaches stakeholder identification from beginner to
advanced level through executable examples.

Core ideas demonstrated:
- Stakeholder definitions and terminology
- Internal and external stakeholders
- Primary, secondary, direct, indirect, and regulatory stakeholders
- Stakeholder discovery techniques
- Stakeholder registers
- Stakeholder mapping
- Power-interest analysis
- Influence-impact analysis
- Salience analysis
- RACI and responsibility relationships
- Stakeholder prioritization
- Communication requirements
- Conflict and dependency analysis
- Risk-oriented stakeholder analysis
- Scoring models and their limitations
- Change management
- Dynamic stakeholder analysis
- Validation and data-quality checks
- Scenario analysis
- Graph-based relationship analysis
- Network centrality
- Sensitivity analysis
- Audit trails
- Practical project governance

The examples use only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from statistics import mean
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
import json
import math
import re


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL TERMINOLOGY
# ---------------------------------------------------------------------------

class StakeholderType(Enum):
    INTERNAL = "Internal"
    EXTERNAL = "External"


class RelationshipType(Enum):
    SUPPORTS = "supports"
    OPPOSES = "opposes"
    DEPENDS_ON = "depends_on"
    INFLUENCES = "influences"
    REPORTS_TO = "reports_to"
    COLLABORATES_WITH = "collaborates_with"


class EngagementLevel(Enum):
    UNAWARE = "Unaware"
    RESISTANT = "Resistant"
    NEUTRAL = "Neutral"
    SUPPORTIVE = "Supportive"
    LEADING = "Leading"


@dataclass
class Stakeholder:
    """
    A stakeholder is a person, group, organization, or other entity that can
    affect, be affected by, or perceive itself to be affected by a decision,
    activity, project, product, or change.
    """

    stakeholder_id: str
    name: str
    stakeholder_type: StakeholderType
    role: str
    organization: str
    interests: List[str]
    power: float
    interest: float
    influence: float
    impact: float
    legitimacy: float = 1.0
    urgency: float = 1.0
    current_engagement: EngagementLevel = EngagementLevel.NEUTRAL
    desired_engagement: EngagementLevel = EngagementLevel.SUPPORTIVE
    communication_frequency: str = "Monthly"
    notes: str = ""

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.stakeholder_id.strip():
            raise ValueError("Stakeholder ID cannot be empty.")
        if not self.name.strip():
            raise ValueError("Stakeholder name cannot be empty.")
        if not 0 <= self.power <= 10:
            raise ValueError("Power must be between 0 and 10.")
        if not 0 <= self.interest <= 10:
            raise ValueError("Interest must be between 0 and 10.")
        if not 0 <= self.influence <= 10:
            raise ValueError("Influence must be between 0 and 10.")
        if not 0 <= self.impact <= 10:
            raise ValueError("Impact must be between 0 and 10.")
        if not 0 <= self.legitimacy <= 1:
            raise ValueError("Legitimacy must be between 0 and 1.")
        if not 0 <= self.urgency <= 1:
            raise ValueError("Urgency must be between 0 and 1.")

    @property
    def power_interest_score(self) -> float:
        return self.power * self.interest

    @property
    def influence_impact_score(self) -> float:
        return self.influence * self.impact

    @property
    def salience_score(self) -> float:
        """
        A simplified salience model.

        Classical stakeholder salience commonly discusses power,
        legitimacy, and urgency as attributes. This numerical model is an
        educational operationalization, not a universal standard.
        """
        return self.power * self.legitimacy * self.urgency

    def power_interest_category(self) -> str:
        high_power = self.power >= 5
        high_interest = self.interest >= 5

        if high_power and high_interest:
            return "Manage closely"
        if high_power and not high_interest:
            return "Keep satisfied"
        if not high_power and high_interest:
            return "Keep informed"
        return "Monitor"

    def engagement_gap(self) -> int:
        order = {
            EngagementLevel.UNAWARE: 0,
            EngagementLevel.RESISTANT: 1,
            EngagementLevel.NEUTRAL: 2,
            EngagementLevel.SUPPORTIVE: 3,
            EngagementLevel.LEADING: 4,
        }
        return order[self.desired_engagement] - order[self.current_engagement]


@dataclass
class Relationship:
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float = 1.0
    description: str = ""

    def __post_init__(self) -> None:
        if not 0 < self.strength <= 1:
            raise ValueError("Relationship strength must be greater than 0 and <= 1.")


@dataclass
class StakeholderRegister:
    stakeholders: Dict[str, Stakeholder] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)

    def add(self, stakeholder: Stakeholder) -> None:
        if stakeholder.stakeholder_id in self.stakeholders:
            raise ValueError(
                f"Duplicate stakeholder ID: {stakeholder.stakeholder_id}"
            )
        self.stakeholders[stakeholder.stakeholder_id] = stakeholder

    def get(self, stakeholder_id: str) -> Stakeholder:
        try:
            return self.stakeholders[stakeholder_id]
        except KeyError as exc:
            raise KeyError(f"Unknown stakeholder: {stakeholder_id}") from exc

    def add_relationship(self, relationship: Relationship) -> None:
        self.get(relationship.source_id)
        self.get(relationship.target_id)
        self.relationships.append(relationship)

    def validate_relationships(self) -> List[str]:
        errors: List[str] = []
        for relationship in self.relationships:
            if relationship.source_id == relationship.target_id:
                errors.append(
                    f"Self-relationship detected for {relationship.source_id}."
                )
        return errors

    def internal(self) -> List[Stakeholder]:
        return [
            stakeholder
            for stakeholder in self.stakeholders.values()
            if stakeholder.stakeholder_type == StakeholderType.INTERNAL
        ]

    def external(self) -> List[Stakeholder]:
        return [
            stakeholder
            for stakeholder in self.stakeholders.values()
            if stakeholder.stakeholder_type == StakeholderType.EXTERNAL
        ]


# ---------------------------------------------------------------------------
# 2. BEGINNER EXAMPLE
# ---------------------------------------------------------------------------

def beginner_example() -> None:
    """
    A simple stakeholder list.

    At the identification stage, the goal is not yet to decide exactly how
    every stakeholder will be managed. First establish who may matter and why.
    """
    stakeholders = [
        ("Project sponsor", "Funds and authorizes the project"),
        ("Project manager", "Coordinates delivery"),
        ("End users", "Use the resulting product"),
        ("Customers", "Receive the product or service"),
        ("Regulator", "Defines or enforces applicable requirements"),
        ("Supplier", "Provides external goods or services"),
    ]

    print("\nBEGINNER EXAMPLE")
    for name, reason in stakeholders:
        print(f"- {name}: {reason}")


# ---------------------------------------------------------------------------
# 3. IDENTIFICATION TECHNIQUES
# ---------------------------------------------------------------------------

def brainstorm_stakeholders(context: str) -> List[str]:
    """
    A simple rule-based brainstorming assistant.

    Real stakeholder discovery normally combines interviews, workshops,
    documentation review, organizational analysis, regulatory analysis,
    customer research, process analysis, and expert judgment.
    """
    context_lower = context.lower()
    candidates: Set[str] = set()

    candidates.update(
        {
            "Project sponsor",
            "Project manager",
            "Project team",
            "End users",
            "Customers",
            "Senior management",
            "Finance",
            "Legal",
            "IT/security",
            "Suppliers",
        }
    )

    if any(word in context_lower for word in ["bank", "payment", "finance"]):
        candidates.update({"Financial regulator", "Payment processor", "Auditor"})

    if any(word in context_lower for word in ["health", "hospital", "medical"]):
        candidates.update(
            {"Patients", "Clinicians", "Healthcare regulator", "Privacy officer"}
        )

    if any(word in context_lower for word in ["school", "education", "student"]):
        candidates.update({"Students", "Teachers", "Parents", "Education authority"})

    if any(word in context_lower for word in ["cloud", "software", "app", "platform"]):
        candidates.update({"Cloud provider", "System administrator", "Data protection officer"})

    return sorted(candidates)


def stakeholder_identification_questions() -> List[str]:
    return [
        "Who funds, sponsors, owns, approves, or governs the initiative?",
        "Who performs work affected by the initiative?",
        "Who uses the product, service, or process?",
        "Who receives direct or indirect benefits?",
        "Who bears costs, risks, disruption, or operational burden?",
        "Who can approve, block, delay, or materially change the initiative?",
        "Who supplies critical resources or dependencies?",
        "Who establishes legal, regulatory, contractual, or compliance requirements?",
        "Who controls important data, infrastructure, or intellectual property?",
        "Who represents affected communities or vulnerable groups?",
        "Who can influence public perception or organizational reputation?",
        "Who becomes important after a major change in scope or operating model?",
    ]


# ---------------------------------------------------------------------------
# 4. SAMPLE PROJECT: DIGITAL PUBLIC-SERVICE PORTAL
# ---------------------------------------------------------------------------

def build_sample_register() -> StakeholderRegister:
    register = StakeholderRegister()

    sample_stakeholders = [
        Stakeholder(
            "S01",
            "Executive Sponsor",
            StakeholderType.INTERNAL,
            "Sponsor",
            "Public Service Department",
            ["Strategic outcomes", "Budget", "Political accountability"],
            9,
            7,
            9,
            8,
            notes="Authorizes major decisions.",
        ),
        Stakeholder(
            "S02",
            "Project Manager",
            StakeholderType.INTERNAL,
            "Project Manager",
            "Public Service Department",
            ["Delivery", "Schedule", "Risk", "Coordination"],
            7,
            10,
            8,
            9,
            current_engagement=EngagementLevel.LEADING,
            desired_engagement=EngagementLevel.LEADING,
            communication_frequency="Weekly",
        ),
        Stakeholder(
            "S03",
            "IT Operations",
            StakeholderType.INTERNAL,
            "Operations",
            "Public Service Department",
            ["Reliability", "Maintainability", "Security"],
            7,
            8,
            8,
            9,
            communication_frequency="Weekly",
        ),
        Stakeholder(
            "S04",
            "Frontline Employees",
            StakeholderType.INTERNAL,
            "Service Staff",
            "Public Service Department",
            ["Usability", "Workload", "Training"],
            5,
            9,
            6,
            9,
            communication_frequency="Biweekly",
        ),
        Stakeholder(
            "S05",
            "Citizens",
            StakeholderType.EXTERNAL,
            "End Users",
            "Public",
            ["Accessibility", "Speed", "Privacy", "Service quality"],
            5,
            10,
            7,
            10,
            communication_frequency="Monthly",
        ),
        Stakeholder(
            "S06",
            "Technology Supplier",
            StakeholderType.EXTERNAL,
            "Vendor",
            "External Supplier",
            ["Contract performance", "Commercial outcome"],
            6,
            7,
            7,
            7,
            communication_frequency="Weekly",
        ),
        Stakeholder(
            "S07",
            "Data Protection Authority",
            StakeholderType.EXTERNAL,
            "Regulator",
            "Government",
            ["Privacy", "Lawful processing", "Security"],
            9,
            6,
            10,
            9,
            legitimacy=1.0,
            urgency=1.0,
            communication_frequency="As required",
        ),
        Stakeholder(
            "S08",
            "Accessibility Advocates",
            StakeholderType.EXTERNAL,
            "Community Representative",
            "Civil Society",
            ["Inclusive design", "Accessibility"],
            4,
            8,
            6,
            8,
            communication_frequency="Monthly",
        ),
        Stakeholder(
            "S09",
            "Finance Department",
            StakeholderType.INTERNAL,
            "Budget Controller",
            "Public Service Department",
            ["Cost control", "Budget compliance"],
            7,
            5,
            7,
            6,
            communication_frequency="Monthly",
        ),
        Stakeholder(
            "S10",
            "Cybersecurity Team",
            StakeholderType.INTERNAL,
            "Security",
            "Public Service Department",
            ["Threat reduction", "Security controls", "Incident response"],
            8,
            8,
            9,
            10,
            communication_frequency="Weekly",
        ),
    ]

    for stakeholder in sample_stakeholders:
        register.add(stakeholder)

    relationships = [
        Relationship("S01", "S02", RelationshipType.SUPPORTS, 0.9),
        Relationship("S02", "S03", RelationshipType.COLLABORATES_WITH, 0.9),
        Relationship("S02", "S04", RelationshipType.COLLABORATES_WITH, 0.8),
        Relationship("S02", "S06", RelationshipType.CONTRACTS_WITH if False else RelationshipType.COLLABORATES_WITH, 0.8),
        Relationship("S07", "S10", RelationshipType.INFLUENCES, 0.9),
        Relationship("S10", "S03", RelationshipType.INFLUENCES, 0.9),
        Relationship("S05", "S02", RelationshipType.INFLUENCES, 0.6),
        Relationship("S08", "S02", RelationshipType.INFLUENCES, 0.5),
        Relationship("S09", "S01", RelationshipType.REPORTS_TO, 0.7),
        Relationship("S06", "S03", RelationshipType.DEPENDS_ON, 0.8),
    ]

    for relationship in relationships:
        register.add_relationship(relationship)

    return register


# ---------------------------------------------------------------------------
# 5. STAKEHOLDER REGISTER OPERATIONS
# ---------------------------------------------------------------------------

def print_register(register: StakeholderRegister) -> None:
    print("\nSTAKEHOLDER REGISTER")
    header = (
        f"{'ID':<5} {'Name':<26} {'Type':<9} {'Power':>5} "
        f"{'Interest':>8} {'Influence':>10} {'Category':<18}"
    )
    print(header)
    print("-" * len(header))

    for stakeholder in register.stakeholders.values():
        print(
            f"{stakeholder.stakeholder_id:<5} "
            f"{stakeholder.name:<26} "
            f"{stakeholder.stakeholder_type.value:<9} "
            f"{stakeholder.power:>5.1f} "
            f"{stakeholder.interest:>8.1f} "
            f"{stakeholder.influence:>10.1f} "
            f"{stakeholder.power_interest_category():<18}"
        )


def create_stakeholder_register_from_names(
    names: Sequence[str],
) -> StakeholderRegister:
    register = StakeholderRegister()

    for index, name in enumerate(names, start=1):
        normalized = re.sub(r"[^A-Za-z0-9]+", "_", name.strip()).strip("_")
        stakeholder_id = f"AUTO{index:03d}"

        register.add(
            Stakeholder(
                stakeholder_id=stakeholder_id,
                name=name,
                stakeholder_type=StakeholderType.EXTERNAL,
                role="Unclassified",
                organization="Unclassified",
                interests=[],
                power=1,
                interest=1,
                influence=1,
                impact=1,
                notes=f"Generated from candidate name: {normalized}",
            )
        )

    return register


# ---------------------------------------------------------------------------
# 6. POWER-INTEREST GRID
# ---------------------------------------------------------------------------

def power_interest_matrix(register: StakeholderRegister) -> Dict[str, List[str]]:
    matrix = {
        "Manage closely": [],
        "Keep satisfied": [],
        "Keep informed": [],
        "Monitor": [],
    }

    for stakeholder in register.stakeholders.values():
        matrix[stakeholder.power_interest_category()].append(stakeholder.name)

    return matrix


def print_power_interest_matrix(register: StakeholderRegister) -> None:
    print("\nPOWER-INTEREST ANALYSIS")

    matrix = power_interest_matrix(register)
    for category, names in matrix.items():
        print(f"\n{category}:")
        for name in names:
            print(f"  - {name}")


# ---------------------------------------------------------------------------
# 7. INFLUENCE-IMPACT ANALYSIS
# ---------------------------------------------------------------------------

def influence_impact_priority(stakeholder: Stakeholder) -> str:
    score = stakeholder.influence_impact_score

    if score >= 64:
        return "Very high"
    if score >= 36:
        return "High"
    if score >= 16:
        return "Moderate"
    return "Low"


def rank_by_influence_impact(
    register: StakeholderRegister,
) -> List[Tuple[Stakeholder, float]]:
    return sorted(
        (
            (stakeholder, stakeholder.influence_impact_score)
            for stakeholder in register.stakeholders.values()
        ),
        key=lambda pair: pair[1],
        reverse=True,
    )


# ---------------------------------------------------------------------------
# 8. SALIENCE ANALYSIS
# ---------------------------------------------------------------------------

def classify_salience(stakeholder: Stakeholder) -> str:
    """
    Educational classification based on whether each normalized attribute is
    active. Different methodologies can operationalize salience differently.
    """
    attributes = {
        "power": stakeholder.power >= 5,
        "legitimacy": stakeholder.legitimacy >= 0.5,
        "urgency": stakeholder.urgency >= 0.5,
    }

    active_count = sum(attributes.values())

    if active_count == 3:
        return "Definitive"
    if active_count == 2:
        return "Expectant"
    if active_count == 1:
        return "Latent"
    return "Low salience"


def salience_report(register: StakeholderRegister) -> List[Tuple[str, float, str]]:
    report = []

    for stakeholder in register.stakeholders.values():
        report.append(
            (
                stakeholder.name,
                stakeholder.salience_score,
                classify_salience(stakeholder),
            )
        )

    return sorted(report, key=lambda item: item[1], reverse=True)


# ---------------------------------------------------------------------------
# 9. RACI RELATIONSHIPS
# ---------------------------------------------------------------------------

def build_raci_matrix() -> Dict[str, Dict[str, str]]:
    """
    RACI:
    R = Responsible: performs the work.
    A = Accountable: ultimately answerable for the outcome.
    C = Consulted: provides relevant input.
    I = Informed: receives relevant information.

    One activity can have multiple responsible parties, but having multiple
    accountabilities for one decision can create ambiguity.
    """
    return {
        "Requirements": {
            "Project Manager": "A",
            "Frontline Employees": "C",
            "Citizens": "C",
            "IT Operations": "C",
            "Cybersecurity Team": "C",
            "Executive Sponsor": "I",
        },
        "Security Review": {
            "Cybersecurity Team": "R",
            "IT Operations": "C",
            "Project Manager": "A",
            "Data Protection Authority": "C",
            "Executive Sponsor": "I",
        },
        "User Acceptance": {
            "Citizens": "R",
            "Frontline Employees": "R",
            "Project Manager": "A",
            "IT Operations": "C",
            "Executive Sponsor": "I",
        },
        "Budget Approval": {
            "Finance Department": "R",
            "Executive Sponsor": "A",
            "Project Manager": "C",
        },
    }


def validate_raci(raci: Dict[str, Dict[str, str]]) -> List[str]:
    errors: List[str] = []
    allowed = {"R", "A", "C", "I"}

    for activity, assignments in raci.items():
        if not assignments:
            errors.append(f"{activity}: no assignments.")
            continue

        for stakeholder, role in assignments.items():
            if role not in allowed:
                errors.append(
                    f"{activity}: invalid RACI role {role!r} for {stakeholder}."
                )

        accountabilities = [
            stakeholder
            for stakeholder, role in assignments.items()
            if role == "A"
        ]

        if len(accountabilities) == 0:
            errors.append(f"{activity}: no accountable stakeholder.")
        elif len(accountabilities) > 1:
            errors.append(
                f"{activity}: multiple accountable stakeholders: "
                f"{', '.join(accountabilities)}"
            )

    return errors


# ---------------------------------------------------------------------------
# 10. ENGAGEMENT GAP
# ---------------------------------------------------------------------------

def engagement_plan(register: StakeholderRegister) -> List[Dict[str, object]]:
    plan = []

    for stakeholder in register.stakeholders.values():
        gap = stakeholder.engagement_gap()

        if gap <= 0:
            action = "Maintain or monitor current engagement."
        elif gap == 1:
            action = "Targeted communication and participation."
        elif gap == 2:
            action = "Structured engagement, consultation, and issue management."
        else:
            action = "Intensive engagement and change-management intervention."

        plan.append(
            {
                "stakeholder": stakeholder.name,
                "current": stakeholder.current_engagement.value,
                "desired": stakeholder.desired_engagement.value,
                "gap": gap,
                "action": action,
            }
        )

    return sorted(plan, key=lambda item: item["gap"], reverse=True)


# ---------------------------------------------------------------------------
# 11. PRIORITIZATION MODELS
# ---------------------------------------------------------------------------

def weighted_priority_score(stakeholder: Stakeholder) -> float:
    """
    A project-specific weighted model.

    The weights are illustrative. They should be agreed with project
    governance rather than treated as universally correct.
    """
    return (
        0.25 * stakeholder.power
        + 0.20 * stakeholder.interest
        + 0.20 * stakeholder.influence
        + 0.20 * stakeholder.impact
        + 0.15 * (stakeholder.legitimacy * 10)
    )


def compare_prioritization_models(register: StakeholderRegister) -> List[Dict[str, object]]:
    rows = []

    for stakeholder in register.stakeholders.values():
        rows.append(
            {
                "name": stakeholder.name,
                "power_interest": round(stakeholder.power_interest_score, 2),
                "influence_impact": round(stakeholder.influence_impact_score, 2),
                "salience": round(stakeholder.salience_score, 2),
                "weighted": round(weighted_priority_score(stakeholder), 2),
            }
        )

    return rows


# ---------------------------------------------------------------------------
# 12. STAKEHOLDER DISCOVERY FROM A BUSINESS PROCESS
# ---------------------------------------------------------------------------

def identify_from_process_steps(
    process_steps: Sequence[Dict[str, object]],
) -> Set[str]:
    """
    Process mapping can reveal stakeholders who are easy to miss in a
    conventional organizational chart.
    """
    discovered: Set[str] = set()

    for step in process_steps:
        for key in ("owner", "actor", "customer", "approver", "supplier", "system_owner"):
            value = step.get(key)
            if isinstance(value, str) and value.strip():
                discovered.add(value.strip())

        reviewers = step.get("reviewers", [])
        if isinstance(reviewers, Iterable) and not isinstance(reviewers, (str, bytes)):
            for reviewer in reviewers:
                if isinstance(reviewer, str) and reviewer.strip():
                    discovered.add(reviewer.strip())

    return discovered


# ---------------------------------------------------------------------------
# 13. DUPLICATE AND DATA-QUALITY DETECTION
# ---------------------------------------------------------------------------

def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def find_possible_duplicate_names(names: Sequence[str]) -> List[Tuple[str, str]]:
    normalized: Dict[str, List[str]] = defaultdict(list)

    for name in names:
        normalized[normalize_name(name)].append(name)

    duplicates: List[Tuple[str, str]] = []

    for values in normalized.values():
        if len(values) > 1:
            for first, second in zip(values, values[1:]):
                duplicates.append((first, second))

    return duplicates


def detect_missing_fields(
    register: StakeholderRegister,
) -> Dict[str, List[str]]:
    missing: Dict[str, List[str]] = {}

    for stakeholder in register.stakeholders.values():
        fields: List[str] = []

        if not stakeholder.role.strip():
            fields.append("role")
        if not stakeholder.organization.strip():
            fields.append("organization")
        if not stakeholder.interests:
            fields.append("interests")
        if not stakeholder.notes.strip():
            fields.append("notes")

        if fields:
            missing[stakeholder.name] = fields

    return missing


# ---------------------------------------------------------------------------
# 14. STAKEHOLDER NETWORK ANALYSIS
# ---------------------------------------------------------------------------

class StakeholderNetwork:
    def __init__(self, register: StakeholderRegister) -> None:
        self.register = register
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)

        for relationship in register.relationships:
            self.adjacency[relationship.source_id].add(relationship.target_id)

    def direct_connections(self, stakeholder_id: str) -> Set[str]:
        return set(self.adjacency.get(stakeholder_id, set()))

    def out_degree(self, stakeholder_id: str) -> int:
        return len(self.adjacency.get(stakeholder_id, set()))

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
    ) -> Optional[List[str]]:
        if source_id == target_id:
            return [source_id]

        queue = deque([source_id])
        previous: Dict[str, Optional[str]] = {source_id: None}

        while queue:
            current = queue.popleft()

            for neighbor in self.adjacency.get(current, set()):
                if neighbor in previous:
                    continue

                previous[neighbor] = current

                if neighbor == target_id:
                    path = [target_id]
                    node = target_id

                    while previous[node] is not None:
                        node = previous[node]  # type: ignore[assignment]
                        path.append(node)

                    path.reverse()
                    return path

                queue.append(neighbor)

        return None

    def betweenness_like_score(self, stakeholder_id: str) -> float:
        """
        A small educational approximation.

        It counts how often a node occurs as an internal vertex on shortest
        paths among all reachable ordered pairs. It is not a replacement for
        a full network-analysis library.
        """
        nodes = list(self.register.stakeholders.keys())
        score = 0.0

        for source in nodes:
            for target in nodes:
                if source == target:
                    continue

                path = self.shortest_path(source, target)

                if path and stakeholder_id in path[1:-1]:
                    score += 1.0

        return score


# ---------------------------------------------------------------------------
# 15. STAKEHOLDER DEPENDENCY ANALYSIS
# ---------------------------------------------------------------------------

def dependency_map(
    register: StakeholderRegister,
) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = defaultdict(list)

    for relationship in register.relationships:
        if relationship.relationship_type == RelationshipType.DEPENDS_ON:
            source = register.get(relationship.source_id).name
            target = register.get(relationship.target_id).name
            result[source].append(target)

    return dict(result)


# ---------------------------------------------------------------------------
# 16. SCENARIO ANALYSIS
# ---------------------------------------------------------------------------

def simulate_scope_change(
    register: StakeholderRegister,
    changed_stakeholder_ids: Set[str],
    power_delta: float = 0,
    interest_delta: float = 0,
) -> List[Dict[str, object]]:
    """
    Demonstrates why stakeholder identification is not a one-time activity.

    A change can alter stakeholder power, interest, influence, and engagement.
    The function copies relevant values instead of mutating the live register.
    """
    result = []

    for stakeholder in register.stakeholders.values():
        if stakeholder.stakeholder_id in changed_stakeholder_ids:
            new_power = max(0, min(10, stakeholder.power + power_delta))
            new_interest = max(0, min(10, stakeholder.interest + interest_delta))
        else:
            new_power = stakeholder.power
            new_interest = stakeholder.interest

        result.append(
            {
                "stakeholder": stakeholder.name,
                "old_category": stakeholder.power_interest_category(),
                "new_power": new_power,
                "new_interest": new_interest,
                "new_category": (
                    "Manage closely"
                    if new_power >= 5 and new_interest >= 5
                    else "Keep satisfied"
                    if new_power >= 5
                    else "Keep informed"
                    if new_interest >= 5
                    else "Monitor"
                ),
            }
        )

    return result


# ---------------------------------------------------------------------------
# 17. SENSITIVITY ANALYSIS
# ---------------------------------------------------------------------------

def sensitivity_analysis(
    stakeholder: Stakeholder,
    variable: str,
    values: Sequence[float],
) -> List[Tuple[float, float]]:
    """
    Tests how a single input affects a weighted priority score.

    This helps expose whether a ranking is highly sensitive to subjective
    scoring assumptions.
    """
    results = []

    for value in values:
        clone = Stakeholder(**asdict(stakeholder))

        if variable == "power":
            clone.power = value
        elif variable == "interest":
            clone.interest = value
        elif variable == "influence":
            clone.influence = value
        elif variable == "impact":
            clone.impact = value
        else:
            raise ValueError(
                "Variable must be power, interest, influence, or impact."
            )

        results.append((value, weighted_priority_score(clone)))

    return results


# ---------------------------------------------------------------------------
# 18. COMMUNICATION DESIGN
# ---------------------------------------------------------------------------

def communication_recommendation(stakeholder: Stakeholder) -> Dict[str, str]:
    category = stakeholder.power_interest_category()

    recommendations = {
        "Manage closely": (
            "Frequent two-way communication, decision participation, "
            "early escalation, and issue transparency."
        ),
        "Keep satisfied": (
            "Provide decision-relevant information, avoid unnecessary detail, "
            "and monitor changes in expectations."
        ),
        "Keep informed": (
            "Provide understandable updates, consultation opportunities, "
            "and feedback channels."
        ),
        "Monitor": (
            "Use proportionate communication and monitor for changes in "
            "power, interest, influence, or impact."
        ),
    }

    return {
        "stakeholder": stakeholder.name,
        "category": category,
        "frequency": stakeholder.communication_frequency,
        "approach": recommendations[category],
    }


# ---------------------------------------------------------------------------
# 19. COMMON MISTAKES
# ---------------------------------------------------------------------------

def common_mistakes() -> List[Dict[str, str]]:
    return [
        {
            "mistake": "Only listing senior managers",
            "problem": "Operational, customer, community, or technical stakeholders may be missed.",
            "correction": "Analyze affected processes, dependencies, users, regulators, suppliers, and communities.",
        },
        {
            "mistake": "Confusing stakeholders with project team members",
            "problem": "Stakeholder status is broader than project-team membership.",
            "correction": "Ask who can affect or be affected by the initiative.",
        },
        {
            "mistake": "Treating power as the only priority factor",
            "problem": "Low-power groups can still experience substantial impact or possess legitimate concerns.",
            "correction": "Use multiple dimensions and document assumptions.",
        },
        {
            "mistake": "Making the register static",
            "problem": "Stakeholder power, interest, influence, and impact can change.",
            "correction": "Review the register at meaningful project or environmental changes.",
        },
        {
            "mistake": "Using numerical scores as objective facts",
            "problem": "Many stakeholder attributes involve judgment and uncertainty.",
            "correction": "Record evidence, assumptions, owners, and confidence levels.",
        },
        {
            "mistake": "Ignoring indirect stakeholders",
            "problem": "Indirect effects can create operational, legal, social, or reputational consequences.",
            "correction": "Map second-order effects and dependencies.",
        },
    ]


# ---------------------------------------------------------------------------
# 20. SECURITY AND PRIVACY CONSIDERATIONS
# ---------------------------------------------------------------------------

def security_checklist() -> List[str]:
    return [
        "Collect only stakeholder data necessary for the analysis.",
        "Avoid storing unnecessary personal or sensitive information.",
        "Apply access controls to stakeholder registers.",
        "Record the source and date of important assessments.",
        "Protect contact details and private organizational information.",
        "Separate analytical scores from factual identity information.",
        "Review whether a stakeholder classification could create unfair treatment.",
        "Use aggregated reporting when individual identification is unnecessary.",
        "Maintain auditability for material changes to stakeholder assessments.",
        "Define retention and deletion rules for stakeholder records.",
    ]


# ---------------------------------------------------------------------------
# 21. EXPORT
# ---------------------------------------------------------------------------

def export_register_json(register: StakeholderRegister) -> str:
    payload = {
        "stakeholders": [
            {
                **asdict(stakeholder),
                "stakeholder_type": stakeholder.stakeholder_type.value,
                "current_engagement": stakeholder.current_engagement.value,
                "desired_engagement": stakeholder.desired_engagement.value,
            }
            for stakeholder in register.stakeholders.values()
        ],
        "relationships": [
            {
                **asdict(relationship),
                "relationship_type": relationship.relationship_type.value,
            }
            for relationship in register.relationships
        ],
    }

    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# 22. UNIT TESTS
# ---------------------------------------------------------------------------

def run_tests() -> None:
    print("\nRUNNING TESTS")

    stakeholder = Stakeholder(
        "T01",
        "Test Stakeholder",
        StakeholderType.INTERNAL,
        "Tester",
        "Test Organization",
        ["Testing"],
        8,
        7,
        6,
        5,
    )

    assert stakeholder.power_interest_score == 56
    assert stakeholder.power_interest_category() == "Manage closely"
    assert stakeholder.influence_impact_score == 30
    assert stakeholder.engagement_gap() == 1

    register = StakeholderRegister()
    register.add(stakeholder)

    try:
        register.add(stakeholder)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate IDs should be rejected.")

    try:
        Stakeholder(
            "BAD",
            "Invalid",
            StakeholderType.INTERNAL,
            "Role",
            "Org",
            [],
            11,
            5,
            5,
            5,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid power should be rejected.")

    raci = build_raci_matrix()
    raci_errors = validate_raci(raci)
    assert not raci_errors, raci_errors

    assert normalize_name("  Example   Person ") == "example person"

    print("All tests passed.")


# ---------------------------------------------------------------------------
# 23. COMPLETE DEMONSTRATION
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 78)
    print("STAKEHOLDER IDENTIFICATION: COMPREHENSIVE PYTHON STUDY")
    print("=" * 78)

    beginner_example()

    print("\nIDENTIFICATION QUESTIONS")
    for number, question in enumerate(stakeholder_identification_questions(), start=1):
        print(f"{number:>2}. {question}")

    print("\nRULE-BASED DISCOVERY EXAMPLE")
    context = "A cloud-based education payment platform for students."
    for candidate in brainstorm_stakeholders(context):
        print(f"- {candidate}")

    register = build_sample_register()

    print_register(register)
    print_power_interest_matrix(register)

    print("\nINFLUENCE-IMPACT ANALYSIS")
    for stakeholder, score in rank_by_influence_impact(register):
        print(
            f"- {stakeholder.name}: score={score:.2f}, "
            f"priority={influence_impact_priority(stakeholder)}"
        )

    print("\nSALIENCE ANALYSIS")
    for name, score, classification in salience_report(register):
        print(f"- {name}: score={score:.2f}, classification={classification}")

    print("\nRACI VALIDATION")
    raci = build_raci_matrix()
    raci_errors = validate_raci(raci)

    if raci_errors:
        for error in raci_errors:
            print(f"- ERROR: {error}")
    else:
        print("RACI matrix passed structural validation.")

    print("\nENGAGEMENT ANALYSIS")
    for item in engagement_plan(register):
        print(
            f"- {item['stakeholder']}: "
            f"{item['current']} -> {item['desired']}, "
            f"gap={item['gap']}; {item['action']}"
        )

    print("\nPRIORITIZATION MODEL COMPARISON")
    comparison = compare_prioritization_models(register)

    for row in comparison:
        print(
            f"- {row['name']}: "
            f"power-interest={row['power_interest']}, "
            f"influence-impact={row['influence_impact']}, "
            f"salience={row['salience']}, "
            f"weighted={row['weighted']}"
        )

    print("\nPROCESS-BASED IDENTIFICATION")
    process_steps = [
        {
            "name": "Submit application",
            "actor": "Citizen",
            "owner": "Frontline Employees",
            "system_owner": "IT Operations",
            "reviewers": ["Accessibility Advocates"],
        },
        {
            "name": "Validate identity",
            "actor": "Identity Service",
            "owner": "IT Operations",
            "approver": "Cybersecurity Team",
            "supplier": "Technology Supplier",
        },
        {
            "name": "Approve privacy controls",
            "actor": "Privacy Officer",
            "owner": "Cybersecurity Team",
            "approver": "Data Protection Authority",
        },
    ]

    for person in sorted(identify_from_process_steps(process_steps)):
        print(f"- {person}")

    print("\nDATA-QUALITY CHECK")
    missing = detect_missing_fields(register)
    if missing:
        for name, fields in missing.items():
            print(f"- {name}: missing {', '.join(fields)}")
    else:
        print("No required analytical fields are missing.")

    names = [
        "Executive Sponsor",
        " executive sponsor ",
        "Citizens",
        "IT Operations",
    ]
    print("\nPOSSIBLE DUPLICATE NAMES")
    for first, second in find_possible_duplicate_names(names):
        print(f"- {first!r} and {second!r}")

    print("\nSTAKEHOLDER NETWORK")
    network = StakeholderNetwork(register)

    for stakeholder_id in ("S01", "S02", "S10"):
        stakeholder = register.get(stakeholder_id)
        print(
            f"- {stakeholder.name}: "
            f"direct outgoing connections={network.out_degree(stakeholder_id)}, "
            f"connections={list(network.direct_connections(stakeholder_id))}"
        )

    path = network.shortest_path("S07", "S03")
    print(f"Path from Data Protection Authority to IT Operations: {path}")

    print("\nNETWORK INTERMEDIARY SCORES")
    for stakeholder_id in register.stakeholders:
        stakeholder = register.get(stakeholder_id)
        score = network.betweenness_like_score(stakeholder_id)
        print(f"- {stakeholder.name}: {score:.1f}")

    print("\nDEPENDENCY MAP")
    for source, targets in dependency_map(register).items():
        print(f"- {source} depends on: {', '.join(targets)}")

    print("\nSCOPE-CHANGE SIMULATION")
    changed = simulate_scope_change(
        register,
        {"S05", "S08"},
        power_delta=2,
        interest_delta=0,
    )

    for item in changed:
        if item["old_category"] != item["new_category"]:
            print(
                f"- {item['stakeholder']}: "
                f"{item['old_category']} -> {item['new_category']}"
            )

    print("\nSENSITIVITY ANALYSIS")
    sponsor = register.get("S01")

    for value, score in sensitivity_analysis(
        sponsor,
        "power",
        [4, 5, 6, 7, 8, 9, 10],
    ):
        print(f"- Sponsor power={value:.1f}: weighted score={score:.2f}")

    print("\nCOMMUNICATION DESIGN")
    for stakeholder_id in ("S01", "S05", "S07", "S08"):
        recommendation = communication_recommendation(
            register.get(stakeholder_id)
        )
        print(
            f"- {recommendation['stakeholder']}: "
            f"{recommendation['category']}; "
            f"{recommendation['frequency']}; "
            f"{recommendation['approach']}"
        )

    print("\nCOMMON MISTAKES")
    for item in common_mistakes():
        print(f"- {item['mistake']}")
        print(f"  Problem: {item['problem']}")
        print(f"  Correction: {item['correction']}")

    print("\nSECURITY AND PRIVACY CHECKLIST")
    for item in security_checklist():
        print(f"- {item}")

    print("\nREGISTER JSON PREVIEW")
    exported = export_register_json(register)
    print(exported[:1800] + "\n...")

    run_tests()

    print("\nKEY CONCEPTS DEMONSTRATED")
    concepts = [
        "Stakeholder discovery",
        "Stakeholder register",
        "Internal and external stakeholders",
        "Power-interest analysis",
        "Influence-impact analysis",
        "Stakeholder salience",
        "RACI",
        "Engagement gap analysis",
        "Weighted prioritization",
        "Process-based discovery",
        "Data-quality validation",
        "Network analysis",
        "Dependency analysis",
        "Scenario analysis",
        "Sensitivity analysis",
        "Communication design",
        "Security and privacy controls",
        "Testing and auditability",
    ]

    for concept in concepts:
        print(f"- {concept}")

    print("\nProgram completed successfully.")


if __name__ == "__main__":
    main()
