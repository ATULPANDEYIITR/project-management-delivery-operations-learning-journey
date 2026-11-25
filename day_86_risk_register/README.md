# Enterprise Risk Register Management

## 1. Introduction

A risk register is a structured record used by an organisation to identify, assess, prioritise, assign, treat and monitor risks that may affect its objectives.

It provides a central reference for understanding uncertainty, allocating responsibility, tracking mitigation activities and communicating exposure to management.

A risk register is not simply a list of problems. It is a management mechanism that connects identified threats and opportunities with measurable assessments, accountable owners, treatment decisions and periodic reviews.

This implementation models an enterprise technology and operational risk register across Python, JavaScript, C++17, Java 17 and PostgreSQL.

## 2. Risk Register Structure

A practical risk register contains the following information:

| Field | Purpose |
|---|---|
| Risk ID | Unique identifier for each risk |
| Risk title | Short description of the risk |
| Risk description | Explanation of the uncertainty and its consequences |
| Risk category | Classification of the risk |
| Risk owner | Person accountable for managing the risk |
| Probability | Estimated likelihood of occurrence |
| Impact | Estimated consequence if the risk occurs |
| Inherent score | Exposure before considering controls |
| Inherent level | Classification of inherent exposure |
| Response strategy | Selected approach to managing the risk |
| Treatment plan | Actions intended to address the risk |
| Treatment owner | Person responsible for implementing actions |
| Existing controls | Measures already implemented |
| Residual probability | Likelihood after treatment |
| Residual impact | Consequence after treatment |
| Residual score | Remaining exposure |
| Status | Current lifecycle position |
| Target date | Expected completion or treatment date |
| Review date | Date for reassessment |
| Audit history | Record of changes and decisions |

A risk identifier should remain stable throughout the risk lifecycle. Changes to an assessment or treatment plan should not create a new risk unless the underlying risk is genuinely different.

## 3. Risk Identification

Risk identification establishes what could prevent an organisation from achieving its objectives.

The process should describe the source of uncertainty, the event that may occur and its potential consequences.

A useful risk statement follows this structure:

**Because of [cause], [risk event] may occur, resulting in [consequence].**

Example:

Because privileged accounts lack multi-factor authentication, an attacker may obtain unauthorised system access, resulting in confidential data exposure and operational disruption.

This structure separates three important elements:

- Cause: The underlying weakness or condition.
- Risk event: The uncertain occurrence.
- Consequence: The potential effect on organisational objectives.

### Risk categories

| Category | Example |
|---|---|
| Strategic | Failure to achieve organisational objectives |
| Operational | Interruption of essential business operations |
| Financial | Budget overruns or liquidity problems |
| Technological | Infrastructure failure or technology obsolescence |
| Cybersecurity | Ransomware, unauthorised access or data breaches |
| Compliance | Failure to satisfy statutory obligations |
| Reputational | Loss of stakeholder confidence |
| Project | Schedule, scope or delivery failure |
| Environmental | Environmental disruption or regulatory exposure |

Classification supports consistent reporting and helps management identify areas with concentrated exposure.

## 4. Risk Assessment

Risk assessment estimates the likelihood and consequence of each identified risk.

The implementations use a five-point probability scale and a five-point impact scale.

### Probability scale

| Score | Classification | Interpretation |
|---:|---|---|
| 1 | Rare | Highly unlikely |
| 2 | Unlikely | Not expected under normal conditions |
| 3 | Possible | Could occur |
| 4 | Likely | Expected to occur in relevant circumstances |
| 5 | Almost Certain | Very likely to occur |

### Impact scale

| Score | Classification | Interpretation |
|---:|---|---|
| 1 | Insignificant | Negligible consequence |
| 2 | Minor | Limited operational effect |
| 3 | Moderate | Noticeable disruption or financial impact |
| 4 | Major | Significant organisational consequences |
| 5 | Severe | Critical business or organisational consequences |

### Risk scoring

The implementations use:

`Risk Score = Probability × Impact`

The resulting score ranges from 1 to 25.

| Score | Risk level |
|---:|---|
| 1–5 | Low |
| 6–11 | Medium |
| 12–19 | High |
| 20–25 | Critical |

For example:

- Probability = 4
- Impact = 5
- Inherent score = 20
- Classification = Critical

This is a prioritisation model rather than a statistical probability calculation.

Multiplying ordinal assessment values produces a useful management index, but it does not establish a mathematically calibrated probability of loss.

Organisations should define scoring criteria appropriate to their operational environment and apply them consistently.

## 5. Inherent and Residual Risk

The distinction between inherent and residual risk is fundamental to risk management.

### Inherent risk

Inherent risk represents exposure before considering the effect of controls and treatment measures.

Example:

A critical information system without effective access controls may have a probability score of 4 and an impact score of 5.

Inherent score = 20.

### Residual risk

Residual risk represents the exposure remaining after considering implemented controls and treatment measures.

Suppose the organisation deploys:

- Multi-factor authentication.
- Endpoint detection and response.
- Privileged access management.
- Immutable backups.
- Security monitoring.

Following implementation, the reassessment may produce:

- Residual probability = 2.
- Residual impact = 3.
- Residual score = 6.

| Assessment | Probability | Impact | Score | Level |
|---|---:|---:|---:|---|
| Inherent | 4 | 5 | 20 | Critical |
| Residual | 2 | 3 | 6 | Medium |

The difference indicates a reduction in assessed exposure.

It does not independently prove that the controls are effective. Control testing, operational evidence and periodic reassessment are required.

A residual assessment should not be recorded merely because a treatment plan has been created. The controls must be implemented or sufficiently evidenced before their effects are reflected in the assessment.

## 6. Risk Treatment Strategies

Risk treatment describes how the organisation intends to respond to an identified risk.

The implementations support four strategies.

### Avoid

The organisation removes the activity or condition that creates the exposure.

Example: Discontinuing an unsafe system integration.

### Mitigate

The organisation introduces controls or operational measures to reduce probability, impact or both.

Example: Deploying multi-factor authentication to reduce unauthorised access risk.

### Transfer

The organisation transfers specified financial or contractual consequences to another party.

Example: Cyber insurance or contractual risk allocation.

Transfer does not necessarily eliminate the underlying operational risk or the organisation's accountability.

### Accept

The organisation consciously retains the exposure after evaluating its consequences and obtaining the necessary authorisation.

Acceptance should have:

- A documented justification.
- An identified approving authority.
- An assessment of remaining exposure.
- A review date where appropriate.
- Evidence of the decision.

Risk acceptance is a management decision, not an indication that the risk has disappeared.

## 7. Risk Ownership and Accountability

A risk owner is accountable for ensuring that an identified risk is assessed, monitored and managed.

A treatment owner is responsible for implementing specific treatment activities.

These responsibilities can belong to different individuals.

| Responsibility | Primary role |
|---|---|
| Risk identification | Business unit or risk analyst |
| Risk assessment | Risk owner and relevant specialists |
| Treatment approval | Authorised management |
| Treatment implementation | Treatment owner |
| Control implementation | Control owner |
| Residual assessment | Risk owner and assessment specialist |
| Monitoring | Risk owner |
| Risk acceptance | Authorised approving authority |
| Governance oversight | Risk management function |

Assigning an owner without providing authority, resources or an actionable treatment plan creates an accountability gap.

The Python and JavaScript implementations maintain separate risk and treatment ownership fields.

The Java implementation models the same distinction through enterprise domain objects.

## 8. Risk Lifecycle

A risk register should maintain a controlled lifecycle rather than treating every risk as a static record.

The implementations use the following lifecycle:

`IDENTIFIED → ASSESSED → TREATMENT_PLANNED → IN_PROGRESS → MONITORING`

Alternative paths include formal acceptance and closure.

### Lifecycle states

| State | Meaning |
|---|---|
| Identified | Risk has been recorded |
| Assessed | Probability, impact and exposure have been evaluated |
| Treatment Planned | A response and treatment approach have been established |
| In Progress | Treatment activities are being implemented |
| Monitoring | Exposure and control effectiveness are being reviewed |
| Accepted | Authorised management has accepted the remaining exposure |
| Closed | The risk record has been formally closed |

State transitions are validated to prevent arbitrary lifecycle changes.

For example, a risk cannot move directly from identification to monitoring without passing through assessment and treatment planning under the defined workflow.

A closed risk can be reopened through an explicit transition.

Reopening should trigger reassessment rather than automatically restoring its former operational status.

## 9. Risk Monitoring and Review

Risk management continues after treatment implementation.

Monitoring determines whether:

- The original risk assumptions remain valid.
- Probability has changed.
- Impact has changed.
- Controls remain operational.
- Treatment activities are overdue.
- New threats have emerged.
- Residual exposure remains within the organisation's tolerance.

The implementations support periodic reviews, treatment progress tracking and overdue-risk identification.

### Review triggers

| Trigger | Required consideration |
|---|---|
| Scheduled review | Reassess current exposure |
| Security incident | Evaluate control effectiveness |
| Regulatory change | Reconsider compliance exposure |
| Supplier failure | Review operational dependencies |
| Major system change | Reassess technology risks |
| Control failure | Recalculate residual exposure |
| Business restructuring | Review ownership and risk assumptions |

Event-driven reviews are important because a risk may change substantially before its next scheduled review.

## 10. Risk Prioritisation and Reporting

Risk prioritisation enables management to allocate attention and resources according to exposure.

The implementations sort risks by descending inherent score.

A typical priority report contains:

- Risk identifier.
- Risk description.
- Category.
- Inherent score.
- Inherent classification.
- Residual score.
- Owner.
- Treatment status.
- Target date.

### Management indicators

| Indicator | Management purpose |
|---|---|
| Total risks | Measures recorded exposure |
| Critical risks | Identifies the highest-priority risks |
| High risks | Identifies significant exposure |
| Average risk score | Indicates the overall assessment profile |
| Overdue risks | Highlights delayed treatment |
| Risks without treatment plans | Identifies management gaps |
| Risks without residual assessments | Identifies incomplete monitoring |
| Control implementation rate | Measures treatment progress |
| Residual score reduction | Indicates changes in assessed exposure |

The average risk score is a descriptive indicator. It should not replace individual risk analysis because a small number of critical risks may be hidden by a large number of low risks.

## 11. Python Implementation

The Python implementation provides a self-contained risk register simulation.

### Main components

| Component | Responsibility |
|---|---|
| `RiskCategory` | Defines risk classifications |
| `RiskStatus` | Represents lifecycle states |
| `RiskResponse` | Defines treatment strategies |
| `RiskLevel` | Defines exposure classifications |
| `Risk` | Stores and validates an individual risk |
| `RiskRegister` | Manages the complete register |

### Technical mechanisms

The implementation uses:

- Dataclasses for structured risk records.
- Enumerations for controlled classifications.
- Dictionaries for constant-time average risk lookup.
- Lists for controls, notes and audit events.
- Properties for calculated inherent and residual scores.
- Exceptions for invalid data and unsupported operations.
- JSON persistence for saving and restoring register information.

Risk updates use validation and rollback so an invalid change does not leave a partially modified record.

The persistence mechanism writes to a temporary file before replacing the destination file.

The example creates three risks covering cybersecurity, project delivery and financial exposure.

It also demonstrates residual assessment, status updates, prioritisation, reporting and persistence validation.

The JSON file is a local demonstration store. A production implementation would require additional concurrency control, access management and durable audit storage.

## 12. JavaScript Implementation

The JavaScript implementation provides an event-driven model.

Its primary purpose is to demonstrate how changes in the risk register can trigger related operational activities.

### Main components

| Component | Responsibility |
|---|---|
| `Risk` | Validates and represents a risk |
| `RiskRegister` | Manages risk records and events |
| `RiskValidationError` | Reports invalid operations |
| `RiskNotFoundError` | Handles missing records |
| `ALLOWED_TRANSITIONS` | Controls lifecycle transitions |

### Event-driven processing

The implementation uses Node.js `EventEmitter`.

Important events include:

- `risk:created`
- `risk:updated`
- `risk:transition`
- `risk:residual`

These events support independent listeners for audit recording, monitoring and notifications.

A risk creation event can be consumed by an audit listener without requiring the risk registration method to contain notification-specific logic.

The implementation uses:

- `Map` for risk lookup.
- `Set` for associated controls.
- `EventEmitter` for event processing.
- Private class fields for internal state.
- Asynchronous file operations for persistence.
- Immutable event payloads to reduce accidental listener-side modification.

The policy evaluator checks escalation requirements, missing treatment plans and formal acceptance conditions.

The implementation demonstrates the distinction between an assessment result and the organisational decisions needed to manage it.

## 13. C++17 Implementation

The C++17 program implements a repository-independent enterprise risk governance engine.

Its primary focus is structured domain modelling, controlled state transitions and management eligibility evaluation.

### Main components

| Component | Responsibility |
|---|---|
| `Risk` | Represents an individual risk |
| `RiskRegister` | Maintains risk records |
| `GovernancePolicy` | Defines management thresholds |
| `Evaluation` | Contains eligibility results |
| `AuditEntry` | Records operational changes |
| `RiskCategory` | Represents risk classification |
| `RiskStatus` | Represents lifecycle state |

### Engineering decisions

The implementation uses:

- `std::map` for ordered risk storage.
- `std::set` for unique control identifiers.
- `std::optional` for assessments that may not exist.
- `std::vector` for reports and audit events.
- Enumerations for controlled domain values.
- Exceptions for invalid operations.
- STL algorithms for prioritisation.

The ordered map provides logarithmic lookup and insertion complexity.

Prioritisation uses sorting with a complexity of O(n log n).

The governance evaluator checks whether treatment requirements and acceptance conditions have been satisfied.

An important distinction is that a low residual score does not automatically authorise closure or acceptance. The status and governance requirements remain separate.

## 14. Java 17 Implementation

The Java implementation models an enterprise risk management service using explicit domain types and repository abstraction.

### Main components

| Component | Responsibility |
|---|---|
| `Risk` | Encapsulates risk information and lifecycle operations |
| `RiskAssessment` | Represents probability and impact assessments |
| `RiskReview` | Records review findings |
| `RiskEvent` | Records status changes |
| `GovernancePolicy` | Defines enterprise evaluation requirements |
| `RiskRepository` | Defines risk persistence operations |
| `InMemoryRiskRepository` | Provides a working repository implementation |
| `RiskGovernanceService` | Provides registration, prioritisation and evaluation |

### Domain modelling

Java records represent immutable assessment and review information.

The `Risk` class encapsulates mutable lifecycle information while preserving controlled update methods.

The repository interface separates business operations from storage implementation.

This design allows the in-memory repository to be replaced by a database-backed repository without changing the core governance service.

The governance service uses Java Streams for:

- Risk prioritisation.
- Risk aggregation.
- Classification distribution.
- Overdue-risk identification.
- Average inherent score calculation.

The implementation demonstrates enterprise-oriented separation of responsibilities, lifecycle validation and explicit policy evaluation.

## 15. PostgreSQL Implementation

The PostgreSQL implementation provides a relational model for managing enterprise risk information.

It separates organisational data, risk records, assessments, treatments, controls, reviews, acceptance decisions and audit information.

### Database relationship model

The principal relationships are:

- One department can have multiple employees.
- One risk register can contain multiple risks.
- One risk can have multiple assessments.
- One risk can have multiple treatment plans.
- One risk can be associated with multiple controls.
- One control can be associated with multiple risks.
- One risk can have multiple reviews.
- One risk can have multiple acceptance records.
- One risk can generate multiple audit events.

The many-to-many relationship between risks and controls is implemented through the `risk_controls` junction table.

### Database mechanisms

| PostgreSQL feature | Purpose |
|---|---|
| Schemas | Organises risk management objects |
| ENUM types | Restricts domain classifications |
| Primary keys | Uniquely identify records |
| Foreign keys | Enforce referential integrity |
| UNIQUE constraints | Prevent duplicate register identifiers |
| CHECK constraints | Validate scores and dates |
| Generated columns | Calculate risk scores and levels |
| Indexes | Improve common retrieval operations |
| Views | Provide consolidated management reporting |
| LATERAL joins | Retrieve the latest assessments |
| CTEs | Structure analytical queries |
| Functions | Calculate scores and eligibility |
| Procedures | Validate and record assessments |
| Triggers | Enforce status transitions and audit changes |
| Transactions | Maintain consistency across operations |
| JSONB | Store structured audit details |

### Risk assessment history

Assessments are stored as separate records rather than overwriting previous values.

This preserves the history of inherent and residual assessments.

The latest assessment is selected using assessment date and assessment identifier.

This approach supports historical analysis and auditability.

### Governance eligibility

The `evaluate_risk_eligibility` function evaluates whether a risk satisfies configured requirements.

It checks:

- Whether an inherent assessment exists.
- Whether critical exposure requires escalation.
- Whether a mitigation plan exists.
- Whether residual assessment requirements are satisfied.
- Whether risk acceptance has been approved.
- Whether an active implemented control is required.

The function returns an eligibility status and a list of blockers.

Eligibility is a calculated management result, not a substitute for an authorised management decision.

### Database integrity

The status trigger prevents invalid lifecycle transitions and automatically updates the record version.

The audit trigger records insertions and updates.

Foreign keys prevent records from referencing nonexistent employees, controls or risks.

The database script uses a transaction so the schema and sample data are committed together.

## 16. Risk Governance and Internal Controls

A risk register becomes operationally useful when its information is connected to governance responsibilities.

A practical governance model separates the following activities:

| Governance activity | Purpose |
|---|---|
| Identification | Establish what may happen |
| Assessment | Estimate likelihood and impact |
| Prioritisation | Determine management attention |
| Treatment approval | Authorise the selected response |
| Implementation | Execute treatment actions |
| Control testing | Establish whether controls work |
| Residual assessment | Evaluate remaining exposure |
| Acceptance | Authorise retention of exposure |
| Monitoring | Detect changes in risk conditions |
| Reporting | Communicate exposure to management |

### Segregation of responsibilities

The individual responsible for implementing a treatment should not automatically become the sole authority for accepting the resulting residual risk.

Independent review is particularly important for:

- Critical cybersecurity exposure.
- Regulatory non-compliance.
- Financial reporting risks.
- Business continuity risks.
- Risks involving senior management decisions.

The sample implementations demonstrate the data and workflow structure needed to support these responsibilities. They do not implement a complete enterprise identity and approval platform.

## 17. Important Edge Cases and Limitations

The following situations require explicit handling:

| Situation | Required handling |
|---|---|
| Duplicate risk identifier | Reject registration |
| Missing risk owner | Reject registration |
| Probability outside 1–5 | Reject assessment |
| Impact outside 1–5 | Reject assessment |
| Missing treatment plan | Flag mitigation gap |
| Missing residual assessment | Flag incomplete monitoring |
| Overdue target date | Include in overdue reporting |
| Invalid status transition | Reject lifecycle change |
| Unauthorised acceptance | Prevent formal acceptance |
| Closed risk reassessment | Require reopening first |
| Ineffective control | Reassess residual exposure |
| Missing assessment history | Flag data-quality issue |

The five implementations are educational reference systems rather than complete production risk platforms.

The in-memory implementations do not provide distributed transactions or multi-user concurrency management.

The file-based implementations do not provide database-level access control.

The PostgreSQL implementation does not establish a complete application security model, authenticated approval workflow or immutable external audit infrastructure.

Production deployments should introduce appropriate authentication, authorisation, separation of duties, backup procedures, monitoring, retention rules and transaction controls.

Risk scores also depend on assessment quality. Different assessors may produce different probability and impact estimates. Organisations should therefore establish consistent scoring definitions, evidence requirements and review procedures.

## 18. Execution and File Organisation

The six implementations are independent and can be maintained as separate files.

| File | Runtime or platform |
|---|---|
| `risk_register.py` | Python 3.10+ |
| `risk_register.js` | Node.js 18+ |
| `risk_register.cpp` | C++17 compiler |
| `RiskRegisterApplication.java` | Java 17 |
| `risk_register.sql` | PostgreSQL 15+ |
| `README.md` | Markdown |

No third-party programming-language dependencies are required.

### Execution requirements

- Python: Standard-library execution.
- JavaScript: Node.js standard-library execution.
- C++17: Standard C++17 compilation.
- Java: Java 17 compilation and execution.
- PostgreSQL: Database permissions to create the schema, tables, functions, procedures and triggers.

The Python and JavaScript programs create local JSON persistence files when executed.

The C++ and Java programs demonstrate risk management through in-memory domain models.

The SQL implementation provides persistent relational storage, constraints, reporting and governance evaluation.
