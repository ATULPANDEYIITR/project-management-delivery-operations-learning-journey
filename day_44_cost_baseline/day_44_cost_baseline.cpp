#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Repository-independent project cost control case study:
 * a public infrastructure project with work-package budgets, time-phased
 * spending, earned-value analysis, and governed baseline revisions.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic cost_baseline.cpp -o cost_baseline
 *
 * Execute:
 *   ./cost_baseline
 *
 * Monetary values are stored as integer paise, avoiding binary floating-point
 * accumulation in the budget ledger.
 */

using Money = long long;

constexpr Money RUPEES_TO_PAISE = 100;

Money rupees(long long value) {
    if (value < 0) {
        throw std::invalid_argument("Negative amounts are not allowed.");
    }
    return value * RUPEES_TO_PAISE;
}

std::string formatMoney(Money value) {
    std::ostringstream output;
    output << (value < 0 ? "-₹" : "₹")
           << std::fixed << std::setprecision(2)
           << static_cast<double>(std::llabs(value)) / 100.0;
    return output.str();
}

struct WorkPackage {
    std::string code;
    std::string description;
    Money approvedEstimate;
};

struct BudgetAllocation {
    std::string month;
    std::string packageCode;
    Money amount;
};

struct ActualCost {
    std::string id;
    std::string month;
    std::string packageCode;
    Money amount;
    bool approved;
};

struct Progress {
    std::string month;
    std::string packageCode;
    int percentage;
};

struct Metrics {
    Money budgetAtCompletion;
    Money plannedValue;
    Money earnedValue;
    Money actualCost;
    Money costVariance;
    Money scheduleVariance;
    std::optional<double> costPerformanceIndex;
    std::optional<double> schedulePerformanceIndex;
    std::optional<Money> estimateAtCompletion;
};

class CostBaseline {
private:
    std::string id_;
    std::string project_;
    std::map<std::string, WorkPackage> packages_;
    std::vector<BudgetAllocation> allocations_;
    bool approved_ = false;
    std::string approver_;

public:
    CostBaseline(
        std::string id,
        std::string project,
        std::map<std::string, WorkPackage> packages,
        std::vector<BudgetAllocation> allocations
    )
        : id_(std::move(id)),
          project_(std::move(project)),
          packages_(std::move(packages)),
          allocations_(std::move(allocations)) {
        if (id_.empty() || project_.empty() || packages_.empty()) {
            throw std::invalid_argument("Baseline identity and packages are required.");
        }

        for (const auto& [key, package] : packages_) {
            if (key != package.code || package.approvedEstimate < 0) {
                throw std::invalid_argument("Invalid work-package definition.");
            }
        }

        validateAllocations();
    }

    void validateAllocations() const {
        std::map<std::string, Money> allocatedByPackage;

        for (const auto& allocation : allocations_) {
            if (!packages_.count(allocation.packageCode)) {
                throw std::invalid_argument("Allocation references an unknown package.");
            }
            if (allocation.month.size() != 7 || allocation.month[4] != '-') {
                throw std::invalid_argument("Month must use YYYY-MM format.");
            }
            if (allocation.amount < 0) {
                throw std::invalid_argument("Budget allocation cannot be negative.");
            }
            allocatedByPackage[allocation.packageCode] += allocation.amount;
        }

        for (const auto& [code, package] : packages_) {
            if (allocatedByPackage[code] != package.approvedEstimate) {
                throw std::invalid_argument(
                    "Time-phased allocation does not match package estimate: " + code
                );
            }
        }
    }

    void approve(const std::string& approver) {
        if (approved_) {
            throw std::logic_error("Baseline has already been approved.");
        }
        if (approver.empty()) {
            throw std::invalid_argument("Approver is required.");
        }

        validateAllocations();
        approved_ = true;
        approver_ = approver;
    }

    bool approved() const {
        return approved_;
    }

    Money budgetAtCompletion() const {
        Money total = 0;
        for (const auto& [code, package] : packages_) {
            (void)code;
            total += package.approvedEstimate;
        }
        return total;
    }

    Money plannedValueThrough(const std::string& month) const {
        Money total = 0;
        for (const auto& allocation : allocations_) {
            if (allocation.month <= month) {
                total += allocation.amount;
            }
        }
        return total;
    }

    Money packageBudget(const std::string& code) const {
        auto iterator = packages_.find(code);
        if (iterator == packages_.end()) {
            throw std::invalid_argument("Unknown package: " + code);
        }
        return iterator->second.approvedEstimate;
    }

    const std::string& project() const {
        return project_;
    }

    const std::string& id() const {
        return id_;
    }

    const std::vector<BudgetAllocation>& allocations() const {
        return allocations_;
    }
};

class CostControlEngine {
private:
    const CostBaseline& baseline_;
    std::vector<ActualCost> costs_;
    std::vector<Progress> progress_;
    std::set<std::string> costIds_;

    void requireApprovedBaseline() const {
        if (!baseline_.approved()) {
            throw std::logic_error("An approved baseline is required.");
        }
    }

public:
    explicit CostControlEngine(const CostBaseline& baseline)
        : baseline_(baseline) {}

    void recordCost(const ActualCost& cost) {
        requireApprovedBaseline();

        if (cost.id.empty() || cost.amount < 0) {
            throw std::invalid_argument("Invalid actual-cost record.");
        }
        if (!costIds_.insert(cost.id).second) {
            throw std::invalid_argument("Duplicate actual-cost ID.");
        }

        // Only approved entries enter the official actual-cost ledger.
        if (cost.approved) {
            baseline_.packageBudget(cost.packageCode);
            costs_.push_back(cost);
        }
    }

    void recordProgress(const Progress& entry) {
        requireApprovedBaseline();

        if (entry.percentage < 0 || entry.percentage > 100) {
            throw std::invalid_argument("Completion must be between 0 and 100.");
        }

        baseline_.packageBudget(entry.packageCode);

        auto previous = std::find_if(
            progress_.begin(),
            progress_.end(),
            [&](const Progress& item) {
                return item.month == entry.month &&
                       item.packageCode == entry.packageCode;
            }
        );

        if (previous != progress_.end()) {
            if (entry.percentage < previous->percentage) {
                throw std::invalid_argument("Completion cannot decrease in a period.");
            }
            *previous = entry;
        } else {
            progress_.push_back(entry);
        }
    }

    Money actualCostThrough(const std::string& month) const {
        Money total = 0;
        for (const auto& cost : costs_) {
            if (cost.month <= month && cost.approved) {
                total += cost.amount;
            }
        }
        return total;
    }

    Money earnedValueThrough(const std::string& month) const {
        // Keep the latest progress observation per work package.
        std::map<std::string, Progress> latest;

        for (const auto& item : progress_) {
            if (item.month <= month) {
                auto found = latest.find(item.packageCode);
                if (found == latest.end() || found->second.month < item.month) {
                    latest[item.packageCode] = item;
                }
            }
        }

        Money total = 0;
        for (const auto& [code, item] : latest) {
            const Money packageBudget = baseline_.packageBudget(code);
            total += packageBudget * item.percentage / 100;
        }
        return total;
    }

    Metrics evaluate(const std::string& month) const {
        requireApprovedBaseline();

        const Money bac = baseline_.budgetAtCompletion();
        const Money pv = baseline_.plannedValueThrough(month);
        const Money ev = earnedValueThrough(month);
        const Money ac = actualCostThrough(month);

        Metrics result{
            bac,
            pv,
            ev,
            ac,
            ev - ac,
            ev - pv,
            std::nullopt,
            std::nullopt,
            std::nullopt
        };

        if (ac > 0) {
            result.costPerformanceIndex =
                static_cast<double>(ev) / static_cast<double>(ac);
        }

        if (pv > 0) {
            result.schedulePerformanceIndex =
                static_cast<double>(ev) / static_cast<double>(pv);
        }

        if (result.costPerformanceIndex.has_value() &&
            result.costPerformanceIndex.value() > 0.0) {
            const double estimate =
                static_cast<double>(bac) /
                result.costPerformanceIndex.value();
            result.estimateAtCompletion =
                static_cast<Money>(std::llround(estimate));
        }

        return result;
    }
};

class ChangeControl {
public:
    enum class Status { Pending, Approved, Rejected };

    struct Request {
        std::string id;
        std::string description;
        Money amountDelta;
        Status status = Status::Pending;
        std::string decision;
    };

private:
    std::map<std::string, Request> requests_;

public:
    void propose(Request request) {
        if (request.id.empty() || request.description.empty()) {
            throw std::invalid_argument("Change ID and description are required.");
        }
        if (request.amountDelta == 0) {
            throw std::invalid_argument("A change must alter the budget.");
        }
        if (requests_.count(request.id)) {
            throw std::invalid_argument("Duplicate change request ID.");
        }
        requests_.emplace(request.id, std::move(request));
    }

    void decide(
        const std::string& id,
        Status decision,
        const std::string& approver,
        const std::string& reason
    ) {
        auto found = requests_.find(id);

        if (found == requests_.end()) {
            throw std::invalid_argument("Unknown change request.");
        }
        if (found->second.status != Status::Pending) {
            throw std::logic_error("Change request has already been decided.");
        }
        if (approver.empty() || reason.empty()) {
            throw std::invalid_argument("Approver and decision reason are required.");
        }
        if (decision == Status::Pending) {
            throw std::invalid_argument("A decision must be approved or rejected.");
        }

        found->second.status = decision;
        found->second.decision = approver + ": " + reason;
    }

    const Request& get(const std::string& id) const {
        auto found = requests_.find(id);
        if (found == requests_.end()) {
            throw std::invalid_argument("Unknown change request.");
        }
        return found->second;
    }
};

void printMetrics(const Metrics& metrics) {
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Budget at completion: " << formatMoney(metrics.budgetAtCompletion) << '\n';
    std::cout << "Planned value:        " << formatMoney(metrics.plannedValue) << '\n';
    std::cout << "Earned value:         " << formatMoney(metrics.earnedValue) << '\n';
    std::cout << "Actual cost:          " << formatMoney(metrics.actualCost) << '\n';
    std::cout << "Cost variance:        " << formatMoney(metrics.costVariance) << '\n';
    std::cout << "Schedule variance:    " << formatMoney(metrics.scheduleVariance) << '\n';

    if (metrics.costPerformanceIndex) {
        std::cout << "CPI:                  " << *metrics.costPerformanceIndex << '\n';
    } else {
        std::cout << "CPI:                  N/A\n";
    }

    if (metrics.schedulePerformanceIndex) {
        std::cout << "SPI:                  " << *metrics.schedulePerformanceIndex << '\n';
    } else {
        std::cout << "SPI:                  N/A\n";
    }

    if (metrics.estimateAtCompletion) {
        std::cout << "Forecast EAC:          "
                  << formatMoney(*metrics.estimateAtCompletion) << '\n';
    } else {
        std::cout << "Forecast EAC:          N/A\n";
    }
}

int main() {
    try {
        std::map<std::string, WorkPackage> packages{
            {"CIVIL", {"CIVIL", "Civil works", rupees(450000)}},
            {"ELECT", {"ELECT", "Electrical installation", rupees(300000)}},
            {"TEST", {"TEST", "Testing and commissioning", rupees(250000)}}
        };

        std::vector<BudgetAllocation> allocations{
            {"2026-01", "CIVIL", rupees(150000)},
            {"2026-02", "CIVIL", rupees(180000)},
            {"2026-03", "CIVIL", rupees(120000)},
            {"2026-02", "ELECT", rupees(50000)},
            {"2026-03", "ELECT", rupees(150000)},
            {"2026-04", "ELECT", rupees(100000)},
            {"2026-03", "TEST", rupees(50000)},
            {"2026-04", "TEST", rupees(100000)},
            {"2026-05", "TEST", rupees(100000)}
        };

        CostBaseline baseline(
            "BASE-001",
            "District Hospital Modernization",
            packages,
            allocations
        );

        baseline.approve("Project Director");
        CostControlEngine engine(baseline);

        std::vector<ActualCost> costs{
            {"C-101", "2026-01", "CIVIL", rupees(140000), true},
            {"C-102", "2026-02", "CIVIL", rupees(200000), true},
            {"C-103", "2026-02", "ELECT", rupees(60000), true},
            {"C-104", "2026-03", "CIVIL", rupees(130000), true},
            {"C-105", "2026-03", "ELECT", rupees(140000), true},
            {"C-106", "2026-03", "TEST", rupees(30000), true},
            {"C-107", "2026-03", "TEST", rupees(25000), false}
        };

        for (const auto& cost : costs) {
            engine.recordCost(cost);
        }

        std::vector<Progress> progress{
            {"2026-01", "CIVIL", 30},
            {"2026-02", "CIVIL", 70},
            {"2026-03", "CIVIL", 100},
            {"2026-02", "ELECT", 10},
            {"2026-03", "ELECT", 55},
            {"2026-03", "TEST", 10}
        };

        for (const auto& item : progress) {
            engine.recordProgress(item);
        }

        std::cout << "Project: " << baseline.project() << '\n';
        std::cout << "Baseline: " << baseline.id() << '\n';
        std::cout << "Reporting period: 2026-03\n\n";
        printMetrics(engine.evaluate("2026-03"));

        ChangeControl changes;
        changes.propose({
            "CR-014",
            "Additional electrical safety panels",
            rupees(50000)
        });

        changes.decide(
            "CR-014",
            ChangeControl::Status::Approved,
            "Project Director",
            "Safety requirement accepted; formal baseline revision required."
        );

        const auto& request = changes.get("CR-014");
        std::cout << "\nChange request: " << request.id << '\n';
        std::cout << "Decision: " << request.decision << '\n';
        std::cout << "Baseline total remains "
                  << formatMoney(baseline.budgetAtCompletion()) << '\n';

        // An empty reporting period has zero PV and AC; the engine avoids
        // dividing by zero and reports unavailable efficiency ratios.
        const Metrics early = engine.evaluate("2025-12");
        if (early.costPerformanceIndex.has_value()) {
            throw std::logic_error("Expected an undefined CPI.");
        }

        std::cout << "\nEdge-case validation passed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Cost-control error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
