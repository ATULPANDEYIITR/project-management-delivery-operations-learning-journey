from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import json
import statistics
import tempfile
import unittest


class RequirementStatus(Enum):
    PLANNED = "planned"
    VALIDATED = "validated"
    FAILED = "failed"
    DEFERRED = "deferred"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class QualityRequirement:
    requirement_id: str
    description: str
    metric: str
    target: float
    priority: int
    verification_method: str


@dataclass
class QualityCheck:
    requirement_id: str
    observed_value: float
    passed: bool
    evidence: str
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class QualityRisk:
    risk_id: str
    description: str
    probability: float
    impact: float
    mitigation: str

    @property
    def score(self) -> float:
        return self.probability * self.impact

    @property
    def level(self) -> RiskLevel:
        if self.score >= 0.75:
            return RiskLevel.CRITICAL
        if self.score >= 0.50:
            return RiskLevel.HIGH
        if self.score >= 0.25:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


@dataclass
class QualityPlan:
    project: str
    requirements: dict[str, QualityRequirement] = field(default_factory=dict)
    checks: list[QualityCheck] = field(default_factory=list)
    risks: list[QualityRisk] = field(default_factory=list)

    def add_requirement(self, requirement: QualityRequirement) -> None:
        if requirement.requirement_id in self.requirements:
            raise ValueError("Requirement IDs must be unique.")
        if not requirement.description.strip():
            raise ValueError("Requirement description cannot be empty.")
        if not 0 <= requirement.target <= 100:
            raise ValueError("Targets must be expressed as percentages from 0 to 100.")
        if requirement.priority not in range(1, 6):
            raise ValueError("Priority must be between 1 and 5.")
        self.requirements[requirement.requirement_id] = requirement

    def record_check(self, check: QualityCheck) -> None:
        if check.requirement_id not in self.requirements:
            raise KeyError(f"Unknown requirement: {check.requirement_id}")
        if not 0 <= check.observed_value <= 100:
            raise ValueError("Observed value must be between 0 and 100.")
        self.checks.append(check)

    def add_risk(self, risk: QualityRisk) -> None:
        if not 0 <= risk.probability <= 1:
            raise ValueError("Probability must be between 0 and 1.")
        if not 0 <= risk.impact <= 1:
            raise ValueError("Impact must be between 0 and 1.")
        self.risks.append(risk)

    def latest_check(self, requirement_id: str) -> QualityCheck | None:
        matches = [
            check for check in self.checks
            if check.requirement_id == requirement_id
        ]
        return max(matches, key=lambda item: item.checked_at) if matches else None

    def readiness(self) -> dict[str, object]:
        if not self.requirements:
            return {
                "ready": False,
                "score": 0.0,
                "reason": "No quality requirements have been planned."
            }

        weighted_results = []
        missing = []

        for requirement in self.requirements.values():
            check = self.latest_check(requirement.requirement_id)
            if check is None:
                missing.append(requirement.requirement_id)
                continue

            achievement = min(check.observed_value / requirement.target, 1.0)
            weighted_results.append(
                (achievement, requirement.priority, check.passed)
            )

        if not weighted_results:
            return {
                "ready": False,
                "score": 0.0,
                "reason": "No quality evidence has been recorded."
            }

        total_weight = sum(priority for _, priority, _ in weighted_results)
        score = (
            sum(achievement * priority for achievement, priority, _ in weighted_results)
            / total_weight
        ) * 100

        critical_risks = [
            risk.risk_id for risk in self.risks
            if risk.level == RiskLevel.CRITICAL
        ]

        failed_checks = [
            check.requirement_id for check in self.checks
            if not check.passed
        ]

        ready = not missing and not failed_checks and not critical_risks

        return {
            "ready": ready,
            "score": round(score, 2),
            "missing_requirements": missing,
            "failed_requirements": sorted(set(failed_checks)),
            "critical_risks": critical_risks,
        }

    def export(self, path: Path) -> None:
        data = {
            "project": self.project,
            "requirements": [
                {
                    "id": requirement.requirement_id,
                    "description": requirement.description,
                    "metric": requirement.metric,
                    "target": requirement.target,
                    "priority": requirement.priority,
                    "verification_method": requirement.verification_method,
                }
                for requirement in self.requirements.values()
            ],
            "checks": [
                {
                    "requirement_id": check.requirement_id,
                    "observed_value": check.observed_value,
                    "passed": check.passed,
                    "evidence": check.evidence,
                    "checked_at": check.checked_at,
                }
                for check in self.checks
            ],
            "risks": [
                {
                    "risk_id": risk.risk_id,
                    "description": risk.description,
                    "probability": risk.probability,
                    "impact": risk.impact,
                    "score": risk.score,
                    "level": risk.level.value,
                    "mitigation": risk.mitigation,
                }
                for risk in self.risks
            ],
        }

        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_example_plan() -> QualityPlan:
    plan = QualityPlan("Customer Order Processing Service")

    plan.add_requirement(QualityRequirement(
        "QR-001",
        "Automated tests must cover critical order-processing paths.",
        "test_coverage_percent",
        90,
        5,
        "CI coverage report"
    ))

    plan.add_requirement(QualityRequirement(
        "QR-002",
        "Critical API requests must complete within the agreed latency target.",
        "requests_within_latency_percent",
        95,
        5,
        "Performance test"
    ))

    plan.add_requirement(QualityRequirement(
        "QR-003",
        "Production defects classified as critical must remain at zero.",
        "critical_defect_free_percent",
        100,
        5,
        "Defect-management report"
    ))

    plan.add_requirement(QualityRequirement(
        "QR-004",
        "Security-sensitive inputs must pass validation tests.",
        "security_validation_percent",
        100,
        4,
        "Security test suite"
    ))

    plan.record_check(QualityCheck(
        "QR-001", 94, True, "CI run 1842: 94% branch coverage"
    ))
    plan.record_check(QualityCheck(
        "QR-002", 97, True, "Load test: 97% of requests below 300 ms"
    ))
    plan.record_check(QualityCheck(
        "QR-003", 100, True, "Release audit: zero critical defects"
    ))
    plan.record_check(QualityCheck(
        "QR-004", 98, False, "Security suite: two invalid-input cases failed"
    ))

    plan.add_risk(QualityRisk(
        "R-001",
        "Incomplete input validation could permit malformed order data.",
        0.40,
        0.90,
        "Add boundary-value and malformed-payload tests."
    ))

    plan.add_risk(QualityRisk(
        "R-002",
        "Performance degradation may occur under peak traffic.",
        0.35,
        0.70,
        "Run load tests against every release candidate."
    ))

    return plan


class QualityPlanningTests(unittest.TestCase):
    def test_duplicate_requirement_is_rejected(self):
        plan = QualityPlan("Test")
        requirement = QualityRequirement(
            "Q1", "Valid requirement", "coverage", 80, 3, "test"
        )
        plan.add_requirement(requirement)
        with self.assertRaises(ValueError):
            plan.add_requirement(requirement)

    def test_unknown_requirement_check_is_rejected(self):
        plan = QualityPlan("Test")
        with self.assertRaises(KeyError):
            plan.record_check(QualityCheck("UNKNOWN", 90, True, "none"))

    def test_readiness_detects_failed_quality_evidence(self):
        plan = build_example_plan()
        result = plan.readiness()
        self.assertFalse(result["ready"])
        self.assertIn("QR-004", result["failed_requirements"])

    def test_risk_level(self):
        risk = QualityRisk("R", "Example", 0.9, 0.9, "Mitigate")
        self.assertEqual(risk.level, RiskLevel.CRITICAL)

    def test_export_creates_valid_json(self):
        plan = build_example_plan()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "quality-plan.json"
            plan.export(output)
            parsed = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(parsed["project"], "Customer Order Processing Service")
            self.assertEqual(len(parsed["requirements"]), 4)


def main() -> None:
    plan = build_example_plan()
    readiness = plan.readiness()

    print(f"Project: {plan.project}")
    print(f"Quality readiness score: {readiness['score']}%")
    print(f"Merge/release quality gate: {'PASS' if readiness['ready'] else 'BLOCKED'}")

    print("\nQuality requirements:")
    for requirement in plan.requirements.values():
        check = plan.latest_check(requirement.requirement_id)
        status = (
            "NO EVIDENCE"
            if check is None
            else "PASS" if check.passed else "FAIL"
        )
        print(
            f"  {requirement.requirement_id}: "
            f"{requirement.metric} >= {requirement.target}% -> {status}"
        )

    print("\nQuality risks:")
    for risk in sorted(plan.risks, key=lambda item: item.score, reverse=True):
        print(
            f"  {risk.risk_id}: score={risk.score:.2f}, "
            f"level={risk.level.value}, mitigation={risk.mitigation}"
        )

    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "quality-plan.json"
        plan.export(output)
        print(f"\nPlan exported to: {output}")

    print("\nRunning validation tests...")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(QualityPlanningTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
