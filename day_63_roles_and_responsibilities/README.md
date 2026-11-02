# Repository Roles and Responsibilities

## Scope

This project models responsibility definition inside a repository-development governance workflow. The five implementations use the same domain boundaries while emphasizing different engineering concerns:

| Area | Primary responsibility |
|---|---|
| Pull Request | Propose and manage a change between source and target branches |
| Code Review | Evaluate the technical and operational quality of proposed changes |
| Approvals | Record explicit reviewer decisions against a reviewed commit |
| Branch Protection | Enforce repository-level conditions before protected-branch changes are accepted |
| Roles and Responsibilities | Define which participants may perform governance actions |

The central relationship is:

Repository → Branches → Commits → Pull Requests → Reviews → Comments and Conversations → Status Checks → Branch Protection → Merge Eligibility → Merge

A Pull Request is the change-management object. Code Review is the evaluation activity. An approval is a review decision. Branch Protection is repository policy enforcement. Roles determine which people may perform particular governance actions.

## Responsibility Model

The implementations use four representative roles:

| Role | Primary responsibility | Governance authority |
|---|---|---|
| Developer | Implement changes and maintain the source branch | Cannot approve their own Pull Request |
| Reviewer | Inspect implementation, identify defects, discuss changes, and approve or request changes | May approve when repository membership permits |
| Maintainer | Resolve repository-level governance decisions and perform controlled merges | May review and approve |
| Administrator | Manage repository governance and exceptional administrative operations | Highest repository policy authority |

The model deliberately separates implementation responsibility from approval responsibility. A developer can create commits and propose a Pull Request without becoming an eligible approver for that same Pull Request.

## Pull Request Lifecycle

A Pull Request connects a source branch containing proposed changes to a target branch that receives those changes after governance requirements are satisfied.

Typical state progression is:

`draft → open → review → checks → eligible → merged`

A Pull Request can also move from `open` to `closed` without being merged. A closed Pull Request may later be reopened when repository policy and platform behavior permit it.

The implementations represent the important state conditions rather than treating a Pull Request as a simple message.

### Source and Target Branches

The source branch contains the proposed commits. The target branch identifies where those changes are intended to land.

The example uses:

`feature/idempotency → main`

The `main` branch is protected. The feature branch remains the development area.

### Commits and Changesets

A Pull Request is associated with commits rather than with an abstract collection of untracked edits. Reviews reference a particular commit.

This matters for approval validity. The example treats approvals as current-head decisions. When a new commit is pushed after approval, earlier approvals no longer satisfy the required current-head approval condition.

That rule models an important governance distinction:

`approved old revision ≠ approved current revision`

### Draft Pull Requests

A draft Pull Request represents work that is not yet ready for normal merge processing. The governance engines explicitly prevent a draft from being merge eligible.

This prevents an incomplete change from satisfying ordinary merge conditions merely because it happens to contain enough approvals and passing checks.

### Synchronization

The model tracks how far the source branch is behind the base branch through `base_behind_by`.

When linear-history or synchronization policy is enabled, a non-zero value blocks eligibility. This separates branch synchronization from code review. A Pull Request can be technically approved while still failing a repository synchronization requirement.

### Conflicts

`mergeable = false` represents an unresolved merge conflict. Conflict resolution is a branch-integration condition, not an approval decision.

### Closing and Reopening

Closing removes a Pull Request from the normal merge path. Reopening can restore it to an active workflow if the repository permits it.

The state distinction prevents a previously closed object from being treated as automatically mergeable.

## Code Review

Code Review evaluates the proposed implementation. It is distinct from the Pull Request container itself.

The review model records:

- Reviewer identity
- Review state
- Reviewed commit
- Review comments
- Conversation resolution

Supported review states are:

| State | Meaning |
|---|---|
| `commented` | Feedback was submitted without an approval decision |
| `approved` | Reviewer accepts the reviewed revision |
| `changes_requested` | Reviewer requires changes |
| `dismissed` | Earlier review decision is no longer active |

### Review Criteria

A useful review considers:

- Functional correctness
- Security impact
- Error handling
- Data integrity
- Test coverage
- Compatibility
- Maintainability
- Performance implications
- Operational risk
- Scope of the proposed change

The implementation does not assume that every comment is an approval or that every Pull Request automatically becomes mergeable after a review.

### Inline Comments and Conversations

Review comments are attached to files and line positions in the PostgreSQL model. Comments can remain unresolved.

A review discussion and an approval are different objects:

`comment → discussion → resolution`

is not equivalent to:

`approval → merge authorization`

A repository may require every conversation to be resolved before merging, while still requiring a separate number of approvals.

### Review Failure Modes

Important failure conditions include:

- Reviewer is not an eligible repository member
- Author attempts self-approval
- Review references an unknown commit
- Reviewer approves an outdated commit
- Required changes remain unresolved
- Required checks fail after review
- New commits invalidate current approval coverage

The governance engines evaluate these conditions explicitly.

## Approvals

Approval represents a specific reviewer decision. It is not merely evidence that somebody viewed a Pull Request.

The example requires two current approvals for `main`.

An eligible approval must satisfy all of these conditions:

1. The reviewer is an active repository member.
2. The reviewer has reviewer or maintainer authority.
3. The reviewer is not the Pull Request author.
4. The approval references the current Pull Request head commit.
5. The approval has not been replaced by a later revision.

The effective approval model is:

`current eligible reviewer + approved state + current head commit`

### Stale Approvals

Suppose commit `a1b2c3d` receives two approvals. A new commit `d4e5f6g` is then added.

The earlier approvals remain historical review records, but they do not satisfy the current-head approval requirement in this project.

This prevents an approval for one implementation revision from being interpreted as approval for a materially different revision.

### Dismissed Approvals

A dismissed approval remains part of review history but does not count as an active approval.

This distinction is important for auditability. Governance systems should preserve historical decisions rather than deleting them when their current effect changes.

### Approval and Merge Eligibility

Approval is one input to merge eligibility. It is not the complete decision.

The protected branch also requires:

- Passing required checks
- No unresolved conversations
- A mergeable Pull Request
- Required branch synchronization
- An open, non-draft Pull Request

Therefore:

`approvals satisfied ≠ merge eligible`

## Branch Protection

Branch Protection moves governance from individual review decisions to repository-level enforcement.

The example protects `main` with these rules:

| Policy | Configuration |
|---|---|
| Required approvals | 2 |
| Required checks | `ci`, `security` |
| Conversation resolution | Required |
| Linear history/synchronization | Required |
| Direct push | Disabled |
| Force push | Disabled |
| Branch deletion | Disabled |

A protected branch is therefore governed by policy rather than by informal agreement.

### Required Status Checks

The example requires both `ci` and `security` to pass.

A Pull Request with two approvals but a failing security check remains blocked.

This separates automated validation from human review:

`human review + automated checks`

rather than treating either mechanism as a substitute for the other.

### Direct Push and Force Push

Disabling direct pushes ensures that protected-branch changes pass through the governed Pull Request path.

Disabling force pushes reduces the possibility of rewriting protected history outside the approved workflow.

Branch deletion is also disabled for the protected branch.

### Administrator and Bypass Behavior

Administrative authority may exist outside ordinary contributor permissions, but bypass mechanisms should be treated as exceptional governance operations rather than as normal merge conditions.

A bypass can weaken the evidence normally provided by reviews and automated checks. In an enterprise repository, bypass operations should therefore be attributable and auditable.

The PostgreSQL model records merge events with the identity of the merging actor and the merge method.

## Roles and Responsibilities

Responsibility is distributed across the workflow rather than assigned to a single participant.

| Activity | Developer | Reviewer | Maintainer | Administrator |
|---|---:|---:|---:|---:|
| Create feature branch | Yes | Yes | Yes | Yes |
| Commit implementation | Yes | Yes | Yes | Yes |
| Open Pull Request | Yes | Yes | Yes | Yes |
| Review code | No by default | Yes | Yes | Yes |
| Approve own Pull Request | No | No | No | No |
| Request changes | No by default | Yes | Yes | Yes |
| Resolve implementation comments | Yes | Discuss | Discuss | Yes |
| Merge protected branch | No by default | No by default | Yes when eligible | Controlled |
| Configure protection | No | No | Limited | Yes |
| Perform exceptional bypass | No | No | Policy-dependent | Controlled |

The exact permissions depend on repository configuration. The table represents the governance model implemented by this project rather than a universal platform permission matrix.

## Python Implementation

The Python program models repository governance with dataclasses and enumerations.

`Person`, `Commit`, `Review`, `StatusCheck`, `BranchProtection`, `PullRequest`, and `Repository` represent the principal domain objects.

The `Repository.merge_eligibility()` method centralizes the decision process. It returns both a Boolean result and explicit blocking reasons, which makes the workflow suitable for diagnostics rather than producing only a yes/no answer.

The Python implementation demonstrates stale approvals by adding a second commit after the initial approvals. It then restores eligibility by recording approvals against the new head.

Validation rejects self-approval and reviews referencing unknown commits.

The implementation uses standard-library types only. Sets are used for reviewer roles and required checks, while dictionaries provide efficient lookup of repository members and status checks.

## JavaScript Implementation

The JavaScript program uses an event-driven model.

`PullRequest` extends `EventEmitter` and emits events when commits and reviews are added. This reflects an event-oriented repository service in which other components could react to governance changes.

`RepositoryPolicy` isolates protected-branch rules from the Pull Request object. `GovernanceEngine` evaluates the policy against current repository state.

JavaScript `Map` and `Set` structures provide efficient membership and lookup operations. The implementation uses `async` execution at the application boundary while keeping policy evaluation deterministic.

Validation rejects self-approval and unknown review commits. Required checks, current approvals, unresolved conversations, merge conflicts, and branch synchronization are evaluated separately.

## C++17 Implementation

The C++ program implements the governance engine as a strongly typed case study.

Enums represent Pull Request, review, and status-check states. Structs model domain records, while `GovernanceEngine` owns the policy evaluation logic.

The engine returns a `Decision` containing both eligibility and blocking reasons.

`std::unordered_set` is used for role and approval membership checks. `std::unordered_map` provides direct access to repository policies and status checks. This gives expected constant-time lookup for the main governance operations.

The program demonstrates that approvals against an earlier commit do not count after a new commit becomes the Pull Request head.

Exception handling surrounds the application boundary so invalid governance conditions produce controlled failure messages.

## Java 17 Implementation

The Java implementation uses explicit domain types and policy objects.

Records provide immutable representations for `Person`, `Commit`, `Review`, `StatusCheck`, and `BranchProtection`.

The `PullRequest` class owns mutable workflow state, while `EligibilityRule` defines a policy-rule interface. `ReviewRequirement` and `StatusCheckRule` implement separate validation concerns.

`RepositoryService` composes these rules and evaluates repository-level merge eligibility.

This structure makes individual governance rules independently testable and prevents all policy logic from being concentrated in the Pull Request entity.

Java collections and streams are used to derive the current approval set. Immutable collections protect policy and domain snapshots from accidental modification.

## PostgreSQL Implementation

The PostgreSQL implementation treats repository governance as relational state.

The principal relationships are:

`repository → branch → commit`

and

`repository → pull_request → review → review_comment`

with:

`pull_request → status_check`

and:

`protected branch → branch_protection → required_status_check`

The database enforces important invariants using primary keys, foreign keys, unique constraints, check constraints, and a review-validation trigger.

The trigger prevents self-review and verifies reviewer eligibility against repository membership.

The `merge_eligibility` view combines:

- Pull Request state
- Current head commit
- Current approvals
- Required status checks
- Unresolved comments
- Conversation state
- Base-branch synchronization
- Mergeability
- Branch protection

The `can_merge()` SQL function exposes the final eligibility result for a Pull Request.

A transactional merge section demonstrates how a merge decision and state transition can be grouped into one database transaction.

## Cross-Implementation Decision Model

The five implementations use the same core decision structure:

`Pull Request state`
`+ current revision`
`+ eligible approvals`
`+ required status checks`
`+ conversation resolution`
`+ branch synchronization`
`+ protected-branch policy`
`= merge eligibility`

The four governance areas remain distinct:

| Mechanism | Question answered |
|---|---|
| Pull Request | What change is being proposed and where? |
| Code Review | What did reviewers find about the change? |
| Approval | Did an eligible reviewer accept the current revision? |
| Branch Protection | What repository conditions must be satisfied before merge? |

Roles and responsibilities operate across all four mechanisms by determining who may perform each action.

## Validation and Failure Conditions

The implementations explicitly handle:

- Empty Pull Requests
- Draft Pull Requests
- Closed or merged Pull Requests
- Self-approval
- Unauthorized reviewers
- Unknown commits
- Stale approvals
- Failing status checks
- Missing status checks
- Merge conflicts
- Unresolved conversations
- Unsynchronized branches
- Unprotected target branches
- Invalid commit identifiers
- Invalid policy counts
- Negative workflow counters

These checks prevent a single positive signal from incorrectly overriding another governance condition.

## Performance Considerations

The in-memory implementations use hash-based collections for member, check, role, and approval lookups.

The PostgreSQL implementation indexes:

- Pull Requests by target branch and state
- Reviews by Pull Request, reviewed commit, and state
- Status checks by Pull Request and state
- Unresolved review comments through a partial index

The database view uses grouped and windowed queries to identify the current Pull Request head and current approval set.

For large repositories, governance evaluation should avoid repeatedly scanning complete review histories when only current-head state is required. Historical review records remain valuable for audit purposes but should not be confused with active eligibility data.

## Security and Governance Considerations

The model applies several security-oriented controls:

- Self-approval is prohibited.
- Reviewer eligibility is validated.
- Protected branches reject uncontrolled direct changes.
- Force pushes are disabled by policy.
- Required security checks must pass.
- Historical review decisions remain auditable.
- Merge events record the responsible actor.
- Approval validity is tied to the reviewed revision.
- Conversation resolution can be mandatory.
- Administrative bypasses are treated as exceptional rather than ordinary workflow.

These controls reduce the risk of unauthorized or insufficiently reviewed changes reaching protected branches.

## Practical Workflow

A governed change proceeds through the following conceptual sequence:

`Developer`
  ↓
`Feature Branch`
  ↓
`Commits`
  ↓
`Pull Request`
  ↓
`Code Review`
  ↓
`Review Comments / Conversations`
  ↓
`Approval Decisions`
  ↓
`Automated Status Checks`
  ↓
`Branch Protection Evaluation`
  ↓
`Merge Eligibility`
  ↓
`Controlled Merge`

A failure at any required stage blocks the final transition.

This structure makes responsibility explicit: developers own implementation, reviewers evaluate changes, approvers provide formal review decisions, and repository governance determines whether the combined evidence satisfies protected-branch policy.
