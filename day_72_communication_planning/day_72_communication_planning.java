import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Enterprise Communication Planning System.
 *
 * Java 17
 * No external dependencies.
 *
 * Implements stakeholder analysis, communication objectives,
 * activity scheduling, approval policies, delivery coordination,
 * feedback collection, audit events, and performance reporting.
 */
public class CommunicationPlanningSystem {

    enum Channel {
        EMAIL,
        MEETING,
        REPORT,
        NEWSLETTER,
        WEBSITE,
        SOCIAL_MEDIA,
        PHONE,
        WORKSHOP
    }

    enum Priority {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum ObjectiveStatus {
        DRAFT,
        ACTIVE,
        COMPLETED,
        CANCELLED
    }

    enum ActivityStatus {
        PLANNED,
        APPROVED,
        SCHEDULED,
        IN_PROGRESS,
        SENT,
        COMPLETED,
        FAILED,
        CANCELLED
    }

    enum AudienceType {
        INTERNAL,
        EXTERNAL,
        MANAGEMENT,
        TECHNICAL,
        PUBLIC
    }

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

    static class PolicyException extends CommunicationException {
        PolicyException(String message) {
            super(message);
        }
    }

    record Stakeholder(
        String name,
        AudienceType audience,
        String department,
        int influence,
        int interest,
        List<Channel> preferredChannels
    ) {
        Stakeholder {
            if (name == null || name.isBlank()) {
                throw new ValidationException("Stakeholder name is required.");
            }

            Objects.requireNonNull(audience);

            if (influence < 1 || influence > 5 ||
                interest < 1 || interest > 5) {
                throw new ValidationException(
                    "Influence and interest must be between 1 and 5."
                );
            }

            department = department == null ? "" : department;

            preferredChannels = preferredChannels == null
                ? List.of()
                : List.copyOf(preferredChannels);
        }
    }

    static final class CommunicationObjective {
        private final UUID id;
        private final String title;
        private final String description;
        private final String desiredOutcome;
        private final Set<String> audiences;
        private final Instant deadline;
        private final Priority priority;

        private ObjectiveStatus status;

        CommunicationObjective(
            String title,
            String description,
            String desiredOutcome,
            Collection<String> audiences,
            Instant deadline,
            Priority priority
        ) {
            this.id = UUID.randomUUID();
            this.title = requireText(title, "Objective title");
            this.description = requireText(description, "Description");
            this.desiredOutcome = requireText(
                desiredOutcome,
                "Desired outcome"
            );

            if (audiences == null || audiences.isEmpty()) {
                throw new ValidationException(
                    "At least one target audience is required."
                );
            }

            this.audiences = Set.copyOf(audiences);
            this.deadline = Objects.requireNonNull(deadline);
            this.priority = Objects.requireNonNull(priority);
            this.status = ObjectiveStatus.DRAFT;
        }

        void activate() {
            if (status != ObjectiveStatus.DRAFT) {
                throw new PolicyException(
                    "Only draft objectives can be activated."
                );
            }

            status = ObjectiveStatus.ACTIVE;
        }

        void complete() {
            if (status != ObjectiveStatus.ACTIVE) {
                throw new PolicyException(
                    "Only active objectives can be completed."
                );
            }

            status = ObjectiveStatus.COMPLETED;
        }

        UUID id() {
            return id;
        }

        Instant deadline() {
            return deadline;
        }

        ObjectiveStatus status() {
            return status;
        }

        Priority priority() {
            return priority;
        }

        Set<String> audiences() {
            return audiences;
        }

        String title() {
            return title;
        }
    }

    record CommunicationFeedback(
        String respondent,
        int satisfaction,
        int understanding,
        String comments,
        Instant recordedAt
    ) {
        CommunicationFeedback {
            respondent = requireText(respondent, "Respondent");

            if (satisfaction < 1 || satisfaction > 5 ||
                understanding < 1 || understanding > 5) {
                throw new ValidationException(
                    "Feedback scores must be between 1 and 5."
                );
            }

            comments = comments == null ? "" : comments;
            recordedAt = Objects.requireNonNull(recordedAt);
        }
    }

    static final class CommunicationActivity {
        private final UUID id;
        private final UUID objectiveId;
        private final String title;
        private final String message;
        private final Channel channel;
        private final Set<String> audience;
        private final String owner;
        private final Instant scheduledAt;
        private final double cost;
        private final boolean approvalRequired;

        private String approvedBy;
        private ActivityStatus status;
        private Instant completedAt;

        private final List<CommunicationFeedback> feedback =
            new ArrayList<>();

        CommunicationActivity(
            UUID objectiveId,
            String title,
            String message,
            Channel channel,
            Collection<String> audience,
            String owner,
            Instant scheduledAt,
            double cost,
            boolean approvalRequired
        ) {
            this.id = UUID.randomUUID();
            this.objectiveId = Objects.requireNonNull(objectiveId);
            this.title = requireText(title, "Activity title");
            this.message = requireText(message, "Message");
            this.channel = Objects.requireNonNull(channel);

            if (audience == null || audience.isEmpty()) {
                throw new ValidationException("Audience cannot be empty.");
            }

            this.audience = Set.copyOf(audience);
            this.owner = requireText(owner, "Activity owner");
            this.scheduledAt = Objects.requireNonNull(scheduledAt);

            if (cost < 0 || !Double.isFinite(cost)) {
                throw new ValidationException("Invalid activity cost.");
            }

            this.cost = cost;
            this.approvalRequired = approvalRequired;
            this.status = ActivityStatus.PLANNED;
        }

        void transition(ActivityStatus next) {
            Map<ActivityStatus, Set<ActivityStatus>> allowed = Map.of(
                ActivityStatus.PLANNED,
                Set.of(
                    ActivityStatus.APPROVED,
                    ActivityStatus.CANCELLED
                ),
                ActivityStatus.APPROVED,
                Set.of(
                    ActivityStatus.SCHEDULED,
                    ActivityStatus.CANCELLED
                ),
                ActivityStatus.SCHEDULED,
                Set.of(
                    ActivityStatus.IN_PROGRESS,
                    ActivityStatus.CANCELLED
                ),
                ActivityStatus.IN_PROGRESS,
                Set.of(
                    ActivityStatus.SENT,
                    ActivityStatus.COMPLETED,
                    ActivityStatus.FAILED
                ),
                ActivityStatus.SENT,
                Set.of(
                    ActivityStatus.COMPLETED,
                    ActivityStatus.FAILED
                ),
                ActivityStatus.FAILED,
                Set.of(
                    ActivityStatus.SCHEDULED,
                    ActivityStatus.CANCELLED
                ),
                ActivityStatus.COMPLETED,
                Set.of(),
                ActivityStatus.CANCELLED,
                Set.of()
            );

            if (!allowed.get(status).contains(next)) {
                throw new PolicyException(
                    "Invalid transition: " + status + " -> " + next
                );
            }

            status = next;

            if (next == ActivityStatus.COMPLETED) {
                completedAt = Instant.now();
            }
        }

        void approve(String approver) {
            if (!approvalRequired) {
                throw new PolicyException(
                    "Activity does not require approval."
                );
            }

            if (status != ActivityStatus.PLANNED) {
                throw new PolicyException(
                    "Activity is not awaiting approval."
                );
            }

            approvedBy = requireText(approver, "Approver");
            transition(ActivityStatus.APPROVED);
            transition(ActivityStatus.SCHEDULED);
        }

        void addFeedback(CommunicationFeedback item) {
            feedback.add(Objects.requireNonNull(item));
        }

        UUID id() {
            return id;
        }

        UUID objectiveId() {
            return objectiveId;
        }

        String title() {
            return title;
        }

        String message() {
            return message;
        }

        Channel channel() {
            return channel;
        }

        Set<String> audience() {
            return audience;
        }

        String owner() {
            return owner;
        }

        Instant scheduledAt() {
            return scheduledAt;
        }

        double cost() {
            return cost;
        }

        ActivityStatus status() {
            return status;
        }

        List<CommunicationFeedback> feedback() {
            return Collections.unmodifiableList(feedback);
        }

        boolean approvalRequired() {
            return approvalRequired;
        }
    }

    record CommunicationPolicy(
        double budget,
        boolean requireExternalApproval,
        boolean requireCriticalApproval,
        boolean restrictWeekendActivities,
        int maximumActivities
    ) {
        CommunicationPolicy {
            if (budget < 0 || !Double.isFinite(budget)) {
                throw new ValidationException("Invalid budget.");
            }

            if (maximumActivities <= 0) {
                throw new ValidationException(
                    "Maximum activities must be positive."
                );
            }
        }
    }

    record AuditEvent(
        Instant timestamp,
        String event,
        String entityId,
        String details
    ) {}

    interface CommunicationListener {
        void onEvent(AuditEvent event);
    }

    record EvaluationReport(
        int totalActivities,
        int completedActivities,
        int failedActivities,
        double completionRate,
        double committedCost,
        double remainingBudget,
        int feedbackCount,
        double averageSatisfaction,
        double averageUnderstanding
    ) {}

    static class CommunicationService {

        private final CommunicationPolicy policy;

        private final Map<String, Stakeholder> stakeholders =
            new LinkedHashMap<>();

        private final Map<UUID, CommunicationObjective> objectives =
            new LinkedHashMap<>();

        private final Map<UUID, CommunicationActivity> activities =
            new LinkedHashMap<>();

        private final List<AuditEvent> auditEvents =
            new ArrayList<>();

        private final List<CommunicationListener> listeners =
            new ArrayList<>();

        CommunicationService(CommunicationPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void addListener(CommunicationListener listener) {
            listeners.add(Objects.requireNonNull(listener));
        }

        private void log(String event, String id, String details) {
            AuditEvent audit = new AuditEvent(
                Instant.now(),
                event,
                id,
                details
            );

            auditEvents.add(audit);

            // Listeners are isolated so a reporting failure cannot
            // roll back an already accepted planning operation.
            for (CommunicationListener listener : listeners) {
                try {
                    listener.onEvent(audit);
                } catch (RuntimeException exception) {
                    System.err.println(
                        "Listener failed: " + exception.getMessage()
                    );
                }
            }
        }

        void addStakeholder(Stakeholder stakeholder) {
            String key = stakeholder.name().toLowerCase(Locale.ROOT);

            if (stakeholders.putIfAbsent(key, stakeholder) != null) {
                throw new ValidationException("Duplicate stakeholder.");
            }

            log("STAKEHOLDER_CREATED", key, stakeholder.name());
        }

        void addObjective(CommunicationObjective objective) {
            if (objectives.putIfAbsent(objective.id(), objective) != null) {
                throw new ValidationException("Duplicate objective.");
            }

            log(
                "OBJECTIVE_CREATED",
                objective.id().toString(),
                objective.title()
            );
        }

        private CommunicationObjective getObjective(UUID id) {
            CommunicationObjective objective = objectives.get(id);

            if (objective == null) {
                throw new ValidationException("Objective not found.");
            }

            return objective;
        }

        private CommunicationActivity getActivity(UUID id) {
            CommunicationActivity activity = activities.get(id);

            if (activity == null) {
                throw new ValidationException("Activity not found.");
            }

            return activity;
        }

        private double committedCost() {
            return activities.values().stream()
                .filter(a -> a.status() != ActivityStatus.CANCELLED)
                .mapToDouble(CommunicationActivity::cost)
                .sum();
        }

        void schedule(CommunicationActivity activity) {
            CommunicationObjective objective =
                getObjective(activity.objectiveId());

            if (objective.status() != ObjectiveStatus.ACTIVE) {
                throw new PolicyException(
                    "Objective must be active."
                );
            }

            if (activity.scheduledAt().isAfter(objective.deadline())) {
                throw new PolicyException(
                    "Activity exceeds objective deadline."
                );
            }

            if (activities.size() >= policy.maximumActivities()) {
                throw new PolicyException("Activity capacity reached.");
            }

            if (activity.cost() > policy.budget() - committedCost()) {
                throw new PolicyException("Insufficient communication budget.");
            }

            for (String audience : activity.audience()) {
                if (!stakeholders.containsKey(
                    audience.toLowerCase(Locale.ROOT)
                )) {
                    throw new ValidationException(
                        "Unknown stakeholder: " + audience
                    );
                }
            }

            boolean external = activity.audience().stream()
                .map(name -> stakeholders.get(
                    name.toLowerCase(Locale.ROOT)
                ))
                .anyMatch(s -> s.audience() == AudienceType.EXTERNAL);

            boolean requiresApproval = activity.approvalRequired()
                || (external && policy.requireExternalApproval())
                || (objective.priority() == Priority.CRITICAL
                    && policy.requireCriticalApproval());

            if (policy.restrictWeekendActivities()) {
                int day = activity.scheduledAt()
                    .atZone(java.time.ZoneId.systemDefault())
                    .getDayOfWeek()
                    .getValue();

                if (day >= 6) {
                    throw new PolicyException(
                        "Weekend communication is restricted."
                    );
                }
            }

            if (!requiresApproval) {
                activity.transition(ActivityStatus.APPROVED);
                activity.transition(ActivityStatus.SCHEDULED);
            }

            activities.put(activity.id(), activity);

            log(
                "ACTIVITY_SCHEDULED",
                activity.id().toString(),
                activity.title()
            );
        }

        void approve(UUID activityId, String approver) {
            CommunicationActivity activity = getActivity(activityId);

            if (!activity.approvalRequired()) {
                throw new PolicyException(
                    "Activity does not require approval."
                );
            }

            activity.approve(approver);

            log(
                "ACTIVITY_APPROVED",
                activityId.toString(),
                approver
            );
        }

        void start(UUID id) {
            CommunicationActivity activity = getActivity(id);
            activity.transition(ActivityStatus.IN_PROGRESS);

            log("ACTIVITY_STARTED", id.toString(), activity.title());
        }

        void markSent(UUID id) {
            CommunicationActivity activity = getActivity(id);
            activity.transition(ActivityStatus.SENT);

            log("ACTIVITY_SENT", id.toString(), activity.title());
        }

        void fail(UUID id) {
            CommunicationActivity activity = getActivity(id);
            activity.transition(ActivityStatus.FAILED);

            log("ACTIVITY_FAILED", id.toString(), activity.title());
        }

        void retry(UUID id) {
            CommunicationActivity activity = getActivity(id);
            activity.transition(ActivityStatus.SCHEDULED);

            log("ACTIVITY_RETRY", id.toString(), activity.title());
        }

        void complete(UUID id) {
            CommunicationActivity activity = getActivity(id);
            activity.transition(ActivityStatus.COMPLETED);

            log("ACTIVITY_COMPLETED", id.toString(), activity.title());
        }

        void cancel(UUID id) {
            CommunicationActivity activity = getActivity(id);
            activity.transition(ActivityStatus.CANCELLED);

            log("ACTIVITY_CANCELLED", id.toString(), activity.title());
        }

        void addFeedback(
            UUID activityId,
            CommunicationFeedback feedback
        ) {
            CommunicationActivity activity = getActivity(activityId);
            activity.addFeedback(feedback);

            log(
                "FEEDBACK_RECORDED",
                activityId.toString(),
                feedback.respondent()
            );
        }

        Map<String, List<String>> stakeholderMatrix() {
            Map<String, List<String>> matrix = new LinkedHashMap<>();

            matrix.put("Manage closely", new ArrayList<>());
            matrix.put("Keep satisfied", new ArrayList<>());
            matrix.put("Keep informed", new ArrayList<>());
            matrix.put("Monitor", new ArrayList<>());

            for (Stakeholder stakeholder : stakeholders.values()) {
                if (stakeholder.influence() >= 4 &&
                    stakeholder.interest() >= 4) {
                    matrix.get("Manage closely").add(stakeholder.name());
                } else if (stakeholder.influence() >= 4) {
                    matrix.get("Keep satisfied").add(stakeholder.name());
                } else if (stakeholder.interest() >= 4) {
                    matrix.get("Keep informed").add(stakeholder.name());
                } else {
                    matrix.get("Monitor").add(stakeholder.name());
                }
            }

            return matrix;
        }

        Channel recommendChannel(String stakeholderName) {
            Stakeholder stakeholder = stakeholders.get(
                stakeholderName.toLowerCase(Locale.ROOT)
            );

            if (stakeholder == null) {
                throw new ValidationException("Stakeholder not found.");
            }

            if (!stakeholder.preferredChannels().isEmpty()) {
                return stakeholder.preferredChannels().get(0);
            }

            return switch (stakeholder.audience()) {
                case MANAGEMENT -> Channel.REPORT;
                case TECHNICAL -> Channel.WORKSHOP;
                case PUBLIC -> Channel.WEBSITE;
                case INTERNAL, EXTERNAL -> Channel.EMAIL;
            };
        }

        Map<Instant, List<String>> detectScheduleConflicts() {
            return activities.values().stream()
                .collect(Collectors.groupingBy(
                    CommunicationActivity::scheduledAt,
                    TreeMap::new,
                    Collectors.mapping(
                        CommunicationActivity::title,
                        Collectors.toList()
                    )
                ))
                .entrySet()
                .stream()
                .filter(entry -> entry.getValue().size() > 1)
                .collect(Collectors.toMap(
                    Map.Entry::getKey,
                    Map.Entry::getValue,
                    (a, b) -> a,
                    TreeMap::new
                ));
        }

        EvaluationReport evaluate() {
            List<CommunicationActivity> all =
                new ArrayList<>(activities.values());

            List<CommunicationActivity> completed = all.stream()
                .filter(a -> a.status() == ActivityStatus.COMPLETED)
                .toList();

            List<CommunicationActivity> failed = all.stream()
                .filter(a -> a.status() == ActivityStatus.FAILED)
                .toList();

            List<CommunicationFeedback> feedback = all.stream()
                .flatMap(a -> a.feedback().stream())
                .toList();

            double satisfaction = feedback.stream()
                .mapToInt(CommunicationFeedback::satisfaction)
                .average()
                .orElse(0);

            double understanding = feedback.stream()
                .mapToInt(CommunicationFeedback::understanding)
                .average()
                .orElse(0);

            double cost = committedCost();

            return new EvaluationReport(
                all.size(),
                completed.size(),
                failed.size(),
                all.isEmpty()
                    ? 0
                    : completed.size() * 100.0 / all.size(),
                cost,
                policy.budget() - cost,
                feedback.size(),
                satisfaction,
                understanding
            );
        }

        List<CommunicationActivity> activities() {
            return List.copyOf(activities.values());
        }

        List<AuditEvent> auditEvents() {
            return List.copyOf(auditEvents);
        }
    }

    private static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(field + " is required.");
        }

        return value.trim();
    }

    public static void main(String[] args) {
        CommunicationPolicy policy = new CommunicationPolicy(
            100000,
            true,
            true,
            false,
            100
        );

        CommunicationService service = new CommunicationService(policy);

        service.addListener(event ->
            System.out.println(
                "AUDIT " + event.event() + " | " + event.details()
            )
        );

        Stakeholder management = new Stakeholder(
            "Executive Management",
            AudienceType.MANAGEMENT,
            "Administration",
            5,
            5,
            List.of(Channel.REPORT, Channel.MEETING)
        );

        Stakeholder technical = new Stakeholder(
            "Technical Team",
            AudienceType.TECHNICAL,
            "Technology",
            3,
            5,
            List.of(Channel.WORKSHOP)
        );

        Stakeholder employees = new Stakeholder(
            "Employees",
            AudienceType.INTERNAL,
            "Operations",
            2,
            4,
            List.of(Channel.EMAIL)
        );

        Stakeholder partners = new Stakeholder(
            "External Partners",
            AudienceType.EXTERNAL,
            "Partnerships",
            4,
            2,
            List.of(Channel.EMAIL)
        );

        service.addStakeholder(management);
        service.addStakeholder(technical);
        service.addStakeholder(employees);
        service.addStakeholder(partners);

        CommunicationObjective objective =
            new CommunicationObjective(
                "Digital Transformation",
                "Coordinate organizational communication.",
                "Improve awareness and stakeholder participation.",
                List.of(
                    management.name(),
                    technical.name(),
                    employees.name(),
                    partners.name()
                ),
                Instant.now().plus(30, ChronoUnit.DAYS),
                Priority.HIGH
            );

        service.addObjective(objective);
        objective.activate();

        CommunicationActivity briefing = new CommunicationActivity(
            objective.id(),
            "Management briefing",
            "Present milestones, responsibilities, and risks.",
            Channel.MEETING,
            List.of(management.name()),
            "Project Director",
            Instant.now().plus(2, ChronoUnit.DAYS),
            15000,
            true
        );

        CommunicationActivity workshop = new CommunicationActivity(
            objective.id(),
            "Technical workshop",
            "Discuss implementation architecture.",
            Channel.WORKSHOP,
            List.of(technical.name()),
            "Technical Lead",
            Instant.now().plus(5, ChronoUnit.DAYS),
            25000,
            false
        );

        CommunicationActivity notification = new CommunicationActivity(
            objective.id(),
            "Partner notification",
            "Communicate relevant operational changes.",
            Channel.EMAIL,
            List.of(partners.name()),
            "Partnership Manager",
            Instant.now().plus(10, ChronoUnit.DAYS),
            2000,
            false
        );

        service.schedule(briefing);
        service.schedule(workshop);
        service.schedule(notification);

        service.approve(
            briefing.id(),
            "Chief Operating Officer"
        );

        service.approve(
            notification.id(),
            "Partnership Director"
        );

        service.start(briefing.id());
        service.markSent(briefing.id());
        service.complete(briefing.id());

        service.start(workshop.id());
        service.markSent(workshop.id());
        service.complete(workshop.id());

        service.start(notification.id());
        service.markSent(notification.id());
        service.complete(notification.id());

        service.addFeedback(
            briefing.id(),
            new CommunicationFeedback(
                "Executive Sponsor",
                5,
                5,
                "Clear and concise briefing.",
                Instant.now()
            )
        );

        service.addFeedback(
            workshop.id(),
            new CommunicationFeedback(
                "Technical Team Lead",
                5,
                4,
                "Technical responsibilities were clear.",
                Instant.now()
            )
        );

        System.out.println("\nSTAKEHOLDER MATRIX");

        service.stakeholderMatrix().forEach(
            (category, names) ->
                System.out.println(category + ": " + names)
        );

        System.out.println("\nCHANNEL RECOMMENDATIONS");

        for (Stakeholder stakeholder :
            List.of(management, technical, employees, partners)) {
            System.out.println(
                stakeholder.name() + " => " +
                service.recommendChannel(stakeholder.name())
            );
        }

        System.out.println("\nEVALUATION");
        System.out.println(service.evaluate());

        System.out.println("\nSCHEDULE CONFLICTS");
        System.out.println(service.detectScheduleConflicts());

        System.out.println("\nPLANNED ACTIVITIES");

        service.activities().forEach(activity ->
            System.out.println(
                activity.title() + " | " +
                activity.channel() + " | " +
                activity.status()
            )
        );
    }
}
