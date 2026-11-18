import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/*
 * Communication Challenges
 *
 * Enterprise communication incident management and governance.
 *
 * Runtime: Java 17
 * Dependencies: Java standard library only.
 */

public class CommunicationManagement {

    enum Category {
        UNCLEAR_MESSAGE,
        INFORMATION_OVERLOAD,
        POOR_LISTENING,
        LANGUAGE_BARRIER,
        CULTURAL_DIFFERENCE,
        WRONG_CHANNEL,
        DELAYED_RESPONSE,
        MISSING_FEEDBACK,
        INCORRECT_ASSUMPTION,
        TECHNICAL_FAILURE,
        INTERPERSONAL_CONFLICT,
        ROLE_AMBIGUITY
    }

    enum Severity {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum Channel {
        EMAIL,
        MEETING,
        CHAT,
        PHONE,
        DOCUMENT,
        VIDEO_CONFERENCE,
        FACE_TO_FACE
    }

    enum Status {
        OPEN,
        INVESTIGATING,
        ACTION_REQUIRED,
        RESOLVED,
        CLOSED
    }

    enum FeedbackDecision {
        PENDING,
        ACCEPTED,
        REJECTED
    }

    enum EventType {
        REPORTED,
        ASSIGNED,
        INVESTIGATED,
        ACTION_PRESCRIBED,
        RESOLVED,
        FEEDBACK_RECEIVED,
        CLOSED,
        STATUS_CHANGED
    }

    record IncidentRequest(
        String title,
        Category category,
        Severity severity,
        Channel channel,
        String department,
        String reporter,
        String description
    ) {}

    record CommunicationEvent(
        Instant timestamp,
        EventType type,
        String description
    ) {}

    record StatusCheck(
        String name,
        boolean passed,
        String details
    ) {
        public StatusCheck {
            name = validate(name, "Check name", 100);
            details = validate(details, "Check details", 500);
        }
    }

    record EligibilityResult(
        boolean eligible,
        List<String> failures
    ) {
        public EligibilityResult {
            failures = List.copyOf(failures);
        }
    }

    record CommunicationPolicy(
        Map<Severity, Integer> responseHours,
        int minimumApprovals,
        boolean requireFeedback,
        boolean requireCorrectiveAction
    ) {
        public CommunicationPolicy {
            responseHours = Collections.unmodifiableMap(
                new EnumMap<>(responseHours)
            );

            if (minimumApprovals < 0) {
                throw new IllegalArgumentException(
                    "Minimum approvals cannot be negative."
                );
            }

            for (Severity severity : Severity.values()) {
                if (
                    !responseHours.containsKey(severity) ||
                    responseHours.get(severity) <= 0
                ) {
                    throw new IllegalArgumentException(
                        "A positive response deadline is required for every severity."
                    );
                }
            }
        }

        public static CommunicationPolicy standard() {
            EnumMap<Severity, Integer> limits =
                new EnumMap<>(Severity.class);

            limits.put(Severity.LOW, 72);
            limits.put(Severity.MEDIUM, 48);
            limits.put(Severity.HIGH, 12);
            limits.put(Severity.CRITICAL, 2);

            return new CommunicationPolicy(
                limits,
                1,
                true,
                true
            );
        }

        public Instant deadline(CommunicationIncident incident) {
            int hours = responseHours.get(incident.severity());

            return incident.createdAt().plus(
                Duration.ofHours(hours)
            );
        }
    }

    static final class CommunicationException
            extends RuntimeException {

        CommunicationException(String message) {
            super(message);
        }
    }

    static final class ValidationException
            extends CommunicationException {

        ValidationException(String message) {
            super(message);
        }
    }

    static final class StateTransitionException
            extends CommunicationException {

        StateTransitionException(String message) {
            super(message);
        }
    }

    private static String validate(
        String value,
        String field,
        int maximum
    ) {
        if (value == null) {
            throw new ValidationException(field + " is required.");
        }

        String normalized = value.strip();

        if (
            normalized.isEmpty() ||
            normalized.length() > maximum
        ) {
            throw new ValidationException(
                field + " must contain 1-" + maximum + " characters."
            );
        }

        if (normalized.chars().anyMatch(
            character ->
                Character.isISOControl(character) &&
                character != '\n' &&
                character != '\t'
        )) {
            throw new ValidationException(
                field + " contains invalid control characters."
            );
        }

        return normalized;
    }

    static final class CommunicationIncident {

        private final long id;
        private final UUID reference;
        private final String title;
        private final Category category;
        private final Severity severity;
        private final Channel channel;
        private final String department;
        private final String reporter;
        private final String description;
        private final Instant createdAt;

        private final List<CommunicationEvent> events =
            new ArrayList<>();

        private final List<StatusCheck> checks =
            new ArrayList<>();

        private Status status = Status.OPEN;
        private String assignee;
        private String correctiveAction;
        private String resolution;

        private Instant resolvedAt;
        private FeedbackDecision feedback =
            FeedbackDecision.PENDING;

        CommunicationIncident(
            long id,
            IncidentRequest request
        ) {
            this.id = id;
            this.reference = UUID.randomUUID();

            this.title = validate(
                request.title(),
                "Title",
                120
            );

            this.category = Objects.requireNonNull(
                request.category(),
                "Category is required."
            );

            this.severity = Objects.requireNonNull(
                request.severity(),
                "Severity is required."
            );

            this.channel = Objects.requireNonNull(
                request.channel(),
                "Channel is required."
            );

            this.department = validate(
                request.department(),
                "Department",
                100
            );

            this.reporter = validate(
                request.reporter(),
                "Reporter",
                100
            );

            this.description = validate(
                request.description(),
                "Description",
                1000
            );

            this.createdAt = Instant.now();

            record(
                EventType.REPORTED,
                "Communication issue registered."
            );
        }

        void record(EventType type, String description) {
            events.add(new CommunicationEvent(
                Instant.now(),
                type,
                description
            ));
        }

        long id() {
            return id;
        }

        UUID reference() {
            return reference;
        }

        String title() {
            return title;
        }

        Category category() {
            return category;
        }

        Severity severity() {
            return severity;
        }

        Channel channel() {
            return channel;
        }

        String department() {
            return department;
        }

        String reporter() {
            return reporter;
        }

        Instant createdAt() {
            return createdAt;
        }

        Status status() {
            return status;
        }

        Optional<String> assignee() {
            return Optional.ofNullable(assignee);
        }

        Optional<String> correctiveAction() {
            return Optional.ofNullable(correctiveAction);
        }

        Optional<String> resolution() {
            return Optional.ofNullable(resolution);
        }

        Optional<Instant> resolvedAt() {
            return Optional.ofNullable(resolvedAt);
        }

        FeedbackDecision feedback() {
            return feedback;
        }

        List<CommunicationEvent> events() {
            return List.copyOf(events);
        }

        List<StatusCheck> checks() {
            return List.copyOf(checks);
        }
    }

    static final class RecommendationService {

        private static final Map<Category, String> ACTIONS =
            Map.ofEntries(
                Map.entry(
                    Category.UNCLEAR_MESSAGE,
                    "Use clear instructions and explicit deadlines."
                ),
                Map.entry(
                    Category.INFORMATION_OVERLOAD,
                    "Prioritize information and divide content into sections."
                ),
                Map.entry(
                    Category.POOR_LISTENING,
                    "Use active listening and paraphrasing."
                ),
                Map.entry(
                    Category.LANGUAGE_BARRIER,
                    "Use plain language and verified translations."
                ),
                Map.entry(
                    Category.CULTURAL_DIFFERENCE,
                    "Establish inclusive communication practices."
                ),
                Map.entry(
                    Category.WRONG_CHANNEL,
                    "Choose a channel based on urgency and confidentiality."
                ),
                Map.entry(
                    Category.DELAYED_RESPONSE,
                    "Establish response deadlines and escalation."
                ),
                Map.entry(
                    Category.MISSING_FEEDBACK,
                    "Introduce structured feedback cycles."
                ),
                Map.entry(
                    Category.INCORRECT_ASSUMPTION,
                    "Verify facts and confirm understanding."
                ),
                Map.entry(
                    Category.TECHNICAL_FAILURE,
                    "Establish technical recovery and alternative channels."
                ),
                Map.entry(
                    Category.INTERPERSONAL_CONFLICT,
                    "Use impartial mediation and structured discussions."
                ),
                Map.entry(
                    Category.ROLE_AMBIGUITY,
                    "Define responsibilities and reporting lines."
                )
            );

        String recommend(Category category) {
            String action = ACTIONS.get(category);

            if (action == null) {
                throw new ValidationException(
                    "No recommendation exists for this category."
                );
            }

            return action;
        }
    }

    static final class CommunicationRepository {

        private final Map<Long, CommunicationIncident> storage =
            new HashMap<>();

        private final AtomicLong sequence = new AtomicLong(1);

        CommunicationIncident save(IncidentRequest request) {
            long id = sequence.getAndIncrement();

            CommunicationIncident incident =
                new CommunicationIncident(id, request);

            storage.put(id, incident);

            return incident;
        }

        CommunicationIncident findById(long id) {
            CommunicationIncident incident = storage.get(id);

            if (incident == null) {
                throw new CommunicationException(
                    "Communication incident not found: " + id
                );
            }

            return incident;
        }

        List<CommunicationIncident> findAll() {
            return List.copyOf(storage.values());
        }
    }

    static final class CommunicationService {

        private static final Map<Status, Set<Status>> TRANSITIONS =
            Map.of(
                Status.OPEN,
                Set.of(Status.INVESTIGATING, Status.CLOSED),

                Status.INVESTIGATING,
                Set.of(
                    Status.ACTION_REQUIRED,
                    Status.RESOLVED,
                    Status.CLOSED
                ),

                Status.ACTION_REQUIRED,
                Set.of(Status.INVESTIGATING, Status.RESOLVED),

                Status.RESOLVED,
                Set.of(Status.CLOSED, Status.INVESTIGATING),

                Status.CLOSED,
                Set.of()
            );

        private final CommunicationRepository repository;
        private final CommunicationPolicy policy;
        private final RecommendationService recommendations;

        CommunicationService(
            CommunicationRepository repository,
            CommunicationPolicy policy,
            RecommendationService recommendations
        ) {
            this.repository = repository;
            this.policy = policy;
            this.recommendations = recommendations;
        }

        CommunicationIncident report(IncidentRequest request) {
            return repository.save(request);
        }

        CommunicationIncident get(long id) {
            return repository.findById(id);
        }

        void assign(long id, String employee) {
            CommunicationIncident incident = get(id);

            if (incident.status == Status.CLOSED) {
                throw new StateTransitionException(
                    "Cannot assign a closed incident."
                );
            }

            incident.assignee = validate(
                employee,
                "Assignee",
                100
            );

            incident.record(
                EventType.ASSIGNED,
                "Assigned to " + incident.assignee
            );
        }

        void transition(long id, Status next) {
            CommunicationIncident incident = get(id);

            if (!TRANSITIONS.get(incident.status).contains(next)) {
                throw new StateTransitionException(
                    "Invalid transition: " +
                    incident.status + " -> " + next
                );
            }

            if (
                next == Status.RESOLVED &&
                (
                    incident.correctiveAction == null ||
                    incident.resolution == null
                )
            ) {
                throw new StateTransitionException(
                    "Corrective action and resolution are required."
                );
            }

            incident.status = next;

            if (next == Status.RESOLVED) {
                incident.resolvedAt = Instant.now();
                incident.record(
                    EventType.RESOLVED,
                    incident.resolution
                );
            } else {
                incident.record(
                    EventType.STATUS_CHANGED,
                    "Status changed to " + next
                );
            }
        }

        String prescribeAction(long id, String customAction) {
            CommunicationIncident incident = get(id);

            if (incident.status == Status.CLOSED) {
                throw new StateTransitionException(
                    "Closed incidents cannot be modified."
                );
            }

            String action = customAction == null
                ? recommendations.recommend(incident.category)
                : validate(customAction, "Corrective action", 1000);

            incident.correctiveAction = action;

            incident.record(
                EventType.ACTION_PRESCRIBED,
                action
            );

            if (
                incident.status == Status.OPEN ||
                incident.status == Status.INVESTIGATING
            ) {
                transition(id, Status.ACTION_REQUIRED);
            }

            return action;
        }

        void resolve(long id, String resolution) {
            CommunicationIncident incident = get(id);

            if (
                incident.status != Status.INVESTIGATING &&
                incident.status != Status.ACTION_REQUIRED
            ) {
                throw new StateTransitionException(
                    "Incident is not under investigation."
                );
            }

            incident.resolution = validate(
                resolution,
                "Resolution",
                1000
            );

            transition(id, Status.RESOLVED);
        }

        void receiveFeedback(
            long id,
            FeedbackDecision decision
        ) {
            CommunicationIncident incident = get(id);

            if (incident.status != Status.RESOLVED) {
                throw new StateTransitionException(
                    "Feedback requires a resolved incident."
                );
            }

            if (decision == FeedbackDecision.PENDING) {
                throw new ValidationException(
                    "Feedback must be accepted or rejected."
                );
            }

            incident.feedback = decision;

            incident.record(
                EventType.FEEDBACK_RECEIVED,
                decision.toString()
            );

            if (decision == FeedbackDecision.REJECTED) {
                transition(id, Status.INVESTIGATING);
            }
        }

        void addStatusCheck(long id, StatusCheck check) {
            CommunicationIncident incident = get(id);

            if (incident.status == Status.CLOSED) {
                throw new StateTransitionException(
                    "Closed incidents cannot receive new checks."
                );
            }

            incident.checks.add(check);
        }

        EligibilityResult evaluateClosure(long id) {
            CommunicationIncident incident = get(id);

            List<String> failures = new ArrayList<>();

            if (incident.status != Status.RESOLVED) {
                failures.add("Incident is not resolved.");
            }

            if (
                policy.requireCorrectiveAction() &&
                incident.correctiveAction == null
            ) {
                failures.add("Corrective action is missing.");
            }

            if (
                policy.requireFeedback() &&
                incident.feedback != FeedbackDecision.ACCEPTED
            ) {
                failures.add("Accepted feedback is missing.");
            }

            incident.checks.stream()
                .filter(check -> !check.passed())
                .forEach(check ->
                    failures.add(
                        "Failed status check: " + check.name()
                    )
                );

            return new EligibilityResult(
                failures.isEmpty(),
                failures
            );
        }

        void close(long id) {
            EligibilityResult result = evaluateClosure(id);

            if (!result.eligible()) {
                throw new StateTransitionException(
                    String.join("; ", result.failures())
                );
            }

            transition(id, Status.CLOSED);

            get(id).record(
                EventType.CLOSED,
                "Incident successfully closed."
            );
        }

        List<CommunicationIncident> search(
            Optional<Category> category,
            Optional<Status> status,
            Optional<String> department
        ) {
            return repository.findAll().stream()
                .filter(item ->
                    category.isEmpty() ||
                    item.category == category.get()
                )
                .filter(item ->
                    status.isEmpty() ||
                    item.status == status.get()
                )
                .filter(item ->
                    department.isEmpty() ||
                    item.department.equalsIgnoreCase(department.get())
                )
                .collect(Collectors.toUnmodifiableList());
        }

        List<CommunicationIncident> overdue(Instant now) {
            return repository.findAll().stream()
                .filter(item ->
                    item.status != Status.RESOLVED &&
                    item.status != Status.CLOSED
                )
                .filter(item ->
                    now.isAfter(policy.deadline(item))
                )
                .toList();
        }

        Map<String, Object> analytics() {
            List<CommunicationIncident> incidents =
                repository.findAll();

            Map<Category, Long> categories = incidents.stream()
                .collect(Collectors.groupingBy(
                    item -> item.category,
                    () -> new EnumMap<>(Category.class),
                    Collectors.counting()
                ));

            Map<Status, Long> statuses = incidents.stream()
                .collect(Collectors.groupingBy(
                    item -> item.status,
                    () -> new EnumMap<>(Status.class),
                    Collectors.counting()
                ));

            List<Duration> durations = incidents.stream()
                .filter(item -> item.resolvedAt != null)
                .map(item -> Duration.between(
                    item.createdAt,
                    item.resolvedAt
                ))
                .toList();

            double resolutionRate = incidents.isEmpty()
                ? 0
                : 100.0 * incidents.stream()
                    .filter(item ->
                        item.status == Status.RESOLVED ||
                        item.status == Status.CLOSED
                    )
                    .count() / incidents.size();

            double averageHours = durations.isEmpty()
                ? 0
                : durations.stream()
                    .mapToDouble(Duration::toMillis)
                    .average()
                    .orElse(0) / 3_600_000.0;

            Map<String, Object> result = new HashMap<>();

            result.put("totalIncidents", incidents.size());
            result.put("categoryDistribution", categories);
            result.put("statusDistribution", statuses);
            result.put("resolutionRatePercent", resolutionRate);
            result.put("averageResolutionHours", averageHours);
            result.put("overdueIncidents", overdue(Instant.now()).size());

            return Map.copyOf(result);
        }
    }

    public static void main(String[] args) {

        CommunicationRepository repository =
            new CommunicationRepository();

        CommunicationPolicy policy =
            CommunicationPolicy.standard();

        RecommendationService recommendations =
            new RecommendationService();

        CommunicationService service =
            new CommunicationService(
                repository,
                policy,
                recommendations
            );

        IncidentRequest firstRequest = new IncidentRequest(
            "Unclear project instructions",
            Category.UNCLEAR_MESSAGE,
            Severity.HIGH,
            Channel.EMAIL,
            "Engineering",
            "Project Manager",
            "Different teams interpreted the project deadline differently."
        );

        CommunicationIncident first = service.report(firstRequest);

        service.assign(first.id(), "Engineering Coordinator");

        service.transition(
            first.id(),
            Status.INVESTIGATING
        );

        service.prescribeAction(first.id(), null);

        service.resolve(
            first.id(),
            "A revised document clarified tasks, owners and deadlines."
        );

        service.receiveFeedback(
            first.id(),
            FeedbackDecision.ACCEPTED
        );

        service.addStatusCheck(
            first.id(),
            new StatusCheck(
                "Resolution documented",
                true,
                "Revised instructions were distributed."
            )
        );

        EligibilityResult eligibility =
            service.evaluateClosure(first.id());

        System.out.println("CLOSURE ELIGIBILITY");
        System.out.println(eligibility);

        service.close(first.id());

        IncidentRequest secondRequest = new IncidentRequest(
            "Delayed response",
            Category.DELAYED_RESPONSE,
            Severity.MEDIUM,
            Channel.EMAIL,
            "Customer Support",
            "Support Manager",
            "A customer request was not answered within the expected time."
        );

        CommunicationIncident second =
            service.report(secondRequest);

        service.assign(second.id(), "Support Team Lead");

        service.transition(
            second.id(),
            Status.INVESTIGATING
        );

        service.prescribeAction(second.id(), null);

        IncidentRequest thirdRequest = new IncidentRequest(
            "Information overload",
            Category.INFORMATION_OVERLOAD,
            Severity.LOW,
            Channel.MEETING,
            "Operations",
            "Operations Manager",
            "Participants received excessive unstructured meeting information."
        );

        service.report(thirdRequest);

        System.out.println("\nCOMMUNICATION ANALYTICS");

        service.analytics().forEach(
            (key, value) ->
                System.out.println(key + ": " + value)
        );

        System.out.println("\nOPEN INVESTIGATIONS");

        service.search(
            Optional.empty(),
            Optional.of(Status.ACTION_REQUIRED),
            Optional.empty()
        ).forEach(item ->
            System.out.println(
                item.id() + " | " + item.title()
            )
        );

        System.out.println("\nOVERDUE INCIDENTS");

        service.overdue(Instant.now()).forEach(item ->
            System.out.println(item.title())
        );

        System.out.println("\nVALIDATION TEST");

        try {
            service.transition(
                first.id(),
                Status.INVESTIGATING
            );

            throw new IllegalStateException(
                "Invalid transition was not rejected."
            );

        } catch (StateTransitionException expected) {
            System.out.println(
                "Invalid transition correctly rejected."
            );
        }

        System.out.println("\nCOMMUNICATION RECOMMENDATION");

        System.out.println(
            recommendations.recommend(
                Category.LANGUAGE_BARRIER
            )
        );
    }
}
