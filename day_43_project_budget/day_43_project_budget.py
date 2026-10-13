"""
Project Budgeting: Creating, validating, monitoring, and forecasting a project budget.

This self-contained example models a realistic software implementation project.
It demonstrates budget categories, planned costs, committed costs, actual costs,
contingency, variance analysis, forecasting, change requests, approval rules,
and budget-health reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Iterable


MONEY = Decimal("0.01")


def money(value: Decimal | int | float | str) -> Decimal:
    """Convert a value to currency precision without using binary float arithmetic."""
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


class BudgetError(Exception):
    """Base exception for invalid budget operations."""


class BudgetStatus(Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    CLOSED = "closed"


class ChangeRequestStatus(Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class BudgetLine:
    category: str
    description: str
    planned: Decimal
    committed: Decimal = Decimal("0.00")
    actual: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        self.planned = money(self.planned)
        self.committed = money(self.committed)
        self.actual = money(self.actual)
        if self.planned < 0 or self.committed < 0 or self.actual < 0:
            raise BudgetError("Budget amounts cannot be negative.")

    @property
    def remaining(self) -> Decimal:
        return money(self.planned - self.actual)

    @property
    def forecast_variance(self) -> Decimal:
        return money(self.planned - self.committed)

    def record_commitment(self, amount: Decimal) -> None:
        amount = money(amount)
        if amount <= 0:
            raise BudgetError("A commitment must be positive.")
        self.committed = money(self.committed + amount)

    def record_actual(self, amount: Decimal) -> None:
        amount = money(amount)
        if amount <= 0:
            raise BudgetError("An actual expense must be positive.")
        self.actual = money(self.actual + amount)


@dataclass
class ChangeRequest:
    request_id: str
    description: str
    amount: Decimal
    status: ChangeRequestStatus = ChangeRequestStatus.PROPOSED

    def __post_init__(self) -> None:
        self.amount = money(self.amount)
        if self.amount <= 0:
            raise BudgetError("Change-request amount must be positive.")


@dataclass
class ProjectBudget:
    project_id: str
    project_name: str
    manager: str
    currency: str = "INR"
    contingency_rate: Decimal = Decimal("0.10")
    status: BudgetStatus = BudgetStatus.DRAFT
    lines: list[BudgetLine] = field(default_factory=list)
    change_requests: list[ChangeRequest] = field(default_factory=list)

    def add_line(self, line: BudgetLine) -> None:
        if self.status not in {BudgetStatus.DRAFT, BudgetStatus.ACTIVE}:
            raise BudgetError("Budget lines cannot be changed in the current status.")
        self.lines.append(line)

    @property
    def direct_budget(self) -> Decimal:
        return money(sum((line.planned for line in self.lines), Decimal("0")))

    @property
    def contingency(self) -> Decimal:
        return money(self.direct_budget * self.contingency_rate)

    @property
    def approved_changes(self) -> Decimal:
        return money(
            sum(
                (request.amount for request in self.change_requests
                 if request.status == ChangeRequestStatus.APPROVED),
                Decimal("0"),
            )
        )

    @property
    def total_authorized_budget(self) -> Decimal:
        return money(self.direct_budget + self.contingency + self.approved_changes)

    @property
    def actual_spend(self) -> Decimal:
        return money(sum((line.actual for line in self.lines), Decimal("0")))

    @property
    def committed_spend(self) -> Decimal:
        return money(sum((line.committed for line in self.lines), Decimal("0")))

    @property
    def projected_cost(self) -> Decimal:
        """
        A simple ETC model:
        projected cost = actual spend + remaining committed amounts.

        In a mature financial system, ETC would also include schedule,
        productivity, inflation, and risk-adjusted estimates.
        """
        remaining_commitments = money(
            sum(
                (
                    max(line.committed - line.actual, Decimal("0"))
                    for line in self.lines
                ),
                Decimal("0"),
            )
        )
        return money(self.actual_spend + remaining_commitments)

    def approve(self) -> None:
        if not self.lines:
            raise BudgetError("Cannot approve a budget without budget lines.")
        if self.direct_budget <= 0:
            raise BudgetError("Approved budget must be greater than zero.")
        self.status = BudgetStatus.APPROVED

    def activate(self) -> None:
        if self.status != BudgetStatus.APPROVED:
            raise BudgetError("Only an approved budget can become active.")
        self.status = BudgetStatus.ACTIVE

    def close(self) -> None:
        if self.status != BudgetStatus.ACTIVE:
            raise BudgetError("Only an active budget can be closed.")
        self.status = BudgetStatus.CLOSED

    def submit_change_request(self, request: ChangeRequest) -> None:
        if self.status != BudgetStatus.ACTIVE:
            raise BudgetError("Change requests require an active budget.")
        self.change_requests.append(request)

    def approve_change_request(self, request_id: str) -> None:
        for request in self.change_requests:
            if request.request_id == request_id:
                request.status = ChangeRequestStatus.APPROVED
                return
        raise BudgetError(f"Unknown change request: {request_id}")

    def variance(self) -> Decimal:
        return money(self.total_authorized_budget - self.actual_spend)

    def utilization(self) -> Decimal:
        if self.total_authorized_budget == 0:
            return Decimal("0")
        return (self.actual_spend / self.total_authorized_budget * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def category_report(self) -> list[dict[str, str]]:
        report = []
        for line in self.lines:
            variance = money(line.planned - line.actual)
            utilization = (
                Decimal("0")
                if line.planned == 0
                else (line.actual / line.planned * 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            )
            report.append(
                {
                    "category": line.category,
                    "description": line.description,
                    "planned": str(line.planned),
                    "actual": str(line.actual),
                    "variance": str(variance),
                    "utilization_percent": str(utilization),
                }
            )
        return report

    def health(self) -> str:
        utilization = self.utilization()
        projected = self.projected_cost
        authorized = self.total_authorized_budget

        if projected > authorized:
            return "OVER_BUDGET"
        if utilization >= Decimal("90"):
            return "CRITICAL"
        if utilization >= Decimal("75"):
            return "WATCH"
        return "HEALTHY"


def print_report(budget: ProjectBudget) -> None:
    print("\nPROJECT BUDGET REPORT")
    print("=" * 72)
    print(f"Project:             {budget.project_name}")
    print(f"Manager:             {budget.manager}")
    print(f"Status:              {budget.status.value}")
    print(f"Currency:            {budget.currency}")
    print(f"Direct budget:       {budget.direct_budget:,.2f}")
    print(f"Contingency:         {budget.contingency:,.2f}")
    print(f"Authorized budget:   {budget.total_authorized_budget:,.2f}")
    print(f"Actual spend:        {budget.actual_spend:,.2f}")
    print(f"Committed spend:     {budget.committed_spend:,.2f}")
    print(f"Projected cost:      {budget.projected_cost:,.2f}")
    print(f"Remaining variance:  {budget.variance():,.2f}")
    print(f"Utilization:         {budget.utilization()}%")
    print(f"Budget health:       {budget.health()}")

    print("\nCATEGORY ANALYSIS")
    for item in budget.category_report():
        print(
            f"{item['category']:15} "
            f"planned={item['planned']:>10} "
            f"actual={item['actual']:>10} "
            f"variance={item['variance']:>10} "
            f"usage={item['utilization_percent']:>7}%"
        )


def demonstrate_budget_creation() -> ProjectBudget:
    budget = ProjectBudget(
        project_id="PRJ-2026-042",
        project_name="Enterprise Data Platform",
        manager="Project Management Office",
        contingency_rate=Decimal("0.12"),
    )

    budget.add_line(
        BudgetLine(
            "Personnel",
            "Backend and data engineering effort",
            "4200000",
        )
    )
    budget.add_line(
        BudgetLine(
            "Cloud",
            "Compute, storage, networking, and managed services",
            "1350000",
        )
    )
    budget.add_line(
        BudgetLine(
            "Software",
            "Commercial development and security tooling",
            "650000",
        )
    )
    budget.add_line(
        BudgetLine(
            "Testing",
            "Performance, security, and integration testing",
            "500000",
        )
    )
    budget.add_line(
        BudgetLine(
            "Training",
            "Technical training and knowledge transfer",
            "300000",
        )
    )

    budget.approve()
    budget.activate()

    budget.lines[0].record_commitment("2800000")
    budget.lines[0].record_actual("2100000")

    budget.lines[1].record_commitment("850000")
    budget.lines[1].record_actual("640000")

    budget.lines[2].record_commitment("420000")
    budget.lines[2].record_actual("350000")

    budget.lines[3].record_commitment("190000")
    budget.lines[3].record_actual("130000")

    budget.lines[4].record_commitment("90000")
    budget.lines[4].record_actual("60000")

    change = ChangeRequest(
        "CR-001",
        "Additional security testing caused by expanded compliance scope",
        "240000",
    )
    budget.submit_change_request(change)
    budget.approve_change_request("CR-001")

    return budget


def demonstrate_edge_cases() -> None:
    print("\nVALIDATION AND FAILURE CASES")
    print("=" * 72)

    try:
        BudgetLine("Invalid", "Negative allocation", "-500")
    except BudgetError as exc:
        print(f"Rejected negative allocation: {exc}")

    try:
        empty = ProjectBudget("PRJ-X", "Invalid Project", "Manager")
        empty.approve()
    except BudgetError as exc:
        print(f"Rejected empty budget approval: {exc}")

    try:
        line = BudgetLine("Cloud", "Example", "10000")
        line.record_actual("-1")
    except BudgetError as exc:
        print(f"Rejected negative expense: {exc}")


def main() -> None:
    budget = demonstrate_budget_creation()
    print_report(budget)

    print("\nCHANGE CONTROL")
    print("=" * 72)
    for request in budget.change_requests:
        print(
            f"{request.request_id}: {request.description} | "
            f"{request.amount:,.2f} | {request.status.value}"
        )

    demonstrate_edge_cases()

    print("\nBUDGETING MECHANISM")
    print("=" * 72)
    print(
        "A project budget establishes an authorized financial baseline. "
        "Actual spending is compared with that baseline, while commitments "
        "indicate costs already contractually or operationally expected."
    )
    print(
        "Contingency is separated from direct planned costs so that identified "
        "budgetary uncertainty does not silently inflate ordinary cost estimates."
    )
    print(
        "Change requests provide controlled modification of the baseline rather "
        "than allowing untracked scope changes to appear as unexplained overruns."
    )


if __name__ == "__main__":
    main()
