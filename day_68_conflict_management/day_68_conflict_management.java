import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

public class ConflictManagementSystem {

    enum ConflictType {
        COMMUNICATION,
        ROLE_AMBIGUITY,
        RESOURCE_ALLOCATION,
        PERFORMANCE,
        PERSONAL_DISAGREEMENT,
        PRIORITY_MISMATCH,
        WORKING_STYLE
    }

    enum Severity {
        LOW, MEDIUM, HIGH, CRITICAL
    }

    enum Status {
        REPORTED,
        ASSESSMENT,
        DISCUSSION,
        MEDIATION,
        RESOLVED,
        ESCALATED,
        CLOSED
    }

    enum ResolutionMethod {
        COLLABORATION,
        COMPROMISE,
        ACCOMMODATION,
        NEGOTIATION,
        MANAGER_DECISION,
        FORMAL_ESCALATION
    }

    enum Role {
        EMPLOYEE,
        MANAGER,
        HR_MEDIATOR,
        ADMINISTRATOR
    }

    static class ConflictException extends RuntimeException {
        ConflictException(String message) {
            super(message);
        }
    }

    static class ValidationException extends ConflictException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class AuthorizationException extends ConflictException {
        AuthorizationException(String message) {
            super(message);
        }
    }

    static class TransitionException extends ConflictException {
        TransitionException(String message) {
            super(message);
        }
    }

    record TeamMember(
        String id,
        String name,
        String department,
        Role role,
        boolean active
    ) {
        TeamMember {
            requireText(id, "Member ID");
            requireText(name, "Name");
            requireText(department, "Department");
            Objects.requireNonNull(role);
        }
    }

    record AuditEvent(
        String eventId,
        String caseId,
        String actorId,
        String action,
        Instant timestamp
    ) {}

    record DiscussionEntry(
        String authorId,
        String message,
        Instant timestamp
    ) {
        DiscussionEntry {
            requireText(authorId, "Author");
            requireText(message, "Message");
        }
    }

    record StatusChange(
        Status previous,
        Status current,
        String actorId,
        Instant timestamp
    ) {}

    static class ResolutionAgreement {
        private final ResolutionMethod method;
        private final List<String> actions;
        private final List<String> criteria;
        private final Set<String> responsibleMembers;
        private final Instant deadline;
        private final Set<String> acceptedBy = new HashSet<>();

        ResolutionAgreement(
            ResolutionMethod method,
            List<String> actions,
            List<String> criteria,
            Set<String> responsibleMembers,
            Instant deadline,
            Set<String> participants
        ) {
            this.method = Objects.requireNonNull(method);
            this.actions = List.copyOf(actions);
            this.criteria = List.copyOf(criteria);
            this.responsibleMembers = Set.copyOf(responsibleMembers);
            this.deadline = Objects.requireNonNull(deadline);

            if (this.actions.isEmpty() || this.criteria.isEmpty()) {
                throw new ValidationException(
                    "Actions and success criteria are required"
                );
            }

            if (this.responsibleMembers.isEmpty() ||
                !participants.containsAll(this.responsibleMembers)) {
                throw new ValidationException(
                    "Invalid responsible members"
                );
            }

            if (!deadline.isAfter(Instant.now())) {
                throw new ValidationException(
                    "Deadline must be in the future"
                );
            }
        }

        ResolutionMethod method() {
            return method;
        }

        List<String> actions() {
            return actions;
        }

        List<String> criteria() {
            return criteria;
        }

        Instant deadline() {
            return deadline;
        }

        Set<String> acceptedBy() {
            return Collections.unmodifiableSet(acceptedBy);
        }

        void accept(String memberId, Set<String> participants) {
            if (!participants.contains(memberId)) {
                throw new AuthorizationException(
                    "Only participants can accept an agreement"
                );
            }

            acceptedBy.add(memberId);
        }

        boolean isAcceptedByAll(Set<String> participants) {
            return acceptedBy.containsAll(participants);
        }
    }

    static class ConflictCase {
        private final String id;
        private final String title;
        private final String description;
        private final ConflictType type;
        private final Severity severity;
        private final String reporterId;
        private final Set<String> participants;
        private final Instant createdAt;

        private Status status = Status.REPORTED;
        private String mediatorId;
        private ResolutionAgreement agreement;

        private final List<DiscussionEntry> discussions =
            new ArrayList<>();

        private final List<StatusChange> history =
            new ArrayList<>();

        ConflictCase(
            String id,
            String title,
            String description,
            ConflictType type,
            Severity severity,
            String reporterId,
            Set<String> participants
        ) {
            requireText(id, "Case ID");
            requireText(title, "Title");
            requireText(description, "Description");

            this.id = id;
            this.title = title;
            this.description = description;
            this.type = Objects.requireNonNull(type);
            this.severity = Objects.requireNonNull(severity);
            this.reporterId = reporterId;
            this.participants = Set.copyOf(participants);
            this.createdAt = Instant.now();

            if (this.participants.size() < 2) {
                throw new ValidationException(
                    "At least two participants are required"
                );
            }

            if (!this.participants.contains(reporterId)) {
                throw new ValidationException(
                    "Reporter must be a participant"
                );
            }
        }

        String id() {
            return id;
        }

        String title() {
            return title;
        }

        Status status() {
            return status;
        }

        Severity severity() {
            return severity;
        }

        ConflictType type() {
            return type;
        }

        Set<String> participants() {
            return participants;
        }

        ResolutionAgreement agreement() {
            return agreement;
        }

        List<DiscussionEntry> discussions() {
            return List.copyOf(discussions);
        }

        List<StatusChange> history() {
            return List.copyOf(history);
        }
    }

    interface ResolutionPolicy {
        ResolutionMethod recommend(ConflictCase conflict);
    }

    static class DefaultResolutionPolicy
        implements ResolutionPolicy {

        @Override
        public ResolutionMethod recommend(ConflictCase conflict) {
            if (conflict.severity() == Severity.CRITICAL) {
                return ResolutionMethod.FORMAL_ESCALATION;
            }

            if (conflict.type() ==
                ConflictType.RESOURCE_ALLOCATION) {
                return ResolutionMethod.NEGOTIATION;
            }

            if (conflict.type() ==
                ConflictType.PRIORITY_MISMATCH) {
                return ResolutionMethod.COLLABORATION;
            }

            if (conflict.severity() == Severity.HIGH) {
                return ResolutionMethod.COLLABORATION;
            }

            return ResolutionMethod.COMPROMISE;
        }
    }

    static class ConflictManagementService {
        private final Map<String, TeamMember> members =
            new HashMap<>();

        private final Map<String, ConflictCase> cases =
            new HashMap<>();

        private final List<AuditEvent> audit =
            new ArrayList<>();

        private final ResolutionPolicy policy;

        private final Map<Status, Set<Status>> transitions =
            new EnumMap<>(Status.class);

        ConflictManagementService(ResolutionPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
            configureTransitions();
        }

        private void configureTransitions() {
            transitions.put(Status.REPORTED, EnumSet.of(
                Status.ASSESSMENT, Status.ESCALATED
            ));

            transitions.put(Status.ASSESSMENT, EnumSet.of(
                Status.DISCUSSION, Status.MEDIATION,
                Status.ESCALATED
            ));

            transitions.put(Status.DISCUSSION, EnumSet.of(
                Status.MEDIATION, Status.RESOLVED,
                Status.ESCALATED
            ));

            transitions.put(Status.MEDIATION, EnumSet.of(
                Status.DISCUSSION, Status.RESOLVED,
                Status.ESCALATED
            ));

            transitions.put(Status.RESOLVED, EnumSet.of(
                Status.CLOSED, Status.ESCALATED
            ));

            transitions.put(Status.ESCALATED, EnumSet.of(
                Status.CLOSED
            ));

            transitions.put(Status.CLOSED, EnumSet.noneOf(Status.class));
        }

        void registerMember(TeamMember member) {
            if (members.putIfAbsent(member.id(), member) != null) {
                throw new ValidationException(
                    "Duplicate member ID"
                );
            }
        }

        private TeamMember getActiveMember(String id) {
            TeamMember member = members.get(id);

            if (member == null || !member.active()) {
                throw new AuthorizationException(
                    "Member is unavailable"
                );
            }

            return member;
        }

        private ConflictCase getCase(String id) {
            ConflictCase conflict = cases.get(id);

            if (conflict == null) {
                throw new ValidationException(
                    "Conflict case not found"
                );
            }

            return conflict;
        }

        private void record(
            String caseId,
            String actorId,
            String action
        ) {
            audit.add(new AuditEvent(
                UUID.randomUUID().toString(),
                caseId,
                actorId,
                action,
                Instant.now()
            ));
        }

        void createCase(ConflictCase conflict) {
            if (cases.containsKey(conflict.id())) {
                throw new ValidationException("Duplicate case ID");
            }

            getActiveMember(conflict.reporterId);

            conflict.participants.forEach(this::getActiveMember);

            cases.put(conflict.id(), conflict);

            record(
                conflict.id(),
                conflict.reporterId,
                "CASE_CREATED"
            );
        }

        void assignMediator(String caseId, String mediatorId) {
            ConflictCase conflict = getCase(caseId);

            TeamMember mediator = getActiveMember(mediatorId);

            if (mediator.role() != Role.HR_MEDIATOR &&
                mediator.role() != Role.ADMINISTRATOR) {
                throw new AuthorizationException(
                    "Mediator role required"
                );
            }

            if (conflict.participants.contains(mediatorId)) {
                throw new ValidationException(
                    "Mediator cannot be a participant"
                );
            }

            conflict.mediatorId = mediatorId;

            record(caseId, mediatorId, "MEDIATOR_ASSIGNED");
        }

        void transition(
            String caseId,
            Status next,
            String actorId
        ) {
            ConflictCase conflict = getCase(caseId);
            getActiveMember(actorId);

            if (!transitions.get(conflict.status).contains(next)) {
                throw new TransitionException(
                    "Invalid status transition: " +
                    conflict.status + " -> " + next
                );
            }

            Status previous = conflict.status;
            conflict.status = next;

            conflict.history.add(new StatusChange(
                previous,
                next,
                actorId,
                Instant.now()
            ));

            record(
                caseId,
                actorId,
                "STATUS_CHANGED:" + previous + ":" + next
            );
        }

        void addDiscussion(
            String caseId,
            String actorId,
            String message
        ) {
            ConflictCase conflict = getCase(caseId);
            getActiveMember(actorId);

            boolean authorized =
                conflict.participants.contains(actorId) ||
                Objects.equals(conflict.mediatorId, actorId);

            if (!authorized) {
                throw new AuthorizationException(
                    "Discussion access denied"
                );
            }

            if (conflict.status != Status.ASSESSMENT &&
                conflict.status != Status.DISCUSSION &&
                conflict.status != Status.MEDIATION) {
                throw new TransitionException(
                    "Discussion is unavailable"
                );
            }

            conflict.discussions.add(new DiscussionEntry(
                actorId,
                message,
                Instant.now()
            ));

            record(caseId, actorId, "DISCUSSION_ADDED");
        }

        ResolutionMethod recommend(String caseId) {
            return policy.recommend(getCase(caseId));
        }

        void createAgreement(
            String caseId,
            String actorId,
            ResolutionAgreement agreement
        ) {
            ConflictCase conflict = getCase(caseId);
            getActiveMember(actorId);

            if (conflict.status != Status.DISCUSSION &&
                conflict.status != Status.MEDIATION) {
                throw new TransitionException(
                    "Agreement requires discussion or mediation"
                );
            }

            conflict.agreement = Objects.requireNonNull(agreement);

            record(caseId, actorId, "AGREEMENT_CREATED");
        }

        void acceptAgreement(
            String caseId,
            String memberId
        ) {
            ConflictCase conflict = getCase(caseId);
            getActiveMember(memberId);

            if (conflict.agreement == null) {
                throw new ValidationException(
                    "Agreement does not exist"
                );
            }

            conflict.agreement.accept(
                memberId,
                conflict.participants
            );

            record(caseId, memberId, "AGREEMENT_ACCEPTED");
        }

        void resolve(String caseId, String managerId) {
            ConflictCase conflict = getCase(caseId);
            TeamMember manager = getActiveMember(managerId);

            if (manager.role() != Role.MANAGER &&
                manager.role() != Role.ADMINISTRATOR) {
                throw new AuthorizationException(
                    "Manager authorization required"
                );
            }

            if (conflict.agreement == null ||
                !conflict.agreement.isAcceptedByAll(
                    conflict.participants
                )) {
                throw new ValidationException(
                    "A fully accepted agreement is required"
                );
            }

            transition(caseId, Status.RESOLVED, managerId);
        }

        void escalate(String caseId, String managerId) {
            TeamMember manager = getActiveMember(managerId);

            if (manager.role() != Role.MANAGER &&
                manager.role() != Role.ADMINISTRATOR) {
                throw new AuthorizationException(
                    "Manager authorization required"
                );
            }

            transition(caseId, Status.ESCALATED, managerId);
        }

        Map<Status, Long> statusReport() {
            return cases.values().stream().collect(
                Collectors.groupingBy(
                    conflict -> conflict.status,
                    () -> new EnumMap<>(Status.class),
                    Collectors.counting()
                )
            );
        }

        List<ConflictCase> openCases() {
            return cases.values().stream()
                .filter(conflict ->
                    conflict.status != Status.CLOSED &&
                    conflict.status != Status.RESOLVED
                )
                .toList();
        }

        List<AuditEvent> auditReport() {
            return List.copyOf(audit);
        }

        void printReport() {
            System.out.println("\nCONFLICT MANAGEMENT REPORT");

            System.out.println(
                "Total cases: " + cases.size()
            );

            statusReport().forEach((status, count) ->
                System.out.println(status + ": " + count)
            );

            System.out.println("\nOPEN CASES");

            openCases().forEach(conflict ->
                System.out.println(
                    conflict.id() + " | " +
                    conflict.title() + " | " +
                    conflict.status()
                )
            );

            System.out.println(
                "\nAudit events: " + audit.size()
            );
        }
    }

    private static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(
                field + " cannot be empty"
            );
        }
    }

    public static void main(String[] args) {
        try {
            ConflictManagementService service =
                new ConflictManagementService(
                    new DefaultResolutionPolicy()
                );

            service.registerMember(new TeamMember(
                "E01", "Ananya", "Engineering",
                Role.EMPLOYEE, true
            ));

            service.registerMember(new TeamMember(
                "E02", "Rahul", "Product",
                Role.EMPLOYEE, true
            ));

            service.registerMember(new TeamMember(
                "E03", "Priya", "Management",
                Role.MANAGER, true
            ));

            service.registerMember(new TeamMember(
                "E04", "Arjun", "Human Resources",
                Role.HR_MEDIATOR, true
            ));

            ConflictCase conflict = new ConflictCase(
                "CF-4001",
                "Release priority disagreement",
                "Engineering and Product disagree on release scope.",
                ConflictType.PRIORITY_MISMATCH,
                Severity.MEDIUM,
                "E01",
                Set.of("E01", "E02")
            );

            service.createCase(conflict);
            service.assignMediator("CF-4001", "E04");

            service.transition(
                "CF-4001", Status.ASSESSMENT, "E03"
            );

            service.transition(
                "CF-4001", Status.DISCUSSION, "E03"
            );

            service.addDiscussion(
                "CF-4001",
                "E01",
                "Engineering needs more testing time."
            );

            service.addDiscussion(
                "CF-4001",
                "E02",
                "Product requires the core release features."
            );

            ResolutionMethod method =
                service.recommend("CF-4001");

            System.out.println("Recommended method: " + method);

            ResolutionAgreement agreement =
                new ResolutionAgreement(
                    method,
                    List.of(
                        "Release core features first",
                        "Move optional features to the next iteration",
                        "Conduct joint acceptance testing"
                    ),
                    List.of(
                        "Acceptance tests pass",
                        "Both teams approve the release plan"
                    ),
                    Set.of("E01", "E02"),
                    Instant.now().plus(14, ChronoUnit.DAYS),
                    conflict.participants()
                );

            service.createAgreement(
                "CF-4001",
                "E03",
                agreement
            );

            service.acceptAgreement("CF-4001", "E01");
            service.acceptAgreement("CF-4001", "E02");

            service.resolve("CF-4001", "E03");

            service.transition(
                "CF-4001", Status.CLOSED, "E03"
            );

            service.printReport();

            System.out.println(
                "\nAudit records: " +
                service.auditReport().size()
            );

            try {
                service.transition(
                    "CF-4001", Status.RESOLVED, "E03"
                );
            } catch (TransitionException exception) {
                System.out.println(
                    "\nExpected failure: " +
                    exception.getMessage()
                );
            }

        } catch (ConflictException exception) {
            System.err.println(
                "Application error: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
