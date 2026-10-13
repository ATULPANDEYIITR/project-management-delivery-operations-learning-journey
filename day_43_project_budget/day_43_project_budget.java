import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Enterprise Project Budget Governance Model.
 *
 * Java 17+.
 *
 * The model separates:
 * - budget baseline
 * - cost categories
 * - actual spending
 * - commitments
 * - contingency
 * - approved changes
 * - governance state
 * - budget health
 */
public class ProjectBudgetApp {

    enum BudgetState {
        DRAFT,
        APPROVED,
        ACTIVE,
        CLOSED
    }

    enum ChangeState {
        PROPOSED,
        APPROVED,
        REJECTED
    }

    enum BudgetHealth {
        HEALTHY,
        WATCH,
        CRITICAL,
        OVER_BUDGET
    }

    enum CostCategory {
        PERSONNEL,
        CLOUD,
        SOFTWARE,
        TESTING,
        TRAINING,
        SECURITY
    }

    static final class BudgetException extends RuntimeException {
        BudgetException(String message) {
            super(message);
        }
    }

    static BigDecimal money(String value) {
        return new BigDecimal(value).setScale(2, RoundingMode.HALF_UP);
    }

    static BigDecimal money(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }

    static void requirePositive(BigDecimal amount, String message) {
        if (amount == null || amount.signum() <= 0) {
            throw new BudgetException(message);
        }
    }

    static final class BudgetLine {
        private final CostCategory category;
        private final String description;
        private final BigDecimal planned;

        private BigDecimal committed = money("0");
        private BigDecimal actual = money("0");

        BudgetLine(
                CostCategory category,
                String description,
                BigDecimal planned
        ) {
            this.category = Objects.requireNonNull(category);
            this.description = Objects.requireNonNull(description);
            requirePositive(
                    planned,
                    "Planned amount must be positive."
            );
            this.planned = money(planned);
        }

        void commit(BigDecimal amount) {
            requirePositive(
                    amount,
                    "Commitment must be positive."
            );
            committed = money(committed.add(amount));
        }

        void spend(BigDecimal amount) {
            requirePositive(
                    amount,
                    "Actual expense must be positive."
            );
            actual = money(actual.add(amount));
        }

        BigDecimal variance() {
            return money(planned.subtract(actual));
        }

        BigDecimal utilization() {
            if (planned.signum() == 0) {
                return money("0");
            }

            return money(
                    actual
                            .divide(planned, 6, RoundingMode.HALF_UP)
                            .multiply(money("100"))
            );
        }

        CostCategory category() {
            return category;
        }

        String description() {
            return description;
        }

        BigDecimal planned() {
            return planned;
        }

        BigDecimal committed() {
            return committed;
        }

        BigDecimal actual() {
            return actual;
        }
    }

    record ChangeRequest(
            String id,
            String description,
            BigDecimal amount,
            ChangeState state
    ) {
        ChangeRequest {
            Objects.requireNonNull(id);
            Objects.requireNonNull(description);
            requirePositive(
                    amount,
                    "Change amount must be positive."
            );
            amount = money(amount);
            Objects.requireNonNull(state);
        }

        ChangeRequest approve() {
            if (state != ChangeState.PROPOSED) {
                throw new BudgetException(
                        "Only proposed changes can be approved."
                );
            }

            return new ChangeRequest(
                    id,
                    description,
                    amount,
                    ChangeState.APPROVED
            );
        }
    }

    interface ApprovalPolicy {
        boolean requiresSeniorApproval(BigDecimal amount);
    }

    static final class ThresholdApprovalPolicy
            implements ApprovalPolicy {

        private final BigDecimal threshold;

        ThresholdApprovalPolicy(BigDecimal threshold) {
            requirePositive(
                    threshold,
                    "Approval threshold must be positive."
            );
            this.threshold = money(threshold);
        }

        @Override
        public boolean requiresSeniorApproval(BigDecimal amount) {
            return amount.compareTo(threshold) >= 0;
        }
    }

    static final class ProjectBudget {
        private final String projectId;
        private final String projectName;
        private final String manager;
        private final BigDecimal contingencyRate;
        private final ApprovalPolicy approvalPolicy;

        private BudgetState state = BudgetState.DRAFT;

        private final Map<CostCategory, BudgetLine> lines =
                new EnumMap<>(CostCategory.class);

        private final List<ChangeRequest> changes =
                new ArrayList<>();

        ProjectBudget(
                String projectId,
                String projectName,
                String manager,
                BigDecimal contingencyRate,
                ApprovalPolicy approvalPolicy
        ) {
            this.projectId = Objects.requireNonNull(projectId);
            this.projectName = Objects.requireNonNull(projectName);
            this.manager = Objects.requireNonNull(manager);

            if (contingencyRate.compareTo(BigDecimal.ZERO) < 0 ||
                contingencyRate.compareTo(BigDecimal.ONE) > 0) {
                throw new BudgetException(
                        "Contingency rate must be between zero and one."
                );
            }

            this.contingencyRate = contingencyRate;
            this.approvalPolicy = Objects.requireNonNull(approvalPolicy);
        }

        void addLine(BudgetLine line) {
            if (state != BudgetState.DRAFT &&
                state != BudgetState.ACTIVE) {
                throw new BudgetException(
                        "Budget lines cannot be modified now."
                );
            }

            if (lines.containsKey(line.category())) {
                throw new BudgetException(
                        "Duplicate cost category: " +
                        line.category()
                );
            }

            lines.put(line.category(), line);
        }

        void approve() {
            if (lines.isEmpty()) {
                throw new BudgetException(
                        "Cannot approve an empty budget."
                );
            }

            state = BudgetState.APPROVED;
        }

        void activate() {
            if (state != BudgetState.APPROVED) {
                throw new BudgetException(
                        "Only approved budgets can become active."
                );
            }

            state = BudgetState.ACTIVE;
        }

        void commit(CostCategory category, BigDecimal amount) {
            requireActive();
            line(category).commit(amount);
        }

        void spend(CostCategory category, BigDecimal amount) {
            requireActive();
            line(category).spend(amount);
        }

        void submitChange(ChangeRequest request) {
            requireActive();

            if (changes.stream()
                    .anyMatch(existing ->
                            existing.id().equals(request.id()))) {
                throw new BudgetException(
                        "Duplicate change request."
                );
            }

            changes.add(request);
        }

        void approveChange(String id) {
            for (int index = 0; index < changes.size(); index++) {
                ChangeRequest request = changes.get(index);

                if (request.id().equals(id)) {
                    if (approvalPolicy.requiresSeniorApproval(
                            request.amount())) {
                        System.out.println(
                                "Governance alert: senior approval " +
                                "is required for " + request.id()
                        );
                    }

                    changes.set(index, request.approve());
                    return;
                }
            }

            throw new BudgetException(
                    "Unknown change request: " + id
            );
        }

        BigDecimal directBudget() {
            return money(
                    lines.values()
                            .stream()
                            .map(BudgetLine::planned)
                            .reduce(
                                    BigDecimal.ZERO,
                                    BigDecimal::add
                            )
            );
        }

        BigDecimal contingency() {
            return money(
                    directBudget().multiply(contingencyRate)
            );
        }

        BigDecimal approvedChanges() {
            return money(
                    changes.stream()
                            .filter(change ->
                                    change.state() ==
                                    ChangeState.APPROVED)
                            .map(ChangeRequest::amount)
                            .reduce(
                                    BigDecimal.ZERO,
                                    BigDecimal::add
                            )
            );
        }

        BigDecimal authorizedBudget() {
            return money(
                    directBudget()
                            .add(contingency())
                            .add(approvedChanges())
            );
        }

        BigDecimal actualSpend() {
            return money(
                    lines.values()
                            .stream()
                            .map(BudgetLine::actual)
                            .reduce(
                                    BigDecimal.ZERO,
                                    BigDecimal::add
                            )
            );
        }

        BigDecimal committedSpend() {
            return money(
                    lines.values()
                            .stream()
                            .map(BudgetLine::committed)
                            .reduce(
                                    BigDecimal.ZERO,
                                    BigDecimal::add
                            )
            );
        }

        BigDecimal projectedCost() {
            BigDecimal remainingCommitments =
                    lines.values()
                            .stream()
                            .map(line ->
                                    line.committed()
                                            .subtract(line.actual())
                                            .max(BigDecimal.ZERO))
                            .reduce(
                                    BigDecimal.ZERO,
                                    BigDecimal::add
                            );

            return money(
                    actualSpend().add(remainingCommitments)
            );
        }

        BudgetHealth health() {
            if (projectedCost()
                    .compareTo(authorizedBudget()) > 0) {
                return BudgetHealth.OVER_BUDGET;
            }

            BigDecimal utilization =
                    actualSpend()
                            .divide(
                                    authorizedBudget(),
                                    6,
                                    RoundingMode.HALF_UP
                            )
                            .multiply(money("100"));

            if (utilization.compareTo(money("90")) >= 0) {
                return BudgetHealth.CRITICAL;
            }

            if (utilization.compareTo(money("75")) >= 0) {
                return BudgetHealth.WATCH;
            }

            return BudgetHealth.HEALTHY;
        }

        boolean expenditureEligible() {
            return state == BudgetState.ACTIVE &&
                   projectedCost()
                           .compareTo(authorizedBudget()) <= 0;
        }

        void printReport() {
            System.out.println();
            System.out.println(
                    "PROJECT BUDGET GOVERNANCE REPORT"
            );
            System.out.println("=".repeat(72));
            System.out.println("Project:            " + projectName);
            System.out.println("Manager:            " + manager);
            System.out.println("State:              " + state);
            System.out.println(
                    "Direct budget:      " + directBudget()
            );
            System.out.println(
                    "Contingency:        " + contingency()
            );
            System.out.println(
                    "Approved changes:   " + approvedChanges()
            );
            System.out.println(
                    "Authorized budget:  " + authorizedBudget()
            );
            System.out.println(
                    "Actual spending:    " + actualSpend()
            );
            System.out.println(
                    "Committed spending: " + committedSpend()
            );
            System.out.println(
                    "Projected cost:     " + projectedCost()
            );
            System.out.println(
                    "Budget health:      " + health()
            );
            System.out.println(
                    "Expenditure status: " +
                    (expenditureEligible() ? "ELIGIBLE" : "BLOCKED")
            );

            System.out.println();
            System.out.println("COST CATEGORY ANALYSIS");

            lines.values().forEach(line ->
                    System.out.printf(
                            "%-12s planned=%12s actual=%12s " +
                            "variance=%12s usage=%s%%%n",
                            line.category(),
                            line.planned(),
                            line.actual(),
                            line.variance(),
                            line.utilization()
                    )
            );
        }

        private BudgetLine line(CostCategory category) {
            BudgetLine line = lines.get(category);

            if (line == null) {
                throw new BudgetException(
                        "Unknown cost category: " + category
                );
            }

            return line;
        }

        private void requireActive() {
            if (state != BudgetState.ACTIVE) {
                throw new BudgetException(
                        "The operation requires an active budget."
                );
            }
        }
    }

    public static void main(String[] args) {
        try {
            ApprovalPolicy approvalPolicy =
                    new ThresholdApprovalPolicy(
                            money("200000")
                    );

            ProjectBudget budget = new ProjectBudget(
                    "PRJ-2026-042",
                    "Enterprise Data Platform",
                    "Technology PMO",
                    new BigDecimal("0.12"),
                    approvalPolicy
            );

            budget.addLine(
                    new BudgetLine(
                            CostCategory.PERSONNEL,
                            "Engineering and delivery team",
                            money("4200000")
                    )
            );

            budget.addLine(
                    new BudgetLine(
                            CostCategory.CLOUD,
                            "Compute, storage, and networking",
                            money("1350000")
                    )
            );

            budget.addLine(
                    new BudgetLine(
                            CostCategory.SECURITY,
                            "Security assurance and tooling",
                            money("650000")
                    )
            );

            budget.addLine(
                    new BudgetLine(
                            CostCategory.TESTING,
                            "Integration and performance testing",
                            money("500000")
                    )
            );

            budget.addLine(
                    new BudgetLine(
                            CostCategory.TRAINING,
                            "Technical training and transition",
                            money("300000")
                    )
            );

            budget.approve();
            budget.activate();

            budget.commit(
                    CostCategory.PERSONNEL,
                    money("2800000")
            );
            budget.spend(
                    CostCategory.PERSONNEL,
                    money("2100000")
            );

            budget.commit(
                    CostCategory.CLOUD,
                    money("850000")
            );
            budget.spend(
                    CostCategory.CLOUD,
                    money("640000")
            );

            budget.commit(
                    CostCategory.SECURITY,
                    money("400000")
            );
            budget.spend(
                    CostCategory.SECURITY,
                    money("270000")
            );

            budget.commit(
                    CostCategory.TESTING,
                    money("180000")
            );
            budget.spend(
                    CostCategory.TESTING,
                    money("120000")
            );

            budget.submitChange(
                    new ChangeRequest(
                            "CR-001",
                            "Expanded compliance testing",
                            money("240000"),
                            ChangeState.PROPOSED
                    )
            );

            budget.approveChange("CR-001");

            budget.printReport();

            System.out.println();
            System.out.println(
                    "The enterprise model keeps the financial baseline, " +
                    "operational transactions, and change governance " +
                    "as separate domain concerns."
            );

        } catch (BudgetException exception) {
            System.err.println(
                    "Budget governance error: " +
                    exception.getMessage()
            );
        }
    }
}
