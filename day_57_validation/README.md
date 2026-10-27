# Project Management Change Governance

## Scope

This project models controlled change management inside a software-oriented project environment. The central relationship is:

Project Repository
→ Branches
→ Commits
→ Pull Requests
→ Code Reviews
→ Review Conversations
→ Approval Decisions
→ Status Checks
→ Branch Protection
→ Merge Eligibility
→ Merge

The four governance areas are intentionally distinct:

| Area | Primary purpose | Main question |
|---|---|---|
| Pull Requests | Propose and coordinate a change | What change is being proposed? |
| Code Review | Evaluate the proposed change | What technical or quality concerns exist? |
| Approvals | Record formal review decisions | Has an eligible reviewer accepted the current revision? |
| Branch Protection | Enforce repository-level governance | Are all mandatory conditions satisfied before merge? |

The implementations use the same domain relationships while emphasizing different engineering approaches.

## Pull Requests

A Pull Request is the controlled workflow object for moving a proposed change from a source branch toward a target branch.

A Pull Request records:

- Source branch
- Target branch
- Author
- Title
- Proposed commits
- Current revision
- Draft status
- Review state
- Status-check results
- Merge conflicts
- Base-branch synchronization
- Final lifecycle state

The lifecycle represented by the implementations is:

`Draft → Open → In Review → Approved → Merged`

A change can also move into `Changes Requested` or `Closed`.

A draft Pull Request allows work to be coordinated before requesting final review. Once the work is ready, it can enter the review workflow.

Base synchronization matters because a proposed change can become incompatible with the current target branch. A conflict blocks merge eligibility until the source branch is synchronized and the conflict is resolved.

Adding a new commit creates a new revision of the proposed change. Existing approvals may no longer describe the current state of the change and are therefore treated as stale.

## Code Review

Code review evaluates the actual proposed changes rather than enforcing repository-level policy.

A review can contain:

- Reviewer identity
- Review state
- Revision reviewed
- Inline or discussion comments
- Resolved or unresolved conversations
- Review timestamps

The supported review states are:

| State | Meaning |
|---|---|
| Commented | Feedback was provided without a final approval decision |
| Approved | Reviewer accepts the reviewed revision |
| Changes Requested | Reviewer requires modification |
| Dismissed | Existing review decision is no longer active |

Review quality depends on scope and evidence. A reviewer should evaluate the change represented by the revision being reviewed rather than assuming that a later revision is unchanged.

The source implementations deliberately associate reviews with revisions. When a new commit is added after approval, the earlier approval cannot automatically be treated as approval of the new content.

Review conversations provide a second layer of review state. A Pull Request may have technically valid approvals while still containing unresolved review discussions. Branch protection can make resolution of those discussions a merge prerequisite.

## Approvals

An approval is a formal decision by an eligible reviewer.

Approval semantics are different from ordinary review comments. A comment communicates feedback; an approval provides a positive decision that can contribute toward a merge requirement.

The implementations enforce several approval controls:

- The Pull Request author cannot approve the author's own change.
- Reviewers must have an eligible project or repository role.
- Only active reviewers are considered.
- Dismissed approvals do not count.
- Approvals must correspond to the current Pull Request revision.
- The required number of approvals is evaluated against eligible reviewers.
- A new revision makes previous approvals stale.

For example, suppose a project requires two approvals:

`Revision 1 → Reviewer A approves → Reviewer B approves`

If the contributor then adds another commit:

`Revision 2 → previous approvals describe Revision 1`

The governance engine therefore reports the Pull Request as blocked until the current revision receives the required approvals.

This prevents an approval for one state of a project change from silently authorizing a materially different state.

## Branch Protection

Branch protection is repository-level enforcement. It does not replace review and it does not constitute an approval.

A protected branch can require:

- Minimum number of approvals
- Specific status checks
- Resolved review conversations
- Restrictions on direct pushes
- Restrictions on force pushes
- Restrictions on branch deletion
- Linear history
- Controlled administrator bypass behavior

The protected branch represents the final enforcement boundary.

The distinction is:

`Pull Request`
→ proposes the change

`Code Review`
→ evaluates the change

`Approval`
→ records an eligible reviewer's decision

`Branch Protection`
→ determines which repository-level conditions must be satisfied

`Merge Eligibility`
→ evaluates the combined state

`Merge`
→ executes the authorized repository transition

## Status Checks

Automated checks represent machine-evaluated conditions associated with the proposed change.

The examples use checks such as:

- `scope-validation`
- `security-validation`
- `quality-gate`
- `unit-tests`
- `project-validation`

A check can be:

- `pending`
- `passed`
- `failed`

A required check that is missing is treated differently from a check that exists but failed. Both block the merge, but the distinction is useful for operational diagnosis.

The PostgreSQL model stores status checks independently from reviews so that automated evidence is not confused with human approval.

## Merge Eligibility

Merge eligibility is a derived decision rather than a manually stored assumption.

A simplified evaluation is:

`Draft?`
→ `Conflicts?`
→ `Base synchronized?`
→ `Required approvals?`
→ `Required checks?`
→ `Open conversations?`
→ `Protected branch rules?`
→ `Eligible`

A Pull Request is eligible only when every mandatory condition is satisfied.

Typical blocking conditions include:

| Condition | Effect |
|---|---|
| Draft | Blocks final merge |
| No commits | Blocks merge |
| Merge conflict | Blocks merge |
| Unsynchronized base | Blocks merge |
| Insufficient approvals | Blocks merge |
| Stale approvals | Blocks merge |
| Failed required check | Blocks merge |
| Missing required check | Blocks merge |
| Unresolved conversation | Can block merge |
| Protected-branch violation | Blocks direct or unauthorized modification |

The Python, JavaScript, C++17, and Java implementations calculate this decision in application memory. PostgreSQL calculates related governance information directly from relational data.

## Python Implementation

The Python implementation provides a complete domain simulation using dataclasses and enums.

Important structures include:

- `User`
- `Commit`
- `Review`
- `ReviewComment`
- `StatusCheck`
- `Branch`
- `PullRequest`
- `BranchProtectionPolicy`
- `GovernanceEngine`

The `PullRequest` class controls lifecycle transitions and validates invalid operations such as adding commits after completion or entering review without commits.

The `GovernanceEngine` separates eligibility evaluation from the Pull Request data model. This keeps repository policy independent from the change object.

The example first demonstrates a successful two-reviewer merge. It then creates a second Pull Request where approvals were issued before a new revision. The new revision makes the previous approval state insufficient.

The script also uses assertions to verify the expected failure condition.

## JavaScript Implementation

The JavaScript implementation uses an event-driven model.

`ProjectChange` extends `EventEmitter`, allowing workflow events such as:

- Commit added
- Review requested
- Review submitted
- Conversation opened
- Conversation resolved
- Status changed

The implementation uses `Map` and `Set` for review, status-check, and conversation management.

Asynchronous status validation is represented with `Promise.all`. Several independent project validation checks can therefore execute concurrently.

The JavaScript implementation treats approvals as stale when a new commit is introduced. This state is stored directly on each review and evaluated by `MergeEvaluator`.

The event-driven design is useful when a project management system needs to notify dashboards, audit services, workflow engines, or other components when a governance state changes.

## C++17 Implementation

The C++17 program implements a repository governance and merge-eligibility engine using strongly typed enumerations, structures, STL containers, and exception handling.

The main domain objects are:

- `User`
- `Commit`
- `Review`
- `StatusCheck`
- `BranchProtection`
- `Branch`
- `PullRequest`
- `GovernanceEngine`

The key design choice is revision-specific approval.

A review stores `revisionReviewed`. The merge evaluator compares that value with the Pull Request's `currentRevision`.

This makes approval validity an explicit state comparison rather than a boolean flag.

The program also separates eligibility evaluation from merge execution. The evaluator returns all blocking reasons, while the merge operation refuses to execute when any policy violation remains.

The example demonstrates both a successful governance decision and a stale-approval failure.

## Java 17 Implementation

The Java implementation represents an enterprise-oriented project governance service.

Java records are used for immutable value-oriented objects such as:

- `User`
- `Commit`
- `Review`
- `ReviewComment`
- `StatusCheck`
- `Branch`
- `ReviewPolicy`
- `EligibilityResult`

The mutable `PullRequest` aggregate owns lifecycle behavior, while `MergeEligibilityService` evaluates policy and `ProjectWorkflowService` performs the merge operation.

This separation represents a service-oriented enterprise design:

`PullRequest`
→ domain state

`MergeEligibilityService`
→ policy evaluation

`ProjectWorkflowService`
→ workflow execution

Custom `GovernanceException` handling makes invalid workflow transitions explicit.

The Java implementation also demonstrates immutable collection exposure through `List.copyOf`, preventing callers from directly modifying internal review state.

## PostgreSQL Implementation

The PostgreSQL implementation models the governance system relationally.

Core tables include:

| Table | Purpose |
|---|---|
| `app_user` | Project and repository participants |
| `repository` | Repository ownership and identity |
| `branch` | Repository branch state |
| `commit_record` | Commit history |
| `pull_request` | Proposed changes |
| `pull_request_commit` | Pull Request changeset membership |
| `review` | Reviewer decisions |
| `review_comment` | Review discussions |
| `status_check` | Automated validation |
| `branch_protection_policy` | Protected branch rules |
| `required_status_check` | Mandatory automated checks |
| `merge_event` | Successful merge audit record |

Database constraints enforce structural correctness.

Examples include:

- Unique repository names
- Unique branch names per repository
- Unique Pull Request numbers per repository
- Valid review states
- Valid status-check states
- Non-negative approval requirements
- Valid commit message length
- Source and target branch distinction

The review trigger prevents self-approval and rejects reviewers who do not hold an eligible role.

The `merge_eligibility_report` view provides an operational reporting surface showing current approvals, required approvals, unresolved comments, branch state, and revision information.

The SQL also includes a transactional merge example. The transaction evaluates the required approval state, changes the Pull Request to `merged`, and records a `merge_event`.

## Failure Handling

The project intentionally models failure as part of governance rather than treating it as an exceptional afterthought.

Representative failure states include:

- Self-approval
- Missing commits
- Draft changes submitted for final review
- Invalid reviewer role
- Failed status check
- Missing status check
- Merge conflict
- Unsynchronized target state
- Unresolved review conversations
- Stale approval
- Closed Pull Request modification
- Protected branch direct modification

A governance system should expose the reason for a blocked operation. Returning only `false` would make operational diagnosis difficult.

The application implementations therefore collect specific failure reasons before refusing a merge.

## Security Controls

The implementations treat repository governance as an authorization boundary.

Important controls include:

- Separation of contributor and reviewer roles
- Prevention of self-approval
- Protected branch restrictions
- Required status checks
- Required approvals
- Review dismissal handling
- Stale approval invalidation
- Transactional merge recording
- Audit-oriented merge events
- Database constraints and triggers

Role membership alone is not sufficient for merge authorization. The current revision, review state, repository policy, automated checks, and branch state must also satisfy the policy.

Administrator bypass is represented as a policy attribute but is disabled in the demonstrated protected-branch configuration. This makes bypass behavior an explicit governance decision rather than an implicit privilege.

## Performance Considerations

The application implementations use maps and sets where membership and lookup operations are frequent.

Examples include:

- Reviewer lookup
- Approval membership
- Status-check lookup
- Open conversation tracking

The PostgreSQL implementation indexes the most important access patterns:

- Pull Requests by target branch and state
- Reviews by Pull Request, state, and revision
- Status checks by Pull Request and state
- Unresolved review comments

The approval calculation uses distinct reviewer identities so that multiple approved comments from the same reviewer do not incorrectly satisfy multiple approval requirements.

The data model favors explicit relationships over duplicated state. This reduces the risk of contradictory approval and review records.

## Project Management Interpretation

Although the technical examples use repository terminology, the governance model maps directly to controlled project work.

| Technical object | Project management interpretation |
|---|---|
| Repository | Controlled project workspace |
| Branch | Parallel workstream |
| Commit | Traceable work increment |
| Pull Request | Formal change proposal |
| Review | Structured quality evaluation |
| Approval | Formal acceptance decision |
| Status Check | Automated validation gate |
| Branch Protection | Governance policy |
| Merge Eligibility | Release/change authorization decision |
| Merge Event | Auditable implementation event |

The important distinction is that a project change can be technically complete without being governance-complete.

For example:

`Implementation complete`
does not necessarily mean
`Approved for integration`.

Likewise:

`Approved by reviewers`
does not necessarily mean
`Eligible for merge`

because branch protection may still require status checks, resolved conversations, synchronization, or other repository-level conditions.

## Validation Requirements

The implementation satisfies the following validation areas:

| Validation | Confirmed mechanism |
|---|---|
| Pull Request lifecycle | Explicit states and transitions |
| Source and target branches | Branch references |
| Changesets | Commit-to-Pull Request relationships |
| Review requests | Review lifecycle |
| Conversations | Review comments and resolution state |
| Status checks | Explicit automated check records |
| Merge conflicts | Pull Request conflict state |
| Base synchronization | Explicit synchronization state |
| Reopening and closing | Lifecycle state model |
| Review decisions | Typed review states |
| Approval eligibility | Role and active-user validation |
| Stale approvals | Revision comparison |
| Dismissed approvals | Explicit dismissal state |
| Required reviews | Branch protection policy |
| Direct-push restrictions | Protected branch policy |
| Force-push restrictions | Protected branch policy |
| Deletion restrictions | Protected branch policy |
| Required conversations | Unresolved-comment validation |
| Merge restrictions | Eligibility service and database workflow |
| Auditability | Merge event records |

## Practical Workflow

A controlled project change can be represented as:

`Developer creates workstream`
→ `Commits implementation`
→ `Opens Pull Request`
→ `Reviewers inspect revision`
→ `Review conversations are resolved`
→ `Required approvals are recorded`
→ `Automated checks pass`
→ `Branch protection evaluates policy`
→ `Merge eligibility is confirmed`
→ `Merge is recorded`

A new commit returns the change to a state requiring renewed evaluation.

This prevents a project decision from being detached from the actual revision that was reviewed.

## Limitations

The implementations model governance mechanics rather than a complete hosted source-control platform.

They do not attempt to reproduce:

- Network-based repository synchronization
- Actual Git object storage
- Remote authentication protocols
- Webhook delivery infrastructure
- Full CI/CD orchestration
- Distributed locking
- Enterprise identity federation
- Repository hosting APIs
- Complete administrator audit infrastructure

The focus is the project-management governance model connecting proposed changes, review decisions, automated validation, policy enforcement, and merge authorization.
