#!/usr/bin/env python3
"""
Risk Identification and Assessment System

Models risk discovery, classification, assessment, evidence collection,
risk ownership, control mapping, prioritization, and monitoring.

Python 3.10+
Standard-library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import json
import logging
import uuid


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("risk_identification")


class RiskCategory(str, Enum):
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    TECHNOLOGICAL = "technological"
    CYBERSECURITY = "cybersecurity"
    COMPLIANCE = "compliance"
    REPUTATIONAL = "reputational"
    ENVIRONMENTAL = "environmental"
    HUMAN_RESOURCE = "human_resource"
    THIRD_PARTY = "third_party"


class RiskStatus(str, Enum):
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    UNDER_REVIEW = "under_review"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class RiskSource(str, Enum):
    WORKSHOP = "workshop"
    AUDIT = "audit"
    INCIDENT = "incident"
    INTERVIEW = "interview"
    HISTORICAL_DATA = "historical_data"
    TECHNICAL_ANALYSIS = "technical_analysis"
    EXTERNAL_ENVIRONMENT = "external_environment"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class RiskEvidence:
    description: str
    source: RiskSource
    reference: str
    collected_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        if not self.description.strip():
            raise ValueError("Evidence description cannot be empty.")
        if not self.reference.strip():
            raise ValueError("Evidence reference cannot be empty.")


@dataclass(frozen=True)
class RiskControl:
    control_id: str
    description: str
    effectiveness: float
    preventive: bool = True

    def __post_init__(self):
        if not 0 <= self.effectiveness <= 1:
            raise ValueError("Control effectiveness must be between 0 and 1.")
        if not self.control_id.strip():
            raise ValueError("Control ID cannot be empty.")


@dataclass
class Risk:
    title: str
    description: str
    category: RiskCategory
    source: RiskSource
    owner: str
    probability: int
    impact: int
    detectability: int
    context: str
    risk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: RiskStatus = RiskStatus.IDENTIFIED
    evidence: list[RiskEvidence] = field(default_factory=list)
    controls: list[RiskControl] = field(default_factory=list)
    identified_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: Optional[datetime] = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.owner = self.owner.strip()
        self.context = self.context.strip()

        if not self.title or not self.description:
            raise ValueError("Risk title and description are required.")

        if not self.owner:
            raise ValueError("Every risk must have an accountable owner.")

        if not self.context:
            raise ValueError("Risk context is required.")

        for name, value in (
            ("probability", self.probability),
            ("impact", self.impact),
            ("detectability", self.detectability),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer.")
            if not 1 <= value <= 5:
                raise ValueError(f"{name} must be between 1 and 5.")

    @property
    def inherent_score(self) -> int:
        """Risk exposure before considering existing controls."""
        return self.probability * self.impact * self.detectability

    @property
    def inherent_level(self) -> RiskLevel:
        return classify_score(self.inherent_score)

    @property
    def control_effectiveness(self) -> float:
        """Combined effectiveness assumes independent controls."""
        remaining = 1.0

        for control in self.controls:
            remaining *= 1.0 - control.effectiveness

        return 1.0 - remaining

    @property
    def residual_score(self) -> float:
        """
        Residual score after controls.

        This is a simplified prioritization model, not a statistical
        probability calculation.
        """
        return self.inherent_score * (1 - self.control_effectiveness)

    @property
    def residual_level(self) -> RiskLevel:
        return classify_score(self.residual_score)

    def add_evidence(self, evidence: RiskEvidence) -> None:
        if any(item.reference == evidence.reference for item in self.evidence):
            raise ValueError("Evidence reference already exists.")

        self.evidence.append(evidence)

    def add_control(self, control: RiskControl) -> None:
        if any(item.control_id == control.control_id for item in self.controls):
            raise ValueError("Control ID already exists.")

        self.controls.append(control)

    def reassess(
        self,
        probability: int,
        impact: int,
        detectability: int
    ) -> None:
        validate_scale(probability, "probability")
        validate_scale(impact, "impact")
        validate_scale(detectability, "detectability")

        self.probability = probability
        self.impact = impact
        self.detectability = detectability
        self.reviewed_at = datetime.now(timezone.utc)
        self.status = RiskStatus.ASSESSED

    def transition(self, new_status: RiskStatus) -> None:
        allowed = {
            RiskStatus.IDENTIFIED: {
                RiskStatus.ASSESSED,
                RiskStatus.UNDER_REVIEW,
                RiskStatus.CLOSED,
            },
            RiskStatus.ASSESSED: {
                RiskStatus.UNDER_REVIEW,
                RiskStatus.MITIGATED,
                RiskStatus.ACCEPTED,
                RiskStatus.CLOSED,
            },
            RiskStatus.UNDER_REVIEW: {
                RiskStatus.ASSESSED,
                RiskStatus.MITIGATED,
                RiskStatus.ACCEPTED,
                RiskStatus.CLOSED,
            },
            RiskStatus.MITIGATED: {
                RiskStatus.UNDER_REVIEW,
                RiskStatus.CLOSED,
            },
            RiskStatus.ACCEPTED: {
                RiskStatus.UNDER_REVIEW,
                RiskStatus.CLOSED,
            },
            RiskStatus.CLOSED: set(),
        }

        if new_status not in allowed[self.status]:
            raise ValueError(
                f"Invalid transition: {self.status.value} "
                f"to {new_status.value}"
            )

        if new_status == RiskStatus.MITIGATED and not self.controls:
            raise ValueError("Mitigation requires at least one control.")

        self.status = new_status
        self.reviewed_at = datetime.now(timezone.utc)


def validate_scale(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")

    if not 1 <= value <= 5:
        raise ValueError(f"{field_name} must be between 1 and 5.")


def classify_score(score: float) -> RiskLevel:
    if score >= 75:
        return RiskLevel.CRITICAL
    if score >= 40:
        return RiskLevel.HIGH
    if score >= 15:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


class RiskRegister:
    """Centralized repository for identified organizational risks."""

    def __init__(self, organization: str):
        if not organization.strip():
            raise ValueError("Organization name is required.")

        self.organization = organization
        self._risks: dict[str, Risk] = {}

    def add(self, risk: Risk) -> None:
        if risk.risk_id in self._risks:
            raise ValueError("Duplicate risk identifier.")

        if any(
            existing.title.casefold() == risk.title.casefold()
            and existing.context.casefold() == risk.context.casefold()
            for existing in self._risks.values()
        ):
            raise ValueError("A similar risk already exists in this context.")

        self._risks[risk.risk_id] = risk
        logger.info("Identified risk: %s", risk.title)

    def get(self, risk_id: str) -> Risk:
        try:
            return self._risks[risk_id]
        except KeyError:
            raise KeyError(f"Risk not found: {risk_id}") from None

    def search(
        self,
        category: Optional[RiskCategory] = None,
        status: Optional[RiskStatus] = None,
        minimum_score: float = 0
    ) -> list[Risk]:
        results = [
            risk
            for risk in self._risks.values()
            if (category is None or risk.category == category)
            and (status is None or risk.status == status)
            and risk.inherent_score >= minimum_score
        ]

        return sorted(
            results,
            key=lambda risk: risk.inherent_score,
            reverse=True
        )

    def category_distribution(self) -> dict[str, int]:
        distribution = {category.value: 0 for category in RiskCategory}

        for risk in self._risks.values():
            distribution[risk.category.value] += 1

        return distribution

    def priority_report(self) -> list[dict]:
        report = []

        for risk in self.search():
            report.append({
                "risk_id": risk.risk_id,
                "title": risk.title,
                "category": risk.category.value,
                "owner": risk.owner,
                "status": risk.status.value,
                "probability": risk.probability,
                "impact": risk.impact,
                "detectability": risk.detectability,
                "inherent_score": risk.inherent_score,
                "inherent_level": risk.inherent_level.value,
                "control_effectiveness": round(
                    risk.control_effectiveness, 3
                ),
                "residual_score": round(risk.residual_score, 2),
                "residual_level": risk.residual_level.value,
                "evidence_count": len(risk.evidence),
            })

        return report

    def export_json(self, filename: str) -> None:
        """Export an assessment snapshot without overwriting silently."""
        if not filename.strip():
            raise ValueError("Filename is required.")

        data = {
            "organization": self.organization,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "risks": self.priority_report(),
            "categories": self.category_distribution(),
        }

        with open(filename, "x", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def __len__(self) -> int:
        return len(self._risks)


def build_example_register() -> RiskRegister:
    register = RiskRegister("Enterprise Digital Operations")

    cyber_risk = Risk(
        title="Unauthorized access to production systems",
        description=(
            "Compromised credentials may allow an attacker "
            "to access sensitive production resources."
        ),
        category=RiskCategory.CYBERSECURITY,
        source=RiskSource.TECHNICAL_ANALYSIS,
        owner="Security Operations Manager",
        probability=4,
        impact=5,
        detectability=4,
        context="Production infrastructure",
    )

    cyber_risk.add_evidence(RiskEvidence(
        description="Privileged accounts lack consistent MFA enforcement.",
        source=RiskSource.AUDIT,
        reference="AUDIT-2026-014",
    ))

    cyber_risk.add_control(RiskControl(
        control_id="CTRL-MFA",
        description="Enforce phishing-resistant multi-factor authentication.",
        effectiveness=0.55,
    ))

    cyber_risk.add_control(RiskControl(
        control_id="CTRL-MONITOR",
        description="Monitor privileged account activity.",
        effectiveness=0.30,
    ))

    cyber_risk.transition(RiskStatus.ASSESSED)
    cyber_risk.transition(RiskStatus.UNDER_REVIEW)

    register.add(cyber_risk)

    operational_risk = Risk(
        title="Critical supplier service interruption",
        description=(
            "A third-party supplier outage may interrupt "
            "business-critical operations."
        ),
        category=RiskCategory.THIRD_PARTY,
        source=RiskSource.HISTORICAL_DATA,
        owner="Vendor Management Lead",
        probability=3,
        impact=4,
        detectability=3,
        context="Cloud service dependencies",
    )

    operational_risk.add_evidence(RiskEvidence(
        description="Previous supplier outages exceeded recovery targets.",
        source=RiskSource.INCIDENT,
        reference="INCIDENT-2026-022",
    ))

    operational_risk.reassess(4, 4, 3)
    register.add(operational_risk)

    compliance_risk = Risk(
        title="Regulatory reporting deadline failure",
        description=(
            "Incomplete operational records may prevent timely "
            "submission of mandatory regulatory reports."
        ),
        category=RiskCategory.COMPLIANCE,
        source=RiskSource.INTERVIEW,
        owner="Compliance Officer",
        probability=2,
        impact=5,
        detectability=3,
        context="Regulatory reporting",
    )

    register.add(compliance_risk)

    return register


def run_tests() -> None:
    assert classify_score(10) == RiskLevel.LOW
    assert classify_score(20) == RiskLevel.MODERATE
    assert classify_score(50) == RiskLevel.HIGH
    assert classify_score(80) == RiskLevel.CRITICAL

    risk = Risk(
        title="Test risk",
        description="Testing validation and state transitions.",
        category=RiskCategory.OPERATIONAL,
        source=RiskSource.WORKSHOP,
        owner="Test Owner",
        probability=2,
        impact=3,
        detectability=4,
        context="Test environment",
    )

    assert risk.inherent_score == 24

    risk.add_control(RiskControl(
        control_id="TEST-1",
        description="Test preventive control",
        effectiveness=0.5,
    ))

    assert risk.residual_score == 12

    try:
        risk.reassess(6, 2, 2)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid probability was accepted.")

    try:
        risk.transition(RiskStatus.MITIGATED)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid state transition was accepted.")


def main() -> None:
    run_tests()

    register = build_example_register()

    print("\nRISK IDENTIFICATION AND ASSESSMENT")
    print("=" * 65)
    print("Organization:", register.organization)
    print("Total identified risks:", len(register))

    print("\nCATEGORY DISTRIBUTION")
    for category, count in register.category_distribution().items():
        if count:
            print(f"{category}: {count}")

    print("\nPRIORITY REPORT")
    for item in register.priority_report():
        print(
            f"\n{item['title']}\n"
            f"Category: {item['category']}\n"
            f"Owner: {item['owner']}\n"
            f"Inherent exposure: {item['inherent_score']} "
            f"({item['inherent_level']})\n"
            f"Residual exposure: {item['residual_score']} "
            f"({item['residual_level']})\n"
            f"Status: {item['status']}\n"
            f"Evidence records: {item['evidence_count']}"
        )

    print("\nHIGH-PRIORITY RISKS")
    for risk in register.search(minimum_score=40):
        print(f"- {risk.title}: {risk.inherent_score}")

    print("\nAll validation tests passed.")


if __name__ == "__main__":
    main()
