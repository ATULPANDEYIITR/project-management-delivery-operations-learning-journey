# Scope Review: Reviewing Scope Management

## Topic Boundary

Scope review is the controlled examination of proposed, completed, or changed work against an approved scope baseline. Its central question is whether the work remains within the agreed delivery boundary.

Scope review is different from simply checking whether software works. A feature can be technically correct, tested, secure, and well implemented while still being outside the approved scope of a particular release.

This repository models scope review through three complementary implementations:

- The Python program provides a structured scope-management simulation with baseline validation, change requests, scope classification, findings, decisions, edge-case handling, and reporting.
- The JavaScript program models scope review as an event-driven workflow. Every review and governance transition produces an audit event, which demonstrates how scope management can become observable in an application.
- The C++ program presents a repository-governance case study in which a scope engine evaluates proposed release changes, records findings, enforces governance conditions, and maintains an audit trail.

The implementations deliberately distinguish scope analysis from the final governance decision. Classification provides evidence; it does not replace the decision process.

## Scope Management and the Scope Baseline

A scope baseline is the reference against which proposed work is evaluated. It should identify what the release is intended to contain and, where useful, what is explicitly excluded.

A useful baseline contains more than feature names. The implementations represent each scope item with:

- a stable identifier
- a descriptive name
- a description of the intended work
- acceptance criteria
- priority where relevant
- explicit exclusion status where applicable

Acceptance criteria are particularly important because a scope item can be referenced by a change request without proving that the requested behavior is actually covered by the baseline.

For example, `SCOPE-101` in the implementations represents a release scope dashboard. A request to add filtering to that dashboard can be evaluated against the existing item. A request to replace the dashboard with an unrelated commercial platform is materially different even though both requests mention the dashboard.

The baseline therefore establishes the boundary, while the acceptance criteria provide evidence for determining whether a requested change belongs inside that boundary.

## Scope Review

A scope review compares a proposed change with the approved baseline.

The implementations examine several characteristics of a request:

| Review characteristic | Scope-management purpose |
| --- | --- |
| Baseline reference | Establishes which approved work the request claims to modify |
| Unknown reference | Detects work that has no corresponding approved scope item |
| Explicit exclusion | Prevents excluded work from being silently treated as approved |
| Description | Provides evidence about the actual requested behavior |
| Estimated effort | Identifies material changes that may require explicit assessment |
| Business justification | Records why the requester wants the change |
| Findings | Documents discrepancies between the request and the baseline |
| Review decision | Records the governance action after the evidence has been examined |

A scope review is therefore more than a search for matching feature names. It examines the relationship between the requested outcome and the approved delivery boundary.

## Scope Classification

The Python and JavaScript implementations use four scope classifications:

| Classification | Meaning |
| --- | --- |
| `in_scope` | The request maps to approved scope and does not trigger detected expansion conditions |
| `partially_in_scope` | Some requested work maps to approved scope while other work does not |
| `out_of_scope` | The request cannot be mapped to approved work |
| `requires_change_control` | The request requires explicit governance because it changes the approved boundary or represents a material scope delta |

`requires_change_control` is intentionally treated as a governance state rather than as a claim that the requested work is inherently invalid. A legitimate business requirement can still require a formal scope decision before it becomes part of the release.

## Reviewing Scope Changes

A change request should provide enough information for a reviewer to determine what is being proposed.

The implementations represent change requests with:

- a unique request identifier
- title
- description
- requester
- related baseline items
- estimated effort
- business justification
- request timestamp in Python

The relationship between a change request and a baseline item is important. A request without a baseline reference may indicate new work rather than modification of existing work.

For example, the request `CR-401` modifies the existing scope-dashboard capability. It is associated with `SCOPE-101`, estimates six hours, and describes filtering of existing information.

The request `CR-402` is different. It references both an approved dashboard item and `SCOPE-104`, which is explicitly excluded. It also describes a redesign and estimates substantial effort. The system therefore does not silently classify the complete request as approved scope.

## Scope Creep Detection

Scope creep occurs when work expands beyond the agreed boundary without the corresponding scope decision or baseline update.

The implementations detect several practical indicators:

- work with no baseline association
- references to excluded scope
- descriptions containing expansion signals such as redesign, migration, replacement, or additional functionality
- materially larger effort estimates

These indicators are not presented as a universal mathematical definition of scope creep. They are review signals.

Natural language detection is particularly limited. A word such as `new` can appear in a legitimate description without meaning that the project scope has expanded. For that reason, the implementation creates a finding rather than automatically rejecting the request.

The reviewer must compare the requested behavior with the actual baseline.

## Findings and Scope Review Quality

A finding records a discrepancy or condition that requires attention.

The implementations associate findings with:

- severity
- subject
- description
- affected scope items
- recommendation
- resolution state

A finding should explain the evidence rather than simply state that a request is problematic.

For example, the JavaScript implementation can produce an `Excluded scope item` finding that identifies the excluded baseline item and recommends changing the approved scope before treating the work as baseline scope.

This makes the review auditable. A future reviewer can understand why a decision was reached rather than seeing only an unexplained accept or reject value.

## Scope Decisions

The implementations deliberately separate classification from decision.

A classification is generated by the scope-review engine. A final decision is recorded by an identified reviewer.

The supported decisions are:

- `accept`
- `accept_with_notes`
- `revise_scope`
- `reject`

The exact governance process can differ between organizations. The important design principle is that the review evidence and the governance decision are separate pieces of information.

The Python and C++ implementations also prevent an `accept` decision when unresolved findings remain. This models a useful governance control: unresolved scope discrepancies should not disappear merely because somebody attempts to mark the request as accepted.

## Python Implementation

The Python program uses `dataclass` records to represent scope-management entities.

`ScopeItem` represents an approved or excluded baseline item. Its acceptance criteria provide a concrete boundary for evaluating requested work.

`ChangeRequest` represents proposed work. It carries the information needed to compare the proposal with the baseline.

`ScopeFinding` represents a review observation and tracks whether that observation has been resolved.

`ScopeBaseline` validates the baseline before the review engine uses it. This prevents malformed governance data from silently influencing later decisions.

`ScopeReviewEngine` performs the central analysis. Its `classify()` method checks baseline references, exclusions, expansion signals, and estimated effort. The `finalize()` method records the reviewer and governance decision separately from the classification.

The Python implementation also maintains a review history and produces an aggregate scope-delta report. This makes it possible to inspect the number of reviewed requests, the number requiring change control, and the estimated aggregate effort delta.

The edge-case demonstrations cover negative effort values and attempts to accept a review containing unresolved findings.

## JavaScript Implementation

The JavaScript implementation approaches the same domain through event-driven behavior rather than translating the Python structure line by line.

`ScopeBaseline` uses a JavaScript `Map` for efficient identifier-based lookup. This reflects a common application pattern where scope items are accessed by stable IDs rather than by repeatedly scanning an array.

`ScopeReviewEngine` exposes an `on()` listener mechanism. Review transitions emit events such as `scope.reviewed`, `scope.finding_resolved`, and `scope.decision_recorded`.

This event model is useful for governance applications because a scope decision may need to feed multiple consumers, such as an audit log, dashboard, notification mechanism, or compliance record.

The implementation also keeps the analysis result in a `Map`, allowing subsequent operations such as finding resolution and finalization to retrieve a review by its request identifier.

JavaScript-specific validation demonstrates how runtime type checking matters in a dynamically typed environment. The engine explicitly checks strings, arrays, numeric effort values, and supported decision values before processing requests.

## C++ Repository Governance Case Study

The C++ implementation models a repository release-governance engine.

The scenario is a release-governance portal responsible for evaluating proposed changes against a release scope baseline.

The architecture consists of three principal layers:

`ScopeBaseline` owns the approved scope reference data.

`ScopeGovernanceEngine` performs analysis, resolves findings, and records governance decisions.

`ScopeReview` stores the analysis result and final decision for an individual change request.

The baseline stores scope items in an `unordered_map`, keyed by stable scope identifiers. Expected lookup is approximately constant time, which is appropriate for repeated membership checks during review.

The engine creates findings for unknown scope references, excluded items, unmapped work, possible expansion, and material effort changes.

The finalization operation is deliberately separate from analysis. The engine does not infer that an item should be accepted simply because some baseline references matched.

The audit log records events such as:

- `scope.reviewed`
- `scope.finding_resolved`
- `scope.decision_recorded`

This produces a trace of governance actions without mixing audit concerns into the scope-item data itself.

## Scope Review Workflow

The implementations model the following relationship:

`Approved baseline → Proposed change → Scope analysis → Findings → Finding resolution → Governance decision → Audit record`

The baseline establishes the reference state.

The proposed change describes the requested modification.

Scope analysis determines whether the request can be mapped to the baseline and whether it contains conditions that require additional examination.

Findings document discrepancies.

Resolution records what happened to each finding.

The governance decision records the authorized outcome.

The audit record preserves the sequence of important state transitions.

This separation prevents a common governance failure in which an implementation change is treated as approved simply because someone has already started working on it.

## Scope Review Versus Technical Review

A technical review and a scope review answer different questions.

A technical review may examine correctness, architecture, maintainability, testing, security, performance, and implementation quality.

A scope review examines whether the requested work belongs to the approved delivery boundary.

These concerns can intersect but should not be conflated.

A technically excellent feature can still be outside the current release scope.

Conversely, an in-scope feature can require technical rework if its implementation does not satisfy engineering requirements.

The distinction is important because scope governance should not become a proxy for technical approval.

## Relationship to Change Control

When a proposed change falls outside the approved baseline, the appropriate response is not necessarily to discard the requirement.

Change control provides a mechanism for deciding whether the baseline should change.

A formal change can require examination of:

- business justification
- delivery impact
- effort
- dependencies
- schedule implications
- resource implications
- acceptance criteria
- downstream scope effects

If the change is approved, the baseline should be updated through the organization's controlled process rather than leaving the old baseline in place while the implementation silently diverges from it.

This is why the implementations use `requires_change_control` as a meaningful state.

## Edge Cases

### Unknown Scope References

A request may contain an identifier that does not exist in the baseline. This can result from stale project information, a typo, or a genuinely new requirement.

The implementations create a finding instead of treating the unknown identifier as automatically approved.

### Explicitly Excluded Work

An excluded item is stronger evidence than an unknown item. The baseline explicitly states that the work is outside the current boundary.

The implementations therefore use a higher severity for excluded scope references.

### Unmapped Requests

A request with no related baseline items can represent entirely new work. The implementations flag this as an unmapped change.

### Large Effort Changes

Effort is not equivalent to scope. A complex implementation of an existing requirement can require many hours without expanding scope.

The implementations therefore use large effort as a review signal rather than as proof of scope expansion.

### Ambiguous Language

Natural-language descriptions can contain words associated with scope expansion without actually changing scope. The systems create findings for these signals so that a reviewer can inspect the context.

Automatic text matching should not replace human scope interpretation.

### Unresolved Findings

An unresolved scope discrepancy should remain visible. The Python and C++ implementations explicitly prevent an `accept` decision when findings remain unresolved.

## Common Scope Review Failures

A scope review becomes weak when reviewers evaluate only whether a requested feature sounds related to an existing feature.

Another failure is treating the current implementation as the scope definition. Implementation is evidence of what has been built; it is not necessarily evidence of what was approved.

A further failure occurs when exclusions are documented but not enforced. An excluded item that can be added without explicit governance is effectively not protected.

Another problem is silently absorbing small requests. Individually minor changes can accumulate into a material change in the release boundary. A scope register provides traceability for these decisions.

Finally, recording only the final decision without the underlying findings makes later auditing difficult. A useful scope review preserves the reasoning evidence that led to the decision.

## Performance Considerations

The Python implementation primarily uses dictionaries for baseline lookup, providing expected constant-time identifier access.

The JavaScript implementation uses `Map` for both baseline items and review records, providing the same general lookup model.

The C++ implementation uses `unordered_map` for scope-item lookup. The expected lookup complexity is approximately O(1), although actual performance depends on hashing behavior and load factor.

Finding resolution is linear in the number of findings attached to a review because the implementations search the finding collection for the requested identifier.

Audit histories grow with the number of recorded events. A production system with very large history requirements would normally persist events externally rather than retaining an unbounded in-memory collection.

## Security and Governance Considerations

Scope-management data can contain commercially sensitive information about planned functionality, release timing, business priorities, and rejected changes.

A production implementation should therefore enforce authorization around operations such as:

- modifying the approved baseline
- creating scope changes
- resolving findings
- recording governance decisions
- changing exclusions
- accessing historical scope records

The identity of the reviewer should be preserved rather than accepting anonymous governance actions.

Audit records should be protected against unauthorized modification because the value of the history depends on its integrity.

The implementations intentionally keep authorization outside the core scope engine. The engine demonstrates the domain rules, while a production service would place identity and authorization controls around those operations.

## Production Considerations

A production scope-management system would normally persist baselines and reviews rather than storing them only in process memory.

Baseline versions should be immutable after approval or should use controlled versioning. This allows a historical review to be interpreted against the baseline that existed when the decision was made.

Scope changes should have their own lifecycle rather than modifying the baseline silently.

Audit events should retain actor identity, timestamp, affected object, previous state where appropriate, and resulting state.

The system should also distinguish between the approved baseline and the current implementation state. A repository can contain work that is not yet approved, and a scope-management system should make that discrepancy visible rather than assuming implementation equals authorization.

## Practical Interpretation

The central technical relationship is:

**Scope baseline defines the boundary.**

**Scope review compares proposed work with that boundary.**

**Findings document discrepancies.**

**Change control handles requests that alter the boundary.**

**Governance decisions determine whether the proposed change is accepted, revised, or rejected.**

The three implementations express the same domain through different technical structures: Python emphasizes structured simulation and data validation, JavaScript emphasizes observable event-driven behavior, and C++ emphasizes an explicit governance engine with efficient identifier lookup and a repository-release case study.
