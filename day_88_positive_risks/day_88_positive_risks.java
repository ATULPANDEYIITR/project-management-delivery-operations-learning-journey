import java.util.*;
import java.util.stream.Collectors;

/*
 * POSITIVE RISKS: ENTERPRISE PROJECT OPPORTUNITY GOVERNANCE
 *
 * Enterprise-oriented domain implementation featuring:
 * - Immutable opportunity assessment inputs
 * - Probability and impact evaluation
 * - Expected Monetary Value
 * - Opportunity response strategies
 * - Ownership and accountability
 * - Workflow state transitions
 * - Portfolio reporting
 * - Policy-driven response eligibility
 * - Custom validation and business exceptions
 */

public class ProjectOpportunityManagement {

    enum Category {
        COST, SCHEDULE, QUALITY, TECHNOLOGY,
        RESOURCE, BUSINESS, STRATEGIC
    }

    enum Strategy {
        EXPLOIT, ENHANCE, SHARE, ACCEPT
    }

    enum Status {
        IDENTIFIED, ASSESSED, PLANNED,
        IN_PROGRESS, REALIZED, CLOSED
    }

    record Assessment(
        double probability,
        double impact,
        double responseCost,
        double confidence
    ) {
        Assessment {
            if (!Double.isFinite(probability) ||
                probability < 0 || probability > 1) {
                throw new IllegalArgumentException(
                    "Probability must be between 0 and 1."
                );
            }

            if (!Double.isFinite(impact) || impact < 0 ||
                !Double.isFinite(responseCost) || responseCost < 0) {
                throw new IllegalArgumentException(
                    "Financial values must be non-negative."
                );
            }

            if (!Double.isFinite(confidence) ||
                confidence <= 0 || confidence > 1) {
                throw new IllegalArgumentException(
                    "Confidence must be greater than 0 and at most 1."
                );
            }
        }

        double emv() {
            return probability * impact;
        }

        double netValue() {
            return emv() - responseCost;
        }

        double adjustedValue() {
            return netValue() * confidence;
        }
    }

    record OpportunityPolicy(
        Set<Strategy> permittedStrategies,
        double minimumProbability,
        double minimumNetValue,
        boolean requirePositiveNetValue
    ) {
        OpportunityPolicy {
            permittedStrategies = Set.copyOf(permittedStrategies);

            if (minimumProbability < 0 ||
                minimumProbability > 1 ||
                !Double.isFinite(minimumNetValue)) {
                throw new IllegalArgumentException(
                    "Invalid opportunity policy."
                );
            }
        }

        void validate(Opportunity opportunity) {
            if (!permittedStrategies.contains(opportunity.strategy())) {
                throw new PolicyViolationException(
                    "Response strategy is not permitted."
                );
            }

            if (opportunity.assessment().probability()
                < minimumProbability) {
                throw new PolicyViolationException(
                    "Probability is below the policy threshold."
                );
            }

            if (opportunity.assessment().netValue()
                < minimumNetValue) {
                throw new PolicyViolationException(
                    "Net expected value is below the threshold."
                );
            }

            if (requirePositiveNetValue &&
                opportunity.assessment().netValue() <= 0) {
                throw new PolicyViolationException(
                    "Positive net expected value is required."
                );
            }
        }
    }

    static class BusinessException extends RuntimeException {
        BusinessException(String message) {
            super(message);
        }
    }

    static class PolicyViolationException extends BusinessException {
        PolicyViolationException(String message) {
            super(message);
        }
    }

    static class Opportunity {

        private final String id;
        private final String title;
        private final String owner;
        private final String description;
        private final Category category;
        private final Strategy strategy;
        private final Assessment assessment;

        private Status status = Status.IDENTIFIED;
        private String responseAction = "";
        private double realizedBenefit;
        private final List<String> auditLog = new ArrayList<>();

        Opportunity(
            String id,
            String title,
            String description,
            String owner,
            Category category,
            Strategy strategy,
            Assessment assessment
        ) {
            this.id = Objects.requireNonNull(id).trim();
            this.title = Objects.requireNonNull(title).trim();
            this.description = Objects.requireNonNull(description).trim();
            this.owner = Objects.requireNonNull(owner).trim();
            this.category = Objects.requireNonNull(category);
            this.strategy = Objects.requireNonNull(strategy);
            this.assessment = Objects.requireNonNull(assessment);

            if (this.id.isEmpty() ||
                this.title.isEmpty() ||
                this.owner.isEmpty()) {
                throw new IllegalArgumentException(
                    "ID, title, and owner are mandatory."
                );
            }

            log("Opportunity identified");
        }

        String id() {
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

        Strategy strategy() {
            return strategy;
        }

        Assessment assessment() {
            return assessment;
        }

        Status status() {
            return status;
        }

        double realizedBenefit() {
            return realizedBenefit;
        }

        List<String> auditLog() {
            return List.copyOf(auditLog);
        }

        void transition(Status expected, Status next, String event) {
            if (status != expected) {
                throw new BusinessException(
                    "Invalid transition for " + id +
                    ": expected " + expected + ", found " + status
                );
            }

            status = next;
            log(event);
        }

        void plan(String action) {
            if (status != Status.IDENTIFIED &&
                status != Status.ASSESSED) {
                throw new BusinessException(
                    "Response planning is not permitted."
                );
            }

            if (action == null || action.isBlank()) {
                throw new IllegalArgumentException(
                    "Response action is required."
                );
            }

            responseAction = action.trim();
            status = Status.PLANNED;
            log("Response plan established");
        }

        void realize(double benefit) {
            if (status != Status.IN_PROGRESS) {
                throw new BusinessException(
                    "Opportunity is not in progress."
                );
            }

            if (!Double.isFinite(benefit) || benefit < 0) {
                throw new IllegalArgumentException(
                    "Invalid realized benefit."
                );
            }

            realizedBenefit = benefit;
            transition(
                Status.IN_PROGRESS,
                Status.REALIZED,
                "Opportunity realized"
            );
        }

        void log(String event) {
            auditLog.add(
                java.time.Instant.now() + " | " + event
            );
        }
    }

    static class OpportunityService {

        private final Map<String, Opportunity> register =
            new LinkedHashMap<>();

        private final OpportunityPolicy policy;

        OpportunityService(OpportunityPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void register(Opportunity opportunity) {
            Objects.requireNonNull(opportunity);

            if (register.containsKey(opportunity.id())) {
                throw new BusinessException(
                    "Duplicate opportunity identifier."
                );
            }

            register.put(opportunity.id(), opportunity);
        }

        Opportunity get(String id) {
            Opportunity opportunity = register.get(id);

            if (opportunity == null) {
                throw new BusinessException(
                    "Opportunity not found: " + id
                );
            }

            return opportunity;
        }

        void assess(String id) {
            Opportunity opportunity = get(id);

            policy.validate(opportunity);

            opportunity.transition(
                Status.IDENTIFIED,
                Status.ASSESSED,
                "Opportunity assessed and policy validated"
            );
        }

        void plan(String id, String action) {
            get(id).plan(action);
        }

        void execute(String id) {
            get(id).transition(
                Status.PLANNED,
                Status.IN_PROGRESS,
                "Response execution started"
            );
        }

        void realize(String id, double benefit) {
            get(id).realize(benefit);
        }

        void close(String id) {
            Opportunity opportunity = get(id);

            if (opportunity.status() != Status.REALIZED &&
                opportunity.status() != Status.IDENTIFIED &&
                opportunity.status() != Status.ASSESSED) {
                throw new BusinessException(
                    "Opportunity cannot be closed in this state."
                );
            }

            Status previous = opportunity.status();

            opportunity.transition(
                previous,
                Status.CLOSED,
                "Opportunity closed"
            );
        }

        List<Opportunity> prioritize() {
            return register.values().stream()
                .sorted(
                    Comparator.comparingDouble(
                        (Opportunity opportunity) ->
                            opportunity.assessment().adjustedValue()
                    ).reversed()
                )
                .toList();
        }

        Map<String, Double> portfolioMetrics() {
            double emv = register.values().stream()
                .mapToDouble(o -> o.assessment().emv())
                .sum();

            double cost = register.values().stream()
                .mapToDouble(o -> o.assessment().responseCost())
                .sum();

            double realized = register.values().stream()
                .mapToDouble(Opportunity::realizedBenefit)
                .sum();

            Map<String, Double> metrics = new LinkedHashMap<>();
            metrics.put("Expected Monetary Value", emv);
            metrics.put("Response Cost", cost);
            metrics.put("Net Expected Value", emv - cost);
            metrics.put("Realized Benefits", realized);

            return Collections.unmodifiableMap(metrics);
        }

        Map<Status, Long> statusDistribution() {
            return register.values().stream()
                .collect(Collectors.groupingBy(
                    Opportunity::status,
                    () -> new EnumMap<>(Status.class),
                    Collectors.counting()
                ));
        }
    }

    public static void main(String[] args) {

        OpportunityPolicy policy = new OpportunityPolicy(
            EnumSet.allOf(Strategy.class),
            0.40,
            0,
            true
        );

        OpportunityService service =
            new OpportunityService(policy);

        service.register(new Opportunity(
            "OPP-201",
            "Process Automation",
            "Automate recurring reporting activities.",
            "Project Manager",
            Category.COST,
            Strategy.EXPLOIT,
            new Assessment(0.85, 200000, 25000, 0.95)
        ));

        service.register(new Opportunity(
            "OPP-202",
            "Accelerated Delivery",
            "Parallelize development activities.",
            "Delivery Lead",
            Category.SCHEDULE,
            Strategy.ENHANCE,
            new Assessment(0.70, 150000, 15000, 0.90)
        ));

        service.register(new Opportunity(
            "OPP-203",
            "Technology Partnership",
            "Joint technology delivery with a partner.",
            "Business Director",
            Category.STRATEGIC,
            Strategy.SHARE,
            new Assessment(0.60, 300000, 30000, 0.85)
        ));

        service.register(new Opportunity(
            "OPP-204",
            "Cloud Optimization",
            "Improve infrastructure efficiency.",
            "Cloud Architect",
            Category.TECHNOLOGY,
            Strategy.ACCEPT,
            new Assessment(0.75, 100000, 0, 0.95)
        ));

        service.assess("OPP-201");
        service.plan(
            "OPP-201",
            "Automate reporting and verify realized savings."
        );
        service.execute("OPP-201");
        service.realize("OPP-201", 175000);

        System.out.println("OPPORTUNITY PRIORITIZATION");

        for (Opportunity opportunity : service.prioritize()) {
            System.out.printf(
                "%s | %-25s | EMV: %.2f | Net EV: %.2f%n",
                opportunity.id(),
                opportunity.title(),
                opportunity.assessment().emv(),
                opportunity.assessment().netValue()
            );
        }

        System.out.println("\nPORTFOLIO METRICS");

        service.portfolioMetrics().forEach(
            (name, value) ->
                System.out.printf("%s: %.2f%n", name, value)
        );

        System.out.println("\nSTATUS DISTRIBUTION");
        System.out.println(service.statusDistribution());

        try {
            service.execute("OPP-202");
        } catch (BusinessException error) {
            System.out.println(
                "Expected workflow rejection: " + error.getMessage()
            );
        }

        try {
            service.register(new Opportunity(
                "OPP-205",
                "Low Value Proposal",
                "An opportunity that does not meet financial policy.",
                "Project Analyst",
                Category.BUSINESS,
                Strategy.ACCEPT,
                new Assessment(0.20, 1000, 2000, 0.90)
            ));

            service.assess("OPP-205");

        } catch (PolicyViolationException error) {
            System.out.println(
                "Expected policy rejection: " + error.getMessage()
            );
        }
    }
}
