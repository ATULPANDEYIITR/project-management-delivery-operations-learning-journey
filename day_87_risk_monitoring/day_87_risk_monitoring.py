#!/usr/bin/env python3
"""
Project Risk Monitoring and Tracking System

A self-contained implementation for identifying, assessing, monitoring,
mitigating, escalating, and closing project risks.

Python: 3.10+
Dependencies: Python standard library only.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("project_risk_monitor")


# ---------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------

class RiskCategory(str, Enum):
    SCHEDULE = "schedule"
    COST = "cost"
    TECHNICAL = "technical"
    RESOURCE = "resource"
    SECURITY = "security"
    OPERATIONAL = "operational"
    LEGAL = "legal"
    EXTERNAL = "external"


class RiskStatus(str, Enum):
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATION_PLANNED = "mitigation_planned"
    MONITORING = "monitoring"
    ESCALATED = "escalated"
    CLOSED = "closed"
    MATERIALIZED = "materialized"


class RiskResponse(str, Enum):
    AVOID = "avoid"
    MITIGATE = "mitigate"
    TRANSFER = "transfer"
    ACCEPT = "accept"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------

class RiskManagementError(Exception):
    """Base exception for risk-management operations."""


class ValidationError(RiskManagementError):
    """Raised when risk information is invalid."""


class RiskNotFoundError(RiskManagementError):
    """Raised when a requested risk does not exist."""


class InvalidTransitionError(RiskManagementError):
    """Raised when a risk cannot enter the requested state."""


class ConcurrentUpdateError(RiskManagementError):
    """Raised when an outdated risk version is submitted."""


# ---------------------------------------------------------------------
# Risk assessment configuration
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RiskThresholds:
    low_max: int = 4
    medium_max: int = 9
    high_max: int = 16

    def __post_init__(self):
        if not (
            1 <= self.low_max < self.medium_max < self.high_max <= 25
        ):
            raise ValidationError("Invalid risk thresholds.")


@dataclass(frozen=True)
class RiskAssessment:
    probability: int
    impact: int
    exposure: int
    level: RiskLevel


class RiskAssessmentEngine:
    """
    Calculates inherent and residual risk using a probability-impact matrix.

    Probability and impact are scored from 1 to 5.
    Exposure = Probability x Impact.
    """

    def __init__(self, thresholds: RiskThresholds | None = None):
        self.thresholds = thresholds or RiskThresholds()

    def assess(self, probability: int, impact: int) -> RiskAssessment:
        if not 1 <= probability <= 5:
            raise ValidationError("Probability must be between 1 and 5.")

        if not 1 <= impact <= 5:
            raise ValidationError("Impact must be between 1 and 5.")

        exposure = probability * impact

        if exposure <= self.thresholds.low_max:
            level = RiskLevel.LOW
        elif exposure <= self.thresholds.medium_max:
            level = RiskLevel.MEDIUM
        elif exposure <= self.thresholds.high_max:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        return RiskAssessment(
            probability=probability,
            impact=impact,
            exposure=exposure,
            level=level
        )


# ---------------------------------------------------------------------
# Project risk data model
# ---------------------------------------------------------------------

@dataclass
class Risk:
    project_id: str
    title: str
    description: str
    category: RiskCategory
    owner: str
    probability: int
    impact: int
    due_date: date
    response: RiskResponse = RiskResponse.MITIGATE
    mitigation_plan: str = ""
    contingency_plan: str = ""
    status: RiskStatus = RiskStatus.IDENTIFIED
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    risk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    review_count: int = 0
    last_reviewed: Optional[datetime] = None
    history: list[dict] = field(default_factory=list)

    def validate(self):
        if not self.project_id.strip():
            raise ValidationError("Project ID is required.")

        if not self.title.strip():
            raise ValidationError("Risk title is required.")

        if not self.description.strip():
            raise ValidationError("Risk description is required.")

        if not self.owner.strip():
            raise ValidationError("Risk owner is required.")

        if not isinstance(self.due_date, date):
            raise ValidationError("A valid due date is required.")

        if not 1 <= self.probability <= 5:
            raise ValidationError("Probability must be between 1 and 5.")

        if not 1 <= self.impact <= 5:
            raise ValidationError("Impact must be between 1 and 5.")


# ---------------------------------------------------------------------
# Risk monitoring events
# ---------------------------------------------------------------------

@dataclass
class RiskObservation:
    risk_id: str
    observed_probability: int
    observed_impact: int
    notes: str
    recorded_by: str
    observed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def validate(self):
        if not 1 <= self.observed_probability <= 5:
            raise ValidationError("Invalid observed probability.")

        if not 1 <= self.observed_impact <= 5:
            raise ValidationError("Invalid observed impact.")

        if not self.recorded_by.strip():
            raise ValidationError("Observer identity is required.")


# ---------------------------------------------------------------------
# Risk repository
# ---------------------------------------------------------------------

class RiskRepository:
    """
    In-memory repository with optimistic version checking.

    Production implementations should replace this repository with
    transactional database persistence.
    """

    def __init__(self):
        self._risks: dict[str, Risk] = {}

    def add(self, risk: Risk):
        risk.validate()

        if risk.risk_id in self._risks:
            raise ValidationError("Duplicate risk identifier.")

        self._risks[risk.risk_id] = risk

    def get(self, risk_id: str) -> Risk:
        risk = self._risks.get(risk_id)

        if risk is None:
            raise RiskNotFoundError(f"Risk {risk_id} was not found.")

        return risk

    def all(self) -> list[Risk]:
        return list(self._risks.values())

    def update(
        self,
        risk: Risk,
        expected_version: int
    ):
        existing = self.get(risk.risk_id)

        if existing.version != expected_version:
            raise ConcurrentUpdateError(
                "Risk record has changed since it was retrieved."
            )

        risk.validate()
        risk.version = expected_version + 1
        risk.updated_at = datetime.now(timezone.utc)

        self._risks[risk.risk_id] = risk

    def delete(self, risk_id: str):
        self.get(risk_id)
        del self._risks[risk_id]


# ---------------------------------------------------------------------
# Risk lifecycle service
# ---------------------------------------------------------------------

class RiskMonitoringService:

    ALLOWED_TRANSITIONS = {
        RiskStatus.IDENTIFIED: {
            RiskStatus.ASSESSED,
            RiskStatus.CLOSED
        },
        RiskStatus.ASSESSED: {
            RiskStatus.MITIGATION_PLANNED,
            RiskStatus.MONITORING,
            RiskStatus.ESCALATED,
            RiskStatus.CLOSED
        },
        RiskStatus.MITIGATION_PLANNED: {
            RiskStatus.MONITORING,
            RiskStatus.ESCALATED,
            RiskStatus.CLOSED
        },
        RiskStatus.MONITORING: {
            RiskStatus.ESCALATED,
            RiskStatus.CLOSED,
            RiskStatus.MATERIALIZED
        },
        RiskStatus.ESCALATED: {
            RiskStatus.MONITORING,
            RiskStatus.CLOSED,
            RiskStatus.MATERIALIZED
        },
        RiskStatus.MATERIALIZED: {
            RiskStatus.CLOSED
        },
        RiskStatus.CLOSED: set()
    }

    def __init__(self, repository: RiskRepository):
        self.repository = repository
        self.engine = RiskAssessmentEngine()

    def register_risk(self, risk: Risk) -> Risk:
        risk.validate()

        risk.history.append({
            "event": "risk_registered",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        self.repository.add(risk)
        return risk

    def transition(
        self,
        risk_id: str,
        new_status: RiskStatus,
        expected_version: int
    ) -> Risk:
        risk = self.repository.get(risk_id)

        if risk.version != expected_version:
            raise ConcurrentUpdateError("Risk version mismatch.")

        if new_status not in self.ALLOWED_TRANSITIONS[risk.status]:
            raise InvalidTransitionError(
                f"Cannot transition from {risk.status.value} "
                f"to {new_status.value}."
            )

        if new_status == RiskStatus.MITIGATION_PLANNED:
            if not risk.mitigation_plan.strip():
                raise ValidationError(
                    "A mitigation plan is required."
                )

        previous_status = risk.status
        risk.status = new_status

        risk.history.append({
            "event": "status_changed",
            "from": previous_status.value,
            "to": new_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        self.repository.update(risk, expected_version)
        return risk

    def record_observation(
        self,
        risk_id: str,
        observation: RiskObservation,
        expected_version: int
    ) -> Risk:
        risk = self.repository.get(risk_id)

        if risk.version != expected_version:
            raise ConcurrentUpdateError("Risk version mismatch.")

        if risk.status not in {
            RiskStatus.MONITORING,
            RiskStatus.ESCALATED
        }:
            raise InvalidTransitionError(
                "Observations require an active monitoring status."
            )

        observation.validate()

        old_assessment = self.engine.assess(
            risk.probability,
            risk.impact
        )

        new_assessment = self.engine.assess(
            observation.observed_probability,
            observation.observed_impact
        )

        risk.probability = observation.observed_probability
        risk.impact = observation.observed_impact
        risk.review_count += 1
        risk.last_reviewed = observation.observed_at

        risk.history.append({
            "event": "risk_observed",
            "observer": observation.recorded_by,
            "notes": observation.notes,
            "previous_exposure": old_assessment.exposure,
            "new_exposure": new_assessment.exposure,
            "previous_level": old_assessment.level.value,
            "new_level": new_assessment.level.value,
            "timestamp": observation.observed_at.isoformat()
        })

        if new_assessment.level == RiskLevel.CRITICAL:
            risk.status = RiskStatus.ESCALATED

        elif (
            new_assessment.level == RiskLevel.HIGH
            and risk.status != RiskStatus.ESCALATED
        ):
            risk.history.append({
                "event": "high_risk_alert",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        self.repository.update(risk, expected_version)
        return risk

    def assess_risk(self, risk_id: str) -> RiskAssessment:
        risk = self.repository.get(risk_id)

        return self.engine.assess(
            risk.probability,
            risk.impact
        )

    def add_mitigation_plan(
        self,
        risk_id: str,
        plan: str,
        contingency: str,
        expected_version: int
    ):
        risk = self.repository.get(risk_id)

        if risk.version != expected_version:
            raise ConcurrentUpdateError("Risk version mismatch.")

        if not plan.strip():
            raise ValidationError("Mitigation plan cannot be empty.")

        if not contingency.strip():
            raise ValidationError("Contingency plan cannot be empty.")

        risk.mitigation_plan = plan
        risk.contingency_plan = contingency

        self.repository.update(risk, expected_version)

        return self.transition(
            risk_id,
            RiskStatus.MITIGATION_PLANNED,
            risk.version
        )

    def dashboard(self) -> dict:
        risks = self.repository.all()

        level_counts = Counter()
        status_counts = Counter()
        category_counts = Counter()

        overdue = []
        critical = []
        total_exposure = 0

        today = date.today()

        for risk in risks:
            assessment = self.assess_risk(risk.risk_id)

            level_counts[assessment.level.value] += 1
            status_counts[risk.status.value] += 1
            category_counts[risk.category.value] += 1

            total_exposure += assessment.exposure

            if (
                risk.due_date < today
                and risk.status != RiskStatus.CLOSED
            ):
                overdue.append(risk.risk_id)

            if assessment.level == RiskLevel.CRITICAL:
                critical.append(risk.risk_id)

        return {
            "total_risks": len(risks),
            "risk_levels": dict(level_counts),
            "statuses": dict(status_counts),
            "categories": dict(category_counts),
            "overdue_risk_ids": overdue,
            "critical_risk_ids": critical,
            "total_exposure": total_exposure,
            "average_exposure": (
                round(total_exposure / len(risks), 2)
                if risks else 0
            )
        }

    def priority_report(self) -> list[dict]:
        active = [
            risk for risk in self.repository.all()
            if risk.status != RiskStatus.CLOSED
        ]

        active.sort(
            key=lambda risk: (
                self.assess_risk(risk.risk_id).exposure,
                risk.due_date
            ),
            reverse=True
        )

        report = []

        for risk in active:
            assessment = self.assess_risk(risk.risk_id)

            report.append({
                "risk_id": risk.risk_id,
                "title": risk.title,
                "owner": risk.owner,
                "category": risk.category.value,
                "probability": risk.probability,
                "impact": risk.impact,
                "exposure": assessment.exposure,
                "level": assessment.level.value,
                "status": risk.status.value,
                "due_date": risk.due_date.isoformat()
            })

        return report

    def stale_risks(self, maximum_age_days: int = 7) -> list[Risk]:
        if maximum_age_days < 0:
            raise ValidationError("Maximum age cannot be negative.")

        cutoff = datetime.now(timezone.utc) - timedelta(
            days=maximum_age_days
        )

        return [
            risk for risk in self.repository.all()
            if (
                risk.status != RiskStatus.CLOSED
                and (
                    risk.last_reviewed is None
                    or risk.last_reviewed < cutoff
                )
            )
        ]


# ---------------------------------------------------------------------
# File persistence
# ---------------------------------------------------------------------

class RiskExporter:

    @staticmethod
    def export_json(
        risks: list[Risk],
        output_path: str
    ):
        """
        Writes a JSON snapshot.

        The caller must select an appropriate trusted output directory.
        """
        path = Path(output_path)

        payload = []

        for risk in risks:
            item = asdict(risk)

            item["category"] = risk.category.value
            item["status"] = risk.status.value
            item["response"] = risk.response.value
            item["due_date"] = risk.due_date.isoformat()
            item["created_at"] = risk.created_at.isoformat()
            item["updated_at"] = risk.updated_at.isoformat()

            if risk.last_reviewed:
                item["last_reviewed"] = (
                    risk.last_reviewed.isoformat()
                )

            payload.append(item)

        path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8"
        )


# ---------------------------------------------------------------------
# Demonstration
# ---------------------------------------------------------------------

def main():
    repository = RiskRepository()
    service = RiskMonitoringService(repository)

    risk1 = Risk(
        project_id="PRJ-2026-001",
        title="Critical supplier delivery delay",
        description=(
            "The primary supplier may fail to deliver "
            "hardware within the scheduled period."
        ),
        category=RiskCategory.SCHEDULE,
        owner="Procurement Manager",
        probability=4,
        impact=5,
        due_date=date.today() + timedelta(days=15),
        mitigation_plan="Qualify a secondary supplier.",
        contingency_plan="Use approved alternative inventory."
    )

    risk2 = Risk(
        project_id="PRJ-2026-001",
        title="Budget overrun",
        description="Unexpected implementation expenses.",
        category=RiskCategory.COST,
        owner="Project Controller",
        probability=3,
        impact=4,
        due_date=date.today() + timedelta(days=30)
    )

    risk3 = Risk(
        project_id="PRJ-2026-001",
        title="Unauthorized system access",
        description="Potential access-control configuration weakness.",
        category=RiskCategory.SECURITY,
        owner="Security Manager",
        probability=2,
        impact=5,
        due_date=date.today() + timedelta(days=5)
    )

    for risk in (risk1, risk2, risk3):
        service.register_risk(risk)

    # Progress the supplier risk through its lifecycle.
    service.transition(
        risk1.risk_id,
        RiskStatus.ASSESSED,
        risk1.version
    )

    service.transition(
        risk1.risk_id,
        RiskStatus.MITIGATION_PLANNED,
        risk1.version
    )

    service.transition(
        risk1.risk_id,
        RiskStatus.MONITORING,
        risk1.version
    )

    observation = RiskObservation(
        risk_id=risk1.risk_id,
        observed_probability=5,
        observed_impact=5,
        notes="Supplier has confirmed a further delivery delay.",
        recorded_by="Procurement Manager"
    )

    service.record_observation(
        risk1.risk_id,
        observation,
        risk1.version
    )

    # Assess and display the project risk portfolio.
    print("\nPROJECT RISK DASHBOARD")
    print(json.dumps(service.dashboard(), indent=2))

    print("\nPRIORITY REPORT")
    print(json.dumps(service.priority_report(), indent=2))

    print("\nRISKS REQUIRING REVIEW")

    for risk in service.stale_risks(maximum_age_days=7):
        print(f"{risk.risk_id} | {risk.title}")

    # Demonstrate validation failure handling.
    try:
        service.engine.assess(7, 3)
    except ValidationError as error:
        logger.warning("Expected validation failure: %s", error)

    # Demonstrate optimistic concurrency protection.
    try:
        service.transition(
            risk2.risk_id,
            RiskStatus.ASSESSED,
            expected_version=99
        )
    except ConcurrentUpdateError as error:
        logger.warning("Expected concurrency failure: %s", error)

    # Export a snapshot.
    RiskExporter.export_json(
        repository.all(),
        "project_risk_register.json"
    )

    print("\nRisk register exported successfully.")


if __name__ == "__main__":
    main()
