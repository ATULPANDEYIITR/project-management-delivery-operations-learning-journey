import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;

public class RiskIssueManagement {

    enum RiskStatus {
        IDENTIFIED,
        ASSESSED,
        MITIGATING,
        ACCEPTED,
        CLOSED
    }

    enum IssueStatus {
        OPEN,
        IN_PROGRESS,
        BLOCKED,
        RESOLVED,
        CLOSED
    }

    enum Severity {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    enum Priority {
        LOW,
        MEDIUM,
        HIGH,
        URGENT
    }

    static class DomainException extends RuntimeException {
        DomainException(String message) {
            super(message);
        }
    }

    static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new DomainException(
                field + " must not be empty."
            );
        }
    }

    static Severity calculateSeverity(int probability, int impact) {
        int exposure = probability * impact;

        if (exposure >= 20) return Severity.CRITICAL;
        if (exposure >= 12) return Severity.HIGH;
        if (exposure >= 6) return Severity.MEDIUM;

        return Severity.LOW;
    }

    static Priority priorityFor(Severity severity) {
        return switch (severity) {
            case LOW -> Priority.LOW;
            case MEDIUM -> Priority.MEDIUM;
            case HIGH -> Priority.HIGH;
            case CRITICAL -> Priority.URGENT;
        };
    }

    record RiskAssessment(
        int probability,
        int impact,
        int exposure,
        Severity severity,
        Instant assessedAt
    ) {
        RiskAssessment {
            if (probability < 1 || probability > 5) {
                throw new DomainException(
                    "Probability must be between 1 and 5."
                );
            }

            if (impact < 1 || impact > 5) {
                throw new DomainException(
                    "Impact must be between 1 and 5."
                );
            }

            if (exposure != probability * impact) {
                throw new DomainException(
                    "Risk exposure calculation is inconsistent."
                );
            }

            Objects.requireNonNull(severity);
            Objects.requireNonNull(assessedAt);
        }

        static RiskAssessment create(int probability, int impact) {
            return new RiskAssessment(
                probability,
                impact,
                probability * impact,
                calculateSeverity(probability, impact),
                Instant.now()
            );
        }
    }

    static final class Risk {
        private final UUID id;
        private final String title;
        private final String description;
        private final String owner;
        private final String category;
        private final String mitigation;
        private final String contingency;
        private final Instant createdAt;

        private final List<RiskAssessment> assessmentHistory =
            new ArrayList<>();

        private RiskStatus status = RiskStatus.IDENTIFIED;

        Risk(
            String title,
            String description,
            String owner,
            String category,
            String mitigation,
            String contingency
        ) {
            requireText(title, "Risk title");
            requireText(description, "Risk description");
            requireText(owner, "Risk owner");
            requireText(category, "Risk category");

            this.id = UUID.randomUUID();
            this.title = title;
            this.description = description;
            this.owner = owner;
            this.category = category;
            this.mitigation = mitigation;
            this.contingency = contingency;
            this.createdAt = Instant.now();
        }

        RiskAssessment assess(int probability, int impact) {
            if (status == RiskStatus.CLOSED) {
                throw new DomainException(
                    "Closed risks cannot be reassessed."
                );
            }

            RiskAssessment assessment =
                RiskAssessment.create(probability, impact);

            assessmentHistory.add(assessment);
            status = RiskStatus.ASSESSED;

            return assessment;
        }

        void startMitigation() {
            if (status != RiskStatus.IDENTIFIED &&
                status != RiskStatus.ASSESSED) {
                throw new DomainException(
                    "Invalid risk mitigation transition."
                );
            }

            requireText(mitigation, "Mitigation plan");
            status = RiskStatus.MITIGATING;
        }

        void accept() {
            if (status == RiskStatus.CLOSED) {
                throw new DomainException(
                    "Closed risk cannot be accepted."
                );
            }

            status = RiskStatus.ACCEPTED;
        }

        void close() {
            if (status != RiskStatus.MITIGATING &&
                status != RiskStatus.ACCEPTED) {
                throw new DomainException(
                    "Risk must be mitigated or accepted."
                );
            }

            status = RiskStatus.CLOSED;
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

        RiskStatus status() {
            return status;
        }

        String category() {
            return category;
        }

        Instant createdAt() {
            return createdAt;
        }

        RiskAssessment latestAssessment() {
            if (assessmentHistory.isEmpty()) {
                throw new DomainException(
                    "Risk has not been assessed."
                );
            }

            return assessmentHistory.get(
                assessmentHistory.size() - 1
            );
        }

        List<RiskAssessment> assessmentHistory() {
            return List.copyOf(assessmentHistory);
        }
    }

    static final class Issue {
        private final UUID id;
        private final String title;
        private final String description;
        private final String owner;
        private final UUID sourceRiskId;
        private final Severity severity;
        private final Priority priority;
        private final Instant createdAt;

        private IssueStatus status = IssueStatus.OPEN;
        private String resolution;

        Issue(
            String title,
            String description,
            String owner,
            Severity severity,
            UUID sourceRiskId
        ) {
            requireText(title, "Issue title");
            requireText(description, "Issue description");
            requireText(owner, "Issue owner");

            this.id = UUID.randomUUID();
            this.title = title;
            this.description = description;
            this.owner = owner;
            this.severity = Objects.requireNonNull(severity);
            this.priority = priorityFor(severity);
            this.sourceRiskId = sourceRiskId;
            this.createdAt = Instant.now();
        }

        void start() {
            if (status != IssueStatus.OPEN) {
                throw new DomainException(
                    "Only open issues can be started."
                );
            }

            status = IssueStatus.IN_PROGRESS;
        }

        void block() {
            if (status != IssueStatus.OPEN &&
                status != IssueStatus.IN_PROGRESS) {
                throw new DomainException(
                    "Invalid issue blocking transition."
                );
            }

            status = IssueStatus.BLOCKED;
        }

        void resolve(String details) {
            if (status != IssueStatus.OPEN &&
                status != IssueStatus.IN_PROGRESS &&
                status != IssueStatus.BLOCKED) {
                throw new DomainException(
                    "Issue cannot be resolved."
                );
            }

            requireText(details, "Resolution");
            resolution = details;
            status = IssueStatus.RESOLVED;
        }

        void close() {
            if (status != IssueStatus.RESOLVED) {
                throw new DomainException(
                    "Only resolved issues can be closed."
                );
            }

            status = IssueStatus.CLOSED;
        }

        UUID id() {
            return id;
        }

        UUID sourceRiskId() {
            return sourceRiskId;
        }

        String title() {
            return title;
        }

        String owner() {
            return owner;
        }

        Severity severity() {
            return severity;
        }

        Priority priority() {
            return priority;
        }

        IssueStatus status() {
            return status;
        }

        String resolution() {
            return resolution;
        }

        Instant createdAt() {
            return createdAt;
        }
    }

    interface RiskPolicy {
        boolean requiresImmediateEscalation(
            RiskAssessment assessment
        );
    }

    static final class StandardRiskPolicy implements RiskPolicy {
        private final int escalationThreshold;

        StandardRiskPolicy(int escalationThreshold) {
            if (escalationThreshold < 1 ||
                escalationThreshold > 25) {
                throw new DomainException(
                    "Invalid escalation threshold."
                );
            }

            this.escalationThreshold = escalationThreshold;
        }

        @Override
        public boolean requiresImmediateEscalation(
            RiskAssessment assessment
        ) {
            return assessment.exposure() >= escalationThreshold;
        }
    }

    static final class GovernanceService {
        private final Map<UUID, Risk> risks = new HashMap<>();
        private final Map<UUID, Issue> issues = new HashMap<>();

        private final RiskPolicy policy;

        GovernanceService(RiskPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void registerRisk(Risk risk) {
            Objects.requireNonNull(risk);

            if (risks.putIfAbsent(risk.id(), risk) != null) {
                throw new DomainException(
                    "Duplicate risk identifier."
                );
            }
        }

        void registerIssue(Issue issue) {
            Objects.requireNonNull(issue);

            if (issue.sourceRiskId() != null &&
                !risks.containsKey(issue.sourceRiskId())) {
                throw new DomainException(
                    "Source risk does not exist."
                );
            }

            if (issues.putIfAbsent(issue.id(), issue) != null) {
                throw new DomainException(
                    "Duplicate issue identifier."
                );
            }
        }

        Issue materializeRisk(
            UUID riskId,
            String issueTitle,
            String issueDescription
        ) {
            Risk risk = risks.get(riskId);

            if (risk == null) {
                throw new DomainException("Risk not found.");
            }

            RiskAssessment assessment = risk.latestAssessment();

            Issue issue = new Issue(
                issueTitle,
                issueDescription,
                risk.owner(),
                assessment.severity(),
                risk.id()
            );

            registerIssue(issue);

            return issue;
        }

        boolean requiresEscalation(UUID riskId) {
            Risk risk = risks.get(riskId);

            if (risk == null) {
                throw new DomainException("Risk not found.");
            }

            return policy.requiresImmediateEscalation(
                risk.latestAssessment()
            );
        }

        Risk getRisk(UUID id) {
            Risk risk = risks.get(id);

            if (risk == null) {
                throw new DomainException("Risk not found.");
            }

            return risk;
        }

        Issue getIssue(UUID id) {
            Issue issue = issues.get(id);

            if (issue == null) {
                throw new DomainException("Issue not found.");
            }

            return issue;
        }

        List<Risk> prioritizedRisks() {
            return risks.values().stream()
                .filter(risk -> risk.status() != RiskStatus.CLOSED)
                .sorted(
                    Comparator.comparingInt(
                        (Risk risk) ->
                            risk.latestAssessment().exposure()
                    ).reversed()
                )
                .toList();
        }

        List<Issue> unresolvedIssues() {
            return issues.values().stream()
                .filter(issue ->
                    issue.status() != IssueStatus.RESOLVED &&
                    issue.status() != IssueStatus.CLOSED
                )
                .sorted(
                    Comparator.comparing(
                        Issue::priority,
                        Comparator.reverseOrder()
                    )
                )
                .toList();
        }

        Map<String, Long> issueStatusReport() {
            return issues.values().stream()
                .collect(Collectors.groupingBy(
                    issue -> issue.status().name(),
                    Collectors.counting()
                ));
        }

        Map<String, Integer> riskStatusReport() {
            Map<String, Integer> report =
                new HashMap<>();

            for (RiskStatus status : RiskStatus.values()) {
                report.put(status.name(), 0);
            }

            for (Risk risk : risks.values()) {
                report.merge(
                    risk.status().name(),
                    1,
                    Integer::sum
                );
            }

            return Map.copyOf(report);
        }

        void validateTraceability() {
            for (Issue issue : issues.values()) {
                if (issue.sourceRiskId() != null &&
                    !risks.containsKey(issue.sourceRiskId())) {
                    throw new DomainException(
                        "Broken risk-to-issue relationship."
                    );
                }
            }
        }

        void printDashboard() {
            System.out.println("\nMANAGEMENT DASHBOARD");
            System.out.println("Total risks: " + risks.size());
            System.out.println("Total issues: " + issues.size());

            long criticalRisks = risks.values().stream()
                .filter(risk -> risk.status() != RiskStatus.CLOSED)
                .filter(risk ->
                    risk.latestAssessment().severity() ==
                        Severity.CRITICAL
                )
                .count();

            System.out.println(
                "Critical active risks: " + criticalRisks
            );

            System.out.println(
                "Unresolved issues: " + unresolvedIssues().size()
            );

            System.out.println(
                "Risk states: " + riskStatusReport()
            );

            System.out.println(
                "Issue states: " + issueStatusReport()
            );
        }
    }

    public static void main(String[] args) {
        try {
            GovernanceService service =
                new GovernanceService(
                    new StandardRiskPolicy(15)
                );

            Risk infrastructureRisk = new Risk(
                "Cloud region failure",
                "The primary cloud region may become unavailable.",
                "Infrastructure Team",
                "Technology",
                "Configure multi-region failover.",
                "Switch traffic to the secondary region."
            );

            service.registerRisk(infrastructureRisk);

            RiskAssessment infrastructureAssessment =
                infrastructureRisk.assess(3, 5);

            infrastructureRisk.startMitigation();

            Risk securityRisk = new Risk(
                "Credential compromise",
                "An attacker may obtain administrator credentials.",
                "Security Team",
                "Cybersecurity",
                "Implement MFA and privileged access management.",
                "Revoke credentials and isolate affected systems."
            );

            service.registerRisk(securityRisk);

            RiskAssessment securityAssessment =
                securityRisk.assess(4, 5);

            Issue databaseIssue = new Issue(
                "Database unavailable",
                "Production transactions cannot access the database.",
                "Database Team",
                Severity.CRITICAL,
                null
            );

            service.registerIssue(databaseIssue);
            databaseIssue.start();

            databaseIssue.resolve(
                "Restored database connectivity and verified transactions."
            );

            databaseIssue.close();

            // A risk becomes an issue when the uncertain event occurs.
            Issue securityIncident = service.materializeRisk(
                securityRisk.id(),
                "Unauthorized administrator login",
                "Monitoring confirmed unauthorized administrator access."
            );

            securityIncident.start();

            System.out.println("RISK ASSESSMENTS");
            System.out.println(infrastructureAssessment);
            System.out.println(securityAssessment);

            System.out.println(
                "\nSecurity risk requires escalation: " +
                service.requiresEscalation(securityRisk.id())
            );

            System.out.println("\nPRIORITIZED RISKS");

            for (Risk risk : service.prioritizedRisks()) {
                System.out.println(
                    risk.title() + " | " +
                    risk.latestAssessment().exposure() + " | " +
                    risk.latestAssessment().severity() + " | " +
                    risk.status()
                );
            }

            System.out.println("\nUNRESOLVED ISSUES");

            for (Issue issue : service.unresolvedIssues()) {
                System.out.println(
                    issue.title() + " | " +
                    issue.priority() + " | " +
                    issue.status()
                );
            }

            service.validateTraceability();
            service.printDashboard();

            System.out.println(
                "\nRisk-to-issue relationship: " +
                securityIncident.sourceRiskId()
            );

            System.out.println("\nAll governance validations passed.");

        } catch (DomainException exception) {
            System.err.println(
                "Governance error: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
