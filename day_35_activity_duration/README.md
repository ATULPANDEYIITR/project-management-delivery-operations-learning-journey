# Activity Duration Estimation

## Scope

This repository models the estimation of how long a task or activity may take, from a simple point estimate through uncertainty-aware and dependency-aware project estimation.

The implementations use software-development activities such as requirements analysis, implementation, testing, documentation, and integration because these activities expose important differences between estimated effort, actual duration, uncertainty, and elapsed project time.

The central distinction is:

`activity duration estimate` describes the expected time for one activity under stated assumptions, while `elapsed project duration` also depends on dependencies, sequencing, and whether independent activities can proceed concurrently.

The six deliverables deliberately approach the same domain from different technical perspectives:

| File | Technical role |
| --- | --- |
| Python | Comprehensive estimation engine with historical calibration, dependency scheduling, uncertainty analysis, and simulation |
| JavaScript | Event-driven and asynchronous activity model with probabilistic simulation |
| C++ | Repository-development duration engine emphasizing strongly structured data, dependency validation, and performance-conscious simulation |
| Java | Enterprise-oriented domain model with immutable records, services, validation, and explicit scheduling responsibilities |
| SQL | Relational activity-estimation model with constraints, historical observations, indexes, views, recursive dependency analysis, and transactions |

## Core Concept: Activity Duration

An activity duration estimate is an attempt to quantify how much time a defined task will require.

A useful estimate should have a clearly defined activity boundary. For example, `Backend implementation` is a more useful estimation unit than an ambiguous statement such as `finish the project`.

The quality of an estimate depends on the information available when the estimate is produced. Unknown requirements, technical uncertainty, external dependencies, interruptions, unfamiliar systems, and rework can all cause actual duration to differ from the initial estimate.

The code therefore avoids treating a duration as an immutable fact. Several implementations represent uncertainty explicitly through optimistic, most-likely, and pessimistic values.

## Three-Point Estimation

The three-point model uses:

- **Optimistic duration**: a favorable but credible completion duration when few problems occur.
- **Most-likely duration**: the duration considered most representative under normal conditions.
- **Pessimistic duration**: a credible high-duration scenario when significant complications occur.

The implementations validate the ordering:

`optimistic <= most_likely <= pessimistic`

Negative durations are rejected because they do not represent meaningful elapsed task time.

A three-point estimate is particularly useful when the estimator can describe a reasonable range but cannot justify one precise number.

### PERT expected duration

The implementations calculate the PERT-style weighted expected duration as:

`E = (O + 4M + P) / 6`

where `O` is optimistic duration, `M` is most-likely duration, and `P` is pessimistic duration.

The most-likely estimate receives four times the weight of each outer estimate. This produces a value that is generally closer to the most-likely scenario than a simple arithmetic mean.

The estimated uncertainty is represented using:

`SD ≈ (P - O) / 6`

This is an approximation used by the implementations to describe the spread implied by the three-point range.

## Python Implementation

The Python program is the broadest implementation of the estimation domain.

`ThreePointEstimate` is a value object that validates duration boundaries and exposes both the simple average and PERT expected duration. This makes the difference between an unweighted average and a weighted estimate executable rather than purely descriptive.

`HistoricalTask` records previous estimates and actual durations. The program uses those observations to calculate an actual-to-estimated factor. A factor greater than `1.0` indicates that historical work took longer than estimated on average.

The program also calculates category-specific calibration factors. This matters because different activity categories can have different estimation behavior. Analysis, implementation, testing, and integration do not necessarily have the same historical error pattern.

The dependency model is represented by `Task.dependencies`. The program performs topological ordering and rejects circular dependencies. A dependency therefore affects when an activity can begin rather than changing the mathematical definition of its individual PERT estimate.

The Python implementation also contains:

- approximate confidence ranges;
- combined uncertainty for independent activity estimates;
- dependency-aware scheduling;
- triangular-distribution Monte Carlo simulation;
- project-level duration percentiles;
- conversion from working effort to calendar dates;
- mean absolute error;
- mean absolute percentage error;
- signed estimation bias;
- invalid three-point estimates;
- missing dependencies;
- circular dependency detection.

The Monte Carlo implementation is particularly important because a single expected duration hides the distribution of possible outcomes. The program reports median, 80th, 90th, and 95th percentile durations so a schedule can be evaluated at different risk levels.

## JavaScript Implementation

The JavaScript implementation emphasizes event-driven behavior and asynchronous activity execution rather than reproducing the Python architecture.

`DurationEstimate` is a JavaScript class responsible for validating the three-point estimate and calculating PERT statistics.

`EventBus` provides an event-driven mechanism for reporting activity start and completion. The execution example uses `Promise.all()` to represent independent activities that can proceed concurrently.

This distinction is important when estimating elapsed time. If three independent activities require 4, 5, and 3 hours respectively and can genuinely execute at the same time, the elapsed time is closer to the longest activity than to the sum of all three durations.

The JavaScript implementation also contains a seeded pseudo-random generator and triangular sampling. A deterministic seed makes simulation results reproducible while still exposing the probabilistic nature of the model.

The dependency resolver uses depth-first traversal and explicitly detects cycles. A circular dependency is a structural failure because no valid start order exists.

The JavaScript quality metrics calculate mean absolute error, mean absolute percentage error, and signed bias from completed activities.

## C++ Case Study: Repository Development Duration Engine

The C++ program models a software repository delivery plan containing:

`Requirements analysis → implementation → verification → system integration`

The implementation contains parallel backend and frontend branches after requirements analysis.

The important scheduling behavior is:

`Requirements analysis`

must finish before both implementation branches can start.

`Backend verification`

depends only on backend implementation.

`Frontend verification`

depends only on frontend implementation.

`System integration`

waits for both verification activities.

This produces a dependency graph rather than a simple sequential list.

### C++ architecture

`ThreePointEstimate` is a validated value type for uncertainty.

`DurationEngine` applies historical calibration to activity estimates.

`DependencyGraph` owns graph validation and topological ordering. It rejects unknown dependencies and cycles.

`ScheduledActivity` records the calculated start and finish position.

The scheduler calculates the earliest possible start of an activity from the latest finish among its prerequisites:

`start = max(finish of every prerequisite)`

The duration of the activity is then added to that start position.

This allows independent branches to overlap instead of incorrectly adding every activity duration into one sequential total.

### Monte Carlo behavior

The C++ program samples each activity using a triangular distribution derived from its three-point estimate.

Every simulation constructs a possible project completion time while respecting the dependency graph. The resulting population is sorted to calculate percentile-based completion thresholds.

The 90th percentile therefore represents a materially different planning statement from the expected duration. It answers a risk-oriented question: what completion duration is exceeded by only approximately ten percent of the simulated outcomes under the model assumptions?

### C++ performance considerations

The dependency graph uses hash maps for activity lookup and state tracking. Topological traversal is linear in the number of activities and dependency edges, expressed conceptually as `O(V + E)`.

Monte Carlo simulation scales approximately with:

`O(S × (V + E))`

where `S` is the number of simulations.

For very large planning graphs, repeatedly reconstructing graph structures would be wasteful. A production implementation could validate and compile the dependency graph once, then reuse the topological order across simulations.

## Java Implementation

The Java implementation takes an enterprise-domain approach.

The `DurationEstimate`, `HistoricalDuration`, `Activity`, and `ScheduleEntry` records represent immutable domain values. This is useful for estimation because a previously calculated value should not silently change through an unrelated reference.

`HistoricalCalibrator` owns the rule for converting historical observations into category-specific calibration factors.

`DependencyResolver` is responsible for graph validation and topological ordering. This keeps dependency concerns separate from estimation mathematics.

`ScheduleService` combines the calibrated activity duration with dependency constraints to calculate start and finish positions.

`MonteCarloService` models project-duration uncertainty independently from the deterministic schedule service. This separation makes the probabilistic analysis explicit rather than hiding it inside ordinary scheduling logic.

The Java implementation also validates invalid estimate ranges, duplicate activities, unknown dependencies, and circular dependencies.

## SQL Data Model

The PostgreSQL script treats duration estimation as a relational domain.

### Repositories

`repositories` identifies the development context in which activities exist.

A repository can contain many activities, allowing historical observations and planned activities to be associated with a specific engineering context.

### Activities

`activities` stores:

- activity name;
- activity category;
- status;
- optimistic duration;
- most-likely duration;
- pessimistic duration;
- start timestamp;
- completion timestamp.

The database enforces the basic estimation invariants using `CHECK` constraints.

The database therefore rejects a negative duration and rejects a three-point estimate in which the optimistic value is greater than the most-likely value or the most-likely value is greater than the pessimistic value.

This is an important distinction between application validation and database integrity. Application code can validate input before sending it to PostgreSQL, but the database constraint protects the stored data from invalid writes arriving through another application or administrative process.

### Activity dependencies

`activity_dependencies` represents prerequisite relationships.

The table contains two foreign keys back to `activities`:

`dependent_activity_id`

identifies the activity that must wait.

`prerequisite_activity_id`

identifies the activity that must finish first.

A self-dependency is rejected because an activity cannot meaningfully require itself to finish before it starts.

The SQL model does not attempt to enforce arbitrary multi-row cycles using a simple `CHECK` constraint. Cycle detection is a graph-level operation, which is why the application implementations perform explicit graph validation and the SQL script uses recursive queries for dependency-depth analysis.

### Historical observations

`historical_duration_observations` records the original estimate and the actual completed duration.

This makes estimation calibration data-driven.

The `historical_calibration` view groups completed observations by activity type and calculates:

- number of observations;
- actual-to-estimated factor;
- average signed error;
- mean absolute error.

A positive signed error means completed work took longer than estimated.

## Database Constraints and Derived Estimates

The `activity_duration_estimates` view calculates PERT expected duration directly from the stored three-point values.

The source estimates remain unchanged. The expected value is derived whenever the view is queried.

This avoids storing duplicated calculated values that could become inconsistent with the underlying estimates.

`calibrated_activity_estimates` then combines the PERT value with historical category behavior.

The SQL model therefore distinguishes:

`raw estimate → PERT expected estimate → historically calibrated estimate`

Each layer has a different purpose.

## Dependency-Aware Duration

An activity's individual duration and a project's elapsed duration are not interchangeable.

Suppose two activities are both available after requirements analysis:

`Backend implementation`

and

`Frontend implementation`

They may execute concurrently if there are sufficient resources and no additional dependency prevents it.

The project therefore does not necessarily require:

`backend duration + frontend duration`

of elapsed time.

Instead, the parallel portion is constrained by the branch that finishes later.

Once both branches reach `System integration`, the integration activity cannot begin until both prerequisites are complete.

This creates a critical-path-like effect even though the implementations do not require a separate critical-path library.

## Historical Calibration

Historical calibration is useful when previous activities are sufficiently comparable to the new activity.

For example, if implementation activities historically required 1.20 times their estimated duration, a raw 15-hour implementation estimate would produce a calibrated value of approximately:

`15 × 1.20 = 18 hours`

Calibration should not be treated as a universal correction factor.

A historical factor derived from integration activities should not automatically be applied to database analysis activities. The implementations therefore support category-specific calibration.

Historical data also has to be sufficiently representative. A factor calculated from a tiny or structurally different sample can produce false confidence.

## Estimation Quality

An estimate should be evaluated after the activity completes.

The implementations calculate several useful measures.

### Mean absolute error

`MAE = average(|actual - estimated|)`

This measures the average magnitude of estimation error without allowing positive and negative errors to cancel.

### Mean absolute percentage error

`MAPE = average(|actual - estimated| / estimated) × 100`

This expresses error relative to the original estimate.

Very small estimates can make percentage-based metrics unstable, so production systems should interpret MAPE carefully.

### Signed bias

`Bias = average(actual - estimated)`

A positive value indicates systematic underestimation in the observed sample.

A negative value indicates systematic overestimation.

Unlike absolute error, signed bias deliberately preserves direction.

## Uncertainty and Percentiles

A single value such as `12 hours` can create an illusion of precision.

A three-point model such as:

`8 / 12 / 24 hours`

communicates that the estimator considers a substantial range plausible.

Monte Carlo simulation extends this idea from one activity to a dependency graph.

The resulting distribution can provide values such as:

- median duration;
- 80th percentile;
- 90th percentile;
- 95th percentile.

These percentiles are not guarantees. They are outputs of a model based on assumptions about activity-duration distributions and dependencies.

The implementations use triangular distributions because they can be constructed directly from optimistic, most-likely, and pessimistic values without requiring a large historical dataset.

## Effort, Duration, and Calendar Time

The amount of work associated with an activity should not automatically be interpreted as elapsed calendar time.

An estimate of `24 working hours` could correspond to approximately three eight-hour working days for one person under ideal allocation.

The actual calendar completion date can be longer when weekends, holidays, interruptions, meetings, resource contention, waiting time, or external dependencies are present.

Conversely, multiple people can sometimes reduce elapsed time when an activity can be decomposed safely into independent work.

The Python implementation explicitly demonstrates conversion from working hours to working dates to show this distinction.

## Common Estimation Failure Modes

### False precision

Reporting `13.27 hours` can suggest more knowledge than the estimation process actually provides.

The three-point and probabilistic implementations preserve uncertainty rather than hiding it.

### Ignoring historical bias

If comparable activities repeatedly take longer than estimated, continuing to use uncalibrated estimates can reproduce the same error.

The historical-calibration implementations expose this bias quantitatively.

### Adding every activity sequentially

Summing every duration is incorrect when independent activities can execute concurrently.

The dependency-aware implementations calculate the start time from prerequisite completion instead.

### Treating dependencies as durations

A dependency does not inherently add a fixed number of hours. It constrains when another activity may begin.

The graph implementations keep dependency relationships separate from duration values.

### Ignoring uncertainty

A task with an optimistic duration of 4 hours and pessimistic duration of 30 hours is fundamentally different from a task with a narrow 8-to-10-hour range, even if their most-likely values are similar.

The range itself is an estimation-risk signal.

### Using incomparable historical data

Historical calibration becomes misleading when the previous activities differ substantially in complexity, technology, scope, staffing, or uncertainty.

A calibration factor should therefore be interpreted in the context of the activity category and available evidence.

## Security and Integrity Considerations

Duration estimates are operational data and can influence planning decisions. A production system should prevent unauthorized modification of historical observations because changing actual durations can distort future calibration.

The SQL implementation protects structural integrity with primary keys, foreign keys, uniqueness rules, and `CHECK` constraints.

The database also records timestamps for activity start and completion. In a production environment, audit records would normally be retained rather than allowing historical state to be silently rewritten.

The application implementations validate dependency references and reject circular graphs before scheduling. This prevents invalid dependency structures from producing misleading duration calculations.

## Production Considerations

A production estimator should preserve the original estimate alongside later revisions rather than overwriting the first estimate. This makes estimation drift measurable.

Historical calibration should normally be based on completed activities and should distinguish activity categories where sufficient data exists.

Simulation assumptions should be stored and versioned when schedule decisions depend on them. Changing the distribution or dependency graph can materially change percentile results.

The estimation model should also distinguish active work time from waiting time when the business process requires that distinction. A database migration may involve direct engineering work plus waiting for deployment windows, approvals, or external systems. Treating all elapsed time as developer effort would distort future estimates.

The most important data boundary is therefore:

`what the activity is expected to require`

versus

`when the activity is expected to finish`

The first is an estimation problem. The second is a scheduling problem influenced by dependencies, concurrency, calendars, and uncertainty.
