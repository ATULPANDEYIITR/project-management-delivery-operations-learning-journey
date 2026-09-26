# Scope Validation: Checking Completed Work Against Requirements

## 1. Topic Introduction

Scope validation is the systematic process of checking completed work against an agreed set of requirements, acceptance criteria, constraints, and boundaries.

The central question is not simply:

`Was the work completed?`

The more precise question is:

`Does the completed work satisfy the defined scope, and is that satisfaction supported by sufficient evidence?`

This distinction is important because a project can contain work that is technically complete but does not satisfy the original requirement. A requirement can also be marked complete without adequate evidence. Conversely, a team can deliver useful functionality that was never part of the approved scope.

Scope validation therefore connects four important elements:

1. The approved scope.
2. The requirements derived from that scope.
3. The work that was actually completed.
4. Evidence demonstrating whether the requirements were satisfied.

The three implementations in this topic model these relationships using Python, JavaScript, and C++.

---

## 2. Fundamental Concepts

### 2.1 Scope

Scope defines the boundaries of work.

It answers questions such as:

- What must be delivered?
- What is explicitly included?
- What is explicitly excluded?
- What constraints apply?
- What acceptance conditions must be satisfied?

A scope boundary should be sufficiently precise that another person can determine whether a completed item belongs inside or outside the agreed work.

### 2.2 Requirement

A requirement is a specific condition that the delivered system, product, process, or service must satisfy.

Examples include:

- Users can authenticate.
- Users can reset passwords.
- Audit events are retained.
- API response latency remains below a specified threshold.
- A report must be exported in a specified format.

The Python, JavaScript, and C++ implementations represent requirements as structured objects containing an identifier, description, type, mandatory status, acceptance criteria, dependencies, and completion status.

### 2.3 Requirement Identifier

A unique identifier such as `REQ-001` makes a requirement traceable.

Identifiers are preferable to relying only on descriptions because descriptions may change while the logical requirement remains the same.

### 2.4 Requirement Type

The implementations distinguish several requirement categories:

- Functional
- Non-functional
- Compliance
- Constraint

A functional requirement describes behavior.

A non-functional requirement describes a quality attribute or measurable operating condition.

A compliance requirement represents an externally imposed or internally governed obligation.

A constraint restricts how the work can be performed.

### 2.5 Mandatory Requirement

A mandatory requirement must be satisfied before the defined scope can be considered complete.

Optional requirements can be delivered without necessarily preventing scope validation from passing.

The implementations deliberately distinguish mandatory from optional work rather than treating every requirement identically.

---

## 3. Completion Versus Validation

Completion and validation are related but different concepts.

A status such as `complete` is a claim about the state of an item.

Validation checks that claim against objective conditions.

For example:

`REQ-001 = complete`

does not by itself prove that authentication works.

Evidence might consist of:

- Automated tests.
- Manual acceptance tests.
- Browser tests.
- Compliance records.
- Performance measurements.
- Approved documents.
- Demonstration results.
- Deployment verification.

The implementations therefore treat completion status and evidence as separate pieces of information.

A requirement marked complete without evidence can produce a validation finding.

This is one of the most important principles in scope validation:

**A completion claim is not equivalent to validated completion.**

---

## 4. Acceptance Criteria

Acceptance criteria define observable conditions that determine whether a requirement has been satisfied.

For example, an authentication requirement may contain:

`valid credentials accepted`

and

`invalid credentials rejected`

Both conditions must be demonstrated if both are part of the requirement.

Acceptance criteria are more precise than a broad statement such as:

`Authentication works.`

The Python implementation checks a requirement against a set of completed criteria and returns the missing criteria.

The JavaScript implementation performs the same conceptual operation using JavaScript collections.

The C++ case study represents acceptance criteria as a vector associated with each requirement and checks them against a set of completed criteria.

---

## 5. Evidence and Traceability

Traceability connects a requirement to evidence.

A basic relationship is:

`Requirement -> Evidence`

For example:

`REQ-001 -> EV-001`

where `EV-001` might represent an automated authentication test.

Traceability provides several benefits:

- Auditing.
- Reproducibility.
- Accountability.
- Defect investigation.
- Release validation.
- Change management.
- Compliance verification.

The implementations use evidence identifiers and requirement identifiers to create these relationships.

### Evidence Properties

The example evidence model contains:

- Evidence ID.
- Requirement ID.
- Description.
- Source.
- Validity state.

Production systems can extend this with:

- Timestamp.
- Author.
- Version.
- Environment.
- Build identifier.
- Test result.
- Digital signature.
- Approval status.
- Hash.
- Immutable storage reference.

---

## 6. Requirement Traceability Matrix

A requirement traceability matrix is a structured representation of requirement coverage.

The implementations produce rows containing information such as:

- Requirement ID.
- Requirement description.
- Mandatory status.
- Completion status.
- Evidence count.
- Traceability state.

A simplified conceptual matrix is:

| Requirement | Mandatory | Status | Evidence | Traceable |
|---|---|---|---|---|
| REQ-001 | Yes | Complete | 1 | Yes |
| REQ-002 | Yes | Complete | 1 | Yes |
| REQ-003 | Yes | Complete | 1 | Yes |
| REQ-004 | No | Complete | 1 | Yes |
| REQ-005 | Yes | In Progress | 0 | No |

This matrix makes gaps visible without requiring someone to inspect the entire project manually.

---

## 7. Python Implementation

The Python program begins with enumerations for requirement type, status, and finding severity.

The `Requirement` dataclass provides a structured representation of scope requirements.

The `Evidence` dataclass represents validation evidence.

The `Finding` dataclass represents a validation problem.

The `ValidationResult` dataclass provides a machine-readable validation result.

### Basic Validation

The function `validate_basic_status()` identifies mandatory requirements that are not complete.

This is intentionally simple because status checking is only the first layer of validation.

### Acceptance Validation

`validate_acceptance_criteria()` checks whether every required acceptance criterion has been demonstrated.

This prevents a requirement from passing merely because its overall status has been set to `complete`.

### ScopeValidator

The `ScopeValidator` class performs requirement-to-evidence validation.

Its logic distinguishes:

- Complete requirements with evidence.
- Complete requirements without evidence.
- Incomplete mandatory requirements.
- Optional requirements.
- Validation findings.

### RequirementMatrix

`RequirementMatrix` creates a traceability view of the project.

This demonstrates how validation data can be transformed into a structure suitable for reporting or dashboard generation.

### RuleBasedValidator

The Python implementation also introduces reusable validation functions.

Examples include:

- `require_evidence`
- `reject_blocked_requirement`
- `check_dependency_status`

This demonstrates a rule-based architecture in which additional validation rules can be introduced without rewriting the complete validation engine.

---

## 8. JavaScript Implementation

The JavaScript implementation uses objects, classes, arrays, `Map`, `Set`, Promises, and asynchronous functions.

This is useful for applications where scope validation occurs inside:

- Web applications.
- Project dashboards.
- Browser-based acceptance testing.
- Node.js services.
- Continuous integration systems.

### EvidenceIndex

The `EvidenceIndex` class creates an index keyed by requirement ID.

Instead of repeatedly searching an entire evidence array, validation can retrieve relevant evidence through a map.

This is especially useful when the number of requirements and evidence records grows.

### ScopeValidationEngine

`ScopeValidationEngine` coordinates requirements, evidence, and validation rules.

It returns a structured object containing:

- Pass/fail state.
- Coverage percentage.
- Mandatory requirement count.
- Satisfied mandatory requirement count.
- Findings.

### Asynchronous Validation

The function `validateExternalEvidence()` demonstrates an asynchronous validation pattern.

In a production environment, the external evidence could come from:

- A CI service.
- A test server.
- A database.
- A document repository.
- An audit platform.

The example deliberately uses a small delay to model an external operation without introducing an external dependency.

### Browser Validation

`validateRenderedScope()` demonstrates another important JavaScript-specific application.

A browser application can validate whether required interface elements actually exist in the rendered document.

For example, a requirement may specify that a dashboard must contain:

- A navigation element.
- A status panel.
- A search control.

The validator can inspect the DOM rather than relying only on source-code claims.

---

## 9. C++ Industry-Style Case Study

The C++ implementation models a software delivery validation system.

The scenario contains:

- Functional requirements.
- Compliance requirements.
- Non-functional requirements.
- Optional functionality.
- Dependencies.
- Acceptance criteria.
- Evidence.
- Traceability.
- Validation findings.
- Release gating.

### Problem Being Solved

A development team has completed part of a software product.

The organization needs to determine whether the mandatory scope is sufficiently validated for release.

The system must distinguish between:

1. Work that is approved and completed.
2. Work that is approved but incomplete.
3. Work that is completed but outside the approved scope.
4. Work that is marked complete without evidence.
5. Work that is blocked.
6. Work that has sufficient validation evidence.

### Major Components

The program contains:

`Requirement`

Represents an approved requirement.

`Evidence`

Represents proof associated with a requirement.

`Finding`

Represents a validation problem.

`ValidationResult`

Represents the aggregate validation state.

`EvidenceIndex`

Provides efficient requirement-to-evidence lookup.

`ScopeValidator`

Performs the central validation process.

### Evidence Indexing

A naive implementation could search every evidence record for every requirement.

If there are `R` requirements and `E` evidence records, repeated scanning can approach:

`O(R × E)`

The C++ implementation instead creates an `unordered_map` indexed by requirement ID.

This makes retrieval of evidence for a known requirement approximately constant-time on average, subject to hash-table behavior.

The JavaScript implementation applies the same architectural idea with `Map`, while the Python implementation demonstrates it with a dictionary.

---

## 10. Scope Boundary Validation

Scope validation should not only ask whether required work exists.

It should also identify work outside the approved boundary.

The implementations compare:

`approved scope`

with

`completed work`

This produces three useful categories:

### Delivered In Scope

Work exists and belongs to the approved scope.

### Completed Outside Scope

Work was completed but was not included in the approved scope.

This is not automatically a defect.

It is a governance condition that requires an explicit scope decision.

Unapproved additional functionality can create:

- Additional maintenance obligations.
- New security exposure.
- Additional testing requirements.
- Increased operational complexity.
- Schedule effects.
- Documentation obligations.
- Support requirements.

### Approved but Missing

The work is part of the agreed scope but has not been completed.

This category is usually the most direct scope-completion gap.

---

## 11. Scope Creep

Scope creep occurs when the scope of work expands without appropriate control or approval.

Examples include:

- Adding an export system that was not requested.
- Adding additional user roles.
- Adding a new integration.
- Expanding a reporting system.
- Adding unrelated UI features.

The important distinction is between:

`approved scope change`

and

`uncontrolled scope expansion`

An approved change can legitimately modify the scope baseline.

An uncontrolled addition should be flagged for review.

The implementations therefore identify out-of-scope completed work without automatically declaring that it is unacceptable.

---

## 12. Validation Coverage

A useful metric is mandatory evidence coverage.

The implementations calculate coverage using the number of mandatory requirements that are both:

1. Complete.
2. Supported by valid evidence.

Conceptually:

`Coverage = satisfied mandatory requirements / total mandatory requirements × 100`

A project with 100% implementation completion can still have less than 100% validation coverage if some requirements lack evidence.

This distinction prevents status dashboards from confusing development progress with validation confidence.

---

## 13. Validation Findings

A finding describes a condition requiring attention.

The examples use several severity levels:

- Low
- Medium
- High
- Critical

Severity should be defined by organizational policy.

A typical interpretation is:

### Low

The issue has limited scope impact and does not threaten the primary validation objective.

### Medium

The issue requires attention but may not block the defined release gate.

### High

The issue affects a mandatory requirement and normally prevents a complete validation decision.

### Critical

The issue represents a severe blocking condition.

The exact meaning of severity should be established before using these categories in production governance.

---

## 14. Release Gates

A release gate converts validation results into a controlled decision.

The examples distinguish:

`VALIDATED`

from

`NOT READY`

and

`BLOCKED`

The release gate in the implementations is intentionally simple.

A real organization may impose additional gates involving:

- Security approval.
- Legal review.
- Compliance approval.
- Performance acceptance.
- Data protection requirements.
- Deployment readiness.
- Business-owner acceptance.
- Operational readiness.

Scope validation should therefore be treated as one part of a broader delivery governance system when such controls are required.

---

## 15. Edge Cases

Scope validation becomes difficult when real-world conditions are considered.

### Requirement Marked Complete Without Evidence

A status field can be manually changed without the underlying work being demonstrated.

The validator flags this condition.

### Optional Requirement Not Completed

An optional requirement may remain incomplete without blocking mandatory scope validation.

The distinction between mandatory and optional scope is therefore important.

### Blocked Mandatory Requirement

A blocked mandatory requirement prevents full scope validation.

### Empty Scope

If a system contains no mandatory requirements, the example implementations treat mandatory coverage as 100%.

Production systems may instead choose to reject an empty scope definition because an empty scope can indicate a configuration error.

### Invalid Evidence

Evidence marked invalid is excluded from the evidence index.

### Duplicate Evidence

Multiple evidence records may support the same requirement.

This can be useful when one requirement requires several independent validation activities.

### Requirement Dependencies

A requirement can depend on another requirement.

Dependency validation becomes especially important when the completion of one feature logically depends on another feature being available.

---

## 16. Exceptions and Error Handling

The Python implementation uses normal Python exceptions and structured validation results.

The JavaScript implementation uses `try` and `catch` for invalid input and handles asynchronous failures.

The C++ implementation uses `std::invalid_argument` and catches standard exceptions in `main()`.

A production validation system should distinguish between:

- Validation failure.
- Invalid input.
- System failure.
- External evidence failure.
- Configuration failure.

These conditions should not be treated as identical.

A requirement that fails validation is different from a validation service that crashes before it can evaluate the requirement.

---

## 17. Common Mistakes

### Mistake 1: Treating a Checkbox as Evidence

A checkbox saying `Complete` does not prove completion.

### Mistake 2: Validating Only the Final Product

Scope validation should connect the final product to the original requirements.

### Mistake 3: Ignoring Acceptance Criteria

A broad status can hide incomplete acceptance conditions.

### Mistake 4: Treating Every Addition as Scope Creep

Additional work is not automatically a defect. The key question is whether the work was approved through the appropriate scope-change process.

### Mistake 5: Ignoring Optional Requirements

Optional and mandatory requirements should be evaluated differently.

### Mistake 6: Using Only Manual Inspection

Manual inspection can be useful but is difficult to scale and reproduce.

### Mistake 7: Failing to Preserve Evidence

A validation decision becomes difficult to audit when its supporting evidence disappears.

### Mistake 8: Ignoring Evidence Provenance

Evidence should have a known origin.

### Mistake 9: Confusing Testing With Complete Scope Validation

Tests may verify functionality but may not prove that all requirements, constraints, documentation, compliance conditions, or operational obligations have been satisfied.

### Mistake 10: Ignoring Non-Functional Requirements

Performance, security, availability, accessibility, reliability, and other quality requirements may be part of scope even when they are not visible as user-facing features.

---

## 18. Python, JavaScript, and C++ Comparison

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| Primary demonstration | Validation logic and data modeling | Application and asynchronous validation | Industry-style validation system |
| Main structures | Dataclasses, dictionaries, lists | Objects, Map, Set, Promise | Structs, classes, vectors, maps |
| Rule architecture | Callable functions | Functions passed to engine | Class-based architecture |
| Evidence lookup | Dictionary | Map | unordered_map |
| Browser relevance | Limited | Strong | Limited |
| Systems-level control | Moderate | Application-focused | Strong |
| Performance control | Moderate | Runtime-dependent | High |
| Error handling | Exceptions | try/catch and rejected Promises | Exceptions |
| Typical deployment | Automation and services | Web applications and Node.js | Systems and performance-sensitive services |

The languages therefore demonstrate different implementation concerns rather than simply translating identical examples.

---

## 19. Python-Specific Design Considerations

Python is well suited to validation automation because its data structures are concise and its standard library supports rapid development.

The Python example uses:

- `dataclass`
- `Enum`
- `list`
- `dict`
- `set`
- Type annotations
- Callable validation rules
- JSON serialization

The dictionary-based evidence index demonstrates how Python can transform a collection into an efficient lookup structure.

The Python implementation is also suitable as a foundation for:

- CI validation scripts.
- Project audits.
- CSV or JSON validation.
- Automated acceptance checks.
- Requirement reporting.

---

## 20. JavaScript-Specific Design Considerations

JavaScript is particularly useful when scope validation interacts with web interfaces.

Relevant mechanisms include:

- `Map`
- `Set`
- Promises
- `async` and `await`
- DOM querying
- Node.js process exit codes

The asynchronous model is important when validation depends on remote systems.

A browser dashboard can also show validation status in real time by consuming structured validation results.

The example avoids external packages so that the core concepts remain visible.

---

## 21. C++-Specific Design Considerations

C++ is useful when validation systems require:

- Predictable performance.
- Strong compile-time structure.
- Efficient memory usage.
- Large-scale data processing.
- Systems integration.

The case study uses:

- `struct`
- `class`
- `vector`
- `set`
- `unordered_map`
- Enumerations
- Exceptions
- Standard algorithms
- Chrono timing

The C++ implementation demonstrates how a validation engine can be designed as a modular system rather than a collection of unrelated checks.

---

## 22. Performance Considerations

The simplest evidence lookup approach repeatedly scans the entire evidence collection.

For `R` requirements and `E` evidence records, this can approach:

`O(R × E)`

Indexing evidence by requirement ID changes the retrieval pattern.

Construction requires approximately:

`O(E)`

average hash-based lookup is approximately:

`O(1)`

for each known requirement.

The total validation process can therefore approach:

`O(E + R)`

for the indexing and basic lookup portions, ignoring the complexity of additional validation rules.

Memory consumption increases because the index stores references or references-equivalent structures.

This represents a standard performance trade-off:

`More memory -> faster repeated lookup`

versus:

`Less auxiliary memory -> more repeated searching`

---

## 23. Security Considerations

Scope validation can become a security-sensitive system when its output controls deployment or release.

Important controls include:

### Evidence Integrity

Evidence should not be freely editable after validation.

### Authentication

Only authorized users should be able to approve or modify requirements.

### Authorization

Different users may require different permissions for:

- Editing requirements.
- Approving scope changes.
- Uploading evidence.
- Accepting findings.
- Overriding validation failures.

### Audit Logging

Important actions should be recorded.

Examples include:

- Requirement creation.
- Requirement modification.
- Scope approval.
- Evidence submission.
- Evidence invalidation.
- Finding resolution.
- Release approval.

### Evidence Provenance

The system should record where evidence came from.

### Tamper Resistance

For high-assurance environments, evidence may require immutable storage, hashes, signatures, or controlled archival.

---

## 24. Data Integrity Considerations

A production implementation should validate:

- Unique requirement IDs.
- Unique evidence IDs.
- Valid requirement references.
- Valid status values.
- Valid requirement types.
- Valid evidence sources.
- Consistent dependency relationships.
- Duplicate or conflicting scope definitions.

Referential integrity is especially important.

For example, evidence referring to `REQ-999` is problematic if `REQ-999` does not exist in the approved requirements.

---

## 25. Reproducibility

A good validation process should be reproducible.

Given the same:

- Requirement set.
- Evidence set.
- Validation rules.
- Scope baseline.
- Configuration.

the system should produce the same validation result.

Reproducibility is valuable for:

- Audits.
- Regulatory review.
- Release investigations.
- Defect analysis.
- Change management.

Non-deterministic validation should be isolated and documented.

---

## 26. Change Management

Scope validation must account for changes.

A requirement may be:

1. Created.
2. Reviewed.
3. Approved.
4. Implemented.
5. Validated.
6. Changed.
7. Revalidated.

Changing a requirement after validation can invalidate earlier evidence.

For example, if a requirement changes from:

`API response below 500 ms`

to:

`API response below 200 ms`

old performance evidence may no longer demonstrate compliance.

Therefore, requirement versions and evidence versions can become necessary in mature systems.

---

## 27. Baselines

A scope baseline is a controlled representation of the approved scope at a particular point in time.

Validation should identify which baseline was used.

A mature validation record may therefore contain:

- Scope baseline ID.
- Requirement version.
- Software version.
- Build ID.
- Evidence version.
- Validation-rule version.
- Validation timestamp.

This prevents ambiguity about what was actually validated.

---

## 28. Requirements Traceability

Traceability can extend beyond requirement-to-evidence relationships.

A mature model can contain:

`Business Objective -> Requirement -> Design Element -> Implementation -> Test -> Evidence -> Release`

This provides end-to-end traceability.

It helps answer questions such as:

- Why does this feature exist?
- Which requirement does this feature satisfy?
- Which test validates it?
- Which evidence proves the test passed?
- Which release contains the implementation?

The examples in this topic implement the central requirement-to-evidence layer while leaving room for a larger traceability architecture.

---

## 29. Validation Versus Verification

The concepts are related but should not be treated as identical.

Verification generally asks whether an artifact satisfies specified requirements or technical conditions.

Validation generally asks whether the delivered result satisfies the intended need or defined acceptance boundary.

In practical software processes, the terms can overlap depending on organizational terminology.

The important engineering principle is to define the exact meaning of each term within the project's governance model rather than assuming everyone uses the terminology identically.

---

## 30. Validation Versus Testing

Testing is one source of validation evidence.

Scope validation is broader.

A requirement may require:

- A functional test.
- A performance test.
- A security review.
- Documentation.
- Operational configuration.
- Regulatory evidence.

A test suite alone may therefore be insufficient to validate the complete scope.

---

## 31. Practical Applications

Scope validation can be applied to:

### Software Development

Check whether all committed features and quality requirements are satisfied.

### Product Development

Validate product features against approved specifications.

### Data Projects

Check whether required datasets, transformations, quality rules, and outputs exist.

### Cybersecurity Projects

Verify that required controls and evidence are present.

### Compliance Projects

Check that mandatory controls have supporting records.

### Research Projects

Validate that defined research deliverables, analyses, datasets, and documentation have been completed.

### Business Operations

Check whether a contracted service has delivered the agreed outputs.

### Automation Systems

Automatically reject incomplete or unsupported deliverables before downstream processing.

---

## 32. Production Architecture

A larger production system can separate the solution into components such as:

`Scope Repository`

Stores approved scope and requirements.

`Evidence Repository`

Stores validation evidence.

`Validation Engine`

Runs deterministic rules.

`Traceability Service`

Connects requirements to evidence and other artifacts.

`Change Management Service`

Records approved scope changes.

`Audit Service`

Preserves historical decisions.

`Dashboard`

Displays current validation status.

`Release Gate`

Uses validated results to enforce organizational release criteria.

A production architecture should keep these responsibilities separated so that modifying the dashboard does not silently modify the underlying validation rules.

---

## 33. Important Design Trade-Offs

### Strictness Versus Flexibility

A strict validator catches more gaps but can reject legitimate cases if the requirements are poorly defined.

A flexible validator accommodates exceptions but can weaken control.

### Manual Versus Automated Validation

Manual validation can handle nuanced judgment.

Automated validation is repeatable and scalable.

A strong system can combine both.

### Evidence Quantity Versus Evidence Quality

More evidence does not automatically mean better validation.

One authoritative, relevant evidence record can be more useful than many weak records.

### Performance Versus Memory

Indexes improve lookup performance but consume additional memory.

### Centralized Versus Distributed Validation

A centralized engine provides consistency.

Distributed validation can reduce dependencies and support independent systems.

---

## 34. Best Practices

1. Define scope before measuring completion.
2. Give requirements stable unique identifiers.
3. Separate mandatory and optional requirements.
4. Write observable acceptance criteria.
5. Require evidence for claims that must be auditable.
6. Preserve evidence provenance.
7. Maintain requirement-to-evidence traceability.
8. Identify completed work outside the approved scope.
9. Version important requirements and baselines.
10. Make validation rules explicit.
11. Separate validation failure from system failure.
12. Record findings with severity and affected requirement.
13. Use indexed data structures for large validation datasets.
14. Keep release gates deterministic where possible.
15. Protect validation evidence from unauthorized modification.
16. Maintain audit history for important decisions.
17. Revalidate affected requirements after scope changes.
18. Include non-functional and compliance requirements where applicable.
19. Avoid treating a project status field as proof.
20. Make validation results reproducible.

---

## 35. Important Distinctions

The following distinctions are central to reliable scope validation:

| Concept | Meaning |
|---|---|
| Scope | Boundary of approved work |
| Requirement | Specific condition that must be satisfied |
| Acceptance criterion | Observable condition used to determine satisfaction |
| Completion | Claimed state of work |
| Evidence | Information supporting a validation claim |
| Traceability | Relationship between requirements and supporting artifacts |
| Scope creep | Uncontrolled expansion of approved work |
| Scope change | Deliberate and controlled modification of scope |
| Finding | Detected validation condition requiring attention |
| Coverage | Measurement of validated requirements |
| Release gate | Rule determining whether a release condition is satisfied |

---

## 36. Implementation Checklist

A practical scope validation implementation should be able to answer:

- Is the approved scope explicitly defined?
- Does every requirement have a unique identifier?
- Is every requirement classified?
- Are mandatory requirements distinguished from optional ones?
- Are acceptance criteria defined?
- Is completion status tracked?
- Is supporting evidence stored?
- Is evidence linked to requirements?
- Are invalid evidence records rejected?
- Are incomplete mandatory requirements detected?
- Are blocked requirements detected?
- Are out-of-scope completed items identified?
- Are scope changes separately tracked?
- Is validation coverage measurable?
- Are findings classified by severity?
- Are validation decisions reproducible?
- Is validation history auditable?
- Are sensitive validation records protected?
- Can the system scale to large requirement and evidence collections?
- Are release gates based on explicit rules?

A system that can answer these questions has a much stronger foundation for reliable scope validation than one that relies only on a completion percentage or project status field.
