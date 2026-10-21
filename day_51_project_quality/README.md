# Project Quality: Understanding Project Quality

## Purpose

Project quality in repository-based software development is not a single property of source code. It is the result of controlled change, independent evaluation, explicit review decisions, and repository-level enforcement.

This artifact models four related but distinct governance mechanisms:

| Mechanism | Primary responsibility |
|---|---|
| Pull Request | Provides the workflow for proposing and integrating a change |
| Code Review | Evaluates the technical content and communicates findings |
| Approvals | Records review decisions that satisfy defined review requirements |
| Branch Protection | Enforces repository-level conditions before integration |

The relationship can be represented as:

`Developer change → Pull Request → Code Review → Approval decision → Branch Protection evaluation → Merge`

The mechanisms must not be treated as synonyms. A Pull Request can exist without approval. A review can contain comments without approval. An approval can be insufficient when the reviewer is ineligible or the approval is stale. Branch protection can block a technically approved Pull Request because a required status check failed or an unresolved conversation remains.

## Pull Requests

A Pull Request is the workflow object used to propose changes from a source branch into a target branch.

The source branch contains the proposed changes. The target branch is the branch that would receive those changes if the merge is permitted. The Pull Request records the relationship between these branches and provides a stable object around which reviews, conversations, checks, and merge decisions can be coordinated.

The Python implementation models a Pull Request as a domain object containing:

- source and target branches
- author
- state
- commits
- reviews
- status checks
- unresolved conversations
- merge-conflict state
- merge strategy
- base revision information

The state machine distinguishes `draft`, `open`, `closed`, and `merged`.

A draft Pull Request allows work to be exposed before it is ready for integration. The Python model requires an explicit transition from draft to open before normal review activity can proceed.

The lifecycle implemented by the Python model is:

`draft → open → merged`

or:

`draft → open → closed → open → merged`

A closed Pull Request can be reopened. A merged Pull Request cannot be reopened or closed as though it were merely an unfinished proposal.

### Source and target branches

The source branch represents the change being proposed. The target branch represents the integration destination.

The implementations reject a Pull Request whose source and target are identical. They also reject references to branches that do not exist.

This distinction matters because repository governance is normally attached to the target branch. A Pull Request targeting an unprotected development branch may have different merge requirements from one targeting a protected production branch.

### Changesets and commits

A Pull Request is not merely a title and description. Its technical content is represented by commits.

The Python, C++, JavaScript, Java, and SQL implementations associate review and validation evidence with a specific commit revision. This is important because an approval of one revision does not automatically prove that a later revision is acceptable.

The model therefore treats a new commit as an event that can invalidate previous review and validation evidence.

### Review requests and conversations

Review requests identify reviewers expected to evaluate a Pull Request.

A conversation is separate from the Pull Request's overall state. A Pull Request may be open while individual review conversations remain unresolved.

The model therefore does not interpret an open Pull Request as automatically ready for merging.

### Status checks

Status checks represent automated validation associated with a particular commit. Examples include:

- unit tests
- security scanning
- static analysis
- integration tests

The SQL model stores both the check name and the commit that produced the result. This prevents a successful check from an older revision from being incorrectly treated as validation of newer code.

### Merge behavior

The examples use three conceptual strategies:

| Strategy | Governance implication |
|---|---|
| Merge commit | Preserves a separate merge commit and can violate linear-history policies |
| Squash | Combines the Pull Request's changes into a single target-branch commit |
| Rebase | Replays commits onto a newer base and preserves individual changes |

Branch protection can restrict which strategies are permitted.

The examples protect `main` by allowing squash and rebase while rejecting merge commits when linear history is required.

### Draft Pull Requests

Draft status represents work that has been proposed for discussion but is not yet ready for normal integration.

The Python, JavaScript, C++, and Java models explicitly represent draft state instead of treating it as an ordinary open Pull Request.

This distinction prevents workflow readiness from being inferred merely from the existence of a Pull Request.

### Base-branch synchronization

The base branch can change after a Pull Request is opened.

The implementations represent the Pull Request's original base revision and current base revision separately. Synchronization can expose merge conflicts and can invalidate review evidence under a stale-review policy.

A production Git implementation would calculate conflicts from the commit graph. The educational implementations intentionally isolate the governance consequence from the lower-level Git merge algorithm.

### Merge conflicts

A Pull Request with unresolved conflicts cannot be considered mergeable under the implemented policies.

The governance engine evaluates conflicts independently from approvals. This prevents an approval from being interpreted as permission to bypass an unresolved integration problem.

### Reopening and closing

Closing a Pull Request stops its active workflow without declaring the change integrated.

Reopening returns a closed Pull Request to the open state. A merged Pull Request remains merged because the integration event has already changed the target branch.

---

## Code Review

Code Review is the evaluation mechanism applied to the proposed changes.

It is distinct from the Pull Request itself. The Pull Request provides the workflow container, while reviews provide technical assessment and communication.

The implementations represent review states:

- `commented`
- `approved`
- `changes_requested`
- `dismissed`

A reviewer can identify a problem without rejecting the entire Pull Request permanently. A later review can change the effective decision.

### Inline comments

The PostgreSQL model represents review comments separately from review records.

A comment can contain:

- reviewer or author
- file path
- line number
- message
- resolution state
- creation timestamp

This allows a review to contain several technical discussions rather than treating the review as a single text field.

### Review states

A review state describes the reviewer's current position regarding the evaluated revision.

`commented` communicates observations without providing approval.

`approved` indicates that the reviewer accepts the evaluated revision under the reviewer's responsibilities.

`changes_requested` indicates that the reviewer expects modifications before the change is considered acceptable.

`dismissed` represents an approval or review decision that is no longer valid under the repository workflow.

### Review discussions

Discussions allow reviewers and authors to examine a specific implementation decision.

The model tracks unresolved conversations separately from approval count. This is important because review approval and discussion resolution answer different questions:

- Approval asks whether an eligible reviewer accepts the change.
- Conversation resolution asks whether review discussions have been addressed.

A repository can require both conditions.

### Requested changes

A requested-change review can neutralize an earlier approval by the same reviewer in the governance model.

This prevents a stale approval from being counted after the reviewer has subsequently identified a blocking problem.

### Reviewer responsibilities

The implementations distinguish repository membership and reviewer eligibility.

The PostgreSQL trigger permits review submissions only from repository members with reviewer-capable roles. Authors are prevented from reviewing their own Pull Requests.

This models a governance principle: an approval is meaningful only when the reviewer is authorized to provide it.

### Review quality and scope

Review quality is represented through the review structure rather than through an arbitrary numeric quality score.

A useful review evaluates the actual changes within a defined scope, such as:

- correctness
- security impact
- regression risk
- maintainability
- compatibility
- test coverage
- operational consequences

The examples use comments, requested changes, and resolution state because these represent observable review workflow behavior.

### Review workflows

A practical workflow represented by the artifacts is:

`Review request → Code inspection → Inline discussion → Requested changes or approval → Resolution → Merge eligibility`

This workflow is separate from the repository-level enforcement mechanism.

### Resolving discussions

The SQL model stores unresolved comments explicitly.

The Python and JavaScript models maintain unresolved conversation counts or conversation objects.

Branch protection can require all review discussions to be resolved before merge. This means an approval alone does not guarantee merge eligibility.

### Review-related failure modes

The models deliberately cover several failure conditions:

- self-review
- review without a commit
- review against a stale commit
- reviewer without appropriate repository role
- unresolved review conversation
- requested changes that neutralize approval
- review evidence invalidated by a new commit

These conditions demonstrate why review state must be modeled independently from Pull Request state.

---

## Approvals

An approval is a specific review decision. It is not equivalent to the existence of a review request or the existence of a reviewer.

The governance model treats approval as current evidence tied to a reviewed commit.

### Approval semantics

The Python, JavaScript, C++, and Java engines count approvals only when the approval applies to the current Pull Request revision.

The SQL function `merge_eligibility` performs the same conceptual evaluation using relational queries.

An approval therefore has at least three relevant properties:

| Property | Governance purpose |
|---|---|
| Reviewer | Identifies who made the decision |
| Reviewed commit | Identifies which revision was evaluated |
| Review state | Identifies the decision |

### Eligible reviewers

Eligibility is enforced separately from the number of approvals.

The SQL trigger checks repository membership and role before accepting a review. This prevents a technically valid database row from automatically becoming a valid governance decision.

### Required reviews

The branch-protection policy in the examples requires two current approvals for `main`.

The number is a policy parameter rather than an intrinsic property of Pull Requests.

Different branches or repositories can define different approval thresholds.

### Approval requirements

The SQL model includes an `approval_requirement` table to represent policy requirements independently from the review records.

This separation is useful because:

`Review record = what a reviewer decided`

while:

`Approval requirement = how many valid decisions governance requires`

The two concepts should not be stored as the same fact.

### Stale approvals

A stale approval is an approval associated with an earlier revision than the one currently proposed for merging.

The implementations invalidate stale evidence when a new commit is added under a stale-review policy.

The second scenario in each programming-language implementation demonstrates this behavior:

`commit-002 → approvals → checks → commit-003 → previous evidence becomes stale`

This is one of the most important distinctions in the model. A Pull Request number remains the same, but its technical content has changed.

### Dismissed approvals

A dismissed review is not equivalent to a current approval.

The SQL model stores dismissal state and timestamp explicitly. The governance query excludes approval evidence that has been superseded by a later changes-requested or dismissed review from the same reviewer.

### Review policies

Approval policies can specify:

- minimum number of reviewers
- reviewer eligibility
- current-revision requirements
- stale-review handling
- required status checks
- conversation-resolution requirements
- permitted merge strategies

These policies determine how individual review decisions affect merge eligibility.

### Effect of approvals on merge eligibility

Approval is one condition among several.

The governance engine evaluates:

`Pull Request open`
`+ commits exist`
`+ no merge conflicts`
`+ permitted merge strategy`
`+ sufficient current approvals`
`+ required checks passed`
`+ required discussions resolved`
`+ branch-specific policy satisfied`

Only when all required conditions hold does the engine report a mergeable Pull Request.

This prevents approval from being interpreted as a general bypass permission.

---

## Branch Protection

Branch Protection is the repository-level enforcement layer.

It is distinct from the Pull Request workflow and from individual reviews.

A Pull Request proposes a change.

A code review evaluates that change.

An approval records a review decision.

Branch protection determines which repository conditions must be satisfied before the change can be integrated.

### Protected branches

The SQL model stores protection separately from branch identity.

The example protects `main` with:

- two required current approvals
- required unit tests
- required security scanning
- conversation resolution
- restricted direct pushes
- no force pushes
- no branch deletion
- linear-history enforcement
- squash or rebase merge strategies

### Required status checks

Required status checks are stored separately from review records.

This allows the policy to state that a Pull Request cannot merge unless specific automated checks pass on the current commit.

The SQL schema uses `required_status_check`, while each actual execution is stored in `status_check`.

The distinction is:

`required_status_check = policy`

`status_check = observed result`

### Required reviews

The branch protection record defines the minimum number of approvals.

The actual approvals remain in code-review records.

This separation allows a policy to change without rewriting historical reviews.

### Direct-push restrictions

A protected branch can restrict direct pushes so that changes must pass through the governed Pull Request workflow.

The database stores the policy flag, while the application-level governance engine can use that flag to determine whether a direct branch update should be rejected.

The model intentionally does not pretend that a database boolean by itself can enforce Git transport permissions. Real enforcement must occur at the repository or hosting-service authorization layer.

### Force-push restrictions

Force pushes can rewrite branch history.

The policy therefore stores whether force pushes are allowed.

For a production repository, allowing force pushes on a protected production branch would require strong justification because rewriting history can invalidate review context and disrupt collaborators.

### Branch deletion restrictions

Protected branches can also prohibit deletion.

The policy records this independently from Pull Request state because deleting a branch is a repository administration operation rather than a review decision.

### Conversation requirements

The branch protection policy can require all review conversations to be resolved.

This is an enforcement rule, not a review state.

A reviewer may approve a Pull Request while another discussion remains unresolved. If the protected branch requires resolution, the Pull Request remains blocked.

### Linear-history requirements

A linear-history requirement changes which merge strategies are valid.

The implementations reject a merge-commit strategy when linear history is required.

This is a branch-level integration policy rather than a code-review criterion.

### Administrator behavior and bypass

Branch protection can contain explicit bypass mechanisms.

The Python, JavaScript, C++, and Java implementations model configured bypass users. The SQL model stores bypass identities in `branch_bypass`.

A bypass should be treated as an explicit governance exception rather than silently allowing privileged users to ignore every policy.

The bypass decision is visible in the merge-evaluation result.

---

## Cross-Mechanism Governance Model

The four mechanisms form a dependency chain without becoming interchangeable:

| Question | Mechanism responsible |
|---|---|
| How is a proposed change organized? | Pull Request |
| What is being evaluated? | Changes and commits associated with the Pull Request |
| Who evaluated it and what did they decide? | Code Review |
| Does a review constitute an approval? | Review and approval policy |
| Are enough valid approvals present? | Approval requirements |
| Can the target branch accept the change? | Branch Protection |
| Are required automated checks satisfied? | Branch Protection using status-check results |
| Are review conversations resolved? | Review workflow plus Branch Protection |
| Is the selected integration strategy allowed? | Branch Protection |

The resulting decision can be represented as:

`Pull Request state`
`→ current changeset`
`→ current review evidence`
`→ approval requirements`
`→ automated checks`
`→ conversation requirements`
`→ branch-protection policy`
`→ merge eligibility`

This separation makes failure diagnosis more precise.

For example:

- A Pull Request can be open but lack approvals.
- A Pull Request can have enough approvals but fail security scanning.
- A Pull Request can have passing checks but contain unresolved conversations.
- A Pull Request can satisfy review requirements but use a prohibited merge strategy.
- A previously approved Pull Request can become non-mergeable after a new commit.
- A review can exist but be invalid because the reviewer is not eligible.
- A protected branch can reject integration even when the Pull Request itself is technically valid.

---

## Python Implementation

The Python implementation is a repository workflow simulator centered on domain objects.

`Repository` owns branches, protection policies, and Pull Requests. `PullRequest`, `Review`, `Commit`, `StatusCheck`, and `BranchProtection` represent distinct domain entities.

The merge evaluator returns both a Boolean result and explicit reasons. This makes debugging governance decisions more useful than returning only a mergeable or blocked flag.

The implementation also demonstrates:

- draft-to-open transitions
- review requests
- commit-specific reviews
- status-check evaluation
- conversation resolution
- base synchronization
- conflict representation
- stale-review invalidation
- merge-strategy restrictions
- close and reopen operations
- bypass behavior
- deterministic merge-result identifiers

The Python model uses standard-library dataclasses and enums to make state explicit without external dependencies.

---

## JavaScript Implementation

The JavaScript implementation uses an event-driven architecture.

`Repository` extends `EventEmitter`, so important workflow operations emit events such as:

- `pull_request.created`
- `pull_request.commit_added`
- `review.requested`
- `review.submitted`
- `status_check.updated`
- `conversation.opened`
- `conversation.resolved`
- `pull_request.synchronized`
- `pull_request.merged`

This makes the implementation complementary to the Python simulator.

The event stream represents what happened. The merge evaluator represents whether the current repository state satisfies policy.

JavaScript `Map` and `Set` structures are used for branches, Pull Requests, checks, conversations, required checks, and bypass identities.

The asynchronous `main` function demonstrates that the model can fit an event-driven Node.js workflow while retaining synchronous policy evaluation for deterministic governance decisions.

---

## C++17 Implementation

The C++ implementation treats repository governance as a merge-eligibility engine.

The design uses explicit structures for:

- commits
- reviews
- status checks
- branch-protection policies
- Pull Requests
- merge decisions

The engine evaluates a Pull Request against a protected target branch and produces a collection of reasons when integration is blocked.

C++17 features include:

- `enum class` for constrained state values
- `std::map` for repository indexes
- `std::set` for approvals and policy membership
- `std::vector` for ordered commits and reviews
- `std::optional`-style reasoning through nullable commit access
- exception-based failure handling
- structured aggregate initialization

The C++ implementation emphasizes deterministic evaluation and explicit data structures suitable for a governance service.

Its commit-specific evidence model also illustrates a practical trade-off: storing review state against a commit prevents an approval from being treated as permanently valid when the source branch changes.

---

## Java 17 Implementation

The Java implementation models enterprise repository governance with explicit domain types and services.

Java records are used for immutable value objects such as:

- `Commit`
- `Review`
- `StatusCheck`
- `BranchProtection`
- `MergeDecision`

The mutable `PullRequest` class represents workflow state because Pull Requests transition through draft, open, closed, and merged states.

`Repository` acts as the domain service responsible for:

- branch management
- Pull Request creation
- commit association
- review submission
- status-check recording
- discussion resolution
- base synchronization
- merge-eligibility evaluation
- merge execution

Java collections provide separate representations for ordered review history, current checks, and unresolved conversations.

The model uses immutable sets in policy records so that callers cannot accidentally mutate branch rules after construction.

The enterprise-oriented design makes policy conflicts explicit through `GovernanceException` and returns a `MergeDecision` containing both eligibility and reasons.

---

## PostgreSQL Relational Model

The PostgreSQL implementation represents repository governance as persistent relational state.

The major relationships are:

`repository`
→ `branch`
→ `branch_protection`

`repository`
→ `pull_request`
→ `pull_request_commit`
→ `commit`

`pull_request`
→ `review_request`

`pull_request`
→ `code_review`
→ `review_comment`

`pull_request`
→ `status_check`

`branch_protection`
→ `required_status_check`

`branch_protection`
→ `protected_merge_strategy`

`branch_protection`
→ `approval_requirement`

`branch_protection`
→ `branch_bypass`

The schema uses PostgreSQL enum types for workflow states. Foreign keys preserve referential integrity, while check constraints prevent invalid states such as a dismissed review without dismissal metadata or a passed status check without a completion timestamp.

The partial index on the default branch prevents a repository from having multiple default branches.

The review trigger enforces reviewer eligibility at the database boundary. The commit-membership trigger prevents a review from referencing a commit that is not actually part of the Pull Request.

The `merge_eligibility` function evaluates the current state relationally.

The `merge_pull_request` function performs the integration decision inside a transaction and locks the Pull Request row before updating its state and target branch.

This is important because governance evaluation followed by mutation must not be treated as two unrelated operations when concurrent users can attempt to merge the same Pull Request.

---

## Transaction and Integrity Model

The SQL implementation uses several layers of integrity.

### Structural integrity

Foreign keys ensure that reviews, commits, status checks, branches, and Pull Requests reference existing records.

### Domain integrity

Check constraints enforce rules such as positive sequence numbers and valid state combinations.

### Workflow integrity

Triggers enforce rules that depend on related records, such as reviewer eligibility and commit membership.

### Policy integrity

Branch-protection tables store requirements independently from the events that satisfy them.

### Transactional integrity

The merge procedure locks the Pull Request before changing its state and target branch.

The intended transactional sequence is:

`evaluate eligibility → lock Pull Request → update Pull Request → update target branch → record merge event → commit`

If the transaction fails, the database does not leave the Pull Request marked as merged while the target branch remains unchanged.

---

## Performance Considerations

The most important access patterns are indexed explicitly.

`idx_pr_target_state` supports retrieval of Pull Requests by protected target branch and workflow state.

`idx_pr_commit_sequence` supports finding the current Pull Request revision efficiently.

`idx_review_pr_commit_state` supports approval evaluation against the current commit.

`idx_review_comments_unresolved` is a partial index because merge evaluation is primarily interested in unresolved discussions.

`idx_status_check_pr` supports required-check lookup.

The in-memory implementations use hash-based or tree-based collections depending on the language and requirement. The main performance concern is not the number of objects in a small repository simulation but the repeated evaluation of current review evidence and required checks.

In a production service, governance evaluation should avoid repeatedly scanning large review histories when the current revision and current effective review state can be materialized or indexed.

---

## Security Considerations

Repository governance is an authorization boundary.

Important controls represented by the artifacts include:

- preventing self-approval
- requiring reviewer eligibility
- restricting direct pushes
- restricting force pushes
- preventing protected branch deletion
- requiring current status-check evidence
- requiring current approvals
- supporting explicit bypass identities
- preserving merge events
- keeping review and commit relationships auditable

The models do not treat an approval string or Boolean as trusted merely because it exists.

A production implementation should also protect repository administration, branch-policy modification, reviewer-role assignment, and bypass configuration with stronger authorization controls than ordinary contributor permissions.

---

## Failure and Debugging Model

The implementations return or record concrete governance failures rather than generic merge errors.

Representative failures include:

| Failure | Governance interpretation |
|---|---|
| Unknown branch | Workflow references invalid repository state |
| Empty commit set | There is nothing to review or merge |
| Self-review | Reviewer independence requirement violated |
| Ineligible reviewer | Approval cannot satisfy policy |
| Stale approval | Decision applies to an older revision |
| Missing check | Required automated validation has no result |
| Failed check | Automated validation rejected the current revision |
| Merge conflict | Source and target cannot currently be integrated safely |
| Unresolved conversation | Review workflow remains incomplete |
| Invalid strategy | Branch policy rejects the selected integration method |
| Insufficient approvals | Required independent decisions are missing |
| Closed Pull Request | Active merge workflow no longer exists |
| Protected branch without policy | Repository governance configuration is incomplete |

This diagnostic structure is important for operational use because a developer needs to know which condition prevented integration rather than simply receiving a generic authorization failure.

---

## Limitations of the Model

The artifacts intentionally model repository governance rather than implementing a complete Git server.

The conflict model represents the existence of conflicts but does not calculate a Git three-way merge.

The merge strategies are represented as governance choices rather than physically rewriting Git object graphs.

Status checks are modeled as stored results rather than executed CI pipelines.

Branch-protection enforcement for network operations such as direct pushes and force pushes requires an authorization layer outside the relational schema.

Reviewer eligibility is simplified to repository roles. Real organizations may use teams, ownership rules, CODEOWNERS-style policies, organization membership, or specialized approval groups.

These boundaries keep Pull Request workflow, Code Review, Approvals, and Branch Protection conceptually distinct while still showing how they interact in a real repository governance system.
