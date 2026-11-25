import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Enterprise Risk Register Management System.
 *
 * Java 17 implementation of risk identification, assessment,
 * treatment, residual evaluation, escalation and governance.
 *
 * No external dependencies.
 */
public class RiskRegisterApplication {

    enum Category {
        STRATEGIC,
        OPERATIONAL,
        FINANCIAL,
        TECHNOLOGY,
        CYBERSECURITY,
        COMPLIANCE,
        REPUTATIONAL,
        PROJECT,
        ENVIRONMENTAL
    }

    enum Status {
        IDENTIFIED,
        ASSESSED,
        TREATMENT_PLANNED,
        IN_PROGRESS,
        MONITORING,
        ACCEPTED,
        CLOSED
    }

    enum Response {
        AVOID,
        MITIGATE,
        TRANSFER,
        ACCEPT
    }

    enum Level {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum ReviewType {
        PERIODIC,
        EVENT_DRIVEN,
        POST_INCIDENT
    }

    record RiskAssessment(
        int probability,
        int impact,
        LocalDate assessedOn,
        String assessor
    ) {
        RiskAssessment {
            validateScore(probability, "Probability");
            validateScore(impact, "Impact");
            Objects.requireNonNull(assessedOn);
            requireText(assessor, "Assessor");
        }

        int score() {
            return probability * impact;
        }

        Level level() {
            return classify(score());
        }
    }

    record RiskEvent(
        LocalDateTime timestamp,
        Status previousStatus,
        Status currentStatus,
        String actor,
        String justification
    ) {}

    record RiskReview(
        LocalDate reviewDate,
        ReviewType type,
        String reviewer,
        String findings
    ) {
        RiskReview {
            Objects.requireNonNull(reviewDate);
            Objects.requireNonNull(type);
            requireText(reviewer, "Reviewer");
            requireText(findings, "Findings");
        }
    }

    record GovernancePolicy(
        int minimumTreatmentScore,
        int criticalEscalationScore,
        boolean requireTreatmentPlan,
        boolean requireResidualAssessment,
        boolean permitRiskAcceptance
    ) {
        GovernancePolicy {
            if (minimumTreatmentScore < 1 ||
                minimumTreatmentScore > 25 ||
                criticalEscalationScore < 1 ||
                criticalEscalationScore > 25) {
                throw new IllegalArgumentException(
                    "Invalid governance thresholds."
                );
            }
        }

        static GovernancePolicy enterpriseDefault() {
            return new GovernancePolicy(
                12, 20, true, true, true
            );
        }
    }

    static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(
                field + " is required."
            );
        }
    }

    static void validateScore(int value, String field) {
        if (value < 1 || value > 5) {
            throw new IllegalArgumentException(
                field + " must be between 1 and 5."
            );
        }
    }

    static Level classify(int score) {
        if (score < 1 || score > 25) {
            throw new IllegalArgumentException(
                "Score must be between 1 and 25."
            );
        }

        if (score >= 20) return Level.CRITICAL;
        if (score >= 12) return Level.HIGH;
        if (score >= 6) return Level.MEDIUM;
        return Level.LOW;
    }

    static class Risk {

        private final String id;
        private String title;
        private String description;
        private final Category category;
        private String owner;

        private RiskAssessment inherentAssessment;
        private RiskAssessment residualAssessment;

        private Response response;
        private Status status;

        private String treatmentPlan = "";
        private String treatmentOwner = "";

        private LocalDate targetDate;

        private final Set<String> controls = new HashSet<>();
        private final List<RiskEvent> history = new ArrayList<>();
        private final List<RiskReview> reviews = new ArrayList<>();

        private long version = 1;

        Risk(
            String id,
            String title,
            String description,
            Category category,
            String owner,
            RiskAssessment assessment,
            Response response,
            LocalDate targetDate
        ) {
            requireText(id, "Risk ID");
            requireText(title, "Title");
            requireText(description, "Description");
            requireText(owner, "Owner");

            this.id = id;
            this.title = title;
            this.description = description;
            this.category = Objects.requireNonNull(category);
            this.owner = owner;
            this.inherentAssessment =
                Objects.requireNonNull(assessment);
            this.response = Objects.requireNonNull(response);
            this.status = Status.IDENTIFIED;
            this.targetDate = targetDate;

            if (targetDate != null &&
                targetDate.isBefore(assessment.assessedOn())) {
                throw new IllegalArgumentException(
                    "Target date precedes identification."
                );
            }
        }

        String id() {
            return id;
        }

        String title() {
            return title;
        }

        Category category() {
            return category;
        }

        String owner() {
            return owner;
        }

        Status status() {
            return status;
        }

        Response response() {
            return response;
        }

        int inherentScore() {
            return inherentAssessment.score();
        }

        int residualScore() {
            return residualAssessment == null
                ? -1
                : residualAssessment.score();
        }

        Level inherentLevel() {
            return inherentAssessment.level();
        }

        void setTreatment(
            String plan,
            String responsibleOwner,
            Set<String> implementedControls
        ) {
            requireText(plan, "Treatment plan");
            requireText(responsibleOwner, "Treatment owner");

            this.treatmentPlan = plan;
            this.treatmentOwner = responsibleOwner;

            controls.clear();
            controls.addAll(implementedControls);

            version++;
        }

        void reassess(
            RiskAssessment assessment,
            boolean residual
        ) {
            Objects.requireNonNull(assessment);

            if (status == Status.CLOSED) {
                throw new IllegalStateException(
                    "Closed risks cannot be reassessed."
                );
            }

            if (residual) {
                residualAssessment = assessment;
            } else {
                inherentAssessment = assessment;
            }

            version++;
        }

        void changeStatus(
            Status next,
            String actor,
            String justification
        ) {
            requireText(actor, "Actor");

            if (!allowedTransition(status, next)) {
                throw new IllegalStateException(
                    "Invalid transition: " + status + " -> " + next
                );
            }

            if ((next == Status.ACCEPTED ||
                 next == Status.CLOSED) &&
                (justification == null || justification.isBlank())) {
                throw new IllegalArgumentException(
                    "Justification is mandatory."
                );
            }

            Status previous = status;
            status = next;
            version++;

            history.add(new RiskEvent(
                LocalDateTime.now(),
                previous,
                next,
                actor,
                justification == null ? "" : justification
            ));
        }

        void addReview(RiskReview review) {
            reviews.add(Objects.requireNonNull(review));
            version++;
        }

        private static boolean allowedTransition(
            Status current,
            Status next
        ) {
            return switch (current) {
                case IDENTIFIED ->
                    next == Status.ASSESSED ||
                    next == Status.CLOSED;

                case ASSESSED ->
                    next == Status.TREATMENT_PLANNED ||
                    next == Status.ACCEPTED ||
                    next == Status.CLOSED;

                case TREATMENT_PLANNED ->
                    next == Status.IN_PROGRESS ||
                    next == Status.ACCEPTED ||
                    next == Status.CLOSED;

                case IN_PROGRESS ->
                    next == Status.MONITORING ||
                    next == Status.TREATMENT_PLANNED ||
                    next == Status.CLOSED;

                case MONITORING ->
                    next == Status.IN_PROGRESS ||
                    next == Status.ACCEPTED ||
                    next == Status.CLOSED;

                case ACCEPTED ->
                    next == Status.MONITORING ||
                    next == Status.CLOSED;

                case CLOSED ->
                    next == Status.IDENTIFIED;
            };
        }

        @Override
        public String toString() {
            return String.format(
                "%s | %-30s | %2d | %-8s | %-20s | %s",
                id,
                title.length() > 30
                    ? title.substring(0, 30)
                    : title,
                inherentScore(),
                inherentLevel(),
                status,
                owner
            );
        }
    }

    record Evaluation(
        String riskId,
        boolean eligible,
        List<String> blockers
    ) {
        Evaluation {
            blockers = List.copyOf(blockers);
        }
    }

    static class RiskNotFoundException
        extends RuntimeException {

        RiskNotFoundException(String id) {
            super("Risk not found: " + id);
        }
    }

    interface RiskRepository {
        void save(Risk risk);
        Risk findById(String id);
        List<Risk> findAll();
    }

    static class InMemoryRiskRepository
        implements RiskRepository {

        private final Map<String, Risk> storage =
            new HashMap<>();

        @Override
        public void save(Risk risk) {
            Objects.requireNonNull(risk);
            storage.put(risk.id(), risk);
        }

        @Override
        public Risk findById(String id) {
            Risk risk = storage.get(id);

            if (risk == null) {
                throw new RiskNotFoundException(id);
            }

            return risk;
        }

        @Override
        public List<Risk> findAll() {
            return new ArrayList<>(storage.values());
        }
    }

    static class RiskGovernanceService {

        private final RiskRepository repository;
        private final GovernancePolicy policy;

        RiskGovernanceService(
            RiskRepository repository,
            GovernancePolicy policy
        ) {
            this.repository = Objects.requireNonNull(repository);
            this.policy = Objects.requireNonNull(policy);
        }

        void register(Risk risk) {
            if (repository.findAll().stream()
                .anyMatch(existing ->
                    existing.id().equals(risk.id()))) {
                throw new IllegalArgumentException(
                    "Duplicate risk ID: " + risk.id()
                );
            }

            repository.save(risk);
        }

        Evaluation evaluate(String id) {
            Risk risk = repository.findById(id);
            List<String> blockers = new ArrayList<>();

            if (risk.inherentScore() >=
                policy.criticalEscalationScore()) {
                blockers.add(
                    "Critical exposure requires management escalation."
                );
            }

            if (risk.inherentScore() >=
                    policy.minimumTreatmentScore() &&
                risk.response() == Response.MITIGATE &&
                policy.requireTreatmentPlan() &&
                risk.treatmentPlan.isBlank()) {
                blockers.add(
                    "Approved treatment plan is missing."
                );
            }

            if (risk.response() == Response.ACCEPT &&
                (!policy.permitRiskAcceptance() ||
                 risk.status() != Status.ACCEPTED)) {
                blockers.add(
                    "Formal risk acceptance is required or prohibited."
                );
            }

            if (risk.status() == Status.MONITORING &&
                risk.response() == Response.MITIGATE &&
                policy.requireResidualAssessment() &&
                risk.residualScore() < 0) {
                blockers.add(
                    "Residual assessment is missing."
                );
            }

            return new Evaluation(
                id,
                blockers.isEmpty(),
                blockers
            );
        }

        List<Risk> prioritise() {
            return repository.findAll().stream()
                .filter(r -> r.status() != Status.CLOSED)
                .sorted(
                    Comparator.comparingInt(Risk::inherentScore)
                        .reversed()
                        .thenComparing(Risk::id)
                )
                .collect(Collectors.toList());
        }

        Map<Level, Long> distribution() {
            Map<Level, Long> result =
                new EnumMap<>(Level.class);

            for (Level level : Level.values()) {
                result.put(level, 0L);
            }

            repository.findAll().stream()
                .collect(Collectors.groupingBy(
                    Risk::inherentLevel,
                    Collectors.counting()
                ))
                .forEach(result::put);

            return Collections.unmodifiableMap(result);
        }

        double averageInherentScore() {
            return repository.findAll().stream()
                .mapToInt(Risk::inherentScore)
                .average()
                .orElse(0.0);
        }

        List<Risk> overdueRisks(LocalDate today) {
            return repository.findAll().stream()
                .filter(r -> r.status() != Status.CLOSED)
                .filter(r -> r.targetDate != null)
                .filter(r -> r.targetDate.isBefore(today))
                .collect(Collectors.toList());
        }
    }

    public static void main(String[] args) {

        RiskRepository repository =
            new InMemoryRiskRepository();

        RiskGovernanceService service =
            new RiskGovernanceService(
                repository,
                GovernancePolicy.enterpriseDefault()
            );

        LocalDate today = LocalDate.now();

        Risk cyberRisk = new Risk(
            "R-001",
            "Ransomware attack",
            "Encryption of critical enterprise systems.",
            Category.CYBERSECURITY,
            "Chief Information Security Officer",
            new RiskAssessment(4, 5, today, "Security Analyst"),
            Response.MITIGATE,
            today.plusDays(30)
        );

        Risk operationalRisk = new Risk(
            "R-002",
            "Supplier disruption",
            "Failure of a critical infrastructure supplier.",
            Category.OPERATIONAL,
            "Procurement Manager",
            new RiskAssessment(3, 4, today, "Risk Analyst"),
            Response.MITIGATE,
            today.plusDays(45)
        );

        Risk financialRisk = new Risk(
            "R-003",
            "Budget overrun",
            "Unplanned project costs may exceed the approved budget.",
            Category.FINANCIAL,
            "Finance Controller",
            new RiskAssessment(3, 3, today, "Finance Analyst"),
            Response.TRANSFER,
            today.plusDays(60)
        );

        service.register(cyberRisk);
        service.register(operationalRisk);
        service.register(financialRisk);

        cyberRisk.setTreatment(
            "Deploy endpoint detection, MFA and immutable backups.",
            "Security Operations Manager",
            Set.of("EDR", "MFA", "Immutable Backups")
        );

        cyberRisk.changeStatus(
            Status.ASSESSED,
            "Risk Analyst",
            "Initial assessment completed."
        );

        cyberRisk.changeStatus(
            Status.TREATMENT_PLANNED,
            "Security Director",
            "Treatment approved."
        );

        cyberRisk.changeStatus(
            Status.IN_PROGRESS,
            "Security Operations Manager",
            "Control implementation initiated."
        );

        cyberRisk.reassess(
            new RiskAssessment(
                2, 3, today, "Security Assessor"
            ),
            true
        );

        cyberRisk.changeStatus(
            Status.MONITORING,
            "Security Director",
            "Controls implemented; monitoring effectiveness."
        );

        cyberRisk.addReview(new RiskReview(
            today,
            ReviewType.PERIODIC,
            "Internal Risk Reviewer",
            "Residual exposure reduced to an acceptable monitoring level."
        ));

        System.out.println("\nENTERPRISE RISK REGISTER");
        System.out.println("-".repeat(115));

        service.prioritise().forEach(System.out::println);

        System.out.println("\nGOVERNANCE EVALUATION");

        for (String id : List.of("R-001", "R-002", "R-003")) {
            Evaluation result = service.evaluate(id);

            System.out.println(
                id + ": " +
                (result.eligible() ? "ELIGIBLE" : "BLOCKED")
            );

            result.blockers().forEach(
                blocker -> System.out.println("  - " + blocker)
            );
        }

        System.out.println("\nRISK DISTRIBUTION");
        service.distribution().forEach(
            (level, count) ->
                System.out.println(level + ": " + count)
        );

        System.out.printf(
            "\nAverage inherent risk score: %.2f%n",
            service.averageInherentScore()
        );

        System.out.println(
            "Overdue risks: " +
            service.overdueRisks(today).size()
        );

        // Demonstrate input validation.
        try {
            new RiskAssessment(
                7, 3, today, "Invalid Assessor"
            );
        } catch (IllegalArgumentException exception) {
            System.out.println(
                "\nExpected validation error: " +
                exception.getMessage()
            );
        }

        // Demonstrate missing risk handling.
        try {
            repository.findById("R-999");
        } catch (RiskNotFoundException exception) {
            System.out.println(exception.getMessage());
        }
    }
}
