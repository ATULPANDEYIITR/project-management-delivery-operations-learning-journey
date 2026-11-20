import java.time.LocalDateTime;
import java.util.ArrayList;
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
 * PROJECT RISK MANAGEMENT
 *
 * Enterprise project risk management and governance application.
 *
 * Java: 17
 * Dependencies: Java standard library only.
 *
 * Features:
 * - Risk register
 * - Risk identification and assessment
 * - Risk categorization
 * - Risk response planning
 * - Inherent and residual exposure
 * - Risk ownership
 * - Policy-based governance
 * - Risk monitoring and escalation
 * - Portfolio reporting
 * - State transition validation
 *
 * Compile:
 * javac ProjectRiskManagement.java
 *
 * Run:
 * java ProjectRiskManagement
 */
public class ProjectRiskManagement {

    enum Category {
        TECHNICAL,
        FINANCIAL,
        OPERATIONAL,
        SCHEDULE,
        RESOURCE,
        SECURITY,
        LEGAL,
        QUALITY,
        SCOPE,
        EXTERNAL
    }

    enum RiskStatus {
        IDENTIFIED,
        ASSESSED,
        RESPONSE_PLANNED,
        MONITORING,
        ESCALATED,
        CLOSED
    }

    enum Strategy {
        AVOID,
        MITIGATE,
        TRANSFER,
        ACCEPT,
        EXPLOIT,
        ENHANCE,
        SHARE
    }

    enum RiskLevel {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum ReviewEvent {
        IDENTIFIED,
        ASSESSED,
        RESPONSE_ASSIGNED,
        MONITORED,
        ESCALATED,
        CLOSED
    }

    static class RiskException extends RuntimeException {
        RiskException(String message) {
            super(message);
        }
    }

    record Assessment(int probability, int impact) {

        Assessment {
            validateScore(probability, "Probability");
            validateScore(impact, "Impact");
        }

        int score() {
            return probability * impact;
        }

        RiskLevel level() {
            return classify(score());
        }
    }

    record ResponsePlan(
        Strategy strategy,
        String action,
        double responseCost,
        double contingencyReserve
    ) {
        ResponsePlan {
            Objects.requireNonNull(strategy, "Strategy is required.");
            requireText(action, "Response action");

            if (
                !Double.isFinite(responseCost) ||
                !Double.isFinite(contingencyReserve) ||
                responseCost < 0 ||
                contingencyReserve < 0
            ) {
                throw new RiskException(
                    "Response costs must be non-negative finite values."
                );
            }
        }

        double totalBudget() {
            return responseCost + contingencyReserve;
        }
    }

    record RiskHistory(
        ReviewEvent event,
        LocalDateTime timestamp,
        String details
    ) {}

    record GovernancePolicy(
        int highThreshold,
        int criticalThreshold,
        boolean requireOwner,
        boolean requireResponseForHighRisk
    ) {
        GovernancePolicy {
            if (
                highThreshold < 1 ||
                criticalThreshold > 25 ||
                highThreshold >= criticalThreshold
            ) {
                throw new RiskException(
                    "Invalid governance thresholds."
                );
            }
        }

        static GovernancePolicy standard() {
            return new GovernancePolicy(
                12,
                20,
                true,
                true
            );
        }
    }

    record PolicyEvaluation(
        String riskId,
        boolean compliant,
        List<String> violations,
        RiskLevel level,
        int exposure
    ) {
        PolicyEvaluation {
            violations = List.copyOf(violations);
        }
    }

    record PortfolioReport(
        int total,
        int active,
        int closed,
        int inherentExposure,
        int residualExposure,
        Map<RiskLevel, Long> levels,
        Map<Category, Integer> categoryExposure
    ) {
        PortfolioReport {
            levels = Map.copyOf(levels);
            categoryExposure = Map.copyOf(categoryExposure);
        }
    }

    static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new RiskException(field + " is required.");
        }
    }

    static void validateScore(int score, String field) {
        if (score < 1 || score > 5) {
            throw new RiskException(
                field + " must be between 1 and 5."
            );
        }
    }

    static RiskLevel classify(int score) {
        if (score >= 20) return RiskLevel.CRITICAL;
        if (score >= 12) return RiskLevel.HIGH;
        if (score >= 6) return RiskLevel.MEDIUM;
        return RiskLevel.LOW;
    }

    static final class Risk {

        private final String id;
        private final String title;
        private final String description;
        private final Category category;
        private final String owner;
        private final Assessment inherentAssessment;
        private final LocalDateTime identifiedAt;

        private RiskStatus status = RiskStatus.IDENTIFIED;

        private Assessment residualAssessment;
        private ResponsePlan responsePlan;

        private final Set<String> tags = new HashSet<>();
        private final List<RiskHistory> history = new ArrayList<>();

        Risk(
            String id,
            String title,
            String description,
            Category category,
            int probability,
            int impact,
            String owner
        ) {
            requireText(id, "Risk ID");
            requireText(title, "Risk title");
            requireText(description, "Risk description");
            requireText(owner, "Risk owner");

            this.id = id;
            this.title = title;
            this.description = description;
            this.category = Objects.requireNonNull(category);
            this.owner = owner;

            this.inherentAssessment = new Assessment(
                probability,
                impact
            );

            this.identifiedAt = LocalDateTime.now();

            record(
                ReviewEvent.IDENTIFIED,
                "Risk entered into the project register."
            );
        }

        private void ensureOpen() {
            if (status == RiskStatus.CLOSED) {
                throw new RiskException(
                    "Closed risks cannot be modified."
                );
            }
        }

        private void record(ReviewEvent event, String details) {
            history.add(
                new RiskHistory(
                    event,
                    LocalDateTime.now(),
                    details
                )
            );
        }

        String id() {
            return id;
        }

        String title() {
            return title;
        }

        String description() {
            return description;
        }

        Category category() {
            return category;
        }

        String owner() {
            return owner;
        }

        RiskStatus status() {
            return status;
        }

        Assessment inherentAssessment() {
            return inherentAssessment;
        }

        Assessment currentAssessment() {
            return residualAssessment != null
                ? residualAssessment
                : inherentAssessment;
        }

        ResponsePlan responsePlan() {
            return responsePlan;
        }

        int inherentScore() {
            return inherentAssessment.score();
        }

        int currentScore() {
            return currentAssessment().score();
        }

        RiskLevel currentLevel() {
            return currentAssessment().level();
        }

        List<RiskHistory> history() {
            return List.copyOf(history);
        }

        void assess() {
            ensureOpen();

            status = RiskStatus.ASSESSED;

            record(
                ReviewEvent.ASSESSED,
                "Inherent exposure assessed at " +
                inherentScore()
            );
        }

        void assignResponse(ResponsePlan plan) {
            ensureOpen();

            this.responsePlan = Objects.requireNonNull(plan);
            status = RiskStatus.RESPONSE_PLANNED;

            record(
                ReviewEvent.RESPONSE_ASSIGNED,
                plan.strategy() + ": " + plan.action()
            );
        }

        void monitor(Assessment assessment) {
            ensureOpen();

            this.residualAssessment =
                Objects.requireNonNull(assessment);

            status = RiskStatus.MONITORING;

            record(
                ReviewEvent.MONITORED,
                "Residual exposure updated to " +
                assessment.score()
            );
        }

        void escalate(String reason) {
            ensureOpen();
            requireText(reason, "Escalation reason");

            status = RiskStatus.ESCALATED;

            record(
                ReviewEvent.ESCALATED,
                reason
            );
        }

        void close(String resolution) {
            ensureOpen();
            requireText(resolution, "Closure resolution");

            status = RiskStatus.CLOSED;

            record(
                ReviewEvent.CLOSED,
                resolution
            );
        }

        void addTag(String tag) {
            ensureOpen();
            requireText(tag, "Tag");
            tags.add(tag);
        }

        Set<String> tags() {
            return Set.copyOf(tags);
        }
    }

    static final class Project {

        private final String id;
        private final String name;

        private final Map<String, Risk> risks = new HashMap<>();

        Project(String id, String name) {
            requireText(id, "Project ID");
            requireText(name, "Project name");

            this.id = id;
            this.name = name;
        }

        void addRisk(Risk risk) {
            Objects.requireNonNull(risk);

            if (risks.putIfAbsent(risk.id(), risk) != null) {
                throw new RiskException(
                    "Duplicate risk ID: " + risk.id()
                );
            }
        }

        Risk getRisk(String id) {
            Risk risk = risks.get(id);

            if (risk == null) {
                throw new RiskException(
                    "Risk does not exist: " + id
                );
            }

            return risk;
        }

        List<Risk> allRisks() {
            return List.copyOf(risks.values());
        }

        List<Risk> prioritizedRisks() {
            return risks.values()
                .stream()
                .sorted(
                    Comparator.comparingInt(Risk::currentScore)
                        .reversed()
                        .thenComparing(Risk::id)
                )
                .toList();
        }

        String id() {
            return id;
        }

        String name() {
            return name;
        }
    }

    static final class GovernanceService {

        private final GovernancePolicy policy;

        GovernanceService(GovernancePolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        PolicyEvaluation evaluate(Risk risk) {
            List<String> violations = new ArrayList<>();

            if (
                policy.requireOwner() &&
                risk.owner().isBlank()
            ) {
                violations.add("Risk owner is missing.");
            }

            if (
                policy.requireResponseForHighRisk() &&
                risk.currentScore() >= policy.highThreshold() &&
                risk.responsePlan() == null
            ) {
                violations.add(
                    "High-risk exposure requires a response plan."
                );
            }

            return new PolicyEvaluation(
                risk.id(),
                violations.isEmpty(),
                violations,
                risk.currentLevel(),
                risk.currentScore()
            );
        }

        List<PolicyEvaluation> evaluateProject(Project project) {
            return project.allRisks()
                .stream()
                .map(this::evaluate)
                .toList();
        }
    }

    static final class ReportingService {

        PortfolioReport generate(Project project) {
            List<Risk> active = project.allRisks()
                .stream()
                .filter(risk -> risk.status() != RiskStatus.CLOSED)
                .toList();

            int inherent = active.stream()
                .mapToInt(Risk::inherentScore)
                .sum();

            int residual = active.stream()
                .mapToInt(Risk::currentScore)
                .sum();

            Map<RiskLevel, Long> levels =
                active.stream().collect(
                    Collectors.groupingBy(
                        Risk::currentLevel,
                        () -> new EnumMap<>(RiskLevel.class),
                        Collectors.counting()
                    )
                );

            Map<Category, Integer> categoryExposure =
                new EnumMap<>(Category.class);

            for (Risk risk : active) {
                categoryExposure.merge(
                    risk.category(),
                    risk.currentScore(),
                    Integer::sum
                );
            }

            return new PortfolioReport(
                project.allRisks().size(),
                active.size(),
                project.allRisks().size() - active.size(),
                inherent,
                residual,
                levels,
                categoryExposure
            );
        }
    }

    static Project createSampleProject() {
        Project project = new Project(
            "PRJ-2026-001",
            "Enterprise Management Platform"
        );

        project.addRisk(new Risk(
            "R001",
            "Cloud provisioning delay",
            "Infrastructure may not be available on schedule.",
            Category.SCHEDULE,
            4,
            5,
            "Infrastructure Lead"
        ));

        project.addRisk(new Risk(
            "R002",
            "Budget overrun",
            "Unexpected licensing costs may increase expenditure.",
            Category.FINANCIAL,
            3,
            5,
            "Project Manager"
        ));

        project.addRisk(new Risk(
            "R003",
            "Unauthorized data access",
            "Confidential project data may be exposed.",
            Category.SECURITY,
            2,
            5,
            "Security Lead"
        ));

        project.addRisk(new Risk(
            "R004",
            "Developer unavailability",
            "A critical developer may become unavailable.",
            Category.RESOURCE,
            3,
            4,
            "Engineering Manager"
        ));

        project.addRisk(new Risk(
            "R005",
            "Uncontrolled scope expansion",
            "Unapproved requirements may delay delivery.",
            Category.SCOPE,
            4,
            4,
            "Product Owner"
        ));

        for (Risk risk : project.allRisks()) {
            risk.assess();
        }

        project.getRisk("R001").assignResponse(
            new ResponsePlan(
                Strategy.MITIGATE,
                "Maintain an alternative infrastructure provider.",
                10000,
                5000
            )
        );

        project.getRisk("R002").assignResponse(
            new ResponsePlan(
                Strategy.MITIGATE,
                "Introduce monthly budget monitoring.",
                2500,
                8000
            )
        );

        project.getRisk("R003").assignResponse(
            new ResponsePlan(
                Strategy.AVOID,
                "Enforce access controls and MFA.",
                4000,
                1000
            )
        );

        project.getRisk("R004").assignResponse(
            new ResponsePlan(
                Strategy.MITIGATE,
                "Cross-train development personnel.",
                3000,
                1000
            )
        );

        project.getRisk("R005").assignResponse(
            new ResponsePlan(
                Strategy.AVOID,
                "Enforce formal scope change approval.",
                1500,
                1000
            )
        );

        project.getRisk("R001").monitor(new Assessment(2, 4));
        project.getRisk("R002").monitor(new Assessment(2, 4));
        project.getRisk("R003").monitor(new Assessment(1, 4));
        project.getRisk("R004").monitor(new Assessment(2, 3));
        project.getRisk("R005").monitor(new Assessment(2, 3));

        return project;
    }

    static void runTests() {
        Risk risk = new Risk(
            "TEST01",
            "Test risk",
            "Validation risk.",
            Category.TECHNICAL,
            3,
            4,
            "Test Owner"
        );

        if (risk.inherentScore() != 12) {
            throw new AssertionError("Inherent score failed.");
        }

        risk.assignResponse(
            new ResponsePlan(
                Strategy.MITIGATE,
                "Introduce automated testing.",
                500,
                100
            )
        );

        risk.monitor(new Assessment(1, 2));

        if (risk.currentScore() != 2) {
            throw new AssertionError("Residual score failed.");
        }

        risk.close("Resolved.");

        try {
            risk.monitor(new Assessment(2, 2));
            throw new AssertionError(
                "Closed risk modification was permitted."
            );
        } catch (RiskException expected) {
            // Expected state-transition rejection.
        }

        try {
            new Assessment(6, 2);
            throw new AssertionError(
                "Invalid assessment was permitted."
            );
        } catch (RiskException expected) {
            // Expected validation rejection.
        }

        System.out.println("\nAll Java 17 tests passed.");
    }

    static void displayReport(Project project) {
        System.out.println("\nPROJECT RISK REGISTER");
        System.out.println(project.name());
        System.out.println("-".repeat(110));

        System.out.printf(
            "%-8s %-32s %-18s %-8s %-12s %-20s%n",
            "ID",
            "Risk",
            "Category",
            "Score",
            "Level",
            "Status"
        );

        for (Risk risk : project.prioritizedRisks()) {
            System.out.printf(
                "%-8s %-32s %-18s %-8d %-12s %-20s%n",
                risk.id(),
                risk.title(),
                risk.category(),
                risk.currentScore(),
                risk.currentLevel(),
                risk.status()
            );
        }
    }

    public static void main(String[] args) {
        try {
            Project project = createSampleProject();

            GovernanceService governance =
                new GovernanceService(
                    GovernancePolicy.standard()
                );

            ReportingService reporting =
                new ReportingService();

            displayReport(project);

            System.out.println("\nGOVERNANCE EVALUATION");

            for (
                PolicyEvaluation result :
                governance.evaluateProject(project)
            ) {
                System.out.printf(
                    "%s | %s | Score: %d | Level: %s%n",
                    result.riskId(),
                    result.compliant() ? "PASS" : "FAIL",
                    result.exposure(),
                    result.level()
                );

                result.violations().forEach(
                    violation -> System.out.println(
                        "  " + violation
                    )
                );
            }

            System.out.println("\nPORTFOLIO REPORT");
            System.out.println(reporting.generate(project));

            runTests();

        } catch (Exception error) {
            System.err.println(
                "Application error: " + error.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
