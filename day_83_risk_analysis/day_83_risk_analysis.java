import java.util.*;
import java.util.stream.Collectors;

/**
 * Risk Analysis Enterprise Management System
 *
 * Java 17 implementation covering:
 * - Enterprise risk identification
 * - Probability and impact assessment
 * - Expected financial exposure
 * - Inherent and residual risk
 * - Risk treatment policies
 * - Approval-based risk acceptance
 * - Immutable assessment records
 * - Risk register and prioritization
 * - Portfolio analysis
 * - Monte Carlo simulation
 *
 * Compile:
 *   javac RiskAnalysis.java
 *
 * Run:
 *   java RiskAnalysis
 */
public class RiskAnalysis {

    enum Category {
        STRATEGIC,
        FINANCIAL,
        OPERATIONAL,
        TECHNOLOGY,
        SECURITY,
        COMPLIANCE,
        REPUTATIONAL
    }

    enum Status {
        IDENTIFIED,
        ASSESSED,
        MITIGATING,
        PENDING_APPROVAL,
        ACCEPTED,
        CLOSED
    }

    enum Treatment {
        ACCEPT,
        MITIGATE,
        TRANSFER,
        AVOID
    }

    enum Level {
        LOW,
        MODERATE,
        HIGH,
        CRITICAL
    }

    enum ApprovalStatus {
        PENDING,
        APPROVED,
        REJECTED
    }


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
        RiskNotFoundException(String id) {
            super("Risk not found: " + id);
        }
    }

    static class PolicyViolationException extends RiskException {
        PolicyViolationException(String message) {
            super(message);
        }
    }


    record RiskControl(
        String name,
        double probabilityReduction,
        double impactReduction
    ) {
        RiskControl {
            if (name == null || name.isBlank()) {
                throw new ValidationException(
                    "Control name is required."
                );
            }

            validateProbability(probabilityReduction);
            validateProbability(impactReduction);
        }
    }


    record Assessment(
        double probability,
        double impact,
        String assessor,
        String rationale,
        long assessmentTime
    ) {
        Assessment {
            validateProbability(probability);
            validateImpact(impact);

            if (assessor == null || assessor.isBlank()) {
                throw new ValidationException(
                    "Assessor is required."
                );
            }

            if (rationale == null || rationale.isBlank()) {
                throw new ValidationException(
                    "Assessment rationale is required."
                );
            }
        }
    }


    record Approval(
        String approver,
        ApprovalStatus status,
        String justification
    ) {
        Approval {
            if (approver == null || approver.isBlank()) {
                throw new ValidationException(
                    "Approver is required."
                );
            }

            if (justification == null || justification.isBlank()) {
                throw new ValidationException(
                    "Approval justification is required."
                );
            }
        }
    }


    record Policy(
        double maximumAcceptableExposure,
        double maximumAcceptableProbability,
        boolean requiresApprovalAboveThreshold
    ) {
        Policy {
            validateImpact(maximumAcceptableExposure);
            validateProbability(maximumAcceptableProbability);
        }

        boolean requiresMitigation(Risk risk) {
            return
                risk.residualExposure() >
                    maximumAcceptableExposure ||
                risk.residualProbability() >
                    maximumAcceptableProbability;
        }
    }


    record RiskReport(
        String riskId,
        String title,
        Category category,
        double inherentExposure,
        double residualExposure,
        double residualProbability,
        double residualImpact,
        Level level,
        Status status,
        Treatment treatment
    ) {}


    static void validateProbability(double probability) {
        if (
            !Double.isFinite(probability) ||
            probability < 0 ||
            probability > 1
        ) {
            throw new ValidationException(
                "Probability must be between 0 and 1."
            );
        }
    }

    static void validateImpact(double impact) {
        if (!Double.isFinite(impact) || impact < 0) {
            throw new ValidationException(
                "Impact must be a non-negative finite value."
            );
        }
    }


    static class Risk {

        private final String id;
        private final String title;
        private final Category category;
        private final String owner;

        private double probability;
        private double impact;

        private Status status;
        private Treatment treatment;

        private final List<RiskControl> controls;
        private final List<Assessment> assessmentHistory;

        private Approval approval;

        private long version;

        Risk(
            String id,
            String title,
            Category category,
            double probability,
            double impact,
            String owner
        ) {
            if (
                id == null || id.isBlank() ||
                title == null || title.isBlank() ||
                owner == null || owner.isBlank()
            ) {
                throw new ValidationException(
                    "Risk ID, title, and owner are required."
                );
            }

            this.id = id;
            this.title = title;
            this.category = Objects.requireNonNull(category);
            this.owner = owner;

            validateProbability(probability);
            validateImpact(impact);

            this.probability = probability;
            this.impact = impact;

            this.status = Status.IDENTIFIED;
            this.treatment = null;

            this.controls = new ArrayList<>();
            this.assessmentHistory = new ArrayList<>();

            this.approval = null;
            this.version = 1;
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

        Treatment treatment() {
            return treatment;
        }

        long version() {
            return version;
        }

        double probability() {
            return probability;
        }

        double impact() {
            return impact;
        }

        double inherentExposure() {
            return probability * impact;
        }

        double residualProbability() {
            double remaining = 1.0;

            for (RiskControl control : controls) {
                remaining *=
                    1 - control.probabilityReduction();
            }

            return probability * remaining;
        }

        double residualImpact() {
            double remaining = 1.0;

            for (RiskControl control : controls) {
                remaining *=
                    1 - control.impactReduction();
            }

            return impact * remaining;
        }

        double residualExposure() {
            return residualProbability() * residualImpact();
        }

        double mitigationPercentage() {
            if (inherentExposure() == 0) {
                return 0;
            }

            return (
                1 - residualExposure() / inherentExposure()
            ) * 100;
        }

        Level level() {
            double exposure = residualExposure();

            if (exposure >= 100000) {
                return Level.CRITICAL;
            }

            if (exposure >= 25000) {
                return Level.HIGH;
            }

            if (exposure >= 5000) {
                return Level.MODERATE;
            }

            return Level.LOW;
        }

        void addControl(RiskControl control) {
            Objects.requireNonNull(control);

            boolean duplicate = controls.stream()
                .anyMatch(existing ->
                    existing.name().equalsIgnoreCase(control.name())
                );

            if (duplicate) {
                throw new ValidationException(
                    "Duplicate control."
                );
            }

            controls.add(control);
            status = Status.MITIGATING;
            version++;
        }

        void recordAssessment(
            Assessment assessment,
            long expectedVersion
        ) {
            if (version != expectedVersion) {
                throw new RiskException(
                    "Concurrent modification detected."
                );
            }

            Objects.requireNonNull(assessment);

            probability = assessment.probability();
            impact = assessment.impact();

            assessmentHistory.add(assessment);

            status = Status.ASSESSED;
            version++;
        }

        void requestAcceptance() {
            if (status == Status.CLOSED) {
                throw new PolicyViolationException(
                    "Closed risks cannot be accepted."
                );
            }

            status = Status.PENDING_APPROVAL;
            version++;
        }

        void approveAcceptance(
            Approval approval,
            Policy policy
        ) {
            Objects.requireNonNull(approval);

            if (status != Status.PENDING_APPROVAL) {
                throw new PolicyViolationException(
                    "Risk is not awaiting approval."
                );
            }

            if (approval.status() == ApprovalStatus.REJECTED) {
                this.approval = approval;
                status = Status.MITIGATING;
                version++;
                return;
            }

            if (policy.requiresMitigation(this)) {
                throw new PolicyViolationException(
                    "Risk exceeds the acceptance policy."
                );
            }

            this.approval = approval;
            treatment = Treatment.ACCEPT;
            status = Status.ACCEPTED;
            version++;
        }

        void applyTreatment(
            Treatment treatment,
            Policy policy
        ) {
            Objects.requireNonNull(treatment);

            if (treatment == Treatment.ACCEPT) {
                requestAcceptance();
                return;
            }

            if (treatment == Treatment.AVOID) {
                this.treatment = treatment;
                status = Status.CLOSED;
            } else if (treatment == Treatment.MITIGATE) {
                this.treatment = treatment;
                status = Status.MITIGATING;
            } else if (treatment == Treatment.TRANSFER) {
                this.treatment = treatment;
                status = Status.ASSESSED;
            }

            version++;
        }

        RiskReport report() {
            return new RiskReport(
                id,
                title,
                category,
                inherentExposure(),
                residualExposure(),
                residualProbability(),
                residualImpact(),
                level(),
                status,
                treatment
            );
        }
    }


    interface RiskRepository {
        void save(Risk risk);
        Risk findById(String id);
        List<Risk> findAll();
    }


    static class InMemoryRiskRepository
        implements RiskRepository {

        private final Map<String, Risk> records =
            new LinkedHashMap<>();

        @Override
        public void save(Risk risk) {
            Objects.requireNonNull(risk);

            if (records.containsKey(risk.id())) {
                throw new ValidationException(
                    "Duplicate risk ID: " + risk.id()
                );
            }

            records.put(risk.id(), risk);
        }

        @Override
        public Risk findById(String id) {
            Risk risk = records.get(id);

            if (risk == null) {
                throw new RiskNotFoundException(id);
            }

            return risk;
        }

        @Override
        public List<Risk> findAll() {
            return List.copyOf(records.values());
        }
    }


    static class RiskAssessmentService {

        private final RiskRepository repository;

        RiskAssessmentService(RiskRepository repository) {
            this.repository = Objects.requireNonNull(repository);
        }

        Risk assess(
            String id,
            Assessment assessment,
            long expectedVersion
        ) {
            Risk risk = repository.findById(id);

            risk.recordAssessment(
                assessment,
                expectedVersion
            );

            return risk;
        }

        List<RiskReport> prioritize() {
            return repository.findAll()
                .stream()
                .map(Risk::report)
                .sorted(
                    Comparator.comparingDouble(
                        RiskReport::residualExposure
                    ).reversed()
                )
                .toList();
        }

        Map<Level, Long> distribution() {
            return repository.findAll()
                .stream()
                .collect(
                    Collectors.groupingBy(
                        Risk::level,
                        () -> new EnumMap<>(Level.class),
                        Collectors.counting()
                    )
                );
        }

        double portfolioInherentExposure() {
            return repository.findAll()
                .stream()
                .mapToDouble(Risk::inherentExposure)
                .sum();
        }

        double portfolioResidualExposure() {
            return repository.findAll()
                .stream()
                .mapToDouble(Risk::residualExposure)
                .sum();
        }

        List<RiskReport> findByCategory(Category category) {
            return repository.findAll()
                .stream()
                .filter(risk -> risk.category() == category)
                .map(Risk::report)
                .toList();
        }
    }


    static class MonteCarloEngine {

        private final Random random;

        MonteCarloEngine(long seed) {
            this.random = new Random(seed);
        }

        Map<String, Double> simulate(
            List<Risk> risks,
            int iterations
        ) {
            if (iterations <= 0) {
                throw new ValidationException(
                    "Iterations must be positive."
                );
            }

            double[] losses = new double[iterations];

            for (int i = 0; i < iterations; i++) {
                double total = 0;

                for (Risk risk : risks) {
                    if (random.nextDouble() <
                        risk.residualProbability()) {
                        total += risk.residualImpact();
                    }
                }

                losses[i] = total;
            }

            Arrays.sort(losses);

            double mean = Arrays.stream(losses)
                .average()
                .orElse(0);

            return Map.of(
                "meanLoss", mean,
                "medianLoss", percentile(losses, 0.50),
                "p95Loss", percentile(losses, 0.95),
                "p99Loss", percentile(losses, 0.99),
                "maximumLoss", losses[losses.length - 1]
            );
        }

        private double percentile(double[] values, double p) {
            int index = (int) Math.floor(
                (values.length - 1) * p
            );

            return values[index];
        }
    }


    static void runValidationTests() {

        Risk risk = new Risk(
            "TEST01",
            "Validation Risk",
            Category.OPERATIONAL,
            0.8,
            10000,
            "Test Owner"
        );

        if (Math.abs(risk.inherentExposure() - 8000) > 0.001) {
            throw new AssertionError(
                "Expected exposure calculation failed."
            );
        }

        risk.addControl(
            new RiskControl("Test Control", 0.5, 0.4)
        );

        if (Math.abs(risk.residualExposure() - 2400) > 0.001) {
            throw new AssertionError(
                "Residual exposure calculation failed."
            );
        }

        boolean rejected = false;

        try {
            new Risk(
                "INVALID",
                "Invalid Risk",
                Category.OPERATIONAL,
                1.5,
                100,
                "Owner"
            );
        } catch (ValidationException exception) {
            rejected = true;
        }

        if (!rejected) {
            throw new AssertionError(
                "Invalid probability was accepted."
            );
        }

        System.out.println("All Java validation tests passed.");
    }


    public static void main(String[] args) {

        runValidationTests();

        RiskRepository repository =
            new InMemoryRiskRepository();

        RiskAssessmentService service =
            new RiskAssessmentService(repository);

        Policy policy = new Policy(
            25000,
            0.50,
            true
        );

        Risk security = new Risk(
            "R001",
            "Cybersecurity Breach",
            Category.SECURITY,
            0.70,
            500000,
            "Security Department"
        );

        security.addControl(
            new RiskControl(
                "Multi-factor Authentication",
                0.40,
                0.10
            )
        );

        security.addControl(
            new RiskControl(
                "Security Monitoring",
                0.15,
                0.25
            )
        );

        Risk financial = new Risk(
            "R002",
            "Budget Overrun",
            Category.FINANCIAL,
            0.45,
            120000,
            "Finance Department"
        );

        financial.addControl(
            new RiskControl(
                "Monthly Budget Reviews",
                0.25,
                0.20
            )
        );

        Risk technology = new Risk(
            "R003",
            "Cloud Service Outage",
            Category.TECHNOLOGY,
            0.30,
            80000,
            "Infrastructure Team"
        );

        technology.addControl(
            new RiskControl(
                "Disaster Recovery",
                0.20,
                0.60
            )
        );

        Risk compliance = new Risk(
            "R004",
            "Regulatory Noncompliance",
            Category.COMPLIANCE,
            0.20,
            250000,
            "Compliance Officer"
        );

        repository.save(security);
        repository.save(financial);
        repository.save(technology);
        repository.save(compliance);

        System.out.println("\nRISK POLICY EVALUATION");

        for (Risk risk : repository.findAll()) {

            boolean requiresMitigation =
                policy.requiresMitigation(risk);

            System.out.printf(
                "%s | Exposure: %.2f | Decision: %s%n",
                risk.id(),
                risk.residualExposure(),
                requiresMitigation
                    ? Treatment.MITIGATE
                    : Treatment.ACCEPT
            );
        }

        System.out.println("\nASSESSMENT UPDATE");

        long currentVersion = technology.version();

        service.assess(
            "R003",
            new Assessment(
                0.35,
                90000,
                "Infrastructure Analyst",
                "Updated outage frequency and recovery cost.",
                System.currentTimeMillis()
            ),
            currentVersion
        );

        System.out.println("\nPRIORITIZED RISK REPORT");

        for (RiskReport report : service.prioritize()) {
            System.out.printf(
                "%s | %-30s | Inherent: %12.2f | " +
                "Residual: %12.2f | Level: %s%n",
                report.riskId(),
                report.title(),
                report.inherentExposure(),
                report.residualExposure(),
                report.level()
            );
        }

        System.out.println("\nPORTFOLIO METRICS");

        System.out.printf(
            "Inherent exposure: %.2f%n",
            service.portfolioInherentExposure()
        );

        System.out.printf(
            "Residual exposure: %.2f%n",
            service.portfolioResidualExposure()
        );

        System.out.println(
            "Risk distribution: " + service.distribution()
        );

        System.out.println("\nMONTE CARLO SIMULATION");

        MonteCarloEngine engine = new MonteCarloEngine(42);

        System.out.println(
            engine.simulate(repository.findAll(), 10000)
        );

        System.out.println("\nAPPROVAL WORKFLOW");

        Risk lowRisk = new Risk(
            "R005",
            "Minor Training Delay",
            Category.OPERATIONAL,
            0.05,
            1000,
            "Operations Manager"
        );

        repository.save(lowRisk);

        lowRisk.requestAcceptance();

        lowRisk.approveAcceptance(
            new Approval(
                "Risk Committee",
                ApprovalStatus.APPROVED,
                "Exposure falls within approved tolerance."
            ),
            policy
        );

        System.out.println(
            lowRisk.id() + " | " + lowRisk.status()
        );
    }
}
