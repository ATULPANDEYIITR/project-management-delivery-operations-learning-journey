# Resource Allocation

## Purpose

Resource allocation is the process of assigning limited resources to tasks while satisfying capacity, compatibility, scheduling, dependency, deadline, and cost constraints.

Resources can represent compute nodes, database servers, employees, equipment, storage pools, or other units of operational capacity. Tasks describe the work that must be completed and the requirements that determine which resources can perform it.

An allocation decision answers several connected questions:

- Which resource is eligible to perform the task?
- Does the resource have sufficient capacity?
- When can execution begin without conflicting with existing reservations?
- Have prerequisite tasks completed?
- Can the task finish before its deadline?
- What is the expected cost of the resulting schedule?

The implementations use a mixed engineering workload involving data preparation, model training, database migration, verification, and production deployment.

## Core Concepts

### Resource capacity and task demand

Capacity defines the maximum amount of a resource that a task may request under the model. Demand represents the amount required by one task.

For a resource with capacity \(C_r\) and a task with demand \(D_t\), the basic feasibility condition is:

\[
D_t \leq C_r
\]

The Python, JavaScript, C++, and Java implementations also compare resource types and required tags. A compute task that requires CUDA cannot be assigned to a CPU-only resource merely because that resource has enough nominal capacity.

The SQL model stores resource capacity and task demand in separate relational columns. Its allocation trigger rejects assignments whose resource type or capacity does not satisfy the task.

The examples treat each resource as exclusively reserved during an allocation interval. This is suitable for tasks that require exclusive use of a machine or operational worker. It is not the same as a multi-tenant system in which several tasks can concurrently share a resource.

### Compatibility

Compatibility is a qualification rule, not a scheduling preference.

A resource is eligible when its type matches the task's required type, its capacity is sufficient, and its tags include all required capabilities.

Tags can represent capabilities such as `cuda`, `linux`, `postgresql`, `backup`, or `production`. A production deployment task may require an operations resource with production access even when another resource appears idle.

Eligibility should be evaluated before optimization. Otherwise, a scheduler might select a cheap but incapable resource and produce an invalid plan.

### Priority and deadlines

Priority expresses relative importance. A higher-priority task is considered before lower-priority tasks when it is ready for scheduling.

A deadline limits the latest acceptable finish time. The scheduling implementations reject a candidate when:

\[
S_t + d_t > L_t
\]

where \(S_t\) is the proposed start time, \(d_t\) is task duration, and \(L_t\) is the deadline.

Priority and deadlines are different policies. Priority determines ordering, while a deadline determines whether a particular placement is feasible. A high-priority task can still be rejected when no compatible resource can meet its deadline.

### Dependencies

Dependencies establish execution precedence. If task B requires task A to finish first, B cannot begin before A finishes.

\[
S_B \geq F_A
\]

where \(S_B\) is the start time of B and \(F_A\) is the finish time of A.

The engineering scenario follows this chain:

`Data preparation → Model training → Output verification → Production deployment`

Database migration is a separate prerequisite for production deployment.

The implementations validate that dependency identifiers exist and that dependency graphs contain no cycles. During scheduling, a task becomes ready only after all prerequisites have reached a resolved outcome. If a prerequisite is rejected, its dependent task cannot be scheduled.

## Scheduling Mechanism

### Earliest feasible start

For each compatible resource, the scheduler determines the earliest time at which the task can run without overlapping an existing reservation.

Reservations are treated as half-open intervals:

\[
[S,F)
\]

A task finishing at 10:00 does not conflict with another task starting at 10:00.

The algorithm examines existing reservations in start-time order. When a proposed interval overlaps a reservation, the candidate start advances to the reservation's finish time. The process continues until a sufficiently long free interval is found.

Candidate resources are then ranked by:

- Earliest feasible start time.
- Lower hourly cost when start times are equal.
- Resource identifier as a deterministic tie-breaker.

This is a scheduling heuristic. It is not guaranteed to minimize total cost, overall completion time, or every deadline violation across all possible schedules.

### Greedy priority allocation

The implementations repeatedly select a ready task using priority, deadline, and identifier ordering. They then find a feasible resource and reserve the task's time interval.

This approach is practical for small deterministic examples and illustrates the interaction between task selection and resource assignment. The final result can depend on the ordering rule. A locally attractive allocation may prevent a later task from using a resource that would have been more valuable to it.

### Makespan and utilization

Makespan is the time between the schedule's start and the latest finish. In the examples, schedules begin at hour zero unless dependencies or prior reservations require a later start.

For an exclusively reserved resource, utilization over a schedule window can be estimated as:

\[
U_r = \frac{B_r}{T} \times 100\%
\]

where \(B_r\) is the total number of reserved hours and \(T\) is the schedule-window duration.

This metric measures time utilization, not capacity-weighted utilization. A resource with capacity 16 and a task demanding 4 units is still considered fully reserved during the task interval. A shared-capacity scheduler would need a different calculation and additional concurrency rules.

## Python Implementation

The Python program defines immutable `Resource` and `Task` records, mutable `Allocation` records, and an `AllocationPlan` containing successful assignments and rejection reasons.

`ResourceAllocator` owns the scheduling workflow. Its compatibility check compares resource type, capacity, and required tags. Dependency validation uses depth-first traversal to detect unknown prerequisites and cycles.

`allocate_by_priority()` repeatedly finds ready tasks, sorts them by scheduling policy, and chooses the earliest feasible compatible resource. It records finish times so dependent tasks cannot begin prematurely. Tasks that lack a suitable resource or miss their deadlines are rejected with explicit reasons.

The `validate_plan()` method independently checks the result. It detects incompatible assignments, incorrect demand, invalid time intervals, multiple allocations for one task, overlapping reservations, and dependency timing violations.

The reporting methods calculate estimated cost and resource utilization. The transactional demonstration makes an invalid change to the schedule, detects the validation failure, and restores the saved plan.

The implementation uses a greedy scheduler rather than a general optimization solver. Its primary purpose is to make the scheduling rules executable and independently testable.

## JavaScript Implementation

The JavaScript program uses Node.js and `EventEmitter` to publish allocation and rejection events.

The `Resource` class owns resource compatibility and reservation behavior. Its `earliestAvailable()` method scans sorted reservations to find a free interval. The `Task` class validates scheduling inputs and stores dependency and capability requirements.

`AllocationEngine` validates the dependency graph, creates working copies of resource reservations, and builds a proposed plan. The copies are important because a failed scheduling attempt should not leave a partially updated live resource state.

After scheduling, the engine commits the new reservations and emits events as each task is allocated or rejected. The report includes task assignments, rejection reasons, makespan, estimated cost, and utilization.

The implementation demonstrates event-driven monitoring and copy-then-commit planning. In a distributed production system, an in-memory commit is not sufficient to protect against simultaneous schedulers or process failures. Reservation changes would require durable storage and concurrency control.

## C++ Case Study

The C++ program models an engineering workload allocation engine for a fleet containing GPU compute, general CPU, database, and production operations resources.

The architecture separates domain records from the `ResourceAllocationEngine`. Resource and task data are stored in maps keyed by stable identifiers. Reservation lists represent the existing schedule, while the `Plan` object records assignments and rejections.

The scheduler uses a dependency graph traversal to reject cyclic workflows. Ready tasks are ordered by priority, deadline, and identifier. Candidate resources are filtered by type, capacity, and tags, then ranked by feasible start time and hourly cost.

`earliestStart()` calculates a non-overlapping placement. The proposed reservation map is copied before planning and replaces the committed map only when the planning process completes. This prevents a partially constructed plan from being published as the committed schedule.

The validation pass checks assignment compatibility, task demand, time intervals, resource overlaps, and dependency precedence. The program reports rejected work rather than silently dropping tasks.

The implementation uses the C++ standard library and compiles with C++17. Its deterministic scheduling policy is appropriate for a small workload, but large scheduling systems may require more efficient interval structures, optimization solvers, or specialized heuristics.

## Java Enterprise Model

The Java implementation uses records to represent `Resource`, `Task`, `Assignment`, and `Rejection`. Records make the domain data concise, while defensive copies of tags and dependency collections prevent callers from modifying those collections after construction.

`ResourceType` is an enum, preventing arbitrary resource-type strings from entering the domain model. `AllocationService` separates input validation, dependency traversal, scheduling, cost estimation, and plan validation.

The scheduling service uses Java collections and stream operations to select ready tasks and order resource candidates. Rejections are represented as domain data so that the caller can distinguish an infeasible task from an internal failure.

The `Plan` record-like class exposes immutable assignment and rejection lists. This supports safer reporting and validation, although immutable lists alone do not provide durable transactions or protect an external resource inventory.

The model is suitable as a starting point for a service-oriented application. A production implementation would normally persist reservations, enforce atomic updates, provide idempotent requests, and distinguish temporary capacity shortages from permanent incompatibility.

## PostgreSQL Data Model

The SQL script defines a dedicated `resource_planning` schema with the following entities.

| Table | Purpose |
|---|---|
| `resources` | Stores resource type, capacity, hourly cost, tags, and enabled state. |
| `tasks` | Stores task demand, duration, priority, deadline, and lifecycle status. |
| `task_dependencies` | Represents prerequisite relationships between tasks. |
| `allocation_plans` | Groups allocations into named planning runs. |
| `allocations` | Records the resource and time interval assigned to each task. |
| `allocation_events` | Stores audit events describing allocations and planning outcomes. |

Primary keys identify records, foreign keys maintain relationships, and unique constraints prevent duplicate resource codes, task codes, and task assignments within one plan. Check constraints reject invalid capacities, demands, durations, priorities, and time intervals.

The `allocations_no_resource_overlap` exclusion constraint prevents overlapping reservations for the same resource. This is stronger than checking for overlaps in an application query alone because the database can enforce the constraint when concurrent transactions attempt conflicting inserts.

The `validate_allocation()` trigger verifies resource availability, resource type, demand, capacity, dependency allocations, dependency timing, and deadlines. The audit trigger records successful allocation inserts.

The sample data includes a workload that cannot fit the available compute capacity. The unallocated-task query identifies tasks without an assignment and distinguishes obvious type-and-capacity incompatibility from cases requiring more scheduling analysis.

The script uses PostgreSQL's `btree_gist` extension for the exclusion constraint. The database must permit this extension to be installed. If the environment restricts extension creation, a database administrator must enable it or the overlap rule must be implemented using another concurrency-safe design.

The dependency trigger assumes prerequisite allocations are inserted before dependent allocations. The application scheduler must therefore produce a dependency-respecting insertion order. The trigger also expects the prerequisite to be allocated in the same plan.

## Allocation Policies and Trade-offs

### Exclusive versus shared capacity

The examples reserve an entire resource for one task during its interval, even if the task uses only part of the resource's nominal capacity. This simplifies conflict detection and suits exclusive workloads.

A shared-capacity model must calculate the sum of all concurrent demand:

\[
\sum_{t \in A(r,\tau)} D_t \leq C_r
\]

where \(A(r,\tau)\) is the set of tasks using resource \(r\) at time \(\tau\). Enforcing this condition requires concurrency-safe capacity accounting, not merely checking each task independently against the maximum capacity.

### Cost versus completion time

Selecting the cheapest resource may increase the overall completion time. Selecting the earliest available resource may increase cost. A policy must define how to balance these objectives.

A practical scheduler may use weighted objectives, hard deadlines, resource-specific pricing, or service-level requirements. Those decisions should be explicit rather than hidden inside an arbitrary sort order.

### Rejected tasks and fairness

A scheduler must retain rejection reasons so operators can distinguish insufficient capacity, missing capabilities, deadline failures, and dependency failures.

Strict priority can starve low-priority work when higher-priority tasks continuously arrive. Fairness policies such as aging, quotas, weighted fair scheduling, or reserved capacity can reduce this risk. The sample implementations do not implement preemption or long-term starvation prevention.

## Complexity and Scaling

Let \(n\) be the number of tasks, \(m\) the number of resources, and \(k\) the number of reservations examined when placing a task.

Dependency validation with depth-first traversal takes \(O(n+e)\) time, where \(e\) is the number of dependency edges.

The scheduling examples repeatedly inspect pending tasks and sort ready tasks. Candidate resource evaluation scans available resources and may scan their reservations. The straightforward implementation is intended for clarity rather than very large workloads.

For larger systems, maintain a ready-task priority queue, index reservations by resource and start time, and use efficient interval queries. If tasks can run concurrently on one resource, maintain time-indexed aggregate capacity rather than treating every reservation as exclusive.

## Reliability and Production Considerations

An allocation plan is a proposal until its reservations are committed. The application implementations use local copies to avoid publishing partially constructed plans, but this mechanism does not replace a database transaction.

A production allocation service should consider:

- **Concurrency control:** Lock or atomically reserve the relevant resource intervals so two schedulers cannot claim the same capacity.
- **Idempotency:** Repeated requests should not create duplicate reservations or charge the same task twice.
- **Recovery:** Persist plans and reservation changes so a process restart does not erase the schedule.
- **Auditability:** Store who or what requested an allocation, the decision criteria, rejection reasons, and any later changes.
- **Time consistency:** Use a consistent timezone and interval convention, and distinguish planned time from actual execution time.
- **Capacity accuracy:** Refresh resource health, enabled state, and capacity before committing a schedule.
- **Policy transparency:** Separate mandatory constraints from preferences such as lower cost or earlier start time.
- **Operational feedback:** Compare estimated duration and cost with actual results to improve future planning.

A reliable resource allocation system does more than assign work to available machines. It preserves constraints, records decisions, and produces a schedule that can be independently validated before resources are committed.
