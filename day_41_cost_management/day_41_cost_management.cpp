#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

enum class CostType {
    Labor,
    Material,
    Equipment,
    Software,
    Travel,
    Subcontract,
    Overhead
};

enum class Classification {
    Direct,
    Indirect
};

std::string toString(CostType type) {
    switch (type) {
        case CostType::Labor: return "Labor";
        case CostType::Material: return "Material";
        case CostType::Equipment: return "Equipment";
        case CostType::Software: return "Software";
        case CostType::Travel: return "Travel";
        case CostType::Subcontract: return "Subcontract";
        case CostType::Overhead: return "Overhead";
    }
    return "Unknown";
}

std::string toString(Classification classification) {
    return classification == Classification::Direct ? "Direct" : "Indirect";
}

struct CostItem {
    std::string name;
    CostType type;
    Classification classification;
    double budgeted;
    double actual;
    double committed;

    double forecast() const {
        return actual + committed;
    }

    double variance() const {
        return budgeted - actual;
    }
};

class ProjectCostGovernance {
private:
    std::string projectName;
    double approvedBudget;
    double managementReserve;
    std::vector<CostItem> costs;

    static void requireNonNegative(double value, const std::string& field) {
        if (value < 0.0) {
            throw std::invalid_argument(field + " cannot be negative.");
        }
    }

public:
    ProjectCostGovernance(
        std::string name,
        double budget,
        double reserve
    )
        : projectName(std::move(name)),
          approvedBudget(budget),
          managementReserve(reserve) {
        requireNonNegative(budget, "Approved budget");
        requireNonNegative(reserve, "Management reserve");
    }

    void addCost(CostItem item) {
        requireNonNegative(item.budgeted, "Budgeted cost");
        requireNonNegative(item.actual, "Actual cost");
        requireNonNegative(item.committed, "Committed cost");
        costs.push_back(std::move(item));
    }

    double plannedCost() const {
        double total = 0.0;
        for (const auto& item : costs) {
            total += item.budgeted;
        }
        return total;
    }

    double actualCost() const {
        double total = 0.0;
        for (const auto& item : costs) {
            total += item.actual;
        }
        return total;
    }

    double committedCost() const {
        double total = 0.0;
        for (const auto& item : costs) {
            total += item.committed;
        }
        return total;
    }

    double forecastAtCompletion() const {
        return actualCost() + committedCost();
    }

    double utilization() const {
        if (approvedBudget == 0.0) {
            return 0.0;
        }
        return actualCost() / approvedBudget * 100.0;
    }

    std::map<CostType, double> costByType() const {
        std::map<CostType, double> result;
        for (const auto& item : costs) {
            result[item.type] += item.actual;
        }
        return result;
    }

    std::string mergeControlStatus() const {
        if (actualCost() > approvedBudget) {
            return "OVER_BUDGET";
        }

        if (forecastAtCompletion() > approvedBudget + managementReserve) {
            return "RESERVE_INSUFFICIENT";
        }

        if (forecastAtCompletion() > approvedBudget) {
            return "RESERVE_REQUIRED";
        }

        if (utilization() >= 90.0) {
            return "HIGH_UTILIZATION";
        }

        if (utilization() >= 75.0) {
            return "WATCH";
        }

        return "WITHIN_PLAN";
    }

    void printCaseStudy() const {
        std::cout << "\n=== PROJECT COST GOVERNANCE CASE STUDY ===\n";
        std::cout << "Project: " << projectName << '\n';
        std::cout << "Approved budget: " << approvedBudget << '\n';
        std::cout << "Management reserve: " << managementReserve << '\n';
        std::cout << "Planned cost: " << plannedCost() << '\n';
        std::cout << "Actual cost: " << actualCost() << '\n';
        std::cout << "Committed cost: " << committedCost() << '\n';
        std::cout << "Forecast at completion: " << forecastAtCompletion() << '\n';
        std::cout << "Budget utilization: " << utilization() << "%\n";
        std::cout << "Control status: " << mergeControlStatus() << '\n';

        std::cout << "\nCost ledger:\n";
        for (const auto& item : costs) {
            std::cout << std::left << std::setw(25)
                      << item.name
                      << " type=" << std::setw(13) << toString(item.type)
                      << " class=" << std::setw(9)
                      << toString(item.classification)
                      << " budget=" << std::setw(10) << item.budgeted
                      << " actual=" << std::setw(10) << item.actual
                      << " committed=" << item.committed
                      << '\n';
        }

        std::cout << "\nCost concentration:\n";
        for (const auto& [type, value] : costByType()) {
            std::cout << "  " << std::setw(15) << toString(type)
                      << value << '\n';
        }

        std::cout << "\nCost-specific observations:\n";
        for (const auto& item : costs) {
            if (item.actual > item.budgeted) {
                std::cout << "  " << item.name
                          << " is above its budget by "
                          << item.actual - item.budgeted << ".\n";
            }

            if (item.committed > 0.0) {
                std::cout << "  " << item.name
                          << " has outstanding commitments of "
                          << item.committed << ".\n";
            }
        }
    }
};

struct EarnedValue {
    double bac;
    double pv;
    double ev;
    double ac;

    double cpi() const {
        if (ac == 0.0) {
            return 0.0;
        }
        return ev / ac;
    }

    double spi() const {
        if (pv == 0.0) {
            return 0.0;
        }
        return ev / pv;
    }

    double estimateAtCompletion() const {
        if (cpi() <= 0.0) {
            return 0.0;
        }
        return bac / cpi();
    }
};

int main() {
    try {
        ProjectCostGovernance project(
            "Regional Data Centre Modernization",
            500000.0,
            40000.0
        );

        project.addCost({
            "Engineering labor",
            CostType::Labor,
            Classification::Direct,
            165000.0,
            172000.0,
            18000.0
        });

        project.addCost({
            "Network equipment",
            CostType::Equipment,
            Classification::Direct,
            120000.0,
            110000.0,
            35000.0
        });

        project.addCost({
            "Security software",
            CostType::Software,
            Classification::Direct,
            70000.0,
            68000.0,
            5000.0
        });

        project.addCost({
            "Implementation contractor",
            CostType::Subcontract,
            Classification::Direct,
            80000.0,
            62000.0,
            30000.0
        });

        project.addCost({
            "Travel and site work",
            CostType::Travel,
            Classification::Direct,
            25000.0,
            19000.0,
            2000.0
        });

        project.addCost({
            "Corporate allocation",
            CostType::Overhead,
            Classification::Indirect,
            20000.0,
            18000.0,
            0.0
        });

        project.printCaseStudy();

        EarnedValue ev{
            project.approvedBudget(),
            250000.0,
            235000.0,
            project.actualCost()
        };

        std::cout << "\n=== EARNED VALUE ANALYSIS ===\n";
        std::cout << "BAC: " << ev.bac << '\n';
        std::cout << "PV:  " << ev.pv << '\n';
        std::cout << "EV:  " << ev.ev << '\n';
        std::cout << "AC:  " << ev.ac << '\n';
        std::cout << "CPI: " << ev.cpi() << '\n';
        std::cout << "SPI: " << ev.spi() << '\n';
        std::cout << "EAC: " << ev.estimateAtCompletion() << '\n';
        std::cout << "VAC: " << ev.bac - ev.estimateAtCompletion() << '\n';

    } catch (const std::exception& error) {
        std::cerr << "Cost governance error: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}
