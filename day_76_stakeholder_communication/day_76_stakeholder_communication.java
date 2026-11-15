import java.time.Duration;
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
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * Enterprise Stakeholder Communication Governance System.
 *
 * Java 17
 * No external dependencies.
 *
 * Demonstrates domain modeling, policy enforcement, approval workflows,
 * communication state transitions, feedback management, and reporting.
 */
public class StakeholderCommunication {

    enum Influence {
        LOW, MEDIUM, HIGH
    }

    enum Engagement {
        UNAWARE, RESISTANT, NEUTRAL, SUPPORTIVE, LEADING
    }

    enum Priority {
        LOW, MEDIUM, HIGH, CRITICAL
    }

    enum Channel {
        EMAIL, MEETING, REPORT, PHONE, COLLABORATION
    }

    enum MessageStatus {
        DRAFT, APPROVED, SENT, ACKNOWLEDGED, ESCALATED, CANCELLED
    }

    enum ReviewDecision {
        COMMENTED, APPROVED, CHANGES_REQUESTED, DISMISSED
    }

    enum FeedbackSentiment {
        POSITIVE, NEUTRAL, NEGATIVE
    }

    enum FeedbackStatus {
        OPEN, IN_PROGRESS, RESOLVED
    }

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static final Pattern EMAIL_PATTERN =
        Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$");

    record Stakeholder(
        String id,
        String name,
        String role,
        String department,
        String email,
        Influence influence,
        Influence interest,
        Engagement engagement,
        Channel preferredChannel,
        boolean active
    ) {
        Stakeholder {
            id = requireText(id, "ID");
            name = requireText(name, "Name");
            role = requireText(role, "Role");
            department = requireText(department, "Department");
            email = requireText(email, "Email").toLowerCase();

            Objects.requireNonNull(influence);
            Objects.requireNonNull(interest);
            Objects.requireNonNull(engagement);
            Objects.requireNonNull(preferredChannel);

            if (!EMAIL_PATTERN.matcher(email).matches()) {
                throw new DomainException("Invalid email address.");
            }
        }

        String powerInterestCategory() {
            if (influence == Influence.HIGH &&
                interest == Influence.HIGH) {
                return "MANAGE_CLOSELY";
            }

            if (influence == Influence.HIGH) {
                return "KEEP_SATISFIED";
            }

            if (interest == Influence.HIGH) {
                return "KEEP_INFORMED";
            }

            return "MONITOR";
        }
    }

    record CommunicationPolicy(
        int requiredApprovals,
        Duration acknowledgementWindow,
        Set<Channel> allowedChannels,
        boolean requireResolvedDiscussions,
        boolean requireAuthorizedApprover
    ) {
        CommunicationPolicy {
            if (requiredApprovals < 0 ||
                acknowledgementWindow == null ||
                acknowledgementWindow.isNegative() ||
                acknowledgementWindow.isZero()) {
                throw new DomainException("Invalid communication policy.");
            }

            allowedChannels = Set.copyOf(allowedChannels);

            if (allowedChannels.isEmpty()) {
                throw new DomainException("At least one channel is required.");
            }
        }
    }

    static final class Review {
        private final String reviewerId;
        private ReviewDecision decision;
        private final String comment;
        private final Instant submittedAt;
        private final boolean eligible;

        Review(
            String reviewerId,
            ReviewDecision decision,
            String comment,
            boolean eligible
        ) {
            this.reviewerId = reviewerId;
            this.decision = decision;
            this.comment = comment;
            this.eligible = eligible;
            this.submittedAt = Instant.now();
        }

        String reviewerId() {
            return reviewerId;
        }

        ReviewDecision decision() {
            return decision;
        }

        boolean eligible() {
            return eligible;
        }

        void dismiss() {
            if (decision != ReviewDecision.APPROVED) {
                throw new DomainException(
                    "Only active approvals can be dismissed."
                );
            }

            decision = ReviewDecision.DISMISSED;
        }
    }

    static final class Communication {
        private final String id;
        private final String stakeholderId;
        private final String subject;
        private final String body;
        private final Channel channel;
        private final Priority priority;
        private final Instant createdAt;
        private final Instant deadline;
        private final List<Review> reviews = new ArrayList<>();

        private MessageStatus status = MessageStatus.DRAFT;
        private String approvedBy;
        private Instant sentAt;
        private Instant acknowledgedAt;

        Communication(
            String stakeholderId,
            String subject,
            String body,
            Channel channel,
            Priority priority,
            Instant deadline
        ) {
            this.id = UUID.randomUUID().toString();
            this.stakeholderId = requireText(stakeholderId, "Stakeholder ID");
            this.subject = requireText(subject, "Subject");
            this.body = requireText(body, "Body");
            this.channel = Objects.requireNonNull(channel);
            this.priority = Objects.requireNonNull(priority);
            this.deadline = deadline;
            this.createdAt = Instant.now();

            if (deadline != null && !deadline.isAfter(createdAt)) {
                throw new DomainException("Deadline must be in the future.");
            }
        }

        String id() {
            return id;
        }

        String stakeholderId() {
            return stakeholderId;
        }

        MessageStatus status() {
            return status;
        }

        List<Review> reviews() {
            return Collections.unmodifiableList(reviews);
        }
    }

    record Feedback(
        String id,
        String stakeholderId,
        String communicationId,
        FeedbackSentiment sentiment,
        String content,
        Instant receivedAt
    ) {
        Feedback {
            Objects.requireNonNull(sentiment);
            content = requireText(content, "Feedback content");
        }
    }

    static final class FeedbackCase {
        private final Feedback feedback;
        private FeedbackStatus status = FeedbackStatus.OPEN;
        private String resolution;

        FeedbackCase(Feedback feedback) {
            this.feedback = feedback;
        }

        void beginInvestigation() {
            if (status != FeedbackStatus.OPEN) {
                throw new DomainException("Invalid feedback transition.");
            }

            status = FeedbackStatus.IN_PROGRESS;
        }

        void resolve(String resolution) {
            if (status == FeedbackStatus.RESOLVED) {
                throw new DomainException("Feedback already resolved.");
            }

            this.resolution = requireText(resolution, "Resolution");
            this.status = FeedbackStatus.RESOLVED;
        }

        FeedbackStatus status() {
            return status;
        }

        Feedback feedback() {
            return feedback;
        }
    }

    interface DeliveryGateway {
        void deliver(Stakeholder recipient, Communication message);
    }

    static final class SimulationGateway implements DeliveryGateway {
        @Override
        public void deliver(Stakeholder recipient, Communication message) {
            if (recipient.email() == null || recipient.email().isBlank()) {
                throw new DomainException("Delivery address unavailable.");
            }

            System.out.println(
                "DELIVERY SIMULATED | " +
                recipient.email() + " | " + message.subject
            );
        }
    }

    static final class AuditEvent {
        private final Instant timestamp;
        private final String event;
        private final String entityId;
        private final String actor;

        AuditEvent(String event, String entityId, String actor) {
            this.timestamp = Instant.now();
            this.event = event;
            this.entityId = entityId;
            this.actor = actor;
        }

        @Override
        public String toString() {
            return timestamp + " | " + event + " | " +
                entityId + " | " + actor;
        }
    }

    static final class CommunicationService {
        private final Map<String, Stakeholder> stakeholders =
            new HashMap<>();

        private final Map<String, Communication> communications =
            new HashMap<>();

        private final Map<String, FeedbackCase> feedbackCases =
            new HashMap<>();

        private final Map<String, CommunicationPolicy> policies =
            new HashMap<>();

        private final List<AuditEvent> audit = new ArrayList<>();

        private final DeliveryGateway gateway;

        CommunicationService(DeliveryGateway gateway) {
            this.gateway = Objects.requireNonNull(gateway);
        }

        private void record(String event, String id, String actor) {
            audit.add(new AuditEvent(event, id, actor));
        }

        void registerStakeholder(Stakeholder stakeholder) {
            if (stakeholders.containsKey(stakeholder.id())) {
                throw new DomainException("Duplicate stakeholder ID.");
            }

            boolean duplicateEmail = stakeholders.values().stream()
                .anyMatch(s -> s.email().equalsIgnoreCase(
                    stakeholder.email()
                ));

            if (duplicateEmail) {
                throw new DomainException("Duplicate stakeholder email.");
            }

            stakeholders.put(stakeholder.id(), stakeholder);
            record("STAKEHOLDER_REGISTERED", stakeholder.id(), "SYSTEM");
        }

        void assignPolicy(
            String stakeholderId,
            CommunicationPolicy policy
        ) {
            requireStakeholder(stakeholderId);
            policies.put(stakeholderId, policy);
        }

        Communication createCommunication(
            String stakeholderId,
            String subject,
            String body,
            Channel channel,
            Priority priority,
            Instant deadline
        ) {
            Stakeholder stakeholder = requireStakeholder(stakeholderId);

            if (!stakeholder.active()) {
                throw new DomainException("Inactive stakeholder.");
            }

            CommunicationPolicy policy = policies.get(stakeholderId);

            if (policy != null && !policy.allowedChannels().contains(channel)) {
                throw new DomainException("Channel prohibited by policy.");
            }

            Communication communication = new Communication(
                stakeholderId,
                subject,
                body,
                channel,
                priority,
                deadline
            );

            communications.put(communication.id(), communication);

            record(
                "COMMUNICATION_DRAFTED",
                communication.id(),
                "PROJECT_MANAGER"
            );

            return communication;
        }

        void submitReview(
            String communicationId,
            String reviewerId,
            ReviewDecision decision,
            String comment,
            boolean eligible
        ) {
            Communication communication = requireCommunication(
                communicationId
            );

            Stakeholder reviewer = requireStakeholder(reviewerId);

            if (!reviewer.active() || !eligible) {
                throw new DomainException("Reviewer is not eligible.");
            }

            if (reviewerId.equals(communication.stakeholderId)) {
                throw new DomainException(
                    "Sender cannot approve their own communication."
                );
            }

            if (communication.status != MessageStatus.DRAFT) {
                throw new DomainException("Review period has closed.");
            }

            if (decision == ReviewDecision.CHANGES_REQUESTED &&
                (comment == null || comment.isBlank())) {
                throw new DomainException(
                    "Requested changes require an explanation."
                );
            }

            if (decision == ReviewDecision.DISMISSED) {
                throw new DomainException(
                    "Use the dismissal operation for existing approvals."
                );
            }

            boolean alreadyApproved = communication.reviews.stream()
                .anyMatch(r ->
                    r.reviewerId().equals(reviewerId) &&
                    r.decision() == ReviewDecision.APPROVED
                );

            if (alreadyApproved && decision == ReviewDecision.APPROVED) {
                throw new DomainException("Duplicate reviewer approval.");
            }

            communication.reviews.add(
                new Review(reviewerId, decision, comment, true)
            );

            record(
                "REVIEW_" + decision,
                communicationId,
                reviewerId
            );
        }

        void dismissApproval(
            String communicationId,
            String reviewerId
        ) {
            Communication communication = requireCommunication(
                communicationId
            );

            if (communication.status != MessageStatus.DRAFT) {
                throw new DomainException(
                    "Approvals cannot be changed after delivery approval."
                );
            }

            Review review = communication.reviews.stream()
                .filter(r -> r.reviewerId().equals(reviewerId))
                .filter(r -> r.decision() == ReviewDecision.APPROVED)
                .findFirst()
                .orElseThrow(() ->
                    new DomainException("Active approval not found.")
                );

            review.dismiss();

            record("APPROVAL_DISMISSED", communicationId, reviewerId);
        }

        private boolean approvalRequirementsSatisfied(
            Communication communication,
            CommunicationPolicy policy
        ) {
            long approvals = communication.reviews.stream()
                .filter(Review::eligible)
                .filter(r -> r.decision() == ReviewDecision.APPROVED)
                .map(Review::reviewerId)
                .distinct()
                .count();

            if (approvals < policy.requiredApprovals()) {
                return false;
            }

            if (policy.requireResolvedDiscussions()) {
                boolean unresolved = communication.reviews.stream()
                    .anyMatch(r ->
                        r.decision() == ReviewDecision.CHANGES_REQUESTED
                    );

                if (unresolved) {
                    return false;
                }
            }

            return true;
        }

        void approveCommunication(
            String communicationId,
            String approverId,
            boolean authorized
        ) {
            Communication communication = requireCommunication(
                communicationId
            );

            CommunicationPolicy policy = policies.get(
                communication.stakeholderId
            );

            if (communication.status != MessageStatus.DRAFT) {
                throw new DomainException("Invalid approval transition.");
            }

            if (policy != null) {
                if (policy.requireAuthorizedApprover() && !authorized) {
                    throw new DomainException(
                        "Approver lacks required authorization."
                    );
                }

                if (!approvalRequirementsSatisfied(communication, policy)) {
                    throw new DomainException(
                        "Review requirements are not satisfied."
                    );
                }
            }

            communication.status = MessageStatus.APPROVED;
            communication.approvedBy = requireText(
                approverId,
                "Approver ID"
            );

            record("COMMUNICATION_APPROVED", communicationId, approverId);
        }

        void sendCommunication(String communicationId) {
            Communication communication = requireCommunication(
                communicationId
            );

            Stakeholder recipient = requireStakeholder(
                communication.stakeholderId
            );

            if (!recipient.active()) {
                throw new DomainException("Recipient is inactive.");
            }

            CommunicationPolicy policy = policies.get(
                communication.stakeholderId
            );

            if (communication.status != MessageStatus.APPROVED &&
                policy != null) {
                throw new DomainException("Formal approval is required.");
            }

            if (communication.status != MessageStatus.APPROVED &&
                communication.status != MessageStatus.DRAFT) {
                throw new DomainException("Invalid delivery transition.");
            }

            // Change state only after successful gateway delivery.
            gateway.deliver(recipient, communication);

            communication.sentAt = Instant.now();
            communication.status = MessageStatus.SENT;

            record("COMMUNICATION_SENT", communicationId, "SYSTEM");
        }

        void acknowledge(
            String communicationId,
            String stakeholderId
        ) {
            Communication communication = requireCommunication(
                communicationId
            );

            if (!communication.stakeholderId.equals(stakeholderId)) {
                throw new DomainException("Acknowledgement identity mismatch.");
            }

            if (communication.status != MessageStatus.SENT) {
                throw new DomainException("Communication has not been sent.");
            }

            communication.acknowledgedAt = Instant.now();
            communication.status = MessageStatus.ACKNOWLEDGED;

            record(
                "COMMUNICATION_ACKNOWLEDGED",
                communicationId,
                stakeholderId
            );
        }

        FeedbackCase recordFeedback(
            String stakeholderId,
            String communicationId,
            FeedbackSentiment sentiment,
            String content
        ) {
            Communication communication = requireCommunication(
                communicationId
            );

            if (!communication.stakeholderId.equals(stakeholderId)) {
                throw new DomainException("Feedback ownership mismatch.");
            }

            if (communication.status != MessageStatus.SENT &&
                communication.status != MessageStatus.ACKNOWLEDGED) {
                throw new DomainException("Communication not delivered.");
            }

            Feedback feedback = new Feedback(
                UUID.randomUUID().toString(),
                stakeholderId,
                communicationId,
                sentiment,
                content,
                Instant.now()
            );

            FeedbackCase feedbackCase = new FeedbackCase(feedback);

            feedbackCases.put(feedback.id(), feedbackCase);

            record("FEEDBACK_RECEIVED", feedback.id(), stakeholderId);

            return feedbackCase;
        }

        List<String> escalateOverdue(Instant referenceTime) {
            List<String> escalated = new ArrayList<>();

            for (Communication communication : communications.values()) {
                if (communication.status == MessageStatus.SENT &&
                    communication.deadline != null &&
                    communication.deadline.isBefore(referenceTime)) {

                    communication.status = MessageStatus.ESCALATED;
                    escalated.add(communication.id());

                    record(
                        "COMMUNICATION_ESCALATED",
                        communication.id(),
                        "SYSTEM"
                    );
                }
            }

            return escalated;
        }

        private Stakeholder requireStakeholder(String id) {
            Stakeholder stakeholder = stakeholders.get(id);

            if (stakeholder == null) {
                throw new DomainException("Stakeholder not found: " + id);
            }

            return stakeholder;
        }

        private Communication requireCommunication(String id) {
            Communication communication = communications.get(id);

            if (communication == null) {
                throw new DomainException("Communication not found: " + id);
            }

            return communication;
        }

        void printReport() {
            Map<MessageStatus, Long> statusCounts =
                communications.values().stream()
                    .collect(Collectors.groupingBy(
                        c -> c.status,
                        () -> new EnumMap<>(MessageStatus.class),
                        Collectors.counting()
                    ));

            Map<String, Long> categories =
                stakeholders.values().stream()
                    .filter(Stakeholder::active)
                    .collect(Collectors.groupingBy(
                        Stakeholder::powerInterestCategory,
                        Collectors.counting()
                    ));

            long sent = communications.values().stream()
                .filter(c -> c.sentAt != null)
                .count();

            long acknowledged = communications.values().stream()
                .filter(c -> c.acknowledgedAt != null)
                .count();

            long unresolvedNegative = feedbackCases.values().stream()
                .filter(f ->
                    f.feedback().sentiment() == FeedbackSentiment.NEGATIVE &&
                    f.status() != FeedbackStatus.RESOLVED
                )
                .count();

            double acknowledgementRate = sent == 0
                ? 0.0
                : acknowledged * 100.0 / sent;

            System.out.println("\nENTERPRISE COMMUNICATION REPORT");
            System.out.println("Stakeholders: " + stakeholders.size());
            System.out.println("Power-interest groups: " + categories);
            System.out.println("Message statuses: " + statusCounts);
            System.out.printf(
                "Acknowledgement rate: %.2f%%%n",
                acknowledgementRate
            );
            System.out.println(
                "Unresolved negative feedback: " + unresolvedNegative
            );

            System.out.println("\nAUDIT TRAIL");

            audit.forEach(System.out::println);
        }
    }

    private static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new DomainException(field + " is required.");
        }

        return value.trim();
    }

    public static void main(String[] args) {
        try {
            CommunicationPolicy policy = new CommunicationPolicy(
                1,
                Duration.ofHours(24),
                Set.of(Channel.EMAIL, Channel.MEETING, Channel.REPORT),
                true,
                true
            );

            CommunicationService service =
                new CommunicationService(new SimulationGateway());

            Stakeholder sponsor = new Stakeholder(
                "STK-001",
                "Ananya Sharma",
                "Project Sponsor",
                "Executive Management",
                "ananya@example.com",
                Influence.HIGH,
                Influence.HIGH,
                Engagement.SUPPORTIVE,
                Channel.MEETING,
                true
            );

            Stakeholder technicalLead = new Stakeholder(
                "STK-002",
                "Rahul Verma",
                "Technical Lead",
                "Engineering",
                "rahul@example.com",
                Influence.HIGH,
                Influence.HIGH,
                Engagement.LEADING,
                Channel.EMAIL,
                true
            );

            service.registerStakeholder(sponsor);
            service.registerStakeholder(technicalLead);
            service.assignPolicy("STK-001", policy);

            Communication message = service.createCommunication(
                "STK-001",
                "Project Delivery and Deployment Status",
                "Integration testing is complete. Three issues remain. " +
                "A deployment decision is requested.",
                Channel.EMAIL,
                Priority.HIGH,
                Instant.now().plus(Duration.ofHours(24))
            );

            service.submitReview(
                message.id(),
                "STK-002",
                ReviewDecision.APPROVED,
                "Technical details verified.",
                true
            );

            service.approveCommunication(
                message.id(),
                "PROGRAM-DIRECTOR",
                true
            );

            service.sendCommunication(message.id());
            service.acknowledge(message.id(), "STK-001");

            FeedbackCase feedback = service.recordFeedback(
                "STK-001",
                message.id(),
                FeedbackSentiment.POSITIVE,
                "The report is clear. Include a deployment risk matrix."
            );

            feedback.beginInvestigation();

            feedback.resolve(
                "Deployment risk matrix added to the next report."
            );

            service.printReport();

        } catch (DomainException exception) {
            System.err.println(
                "Governance validation failed: " + exception.getMessage()
            );

            System.exitCodePlaceholder();
        }
    }
}
