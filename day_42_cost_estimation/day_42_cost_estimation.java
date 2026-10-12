import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

public class ProjectCostEstimation {

    enum CostCategory {
        LABOR,
        INFRASTRUCTURE,
        SECURITY,
        TRAINING,
        EXTERNAL
    }

    enum ProjectState {
        DRAFT,
        ESTIMATED,
        APPROVED,
        FORECASTING,
        CLOSED
    }

    record CostItem(
        String name,
        CostCategory category,
        BigDecimal quantity,
        BigDecimal unitCost
    ) {
        CostItem {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Cost item name is required."
                );
            }

            if (quantity.signum() < 0) {
                throw new IllegalArgumentException(
                    "Quantity cannot be negative."
                );
            }

            if (unitCost.signum() < 0) {
                throw new IllegalArgumentException(
                    "Unit cost cannot be negative."
                );
            }
        }

        BigDecimal total() {
            return quantity
                .multiply(unitCost)
                .setScale(2, RoundingMode.HALF_UP);
        }
    }

    record RiskEvent(
        String name,
        BigDecimal probability,
        BigDecimal impact
    ) {
        RiskEvent {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Risk name is required."
                );
            }

            if (probability.compareTo(BigDecimal.ZERO) < 0
                || probability.compareTo(BigDecimal.ONE) > 0) {
                throw new IllegalArgumentException(
                    "Risk probability must be between 0 and 1."
                );
            }

            if (impact.signum() < 0) {
                throw new IllegalArgumentException(
                    "Risk impact cannot be negative."
                );
            }
        }

        BigDecimal expectedValue() {
            return probability
                .multiply(impact)
                .setScale(2, RoundingMode.HALF_UP);
        }
    }

    record ApprovalPolicy(
        int requiredApprovals,
        boolean requireIndependentReviewer,
        boolean requirePassingChecks
    ) {
        ApprovalPolicy {
            if (requiredApprovals < 0) {
                throw new IllegalArgumentException(
                    "Required approvals cannot be negative."
                );
            }
        }
    }

    static final class ProjectEstimate {
        private final String projectName;
        private final List<CostItem> costItems = new ArrayList<>();
        private final List<RiskEvent> risks = new ArrayList<>();
        private ProjectState state = ProjectState.DRAFT;

        ProjectEstimate(String projectName) {
            if (projectName == null || projectName.isBlank()) {
                throw new IllegalArgumentException(
                    "Project name is required."
                );
            }

            this.projectName = projectName;
        }

        void addCostItem(CostItem item) {
            ensureEditable();
            costItems.add(item);
        }

        void addRisk(RiskEvent risk) {
            ensureEditable();
            risks.add(risk);
        }

        BigDecimal directCost() {
            return costItems.stream()
                .map(CostItem::total)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
        }

        BigDecimal expectedRiskCost() {
            return risks.stream()
                .map(RiskEvent::expectedValue)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_UP);
        }

        BigDecimal managementReserve(BigDecimal rate) {
            if (rate.signum() < 0
                || rate.compareTo(BigDecimal.ONE) > 0) {
                throw new IllegalArgumentException(
                    "Reserve rate must be between 0 and 1."
                );
            }

            return directCost()
                .multiply(rate)
                .setScale(2, RoundingMode.HALF_UP);
        }

        BigDecimal totalEstimate() {
            return directCost()
                .add(expectedRiskCost())
                .add(managementReserve(new BigDecimal("0.05")))
                .setScale(2, RoundingMode.HALF_UP);
        }

        Map<CostCategory, BigDecimal> costByCategory() {
            Map<CostCategory, BigDecimal> totals =
                new EnumMap<>(CostCategory.class);

            for (CostItem item : costItems) {
                totals.merge(
                    item.category(),
                    item.total(),
                    BigDecimal::add
                );
            }

            return totals;
        }

        void markEstimated() {
            requireState(ProjectState.DRAFT);
            if (costItems.isEmpty()) {
                throw new IllegalStateException(
                    "An estimate requires cost items."
                );
            }

            state = ProjectState.ESTIMATED;
        }

        void approve() {
            requireState(ProjectState.ESTIMATED);
            state = ProjectState.APPROVED;
        }

        void beginForecasting() {
            requireState(ProjectState.APPROVED);
            state = ProjectState.FORECASTING;
        }

        void close() {
            requireState(ProjectState.FORECASTING);
            state = ProjectState.CLOSED;
        }

        ProjectState state() {
            return state;
        }

        private void ensureEditable() {
            if (state != ProjectState.DRAFT
                && state != ProjectState.ESTIMATED) {
                throw new IllegalStateException(
                    "The estimate is no longer editable."
                );
            }
        }

        private void requireState(ProjectState expected) {
            if (state != expected) {
                throw new IllegalStateException(
                    "Invalid transition from "
                    + state
                    + "; expected "
                    + expected
                );
            }
        }

        void printReport() {
            System.out.println(
                "\nPROJECT COST ESTIMATION"
            );
            System.out.println(
                "Project: " + projectName
            );
            System.out.println(
                "State: " + state
            );

            System.out.println("\nCost by category:");

            costByCategory().forEach(
                (category, value) ->
                    System.out.printf(
                        "  %-18s %12.2f%n",
                        category,
                        value
                    )
            );

            System.out.printf(
                "%nDirect cost:          %12.2f%n",
                directCost()
            );

            System.out.printf(
                "Expected risk cost:   %12.2f%n",
                expectedRiskCost()
            );

            System.out.printf(
                "Management reserve:   %12.2f%n",
                managementReserve(new BigDecimal("0.05"))
            );

            System.out.printf(
                "Total estimate:       %12.2f%n",
                totalEstimate()
            );
        }
    }

    static final class MergeStyleCostModel {
        private final ApprovalPolicy policy;

        MergeStyleCostModel(ApprovalPolicy policy) {
            this.policy = policy;
        }

        boolean eligible(
            int approvals,
            boolean independentReviewerPresent,
            boolean checksPassing
        ) {
            if (approvals < policy.requiredApprovals()) {
                return false;
            }

            if (policy.requireIndependentReviewer()
                && !independentReviewerPresent) {
                return false;
            }

            return !policy.requirePassingChecks() || checksPassing;
        }
    }

    public static void main(String[] args) {
        ProjectEstimate project =
            new ProjectEstimate(
                "Public Infrastructure Monitoring Platform"
            );

        project.addCostItem(
            new CostItem(
                "Requirements analysis",
                CostCategory.LABOR,
                new BigDecimal("120"),
                new BigDecimal("90")
            )
        );

        project.addCostItem(
            new CostItem(
                "Application engineering",
                CostCategory.LABOR,
                new BigDecimal("420"),
                new BigDecimal("72")
            )
        );

        project.addCostItem(
            new CostItem(
                "Testing and quality assurance",
                CostCategory.LABOR,
                new BigDecimal("180"),
                new BigDecimal("58")
            )
        );

        project.addCostItem(
            new CostItem(
                "Cloud environment",
                CostCategory.INFRASTRUCTURE,
                new BigDecimal("12"),
                new BigDecimal("800")
            )
        );

        project.addCostItem(
            new CostItem(
                "Security validation",
                CostCategory.SECURITY,
                new BigDecimal("60"),
                new BigDecimal("105")
            )
        );

        project.addRisk(
            new RiskEvent(
                "External integration rework",
                new BigDecimal("0.25"),
                new BigDecimal("22000")
            )
        );

        project.addRisk(
            new RiskEvent(
                "Security remediation",
                new BigDecimal("0.15"),
                new BigDecimal("28000")
            )
        );

        project.markEstimated();
        project.printReport();

        project.approve();
        project.beginForecasting();

        System.out.println(
            "\nState after approval and forecasting: "
            + project.state()
        );

        ApprovalPolicy policy =
            new ApprovalPolicy(
                2,
                true,
                true
            );

        MergeStyleCostModel policyModel =
            new MergeStyleCostModel(policy);

        System.out.println(
            "Policy-compatible governance result: "
            + policyModel.eligible(
                2,
                true,
                true
            )
        );

        project.close();

        System.out.println(
            "Final project state: "
            + project.state()
        );
    }
}
