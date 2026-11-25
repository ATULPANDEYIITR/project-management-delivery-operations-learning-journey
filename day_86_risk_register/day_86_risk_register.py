#!/usr/bin/env python3
"""
Risk Register Management System

Implements risk identification, assessment, prioritisation, mitigation,
ownership, monitoring, residual-risk evaluation, and reporting.
Uses only the Python standard library.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("risk_register")


class RiskCategory(str, Enum):
    STRATEGIC = "Strategic"
    OPERATIONAL = "Operational"
    FINANCIAL = "Financial"
    TECHNOLOGICAL = "Technological"
    CYBERSECURITY = "Cybersecurity"
    COMPLIANCE = "Compliance"
    REPUTATIONAL = "Reputational"
    PROJECT = "Project"
    ENVIRONMENTAL = "Environmental"


class RiskStatus(str, Enum):
    IDENTIFIED = "Identified"
    ASSESSED = "Assessed"
    TREATMENT_PLANNED = "Treatment Planned"
    IN_PROGRESS = "In Progress"
    MONITORING = "Monitoring"
    ACCEPTED = "Accepted"
    CLOSED = "Closed"


class RiskResponse(str, Enum):
    AVOID = "Avoid"
    MITIGATE = "Mitigate"
    TRANSFER = "Transfer"
    ACCEPT = "Accept"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class Risk:
    risk_id: str
    title: str
    description: str
    category: RiskCategory
    owner: str
    probability: int
    impact: int
    identified_date: str
    response: RiskResponse = RiskResponse.MITIGATE
    mitigation_plan: str = ""
    mitigation_owner: str = ""
    target_date: Optional[str] = None
    status: RiskStatus = RiskStatus.IDENTIFIED
    residual_probability: Optional[int] = None
    residual_impact: Optional[int] = None
    controls: list[str] = field(default_factory=list)
    review_date: Optional[str] = None
    notes: list[str] = field(default_factory=list)
    version: int = 1

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self.risk_id.strip():
            raise ValueError("Risk ID cannot be empty.")
        if not self.title.strip():
            raise ValueError("Risk title cannot be empty.")
        if not self.owner.strip():
            raise ValueError("Risk owner is required.")
        if not 1 <= self.probability <= 5:
            raise ValueError("Probability must be between 1 and 5.")
        if not 1 <= self.impact <= 5:
            raise ValueError("Impact must be between 1 and 5.")
        date.fromisoformat(self.identified_date)

        if self.target_date:
            target = date.fromisoformat(self.target_date)
            if target < date.fromisoformat(self.identified_date):
                raise ValueError("Target date cannot precede identification.")

        if self.residual_probability is not None:
            if not 1 <= self.residual_probability <= 5:
                raise ValueError("Residual probability must be between 1 and 5.")

        if self.residual_impact is not None:
            if not 1 <= self.residual_impact <= 5:
                raise ValueError("Residual impact must be between 1 and 5.")

        if (self.residual_probability is None) != (
            self.residual_impact is None
        ):
            raise ValueError("Both residual scores must be supplied together.")

        if self.version < 1:
            raise ValueError("Version must be positive.")

    @property
    def inherent_score(self) -> int:
        return self.probability * self.impact

    @property
    def residual_score(self) -> Optional[int]:
        if self.residual_probability is None:
            return None
        return self.residual_probability * self.residual_impact

    @staticmethod
    def classify(score: int) -> RiskLevel:
        if not 1 <= score <= 25:
            raise ValueError("Risk score must be between 1 and 25.")
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
    def residual_level(self) -> Optional[RiskLevel]:
        if self.residual_score is None:
            return None
        return self.classify(self.residual_score)

    def add_note(self, note: str):
        if not note.strip():
            raise ValueError("Note cannot be empty.")
        self.notes.append({
            "date": date.today().isoformat(),
            "text": note.strip(),
        })
        self.version += 1

    def assess_residual_risk(self, probability: int, impact: int):
        if not 1 <= probability <= 5 or not 1 <= impact <= 5:
            raise ValueError("Residual scores must be between 1 and 5.")
        self.residual_probability = probability
        self.residual_impact = impact
        self.status = RiskStatus.MONITORING
        self.version += 1

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("category", "status", "response"):
            data[key] = getattr(self, key).value
        data["inherent_score"] = self.inherent_score
        data["inherent_level"] = self.inherent_level.value
        data["residual_score"] = self.residual_score
        data["residual_level"] = (
            self.residual_level.value if self.residual_level else None
        )
        return data


class RiskRegister:
    def __init__(self, name: str):
        if not name.strip():
            raise ValueError("Register name is required.")
        self.name = name
        self._risks: dict[str, Risk] = {}
        self.audit_log: list[dict] = []

    def _audit(self, action: str, risk_id: str, details: str):
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "action": action,
            "risk_id": risk_id,
            "details": details,
        })

    def add_risk(self, risk: Risk):
        risk.validate()
        if risk.risk_id in self._risks:
            raise ValueError(f"Duplicate risk ID: {risk.risk_id}")
        self._risks[risk.risk_id] = risk
        self._audit("CREATE", risk.risk_id, risk.title)

    def get_risk(self, risk_id: str) -> Risk:
        try:
            return self._risks[risk_id]
        except KeyError:
            raise KeyError(f"Risk {risk_id} does not exist.") from None

    def update_risk(self, risk_id: str, **changes):
        risk = self.get_risk(risk_id)
        allowed = {
            "owner", "probability", "impact", "response",
            "mitigation_plan", "mitigation_owner", "target_date",
            "status", "controls", "review_date",
        }

        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Unsupported fields: {sorted(unknown)}")

        original = asdict(risk)
        try:
            for key, value in changes.items():
                if key in {"response", "status"} and isinstance(value, str):
                    enum_type = (
                        RiskResponse if key == "response" else RiskStatus
                    )
                    value = enum_type(value)
                setattr(risk, key, value)

            risk.validate()
        except Exception:
            for key, value in original.items():
                setattr(risk, key, value)
            raise

        risk.version += 1
        self._audit("UPDATE", risk_id, str(changes))

    def close_risk(self, risk_id: str, justification: str):
        risk = self.get_risk(risk_id)
        if not justification.strip():
            raise ValueError("Closure justification is required.")
        if risk.status == RiskStatus.CLOSED:
            raise ValueError("Risk is already closed.")
        risk.status = RiskStatus.CLOSED
        risk.add_note(f"Closure: {justification}")
        self._audit("CLOSE", risk_id, justification)

    def search(
        self,
        category: Optional[RiskCategory] = None,
        level: Optional[RiskLevel] = None,
        status: Optional[RiskStatus] = None,
        owner: Optional[str] = None,
    ) -> list[Risk]:
        results = self._risks.values()

        if category:
            results = filter(lambda r: r.category == category, results)
        if level:
            results = filter(lambda r: r.inherent_level == level, results)
        if status:
            results = filter(lambda r: r.status == status, results)
        if owner:
            results = filter(lambda r: r.owner.casefold() == owner.casefold(), results)

        return sorted(
            results,
            key=lambda r: (-r.inherent_score, r.risk_id),
        )

    def overdue_risks(self) -> list[Risk]:
        today = date.today()
        return [
            r for r in self._risks.values()
            if r.target_date
            and date.fromisoformat(r.target_date) < today
            and r.status != RiskStatus.CLOSED
        ]

    def report(self) -> dict:
        risks = list(self._risks.values())
        levels = {level.value: 0 for level in RiskLevel}

        for risk in risks:
            levels[risk.inherent_level.value] += 1

        return {
            "register": self.name,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "total_risks": len(risks),
            "risk_levels": levels,
            "average_inherent_score": (
                round(sum(r.inherent_score for r in risks) / len(risks), 2)
                if risks else 0
            ),
            "open_risks": sum(
                r.status != RiskStatus.CLOSED for r in risks
            ),
            "overdue_risks": len(self.overdue_risks()),
            "risks": [r.to_dict() for r in sorted(
                risks, key=lambda x: -x.inherent_score
            )],
        }

    def save(self, path: str):
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "name": self.name,
            "risks": [r.to_dict() for r in self._risks.values()],
            "audit_log": self.audit_log,
        }

        # Write to a temporary file before replacing the destination.
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            temporary.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )
            temporary.replace(destination)
        except OSError:
            temporary.unlink(missing_ok=True)
            logger.exception("Unable to save risk register.")
            raise

    def load(self, path: str):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("name") != self.name:
            raise ValueError("Register name does not match.")

        restored = {}
        for item in payload.get("risks", []):
            item.pop("inherent_score", None)
            item.pop("inherent_level", None)
            item.pop("residual_score", None)
            item.pop("residual_level", None)

            item["category"] = RiskCategory(item["category"])
            item["status"] = RiskStatus(item["status"])
            item["response"] = RiskResponse(item["response"])

            risk = Risk(**item)
            if risk.risk_id in restored:
                raise ValueError("Duplicate risk ID in saved file.")
            restored[risk.risk_id] = risk

        self._risks = restored
        self.audit_log = payload.get("audit_log", [])


def demonstrate():
    register = RiskRegister("Enterprise Technology Project")

    register.add_risk(Risk(
        risk_id="RISK-001",
        title="Unauthorised system access",
        description="Compromised credentials may expose confidential data.",
        category=RiskCategory.CYBERSECURITY,
        owner="Security Manager",
        probability=4,
        impact=5,
        identified_date=date.today().isoformat(),
        mitigation_plan="Deploy MFA, privileged access management and monitoring.",
        mitigation_owner="IT Security Team",
        target_date=(date.today() + timedelta(days=30)).isoformat(),
        controls=["MFA", "SIEM", "Access Reviews"],
    ))

    register.add_risk(Risk(
        risk_id="RISK-002",
        title="Project delivery delay",
        description="Dependency delays may affect the delivery schedule.",
        category=RiskCategory.PROJECT,
        owner="Project Manager",
        probability=3,
        impact=4,
        identified_date=date.today().isoformat(),
        response=RiskResponse.MITIGATE,
        mitigation_plan="Maintain dependency tracking and schedule buffers.",
        mitigation_owner="Delivery Team",
        target_date=(date.today() + timedelta(days=45)).isoformat(),
    ))

    register.add_risk(Risk(
        risk_id="RISK-003",
        title="Unexpected operating expenditure",
        description="Higher infrastructure costs may exceed the budget.",
        category=RiskCategory.FINANCIAL,
        owner="Finance Manager",
        probability=2,
        impact=3,
        identified_date=date.today().isoformat(),
        response=RiskResponse.TRANSFER,
    ))

    # Update the first risk after implementing its controls.
    register.get_risk("RISK-001").assess_residual_risk(2, 3)

    register.update_risk(
        "RISK-002",
        status=RiskStatus.IN_PROGRESS,
    )

    register.get_risk("RISK-001").add_note(
        "MFA deployment completed; monitoring effectiveness."
    )

    print("\nRISK REGISTER REPORT")
    print("=" * 65)

    for risk in register.search():
        print(
            f"{risk.risk_id} | {risk.title} | "
            f"Inherent: {risk.inherent_score}/25 "
            f"({risk.inherent_level.value}) | "
            f"Residual: {risk.residual_score} | "
            f"Owner: {risk.owner}"
        )

    print("\nAGGREGATE REPORT")
    print(json.dumps(register.report(), indent=2))

    output_file = Path("risk_register.json")
    register.save(str(output_file))
    print(f"\nRegister saved to {output_file.resolve()}")

    # Validate persistence by loading the saved register.
    restored = RiskRegister("Enterprise Technology Project")
    restored.load(str(output_file))
    assert len(restored._risks) == 3
    assert restored.get_risk("RISK-001").residual_score == 6

    print("Persistence validation passed.")


if __name__ == "__main__":
    try:
        demonstrate()
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        logger.error("Risk register execution failed: %s", error)
        raise
