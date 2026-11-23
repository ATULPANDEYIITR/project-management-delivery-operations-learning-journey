import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

/*
 * JAVA 17 ENTERPRISE PROJECT RISK MANAGEMENT
 *
 * Features:
 * - Immutable risk assessment records
 * - Enterprise risk ownership
 * - Assessment and approval workflow
 * - Risk ranking and exposure aggregation
 * - Mitigation budget allocation
 * - Explicit state transition policies
 */

public class RiskPrioritization {

    enum Category {
        TECHNICAL,
        SECURITY,
        FINANCIAL,
        OPERATIONAL,
        SCHEDULE,
        LEGAL,
        RESOURCE,
        EXTERNAL
    }

    enum Status {
        IDENTIFIED,
        ASSESSED,
        MITIGATING,
        MONITORING,
        CLOSED
    }

    enum Priority {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    record Assessment(
        int probability,
        int impact,
        int urgency,
        int detectability,
        int mitigationEffectiveness
    ) {
        Assessment {
            validateRating(probability, "Probability");
            validateRating(impact, "Impact");
            validateRating(urgency, "Urgency");
            validateRating(detectability, "Detectability");
            validateRating(
                mitigationEffectiveness,
                "Mitigation effectiveness"
            );
        }

        private static void validateRating(
            int value,
            String name
        ) {
            if (value < 1 || value > 5) {
                throw new IllegalArgumentException(
                    name + " must be between 1 and 5."
                );
            }
        }

        double inherentScore() {
            return probability * impact * urgency;
        }

        double residualScore() {
            double detectionFactor =
                0.8 + (detectability - 1) * 0.1;

            double mitigationFactor =
                1 - mitigationEffectiveness * 0.12;

            return Math.round(
                inherentScore() *
                detectionFactor *
                mitigationFactor * 100
            ) / 100.0;
        }

        Priority priority() {
            double score = residualScore();

            if (score >= 60) return Priority.CRITICAL;
            if (score >= 35) return Priority.HIGH;
            if (score >= 15) return Priority.MEDIUM;

            return Priority.LOW;
        }
    }

    record Risk(
        String id,
        String title,
        Category category,
        Assessment assessment,
        String owner,
        LocalDate deadline,
        double mitigationCost,
        Status status
    ) {
        Risk {
            if (id == null || id.isBlank()) {
                throw new IllegalArgumentException(
                    "Risk ID is required."
                );
            }

            if (title == null || title.isBlank()) {
                throw new IllegalArgumentException(
                    "Risk title is required."
                );
            }

            Objects.requireNonNull(category);
            Objects.requireNonNull(assessment);
            Objects.requireNonNull(deadline);
            Objects.requireNonNull(status);

            if (owner == null || owner.isBlank()) {
                throw new IllegalArgumentException(
                    "Risk owner is required."
                );
            }

            if (!Double.isFinite(mitigationCost) ||
                mitigationCost < 0) {
                throw new IllegalArgumentException(
                    "Invalid mitigation cost."
                );
            }
        }

        double residualScore() {
            return assessment.residualScore();
        }

        Priority priority() {
            return assessment.priority();
        }

        double inherentScore() {
            return assessment.inherentScore();
        }

        Risk withStatus(Status newStatus) {
            return new Risk(
                id, title, category, assessment,
                owner, deadline, mitigationCost, newStatus
            );
        }

        Risk withAssessment(Assessment newAssessment) {
            return new Risk(
                id, title, category, newAssessment,
                owner, deadline, mitigationCost, status
            );
        }
    }

    record MitigationAllocation(
        String riskId,
        double requestedCost,
        boolean funded,
        double remainingBudget
    ) {}

    record RiskReport(
        int activeRisks,
        Map<Priority, Long> priorityDistribution,
        Map<Category, Double> categoryExposure,
        List<Risk> rankedRisks
    ) {}

    static class RiskManagementException
        extends RuntimeException {

        RiskManagementException(String message) {
            super(message);
        }
    }

    interface RiskPolicy {
        boolean isValidTransition(Status current, Status next);

        boolean requiresImmediateAction(Risk risk);
    }

    static class EnterpriseRiskPolicy implements RiskPolicy {

        private final Map<Status, Set<Status>> transitions =
            new EnumMap<>(Status.class);

        EnterpriseRiskPolicy() {
            transitions.put(
                Status.IDENTIFIED,
                Set.of(Status.ASSESSED, Status.CLOSED)
            );

            transitions.put(
                Status.ASSESSED,
                Set.of(
                    Status.MITIGATING,
                    Status.MONITORING,
                    Status.CLOSED
                )
            );

            transitions.put(
                Status.MITIGATING,
                Set.of(
                    Status.MONITORING,
                    Status.ASSESSED,
                    Status.CLOSED
                )
            );

            transitions.put(
                Status.MONITORING,
                Set.of(Status.MITIGATING, Status.CLOSED)
            );

            transitions.put(Status.CLOSED, Set.of());
        }

        @Override
        public boolean isValidTransition(
            Status current,
            Status next
        ) {
            return transitions
                .getOrDefault(current, Set.of())
                .contains(next);
        }

        @Override
        public boolean requiresImmediateAction(Risk risk) {
            return risk.status() != Status.CLOSED &&
                (risk.priority() == Priority.CRITICAL ||
                 risk.priority() == Priority.HIGH);
        }
    }

    static class RiskManagementService {

        private final Map<String, Risk> register =
            new HashMap<>();

        private final RiskPolicy policy;

        RiskManagementService(RiskPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        public void registerRisk(Risk risk) {
            Objects.requireNonNull(risk);

            if (register.containsKey(risk.id())) {
                throw new RiskManagementException(
                    "Duplicate risk ID: " + risk.id()
                );
            }

            register.put(risk.id(), risk);
        }

        public Risk getRisk(String id) {
            Risk risk = register.get(id);

            if (risk == null) {
                throw new RiskManagementException(
                    "Risk not found: " + id
                );
            }

            return risk;
        }

        public void updateAssessment(
            String id,
            Assessment assessment
        ) {
            Risk current = getRisk(id);

            if (current.status() == Status.CLOSED) {
                throw new RiskManagementException(
                    "Closed risks cannot be reassessed."
                );
            }

            Risk updated = current.withAssessment(assessment);

            // Replace only after all validation succeeds.
            register.put(id, updated);
        }

        public void transition(
            String id,
            Status next
        ) {
            Risk current = getRisk(id);

            if (!policy.isValidTransition(current.status(), next)) {
                throw new RiskManagementException(
                    "Invalid transition: " +
                    current.status() + " -> " + next
                );
            }

            register.put(id, current.withStatus(next));
        }

        public List<Risk> rankRisks() {
            return register.values()
                .stream()
                .filter(risk -> risk.status() != Status.CLOSED)
                .sorted(
                    Comparator
                        .comparingDouble(Risk::residualScore)
                        .reversed()
                        .thenComparing(
                            Comparator.comparingDouble(
                                Risk::inherentScore
                            ).reversed()
                        )
                        .thenComparing(Risk::deadline)
                        .thenComparing(Risk::id)
                )
                .toList();
        }

        public List<Risk> immediateActionRisks() {
            return rankRisks()
                .stream()
                .filter(policy::requiresImmediateAction)
                .toList();
        }

        public Map<Category, Double> categoryExposure() {
            Map<Category, Double> result =
                new EnumMap<>(Category.class);

            for (Risk risk : rankRisks()) {
                result.merge(
                    risk.category(),
                    risk.residualScore(),
                    Double::sum
                );
            }

            return result;
        }

        public Map<Priority, Long> priorityDistribution() {
            Map<Priority, Long> result =
                new EnumMap<>(Priority.class);

            for (Priority priority : Priority.values()) {
                result.put(priority, 0L);
            }

            rankRisks().stream()
                .collect(Collectors.groupingBy(
                    Risk::priority,
                    Collectors.counting()
                ))
                .forEach(result::put);

            return result;
        }

        public List<MitigationAllocation> allocateBudget(
            double budget
        ) {
            if (!Double.isFinite(budget) || budget < 0) {
                throw new IllegalArgumentException(
                    "Budget must be non-negative."
                );
            }

            double remaining = budget;

            List<MitigationAllocation> allocations =
                new ArrayList<>();

            for (Risk risk : immediateActionRisks()) {
                boolean funded =
                    risk.mitigationCost() <= remaining;

                if (funded) {
                    remaining -= risk.mitigationCost();
                }

                allocations.add(
                    new MitigationAllocation(
                        risk.id(),
                        risk.mitigationCost(),
                        funded,
                        remaining
                    )
                );
            }

            return List.copyOf(allocations);
        }

        public RiskReport generateReport() {
            List<Risk> ranked = rankRisks();

            return new RiskReport(
                ranked.size(),
                priorityDistribution(),
                Map.copyOf(categoryExposure()),
                List.copyOf(ranked)
            );
        }

        public int totalRegisteredRisks() {
            return register.size();
        }
    }

    private static Assessment assessment(
        int probability,
        int impact,
        int urgency,
        int detectability,
        int mitigation
    ) {
        return new Assessment(
            probability,
            impact,
            urgency,
            detectability,
            mitigation
        );
    }

    private static Risk createRisk(
        String id,
        String title,
        Category category,
        int probability,
        int impact,
        int urgency,
        int detectability,
        int mitigation,
        String owner,
        int deadlineDays,
        double cost
    ) {
        return new Risk(
            id,
            title,
            category,
            assessment(
                probability,
                impact,
                urgency,
                detectability,
                mitigation
            ),
            owner,
            LocalDate.now().plusDays(deadlineDays),
            cost,
            Status.ASSESSED
        );
    }

    private static void runTests() {
        Assessment test = assessment(5, 5, 5, 5, 1);

        if (test.inherentScore() != 125 ||
            test.residualScore() != 112.5 ||
            test.priority() != Priority.CRITICAL) {
            throw new AssertionError(
                "Assessment calculation failed."
            );
        }

        RiskManagementService service =
            new RiskManagementService(
                new EnterpriseRiskPolicy()
            );

        Risk risk = createRisk(
            "TEST01", "Security incident",
            Category.SECURITY,
            5, 5, 5, 5, 1,
            "Security Lead", 5, 50000
        );

        service.registerRisk(risk);

        try {
            service.registerRisk(risk);
            throw new AssertionError(
                "Duplicate risk was accepted."
            );
        } catch (RiskManagementException expected) {
            // Expected duplicate rejection.
        }

        service.transition("TEST01", Status.MITIGATING);

        try {
            service.transition("TEST01", Status.ASSESSED);
            throw new AssertionError(
                "Invalid state transition was accepted."
            );
        } catch (RiskManagementException expected) {
            // Expected transition rejection.
        }

        System.out.println("Java 17 validation tests passed.");
    }

    private static void displayReport(
        RiskManagementService service
    ) {
        RiskReport report = service.generateReport();

        System.out.println(
            "\nENTERPRISE PROJECT RISK REGISTER"
        );

        System.out.printf(
            "%-9s %-30s %-13s %10s %-10s %-20s%n",
            "ID", "Risk", "Category",
            "Score", "Priority", "Owner"
        );

        System.out.println("-".repeat(105));

        for (Risk risk : report.rankedRisks()) {
            System.out.printf(
                "%-9s %-30s %-13s %10.2f %-10s %-20s%n",
                risk.id(),
                risk.title(),
                risk.category(),
                risk.residualScore(),
                risk.priority(),
                risk.owner()
            );
        }

        System.out.println("\nPRIORITY DISTRIBUTION");

        report.priorityDistribution().forEach(
            (priority, count) ->
                System.out.println(priority + ": " + count)
        );

        System.out.println("\nCATEGORY EXPOSURE");

        report.categoryExposure().forEach(
            (category, exposure) ->
                System.out.printf(
                    "%s: %.2f%n",
                    category,
                    exposure
                )
        );
    }

    public static void main(String[] args) {
        runTests();

        RiskManagementService service =
            new RiskManagementService(
                new EnterpriseRiskPolicy()
            );

        List<Risk> samples = List.of(
            createRisk(
                "R001", "Cybersecurity breach",
                Category.SECURITY,
                5, 5, 5, 5, 1,
                "Security Lead", 5, 150000
            ),
            createRisk(
                "R002", "Cloud migration failure",
                Category.TECHNICAL,
                4, 5, 4, 3, 2,
                "Cloud Architect", 12, 80000
            ),
            createRisk(
                "R003", "Budget overrun",
                Category.FINANCIAL,
                4, 4, 4, 2, 3,
                "Finance Lead", 20, 30000
            ),
            createRisk(
                "R004", "Vendor delivery delay",
                Category.SCHEDULE,
                3, 3, 2, 2, 4,
                "Project Manager", 40, 10000
            ),
            createRisk(
                "R005", "Regulatory non-compliance",
                Category.LEGAL,
                3, 5, 5, 4, 1,
                "Compliance Officer", 7, 45000
            )
        );

        samples.forEach(service::registerRisk);

        service.updateAssessment(
            "R003",
            assessment(5, 4, 5, 2, 3)
        );

        displayReport(service);

        System.out.println("\nMITIGATION ALLOCATION");

        service.allocateBudget(100000).forEach(
            allocation -> System.out.println(
                allocation.riskId() +
                " | Cost: " + allocation.requestedCost() +
                " | Funded: " + allocation.funded() +
                " | Remaining: " + allocation.remainingBudget()
            )
        );
    }
}
