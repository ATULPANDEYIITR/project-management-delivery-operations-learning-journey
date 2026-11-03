import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class RaciGovernance {

    enum Responsibility {
        RESPONSIBLE("R"),
        ACCOUNTABLE("A"),
        CONSULTED("C"),
        INFORMED("I");

        private final String code;

        Responsibility(String code) {
            this.code = code;
        }

        public String code() {
            return code;
        }
    }

    enum MatrixState {
        DRAFT,
        IN_REVIEW,
        APPROVED,
        ACTIVE
    }

    record Role(
        String code,
        String name,
        String department,
        int maxResponsibleTasks
    ) {
        Role {
            code = requireText(code, "Role code").toUpperCase(Locale.ROOT);
            name = requireText(name, "Role name");
            department = requireText(department, "Department");

            if (maxResponsibleTasks < -1) {
                throw new IllegalArgumentException(
                    "Role capacity must be -1 or a non-negative integer."
                );
            }
        }

        boolean hasCapacityLimit() {
            return maxResponsibleTasks >= 0;
        }
    }

    record WorkItem(
        String id,
        String title,
        boolean securitySensitive
    ) {
        WorkItem {
            id = requireText(id, "Task ID");
            title = requireText(title, "Task title");
        }
    }

    record MatrixPolicy(
        boolean requireSecurityConsultation,
        String securityRoleCode
    ) {
        MatrixPolicy {
            securityRoleCode = requireText(
                securityRoleCode,
                "Security role code"
            ).toUpperCase(Locale.ROOT);
        }
    }

    record ApprovalPolicy(
        Set<String> eligibleApprovers,
        int requiredApprovals,
        boolean prohibitAuthorApproval
    ) {
        ApprovalPolicy {
            eligibleApprovers = Set.copyOf(eligibleApprovers);

            if (eligibleApprovers.isEmpty()) {
                throw new IllegalArgumentException(
                    "At least one eligible matrix approver is required."
                );
            }
            if (requiredApprovals < 1 ||
                requiredApprovals > eligibleApprovers.size()) {
                throw new IllegalArgumentException(
                    "Required approvals must be between one and the number of eligible approvers."
                );
            }
        }
    }

    record AuditEntry(
        Instant timestamp,
        String actor,
        String action,
        String details
    ) {}

    static class RaciPolicyException extends RuntimeException {
        RaciPolicyException(String message) {
            super(message);
        }
    }

    static class RaciMatrix {
        private final String projectId;
        private final String projectName;
        private final String author;
        private final MatrixPolicy matrixPolicy;
        private final ApprovalPolicy approvalPolicy;

        private final Map<String, Role> roles = new LinkedHashMap<>();
        private final Map<String, WorkItem> tasks = new LinkedHashMap<>();
        private final Map<String, Map<String, Responsibility>> assignments =
            new LinkedHashMap<>();

        private final Set<String> approvals = new LinkedHashSet<>();
        private final List<AuditEntry> audit = new ArrayList<>();

        private MatrixState state = MatrixState.DRAFT;
        private int version = 1;

        RaciMatrix(
            String projectId,
            String projectName,
            String author,
            MatrixPolicy matrixPolicy,
            ApprovalPolicy approvalPolicy
        ) {
            this.projectId = requireText(projectId, "Project ID");
            this.projectName = requireText(projectName, "Project name");
            this.author = requireText(author, "Author");
            this.matrixPolicy = Objects.requireNonNull(matrixPolicy);
            this.approvalPolicy = Objects.requireNonNull(approvalPolicy);
        }

        private void ensureDraft() {
            if (state != MatrixState.DRAFT) {
                throw new RaciPolicyException(
                    "Roles, tasks, and assignments can only change in DRAFT."
                );
            }
        }

        void addRole(Role role) {
            ensureDraft();
            Objects.requireNonNull(role, "Role cannot be null.");

            if (roles.putIfAbsent(role.code(), role) != null) {
                throw new RaciPolicyException(
                    "Duplicate role code: " + role.code()
                );
            }

            recordEvent("SYSTEM", "ROLE_ADDED", role.code());
        }

        void addTask(WorkItem task) {
            ensureDraft();
            Objects.requireNonNull(task, "Task cannot be null.");

            if (tasks.putIfAbsent(task.id(), task) != null) {
                throw new RaciPolicyException(
                    "Duplicate task ID: " + task.id()
                );
            }

            assignments.put(task.id(), new LinkedHashMap<>());
            recordEvent("SYSTEM", "TASK_ADDED", task.id());
        }

        void assign(
            String taskId,
            String roleCode,
            Responsibility responsibility
        ) {
            ensureDraft();

            if (!tasks.containsKey(taskId)) {
                throw new RaciPolicyException("Unknown task: " + taskId);
            }
            if (!roles.containsKey(roleCode)) {
                throw new RaciPolicyException("Unknown role: " + roleCode);
            }
            Objects.requireNonNull(
                responsibility,
                "Responsibility cannot be null."
            );

            Map<String, Responsibility> row = assignments.get(taskId);

            if (row.containsKey(roleCode)) {
                throw new RaciPolicyException(
                    "Role " + roleCode + " already has an assignment for " + taskId
                );
            }

            row.put(roleCode, responsibility);
            recordEvent(
                "SYSTEM",
                "ASSIGNMENT_ADDED",
                taskId + "/" + roleCode + "=" + responsibility.code()
            );
        }

        List<String> validateMatrix() {
            List<String> violations = new ArrayList<>();

            if (tasks.isEmpty()) {
                violations.add("The matrix contains no tasks.");
            }

            for (WorkItem task : tasks.values()) {
                Map<String, Responsibility> row =
                    assignments.getOrDefault(task.id(), Map.of());

                long accountableCount = row.values().stream()
                    .filter(code -> code == Responsibility.ACCOUNTABLE)
                    .count();

                long responsibleCount = row.values().stream()
                    .filter(code -> code == Responsibility.RESPONSIBLE)
                    .count();

                if (accountableCount != 1) {
                    violations.add(
                        task.id() + ": expected exactly one A; found " +
                        accountableCount + "."
                    );
                }

                if (responsibleCount < 1) {
                    violations.add(
                        task.id() + ": at least one R is required."
                    );
                }

                if (matrixPolicy.requireSecurityConsultation() &&
                    task.securitySensitive() &&
                    row.get(matrixPolicy.securityRoleCode()) != Responsibility.CONSULTED) {
                    violations.add(
                        task.id() + ": " +
                        matrixPolicy.securityRoleCode() +
                        " must be assigned C."
                    );
                }
            }

            return List.copyOf(violations);
        }

        List<String> workloadWarnings() {
            Map<String, Long> workload = new HashMap<>();

            for (Map<String, Responsibility> row : assignments.values()) {
                row.forEach((roleCode, responsibility) -> {
                    if (responsibility == Responsibility.RESPONSIBLE) {
                        workload.merge(roleCode, 1L, Long::sum);
                    }
                });
            }

            List<String> warnings = new ArrayList<>();

            for (Role role : roles.values()) {
                if (!role.hasCapacityLimit()) {
                    continue;
                }

                long count = workload.getOrDefault(role.code(), 0L);
                if (count > role.maxResponsibleTasks()) {
                    warnings.add(
                        role.code() + ": " + count +
                        " Responsible tasks exceed capacity " +
                        role.maxResponsibleTasks() + "."
                    );
                }
            }

            return List.copyOf(warnings);
        }

        void submitForApproval(String actor) {
            requireState(MatrixState.DRAFT);
            String submittingActor = requireText(actor, "Submitting actor");

            List<String> violations = validateMatrix();
            if (!violations.isEmpty()) {
                throw new RaciPolicyException(
                    "Submission blocked:\n- " +
                    String.join("\n- ", violations)
                );
            }

            state = MatrixState.IN_REVIEW;
            recordEvent(
                submittingActor,
                "SUBMITTED_FOR_APPROVAL",
                "Version " + version
            );
        }

        void approve(String reviewer) {
            requireState(MatrixState.IN_REVIEW);
            String reviewerId = requireText(reviewer, "Reviewer");

            if (!approvalPolicy.eligibleApprovers().contains(reviewerId)) {
                throw new RaciPolicyException(
                    "Reviewer is not eligible: " + reviewerId
                );
            }

            if (approvalPolicy.prohibitAuthorApproval() &&
                reviewerId.equals(author)) {
                throw new RaciPolicyException(
                    "The matrix author cannot approve their own submission."
                );
            }

            if (!approvals.add(reviewerId)) {
                throw new RaciPolicyException(
                    "Duplicate approval from: " + reviewerId
                );
            }

            recordEvent(
                reviewerId,
                "APPROVAL_RECORDED",
                approvals.size() + "/" +
                approvalPolicy.requiredApprovals()
            );

            if (approvals.size() >= approvalPolicy.requiredApprovals()) {
                state = MatrixState.APPROVED;
                recordEvent(
                    reviewerId,
                    "MATRIX_APPROVED",
                    "Required approvals received."
                );
            }
        }

        void publish() {
            requireState(MatrixState.APPROVED);

            List<String> violations = validateMatrix();
            if (!violations.isEmpty()) {
                throw new RaciPolicyException(
                    "Publication blocked:\n" +
                    String.join("\n", violations)
                );
            }

            state = MatrixState.ACTIVE;
            version++;
            recordEvent(
                "SYSTEM",
                "MATRIX_PUBLISHED",
                "Active version " + version
            );
        }

        private void requireState(MatrixState expected) {
            if (state != expected) {
                throw new RaciPolicyException(
                    "Expected state " + expected + " but found " + state
                );
            }
        }

        private void recordEvent(
            String actor,
            String action,
            String details
        ) {
            audit.add(new AuditEntry(
                Instant.now(),
                actor,
                action,
                details
            ));
        }

        void printMatrix() {
            System.out.println("\nRACI Matrix");
            System.out.printf("%-36s", "Work item");

            for (Role role : roles.values()) {
                System.out.printf(" | %-14s", role.code());
            }
            System.out.println();

            System.out.println("-".repeat(36 + roles.size() * 17));

            for (WorkItem task : tasks.values()) {
                System.out.printf(
                    "%-36s",
                    task.id() + ": " + task.title()
                );

                Map<String, Responsibility> row =
                    assignments.getOrDefault(task.id(), Map.of());

                for (Role role : roles.values()) {
                    Responsibility responsibility = row.get(role.code());
                    String code = responsibility == null
                        ? "-"
                        : responsibility.code();

                    System.out.printf(" | %-14s", code);
                }
                System.out.println();
            }
        }

        void printWorkload() {
            Map<String, EnumMap<Responsibility, Integer>> counts =
                new LinkedHashMap<>();

            for (Role role : roles.values()) {
                EnumMap<Responsibility, Integer> roleCounts =
                    new EnumMap<>(Responsibility.class);

                for (Responsibility responsibility : Responsibility.values()) {
                    roleCounts.put(responsibility, 0);
                }

                counts.put(role.code(), roleCounts);
            }

            assignments.values().forEach(row ->
                row.forEach((roleCode, responsibility) ->
                    counts.get(roleCode).merge(responsibility, 1, Integer::sum)
                )
            );

            System.out.println("\nRole workload");
            counts.forEach((roleCode, values) -> {
                System.out.printf(
                    "%s: R=%d, A=%d, C=%d, I=%d%n",
                    roleCode,
                    values.get(Responsibility.RESPONSIBLE),
                    values.get(Responsibility.ACCOUNTABLE),
                    values.get(Responsibility.CONSULTED),
                    values.get(Responsibility.INFORMED)
                );
            });
        }

        MatrixState state() {
            return state;
        }

        int version() {
            return version;
        }

        List<AuditEntry> auditEntries() {
            return List.copyOf(audit);
        }
    }

    private static String requireText(String value, String field) {
        Objects.requireNonNull(value, field + " cannot be null.");

        if (value.isBlank()) {
            throw new IllegalArgumentException(field + " cannot be blank.");
        }

        return value.trim();
    }

    private static MatrixPolicy defaultMatrixPolicy() {
        return new MatrixPolicy(true, "SECURITY_OFFICER");
    }

    private static ApprovalPolicy defaultApprovalPolicy() {
        return new ApprovalPolicy(
            Set.of("GOVERNANCE_BOARD", "SECURITY_GOVERNANCE"),
            2,
            true
        );
    }

    private static RaciMatrix buildCloudMigrationMatrix() {
        RaciMatrix matrix = new RaciMatrix(
            "PRJ-100",
            "Cloud Infrastructure Migration",
            "PM-001",
            defaultMatrixPolicy(),
            defaultApprovalPolicy()
        );

        matrix.addRole(new Role(
            "SPONSOR", "Project Sponsor", "Executive Office", -1
        ));
        matrix.addRole(new Role(
            "PM", "Project Manager", "Program Management", -1
        ));
        matrix.addRole(new Role(
            "ARCHITECT", "Cloud Architect", "Technology", 2
        ));
        matrix.addRole(new Role(
            "SECURITY_OFFICER", "Security Officer", "Information Security", -1
        ));
        matrix.addRole(new Role(
            "QA", "Quality Lead", "Quality Assurance", -1
        ));
        matrix.addRole(new Role(
            "OPERATIONS", "Operations Lead", "IT Operations", 2
        ));

        matrix.addTask(new WorkItem(
            "T1", "Inventory and discovery", false
        ));
        matrix.addTask(new WorkItem(
            "T2", "Target architecture approval", true
        ));
        matrix.addTask(new WorkItem(
            "T3", "Production migration", true
        ));
        matrix.addTask(new WorkItem(
            "T4", "Acceptance testing", false
        ));

        assign(matrix, "T1", "SPONSOR", Responsibility.ACCOUNTABLE);
        assign(matrix, "T1", "PM", Responsibility.RESPONSIBLE);
        assign(matrix, "T1", "ARCHITECT", Responsibility.CONSULTED);
        assign(matrix, "T1", "SECURITY_OFFICER", Responsibility.INFORMED);
        assign(matrix, "T1", "QA", Responsibility.INFORMED);
        assign(matrix, "T1", "OPERATIONS", Responsibility.CONSULTED);

        assign(matrix, "T2", "SPONSOR", Responsibility.INFORMED);
        assign(matrix, "T2", "PM", Responsibility.ACCOUNTABLE);
        assign(matrix, "T2", "ARCHITECT", Responsibility.RESPONSIBLE);
        assign(matrix, "T2", "SECURITY_OFFICER", Responsibility.CONSULTED);
        assign(matrix, "T2", "QA", Responsibility.INFORMED);
        assign(matrix, "T2", "OPERATIONS", Responsibility.CONSULTED);

        assign(matrix, "T3", "SPONSOR", Responsibility.INFORMED);
        assign(matrix, "T3", "PM", Responsibility.ACCOUNTABLE);
        assign(matrix, "T3", "ARCHITECT", Responsibility.RESPONSIBLE);
        assign(matrix, "T3", "SECURITY_OFFICER", Responsibility.CONSULTED);
        assign(matrix, "T3", "QA", Responsibility.INFORMED);
        assign(matrix, "T3", "OPERATIONS", Responsibility.RESPONSIBLE);

        assign(matrix, "T4", "SPONSOR", Responsibility.INFORMED);
        assign(matrix, "T4", "PM", Responsibility.ACCOUNTABLE);
        assign(matrix, "T4", "ARCHITECT", Responsibility.INFORMED);
        assign(matrix, "T4", "SECURITY_OFFICER", Responsibility.INFORMED);
        assign(matrix, "T4", "QA", Responsibility.RESPONSIBLE);
        assign(matrix, "T4", "OPERATIONS", Responsibility.CONSULTED);

        return matrix;
    }

    private static void assign(
        RaciMatrix matrix,
        String taskId,
        String roleCode,
        Responsibility responsibility
    ) {
        matrix.assign(taskId, roleCode, responsibility);
    }

    private static void demonstrateInvalidMatrix() {
        RaciMatrix incomplete = new RaciMatrix(
            "PRJ-200",
            "Incomplete Payment Platform",
            "PM-002",
            defaultMatrixPolicy(),
            defaultApprovalPolicy()
        );

        incomplete.addRole(new Role(
            "PM", "Project Manager", "Delivery", -1
        ));
        incomplete.addRole(new Role(
            "DEV", "Developer", "Engineering", -1
        ));
        incomplete.addRole(new Role(
            "SECURITY_OFFICER", "Security Officer", "Security", -1
        ));

        incomplete.addTask(new WorkItem(
            "P1", "Payment security review", true
        ));

        incomplete.assign("P1", "DEV", Responsibility.RESPONSIBLE);
        incomplete.assign("P1", "SECURITY_OFFICER", Responsibility.INFORMED);

        try {
            incomplete.submitForApproval("PM-002");
        } catch (RaciPolicyException exception) {
            System.out.println("\nExpected submission failure:");
            System.out.println(exception.getMessage());
        }
    }

    public static void main(String[] args) {
        try {
            RaciMatrix matrix = buildCloudMigrationMatrix();

            List<String> violations = matrix.validateMatrix();
            if (!violations.isEmpty()) {
                throw new RaciPolicyException(
                    "Invalid demonstration matrix: " +
                    String.join("; ", violations)
                );
            }

            matrix.printMatrix();
            matrix.printWorkload();

            List<String> warnings = matrix.workloadWarnings();
            System.out.println("\nWorkload warnings:");
            if (warnings.isEmpty()) {
                System.out.println("None");
            } else {
                warnings.forEach(warning -> System.out.println("- " + warning));
            }

            matrix.submitForApproval("PM-001");

            try {
                matrix.approve("PM-001");
            } catch (RaciPolicyException exception) {
                System.out.println(
                    "\nExpected author-approval rejection: " +
                    exception.getMessage()
                );
            }

            matrix.approve("GOVERNANCE_BOARD");
            matrix.approve("SECURITY_GOVERNANCE");
            matrix.publish();

            System.out.println("\nState: " + matrix.state());
            System.out.println("Version: " + matrix.version());
            System.out.println("Audit entries: " + matrix.auditEntries().size());

            try {
                matrix.assign(
                    "T1",
                    "PM",
                    Responsibility.ACCOUNTABLE
                );
            } catch (RaciPolicyException exception) {
                System.out.println(
                    "\nExpected modification failure: " +
                    exception.getMessage()
                );
            }

            demonstrateInvalidMatrix();

        } catch (RuntimeException exception) {
            System.err.println("Execution failed: " + exception.getMessage());
            System.exit(1);
        }
    }
}
