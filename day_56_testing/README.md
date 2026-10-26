# Testing Project Deliverables: Repository Change Governance

## Purpose

This project models testing and validation around a repository-development workflow in which a Pull Request proposes a change, Code Review evaluates the change, Approvals record explicit review decisions, and Branch Protection enforces repository-level conditions before integration.

The four areas are related but represent different responsibilities:

- **Pull Request:** the workflow object that proposes changes from a source branch into a target branch.
- **Code Review:** the evaluation activity performed against the proposed change.
- **Approvals:** explicit review decisions that contribute to merge eligibility.
- **Branch Protection:** repository policy that prevents integration when required conditions are not satisfied.

The implementations use the same domain concepts from different engineering perspectives rather than translating one program mechanically into another.

## Domain Model

The central workflow is:

`Repository → Branches → Commits → Pull Requests → Reviews → Review Comments → Conversations → Status Checks → Branch Protection Policies → Approval Requirements → Merge Eligibility → Merge`

Each object has a distinct responsibility.

| Object | Responsibility |
|---|---|
| Repository | Owns branches, reviewers, and governance policy |
| Branch | Represents an independently evolving line of development |
| Commit | Represents an immutable change in repository history |
| Pull Request | Proposes integration of a source branch into a target branch |
| Review | Records a reviewer's decision about a change set |
| Review Comment | Records detailed review feedback |
| Conversation | Represents a discussion that may need resolution |
| Status Check | Represents automated validation associated with a Pull Request |
| Branch Protection | Defines repository-level conditions for integration |
| Approval Requirement | Defines how many eligible approvals are required |
| Merge Eligibility | Determines whether all conditions permit integration |
| Merge | Performs the final state transition into the target branch |

## Pull Request Lifecycle

A Pull Request connects two different branches.

The source branch contains the proposed changes. The target branch is the branch into which those changes may eventually be integrated.

A typical lifecycle is:

`Draft → Open → Reviewed → Eligible → Merged`

A Pull Request can also follow:

`Open → Closed → Reopened → Open`

A merged Pull Request is terminal in the implementations because merging represents a completed integration event.

The Python implementation explicitly models source and target branches, commits, draft status, base synchronization, review activity, status checks, conversations, eligibility, and merge strategies.

The JavaScript implementation adds event emission so state changes can be observed by other workflow components.

The C++ implementation concentrates on a deterministic merge-eligibility engine.

The Java implementation separates domain entities, policies, and the eligibility service.

The PostgreSQL implementation persists the workflow using foreign keys and database constraints.

## Draft Pull Requests

A draft Pull Request represents proposed work that is not yet ready for final integration.

The implementations prevent a draft from being merge eligible.

Publishing a draft changes its workflow state to open. This distinction is important because review activity can begin before a change is considered ready for integration.

Draft state is therefore part of Pull Request lifecycle management rather than an approval decision.

## Commits and Changesets

A Pull Request references commits from its source branch.

The source files validate commit identity and prevent duplicate commits from being inserted into a Pull Request.

The PostgreSQL model separates commits from Pull Requests through `pull_request_commits`. This allows one Pull Request to contain multiple commits while retaining repository-level commit identity.

The base commit recorded when a Pull Request is opened is used to detect target-branch movement.

If the target branch advances, merge eligibility is blocked until the Pull Request is synchronized.

This models the practical difference between:

- the change set that was reviewed,
- the current source branch,
- and the current target branch.

## Base-Branch Synchronization

Synchronization is important because review decisions describe a particular state of the proposed change.

When the target branch changes after a Pull Request is opened, the reviewed context can become stale.

The implementations therefore treat synchronization as a significant state operation.

The Python, C++, JavaScript, and Java models dismiss previous approvals when synchronization changes the effective base. The PostgreSQL model stores the base commit and uses it during eligibility evaluation.

This prevents an approval from being treated as automatically valid for an altered change context.

## Code Review

Code Review is the evaluation process applied to a proposed change.

It is distinct from the Pull Request itself.

The implementations model review states such as:

- `commented`
- `approved`
- `changes_requested`
- `dismissed`

A reviewer can identify defects without approving a change. A reviewer can also approve a change after evaluating it.

Review quality is represented through reviewer identity, reviewed commit identity, comments, and conversations.

The Python implementation stores review comments and conversations directly in the workflow model.

The JavaScript implementation associates review events with an event-driven workflow.

The C++ implementation focuses on review decisions as inputs to a deterministic governance engine.

The Java implementation uses explicit review records and immutable record types.

The PostgreSQL model separates reviews, review comments, and conversations into related tables so reporting can distinguish a review decision from detailed feedback.

## Review Mechanics

A review references a specific commit.

This matters because a review is meaningful only in relation to the code that was actually inspected.

The implementations also prevent self-approval.

Eligible reviewers are explicitly registered at repository level.

A reviewer's presence in the repository does not automatically mean that the reviewer can approve every Pull Request. The domain model first establishes repository reviewer eligibility.

A `changes_requested` review blocks merge eligibility until the review state is changed or replaced by a later valid review decision according to the workflow represented by the implementation.

## Review Comments and Conversations

Review comments describe specific findings.

Conversations represent discussions that may remain unresolved.

The implementations treat unresolved conversations as a separate merge condition.

This prevents an approval count from being considered sufficient when substantive review discussions remain unresolved.

A resolved conversation records the fact that the discussion has been addressed without changing the meaning of the original review comment.

The PostgreSQL schema stores the resolution timestamp separately from the creation timestamp, enabling workflow auditing.

## Approvals

An approval is a specific review decision.

Approval count is therefore different from the total number of reviews or comments.

For example, three reviewers can participate in review while only two provide approvals.

The governance models count distinct eligible approving reviewers.

The principal approval conditions are:

1. The reviewer must be eligible for the repository.
2. The reviewer cannot approve their own Pull Request.
3. The review must have an approved state.
4. The approval must remain valid for the current reviewed change set.
5. The number of valid approvals must satisfy the branch requirement.

The implementations deliberately avoid treating comments as approvals.

## Stale Approvals

An approval can become stale when the reviewed change context changes.

Base-branch synchronization is therefore treated as a state-changing event.

The Python, JavaScript, C++, and Java models dismiss existing approvals during synchronization.

The database model preserves review history and uses the Pull Request base commit when evaluating eligibility.

This distinction is important for testing because a workflow must not assume that an approval made against one repository state automatically approves every later state.

## Dismissed Approvals

Dismissal is different from rejection.

A dismissed approval remains part of review history but no longer contributes to the active approval requirement.

The Java implementation represents dismissal explicitly with `ReviewState.DISMISSED`.

The C++ implementation uses the same explicit state.

The Python and JavaScript implementations apply the state transition when base synchronization invalidates previous approvals.

This preserves historical information while preventing obsolete decisions from satisfying current governance requirements.

## Branch Protection

Branch Protection is repository-level enforcement.

It does not perform the review itself and does not create the Pull Request.

Instead, it establishes conditions that must be satisfied before integration.

The project models controls including:

- required approvals,
- required status checks,
- resolved conversations,
- direct-push restrictions,
- force-push restrictions,
- branch deletion restrictions,
- linear-history requirements,
- administrator bypass policy.

The distinction is:

`Pull Request proposes`

`Code Review evaluates`

`Approval records a decision`

`Branch Protection enforces policy`

## Required Status Checks

Status checks represent automated validation.

Typical checks in the implementations include:

- `unit-tests`
- `security-scan`
- `integration-tests`

A required check must exist and must be passing.

Missing checks and failing checks are treated differently from missing approvals, but both can block the same final merge decision.

This separates automated validation from human review.

The JavaScript implementation demonstrates asynchronous check completion with Promises and event-driven updates.

The PostgreSQL implementation stores checks independently and joins them against required policy checks during eligibility evaluation.

## Direct Push and Force Push Restrictions

Protected branches can restrict direct changes.

The model represents direct-push and force-push permissions as branch-level governance attributes and branch-protection policy attributes.

These controls are not equivalent to review approval.

A reviewer approving a Pull Request does not authorize an unrelated direct push to the protected branch.

Similarly, a Pull Request being eligible for merge does not imply that force-push operations should be permitted.

## Merge Eligibility

Merge eligibility is the intersection of independent conditions.

A simplified model is:

`Eligible = Open + Ready + Commits + Valid Reviews + Required Approvals + Passing Checks + Resolved Conversations + Current Base`

A failure in any required condition blocks integration.

The C++ implementation is specifically structured as a merge-eligibility engine and returns explicit failure reasons.

The Java implementation returns a `MergeDecision` containing eligibility and immutable reasons.

The Python implementation returns a Boolean result plus a list of blocking reasons.

The JavaScript implementation returns an object containing `eligible` and `failures`.

The PostgreSQL function returns a relational result containing eligibility and an explanation.

## Merge Strategies

The implementations represent three merge strategies:

| Strategy | Modelled behavior |
|---|---|
| Merge | Creates an integration commit representing the branch merge |
| Squash | Represents the Pull Request as one integrated commit |
| Rebase | Represents replayed change history before integration |

The examples use squash merging for the successful workflow.

The strategy is deliberately separated from eligibility. A Pull Request must first satisfy governance policy before the selected integration strategy is applied.

## Testing and Failure Handling

The project uses realistic failure conditions rather than treating successful execution as the only outcome.

Important failure cases include:

- missing source branch,
- missing target branch,
- identical source and target branches,
- empty Pull Request titles,
- invalid commits,
- duplicate commits,
- draft Pull Requests,
- self-approval,
- ineligible reviewers,
- requested changes,
- insufficient approvals,
- missing status checks,
- failing status checks,
- unresolved conversations,
- stale base branches,
- invalid state transitions,
- attempting to reopen a merged Pull Request,
- attempting to merge an ineligible Pull Request.

These cases are valuable testing targets because they validate the rules controlling state transitions rather than only testing ordinary data processing.

## Python Implementation

The Python program models the complete workflow with dataclasses and enumerations.

`RepositoryWorkflow` coordinates:

- Pull Request creation,
- commits,
- reviews,
- conversations,
- status checks,
- base synchronization,
- eligibility evaluation,
- merge,
- close,
- reopen.

`BranchProtection` stores governance policy.

`eligibility()` produces both a Boolean result and detailed blocking reasons.

The program also demonstrates expected failure handling after a Pull Request has been merged.

Python's dictionaries and sets provide efficient repository and reviewer lookup. The use of dataclasses keeps domain state explicit and reduces accidental ambiguity between entities.

## JavaScript Implementation

The JavaScript implementation uses a `Repository` class as the workflow boundary.

JavaScript-specific behavior is introduced through:

- `Map` for branches and Pull Requests,
- `Set` for eligible reviewers,
- `EventEmitter` for workflow events,
- Promises for asynchronous status-check processing,
- structured objects for stateful domain records.

Events such as review submission, conversation resolution, check updates, and merge completion provide an event-driven representation of repository activity.

The asynchronous check runner demonstrates that automated validation can complete independently before the final eligibility decision is made.

## C++17 Implementation

The C++ program is designed as a deterministic governance engine.

The central `MergeEligibilityEngine` evaluates:

- Pull Request state,
- draft state,
- commits,
- reviewer eligibility,
- approval count,
- requested changes,
- status checks,
- conversations,
- base-branch synchronization.

STL containers such as `std::map`, `std::set`, and `std::vector` represent repository state.

`std::any_of` is used for duplicate detection.

Exceptions represent invalid domain operations and blocked transitions.

The implementation keeps policy evaluation separate from the demonstration code, which makes the governance rules easier to test independently.

## Java 17 Implementation

The Java implementation emphasizes enterprise-style domain modeling.

Java records represent immutable value objects such as:

- `Commit`
- `StatusCheck`
- `Review`
- `ReviewComment`
- `BranchProtectionPolicy`
- `MergeDecision`

Mutable aggregate behavior is contained in `Repository`, `Branch`, and `PullRequest`.

The repository performs explicit validation before creating workflow objects.

The `evaluate()` method creates an immutable `MergeDecision`, separating policy evaluation from the final merge operation.

This structure reflects a service-oriented enterprise design where policy rules are explicit and domain state transitions are controlled.

## PostgreSQL Implementation

The PostgreSQL model provides persistent relational enforcement.

The schema separates:

- repositories,
- users,
- repository reviewers,
- branches,
- commits,
- Pull Requests,
- Pull Request commits,
- reviews,
- review comments,
- conversations,
- status checks,
- branch-protection policies,
- required status checks,
- merge events.

Foreign keys protect relationships between these entities.

Check constraints validate values such as commit length, approval counts, branch names, and comment content.

Unique constraints prevent duplicate repository branches, Pull Request numbers, commits, status-check definitions, and Pull Request commit ordering.

Indexes target common workflow queries such as:

- Pull Requests by target branch and state,
- reviews by Pull Request and review state,
- status checks by Pull Request,
- unresolved conversations,
- Pull Request commit ordering.

The `evaluate_merge_eligibility()` function performs database-side policy evaluation using CTEs.

This keeps merge eligibility reproducible from persisted repository state rather than relying only on application memory.

## Database-Level Validation

The review eligibility trigger verifies that a reviewer belongs to the repository's eligible reviewer set and prevents self-review.

The conversation trigger maintains `resolved_at` consistently with the resolution state.

The schema also uses foreign keys to prevent orphaned reviews, comments, checks, conversations, and merge events.

This demonstrates an important testing principle: validation should exist at the correct system boundary.

Application validation improves user feedback, while database constraints protect persisted integrity.

## Workflow State and Failure Boundaries

The principal state transitions are:

`Draft → Open`

`Open → Closed`

`Closed → Open`

`Open → Merged`

A merged Pull Request is not reopened in the implemented workflows.

The distinction between workflow state and policy state is intentional.

A Pull Request can be open while being ineligible for merge.

A Pull Request can have approvals while still being blocked by status checks.

A Pull Request can have passing checks while still being blocked by unresolved conversations.

This prevents one successful condition from being mistaken for overall eligibility.

## Security Considerations

The implementations apply several repository-governance controls:

- self-approval is rejected,
- reviewer eligibility is explicit,
- protected branches restrict direct modification,
- force-push restrictions are represented separately,
- branch deletion restrictions are represented separately,
- administrator bypass is an explicit policy setting,
- merge decisions require all configured mandatory conditions,
- invalid state transitions raise errors rather than silently changing state.

The database design uses foreign keys and constraints to protect integrity at persistence level.

Security policy is not represented as a single Boolean because repository governance consists of multiple independent controls.

## Performance Considerations

Repository lookup is modeled with hash-based or tree-based containers depending on language.

Python dictionaries and sets provide average constant-time lookup for repositories, Pull Requests, and reviewers.

JavaScript `Map` and `Set` provide efficient key-based lookup.

C++ uses `std::map` and `std::set`, providing logarithmic lookup with ordered storage.

Java uses `HashMap` and `HashSet` for common repository and reviewer lookup.

PostgreSQL indexes target the workflow queries most likely to be executed repeatedly.

Approval evaluation uses distinct reviewers so duplicate approval records from the same reviewer do not artificially increase the approval count.

## Design Trade-offs

The implementations intentionally favor explicit domain state over a minimal data structure.

This increases the amount of state that must be maintained, but it makes important governance distinctions testable.

The models also treat synchronization as a significant event rather than silently accepting stale approvals.

The database representation is more normalized than the in-memory implementations because relational integrity requires explicit relationships between entities.

The JavaScript implementation favors event-driven behavior, while C++ emphasizes deterministic policy evaluation and Java emphasizes explicit enterprise domain types.

These differences are deliberate rather than accidental language translations.

## Practical Testing Matrix

| Scenario | Expected result |
|---|---|
| Draft Pull Request | Merge blocked |
| No commits | Merge blocked |
| Self-approval | Operation rejected |
| Ineligible reviewer | Review rejected |
| One approval when two are required | Merge blocked |
| Requested changes present | Merge blocked |
| Required check missing | Merge blocked |
| Required check failing | Merge blocked |
| Unresolved conversation | Merge blocked |
| Target branch advanced | Merge blocked |
| Base synchronized and approvals refreshed | Eligibility can be reevaluated |
| All required conditions satisfied | Merge permitted |
| Merged Pull Request reopened | Operation rejected |
| Protected branch direct modification | Restricted by policy |
| Duplicate commit | Operation rejected |

## Implementation Comparison

| Capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Pull Request lifecycle | Yes | Yes | Yes | Yes | Yes |
| Draft state | Yes | Yes | Yes | Yes | Yes |
| Commit tracking | Yes | Yes | Yes | Yes | Yes |
| Review states | Yes | Yes | Yes | Yes | Yes |
| Approval evaluation | Yes | Yes | Yes | Yes | Yes |
| Status checks | Yes | Yes | Yes | Yes | Yes |
| Conversations | Yes | Yes | Yes | Yes | Yes |
| Base synchronization | Yes | Yes | Yes | Yes | Persisted state |
| Merge strategies | Yes | Yes | Yes | Yes | Yes |
| Branch protection | Yes | Yes | Yes | Yes | Yes |
| Event-driven workflow | No | Yes | No | No | No |
| Explicit policy engine | Yes | Yes | Yes | Yes | Yes |
| Relational constraints | No | No | No | No | Yes |
| Database triggers | No | No | No | No | Yes |
| Transactional merge record | No | No | No | No | Yes |

## Key Distinctions

A Pull Request is not an approval.

A review is not automatically an approval.

An approval is not the same as merge eligibility.

A passing status check is not equivalent to reviewer approval.

Branch Protection does not perform Code Review.

Branch Protection defines conditions that the integration operation must satisfy.

Merge eligibility is the point at which these independent conditions are evaluated together.

The project therefore models repository governance as a layered testing problem:

`Proposed Change`
→ `Review`
→ `Approval Decisions`
→ `Automated Checks`
→ `Repository Policy`
→ `Eligibility Evaluation`
→ `Integration`

This separation makes failures attributable to the correct mechanism and allows each layer to be tested independently.
