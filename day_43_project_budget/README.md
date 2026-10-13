# Project Budget: Creating, Controlling, and Monitoring a Project Budget

## Purpose

A project budget is a controlled financial baseline that translates project scope and delivery assumptions into authorized monetary limits.

Creating a useful budget is not simply the act of adding estimated costs. A project budget must distinguish planned expenditure from money already committed, money actually spent, expected future expenditure, contingency, and approved changes to the original baseline.

This learning artifact models a technology project with personnel, cloud infrastructure, software, security, testing, and training costs. The implementations approach the same financial problem from different technical perspectives:

- Python provides a self-contained budgeting and forecasting model.
- JavaScript models an event-driven operational budgeting workflow.
- C++ implements a governance-oriented budget engine with explicit policy evaluation.
- Java represents the domain through enterprise-oriented types, interfaces, immutable change-request records, and service-like rules.
- PostgreSQL represents the financial model using relational integrity, constraints, indexes, views, transactions, and analytical queries.

The central relationship is:

**Project scope → cost estimates → budget baseline → commitments and actuals → variance analysis → change control → forecast → financial governance**

---

## Core Budget Concepts

### Budget baseline

The baseline represents the approved financial plan against which project performance is measured.

A baseline normally contains cost categories such as personnel, infrastructure, software, testing, security, training, travel, equipment, or external services.

The implementations deliberately keep the baseline separate from actual expenditure. This prevents an organization from redefining the original plan every time spending changes.

A planned amount of INR 4,200,000 for engineering remains the baseline even when actual engineering expenditure reaches INR 2,100,000.

### Direct budget

The direct budget is the sum of planned amounts assigned to the project cost categories.

For the modeled project:

| Category | Planned amount |
|---|---:|
| Personnel / Engineering | INR 4,200,000 |
| Cloud | INR 1,350,000 |
| Software | INR 650,000 |
| Security | INR 650,000 |
| Testing | INR 500,000 |
| Training | INR 300,000 |

The direct budget is therefore INR 7,650,000.

The exact representation differs by language, but each implementation retains the distinction between individual budget lines and the aggregate project budget.

### Contingency

Contingency is a controlled allowance for identified uncertainty.

The examples use a 12% contingency rate. The contingency is calculated separately from direct cost estimates rather than being hidden inside every category.

This makes the financial model easier to audit because reviewers can distinguish:

`direct planned cost`

from

`uncertainty allowance`

from

`approved scope changes`.

Contingency should not be treated as permission to spend without governance. Its use normally requires a defined organizational policy.

### Commitments

A commitment represents expenditure that has been contractually or operationally committed but may not yet have been fully recognized as an actual expense.

Examples include:

- a cloud reservation,
- a vendor purchase order,
- contracted testing services,
- approved engineering effort,
- software licensing obligations.

The distinction between committed and actual spending matters because a project can appear financially healthy when looking only at posted expenses while significant future obligations are already locked in.

### Actual expenditure

Actual expenditure represents recognized spending.

The Python, JavaScript, C++, Java, and SQL implementations all maintain actual expenditure independently from planned amounts.

This permits variance analysis:

`variance = planned budget - actual expenditure`

A positive variance indicates remaining budget relative to actual expenditure. A negative variance indicates that actual expenditure has exceeded the baseline.

### Forecast cost

A simple forecast used in the implementations combines current actual expenditure with outstanding commitments:

`projected cost = actual expenditure + remaining commitments`

This is deliberately conservative and transparent. A production forecasting system can incorporate remaining work, schedule slippage, resource rates, inflation, exchange rates, historical burn rates, and risk-adjusted estimates.

---

## Budget Creation Workflow

A project budget starts with scope rather than with arbitrary financial numbers.

The cost structure should correspond to real delivery activities. In the example project, engineering, cloud infrastructure, security, testing, and training represent recognizable delivery cost centers.

Each category receives a planned amount.

The baseline is then subject to approval before operational expenditure begins.

Once active, the budget receives transactions:

- commitments capture expected financial obligations;
- actual expenses capture recognized expenditure;
- approved changes modify authorized financial capacity;
- reporting compares the current financial state against the baseline.

This creates a controlled distinction between planning and execution.

---

## Variance Analysis

Variance analysis identifies the difference between planned and actual expenditure.

For a budget line:

`variance = planned - actual`

If engineering has a planned budget of INR 4,200,000 and actual expenditure is INR 2,100,000, its current variance is INR 2,100,000.

That does not automatically mean INR 2,100,000 is available for unrestricted use. Outstanding commitments and future work must also be considered.

Utilization provides a complementary measure:

`utilization = actual / planned × 100`

A category with 90% utilization requires more attention than a category at 20%, even when both remain technically within budget.

The examples classify overall health using thresholds while also checking projected expenditure against authorized budget.

---

## Change Control

A budget baseline should not silently change when project scope changes.

The implementations use change requests to model controlled modification.

A change request contains:

- an identifier;
- a business or delivery reason;
- a requested amount;
- a lifecycle state.

The state begins as `PROPOSED` and can become `APPROVED` or `REJECTED`.

An approved change contributes to the authorized budget. A proposed change does not.

This distinction prevents an unapproved request from being treated as available financial authorization.

The modeled change `CR-001` represents additional compliance testing with a requested value of INR 240,000.

---

## Python Implementation

The Python implementation uses `Decimal` rather than binary floating-point arithmetic for monetary values. This avoids common financial precision problems caused by representing decimal fractions as binary floating-point numbers.

`BudgetLine` owns category-level planned, committed, and actual values.

`ProjectBudget` owns the project-wide baseline, contingency, approved changes, lifecycle state, reporting, and forecasting rules.

The project lifecycle is represented by `DRAFT`, `APPROVED`, `ACTIVE`, and `CLOSED`.

The implementation prevents an empty budget from being approved and prevents negative allocations or negative transactions.

The `projected_cost` calculation considers actual spending and remaining commitments. This is important because a financial report based only on posted expenses can understate the amount the project is already obligated to spend.

The reporting function provides category-level variance and utilization while the `health` method evaluates the financial state.

The validation examples deliberately exercise invalid negative allocations, empty-budget approval, and negative expenses.

---

## JavaScript Implementation

The JavaScript implementation uses an event-driven design rather than reproducing the Python object model line by line.

`EventBus` allows operational events such as:

`budget.approved`

`budget.activated`

`expense.recorded`

`commitment.recorded`

`change.requested`

`change.approved`

This reflects an environment in which budgeting is part of a larger application. A real system could use such events to update dashboards, audit records, notifications, or downstream reporting services.

A `Map` stores budget categories, making category lookup explicit rather than requiring repeated array scans.

`Object.freeze()` is used for reporting snapshots so that consumers receive a stable representation of the current budget state rather than a mutable reference to internal objects.

The asynchronous simulation demonstrates how financial events can arrive over time. The implementation does not assume that all transactions are processed in a single synchronous operation.

Validation is performed before financial state changes. Unknown categories and invalid transaction amounts are rejected.

---

## C++ Governance Case Study

The C++ program treats the budget as a governance engine.

The monetary representation uses integer minor currency units rather than floating-point values internally. This provides deterministic arithmetic for the modeled currency representation.

`BudgetPolicy` separates policy from the budget data itself.

The policy controls contingency calculation and identifies changes that require senior approval.

`ProjectBudget` maintains budget lines and change requests using associative containers. Categories are stored in a `std::map`, which provides deterministic lookup and reporting order.

The system has explicit lifecycle transitions:

`Draft → Approved → Active`

Transactions are rejected unless the budget is active.

The change request mechanism demonstrates a second governance layer. A large change does not simply become authorized because a user submitted it. The policy identifies it as requiring additional approval.

The `mergeEligible()` method is a governance-oriented decision function. It represents whether current projected expenditure satisfies the financial authorization boundary.

The case study therefore separates financial data from the rules used to determine whether the project can continue under its current authorization.

---

## Java Enterprise Domain Model

The Java implementation uses explicit domain types to model project budgeting.

`CostCategory` is an enum rather than an arbitrary string. This prevents inconsistent category names such as `Cloud`, `cloud`, and `Cloud Infrastructure` from becoming accidental duplicate concepts inside the same domain model.

`BudgetState`, `ChangeState`, and `BudgetHealth` represent controlled state vocabularies.

`BudgetLine` owns category-level financial values.

`ChangeRequest` is a Java record. Its approval operation returns a new state representation instead of exposing mutable fields directly.

The `ApprovalPolicy` interface separates change-approval policy from the budget itself. `ThresholdApprovalPolicy` is one concrete implementation in which changes above a defined financial threshold require senior approval.

This design demonstrates a useful enterprise principle: financial policy should be explicit rather than scattered across unrelated conditional statements.

The budget service methods enforce lifecycle constraints. Expenses and commitments require an active budget. A budget must contain lines before approval. Duplicate categories and duplicate change requests are rejected.

Java streams are used for aggregate calculations such as total planned budget, approved changes, and actual spending.

---

## PostgreSQL Data Model

The SQL implementation treats the budget as a relational domain.

`projects` stores project-level information and lifecycle state.

`budget_categories` defines controlled financial categories.

`project_budget_lines` connects projects to their approved financial allocations.

`commitments` records financial obligations associated with budget lines.

`expenses` records recognized expenditure.

`change_requests` stores proposed and approved modifications to the baseline.

`reviewers` and `change_approvals` preserve evidence of financial authorization.

Foreign keys prevent orphaned budget records. A commitment cannot reference a nonexistent budget line, and an expense cannot exist without a valid budget line.

Check constraints enforce rules directly inside PostgreSQL. Planned amounts, commitment amounts, expense amounts, and requested change values must be positive.

The project date constraint prevents an end date earlier than the start date.

The contingency-rate constraint limits the value to a valid proportion.

A uniqueness constraint prevents the same project from having duplicate category allocations.

---

## Database Reporting

The `budget_line_actuals` view combines planned, committed, and actual financial information at category level.

This creates a reusable analytical representation without duplicating financial transaction data.

The `project_budget_summary` view calculates:

- direct planned budget;
- contingency;
- approved changes;
- authorized budget;
- actual expenditure.

The analytical queries then calculate utilization, variance, budget health, and approved-change evidence.

This division is important because raw transaction tables answer operational questions, while reporting views answer management questions.

---

## Financial Integrity

Database constraints are stronger than application-only validation when multiple applications can write to the same database.

For example, an application might validate that a planned amount is positive, but another client could bypass that application and issue SQL directly.

The database-level constraint:

`CHECK (planned_amount > 0)`

makes the rule apply regardless of which client submits the data.

Foreign keys similarly prevent invalid relationships.

Transactions provide atomicity for related operations. A change approval and its supporting state update should not leave the database in a partially updated state.

---

## Budget Lifecycle

The modeled lifecycle separates planning from execution.

A `DRAFT` budget is still being prepared.

An `APPROVED` budget has passed the required approval boundary but is not yet receiving operational expenditure.

An `ACTIVE` budget is authorized for execution.

A `CLOSED` budget represents a completed financial control period.

The exact lifecycle used by an organization may be more detailed, but the key design principle remains the same: financial transactions should be constrained by project state.

---

## Contingency Versus Scope Change

These concepts must not be confused.

Contingency addresses uncertainty within the approved project context.

A scope change introduces a new requirement, capability, deliverable, or obligation that was not part of the original baseline.

Using contingency to hide a genuine scope change weakens budget governance.

The change-request model therefore adds approved scope changes separately from contingency.

This makes the authorized amount auditable:

`authorized budget = direct budget + contingency + approved changes`

---

## Common Budgeting Failure Modes

### Treating estimates as authorization

An estimate is a planning input. It is not automatically permission to spend.

### Replacing the baseline with actual values

Changing the original budget whenever expenditure changes destroys meaningful variance analysis.

### Ignoring commitments

A project may have relatively low posted expenditure while already carrying substantial contractual obligations.

### Allowing uncontrolled scope changes

New requirements can increase cost without appearing as obvious overruns if they are not represented through change control.

### Using floating-point arithmetic for money

Binary floating-point representation can introduce precision errors. The Python and Java implementations use decimal representations, while the C++ implementation uses integer minor units.

### Relying exclusively on application validation

If several applications access the same financial database, important integrity rules should also exist at the database layer.

### Treating contingency as unrestricted spending

Contingency should remain governed by the organization's financial policy.

---

## Performance Considerations

Budget calculations are generally inexpensive at project scale, but reporting can become expensive when transaction volumes increase.

The SQL implementation therefore indexes relationships used by reporting queries, especially:

`project_id`

`budget_line_id`

`expense_date`

`change_request project/status`

and approval relationships.

For a large portfolio, financial reporting should avoid repeatedly scanning every transaction for every dashboard request. Materialized reporting tables, partitioning, aggregation pipelines, or carefully designed analytical views may become appropriate.

Application implementations also use direct category lookup structures such as Python dictionaries, JavaScript `Map`, and Java maps.

---

## Security and Audit Considerations

Financial data requires stronger controls than ordinary application state.

A production implementation should record who created a budget, who approved it, who changed it, who posted expenditure, and when each operation occurred.

The SQL model begins this pattern through reviewers and change approvals.

Authorization should be separated from authentication. Knowing who a user is does not automatically mean that the user is permitted to approve a budget.

Sensitive financial data should be protected through database permissions, application authorization, encrypted transport, controlled secrets, and audit logging.

Approval actions should be append-oriented where audit requirements demand preservation of historical decisions. Overwriting a previous approval without retaining its history weakens auditability.

---

## Forecasting Limitations

The example forecast uses actual expenditure plus remaining commitments.

That model is useful because it is transparent, but it is not a complete project forecasting method.

A production forecast may need:

- remaining work;
- remaining duration;
- resource capacity;
- resource cost rates;
- vendor contracts;
- inflation;
- foreign exchange;
- seasonality;
- historical spending patterns;
- approved but not yet contracted work;
- quantified project risks.

A sophisticated forecast should distinguish committed expenditure from expected expenditure that has not yet become a commitment.

---

## Relationship Between the Implementations

The implementations intentionally use different technical perspectives.

| Implementation | Primary perspective |
|---|---|
| Python | Budget calculation, validation, forecasting, and reporting |
| JavaScript | Event-driven operational workflow |
| C++ | Financial governance and policy evaluation |
| Java | Enterprise domain modeling and approval policy |
| PostgreSQL | Relational integrity and financial reporting |

The underlying financial concepts remain consistent, but the implementations are not simple translations.

Python emphasizes executable financial modeling.

JavaScript emphasizes state changes arriving as events.

C++ emphasizes policy and governance decisions.

Java emphasizes explicit domain abstractions and enterprise validation.

PostgreSQL emphasizes durable financial relationships, integrity constraints, transactions, and analytical queries.

---

## Production Design Considerations

A production project-budgeting system should treat the budget as a controlled financial artifact rather than merely as a collection of numbers.

The baseline should have a defined approval authority.

Financial transactions should be immutable or strongly audited where required.

Changes should preserve historical authorization evidence.

Budget calculations should use appropriate monetary precision.

Forecasting should distinguish actual, committed, and expected expenditure.

Reporting should expose both category-level and project-level variance.

Database constraints should protect fundamental financial relationships.

The most important design boundary is the distinction between **planned**, **authorized**, **committed**, **actual**, and **forecast** amounts. Keeping these states separate makes a project budget auditable, explainable, and useful for management control.
