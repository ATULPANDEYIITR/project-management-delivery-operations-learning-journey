# Requirements Collection

## Topic introduction

Requirements collection is the systematic process of discovering, clarifying, documenting, validating, prioritizing, and controlling the needs and constraints of a project or product.

A project can fail even when its software is technically functional if the team builds the wrong functionality, misunderstands stakeholder expectations, ignores operational constraints, or fails to define how success will be measured.

Requirements collection therefore sits between the business problem and the solution implementation. It translates business needs into sufficiently clear statements that designers, developers, testers, managers, security teams, and other stakeholders can understand and verify.

The three implementations in this repository approach the subject from different perspectives:

- The Python implementation is a broad educational laboratory covering requirements terminology, elicitation, validation, prioritization, traceability, versioning, scope, and change management.
- The JavaScript implementation demonstrates how a requirements repository and collection workflow can be represented using modern objects, collections, validation functions, asynchronous operations, and application-style services.
- The C++ implementation develops an industry-style digital application management case study with strongly structured types, a requirements repository, validation, traceability, version history, scope management, change requests, and complexity considerations.

Requirements collection is not equivalent to simply asking stakeholders what they want. Stakeholders may describe symptoms rather than root problems, use ambiguous language, contradict each other, omit exceptional situations, or request solutions before the underlying need is understood.

A disciplined requirements process therefore separates discovery from interpretation, interpretation from documentation, and documentation from validation.

## Fundamental concepts

### Requirement

A requirement is a documented need, capability, condition, or constraint that a solution is expected to satisfy.

Examples include:

- The system shall allow an authenticated customer to submit an application.
- The system shall prevent unauthorized access to protected records.
- The system shall retain an audit record for security-relevant events.
- The service shall meet a defined availability target.
- The solution shall comply with a specified organizational policy.

A requirement should communicate enough information to allow relevant stakeholders to determine whether the expected condition has been satisfied.

### Stakeholder

A stakeholder is an individual, group, or organization that can affect the project, is affected by it, uses its outputs, funds it, operates it, governs it, or imposes constraints upon it.

Typical stakeholders include:

- customers
- end users
- business owners
- managers
- product managers
- developers
- testers
- operations teams
- security teams
- legal teams
- compliance teams
- regulators
- external partners
- suppliers

Stakeholder identification is important because requirements collected from one group rarely represent the complete needs of the system.

### Business requirement

A business requirement describes the organizational objective or business outcome.

Example:

`The organization requires a controlled digital process through which customers and authorized employees can obtain accurate application status.`

This does not prescribe every system feature. It establishes why the project exists.

### User requirement

A user requirement expresses what a particular class of user needs to accomplish.

Example:

`A customer needs to determine the current status of an application.`

User requirements are generally closer to user goals than technical implementation details.

### Functional requirement

A functional requirement describes behavior that the system must perform.

Examples include:

- creating a record
- submitting an application
- validating information
- calculating a value
- searching for a record
- sending a notification
- generating a report
- enforcing a workflow

A common structure is:

`The system shall <perform an observable action>.`

### Non-functional requirement

A non-functional requirement describes a quality attribute, performance characteristic, constraint, or operational property.

Examples include:

- response time
- availability
- scalability
- reliability
- maintainability
- accessibility
- security
- auditability
- recoverability

A non-functional requirement should be expressed in measurable or verifiable terms whenever practical.

Weak:

`The system shall be fast.`

Stronger:

`The system shall return application search results within 2 seconds for at least 95% of requests under the approved production workload.`

The second form establishes a measurable condition.

### Constraint

A constraint limits the available solution space.

Examples include:

- a regulatory obligation
- an approved technology
- an existing enterprise integration
- a fixed deployment environment
- a mandatory security policy
- a budget or schedule boundary
- a data residency requirement

Constraints are requirements even when they do not describe a user-facing feature.

### Assumption

An assumption is treated as true for planning purposes but has not necessarily been fully verified.

Examples:

- An existing identity provider will remain available.
- A particular external service will provide the required interface.
- A specified department will supply data by an agreed date.

Unrecorded assumptions create hidden project risk.

### Dependency

A dependency is something required for another requirement or activity to function.

For example, application status tracking may depend on application submission and the existence of an authoritative application-status data source.

Dependencies should be visible because a change in one requirement can affect other requirements.

### Acceptance criterion

An acceptance criterion defines a condition that can be checked to determine whether a requirement has been satisfied.

Example:

`Given a valid application identifier, the current application status is displayed.`

Acceptance criteria transform abstract expectations into observable conditions.

## Requirements collection versus requirements specification

Requirements collection focuses on discovering what is needed.

Requirements specification focuses on documenting the discovered needs with enough precision for implementation and verification.

The activities overlap in iterative development, but the distinction remains useful:

1. Discover stakeholder needs.
2. Understand the current problem.
3. Analyze the information.
4. Convert observations into candidate requirements.
5. Validate the requirements.
6. Document the approved requirements.
7. Maintain them as the project changes.

## Requirements elicitation

Elicitation is the process of obtaining information about needs, goals, constraints, processes, and expectations.

The Python and JavaScript implementations demonstrate several elicitation techniques.

### Interviews

An interview allows a requirements analyst or product professional to explore an individual's knowledge in depth.

Useful questions include:

- What problem are you trying to solve?
- Who experiences the problem?
- What happens today?
- Which part of the current process causes the most difficulty?
- What information is required?
- What happens when something goes wrong?
- How should success be measured?
- What constraints apply?

Effective interviews use open questions before moving toward detailed clarification.

Poor questioning can introduce the interviewer's assumptions into the requirements.

### Questionnaires

Questionnaires are useful when information is required from many people.

Advantages include:

- broad reach
- standardized questions
- easy aggregation
- relatively low individual interview time

Limitations include:

- limited opportunity for clarification
- ambiguous answers
- response bias
- difficulty exploring unexpected information

### Workshops

A requirements workshop brings multiple stakeholders together.

Workshops are useful for:

- resolving disagreements
- mapping processes
- identifying dependencies
- defining business rules
- reviewing prototypes
- establishing priorities

A workshop requires preparation and facilitation. Without structure, participants may spend the session debating solutions without establishing the actual problem.

### Observation

Observation examines what people actually do rather than relying exclusively on what they say they do.

It can reveal:

- manual workarounds
- repeated data entry
- undocumented process steps
- interruptions
- exceptions
- dependencies on spreadsheets or external systems

Observation has limitations. A short observation period may not reveal rare events or unusual operating conditions.

### Document analysis

Existing documents can provide requirements evidence.

Examples include:

- policies
- contracts
- standard operating procedures
- regulations
- process manuals
- existing system documentation
- data dictionaries
- service-level agreements

Documents should not automatically be treated as current truth. They may be outdated or inconsistent with actual operations.

### Prototyping

A prototype provides a concrete representation of a possible interface or workflow.

Prototypes can expose ambiguity that is difficult to identify in written descriptions.

A prototype should not automatically be treated as the final technical design. Its primary requirements value is often the feedback it generates.

## Stakeholder analysis

The Python, JavaScript, and C++ implementations model stakeholders using influence and interest.

A basic mapping can distinguish:

- high influence, high interest
- high influence, lower interest
- lower influence, high interest
- lower influence, lower interest

This is not a complete stakeholder-management method, but it demonstrates why different stakeholders require different engagement approaches.

For example:

A security officer may have high influence because security controls can block a release.

An end user may have lower formal authority but high interest because the user interacts directly with the system.

An operations manager may have both high interest and high influence because the system changes an operational process.

## From stakeholder statements to requirements

Stakeholder statements are often incomplete.

Example:

`Customers need the application to be faster.`

This identifies a concern but not a measurable requirement.

Questions that should follow include:

- Which operation?
- Faster than what?
- Under what workload?
- For which users?
- What percentage of transactions?
- What measurement method?
- What time period?
- Are there exceptions?

The Python implementation demonstrates this transformation by converting informal statements into structured requirement records.

The conversion must remain subject to human validation. Natural-language processing or automated transformation can assist analysis but should not silently invent business meaning.

## Requirement structure

A practical requirement record can contain:

- identifier
- title
- description
- requirement type
- priority
- source
- stakeholders
- acceptance criteria
- dependencies
- assumptions
- status
- version

The implementations use these fields consistently.

An identifier provides stable reference.

A title gives a concise description.

The description communicates the expected condition.

The type classifies the requirement.

The priority communicates relative importance.

The source identifies where the requirement originated.

Stakeholder references provide ownership and context.

Acceptance criteria support verification.

Dependencies and assumptions expose relationships and uncertainty.

Status communicates lifecycle state.

Version information supports change control.

## User stories

A common user-story structure is:

`As a <role>, I want to <action>, so that <benefit>.`

The JavaScript and C++ implementations use examples such as:

`As a customer, I want to search for an application, so that I can see its current status.`

The role identifies the actor.

The action describes the desired capability.

The benefit explains why the capability matters.

A user story without acceptance criteria may remain too vague to test.

## Acceptance criteria

Acceptance criteria should describe observable outcomes.

For an application status feature, useful criteria might include:

- Given a valid identifier, the current status is displayed.
- If no record exists, the system returns a controlled not-found response.
- If the user is not authorized, protected information is not returned.

Acceptance criteria should address normal behavior and important failure conditions.

## Use cases

A use case provides a more structured description of interaction.

The implementations represent:

- use-case identifier
- name
- primary actor
- preconditions
- main flow
- alternate flows
- postconditions

For an application-submission use case:

### Preconditions

The customer is authenticated and required information is available.

### Main flow

1. Customer opens the form.
2. System displays required fields.
3. Customer enters information.
4. System validates information.
5. System stores the application.
6. System returns a confirmation identifier.

### Alternate flows

Invalid data produces validation feedback.

A storage failure must not result in a false success response.

### Postcondition

A valid application is stored with an identifiable record.

Use cases are especially useful when workflows contain multiple actors, conditions, and exceptions.

## Requirement quality

Good requirements are generally:

- clear
- specific
- complete
- consistent
- feasible
- necessary
- verifiable
- traceable
- appropriately prioritized
- sufficiently atomic

These characteristics are not absolute mathematical properties. They provide review criteria.

### Ambiguity

Words such as the following can be problematic without defined measurements:

- fast
- easy
- simple
- quick
- efficient
- reasonable
- appropriate
- soon
- etc.

The implementations detect several of these words automatically.

The detection mechanism is intentionally simple. A word is not automatically invalid merely because it appears in a requirement. Context determines whether clarification is necessary.

For example, `reasonable security controls` may be ambiguous, while a formally defined organizational term may have a precise meaning in its project context.

## Completeness

A requirement may appear clear but still be incomplete.

For example:

`The system shall allow customers to submit applications.`

Questions remain:

- Which customers?
- What information is required?
- What validation occurs?
- What happens if information is invalid?
- What confirmation is returned?
- What happens if submission fails?
- Can the customer modify the application?
- How is the application identified?
- What authorization is required?

Completeness is therefore broader than sentence length.

## Consistency

Two requirements can conflict.

Example:

`Managers shall have access to operational customer data.`

and:

`The system shall prevent unauthorized access to customer data.`

These statements are not necessarily contradictory. The important missing concept is authorization.

The refined interpretation can be:

`Authorized managers shall have access to operational customer data.`

while unauthorized users remain restricted.

The implementations deliberately identify this as a potential conflict rather than automatically declaring the requirements contradictory.

Natural-language conflict detection cannot reliably replace stakeholder analysis.

## Feasibility

A requirement should be achievable within the relevant technical, operational, legal, financial, and schedule constraints.

Feasibility questions include:

- Is the required data available?
- Can the system meet the performance target?
- Can the organization operate the proposed solution?
- Are required integrations possible?
- Are security requirements compatible with usability requirements?
- Are regulatory obligations understood?
- Are required skills and infrastructure available?

A requirement can be desirable but infeasible under current constraints.

## Testability

A requirement is testable when a defined verification method can determine whether it has been satisfied.

Weak:

`The application should be user-friendly.`

Stronger:

`A customer shall be able to submit a valid application without assistance using the defined standard workflow.`

A precise usability requirement may also define a measurable task-completion rate, completion time, or usability study method.

## Requirement prioritization

Requirements often exceed available time, budget, capacity, or implementation scope.

The implementations demonstrate a simple multi-factor scoring model using:

- business value
- urgency
- risk reduction
- dependency impact

The numerical values are decision-support information rather than objective truth.

A prioritization model should document:

- scoring scale
- criteria
- weights
- responsible decision makers
- review date
- assumptions

Common priority categories include:

- Must
- Should
- Could
- Won't

The important principle is that priorities must be explicit. Without prioritization, every stakeholder may describe their requirement as critical.

## Scope management

Requirements collection can expand indefinitely if project boundaries are not established.

The implementations distinguish:

- in-scope items
- out-of-scope items
- unclassified items

An unclassified item should not automatically be accepted or rejected. It should be evaluated against the project's objectives and boundaries.

Scope boundaries help prevent unrelated requests from silently entering the project.

## Dependencies

Dependencies describe relationships between requirements.

For example:

Application status tracking may depend on application submission because a status cannot exist without an application record.

Performance requirements may depend on data-access architecture.

Audit requirements may depend on the identity and authorization mechanisms.

Dependencies are important during change analysis. Changing one requirement can affect several others.

## Assumptions

Assumptions should be recorded rather than left implicit.

Examples include:

- an external identity provider will remain available
- a data source will contain required fields
- a regulatory interpretation will remain applicable
- an internal team will provide an integration by a defined date

When an assumption becomes false, related requirements should be reassessed.

## Requirements traceability

Traceability connects different levels of project evidence.

A simple chain can be:

`Business objective -> User story -> System requirement -> Test case`

The implementations provide a traceability matrix connecting:

- business requirements to user stories
- user stories to system requirements
- requirements to tests

Traceability helps answer questions such as:

- Why does this requirement exist?
- Which business objective does it support?
- Which user need does it address?
- Which test verifies it?
- Which requirements are not currently verified?
- Which implementation changes may affect a business objective?

Traceability becomes increasingly valuable as project size and regulatory requirements increase.

## Requirements validation

Validation asks whether the documented requirements are suitable.

Important validation questions include:

### Is the requirement necessary?

Does it support a legitimate business or user need?

### Is it clear?

Would different readers interpret it differently?

### Is it complete?

Are important conditions and exceptions documented?

### Is it consistent?

Does it conflict with another requirement?

### Is it feasible?

Can the organization realistically satisfy it?

### Is it testable?

Can satisfaction be demonstrated?

### Is it traceable?

Can its origin and verification be identified?

The Python, JavaScript, and C++ implementations automate several of these checks.

Automated validation is useful for finding structural problems, but stakeholder review remains necessary for semantic correctness.

## Requirements repository

The Python and JavaScript implementations include an in-memory requirements repository.

The repository provides operations for:

- adding requirements
- retrieving requirements
- filtering by type
- filtering by priority
- updating requirements
- preserving previous versions

The C++ implementation provides equivalent behavior through a typed repository class.

An enterprise repository would normally require more capabilities, such as:

- persistent storage
- authentication
- authorization
- audit logging
- concurrent editing controls
- search
- filtering
- version history
- approval workflow
- backups
- retention controls
- reporting

## Versioning

Requirements change.

Changes can occur because:

- stakeholder needs change
- regulations change
- business processes change
- technical constraints change
- security threats change
- external integrations change
- project scope changes
- new information becomes available

The implementations preserve a previous requirement snapshot before updating the current version.

A formal change process should normally record:

- change identifier
- requirement affected
- requester
- reason
- impact
- approval state
- resulting version

## Change requests

A change request is a controlled proposal to modify an approved requirement or project condition.

A change should be evaluated for impact on:

- scope
- schedule
- budget
- architecture
- security
- data
- integrations
- testing
- operations
- other requirements

A request should not be implemented simply because someone asked for it. The project should determine its impact and appropriate approval path.

## Baselines

A baseline is a controlled version of requirements against which subsequent changes can be measured.

A baseline can answer:

`What did the project officially agree to at this point in time?`

Baselines are particularly useful when requirements change repeatedly.

The Python implementation creates a lightweight baseline containing identifiers, versions, titles, and descriptions.

A production system would normally store baselines in a controlled repository.

## The Python implementation

The Python implementation is intentionally broad.

It begins with terminology and classification and progresses through:

- stakeholder modeling
- elicitation techniques
- requirement records
- user stories
- use cases
- acceptance criteria
- ambiguity detection
- requirement validation
- prioritization
- conflict detection
- traceability
- repository management
- versioning
- change requests
- scope management
- baselines
- metrics
- an end-to-end collection workflow
- security considerations
- performance considerations
- a complete mini case study

Python is useful for requirements-analysis tooling because its data structures make it straightforward to represent requirements, stakeholder records, traceability relationships, validation results, and workflow state.

Dictionaries provide efficient identifier-based access.

Lists represent ordered collections such as acceptance criteria.

Sets represent relationships where duplicate entries should not be retained.

Dataclasses provide compact structured records while retaining readable source code.

Exceptions demonstrate how invalid operations can be handled rather than silently ignored.

The repository demonstrates why requirements management benefits from explicit data structures rather than unstructured notes alone.

## The JavaScript implementation

The JavaScript implementation models requirements as an application-oriented system.

It demonstrates:

- objects and classes
- `Map`
- `Set`
- arrays
- object spread
- optional chaining
- validation
- exception handling
- asynchronous operations
- `Promise`
- `Promise.all`
- service classes
- version history

JavaScript is particularly useful when requirements collection is integrated into a browser-based or web-based product-management application.

For example, a web application could collect stakeholder input through forms, store requirement records through an API, validate information in the browser, and display traceability relationships interactively.

The asynchronous interview simulation demonstrates that application workflows may collect information from multiple sources concurrently. The example is deliberately simulated because actual stakeholder elicitation still requires people and structured facilitation.

## The C++ case study

The C++ implementation models a digital application management platform.

The scenario includes:

- customers
- operations managers
- security officers
- application submission
- application status tracking
- access control
- audit logging
- performance requirements
- traceability
- change requests
- version history

The system begins by defining strongly typed enumerations for requirement types, priorities, and statuses.

The `Stakeholder` structure represents participants in the requirements process.

The `Requirement` structure contains the core requirements information.

The validation functions examine structural completeness and potentially ambiguous language.

The `UserStory` structure represents user-oriented requirements.

The `UseCase` structure models a workflow with preconditions, main flow, alternate flows, and postconditions.

The `RequirementsRepository` manages requirement records and historical snapshots.

The `TraceabilityMatrix` connects business needs, user stories, requirements, and tests.

The `ScopeBoundary` separates included, excluded, and unclassified items.

The `ChangeRequest` structure models controlled change.

This architecture is intentionally more explicit than the Python example. C++ requires types and data structures to be defined clearly, which makes the relationship between different elements of the requirements domain visible.

## Case study problem

The modeled organization needs a digital platform that allows customers to submit applications and track their status.

Operations staff need visibility into the process.

Security staff require authenticated and authorized access.

The project therefore needs requirements covering:

- application submission
- application tracking
- access control
- audit logging
- performance

The business requirement establishes the organizational objective.

User requirements describe customer needs.

Functional requirements describe system behavior.

Security requirements define protection conditions.

The performance requirement defines measurable response behavior.

Audit requirements establish evidence about security-relevant activity.

## Case study design

The C++ case study separates the main domain concepts.

### Stakeholders

Stakeholders contain:

- identifier
- name
- role
- influence
- interest
- needs
- concerns

### Requirements

Requirements contain:

- identifier
- title
- description
- type
- priority
- source
- stakeholders
- acceptance criteria
- dependencies
- assumptions
- status
- version

### Repository

The repository provides controlled access to requirements and historical snapshots.

`std::map` is used because deterministic identifier ordering is convenient for demonstration and inspection.

An alternative production design could use `std::unordered_map` where average constant-time identifier lookup is more important than ordering.

### Traceability

The traceability matrix uses maps from one requirement layer to another.

This demonstrates the principle that requirements should not exist as isolated statements.

### Change control

A change request records who requested a modification, why it was requested, its expected impact, and its status.

The repository records a previous snapshot before changing the current requirement.

## Algorithms and complexity

Different data structures provide different lookup characteristics.

A sequential search through a vector generally requires O(n) time.

A balanced tree structure such as `std::map` generally provides O(log n) lookup.

A hash table such as `std::unordered_map` provides average O(1) lookup, although worst-case behavior can degrade.

Requirements repositories also require operations other than lookup.

Examples include:

- filtering
- sorting
- full-text search
- relationship traversal
- version retrieval
- impact analysis

For large systems, the requirements repository would normally move beyond an in-memory structure and use indexed persistent storage.

## Edge cases

Requirements collection must handle situations such as:

- duplicate requirement identifiers
- missing requirements
- incomplete requirements
- missing stakeholders
- requirements without acceptance criteria
- ambiguous terminology
- conflicting access rules
- requirements without test mappings
- scope items that are neither clearly included nor excluded
- changes to approved requirements
- dependencies on changed requirements

The implementations deliberately demonstrate these situations.

## Failure handling

A requirements tool should fail safely.

For example, attempting to create a duplicate identifier should not silently overwrite an existing requirement.

The Python implementation raises exceptions for duplicate identifiers and missing records.

The JavaScript implementation uses exceptions for invalid repository operations.

The C++ implementation uses exceptions such as `std::invalid_argument`, `std::runtime_error`, and `std::out_of_range`.

The exact error-handling strategy can vary by architecture, but silent data corruption is particularly dangerous in requirements management.

## Security considerations

Requirements repositories may contain sensitive information.

Examples include:

- internal business processes
- security requirements
- system architecture details
- regulatory interpretations
- customer information
- supplier information
- operational constraints
- unpublished product plans

Important controls include:

- authentication
- authorization
- audit logging
- controlled editing
- version history
- access reviews
- secure storage
- retention rules
- appropriate confidentiality controls

Credentials and secrets should never be stored as requirements.

Authentication and authorization should also remain conceptually separate.

Authentication answers:

`Who is the user?`

Authorization answers:

`What is the user allowed to access or change?`

The C++ case study explicitly incorporates authorization into the application-data requirement.

## Performance considerations

A small requirements collection can be handled using simple data structures.

As the repository grows, performance considerations become important.

Potential requirements-management performance features include:

- indexed identifier lookup
- full-text search indexes
- pagination
- caching
- incremental loading
- efficient relationship queries
- background processing
- database indexing

Performance requirements themselves should also be measurable.

A statement such as:

`The system must be fast.`

does not define a testable target.

A statement such as:

`The system shall return search results within 2 seconds for at least 95% of requests under the approved production workload.`

provides a defined measurement condition.

## Common mistakes

### Starting with a solution instead of the problem

A stakeholder may request:

`We need a mobile application.`

The actual need may be faster access to information rather than a mobile application itself.

Requirements collection should investigate the underlying problem before locking the project into a solution.

### Treating every stakeholder statement as a final requirement

A stakeholder statement is evidence.

It may require clarification, validation, conflict resolution, and formalization before becoming an approved requirement.

### Using vague language

Terms such as `fast`, `easy`, and `user-friendly` often need measurable definitions.

### Ignoring exceptions

A process description that only covers the successful path is incomplete.

Important exceptions may include:

- invalid input
- missing data
- duplicate records
- authorization failure
- network failure
- external service failure
- database failure
- timeout
- partial completion

### Ignoring non-functional requirements

Teams often focus on features and neglect:

- performance
- security
- availability
- accessibility
- maintainability
- reliability
- auditability
- recoverability

A system can provide every requested feature and still fail operationally.

### Failing to record the source

Without source information, it becomes difficult to determine why a requirement exists or who should validate a disputed interpretation.

### Failing to control changes

Requirements inevitably change. Uncontrolled changes can cause scope expansion, conflicting requirements, missed tests, and inaccurate project plans.

### Treating priority as permanent

A requirement marked as high priority can become less important when business circumstances change.

Priorities should therefore have a defined ownership and review mechanism.

### Assuming one stakeholder represents everyone

Different stakeholders can have different needs and constraints.

Requirements should be validated across the relevant stakeholder groups.

## Practical workflow

A disciplined requirements collection process can follow this sequence:

1. Define the problem and desired business outcome.
2. Establish initial project scope.
3. Identify relevant stakeholders.
4. Understand the current process.
5. Review existing documentation.
6. Conduct interviews and workshops.
7. Observe important operational workflows.
8. Capture user goals and pain points.
9. Identify business rules and constraints.
10. Identify functional requirements.
11. Identify non-functional requirements.
12. Identify data and interface requirements.
13. Identify security and regulatory requirements.
14. Record assumptions and dependencies.
15. Convert raw findings into structured requirements.
16. Write acceptance criteria.
17. Review ambiguity and completeness.
18. Identify conflicts.
19. Assess feasibility.
20. Prioritize requirements.
21. Establish traceability.
22. Validate requirements with stakeholders.
23. Baseline approved requirements.
24. Manage future changes through controlled change requests.

The process is iterative. New information can cause earlier requirements to be clarified or changed.

## Important distinctions

### Requirement versus feature

A feature is generally a user-visible or system-visible capability.

A requirement describes what the solution must satisfy.

One requirement may contribute to several features, and one feature may satisfy multiple requirements.

### Requirement versus specification

A requirement describes what is needed.

A technical specification can describe how the solution will implement it.

The distinction prevents technical design decisions from being presented prematurely as business needs.

### Requirement versus acceptance criterion

A requirement describes an expected condition.

Acceptance criteria define conditions by which that expectation can be verified.

### Requirement versus constraint

A requirement may describe desired behavior.

A constraint limits how the solution can be designed or delivered.

### Assumption versus fact

A fact has been established through appropriate evidence.

An assumption is being treated as true for planning purposes and may require verification.

### Stakeholder need versus stakeholder solution

A stakeholder may request a particular implementation because they believe it solves their problem.

Requirements analysis should distinguish the underlying need from the proposed solution.

## Real-world applications

Requirements collection applies to:

- enterprise software
- banking systems
- healthcare systems
- government platforms
- e-commerce
- logistics
- manufacturing
- cybersecurity systems
- data platforms
- cloud services
- mobile applications
- financial technology
- educational platforms
- industrial automation
- embedded systems
- artificial intelligence systems
- infrastructure projects

The techniques vary by domain, but the core reasoning remains similar:

Identify the problem, identify the stakeholders, understand the context, define the required outcome, make the requirement testable, validate it, and control changes.

## Requirements collection checklist

A complete collection exercise should consider:

- [ ] Business problem defined
- [ ] Desired business outcome defined
- [ ] Scope boundaries established
- [ ] Stakeholders identified
- [ ] Stakeholder roles documented
- [ ] Current process understood
- [ ] Existing documentation reviewed
- [ ] Interviews conducted where appropriate
- [ ] Workshops conducted where appropriate
- [ ] Observation performed where appropriate
- [ ] User needs identified
- [ ] Business rules identified
- [ ] Functional requirements identified
- [ ] Non-functional requirements identified
- [ ] Data requirements identified
- [ ] Interface requirements identified
- [ ] Security requirements identified
- [ ] Regulatory requirements identified
- [ ] Constraints documented
- [ ] Assumptions documented
- [ ] Dependencies documented
- [ ] Acceptance criteria defined
- [ ] Ambiguity reviewed
- [ ] Conflicts analyzed
- [ ] Feasibility considered
- [ ] Priorities established
- [ ] Traceability established
- [ ] Requirements validated
- [ ] Approved requirements baselined
- [ ] Change management established
- [ ] Requirement versions controlled
- [ ] Verification coverage reviewed

## Implementation relationship

The three programs intentionally overlap in their domain model while emphasizing different programming techniques.

The Python implementation emphasizes breadth and educational progression. It demonstrates requirements collection as an analytical discipline and uses Python's flexible data structures to model the lifecycle.

The JavaScript implementation emphasizes application-oriented behavior. It demonstrates how requirements could be represented and manipulated inside a web-oriented application, including asynchronous collection workflows.

The C++ implementation emphasizes a strongly structured technical case study. It models a realistic application-management platform and demonstrates explicit types, repository design, exception handling, traceability, versioning, and algorithmic considerations.

Together, the implementations show that requirements collection is not merely documentation. It is a structured engineering activity connecting stakeholder needs, business objectives, system behavior, quality attributes, verification, and controlled change.
