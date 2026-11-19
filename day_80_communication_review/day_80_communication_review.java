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

public class CommunicationGovernance {

    enum CommunicationType {
        EMAIL, MEETING, REPORT, PRESENTATION, NOTICE
    }

    enum Status {
        DRAFT,
        SUBMITTED,
        UNDER_REVIEW,
        REVISION_REQUIRED,
        REJECTED,
        APPROVED,
        PUBLISHED,
        ARCHIVED
    }

    enum Decision {
        APPROVE, REVISE, REJECT
    }

    enum Severity {
        LOW, MEDIUM, HIGH, CRITICAL
    }

    enum Sensitivity {
        PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    }

    record Stakeholder(
        String id,
        String name,
        String role,
        String department,
        boolean active
    ) {
        Stakeholder {
            Objects.requireNonNull(id);
            Objects.requireNonNull(name);
            Objects.requireNonNull(role);
            Objects.requireNonNull(department);

            if (
                id.isBlank() ||
                name.isBlank() ||
                role.isBlank() ||
                department.isBlank()
            ) {
                throw new IllegalArgumentException(
                    "Stakeholder fields cannot be blank."
                );
            }
        }
    }

    record ReviewPolicy(
        int requiredApprovals,
        double minimumScore,
        boolean blockCriticalComments,
        double minimumDeliveryRate,
        double minimumAcknowledgementRate
    ) {
        ReviewPolicy {
            if (requiredApprovals < 1) {
                throw new IllegalArgumentException(
                    "At least one approval is required."
                );
            }

            if (
                !Double.isFinite(minimumScore) ||
                minimumScore < 0 ||
                minimumScore > 100
            ) {
                throw new IllegalArgumentException(
                    "Invalid minimum score."
                );
            }

            if (
                minimumDeliveryRate < 0 ||
                minimumDeliveryRate > 100 ||
                minimumAcknowledgementRate < 0 ||
                minimumAcknowledgementRate > 100
            ) {
                throw new IllegalArgumentException(
                    "Invalid communication performance thresholds."
                );
            }
        }
    }

    record ReviewCriterion(String name, double score) {
        ReviewCriterion {
            Objects.requireNonNull(name);

            if (
                name.isBlank() ||
                !Double.isFinite(score) ||
                score < 0 ||
                score > 100
            ) {
                throw new IllegalArgumentException(
                    "Invalid review criterion."
                );
            }
        }
    }

    record Review(
        String id,
        String reviewerId,
        String communicationId,
        Decision decision,
        double averageScore,
        String feedback,
        int version,
        Instant reviewedAt
    ) {}

    record ReviewComment(
        String id,
        String communicationId,
        String reviewerId,
        String criterion,
        String message,
        Severity severity,
        boolean resolved,
        Instant createdAt
    ) {}

    record EligibilityResult(
        boolean eligible,
        int validApprovals,
        double averageScore,
        List<String> reasons
    ) {
        EligibilityResult {
            reasons = List.copyOf(reasons);
        }
    }

    record DeliveryMetrics(
        int recipients,
        int delivered,
        int read,
        int acknowledged,
        double deliveryRate,
        double readRate,
        double acknowledgementRate,
        boolean deliveryTargetMet,
        boolean acknowledgementTargetMet
    ) {}

    static class CommunicationException extends RuntimeException {
        CommunicationException(String message) {
            super(message);
        }
    }

    static class AuthorizationException extends CommunicationException {
        AuthorizationException(String message) {
            super(message);
        }
    }

    static class WorkflowException extends CommunicationException {
        WorkflowException(String message) {
            super(message);
        }
    }

    static class Communication {
        private final String id;
        private final String title;
        private final CommunicationType type;
        private final String senderId;
        private final List<String> recipients;
        private final String subject;
        private String content;
        private final List<String> objectives;
        private final Sensitivity sensitivity;
        private final boolean acknowledgementRequired;

        private Status status = Status.DRAFT;
        private int version = 1;

        private int delivered;
        private int read;
        private int acknowledged;

        private final Instant createdAt = Instant.now();

        Communication(
            String title,
            CommunicationType type,
            String senderId,
            List<String> recipients,
            String subject,
            String content,
            List<String> objectives,
            Sensitivity sensitivity,
            boolean acknowledgementRequired
        ) {
            this.id = UUID.randomUUID().toString();
            this.title = title;
            this.type = type;
            this.senderId = senderId;
            this.recipients = List.copyOf(recipients);
            this.subject = subject;
            this.content = content;
            this.objectives = List.copyOf(objectives);
            this.sensitivity = sensitivity;
            this.acknowledgementRequired = acknowledgementRequired;
        }

        public String id() {
            return id;
        }

        public Status status() {
            return status;
        }

        public int version() {
            return version;
        }

        public String senderId() {
            return senderId;
        }

        public List<String> recipients() {
            return recipients;
        }

        public boolean acknowledgementRequired() {
            return acknowledgementRequired;
        }

        public int delivered() {
            return delivered;
        }

        public int read() {
            return read;
        }

        public int acknowledged() {
            return acknowledged;
        }
    }

    interface AuditService {
        void record(String action, String entityId, String actorId);
    }

    static class InMemoryAuditService implements AuditService {
        private final List<String> events = new ArrayList<>();

        @Override
        public void record(
            String action,
            String entityId,
            String actorId
        ) {
            events.add(
                Instant.now() + " | " +
                action + " | " +
                entityId + " | " +
                actorId
            );
        }

        public List<String> events() {
            return Collections.unmodifiableList(events);
        }
    }

    static class ReviewService {
        private static final Set<String> REQUIRED_CRITERIA = Set.of(
            "clarity",
            "accuracy",
            "completeness",
            "audience_alignment",
            "timeliness",
            "actionability",
            "professionalism"
        );

        private final ReviewPolicy policy;

        private final Map<String, Stakeholder> stakeholders =
            new HashMap<>();

        private final Map<String, Communication> communications =
            new HashMap<>();

        private final Map<String, List<Review>> reviews =
            new HashMap<>();

        private final Map<String, List<ReviewComment>> comments =
            new HashMap<>();

        private final AuditService auditService;

        ReviewService(ReviewPolicy policy, AuditService auditService) {
            this.policy = Objects.requireNonNull(policy);
            this.auditService = Objects.requireNonNull(auditService);
        }

        void registerStakeholder(Stakeholder stakeholder) {
            Objects.requireNonNull(stakeholder);

            if (stakeholders.containsKey(stakeholder.id())) {
                throw new CommunicationException(
                    "Duplicate stakeholder."
                );
            }

            stakeholders.put(stakeholder.id(), stakeholder);
        }

        private Stakeholder getStakeholder(String id) {
            Stakeholder stakeholder = stakeholders.get(id);

            if (stakeholder == null) {
                throw new CommunicationException(
                    "Stakeholder not found: " + id
                );
            }

            return stakeholder;
        }

        private Communication getCommunication(String id) {
            Communication communication = communications.get(id);

            if (communication == null) {
                throw new CommunicationException(
                    "Communication not found."
                );
            }

            return communication;
        }

        String createCommunication(
            String title,
            CommunicationType type,
            String senderId,
            List<String> recipients,
            String subject,
            String content,
            List<String> objectives,
            Sensitivity sensitivity,
            boolean acknowledgementRequired
        ) {
            requireText(title, "Title");
            requireText(subject, "Subject");
            requireText(content, "Content");

            Objects.requireNonNull(type);
            Objects.requireNonNull(sensitivity);

            Stakeholder sender = getStakeholder(senderId);

            if (!sender.active()) {
                throw new AuthorizationException("Inactive sender.");
            }

            if (recipients == null || recipients.isEmpty()) {
                throw new IllegalArgumentException(
                    "Recipients are required."
                );
            }

            if (new HashSet<>(recipients).size() != recipients.size()) {
                throw new IllegalArgumentException(
                    "Duplicate recipients are not allowed."
                );
            }

            for (String recipientId : recipients) {
                if (!getStakeholder(recipientId).active()) {
                    throw new AuthorizationException(
                        "Inactive recipient."
                    );
                }
            }

            if (objectives == null || objectives.isEmpty()) {
                throw new IllegalArgumentException(
                    "Communication objectives are required."
                );
            }

            Communication communication = new Communication(
                title,
                type,
                senderId,
                recipients,
                subject,
                content,
                objectives,
                sensitivity,
                acknowledgementRequired
            );

            communications.put(communication.id(), communication);
            reviews.put(communication.id(), new ArrayList<>());
            comments.put(communication.id(), new ArrayList<>());

            auditService.record(
                "COMMUNICATION_CREATED",
                communication.id(),
                senderId
            );

            return communication.id();
        }

        private void requireText(String value, String field) {
            if (value == null || value.isBlank()) {
                throw new IllegalArgumentException(
                    field + " is required."
                );
            }
        }

        private void transition(
            Communication communication,
            Status next,
            String actorId
        ) {
            Map<Status, Set<Status>> allowed =
                new EnumMap<>(Status.class);

            allowed.put(Status.DRAFT, Set.of(Status.SUBMITTED));
            allowed.put(
                Status.SUBMITTED,
                Set.of(Status.UNDER_REVIEW, Status.REJECTED)
            );
            allowed.put(
                Status.UNDER_REVIEW,
                Set.of(
                    Status.APPROVED,
                    Status.REJECTED,
                    Status.REVISION_REQUIRED
                )
            );
            allowed.put(
                Status.REVISION_REQUIRED,
                Set.of(Status.SUBMITTED)
            );
            allowed.put(Status.APPROVED, Set.of(Status.PUBLISHED));
            allowed.put(Status.PUBLISHED, Set.of(Status.ARCHIVED));
            allowed.put(Status.REJECTED, Set.of(Status.ARCHIVED));
            allowed.put(Status.ARCHIVED, Set.of());

            if (!allowed.get(communication.status).contains(next)) {
                throw new WorkflowException(
                    "Invalid transition from " +
                    communication.status + " to " + next
                );
            }

            Status previous = communication.status;
            communication.status = next;

            auditService.record(
                previous + "_TO_" + next,
                communication.id(),
                actorId
            );
        }

        void submit(String id, String actorId) {
            Communication communication = getCommunication(id);

            if (!communication.senderId().equals(actorId)) {
                throw new AuthorizationException(
                    "Only the sender can submit."
                );
            }

            transition(communication, Status.SUBMITTED, actorId);
        }

        void beginReview(String id, String reviewerId) {
            Communication communication = getCommunication(id);
            Stakeholder reviewer = getStakeholder(reviewerId);

            if (!reviewer.active()) {
                throw new AuthorizationException("Reviewer is inactive.");
            }

            if (reviewerId.equals(communication.senderId())) {
                throw new AuthorizationException(
                    "Self-review is prohibited."
                );
            }

            if (communication.status() == Status.SUBMITTED) {
                transition(
                    communication,
                    Status.UNDER_REVIEW,
                    reviewerId
                );
            } else if (communication.status() != Status.UNDER_REVIEW) {
                throw new WorkflowException(
                    "Communication is not available for review."
                );
            }
        }

        void addComment(
            String id,
            String reviewerId,
            String criterion,
            String message,
            Severity severity
        ) {
            Communication communication = getCommunication(id);
            getStakeholder(reviewerId);

            if (reviewerId.equals(communication.senderId())) {
                throw new AuthorizationException("Self-review is prohibited.");
            }

            if (communication.status() != Status.UNDER_REVIEW) {
                throw new WorkflowException("Review is not active.");
            }

            requireText(criterion, "Criterion");
            requireText(message, "Comment");

            comments.get(id).add(
                new ReviewComment(
                    UUID.randomUUID().toString(),
                    id,
                    reviewerId,
                    criterion,
                    message,
                    severity,
                    false,
                    Instant.now()
                )
            );

            auditService.record("COMMENT_ADDED", id, reviewerId);
        }

        void resolveComment(
            String id,
            String commentId,
            String actorId
        ) {
            Communication communication = getCommunication(id);

            if (!communication.senderId().equals(actorId)) {
                throw new AuthorizationException(
                    "Only the owner can resolve comments."
                );
            }

            List<ReviewComment> existing = comments.get(id);

            int index = -1;

            for (int i = 0; i < existing.size(); i++) {
                if (existing.get(i).id().equals(commentId)) {
                    index = i;
                    break;
                }
            }

            if (index < 0) {
                throw new CommunicationException("Comment not found.");
            }

            ReviewComment old = existing.get(index);

            existing.set(
                index,
                new ReviewComment(
                    old.id(),
                    old.communicationId(),
                    old.reviewerId(),
                    old.criterion(),
                    old.message(),
                    old.severity(),
                    true,
                    old.createdAt()
                )
            );

            auditService.record("COMMENT_RESOLVED", id, actorId);
        }

        Review recordReview(
            String id,
            String reviewerId,
            List<ReviewCriterion> criteria,
            Decision decision,
            String feedback
        ) {
            Communication communication = getCommunication(id);
            Stakeholder reviewer = getStakeholder(reviewerId);

            if (!reviewer.active()) {
                throw new AuthorizationException("Inactive reviewer.");
            }

            if (reviewerId.equals(communication.senderId())) {
                throw new AuthorizationException("Self-review is prohibited.");
            }

            if (communication.status() != Status.UNDER_REVIEW) {
                throw new WorkflowException("Review is not active.");
            }

            List<Review> existing = reviews.get(id);

            if (
                existing.stream().anyMatch(
                    review -> review.reviewerId().equals(reviewerId)
                )
            ) {
                throw new WorkflowException(
                    "Reviewer has already submitted a review."
                );
            }

            if (criteria == null || criteria.isEmpty()) {
                throw new IllegalArgumentException(
                    "Review criteria are required."
                );
            }

            Set<String> supplied = criteria.stream()
                .map(ReviewCriterion::name)
                .collect(Collectors.toSet());

            if (!supplied.containsAll(REQUIRED_CRITERIA)) {
                throw new IllegalArgumentException(
                    "Mandatory review criteria are missing."
                );
            }

            double average = criteria.stream()
                .mapToDouble(ReviewCriterion::score)
                .average()
                .orElseThrow();

            if (
                decision == Decision.APPROVE &&
                average < policy.minimumScore()
            ) {
                throw new WorkflowException(
                    "Approval score is below threshold."
                );
            }

            requireText(feedback, "Feedback");

            Review review = new Review(
                UUID.randomUUID().toString(),
                reviewerId,
                id,
                decision,
                average,
                feedback,
                communication.version(),
                Instant.now()
            );

            existing.add(review);

            auditService.record("REVIEW_RECORDED", id, reviewerId);

            if (decision == Decision.REJECT) {
                transition(communication, Status.REJECTED, reviewerId);
            } else if (decision == Decision.REVISE) {
                transition(
                    communication,
                    Status.REVISION_REQUIRED,
                    reviewerId
                );
            }

            return review;
        }

        EligibilityResult evaluate(String id) {
            Communication communication = getCommunication(id);

            List<Review> currentReviews = reviews.get(id).stream()
                .filter(review ->
                    review.version() == communication.version()
                )
                .toList();

            List<Review> approvals = currentReviews.stream()
                .filter(review ->
                    review.decision() == Decision.APPROVE &&
                    review.averageScore() >= policy.minimumScore() &&
                    getStakeholder(review.reviewerId()).active()
                )
                .toList();

            boolean rejected = currentReviews.stream()
                .anyMatch(review ->
                    review.decision() == Decision.REJECT
                );

            boolean revisionRequested = currentReviews.stream()
                .anyMatch(review ->
                    review.decision() == Decision.REVISE
                );

            double average = currentReviews.stream()
                .mapToDouble(Review::averageScore)
                .average()
                .orElse(0.0);

            long criticalComments = comments.get(id).stream()
                .filter(comment ->
                    comment.severity() == Severity.CRITICAL &&
                    !comment.resolved()
                )
                .count();

            List<String> reasons = new ArrayList<>();

            if (approvals.size() < policy.requiredApprovals()) {
                reasons.add("Insufficient eligible approvals.");
            }

            if (rejected) {
                reasons.add("Communication rejected.");
            }

            if (revisionRequested) {
                reasons.add("Revision requested.");
            }

            if (
                policy.blockCriticalComments() &&
                criticalComments > 0
            ) {
                reasons.add("Unresolved critical comments.");
            }

            return new EligibilityResult(
                reasons.isEmpty(),
                approvals.size(),
                average,
                reasons
            );
        }

        void approvePublication(String id, String actorId) {
            Communication communication = getCommunication(id);

            if (!communication.senderId().equals(actorId)) {
                throw new AuthorizationException(
                    "Only the sender can authorize publication."
                );
            }

            if (communication.status() != Status.UNDER_REVIEW) {
                throw new WorkflowException(
                    "Communication is not under review."
                );
            }

            EligibilityResult result = evaluate(id);

            if (!result.eligible()) {
                throw new WorkflowException(
                    "Publication blocked: " +
                    String.join("; ", result.reasons())
                );
            }

            transition(communication, Status.APPROVED, actorId);
        }

        void publish(String id, String actorId) {
            Communication communication = getCommunication(id);

            if (!communication.senderId().equals(actorId)) {
                throw new AuthorizationException("Only sender can publish.");
            }

            transition(communication, Status.PUBLISHED, actorId);
        }

        void updateContent(String id, String actorId, String newContent) {
            Communication communication = getCommunication(id);

            if (!communication.senderId().equals(actorId)) {
                throw new AuthorizationException("Only sender can edit.");
            }

            if (
                communication.status() == Status.PUBLISHED ||
                communication.status() == Status.ARCHIVED
            ) {
                throw new WorkflowException("Published content is immutable.");
            }

            requireText(newContent, "Content");

            communication.content = newContent;
            communication.version++;

            reviews.get(id).clear();

            transition(
                communication,
                Status.REVISION_REQUIRED,
                actorId
            );
        }

        DeliveryMetrics recordDelivery(
            String id,
            int delivered,
            int read,
            int acknowledged
        ) {
            Communication communication = getCommunication(id);

            if (communication.status() != Status.PUBLISHED) {
                throw new WorkflowException(
                    "Communication must be published."
                );
            }

            int total = communication.recipients().size();

            if (
                delivered < 0 ||
                acknowledged < 0 ||
                acknowledged > read ||
                read > delivered ||
                delivered > total
            ) {
                throw new IllegalArgumentException(
                    "Invalid delivery counts."
                );
            }

            communication.delivered = delivered;
            communication.read = read;
            communication.acknowledged = acknowledged;

            double deliveryRate = percentage(delivered, total);
            double readRate = percentage(read, total);
            double acknowledgementRate = percentage(
                acknowledged,
                total
            );

            return new DeliveryMetrics(
                total,
                delivered,
                read,
                acknowledged,
                deliveryRate,
                readRate,
                acknowledgementRate,
                deliveryRate >= policy.minimumDeliveryRate(),
                !communication.acknowledgementRequired() ||
                    acknowledgementRate >=
                    policy.minimumAcknowledgementRate()
            );
        }

        private double percentage(int value, int total) {
            return total == 0 ? 0.0 : value * 100.0 / total;
        }

        Map<Status, Long> statusReport() {
            Map<Status, Long> result = new EnumMap<>(Status.class);

            for (Status status : Status.values()) {
                result.put(
                    status,
                    communications.values().stream()
                        .filter(c -> c.status() == status)
                        .count()
                );
            }

            return Collections.unmodifiableMap(result);
        }

        int totalCommunications() {
            return communications.size();
        }

        int totalReviews() {
            return reviews.values().stream()
                .mapToInt(List::size)
                .sum();
        }

        int totalComments() {
            return comments.values().stream()
                .mapToInt(List::size)
                .sum();
        }

        void printCommunication(String id) {
            Communication c = getCommunication(id);

            System.out.println("\nCOMMUNICATION");
            System.out.println("ID: " + c.id());
            System.out.println("Status: " + c.status());
            System.out.println("Version: " + c.version());
            System.out.println("Type: " + c.type);
            System.out.println("Subject: " + c.subject);
            System.out.println("Recipients: " + c.recipients().size());
            System.out.println("Created: " + c.createdAt);
        }
    }

    public static void main(String[] args) {
        try {
            ReviewPolicy policy = new ReviewPolicy(
                2,
                70,
                true,
                95,
                80
            );

            InMemoryAuditService audit = new InMemoryAuditService();

            ReviewService service = new ReviewService(policy, audit);

            service.registerStakeholder(new Stakeholder(
                "EMP001",
                "Project Manager",
                "Manager",
                "Operations",
                true
            ));

            service.registerStakeholder(new Stakeholder(
                "EMP002",
                "Quality Officer",
                "Reviewer",
                "Quality",
                true
            ));

            service.registerStakeholder(new Stakeholder(
                "EMP003",
                "Technical Lead",
                "Reviewer",
                "Technology",
                true
            ));

            service.registerStakeholder(new Stakeholder(
                "EMP004",
                "Department Head",
                "Recipient",
                "Management",
                true
            ));

            service.registerStakeholder(new Stakeholder(
                "EMP005",
                "Field Coordinator",
                "Recipient",
                "Operations",
                true
            ));

            String communicationId = service.createCommunication(
                "Monthly Operational Review",
                CommunicationType.REPORT,
                "EMP001",
                List.of("EMP004", "EMP005"),
                "Performance and Corrective Actions",
                "This report covers performance, operational risks, " +
                "pending activities, and corrective actions.",
                List.of(
                    "Communicate performance",
                    "Identify operational risks",
                    "Assign corrective actions"
                ),
                Sensitivity.INTERNAL,
                true
            );

            service.submit(communicationId, "EMP001");

            List<ReviewCriterion> criteria = List.of(
                new ReviewCriterion("clarity", 92),
                new ReviewCriterion("accuracy", 95),
                new ReviewCriterion("completeness", 90),
                new ReviewCriterion("audience_alignment", 88),
                new ReviewCriterion("timeliness", 92),
                new ReviewCriterion("actionability", 90),
                new ReviewCriterion("professionalism", 96)
            );

            for (String reviewer : List.of("EMP002", "EMP003")) {
                service.beginReview(communicationId, reviewer);

                service.recordReview(
                    communicationId,
                    reviewer,
                    criteria,
                    Decision.APPROVE,
                    "The communication meets the required standards."
                );
            }

            System.out.println("\nELIGIBILITY");

            EligibilityResult eligibility =
                service.evaluate(communicationId);

            System.out.println(eligibility);

            service.approvePublication(
                communicationId,
                "EMP001"
            );

            service.publish(communicationId, "EMP001");

            DeliveryMetrics metrics = service.recordDelivery(
                communicationId,
                2,
                2,
                2
            );

            System.out.println("\nDELIVERY METRICS");
            System.out.println(metrics);

            System.out.println("\nMANAGEMENT REPORT");
            System.out.println(service.statusReport());

            System.out.println(
                "Total communications: " +
                service.totalCommunications()
            );

            System.out.println(
                "Total reviews: " + service.totalReviews()
            );

            System.out.println(
                "Total comments: " + service.totalComments()
            );

            System.out.println("\nAUDIT EVENTS");

            audit.events().forEach(System.out::println);

        } catch (CommunicationException |
                 IllegalArgumentException exception) {

            System.err.println(
                "COMMUNICATION GOVERNANCE ERROR: " +
                exception.getMessage()
            );

            System.exit(1);
        }
    }
}
