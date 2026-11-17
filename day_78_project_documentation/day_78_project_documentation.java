import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Enterprise Project Documentation Management System.
 *
 * Java version: 17
 * External dependencies: None.
 *
 * Features:
 * - Project and document management
 * - Immutable document versions
 * - Role-based authorization
 * - Review and approval workflow
 * - State transition validation
 * - Version conflict detection
 * - Integrity verification
 * - Audit history
 * - Project reporting
 */
public class ProjectDocumentationManager {

    // ========================================================
    // ENUMERATIONS
    // ========================================================

    enum DocumentType {
        REQUIREMENTS,
        PROJECT_PLAN,
        TECHNICAL_SPECIFICATION,
        DESIGN,
        MEETING_MINUTES,
        PROGRESS_REPORT,
        RISK_REGISTER,
        TEST_REPORT,
        USER_GUIDE,
        CLOSURE_REPORT
    }

    enum DocumentStatus {
        DRAFT,
        UNDER_REVIEW,
        APPROVED,
        REJECTED,
        ARCHIVED
    }

    enum Role {
        ADMIN,
        PROJECT_MANAGER,
        AUTHOR,
        REVIEWER,
        VIEWER
    }

    enum Decision {
        APPROVED,
        REJECTED,
        CHANGES_REQUESTED
    }

    // ========================================================
    // CUSTOM EXCEPTIONS
    // ========================================================

    static class DocumentationException extends RuntimeException {
        DocumentationException(String message) {
            super(message);
        }
    }

    static class ValidationException extends DocumentationException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class AuthorizationException extends DocumentationException {
        AuthorizationException(String message) {
            super(message);
        }
    }

    static class StateException extends DocumentationException {
        StateException(String message) {
            super(message);
        }
    }

    static class VersionConflictException extends DocumentationException {
        VersionConflictException(String message) {
            super(message);
        }
    }

    // ========================================================
    // VALIDATION UTILITIES
    // ========================================================

    static String requiredText(
        String value,
        String field,
        int maximumLength
    ) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(
                field + " is required."
            );
        }

        if (value.length() > maximumLength) {
            throw new ValidationException(
                field + " exceeds its size limit."
            );
        }

        return value.trim();
    }

    static String validateEmail(String email) {

        String normalized = requiredText(
            email,
            "Email",
            254
        ).toLowerCase();

        if (!normalized.matches(
            "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$"
        )) {
            throw new ValidationException(
                "Invalid email address."
            );
        }

        return normalized;
    }

    // ========================================================
    // HASHING
    // ========================================================

    static String sha256(String content) {

        try {

            MessageDigest digest =
                MessageDigest.getInstance("SHA-256");

            byte[] bytes = digest.digest(
                content.getBytes(StandardCharsets.UTF_8)
            );

            StringBuilder result = new StringBuilder();

            for (byte value : bytes) {
                result.append(
                    String.format("%02x", value & 0xff)
                );
            }

            return result.toString();

        } catch (NoSuchAlgorithmException exception) {

            throw new DocumentationException(
                "SHA-256 is unavailable."
            );
        }
    }

    // ========================================================
    // DOMAIN RECORDS
    // ========================================================

    record User(
        UUID id,
        String name,
        String email,
        Role role,
        boolean active
    ) {}

    record Project(
        UUID id,
        String name,
        UUID managerId,
        Instant createdAt
    ) {}

    record DocumentVersion(
        UUID id,
        int number,
        String content,
        String checksum,
        UUID authorId,
        String changeDescription,
        Instant createdAt
    ) {}

    record Review(
        UUID id,
        UUID reviewerId,
        int version,
        Decision decision,
        String comments,
        Instant createdAt
    ) {}

    record AuditEvent(
        UUID id,
        UUID documentId,
        UUID actorId,
        String action,
        String details,
        Instant timestamp
    ) {}

    record DocumentSnapshot(
        UUID id,
        UUID projectId,
        String title,
        DocumentType type,
        UUID ownerId,
        DocumentStatus status,
        int currentVersion,
        List<DocumentVersion> versions,
        List<Review> reviews,
        Set<String> tags,
        Instant createdAt,
        Instant updatedAt
    ) {}

    record ProjectReport(
        UUID projectId,
        int totalDocuments,
        int totalVersions,
        Map<DocumentStatus, Long> statusDistribution,
        Map<DocumentType, Long> typeDistribution
    ) {}

    // ========================================================
    // DOCUMENT ENTITY
    // ========================================================

    static final class ProjectDocument {

        private final UUID id;
        private final UUID projectId;
        private final String title;
        private final DocumentType type;
        private final UUID ownerId;
        private final Instant createdAt;

        private DocumentStatus status;
        private int currentVersion;

        private final List<DocumentVersion> versions;
        private final List<Review> reviews;
        private final Set<String> tags;

        private Instant updatedAt;

        ProjectDocument(
            UUID id,
            UUID projectId,
            String title,
            DocumentType type,
            UUID ownerId,
            DocumentVersion initialVersion,
            Set<String> tags
        ) {
            this.id = id;
            this.projectId = projectId;
            this.title = title;
            this.type = type;
            this.ownerId = ownerId;

            this.status = DocumentStatus.DRAFT;
            this.currentVersion = 1;

            this.versions = new ArrayList<>();
            this.reviews = new ArrayList<>();
            this.tags = new HashSet<>(tags);

            this.versions.add(initialVersion);

            this.createdAt = Instant.now();
            this.updatedAt = this.createdAt;
        }

        DocumentVersion latestVersion() {
            return versions.get(versions.size() - 1);
        }

        void transition(DocumentStatus next) {

            boolean allowed = switch (status) {

                case DRAFT ->
                    next == DocumentStatus.UNDER_REVIEW ||
                    next == DocumentStatus.ARCHIVED;

                case UNDER_REVIEW ->
                    next == DocumentStatus.DRAFT ||
                    next == DocumentStatus.APPROVED ||
                    next == DocumentStatus.REJECTED;

                case APPROVED, REJECTED ->
                    next == DocumentStatus.DRAFT ||
                    next == DocumentStatus.ARCHIVED;

                case ARCHIVED -> false;
            };

            if (!allowed) {
                throw new StateException(
                    "Invalid transition: " +
                    status + " -> " + next
                );
            }

            status = next;
            updatedAt = Instant.now();
        }

        DocumentSnapshot snapshot() {

            return new DocumentSnapshot(
                id,
                projectId,
                title,
                type,
                ownerId,
                status,
                currentVersion,
                List.copyOf(versions),
                List.copyOf(reviews),
                Set.copyOf(tags),
                createdAt,
                updatedAt
            );
        }
    }

    // ========================================================
    // REVIEW POLICY
    // ========================================================

    static final class ReviewPolicy {

        private final int requiredApprovals;
        private final boolean prohibitSelfApproval;

        ReviewPolicy(
            int requiredApprovals,
            boolean prohibitSelfApproval
        ) {
            if (requiredApprovals < 1) {
                throw new ValidationException(
                    "At least one approval is required."
                );
            }

            this.requiredApprovals = requiredApprovals;
            this.prohibitSelfApproval = prohibitSelfApproval;
        }

        boolean isProhibitSelfApproval() {
            return prohibitSelfApproval;
        }

        int requiredApprovals() {
            return requiredApprovals;
        }
    }

    // ========================================================
    // REPOSITORY LAYER
    // ========================================================

    static final class DocumentRepository {

        private final Map<UUID, ProjectDocument> documents =
            new HashMap<>();

        synchronized void save(ProjectDocument document) {
            documents.put(document.id, document);
        }

        synchronized ProjectDocument find(UUID documentId) {

            ProjectDocument document = documents.get(documentId);

            if (document == null) {
                throw new DocumentationException(
                    "Document not found."
                );
            }

            return document;
        }

        synchronized List<ProjectDocument> findByProject(
            UUID projectId
        ) {
            return documents.values()
                .stream()
                .filter(document ->
                    document.projectId.equals(projectId)
                )
                .toList();
        }
    }

    // ========================================================
    // DOCUMENT MANAGEMENT SERVICE
    // ========================================================

    static final class DocumentationService {

        private final Map<UUID, User> users = new HashMap<>();

        private final Map<String, UUID> emailIndex =
            new HashMap<>();

        private final Map<UUID, Project> projects =
            new HashMap<>();

        private final DocumentRepository repository =
            new DocumentRepository();

        private final List<AuditEvent> auditLog =
            Collections.synchronizedList(new ArrayList<>());

        private final ReviewPolicy reviewPolicy;

        DocumentationService(ReviewPolicy reviewPolicy) {
            this.reviewPolicy = Objects.requireNonNull(
                reviewPolicy
            );
        }

        // ----------------------------------------------------
        // USER MANAGEMENT
        // ----------------------------------------------------

        synchronized User registerUser(
            String name,
            String email,
            Role role
        ) {
            String safeName = requiredText(
                name,
                "Name",
                200
            );

            String safeEmail = validateEmail(email);

            if (emailIndex.containsKey(safeEmail)) {
                throw new ValidationException(
                    "Email already registered."
                );
            }

            User user = new User(
                UUID.randomUUID(),
                safeName,
                safeEmail,
                Objects.requireNonNull(role),
                true
            );

            users.put(user.id(), user);
            emailIndex.put(safeEmail, user.id());

            return user;
        }

        private User getUser(UUID userId) {

            User user = users.get(userId);

            if (user == null || !user.active()) {
                throw new AuthorizationException(
                    "User is unavailable."
                );
            }

            return user;
        }

        private User authorize(
            UUID userId,
            Set<Role> allowedRoles
        ) {
            User user = getUser(userId);

            if (!allowedRoles.contains(user.role())) {
                throw new AuthorizationException(
                    "Insufficient permissions."
                );
            }

            return user;
        }

        // ----------------------------------------------------
        // AUDIT
        // ----------------------------------------------------

        private void audit(
            UUID documentId,
            UUID actorId,
            String action,
            String details
        ) {
            auditLog.add(
                new AuditEvent(
                    UUID.randomUUID(),
                    documentId,
                    actorId,
                    action,
                    details,
                    Instant.now()
                )
            );
        }

        // ----------------------------------------------------
        // PROJECT MANAGEMENT
        // ----------------------------------------------------

        synchronized Project createProject(
            UUID actorId,
            String name
        ) {
            User manager = authorize(
                actorId,
                Set.of(Role.ADMIN, Role.PROJECT_MANAGER)
            );

            Project project = new Project(
                UUID.randomUUID(),
                requiredText(name, "Project name", 200),
                manager.id(),
                Instant.now()
            );

            projects.put(project.id(), project);

            return project;
        }

        // ----------------------------------------------------
        // DOCUMENT CREATION
        // ----------------------------------------------------

        synchronized DocumentSnapshot createDocument(
            UUID actorId,
            UUID projectId,
            String title,
            DocumentType type,
            String content,
            Set<String> tags
        ) {
            authorize(
                actorId,
                Set.of(
                    Role.ADMIN,
                    Role.PROJECT_MANAGER,
                    Role.AUTHOR
                )
            );

            if (!projects.containsKey(projectId)) {
                throw new ValidationException(
                    "Project not found."
                );
            }

            String safeTitle = requiredText(
                title,
                "Title",
                200
            );

            String safeContent = requiredText(
                content,
                "Content",
                5_000_000
            );

            Objects.requireNonNull(type);

            Set<String> safeTags = tags.stream()
                .map(tag -> requiredText(tag, "Tag", 100).toLowerCase())
                .collect(Collectors.toSet());

            DocumentVersion initial = new DocumentVersion(
                UUID.randomUUID(),
                1,
                safeContent,
                sha256(safeContent),
                actorId,
                "Initial creation",
                Instant.now()
            );

            ProjectDocument document = new ProjectDocument(
                UUID.randomUUID(),
                projectId,
                safeTitle,
                type,
                actorId,
                initial,
                safeTags
            );

            repository.save(document);

            audit(
                document.id,
                actorId,
                "DOCUMENT_CREATED",
                "Version 1"
            );

            return document.snapshot();
        }

        // ----------------------------------------------------
        // VERSION MANAGEMENT
        // ----------------------------------------------------

        synchronized DocumentVersion updateDocument(
            UUID documentId,
            UUID actorId,
            String content,
            String description,
            int expectedVersion
        ) {
            User actor = authorize(
                actorId,
                Set.of(
                    Role.ADMIN,
                    Role.PROJECT_MANAGER,
                    Role.AUTHOR
                )
            );

            ProjectDocument document =
                repository.find(documentId);

            if (
                actor.role() == Role.AUTHOR &&
                !document.ownerId.equals(actorId)
            ) {
                throw new AuthorizationException(
                    "Authors can update only their own documents."
                );
            }

            if (document.status == DocumentStatus.ARCHIVED) {
                throw new StateException(
                    "Archived documents cannot be modified."
                );
            }

            if (document.currentVersion != expectedVersion) {
                throw new VersionConflictException(
                    "Document version has changed."
                );
            }

            String safeContent = requiredText(
                content,
                "Content",
                5_000_000
            );

            String safeDescription = requiredText(
                description,
                "Change description",
                500
            );

            int nextVersion = document.currentVersion + 1;

            DocumentVersion version = new DocumentVersion(
                UUID.randomUUID(),
                nextVersion,
                safeContent,
                sha256(safeContent),
                actorId,
                safeDescription,
                Instant.now()
            );

            document.versions.add(version);
            document.currentVersion = nextVersion;

            if (
                document.status == DocumentStatus.APPROVED ||
                document.status == DocumentStatus.REJECTED ||
                document.status == DocumentStatus.UNDER_REVIEW
            ) {
                document.transition(DocumentStatus.DRAFT);
            }

            document.updatedAt = Instant.now();

            audit(
                documentId,
                actorId,
                "VERSION_CREATED",
                "Version " + nextVersion
            );

            return version;
        }

        // ----------------------------------------------------
        // REVIEW SUBMISSION
        // ----------------------------------------------------

        synchronized void submitForReview(
            UUID documentId,
            UUID actorId
        ) {
            ProjectDocument document =
                repository.find(documentId);

            User actor = getUser(actorId);

            if (
                !document.ownerId.equals(actorId) &&
                actor.role() != Role.ADMIN &&
                actor.role() != Role.PROJECT_MANAGER
            ) {
                throw new AuthorizationException(
                    "Not permitted to submit this document."
                );
            }

            document.transition(
                DocumentStatus.UNDER_REVIEW
            );

            audit(
                documentId,
                actorId,
                "SUBMITTED_FOR_REVIEW",
                "Current version"
            );
        }

        // ----------------------------------------------------
        // REVIEW AND APPROVAL
        // ----------------------------------------------------

        synchronized Review reviewDocument(
            UUID documentId,
            UUID reviewerId,
            Decision decision,
            String comments
        ) {
            User reviewer = authorize(
                reviewerId,
                Set.of(
                    Role.ADMIN,
                    Role.PROJECT_MANAGER,
                    Role.REVIEWER
                )
            );

            ProjectDocument document =
                repository.find(documentId);

            if (
                reviewPolicy.isProhibitSelfApproval() &&
                document.ownerId.equals(reviewerId)
            ) {
                throw new AuthorizationException(
                    "Self-approval is prohibited."
                );
            }

            if (document.status != DocumentStatus.UNDER_REVIEW) {
                throw new StateException(
                    "Document is not under review."
                );
            }

            String safeComments = requiredText(
                comments,
                "Review comments",
                5000
            );

            Review review = new Review(
                UUID.randomUUID(),
                reviewer.id(),
                document.currentVersion,
                decision,
                safeComments,
                Instant.now()
            );

            document.reviews.add(review);

            switch (decision) {

                case APPROVED ->
                    document.transition(DocumentStatus.APPROVED);

                case REJECTED ->
                    document.transition(DocumentStatus.REJECTED);

                case CHANGES_REQUESTED ->
                    document.transition(DocumentStatus.DRAFT);
            }

            audit(
                documentId,
                reviewerId,
                "REVIEW_COMPLETED",
                decision.name()
            );

            return review;
        }

        // ----------------------------------------------------
        // MULTI-APPROVER POLICY EVALUATION
        // ----------------------------------------------------

        synchronized boolean hasRequiredApprovals(
            UUID documentId
        ) {
            ProjectDocument document =
                repository.find(documentId);

            int version = document.currentVersion;

            Set<UUID> approvers = document.reviews.stream()
                .filter(review -> review.version() == version)
                .filter(review -> review.decision() == Decision.APPROVED)
                .map(Review::reviewerId)
                .collect(Collectors.toSet());

            return approvers.size() >=
                reviewPolicy.requiredApprovals();
        }

        // ----------------------------------------------------
        // DOCUMENT ARCHIVING
        // ----------------------------------------------------

        synchronized void archiveDocument(
            UUID documentId,
            UUID actorId
        ) {
            authorize(
                actorId,
                Set.of(Role.ADMIN, Role.PROJECT_MANAGER)
            );

            ProjectDocument document =
                repository.find(documentId);

            document.transition(DocumentStatus.ARCHIVED);

            audit(
                documentId,
                actorId,
                "DOCUMENT_ARCHIVED",
                "Archived"
            );
        }

        // ----------------------------------------------------
        // DOCUMENT RETRIEVAL
        // ----------------------------------------------------

        DocumentSnapshot getDocument(
            UUID documentId,
            UUID actorId
        ) {
            getUser(actorId);

            return repository.find(documentId).snapshot();
        }

        // ----------------------------------------------------
        // SEARCH
        // ----------------------------------------------------

        List<DocumentSnapshot> searchDocuments(
            UUID projectId,
            UUID actorId,
            String keyword
        ) {
            getUser(actorId);

            String query = requiredText(
                keyword,
                "Search keyword",
                200
            ).toLowerCase();

            return repository.findByProject(projectId)
                .stream()
                .filter(document -> {
                    String searchable =
                        document.title + " " +
                        document.latestVersion().content() + " " +
                        String.join(" ", document.tags);

                    return searchable.toLowerCase().contains(query);
                })
                .map(ProjectDocument::snapshot)
                .toList();
        }

        // ----------------------------------------------------
        // INTEGRITY VERIFICATION
        // ----------------------------------------------------

        boolean verifyIntegrity(
            UUID documentId,
            UUID actorId
        ) {
            getUser(actorId);

            ProjectDocument document =
                repository.find(documentId);

            return document.versions.stream().allMatch(
                version ->
                    sha256(version.content()).equals(version.checksum())
            );
        }

        // ----------------------------------------------------
        // PROJECT REPORT
        // ----------------------------------------------------

        ProjectReport generateReport(
            UUID projectId,
            UUID actorId
        ) {
            getUser(actorId);

            if (!projects.containsKey(projectId)) {
                throw new ValidationException(
                    "Project not found."
                );
            }

            List<ProjectDocument> documents =
                repository.findByProject(projectId);

            Map<DocumentStatus, Long> statuses =
                new EnumMap<>(DocumentStatus.class);

            Map<DocumentType, Long> types =
                new EnumMap<>(DocumentType.class);

            for (DocumentStatus status : DocumentStatus.values()) {
                statuses.put(status, 0L);
            }

            for (DocumentType type : DocumentType.values()) {
                types.put(type, 0L);
            }

            documents.forEach(document -> {
                statuses.merge(document.status, 1L, Long::sum);
                types.merge(document.type, 1L, Long::sum);
            });

            int totalVersions = documents.stream()
                .mapToInt(document -> document.versions.size())
                .sum();

            return new ProjectReport(
                projectId,
                documents.size(),
                totalVersions,
                Map.copyOf(statuses),
                Map.copyOf(types)
            );
        }

        // ----------------------------------------------------
        // AUDIT HISTORY
        // ----------------------------------------------------

        synchronized List<AuditEvent> getAuditHistory(
            UUID documentId,
            UUID actorId
        ) {
            authorize(
                actorId,
                Set.of(Role.ADMIN, Role.PROJECT_MANAGER)
            );

            repository.find(documentId);

            return auditLog.stream()
                .filter(event ->
                    event.documentId().equals(documentId)
                )
                .toList();
        }
    }

    // ========================================================
    // EXECUTABLE DEMONSTRATION
    // ========================================================

    public static void main(String[] args) {

        DocumentationService service =
            new DocumentationService(
                new ReviewPolicy(1, true)
            );

        User admin = service.registerUser(
            "Administrator",
            "admin@example.com",
            Role.ADMIN
        );

        User author = service.registerUser(
            "Technical Author",
            "author@example.com",
            Role.AUTHOR
        );

        User reviewer = service.registerUser(
            "Technical Reviewer",
            "reviewer@example.com",
            Role.REVIEWER
        );

        Project project = service.createProject(
            admin.id(),
            "Enterprise Documentation Platform"
        );

        DocumentSnapshot document = service.createDocument(
            author.id(),
            project.id(),
            "System Requirements",
            DocumentType.REQUIREMENTS,
            "The system must support secure document storage.",
            Set.of("requirements", "security")
        );

        DocumentVersion secondVersion =
            service.updateDocument(
                document.id(),
                author.id(),
                "The system must support secure storage, " +
                "version history and approval workflows.",
                "Added governance requirements.",
                1
            );

        service.submitForReview(
            document.id(),
            author.id()
        );

        Review review = service.reviewDocument(
            document.id(),
            reviewer.id(),
            Decision.APPROVED,
            "The requirements are complete."
        );

        DocumentSnapshot approved =
            service.getDocument(
                document.id(),
                author.id()
            );

        System.out.println("\nDOCUMENT DETAILS");

        System.out.println("Title: " + approved.title());

        System.out.println("Version: " + approved.currentVersion());

        System.out.println("Status: " + approved.status());

        System.out.println(
            "Approval requirement satisfied: " +
            service.hasRequiredApprovals(document.id())
        );

        System.out.println(
            "Integrity valid: " +
            service.verifyIntegrity(document.id(), author.id())
        );

        System.out.println("\nPROJECT REPORT");

        ProjectReport report = service.generateReport(
            project.id(),
            admin.id()
        );

        System.out.println(report);

        System.out.println("\nSEARCH RESULTS");

        List<DocumentSnapshot> search =
            service.searchDocuments(
                project.id(),
                author.id(),
                "secure storage"
            );

        search.forEach(item ->
            System.out.println(item.title())
        );

        System.out.println("\nAUDIT EVENTS");

        service.getAuditHistory(
            document.id(),
            admin.id()
        ).forEach(System.out::println);

        // Stale version rejection.
        try {

            service.updateDocument(
                document.id(),
                author.id(),
                "Outdated content.",
                "Version conflict test.",
                1
            );

        } catch (VersionConflictException exception) {

            System.out.println(
                "\nEXPECTED VERSION CONFLICT: " +
                exception.getMessage()
            );
        }

        // Self-approval rejection.
        DocumentSnapshot second = service.createDocument(
            author.id(),
            project.id(),
            "Architecture Design",
            DocumentType.DESIGN,
            "The system follows a modular architecture.",
            Set.of("architecture")
        );

        service.submitForReview(second.id(), author.id());

        try {

            service.reviewDocument(
                second.id(),
                author.id(),
                Decision.APPROVED,
                "Self-approval attempt."
            );

        } catch (AuthorizationException exception) {

            System.out.println(
                "\nEXPECTED PERMISSION DENIAL: " +
                exception.getMessage()
            );
        }

        System.out.println(
            "\nJava 17 demonstration completed successfully."
        );
    }
}
