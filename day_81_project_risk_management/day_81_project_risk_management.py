"""
PROJECT RISK MANAGEMENT
Introduction to Project Risks

A self-contained project risk management simulation covering:
- Risk identification
- Risk categorization
- Probability and impact assessment
- Risk exposure and prioritization
- Qualitative risk analysis
- Risk response planning
- Risk ownership
- Risk monitoring and reassessment
- Risk escalation
- Risk closure
- Risk reporting
- Risk register persistence

Run: python project_risk_management.py
Python: 3.10+
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s"
)

LOGGER = logging.getLogger("project_risk_management")


class RiskCategory(str, Enum):
    TECHNICAL = "Technical"
    FINANCIAL = "Financial"
    OPERATIONAL = "Operational"
    SCHEDULE = "Schedule"
    RESOURCE = "Resource"
    SECURITY = "Security"
    LEGAL = "Legal"
    EXTERNAL = "External"
    QUALITY = "Quality"
    SCOPE = "Scope"


class RiskStatus(str, Enum):
    IDENTIFIED = "Identified"
    ASSESSED = "Assessed"
    PLANNED = "Response Planned"
    MONITORING = "Monitoring"
    ESCALATED = "Escalated"
    CLOSED = "Closed"


class ResponseStrategy(str, Enum):
    AVOID = "Avoid"
    MITIGATE = "Mitigate"
    TRANSFER = "Transfer"
    ACCEPT = "Accept"
    EXPLOIT = "Exploit"
    ENHANCE = "Enhance"
    SHARE = "Share"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskEvent(str, Enum):
    REVIEWED = "Reviewed"
    ASSESSED = "Assessed"
    RESPONSE_ASSIGNED = "Response Assigned"
    MONITORED = "Monitored"
    ESCALATED = "Escalated"
    CLOSED = "Closed"


@dataclass
class RiskHistory:
    event: str
    timestamp: str
    details: str


@dataclass
class Risk:
    risk_id: str
    title: str
    description: str
    category: RiskCategory
    probability: int
    impact: int
    owner: str
    identified_date: date
    response_strategy: Optional[ResponseStrategy] = None
    response_action: str = ""
    response_cost: float = 0.0
    contingency_reserve: float = 0.0
    status: RiskStatus = RiskStatus.IDENTIFIED
    due_date: Optional[date] = None
    residual_probability: Optional[int] = None
    residual_impact: Optional[int] = None
    history: list[RiskHistory] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self):
        if not self.risk_id.strip():
            raise ValueError("Risk ID cannot be empty.")

        if not self.title.strip():
            raise ValueError("Risk title cannot be empty.")

        if not self.description.strip():
            raise ValueError("Risk description cannot be empty.")

        if not self.owner.strip():
            raise ValueError("Every risk must have an owner.")

        self.validate_score(self.probability, "Probability")
        self.validate_score(self.impact, "Impact")

        if self.response_cost < 0 or self.contingency_reserve < 0:
            raise ValueError("Financial amounts cannot be negative.")

        if (
            self.residual_probability is not None
            and self.residual_impact is not None
        ):
            self.validate_score(
                self.residual_probability,
                "Residual probability"
            )
            self.validate_score(
                self.residual_impact,
                "Residual impact"
            )

        self.record(
            RiskEvent.REVIEWED,
            "Risk created and entered into the risk register."
        )

    @staticmethod
    def validate_score(value: int, label: str):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{label} must be an integer.")

        if not 1 <= value <= 5:
            raise ValueError(f"{label} must be between 1 and 5.")

    @property
    def inherent_score(self) -> int:
        return self.probability * self.impact

    @property
    def current_score(self) -> int:
        probability = (
            self.residual_probability
            if self.residual_probability is not None
            else self.probability
        )
        impact = (
            self.residual_impact
            if self.residual_impact is not None
            else self.impact
        )
        return probability * impact

    @staticmethod
    def classify(score: int) -> RiskLevel:
        if score >= 20:
            return RiskLevel.CRITICAL
        if score >= 12:
            return RiskLevel.HIGH
        if score >= 6:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @property
    def inherent_level(self) -> RiskLevel:
        return self.classify(self.inherent_score)

    @property
    def current_level(self) -> RiskLevel:
        return self.classify(self.current_score)

    def record(self, event: RiskEvent, details: str):
        self.history.append(
            RiskHistory(
                event=event.value,
                timestamp=datetime.now().isoformat(timespec="seconds"),
                details=details
            )
        )

    def assess(self):
        if self.status == RiskStatus.CLOSED:
            raise ValueError("Closed risks cannot be reassessed.")

        self.status = RiskStatus.ASSESSED
        self.record(
            RiskEvent.ASSESSED,
            f"Inherent exposure: {self.inherent_score}; "
            f"level: {self.inherent_level.value}."
        )

    def assign_response(
        self,
        strategy: ResponseStrategy,
        action: str,
        response_cost: float = 0.0,
        contingency_reserve: float = 0.0
    ):
        if self.status == RiskStatus.CLOSED:
            raise ValueError("Cannot plan a response for a closed risk.")

        if not action.strip():
            raise ValueError("A response action is required.")

        if response_cost < 0 or contingency_reserve < 0:
            raise ValueError("Costs cannot be negative.")

        self.response_strategy = strategy
        self.response_action = action
        self.response_cost = response_cost
        self.contingency_reserve = contingency_reserve
        self.status = RiskStatus.PLANNED

        self.record(
            RiskEvent.RESPONSE_ASSIGNED,
            f"{strategy.value}: {action}"
        )

    def update_residual_risk(
        self,
        probability: int,
        impact: int
    ):
        if self.status == RiskStatus.CLOSED:
            raise ValueError("Closed risks cannot be monitored.")

        self.validate_score(probability, "Residual probability")
        self.validate_score(impact, "Residual impact")

        self.residual_probability = probability
        self.residual_impact = impact
        self.status = RiskStatus.MONITORING

        self.record(
            RiskEvent.MONITORED,
            f"Residual exposure updated to {probability * impact}."
        )

    def escalate(self, reason: str):
        if self.status == RiskStatus.CLOSED:
            raise ValueError("A closed risk cannot be escalated.")

        if not reason.strip():
            raise ValueError("Escalation reason is required.")

        self.status = RiskStatus.ESCALATED
        self.record(RiskEvent.ESCALATED, reason)

    def close(self, resolution: str):
        if self.status == RiskStatus.CLOSED:
            raise ValueError("Risk is already closed.")

        if not resolution.strip():
            raise ValueError("A closure resolution is required.")

        self.status = RiskStatus.CLOSED
        self.record(RiskEvent.CLOSED, resolution)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["category"] = self.category.value
        data["status"] = self.status.value
        data["identified_date"] = self.identified_date.isoformat()
        data["due_date"] = (
            self.due_date.isoformat() if self.due_date else None
        )
        data["response_strategy"] = (
            self.response_strategy.value
            if self.response_strategy else None
        )
        data["tags"] = sorted(self.tags)
        return data


class RiskRegister:
    def __init__(self, project_id: str, project_name: str):
        if not project_id.strip() or not project_name.strip():
            raise ValueError("Project ID and name are required.")

        self.project_id = project_id
        self.project_name = project_name
        self.risks: dict[str, Risk] = {}

    def add(self, risk: Risk):
        if risk.risk_id in self.risks:
            raise ValueError(f"Duplicate risk ID: {risk.risk_id}")

        self.risks[risk.risk_id] = risk
        LOGGER.info("Added risk %s", risk.risk_id)

    def get(self, risk_id: str) -> Risk:
        try:
            return self.risks[risk_id]
        except KeyError:
            raise KeyError(f"Risk {risk_id} does not exist.") from None

    def remove(self, risk_id: str):
        risk = self.get(risk_id)

        if risk.status != RiskStatus.CLOSED:
            raise ValueError("Only closed risks can be removed.")

        del self.risks[risk_id]

    def identify(self, risk: Risk):
        self.add(risk)

    def prioritized(self) -> list[Risk]:
        return sorted(
            self.risks.values(),
            key=lambda risk: (
                risk.current_score,
                risk.inherent_score,
                risk.risk_id
            ),
            reverse=True
        )

    def filter_by_category(
        self,
        category: RiskCategory
    ) -> list[Risk]:
        return [
            risk for risk in self.risks.values()
            if risk.category == category
        ]

    def filter_by_owner(self, owner: str) -> list[Risk]:
        return [
            risk for risk in self.risks.values()
            if risk.owner.casefold() == owner.casefold()
        ]

    def overdue(self, reference_date: Optional[date] = None):
        reference_date = reference_date or date.today()

        return [
            risk for risk in self.risks.values()
            if risk.due_date is not None
            and risk.due_date < reference_date
            and risk.status != RiskStatus.CLOSED
        ]

    def exposure_by_category(self) -> dict[str, int]:
        totals: dict[str, int] = {}

        for risk in self.risks.values():
            category = risk.category.value
            totals[category] = (
                totals.get(category, 0) + risk.current_score
            )

        return totals

    def summary(self) -> dict:
        active = [
            risk for risk in self.risks.values()
            if risk.status != RiskStatus.CLOSED
        ]

        levels = {
            level.value: sum(
                risk.current_level == level for risk in active
            )
            for level in RiskLevel
        }

        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "total_risks": len(self.risks),
            "active_risks": len(active),
            "closed_risks": len(self.risks) - len(active),
            "total_inherent_exposure": sum(
                risk.inherent_score for risk in active
            ),
            "total_residual_exposure": sum(
                risk.current_score for risk in active
            ),
            "risk_levels": levels,
            "overdue_risks": len(self.overdue()),
            "exposure_by_category": self.exposure_by_category()
        }

    def save_json(self, filename: str | Path):
        path = Path(filename)

        payload = {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "exported_at": datetime.now().isoformat(),
            "risks": [
                risk.to_dict()
                for risk in self.risks.values()
            ]
        }

        temporary = path.with_suffix(path.suffix + ".tmp")

        try:
            temporary.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8"
            )
            temporary.replace(path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise

    def export_csv(self, filename: str | Path):
        fields = [
            "risk_id",
            "title",
            "category",
            "owner",
            "probability",
            "impact",
            "inherent_score",
            "inherent_level",
            "current_score",
            "current_level",
            "response_strategy",
            "status"
        ]

        with Path(filename).open(
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()

            for risk in self.risks.values():
                writer.writerow({
                    "risk_id": risk.risk_id,
                    "title": risk.title,
                    "category": risk.category.value,
                    "owner": risk.owner,
                    "probability": risk.probability,
                    "impact": risk.impact,
                    "inherent_score": risk.inherent_score,
                    "inherent_level": risk.inherent_level.value,
                    "current_score": risk.current_score,
                    "current_level": risk.current_level.value,
                    "response_strategy": (
                        risk.response_strategy.value
                        if risk.response_strategy else ""
                    ),
                    "status": risk.status.value
                })


def probability_description(score: int) -> str:
    descriptions = {
        1: "Very unlikely",
        2: "Unlikely",
        3: "Possible",
        4: "Likely",
        5: "Very likely"
    }
    return descriptions[score]


def impact_description(score: int) -> str:
    descriptions = {
        1: "Negligible",
        2: "Minor",
        3: "Moderate",
        4: "Major",
        5: "Severe"
    }
    return descriptions[score]


def create_sample_project() -> RiskRegister:
    register = RiskRegister(
        "PRJ-2026-001",
        "Enterprise Project Management System"
    )

    samples = [
        Risk(
            "R001",
            "Cloud infrastructure delay",
            "Cloud environment provisioning may exceed the planned date.",
            RiskCategory.SCHEDULE,
            4,
            5,
            "Infrastructure Lead",
            date.today(),
            due_date=date.today() + timedelta(days=10)
        ),
        Risk(
            "R002",
            "Budget overrun",
            "Unexpected licensing and infrastructure costs may increase expenditure.",
            RiskCategory.FINANCIAL,
            3,
            5,
            "Project Manager",
            date.today(),
            due_date=date.today() + timedelta(days=20)
        ),
        Risk(
            "R003",
            "Data breach",
            "Unauthorized access may expose confidential project information.",
            RiskCategory.SECURITY,
            2,
            5,
            "Security Lead",
            date.today(),
            due_date=date.today() + timedelta(days=5)
        ),
        Risk(
            "R004",
            "Key developer unavailability",
            "An essential developer may become unavailable during integration.",
            RiskCategory.RESOURCE,
            3,
            4,
            "Engineering Manager",
            date.today(),
            due_date=date.today() + timedelta(days=15)
        ),
        Risk(
            "R005",
            "Scope expansion",
            "Uncontrolled requirements may increase development workload.",
            RiskCategory.SCOPE,
            4,
            4,
            "Product Owner",
            date.today(),
            due_date=date.today() + timedelta(days=8)
        ),
        Risk(
            "R006",
            "Regulatory approval delay",
            "Required external approval may take longer than expected.",
            RiskCategory.LEGAL,
            2,
            3,
            "Compliance Manager",
            date.today(),
            due_date=date.today() + timedelta(days=30)
        )
    ]

    for risk in samples:
        register.identify(risk)
        risk.assess()

    register.get("R001").assign_response(
        ResponseStrategy.MITIGATE,
        "Use an alternative cloud provisioning path and track delivery daily.",
        12000,
        5000
    )

    register.get("R002").assign_response(
        ResponseStrategy.MITIGATE,
        "Introduce monthly cost forecasts and spending thresholds.",
        3000,
        10000
    )

    register.get("R003").assign_response(
        ResponseStrategy.AVOID,
        "Block public access and enforce multi-factor authentication.",
        5000,
        2000
    )

    register.get("R004").assign_response(
        ResponseStrategy.MITIGATE,
        "Cross-train a second developer and document critical modules.",
        4000,
        1000
    )

    register.get("R005").assign_response(
        ResponseStrategy.AVOID,
        "Require formal approval for changes to the project baseline.",
        1500,
        1000
    )

    register.get("R006").assign_response(
        ResponseStrategy.TRANSFER,
        "Engage a qualified compliance service provider.",
        2500,
        1500
    )

    register.get("R001").update_residual_risk(2, 4)
    register.get("R002").update_residual_risk(2, 4)
    register.get("R003").update_residual_risk(1, 4)
    register.get("R004").update_residual_risk(2, 3)
    register.get("R005").update_residual_risk(2, 3)
    register.get("R006").update_residual_risk(2, 3)

    return register


def display_risk_register(register: RiskRegister):
    print("\n" + "=" * 110)
    print("PROJECT RISK REGISTER")
    print(register.project_name)
    print("=" * 110)

    header = (
        f"{'ID':<7}{'Risk':<30}{'Owner':<23}"
        f"{'P':<5}{'I':<5}{'Score':<8}{'Level':<12}{'Status'}"
    )

    print(header)
    print("-" * 110)

    for risk in register.prioritized():
        print(
            f"{risk.risk_id:<7}"
            f"{risk.title[:28]:<30}"
            f"{risk.owner[:21]:<23}"
            f"{risk.probability:<5}"
            f"{risk.impact:<5}"
            f"{risk.current_score:<8}"
            f"{risk.current_level.value:<12}"
            f"{risk.status.value}"
        )

    print("-" * 110)


def display_summary(register: RiskRegister):
    summary = register.summary()

    print("\nPROJECT RISK SUMMARY")
    print("-" * 45)

    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")


def run_tests():
    risk = Risk(
        "TEST01",
        "Test risk",
        "Risk used for validation.",
        RiskCategory.TECHNICAL,
        3,
        4,
        "Test Owner",
        date.today()
    )

    assert risk.inherent_score == 12
    assert risk.inherent_level == RiskLevel.HIGH

    risk.assign_response(
        ResponseStrategy.MITIGATE,
        "Introduce automated testing."
    )

    risk.update_residual_risk(1, 2)

    assert risk.current_score == 2
    assert risk.current_level == RiskLevel.LOW

    risk.close("Risk no longer exists.")

    assert risk.status == RiskStatus.CLOSED

    try:
        risk.escalate("Invalid escalation")
        raise AssertionError("Closed risk escalation should fail.")
    except ValueError:
        pass

    try:
        Risk(
            "INVALID",
            "Invalid score",
            "Probability outside valid range.",
            RiskCategory.TECHNICAL,
            6,
            3,
            "Owner",
            date.today()
        )
        raise AssertionError("Invalid probability should fail.")
    except ValueError:
        pass

    print("\nAll validation tests passed.")


def main():
    register = create_sample_project()

    display_risk_register(register)
    display_summary(register)

    print("\nCATEGORY EXPOSURE")
    for category, exposure in sorted(
        register.exposure_by_category().items(),
        key=lambda item: item[1],
        reverse=True
    ):
        print(f"{category:<20} {exposure}")

    print("\nHIGHEST PRIORITY RISKS")
    for risk in register.prioritized()[:3]:
        print(
            f"{risk.risk_id}: {risk.title} | "
            f"Inherent: {risk.inherent_score} | "
            f"Residual: {risk.current_score} | "
            f"Probability: {probability_description(risk.probability)} | "
            f"Impact: {impact_description(risk.impact)}"
        )

    print("\nRISK HISTORY")
    for entry in register.get("R001").history:
        print(
            f"{entry.timestamp} | {entry.event} | {entry.details}"
        )

    register.save_json("project_risk_register.json")
    register.export_csv("project_risk_register.csv")

    run_tests()

    print("\nRisk register exported successfully.")
    print("Files: project_risk_register.json, project_risk_register.csv")


if __name__ == "__main__":
    main()
