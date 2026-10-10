# Schedule Review

## Scope

Schedule review is the controlled examination of a planned sequence of work to determine whether the dates, dependencies, resource assignments, workload, progress, and delivery assumptions remain credible.

A schedule review is different from simply displaying a calendar. A calendar answers where work has been placed. A review asks whether the placement is internally consistent and whether the resulting plan can still support the intended delivery outcome.

The six implementations model the same technical subject from different perspectives:

| Deliverable | Primary perspective |
|---|---|
| Python | Analytical schedule-review engine with validation, dependency analysis, capacity checks, critical-path analysis, reporting, and export |
| JavaScript | Event-driven review workbench with mutable task state, review events, policy evaluation, and machine-readable evidence |
| C++ | Performance-oriented governance case study using explicit data structures and dependency-graph analysis |
| Java | Enterprise domain model using records, interfaces, immutable collections, explicit review rules, and typed review decisions |
| SQL | Relational schedule-review model with integrity constraints, dependencies, resource analysis, progress analysis, recursive queries, transactions, and review history |

The examples use a software delivery schedule because it exposes dependency, workload, progress, and release-planning problems clearly. The mechanisms are applicable to operational schedules, maintenance plans, implementation programs, training calendars, production plans, and other dependency-driven work.

## Schedule Review Concepts

A schedule contains tasks with at least four important dimensions: time, work, responsibility, and relationship.

Time is represented by start and end dates. Work is represented by planned effort and progress. Responsibility identifies the resource assigned to the task. Relationships identify prerequisites that constrain when work can begin.

A useful review therefore examines the schedule from multiple angles rather than relying on one date or one progress percentage.

### Calendar validity

Every task must have a coherent interval. The end date cannot precede the start date, durations should be calculated consistently, and progress values must remain within their permitted range.

The implementations reject malformed task ranges and invalid progress values instead of allowing invalid state to silently enter the review.

### Dependency validity

A dependency expresses an ordering constraint. If task `TEST` depends on `BUILD`, the review must verify that the planned timing of `BUILD` permits `TEST` to start.

The Python, C++, Java, and SQL implementations explicitly model predecessor and successor relationships. A missing dependency reference is treated as a structural defect rather than as a cosmetic scheduling problem.

A dependency timing violation is different from a resource conflict. A schedule may have valid dependency dates while assigning two overlapping tasks to the same person.

### Resource conflicts

Resource conflicts occur when the same person or resource is assigned to overlapping tasks.

The Python implementation groups tasks by owner and compares their intervals. The JavaScript implementation performs the same analysis through repository state and produces structured conflict objects. The C++ case study uses owner-indexed vectors, while the Java implementation groups immutable task records by resource.

The SQL implementation identifies overlaps through a self-join:

`a.start_date <= b.end_date AND b.start_date <= a.end_date`

The comparison is restricted with `a.task_id < b.task_id` so that each pair is evaluated once.

### Capacity

Calendar overlap and total capacity are related but distinct.

A person can have tasks that do not overlap yet still have more planned work than the available capacity for the planning period. Conversely, total workload may fit within capacity while two tasks collide on the same day.

The examples therefore evaluate both dimensions separately.

The SQL implementation aggregates `planned_hours` by resource and compares the result with `weekly_capacity_hours`. This makes capacity analysis a database query rather than an assumption embedded only in application code.

## Dependency Graph and Critical Path

The dependency structure can be viewed as a directed graph.

A typical sequence in the examples is:

`PLAN -> DESIGN -> BUILD -> TEST -> RELEASE`

A second branch is introduced through schedule-data validation:

`DESIGN -> DATA -> TEST`

This produces a graph rather than a simple linear list.

The Python, C++, and Java implementations detect cycles using depth-first traversal. A cycle such as `A -> B -> C -> A` prevents reliable dependency ordering because there is no valid starting point that satisfies all three relationships.

Critical-path analysis then finds the longest dependency path using task duration as the path weight. The result is useful because delay to a task on the longest dependency chain has greater potential to affect the overall delivery horizon than delay to a task with substantial schedule slack.

Critical-path duration in these examples is calculated as a sum of task durations along a dependency path. It is therefore an educational dependency-path model, not a replacement for a full project scheduling engine with calendars, lag, holidays, working-time rules, and resource leveling.

## Progress Review

Progress is evaluated against the review date rather than treated as an isolated percentage.

For a task already finished by the review date, expected calendar progress is 100 percent. For a task that has not started, expected progress is zero. For a task in progress, the implementations calculate the proportion of its planned calendar interval that has elapsed.

For example, a task with six planned calendar days and three elapsed days has an expected calendar progress of approximately 50 percent. A reported progress of 40 percent therefore indicates negative schedule progress variance under this simplified measure.

This measure is intentionally not earned-value analysis. It does not incorporate budgeted cost, earned value, actual cost, schedule performance index, or cost performance index.

## Python Implementation

The Python program is structured around `Task`, `ScheduleEngine`, and `ScheduleReviewService`.

`Task` owns task-level validation and interval behavior. `ScheduleEngine` performs schedule analysis, including dependency validation, cycle detection, resource conflicts, capacity violations, critical-path analysis, and workload calculation.

`ScheduleReviewService` separates evidence collection from governance. The engine determines what is wrong or potentially risky. The service converts those findings into `ACCEPT`, `REVISE`, or `ESCALATE`.

The distinction matters because a finding is not automatically a decision. A minor warning may permit revision, while a dependency cycle prevents reliable critical-path analysis and therefore requires escalation.

The Python implementation also exports schedule data to CSV and review evidence to JSON. This demonstrates how a schedule review can produce both human-readable output and machine-readable evidence for downstream reporting.

The validation demonstration intentionally rejects an impossible date range and separately detects a dependency cycle. These cases illustrate why schedule validation should happen before analytical calculations.

## JavaScript Implementation

The JavaScript implementation uses Node.js event behavior to represent changes in schedule state.

`ScheduleRepository` extends `EventEmitter`. Adding a task emits `taskAdded`, while changing task progress emits `progressChanged`. A completed review emits `reviewCompleted`.

This event-driven design is useful for applications where schedule changes need to trigger other behavior such as recalculation, dashboard refreshes, audit logging, notifications, or workflow transitions.

`ScheduleAnalyzer` is responsible for dependency analysis, resource conflict detection, capacity analysis, progress variance, and longest-path calculation. `ReviewPolicy` then evaluates the evidence.

This separation prevents the event layer from becoming responsible for schedule mathematics. Events communicate state changes, while analysis classes calculate schedule facts.

The final review is serialized to `schedule-review-evidence.json`, making the result suitable for another Node.js process or an external dashboard.

## C++ Case Study

The C++ program models a repository-governance-style schedule as a technical case study, but its core domain remains schedule review.

`RepositoryGovernanceSchedule` stores tasks in an ordered map. Dependency relationships are represented directly inside each task. The class provides dependency validation, cycle detection, resource conflict analysis, capacity analysis, and critical-path calculation.

The dependency graph is traversed recursively. Memoization is used during longest-path calculation so that a previously calculated dependency path does not need to be recomputed for every downstream task.

The resource analysis first groups task pointers by owner and sorts each owner's tasks by start date. Once a later task starts after the current task ends, subsequent tasks can be skipped for that comparison sequence. This avoids unnecessary comparisons in ordered schedules.

The C++ implementation uses explicit exception handling for malformed tasks and impossible analytical states. A cyclic schedule causes critical-path calculation to fail rather than returning an apparently valid but incorrect path.

## Java Implementation

The Java program represents the schedule as an enterprise domain model.

`Task` is a Java record with immutable task data and validation performed during construction. This prevents callers from changing a task into an invalid state after creation.

`ReviewRule` is an interface that separates individual review policies. The implementation supplies separate rules for dependency correctness, dependency cycles, resource conflicts, and capacity. This design is useful when different organizations require different schedule-review policies.

`ScheduleAnalysisService` produces typed evidence rather than printing findings directly. `ScheduleReviewService` consumes that evidence and determines whether the schedule should be accepted, revised, or escalated.

This structure is particularly useful for enterprise applications because policy rules can be tested independently of presentation code.

The use of `Optional` for a possible dependency cycle makes the absence of a cycle explicit. Immutable collections reduce accidental mutation between analysis and review.

## SQL Data Model

The PostgreSQL implementation represents the schedule as relational data.

The `resource` table stores responsible resources and capacity. `schedule` identifies a particular schedule and its review date. `schedule_task` stores task timing, workload, progress, status, and priority.

Dependencies are modeled separately in `task_dependency`. This is important because one task can have multiple predecessors and one predecessor can support multiple successors.

`task_dependency` uses a composite primary key over predecessor and successor IDs. A self-dependency is prohibited by a check constraint.

Review history is stored in `schedule_review`, while individual review findings are stored in `review_finding`. This prevents the latest review from destroying historical evidence.

Foreign keys ensure that tasks reference real schedules and resources. Cascading deletes maintain referential integrity when a schedule is intentionally removed.

The database also rejects invalid date ranges, negative planned effort, negative actual effort, and progress outside 0 to 100 percent.

## SQL Review Queries

The dependency query identifies predecessor tasks whose end date occurs after the successor's start date.

The resource-conflict query performs a self-join over tasks belonging to the same resource. It detects actual calendar intersection and reports the overlap interval.

The capacity query aggregates planned hours by resource and compares the workload against declared capacity.

The progress query calculates expected progress from the review date and compares it with reported progress.

The recursive dependency query reconstructs dependency paths from root tasks. PostgreSQL recursive common table expressions are useful when the schedule contains a hierarchy or directed dependency structure.

The review transaction demonstrates that a decision and its audit evidence can be persisted atomically. This is important when schedule review becomes part of an operational control process.

## Review Decision Model

The implementations use three conceptual outcomes.

`ACCEPT` means the schedule satisfies the configured review rules.

`REVISE` means the schedule contains actionable problems such as resource overlap, capacity excess, or dependency timing problems, but the schedule remains analyzable.

`ESCALATE` is reserved for conditions that prevent reliable evaluation, particularly dependency cycles in the supplied models.

These outcomes should not be confused with task status. A task can be `IN_PROGRESS` while the schedule is accepted, and a schedule can require revision even when many individual tasks are marked complete.

## Review Findings Versus Decisions

A schedule review should preserve the distinction between evidence and governance.

A resource conflict is evidence. A capacity excess is evidence. A dependency cycle is evidence.

The review policy determines what those findings mean operationally.

This distinction allows the same analytical engine to support different policies. One organization may permit a small capacity variance, while another may require every planned hour to remain within declared capacity.

The Java interface-based policy model makes this distinction explicit. The Python service model and JavaScript `ReviewPolicy` provide the same conceptual separation in different programming styles.

## Common Schedule-Review Failure Modes

### Treating a calendar as proof of feasibility

A visually clean calendar can still contain impossible dependency relationships or excessive resource workload. Dates must be checked against relationships and capacity.

### Checking only task progress

A task at 80 percent completion may still be late if the planned schedule expected 100 percent by the review date. Progress must be interpreted relative to the time available.

### Ignoring resource overlap

Dependencies alone do not expose two independent tasks assigned to the same person during the same period.

### Using total workload as a substitute for overlap analysis

Capacity and concurrency answer different questions. Both need independent checks.

### Allowing cycles into the schedule

A circular dependency cannot produce a valid execution ordering. The review system should identify the cycle before critical-path or sequencing calculations.

### Overwriting review history

Schedule reviews are temporal decisions. Keeping previous review records makes it possible to determine whether a schedule is improving, repeatedly failing the same rule, or changing materially between review dates.

## Performance Considerations

Dependency validation is approximately proportional to the number of dependency edges.

Cycle detection through depth-first traversal is linear in the number of tasks plus dependency edges for an adjacency-list representation.

Resource-overlap detection can become expensive if every task is compared with every other task. Sorting tasks by start date allows comparisons to stop once subsequent intervals cannot overlap the current interval.

Critical-path analysis benefits from memoization. Without memoization, repeated traversal of shared dependency chains can cause unnecessary recomputation.

Database performance depends strongly on indexes. The SQL implementation indexes schedule dates, resource dates, dependency successors, and review findings because those columns participate in common analytical queries.

## Data Integrity

Some schedule rules belong in application code because they require contextual policy.

Other rules should be enforced at the database boundary because every application must respect them.

The SQL schema enforces nonnegative effort, valid progress ranges, valid date intervals, valid resource references, valid schedule references, and unique task codes within a schedule.

This layered approach reduces the probability that a different client, import process, or administrative query can insert structurally invalid schedule records.

## Practical Review Workflow

A practical review begins with structural validation. Task identity, dates, resource references, and dependency references must be valid before higher-level analysis is meaningful.

Dependency timing is then checked to ensure prerequisite work does not finish after dependent work begins.

Resource concurrency is evaluated separately because independent tasks can compete for the same person or equipment.

Capacity is evaluated as planned workload against available capacity.

Progress is interpreted relative to the review date.

The dependency graph is then analyzed for cycles and longest paths.

Finally, the evidence is evaluated against explicit review rules and recorded as a decision with findings.

This ordering prevents a governance decision from being based on calculations that were already invalid at the structural level.

## Production Considerations

A production scheduling system would normally need richer calendar semantics than the examples provide. Working days, holidays, time zones, shifts, partial-day assignments, resource calendars, dependency lag, milestones, recurring work, and multiple resource types can materially change schedule calculations.

Capacity should also be time-phased. A weekly capacity number is insufficient when workload is concentrated into a small number of days.

Progress should distinguish reported completion from verified completion when schedule control has financial, operational, or regulatory consequences.

Review findings should be auditable. The reviewer, review time, schedule version, decision rules, and evidence used to reach the decision should be retained.

Schedule review is strongest when it is treated as an evidence-based control process rather than as a manual inspection of dates.
