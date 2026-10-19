# Resource Availability

## Scope

Resource availability is the management of finite capacity that competing workloads need in order to execute. The resource can be CPU capacity, memory, persistent storage, database connections, API quota, worker slots, or another measurable capacity unit.

The central problem is not merely recording how much capacity exists. A useful resource-management system must answer whether a request can be admitted, reserve the required capacity without creating an inconsistent state, release capacity when work completes, prioritize competing workloads, detect constrained resources, and expose utilization for operational decisions.

The six artifacts model these concerns from different technical perspectives:

| Artifact | Primary perspective |
|---|---|
| Python | Resource pools, atomic multi-resource admission, priority scheduling, persistence, validation, concurrency |
| JavaScript | Event-driven scheduling, asynchronous workload execution, state changes, quota handling |
| C++ | Capacity-management case study with transactional admission and priority scheduling |
| Java | Enterprise domain model with explicit resource types, policies, immutable workload definitions, and synchronized allocation |
| PostgreSQL | Relational representation of pools, workloads, requirements, allocations, constraints, indexes, and transactions |
| README | Conceptual relationship between availability, allocation, scheduling, utilization, and capacity planning |

## Resource Availability Model

A resource pool has a fixed capacity and a current available quantity.

If a pool has capacity `C` and currently allocated quantity `A`, then:

`available = C - A`

Utilization is:

`utilization = A / C`

The distinction between capacity and availability matters operationally. A server cluster may have 100 CPU units in total while only 25 are currently available because workloads have already reserved 75.

Availability is also resource-specific. CPU, memory, storage, database connections, and API quotas cannot safely be treated as interchangeable units. A workload that has enough CPU but insufficient memory is still not admissible if both resources are required.

## Allocation and Admission

Allocation changes the state of a resource pool by reserving capacity for a consumer.

The implementations use atomic admission for workloads that request several resource types. Before modifying any pool, the manager calculates the total requirement for each resource and verifies that every required pool can satisfy it.

This prevents a partial allocation such as:

- CPU successfully reserved
- memory unavailable
- workload rejected
- CPU accidentally left reserved

The Python `ResourceManager.request`, Java `ResourceService.allocate`, and C++ `GovernanceResourceManager::request` all use this pattern.

The SQL implementation expresses the same integrity requirement through a transaction and row locking. `SELECT ... FOR UPDATE` locks the resource rows involved in the admission decision so competing transactions cannot independently observe and consume the same availability.

## Resource Pools

A resource pool represents a bounded capacity domain.

The examples use:

- `compute` for execution capacity
- `memory` for RAM
- `storage` for persistent storage
- `database_connections` for concurrent database sessions
- `api_quota` for externally imposed request limits

A pool has a name, resource type, capacity, and available amount. Allocations are associated with a workload or consumer rather than simply reducing a global counter.

This ownership information is important because releasing resources requires knowing which consumer currently holds them.

The Python implementation stores allocations in dictionaries. The JavaScript implementation uses `Map`. The C++ implementation uses `unordered_map`. Java uses a standard `Map`. PostgreSQL represents ownership explicitly through the `allocations` table.

## Workload Admission

A workload is admitted only when its complete resource requirement can be satisfied.

For example, a customer-facing service might require:

`compute = 8`

`memory = 32`

`database connections = 10`

A system with enough compute but only four available database connections must defer the workload.

The multi-resource check is deliberately performed before mutation. This creates a clear boundary between validation and commitment.

The Python implementation also combines repeated requests for the same resource type before checking capacity. That prevents two separate requirements from accidentally being evaluated independently when their combined demand exceeds the pool.

## Scheduling and Priority

Availability management becomes a scheduling problem when several workloads compete for limited capacity.

The Python implementation introduces `Priority` and an `AdmissionController`. Jobs are ordered by priority and admitted when their complete resource requirements fit.

The C++ case study uses `std::priority_queue` to model the same operational pattern with explicit workload objects. The Java implementation uses a `Priority` enum with weighted values and sorts workloads before admission.

Priority does not create capacity. It determines which eligible workload gets access when capacity is scarce.

A high-priority workload can still remain queued when its resource requirements cannot currently be satisfied.

A production scheduler may need additional policies such as deadlines, aging, fairness, reservation limits, workload classes, placement constraints, or starvation protection. Those policies are distinct from the basic availability calculation.

## JavaScript Event-Driven Model

The JavaScript implementation treats resource management as an event-driven service.

`AsyncScheduler` extends `EventTarget` and emits events when workloads are queued, started, and completed. This is useful for systems where resource state drives other application behavior, such as dashboards, operational notifications, queue processing, or browser-based infrastructure consoles.

The asynchronous `run` method represents the time during which a workload owns its reserved capacity. Completion releases the capacity and emits a completion event.

The example deliberately avoids treating asynchronous execution as a replacement for resource coordination. JavaScript's event loop does not provide distributed locking. A multi-process or multi-machine deployment requires coordination outside a single JavaScript runtime.

## C++ Capacity-Management Case Study

The C++ program models a capacity scheduler for an application platform.

`ResourcePool` owns the capacity state and allocation ownership. `GovernanceResourceManager` coordinates multi-resource admission. `CapacityScheduler` maintains a priority queue of workloads.

The case study demonstrates a production-relevant failure mode: a workload may require several resources, and one unavailable resource must prevent the entire admission.

The use of `std::map` for resource pools gives deterministic iteration while `std::unordered_map` provides efficient ownership lookup inside each pool. The priority queue provides efficient access to the highest-priority waiting workload.

The scheduler preserves workloads that cannot currently fit instead of discarding them. This is important because temporary scarcity should normally produce deferred execution rather than data loss.

The comments also identify a limitation of simple scalar capacity models. Real infrastructure can contain placement constraints such as individual machines, NUMA nodes, accelerator classes, zones, or other topology. A total CPU count does not prove that a particular placement is possible.

## Java Enterprise Model

The Java program uses explicit domain types instead of representing resource-management rules only through primitive values.

`ResourceType` identifies resource classes, while `Priority` represents scheduling importance. `ResourceRequirement` is a Java record that validates each individual requirement and provides an immutable value object.

`Workload` is also a record and makes its requirement list immutable with `List.copyOf`. This prevents callers from changing a workload's resource demand after it has entered the admission process.

`ResourceService` owns resource pools and synchronizes allocation and release operations. The synchronization is appropriate for the single-process model demonstrated by the program. A distributed enterprise deployment would need coordination at the database, distributed-lock, or resource-orchestrator layer.

`AdmissionPolicy` separates scheduling policy from raw resource accounting. It orders workloads by priority and delegates actual capacity decisions to `ResourceService`.

This separation is significant because priority is a policy decision, while capacity accounting is a state-management responsibility.

## Relational Data Model

The PostgreSQL implementation represents resource management through related entities.

`resource_types` defines resource categories.

`resource_pools` stores actual capacity and current availability.

`resource_consumers` identifies teams or services using capacity.

`workloads` stores executable units and their lifecycle state.

`workload_requirements` defines how much of each resource a workload needs.

`allocations` records the capacity actually reserved and whether it has been released.

This separation distinguishes requested capacity from allocated capacity. A queued workload can have requirements without consuming resources. An active workload has allocations. A completed workload retains allocation history while its active allocation records receive a release timestamp.

## Database Integrity

The database uses constraints to prevent structurally invalid states.

A resource capacity must be positive.

Available capacity cannot be negative.

Available capacity cannot exceed total capacity.

Requirement and allocation quantities must be positive.

Workload state is restricted to known lifecycle values.

Foreign keys prevent requirements from referring to nonexistent workloads or resource pools.

These constraints are important because application validation alone is insufficient when several services can access the same database.

## Indexing

The SQL schema creates indexes around actual resource-management access patterns.

`idx_workloads_state_priority` supports finding queued workloads in priority order.

`idx_requirements_pool` supports queries that inspect demand against a particular resource pool.

The partial allocation indexes focus on active allocations, where `released_at IS NULL`. This avoids treating historical allocation records as if they were still consuming capacity.

Indexes should follow workload patterns rather than being added indiscriminately. Each index creates storage overhead and adds work to writes.

## Transactions and Concurrency

Resource availability is vulnerable to race conditions.

Suppose two transactions both observe 10 available units and each requests 8. If both read the value before either updates it, both may believe the request is valid. The resulting allocations would require 16 units from a 10-unit pool.

The PostgreSQL transaction uses row locking to serialize access to the relevant resource records.

A correct distributed resource manager must define the boundary at which availability is checked and changed. The check and mutation cannot be treated as unrelated operations.

The application implementations demonstrate the same logical principle within their process boundaries. The Python manager uses a lock, while Java synchronizes allocation and release.

A process-local lock does not protect a resource shared by several application processes or machines. In such systems, the authoritative state must normally be coordinated by a shared transactional store or dedicated resource scheduler.

## Utilization and Capacity Planning

Utilization is useful but must be interpreted with workload behavior.

A pool operating at 95% utilization may indicate efficient resource use, but it may also leave too little room for bursts, failures, maintenance, or latency-sensitive workloads.

The Python implementation reports utilization and identifies high utilization as a capacity-planning signal.

The SQL view exposes capacity, available units, allocated units, and percentage utilization in a form suitable for operational reporting.

Capacity planning therefore involves more than increasing the size of the resource pool. The relevant questions include:

- Whether demand is stable or bursty.
- Whether workloads have different priorities.
- Whether capacity must be reserved for critical services.
- Whether one resource type is consistently the bottleneck.
- Whether high utilization causes latency or queue growth.
- Whether unused capacity is expensive.
- Whether failure recovery requires spare capacity.

## Quotas Versus Capacity

The API quota represented in the examples behaves differently from physical compute or memory.

Compute capacity can often be released when a workload completes. An API quota may instead represent a rate or consumption budget that resets according to an external policy.

The common resource-management abstraction is still useful because both systems need admission decisions based on remaining capacity. The release semantics must differ according to the resource's actual behavior.

This distinction prevents a generic resource manager from incorrectly assuming that every resource can simply be returned to a pool after use.

## Resource Lifecycle

A typical workload moves through a resource lifecycle:

`queued -> running -> completed`

A queued workload owns no active allocation.

Admission reserves the required resources and changes the workload to `running`.

Completion releases the active allocations and changes the workload to `completed`.

A rejected workload represents a failed admission decision rather than a temporary active allocation.

Keeping workload state separate from resource allocation history makes auditing possible. The SQL model can show which workload requested capacity, which resources were allocated, when allocation began, and when it was released.

## Failure Conditions

Resource management must explicitly handle invalid and constrained requests.

The implementations reject non-positive quantities instead of interpreting zero or negative values as meaningful capacity.

Unknown resource pools are treated as configuration errors.

Requests exceeding available capacity are rejected or deferred without partially consuming other resources.

Releasing an unknown owner does not create new capacity.

The SQL constraints provide a second line of protection against negative quantities and invalid pool states.

## Fragmentation and Placement

A scalar pool can hide placement limitations.

For example, a system may have four machines with two CPU units each. A request for eight CPU units might appear possible from the aggregate perspective, but a workload requiring eight units on one machine cannot be placed.

The examples intentionally keep the primary model aggregate so that the distinction is visible. Real schedulers may need additional dimensions such as:

- Host or node identity
- Availability zone
- Accelerator type
- NUMA topology
- Network locality
- Storage class
- Hardware capability

Those constraints turn resource availability into a placement problem rather than a simple subtraction operation.

## Common Design Errors

Treating capacity checks as independent from allocation creates race conditions.

Allocating one resource before checking another creates partial reservations.

Using only a global available counter loses ownership information and makes safe release difficult.

Ignoring resource types allows incompatible quantities to be combined.

Treating all resources as reusable in exactly the same way produces incorrect behavior for quotas and rate-limited resources.

Using utilization alone as a scaling trigger can cause over-provisioning or insufficient burst capacity.

Relying only on application validation leaves database state vulnerable to other writers.

## Production Considerations

A production resource-management service normally needs an authoritative source of capacity state, durable allocation records, concurrency control, observability, failure recovery, and clear ownership semantics.

Allocation should have a defined timeout or lease when workloads can disappear without explicitly releasing resources. Otherwise abandoned allocations can reduce availability indefinitely.

Capacity changes should be auditable. Increasing a pool from 100 to 150 units is operationally different from releasing 50 units that were previously allocated.

Monitoring should distinguish total capacity, currently available capacity, active allocations, queued demand, admission failures, and time spent waiting. These measurements reveal both resource saturation and scheduler behavior.

The most important architectural boundary is that resource availability is state, while scheduling is policy. The resource manager determines what capacity exists and what can be safely reserved. The scheduler determines which eligible workload should receive that capacity. Keeping those responsibilities distinct makes the system easier to validate, test, and evolve.
