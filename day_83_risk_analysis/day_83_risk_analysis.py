#!/usr/bin/env python3
"""
Risk Analysis: Understanding Probability and Impact

A self-contained risk analysis system covering:
- Risk identification and classification
- Probability and impact assessment
- Inherent and residual risk
- Risk exposure and expected monetary loss
- Risk prioritization
- Mitigation controls
- Risk acceptance and escalation
- Monte Carlo portfolio simulation
- Risk reporting and JSON persistence

Run:
    python risk_analysis.py
"""

from __future__ import annotations

import json
import random
import statistics
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class RiskCategory(str, Enum):
    STRATEGIC = "Strategic"
    OPERATIONAL = "Operational"
    FINANCIAL = "Financial"
    TECHNOLOGY = "Technology"
    SECURITY = "Security"
    COMPLIANCE = "Compliance"
    REPUTATIONAL = "Reputational"


class RiskStatus(str, Enum):
    IDENTIFIED = "Identified"
    UNDER_REVIEW = "Under Review"
    MITIGATING = "Mitigating"
    ACCEPTED = "Accepted"
    CLOSED = "Closed"


class RiskLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskDecision(str, Enum):
    ACCEPT = "Accept"
    MITIGATE = "Mitigate"
    TRANSFER = "Transfer"
    AVOID = "Avoid"


@dataclass(frozen=True)
class RiskControl:
    name: str
    probability_reduction: float
    impact_reduction: float

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Control name cannot be empty.")

        for value in (
            self.probability_reduction,
            self.impact_reduction,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Control effectiveness must be between 0 and 1.")


@dataclass
class Risk:
    risk_id: str
    title: str
    description: str
    category: RiskCategory
    probability: float
    impact: float
    owner: str
    status: RiskStatus = RiskStatus.IDENTIFIED
    controls: list[RiskControl] = field(default_factory=list)
    decision: Optional[RiskDecision] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self):
        if not self.risk_id.strip():
            raise ValueError("Risk ID cannot be empty.")

        if not self.title.strip() or not self.owner.strip():
            raise ValueError("Risk title and owner are required.")

        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be between 0 and 1.")

        if self.impact < 0:
            raise ValueError("Impact cannot be negative.")

        if not isinstance(self.category, RiskCategory):
            raise ValueError("Invalid risk category.")

    @property
    def inherent_exposure(self) -> float:
        """Expected monetary loss before controls."""
        return self.probability * self.impact

    @property
    def residual_probability(self) -> float:
        """Probability after applying independent control reductions."""
        remaining = 1.0

        for control in self.controls:
            remaining *= 1 - control.probability_reduction

        return self.probability * remaining

    @property
    def residual_impact(self) -> float:
        """Impact after applying independent impact reductions."""
        remaining = 1.0

        for control in self.controls:
            remaining *= 1 - control.impact_reduction

        return self.impact * remaining

    @property
    def residual_exposure(self) -> float:
        return self.residual_probability * self.residual_impact

    @property
    def reduction_percentage(self) -> float:
        if self.inherent_exposure == 0:
            return 0.0

        return (
            1 - self.residual_exposure / self.inherent_exposure
        ) * 100

    @property
    def risk_level(self) -> RiskLevel:
        """
        Classification uses a probability-impact score.

        Probability and impact are mapped to five-point scales.
        Monetary exposure is calculated separately.
        """
        probability_score = min(
            5, max(1, int(self.probability * 5) + 1)
        )

        impact_score = (
            1 if self.impact == 0 else
            2 if self.impact <= 1000 else
            3 if self.impact <= 10000 else
            4 if self.impact <= 100000 else
            5
        )

        score = probability_score * impact_score

        if score >= 20:
            return RiskLevel.CRITICAL
        if score >= 12:
            return RiskLevel.HIGH
        if score >= 6:
            return RiskLevel.MODERATE

        return RiskLevel.LOW

    def add_control(self, control: RiskControl) -> None:
        if any(c.name == control.name for c in self.controls):
            raise ValueError("A control with this name already exists.")

        self.controls.append(control)

        if self.status == RiskStatus.IDENTIFIED:
            self.status = RiskStatus.MITIGATING

    def assign_decision(self, decision: RiskDecision) -> None:
        if decision == RiskDecision.ACCEPT and self.residual_exposure > 100000:
            raise ValueError(
                "High residual exposure requires additional authorization."
            )

        self.decision = decision

        if decision == RiskDecision.MITIGATE:
            self.status = RiskStatus.MITIGATING
        elif decision == RiskDecision.ACCEPT:
            self.status = RiskStatus.ACCEPTED
        elif decision == RiskDecision.AVOID:
            self.status = RiskStatus.CLOSED


class RiskRegister:
    """Central repository for identified organizational risks."""

    def __init__(self):
        self._risks: dict[str, Risk] = {}

    def add(self, risk: Risk) -> None:
        if risk.risk_id in self._risks:
            raise ValueError(f"Duplicate risk ID: {risk.risk_id}")

        self._risks[risk.risk_id] = risk

    def get(self, risk_id: str) -> Risk:
        try:
            return self._risks[risk_id]
        except KeyError:
            raise KeyError(f"Risk not found: {risk_id}") from None

    def all(self) -> list[Risk]:
        return list(self._risks.values())

    def prioritize(self) -> list[Risk]:
        return sorted(
            self.all(),
            key=lambda risk: (
                risk.residual_exposure,
                risk.inherent_exposure,
            ),
            reverse=True,
        )

    def filter_by_category(
        self,
        category: RiskCategory,
    ) -> list[Risk]:
        return [
            risk for risk in self.all()
            if risk.category == category
        ]

    def portfolio_exposure(self) -> dict[str, float]:
        risks = self.all()

        return {
            "inherent_exposure": sum(
                r.inherent_exposure for r in risks
            ),
            "residual_exposure": sum(
                r.residual_exposure for r in risks
            ),
        }

    def level_distribution(self) -> dict[str, int]:
        distribution = {level.value: 0 for level in RiskLevel}

        for risk in self.all():
            distribution[risk.risk_level.value] += 1

        return distribution

    def save(self, filepath: str) -> None:
        """Write the register atomically to avoid partial JSON files."""
        path = Path(filepath).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        records = []

        for risk in self.all():
            record = asdict(risk)
            record["category"] = risk.category.value
            record["status"] = risk.status.value
            record["decision"] = (
                risk.decision.value if risk.decision else None
            )
            records.append(record)

        temporary = path.with_suffix(path.suffix + ".tmp")

        try:
            temporary.write_text(
                json.dumps(records, indent=2),
                encoding="utf-8",
            )
            temporary.replace(path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise


def monte_carlo_simulation(
    risks: list[Risk],
    iterations: int = 10000,
    seed: int = 42,
) -> dict[str, float]:
    """
    Simulate portfolio losses.

    Each risk is treated as an independent Bernoulli event.
    A realized event produces its modeled impact.

    This assumption must be changed when risks are correlated.
    """

    if iterations <= 0:
        raise ValueError("Iterations must be positive.")

    generator = random.Random(seed)
    outcomes = []

    for _ in range(iterations):
        total_loss = 0.0

        for risk in risks:
            if generator.random() < risk.residual_probability:
                total_loss += risk.residual_impact

        outcomes.append(total_loss)

    ordered = sorted(outcomes)

    def percentile(values: list[float], p: float) -> float:
        index = int((len(values) - 1) * p)
        return values[index]

    return {
        "iterations": iterations,
        "mean_loss": statistics.mean(outcomes),
        "median_loss": statistics.median(outcomes),
        "standard_deviation": statistics.pstdev(outcomes),
        "p95_loss": percentile(ordered, 0.95),
        "p99_loss": percentile(ordered, 0.99),
        "maximum_simulated_loss": max(outcomes),
    }


def display_report(register: RiskRegister) -> None:
    print("\n" + "=" * 90)
    print("ORGANIZATIONAL RISK ANALYSIS REPORT")
    print("=" * 90)

    print(
        f"{'ID':<10} {'Risk':<30} {'Probability':>12} "
        f"{'Impact':>12} {'Level':<12} {'Residual':>12}"
    )

    print("-" * 90)

    for risk in register.prioritize():
        print(
            f"{risk.risk_id:<10} "
            f"{risk.title[:29]:<30} "
            f"{risk.probability:>11.1%} "
            f"{risk.impact:>12,.2f} "
            f"{risk.risk_level.value:<12} "
            f"{risk.residual_exposure:>12,.2f}"
        )

    portfolio = register.portfolio_exposure()

    print("-" * 90)
    print(f"Inherent portfolio exposure: {portfolio['inherent_exposure']:,.2f}")
    print(f"Residual portfolio exposure: {portfolio['residual_exposure']:,.2f}")
    print(f"Risk distribution: {register.level_distribution()}")


def build_example_register() -> RiskRegister:
    register = RiskRegister()

    risks = [
        Risk(
            risk_id="R001",
            title="Cybersecurity Breach",
            description="Unauthorized access to sensitive systems.",
            category=RiskCategory.SECURITY,
            probability=0.65,
            impact=500000,
            owner="Security Department",
        ),
        Risk(
            risk_id="R002",
            title="Project Cost Overrun",
            description="Actual implementation cost exceeds budget.",
            category=RiskCategory.FINANCIAL,
            probability=0.45,
            impact=120000,
            owner="Finance Department",
        ),
        Risk(
            risk_id="R003",
            title="Cloud Service Outage",
            description="Critical cloud infrastructure becomes unavailable.",
            category=RiskCategory.TECHNOLOGY,
            probability=0.30,
            impact=80000,
            owner="Infrastructure Team",
        ),
        Risk(
            risk_id="R004",
            title="Regulatory Noncompliance",
            description="Failure to meet mandatory regulatory obligations.",
            category=RiskCategory.COMPLIANCE,
            probability=0.20,
            impact=250000,
            owner="Compliance Officer",
        ),
        Risk(
            risk_id="R005",
            title="Employee Training Delay",
            description="Training completion is delayed.",
            category=RiskCategory.OPERATIONAL,
            probability=0.10,
            impact=5000,
            owner="Operations Manager",
        ),
    ]

    for risk in risks:
        register.add(risk)

    risks[0].add_control(
        RiskControl(
            "Multi-factor Authentication",
            probability_reduction=0.35,
            impact_reduction=0.05,
        )
    )

    risks[0].add_control(
        RiskControl(
            "Continuous Security Monitoring",
            probability_reduction=0.15,
            impact_reduction=0.25,
        )
    )

    risks[1].add_control(
        RiskControl(
            "Monthly Budget Reviews",
            probability_reduction=0.25,
            impact_reduction=0.20,
        )
    )

    risks[2].add_control(
        RiskControl(
            "Disaster Recovery Infrastructure",
            probability_reduction=0.20,
            impact_reduction=0.60,
        )
    )

    return register


def run_tests() -> None:
    control = RiskControl("Test Control", 0.5, 0.4)

    risk = Risk(
        "TEST01",
        "Test Risk",
        "Validation test",
        RiskCategory.OPERATIONAL,
        0.8,
        10000,
        "Test Owner",
    )

    assert risk.inherent_exposure == 8000

    risk.add_control(control)

    assert risk.residual_probability == 0.4
    assert risk.residual_impact == 6000
    assert risk.residual_exposure == 2400

    try:
        RiskControl("Invalid Control", 1.5, 0.2)
        raise AssertionError("Invalid effectiveness was accepted.")
    except ValueError:
        pass

    try:
        Risk(
            "INVALID",
            "Invalid",
            "Invalid probability",
            RiskCategory.OPERATIONAL,
            1.5,
            100,
            "Owner",
        )
        raise AssertionError("Invalid probability was accepted.")
    except ValueError:
        pass

    print("All validation tests passed.")


def main() -> None:
    run_tests()

    register = build_example_register()

    display_report(register)

    print("\nMONTE CARLO PORTFOLIO SIMULATION")

    simulation = monte_carlo_simulation(
        register.all(),
        iterations=10000,
    )

    for metric, value in simulation.items():
        if metric == "iterations":
            print(f"{metric}: {value}")
        else:
            print(f"{metric}: {value:,.2f}")

    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "risk_register.json"
        register.save(str(output))

        print(f"\nRisk register saved successfully: {output.name}")


if __name__ == "__main__":
    main()
