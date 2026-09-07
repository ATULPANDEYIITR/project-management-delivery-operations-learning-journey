# Project Scope: What Is Included and Excluded

## Introduction

Project scope defines the boundaries of a project. It establishes the work, deliverables, features, responsibilities, and outcomes that the project is authorized to provide. It also identifies work and responsibilities that are outside those boundaries.

A fundamental scope question is:

- What is included in the project?
- What is excluded from the project?

A project can fail to meet expectations even when the team completes a large amount of work if stakeholders do not share the same understanding of those boundaries. Clear scope management reduces ambiguity, supports planning, controls changes, and provides a basis for evaluating whether a deliverable is complete and acceptable.

The Python script demonstrates project scope concepts through definitions, data structures, validation functions, dependency analysis, change workflows, testing, and practical examples.

---

# 1. Meaning of Project Scope

Project scope is the defined boundary of authorized project work.

It describes:

- What the project will deliver.
- What work the project team will perform.
- What requirements must be satisfied.
- What responsibilities belong to the project.
- What responsibilities do not belong to the project.
- What conditions determine successful completion.

Scope is not simply a list of features. It connects requirements, deliverables, activities, responsibilities, acceptance criteria, assumptions, constraints, and change-control decisions.

A useful scope definition must be sufficiently clear that relevant stakeholders can distinguish between approved work and work that requires clarification or authorization.

---

# 2. Included Scope

Included scope consists of work, deliverables, services, features, or responsibilities that are formally part of the project.

Examples include:

- Designing a website.
- Developing a user registration system.
- Integrating an approved payment provider.
- Performing functional testing.
- Deploying an approved application.
- Producing specified reports.

An inclusion should be specific enough to support planning and execution.

For example:

> Develop a website.

This statement may be too broad because it does not identify the required functionality.

A more useful scope statement may specify:

- Responsive public website.
- Contact form.
- Basic search engine optimization.
- Compatibility with defined browsers.
- Deployment to an approved hosting environment.

Specific inclusions reduce the possibility that stakeholders interpret broad statements differently.

---

# 3. Excluded Scope

Excluded scope consists of work, deliverables, responsibilities, or services that are explicitly outside the project boundary.

Examples include:

- Native Android application development.
- Native iOS application development.
- Long-term customer support operations.
- Content creation after project delivery.
- Marketing campaign management.
- Hardware procurement.

Exclusions are particularly important because stakeholders may otherwise assume that a related activity is included.

For example, a project called "E-Commerce Website Development" may cause stakeholders to assume that the project includes:

- Product photography.
- Inventory management.
- Warehouse integration.
- Payment processing.
- Customer support.
- Mobile applications.
- Marketing automation.

Some of these activities may be required, while others may be outside project responsibility. Explicit exclusions make those boundaries visible.

---

# 4. Scope Boundaries

A scope boundary separates three categories of work:

1. Included work.
2. Excluded work.
3. Work requiring clarification or formal evaluation.

The Python script models these categories using the `ScopeStatus` enumeration:

- `INCLUDED`
- `EXCLUDED`
- `UNCLEAR`

The `ScopeBoundary` class demonstrates a basic classification mechanism.

A request matching approved included work is classified as included. A request matching an explicit exclusion is classified as excluded. Any other request is classified as unclear.

The unclear category is important. Work should not automatically be treated as included merely because it appears useful or related to the project.

An unclear request may represent:

- A new requirement.
- A partially specified requirement.
- A dependency.
- A misunderstanding.
- A future project.
- A scope change requiring approval.

---

# 5. Project Scope and Product Scope

Project scope and product scope are related but distinct.

## Project Scope

Project scope focuses on the work required to complete the project.

Examples:

- Design the authentication workflow.
- Develop authentication functionality.
- Test authentication.
- Deploy the approved system.

## Product Scope

Product scope focuses on the characteristics and capabilities of the final product.

Examples:

- Users can create accounts.
- Users can log in with approved credentials.
- Invalid login attempts are rejected.
- Passwords must meet defined requirements.

Project scope asks:

> What work must be performed?

Product scope asks:

> What characteristics must the resulting product have?

A complete project must manage both perspectives.

---

# 6. Requirements

A requirement is a defined need or condition that a deliverable must satisfy.

Examples:

- Users can create an account using email and password.
- Users can log into the system.
- Invalid credentials are rejected.
- Course purchasers can access purchased content.

The script represents requirements using the `Requirement` data class.

Each requirement includes:

- A unique identifier.
- A description.
- Acceptance criteria.
- A priority.

Unique identifiers improve traceability because requirements can be connected to:

- Deliverables.
- Design decisions.
- Implementation work.
- Tests.
- Change requests.
- Acceptance records.

---

# 7. Deliverables

A deliverable is a verifiable output produced by the project.

Examples:

- Authentication module.
- Website.
- Course catalog.
- Payment module.
- Inventory report.
- Deployment package.

A deliverable is different from an activity.

For example:

Deliverable:

> User Authentication Module

Activities:

- Design authentication flow.
- Implement authentication logic.
- Test authentication.

The deliverable is the output. The activities are work performed to produce or validate that output.

Confusing activities and deliverables can make scope planning unclear because a project may complete activities without producing an acceptable deliverable.

---

# 8. Acceptance Criteria

Acceptance criteria define conditions that must be satisfied before a requirement or deliverable is accepted.

Examples:

- A valid email address is required.
- A password must satisfy defined security requirements.
- Invalid credentials are rejected.
- A successful registration creates an account.

Acceptance criteria reduce subjective interpretations of completion.

Without acceptance criteria, stakeholders may disagree about whether work is complete.

The script models acceptance testing through the `AcceptanceTest` class. Each test compares an expected result with an actual result.

A deliverable review is also demonstrated using `DeliverableReview`, which determines whether all required conditions have passed.

---

# 9. Specific and Ambiguous Scope Statements

Scope statements should avoid subjective terms unless those terms are supported by measurable definitions.

Examples of potentially ambiguous words include:

- Modern.
- Fast.
- User-friendly.
- High-quality.
- Advanced.
- Appropriate.

The statement:

> Build a modern, fast, user-friendly website.

does not provide measurable boundaries.

A more precise statement may define:

- Supported screen sizes.
- Response-time requirements.
- Browser compatibility.
- Accessibility requirements.
- Defined user tasks.
- Measurable usability criteria.

The script includes the `evaluate_scope_statement` function, which demonstrates simple detection of potentially vague terminology.

This implementation is intentionally limited. Real scope analysis requires stakeholder interpretation because ambiguity is often contextual.

---

# 10. Scope Statement

A project scope statement formally documents major project boundaries.

The script models a scope statement using the `ScopeStatement` data class.

It contains:

- Project name.
- Objective.
- Deliverables.
- Inclusions.
- Exclusions.
- Acceptance criteria.
- Assumptions.
- Constraints.

A complete scope statement does not necessarily need identical wording across projects, but these categories address common causes of misunderstanding.

---

# 11. Project Objective

The project objective describes the intended outcome.

An objective should communicate the purpose of the project without replacing detailed scope.

For example:

> Deliver a minimum viable web platform allowing students to register, purchase approved courses, and access course content.

The objective identifies the intended business outcome.

Detailed inclusions and exclusions define the operational boundary.

---

# 12. Assumptions

An assumption is a planning condition believed to be true without complete certainty.

Examples:

- The client will provide branding assets.
- Subject matter experts will be available.
- Course content will be available for testing.
- A payment provider account will be available.

Assumptions are important because project plans may depend on conditions outside the project team's direct control.

If an assumption becomes false, the project may experience:

- Delay.
- Increased cost.
- Rework.
- Scope conflict.
- Increased risk.

Assumptions should therefore be visible rather than hidden inside informal expectations.

---

# 13. Constraints

A constraint is a limitation affecting available choices.

Common constraints include:

- Budget.
- Deadline.
- Technology requirements.
- Resource availability.
- Contractual obligations.
- Regulatory requirements.

Examples:

- The project must remain within the approved budget.
- The system must be released before a contractual deadline.
- Only approved technologies may be used.

Constraints influence what scope can realistically be delivered.

A technically desirable feature may still be rejected if it violates a schedule or budget constraint.

---

# 14. Work Breakdown Structure

A Work Breakdown Structure, commonly abbreviated as WBS, decomposes project scope into smaller components.

The script represents this using the recursive `WBSNode` class.

A simplified hierarchy may contain:

- Project.
  - User Management.
    - Registration.
    - Login.
    - Password Security.
  - Course Management.
    - Course Catalog.
    - Course Details.
    - Course Access.
  - Payments.
    - Payment Provider Integration.
    - Payment Confirmation.
  - Testing.
    - Functional Testing.
    - Acceptance Testing.

The WBS improves scope management by making work more visible and structured.

The script includes:

- Recursive printing of the hierarchy.
- Identification of leaf-level work components.

---

# 15. The 100 Percent Principle

The 100 Percent Principle states that the WBS should represent the complete approved scope.

This means:

- Required scope should not be missing.
- Unapproved work should not be silently included.

The script demonstrates this by comparing:

- Approved scope.
- Planned work.

The `compare_scope_to_wbs` function identifies:

- Approved work that is missing from the plan.
- Planned work that may not belong to approved scope.

This comparison is useful because planning errors can occur in either direction.

Missing work may create incomplete deliverables.

Extra work may create unnecessary cost, delay, or uncontrolled scope expansion.

---

# 16. Scope Baseline

A scope baseline is an approved reference used to evaluate project work.

A practical scope baseline may include:

- Approved scope statement.
- Approved requirements.
- Work Breakdown Structure.
- Detailed work descriptions.

The baseline provides a reference for determining whether a request represents:

- Existing approved scope.
- Clarification of existing scope.
- New scope.
- A required scope change.

A baseline does not mean that scope can never change. It means changes should be visible and controlled.

---

# 17. Dependencies and Scope Boundaries

Included work may depend on external components.

For example:

> Course Access

may depend on:

- Authentication.
- Payment confirmation.

Payment confirmation may depend on:

- An external payment provider.

A critical scope problem occurs when an included component depends on something explicitly excluded or undefined.

The script uses `ScopedFeature` and `validate_dependencies` to identify cases where:

- An included feature depends on an excluded feature.
- An included feature depends on an undefined component.

An exclusion may therefore create a feasibility problem if required dependencies are not properly assigned or addressed.

---

# 18. Scope Creep

Scope creep is uncontrolled expansion of project requirements or work.

Example:

The approved scope contains:

- Student registration.
- Student login.
- Course catalog.

A stakeholder requests:

> Add a gamification system with achievement badges.

If the team begins implementing the feature without evaluating or approving the change, the project scope has expanded without proper control.

Scope creep can affect:

- Cost.
- Schedule.
- Resources.
- Quality.
- Risk.
- Testing effort.
- Operational complexity.

The `ScopeManager` class demonstrates how a request can remain outside approved scope until formally approved.

---

# 19. Scope Creep and Approved Scope Changes

Scope expansion is not automatically scope creep.

A legitimate scope change may be necessary because of:

- Business changes.
- Customer requirements.
- Regulations.
- Technology changes.
- Strategic decisions.
- Newly discovered constraints.

The difference is controlled authorization.

An approved scope change should normally involve:

1. Identification of the proposed change.
2. Impact analysis.
3. Risk evaluation.
4. Stakeholder review.
5. Authorization or rejection.
6. Documentation.
7. Plan or baseline updates when approved.

The script demonstrates this concept using scope requests and change-state workflows.

---

# 20. Gold Plating

Gold plating occurs when a team adds unrequested or unapproved functionality.

Example requirement:

> Users can download a report as PDF.

The team also adds:

- Interactive dashboards.
- Spreadsheet export.
- Automated email reports.
- Custom report themes.

These additions may appear beneficial, but they increase project complexity.

Gold plating may introduce:

- Additional development work.
- Additional testing.
- New security risks.
- More maintenance requirements.
- Schedule delays.
- Cost increases.

Professional scope management focuses on delivering approved requirements rather than assuming that additional features are automatically valuable.

---

# 21. Change Impact Analysis

A scope change can affect multiple project dimensions.

The script models this using the `ChangeImpact` data class.

The demonstrated analysis considers:

- Cost impact.
- Schedule impact.
- Risk level.
- Resource requirements.
- Available budget.
- Available schedule capacity.

The `analyze_change` function demonstrates simplified decision logic.

Real projects may also evaluate:

- Contractual obligations.
- Architecture.
- Security.
- Compliance.
- Operations.
- Procurement.
- Training.
- Support.
- Data migration.
- Stakeholder priorities.

A scope change should therefore not be evaluated only by asking whether the requested feature is technically possible.

---

# 22. Scope Prioritization

Not all requested functionality has equal importance.

The script demonstrates MoSCoW prioritization:

- Must Have.
- Should Have.
- Could Have.
- Will Not Have in This Release.

Prioritization is particularly useful when:

- Budget is limited.
- Deadlines are fixed.
- Resources are constrained.
- Requirements exceed available capacity.

An explicit "Will Not Have" category is closely related to scope exclusions because it documents functionality intentionally excluded from the current release.

---

# 23. Stakeholder Perspectives

Different stakeholders may interpret scope differently.

Examples include:

## Sponsor

Interested in:

- Business value.
- Cost.
- Strategic alignment.

## Customer

Interested in:

- Required features.
- Usability.
- Expected outcomes.

## Project Manager

Interested in:

- Clear boundaries.
- Planning.
- Controlled changes.

## Development Team

Interested in:

- Technical requirements.
- Implementation boundaries.
- Dependencies.

## Operations Team

Interested in:

- Deployment.
- Monitoring.
- Maintenance.
- Support responsibilities.

Scope documentation should establish a shared understanding across these perspectives.

---

# 24. Unclear Requests and Similarity Analysis

Scope terminology may differ between stakeholders.

For example:

> User account signup

may refer to:

> User registration

The script demonstrates the standard library `difflib` module through `ScopeSimilarityChecker`.

This can help identify potentially related scope items.

Similarity matching has limitations.

It cannot determine whether two requirements are truly equivalent.

For example:

- User registration.
- User identity verification.

These concepts may appear related but can involve significantly different work, security requirements, compliance obligations, and cost.

Similarity tools can support review, but formal scope decisions require contextual judgment.

---

# 25. Excluded Responsibility Does Not Mean Irrelevance

An activity may be excluded from the project team's responsibility while still affecting project success.

Example:

Excluded:

> Creation of course content.

The project may still depend on:

- Content being available.
- Content owners approving material.
- Content being ready for testing.

The excluded activity may therefore be:

- An external dependency.
- An assumption.
- A stakeholder responsibility.
- A project risk.

This distinction is important.

"Not our responsibility" does not necessarily mean "irrelevant to delivery."

---

# 26. Responsibility Boundaries

Scope should often be connected with responsibility definitions.

The script demonstrates a responsibility model similar to common responsibility assignment approaches.

Responsibilities include:

- Responsible.
- Accountable.
- Consulted.
- Informed.

For example:

| Activity | Stakeholder | Responsibility |
|---|---|---|
| Develop website | Development Team | Responsible |
| Approve scope | Project Sponsor | Accountable |
| Review branding | Marketing Team | Consulted |
| Receive release update | Operations Team | Informed |

Clear responsibility boundaries reduce situations where multiple parties assume another team is responsible.

---

# 27. Common Scope Mistakes

## Vague Inclusions

Using subjective terminology without measurable definitions.

## Missing Exclusions

Stakeholders may assume related work is included.

## Confusing Deliverables and Activities

Activities describe work. Deliverables describe outputs.

## Ignoring Dependencies

An included feature may depend on excluded or undefined work.

## Informal Scope Changes

New work is accepted without evaluating impacts.

## Gold Plating

Teams add functionality that was not requested or approved.

## Missing Acceptance Criteria

Stakeholders disagree about whether a deliverable is complete.

## Inconsistent Terminology

Different stakeholders use the same words with different meanings.

---

# 28. Automated Scope Quality Checking

The script implements `validate_scope_quality`.

It checks for issues such as:

- Missing objective.
- Missing deliverables.
- Missing inclusions.
- Missing exclusions.
- Missing acceptance criteria.
- Conflicts between included and excluded items.

The validation function returns a `ScopeQualityReport` containing:

- Errors.
- Warnings.
- A validity property.

Automated validation is useful for detecting structural problems, but it cannot determine whether the scope accurately represents stakeholder intent.

Human review remains necessary.

---

# 29. Partially Included Features

Scope is not always binary.

A feature category may be included only within specific boundaries.

Example:

Included:

- Payment processing through the approved provider.
- Payment confirmation.

Excluded:

- Additional payment providers.
- Cryptocurrency payments.
- Installment financing.

The category "payment processing" exists within project scope, but only defined capabilities are authorized.

The script models this through `FeatureBoundary`.

This approach prevents broad category names from creating unintended obligations.

---

# 30. Scope and Risk

Poorly defined scope creates project risk.

Examples include:

- Stakeholders misunderstanding exclusions.
- External dependencies becoming unavailable.
- Ambiguous terminology producing rework.
- Uncontrolled changes increasing cost.

The script represents risks using `ScopeRisk`.

Each risk has:

- Probability.
- Impact.
- Calculated score.
- Risk classification.

The demonstrated risk score is calculated as:

    probability × impact

The implementation then classifies the result as low, medium, or high.

Real risk models may use more complex methods and organizational criteria.

---

# 31. Scope in Predictive and Agile Environments

Predictive projects often establish more detailed scope earlier and manage changes against an approved baseline.

Agile projects may allow detailed requirements to evolve.

This does not mean agile projects have unlimited scope.

Agile delivery still requires boundaries related to:

- Product vision.
- Release objectives.
- Priorities.
- Time.
- Budget.
- Team capacity.
- Acceptance criteria.
- Definition of Done.

The script demonstrates backlog selection based on:

- Approval status.
- Priority.
- Story points.
- Release capacity.

An item may be valuable but excluded from the current release because capacity is limited.

Controlled prioritization is different from uncontrolled scope expansion.

---

# 32. Security Requirements as Scope

Security requirements can be part of project scope.

The statement:

> Make the application secure.

is too broad to provide reliable implementation or acceptance criteria.

Specific requirements may include:

- Passwords must not be stored in plaintext.
- Approved encrypted communication mechanisms must be used.
- Administrative functions require appropriate authorization.
- Authentication failures must not reveal sensitive information.

The script demonstrates a simple password validation function.

It checks:

- Minimum length.
- Uppercase characters.
- Lowercase characters.
- Digits.

The example is educational and not a complete production authentication system.

Production security design requires established security standards, secure password hashing, access control, secure storage, logging controls, threat modeling, and appropriate testing.

---

# 33. Performance Requirements

Performance requirements should be measurable.

The statement:

> The application must be fast.

does not define acceptable performance.

A measurable requirement may specify:

> Under the defined test environment, 95 percent of approved requests must complete within two seconds.

The script demonstrates percentile calculation through `calculate_percentile`.

The function handles important edge cases:

- Empty input raises `ValueError`.
- Percentiles below zero are rejected.
- Percentiles above one hundred are rejected.

Performance requirements should define context, including:

- Workload.
- Test environment.
- Request type.
- Measurement period.
- Percentile.
- Acceptable response time.

A performance number without context may still be ambiguous.

---

# 34. Requirements Traceability

Traceability connects requirements to later project activities.

A requirement can be traced to:

- A deliverable.
- Implementation work.
- Tests.
- Acceptance evidence.

The script represents this relationship using `TraceabilityRecord`.

The example connects:

- Requirement identifier.
- Requirement description.
- Deliverable.
- Test.
- Implementation status.

The `find_untraced_requirements` function identifies approved requirements that have no traceability record.

Untraced requirements create risk because they may be:

- Forgotten.
- Not implemented.
- Not tested.
- Not formally accepted.

---

# 35. Complete Practical Scope Model

The script includes an inventory management system example.

Included scope contains:

- User authentication.
- Product management.
- Stock quantity tracking.
- Stock movement recording.
- Inventory reports.
- Web application deployment.

Excluded scope contains:

- Native mobile application.
- Warehouse robotics.
- Accounting software replacement.
- Hardware procurement.
- Twenty-four-hour support operations.

The `ProjectScopeModel` class classifies requests as:

- Included.
- Excluded.
- Unclear.

This demonstrates how scope documentation can support practical decision-making.

A request for product management is included.

A request for a native mobile application is excluded.

A request for machine-learning demand forecasting is unclear and would require evaluation rather than automatic implementation.

---

# 36. Change-Control Workflow

The script implements an advanced workflow using `ChangeState`.

Possible states include:

- Submitted.
- Under Review.
- Approved.
- Rejected.
- Implemented.

The `ChangeControlBoard` class defines valid transitions.

For example:

Submitted → Under Review

Under Review → Approved

Under Review → Rejected

Approved → Implemented

Invalid transitions raise an error.

This prevents logically inconsistent changes, such as moving directly from a submitted state to implementation without review and approval.

A production workflow may also require:

- Financial authorization.
- Technical review.
- Security review.
- Compliance approval.
- Contract review.
- Documentation updates.
- Baseline updates.

---

# 37. Testing Scope Management Logic

The script includes automated tests using Python assertions.

The tests verify:

- Included items are classified correctly.
- Excluded items are classified correctly.
- Unclear items are detected.
- Inclusion and exclusion conflicts are identified.
- Included features depending on excluded features are detected.
- Change workflows enforce valid transitions.

Testing management logic is important when scope management becomes part of a software system.

Incorrect scope classification can cause:

- Unauthorized work.
- Incorrect reporting.
- Approval errors.
- Missing requirements.
- Compliance problems.

---

# 38. Production Considerations

Production scope management requires more than maintaining a list of requirements.

## Version Control

Scope documents and change records should have controlled versions.

## Authorization

Significant changes should be approved by authorized stakeholders.

## Traceability

Requirements should connect to implementation and validation evidence.

## Auditability

Important decisions should have documented rationale.

## Operational Boundaries

Projects should clarify responsibilities after delivery.

Questions may include:

- Who maintains the system?
- Who provides support?
- Who monitors production?
- Who handles incidents?
- Who owns future changes?

## Security and Compliance

Security, privacy, contractual, and regulatory responsibilities should be explicitly assigned when relevant.

## Dependency Management

External systems and teams may affect delivery even when their work is excluded from the project's direct responsibilities.

## Change Discipline

Informal conversations should not silently change commitments involving cost, schedule, risk, quality, or contractual obligations.

---

# 39. Important Distinctions

## Included Scope

Work or deliverables the project is authorized to perform or provide.

## Excluded Scope

Work or deliverables explicitly outside project responsibility.

## Assumption

A planning condition believed to be true without complete certainty.

## Constraint

A limitation affecting available choices.

## Requirement

A defined need or condition that a deliverable must satisfy.

## Deliverable

A verifiable output produced by the project.

## Acceptance Criterion

A measurable condition used to determine whether work is acceptable.

## Scope Creep

Uncontrolled expansion of work or requirements.

## Approved Scope Change

An authorized modification evaluated through an appropriate process.

## Gold Plating

Adding functionality that was not requested or approved.

---

# 40. Best Practices for Defining Inclusions and Exclusions

A strong scope definition should:

1. Use specific language.
2. Define major deliverables.
3. Explicitly identify excluded work.
4. Distinguish requirements from activities.
5. Define acceptance criteria.
6. Identify assumptions.
7. Identify constraints.
8. Identify important dependencies.
9. Define responsibility boundaries.
10. Establish a reference baseline.
11. Evaluate changes before implementation.
12. Maintain traceability between requirements and validation.
13. Avoid unapproved features.
14. Review scope with relevant stakeholders.
15. Treat unclear requests as requiring clarification rather than assuming inclusion.

---

# 41. Performance and Complexity Considerations

The script uses mostly simple data structures such as:

- Lists.
- Sets.
- Dictionaries.
- Data classes.
- Enumerations.

Set operations are particularly useful for scope comparison because they efficiently identify:

- Missing approved work.
- Extra planned work.
- Overlap between inclusions and exclusions.

The dependency validation example performs repeated checks across features and dependencies. For very large project portfolios, a graph-based representation may be more appropriate.

Large-scale systems may model:

- Requirements as nodes.
- Dependencies as edges.
- Deliverables as grouped components.
- Change requests as versioned events.

This enables more advanced analysis of dependency chains and change impacts.

---

# 42. Limitations of Automated Scope Analysis

Automated analysis cannot fully replace project judgment.

Software can detect structural issues such as:

- Missing fields.
- Duplicate entries.
- Inclusion and exclusion conflicts.
- Undefined dependencies.

Software cannot reliably determine all business interpretations.

For example:

> Support international customers.

This may involve:

- Multiple languages.
- Multiple currencies.
- Tax compliance.
- International payments.
- Regional hosting.
- Data privacy requirements.

The statement requires stakeholder clarification.

Automated tools are most effective when used with clear terminology, structured requirements, traceability, and formal review processes.

---

# 43. Real-World Relevance

Scope boundaries affect nearly every major project-management activity.

They influence:

- Cost estimation.
- Scheduling.
- Resource planning.
- Procurement.
- Risk management.
- Testing.
- Security.
- Stakeholder communication.
- Contract management.
- Operational handover.

A project team cannot reliably estimate cost or schedule without understanding what work is included.

Similarly, stakeholders cannot reliably evaluate success without knowing what the project was expected to deliver.

Clear inclusion and exclusion statements therefore serve as a shared reference for project decisions throughout the project lifecycle.
