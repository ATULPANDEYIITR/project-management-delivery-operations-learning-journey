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
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class TeamCommunication {

    enum Role {
        ADMIN,
        MANAGER,
        MEMBER,
        OBSERVER
    }

    enum ChannelType {
        GENERAL,
        PROJECT,
        ANNOUNCEMENT,
        INCIDENT,
        PRIVATE
    }

    enum Priority {
        LOW,
        NORMAL,
        HIGH,
        URGENT
    }

    enum MessageStatus {
        SENT,
        ACKNOWLEDGED,
        RESOLVED,
        ARCHIVED
    }

    enum TaskStatus {
        OPEN,
        IN_PROGRESS,
        BLOCKED,
        COMPLETED
    }

    enum EventType {
        MESSAGE_SENT,
        MESSAGE_READ,
        MESSAGE_ACKNOWLEDGED,
        TASK_ASSIGNED,
        TASK_COMPLETED,
        TASK_BLOCKED,
        CHANNEL_CREATED
    }

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

    static class ValidationException extends CommunicationException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class ConflictException extends CommunicationException {
        ConflictException(String message) {
            super(message);
        }
    }

    record User(
        String id,
        String name,
        String email,
        Role role,
        boolean active
    ) {
        private static final Pattern EMAIL_PATTERN =
            Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$");

        User {
            Objects.requireNonNull(id);
            Objects.requireNonNull(role);

            if (name == null || name.isBlank()) {
                throw new ValidationException("User name is required.");
            }

            if (email == null ||
                !EMAIL_PATTERN.matcher(email).matches()) {
                throw new ValidationException("Invalid email address.");
            }

            name = name.trim();
            email = email.toLowerCase();
        }
    }

    static class Channel {
        private final String id;
        private final String name;
        private final ChannelType type;
        private final String createdBy;
        private final Set<String> members = new HashSet<>();
        private boolean archived;

        Channel(
            String id,
            String name,
            ChannelType type,
            String createdBy,
            Set<String> members
        ) {
            this.id = id;
            this.name = name;
            this.type = type;
            this.createdBy = createdBy;
            this.members.addAll(members);
        }

        String getId() {
            return id;
        }

        Set<String> getMembers() {
            return Collections.unmodifiableSet(members);
        }
    }

    static class Message {
        private final String id;
        private final String channelId;
        private final String senderId;
        private String content;
        private final Priority priority;
        private final Instant createdAt;
        private Instant editedAt;
        private final String parentId;

        private final Set<String> recipients;
        private final Set<String> readBy = new HashSet<>();
        private final Set<String> acknowledgedBy = new HashSet<>();

        private MessageStatus status = MessageStatus.SENT;

        Message(
            String id,
            String channelId,
            String senderId,
            String content,
            Priority priority,
            Instant createdAt,
            String parentId,
            Set<String> recipients
        ) {
            this.id = id;
            this.channelId = channelId;
            this.senderId = senderId;
            this.content = content;
            this.priority = priority;
            this.createdAt = createdAt;
            this.parentId = parentId;
            this.recipients = new HashSet<>(recipients);
        }

        String getId() {
            return id;
        }

        MessageStatus getStatus() {
            return status;
        }

        Set<String> getAcknowledgedBy() {
            return Collections.unmodifiableSet(acknowledgedBy);
        }
    }

    static class ActionItem {
        private final String id;
        private final String messageId;
        private final String ownerId;
        private final String title;
        private final Instant dueAt;
        private final Instant createdAt;
        private TaskStatus status = TaskStatus.OPEN;

        ActionItem(
            String id,
            String messageId,
            String ownerId,
            String title,
            Instant dueAt
        ) {
            this.id = id;
            this.messageId = messageId;
            this.ownerId = ownerId;
            this.title = title;
            this.dueAt = dueAt;
            this.createdAt = Instant.now();
        }

        TaskStatus getStatus() {
            return status;
        }
    }

    record AuditEvent(
        String actorId,
        String action,
        String targetId,
        Instant timestamp
    ) {}

    record Notification(
        String id,
        String recipientId,
        String eventType,
        String targetId,
        Instant createdAt
    ) {}

    record Escalation(
        String messageId,
        Priority priority,
        Set<String> pendingRecipients,
        long ageMinutes
    ) {}

    record ChannelReport(
        String channelId,
        int totalMessages,
        int acknowledgedMessages,
        int unreadMessages,
        int totalTasks,
        int completedTasks,
        double acknowledgementRate
    ) {}

    interface NotificationGateway {
        void deliver(Notification notification);
    }

    static class NotificationService {
        private final Map<String, List<Notification>> queues =
            new HashMap<>();

        private final List<Notification> deliveryHistory =
            new ArrayList<>();

        void enqueue(Notification notification) {
            queues.computeIfAbsent(
                notification.recipientId(),
                ignored -> new ArrayList<>()
            ).add(notification);
        }

        int dispatch(
            String recipientId,
            NotificationGateway gateway
        ) {
            List<Notification> queue =
                queues.getOrDefault(recipientId, List.of());

            List<Notification> failed = new ArrayList<>();
            int delivered = 0;

            for (Notification notification : queue) {
                try {
                    gateway.deliver(notification);
                    deliveryHistory.add(notification);
                    delivered++;
                } catch (RuntimeException error) {
                    failed.add(notification);
                }
            }

            queues.put(recipientId, failed);
            return delivered;
        }

        int pendingCount(String userId) {
            return queues.getOrDefault(userId, List.of()).size();
        }
    }

    static class EventBus {
        private final Map<EventType, List<Consumer<Object>>> listeners =
            new EnumMap<>(EventType.class);

        void subscribe(
            EventType event,
            Consumer<Object> listener
        ) {
            listeners.computeIfAbsent(
                event,
                ignored -> new CopyOnWriteArrayList<>()
            ).add(listener);
        }

        void publish(EventType event, Object payload) {
            List<Consumer<Object>> subscribers =
                listeners.getOrDefault(event, List.of());

            List<RuntimeException> failures = new ArrayList<>();

            for (Consumer<Object> subscriber : subscribers) {
                try {
                    subscriber.accept(payload);
                } catch (RuntimeException error) {
                    failures.add(error);
                }
            }

            if (!failures.isEmpty()) {
                System.err.println(
                    failures.size() + " event handler(s) failed for " + event
                );
            }
        }
    }

    static class ReviewPolicy {
        private final int minimumApprovals;
        private final boolean requireAcknowledgment;
        private final boolean prohibitSelfApproval;

        ReviewPolicy(
            int minimumApprovals,
            boolean requireAcknowledgment,
            boolean prohibitSelfApproval
        ) {
            if (minimumApprovals < 0) {
                throw new ValidationException("Invalid approval threshold.");
            }

            this.minimumApprovals = minimumApprovals;
            this.requireAcknowledgment = requireAcknowledgment;
            this.prohibitSelfApproval = prohibitSelfApproval;
        }

        boolean isAcknowledgmentRequired() {
            return requireAcknowledgment;
        }

        boolean canApprove(
            String senderId,
            String reviewerId,
            Set<String> acknowledgedBy
        ) {
            if (prohibitSelfApproval && senderId.equals(reviewerId)) {
                return false;
            }

            return !requireAcknowledgment ||
                acknowledgedBy.contains(reviewerId);
        }

        int getMinimumApprovals() {
            return minimumApprovals;
        }
    }

    static class TeamCommunicationService {
        private final Map<String, User> users = new HashMap<>();
        private final Map<String, Channel> channels = new HashMap<>();
        private final Map<String, Message> messages = new HashMap<>();
        private final Map<String, ActionItem> tasks = new HashMap<>();

        private final List<AuditEvent> auditLog = new ArrayList<>();

        private final NotificationService notificationService =
            new NotificationService();

        private final EventBus eventBus = new EventBus();

        private final ReviewPolicy acknowledgmentPolicy =
            new ReviewPolicy(0, false, true);

        TeamCommunicationService() {
            eventBus.subscribe(
                EventType.MESSAGE_SENT,
                payload -> {
                    Message message = (Message) payload;

                    for (String recipient : message.recipients) {
                        notificationService.enqueue(
                            new Notification(
                                UUID.randomUUID().toString(),
                                recipient,
                                "NEW_MESSAGE",
                                message.id,
                                Instant.now()
                            )
                        );
                    }
                }
            );

            eventBus.subscribe(
                EventType.TASK_ASSIGNED,
                payload -> {
                    ActionItem task = (ActionItem) payload;

                    notificationService.enqueue(
                        new Notification(
                            UUID.randomUUID().toString(),
                            task.ownerId,
                            "TASK_ASSIGNED",
                            task.id,
                            Instant.now()
                        )
                    );
                }
            );
        }

        private void audit(
            String actorId,
            String action,
            String targetId
        ) {
            auditLog.add(new AuditEvent(
                actorId,
                action,
                targetId,
                Instant.now()
            ));
        }

        private User requireUser(String userId) {
            User user = users.get(userId);

            if (user == null || !user.active()) {
                throw new AuthorizationException("User unavailable.");
            }

            return user;
        }

        private Channel requireChannel(String channelId) {
            Channel channel = channels.get(channelId);

            if (channel == null || channel.archived) {
                throw new ValidationException("Channel unavailable.");
            }

            return channel;
        }

        private void requireMembership(
            String userId,
            String channelId
        ) {
            requireUser(userId);
            Channel channel = requireChannel(channelId);

            if (!channel.members.contains(userId)) {
                throw new AuthorizationException(
                    "Channel membership required."
                );
            }
        }

        User registerUser(
            String name,
            String email,
            Role role
        ) {
            User user = new User(
                UUID.randomUUID().toString(),
                name,
                email,
                role,
                true
            );

            boolean duplicate = users.values().stream()
                .anyMatch(existing ->
                    existing.email().equalsIgnoreCase(user.email())
                );

            if (duplicate) {
                throw new ConflictException("Duplicate email address.");
            }

            users.put(user.id(), user);
            audit(user.id(), "USER_REGISTERED", user.id());

            return user;
        }

        Channel createChannel(
            String creatorId,
            String name,
            ChannelType type,
            Set<String> requestedMembers
        ) {
            User creator = requireUser(creatorId);

            if (creator.role() != Role.ADMIN &&
                creator.role() != Role.MANAGER) {
                throw new AuthorizationException(
                    "Channel creation permission denied."
                );
            }

            if (name == null || name.isBlank() || name.length() > 80) {
                throw new ValidationException("Invalid channel name.");
            }

            Set<String> members = new HashSet<>(requestedMembers);
            members.add(creatorId);

            members.forEach(this::requireUser);

            if (type == ChannelType.PRIVATE && members.size() < 2) {
                throw new ValidationException(
                    "Private channels require at least two members."
                );
            }

            Channel channel = new Channel(
                UUID.randomUUID().toString(),
                name.trim(),
                type,
                creatorId,
                members
            );

            channels.put(channel.id, channel);
            audit(creatorId, "CHANNEL_CREATED", channel.id);

            eventBus.publish(EventType.CHANNEL_CREATED, channel);

            return channel;
        }

        void addMember(
            String actorId,
            String channelId,
            String memberId
        ) {
            requireMembership(actorId, channelId);
            requireUser(memberId);

            User actor = requireUser(actorId);

            if (actor.role() != Role.ADMIN &&
                actor.role() != Role.MANAGER) {
                throw new AuthorizationException(
                    "Member management denied."
                );
            }

            requireChannel(channelId).members.add(memberId);
            audit(actorId, "MEMBER_ADDED", channelId);
        }

        Message sendMessage(
            String senderId,
            String channelId,
            String content,
            Priority priority,
            Set<String> requestedRecipients,
            String parentId
        ) {
            requireMembership(senderId, channelId);

            User sender = requireUser(senderId);
            Channel channel = requireChannel(channelId);

            if (sender.role() == Role.OBSERVER) {
                throw new AuthorizationException(
                    "Observers cannot send messages."
                );
            }

            if (channel.type == ChannelType.ANNOUNCEMENT &&
                sender.role() != Role.ADMIN &&
                sender.role() != Role.MANAGER) {
                throw new AuthorizationException(
                    "Announcement permission denied."
                );
            }

            if (content == null ||
                content.isBlank() ||
                content.length() > 10000) {
                throw new ValidationException("Invalid message content.");
            }

            if (parentId != null) {
                Message parent = messages.get(parentId);

                if (parent == null ||
                    !parent.channelId.equals(channelId)) {
                    throw new ValidationException("Invalid reply reference.");
                }
            }

            Set<String> recipients = requestedRecipients == null
                ? new HashSet<>(channel.members)
                : new HashSet<>(requestedRecipients);

            recipients.remove(senderId);

            if (!channel.members.containsAll(recipients)) {
                throw new AuthorizationException(
                    "All recipients must belong to the channel."
                );
            }

            Message message = new Message(
                UUID.randomUUID().toString(),
                channelId,
                senderId,
                content.trim(),
                priority,
                Instant.now(),
                parentId,
                recipients
            );

            messages.put(message.id, message);
            audit(senderId, "MESSAGE_SENT", message.id);

            eventBus.publish(EventType.MESSAGE_SENT, message);

            return message;
        }

        void markRead(String userId, String messageId) {
            Message message = messages.get(messageId);

            if (message == null) {
                throw new ValidationException("Message not found.");
            }

            requireMembership(userId, message.channelId);

            if (!message.senderId.equals(userId) &&
                !message.recipients.contains(userId)) {
                throw new AuthorizationException("Message access denied.");
            }

            message.readBy.add(userId);
            audit(userId, "MESSAGE_READ", messageId);

            eventBus.publish(EventType.MESSAGE_READ, message);
        }

        void acknowledge(String userId, String messageId) {
            markRead(userId, messageId);

            Message message = messages.get(messageId);

            if (!message.recipients.contains(userId)) {
                throw new AuthorizationException(
                    "Only recipients can acknowledge."
                );
            }

            if (!acknowledgmentPolicy.canApprove(
                message.senderId,
                userId,
                message.acknowledgedBy
            )) {
                throw new AuthorizationException(
                    "Acknowledgment policy rejected the operation."
                );
            }

            message.acknowledgedBy.add(userId);

            if (message.acknowledgedBy.containsAll(message.recipients)) {
                message.status = MessageStatus.ACKNOWLEDGED;
            }

            audit(userId, "MESSAGE_ACKNOWLEDGED", messageId);

            eventBus.publish(
                EventType.MESSAGE_ACKNOWLEDGED,
                message
            );
        }

        void editMessage(
            String actorId,
            String messageId,
            String content
        ) {
            User actor = requireUser(actorId);
            Message message = messages.get(messageId);

            if (message == null) {
                throw new ValidationException("Message not found.");
            }

            if (!message.senderId.equals(actorId) &&
                actor.role() != Role.ADMIN) {
                throw new AuthorizationException("Edit permission denied.");
            }

            if (message.status == MessageStatus.ARCHIVED) {
                throw new ConflictException(
                    "Archived messages cannot be edited."
                );
            }

            if (content == null ||
                content.isBlank() ||
                content.length() > 10000) {
                throw new ValidationException("Invalid message content.");
            }

            message.content = content.trim();
            message.editedAt = Instant.now();

            audit(actorId, "MESSAGE_EDITED", messageId);
        }

        ActionItem assignTask(
            String creatorId,
            String messageId,
            String ownerId,
            String title,
            Instant dueAt
        ) {
            Message message = messages.get(messageId);

            if (message == null) {
                throw new ValidationException("Message not found.");
            }

            requireMembership(creatorId, message.channelId);
            requireMembership(ownerId, message.channelId);

            User creator = requireUser(creatorId);

            if (!message.senderId.equals(creatorId) &&
                creator.role() != Role.ADMIN &&
                creator.role() != Role.MANAGER) {
                throw new AuthorizationException("Task assignment denied.");
            }

            if (title == null || title.isBlank() ||
                dueAt == null || !dueAt.isAfter(Instant.now())) {
                throw new ValidationException("Invalid task details.");
            }

            ActionItem task = new ActionItem(
                UUID.randomUUID().toString(),
                messageId,
                ownerId,
                title.trim(),
                dueAt
            );

            tasks.put(task.id, task);
            audit(creatorId, "TASK_ASSIGNED", task.id);

            eventBus.publish(EventType.TASK_ASSIGNED, task);

            return task;
        }

        void updateTask(
            String actorId,
            String taskId,
            TaskStatus nextStatus
        ) {
            User actor = requireUser(actorId);
            ActionItem task = tasks.get(taskId);

            if (task == null) {
                throw new ValidationException("Task not found.");
            }

            Message message = messages.get(task.messageId);

            boolean authorized =
                actorId.equals(task.ownerId) ||
                actorId.equals(message.senderId) ||
                actor.role() == Role.ADMIN ||
                actor.role() == Role.MANAGER;

            if (!authorized) {
                throw new AuthorizationException("Task update denied.");
            }

            Map<TaskStatus, Set<TaskStatus>> transitions =
                Map.of(
                    TaskStatus.OPEN,
                    Set.of(
                        TaskStatus.IN_PROGRESS,
                        TaskStatus.BLOCKED,
                        TaskStatus.COMPLETED
                    ),
                    TaskStatus.IN_PROGRESS,
                    Set.of(
                        TaskStatus.OPEN,
                        TaskStatus.BLOCKED,
                        TaskStatus.COMPLETED
                    ),
                    TaskStatus.BLOCKED,
                    Set.of(
                        TaskStatus.OPEN,
                        TaskStatus.IN_PROGRESS
                    ),
                    TaskStatus.COMPLETED,
                    Set.of()
                );

            if (task.status != nextStatus &&
                !transitions.get(task.status).contains(nextStatus)) {
                throw new ConflictException(
                    "Invalid task state transition."
                );
            }

            task.status = nextStatus;
            audit(actorId, "TASK_UPDATED", taskId);

            if (nextStatus == TaskStatus.COMPLETED) {
                eventBus.publish(EventType.TASK_COMPLETED, task);
            } else if (nextStatus == TaskStatus.BLOCKED) {
                eventBus.publish(EventType.TASK_BLOCKED, task);
            }
        }

        List<Escalation> getEscalations(Instant now) {
            return messages.values().stream()
                .filter(message ->
                    message.priority == Priority.HIGH ||
                    message.priority == Priority.URGENT
                )
                .filter(message ->
                    message.status != MessageStatus.RESOLVED &&
                    message.status != MessageStatus.ARCHIVED
                )
                .map(message -> {
                    long age = Duration.between(
                        message.createdAt,
                        now
                    ).toMinutes();

                    long threshold =
                        message.priority == Priority.URGENT ? 15 : 240;

                    Set<String> pending = new HashSet<>(
                        message.recipients
                    );

                    pending.removeAll(message.acknowledgedBy);

                    return new Escalation(
                        message.id,
                        message.priority,
                        Set.copyOf(pending),
                        age
                    );
                })
                .filter(item ->
                    item.ageMinutes() >
                    (item.priority() == Priority.URGENT ? 15 : 240)
                    && !item.pendingRecipients().isEmpty()
                )
                .toList();
        }

        ChannelReport getChannelReport(
            String viewerId,
            String channelId
        ) {
            requireMembership(viewerId, channelId);

            List<Message> channelMessages = messages.values().stream()
                .filter(message ->
                    message.channelId.equals(channelId)
                )
                .toList();

            int total = channelMessages.size();

            int acknowledged = (int) channelMessages.stream()
                .filter(message ->
                    message.status == MessageStatus.ACKNOWLEDGED
                )
                .count();

            int unread = (int) channelMessages.stream()
                .filter(message ->
                    message.recipients.contains(viewerId) &&
                    !message.readBy.contains(viewerId)
                )
                .count();

            Set<String> messageIds = channelMessages.stream()
                .map(message -> message.id)
                .collect(Collectors.toSet());

            List<ActionItem> channelTasks = tasks.values().stream()
                .filter(task -> messageIds.contains(task.messageId))
                .toList();

            int completed = (int) channelTasks.stream()
                .filter(task -> task.status == TaskStatus.COMPLETED)
                .count();

            double rate = total == 0
                ? 0.0
                : (double) acknowledged / total;

            return new ChannelReport(
                channelId,
                total,
                acknowledged,
                unread,
                channelTasks.size(),
                completed,
                rate
            );
        }

        int dispatchNotifications(
            String userId,
            NotificationGateway gateway
        ) {
            requireUser(userId);
            return notificationService.dispatch(userId, gateway);
        }

        List<AuditEvent> getAuditLog() {
            return List.copyOf(auditLog);
        }
    }

    public static void main(String[] args) {
        TeamCommunicationService service =
            new TeamCommunicationService();

        try {
            User manager = service.registerUser(
                "Project Manager",
                "manager@example.com",
                Role.MANAGER
            );

            User engineer = service.registerUser(
                "Software Engineer",
                "engineer@example.com",
                Role.MEMBER
            );

            User analyst = service.registerUser(
                "Quality Analyst",
                "analyst@example.com",
                Role.MEMBER
            );

            User observer = service.registerUser(
                "Read Only Observer",
                "observer@example.com",
                Role.OBSERVER
            );

            Channel channel = service.createChannel(
                manager.id(),
                "Enterprise Delivery",
                ChannelType.PROJECT,
                Set.of(engineer.id(), analyst.id())
            );

            Message message = service.sendMessage(
                manager.id(),
                channel.getId(),
                "Complete the integration tests before deployment.",
                Priority.HIGH,
                null,
                null
            );

            service.markRead(engineer.id(), message.getId());

            service.acknowledge(
                engineer.id(),
                message.getId()
            );

            service.acknowledge(
                analyst.id(),
                message.getId()
            );

            ActionItem task = service.assignTask(
                manager.id(),
                message.getId(),
                engineer.id(),
                "Complete integration testing",
                Instant.now().plus(Duration.ofDays(2))
            );

            service.updateTask(
                engineer.id(),
                task.id,
                TaskStatus.IN_PROGRESS
            );

            int delivered = service.dispatchNotifications(
                engineer.id(),
                notification -> System.out.println(
                    "Delivered: " + notification.eventType()
                    + " -> " + notification.targetId()
                )
            );

            System.out.println("\nCHANNEL REPORT");

            ChannelReport report = service.getChannelReport(
                manager.id(),
                channel.getId()
            );

            System.out.println("Messages: " + report.totalMessages());
            System.out.println(
                "Acknowledged: " + report.acknowledgedMessages()
            );
            System.out.println("Unread: " + report.unreadMessages());
            System.out.println("Tasks: " + report.totalTasks());
            System.out.println(
                "Acknowledgment rate: "
                + report.acknowledgementRate()
            );

            System.out.println("Notifications delivered: " + delivered);

            System.out.println(
                "Escalations: "
                + service.getEscalations(Instant.now()).size()
            );

            try {
                service.sendMessage(
                    observer.id(),
                    channel.getId(),
                    "Unauthorized message",
                    Priority.NORMAL,
                    null,
                    null
                );
            } catch (AuthorizationException error) {
                System.out.println(
                    "Expected authorization failure: " + error.getMessage()
                );
            }

            try {
                service.updateTask(
                    engineer.id(),
                    task.id,
                    TaskStatus.COMPLETED
                );

                service.updateTask(
                    engineer.id(),
                    task.id,
                    TaskStatus.IN_PROGRESS
                );
            } catch (ConflictException error) {
                System.out.println(
                    "Expected state conflict: " + error.getMessage()
                );
            }

            System.out.println(
                "Audit events: " + service.getAuditLog().size()
            );

        } catch (CommunicationException error) {
            System.err.println("Communication failure: " + error.getMessage());
            System.exit(1);
        }
    }
}
