import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

public class CostVarianceEnterprise {

    private static final BigDecimal HUNDRED = new BigDecimal("100");

    enum VarianceStatus {
        FAVORABLE,
        UNFAVORABLE,
        ON_PLAN
    }

    enum CostState {
        PLANNED,
        PARTIALLY_ACTUALIZED,
        ACTUALIZED
    }

    record CostPosting(
            String source,
            BigDecimal amount,
            String description
    ) {
        CostPosting {
            Objects.requireNonNull(source, "Posting source is required.");
            Objects.requireNonNull(description, "Posting description is required.");

            if (source.isBlank()) {
                throw new IllegalArgumentException("Posting source cannot be blank.");
            }

            if (description.isBlank()) {
                throw new IllegalArgumentException("Posting description cannot be blank.");
            }

            if (amount == null || amount.signum() <= 0) {
                throw new IllegalArgumentException(
                        "A cost posting must be greater than zero."
                );
            }

            amount = amount.setScale(2, RoundingMode.HALF_UP);
        }
    }

    static final class CostBudgetLine {
        private final String category;
        private final BigDecimal plannedCost;
        private final List<CostPosting> postings = new ArrayList<>();

        CostBudgetLine(String category, BigDecimal plannedCost) {
            if (category == null || category.isBlank()) {
                throw new IllegalArgumentException("Category is required.");
            }

            if (plannedCost == null || plannedCost.signum() < 0) {
                throw new IllegalArgumentException(
                        "Planned cost cannot be negative."
                );
            }

            this.category = category;
            this.plannedCost = normalize(plannedCost);
        }

        void post(CostPosting posting) {
            Objects.requireNonNull(posting, "Posting is required.");
            postings.add(posting);
        }

        String category() {
            return category;
        }

        BigDecimal plannedCost() {
            return plannedCost;
        }

        BigDecimal actualCost() {
            return normalize(
                    postings.stream()
                            .map(CostPosting::amount)
                            .reduce(BigDecimal.ZERO, BigDecimal::add)
            );
        }

        BigDecimal variance() {
            return normalize(actualCost().subtract(plannedCost));
        }

        Optional<BigDecimal> variancePercentage() {
            if (plannedCost.signum() == 0) {
                return Optional.empty();
            }

            return Optional.of(
                    normalize(
                            variance()
                                    .divide(plannedCost, 8, RoundingMode.HALF_UP)
                                    .multiply(HUNDRED)
                    )
            );
        }

        VarianceStatus status() {
            int comparison = actualCost().compareTo(plannedCost);

            if (comparison > 0) {
                return VarianceStatus.UNFAVORABLE;
            }

            if (comparison < 0) {
                return VarianceStatus.FAVORABLE;
            }

            return VarianceStatus.ON_PLAN;
        }

        CostState state() {
            if (postings.isEmpty()) {
                return CostState.PLANNED;
            }

            if (actualCost().compareTo(plannedCost) < 0) {
                return CostState.PARTIALLY_ACTUALIZED;
            }

            return CostState.ACTUALIZED;
        }

        List<CostPosting> postings() {
            return List.copyOf(postings);
        }
    }

    interface VariancePolicy {
        boolean requiresInvestigation(CostBudgetLine line);

        String explanation(CostBudgetLine line);
    }

    static final class MaterialVariancePolicy implements VariancePolicy {
        private final BigDecimal thresholdPercentage;

        MaterialVariancePolicy(BigDecimal thresholdPercentage) {
            if (thresholdPercentage == null
                    || thresholdPercentage.signum() < 0) {
                throw new IllegalArgumentException(
                        "Threshold percentage cannot be negative."
                );
            }

            this.thresholdPercentage = thresholdPercentage;
        }

        @Override
        public boolean requiresInvestigation(CostBudgetLine line) {
            Optional<BigDecimal> rate = line.variancePercentage();

            return rate.isPresent()
                    && rate.get().abs().compareTo(thresholdPercentage) > 0;
        }

        @Override
        public String explanation(CostBudgetLine line) {
            if (line.status() == VarianceStatus.UNFAVORABLE) {
                return "Actual expenditure exceeds the approved baseline.";
            }

            if (line.status() == VarianceStatus.FAVORABLE) {
                return "Actual expenditure is below the approved baseline.";
            }

            return "Actual expenditure matches the approved baseline.";
        }
    }

    static final class CostVarianceService {
        private final List<CostBudgetLine> lines = new ArrayList<>();
        private final VariancePolicy policy;

        CostVarianceService(VariancePolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        void register(CostBudgetLine line) {
            boolean duplicate = lines.stream()
                    .anyMatch(existing ->
                            existing.category().equalsIgnoreCase(line.category()));

            if (duplicate) {
                throw new IllegalArgumentException(
                        "Duplicate cost category: " + line.category()
                );
            }

            lines.add(line);
        }

        BigDecimal plannedTotal() {
            return normalize(
                    lines.stream()
                            .map(CostBudgetLine::plannedCost)
                            .reduce(BigDecimal.ZERO, BigDecimal::add)
            );
        }

        BigDecimal actualTotal() {
            return normalize(
                    lines.stream()
                            .map(CostBudgetLine::actualCost)
                            .reduce(BigDecimal.ZERO, BigDecimal::add)
            );
        }

        BigDecimal totalVariance() {
            return normalize(actualTotal().subtract(plannedTotal()));
        }

        Optional<BigDecimal> totalVariancePercentage() {
            if (plannedTotal().signum() == 0) {
                return Optional.empty();
            }

            return Optional.of(
                    normalize(
                            totalVariance()
                                    .divide(
                                            plannedTotal(),
                                            8,
                                            RoundingMode.HALF_UP
                                    )
                                    .multiply(HUNDRED)
                    )
            );
        }

        List<CostBudgetLine> materialVariances() {
            return lines.stream()
                    .filter(policy::requiresInvestigation)
                    .sorted(
                            Comparator.comparing(
                                    CostBudgetLine::variance,
                                    Comparator.reverseOrder()
                            )
                    )
                    .toList();
        }

        List<CostBudgetLine> lines() {
            return List.copyOf(lines);
        }

        void printReport() {
            System.out.println("\nENTERPRISE COST VARIANCE REPORT");
            System.out.println("=".repeat(90));

            for (CostBudgetLine line : lines) {
                String rate = line.variancePercentage()
                        .map(value -> value + "%")
                        .orElse("n/a");

                System.out.printf(
                        "%-26s planned=%10s actual=%10s variance=%10s rate=%9s state=%s%n",
                        line.category(),
                        line.plannedCost(),
                        line.actualCost(),
                        line.variance(),
                        rate,
                        line.state()
                );
            }

            System.out.println("-".repeat(90));
            System.out.printf(
                    "TOTAL planned=%s actual=%s variance=%s rate=%s%n",
                    plannedTotal(),
                    actualTotal(),
                    totalVariance(),
                    totalVariancePercentage()
                            .map(value -> value + "%")
                            .orElse("n/a")
            );

            System.out.println("\nMATERIAL VARIANCES");
            for (CostBudgetLine line : materialVariances()) {
                System.out.printf(
                        "%s: %s%n",
                        line.category(),
                        policy.explanation(line)
                );
            }
        }
    }

    private static BigDecimal normalize(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }

    private static BigDecimal cost(String value) {
        return normalize(new BigDecimal(value));
    }

    private static void demonstratePolicyBoundaries() {
        System.out.println("\nPOLICY BOUNDARY CASES");
        System.out.println("=".repeat(90));

        VariancePolicy policy = new MaterialVariancePolicy(cost("10"));

        CostBudgetLine smallDeviation =
                new CostBudgetLine("Minor cloud variance", cost("1000"));
        smallDeviation.post(
                new CostPosting(
                        "cloud-billing",
                        cost("1080"),
                        "Small usage increase"
                )
        );

        CostBudgetLine materialDeviation =
                new CostBudgetLine("Material cloud variance", cost("1000"));
        materialDeviation.post(
                new CostPosting(
                        "cloud-billing",
                        cost("1200"),
                        "Unexpected workload expansion"
                )
        );

        System.out.println(
                "Minor deviation requires investigation: "
                        + policy.requiresInvestigation(smallDeviation)
        );

        System.out.println(
                "Material deviation requires investigation: "
                        + policy.requiresInvestigation(materialDeviation)
        );

        CostBudgetLine zeroBaseline =
                new CostBudgetLine("Emergency activity", cost("0"));
        zeroBaseline.post(
                new CostPosting(
                        "operations",
                        cost("250"),
                        "Unplanned emergency work"
                )
        );

        System.out.println(
                "Zero-baseline variance: " + zeroBaseline.variance()
        );
        System.out.println(
                "Zero-baseline percentage: "
                        + zeroBaseline.variancePercentage()
        );
    }

    public static void main(String[] args) {
        try {
            VariancePolicy policy = new MaterialVariancePolicy(cost("10"));
            CostVarianceService service = new CostVarianceService(policy);

            CostBudgetLine cloud =
                    new CostBudgetLine("Cloud infrastructure", cost("12000"));
            cloud.post(
                    new CostPosting(
                            "cloud-metering",
                            cost("13800"),
                            "Compute, storage and network usage"
                    )
            );

            CostBudgetLine contractors =
                    new CostBudgetLine("External contractors", cost("30000"));
            contractors.post(
                    new CostPosting(
                            "accounts-payable",
                            cost("28750"),
                            "Monthly delivery invoice"
                    )
            );

            CostBudgetLine testing =
                    new CostBudgetLine("Testing services", cost("8000"));
            testing.post(
                    new CostPosting(
                            "test-vendor",
                            cost("9200"),
                            "Performance and resilience testing"
                    )
            );

            CostBudgetLine security =
                    new CostBudgetLine("Security tooling", cost("6500"));
            security.post(
                    new CostPosting(
                            "procurement",
                            cost("6100"),
                            "Annual security platform charge"
                    )
            );

            CostBudgetLine travel =
                    new CostBudgetLine("Travel", cost("3500"));
            travel.post(
                    new CostPosting(
                            "expense-system",
                            cost("4200"),
                            "Project workshops"
                    )
            );

            service.register(cloud);
            service.register(contractors);
            service.register(testing);
            service.register(security);
            service.register(travel);

            service.printReport();
            demonstratePolicyBoundaries();

        } catch (IllegalArgumentException | ArithmeticException error) {
            System.err.println(
                    "Cost variance processing failed: " + error.getMessage()
            );
            System.exit(1);
        }
    }
}
