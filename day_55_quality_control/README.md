# Quality Control for Checking Project Outputs

## Purpose

This project implements a quality control workflow for reviewing deliverables before they are accepted or released. It treats quality control as a measurable process in which outputs are checked against documented requirements, failures are recorded with evidence, corrective actions are tracked, and release decisions are enforced.

The scenario uses project reports, operational dashboards, and data exports. The same workflow can be adapted to software releases, analytical datasets, business documents, and operational deliverables.

The five implementations approach the same domain from different engineering perspectives:

| Implementation | Primary purpose |
|---|---|
| Python | Model inspections, findings, workflow states, audit events, and release decisions |
| JavaScript | Evaluate inspection results and publish domain events in an event-driven workflow |
| C++17 | Implement a governance engine with explicit validation and release gates |
| Java 17 | Represent quality requirements and workflow transitions using enterprise-oriented domain types |
| PostgreSQL | Persist project outputs, requirements, inspection evidence, findings, and audit records |

## Quality Control Concepts

### Requirements and acceptance criteria

A quality requirement defines a condition an output must satisfy. Requirements should be specific enough that different inspectors can evaluate the same evidence consistently.

Examples include:

- All mandatory report sections are present.
- Reported totals reconcile with authoritative source records.
- Dataset columns match an approved schema.
- Required identifiers are unique.
- Charts use the correct units and labels.
- The exported file opens and can be read.

Each requirement has an identifier, description, and mandatory flag. The identifier connects inspection results and findings to the exact condition that was evaluated.

Mandatory requirements affect release eligibility. Optional requirements can identify improvements without necessarily preventing release.

### Inspections and evidence

An inspection records an evaluation of a particular output version. Each checked requirement receives a pass or fail result, with supporting evidence where available.

Useful evidence includes reconciliation totals, validation reports, checklist results, schema comparisons, and reproducible test outcomes.

A missing result is not automatically a pass. If a mandatory requirement was not checked, the implementations create a blocking finding. This prevents incomplete inspections from being mistaken for successful quality control.

### Findings and severity

A finding describes a quality problem discovered during inspection.

| Severity | Typical example | Release implication |
|---|---|---|
| Critical | A deliverable contains a serious integrity or safety failure | Blocks release |
| Major | A mandatory reconciliation or acceptance condition fails | Blocks release |
| Minor | An optional presentation requirement fails | Does not independently block release |
| Observation | An improvement opportunity without a confirmed defect | Requires assessment rather than automatic rejection |

Severity and status represent different dimensions. Severity measures the impact of the finding, while status describes the progress of its corrective action.

The implementations model finding states such as `open`, `fixed`, `verified`, and `accepted`. A correction is not equivalent to verification: a finding can be marked fixed and then checked again before it is considered verified.

### Inspection versus release approval

An inspection evaluates evidence against requirements. Release is a separate authorization decision.

A passing inspection does not automatically make every workflow safe. The release gate also checks the output's current state and whether blocking findings remain unresolved.

This distinction prevents a historical passing inspection from overriding a later failed inspection or an unresolved major defect.

## Quality Control Workflow

The intended lifecycle is:

`Draft → Inspection → Rework → Inspection → Released`

A rejected output follows a separate terminal path.

1. **Define the output.** Record its identity, version, artifact location, and applicable quality requirements.
2. **Inspect the deliverable.** Evaluate the requirements and record results and evidence.
3. **Create findings.** Record failures, severity, and supporting evidence.
4. **Perform corrective work.** Repair the underlying output and update the relevant findings.
5. **Reinspect.** Evaluate the corrected version against the acceptance criteria.
6. **Authorize release.** Confirm that the latest inspection passed and no blocking findings remain open.
7. **Retain audit evidence.** Preserve the decisions, actors, timestamps, and reasons needed to reconstruct the workflow.

The implementations focus on the inspection and release-control portions of this lifecycle. They do not claim to provide a complete artifact storage, correction assignment, or external identity-management platform.

## Python Implementation

The Python file uses dataclasses, enums, type annotations, and standard-library functionality to represent quality control as a domain model.

### Main components

- `QualityRequirement` stores the identifier, description, and mandatory flag.
- `Finding` stores severity, evidence, assignment information, and corrective-action status.
- `Inspection` groups the findings created during a review and calculates whether blocking findings remain.
- `ProjectOutput` manages output state, inspection history, and audit events.

The `inspect()` method validates supplied requirement identifiers, detects missing mandatory checks, and creates findings for failed requirements. A successful inspection moves the output into the inspection state; blocking findings move it into rework.

The `release()` method requires a passing latest inspection and checks for unresolved major or critical findings. Invalid transitions raise exceptions rather than silently permitting release.

### Validation and reporting

`load_requirements()` reads a JSON array and rejects malformed data, incomplete requirement definitions, and duplicate identifiers. `safe_artifact_name()` prevents path components from being used as artifact filenames.

`write_report()` creates a JSON report containing requirements, inspections, findings, and audit history. It writes through a temporary file and then replaces the destination, reducing the chance that an interrupted write leaves a partially written report.

The included unit tests check successful release, failed mandatory checks, missing evidence, unknown requirement identifiers, and unsafe filenames.

Run the file using Python 3.10 or later. It uses only the standard library.

## JavaScript Implementation

The JavaScript file models inspection as an event-driven operation suitable for an application that needs to react to quality decisions.

### Event-driven design

`EventBus` allows listeners to subscribe to named events. When an inspection completes, the workflow emits an event containing the output identifier, actor, timestamp, and decision details.

Listener exceptions are isolated from the completed domain operation. This is useful for monitoring and reporting integrations, although production applications should also log listener failures to a durable monitoring service.

`OutputInspector` stores requirements in a `Map`, validates incoming results, and creates findings for failed or missing mandatory checks.

`QualityWorkflow` manages the output state, records audit events, and enforces release conditions. `Finding` defines allowed corrective-action transitions and rejects invalid state changes.

### Asynchronous report persistence

The report writer uses Node.js filesystem promises to create a directory, write a temporary JSON file with restrictive file permissions, and rename it into place. A unique temporary filename reduces collisions between concurrent writers.

The file includes validation tests for failed reconciliation, unknown requirement identifiers, and unsafe filenames.

Run it with Node.js 18 or later. No external npm packages are required.

The event bus is an in-process mechanism. It does not provide durable delivery, distributed transactions, or guaranteed event delivery after a process crash.

## C++17 Implementation

The C++ program emphasizes an explicit governance engine and predictable control flow.

### Domain design

- `Requirement` defines each acceptance condition.
- `Finding` represents a defect and controls corrective-action transitions.
- `Inspection` evaluates whether its findings block release.
- `QualityEngine` owns requirements, inspection history, output state, and audit events.

The requirement registry uses a `std::map` keyed by requirement identifier. This supports deterministic traversal and efficient identifier lookup.

The inspection method first validates every supplied identifier. It then evaluates all registered requirements, creating a major finding for a missing mandatory check and a severity-appropriate finding for a failed check.

The release method verifies the latest inspection and scans recorded findings for unresolved critical or major defects.

### Engineering trade-offs

The implementation uses value types and standard containers instead of external frameworks. This makes the control logic easy to compile and inspect, but the in-memory audit history disappears when the process exits.

Inspection processing is approximately \(O(R + K \log R)\) for \(R\) registered requirements and \(K\) supplied result identifiers, including map-based validation. Finding and audit history consume additional memory proportional to the number of recorded events.

Compile with a C++17-compatible compiler. The program requires no third-party libraries.

## Java 17 Implementation

The Java implementation emphasizes enterprise domain modeling and explicit validation.

### Domain types

The program uses records for immutable requirement definitions, check results, inspection metadata, and audit events. Enums constrain valid severity and workflow states.

`Output` owns the requirement registry, inspection history, and audit trail. The constructor rejects duplicate requirement identifiers and exposes the requirement registry through an unmodifiable map.

`Inspection` copies its finding list, preventing callers from changing the collection structure after inspection creation. Finding objects retain controlled state transitions for corrective actions.

The `inspect()` method validates input before recording an inspection. The `release()` method checks the latest inspection and searches recorded findings for unresolved blocking defects.

### Enterprise considerations

The model separates domain behavior from persistence and presentation. A production service could place repository interfaces and transaction boundaries around these domain objects while retaining the same acceptance rules.

The current implementation is deliberately in-memory. It does not provide distributed locking, database transactions, authorization, or durable audit storage. Those responsibilities belong to the surrounding application architecture.

Compile and run using Java 17. The implementation requires no third-party dependencies.

## PostgreSQL Implementation

The SQL file persists quality-control data in a relational schema and enforces important rules inside the database.

### Relational model

The primary relationships are:

`Projects → Project Outputs → Inspections → Inspection Results`

`Quality Requirements → Inspection Results`

`Inspections → Quality Findings`

`Project Outputs → Quality Audit`

A project can contain multiple outputs and requirements. An output can have multiple inspections, and each inspection can evaluate multiple requirements. Findings refer to the inspection and requirement that exposed the defect.

The schema uses primary keys, foreign keys, unique constraints, check constraints, and enumerated types to restrict invalid data.

The unique constraint on `(inspection_id, requirement_id)` prevents duplicate results for the same requirement in one inspection. The unique output constraint prevents the same project, output name, and version from being registered twice.

### Database-enforced workflow rules

The finding trigger restricts status changes to defined transitions. A finding cannot be moved out of the verified state, and a finding cannot be verified before it has been marked fixed.

The output trigger blocks changes from terminal states and requires a passing latest inspection before release. It also rejects release when critical or major findings remain open.

The audit trigger records output creation and status changes. The audit table retains the actor, timestamp, event type, and structured details.

These controls protect against application paths that attempt to bypass the intended workflow. In a production deployment, database permissions should prevent ordinary application roles from disabling triggers or modifying audit records directly.

### Inspection function

`complete_inspection()` accepts an output identifier, inspector, JSON results, and notes.

The function:

- Locks the output row while creating the inspection.
- Rejects unknown requirement codes.
- Creates findings for missing mandatory checks.
- Stores results and supporting evidence.
- Determines whether the inspection passes.
- Moves the output into inspection or rework.
- Writes an audit event.

The surrounding transaction ensures that an exception does not leave a partially completed inspection.

`evaluate_output()` calculates release eligibility, including the latest inspection, open blocking findings, and missing mandatory checks. The reporting queries expose inspection evidence and summarize the quality state by project and output.

### Indexing and performance

The schema indexes output status by project, recent inspections by output, unresolved findings by inspection, and audit events by output and timestamp.

The partial index on open findings is useful because release evaluation frequently searches for unresolved blocking defects rather than all historical findings.

The reporting query that summarizes findings may scan multiple inspections and findings for each output. Larger deployments should evaluate query plans and consider precomputed aggregates only if measured workload justifies them.

Run the SQL script in PostgreSQL with permission to create a schema, types, tables, functions, and triggers. It uses a transaction and creates its own `quality_control` schema.

## Interpreting the Results

A failed inspection is not merely a negative status. It is a decision supported by identified requirements and recorded evidence.

For example, suppose a report contains a total of 76,500 while the authoritative source records total 76,440. The discrepancy should become a finding tied to the reconciliation requirement. If reconciliation is mandatory, the finding blocks release until the underlying problem is corrected and the relevant quality conditions are satisfied.

A later passing inspection does not automatically erase the historical failure. Retaining inspection history supports traceability and makes it possible to explain why the output was initially rejected for rework and subsequently released.

The severity of a finding should reflect its operational impact and documented policy. A minor formatting issue should not be treated as equivalent to incorrect financial totals, and a missing mandatory inspection should never be interpreted as evidence that the requirement passed.

## Security, Reliability, and Limitations

The implementations illustrate core controls but are not complete production quality-management platforms.

Important operational safeguards include:

- Authenticate inspectors and release approvers.
- Authorize actions according to project and output ownership.
- Store evidence in controlled artifact storage.
- Protect audit records from unauthorized alteration.
- Validate filenames, input identifiers, and external data.
- Keep database credentials and secrets outside source files.
- Record the inspected artifact version or content hash to link evidence to the exact deliverable.
- Use transaction isolation and appropriate locking when multiple workers inspect or release the same output.
- Separate the authority to inspect from the authority to approve release when policy requires independent review.
- Preserve correction history instead of silently replacing prior inspection evidence.

A further distinction is important: these examples evaluate recorded inspection results, not the actual correctness of an artifact. A result marked as passed is only as reliable as the inspection procedure and evidence supporting it. Production systems should integrate appropriate automated checks, reproducible manual-review procedures, and controls that establish which artifact was inspected.

The central design principle is that quality control must connect explicit requirements, verifiable evidence, controlled corrective actions, and an enforceable release decision.
