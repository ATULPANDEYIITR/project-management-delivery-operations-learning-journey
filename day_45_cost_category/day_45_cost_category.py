from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
import csv
import json
import statistics
from collections import defaultdict


class CostCategory(str, Enum):
    LABOR = "labor"
    SOFTWARE = "software"
    CLOUD = "cloud"
    EQUIPMENT = "equipment"
    TRAVEL = "travel"
    CONTRACTOR = "contractor"
    MATERIALS = "materials"
    OTHER = "other"


class CostStatus(str, Enum):
    PLANNED = "planned"
    COMMITTED = "committed"
    ACTUAL = "actual"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class BudgetLine:
    category: CostCategory
    budget: Decimal


@dataclass
class Expense:
    expense_id: str
    project_id: str
    category: CostCategory
    description: str
    amount: Decimal
    expense_date: date
    vendor: str
    status: CostStatus = CostStatus.ACTUAL
    approved: bool = False
    invoice_number: str | None = None

    def __post_init__(self) -> None:
        if self.amount <= Decimal("0"):
            raise ValueError("Expense amount must be positive.")
        if not self.description.strip():
            raise ValueError("Expense description cannot be empty.")
        if not self.vendor.strip():
            raise ValueError("Vendor cannot be empty.")


@dataclass
class Project:
    project_id: str
    name: str
    start_date: date
    end_date: date
    budget_lines: dict[CostCategory, Decimal]
    expenses: list[Expense] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("Project end date cannot precede start date.")
        if not self.budget_lines:
            raise ValueError("At least one budget category is required.")
        if any(amount < Decimal("0") for amount in self.budget_lines.values()):
            raise ValueError("Budget values cannot be negative.")

    @property
    def total_budget(self) -> Decimal:
        return sum(self.budget_lines.values(), Decimal("0"))

    @property
    def total_actual(self) -> Decimal:
        return sum(
            expense.amount
            for expense in self.expenses
            if expense.status == CostStatus.ACTUAL
        )

    def add_expense(self, expense: Expense) -> None:
        if expense.project_id != self.project_id:
            raise ValueError("Expense belongs to a different project.")
        if not self.start_date <= expense.expense_date <= self.end_date:
            raise ValueError("Expense date falls outside the project period.")
        if any(existing.expense_id == expense.expense_id for existing in self.expenses):
            raise ValueError(f"Duplicate expense ID: {expense.expense_id}")
        self.expenses.append(expense)

    def category_actual(self) -> dict[CostCategory, Decimal]:
        totals = defaultdict(lambda: Decimal("0"))
        for expense in self.expenses:
            if expense.status == CostStatus.ACTUAL:
                totals[expense.category] += expense.amount
        return dict(totals)

    def category_variance(self) -> dict[CostCategory, Decimal]:
        actual = self.category_actual()
        categories = set(self.budget_lines) | set(actual)
        return {
            category: self.budget_lines.get(category, Decimal("0"))
            - actual.get(category, Decimal("0"))
            for category in categories
        }

    def utilization(self) -> Decimal:
        if self.total_budget == Decimal("0"):
            return Decimal("0")
        return (self.total_actual / self.total_budget) * Decimal("100")


class CostTracker:
    """Coordinates project-level cost analysis and operational controls."""

    def __init__(self) -> None:
        self.projects: dict[str, Project] = {}

    def add_project(self, project: Project) -> None:
        if project.project_id in self.projects:
            raise ValueError(f"Project already exists: {project.project_id}")
        self.projects[project.project_id] = project

    def record_expense(self, expense: Expense) -> None:
        if expense.project_id not in self.projects:
            raise KeyError(f"Unknown project: {expense.project_id}")
        self.projects[expense.project_id].add_expense(expense)

    def budget_alerts(self, project_id: str, threshold: Decimal = Decimal("80")) -> list[str]:
        project = self.projects[project_id]
        alerts: list[str] = []
        actual = project.category_actual()

        for category, budget in project.budget_lines.items():
            spent = actual.get(category, Decimal("0"))
            if budget == Decimal("0"):
                if spent > 0:
                    alerts.append(
                        f"{category.value}: {spent:.2f} spent against zero budget"
                    )
                continue

            utilization = spent / budget * Decimal("100")
            if utilization >= threshold:
                alerts.append(
                    f"{category.value}: {utilization:.1f}% of budget consumed"
                )

        if project.total_actual > project.total_budget:
            alerts.append(
                f"PROJECT OVERRUN: actual {project.total_actual:.2f} "
                f"exceeds budget {project.total_budget:.2f}"
            )
        return alerts

    def monthly_actuals(self, project_id: str) -> dict[str, Decimal]:
        project = self.projects[project_id]
        totals = defaultdict(lambda: Decimal("0"))

        for expense in project.expenses:
            if expense.status == CostStatus.ACTUAL:
                month = expense.expense_date.strftime("%Y-%m")
                totals[month] += expense.amount

        return dict(sorted(totals.items()))

    def forecast(self, project_id: str, as_of: date | None = None) -> Decimal:
        project = self.projects[project_id]
        as_of = as_of or date.today()

        elapsed_days = max(
            1,
            min((as_of - project.start_date).days + 1,
                (project.end_date - project.start_date).days + 1),
        )
        total_days = max(1, (project.end_date - project.start_date).days + 1)

        actual = project.total_actual

        if as_of <= project.start_date:
            return Decimal("0")

        if elapsed_days >= total_days:
            return actual

        daily_rate = actual / Decimal(elapsed_days)
        return daily_rate * Decimal(total_days)

    def cost_per_vendor(self, project_id: str) -> dict[str, Decimal]:
        totals = defaultdict(lambda: Decimal("0"))
        for expense in self.projects[project_id].expenses:
            if expense.status == CostStatus.ACTUAL:
                totals[expense.vendor] += expense.amount
        return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))

    def expense_quality_checks(self, project_id: str) -> list[str]:
        project = self.projects[project_id]
        issues: list[str] = []

        seen_invoices: set[str] = set()
        for expense in project.expenses:
            if expense.amount > Decimal("10000") and not expense.approved:
                issues.append(
                    f"{expense.expense_id}: high-value expense lacks approval"
                )

            if expense.invoice_number:
                if expense.invoice_number in seen_invoices:
                    issues.append(
                        f"{expense.expense_id}: duplicate invoice "
                        f"{expense.invoice_number}"
                    )
                seen_invoices.add(expense.invoice_number)

        return issues

    def export_csv(self, project_id: str, path: str | Path) -> None:
        project = self.projects[project_id]
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "expense_id",
                    "project_id",
                    "category",
                    "description",
                    "amount",
                    "expense_date",
                    "vendor",
                    "status",
                    "approved",
                    "invoice_number",
                ],
            )
            writer.writeheader()
            for expense in project.expenses:
                writer.writerow(
                    {
                        "expense_id": expense.expense_id,
                        "project_id": expense.project_id,
                        "category": expense.category.value,
                        "description": expense.description,
                        "amount": str(expense.amount),
                        "expense_date": expense.expense_date.isoformat(),
                        "vendor": expense.vendor,
                        "status": expense.status.value,
                        "approved": expense.approved,
                        "invoice_number": expense.invoice_number or "",
                    }
                )

    def export_report(self, project_id: str, path: str | Path) -> None:
        project = self.projects[project_id]
        report = {
            "project": {
                "id": project.project_id,
                "name": project.name,
                "budget": str(project.total_budget),
                "actual": str(project.total_actual),
                "variance": str(project.total_budget - project.total_actual),
                "utilization_percent": str(project.utilization()),
            },
            "category_variance": {
                category.value: str(amount)
                for category, amount in project.category_variance().items()
            },
            "monthly_actuals": {
                month: str(amount)
                for month, amount in self.monthly_actuals(project_id).items()
            },
            "forecast": str(self.forecast(project_id)),
            "alerts": self.budget_alerts(project_id),
            "data_quality_issues": self.expense_quality_checks(project_id),
        }

        Path(path).write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )


def money(value: str | int | float | Decimal) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid monetary value: {value}") from exc


def build_demo_tracker() -> CostTracker:
    tracker = CostTracker()

    project = Project(
        project_id="PRJ-2026-001",
        name="Enterprise Data Platform",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        budget_lines={
            CostCategory.LABOR: money("180000"),
            CostCategory.CLOUD: money("60000"),
            CostCategory.SOFTWARE: money("30000"),
            CostCategory.EQUIPMENT: money("45000"),
            CostCategory.TRAVEL: money("20000"),
            CostCategory.CONTRACTOR: money("50000"),
        },
    )
    tracker.add_project(project)

    sample_expenses = [
        Expense(
            "EXP-001", "PRJ-2026-001", CostCategory.LABOR,
            "January engineering payroll allocation", money("28000"),
            date(2026, 1, 31), "Internal Engineering", approved=True
        ),
        Expense(
            "EXP-002", "PRJ-2026-001", CostCategory.CLOUD,
            "January production cloud usage", money("7200"),
            date(2026, 1, 31), "Cloud Provider", approved=True,
            invoice_number="CLOUD-2026-01"
        ),
        Expense(
            "EXP-003", "PRJ-2026-001", CostCategory.SOFTWARE,
            "Developer IDE and security licenses", money("8400"),
            date(2026, 2, 5), "Software Vendor", approved=True,
            invoice_number="SW-8821"
        ),
        Expense(
            "EXP-004", "PRJ-2026-001", CostCategory.EQUIPMENT,
            "Staging database servers", money("18500"),
            date(2026, 2, 20), "Hardware Supplier", approved=True,
            invoice_number="HW-1044"
        ),
        Expense(
            "EXP-005", "PRJ-2026-001", CostCategory.CONTRACTOR,
            "Security architecture assessment", money("12500"),
            date(2026, 3, 15), "Security Consultancy", approved=False,
            invoice_number="SEC-0315"
        ),
        Expense(
            "EXP-006", "PRJ-2026-001", CostCategory.CLOUD,
            "February cloud consumption", money("9100"),
            date(2026, 2, 28), "Cloud Provider", approved=True,
            invoice_number="CLOUD-2026-02"
        ),
        Expense(
            "EXP-007", "PRJ-2026-001", CostCategory.TRAVEL,
            "Architecture workshop travel", money("6200"),
            date(2026, 3, 10), "Travel Agency", approved=True,
            invoice_number="TR-0310"
        ),
    ]

    for expense in sample_expenses:
        tracker.record_expense(expense)

    return tracker


def print_report(tracker: CostTracker, project_id: str) -> None:
    project = tracker.projects[project_id]

    print("\n=== PROJECT COST DASHBOARD ===")
    print(f"Project: {project.name}")
    print(f"Budget:  {project.total_budget:,.2f}")
    print(f"Actual:  {project.total_actual:,.2f}")
    print(f"Variance: {project.total_budget - project.total_actual:,.2f}")
    print(f"Utilization: {project.utilization():.2f}%")
    print(f"Forecast at project completion: {tracker.forecast(project_id):,.2f}")

    print("\nCategory analysis:")
    actual = project.category_actual()
    for category in sorted(
        set(project.budget_lines) | set(actual),
        key=lambda item: item.value,
    ):
        budget = project.budget_lines.get(category, Decimal("0"))
        spent = actual.get(category, Decimal("0"))
        variance = budget - spent
        print(
            f"  {category.value:12} "
            f"budget={budget:>10,.2f} "
            f"actual={spent:>10,.2f} "
            f"variance={variance:>10,.2f}"
        )

    print("\nMonthly actuals:")
    for month, amount in tracker.monthly_actuals(project_id).items():
        print(f"  {month}: {amount:,.2f}")

    print("\nVendor exposure:")
    for vendor, amount in tracker.cost_per_vendor(project_id).items():
        print(f"  {vendor}: {amount:,.2f}")

    print("\nBudget alerts:")
    alerts = tracker.budget_alerts(project_id)
    if alerts:
        for alert in alerts:
            print(f"  {alert}")
    else:
        print("  No threshold alerts.")

    print("\nData quality checks:")
    issues = tracker.expense_quality_checks(project_id)
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print("  No data quality issues.")


def demonstrate_edge_cases() -> None:
    print("\n=== VALIDATION AND EDGE CASES ===")

    try:
        Expense(
            "BAD-001", "PRJ-2026-001", CostCategory.CLOUD,
            "Negative cloud adjustment", money("-50"),
            date(2026, 5, 1), "Cloud Provider"
        )
    except ValueError as exc:
        print(f"Rejected invalid amount: {exc}")

    try:
        Project(
            "BAD-PROJECT",
            "Invalid Project",
            date(2026, 12, 31),
            date(2026, 1, 1),
            {CostCategory.LABOR: money("1000")},
        )
    except ValueError as exc:
        print(f"Rejected invalid project dates: {exc}")

    try:
        tracker = CostTracker()
        tracker.add_project(
            Project(
                "DUP",
                "Duplicate Test",
                date(2026, 1, 1),
                date(2026, 1, 2),
                {CostCategory.LABOR: money("100")},
            )
        )
        tracker.add_project(
            Project(
                "DUP",
                "Duplicate Test Again",
                date(2026, 1, 1),
                date(2026, 1, 2),
                {CostCategory.LABOR: money("100")},
            )
        )
    except ValueError as exc:
        print(f"Rejected duplicate project: {exc}")


def main() -> None:
    tracker = build_demo_tracker()
    project_id = "PRJ-2026-001"

    print_report(tracker, project_id)
    demonstrate_edge_cases()

    output_directory = Path("cost_tracking_output")
    output_directory.mkdir(exist_ok=True)

    tracker.export_csv(
        project_id,
        output_directory / "project_expenses.csv",
    )
    tracker.export_report(
        project_id,
        output_directory / "cost_report.json",
    )

    print(f"\nReports written to: {output_directory.resolve()}")

    project = tracker.projects[project_id]
    monthly_values = list(tracker.monthly_actuals(project_id).values())
    if len(monthly_values) > 1:
        average_monthly_cost = statistics.mean(monthly_values)
        print(f"Average monthly actual cost: {average_monthly_cost:,.2f}")


if __name__ == "__main__":
    main()
