import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/*
 * Enterprise Team Motivation Management System
 *
 * Java 17 implementation.
 *
 * Features:
 * - Immutable employee records
 * - Motivation assessment
 * - Self-determination theory
 * - Recognition management
 * - Goal tracking
 * - Workload risk detection
 * - Motivation intervention policies
 * - Enterprise reporting
 * - Explicit state validation
 */

public class TeamMotivationSystem {

    enum MotivationLevel {
        HIGH,
        MODERATE,
        LOW,
        CRITICAL
    }

    enum GoalStatus {
        NOT_STARTED,
        IN_PROGRESS,
        COMPLETED,
        BLOCKED
    }

    enum RecognitionType {
        PUBLIC,
        PRIVATE,
        DEVELOPMENT,
        FINANCIAL,
        TEAM
    }

    static class ValidationException extends RuntimeException {
        ValidationException(String message) {
            super(message);
        }
    }

    static void validateScore(double value, String field) {
        if (!Double.isFinite(value) || value < 0 || value > 100) {
            throw new ValidationException(
                field + " must be between 0 and 100."
            );
        }
    }

    record Employee(
        int id,
        String name,
        String department,
        String role,
        double autonomy,
        double competence,
        double relatedness,
        double workload,
        double psychologicalSafety,
        double engagement,
        double intrinsicMotivation,
        double extrinsicMotivation
    ) {

        Employee {
            if (id <= 0) {
                throw new ValidationException(
                    "Employee ID must be positive."
                );
            }

            Objects.requireNonNull(name);
            Objects.requireNonNull(department);
            Objects.requireNonNull(role);

            if (
                name.isBlank() ||
                department.isBlank() ||
                role.isBlank()
            ) {
                throw new ValidationException(
                    "Employee details cannot be empty."
                );
            }

            validateScore(autonomy, "Autonomy");
            validateScore(competence, "Competence");
            validateScore(relatedness, "Relatedness");
            validateScore(workload, "Workload");

            validateScore(
                psychologicalSafety,
                "Psychological safety"
            );

            validateScore(engagement, "Engagement");

            validateScore(
                intrinsicMotivation,
                "Intrinsic motivation"
            );

            validateScore(
                extrinsicMotivation,
                "Extrinsic motivation"
            );
        }
    }

    record Goal(
        int id,
        int ownerId,
        String description,
        double target,
        double progress,
        GoalStatus status
    ) {

        Goal {
            if (id <= 0 || ownerId <= 0) {
                throw new ValidationException("Invalid goal IDs.");
            }

            if (
                description == null ||
                description.isBlank()
            ) {
                throw new ValidationException(
                    "Goal description is required."
                );
            }

            if (
                !Double.isFinite(target) ||
                target <= 0 ||
                !Double.isFinite(progress) ||
                progress < 0 ||
                progress > target
            ) {
                throw new ValidationException(
                    "Invalid goal measurements."
                );
            }

            Objects.requireNonNull(status);
        }

        Goal update(double newProgress) {

            if (
                !Double.isFinite(newProgress) ||
                newProgress < 0 ||
                newProgress > target
            ) {
                throw new ValidationException(
                    "Progress must be between zero and target."
                );
            }

            GoalStatus newStatus =
                newProgress == target
                    ? GoalStatus.COMPLETED
                    : newProgress > 0
                        ? GoalStatus.IN_PROGRESS
                        : GoalStatus.NOT_STARTED;

            return new Goal(
                id,
                ownerId,
                description,
                target,
                newProgress,
                newStatus
            );
        }
    }

    record Recognition(
        int id,
        int employeeId,
        RecognitionType type,
        String reason,
        Instant awardedAt
    ) {

        Recognition {
            if (id <= 0 || employeeId <= 0) {
                throw new ValidationException(
                    "Invalid recognition identifiers."
                );
            }

            Objects.requireNonNull(type);
            Objects.requireNonNull(awardedAt);

            if (reason == null || reason.isBlank()) {
                throw new ValidationException(
                    "Recognition reason is required."
                );
            }
        }
    }

    record MotivationAssessment(
        int employeeId,
        String employeeName,
        double score,
        MotivationLevel level,
        List<String> risks,
        List<String> actions
    ) {

        MotivationAssessment {
            risks = List.copyOf(risks);
            actions = List.copyOf(actions);
        }
    }

    interface MotivationPolicy {
        double calculate(Employee employee);
    }

    static class WeightedMotivationPolicy
        implements MotivationPolicy {

        @Override
        public double calculate(Employee employee) {

            /*
             * The score is a management indicator,
             * not a validated psychological diagnosis.
             */
            return (
                employee.autonomy() * 0.18
                + employee.competence() * 0.18
                + employee.relatedness() * 0.16
                + employee.psychologicalSafety() * 0.16
                + employee.engagement() * 0.14
                + employee.intrinsicMotivation() * 0.12
                + (100 - employee.workload()) * 0.06
            );
        }
    }

    static class MotivationService {

        private final Map<Integer, Employee> employees =
            new java.util.LinkedHashMap<>();

        private final Map<Integer, Goal> goals =
            new java.util.LinkedHashMap<>();

        private final List<Recognition> recognitions =
            new ArrayList<>();

        private final MotivationPolicy policy;

        MotivationService(MotivationPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void registerEmployee(Employee employee) {

            Objects.requireNonNull(employee);

            if (employees.containsKey(employee.id())) {
                throw new ValidationException(
                    "Employee already registered."
                );
            }

            employees.put(employee.id(), employee);
        }

        void createGoal(Goal goal) {

            Objects.requireNonNull(goal);

            if (goals.containsKey(goal.id())) {
                throw new ValidationException(
                    "Goal already exists."
                );
            }

            if (!employees.containsKey(goal.ownerId())) {
                throw new ValidationException(
                    "Goal owner does not exist."
                );
            }

            goals.put(goal.id(), goal);
        }

        void updateGoal(int goalId, double progress) {

            Goal current = goals.get(goalId);

            if (current == null) {
                throw new ValidationException("Goal not found.");
            }

            goals.put(goalId, current.update(progress));
        }

        void recognize(
            int employeeId,
            RecognitionType type,
            String reason
        ) {

            if (!employees.containsKey(employeeId)) {
                throw new ValidationException(
                    "Unknown recognition recipient."
                );
            }

            Recognition recognition = new Recognition(
                recognitions.size() + 1,
                employeeId,
                type,
                reason,
                Instant.now()
            );

            recognitions.add(recognition);
        }

        private Employee getEmployee(int id) {

            Employee employee = employees.get(id);

            if (employee == null) {
                throw new ValidationException(
                    "Employee not found: " + id
                );
            }

            return employee;
        }

        private MotivationLevel classify(double score) {

            if (score >= 80) return MotivationLevel.HIGH;
            if (score >= 65) return MotivationLevel.MODERATE;
            if (score >= 45) return MotivationLevel.LOW;

            return MotivationLevel.CRITICAL;
        }

        MotivationAssessment assess(int employeeId) {

            Employee e = getEmployee(employeeId);

            double score = Math.max(
                0,
                Math.min(100, policy.calculate(e))
            );

            List<String> risks = new ArrayList<>();
            List<String> actions = new ArrayList<>();

            if (e.workload() >= 85) {
                risks.add("High workload and burnout risk");
            }

            if (e.autonomy() < 40) {
                risks.add("Limited decision-making authority");
            }

            if (e.competence() < 40) {
                risks.add("Insufficient development support");
            }

            if (e.relatedness() < 40) {
                risks.add("Weak team relationships");
            }

            if (e.psychologicalSafety() < 40) {
                risks.add("Low psychological safety");
            }

            if (e.engagement() < 40) {
                risks.add("Low employee engagement");
            }

            if (e.workload() > 70) {
                actions.add(
                    "Review workload allocation and priorities."
                );
            }

            if (e.autonomy() < 60) {
                actions.add(
                    "Increase ownership and decision authority."
                );
            }

            if (e.competence() < 60) {
                actions.add(
                    "Provide targeted training and mentoring."
                );
            }

            if (e.relatedness() < 60) {
                actions.add(
                    "Strengthen collaboration and team relationships."
                );
            }

            if (e.psychologicalSafety() < 60) {
                actions.add(
                    "Improve communication and feedback practices."
                );
            }

            if (e.engagement() < 60) {
                actions.add(
                    "Arrange an individual engagement discussion."
                );
            }

            if (actions.isEmpty()) {
                actions.add(
                    "Maintain current development and engagement practices."
                );
            }

            return new MotivationAssessment(
                e.id(),
                e.name(),
                score,
                classify(score),
                risks,
                actions
            );
        }

        List<MotivationAssessment> assessAll() {

            return employees.keySet()
                .stream()
                .map(this::assess)
                .collect(Collectors.toUnmodifiableList());
        }

        void printEnterpriseReport() {

            if (employees.isEmpty()) {
                throw new ValidationException(
                    "Cannot report on an empty team."
                );
            }

            List<MotivationAssessment> assessments =
                assessAll();

            double average = assessments.stream()
                .mapToDouble(MotivationAssessment::score)
                .average()
                .orElseThrow();

            Map<MotivationLevel, Long> distribution =
                assessments.stream()
                    .collect(Collectors.groupingBy(
                        MotivationAssessment::level,
                        () -> new EnumMap<>(
                            MotivationLevel.class
                        ),
                        Collectors.counting()
                    ));

            System.out.println("\nENTERPRISE TEAM REPORT");

            System.out.println(
                "Employees: " + assessments.size()
            );

            System.out.printf(
                "Average motivation: %.2f%n",
                average
            );

            System.out.println(
                "\nMOTIVATION DISTRIBUTION"
            );

            for (MotivationLevel level : MotivationLevel.values()) {
                System.out.println(
                    level + ": " +
                    distribution.getOrDefault(level, 0L)
                );
            }

            System.out.println("\nINDIVIDUAL ASSESSMENTS");

            for (MotivationAssessment a : assessments) {

                System.out.println("\nEmployee: " + a.employeeName());

                System.out.printf(
                    "Score: %.2f%n",
                    a.score()
                );

                System.out.println("Level: " + a.level());

                System.out.println("Risks: " + a.risks());

                System.out.println(
                    "Recommended actions: " + a.actions()
                );
            }

            System.out.println("\nGOAL STATUS");

            goals.values().forEach(goal ->
                System.out.println(
                    goal.description() + " | " +
                    goal.progress() + "/" +
                    goal.target() + " | " +
                    goal.status()
                )
            );

            System.out.println(
                "\nRecognition records: " +
                recognitions.size()
            );
        }
    }

    public static void main(String[] args) {

        try {

            MotivationService service =
                new MotivationService(
                    new WeightedMotivationPolicy()
                );

            service.registerEmployee(
                new Employee(
                    1,
                    "Ananya",
                    "Engineering",
                    "Developer",
                    85, 90, 80, 55,
                    90, 88, 90, 65
                )
            );

            service.registerEmployee(
                new Employee(
                    2,
                    "Rahul",
                    "Analytics",
                    "Business Analyst",
                    35, 55, 45, 90,
                    40, 38, 45, 70
                )
            );

            service.registerEmployee(
                new Employee(
                    3,
                    "Priya",
                    "Management",
                    "Project Manager",
                    75, 80, 85, 65,
                    85, 78, 80, 75
                )
            );

            service.createGoal(
                new Goal(
                    101,
                    1,
                    "Complete quarterly product release",
                    100,
                    0,
                    GoalStatus.NOT_STARTED
                )
            );

            service.updateGoal(101, 65);

            service.recognize(
                1,
                RecognitionType.PUBLIC,
                "Resolved a critical production issue."
            );

            service.recognize(
                3,
                RecognitionType.DEVELOPMENT,
                "Successfully coordinated project delivery."
            );

            service.printEnterpriseReport();

            System.out.println("\nVALIDATION EXAMPLE");

            try {

                service.registerEmployee(
                    new Employee(
                        4,
                        "Test",
                        "Engineering",
                        "Intern",
                        120, 50, 50, 50,
                        50, 50, 50, 50
                    )
                );

            } catch (ValidationException error) {
                System.out.println(error.getMessage());
            }

        } catch (RuntimeException error) {

            System.err.println(
                "Enterprise service error: " +
                error.getMessage()
            );

            System.exit(1);
        }
    }
}
