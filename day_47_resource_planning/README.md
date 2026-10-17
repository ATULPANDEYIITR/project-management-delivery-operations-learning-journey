# Project Resource Planning

## Scope

Project resource planning is the process of deciding which people, equipment, software capacity, and financial capacity are required to complete project work within its schedule and constraints.

The four implementation layers in this repository treat resource planning as a constrained decision problem:

- **Python** builds an executable planning model with people, skills, task effort, capacity, cost, allocation validation, and exportable planning records.
- **JavaScript** models allocation as an event-driven operation so a planning interface or service can react to resource-allocation events without coupling the dashboard to the planning logic.
- **C++** presents a resource-governance case study in which a planning engine qualifies resources, validates capacity, records allocations, and calculates planned personnel cost.
- **Java** models an enterprise resource-planning service with immutable domain records, explicit task states, skill requirements, validation exceptions, capacity controls, and budget enforcement.
- **PostgreSQL** represents the planning domain relationally and uses foreign keys, check constraints, indexes, views, transactions, and a trigger to enforce task-effort integrity.

The implementations deliberately use different perspectives. The Python model emphasizes planning and reporting, JavaScript emphasizes event-driven behavior, C++ emphasizes a constrained allocation engine, Java emphasizes enterprise domain modeling, and SQL emphasizes durable relational integrity.

## Resource Planning Model

A useful resource plan connects four dimensions:

| Dimension | Planning question | Representation in the implementations |
|---|---|---|
| Work | What must be completed? | Project tasks with dates, effort, priority, and required skills |
| Resources | Who or what can perform the work? | People, equipment, software resources, skills, capacity, and rates |
| Allocation | How much resource capacity is committed? | Resource-to-task allocations with hours and states |
| Constraints | When is an allocation unacceptable? | Skill qualification, capacity, schedule, budget, and database integrity rules |

Resource planning is not equivalent to assigning the cheapest available person. A valid allocation must satisfy the requirements of the work while respecting resource capacity and project constraints.

For example, a security-validation task can require both `security` and `testing` at an expert level. A person with general engineering experience is not automatically an eligible resource. Qualification is evaluated separately from availability and cost.

## Core Domain Relationships

The conceptual relationship can be represented as:

`Project -> Tasks -> Required Skills`

`Resource -> Skills`

`Task <- Allocation -> Resource`

`Project -> Budget`

An allocation connects work to capacity. The task determines what is needed, the resource determines what is available, and the allocation records the amount committed.

This separation prevents a common planning error in which a task is considered staffed merely because a person has been named. The resource must also have sufficient capability and capacity.

## Capacity Planning

Capacity represents the amount of resource effort available during a planning period.

For a person with a 40-hour weekly capacity:

`utilization = allocated hours / available capacity × 100`

An allocation of 32 hours therefore represents 80% utilization for that capacity period.

Capacity must be interpreted in the context of the planning interval. A person may have 40 hours available in a week but only 24 usable hours after accounting for leave, organizational commitments, training, or other projects.

The Python implementation calculates utilization from allocation records rather than storing a manually maintained percentage. The JavaScript and C++ implementations apply capacity checks before accepting allocations. The Java service performs the same validation inside the application service boundary. PostgreSQL provides queries that expose capacity violations from persisted allocation data.

A planning system should distinguish between:

- available capacity
- allocated capacity
- committed capacity
- consumed capacity
- unavailable capacity

Treating all four as one number makes forecasts difficult to audit.

## Skill-Based Resource Matching

Skill matching is different from capacity matching.

A resource may have enough free hours but still be unsuitable for a task. Conversely, a highly qualified resource may be suitable but already fully allocated.

The Python model stores required task skills as a set and checks that the candidate resource contains every required skill. The JavaScript implementation performs the same qualification through its `canPerform` method. The C++ case study uses `std::set` to evaluate required capabilities. Java places qualification logic directly on the immutable `Resource` domain record. PostgreSQL stores resource skills and task-required skills as separate relations so qualification can be queried from durable data.

This separation supports better allocation decisions:

`qualification -> capacity -> cost`

rather than:

`lowest cost -> assignment`

## Scheduling and Resource Conflicts

Resource allocation is time-dependent. An allocation cannot be evaluated only from the total project effort because two tasks may require the same person during overlapping periods.

The Python implementation stores task start and end dates and uses overlap checks when validating an assignment. The JavaScript implementation provides `overlappingAllocations`, allowing an application to inspect conflicting commitments. The SQL schema stores allocation periods and includes an index over resource and allocation dates to support conflict-oriented queries.

A basic date-overlap condition is:

`existing_start <= requested_end AND existing_end >= requested_start`

This identifies two allocations whose periods intersect.

Real planning systems extend this model with working calendars, holidays, shifts, time zones, part-time schedules, leave, and resource-specific availability.

## Cost Planning

Resource cost is derived from allocation effort and the resource rate.

`allocation cost = allocated hours × hourly cost`

The Python, C++, and Java implementations calculate this value from the allocation register rather than storing a manually entered cost on every allocation.

This matters because a planning system should make cost reproducible. If an allocation changes from 40 hours to 48 hours, its cost should change from the underlying allocation quantity rather than requiring someone to edit a separate cost field.

The SQL implementation performs the same calculation through joins between allocations and resources and aggregates the result against the project budget.

Budget control becomes meaningful when cost is evaluated against planned allocation, not merely against the original project estimate.

## Python Implementation

The Python program defines `Person`, `Equipment`, `SoftwareLicense`, `ProjectTask`, `Allocation`, and `ResourcePlan`.

`ResourcePlan` acts as the central planning model. It provides:

- skill-based candidate discovery
- capacity validation
- task assignment
- allocation cost calculation
- budget remaining calculation
- utilization reporting
- detection of unassigned tasks
- JSON export
- CSV export

The sample project is a public-service platform. Its work is divided into secure API implementation, a citizen portal, security validation, and an operational data pipeline.

The Python implementation also demonstrates a failed allocation. Attempting to assign an unsuitable person to a security task raises a validation exception instead of silently creating an invalid plan.

The use of dictionaries provides direct lookup by resource and task identifiers. Lists preserve allocation records, while sets provide efficient skill-membership checks.

The export functions demonstrate a practical boundary between an in-memory planning model and operational artifacts. JSON preserves the hierarchical plan structure, while CSV is convenient for allocation-register analysis.

## JavaScript Implementation

The JavaScript program uses classes for people, tasks, and the resource planner.

Its most important distinction from the Python implementation is the event-driven allocation boundary. `ResourcePlanner` extends `EventTarget` and emits a `resourceAllocated` event after an allocation has been accepted.

This allows a user interface or service layer to react to an allocation without being embedded in the allocation method itself.

For example, an event consumer can update:

- a resource-utilization dashboard
- an audit log
- a planning timeline
- a notification panel
- a cost forecast

The planner also exposes a dashboard-oriented object containing budget status, resource utilization, and allocation records.

The implementation uses JavaScript `Map` and `Set` structures for indexed resource/task storage and skill membership. It uses `Date` objects for task periods and explicitly calculates working days when translating an allocation into a weekly-capacity equivalent.

The validation path rejects unknown resources, unknown tasks, invalid effort, insufficient skills, and capacity violations.

## C++ Resource Governance Case Study

The C++ program models a repository-independent project resource governance engine for a public-sector digital-service project.

The system separates:

- resource definitions
- task definitions
- allocations
- qualification checks
- capacity validation
- cost calculation

`ResourceGovernanceEngine` owns the planning collections and exposes operations for registration, validation, allocation, resource qualification, reporting, and cost calculation.

The `std::set` representation of skills is appropriate because resource qualification is fundamentally a membership problem: every required skill must exist in the candidate resource's skill set.

`validateAllocation` produces a structured validation result instead of immediately throwing an exception. The public `allocate` operation then converts an invalid result into an exception because allocation is a state-changing operation.

The case study intentionally attempts an invalid second assignment to a resource whose capacity has already been consumed. The allocation is rejected before it enters the allocation vector.

This design separates decision validation from state mutation. That separation is useful when a future planning application needs a "validate before commit" operation.

## Java Enterprise Model

The Java implementation uses immutable records for `Resource`, `Task`, and `Allocation`.

The `Resource` record owns its qualification rule through `canPerform`. This places the resource capability decision close to the data that describes the resource while keeping orchestration inside `ResourcePlanService`.

`SkillLevel` is an enum with explicit numeric ranking. This prevents the application from comparing arbitrary strings such as `"senior"` and `"expert"`.

Task state is also represented by an enum:

`PLANNED -> ACTIVE -> BLOCKED / COMPLETED`

The `Task.activate` method demonstrates explicit state-transition validation. A completed task cannot be moved into an invalid blocked state.

`ResourcePlanService` coordinates:

- resource registration
- task registration
- qualified-resource discovery
- capacity checking
- task-effort checking
- budget checking
- allocation persistence in memory
- utilization calculation
- cost reporting

The service throws a domain-specific `ResourceAllocationException` when a planning rule is violated. This distinguishes business validation failures from programming errors such as an unknown identifier.

Java streams are used for read-oriented queries such as finding eligible people and calculating aggregate allocation hours. Immutable records reduce the possibility of accidental mutation of core planning values.

## PostgreSQL Data Model

The SQL implementation uses a dedicated `resource_planning` schema.

`projects` stores project-level financial and schedule boundaries.

`resources` stores people and non-person resources with capacity and hourly cost.

`resource_skills` separates skills from resources because a resource can have many skills and each skill can have a different proficiency level.

`tasks` stores project work, estimated effort, priority, dates, and state.

`task_required_skills` expresses the many-to-many relationship between tasks and required skills while retaining a minimum skill level.

`allocations` connects resources to tasks and records the amount of committed effort.

`resource_absences` provides a place for availability exceptions such as leave or other periods in which a resource cannot be scheduled.

The foreign keys prevent orphaned tasks, skills, and allocations. Check constraints prevent negative budgets, zero-capacity resources, negative costs, invalid dates, and non-positive effort.

## Database-Level Enforcement

Application validation is useful, but important planning invariants should not depend exclusively on application code.

The SQL script includes a trigger function named `enforce_task_effort`. It checks the accumulated non-released allocation for a task against the task's estimated effort.

This protects the database when an allocation is inserted outside the application that normally performs the validation.

The script also uses a transaction and savepoint around an intentionally invalid allocation. The failure is handled while preserving the database session.

This illustrates an important distinction:

- application validation improves user feedback
- database constraints protect persistent integrity

Both layers have different responsibilities.

## Planning Queries

The SQL queries provide operational views of the plan.

The resource-utilization view calculates allocated hours and utilization percentage from allocation records.

The qualification query finds task requirements for which no active resource has a sufficient skill.

The capacity query identifies resources whose non-released allocations exceed stated capacity.

The cost query calculates planned resource cost against the project budget.

The skill-validation query detects persisted allocations where the assigned person lacks a required skill.

The absence-oriented query identifies allocations overlapping a resource's recorded absence period.

These queries make the relational model useful for project-control reporting rather than limiting SQL to data storage.

## Resource Allocation Decision Flow

A defensible allocation decision follows this relationship:

`Task requirements -> Qualified resources -> Available capacity -> Schedule compatibility -> Cost -> Allocation`

Qualification removes resources that cannot perform the work.

Capacity removes resources that cannot accept the required effort.

Schedule compatibility removes resources whose existing commitments conflict with the requested period.

Cost supports budget-aware selection among feasible resources.

The final allocation records the decision so utilization and financial reporting can be calculated later.

## Resource Types

People are usually capacity-constrained by working hours and skills.

Equipment can be constrained by availability windows, maintenance periods, physical location, or operating hours.

Software resources can be constrained by license seats, subscription periods, or environment capacity.

Financial resources are different because money is not assigned in exactly the same way as a person. Budget represents a project constraint against which resource commitments are evaluated.

The implementations therefore treat resource type as a domain attribute rather than assuming every resource behaves identically.

## Edge Cases

A robust resource plan must account for conditions that make a superficially valid allocation unacceptable.

A task with no qualified resource is not automatically solved by assigning an available generalist. The planning system should expose the staffing gap.

A resource with unused total capacity can still be unavailable during the required period because another allocation overlaps the task dates.

A task can have sufficient assigned hours but still exceed its estimated effort if duplicated allocations are created accidentally. The PostgreSQL trigger protects against this specific integrity failure.

A project can have sufficient personnel capacity but still exceed its budget when expensive specialist resources are assigned for excessive hours.

A resource can also become unavailable after an allocation was planned. This is why resource absence and allocation state are separate concepts in the SQL model.

## Common Planning Failures

**Capacity over-allocation** occurs when planned hours exceed the resource's usable capacity. It causes schedule slippage and makes utilization reports misleading.

**Skill mismatch** occurs when the assigned person does not meet the work's capability requirement. The resource may appear available while still being unsuitable.

**Hidden schedule overlap** occurs when a planning system aggregates hours without considering dates. Total hours can look reasonable while two tasks compete for the same resource at the same time.

**Budget drift** occurs when resource effort changes but the financial forecast is not recalculated from the current allocation register.

**Stale planning data** occurs when utilization or cost percentages are manually stored and later diverge from the underlying allocations.

**Single-person dependency** occurs when critical work is concentrated in one specialist. The allocation may be valid but operationally fragile because the project has little substitution capacity.

## Performance Considerations

Resource qualification can become expensive when a project has thousands of resources and tasks. Indexing skill relations, as demonstrated in PostgreSQL, reduces the amount of data that must be scanned for qualification queries.

Allocation conflict checks benefit from indexes involving resource identifiers and allocation dates.

In application code, dictionaries, maps, and hash sets provide efficient direct lookup and skill membership operations.

Cost and utilization reports should normally aggregate from authoritative allocation records rather than repeatedly recalculating the same values through multiple disconnected data structures.

For large planning systems, allocation data may require time-phased storage so that capacity is evaluated per day or per planning period rather than against a single project-wide number.

## Security and Governance

Resource plans can expose sensitive organizational information, including employee assignments, labor costs, project priorities, and planned availability.

Access control should therefore distinguish between users who can view resource assignments and users who can change them.

Cost visibility may need to be restricted even when task assignments are broadly visible.

Allocation changes should be auditable. A production system should preserve who changed an allocation, when it changed, what the previous value was, and why the change was approved.

Database permissions should prevent ordinary application users from bypassing the normal planning workflow by writing arbitrary allocation records directly.

## Practical Production Considerations

The examples use in-memory collections for application-level demonstrations. A production planning system needs durable persistence, authenticated users, transactional updates, audit history, time-aware calendars, and concurrency control.

A production allocation operation should normally validate the current resource capacity inside the same transaction that records the allocation. Otherwise two simultaneous users can each observe free capacity and commit allocations that collectively exceed the limit.

Resource rates may also change over time. A production financial model should preserve the rate applicable to the allocation period rather than assuming the current rate always applies historically.

Forecasting can be extended from simple planned hours into remaining effort, actual effort, forecast effort, variance, and projected completion cost. Those concepts should remain separate so a manager can distinguish what was planned from what has actually been consumed.

## Implementation Boundaries

The six artifacts intentionally do not represent one shared executable application.

The Python implementation is a planning simulator and reporting model.

The JavaScript implementation demonstrates an event-driven planning component suitable for an interactive application boundary.

The C++ implementation focuses on a resource-governance engine with explicit validation results and deterministic allocation decisions.

The Java implementation emphasizes enterprise domain modeling, immutable values, state transitions, and service-level validation.

The PostgreSQL implementation focuses on persistent relational integrity, analytical queries, transactions, and database enforcement.

Together they represent the same resource-planning domain from complementary technical perspectives without making the implementations identical.
