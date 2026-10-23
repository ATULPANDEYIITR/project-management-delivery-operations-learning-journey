# Pull Requests, Code Review, Approvals, and Branch Protection

This project models repository change governance through four related but distinct mechanisms:

- **Pull Requests** provide the workflow for proposing a changeset.
- **Code Review** evaluates the proposed changes and records reviewer decisions and discussions.
- **Approvals** represent review decisions that may satisfy a repository policy.
- **Branch Protection** defines repository-level conditions that must be satisfied before a protected branch accepts a merge.

The central relationship is:

`feature branch → Pull Request → Code Review → Approval decisions → Branch Protection evaluation → Merge`

These mechanisms overlap operationally, but they solve different problems. A Pull Request is not itself an approval. An approval is not itself a branch-protection policy. Code Review provides evaluation and discussion, while Branch Protection determines which repository conditions are mandatory.

## Pull Request lifecycle

A Pull Request connects a **source branch** containing proposed changes to a **target branch** that should receive them.

The modeled lifecycle is:

`Draft → Open → Review → Synchronization → Eligible → Merged`

A Pull Request may also move from `Open` to `Closed` and later be reopened. A merged Pull Request becomes immutable in the models.

A Pull Request contains a current head revision. This is important because review decisions and automated checks are associated with a particular changeset. Adding another commit changes the revision being evaluated.

The Python implementation uses `PullRequest` objects with explicit state, source branch, target branch, commits, reviewers, reviews, checks, and conversations. The implementation rejects invalid transitions such as modifying a merged Pull Request.

The JavaScript implementation treats Pull Request state changes as events. Events such as `reviewRequested`, `reviewSubmitted`, `commitAdded`, and `merged` allow surrounding services to react without embedding every workflow concern inside the Pull Request object.

The C++ implementation focuses on an explicit governance engine. The Pull Request is the proposed change, while the governance engine decides whether the proposal satisfies protected-branch conditions.

The Java implementation separates domain state from `GovernanceService`. Immutable records represent commits, reviews, checks, policies, and decisions while the Pull Request controls mutable workflow state.

The PostgreSQL model stores Pull Requests independently from commits, review requests, reviews, comments, status checks, and merge records. Foreign keys preserve relationships between these objects.

## Changesets, commits, and base-branch synchronization

A Pull Request is evaluated against a particular head revision. The five implementations therefore avoid treating a Pull Request as a static document.

When a new commit is added:

- the Pull Request receives a new head revision;
- approvals attached to an older revision become stale or dismissed;
- status checks from the older revision cannot automatically satisfy checks for the new revision;
- reviewers must evaluate the current changeset again.

Base-branch synchronization is modeled as a revision-changing operation. The Python and JavaScript implementations explicitly invalidate prior approvals and checks when synchronization changes the evaluated revision.

This reflects an important governance distinction: approval of revision `A` does not necessarily mean approval of revision `B`, even when `B` contains most of the same code.

Merge conflicts are a related Pull Request condition. A conflict means the proposed source changes cannot be cleanly applied to the current target-branch state. Synchronization can update the source branch, but it does not itself constitute review approval.

## Code Review

Code Review evaluates the actual proposed changes.

A review can contain:

- a reviewer identity;
- a review state;
- the revision inspected;
- comments;
- discussion state;
- a dismissal state.

The implementations distinguish `commented`, `approved`, `changes_requested`, and `dismissed` states.

An inline review comment is represented separately from the overall review in the SQL model. This distinction matters because one review can contain multiple comments, while the review itself still has one principal decision state.

A review workflow can therefore look like:

`Reviewer receives request → inspects current revision → comments → requests changes or approves → author responds → reviewer reevaluates`

### Review quality and scope

A review should evaluate the proposed changes rather than unrelated repository changes. The governance models associate each review with a specific commit revision so that the decision has an identifiable scope.

The examples use payment authorization because it produces realistic review concerns:

- authorization boundaries;
- regression coverage;
- security checks;
- review discussions;
- changes requested by a reviewer;
- re-review after the author adds a corrective commit.

The code does not treat the existence of a comment as proof that a review was completed. A comment, an approval, and a requested-change decision have different meanings.

### Review discussions

Unresolved conversations are tracked separately from review decisions.

This allows a repository policy to require all review conversations to be resolved before merging. Resolving a discussion does not automatically create an approval. Likewise, an approval does not automatically resolve every conversation.

This separation prevents one workflow state from being incorrectly used as a substitute for another.

## Approvals

An approval is a review decision with a specific semantic meaning: the reviewer accepts the current revision according to the reviewer's responsibilities and the repository's review policy.

The governance models count only approvals that satisfy all of these conditions:

- the review is an approval;
- the reviewer is not the Pull Request author;
- the review has not been dismissed;
- the review references the current Pull Request head revision.

This is intentionally stricter than simply counting every historical approval.

### Eligible reviewers

Reviewer eligibility is separate from approval count.

The Python, JavaScript, C++, and Java models prevent self-review. The SQL model records repository membership and reviewer capability so eligibility can be represented at the data level.

A production policy can make eligibility more restrictive by considering:

- repository membership;
- team membership;
- ownership of affected files;
- required security reviewers;
- separation-of-duties rules;
- administrator bypass policy.

### Stale approvals

A stale approval is an approval made against a revision that is no longer the current revision.

For example:

`a100 → Bob approves`

followed by:

`a101 → author changes authorization logic`

means Bob's approval for `a100` should not automatically satisfy a policy requiring approval of `a101`.

The implementations therefore dismiss or ignore approvals attached to older revisions.

This is one of the most important relationships between Pull Requests and Approvals: the Pull Request supplies the current changeset, while the approval is a decision about a particular changeset.

### Dismissed approvals

A dismissed approval cannot satisfy the current approval requirement.

Dismissal can occur because:

- the Pull Request changed substantially;
- repository policy invalidated the review;
- an authorized governance action explicitly dismissed the review;
- a reviewer's decision is no longer applicable.

The models represent dismissal independently from simply deleting the historical review. Preserving the historical decision provides an audit trail.

## Branch Protection

Branch Protection operates at repository governance level.

A protected branch can require conditions such as:

| Policy | Purpose |
|---|---|
| Required reviews | Establishes the minimum approval threshold |
| Required status checks | Requires automated validation |
| Conversation resolution | Prevents unresolved review discussions from being merged |
| Direct-push restriction | Forces changes through the governed workflow |
| Force-push restriction | Protects branch history |
| Deletion restriction | Prevents accidental removal of important branches |
| Linear-history requirement | Restricts acceptable history shape |
| Administrator bypass | Defines whether privileged users can bypass selected controls |

The branch-protection layer does not perform the review itself. It evaluates whether the Pull Request and its associated evidence satisfy the repository's rules.

The project uses two required status checks:

`tests`

and

`security`

Both must pass against the current Pull Request revision.

## Merge eligibility

Merge eligibility is a policy decision rather than a single review result.

For the example repository, the effective rule is:

`Open PR`
`+ current head revision`
`+ 2 current approvals`
`+ no active changes-requested review`
`+ tests passed on current revision`
`+ security passed on current revision`
`+ zero unresolved conversations`
`= merge eligible`

A failure in any required condition blocks the merge.

This makes the distinction between approval and branch protection explicit. Two approvals are necessary but are not sufficient if a required security check is failing.

## Merge strategies

The implementations model three common merge strategies:

- `merge_commit` preserves an explicit merge commit;
- `squash` combines Pull Request changes into a consolidated commit;
- `rebase` applies commits onto the current target history.

Branch protection may constrain which strategies are acceptable. The C++ and Java models expose strategy selection while the policy separately represents linear-history requirements.

A linear-history requirement is therefore a branch policy rather than a property of the Pull Request itself.

## Python implementation

The Python program provides the most direct repository workflow simulation.

`PullRequest` owns the lifecycle and review-related state. `BranchProtection` defines repository policy, while `Repository.evaluate_merge()` evaluates the Pull Request against that policy.

Important mechanisms include:

- dataclasses for repository entities;
- enums for explicit state values;
- sets for reviewer and required-check membership;
- revision-aware approval validation;
- stale-approval invalidation;
- status-check validation;
- conversation resolution;
- merge-state enforcement;
- exception-based validation.

The demonstration intentionally starts with a blocked Pull Request. One reviewer initially requests changes, a conversation remains unresolved, and only one approval is valid. The author then adds a corrective commit, both reviewers approve the new revision, the conversation is resolved, and the required checks are rerun.

## JavaScript implementation

The JavaScript implementation uses an event-driven design rather than directly mirroring the Python object model.

`PullRequest` extends `EventEmitter`, allowing repository services to observe workflow events such as:

- review requests;
- submitted reviews;
- new commits;
- status changes;
- conversations;
- base synchronization;
- merges.

`GovernanceEngine` evaluates branch policy independently.

This separation is useful in an event-driven application because notification, audit logging, metrics, and policy evaluation can subscribe to repository events without being tightly coupled to the Pull Request's internal methods.

The JavaScript model uses `Set` for reviewer and approval identity uniqueness and `Map` for current status checks.

## C++ implementation

The C++ program is structured as a repository governance engine.

The `PullRequest` class manages the proposed changeset and workflow state. `GovernanceEngine` evaluates merge eligibility using `BranchProtection`.

`MergeDecision` contains both the boolean decision and detailed failure reasons. This is preferable to returning only `true` or `false` because governance systems need an actionable explanation when a merge is blocked.

The program also uses C++17 features such as:

- scoped enumerations;
- structured bindings;
- standard containers;
- move semantics;
- immutable-by-interface accessors;
- exception-based validation.

The governance engine checks current-revision approvals and status checks rather than historical results.

## Java implementation

The Java implementation uses explicit enterprise domain types.

Records represent immutable values such as:

- `Commit`;
- `Review`;
- `StatusCheck`;
- `BranchProtectionPolicy`;
- `MergeDecision`.

`PullRequest` owns workflow state, while `GovernanceService` evaluates policy.

This separation reflects an enterprise architecture in which domain state and governance policy have distinct responsibilities.

Java's immutable records are useful for audit-oriented values because a stored review decision cannot be modified accidentally after construction. A dismissed review is represented as a new review value rather than by mutating the original record.

The service returns a `MergeDecision` containing failure reasons instead of allowing callers to infer policy state from exceptions.

## PostgreSQL implementation

The PostgreSQL model treats repository governance as relational data.

The principal relationships are:

`repositories → branches → branch protection`

`repositories → commits`

`pull_requests → branches`

`pull_requests → pull_request_commits`

`pull_requests → review_requests`

`pull_requests → reviews → review_comments`

`pull_requests → status_checks`

`pull_requests → pull_request_merges`

Foreign keys preserve referential integrity, while check constraints reject invalid values such as negative unresolved-conversation counts.

The database also uses PostgreSQL-specific features:

- `ENUM` types for controlled workflow states;
- `BIGSERIAL` identifiers;
- partial indexes for unresolved comments;
- `FILTER` aggregation;
- PL/pgSQL functions;
- triggers;
- transactional merge processing;
- CTE-based reporting.

The `evaluate_merge_eligibility()` function evaluates approvals against the Pull Request's current head commit. This prevents historical approvals from being counted merely because they exist in the database.

The `merge_pull_request()` function performs the merge operation only after policy evaluation succeeds.

## Transaction and integrity behavior

The SQL workflow uses a transaction around the merge operation.

The database first evaluates the current governance state, then records the merge and changes the Pull Request state to `merged`.

The Pull Request mutation trigger prevents subsequent state modification of an already merged Pull Request.

This protects the database from a class of application-level errors where an already completed governance operation could later be altered by an ordinary update.

## Failure modes represented by the project

The implementations deliberately handle failures that occur in real repository workflows.

### Invalid Pull Request state

A closed or merged Pull Request cannot be treated as an ordinary open review target.

### Empty or invalid changesets

A Pull Request without a current commit cannot satisfy revision-based approval or status-check requirements.

### Self-review

The author cannot satisfy the required independent-review count by approving their own Pull Request.

### Stale approvals

An approval associated with an older commit cannot satisfy a policy requiring approval of the current revision.

### Requested changes

An active `changes_requested` review blocks merging until the review state is addressed according to repository policy.

### Failed or stale checks

A check passing for an old revision does not prove that the current revision passes.

### Unresolved conversations

A repository can require review discussions to be resolved before merging.

### Merge conflicts

Conflicts arise from incompatibility between the source changes and the current target branch. They require source-branch synchronization and conflict resolution before the resulting revision can be evaluated again.

### Direct pushes

A protected branch can prohibit direct pushes so that changes must pass through the governed Pull Request workflow.

### Force pushes

A protected branch can prohibit force pushes to reduce history-rewriting risk.

### Branch deletion

A protected branch can prohibit deletion, preventing accidental removal of critical repository history.

### Administrative bypass

The models include an administrator-bypass policy flag because governance systems sometimes distinguish ordinary enforcement from explicitly authorized exceptional operations. A production implementation should audit every bypass rather than silently treating it as a normal merge.

## Repository governance model

The four mechanisms form a control chain:

`Pull Request`
`  ↓`
`proposes a changeset`

`Code Review`
`  ↓`
`evaluates the changeset`

`Approvals`
`  ↓`
`records eligible review decisions`

`Branch Protection`
`  ↓`
`enforces repository-level merge conditions`

`Merge`
`  ↓`
`accepts the changes into the protected branch`

The distinction matters operationally. A Pull Request can exist without an approval. A review can exist without approval. An approval can exist without satisfying branch protection. Branch protection can reject an otherwise well-reviewed Pull Request because a required automated check failed or a discussion remains unresolved.

## Performance and security considerations

Repository systems can accumulate large numbers of commits, reviews, comments, and status checks. Queries should therefore use indexes based on actual access patterns.

The SQL model indexes:

- Pull Requests by target branch and state;
- reviews by Pull Request, revision, and state;
- unresolved comments using a partial index;
- status checks by Pull Request and state;
- Pull Request commits by Pull Request and position.

The application models use hash-based collections such as Python sets and JavaScript `Set` objects for membership tests. Java and C++ use appropriate collection types for reviewer and policy membership.

Security-sensitive repository governance should treat reviewer identity and branch policy as authorization data rather than ordinary display information. Self-review prevention, reviewer eligibility, protected branches, force-push restrictions, and bypass rules should be enforced by the authoritative repository service or database rather than relying only on user-interface behavior.

The most important security boundary is the merge operation itself. A client may display a Pull Request as ready, but the authoritative merge service must independently reevaluate the current revision and all required branch-protection conditions immediately before accepting the merge.
