# Team Formation: Building a Project Team

## Purpose

This project models the formation of a project team from an available candidate pool. The implementation treats team formation as a constrained decision problem rather than simple employee selection.

The central domain relationship is:

`Project → Requirements → Candidate Pool → Role Coverage → Skill Coverage → Team Validation → Formation Decision`

The five implementations use the same business problem while applying different engineering approaches.

## Domain Model

A project defines:

- required roles
- required skills
- minimum team size
- maximum team size
- project risk
- availability constraints

A candidate defines:

- identity
- professional roles
- technical and operational skills
- experience
- availability
- project capacity

A valid team must satisfy the project's structural and capability requirements.

### Core Distinctions

| Concept | Meaning |
|---|---|
| Candidate | A person eligible for consideration |
| Role | A responsibility required within the team |
| Skill | A capability used to satisfy project requirements |
| Availability | Whether the candidate can participate |
| Project | The work requiring a team |
| Team | The selected set of candidates |
| Formation Policy | Rules determining whether the team is acceptable |
| Formation Decision | The resulting eligibility state |

## Team Formation Workflow

    Project Definition
           |
           v
    Required Roles + Required Skills
           |
           v
    Eligible Candidate Pool
           |
           v
    Mandatory Role Coverage
           |
           v
    Minimum Team Size
           |
           v
    Skill Gap Reduction
           |
           v
    Maximum Team Size
           |
           v
    Policy Validation
           |
           +---- invalid ----> Rejected
           |
           v
    Validated Team

Role coverage and skill coverage are separate checks. A candidate can satisfy a role without satisfying every skill associated with the project, and a candidate can contribute a skill without filling a required organizational role.

## Selection Rules

The implementations use a constrained scoring approach.

Candidate ranking considers:

- overlap between candidate skills and project skills
- overlap between candidate roles and required roles
- availability
- relevant experience

Mandatory roles receive priority. This prevents a highly skilled candidate pool from producing a technically capable team that lacks an essential responsibility.

After required roles are represented, additional candidates are selected to reach the minimum team size. Optional capacity is used only when a candidate reduces an outstanding skill gap.

Unavailable candidates are excluded from normal selection.

## Python Implementation

The Python implementation models the domain with `dataclass` objects and `Enum` values.

`Candidate` is immutable through a frozen dataclass. Roles and skills are represented as sets, making membership and overlap operations direct.

`Project` contains the required capabilities and team-size boundaries.

`TeamFormationEngine` performs:

1. candidate validation
2. candidate ranking
3. mandatory role assignment
4. minimum-size completion
5. optional skill-coverage improvement
6. final validation

The engine raises `TeamFormationError` when formation is impossible.

The validation result records:

- team-size validity
- missing roles
- missing skills
- duplicate members
- availability distribution

The script also exercises a deliberate failure case involving a project requiring an unavailable capability. Assertions verify important invariants after normal formation.

The implementation uses standard-library functionality only.

### Python Complexity

For `n` candidates, `r` required roles, and `s` relevant skills, the main selection process is approximately `O(nr + n²s)` in the current straightforward implementation. The code favors transparent domain behavior over premature optimization.

## JavaScript Implementation

The JavaScript implementation treats team formation as an event-driven process.

`Candidate` and `Project` are domain classes. JavaScript `Set` objects represent roles and skills, while `EventEmitter` exposes formation events.

Two events are emitted:

- `memberSelected`
- `teamFormed`

The formation operation is asynchronous through `async` and `Promise` scheduling. This creates a natural boundary for replacing the in-memory candidate pool with asynchronous services later without changing the domain event model.

Validation returns structured information containing:

- validity
- errors
- missing roles
- missing skills

The implementation uses modern Node.js functionality and does not require npm packages.

The JavaScript model emphasizes state observation and event-driven behavior rather than reproducing the Python class structure mechanically.

## C++17 Implementation

The C++ implementation treats team formation as a governance-oriented selection engine.

`enum class` provides strongly typed roles and availability states. STL `set`, `vector`, `algorithm`, and associative containers are used for deterministic membership and selection operations.

The engine separates:

- candidate ranking
- role coverage
- skill coverage
- team construction
- validation

The formation algorithm first satisfies mandatory roles, then selects candidates that cover missing skills, and finally evaluates whether optional candidates provide measurable improvement.

C++ exception handling reports invalid policies, duplicate candidates, missing roles, insufficient candidates, and failed validation.

The program uses no external libraries and is directly compilable with C++17.

### C++ Design Trade-Off

Using `std::set` gives predictable ordered behavior and efficient membership operations, while `std::vector` keeps the final team representation compact and easy to traverse.

The implementation deliberately performs explicit validation instead of relying on unchecked assumptions. This is useful when team formation becomes part of a larger governance or allocation service.

## Java 17 Implementation

The Java implementation models team formation as an enterprise policy service.

The domain uses:

- records for immutable value objects
- enums for controlled states
- interfaces for formation policies
- collections for candidate and requirement sets
- streams for filtering and aggregation
- explicit state values for formation decisions
- custom policy objects for independent validation

The `TeamPolicy` interface separates business rules from candidate selection.

Two policies are implemented:

| Policy | Responsibility |
|---|---|
| `MinimumCoveragePolicy` | Checks team size, required roles, and required skills |
| `SecurityPolicy` | Requires a Security Engineer for high-risk projects |

This separation prevents all business rules from being embedded in a single selection method.

The resulting `FormationDecision` records:

- decision state
- selected members
- missing roles
- missing skills
- policy rejection reasons

This creates an explicit distinction between selecting a team and determining whether that team is acceptable.

## PostgreSQL Implementation

The PostgreSQL implementation stores the team-formation domain relationally.

The principal entities are:

- `repositories`
- `candidates`
- `roles`
- `skills`
- `candidate_roles`
- `candidate_skills`
- `projects`
- `project_required_roles`
- `project_required_skills`
- `teams`
- `team_members`
- `formation_decisions`

The many-to-many relationships between candidates and roles, candidates and skills, projects and required roles, and projects and required skills are represented through junction tables.

### Database Integrity

Primary keys identify entities.

Foreign keys enforce relationships.

Unique constraints prevent duplicate candidate codes, role names, skill names, and project codes.

Check constraints enforce:

- non-negative experience
- valid project capacities
- valid skill proficiency
- valid team-size boundaries

PostgreSQL enums constrain controlled lifecycle and availability values.

Indexes are placed on relationship columns used by role, skill, candidate, project, and team-state queries.

## SQL Eligibility Evaluation

The `evaluate_team` function evaluates a team's formation state against its project.

It checks:

1. minimum team size
2. maximum team size
3. required role coverage
4. required skill coverage
5. required skill proficiency

The function returns an `eligible` or `ineligible` decision together with missing counts and human-readable reasons.

This keeps important eligibility logic close to the data that it protects.

## Transactional Workflow

The SQL workflow evaluates a team and persists the formation decision inside a transaction.

The resulting state becomes:

`approved` when the team satisfies the formation rules

or

`rejected` when required conditions remain unsatisfied.

This demonstrates the distinction between:

- storing team membership
- evaluating the team
- recording a decision
- changing the team lifecycle state

## Availability and Capacity

Availability is not treated as a simple preference.

`available` candidates can normally be selected.

`partial` candidates can be selected when the project requires their capability, but their availability remains visible.

`unavailable` candidates are excluded from the normal formation pool.

The database also records `max_projects`, which represents a capacity constraint that can be extended to portfolio-level allocation rules.

## Role Coverage Versus Skill Coverage

Role coverage answers:

`Does the team contain people assigned to the responsibilities required by the project?`

Skill coverage answers:

`Does the team collectively possess the capabilities required to execute the project?`

These checks should not be merged.

For example, a Technical Lead may also have backend skills, but the presence of backend skills does not automatically satisfy a project policy that explicitly requires a dedicated Backend Engineer role.

## Formation Decisions

A team can be technically strong and still be rejected.

Typical rejection conditions include:

- missing mandatory role
- missing required skill
- insufficient team size
- excessive team size
- unavailable candidates
- insufficient security capability
- invalid candidate data

The decision model therefore separates candidate quality from policy compliance.

## Edge Cases

The implementations explicitly handle several failure conditions:

- duplicate candidate identifiers
- invalid team-size limits
- negative experience values
- unavailable candidates
- insufficient candidates
- missing mandatory roles
- missing mandatory skills
- impossible project requirements
- teams exceeding maximum capacity
- security requirements without security expertise

These cases prevent silent formation of teams that appear complete but violate project constraints.

## Security Considerations

Team formation data can contain operationally sensitive information such as employee availability, skills, project assignments, and security responsibilities.

A production implementation should therefore enforce:

- least-privilege database access
- authenticated access to candidate information
- authorization for team assignment changes
- audit records for formation decisions
- controlled exposure of candidate availability
- transaction boundaries around membership changes
- validation at the service and database layers

The PostgreSQL model demonstrates database-level integrity, while the application implementations demonstrate validation before accepting a team.

## Practical Architecture

    Candidate Directory
            |
            v
    Eligibility Filter
            |
            v
    Role Coverage Engine
            |
            v
    Skill Coverage Engine
            |
            v
    Team Capacity Rules
            |
            v
    Policy Evaluation
            |
            v
    Formation Decision
            |
            +------> Rejected
            |
            v
    Validated / Approved Team

This architecture keeps selection, validation, and final decision-making conceptually separate.

## Relationship Between the Five Implementations

| Implementation | Primary Perspective |
|---|---|
| Python | Repository-style domain simulation and constrained team construction |
| JavaScript | Event-driven team formation and asynchronous policy evaluation |
| C++17 | Explicit governance and efficient rule evaluation |
| Java 17 | Enterprise domain modeling and composable policy services |
| PostgreSQL | Relational integrity, eligibility queries, and transactional workflow |

The implementations describe the same project-team problem but use different architectural strengths. None of them depends on a particular web framework or external service.

## Performance Considerations

Candidate selection benefits from set-based membership checks for roles and skills.

For small and medium project teams, the direct in-memory algorithms are sufficient and easy to audit.

For large candidate pools, candidate scoring can be pre-indexed by role and skill so that the system does not repeatedly scan every candidate.

At database scale, indexes on junction-table foreign keys reduce the cost of role and skill coverage queries.

The PostgreSQL function performs relational existence checks rather than loading the entire candidate population into an application process.

## Limitations

The implemented selection strategy is heuristic rather than an optimal workforce-allocation solver.

It prioritizes mandatory role coverage and incremental skill coverage. It does not solve every possible combination of:

- project portfolios
- competing project assignments
- individual preferences
- salary constraints
- geographic restrictions
- time-zone overlap
- interpersonal compatibility
- workload forecasting
- historical delivery performance

Those concerns require additional domain rules and, for large optimization problems, potentially a formal constraint or optimization model.

The current artifacts focus specifically on building a valid project team from a defined candidate pool while maintaining clear role, skill, availability, capacity, and policy boundaries.
