import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/*
 * Enterprise Project Risk Monitoring System
 *
 * Java 17
 * Standard library only.
 *
 * Implements an enterprise-oriented project risk register,
 * assessment policies, monitoring observations, escalation,
 * governance rules, audit history, and portfolio reporting.
 */

public class ProjectRiskMonitoring {

    // ---------------------------------------------------------
    // Enumerations
    // ---------------------------------------------------------

    enum RiskCategory {
        SCHEDULE,
        COST,
        TECHNICAL,
        RESOURCE,
        SECURITY,
        OPERATIONAL,
        LEGAL,
        EXTERNAL
    }

    enum RiskStatus {
        IDENTIFIED,
        ASSESSED,
        MITIGATION_PLANNED,
        MONITORING,
        ESCALATED,
        MATERIALIZED,
        CLOSED
    }

    enum RiskResponse {
        AVOID,
        MITIGATE,
        TRANSFER,
        ACCEPT
    }

    enum RiskLevel {
        LOW,
        MEDIUM,
        HIGH,
        CRITICAL
    }

    // ---------------------------------------------------------
    // Custom exceptions
    // ---------------------------------------------------------

    static class RiskException extends RuntimeException {
        RiskException(String message) {
            super(message);
        }
    }

    static class ValidationException extends RiskException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class RiskNotFoundException extends RiskException {
        RiskNotFoundException(String message) {
            super(message);
        }
    }

    static class InvalidTransitionException extends RiskException {
        InvalidTransitionException(String message) {
            super(message);
        }
    }

    static class VersionConflictException extends RiskException {
        VersionConflictException(String message) {
            super(message);
        }
    }

    // ---------------------------------------------------------
    // Immutable domain records
    // ---------------------------------------------------------

    record Assessment(
        int probability,
        int impact,
        int exposure,
        RiskLevel level
    ) {}

    record RiskObservation(
        int probability,
        int impact,
        String notes,
        String recordedBy,
        LocalDateTime observedAt,
        Assessment previousAssessment,
        Assessment currentAssessment
    ) {
        RiskObservation {
            validateScore(probability, "Probability");
            validateScore(impact, "Impact");
            requireText(notes, "Observation notes");
            requireText(recordedBy, "Recorded by");

            Objects.requireNonNull(observedAt);
            Objects.requireNonNull(previousAssessment);
            Objects.requireNonNull(currentAssessment);
        }
    }

    record AuditEvent(
        String eventType,
        String actor,
        String description,
        LocalDateTime timestamp
    ) {}

    record RiskSummary(
        String riskId,
        String title,
        String owner,
        RiskCategory category,
        RiskStatus status,
        int exposure,
        RiskLevel level,
        LocalDate dueDate
    ) {}

    record PortfolioReport(
        int totalRisks,
        int activeRisks,
        int overdueRisks,
        int totalExposure,
        double averageExposure,
        Map<RiskLevel, Long> riskLevels,
        Map<RiskStatus, Long> statuses,
        Map<RiskCategory, Long> categories
    ) {}

    // ---------------------------------------------------------
    // Validation utilities
    // ---------------------------------------------------------

    static void requireText(String value, String field) {
        if (value == null || value.isBlank()) {
            throw new ValidationException(
                field + " is required"
            );
        }
    }

    static void validateScore(int value, String field) {
        if (value < 1 || value > 5) {
            throw new ValidationException(
                field + " must be between 1 and 5"
            );
        }
    }

    // ---------------------------------------------------------
    // Assessment policy interface
    // ---------------------------------------------------------

    interface AssessmentPolicy {
        Assessment evaluate(int probability, int impact);
    }

    static final class ProbabilityImpactPolicy
            implements AssessmentPolicy {

        private final int lowMaximum;
        private final int mediumMaximum;
        private final int highMaximum;

        ProbabilityImpactPolicy(
            int lowMaximum,
            int mediumMaximum,
            int highMaximum
        ) {
            if (
                lowMaximum < 1 ||
                lowMaximum >= mediumMaximum ||
                mediumMaximum >= highMaximum ||
                highMaximum >= 25
            ) {
                throw new ValidationException(
                    "Invalid assessment thresholds"
                );
            }

            this.lowMaximum = lowMaximum;
            this.mediumMaximum = mediumMaximum;
            this.highMaximum = highMaximum;
        }

        @Override
        public Assessment evaluate(
            int probability,
            int impact
        ) {
            validateScore(probability, "Probability");
            validateScore(impact, "Impact");

            int exposure = probability * impact;

            RiskLevel level;

            if (exposure <= lowMaximum) {
                level = RiskLevel.LOW;
            } else if (exposure <= mediumMaximum) {
                level = RiskLevel.MEDIUM;
            } else if (exposure <= highMaximum) {
                level = RiskLevel.HIGH;
            } else {
                level = RiskLevel.CRITICAL;
            }

            return new Assessment(
                probability,
                impact,
                exposure,
                level
            );
        }
    }

    // ---------------------------------------------------------
    // Risk entity
    // ---------------------------------------------------------

    static final class ProjectRisk {

        private final String id;
        private final String projectId;
        private final String title;
        private final String description;
        private final String owner;
        private final RiskCategory category;
        private final RiskResponse response;
        private final LocalDate dueDate;
        private final LocalDateTime createdAt;

        private RiskStatus status;

        private int probability;
        private int impact;
        private int version;
        private int reviewCount;

        private String mitigationPlan;
        private String contingencyPlan;

        private LocalDateTime updatedAt;
        private LocalDateTime lastReviewed;

        private final List<RiskObservation> observations;
        private final List<AuditEvent> auditTrail;

        ProjectRisk(
            String projectId,
            String title,
            String description,
            RiskCategory category,
            String owner,
            int probability,
            int impact,
            LocalDate dueDate,
            RiskResponse response
        ) {
            requireText(projectId, "Project ID");
            requireText(title, "Title");
            requireText(description, "Description");
            requireText(owner, "Owner");

            validateScore(probability, "Probability");
            validateScore(impact, "Impact");

            this.id = UUID.randomUUID().toString();
            this.projectId = projectId;
            this.title = title;
            this.description = description;
            this.category = Objects.requireNonNull(category);
            this.owner = owner;
            this.probability = probability;
            this.impact = impact;
            this.dueDate = Objects.requireNonNull(dueDate);
            this.response = Objects.requireNonNull(response);

            this.status = RiskStatus.IDENTIFIED;
            this.version = 1;
            this.reviewCount = 0;

            this.mitigationPlan = "";
            this.contingencyPlan = "";

            this.createdAt = LocalDateTime.now();
            this.updatedAt = createdAt;

            this.observations = new ArrayList<>();
            this.auditTrail = new ArrayList<>();

            recordEvent(
                "REGISTERED",
                "SYSTEM",
                "Risk registered"
            );
        }

        private void recordEvent(
            String type,
            String actor,
            String description
        ) {
            auditTrail.add(
                new AuditEvent(
                    type,
                    actor,
                    description,
                    LocalDateTime.now()
                )
            );
        }

        public String getId() {
            return id;
        }

        public String getProjectId() {
            return projectId;
        }

        public String getTitle() {
            return title;
        }

        public String getOwner() {
            return owner;
        }

        public RiskCategory getCategory() {
            return category;
        }

        public RiskStatus getStatus() {
            return status;
        }

        public int getVersion() {
            return version;
        }

        public LocalDate getDueDate() {
            return dueDate;
        }

        public List<AuditEvent> getAuditTrail() {
            return List.copyOf(auditTrail);
        }

        public List<RiskObservation> getObservations() {
            return List.copyOf(observations);
        }
    }

    // ---------------------------------------------------------
    // Lifecycle policy
    // ---------------------------------------------------------

    static final class RiskLifecyclePolicy {

        private static final Map<
            RiskStatus,
            Set<RiskStatus>
        > TRANSITIONS = Map.of(
            RiskStatus.IDENTIFIED,
            Set.of(
                RiskStatus.ASSESSED,
                RiskStatus.CLOSED
            ),

            RiskStatus.ASSESSED,
            Set.of(
                RiskStatus.MITIGATION_PLANNED,
                RiskStatus.MONITORING,
                RiskStatus.ESCALATED,
                RiskStatus.CLOSED
            ),

            RiskStatus.MITIGATION_PLANNED,
            Set.of(
                RiskStatus.MONITORING,
                RiskStatus.ESCALATED,
                RiskStatus.CLOSED
            ),

            RiskStatus.MONITORING,
            Set.of(
                RiskStatus.ESCALATED,
                RiskStatus.MATERIALIZED,
                RiskStatus.CLOSED
            ),

            RiskStatus.ESCALATED,
            Set.of(
                RiskStatus.MONITORING,
                RiskStatus.MATERIALIZED,
                RiskStatus.CLOSED
            ),

            RiskStatus.MATERIALIZED,
            Set.of(RiskStatus.CLOSED),

            RiskStatus.CLOSED,
            Set.of()
        );

        static void validate(
            RiskStatus current,
            RiskStatus next,
            ProjectRisk risk
        ) {
            if (!TRANSITIONS.get(current).contains(next)) {
                throw new InvalidTransitionException(
                    "Prohibited transition: " +
                    current + " -> " + next
                );
            }

            if (
                next == RiskStatus.MITIGATION_PLANNED &&
                risk.mitigationPlan.isBlank()
            ) {
                throw new ValidationException(
                    "Mitigation plan is mandatory"
                );
            }
        }
    }

    // ---------------------------------------------------------
    // Repository interface
    // ---------------------------------------------------------

    interface RiskRepository {
        void save(ProjectRisk risk);
        Optional<ProjectRisk> findById(String id);
        List<ProjectRisk> findByProject(String projectId);
        List<ProjectRisk> findAll();
    }

    static final class InMemoryRiskRepository
            implements RiskRepository {

        private final Map<String, ProjectRisk> records =
            new ConcurrentHashMap<>();

        @Override
        public void save(ProjectRisk risk) {
            records.put(risk.id, risk);
        }

        @Override
        public Optional<ProjectRisk> findById(String id) {
            return Optional.ofNullable(records.get(id));
        }

        @Override
        public List<ProjectRisk> findByProject(
            String projectId
        ) {
            return records.values().stream()
                .filter(risk ->
                    risk.projectId.equals(projectId)
                )
                .toList();
        }

        @Override
        public List<ProjectRisk> findAll() {
            return List.copyOf(records.values());
        }
    }

    // ---------------------------------------------------------
    // Enterprise risk service
    // ---------------------------------------------------------

    static final class RiskManagementService {

        private final RiskRepository repository;
        private final AssessmentPolicy assessmentPolicy;

        RiskManagementService(
            RiskRepository repository,
            AssessmentPolicy assessmentPolicy
        ) {
            this.repository = Objects.requireNonNull(repository);
            this.assessmentPolicy =
                Objects.requireNonNull(assessmentPolicy);
        }

        ProjectRisk register(
            String projectId,
            String title,
            String description,
            RiskCategory category,
            String owner,
            int probability,
            int impact,
            LocalDate dueDate,
            RiskResponse response
        ) {
            ProjectRisk risk = new ProjectRisk(
                projectId,
                title,
                description,
                category,
                owner,
                probability,
                impact,
                dueDate,
                response
            );

            repository.save(risk);

            return risk;
        }

        ProjectRisk find(String id) {
            return repository.findById(id)
                .orElseThrow(() ->
                    new RiskNotFoundException(
                        "Risk not found: " + id
                    )
                );
        }

        Assessment assess(String id) {
            ProjectRisk risk = find(id);

            return assessmentPolicy.evaluate(
                risk.probability,
                risk.impact
            );
        }

        void transition(
            String id,
            RiskStatus next,
            int expectedVersion,
            String actor
        ) {
            ProjectRisk risk = find(id);

            synchronized (risk) {
                verifyVersion(risk, expectedVersion);

                RiskLifecyclePolicy.validate(
                    risk.status,
                    next,
                    risk
                );

                RiskStatus previous = risk.status;

                risk.status = next;
                risk.version++;
                risk.updatedAt = LocalDateTime.now();

                risk.recordEvent(
                    "STATUS_CHANGED",
                    actor,
                    previous + " -> " + next
                );

                repository.save(risk);
            }
        }

        void addMitigation(
            String id,
            String plan,
            String contingency,
            int expectedVersion,
            String actor
        ) {
            requireText(plan, "Mitigation plan");
            requireText(contingency, "Contingency plan");

            ProjectRisk risk = find(id);

            synchronized (risk) {
                verifyVersion(risk, expectedVersion);

                if (risk.status != RiskStatus.ASSESSED) {
                    throw new InvalidTransitionException(
                        "Risk must be assessed before mitigation"
                    );
                }

                risk.mitigationPlan = plan;
                risk.contingencyPlan = contingency;

                risk.version++;
                risk.updatedAt = LocalDateTime.now();

                risk.recordEvent(
                    "MITIGATION_RECORDED",
                    actor,
                    "Mitigation and contingency plans recorded"
                );

                repository.save(risk);

                // Transition executes with the updated version.
                transition(
                    id,
                    RiskStatus.MITIGATION_PLANNED,
                    risk.version,
                    actor
                );
            }
        }

        RiskObservation observe(
            String id,
            int probability,
            int impact,
            String notes,
            String recordedBy,
            int expectedVersion
        ) {
            ProjectRisk risk = find(id);

            synchronized (risk) {
                verifyVersion(risk, expectedVersion);

                if (
                    risk.status != RiskStatus.MONITORING &&
                    risk.status != RiskStatus.ESCALATED
                ) {
                    throw new InvalidTransitionException(
                        "Risk is not actively monitored"
                    );
                }

                Assessment previous = assessmentPolicy.evaluate(
                    risk.probability,
                    risk.impact
                );

                Assessment current = assessmentPolicy.evaluate(
                    probability,
                    impact
                );

                RiskObservation observation =
                    new RiskObservation(
                        probability,
                        impact,
                        notes,
                        recordedBy,
                        LocalDateTime.now(),
                        previous,
                        current
                    );

                risk.probability = probability;
                risk.impact = impact;

                risk.observations.add(observation);
                risk.reviewCount++;

                risk.lastReviewed = observation.observedAt();
                risk.updatedAt = observation.observedAt();

                risk.version++;

                risk.recordEvent(
                    "OBSERVATION_RECORDED",
                    recordedBy,
                    "Exposure changed from " +
                    previous.exposure() + " to " +
                    current.exposure()
                );

                if (current.level() == RiskLevel.CRITICAL) {
                    risk.status = RiskStatus.ESCALATED;

                    risk.recordEvent(
                        "AUTOMATIC_ESCALATION",
                        "SYSTEM",
                        "Critical risk exposure detected"
                    );

                    risk.version++;
                } else if (
                    current.level() == RiskLevel.HIGH
                ) {
                    risk.recordEvent(
                        "HIGH_RISK_ALERT",
                        "SYSTEM",
                        "High exposure requires management attention"
                    );
                }

                repository.save(risk);

                return observation;
            }
        }

        void close(
            String id,
            String reason,
            int expectedVersion,
            String actor
        ) {
            requireText(reason, "Closure reason");

            ProjectRisk risk = find(id);

            synchronized (risk) {
                verifyVersion(risk, expectedVersion);

                transition(
                    id,
                    RiskStatus.CLOSED,
                    expectedVersion,
                    actor
                );

                risk.recordEvent(
                    "CLOSURE_REASON",
                    actor,
                    reason
                );

                repository.save(risk);
            }
        }

        private void verifyVersion(
            ProjectRisk risk,
            int expectedVersion
        ) {
            if (risk.version != expectedVersion) {
                throw new VersionConflictException(
                    "Expected version " + expectedVersion +
                    " but found " + risk.version
                );
            }
        }

        List<RiskSummary> priorityReport() {
            return repository.findAll().stream()
                .filter(risk ->
                    risk.status != RiskStatus.CLOSED
                )
                .map(risk -> {
                    Assessment assessment =
                        assessmentPolicy.evaluate(
                            risk.probability,
                            risk.impact
                        );

                    return new RiskSummary(
                        risk.id,
                        risk.title,
                        risk.owner,
                        risk.category,
                        risk.status,
                        assessment.exposure(),
                        assessment.level(),
                        risk.dueDate
                    );
                })
                .sorted(
                    Comparator.comparingInt(
                        RiskSummary::exposure
                    ).reversed()
                )
                .toList();
        }

        List<ProjectRisk> findStaleRisks(
            int maximumAgeDays
        ) {
            if (maximumAgeDays < 0) {
                throw new ValidationException(
                    "Maximum age cannot be negative"
                );
            }

            LocalDateTime cutoff =
                LocalDateTime.now().minusDays(maximumAgeDays);

            return repository.findAll().stream()
                .filter(risk ->
                    risk.status != RiskStatus.CLOSED
                )
                .filter(risk ->
                    risk.lastReviewed == null ||
                    risk.lastReviewed.isBefore(cutoff)
                )
                .toList();
        }

        List<ProjectRisk> findOverdueRisks(
            LocalDate asOf
        ) {
            Objects.requireNonNull(asOf);

            return repository.findAll().stream()
                .filter(risk ->
                    risk.status != RiskStatus.CLOSED
                )
                .filter(risk ->
                    risk.dueDate.isBefore(asOf)
                )
                .toList();
        }

        PortfolioReport portfolioReport(
            LocalDate asOf
        ) {
            List<ProjectRisk> all = repository.findAll();

            Map<RiskLevel, Long> levels =
                new EnumMap<>(RiskLevel.class);

            Map<RiskStatus, Long> statuses =
                new EnumMap<>(RiskStatus.class);

            Map<RiskCategory, Long> categories =
                new EnumMap<>(RiskCategory.class);

            int active = 0;
            int overdue = 0;
            int totalExposure = 0;

            for (ProjectRisk risk : all) {
                Assessment assessment =
                    assessmentPolicy.evaluate(
                        risk.probability,
                        risk.impact
                    );

                levels.merge(
                    assessment.level(),
                    1L,
                    Long::sum
                );

                statuses.merge(
                    risk.status,
                    1L,
                    Long::sum
                );

                categories.merge(
                    risk.category,
                    1L,
                    Long::sum
                );

                totalExposure += assessment.exposure();

                if (risk.status != RiskStatus.CLOSED) {
                    active++;

                    if (risk.dueDate.isBefore(asOf)) {
                        overdue++;
                    }
                }
            }

            double average = all.isEmpty()
                ? 0.0
                : (double) totalExposure / all.size();

            return new PortfolioReport(
                all.size(),
                active,
                overdue,
                totalExposure,
                average,
                Map.copyOf(levels),
                Map.copyOf(statuses),
                Map.copyOf(categories)
            );
        }
    }

    // ---------------------------------------------------------
    // Application entry point
    // ---------------------------------------------------------

    public static void main(String[] args) {

        RiskRepository repository =
            new InMemoryRiskRepository();

        AssessmentPolicy policy =
            new ProbabilityImpactPolicy(4, 9, 16);

        RiskManagementService service =
            new RiskManagementService(repository, policy);

        ProjectRisk supplier = service.register(
            "PRJ-2026-001",
            "Supplier delivery delay",
            "Hardware may not arrive before the milestone.",
            RiskCategory.SCHEDULE,
            "Procurement Manager",
            4,
            4,
            LocalDate.now().plusDays(15),
            RiskResponse.MITIGATE
        );

        ProjectRisk security = service.register(
            "PRJ-2026-001",
            "Unauthorized system access",
            "Access-control configuration may expose data.",
            RiskCategory.SECURITY,
            "Security Manager",
            2,
            5,
            LocalDate.now().plusDays(5),
            RiskResponse.AVOID
        );

        try {
            System.out.println(
                "INITIAL EXPOSURE: " +
                service.assess(supplier.id).exposure()
            );

            service.transition(
                supplier.id,
                RiskStatus.ASSESSED,
                supplier.version,
                "Project Manager"
            );

            service.addMitigation(
                supplier.id,
                "Qualify an alternative supplier.",
                "Use reserve inventory.",
                supplier.version,
                "Procurement Manager"
            );

            service.transition(
                supplier.id,
                RiskStatus.MONITORING,
                supplier.version,
                "Project Manager"
            );

            service.observe(
                supplier.id,
                5,
                5,
                "Supplier confirmed another delay.",
                "Procurement Manager",
                supplier.version
            );

            System.out.println("\nPRIORITY REPORT");

            service.priorityReport().forEach(summary ->
                System.out.printf(
                    "%s | %s | %s | Exposure: %d | %s%n",
                    summary.riskId(),
                    summary.title(),
                    summary.owner(),
                    summary.exposure(),
                    summary.level()
                )
            );

            PortfolioReport report =
                service.portfolioReport(LocalDate.now());

            System.out.println("\nPORTFOLIO REPORT");
            System.out.println(report);

            System.out.println("\nSTALE RISKS: " +
                service.findStaleRisks(7).size());

            System.out.println("\nOVERDUE RISKS: " +
                service.findOverdueRisks(
                    LocalDate.now()
                ).size());

            System.out.println(
                "\nPROJECT RISK COUNT: " +
                repository.findByProject(
                    "PRJ-2026-001"
                ).size()
            );

            System.out.println(
                "\nAUDIT EVENTS: " +
                supplier.getAuditTrail().size()
            );

            // Version conflict demonstration.
            try {
                service.transition(
                    security.id,
                    RiskStatus.ASSESSED,
                    99,
                    "Project Manager"
                );
            } catch (VersionConflictException exception) {
                System.err.println(
                    "Expected version failure: " +
                    exception.getMessage()
                );
            }

            // Invalid assessment demonstration.
            try {
                policy.evaluate(8, 3);
            } catch (ValidationException exception) {
                System.err.println(
                    "Expected validation failure: " +
                    exception.getMessage()
                );
            }

        } catch (RiskException exception) {
            System.err.println(
                "Risk-management failure: " +
                exception.getMessage()
            );
        }
    }
}
