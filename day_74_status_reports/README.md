# Project Status Reporting: Design, Implementation and Governance

## 1. Project Status Reporting

Project status reporting is the structured process of collecting, validating, analyzing, and communicating information about a project's current condition.

A project status report converts operational information into a management-level view of delivery progress, schedule performance, expenditure, risks, dependencies, and outstanding decisions.

The purpose is not simply to describe completed activities. A useful report identifies deviations from the approved project baseline, explains their consequences, and makes management intervention possible.

The implementation models an enterprise reporting environment in which project execution and software repository governance contribute to the same delivery picture.

### 1.1 Information dimensions

| Dimension | Information monitored | Management purpose |
|---|---|---|
| Schedule | Start date, target date, remaining time | Identify schedule deviations |
| Delivery | Tasks, owners, completion, blocked work | Measure execution |
| Milestones | Planned and completed milestones | Monitor major deliverables |
| Financials | Budget, expenditure, variance | Control project costs |
| Risks | Probability, impact, mitigation | Identify threats |
| Issues | Blocked tasks and unresolved discussions | Identify immediate obstacles |
| Dependencies | Work requiring other activities | Detect delivery constraints |
| Governance | Reviews, approvals, checks, branch policies | Monitor software delivery controls |
| Reporting history | Previous reporting periods | Identify trends |

A report should distinguish observed facts from forecasts, assumptions, and management assessments. A calculated status indicator is not a substitute for an explanation of the underlying evidence.

## 2. Project Status and Health Classification

The implementations use five principal health classifications.

| Classification | Meaning |
|---|---|
| Not Started | No meaningful execution has begun |
| On Track | Current indicators do not identify a major delivery threat |
| At Risk | A material risk, blocker, or dependency requires attention |
| Delayed | A significant schedule or financial condition indicates a delay |
| Completed | All tracked tasks have reached completion |

The classification logic uses several independent indicators:

- Task completion.
- High-priority blocked activities.
- Active high-exposure risks.
- Budget utilization.
- Target-date position.

The Python, JavaScript, C++, and Java implementations use the current date when evaluating remaining schedule time in their report models where applicable. The SQL reporting procedure evaluates delivery, risks, and financial conditions.

A production implementation should also compare actual delivery against a dated baseline. A project with 70% completion is not necessarily healthy if it was expected to be 90% complete.

### 2.1 Delivery completion

The task-based completion measure is:

\[
Completion(\%) =
\frac{Completed\ Tasks}{Total\ Tasks}\times100
\]

For five tasks, two completed tasks produce:

\[
Completion = \frac{2}{5}\times100 = 40\%
\]

This is a count-based indicator. It assumes that tasks have comparable significance.

For projects with highly unequal task sizes, weighted completion is more appropriate:

\[
Weighted\ Completion =
\frac{\sum_i w_i c_i}{\sum_i w_i}\times100
\]

Where:

- \(w_i\) represents the approved task weight.
- \(c_i\) equals 1 for completed work and 0 otherwise.

A weighted model should use approved estimates or another consistent baseline rather than changing weights after observing actual progress.

### 2.2 Milestone completion

\[
Milestone\ Completion =
\frac{Completed\ Milestones}{Total\ Milestones}
\times100
\]

Milestone completion and task completion are separate measurements.

A project may complete numerous small tasks without completing a major contractual milestone.

### 2.3 Schedule monitoring

The remaining-time indicator is:

\[
Remaining\ Days = Target\ Date - Current\ Date
\]

A negative value indicates that the target date has passed.

This indicator does not independently measure schedule performance. Actual schedule variance requires comparison between baseline and actual or forecast dates.

A more advanced reporting system can incorporate:

- Planned Value (PV).
- Earned Value (EV).
- Actual Cost (AC).
- Schedule Performance Index (SPI).
- Cost Performance Index (CPI).

The standard earned-value relationships are:

\[
SPI = \frac{EV}{PV}
\]

\[
CPI = \frac{EV}{AC}
\]

Values below 1 indicate unfavorable schedule or cost performance relative to the baseline.

These indicators require reliable work-package weights, approved budgets, and consistent earned-value measurement rules. They are not inferred from simple task counts.

## 3. Financial Status Reporting

Financial reporting compares approved project expenditure with actual expenditure.

### 3.1 Budget variance

\[
Budget\ Variance = Actual\ Cost - Approved\ Budget
\]

A positive result indicates expenditure above the approved budget.

A negative result indicates expenditure below the approved budget.

### 3.2 Budget utilization

\[
Budget\ Utilization =
\frac{Actual\ Cost}{Approved\ Budget}\times100
\]

The example project uses:

| Financial indicator | Amount |
|---|---:|
| Approved budget | 500,000 |
| Actual expenditure | 185,000 |
| Remaining budget | 315,000 |
| Budget utilization | 37% |
| Budget variance | -315,000 |

Remaining budget is calculated as approved budget minus actual expenditure.

Budget utilization must not be interpreted as project completion. Spending 37% of the budget does not imply that 37% of the deliverables have been completed.

A mature financial reporting system should distinguish:

- Approved budget.
- Committed expenditure.
- Actual expenditure.
- Accrued expenditure.
- Forecast expenditure.
- Estimate at Completion (EAC).
- Estimate to Complete (ETC).

Committed costs and actual payments are different financial events. They should not be combined without a documented accounting rule.

## 4. Task and Milestone Management

Tasks represent individual units of project work.

Each task has:

- Unique identifier.
- Description.
- Assigned owner.
- Priority.
- Workflow state.
- Estimated effort.
- Actual effort.
- Planned dates.

The task state model is:

`TODO → IN_PROGRESS → COMPLETED`

A task can also enter `BLOCKED` when a dependency, technical problem, resource constraint, or external decision prevents execution.

Blocked work must remain visible in management reports. Treating blocked tasks as ordinary in-progress work hides delivery constraints.

### 4.1 Task validation

The implementations validate:

- Non-empty task identifiers.
- Valid ownership.
- Positive estimated effort.
- Non-negative actual effort.
- Valid priority.
- Valid workflow state.
- Unique identifiers where the application maintains collections.

The PostgreSQL schema enforces corresponding relational constraints.

Actual hours exceeding estimated hours are not automatically invalid. They represent a potentially important variance that should be reported and investigated.

### 4.2 Milestone management

Milestones represent major project outcomes rather than individual work activities.

Examples include:

- Requirements approval.
- Database completion.
- System testing.
- Production deployment.

A milestone should have a planned date, completion state, and recorded completion date.

The SQL schema enforces consistency between the completion flag and completion timestamp.

This prevents a milestone from being recorded as completed without an associated completion event.

## 5. Project Risk Reporting

A risk is an uncertain event or condition that may affect project objectives.

The risk model contains:

- Risk identifier.
- Description.
- Probability.
- Impact.
- Responsible owner.
- Mitigation action.
- Current state.

### 5.1 Risk exposure

The implementations use a five-point probability and impact scale.

\[
Risk\ Exposure = Probability \times Impact
\]

For example:

| Probability | Impact | Exposure |
|---:|---:|---:|
| 4 | 5 | 20 |
| 3 | 3 | 9 |
| 2 | 2 | 4 |

A score of 20 identifies a high-exposure risk requiring management attention under the example policy.

The multiplication model is a simplified prioritization technique. It does not establish a statistically calibrated probability of financial or schedule loss.

### 5.2 Risk lifecycle

`OPEN → MITIGATING → CLOSED`

- Open: The risk has been identified.
- Mitigating: An active response is being implemented.
- Closed: The risk is no longer considered active.

A closed risk remains part of historical reporting but should not contribute to the active-risk count.

The sample project contains a security testing infrastructure risk with probability 4 and impact 5. Its exposure is 20.

The report identifies the risk owner and mitigation action rather than displaying only an aggregate score.

## 6. Status Report Generation Workflow

The implementations follow a common reporting sequence.

`Project Data → Validation → Metric Calculation → Health Evaluation → Report Generation → Persistence`

### 6.1 Data collection

Information is collected from:

- Project master records.
- Task registers.
- Milestone records.
- Financial records.
- Risk registers.
- Repository activity.
- Review and approval records.
- Automated status checks.

### 6.2 Validation

Data validation occurs before reporting.

Examples include:

- Invalid project date ranges.
- Negative financial amounts.
- Duplicate task identifiers.
- Invalid risk probability.
- Missing reviewer identity.
- Inconsistent milestone completion.
- Missing required status checks.

### 6.3 Metric calculation

The reporting engine calculates completion, milestone progress, budget variance, budget utilization, risk exposure, and repository activity.

### 6.4 Status evaluation

The health classification is calculated from defined rules.

The classification should remain explainable. Each indicator should be traceable to its underlying records.

### 6.5 Persistence

The Python implementation produces JSON and Markdown reports.

The JavaScript implementation produces an asynchronously generated JSON report.

The C++ implementation evaluates the project and governance state in memory.

The Java implementation creates an enterprise-oriented structured report using immutable records and service classes.

The PostgreSQL implementation stores reporting snapshots in a relational table.

## 7. Software Delivery Governance in Project Reports

Software development projects require reporting on repository activity as well as conventional project management indicators.

Four distinct mechanisms are represented:

| Mechanism | Primary responsibility |
|---|---|
| Pull Request | Proposes a change to a target branch |
| Code Review | Evaluates the proposed changes |
| Approval | Records a review decision |
| Branch Protection | Enforces repository-level conditions |

These mechanisms interact, but they are not interchangeable.

A project status report can use them to identify delivery progress, review delays, outstanding approvals, failed checks, and blocked integrations.

## 8. Pull Requests

A Pull Request (PR) is a repository workflow through which proposed changes are presented for integration into another branch.

It identifies:

- Source branch.
- Target branch.
- Proposed changeset.
- Commits.
- Author.
- Review participants.
- Automated checks.
- Integration state.

A Pull Request does not itself represent the complete source branch or target branch.

It represents a proposal to integrate a particular set of changes.

### 8.1 Pull Request lifecycle

`Draft → Open → Review → Approved → Merge Eligible → Merged`

A separate closure path is possible:

`Open → Closed`

A closed Pull Request can be reopened when repository conditions permit and the proposed work remains relevant.

### 8.2 Source and target branches

The source branch contains the proposed changes.

The target branch is the branch into which those changes are intended to be integrated.

The proposed changeset is evaluated relative to the target branch.

A source branch may continue to receive commits while a Pull Request is open. The proposed changeset therefore changes as the branch changes.

The target branch may also receive new commits from other contributors.

This can make the source branch outdated or introduce merge conflicts.

### 8.3 Changesets and commits

A commit represents a recorded repository change.

A changeset represents the proposed difference between the source and target states.

These are related but distinct concepts.

A Pull Request containing four commits does not necessarily contain only four independent logical changes.

Several commits can modify the same files, and later commits can correct earlier work.

### 8.4 Draft Pull Requests

Draft Pull Requests communicate that work is incomplete or not ready for formal integration.

The sample implementations prevent draft Pull Requests from being merge eligible.

Drafts are useful for early feedback and visibility without representing completed review readiness.

### 8.5 Synchronizing the base branch

When the target branch advances, contributors may need to synchronize their source branch.

This process can involve:

- Fetching the latest target branch.
- Merging or rebasing changes.
- Resolving conflicts.
- Re-running tests.
- Updating the proposed changeset.

Synchronization is particularly important when branch protection requires the source branch to be current.

### 8.6 Merge strategies

| Strategy | Behavior |
|---|---|
| Merge commit | Preserves branch integration history with a merge commit |
| Squash | Combines proposed commits into one target-branch commit |
| Rebase | Replays commits onto a different base |

The appropriate strategy depends on repository history requirements and team policy.

A linear-history policy generally rejects merge commits.

### 8.7 Merge conflicts

A conflict occurs when changes cannot be integrated automatically.

Typical causes include:

- Concurrent modifications to the same lines.
- File deletion and modification conflicts.
- Incompatible changes to shared components.
- Changes made to the target branch after development began.

A Pull Request with unresolved conflicts must not be considered merge eligible.

### 8.8 Pull Requests in project reporting

A project report can measure:

- Total Pull Requests.
- Open Pull Requests.
- Draft Pull Requests.
- Merged Pull Requests.
- Closed Pull Requests.
- Average review duration.
- Outstanding review requests.
- Conflicted changesets.

These measurements provide visibility into the software delivery pipeline.

They should not be confused with the percentage of business requirements completed.

## 9. Code Review

Code Review is the technical evaluation of proposed changes by reviewers.

A review examines the quality, correctness, security, maintainability, and suitability of the proposed implementation.

It is an evaluation process, not a repository-level merge enforcement mechanism.

### 9.1 Review mechanics

A reviewer examines the proposed changeset and may:

- Inspect individual files.
- Add inline comments.
- Identify defects.
- Request modifications.
- Ask questions.
- Approve the proposal.
- Participate in review discussions.

### 9.2 Review states

| Review state | Meaning |
|---|---|
| Pending | Review has not been submitted |
| Approved | Reviewer accepts the proposed changes |
| Changes Requested | Reviewer identifies changes required |
| Commented | Reviewer provides feedback without approval |
| Dismissed | A previous review decision is no longer active |

The review state belongs to the review record, not the Pull Request lifecycle.

A Pull Request can remain open while reviews are submitted, updated, or dismissed.

### 9.3 Inline comments and discussions

Inline comments associate feedback with a particular file and, where applicable, a line number.

Discussions allow reviewers and contributors to clarify implementation decisions.

A discussion can be resolved when the underlying concern has been addressed.

Resolving a discussion does not automatically approve the Pull Request.

Similarly, approving a Pull Request does not automatically establish that every conversation has been resolved.

### 9.4 Review quality criteria

Reviewers should assess:

- Functional correctness.
- Input validation.
- Error handling.
- Security implications.
- Performance.
- Maintainability.
- Test coverage.
- Compatibility.
- Consistency with project requirements.

Review scope should remain proportional to the proposed change.

A small change should not be delayed by unrelated architectural discussions unless a material risk is identified.

### 9.5 Review failure modes

Common failures include:

- Reviewing outdated changes.
- Missing security defects.
- Approving without inspecting the changeset.
- Failing to identify regression risks.
- Leaving unresolved conversations.
- Allowing conflicts between review decisions.
- Treating automated test success as a substitute for human review.

Review quality depends on technical understanding and adequate review time.

## 10. Approvals

An approval is an explicit review decision.

It communicates that an eligible reviewer accepts the proposed changes under the applicable review process.

Approval is distinct from the existence of a review.

A reviewer can submit comments or request changes without approving the Pull Request.

### 10.1 Eligible reviewers

An approval should count only when the reviewer satisfies the relevant policy.

Eligibility can depend on:

- Repository membership.
- Active account status.
- Review permissions.
- Required reviewer roles.
- Independence requirements.
- Code ownership rules.

The JavaScript, C++, and Java examples model reviewer eligibility explicitly.

The PostgreSQL implementation validates repository membership and approval capability before accepting an approval.

### 10.2 Required reviews

A repository may require two or more approvals before integration.

For example:

| Requirement | Configured value |
|---|---:|
| Required approvals | 2 |
| Eligible reviewers | 2 |
| Current valid approvals | 2 |
| Approval requirement | Satisfied |

An approval count is based on distinct eligible reviewers rather than the number of review events.

This avoids counting repeated approval records from the same reviewer as independent approvals.

### 10.3 Stale and dismissed approvals

An approval can become stale when new changes are introduced after the review.

Repository policies may require approval again after significant updates.

Dismissed approvals no longer count as valid approval decisions.

The example implementations model dismissal and reviewer eligibility.

A production implementation should retain the complete review event history rather than merely replacing the previous state.

### 10.4 Approval and merge eligibility

Approval satisfaction is one condition of merge eligibility.

It does not independently guarantee that integration is permitted.

A Pull Request can have two valid approvals and still be blocked by:

- Failed security checks.
- Unresolved discussions.
- Merge conflicts.
- An outdated source branch.
- Draft status.
- Linear-history restrictions.

## 11. Branch Protection

Branch Protection is the repository-level mechanism that enforces conditions before changes can be integrated into sensitive branches.

It is a governance control rather than a review decision.

A protected branch may represent:

- Production.
- Main development.
- Release.
- A regulated deployment baseline.

### 11.1 Protection mechanisms

| Control | Purpose |
|---|---|
| Required reviews | Establish minimum review requirements |
| Required status checks | Require successful automated validation |
| Direct-push restriction | Prevent uncontrolled changes |
| Force-push restriction | Protect repository history |
| Branch deletion restriction | Prevent accidental branch removal |
| Conversation requirement | Require review discussions to be resolved |
| Up-to-date requirement | Require synchronization with the target |
| Linear-history requirement | Restrict integration history |
| Administrator bypass | Define privileged exceptions |

### 11.2 Required status checks

Automated status checks provide evidence about the proposed changes.

Examples include:

- Unit tests.
- Integration tests.
- Security scans.
- Static analysis.
- Code formatting.
- Build validation.

A required check that is missing must not be treated as successful.

The sample governance engines use an explicit required-check set.

### 11.3 Direct-push restrictions

Protected branches commonly restrict direct pushes.

Contributors must use the approved integration workflow.

This creates an opportunity for review and automated validation before repository integration.

### 11.4 Force-push restrictions

Force pushes can rewrite branch history.

Disabling them reduces the risk of losing commits or disrupting other contributors.

### 11.5 Administrator bypass

Some repository platforms allow privileged administrators to bypass selected protection rules.

Bypass must be treated as a separately authorized operation.

It should be recorded in an audit trail with the actor, reason, time, and affected branch.

The sample implementations expose bypass configuration but deliberately do not provide an automatic administrator bypass path.

### 11.6 Repository governance and merge enforcement

The distinction is fundamental:

- A Pull Request provides the proposal workflow.
- Code Review evaluates the proposed changes.
- Approvals record review decisions.
- Branch Protection enforces integration requirements.

A repository can have a high number of approvals while still having an unacceptable number of blocked Pull Requests.

A project report should therefore display both approval activity and final merge eligibility.

## 12. Governance Evaluation Model

The governance engine evaluates a Pull Request against a branch protection policy.

The principal conditions are:

1. The Pull Request must be open.
2. The Pull Request must not be a draft.
3. The target branch must match the protected branch.
4. At least one commit must exist.
5. Merge conflicts must be resolved.
6. Required approvals must be satisfied.
7. Required status checks must pass.
8. Required conversations must be resolved.
9. Source synchronization must satisfy policy.
10. Merge strategy must comply with history restrictions.

The result contains:

- Pull Request identifier.
- Eligibility boolean.
- A collection of failure reasons.

This design provides explainable policy evaluation.

It avoids returning only a generic merge failure.

### 12.1 Evaluation complexity

Let:

- \(R\) represent the number of review records.
- \(C\) represent the number of status checks.
- \(P\) represent the number of required checks.

The simple governance implementations perform review and check evaluation in approximately:

\[
O(R+C+P)
\]

The C++ implementation uses ordered maps and sets where deterministic lookup and reviewer uniqueness are useful.

The JavaScript implementation uses `Map` and `Set` for check lookup and approval deduplication.

The Java implementation uses immutable records and collection operations.

The SQL implementation uses indexed relational queries and database constraints.

For larger repositories, current review state and check state should be maintained efficiently rather than repeatedly scanning the complete historical event stream.

## 13. Python Implementation

The Python file provides a self-contained project workflow simulator.

### 13.1 Domain model

Dataclasses represent:

- Project.
- Task.
- Milestone.
- Risk.
- Pull Request.
- Review.
- Status check.
- Branch protection.
- Governance result.

Enums restrict the permitted workflow states.

### 13.2 Reporting service

`StatusReportService` calculates:

- Completion percentage.
- Milestone completion.
- Budget variance.
- Budget utilization.
- Remaining days.
- Risk exposure.
- Repository activity.

`calculate_status()` applies the project health rules.

### 13.3 Governance engine

`GovernanceEngine` evaluates merge eligibility independently of project health.

This is important because project-level health and repository-level merge eligibility describe different conditions.

A project can be at risk while a particular Pull Request is merge eligible.

### 13.4 File persistence

`ReportExporter` creates:

- `output/project_status.json`
- `output/project_status.md`

JSON supports structured consumption.

Markdown provides a human-readable management report.

The JSON export uses a temporary file followed by replacement to reduce the chance of exposing a partially written report.

### 13.5 Execution and testing

Run with Python 3.10 or later.

The script uses standard-library modules and does not require external packages.

The built-in assertions validate completion calculations, risk classification, governance decisions, and invalid input rejection.

## 14. JavaScript Implementation

The JavaScript implementation adopts an event-driven reporting architecture.

### 14.1 Event-driven processing

`ProjectEventBus` extends Node.js `EventEmitter`.

When a report is generated, the system publishes a `report.generated` event.

This separates report production from downstream event handling.

Other services could subscribe to such events for notification, dashboard refresh, or audit processing.

### 14.2 Asynchronous processing

`ReportService.generate()` is asynchronous.

It yields control to the Node.js event loop before producing the report.

`ReportRepository` persists the generated JSON asynchronously using the Node.js filesystem API.

Temporary-file replacement helps avoid incomplete report files.

### 14.3 Collection design

| Structure | Application |
|---|---|
| Map | Tasks, milestones, risks, Pull Requests |
| Set | Required checks and distinct approvals |
| Array | Reviews and status-check records |
| EventEmitter | Reporting event notifications |

The implementation also uses `crypto.randomUUID()` to generate unique event and report identifiers.

### 14.4 Failure handling

The main function catches asynchronous execution errors.

Invalid domain values raise `DomainError`.

Filesystem errors are propagated after temporary-file cleanup.

## 15. C++17 Implementation

The C++ program provides a repository governance and merge-eligibility engine alongside project reporting.

### 15.1 Domain modeling

Enums represent task states, priorities, risk states, review states, Pull Request states, and merge strategies.

Structures represent project entities.

The `Project` class owns delivery information and calculates project health.

### 15.2 Governance engine

`GovernanceEngine` evaluates the conditions imposed by `BranchProtection`.

It checks:

- Pull Request state.
- Draft status.
- Target branch.
- Commit count.
- Conflicts.
- Synchronization.
- Approval count.
- Required status checks.
- Conversation resolution.
- Linear-history requirements.

The engine returns all identified blocking reasons rather than stopping after the first failure.

### 15.3 Memory and performance

Vectors provide sequential storage for tasks, risks, reviews, and Pull Requests.

Sets provide unique reviewer counting.

Maps provide status-check lookup.

These choices are suitable for the demonstration workload.

A production implementation processing very large repositories should consider indexed persistent storage and incremental evaluation.

### 15.4 Error handling

`ValidationError` handles invalid domain data.

The main function catches exceptions and reports execution failures.

The built-in tests validate both accepted and rejected merge decisions.

## 16. Java 17 Implementation

The Java implementation emphasizes enterprise-oriented domain modeling.

### 16.1 Immutable records

Java 17 records represent project entities.

Records provide concise immutable data structures with generated accessors and value-based equality.

Collections are copied using `List.copyOf()` and `Set.copyOf()` to prevent external mutation of the stored collection structure.

### 16.2 Service separation

The implementation separates:

- Domain validation.
- Project reporting.
- Merge policy evaluation.
- Report generation.

`MergePolicyEvaluator` provides an interface for policy evaluation.

`MergeEligibilityService` implements that interface.

This allows the governance logic to be replaced or extended without changing the reporting service.

### 16.3 Enterprise validation

The `Project` record checks:

- Project identity.
- Date consistency.
- Financial values.
- Unique task identifiers.
- Unique milestone identifiers.
- Unique risk identifiers.
- Unique Pull Request identifiers.

The `PullRequest` record checks branch identity, commit count, and review and check collection validity.

### 16.4 Structured reporting

The reporting service returns a structured `Map<String, Object>`.

The structure separates metadata, schedule, financials, delivery, risks, and repository activity.

A production API can serialize this structure into JSON and expose it to a dashboard or reporting interface.

The implementation intentionally avoids a third-party serialization dependency.

## 17. PostgreSQL Relational Architecture

The SQL implementation models project reporting and repository governance using relational entities.

The dedicated schema is `project_reporting`.

### 17.1 Entity relationships

The principal relationships are:

`Project → Tasks → Task Owners`

`Project → Milestones`

`Project → Risks`

`Project → Repository → Branches`

`Repository → Reviewers`

`Branch → Protection Policy → Required Checks`

`Pull Request → Commits`

`Pull Request → Code Reviews → Review Comments`

`Pull Request → Status Checks`

`Pull Request → Merge History`

`Project → Status Reports`

### 17.2 Referential integrity

Primary keys uniquely identify records.

Foreign keys ensure that related records refer to existing entities.

Unique constraints prevent duplicate identifiers within their intended scopes.

Check constraints enforce valid numerical and workflow-related conditions.

### 17.3 Indexing

Indexes support common retrieval patterns.

Examples include:

- Project and task state.
- Task ownership.
- Outstanding task due dates.
- Active risk exposure.
- Repository and Pull Request state.
- Target branch and Pull Request state.
- Review state.
- Required status checks.
- Reporting period history.

The indexes are designed around frequently used filters and joins.

Indexes consume storage and increase write overhead. They should be reviewed against actual query plans in production.

### 17.4 Views

Three reporting views are implemented:

| View | Purpose |
|---|---|
| `project_delivery_summary` | Task counts and completion |
| `project_risk_summary` | Active and critical risks |
| `pull_request_reporting` | Commits, approvals, and checks |

Views separate frequently used reporting queries from application-level presentation logic.

### 17.5 Functions and procedures

`evaluate_merge_eligibility()` evaluates repository integration conditions.

`merge_pull_request()` performs controlled merge-state updates and records merge history.

`generate_project_status_report()` calculates project reporting metrics and stores a historical snapshot.

The merge procedure locks the relevant Pull Request row during processing.

A failed eligibility evaluation raises an exception instead of silently merging an invalid proposal.

### 17.6 Triggers

The project timestamp trigger updates `updated_at` automatically.

The review validation trigger checks reviewer eligibility and repository membership.

Database triggers are useful for enforcing shared integrity rules across multiple application clients.

They should remain focused on database invariants rather than becoming an alternative application service layer.

### 17.7 Transactions

The sample data and initial report generation are grouped within a transaction.

A transaction provides atomicity: either the database operations complete successfully or the transaction can be rolled back.

The merge procedure uses row locking to reduce concurrent merge-state inconsistencies.

For high-concurrency production environments, isolation levels, lock ordering, and retry behavior should be designed explicitly.

## 18. Project Status Report Design

A practical executive report should be concise while retaining sufficient evidence to explain project health.

The following structure is appropriate.

### Executive information

| Field | Description |
|---|---|
| Project name | Official project identity |
| Project manager | Accountable manager |
| Reporting period | Period covered |
| Report generation date | Date of preparation |
| Overall status | Health classification |

### Delivery information

| Field | Description |
|---|---|
| Total tasks | Number of tracked tasks |
| Completed | Finished tasks |
| In progress | Active tasks |
| Blocked | Tasks requiring intervention |
| Completion | Calculated percentage |
| Milestones | Planned and completed outcomes |

### Financial information

| Field | Description |
|---|---|
| Approved budget | Authorized financial baseline |
| Actual cost | Recorded expenditure |
| Variance | Actual expenditure minus budget |
| Utilization | Percentage of budget consumed |

### Risk information

| Field | Description |
|---|---|
| Risk description | Identified threat |
| Probability | Likelihood assessment |
| Impact | Consequence assessment |
| Exposure | Probability multiplied by impact |
| Owner | Responsible individual |
| Mitigation | Planned response |
| State | Current mitigation status |

### Management decisions

A complete operational report should also document:

- Decision required.
- Decision owner.
- Required decision date.
- Consequence of delay.
- Escalation status.

The source implementations calculate the core metrics. A production reporting process should add an explicit decision register and record approved decisions separately from calculated indicators.

## 19. Security and Data Governance

Project reporting systems may contain confidential financial information, personnel information, delivery risks, and security findings.

Appropriate controls include:

- Role-based access control.
- Authentication.
- Project-level authorization.
- Restricted financial-data access.
- Secure reviewer identity management.
- Audit logging.
- Input validation.
- Controlled report distribution.
- Encrypted transport.
- Backup and recovery procedures.

Repository governance also requires controls around privileged operations.

Administrator bypass should be restricted and audited.

A user who can read a status report should not automatically receive permission to modify project financials, approve Pull Requests, or alter branch protection.

The SQL schema provides integrity mechanisms, but production deployment must configure database roles and grants separately.

## 20. Limitations and Engineering Considerations

The examples are functional educational implementations rather than complete enterprise project management platforms.

| Area | Current implementation | Production consideration |
|---|---|---|
| Completion | Task-count percentage | Weighted or earned-value progress |
| Schedule | Remaining days | Baseline schedule variance |
| Financials | Budget and actual cost | Forecasting and committed expenditure |
| Risk | Probability multiplied by impact | Calibrated quantitative risk models |
| Reporting | JSON, Markdown, structured data, SQL snapshots | Dashboard and distribution services |
| Review history | Current review decisions | Complete immutable review event history |
| Status checks | Current check state | Execution history and commit-specific checks |
| Branch protection | Simplified policy model | Platform-specific policy integration |
| Concurrency | Basic locking and in-memory state | Distributed concurrency control |
| Notifications | JavaScript event emission | Reliable delivery and retry mechanisms |

The examples intentionally avoid claiming that a project is healthy solely because its completion percentage is high.

Management decisions require context, historical comparisons, and reliable evidence.

## 21. Comparative Implementation Matrix

| Capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Project model | Dataclasses | Classes | Structures and classes | Records | Relational tables |
| Task tracking | Lists | Maps | Vectors | Immutable lists | Tables |
| Risk analysis | Risk objects | Risk objects | Risk structures | Risk records | SQL calculations |
| Status reporting | JSON and Markdown | Async JSON | Console report | Structured map | Historical snapshots |
| Event processing | Direct execution | EventEmitter | Direct execution | Service execution | Triggers |
| Review evaluation | Governance engine | Policy service | Governance engine | Policy service | SQL function |
| Approval validation | Reviewer eligibility | Reviewer eligibility | Reviewer eligibility | Reviewer eligibility | Trigger |
| Branch protection | Policy object | Policy object | Policy structure | Policy record | Policy tables |
| Merge evaluation | Rule-based | Rule-based | Rule-based | Interface-based | Stored function |
| Persistence | Filesystem | Filesystem | In-memory | In-memory | Relational database |

## 22. Practical Learning Outcomes

The five implementations demonstrate how project status reporting connects project management, software delivery, database design, and repository governance.

The main engineering distinctions are:

1. Project progress is a measurement of delivery, not a substitute for schedule or financial analysis.
2. Milestones represent significant outcomes, while tasks represent individual work activities.
3. Risk exposure prioritizes threats but does not independently establish their actual financial consequences.
4. A Pull Request proposes changes to a target branch.
5. Code Review evaluates the proposed changes.
6. Approval records an eligible review decision.
7. Branch Protection enforces repository integration conditions.
8. Merge eligibility is the result of evaluating the applicable repository rules.
9. A historical status report is a snapshot of recorded information at a particular reporting time.
10. Reliable reporting requires traceable source records, consistent calculations, and explicit validation rules.

The resulting architecture provides a foundation for understanding how operational project information can be converted into structured, auditable, and management-oriented status reports.
