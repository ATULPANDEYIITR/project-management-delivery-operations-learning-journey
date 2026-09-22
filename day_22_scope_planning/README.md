# Scope Planning

## Topic introduction

Scope planning is the structured process of determining what a project is required to accomplish, what work is included, what work is excluded, what deliverables must be produced, and how completion will be judged.

A well-defined scope creates a common reference for project stakeholders. It reduces ambiguity between the business objective and the work performed by the project team.

Two related concepts must be distinguished.

- **Product scope** describes the features, functions, characteristics, and capabilities of the product, service, or result.
- **Project scope** describes the work required to produce that product, service, or result.

A practical scope-planning chain is:

`Business need → objective → requirements → deliverables → work packages → acceptance criteria → baseline → controlled changes`

Scope planning does not mean preventing every future change. Projects frequently evolve. The important distinction is between an authorized change to the approved scope and an uncontrolled addition that consumes resources without appropriate evaluation or authorization.

---

## Fundamental concepts

### Business need

The business need explains why the project exists.

Examples include:

- reducing manual processing
- creating a new customer service
- replacing an obsolete system
- improving information visibility
- meeting a contractual obligation
- supporting a new business capability

The business need should be translated into an objective that can guide project decisions.

### Project objective

An objective describes the result the project is expected to achieve.

A weak objective might be:

`Build a good project dashboard.`

The word "good" does not establish a measurable boundary.

A more useful objective is:

`Deliver a browser-based dashboard that allows authenticated users to view project status and search projects by name before the agreed MVP acceptance date.`

The second statement identifies the result, users, important capabilities, and a delivery context.

### Requirements

A requirement states a need, condition, capability, or constraint that must be satisfied.

The implementations use requirement records containing:

- identifier
- description
- priority
- source
- acceptance criteria

For example, `REQ-001` states that users must be able to create an account using an email address.

Requirements should be sufficiently clear that the project team and stakeholders can determine whether the requirement has been satisfied.

### Deliverables

A deliverable is a verifiable output produced by the project.

Examples include:

- software components
- reports
- configured systems
- training materials
- approved documents
- tested releases
- infrastructure components

A deliverable should have a clear relationship with the requirements it satisfies.

### Work packages

A work package is a manageable component of the work breakdown structure.

The examples use work packages such as:

- Authentication
- Dashboard
- Acceptance testing

Each work package has an identifier, description, estimated effort, and linked deliverables.

---

## Scope boundaries

A useful scope statement distinguishes four categories.

### Inclusions

Inclusions specify what belongs to the project.

The case study includes:

- account creation and authentication
- project dashboard
- project search
- English interface
- basic project status tracking

### Exclusions

Exclusions specify what does not belong to the current scope.

The case study explicitly excludes:

- native mobile applications
- advanced financial accounting
- third-party payroll processing
- multilingual translation in the first release

Exclusions are important because stakeholders can otherwise assume that a related capability is automatically included.

### Assumptions

An assumption is a condition believed to be true for planning purposes.

Examples from the implementations include:

- branding assets will be supplied
- users will have internet access
- the hosting environment will be available before acceptance testing

An assumption is not the same as a fact. If it becomes false, the project may need a risk response, replanning, or a formal change analysis.

### Constraints

A constraint restricts available project choices.

Examples include:

- a fixed release date
- a limited budget
- an approved technology stack

Constraints influence trade-offs between scope, time, cost, resources, quality, and technical alternatives.

---

## Core scope-planning principles

### Clear boundaries

A scope statement should make it possible to determine whether a proposed piece of work belongs to the project.

### Traceability

Requirements should be traceable to deliverables, and deliverables should be traceable to work packages and acceptance conditions.

Traceability makes it possible to answer questions such as:

- Why is this deliverable required?
- Which requirement does this work satisfy?
- Which requirements are not covered?
- Which work is affected by a proposed change?

### Measurability

Requirements and acceptance criteria should be observable and testable.

`The system should be fast` is ambiguous.

A measurable performance requirement could specify:

`The dashboard shall return a result within an agreed response-time threshold under a defined workload and test environment.`

### Controlled change

A baseline should be treated as an approved reference point. It does not mean the scope can never change.

A legitimate change should be:

1. recorded
2. clarified
3. analyzed
4. evaluated against relevant constraints
5. approved or rejected
6. incorporated into the baseline when approved
7. communicated
8. verified after implementation

---

## Requirements and prioritization

The examples use four priority categories:

- `Must`
- `Should`
- `Could`
- `Won't`

Priority identifies relative importance. It does not automatically determine technical complexity, implementation cost, or risk.

A high-priority requirement can still be impossible to deliver under a particular constraint.

A lower-priority requirement can be deferred without necessarily being removed permanently from the product strategy.

The Python, JavaScript, and C++ implementations represent priority as structured data so that requirements can be sorted, counted, validated, and analyzed programmatically.

---

## Acceptance criteria

Acceptance criteria define observable conditions used to decide whether a requirement or deliverable is acceptable.

For the authentication requirement, examples include:

- valid registration succeeds
- duplicate email registration is rejected
- valid credentials create a session
- invalid credentials are rejected

Acceptance criteria should ideally be agreed before acceptance testing begins.

Strong acceptance criteria are:

- specific
- observable
- testable
- relevant
- unambiguous
- connected to the requirement

Acceptance criteria should not silently introduce new requirements. If a criterion requires a capability not contained in the approved scope, that discrepancy should be analyzed rather than hidden inside testing.

---

## Work Breakdown Structure

The Work Breakdown Structure, or WBS, decomposes the project scope into manageable components.

The case study uses the following simplified structure:

`1.1 Authentication`

`1.2 Dashboard`

`1.3 Acceptance testing`

Each work package has an estimated effort and links to deliverables.

A useful WBS should cover the project work without intentionally omitting necessary work. The 100 percent rule is a useful conceptual test: the WBS should represent all work required by the approved project scope, including appropriate project-management work.

The WBS should not become an arbitrary list of extremely small tasks. Decomposition should stop at a level where the work can be estimated, assigned, monitored, and controlled effectively.

---

## Requirement traceability

Traceability connects requirements with the outputs intended to satisfy them.

The case study creates relationships such as:

`REQ-001 → Authentication module`

`REQ-002 → Authentication module`

`REQ-003 → Project dashboard`

`REQ-004 → English release`

The implementations calculate traceability coverage.

A simplified coverage formula is:

`covered requirements / total requirements × 100`

A result of 100% means every requirement is represented by at least one linked deliverable in the model. It does not prove that the implementation is correct or that the requirement itself is complete.

Traceability is therefore a necessary control, not proof of project success.

---

## Scope baseline

A scope baseline is an approved reference version of the project scope.

The Python implementation represents a baseline with:

- version
- scope statement
- requirements
- deliverables

The C++ implementation extends the model to include work packages.

A baseline makes changes visible. Without a baseline, it is difficult to distinguish an actual scope change from normal execution of previously agreed work.

A baseline can be revised through authorized change control.

---

## Scope change control

A change request represents a proposed modification to the approved scope.

The case study uses:

- change identifier
- description
- reason
- estimated effort
- cost impact
- schedule impact
- status

Possible statuses include:

- Proposed
- Analyzing
- Approved
- Rejected
- Implemented

A change should be evaluated across relevant dimensions rather than judged solely on whether the requested feature appears useful.

Important impact categories include:

- scope
- requirements
- deliverables
- effort
- cost
- schedule
- quality
- resources
- architecture
- security
- dependencies
- contractual obligations
- operational support

The JavaScript implementation demonstrates an event-driven change-control mechanism. A submitted change can generate an event, and approval or rejection can generate additional events.

---

## Scope creep

Scope creep is uncontrolled expansion of project scope.

For example, suppose the baseline includes a browser application but someone begins implementing a native mobile application without an approved change. The mobile application consumes effort while remaining outside the controlled baseline.

This differs from a formally approved scope change.

The distinction is:

`Authorized change → controlled scope evolution`

`Unauthorized addition → scope-control problem`

A project may legitimately grow. The governance problem arises when the growth is not properly evaluated, authorized, resourced, or incorporated into the project baseline.

---

## Python implementation

The Python script provides the most extensive educational representation of scope planning.

### Data classes

The implementation uses:

- `Requirement`
- `Deliverable`
- `ScopeStatement`
- `WorkPackage`
- `ChangeRequest`
- `ScopeBaseline`
- `ScopeModel`

Python data classes make these project artifacts explicit and easy to validate.

### Requirement validation

`Requirement.is_complete()` checks whether the core requirement fields and acceptance criteria are present.

This demonstrates an important distinction between having a requirement record and having a sufficiently structured requirement record.

### Scope statement

`ScopeStatement` contains:

- objective
- inclusions
- exclusions
- assumptions
- constraints

This gives the project boundary a clear data representation.

### Work package validation

`WorkPackage.validate()` checks for:

- an identifier
- a name
- positive estimated effort
- linked deliverables

This demonstrates how scope artifacts can be checked automatically rather than relying entirely on manual review.

### Traceability

The Python implementation calculates requirement coverage and identifies unmapped requirements.

It also validates whether deliverables reference existing requirement identifiers.

### Baseline

`ScopeBaseline` captures an approved version of the scope-related artifacts.

The baseline can therefore be compared with later project information.

### Change requests

`ChangeRequest` records effort, cost, and schedule effects.

The example also computes a simple impact score. This is an educational metric, not a universal project-management formula. Real organizations should define their own decision model according to their governance practices.

### Edge cases

The Python script tests:

- duplicate requirement identifiers
- empty requirements
- invalid work packages
- missing acceptance conditions
- unmapped requirements

These examples demonstrate that scope planning can be treated as a validation problem as well as a documentation activity.

---

## JavaScript implementation

The JavaScript implementation focuses on object-oriented and event-driven modeling.

### Classes

The main classes are:

- `Requirement`
- `ScopeStatement`
- `Deliverable`
- `WorkPackage`
- `ScopeBaseline`
- `ChangeRequest`
- `ChangeControl`
- `ScopeModel`

JavaScript classes provide a natural way to model project artifacts as objects with both data and behavior.

### Sets

The implementation uses `Set` for:

- requirement identifiers
- mapped requirements
- duplicate detection
- baseline comparison

Set membership has average constant-time behavior in typical implementations, making it appropriate for identifier-based membership checks.

### Arrays

Arrays are used for collections such as:

- requirements
- deliverables
- work packages
- acceptance criteria

Array methods such as `filter`, `map`, `reduce`, and `flatMap` make common scope-analysis operations concise.

### Event-driven change control

`ChangeControl` implements a small event system.

Listeners can subscribe to events such as:

- `changeSubmitted`
- `changeApproved`
- `changeRejected`

This is relevant to application development because a real scope-management application may need to trigger:

- notifications
- audit logging
- approval workflows
- dashboard updates
- persistence operations

The example demonstrates the architectural idea without requiring an external framework.

### JavaScript-specific relevance

JavaScript is particularly useful when scope-management concepts are being integrated into:

- web applications
- browser interfaces
- dashboards
- interactive forms
- event-driven workflows
- API clients

The implementation therefore emphasizes object behavior, collections, validation, and event-driven application logic.

---

## C++ case study

The C++ implementation models an enterprise-style project scope management system.

### Problem being solved

The modeled organization is developing a browser-based project management MVP for small teams.

The system must maintain a controlled relationship between:

`Requirements → Deliverables → Work Packages → Acceptance`

It must also support:

`Scope Baseline → Change Request → Impact Analysis → Approval`

### Main components

The C++ program contains:

- `Requirement`
- `Deliverable`
- `WorkPackage`
- `ScopeStatement`
- `ChangeRequest`
- `ScopeBaseline`
- `ScopeManagementSystem`

### `ScopeManagementSystem`

This class acts as the central scope repository.

It manages:

- requirements
- deliverables
- work packages
- change requests
- the current baseline

It also performs:

- validation
- traceability checking
- coverage calculation
- effort calculation
- baseline creation
- change submission
- change analysis
- change approval
- change rejection

### Data structures

`unordered_map` stores artifacts by identifier.

This is useful because project-management operations frequently require retrieving a requirement or deliverable by a known identifier.

Average lookup is approximately O(1), although exact performance depends on the implementation and hashing behavior.

`vector` stores ordered collections such as acceptance criteria and change requests.

`set` is used for membership and unique-item analysis.

`optional` represents the possibility that a baseline or change request does not exist.

### Validation

The system validates:

- empty identifiers
- empty descriptions
- missing acceptance criteria
- invalid work-package effort
- missing deliverable references
- missing requirement references
- negative change impacts

The C++ program uses exceptions for invalid change-request data.

This illustrates an important implementation principle: invalid state should be rejected at the boundary rather than silently accepted and discovered later.

### Baseline creation

`createBaseline()` captures the current scope-related artifacts into a versioned baseline.

This represents the point at which the project has an approved reference for scope control.

### Acceptance evaluation

The C++ program compares completed conditions against required conditions.

If any required condition is missing, the result is not accepted.

This demonstrates the difference between "work has been performed" and "the agreed acceptance conditions have been satisfied."

### Change impact analysis

The example change requests:

`Add multilingual interface support.`

The modeled impact includes:

- 80 hours of estimated effort
- 12,000 cost impact
- 10 schedule days

The program calculates a composite educational impact score.

The score is deliberately simple. In an actual organization, scope decisions may use a formal change-control board, financial analysis, schedule models, risk assessment, contractual analysis, or weighted decision criteria.

---

## Scope planning workflow

A practical scope-planning workflow can be represented as follows.

### Identify the business need

Understand the problem or opportunity that motivates the project.

### Define the objective

State the result in a form that can guide decisions.

### Identify stakeholders

Determine who provides requirements, who approves scope, who performs the work, who accepts the deliverables, and who is affected by the result.

### Gather requirements

Capture functional requirements, non-functional requirements, constraints, assumptions, and relevant business rules.

### Analyze and prioritize requirements

Identify relative importance, dependencies, ambiguity, feasibility, and conflicts.

### Define deliverables

Translate requirements into observable outputs.

### Define exclusions

Document important work that is explicitly outside the current project boundary.

### Build the WBS

Decompose the approved scope into manageable work packages.

### Define acceptance criteria

Specify how deliverables will be evaluated.

### Establish the baseline

Approve and record the scope reference.

### Control changes

Evaluate proposed changes before modifying the approved scope.

---

## Important distinctions

### Scope versus schedule

Scope describes what must be delivered and the work required.

Schedule describes when that work is expected to occur.

A schedule change does not automatically mean scope changed.

### Scope versus cost

Scope describes the work and outputs.

Cost describes the resources required to perform that work.

An increase in scope can create cost effects, but scope and cost remain distinct dimensions.

### Requirement versus deliverable

A requirement describes a needed condition or capability.

A deliverable is an output produced to satisfy one or more requirements.

### Deliverable versus work package

A deliverable is an output.

A work package is a manageable unit of work used to produce outputs.

### Assumption versus constraint

An assumption is something treated as true for planning.

A constraint is a restriction on available choices.

### Scope change versus scope creep

A scope change is a modification to scope.

Scope creep refers to uncontrolled or unauthorized expansion.

A properly approved change is not automatically scope creep.

---

## Edge cases

### Duplicate identifiers

Two requirements should not silently share the same identifier.

Identifiers support:

- traceability
- reporting
- change history
- testing
- auditability

The implementations explicitly test duplicate IDs.

### Requirement without acceptance criteria

A requirement can exist syntactically while remaining difficult to verify.

The examples therefore treat acceptance criteria as an important completeness condition.

### Deliverable referencing an unknown requirement

This is a traceability defect.

The C++ and Python implementations detect references to unknown requirement identifiers.

### Work package with zero effort

An executable work package should normally have a meaningful estimate.

A zero or negative estimate can indicate incomplete planning or invalid data.

### Requirement removed after baseline

Removing a requirement after baseline creation should be treated as a controlled change rather than silently deleting it.

Historical records should normally preserve the previous state.

### Contradictory requirements

Two stakeholders may request mutually incompatible outcomes.

The conflict should be identified and resolved through requirements analysis and governance rather than hidden inside implementation work.

---

## Common mistakes

### Defining scope using vague language

Words such as "good", "modern", "fast", "simple", and "complete" require measurable definitions when they influence acceptance.

### Describing only features

A feature list may not describe all project work.

Project scope can include:

- analysis
- design
- development
- integration
- testing
- migration
- documentation
- deployment
- training
- project-management work

### Ignoring exclusions

If boundaries are not documented, stakeholders may form different assumptions about what is included.

### Failing to connect requirements and deliverables

Without traceability, it becomes difficult to demonstrate why a deliverable exists or whether every approved requirement is covered.

### Treating the baseline as permanent

A baseline is controlled, not necessarily immutable.

Authorized changes can modify it.

### Accepting undocumented work

Unrecorded additions make project performance difficult to measure because the original boundary becomes unclear.

### Treating metrics as objectives

A high traceability percentage, for example, does not prove that the requirements are correct. Metrics are indicators, not substitutes for judgment and governance.

---

## Limitations of the implementations

These programs are educational models rather than complete enterprise scope-management platforms.

They do not provide:

- persistent database storage
- multi-user concurrency
- authentication
- authorization
- distributed deployment
- database transactions
- formal approval signatures
- document management
- full audit trails
- enterprise portfolio integration
- contractual workflow management

The examples intentionally keep the data model understandable while demonstrating the underlying mechanisms.

A production implementation would require stronger controls around data persistence, identity, authorization, auditability, concurrency, validation, and integration.

---

## Performance considerations

For typical collections:

- dictionary or hash-map identifier lookup is approximately O(1) on average
- set membership is approximately O(1) on average
- linear scans are O(n)
- sorting is generally O(n log n)
- traceability scans are approximately O(R + D), depending on how requirement references are represented

Here `R` represents the number of requirements and `D` represents the number of relevant deliverable references.

For a small project, simple in-memory collections are generally sufficient for demonstrations and prototypes.

For a large organization, scope data may need:

- indexed database fields
- pagination
- incremental validation
- versioned storage
- caching
- efficient graph queries
- asynchronous processing
- immutable audit records

Performance should be considered in relation to actual data volume and usage patterns rather than optimized prematurely.

---

## Security considerations

Scope-management systems can contain sensitive information.

Examples include:

- contractual commitments
- financial estimates
- customer requirements
- technical architecture
- internal project plans
- security requirements
- supplier information

A production system should therefore implement appropriate controls such as:

- authentication
- role-based authorization
- least-privilege access
- input validation
- audit logging
- secure storage
- controlled baseline modification
- protection against unauthorized deletion
- historical version preservation

An especially important control is authorization around baseline and change approval. A user who can view scope should not automatically be permitted to approve or modify it.

---

## Implementation considerations

A production scope-management system should distinguish between current state and historical state.

For example, if a requirement changes from:

`Users shall authenticate using email credentials.`

to:

`Users shall authenticate using email credentials and a second authentication factor.`

the system should preserve the earlier version rather than simply overwriting it.

Useful records can include:

- version number
- author
- timestamp
- previous value
- new value
- reason
- approval reference
- affected deliverables
- affected work packages

This creates an auditable history.

---

## Scope metrics

Useful scope-related metrics can include:

- requirement traceability coverage
- requirements without acceptance criteria
- number of approved changes
- number of rejected changes
- requirement volatility
- deliverable acceptance rate
- number of unapproved scope additions
- change-request processing time
- percentage of work packages linked to deliverables
- number of unresolved requirement conflicts

A simple requirement-volatility calculation can be expressed as:

`(requirements added + requirements removed) / initial requirements × 100`

The meaning of a metric depends on context. High volatility may indicate unclear discovery, changing business conditions, evolving product strategy, external changes, or an intentionally iterative development process.

The metric alone does not identify the cause.

---

## Real-world applications

Scope planning is relevant to many project environments.

### Software development

Scope can cover:

- application features
- APIs
- database changes
- integrations
- testing
- migration
- deployment
- documentation

### Infrastructure projects

Scope can include:

- equipment
- installation
- configuration
- testing
- commissioning
- documentation

### Data projects

Scope can include:

- source systems
- data ingestion
- transformations
- quality rules
- models
- dashboards
- governance

### Consulting projects

Scope can define:

- analysis activities
- deliverables
- workshops
- reports
- review cycles
- exclusions

### Research projects

Scope can establish:

- research questions
- datasets
- experimental boundaries
- methods
- outputs
- acceptance conditions

---

## Python, JavaScript, and C++ comparison

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| Main emphasis | Educational modeling and validation | Application and event-driven behavior | Structured system case study |
| Data modeling | Data classes | Classes and objects | Structs and classes |
| Collections | Lists, sets, dictionaries | Arrays, Set, Map | vector, set, unordered_map |
| Validation | Explicit methods and functions | Methods and collection operations | Class methods and exceptions |
| Change control | Data modeling | Event-driven workflow | Stateful management system |
| Typical strength | Rapid modeling and analysis | Web applications and event workflows | Performance and explicit system design |
| Runtime style | Interpreted | Runtime-based | Compiled |
| External dependencies | None | None | Standard library only |

The same project-management concepts can therefore be represented differently depending on the language and application environment.

Python makes it convenient to express analytical models and validation logic.

JavaScript naturally supports interactive, event-driven application behavior.

C++ makes data ownership, system structure, explicit types, and performance characteristics more visible.

---

## Best practices

A disciplined scope-planning approach should:

- define the business objective before decomposing work
- identify stakeholders and requirement sources
- write requirements in clear language
- attach acceptance criteria to important requirements
- define deliverables explicitly
- document exclusions
- distinguish assumptions from constraints
- build traceability relationships
- decompose approved scope into manageable work packages
- establish an approved baseline
- evaluate changes before implementation
- preserve historical versions
- maintain auditability
- validate scope artifacts programmatically where appropriate
- communicate approved changes to affected stakeholders
- verify delivered results against acceptance criteria

The most important structural relationship is:

`Requirement → Deliverable → Work Package → Acceptance`

Change control then operates around the approved baseline:

`Baseline → Proposed Change → Impact Analysis → Decision → Revised Baseline`

This structure gives the project a controlled relationship between what was requested, what must be produced, what work is performed, and how completion is verified.
