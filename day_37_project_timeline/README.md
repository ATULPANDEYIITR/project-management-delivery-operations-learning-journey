# Project Timeline

## Scope

This project is a multi-language technical study of **creating, validating, analyzing, and maintaining a project timeline**.

The central idea is that a project timeline is not simply a list of start and end dates. A useful timeline represents temporal relationships between tasks, dependencies, milestones, ownership, progress, priorities, schedule risk, and delivery constraints.

The implementations deliberately use different technical perspectives:

| Implementation | Primary perspective |
|---|---|
| Python | Flexible timeline modeling, validation, dependency analysis, risk detection, and file export |
| JavaScript | Event-driven timeline updates and state changes in a Node.js application |
| C++ | Performance-oriented schedule and dependency analysis engine |
| Java | Enterprise-oriented domain model with explicit task states and policy-like validation |
| PostgreSQL | Relational representation of projects, tasks, dependencies, milestones, owners, and status checks |

The examples use an operations analytics platform as the project scenario so that the timeline has realistic dependencies and delivery constraints.

---

## Project Timeline as a Technical Model

A project timeline normally answers several different questions at the same time.

A date range answers when work is planned. A dependency answers why one task cannot safely begin before another task reaches an appropriate completion point. A milestone identifies a significant delivery or decision boundary. Ownership identifies who is responsible for the work. Progress describes the current execution state. Priority indicates the consequence of schedule movement.

These properties should not be collapsed into one field.

For example, a task can be:

- planned for a future date while having zero progress;
- currently active with partial progress;
- completed before its scheduled end;
- overdue while still incomplete;
- high priority but not yet started;
- blocked because a predecessor has not finished.

A timeline therefore behaves more like a small scheduling system than a static calendar.

---

## Core Domain Model

The implementations consistently use a task with attributes similar to:

`task_id`, `name`, `start`, `end`, `owner`, `dependencies`, `progress`, and `priority`.

The SQL implementation separates dependencies into their own relational table because a task can have multiple predecessors and a predecessor can support multiple successors.

A dependency has directional meaning:

`predecessor -> successor`

For example:

`Requirements -> Architecture -> Implementation -> Testing -> Deployment`

This means the schedule is a directed graph as well as a calendar.

A valid timeline must prevent contradictory temporal relationships. If an implementation task depends on architecture work, the implementation should not begin before the required architecture work has finished unless the planning model explicitly permits overlap.

---

## Creating a Timeline

Timeline creation starts by establishing the project boundary and then defining work packages inside that boundary.

The Python implementation creates an `Operations Analytics Platform` timeline containing kickoff, requirements, architecture, engineering, testing, and production handover activities.

The dates are deliberately related. The engineering work depends on the architecture task, testing depends on engineering and dashboard work, and production handover depends on testing.

This creates a schedule in which changing an upstream activity can affect several downstream activities.

The JavaScript implementation models the same kind of dependency relationship but uses an event-driven design. A progress update emits a `progressChanged` event, allowing other application components to react to a timeline change without embedding every reaction inside the update operation.

The C++ implementation treats the timeline as an analysis engine. Its emphasis is on explicit data structures, dependency traversal, validation, and critical-path calculation.

The Java implementation models the timeline as an enterprise domain with explicit task states such as `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `BLOCKED`, and `OVERDUE`.

The SQL implementation persists the timeline so that schedule information can be queried, aggregated, indexed, and protected by database constraints.

---

## Dates and Duration

A task has a start date and an end date.

The examples calculate calendar duration using an inclusive interpretation:

`duration = end_date - start_date + 1`

Therefore a task beginning on October 12 and ending on October 13 occupies two calendar days.

The Python implementation also demonstrates business-day calculations separately. This distinction is important because calendar duration and working duration answer different scheduling questions.

A project that lasts ten calendar days does not necessarily contain ten working days. Weekends, holidays, organizational calendars, and regional working rules can change the actual effort window.

The implementations keep the basic examples deterministic by using calendar dates. A production scheduling system would normally model working calendars explicitly rather than assuming every weekday is a working day.

---

## Dependencies and Temporal Consistency

Dependencies are one of the most important parts of a project timeline because they convert independent date ranges into a coordinated schedule.

The implementations validate two major failure conditions.

A missing dependency is invalid because the schedule references work that does not exist.

A temporal conflict is invalid when a successor begins before its predecessor finishes.

The Python implementation exposes these conditions through `validate_dependencies()`.

The JavaScript implementation performs the same validation through the `ProjectTimeline` class, but it integrates the model with event-driven state changes.

The C++ implementation represents dependencies as vectors inside each task and uses graph traversal for cycle detection.

The Java implementation stores dependencies as a `Set<String>`, which prevents duplicate dependency references inside a task.

The SQL implementation uses `task_dependencies` with foreign keys and a trigger that checks the predecessor and successor dates. This places part of the scheduling rule at the database boundary rather than relying only on application validation.

---

## Dependency Cycles

A dependency graph must not contain a cycle when the timeline is intended to represent a directed execution order.

An invalid relationship such as:

`A -> B -> C -> A`

creates a circular scheduling requirement. No task in that cycle can establish a valid first completion point.

All four application implementations therefore contain cycle detection.

The Python implementation uses depth-first traversal with `visiting` and `visited` sets.

The JavaScript implementation applies the same graph concept using JavaScript `Set` objects.

The C++ implementation uses `std::set` for traversal state.

The Java implementation uses `HashSet` collections to distinguish the current recursion path from tasks that have already been fully visited.

Cycle detection is distinct from date validation. A graph can have no cycle but still contain a temporal conflict, and a timeline can contain valid dates while still forming a dependency cycle.

---

## Critical Path

The critical path represents the longest dependency-driven sequence through the schedule under the simplified assumptions used by these examples.

For a dependency chain such as:

`Requirements -> Architecture -> Engineering -> Testing -> Deployment`

a delay in an upstream task can directly affect the final delivery date when there is no available scheduling slack.

The Python implementation calculates a longest dependency path using dynamic programming.

For each task, it calculates the longest known completion distance among its predecessors and adds the task duration.

The C++ implementation provides the same analysis in a separate performance-oriented case study.

The Java implementation returns the task identifiers that form the longest dependency chain.

Critical-path analysis is not identical to simply selecting the task with the latest end date. The path is derived from dependency relationships.

A production scheduling system may need a richer Critical Path Method implementation that calculates earliest start, earliest finish, latest start, latest finish, total float, and free float.

---

## Milestones

A milestone represents a significant project boundary rather than ordinary execution work.

The examples use milestones such as:

- requirements baseline approval;
- prototype readiness;
- production release.

A milestone normally has a due date and a completion state.

The Python implementation classifies milestones as `completed`, `overdue`, `due_soon`, or `upcoming` relative to an analysis date.

The Java implementation uses a similar status interpretation while retaining milestones as immutable records.

The SQL implementation stores milestone state separately from tasks because a milestone is not necessarily a duration-bearing activity.

This distinction is useful when reporting project health. A project may contain many active tasks while still having a small number of critical milestones that determine governance or release decisions.

---

## Progress

Progress is modeled as a percentage from zero to one hundred.

The validation rules prevent negative progress and values above one hundred.

A completed task must have 100 percent progress in the SQL model.

Progress should not be interpreted as schedule health by itself.

A task at 70 percent progress may still be a serious schedule risk if only one day remains. A task at 20 percent progress may be acceptable when its scheduled window is several weeks long.

For that reason, the examples combine progress with:

- planned dates;
- priority;
- dependency position;
- task state;
- milestone dates;
- current analysis date.

The Python implementation calculates duration-weighted project progress rather than simply averaging percentages. A longer task therefore has greater influence on the aggregate progress value than a very short task.

---

## Schedule Risk

Schedule risk emerges when planned execution and current execution diverge.

The examples identify conditions such as an incomplete task whose end date has passed, a task currently inside its schedule window with zero progress, and a high-priority task whose progress remains below a defined threshold.

These rules are intentionally explicit rather than pretending that a single progress percentage is sufficient.

The JavaScript implementation returns structured risk objects containing a risk type, task identifier, and message.

The Python implementation returns human-readable risk descriptions.

The C++ implementation prints risk classifications directly from its schedule analysis engine.

The Java implementation derives task state from both date and progress.

The SQL implementation expresses schedule risk through a query so that risk can be evaluated across many projects without loading every record into application memory.

---

## Python Implementation

The Python program is the most exploratory implementation.

Its `Task` dataclass represents an individual schedule activity. Validation occurs close to the domain object so invalid dates, progress percentages, task identifiers, and priorities are rejected early.

`ProjectTimeline` owns tasks and milestones and provides higher-level scheduling behavior.

Important mechanisms include:

- calendar duration calculation;
- business-day calculation;
- business-day date advancement;
- dependency validation;
- dependency-cycle detection;
- critical-path analysis;
- duration-weighted progress;
- owner workload aggregation;
- milestone status classification;
- schedule-risk detection;
- JSON export;
- CSV export;
- ASCII timeline rendering.

The JSON export preserves structured project information, while CSV export makes task information convenient for spreadsheet-oriented analysis.

The ASCII rendering provides a lightweight visual representation without requiring a graphical dependency.

The script also demonstrates failure handling by intentionally constructing invalid tasks and catching the resulting validation exceptions.

---

## JavaScript Implementation

The JavaScript program uses a Node.js-oriented event-driven design.

`TimelineTask` represents schedule work and performs validation during construction.

`ProjectTimeline` manages tasks, milestones, dependency analysis, progress changes, risk detection, and serialization.

The event mechanism is a deliberate JavaScript-specific design choice.

When `updateProgress()` changes a task, the timeline emits `progressChanged`. Other components can subscribe using `on()`.

This separates the action of changing schedule state from the reactions to that change.

The program also exports the current timeline as JSON using Node's built-in `fs/promises` module.

No npm dependency is required.

This makes the implementation useful as a foundation for a larger Node.js service in which schedule changes could later trigger notifications, dashboards, recalculation, or persistence.

---

## C++ Case Study

The C++ implementation models a repository-governance-style technical case study as a project scheduling engine.

The actual scheduling scenario is an operations platform with requirements, architecture, implementation, testing, and release phases.

The `Task` structure stores the data required by the scheduling engine.

`RepositoryTimelineEngine` manages tasks and milestones and provides:

- duplicate-task detection;
- date-range validation;
- progress validation;
- self-dependency rejection;
- dependency validation;
- cycle detection;
- critical-path calculation;
- weighted progress;
- schedule-risk reporting.

The implementation uses `std::map` to provide deterministic task ordering and direct lookup by task identifier.

Cycle detection uses depth-first traversal. The `visiting` set represents the active recursion path, while `visited` records tasks whose dependency trees have already been processed.

The critical-path calculation uses dynamic programming. For each task, the engine records the longest dependency distance that reaches that task and remembers the predecessor responsible for that maximum.

The example also constructs a separate cyclic dependency graph to demonstrate why cycle detection is required before critical-path analysis.

---

## Java Implementation

The Java implementation is structured as an enterprise-oriented domain model.

`ProjectTask` encapsulates task identity, dates, ownership, dependencies, priority, and progress.

`TaskState` expresses operational state separately from priority.

This distinction is important. `CRITICAL` is a priority classification, while `OVERDUE` is a schedule state. A critical task can be planned, active, completed, or overdue.

`Priority` therefore represents consequence or urgency, while `TaskState` represents the current temporal and execution condition.

The Java implementation also uses a `record` for `Milestone`. A milestone is primarily immutable schedule information, so a record is appropriate for this representation.

Collections are exposed carefully. Dependency sets are returned through an unmodifiable view rather than exposing the mutable internal collection directly.

The timeline service validates dependencies before performing critical-path analysis and rejects cycles before calculating a longest dependency sequence.

The enterprise-oriented model makes it possible to extend the design with approval policies, resource calendars, permissions, persistence services, or project portfolio rules without changing the fundamental task model.

---

## PostgreSQL Data Model

The SQL implementation uses a dedicated `project_timeline` schema.

The principal entities are:

`projects` stores project-level boundaries and identity.

`project_members` stores people responsible for project work.

`tasks` stores schedule activities, dates, priority, status, progress, and effort.

`task_dependencies` represents predecessor-successor relationships.

`milestones` stores important project boundaries independently of task duration.

`status_checks` records checks associated with task execution.

Foreign keys preserve relationships between these entities.

The `(project_id, task_code)` unique constraint prevents duplicate task identifiers within one project.

Date constraints prevent a task from ending before it starts.

The progress constraint prevents values outside zero through one hundred.

The completion constraint prevents a task marked as completed from having a progress value other than one hundred.

---

## Database-Level Dependency Enforcement

The SQL model uses a trigger function named `validate_task_dependency_dates()`.

When a dependency is inserted or changed, the function retrieves the predecessor end date and successor start date.

It raises an exception when the predecessor finishes on or after the successor begins.

This is an example of placing a domain integrity rule close to the data.

Application validation remains useful, but database-level enforcement prevents a second application, administrative query, import job, or integration process from silently creating the same invalid dependency.

The database cannot by itself solve every scheduling problem. More sophisticated scheduling logic may require graph algorithms, resource calendars, optimization, or external planning services.

---

## Indexing

The SQL implementation indexes common schedule access patterns.

`idx_tasks_project_dates` supports project-level timeline queries ordered or filtered by task dates.

`idx_tasks_owner` supports owner-oriented workload analysis.

`idx_task_dependencies_successor` supports queries that begin with a successor and need to discover predecessor relationships.

`idx_milestones_project_due` supports project milestone reports ordered by due date.

`idx_status_checks_task` supports recent status-check retrieval for individual tasks.

Indexes should correspond to actual access patterns. Adding indexes indiscriminately increases storage requirements and can increase write cost.

---

## Transactional Schedule Changes

The SQL script demonstrates a transaction that updates task completion and milestone completion together.

The transaction ensures that the two related changes are committed as one unit.

This matters when the business meaning of the changes is coupled. Marking a requirements task complete while leaving the corresponding governance milestone unchanged can create inconsistent reporting.

A production system may use additional transactional rules around rescheduling, bulk task updates, milestone changes, and project baselines.

---

## Resource Workload

The Python and SQL implementations demonstrate workload aggregation.

The Python version sums calendar task-days by owner.

The SQL version groups assigned tasks by project member and calculates:

- number of assigned tasks;
- total assigned calendar days;
- average progress.

This is important because timeline quality depends partly on resource feasibility.

A technically valid dependency graph can still be unrealistic if one person is assigned to too many concurrent tasks.

A more advanced scheduling engine would incorporate capacity, working hours, holidays, skills, task effort, and resource calendars.

---

## Timeline Versus Calendar

A calendar answers when events occur.

A project timeline explains how planned work progresses through time and how activities relate to each other.

The distinction becomes important when several tasks overlap.

For example, dashboard development can run in parallel with an analytics pipeline after architecture is complete. A simple sequential list would incorrectly inflate the project duration if it forced every activity to occur one after another.

Dependency-aware scheduling allows independent tasks to overlap.

The critical path then identifies the dependency sequence that controls the modeled delivery duration.

---

## Timeline Versus Milestone Plan

A timeline contains duration-bearing work.

A milestone normally represents a point in time.

For example:

`2026-11-06` can represent the milestone "Prototype ready", while `2026-10-29 -> 2026-11-06` represents the implementation activity that produces that milestone.

Treating milestones as ordinary tasks can obscure this distinction.

The implementations therefore maintain milestones separately.

---

## Timeline Baselines

A useful production timeline normally distinguishes the current schedule from an approved baseline.

The baseline represents what the project was expected to do at a particular planning point.

The current schedule represents the latest forecast.

Comparing the two makes schedule variance measurable.

The example code does not implement full baseline versioning, but the domain structures are suitable for an extension in which a project stores baseline task dates separately from current dates.

A baseline model would normally preserve:

- baseline start;
- baseline finish;
- current start;
- current finish;
- variance;
- baseline version;
- approval timestamp.

This prevents historical plans from being overwritten when a schedule is revised.

---

## Rescheduling

Rescheduling should not be treated as changing one date field.

Moving an upstream task may require recalculating dependent tasks.

For example, if architecture is delayed by three working days, the schedule engine may need to determine whether the engineering task can absorb the delay through available float or whether its start must move.

The examples intentionally keep date mutation simple so that the dependency and analysis mechanisms remain clear.

A production rescheduling engine would normally distinguish:

- fixed-date constraints;
- dependency constraints;
- resource constraints;
- working calendars;
- holidays;
- available float;
- milestone commitments.

---

## Common Failure Modes

A timeline can appear complete while containing serious planning defects.

A task can have an end date before its start date.

A successor can begin before its predecessor has finished.

A dependency can reference a task that does not exist.

Two or more tasks can create a circular dependency.

A completed task can contain a progress value below 100 percent.

A project can have a reasonable overall progress percentage while a critical task is severely delayed.

A milestone can remain marked as upcoming after its due date.

A schedule can be mathematically consistent but operationally infeasible because the same person is overloaded with concurrent work.

The implementations explicitly validate several of these conditions rather than relying on presentation logic.

---

## Performance Considerations

For a modest project, straightforward graph traversal and in-memory collections are sufficient.

Dependency validation is approximately proportional to the number of dependency relationships.

Cycle detection is linear in the graph representation when each task and dependency is traversed once.

The longest-path calculation used by the examples is efficient for a directed acyclic dependency graph because each task is processed after its dependencies.

Database performance becomes more important as the number of projects and tasks increases. Indexes on project identifiers, dates, owners, dependencies, and milestones reduce the cost of common schedule queries.

For very large portfolio scheduling systems, graph analysis, resource allocation, optimization, and repeated schedule recalculation may require specialized algorithms or dedicated scheduling services.

---

## Security and Integrity Considerations

Timeline data can expose organizational information about project plans, staff assignments, delivery dates, and operational priorities.

A production implementation should therefore restrict who can create, modify, approve, or publish schedule information.

Database credentials should not be embedded in application source code.

Input validation should occur before parsing external schedule files or API payloads.

SQL parameters should be used for externally supplied values rather than constructing SQL strings through concatenation.

Audit information is important when schedule dates affect contractual commitments or operational releases.

The SQL model's constraints are particularly useful for preventing malformed data from entering through secondary applications or administrative workflows.

---

## Practical Applications

The same timeline model can support many operational settings.

A software implementation project can use dependencies between requirements, architecture, development, testing, and deployment.

A procurement project can represent specification preparation, tender publication, evaluation, approval, contracting, and supplier onboarding.

An infrastructure project can represent design, procurement, construction, inspection, commissioning, and handover.

A research project can represent literature review, data collection, experimentation, analysis, manuscript preparation, review, and submission.

An organizational transformation project can represent assessment, design, pilot implementation, training, rollout, and stabilization.

The domain model remains useful because each case contains work, time boundaries, dependencies, ownership, progress, and delivery points.

---

## Design Decisions

The examples deliberately separate several concepts that are often incorrectly merged.

Priority is not progress.

Progress is not schedule health.

A milestone is not necessarily a task.

A dependency is not merely a label.

A critical path is not simply the sequence of latest dates.

A project end date is not enough to determine whether the schedule is healthy.

These distinctions make the timeline model more expressive and allow each implementation to perform meaningful analysis.

---

## Production Considerations

A production project timeline system would normally extend the examples with persistent baseline versions, audit history, working calendars, holidays, resource capacity, permissions, change control, notifications, API integration, and reporting.

It would also need a defined policy for schedule changes.

For example, changing a task end date might require recalculation of dependent activities, detection of milestone impact, identification of newly overdue tasks, and generation of a schedule-variance record.

The database model can support these capabilities by introducing schedule versions, task history, resource calendars, and change records.

The application implementations can support them by separating the domain model from persistence, presentation, and integration layers.

The central principle remains the same: a useful project timeline is a dependency-aware representation of planned work through time, with enough structure to detect inconsistencies and explain how schedule changes affect delivery.
