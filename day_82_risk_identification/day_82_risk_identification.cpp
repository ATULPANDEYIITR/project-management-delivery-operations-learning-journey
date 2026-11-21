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
 * Risk Identification and Repository-Independent Governance Engine
 *
 * C++17
 *
 * Models:
 * - Risk identification and classification
 * - Inherent and residual risk
 * - Evidence records
 * - Preventive and detective controls
 * - Ownership
 * - Risk register
 * - Risk prioritization
 * - Risk acceptance and mitigation
 * - Validation and state transitions
 */

enum class Category {
    Strategic,
    Operational,
    Financial,
    Technological,
    Cybersecurity,
    Compliance,
    Reputational,
    Environmental,
    HumanResource,
    ThirdParty
};

enum class Source {
    Workshop,
    Audit,
    Incident,
    Interview,
    HistoricalData,
    TechnicalAnalysis,
    ExternalEnvironment
};

enum class Status {
    Identified,
    Assessed,
    UnderReview,
    Mitigated,
    Accepted,
    Closed
};

enum class Level {
    Low,
    Moderate,
    High,
    Critical
};

enum class ControlType {
    Preventive,
    Detective,
    Corrective
};

std::string toString(Category category) {
    static const std::map<Category, std::string> names = {
        {Category::Strategic, "Strategic"},
        {Category::Operational, "Operational"},
        {Category::Financial, "Financial"},
        {Category::Technological, "Technological"},
        {Category::Cybersecurity, "Cybersecurity"},
        {Category::Compliance, "Compliance"},
        {Category::Reputational, "Reputational"},
        {Category::Environmental, "Environmental"},
        {Category::HumanResource, "Human Resource"},
        {Category::ThirdParty, "Third Party"}
    };

    return names.at(category);
}

std::string toString(Status status) {
    static const std::map<Status, std::string> names = {
        {Status::Identified, "Identified"},
        {Status::Assessed, "Assessed"},
        {Status::UnderReview, "Under Review"},
        {Status::Mitigated, "Mitigated"},
        {Status::Accepted, "Accepted"},
        {Status::Closed, "Closed"}
    };

    return names.at(status);
}

std::string toString(Level level) {
    static const std::map<Level, std::string> names = {
        {Level::Low, "Low"},
        {Level::Moderate, "Moderate"},
        {Level::High, "High"},
        {Level::Critical, "Critical"}
    };

    return names.at(level);
}

void validateScale(int value, const std::string& field) {
    if (value < 1 || value > 5) {
        throw std::invalid_argument(
            field + " must be between 1 and 5."
        );
    }
}

void validateText(
    const std::string& value,
    const std::string& field
) {
    if (value.find_first_not_of(" \t\n\r") == std::string::npos) {
        throw std::invalid_argument(field + " cannot be empty.");
    }
}

Level classify(double score) {
    if (score >= 75.0) return Level::Critical;
    if (score >= 40.0) return Level::High;
    if (score >= 15.0) return Level::Moderate;
    return Level::Low;
}

struct Evidence {
    std::string reference;
    std::string description;
    Source source;
};

struct Control {
    std::string id;
    std::string description;
    ControlType type;
    double effectiveness;
};

class Risk {
private:
    std::string id_;
    std::string title_;
    std::string description_;
    std::string owner_;
    std::string context_;

    Category category_;
    Status status_ = Status::Identified;

    int probability_;
    int impact_;
    int detectability_;

    std::vector<Evidence> evidence_;
    std::vector<Control> controls_;

    double calculateEffectiveness() const {
        double remaining = 1.0;

        for (const auto& control : controls_) {
            remaining *= 1.0 - control.effectiveness;
        }

        return 1.0 - remaining;
    }

public:
    Risk(
        std::string id,
        std::string title,
        std::string description,
        std::string owner,
        std::string context,
        Category category,
        int probability,
        int impact,
        int detectability
    )
        : id_(std::move(id)),
          title_(std::move(title)),
          description_(std::move(description)),
          owner_(std::move(owner)),
          context_(std::move(context)),
          category_(category),
          probability_(probability),
          impact_(impact),
          detectability_(detectability) {

        validateText(id_, "Risk ID");
        validateText(title_, "Title");
        validateText(description_, "Description");
        validateText(owner_, "Owner");
        validateText(context_, "Context");

        validateScale(probability_, "Probability");
        validateScale(impact_, "Impact");
        validateScale(detectability_, "Detectability");
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

    const std::string& context() const {
        return context_;
    }

    Category category() const {
        return category_;
    }

    Status status() const {
        return status_;
    }

    int inherentScore() const {
        return probability_ * impact_ * detectability_;
    }

    Level inherentLevel() const {
        return classify(inherentScore());
    }

    double controlEffectiveness() const {
        return calculateEffectiveness();
    }

    double residualScore() const {
        return inherentScore() * (1.0 - calculateEffectiveness());
    }

    Level residualLevel() const {
        return classify(residualScore());
    }

    const std::vector<Evidence>& evidence() const {
        return evidence_;
    }

    const std::vector<Control>& controls() const {
        return controls_;
    }

    void addEvidence(Evidence evidence) {
        validateText(evidence.reference, "Evidence reference");
        validateText(evidence.description, "Evidence description");

        const auto duplicate = std::find_if(
            evidence_.begin(),
            evidence_.end(),
            [&](const Evidence& existing) {
                return existing.reference == evidence.reference;
            }
        );

        if (duplicate != evidence_.end()) {
            throw std::invalid_argument(
                "Duplicate evidence reference."
            );
        }

        evidence_.push_back(std::move(evidence));
    }

    void addControl(Control control) {
        validateText(control.id, "Control ID");
        validateText(control.description, "Control description");

        if (
            !std::isfinite(control.effectiveness) ||
            control.effectiveness < 0.0 ||
            control.effectiveness > 1.0
        ) {
            throw std::invalid_argument(
                "Control effectiveness must be between 0 and 1."
            );
        }

        const auto duplicate = std::find_if(
            controls_.begin(),
            controls_.end(),
            [&](const Control& existing) {
                return existing.id == control.id;
            }
        );

        if (duplicate != controls_.end()) {
            throw std::invalid_argument("Duplicate control ID.");
        }

        controls_.push_back(std::move(control));
    }

    void reassess(
        int probability,
        int impact,
        int detectability
    ) {
        validateScale(probability, "Probability");
        validateScale(impact, "Impact");
        validateScale(detectability, "Detectability");

        probability_ = probability;
        impact_ = impact;
        detectability_ = detectability;
        status_ = Status::Assessed;
    }

    void transition(Status next) {
        static const std::map<Status, std::set<Status>> allowed = {
            {Status::Identified, {
                Status::Assessed,
                Status::UnderReview,
                Status::Closed
            }},
            {Status::Assessed, {
                Status::UnderReview,
                Status::Mitigated,
                Status::Accepted,
                Status::Closed
            }},
            {Status::UnderReview, {
                Status::Assessed,
                Status::Mitigated,
                Status::Accepted,
                Status::Closed
            }},
            {Status::Mitigated, {
                Status::UnderReview,
                Status::Closed
            }},
            {Status::Accepted, {
                Status::UnderReview,
                Status::Closed
            }},
            {Status::Closed, {}}
        };

        if (allowed.at(status_).count(next) == 0) {
            throw std::logic_error("Invalid risk state transition.");
        }

        if (next == Status::Mitigated && controls_.empty()) {
            throw std::logic_error(
                "Mitigation requires at least one recorded control."
            );
        }

        status_ = next;
    }
};

class RiskRegister {
private:
    std::string organization_;
    std::map<std::string, Risk> risks_;

public:
    explicit RiskRegister(std::string organization)
        : organization_(std::move(organization)) {
        validateText(organization_, "Organization");
    }

    void add(Risk risk) {
        if (risks_.find(risk.id()) != risks_.end()) {
            throw std::invalid_argument("Duplicate risk identifier.");
        }

        for (const auto& entry : risks_) {
            const Risk& existing = entry.second;

            if (
                existing.title() == risk.title() &&
                existing.context() == risk.context()
            ) {
                throw std::invalid_argument(
                    "Potential duplicate risk in the same context."
                );
            }
        }

        risks_.emplace(risk.id(), std::move(risk));
    }

    Risk& get(const std::string& id) {
        auto iterator = risks_.find(id);

        if (iterator == risks_.end()) {
            throw std::out_of_range("Risk not found: " + id);
        }

        return iterator->second;
    }

    std::vector<const Risk*> priorities(
        int minimumScore = 0,
        std::optional<Category> category = std::nullopt
    ) const {
        std::vector<const Risk*> result;

        for (const auto& entry : risks_) {
            const Risk& risk = entry.second;

            if (risk.inherentScore() < minimumScore) {
                continue;
            }

            if (category && risk.category() != *category) {
                continue;
            }

            result.push_back(&risk);
        }

        std::sort(
            result.begin(),
            result.end(),
            [](const Risk* first, const Risk* second) {
                if (first->inherentScore() != second->inherentScore()) {
                    return first->inherentScore() >
                           second->inherentScore();
                }

                return first->id() < second->id();
            }
        );

        return result;
    }

    std::map<Category, int> distribution() const {
        std::map<Category, int> result;

        for (const auto& entry : risks_) {
            result[entry.second.category()]++;
        }

        return result;
    }

    std::size_t size() const {
        return risks_.size();
    }

    const std::string& organization() const {
        return organization_;
    }
};

void printReport(const RiskRegister& registerData) {
    std::cout << "\nRISK IDENTIFICATION REPORT\n";
    std::cout << "Organization: "
              << registerData.organization() << "\n";
    std::cout << "Total risks: " << registerData.size() << "\n";

    std::cout << "\nPRIORITY REGISTER\n";

    std::cout << std::left
              << std::setw(15) << "Risk ID"
              << std::setw(37) << "Risk"
              << std::setw(14) << "Category"
              << std::setw(10) << "Score"
              << std::setw(12) << "Level"
              << std::setw(12) << "Residual"
              << "\n";

    std::cout << std::string(100, '-') << "\n";

    for (const Risk* risk : registerData.priorities()) {
        std::cout
            << std::left
            << std::setw(15) << risk->id()
            << std::setw(37) << risk->title()
            << std::setw(14) << toString(risk->category())
            << std::setw(10) << risk->inherentScore()
            << std::setw(12) << toString(risk->inherentLevel())
            << std::setw(12) << std::fixed
            << std::setprecision(2)
            << risk->residualScore()
            << "\n";
    }

    std::cout << "\nCATEGORY DISTRIBUTION\n";

    for (const auto& item : registerData.distribution()) {
        std::cout << toString(item.first)
                  << ": " << item.second << "\n";
    }
}

void runTests() {
    if (classify(10) != Level::Low) {
        throw std::runtime_error("Low classification test failed.");
    }

    if (classify(50) != Level::High) {
        throw std::runtime_error("High classification test failed.");
    }

    if (classify(80) != Level::Critical) {
        throw std::runtime_error("Critical classification test failed.");
    }

    Risk risk(
        "TEST-001",
        "Test risk",
        "Validation scenario",
        "Test Owner",
        "Test environment",
        Category::Operational,
        2, 3, 4
    );

    if (risk.inherentScore() != 24) {
        throw std::runtime_error("Exposure calculation failed.");
    }

    risk.addControl({
        "CTRL-1",
        "Test control",
        ControlType::Preventive,
        0.5
    });

    if (std::abs(risk.residualScore() - 12.0) > 0.0001) {
        throw std::runtime_error("Residual calculation failed.");
    }

    bool rejected = false;

    try {
        risk.reassess(6, 3, 2);
    } catch (const std::invalid_argument&) {
        rejected = true;
    }

    if (!rejected) {
        throw std::runtime_error("Invalid scale was accepted.");
    }
}

int main() {
    try {
        runTests();

        RiskRegister registerData(
            "Enterprise Digital Operations"
        );

        Risk cyber(
            "RISK-001",
            "Unauthorized production access",
            "Compromised credentials may expose production systems.",
            "Security Operations Manager",
            "Production infrastructure",
            Category::Cybersecurity,
            4, 5, 4
        );

        cyber.addEvidence({
            "AUDIT-014",
            "Privileged accounts lack consistent MFA enforcement.",
            Source::Audit
        });

        cyber.addControl({
            "CTRL-MFA",
            "Enforce phishing-resistant MFA.",
            ControlType::Preventive,
            0.55
        });

        cyber.addControl({
            "CTRL-MON",
            "Monitor privileged account activity.",
            ControlType::Detective,
            0.30
        });

        cyber.transition(Status::Assessed);
        cyber.transition(Status::UnderReview);

        registerData.add(std::move(cyber));

        Risk supplier(
            "RISK-002",
            "Critical supplier interruption",
            "A supplier outage may interrupt essential services.",
            "Vendor Management Lead",
            "Cloud service dependencies",
            Category::ThirdParty,
            3, 4, 3
        );

        supplier.addEvidence({
            "INC-022",
            "Historical outages exceeded recovery targets.",
            Source::Incident
        });

        supplier.reassess(4, 4, 3);

        registerData.add(std::move(supplier));

        Risk compliance(
            "RISK-003",
            "Regulatory reporting failure",
            "Incomplete records may delay regulatory submissions.",
            "Compliance Officer",
            "Regulatory reporting",
            Category::Compliance,
            2, 5, 3
        );

        registerData.add(std::move(compliance));

        printReport(registerData);

        std::cout << "\nHIGH-PRIORITY RISKS\n";

        for (const Risk* risk : registerData.priorities(40)) {
            std::cout << risk->id()
                      << " - " << risk->title() << "\n";
        }

        std::cout << "\nAll validation tests passed.\n";

    } catch (const std::exception& exception) {
        std::cerr << "Risk engine error: "
                  << exception.what() << "\n";

        return 1;
    }

    return 0;
}
