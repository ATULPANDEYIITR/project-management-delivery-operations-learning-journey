# Activity Sequencing: Determining Activity Order

## Topic Scope

Activity sequencing determines the logical order in which project activities can be performed. The central question is not simply which activity has a smaller identifier or which task appears first in a list. The question is which activities must occur before other activities can legitimately begin.

A sequence is created from relationships such as:

- an architecture activity must finish before implementation can begin;
- a test strategy can begin after the relevant requirements are known;
- integration testing must wait until all required implementation and environment activities are complete;
- deployment must wait until release validation has finished.

The important distinction is between **activity order** and **calendar scheduling**. Sequencing establishes dependency constraints. Scheduling adds durations, resource availability, calendars, capacity, and other constraints to determine when activities actually occur.

The implementations in this project model activity sequencing as a directed dependency graph. An activity is a node, and a predecessor relationship is a directed edge:

`A -> B`

means that activity `A` must be completed before activity `B` can start.

## Core Model

Each activity contains:

| Attribute | Meaning |
| --- | --- |
| Activity ID | Stable identifier used by the dependency graph |
| Name | Human-readable description of the work |
| Duration | Estimated execution time |
| Predecessors | Activities that must finish before this activity starts |

Consider a release workflow containing:

`A -> B -> D -> G -> H -> I`

and another branch:

`A -> C -> F -> G`

The branches after `A` are dependency-independent. `G`, which represents integration testing, is a merge point because it requires work from both branches.

This distinction matters because a valid sequence does not necessarily mean that every activity must execute sequentially. Several activities may be ready at the same time.

## Dependency Relationships

A predecessor relationship expresses a logical readiness condition.

For example:

`B: Design application architecture`

with predecessor `A: Finalize release scope`

means the architecture activity is not dependency-ready until the scope activity has completed.

A downstream activity can have multiple predecessors:

`G: Execute integration testing`

with predecessors `D`, `E`, and `F`

means all three activities must be complete before `G` becomes dependency-ready.

This creates a synchronization point. The earliest possible start of `G` is controlled by the latest-finishing predecessor.

The dependency model therefore answers questions such as:

- Which activity can start immediately?
- Which activities become available after a particular activity finishes?
- Which activities can theoretically run in parallel?
- Which activity is blocked by an unfinished predecessor?
- Does the proposed order violate any dependency?
- Does the dependency network contain a circular relationship?

## Activity Sequencing as a Directed Graph

The graph representation is particularly useful because it makes ordering rules explicit.

For an edge:

`A -> B`

the invariant is:

`position(A) < position(B)`

A sequence is dependency-valid only when that condition holds for every predecessor relationship.

For example, this sequence is valid:

`A -> B -> C`

when `C` depends on `B`.

This sequence is invalid:

`A -> C -> B`

because `C` has been placed before its required predecessor `B`.

A dependency graph should also be acyclic for ordinary forward project sequencing. A cycle such as:

`A -> B -> C -> A`

does not define a feasible starting point. Every activity waits for another activity in the same cycle.

## Topological Ordering

The Python, JavaScript, and C++ implementations use topological sorting to produce a dependency-valid order.

The fundamental mechanism is:

- calculate the number of unresolved predecessors for each activity;
- identify activities with zero unresolved predecessors;
- place a ready activity into the sequence;
- remove its dependency contribution from successor activities;
- make newly unlocked activities available;
- continue until all activities have been processed.

The Python implementation uses Kahn's algorithm with a `deque`. The JavaScript implementation maintains a sorted ready array. The C++ implementation uses a priority queue so that simultaneous ready activities have deterministic ordering.

Topological ordering is not necessarily the only valid sequence. If two activities have no dependency relationship, both relative orders may be valid.

For example, if:

`A -> B`

and

`A -> C`

then both of these may satisfy the dependency graph:

`A -> B -> C`

and:

`A -> C -> B`

The graph determines the required ordering constraints, not an arbitrary preference between unrelated activities.

## Dependency Levels and Parallelism

The implementations also group activities into dependency levels.

An activity with no predecessors belongs to the initial level.

An activity whose predecessors are all in earlier levels is placed after those predecessors. This produces a dependency frontier that can expose parallel work.

For example:

`A`

followed by:

`B     C`

followed by:

`D`

shows that `B` and `C` are both unlocked after `A`. They are candidates for parallel execution from a dependency perspective.

That does not mean they can always execute simultaneously.

If both activities require the same unavailable specialist, machine, environment, or approval authority, a resource-constrained scheduling process may need to serialize them.

Therefore:

**Dependency parallelism is not the same as resource feasibility.**

Activity sequencing determines logical order. Resource scheduling determines whether logically available work can actually be performed at the same time.

## Python Implementation

The Python program provides the most complete instructional graph model.

`Activity` represents a single unit of work and validates basic properties such as non-empty identifiers and non-negative durations.

`ActivityNetwork` stores the dependency graph and provides separate mechanisms for:

- dependency validation;
- successor construction;
- topological ordering;
- dependency-level calculation;
- CPM forward and backward passes;
- critical-path identification;
- parallelism detection;
- dependency-table generation.

The `validate()` method checks for missing predecessors and then invokes topological ordering. This is important because a dependency reference to an unknown activity is a different failure from a circular dependency.

For example, an activity referring to `UNKNOWN` cannot be evaluated because the graph is incomplete. A cycle, by contrast, is a structurally complete graph whose relationships make sequencing impossible.

### Critical Path Analysis

The Python implementation goes beyond pure ordering by applying the Critical Path Method to the dependency network.

For each activity it calculates:

- `ES`: earliest start;
- `EF`: earliest finish;
- `LS`: latest start without delaying the project completion date;
- `LF`: latest finish without delaying the project completion date;
- `Float`: scheduling flexibility under the modeled network.

The forward pass calculates:

`ES(activity) = maximum EF of its predecessors`

for an activity with predecessors.

Then:

`EF(activity) = ES(activity) + duration`

The backward pass begins from the calculated project completion time and moves in reverse dependency order.

For an activity with successors:

`LF(activity) = minimum LS of its successors`

and:

`LS(activity) = LF(activity) - duration`

An activity with zero total float is treated as critical in the modeled schedule.

The implementation also supports more than one critical path when the network contains multiple zero-float branches.

### Dependency Change Demonstration

The Python program deliberately modifies one dependency between two otherwise parallel branches.

Originally:

`A -> B`

and:

`A -> C`

allow `B` and `C` to proceed independently after `A`.

When the relationship changes to:

`A -> B -> C`

the branches become partially serial.

This demonstrates an important sequencing effect: adding a logical dependency can change the feasible activity order and increase the calculated project duration.

## JavaScript Implementation

The JavaScript implementation approaches activity sequencing through an event-driven model.

`ActivityNetwork` handles the static dependency graph, while `SequencingEngine` models state changes as activities become ready, start, and finish.

This separation reflects a useful software design distinction:

- the network defines what is legally possible;
- the engine observes execution state and reacts to changes.

The `SequencingEngine` extends `EventTarget`. When an activity starts, an `activity-started` event is dispatched. When it finishes, an `activity-completed` event is dispatched.

The completion event calculates which activities have become newly dependency-ready.

This represents an important runtime characteristic of activity sequencing: readiness changes dynamically as predecessor activities complete.

### Asynchronous Execution

The JavaScript simulation uses `Promise` and `setTimeout()` to represent concurrent execution of dependency-ready activities.

The simulated duration is scaled into milliseconds so the dependency behavior can be observed without waiting for real project durations.

When several activities are ready, they are launched through separate promises and awaited with `Promise.all()`.

This is intentionally different from merely translating the Python algorithm. The JavaScript implementation demonstrates how a dependency model can drive an event-oriented execution process.

The simulation still makes an important limitation explicit: launching all dependency-ready activities does not model scarce resources.

A production scheduler would need additional controls for:

- maximum concurrent activities;
- specialist availability;
- machine capacity;
- environment availability;
- working calendars;
- activity priorities;
- resource conflicts.

## C++ Case Study

The C++ program models a software release-engineering workflow.

The activities are:

| ID | Activity | Duration | Predecessors |
| --- | --- | ---: | --- |
| A | Finalize release scope | 2 | None |
| B | Design application architecture | 3 | A |
| C | Design test strategy | 2 | A |
| D | Implement persistence layer | 4 | B |
| E | Implement service layer | 5 | B |
| F | Prepare integration environment | 2 | C |
| G | Execute integration testing | 3 | D, E, F |
| H | Perform release validation | 2 | G |
| I | Deploy production release | 1 | H |

This network contains two branches after `A`.

The architecture branch produces `D` and `E`, while the testing branch produces `F`. The integration activity `G` cannot begin until all three required inputs are complete.

### C++ Data Structures

The case study uses an `Activity` structure containing:

- an identifier;
- a descriptive name;
- a duration;
- a set of predecessor identifiers.

`ReleaseSequencingEngine` owns the activity model and implements the graph algorithms.

`std::unordered_map` provides activity lookup by identifier, while `std::set` provides deterministic predecessor and successor traversal.

The topological-ordering mechanism uses a priority queue. When multiple activities have zero unresolved predecessors, the queue selects them deterministically.

### Proposed Sequence Validation

The C++ implementation does not merely calculate an order. It can validate an externally proposed order.

The proposed sequence is checked for:

- correct number of activities;
- unknown activity identifiers;
- duplicate activity identifiers;
- predecessor relationships that are violated by the proposed positions.

For every relationship `predecessor -> activity`, the validator requires the predecessor's position to be smaller than the dependent activity's position.

This models a practical governance rule: a schedule or execution plan can be rejected when it contradicts the project's dependency network.

### Critical Path Analysis

The C++ case study implements both forward and backward CPM passes.

The forward pass establishes the earliest feasible timing under the dependency constraints.

The backward pass establishes the latest timing that preserves the calculated project completion date.

The resulting float values identify activities that have no timing flexibility under the modeled assumptions.

This connects activity sequencing with schedule impact. Sequencing alone determines legal order, while CPM shows how dependency structure and activity durations influence completion timing.

## Relationship Between Sequencing, Duration, and Resources

Activity sequencing should not be confused with assigning every activity a fixed calendar slot.

Suppose:

`A -> B`

and:

`A -> C`

After `A` completes, both `B` and `C` are dependency-ready.

If `B` requires a database specialist and `C` requires a test specialist, they may proceed concurrently.

If both require the same specialist, logical sequencing still says both are ready, but resource constraints prevent simultaneous execution.

This creates two separate layers:

**Logical layer**

Determines whether predecessor relationships allow an activity to begin.

**Resource layer**

Determines whether the necessary people, equipment, environments, or capacity are available.

A robust scheduling system should preserve this distinction instead of encoding resource limitations as artificial dependencies unless the resource constraint is intentionally part of the scheduling model.

## Common Failure Modes

### Missing predecessor

An activity references a predecessor that is not present in the network.

Example:

`Integration -> UNKNOWN`

There is no way to establish whether `UNKNOWN` has completed. The network is therefore incomplete and should be rejected rather than silently treating the missing activity as already finished.

### Circular dependency

A cycle such as:

`A -> B -> C -> A`

has no dependency-valid starting point.

A topological-sort algorithm detects this because some activities remain with unresolved incoming dependencies after all available activities have been processed.

### Incorrect manual ordering

A human may place a dependent activity before its predecessor even when the activity names appear reasonable.

For example:

`A -> B -> C`

cannot be represented by:

`A -> C -> B`

when `C` explicitly depends on `B`.

The C++ implementation checks proposed sequences directly to catch this error.

### Artificial serialization

A common modeling mistake is to put every activity into a single chain even when no dependency requires that order.

If:

`A -> B`

and:

`A -> C`

there is no dependency-based reason to force `B -> C`.

Artificial serialization can increase elapsed time and hide opportunities for legitimate parallel work.

### Hidden resource dependency

The opposite problem occurs when a dependency graph indicates parallel work but the required resource cannot actually support it.

Dependency analysis alone cannot guarantee resource feasibility.

### Assuming one topological order is the only correct order

A graph can have multiple valid topological orders.

When two activities are independent, their relative order may change without violating the dependency rules.

The correct question is whether the proposed sequence satisfies every required predecessor relationship, not whether it exactly matches one particular topological sort.

## Edge Cases

### Zero-duration activities

A zero-duration activity can represent an instantaneous logical milestone or decision point in the simplified model.

It still participates in dependencies and can therefore affect which activities become ready.

### Multiple predecessors

An activity with several predecessors must wait for all of them under the finish-to-start dependency model represented by these implementations.

Its earliest start is controlled by the latest predecessor finish.

### Multiple terminal activities

A network may contain several activities with no successors. CPM must treat the latest terminal finish as the project completion point.

### Multiple critical paths

Equal-duration branches can produce multiple zero-float paths. A critical-path implementation should not assume that exactly one path exists.

### Independent activities

Two activities with no path between them can appear in different valid positions in a topological sequence.

### Empty network

An empty network has no work and therefore a calculated duration of zero in the provided CPM implementation. A production system may instead reject an empty project because it does not represent a meaningful schedule.

## Algorithmic Complexity

For a graph with `V` activities and `E` dependency relationships, topological sorting is fundamentally linear in the graph size:

`O(V + E)`

when adjacency structures provide efficient edge traversal.

The CPM forward and backward passes also process each activity and dependency relationship once, giving:

`O(V + E)`

for the main schedule calculation.

The JavaScript ready queue is maintained as a sorted array for clarity and deterministic demonstration. Repeated sorting can introduce additional overhead compared with a heap-based implementation.

The C++ implementation uses a priority queue for ready activities, providing efficient deterministic selection.

Memory usage for the dependency graph is:

`O(V + E)`

because each activity and predecessor relationship must be represented.

## Practical Design Decisions

The implementations deliberately represent predecessors explicitly rather than relying on activity names or list positions.

This makes the sequencing model resilient to changes in presentation order.

An activity's position in an input file does not determine its execution order. The dependency graph determines the legal order.

Deterministic selection among simultaneously ready activities is used for reproducible demonstrations. Determinism is useful for testing, logging, debugging, and comparing schedule calculations.

Validation occurs before schedule analysis. This prevents downstream calculations from operating on an incomplete or cyclic graph.

The model also keeps logical sequencing separate from resource allocation. Combining those concerns too early can make it difficult to determine whether a delay was caused by a dependency or by resource scarcity.

## Debugging Considerations

When an activity is unexpectedly blocked, inspect its predecessor set first.

A useful debugging path is:

`blocked activity -> predecessors -> predecessor completion state`

If a dependency is missing from the model, the activity may never become ready.

If a cycle exists, inspect the unresolved activities returned by the topological-sort validation.

If the calculated project duration unexpectedly increases after a schedule change, compare the dependency graph before and after the change. A new predecessor relationship may have converted parallel work into serial work.

If an activity is logically ready but cannot actually start, inspect resource constraints separately from the dependency graph.

## Production Considerations

The implementations use a simplified finish-to-start dependency model. Real project scheduling systems may require additional relationship types such as start-to-start, finish-to-finish, and finish-to-start relationships with leads or lags.

Real scheduling systems may also require:

- working calendars rather than simple elapsed durations;
- holidays and non-working periods;
- resource capacities;
- skills and role constraints;
- priority rules;
- baselines and schedule versions;
- progress percentages;
- actual start and finish dates;
- dependency-change auditing;
- uncertainty and probabilistic duration estimates;
- schedule recalculation after changes.

A production implementation should also distinguish planned dependencies from accidental sequencing. A dependency should exist because the downstream activity genuinely requires the upstream result, not merely because one task happened to be entered first.

The fundamental principle remains the same: **activity order should be derived from explicit, validated relationships rather than from arbitrary list position.**
