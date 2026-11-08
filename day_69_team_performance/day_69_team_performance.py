#!/usr/bin/env python3
"""
Team Performance Evaluation System

Evaluates team performance using:
- Goal achievement
- Productivity
- Work quality
- Collaboration
- Reliability
- Delivery consistency

Includes weighted scoring, performance bands, trend analysis,
team comparisons, validation, JSON reporting, and automated tests.

Python 3.10+
"""

from __future__ import annotations

import json
import logging
import statistics
import unittest

from dataclasses import dataclass, field, asdict
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("team_performance")


class PerformanceError(Exception):
    """Base exception for performance evaluation."""


class ValidationError(PerformanceError):
    """Raised when performance data is invalid."""


class PerformanceBand(str, Enum):
    EXCELLENT = "Excellent"
    STRONG = "Strong"
    SATISFACTORY = "Satisfactory"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    CRITICAL = "Critical"


@dataclass(frozen=True)
class EvaluationWeights:
    goal_achievement: float = 0.25
    productivity: float = 0.20
    work_quality: float = 0.20
    collaboration: float = 0.15
    reliability: float = 0.10
    delivery_consistency: float = 0.10

    def __post_init__(self):
        values = asdict(self)

        if any(not 0 <= value <= 1 for value in values.values()):
            raise ValidationError("Weights must be between 0 and 1.")

        if abs(sum(values.values()) - 1.0) > 0.000001:
            raise ValidationError("Evaluation weights must total 1.0.")


@dataclass
class TeamMetrics:
    goal_achievement: float
    productivity: float
    work_quality: float
    collaboration: float
    reliability: float
    delivery_consistency: float

    def validate(self):
        for name, value in asdict(self).items():
            if not isinstance(value, (int, float)):
                raise ValidationError(f"{name} must be numeric.")

            if isinstance(value, bool) or not 0 <= value <= 100:
                raise ValidationError(
                    f"{name} must be between 0 and 100."
                )


@dataclass
class Team:
    team_id: str
    name: str
    department: str
    members: int
    metrics: TeamMetrics
    period: str
    manager: str

    def validate(self):
        if not self.team_id.strip():
            raise ValidationError("Team ID cannot be empty.")

        if not self.name.strip():
            raise ValidationError("Team name cannot be empty.")

        if not self.department.strip():
            raise ValidationError("Department cannot be empty.")

        if not isinstance(self.members, int) or isinstance(self.members, bool):
            raise ValidationError("Member count must be an integer.")

        if self.members <= 0:
            raise ValidationError("A team must have at least one member.")

        if not self.period.strip() or not self.manager.strip():
            raise ValidationError("Period and manager are required.")

        self.metrics.validate()


@dataclass
class EvaluationResult:
    team_id: str
    team_name: str
    score: float
    band: PerformanceBand
    strengths: list[str]
    improvement_areas: list[str]
    evaluated_on: str
    previous_score: Optional[float] = None
    trend: str = "Not Available"


class PerformanceEvaluator:

    def __init__(
        self,
        weights: EvaluationWeights = EvaluationWeights()
    ):
        self.weights = weights

    @staticmethod
    def performance_band(score: float) -> PerformanceBand:
        if score >= 90:
            return PerformanceBand.EXCELLENT
        if score >= 80:
            return PerformanceBand.STRONG
        if score >= 70:
            return PerformanceBand.SATISFACTORY
        if score >= 60:
            return PerformanceBand.NEEDS_IMPROVEMENT
        return PerformanceBand.CRITICAL

    def calculate_score(self, metrics: TeamMetrics) -> float:
        metrics.validate()

        weighted_score = sum(
            getattr(metrics, name) * weight
            for name, weight in asdict(self.weights).items()
        )

        return round(weighted_score, 2)

    def evaluate(
        self,
        team: Team,
        previous_score: Optional[float] = None
    ) -> EvaluationResult:

        team.validate()

        if previous_score is not None:
            if not isinstance(previous_score, (int, float)):
                raise ValidationError("Previous score must be numeric.")

            if isinstance(previous_score, bool) or not 0 <= previous_score <= 100:
                raise ValidationError("Previous score must be between 0 and 100.")

        metrics = asdict(team.metrics)
        score = self.calculate_score(team.metrics)

        strengths = [
            name.replace("_", " ").title()
            for name, value in metrics.items()
            if value >= 85
        ]

        improvement_areas = [
            name.replace("_", " ").title()
            for name, value in metrics.items()
            if value < 70
        ]

        if previous_score is None:
            trend = "Not Available"
        elif score > previous_score:
            trend = "Improving"
        elif score < previous_score:
            trend = "Declining"
        else:
            trend = "Stable"

        return EvaluationResult(
            team_id=team.team_id,
            team_name=team.name,
            score=score,
            band=self.performance_band(score),
            strengths=strengths,
            improvement_areas=improvement_areas,
            evaluated_on=date.today().isoformat(),
            previous_score=previous_score,
            trend=trend
        )


class PerformanceRegistry:

    def __init__(self):
        self.teams: dict[str, Team] = {}
        self.history: dict[str, list[float]] = {}

    def register(self, team: Team):
        team.validate()

        if team.team_id in self.teams:
            raise ValidationError(
                f"Team {team.team_id} already exists."
            )

        self.teams[team.team_id] = team
        self.history[team.team_id] = []

    def update_metrics(self, team_id: str, metrics: TeamMetrics):
        if team_id not in self.teams:
            raise ValidationError("Team does not exist.")

        metrics.validate()
        self.teams[team_id].metrics = metrics

    def add_historical_score(self, team_id: str, score: float):
        if team_id not in self.teams:
            raise ValidationError("Team does not exist.")

        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValidationError("Score must be numeric.")

        if not 0 <= score <= 100:
            raise ValidationError("Score must be between 0 and 100.")

        self.history[team_id].append(float(score))

    def get_previous_score(self, team_id: str) -> Optional[float]:
        scores = self.history.get(team_id, [])
        return scores[-1] if scores else None

    def all_teams(self) -> list[Team]:
        return list(self.teams.values())


class PerformanceReport:

    @staticmethod
    def summarize(results: list[EvaluationResult]) -> dict:
        if not results:
            return {
                "team_count": 0,
                "average_score": 0,
                "highest_score": None,
                "lowest_score": None,
                "performance_distribution": {}
            }

        scores = [result.score for result in results]

        distribution = {
            band.value: sum(
                result.band == band for result in results
            )
            for band in PerformanceBand
        }

        return {
            "team_count": len(results),
            "average_score": round(statistics.mean(scores), 2),
            "median_score": round(statistics.median(scores), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "performance_distribution": distribution
        }

    @staticmethod
    def save_json(results: list[EvaluationResult], filepath: str):
        path = Path(filepath)

        if path.suffix.lower() != ".json":
            raise ValidationError("Report filename must end in .json.")

        payload = {
            "evaluations": [
                {
                    **asdict(result),
                    "band": result.band.value
                }
                for result in results
            ],
            "summary": PerformanceReport.summarize(results)
        }

        # Prevent accidentally writing outside the intended directory
        # only when an application supplies a controlled output directory.
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4, ensure_ascii=False)


def evaluate_organization(
    registry: PerformanceRegistry,
    evaluator: PerformanceEvaluator
) -> list[EvaluationResult]:

    results = []

    for team in registry.all_teams():
        previous = registry.get_previous_score(team.team_id)

        result = evaluator.evaluate(team, previous)
        results.append(result)

        logger.info(
            "%s: %.2f (%s)",
            result.team_name,
            result.score,
            result.band.value
        )

    return sorted(
        results,
        key=lambda result: result.score,
        reverse=True
    )


def print_report(results: list[EvaluationResult]):
    print("\nTEAM PERFORMANCE REPORT")
    print("=" * 75)

    for position, result in enumerate(results, start=1):
        print(
            f"{position}. {result.team_name} | "
            f"Score: {result.score} | "
            f"Rating: {result.band.value} | "
            f"Trend: {result.trend}"
        )

        print(
            f"   Strengths: {', '.join(result.strengths) or 'None identified'}"
        )

        print(
            f"   Improvement: "
            f"{', '.join(result.improvement_areas) or 'None identified'}"
        )

    print("\nORGANIZATIONAL SUMMARY")
    print(json.dumps(
        PerformanceReport.summarize(results),
        indent=4
    ))


class PerformanceTests(unittest.TestCase):

    def setUp(self):
        self.evaluator = PerformanceEvaluator()

    def test_perfect_score(self):
        metrics = TeamMetrics(100, 100, 100, 100, 100, 100)
        self.assertEqual(self.evaluator.calculate_score(metrics), 100)

    def test_zero_score(self):
        metrics = TeamMetrics(0, 0, 0, 0, 0, 0)
        self.assertEqual(self.evaluator.calculate_score(metrics), 0)

    def test_invalid_metric(self):
        metrics = TeamMetrics(110, 80, 80, 80, 80, 80)

        with self.assertRaises(ValidationError):
            metrics.validate()

    def test_invalid_weights(self):
        with self.assertRaises(ValidationError):
            EvaluationWeights(0.5, 0.5, 0.5, 0, 0, 0)

    def test_performance_band(self):
        self.assertEqual(
            self.evaluator.performance_band(95),
            PerformanceBand.EXCELLENT
        )

    def test_historical_trend(self):
        team = Team(
            "T1", "Engineering", "Technology", 5,
            TeamMetrics(90, 90, 90, 90, 90, 90),
            "2026-Q4", "Manager A"
        )

        result = self.evaluator.evaluate(team, 75)
        self.assertEqual(result.trend, "Improving")


def main():
    registry = PerformanceRegistry()
    evaluator = PerformanceEvaluator()

    teams = [
        Team(
            "T001",
            "Engineering",
            "Technology",
            12,
            TeamMetrics(92, 88, 95, 85, 90, 87),
            "2026-Q4",
            "Manager A"
        ),
        Team(
            "T002",
            "Customer Support",
            "Operations",
            10,
            TeamMetrics(78, 85, 82, 91, 88, 80),
            "2026-Q4",
            "Manager B"
        ),
        Team(
            "T003",
            "Research",
            "R&D",
            8,
            TeamMetrics(95, 72, 90, 80, 75, 78),
            "2026-Q4",
            "Manager C"
        ),
        Team(
            "T004",
            "Quality Assurance",
            "Technology",
            6,
            TeamMetrics(65, 68, 92, 75, 70, 62),
            "2026-Q4",
            "Manager D"
        )
    ]

    for team in teams:
        registry.register(team)

    registry.add_historical_score("T001", 84)
    registry.add_historical_score("T002", 82)
    registry.add_historical_score("T003", 80)
    registry.add_historical_score("T004", 70)

    results = evaluate_organization(registry, evaluator)

    print_report(results)

    PerformanceReport.save_json(
        results,
        "reports/team_performance.json"
    )

    print("\nReport saved to reports/team_performance.json")

    unittest.main(argv=["team_performance.py"], exit=False)


if __name__ == "__main__":
    main()
