#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

enum class CostCategory {
    Labor,
    Cloud,
    Software,
    Equipment,
    Travel,
    Contractor
};

std::string categoryName(CostCategory category) {
    switch (category) {
        case CostCategory::Labor: return "Labor";
        case CostCategory::Cloud: return "Cloud";
        case CostCategory::Software: return "Software";
        case CostCategory::Equipment: return "Equipment";
        case CostCategory::Travel: return "Travel";
        case CostCategory::Contractor: return "Contractor";
    }
    return "Unknown";
}

struct Expense {
    std::string id;
    CostCategory category;
    std::string description;
    double amount;
    std::string vendor;
    std::string expenseDate;
    bool approved;
    std::string invoice;
};

struct BudgetRule {
    double warningRatio;
    double criticalRatio;
};

class ProjectCostGovernance {
private:
    std::string projectId_;
    std::string projectName_;
    std::map<CostCategory, double> budget_;
    std::vector<Expense> expenses_;
    std::set<std::string> expenseIds_;
    std::set<std::string> invoices_;

    static void validateExpense(const Expense& expense) {
        if (expense.id.empty()) {
            throw std::invalid_argument("Expense ID cannot be empty.");
        }

        if (expense.amount <= 0.0) {
            throw std::invalid_argument(
                "Expense amount must be greater than zero."
            );
        }

        if (expense.vendor.empty()) {
            throw std::invalid_argument("Vendor cannot be empty.");
        }

        if (expense.expenseDate.empty()) {
            throw std::invalid_argument("Expense date cannot be empty.");
        }
    }

public:
    ProjectCostGovernance(
        std::string projectId,
        std::string projectName,
        std::map<CostCategory, double> budget
    )
        : projectId_(std::move(projectId)),
          projectName_(std::move(projectName)),
          budget_(std::move(budget)) {
        if (projectId_.empty() || projectName_.empty()) {
            throw std::invalid_argument(
                "Project identity must be provided."
            );
        }

        for (const auto& [category, amount] : budget_) {
            if (amount < 0.0) {
                throw std::invalid_argument(
                    "Budget cannot contain negative values."
                );
            }
        }
    }

    void recordExpense(const Expense& expense) {
        validateExpense(expense);

        if (expenseIds_.contains(expense.id)) {
            throw std::invalid_argument(
                "Duplicate expense ID: " + expense.id
            );
        }

        if (!expense.invoice.empty() &&
            invoices_.contains(expense.invoice)) {
            throw std::invalid_argument(
                "Duplicate invoice: " + expense.invoice
            );
        }

        /*
         * The invoice set prevents the same invoice from being counted
         * twice. This is a business-integrity rule, not just formatting.
         */
        expenseIds_.insert(expense.id);

        if (!expense.invoice.empty()) {
            invoices_.insert(expense.invoice);
        }

        expenses_.push_back(expense);
    }

    double totalBudget() const {
        double total = 0.0;

        for (const auto& [category, amount] : budget_) {
            total += amount;
        }

        return total;
    }

    double totalActual() const {
        return std::accumulate(
            expenses_.begin(),
            expenses_.end(),
            0.0,
            [](double total, const Expense& expense) {
                return total + expense.amount;
            }
        );
    }

    std::map<CostCategory, double> actualByCategory() const {
        std::map<CostCategory, double> totals;

        for (const auto& expense : expenses_) {
            totals[expense.category] += expense.amount;
        }

        return totals;
    }

    std::map<CostCategory, double> varianceByCategory() const {
        const auto actual = actualByCategory();
        std::map<CostCategory, double> variance;

        for (const auto& [category, budget] : budget_) {
            const auto actualIt = actual.find(category);
            const double spent =
                actualIt == actual.end() ? 0.0 : actualIt->second;

            variance[category] = budget - spent;
        }

        return variance;
    }

    std::vector<std::string> evaluateBudget(
        const BudgetRule& rule
    ) const {
        std::vector<std::string> alerts;
        const auto actual = actualByCategory();

        for (const auto& [category, budget] : budget_) {
            const auto actualIt = actual.find(category);
            const double spent =
                actualIt == actual.end() ? 0.0 : actualIt->second;

            if (budget == 0.0 && spent > 0.0) {
                alerts.push_back(
                    categoryName(category) +
                    ": spending exists without a budget."
                );
                continue;
            }

            if (budget <= 0.0) {
                continue;
            }

            const double ratio = spent / budget;

            if (ratio >= rule.criticalRatio) {
                std::ostringstream message;
                message << categoryName(category)
                        << ": critical utilization "
                        << std::fixed << std::setprecision(1)
                        << ratio * 100.0 << "%.";
                alerts.push_back(message.str());
            } else if (ratio >= rule.warningRatio) {
                std::ostringstream message;
                message << categoryName(category)
                        << ": warning utilization "
                        << std::fixed << std::setprecision(1)
                        << ratio * 100.0 << "%.";
                alerts.push_back(message.str());
            }
        }

        if (totalActual() > totalBudget()) {
            alerts.push_back("Project has exceeded its total budget.");
        }

        return alerts;
    }

    double projectedFinalCost(double elapsedDays, double totalDays) const {
        if (elapsedDays <= 0.0 || totalDays <= 0.0) {
            return 0.0;
        }

        if (elapsedDays >= totalDays) {
            return totalActual();
        }

        const double dailyRate = totalActual() / elapsedDays;
        return dailyRate * totalDays;
    }

    std::map<std::string, double> monthlyCost() const {
        std::map<std::string, double> result;

        for (const auto& expense : expenses_) {
            if (expense.expenseDate.size() >= 7) {
                const std::string month =
                    expense.expenseDate.substr(0, 7);
                result[month] += expense.amount;
            }
        }

        return result;
    }

    std::map<std::string, double> vendorExposure() const {
        std::map<std::string, double> result;

        for (const auto& expense : expenses_) {
            result[expense.vendor] += expense.amount;
        }

        return result;
    }

    std::vector<std::string> controlExceptions() const {
        std::vector<std::string> exceptions;

        for (const auto& expense : expenses_) {
            if (expense.amount >= 10000.0 && !expense.approved) {
                exceptions.push_back(
                    expense.id +
                    ": high-value expense lacks approval."
                );
            }
        }

        return exceptions;
    }

    void printReport(const BudgetRule& rule) const {
        std::cout << "\n=== PROJECT COST GOVERNANCE CASE STUDY ===\n";
        std::cout << "Project: " << projectName_ << "\n";

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "Budget: " << totalBudget() << "\n";
        std::cout << "Actual: " << totalActual() << "\n";
        std::cout << "Variance: "
                  << totalBudget() - totalActual() << "\n";

        if (totalBudget() > 0.0) {
            std::cout << "Utilization: "
                      << totalActual() / totalBudget() * 100.0
                      << "%\n";
        }

        std::cout << "\nCategory controls:\n";
        const auto actual = actualByCategory();

        for (const auto& [category, budget] : budget_) {
            const double spent = actual.contains(category)
                ? actual.at(category)
                : 0.0;

            std::cout << "  " << categoryName(category)
                      << " | budget=" << budget
                      << " | actual=" << spent
                      << " | variance=" << budget - spent
                      << "\n";
        }

        std::cout << "\nBudget alerts:\n";
        for (const auto& alert : evaluateBudget(rule)) {
            std::cout << "  " << alert << "\n";
        }

        std::cout << "\nMonthly cost:\n";
        for (const auto& [month, amount] : monthlyCost()) {
            std::cout << "  " << month << ": " << amount << "\n";
        }

        std::cout << "\nVendor exposure:\n";
        for (const auto& [vendor, amount] : vendorExposure()) {
            std::cout << "  " << vendor << ": " << amount << "\n";
        }

        std::cout << "\nControl exceptions:\n";
        for (const auto& exception : controlExceptions()) {
            std::cout << "  " << exception << "\n";
        }
    }
};

int main() {
    try {
        ProjectCostGovernance project(
            "PRJ-CPP-001",
            "Infrastructure Reliability Programme",
            {
                {CostCategory::Labor, 150000.0},
                {CostCategory::Cloud, 50000.0},
                {CostCategory::Software, 25000.0},
                {CostCategory::Equipment, 40000.0},
                {CostCategory::Travel, 15000.0},
                {CostCategory::Contractor, 35000.0}
            }
        );

        project.recordExpense({
            "CPP-001",
            CostCategory::Labor,
            "Reliability engineering allocation",
            30000.0,
            "Internal Engineering",
            "2026-01-31",
            true,
            "LAB-2026-01"
        });

        project.recordExpense({
            "CPP-002",
            CostCategory::Cloud,
            "Production observability workload",
            8200.0,
            "Cloud Provider",
            "2026-01-31",
            true,
            "CLOUD-2026-01"
        });

        project.recordExpense({
            "CPP-003",
            CostCategory::Equipment,
            "Network monitoring appliances",
            21000.0,
            "Infrastructure Supplier",
            "2026-02-12",
            true,
            "EQ-2026-02"
        });

        project.recordExpense({
            "CPP-004",
            CostCategory::Contractor,
            "Specialist reliability assessment",
            14500.0,
            "Reliability Consultancy",
            "2026-03-07",
            false,
            "CON-2026-03"
        });

        project.recordExpense({
            "CPP-005",
            CostCategory::Cloud,
            "February compute and storage",
            9700.0,
            "Cloud Provider",
            "2026-02-28",
            true,
            "CLOUD-2026-02"
        });

        project.recordExpense({
            "CPP-006",
            CostCategory::Software,
            "Observability platform subscription",
            12000.0,
            "Monitoring Vendor",
            "2026-03-01",
            true,
            "MON-2026-03"
        });

        project.printReport({0.80, 1.00});

        std::cout << "\nProjected final cost after 120 of 365 days: "
                  << project.projectedFinalCost(120.0, 365.0)
                  << "\n";

        std::cout << "\n=== INVALID INPUT TEST ===\n";

        try {
            project.recordExpense({
                "CPP-BAD",
                CostCategory::Cloud,
                "Invalid negative transaction",
                -500.0,
                "Cloud Provider",
                "2026-04-01",
                false,
                "BAD-001"
            });
        } catch (const std::exception& error) {
            std::cout << "Rejected invalid expense: "
                      << error.what() << "\n";
        }

        try {
            project.recordExpense({
                "CPP-DUP",
                CostCategory::Cloud,
                "Duplicate invoice test",
                500.0,
                "Cloud Provider",
                "2026-04-02",
                true,
                "CLOUD-2026-02"
            });
        } catch (const std::exception& error) {
            std::cout << "Rejected duplicate invoice: "
                      << error.what() << "\n";
        }

    } catch (const std::exception& error) {
        std::cerr << "Fatal cost tracking error: "
                  << error.what() << "\n";
        return 1;
    }

    return 0;
}
