# Project Cost Tracking and Expense Monitoring

## Scope

This repository models project cost tracking as a controlled process for recording expenses, comparing actual spending with approved budgets, detecting cost pressure, validating financial data, and producing management-level cost information.

The four core areas are deliberately separated:

- **Cost planning** establishes the budget available to each project and spending category.
- **Expense monitoring** records actual, committed, and planned costs and evaluates their effect on the project budget.
- **Variance analysis** compares planned amounts with actual expenditure and identifies categories that require attention.
- **Cost governance** applies validation, approval, duplicate detection, threshold rules, and database constraints so that financial information remains reliable.

The implementations use different perspectives rather than translating one program into five languages. Python provides a reusable cost-analysis model, JavaScript demonstrates an event-driven and asynchronous workflow, C++ implements a governance-oriented cost engine, Java models an enterprise domain with explicit types and policies, and PostgreSQL represents the same operational problem through relational integrity and analytical queries.

## Cost Tracking Model

A project normally has a finite approved budget distributed across cost categories such as labor, cloud services, software, equipment, travel, and contractors.

A useful cost model distinguishes at least three quantities:

`Budget = approved amount available for the project or category`

`Actual Cost = expenditure that has occurred and is recognized as actual`

`Variance = Budget - Actual Cost`

A positive variance indicates remaining budget under the simple budget-minus-actual definition. A negative variance indicates that actual spending has exceeded the corresponding budget.

Budget utilization is represented as:

`Utilization = Actual Cost / Budget × 100`

Utilization is useful because the absolute amount alone does not show whether a category is approaching its limit. A ₹10,000 expense may be insignificant against a ₹1 million category but material against a ₹15,000 category.

The implementation also distinguishes high-value expenses that require approval from ordinary transactions. This is important because monitoring is not only about arithmetic. A technically correct total can still be operationally unreliable if transactions are duplicated, incorrectly dated, unapproved, or assigned to the wrong project.

## Expense States

The examples use expense states to distinguish financial intent from recognized expenditure.

`planned` represents an expected cost that has not yet become a committed transaction.

`committed` represents an obligation that the project expects to pay even though the final actual transaction may not yet have been recorded.

`actual` represents recognized project expenditure and is the state used for actual-cost calculations.

`cancelled` represents a transaction that should not contribute to actual project cost.

This distinction prevents the cost dashboard from treating a forecast or commitment as though it were already paid or recognized actual expenditure.

## Python Implementation

The Python implementation is centered on the `Project`, `Expense`, and `CostTracker` classes.

`Project` owns the project period, budget by category, and recorded expenses. Its `total_budget`, `total_actual`, `category_actual`, `category_variance`, and `utilization` properties and methods provide the basic financial measurements.

`Expense` validates the fundamental transaction fields. A positive amount is required, a description and vendor are required, and the transaction carries its category, project identity, date, status, approval state, and optional invoice number.

`CostTracker` acts as the operational service layer. It prevents duplicate project identifiers, routes expenses to the correct project, creates budget alerts, aggregates monthly spending, calculates vendor exposure, checks transaction quality, and produces CSV and JSON reports.

The Python implementation uses `Decimal` rather than binary floating-point arithmetic for monetary calculations. This avoids common representation errors that can appear when financial values are repeatedly added using ordinary binary floating-point numbers.

The forecast method uses a simple run-rate model. It calculates an observed daily spending rate and extrapolates that rate across the project duration. This is deliberately a basic forecast rather than a claim that future costs will necessarily follow historical spending.

The script also checks for high-value unapproved expenses and duplicate invoice numbers. These checks illustrate why cost monitoring requires data-quality controls in addition to aggregation.

The generated files are placed in `cost_tracking_output`. The CSV contains transaction-level records, while the JSON report contains project totals, category variance, monthly actuals, forecast information, alerts, and data-quality exceptions.

## JavaScript Implementation

The JavaScript implementation treats cost tracking as an event-driven workflow.

`ProjectCostTracker` maintains expenses in a `Map`, allowing direct lookup by expense identifier and making duplicate transaction detection explicit.

The `on` and `emit` methods implement a lightweight event mechanism. Recording an expense emits an `expenseRecorded` event, allowing monitoring behavior to react to a transaction without embedding reporting logic directly inside the transaction object.

This is useful in Node.js applications where an expense could trigger logging, an alert, asynchronous persistence, or another downstream operation.

The implementation uses immutable expense objects through `Object.freeze`. The expense record is therefore not silently modified after validation.

The asynchronous `persistSnapshot` method demonstrates a Promise-based persistence boundary. It does not introduce a database dependency, but it represents the point at which a real application could send the validated snapshot to a database, API, queue, or storage service.

JavaScript-specific aggregation uses `Map`, object transformations, `Intl.NumberFormat`, and asynchronous execution. The budget-policy method classifies category pressure as warning or critical based on utilization.

The implementation also separates data-quality problems from budget alerts. An expense can be within budget while still being operationally problematic because it is unapproved or duplicates an invoice.

## C++ Governance Case Study

The C++ program models a project cost-governance engine for an infrastructure reliability programme.

The `ProjectCostGovernance` class owns the budget, expense collection, transaction identifiers, and invoice identifiers. The design emphasizes integrity checks at the point where an expense enters the system.

The use of `std::set` for expense and invoice identifiers provides an explicit uniqueness mechanism. An expense identifier cannot be registered twice, and an invoice cannot be counted twice. This models a control that would normally also be enforced by a database unique constraint.

The `actualByCategory` method uses a `std::map` to aggregate recognized spending by category. `std::accumulate` is used for the total actual cost, demonstrating standard-library aggregation without introducing an unnecessary framework.

The `evaluateBudget` method applies warning and critical utilization thresholds. It also detects spending against a zero budget and total project overruns.

The case study includes a run-rate forecast using elapsed days and total project duration. This is intentionally separated from historical aggregation because forecasting and reporting answer different questions.

Vendor exposure provides another management perspective. Two projects can have the same total expenditure while having very different supplier concentration. A vendor carrying a large portion of project spend may represent commercial or operational concentration that deserves separate review.

The control-exception mechanism identifies high-value expenses without approval. This demonstrates a governance rule rather than a simple reporting calculation.

## Java Enterprise Domain Model

The Java implementation uses explicit domain types to model enterprise cost governance.

`CostCategory`, `ExpenseStatus`, and `Severity` are enums rather than unvalidated strings. This limits the state space and makes invalid category or status values harder to introduce accidentally.

`CostExpense` is a Java record. It represents an immutable transaction value with validation performed when the object is constructed.

`Project` owns budget lines and expense records. It calculates total budget, actual cost, category-level actuals, monthly actuals, vendor exposure, and policy violations.

`BudgetPolicy` makes governance thresholds explicit. The warning threshold, critical threshold, and high-value approval limit are part of the policy rather than hidden constants scattered through application logic.

`CostManagementService` provides the application-facing boundary for registering projects and recording expenses. This separation is useful in enterprise systems because domain rules remain inside domain objects while orchestration remains in a service layer.

`BigDecimal` is used for monetary values. This is important for financial systems because decimal arithmetic provides predictable monetary precision and avoids the representation behavior of binary floating-point values.

The Java program also rejects transactions with invalid amounts, duplicate identifiers, duplicate invoices, and approval problems. The policy layer distinguishes ordinary budget utilization from governance violations.

## SQL Data Model

The PostgreSQL implementation models the cost-tracking domain relationally.

The `projects` table stores project identity and project duration. A check constraint prevents an end date from preceding the start date.

`budget_lines` stores category-level approved budgets and enforces one budget line per category for a project through a unique constraint.

`vendors` stores supplier identity independently from transactions. `employees` stores transaction-entry and approval authority.

`expenses` is the transaction table. It references projects, vendors, and employees through foreign keys and stores the category, amount, date, status, invoice number, approval information, and creation timestamp.

The amount constraint requires every expense to be positive. The approval fields are also constrained so that an approval timestamp cannot exist without an approving employee.

The partial unique index on `(vendor_id, invoice_number)` prevents the same vendor invoice from being entered more than once while still permitting transactions that do not yet have an invoice number.

The project/date trigger validates that an expense date belongs to the project period. This rule belongs naturally at the database layer because all applications writing to the database should obey the same project-period boundary.

The approval trigger verifies that the selected approver is active and has an approval limit at least as large as the expense amount. This prevents application code from being the only enforcement point for an important financial-control rule.

## SQL Analytical Views

`project_cost_summary` provides project-level budget, actual, and variance information.

`category_cost_analysis` compares budget and actual expenditure at category level. The query classifies categories as `UNBUDGETED`, `OVER_BUDGET`, `WARNING`, or `WITHIN_PLAN`.

The monthly common table expression aggregates actual expenditure by month. A window function then produces cumulative actual spending. This is useful for examining the progression of expenditure rather than viewing each month in isolation.

Vendor exposure aggregates actual expenditure by supplier and counts transactions. This supports concentration analysis and supplier-level monitoring.

The high-value exception query finds actual transactions above the selected control threshold that have no recorded approver.

## Transactional Behavior

The SQL script demonstrates a transaction in which a committed cloud cost is inserted and then converted to actual status.

The transaction boundary ensures that the workflow can be treated as one database operation. If a production application needed several dependent changes, the same approach could ensure that either all required changes succeed or none of them become visible as a partial workflow.

The script also uses PostgreSQL exception blocks to demonstrate rejection of an expense dated outside the project period and rejection of a duplicate vendor invoice.

## Budget Monitoring Logic

A category-level monitoring system should not rely only on the total project budget.

For example, a project can remain below its total budget while its cloud category is already over budget. Another category may have substantial unused funds that mask the problem when only project-level totals are viewed.

The implementations therefore provide both project-level and category-level analysis.

A typical operational interpretation is:

| Utilization | Interpretation |
|---|---|
| Below 80% | Spending remains below the warning threshold |
| 80% to below 100% | Category requires monitoring |
| 100% or higher | Category is at or above its approved budget |
| Spending with zero budget | Immediate governance exception |

These thresholds are policy examples rather than universal financial rules. Actual organizations may use thresholds based on project type, contract terms, funding restrictions, materiality, or management policy.

## Actual, Committed, and Forecast Costs

Cost tracking becomes more useful when actual expenditure is not confused with expected expenditure.

Actual cost answers what has been recognized.

Committed cost answers what the organization has already obligated itself to spend.

Forecast cost answers what the project is expected to spend by completion.

A management dashboard can therefore contain three distinct views:

`Actual = recognized expenditure`

`Committed = existing obligations`

`Forecast = expected final cost`

Adding these concepts prevents a common monitoring error in which a project appears financially healthy only because committed or expected expenditure has not yet entered the actual ledger.

The examples implement actual-cost aggregation directly and use simple run-rate forecasting. A production forecasting system could incorporate remaining contractual obligations, planned milestones, resource schedules, seasonality, procurement commitments, and approved change requests.

## Variance Analysis

Variance should be examined at multiple levels.

Project variance shows whether total actual expenditure remains inside the approved project budget.

Category variance shows which cost areas create the project-level result.

Monthly variance shows when spending pressure occurred.

Vendor exposure shows where expenditure is concentrated.

Control exceptions show whether spending complies with approval requirements.

These perspectives are complementary. A project can have acceptable total variance but an unacceptable control exception. It can also have a favorable total variance while one category is materially over budget and another category has not yet started.

## Data Quality Controls

Expense monitoring depends on reliable transaction data.

The examples enforce several controls:

- Positive monetary amounts prevent nonsensical negative expense transactions.
- Project-period validation prevents expenses from being assigned outside the project's active dates.
- Unique expense identifiers prevent the same transaction from being recorded twice.
- Vendor invoice uniqueness reduces duplicate invoice risk.
- Approval checks identify high-value expenditure that lacks required authorization.
- Category budgets provide a reference point for interpreting actual spending.
- Status values distinguish actual costs from planned or committed costs.

These controls reduce the risk that a mathematically correct report is based on incorrect input data.

## Performance Considerations

The Python, JavaScript, C++, and Java examples use in-memory collections, so their aggregation operations generally require scanning the recorded expenses.

For `n` expense records, a category or monthly aggregation is typically `O(n)`.

The C++ and Java implementations use set or hash-based identifier checks so that duplicate detection is efficient for normal workloads.

The PostgreSQL implementation uses indexes because database-scale cost tracking differs from an in-memory demonstration. The project/date index supports queries that retrieve transactions by project and time period, while the category index supports category-level analysis.

Indexes should be selected according to actual query patterns. An index has storage and write-maintenance costs, so adding indexes without a query-performance reason can make a transactional system less efficient.

## Security and Financial Control

Cost data can contain commercially sensitive information such as supplier identities, contract values, invoices, employee identities, and project expenditure.

A production implementation should restrict who can create, modify, approve, and export expense information.

Approval authority should not be inferred from a client-side flag. The PostgreSQL model demonstrates a database-side approval-limit check because a financial control should not depend exclusively on the behavior of one application interface.

Auditability is also important. The SQL `approval_events` table separates approval history from the current expense state, allowing a system to retain evidence of approval decisions.

Production systems should also preserve timestamps, actors, change history, and transaction references for material financial events.

## Common Failure Modes

A cost system can produce misleading results even when the calculation formula is correct.

A duplicated invoice can inflate actual expenditure.

An expense assigned to the wrong category can make one budget appear healthy while another appears over budget.

A transaction dated outside the project period can distort monthly reporting.

An unapproved high-value transaction can make reported expenditure appear operationally complete when the required authorization has not occurred.

Counting committed costs as actual costs can make current expenditure appear higher than the recognized ledger.

Ignoring committed costs can make a project appear safer than it is.

Comparing actual costs only against the total project budget can hide category-level overruns.

Using binary floating-point arithmetic for repeated monetary calculations can introduce representation and rounding problems.

The implementations address these failure modes through validation, explicit states, decimal monetary types where appropriate, uniqueness controls, approval checks, and category-level reporting.

## Practical Cost-Monitoring Workflow

The technical workflow represented by the six artifacts is:

`Project Budget → Budget Categories → Expense Entry → Validation → Approval Controls → Actual-Cost Aggregation → Variance Analysis → Alerts → Management Reporting`

The database provides persistent integrity enforcement, while the application implementations demonstrate how the same business concepts can be represented in different programming models.

The most important relationship is between transaction integrity and monitoring. Monitoring cannot compensate for systematically incorrect expense records. Validation and governance therefore form the foundation on which meaningful cost analysis is built.

## Implementation Boundaries

The examples are intentionally self-contained. They use standard language features and PostgreSQL capabilities rather than introducing external application frameworks.

The forecast model is a simple run-rate calculation and should not be interpreted as a full financial forecasting model.

The approval model demonstrates delegated approval limits but does not implement an organization-wide authorization hierarchy.

The SQL schema records approval events but does not attempt to implement a complete accounting ledger, tax system, procurement system, payment processor, or general ledger.

The dashboard calculations focus on project expense monitoring rather than full financial accounting.

These boundaries keep the implementations focused on monitoring project expenses, budget utilization, variance, controls, and cost governance.
