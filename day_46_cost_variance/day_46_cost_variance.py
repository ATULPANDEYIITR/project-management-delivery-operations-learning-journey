from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Iterable
import csv
import json
import tempfile


MONEY_PLACES = Decimal("0.01")
PERCENT_PLACES = Decimal("0.01")


def money(value: Decimal | int | float | str) -> Decimal:
    """Convert a value to a two-decimal monetary Decimal."""
    try:
        return Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid monetary value: {value!r}") from exc


def percent(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(PERCENT_PLACES, rounding=ROUND_HALF_UP)


class VarianceStatus(Enum):
    FAVORABLE = "Favorable"
    UNFAVORABLE = "Unfavorable"
    ON_PLAN = "On plan"


@dataclass(frozen=True)
class CostLine:
    category: str
    planned_cost: Decimal
    actual_cost: Decimal

    def __post_init__(self) -> None:
        if not self.category.strip():
            raise ValueError("Cost category cannot be empty.")
        if self.planned_cost < 0 or self.actual_cost < 0:
            raise ValueError("Costs cannot be negative.")

    @property
    def variance(self) -> Decimal:
        # Positive variance means actual spending exceeded the plan.
        return money(self.actual_cost - self.planned_cost)

    @property
    def variance_percent(self) -> Decimal | None:
        if self.planned_cost == 0:
            return None
        return percent((self.variance / self.planned_cost) * Decimal("100"))

    @property
    def status(self) -> VarianceStatus:
        if self.variance > 0:
            return VarianceStatus.UNFAVORABLE
        if self.variance < 0:
            return VarianceStatus.FAVORABLE
        return VarianceStatus.ON_PLAN


@dataclass
class CostVarianceReport:
    lines: list[CostLine] = field(default_factory=list)

    def add_line(self, category: str, planned: Decimal | int | float | str,
                 actual: Decimal | int | float | str) -> None:
        self.lines.append(CostLine(category, money(planned), money(actual)))

    @property
    def planned_total(self) -> Decimal:
        return money(sum((line.planned_cost for line in self.lines), Decimal("0")))

    @property
    def actual_total(self) -> Decimal:
        return money(sum((line.actual_cost for line in self.lines), Decimal("0")))

    @property
    def total_variance(self) -> Decimal:
        return money(self.actual_total - self.planned_total)

    @property
    def total_variance_percent(self) -> Decimal | None:
        if self.planned_total == 0:
            return None
        return percent((self.total_variance / self.planned_total) * Decimal("100"))

    @property
    def status(self) -> VarianceStatus:
        if self.total_variance > 0:
            return VarianceStatus.UNFAVORABLE
        if self.total_variance < 0:
            return VarianceStatus.FAVORABLE
        return VarianceStatus.ON_PLAN

    def largest_unfavorable_lines(self, limit: int = 3) -> list[CostLine]:
        if limit < 1:
            raise ValueError("Limit must be positive.")
        return sorted(
            (line for line in self.lines if line.variance > 0),
            key=lambda line: line.variance,
            reverse=True,
        )[:limit]

    def largest_favorable_lines(self, limit: int = 3) -> list[CostLine]:
        if limit < 1:
            raise ValueError("Limit must be positive.")
        return sorted(
            (line for line in self.lines if line.variance < 0),
            key=lambda line: line.variance,
        )[:limit]

    def by_status(self, status: VarianceStatus) -> list[CostLine]:
        return [line for line in self.lines if line.status is status]

    def as_dict(self) -> dict:
        return {
            "planned_total": str(self.planned_total),
            "actual_total": str(self.actual_total),
            "variance": str(self.total_variance),
            "variance_percent": (
                str(self.total_variance_percent)
                if self.total_variance_percent is not None
                else None
            ),
            "status": self.status.value,
            "lines": [
                {
                    "category": line.category,
                    "planned": str(line.planned_cost),
                    "actual": str(line.actual_cost),
                    "variance": str(line.variance),
                    "variance_percent": (
                        str(line.variance_percent)
                        if line.variance_percent is not None
                        else None
                    ),
                    "status": line.status.value,
                }
                for line in self.lines
            ],
        }


def load_csv(path: Path) -> CostVarianceReport:
    report = CostVarianceReport()
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"category", "planned_cost", "actual_cost"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError(
                f"CSV must contain columns: {', '.join(sorted(required))}"
            )
        for row in reader:
            report.add_line(
                row["category"],
                row["planned_cost"],
                row["actual_cost"],
            )
    return report


def save_json(report: CostVarianceReport, path: Path) -> None:
    path.write_text(
        json.dumps(report.as_dict(), indent=2),
        encoding="utf-8",
    )


def print_report(report: CostVarianceReport) -> None:
    print("\nCOST VARIANCE REPORT")
    print("=" * 78)
    print(f"{'Category':<24} {'Planned':>12} {'Actual':>12} {'Variance':>12} {'%':>9}")
    print("-" * 78)

    for line in report.lines:
        variance_percent = (
            f"{line.variance_percent:.2f}%"
            if line.variance_percent is not None
            else "n/a"
        )
        print(
            f"{line.category:<24} "
            f"{line.planned_cost:>12.2f} "
            f"{line.actual_cost:>12.2f} "
            f"{line.variance:>12.2f} "
            f"{variance_percent:>9}"
        )

    print("-" * 78)
    total_percent = (
        f"{report.total_variance_percent:.2f}%"
        if report.total_variance_percent is not None
        else "n/a"
    )
    print(
        f"{'TOTAL':<24} "
        f"{report.planned_total:>12.2f} "
        f"{report.actual_total:>12.2f} "
        f"{report.total_variance:>12.2f} "
        f"{total_percent:>9}"
    )
    print(f"Status: {report.status.value}")

    print("\nLargest unfavorable variances")
    for line in report.largest_unfavorable_lines():
        print(f"  {line.category}: +{line.variance:.2f}")

    print("\nLargest favorable variances")
    for line in report.largest_favorable_lines():
        print(f"  {line.category}: {line.variance:.2f}")


def demonstrate_edge_cases() -> None:
    print("\nEDGE-CASE VALIDATION")
    print("=" * 78)

    zero_plan = CostLine("Unplanned Activity", money("0"), money("250"))
    print(
        f"{zero_plan.category}: planned={zero_plan.planned_cost:.2f}, "
        f"actual={zero_plan.actual_cost:.2f}, "
        f"variance={zero_plan.variance:.2f}, "
        f"percentage={zero_plan.variance_percent}"
    )

    try:
        CostLine("Invalid", money("-1"), money("20"))
    except ValueError as exc:
        print(f"Negative-cost validation: {exc}")

    try:
        money("not-a-number")
    except ValueError as exc:
        print(f"Invalid-number validation: {exc}")


def demonstrate_file_workflow() -> None:
    csv_content = """category,planned_cost,actual_cost
Cloud infrastructure,12000,13800
Contractors,30000,28750
Testing,8000,9200
Security tooling,6500,6100
Travel,3500,4200
"""

    with tempfile.TemporaryDirectory() as directory:
        directory_path = Path(directory)
        input_path = directory_path / "costs.csv"
        output_path = directory_path / "variance_report.json"

        input_path.write_text(csv_content, encoding="utf-8")
        report = load_csv(input_path)
        save_json(report, output_path)

        print("\nFILE-BASED WORKFLOW")
        print("=" * 78)
        print(f"Loaded: {input_path.name}")
        print(f"Saved: {output_path.name}")
        print(output_path.read_text(encoding="utf-8"))


def demonstrate_monthly_analysis() -> None:
    monthly_data = {
        "January": {"planned": "45000", "actual": "46800"},
        "February": {"planned": "47000", "actual": "46100"},
        "March": {"planned": "49000", "actual": "51250"},
        "April": {"planned": "51000", "actual": "50750"},
    }

    print("\nMONTHLY COST VARIANCE")
    print("=" * 78)

    cumulative_planned = Decimal("0")
    cumulative_actual = Decimal("0")

    for month, values in monthly_data.items():
        planned = money(values["planned"])
        actual = money(values["actual"])
        variance = money(actual - planned)
        cumulative_planned += planned
        cumulative_actual += actual
        ratio = (
            (variance / planned) * Decimal("100")
            if planned
            else None
        )
        print(
            f"{month:<10} planned={planned:>9.2f} "
            f"actual={actual:>9.2f} variance={variance:>9.2f} "
            f"rate={ratio:.2f}%"
        )

    cumulative_variance = money(cumulative_actual - cumulative_planned)
    print(
        f"Cumulative: planned={money(cumulative_planned):.2f}, "
        f"actual={money(cumulative_actual):.2f}, "
        f"variance={cumulative_variance:.2f}"
    )


def main() -> None:
    report = CostVarianceReport()

    # A realistic technology-project budget. Positive variance means
    # actual expenditure is above the approved plan.
    report.add_line("Cloud infrastructure", "12000", "13800")
    report.add_line("Contractors", "30000", "28750")
    report.add_line("Testing", "8000", "9200")
    report.add_line("Security tooling", "6500", "6100")
    report.add_line("Travel", "3500", "4200")
    report.add_line("Training", "5000", "4750")

    print_report(report)

    print("\nVARIANCE CLASSIFICATION")
    print("=" * 78)
    for status in VarianceStatus:
        lines = report.by_status(status)
        print(f"{status.value}: {len(lines)} cost lines")

    demonstrate_edge_cases()
    demonstrate_monthly_analysis()
    demonstrate_file_workflow()

    # A JSON artifact can be consumed by a dashboard, audit process,
    # or downstream reporting service without losing monetary precision.
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "cost_variance.json"
        save_json(report, output)
        print("\nREPORT ARTIFACT")
        print("=" * 78)
        print(output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
