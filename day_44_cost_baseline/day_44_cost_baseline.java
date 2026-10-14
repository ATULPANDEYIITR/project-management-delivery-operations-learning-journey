import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;

/*
 * Cost Baseline: enterprise project governance model.
 *
 * Compile and run:
 *   javac CostBaseline.java
 *   java CostBaseline
 *
 * The model separates approved planning data, financial transactions,
 * physical progress, forecasts, and formal change-control decisions.
 */
public class CostBaseline {

    private static final BigDecimal ZERO = new BigDecimal("0.00");
    private static final BigDecimal HUNDRED = new BigDecimal("100");

    private static BigDecimal money(BigDecimal value) {
        Objects.requireNonNull(value, "Amount is required.");

        BigDecimal normalized = value.setScale(2, RoundingMode.HALF_UP);
        if (normalized.signum() < 0) {
            throw new IllegalArgumentException("Amounts cannot be negative.");
        }
        return normalized;
    }

    private static BigDecimal money(String value) {
        return money(new BigDecimal(value));
    }

    private static BigDecimal signedAmount(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }

    enum BaselineState {
        DRAFT,
        APPROVED,
        SUPERSEDED
    }

    enum ChangeState {
        PENDING,
        APPROVED,
        REJECTED
    }

    record WorkPackage(String code, String description, BigDecimal budget) {
        WorkPackage {
            if (code == null || code.isBlank()
                    || description == null || description.isBlank()) {
                throw new IllegalArgumentException("Work package identity is required.");
            }
            budget = money(budget);
        }
    }

    record Allocation(YearMonth period, String packageCode, BigDecimal amount) {
        Allocation {
            Objects.requireNonNull(period, "Period is required.");
            if (packageCode == null || packageCode.isBlank()) {
                throw new IllegalArgumentException("Package code is required.");
            }
            amount = money(amount);
        }
    }

    record CostTransaction(
            String id,
            YearMonth period,
            String packageCode,
            BigDecimal amount,
            String description,
            boolean approved) {
        CostTransaction {
            if (id == null || id.isBlank()
                    || description == null || description.isBlank()) {
                throw new IllegalArgumentException("Transaction identity is required.");
            }
            Objects.requireNonNull(period, "Period is required.");
            if (packageCode == null || packageCode.isBlank()) {
                throw new IllegalArgumentException("Package code is required.");
            }
            amount = money(amount);
        }
    }

    record ProgressRecord(
            YearMonth period,
            String packageCode,
            BigDecimal percentage) {
        ProgressRecord {
            Objects.requireNonNull(period, "Period is required.");
            if (packageCode == null || packageCode.isBlank()) {
                throw new IllegalArgumentException("Package code is required.");
            }
            Objects.requireNonNull(percentage, "Percentage is required.");

            if (percentage.compareTo(BigDecimal.ZERO) < 0
                    || percentage.compareTo(HUNDRED) > 0) {
                throw new IllegalArgumentException("Progress must be between 0 and 100.");
            }
        }
    }

    static final class ApprovedBaseline {
        private final String id;
        private final String projectName;
        private final Map<String, WorkPackage> packages;
        private final List<Allocation> allocations;
        private BaselineState state = BaselineState.DRAFT;
        private String approvedBy;

        ApprovedBaseline(
                String id,
                String projectName,
                List<WorkPackage> packages,
                List<Allocation> allocations) {

            if (id == null || id.isBlank()
                    || projectName == null || projectName.isBlank()) {
                throw new IllegalArgumentException("Baseline identity is required.");
            }

            this.id = id;
            this.projectName = projectName;

            Map<String, WorkPackage> packageMap = new TreeMap<>();
            for (WorkPackage item : packages) {
                if (packageMap.putIfAbsent(item.code(), item) != null) {
                    throw new IllegalArgumentException("Duplicate work package.");
                }
            }

            if (packageMap.isEmpty()) {
                throw new IllegalArgumentException("At least one package is required.");
            }

            this.packages = Collections.unmodifiableMap(packageMap);
            this.allocations = List.copyOf(allocations);
            validateAllocationTotals();
        }

        private void validateAllocationTotals() {
            Map<String, BigDecimal> totals = new HashMap<>();

            for (Allocation allocation : allocations) {
                if (!packages.containsKey(allocation.packageCode())) {
                    throw new IllegalArgumentException("Allocation references unknown package.");
                }

                totals.merge(
                        allocation.packageCode(),
                        allocation.amount(),
                        BigDecimal::add);
            }

            for (WorkPackage item : packages.values()) {
                BigDecimal allocated = totals.getOrDefault(item.code(), ZERO);
                if (allocated.compareTo(item.budget()) != 0) {
                    throw new IllegalArgumentException(
                            "Budget allocation does not match estimate for " + item.code());
                }
            }
        }

        void approve(String approver) {
            if (state != BaselineState.DRAFT) {
                throw new IllegalStateException("Only a draft can be approved.");
            }
            if (approver == null || approver.isBlank()) {
                throw new IllegalArgumentException("Approver is required.");
            }

            validateAllocationTotals();
            approvedBy = approver;
            state = BaselineState.APPROVED;
        }

        void supersede() {
            if (state != BaselineState.APPROVED) {
                throw new IllegalStateException("Only an approved baseline can be superseded.");
            }
            state = BaselineState.SUPERSEDED;
        }

        void requireApproved() {
            if (state != BaselineState.APPROVED) {
                throw new IllegalStateException("The active baseline is not approved.");
            }
        }

        BigDecimal budgetAtCompletion() {
            return packages.values().stream()
                    .map(WorkPackage::budget)
                    .reduce(ZERO, BigDecimal::add);
        }

        BigDecimal plannedValueThrough(YearMonth period) {
            return allocations.stream()
                    .filter(item -> !item.period().isAfter(period))
                    .map(Allocation::amount)
                    .reduce(ZERO, BigDecimal::add);
        }

        BigDecimal packageBudget(String code) {
            WorkPackage item = packages.get(code);
            if (item == null) {
                throw new IllegalArgumentException("Unknown work package: " + code);
            }
            return item.budget();
        }

        String id() {
            return id;
        }

        String projectName() {
            return projectName;
        }

        BaselineState state() {
            return state;
        }

        String approvedBy() {
            return approvedBy;
        }

        Map<String, WorkPackage> packages() {
            return packages;
        }
    }

    static final class ChangeRequest {
        private final String id;
        private final String description;
        private final BigDecimal delta;
        private final YearMonth effectivePeriod;
        private ChangeState state = ChangeState.PENDING;
        private String decisionNote;

        ChangeRequest(
                String id,
                String description,
                BigDecimal delta,
                YearMonth effectivePeriod) {

            if (id == null || id.isBlank()
                    || description == null || description.isBlank()) {
                throw new IllegalArgumentException("Change identity is required.");
            }
            if (delta == null || delta.signum() == 0) {
                throw new IllegalArgumentException("Change amount must be non-zero.");
            }

            this.id = id;
            this.description = description;
            this.delta = delta.setScale(2, RoundingMode.HALF_UP);
            this.effectivePeriod = Objects.requireNonNull(effectivePeriod);
        }

        void decide(ChangeState decision, String approver, String reason) {
            if (state != ChangeState.PENDING) {
                throw new IllegalStateException("Change has already been decided.");
            }
            if (decision == ChangeState.PENDING) {
                throw new IllegalArgumentException("A final decision is required.");
            }
            if (approver == null || approver.isBlank()
                    || reason == null || reason.isBlank()) {
                throw new IllegalArgumentException("Decision details are required.");
            }

            state = decision;
            decisionNote = approver + ": " + reason;
        }
    }

    record PerformanceReport(
            YearMonth period,
            BigDecimal bac,
            BigDecimal pv,
            BigDecimal ev,
            BigDecimal ac,
            BigDecimal cv,
            BigDecimal sv,
            BigDecimal cpi,
            BigDecimal spi,
            BigDecimal eac,
            BigDecimal etc) {
    }

    static final class PerformanceService {
        private final ApprovedBaseline baseline;
        private final List<CostTransaction> transactions = new ArrayList<>();
        private final Map<String, ProgressRecord> latestProgress = new HashMap<>();
        private final Set<String> transactionIds = new HashSet<>();

        PerformanceService(ApprovedBaseline baseline) {
            this.baseline = Objects.requireNonNull(baseline);
            baseline.requireApproved();
        }

        void recordCost(CostTransaction transaction) {
            baseline.requireApproved();

            if (!transactionIds.add(transaction.id())) {
                throw new IllegalArgumentException("Duplicate transaction ID.");
            }

            baseline.packageBudget(transaction.packageCode());

            // The transaction ID remains reserved even when a claim is rejected,
            // preventing the same source transaction from being submitted again.
            if (transaction.approved()) {
                transactions.add(transaction);
            }
        }

        void recordProgress(ProgressRecord record) {
            baseline.requireApproved();
            baseline.packageBudget(record.packageCode());

            String key = record.packageCode();
            ProgressRecord previous = latestProgress.get(key);

            if (previous != null && record.period().isBefore(previous.period())) {
                throw new IllegalArgumentException("Out-of-order progress record.");
            }

            if (previous != null
                    && record.period().equals(previous.period())
                    && record.percentage().compareTo(previous.percentage()) < 0) {
                throw new IllegalArgumentException("Completion cannot decrease.");
            }

            latestProgress.put(key, record);
        }

        private BigDecimal actualCostThrough(YearMonth period) {
            return transactions.stream()
                    .filter(item -> !item.period().isAfter(period))
                    .map(CostTransaction::amount)
                    .reduce(ZERO, BigDecimal::add);
        }

        private BigDecimal earnedValueThrough(YearMonth period) {
            BigDecimal earned = ZERO;

            for (WorkPackage item : baseline.packages().values()) {
                ProgressRecord record = latestProgress.get(item.code());

                if (record != null && !record.period().isAfter(period)) {
                    BigDecimal packageEarned = item.budget()
                            .multiply(record.percentage())
                            .divide(HUNDRED, 2, RoundingMode.HALF_UP);
                    earned = earned.add(packageEarned);
                }
            }

            return earned.setScale(2, RoundingMode.HALF_UP);
        }

        PerformanceReport evaluate(YearMonth period) {
            baseline.requireApproved();

            BigDecimal bac = baseline.budgetAtCompletion();
            BigDecimal pv = baseline.plannedValueThrough(period);
            BigDecimal ev = earnedValueThrough(period);
            BigDecimal ac = actualCostThrough(period);
            BigDecimal cv = ev.subtract(ac);
            BigDecimal sv = ev.subtract(pv);

            // Optional ratios explicitly represent undefined zero-denominator cases.
            BigDecimal cpi = ac.signum() > 0
                    ? ev.divide(ac, 4, RoundingMode.HALF_UP)
                    : null;

            BigDecimal spi = pv.signum() > 0
                    ? ev.divide(pv, 4, RoundingMode.HALF_UP)
                    : null;

            BigDecimal eac = cpi != null && cpi.signum() > 0
                    ? bac.divide(cpi, 2, RoundingMode.HALF_UP)
                    : null;

            BigDecimal etc = eac != null ? eac.subtract(ac) : null;

            return new PerformanceReport(
                    period, bac, pv, ev, ac, cv, sv, cpi, spi, eac, etc);
        }
    }

    private static ApprovedBaseline createBaseline() {
        List<WorkPackage> packages = List.of(
                new WorkPackage("CIVIL", "Civil works", money("450000")),
                new WorkPackage("ELECT", "Electrical installation", money("300000")),
                new WorkPackage("TEST", "Testing and commissioning", money("250000"))
        );

        List<Allocation> allocations = List.of(
                new Allocation(YearMonth.of(2026, 1), "CIVIL", money("150000")),
                new Allocation(YearMonth.of(2026, 2), "CIVIL", money("180000")),
                new Allocation(YearMonth.of(2026, 3), "CIVIL", money("120000")),
                new Allocation(YearMonth.of(2026, 2), "ELECT", money("50000")),
                new Allocation(YearMonth.of(2026, 3), "ELECT", money("150000")),
                new Allocation(YearMonth.of(2026, 4), "ELECT", money("100000")),
                new Allocation(YearMonth.of(2026, 3), "TEST", money("50000")),
                new Allocation(YearMonth.of(2026, 4), "TEST", money("100000")),
                new Allocation(YearMonth.of(2026, 5), "TEST", money("100000"))
        );

        ApprovedBaseline baseline = new ApprovedBaseline(
                "BASE-001",
                "District Hospital Modernization",
                packages,
                allocations
        );

        baseline.approve("Project Director");
        return baseline;
    }

    private static void printReport(PerformanceReport report) {
        System.out.println("Reporting period: " + report.period());
        System.out.println("Budget at completion: ₹" + report.bac());
        System.out.println("Planned value: ₹" + report.pv());
        System.out.println("Earned value: ₹" + report.ev());
        System.out.println("Actual cost: ₹" + report.ac());
        System.out.println("Cost variance: ₹" + signedAmount(report.cv()));
        System.out.println("Schedule variance: ₹" + signedAmount(report.sv()));
        System.out.println("CPI: " + (report.cpi() == null ? "N/A" : report.cpi()));
        System.out.println("SPI: " + (report.spi() == null ? "N/A" : report.spi()));
        System.out.println("EAC: " + (report.eac() == null ? "N/A" : "₹" + report.eac()));
        System.out.println("ETC: " + (report.etc() == null ? "N/A" : "₹" + report.etc()));
    }

    public static void main(String[] args) {
        ApprovedBaseline baseline = createBaseline();
        PerformanceService service = new PerformanceService(baseline);

        List<CostTransaction> transactions = List.of(
                new CostTransaction("C-101", YearMonth.of(2026, 1),
                        "CIVIL", money("140000"), "Site preparation", true),
                new CostTransaction("C-102", YearMonth.of(2026, 2),
                        "CIVIL", money("200000"), "Structural work", true),
                new CostTransaction("C-103", YearMonth.of(2026, 2),
                        "ELECT", money("60000"), "Cable procurement", true),
                new CostTransaction("C-104", YearMonth.of(2026, 3),
                        "CIVIL", money("130000"), "Civil completion", true),
                new CostTransaction("C-105", YearMonth.of(2026, 3),
                        "ELECT", money("140000"), "Electrical installation", true),
                new CostTransaction("C-106", YearMonth.of(2026, 3),
                        "TEST", money("30000"), "Pre-commissioning tests", true),
                new CostTransaction("C-107", YearMonth.of(2026, 3),
                        "TEST", money("25000"), "Unapproved supplier claim", false)
        );

        transactions.forEach(service::recordCost);

        List<ProgressRecord> progress = List.of(
                new ProgressRecord(YearMonth.of(2026, 1), "CIVIL", new BigDecimal("30")),
                new ProgressRecord(YearMonth.of(2026, 2), "CIVIL", new BigDecimal("70")),
                new ProgressRecord(YearMonth.of(2026, 3), "CIVIL", new BigDecimal("100")),
                new ProgressRecord(YearMonth.of(2026, 2), "ELECT", new BigDecimal("10")),
                new ProgressRecord(YearMonth.of(2026, 3), "ELECT", new BigDecimal("55")),
                new ProgressRecord(YearMonth.of(2026, 3), "TEST", new BigDecimal("10"))
        );

        progress.forEach(service::recordProgress);

        System.out.println("Project: " + baseline.projectName());
        System.out.println("Baseline: " + baseline.id());
        System.out.println("Approved by: " + baseline.approvedBy());
        printReport(service.evaluate(YearMonth.of(2026, 3)));

        ChangeRequest change = new ChangeRequest(
                "CR-014",
                "Additional electrical safety panels",
                money("50000"),
                YearMonth.of(2026, 5)
        );

        change.decide(
                ChangeState.APPROVED,
                "Project Director",
                "Required for revised electrical safety specifications."
        );

        System.out.println("\nChange state: " + change.state);
        System.out.println("Change decision: " + change.decisionNote);
        System.out.println("Baseline remains ₹" + baseline.budgetAtCompletion()
                + " until a separate revision is approved.");

        PerformanceReport early = service.evaluate(YearMonth.of(2025, 12));
        if (early.cpi() != null || early.spi() != null) {
            throw new IllegalStateException("Zero-denominator edge case failed.");
        }

        System.out.println("\nValidation checks passed.");
    }
}
