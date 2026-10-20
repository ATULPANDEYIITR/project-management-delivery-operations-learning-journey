# Cost and Resource Review: Repository Governance

This artifact models the relationship between Pull Requests, Code Review, Approvals, and Branch Protection while treating engineering review capacity as a measurable resource.

The four mechanisms have different responsibilities:

| Area | Primary responsibility | Main decision |
|---|---|---|
| Pull Request | Proposes and tracks a change between branches | What change is being proposed? |
| Code Review | Evaluates the proposed implementation | What technical feedback or concerns exist? |
| Approvals | Records formal reviewer decisions | Has an eligible reviewer accepted the change? |
| Branch Protection | Enforces repository-level merge conditions | Is the repository willing to permit the merge? |

A useful governance flow is:

`Source branch → Pull Request → Code Review → Approval decisions → Branch Protection gates → Merge`

Review effort is a related resource concern rather than another governance mechanism. Changed-file counts and review estimates provide a practical way to identify large review workloads without changing the meaning of approvals or protection rules.

## Pull Request lifecycle and mechanics

A Pull Request connects a source branch containing proposed work to a target branch that will receive the change.

The Python model represents a Pull Request with:

- source and target branches
- commits
- review records
- status checks
- unresolved conversations
- synchronization state
- merge-conflict state
- draft, open, closed, and merged states

A draft Pull Request can be used while implementation is still being prepared. Opening the draft changes it into an active review object.

The lifecycle modeled by the implementation is:

`draft → open → closed`

or:

`draft → open → merged`

A closed Pull Request can be reopened. A merged Pull Request is treated as final.

### Source and target branches

The source branch contains proposed changes. The target branch is the branch into which the change is eventually merged.

The implementations reject a Pull Request whose source and target branches are identical. This prevents a meaningless merge relationship.

The SQL model stores both branches as foreign keys rather than treating branch names as free text inside every Pull Request record.

### Changesets and commits

Commits form the concrete changeset associated with a Pull Request.

The Python and C++ implementations aggregate changed-file counts from commits. This creates a simple resource-review signal:

`estimated review effort = max(10 minutes, changed files × 4 minutes)`

This is deliberately an estimate rather than a measurement of actual reviewer productivity. Large generated files, complex algorithms, security-sensitive changes, and configuration changes can make a file-count-only estimate inaccurate.

The SQL implementation keeps commits separate from Pull Requests and uses `pull_request_commit` as a relationship table. This permits one commit to be represented as part of a Pull Request without duplicating commit metadata.

### Base-branch synchronization and conflicts

A Pull Request may become stale when its target branch changes.

The implementations track:

- whether the Pull Request is synchronized with the base branch
- whether merge conflicts exist
- the revision at which reviews and status checks were produced

A base-branch update can invalidate previously evaluated conditions. Synchronization does not automatically mean that approvals or checks should remain valid.

This distinction is important:

`Synchronization` describes the relationship between the proposed change and the current target branch.

`Approval validity` describes whether a reviewer decision still applies to the current revision.

They are related but not interchangeable.

### Merge strategies

The examples support three common conceptual strategies:

| Strategy | Meaning |
|---|---|
| Merge commit | Preserves a separate merge commit joining the histories |
| Squash | Combines Pull Request changes into a single target-branch commit |
| Rebase | Replays commits onto another base |

The sample protected branch allows squash merging only. A repository can choose a different policy based on its history requirements.

## Code Review

Code Review is the evaluation activity performed on the proposed changes.

It is distinct from the Pull Request itself. The Pull Request provides the workflow container; Code Review records technical evaluation within that workflow.

The implementations model review states:

- `commented`
- `approved`
- `changes_requested`
- `dismissed`

A review can contain inline-comment counts and textual feedback.

### Inline comments

The SQL model stores review comments separately from the review decision. Each comment identifies:

- reviewer decision
- file path
- line number
- comment body
- resolution state
- creation time

This separation reflects a practical distinction between a reviewer’s overall decision and individual observations about implementation details.

For example, a reviewer may identify an insecure permission check on one line while still withholding approval for the entire Pull Request.

### Review state

A reviewer can move from a requested-changes decision to an approval after the issue is corrected.

The implementations use the latest review from each reviewer for policy evaluation. Historical review records remain stored for auditability.

Conceptually:

`review history → latest reviewer decision → current policy evaluation`

This avoids counting every historical approval as an independent current approval.

### Review discussions and resolution

Review comments can create unresolved conversations.

The branch-protection policy may require all conversations to be resolved before merging. This condition belongs to the merge gate rather than to the meaning of an approval.

A reviewer can approve a change while a separate conversation remains unresolved. The repository policy can still prevent merging until that conversation is addressed.

### Reviewer responsibilities

A reviewer should evaluate the technical scope appropriate to the change.

Relevant review criteria include:

- correctness
- security implications
- data integrity
- failure handling
- maintainability
- test coverage
- resource impact
- unintended behavior
- consistency with repository policy

Review quality is not equivalent to the number of comments. A review with many low-value comments can consume more engineering capacity without providing proportional risk reduction.

The implementations therefore keep review comments and approval decisions as separate concepts.

## Approvals

An approval is a formal reviewer decision.

It is narrower than Code Review as a whole. A reviewer may comment without approving, request changes without approving, or approve after evaluating the current revision.

### Reviewer eligibility

The examples define eligible reviewers through repository membership and roles.

The SQL implementation treats members with `write`, `maintain`, or `admin` roles as eligible for the sample approval policy.

This is a simplified repository policy. Real organizations may use teams, ownership rules, required reviewer groups, separation-of-duties controls, or different eligibility rules.

### Required approvals

The protected `main` branch requires two approvals.

The merge engine counts the latest decision for each eligible reviewer rather than counting every approval ever submitted.

For example:

`Alice approved`
`Bob requested changes`
`Bob later approved`

The current decisions are:

`Alice → approved`
`Bob → approved`

Therefore two current approvals exist.

### Stale approvals

The examples use revision numbers to demonstrate stale approval handling.

Suppose a Pull Request is reviewed at revision 4:

`PR revision = 4`
`Alice approval = revision 4`

A later source or base change produces:

`PR revision = 5`
`Alice approval = revision 4`

With stale-approval dismissal enabled, Alice's previous approval is not sufficient for revision 5.

The purpose is to prevent an approval from being interpreted as acceptance of code the reviewer never evaluated.

### Dismissed approvals

A dismissed review is not counted as a current approval.

Dismissal is represented as a review state rather than deleting the historical record. This preserves an audit trail while preventing the dismissed decision from satisfying the merge requirement.

### Effect on merge eligibility

Approval is necessary but not necessarily sufficient.

The following can all be true at once:

- two reviewers have approved
- a required status check failed
- a review conversation remains unresolved
- the Pull Request has merge conflicts

In that situation, the Pull Request remains ineligible.

This demonstrates the distinction between reviewer decisions and repository enforcement.

## Branch Protection

Branch Protection is the repository-level enforcement mechanism.

It does not perform the Code Review itself. It does not create reviewer opinions. It defines conditions that must be satisfied before a protected branch accepts a merge.

The SQL model stores branch protection independently from Pull Request records.

### Protected branches

The sample repository protects `main`.

The protection policy requires:

| Policy | Sample value |
|---|---|
| Required approvals | 2 |
| Required checks | `unit-tests`, `security-scan` |
| Stale approval dismissal | Enabled |
| Conversation resolution | Required |
| Direct pushes | Restricted |
| Force pushes | Disabled |
| Branch deletion | Disabled |
| Linear history | Required |
| Allowed merge strategy | Squash |

These conditions belong to the branch rather than to one specific Pull Request.

### Required status checks

Status checks provide automated evidence that a change satisfies defined technical gates.

The examples require:

- `unit-tests`
- `security-scan`

A missing check and a failed check are different failure conditions.

A check can also be stale if it was executed against an earlier Pull Request revision.

The SQL function therefore evaluates:

`check exists → check passed → check revision is current`

### Direct-push restrictions

A Pull Request workflow loses its governance value if contributors can bypass it by directly pushing to the protected branch.

The policy therefore records `restrict_direct_push = true`.

This is a repository governance rule rather than a review decision.

### Force-push restrictions

Force-push restrictions protect branch history from destructive rewriting.

The example disables force pushes on `main`. This is especially relevant where auditability and stable commit ancestry matter.

### Branch deletion restrictions

The protected branch cannot be deleted under the sample policy.

This prevents accidental removal of a repository's primary integration point.

### Conversation requirements

The policy can require unresolved review conversations to reach zero before merge.

This is an enforcement rule:

`unresolved conversations = 0`

It does not mean that every comment must result in a code change. A discussion can be resolved after explanation, correction, or an explicit agreement that no code modification is required.

### Linear history

The sample policy requires linear history and permits squash merging.

The exact relationship between linear-history requirements and permitted merge strategies depends on repository configuration. The governance model therefore stores the allowed strategies explicitly rather than assuming that one strategy is universally correct.

### Administrator behavior and bypass

Administrative authority and bypass mechanisms are security-sensitive governance decisions.

The example intentionally models the policy boundary without assuming that every administrator should automatically bypass every protection rule.

A production governance implementation should explicitly define:

- who may bypass protection
- which protections can be bypassed
- whether bypasses require justification
- whether bypass events are audited
- whether emergency changes receive retrospective review

A bypass should be treated as an exceptional governance path, not as another form of approval.

## Python implementation

The Python program models repository workflow behavior directly through domain classes.

`PullRequest` owns the state of a proposed change. `Commit`, `Review`, `StatusCheck`, and `BranchProtection` represent supporting domain objects.

`RepositoryWorkflow.evaluate_merge()` performs the central policy evaluation.

It checks:

- Pull Request state
- source and target branch validity
- presence of commits
- base-branch synchronization
- merge conflicts
- merge strategy
- reviewer eligibility
- latest review decisions
- stale approvals
- required status checks
- unresolved conversations

The program also calculates estimated review effort from changed-file counts.

Python dictionaries are used for latest-review selection because each reviewer needs one effective current decision. Sets provide efficient membership checks for eligible reviewers and required checks.

The implementation raises explicit exceptions for invalid transitions such as adding commits after merge.

## JavaScript implementation

The JavaScript implementation uses an event-driven model based on Node.js `EventEmitter`.

Repository events include:

- review requests
- review submissions
- status-check updates
- conversation creation
- conversation resolution
- base-branch updates
- synchronization
- state transitions

This perspective is different from the Python workflow model. Instead of primarily demonstrating synchronous domain operations, the JavaScript program exposes repository activity as observable events.

The `GovernancePolicy` object evaluates the current Pull Request state after those events occur.

The JavaScript implementation also calculates review-resource demand from changed-file counts and demonstrates stale status checks through revision tracking.

## C++ implementation

The C++ program implements a merge-eligibility engine.

`PullRequest` owns repository-change state, while `MergeEligibilityEngine` evaluates branch-protection policy.

The engine returns a structured `MergeEvaluation` rather than immediately merging or throwing away the individual reasons.

This makes the engine useful for governance tooling because callers can display every blocking condition.

The C++ model also uses:

- `std::vector` for commits and review history
- `std::map` for current status checks
- `std::set` for eligible reviewers and required checks
- `std::optional`-compatible domain design through explicit state validation
- enum classes for controlled state values
- exceptions for invalid domain transitions

The implementation is compiled as a C++17 program.

## Java implementation

The Java implementation models repository governance as an enterprise domain.

Records are used for immutable value-oriented objects such as:

- `Commit`
- `Review`
- `StatusCheck`
- `BranchProtectionPolicy`
- `GovernanceDecision`

The `PullRequest` class controls state transitions, while `MergeEligibilityService` evaluates merge policy.

The design makes a deliberate separation between:

`domain state → policy → decision`

This allows a policy to be evaluated without embedding every governance rule directly into the Pull Request entity.

Java collections are used for immutable policy sets and review histories. The stream API calculates aggregate changed-file counts for the resource-review estimate.

## PostgreSQL implementation

The PostgreSQL model represents the repository as relational data.

The principal relationships are:

`repository → branches → branch protection`

and:

`repository → Pull Requests → commits/reviews/status checks`

A Pull Request and its commits use the `pull_request_commit` relationship table.

Reviews and review comments are separate because an overall reviewer decision is not equivalent to an individual inline discussion.

Branch protection is separated from Pull Requests so that the same protected branch policy can govern many future Pull Requests.

The database enforces integrity through:

- primary keys
- foreign keys
- unique constraints
- check constraints
- indexes
- enumerated types
- a revision trigger
- a merge-eligibility function

The `merge_eligibility()` function centralizes database-level evaluation of:

- Pull Request state
- commits
- synchronization
- conflicts
- permitted merge strategies
- eligible approvals
- stale approvals
- requested changes
- required checks
- stale checks
- unresolved conversations

This permits reporting and operational tooling to evaluate governance conditions without reconstructing the policy in application code.

## Cost and resource review

Repository governance consumes engineering resources.

The implementations make that resource dimension visible without confusing it with the four governance mechanisms.

The principal measurable signal is changed-file volume:

`commits → changed files → estimated review minutes`

This is useful for identifying potentially expensive reviews, but it has important limitations.

A ten-file security-critical change may require substantially more review effort than a fifty-file mechanical rename. Generated files can also distort file-count estimates.

Therefore, the estimate should be treated as a capacity-planning signal rather than an approval rule.

Useful operational interpretations include:

| Signal | Possible implication |
|---|---|
| Very large changeset | Consider smaller reviewable units |
| High review-minute estimate | Reviewer capacity may become a bottleneck |
| Repeated stale approvals | Base branch changes are causing review churn |
| Many unresolved conversations | Review workflow is not reaching closure |
| Repeated failed checks | Engineering time is being spent before merge eligibility can be reached |
| High approval latency | Reviewer availability may be constraining delivery |

These signals support cost and resource review while preserving the distinct responsibilities of Pull Requests, Code Review, Approvals, and Branch Protection.

## Failure modes represented by the artifacts

The implementations deliberately model common governance failures:

- empty Pull Requests
- identical source and target branches
- invalid commit identifiers
- invalid state transitions
- no eligible approvals
- reviewer requests changes
- stale approvals
- missing status checks
- failed status checks
- stale status checks
- unresolved review conversations
- merge conflicts
- unsynchronized base branches
- prohibited merge strategies
- attempts to modify merged Pull Requests

A particularly important failure mode is treating approval as equivalent to merge permission.

The implemented decision path is intentionally:

`review decision → approval evaluation → branch policy evaluation → merge eligibility`

rather than:

`approval → automatic merge`

## Security and governance considerations

Repository governance is an access-control problem as well as a collaboration workflow.

Important controls include:

- restricting direct pushes to protected branches
- preventing unauthorized force pushes
- limiting branch deletion
- requiring eligible reviewers
- invalidating stale approvals when appropriate
- requiring security status checks
- retaining historical review decisions
- auditing bypasses
- separating reviewer authority from repository administration where organizational policy requires it

The examples do not treat administrator access as an implicit justification for bypassing controls. A production implementation should make privileged bypass behavior explicit and auditable.

## Performance considerations

The main application-level evaluations use maps and sets to avoid repeatedly scanning large collections for membership checks.

For a Pull Request with `R` review records, `C` required status checks, and `E` eligible reviewers, the core evaluation is approximately:

`O(R + C + E)`

The SQL implementation uses indexes on:

- Pull Request target branch and state
- Pull Request reviews
- status checks
- Pull Request commit relationships

These indexes support the common governance queries without indexing every column indiscriminately.

The database function performs latest-review selection with PostgreSQL's `DISTINCT ON`, which is well suited to selecting the most recent review per reviewer when paired with an appropriate ordering strategy.

## Relationship between the four mechanisms

The complete model can be represented as:

`Pull Request`
`    ↓`
`proposes a source-to-target change`
`    ↓`
`Code Review`
`    ↓`
`evaluates implementation and records discussions`
`    ↓`
`Approvals`
`    ↓`
`records eligible reviewer decisions`
`    ↓`
`Branch Protection`
`    ↓`
`enforces repository-level merge conditions`
`    ↓`
`Merge`

A Pull Request is therefore the workflow object, Code Review is the evaluation process, Approval is a formal review decision, and Branch Protection is the enforcement layer.

Keeping these responsibilities separate makes repository governance easier to reason about, audit, implement, and evaluate under changing resource and risk constraints.
