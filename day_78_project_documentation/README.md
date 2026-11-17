# Project Documentation Management System

## 1. Project Overview

Project documentation management is the process of creating, organizing, maintaining, reviewing, approving, distributing, and preserving documents throughout a project's lifecycle.

A project produces several types of documents. These documents record requirements, responsibilities, decisions, technical designs, progress, risks, test results, and final outcomes.

Without controlled documentation, project teams can experience:

- Conflicting document versions.
- Missing project decisions.
- Unclear ownership.
- Unauthorized modifications.
- Delayed reviews and approvals.
- Inconsistent project information.
- Loss of historical records.
- Inadequate audit evidence.
- Difficulty identifying the latest approved document.

The system implemented in these five source files models a centralized document management workflow.

Its principal objectives are:

1. Maintain structured project documents.
2. Preserve document version history.
3. Control document ownership and access.
4. Support review and approval workflows.
5. Track document changes.
6. Verify document integrity.
7. Support document searching and retrieval.
8. Maintain historical audit records.
9. Generate project documentation reports.
10. Manage document retention and archiving.

## 2. Project Documentation Fundamentals

### 2.1 What Is Project Documentation?

Project documentation is the organized collection of records created and maintained to plan, execute, monitor, control, and close a project.

A document can contain information about a particular project activity, decision, deliverable, requirement, or technical component.

Documentation serves several purposes:

| Purpose | Description |
|---|---|
| Planning | Records objectives, schedules, resources, and responsibilities |
| Requirements | Defines expected project outcomes |
| Communication | Maintains a shared understanding among stakeholders |
| Execution | Provides instructions and technical specifications |
| Monitoring | Records progress, issues, and project performance |
| Governance | Documents decisions, approvals, and responsibilities |
| Compliance | Maintains evidence of required processes |
| Knowledge preservation | Retains information for future reference |
| Closure | Records completed deliverables and final decisions |

Documentation is not limited to writing files. It also involves managing their ownership, lifecycle, access, accuracy, and history.

### 2.2 Types of Project Documents

The system implements ten document categories.

| Document category | Purpose |
|---|---|
| Requirements | Records functional and non-functional requirements |
| Project plan | Defines project activities, resources, schedules, and responsibilities |
| Technical specification | Describes technical requirements and system behavior |
| Design | Records architecture, components, and design decisions |
| Meeting minutes | Preserves meeting discussions and decisions |
| Progress report | Records project status and completed work |
| Risk register | Maintains identified risks and their treatment |
| Test report | Records testing activities and results |
| User guide | Explains how users operate a deliverable |
| Closure report | Records final project outcomes and closure activities |

These document categories are represented using enumerations in Python, JavaScript, C++17, and Java 17, and an enumerated PostgreSQL data type.

The classification makes document retrieval, reporting, and governance easier.

## 3. Document Management Lifecycle

A document passes through several operational stages.

### 3.1 Document Creation

Document creation establishes a new record in the project documentation system.

Each document receives:

- A unique document identifier.
- A project identifier.
- A title.
- A document category.
- An owner.
- Initial content.
- An initial version number.
- A creation timestamp.
- Optional tags.

The initial version is version 1.

The document is created in the Draft state.

### 3.2 Document Organization

Documents are associated with projects and classified using document types and tags.

For example:

| Document | Type | Tags |
|---|---|---|
| System Requirements | Requirements | Security, Functional |
| Architecture Specification | Technical specification | Architecture, Design |
| Project Status | Progress report | Monitoring, Reporting |
| Risk Register | Risk register | Risks, Mitigation |

Tags provide an additional classification mechanism.

Document type identifies the formal category. Tags provide more flexible descriptive information.

### 3.3 Document Review

Review evaluates the correctness, completeness, consistency, and suitability of a document.

A review can identify:

- Missing requirements.
- Technical errors.
- Inconsistent statements.
- Incorrect assumptions.
- Incomplete sections.
- Security concerns.
- Unclear responsibilities.
- Missing supporting information.

The reviewer records a decision and comments against a particular document version.

### 3.4 Document Approval

Approval represents a formal decision that a document satisfies the applicable acceptance requirements.

Approval may be required before a document is distributed, used as an authoritative reference, or treated as an accepted project deliverable.

The implementations distinguish a review decision from the broader document management workflow.

### 3.5 Document Archiving

Archiving preserves documents that are no longer undergoing active modification.

Archived documents remain available for historical reference and audit purposes.

The implementations prohibit normal document modification after archiving.

Archiving is different from deletion. It preserves the document and its history.

## 4. Document States and State Transitions

The system implements five document states.

| State | Meaning |
|---|---|
| Draft | Document is being prepared or modified |
| Under Review | Document has been submitted for examination |
| Approved | Document has received an approval decision |
| Rejected | Document has received a rejection decision |
| Archived | Document has been placed into historical storage |

### 4.1 State Transition Rules

The permitted transitions are:

| Current state | Permitted next state |
|---|---|
| Draft | Under Review, Archived |
| Under Review | Draft, Approved, Rejected |
| Approved | Draft, Archived |
| Rejected | Draft, Archived |
| Archived | None |

A state machine prevents invalid workflow operations.

For example:

- A draft document cannot be directly approved.
- An archived document cannot return to draft.
- A document under review cannot be archived through the normal workflow.
- An approved document must return to draft before another review cycle.

These restrictions prevent inconsistent document states.

### 4.2 State Versus Content

Document content and document state are separate concepts.

Content represents what the document contains.

State represents its current position in the management workflow.

Changing content creates a new version. Changing state records a workflow transition.

This distinction is important because a document can have the same title while its content and approval status change over time.

## 5. Document Version Management

Version management preserves successive representations of a document.

A new version is created whenever an authorized user changes document content.

For example:

| Version | Change | Status |
|---|---|---|
| 1 | Initial requirements | Draft |
| 2 | Added security requirements | Draft |
| 3 | Added access restrictions | Under Review |
| 4 | Revised requirements after feedback | Draft |
| 5 | Final reviewed requirements | Approved |

### 5.1 Version Numbering

The system uses sequential integer version numbers.

The next version is calculated as:

`Next version = Current version + 1`

Each version records:

- Version identifier.
- Version number.
- Document content.
- Author.
- Creation timestamp.
- Change description.
- Content checksum.

### 5.2 Immutable Historical Versions

An existing version should not be silently overwritten.

Instead, modifications create new versions.

This provides:

- Historical traceability.
- Accountability.
- Comparison between revisions.
- Recovery of previous content.
- Evidence of document evolution.

The PostgreSQL implementation uses a trigger to prevent updates and deletions of historical version records.

### 5.3 Optimistic Concurrency Control

Concurrent editing can create conflicting updates.

Consider two users opening version 3.

Both users begin modifying the same document.

The first user saves a new version, producing version 4.

The second user attempts to save using version 3 as the expected current version.

The system rejects the second operation.

The validation rule is:

`Expected version = Actual current version`

If the values differ, the update fails.

Python, JavaScript, C++17, Java 17, and PostgreSQL implement this protection.

This mechanism prevents a user from unintentionally overwriting a newer version.

### 5.4 Content Integrity

A checksum helps identify unexpected changes to stored content.

The Python, JavaScript, and Java implementations use SHA-256.

The C++17 implementation uses FNV-1a for lightweight change detection. FNV-1a is not cryptographically secure and must not be used for security-sensitive integrity verification.

The PostgreSQL implementation stores a SHA-256 checksum supplied by the application.

A checksum can identify content changes when compared against a trusted original checksum.

It does not independently prove who created the document or whether the stored checksum itself was altered.

## 6. Document Ownership and Access Management

Document management requires clear responsibilities.

The system implements five user roles.

| Role | Main responsibility |
|---|---|
| Admin | Administrative control |
| Project Manager | Project and document governance |
| Author | Document creation and modification |
| Reviewer | Independent document examination |
| Viewer | Read-only access |

### 6.1 Role-Based Access Control

Role-Based Access Control, or RBAC, assigns permissions according to user roles.

For example:

| Operation | Admin | Project Manager | Author | Reviewer | Viewer |
|---|---|---|---|---|---|
| Create documents | Yes | Yes | Yes | No | No |
| Modify owned documents | Yes | Yes | Yes | No | No |
| Review documents | Yes | Yes | No | Yes | No |
| Archive documents | Yes | Yes | No | No | No |
| View documents | Yes | Yes | Yes | Yes | Yes |
| Generate administrative reports | Yes | Yes | No | No | No |

The implementations enforce role checks within their management services.

### 6.2 Document Ownership

Ownership identifies the person responsible for a document.

The owner is not necessarily the reviewer or project manager.

For example:

- A technical author creates the architecture specification.
- A technical reviewer examines its correctness.
- A project manager supervises the documentation workflow.
- An administrator maintains system-level controls.

The system prohibits authors from approving their own documents.

This separation improves the independence of the review process.

### 6.3 Project Membership and Document Permissions

The PostgreSQL model separates project membership from document-specific permissions.

Project membership records a user's participation in a project.

Document permissions record specific access rights for an individual document.

This allows a project to have several participants with different responsibilities.

The database provides the foundation for permission evaluation. A production deployment must enforce these permissions through database privileges, Row-Level Security policies, or a trusted application service. Merely storing permission records does not automatically enforce them.

## 7. Document Review Management

Review evaluates the quality of a particular document version.

It is different from simply opening or reading a document.

A review records a formal decision.

### 7.1 Review Decisions

The system supports three decisions.

| Decision | Meaning | Resulting state |
|---|---|---|
| Approved | Document satisfies the review requirements | Approved |
| Rejected | Document is unsuitable for acceptance | Rejected |
| Changes Requested | Document requires further modification | Draft |

Each review includes:

- Reviewer identity.
- Document identifier.
- Reviewed version.
- Decision.
- Comments.
- Timestamp.

### 7.2 Review Independence

The implementations prohibit a document owner from reviewing and approving their own document.

This reduces conflicts of interest.

A production policy can impose further restrictions, such as:

- Reviewer qualifications.
- Separation of technical and managerial approval.
- Minimum number of reviewers.
- Mandatory security review.
- Department-specific review requirements.

### 7.3 Review Comments

Review comments provide specific feedback.

A comment may refer to a document section or an earlier discussion.

The PostgreSQL implementation supports parent-child comments and resolution tracking.

For example:

| Section | Comment | Status |
|---|---|---|
| Security | Clarify access control requirements | Resolved |
| Architecture | Explain the database backup process | Open |
| Testing | Add evidence of integration testing | Resolved |

Resolving a discussion means that the associated issue has been addressed or otherwise closed.

It does not automatically approve the document.

## 8. Approval Management

Approval represents a formal decision concerning document acceptance.

A project may require more than one approval.

For example:

| Document category | Required approvals |
|---|---:|
| Requirements | 1 |
| Technical specification | 2 |
| Project plan | 1 |
| Security design | 2 |

The Java implementation provides an explicit `ReviewPolicy` object that defines the required approval count and self-approval restriction.

The PostgreSQL implementation stores approval requirements by project and document type.

### 8.1 Distinct Approvals

When multiple approvals are required, the system counts distinct reviewers.

Two approval records from the same reviewer must not count as two independent approvals.

The database uses distinct reviewer identifiers when calculating approval eligibility.

### 8.2 Version-Specific Approval

An approval applies to the version that was reviewed.

If a document changes after approval, the previous approval must not automatically be treated as approval of the new content.

For example:

- Version 3 receives approval.
- The author creates version 4.
- Version 4 requires a new review and approval cycle.

This prevents outdated decisions from being applied to modified documents.

### 8.3 Approval Versus Publication

Approval and publication are separate concepts.

Approval indicates that the document satisfies its acceptance policy.

Publication eligibility can also depend on:

- Automated validation results.
- Unresolved review comments.
- Required approvals.
- Current document status.

The PostgreSQL publication eligibility function evaluates these conditions separately.

## 9. Automated Document Validation

Automated checks can verify document properties before acceptance.

Examples include:

| Check | Purpose |
|---|---|
| Content validation | Confirms required content exists |
| Metadata validation | Checks mandatory document information |
| Version validation | Confirms the current version exists |
| Integrity validation | Compares content checksums |
| Review validation | Confirms required review decisions |
| Approval validation | Checks approval requirements |
| Discussion validation | Identifies unresolved comments |

The PostgreSQL implementation stores automated results in `document_status_checks`.

Each check is associated with a specific document version.

A failed check prevents the publication eligibility function from returning an eligible result.

The current implementation uses sample validation records. Actual document-format validation requires additional application-level parsing and validation logic.

## 10. Document Search and Retrieval

Document search helps users locate relevant information.

The implementations support keyword-based searching.

Searchable information includes:

- Document titles.
- Document content.
- Document types.
- Tags.

The Python implementation uses dictionaries and lists.

The JavaScript implementation uses `Map`, `Set`, and array filtering.

The C++17 implementation uses STL containers and algorithms.

The Java implementation uses streams and collections.

The PostgreSQL implementation demonstrates full-text searching using `to_tsvector` and `plainto_tsquery`.

### 10.1 Search Performance

A basic in-memory search scans the available documents.

For `n` documents and an average searchable content length of `m`, a straightforward search has approximately O(n × m) character-processing cost.

For larger systems, PostgreSQL full-text indexes or dedicated search indexes can reduce the amount of content examined.

Search results should also respect the user's document access permissions.

## 11. Audit Logging and Traceability

An audit log records important document management activities.

Examples include:

- Document creation.
- Document access.
- Version creation.
- Review submission.
- Review decisions.
- Archiving.
- Document export.

An audit record contains:

| Field | Purpose |
|---|---|
| Audit identifier | Unique event reference |
| Document identifier | Related document |
| Actor identifier | User responsible |
| Action | Operation performed |
| Details | Supporting event information |
| Timestamp | Time of the event |

Audit logging helps establish the history of document operations.

It supports:

- Accountability.
- Internal investigations.
- Compliance verification.
- Change tracking.
- Project governance.
- Historical reconstruction.

An ordinary application audit table is not automatically tamper-proof.

Production environments should restrict audit-table modification, separate administrative responsibilities, and consider external or append-only audit storage.

## 12. Document Retention and Archiving

Document retention defines how long a document must be preserved.

Retention periods may depend on:

- Project requirements.
- Contractual obligations.
- Organizational policies.
- Regulatory obligations.
- Legal requirements.
- Records classification.

The PostgreSQL model includes a `retention_until` date.

The retention reporting view classifies documents into:

| State | Meaning |
|---|---|
| Not configured | No retention date has been assigned |
| Expired | Retention date has passed |
| Expiring soon | Retention expires within 30 days |
| Within retention | Retention period remains active |

The current implementations demonstrate archiving but do not implement automated legal deletion or physical storage lifecycle management.

Retention and deletion policies should be explicitly approved before implementation.

## 13. Project Documentation Reporting

Reporting provides information about the documentation status of a project.

The system generates:

- Total document count.
- Documents by status.
- Documents by category.
- Total version count.
- Pending review count.
- Audit history.
- Retention status.

A project manager can use these reports to identify documentation bottlenecks.

For example:

| Metric | Interpretation |
|---|---|
| Draft documents | Work still being prepared |
| Under-review documents | Work awaiting examination |
| Approved documents | Accepted documentation |
| Rejected documents | Documentation requiring further attention |
| Archived documents | Historical records |
| Total versions | Amount of document revision activity |

A high number of documents under review may indicate reviewer capacity problems or delayed decision-making.

A high number of rejected documents may indicate incomplete requirements or inadequate document quality.

## 14. Implementation Architecture

The five implementations use different engineering approaches to model the same documentation domain.

### 14.1 Python

The Python implementation emphasizes a service-oriented object model.

Principal components:

| Component | Responsibility |
|---|---|
| User | Represents a system participant |
| ProjectDocument | Represents a managed document |
| DocumentVersion | Preserves a document revision |
| Review | Stores review decisions |
| AuditEvent | Records document operations |
| ProjectDocumentationManager | Controls the management workflow |

Python features include:

- Dataclasses for domain records.
- Enumerations for controlled values.
- Dictionaries for fast identifier-based lookup.
- Sets for project and tag management.
- Exceptions for validation and authorization failures.
- SHA-256 for content integrity checks.
- JSON for document export.
- Assertions for executable verification.

The manager centralizes workflow operations and maintains application state.

The implementation uses in-memory storage, making it suitable for learning and controlled demonstrations rather than persistent multi-user deployment.

### 14.2 JavaScript

The JavaScript implementation emphasizes event-driven operations and asynchronous processing.

Principal components:

| Component | Responsibility |
|---|---|
| User | Represents a system participant |
| DocumentRepository | Stores document records |
| DocumentationService | Coordinates operations |
| EventEmitter | Publishes document events |
| Version management | Protects document updates |
| Export service | Handles asynchronous file operations |

Important JavaScript mechanisms include:

- `Map` for document and user lookup.
- `Set` for unique projects and tags.
- `EventEmitter` for event notification.
- `async` and `await` for asynchronous file operations.
- Promises for operation sequencing.
- `crypto` for identifiers and checksums.
- `fs/promises` for file persistence.
- Structured cloning for defensive data copying.

The service emits events when important document operations occur.

The in-memory locking mechanism prevents overlapping updates within the same service instance.

It is not a distributed locking mechanism. Multiple application processes require shared database transactions or a distributed concurrency-control mechanism.

### 14.3 C++17

The C++17 implementation emphasizes domain modeling and explicit workflow enforcement.

Principal components:

| Component | Responsibility |
|---|---|
| User | Represents a system participant |
| Project | Represents a managed project |
| DocumentVersion | Stores revision information |
| ProjectDocument | Maintains document state |
| Review | Records review decisions |
| AuditEvent | Maintains event history |
| DocumentationEngine | Coordinates governance |

C++17 capabilities include:

- Classes and structures.
- Strongly typed enumerations.
- STL vectors.
- STL sets.
- STL maps.
- Unordered maps.
- Algorithms such as `all_of`, `find`, and `transform`.
- Exception-based error handling.
- Modular domain operations.

The implementation uses integer identifiers for demonstration purposes.

It uses FNV-1a as a lightweight content-change detector. This hash is not suitable for cryptographic integrity guarantees.

### 14.4 Java 17

The Java implementation emphasizes enterprise-oriented domain design.

Principal components:

| Component | Responsibility |
|---|---|
| User | Immutable user record |
| Project | Immutable project record |
| DocumentVersion | Immutable version record |
| Review | Immutable review record |
| ProjectDocument | Document entity |
| DocumentRepository | Document persistence abstraction |
| ReviewPolicy | Approval policy |
| DocumentationService | Business workflow service |

Java 17 features include:

- Records for immutable data structures.
- Enumerations for controlled domain values.
- Collections for entity storage.
- Streams for document filtering and aggregation.
- `Map` and `Set` for efficient lookup.
- Custom exception classes.
- `MessageDigest` for SHA-256.
- Synchronized service operations.
- Switch expressions for state transitions.

The repository layer separates document retrieval from business workflow logic.

The service layer enforces permissions and manages document state.

This separation provides a foundation for replacing in-memory storage with a database-backed repository.

### 14.5 PostgreSQL

The PostgreSQL implementation emphasizes relational integrity and transactional workflow processing.

Its schema contains:

| Table | Responsibility |
|---|---|
| users | Stores users and roles |
| projects | Stores project information |
| project_members | Stores project participation |
| documents | Stores document metadata and current state |
| document_versions | Stores historical content |
| document_tags | Stores document classification |
| document_permissions | Stores document-specific permissions |
| approval_requirements | Stores approval policies |
| document_reviews | Stores review decisions |
| review_comments | Stores review discussions |
| document_status_checks | Stores automated validation results |
| document_audit | Stores audit events |

The database uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Enumerated types.
- Indexes.
- Triggers.
- Functions.
- Procedures.
- Common Table Expressions.
- Reporting views.
- Transactions.

The current-version foreign key is deferrable so a document and its initial version can be created in the same transaction.

The version-creation function locks the document row using `FOR UPDATE`, checks the expected version, inserts the new version, and updates the document record.

This protects against concurrent database updates.

## 15. Database Relationship Model

The relational model represents the principal entities and their relationships.

Project structure:

Project  
→ Project Members  
→ Documents  
→ Document Versions  
→ Reviews  
→ Review Comments  
→ Status Checks  
→ Audit Events

Additional relationships:

- Projects have approval requirements.
- Documents have tags.
- Documents have individual access permissions.
- Users create document versions.
- Users submit reviews.
- Reviewers resolve discussions.
- Projects contain multiple document categories.
- Document versions have independent checksums.

### 15.1 Entity Relationships

| Relationship | Cardinality |
|---|---|
| Project to Documents | One-to-many |
| Project to Members | One-to-many |
| User to Documents | One-to-many |
| Document to Versions | One-to-many |
| Document to Reviews | One-to-many |
| Review to Comments | One-to-many |
| Document to Status Checks | One-to-many |
| Document to Audit Events | One-to-many |
| Document to Tags | One-to-many |
| Document to Permissions | One-to-many |

Foreign keys maintain referential integrity.

Unique constraints prevent duplicate version numbers and duplicate reviewer decisions for the same version.

## 16. Transaction Management

Transactions ensure that related database operations succeed or fail together.

Consider initial document creation.

The operation requires:

1. Creating document metadata.
2. Creating the initial document version.
3. Establishing the current version reference.

If one operation fails, the transaction must not leave incomplete records.

The PostgreSQL script demonstrates transactional execution through `BEGIN` and `COMMIT`.

The version-creation function also locks the document row before updating it.

This reduces the risk of concurrent users creating conflicting versions.

A production system should use explicit transaction boundaries around multi-operation workflows and carefully define its isolation requirements.

## 17. Error Handling and Failure Scenarios

The implementations include several failure-handling mechanisms.

| Failure | Expected behavior |
|---|---|
| Missing document | Reject retrieval or modification |
| Empty title | Reject document creation |
| Empty content | Reject document creation or update |
| Invalid email | Reject user registration |
| Duplicate email | Reject registration |
| Unauthorized operation | Reject the request |
| Self-approval | Reject the review |
| Archived document modification | Reject the update |
| Invalid state transition | Reject the transition |
| Stale version update | Reject the update |
| Missing project | Reject document creation |
| Invalid review comments | Reject review submission |

These checks protect the integrity of document operations.

Errors should be recorded with sufficient diagnostic information while avoiding unnecessary disclosure of confidential document content.

## 18. Security Considerations

Project documentation may contain confidential information, intellectual property, technical designs, operational procedures, and contractual records.

A production document management system should address the following security controls.

### 18.1 Authentication

Users should authenticate before accessing protected project documents.

The demonstrations use registered user identifiers but do not implement password management or authentication protocols.

### 18.2 Authorization

Permissions should be checked for every sensitive operation.

Authorization should not depend solely on the user interface.

The server and database must enforce the applicable access rules.

### 18.3 Data Protection

Sensitive documents should be protected during transmission and storage.

Encryption, secure backup, and appropriate key management should be part of the deployment architecture.

### 18.4 Integrity

SHA-256 checksums can detect content differences when compared against trusted values.

Cryptographic signatures and independently protected audit records can provide stronger evidence of authenticity and accountability.

### 18.5 Input Validation

Document titles, content sizes, tags, email addresses, and comments are validated.

Database queries should use parameterized statements.

Untrusted document content should not be interpreted as executable code.

### 18.6 Audit Protection

Audit records should have restricted modification privileges.

Administrative actions should also be monitored.

### 18.7 Backup and Recovery

Document storage should support:

- Regular backups.
- Backup integrity verification.
- Recovery testing.
- Version preservation.
- Access-controlled backup storage.

## 19. Performance and Scalability

The demonstration implementations use in-memory collections in their application layers.

Their performance characteristics differ from a persistent enterprise system.

| Operation | Demonstration approach | Approximate complexity |
|---|---|---|
| Document lookup | Hash map | Average O(1) |
| User lookup | Hash map | Average O(1) |
| Document search | Sequential scan | O(n × m) |
| Version retrieval | Indexed list position | O(1) |
| Tag uniqueness | Set | Average O(1) |
| Project report | Document aggregation | O(n) |
| Audit filtering | Sequential scan | O(a) |

Where:

- `n` represents the number of documents.
- `m` represents the average searchable content length.
- `a` represents the number of audit records.

For larger deployments:

- Use database-backed repositories.
- Add indexes for frequently queried fields.
- Introduce full-text search.
- Paginate large document lists.
- Separate document metadata from large content objects where appropriate.
- Use object storage for large attachments.
- Apply connection pooling.
- Use database transactions for concurrent modifications.
- Archive old records according to approved retention policies.

## 20. Practical Workflow Example

Consider a project developing an enterprise document management platform.

The project team needs to maintain requirements, technical specifications, design records, meeting minutes, and testing reports.

A typical workflow is:

1. The project manager creates the project.
2. The technical author creates the requirements document.
3. The system assigns version 1.
4. The author modifies the requirements.
5. The system creates version 2.
6. The author submits version 2 for review.
7. An independent reviewer examines the document.
8. The reviewer records an approval decision.
9. The system records the decision against version 2.
10. Automated checks evaluate the document.
11. The system evaluates publication eligibility.
12. The document remains available for project use and reporting.
13. Future changes create subsequent versions.
14. The project manager eventually archives the document when appropriate.

The workflow maintains the distinction between content changes, review decisions, approval decisions, and document lifecycle states.

## 21. Important Limitations

These implementations are educational management systems rather than complete enterprise document repositories.

The following capabilities require additional deployment-level engineering:

| Area | Current limitation |
|---|---|
| Persistence | Application implementations primarily use in-memory storage |
| Authentication | Full login and identity-provider integration is not implemented |
| Distributed locking | Application-level locks do not coordinate multiple servers |
| File management | Python and JavaScript demonstrate JSON export rather than full document storage |
| File format validation | PDF, DOCX, XLSX, and other formats are not parsed |
| Access enforcement | PostgreSQL permission records require application or database enforcement |
| Encryption | Storage and transmission encryption are deployment responsibilities |
| Digital signatures | Cryptographic signing is not implemented |
| Notifications | Email and collaboration notifications are not implemented |
| Backup | Automated backup and restoration are not implemented |
| Retention execution | Retention reporting exists, but automated deletion is not implemented |
| Search | Advanced relevance ranking and document indexing are not implemented |

The PostgreSQL publication eligibility function provides an additional governance check. It does not replace a complete enterprise publication or distribution service.

The application implementations use different levels of workflow enforcement. In particular, the Java implementation provides an explicit multi-approval policy model, while the Python, JavaScript, and C++17 demonstrations use a simpler single-review decision workflow.

## 22. Execution Requirements

### Python

| Requirement | Value |
|---|---|
| Runtime | Python 3.10 or later |
| External packages | None |
| Main file | `project_documentation.py` |

The program runs using the Python standard library.

### JavaScript

| Requirement | Value |
|---|---|
| Runtime | Node.js 18 or later |
| External packages | None |
| Main file | `project_documentation.js` |

The program uses Node.js built-in modules.

### C++17

| Requirement | Value |
|---|---|
| Standard | C++17 |
| External libraries | None |
| Main file | `project_documentation.cpp` |

The program uses the C++ standard library.

### Java 17

| Requirement | Value |
|---|---|
| Runtime | Java 17 |
| External packages | None |
| Main file | `ProjectDocumentationManager.java` |

The program uses Java 17 language features.

### PostgreSQL

| Requirement | Value |
|---|---|
| Database | PostgreSQL 15 or later |
| Extension | `pgcrypto` for UUID generation |
| Schema | `project_docs` |
| Main file | `project_documentation.sql` |

The PostgreSQL script creates its schema, domain types, tables, functions, procedures, triggers, indexes, sample data, and reporting queries.

The database user requires permission to create schemas and database objects, install the required extension where necessary, and execute the script.

The SQL demonstration uses illustrative checksums. A production application must calculate and verify the actual SHA-256 digest of document content before inserting or accepting a version.

## 23. Expected System Capabilities

| Capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Project management | Yes | Yes | Yes | Yes | Yes |
| User management | Yes | Yes | Yes | Yes | Yes |
| Document creation | Yes | Yes | Yes | Yes | Yes |
| Version management | Yes | Yes | Yes | Yes | Yes |
| Version conflict handling | Yes | Yes | Yes | Yes | Yes |
| Review workflow | Yes | Yes | Yes | Yes | Yes |
| Approval decisions | Yes | Yes | Yes | Yes | Yes |
| Role validation | Yes | Yes | Yes | Yes | Modelled |
| Content integrity | SHA-256 | SHA-256 | FNV-1a | SHA-256 | Stored checksum |
| Document search | Yes | Yes | Yes | Yes | Full-text query |
| Audit records | Yes | Yes | Yes | Yes | Yes |
| Reporting | Yes | Yes | Yes | Yes | Yes |
| Archiving | Yes | Yes | Yes | Yes | Yes |
| Asynchronous export | No | Yes | No | No | Not applicable |
| Relational integrity | In-memory | In-memory | In-memory | In-memory | Yes |

The five implementations demonstrate different ways to represent the same project documentation domain while preserving its essential management concepts, version history, workflow controls, review decisions, approval requirements, and accountability mechanisms.
