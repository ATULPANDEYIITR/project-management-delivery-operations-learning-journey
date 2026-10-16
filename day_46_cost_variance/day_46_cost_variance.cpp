#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

using Money = long long; // Store currency in minor units to avoid floating-point rounding.

enum class VarianceStatus {
    Favorable,
    Unfavorable,
    OnPlan
};

std::string statusToString(VarianceStatus status) {
    switch (status) {
        case VarianceStatus::Favorable:
            return "Favorable";
        case VarianceStatus::Unfavorable:
            return "Unfavorable";
        case VarianceStatus::OnPlan:
            return "On plan";
    }
    return "Unknown";
}

double percentage(Money numerator, Money denominator) {
    if (denominator == 0) {
        throw std::domain_error("Cannot calculate a percentage with a zero plan.");
    }
    return (static_cast<double>(numerator) /
            static_cast<double>(denominator)) * 100.0;
}

struct CostRecord {
    std::string category;
    Money planned;
    Money actual;

    Money variance() const {
        return actual - planned;
    }

    VarianceStatus status() const {
        if (actual > planned) {
            return VarianceStatus::Unfavorable;
        }
        if (actual < planned) {
            return VarianceStatus::Favorable;
        }
        return VarianceStatus::OnPlan;
    }
};

class RepositoryCostGovernance {
private:
    std::map<std::string, CostRecord> records;

    static void validateMoney(Money amount) {
        if (amount < 0) {
            throw std::invalid_argument("Cost values cannot be negative.");
        }
    }

public:
    void createBudgetLine(
        const std::string& category,
        Money planned
    ) {
        if (category.empty()) {
            throw std::invalid_argument("Category cannot be empty.");
        }

        validateMoney(planned);

        if (records.contains(category)) {
            throw std::logic_error("Budget category already exists: " + category);
        }

        records.emplace(
            category,
            CostRecord{category, planned, 0}
        );
    }

    void recordActualCost(
        const std::string& category,
        Money actualCost
    ) {
        validateMoney(actualCost);

        auto it = records.find(category);
        if (it == records.end()) {
            throw std::out_of_range("Unknown budget category: " + category);
        }

        it->second.actual += actualCost;
    }

    Money plannedTotal() const {
        Money total = 0;
        for (const auto& [category, record] : records) {
            total += record.planned;
        }
        return total;
    }

    Money actualTotal() const {
        Money total = 0;
        for (const auto& [category, record] : records) {
            total += record.actual;
        }
        return total;
    }

    Money totalVariance() const {
        return actualTotal() - plannedTotal();
    }

    std::vector<CostRecord> unfavorableItems() const {
        std::vector<CostRecord> result;

        for (const auto& [category, record] : records) {
            if (record.variance() > 0) {
                result.push_back(record);
            }
        }

        std::sort(
            result.begin(),
            result.end(),
            [](const CostRecord& left, const CostRecord& right) {
                return left.variance() > right.variance();
            }
        );

        return result;
    }

    std::vector<CostRecord> favorableItems() const {
        std::vector<CostRecord> result;

        for (const auto& [category, record] : records) {
            if (record.variance() < 0) {
                result.push_back(record);
            }
        }

        std::sort(
            result.begin(),
            result.end(),
            [](const CostRecord& left, const CostRecord& right) {
                return left.variance() < right.variance();
            }
        );

        return result;
    }

    void printGovernanceReport() const {
        std::cout << "\nPROJECT COST CONTROL REPORT\n";
        std::cout << std::string(92, '=') << '\n';

        std::cout << std::left
                  << std::setw(28) << "Cost category"
                  << std::right
                  << std::setw(14) << "Planned"
                  << std::setw(14) << "Actual"
                  << std::setw(14) << "Variance"
                  << std::setw(18) << "Status"
                  << '\n';

        std::cout << std::string(92, '-') << '\n';

        for (const auto& [category, record] : records) {
            std::cout << std::left
                      << std::setw(28) << category
                      << std::right
                      << std::setw(14) << record.planned
                      << std::setw(14) << record.actual
                      << std::setw(14) << record.variance()
                      << std::setw(18) << statusToString(record.status())
                      << '\n';
        }

        const Money plan = plannedTotal();
        const Money actual = actualTotal();
        const Money variance = totalVariance();

        std::cout << std::string(92, '-') << '\n';
        std::cout << std::left
                  << std::setw(28) << "TOTAL"
                  << std::right
                  << std::setw(14) << plan
                  << std::setw(14) << actual
                  << std::setw(14) << variance
                  << std::setw(18)
                  << statusToString(
                         variance > 0
                             ? VarianceStatus::Unfavorable
                             : variance < 0
                                   ? VarianceStatus::Favorable
                                   : VarianceStatus::OnPlan)
                  << '\n';

        if (plan != 0) {
            std::cout << std::fixed << std::setprecision(2)
                      << "Total variance rate: "
                      << percentage(variance, plan)
                      << "%\n";
        } else {
            std::cout << "Total variance rate: not defined because the plan is zero.\n";
        }
    }
};

void printExceptionScenario() {
    std::cout << "\nVALIDATION CASES\n";
    std::cout << std::string(92, '=') << '\n';

    RepositoryCostGovernance governance;

    try {
        governance.createBudgetLine("Invalid", -500);
    } catch (const std::exception& error) {
        std::cout << "Rejected negative budget: "
                  << error.what() << '\n';
    }

    try {
        governance.recordActualCost("Missing category", 100);
    } catch (const std::exception& error) {
        std::cout << "Rejected unknown category: "
                  << error.what() << '\n';
    }
}

void printDrivers(const RepositoryCostGovernance& governance) {
    std::cout << "\nVARIANCE DRIVERS\n";
    std::cout << std::string(92, '=') << '\n';

    const auto unfavorable = governance.unfavorableItems();

    if (unfavorable.empty()) {
        std::cout << "No unfavorable cost lines detected.\n";
    } else {
        for (const auto& record : unfavorable) {
            std::cout << record.category
                      << ": +" << record.variance()
                      << " above plan";

            if (record.planned != 0) {
                std::cout << " (" << std::fixed << std::setprecision(2)
                          << percentage(record.variance(), record.planned)
                          << "%)";
            }

            std::cout << '\n';
        }
    }

    const auto favorable = governance.favorableItems();

    std::cout << "\nFAVORABLE OFFSETS\n";

    for (const auto& record : favorable) {
        std::cout << record.category
                  << ": " << record.variance()
                  << " below plan\n";
    }
}

int main() {
    try {
        RepositoryCostGovernance governance;

        /*
         * The case study represents a technology program whose approved budget
         * is compared with posted actual expenditure. Costs are kept in minor
         * currency units so the arithmetic remains deterministic.
         */
        governance.createBudgetLine("Cloud infrastructure", 1200000);
        governance.createBudgetLine("External contractors", 3000000);
        governance.createBudgetLine("Testing services", 800000);
        governance.createBudgetLine("Security tooling", 650000);
        governance.createBudgetLine("Travel and workshops", 350000);
        governance.createBudgetLine("Training", 500000);

        governance.recordActualCost("Cloud infrastructure", 1380000);
        governance.recordActualCost("External contractors", 2875000);
        governance.recordActualCost("Testing services", 920000);
        governance.recordActualCost("Security tooling", 610000);
        governance.recordActualCost("Travel and workshops", 420000);
        governance.recordActualCost("Training", 475000);

        governance.printGovernanceReport();
        printDrivers(governance);
        printExceptionScenario();

        RepositoryCostGovernance zeroBaseline;
        zeroBaseline.createBudgetLine("Unplanned emergency", 0);
        zeroBaseline.recordActualCost("Unplanned emergency", 25000);

        std::cout << "\nZERO-BASELINE ANALYSIS\n";
        std::cout << std::string(92, '=') << '\n';
        std::cout << "Planned: 0\n";
        std::cout << "Actual:  25000\n";
        std::cout << "Variance: 25000\n";
        std::cout << "Variance percentage is intentionally undefined because "
                     "the planned baseline is zero.\n";

    } catch (const std::exception& error) {
        std::cerr << "Fatal cost-analysis error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
