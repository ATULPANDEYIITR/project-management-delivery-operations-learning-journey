# Project Activity Identification

## Purpose

Activity identification is the process of determining the actual pieces of work and meaningful project events that must exist for a project to produce its planned deliverables.

The activity list is more specific than a high-level project scope statement and more operational than a broad work package. A useful activity has a recognizable purpose, an understandable outcome, and enough definition to be assigned, estimated, sequenced, monitored, and eventually completed.

This repository models activity identification for a realistic operational analytics implementation. The examples distinguish between identifying project work, validating the resulting activity model, understanding dependencies, classifying work, and detecting gaps before detailed scheduling begins.

The three implementations deliberately approach the subject differently:

| Implementation | Primary perspective |
| --- | --- |
| Python | A comprehensive activity identification and dependency-analysis engine |
| JavaScript | An event-driven activity register with candidate extraction and workflow validation |
| C++ | A repository-style governance engine for a realistic analytics project activity model |

The central relationship is:

`project objective → deliverables → work packages → activities → dependencies → schedule`

Activity identification sits between high-level project decomposition and detailed schedule construction. If activities are missing, duplicated, overly broad, or incorrectly connected, later planning calculations inherit those defects.

## Activity Identification

An activity is a defined unit of project work or a meaningful project event that can be recognized independently within the project model.

The implementations distinguish activities from general statements.

A statement such as `improve operational reporting` describes an objective or desired outcome. It does not identify enough concrete work to support assignment or scheduling.

Statements such as `identify operational reporting requirements`, `define analytical data model`, and `implement reporting data pipeline` are identifiable activities because each describes a distinct piece of work with a recognizable result.

An activity can also represent an event rather than a duration-bearing task. The examples use a production-readiness milestone for this purpose. The milestone has zero duration because it represents a point in the project rather than a period of work.

## From Deliverables to Activities

Activity identification works best when the project team decomposes deliverables into the work required to produce them.

For the analytics scenario, the project needs an operational reporting capability. That broad result is decomposed into intermediate outputs:

- A validated requirements register captures the reporting needs that have been identified and agreed.
- An analytical data model defines the entities, measures, dimensions, and relationships required by reporting.
- A dashboard interaction specification defines how users navigate and interact with the reporting interface.
- A validated reporting pipeline provides the transformed data needed by the dashboard.
- A functional dashboard provides the user-facing reporting capability.
- An integration validation report provides evidence that the complete flow has been tested.
- An operational readiness decision represents the formal review of whether the implementation is ready for operational use.

These outputs make the activities identifiable because the project team can connect work to a tangible result.

## Activity Boundaries

A useful activity has a meaningful boundary.

`Build reporting system` is too broad for detailed activity identification because it combines requirements, architecture, data engineering, interface development, testing, and operational readiness.

The examples separate those areas into activities with different owners, durations, deliverables, and dependencies.

The opposite problem is excessive decomposition. Splitting `implement reporting data pipeline` into dozens of tiny actions may make the activity register difficult to manage without adding useful control. The appropriate level depends on project complexity, reporting needs, ownership boundaries, and the level at which progress must be controlled.

Activity identification therefore involves judgment rather than simply producing the largest possible list.

## Activity Attributes

The implementations use several attributes to make identified activities operationally useful.

| Attribute | Purpose |
| --- | --- |
| Activity ID | Provides a stable identifier for the activity |
| Name | Provides a concise description of the work or event |
| Description | Records the specific purpose of the activity |
| Type | Distinguishes tasks, reviews, handoffs, and milestones |
| Owner | Identifies the function or role responsible for the activity |
| Duration | Represents expected elapsed project work time in the simplified models |
| Priority | Indicates the level of planning attention required |
| Dependencies | Identifies prerequisite activities |
| Deliverable | Identifies the result expected from the activity |
| Tags | Groups activities into work packages or functional areas |

The attributes do not make an activity valid by themselves. They provide enough structure to examine whether the identified work is complete and coherent.

## Candidate Activity Identification

The Python and JavaScript implementations include rule-based candidate extraction from project descriptions.

The extractor looks for action-oriented language such as `identify`, `define`, `design`, `implement`, `validate`, `review`, and `deploy`.

For example, a statement containing `Define the analytical data structure` can be recognized as a candidate because `define` indicates an actionable activity.

Candidate extraction is not treated as final activity identification. Natural-language statements can contain multiple activities, vague actions, objectives, constraints, or outcomes. The extracted candidates therefore require project-team validation.

This distinction is important:

`candidate extraction` identifies possible activities from source descriptions.

`activity validation` determines whether those candidates are sufficiently distinct, meaningful, and structurally valid.

## Activity Types

The examples use several activity types because not every project activity represents the same kind of work.

### Tasks

A task represents duration-bearing project work such as implementing a data pipeline or designing an interaction model.

Tasks normally have an owner, duration, deliverable, and possibly prerequisites.

### Reviews

A review is modeled separately when the project requires a deliberate evaluation or decision activity.

`Validate end-to-end reporting flow` and `Review operational readiness` are reviews because their purpose is evaluation rather than construction.

This distinction is useful when review work has a different owner, duration, or governance significance from implementation work.

### Handoffs

A handoff represents a transfer of operational responsibility or information between project functions.

The JavaScript implementation demonstrates an operational handoff after production-readiness work. Treating the handoff as an identifiable activity makes the transfer visible instead of hiding it inside another task.

### Milestones

A milestone represents a significant event or point in the project.

The production-readiness milestone has zero duration. It does not represent the work required to achieve readiness. That work is represented by separate activities such as validation and readiness review.

This distinction prevents a milestone from being incorrectly used as a substitute for the activities that produce the milestone.

## Dependency Identification

Dependencies describe relationships between activities.

For example:

`Identify requirements → Define data model → Implement data pipeline`

means the data model cannot be treated as independent of the requirements activity, and the pipeline implementation depends on the defined data model.

The examples represent dependencies as directed relationships from an activity to its prerequisites.

For `ACT-205`, the dashboard implementation depends on both the interaction design and the reporting data pipeline. The activity therefore cannot be considered structurally ready until both prerequisite activities are identified.

Dependencies are not the same as simply listing activities in an arbitrary order. A dependency expresses a logical relationship that constrains sequencing.

## Dependency Graph

The activity model can be represented as a directed graph.

A simplified representation of the analytics project is:

`ACT-201 → ACT-202 → ACT-204 → ACT-205 → ACT-206 → ACT-207 → ACT-208`

and in parallel:

`ACT-201 → ACT-203 → ACT-205`

This structure shows why activity identification should happen before detailed scheduling.

The project does not consist of one linear chain. Some activities can be performed after a common prerequisite and before a later integration point.

The Python, JavaScript, and C++ implementations validate the graph and use topological ordering to produce a dependency-consistent sequence.

## Topological Ordering

Topological ordering is useful when activity dependencies form a directed acyclic graph.

An activity with no prerequisites can appear at the beginning of the dependency order. An activity with prerequisites becomes eligible for ordering only after those prerequisites have appeared.

The implementations use this property to produce deterministic activity orders.

For a graph containing:

`A → C`

and

`B → C`

both `A` and `B` can appear before `C`. Their relative order does not necessarily imply that one depends on the other.

This distinction matters because a topological order is not automatically a project schedule. It establishes dependency consistency, not resource availability, working calendars, or exact dates.

## Duplicate Activity Detection

Duplicate identification is a common activity-model quality problem.

A project team might accidentally identify both:

`Implement reporting dashboard`

and

`Build reporting dashboard`

as separate activities even though they describe the same work.

The implementations perform simple normalized-name similarity checks to detect likely duplicates.

This mechanism is deliberately conservative. Similarity is treated as a warning or validation failure in the examples rather than proof that two activities are identical. Human review is still required because two similarly named activities may represent different deliverables or scopes.

## Missing Owners

An identified activity without an owner can create accountability ambiguity.

The Python, JavaScript, and C++ implementations explicitly detect activities without assigned owners.

Ownership should represent the role or function accountable for completing or coordinating the activity. It should not be confused with every individual who contributes to the work.

For example, the analytics scenario assigns:

- Business Analyst to requirements identification.
- Data Architect to the analytical data model.
- Data Engineer to the reporting pipeline.
- Frontend Engineer to the dashboard.
- QA Engineer to end-to-end validation.
- Release Manager to operational readiness.

These ownership assignments make the activity model actionable without embedding personal staffing details into the technical model.

## Missing Deliverables

An activity can be difficult to validate if its expected result is unclear.

The implementations therefore identify actionable activities without deliverables.

A deliverable does not have to be a physical document. It can be a validated pipeline, configured system capability, approved design, test result, or formal decision.

The distinction is useful because an activity should answer the question:

`What meaningful result exists when this activity is complete?`

If that question cannot be answered, the activity may be too vague or may need clearer scope.

## Work-Package Classification

The examples use tags to associate activities with functional work packages such as:

`requirements`

`data`

`design`

`development`

`quality`

`release`

This classification is different from dependency sequencing.

Two activities can belong to the same work package while having different dependencies. Conversely, two activities in different work packages can depend directly on one another.

The work-package view helps analyze the composition of the project without confusing organizational grouping with logical sequencing.

## Identification Quality Checks

A useful activity register should be checked for structural problems before it is used for detailed schedule development.

The implementations examine:

- Duplicate activity identifiers.
- Potential duplicate names.
- Empty activity names.
- Invalid negative durations.
- Non-zero-duration milestones.
- Unknown dependencies.
- Cyclic dependencies.
- Activities without owners.
- Actionable activities without deliverables.
- High-priority activities.
- Activities with unusually large numbers of prerequisites.

These checks address different failure modes. A duplicate identifier is a data-integrity problem, while an activity without a deliverable is a scope-definition problem. An unknown dependency is a model-reference problem, while a dependency cycle is a sequencing problem.

## Python Implementation

The Python program provides the most extensive activity-analysis model.

`Activity` represents a project activity and validates core attributes when an instance is created. The class distinguishes milestones from duration-bearing work and provides normalized activity names for duplicate detection.

`ActivityRegister` is the central activity repository. It prevents duplicate identifiers, detects highly similar activity names, validates dependency references, and detects cycles in the dependency graph.

`ActivityExtractor` demonstrates candidate activity identification from project descriptions. It uses action verbs to find sentences that may represent project work.

`ActivityAnalyzer` focuses on quality analysis. It identifies activities without owners, activities without deliverables, high-attention activities, work-package groupings, and activity-type distributions.

`DependencyAnalyzer` provides topological ordering and identifies foundational activities with no prerequisites.

`SimpleActivityScheduler` demonstrates the relationship between identified activities and an earliest-start schedule. It does not claim to be a full project scheduling engine. It uses the dependency graph to calculate simple dates after activities have already been identified.

The Python failure examples demonstrate both an unknown dependency and a cyclic dependency.

## JavaScript Implementation

The JavaScript implementation emphasizes event-driven activity registration.

`ActivityRegister` uses a `Map` for activity storage and exposes an event mechanism through `on()` and `emit()`. When an activity is added, an `activityAdded` event is emitted.

This pattern is useful for applications where activity identification changes must trigger other behavior such as audit logging, interface refreshes, validation, or downstream processing.

`ActivityEventLog` records activity-registration events with timestamps.

`ActivityCandidateExtractor` provides a lightweight natural-language candidate-identification mechanism.

`ActivityAnalyzer` examines missing owners, missing deliverables, high-attention activities, and work-package distribution.

`DependencyPlanner` uses dependency relationships to produce a topological order.

The JavaScript implementation therefore focuses on how an activity-identification application could react to changes rather than simply storing static project data.

## C++ Case Study

The C++ implementation models a repository-style activity governance engine for an operational analytics project.

The `Activity` structure contains the core activity information. `ActivityRegister` owns the activity collection and performs structural validation.

The activity register uses `std::map` for deterministic activity lookup and output. Dependencies and tags use `std::set`, which provides uniqueness and predictable ordering.

The duplicate detector tokenizes activity names and calculates a simple Jaccard-style similarity:

`intersection size / union size`

A high similarity value indicates that two activity names may represent duplicate work.

`ActivityGovernanceEngine` analyzes the activity model after identification. It validates ownership and deliverables, groups activities by work package, identifies high-attention activities, and constructs a topological dependency order.

The case study contains parallel activity paths. Requirements identification feeds both the analytical data model and dashboard interaction design. The data model feeds the reporting pipeline. The design and pipeline then converge at dashboard implementation.

This is a realistic example of why activity identification must capture relationships rather than merely create a flat list.

## Activity Identification Versus Scheduling

Activity identification and scheduling are related but distinct.

Activity identification asks:

`What work and meaningful project events must be represented?`

Scheduling asks questions such as:

`When can this activity start?`

`When can it finish?`

`Which resources are available?`

`Which activities can occur concurrently?`

The Python implementation intentionally demonstrates both concepts while keeping their boundaries visible.

The activity register is created first. Dependencies are validated next. Only then does the simplified scheduler calculate earliest dates.

This separation prevents the schedule from hiding missing or incorrectly defined activities.

## Parallel Work

Activity identification should preserve genuine opportunities for parallel work.

In the analytics case:

`ACT-202` defines the analytical data model.

`ACT-203` designs the dashboard interaction model.

Both depend on `ACT-201`, but neither depends directly on the other.

Therefore, the activity model represents two parallel branches that later converge at `ACT-205`.

If the activity list were forced into a simple linear sequence, it would lose information about the actual project structure.

## Foundational Activities

An activity with no dependencies is foundational in the dependency model.

This does not necessarily mean that it is the most important activity in the project. It means that no other identified activity has been declared as its prerequisite.

The Python dependency analyzer identifies these activities explicitly.

This distinction matters because dependency status and business priority answer different questions.

An activity can be foundational without being high priority, and a critical activity can depend on several earlier activities.

## High-Attention Activities

The examples identify activities for additional planning attention when they are marked high or critical priority or have several dependencies.

This is not a formal risk score. It is a practical structural signal.

An activity with many prerequisites can be sensitive to upstream delays because multiple conditions must be satisfied before it can proceed.

A high-priority activity can also require closer planning attention because its result has greater significance to the project.

The implementations keep this classification separate from dependency logic so that priority does not accidentally become a dependency.

## Failure Conditions

### Unknown Dependencies

An activity referencing an activity that does not exist creates an invalid dependency relationship.

For example:

`ACT-300 depends on UNKNOWN-001`

cannot be resolved within the identified activity model.

The implementations detect this condition before dependency ordering.

### Cyclic Dependencies

A dependency cycle occurs when activities eventually depend on themselves through a chain.

For example:

`A → B`

and

`B → A`

creates a cycle.

A more complex cycle can involve three or more activities.

Topological ordering cannot produce a valid dependency sequence for a cyclic graph. The implementations therefore detect cycles before attempting to construct a dependency order.

### Duplicate Activities

Duplicate activities can cause double counting of work, incorrect effort estimates, conflicting ownership, and misleading schedules.

Name similarity detection helps identify suspicious records, but similarity alone is not proof of duplication.

### Missing Deliverables

An activity without a meaningful expected result may be too vague to control effectively.

The examples flag such activities for review rather than silently treating them as complete definitions.

### Invalid Milestones

A milestone with a non-zero duration mixes two different concepts: work and an event.

The implementations reject that representation and require duration-bearing work to be represented by tasks or reviews while milestones represent zero-duration events.

## Common Identification Mistakes

### Treating Objectives as Activities

`Improve reporting visibility` is an objective.

`Identify operational reporting requirements` is an activity.

The latter describes work that can be assigned and produces an identifiable result.

### Making Activities Too Broad

`Develop the entire analytics platform` combines many different forms of work and prevents clear ownership and progress measurement.

### Making Activities Too Small

Breaking every minor action into a separate controlled activity can produce administrative overhead without improving project visibility.

### Omitting Integration Work

Projects often identify development activities but omit integration, validation, readiness review, or operational handoff.

The analytics case explicitly represents these activities so that the project model includes the work required to move from implementation to operational readiness.

### Confusing Dependencies With Ownership

An activity owned by the Data Engineering function can depend on an activity owned by the Data Architecture function.

Ownership describes accountability. Dependency describes logical sequencing.

### Confusing Priority With Sequence

A critical activity is not automatically the first activity.

Priority indicates attention or importance. Dependencies determine which activities can logically precede another activity.

## Performance Considerations

The Python and C++ dependency ordering algorithms use graph traversal/topological sorting with time complexity approximately proportional to the number of activities plus dependency relationships:

`O(V + E)`

where `V` is the number of activities and `E` is the number of dependency edges.

The JavaScript planner follows the same graph principle.

Name similarity detection is more expensive than simple identifier lookup because candidate names must be compared with existing names. For large activity repositories, indexing, token-based search, or specialized similarity structures can reduce unnecessary pairwise comparisons.

Memory usage is primarily driven by the activity collection and dependency graph.

## Data Quality Considerations

Activity identification is highly dependent on input quality.

If project descriptions are vague, automated candidate extraction may produce incomplete or overly broad activities.

If dependencies are omitted, the graph may appear simpler than the actual project.

If ownership is missing, accountability becomes unclear.

If deliverables are absent, completion criteria may be difficult to determine.

For these reasons, automated extraction should be treated as a candidate-generation mechanism rather than a replacement for project analysis.

## Practical Governance

A controlled activity register should preserve stable activity identifiers and avoid silently changing the meaning of an existing activity.

Changes to activity scope should be visible because they can affect dependencies, estimates, ownership, and downstream schedule logic.

An activity that is split into two activities may require dependency relationships to be redistributed.

An activity that is merged with another may require obsolete dependencies to be removed.

Deleting an activity should therefore be treated as a structural model change rather than a simple record deletion.

## Limitations of the Implementations

The examples intentionally use simplified project-planning assumptions.

Durations are represented as integer days and do not model holidays, working calendars, time zones, partial availability, resource constraints, or elapsed-versus-working time.

Dependencies represent basic prerequisite relationships and do not implement lag, lead, finish-to-start variations, start-to-start relationships, finish-to-finish relationships, or resource-driven constraints.

The natural-language candidate extractors use action verbs and sentence-level rules. They do not understand every possible linguistic structure and may identify candidates that require human refinement.

The duplicate detectors use lexical similarity and cannot establish semantic equivalence with certainty.

The simplified scheduler demonstrates the relationship between activity identification and dates but is not a full critical-path, resource-leveling, or enterprise scheduling engine.

These limitations are deliberate because the central subject is identification of project activities rather than complete project scheduling software.

## Relationship Between the Three Implementations

The three files model the same domain from different technical perspectives.

The Python implementation emphasizes domain modeling, validation, graph analysis, and a simple scheduling transition.

The JavaScript implementation emphasizes event-driven activity registration and application behavior when identified activities are added.

The C++ implementation emphasizes deterministic data structures, validation, graph analysis, and a governance-oriented case study.

The domain relationship remains consistent:

`identify work → represent activities → validate activity definitions → identify dependencies → analyze structure → prepare for scheduling`

The implementations do not require the activity register to be a schedule. They demonstrate why a sound activity model is a prerequisite for reliable downstream planning.
