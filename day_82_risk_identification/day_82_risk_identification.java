import java.time.Instant;
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

/*
 * Enterprise Risk Identification and Assessment System
 *
 * Java 17
 * Standard library only.
 *
 * Provides:
 * - Strongly typed risk domain
 * - Risk identification workflow
 * - Evidence traceability
 * - Risk assessment
 * - Risk ownership
 * - Risk control evaluation
 * - Enterprise policy validation
 * - State transition enforcement
 * - Prioritization and reporting
 */

public class RiskIdentificationSystem {

    enum Category {
        STRATEGIC,
        OPERATIONAL,
        FINANCIAL,
        TECHNOLOGICAL,
        CYBERSECURITY,
        COMPLIANCE,
        REPUTATIONAL,
        ENVIRONMENTAL,
        HUMAN_RESOURCE,
        THIRD_PARTY
    }

    enum IdentificationSource {
        WORKSHOP,
        AUDIT,
        INCIDENT,
        INTERVIEW,
        HISTORICAL_DATA,
        TECHNICAL_ANALYSIS,
        EXTERNAL_ENVIRONMENT
    }

    enum RiskStatus {
        IDENTIFIED,
        ASSESSED,
        UNDER_REVIEW,
        MITIGATED,
        ACCEPTED,
        CLOSED
    }

    enum RiskLevel {
        LOW,
        MODERATE,
        HIGH,
        CRITICAL
    }

    enum ControlType {
        PREVENTIVE,
        DETECTIVE,
        CORRECTIVE
    }

    static class RiskException extends RuntimeException {
        RiskException(String message) {
            super(message);
        }
    }

    static String requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new RiskException(field + " is required.");
        }

        return value.trim();
    }

    static int validateScale(int value, String field) {
        if (value < 1 || value > 5) {
            throw new RiskException(
                field + " must be between 1 and 5."
            );
        }

        return value;
    }

    static double validateEffectiveness(double value) {
        if (!Double.isFinite(value) || value < 0 || value > 1) {
            throw new RiskException(
                "Control effectiveness must be between 0 and 1."
            );
        }

        return value;
    }

    static RiskLevel classify(double score) {
        if (score >= 75) return RiskLevel.CRITICAL;
        if (score >= 40) return RiskLevel.HIGH;
        if (score >= 15) return RiskLevel.MODERATE;
        return RiskLevel.LOW;
    }

    record Assessment(
        int probability,
        int impact,
        int detectability
    ) {
        Assessment {
            validateScale(probability, "Probability");
            validateScale(impact, "Impact");
            validateScale(detectability, "Detectability");
        }

        int score() {
            return probability * impact * detectability;
        }
    }

    record Evidence(
        String reference,
        String description,
        IdentificationSource source,
        Instant collectedAt
    ) {
        Evidence {
            reference = requireText(reference, "Evidence reference");
            description = requireText(description, "Evidence description");
            Objects.requireNonNull(source, "Evidence source is required.");
            collectedAt = Objects.requireNonNullElseGet(
                collectedAt,
                Instant::now
            );
        }
    }

    record Control(
        String id,
        String description,
        ControlType type,
        double effectiveness
    ) {
        Control {
            id = requireText(id, "Control ID");
            description = requireText(description, "Control description");
            Objects.requireNonNull(type, "Control type is required.");
            validateEffectiveness(effectiveness);
        }
    }

    record RiskPolicy(
        int maximumAcceptedInherentScore,
        boolean evidenceRequired,
        boolean ownerRequired,
        boolean highRiskRequiresSeniorReview
    ) {
        RiskPolicy {
            if (
                maximumAcceptedInherentScore < 1 ||
                maximumAcceptedInherentScore > 125
            ) {
                throw new RiskException(
                    "Invalid accepted-risk threshold."
                );
            }
        }

        static RiskPolicy enterpriseDefault() {
            return new RiskPolicy(39, true, true, true);
        }
    }

    static class Risk {

        private final UUID id;
        private final String title;
        private final String description;
        private final String context;
        private final Category category;
        private final IdentificationSource source;
        private final String owner;

        private Assessment assessment;
        private RiskStatus status;

        private final Map<String, Evidence> evidence;
        private final Map<String, Control> controls;

        private final Instant identifiedAt;
        private Instant reviewedAt;

        Risk(
            String title,
            String description,
            String context,
            Category category,
            IdentificationSource source,
            String owner,
            Assessment assessment
        ) {
            this.id = UUID.randomUUID();

            this.title = requireText(title, "Risk title");
            this.description = requireText(description, "Description");
            this.context = requireText(context, "Context");
            this.owner = requireText(owner, "Owner");

            this.category = Objects.requireNonNull(
                category,
                "Category is required."
            );

            this.source = Objects.requireNonNull(
                source,
                "Identification source is required."
            );

            this.assessment = Objects.requireNonNull(
                assessment,
                "Assessment is required."
            );

            this.status = RiskStatus.IDENTIFIED;
            this.evidence = new HashMap<>();
            this.controls = new HashMap<>();
            this.identifiedAt = Instant.now();
        }

        UUID id() {
            return id;
        }

        String title() {
            return title;
        }

        String owner() {
            return owner;
        }

        Category category() {
            return category;
        }

        RiskStatus status() {
            return status;
        }

        int inherentScore() {
            return assessment.score();
        }

        RiskLevel inherentLevel() {
            return classify(inherentScore());
        }

        double controlEffectiveness() {
            double remaining = 1.0;

            for (Control control : controls.values()) {
                remaining *= 1.0 - control.effectiveness();
            }

            return 1.0 - remaining;
        }

        double residualScore() {
            return inherentScore() * (1.0 - controlEffectiveness());
        }

        RiskLevel residualLevel() {
            return classify(residualScore());
        }

        void addEvidence(Evidence item) {
            if (evidence.putIfAbsent(item.reference(), item) != null) {
                throw new RiskException(
                    "Duplicate evidence reference: " + item.reference()
                );
            }
        }

        void addControl(Control control) {
            if (controls.putIfAbsent(control.id(), control) != null) {
                throw new RiskException(
                    "Duplicate control ID: " + control.id()
                );
            }
        }

        void reassess(Assessment nextAssessment) {
            Objects.requireNonNull(nextAssessment);

            assessment = nextAssessment;
            status = RiskStatus.ASSESSED;
            reviewedAt = Instant.now();
        }

        void transition(RiskStatus next) {
            Objects.requireNonNull(next);

            Map<RiskStatus, Set<RiskStatus>> allowed = Map.of(
                RiskStatus.IDENTIFIED, Set.of(
                    RiskStatus.ASSESSED,
                    RiskStatus.UNDER_REVIEW,
                    RiskStatus.CLOSED
                ),
                RiskStatus.ASSESSED, Set.of(
                    RiskStatus.UNDER_REVIEW,
                    RiskStatus.MITIGATED,
                    RiskStatus.ACCEPTED,
                    RiskStatus.CLOSED
                ),
                RiskStatus.UNDER_REVIEW, Set.of(
                    RiskStatus.ASSESSED,
                    RiskStatus.MITIGATED,
                    RiskStatus.ACCEPTED,
                    RiskStatus.CLOSED
                ),
                RiskStatus.MITIGATED, Set.of(
                    RiskStatus.UNDER_REVIEW,
                    RiskStatus.CLOSED
                ),
                RiskStatus.ACCEPTED, Set.of(
                    RiskStatus.UNDER_REVIEW,
                    RiskStatus.CLOSED
                ),
                RiskStatus.CLOSED, Set.of()
            );

            if (!allowed.get(status).contains(next)) {
                throw new RiskException(
                    "Invalid transition from " + status + " to " + next
                );
            }

            if (
                next == RiskStatus.MITIGATED &&
                controls.isEmpty()
            ) {
                throw new RiskException(
                    "Mitigation requires at least one control."
                );
            }

            status = next;
            reviewedAt = Instant.now();
        }

        List<Evidence> evidenceRecords() {
            return List.copyOf(evidence.values());
        }

        List<Control> controlRecords() {
            return List.copyOf(controls.values());
        }
    }

    interface RiskValidationRule {
        List<String> validate(Risk risk);
    }

    static class EvidenceValidationRule
        implements RiskValidationRule {

        @Override
        public List<String> validate(Risk risk) {
            if (risk.evidenceRecords().isEmpty()) {
                return List.of(
                    "At least one supporting evidence record is required."
                );
            }

            return List.of();
        }
    }

    static class SeniorReviewRule
        implements RiskValidationRule {

        @Override
        public List<String> validate(Risk risk) {
            if (
                risk.inherentScore() >= 40 &&
                risk.status() != RiskStatus.UNDER_REVIEW &&
                risk.status() != RiskStatus.MITIGATED &&
                risk.status() != RiskStatus.ACCEPTED
            ) {
                return List.of(
                    "High-risk items require senior review."
                );
            }

            return List.of();
        }
    }

    static class RiskGovernanceService {

        private final RiskPolicy policy;
        private final List<RiskValidationRule> rules;
        private final Map<UUID, Risk> risks;
        private final Set<String> fingerprints;

        RiskGovernanceService(RiskPolicy policy) {
            this.policy = Objects.requireNonNull(policy);

            this.rules = List.of(
                new EvidenceValidationRule(),
                new SeniorReviewRule()
            );

            this.risks = new HashMap<>();
            this.fingerprints = new HashSet<>();
        }

        Risk identify(
            String title,
            String description,
            String context,
            Category category,
            IdentificationSource source,
            String owner,
            Assessment assessment
        ) {
            Risk risk = new Risk(
                title,
                description,
                context,
                category,
                source,
                owner,
                assessment
            );

            String fingerprint = (
                risk.title().toLowerCase() + "|" +
                risk.category() + "|" +
                context.toLowerCase()
            );

            if (!fingerprints.add(fingerprint)) {
                throw new RiskException(
                    "Duplicate risk in the same organizational context."
                );
            }

            risks.put(risk.id(), risk);

            return risk;
        }

        Risk get(UUID id) {
            Risk risk = risks.get(id);

            if (risk == null) {
                throw new RiskException("Risk does not exist: " + id);
            }

            return risk;
        }

        List<String> validate(Risk risk) {
            List<String> violations = new ArrayList<>();

            if (policy.ownerRequired && risk.owner().isBlank()) {
                violations.add("Risk owner is required.");
            }

            if (
                risk.status() == RiskStatus.ACCEPTED &&
                risk.inherentScore() >
                    policy.maximumAcceptedInherentScore
            ) {
                violations.add(
                    "Risk acceptance exceeds permitted inherent exposure."
                );
            }

            if (policy.evidenceRequired) {
                for (RiskValidationRule rule : rules) {
                    violations.addAll(rule.validate(risk));
                }
            }

            return List.copyOf(violations);
        }

        void acceptRisk(UUID id) {
            Risk risk = get(id);

            List<String> violations = validate(risk);

            if (!violations.isEmpty()) {
                throw new RiskException(
                    "Acceptance rejected: " +
                    String.join("; ", violations)
                );
            }

            risk.transition(RiskStatus.ACCEPTED);
        }

        List<Risk> search(
            Category category,
            RiskStatus status,
            int minimumScore
        ) {
            return risks.values()
                .stream()
                .filter(risk ->
                    category == null || risk.category() == category
                )
                .filter(risk ->
                    status == null || risk.status() == status
                )
                .filter(risk ->
                    risk.inherentScore() >= minimumScore
                )
                .sorted(
                    Comparator.comparingInt(Risk::inherentScore)
                        .reversed()
                        .thenComparing(Risk::title)
                )
                .toList();
        }

        Map<Category, Long> categoryReport() {
            return risks.values()
                .stream()
                .collect(Collectors.groupingBy(
                    Risk::category,
                    () -> new EnumMap<>(Category.class),
                    Collectors.counting()
                ));
        }

        List<Risk> allRisks() {
            return List.copyOf(risks.values());
        }
    }

    static void runTests() {
        if (classify(10) != RiskLevel.LOW) {
            throw new AssertionError("Low classification failed.");
        }

        if (classify(50) != RiskLevel.HIGH) {
            throw new AssertionError("High classification failed.");
        }

        if (classify(80) != RiskLevel.CRITICAL) {
            throw new AssertionError("Critical classification failed.");
        }

        Risk risk = new Risk(
            "Test risk",
            "Testing enterprise assessment.",
            "Test environment",
            Category.OPERATIONAL,
            IdentificationSource.WORKSHOP,
            "Test Owner",
            new Assessment(2, 3, 4)
        );

        if (risk.inherentScore() != 24) {
            throw new AssertionError("Inherent score failed.");
        }

        risk.addControl(new Control(
            "TEST-1",
            "Validation control",
            ControlType.PREVENTIVE,
            0.5
        ));

        if (Math.abs(risk.residualScore() - 12) > 0.001) {
            throw new AssertionError("Residual score failed.");
        }

        boolean rejected = false;

        try {
            new Assessment(6, 2, 3);
        } catch (RiskException exception) {
            rejected = true;
        }

        if (!rejected) {
            throw new AssertionError("Invalid assessment accepted.");
        }
    }

    static void printReport(RiskGovernanceService service) {
        System.out.println("\nENTERPRISE RISK REGISTER");
        System.out.println(
            "ID | Risk | Category | Owner | Inherent | Residual | Status"
        );

        service.search(null, null, 0).forEach(risk ->
            System.out.printf(
                "%s | %s | %s | %s | %d (%s) | %.2f (%s) | %s%n",
                risk.id().toString().substring(0, 8),
                risk.title(),
                risk.category(),
                risk.owner(),
                risk.inherentScore(),
                risk.inherentLevel(),
                risk.residualScore(),
                risk.residualLevel(),
                risk.status()
            )
        );

        System.out.println("\nCATEGORY DISTRIBUTION");

        service.categoryReport().forEach((category, count) ->
            System.out.println(category + ": " + count)
        );
    }

    public static void main(String[] args) {
        try {
            runTests();

            RiskGovernanceService service =
                new RiskGovernanceService(
                    RiskPolicy.enterpriseDefault()
                );

            Risk cyber = service.identify(
                "Unauthorized production access",
                "Compromised credentials may expose sensitive systems.",
                "Production infrastructure",
                Category.CYBERSECURITY,
                IdentificationSource.TECHNICAL_ANALYSIS,
                "Security Operations Manager",
                new Assessment(4, 5, 4)
            );

            cyber.addEvidence(new Evidence(
                "AUDIT-014",
                "Privileged accounts lack consistent MFA enforcement.",
                IdentificationSource.AUDIT,
                Instant.now()
            ));

            cyber.addControl(new Control(
                "CTRL-MFA",
                "Enforce phishing-resistant MFA.",
                ControlType.PREVENTIVE,
                0.55
            ));

            cyber.addControl(new Control(
                "CTRL-MON",
                "Monitor privileged account activity.",
                ControlType.DETECTIVE,
                0.30
            ));

            cyber.transition(RiskStatus.ASSESSED);
            cyber.transition(RiskStatus.UNDER_REVIEW);

            Risk supplier = service.identify(
                "Critical supplier interruption",
                "A supplier outage may interrupt business operations.",
                "Cloud service dependencies",
                Category.THIRD_PARTY,
                IdentificationSource.HISTORICAL_DATA,
                "Vendor Management Lead",
                new Assessment(4, 4, 3)
            );

            supplier.addEvidence(new Evidence(
                "INCIDENT-022",
                "Previous outages exceeded recovery targets.",
                IdentificationSource.INCIDENT,
                Instant.now()
            ));

            supplier.transition(RiskStatus.ASSESSED);
            supplier.transition(RiskStatus.UNDER_REVIEW);

            Risk compliance = service.identify(
                "Regulatory reporting failure",
                "Incomplete records may delay regulatory submissions.",
                "Regulatory reporting",
                Category.COMPLIANCE,
                IdentificationSource.INTERVIEW,
                "Compliance Officer",
                new Assessment(2, 5, 3)
            );

            compliance.addEvidence(new Evidence(
                "INT-2026-003",
                "Reporting dependency gaps identified in interviews.",
                IdentificationSource.INTERVIEW,
                Instant.now()
            ));

            compliance.transition(RiskStatus.ASSESSED);

            printReport(service);

            System.out.println("\nVALIDATION RESULTS");

            for (Risk risk : service.allRisks()) {
                List<String> violations = service.validate(risk);

                System.out.println(
                    risk.title() + ": " +
                    (violations.isEmpty()
                        ? "Valid"
                        : String.join("; ", violations))
                );
            }

            System.out.println("\nAll validation tests passed.");

        } catch (RuntimeException exception) {
            System.err.println(
                "Enterprise risk processing failed: " +
                exception.getMessage()
            );

            System.exit(1);
        }
    }
}
