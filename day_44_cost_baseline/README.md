# Cost Baseline: Understanding Planned Spending

## Purpose and scope

A cost baseline is the formally approved, time-phased budget against which project spending and completed work are measured. It answers two distinct questions: how much the project is authorized to spend, and when that spending is expected to occur.

A total budget alone does not provide enough information for effective cost control. A project with an approved budget of ₹10,00,000 might plan to spend ₹3,00,000 in January, ₹2,50,000 in February, and the remainder over subsequent months. If the same amount is spent too early, or the planned work is not completed, the project can experience cost pressure even when its final budget has not changed.

The implementations use a district hospital modernization project with three work packages:

| Work package | Approved estimate |
|---|---:|
| Civil works | ₹4,50,000 |
| Electrical installation | ₹3,00,000 |
| Testing and commissioning | ₹2,50,000 |
| **Budget at completion** | **₹10,00,000** |

The time-phased budget distributes these estimates across January to May 2026. Actual cost transactions and verified progress are recorded separately so that spending can be compared with the original plan.

The examples use Indian rupees, a fixed reporting currency, and an approved original baseline. The same principles apply to infrastructure, software implementation, equipment installation, public-sector modernization, and other projects with defined scope and schedules.

## What constitutes a cost baseline?

A cost baseline is more than a spreadsheet containing planned expenses. It combines an approved spending plan with the scope and schedule against which performance is evaluated.

**Work-package estimates** assign a budget to a defined portion of the project. Civil works and electrical installation have separate estimates so that cost deviations can be traced to their sources.

**Time-phased allocations** distribute each work-package estimate across reporting periods. These allocations form the planned spending curve and establish how much budgeted work should have been scheduled by a particular date.

**Approval and revision control** distinguish the current authorized plan from draft estimates and proposed changes. A proposed budget increase does not automatically change the reference used to assess performance.

**Actual costs and progress measurements** are recorded independently. Actual cost measures the cost incurred for completed or ongoing work, while progress records indicate how much of the planned scope has been completed.

The baseline is therefore a controlled reference. Its value comes from consistency, traceability, and the ability to compare the same approved plan with later project evidence.

## Baseline terminology

| Term | Meaning | Practical use |
|---|---|---|
| Budget at completion (BAC) | Total approved baseline budget | Defines the authorized cost target |
| Planned value (PV) | Budgeted value of work scheduled by a reporting date | Establishes how much work should have been completed |
| Earned value (EV) | Budgeted value of work actually completed | Measures progress in the same monetary terms as the plan |
| Actual cost (AC) | Approved cost incurred for the work through the reporting date | Measures the financial resources consumed |
| Cost variance (CV) | EV minus AC | Identifies cost efficiency for completed work |
| Schedule variance (SV) | EV minus PV | Identifies whether completed work is ahead of or behind the planned amount |
| Cost performance index (CPI) | EV divided by AC | Measures earned value per unit of actual expenditure |
| Schedule performance index (SPI) | EV divided by PV | Measures progress relative to the planned value |
| Estimate at completion (EAC) | Forecast total cost at project completion | Estimates the likely final expenditure |
| Estimate to complete (ETC) | Forecast expenditure still required | Supports funding and cash planning |
| Variance at completion (VAC) | BAC minus EAC | Estimates the difference between the authorized budget and forecast final cost |

These metrics answer different questions. BAC is an approved plan value, AC is a financial measure, and EV is a measure of completed work valued at the approved budget rates. They should not be treated as interchangeable.

## Time-phased planning

A time-phased baseline associates each allocation with a reporting period and a work package. The cumulative planned value is the sum of all allocations scheduled on or before the reporting date.

For the case study, the monthly allocations are:

| Month | Planned spending | Cumulative planned value |
|---|---:|---:|
| January 2026 | ₹1,50,000 | ₹1,50,000 |
| February 2026 | ₹2,30,000 | ₹3,80,000 |
| March 2026 | ₹3,20,000 | ₹7,00,000 |
| April 2026 | ₹2,00,000 | ₹9,00,000 |
| May 2026 | ₹1,00,000 | ₹10,00,000 |

The cumulative values create a spending reference for each month. They are not forecasts of invoices alone. They represent the budgeted value of the work scheduled for completion over time.

The Python implementation groups allocations by month and work package. The JavaScript implementation validates allocation totals when constructing the baseline. The C++ implementation uses a collection of budget allocations and calculates cumulative planned value. The Java implementation models each allocation as an immutable record. The SQL implementation stores allocations relationally and aggregates them through a view.

The different implementations enforce the same financial principle through mechanisms suited to each language.

## Earned-value analysis

Earned-value analysis combines planned value, earned value, and actual cost. It helps distinguish a project that has spent money efficiently from a project that has simply spent less because it has completed less work.

The main relationships are:

- Cost variance: `CV = EV - AC`
- Schedule variance: `SV = EV - PV`
- Cost performance index: `CPI = EV / AC`
- Schedule performance index: `SPI = EV / PV`
- Forecast at completion: `EAC = BAC / CPI`, when CPI is defined and positive
- Estimate to complete: `ETC = EAC - AC`, when EAC is available

A positive CV indicates that completed work has a budgeted value greater than its actual cost. A negative CV indicates that the work has cost more than its budgeted value.

A positive SV indicates that the value of completed work exceeds the value scheduled by the reporting date. A negative SV indicates that the project has completed less budgeted work than planned.

CPI and SPI are ratios rather than currency amounts. A CPI below 1.00 means that each rupee spent has earned less than one rupee of budgeted value. An SPI below 1.00 means that completed work represents less than the value scheduled.

These indicators do not directly measure calendar days. Schedule variance is expressed in monetary units because it compares budgeted values of work. A separate schedule analysis is required to estimate a completion-date delay.

### March performance example

At the end of March 2026, the approved plan has a cumulative PV of ₹7,00,000. Verified progress earns ₹7,70,000 of budgeted value, while approved actual costs total ₹6,70,000.

| Metric | Value |
|---|---:|
| BAC | ₹10,00,000 |
| PV | ₹7,00,000 |
| EV | ₹7,70,000 |
| AC | ₹6,70,000 |
| CV | ₹1,00,000 |
| SV | ₹70,000 |
| CPI | Approximately 1.149 |
| SPI | 1.100 |
| EAC | Approximately ₹8,70,130 |

The figures indicate favorable cost and progress performance at the reporting date. The EAC is a projection based on the assumption that the observed cost efficiency continues. It is not a guaranteed final cost.

The sample includes a pending supplier claim of ₹25,000. It is excluded from approved AC until it passes the financial approval process. The claim remains visible in the transaction ledger so that exclusion from performance calculations does not mean that the claim has disappeared from review.

## Python implementation

The Python script models the baseline with dataclasses and `Decimal` arithmetic. Decimal values avoid the rounding artifacts that can occur when monetary amounts are accumulated using binary floating-point values.

`WorkPackage`, `MonthlyBudget`, `CostEntry`, and `ProgressEntry` represent separate parts of the control model. Their validation logic rejects invalid periods, negative monetary values, missing identifiers, and completion percentages outside the permitted range.

`CostBaseline.validate()` reconciles the sum of monthly allocations against each work-package estimate. An approved baseline cannot be used for performance calculations until its allocations have passed validation.

`ProjectControls` records approved cost entries and progress observations. It calculates cumulative PV and AC, determines EV from the latest available completion percentage for each package, and derives performance metrics. The test suite covers allocation mismatches, duplicate cost identifiers, unapproved expenditure, invalid completion changes, and baseline revisions.

The change-control implementation makes an important distinction between approving a request and approving a revised baseline. A change request can receive an approval decision without altering the active financial reference. A separately validated revision is required before the official plan changes.

The script also exports a JSON performance report and a CSV allocation file using Python's standard library. These files provide a simple audit trail for reporting and further analysis.

## JavaScript implementation

The JavaScript implementation emphasizes event-driven processing and concurrent submissions.

The `Baseline` class validates package allocations and freezes its package and allocation records. Its approval method establishes the approved state before the cost ledger can be created.

`CostLedger` extends Node.js's `EventEmitter`. It publishes events when costs are recorded or rejected and when a change request receives a decision. This structure separates the core cost-control operations from reporting or notification handlers.

Cost submission uses an expected-version check. Two concurrent submissions based on the same ledger version cannot both commit: after one succeeds, the other detects that the ledger has changed. This is a demonstration of optimistic concurrency control, not a replacement for a transactional database in a multi-process production system.

The JavaScript version also keeps unapproved costs outside the approved ledger and computes EV using the latest progress observation for each package. Its assertions validate the sample's financial calculations and the concurrent-submission behavior.

JavaScript's event loop and asynchronous execution are particularly relevant when cost records arrive from multiple application requests or external financial systems. In production, database transactions, idempotency keys, and persistent audit records would still be needed.

## C++ case study

The C++ program models a public infrastructure cost-control engine with a strict separation between the baseline, operational measurements, and change governance.

`CostBaseline` owns the work-package estimates and time-phased allocations. Its approval operation validates the allocation totals before enabling the baseline for performance calculations.

`CostControlEngine` processes actual-cost records, maintains unique transaction identifiers, stores verified progress, and calculates cumulative PV, EV, and AC. Its data structures are appropriate for a compact, in-memory case study: a map provides package lookup, a vector retains ordered financial records, and a set detects duplicate cost identifiers.

Money is represented as integer paise. This avoids accumulating small binary floating-point errors when adding or subtracting currency amounts. The performance indices use floating-point ratios because CPI and SPI are calculated measurements rather than stored monetary transactions.

The `ChangeControl` class represents proposed changes with explicit pending, approved, and rejected states. A final decision requires an approver and a reason. The change remains separate from the baseline so that approval of a request cannot silently rewrite the original plan.

The engine also handles zero-denominator cases. When actual cost or planned value is zero, the corresponding performance index is undefined rather than a fabricated numeric result.

For a production implementation, month validation should use a proper date type, audit records should be persisted transactionally, and all financial updates should use database-backed concurrency control.

## Java implementation

The Java program uses records, enums, immutable collections, and service-oriented domain classes to represent enterprise cost governance.

`WorkPackage`, `Allocation`, `CostTransaction`, and `ProgressRecord` are records with constructor validation. `ApprovedBaseline` manages the approval state and exposes read-only package data. `PerformanceService` is responsible for financial measurements rather than embedding all reporting logic in the baseline object.

The explicit `BaselineState` and `ChangeState` enums make invalid transitions visible. A draft baseline can be approved, and an approved baseline can later be marked superseded when a formally approved successor exists. A finalized baseline is not intended to be edited in place.

`PerformanceService` rejects duplicate transaction identifiers and unknown package references. It includes only approved financial transactions in AC and maintains the latest verified progress for each package.

The `PerformanceReport` record returns PV, EV, AC, CV, SV, CPI, SPI, EAC, and ETC as a coherent result. Ratios and forecasts are represented as nullable values when the required denominator or performance assumptions are unavailable.

This design is useful in enterprise systems because it separates validation, state transitions, financial calculation, and presentation. A production service would add authorization, persistent transactions, audit logging, and explicit baseline-revision workflows.

## SQL relational model

The PostgreSQL script models the baseline and its supporting evidence in relational tables.

| Table | Responsibility |
|---|---|
| `projects` | Identifies the project and reporting currency |
| `project_baselines` | Stores baseline revisions, approval metadata, and status |
| `work_packages` | Stores approved estimates for defined project components |
| `budget_allocations` | Stores the month-by-month planned spending curve |
| `cost_transactions` | Records submitted and approved financial transactions |
| `progress_observations` | Stores verified package completion by reporting month |
| `change_requests` | Tracks proposed financial changes and their decisions |

Primary keys provide record identity. Foreign keys preserve relationships between projects, baselines, packages, allocations, and cost transactions. Unique constraints prevent duplicate project codes, baseline revisions, package codes within a baseline, monthly package allocations, transaction references, and progress observations for the same package and month.

The `NUMERIC(14, 2)` type represents currency values without binary floating-point storage. Check constraints prevent negative spending and invalid progress percentages. The transaction status constraint requires approval metadata for approved costs and prohibits approval metadata on pending or rejected costs.

The partial unique index `one_approved_baseline_per_project` prevents a project from having multiple baselines in the approved state. The allocation and progress indexes support period-oriented reporting.

The allocation reconciliation triggers validate the relationship between package estimates and their time-phased allocations when a transaction commits. The progress trigger prevents a later observation from reporting lower completion than the preceding observation.

The monthly spending view aggregates planned amounts by baseline and month. The reconciliation view exposes discrepancies between work-package estimates and allocations. The earned-value query uses common table expressions to compute BAC, PV, EV, AC, CV, SV, CPI, SPI, and EAC for March 2026.

The SQL design demonstrates database-level integrity rather than relying only on application validation. It is an educational relational model; a production deployment would require additional authorization rules, migration management, and carefully designed revision procedures.

## Baseline changes and governance

The approved baseline should change only through formal change control. A request should identify the reason for the proposed change, its financial effect, its effective period, the responsible decision-maker, and the decision record.

A useful distinction is the difference between these states:

- **Pending:** The request has been submitted but has not received a decision.
- **Approved:** The change has received authorization but may still require a formal baseline revision.
- **Rejected:** The request is not authorized to alter the approved plan.

An approved change request and an approved baseline revision are separate governance events. The revision must contain consistent package estimates and time-phased allocations, pass validation, and receive the required approval. Once a new revision becomes active, the previous revision should remain available for historical reporting.

The examples preserve the original ₹10,00,000 baseline after the sample ₹50,000 safety-panel request is approved. The amount is not silently added to the performance reference. This prevents retrospective changes from making earlier performance appear better or worse merely because the reporting target was rewritten.

## Edge cases and operational limitations

**Zero planned value:** SPI cannot be calculated when PV is zero. A zero denominator must produce an unavailable ratio rather than an error or misleading number.

**Zero actual cost:** CPI cannot be calculated when AC is zero. A forecast based on CPI is also unavailable unless the chosen forecasting method has sufficient evidence.

**Unapproved claims:** Pending supplier claims should not be treated as approved expenditure in the official performance measure. They still need a separate review process so that potential liabilities are not overlooked.

**Budget allocation mismatches:** A package estimate of ₹3,00,000 cannot be reconciled with monthly allocations totaling ₹2,80,000. The baseline should fail validation until the discrepancy is corrected.

**Duplicate transactions:** A repeated source invoice must not increase AC twice. A unique transaction reference is necessary, and production systems should also use source-system identifiers and idempotent processing.

**Progress corrections:** Progress observations may require correction, but changes should be traceable. The educational implementations use simplified rules to prevent unexplained reductions in completion.

**Forecast assumptions:** EAC calculated as BAC divided by CPI assumes that observed cost efficiency remains representative. Changes in procurement prices, project scope, productivity, or remaining-work conditions may make this assumption unsuitable.

**Rounding:** Monetary values should use decimal or fixed-point representations. Ratios may use a specified precision, while financial reports should retain a consistent currency scale.

**Concurrent updates:** An in-memory version check illustrates how conflicting updates can be detected. It does not provide the durability, isolation, or recovery guarantees of a transactional database.

## Practical interpretation

The purpose of a cost baseline is not to force actual spending to match a monthly figure regardless of project conditions. It is to provide a consistent, approved reference for understanding financial performance and identifying deviations early.

A useful control review compares the scheduled value of work, the budgeted value of completed work, and the approved actual cost. Investigations should then determine whether a variance arises from delayed work, underestimated resources, price changes, procurement timing, inaccurate progress reporting, or a genuine change in project scope.

The baseline is most useful when the underlying work packages are measurable, the spending plan reflects the schedule, financial records are reconciled, progress measurements are independently verified, and revisions follow a documented approval process.
