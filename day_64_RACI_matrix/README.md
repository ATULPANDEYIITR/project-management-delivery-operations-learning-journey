# RACI Matrix

## 1. Purpose and scope

A RACI matrix assigns responsibility for activities, deliverables, and decisions within a project or operational process. It makes ownership visible by associating each work item with the roles that perform the work, own its outcome, provide input, or receive updates.

RACI represents four responsibility categories:

| Code | Category | Meaning | Typical involvement |
|---|---|---|---|
| R | Responsible | Performs or coordinates the work required to complete an activity. | Executes tasks and produces deliverables. |
| A | Accountable | Owns the final outcome and answers for completion of the activity. | Makes or accepts the final decision. |
| C | Consulted | Provides information, expertise, or advice before or during the activity. | Participates in two-way communication. |
| I | Informed | Receives relevant progress or outcome information. | Receives one-way communication. |

The distinction between Responsible and Accountable is important. A Responsible role performs the work. An Accountable role owns the result. Multiple roles can contribute as Responsible, but this implementation requires exactly one Accountable role for each work item.

Consulted and Informed are communication relationships. Consulted participants provide input that may influence the work. Informed participants receive information without being required to provide a decision or contribution.

## 2. Matrix structure

A conventional RACI matrix places work items in rows and organizational roles in columns.

The cell at the intersection identifies the responsibility of a role for a work item. A blank cell means that the role has no defined responsibility for that activity.

Example:

| Work item | Project Manager | Cloud Architect | Security Officer | Operations Lead |
|---|---:|---:|---:|---:|
| Inventory | R | C | I | C |
| Architecture approval | A | R | C | C |
| Production migration | A | R | C | R |
| Acceptance testing | A | I | I | C |

The table is a role-to-task relationship model, not a list of individual employee assignments. A role can be associated with a person through a separate organizational directory or project staffing record.

### Matrix invariants

The five implementations use a common set of validation rules:

1. Every work item must have exactly one `A`.
2. Every work item must have at least one `R`.
3. A role has only one responsibility code for a particular work item.
4. A task marked security-sensitive must have the `SECURITY_OFFICER` role assigned `C`.
5. Roles and work items must exist before an assignment can reference them.
6. Published matrices cannot be modified through the supplied application interfaces.

The implementation uses one responsibility code per role-task pair. It does not support combined codes such as `R/A` in one cell. This keeps assignment validation, reporting, and workload calculations unambiguous.

The exact-one-Accountable rule is a governance rule adopted by these implementations. Organizations should define their own RACI conventions before adopting a matrix, especially when they permit shared accountability or combined role codes.

## 3. Roles, work items, and assignments

A **role** describes an organizational function involved in project delivery. Examples include Project Sponsor, Project Manager, Cloud Architect, Security Officer, Quality Lead, and Operations Lead.

A **work item** is an activity or deliverable whose ownership must be explicit. Work items should be expressed at a useful level of detail. A task that is too broad can conceal multiple decisions and responsibilities. A task that is too small can make the matrix difficult to maintain.

An **assignment** connects one role to one work item and gives that relationship a responsibility code.

The relationship can be represented as:

Project
- Roles
- Work items
- Assignments
  - Work item
  - Role
  - Responsibility code

For example, a production migration can have the Project Manager as Accountable, the Cloud Architect and Operations Lead as Responsible, the Security Officer as Consulted, and the Quality Lead as Informed.

The same role can have different responsibility codes across different work items. The Project Manager may be Responsible for project reporting and Accountable for the migration milestone.

## 4. Validation and governance rules

### Accountability validation

Exactly one Accountable assignment establishes a clear owner for each activity. No Accountable assignment leaves the final decision or outcome unclear. Multiple Accountable assignments can create uncertainty about who owns the final result.

The Python, JavaScript, C++17, and Java implementations check this rule before publication. The PostgreSQL implementation enforces at most one Accountable assignment through a partial unique index and checks for exactly one during publication.

### Responsibility validation

At least one Responsible assignment is required for each work item. Accountability without someone performing or coordinating the work is insufficient.

Multiple Responsible roles are permitted. This is useful when work is divided between engineering, operations, testing, and other delivery functions.

### Consultation requirements

Consultation requirements can be defined by organizational policy or by the nature of the work. In the example project, security-sensitive work requires the Security Officer to be Consulted.

This is an example of a policy-based rule rather than a universal RACI requirement. Other projects may require legal, compliance, finance, safety, or privacy consultation for selected activities.

### Workload capacity

A valid matrix can still be impractical when one role is assigned too many Responsible activities. Each implementation can calculate the number of work items for which a role is Responsible.

The example defines a maximum Responsible-task capacity for selected roles. A capacity overrun is reported as a warning rather than a publication failure. The assumption is that workload requires management review but does not automatically invalidate the responsibility structure.

Workload counts do not measure task duration, complexity, skill requirements, or concurrent deadlines. They are indicators for review, not a complete resource-planning model.

## 5. Workflow

The implementations use the following lifecycle:

Draft
  |
  v
Define project roles
  |
  v
Define work items
  |
  v
Assign R, A, C, and I
  |
  v
Validate assignment rules
  |
  v
Review workload warnings
  |
  v
Publish
  |
  v
Active and read-only

A draft matrix can be changed while roles, work items, and assignments are being defined. Validation identifies missing accountability, missing execution ownership, and policy violations.

Publication is a controlled state transition. An invalid matrix cannot become active. Once active, the supplied implementations reject further changes. A real enterprise system would normally support a controlled revision process that creates a new version, records the reason for the change, obtains approval, and preserves the previous published version.

## 6. Implementation details

| Deliverable | Engineering perspective | Main mechanisms |
|---|---|---|
| Python | Domain model and workflow simulation | Dataclasses, enums, dictionaries, validation, workload analysis, serialization, and assertions |
| JavaScript | Event-driven workspace | Maps, Sets, event emission, atomic batch updates, asynchronous audit persistence, and publication handling |
| C++17 | Governance and validation engine | Structs, enums, STL maps, optional capacity limits, policy checks, and controlled state changes |
| Java 17 | Enterprise governance service | Records, immutable policy objects, collections, state transitions, approval policies, and audit entries |
| PostgreSQL | Relational persistence and enforcement | Foreign keys, constraints, partial indexes, views, triggers, validation functions, transactions, and reporting queries |

### Python implementation

The Python script defines `Role` and `WorkItem` as immutable dataclasses. `Responsibility` and `MatrixStatus` are enums, which restrict valid responsibility codes and matrix states.

`RaciMatrix` stores roles and work items in dictionaries. A nested dictionary stores each task's role assignments. This provides direct lookup by task ID and role code.

The `validate()` method checks the matrix without modifying it. It returns a list of blocking errors so that all relevant problems can be displayed together rather than stopping at the first invalid task.

The `workload_warnings()` method calculates Responsible assignments by role. The `publish()` method changes the matrix state only after validation succeeds. The JSON representation provides a structured export for inspection or integration.

The invalid demonstration matrix shows that a security-sensitive task without an Accountable assignment and the required security consultation cannot be published.

Run the file with `python raci_matrix.py`.

### JavaScript implementation

The JavaScript version uses `Map` for role, task, and assignment storage. `Set` is used to define the permitted responsibility codes.

`RaciWorkspace` extends Node.js `EventEmitter`. Assignment changes produce `assignment.changed` events, while successful publication produces a `matrix.published` event. This allows other components to react to matrix changes without being tightly coupled to the assignment methods.

`applyAssignments()` stages a batch in cloned maps. If a task, role, or responsibility code is invalid, it throws an error before replacing the live assignment state. This provides atomic behavior for a batch of assignment changes.

Publication is asynchronous. The audit sink is called and awaited before the matrix status changes to `ACTIVE`. If the audit operation fails, publication does not complete.

Run the file with `node raci_matrix.js`. The implementation uses only Node.js standard-library functionality.

### C++17 implementation

The C++ program models roles and work items with structs and responsibility values with an enum. `RaciEngine` owns the matrix state and prevents changes after publication.

A map keyed by `(task ID, role code)` stores one responsibility value for each role-task pair. The ordered map supports predictable reporting and direct assignment lookup.

Validation iterates through the work items and their roles to count Responsible and Accountable assignments. Workload analysis counts Responsible assignments and compares them with optional role capacities.

The program uses standard-library containers and does not require external dependencies. Map-based lookup and ordered traversal make the implementation straightforward to inspect. For very large matrices, a different indexing strategy or a database-backed model may be more appropriate.

Compile with a C++17 compiler, for example: `g++ -std=c++17 -O2 -Wall -Wextra -pedantic raci_matrix.cpp -o raci_matrix`.

Run with `./raci_matrix` on Linux or the equivalent executable on Windows.

### Java 17 implementation

The Java implementation models the domain using records for roles, work items, matrix policies, approval policies, and audit entries. Records provide immutable data objects with generated accessors.

`RaciMatrix` controls its internal collections and exposes operations rather than direct access to mutable assignment data. Matrix state moves through `DRAFT`, `IN_REVIEW`, `APPROVED`, and `ACTIVE`.

The `MatrixPolicy` object contains responsibility validation rules. The separate `ApprovalPolicy` defines eligible matrix reviewers, the number of approvals required, and whether the author can approve their own submission.

Matrix approval is distinct from RACI accountability. An Accountable role owns a work item's outcome. A matrix reviewer authorizes the governance document to progress through its publication lifecycle. These are separate decisions.

The example requires two eligible governance approvals. The author is not permitted to approve their own submission, and duplicate approvals are rejected. Publication is allowed only after the matrix reaches `APPROVED`.

Compile with `javac RaciGovernance.java` and run with `java RaciGovernance`.

## 7. PostgreSQL data model

The SQL script creates a dedicated `raci` schema. Its relational model separates projects, project roles, work items, assignments, and audit records.

| Table | Purpose |
|---|---|
| `projects` | Stores project identity and publication status. |
| `project_roles` | Defines roles participating in a project and their optional workload limits. |
| `work_items` | Stores project activities and security-sensitive indicators. |
| `raci_assignments` | Connects a task and a role to one responsibility code. |
| `assignment_audit` | Records assignment insertions, updates, and deletions. |

### Referential integrity

Foreign keys ensure that assignments refer to roles and work items belonging to the same project. The unique constraint on `(project_id, task_id, role_id)` prevents a role from receiving multiple responsibility records for the same task.

The responsibility column uses a PostgreSQL enum, restricting values to `R`, `A`, `C`, and `I`.

The partial unique index `uq_one_accountable_per_task` prevents two Accountable assignments for a task. This index enforces the upper bound immediately. The publication function enforces the lower bound by rejecting tasks with no Accountable assignment.

### Views and reporting

`v_matrix_validation` calculates the number of Accountable, Responsible, and security consultation assignments for each work item. It exposes an `is_valid` result for publication and reporting.

`v_task_matrix` produces a readable list of role-to-responsibility assignments for each task.

`v_role_workload` aggregates the number of Responsible work items assigned to each role and identifies capacity overruns.

These views centralize reporting logic so that validation and reporting queries use consistent definitions.

### Triggers and publication

The assignment trigger rejects modifications to active projects. It takes a shared lock on the associated project row, while the publication function obtains an exclusive row lock. This coordinates publication with concurrent assignment changes.

The work-item trigger applies the same read-only rule to published project activities.

The audit trigger records assignment changes with the old and new row values in JSONB format. This supports investigation of changes without requiring the current assignment record to preserve its previous values.

`publish_matrix(project_id)` checks that the project exists, is still in `DRAFT`, contains at least one work item, and has no invalid tasks. It reports role capacity overruns as warnings and changes the project to `ACTIVE` only after the blocking checks pass.

The script includes one valid cloud migration project and one intentionally incomplete payment security project. The latter demonstrates a task that has Responsible and Accountable assignments but fails the security consultation requirement.

Run the SQL script using `psql` or another PostgreSQL client with permission to create the schema and database objects.

## 8. Performance and security considerations

The relational design uses indexes for project-task retrieval, role workload aggregation, and assignment lookup. The partial unique index provides both an integrity rule and an efficient lookup structure for Accountable assignments.

The programming-language implementations use direct in-memory lookup structures. Their validation cost grows with the number of task-role assignment relationships. A matrix with T tasks and R roles can require up to O(T × R) checks when every task is evaluated against every role. Workload aggregation is proportional to the number of stored assignments.

Role and task identifiers should be validated at application boundaries. A production implementation should authenticate users, authorize assignment changes, record the identity of each actor, and protect audit data from unauthorized modification.

The database triggers prevent ordinary assignment changes after publication. Database owners and sufficiently privileged administrators may still alter objects or bypass application-level controls. Production governance therefore requires restricted database privileges, controlled administrative access, backups, and independently protected audit records.

The JavaScript audit sink is an injectable function. The demonstration uses an in-memory collection; a production deployment should persist audit events to a durable store and define retry, failure, and retention policies.

## 9. Edge cases and limitations

The implementations explicitly handle:

- Tasks with no Accountable assignment.
- Tasks with multiple Accountable assignments.
- Tasks with no Responsible assignment.
- Security-sensitive work without the required Security Officer consultation.
- Duplicate role or task identifiers.
- Assignments that reference unknown roles or tasks.
- Attempts to modify an active matrix.
- Workload limits exceeded by Responsible assignments.
- Ineligible, duplicate, or self-approvals in the Java governance lifecycle.
- Failed audit persistence before JavaScript publication.
- Invalid assignment batches in the JavaScript workspace.
- Concurrent assignment and publication operations in the PostgreSQL model.

A RACI matrix does not establish project dependencies, estimate effort, allocate financial resources, measure performance, or replace a detailed project schedule. It also does not define the authority of a role outside the work items represented in the matrix.

The examples use role codes rather than employee identities. Employee assignment, organizational hierarchy, delegation, absence coverage, and role succession require additional data structures and governance rules.

Workload counts are basic indicators. A role responsible for four small tasks may have a lower workload than a role responsible for one complex migration. Capacity planning should consider task duration, concurrency, dependencies, skills, and deadlines.

The JavaScript and C++ implementations use in-memory state. The Python implementation serializes state to JSON but does not provide a persistent repository. PostgreSQL provides relational persistence and database-enforced restrictions, while the Java implementation demonstrates a separate approval lifecycle. These are complementary implementation perspectives rather than interchangeable production systems.
