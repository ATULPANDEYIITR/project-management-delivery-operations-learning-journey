"use strict";

/**
 * PROJECT DOCUMENTATION MANAGEMENT SYSTEM
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 *
 * Features:
 * - Event-driven document management
 * - Version history and checksum verification
 * - Role-based permissions
 * - Review workflows
 * - Approval decisions
 * - Document search
 * - Audit events
 * - Asynchronous persistence
 * - Concurrent update protection
 */

const crypto = require("node:crypto");
const fs = require("node:fs/promises");
const path = require("node:path");
const EventEmitter = require("node:events");

// ==========================================================
// ENUMERATIONS
// ==========================================================

const DocumentType = Object.freeze({
    REQUIREMENTS: "requirements",
    PROJECT_PLAN: "project_plan",
    TECHNICAL_SPECIFICATION: "technical_specification",
    DESIGN: "design",
    MEETING_MINUTES: "meeting_minutes",
    PROGRESS_REPORT: "progress_report",
    RISK_REGISTER: "risk_register",
    TEST_REPORT: "test_report",
    USER_GUIDE: "user_guide",
    CLOSURE_REPORT: "closure_report"
});

const DocumentStatus = Object.freeze({
    DRAFT: "draft",
    UNDER_REVIEW: "under_review",
    APPROVED: "approved",
    REJECTED: "rejected",
    ARCHIVED: "archived"
});

const Role = Object.freeze({
    ADMIN: "admin",
    PROJECT_MANAGER: "project_manager",
    AUTHOR: "author",
    REVIEWER: "reviewer",
    VIEWER: "viewer"
});

const Decision = Object.freeze({
    APPROVED: "approved",
    REJECTED: "rejected",
    CHANGES_REQUESTED: "changes_requested"
});

// ==========================================================
// CUSTOM ERRORS
// ==========================================================

class DocumentationError extends Error {}
class ValidationError extends DocumentationError {}
class AuthorizationError extends DocumentationError {}
class NotFoundError extends DocumentationError {}
class StateError extends DocumentationError {}
class VersionConflictError extends DocumentationError {}

// ==========================================================
// CONSTANTS AND VALIDATION
// ==========================================================

const ALLOWED_TRANSITIONS = Object.freeze({
    draft: ["under_review", "archived"],
    under_review: ["draft", "approved", "rejected"],
    approved: ["draft", "archived"],
    rejected: ["draft", "archived"],
    archived: []
});

function validateText(value, field, maximumLength = 5000000) {
    if (typeof value !== "string" || !value.trim()) {
        throw new ValidationError(`${field} is required.`);
    }

    if (Buffer.byteLength(value, "utf8") > maximumLength) {
        throw new ValidationError(`${field} exceeds its size limit.`);
    }

    return value.trim();
}

function validateEmail(email) {
    if (
        typeof email !== "string" ||
        !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    ) {
        throw new ValidationError("Invalid email address.");
    }

    return email.toLowerCase();
}

function checksum(content) {
    return crypto
        .createHash("sha256")
        .update(content, "utf8")
        .digest("hex");
}

function identifier() {
    return crypto.randomUUID();
}

// ==========================================================
// DOCUMENTATION DOMAIN
// ==========================================================

class User {
    constructor(name, email, role) {
        this.id = identifier();
        this.name = validateText(name, "User name", 200);
        this.email = validateEmail(email);

        if (!Object.values(Role).includes(role)) {
            throw new ValidationError("Invalid user role.");
        }

        this.role = role;
        this.active = true;
    }
}

class DocumentRepository {
    constructor() {
        this.documents = new Map();
        this.projects = new Set();
    }

    add(document) {
        if (this.documents.has(document.id)) {
            throw new ValidationError("Duplicate document identifier.");
        }

        this.documents.set(document.id, document);
        return document;
    }

    get(documentId) {
        const document = this.documents.get(documentId);

        if (!document) {
            throw new NotFoundError("Document not found.");
        }

        return document;
    }

    list(projectId) {
        return [...this.documents.values()]
            .filter(document => document.projectId === projectId);
    }
}

// ==========================================================
// DOCUMENT MANAGEMENT SERVICE
// ==========================================================

class DocumentationService extends EventEmitter {

    constructor() {
        super();

        this.users = new Map();
        this.emailIndex = new Map();

        this.repository = new DocumentRepository();

        this.auditLog = [];
        this.operationLocks = new Set();

        this.maximumDocumentBytes = 5_000_000;
    }

    // ------------------------------------------------------
    // USERS
    // ------------------------------------------------------

    registerUser(name, email, role) {
        const normalizedEmail = validateEmail(email);

        if (this.emailIndex.has(normalizedEmail)) {
            throw new ValidationError("Email already registered.");
        }

        const user = new User(name, normalizedEmail, role);

        this.users.set(user.id, user);
        this.emailIndex.set(normalizedEmail, user.id);

        return user;
    }

    getActiveUser(userId) {
        const user = this.users.get(userId);

        if (!user || !user.active) {
            throw new AuthorizationError(
                "User is unavailable or inactive."
            );
        }

        return user;
    }

    authorize(userId, allowedRoles) {
        const user = this.getActiveUser(userId);

        if (!allowedRoles.includes(user.role)) {
            throw new AuthorizationError(
                `Role ${user.role} is not permitted.`
            );
        }

        return user;
    }

    // ------------------------------------------------------
    // AUDIT EVENTS
    // ------------------------------------------------------

    recordEvent(document, actorId, action, details = {}) {
        const event = Object.freeze({
            id: identifier(),
            documentId: document.id,
            actorId,
            action,
            details: structuredClone(details),
            timestamp: new Date().toISOString()
        });

        this.auditLog.push(event);

        this.emit("document:event", event);

        return event;
    }

    // ------------------------------------------------------
    // PROJECTS
    // ------------------------------------------------------

    createProject(actorId, name) {
        this.authorize(actorId, [
            Role.ADMIN,
            Role.PROJECT_MANAGER
        ]);

        const project = Object.freeze({
            id: identifier(),
            name: validateText(name, "Project name", 200),
            createdAt: new Date().toISOString()
        });

        this.repository.projects.add(project.id);

        return project;
    }

    // ------------------------------------------------------
    // DOCUMENT CREATION
    // ------------------------------------------------------

    createDocument({
        actorId,
        projectId,
        title,
        type,
        content,
        tags = []
    }) {
        const actor = this.authorize(actorId, [
            Role.ADMIN,
            Role.PROJECT_MANAGER,
            Role.AUTHOR
        ]);

        if (!this.repository.projects.has(projectId)) {
            throw new ValidationError("Unknown project.");
        }

        if (!Object.values(DocumentType).includes(type)) {
            throw new ValidationError("Invalid document type.");
        }

        const safeTitle = validateText(title, "Document title", 200);

        const safeContent = validateText(
            content,
            "Document content",
            this.maximumDocumentBytes
        );

        if (!Array.isArray(tags)) {
            throw new ValidationError("Tags must be an array.");
        }

        const normalizedTags = [
            ...new Set(
                tags.map(tag =>
                    validateText(tag, "Tag", 100).toLowerCase()
                )
            )
        ];

        const version = Object.freeze({
            id: identifier(),
            number: 1,
            content: safeContent,
            checksum: checksum(safeContent),
            authorId: actor.id,
            changeDescription: "Initial creation",
            createdAt: new Date().toISOString()
        });

        const document = {
            id: identifier(),
            projectId,
            title: safeTitle,
            type,
            ownerId: actor.id,
            status: DocumentStatus.DRAFT,
            currentVersion: 1,
            versions: [version],
            reviews: [],
            tags: normalizedTags,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };

        this.repository.add(document);

        this.recordEvent(
            document,
            actorId,
            "DOCUMENT_CREATED",
            { version: 1 }
        );

        return structuredClone(document);
    }

    // ------------------------------------------------------
    // CONCURRENT UPDATE PROTECTION
    // ------------------------------------------------------

    async withLock(documentId, operation) {
        if (this.operationLocks.has(documentId)) {
            throw new VersionConflictError(
                "Another update is in progress."
            );
        }

        this.operationLocks.add(documentId);

        try {
            return await operation();
        } finally {
            this.operationLocks.delete(documentId);
        }
    }

    // ------------------------------------------------------
    // VERSION MANAGEMENT
    // ------------------------------------------------------

    async updateDocument({
        documentId,
        actorId,
        content,
        changeDescription,
        expectedVersion
    }) {
        return this.withLock(documentId, async () => {
            const actor = this.authorize(actorId, [
                Role.ADMIN,
                Role.PROJECT_MANAGER,
                Role.AUTHOR
            ]);

            const document = this.repository.get(documentId);

            if (
                actor.role === Role.AUTHOR &&
                document.ownerId !== actorId
            ) {
                throw new AuthorizationError(
                    "Authors can update only their own documents."
                );
            }

            if (document.status === DocumentStatus.ARCHIVED) {
                throw new StateError(
                    "Archived documents cannot be modified."
                );
            }

            if (document.currentVersion !== expectedVersion) {
                throw new VersionConflictError(
                    "Document version has changed."
                );
            }

            const safeContent = validateText(
                content,
                "Content",
                this.maximumDocumentBytes
            );

            const nextVersion = document.currentVersion + 1;

            const version = Object.freeze({
                id: identifier(),
                number: nextVersion,
                content: safeContent,
                checksum: checksum(safeContent),
                authorId: actorId,
                changeDescription: validateText(
                    changeDescription,
                    "Change description",
                    500
                ),
                createdAt: new Date().toISOString()
            });

            document.versions.push(version);
            document.currentVersion = nextVersion;

            if (
                document.status === DocumentStatus.APPROVED ||
                document.status === DocumentStatus.REJECTED ||
                document.status === DocumentStatus.UNDER_REVIEW
            ) {
                document.status = DocumentStatus.DRAFT;
            }

            document.updatedAt = new Date().toISOString();

            this.recordEvent(
                document,
                actorId,
                "VERSION_CREATED",
                { version: nextVersion }
            );

            return structuredClone(version);
        });
    }

    // ------------------------------------------------------
    // REVIEW SUBMISSION
    // ------------------------------------------------------

    submitForReview(documentId, actorId) {
        const document = this.repository.get(documentId);

        if (
            document.ownerId !== actorId &&
            ![
                Role.ADMIN,
                Role.PROJECT_MANAGER
            ].includes(this.getActiveUser(actorId).role)
        ) {
            throw new AuthorizationError(
                "Not authorized to submit this document."
            );
        }

        this.transition(
            document,
            DocumentStatus.UNDER_REVIEW
        );

        this.recordEvent(
            document,
            actorId,
            "SUBMITTED_FOR_REVIEW"
        );
    }

    // ------------------------------------------------------
    // STATE TRANSITIONS
    // ------------------------------------------------------

    transition(document, nextStatus) {
        const allowed = ALLOWED_TRANSITIONS[document.status];

        if (!allowed || !allowed.includes(nextStatus)) {
            throw new StateError(
                `Invalid transition: ${document.status} -> ${nextStatus}`
            );
        }

        document.status = nextStatus;
        document.updatedAt = new Date().toISOString();
    }

    // ------------------------------------------------------
    // REVIEW DECISIONS
    // ------------------------------------------------------

    reviewDocument({
        documentId,
        reviewerId,
        decision,
        comments
    }) {
        const reviewer = this.authorize(reviewerId, [
            Role.ADMIN,
            Role.PROJECT_MANAGER,
            Role.REVIEWER
        ]);

        const document = this.repository.get(documentId);

        if (reviewerId === document.ownerId) {
            throw new AuthorizationError(
                "Self-review is prohibited."
            );
        }

        if (document.status !== DocumentStatus.UNDER_REVIEW) {
            throw new StateError(
                "Document is not under review."
            );
        }

        if (!Object.values(Decision).includes(decision)) {
            throw new ValidationError("Invalid review decision.");
        }

        const review = Object.freeze({
            id: identifier(),
            reviewerId,
            version: document.currentVersion,
            decision,
            comments: validateText(comments, "Review comments", 5000),
            createdAt: new Date().toISOString()
        });

        document.reviews.push(review);

        const nextStatus = {
            [Decision.APPROVED]: DocumentStatus.APPROVED,
            [Decision.REJECTED]: DocumentStatus.REJECTED,
            [Decision.CHANGES_REQUESTED]: DocumentStatus.DRAFT
        }[decision];

        this.transition(document, nextStatus);

        this.recordEvent(
            document,
            reviewer.id,
            "REVIEW_COMPLETED",
            {
                decision,
                version: review.version
            }
        );

        return review;
    }

    // ------------------------------------------------------
    // DOCUMENT ARCHIVING
    // ------------------------------------------------------

    archiveDocument(documentId, actorId) {
        this.authorize(actorId, [
            Role.ADMIN,
            Role.PROJECT_MANAGER
        ]);

        const document = this.repository.get(documentId);

        this.transition(
            document,
            DocumentStatus.ARCHIVED
        );

        this.recordEvent(
            document,
            actorId,
            "DOCUMENT_ARCHIVED"
        );
    }

    // ------------------------------------------------------
    // DOCUMENT SEARCH
    // ------------------------------------------------------

    searchDocuments(projectId, actorId, keyword) {
        this.getActiveUser(actorId);

        const query = validateText(keyword, "Search keyword").toLowerCase();

        return this.repository
            .list(projectId)
            .filter(document => {
                const latest = document.versions.at(-1);

                const searchable = [
                    document.title,
                    document.type,
                    latest.content,
                    ...document.tags
                ].join(" ").toLowerCase();

                return searchable.includes(query);
            })
            .map(document => structuredClone(document));
    }

    // ------------------------------------------------------
    // VERSION VERIFICATION
    // ------------------------------------------------------

    verifyDocumentIntegrity(documentId, actorId) {
        this.getActiveUser(actorId);

        const document = this.repository.get(documentId);

        return document.versions.map(version => ({
            version: version.number,
            valid: checksum(version.content) === version.checksum
        }));
    }

    // ------------------------------------------------------
    // ASYNCHRONOUS EXPORT
    // ------------------------------------------------------

    async exportDocument(documentId, actorId, outputDirectory) {
        this.getActiveUser(actorId);

        const document = this.repository.get(documentId);

        const version = document.versions.at(-1);

        const output = {
            documentId: document.id,
            projectId: document.projectId,
            title: document.title,
            type: document.type,
            status: document.status,
            version: version.number,
            checksum: version.checksum,
            content: version.content,
            exportedAt: new Date().toISOString()
        };

        const directory = path.resolve(outputDirectory);

        await fs.mkdir(directory, { recursive: true });

        const filename = `${document.id}.json`;
        const destination = path.join(directory, filename);
        const temporary = `${destination}.${identifier()}.tmp`;

        try {
            await fs.writeFile(
                temporary,
                JSON.stringify(output, null, 2),
                { encoding: "utf8", flag: "wx" }
            );

            await fs.rename(temporary, destination);

            this.recordEvent(
                document,
                actorId,
                "DOCUMENT_EXPORTED",
                { filename }
            );

            return destination;

        } catch (error) {
            await fs.rm(temporary, { force: true }).catch(() => {});
            throw error;
        }
    }

    // ------------------------------------------------------
    // PROJECT REPORT
    // ------------------------------------------------------

    generateReport(projectId, actorId) {
        this.getActiveUser(actorId);

        const documents = this.repository.list(projectId);

        const statusCounts = Object.fromEntries(
            Object.values(DocumentStatus).map(status => [status, 0])
        );

        const typeCounts = Object.fromEntries(
            Object.values(DocumentType).map(type => [type, 0])
        );

        for (const document of documents) {
            statusCounts[document.status]++;
            typeCounts[document.type]++;
        }

        return {
            projectId,
            totalDocuments: documents.length,
            statusCounts,
            typeCounts,
            totalVersions: documents.reduce(
                (sum, document) => sum + document.versions.length,
                0
            ),
            pendingReviews: statusCounts.under_review
        };
    }

    // ------------------------------------------------------
    // AUDIT RETRIEVAL
    // ------------------------------------------------------

    getAuditHistory(documentId, actorId) {
        this.authorize(actorId, [
            Role.ADMIN,
            Role.PROJECT_MANAGER
        ]);

        return this.auditLog
            .filter(event => event.documentId === documentId)
            .map(event => structuredClone(event));
    }
}

// ==========================================================
// EXECUTABLE TEST SCENARIO
// ==========================================================

async function main() {
    const service = new DocumentationService();

    service.on("document:event", event => {
        console.log(
            `[EVENT] ${event.action} | ${event.documentId}`
        );
    });

    const admin = service.registerUser(
        "Administrator",
        "admin@example.com",
        Role.ADMIN
    );

    const author = service.registerUser(
        "Technical Author",
        "author@example.com",
        Role.AUTHOR
    );

    const reviewer = service.registerUser(
        "Reviewer",
        "reviewer@example.com",
        Role.REVIEWER
    );

    const project = service.createProject(
        admin.id,
        "Enterprise Documentation Platform"
    );

    const document = service.createDocument({
        actorId: author.id,
        projectId: project.id,
        title: "System Requirements",
        type: DocumentType.REQUIREMENTS,
        content: "The platform must provide secure document storage.",
        tags: ["requirements", "security"]
    });

    await service.updateDocument({
        documentId: document.id,
        actorId: author.id,
        content:
            "The platform must provide secure storage, " +
            "version control and document approval.",
        changeDescription: "Expanded requirements.",
        expectedVersion: 1
    });

    service.submitForReview(document.id, author.id);

    service.reviewDocument({
        documentId: document.id,
        reviewerId: reviewer.id,
        decision: Decision.APPROVED,
        comments: "The requirements are sufficiently complete."
    });

    const integrity = service.verifyDocumentIntegrity(
        document.id,
        author.id
    );

    console.log("\nVERSION INTEGRITY");
    console.log(integrity);

    const results = service.searchDocuments(
        project.id,
        author.id,
        "version control"
    );

    console.log("\nSEARCH RESULTS");
    console.log(results.map(item => item.title));

    const report = service.generateReport(
        project.id,
        admin.id
    );

    console.log("\nPROJECT REPORT");
    console.log(JSON.stringify(report, null, 2));

    const outputDirectory = path.join(
        process.cwd(),
        "project-document-exports"
    );

    const exportedFile = await service.exportDocument(
        document.id,
        author.id,
        outputDirectory
    );

    console.log("\nEXPORTED:", exportedFile);

    // Verify stale update rejection.
    try {
        await service.updateDocument({
            documentId: document.id,
            actorId: author.id,
            content: "Outdated update.",
            changeDescription: "Conflict test",
            expectedVersion: 1
        });
    } catch (error) {
        if (!(error instanceof VersionConflictError)) {
            throw error;
        }

        console.log("\nEXPECTED CONFLICT:", error.message);
    }

    // Verify author cannot approve their own document.
    const second = service.createDocument({
        actorId: author.id,
        projectId: project.id,
        title: "Architecture Design",
        type: DocumentType.DESIGN,
        content: "The system follows a modular architecture."
    });

    service.submitForReview(second.id, author.id);

    try {
        service.reviewDocument({
            documentId: second.id,
            reviewerId: author.id,
            decision: Decision.APPROVED,
            comments: "Self-approval attempt."
        });
    } catch (error) {
        if (!(error instanceof AuthorizationError)) {
            throw error;
        }

        console.log("\nEXPECTED PERMISSION ERROR:", error.message);
    }

    console.log("\nAll JavaScript tests completed.");
}

if (require.main === module) {
    main().catch(error => {
        console.error("APPLICATION FAILURE:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    DocumentationService,
    DocumentType,
    DocumentStatus,
    Role,
    Decision
};
