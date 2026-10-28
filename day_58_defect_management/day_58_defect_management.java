import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class DefectManagementEnterprise {

    enum Severity {
        BLOCKER, CRITICAL, MAJOR, MINOR, TRIVIAL
    }

    enum Priority {
        P0, P1, P2, P3
    }

    enum Status {
        NEW, TRIAGED, ASSIGNED, IN_PROGRESS,
        RESOLVED, VERIFIED, REOPENED, CLOSED, REJECTED
    }

    enum Role {
        REPORTER, DEVELOPER, QA, LEAD, MANAGER
    }

    record User(long id, String name, Role role) {
        public User {
            if (id <= 0 || name == null || name.isBlank()) {
                throw new IllegalArgumentException("Invalid user.");
            }
            Objects.requireNonNull(role, "Role is required.");
        }
    }

    record StatusCheck(String name, boolean passed) {
        public StatusCheck {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Check name is required.");
            }
        }
    }

    record AuditEvent(
        Instant timestamp,
        long actorId,
        String action,
        String details
    ) {}

    static final class DefectException extends RuntimeException {
        DefectException(String message) {
            super(message);
        }
    }

    static final class Defect {
        private final long id;
        private final String title;
        private final String component;
        private final Severity severity;
        private final Priority priority;
        private final long reporterId;
        private Status status;
        private Long assigneeId;
        private String resolution;
        private final List<AuditEvent> auditTrail = new ArrayList<>();

        Defect(
            long id,
            String title,
            String component,
            Severity severity,
            Priority priority,
            long reporterId
        ) {
            if (title == null || title.isBlank()) {
                throw new IllegalArgumentException("Title is required.");
            }
            if (component == null || component.isBlank()) {
                throw new IllegalArgumentException("Component is required.");
            }

            this.id = id;
            this.title = title.trim();
            this.component = component.trim();
            this.severity = Objects.requireNonNull(severity);
            this.priority = Objects.requireNonNull(priority);
            this.reporterId = reporterId;
            this.status = Status.NEW;
            audit(reporterId, "CREATED", "Defect registered.");
        }

        private void audit(long actorId, String action, String details) {
            auditTrail.add(new AuditEvent(Instant.now(), actorId, action, details));
        }

        private void requireStatus(Set<Status> allowed) {
            if (!allowed.contains(status)) {
                throw new DefectException(
                    "Invalid transition from " + status
                );
            }
        }

        void triage(long actorId) {
            requireStatus(Set.of(Status.NEW));
            status = Status.TRIAGED;
            audit(actorId, "TRIAGED", "Defect accepted for triage.");
        }

        void assign(long actorId, long developerId) {
            requireStatus(Set.of(Status.TRIAGED, Status.REOPENED));
            assigneeId = developerId;
            status = Status.ASSIGNED;
            audit(actorId, "ASSIGNED", "Assigned to " + developerId);
        }

        void start(long actorId) {
            requireStatus(Set.of(Status.ASSIGNED));
            if (!Objects.equals(assigneeId, actorId)) {
                throw new DefectException("Only the assignee may start work.");
            }
            status = Status.IN_PROGRESS;
            audit(actorId, "IN_PROGRESS", "Implementation started.");
        }

        void resolve(long actorId, String resolution) {
            requireStatus(Set.of(Status.IN_PROGRESS));
            if (!Objects.equals(assigneeId, actorId)) {
                throw new DefectException("Only the assignee may resolve.");
            }
            if (resolution == null || resolution.isBlank()) {
                throw new DefectException("Resolution is required.");
            }
            this.resolution = resolution.trim();
            status = Status.RESOLVED;
            audit(actorId, "RESOLVED", this.resolution);
        }

        void verify(long actorId, boolean passed) {
            requireStatus(Set.of(Status.RESOLVED));
            status = passed ? Status.VERIFIED : Status.REOPENED;
            audit(
                actorId,
                passed ? "VERIFIED" : "REOPENED",
                passed ? "Verification passed." : "Verification failed."
            );
        }

        void close(long actorId) {
            requireStatus(Set.of(Status.VERIFIED));
            status = Status.CLOSED;
            audit(actorId, "CLOSED", "Defect closed after verification.");
        }

        long id() {
            return id;
        }

        String title() {
            return title;
        }

        String component() {
            return component;
        }

        Severity severity() {
            return severity;
        }

        Priority priority() {
            return priority;
        }

        Status status() {
            return status;
        }

        Long assigneeId() {
            return assigneeId;
        }

        List<AuditEvent> auditTrail() {
            return List.copyOf(auditTrail);
        }

        @Override
        public String toString() {
            return id + " | " + title + " | " + component + " | "
                + severity + " | " + priority + " | " + status;
        }
    }

    interface DefectPolicy {
        boolean permits(Defect defect, PolicyContext context);
    }

    record PolicyContext(
        List<StatusCheck> checks,
        int requiredApprovals,
        int actualApprovals,
        boolean conversationsResolved,
        boolean managerApproval
    ) {
        PolicyContext {
            checks = List.copyOf(checks);
            if (requiredApprovals < 0 || actualApprovals < 0) {
                throw new IllegalArgumentException("Approval counts cannot be negative.");
            }
        }
    }

    static final class EnterpriseMergePolicy implements DefectPolicy {
        @Override
        public boolean permits(Defect defect, PolicyContext context) {
            if (defect.status() != Status.VERIFIED) {
                return false;
            }

            if (context.actualApprovals() < context.requiredApprovals()) {
                return false;
            }

            if (!context.conversationsResolved()) {
                return false;
            }

            if (defect.severity() == Severity.BLOCKER ||
                defect.severity() == Severity.CRITICAL) {
                if (!context.managerApproval()) {
                    return false;
                }
            }

            return context.checks().stream().allMatch(StatusCheck::passed);
        }
    }

    static final class DefectService {
        private final Map<Long, Defect> defects = new HashMap<>();
        private long nextId = 9000;

        Defect register(
            String title,
            String component,
            Severity severity,
            Priority priority,
            long reporterId
        ) {
            Defect defect = new Defect(
                nextId++,
                title,
                component,
                severity,
                priority,
                reporterId
            );
            defects.put(defect.id(), defect);
            return defect;
        }

        List<Defect> openDefects() {
            return defects.values().stream()
                .filter(d -> d.status() != Status.CLOSED &&
                             d.status() != Status.REJECTED)
                .sorted(
                    java.util.Comparator
                        .comparingInt((Defect d) -> severityWeight(d.severity()))
                        .reversed()
                        .thenComparingInt(
                            d -> priorityWeight(d.priority())
                        ).reversed()
                        .thenComparingLong(Defect::id)
                )
                .toList();
        }

        private static int severityWeight(Severity severity) {
            return switch (severity) {
                case BLOCKER -> 5;
                case CRITICAL -> 4;
                case MAJOR -> 3;
                case MINOR -> 2;
                case TRIVIAL -> 1;
            };
        }

        private static int priorityWeight(Priority priority) {
            return switch (priority) {
                case P0 -> 4;
                case P1 -> 3;
                case P2 -> 2;
                case P3 -> 1;
            };
        }
    }

    public static void main(String[] args) {
        DefectService service = new DefectService();

        User qa = new User(1, "Nisha", Role.QA);
        User developer = new User(2, "Arjun", Role.DEVELOPER);
        User manager = new User(3, "Kiran", Role.MANAGER);
        User verifier = new User(4, "Rohit", Role.QA);

        Defect defect = service.register(
            "Authorization succeeds after account deactivation",
            "identity",
            Severity.CRITICAL,
            Priority.P0,
            qa.id()
        );

        defect.triage(qa.id());
        defect.assign(qa.id(), developer.id());
        defect.start(developer.id());
        defect.resolve(
            developer.id(),
            "Authorization now checks active account state on every protected request."
        );
        defect.verify(verifier.id(), true);

        PolicyContext context = new PolicyContext(
            List.of(
                new StatusCheck("unit-tests", true),
                new StatusCheck("integration-tests", true),
                new StatusCheck("security-tests", true)
            ),
            2,
            2,
            true,
            true
        );

        DefectPolicy policy = new EnterpriseMergePolicy();
        boolean eligible = policy.permits(defect, context);

        if (!eligible) {
            throw new DefectException("Defect failed enterprise merge policy.");
        }

        defect.close(manager.id());

        try {
            defect.start(developer.id());
        } catch (DefectException ex) {
            System.out.println("Expected failure: " + ex.getMessage());
        }

        Defect reopened = service.register(
            "Report export loses timezone information",
            "reporting",
            Severity.MAJOR,
            Priority.P2,
            qa.id()
        );

        reopened.triage(qa.id());
        reopened.assign(qa.id(), developer.id());
        reopened.start(developer.id());
        reopened.resolve(
            developer.id(),
            "Report serialization now preserves the originating timezone."
        );
        reopened.verify(verifier.id(), false);

        System.out.println("Closed defect:");
        System.out.println(defect);

        System.out.println("\nPrioritized open defects:");
        service.openDefects().forEach(System.out::println);

        System.out.println("\nEnterprise policy result: " + eligible);

        System.out.println("\nAudit trail:");
        defect.auditTrail().forEach(System.out::println);

        if (defect.status() != Status.CLOSED) {
            throw new AssertionError("Closed-state invariant failed.");
        }

        if (reopened.status() != Status.REOPENED) {
            throw new AssertionError("Reopen-state invariant failed.");
        }
    }
}
