# Project Dependencies: Understanding Task Dependencies

## Scope

Project dependencies describe the conditions that determine when work can begin, which work can proceed concurrently, and which work must wait for another activity.

The core relationship is:

`prerequisite -> dependent`

If `DATABASE_SCHEMA` is a prerequisite of `BACKEND_API`, the API task cannot be considered executable until the schema requirement has been satisfied.

This repository models dependencies as a directed graph. A task is a vertex, and a dependency relationship is a directed edge. A valid project dependency graph must contain resolvable task references and must not contain a circular dependency that makes completion logically impossible.

The implementations use different perspectives:

- Python builds a reusable dependency-analysis engine with validation, scheduling, state management, critical-path analysis, failure propagation, and export.
- JavaScript models dependency execution as an event-driven system and uses asynchronous task simulation to show how dependency readiness interacts with concurrency.
- C++ presents a repository migration case study where database, service, security, observability, rollback, and production-cutover activities form a constrained delivery graph.

The three implementations use the same fundamental dependency model but deliberately emphasize different engineering concerns.

## Core Dependency Model

A task can be represented as:

| Attribute | Meaning |
| --- | --- |
| Task ID | Stable identifier used by other tasks when declaring dependencies |
| Name | Human-readable description of the work |
| Duration | Estimated execution time used by scheduling analysis |
| Dependencies | Tasks that must be completed first |
| Owner | Team or role responsible for the task |
| Priority | Relative scheduling importance |
| Status | Current lifecycle state |
| Failure reason | Operational explanation when execution fails |

Suppose a project contains:

`REQUIREMENTS -> ARCHITECTURE -> DATABASE -> API -> INTEGRATION -> RELEASE`

The arrows do not merely describe a preferred sequence. They encode prerequisites.

A scheduler therefore cannot legally move `API` ahead of `DATABASE` unless the dependency relationship is removed or the project model is changed.

## Dependency Graphs

The graph is directed because dependency relationships have a direction.

If task `A` is required by task `B`, the relationship is:

`A -> B`

The reverse relationship is not automatically true.

For example, a database schema can be required by an API implementation, but the API implementation is not a prerequisite for creating that schema.

The Python and C++ implementations construct an adjacency representation that maps prerequisites to their dependents. This makes it efficient to determine which tasks become candidates for execution after a prerequisite completes.

The task representation itself stores dependencies in the opposite conceptual direction:

`B.dependencies = {A}`

Both representations are useful. Storing prerequisites on the task makes the task's requirements easy to inspect. Building reverse adjacency makes scheduling propagation efficient.

## Dependency Validation

A project dependency system should reject invalid relationships before attempting to schedule work.

### Missing dependencies

A task referring to an unknown task creates an unresolved graph:

`PAYMENT_MIGRATION -> BACKUP`

when `BACKUP` does not exist.

This is a data-integrity problem. It should not be treated as an ordinary scheduling delay because the scheduler cannot determine what the prerequisite actually means.

All three implementations validate dependency references.

The Python implementation raises `DependencyError`. The JavaScript implementation uses `DependencyError`, and the C++ implementation raises standard exception types such as `std::invalid_argument`.

### Self-dependencies

A task depending on itself has no valid starting point:

`DEPLOY -> DEPLOY`

The implementations reject this relationship during task creation.

### Circular dependencies

A circular dependency contains a path that eventually points back to an earlier task:

`SCHEMA -> SERVICE -> MIGRATION -> SCHEMA`

No member of this cycle can satisfy every prerequisite independently. A scheduler based on dependency completion therefore cannot produce a valid starting sequence for the cycle.

The implementations use graph traversal to identify cycles. This validation is particularly important when dependency data comes from a database, JSON file, spreadsheet, API, or other external source.

## Topological Scheduling

A directed acyclic dependency graph can be converted into a valid execution order using topological sorting.

The implementations use Kahn's algorithm.

The scheduler calculates the number of unresolved prerequisites for each task. Tasks with zero unresolved prerequisites enter the ready set.

When a task is processed, each dependent task has one fewer unresolved prerequisite.

When a dependent reaches zero unresolved prerequisites, it becomes eligible for scheduling.

Conceptually:

`zero prerequisites -> ready`

`complete task -> decrement dependent prerequisites`

`dependent reaches zero -> ready`

This is different from simply sorting tasks alphabetically, by priority, or by creation date. Those properties may influence scheduling policy, but they cannot violate dependency constraints.

## Execution Waves

A dependency graph often reveals opportunities for parallel work.

Consider:

`REQUIREMENTS -> ARCHITECTURE`

and then:

`ARCHITECTURE -> DATABASE`

`ARCHITECTURE -> INFRASTRUCTURE`

After `ARCHITECTURE` completes, `DATABASE` and `INFRASTRUCTURE` may be eligible at the same time.

The graph can therefore be divided into dependency waves:

| Wave | Eligible work |
| --- | --- |
| Initial | REQUIREMENTS |
| Next | ARCHITECTURE |
| Next | DATABASE, INFRASTRUCTURE |
| Later | API, monitoring, integration work |

A wave represents dependency eligibility, not unlimited real-world capacity.

Two tasks can be dependency-independent while still competing for the same engineer, database environment, deployment window, or test infrastructure.

Consequently, a production scheduler normally combines dependency constraints with resource constraints.

## Python Implementation

The Python program is centered on `ProjectDependencyGraph`.

The `Task` dataclass contains the state required for dependency-aware scheduling. `TaskStatus` separates ordinary unfinished work from active, completed, failed, and blocked work.

The graph validates references before analysis and rejects cycles before generating an execution order.

`topological_order()` implements Kahn's algorithm. It provides an executable ordering while preserving all prerequisite relationships.

`execution_waves()` goes beyond a single ordering. It groups tasks into dependency levels, making parallel execution opportunities visible.

`ready_tasks()` evaluates the current project state rather than merely inspecting the static graph. A task is ready only when every prerequisite is actually completed.

The state transition methods enforce operational rules:

- `mark_started()` prevents a task from starting while prerequisites remain incomplete.
- `mark_completed()` prevents arbitrary completion without an active execution state.
- `mark_failed()` records failure and triggers blocked-state propagation.
- `propagate_blocked_status()` distinguishes failed dependency paths from ordinary waiting.

This distinction is important in real project systems. A task waiting for unfinished work may become ready later. A task whose prerequisite has failed may require corrective action instead.

### Critical-path analysis

The Python implementation calculates:

- earliest start,
- earliest finish,
- latest start,
- latest finish,
- slack,
- critical tasks,
- minimum project duration under the model assumptions.

For each task:

`earliest finish = earliest start + duration`

If a task has prerequisites, its earliest start is constrained by the latest earliest finish among those prerequisites.

Slack is:

`latest start - earliest start`

A task with zero slack belongs to the critical path.

The implementation assumes unlimited execution capacity for this calculation. Real resource constraints can make resource-constrained scheduling more complex than ordinary critical-path analysis.

### Export

The Python implementation exports the dependency plan to JSON and CSV.

JSON preserves structured relationships and is suitable for programmatic processing.

CSV provides a tabular representation suitable for spreadsheet analysis.

Both formats include dependency information rather than exporting only task names. This is essential because a task list without dependency relationships loses the information needed to reconstruct the execution graph.

## JavaScript Implementation

The JavaScript implementation models the same domain from an event-driven perspective.

The `Project` class uses a `Map` for task storage. Each task contains a `Set` of dependencies, preventing duplicate dependency entries.

The implementation includes an event system through `on()` and `emit()`.

Events include:

- `taskAdded`
- `taskStarted`
- `taskCompleted`
- `taskFailed`
- `taskBlocked`

This provides a useful architecture for a project-management system in which other components might react to dependency state changes.

For example, a completed task could cause a dashboard to refresh, a notification to be emitted, or another scheduler cycle to begin.

### Asynchronous execution

`simulateTask()` uses a Promise and `setTimeout()` to represent asynchronous project work.

The implementation does not use asynchronous execution merely as a JavaScript syntax example. It demonstrates a meaningful relationship between dependency scheduling and event-driven execution.

`runAvailableTasks()` selects ready tasks and executes a bounded number concurrently.

The `concurrency` parameter represents a simplified resource capacity.

If three tasks are dependency-ready and the execution capacity is two, only two are launched during the current batch.

This demonstrates an important distinction:

**dependency eligibility is not the same as execution capacity.**

A task can be ready but still wait because available execution resources are exhausted.

### Failure propagation

The JavaScript implementation can deliberately fail a task.

When `API` fails, tasks depending directly or indirectly on it can become blocked.

This is modeled through `propagateBlockedTasks()`.

The resulting state is more informative than simply saying that the project is incomplete. It identifies which work is affected by the failed dependency path.

### Event-driven design

An event-driven dependency engine is useful when project state changes asynchronously.

For example:

`taskCompleted -> dependency state changes -> new task becomes ready -> scheduler launches work`

This pattern can support dashboards, automation engines, build systems, deployment pipelines, and project orchestration systems.

## C++ Case Study: Customer Platform Database Migration

The C++ program models a production database migration.

The scenario includes:

`PLAN`

`SCHEMA`

`BACKUP`

`SERVICE`

`MIGRATION`

`OBSERVABILITY`

`COMPATIBILITY`

`SECURITY`

`ROLLBACK_TEST`

`PRODUCTION`

The relationships are deliberately realistic.

The schema depends on the migration plan.

The backup also depends on the plan.

The application service depends on the schema because the deployed version must understand the new database structure.

The migration requires both a compatible schema and a verified backup.

Compatibility testing requires the service, migration, and observability capabilities.

Production cutover requires compatibility validation, security verification, and rollback readiness.

This creates a graph in which several activities can proceed independently while other activities require convergence of multiple dependency paths.

### Architecture

`DependencyEngine` owns the task graph and exposes operations for:

- task registration,
- dependency validation,
- cycle detection,
- topological ordering,
- execution-wave calculation,
- readiness evaluation,
- state transitions,
- failure propagation,
- critical-path analysis.

The `Task` structure represents the state of one project activity.

The `std::map` container gives deterministic task iteration, which makes the scheduling output reproducible.

`std::set` is used for dependencies so each relationship is unique and deterministic.

### State transitions

The case study restricts state changes.

A task cannot be completed directly from `NotStarted`.

It must first enter `InProgress`.

A task cannot enter `InProgress` while any prerequisite is incomplete.

A failed task records a failure reason and triggers dependency propagation.

This is important for systems where task state is operationally meaningful rather than merely descriptive.

### Failure scenario

The C++ program deliberately fails the `SCHEMA` task after planning and backup work have completed.

The result demonstrates that:

`SCHEMA failure -> SERVICE blocked`

and:

`SCHEMA failure -> MIGRATION blocked`

Downstream work that requires those paths cannot safely proceed.

This is different from unrelated tasks. Observability work can remain complete because it does not depend on the failed schema path.

The model therefore preserves dependency locality rather than marking the entire project as failed.

## Critical Path and Slack

Critical-path analysis answers a specific scheduling question:

**Which dependency chain determines the minimum project duration under the modeled durations and unlimited parallel capacity?**

Suppose:

`A -> B -> C`

has durations:

`2 -> 5 -> 3`

The chain requires ten time units.

If another independent chain requires only six units, the first chain determines the minimum project completion time.

A task with non-zero slack can move within its scheduling window without immediately changing the modeled project completion time.

A task with zero slack has no such modeled buffer.

Critical-path analysis should not be interpreted as a complete project-risk model. Duration estimates can be uncertain, resources can be constrained, and external events can change the dependency structure.

## Dependency Types

The implementations primarily model finish-to-start dependencies.

A finish-to-start relationship means:

`prerequisite finishes -> dependent may start`

This is the most common dependency form for software delivery activities.

Other project-management systems may support relationships such as:

- start-to-start, where another activity may begin after a predecessor starts;
- finish-to-finish, where completion of one activity constrains completion of another;
- start-to-finish, where a predecessor's start constrains another task's completion.

The graph implementations here intentionally focus on prerequisite completion because it produces a clear directed dependency model suitable for task scheduling.

## Dependencies Versus Priorities

Priority and dependency are different constraints.

Suppose `SECURITY` has critical priority and `DOCUMENTATION` has normal priority.

If both are ready, priority can determine which one receives limited capacity first.

Priority cannot legitimately override an explicit dependency.

If `SECURITY` depends on `API`, the security task remains blocked until `API` satisfies its prerequisite condition even if `SECURITY` has the highest priority in the project.

A sound scheduler therefore evaluates:

`dependency eligibility -> resource availability -> scheduling policy`

rather than treating priority as permission to bypass dependencies.

## Dependencies Versus Resources

Dependency analysis answers:

**Can this task start based on its prerequisites?**

Resource scheduling answers:

**Can this task actually be executed with the available people, systems, environments, or capacity?**

These are separate questions.

For example, two testing tasks may have no dependency relationship, but both may require the same staging environment.

The dependency graph permits them to run concurrently.

The resource scheduler may still serialize them.

This distinction prevents a dependency engine from incorrectly claiming that all tasks in a dependency wave can necessarily run at the same time.

## Failure and Blocked Work

A useful dependency engine should distinguish at least these conditions:

| State | Meaning |
| --- | --- |
| `not_started` | Task has not begun and may still be waiting |
| `in_progress` | Task is currently being executed |
| `completed` | Task has satisfied its prerequisite condition for dependents |
| `failed` | Task execution ended unsuccessfully |
| `blocked` | Task cannot proceed because a dependency path has failed |

A task in `not_started` is not necessarily blocked.

For example:

`API -> INTEGRATION`

If `API` is still running, `INTEGRATION` simply waits.

If `API` fails permanently, `INTEGRATION` can become blocked.

This distinction is operationally valuable because waiting work does not necessarily require intervention, while blocked work may require repair, retry, rollback, or dependency replacement.

## Common Dependency Modeling Errors

### Treating sequence as dependency

Not every task that happens later needs to depend on every earlier task.

If `DOCUMENTATION` and `MONITORING` can proceed independently after architecture approval, creating a dependency from documentation to monitoring artificially reduces parallelism.

Unnecessary edges make schedules more restrictive than the real project.

### Omitting a real prerequisite

If `PRODUCTION_RELEASE` actually requires security validation but the dependency is omitted, a scheduler can incorrectly mark the release as ready.

Missing dependency edges are more dangerous than unnecessary edges because they can allow unsafe execution.

### Creating cycles accidentally

Cycles often appear when responsibilities are modeled without checking the direction of the relationship.

For example, if service deployment requires a migration, and the migration is incorrectly defined as requiring the already-deployed service, the graph becomes cyclic.

Cycle validation should occur before scheduling.

### Confusing dependency with ownership

If the database team owns `SCHEMA` and the backend team owns `API`, that does not by itself create a dependency.

Ownership identifies responsibility.

Dependencies identify prerequisites.

A project system should store both without treating them as interchangeable.

### Using priority to override dependencies

A high-priority task should not bypass a prerequisite merely because its priority value is larger.

Doing so converts a dependency graph into an inconsistent schedule.

## Performance Characteristics

For a graph with `V` tasks and `E` dependency relationships, adjacency-list implementations can perform topological sorting in approximately:

`O(V + E)`

Cycle detection through graph traversal also operates in:

`O(V + E)`

Critical-path calculation after topological ordering is likewise linear in the graph size when adjacency structures are already available.

Memory usage is approximately:

`O(V + E)`

because the scheduler must retain task records and dependency edges.

For large projects, repeated reconstruction of reverse dependency maps can become unnecessary overhead. A production implementation may maintain both prerequisite and dependent indexes incrementally.

## Concurrency Considerations

A real scheduler can have several workers attempting to update task state at the same time.

That creates consistency requirements not represented by a simple in-memory single-threaded model.

For example, two workers must not both acquire the same task.

A production system may require:

- transactional state changes,
- optimistic locking,
- atomic task claiming,
- durable event records,
- idempotent completion handling,
- retry policies,
- distributed locks where justified.

Dependency validation should also be performed when externally supplied project data enters the system, not only when the original project was created.

## Persistence Considerations

A persisted dependency graph should retain enough information to reconstruct relationships.

A task record should normally contain a stable identifier.

Dependencies should reference stable IDs rather than task names because names can change without changing the identity of the work item.

For example:

`API_IMPLEMENTATION` is a better dependency reference than `Build backend API`.

The Python implementation demonstrates persistence through JSON and CSV exports.

JSON preserves nested dependency information naturally.

CSV is convenient for tabular inspection but requires careful handling when representing many-to-many dependency relationships.

## Security Considerations

Dependency data can affect operational decisions.

An attacker or unauthorized user who can modify dependencies may be able to make a release appear eligible before required validation has occurred.

Systems that control production workflows should therefore treat dependency configuration as governed data.

Relevant controls include:

- authenticated modification of project definitions,
- authorization based on project role,
- audit records for dependency changes,
- validation before execution,
- protection against arbitrary task-state transitions,
- immutable or reviewable production prerequisites,
- separation between planning permissions and execution permissions.

The dependency engine itself cannot establish organizational trust. It can only enforce the rules encoded in its model.

## Debugging Dependency Problems

When a task unexpectedly remains unavailable, inspect its direct prerequisites first.

For a task `RELEASE`, determine:

`RELEASE.dependencies`

Then inspect each dependency's state.

If all direct prerequisites are complete but the task is still unavailable, the scheduler's readiness calculation is likely incorrect.

If a dependency is incomplete, trace that task's prerequisites recursively.

A dependency chain can therefore be debugged as a graph path rather than as an arbitrary collection of task records.

When a project has a cycle, the cycle itself is the most useful diagnostic artifact. A message such as:

`A -> B -> C -> A`

shows the exact relationship that prevents scheduling.

## Practical Design Rules

A robust project dependency system should:

- use stable task identifiers for relationships;
- validate every referenced dependency;
- reject self-dependencies;
- reject circular dependency graphs;
- separate dependency eligibility from resource capacity;
- distinguish waiting from blocked work;
- enforce valid state transitions;
- preserve failure reasons;
- calculate scheduling information from actual graph relationships;
- recalculate readiness when prerequisite state changes;
- retain an auditable representation of dependency changes.

The most important design principle is that dependencies should represent real prerequisites. An edge in the graph should exist because the dependent activity genuinely requires the prerequisite activity or its output.

A graph with too many artificial dependencies hides parallelism. A graph with missing dependencies permits unsafe or logically invalid scheduling.
