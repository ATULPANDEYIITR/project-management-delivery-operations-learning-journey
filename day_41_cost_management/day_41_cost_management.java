import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

public class ProjectCostManagement {

    private static final int SCALE = 2;

    enum CostType {
        LABOR,
        MATERIAL,
        EQUIPMENT,
        SOFTWARE,
        TRAVEL,
        SUBCONTRACT,
        OVERHEAD
    }

    enum Classification {
        DIRECT,
        INDIRECT
    }

    enum CostStatus {
        WITHIN_PLAN,
        WATCH,
        HIGH_UTILIZATION,
        FORECAST_OVER_BUDGET,
        OVER_BUDGET
    }

    record CostItem(
        String name,
        CostType type,
        Classification classification,
        BigDecimal planned,
        BigDecimal actual,
        BigDecimal committed
    ) {
        CostItem {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException("Cost name is required.");
            }

            requireNonNegative(planned, "planned");
            requireNonNegative(actual, "actual");
            requireNonNegative(committed, "committed");

            planned = money(planned);
            actual = money(actual);
            committed = money(committed);
        }

        BigDecimal forecast() {
            return money(actual.add(committed));
        }

        BigDecimal variance() {
            return money(planned.subtract(actual));
        }
    }

    record BudgetSnapshot(
        BigDecimal approvedBudget,
        BigDecimal plannedCost,
        BigDecimal actualCost,
        BigDecimal committedCost,
        BigDecimal forecastAtCompletion,
        BigDecimal remainingBudget,
        BigDecimal utilizationPercent,
        CostStatus status
    ) {}

    static class CostManagementService {
        private final String projectName;
        private final BigDecimal approvedBudget;
        private final BigDecimal managementReserve;
        private final List<CostItem> costItems = new ArrayList<>();

        CostManagementService(
            String projectName,
            BigDecimal approvedBudget,
            BigDecimal managementReserve
        ) {
            if (projectName == null || projectName.isBlank()) {
                throw new IllegalArgumentException("Project name is required.");
            }

            requireNonNegative(approvedBudget, "approvedBudget");
            requireNonNegative(managementReserve, "managementReserve");

            this.projectName = projectName;
            this.approvedBudget = money(approvedBudget);
            this.managementReserve = money(managementReserve);
        }

        void recordCost(CostItem item) {
            costItems.add(item);
        }

        BigDecimal plannedCost() {
            return sum(CostItem::planned);
        }

        BigDecimal actualCost() {
            return sum(CostItem::actual);
        }

        BigDecimal committedCost() {
            return sum(CostItem::committed);
        }

        BigDecimal forecastAtCompletion() {
            return money(actualCost().add(committedCost()));
        }

        BigDecimal remainingBudget() {
            return money(approvedBudget.subtract(actualCost()));
        }

        BigDecimal utilizationPercent() {
            if (approvedBudget.signum() == 0) {
                return BigDecimal.ZERO.setScale(SCALE, RoundingMode.HALF_UP);
            }

            return actualCost()
                .divide(approvedBudget, 6, RoundingMode.HALF_UP)
                .multiply(BigDecimal.valueOf(100))
                .setScale(SCALE, RoundingMode.HALF_UP);
        }

        CostStatus status() {
            if (actualCost().compareTo(approvedBudget) > 0) {
                return CostStatus.OVER_BUDGET;
            }

            if (forecastAtCompletion().compareTo(approvedBudget) > 0) {
                return CostStatus.FORECAST_OVER_BUDGET;
            }

            if (utilizationPercent().compareTo(BigDecimal.valueOf(90)) >= 0) {
                return CostStatus.HIGH_UTILIZATION;
            }

            if (utilizationPercent().compareTo(BigDecimal.valueOf(75)) >= 0) {
                return CostStatus.WATCH;
            }

            return CostStatus.WITHIN_PLAN;
        }

        Map<CostType, BigDecimal> actualCostByType() {
            Map<CostType, BigDecimal> result = new EnumMap<>(CostType.class);

            for (CostItem item : costItems) {
                result.merge(
                    item.type(),
                    item.actual(),
                    (oldValue, newValue) -> money(oldValue.add(newValue))
                );
            }

            return result;
        }

        Map<Classification, BigDecimal> actualCostByClassification() {
            Map<Classification, BigDecimal> result =
                new EnumMap<>(Classification.class);

            for (CostItem item : costItems) {
                result.merge(
                    item.classification(),
                    item.actual(),
                    (oldValue, newValue) -> money(oldValue.add(newValue))
                );
            }

            return result;
        }

        BudgetSnapshot snapshot() {
            return new BudgetSnapshot(
                approvedBudget,
                plannedCost(),
                actualCost(),
                committedCost(),
                forecastAtCompletion(),
                remainingBudget(),
                utilizationPercent(),
                status()
            );
        }

        void printReport() {
            BudgetSnapshot snapshot = snapshot();

            System.out.println("\n=== ENTERPRISE PROJECT COST CONTROL ===");
            System.out.println("Project: " + projectName);
            System.out.println("Approved budget: " + snapshot.approvedBudget());
            System.out.println("Planned cost: " + snapshot.plannedCost());
            System.out.println("Actual cost: " + snapshot.actualCost());
            System.out.println("Committed cost: " + snapshot.committedCost());
            System.out.println("Forecast at completion: "
                + snapshot.forecastAtCompletion());
            System.out.println("Remaining budget: "
                + snapshot.remainingBudget());
            System.out.println("Utilization: "
                + snapshot.utilizationPercent() + "%");
            System.out.println("Status: " + snapshot.status());

            System.out.println("\nActual cost by category:");
            actualCostByType().forEach(
                (type, amount) ->
                    System.out.printf("  %-15s %10s%n", type, amount)
            );

            System.out.println("\nDirect versus indirect cost:");
            actualCostByClassification().forEach(
                (classification, amount) ->
                    System.out.printf(
                        "  %-10s %10s%n",
                        classification,
                        amount
                    )
            );

            System.out.println("\nCost-specific controls:");
            for (CostItem item : costItems) {
                if (item.actual().compareTo(item.planned()) > 0) {
                    System.out.println(
                        "  " + item.name()
                        + ": actual spending exceeds its plan by "
                        + item.actual().subtract(item.planned())
                    );
                }

                if (item.committed().signum() > 0) {
                    System.out.println(
                        "  " + item.name()
                        + ": outstanding commitment = "
                        + item.committed()
                    );
                }
            }

            if (forecastAtCompletion().compareTo(
                    approvedBudget.add(managementReserve)) > 0) {
                System.out.println(
                    "  Forecast exceeds approved budget plus management reserve."
                );
            }
        }

        private BigDecimal sum(
            java.util.function.Function<CostItem, BigDecimal> selector
        ) {
            BigDecimal total = BigDecimal.ZERO;

            for (CostItem item : costItems) {
                total = total.add(selector.apply(item));
            }

            return money(total);
        }
    }

    record EarnedValueMetrics(
        BigDecimal bac,
        BigDecimal pv,
        BigDecimal ev,
        BigDecimal ac,
        BigDecimal cpi,
        BigDecimal spi,
        BigDecimal eac,
        BigDecimal vac
    ) {}

    static EarnedValueMetrics calculateEarnedValue(
        BigDecimal bac,
        BigDecimal pv,
        BigDecimal ev,
        BigDecimal ac
    ) {
        requireNonNegative(bac, "BAC");
        requireNonNegative(pv, "PV");
        requireNonNegative(ev, "EV");
        requireNonNegative(ac, "AC");

        BigDecimal cpi = ac.signum() == 0
            ? null
            : ev.divide(ac, 6, RoundingMode.HALF_UP);

        BigDecimal spi = pv.signum() == 0
            ? null
            : ev.divide(pv, 6, RoundingMode.HALF_UP);

        BigDecimal eac = cpi != null && cpi.signum() > 0
            ? bac.divide(cpi, 2, RoundingMode.HALF_UP)
            : null;

        BigDecimal vac = eac == null
            ? null
            : money(bac.subtract(eac));

        return new EarnedValueMetrics(
            money(bac),
            money(pv),
            money(ev),
            money(ac),
            cpi == null ? null : cpi.setScale(2, RoundingMode.HALF_UP),
            spi == null ? null : spi.setScale(2, RoundingMode.HALF_UP),
            eac,
            vac
        );
    }

    private static BigDecimal money(BigDecimal value) {
        return value.setScale(SCALE, RoundingMode.HALF_UP);
    }

    private static void requireNonNegative(
        BigDecimal value,
        String field
    ) {
        if (value == null || value.signum() < 0) {
            throw new IllegalArgumentException(
                field + " must be non-negative."
            );
        }
    }

    public static void main(String[] args) {
        CostManagementService service =
            new CostManagementService(
                "National Logistics Analytics Platform",
                new BigDecimal("400000"),
                new BigDecimal("30000")
            );

        service.recordCost(
            new CostItem(
                "Project management",
                CostType.LABOR,
                Classification.DIRECT,
                new BigDecimal("45000"),
                new BigDecimal("41000"),
                new BigDecimal("3000")
            )
        );

        service.recordCost(
            new CostItem(
                "Software engineering",
                CostType.LABOR,
                Classification.DIRECT,
                new BigDecimal("135000"),
                new BigDecimal("142000"),
                new BigDecimal("18000")
            )
        );

        service.recordCost(
            new CostItem(
                "Cloud infrastructure",
                CostType.EQUIPMENT,
                Classification.DIRECT,
                new BigDecimal("70000"),
                new BigDecimal("62000"),
                new BigDecimal("12000")
            )
        );

        service.recordCost(
            new CostItem(
                "Analytics licenses",
                CostType.SOFTWARE,
                Classification.DIRECT,
                new BigDecimal("50000"),
                new BigDecimal("47000"),
                new BigDecimal("2000")
            )
        );

        service.recordCost(
            new CostItem(
                "Implementation services",
                CostType.SUBCONTRACT,
                Classification.DIRECT,
                new BigDecimal("65000"),
                new BigDecimal("53000"),
                new BigDecimal("10000")
            )
        );

        service.recordCost(
            new CostItem(
                "Corporate overhead",
                CostType.OVERHEAD,
                Classification.INDIRECT,
                new BigDecimal("25000"),
                new BigDecimal("21000"),
                BigDecimal.ZERO
            )
        );

        service.printReport();

        EarnedValueMetrics metrics = calculateEarnedValue(
            new BigDecimal("400000"),
            new BigDecimal("220000"),
            new BigDecimal("205000"),
            service.actualCost()
        );

        System.out.println("\n=== EARNED VALUE METRICS ===");
        System.out.println("BAC: " + metrics.bac());
        System.out.println("PV:  " + metrics.pv());
        System.out.println("EV:  " + metrics.ev());
        System.out.println("AC:  " + metrics.ac());
        System.out.println("CPI: " + metrics.cpi());
        System.out.println("SPI: " + metrics.spi());
        System.out.println("EAC: " + metrics.eac());
        System.out.println("VAC: " + metrics.vac());
    }
}
