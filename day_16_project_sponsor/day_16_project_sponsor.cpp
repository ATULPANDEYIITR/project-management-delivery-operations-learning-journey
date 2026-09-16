/*
 * Project Sponsor and the Role of the Project Sponsor
 *
 * Industry-style C++17 case study:
 * Enterprise Customer Service Modernization Governance System
 *
 * The program models:
 *   - Project sponsorship
 *   - Strategic alignment
 *   - Stakeholders
 *   - Risk management
 *   - Benefits realization
 *   - Decision governance
 *   - Escalation
 *   - Change control
 *   - Budget oversight
 *   - Earned value indicators
 *   - Executive reporting
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic project_sponsor.cpp -o project_sponsor
 */

#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;


// ============================================================================
// Utility Functions
// ============================================================================

void requireNonNegative(double value, const string& fieldName) {
    if (!isfinite(value) || value < 0.0) {
        throw invalid_argument(fieldName + " must be a non-negative number.");
    }
}

void requireProbability(double value) {
    if (!isfinite(value) || value < 0.0 || value > 1.0) {
        throw invalid_argument("Probability must be between 0 and 1.");
    }
}

string formatMoney(double value) {
    ostringstream output;
    output << fixed << setprecision(2) << value;
    return output.str();
}


// ============================================================================
// Enumerations
// ============================================================================

enum class ProjectStatus {
    Initiating,
    Planning,
    Executing,
    AtRisk,
    OnHold,
    Completed,
    Cancelled
};

enum class DecisionType {
    Routine,
    Major,
    Strategic,
    Emergency
};

enum class RiskLevel {
    Low,
    Medium,
    High,
    Critical
};

enum class Influence {
    Low,
    Medium,
    High
};

string toString(ProjectStatus status) {
    switch (status) {
        case ProjectStatus::Initiating: return "Initiating";
        case ProjectStatus::Planning: return "Planning";
        case ProjectStatus::Executing: return "Executing";
        case ProjectStatus::AtRisk: return "At Risk";
        case ProjectStatus::OnHold: return "On Hold";
        case ProjectStatus::Completed: return "Completed";
        case ProjectStatus::Cancelled: return "Cancelled";
    }

    return "Unknown";
}

string toString(DecisionType type) {
    switch (type) {
        case DecisionType::Routine: return "Routine";
        case DecisionType::Major: return "Major";
        case DecisionType::Strategic: return "Strategic";
        case DecisionType::Emergency: return "Emergency";
    }

    return "Unknown";
}

string toString(RiskLevel level) {
    switch (level) {
        case RiskLevel::Low: return "Low";
        case RiskLevel::Medium: return "Medium";
        case RiskLevel::High: return "High";
        case RiskLevel::Critical: return "Critical";
    }

    return "Unknown";
}

string toString(Influence influence) {
    switch (influence) {
        case Influence::Low: return "Low";
        case Influence::Medium: return "Medium";
        case Influence::High: return "High";
    }

    return "Unknown";
}


// ============================================================================
// Date Representation
// ============================================================================

struct SimpleDate {
    int year;
    int month;
    int day;

    bool operator<(const SimpleDate& other) const {
        if (year != other.year) return year < other.year;
        if (month != other.month) return month < other.month;
        return day < other.day;
    }
};

SimpleDate todayDate() {
    using namespace chrono;

    const auto now = system_clock::now();
    const time_t currentTime = system_clock::to_time_t(now);

    tm localTime{};

#ifdef _WIN32
    localtime_s(&localTime, &currentTime);
#else
    localtime_r(&currentTime, &localTime);
#endif

    return {
        localTime.tm_year + 1900,
        localTime.tm_mon + 1,
        localTime.tm_mday
    };
}

SimpleDate daysFromToday(int offset) {
    using namespace chrono;

    const auto now = system_clock::now();
    const auto shifted = now + hours(24 * offset);
    const time_t timestamp = system_clock::to_time_t(shifted);

    tm localTime{};

#ifdef _WIN32
    localtime_s(&localTime, &timestamp);
#else
    localtime_r(&timestamp, &localTime);
#endif

    return {
        localTime.tm_year + 1900,
        localTime.tm_mon + 1,
        localTime.tm_mday
    };
}

string dateToString(const SimpleDate& date) {
    ostringstream output;
    output << setfill('0')
           << setw(4) << date.year << "-"
           << setw(2) << date.month << "-"
           << setw(2) << date.day;
    return output.str();
}


// ============================================================================
// Stakeholder
// ============================================================================

struct Stakeholder {
    string name;
    string role;
    Influence influence;
    Influence interest;
    int engagementPercentage;

    string engagementCategory() const {
        if (engagementPercentage >= 80) return "Highly engaged";
        if (engagementPercentage >= 60) return "Engaged";
        if (engagementPercentage >= 40) return "Neutral";
        return "Needs attention";
    }
};

string engagementAction(const Stakeholder& stakeholder) {
    if (
        stakeholder.influence == Influence::High &&
        stakeholder.interest == Influence::High
    ) {
        return "Manage closely";
    }

    if (
        stakeholder.influence == Influence::High &&
        stakeholder.interest == Influence::Low
    ) {
        return "Keep satisfied";
    }

    if (
        stakeholder.influence == Influence::Low &&
        stakeholder.interest == Influence::High
    ) {
        return "Keep informed";
    }

    return "Monitor";
}


// ============================================================================
// Risk
// ============================================================================

struct Risk {
    string id;
    string description;
    double probability;
    double impact;
    string owner;
    string mitigation;
    string status = "Open";

    double exposure() const {
        return probability * impact;
    }

    RiskLevel level() const {
        const double value = exposure();

        if (value >= 20.0) return RiskLevel::Critical;
        if (value >= 12.0) return RiskLevel::High;
        if (value >= 6.0) return RiskLevel::Medium;

        return RiskLevel::Low;
    }
};


// ============================================================================
// Benefit
// ============================================================================

struct Benefit {
    string id;
    string description;
    double baseline;
    double target;
    double current;
    string unit;
    string owner;

    double progressPercentage() const {
        const double denominator = target - baseline;

        if (abs(denominator) < numeric_limits<double>::epsilon()) {
            return current >= target ? 100.0 : 0.0;
        }

        const double raw =
            ((current - baseline) / denominator) * 100.0;

        return max(0.0, min(100.0, raw));
    }
};


// ============================================================================
// Decision
// ============================================================================

struct Decision {
    string id;
    string description;
    DecisionType type;
    SimpleDate requiredBy;
    string owner;
    bool decided = false;
    optional<string> outcome;

    bool overdue(const SimpleDate& referenceDate) const {
        return !decided && requiredBy < referenceDate;
    }

    void makeDecision(const string& decisionOutcome) {
        if (decisionOutcome.empty()) {
            throw invalid_argument("Decision outcome cannot be empty.");
        }

        decided = true;
        outcome = decisionOutcome;
    }
};


// ============================================================================
// Project
// ============================================================================

class Project {
private:
    string projectId_;
    string name_;
    string strategicObjective_;
    string sponsorName_;
    string projectManagerName_;
    double approvedBudget_;
    double currentForecast_;
    ProjectStatus status_;
    string scopeBaseline_;

public:
    vector<Stakeholder> stakeholders;
    vector<Risk> risks;
    vector<Benefit> benefits;
    vector<Decision> decisions;

    Project(
        string projectId,
        string name,
        string strategicObjective,
        string sponsorName,
        string projectManagerName,
        double approvedBudget,
        double currentForecast,
        string scopeBaseline
    )
        : projectId_(move(projectId)),
          name_(move(name)),
          strategicObjective_(move(strategicObjective)),
          sponsorName_(move(sponsorName)),
          projectManagerName_(move(projectManagerName)),
          approvedBudget_(approvedBudget),
          currentForecast_(currentForecast),
          status_(ProjectStatus::Initiating),
          scopeBaseline_(move(scopeBaseline)) {

        requireNonNegative(approvedBudget_, "Approved budget");
        requireNonNegative(currentForecast_, "Current forecast");
    }

    const string& name() const {
        return name_;
    }

    const string& strategicObjective() const {
        return strategicObjective_;
    }

    const string& sponsorName() const {
        return sponsorName_;
    }

    const string& projectManagerName() const {
        return projectManagerName_;
    }

    double approvedBudget() const {
        return approvedBudget_;
    }

    double currentForecast() const {
        return currentForecast_;
    }

    ProjectStatus status() const {
        return status_;
    }

    void setStatus(ProjectStatus status) {
        status_ = status;
    }

    double budgetVariance() const {
        return approvedBudget_ - currentForecast_;
    }

    double budgetVariancePercentage() const {
        if (approvedBudget_ == 0.0) return 0.0;
        return (budgetVariance() / approvedBudget_) * 100.0;
    }

    int criticalRiskCount() const {
        return static_cast<int>(
            count_if(
                risks.begin(),
                risks.end(),
                [](const Risk& risk) {
                    return risk.level() == RiskLevel::Critical;
                }
            )
        );
    }

    int overdueDecisionCount(const SimpleDate& today) const {
        return static_cast<int>(
            count_if(
                decisions.begin(),
                decisions.end(),
                [&today](const Decision& decision) {
                    return decision.overdue(today);
                }
            )
        );
    }

    double averageBenefitProgress() const {
        if (benefits.empty()) return 0.0;

        double total = 0.0;

        for (const Benefit& benefit : benefits) {
            total += benefit.progressPercentage();
        }

        return total / static_cast<double>(benefits.size());
    }

    bool increaseForecast(double amount) {
        requireNonNegative(amount, "Forecast increase");
        currentForecast_ += amount;
        return true;
    }
};


// ============================================================================
// Sponsor
// ============================================================================

class ProjectSponsor {
private:
    string name_;
    string title_;
    double authorityLimit_;
    vector<string> strategicPriorities_;
    vector<Project*> activeProjects_;

public:
    ProjectSponsor(
        string name,
        string title,
        double authorityLimit,
        vector<string> strategicPriorities
    )
        : name_(move(name)),
          title_(move(title)),
          authorityLimit_(authorityLimit),
          strategicPriorities_(move(strategicPriorities)) {

        requireNonNegative(authorityLimit_, "Sponsor authority limit");
    }

    const string& name() const {
        return name_;
    }

    double authorityLimit() const {
        return authorityLimit_;
    }

    void sponsorProject(Project& project) {
        if (project.sponsorName() != name_) {
            throw logic_error(
                "Sponsor identity does not match the project's sponsor."
            );
        }

        if (
            find(
                activeProjects_.begin(),
                activeProjects_.end(),
                &project
            ) == activeProjects_.end()
        ) {
            activeProjects_.push_back(&project);
        }

        project.setStatus(ProjectStatus::Initiating);

        cout << "\nSponsor " << name_
             << " has accepted executive sponsorship for '"
             << project.name() << "'.\n";
    }

    bool confirmStrategicAlignment(const Project& project) const {
        string objective = project.strategicObjective();

        transform(
            objective.begin(),
            objective.end(),
            objective.begin(),
            [](unsigned char character) {
                return static_cast<char>(tolower(character));
            }
        );

        bool aligned = false;

        for (const string& priority : strategicPriorities_) {
            string normalizedPriority = priority;

            transform(
                normalizedPriority.begin(),
                normalizedPriority.end(),
                normalizedPriority.begin(),
                [](unsigned char character) {
                    return static_cast<char>(tolower(character));
                }
            );

            if (objective.find(normalizedPriority) != string::npos) {
                aligned = true;
                break;
            }
        }

        cout << "Strategic alignment: "
             << (aligned ? "Aligned" : "Requires review")
             << '\n';

        return aligned;
    }

    bool approveFunding(Project& project, double amount) const {
        requireNonNegative(amount, "Funding request");

        if (amount > authorityLimit_) {
            cout << "Funding request " << formatMoney(amount)
                 << " exceeds sponsor authority of "
                 << formatMoney(authorityLimit_) << ".\n";
            return false;
        }

        cout << "Funding approved: "
             << formatMoney(amount) << '\n';

        return true;
    }

    bool makeDecision(
        Project& project,
        const string& decisionId,
        const string& outcome
    ) const {
        for (Decision& decision : project.decisions) {
            if (decision.id == decisionId) {
                decision.makeDecision(outcome);

                cout << "Sponsor decision " << decisionId
                     << ": " << outcome << '\n';

                return true;
            }
        }

        cout << "Decision " << decisionId
             << " was not found.\n";

        return false;
    }

    void removeOrganizationalBarrier(
        const Project& project,
        const string& barrier
    ) const {
        cout << "Executive action for '"
             << project.name()
             << "': " << barrier << '\n';
    }

    bool approveMajorChange(
        Project& project,
        double cost,
        bool strategicallyAligned
    ) const {
        requireNonNegative(cost, "Change cost");

        if (!strategicallyAligned) {
            cout << "Change rejected: insufficient strategic alignment.\n";
            return false;
        }

        if (cost > authorityLimit_) {
            cout << "Change escalated: outside sponsor authority.\n";
            return false;
        }

        project.increaseForecast(cost);

        cout << "Major change approved. Forecast increased by "
             << formatMoney(cost) << ".\n";

        return true;
    }

    vector<const Risk*> reviewCriticalRisks(const Project& project) const {
        vector<const Risk*> critical;

        for (const Risk& risk : project.risks) {
            if (risk.level() == RiskLevel::Critical) {
                critical.push_back(&risk);
            }
        }

        cout << "Critical risks requiring executive attention: "
             << critical.size() << '\n';

        return critical;
    }

    double reviewBenefits(const Project& project) const {
        const double progress = project.averageBenefitProgress();

        cout << "Average benefit realization: "
             << fixed << setprecision(1)
             << progress << "%\n";

        return progress;
    }

    bool authorizeClosure(const Project& project) const {
        const bool closable =
            project.status() == ProjectStatus::Completed ||
            project.status() == ProjectStatus::Cancelled;

        if (!closable) {
            cout << "Closure cannot be authorized while the project is active.\n";
            return false;
        }

        cout << "Closure authorized for '"
             << project.name() << "'.\n";

        return true;
    }
};


// ============================================================================
// Earned Value
// ============================================================================

struct EarnedValue {
    double plannedValue;
    double earnedValue;
    double actualCost;

    EarnedValue(
        double plannedValueValue,
        double earnedValueValue,
        double actualCostValue
    )
        : plannedValue(plannedValueValue),
          earnedValue(earnedValueValue),
          actualCost(actualCostValue) {

        requireNonNegative(plannedValue, "Planned value");
        requireNonNegative(earnedValue, "Earned value");
        requireNonNegative(actualCost, "Actual cost");
    }

    double scheduleVariance() const {
        return earnedValue - plannedValue;
    }

    double costVariance() const {
        return earnedValue - actualCost;
    }

    double schedulePerformanceIndex() const {
        if (plannedValue == 0.0) {
            return numeric_limits<double>::quiet_NaN();
        }

        return earnedValue / plannedValue;
    }

    double costPerformanceIndex() const {
        if (actualCost == 0.0) {
            return numeric_limits<double>::quiet_NaN();
        }

        return earnedValue / actualCost;
    }
};


// ============================================================================
// Decision Rights
// ============================================================================

string decisionAuthority(
    const string& impact,
    double cost,
    bool strategicChange,
    double sponsorLimit
) {
    requireNonNegative(cost, "Decision cost");

    if (strategicChange) {
        if (cost > sponsorLimit) {
            return "Higher governing authority";
        }

        return "Project sponsor or governing body";
    }

    if (cost > sponsorLimit) {
        return "Higher governing authority";
    }

    if (impact == "low") {
        return "Project manager";
    }

    if (impact == "medium") {
        return "Project manager with governance review";
    }

    return "Project sponsor";
}


// ============================================================================
// Executive Report
// ============================================================================

struct ExecutiveReport {
    string projectName;
    string sponsorName;
    ProjectStatus status;
    double approvedBudget;
    double forecast;
    double budgetVariance;
    int criticalRisks;
    int overdueDecisions;
    double benefitProgress;

    void print() const {
        cout << "\nEXECUTIVE SPONSOR REPORT\n";
        cout << "Project: " << projectName << '\n';
        cout << "Sponsor: " << sponsorName << '\n';
        cout << "Status: " << toString(status) << '\n';
        cout << "Approved budget: "
             << formatMoney(approvedBudget) << '\n';
        cout << "Current forecast: "
             << formatMoney(forecast) << '\n';
        cout << "Budget variance: "
             << formatMoney(budgetVariance) << '\n';
        cout << "Critical risks: "
             << criticalRisks << '\n';
        cout << "Overdue decisions: "
             << overdueDecisions << '\n';
        cout << "Average benefit realization: "
             << fixed << setprecision(1)
             << benefitProgress << "%\n";
    }
};

ExecutiveReport buildExecutiveReport(
    const Project& project,
    const ProjectSponsor& sponsor,
    const SimpleDate& today
) {
    return {
        project.name(),
        sponsor.name(),
        project.status(),
        project.approvedBudget(),
        project.currentForecast(),
        project.budgetVariance(),
        project.criticalRiskCount(),
        project.overdueDecisionCount(today),
        project.averageBenefitProgress()
    };
}


// ============================================================================
// Main Industry Case Study
// ============================================================================

int main() {
    try {
        cout << string(78, '=') << '\n';
        cout << "PROJECT SPONSOR: INDUSTRY-STYLE GOVERNANCE CASE STUDY\n";
        cout << string(78, '=') << '\n';

        Project project(
            "PRJ-001",
            "Enterprise Customer Service Modernization",
            "Digital transformation and customer service improvement",
            "Anita Sharma",
            "Rahul Mehta",
            5'000'000.00,
            4'850'000.00,
            "Implement a unified customer service platform, migrate "
            "approved customer data, integrate selected channels, "
            "train service teams, and measure service improvements."
        );

        ProjectSponsor sponsor(
            "Anita Sharma",
            "Chief Customer Officer",
            750'000.00,
            {
                "Digital transformation",
                "Customer service improvement",
                "Operational efficiency"
            }
        );

        // --------------------------------------------------------------------
        // Stakeholder Register
        // --------------------------------------------------------------------

        project.stakeholders = {
            {
                "Chief Executive Officer",
                "Executive stakeholder",
                Influence::High,
                Influence::High,
                80
            },
            {
                "Chief Information Officer",
                "Technology executive",
                Influence::High,
                Influence::High,
                75
            },
            {
                "Customer Service Director",
                "Business owner",
                Influence::High,
                Influence::High,
                90
            },
            {
                "Service Agents",
                "End users",
                Influence::Medium,
                Influence::High,
                55
            },
            {
                "Finance Controller",
                "Control function",
                Influence::Medium,
                Influence::Medium,
                65
            }
        };

        // --------------------------------------------------------------------
        // Risk Register
        // --------------------------------------------------------------------

        project.risks = {
            {
                "R-001",
                "Legacy customer data contains inconsistent records.",
                0.70,
                8.0,
                "Data Migration Lead",
                "Data profiling, cleansing, reconciliation and validation."
            },
            {
                "R-002",
                "Business users may resist the new operating model.",
                0.60,
                9.0,
                "Change Lead",
                "Training, communication and user involvement."
            },
            {
                "R-003",
                "Critical integration may miss the release window.",
                0.40,
                10.0,
                "Technical Lead",
                "Early interface testing and contingency planning."
            },
            {
                "R-004",
                "Uncontrolled scope growth may increase total cost.",
                0.50,
                7.0,
                "Project Manager",
                "Formal change control and sponsor governance."
            }
        };

        // --------------------------------------------------------------------
        // Benefits Register
        // --------------------------------------------------------------------

        project.benefits = {
            {
                "B-001",
                "Reduce average customer response time.",
                24.0,
                12.0,
                17.0,
                "hours",
                "Customer Service Director"
            },
            {
                "B-002",
                "Increase first-contact resolution.",
                62.0,
                80.0,
                72.0,
                "%",
                "Customer Service Director"
            },
            {
                "B-003",
                "Reduce manual service processing effort.",
                100.0,
                70.0,
                82.0,
                "index",
                "Operations Director"
            }
        };

        // --------------------------------------------------------------------
        // Decision Register
        // --------------------------------------------------------------------

        project.decisions = {
            {
                "D-001",
                "Approve integration architecture exception.",
                DecisionType::Major,
                daysFromToday(-2),
                sponsor.name()
            },
            {
                "D-002",
                "Select phased versus single-release deployment.",
                DecisionType::Strategic,
                daysFromToday(3),
                sponsor.name()
            }
        };

        // --------------------------------------------------------------------
        // Sponsor Activation
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "SPONSOR ACTIVATION\n";
        cout << string(78, '=') << '\n';

        sponsor.sponsorProject(project);

        cout << "Project: " << project.name() << '\n';
        cout << "Strategic objective: "
             << project.strategicObjective() << '\n';

        sponsor.confirmStrategicAlignment(project);

        project.setStatus(ProjectStatus::Planning);

        // --------------------------------------------------------------------
        // Funding Governance
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "FUNDING GOVERNANCE\n";
        cout << string(78, '=') << '\n';

        sponsor.approveFunding(project, 5'000'000.00);

        // The following request is deliberately above the sponsor's
        // delegated authority and therefore demonstrates escalation.
        sponsor.approveFunding(project, 1'500'000.00);

        // --------------------------------------------------------------------
        // Stakeholder Review
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "STAKEHOLDER REVIEW\n";
        cout << string(78, '=') << '\n';

        for (const Stakeholder& stakeholder : project.stakeholders) {
            cout << left
                 << setw(27) << stakeholder.name
                 << setw(18) << stakeholder.engagementCategory()
                 << engagementAction(stakeholder)
                 << '\n';
        }

        // --------------------------------------------------------------------
        // Risk Review
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "RISK REVIEW\n";
        cout << string(78, '=') << '\n';

        for (const Risk& risk : project.risks) {
            cout << risk.id
                 << " | exposure="
                 << fixed << setprecision(2)
                 << risk.exposure()
                 << " | level="
                 << toString(risk.level())
                 << " | "
                 << risk.description
                 << '\n';
        }

        const vector<const Risk*> criticalRisks =
            sponsor.reviewCriticalRisks(project);

        for (const Risk* risk : criticalRisks) {
            cout << "Executive attention: "
                 << risk->id << " -> "
                 << risk->mitigation << '\n';
        }

        // --------------------------------------------------------------------
        // Decision Governance
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "DECISION GOVERNANCE\n";
        cout << string(78, '=') << '\n';

        const SimpleDate today = todayDate();

        for (const Decision& decision : project.decisions) {
            cout << decision.id
                 << " | "
                 << toString(decision.type)
                 << " | due="
                 << dateToString(decision.requiredBy)
                 << " | "
                 << (decision.decided ? "Decided" : "Pending")
                 << '\n';

            if (decision.overdue(today)) {
                sponsor.makeDecision(
                    project,
                    decision.id,
                    "Approved with controlled implementation."
                );
            }
        }

        // --------------------------------------------------------------------
        // Organizational Barrier Removal
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "EXECUTIVE BARRIER REMOVAL\n";
        cout << string(78, '=') << '\n';

        sponsor.removeOrganizationalBarrier(
            project,
            "Resolve cross-functional ownership conflict for data migration."
        );

        // --------------------------------------------------------------------
        // Benefits Governance
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "BENEFITS GOVERNANCE\n";
        cout << string(78, '=') << '\n';

        for (const Benefit& benefit : project.benefits) {
            cout << benefit.id
                 << " | "
                 << benefit.description
                 << " | progress="
                 << fixed << setprecision(1)
                 << benefit.progressPercentage()
                 << "%\n";
        }

        sponsor.reviewBenefits(project);

        // --------------------------------------------------------------------
        // Change Control
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "CHANGE CONTROL\n";
        cout << string(78, '=') << '\n';

        sponsor.approveMajorChange(
            project,
            450'000.00,
            true
        );

        cout << "Forecast: "
             << formatMoney(project.currentForecast())
             << '\n';

        cout << "Budget variance: "
             << formatMoney(project.budgetVariance())
             << " ("
             << fixed << setprecision(2)
             << project.budgetVariancePercentage()
             << "%)\n";

        // --------------------------------------------------------------------
        // Earned Value Analysis
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "EARNED VALUE ANALYSIS\n";
        cout << string(78, '=') << '\n';

        EarnedValue earnedValue(
            3'000'000.00,
            2'700'000.00,
            2'900'000.00
        );

        cout << "PV:  "
             << formatMoney(earnedValue.plannedValue)
             << '\n';

        cout << "EV:  "
             << formatMoney(earnedValue.earnedValue)
             << '\n';

        cout << "AC:  "
             << formatMoney(earnedValue.actualCost)
             << '\n';

        cout << "SV:  "
             << formatMoney(earnedValue.scheduleVariance())
             << '\n';

        cout << "CV:  "
             << formatMoney(earnedValue.costVariance())
             << '\n';

        cout << "SPI: "
             << fixed << setprecision(3)
             << earnedValue.schedulePerformanceIndex()
             << '\n';

        cout << "CPI: "
             << fixed << setprecision(3)
             << earnedValue.costPerformanceIndex()
             << '\n';

        if (earnedValue.schedulePerformanceIndex() < 1.0) {
            cout << "Schedule interpretation: "
                 << "earned progress is below planned progress.\n";
        }

        if (earnedValue.costPerformanceIndex() < 1.0) {
            cout << "Cost interpretation: "
                 << "earned value is below actual cost.\n";
        }

        // --------------------------------------------------------------------
        // Decision Rights Matrix
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "DECISION RIGHTS MATRIX\n";
        cout << string(78, '=') << '\n';

        struct DecisionScenario {
            string impact;
            double cost;
            bool strategicChange;
        };

        const vector<DecisionScenario> scenarios = {
            {"low", 20'000.00, false},
            {"medium", 100'000.00, false},
            {"high", 400'000.00, true},
            {"high", 1'200'000.00, false}
        };

        for (const auto& scenario : scenarios) {
            cout << "impact=" << scenario.impact
                 << " | cost="
                 << formatMoney(scenario.cost)
                 << " | strategic="
                 << boolalpha
                 << scenario.strategicChange
                 << " | authority="
                 << decisionAuthority(
                        scenario.impact,
                        scenario.cost,
                        scenario.strategicChange,
                        sponsor.authorityLimit()
                    )
                 << '\n';
        }

        // --------------------------------------------------------------------
        // Executive Reporting
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "EXECUTIVE REPORTING\n";
        cout << string(78, '=') << '\n';

        ExecutiveReport report =
            buildExecutiveReport(project, sponsor, today);

        report.print();

        // --------------------------------------------------------------------
        // Closure Governance
        // --------------------------------------------------------------------

        cout << "\n" << string(78, '=') << '\n';
        cout << "CLOSURE CONTROL\n";
        cout << string(78, '=') << '\n';

        // Demonstrates that a sponsor should not authorize closure while
        // the project is still active.
        sponsor.authorizeClosure(project);

        project.setStatus(ProjectStatus::Completed);

        // Once acceptance and transition conditions have been satisfied,
        // the sponsor can authorize formal closure.
        sponsor.authorizeClosure(project);

        cout << "\n" << string(78, '=') << '\n';
        cout << "CASE STUDY COMPLETED\n";
        cout << string(78, '=') << '\n';

        return 0;
    }
    catch (const exception& error) {
        cerr << "Execution error: "
             << error.what()
             << '\n';

        return 1;
    }
}
