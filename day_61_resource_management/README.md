# Resource Management for Project Repository Governance

## Scope

This project models project resource management through a repository-development workflow. The central problem is not only how many people or automated resources are available, but how those resources interact with Pull Requests, Code Review, Approvals, Branch Protection, validation checks, and final merge eligibility.

The four repository-governance areas remain distinct:

| Area | Primary responsibility |
|---|---|
| Pull Requests | Propose and manage a changeset from a source branch toward a target branch |
| Code Review | Evaluate the technical changes and manage review discussions |
| Approvals | Record formal reviewer decisions that can satisfy review requirements |
| Branch Protection | Enforce repository-level conditions before a merge is permitted |

The project-resource perspective adds a separate operational layer:

`Resources → Allocation → Work Capacity → Review Capacity → Validation → Governance → Merge Eligibility`

A resource allocation does not constitute approval. A review does not itself change branch protection. A passing status check is not a human approval. Branch protection combines these independent signals when deciding whether a Pull Request may merge.

## Domain Model

The implemented relationship is:

`Repository`
→ `Branches`
→ `Commits`
→ `Pull Requests`
→ `Reviews`
→ `Review Comments`
→ `Status Checks`
→ `Branch Protection`
→ `Approval Requirements`
→ `Merge Eligibility`
→ `Merge`

Resource planning operates beside this workflow:

`Resources`
→ `Project Allocations`
→ `Capacity`
→ `Utilization`
→ `Cost`

The source branch contains proposed changes. The target branch represents the protected destination. Commits identify the changeset. Reviews evaluate those changes. Approval records capture formal review decisions. Status checks provide automated validation. Branch protection defines repository-level constraints. Merge eligibility evaluates all applicable conditions.

## Pull Request Lifecycle

A Pull Request begins with a source branch containing commits that are not yet part of the target branch. The Python, JavaScript, C++17, Java 17, and PostgreSQL implementations represent source and target branches explicitly.

A typical lifecycle is:

`Draft → Open → Review → Validation → Eligible → Merged`

Alternative terminal states include:

`Open → Closed`

and:

`Closed → Reopened → Open`

A Draft Pull Request represents proposed work that is not ready for final integration. The implementations prevent a draft from being considered mergeable until it becomes an active Pull Request.

Base-branch synchronization is also modeled. If the target branch advances after a review, the previous approval can become stale because the reviewed state no longer represents the current integration state. The Python and JavaScript models explicitly track synchronization and prevent stale approvals from satisfying the merge condition.

Merge strategies are represented as `merge`, `squash`, and `rebase`. The implementations validate the selected strategy rather than treating all merge operations as identical.

Closing a Pull Request is different from merging it. A closed Pull Request does not enter the merged state. The Python model also supports reopening a closed Pull Request.

## Code Review

Code Review is the technical evaluation of the proposed changes.

The model separates a review from individual review comments. A review has a state such as `commented`, `changes_requested`, `approved`, or `dismissed`. Review comments identify a file, line, message, and resolution state.

A review discussion may therefore follow:

`Review → Comment → Change → Resolution → New Review Decision`

The implementations intentionally avoid treating every comment as an approval decision. A reviewer may identify a defect without approving the Pull Request. A discussion can be resolved independently of the review state.

Review quality is represented through several controls:

- Reviewers cannot approve their own Pull Requests.
- Review decisions reference the commit that was reviewed.
- Comments can remain unresolved.
- Merge eligibility can require all review conversations to be resolved.
- A changed base can invalidate an otherwise valid review decision.
- Required automated checks remain separate from human review.

The C++ implementation uses explicit structures for reviews, comments, status checks, and Pull Requests. The Java implementation uses immutable records for domain values and a service class for governance decisions. The JavaScript implementation uses event emission to model review and validation events.

## Approval Semantics

Approval is a formal review decision, not simply evidence that somebody examined a Pull Request.

The implementations count approvals only when the approval corresponds to the current source commit and the base branch remains synchronized. This models a stale-approval condition.

For example:

`Commit A → Approval`

followed by:

`Commit B → source branch changes`

means the approval for Commit A cannot automatically satisfy a policy requiring approval of Commit B.

Dismissed or non-approval review states do not count toward the required approval threshold.

The model also prevents self-approval. Reviewer eligibility is represented by requiring a reviewer identity distinct from the Pull Request author. The PostgreSQL implementation enforces this rule through a database trigger, while the application implementations enforce it during review submission.

Approval requirements are repository policy rather than resource allocation rules. Assigning four hours to a reviewer does not produce an approval. The reviewer must independently evaluate the changes and submit an appropriate review decision.

## Branch Protection

Branch Protection operates at the repository or target-branch governance layer.

The model supports:

- Required approvals
- Required status checks
- Direct-push restrictions
- Force-push restrictions
- Branch-deletion restrictions
- Required conversation resolution
- Linear-history requirements
- Administrator bypass policy representation

A protected branch can require both human and automated conditions.

For example:

`1 approval`
+
`unit-tests = pass`
+
`security-scan = pass`
+
`no unresolved conversations`
+
`current base`
=
`merge eligible`

If one condition fails, merge eligibility fails even if the other conditions are satisfied.

Direct-push and force-push controls are represented as policy attributes. These controls concern repository governance and are deliberately separate from Pull Request review behavior.

Administrator bypass is represented as a policy capability in the PostgreSQL model. A bypass mechanism should be treated as an exceptional governance path rather than a replacement for normal review requirements.

## Resource Management Model

Project resources include human and automated capacity.

The implementations model three resource categories:

| Resource | Purpose |
|---|---|
| Engineer | Implements and updates the proposed changes |
| Reviewer | Evaluates the changes and supplies review decisions |
| Automation | Runs validation and security checks |

Each resource has:

- Capacity in hours
- Current allocation
- Hourly cost
- Utilization
- Active/inactive status where represented by PostgreSQL

The basic capacity rule is:

`allocated_hours <= capacity_hours`

An allocation exceeding available capacity is rejected.

Resource cost is calculated as:

`allocated_hours × hourly_cost`

The project therefore distinguishes resource availability from governance state.

A Pull Request may be merge-eligible while the project is poorly staffed. Conversely, sufficient resource capacity does not make a Pull Request eligible for merging.

## Python Implementation

The Python file provides a complete in-memory repository and resource-management simulation.

`ResourceManager` tracks resource definitions, allocations, remaining capacity, utilization, and project cost. The class rejects unknown resources, non-positive allocations, and capacity violations.

`Repository` models branches and Pull Requests. It supports branch creation, commits, Pull Request creation, reviews, status checks, base synchronization, reopening, closing, merge eligibility, and merge operations.

The `BranchProtection` dataclass stores repository policy. Merge eligibility is evaluated as a collection of independent conditions rather than one Boolean shortcut.

The Python model also demonstrates a review failure followed by resolution. A review initially requests changes, a discussion is resolved, an approval is submitted against the latest commit, required checks pass, and the Pull Request becomes mergeable.

The final example deliberately attempts to over-allocate an engineer. The resulting exception demonstrates capacity enforcement.

## JavaScript Implementation

The JavaScript implementation uses Node.js standard-library features and focuses on event-driven governance.

`ResourcePool` manages resource capacity and calculates utilization and cost.

`Repository` extends `EventEmitter`. Important workflow events include:

- Pull Request opened
- Review submitted
- Status check completed
- Pull Request merged

This event model is useful when repository governance is integrated with operational systems such as notifications, dashboards, audit pipelines, or resource monitoring.

The status checks are executed asynchronously with Promises. The checks are then incorporated into merge eligibility.

JavaScript `Map` objects represent branches, Pull Requests, resources, allocations, and status checks. `Set` is used for required checks and distinct approvals.

The implementation also distinguishes stale base state from current base state. A Pull Request cannot satisfy the normal merge policy while its base branch is marked stale.

## C++17 Implementation

The C++ program treats repository governance as a deterministic policy engine.

`ResourceLedger` owns resource definitions and enforces allocation limits.

`GovernanceEngine` owns:

- Branches
- Pull Requests
- Reviews
- Comments
- Status checks
- Branch protection

The C++ implementation uses STL containers such as `std::map`, `std::set`, and `std::vector`. It performs explicit validation and throws exceptions for invalid state transitions.

Merge eligibility returns both a Boolean result and a collection of failure reasons. This is useful for operational diagnostics because a blocked merge can expose all failed conditions instead of only the first failure.

The program uses a concrete case where a reviewer first requests changes. The review conversation is resolved, an approval is submitted, required checks pass, and a squash merge is performed.

Resource allocation and repository governance remain separate subsystems, which reflects the distinction between project capacity management and source-control enforcement.

## Java 17 Implementation

The Java implementation uses explicit enterprise-oriented domain types.

Records represent immutable values such as:

- `Resource`
- `Commit`
- `Review`
- `ReviewComment`
- `StatusCheck`
- `MergeDecision`

`ResourceAllocationService` manages resource capacity and cost.

`RepositoryGovernanceService` owns branch and Pull Request policy evaluation. It produces a `MergeDecision` containing both eligibility and detailed failure reasons.

Custom exceptions distinguish resource-capacity failures from merge-policy failures.

The service model separates domain state from policy evaluation. This structure is appropriate for enterprise applications where repository governance may be exposed through service APIs, scheduled processes, audit systems, or administrative interfaces.

Java Streams are used for approval collection, status validation, and utilization reporting. Immutable records reduce accidental modification of important domain values.

## PostgreSQL Implementation

The PostgreSQL implementation models the same domain relationally.

Core tables include:

| Table | Purpose |
|---|---|
| `repositories` | Repository identity and default branch |
| `resources` | Available project resources and their capacities |
| `project_allocations` | Resource usage against a repository |
| `branches` | Repository branch state |
| `commits` | Commit history |
| `pull_requests` | Proposed changes and workflow state |
| `pull_request_commits` | Changesets associated with Pull Requests |
| `reviewers` | Eligible reviewer identities |
| `reviews` | Formal review decisions |
| `review_comments` | Line-level review discussions |
| `status_checks` | Automated validation results |
| `branch_protection_policies` | Protected-branch rules |
| `required_status_checks` | Checks required by a policy |
| `approval_requirements` | Explicit approval requirements |
| `merges` | Completed merge operations |

Foreign keys preserve relationships between repositories, branches, Pull Requests, reviews, and commits.

Check constraints reject invalid capacities, costs, sequence numbers, and other malformed values.

The resource-capacity trigger calculates existing allocations before accepting a new allocation. This moves an important business rule into the database so it is not dependent solely on application-level validation.

The self-approval trigger prevents an author from creating an approval for the author's own Pull Request.

The `calculate_merge_eligibility` function evaluates:

- Pull Request state
- Draft status
- Required approvals
- Current reviewed commit
- Required status checks
- Unresolved comments
- Base synchronization

The function returns both eligibility and diagnostic reasons.

The `pull_request_governance_report` view exposes these decisions in a reporting-oriented form.

The transaction at the end demonstrates that merge eligibility and the state transition to `merged` can be performed as one database operation.

## Failure Conditions

The implementations intentionally model failure rather than silently accepting invalid state.

| Failure | Result |
|---|---|
| Unknown resource | Allocation rejected |
| Negative or zero allocation | Validation failure |
| Allocation exceeds capacity | Resource-capacity failure |
| Unknown branch | Repository operation rejected |
| Empty changeset | Pull Request creation rejected |
| Self-approval | Review rejected |
| Missing approval | Merge blocked |
| Failed required check | Merge blocked |
| Unresolved discussion | Merge blocked when policy requires resolution |
| Stale base | Merge blocked |
| Draft Pull Request | Merge blocked |
| Closed Pull Request | Merge blocked |
| Invalid merge strategy | Merge rejected |

These failures are different types of state violations and are not collapsed into one generic condition.

## Resource Capacity and Governance Interaction

Resource management affects the ability to perform work, while repository governance determines whether completed work may be integrated.

A realistic project can therefore have this state:

`Engineer capacity available`
→ `Implementation completed`
→ `Pull Request opened`
→ `Reviewer allocated`
→ `Review completed`
→ `Approval recorded`
→ `CI resources execute`
→ `Status checks pass`
→ `Branch protection evaluated`
→ `Merge`

The sequence does not imply that one stage automatically satisfies another.

Resource allocation is an operational commitment. Review is a technical evaluation. Approval is a formal decision. Status checks are automated evidence. Branch protection is enforcement.

## Performance Considerations

The in-memory implementations use maps and sets for direct lookup of resources, Pull Requests, branches, reviewers, and required checks.

Let:

- `R` = number of reviews
- `C` = number of review comments
- `S` = number of required status checks

A merge-eligibility evaluation is approximately `O(R + C + S)` for the modeled workflow.

PostgreSQL indexes support common access paths:

- Pull Requests by repository and state
- Reviews by Pull Request and state
- Comments by review and resolution
- Status checks by Pull Request and check name
- Resource allocations by repository and resource

The indexes are intentionally tied to actual filtering and join patterns rather than added to every column.

For large repositories, historical review data and status-check records would normally require retention and indexing strategies appropriate to query volume.

## Security Considerations

The model treats repository governance as an authorization boundary.

Important controls include:

- Protected target branches
- No direct pushes to protected branches
- No force pushes where prohibited
- No self-approval
- Required independent reviews
- Required automated checks
- Resolved review discussions
- Explicit merge strategies
- Audit records for completed merges
- Database constraints for critical business rules

Resource data can also represent operationally sensitive information because capacity and cost expose staffing and project-planning details. Access to allocation records should therefore follow the project's authorization model.

The implementations do not treat application validation as the only security boundary. The PostgreSQL model places selected invariants directly in database constraints and triggers.

## Design Distinctions

The four governance mechanisms answer different questions.

| Mechanism | Question answered |
|---|---|
| Pull Request | What changes are being proposed, from where, and toward which branch? |
| Code Review | What is technically wrong, risky, unclear, or acceptable about those changes? |
| Approval | Has an eligible reviewer formally accepted the current reviewed state? |
| Branch Protection | Are all repository-level conditions satisfied before integration? |

Resource management answers a separate operational question:

`Do the people and automated systems have sufficient capacity to perform the work and validation?`

Keeping these questions separate prevents resource allocation from being confused with technical authorization or repository policy enforcement.

## Practical Workflow

A project using this model can organize work as follows:

`Resource Planning`
→ allocate engineering and review capacity

`Implementation`
→ create a source branch and commits

`Pull Request`
→ propose the changes against the protected target branch

`Code Review`
→ inspect implementation and resolve discussions

`Approval`
→ eligible reviewers approve the current reviewed commit

`Validation`
→ required automated checks complete successfully

`Branch Protection`
→ repository policy evaluates all required conditions

`Merge`
→ approved merge strategy updates the target branch

This workflow preserves a clear boundary between project resource management and source-control governance while allowing the two systems to cooperate operationally.
