"""
POSITIVE RISKS: UNDERSTANDING PROJECT OPPORTUNITIES

A self-contained project opportunity management system.

Features:
- Opportunity identification and classification
- Probability and impact assessment
- Expected Monetary Value (EMV)
- Opportunity response strategies
- Opportunity ownership
- Risk scoring and prioritization
- Response planning and execution
- Opportunity monitoring
- Event tracking and reporting
- JSON persistence
- Validation and exception handling
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("opportunity_management")


class OpportunityCategory(Enum):
    COST = "Cost"
    SCHEDULE = "Schedule"
    QUALITY = "Quality"
    TECHNOLOGY = "Technology"
    RESOURCE = "Resource"
    BUSINESS = "Business"
    STRATEGIC = "Strategic"


class ResponseStrategy(Enum):
    EXPLOIT = "Exploit"
    ENHANCE = "Enhance"
    SHARE = "Share"
    ACCEPT = "Accept"


class OpportunityStatus(Enum):
    IDENTIFIED = "Identified"
    ASSESSED = "Assessed"
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    REALIZED = "Realized"
    CLOSED = "Closed"


@dataclass
class Opportunity:
    opportunity_id: str
    title: str
    description: str
    category: OpportunityCategory
    probability: float
    financial_impact: float
    owner: str
    strategy: ResponseStrategy
    status: OpportunityStatus = OpportunityStatus.IDENTIFIED
    response_cost: float = 0.0
    confidence: float = 1.0
    deadline: Optional[str] = None
    response_action: str = ""
    realized_benefit: float = 0.0
    history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self.opportunity_id.strip():
            raise ValueError("Opportunity ID is required.")

        if not self.title.strip():
            raise ValueError("Opportunity title is required.")

        if not self.owner.strip():
            raise ValueError("Opportunity owner is required.")

        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1.")

        if self.financial_impact < 0:
            raise ValueError("Positive opportunity impact cannot be negative.")

        if self.response_cost < 0:
            raise ValueError("Response cost cannot be negative.")

        if not 0 < self.confidence <= 1:
            raise ValueError("Confidence must be greater than 0 and at most 1.")

        if self.realized_benefit < 0:
            raise ValueError("Realized benefit cannot be negative.")

    @property
    def expected_monetary_value(self) -> float:
        return self.probability * self.financial_impact

    @property
    def net_expected_value(self) -> float:
        return self.expected_monetary_value - self.response_cost

    @property
    def risk_adjusted_value(self) -> float:
        return self.net_expected_value * self.confidence

    def record_event(self, event: str):
        self.history.append({
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": self.status.value
        })


class OpportunityManagementSystem:
    def __init__(self):
        self.opportunities: dict[str, Opportunity] = {}

    def add_opportunity(self, opportunity: Opportunity):
        if opportunity.opportunity_id in self.opportunities:
            raise ValueError("Duplicate opportunity ID.")

        self.opportunities[opportunity.opportunity_id] = opportunity
        opportunity.record_event("Opportunity identified")
        logger.info("Registered opportunity %s", opportunity.opportunity_id)

    def assess_opportunity(self, opportunity_id: str):
        opportunity = self._get(opportunity_id)

        if opportunity.status != OpportunityStatus.IDENTIFIED:
            raise ValueError("Only identified opportunities can be assessed.")

        opportunity.validate()
        opportunity.status = OpportunityStatus.ASSESSED
        opportunity.record_event("Opportunity assessed")

    def plan_response(self, opportunity_id: str, action: str):
        opportunity = self._get(opportunity_id)

        if opportunity.status not in (
            OpportunityStatus.IDENTIFIED,
            OpportunityStatus.ASSESSED
        ):
            raise ValueError("Response planning is not permitted in this state.")

        if not action.strip():
            raise ValueError("Response action is required.")

        opportunity.response_action = action
        opportunity.status = OpportunityStatus.PLANNED
        opportunity.record_event("Response plan established")

    def execute_response(self, opportunity_id: str):
        opportunity = self._get(opportunity_id)

        if opportunity.status != OpportunityStatus.PLANNED:
            raise ValueError("Opportunity must have a response plan.")

        opportunity.status = OpportunityStatus.IN_PROGRESS
        opportunity.record_event("Response execution started")

    def realize_opportunity(self, opportunity_id: str, benefit: float):
        opportunity = self._get(opportunity_id)

        if opportunity.status != OpportunityStatus.IN_PROGRESS:
            raise ValueError("Opportunity must be in progress.")

        if benefit < 0:
            raise ValueError("Realized benefit cannot be negative.")

        opportunity.realized_benefit = benefit
        opportunity.status = OpportunityStatus.REALIZED
        opportunity.record_event("Opportunity realized")

    def close_opportunity(self, opportunity_id: str):
        opportunity = self._get(opportunity_id)

        if opportunity.status not in (
            OpportunityStatus.REALIZED,
            OpportunityStatus.IDENTIFIED,
            OpportunityStatus.ASSESSED
        ):
            raise ValueError("Opportunity cannot be closed in its current state.")

        opportunity.status = OpportunityStatus.CLOSED
        opportunity.record_event("Opportunity closed")

    def _get(self, opportunity_id: str) -> Opportunity:
        try:
            return self.opportunities[opportunity_id]
        except KeyError:
            raise KeyError(f"Opportunity {opportunity_id} does not exist.")

    def rank_opportunities(self) -> list[Opportunity]:
        return sorted(
            self.opportunities.values(),
            key=lambda item: item.risk_adjusted_value,
            reverse=True
        )

    def portfolio_report(self) -> dict:
        items = list(self.opportunities.values())

        return {
            "total_opportunities": len(items),
            "total_expected_value": round(
                sum(x.expected_monetary_value for x in items), 2
            ),
            "total_response_cost": round(
                sum(x.response_cost for x in items), 2
            ),
            "total_net_expected_value": round(
                sum(x.net_expected_value for x in items), 2
            ),
            "realized_benefits": round(
                sum(x.realized_benefit for x in items), 2
            ),
            "by_status": {
                status.value: sum(
                    x.status == status for x in items
                )
                for status in OpportunityStatus
            }
        }

    def save(self, filepath: str):
        data = []

        for opportunity in self.opportunities.values():
            record = asdict(opportunity)
            record["category"] = opportunity.category.value
            record["strategy"] = opportunity.strategy.value
            record["status"] = opportunity.status.value
            data.append(record)

        path = Path(filepath)
        temporary = path.with_suffix(path.suffix + ".tmp")

        temporary.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )
        temporary.replace(path)

    def load(self, filepath: str):
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(filepath)

        data = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(data, list):
            raise ValueError("Invalid opportunity file format.")

        loaded = {}

        for record in data:
            record["category"] = OpportunityCategory(record["category"])
            record["strategy"] = ResponseStrategy(record["strategy"])
            record["status"] = OpportunityStatus(record["status"])

            opportunity = Opportunity(**record)

            if opportunity.opportunity_id in loaded:
                raise ValueError("Duplicate opportunity in persistence file.")

            loaded[opportunity.opportunity_id] = opportunity

        self.opportunities = loaded


def create_sample_system() -> OpportunityManagementSystem:
    system = OpportunityManagementSystem()

    samples = [
        Opportunity(
            "OPP-001",
            "Automation Savings",
            "Automating repetitive project reporting activities.",
            OpportunityCategory.COST,
            0.85,
            200000,
            "Project Manager",
            ResponseStrategy.EXPLOIT,
            response_cost=25000,
            confidence=0.95
        ),
        Opportunity(
            "OPP-002",
            "Early Delivery",
            "Using parallel development to complete delivery earlier.",
            OpportunityCategory.SCHEDULE,
            0.65,
            150000,
            "Delivery Lead",
            ResponseStrategy.ENHANCE,
            response_cost=15000,
            confidence=0.90
        ),
        Opportunity(
            "OPP-003",
            "Technology Partnership",
            "Sharing development resources with a strategic partner.",
            OpportunityCategory.STRATEGIC,
            0.55,
            300000,
            "Business Director",
            ResponseStrategy.SHARE,
            response_cost=30000,
            confidence=0.85
        ),
        Opportunity(
            "OPP-004",
            "Cloud Optimization",
            "Reducing infrastructure expenditure through workload optimization.",
            OpportunityCategory.TECHNOLOGY,
            0.75,
            100000,
            "Cloud Architect",
            ResponseStrategy.ACCEPT,
            response_cost=0,
            confidence=0.95
        )
    ]

    for opportunity in samples:
        system.add_opportunity(opportunity)

    return system


def main():
    system = create_sample_system()

    print("\nPROJECT OPPORTUNITY REGISTER")
    print("=" * 90)

    for opportunity in system.rank_opportunities():
        print(
            f"{opportunity.opportunity_id} | "
            f"{opportunity.title} | "
            f"Probability: {opportunity.probability:.0%} | "
            f"EMV: {opportunity.expected_monetary_value:,.2f} | "
            f"Net EV: {opportunity.net_expected_value:,.2f} | "
            f"Strategy: {opportunity.strategy.value}"
        )

    system.assess_opportunity("OPP-001")
    system.plan_response(
        "OPP-001",
        "Deploy automated reporting and validate savings."
    )
    system.execute_response("OPP-001")
    system.realize_opportunity("OPP-001", 175000)

    print("\nPORTFOLIO REPORT")
    print(json.dumps(system.portfolio_report(), indent=2))

    system.save("opportunity_register.json")
    print("\nRegister saved successfully.")

    # Validate duplicate detection and invalid probability handling.
    try:
        system.add_opportunity(system.opportunities["OPP-001"])
    except ValueError as error:
        print("Expected validation:", error)

    try:
        Opportunity(
            "INVALID",
            "Invalid Opportunity",
            "Invalid probability example",
            OpportunityCategory.BUSINESS,
            1.5,
            10000,
            "Owner",
            ResponseStrategy.ACCEPT
        )
    except ValueError as error:
        print("Expected input rejection:", error)


if __name__ == "__main__":
    main()
