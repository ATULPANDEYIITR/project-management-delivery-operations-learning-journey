# Cost Variance: Comparing Planned and Actual Costs

## Scope

Cost variance measures the difference between an approved or expected cost baseline and the cost actually incurred.

The core calculation used throughout this repository is:

`variance = actual cost - planned cost`

A positive variance means actual spending is above the planned amount and is therefore **unfavorable** from a cost-control perspective. A negative variance means actual spending is below plan and is **favorable**. A zero variance means the actual amount matches the baseline.

The four implementations treat the same financial concept from different technical perspectives:

| Implementation | Primary technical perspective |
|---|---|
| Python | Cost-analysis model, validation, reporting, CSV input, JSON output, and edge-case handling |
| JavaScript | Event-driven operational cost ledger with asynchronous postings and audit events |
| C++ | Deterministic cost-governance engine using minor currency units, ordered data, and explicit exception handling |
| Java | Enterprise-oriented domain model with immutable posting records, policies, state modeling, and materiality rules |
| PostgreSQL | Relational cost-control model with constraints, indexes, views, transactions, and analytical queries |

The implementations deliberately distinguish between the **planned baseline**, **actual expenditure**, **variance amount**, **variance percentage**, and **variance interpretation**. These values are related but they answer different management questions.

## Core Cost-Variance Model

A budget line contains a planned amount and receives one or more actual cost postings.

For a budget line:

`planned_cost = approved baseline`

`actual_cost = sum of valid actual postings`

`variance = actual_cost - planned_cost`

For example, if cloud infrastructure was planned at 12,000 and actual expenditure reached 13,800:

`variance = 13,800 - 12,000 = 1,800`

The result is an unfavorable variance of 1,800.

The percentage expresses the size of the deviation relative to the baseline:

`variance_percentage = (variance / planned_cost) × 100`

The same cloud example therefore has:

`(1,800 / 12,000) × 100 = 15%`

The amount and percentage should both be retained. A 1,800 variance can be material for a small project but relatively minor for a large programme.

## Planned Cost and Actual Cost Are Different Data Concepts

The planned amount represents a baseline established before or at the beginning of the relevant reporting period. It should not be silently replaced when actual costs arrive.

Actual cost represents expenditure recorded during execution. A single budget line can receive multiple postings, such as several supplier invoices, cloud usage charges, testing invoices, or expense claims.

The database implementation therefore stores `budget_lines` separately from `cost_postings`.

This separation makes it possible to audit how an actual total was formed. The actual amount is not simply overwritten when a new cost occurs. Each posting retains its source, description, amount, and timestamp.

The same distinction appears in the JavaScript ledger, where a `BudgetLine` stores the baseline while individual operational postings increase the actual amount.

## Favorable and Unfavorable Variance

Cost variance interpretation depends on the direction of the difference.

| Relationship | Variance | Cost interpretation |
|---|---:|---|
| Actual > Planned | Positive | Unfavorable |
| Actual < Planned | Negative | Favorable |
| Actual = Planned | Zero | On plan |

A favorable variance does not automatically mean that project performance is better. A lower cost can result from efficient procurement, lower resource usage, delayed work, incomplete scope, or an accounting timing difference. Cost variance should therefore be interpreted alongside the operational context that produced it.

The implementations intentionally use the term **favorable** for a negative cost variance rather than treating every negative number as inherently positive.

## Python Implementation

The Python implementation builds a reusable cost-analysis model around `CostLine` and `CostVarianceReport`.

`CostLine` validates the category and prevents negative planned or actual costs. Its `variance` property calculates actual minus planned, while `variance_percent` handles the special case where the planned baseline is zero.

`CostVarianceReport` aggregates budget lines and provides:

- Planned and actual totals
- Net variance
- Total variance percentage
- Favorable and unfavorable classifications
- Largest unfavorable cost drivers
- Largest favorable offsets
- Status-based filtering

The script uses `Decimal` rather than binary floating-point arithmetic for monetary calculations. This prevents common representation problems in financial calculations where values such as decimal fractions cannot always be represented exactly by binary floating-point numbers.

The Python implementation also demonstrates an operational reporting workflow. A CSV file containing `category`, `planned_cost`, and `actual_cost` is loaded into the domain model. The resulting report is serialized as JSON. This reflects a practical separation between an input source and a machine-readable reporting artifact.

The file workflow is deliberately implemented with temporary files so the program remains executable without requiring a particular project directory or external data source.

Validation is part of the model rather than being left entirely to callers. Negative costs are rejected, malformed monetary values produce exceptions, and an empty category is invalid.

A planned cost of zero receives special handling. An actual cost of 250 against a zero baseline has a valid amount variance of 250, but a percentage variance would require division by zero. The program therefore reports the percentage as undefined rather than manufacturing a misleading value.

## JavaScript Implementation

The JavaScript implementation uses a different architecture: an event-driven cost ledger.

`BudgetLine` represents the approved baseline and accumulated actual expenditure. `CostLedger` owns the collection of budget lines and emits events when budget lines are created or actual costs are posted.

This makes the implementation useful for understanding how a cost-variance component could sit inside an operational application where costs arrive from multiple systems.

The example sources include cloud metering, accounts payable, procurement, and testing systems. The ledger does not assume that all costs arrive at the same time.

`EventEmitter` provides an explicit event boundary:

- A budget line is created.
- An operational source posts an actual cost.
- The ledger records the posting.
- A `cost.posted` event is emitted.
- An audit trail retains the posting metadata.

The asynchronous simulation uses `Promise` and `setTimeout` to model independent operational postings. This is not intended to reproduce a production billing integration. It demonstrates the architectural distinction between a cost arriving as an event and a report being generated from the accumulated ledger.

JavaScript monetary values are converted to integer cents before arithmetic. This avoids performing financial arithmetic directly with ordinary binary floating-point values. A production financial system would normally use a decimal-capable library or a database monetary representation when the required accounting precision exceeds the application's chosen minor-unit representation.

The implementation also rejects non-positive postings. A negative amount is not silently interpreted as a correction because reversals require explicit business semantics and should normally be represented as controlled accounting events rather than accidental negative input.

## C++ Case Study

The C++ program models a project cost-governance engine.

The `RepositoryCostGovernance` class stores budget lines in a `std::map`, making cost categories directly addressable while keeping reporting deterministic by category.

The program uses `long long` minor currency units instead of `double`. For example, a value of 12,000 currency units is stored as 1,200,000 minor units when the minor unit is one hundredth of the primary currency. This avoids floating-point accumulation error in the core variance arithmetic.

The case study contains a technology programme with separate budget lines for cloud infrastructure, external contractors, testing, security tooling, travel, and training.

Actual costs are recorded independently from planned costs. The governance engine then calculates:

- Total planned cost
- Total actual cost
- Net variance
- Variance percentage
- Unfavorable cost drivers
- Favorable cost offsets

The `unfavorableItems()` method sorts cost lines by descending positive variance. This is useful when the purpose of the report is not merely to identify whether a project is over plan, but to identify which cost categories are driving the deviation.

The program also separates validation failures from normal variance. A negative budget is an invalid data state and produces an exception. An unknown category is also an invalid operational state. Neither should be represented as a normal unfavorable variance.

The distinction is important: a variance is a valid financial result, while invalid input is a data-quality or processing failure.

The zero-baseline case demonstrates another boundary. An unplanned emergency cost can have an amount variance even when planned cost is zero. Its percentage variance is intentionally not calculated.

## Java Enterprise Domain Model

The Java implementation models cost variance as an enterprise domain rather than as a collection of reporting statements.

`CostBudgetLine` owns its approved baseline and its list of `CostPosting` records. `CostPosting` is a Java record representing an immutable actual-cost event with a source, amount, and description.

This structure provides traceability from a reported actual total back to the individual postings that generated it.

The domain also introduces `CostState`:

- `PLANNED` means no actual postings have been recorded.
- `PARTIALLY_ACTUALIZED` means actual expenditure exists but remains below the planned amount.
- `ACTUALIZED` represents a line whose actual expenditure has reached or exceeded the planned amount.

This state is separate from `VarianceStatus`. A state describes the lifecycle of the cost line, while variance status describes its financial relationship to the baseline.

The Java implementation also introduces `VariancePolicy`. The concrete `MaterialVariancePolicy` determines whether a variance exceeds an investigation threshold.

For example, a project may define a 10 percent threshold. A variance of 8 percent can be reported without triggering the material-variance policy, while a 12 percent deviation requires investigation.

This separates the mathematical calculation from the organizational decision rule. The variance engine answers what happened; the policy determines when the deviation requires attention.

Java's `Optional` is used for percentage calculations because a percentage cannot be meaningfully produced when the planned baseline is zero.

## SQL Data Model

The PostgreSQL implementation represents cost variance as a relational workflow.

The central entities are:

- `projects`, which identify the reporting scope and approved project budget
- `cost_categories`, which define controlled cost classifications
- `budget_lines`, which associate a project and category with a planned cost
- `cost_postings`, which record actual expenditure events
- `variance_policies`, which store project-specific investigation thresholds

The relationships preserve the distinction between baseline and actuals.

A project can have many budget lines. Each budget line belongs to one cost category. A budget line can have many actual cost postings. This one-to-many relationship is important because actual expenditure commonly arrives through multiple transactions.

Foreign keys prevent postings from referencing nonexistent budget lines. The `CHECK` constraint on `planned_cost` prevents negative planned amounts. The `CHECK` constraint on `actual_cost` requires actual postings to be greater than zero.

The unique constraint on `(project_id, category_id)` prevents accidental creation of multiple baseline records for the same project and cost category.

## Database-Level Variance Calculation

The `v_cost_variance` view calculates actual expenditure using:

`COALESCE(SUM(cp.actual_cost), 0.00)`

This means a budget line with no postings still has an actual value of zero rather than a null reporting value.

The view then calculates:

`actual_cost - planned_cost`

and derives the corresponding percentage when planned cost is nonzero.

The view also assigns a `variance_status` enum. This keeps the reporting interpretation close to the database calculation while retaining the underlying planned and actual amounts.

A reporting query can therefore retrieve category-level variance without duplicating the calculation in every application.

## Material Variance

A net project variance can hide important category-level deviations.

For example, one category may be 20 percent over plan while another category is 15 percent below plan. The project could appear close to budget even though the first category deserves investigation.

The SQL model therefore stores `threshold_percentage` in `variance_policies`.

The material-variance query compares the absolute category variance percentage with the project's configured threshold.

This distinction separates:

`variance`

from:

`material variance`

A variance is the numerical difference. Materiality is a policy decision about whether the difference is sufficiently significant to investigate.

## Favorable Offsets and Gross Cost Pressure

The SQL reporting layer also calculates favorable and unfavorable amounts separately.

A project can have:

`unfavorable_amount`

and

`favorable_amount`

whose net difference produces:

`net_variance`

This prevents a single net number from hiding the size of opposing cost movements.

For management analysis, this distinction matters because a project with a small net variance can still have substantial cost volatility across categories.

## Transactions and Integrity

The SQL script includes a transaction around an actual cost posting.

The transaction demonstrates an important database principle: the posting should either be accepted as a valid database operation or not leave a partial state.

Constraints also provide a second layer of protection. Application code can validate a cost before insertion, but the database should still enforce rules that must remain true regardless of which application submits the record.

The SQL example intentionally comments out an invalid zero-cost posting rather than executing it. The `actual_cost > 0` constraint would reject that record.

This is preferable to relying exclusively on application-side validation because direct database clients, batch jobs, integrations, and future applications should not be able to bypass core integrity rules.

## Variance Percentage and Zero Baselines

A zero planned cost requires special treatment.

If:

`planned_cost = 0`

and:

`actual_cost = 250`

then:

`variance = 250`

is meaningful.

But:

`250 / 0`

has no defined percentage result.

The implementations therefore preserve the amount variance while returning an undefined or null percentage.

This distinction is important in reporting systems. Substituting zero percent, 100 percent, infinity, or an arbitrary sentinel value can make dashboards misleading.

## Multiple Actual Postings

Actual expenditure should normally be accumulated from individual postings rather than replacing the previous actual value.

Suppose a testing budget is 8,000 and three invoices are posted:

| Posting | Amount |
|---|---:|
| Test planning | 2,000 |
| Performance testing | 3,500 |
| Security testing | 3,700 |
| Actual total | 9,200 |

The resulting variance is:

`9,200 - 8,000 = 1,200`

and the variance percentage is:

`15%`

The database representation preserves all three postings, while the reporting view aggregates them.

This structure supports auditability and makes later investigation possible.

## Common Interpretation Errors

A cost variance report can be mathematically correct and still be interpreted incorrectly.

A favorable cost variance should not automatically be described as an operational success. Lower spending can occur because a planned activity was delayed, a supplier invoice has not yet arrived, or project scope has not been completed.

A positive variance should not automatically be treated as evidence of poor management. Unexpected infrastructure demand, approved scope expansion, inflation, supplier pricing changes, or timing differences can cause actual expenditure to exceed the original baseline.

A net project variance should not be used as the only diagnostic measure. Category-level variances and individual actual postings provide the evidence needed to understand the source of the deviation.

## Variance Versus Forecast

Cost variance compares a baseline with actual expenditure:

`actual - planned`

A forecast answers a different question: what is the expected final cost based on current information?

For example, a project may have a planned cost of 100,000 and actual expenditure of 55,000 halfway through execution. The current variance is:

`55,000 - 100,000 = -45,000`

This does not necessarily mean the project will finish 45,000 under budget. If significant remaining work is expected, the final forecast can still exceed 100,000.

The artifacts in this repository focus on cost variance rather than pretending that variance alone is a complete forecasting model.

## Performance and Precision Considerations

Financial arithmetic should not depend casually on binary floating-point representation.

The Python implementation uses `Decimal`. The C++ implementation uses integer minor units. The Java implementation uses `BigDecimal`. PostgreSQL uses `NUMERIC`.

These choices are different language-specific mechanisms for addressing the same engineering concern: monetary calculations require predictable decimal behavior.

The SQL indexes focus on actual query access paths rather than adding indexes indiscriminately. The index on `budget_line_id` supports aggregation and retrieval of postings for a budget line, while the timestamp index supports time-oriented audit queries.

The C++ implementation uses ordered storage for predictable reporting and sorts only the derived unfavorable and favorable collections. The JavaScript implementation uses `Map` for direct budget-line lookup.

## Security and Data Integrity

Cost variance data can influence budget decisions and financial reporting, so integrity is more important than merely producing a visually correct report.

Core controls demonstrated by these implementations include:

- Rejecting negative or malformed costs.
- Preventing unknown budget categories from receiving postings.
- Enforcing foreign-key relationships in PostgreSQL.
- Preventing duplicate project-category budget lines.
- Preserving actual postings instead of silently overwriting them.
- Retaining posting source and descriptions for auditability.
- Keeping policy thresholds separate from mathematical variance.
- Handling zero baselines explicitly rather than generating misleading percentages.

A production system would also need authentication, authorization, audit identity, segregation of duties, controlled adjustments, immutable accounting records where required, and formal reconciliation procedures. Those controls are outside the scope of these standalone implementations.

## Practical Reporting Structure

A useful cost-variance report should allow a reader to move from the project-level result to the underlying driver.

A practical hierarchy is:

`Project → Cost Category → Actual Posting`

The project level answers whether total expenditure is above or below plan.

The category level identifies where the variance originates.

The posting level provides the evidence supporting the actual amount.

The SQL schema and Java domain model both preserve this hierarchy directly. The Python report exposes the category-level result and the JavaScript event ledger preserves the operational posting trail.

## Relationship Between Amount, Percentage, and Materiality

These three measures should not be treated as interchangeable.

**Variance amount** answers how much money separates actual expenditure from the baseline.

**Variance percentage** answers how large that difference is relative to the baseline.

**Materiality** answers whether the difference is significant enough under a defined policy to require investigation.

A large project can have a large monetary variance with a small percentage. A small project can have a small monetary variance with a very large percentage.

A sound control process therefore uses both the numerical measures and explicit organizational thresholds rather than relying on one universal rule.
