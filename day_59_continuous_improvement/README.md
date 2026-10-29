# Continuous Improvement: Improving Project Processes

## Purpose

This learning artifact models continuous improvement as a controlled software-delivery process. The implementations use pull requests, code review, approvals, status checks, and branch protection as distinct mechanisms that collectively reduce process risk and make repository changes measurable.

The central relationship is:

Repository
→ Branches
→ Commits
→ Pull Requests
→ Code Reviews
→ Review Decisions
→ Status Checks
→ Branch Protection
→ Merge Eligibility
→ Merge
→ Process Measurement
→ Continuous Improvement

The four governance concepts have different responsibilities:

| Area | Primary responsibility |
|---|---|
| Pull Requests | Propose and manage a change between branches |
| Code Review | Evaluate the technical quality and risks of the proposed change |
| Approvals | Record formal reviewer decisions |
| Branch Protection | Enforce repository-level conditions before merge |

A pull request is therefore a workflow object. Code review is an evaluation activity performed against the proposed changes. An approval is a review decision with a specific state and commit context. Branch protection is an enforcement mechanism that determines which conditions must be satisfied before a protected branch accepts the change.

## Continuous Improvement Model

The implementations treat process improvement as a measurable engineering workflow rather than as an informal recommendation.

A typical improvement cycle is:

1. Establish a baseline.
2. Propose a process change through a pull request.
3. Review the proposed change.
4. Run automated checks.
5. Resolve review discussions.
6. Satisfy approval requirements.
7. Evaluate protected-branch rules.
8. Merge only when all required conditions are satisfied.
9. Measure the resulting workflow.
10. Use the measurements to identify the next improvement.

Useful process measurements include pull request cycle time, number of review iterations, unresolved conversations, approval latency, status-check failures, and merge eligibility failures.

## Pull Requests

A pull request connects a source branch to a target branch. The source branch contains the proposed changes, while the target branch identifies the branch that may receive those changes after governance conditions are satisfied.

The Python implementation represents this directly with `PullRequest`, `Branch`, and `Commit` objects. A pull request records its source branch, target branch, author, proposed commits, reviews, status checks, conversations, and lifecycle state.

The lifecycle represented by the implementations is:

`draft → open → closed`

or:

`draft → open → merged`

A closed pull request is not automatically equivalent to a merged pull request. A merged pull request records successful integration into the target branch.

### Source and Target Branches

The source branch supplies the proposed changes. The target branch supplies the repository context and governance policy that controls the merge.

The implementations reject a pull request where source and target are identical and require the source branch to contain a commit.

A source branch may continue to change while its pull request is open. The `synchronize` operations in Python, JavaScript, and Java refresh the proposed commit set from the source branch.

### Commits and Changesets

Commits are the concrete units of repository history. A pull request is a higher-level grouping of those commits for review and integration.

The implementations associate reviews and status checks with a commit SHA. This is important because an approval against one commit should not automatically remain valid after the proposed code changes.

### Draft Pull Requests

Draft status represents work that is not ready for final integration. The governance engines prevent a draft pull request from becoming merge eligible.

The draft state is distinct from review rejection. A draft is a workflow state, while `changes_requested` is a reviewer decision.

### Synchronization and Stale Decisions

When a source branch changes, previous approval decisions may no longer describe the current code. The Python, JavaScript, and Java implementations therefore support stale-approval dismissal when configured by branch policy.

For example:

`commit B100002 → approval`

followed by:

`commit B100003 → source branch changes`

causes the approval associated with `B100002` to be treated as stale when the policy requires dismissal.

This prevents an approval for an earlier changeset from silently authorizing a different changeset.

### Merge Conflicts

The implementations model branch divergence through separate branch histories and merge eligibility rather than attempting to reproduce Git's complete three-way merge algorithm.

A production Git integration must obtain the actual repository merge state from Git or the hosting service. The governance models deliberately focus on policy evaluation rather than implementing a complete version-control engine.

### Reopening and Closing

The Python implementation explicitly supports closing and reopening pull requests. The JavaScript and Java models concentrate on governance evaluation and merge state.

A reopened pull request must be evaluated against its current state and current protection policy. Closing a pull request does not imply that its reviews should be reused without validation.

## Code Review

Code review evaluates the proposed changes. It is broader than the final approval decision.

A review may:

- provide comments without approval;
- request changes;
- approve the current changeset;
- become dismissed because the approved commit is no longer current.

The implementations represent these states explicitly through `ReviewState`.

### Review Scope

A useful review evaluates criteria such as:

| Criterion | Review question |
|---|---|
| Correctness | Does the change implement the intended behavior? |
| Maintainability | Is the resulting process or code understandable? |
| Testing | Are important behavior paths validated? |
| Security | Does the change introduce an avoidable security weakness? |
| Reliability | What happens when dependencies or checks fail? |
| Operational impact | Can the change affect deployment or recovery? |
| Scope | Does the change remain aligned with the stated objective? |

The model separates review discussion from approval enforcement. A reviewer can comment without granting approval.

### Review Discussions

The Python implementation represents unresolved conversations with an integer count. The JavaScript and Java implementations use explicit conversation identifiers or sets. The PostgreSQL model uses a dedicated `conversations` table.

This allows a policy to require that review discussions be resolved before merging.

A discussion lifecycle is:

`opened → reviewed → resolved`

A resolved discussion does not itself constitute an approval. These are separate process states.

### Requested Changes

`changes_requested` means the reviewer does not consider the current implementation ready for acceptance.

A requested change can coexist with successful automated checks. Automated checks measure machine-verifiable conditions; human review evaluates aspects that require contextual judgment.

### Review Quality

Review quality is represented through reviewer identity, commit context, review state, comments, and conversation state.

A high-quality process should avoid treating the number of approvals as a complete measure of review quality. The number of approvals is a governance threshold, not a substitute for technical review depth.

## Approvals

Approval is a specific review decision. It should be evaluated against the current pull request head and repository policy.

The implementations enforce several approval rules:

- authors cannot approve their own pull requests;
- only eligible reviewers can contribute approval decisions in the Java model;
- approval must correspond to the current head commit;
- dismissed approvals do not count;
- multiple approvals can be required;
- approval count is distinct from review-comment count.

### Eligible Reviewers

Reviewer eligibility is a policy question.

The Java implementation makes this explicit with `ReviewerEligibilityPolicy`. The sample policy allows designated reviewers while rejecting self-approval.

The PostgreSQL implementation records repository membership and roles so that eligibility can be extended into a database-level policy.

### Required Reviews

A branch protection policy may require two approvals, for example:

`required approvals = 2`

A pull request with one current approval remains blocked even when all status checks pass.

This separates human governance from automated validation.

### Stale Approvals

Approval is associated with a commit. When the pull request head changes, an earlier approval may no longer represent the current code.

The implementations model this by comparing:

`review.commitSha`

with:

`pullRequest.head()`

When stale-approval dismissal is enabled, the approval becomes `dismissed`.

### Dismissed Approvals

Dismissal is not the same as a new rejection. It indicates that an existing approval is no longer valid for the merge decision.

A new approval can be submitted against the new head commit.

### Effect on Merge Eligibility

Approvals contribute to merge eligibility, but they do not independently authorize a merge.

The merge decision combines:

- pull request state;
- draft status;
- current approvals;
- current status checks;
- unresolved conversations;
- target-branch policy.

This distinction prevents an approval from bypassing repository-level enforcement.

## Branch Protection

Branch protection is the repository-level enforcement layer.

A protected branch can require:

- a minimum number of approvals;
- successful status checks;
- resolved conversations;
- linear history;
- restricted direct pushes;
- restricted force pushes;
- restricted branch deletion.

The PostgreSQL model stores these controls in `branch_protection_policies` and `required_status_checks`.

### Protected Branches

The sample repository protects `main`.

The intended workflow is:

`developer branch`
→ `pull request`
→ `review`
→ `status checks`
→ `approval`
→ `branch policy evaluation`
→ `main`

A direct push does not represent the same governance path as a pull request.

### Required Status Checks

Status checks are automated signals associated with a specific commit.

The examples use:

- `unit-tests`
- `security-scan`

A check must be successful for the current pull request head. A successful check belonging to an older commit does not satisfy the current requirement.

### Direct Push Restrictions

The sample policy sets direct pushes to the protected branch as disallowed.

The code models this as a policy property. A complete production implementation would enforce the restriction at the repository hosting layer.

### Force Push Restrictions

Force pushes can rewrite branch history and invalidate assumptions about the reviewed state.

The policy therefore records `allowForcePush = false`.

This is particularly important for protected branches where review decisions depend on a stable history.

### Branch Deletion

The policy model contains a branch-deletion restriction. Protected production branches generally require explicit governance before deletion.

The database stores this as `allow_branch_deletion`.

### Linear History

The policy model supports a `requireLinearHistory` setting.

Linear history reduces certain forms of branch-history complexity. It is a repository policy rather than a property of a code review itself.

The examples store the requirement and evaluate the surrounding merge policy. A production implementation must combine this rule with the actual Git merge graph.

### Administrator Behavior and Bypass

The models deliberately do not treat administrative privilege as an implicit merge approval.

A real repository platform can support administrative bypass mechanisms, but bypassing branch protection changes the governance path. A bypass should therefore be audited separately from an ordinary policy-compliant merge.

The database design can support this distinction through `repository_members`, `merge_events`, and `merged_by`.

## Python Implementation

The Python file models repository workflow behavior with dataclasses and enumerations.

Important domain types include:

- `Repository`
- `Branch`
- `Commit`
- `PullRequest`
- `Review`
- `StatusCheck`
- `ProtectionPolicy`

The repository maintains dictionaries for branches, commits, pull requests, and policies. This provides efficient identifier-based lookup for the in-memory simulation.

### Python Workflow

The example creates:

- a protected `main` branch;
- an improvement branch;
- commits representing process changes;
- a protection policy requiring two approvals;
- unit-test and security-scan checks;
- a review conversation;
- two reviewer decisions.

The first merge evaluation is blocked because one approval is not enough and a conversation remains unresolved.

After resolving the conversation and obtaining the second approval, the pull request becomes eligible and is merged.

The second scenario demonstrates stale approvals. A new source commit is added after approvals were granted. Synchronization dismisses those approvals, causing merge eligibility to fail.

### Python Validation

Validation rejects:

- unknown branches;
- duplicate commits;
- empty titles;
- identical source and target branches;
- empty source branches;
- self-approval;
- reviews without a head commit;
- invalid status checks;
- operations on inactive pull requests.

This makes failure conditions explicit rather than silently accepting inconsistent state.

## JavaScript Implementation

The JavaScript file uses Node.js standard-library functionality and an event-driven design.

`RepositoryGovernance` extends `EventEmitter`, allowing repository operations to publish events such as:

- commit added;
- policy changed;
- pull request created;
- review submitted;
- merged.

The implementation uses `Map` for repositories and branches of state, `Set` for unresolved conversations and approval identities, and asynchronous processing through a small Promise-based delay.

### JavaScript Policy Evaluation

The JavaScript implementation treats governance as an event-driven policy engine.

`evaluate()` calculates:

- current pull request state;
- draft status;
- current head;
- current approvals;
- required checks;
- unresolved conversations.

It returns a structured decision containing both eligibility and blocking reasons.

This makes the result useful to a user interface, automation service, webhook processor, or repository controller without coupling the decision to console output.

### JavaScript Security Controls

The implementation validates branch names, commit identifiers, reviewer identities, status-check names, and state transitions.

Self-approval is explicitly rejected.

Status checks are bound to the current commit SHA, preventing a successful check from an older commit from being reused after source changes.

## C++17 Implementation

The C++ implementation is a repository governance engine built around strongly typed structures and STL containers.

The main domain types are:

- `Commit`
- `Review`
- `StatusCheck`
- `Branch`
- `PullRequest`
- `BranchProtection`
- `Eligibility`

`GovernanceEngine` owns the repository state and performs validation, synchronization, policy evaluation, and merge operations.

### C++ Engineering Perspective

The implementation emphasizes explicit ownership of domain state and deterministic policy evaluation.

`std::map` provides indexed storage for branches, policies, and pull requests. `std::set` is used for required checks and unique approvers. `std::vector` represents ordered commit and review collections.

`std::optional` is used when a pull request may have no head commit.

The implementation uses exceptions for invalid repository operations and reports failure through the program's exit status.

### C++ Governance Engine

The merge engine requires:

1. an open non-draft pull request;
2. a current head commit;
3. sufficient current approvals;
4. successful required checks;
5. no unresolved conversations when required.

The stale approval example demonstrates why commit identity must be part of the review model.

## Java 17 Implementation

The Java implementation represents repository governance as an enterprise-oriented domain model.

Java records are used for immutable value types such as:

- `Commit`
- `Review`
- `StatusCheck`
- `BranchProtectionPolicy`
- `MergeDecision`

Mutable workflow entities are represented by `Branch` and `PullRequest`.

### Explicit Policy Objects

The `ReviewerEligibilityPolicy` interface separates reviewer eligibility from the main governance service.

`DefaultReviewerEligibilityPolicy` defines an explicit set of eligible reviewers and prevents the pull request author from contributing an approval.

This separation allows the governance service to evaluate policy without embedding every organization-specific reviewer rule directly into the pull request model.

### Explicit State Transitions

`PullRequestState` describes workflow state independently from `ReviewState`.

This is important because:

- `OPEN` describes pull request lifecycle;
- `CHANGES_REQUESTED` describes a review decision;
- `APPROVED` describes a review decision;
- `MERGED` describes final integration.

The service therefore avoids treating review states as pull request states.

### Java Validation

The domain model rejects invalid commit identifiers, empty messages, invalid approval requirements, unknown branches, self-approval, inactive pull requests, and merge attempts that fail governance conditions.

The use of immutable records reduces accidental mutation of policy and value objects.

## PostgreSQL Implementation

The PostgreSQL implementation turns the domain model into a relational workflow.

The schema separates:

- repositories;
- users;
- repository membership;
- branches;
- commits;
- pull requests;
- pull request commits;
- reviews;
- review comments;
- conversations;
- status checks;
- branch protection policies;
- required checks;
- merge events.

This separation avoids placing unrelated governance concepts into a single table.

### Relational Integrity

Primary keys identify entities. Foreign keys enforce relationships.

Examples include:

`pull_requests.source_branch_id → branches.branch_id`

`reviews.pull_request_id → pull_requests.pull_request_id`

`status_checks.commit_id → commits.commit_id`

`branch_protection_policies.branch_id → branches.branch_id`

These relationships prevent orphaned workflow records.

### Database Constraints

The schema uses check constraints for:

- valid commit SHA length and format;
- non-empty names;
- non-negative approval requirements;
- valid line numbers;
- valid merged-state consistency.

The `prevent_self_approval` trigger enforces a rule that should not depend only on application code.

### Merge Eligibility Function

The `merge_eligibility()` function evaluates the protected branch's policy.

It checks:

1. pull request existence;
2. open state;
3. draft state;
4. required approval count;
5. unresolved conversations;
6. required status checks.

It returns a boolean eligibility result together with a specific reason.

This makes governance evaluation queryable and auditable.

### Reporting View

`pull_request_governance_report` combines repository, branch, author, approval, conversation, and status-check information.

It supports process analysis such as:

- number of pull requests;
- merged versus unmerged changes;
- average cycle time;
- average approvals;
- unresolved conversation counts;
- successful status checks.

These metrics provide an operational foundation for continuous process improvement.

### Transactional Merge

The sample merge workflow uses a PostgreSQL transaction.

The pull request is changed to `merged` only when the eligibility function reports success. A corresponding `merge_events` record identifies the merge actor and strategy.

The transaction keeps the workflow state and audit event consistent.

## Process Improvement Measurements

A repository governance system can expose measurable signals for process improvement.

| Metric | Interpretation |
|---|---|
| Pull request cycle time | Time from proposal to merge |
| Review iteration count | Amount of rework during review |
| Approval latency | Time required to obtain required decisions |
| Unresolved conversations | Remaining review friction |
| Status-check failure rate | Automated validation instability or change quality |
| Merge-block frequency | Frequency of policy violations or incomplete work |
| Stale approval frequency | Amount of review invalidated by later changes |
| Draft duration | Time spent before a change becomes reviewable |

These metrics should be interpreted together. A lower cycle time is not automatically an improvement if review quality or failure rates deteriorate.

## Edge Cases and Failure Handling

The implementations explicitly cover several failure conditions.

| Condition | Expected behavior |
|---|---|
| Empty source branch | Pull request creation is rejected |
| Same source and target | Pull request creation is rejected |
| Self-approval | Approval is rejected |
| Draft pull request | Merge is blocked |
| Missing approval | Merge is blocked |
| Failed required check | Merge is blocked |
| Missing required check | Merge is blocked |
| Unresolved conversation | Merge is blocked when policy requires resolution |
| Changed head after approval | Previous approval becomes stale when configured |
| Closed pull request | Merge and active workflow operations are rejected |
| Invalid branch | Repository operation fails |
| Duplicate commit | Commit insertion is rejected |
| Invalid commit identifier | Validation fails |

## Performance Considerations

The in-memory implementations use hash-based or ordered collections to avoid repeatedly scanning unrelated repository state.

Approval evaluation uses unique reviewer sets so multiple approvals by the same reviewer do not inflate the approval count.

Status checks are associated with commit identifiers, allowing the evaluator to ignore results belonging to older commits.

The PostgreSQL implementation adds indexes where the workflow repeatedly filters by:

- target branch and pull request state;
- pull request, commit, and review state;
- pull request and commit for status checks;
- unresolved conversations.

Indexes should remain aligned with actual query patterns. Excessive indexing increases write cost and storage requirements.

## Security Considerations

Repository governance should enforce authorization separately from process state.

Important controls represented by the implementations include:

- preventing self-approval;
- restricting eligible reviewers;
- requiring successful security checks;
- preventing direct writes to protected branches;
- preventing force pushes where policy disallows them;
- binding approvals and checks to exact commit identities;
- retaining merge actor information;
- preserving review and conversation history.

The examples do not implement authentication or a hosting provider's authorization system. Those controls belong at the repository platform or service boundary.

## Distinguishing the Four Governance Layers

The four concepts form a dependency chain without being interchangeable.

`Pull Request`
defines the proposed change and its source and target.

↓

`Code Review`
evaluates the proposed changes and records discussion or requested changes.

↓

`Approval`
records a formal reviewer decision against a specific changeset.

↓

`Branch Protection`
enforces repository-level requirements before the target branch accepts the change.

↓

`Merge Eligibility`
combines these conditions into one decision.

This separation is essential for process improvement because each layer produces a different operational signal. A long review discussion is not the same as a missing approval. A missing status check is not the same as a reviewer requesting changes. A protected-branch violation is not the same as a defect in the proposed code.

## Practical Process Interpretation

A continuous-improvement workflow should use governance data to identify where project execution is slowing down.

For example:

`High cycle time`
→ inspect review latency

`High review latency`
→ inspect reviewer workload and scope

`Many requested changes`
→ inspect requirements and implementation quality

`Many stale approvals`
→ inspect change frequency during review

`Many failed checks`
→ inspect test stability and development feedback loops

`Many unresolved conversations`
→ inspect review clarity and ownership

This creates a measurable feedback loop between repository activity and project-process improvement without weakening technical controls.

## File Responsibilities

| File | Primary responsibility |
|---|---|
| Python | In-memory simulation of repository workflow, review decisions, stale approvals, and merge eligibility |
| JavaScript | Event-driven governance and asynchronous workflow evaluation |
| C++17 | Strongly typed repository governance and merge-decision engine |
| Java 17 | Enterprise domain model with explicit policy and reviewer-eligibility abstractions |
| PostgreSQL | Relational governance model, constraints, triggers, reporting, eligibility function, and transactional merge workflow |

The five implementations describe the same domain from different engineering perspectives while keeping pull requests, code review, approvals, and branch protection as separate technical concepts.
