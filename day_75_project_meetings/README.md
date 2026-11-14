# Project Meeting Management

## Project Overview

Project Meeting Management is a structured system for planning, conducting, documenting, and monitoring project meetings.

The system treats a meeting as an operational process rather than an isolated calendar event. Its lifecycle connects scheduling, participant coordination, agenda management, attendance, decision recording, action assignment, meeting minutes, and follow-up reporting.

The five implementations use different engineering approaches while maintaining a consistent business domain.

The central operational objective is to establish traceability between:

- The purpose of a meeting.
- The people responsible for its proceedings.
- The subjects discussed.
- The decisions reached.
- The tasks assigned.
- The deadlines and evidence associated with those tasks.
- The resulting project progress.

## 1. Project Meeting Management Fundamentals

### 1.1 Definition

Project meeting management is the systematic coordination of meetings conducted to plan, monitor, review, control, and complete project activities.

A properly managed meeting should have:

- A defined purpose.
- An accountable organizer.
- A scheduled date and duration.
- Identified participants.
- A documented agenda.
- Recorded attendance.
- Traceable decisions.
- Assigned action items.
- A formal record of proceedings.
- A mechanism for monitoring outstanding work.

Meetings should produce operational outcomes that can be reviewed after the discussion.

### 1.2 Types of project meetings

| Meeting type | Primary purpose | Typical output |
|---|---|---|
| Project kickoff | Establish objectives and responsibilities | Project charter alignment |
| Planning meeting | Organize upcoming work | Work plan and assignments |
| Daily stand-up | Review immediate progress | Blockers and short-term commitments |
| Project review | Evaluate delivery performance | Progress and corrective actions |
| Risk review | Identify and assess project risks | Mitigation assignments |
| Retrospective | Evaluate completed work | Process improvements |
| Steering committee | Resolve strategic project matters | Governance decisions |

Each meeting type has a different operational purpose. The meeting classification can influence its agenda, participants, duration, and reporting requirements.

## 2. Meeting Lifecycle

A meeting follows a controlled sequence of states.

### 2.1 Lifecycle stages

| Stage | Description | Important controls |
|---|---|---|
| Preparation | Define purpose and expected outcomes | Scope and ownership |
| Scheduling | Establish time and location | Availability and conflicts |
| Invitation | Notify participants | Valid participant records |
| Agenda preparation | Arrange discussion subjects | Owners and time allocation |
| Commencement | Begin proceedings | Valid lifecycle transition |
| Discussion | Process agenda items | Notes and progress |
| Decision recording | Capture agreed outcomes | Responsible decision-maker |
| Action assignment | Allocate follow-up work | Assignee and deadline |
| Closure | Finalize proceedings | Minutes and closure validation |
| Follow-up | Monitor commitments | Status and overdue reporting |

### 2.2 Meeting state transitions

The implementations use four primary meeting states:

| State | Meaning |
|---|---|
| `scheduled` | Meeting is planned but has not started |
| `in_progress` | Meeting proceedings are active |
| `completed` | Meeting has been formally closed |
| `cancelled` | Meeting will not proceed |

The normal lifecycle is:

`Scheduled → In Progress → Completed`

An alternative transition is:

`Scheduled → Cancelled`

An active meeting may also be cancelled when the business rules permit it.

Completed and cancelled meetings are terminal states in these implementations.

This prevents accidental reopening or modification of finalized meeting records.

### 2.3 Scheduling conflicts

Scheduling validation is based on time intervals.

For two meetings belonging to the same organizer, an overlap exists when:

`New Start < Existing End`

and

`Existing Start < New End`

The interval comparison correctly handles:

- Meetings that begin at the same time.
- Meetings that partially overlap.
- Meetings completely contained within another meeting.
- Meetings with consecutive schedules.

Meetings ending exactly when another begins are not considered overlapping.

The Python, JavaScript, C++17, and Java implementations check organizer conflicts before accepting a new meeting.

A production scheduling service should extend this check to other constrained resources, including rooms, equipment, and mandatory participants.

## 3. Participants and Attendance

### 3.1 Participant responsibilities

Participants are associated with specific meeting responsibilities.

| Role | Responsibility |
|---|---|
| Organizer | Arranges and coordinates the meeting |
| Chairperson | Directs proceedings and manages discussion |
| Member | Contributes to the discussion and assigned work |
| Observer | Attends for information or oversight |

The organizer is required to be a registered meeting participant.

Participant information includes an identifier, name, email address, and role.

Email validation prevents obviously invalid contact information from entering the application.

### 3.2 Invitation and attendance are different

An invitation records whether a participant has accepted, declined, or tentatively accepted an invitation.

Attendance records what actually happened during the meeting.

These are separate operational facts.

For example, an accepted invitation does not establish that the participant attended.

The PostgreSQL implementation maintains separate fields for:

- `invitation_status`
- `attendance_status`
- `joined_at`

This allows attendance reporting without treating invitation responses as evidence of attendance.

### 3.3 Attendance measurement

Attendance percentage is calculated as:

`Attendance Percentage = Attended Participants / Invited Participants × 100`

Present and late participants are included in the attended count.

A missing attendance record should not automatically be interpreted as absence.

The database report protects against division by zero using `NULLIF`.

## 4. Agenda Management

An agenda is the structured list of subjects to be discussed.

Each agenda item contains:

- Unique identifier.
- Meeting association.
- Sequence number.
- Discussion title.
- Description.
- Responsible owner.
- Planned duration.
- Priority.
- Discussion status.
- Discussion notes.

### 4.1 Agenda sequencing

The sequence number determines the intended discussion order.

For example:

| Sequence | Agenda item | Owner | Duration |
|---:|---|---|---:|
| 1 | Project objectives | Project Manager | 20 minutes |
| 2 | Technical architecture | Technical Lead | 30 minutes |
| 3 | Business requirements | Business Analyst | 20 minutes |

The planned agenda duration can be compared with the overall meeting duration.

The database enforces uniqueness of the sequence number within each meeting.

### 4.2 Agenda states

| State | Meaning |
|---|---|
| `pending` | Discussion has not started |
| `in_progress` | Discussion is active |
| `completed` | Discussion has concluded |
| `deferred` | Discussion has been postponed |

An agenda item being completed does not necessarily mean its associated project work is completed.

It only indicates that the discussion has concluded.

This distinction is important when a discussion creates follow-up actions.

## 5. Decision Management

A decision is a recorded outcome reached during a meeting.

Decisions should be distinguishable from discussion notes and action assignments.

A decision record contains:

- Decision identifier.
- Meeting identifier.
- Decision sequence.
- Description.
- Rationale.
- Recording participant.
- Decision status.
- Recording timestamp.

### 5.1 Decision states

| State | Meaning |
|---|---|
| `approved` | Decision has been accepted |
| `rejected` | Proposed decision was not accepted |
| `deferred` | Decision has been postponed |
| `under_review` | Further examination is required |

A decision should identify who recorded it and why it was reached.

The rationale helps subsequent reviewers understand the basis of the decision.

A decision and an action item are not interchangeable.

For example:

- Decision: Approve the revised project schedule.
- Action: Update the project schedule document.
- Owner: Project Manager.
- Deadline: Specified completion date.

The decision records what was agreed. The action item records the work required to implement that agreement.

## 6. Action Item Management

An action item represents an assigned piece of work resulting from a meeting.

Every action item should contain:

- Unique action identifier.
- Description.
- Responsible participant.
- Assigning participant.
- Priority.
- Due date.
- Current status.
- Completion evidence.
- Completion timestamp, when applicable.

### 6.1 Action lifecycle

The implementations support the following states:

| State | Meaning |
|---|---|
| `open` | Work has been assigned |
| `in_progress` | Work has started |
| `blocked` | Work cannot proceed because of an identified obstacle |
| `completed` | Work has been completed |
| `cancelled` | Work has been withdrawn |

A completed action requires completion evidence.

A blocked action requires a documented reason.

A completed action cannot be reopened in the supplied implementations.

This is a deliberate integrity rule that protects the reliability of completion reporting.

### 6.2 Priority management

| Priority | Operational interpretation |
|---|---|
| Low | Routine follow-up |
| Medium | Normal project commitment |
| High | Important delivery requirement |
| Critical | Urgent project dependency or major operational concern |

Priority and status represent different information.

An action may be critical and open, high priority and blocked, or medium priority and completed.

Priority does not automatically determine completion status.

### 6.3 Overdue action calculation

An action is overdue when:

- Its due date is earlier than the current time.
- Its status is not completed.
- Its status is not cancelled.

The implementations use this rule for operational reporting.

A production implementation should also retain the history of deadline changes and reassignment events.

## 7. Meeting Minutes and Documentation

Meeting minutes provide a formal record of the proceedings.

They should capture:

- Meeting identification.
- Date and location.
- Participants and attendance.
- Agenda items discussed.
- Important discussion outcomes.
- Decisions.
- Assigned responsibilities.
- Deadlines.
- Outstanding issues.

Meeting minutes are not a verbatim transcript.

Their primary purpose is to preserve relevant information and provide a reliable record of agreed outcomes.

The Python, JavaScript, C++17, and Java implementations require non-empty minutes before a meeting can be completed.

The PostgreSQL implementation enforces the same closure requirement through a database trigger.

The relational model also includes `meeting_documents` for associating agendas, minutes, presentations, reports, and attachments with meetings.

## 8. Follow-up and Performance Reporting

The meeting process continues after the formal discussion ends.

Follow-up activities ensure that decisions are translated into completed project work.

### 8.1 Operational indicators

| Indicator | Calculation or interpretation |
|---|---|
| Total meetings | Number of recorded meetings |
| Completed meetings | Meetings formally closed |
| Cancelled meetings | Meetings withdrawn |
| Attendance percentage | Attended participants divided by invited participants |
| Decisions recorded | Number of documented decisions |
| Total actions | Number of assigned action items |
| Completed actions | Actions with completed status |
| Overdue actions | Outstanding actions past their deadlines |
| Action completion percentage | Completed actions divided by total actions |

These indicators provide information about meeting execution and follow-up performance.

Meeting count alone is not a reliable measure of project progress.

Decision quality, action ownership, completion rates, and overdue commitments provide additional operational information.

### 8.2 Project-level reporting

The implementations provide project-based reporting.

A project report groups meetings and their associated actions by project.

This allows managers to evaluate:

- Meeting execution.
- Decisions recorded.
- Work assigned.
- Outstanding commitments.
- Completed work.
- Overdue responsibilities.

The PostgreSQL implementation uses `project_meeting_performance` and `action_tracking` views for reusable reporting.

## 9. Python Implementation

**File type:** Standalone Python script.

### 9.1 Architecture

The Python implementation uses dataclasses and enumerations to represent the meeting domain.

| Component | Responsibility |
|---|---|
| `Participant` | Stores participant identity and role |
| `AgendaItem` | Represents an agenda subject |
| `Decision` | Records meeting decisions |
| `ActionItem` | Tracks assigned work |
| `Meeting` | Controls the meeting lifecycle |
| `MeetingManager` | Coordinates meetings and reporting |

### 9.2 Important mechanisms

**Dataclasses**

Dataclasses provide structured records with automatically generated initialization and representation methods.

**Enumerations**

Enums prevent arbitrary values from being used for meeting states, action states, priorities, and participant roles.

**Dictionaries**

The meeting manager uses dictionaries for identifier-based meeting and participant lookup.

Average dictionary lookup is approximately O(1).

**Lists**

Agenda items, decisions, and action items retain their ordered collection structure.

**Exceptions**

Custom exceptions distinguish validation errors, missing resources, and invalid state transitions.

**JSON export**

The export mechanism converts domain objects into serializable dictionaries.

A temporary file is written before replacement of the destination file, reducing the possibility of exposing a partially written report.

### 9.3 Demonstrated workflow

The demonstration creates a project review meeting, adds participants and agenda items, records attendance, starts the meeting, records a decision, assigns an action, updates its status, closes the meeting, and generates a project report.

The script also tests duplicate scheduling and invalid state transitions.

## 10. JavaScript Implementation

**File type:** Standalone Node.js JavaScript file.

### 10.1 Event-driven architecture

The JavaScript implementation uses `EventEmitter` to publish meeting lifecycle events.

Examples include:

| Event | Meaning |
|---|---|
| `meeting.scheduled` | A meeting was accepted |
| `meeting.started` | Proceedings began |
| `agenda.added` | An agenda item was registered |
| `decision.recorded` | A decision was stored |
| `action.created` | An action was assigned |
| `action.updated` | An action status changed |
| `meeting.completed` | The meeting was closed |

The service subscribes to meeting changes and maintains an event history.

This separates domain operations from event consumers.

### 10.2 Maps and Sets

The implementation uses:

- `Map` for participant and meeting lookup.
- `Set` for attendance tracking.
- Arrays for agenda items, decisions, and actions.

These structures provide efficient lookup and prevent duplicate attendance entries.

### 10.3 Policy evaluation

`MeetingPolicy` evaluates:

- Maximum meeting duration.
- Maximum participant count.
- Minimum agenda requirements.
- Mandatory meeting minutes.

The meeting cannot start if its policy requirements are violated.

### 10.4 Asynchronous file operations

The `exportJSON` method uses Node.js asynchronous file handling.

It writes a temporary file and renames it after successful completion.

The operation includes error handling and temporary-file cleanup.

The event-driven design can be extended to notification delivery, calendar integration, and external project-management systems.

## 11. C++17 Implementation

**File type:** Standalone C++17 program.

### 11.1 Domain-oriented design

The C++ implementation uses structures and classes to represent the meeting domain.

| Component | Responsibility |
|---|---|
| `Participant` | Participant data |
| `AgendaItem` | Discussion subject |
| `Decision` | Recorded decision |
| `ActionItem` | Follow-up work |
| `Meeting` | Meeting state and operations |
| `RepositoryGovernance` | Central meeting coordination |

### 11.2 STL data structures

The implementation uses:

- `std::map` for identifier-based records.
- `std::vector` for ordered agenda, decisions, and actions.
- `std::find_if` for record searches.
- `std::sort` for upcoming meeting ordering.
- `std::time_t` for scheduling and deadlines.

A map offers logarithmic lookup, insertion, and deletion.

Vector-based searches are linear in the number of records.

This design is suitable for a compact standalone management engine.

For a large multi-user application, indexed persistent storage would be preferable.

### 11.3 Exception handling

The custom `MeetingException` class provides a common error mechanism.

Invalid scheduling, unknown participants, duplicate identifiers, invalid transitions, and missing completion evidence are rejected.

### 11.4 State management

The `Meeting` class owns its lifecycle and validates operations before modifying its internal state.

The manager coordinates scheduling and reporting without duplicating the meeting's business rules.

## 12. Java 17 Implementation

**File type:** Standalone Java 17 application.

### 12.1 Enterprise domain architecture

The Java implementation uses a layered domain design.

| Component | Responsibility |
|---|---|
| `Participant` record | Immutable participant identity |
| `AgendaItem` record | Structured agenda definition |
| `Decision` record | Immutable decision record |
| `ActionItem` record | Immutable action representation |
| `MeetingPolicy` | Business rule evaluation |
| `Meeting` | Lifecycle and domain operations |
| `MeetingManagementService` | Scheduling and reporting |
| `ProjectReport` | Immutable reporting result |

### 12.2 Java records

Records provide concise immutable data structures.

The implementation uses records for participants, agenda items, decisions, action items, and project reports.

The `ActionItem.update()` method creates a new action record instead of modifying the existing record.

### 12.3 Collections and streams

The application uses:

- `HashMap` for identifier-based lookup.
- `ArrayList` for ordered records.
- `HashSet` for attendance tracking.
- Stream operations for reporting and filtering.
- `List.copyOf()` for immutable collection snapshots.

The `upcoming()` method filters and sorts scheduled meetings.

The `overdueActions()` method identifies outstanding actions whose deadlines have passed.

### 12.4 Enterprise policy separation

The `MeetingPolicy` class separates organizational rules from meeting operations.

A policy can enforce:

- Maximum meeting duration.
- Maximum participant count.
- Minimum agenda requirements.
- Mandatory meeting minutes.

This approach allows different meeting categories to use different policies without embedding all policy rules into the service class.

## 13. PostgreSQL Implementation

**File type:** Executable PostgreSQL SQL script.

### 13.1 Relational architecture

The database separates project, meeting, participant, and follow-up information.

| Table | Purpose |
|---|---|
| `projects` | Project master records |
| `participants` | Participant master records |
| `meetings` | Meeting schedules and lifecycle |
| `meeting_participants` | Participant membership and attendance |
| `agenda_items` | Meeting agenda |
| `decisions` | Recorded decisions |
| `action_items` | Assigned follow-up work |
| `meeting_documents` | Meeting-related documents |
| `meeting_policies` | Meeting governance rules |
| `meeting_audit` | Operational audit events |

### 13.2 Referential integrity

Primary keys uniquely identify records.

Foreign keys preserve relationships between projects, meetings, participants, decisions, and actions.

The composite foreign keys in `agenda_items`, `decisions`, and `action_items` ensure that the associated owner or recorder belongs to the relevant meeting.

This prevents assigning meeting responsibilities to unrelated participants.

### 13.3 Constraints

The schema uses:

- `PRIMARY KEY` for record identity.
- `FOREIGN KEY` for relationship integrity.
- `UNIQUE` for meeting codes and participant emails.
- `CHECK` for permitted statuses and valid durations.
- `NOT NULL` for mandatory attributes.

The action completion constraint requires a completion timestamp and completion notes.

A blocked action requires a blocker description.

### 13.4 Triggers

The database contains several business-integrity triggers.

**Timestamp triggers**

Automatically update the modification timestamp when meetings and actions change.

**Participant validation**

Prevents inactive participants from joining a meeting and prevents new participants from being added after proceedings start.

**Meeting lifecycle validation**

Prevents invalid transitions and requires agenda items before commencement.

**Action transition validation**

Prevents completed actions from being reopened and enforces completion evidence.

**Audit trigger**

Records meeting creation and changes in meeting state.

Database-level enforcement is important because applications are not the only possible source of database modifications.

### 13.5 Functions and procedures

`evaluate_meeting()` evaluates a meeting against a selected policy and returns:

- Eligibility.
- Agenda count.
- Participant count.
- Policy violations.

`start_meeting()` applies the evaluation before changing the meeting state.

`complete_action()` validates completion evidence and updates the action.

These operations provide reusable database-level business rules.

### 13.6 Views

`meeting_overview` combines project and meeting information with participant, agenda, decision, and action counts.

`action_tracking` provides assignment and deadline information.

`project_meeting_performance` provides project-level meeting and action indicators.

The views separate commonly used reporting logic from individual application queries.

### 13.7 Transactions

The demonstration uses transactions when starting a meeting and completing an action.

A transaction groups related operations into a single unit of work.

If an operation fails before commit, the transaction can be rolled back.

This prevents partially applied workflow changes.

### 13.8 Query patterns

The SQL implementation demonstrates:

- Filtering scheduled meetings.
- Retrieving participants and attendance.
- Evaluating meeting eligibility.
- Identifying overdue actions.
- Grouping action assignments by participant.
- Calculating attendance percentages.
- Reporting decision records.
- Aggregating project performance.
- Using CTEs for multi-stage project analysis.

## 14. Relationship Between the Five Implementations

All implementations follow the same fundamental business sequence.

`Project → Meeting → Participants → Agenda → Discussion → Decisions → Actions → Minutes → Follow-up`

Their engineering approaches differ.

| Engineering concern | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Primary approach | Domain simulation | Event-driven service | Governance engine | Enterprise domain model | Relational workflow |
| State representation | Enums | Frozen constants | Enums | Enums | CHECK constraints |
| Record structures | Dataclasses | Objects | Structs | Records | Tables |
| Collection management | Dict and list | Map and Set | Map and vector | Map, List and Set | Relational indexes |
| Validation | Exceptions | Policy objects | Domain validation | Policy service | Constraints and triggers |
| Reporting | Dictionaries | Objects | Aggregation | Records and streams | Views and CTEs |
| Persistence | JSON export | JSON export | In-memory | In-memory | Relational tables |

The implementations are independent demonstrations rather than components of one distributed application.

Their identifier formats and storage mechanisms are not intended to be interchangeable without an integration layer.

## 15. Validation, Failure Handling, and Security

### 15.1 Validation requirements

The system validates:

- Mandatory meeting information.
- Valid participant identifiers.
- Email format.
- Positive meeting duration.
- Valid agenda duration.
- Valid action deadlines.
- Meeting lifecycle transitions.
- Organizer scheduling conflicts.
- Action ownership.
- Completion evidence.
- Required meeting minutes.

### 15.2 Failure scenarios

| Failure | Expected handling |
|---|---|
| Duplicate meeting identifier | Reject registration |
| Invalid participant email | Reject participant |
| Organizer scheduling conflict | Reject schedule |
| Missing agenda | Prevent commencement |
| Unknown participant | Reject attendance or assignment |
| Invalid meeting state | Reject transition |
| Missing completion evidence | Reject action completion |
| Missing meeting minutes | Reject closure |
| Missing action record | Return a not-found error |
| File export failure | Report error and clean temporary file |

### 15.3 Security considerations

A production meeting-management system should implement:

- Authentication for all users.
- Role-based access control.
- Authorization checks for meeting modification.
- Restrictions on decision and minutes editing.
- Encryption for sensitive meeting records.
- Secure storage for attachments.
- Input validation and output encoding.
- Audit logging for important changes.
- Retention and deletion policies.
- Protected database credentials.
- Backup and recovery procedures.

Meeting access should be restricted according to project membership and organizational responsibilities.

The demonstration programs validate business operations but do not implement authentication, authorization, encryption, or a production identity-management service.

The PostgreSQL audit trigger records meeting changes, but a production audit system should also capture actor identity through a trusted authenticated database session rather than relying on client-supplied values.

## 16. Performance and Scalability

### 16.1 Computational complexity

| Operation | Typical complexity |
|---|---|
| Python dictionary lookup | O(1) average |
| JavaScript Map lookup | O(1) average |
| C++ ordered map lookup | O(log n) |
| Java HashMap lookup | O(1) average |
| Agenda search using a linear collection | O(n) |
| Sorting upcoming meetings | O(n log n) |
| Project report aggregation | O(n + a) |
| Indexed database lookup | Depends on index structure and selectivity |

Here, `n` represents the number of meetings and `a` represents the number of action records examined.

### 16.2 Database optimization

The PostgreSQL implementation creates indexes on:

- Project and meeting schedule.
- Meeting status and schedule.
- Participant-to-meeting relationships.
- Agenda ordering.
- Decision timestamps.
- Action assignee, status, and due date.
- Audit history.

The partial index on outstanding actions focuses on records that may require operational attention.

For large installations, reporting workloads should be measured with actual execution plans and realistic data volumes.

### 16.3 Concurrency

The supplied examples are primarily single-process demonstrations.

A production environment must handle simultaneous operations, such as:

- Two users changing the same meeting.
- Concurrent participant registration.
- Multiple users updating one action.
- Simultaneous meeting commencement.
- Conflicting room reservations.

Database transactions, row-level locking, optimistic version checks, and appropriate transaction isolation can address these issues.

The JavaScript and Python in-memory models do not provide distributed concurrency control.

## 17. Practical Operational Workflow

A project manager can use the implemented model as the basis for the following operational procedure.

| Activity | Responsible role | Required record |
|---|---|---|
| Define meeting objective | Organizer | Meeting record |
| Schedule meeting | Organizer | Date and location |
| Invite participants | Organizer | Participant records |
| Prepare agenda | Organizer and owners | Agenda items |
| Confirm attendance | Meeting coordinator | Attendance records |
| Conduct proceedings | Chairperson | Discussion notes |
| Record decisions | Authorized participant | Decision records |
| Assign follow-up work | Organizer or chairperson | Action records |
| Finalize proceedings | Organizer | Meeting minutes |
| Monitor outstanding work | Project manager | Action tracking report |
| Review performance | Project manager | Project report |

The effectiveness of the process depends on accurate records, clear responsibility, realistic deadlines, and timely follow-up.

## 18. Implementation Limitations

The implementations intentionally focus on the core meeting-management workflow.

They do not provide:

- A graphical user interface.
- External calendar synchronization.
- Automated email delivery.
- Real-time video conferencing.
- Multi-tenant identity management.
- Distributed event processing.
- File storage infrastructure.
- Advanced recurring-meeting rules.
- Automated room and equipment allocation.
- Full document version control.

The Python and JavaScript implementations export JSON snapshots rather than maintaining persistent transactional databases.

The C++17 and Java 17 implementations maintain their data in memory.

PostgreSQL provides the persistent relational model and database-level integrity controls.

The sample database uses identity values for illustrative records. A production migration should use controlled sequence management, database roles, schema permissions, and backup policies.

## 19. Execution Requirements

| Implementation | Runtime | External dependencies |
|---|---|---|
| Python | Python 3.10 or later | None |
| JavaScript | Node.js 18 or later | None |
| C++17 | C++17-compatible compiler | None |
| Java | Java 17 | None |
| PostgreSQL | PostgreSQL 14 or later | PostgreSQL server |

### Python

Save the first source file as `project_meeting_management.py`.

Run it using Python. The program generates `meeting_data.json`.

### JavaScript

Save the second source file as `project-meeting-management.js`.

Run it using Node.js. The program generates `meeting_report.json`.

### C++17

Save the third source file as `project_meeting_management.cpp`.

Compile using a C++17-compatible compiler and execute the resulting program.

### Java 17

Save the fourth source file as `ProjectMeetingManagement.java`.

Compile and execute using Java 17.

### PostgreSQL

Save the fifth source file as `project_meeting_management.sql`.

Execute it against a PostgreSQL database with permission to create schemas, tables, functions, procedures, and triggers.

The SQL script creates the `project_meetings` schema and its associated objects.

The demonstration data is inserted using conflict-aware statements so that repeated execution does not duplicate the supplied records.

The sample script is intended for a controlled development database. It should not be executed against an existing production schema without reviewing its effects.

## 20. Technical Learning Outcomes

The project demonstrates the relationship between meeting administration and structured software engineering.

Its principal technical concepts are:

- Lifecycle-based process management.
- Scheduling and interval conflict detection.
- Domain modeling.
- Participant and attendance management.
- Agenda sequencing.
- Decision traceability.
- Action ownership and deadline monitoring.
- Policy-driven validation.
- Immutable records and state transitions.
- Event-driven programming.
- Relational database integrity.
- Transaction management.
- Audit logging.
- Operational reporting.
- Performance-oriented data structures.
- Failure handling and security controls.

The central distinction is between recording that a meeting occurred and managing the work produced by that meeting.

A complete meeting-management process must preserve both the record of the discussion and the traceable execution of its decisions.
