/*
 * PROJECT COMMUNICATION MANAGEMENT
 * Introduction to Project Communication
 *
 * Java 17 enterprise communication management model.
 *
 * Features:
 * - Strongly typed stakeholder records
 * - Communication policies
 * - Stakeholder authorization
 * - Message lifecycle
 * - Communication plans
 * - Meeting coordination
 * - Decision recording
 * - Action-item workflows
 * - Escalation and reporting
 * - Immutable audit events
 *
 * Compile:
 * javac ProjectCommunication.java
 *
 * Run:
 * java ProjectCommunication
 */

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
import java.util.stream.Collectors;

// ============================================================
// MAIN APPLICATION
// ============================================================

public class ProjectCommunication {

    // ========================================================
    // ENUMERATIONS
    // ========================================================

    enum Role {
        PROJECT_MANAGER,
        SPONSOR,
        DEVELOPER,
        CLIENT,
        VENDOR,
        EXECUTIVE
    }

    enum Channel {
        EMAIL,
        MEETING,
        CHAT,
        REPORT,
        PHONE,
        PORTAL
    }

    enum Purpose {
        INFORMATION,
        STATUS_UPDATE,
        DECISION,
        REQUEST,
        ESCALATION
    }

    enum Confidentiality {
        PUBLIC(1),
        INTERNAL(2),
        CONFIDENTIAL(3),
        RESTRICTED(4);

        private final int level;

        Confidentiality(int level) {
            this.level = level;
        }

        public int level() {
            return level;
        }
    }

    enum MessageState {
        DRAFT,
        SENT,
        ACKNOWLEDGED,
        ESCALATED
    }

    enum ActionState {
        OPEN,
        IN_PROGRESS,
        BLOCKED,
        COMPLETED,
        CANCELLED
    }

    // ========================================================
    // EXCEPTIONS
    // ========================================================

    static class CommunicationException extends RuntimeException {
        CommunicationException(String message) {
            super(message);
        }
    }

    static class ValidationException extends CommunicationException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class AuthorizationException extends CommunicationException {
        AuthorizationException(String message) {
            super(message);
        }
    }

    static class NotFoundException extends CommunicationException {
        NotFoundException(String message) {
            super(message);
        }
    }

    static class StateTransitionException extends CommunicationException {
        StateTransitionException(String message) {
            super(message);
        }
    }

    // ========================================================
    // VALIDATION UTILITIES
    // ========================================================

    static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(field + " is required.");
        }

        return value.trim();
    }

    static String newId(String prefix) {
        return prefix + "-" + UUID.randomUUID();
    }

    // ========================================================
    // DOMAIN RECORDS
    // ========================================================

    record Stakeholder(
        String id,
        String name,
        String email,
        Role role,
        int influence,
        int interest,
        Confidentiality clearance,
        boolean active
    ) {
        Stakeholder {
            id = requireText(id, "Stakeholder ID");
            name = requireText(name, "Stakeholder name");
            email = requireText(email, "Email");

            if (!email.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
                throw new ValidationException("Invalid email.");
            }

            Objects.requireNonNull(role);
            Objects.requireNonNull(clearance);

            if (influence < 1 || influence > 5 ||
                interest < 1 || interest > 5) {
                throw new ValidationException(
                    "Influence and interest must be between 1 and 5."
                );
            }
        }

        String engagementStrategy() {
            int score = influence * interest;

            if (score >= 16) return "MANAGE CLOSELY";
            if (influence >= 4) return "KEEP SATISFIED";
            if (interest >= 4) return "KEEP INFORMED";

            return "MONITOR";
        }
    }

    record CommunicationPlan(
        String id,
        String stakeholderId,
        String ownerId,
        Channel channel,
        Purpose purpose,
        String frequency,
        Instant nextCommunication,
        boolean active
    ) {
        CommunicationPlan {
            id = requireText(id, "Plan ID");
            stakeholderId = requireText(stakeholderId, "Stakeholder ID");
            ownerId = requireText(ownerId, "Owner ID");
            Objects.requireNonNull(channel);
            Objects.requireNonNull(purpose);
            Objects.requireNonNull(nextCommunication);

            frequency = requireText(frequency, "Frequency");
        }
    }

    record AuditEvent(
        String id,
        String eventType,
        String entityId,
        String actorId,
        Instant timestamp,
        Map<String, String> details
    ) {
        AuditEvent {
            details = Collections.unmodifiableMap(
                new HashMap<>(details)
            );
        }
    }

    record CommunicationMetrics(
        int stakeholderCount,
        int messageCount,
        int sentMessages,
        int expectedAcknowledgements,
        int actualAcknowledgements,
        double acknowledgementRate,
        int overdueActions,
        int meetings,
        int decisions,
        int auditEvents
    ) {}

    // ========================================================
    // COMMUNICATION POLICY
    // ========================================================

    interface CommunicationPolicy {
        boolean canSend(Stakeholder sender, Purpose purpose);

        boolean canReceive(
            Stakeholder recipient,
            Confidentiality confidentiality
        );
    }

    static class DefaultCommunicationPolicy
        implements CommunicationPolicy {

        private final Map<Role, Set<Purpose>> permissions =
            new EnumMap<>(Role.class);

        DefaultCommunicationPolicy() {
            permissions.put(
                Role.PROJECT_MANAGER,
                Set.of(Purpose.values())
            );

            permissions.put(
                Role.SPONSOR,
                Set.of(
                    Purpose.INFORMATION,
                    Purpose.STATUS_UPDATE,
                    Purpose.DECISION,
                    Purpose.ESCALATION
                )
            );

            permissions.put(
                Role.DEVELOPER,
                Set.of(
                    Purpose.INFORMATION,
                    Purpose.STATUS_UPDATE,
                    Purpose.REQUEST
                )
            );

            permissions.put(
                Role.CLIENT,
                Set.of(
                    Purpose.INFORMATION,
                    Purpose.STATUS_UPDATE,
                    Purpose.DECISION,
                    Purpose.REQUEST
                )
            );

            permissions.put(
                Role.VENDOR,
                Set.of(
                    Purpose.INFORMATION,
                    Purpose.STATUS_UPDATE,
                    Purpose.REQUEST
                )
            );

            permissions.put(
                Role.EXECUTIVE,
                Set.of(
                    Purpose.INFORMATION,
                    Purpose.STATUS_UPDATE,
                    Purpose.ESCALATION
                )
            );
        }

        @Override
        public boolean canSend(Stakeholder sender, Purpose purpose) {
            return sender.active() &&
                permissions.getOrDefault(sender.role(), Set.of())
                    .contains(purpose);
        }

        @Override
        public boolean canReceive(
            Stakeholder recipient,
            Confidentiality confidentiality
        ) {
            return recipient.active() &&
                recipient.clearance().level() >= confidentiality.level();
        }
    }

    // ========================================================
    // MESSAGE AGGREGATE
    // ========================================================

    static class ProjectMessage {

        private final String id;
        private final String senderId;
        private final String subject;
        private final String body;
        private final Channel channel;
        private final Purpose purpose;
        private final Confidentiality confidentiality;
        private final Set<String> recipientIds;

        private final Set<String> acknowledgements = new HashSet<>();

        private final Instant createdAt;

        private Instant sentAt;
        private MessageState state = MessageState.DRAFT;

        ProjectMessage(
            String senderId,
            String subject,
            String body,
            Channel channel,
            Purpose purpose,
            Confidentiality confidentiality,
            Set<String> recipientIds
        ) {
            this.id = newId("MSG");
            this.senderId = senderId;
            this.subject = requireText(subject, "Subject");
            this.body = requireText(body, "Body");

            this.channel = Objects.requireNonNull(channel);
            this.purpose = Objects.requireNonNull(purpose);
            this.confidentiality = Objects.requireNonNull(confidentiality);

            if (recipientIds.isEmpty()) {
                throw new ValidationException("Recipients are required.");
            }

            this.recipientIds = Collections.unmodifiableSet(
                new HashSet<>(recipientIds)
            );

            this.createdAt = Instant.now();
        }

        String id() {
            return id;
        }

        String senderId() {
            return senderId;
        }

        String subject() {
            return subject;
        }

        Set<String> recipientIds() {
            return recipientIds;
        }

        Set<String> acknowledgements() {
            return Collections.unmodifiableSet(acknowledgements);
        }

        MessageState state() {
            return state;
        }

        Instant sentAt() {
            return sentAt;
        }

        void send() {
            if (state != MessageState.DRAFT) {
                throw new StateTransitionException(
                    "Only draft messages can be sent."
                );
            }

            state = MessageState.SENT;
            sentAt = Instant.now();
        }

        void acknowledge(String stakeholderId) {
            if (state != MessageState.SENT &&
                state != MessageState.ACKNOWLEDGED) {
                throw new StateTransitionException(
                    "Message cannot be acknowledged."
                );
            }

            if (!recipientIds.contains(stakeholderId)) {
                throw new AuthorizationException(
                    "Stakeholder is not an intended recipient."
                );
            }

            acknowledgements.add(stakeholderId);

            if (acknowledgements.size() == recipientIds.size()) {
                state = MessageState.ACKNOWLEDGED;
            }
        }

        void escalate() {
            if (state == MessageState.SENT) {
                state = MessageState.ESCALATED;
            }
        }

        Confidentiality confidentiality() {
            return confidentiality;
        }

        Purpose purpose() {
            return purpose;
        }

        Channel channel() {
            return channel;
        }
    }

    // ========================================================
    // MEETING AND DECISION MODELS
    // ========================================================

    static class Meeting {

        private final String id = newId("MEET");
        private final String organizerId;
        private final String title;
        private final Set<String> participantIds;
        private final Instant scheduledAt;
        private final List<String> agenda;

        private String minutes;
        private boolean completed;

        Meeting(
            String organizerId,
            String title,
            Set<String> participantIds,
            Instant scheduledAt,
            List<String> agenda
        ) {
            this.organizerId = organizerId;
            this.title = requireText(title, "Meeting title");

            if (participantIds.isEmpty() || agenda.isEmpty()) {
                throw new ValidationException(
                    "Meeting needs participants and agenda."
                );
            }

            this.participantIds = Set.copyOf(participantIds);
            this.scheduledAt = Objects.requireNonNull(scheduledAt);
            this.agenda = List.copyOf(agenda);
        }

        String id() {
            return id;
        }

        String organizerId() {
            return organizerId;
        }

        boolean completed() {
            return completed;
        }

        void finalizeMeeting(String actorId, String minutes) {
            if (!organizerId.equals(actorId)) {
                throw new AuthorizationException(
                    "Only organizer can finalize the meeting."
                );
            }

            if (completed) {
                throw new StateTransitionException(
                    "Meeting already completed."
                );
            }

            this.minutes = requireText(minutes, "Meeting minutes");
            this.completed = true;
        }
    }

    record Decision(
        String id,
        String meetingId,
        String description,
        String ownerId,
        boolean approved,
        Instant recordedAt
    ) {}

    // ========================================================
    // ACTION ITEM AGGREGATE
    // ========================================================

    static class ActionItem {

        private final String id = newId("ACT");
        private final String description;
        private final String assignedTo;
        private final String createdBy;
        private final Instant dueDate;

        private ActionState state = ActionState.OPEN;

        ActionItem(
            String description,
            String assignedTo,
            String createdBy,
            Instant dueDate
        ) {
            this.description = requireText(
                description, "Action description"
            );

            this.assignedTo = assignedTo;
            this.createdBy = createdBy;
            this.dueDate = Objects.requireNonNull(dueDate);
        }

        String id() {
            return id;
        }

        ActionState state() {
            return state;
        }

        Instant dueDate() {
            return dueDate;
        }

        void update(String actorId, ActionState nextState) {
            if (!actorId.equals(assignedTo) &&
                !actorId.equals(createdBy)) {
                throw new AuthorizationException(
                    "Actor cannot update action."
                );
            }

            Map<ActionState, Set<ActionState>> transitions =
                new EnumMap<>(ActionState.class);

            transitions.put(
                ActionState.OPEN,
                Set.of(
                    ActionState.IN_PROGRESS,
                    ActionState.BLOCKED,
                    ActionState.CANCELLED
                )
            );

            transitions.put(
                ActionState.IN_PROGRESS,
                Set.of(
                    ActionState.COMPLETED,
                    ActionState.BLOCKED,
                    ActionState.CANCELLED
                )
            );

            transitions.put(
                ActionState.BLOCKED,
                Set.of(
                    ActionState.IN_PROGRESS,
                    ActionState.CANCELLED
                )
            );

            transitions.put(ActionState.COMPLETED, Set.of());
            transitions.put(ActionState.CANCELLED, Set.of());

            if (!transitions.get(state).contains(nextState)) {
                throw new StateTransitionException(
                    "Invalid action state transition."
                );
            }

            state = nextState;
        }
    }

    // ========================================================
    // APPLICATION SERVICE
    // ========================================================

    static class CommunicationService {

        private final String projectName;

        private final CommunicationPolicy policy;

        private final Map<String, Stakeholder> stakeholders =
            new HashMap<>();

        private final Map<String, CommunicationPlan> plans =
            new HashMap<>();

        private final Map<String, ProjectMessage> messages =
            new HashMap<>();

        private final Map<String, Meeting> meetings =
            new HashMap<>();

        private final Map<String, Decision> decisions =
            new HashMap<>();

        private final Map<String, ActionItem> actions =
            new HashMap<>();

        private final List<AuditEvent> audit =
            new ArrayList<>();

        CommunicationService(
            String projectName,
            CommunicationPolicy policy
        ) {
            this.projectName = requireText(projectName, "Project name");
            this.policy = Objects.requireNonNull(policy);
        }

        private Stakeholder getStakeholder(String id) {
            Stakeholder stakeholder = stakeholders.get(id);

            if (stakeholder == null || !stakeholder.active()) {
                throw new NotFoundException(
                    "Active stakeholder not found: " + id
                );
            }

            return stakeholder;
        }

        private void audit(
            String type,
            String entityId,
            String actorId
        ) {
            audit.add(
                new AuditEvent(
                    newId("AUD"),
                    type,
                    entityId,
                    actorId,
                    Instant.now(),
                    Map.of()
                )
            );
        }

        // ----------------------------------------------------
        // STAKEHOLDERS
        // ----------------------------------------------------

        void addStakeholder(Stakeholder stakeholder) {
            if (stakeholders.containsKey(stakeholder.id())) {
                throw new ValidationException(
                    "Duplicate stakeholder ID."
                );
            }

            boolean duplicateEmail = stakeholders.values()
                .stream()
                .anyMatch(existing ->
                    existing.email().equalsIgnoreCase(stakeholder.email())
                );

            if (duplicateEmail) {
                throw new ValidationException(
                    "Duplicate stakeholder email."
                );
            }

            stakeholders.put(stakeholder.id(), stakeholder);

            audit(
                "STAKEHOLDER_ADDED",
                stakeholder.id(),
                stakeholder.id()
            );
        }

        // ----------------------------------------------------
        // COMMUNICATION PLANS
        // ----------------------------------------------------

        void addPlan(CommunicationPlan plan) {
            getStakeholder(plan.stakeholderId());
            getStakeholder(plan.ownerId());

            if (plans.containsKey(plan.id())) {
                throw new ValidationException("Duplicate plan ID.");
            }

            plans.put(plan.id(), plan);

            audit("PLAN_CREATED", plan.id(), plan.ownerId());
        }

        // ----------------------------------------------------
        // MESSAGE MANAGEMENT
        // ----------------------------------------------------

        ProjectMessage createMessage(
            String senderId,
            String subject,
            String body,
            Channel channel,
            Purpose purpose,
            Confidentiality confidentiality,
            Set<String> recipientIds
        ) {
            Stakeholder sender = getStakeholder(senderId);

            if (!policy.canSend(sender, purpose)) {
                throw new AuthorizationException(
                    "Sender is not authorized."
                );
            }

            for (String recipientId : recipientIds) {
                Stakeholder recipient = getStakeholder(recipientId);

                if (!policy.canReceive(recipient, confidentiality)) {
                    throw new AuthorizationException(
                        "Recipient lacks sufficient clearance."
                    );
                }
            }

            ProjectMessage message = new ProjectMessage(
                senderId,
                subject,
                body,
                channel,
                purpose,
                confidentiality,
                recipientIds
            );

            messages.put(message.id(), message);

            audit("MESSAGE_CREATED", message.id(), senderId);

            return message;
        }

        void sendMessage(String messageId) {
            ProjectMessage message = messages.get(messageId);

            if (message == null) {
                throw new NotFoundException("Message not found.");
            }

            Stakeholder sender = getStakeholder(message.senderId());

            if (!policy.canSend(sender, message.purpose())) {
                throw new AuthorizationException(
                    "Sender authorization changed."
                );
            }

            for (String recipientId : message.recipientIds()) {
                Stakeholder recipient = getStakeholder(recipientId);

                if (!policy.canReceive(
                    recipient,
                    message.confidentiality()
                )) {
                    throw new AuthorizationException(
                        "Recipient authorization changed."
                    );
                }
            }

            message.send();

            audit("MESSAGE_SENT", messageId, message.senderId());
        }

        void acknowledgeMessage(
            String messageId,
            String stakeholderId
        ) {
            ProjectMessage message = messages.get(messageId);

            if (message == null) {
                throw new NotFoundException("Message not found.");
            }

            getStakeholder(stakeholderId);

            message.acknowledge(stakeholderId);

            audit(
                "MESSAGE_ACKNOWLEDGED",
                messageId,
                stakeholderId
            );
        }

        List<String> escalateUnacknowledged(
            String messageId,
            Duration maximumWait
        ) {
            ProjectMessage message = messages.get(messageId);

            if (message == null) {
                throw new NotFoundException("Message not found.");
            }

            if (maximumWait.isNegative()) {
                throw new ValidationException(
                    "Maximum wait cannot be negative."
                );
            }

            if (message.state() != MessageState.SENT ||
                message.sentAt() == null) {
                return List.of();
            }

            if (Duration.between(
                message.sentAt(),
                Instant.now()
            ).compareTo(maximumWait) <= 0) {
                return List.of();
            }

            List<String> pending = message.recipientIds()
                .stream()
                .filter(id -> !message.acknowledgements().contains(id))
                .toList();

            if (!pending.isEmpty()) {
                message.escalate();

                audit(
                    "MESSAGE_ESCALATED",
                    messageId,
                    message.senderId()
                );
            }

            return pending;
        }

        // ----------------------------------------------------
        // MEETINGS
        // ----------------------------------------------------

        Meeting scheduleMeeting(
            String organizerId,
            String title,
            Set<String> participants,
            Instant scheduledAt,
            List<String> agenda
        ) {
            getStakeholder(organizerId);

            participants.forEach(this::getStakeholder);

            Meeting meeting = new Meeting(
                organizerId,
                title,
                participants,
                scheduledAt,
                agenda
            );

            meetings.put(meeting.id(), meeting);

            audit(
                "MEETING_SCHEDULED",
                meeting.id(),
                organizerId
            );

            return meeting;
        }

        void finalizeMeeting(
            String meetingId,
            String organizerId,
            String minutes
        ) {
            Meeting meeting = meetings.get(meetingId);

            if (meeting == null) {
                throw new NotFoundException("Meeting not found.");
            }

            meeting.finalizeMeeting(organizerId, minutes);

            audit(
                "MEETING_FINALIZED",
                meetingId,
                organizerId
            );
        }

        Decision recordDecision(
            String meetingId,
            String ownerId,
            String description,
            boolean approved
        ) {
            Meeting meeting = meetings.get(meetingId);

            if (meeting == null || !meeting.completed()) {
                throw new StateTransitionException(
                    "Decision requires completed meeting."
                );
            }

            getStakeholder(ownerId);

            Decision decision = new Decision(
                newId("DEC"),
                meetingId,
                requireText(description, "Decision description"),
                ownerId,
                approved,
                Instant.now()
            );

            decisions.put(decision.id(), decision);

            audit(
                "DECISION_RECORDED",
                decision.id(),
                ownerId
            );

            return decision;
        }

        // ----------------------------------------------------
        // ACTION ITEMS
        // ----------------------------------------------------

        ActionItem createAction(
            String description,
            String assignedTo,
            String createdBy,
            Instant dueDate
        ) {
            getStakeholder(assignedTo);
            getStakeholder(createdBy);

            ActionItem action = new ActionItem(
                description,
                assignedTo,
                createdBy,
                dueDate
            );

            actions.put(action.id(), action);

            audit(
                "ACTION_CREATED",
                action.id(),
                createdBy
            );

            return action;
        }

        List<ActionItem> overdueActions() {
            Instant now = Instant.now();

            return actions.values()
                .stream()
                .filter(action ->
                    action.dueDate().isBefore(now) &&
                    action.state() != ActionState.COMPLETED &&
                    action.state() != ActionState.CANCELLED
                )
                .toList();
        }

        // ----------------------------------------------------
        // REPORTING
        // ----------------------------------------------------

        CommunicationMetrics metrics() {
            int expected = messages.values()
                .stream()
                .filter(message -> message.sentAt() != null)
                .mapToInt(message -> message.recipientIds().size())
                .sum();

            int actual = messages.values()
                .stream()
                .mapToInt(message -> message.acknowledgements().size())
                .sum();

            int sent = (int) messages.values()
                .stream()
                .filter(message -> message.sentAt() != null)
                .count();

            double rate = expected == 0
                ? 0.0
                : actual * 100.0 / expected;

            return new CommunicationMetrics(
                stakeholders.size(),
                messages.size(),
                sent,
                expected,
                actual,
                Math.round(rate * 100.0) / 100.0,
                overdueActions().size(),
                meetings.size(),
                decisions.size(),
                audit.size()
            );
        }

        void printReport() {
            CommunicationMetrics report = metrics();

            System.out.println("\nPROJECT COMMUNICATION REPORT");
            System.out.println("Project: " + projectName);
            System.out.println("Stakeholders: " + report.stakeholderCount());
            System.out.println("Messages: " + report.messageCount());
            System.out.println("Sent messages: " + report.sentMessages());

            System.out.println(
                "Acknowledgement rate: " +
                report.acknowledgementRate() + "%"
            );

            System.out.println("Overdue actions: " + report.overdueActions());
            System.out.println("Meetings: " + report.meetings());
            System.out.println("Decisions: " + report.decisions());
            System.out.println("Audit events: " + report.auditEvents());

            System.out.println("\nSTAKEHOLDER ENGAGEMENT");

            stakeholders.values()
                .stream()
                .sorted((a, b) ->
                    Integer.compare(
                        b.influence() * b.interest(),
                        a.influence() * a.interest()
                    )
                )
                .forEach(stakeholder ->
                    System.out.println(
                        stakeholder.name() + " | " +
                        stakeholder.engagementStrategy()
                    )
                );
        }

        List<AuditEvent> auditTrail() {
            return List.copyOf(audit);
        }
    }

    // ========================================================
    // EXECUTABLE ENTERPRISE SCENARIO
    // ========================================================

    public static void main(String[] args) {

        try {

            CommunicationService service =
                new CommunicationService(
                    "Enterprise Project Management System",
                    new DefaultCommunicationPolicy()
                );

            Stakeholder manager = new Stakeholder(
                "ST-001",
                "Project Manager",
                "manager@example.com",
                Role.PROJECT_MANAGER,
                5,
                5,
                Confidentiality.RESTRICTED,
                true
            );

            Stakeholder sponsor = new Stakeholder(
                "ST-002",
                "Project Sponsor",
                "sponsor@example.com",
                Role.SPONSOR,
                5,
                4,
                Confidentiality.CONFIDENTIAL,
                true
            );

            Stakeholder developer = new Stakeholder(
                "ST-003",
                "Development Lead",
                "developer@example.com",
                Role.DEVELOPER,
                3,
                5,
                Confidentiality.INTERNAL,
                true
            );

            Stakeholder client = new Stakeholder(
                "ST-004",
                "Client Representative",
                "client@example.com",
                Role.CLIENT,
                4,
                5,
                Confidentiality.CONFIDENTIAL,
                true
            );

            service.addStakeholder(manager);
            service.addStakeholder(sponsor);
            service.addStakeholder(developer);
            service.addStakeholder(client);

            CommunicationPlan plan = new CommunicationPlan(
                "PLAN-001",
                sponsor.id(),
                manager.id(),
                Channel.EMAIL,
                Purpose.STATUS_UPDATE,
                "weekly",
                Instant.now().plus(Duration.ofDays(7)),
                true
            );

            service.addPlan(plan);

            ProjectMessage message = service.createMessage(
                manager.id(),
                "Weekly Project Status",
                "Development is 65 percent complete.",
                Channel.EMAIL,
                Purpose.STATUS_UPDATE,
                Confidentiality.INTERNAL,
                Set.of(sponsor.id(), developer.id())
            );

            service.sendMessage(message.id());

            service.acknowledgeMessage(
                message.id(),
                sponsor.id()
            );

            service.acknowledgeMessage(
                message.id(),
                developer.id()
            );

            Meeting meeting = service.scheduleMeeting(
                manager.id(),
                "Weekly Project Review",
                Set.of(
                    sponsor.id(),
                    developer.id(),
                    client.id()
                ),
                Instant.now().plus(Duration.ofDays(1)),
                List.of(
                    "Progress review",
                    "Risk assessment",
                    "Testing preparation"
                )
            );

            service.finalizeMeeting(
                meeting.id(),
                manager.id(),
                "Testing preparation approved. Delivery schedule unchanged."
            );

            service.recordDecision(
                meeting.id(),
                sponsor.id(),
                "Approve testing preparation.",
                true
            );

            ActionItem action = service.createAction(
                "Prepare the testing plan.",
                developer.id(),
                manager.id(),
                Instant.now().plus(Duration.ofDays(5))
            );

            action.update(
                developer.id(),
                ActionState.IN_PROGRESS
            );

            service.printReport();

            // Verify important workflow outcomes.
            if (message.state() != MessageState.ACKNOWLEDGED) {
                throw new IllegalStateException(
                    "Acknowledgement validation failed."
                );
            }

            if (!meeting.completed()) {
                throw new IllegalStateException(
                    "Meeting validation failed."
                );
            }

            if (action.state() != ActionState.IN_PROGRESS) {
                throw new IllegalStateException(
                    "Action validation failed."
                );
            }

            // Validate authorization failure.
            try {
                service.createMessage(
                    developer.id(),
                    "Restricted update",
                    "This communication must be rejected.",
                    Channel.EMAIL,
                    Purpose.ESCALATION,
                    Confidentiality.RESTRICTED,
                    Set.of(sponsor.id())
                );
            } catch (AuthorizationException exception) {
                System.out.println(
                    "\nUnauthorized communication rejected: " +
                    exception.getMessage()
                );
            }

            // Validate invalid action transition.
            try {
                action.update(
                    developer.id(),
                    ActionState.OPEN
                );
            } catch (StateTransitionException exception) {
                System.out.println(
                    "Invalid transition rejected: " +
                    exception.getMessage()
                );
            }

            System.out.println(
                "\nAudit records: " + service.auditTrail().size()
            );

            System.out.println(
                "All enterprise communication checks completed."
            );

        } catch (CommunicationException exception) {
            System.err.println(
                "Communication system error: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
