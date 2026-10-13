#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Enterprise Project Budget Governance Engine
 *
 * Case study:
 * A technology organization controls project spending through a budget
 * baseline. The engine evaluates:
 *   - budget categories
 *   - actual expenditure
 *   - committed expenditure
 *   - contingency
 *   - approved scope changes
 *   - status checks on financial data
 *   - merge-like authorization of a budget release
 *
 * The design uses C++17 standard-library facilities only.
 */

using Money = long long; // Store currency in the smallest unit, such as paise.

Money parseMoney(double amount) {
    if (amount < 0.0) {
        throw std::invalid_argument("Money cannot be negative.");
    }

    return static_cast<Money>(amount * 100.0 + 0.5);
}

double displayMoney(Money amount) {
    return static_cast<double>(amount) / 100.0;
}

enum class ProjectState {
    Draft,
    Approved,
    Active,
    Closed
};

enum class ChangeState {
    Proposed,
    Approved,
    Rejected
};

struct BudgetLine {
    std::string category;
    std::string description;
    Money planned{};
    Money committed{};
    Money actual{};

    Money variance() const {
        return planned - actual;
    }

    double utilization() const {
        if (planned == 0) {
            return 0.0;
        }

        return static_cast<double>(actual) /
               static_cast<double>(planned) * 100.0;
    }
};

struct ChangeRequest {
    std::string id;
    std::string description;
    Money amount{};
    ChangeState state{ChangeState::Proposed};
};

class BudgetPolicy {
public:
    explicit BudgetPolicy(double contingencyRate,
                          Money approvalThreshold)
        : contingencyRate_(contingencyRate),
          approvalThreshold_(approvalThreshold) {
        if (contingencyRate < 0.0 || contingencyRate > 1.0) {
            throw std::invalid_argument(
                "Contingency rate must be between 0 and 1."
            );
        }
    }

    Money contingency(Money directBudget) const {
        return static_cast<Money>(
            static_cast<double>(directBudget) * contingencyRate_ + 0.5
        );
    }

    bool requiresSeniorApproval(Money changeAmount) const {
        return changeAmount >= approvalThreshold_;
    }

private:
    double contingencyRate_;
    Money approvalThreshold_;
};

class ProjectBudget {
public:
    ProjectBudget(std::string id,
                  std::string name,
                  std::string manager,
                  BudgetPolicy policy)
        : id_(std::move(id)),
          name_(std::move(name)),
          manager_(std::move(manager)),
          policy_(std::move(policy)) {}

    void addLine(const BudgetLine& line) {
        if (state_ != ProjectState::Draft &&
            state_ != ProjectState::Active) {
            throw std::logic_error(
                "Budget lines cannot be changed in the current state."
            );
        }

        if (line.planned <= 0) {
            throw std::invalid_argument(
                "A budget line must have a positive planned amount."
            );
        }

        if (lines_.contains(line.category)) {
            throw std::invalid_argument(
                "Duplicate budget category: " + line.category
            );
        }

        lines_.emplace(line.category, line);
    }

    void approve() {
        if (lines_.empty()) {
            throw std::logic_error(
                "A budget cannot be approved without cost categories."
            );
        }

        state_ = ProjectState::Approved;
    }

    void activate() {
        if (state_ != ProjectState::Approved) {
            throw std::logic_error(
                "Only approved budgets can become active."
            );
        }

        state_ = ProjectState::Active;
    }

    void commit(const std::string& category, Money amount) {
        requireActive();
        requirePositive(amount);

        auto& line = findLine(category);
        line.committed += amount;
    }

    void spend(const std::string& category, Money amount) {
        requireActive();
        requirePositive(amount);

        auto& line = findLine(category);
        line.actual += amount;
    }

    void submitChange(ChangeRequest request) {
        requireActive();

        if (request.amount <= 0) {
            throw std::invalid_argument(
                "Change request must have a positive amount."
            );
        }

        if (changes_.contains(request.id)) {
            throw std::invalid_argument(
                "Duplicate change request: " + request.id
            );
        }

        changes_.emplace(request.id, std::move(request));
    }

    void approveChange(const std::string& id) {
        auto iterator = changes_.find(id);

        if (iterator == changes_.end()) {
            throw std::invalid_argument("Unknown change request.");
        }

        if (iterator->second.state != ChangeState::Proposed) {
            throw std::logic_error(
                "Only proposed changes can be approved."
            );
        }

        /*
         * Large scope changes have a separate policy signal. This does not
         * automatically reject them; it identifies the governance path.
         */
        if (policy_.requiresSeniorApproval(iterator->second.amount)) {
            std::cout
                << "Governance alert: senior approval required for "
                << iterator->second.id << "\n";
        }

        iterator->second.state = ChangeState::Approved;
    }

    Money directBudget() const {
        Money total = 0;

        for (const auto& [category, line] : lines_) {
            total += line.planned;
        }

        return total;
    }

    Money approvedChanges() const {
        Money total = 0;

        for (const auto& [id, request] : changes_) {
            if (request.state == ChangeState::Approved) {
                total += request.amount;
            }
        }

        return total;
    }

    Money authorizedBudget() const {
        return directBudget() +
               policy_.contingency(directBudget()) +
               approvedChanges();
    }

    Money actualSpend() const {
        Money total = 0;

        for (const auto& [category, line] : lines_) {
            total += line.actual;
        }

        return total;
    }

    Money committedSpend() const {
        Money total = 0;

        for (const auto& [category, line] : lines_) {
            total += line.committed;
        }

        return total;
    }

    Money projectedCost() const {
        Money remainingCommitments = 0;

        for (const auto& [category, line] : lines_) {
            if (line.committed > line.actual) {
                remainingCommitments += line.committed - line.actual;
            }
        }

        return actualSpend() + remainingCommitments;
    }

    bool mergeEligible() const {
        /*
         * The name "merge eligible" is deliberately used as a software
         * governance analogy: the project budget may proceed only when
         * required financial conditions are satisfied.
         */
        return state_ == ProjectState::Active &&
               projectedCost() <= authorizedBudget();
    }

    void printReport() const {
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "\nPROJECT BUDGET GOVERNANCE REPORT\n";
        std::cout << std::string(72, '=') << "\n";
        std::cout << "Project:             " << name_ << "\n";
        std::cout << "Manager:             " << manager_ << "\n";
        std::cout << "Direct budget:       "
                  << displayMoney(directBudget()) << "\n";
        std::cout << "Contingency:         "
                  << displayMoney(policy_.contingency(directBudget()))
                  << "\n";
        std::cout << "Approved changes:    "
                  << displayMoney(approvedChanges()) << "\n";
        std::cout << "Authorized budget:   "
                  << displayMoney(authorizedBudget()) << "\n";
        std::cout << "Actual spend:        "
                  << displayMoney(actualSpend()) << "\n";
        std::cout << "Committed spend:     "
                  << displayMoney(committedSpend()) << "\n";
        std::cout << "Projected cost:      "
                  << displayMoney(projectedCost()) << "\n";
        std::cout << "Variance:            "
                  << displayMoney(authorizedBudget() - actualSpend())
                  << "\n";
        std::cout << "Governance status:   "
                  << (mergeEligible() ? "ELIGIBLE" : "BLOCKED")
                  << "\n";

        std::cout << "\nCATEGORY ANALYSIS\n";

        for (const auto& [category, line] : lines_) {
            std::cout << std::left << std::setw(16)
                      << category
                      << " planned=" << std::setw(12)
                      << displayMoney(line.planned)
                      << " actual=" << std::setw(12)
                      << displayMoney(line.actual)
                      << " variance="
                      << displayMoney(line.variance())
                      << " usage=" << line.utilization()
                      << "%\n";
        }
    }

private:
    BudgetLine& findLine(const std::string& category) {
        auto iterator = lines_.find(category);

        if (iterator == lines_.end()) {
            throw std::invalid_argument(
                "Unknown budget category: " + category
            );
        }

        return iterator->second;
    }

    void requireActive() const {
        if (state_ != ProjectState::Active) {
            throw std::logic_error(
                "The operation requires an active budget."
            );
        }
    }

    static void requirePositive(Money amount) {
        if (amount <= 0) {
            throw std::invalid_argument(
                "Transaction amount must be positive."
            );
        }
    }

    std::string id_;
    std::string name_;
    std::string manager_;
    BudgetPolicy policy_;
    ProjectState state_{ProjectState::Draft};

    std::map<std::string, BudgetLine> lines_;
    std::map<std::string, ChangeRequest> changes_;
};

int main() {
    try {
        BudgetPolicy policy(
            0.12,
            parseMoney(200000.0)
        );

        ProjectBudget budget(
            "PRJ-2026-042",
            "Enterprise Data Platform",
            "Technology PMO",
            policy
        );

        budget.addLine({
            "Engineering",
            "Application and data engineering",
            parseMoney(4200000.0)
        });

        budget.addLine({
            "Cloud",
            "Infrastructure and managed services",
            parseMoney(1350000.0)
        });

        budget.addLine({
            "Security",
            "Security assurance and tooling",
            parseMoney(650000.0)
        });

        budget.addLine({
            "Testing",
            "Integration and performance testing",
            parseMoney(500000.0)
        });

        budget.approve();
        budget.activate();

        budget.commit("Engineering", parseMoney(2800000.0));
        budget.spend("Engineering", parseMoney(2100000.0));

        budget.commit("Cloud", parseMoney(850000.0));
        budget.spend("Cloud", parseMoney(640000.0));

        budget.commit("Security", parseMoney(400000.0));
        budget.spend("Security", parseMoney(270000.0));

        budget.commit("Testing", parseMoney(180000.0));
        budget.spend("Testing", parseMoney(120000.0));

        budget.submitChange({
            "CR-001",
            "Expanded compliance testing",
            parseMoney(240000.0),
            ChangeState::Proposed
        });

        budget.approveChange("CR-001");

        budget.printReport();

        std::cout << "\nEDGE-CASE CHECK\n";

        try {
            budget.spend("Unknown", parseMoney(1000.0));
        } catch (const std::exception& error) {
            std::cout << "Rejected invalid category: "
                      << error.what() << "\n";
        }

        try {
            budget.commit("Cloud", parseMoney(-500.0));
        } catch (const std::exception& error) {
            std::cout << "Rejected negative transaction: "
                      << error.what() << "\n";
        }
    } catch (const std::exception& error) {
        std::cerr << "Budget engine failure: "
                  << error.what() << "\n";
        return 1;
    }

    return 0;
}
