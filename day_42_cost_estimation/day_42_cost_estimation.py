from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
import csv
import json
import math
import statistics
from typing import Dict, List, Optional, Tuple


MONEY = Decimal("0.01")


def money(value: float | int | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


class EstimateMethod(Enum):
    BOTTOM_UP = "bottom_up"
    PARAMETRIC = "parametric"
    THREE_POINT = "three_point"
    ANALOGOUS = "analogous"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CostItem:
    name: str
    quantity: float
    unit_cost: Decimal
    category: str
    confidence: float = 0.9

    @property
    def total(self) -> Decimal:
        return money(self.quantity * float(self.unit_cost))


@dataclass
class Risk:
    name: str
    probability: float
    impact: Decimal
    contingency_factor: float = 1.0

    @property
    def expected_monetary_value(self) -> Decimal:
        return money(
            float(self.impact) * self.probability * self.contingency_factor
        )


@dataclass
class ThreePointEstimate:
    optimistic: Decimal
    most_likely: Decimal
    pessimistic: Decimal

    def triangular(self) -> Decimal:
        return money(
            (
                float(self.optimistic)
                + float(self.most_likely)
                + float(self.pessimistic)
            )
            / 3
        )

    def pert(self) -> Decimal:
        return money(
            (
                float(self.optimistic)
                + 4 * float(self.most_likely)
                + float(self.pessimistic)
            )
            / 6
        )

    def standard_deviation(self) -> float:
        return (
            float(self.pessimistic) - float(self.optimistic)
        ) / 6


@dataclass
class ProjectEstimate:
    project_name: str
    direct_items: List[CostItem] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    management_reserve_rate: float = 0.05

    @property
    def direct_cost(self) -> Decimal:
        return money(sum(float(item.total) for item in self.direct_items))

    @property
    def expected_risk_cost(self) -> Decimal:
        return money(
            sum(float(risk.expected_monetary_value) for risk in self.risks)
        )

    @property
    def contingency_reserve(self) -> Decimal:
        return money(
            float(self.direct_cost) * self.management_reserve_rate
        )

    @property
    def estimated_project_cost(self) -> Decimal:
        return money(
            float(self.direct_cost)
            + float(self.expected_risk_cost)
            + float(self.contingency_reserve)
        )


def validate_cost_item(item: CostItem) -> None:
    if not item.name.strip():
        raise ValueError("Cost item name cannot be empty.")
    if item.quantity < 0:
        raise ValueError(f"Quantity cannot be negative: {item.name}")
    if item.unit_cost < 0:
        raise ValueError(f"Unit cost cannot be negative: {item.name}")
    if not 0 <= item.confidence <= 1:
        raise ValueError(f"Confidence must be between 0 and 1: {item.name}")


def validate_risk(risk: Risk) -> None:
    if not risk.name.strip():
        raise ValueError("Risk name cannot be empty.")
    if not 0 <= risk.probability <= 1:
        raise ValueError(f"Invalid probability for {risk.name}")
    if risk.impact < 0:
        raise ValueError(f"Risk impact cannot be negative: {risk.name}")
    if risk.contingency_factor < 0:
        raise ValueError(f"Contingency factor cannot be negative: {risk.name}")


def demonstrate_basic_cost_estimation() -> ProjectEstimate:
    print("\n=== Bottom-Up Cost Estimation ===")

    estimate = ProjectEstimate("Municipal Asset Inspection Platform")

    items = [
        CostItem("Business analysis", 80, money(85), "labor", 0.92),
        CostItem("Backend development", 240, money(70), "labor", 0.88),
        CostItem("Frontend development", 180, money(65), "labor", 0.86),
        CostItem("Cloud infrastructure", 12, money(450), "infrastructure", 0.80),
        CostItem("Security assessment", 5, money(1200), "security", 0.76),
        CostItem("Training", 4, money(750), "training", 0.90),
    ]

    for item in items:
        validate_cost_item(item)
        estimate.direct_items.append(item)
        print(f"{item.name:30} {item.total:>12,.2f}")

    print(f"Direct cost:                  {estimate.direct_cost:>12,.2f}")
    return estimate


def parametric_estimate(
    units: int,
    cost_per_unit: Decimal,
    fixed_cost: Decimal = Decimal("0"),
) -> Decimal:
    if units < 0:
        raise ValueError("Units cannot be negative.")
    if cost_per_unit < 0 or fixed_cost < 0:
        raise ValueError("Costs cannot be negative.")

    return money(units * float(cost_per_unit) + float(fixed_cost))


def demonstrate_parametric_estimation() -> Decimal:
    print("\n=== Parametric Cost Estimation ===")

    inspection_units = 1250
    variable_cost = money(18.50)
    platform_setup = money(12000)

    result = parametric_estimate(
        inspection_units,
        variable_cost,
        platform_setup,
    )

    print(f"Inspection units:              {inspection_units}")
    print(f"Variable cost per unit:        {variable_cost:,.2f}")
    print(f"Fixed setup cost:              {platform_setup:,.2f}")
    print(f"Parametric estimate:           {result:,.2f}")

    return result


def demonstrate_three_point_estimation() -> ThreePointEstimate:
    print("\n=== Three-Point Estimation ===")

    estimate = ThreePointEstimate(
        optimistic=money(70000),
        most_likely=money(95000),
        pessimistic=money(145000),
    )

    print(f"Optimistic:                    {estimate.optimistic:,.2f}")
    print(f"Most likely:                   {estimate.most_likely:,.2f}")
    print(f"Pessimistic:                   {estimate.pessimistic:,.2f}")
    print(f"Triangular estimate:           {estimate.triangular():,.2f}")
    print(f"PERT estimate:                 {estimate.pert():,.2f}")
    print(f"Standard deviation:            {estimate.standard_deviation():,.2f}")

    return estimate


def analogous_estimate(
    historical_projects: List[Tuple[str, Decimal, float]],
    similarity_weights: List[float],
) -> Decimal:
    if not historical_projects:
        raise ValueError("At least one historical project is required.")

    if len(historical_projects) != len(similarity_weights):
        raise ValueError("Project and weight counts must match.")

    if any(weight < 0 for weight in similarity_weights):
        raise ValueError("Similarity weights cannot be negative.")

    total_weight = sum(similarity_weights)
    if total_weight <= 0:
        raise ValueError("At least one positive similarity weight is required.")

    weighted_cost = sum(
        float(cost) * weight
        for (_, cost, _), weight in zip(historical_projects, similarity_weights)
    )

    return money(weighted_cost / total_weight)


def calculate_labor_cost(
    roles: Dict[str, Tuple[float, Decimal]]
) -> Decimal:
    total = Decimal("0")

    for role, (hours, rate) in roles.items():
        if hours < 0 or rate < 0:
            raise ValueError(f"Invalid labor input for {role}.")
        total += Decimal(str(hours)) * rate

    return money(total)


def simulate_monthly_burn(
    total_budget: Decimal,
    months: int,
    spending_profile: List[float],
) -> List[Decimal]:
    if months <= 0:
        raise ValueError("Months must be positive.")
    if len(spending_profile) != months:
        raise ValueError("Spending profile must contain one value per month.")
    if any(value < 0 for value in spending_profile):
        raise ValueError("Spending profile cannot contain negative values.")

    profile_total = sum(spending_profile)
    if profile_total <= 0:
        raise ValueError("Spending profile must contain positive spending.")

    return [
        money(float(total_budget) * percentage / profile_total)
        for percentage in spending_profile
    ]


def calculate_schedule_cost(
    hourly_rate: Decimal,
    hours_per_day: float,
    duration_days: int,
) -> Decimal:
    if hourly_rate < 0 or hours_per_day < 0 or duration_days < 0:
        raise ValueError("Schedule cost inputs cannot be negative.")

    return money(float(hourly_rate) * hours_per_day * duration_days)


def sensitivity_analysis(
    base_cost: Decimal,
    variables: Dict[str, float],
) -> List[Tuple[str, Decimal]]:
    results = []

    for name, percentage_change in variables.items():
        adjusted = money(
            float(base_cost) * (1 + percentage_change / 100)
        )
        results.append((name, adjusted))

    return results


def monte_carlo_cost(
    estimate: ThreePointEstimate,
    iterations: int = 10000,
    seed: int = 42,
) -> Dict[str, float]:
    import random

    if iterations <= 0:
        raise ValueError("Iterations must be positive.")

    random.seed(seed)

    samples = []
    low = float(estimate.optimistic)
    mode = float(estimate.most_likely)
    high = float(estimate.pessimistic)

    for _ in range(iterations):
        samples.append(random.triangular(low, high, mode))

    samples.sort()

    def percentile(p: float) -> float:
        index = int((len(samples) - 1) * p)
        return samples[index]

    return {
        "mean": statistics.mean(samples),
        "median": statistics.median(samples),
        "p50": percentile(0.50),
        "p80": percentile(0.80),
        "p90": percentile(0.90),
        "minimum": samples[0],
        "maximum": samples[-1],
    }


def classify_budget_status(
    estimate: Decimal,
    approved_budget: Decimal,
) -> str:
    if approved_budget < 0:
        raise ValueError("Approved budget cannot be negative.")

    if estimate <= approved_budget:
        variance = approved_budget - estimate
        return f"WITHIN BUDGET; remaining reserve = {variance:,.2f}"

    variance = estimate - approved_budget
    return f"OVER BUDGET; required funding = {variance:,.2f}"


def export_estimate_to_json(
    estimate: ProjectEstimate,
    path: Path,
) -> None:
    payload = {
        "project": estimate.project_name,
        "direct_cost": str(estimate.direct_cost),
        "expected_risk_cost": str(estimate.expected_risk_cost),
        "management_reserve": str(estimate.contingency_reserve),
        "total_estimate": str(estimate.estimated_project_cost),
        "items": [
            {
                "name": item.name,
                "quantity": item.quantity,
                "unit_cost": str(item.unit_cost),
                "category": item.category,
                "total": str(item.total),
                "confidence": item.confidence,
            }
            for item in estimate.direct_items
        ],
        "risks": [
            {
                "name": risk.name,
                "probability": risk.probability,
                "impact": str(risk.impact),
                "expected_monetary_value": str(
                    risk.expected_monetary_value
                ),
            }
            for risk in estimate.risks
        ],
    }

    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def export_cost_items_to_csv(
    items: List[CostItem],
    path: Path,
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["name", "category", "quantity", "unit_cost", "total", "confidence"]
        )

        for item in items:
            writer.writerow(
                [
                    item.name,
                    item.category,
                    item.quantity,
                    item.unit_cost,
                    item.total,
                    item.confidence,
                ]
            )


def demonstrate_risk_and_reserve(
    estimate: ProjectEstimate,
) -> None:
    print("\n=== Risk-Based Cost Reserve ===")

    risks = [
        Risk(
            "Integration rework",
            probability=0.30,
            impact=money(18000),
            contingency_factor=1.0,
        ),
        Risk(
            "Cloud consumption above forecast",
            probability=0.20,
            impact=money(12000),
            contingency_factor=1.0,
        ),
        Risk(
            "Security remediation",
            probability=0.15,
            impact=money(30000),
            contingency_factor=1.0,
        ),
    ]

    for risk in risks:
        validate_risk(risk)
        estimate.risks.append(risk)
        print(
            f"{risk.name:35} EMV = "
            f"{risk.expected_monetary_value:,.2f}"
        )

    print(f"Expected risk cost:             {estimate.expected_risk_cost:,.2f}")
    print(f"Management reserve:              {estimate.contingency_reserve:,.2f}")
    print(f"Total estimated cost:            {estimate.estimated_project_cost:,.2f}")


def demonstrate_cost_controls() -> None:
    print("\n=== Cost Control and Forecasting ===")

    approved = money(185000)
    current_estimate = money(179500)
    actual_to_date = money(92000)
    remaining_forecast = money(91500)

    estimate_at_completion = money(
        float(actual_to_date) + float(remaining_forecast)
    )

    print(f"Approved budget:                {approved:,.2f}")
    print(f"Current estimate:               {current_estimate:,.2f}")
    print(f"Actual cost to date:            {actual_to_date:,.2f}")
    print(f"Remaining forecast:             {remaining_forecast:,.2f}")
    print(f"Estimate at completion:         {estimate_at_completion:,.2f}")
    print(
        "Budget status:                 ",
        classify_budget_status(estimate_at_completion, approved),
    )

    if estimate_at_completion > approved:
        print("Control action: review major cost drivers and reserve usage.")
    else:
        print("Control action: continue monitoring forecast variance.")


def demonstrate_schedule_impact() -> None:
    print("\n=== Schedule-Cost Relationship ===")

    engineering_rate = money(75)
    baseline_hours_per_day = 7.5
    baseline_days = 40
    delay_days = 8

    baseline = calculate_schedule_cost(
        engineering_rate,
        baseline_hours_per_day,
        baseline_days,
    )

    delayed = calculate_schedule_cost(
        engineering_rate,
        baseline_hours_per_day,
        baseline_days + delay_days,
    )

    delay_cost = delayed - baseline

    print(f"Baseline labor cost:            {baseline:,.2f}")
    print(f"Delayed labor cost:             {delayed:,.2f}")
    print(f"Incremental delay cost:         {delay_cost:,.2f}")


def demonstrate_sensitivity(base_cost: Decimal) -> None:
    print("\n=== Sensitivity Analysis ===")

    changes = {
        "Labor rate +10%": 10,
        "Cloud cost +20%": 20,
        "Labor efficiency -10%": 10,
        "Scope reduction -8%": -8,
    }

    for name, adjusted in sensitivity_analysis(base_cost, changes):
        delta = adjusted - base_cost
        print(f"{name:28} {adjusted:,.2f}  delta={delta:,.2f}")


def demonstrate_analogous_estimation() -> None:
    print("\n=== Analogous Estimation ===")

    history = [
        ("Asset portal A", money(140000), 0.85),
        ("Asset portal B", money(175000), 0.95),
        ("Asset portal C", money(220000), 0.60),
    ]

    weights = [project[2] for project in history]
    estimate = analogous_estimate(history, weights)

    print(f"Weighted historical estimate:  {estimate:,.2f}")


def demonstrate_monte_carlo() -> None:
    print("\n=== Probabilistic Cost Forecast ===")

    estimate = ThreePointEstimate(
        optimistic=money(120000),
        most_likely=money(160000),
        pessimistic=money(240000),
    )

    distribution = monte_carlo_cost(estimate, iterations=10000)

    for key, value in distribution.items():
        print(f"{key:12}: {value:,.2f}")


def demonstrate_edge_cases() -> None:
    print("\n=== Validation and Failure Conditions ===")

    invalid_items = [
        CostItem("Negative quantity", -5, money(100), "labor"),
        CostItem("Negative rate", 5, money(-100), "labor"),
    ]

    for item in invalid_items:
        try:
            validate_cost_item(item)
        except ValueError as exc:
            print(f"Rejected invalid item: {exc}")

    try:
        parametric_estimate(100, money(-2))
    except ValueError as exc:
        print(f"Rejected invalid parametric estimate: {exc}")

    try:
        ThreePointEstimate(
            money(100),
            money(80),
            money(50),
        )
        print(
            "Three-point ordering should be checked before production use."
        )
    except ValueError as exc:
        print(f"Rejected three-point input: {exc}")


def build_final_project_model() -> ProjectEstimate:
    project = ProjectEstimate(
        project_name="Public Infrastructure Monitoring Platform",
        management_reserve_rate=0.05,
    )

    categories = [
        CostItem("Requirements and process analysis", 120, money(90), "labor", 0.90),
        CostItem("Architecture and engineering", 100, money(110), "labor", 0.82),
        CostItem("Application development", 420, money(72), "labor", 0.85),
        CostItem("Testing and quality assurance", 180, money(58), "labor", 0.88),
        CostItem("Security validation", 60, money(105), "security", 0.76),
        CostItem("Cloud environment", 12, money(800), "infrastructure", 0.82),
        CostItem("User training", 10, money(650), "training", 0.90),
    ]

    for item in categories:
        validate_cost_item(item)
        project.direct_items.append(item)

    project.risks = [
        Risk("External system integration", 0.25, money(22000)),
        Risk("Unexpected infrastructure demand", 0.20, money(15000)),
        Risk("Security remediation", 0.15, money(28000)),
    ]

    for risk in project.risks:
        validate_risk(risk)

    return project


def main() -> None:
    print("PROJECT COST ESTIMATION WORKBENCH")

    basic = demonstrate_basic_cost_estimation()
    demonstrate_parametric_estimation()
    demonstrate_three_point_estimation()
    demonstrate_analogous_estimation()

    labor = calculate_labor_cost(
        {
            "Project manager": (80, money(95)),
            "Engineer": (240, money(72)),
            "QA analyst": (120, money(58)),
        }
    )
    print(f"\nLabor-only estimate:            {labor:,.2f}")

    monthly = simulate_monthly_burn(
        money(180000),
        6,
        [8, 12, 18, 25, 22, 15],
    )
    print("\nMonthly forecast:")
    for month, value in enumerate(monthly, start=1):
        print(f"Month {month}:                    {value:,.2f}")

    demonstrate_risk_and_reserve(basic)
    demonstrate_cost_controls()
    demonstrate_schedule_impact()
    demonstrate_sensitivity(basic.direct_cost)
    demonstrate_monte_carlo()
    demonstrate_edge_cases()

    final_project = build_final_project_model()

    print("\n=== Integrated Project Estimate ===")
    print(f"Project:                         {final_project.project_name}")
    print(f"Direct cost:                     {final_project.direct_cost:,.2f}")
    print(
        f"Expected risk cost:              "
        f"{final_project.expected_risk_cost:,.2f}"
    )
    print(
        f"Management reserve:              "
        f"{final_project.contingency_reserve:,.2f}"
    )
    print(
        f"Estimated project cost:          "
        f"{final_project.estimated_project_cost:,.2f}"
    )

    output_dir = Path("cost_estimation_output")
    output_dir.mkdir(exist_ok=True)

    export_estimate_to_json(
        final_project,
        output_dir / "project_estimate.json",
    )
    export_cost_items_to_csv(
        final_project.direct_items,
        output_dir / "cost_items.csv",
    )

    print(f"\nReports written to:              {output_dir.resolve()}")
    print("\nCost estimation workflow completed successfully.")


if __name__ == "__main__":
    main()
