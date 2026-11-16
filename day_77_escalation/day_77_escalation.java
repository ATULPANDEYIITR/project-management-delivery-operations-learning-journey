import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * Enterprise Escalation and Critical Problem Reporting System
 *
 * Java 17
 * No external dependencies.
 *
 * Demonstrates:
 * - Domain-driven incident modeling
 * - Role-based authorization
 * - Policy-based escalation
 * - State transitions
 * - Immutable event records
 * - Deadline management
 * - Resolution verification
 * - Auditability
 * - Enterprise reporting
 */

public class EscalationManagement {

    enum Severity {
        LOW, MEDIUM, HIGH, CRITICAL
    }

    enum IncidentStatus {
        REPORTED,
        ACKNOWLEDGED,
        INVESTIGATING,
        ESCALATED,
        RESOLVED,
        CLOSED
    }

    enum EscalationLevel {
        LEVEL_1(1),
        LEVEL_2(2),
        LEVEL_3(3),
        EXECUTIVE(4);

        private final int value;

        EscalationLevel(int value) {
            this.value = value;
        }

        public int value() {
            return value;
        }

        public static EscalationLevel fromValue(int value) {
            for (EscalationLevel level : values()) {
                if (level.value == value) {
                    return level;
                }
            }

            throw new IllegalArgumentException(
                "Invalid escalation level."
            );
        }
    }

    enum ActorRole {
        REPORTER,
        RESPONDER,
        TEAM_LEAD,
        INCIDENT_MANAGER,
        ADMINISTRATOR
    }

    enum EventType {
        REPORTED,
        ASSIGNED,
        ACKNOWLEDGED,
        INVESTIGATION_STARTED,
        ESCALATED,
        RESOLVED,
        CLOSED,
        REOPENED,
        DEADLINE_BREACHED
    }

    record Actor(
        String id,
        String name,
        ActorRole role,
        String department
    ) {
        Actor {
            id = requireText(id, "Actor ID", 80);
            name = requireText(name, "Actor name", 120);
            Objects.requireNonNull(role, "Role is required.");
            department = requireText(
                department, "Department", 100
            );
        }
    }

    record EscalationPolicy(
        Duration acknowledgementTime,
        Duration resolutionTime,
        EscalationLevel initialLevel
    ) {
        EscalationPolicy {
            Objects.requireNonNull(acknowledgementTime);
            Objects.requireNonNull(resolutionTime);
            Objects.requireNonNull(initialLevel);

            if (
                acknowledgementTime.isNegative() ||
                acknowledgementTime.isZero() ||
                resolutionTime.compareTo(acknowledgementTime) <= 0
            ) {
                throw new IllegalArgumentException(
                    "Invalid escalation deadlines."
                );
            }
        }
    }

    record AuditEvent(
        UUID eventId,
        String incidentId,
        String actorId,
        EventType type,
        String details,
        Instant timestamp
    ) {}

    record Notification(
        UUID id,
        String incidentId,
        String recipient,
        String event,
        Instant createdAt
    ) {}

    record DeadlineBreach(
        String incidentId,
        String breachType,
        Severity severity,
        Instant detectedAt
    ) {}

    record MergeEvaluation(
        boolean eligible,
        List<String> blockers
    ) {
        MergeEvaluation {
            blockers = List.copyOf(blockers);
        }
    }

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static class AuthorizationException extends DomainException {
        AuthorizationException(String message) {
            super(message);
        }
    }

    static class TransitionException extends DomainException {
        TransitionException(String message) {
            super(message);
        }
    }

    static String requireText(
        String value,
        String field,
        int maximum
    ) {
        if (value == null) {
            throw new IllegalArgumentException(
                field + " is required."
            );
        }

        String normalized = value.trim();

        if (
            normalized.isEmpty() ||
            normalized.length() > maximum
        ) {
            throw new IllegalArgumentException(
                field + " must contain 1 to " + maximum + " characters."
            );
        }

        return normalized;
    }

    static final Map<Severity, EscalationPolicy> POLICIES;

    static {
        EnumMap<Severity, EscalationPolicy> policies =
            new EnumMap<>(Severity.class);

        policies.put(
            Severity.LOW,
            new EscalationPolicy(
                Duration.ofMinutes(480),
                Duration.ofMinutes(2880),
                EscalationLevel.LEVEL_1
            )
        );

        policies.put(
            Severity.MEDIUM,
            new EscalationPolicy(
                Duration.ofMinutes(120),
                Duration.ofMinutes(1440),
                EscalationLevel.LEVEL_1
            )
        );

        policies.put(
            Severity.HIGH,
            new EscalationPolicy(
                Duration.ofMinutes(30),
                Duration.ofMinutes(240),
                EscalationLevel.LEVEL_2
            )
        );

        policies.put(
            Severity.CRITICAL,
            new EscalationPolicy(
                Duration.ofMinutes(10),
                Duration.ofMinutes(60),
                EscalationLevel.EXECUTIVE
            )
        );

        POLICIES = Map.copyOf(policies);
    }

    static class Incident {

        private final String id;
        private final String title;
        private final String description;
        private final String category;
        private final String department;
        private final String reporterId;
        private final Instant reportedAt;
        private final Instant acknowledgementDeadline;
        private final Instant resolutionDeadline;
        private final String parentIncidentId;

        private final Set<String> tags = new HashSet<>();
        private final List<AuditEvent> audit = new ArrayList<>();
        private final List<StatusCheck> statusChecks =
            new ArrayList<>();

        private Severity severity;
        private IncidentStatus status;
        private EscalationLevel escalationLevel;

        private String assignedTo;
        private Instant acknowledgedAt;
        private Instant resolvedAt;
        private String resolutionNotes;

        private long version = 1;

        Incident(
            String title,
            String description,
            String category,
            String department,
            String reporterId,
            Severity severity,
            String parentIncidentId,
            Set<String> tags
        ) {
            this.id = UUID.randomUUID().toString();
            this.title = requireText(title, "Title", 160);
            this.description = requireText(
                description, "Description", 5000
            );
            this.category = requireText(category, "Category", 80);
            this.department = requireText(
                department, "Department", 100
            );
            this.reporterId = reporterId;
            this.severity = Objects.requireNonNull(severity);
            this.parentIncidentId = parentIncidentId;

            EscalationPolicy policy = POLICIES.get(severity);

            this.reportedAt = Instant.now();
            this.acknowledgementDeadline =
                reportedAt.plus(policy.acknowledgementTime());

            this.resolutionDeadline =
                reportedAt.plus(policy.resolutionTime());

            this.escalationLevel = policy.initialLevel();
            this.status = IncidentStatus.REPORTED;

            if (tags != null) {
                for (String tag : tags) {
                    this.tags.add(requireText(tag, "Tag", 60));
                }
            }
        }

        String id() {
            return id;
        }

        Severity severity() {
            return severity;
        }

        IncidentStatus status() {
            return status;
        }

        long version() {
            return version;
        }

        List<AuditEvent> audit() {
            return List.copyOf(audit);
        }

        List<StatusCheck> statusChecks() {
            return List.copyOf(statusChecks);
        }

        IncidentView view() {
            return new IncidentView(
                id,
                title,
                description,
                category,
                department,
                severity,
                status,
                escalationLevel,
                reporterId,
                assignedTo,
                reportedAt,
                acknowledgementDeadline,
                resolutionDeadline,
                resolvedAt,
                version,
                Set.copyOf(tags)
            );
        }
    }

    record IncidentView(
        String id,
        String title,
        String description,
        String category,
        String department,
        Severity severity,
        IncidentStatus status,
        EscalationLevel escalationLevel,
        String reporterId,
        String assignedTo,
        Instant reportedAt,
        Instant acknowledgementDeadline,
        Instant resolutionDeadline,
        Instant resolvedAt,
        long version,
        Set<String> tags
    ) {
        IncidentView {
            tags = Set.copyOf(tags);
        }
    }

    record StatusCheck(
        String name,
        boolean required,
        boolean completed,
        boolean passed
    ) {
        StatusCheck {
            name = requireText(name, "Check name", 100);
        }
    }

    interface NotificationGateway {
        void deliver(Notification notification);
    }

    static class InMemoryNotificationGateway
        implements NotificationGateway {

        private final List<Notification> delivered =
            new CopyOnWriteArrayList<>();

        @Override
        public void deliver(Notification notification) {
            delivered.add(notification);

            System.out.printf(
                "[NOTIFICATION] %s -> %s%n",
                notification.event(),
                notification.recipient()
            );
        }

        List<Notification> history() {
            return List.copyOf(delivered);
        }
    }

    static class AuthorizationService {

        boolean canManage(Actor actor, Severity severity) {
            return switch (actor.role()) {
                case ADMINISTRATOR, INCIDENT_MANAGER -> true;
                case TEAM_LEAD -> severity != Severity.CRITICAL;
                case RESPONDER -> true;
                case REPORTER -> false;
            };
        }

        void requirePermission(Actor actor, Severity severity) {
            if (!canManage(actor, severity)) {
                throw new AuthorizationException(
                    "Actor cannot manage this incident."
                );
            }
        }
    }

    static class EscalationService {

        private static final Map<
            IncidentStatus,
            Set<IncidentStatus>
        > TRANSITIONS = createTransitions();

        private static Map<
            IncidentStatus,
            Set<IncidentStatus>
        > createTransitions() {
            EnumMap<
                IncidentStatus,
                Set<IncidentStatus>
            > map = new EnumMap<>(IncidentStatus.class);

            map.put(
                IncidentStatus.REPORTED,
                Set.of(
                    IncidentStatus.ACKNOWLEDGED,
                    IncidentStatus.ESCALATED
                )
            );

            map.put(
                IncidentStatus.ACKNOWLEDGED,
                Set.of(
                    IncidentStatus.INVESTIGATING,
                    IncidentStatus.ESCALATED
                )
            );

            map.put(
                IncidentStatus.INVESTIGATING,
                Set.of(
                    IncidentStatus.ESCALATED,
                    IncidentStatus.RESOLVED
                )
            );

            map.put(
                IncidentStatus.ESCALATED,
                Set.of(
                    IncidentStatus.ACKNOWLEDGED,
                    IncidentStatus.INVESTIGATING,
                    IncidentStatus.RESOLVED
                )
            );

            map.put(
                IncidentStatus.RESOLVED,
                Set.of(
                    IncidentStatus.CLOSED,
                    IncidentStatus.INVESTIGATING
                )
            );

            map.put(IncidentStatus.CLOSED, Set.of());

            return Map.copyOf(map);
        }

        private final Map<String, Actor> actors =
            new ConcurrentHashMap<>();

        private final Map<String, Incident> incidents =
            new ConcurrentHashMap<>();

        private final List<AuditEvent> auditEvents =
            new CopyOnWriteArrayList<>();

        private final List<DeadlineBreach> breaches =
            new CopyOnWriteArrayList<>();

        private final NotificationGateway notificationGateway;
        private final AuthorizationService authorization =
            new AuthorizationService();

        EscalationService(NotificationGateway gateway) {
            this.notificationGateway =
                Objects.requireNonNull(gateway);
        }

        void registerActor(Actor actor) {
            if (actors.putIfAbsent(actor.id(), actor) != null) {
                throw new DomainException("Actor already exists.");
            }
        }

        Actor actor(String actorId) {
            Actor actor = actors.get(actorId);

            if (actor == null) {
                throw new DomainException("Actor not found.");
            }

            return actor;
        }

        Incident incident(String id) {
            Incident incident = incidents.get(id);

            if (incident == null) {
                throw new DomainException("Incident not found.");
            }

            return incident;
        }

        private void audit(
            Incident incident,
            String actorId,
            EventType type,
            String details
        ) {
            AuditEvent event = new AuditEvent(
                UUID.randomUUID(),
                incident.id,
                actorId,
                type,
                details,
                Instant.now()
            );

            incident.audit.add(event);
            auditEvents.add(event);
            incident.version++;
        }

        private void notify(
            Incident incident,
            String recipient,
            String event
        ) {
            notificationGateway.deliver(
                new Notification(
                    UUID.randomUUID(),
                    incident.id,
                    recipient,
                    event,
                    Instant.now()
                )
            );
        }

        private void transition(
            Incident incident,
            String actorId,
            IncidentStatus next,
            EventType eventType,
            String details
        ) {
            Set<IncidentStatus> allowed =
                TRANSITIONS.get(incident.status);

            if (!allowed.contains(next)) {
                throw new TransitionException(
                    "Invalid transition from " +
                    incident.status + " to " + next
                );
            }

            IncidentStatus previous = incident.status;
            incident.status = next;

            audit(
                incident,
                actorId,
                eventType,
                previous + " -> " + next + ": " + details
            );
        }

        IncidentView report(
            String reporterId,
            String title,
            String description,
            String category,
            String department,
            Severity severity,
            Set<String> tags,
            String parentIncidentId
        ) {
            actor(reporterId);

            if (parentIncidentId != null) {
                incident(parentIncidentId);
            }

            Incident created = new Incident(
                title,
                description,
                category,
                department,
                reporterId,
                severity,
                parentIncidentId,
                tags
            );

            created.audit.add(
                new AuditEvent(
                    UUID.randomUUID(),
                    created.id,
                    reporterId,
                    EventType.REPORTED,
                    "Incident submitted",
                    Instant.now()
                )
            );

            if (
                incidents.putIfAbsent(created.id, created) != null
            ) {
                throw new DomainException(
                    "Incident identifier collision."
                );
            }

            auditEvents.addAll(created.audit);

            notify(
                created,
                "incident_management",
                "INCIDENT_REPORTED"
            );

            if (severity == Severity.CRITICAL) {
                notify(
                    created,
                    "executive_team",
                    "CRITICAL_ALERT"
                );
            }

            return created.view();
        }

        void assign(
            String incidentId,
            String actorId,
            String assigneeId
        ) {
            Incident incident = incident(incidentId);
            Actor actor = actor(actorId);
            actor(assigneeId);

            authorization.requirePermission(
                actor, incident.severity
            );

            incident.assignedTo = assigneeId;

            audit(
                incident,
                actorId,
                EventType.ASSIGNED,
                "Assigned to " + assigneeId
            );

            notify(
                incident,
                assigneeId,
                "INCIDENT_ASSIGNED"
            );
        }

        void acknowledge(
            String incidentId,
            String actorId
        ) {
            Incident incident = incident(incidentId);
            Actor actor = actor(actorId);

            authorization.requirePermission(
                actor, incident.severity
            );

            transition(
                incident,
                actorId,
                IncidentStatus.ACKNOWLEDGED,
                EventType.ACKNOWLEDGED,
                "Incident acknowledged"
            );

            incident.acknowledgedAt = Instant.now();

            notify(
                incident,
                incident.reporterId,
                "INCIDENT_ACKNOWLEDGED"
            );
        }

        void investigate(
            String incidentId,
            String actorId
        ) {
            Incident incident = incident(incidentId);
            Actor actor = actor(actorId);

            authorization.requirePermission(
                actor, incident.severity
            );

            if (incident.assignedTo == null) {
                throw new DomainException(
                    "Incident owner must be assigned first."
                );
            }

            transition(
                incident,
                actorId,
                IncidentStatus.INVESTIGATING,
                EventType.INVESTIGATION_STARTED,
                "Investigation started"
            );
        }

        void escalate(
            String incidentId,
            String actorId,
            String reason,
            EscalationLevel target
        ) {
            Incident incident = incident(incidentId);
            Actor actor = actor(actorId);

            authorization.requirePermission(
                actor, incident.severity
            );

            reason = requireText(
                reason, "Escalation reason", 1000
            );

            if (
                incident.status == IncidentStatus.RESOLVED ||
                incident.status == IncidentStatus.CLOSED
            ) {
                throw new TransitionException(
                    "Completed incidents cannot be escalated."
                );
            }

            if (
                target.value() <= incident.escalationLevel.value()
            ) {
                throw new DomainException(
                    "Escalation level must increase."
                );
            }

            incident.escalationLevel = target;

            if (incident.status != IncidentStatus.ESCALATED) {
                transition(
                    incident,
                    actorId,
                    IncidentStatus.ESCALATED,
                    EventType.ESCALATED,
                    reason
                );
            } else {
                audit(
                    incident,
                    actorId,
                    EventType.ESCALATED,
                    reason
                );
            }

            String recipient =
                target == EscalationLevel.EXECUTIVE
                ? "executive_team"
                : "management_level_" + target.value();

            notify(
                incident,
                recipient,
                "INCIDENT_ESCALATED"
            );
        }

        void recordStatusCheck(
            String incidentId,
            String actorId,
            StatusCheck check
        ) {
            Incident incident = incident(incidentId);
            Actor actor = actor(actorId);

            authorization.requirePermission(
                actor, incident.severity
            );

            incident.statusChecks.add(check);

            audit(
                incident,
                actorId,
                EventType.INVESTIGATION_STARTED,
                "Check recorded: " + check.name()
            );
        }

        void resolve(
            String incidentId,
            String actorId,
            String resolutionNotes
        ) {
            Incident incident = incident(incidentId);
            Actor actor = actor(actorId);

            authorization.requirePermission(
                actor, incident.severity
            );

            resolutionNotes = requireText(
                resolutionNotes, "Resolution notes", 3000
            );

            transition(
                incident,
                actorId,
                IncidentStatus.RESOLVED,
                EventType.RESOLVED,
                resolutionNotes
            );

            incident.resolvedAt = Instant.now();
            incident.resolutionNotes = resolutionNotes;

            notify(
                incident,
                incident.reporterId,
                "INCIDENT_RESOLVED"
            );
        }

        void close(
            String incidentId,
            String actorId
        ) {
            Incident incident = incident(incidentId);
            Actor actor = actor(actorId);

            authorization.requirePermission(
                actor, incident.severity
            );

            if (
                incident.resolvedAt == null ||
                incident.resolutionNotes == null
            ) {
                throw new DomainException(
                    "Resolution evidence is mandatory."
                );
            }

            transition(
                incident,
                actorId,
                IncidentStatus.CLOSED,
                EventType.CLOSED,
                "Administrative closure"
            );
        }

        void reopen(
            String incidentId,
            String actorId,
            String reason
        ) {
            Incident incident = incident(incidentId);
            Actor actor = actor(actorId);

            authorization.requirePermission(
                actor, incident.severity
            );

            reason = requireText(
                reason, "Reopening reason", 1000
            );

            transition(
                incident,
                actorId,
                IncidentStatus.INVESTIGATING,
                EventType.REOPENED,
                reason
            );

            incident.resolvedAt = null;
            incident.resolutionNotes = null;
        }

        List<DeadlineBreach> evaluateDeadlines(Instant now) {
            List<DeadlineBreach> results = new ArrayList<>();

            for (Incident incident : incidents.values()) {
                if (
                    incident.status == IncidentStatus.RESOLVED ||
                    incident.status == IncidentStatus.CLOSED
                ) {
                    continue;
                }

                if (
                    incident.acknowledgedAt == null &&
                    now.isAfter(incident.acknowledgementDeadline)
                ) {
                    results.add(new DeadlineBreach(
                        incident.id,
                        "ACKNOWLEDGEMENT",
                        incident.severity,
                        now
                    ));
                } else if (now.isAfter(incident.resolutionDeadline)) {
                    results.add(new DeadlineBreach(
                        incident.id,
                        "RESOLUTION",
                        incident.severity,
                        now
                    ));
                }
            }

            breaches.addAll(results);
            return List.copyOf(results);
        }

        MergeEvaluation evaluateMergeEligibility(
            String incidentId,
            int requiredApprovals
        ) {
            Incident incident = incident(incidentId);
            List<String> blockers = new ArrayList<>();

            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Required approvals cannot be negative."
                );
            }

            if (incident.status != IncidentStatus.RESOLVED) {
                blockers.add("Incident is not resolved.");
            }

            if (incident.assignedTo == null) {
                blockers.add("Incident owner is missing.");
            }

            if (incident.resolutionNotes == null) {
                blockers.add("Resolution evidence is missing.");
            }

            for (StatusCheck check : incident.statusChecks) {
                if (
                    check.required() &&
                    (!check.completed() || !check.passed())
                ) {
                    blockers.add(
                        "Required check failed: " + check.name()
                    );
                }
            }

            return new MergeEvaluation(
                blockers.isEmpty(),
                blockers
            );
        }

        List<IncidentView> search(
            Predicate<IncidentView> filter
        ) {
            return incidents.values()
                .stream()
                .map(Incident::view)
                .filter(filter)
                .sorted((a, b) ->
                    b.reportedAt().compareTo(a.reportedAt())
                )
                .toList();
        }

        Map<String, Long> dashboard() {
            Map<String, Long> result = new HashMap<>();

            result.put("total", (long) incidents.size());

            result.put(
                "open",
                incidents.values().stream()
                    .filter(i ->
                        i.status != IncidentStatus.RESOLVED &&
                        i.status != IncidentStatus.CLOSED
                    )
                    .count()
            );

            result.put(
                "critical",
                incidents.values().stream()
                    .filter(i -> i.severity == Severity.CRITICAL)
                    .count()
            );

            result.put(
                "escalated",
                incidents.values().stream()
                    .filter(i -> i.status == IncidentStatus.ESCALATED)
                    .count()
            );

            result.put(
                "resolved",
                incidents.values().stream()
                    .filter(i ->
                        i.status == IncidentStatus.RESOLVED ||
                        i.status == IncidentStatus.CLOSED
                    )
                    .count()
            );

            return Map.copyOf(result);
        }

        List<AuditEvent> auditHistory() {
            return List.copyOf(auditEvents);
        }

        List<DeadlineBreach> breachHistory() {
            return List.copyOf(breaches);
        }
    }

    public static void main(String[] args) {

        InMemoryNotificationGateway gateway =
            new InMemoryNotificationGateway();

        EscalationService service =
            new EscalationService(gateway);

        service.registerActor(new Actor(
            "U001",
            "Operations Reporter",
            ActorRole.REPORTER,
            "Operations"
        ));

        service.registerActor(new Actor(
            "U002",
            "Technical Responder",
            ActorRole.RESPONDER,
            "Technology"
        ));

        service.registerActor(new Actor(
            "U003",
            "Incident Manager",
            ActorRole.INCIDENT_MANAGER,
            "Operations"
        ));

        service.registerActor(new Actor(
            "U004",
            "Executive Director",
            ActorRole.ADMINISTRATOR,
            "Executive"
        ));

        IncidentView incident = service.report(
            "U001",
            "Enterprise transaction service outage",
            "Payment transactions are failing in production.",
            "Infrastructure",
            "Technology",
            Severity.CRITICAL,
            Set.of("payments", "production", "availability"),
            null
        );

        System.out.println("\nCREATED INCIDENT");
        System.out.println(incident);

        service.assign(
            incident.id(),
            "U003",
            "U002"
        );

        service.acknowledge(
            incident.id(),
            "U003"
        );

        service.investigate(
            incident.id(),
            "U002"
        );

        service.recordStatusCheck(
            incident.id(),
            "U003",
            new StatusCheck(
                "Database connectivity",
                true,
                true,
                true
            )
        );

        service.recordStatusCheck(
            incident.id(),
            "U003",
            new StatusCheck(
                "Transaction verification",
                true,
                true,
                true
            )
        );

        service.escalate(
            incident.id(),
            "U003",
            "Customer transactions are affected.",
            EscalationLevel.EXECUTIVE
        );

        MergeEvaluation beforeResolution =
            service.evaluateMergeEligibility(
                incident.id(),
                2
            );

        System.out.println("\nPRE-RESOLUTION EVALUATION");
        System.out.println(beforeResolution);

        service.resolve(
            incident.id(),
            "U003",
            "Payment service restored and test transactions verified."
        );

        MergeEvaluation afterResolution =
            service.evaluateMergeEligibility(
                incident.id(),
                2
            );

        System.out.println("\nPOST-RESOLUTION EVALUATION");
        System.out.println(afterResolution);

        service.close(
            incident.id(),
            "U003"
        );

        System.out.println("\nENTERPRISE DASHBOARD");

        service.dashboard().forEach(
            (key, value) ->
                System.out.println(key + ": " + value)
        );

        System.out.println("\nAUDIT EVENT COUNT: " +
            service.auditHistory().size()
        );

        System.out.println("NOTIFICATION COUNT: " +
            gateway.history().size()
        );

        System.out.println("\nEXPECTED FAILURE");

        try {
            service.investigate(
                incident.id(),
                "U002"
            );
        } catch (DomainException error) {
            System.out.println(error.getMessage());
        }

        System.out.println("\nCRITICAL INCIDENT SEARCH");

        service.search(view ->
            view.severity() == Severity.CRITICAL
        ).forEach(System.out::println);

        if (!afterResolution.eligible()) {
            throw new IllegalStateException(
                "Expected resolution conditions were not satisfied."
            );
        }
    }
}
