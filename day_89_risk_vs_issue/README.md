# Risk vs Issue Management

## 1. Introduction

Risk and issue management are related management disciplines used in project management, enterprise governance, cybersecurity, software engineering, operations, and business continuity.

Although both involve identifying threats to objectives, they describe different conditions.

**A risk is an uncertain future event or condition that may affect an objective.**

**An issue is an existing problem, failure, or condition that requires attention and action.**

The central distinction is uncertainty versus actuality.

| Dimension | Risk | Issue |
|---|---|---|
| Meaning | Potential future event | Existing problem or realized event |
| Time orientation | Future-oriented | Present or past event with current consequences |
| Certainty | Has not necessarily occurred | Has occurred or currently exists |
| Management approach | Identify, assess, prevent, mitigate, accept, monitor | Record, prioritize, assign, resolve, verify, close |
| Assessment | Probability and impact | Severity and priority |
| Primary objective | Reduce likelihood or consequences | Restore acceptable conditions |
| Management record | Risk register | Issue register |
| Typical owner | Risk owner | Issue or resolution owner |
| Example | A cloud provider may become unavailable | The production cloud service is unavailable |

A risk can materialize into an issue, but not every issue must originate from a previously recorded risk.

For example, an unexpected hardware failure can become an issue even when it was not previously identified in the risk register.

## 2. Risk Management

### 2.1 Risk identification

Risk identification determines which uncertain events could affect project or organizational objectives.

Common risk categories include:

| Category | Example |
|---|---|
| Strategic | A new competitor reduces market share |
| Financial | Project expenditure may exceed its budget |
| Operational | A critical supplier may fail |
| Technology | A cloud infrastructure outage may occur |
| Cybersecurity | An attacker may exploit weak authentication |
| Compliance | A regulatory requirement may not be satisfied |
| Environmental | Extreme weather may interrupt operations |

A risk statement should describe a possible event and its consequences.

Example:

- Cause: Insufficient infrastructure redundancy.
- Event: The primary cloud region becomes unavailable.
- Consequence: Production applications experience service disruption.

This structure helps distinguish a risk from an existing failure.

### 2.2 Probability and impact

Risk assessment estimates two dimensions:

- Probability: How likely is the event to occur?
- Impact: How serious would its consequences be?

The implementations use a five-point assessment scale.

| Score | Probability | Impact |
|---|---|---|
| 1 | Rare | Negligible |
| 2 | Unlikely | Minor |
| 3 | Possible | Moderate |
| 4 | Likely | Major |
| 5 | Almost certain | Severe |

The numerical exposure score is:

\[
Risk\ Exposure = Probability \times Impact
\]

The implemented severity classification is:

| Exposure | Severity |
|---:|---|
| 1–5 | Low |
| 6–11 | Medium |
| 12–19 | High |
| 20–25 | Critical |

Example:

Probability = 4

Impact = 5

\[
4 \times 5 = 20
\]

The resulting risk is classified as critical.

This is a prioritization model, not a statistically calibrated probability of loss. Organizations may use more sophisticated quantitative models when sufficient historical data is available.

### 2.3 Risk response strategies

Risk responses describe how an organization manages uncertainty.

| Strategy | Meaning | Example |
|---|---|---|
| Avoid | Eliminate the activity producing the risk | Cancel an unsafe deployment |
| Mitigate | Reduce probability or impact | Introduce multi-region infrastructure |
| Transfer | Allocate financial consequences to another party | Obtain appropriate insurance |
| Accept | Retain the risk within approved tolerance | Accept a low-exposure operational risk |

A contingency plan describes what should happen if the event occurs despite preventive measures.

Mitigation and contingency are different:

- Mitigation attempts to influence the probability or consequences before the event.
- Contingency prepares the organization to respond after the event occurs.

### 2.4 Risk lifecycle

The implementations model the following states:

| State | Meaning |
|---|---|
| Identified | Risk has been recorded |
| Assessed | Probability and impact have been evaluated |
| Mitigating | Preventive or impact-reduction actions are underway |
| Accepted | The organization formally accepts the remaining exposure |
| Closed | The risk is no longer actively managed |

The principal workflow is:

Identified → Assessed → Mitigating → Closed

An alternative is:

Identified → Assessed → Accepted → Closed

A closed risk cannot be reassessed through the implemented state-transition methods. A new assessment or reopening procedure would require an explicit governance decision.

## 3. Issue Management

### 3.1 Issue identification

An issue represents an actual condition that requires intervention.

Examples include:

- A production database has stopped responding.
- A payment gateway is returning HTTP 503 errors.
- An employee has reported an unauthorized access incident.
- A project has exceeded its approved expenditure.
- A required regulatory submission has missed its deadline.

Unlike a risk, an issue does not depend on whether an event might occur. The relevant event or condition already exists.

### 3.2 Severity and priority

Severity describes the seriousness of the issue and its consequences.

Priority determines how urgently the organization should address it.

These dimensions are related but not identical.

| Dimension | Severity | Priority |
|---|---|---|
| Main question | How serious is the problem? | How urgently should it be handled? |
| Basis | Consequences and operational impact | Severity, deadlines, dependencies, business requirements |
| Example | Critical database failure | Urgent restoration |

The implementations use a deterministic mapping:

| Severity | Default priority |
|---|---|
| Low | Low |
| Medium | Medium |
| High | High |
| Critical | Urgent |

This mapping is suitable for the demonstration workflow. A production organization may use a priority matrix that also considers affected users, service-level agreements, regulatory deadlines, and business dependencies.

### 3.3 Issue lifecycle

The implementations use these states:

| State | Meaning |
|---|---|
| Open | Issue has been reported and registered |
| In Progress | Resolution activities have started |
| Blocked | Resolution cannot proceed because of a dependency |
| Resolved | Corrective action has been completed |
| Closed | Resolution has been verified and formally closed |

The normal workflow is:

Open → In Progress → Resolved → Closed

A blocked workflow is:

Open → Blocked → In Progress → Resolved → Closed

A resolved issue is not automatically considered closed. Verification and formal closure provide an additional management control.

### 3.4 Issue resolution

A complete resolution process generally includes:

1. Record the actual problem.
2. Determine its severity and priority.
3. Assign an accountable owner.
4. Investigate the underlying cause.
5. Implement corrective action.
6. Verify the outcome.
7. Record resolution evidence.
8. Close the issue.

Resolution should contain sufficient information to establish what was corrected and how the result was verified.

## 4. Risk vs Issue: Their Relationship

A risk and an issue can describe different stages of the same operational event.

Consider a cloud infrastructure example.

<escape>Stage 1: A cloud region may become unavailable.
        |
        v
Stage 2: Record the uncertainty in the risk register.
        |
        v
Stage 3: Assess probability and impact.
        |
        v
Stage 4: Implement redundancy and contingency measures.
        |
        v
Stage 5: The cloud region actually becomes unavailable.
        |
        v
Stage 6: Record an operational issue.
        |
        v
Stage 7: Restore service and verify recovery.
        |
        v
Stage 8: Close the issue and review the original risk.</escape>

The original risk record should remain available for historical analysis.

The issue should have a separate identifier, owner, status, and resolution record.

This separation supports:

- Historical traceability.
- Risk forecasting.
- Incident analysis.
- Accountability.
- Management reporting.
- Continuous improvement.

A materialized risk may also remain under review because its consequences can create further uncertainty.

For example, a cybersecurity incident can create additional risks involving data exposure, regulatory penalties, litigation, and reputational damage.

## 5. Risk Register vs Issue Register

These registers serve different purposes.

### 5.1 Risk register

A risk register maintains information about uncertain events.

Typical fields include:

| Field | Purpose |
|---|---|
| Risk ID | Unique identifier |
| Title | Concise risk statement |
| Description | Event and potential consequences |
| Category | Risk classification |
| Probability | Estimated likelihood |
| Impact | Potential consequences |
| Exposure | Probability multiplied by impact |
| Severity | Derived risk classification |
| Owner | Person accountable for managing the risk |
| Mitigation plan | Preventive or impact-reduction measures |
| Contingency plan | Response if the event occurs |
| Status | Current management state |

### 5.2 Issue register

An issue register maintains existing problems and their resolution progress.

Typical fields include:

| Field | Purpose |
|---|---|
| Issue ID | Unique identifier |
| Title | Actual problem |
| Description | Details of the condition |
| Severity | Seriousness of the problem |
| Priority | Required response urgency |
| Owner | Person responsible for resolution |
| Source Risk ID | Optional originating risk reference |
| Status | Current resolution state |
| Resolution | Corrective action and outcome |
| Reported date | When the issue was registered |
| Resolved date | When the issue was resolved |

An issue does not require a source risk identifier because an issue can arise unexpectedly.

## 6. Python Implementation

The Python implementation models the workflow using object-oriented domain structures.

### 6.1 Data structures

The implementation uses:

- `Risk` dataclass for uncertain future events.
- `Issue` dataclass for existing problems.
- `RiskStatus` and `IssueStatus` enums for lifecycle control.
- `Severity` and `Priority` enums for classification.
- Dictionaries for constant-time average identifier-based lookup.
- Lists for ordered reporting.

The two principal domain entities have separate identifiers and state transitions.

### 6.2 Risk exposure calculation

The `exposure` property calculates probability multiplied by impact.

The `severity` property translates the resulting score into a classification.

The calculation is derived from current probability and impact values rather than stored as an independently mutable field.

### 6.3 Risk-to-issue conversion

The `convert_risk_to_issue()` method creates a separate issue using the original risk's severity.

The new issue stores the original risk identifier in `source_risk_id`.

The original risk is retained.

This is important because converting a risk should not destroy the evidence that the organization previously identified the possibility of the event.

### 6.4 State validation

Each domain entity controls its own transitions.

Examples include:

- A closed risk cannot be accepted again.
- A risk cannot enter mitigation without a mitigation plan.
- An issue cannot be closed before resolution.
- An issue cannot be resolved without resolution details.

These validations prevent invalid state changes.

### 6.5 Reporting and export

`highest_risks()` sorts active risks by exposure.

`unresolved_issues()` filters issues that still require attention.

`dashboard()` produces separate risk and issue statistics.

`export_json()` creates a structured report using Python's standard JSON library.

The export method uses exclusive file creation to avoid accidental overwriting.

## 7. JavaScript Implementation

The JavaScript implementation provides an event-driven management model.

### 7.1 Event-driven architecture

`RiskIssueManager` extends Node.js `EventEmitter`.

Domain events are emitted when records are created or when a risk materializes.

Events contain:

- Event identifier.
- Event type.
- Associated entity identifier.
- Timestamp.

This makes the implementation suitable for integration with notification services, audit pipelines, and downstream reporting systems.

### 7.2 Maps and structured state

JavaScript `Map` collections maintain the risk and issue registers.

Each collection uses its own identifiers.

This avoids mixing uncertain events with existing operational problems.

### 7.3 Asynchronous report handling

The implementation uses Node.js asynchronous file operations.

The export method uses exclusive file creation and restrictive file permissions.

Errors are handled through Promise rejection and the top-level asynchronous execution handler.

### 7.4 Policy evaluation

The severity calculation is implemented as a separate function.

The priority mapping is also isolated.

This separation makes it possible to replace the classification policy without rewriting the underlying domain entities.

## 8. C++17 Implementation

The C++17 implementation focuses on a repository-independent governance engine for operational risk and issue management.

### 8.1 Domain modeling

The program uses:

- `struct Risk` for risk information.
- `struct Issue` for existing operational problems.
- Enums for lifecycle states and classifications.
- `GovernanceEngine` for centralized record management.

The entities contain their own validation and transition methods.

### 8.2 STL containers

The implementation uses `std::map` for identifier-based record storage.

This provides ordered identifiers and logarithmic lookup, insertion, and deletion complexity.

The reporting functions use `std::vector` to construct sorted views of the records.

### 8.3 Prioritization

The `prioritizedRisks()` method sorts active risks by exposure.

The `unresolvedIssues()` method returns only issues that have not reached a resolved or closed state.

The engine does not automatically equate risk exposure with issue priority.

### 8.4 Exception handling

The program distinguishes:

- Invalid input through `std::invalid_argument`.
- Missing records through `std::out_of_range`.
- Invalid lifecycle transitions through `std::logic_error`.

The main function catches standard exceptions and returns a non-zero exit code on execution failure.

### 8.5 Complexity

Let:

- \(R\) represent the number of risks.
- \(I\) represent the number of issues.

| Operation | Complexity |
|---|---|
| Risk lookup | O(log R) |
| Issue lookup | O(log I) |
| Risk insertion | O(log R) |
| Issue insertion | O(log I) |
| Risk prioritization | O(R log R) |
| Unresolved issue reporting | O(I) |
| Traceability validation | O(I log R) |

The implementation avoids unnecessary dependencies and uses standard C++17 facilities.

## 9. Java 17 Enterprise Implementation

The Java implementation emphasizes explicit domain types, policy separation, immutable assessment records, and service-level governance.

### 9.1 Records

`RiskAssessment` is a Java record.

It captures:

- Probability.
- Impact.
- Exposure.
- Severity.
- Assessment timestamp.

The compact constructor validates the supplied values.

Records provide concise immutable data structures for historical assessment information.

### 9.2 Domain entities

`Risk` and `Issue` are separate classes.

Their identifiers are UUID values.

This reduces the possibility of identifier collisions across independently managed records.

Risk assessment history is retained in a list and exposed through immutable copies.

### 9.3 Policy objects

`RiskPolicy` defines an escalation decision.

`StandardRiskPolicy` implements the policy using an exposure threshold.

The `GovernanceService` delegates escalation evaluation to the policy object.

This separates management rules from record storage and state management.

### 9.4 Service responsibilities

`GovernanceService` handles:

- Risk registration.
- Issue registration.
- Risk materialization.
- Risk prioritization.
- Unresolved issue reporting.
- Status aggregation.
- Risk-to-issue traceability validation.

The service checks foreign-reference consistency before accepting an issue associated with a risk.

### 9.5 Java Streams

Streams provide filtering, sorting, and grouping operations.

The implementation uses immutable result lists where appropriate.

The policy object can be replaced with an organization-specific implementation without changing the risk and issue domain classes.

## 10. PostgreSQL Relational Implementation

The PostgreSQL implementation models an enterprise risk and issue management database.

### 10.1 Database relationships

The principal relationships are:

<escape>Departments
    |
    v
Employees
    |
    +--------------------+
    |                    |
    v                    v
Risks                 Issues
    |                    |
    |                    |
    v                    |
Risk Assessment History  |
    |                    |
    v                    |
Mitigation Actions       |
                         |
                         v
                  Issue Activities

Risks 1 -------- 0..N Issues
        (source risk reference)</escape>

A risk can be associated with multiple issues if multiple consequences materialize.

An issue can also exist independently without an originating risk.

### 10.2 Database integrity

The schema uses:

- Primary keys for record identification.
- Foreign keys for organizational and traceability relationships.
- Unique constraints for risk and issue codes.
- Check constraints for valid probability and impact values.
- Enumerated types for controlled lifecycle states.
- Generated columns for risk exposure.

These controls enforce important domain rules at the database level.

### 10.3 Historical assessment

`risk_assessment_history` records individual assessments.

This prevents historical probability and impact values from disappearing when a risk is reassessed.

The main risk record maintains the current assessment.

The historical table maintains previous assessment information and the assessor identity.

### 10.4 Triggers and audit records

The database implements triggers for:

- Updating modification timestamps.
- Recording risk changes.
- Recording issue changes.

`governance_audit` provides an audit trail for the demonstrated operations.

A production audit system should also capture authenticated actor identity, transaction correlation identifiers, and appropriate retention controls.

### 10.5 Functions and procedures

`calculate_severity()` calculates severity from probability and impact.

`severity_to_priority()` translates severity into the demonstration priority classification.

`materialize_risk()` creates a new issue associated with an existing risk.

`record_risk_assessment()` updates the current assessment and records its history.

The procedure executes both operations within the calling transaction.

### 10.6 Reporting

The SQL provides queries for:

- Risk register retrieval.
- Issue register retrieval.
- Critical risk identification.
- Category-wise exposure analysis.
- Issue backlog reporting.
- Department-wise issue analysis.
- Historical risk assessment retrieval.
- Risk-to-issue traceability.
- Mitigation action coverage.
- Management dashboard reporting.

Indexes support common access patterns involving active risks, issue statuses, owners, and originating risk identifiers.

### 10.7 Transaction handling

Risk materialization should be transactional.

If the creation of an issue fails, the operation should not leave partially committed changes.

The database function executes within the caller's transaction.

The demonstration includes an explicit transaction and a controlled validation failure.

## 11. Risk Management vs Issue Management in Practice

The following scenarios demonstrate why both management disciplines are necessary.

| Scenario | Risk | Issue |
|---|---|---|
| Cloud infrastructure | A cloud region may become unavailable | The cloud region is currently unavailable |
| Cybersecurity | Administrator credentials may be compromised | Unauthorized administrator access has been confirmed |
| Finance | Project expenditure may exceed its budget | Actual expenditure has exceeded the approved budget |
| Software deployment | A deployment may introduce defects | A deployment has introduced a production defect |
| Compliance | A regulatory deadline may be missed | The regulatory deadline has already been missed |
| Supply chain | A supplier may fail to deliver | The supplier has failed to deliver |

The management response differs according to the condition.

A potential cloud outage requires infrastructure resilience planning.

An existing cloud outage requires service restoration.

Similarly, a potential credential compromise requires preventive controls, while confirmed unauthorized access requires incident containment and investigation.

## 12. Common Management Mistakes

### 12.1 Treating every risk as an issue

Recording an uncertain event as an existing problem produces inaccurate operational reporting.

The organization may appear to have more active failures than it actually does.

### 12.2 Treating every issue as a risk

An existing failure needs immediate corrective action.

Recording it only as a future uncertainty can delay accountability and resolution.

### 12.3 Confusing severity and priority

A serious issue does not always have the highest immediate priority.

For example, a critical problem affecting an isolated development environment may have lower immediate priority than a high-severity problem affecting a production payment service.

### 12.4 Closing risks without evidence

A risk should not be closed merely because a mitigation action has been assigned.

Closure should consider residual exposure, completed controls, acceptance authority, and monitoring requirements.

### 12.5 Closing issues without verification

A technical action being completed does not necessarily prove that the original problem has been resolved.

Verification should establish that the affected service, process, or control has returned to an acceptable condition.

### 12.6 Losing risk-to-issue traceability

When a risk materializes, the original risk record should remain accessible.

The organization should be able to determine:

- What was anticipated.
- How the risk was assessed.
- Which mitigation controls were implemented.
- When the event occurred.
- Which issue was created.
- How the issue was resolved.

## 13. Security and Production Considerations

The implementations demonstrate core domain logic. Enterprise deployment requires additional controls.

**Access control**

- Restrict risk creation and modification to authorized roles.
- Restrict issue closure to authorized personnel.
- Require appropriate approval for accepting critical risks.
- Separate risk ownership from independent oversight where necessary.

**Data protection**

- Protect sensitive incident descriptions.
- Avoid placing passwords, authentication tokens, or confidential credentials in management records.
- Encrypt sensitive information in transit and at rest.
- Apply retention and access policies to audit records.

**Operational reliability**

- Use transactional database operations.
- Maintain backups and recovery procedures.
- Record assessment history.
- Monitor overdue mitigation actions.
- Escalate critical unresolved issues.
- Use idempotency controls when integrating external incident-management systems.

**Governance**

- Define organizational risk appetite.
- Establish risk acceptance authority.
- Standardize severity and priority definitions.
- Maintain accountable owners.
- Review residual risks periodically.
- Separate corrective action verification from issue closure where required.

**Limitations**

The implementations use a five-point probability-impact model and deterministic severity-to-priority mapping. These are simplified governance rules, not universal standards.

They do not implement distributed locking, multi-user authorization, notification delivery, external ticket synchronization, or a complete enterprise audit architecture.

The PostgreSQL schema provides relational integrity and basic audit mechanisms, but its audit table does not independently guarantee tamper resistance. Production deployments require stronger access controls, retention policies, and protected audit storage.

## 14. Execution and Technical Requirements

| Implementation | Runtime | External dependencies |
|---|---|---|
| Python | Python 3.10 or later | None |
| JavaScript | Node.js 18 or later | None |
| C++17 | C++17-compatible compiler | None |
| Java | Java 17 | None |
| PostgreSQL | PostgreSQL 14 or later | None |

The Java program is compiled using the public class name `RiskIssueManagement`.

The C++ implementation requires the C++17 language standard.

The JavaScript implementation uses built-in Node.js modules.

The PostgreSQL script creates a dedicated `governance` schema and its associated database objects.

The database objects and sample records are designed to demonstrate the distinction between potential risks and existing issues, their separate management lifecycles, and their relationship when an uncertain event materializes.
