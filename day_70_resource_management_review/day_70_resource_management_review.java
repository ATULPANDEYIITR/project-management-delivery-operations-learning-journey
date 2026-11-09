/*
 * RESOURCE MANAGEMENT REVIEW
 * Enterprise Team Management and Resource Governance
 *
 * Java Version: 17
 *
 * Engineering focus:
 * - Enterprise domain modeling
 * - Immutable records
 * - Resource allocation policies
 * - Team capacity management
 * - Skill-based assignment
 * - Workload distribution
 * - Review lifecycle management
 * - Approval decisions
 * - Risk evaluation
 * - Corrective action ownership
 * - Audit history
 *
 * Compile:
 * javac ResourceManagementReview.java
 *
 * Run:
 * java ResourceManagementReview
 */

import java.time.LocalDate;
import java.time.LocalDateTime;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

import java.util.UUID;
import java.util.stream.Collectors;


// ---------------------------------------------------------
// MAIN APPLICATION
// ---------------------------------------------------------

public class ResourceManagementReview {

    // -----------------------------------------------------
    // ENUMERATIONS
    // -----------------------------------------------------

    enum EmployeeStatus {
        ACTIVE,
        ON_LEAVE,
        INACTIVE
    }

    enum ProjectStatus {
        ACTIVE,
        ON_HOLD,
        COMPLETED
    }

    enum ReviewStatus {
        DRAFT,
        UNDER_REVIEW,
        APPROVED,
        REJECTED
    }

    enum RiskLevel {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum ActionStatus {
        OPEN,
        IN_PROGRESS,
        COMPLETED,
        CANCELLED
    }

    enum Decision {
        APPROVE,
        REJECT
    }


    // -----------------------------------------------------
    // CUSTOM EXCEPTIONS
    // -----------------------------------------------------

    static class ResourceException extends RuntimeException {
        ResourceException(String message) {
            super(message);
        }
    }

    static class CapacityException extends ResourceException {
        CapacityException(String message) {
            super(message);
        }
    }

    static class ReviewException extends ResourceException {
        ReviewException(String message) {
            super(message);
        }
    }


    // -----------------------------------------------------
    // VALIDATION UTILITIES
    // -----------------------------------------------------

    static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ResourceException(
                field + " is required."
            );
        }
    }

    static void validateCapacity(double capacity) {
        if (!Double.isFinite(capacity) || capacity <= 0) {
            throw new ResourceException(
                "Weekly capacity must be positive."
            );
        }
    }

    static void validateSkills(Map<String, Integer> skills) {
        Objects.requireNonNull(skills, "Skills are required.");

        skills.forEach((name, level) -> {
            requireText(name, "Skill name");

            if (level == null || level < 1 || level > 5) {
                throw new ResourceException(
                    "Skill level must be between 1 and 5."
                );
            }
        });
    }


    // -----------------------------------------------------
    // DOMAIN RECORDS
    // -----------------------------------------------------

    record Employee(
        String id,
        String name,
        String department,
        String role,
        Map<String, Integer> skills,
        double weeklyCapacity,
        EmployeeStatus status
    ) {
        Employee {
            requireText(id, "Employee ID");
            requireText(name, "Employee name");
            requireText(department, "Department");
            requireText(role, "Role");

            validateCapacity(weeklyCapacity);
            validateSkills(skills);

            Objects.requireNonNull(status);

            skills = Map.copyOf(skills);
        }

        Employee withStatus(EmployeeStatus newStatus) {
            return new Employee(
                id,
                name,
                department,
                role,
                skills,
                weeklyCapacity,
                newStatus
            );
        }
    }


    record Project(
        String id,
        String name,
        Map<String, Integer> requiredSkills,
        int priority,
        ProjectStatus status
    ) {
        Project {
            requireText(id, "Project ID");
            requireText(name, "Project name");
            validateSkills(requiredSkills);

            if (priority < 1 || priority > 5) {
                throw new ResourceException(
                    "Project priority must be between 1 and 5."
                );
            }

            Objects.requireNonNull(status);

            requiredSkills = Map.copyOf(requiredSkills);
        }
    }


    record Allocation(
        String id,
        String employeeId,
        String projectId,
        double weeklyHours,
        LocalDate start,
        LocalDate end
    ) {
        Allocation {
            requireText(id, "Allocation ID");
            requireText(employeeId, "Employee ID");
            requireText(projectId, "Project ID");

            if (!Double.isFinite(weeklyHours) || weeklyHours <= 0) {
                throw new ResourceException(
                    "Allocation hours must be positive."
                );
            }

            Objects.requireNonNull(start);
            Objects.requireNonNull(end);

            if (start.isAfter(end)) {
                throw new ResourceException(
                    "Invalid allocation period."
                );
            }
        }
    }


    record LeaveRecord(
        String employeeId,
        LocalDate start,
        LocalDate end,
        double unavailableHours
    ) {
        LeaveRecord {
            requireText(employeeId, "Employee ID");

            Objects.requireNonNull(start);
            Objects.requireNonNull(end);

            if (start.isAfter(end)) {
                throw new ResourceException(
                    "Invalid leave period."
                );
            }

            if (
                !Double.isFinite(unavailableHours) ||
                unavailableHours < 0 ||
                unavailableHours > 40
            ) {
                throw new ResourceException(
                    "Invalid unavailable hours."
                );
            }
        }
    }


    record CapacityReport(
        String employeeId,
        double effectiveCapacity,
        double allocatedHours,
        double availableHours,
        double utilization,
        boolean overallocated
    ) {}


    record Risk(
        String employeeId,
        RiskLevel level,
        String reason
    ) {}


    record SkillMatch(
        String employeeId,
        String employeeName,
        double matchPercentage,
        List<String> missingSkills
    ) {
        SkillMatch {
            missingSkills = List.copyOf(missingSkills);
        }
    }


    record ReviewAction(
        String id,
        String description,
        String ownerId,
        LocalDate dueDate,
        ActionStatus status
    ) {
        ReviewAction {
            requireText(id, "Action ID");
            requireText(description, "Action description");
            requireText(ownerId, "Action owner");

            Objects.requireNonNull(dueDate);
            Objects.requireNonNull(status);
        }
    }


    record AuditEvent(
        String eventId,
        String eventType,
        String entityId,
        String description,
        LocalDateTime timestamp
    ) {}


    // -----------------------------------------------------
    // REVIEW POLICY
    // -----------------------------------------------------

    record ReviewPolicy(
        double highUtilizationThreshold,
        double criticalUtilizationThreshold,
        double underutilizationThreshold,
        boolean blockApprovalOnCriticalRisk
    ) {

        ReviewPolicy {
            if (
                highUtilizationThreshold <= 0 ||
                criticalUtilizationThreshold <= highUtilizationThreshold ||
                criticalUtilizationThreshold > 100 ||
                underutilizationThreshold < 0 ||
                underutilizationThreshold >= highUtilizationThreshold
            ) {
                throw new ResourceException(
                    "Invalid resource review policy."
                );
            }
        }

        Risk evaluate(CapacityReport report) {

            if (report.overallocated()) {
                return new Risk(
                    report.employeeId(),
                    RiskLevel.CRITICAL,
                    "Allocated hours exceed capacity."
                );
            }

            if (
                report.utilization() >=
                criticalUtilizationThreshold
            ) {
                return new Risk(
                    report.employeeId(),
                    RiskLevel.HIGH,
                    "Capacity buffer is critically low."
                );
            }

            if (
                report.utilization() >= highUtilizationThreshold
            ) {
                return new Risk(
                    report.employeeId(),
                    RiskLevel.MEDIUM,
                    "High workload concentration."
                );
            }

            if (
                report.utilization() <
                underutilizationThreshold
            ) {
                return new Risk(
                    report.employeeId(),
                    RiskLevel.MEDIUM,
                    "Potential underutilization."
                );
            }

            return new Risk(
                report.employeeId(),
                RiskLevel.LOW,
                "Utilization is within the expected range."
            );
        }
    }


    // -----------------------------------------------------
    // REVIEW ENTITY
    // -----------------------------------------------------

    static class ResourceReview {

        private final String id;
        private final String reviewer;
        private final LocalDate start;
        private final LocalDate end;

        private ReviewStatus status;

        private final List<Risk> findings;
        private final List<ReviewAction> actions;

        private String decisionNotes;

        private String decisionMaker;

        ResourceReview(
            String reviewer,
            LocalDate start,
            LocalDate end,
            List<Risk> findings
        ) {
            this.id = UUID.randomUUID().toString();

            requireText(reviewer, "Reviewer");

            this.reviewer = reviewer;
            this.start = start;
            this.end = end;

            this.findings = new ArrayList<>(findings);
            this.actions = new ArrayList<>();

            this.status = ReviewStatus.UNDER_REVIEW;
            this.decisionNotes = "";
            this.decisionMaker = "";
        }

        void addAction(ReviewAction action) {

            if (status != ReviewStatus.UNDER_REVIEW) {
                throw new ReviewException(
                    "Review is not editable."
                );
            }

            boolean duplicate = actions.stream()
                .anyMatch(existing ->
                    existing.id().equals(action.id())
                );

            if (duplicate) {
                throw new ReviewException(
                    "Duplicate action ID."
                );
            }

            actions.add(action);
        }

        void decide(
            Decision decision,
            String decisionMaker,
            String notes,
            ReviewPolicy policy
        ) {
            if (status != ReviewStatus.UNDER_REVIEW) {
                throw new ReviewException(
                    "Review has already been finalized."
                );
            }

            Objects.requireNonNull(decision);

            requireText(decisionMaker, "Decision maker");
            requireText(notes, "Decision notes");

            boolean critical = findings.stream()
                .anyMatch(risk ->
                    risk.level() == RiskLevel.CRITICAL
                );

            if (
                decision == Decision.APPROVE &&
                policy.blockApprovalOnCriticalRisk() &&
                critical
            ) {
                throw new ReviewException(
                    "Critical resource risks block approval."
                );
            }

            this.status = decision == Decision.APPROVE
                ? ReviewStatus.APPROVED
                : ReviewStatus.REJECTED;

            this.decisionMaker = decisionMaker;
            this.decisionNotes = notes;
        }

        String id() {
            return id;
        }

        ReviewStatus status() {
            return status;
        }

        List<Risk> findings() {
            return List.copyOf(findings);
        }

        List<ReviewAction> actions() {
            return List.copyOf(actions);
        }

        String report() {
            return """
                RESOURCE REVIEW
                Review ID: %s
                Reviewer: %s
                Period: %s to %s
                Status: %s
                Decision Maker: %s
                Decision Notes: %s
                Findings: %d
                Actions: %d
                """.formatted(
                    id,
                    reviewer,
                    start,
                    end,
                    status,
                    decisionMaker,
                    decisionNotes,
                    findings.size(),
                    actions.size()
                );
        }
    }


    // -----------------------------------------------------
    // AUDIT SERVICE
    // -----------------------------------------------------

    static class AuditService {

        private final List<AuditEvent> events =
            new ArrayList<>();

        void record(
            String type,
            String entityId,
            String description
        ) {
            events.add(new AuditEvent(
                UUID.randomUUID().toString(),
                type,
                entityId,
                description,
                LocalDateTime.now()
            ));
        }

        List<AuditEvent> events() {
            return List.copyOf(events);
        }
    }


    // -----------------------------------------------------
    // RESOURCE MANAGEMENT SERVICE
    // -----------------------------------------------------

    static class ResourceService {

        private final Map<String, Employee> employees =
            new HashMap<>();

        private final Map<String, Project> projects =
            new HashMap<>();

        private final Map<String, Allocation> allocations =
            new HashMap<>();

        private final List<LeaveRecord> leaves =
            new ArrayList<>();

        private final Map<String, ResourceReview> reviews =
            new HashMap<>();

        private final AuditService audit;

        private final ReviewPolicy policy;

        ResourceService(
            AuditService audit,
            ReviewPolicy policy
        ) {
            this.audit = Objects.requireNonNull(audit);
            this.policy = Objects.requireNonNull(policy);
        }

        // ---------------------------------------------
        // Employee operations
        // ---------------------------------------------

        void addEmployee(Employee employee) {

            if (employees.putIfAbsent(
                employee.id(),
                employee
            ) != null) {
                throw new ResourceException(
                    "Employee already exists."
                );
            }

            audit.record(
                "EMPLOYEE_CREATED",
                employee.id(),
                employee.name()
            );
        }

        void updateStatus(
            String employeeId,
            EmployeeStatus status
        ) {
            Employee employee = getEmployee(employeeId);

            Employee updated = employee.withStatus(status);

            employees.put(employeeId, updated);

            audit.record(
                "EMPLOYEE_STATUS_CHANGED",
                employeeId,
                status.name()
            );
        }

        // ---------------------------------------------
        // Project operations
        // ---------------------------------------------

        void addProject(Project project) {

            if (projects.putIfAbsent(
                project.id(),
                project
            ) != null) {
                throw new ResourceException(
                    "Project already exists."
                );
            }

            audit.record(
                "PROJECT_CREATED",
                project.id(),
                project.name()
            );
        }

        // ---------------------------------------------
        // Domain retrieval
        // ---------------------------------------------

        private Employee getEmployee(String id) {

            Employee employee = employees.get(id);

            if (employee == null) {
                throw new ResourceException(
                    "Employee not found: " + id
                );
            }

            return employee;
        }

        private Project getProject(String id) {

            Project project = projects.get(id);

            if (project == null) {
                throw new ResourceException(
                    "Project not found: " + id
                );
            }

            return project;
        }

        // ---------------------------------------------
        // Leave operations
        // ---------------------------------------------

        void addLeave(LeaveRecord leave) {

            getEmployee(leave.employeeId());

            leaves.add(leave);

            audit.record(
                "LEAVE_RECORDED",
                leave.employeeId(),
                leave.start() + " to " + leave.end()
            );
        }

        private double unavailableHours(
            String employeeId,
            LocalDate start,
            LocalDate end
        ) {

            double total = leaves.stream()
                .filter(leave ->
                    leave.employeeId().equals(employeeId)
                )
                .filter(leave ->
                    !leave.start().isAfter(end) &&
                    !leave.end().isBefore(start)
                )
                .mapToDouble(LeaveRecord::unavailableHours)
                .sum();

            return Math.min(
                total,
                getEmployee(employeeId).weeklyCapacity()
            );
        }

        // ---------------------------------------------
        // Allocation calculations
        // ---------------------------------------------

        private double allocatedHours(
            String employeeId,
            LocalDate start,
            LocalDate end
        ) {

            return allocations.values().stream()
                .filter(allocation ->
                    allocation.employeeId().equals(employeeId)
                )
                .filter(allocation ->
                    !allocation.start().isAfter(end) &&
                    !allocation.end().isBefore(start)
                )
                .mapToDouble(Allocation::weeklyHours)
                .sum();
        }

        CapacityReport capacity(
            String employeeId,
            LocalDate start,
            LocalDate end
        ) {

            if (start.isAfter(end)) {
                throw new ResourceException(
                    "Invalid capacity period."
                );
            }

            Employee employee = getEmployee(employeeId);

            if (employee.status() != EmployeeStatus.ACTIVE) {
                return new CapacityReport(
                    employeeId,
                    0,
                    0,
                    0,
                    0,
                    false
                );
            }

            double unavailable = unavailableHours(
                employeeId,
                start,
                end
            );

            double effectiveCapacity = Math.max(
                0,
                employee.weeklyCapacity() - unavailable
            );

            double allocated = allocatedHours(
                employeeId,
                start,
                end
            );

            double available = Math.max(
                0,
                effectiveCapacity - allocated
            );

            double utilization = effectiveCapacity > 0
                ? allocated / effectiveCapacity * 100
                : 0;

            return new CapacityReport(
                employeeId,
                effectiveCapacity,
                allocated,
                available,
                utilization,
                allocated > effectiveCapacity
            );
        }

        // ---------------------------------------------
        // Allocation service
        // ---------------------------------------------

        void allocate(Allocation allocation) {

            Employee employee = getEmployee(
                allocation.employeeId()
            );

            Project project = getProject(
                allocation.projectId()
            );

            if (employee.status() != EmployeeStatus.ACTIVE) {
                throw new CapacityException(
                    "Employee is not active."
                );
            }

            if (project.status() != ProjectStatus.ACTIVE) {
                throw new CapacityException(
                    "Project is not active."
                );
            }

            if (allocations.containsKey(allocation.id())) {
                throw new CapacityException(
                    "Allocation already exists."
                );
            }

            CapacityReport report = capacity(
                employee.id(),
                allocation.start(),
                allocation.end()
            );

            if (allocation.weeklyHours() > report.availableHours()) {
                throw new CapacityException(
                    "Allocation exceeds available capacity."
                );
            }

            allocations.put(allocation.id(), allocation);

            audit.record(
                "RESOURCE_ALLOCATED",
                allocation.id(),
                employee.id() + " -> " + project.id()
            );
        }

        // ---------------------------------------------
        // Utilization reporting
        // ---------------------------------------------

        List<CapacityReport> utilizationReport(
            LocalDate start,
            LocalDate end
        ) {

            return employees.values().stream()
                .filter(employee ->
                    employee.status() == EmployeeStatus.ACTIVE
                )
                .map(employee ->
                    capacity(employee.id(), start, end)
                )
                .sorted(
                    Comparator.comparing(
                        CapacityReport::utilization
                    ).reversed()
                )
                .toList();
        }

        // ---------------------------------------------
        // Skill matching
        // ---------------------------------------------

        List<SkillMatch> skillMatch(String projectId) {

            Project project = getProject(projectId);

            return employees.values().stream()
                .filter(employee ->
                    employee.status() == EmployeeStatus.ACTIVE
                )
                .map(employee -> {

                    List<String> missing =
                        project.requiredSkills().entrySet()
                            .stream()
                            .filter(required ->
                                employee.skills().getOrDefault(
                                    required.getKey(), 0
                                ) < required.getValue()
                            )
                            .map(Map.Entry::getKey)
                            .toList();

                    int total = project.requiredSkills().size();

                    double percentage = total == 0
                        ? 100
                        : (total - missing.size()) *
                          100.0 / total;

                    return new SkillMatch(
                        employee.id(),
                        employee.name(),
                        percentage,
                        missing
                    );
                })
                .sorted(
                    Comparator.comparingDouble(
                        SkillMatch::matchPercentage
                    ).reversed()
                )
                .toList();
        }

        // ---------------------------------------------
        // Risk evaluation
        // ---------------------------------------------

        List<Risk> evaluateRisks(
            LocalDate start,
            LocalDate end
        ) {

            return utilizationReport(start, end)
                .stream()
                .map(policy::evaluate)
                .toList();
        }

        // ---------------------------------------------
        // Review lifecycle
        // ---------------------------------------------

        ResourceReview createReview(
            String reviewer,
            LocalDate start,
            LocalDate end
        ) {

            List<Risk> findings = evaluateRisks(start, end)
                .stream()
                .filter(risk ->
                    risk.level() == RiskLevel.HIGH ||
                    risk.level() == RiskLevel.CRITICAL
                )
                .toList();

            ResourceReview review = new ResourceReview(
                reviewer,
                start,
                end,
                findings
            );

            reviews.put(review.id(), review);

            audit.record(
                "REVIEW_CREATED",
                review.id(),
                reviewer
            );

            return review;
        }

        void addReviewAction(
            String reviewId,
            ReviewAction action
        ) {

            ResourceReview review = reviews.get(reviewId);

            if (review == null) {
                throw new ReviewException("Review not found.");
            }

            getEmployee(action.ownerId());

            review.addAction(action);

            audit.record(
                "ACTION_CREATED",
                action.id(),
                reviewId
            );
        }

        void decideReview(
            String reviewId,
            Decision decision,
            String decisionMaker,
            String notes
        ) {

            ResourceReview review = reviews.get(reviewId);

            if (review == null) {
                throw new ReviewException("Review not found.");
            }

            review.decide(
                decision,
                decisionMaker,
                notes,
                policy
            );

            audit.record(
                "REVIEW_DECIDED",
                reviewId,
                decision.name()
            );
        }

        ResourceReview getReview(String id) {

            ResourceReview review = reviews.get(id);

            if (review == null) {
                throw new ReviewException("Review not found.");
            }

            return review;
        }

        List<AuditEvent> auditEvents() {
            return audit.events();
        }
    }


    // -----------------------------------------------------
    // REPORTING SERVICE
    // -----------------------------------------------------

    static class ReportingService {

        static void printUtilization(
            List<CapacityReport> reports
        ) {

            System.out.println("\nRESOURCE UTILIZATION");

            reports.forEach(report ->
                System.out.printf(
                    "%-8s Capacity: %6.2f | Allocated: %6.2f | " +
                    "Available: %6.2f | Utilization: %6.2f%%%n",
                    report.employeeId(),
                    report.effectiveCapacity(),
                    report.allocatedHours(),
                    report.availableHours(),
                    report.utilization()
                )
            );
        }

        static void printSkillMatches(
            List<SkillMatch> matches
        ) {

            System.out.println("\nSKILL MATCHING");

            matches.forEach(match ->
                System.out.printf(
                    "%-8s %-20s Match: %6.2f%% | Gaps: %s%n",
                    match.employeeId(),
                    match.employeeName(),
                    match.matchPercentage(),
                    match.missingSkills()
                )
            );
        }

        static void printRisks(List<Risk> risks) {

            System.out.println("\nRESOURCE RISKS");

            risks.forEach(risk ->
                System.out.println(
                    risk.employeeId() +
                    " | " + risk.level() +
                    " | " + risk.reason()
                )
            );
        }

        static void printAudit(List<AuditEvent> events) {

            System.out.println("\nAUDIT HISTORY");

            events.forEach(event ->
                System.out.println(
                    event.timestamp() +
                    " | " + event.eventType() +
                    " | " + event.entityId() +
                    " | " + event.description()
                )
            );
        }
    }


    // -----------------------------------------------------
    // APPLICATION ENTRY POINT
    // -----------------------------------------------------

    public static void main(String[] args) {

        LocalDate start = LocalDate.of(2026, 11, 1);
        LocalDate end = LocalDate.of(2026, 11, 30);

        AuditService audit = new AuditService();

        ReviewPolicy policy = new ReviewPolicy(
            85,
            95,
            40,
            true
        );

        ResourceService service = new ResourceService(
            audit,
            policy
        );

        try {

            service.addEmployee(new Employee(
                "E101",
                "Aarav Sharma",
                "Engineering",
                "Senior Developer",
                Map.of(
                    "python", 5,
                    "sql", 4,
                    "cloud", 4
                ),
                40,
                EmployeeStatus.ACTIVE
            ));

            service.addEmployee(new Employee(
                "E102",
                "Meera Singh",
                "Engineering",
                "Backend Developer",
                Map.of(
                    "python", 4,
                    "sql", 5,
                    "cloud", 3
                ),
                40,
                EmployeeStatus.ACTIVE
            ));

            service.addEmployee(new Employee(
                "E103",
                "Rohan Verma",
                "Analytics",
                "Data Analyst",
                Map.of(
                    "python", 3,
                    "sql", 4,
                    "analytics", 5
                ),
                40,
                EmployeeStatus.ACTIVE
            ));

            service.addEmployee(new Employee(
                "E104",
                "Ananya Gupta",
                "Engineering",
                "Cloud Engineer",
                Map.of(
                    "cloud", 5,
                    "python", 3,
                    "security", 4
                ),
                40,
                EmployeeStatus.ACTIVE
            ));

            service.addProject(new Project(
                "P101",
                "Enterprise Platform Modernization",
                Map.of(
                    "python", 4,
                    "sql", 4,
                    "cloud", 4
                ),
                5,
                ProjectStatus.ACTIVE
            ));

            service.allocate(new Allocation(
                "A101", "E101", "P101", 35, start, end
            ));

            service.allocate(new Allocation(
                "A102", "E102", "P101", 25, start, end
            ));

            service.allocate(new Allocation(
                "A103", "E103", "P101", 20, start, end
            ));

            service.allocate(new Allocation(
                "A104", "E104", "P101", 30, start, end
            ));

            service.addLeave(new LeaveRecord(
                "E102",
                LocalDate.of(2026, 11, 10),
                LocalDate.of(2026, 11, 14),
                8
            ));

            ReportingService.printUtilization(
                service.utilizationReport(start, end)
            );

            ReportingService.printSkillMatches(
                service.skillMatch("P101")
            );

            ReportingService.printRisks(
                service.evaluateRisks(start, end)
            );

            ResourceReview review = service.createReview(
                "Resource Management Lead",
                start,
                end
            );

            service.addReviewAction(
                review.id(),
                new ReviewAction(
                    "ACT101",
                    "Review engineering capacity distribution",
                    "E101",
                    LocalDate.of(2026, 12, 5),
                    ActionStatus.OPEN
                )
            );

            try {

                service.decideReview(
                    review.id(),
                    Decision.APPROVE,
                    "Department Head",
                    "Resource review approved."
                );

            } catch (ReviewException exception) {

                System.out.println(
                    "\nAPPROVAL BLOCKED: " +
                    exception.getMessage()
                );

                service.decideReview(
                    review.id(),
                    Decision.REJECT,
                    "Department Head",
                    "Critical findings require corrective action."
                );
            }

            System.out.println("\nFINAL REVIEW");
            System.out.println(
                service.getReview(review.id()).report()
            );

            ReportingService.printAudit(
                service.auditEvents()
            );

            // Negative test: allocation beyond available
            // capacity must be rejected.
            try {

                service.allocate(new Allocation(
                    "A999",
                    "E103",
                    "P101",
                    50,
                    start,
                    end
                ));

                throw new ResourceException(
                    "Capacity validation failed."
                );

            } catch (CapacityException exception) {

                System.out.println(
                    "\nCAPACITY VALIDATION: PASSED"
                );

                System.out.println(exception.getMessage());
            }

            // Review decisions are terminal states.
            try {

                service.decideReview(
                    review.id(),
                    Decision.APPROVE,
                    "Department Head",
                    "Second decision."
                );

                throw new ResourceException(
                    "Terminal state validation failed."
                );

            } catch (ReviewException exception) {

                System.out.println(
                    "REVIEW STATE VALIDATION: PASSED"
                );
            }

            System.out.println(
                "\nRESOURCE MANAGEMENT REVIEW COMPLETED"
            );

        } catch (Exception exception) {

            System.err.println(
                "APPLICATION ERROR: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
