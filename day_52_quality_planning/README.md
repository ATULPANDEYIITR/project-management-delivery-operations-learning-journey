# Quality Planning: Planning Quality Requirements

## Purpose

This repository models **Quality Planning** as the disciplined process of defining measurable quality requirements before delivery, selecting verification methods, recording objective evidence, assessing quality risks, and determining whether the planned quality gate can be passed.

The implementation treats quality planning as a control system rather than a collection of generic quality statements.

The central relationship is:

**Quality objective → measurable requirement → verification method → evidence → evaluation → quality gate**

A quality requirement defines the expected condition. Evidence determines whether that condition has actually been achieved. A quality risk represents a threat that can prevent the planned quality level from being reached. The quality gate combines these facts into a release-readiness decision.

## Quality Planning Model

The artifacts use four distinct planning concepts.

| Concept | Purpose | Example |
|---|---|---|
| Quality requirement | Defines the required quality condition | Critical workflows require at least 90% test coverage |
| Metric | Defines how the requirement is measured | `test_coverage` |
| Target | Defines the acceptable threshold | `90%` |
| Verification method | Defines how evidence is obtained | CI coverage report |
| Quality evidence | Records the observed result | `93%`, passed |
| Quality risk | Identifies a threat to quality | Boundary validation may fail |
| Quality gate | Converts quality evidence into a decision | `PASS` or `BLOCKED` |

This separation prevents a planned requirement from being treated as proof of achieved quality.

## Planning Quality Requirements

A useful requirement contains a measurable condition and a defined verification mechanism.

The implementations use requirements such as:

| Requirement | Metric | Target | Verification |
|---|---|---:|---|
| Critical workflow coverage | `test_coverage` | 90% | CI coverage report |
| API performance | `latency_compliance` | 95% | Load test |
| Critical defect freedom | `critical_defect_free` | 100% | Defect audit |
| Security validation | `security_validation` | 100% | Security regression suite |

The target is deliberately represented as data instead of being embedded in application logic. This allows different projects to establish different quality thresholds while using the same evaluation mechanism.

Priority is also explicit. A high-priority requirement contributes more strongly to the readiness score, but a weighted score does not override a failed mandatory requirement.

## Quality Evidence

Quality planning is incomplete when requirements exist without verification evidence.

Evidence contains:

- the requirement being evaluated
- the observed measurement
- a pass or fail result
- the source of the evidence
- the time at which the verification occurred

The examples deliberately include a security requirement with an observed value below its target. This produces a blocked quality gate even though the other requirements pass.

The model therefore distinguishes:

`planned requirement != verified requirement`

A requirement becomes verified only after appropriate evidence has been recorded.

## Risk-Based Quality Planning

Quality planning also considers threats that may prevent requirements from being achieved.

Risk is represented by:

`risk score = probability × impact`

The implementations classify scores into four levels:

| Score | Level |
|---:|---|
| `< 0.25` | Low |
| `0.25–<0.50` | Medium |
| `0.50–<0.75` | High |
| `>= 0.75` | Critical |

A critical risk blocks the quality gate in the supplied scenarios.

This reflects an important planning distinction. A project can satisfy currently measured quality requirements while still carrying a sufficiently severe quality risk to require additional mitigation before release.

## Python Implementation

The Python implementation models the planning process with dataclasses and explicit domain objects.

`QualityRequirement` stores the planned quality condition. Validation prevents invalid targets and priorities from entering the model.

`QualityCheck` represents objective verification evidence. The model rejects evidence for unknown requirements, preventing orphaned quality measurements.

`QualityRisk` calculates its own risk score and classification. This keeps risk-level behavior close to the data that determines it.

`QualityPlan` acts as the central planning aggregate. It maintains requirements, checks, and risks and provides:

- requirement registration
- evidence validation
- risk registration
- latest-evidence lookup
- weighted readiness calculation
- quality-gate evaluation
- JSON export

The readiness calculation uses requirement priority as a weighting factor. Achievement is capped at `100%` so exceptionally high measurements do not distort the score.

The gate remains stricter than the score. Missing evidence, failed checks, or critical risks cause the result to be blocked.

The script also includes executable `unittest` cases for duplicate requirements, unknown evidence, risk classification, failed quality evidence, and JSON serialization.

## JavaScript Implementation

The JavaScript implementation models quality planning as an event-oriented Node.js service.

Private class fields are used for the internal requirement, evidence, and risk collections. This prevents consumers of the class from directly mutating the planning state.

`QualityRequirement`, `QualityCheck`, and `QualityRisk` provide domain validation at object construction time.

The `QualityPlanningEngine` provides the planning workflow:

- register requirements
- record evidence
- register risks
- identify the latest evidence
- calculate readiness
- evaluate the quality gate
- serialize the plan
- persist the plan asynchronously

The file uses Node.js asynchronous file operations to save the quality plan as JSON.

The implementation also demonstrates why asynchronous processing is useful for persistence. Quality planning may be integrated with CI systems, test reports, audit records, or other external sources where non-blocking I/O is appropriate.

The quality gate does not depend only on a numeric score. Failed evidence and critical risks remain explicit blocking conditions.

## C++ Implementation

The C++ program treats quality planning as a governance engine.

The `QualityGovernanceEngine` stores requirements in an ordered map, allowing requirement lookup by stable identifier. Evidence is maintained separately because a requirement may receive multiple verification results over time.

The latest evidence is selected by traversing evidence in reverse insertion order. This provides a simple append-only model suitable for the case study.

The program separates:

- requirement definition
- evidence collection
- risk analysis
- readiness scoring
- gate evaluation

`std::optional` is used to represent missing evidence explicitly. Missing evidence is therefore different from a failed measurement.

The merge/release-style quality gate is intentionally stricter than the readiness score. Every requirement must have passing evidence, and critical risks must be absent.

The program returns a non-zero status when the quality gate is blocked. This behavior makes the model suitable for command-line automation where an external pipeline can interpret the process exit code.

## Java Implementation

The Java implementation uses an enterprise-oriented domain model.

Java records represent immutable domain values:

- `QualityRequirement`
- `QualityEvidence`
- `QualityRisk`

The `QualityPlan` aggregate owns the relationships between requirements, evidence, and risks.

Requirement states are represented explicitly through an enum:

| State | Meaning |
|---|---|
| `PLANNED` | A quality requirement exists but has no successful verification evidence |
| `VERIFIED` | The latest evidence passed |
| `FAILED` | The latest evidence failed |
| `DEFERRED` | Quality verification has intentionally been postponed |

The enterprise model uses separate maps for requirements and their evidence. This preserves the distinction between a requirement and its verification history.

`Optional` is used when evidence may not exist. This prevents missing verification from being represented as a fabricated value.

The `GateDecision` enum expresses the business outcome independently from the readiness score.

This design makes policy behavior explicit: a project does not pass simply because its aggregate score is high. Every requirement must have passing evidence and no critical quality risk may remain.

## PostgreSQL Implementation

The PostgreSQL script represents quality planning as relational data.

The main entities are:

| Table | Responsibility |
|---|---|
| `projects` | Defines the project being planned |
| `quality_requirements` | Stores measurable quality requirements |
| `quality_evidence` | Stores verification results |
| `quality_risks` | Stores quality threats and mitigations |
| `quality_gate_decisions` | Stores auditable gate outcomes |

Foreign keys preserve relationships between the project, requirements, evidence, risks, and decisions.

Check constraints enforce domain rules directly in PostgreSQL. For example, targets and observed measurements must remain between `0` and `100`, while probability and impact must remain between `0` and `1`.

The database therefore rejects invalid quality data even if an application layer fails to validate it.

## Database State Transition

The `quality_evidence` table contains the actual verification history.

An `AFTER INSERT` trigger invokes `refresh_requirement_state()`.

The trigger changes a requirement to:

- `verified` when the new evidence passes
- `failed` when the new evidence fails

This demonstrates a database-level state transition based on recorded quality evidence.

The trigger does not decide whether the entire project is ready. Project-level readiness remains a separate evaluation concern.

## PostgreSQL Quality Evaluation

The `evaluate_project_quality()` function uses several CTEs.

The `latest_evidence` CTE selects the most recent evidence for every requirement.

The `requirement_evaluation` CTE compares observed measurements with their planned targets and calculates achievement.

The `risk_evaluation` CTE identifies critical risks.

The final result combines these conditions into:

- readiness score
- missing requirements
- failed requirements
- critical risks
- quality-gate decision

The resulting decision is `pass` only when all planned requirements have evidence, no requirement has failed, and no critical quality risk remains.

## Transactional Quality-Gate Recording

The sample workflow calculates the quality decision and inserts it into `quality_gate_decisions` inside a transaction.

The transaction ensures that the audit record is either fully written or not written at all.

This is important for governance because a calculated quality decision without a corresponding audit record creates an incomplete release-control history.

## Views and Reporting

`quality_requirement_status` provides a requirement-level reporting view.

It combines:

- project
- requirement
- metric
- target
- current state
- latest observation
- verification result
- verification timestamp

`quality_risk_register` provides a risk-oriented view with calculated risk scores and levels.

These views keep reporting queries separate from the underlying transactional tables.

## Quality Gate Logic

The five implementations intentionally use a two-layer evaluation model.

The first layer is a **readiness score**.

The second layer is a **hard quality gate**.

The readiness score answers:

> How much of the planned quality objective has been achieved according to the weighted evidence?

The quality gate answers:

> Are all mandatory conditions satisfied strongly enough to permit the planned delivery decision?

This distinction prevents a high aggregate score from hiding one critical failed requirement.

For example, if three important requirements achieve strong results but a mandatory security requirement fails, the project remains blocked.

## Failure Conditions

The artifacts explicitly handle several failure conditions.

| Failure | Planning response |
|---|---|
| Duplicate requirement identifier | Reject the requirement |
| Empty requirement description | Reject the requirement |
| Invalid target range | Reject the requirement |
| Invalid priority | Reject the requirement |
| Evidence for unknown requirement | Reject the evidence |
| Missing verification evidence | Block the quality gate |
| Failed verification | Block the quality gate |
| Critical quality risk | Block the quality gate |
| Invalid probability or impact | Reject the risk |
| No requirements | Quality plan is not ready |

These failures are different from one another. Invalid data is rejected during validation, while incomplete or unsuccessful quality evidence is represented as a legitimate planning state that affects the gate.

## Performance Considerations

The in-memory implementations use direct identifier lookup for requirements.

Python uses dictionaries, JavaScript uses `Map`, Java uses `LinkedHashMap`, and C++ uses `std::map`.

Evidence history is retained separately because multiple verification results may exist for the same requirement.

The PostgreSQL implementation adds an index on:

`quality_evidence(requirement_id, checked_at DESC)`

This supports the common query pattern of retrieving the most recent evidence for a requirement.

The project and requirement-state index supports project-level reporting and state filtering.

Indexes are limited to access patterns represented by the quality-planning queries rather than being added indiscriminately.

## Security and Governance Considerations

Quality planning data can contain evidence about security tests, defects, performance, and release readiness. It should therefore be treated as controlled engineering information.

Important controls include:

- validate quality measurements before persistence
- constrain numeric ranges at the database layer
- preserve evidence history rather than overwriting historical results
- retain verification timestamps
- keep quality-gate decisions auditable
- distinguish missing evidence from passing evidence
- avoid allowing a calculated score to bypass mandatory requirements
- protect evidence and risk records from unauthorized modification

The model does not assume that a quality percentage alone establishes security or correctness. A metric is meaningful only when its verification method and evidence source are appropriate to the requirement.

## Relationship Between Planning and Verification

The workflow implemented across the artifacts can be represented as:

**Quality objective**  
↓  
**Measurable requirement**  
↓  
**Target and priority**  
↓  
**Verification method**  
↓  
**Quality evidence**  
↓  
**Risk evaluation**  
↓  
**Readiness score**  
↓  
**Quality gate**

This structure keeps planning separate from actual verification while ensuring that the two are connected through explicit evidence.

## Edge Cases and Limitations

The readiness score is a planning indicator, not a mathematical proof of software quality.

A project may receive strong measurements while still having defects that the selected metrics do not detect.

The examples also use percentage-based metrics for comparability. Real projects may require other measurement types such as:

- defect counts
- response-time percentiles
- failure rates
- escaped-defect rates
- reliability measures
- recovery-time objectives
- accessibility conformance
- security-test findings

A production implementation would normally define metric semantics more precisely, including measurement windows, sampling rules, evidence ownership, acceptable variance, and expiration rules for old evidence.

The supplied model intentionally focuses on the core planning relationship between requirements, measurable targets, evidence, risk, and quality-gate decisions.

## File Responsibilities

| File | Technical perspective | Main responsibility |
|---|---|---|
| Python | Domain simulation and validation | Models requirements, evidence, risks, scoring, export, and tests |
| JavaScript | Event-driven Node.js model | Evaluates and persists a quality plan asynchronously |
| C++17 | Governance engine | Performs deterministic quality-gate evaluation with explicit failure status |
| Java 17 | Enterprise domain model | Uses immutable records, enums, collections, and explicit policy behavior |
| PostgreSQL | Relational governance model | Persists requirements, evidence, risks, state transitions, and audit decisions |

The five implementations represent the same quality-planning domain from deliberately different engineering perspectives rather than reproducing identical source structures.

## Practical Quality-Planning Scenario

The included scenario models a software project preparing for a release.

The project has four planned requirements:

- critical workflow test coverage
- API performance compliance
- critical defect freedom
- security-input validation

Evidence demonstrates that three requirements have passed while the security requirement has failed.

The quality plan therefore produces a blocked decision.

This is intentional. Quality planning is useful precisely because it makes an unacceptable condition visible before the delivery decision is treated as complete.

The risk register independently identifies threats such as malformed-input failures and performance degradation under peak traffic.

The result is a planning system in which quality expectations, measurement, evidence, risk, and governance decisions remain traceable to one another.
