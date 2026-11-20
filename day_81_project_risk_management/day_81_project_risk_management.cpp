#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * PROJECT RISK MANAGEMENT
 *
 * C++17 repository-independent project risk governance engine.
 *
 * Implements:
 * - Risk identification
 * - Risk classification
 * - Probability and impact scoring
 * - Risk prioritization
 * - Response planning
 * - Residual risk assessment
 * - Risk ownership
 * - Escalation
 * - Closure
 * - Project risk portfolio reporting
 * - Merge-independent risk policy evaluation
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic project_risk.cpp -o project_risk
 *
 * Execute:
 * ./project_risk
 */

namespace risk_management {

enum class Category {
    Technical,
    Financial,
    Operational,
    Schedule,
    Resource,
    Security,
    Legal,
    Quality,
    Scope,
    External
};

enum class Status {
    Identified,
    Assessed,
    ResponsePlanned,
    Monitoring,
    Escalated,
    Closed
};

enum class Strategy {
    Avoid,
    Mitigate,
    Transfer,
    Accept,
    Exploit,
    Enhance,
    Share
};

enum class Level {
    Low,
    Medium,
    High,
    Critical
};

std::string toString(Category value) {
    switch (value) {
        case Category::Technical: return "Technical";
        case Category::Financial: return "Financial";
        case Category::Operational: return "Operational";
        case Category::Schedule: return "Schedule";
        case Category::Resource: return "Resource";
        case Category::Security: return "Security";
        case Category::Legal: return "Legal";
        case Category::Quality: return "Quality";
        case Category::Scope: return "Scope";
        case Category::External: return "External";
    }

    throw std::logic_error("Unknown category.");
}

std::string toString(Status value) {
    switch (value) {
        case Status::Identified: return "Identified";
        case Status::Assessed: return "Assessed";
        case Status::ResponsePlanned: return "Response Planned";
        case Status::Monitoring: return "Monitoring";
        case Status::Escalated: return "Escalated";
        case Status::Closed: return "Closed";
    }

    throw std::logic_error("Unknown status.");
}

std::string toString(Strategy value) {
    switch (value) {
        case Strategy::Avoid: return "Avoid";
        case Strategy::Mitigate: return "Mitigate";
        case Strategy::Transfer: return "Transfer";
        case Strategy::Accept: return "Accept";
        case Strategy::Exploit: return "Exploit";
        case Strategy::Enhance: return "Enhance";
        case Strategy::Share: return "Share";
    }

    throw std::logic_error("Unknown strategy.");
}

std::string toString(Level value) {
    switch (value) {
        case Level::Low: return "Low";
        case Level::Medium: return "Medium";
        case Level::High: return "High";
        case Level::Critical: return "Critical";
    }

    throw std::logic_error("Unknown level.");
}

void validateText(const std::string& value, const std::string& field) {
    if (value.empty() ||
        value.find_first_not_of(" \t\n\r") == std::string::npos) {
        throw std::invalid_argument(field + " cannot be empty.");
    }
}

void validateScore(int score, const std::string& field) {
    if (score < 1 || score > 5) {
        throw std::invalid_argument(
            field + " must be between 1 and 5."
        );
    }
}

Level classify(int score) {
    if (score >= 20) return Level::Critical;
    if (score >= 12) return Level::High;
    if (score >= 6) return Level::Medium;
    return Level::Low;
}

struct RiskHistory {
    std::string event;
    std::string details;
};

struct ResponsePlan {
    Strategy strategy;
    std::string action;
    double responseCost = 0.0;
    double contingencyReserve = 0.0;
};

struct ResidualAssessment {
    int probability;
    int impact;

    int score() const {
        return probability * impact;
    }
};

class Risk {
private:
    std::string id_;
    std::string title_;
    std::string description_;
    Category category_;
    int probability_;
    int impact_;
    std::string owner_;

    Status status_ = Status::Identified;

    std::optional<ResponsePlan> response_;
    std::optional<ResidualAssessment> residual_;

    std::vector<RiskHistory> history_;
    std::set<std::string> tags_;

    void requireOpen() const {
        if (status_ == Status::Closed) {
            throw std::logic_error(
                "Closed risks cannot be modified."
            );
        }
    }

    void record(
        const std::string& event,
        const std::string& details
    ) {
        history_.push_back({event, details});
    }

public:
    Risk(
        std::string id,
        std::string title,
        std::string description,
        Category category,
        int probability,
        int impact,
        std::string owner
    )
        : id_(std::move(id)),
          title_(std::move(title)),
          description_(std::move(description)),
          category_(category),
          probability_(probability),
          impact_(impact),
          owner_(std::move(owner)) {

        validateText(id_, "Risk ID");
        validateText(title_, "Risk title");
        validateText(description_, "Risk description");
        validateText(owner_, "Risk owner");

        validateScore(probability_, "Probability");
        validateScore(impact_, "Impact");

        record("IDENTIFIED", "Risk added to the register.");
    }

    const std::string& id() const {
        return id_;
    }

    const std::string& title() const {
        return title_;
    }

    const std::string& owner() const {
        return owner_;
    }

    Category category() const {
        return category_;
    }

    Status status() const {
        return status_;
    }

    int probability() const {
        return probability_;
    }

    int impact() const {
        return impact_;
    }

    int inherentScore() const {
        return probability_ * impact_;
    }

    int currentScore() const {
        return residual_
            ? residual_->score()
            : inherentScore();
    }

    Level inherentLevel() const {
        return classify(inherentScore());
    }

    Level currentLevel() const {
        return classify(currentScore());
    }

    const std::vector<RiskHistory>& history() const {
        return history_;
    }

    const std::optional<ResponsePlan>& response() const {
        return response_;
    }

    void assess() {
        requireOpen();

        status_ = Status::Assessed;

        record(
            "ASSESSED",
            "Inherent exposure: " +
            std::to_string(inherentScore())
        );
    }

    void planResponse(ResponsePlan plan) {
        requireOpen();

        validateText(plan.action, "Response action");

        if (plan.responseCost < 0 ||
            plan.contingencyReserve < 0) {
            throw std::invalid_argument(
                "Response costs cannot be negative."
            );
        }

        response_ = std::move(plan);
        status_ = Status::ResponsePlanned;

        record(
            "RESPONSE PLANNED",
            toString(response_->strategy) +
            ": " + response_->action
        );
    }

    void monitor(int probability, int impact) {
        requireOpen();

        validateScore(probability, "Residual probability");
        validateScore(impact, "Residual impact");

        residual_ = ResidualAssessment{
            probability,
            impact
        };

        status_ = Status::Monitoring;

        record(
            "MONITORED",
            "Residual exposure: " +
            std::to_string(currentScore())
        );
    }

    void escalate(const std::string& reason) {
        requireOpen();
        validateText(reason, "Escalation reason");

        status_ = Status::Escalated;

        record("ESCALATED", reason);
    }

    void close(const std::string& resolution) {
        requireOpen();
        validateText(resolution, "Closure resolution");

        status_ = Status::Closed;

        record("CLOSED", resolution);
    }

    void addTag(const std::string& tag) {
        requireOpen();
        validateText(tag, "Tag");
        tags_.insert(tag);
    }
};

class Project {
private:
    std::string id_;
    std::string name_;

    std::map<std::string, Risk> risks_;

public:
    Project(std::string id, std::string name)
        : id_(std::move(id)),
          name_(std::move(name)) {

        validateText(id_, "Project ID");
        validateText(name_, "Project name");
    }

    void addRisk(Risk risk) {
        const std::string riskId = risk.id();

        if (risks_.find(riskId) != risks_.end()) {
            throw std::invalid_argument(
                "Duplicate risk ID: " + riskId
            );
        }

        risks_.emplace(riskId, std::move(risk));
    }

    Risk& getRisk(const std::string& id) {
        auto it = risks_.find(id);

        if (it == risks_.end()) {
            throw std::out_of_range("Risk not found: " + id);
        }

        return it->second;
    }

    const std::map<std::string, Risk>& risks() const {
        return risks_;
    }

    std::vector<const Risk*> prioritizedRisks() const {
        std::vector<const Risk*> result;

        for (const auto& entry : risks_) {
            result.push_back(&entry.second);
        }

        std::sort(
            result.begin(),
            result.end(),
            [](const Risk* a, const Risk* b) {
                if (a->currentScore() != b->currentScore()) {
                    return a->currentScore() > b->currentScore();
                }

                return a->id() < b->id();
            }
        );

        return result;
    }
};

struct GovernancePolicy {
    int highRiskThreshold = 12;
    int criticalRiskThreshold = 20;
    bool requireResponseForHighRisk = true;
    bool requireOwner = true;
};

struct PolicyResult {
    bool eligible;
    std::vector<std::string> violations;
};

class RiskGovernance {
private:
    GovernancePolicy policy_;

public:
    explicit RiskGovernance(GovernancePolicy policy)
        : policy_(policy) {

        if (
            policy_.highRiskThreshold < 1 ||
            policy_.criticalRiskThreshold > 25 ||
            policy_.highRiskThreshold >=
                policy_.criticalRiskThreshold
        ) {
            throw std::invalid_argument(
                "Invalid governance thresholds."
            );
        }
    }

    PolicyResult evaluate(const Risk& risk) const {
        PolicyResult result{true, {}};

        if (
            policy_.requireResponseForHighRisk &&
            risk.currentScore() >= policy_.highRiskThreshold &&
            !risk.response().has_value()
        ) {
            result.violations.push_back(
                "High-risk exposure requires a response plan."
            );
        }

        if (
            policy_.requireOwner &&
            risk.owner().empty()
        ) {
            result.violations.push_back(
                "Risk owner is required."
            );
        }

        result.eligible = result.violations.empty();

        return result;
    }
};

struct PortfolioSummary {
    std::size_t total = 0;
    std::size_t active = 0;
    std::size_t closed = 0;

    int inherentExposure = 0;
    int currentExposure = 0;

    std::map<Level, int> levelCounts;
    std::map<Category, int> categoryExposure;
};

PortfolioSummary summarize(const Project& project) {
    PortfolioSummary summary;

    summary.total = project.risks().size();

    for (const auto& entry : project.risks()) {
        const Risk& risk = entry.second;

        if (risk.status() == Status::Closed) {
            ++summary.closed;
            continue;
        }

        ++summary.active;

        summary.inherentExposure += risk.inherentScore();
        summary.currentExposure += risk.currentScore();

        ++summary.levelCounts[risk.currentLevel()];

        summary.categoryExposure[risk.category()] +=
            risk.currentScore();
    }

    return summary;
}

void displayReport(const Project& project) {
    std::cout << "\nPROJECT RISK REGISTER\n";
    std::cout << "Project: Enterprise Management Platform\n";
    std::cout << std::string(115, '-') << '\n';

    std::cout
        << std::left
        << std::setw(10) << "Risk ID"
        << std::setw(32) << "Risk"
        << std::setw(22) << "Category"
        << std::setw(8) << "Score"
        << std::setw(12) << "Level"
        << std::setw(22) << "Status"
        << "Owner\n";

    std::cout << std::string(115, '-') << '\n';

    for (const Risk* risk : project.prioritizedRisks()) {
        std::cout
            << std::left
            << std::setw(10) << risk->id()
            << std::setw(32) << risk->title().substr(0, 30)
            << std::setw(22) << toString(risk->category())
            << std::setw(8) << risk->currentScore()
            << std::setw(12) << toString(risk->currentLevel())
            << std::setw(22) << toString(risk->status())
            << risk->owner()
            << '\n';
    }

    std::cout << std::string(115, '-') << '\n';
}

void displaySummary(const Project& project) {
    const PortfolioSummary summary = summarize(project);

    std::cout << "\nPORTFOLIO SUMMARY\n";

    std::cout << "Total risks: "
              << summary.total << '\n';

    std::cout << "Active risks: "
              << summary.active << '\n';

    std::cout << "Closed risks: "
              << summary.closed << '\n';

    std::cout << "Inherent exposure: "
              << summary.inherentExposure << '\n';

    std::cout << "Current exposure: "
              << summary.currentExposure << '\n';

    std::cout << "\nRISK LEVEL DISTRIBUTION\n";

    for (const auto& entry : summary.levelCounts) {
        std::cout
            << toString(entry.first)
            << ": "
            << entry.second
            << '\n';
    }

    std::cout << "\nCATEGORY EXPOSURE\n";

    for (const auto& entry : summary.categoryExposure) {
        std::cout
            << toString(entry.first)
            << ": "
            << entry.second
            << '\n';
    }
}

void runTests() {
    Risk risk(
        "TEST01",
        "Validation test",
        "A test risk.",
        Category::Technical,
        3,
        4,
        "Test Owner"
    );

    if (risk.inherentScore() != 12) {
        throw std::runtime_error("Inherent score test failed.");
    }

    risk.planResponse({
        Strategy::Mitigate,
        "Introduce automated tests.",
        1000,
        500
    });

    risk.monitor(1, 2);

    if (risk.currentScore() != 2) {
        throw std::runtime_error("Residual score test failed.");
    }

    risk.close("Resolved.");

    bool rejected = false;

    try {
        risk.escalate("Invalid escalation.");
    } catch (const std::logic_error&) {
        rejected = true;
    }

    if (!rejected) {
        throw std::runtime_error(
            "Closed risk modification was permitted."
        );
    }

    bool invalidScoreRejected = false;

    try {
        validateScore(6, "Probability");
    } catch (const std::invalid_argument&) {
        invalidScoreRejected = true;
    }

    if (!invalidScoreRejected) {
        throw std::runtime_error("Score validation failed.");
    }

    std::cout << "\nAll C++17 tests passed.\n";
}

Project createProject() {
    Project project(
        "PRJ-2026-001",
        "Enterprise Management Platform"
    );

    project.addRisk(Risk(
        "R001",
        "Cloud provisioning delay",
        "Infrastructure delivery may exceed schedule.",
        Category::Schedule,
        4,
        5,
        "Infrastructure Lead"
    ));

    project.addRisk(Risk(
        "R002",
        "Budget overrun",
        "Unexpected licensing expenditure.",
        Category::Financial,
        3,
        5,
        "Project Manager"
    ));

    project.addRisk(Risk(
        "R003",
        "Unauthorized access",
        "Confidential project data may be exposed.",
        Category::Security,
        2,
        5,
        "Security Lead"
    ));

    project.addRisk(Risk(
        "R004",
        "Key developer unavailability",
        "A critical developer may become unavailable.",
        Category::Resource,
        3,
        4,
        "Engineering Manager"
    ));

    project.addRisk(Risk(
        "R005",
        "Scope expansion",
        "Uncontrolled requirements may affect delivery.",
        Category::Scope,
        4,
        4,
        "Product Owner"
    ));

    for (const std::string id : {
        "R001", "R002", "R003", "R004", "R005"
    }) {
        project.getRisk(id).assess();
    }

    project.getRisk("R001").planResponse({
        Strategy::Mitigate,
        "Maintain an alternative cloud provider.",
        10000,
        5000
    });

    project.getRisk("R002").planResponse({
        Strategy::Mitigate,
        "Introduce monthly budget reviews.",
        2500,
        8000
    });

    project.getRisk("R003").planResponse({
        Strategy::Avoid,
        "Enforce access restrictions and MFA.",
        4000,
        1000
    });

    project.getRisk("R004").planResponse({
        Strategy::Mitigate,
        "Cross-train engineering personnel.",
        3000,
        1000
    });

    project.getRisk("R005").planResponse({
        Strategy::Avoid,
        "Enforce formal scope approval.",
        1500,
        1000
    });

    project.getRisk("R001").monitor(2, 4);
    project.getRisk("R002").monitor(2, 4);
    project.getRisk("R003").monitor(1, 4);
    project.getRisk("R004").monitor(2, 3);
    project.getRisk("R005").monitor(2, 3);

    return project;
}

} // namespace risk_management

int main() {
    try {
        using namespace risk_management;

        Project project = createProject();

        displayReport(project);
        displaySummary(project);

        GovernancePolicy policy;
        RiskGovernance governance(policy);

        std::cout << "\nGOVERNANCE POLICY EVALUATION\n";

        for (const auto& entry : project.risks()) {
            const Risk& risk = entry.second;
            const PolicyResult result = governance.evaluate(risk);

            std::cout
                << risk.id()
                << ": "
                << (result.eligible ? "PASS" : "FAIL")
                << '\n';

            for (const auto& violation : result.violations) {
                std::cout << "  " << violation << '\n';
            }
        }

        runTests();

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Application error: "
                  << error.what() << '\n';

        return 1;
    }
}
