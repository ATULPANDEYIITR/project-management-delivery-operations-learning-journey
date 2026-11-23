"""
RISK PRIORITIZATION ENGINE
Rank project risks using probability, impact, urgency, detectability,
mitigation effectiveness, and risk ownership.

Python 3.10+
Standard library only.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Optional
import json
import csv
from pathlib import Path


class RiskCategory(Enum):
    TECHNICAL = "Technical"
    FINANCIAL = "Financial"
    OPERATIONAL = "Operational"
    SECURITY = "Security"
    LEGAL = "Legal"
    SCHEDULE = "Schedule"
    RESOURCE = "Resource"
    EXTERNAL = "External"


class RiskStatus(Enum):
    IDENTIFIED = "Identified"
    UNDER_REVIEW = "Under Review"
    MITIGATING = "Mitigating"
    MONITORING = "Monitoring"
    CLOSED = "Closed"


@dataclass
class Risk:
    risk_id: str
    title: str
    category: RiskCategory
    probability: int
    impact: int
    urgency: int
    detectability: int
    mitigation_effectiveness: int
    owner: str
    deadline: date
    status: RiskStatus = RiskStatus.IDENTIFIED
    mitigation_cost: float = 0.0
    notes: str = ""

    def validate(self) -> None:
        if not self.risk_id.strip() or not self.title.strip():
            raise ValueError("Risk ID and title are required.")

        if not self.owner.strip():
            raise ValueError("Every active risk requires an owner.")

        for name, value in (
            ("probability", self.probability),
            ("impact", self.impact),
            ("urgency", self.urgency),
            ("detectability", self.detectability),
            ("mitigation_effectiveness", self.mitigation_effectiveness),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer.")

            if not 1 <= value <= 5:
                raise ValueError(f"{name} must be between 1 and 5.")

        if self.mitigation_cost < 0:
            raise ValueError("Mitigation cost cannot be negative.")

    @property
    def inherent_score(self) -> float:
        """Calculate the unmitigated risk exposure."""
        return self.probability * self.impact * self.urgency

    @property
    def residual_score(self) -> float:
        """
        Higher detectability means a problem is harder to detect.
        Mitigation effectiveness reduces residual exposure.
        """
        detection_factor = 0.8 + (self.detectability - 1) * 0.1
        mitigation_factor = 1 - self.mitigation_effectiveness * 0.12

        return round(
            self.inherent_score * detection_factor * mitigation_factor,
            2
        )

    @property
    def priority_level(self) -> str:
        score = self.residual_score

        if score >= 60:
            return "CRITICAL"
        if score >= 35:
            return "HIGH"
        if score >= 15:
            return "MEDIUM"
        return "LOW"

    @property
    def is_overdue(self) -> bool:
        return self.deadline < date.today() and self.status != RiskStatus.CLOSED

    @property
    def response_required(self) -> bool:
        return (
            self.priority_level in {"CRITICAL", "HIGH"}
            and self.status != RiskStatus.CLOSED
        )

    def to_dict(self) -> dict:
        return {
            "risk_id": self.risk_id,
            "title": self.title,
            "category": self.category.value,
            "probability": self.probability,
            "impact": self.impact,
            "urgency": self.urgency,
            "detectability": self.detectability,
            "mitigation_effectiveness": self.mitigation_effectiveness,
            "inherent_score": self.inherent_score,
            "residual_score": self.residual_score,
            "priority": self.priority_level,
            "owner": self.owner,
            "deadline": self.deadline.isoformat(),
            "status": self.status.value,
            "overdue": self.is_overdue,
            "mitigation_cost": self.mitigation_cost,
        }


class RiskRegister:
    """Maintains, evaluates, and ranks a project's risk register."""

    def __init__(self, project_name: str):
        if not project_name.strip():
            raise ValueError("Project name is required.")

        self.project_name = project_name
        self._risks: dict[str, Risk] = {}

    def add_risk(self, risk: Risk) -> None:
        risk.validate()

        if risk.risk_id in self._risks:
            raise ValueError(f"Duplicate risk ID: {risk.risk_id}")

        self._risks[risk.risk_id] = risk

    def update_status(self, risk_id: str, status: RiskStatus) -> None:
        risk = self.get_risk(risk_id)

        if risk.status == RiskStatus.CLOSED and status != RiskStatus.CLOSED:
            raise ValueError("Closed risks cannot be reopened automatically.")

        risk.status = status

    def get_risk(self, risk_id: str) -> Risk:
        try:
            return self._risks[risk_id]
        except KeyError:
            raise KeyError(f"Risk not found: {risk_id}") from None

    def rank_risks(
        self,
        include_closed: bool = False
    ) -> list[Risk]:
        risks = list(self._risks.values())

        if not include_closed:
            risks = [
                risk for risk in risks
                if risk.status != RiskStatus.CLOSED
            ]

        # Stable deterministic ordering for equal risk scores.
        return sorted(
            risks,
            key=lambda risk: (
                -risk.residual_score,
                -risk.inherent_score,
                risk.deadline,
                risk.risk_id
            )
        )

    def category_exposure(self) -> dict[str, float]:
        exposure: dict[str, float] = {}

        for risk in self.rank_risks():
            category = risk.category.value
            exposure[category] = (
                exposure.get(category, 0.0) + risk.residual_score
            )

        return dict(sorted(
            exposure.items(),
            key=lambda item: (-item[1], item[0])
        ))

    def priority_distribution(self) -> dict[str, int]:
        distribution = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        }

        for risk in self.rank_risks():
            distribution[risk.priority_level] += 1

        return distribution

    def response_plan(self) -> list[dict]:
        plan = []

        for risk in self.rank_risks():
            if risk.response_required:
                plan.append({
                    "risk_id": risk.risk_id,
                    "action": "Immediate mitigation review",
                    "owner": risk.owner,
                    "deadline": risk.deadline.isoformat(),
                    "score": risk.residual_score,
                })

        return plan

    def export_json(self, filepath: str) -> None:
        output = {
            "project": self.project_name,
            "generated_on": date.today().isoformat(),
            "risks": [risk.to_dict() for risk in self.rank_risks(
                include_closed=True
            )],
            "distribution": self.priority_distribution(),
            "category_exposure": self.category_exposure(),
        }

        path = Path(filepath)
        path.write_text(
            json.dumps(output, indent=4),
            encoding="utf-8"
        )

    def export_csv(self, filepath: str) -> None:
        fields = list(Risk(
            "TEMP", "Temporary", RiskCategory.TECHNICAL,
            1, 1, 1, 1, 1, "System", date.today()
        ).to_dict().keys())

        with Path(filepath).open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()

            for risk in self.rank_risks(include_closed=True):
                writer.writerow(risk.to_dict())

    def display(self) -> None:
        print(f"\nPROJECT: {self.project_name}")
        print("=" * 105)
        print(
            f"{'ID':<9} {'RISK':<30} {'CATEGORY':<14} "
            f"{'SCORE':>8} {'LEVEL':<10} {'OWNER':<16} {'STATUS'}"
        )
        print("-" * 105)

        for risk in self.rank_risks():
            print(
                f"{risk.risk_id:<9} "
                f"{risk.title[:29]:<30} "
                f"{risk.category.value:<14} "
                f"{risk.residual_score:>8.2f} "
                f"{risk.priority_level:<10} "
                f"{risk.owner[:15]:<16} "
                f"{risk.status.value}"
            )

        print("=" * 105)


def build_sample_register() -> RiskRegister:
    register = RiskRegister("Enterprise Digital Transformation")

    sample_risks = [
        Risk(
            "R001", "Cybersecurity breach",
            RiskCategory.SECURITY, 5, 5, 5, 5, 1,
            "Security Lead", date.today() + timedelta(days=5),
            mitigation_cost=150000
        ),
        Risk(
            "R002", "Cloud migration failure",
            RiskCategory.TECHNICAL, 4, 5, 4, 3, 2,
            "Cloud Architect", date.today() + timedelta(days=12),
            mitigation_cost=80000
        ),
        Risk(
            "R003", "Budget overrun",
            RiskCategory.FINANCIAL, 4, 4, 4, 2, 3,
            "Finance Lead", date.today() + timedelta(days=20),
            mitigation_cost=30000
        ),
        Risk(
            "R004", "Key employee attrition",
            RiskCategory.RESOURCE, 3, 4, 3, 3, 2,
            "HR Manager", date.today() + timedelta(days=30),
            mitigation_cost=12000
        ),
        Risk(
            "R005", "Regulatory non-compliance",
            RiskCategory.LEGAL, 3, 5, 5, 4, 1,
            "Compliance Officer", date.today() + timedelta(days=7),
            mitigation_cost=45000
        ),
        Risk(
            "R006", "Vendor delivery delay",
            RiskCategory.SCHEDULE, 3, 3, 2, 2, 4,
            "Project Manager", date.today() + timedelta(days=40),
            mitigation_cost=10000
        ),
    ]

    for risk in sample_risks:
        register.add_risk(risk)

    return register


def run_tests() -> None:
    risk = Risk(
        "TEST01", "Test risk", RiskCategory.TECHNICAL,
        5, 5, 5, 5, 1, "Tester", date.today()
    )

    risk.validate()

    assert risk.inherent_score == 125
    assert risk.residual_score == 112.5
    assert risk.priority_level == "CRITICAL"

    register = RiskRegister("Test Project")
    register.add_risk(risk)

    assert len(register.rank_risks()) == 1

    try:
        register.add_risk(risk)
        raise AssertionError("Duplicate risk was accepted.")
    except ValueError:
        pass

    try:
        Risk(
            "INVALID", "Invalid", RiskCategory.TECHNICAL,
            6, 5, 5, 5, 1, "Tester", date.today()
        ).validate()
        raise AssertionError("Invalid probability was accepted.")
    except ValueError:
        pass

    register.update_status("TEST01", RiskStatus.CLOSED)
    assert len(register.rank_risks()) == 0

    print("All validation tests passed.")


def main() -> None:
    run_tests()

    register = build_sample_register()
    register.display()

    print("\nPRIORITY DISTRIBUTION")
    for level, count in register.priority_distribution().items():
        print(f"{level}: {count}")

    print("\nCATEGORY EXPOSURE")
    for category, score in register.category_exposure().items():
        print(f"{category}: {score:.2f}")

    print("\nIMMEDIATE RESPONSE PLAN")
    for item in register.response_plan():
        print(item)

    register.export_json("risk_assessment.json")
    register.export_csv("risk_assessment.csv")

    print("\nReports exported successfully.")


if __name__ == "__main__":
    main()
