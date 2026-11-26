#include <algorithm>
#include <chrono>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

// ------------------------------------------------------------
// Enumerations
// ------------------------------------------------------------

enum class RiskCategory {
    Schedule,
    Cost,
    Technical,
    Resource,
    Security,
    Operational,
    Legal,
    External
};

enum class RiskStatus {
    Identified,
    Assessed,
    MitigationPlanned,
    Monitoring,
    Escalated,
    Materialized,
    Closed
};

enum class RiskResponse {
    Avoid,
    Mitigate,
    Transfer,
    Accept
};

enum class RiskLevel {
    Low,
    Medium,
    High,
    Critical
};

// ------------------------------------------------------------
// String conversion
// ------------------------------------------------------------

string toString(RiskCategory category) {
    switch (category) {
        case RiskCategory::Schedule: return "Schedule";
        case RiskCategory::Cost: return "Cost";
        case RiskCategory::Technical: return "Technical";
        case RiskCategory::Resource: return "Resource";
        case RiskCategory::Security: return "Security";
        case RiskCategory::Operational: return "Operational";
        case RiskCategory::Legal: return "Legal";
        case RiskCategory::External: return "External";
    }
    throw invalid_argument("Unknown risk category");
}

string toString(RiskStatus status) {
    switch (status) {
        case RiskStatus::Identified: return "Identified";
        case RiskStatus::Assessed: return "Assessed";
        case RiskStatus::MitigationPlanned:
            return "Mitigation Planned";
        case RiskStatus::Monitoring: return "Monitoring";
        case RiskStatus::Escalated: return "Escalated";
        case RiskStatus::Materialized: return "Materialized";
        case RiskStatus::Closed: return "Closed";
    }
    throw invalid_argument("Unknown risk status");
}

string toString(RiskLevel level) {
    switch (level) {
        case RiskLevel::Low: return "Low";
        case RiskLevel::Medium: return "Medium";
        case RiskLevel::High: return "High";
        case RiskLevel::Critical: return "Critical";
    }
    throw invalid_argument("Unknown risk level");
}

// ------------------------------------------------------------
// Domain structures
// ------------------------------------------------------------

struct Assessment {
    int probability;
    int impact;
    int exposure;
    RiskLevel level;
};

struct Observation {
    int probability;
    int impact;
    string notes;
    string recordedBy;
    string timestamp;
};

struct Risk {
    string id;
    string projectId;
    string title;
    string description;
    string owner;

    RiskCategory category;
    RiskResponse response;
    RiskStatus status;

    int probability;
    int impact;
    int version;
    int reviewCount;

    string dueDate;
    string mitigationPlan;
    string contingencyPlan;

    optional<string> lastReviewed;

    vector<Observation> observations;
    vector<string> history;
};

struct RiskReport {
    int totalRisks = 0;
    int activeRisks = 0;
    int overdueRisks = 0;
    int totalExposure = 0;

    map<string, int> levels;
    map<string, int> statuses;
    map<string, int> categories;
};

// ------------------------------------------------------------
// Date utilities
// ------------------------------------------------------------

bool validDate(const string& input) {
    if (input.size() != 10 ||
        input[4] != '-' ||
        input[7] != '-') {
        return false;
    }

    tm date = {};

    istringstream stream(input);
    stream >> get_time(&date, "%Y-%m-%d");

    if (stream.fail()) {
        return false;
    }

    date.tm_isdst = -1;

    time_t value = mktime(&date);

    if (value == -1) {
        return false;
    }

    tm normalized = *localtime(&value);

    ostringstream output;
    output << put_time(&normalized, "%Y-%m-%d");

    return output.str() == input;
}

string currentDate() {
    auto now = chrono::system_clock::now();
    time_t value = chrono::system_clock::to_time_t(now);

    tm local = *localtime(&value);

    ostringstream output;
    output << put_time(&local, "%Y-%m-%d");

    return output.str();
}

// ------------------------------------------------------------
// Risk assessment engine
// ------------------------------------------------------------

class RiskAssessmentEngine {
private:
    int lowMaximum;
    int mediumMaximum;
    int highMaximum;

public:
    RiskAssessmentEngine(
        int low = 4,
        int medium = 9,
        int high = 16
    ) : lowMaximum(low),
        mediumMaximum(medium),
        highMaximum(high) {

        if (
            low < 1 ||
            low >= medium ||
            medium >= high ||
            high >= 25
        ) {
            throw invalid_argument(
                "Invalid risk assessment thresholds"
            );
        }
    }

    Assessment evaluate(int probability, int impact) const {
        if (
            probability < 1 || probability > 5 ||
            impact < 1 || impact > 5
        ) {
            throw invalid_argument(
                "Probability and impact must be between 1 and 5"
            );
        }

        int exposure = probability * impact;

        RiskLevel level;

        if (exposure <= lowMaximum) {
            level = RiskLevel::Low;
        } else if (exposure <= mediumMaximum) {
            level = RiskLevel::Medium;
        } else if (exposure <= highMaximum) {
            level = RiskLevel::High;
        } else {
            level = RiskLevel::Critical;
        }

        return {
            probability,
            impact,
            exposure,
            level
        };
    }
};

// ------------------------------------------------------------
// Repository and governance engine
// ------------------------------------------------------------

class RiskGovernanceEngine {
private:
    unordered_map<string, Risk> risks;
    unordered_map<string, set<string>> projectIndex;

    RiskAssessmentEngine assessmentEngine;

    static bool isAllowedTransition(
        RiskStatus current,
        RiskStatus next
    ) {
        switch (current) {
            case RiskStatus::Identified:
                return next == RiskStatus::Assessed ||
                       next == RiskStatus::Closed;

            case RiskStatus::Assessed:
                return next == RiskStatus::MitigationPlanned ||
                       next == RiskStatus::Monitoring ||
                       next == RiskStatus::Escalated ||
                       next == RiskStatus::Closed;

            case RiskStatus::MitigationPlanned:
                return next == RiskStatus::Monitoring ||
                       next == RiskStatus::Escalated ||
                       next == RiskStatus::Closed;

            case RiskStatus::Monitoring:
                return next == RiskStatus::Escalated ||
                       next == RiskStatus::Materialized ||
                       next == RiskStatus::Closed;

            case RiskStatus::Escalated:
                return next == RiskStatus::Monitoring ||
                       next == RiskStatus::Materialized ||
                       next == RiskStatus::Closed;

            case RiskStatus::Materialized:
                return next == RiskStatus::Closed;

            case RiskStatus::Closed:
                return false;
        }

        return false;
    }

    Risk& findRisk(const string& id) {
        auto iterator = risks.find(id);

        if (iterator == risks.end()) {
            throw out_of_range("Risk not found: " + id);
        }

        return iterator->second;
    }

    const Risk& findRisk(const string& id) const {
        auto iterator = risks.find(id);

        if (iterator == risks.end()) {
            throw out_of_range("Risk not found: " + id);
        }

        return iterator->second;
    }

    static void validateText(
        const string& value,
        const string& field
    ) {
        if (value.empty() ||
            value.find_first_not_of(" \t\n\r") == string::npos) {
            throw invalid_argument(field + " is required");
        }
    }

    static string generateId() {
        static unsigned long counter = 0;

        return "RISK-" + to_string(++counter);
    }

public:
    RiskGovernanceEngine() = default;

    string registerRisk(
        const string& projectId,
        const string& title,
        const string& description,
        RiskCategory category,
        const string& owner,
        int probability,
        int impact,
        const string& dueDate,
        RiskResponse response
    ) {
        validateText(projectId, "Project ID");
        validateText(title, "Title");
        validateText(description, "Description");
        validateText(owner, "Owner");

        if (!validDate(dueDate)) {
            throw invalid_argument("Invalid due date");
        }

        assessmentEngine.evaluate(probability, impact);

        Risk risk;

        risk.id = generateId();
        risk.projectId = projectId;
        risk.title = title;
        risk.description = description;
        risk.owner = owner;
        risk.category = category;
        risk.response = response;
        risk.status = RiskStatus::Identified;
        risk.probability = probability;
        risk.impact = impact;
        risk.version = 1;
        risk.reviewCount = 0;
        risk.dueDate = dueDate;

        risk.history.push_back("Risk registered");

        string id = risk.id;

        risks.emplace(id, move(risk));
        projectIndex[projectId].insert(id);

        return id;
    }

    Assessment assess(const string& id) const {
        const Risk& risk = findRisk(id);

        return assessmentEngine.evaluate(
            risk.probability,
            risk.impact
        );
    }

    void transition(
        const string& id,
        RiskStatus next,
        int expectedVersion
    ) {
        Risk& risk = findRisk(id);

        if (risk.version != expectedVersion) {
            throw runtime_error(
                "Concurrent modification detected"
            );
        }

        if (!isAllowedTransition(risk.status, next)) {
            throw logic_error(
                "Invalid lifecycle transition: " +
                toString(risk.status) + " -> " +
                toString(next)
            );
        }

        if (
            next == RiskStatus::MitigationPlanned &&
            risk.mitigationPlan.empty()
        ) {
            throw logic_error(
                "Mitigation plan is required"
            );
        }

        risk.history.push_back(
            "Status changed from " +
            toString(risk.status) +
            " to " + toString(next)
        );

        risk.status = next;
        ++risk.version;
    }

    void setMitigation(
        const string& id,
        const string& plan,
        const string& contingency,
        int expectedVersion
    ) {
        Risk& risk = findRisk(id);

        if (risk.version != expectedVersion) {
            throw runtime_error("Version mismatch");
        }

        if (risk.status != RiskStatus::Assessed) {
            throw logic_error(
                "Risk must be assessed before mitigation"
            );
        }

        validateText(plan, "Mitigation plan");
        validateText(contingency, "Contingency plan");

        risk.mitigationPlan = plan;
        risk.contingencyPlan = contingency;

        ++risk.version;

        risk.history.push_back("Mitigation and contingency recorded");

        transition(
            id,
            RiskStatus::MitigationPlanned,
            risk.version
        );
    }

    void recordObservation(
        const string& id,
        const Observation& observation,
        int expectedVersion
    ) {
        Risk& risk = findRisk(id);

        if (risk.version != expectedVersion) {
            throw runtime_error("Version mismatch");
        }

        if (
            risk.status != RiskStatus::Monitoring &&
            risk.status != RiskStatus::Escalated
        ) {
            throw logic_error(
                "Risk is not actively monitored"
            );
        }

        validateText(observation.recordedBy, "Observer");

        Assessment previous = assess(id);

        Assessment current = assessmentEngine.evaluate(
            observation.probability,
            observation.impact
        );

        risk.probability = observation.probability;
        risk.impact = observation.impact;
        risk.observations.push_back(observation);

        ++risk.reviewCount;
        risk.lastReviewed = observation.timestamp;

        ostringstream event;

        event << "Observation: "
              << previous.exposure
              << " -> "
              << current.exposure;

        risk.history.push_back(event.str());

        if (current.level == RiskLevel::Critical) {
            risk.status = RiskStatus::Escalated;
            risk.history.push_back("Automatically escalated");
        }

        ++risk.version;
    }

    vector<string> getProjectRisks(
        const string& projectId
    ) const {
        vector<string> result;

        auto iterator = projectIndex.find(projectId);

        if (iterator == projectIndex.end()) {
            return result;
        }

        result.assign(
            iterator->second.begin(),
            iterator->second.end()
        );

        return result;
    }

    vector<pair<string, Assessment>> priorityReport() const {
        vector<pair<string, Assessment>> report;

        for (const auto& entry : risks) {
            const Risk& risk = entry.second;

            if (risk.status == RiskStatus::Closed) {
                continue;
            }

            report.push_back({
                risk.id,
                assessmentEngine.evaluate(
                    risk.probability,
                    risk.impact
                )
            });
        }

        sort(
            report.begin(),
            report.end(),
            [](const auto& first, const auto& second) {
                return first.second.exposure >
                       second.second.exposure;
            }
        );

        return report;
    }

    vector<string> staleRisks(int maximumAgeDays) const {
        if (maximumAgeDays < 0) {
            throw invalid_argument(
                "Maximum review age cannot be negative"
            );
        }

        vector<string> result;

        for (const auto& entry : risks) {
            const Risk& risk = entry.second;

            if (risk.status == RiskStatus::Closed) {
                continue;
            }

            if (!risk.lastReviewed.has_value()) {
                result.push_back(risk.id);
            }
        }

        return result;
    }

    RiskReport generateReport() const {
        RiskReport report;

        report.totalRisks = static_cast<int>(risks.size());

        const string today = currentDate();

        for (const auto& entry : risks) {
            const Risk& risk = entry.second;

            Assessment assessment = assessmentEngine.evaluate(
                risk.probability,
                risk.impact
            );

            report.totalExposure += assessment.exposure;

            report.levels[toString(assessment.level)]++;
            report.statuses[toString(risk.status)]++;
            report.categories[toString(risk.category)]++;

            if (risk.status != RiskStatus::Closed) {
                ++report.activeRisks;

                if (risk.dueDate < today) {
                    ++report.overdueRisks;
                }
            }
        }

        return report;
    }

    void printReport() const {
        RiskReport report = generateReport();

        cout << "\nPROJECT RISK REPORT\n";
        cout << "-------------------\n";

        cout << "Total risks: "
             << report.totalRisks << '\n';

        cout << "Active risks: "
             << report.activeRisks << '\n';

        cout << "Overdue risks: "
             << report.overdueRisks << '\n';

        cout << "Total exposure: "
             << report.totalExposure << '\n';

        cout << "\nRISK LEVELS\n";

        for (const auto& item : report.levels) {
            cout << item.first << ": "
                 << item.second << '\n';
        }

        cout << "\nRISK PRIORITY\n";

        for (const auto& item : priorityReport()) {
            cout << item.first
                 << " | Exposure: "
                 << item.second.exposure
                 << " | Level: "
                 << toString(item.second.level)
                 << '\n';
        }
    }

    void printRiskHistory(const string& id) const {
        const Risk& risk = findRisk(id);

        cout << "\nHISTORY: " << risk.title << '\n';

        for (const string& event : risk.history) {
            cout << "- " << event << '\n';
        }
    }
};

// ------------------------------------------------------------
// Demonstration
// ------------------------------------------------------------

int main() {
    try {
        RiskGovernanceEngine engine;

        string supplierRisk = engine.registerRisk(
            "PRJ-2026-001",
            "Critical supplier delivery delay",
            "Hardware delivery may miss the project milestone.",
            RiskCategory::Schedule,
            "Procurement Manager",
            4,
            4,
            "2026-12-15",
            RiskResponse::Mitigate
        );

        string securityRisk = engine.registerRisk(
            "PRJ-2026-001",
            "Unauthorized system access",
            "Potential weakness in access permissions.",
            RiskCategory::Security,
            "Security Manager",
            2,
            5,
            "2026-12-05",
            RiskResponse::Avoid
        );

        // Supplier risk assessment.
        Assessment initial = engine.assess(supplierRisk);

        cout << "Initial supplier exposure: "
             << initial.exposure << '\n';

        // Lifecycle progression.
        engine.transition(
            supplierRisk,
            RiskStatus::Assessed,
            1
        );

        engine.setMitigation(
            supplierRisk,
            "Qualify a secondary supplier.",
            "Use approved reserve inventory.",
            2
        );

        engine.transition(
            supplierRisk,
            RiskStatus::Monitoring,
            3
        );

        Observation observation{
            5,
            5,
            "Supplier confirmed another delay.",
            "Procurement Manager",
            "2026-11-26"
        };

        engine.recordObservation(
            supplierRisk,
            observation,
            4
        );

        engine.printReport();

        engine.printRiskHistory(supplierRisk);

        cout << "\nPROJECT RISK COUNT: "
             << engine.getProjectRisks(
                    "PRJ-2026-001"
                ).size()
             << '\n';

        cout << "\nSTALE RISKS: "
             << engine.staleRisks(7).size()
             << '\n';

        // Invalid assessment demonstration.
        try {
            engine.assess("UNKNOWN-RISK");
        } catch (const exception& error) {
            cerr << "Expected failure: "
                 << error.what() << '\n';
        }

        // Invalid score demonstration.
        try {
            RiskAssessmentEngine().evaluate(8, 2);
        } catch (const exception& error) {
            cerr << "Validation failure: "
                 << error.what() << '\n';
        }

        (void)securityRisk;

    } catch (const exception& error) {
        cerr << "Application failure: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
