# Cost Management: Introduction to Project Costs

## Scope

Project cost management is the discipline of estimating, budgeting, recording, monitoring, forecasting, and controlling the money required to deliver a project.

The implementations in this repository model a project cost ledger rather than treating cost as a single budget number. A project can have planned expenditure, actual expenditure, outstanding commitments, indirect costs, management reserve, and forecast expenditure at completion. These values answer different management questions and should not be collapsed into one figure.

The central relationship used throughout the implementations is:

`Forecast at Completion = Actual Cost + Committed Cost`

A current variance is expressed as:

`Cost Variance = Planned or Approved Cost - Actual Cost`

The distinction matters because an apparently healthy current budget can still contain a future cost problem when substantial purchase orders, contracts, or other commitments have not yet become actual expenditure.

## Cost Structure

The examples distinguish **direct** and **indirect** project costs.

Direct costs can be traced to project work. Typical examples include project labor, implementation contractors, project-specific software, equipment, and site travel.

Indirect costs support organizational operations but are not naturally attributable to one individual project activity. Corporate allocations and general overhead are represented as indirect costs in the examples.

The implementations also classify costs by operational type:

| Cost type | Project-specific meaning |
| --- | --- |
| Labor | Employee or specialist effort assigned to project work |
| Material | Physical consumables or project materials |
| Equipment | Infrastructure or equipment acquired or used for delivery |
| Software | Licenses, subscriptions, and project-specific software |
| Travel | Travel and site expenditure attributable to project delivery |
| Subcontract | External implementation or specialist services |
| Overhead | Organizational costs allocated to the project |
| Contingency | An allowance intended to address identified cost uncertainty |

Classification by type answers **what the money is being spent on**. Classification as direct or indirect answers **how the expenditure relates to the project**. These dimensions should remain separate.

## Budget, Actual, Commitment, and Forecast

The approved budget establishes the financial ceiling authorized for the project.

Planned cost describes expected expenditure at the cost-item level. Actual cost represents expenditure already recorded. Committed cost represents obligations that have been created but have not necessarily become actual expenditure.

Consider a project with an approved budget of `250000`. If `180000` has been spent and another `40000` is committed, the current actual position is `180000`, but the simple forecast is `220000`. Looking only at actual expenditure would understate the expected financial position.

The Python implementation exposes these concepts through `ProjectBudget`. Its `planned_cost`, `actual_cost`, `committed_cost`, and `forecast_at_completion` properties deliberately remain separate.

The JavaScript implementation uses `ProjectCostManager` to produce the same financial distinctions while adding event-driven threshold and forecast alerts.

The C++ case study applies the same principles to a regional data-centre modernization scenario. The Java program models the concepts as enterprise domain objects and produces an immutable `BudgetSnapshot`.

## Cost Estimation

Cost estimation converts project work into expected monetary requirements.

The Python implementation demonstrates two basic quantity-based calculations:

`Labor Cost = Hours × Hourly Rate`

`Material Cost = Quantity × Unit Cost`

It also calculates contingency as a percentage of a defined cost base. These calculations are deliberately validated so negative hours, quantities, rates, or percentages are rejected.

Real project estimation can require more sophisticated methods, but the fundamental control remains the same: the basis of an estimate must be identifiable. A labor estimate should have a relationship to effort and rate, while a procurement estimate should have a relationship to quantity and unit price.

Using Python's `Decimal` rather than binary floating-point arithmetic for monetary values is important when exact currency rounding is required.

## Cost Variance

Variance identifies the difference between an expected or approved amount and the current actual amount.

The implementations use:

`Variance = Planned Amount - Actual Amount`

A positive value indicates that actual spending is below the planned amount. A negative value indicates that actual spending is above the plan.

A project-level variance and a cost-item variance answer different questions. A project can remain within its total budget while a specific cost category is already experiencing an unfavorable variance. The Python, JavaScript, C++, and Java implementations therefore retain individual cost records instead of storing only a project total.

The SQL implementation exposes item-level variance through queries that compare `planned_amount` with `actual_amount`.

## Budget Utilization

Budget utilization measures how much of the approved budget has already been consumed:

`Budget Utilization = Actual Cost / Approved Budget × 100`

A utilization percentage is not itself a performance judgment. Spending 90% of the budget can be appropriate when the project is almost complete, but it can be dangerous when substantial project work remains.

The examples therefore combine utilization with forecast and commitment information.

The implementations use operational thresholds such as `75%` for a watch condition and `90%` for high utilization. These thresholds are governance examples, not universal project-management rules.

## Management Reserve

Management reserve is represented separately from the approved project budget.

This distinction allows the examples to model a situation in which forecast expenditure is higher than the approved budget but can still be covered by authorized reserve.

For example:

`Approved Budget = 300000`

`Management Reserve = 20000`

`Forecast = 315000`

The forecast is `15000` above the approved budget but remains within the combined budget and reserve envelope.

A forecast exceeding both the approved budget and available reserve is treated as a stronger control problem.

The SQL implementation makes this distinction explicit through its reserve assessment query.

## Python Implementation

The Python program uses `CostItem` as the atomic financial record. Each item contains a name, cost type, direct or indirect classification, planned amount, actual amount, and outstanding commitment.

`ProjectBudget` aggregates those records and calculates project-level measures without requiring callers to maintain duplicate totals.

The implementation also validates negative monetary values, detects item-level overruns, calculates cost distribution by type, and produces CSV and JSON output files. The file exports are useful because cost management frequently requires transferring financial information into reporting or audit workflows.

The `earned_value_metrics` function introduces:

- `BAC`, the Budget at Completion.
- `PV`, the Planned Value.
- `EV`, the Earned Value.
- `AC`, the Actual Cost.
- `CPI`, the Cost Performance Index.
- `SPI`, the Schedule Performance Index.
- `EAC`, the Estimate at Completion.
- `VAC`, the Variance at Completion.

The implementation uses the common introductory relationships `CPI = EV / AC`, `SPI = EV / PV`, and `EAC = BAC / CPI` when the required denominator is positive.

## JavaScript Implementation

The JavaScript program treats cost records as immutable objects created by `createCostItem`.

`ProjectCostManager` maintains the project's cost ledger and uses a `Map` to aggregate expenditure by cost type. This is particularly useful when category totals need to be constructed dynamically without relying on fixed object properties.

The implementation also uses Node.js `EventEmitter`. Adding a cost item causes control evaluation, and the manager emits `thresholdExceeded` or `forecastRisk` events when the financial state reaches defined risk conditions.

This event-driven design is distinct from a simple sequential report. A larger Node.js application could use the same event boundary to connect cost changes to logging, notifications, dashboards, or audit processing without embedding those concerns directly into the cost calculation methods.

The file uses Node's standard `fs/promises` API to persist a JSON report and CSV cost ledger. No third-party npm package is required.

## C++ Case Study

The C++ implementation models a **Regional Data Centre Modernization** project.

`ProjectCostGovernance` owns the project-level financial state and a vector of `CostItem` records. The class calculates planned cost, actual cost, commitments, forecast expenditure, utilization, and control status.

The case study distinguishes four important forecast conditions:

- `WITHIN_PLAN` means current and forecast costs remain within the approved budget.
- `WATCH` identifies elevated budget utilization.
- `HIGH_UTILIZATION` identifies a project that has consumed most of its approved budget.
- `RESERVE_REQUIRED` identifies a forecast above the approved budget but within the management reserve.
- `RESERVE_INSUFFICIENT` identifies a forecast that exceeds both the approved budget and available reserve.
- `OVER_BUDGET` identifies actual expenditure already above the approved budget.

The C++ implementation also uses a `std::map` to aggregate cost by type and produces observations for individual cost items with unfavorable variances or outstanding commitments.

The design uses value-oriented structures and standard-library containers, so the program can be compiled using C++17 without external dependencies.

## Java Enterprise Model

The Java implementation models cost management as an enterprise service.

`CostItem` is a Java record, making each financial record concise and immutable. Validation occurs when the record is constructed, preventing negative planned, actual, or committed amounts from entering the domain model.

`CostManagementService` owns the project-level operations. It calculates totals, budget utilization, cost distribution, direct and indirect expenditure, forecast cost, and the current `CostStatus`.

The explicit `CostStatus` enum prevents the application from relying on arbitrary strings when communicating financial state.

`BudgetSnapshot` provides a stable representation of the current project financial position. The service also calculates earned-value measures through `EarnedValueMetrics`.

Java's `BigDecimal` is used for monetary values instead of `double`. This avoids the binary floating-point representation problems that can occur when currency values are repeatedly added, divided, or rounded.

## SQL Data Model

The PostgreSQL implementation treats project cost management as a relational control system.

The principal relationships are:

`projects → cost_items → cost_transactions`

A project contains many cost items. Each cost item belongs to a cost category and can have many financial transactions.

`cost_categories` separates reusable business classifications from individual project records.

`budget_change_requests` provides a separate representation of proposed budget adjustments rather than silently modifying the approved budget.

The database uses primary keys for identity, foreign keys for relationships, unique constraints for project codes and transaction references, and `CHECK` constraints to prevent negative monetary amounts.

The PostgreSQL enum types constrain cost classification and project status to recognized values.

## Database-Level Integrity

The SQL model demonstrates why important financial rules should not exist exclusively in application code.

For example, `approved_budget`, `planned_amount`, `actual_amount`, `committed_amount`, and transaction `amount` have database constraints that prevent negative values.

A foreign key prevents a cost item from referencing a project that does not exist.

A unique transaction reference prevents the same financial transaction identifier from being recorded twice.

The `prevent_excessive_cost_transaction` trigger provides an additional database-level control. It rejects a new transaction when the resulting project forecast would exceed 150% of the approved budget. This is deliberately a demonstration threshold rather than a universal accounting rule.

## Transactional Budget Changes

The SQL script inserts a budget change request inside a transaction and then marks that request as approved.

Transactions are relevant because financial changes can involve multiple related records. If part of a multi-step financial operation fails, atomic transaction behavior prevents the database from being left with only a partial update.

The example keeps the change request separate from the original approved budget. This preserves the distinction between the original authorization and a later governance action.

## Cost Transactions Versus Cost Items

A cost item is a reporting and planning category such as `Cloud infrastructure`.

A cost transaction represents an individual financial event associated with that item.

This distinction allows the database to retain detailed expenditure history while still maintaining a higher-level project cost structure.

The SQL indexes on project, cost type, and transaction date support common operational queries without indexing every column indiscriminately.

## Forecasting

A basic cost forecast can be calculated from actual expenditure and known commitments:

`Forecast at Completion = Actual Cost + Committed Cost`

This is intentionally simple. It does not claim that future spending will always equal outstanding commitments. More advanced forecasting can incorporate remaining work, historical spending patterns, productivity, risk, schedule effects, and updated estimates.

The examples use the simple model because the purpose is to establish the distinction between current expenditure and expected final expenditure.

## Earned Value

Earned value connects financial performance to the amount of planned work that has actually been accomplished.

`BAC` represents the approved budget at completion.

`PV` represents the budgeted value of work that was planned to be completed by the measurement point.

`EV` represents the budgeted value of work actually completed.

`AC` represents the actual cost incurred for that completed work.

The Cost Performance Index is:

`CPI = EV / AC`

A CPI below `1.00` indicates that less budgeted value has been earned for each monetary unit spent.

The Schedule Performance Index is:

`SPI = EV / PV`

An SPI below `1.00` indicates that the earned value is below the planned value at the measurement point.

These indicators should not be interpreted independently of project context. A single reporting period can be affected by procurement timing, accounting treatment, milestone timing, or delayed cost posting.

## Practical Cost-Control Workflow

A practical project cost workflow represented by these implementations is:

**Estimate**

Define the expected cost of labor, materials, equipment, software, external services, travel, and other project expenditure.

**Authorize**

Establish the approved project budget and identify any management reserve that is governed separately.

**Record**

Capture actual expenditure and outstanding commitments against identifiable cost items.

**Compare**

Calculate variance between planned or approved values and actual expenditure.

**Forecast**

Combine current financial information with known commitments to estimate the likely final cost.

**Control**

Investigate unfavorable variances, high utilization, and forecast overruns before they become irreversible financial problems.

**Report**

Present project totals together with category-level information so decision-makers can identify where cost pressure originates.

## Important Distinctions

**Budget versus actual cost:** the budget represents authorization or expectation, while actual cost represents expenditure recorded to date.

**Actual cost versus committed cost:** actual cost has been incurred or recorded; committed cost represents an outstanding financial obligation.

**Variance versus forecast:** variance describes the current difference between expected and actual values; forecast estimates where the project is likely to finish.

**Direct versus indirect cost:** direct cost can be associated with project delivery; indirect cost is allocated from broader organizational expenditure.

**Contingency versus management reserve:** contingency is normally associated with identified cost uncertainty within the cost planning structure, while management reserve is a separately governed amount held for approved uncertainty or unforeseen needs.

## Edge Cases and Failure Conditions

A zero approved budget must not be used as a denominator when calculating utilization. The implementations explicitly handle that condition.

A zero actual cost makes CPI undefined because `EV / AC` would divide by zero. The Python and Java implementations therefore represent CPI as unavailable rather than manufacturing a value.

Negative cost values are rejected because the model represents expenditure rather than credit adjustments. A real accounting system may support reversals and credits, but those should be represented explicitly with appropriate transaction semantics rather than silently allowing negative values into every cost field.

A project can have a positive current variance and still have a negative forecast variance because future commitments have not yet been reflected in actual expenditure.

A category can exceed its planned amount while the total project remains below its approved budget. Category-level analysis is therefore necessary for meaningful cost control.

## Performance Considerations

The in-memory implementations calculate totals by scanning the cost collection. This is straightforward and appropriate for educational and moderate-sized datasets.

A production database should aggregate large cost ledgers using indexed queries and appropriate execution plans. The PostgreSQL script provides indexes on project identifiers, cost types, and transaction dates because these fields participate in common filtering and aggregation paths.

Repeated aggregation of the same large project ledger can also be optimized through materialized reporting structures, incremental aggregation, or carefully designed analytical queries when the workload requires it.

## Security and Financial Integrity

Cost data can contain commercially sensitive information such as supplier charges, labor rates, contracts, and internal budgets.

Application-level validation should therefore be complemented by database constraints, authorization controls, audit logging, and controlled access to financial records.

The SQL schema demonstrates integrity controls but does not attempt to implement an entire enterprise authorization system.

Financial changes should be traceable. A budget change request should preserve its reason, timestamp, requesting context, and approval state rather than silently overwriting the original budget.

## Common Modeling Mistakes

Treating the approved budget as the same value as current expenditure makes it difficult to determine whether a project is actually consuming money as expected.

Ignoring commitments can make a project appear healthier than it really is because future obligations remain outside the current actual-cost figure.

Using only project-level totals can hide a rapidly growing problem inside one cost category.

Using floating-point values indiscriminately for currency can introduce rounding artifacts. The Python and Java implementations use decimal-oriented monetary representations to make currency calculations explicit.

Changing an approved budget without preserving the reason for the change destroys useful governance history. The SQL implementation instead records budget change requests separately.

## Implementation Relationship

The five implementations intentionally provide different technical perspectives on the same cost-management domain.

Python emphasizes financial calculations, validation, reporting, and file-based cost analysis.

JavaScript emphasizes an event-driven cost-management model in which threshold and forecast conditions generate events that other application components could consume.

C++ emphasizes a performance-oriented project governance engine with explicit cost classifications, forecast controls, and a coherent modernization case study.

Java emphasizes enterprise domain modeling through immutable records, enums, `BigDecimal`, collections, and a service layer.

PostgreSQL emphasizes relational integrity, financial transactions, constraints, indexes, reporting views, aggregation, and database-level controls.

Together, these implementations preserve the central project-cost relationships while demonstrating why cost management is not simply the act of adding project expenses. It requires a controlled connection between estimates, authorization, expenditure, commitments, variance, forecast, reserve, and financial governance.
