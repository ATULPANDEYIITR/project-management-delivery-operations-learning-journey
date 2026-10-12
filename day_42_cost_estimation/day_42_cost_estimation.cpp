#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

enum class ReviewState {
    Pending,
    Approved,
    ChangesRequested,
    Rejected
};

enum class BranchState {
    Open,
    Protected,
    Archived
};

struct Review {
    std::string reviewer;
    ReviewState state;
    bool eligible;
};

struct CostDriver {
    std::string name;
    double quantity;
    double unitCost;
    std::string category;

    double total() const {
        return quantity * unitCost;
    }
};

struct Risk {
    std::string name;
    double probability;
    double impact;

    double expectedValue() const {
        return probability * impact;
    }
};

class CostEstimationEngine {
private:
    std::vector<CostDriver> drivers_;
    std::vector<Risk> risks_;

public:
    void addDriver(const CostDriver& driver) {
        if (driver.quantity < 0 || driver.unitCost < 0) {
            throw std::invalid_argument(
                "Cost driver quantity and unit cost must be non-negative."
            );
        }

        drivers_.push_back(driver);
    }

    void addRisk(const Risk& risk) {
        if (risk.probability < 0 || risk.probability > 1) {
            throw std::invalid_argument(
                "Risk probability must be between zero and one."
            );
        }

        if (risk.impact < 0) {
            throw std::invalid_argument(
                "Risk impact cannot be negative."
            );
        }

        risks_.push_back(risk);
    }

    double directCost() const {
        return std::accumulate(
            drivers_.begin(),
            drivers_.end(),
            0.0,
            [](double total, const CostDriver& driver) {
                return total + driver.total();
            }
        );
    }

    double expectedRiskCost() const {
        return std::accumulate(
            risks_.begin(),
            risks_.end(),
            0.0,
            [](double total, const Risk& risk) {
                return total + risk.expectedValue();
            }
        );
    }

    double managementReserve(double rate) const {
        if (rate < 0 || rate > 1) {
            throw std::invalid_argument(
                "Reserve rate must be between zero and one."
            );
        }

        return directCost() * rate;
    }

    double totalEstimate(double reserveRate) const {
        return directCost()
            + expectedRiskCost()
            + managementReserve(reserveRate);
    }

    std::map<std::string, double> costByCategory() const {
        std::map<std::string, double> result;

        for (const auto& driver : drivers_) {
            result[driver.category] += driver.total();
        }

        return result;
    }
};

class ProjectCostCaseStudy {
private:
    std::string projectName_;
    double approvedBudget_;
    CostEstimationEngine engine_;

public:
    ProjectCostCaseStudy(
        std::string projectName,
        double approvedBudget
    )
        : projectName_(std::move(projectName)),
          approvedBudget_(approvedBudget) {
        if (approvedBudget < 0) {
            throw std::invalid_argument(
                "Approved budget cannot be negative."
            );
        }
    }

    void buildEstimate() {
        /*
         * The case study separates direct cost drivers from uncertain
         * future events. This prevents risk exposure from being hidden
         * inside arbitrary unit rates.
         */
        engine_.addDriver({
            "Requirements engineering",
            120,
            90,
            "labor"
        });

        engine_.addDriver({
            "Application engineering",
            420,
            72,
            "labor"
        });

        engine_.addDriver({
            "Quality assurance",
            180,
            58,
            "labor"
        });

        engine_.addDriver({
            "Security validation",
            60,
            105,
            "security"
        });

        engine_.addDriver({
            "Cloud environment",
            12,
            800,
            "infrastructure"
        });

        engine_.addDriver({
            "Training",
            10,
            650,
            "training"
        });

        engine_.addRisk({
            "External integration rework",
            0.25,
            22000
        });

        engine_.addRisk({
            "Security remediation",
            0.15,
            28000
        });

        engine_.addRisk({
            "Infrastructure consumption increase",
            0.20,
            15000
        });
    }

    void printReport() const {
        const double reserveRate = 0.05;
        const double direct = engine_.directCost();
        const double risk = engine_.expectedRiskCost();
        const double reserve = engine_.managementReserve(reserveRate);
        const double estimate = engine_.totalEstimate(reserveRate);
        const double variance = approvedBudget_ - estimate;

        std::cout << std::fixed << std::setprecision(2);

        std::cout << "\nPROJECT COST ESTIMATION CASE STUDY\n";
        std::cout << "Project: " << projectName_ << '\n';

        std::cout << "\nCost by category:\n";

        for (const auto& [category, value] :
             engine_.costByCategory()) {
            std::cout
                << "  " << std::left << std::setw(18)
                << category
                << std::right << std::setw(12)
                << value << '\n';
        }

        std::cout << "\nDirect cost:             " << direct << '\n';
        std::cout << "Expected risk cost:      " << risk << '\n';
        std::cout << "Management reserve:      " << reserve << '\n';
        std::cout << "Estimated total cost:    " << estimate << '\n';
        std::cout << "Approved budget:         " << approvedBudget_ << '\n';

        if (variance >= 0) {
            std::cout
                << "Budget headroom:         "
                << variance << '\n';
        } else {
            std::cout
                << "Funding gap:             "
                << std::abs(variance) << '\n';
        }
    }

    void runSensitivityAnalysis() const {
        std::cout << "\nSENSITIVITY ANALYSIS\n";

        const double base =
            engine_.totalEstimate(0.05);

        const std::vector<double> changes = {
            -0.10,
            -0.05,
            0.00,
            0.05,
            0.10,
            0.20
        };

        for (double change : changes) {
            const double adjusted =
                base * (1.0 + change);

            std::cout
                << std::setw(7)
                << change * 100.0
                << "% -> "
                << std::setw(12)
                << adjusted
                << '\n';
        }
    }
};

int main() {
    try {
        ProjectCostCaseStudy project(
            "Regional Infrastructure Monitoring Platform",
            200000.00
        );

        project.buildEstimate();
        project.printReport();
        project.runSensitivityAnalysis();

        std::cout << "\nValidation example:\n";

        try {
            CostEstimationEngine invalidEngine;

            invalidEngine.addDriver({
                "Invalid negative cost",
                10,
                -50,
                "labor"
            });
        } catch (const std::exception& error) {
            std::cout
                << "Rejected invalid cost driver: "
                << error.what()
                << '\n';
        }

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal estimation error: "
            << error.what()
            << '\n';

        return 1;
    }
}
