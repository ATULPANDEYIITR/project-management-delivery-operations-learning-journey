# Project Milestones and Important Project Events

## Purpose

Project milestones identify significant outcomes that indicate meaningful progress rather than recording every routine activity. A milestone can represent an approved requirements baseline, completion of a major implementation, readiness for production, or a release that has satisfied its governance conditions.

The implementations in this project model milestones as explicit project entities and connect them to important repository events. Pull Requests, Code Review, Approvals, and Branch Protection are treated as related but distinct mechanisms:

- A **Pull Request** is the change-delivery workflow that proposes a changeset from a source branch toward a target branch.
- **Code Review** is the evaluation of that proposed changeset through reviews, inline comments, discussions, and requested changes.
- An **Approval** is a specific review decision indicating that an eligible reviewer accepts the current state of the proposed changes.
- **Branch Protection** is repository-level governance that determines which conditions must be satisfied before a protected branch can accept the change.
- A **Project Milestone** is a project-level outcome whose completion can be supported by those repository events.

This separation prevents a repository event from being mistaken for a project outcome. Opening a Pull Request is important evidence of implementation progress, but it is not automatically equivalent to completing the implementation milestone. Likewise, an approval is evidence from one review decision, not the same thing as the repository policy that may require several approvals.

## What Counts as an Important Project Event

An important event is an event that changes the interpretation of project progress, risk, governance, or delivery state.

Examples represented by the implementations include:

- Requirements receiving formal approval.
- An architecture or design reaching an accepted state.
- A Pull Request being opened against a protected target branch.
- A Pull Request moving from draft to review-ready state.
- Code Review producing a requested-change decision.
- An eligible reviewer granting an approval.
- A required status check failing or passing.
- A Pull Request being synchronized with new commits.
- A protected branch accepting a merge after governance conditions are satisfied.
- A production release being recorded.
- A milestone becoming blocked.
- A milestone being formally completed.

Routine events such as an arbitrary file edit do not necessarily deserve milestone-level visibility. The important-event model therefore selects events that provide useful evidence about whether a project is approaching or achieving a significant outcome.

## Milestones Versus Events

A milestone is a durable project objective. An event is evidence that something happened.

For example, `Billing Core Implementation` can be a milestone. A Pull Request opening is an event associated with that milestone. A review approval is another event. Passing the security scan is another event. The eventual merge provides stronger evidence that the implementation has passed the repository's configured delivery controls.

The milestone should not be marked complete merely because one event occurred. The Python, C++, Java, and SQL implementations enforce stronger completion conditions by checking that Pull Requests associated with the milestone have been merged.

This creates a useful relationship:

`Milestone -> supporting events -> Pull Request -> reviews and approvals -> branch-policy checks -> merge -> milestone completion`

The event stream preserves the evidence while the milestone represents the business or engineering outcome.

## Pull Request Mechanics

A Pull Request connects a source branch containing proposed changes to a target branch that will receive those changes if the repository's merge conditions are satisfied.

The data model explicitly stores:

- Source branch.
- Target branch.
- Associated project milestone.
- Pull Request number.
- Commits included in the changeset.
- Draft state.
- Conflict state.
- Review state.
- Status-check state.
- Merge state.

The source and target branches must be different. The Python, JavaScript, C++, and Java implementations validate this relationship when a Pull Request is created.

A Pull Request may begin as a draft. A draft communicates that the author is still developing the changes and does not yet expect normal merge evaluation. The implementations therefore reject a draft Pull Request during merge-eligibility evaluation.

A Pull Request can later become ready for review. At that point, the repository workflow can evaluate its review, approval, status-check, conflict, and branch-protection conditions.

The changeset is represented by the commits attached to the Pull Request. Synchronizing the Pull Request means incorporating additional changes into the proposed changeset. This is significant for milestone tracking because the state that reviewers approved may no longer be identical to the state after synchronization.

A new commit can therefore make an earlier approval stale when the configured repository policy dismisses stale approvals. The JavaScript and Java implementations explicitly model this behavior, while the Python and C++ implementations also demonstrate approval invalidation after synchronization.

### Pull Request lifecycle represented by the implementations

`draft -> review-ready -> reviewed -> approved -> checks passed -> merge eligible -> merged`

The lifecycle is not purely linear. A Pull Request can move backward from an apparently approved state when new commits invalidate approvals. It can also become blocked by conflicts, requested changes, failed checks, or unresolved review discussions.

A closed Pull Request is not equivalent to a merged Pull Request. For milestone accounting, the implementations use the stronger condition of `merged` before allowing a milestone to be completed.

## Code Review

Code Review evaluates the actual changes proposed by a Pull Request.

The review model distinguishes three states:

- `APPROVED` means the reviewer accepts the current changeset.
- `CHANGES_REQUESTED` means the reviewer believes modification is required before the change should proceed.
- `COMMENTED` represents discussion or feedback without granting approval.

Review comments are attached to a review and can remain unresolved. An approval with unresolved review discussions is therefore not treated as an effective approval by the merge-eligibility logic.

This is important because approval and discussion resolution answer different questions. A reviewer may approve a Pull Request while another comment remains unresolved, or a later review may request changes. Branch policy can require all review conversations to be resolved before merge.

The review implementations track comment counts and resolution state instead of reducing Code Review to a Boolean flag.

### Review quality criteria

A useful review process evaluates the actual changeset rather than merely checking that a review record exists. The examples therefore distinguish:

- Whether a reviewer submitted a review.
- Which review state was submitted.
- Whether comments remain unresolved.
- Whether changes were requested.
- Whether the reviewer granted approval.
- Whether the approval remains valid for the current changeset.

This allows a project milestone to use review events as evidence without confusing the existence of a review with successful review completion.

### Review failure modes

A Pull Request can remain unmergeable when:

- A reviewer has requested changes.
- Review discussions remain unresolved.
- The required number of approvals has not been reached.
- A previously granted approval became stale after new commits.
- A review is dismissed.
- A reviewer is not eligible under the repository's governance policy.

These are review-specific conditions. Branch protection can enforce some of them, but the review system itself records the underlying decisions and discussions.

## Approvals

An approval is a review decision, not merely the presence of a reviewer.

The implementations count active approvals using reviewers whose current review state is `APPROVED` and whose associated review discussions are resolved.

The approval model therefore considers both decision state and discussion state.

For example, a Pull Request can have two reviewers but zero effective approvals if both reviewers only leave comments. It can also have two approvals but fail merge eligibility if the repository requires three approvals.

Approval requirements are repository-policy rules. The Pull Request contains the current review decisions, while Branch Protection determines how many eligible approvals are necessary.

### Stale approvals

A particularly important relationship exists between new commits and old approvals.

Suppose two reviewers approve a Pull Request. The author then pushes a new commit that changes the implementation. The approval may no longer represent the code currently under consideration.

When `dismiss_stale_approvals` is enabled, synchronization changes existing approvals into a non-approval state in the JavaScript and Java implementations. The Python and C++ implementations model the same governance idea.

This prevents a project milestone from being considered review-complete based on approval of an older changeset.

### Required reviews

The SQL branch-protection model stores the number of required approvals independently from individual review records.

This separation is deliberate:

`reviews` answer what reviewers decided.

`branch_protection_policies.required_approvals` answers how many valid decisions the repository requires.

That distinction is essential when repository governance changes without rewriting historical review records.

## Branch Protection

Branch Protection controls what may happen to a protected target branch.

The model includes policy fields for:

- Required approvals.
- Required status checks.
- Conversation resolution.
- Restrictions on direct pushes.
- Force-push restrictions.
- Branch deletion restrictions.
- Linear-history requirements.
- Stale-approval dismissal.

A protected branch therefore becomes a governance boundary between proposed project work and accepted repository history.

The Pull Request itself does not decide whether a merge is permitted. The merge-eligibility service evaluates the Pull Request against the policy attached to its target branch.

### Required status checks

Status checks provide automated evidence about the changeset.

The example repository requires:

- `unit-tests`
- `integration-tests`
- `security-scan`

A passing review does not override a failed required check. Likewise, passing all automated checks does not substitute for required human approvals.

The resulting merge decision is conjunctive:

`merge eligible = review conditions AND approval conditions AND status checks AND conflict conditions AND policy conditions`

### Direct pushes

A protected branch may restrict direct pushes so that project changes must enter through the governed Pull Request path.

This makes the Pull Request lifecycle relevant to milestone identification. A project milestone can use the merged Pull Request as evidence that the implementation crossed the repository governance boundary.

### Force pushes and deletion

Force-push restrictions protect the stability of protected branch history. Branch deletion restrictions protect the continued existence of important project integration points.

These controls do not constitute Code Review themselves. They are repository governance rules that constrain operations on important branches.

### Linear history

The data model includes a linear-history requirement because some repositories use it to constrain merge strategies and history structure.

It is distinct from approval. A reviewer can approve a Pull Request while a linear-history policy can still reject the merge if the resulting history violates repository policy.

### Administrator and bypass behavior

The implementations model ordinary policy enforcement and explicitly avoid treating administrative privileges as an automatic substitute for milestone evidence.

A production governance system may provide narrowly controlled bypass mechanisms for emergencies. If bypasses are allowed, they should themselves be recorded as important project events because bypassing a protection rule changes the governance evidence surrounding the milestone.

## Architecture of the Python Implementation

The Python implementation uses a `MilestoneTracker` as the central project workflow object.

`Milestone` stores project-level objectives, target dates, importance, dependencies, and lifecycle status.

`ProjectEvent` stores the event stream that provides evidence for milestone progress.

`PullRequest` models the proposed changeset, branches, commits, review state, status checks, conflicts, and merge state.

`Review` models reviewer identity, review state, and discussion resolution.

`BranchProtection` represents repository governance rules.

The tracker connects these objects without collapsing their responsibilities.

The implementation demonstrates dependency-aware milestone activation. A milestone cannot become active while its required predecessor milestones remain incomplete.

It also prevents completion when associated Pull Requests remain unmerged. This makes milestone completion an explicit state transition rather than a cosmetic label.

The `important_events()` method filters the event stream so that project reporting focuses on significant events rather than every internal operation.

## Python Workflow

The Python scenario uses a payment-platform modernization project.

The requirements milestone is completed after requirements approval. The implementation milestone then becomes active. A Pull Request is created from `feature/payment-service` into `main`.

The Pull Request initially contains three commits and is configured as a draft. It later becomes review-ready.

One engineer approves the Pull Request while another initially leaves a comment with an unresolved discussion. Merge evaluation correctly identifies the unresolved review condition.

After the security reviewer resolves the discussion and grants approval, the required status checks pass. The Pull Request becomes merge-eligible and is merged.

The implementation milestone can then be completed, allowing the production-release milestone to become active.

This demonstrates how important events create an evidence trail around milestone state transitions.

## JavaScript Implementation

The JavaScript implementation uses an event-driven design.

`EventBus` demonstrates how project systems can react to significant events without embedding every notification or reporting action directly into the state-transition code.

`ProjectMilestoneEngine` coordinates milestones, Pull Requests, branch policies, reviews, and event recording.

The JavaScript implementation is particularly focused on event-driven behavior. When a merge or milestone-completion event occurs, registered handlers can immediately observe it.

`PullRequest` maintains status checks and reviews, while `Review` owns review-specific state. `BranchProtectionPolicy` contains repository-level rules.

The implementation also demonstrates JavaScript collection types such as `Map` and `Set` for status checks, milestones, Pull Requests, dependencies, and unique approvers.

## C++ Governance Case Study

The C++ program presents an enterprise billing modernization repository.

The central `RepositoryGovernanceEngine` manages project milestones, Pull Requests, branch protection policies, and project events.

The case study uses a protected `main` branch and requires two approvals plus three automated checks:

`unit-tests`

`integration-tests`

`security-scan`

The Pull Request begins in draft state and is later made ready for review.

The first review is approved, while the second reviewer initially leaves an unresolved comment. The engine consequently rejects the first merge evaluation.

After the second reviewer approves with all discussion resolved and the required automated checks pass, the engine permits the merge.

The milestone can then be completed because the associated Pull Request is merged.

### C++ design decisions

The program uses `std::map` for keyed repository objects and `std::set` for unique approval identities and protected-policy collections.

The `approvalCount()` function uses reviewer identity rather than raw review count. This prevents duplicate reviews from the same reviewer from artificially satisfying an approval threshold.

`evaluateMergeEligibility()` returns both a Boolean decision and explicit failure reasons. This is more useful than returning only `true` or `false because project governance needs to explain why a milestone-related delivery event is blocked.

The C++ implementation also uses exceptions for invalid state transitions and invalid repository data.

## Java Enterprise Model

The Java implementation models repository governance using explicit domain objects and service-oriented state management.

`Milestone` owns milestone lifecycle transitions.

`Review` owns review decisions and comment resolution.

`PullRequest` owns changeset-related state.

`BranchProtectionPolicy` represents repository-level merge requirements.

`RepositoryGovernanceService` evaluates relationships among those entities.

The use of records for immutable event and policy representations prevents accidental modification of historical event metadata.

The service uses a `MergeDecision` object rather than returning a simple Boolean. This provides both the decision and the reasons for failure.

The Java implementation also models stale approval dismissal during Pull Request synchronization. When new commits arrive and the branch policy requires stale approvals to be dismissed, previous approvals are converted away from active approval state.

This behavior is important for milestone identification because an approval must correspond to the current changeset.

## SQL Data Model

The PostgreSQL implementation stores the governance model relationally.

`projects` identifies the project itself.

`repositories` associates source repositories with projects.

`repository_branches` stores source and target branch identities.

`project_milestones` stores important project outcomes.

`milestone_dependencies` models dependencies between milestones.

`commits` stores changeset history.

`pull_requests` represents proposed changes between branches.

`pull_request_commits` connects individual commits to Pull Requests in sequence order.

`reviewers` stores reviewer identities and roles.

`reviews` records review decisions.

`review_comments` stores review discussions and resolution state.

`status_checks` records automated validation.

`branch_protection_policies` stores repository-level governance.

`required_status_checks` identifies checks that must pass for a protected branch.

`project_events` creates the project event stream.

This separation keeps milestone state distinct from Pull Request state, review state, approval state, and branch policy.

## Database-Level Enforcement

The SQL schema uses constraints where the database can enforce a rule reliably.

Primary keys prevent duplicate entity identities.

Foreign keys prevent references to missing projects, repositories, milestones, branches, Pull Requests, reviewers, or reviews.

Unique constraints prevent duplicate repository names, branch names within repositories, Pull Request numbers within repositories, and commit hashes.

Check constraints validate importance ranges, review-comment resolution state, and Pull Request branch relationships.

The milestone completion trigger provides a stronger business rule: a milestone cannot be completed while a related Pull Request remains unmerged.

This rule belongs close to the data because milestone completion must remain valid even when multiple applications or administrative processes write to the database.

## Important SQL Queries

The `important_project_events` view provides a project-level event feed filtered to significant event types.

The `pull_request_review_state` view calculates active approvals, requested changes, and unresolved review comments for each Pull Request.

The `milestone_progress` view combines milestone state with event and Pull Request evidence.

The final queries expose:

- Milestone progress.
- Important project events.
- Review state.
- Schedule state.
- Approval and merge evidence.
- High-importance milestone activity.

These views allow project reporting to be based on stored evidence rather than manually maintained status fields.

## Merge Eligibility as a Governance Relationship

Merge eligibility is not one of the same concepts as a milestone.

A milestone asks:

`Has the project achieved the required outcome?`

A Pull Request asks:

`What changes are being proposed for integration?`

Code Review asks:

`Have qualified reviewers evaluated those changes?`

Approval asks:

`Has an eligible reviewer accepted the current changeset?`

Branch Protection asks:

`What conditions must be satisfied before this target branch accepts the change?`

Merge eligibility combines the answers.

This relationship is the central architectural distinction represented across the implementations.

## Milestone Dependencies

A milestone can depend on another milestone.

For example:

`Requirements Baseline -> Billing Core Implementation -> Production Release`

The implementation milestone should not become active before the requirements milestone is complete.

Similarly, the production milestone should not become active before the implementation milestone is complete.

Dependencies make milestone status meaningful because the system can reject an apparently reasonable state transition when prerequisite work has not been completed.

## Important Edge Cases

### Draft Pull Request

A draft Pull Request indicates that the changeset is not yet ready for normal merge evaluation. The implementations reject it as merge-eligible until it becomes ready.

### Merge Conflict

A Pull Request containing conflicts cannot be considered merge-ready. Conflict resolution is separate from Code Review because a reviewer may have approved code that later conflicts with the target branch.

### Requested Changes

A single active review requesting changes can block merge eligibility even when another reviewer has approved the Pull Request.

### Unresolved Review Conversation

An approval does not automatically resolve every discussion. When the repository requires conversation resolution, unresolved comments remain a merge blocker.

### Failed Status Check

Automated checks can prevent merge even when every required reviewer has approved.

### Stale Approval

A new commit can invalidate previous approval when the repository policy dismisses stale approvals.

### Duplicate Approval

Counting raw review rows can incorrectly inflate approval counts. The implementations instead count unique reviewers with valid active approvals.

### Unmerged Pull Request

A milestone with an unmerged associated Pull Request cannot be completed in the provided governance model.

### Missing Branch Policy

The examples treat the absence of a protection policy as a merge-governance failure rather than silently assuming that the branch is safe.

## Common Modeling Mistakes

A common mistake is treating the milestone status as the only source of truth. A milestone marked `completed` without supporting events and delivery evidence provides weak auditability.

Another mistake is treating a Pull Request as synonymous with a milestone. A Pull Request represents a changeset workflow; a milestone represents an outcome.

Another mistake is treating any review as an approval. A `COMMENTED` review is not an approval, and a `CHANGES_REQUESTED` review indicates an explicit blocker.

Another mistake is counting approvals without considering whether the approval belongs to the current changeset.

Another mistake is implementing branch protection only in the user interface. Repository governance must be enforced at the actual merge boundary.

Another mistake is recording only the final state. A project event timeline is useful because it shows how the final state was reached and which events created blockers or evidence.

## Performance Considerations

Event queries should normally be indexed by project, milestone, and timestamp because project dashboards frequently ask for recent milestone activity.

Pull Request queries should be indexed by milestone and status because project reporting often needs to determine whether all changes associated with a milestone have reached a merged state.

Review queries should be indexed by Pull Request and review state because merge evaluation repeatedly needs to determine active approvals and requested changes.

Review-comment resolution should be indexed because unresolved discussion checks can otherwise become expensive as review history grows.

The SQL implementation therefore creates indexes around the principal governance access paths rather than indexing every column indiscriminately.

## Security Considerations

Reviewer identity must be authoritative. A production implementation should not accept arbitrary reviewer names from an untrusted client when determining whether an approval satisfies repository policy.

Branch protection configuration should be restricted to authorized repository administrators or governance roles.

Merge eligibility should be evaluated using server-side policy data rather than a client-provided Boolean.

Project events should be append-oriented and auditable. Historical event records should not be casually rewritten because the event history can provide evidence for why a milestone was considered complete.

Administrative bypasses should produce explicit events so that emergency exceptions remain visible in project governance records.

Secrets, access tokens, repository credentials, and private authentication data do not belong in milestone event payloads.

## Debugging and Auditability

A useful debugging strategy is to inspect the event sequence before inspecting the final milestone state.

For example, if a milestone appears blocked, the event stream can reveal whether the cause was a failed status check, requested changes, unresolved review discussions, stale approvals, merge conflicts, or another policy condition.

The merge-evaluation methods in the Python, C++, and Java implementations return explicit failure reasons. This makes a governance failure diagnosable rather than producing an unexplained `false`.

The SQL views provide a similar diagnostic surface by exposing approval counts, unresolved comments, Pull Request states, and milestone progress.

## Production Considerations

A production implementation would normally connect repository events to an authoritative source rather than relying on manually generated events.

Milestone identifiers should remain stable so that Pull Requests, releases, deployments, and events can be associated with the same project outcome over time.

Event timestamps should use a consistent timezone-aware representation. The Python implementation uses `datetime`, Java uses `Instant`, C++ uses `system_clock`, and PostgreSQL uses `TIMESTAMPTZ`.

Historical review decisions should remain distinguishable from current approval state. A review that was once approved but later dismissed should not disappear from the audit history.

Repository governance policies should be versioned when policy changes are significant. Otherwise, it can become difficult to determine which approval requirement applied when a historical merge occurred.

The strongest project milestone evidence combines milestone state with an auditable sequence of requirement approval, implementation activity, review, approval, automated validation, protected-branch merge, and release events.
