# Defect Management

## Scope

This project models defect management as a controlled engineering workflow for identifying, recording, prioritizing, assigning, resolving, verifying, and reporting software defects.

The implementation treats defect management as a set of related but distinct concerns:

| Area | Responsibility |
|---|---|
| Identification | Capture reproducible evidence that a product behavior is incorrect |
| Triage | Determine severity, priority, ownership, and workflow eligibility |
| Assignment | Give an actionable defect to an accountable engineer |
| Resolution | Record the technical correction or an explicit disposition |
| Verification | Confirm whether the proposed correction actually addresses the defect |
| Reopening | Return a defect to active work when verification fails |
| Closure | Complete the lifecycle after successful verification |
| Reporting | Measure defect distribution, state, ownership, and resolution progress |

The central lifecycle implemented by the source files is:

`NEW → TRIAGED → ASSIGNED → IN_PROGRESS → RESOLVED → VERIFIED → CLOSED`

A failed verification follows a different path:

`RESOLVED → REOPENED → ASSIGNED → IN_PROGRESS`

A defect that is invalid, duplicated, or intentionally excluded from correction can be rejected during an allowed early lifecycle state.

## Defect Identification

A defect record needs enough information for another engineer or tester to reproduce the observed behavior without relying on undocumented knowledge.

The implementations therefore distinguish:

- title
- description
- defect type
- severity
- priority
- reporter
- assignee
- environment
- affected version
- reproduction steps
- expected result
- actual result
- resolution
- verification evidence
- audit history

The expected result describes the behavior that should occur. The actual result describes the observed behavior. The difference between these two fields provides the fundamental evidence that a defect exists.

Reproduction steps are validated rather than treated as optional descriptive text. The Python and database implementations require at least one reproduction step.

## Severity and Priority

Severity describes the technical or operational impact of a defect.

| Severity | Meaning |
|---|---|
| BLOCKER | Prevents a critical workflow or release |
| CRITICAL | Severe functional, security, or reliability impact |
| MAJOR | Significant functionality is impaired |
| MINOR | Limited functional or usability impact |
| TRIVIAL | Very small impact, usually cosmetic or low-risk |

Priority describes how urgently the organization should address the defect.

These concepts are intentionally separate. A major defect can have P0 priority when a release deadline or operational dependency makes immediate action necessary. A critical defect normally receives high priority, but severity and priority should not be treated as synonyms.

The Python and C++ implementations use severity and priority weights to produce an actionable open-defect queue.

## Defect Lifecycle

The lifecycle is explicitly constrained rather than allowing arbitrary status changes.

### New

A newly reported defect has enough information to enter the tracking system but has not yet been accepted through triage.

### Triaged

Triage confirms that the report is suitable for engineering action and establishes its operational classification.

### Assigned

An accountable developer or engineer has been selected.

### In Progress

Implementation work is actively taking place.

### Resolved

The assignee records a correction or disposition. Resolution does not mean the defect has been proven fixed.

### Verified

A tester or independent verification actor confirms that the correction satisfies the expected behavior.

### Reopened

Verification fails, so the defect returns to active engineering work.

### Closed

The defect has passed verification and the lifecycle is complete.

The distinction between `RESOLVED` and `VERIFIED` is important. Resolution represents an engineering claim that a correction has been implemented. Verification represents evidence that the correction works as intended.

## Python Implementation

The Python file models the workflow as a self-contained application service.

### Domain model

`Defect`, `User`, and `Comment` are dataclasses. Enumerations define defect status, severity, priority, and type without relying on unvalidated strings.

The `Defect` class owns state transitions such as:

- assignment
- starting work
- resolution
- verification
- reopening
- closure
- rejection

`DefectManager` owns application-level operations such as registration, triage, comments, open-defect retrieval, prioritization, and metrics.

### Validation

The implementation rejects:

- unknown users
- duplicate user identifiers
- empty titles
- empty descriptions
- missing expected or actual results
- missing reproduction steps
- unauthorized triage
- unauthorized resolution
- invalid lifecycle transitions
- missing resolution text
- empty comments

The state machine prevents a defect from being closed before successful verification.

### Audit history

Every important state change creates a timestamped history entry. This provides a simple audit trail suitable for debugging workflow behavior.

The implementation also records comments separately from lifecycle events.

### Failure handling

The executable example intentionally attempts an invalid transition after closure. The resulting exception is handled and the defect remains unchanged.

A second defect demonstrates failed verification and reopening.

### Metrics

The manager calculates:

- total defects
- open defects
- resolved-or-later defects
- rejected defects
- counts by status
- counts by severity

These metrics separate operational workload from completed or rejected records.

## JavaScript Implementation

The JavaScript implementation takes an event-driven approach.

### Event-driven lifecycle

`Defect` extends Node.js `EventEmitter`.

Lifecycle changes emit events that can be consumed by independent services. `NotificationService` listens for status and comment events and records notifications without embedding notification logic inside the lifecycle policy itself.

This separates state mutation from reactions to state changes.

The event flow is:

`Defect state change → EventEmitter → NotificationService`

### Policy evaluation

`DefectPolicy` evaluates whether a defect satisfies a defined operational policy.

The policy considers:

- required checks
- assignee existence
- critical-defect ownership approval
- P0 management approval

The policy returns an explicit decision containing an eligibility flag and failure reasons.

This prevents policy logic from being mixed with the mechanics of changing a defect's state.

### Asynchronous processing

`processDefects` uses Promises and `setImmediate` to demonstrate independent asynchronous processing of open defects without requiring external packages.

This structure can support future event queues or asynchronous integrations while retaining a simple executable implementation.

### Security considerations

The JavaScript model validates state transitions and actor identity before allowing sensitive actions.

For example, only the assigned user can start or resolve a defect. The implementation also uses `crypto.randomUUID()` for comment identifiers rather than predictable sequential identifiers.

## C++17 Implementation

The C++ implementation treats defect management as a governance engine.

### Domain structures

The program uses:

- `enum class` for controlled status, severity, and priority values
- `struct` for status checks and defect records
- `std::map` for deterministic defect storage
- `std::vector` for audit history and check collections
- `std::optional` for nullable assignment
- STL algorithms for prioritization

The use of `std::optional<int>` makes the absence of an assignee explicit instead of representing it with a special numeric value.

### Governance evaluation

The `merge_eligible` method evaluates whether a defect satisfies a set of governance conditions:

- required automated checks pass
- required approvals exist
- conversations are resolved
- critical or blocker defects have security-owner approval
- the defect is not rejected

This demonstrates that defect state can be one input into a larger engineering governance decision.

### Prioritization

Open defects are copied into a vector and sorted using severity and priority weights.

The ordering is:

1. higher severity
2. higher priority
3. lower defect identifier as a deterministic tie-breaker

Sorting requires `O(n log n)` time for `n` open defects.

The underlying `std::map` provides logarithmic lookup by defect identifier.

### Failure isolation

An attempted close of a defect that has not reached verification is rejected through an exception.

The program captures the state before and after the failed operation and verifies that the rejected operation did not mutate the state.

## Java 17 Implementation

The Java implementation represents defect management as an enterprise domain model.

### Domain types

The implementation uses:

- records for immutable user and status-check data
- enums for domain states
- classes for mutable aggregate behavior
- interfaces for policy abstraction
- collections for defect storage and audit events
- streams for open-defect reporting
- custom exceptions for domain failures

The `DefectPolicy` interface separates policy definition from defect state management.

`EnterpriseMergePolicy` provides a concrete policy implementation.

### Explicit state transitions

The `Defect` class controls its own lifecycle and validates allowed predecessor states before changing status.

For example:

`ASSIGNED → IN_PROGRESS`

is valid, while:

`NEW → IN_PROGRESS`

is rejected.

This protects the domain from callers bypassing intermediate workflow controls.

### Policy object

The enterprise policy requires:

- verified defect state
- sufficient approvals
- resolved conversations
- passing status checks
- manager approval for critical or blocker defects

The policy receives a `PolicyContext`, making its inputs explicit and testable.

### Immutable boundaries

Records and `List.copyOf` are used where data should not be externally mutated.

The audit trail is exposed as an immutable list, preventing callers from deleting or altering historical events through the returned collection.

## PostgreSQL Implementation

The PostgreSQL implementation provides a relational defect-management workflow.

### Relational model

The main relationship is:

`Repository → Defect → Comments`

with supporting entities:

`Users`
`Status Checks`
`Verification`
`Defect History`
`Tags`
`Defect Policy`

Repositories and branches establish the software context. Defects reference repositories and users. Comments capture discussion. Status checks represent automated evidence. Verification records represent human or test-based confirmation. History records state transitions.

### Constraints

The database enforces important rules through:

- primary keys
- foreign keys
- unique constraints
- check constraints
- enum types
- triggers

Examples include:

- titles must contain meaningful text
- descriptions must contain sufficient information
- reproduction steps cannot be empty
- valid user roles are restricted
- defect states are restricted
- resolved and closed defects require a resolution
- assigned and later states require an assignee

These rules remain active even when data is modified outside an application layer.

### Transition trigger

`validate_defect_transition` implements database-level lifecycle protection.

It prevents invalid transitions such as:

`CLOSED → IN_PROGRESS`

and:

`NEW → RESOLVED`

It also ensures that state-dependent fields are populated.

This provides defense in depth because workflow correctness does not depend solely on application code.

### Audit trigger

`audit_defect_transition` automatically records status changes in `defect_history`.

The audit trail therefore originates from database state changes rather than requiring every application caller to remember to create an audit record.

### Status checks

Automated validation is represented by `status_check`.

A check can be:

- `PENDING`
- `PASSED`
- `FAILED`

This separates automated evidence from the defect's lifecycle state.

A defect can therefore be technically resolved while a required integration test remains pending.

### Verification

The `verification` table records:

- tester
- pass/fail result
- evidence
- verification timestamp

This makes verification evidence a first-class record rather than a comment embedded in free-form text.

## Reporting and Evaluation

The SQL script creates `defect_merge_eligibility` as a view.

The view combines:

- defect lifecycle state
- status-check results
- verification results
- repository policy

The result is a derived eligibility decision rather than another manually maintained field.

This distinction is important because eligibility should be recalculable from authoritative state.

## Performance Considerations

The implementations use different structures appropriate to their runtime environments.

| Implementation | Main structure | Relevant performance property |
|---|---|---|
| Python | Dictionaries and sorted lists | Fast identifier lookup; `O(n log n)` prioritization |
| JavaScript | `Map` and `Set` | Efficient identifier and membership operations |
| C++17 | `std::map` and vectors | Ordered logarithmic lookup and STL sorting |
| Java 17 | `HashMap` and streams | Expected constant-time hash lookup and linear filtering before sorting |
| PostgreSQL | Indexed relational tables | Index-assisted filtering for common status, ownership, version, and child-record queries |

The database indexes target actual access patterns rather than every column. Indexes on status/priority, assignee/status, repository/version, comments, and status checks support operational queries used by the workflow.

Excessive indexing would increase write cost and storage usage, so indexes should correspond to measured query requirements.

## Security Controls

Defect management can contain sensitive operational information, particularly when security vulnerabilities are reported.

The implementations apply several controls:

- explicit actor validation for sensitive lifecycle actions
- role validation for triage
- assignee checks before resolution
- constrained workflow transitions
- immutable or append-oriented audit information
- database foreign-key enforcement
- server-side database constraints
- explicit status-check evidence
- separate verification records

A production implementation should also enforce authentication, authorization, encrypted transport, secret management, access logging, retention policies, and appropriate disclosure controls at the deployment layer.

The sample programs intentionally avoid embedding credentials or external service secrets.

## Failure Modes

Important defect-management failures represented by the implementations include:

| Failure | Handling |
|---|---|
| Missing reproduction information | Validation rejects the defect |
| Unknown reporter or actor | Operation fails |
| Unauthorized assignment or resolution | Permission failure |
| Invalid lifecycle transition | Domain exception or database exception |
| Missing resolution | Resolution operation rejected |
| Failed verification | Defect is reopened |
| Failed automated check | Governance decision is blocked |
| Missing required approval | Governance decision is blocked |
| Closed defect mutation | Transition rejected |
| Missing assignee in active state | Application/database validation rejects state |

These failures are treated as workflow conditions rather than silently ignored.

## Practical Workflow

A realistic engineering workflow represented by the project is:

`Reporter`
→ records reproducible evidence
→ `Triage`
→ determines severity and priority
→ `Assignment`
→ selects accountable engineer
→ `Implementation`
→ records resolution
→ `Verification`
→ validates expected behavior
→ `Closure`

If verification fails:

`Verification`
→ `REOPENED`
→ `Assignment`
→ `Implementation`
→ `Verification`

Automated status checks operate alongside this lifecycle and provide additional evidence for release or governance decisions.

## Distinguishing Defect Concepts

The project deliberately separates concepts that are frequently conflated.

**Defect identification** establishes that observed behavior differs from expected behavior.

**Severity** describes impact.

**Priority** describes urgency.

**Resolution** records what engineering did about the defect.

**Verification** establishes whether the resolution actually satisfies the expected behavior.

**Closure** completes the workflow after successful verification.

**Audit history** records how the state changed over time.

**Status checks** provide automated evidence.

**Policy evaluation** determines whether the collected evidence satisfies defined organizational requirements.

These distinctions prevent a defect tracker from becoming merely a list of issue titles and statuses.

## Cross-Language Design Comparison

The five implementations intentionally use different engineering perspectives.

| File | Primary perspective |
|---|---|
| Python | Application-level defect lifecycle and metrics |
| JavaScript | Event-driven lifecycle and policy evaluation |
| C++17 | Governance engine and deterministic prioritization |
| Java 17 | Enterprise domain model and policy abstraction |
| PostgreSQL | Relational persistence, constraints, triggers, and reporting |

The same core domain is therefore represented through different computational models rather than being mechanically translated between languages.

## Limitations

The source files are executable learning artifacts rather than a complete production defect platform.

They do not attempt to provide:

- distributed locking
- authentication infrastructure
- multi-tenant isolation
- external issue-tracker synchronization
- binary attachment storage
- full-text search infrastructure
- production notification delivery
- distributed event processing
- database migration management
- enterprise identity integration

The PostgreSQL model provides database-level workflow enforcement, but production deployments would still need appropriate transaction boundaries and concurrency controls for simultaneous updates.

The in-memory Python, JavaScript, C++17, and Java 17 implementations lose state when their processes terminate. PostgreSQL provides durable persistence for the relational workflow.
