# Risk Identification and Assessment

## 1. Introduction

Risk identification is the systematic process of discovering, describing, recording, and categorizing events or conditions that could affect the achievement of organizational objectives.

It is the starting point of risk management. An organization cannot assess, prioritize, monitor, or respond effectively to an exposure that has not been recognized and documented.

Risk identification focuses on determining:

- What could happen?
- What objectives could be affected?
- What circumstances could cause the event?
- What consequences could follow?
- Where does the exposure originate?
- Who is responsible for examining the risk?
- What evidence supports its existence?

Risk identification does not establish that a negative event will occur. It establishes that a plausible uncertainty deserves examination.

The five implementations provide different perspectives on the same organizational risk management domain.

| Implementation | Engineering perspective |
|---|---|
| Python | Object-oriented risk register and workflow simulation |
| JavaScript | Event-driven identification and asynchronous validation |
| C++17 | Structured risk governance and assessment engine |
| Java 17 | Enterprise domain modeling and policy validation |
| PostgreSQL | Relational risk management and reporting infrastructure |

## 2. Risk Identification Fundamentals

### 2.1 Risk

A risk is the effect of uncertainty on objectives.

A risk may represent a potential negative outcome, a beneficial opportunity, or a combination of uncertain effects. These implementations concentrate on adverse organizational exposures to establish a consistent assessment and prioritization workflow.

A useful risk statement identifies:

1. The underlying cause or condition.
2. The uncertain event.
3. The possible consequence.
4. The organizational objective affected.

For example:

**Cause:** Privileged accounts do not consistently use strong authentication.

**Event:** An attacker obtains access to a privileged account.

**Consequence:** Sensitive production systems become exposed.

This structure is more useful than recording a vague entry such as unauthorized access.

### 2.2 Risk Identification Versus Risk Assessment

These activities are related but distinct.

| Activity | Purpose | Output |
|---|---|---|
| Risk identification | Discover possible exposures | Documented risks |
| Risk analysis | Understand likelihood, consequences, and contributing factors | Risk analysis |
| Risk evaluation | Compare exposure against organizational criteria | Risk priorities |
| Risk treatment | Select actions to address exposure | Treatment plans |
| Risk monitoring | Track changes and treatment effectiveness | Updated risk information |

Risk identification establishes the initial risk record. Risk assessment examines its significance.

### 2.3 Risk Categories

The implementations support ten risk categories.

| Category | Meaning | Example |
|---|---|---|
| Strategic | Threats to long-term objectives | Failed business expansion |
| Operational | Disruptions to business processes | Staffing shortages |
| Financial | Financial losses or instability | Unexpected expenditure |
| Technological | Technology failures | Infrastructure failure |
| Cybersecurity | Unauthorized access or compromise | Credential theft |
| Compliance | Failure to meet legal obligations | Regulatory reporting failure |
| Reputational | Damage to organizational trust | Public disclosure incident |
| Environmental | Environmental hazards | Flooding |
| Human Resource | Workforce-related exposure | Loss of critical expertise |
| Third Party | External dependency exposure | Supplier interruption |

A single event may have consequences across multiple categories. Classification should represent the principal exposure while recording secondary consequences in its description.

## 3. Risk Discovery Methods

Risk identification should use multiple information sources. Depending on one source can create blind spots.

### 3.1 Workshops

Structured workshops bring together employees with different responsibilities and operational knowledge.

Participants identify:

- Process weaknesses.
- Dependency failures.
- External threats.
- Resource constraints.
- Control deficiencies.
- Unexpected operational scenarios.

Workshops are useful for discovering risks that have not yet produced measurable incidents.

### 3.2 Interviews

Interviews obtain information from employees, managers, technical specialists, suppliers, and other stakeholders.

They are particularly useful when risks are associated with informal processes, undocumented dependencies, or knowledge held by specific individuals.

### 3.3 Audits

Audits identify deficiencies in policies, processes, controls, records, and compliance arrangements.

An audit finding may indicate an existing control weakness that creates a future risk.

An audit finding and a risk are not necessarily the same record. The finding provides supporting evidence for the risk.

### 3.4 Incident Analysis

Historical incidents provide information about actual failures.

Incident analysis examines:

- What happened?
- When did it happen?
- What caused the event?
- Which controls failed?
- What was the consequence?
- Could similar circumstances occur elsewhere?

A previous incident may reveal exposure in another process or organizational unit.

### 3.5 Historical Data

Historical operational information can reveal recurring patterns.

Examples include:

- System downtime.
- Supplier interruptions.
- Financial losses.
- Delayed deliveries.
- Security events.
- Equipment failures.

Historical frequency can support probability assessment, although past observations do not guarantee future behavior.

### 3.6 Technical Analysis

Technical analysis examines system architecture, configurations, vulnerabilities, infrastructure, access arrangements, dependencies, and failure scenarios.

For cybersecurity risk identification, relevant observations include:

- Weak authentication.
- Excessive privileges.
- Unpatched software.
- Exposed interfaces.
- Insufficient monitoring.
- Inadequate backup arrangements.
- Vulnerable third-party components.

### 3.7 External Environment Analysis

External factors may create risks that originate outside the organization's direct control.

Examples include:

- Regulatory changes.
- Economic instability.
- Geopolitical developments.
- Natural disasters.
- Supplier market concentration.
- Technological changes.

## 4. Risk Register and Domain Structure

A risk register is the central record of identified organizational risks.

It provides a structured representation of exposures, their ownership, assessment dimensions, supporting evidence, controls, and current status.

The implementations use the following domain relationship:

    Organization
        |
        +-- Users and Risk Owners
        |
        +-- Risk Register
              |
              +-- Risk Identification
              |
              +-- Risk Classification
              |
              +-- Assessment Dimensions
              |
              +-- Evidence Records
              |
              +-- Assigned Controls
              |
              +-- Assessment History
              |
              +-- Risk Status
              |
              +-- Priority Reports

### 4.1 Risk Identity

Each risk receives a unique identifier.

The identifier distinguishes the record from other risks, even when two risks have similar descriptions.

The Python and Java implementations use UUIDs. The C++ implementation uses explicit risk identifiers. The JavaScript implementation uses cryptographically generated UUIDs. PostgreSQL uses generated numeric primary keys and organization-specific risk codes.

### 4.2 Risk Description

A useful risk description should communicate the uncertain event and its potential consequences.

Descriptions should be:

- Specific.
- Understandable.
- Relevant to an objective.
- Distinct from control activities.
- Supported by available information.

A statement such as poor cybersecurity is insufficient because it does not identify a particular event or consequence.

### 4.3 Risk Context

Risk context describes the environment in which an exposure exists.

Examples include:

- Production infrastructure.
- Regulatory reporting.
- Cloud service dependencies.
- Financial operations.
- Supply chain operations.

Context improves classification, comparison, and duplicate detection.

### 4.4 Risk Ownership

Every risk requires an accountable owner.

The risk owner is responsible for ensuring that the exposure is examined, assessed, reviewed, and escalated when necessary.

Ownership does not imply that the owner personally performs every treatment activity.

The implementations validate the presence of an owner, while PostgreSQL also establishes a foreign-key relationship between the risk and the organizational user.

## 5. Risk Assessment Dimensions

The implementations use three assessment dimensions:

- Probability.
- Impact.
- Detectability.

Each dimension uses a scale from 1 to 5.

### 5.1 Probability

Probability estimates the possibility that an event will occur within the defined assessment context and period.

| Score | Interpretation |
|---:|---|
| 1 | Rare |
| 2 | Unlikely |
| 3 | Possible |
| 4 | Likely |
| 5 | Almost certain |

The scale is ordinal. A score of 4 should not automatically be interpreted as twice the probability represented by a score of 2.

### 5.2 Impact

Impact represents the potential consequence if the risk materializes.

Potential consequences include:

- Financial loss.
- Operational interruption.
- Legal exposure.
- Reputational damage.
- Information disclosure.
- Safety implications.
- Service degradation.

| Score | Interpretation |
|---:|---|
| 1 | Negligible |
| 2 | Minor |
| 3 | Moderate |
| 4 | Major |
| 5 | Severe |

The assessment should consider the organization's objectives and applicable impact criteria.

### 5.3 Detectability

Detectability estimates how difficult it may be to discover the relevant problem before or during its consequences.

| Score | Interpretation |
|---:|---|
| 1 | Very easy to detect |
| 2 | Easy to detect |
| 3 | Moderately difficult |
| 4 | Difficult |
| 5 | Very difficult to detect |

A higher detectability score represents greater difficulty in detecting the problem.

This dimension is particularly useful when examining failures that can remain unnoticed for extended periods.

Detectability is not identical to probability. A highly probable event may still be easy to detect.

### 5.4 Inherent Risk Score

Inherent risk represents exposure before considering existing controls.

The implementations calculate:

`Inherent Score = Probability × Impact × Detectability`

The maximum possible score is:

`5 × 5 × 5 = 125`

The minimum possible score is:

`1 × 1 × 1 = 1`

The implementation uses the following prioritization thresholds:

| Score | Classification |
|---:|---|
| 1–14 | Low |
| 15–39 | Moderate |
| 40–74 | High |
| 75–125 | Critical |

These thresholds are illustrative organizational criteria. They should be calibrated against the organization's risk appetite and operating environment.

The multiplication model is a prioritization convention rather than a statistically validated probability model.

## 6. Evidence and Risk Traceability

Evidence provides the basis for identifying and evaluating a risk.

Examples include:

- Audit findings.
- Incident records.
- Interview observations.
- Technical assessment results.
- Historical operational data.
- Workshop findings.
- External notifications.

An evidence record contains:

| Field | Purpose |
|---|---|
| Evidence ID | Unique record identity |
| Reference | Traceable source identifier |
| Description | What the evidence establishes |
| Source | Where the evidence originated |
| Collector | Person recording the evidence |
| Timestamp | When the evidence was collected |

Evidence references should be traceable to authoritative records.

A risk supported by evidence is easier to validate, review, challenge, and reassess.

Evidence should not automatically be treated as proof that an event will occur. It supports the reasoning behind the identified exposure.

The Python, JavaScript, C++, and Java implementations maintain evidence collections within each risk.

PostgreSQL uses a separate `risk_evidence` table, allowing multiple evidence records to be associated with one risk.

## 7. Controls and Residual Risk

Controls are existing or planned measures intended to prevent events, detect problems, or reduce their consequences.

The implementations distinguish three control types.

| Control type | Purpose | Example |
|---|---|---|
| Preventive | Reduce the possibility of an event | Multi-factor authentication |
| Detective | Identify suspicious or abnormal activity | Security monitoring |
| Corrective | Restore operations or limit consequences | Recovery arrangements |

### 7.1 Control Effectiveness

The implementations represent control effectiveness as a value between 0 and 1.

For example:

- 0.00 represents no modeled effectiveness.
- 0.50 represents 50% modeled effectiveness.
- 1.00 represents complete modeled effectiveness.

When multiple independent controls are recorded, the combined effectiveness is calculated as:

`Combined Effectiveness = 1 - Product(1 - Individual Effectiveness)`

For two controls with effectiveness values of 0.55 and 0.30:

`1 - ((1 - 0.55) × (1 - 0.30)) = 0.685`

The combined modeled effectiveness is 68.5%.

This calculation assumes independent control effects. Correlated controls can produce an exaggerated estimate of effectiveness.

A production assessment should also consider control design, operating effectiveness, verification status, dependencies, and implementation evidence.

### 7.2 Residual Risk

Residual risk is the exposure remaining after considering existing controls.

The implementations calculate:

`Residual Score = Inherent Score × (1 - Combined Control Effectiveness)`

For an inherent score of 80 and modeled control effectiveness of 0.685:

`Residual Score = 80 × 0.315 = 25.2`

The inherent classification remains critical, while the modeled residual classification becomes moderate.

These scores are illustrative assessment indicators. They should not be interpreted as measured probabilities of loss.

## 8. Risk Lifecycle and State Management

A risk changes state as it moves through organizational examination and management.

The implementations support:

| State | Meaning |
|---|---|
| Identified | Risk has been recorded |
| Assessed | Assessment dimensions have been evaluated |
| Under Review | Risk is being examined |
| Mitigated | Mitigation controls have been recorded |
| Accepted | Exposure has been formally accepted |
| Closed | Risk record has been closed |

The permitted transitions are:

    Identified
        |
        +------> Assessed
        |           |
        |           +------> Under Review
        |                       |
        |                       +------> Mitigated
        |                       |
        |                       +------> Accepted
        |                       |
        |                       +------> Closed
        |
        +------> Under Review
        |
        +------> Closed

    Mitigated ------> Under Review ------> Closed

    Accepted -------> Under Review ------> Closed

    Closed is terminal.

Invalid transitions are rejected.

For example, a risk cannot move directly from Identified to Mitigated without an assessment or review transition.

Mitigation requires at least one recorded control.

Formal organizational approval of risk acceptance is a separate governance activity. The implementations provide basic state validation, while the Java and PostgreSQL versions introduce explicit policy checks.

## 9. Python Implementation

### 9.1 Architecture

The Python implementation uses dataclasses, enumerations, classes, dictionaries, lists, properties, and exceptions.

Its main components are:

| Component | Responsibility |
|---|---|
| `Risk` | Stores and evaluates an individual risk |
| `RiskEvidence` | Represents supporting evidence |
| `RiskControl` | Represents an assigned control |
| `RiskRegister` | Maintains the organizational register |
| `RiskCategory` | Defines the risk taxonomy |
| `RiskStatus` | Defines workflow states |
| `RiskLevel` | Defines exposure classifications |

### 9.2 Assessment Properties

The `Risk` class exposes calculated properties rather than requiring callers to maintain duplicate score fields.

These include:

- `inherent_score`
- `inherent_level`
- `control_effectiveness`
- `residual_score`
- `residual_level`

This reduces inconsistencies between stored assessment dimensions and calculated results.

### 9.3 Risk Register

The `RiskRegister` class maintains risks in a dictionary indexed by unique risk identifiers.

Its operations include:

- Risk registration.
- Duplicate detection.
- Risk retrieval.
- Category filtering.
- Status filtering.
- Minimum-score filtering.
- Category aggregation.
- Priority reporting.
- JSON export.

Dictionary lookup provides average-case constant-time retrieval by identifier.

Priority reporting requires sorting, with complexity approximately O(n log n) for n registered risks.

### 9.4 Validation and Failure Handling

The implementation rejects:

- Empty titles.
- Missing descriptions.
- Missing owners.
- Invalid assessment dimensions.
- Duplicate risk identifiers.
- Duplicate evidence references.
- Duplicate control identifiers.
- Invalid workflow transitions.
- Mitigation without controls.

The test function verifies classification, scoring, residual exposure, and invalid assessment handling.

The JSON export uses exclusive file creation to prevent accidental replacement of an existing report.

## 10. JavaScript Implementation

### 10.1 Event-Driven Architecture

The JavaScript implementation uses Node.js event-driven capabilities.

The `RiskIdentificationEngine` extends `EventEmitter`.

Important events include:

| Event | Meaning |
|---|---|
| `risk:identified` | A new risk is registered |
| `risk:assessed` | Assessment dimensions are updated |
| `risk:evidence-added` | Evidence is recorded |
| `risk:control-added` | A control is assigned |
| `risk:status-changed` | Risk lifecycle state changes |
| `risk:validated` | External validation completes |

This design separates risk operations from downstream consumers.

An audit logger, notification service, or reporting component can subscribe to relevant events.

### 10.2 Maps and Sets

The implementation uses `Map` for:

- Risk records.
- Evidence records.
- Control records.

This provides efficient identifier-based retrieval and prevents duplicate keys within each collection.

A fingerprint map supports duplicate detection using the combination of normalized title, context, and category.

### 10.3 Asynchronous Validation

The `validateRisk` method accepts an asynchronous validation function.

This allows external checks to be incorporated without blocking the overall event-driven design.

For example, an organization may validate whether a risk has:

- Supporting audit evidence.
- A valid owner.
- An approved classification.
- Required contextual information.

The method validates the returned response structure before emitting its completion event.

### 10.4 Reporting

The dashboard calculates:

- Total risks.
- Critical risks.
- High risks.
- Open risks.
- Category distribution.
- Prioritized risk details.

JSON export uses Node.js file operations with exclusive creation and restricted file permissions.

The event system is synchronous when events are emitted. Consumers requiring durable delivery, retries, or guaranteed processing need a persistent messaging mechanism rather than relying exclusively on in-memory events.

## 11. C++17 Implementation

### 11.1 Domain-Oriented Design

The C++ implementation emphasizes explicit domain modeling and predictable state management.

Its principal components are:

- `Risk`
- `Evidence`
- `Control`
- `RiskRegister`
- `Category`
- `Status`
- `Level`
- `ControlType`

Enumerations prevent arbitrary category and status strings from entering the domain model.

### 11.2 STL Containers

The implementation uses:

- `std::map` for identifier-based risk storage.
- `std::vector` for evidence and controls.
- `std::set` for permitted transitions.
- `std::optional` for optional category filtering.
- STL algorithms for searching and sorting.

The register maintains risks using their identifiers as keys.

The risk prioritization function filters records and sorts pointers to existing risks rather than copying complete risk objects.

### 11.3 State Transition Validation

The transition rules are stored in a map of permitted states.

An attempted invalid transition raises an exception.

The implementation also prevents mitigation without recorded controls.

### 11.4 Performance Characteristics

For n registered risks:

| Operation | Expected complexity |
|---|---|
| Risk lookup using `std::map` | O(log n) |
| Risk insertion | O(log n) |
| Risk filtering | O(n) |
| Risk prioritization | O(n log n) |
| Evidence duplicate search | O(e) |
| Control duplicate search | O(c) |

Here, e represents evidence records per risk and c represents assigned controls per risk.

The ordered map offers predictable logarithmic lookup and iteration.

For larger registers requiring high-frequency identifier retrieval, an unordered container may provide better average-case lookup performance.

### 11.5 Failure Handling

The implementation uses standard exceptions for invalid input, missing records, duplicate evidence, duplicate controls, and invalid state changes.

The main function catches standard exceptions and returns a nonzero process status when processing fails.

## 12. Java 17 Implementation

### 12.1 Enterprise Domain Modeling

The Java implementation uses records, enums, immutable value structures, interfaces, collections, streams, and dedicated service classes.

Its domain separates:

- Assessment dimensions.
- Evidence.
- Controls.
- Risk policies.
- Risk records.
- Validation rules.
- Governance operations.

### 12.2 Records

The `Assessment`, `Evidence`, and `Control` records represent value-oriented domain information.

Their constructors validate incoming data.

This ensures that invalid values are rejected when the objects are created rather than discovered later during reporting.

### 12.3 Policy Objects

`RiskPolicy` represents organizational assessment rules.

The default policy defines:

- Maximum acceptable inherent score.
- Evidence requirements.
- Owner requirements.
- Senior review requirements.

This separates organizational governance criteria from individual risk records.

### 12.4 Validation Interfaces

`RiskValidationRule` defines a common interface for validation rules.

Two implementations are provided:

- `EvidenceValidationRule`
- `SeniorReviewRule`

Additional enterprise rules can implement the same interface without changing the core risk domain.

### 12.5 Governance Service

`RiskGovernanceService` coordinates:

- Risk identification.
- Duplicate detection.
- Risk retrieval.
- Evidence validation.
- Acceptance checks.
- Risk searches.
- Category aggregation.

The service uses streams to filter and sort records.

`List.copyOf` and immutable record structures help prevent unintended modification of exposed collection data.

### 12.6 Policy Conflicts

The acceptance policy rejects risks whose inherent exposure exceeds the configured acceptance threshold.

This is distinct from the residual exposure calculation.

A high inherent score cannot automatically become acceptable merely because controls reduce its calculated residual score.

An actual organization may permit exceptions through formally documented approvals, but the supplied default policy does not implement an exception or override mechanism.

## 13. PostgreSQL Implementation

### 13.1 Relational Architecture

The SQL implementation uses a dedicated `risk_management` schema.

Its principal tables are:

| Table | Purpose |
|---|---|
| `organizations` | Organizational identity |
| `users` | Organizational users and risk owners |
| `risks` | Main risk register |
| `risk_evidence` | Supporting evidence |
| `controls` | Organizational control catalogue |
| `risk_controls` | Risk-to-control assignments |
| `risk_assessment_history` | Historical assessments |
| `risk_policies` | Organizational governance criteria |

The principal relationships are:

    organizations
        |
        +------ users
        |         |
        |         +------ risks
        |                   |
        |                   +------ risk_evidence
        |                   |
        |                   +------ risk_assessment_history
        |                   |
        |                   +------ risk_controls
        |                              |
        +------ controls --------------+

        +------ risk_policies

A risk belongs to one organization and has one accountable owner.

A risk can have multiple evidence records and multiple assigned controls.

The `risk_controls` table implements the many-to-many relationship between risks and controls.

### 13.2 Referential Integrity

Primary keys establish record identity.

Foreign keys enforce relationships between organizational entities.

Unique constraints prevent duplicate identifiers within their relevant scopes.

Check constraints enforce:

- Valid assessment scales.
- Valid control effectiveness.
- Valid implementation statuses.
- Valid policy thresholds.
- Consistent closure timestamps.

A partial unique index prevents duplicate active risks with the same normalized title and context within an organization.

Closed risks are excluded from that uniqueness rule.

### 13.3 Assessment Functions

`calculate_inherent_score` validates the three assessment dimensions and calculates exposure.

`classify_risk` maps an exposure score to a risk classification.

Both functions are immutable because their results depend only on their inputs.

### 13.4 Assessment Views

`v_risk_assessment` calculates inherent exposure and modeled control effectiveness.

`v_risk_priority` extends the assessment view with residual classifications.

The views avoid maintaining manually synchronized score fields in the primary risk table.

They provide a consistent reporting interface.

### 13.5 Triggers

The `trg_risk_transition` trigger validates changes to risk status.

It also updates:

- Last review timestamp.
- Record version.
- Closure timestamp.

The `trg_assessment_history` trigger records changes to assessment dimensions.

This preserves a historical assessment trail instead of relying only on the latest values.

### 13.6 Eligibility Evaluation

The `evaluate_risk_eligibility` function checks an individual risk against the organization's active policy.

It examines:

- Policy availability.
- Supporting evidence.
- Active ownership.
- Senior review requirements.
- Acceptance thresholds.
- Verified controls for mitigated risks.

It returns an eligibility result and an array of validation findings.

Eligibility is a governance decision input. It does not itself perform risk acceptance or treatment.

### 13.7 Transaction Processing

The reassessment procedure updates the risk dimensions and records the assessment change.

The sample transaction demonstrates controlled workflow execution.

PostgreSQL transactions ensure that database changes can be committed or rolled back as a unit.

For concurrent production workloads, risk updates should also use suitable row locking or optimistic version checks where multiple users may modify the same risk simultaneously.

### 13.8 Indexing

The implementation creates indexes for common access patterns:

- Organizational risk prioritization.
- Category and status filtering.
- Owner-based retrieval.
- Recent risk identification.
- Evidence retrieval.
- Control assignments.
- Assessment history.

Index selection should be validated against actual query plans and data volume. Additional indexes increase storage requirements and write costs.

## 14. Practical Risk Identification Workflow

A typical organizational workflow is:

| Stage | Activity | Output |
|---|---|---|
| 1 | Define objectives and context | Assessment boundaries |
| 2 | Collect information | Discovery evidence |
| 3 | Conduct workshops and analysis | Potential risk scenarios |
| 4 | Write structured risk statements | Identified risks |
| 5 | Assign categories and owners | Classified risk records |
| 6 | Record supporting evidence | Traceable risk documentation |
| 7 | Assess probability, impact, and detectability | Inherent exposure |
| 8 | Examine existing controls | Control information |
| 9 | Calculate residual exposure | Remaining exposure |
| 10 | Apply organizational criteria | Prioritized risk register |
| 11 | Review and update records | Current risk information |

A practical example is a cloud-service dependency.

1. Historical incidents reveal repeated supplier interruptions.
2. The interruption scenario is documented as a third-party risk.
3. Its operational context and accountable owner are recorded.
4. Historical incident records are attached as evidence.
5. Probability, impact, and detectability are assessed.
6. Continuity controls are examined.
7. Residual exposure is calculated.
8. The risk is prioritized for management review.

## 15. Edge Cases and Failure Conditions

Reliable risk identification systems must address incomplete and inconsistent information.

| Condition | Required handling |
|---|---|
| Missing risk description | Reject registration |
| Missing owner | Reject registration |
| Invalid assessment scale | Reject assessment |
| Duplicate risk | Reject or investigate possible duplication |
| Missing evidence | Flag policy violation |
| Duplicate evidence reference | Reject duplicate |
| Duplicate control identifier | Reject duplicate |
| Invalid state transition | Reject transition |
| Mitigation without controls | Reject transition |
| Missing active policy | Report ineligibility |
| Inactive risk owner | Flag governance violation |
| Incomplete historical information | Record uncertainty explicitly |

### 15.1 Duplicate Identification

Different teams may describe the same underlying exposure using different terminology.

Exact title matching alone is insufficient.

Production implementations can improve duplicate detection using:

- Normalized descriptions.
- Organizational context.
- Category comparisons.
- Common causes.
- Related incidents.
- Dependency relationships.
- Human review.

Automated duplicate detection should identify possible duplicates rather than silently discard distinct risks.

### 15.2 Incomplete Evidence

A risk can be identified before supporting evidence is fully collected.

The absence of evidence should not automatically mean that the risk does not exist.

The organization should distinguish between:

- An identified risk awaiting evidence.
- A risk supported by documented evidence.
- An unverified assumption.
- A rejected or invalid risk record.

### 15.3 Changing Conditions

Risk information can become outdated because of:

- New incidents.
- Organizational restructuring.
- Supplier changes.
- New technologies.
- Regulatory changes.
- Control failures.
- Environmental developments.

Risk identification is therefore an ongoing process rather than a one-time activity.

## 16. Security, Governance, and Operational Considerations

A production risk register may contain sensitive security findings, supplier information, operational weaknesses, and compliance observations.

Important safeguards include:

- Role-based access to risk records.
- Restricted access to sensitive evidence.
- Authentication for risk-management operations.
- Encryption in transit and at rest.
- Audit trails for assessment changes.
- Controlled policy modifications.
- Backup and recovery procedures.
- Data retention policies.
- Separation of duties for sensitive approvals.
- Protection against unauthorized deletion or alteration.

The sample implementations demonstrate domain validation and basic data-integrity controls. They are educational reference systems, not complete production security platforms.

In particular, the Python and C++ implementations maintain in-memory records, while the JavaScript implementation uses in-memory event processing. The Java implementation provides a service-oriented domain model. PostgreSQL provides persistent relational storage and database-level integrity enforcement.

## 17. Important Modeling Limitations

The implementations deliberately use a common assessment model to make their behavior comparable.

The model has several limitations.

### 17.1 Ordinal Scales

Probability, impact, and detectability are ordinal ratings.

Multiplication creates a useful prioritization score but does not establish a statistically calibrated measure of expected loss.

### 17.2 Control Independence

The combined control effectiveness calculation assumes independent effects.

Controls that depend on the same infrastructure, identity provider, personnel, or operational process may fail together.

Their effectiveness should not be treated as independent without supporting justification.

### 17.3 Qualitative and Quantitative Risk

The implementations use a simplified numeric model.

Organizations may also use:

- Scenario analysis.
- Financial loss estimates.
- Failure Mode and Effects Analysis.
- Fault Tree Analysis.
- Bow-tie analysis.
- Threat modeling.
- Business Impact Analysis.
- Monte Carlo simulation.

Different methods address different types of uncertainty and should not be treated as interchangeable.

### 17.4 Risk Appetite

The thresholds used in the implementations are illustrative.

Actual risk acceptance criteria must reflect organizational objectives, legal requirements, financial capacity, operational constraints, and approved risk appetite.

### 17.5 Historical Data

Historical incidents can support identification and assessment but may not represent new threats, changing dependencies, or emerging failure patterns.

Risk owners should document assumptions and uncertainty rather than treating historical observations as definitive predictions.

## 18. Cross-Language Implementation Comparison

| Capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Risk modeling | Dataclasses | Classes | Classes and structs | Records and classes | Relational tables |
| Taxonomy | Enums | Frozen objects | Enums | Enums | Enum types |
| Evidence | Lists | Maps | Vectors | Maps | Separate table |
| Controls | Dataclasses | Maps | Structs | Records | Related tables |
| Validation | Exceptions | Custom errors | Exceptions | Custom exceptions | Constraints and functions |
| State management | Methods | Event-driven methods | Transition map | Domain methods | Trigger |
| Risk scoring | Properties | Getters | Methods | Methods | SQL functions |
| Reporting | Dictionaries | JSON objects | STL containers | Streams | Views and queries |
| Persistence | JSON export | JSON export | In-memory | In-memory | Relational database |
| Governance | State rules | Event validation | Transition rules | Policy objects | Eligibility function |

## 19. Execution and Compilation

### Python

Save the first implementation as `risk_identification.py`.

Execute:

`python risk_identification.py`

The script uses only the Python standard library.

### JavaScript

Save the second implementation as `risk_identification.js`.

Execute:

`node risk_identification.js`

Node.js 18 or later is recommended.

### C++17

Save the third implementation as `risk_identification.cpp`.

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic risk_identification.cpp -o risk_identification`

Execute:

`./risk_identification`

On Windows, execute `risk_identification.exe`.

### Java 17

Save the fourth implementation as `RiskIdentificationSystem.java`.

Compile:

`javac --release 17 RiskIdentificationSystem.java`

Execute:

`java RiskIdentificationSystem`

### PostgreSQL

Save the fifth implementation as `risk_identification.sql`.

Execute:

`psql -U postgres -d postgres -f risk_identification.sql`

The executing database role must have permission to create schemas, types, tables, functions, procedures, and triggers.

The script creates a dedicated schema named `risk_management`.

## 20. Educational Outcomes

The implementations demonstrate how risk identification can be translated into executable software and persistent data structures.

The central technical distinctions are:

- Identification establishes that a potential exposure exists.
- Classification organizes the exposure into a meaningful category.
- Evidence supports the identification and its underlying assumptions.
- Assessment examines probability, impact, and detectability.
- Inherent exposure represents risk before controls.
- Controls represent measures intended to address exposure.
- Residual exposure represents the remaining modeled risk.
- Ownership establishes accountability.
- Governance policies determine whether organizational requirements are satisfied.
- Monitoring keeps risk information current.

Together, these mechanisms provide a structured foundation for maintaining an auditable, evidence-supported, and consistently assessed organizational risk register.
