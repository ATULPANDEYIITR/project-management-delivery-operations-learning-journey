from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
import csv
import json
from typing import Iterable


MONEY = Decimal("0.01")


def money(value: Decimal | int | float | str) -> Decimal:
    """Normalize monetary values to two decimal places."""
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


class CostType(Enum):
    LABOR = "labor"
    MATERIAL = "material"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    TRAVEL = "travel"
    SUBCONTRACT = "subcontract"
    OVERHEAD = "overhead"
    CONTINGENCY = "contingency"


class CostClassification(Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"


@dataclass(frozen=True)
class CostItem:
    name: str
    cost_type: CostType
    classification: CostClassification
    planned: Decimal
    actual: Decimal
    committed: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        if self.planned < 0 or self.actual < 0 or self.committed < 0:
            raise ValueError("Cost values cannot be negative.")

    @property
    def variance(self) -> Decimal:
        return money(self.planned - self.actual)

    @property
    def forecast(self) -> Decimal:
        # A simple forecast: actual spend plus outstanding commitments.
        return money(self.actual + self.committed)

    @property
    def utilization(self) -> Decimal:
        if self.planned == 0:
            return Decimal("0.00")
        return money((self.actual / self.planned) * Decimal("100"))


@dataclass
class ProjectBudget:
    name: str
    approved_budget: Decimal
    management_reserve: Decimal = Decimal("0.00")
    costs: list[CostItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.approved_budget = money(self.approved_budget)
        self.management_reserve = money(self.management_reserve)
        if self.approved_budget < 0 or self.management_reserve < 0:
            raise ValueError("Budget values cannot be negative.")

    def add_cost(self, item: CostItem) -> None:
        self.costs.append(item)

    @property
    def planned_cost(self) -> Decimal:
        return money(sum((item.planned for item in self.costs), Decimal("0")))

    @property
    def actual_cost(self) -> Decimal:
        return money(sum((item.actual for item in self.costs), Decimal("0")))

    @property
    def committed_cost(self) -> Decimal:
        return money(sum((item.committed for item in self.costs), Decimal("0")))

    @property
    def forecast_at_completion(self) -> Decimal:
        return money(self.actual_cost + self.committed_cost)

    @property
    def remaining_budget(self) -> Decimal:
        return money(self.approved_budget - self.actual_cost)

    @property
    def forecast_variance(self) -> Decimal:
        return money(self.approved_budget - self.forecast_at_completion)

    @property
    def budget_utilization(self) -> Decimal:
        if self.approved_budget == 0:
            return Decimal("0.00")
        return money((self.actual_cost / self.approved_budget) * Decimal("100"))

    @property
    def reserve_available(self) -> Decimal:
        return money(self.management_reserve - self.committed_cost)

    def direct_cost(self) -> Decimal:
        return money(
            sum(
                (
                    item.actual
                    for item in self.costs
                    if item.classification == CostClassification.DIRECT
                ),
                Decimal("0"),
            )
        )

    def indirect_cost(self) -> Decimal:
        return money(
            sum(
                (
                    item.actual
                    for item in self.costs
                    if item.classification == CostClassification.INDIRECT
                ),
                Decimal("0"),
            )
        )

    def cost_by_type(self) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}
        for item in self.costs:
            key = item.cost_type.value
            totals[key] = money(totals.get(key, Decimal("0")) + item.actual)
        return totals

    def validate(self) -> list[str]:
        errors: list[str] = []

        if self.actual_cost > self.approved_budget:
            errors.append("Actual project cost exceeds the approved budget.")

        if self.forecast_at_completion > self.approved_budget + self.management_reserve:
            errors.append(
                "Forecast cost exceeds the approved budget plus management reserve."
            )

        for item in self.costs:
            if item.actual > item.planned and item.planned > 0:
                errors.append(
                    f"{item.name}: actual spending is above its planned amount."
                )

        return errors

    def status(self) -> str:
        utilization = self.budget_utilization
        if self.actual_cost > self.approved_budget:
            return "OVER_BUDGET"
        if self.forecast_at_completion > self.approved_budget:
            return "FORECAST_OVER_BUDGET"
        if utilization >= Decimal("90"):
            return "HIGH_UTILIZATION"
        if utilization >= Decimal("75"):
            return "WATCH"
        return "WITHIN_PLAN"


def calculate_labor_cost(hours: Decimal, hourly_rate: Decimal) -> Decimal:
    if hours < 0 or hourly_rate < 0:
        raise ValueError("Hours and hourly rate cannot be negative.")
    return money(hours * hourly_rate)


def calculate_material_cost(quantity: Decimal, unit_cost: Decimal) -> Decimal:
    if quantity < 0 or unit_cost < 0:
        raise ValueError("Quantity and unit cost cannot be negative.")
    return money(quantity * unit_cost)


def calculate_contingency(base_cost: Decimal, rate: Decimal) -> Decimal:
    if base_cost < 0 or rate < 0:
        raise ValueError("Base cost and contingency rate cannot be negative.")
    return money(base_cost * rate / Decimal("100"))


def earned_value_metrics(
    budget_at_completion: Decimal,
    planned_value: Decimal,
    earned_value: Decimal,
    actual_cost: Decimal,
) -> dict[str, Decimal | None]:
    """
    Calculate introductory earned-value metrics.

    CPI = EV / AC
    SPI = EV / PV
    EAC = BAC / CPI when CPI is positive
    """
    bac = money(budget_at_completion)
    pv = money(planned_value)
    ev = money(earned_value)
    ac = money(actual_cost)

    cpi = None if ac == 0 else (ev / ac).quantize(MONEY)
    spi = None if pv == 0 else (ev / pv).quantize(MONEY)
    eac = None
    if cpi is not None and cpi > 0:
        eac = (bac / cpi).quantize(MONEY)

    return {
        "BAC": bac,
        "PV": pv,
        "EV": ev,
        "AC": ac,
        "CPI": cpi,
        "SPI": spi,
        "EAC": eac,
        "VAC": None if eac is None else money(bac - eac),
    }


def print_project_report(project: ProjectBudget) -> None:
    print("\n=== PROJECT COST MANAGEMENT REPORT ===")
    print(f"Project: {project.name}")
    print(f"Approved budget:       {project.approved_budget:,.2f}")
    print(f"Management reserve:    {project.management_reserve:,.2f}")
    print(f"Planned cost:          {project.planned_cost:,.2f}")
    print(f"Actual cost:           {project.actual_cost:,.2f}")
    print(f"Committed cost:        {project.committed_cost:,.2f}")
    print(f"Forecast at completion:{project.forecast_at_completion:,.2f}")
    print(f"Remaining budget:      {project.remaining_budget:,.2f}")
    print(f"Forecast variance:     {project.forecast_variance:,.2f}")
    print(f"Budget utilization:    {project.budget_utilization:,.2f}%")
    print(f"Status:                {project.status()}")

    print("\nCost items:")
    for item in project.costs:
        print(
            f"  {item.name:<24}"
            f" planned={item.planned:>9,.2f}"
            f" actual={item.actual:>9,.2f}"
            f" committed={item.committed:>9,.2f}"
            f" variance={item.variance:>9,.2f}"
        )

    print("\nActual cost by type:")
    for category, total in project.cost_by_type().items():
        print(f"  {category:<15} {total:>10,.2f}")

    errors = project.validate()
    print("\nCost controls:")
    if errors:
        for error in errors:
            print(f"  WARNING: {error}")
    else:
        print("  No budget control violations detected.")


def export_costs_csv(project: ProjectBudget, output_file: Path) -> None:
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "name",
                "cost_type",
                "classification",
                "planned",
                "actual",
                "committed",
                "variance",
                "forecast",
            ]
        )
        for item in project.costs:
            writer.writerow(
                [
                    item.name,
                    item.cost_type.value,
                    item.classification.value,
                    str(item.planned),
                    str(item.actual),
                    str(item.committed),
                    str(item.variance),
                    str(item.forecast),
                ]
            )


def export_summary_json(project: ProjectBudget, output_file: Path) -> None:
    summary = {
        "project": project.name,
        "approved_budget": str(project.approved_budget),
        "management_reserve": str(project.management_reserve),
        "planned_cost": str(project.planned_cost),
        "actual_cost": str(project.actual_cost),
        "committed_cost": str(project.committed_cost),
        "forecast_at_completion": str(project.forecast_at_completion),
        "remaining_budget": str(project.remaining_budget),
        "forecast_variance": str(project.forecast_variance),
        "budget_utilization_percent": str(project.budget_utilization),
        "status": project.status(),
        "cost_by_type": {
            key: str(value) for key, value in project.cost_by_type().items()
        },
        "validation_errors": project.validate(),
    }
    output_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def build_example_project() -> ProjectBudget:
    project = ProjectBudget(
        name="Customer Data Platform Upgrade",
        approved_budget=Decimal("180000"),
        management_reserve=Decimal("15000"),
    )

    project.add_cost(
        CostItem(
            "Business analysis",
            CostType.LABOR,
            CostClassification.DIRECT,
            Decimal("24000"),
            Decimal("22000"),
            Decimal("1000"),
        )
    )
    project.add_cost(
        CostItem(
            "Software engineering",
            CostType.LABOR,
            CostClassification.DIRECT,
            Decimal("65000"),
            Decimal("72000"),
            Decimal("6000"),
        )
    )
    project.add_cost(
        CostItem(
            "Cloud infrastructure",
            CostType.EQUIPMENT,
            CostClassification.DIRECT,
            Decimal("30000"),
            Decimal("28000"),
            Decimal("5000"),
        )
    )
    project.add_cost(
        CostItem(
            "Database licenses",
            CostType.SOFTWARE,
            CostClassification.DIRECT,
            Decimal("18000"),
            Decimal("18500"),
            Decimal("0"),
        )
    )
    project.add_cost(
        CostItem(
            "Implementation partner",
            CostType.SUBCONTRACT,
            CostClassification.DIRECT,
            Decimal("22000"),
            Decimal("19000"),
            Decimal("7000"),
        )
    )
    project.add_cost(
        CostItem(
            "Project travel",
            CostType.TRAVEL,
            CostClassification.DIRECT,
            Decimal("7000"),
            Decimal("4500"),
            Decimal("500"),
        )
    )
    project.add_cost(
        CostItem(
            "Corporate allocation",
            CostType.OVERHEAD,
            CostClassification.INDIRECT,
            Decimal("9000"),
            Decimal("8000"),
            Decimal("0"),
        )
    )
    return project


def run_validation_examples() -> None:
    print("\n=== COST ESTIMATION EXAMPLES ===")

    engineering_cost = calculate_labor_cost(
        Decimal("960"),
        Decimal("75"),
    )
    server_cost = calculate_material_cost(
        Decimal("12"),
        Decimal("1450"),
    )
    contingency = calculate_contingency(
        engineering_cost + server_cost,
        Decimal("10"),
    )

    print(f"Engineering labor: {engineering_cost:,.2f}")
    print(f"Server procurement: {server_cost:,.2f}")
    print(f"10% contingency: {contingency:,.2f}")

    try:
        calculate_labor_cost(Decimal("-1"), Decimal("75"))
    except ValueError as exc:
        print(f"Rejected invalid labor input: {exc}")


def run_earned_value_example() -> None:
    print("\n=== EARNED VALUE SNAPSHOT ===")

    metrics = earned_value_metrics(
        budget_at_completion=Decimal("180000"),
        planned_value=Decimal("95000"),
        earned_value=Decimal("87000"),
        actual_cost=Decimal("102000"),
    )

    for key, value in metrics.items():
        print(f"{key}: {value}")


def main() -> None:
    project = build_example_project()

    print("Cost management begins with establishing what the project is expected to cost,")
    print("recording actual spending, identifying commitments, and comparing results")
    print("with the approved budget.")

    run_validation_examples()
    print_project_report(project)
    run_earned_value_example()

    export_dir = Path("cost_management_output")
    export_dir.mkdir(exist_ok=True)

    export_costs_csv(project, export_dir / "project_costs.csv")
    export_summary_json(project, export_dir / "cost_summary.json")

    print("\nReports written to:")
    print(f"  {export_dir / 'project_costs.csv'}")
    print(f"  {export_dir / 'cost_summary.json'}")


if __name__ == "__main__":
    main()
