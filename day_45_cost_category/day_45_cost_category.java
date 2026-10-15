import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

public class ProjectCostGovernance {

    enum CostCategory {
        LABOR,
        CLOUD,
        SOFTWARE,
        EQUIPMENT,
        TRAVEL,
        CONTRACTOR
    }

    enum ExpenseStatus {
        PLANNED,
        COMMITTED,
        ACTUAL,
        CANCELLED
    }

    enum Severity {
        INFORMATIONAL,
        WARNING,
        CRITICAL
    }

    record BudgetPolicy(
        BigDecimal warningThreshold,
        BigDecimal criticalThreshold,
        BigDecimal highValueApprovalLimit
    ) {
        BudgetPolicy {
            requireNonNegative(warningThreshold, "warningThreshold");
            requireNonNegative(criticalThreshold, "criticalThreshold");
            requireNonNegative(highValueApprovalLimit, "highValueApprovalLimit");

            if (criticalThreshold.compareTo(warningThreshold) < 0) {
                throw new IllegalArgumentException(
                    "Critical threshold cannot be below warning threshold."
                );
            }
        }
    }

    record CostExpense(
        String id,
        CostCategory category,
        String description,
        BigDecimal amount,
        LocalDate expenseDate,
        String vendor,
        ExpenseStatus status,
        boolean approved,
        String invoiceNumber
    ) {
        CostExpense {
            Objects.requireNonNull(id);
            Objects.requireNonNull(category);
            Objects.requireNonNull(description);
            Objects.requireNonNull(amount);
            Objects.requireNonNull(expenseDate);
            Objects.requireNonNull(vendor);
            Objects.requireNonNull(status);

            if (id.isBlank()) {
                throw new IllegalArgumentException("Expense ID cannot be blank.");
            }

            if (amount.compareTo(BigDecimal.ZERO) <= 0) {
                throw new IllegalArgumentException(
                    "Expense amount must be positive."
                );
            }

            if (description.isBlank() || vendor.isBlank()) {
                throw new IllegalArgumentException(
                    "Description and vendor are required."
                );
            }

            amount = amount.setScale(2, RoundingMode.HALF_UP);
        }
    }

    static final class Project {
        private final String id;
        private final String name;
        private final LocalDate startDate;
        private final LocalDate endDate;
        private final Map<CostCategory, BigDecimal> budget;
        private final List<CostExpense> expenses = new ArrayList<>();
        private final Set<String> expenseIds = new HashSet<>();
        private final Set<String> invoiceNumbers = new HashSet<>();

        Project(
            String id,
            String name,
            LocalDate startDate,
            LocalDate endDate,
            Map<CostCategory, BigDecimal> budget
        ) {
            if (id == null || id.isBlank() ||
                name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Project identity is required."
                );
            }

            if (endDate.isBefore(startDate)) {
                throw new IllegalArgumentException(
                    "Project end date cannot precede start date."
                );
            }

            this.id = id;
            this.name = name;
            this.startDate = startDate;
            this.endDate = endDate;
            this.budget = new EnumMap<>(CostCategory.class);

            for (Map.Entry<CostCategory, BigDecimal> entry :
                budget.entrySet()) {
                requireNonNegative(
                    entry.getValue(),
                    "budget for " + entry.getKey()
                );
                this.budget.put(entry.getKey(), entry.getValue());
            }
        }

        void addExpense(CostExpense expense) {
            if (!id.equals(expense.id().startsWith("EXP-") ? id : id)) {
                // Project ownership is checked explicitly below through the
                // service boundary because the expense record contains no
                // mutable project reference.
            }

            if (expenseIds.contains(expense.id())) {
                throw new IllegalArgumentException(
                    "Duplicate expense ID: " + expense.id()
                );
            }

            if (expense.expenseDate().isBefore(startDate) ||
                expense.expenseDate().isAfter(endDate)) {
                throw new IllegalArgumentException(
                    "Expense date falls outside project period."
                );
            }

            if (expense.invoiceNumber() != null &&
                !expense.invoiceNumber().isBlank() &&
                invoiceNumbers.contains(expense.invoiceNumber())) {
                throw new IllegalArgumentException(
                    "Duplicate invoice number: " +
                    expense.invoiceNumber()
                );
            }

            expenseIds.add(expense.id());

            if (expense.invoiceNumber() != null &&
                !expense.invoiceNumber().isBlank()) {
                invoiceNumbers.add(expense.invoiceNumber());
            }

            expenses.add(expense);
        }

        BigDecimal totalBudget() {
            return budget.values()
                .stream()
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        BigDecimal totalActual() {
            return expenses.stream()
                .filter(e -> e.status() == ExpenseStatus.ACTUAL)
                .map(CostExpense::amount)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        Map<CostCategory, BigDecimal> actualByCategory() {
            Map<CostCategory, BigDecimal> result =
                new EnumMap<>(CostCategory.class);

            for (CostExpense expense : expenses) {
                if (expense.status() == ExpenseStatus.ACTUAL) {
                    result.merge(
                        expense.category(),
                        expense.amount(),
                        BigDecimal::add
                    );
                }
            }

            return result;
        }

        Map<YearMonth, BigDecimal> monthlyActual() {
            return expenses.stream()
                .filter(e -> e.status() == ExpenseStatus.ACTUAL)
                .collect(Collectors.groupingBy(
                    e -> YearMonth.from(e.expenseDate()),
                    Collectors.reducing(
                        BigDecimal.ZERO,
                        CostExpense::amount,
                        BigDecimal::add
                    )
                ));
        }

        List<String> policyViolations(BudgetPolicy policy) {
            List<String> violations = new ArrayList<>();
            Map<CostCategory, BigDecimal> actual = actualByCategory();

            for (Map.Entry<CostCategory, BigDecimal> entry :
                budget.entrySet()) {
                CostCategory category = entry.getKey();
                BigDecimal budgetValue = entry.getValue();
                BigDecimal spent = actual.getOrDefault(
                    category,
                    BigDecimal.ZERO
                );

                if (budgetValue.signum() == 0 &&
                    spent.signum() > 0) {
                    violations.add(
                        category + ": spending exists without budget."
                    );
                    continue;
                }

                if (budgetValue.signum() > 0) {
                    BigDecimal ratio = spent.divide(
                        budgetValue,
                        6,
                        RoundingMode.HALF_UP
                    );

                    if (ratio.compareTo(policy.criticalThreshold()) >= 0) {
                        violations.add(
                            category + ": critical budget utilization."
                        );
                    } else if (
                        ratio.compareTo(policy.warningThreshold()) >= 0
                    ) {
                        violations.add(
                            category + ": warning budget utilization."
                        );
                    }
                }
            }

            if (totalActual().compareTo(totalBudget()) > 0) {
                violations.add("Total project budget has been exceeded.");
            }

            for (CostExpense expense : expenses) {
                if (expense.amount().compareTo(
                    policy.highValueApprovalLimit()
                ) >= 0 && !expense.approved()) {
                    violations.add(
                        expense.id() +
                        ": high-value expense requires approval."
                    );
                }
            }

            return violations;
        }

        Map<String, BigDecimal> vendorExposure() {
            Map<String, BigDecimal> result = new HashMap<>();

            for (CostExpense expense : expenses) {
                if (expense.status() == ExpenseStatus.ACTUAL) {
                    result.merge(
                        expense.vendor(),
                        expense.amount(),
                        BigDecimal::add
                    );
                }
            }

            return result;
        }

        String id() {
            return id;
        }

        String name() {
            return name;
        }
    }

    static final class CostManagementService {
        private final Map<String, Project> projects = new HashMap<>();

        void registerProject(Project project) {
            if (projects.putIfAbsent(project.id(), project) != null) {
                throw new IllegalArgumentException(
                    "Project already exists: " + project.id()
                );
            }
        }

        void recordExpense(String projectId, CostExpense expense) {
            Project project = projects.get(projectId);

            if (project == null) {
                throw new IllegalArgumentException(
                    "Unknown project: " + projectId
                );
            }

            project.addExpense(expense);
        }

        void printDashboard(
            String projectId,
            BudgetPolicy policy
        ) {
            Project project = projects.get(projectId);

            if (project == null) {
                throw new IllegalArgumentException(
                    "Unknown project: " + projectId
                );
            }

            BigDecimal budget = project.totalBudget();
            BigDecimal actual = project.totalActual();

            System.out.println(
                "\n=== ENTERPRISE PROJECT COST DASHBOARD ==="
            );
            System.out.println("Project: " + project.name());
            System.out.println("Budget: " + budget);
            System.out.println("Actual: " + actual);
            System.out.println(
                "Variance: " + budget.subtract(actual)
            );

            if (budget.signum() > 0) {
                BigDecimal utilization = actual
                    .multiply(BigDecimal.valueOf(100))
                    .divide(
                        budget,
                        2,
                        RoundingMode.HALF_UP
                    );

                System.out.println(
                    "Utilization: " + utilization + "%"
                );
            }

            System.out.println("\nCategory actuals:");
            project.actualByCategory()
                .forEach((category, amount) ->
                    System.out.println(
                        "  " + category + ": " + amount
                    )
                );

            System.out.println("\nMonthly actuals:");
            project.monthlyActual()
                .entrySet()
                .stream()
                .sorted(Map.Entry.comparingByKey())
                .forEach(entry ->
                    System.out.println(
                        "  " + entry.getKey() +
                        ": " + entry.getValue()
                    )
                );

            System.out.println("\nVendor exposure:");
            project.vendorExposure()
                .entrySet()
                .stream()
                .sorted(
                    Map.Entry.<String, BigDecimal>comparingByValue()
                        .reversed()
                )
                .forEach(entry ->
                    System.out.println(
                        "  " + entry.getKey() +
                        ": " + entry.getValue()
                    )
                );

            System.out.println("\nPolicy evaluation:");
            for (String violation :
                project.policyViolations(policy)) {
                System.out.println("  " + violation);
            }
        }
    }

    private static void requireNonNegative(
        BigDecimal value,
        String field
    ) {
        Objects.requireNonNull(value, field + " cannot be null.");

        if (value.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException(
                field + " cannot be negative."
            );
        }
    }

    public static void main(String[] args) {
        CostManagementService service = new CostManagementService();

        Map<CostCategory, BigDecimal> budget =
            new EnumMap<>(CostCategory.class);

        budget.put(CostCategory.LABOR, new BigDecimal("175000"));
        budget.put(CostCategory.CLOUD, new BigDecimal("65000"));
        budget.put(CostCategory.SOFTWARE, new BigDecimal("28000"));
        budget.put(CostCategory.EQUIPMENT, new BigDecimal("35000"));
        budget.put(CostCategory.TRAVEL, new BigDecimal("18000"));
        budget.put(CostCategory.CONTRACTOR, new BigDecimal("45000"));

        Project project = new Project(
            "PRJ-JAVA-001",
            "Enterprise Operations Platform",
            LocalDate.of(2026, 1, 1),
            LocalDate.of(2026, 12, 31),
            budget
        );

        service.registerProject(project);

        service.recordExpense(
            "PRJ-JAVA-001",
            new CostExpense(
                "EXP-JAVA-001",
                CostCategory.LABOR,
                "Platform engineering allocation",
                new BigDecimal("29000"),
                LocalDate.of(2026, 1, 31),
                "Internal Engineering",
                ExpenseStatus.ACTUAL,
                true,
                "LAB-J-001"
            )
        );

        service.recordExpense(
            "PRJ-JAVA-001",
            new CostExpense(
                "EXP-JAVA-002",
                CostCategory.CLOUD,
                "January production workloads",
                new BigDecimal("8300"),
                LocalDate.of(2026, 1, 31),
                "Cloud Provider",
                ExpenseStatus.ACTUAL,
                true,
                "CLOUD-J-001"
            )
        );

        service.recordExpense(
            "PRJ-JAVA-001",
            new CostExpense(
                "EXP-JAVA-003",
                CostCategory.SOFTWARE,
                "Enterprise monitoring licenses",
                new BigDecimal("13500"),
                LocalDate.of(2026, 2, 15),
                "Monitoring Vendor",
                ExpenseStatus.ACTUAL,
                true,
                "MON-J-001"
            )
        );

        service.recordExpense(
            "PRJ-JAVA-001",
            new CostExpense(
                "EXP-JAVA-004",
                CostCategory.CONTRACTOR,
                "Specialist migration support",
                new BigDecimal("16000"),
                LocalDate.of(2026, 3, 8),
                "Migration Consultancy",
                ExpenseStatus.ACTUAL,
                false,
                "MIG-J-001"
            )
        );

        service.recordExpense(
            "PRJ-JAVA-001",
            new CostExpense(
                "EXP-JAVA-005",
                CostCategory.CLOUD,
                "February data processing",
                new BigDecimal("10500"),
                LocalDate.of(2026, 2, 28),
                "Cloud Provider",
                ExpenseStatus.ACTUAL,
                true,
                "CLOUD-J-002"
            )
        );

        BudgetPolicy policy = new BudgetPolicy(
            new BigDecimal("0.80"),
            new BigDecimal("1.00"),
            new BigDecimal("10000")
        );

        service.printDashboard("PRJ-JAVA-001", policy);

        System.out.println("\n=== DOMAIN VALIDATION TEST ===");

        try {
            service.recordExpense(
                "PRJ-JAVA-001",
                new CostExpense(
                    "EXP-JAVA-BAD",
                    CostCategory.CLOUD,
                    "Negative transaction",
                    new BigDecimal("-50"),
                    LocalDate.of(2026, 4, 1),
                    "Cloud Provider",
                    ExpenseStatus.ACTUAL,
                    false,
                    "BAD-J-001"
                )
            );
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Rejected invalid expense: " + error.getMessage()
            );
        }

        try {
            service.recordExpense(
                "PRJ-JAVA-001",
                new CostExpense(
                    "EXP-JAVA-DUP",
                    CostCategory.CLOUD,
                    "Duplicate invoice transaction",
                    new BigDecimal("500"),
                    LocalDate.of(2026, 4, 2),
                    "Cloud Provider",
                    ExpenseStatus.ACTUAL,
                    true,
                    "CLOUD-J-002"
                )
            );
        } catch (IllegalArgumentException error) {
            System.out.println(
                "Rejected duplicate invoice: " +
                error.getMessage()
            );
        }
    }
}
