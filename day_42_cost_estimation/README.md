# Project Cost Estimation

## Scope

This repository models project cost estimation as a structured process for turning project scope, resource assumptions, historical evidence, uncertainty, and actual spending into a defensible cost forecast.

The implementations use the same core domain but deliberately emphasize different technical perspectives:

- Python provides a comprehensive estimation workbench with bottom-up, parametric, analogous, three-point, risk-based, sensitivity, schedule-cost, forecasting, validation, and reporting logic.
- JavaScript models estimation as an event-driven application with mutable project state, subscriptions, immutable snapshots, asynchronous persistence, and forecast calculations.
- C++ presents a compact technical case study in which direct cost drivers, risk exposure, category aggregation, validation, and sensitivity analysis are encapsulated in an estimation engine.
- Java models an enterprise-oriented estimation domain using records, enums, collections, immutable value-oriented data structures, explicit state transitions, and policy abstractions.
- PostgreSQL represents the estimation domain relationally and moves important financial integrity rules into constraints, indexes, views, transactions, and database-side validation.

The central distinction is between a cost estimate and a budget. An estimate is an analytical forecast of what the project is expected to cost. An approved budget is the financial boundary against which that estimate is evaluated. A project can therefore have an estimate that is lower than, equal to, or greater than its approved budget.

---

## Cost Estimation Model

A practical project estimate can be represented as:

`Estimated Project Cost = Direct Cost + Expected Risk Cost + Management Reserve`

This model is intentionally separated into components because the components represent different sources of financial uncertainty.

**Direct cost** represents identifiable expenditure associated with planned work. Examples include labor, infrastructure, testing, security activities, training, equipment, and external services.

**Expected risk cost** represents the expected monetary value of identified uncertain events:

`Expected Monetary Value = Probability × Financial Impact`

For example, a 25% probability of an integration problem costing 22,000 produces an expected exposure of 5,500.

**Management reserve** provides an additional controlled allowance for uncertainty that is not fully represented by individual identified risks. In the implementations, it is modeled as a percentage of direct cost. The reserve rate is deliberately explicit rather than hidden inside individual unit rates.

This separation makes the estimate auditable. A reviewer can determine whether a change came from scope, resource pricing, quantity, identified risk, or reserve policy.

---

## Fundamental Estimation Approaches

### Bottom-Up Estimation

Bottom-up estimation decomposes a project into cost-bearing work or resources and calculates the cost of each item.

The Python implementation represents an item with:

`name`, `quantity`, `unit_cost`, `category`, and `confidence`.

The fundamental calculation is:

`Item Cost = Quantity × Unit Cost`

The project-level direct cost is the sum of all validated items.

This approach is useful when the work structure is sufficiently understood to identify specific resources and quantities. It also produces a detailed audit trail because a total can be traced back to individual cost drivers.

The Python example separates requirements analysis, engineering, testing, cloud infrastructure, security validation, and training. These are deliberately different cost categories rather than repeated generic tasks.

### Parametric Estimation

Parametric estimation uses a measurable cost relationship such as cost per inspection, cost per employee trained, cost per device deployed, or cost per service transaction.

The implementation uses:

`Parametric Cost = Units × Cost Per Unit + Fixed Cost`

The JavaScript and Python implementations use an infrastructure-inspection scenario where the number of units and the unit cost provide the principal variable component.

Parametric estimation is particularly useful when a historical or operational relationship between volume and cost is stable enough to justify the model. Its weakness is that the unit-cost relationship can become unreliable when scale, technology, complexity, geography, or resource productivity changes.

### Analogous Estimation

Analogous estimation uses completed projects as reference points.

The Python implementation uses historical project costs combined with similarity weights. A highly similar historical project contributes more strongly to the weighted estimate than a weakly comparable project.

The quality of an analogous estimate therefore depends on whether the historical projects are genuinely comparable. A project that appears similar at a high level may still have materially different integration requirements, security controls, staffing models, deployment environments, or regulatory requirements.

### Three-Point Estimation

Three-point estimation explicitly models uncertainty using:

- optimistic cost
- most-likely cost
- pessimistic cost

The implementations calculate both a simple triangular estimate and a PERT-style estimate:

`PERT = (Optimistic + 4 × Most Likely + Pessimistic) / 6`

The Python implementation also calculates the approximate standard deviation:

`Standard Deviation = (Pessimistic − Optimistic) / 6`

Three-point estimation is useful when uncertainty is material and a single deterministic number would conceal the range of plausible outcomes.

---

## Risk and Uncertainty

Risk should not be confused with an ordinary cost item.

A cost item describes planned expenditure. A risk describes an uncertain event and its potential financial impact.

The Python, JavaScript, C++, Java, and SQL implementations keep these concepts separate.

For example:

`Security validation = planned cost`

`Security remediation = uncertain risk exposure`

This distinction prevents a project team from embedding arbitrary risk padding into every line item without being able to explain where the uncertainty originated.

The risk model uses probability and impact. The expected monetary value provides a quantitative exposure that can be included in the estimate.

The model is not a prediction that the expected value will actually be spent. A 25% probability of a 22,000 loss does not mean the project will necessarily spend 5,500. It means that 5,500 is the mathematical expected exposure under the specified probability assumption.

---

## Python Implementation

The Python program is the broadest implementation.

It begins with structured `CostItem`, `Risk`, `ThreePointEstimate`, and `ProjectEstimate` objects. Validation occurs at the boundary of the calculation rather than after invalid values have already entered the model.

The `ProjectEstimate` class separates:

- direct cost
- expected risk cost
- management reserve
- total estimated project cost

The script then expands the model into practical estimation techniques.

The labor calculator converts role-level hours and rates into a labor estimate. The monthly burn simulation distributes an approved amount according to a supplied spending profile. The schedule-cost calculation demonstrates how schedule delay can produce additional labor expenditure.

The sensitivity analysis changes the base estimate according to explicitly defined percentage changes. This is useful for determining which cost assumptions have the greatest effect on the final result.

The Monte Carlo component uses a triangular distribution based on optimistic, most-likely, and pessimistic estimates. It produces percentile-oriented outputs such as P50, P80, and P90. These values are more informative for uncertainty analysis than a single deterministic forecast.

The script also performs validation of negative quantities, negative rates, invalid probabilities, invalid reserve rates, and other malformed inputs.

The reporting functions write a JSON project estimate and a CSV cost-item dataset. This demonstrates how an estimation model can become an operational artifact rather than remaining only an in-memory calculation.

---

## JavaScript Implementation

The JavaScript program treats the estimate as an event-driven application state.

`CostEstimate` maintains the project state and emits events whenever important changes occur. Subscribers can observe events such as `cost-item-added`, `risk-added`, `estimate-completed`, and `estimate-approved`.

This design is useful for browser or Node.js applications where user-interface components, logging services, audit systems, or persistence layers may need to react to estimation changes without being embedded directly inside the calculation methods.

The JavaScript implementation also uses explicit project states:

`draft → estimated → approved → forecasting → closed`

The state transitions prevent operations that do not make sense in a particular lifecycle stage. For example, a closed project cannot accept a new cost item.

The `snapshot()` method creates an immutable representation of the current financial state. This is useful when an application needs a stable object for display, persistence, logging, or audit.

The asynchronous persistence function uses a Promise to represent an external persistence operation without introducing a third-party dependency.

The JavaScript program also includes earned-value forecasting. The cost performance index is calculated as:

`CPI = Earned Value / Actual Cost`

An estimate-at-completion calculation then uses the performance ratio to project the final cost.

This makes the JavaScript implementation complementary to the Python model: it focuses more strongly on application state, events, asynchronous behavior, and runtime workflow.

---

## C++ Case Study

The C++ program models a project estimation engine for a public infrastructure monitoring platform.

`CostDriver` represents a planned cost-bearing resource. The class calculates the cost from quantity and unit price.

`Risk` represents uncertain expenditure separately and exposes an expected-value calculation.

`CostEstimationEngine` aggregates both structures and provides:

- direct cost calculation
- expected risk cost
- management reserve
- total estimate
- category-level aggregation

The category aggregation uses `std::map`, while numerical aggregation uses standard-library algorithms such as `std::accumulate`.

The design intentionally keeps the estimation engine independent from the case-study wrapper. This makes the calculation layer easier to reason about and test.

The case study also performs sensitivity analysis by applying different percentage changes to the integrated estimate. This allows management to observe how changes in assumptions influence total projected cost.

C++ is particularly appropriate for demonstrating how an estimation engine can be expressed as a compact domain component with explicit ownership, value structures, standard containers, exception-based validation, and predictable computational behavior.

The main calculation is linear in the number of cost drivers and risks. A complete aggregation pass therefore has approximately `O(n + r)` time complexity for `n` cost drivers and `r` risks.

---

## Java Enterprise Domain Model

The Java implementation emphasizes explicit domain types.

`CostCategory` prevents arbitrary category strings from silently entering the model. The compiler therefore helps enforce the distinction between labor, infrastructure, security, training, and external costs.

`ProjectState` represents lifecycle state directly rather than using loosely defined strings.

Java records are used for `CostItem`, `RiskEvent`, and `ApprovalPolicy`. These types represent values whose identity is defined primarily by their contents.

The `ProjectEstimate` class owns the lifecycle of the estimate. Invalid transitions are rejected. For example, approval cannot occur while the estimate is still in draft state.

The implementation also uses `BigDecimal` rather than binary floating-point arithmetic for financial values. This is an important financial-system design decision because decimal monetary calculations should avoid the representation surprises associated with ordinary floating-point types.

The `MergeStyleCostModel` is intentionally a policy abstraction rather than a cost calculator. It demonstrates how an enterprise system can isolate policy evaluation from financial arithmetic. Its inputs represent approval count, independent review presence, and required checks.

This separation illustrates an important design principle: domain calculations, lifecycle rules, and policy rules should not be collapsed into one large conditional block.

---

## PostgreSQL Data Model

The SQL implementation models cost estimation as relational data.

The `projects` table stores the project-level budget, reserve policy, and lifecycle state.

`cost_items` stores the planned cost drivers. A foreign key connects each item to its project. A uniqueness constraint prevents duplicate descriptions inside the same project.

`project_risks` stores probability, impact, and risk status independently of planned costs.

`actual_costs` records expenditure that has already occurred.

`monthly_forecasts` stores remaining forecast expenditure by month.

The schema uses PostgreSQL enumerated types for project status, cost category, and risk status. This prevents arbitrary status strings from entering the database.

Financial columns use `NUMERIC` rather than floating-point types. This is appropriate for monetary data because exact decimal arithmetic is preferable to approximate binary floating-point representation.

---

## Database Integrity

Several rules are enforced directly by the database.

Quantities and unit costs cannot be negative.

Risk probabilities must remain between zero and one.

Risk impact cannot be negative.

Reserve rates must remain between zero and one.

A cost item must belong to an existing project through a foreign key.

Deleting a project cascades to its dependent cost records and risk records because those records have no meaningful existence without the project.

These constraints reduce dependence on application-level validation. Application code should still validate inputs for usability, but the database provides the final integrity boundary for persisted information.

---

## SQL Cost Summary

The `project_cost_summary` view combines direct cost, expected risk cost, reserve, and total estimated cost.

The direct cost subquery aggregates:

`quantity × unit_cost`

The risk subquery aggregates:

`probability × impact`

The final estimate adds the reserve calculated from the project's configured reserve rate.

This makes the calculation reusable from reporting queries without copying the same aggregation logic into every consumer.

The category query also calculates each category's percentage of direct cost. This supports cost-driver analysis by showing where the estimate is concentrated.

---

## Forecasting Actual Cost

An estimate becomes more useful when it can be compared with actual expenditure.

The SQL script records actual costs separately from planned cost items.

The forecast query combines:

`Actual Cost to Date + Remaining Forecast = Estimate at Completion`

This is distinct from the original baseline estimate.

The baseline answers what the project was expected to cost when estimated.

The estimate at completion answers what the project is currently expected to cost based on actual expenditure and the remaining forecast.

The difference between the approved budget and estimate at completion provides a current forecast variance.

---

## Reserve Versus Contingency

The implementations distinguish identified risk exposure from a general management reserve.

Expected risk cost is calculated from explicitly modeled risks.

Management reserve is calculated as a configurable percentage of direct cost.

This distinction is useful because identified risk and broader uncertainty have different management meanings. A project manager can review the individual risk register while separately reviewing whether the reserve policy remains appropriate.

A reserve should not be treated as permission to increase every cost item without explanation. Its value comes from being visible, quantified, and governed.

---

## Sensitivity Analysis

Sensitivity analysis tests how assumptions influence the final estimate.

The C++ implementation evaluates a range of percentage changes around the base estimate.

The Python implementation evaluates named cost assumptions such as labor rates, cloud costs, efficiency, and scope changes.

A sensitivity analysis is useful because a project can have a large total estimate while being highly dependent on only one or two assumptions.

For example, a software project may have many cost items but still be dominated by engineering labor. In that case, a change in labor productivity may have a larger financial effect than a small change in training expenditure.

---

## Schedule and Cost Relationship

Schedule assumptions directly influence cost when resources are paid for time.

The Python implementation calculates labor expenditure from:

`Hourly Rate × Hours Per Day × Duration`

An eight-day schedule extension therefore has an identifiable incremental labor cost when the affected personnel remain assigned.

The relationship is not universally linear. Some costs are fixed, some are variable, and some are stepped. A cloud contract, for example, may have a different cost behavior from an hourly contractor.

A production estimation system should therefore classify cost drivers according to their actual behavior rather than assuming every cost scales linearly with schedule duration.

---

## Forecasting and Performance

A baseline estimate should not remain unchanged when reliable actual information becomes available.

The JavaScript implementation demonstrates a performance-based forecast using cost performance index.

The basic interpretation is:

- CPI above 1 indicates that earned value is being achieved at a lower actual cost than the corresponding earned amount.
- CPI below 1 indicates cost inefficiency.
- CPI equal to 1 indicates cost performance at the baseline ratio.

A forecast based on CPI is only meaningful when the underlying earned-value measurement is credible. A mathematically precise formula cannot compensate for poor measurement of actual work completion or actual expenditure.

---

## Edge Cases

A robust estimation system must explicitly handle invalid conditions.

The implementations reject negative quantities and unit costs because they do not represent ordinary project expenditure.

Risk probabilities outside the `[0, 1]` interval are rejected because they cannot represent valid probabilities.

Three-point estimates should maintain the ordering:

`Optimistic <= Most Likely <= Pessimistic`

The Python implementation demonstrates the importance of this validation even though the demonstration deliberately shows the need for an explicit ordering check.

An estimate with no cost items is rejected before it can be marked as complete.

Lifecycle-based implementations reject state transitions that would create an inconsistent financial record.

The SQL schema provides another layer of protection by enforcing numeric and referential constraints after application validation.

---

## Financial Precision

The Python implementation uses `Decimal` for monetary calculations.

The Java implementation uses `BigDecimal`.

The SQL implementation uses PostgreSQL `NUMERIC`.

The C++ and JavaScript examples use ordinary numeric arithmetic for readability and then round displayed monetary results. In a production financial system, exact decimal or integer-minor-unit arithmetic should generally be preferred where financial precision is critical.

Currency conversion should also be treated as a separate domain operation. An estimate should not silently mix currencies without recording the currency, conversion rate, conversion date, and source of the rate.

---

## Performance Considerations

Most calculations in these examples are linear.

Summing `n` cost items requires `O(n)` work.

Summing `r` risks requires `O(r)` work.

Grouping costs by category is also approximately `O(n)` for ordinary hash-based or ordered-map implementations, with the precise behavior depending on the selected data structure.

The SQL indexes target common access patterns involving project identifiers, cost categories, risk status, actual-cost dates, and forecast months.

The Monte Carlo implementation is intentionally more computationally expensive because it performs many independent simulations. Its approximate time complexity is `O(k)` for `k` simulation iterations, with additional work for percentile extraction.

For large production models, simulation count, distribution choice, correlated risks, and data quality should be considered before interpreting probabilistic outputs.

---

## Common Estimation Errors

A major estimation failure occurs when scope uncertainty is disguised as a highly precise number. Precision in the final decimal value does not imply precision in the underlying assumptions.

Another failure occurs when historical projects are used without checking comparability. A historical cost is evidence only to the extent that the historical project resembles the current one in meaningful cost drivers.

Double-counting risk is also problematic. If a risk has already been incorporated into a pessimistic estimate or inflated unit rate, adding the same risk again as a separate reserve can overstate the forecast.

Using a reserve without a documented basis can hide estimation weakness. Reserve assumptions should be visible and adjustable.

Actual cost should not automatically be treated as evidence that the original estimate was wrong. A project can spend according to plan while the remaining forecast changes because new information becomes available.

---

## Practical Interpretation

The six implementations represent different layers of a cost-estimation system.

The Python implementation emphasizes analytical breadth and experimentation.

The JavaScript implementation emphasizes application behavior, events, asynchronous operations, and lifecycle state.

The C++ implementation emphasizes a compact computational engine and category aggregation.

The Java implementation emphasizes strongly typed domain modeling, lifecycle transitions, decimal financial arithmetic, and policy abstraction.

The PostgreSQL implementation emphasizes persistent financial data, integrity constraints, aggregation, forecasting, indexing, and transactions.

Together, these perspectives show why cost estimation is not simply a multiplication exercise. A defensible estimate requires a structured cost model, explicit uncertainty, appropriate estimation techniques, validation, financial precision, traceability, and mechanisms for updating the forecast when project conditions change.
