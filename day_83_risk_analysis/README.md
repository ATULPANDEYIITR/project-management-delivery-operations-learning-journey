# Risk Analysis: Understanding Probability and Impact

## 1. Introduction

Risk analysis is a structured process used to identify uncertain events, estimate their likelihood, evaluate their consequences, and determine appropriate organizational responses.

Every risk contains two fundamental dimensions:

- **Probability:** The likelihood that an uncertain event will occur.
- **Impact:** The consequence or loss associated with the event if it occurs.

Probability and impact provide the foundation for risk assessment, prioritization, resource allocation, and management decisions.

A cybersecurity breach, project cost overrun, infrastructure outage, regulatory violation, and operational delay are different risk events. Their probability and consequences must be assessed separately rather than treated as interchangeable uncertainties.

The five implementations provide different engineering perspectives on this process:

| Implementation | Primary perspective |
|---|---|
| Python | Risk register, assessment, reporting, and probabilistic simulation |
| JavaScript | Event-driven risk management and policy evaluation |
| C++17 | Risk computation and portfolio analysis engine |
| Java 17 | Enterprise risk governance and approval workflow |
| PostgreSQL | Persistent relational risk management and reporting |

## 2. Fundamental Concepts

### 2.1 Risk

A risk is an uncertain event or condition that may affect the achievement of an objective.

A risk description should identify:

- The uncertain event.
- Its possible cause.
- Its potential consequence.
- The organizational objective affected.
- The person responsible for monitoring and managing it.

For example:

| Attribute | Example |
|---|---|
| Risk ID | R001 |
| Risk event | Unauthorized system access |
| Cause | Compromised credentials |
| Consequence | Data exposure and financial loss |
| Category | Security |
| Owner | Security Department |

A risk should not be confused with an incident.

A risk represents uncertainty about a possible event. An incident is an event that has actually occurred.

### 2.2 Probability

Probability measures the likelihood of an event occurring.

It is expressed as a value between zero and one.

| Probability | Interpretation |
|---:|---|
| 0.00 | No occurrence under the modeled assumptions |
| 0.10 | 10% likelihood |
| 0.25 | 25% likelihood |
| 0.50 | 50% likelihood |
| 0.75 | 75% likelihood |
| 1.00 | Certain under the modeled assumptions |

Probability can also be expressed as a percentage.

For example:

- 0.20 represents 20%.
- 0.65 represents 65%.
- 0.90 represents 90%.

A probability estimate must have a defined assessment period and reference population.

A 20% probability of an outage during one month is not equivalent to a 20% probability over five years.

Probability estimation can use:

- Historical incident frequencies.
- Statistical models.
- Operational performance data.
- Expert judgment.
- Scenario analysis.
- Bayesian updating.
- Reliability engineering.

Historical frequency is useful but does not guarantee future probability. Changes in technology, operating conditions, threats, and organizational controls can alter the likelihood of an event.

### 2.3 Impact

Impact measures the severity of the consequences if a risk event occurs.

Impact can be expressed in monetary or non-monetary terms.

Financial impact may include:

- Direct financial loss.
- Recovery expenditure.
- Regulatory penalties.
- Business interruption costs.
- Contractual liabilities.
- Replacement and remediation expenses.

Non-financial impact may include:

- Reputational damage.
- Loss of customer confidence.
- Operational disruption.
- Safety consequences.
- Regulatory consequences.
- Loss of sensitive information.

The implementations use monetary impact for quantitative calculations. Other impact dimensions should be evaluated separately when monetary valuation would conceal important consequences.

For example, a security incident with a relatively small direct financial loss may still create severe privacy, legal, or reputational consequences.

## 3. Probability and Impact Relationship

Probability and impact are combined to estimate risk exposure.

### 3.1 Expected Monetary Loss

The fundamental calculation is:

\[
E(L) = P(E) \times I(E)
\]

Where:

- \(E(L)\) = Expected loss.
- \(P(E)\) = Probability of the event.
- \(I(E)\) = Financial impact if the event occurs.

Consider a cybersecurity event with:

- Probability = 0.40.
- Financial impact = ₹500,000.

The expected loss is:

\[
E(L) = 0.40 \times 500000
\]

\[
E(L) = ₹200000
\]

This means that the modeled expected loss is ₹200,000 over the specified assessment period.

It does not mean that the organization will necessarily lose ₹200,000.

The actual outcome could be zero if the event does not occur, or ₹500,000 if it occurs at the modeled impact.

Expected loss is an average over repeated comparable situations or a probability-weighted estimate. It is not a prediction of the exact next outcome.

### 3.2 Comparing Different Risks

Consider three hypothetical risks.

| Risk | Probability | Impact | Expected loss |
|---|---:|---:|---:|
| Cybersecurity breach | 20% | ₹500,000 | ₹100,000 |
| Infrastructure outage | 50% | ₹100,000 | ₹50,000 |
| Training delay | 80% | ₹20,000 | ₹16,000 |

The first risk has the highest expected financial exposure even though its probability is lower than the other two.

This illustrates why probability alone cannot determine risk priority.

Likewise, impact alone cannot determine risk priority.

Both dimensions must be considered.

### 3.3 Expected Loss Limitations

Expected loss is useful for financial comparison, but it does not fully describe risk.

Two risks may have the same expected loss while having very different distributions of possible outcomes.

For example:

| Risk | Probability | Impact | Expected loss |
|---|---:|---:|---:|
| A | 50% | ₹200,000 | ₹100,000 |
| B | 10% | ₹1,000,000 | ₹100,000 |

Both have the same expected loss.

Risk B has a much lower probability but a substantially larger potential consequence.

An organization with limited financial reserves may consider Risk B more serious.

This is why expected loss should be supplemented with severity classification, exposure limits, scenario analysis, and tail-risk measures.

## 4. Qualitative Risk Assessment

Not every risk can be measured reliably in monetary terms.

Qualitative assessment uses categories such as Low, Moderate, High, and Critical.

A common approach uses a five-point probability scale and a five-point impact scale.

### 4.1 Probability Scale

| Score | Classification | Illustrative probability |
|---:|---|---|
| 1 | Rare | 0% to 10% |
| 2 | Unlikely | Above 10% to 30% |
| 3 | Possible | Above 30% to 50% |
| 4 | Likely | Above 50% to 80% |
| 5 | Almost Certain | Above 80% |

The exact boundaries should be defined by organizational policy and the assessment period.

### 4.2 Impact Scale

| Score | Classification | Illustrative financial impact |
|---:|---|---|
| 1 | Insignificant | Up to ₹1,000 |
| 2 | Minor | Above ₹1,000 to ₹5,000 |
| 3 | Moderate | Above ₹5,000 to ₹10,000 |
| 4 | Major | Above ₹10,000 to ₹100,000 |
| 5 | Severe | Above ₹100,000 |

These thresholds are examples. Actual impact scales should reflect organizational size, financial capacity, regulatory obligations, and operational objectives.

### 4.3 Risk Score

A simple qualitative scoring model is:

\[
R = P_s \times I_s
\]

Where:

- \(P_s\) = Probability score.
- \(I_s\) = Impact score.

For example:

Probability score = 4.

Impact score = 5.

\[
R = 4 \times 5 = 20
\]

The resulting score indicates a high-priority risk under the selected scoring policy.

A score of 20 does not represent a 20% probability or a monetary loss. It is an ordinal prioritization score.

### 4.4 Risk Classification

The implementations demonstrate configurable classification policies.

The financial classification used in the code is:

| Expected residual exposure | Classification |
|---:|---|
| Below ₹5,000 | Low |
| ₹5,000 to below ₹25,000 | Moderate |
| ₹25,000 to below ₹100,000 | High |
| ₹100,000 and above | Critical |

These thresholds are illustrative and should be replaced with approved organizational tolerance limits.

Qualitative scores and monetary exposure are separate measurements. They should not be combined without an explicit and defensible calibration method.

## 5. Risk Matrix

A risk matrix combines probability and impact categories.

An illustrative five-by-five matrix is:

| Probability / Impact | 1 Insignificant | 2 Minor | 3 Moderate | 4 Major | 5 Severe |
|---|---:|---:|---:|---:|---:|
| 5 Almost Certain | 5 | 10 | 15 | 20 | 25 |
| 4 Likely | 4 | 8 | 12 | 16 | 20 |
| 3 Possible | 3 | 6 | 9 | 12 | 15 |
| 2 Unlikely | 2 | 4 | 6 | 8 | 10 |
| 1 Rare | 1 | 2 | 3 | 4 | 5 |

An illustrative classification is:

- 1–5: Low.
- 6–10: Moderate.
- 11–15: High.
- 16–25: Critical.

The matrix is useful for prioritizing risks when precise probability distributions or financial estimates are unavailable.

Its limitations include subjective scoring, arbitrary category boundaries, and loss of information when continuous measurements are converted into discrete categories.

A matrix should support management decisions rather than replace professional judgment.

## 6. Inherent and Residual Risk

Risk assessment must distinguish the exposure before controls from the exposure remaining after controls.

### 6.1 Inherent Risk

Inherent risk is the exposure assessed before considering the effect of relevant controls.

For example:

- Probability of a cybersecurity breach = 70%.
- Potential financial impact = ₹500,000.

\[
IR = 0.70 \times 500000
\]

\[
IR = ₹350000
\]

The result is the inherent expected financial exposure.

### 6.2 Risk Controls

Controls are measures designed to prevent an event, reduce its probability, limit its impact, or improve recovery.

Examples include:

| Control | Primary purpose |
|---|---|
| Multi-factor authentication | Reduce unauthorized access |
| Security monitoring | Improve detection and response |
| Data backups | Reduce recovery impact |
| Disaster recovery | Limit service interruption |
| Budget monitoring | Identify financial deviations |
| Regulatory audits | Identify compliance deficiencies |

A control should have an identifiable owner, implementation status, measurable effectiveness, and review frequency.

A documented control should not automatically be considered effective. Evidence of implementation and operating effectiveness is required.

### 6.3 Residual Risk

Residual risk is the exposure remaining after accounting for implemented and effective controls.

The implementations use the following illustrative independent-reduction model.

Let:

- \(P_0\) = Inherent probability.
- \(I_0\) = Inherent impact.
- \(r_i\) = Probability reduction from control \(i\).
- \(m_i\) = Impact reduction from control \(i\).

Residual probability:

\[
P_r = P_0 \prod_{i=1}^{n}(1-r_i)
\]

Residual impact:

\[
I_r = I_0 \prod_{i=1}^{n}(1-m_i)
\]

Residual expected loss:

\[
RE = P_r \times I_r
\]

Consider a risk with:

- Inherent probability = 70%.
- Inherent impact = ₹500,000.
- First control probability reduction = 40%.
- First control impact reduction = 10%.
- Second control probability reduction = 15%.
- Second control impact reduction = 25%.

Residual probability:

\[
P_r = 0.70 \times 0.60 \times 0.85
\]

\[
P_r = 0.357
\]

Residual impact:

\[
I_r = 500000 \times 0.90 \times 0.75
\]

\[
I_r = ₹337500
\]

Residual expected loss:

\[
RE = 0.357 \times 337500
\]

\[
RE = ₹120487.50
\]

The estimated exposure has decreased from ₹350,000 to ₹120,487.50.

### 6.4 Important Assumptions

The multiplicative control model assumes that control effects can be combined independently.

Real controls may overlap.

For example, two monitoring systems may detect the same activity and therefore provide less combined benefit than the mathematical product suggests.

The implementation is a useful computational model, not a universal control-effectiveness formula.

Where control dependencies, common causes, or overlapping effects exist, the organization should use a more appropriate probabilistic or causal model.

## 7. Risk Treatment Strategies

After assessing residual exposure, management determines how the risk should be handled.

Four common treatment strategies are implemented.

### 7.1 Risk Acceptance

The organization consciously accepts the remaining risk.

Acceptance may be appropriate when:

- Residual exposure is within approved tolerance.
- Further mitigation is disproportionately expensive.
- The event has limited consequences.
- The organization has sufficient capacity to absorb the loss.

Acceptance must be documented and approved by an authorized person.

A low calculated expected loss does not automatically authorize acceptance.

### 7.2 Risk Mitigation

Mitigation introduces or improves controls.

Examples:

- Strengthening authentication.
- Implementing recovery infrastructure.
- Increasing monitoring.
- Improving operational procedures.
- Conducting compliance audits.

Mitigation is appropriate when exposure exceeds approved tolerance or the probability or consequences require further reduction.

### 7.3 Risk Transfer

Risk transfer shifts specified financial or contractual consequences to another party.

Examples:

- Insurance.
- Contractual indemnification.
- Outsourcing under defined contractual obligations.

Transfer does not eliminate all organizational risk.

Reputational damage, regulatory responsibility, operational dependency, and uninsured losses may remain.

### 7.4 Risk Avoidance

Risk avoidance removes the activity or condition that creates the risk.

For example, an organization may discontinue a project when its risk exposure is unacceptable.

Avoidance may also involve losing the benefits associated with the activity.

## 8. Risk Prioritization and Portfolio Analysis

An organization may maintain hundreds or thousands of risks.

Risk prioritization helps determine where management attention and resources should be allocated.

The implementations use residual expected exposure as the principal financial ranking metric.

A risk register contains:

- Risk identifier.
- Risk title.
- Description.
- Category.
- Owner.
- Probability.
- Impact.
- Inherent exposure.
- Controls.
- Residual probability.
- Residual impact.
- Residual exposure.
- Status.
- Treatment decision.

Portfolio analysis aggregates exposure across risks.

\[
Portfolio\ Exposure = \sum_{i=1}^{n} E(L_i)
\]

This calculation assumes that the expected losses are measured over compatible periods and on a consistent financial basis.

The aggregate expected exposure does not describe the full portfolio loss distribution.

### 8.1 Risk Categories

The implementations distinguish the following categories:

| Category | Example |
|---|---|
| Strategic | Failure to achieve a business objective |
| Financial | Budget overrun or credit loss |
| Operational | Process failure or service disruption |
| Technology | Infrastructure or software failure |
| Security | Unauthorized access or data breach |
| Compliance | Violation of regulatory requirements |
| Reputational | Loss of stakeholder confidence |

Categorization supports ownership assignment, reporting, and analysis of risk concentration.

## 9. Monte Carlo Risk Simulation

Expected loss provides an average estimate, but it does not fully describe uncertainty in the portfolio.

Monte Carlo simulation models multiple possible outcomes using repeated random experiments.

### 9.1 Basic Mechanism

For each simulation iteration:

1. Generate a random value for each risk.
2. Compare it with the risk's residual probability.
3. Determine whether the event occurs.
4. Add the corresponding residual impact when it occurs.
5. Calculate the total portfolio loss.
6. Repeat for the required number of iterations.

The implementations use a Bernoulli occurrence model.

For a risk with probability \(P\):

\[
X =
\begin{cases}
1 & \text{if the event occurs}\\
0 & \text{otherwise}
\end{cases}
\]

Simulated loss:

\[
L = X \times I
\]

Portfolio loss:

\[
L_p = \sum_{i=1}^{n} X_i I_i
\]

### 9.2 Simulation Outputs

The Python, JavaScript, C++, and Java programs calculate:

| Metric | Meaning |
|---|---|
| Mean loss | Average simulated portfolio loss |
| Median loss | Middle simulated outcome |
| P95 loss | Loss at the 95th percentile |
| P99 loss | Loss at the 99th percentile |
| Maximum simulated loss | Highest observed simulation outcome |
| Standard deviation | Dispersion of simulated outcomes |

The 95th percentile indicates that approximately 95% of modeled outcomes fall at or below that value.

It is not a guarantee that losses will remain below that amount.

### 9.3 Simulation Assumptions

The implementations use independent risk events and fixed impacts.

These assumptions simplify the simulation.

Real organizational risks may be correlated.

For example:

- A cyberattack may simultaneously disrupt several systems.
- A cloud provider outage may affect multiple business services.
- A supplier failure may create operational and financial losses.
- A regulatory event may produce financial and reputational consequences.

Ignoring these relationships can underestimate aggregate exposure.

More advanced models may include:

- Correlation matrices.
- Conditional probabilities.
- Common-cause failures.
- Variable impact distributions.
- Frequency and severity distributions.
- Bayesian networks.
- Stress scenarios.

Monte Carlo outputs are conditional on the input assumptions. Simulation volume does not compensate for inaccurate probability estimates or incomplete risk identification.

## 10. Python Implementation

**File:** `risk_analysis.py`

The Python implementation provides a centralized risk register and a complete assessment workflow.

### 10.1 Domain Modeling

The program uses enumerations for:

- Risk categories.
- Risk statuses.
- Risk levels.
- Treatment decisions.

The `Risk` dataclass stores the principal risk attributes and calculates exposure through properties.

`RiskControl` represents a control with separate probability and impact reduction factors.

This distinction is important because prevention and consequence reduction are different control objectives.

### 10.2 Risk Register

The `RiskRegister` class uses a dictionary indexed by risk identifier.

Its principal operations include:

- Adding risks.
- Retrieving individual risks.
- Filtering by category.
- Prioritizing risks.
- Calculating portfolio exposure.
- Generating classification distributions.

Dictionary-based retrieval has average \(O(1)\) lookup complexity.

Sorting the register for prioritization requires \(O(n \log n)\) time.

### 10.3 Data Persistence

The implementation exports risk information into JSON.

It writes to a temporary file before replacing the destination.

This reduces the possibility of leaving a partially written register when an export operation fails.

The script uses the Python standard library and does not require third-party packages.

### 10.4 Validation

The implementation rejects:

- Empty identifiers.
- Missing titles.
- Missing owners.
- Invalid probabilities.
- Negative impacts.
- Invalid control effectiveness.
- Duplicate risk identifiers.
- Duplicate control names.

It also prevents acceptance of exposure above the configured authorization threshold.

### 10.5 Testing

The script includes assertions for:

- Expected loss.
- Residual probability.
- Residual impact.
- Residual exposure.
- Invalid probability.
- Invalid control effectiveness.

These tests verify the mathematical relationships used by the model.

## 11. JavaScript Implementation

**File:** `risk_analysis.js`

The JavaScript implementation provides an event-driven risk management architecture.

It is designed around asynchronous processing, policy evaluation, and state changes.

### 11.1 Event-Driven Risk Management

The `RiskRepository` extends Node.js `EventEmitter`.

It publishes events when risks are:

- Created.
- Assessed.

Event listeners receive structured snapshots of the relevant risk.

This separates risk management operations from reporting and notification mechanisms.

For example, an assessment event could be used by an enterprise application to trigger:

- Risk dashboard updates.
- Management notifications.
- Audit record creation.
- Escalation workflows.

### 11.2 Maps and Encapsulation

The repository uses a private `Map` to store risks.

This provides efficient identifier-based access and prevents external code from directly manipulating the internal collection.

Private fields also establish a clear boundary between repository operations and stored data.

### 11.3 Asynchronous Assessment

The `assess()` method demonstrates asynchronous risk assessment.

It uses optimistic version checking.

The application compares the version supplied by the caller with the current version before applying changes.

This prevents a stale assessment from silently overwriting a newer one.

Version checking is especially important in systems where multiple users may assess the same risk concurrently.

The example demonstrates an in-memory concurrency pattern. A distributed application requires atomic persistence and concurrency control at its database or service boundary.

### 11.4 Policy Evaluation

`RiskPolicy` evaluates residual exposure and probability against configured thresholds.

The output contains:

- A treatment decision.
- A reason supporting that decision.

Separating policy evaluation from risk storage makes policy changes easier to test and maintain.

### 11.5 Deterministic Simulation

The JavaScript simulation uses a seeded pseudo-random generator.

The same seed and inputs produce repeatable simulation results.

This is useful for testing and comparing changes in assumptions.

The generated values are not cryptographically secure and must not be used for security-sensitive random decisions.

## 12. C++17 Implementation

**File:** `risk_analysis.cpp`

The C++ implementation emphasizes computational efficiency, explicit domain modeling, and controlled access to risk information.

### 12.1 Class-Based Architecture

The principal classes are:

- `Risk`
- `RiskRegister`

Supporting structures include:

- `Control`
- `Policy`
- `SimulationResult`

Enumerations represent risk categories, statuses, treatments, and classification levels.

The `Risk` class encapsulates probability, impact, controls, and treatment-related operations.

### 12.2 Standard Template Library

The implementation uses:

| STL component | Purpose |
|---|---|
| `vector` | Stores controls and simulation results |
| `map` | Maintains the risk register |
| `sort` | Prioritizes risk exposure |
| `find_if` | Checks for duplicate controls |
| `mt19937` | Generates reproducible random sequences |
| `uniform_real_distribution` | Models event occurrence |
| `setprecision` | Formats financial output |

The ordered map provides logarithmic lookup and insertion complexity.

Sorting a portfolio of \(n\) risks requires \(O(n \log n)\) time.

### 12.3 Exception Handling

The program uses exceptions to reject:

- Invalid probability.
- Negative financial impact.
- Duplicate risk identifiers.
- Duplicate controls.
- Invalid treatment conditions.
- Invalid simulation iterations.

These checks prevent invalid data from entering the computational workflow.

### 12.4 Financial Risk Engine

The implementation separately calculates:

- Inherent exposure.
- Residual probability.
- Residual impact.
- Residual exposure.
- Mitigation percentage.

The distinction makes it possible to evaluate whether a control reduces the likelihood of an event, its consequences, or both.

### 12.5 Simulation

The program uses the Mersenne Twister random number generator.

The random seed makes simulation output reproducible.

Simulation results are stored in a vector and sorted to calculate the required percentiles.

For \(n\) risks and \(k\) simulation iterations, the primary simulation complexity is \(O(kn)\), followed by \(O(k \log k)\) sorting.

## 13. Java 17 Implementation

**File:** `RiskAnalysis.java`

The Java implementation emphasizes enterprise application architecture, explicit state transitions, domain validation, and approval workflows.

### 13.1 Records and Enumerations

Java 17 records model immutable value objects.

The implementation uses records for:

- `RiskControl`
- `Assessment`
- `Approval`
- `Policy`
- `RiskReport`

These types represent structured business information that should not be modified after construction.

Enumerations represent the valid categories, risk states, treatment decisions, and approval decisions.

### 13.2 Service and Repository Separation

The implementation uses a `RiskRepository` interface and an `InMemoryRiskRepository` implementation.

The repository manages risk storage.

`RiskAssessmentService` handles:

- Assessment operations.
- Risk prioritization.
- Category filtering.
- Portfolio exposure.
- Risk distribution.

This separation makes the domain logic independent of a specific storage implementation.

A production application could implement the repository interface using a relational database.

### 13.3 Approval Workflow

Risk acceptance is treated as a governed decision.

The workflow contains three stages:

1. A risk owner requests acceptance.
2. The risk enters `PENDING_APPROVAL`.
3. An authorized approver records an approval or rejection.

An approved risk must still satisfy the configured acceptance policy.

Approval and eligibility are separate concepts.

An approval is a management decision. Eligibility represents compliance with defined acceptance conditions.

A rejected request returns the risk to mitigation.

### 13.4 Assessment History

Every assessment is represented as an immutable `Assessment` record.

The risk stores assessment history instead of treating every reassessment as an untraceable replacement.

The assessment operation also uses version checking to detect stale updates.

### 13.5 Java Collections and Streams

The service uses:

- `Map` for repository storage.
- `List` for ordered assessment results.
- `EnumMap` for classification distribution.
- Streams for filtering and aggregation.
- `Comparator` for prioritization.

This architecture is suitable for extending the risk register into a larger enterprise management system.

## 14. PostgreSQL Implementation

**File:** `risk_analysis.sql`

The PostgreSQL implementation provides a persistent relational data model for risk assessment and governance.

Unlike the in-memory implementations, the database maintains relationships, historical assessments, treatment decisions, and audit events.

### 14.1 Relational Structure

The principal relationships are:

    risk_users
        |
        | owns
        v
      risks
        |
        | has
        +--------------------+
        |                    |
        v                    v
    risk_assessments    risk_treatments
        |
        |
      risks
        |
        +--------------------+
        |                    |
        v                    v
  risk_control_mapping   risk_approvals
        |
        |
        v
   risk_controls

The audit log maintains a separate record of significant risk events.

### 14.2 Core Tables

| Table | Responsibility |
|---|---|
| `risk_users` | Organizational users and responsibilities |
| `risks` | Central risk register |
| `risk_assessments` | Probability and impact assessment history |
| `risk_controls` | Preventive and corrective controls |
| `risk_control_mapping` | Many-to-many relationship between risks and controls |
| `risk_treatments` | Treatment assignments and decisions |
| `risk_approvals` | Acceptance approval workflow |
| `risk_audit_log` | Historical risk-management events |

### 14.3 Constraints

The database applies several integrity rules.

Probability must be between zero and one.

Financial impact cannot be negative.

Risk identifiers must follow a defined format.

Email addresses must satisfy the configured validation pattern.

Control effectiveness must be between zero and one.

Foreign keys prevent references to nonexistent organizational users or risks.

Unique constraints prevent duplicate risk identifiers, assessment versions, control names, and risk-approver combinations.

These constraints enforce data integrity independently of the application that accesses the database.

### 14.4 Historical Assessment

The `risk_assessments` table stores assessment versions.

This allows the organization to compare an original assessment with later reassessments.

For example:

| Assessment version | Probability | Impact |
|---|---:|---:|
| 1 | 30% | ₹80,000 |
| 2 | 25% | ₹90,000 |

The probability decreased while the estimated impact increased.

Retaining both assessments supports auditability and trend analysis.

### 14.5 SQL Functions

The database includes functions for:

- Expected loss calculation.
- Risk classification.
- Residual exposure calculation.
- Risk acceptance eligibility.

`calculate_expected_loss()` applies probability and impact validation before returning the expected financial exposure.

`classify_risk()` applies the configured exposure thresholds.

`get_residual_assessment()` calculates the effect of implemented and active controls.

### 14.6 Views

`current_risk_exposure` provides a consolidated view of the current assessment.

It combines:

- Risk identity.
- Risk owner.
- Category.
- Inherent probability.
- Inherent impact.
- Inherent exposure.
- Residual probability.
- Residual impact.
- Residual exposure.
- Classification.

`risk_control_effectiveness` provides a control implementation report.

Views simplify reporting without duplicating the underlying data.

### 14.7 Triggers

The database uses triggers to update risk metadata and record status changes.

When a risk record is updated, the metadata trigger increments its version and updates its timestamp.

When the risk status changes, the audit trigger records the old and new status.

This supports traceability at the database level.

The audit example records important workflow events, but a production audit architecture should also restrict direct modification and deletion of historical audit records.

### 14.8 Transaction Processing

The SQL script demonstrates transaction boundaries for:

- Risk reassessment.
- Risk status updates.
- Audit recording.
- Risk acceptance.
- Approval decisions.

A transaction ensures that related database operations either commit together or roll back together.

The approval procedures lock the relevant risk or approval record during the decision process.

The application should still enforce user authentication and authorization. Database constraints alone do not establish who is entitled to approve a risk.

## 15. Risk Governance and Decision-Making

Risk analysis is not complete when probability and impact have been calculated.

The organization must determine who can make decisions, what exposure is acceptable, and how decisions are documented.

### 15.1 Risk Ownership

Every identified risk should have an accountable owner.

The owner is responsible for:

- Monitoring the risk.
- Maintaining assessment information.
- Coordinating control implementation.
- Reviewing changes in exposure.
- Escalating unacceptable conditions.
- Reporting treatment progress.

Risk ownership should be assigned to a person or formally designated role rather than an undefined department alone.

### 15.2 Risk Appetite

Risk appetite describes the amount and type of risk an organization is willing to pursue or retain while achieving its objectives.

For example:

An organization may accept moderate operational uncertainty but maintain very low tolerance for severe regulatory or information-security consequences.

Risk appetite is a governance decision and should not be inferred solely from the expected-loss calculation.

### 15.3 Risk Tolerance

Risk tolerance defines acceptable variation around an objective or exposure limit.

It can be represented through:

- Maximum financial exposure.
- Maximum downtime.
- Maximum incident frequency.
- Maximum probability.
- Maximum operational disruption.
- Mandatory escalation conditions.

The code implementations demonstrate configurable numerical thresholds.

These thresholds are examples and are not universal standards.

### 15.4 Risk Escalation

A risk should be escalated when:

- Exposure exceeds approved tolerance.
- A critical control fails.
- Probability increases materially.
- Potential impact becomes more severe.
- A regulatory obligation is affected.
- The assigned owner cannot manage the exposure.
- Acceptance requires a higher authorization level.

Escalation should result in a documented management decision.

## 16. Edge Cases and Technical Limitations

Reliable risk analysis requires handling situations that can distort calculations or produce invalid decisions.

| Condition | Required treatment |
|---|---|
| Probability equals zero | Expected loss is zero under the current model |
| Probability equals one | Event is certain under the modeled assumptions |
| Impact equals zero | Financial exposure is zero, but non-financial consequences may remain |
| Negative impact | Reject the assessment |
| Probability above one | Reject the assessment |
| Duplicate risk identifier | Reject registration |
| Missing owner | Reject registration |
| Duplicate control | Reject the control assignment |
| Ineffective control | Do not assume a reduction in exposure |
| Unimplemented control | Exclude it from residual-risk calculations |
| Stale assessment version | Reject the update |
| Excessive residual exposure | Require mitigation or authorized escalation |
| Correlated risks | Use an appropriate dependency model |
| Incomplete assessment data | Prevent eligibility determination |

### 16.1 Zero Probability

A probability of zero produces zero expected loss in the mathematical model.

In practical risk management, a zero probability estimate should be treated cautiously.

It may reflect incomplete information or a model that does not capture the relevant event.

### 16.2 Zero Impact

A zero financial impact does not necessarily mean that the event is harmless.

An event can have legal, operational, environmental, safety, or reputational consequences that are not represented by the monetary field.

### 16.3 Control Effectiveness

The model uses control effectiveness percentages as reductions.

These values should be supported by testing, operational evidence, historical performance, and periodic reassessment.

A control's documented existence does not prove its effectiveness.

### 16.4 Double Counting

When two risks describe the same underlying event, adding their expected losses may double-count exposure.

Risk registers should identify overlapping scenarios and dependencies.

### 16.5 Correlation

Portfolio exposure is more complicated when risks are dependent.

For independent risks, individual expected losses can be added to obtain aggregate expected loss.

For dependent risks, aggregate uncertainty and tail outcomes require an appropriate joint probability model.

## 17. Performance and Security Considerations

### 17.1 Performance

The implementations use appropriate data structures for their respective workloads.

| Component | Principal performance characteristic |
|---|---|
| Python dictionary | Average constant-time identifier lookup |
| JavaScript Map | Efficient keyed access |
| C++ ordered map | Logarithmic lookup and insertion |
| Java LinkedHashMap | Average constant-time keyed access |
| PostgreSQL indexes | Accelerated indexed retrieval |
| Portfolio sorting | \(O(n \log n)\) |
| Monte Carlo simulation | \(O(kn)\) before percentile sorting |

Where \(n\) represents the number of risks and \(k\) represents the number of simulation iterations.

For large portfolios, repeated risk calculations can be cached or materialized where consistency requirements permit.

### 17.2 Security

Risk registers may contain sensitive organizational information.

A production implementation should include:

- Role-based access control.
- Authentication.
- Encryption in transit.
- Encryption at rest.
- Secure database credentials.
- Input validation.
- Audit logging.
- Restricted approval privileges.
- Controlled exports.
- Backup and recovery procedures.
- Retention policies.
- Protection against unauthorized changes.

The example programs demonstrate domain validation and basic audit mechanisms. They are not complete authentication or authorization systems.

Database access should use parameterized queries, restricted database roles, and secure connection settings.

Risk approval must be performed by an authorized identity rather than accepted from an unverified request.

### 17.3 Model Governance

Probability and impact estimates should be periodically reviewed.

A defensible risk model should document:

- Assessment assumptions.
- Assessment period.
- Data sources.
- Estimation methodology.
- Control effectiveness evidence.
- Model limitations.
- Approval authority.
- Changes in assumptions.

Model outputs should be distinguishable from observed incident data and approved management decisions.

## 18. Integrated Risk Analysis Workflow

The implementations collectively represent the following organizational workflow:

    Risk Identification
           |
           v
    Risk Categorization
           |
           v
    Probability Assessment
           |
           v
    Impact Assessment
           |
           v
    Inherent Exposure Calculation
           |
           v
    Risk Classification
           |
           v
    Control Identification
           |
           v
    Control Implementation
           |
           v
    Residual Exposure Calculation
           |
           v
    Risk Prioritization
           |
           v
    Treatment Decision
           |
           +-----------------------+
           |           |           |
           v           v           v
        Accept      Mitigate     Transfer
           |           |           |
           v           v           v
       Approval     Reassess     Monitor
           |
           v
    Risk Monitoring and Reporting

Risk avoidance is another available treatment when the activity generating the exposure can be discontinued.

The workflow is iterative. New information, incidents, control failures, regulatory changes, and operating conditions can require reassessment.

## 19. Comparative Implementation Matrix

| Technical capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Risk identification | Yes | Yes | Yes | Yes | Yes |
| Probability validation | Yes | Yes | Yes | Yes | Yes |
| Impact validation | Yes | Yes | Yes | Yes | Yes |
| Expected loss | Yes | Yes | Yes | Yes | Yes |
| Residual exposure | Yes | Yes | Yes | Yes | Yes |
| Control effectiveness | Yes | Yes | Yes | Yes | Yes |
| Treatment decisions | Yes | Yes | Yes | Yes | Yes |
| Policy evaluation | Basic | Yes | Yes | Yes | Yes |
| Approval workflow | Threshold | Basic | Basic | Yes | Yes |
| Event-driven processing | No | Yes | No | No | Triggers |
| Assessment versioning | No | Yes | No | Yes | Yes |
| Portfolio reporting | Yes | Yes | Yes | Yes | Yes |
| Monte Carlo simulation | Yes | Yes | Yes | Yes | Not implemented |

## 20. Execution and File Structure

The six independent files are:

| File | Execution |
|---|---|
| `risk_analysis.py` | `python risk_analysis.py` |
| `risk_analysis.js` | `node risk_analysis.js` |
| `risk_analysis.cpp` | `g++ -std=c++17 -O2 -Wall -Wextra -pedantic risk_analysis.cpp -o risk_analysis` followed by `./risk_analysis` |
| `RiskAnalysis.java` | `javac RiskAnalysis.java` followed by `java RiskAnalysis` |
| `risk_analysis.sql` | Execute using PostgreSQL through `psql` or a database client |
| `README.md` | Documentation |

The Python and JavaScript implementations require their respective runtimes.

The C++ implementation requires a compiler supporting C++17.

The Java implementation requires Java 17.

The SQL implementation requires PostgreSQL with permission to create a schema, tables, functions, procedures, triggers, and types.

The SQL script creates the `risk_management` schema and its sample records. Its sample approval workflow assumes the example records are executed in the supplied order.

The financial examples use consistent monetary units within each assessment. A production deployment should explicitly define its reporting currency, assessment period, exchange-rate policy, and treatment of inflation.

The implementations establish a common analytical foundation: probability describes how likely an event is, impact describes the consequence if it occurs, and their relationship provides a structured basis for measuring, comparing, prioritizing, and managing organizational risk.
