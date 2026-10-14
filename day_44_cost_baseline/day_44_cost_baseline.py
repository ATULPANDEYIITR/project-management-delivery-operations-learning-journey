"""
Cost Baseline: Understanding Planned Spending

A cost baseline is the approved, time-phased budget used to measure and
control project cost performance. It represents planned spending across
the project schedule and provides the reference against which actual costs
and earned value are compared.

This executable case study models a government infrastructure project,
including work packages, monthly budgets, baseline approval, actual costs,
earned value, cost variance, schedule variance, estimate at completion,
change control, and audit reporting.

Run with Python 3.10 or later:
    python cost_baseline.py

Only the Python standard library is required.
"""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Iterable


CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value: Decimal | int | str) -> Decimal:
    """Normalize monetary values without introducing binary float errors."""
    try:
        result = Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid monetary value: {value!r}") from exc

    if not result.is_finite():
        raise ValueError("Monetary values must be finite.")

    if result < ZERO:
        raise ValueError("Monetary values cannot be negative.")

    return result


def signed_money(value: Decimal) -> str:
    """Format signed variances while preserving their financial meaning."""
    normalized = value.quantize(CENT, rounding=ROUND_HALF_UP)
    return f"-₹{abs(normalized):,.2f}" if normalized < ZERO else f"₹{normalized:,.2f}"


class BaselineStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class WorkPackage:
    code: str
    name: str
    planned_value: Decimal

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.name.strip():
            raise ValueError("Work package code and name are required.")
        object.__setattr__(self, "planned_value", money(self.planned_value))


@dataclass(frozen=True)
class MonthlyBudget:
    period: str
    work_package_code: str
    amount: Decimal

    def __post_init__(self) -> None:
        try:
            date.fromisoformat(self.period + "-01")
        except ValueError as exc:
            raise ValueError(f"Invalid budget period: {self.period}") from exc

        object.__setattr__(self, "amount", money(self.amount))


@dataclass(frozen=True)
class CostEntry:
    entry_id: str
    period: str
    work_package_code: str
    amount: Decimal
    description: str
    approved: bool = True

    def __post_init__(self) -> None:
        if not self.entry_id.strip():
            raise ValueError("Cost entry ID is required.")
        if not self.description.strip():
            raise ValueError("Cost description is required.")

        try:
            date.fromisoformat(self.period + "-01")
        except ValueError as exc:
            raise ValueError(f"Invalid actual-cost period: {self.period}") from exc

        object.__setattr__(self, "amount", money(self.amount))


@dataclass(frozen=True)
class ProgressEntry:
    period: str
    work_package_code: str
    completion_percent: Decimal

    def __post_init__(self) -> None:
        percent = Decimal(str(self.completion_percent))
        if not percent.is_finite() or not ZERO <= percent <= Decimal("100"):
            raise ValueError("Completion percentage must be between 0 and 100.")
        object.__setattr__(self, "completion_percent", percent)


@dataclass
class ChangeRequest:
    request_id: str
    description: str
    amount_delta: Decimal
    effective_period: str
    status: str = "PENDING"
    decision_note: str = ""

    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.description.strip():
            raise ValueError("Change request ID and description are required.")
        self.amount_delta = Decimal(str(self.amount_delta)).quantize(CENT)

        if not self.amount_delta.is_finite():
            raise ValueError("Change amount must be finite.")

        try:
            date.fromisoformat(self.effective_period + "-01")
        except ValueError as exc:
            raise ValueError("Invalid change effective period.") from exc


@dataclass
class CostBaseline:
    baseline_id: str
    project_name: str
    currency: str
    work_packages: dict[str, WorkPackage]
    monthly_budgets: list[MonthlyBudget]
    status: BaselineStatus = BaselineStatus.DRAFT
    approved_by: str | None = None
    approved_on: date | None = None
    revision: int = 1

    def __post_init__(self) -> None:
        if not self.baseline_id.strip() or not self.project_name.strip():
            raise ValueError("Baseline ID and project name are required.")
        if self.currency != "INR":
            raise ValueError("This case study uses INR as its reporting currency.")
        if not self.work_packages:
            raise ValueError("At least one work package is required.")

        for package in self.work_packages.values():
            if package.code not in self.work_packages:
                raise ValueError("Work package dictionary keys must match codes.")

        for budget in self.monthly_budgets:
            if budget.work_package_code not in self.work_packages:
                raise ValueError(
                    f"Unknown work package: {budget.work_package_code}"
                )

    @property
    def total_budget(self) -> Decimal:
        return sum((item.amount for item in self.monthly_budgets), ZERO)

    def budget_by_period(self) -> dict[str, Decimal]:
        result: dict[str, Decimal] = {}
        for item in self.monthly_budgets:
            result[item.period] = result.get(item.period, ZERO) + item.amount
        return dict(sorted(result.items()))

    def budget_by_package(self) -> dict[str, Decimal]:
        result = {code: ZERO for code in self.work_packages}
        for item in self.monthly_budgets:
            result[item.work_package_code] += item.amount
        return result

    def validate(self) -> None:
        """Check that the time-phased budget agrees with the package estimates."""
        package_budgets = self.budget_by_package()

        for code, package in self.work_packages.items():
            if package_budgets[code] != package.planned_value:
                raise ValueError(
                    f"{code}: monthly allocation {package_budgets[code]} "
                    f"does not match package estimate {package.planned_value}."
                )

        if self.total_budget <= ZERO:
            raise ValueError("The baseline must contain positive planned spending.")

        periods = self.budget_by_period()
        if not periods:
            raise ValueError("The baseline must include at least one period.")

    def approve(self, approver: str, approval_date: date) -> None:
        if self.status != BaselineStatus.DRAFT:
            raise ValueError("Only a draft baseline can be approved.")
        if not approver.strip():
            raise ValueError("An approver is required.")

        self.validate()
        self.status = BaselineStatus.APPROVED
        self.approved_by = approver
        self.approved_on = approval_date

    def create_revision(
        self,
        revision_id: str,
        additional_budget: Decimal,
        effective_period: str,
    ) -> CostBaseline:
        """Return a separate draft revision rather than silently changing an approved baseline."""
        if self.status != BaselineStatus.APPROVED:
            raise ValueError("Only an approved baseline can be revised.")

        delta = Decimal(str(additional_budget)).quantize(CENT)
        if not delta.is_finite():
            raise ValueError("Revision amount must be finite.")

        if delta < ZERO:
            raise ValueError("Use an explicit budget-reduction change for negative revisions.")

        if delta == ZERO:
            raise ValueError("A revision must change the approved budget.")

        try:
            date.fromisoformat(effective_period + "-01")
        except ValueError as exc:
            raise ValueError("Invalid revision effective period.") from exc

        updated_packages = dict(self.work_packages)
        first_package = next(iter(updated_packages.values()))
        updated_packages[first_package.code] = WorkPackage(
            first_package.code,
            first_package.name,
            first_package.planned_value + delta,
        )

        revised_budgets = list(self.monthly_budgets)
        revised_budgets.append(
            MonthlyBudget(effective_period, first_package.code, delta)
        )

        return CostBaseline(
            baseline_id=revision_id,
            project_name=self.project_name,
            currency=self.currency,
            work_packages=updated_packages,
            monthly_budgets=revised_budgets,
            revision=self.revision + 1,
        )


@dataclass
class ProjectControls:
    baseline: CostBaseline
    actual_costs: list[CostEntry] = field(default_factory=list)
    progress_entries: list[ProgressEntry] = field(default_factory=list)
    change_requests: list[ChangeRequest] = field(default_factory=list)

    def _require_approved_baseline(self) -> None:
        if self.baseline.status != BaselineStatus.APPROVED:
            raise ValueError("Cost performance requires an approved baseline.")

    def add_actual_cost(self, entry: CostEntry) -> None:
        self._require_approved_baseline()

        if entry.work_package_code not in self.baseline.work_packages:
            raise ValueError("Actual cost references an unknown work package.")

        if any(existing.entry_id == entry.entry_id for existing in self.actual_costs):
            raise ValueError(f"Duplicate cost entry ID: {entry.entry_id}")

        if entry.approved:
            self.actual_costs.append(entry)

    def record_progress(self, entry: ProgressEntry) -> None:
        self._require_approved_baseline()

        if entry.work_package_code not in self.baseline.work_packages:
            raise ValueError("Progress references an unknown work package.")

        existing = [
            item
            for item in self.progress_entries
            if item.period == entry.period
            and item.work_package_code == entry.work_package_code
        ]

        if existing and entry.completion_percent < existing[-1].completion_percent:
            raise ValueError("Cumulative completion cannot decrease.")

        if existing:
            self.progress_entries.remove(existing[-1])

        self.progress_entries.append(entry)

    def cumulative_planned_value(self, period: str) -> Decimal:
        return sum(
            (
                amount
                for month, amount in self.baseline.budget_by_period().items()
                if month <= period
            ),
            ZERO,
        )

    def cumulative_actual_cost(self, period: str) -> Decimal:
        return sum(
            (
                entry.amount
                for entry in self.actual_costs
                if entry.approved and entry.period <= period
            ),
            ZERO,
        )

    def earned_value(self, period: str) -> Decimal:
        """Calculate budgeted value of completed work, not the money spent."""
        result = ZERO
        latest: dict[str, ProgressEntry] = {}

        for entry in sorted(self.progress_entries, key=lambda item: item.period):
            if entry.period <= period:
                latest[entry.work_package_code] = entry

        for code, progress in latest.items():
            package_budget = self.baseline.work_packages[code].planned_value
            result += (
                package_budget * progress.completion_percent / Decimal("100")
            ).quantize(CENT, rounding=ROUND_HALF_UP)

        return result

    def metrics(self, period: str) -> dict[str, Decimal | None]:
        self._require_approved_baseline()

        pv = self.cumulative_planned_value(period)
        ac = self.cumulative_actual_cost(period)
        ev = self.earned_value(period)

        # Positive CV means under budget for completed work.
        cost_variance = ev - ac

        # Positive SV means more budgeted work has been completed than planned.
        schedule_variance = ev - pv

        cpi = (ev / ac) if ac > ZERO else None
        spi = (ev / pv) if pv > ZERO else None

        # The forecast assumes the observed cost efficiency continues.
        estimate_at_completion = (
            self.baseline.total_budget / cpi
            if cpi is not None and cpi > ZERO
            else None
        )

        estimate_to_complete = (
            estimate_at_completion - ac
            if estimate_at_completion is not None
            else None
        )

        variance_at_completion = (
            self.baseline.total_budget - estimate_at_completion
            if estimate_at_completion is not None
            else None
        )

        return {
            "period": period,
            "BAC": self.baseline.total_budget,
            "PV": pv,
            "EV": ev,
            "AC": ac,
            "CV": cost_variance,
            "SV": schedule_variance,
            "CPI": cpi,
            "SPI": spi,
            "EAC": estimate_at_completion,
            "ETC": estimate_to_complete,
            "VAC": variance_at_completion,
        }

    def propose_change(self, request: ChangeRequest) -> None:
        if any(
            existing.request_id == request.request_id
            for existing in self.change_requests
        ):
            raise ValueError("Change request IDs must be unique.")

        if request.status != "PENDING":
            raise ValueError("New change requests must be pending.")

        self.change_requests.append(request)

    def decide_change(
        self,
        request_id: str,
        approver: str,
        approved: bool,
        decision_note: str,
    ) -> None:
        if not approver.strip() or not decision_note.strip():
            raise ValueError("Approver and decision note are required.")

        request = next(
            (item for item in self.change_requests if item.request_id == request_id),
            None,
        )
        if request is None:
            raise ValueError("Change request was not found.")

        if request.status != "PENDING":
            raise ValueError("A decided change request cannot be decided again.")

        request.status = "APPROVED" if approved else "REJECTED"
        request.decision_note = f"{approver}: {decision_note}"

        # Approval of a change request is not itself a baseline revision.
        # The project manager must create, validate, and approve a new revision
        # before the official performance reference changes.


def sample_project() -> ProjectControls:
    packages = {
        "CIVIL": WorkPackage("CIVIL", "Civil works", "450000.00"),
        "ELECT": WorkPackage("ELECT", "Electrical installation", "300000.00"),
        "TEST": WorkPackage("TEST", "Testing and commissioning", "250000.00"),
    }

    budgets = [
        MonthlyBudget("2026-01", "CIVIL", "150000"),
        MonthlyBudget("2026-02", "CIVIL", "180000"),
        MonthlyBudget("2026-03", "CIVIL", "120000"),
        MonthlyBudget("2026-02", "ELECT", "50000"),
        MonthlyBudget("2026-03", "ELECT", "150000"),
        MonthlyBudget("2026-04", "ELECT", "100000"),
        MonthlyBudget("2026-03", "TEST", "50000"),
        MonthlyBudget("2026-04", "TEST", "100000"),
        MonthlyBudget("2026-05", "TEST", "100000"),
    ]

    baseline = CostBaseline(
        baseline_id="BASE-001",
        project_name="District Hospital Electrical Modernization",
        currency="INR",
        work_packages=packages,
        monthly_budgets=budgets,
    )
    baseline.approve("Project Director", date(2025, 12, 20))

    controls = ProjectControls(baseline=baseline)

    costs = [
        CostEntry("AC-001", "2026-01", "CIVIL", "140000", "Site preparation"),
        CostEntry("AC-002", "2026-02", "CIVIL", "200000", "Structural work"),
        CostEntry("AC-003", "2026-02", "ELECT", "60000", "Cable procurement"),
        CostEntry("AC-004", "2026-03", "CIVIL", "130000", "Civil completion"),
        CostEntry("AC-005", "2026-03", "ELECT", "140000", "Electrical installation"),
        CostEntry("AC-006", "2026-03", "TEST", "30000", "Pre-commissioning tests"),
        CostEntry(
            "AC-007", "2026-03", "TEST", "25000",
            "Unapproved supplier claim", approved=False
        ),
    ]

    for cost in costs:
        controls.add_actual_cost(cost)

    progress = [
        ProgressEntry("2026-01", "CIVIL", Decimal("30")),
        ProgressEntry("2026-02", "CIVIL", Decimal("70")),
        ProgressEntry("2026-03", "CIVIL", Decimal("100")),
        ProgressEntry("2026-02", "ELECT", Decimal("10")),
        ProgressEntry("2026-03", "ELECT", Decimal("55")),
        ProgressEntry("2026-03", "TEST", Decimal("10")),
    ]

    for entry in progress:
        controls.record_progress(entry)

    return controls


def print_report(controls: ProjectControls, period: str) -> None:
    metrics = controls.metrics(period)

    print(f"\nProject: {controls.baseline.project_name}")
    print(f"Baseline: {controls.baseline.baseline_id}")
    print(f"Approved on: {controls.baseline.approved_on}")
    print(f"Reporting period: {period}")
    print("-" * 66)

    labels = {
        "BAC": "Budget at completion",
        "PV": "Planned value",
        "EV": "Earned value",
        "AC": "Actual cost",
        "CV": "Cost variance (EV - AC)",
        "SV": "Schedule variance (EV - PV)",
        "EAC": "Estimate at completion",
        "ETC": "Estimate to complete",
        "VAC": "Variance at completion",
    }

    for key, label in labels.items():
        value = metrics[key]
        print(f"{label:<31} {signed_money(value) if value is not None else 'N/A':>20}")

    for key in ("CPI", "SPI"):
        value = metrics[key]
        print(f"{key + ' efficiency index':<31} {value:.3f}" if value is not None
              else f"{key + ' efficiency index':<31} N/A")

    print("\nInterpretation:")
    print("  CPI below 1.00 indicates cost inefficiency.")
    print("  SPI below 1.00 indicates progress behind the time-phased plan.")
    print("  A positive CV indicates that earned work costs less than actual spending.")
    print("  Forecasts depend on the assumptions used and are not guaranteed outcomes.")


def export_report(controls: ProjectControls, period: str, directory: Path) -> None:
    """Export auditable machine-readable metrics without third-party libraries."""
    directory.mkdir(parents=True, exist_ok=True)
    metrics = controls.metrics(period)

    serializable = {
        key: str(value) if isinstance(value, Decimal) else value
        for key, value in metrics.items()
    }

    with (directory / "cost_baseline_report.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(serializable, handle, indent=2)

    with (directory / "monthly_budget.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["period", "work_package_code", "amount_inr"])
        for item in sorted(
            controls.baseline.monthly_budgets,
            key=lambda entry: (entry.period, entry.work_package_code),
        ):
            writer.writerow([item.period, item.work_package_code, str(item.amount)])


class CostBaselineTests(unittest.TestCase):
    def test_baseline_total(self) -> None:
        controls = sample_project()
        self.assertEqual(controls.baseline.total_budget, Decimal("1000000.00"))

    def test_unapproved_cost_is_excluded(self) -> None:
        controls = sample_project()
        self.assertEqual(
            controls.cumulative_actual_cost("2026-03"),
            Decimal("670000.00"),
        )

    def test_variances_are_consistent(self) -> None:
        controls = sample_project()
        metrics = controls.metrics("2026-03")
        self.assertEqual(metrics["CV"], metrics["EV"] - metrics["AC"])
        self.assertEqual(metrics["SV"], metrics["EV"] - metrics["PV"])

    def test_draft_baseline_cannot_be_used(self) -> None:
        baseline = CostBaseline(
            "DRAFT-001",
            "Test project",
            "INR",
            {"CIVIL": WorkPackage("CIVIL", "Civil works", "100")},
            [MonthlyBudget("2026-01", "CIVIL", "100")],
        )
        controls = ProjectControls(baseline)
        with self.assertRaises(ValueError):
            controls.metrics("2026-01")

    def test_duplicate_cost_entry_rejected(self) -> None:
        controls = sample_project()
        duplicate = CostEntry(
            "AC-001", "2026-03", "CIVIL", "100", "Duplicate"
        )
        with self.assertRaises(ValueError):
            controls.add_actual_cost(duplicate)

    def test_package_allocation_must_match_estimate(self) -> None:
        baseline = CostBaseline(
            "INVALID-001",
            "Test project",
            "INR",
            {"CIVIL": WorkPackage("CIVIL", "Civil works", "200")},
            [MonthlyBudget("2026-01", "CIVIL", "100")],
        )
        with self.assertRaises(ValueError):
            baseline.approve("Project Director", date(2025, 12, 1))

    def test_negative_cost_rejected(self) -> None:
        with self.assertRaises(ValueError):
            money("-1.00")

    def test_revision_does_not_mutate_original(self) -> None:
        controls = sample_project()
        original_total = controls.baseline.total_budget
        revision = controls.baseline.create_revision(
            "BASE-002", Decimal("50000"), "2026-05"
        )
        self.assertEqual(controls.baseline.total_budget, original_total)
        self.assertEqual(revision.total_budget, original_total + Decimal("50000"))

    def test_duplicate_progress_period_updates_latest_value(self) -> None:
        controls = sample_project()
        controls.record_progress(ProgressEntry("2026-03", "TEST", Decimal("20")))
        self.assertEqual(
            controls.earned_value("2026-03"),
            Decimal("770000.00"),
        )

    def test_completion_cannot_decrease(self) -> None:
        controls = sample_project()
        with self.assertRaises(ValueError):
            controls.record_progress(
                ProgressEntry("2026-04", "CIVIL", Decimal("90"))
            )


def main() -> None:
    controls = sample_project()
    print_report(controls, "2026-03")

    controls.propose_change(
        ChangeRequest(
            request_id="CR-014",
            description="Additional electrical safety panels",
            amount_delta=Decimal("50000"),
            effective_period="2026-05",
        )
    )
    controls.decide_change(
        "CR-014",
        "Project Director",
        approved=True,
        decision_note="Required to satisfy revised safety specifications.",
    )

    print("\nChange control:")
    request = controls.change_requests[0]
    print(f"  Request: {request.request_id}")
    print(f"  Status: {request.status}")
    print(f"  Decision: {request.decision_note}")
    print("  Official baseline unchanged until a revision is approved.")

    with tempfile.TemporaryDirectory(prefix="cost-baseline-") as temp_dir:
        export_report(controls, "2026-03", Path(temp_dir))
        print(f"\nAudit exports written to: {temp_dir}")

    print("\nValidation tests:")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CostBaselineTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
