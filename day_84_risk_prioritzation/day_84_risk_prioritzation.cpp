#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * C++17 PROJECT RISK PRIORITIZATION ENGINE
 *
 * Evaluates risks, ranks exposures, applies governance rules,
 * and selects mitigation actions under a limited budget.
 */

enum class RiskCategory {
    Technical,
    Security,
    Financial,
    Operational,
    Schedule,
    Legal,
    Resource,
    External
};

enum class RiskStatus {
    Identified,
    Assessed,
    Mitigating,
    Monitoring,
    Closed
};

enum class Priority {
    Low,
    Medium,
    High,
    Critical
};

string toString(RiskCategory category) {
    switch (category) {
        case RiskCategory::Technical: return "Technical";
        case RiskCategory::Security: return "Security";
        case RiskCategory::Financial: return "Financial";
        case RiskCategory::Operational: return "Operational";
        case RiskCategory::Schedule: return "Schedule";
        case RiskCategory::Legal: return "Legal";
        case RiskCategory::Resource: return "Resource";
        case RiskCategory::External: return "External";
    }

    throw invalid_argument("Unknown risk category.");
}

string toString(RiskStatus status) {
    switch (status) {
        case RiskStatus::Identified: return "Identified";
        case RiskStatus::Assessed: return "Assessed";
        case RiskStatus::Mitigating: return "Mitigating";
        case RiskStatus::Monitoring: return "Monitoring";
        case RiskStatus::Closed: return "Closed";
    }

    throw invalid_argument("Unknown risk status.");
}

string toString(Priority priority) {
    switch (priority) {
        case Priority::Critical: return "CRITICAL";
        case Priority::High: return "HIGH";
        case Priority::Medium: return "MEDIUM";
        case Priority::Low: return "LOW";
    }

    throw invalid_argument("Unknown priority.");
}

struct Risk {
    string id;
    string title;
    RiskCategory category;
    int probability;
    int impact;
    int urgency;
    int detectability;
    int mitigationEffectiveness;
    string owner;
    double mitigationCost;
    RiskStatus status;

    void validate() const {
        if (id.empty() || title.empty() || owner.empty()) {
            throw invalid_argument(
                "Risk ID, title, and owner are required."
            );
        }

        const vector<int> values = {
            probability,
            impact,
            urgency,
            detectability,
            mitigationEffectiveness
        };

        for (int value : values) {
            if (value < 1 || value > 5) {
                throw invalid_argument(
                    "Risk ratings must be between 1 and 5."
                );
            }
        }

        if (!isfinite(mitigationCost) || mitigationCost < 0) {
            throw invalid_argument("Invalid mitigation cost.");
        }
    }

    double inherentScore() const {
        return probability * impact * urgency;
    }

    double residualScore() const {
        double detectionFactor =
            0.8 + (detectability - 1) * 0.1;

        double mitigationFactor =
            1.0 - mitigationEffectiveness * 0.12;

        return round(
            inherentScore() * detectionFactor * mitigationFactor
            * 100.0
        ) / 100.0;
    }

    Priority priority() const {
        double score = residualScore();

        if (score >= 60) return Priority::Critical;
        if (score >= 35) return Priority::High;
        if (score >= 15) return Priority::Medium;

        return Priority::Low;
    }
};

struct MitigationDecision {
    string riskId;
    double cost;
    bool funded;
};

class RiskGovernanceEngine {
private:
    map<string, Risk> risks;

    static bool isValidTransition(
        RiskStatus current,
        RiskStatus next
    ) {
        switch (current) {
            case RiskStatus::Identified:
                return next == RiskStatus::Assessed ||
                       next == RiskStatus::Closed;

            case RiskStatus::Assessed:
                return next == RiskStatus::Mitigating ||
                       next == RiskStatus::Monitoring ||
                       next == RiskStatus::Closed;

            case RiskStatus::Mitigating:
                return next == RiskStatus::Monitoring ||
                       next == RiskStatus::Assessed ||
                       next == RiskStatus::Closed;

            case RiskStatus::Monitoring:
                return next == RiskStatus::Mitigating ||
                       next == RiskStatus::Closed;

            case RiskStatus::Closed:
                return false;
        }

        return false;
    }

public:
    void addRisk(const Risk& risk) {
        risk.validate();

        if (risks.count(risk.id)) {
            throw invalid_argument(
                "Duplicate risk ID: " + risk.id
            );
        }

        risks.emplace(risk.id, risk);
    }

    void updateStatus(
        const string& id,
        RiskStatus next
    ) {
        auto it = risks.find(id);

        if (it == risks.end()) {
            throw out_of_range("Risk not found: " + id);
        }

        if (!isValidTransition(it->second.status, next)) {
            throw invalid_argument(
                "Invalid risk status transition."
            );
        }

        it->second.status = next;
    }

    void updateAssessment(
        const string& id,
        int probability,
        int impact,
        int urgency,
        int detectability,
        int mitigationEffectiveness
    ) {
        auto it = risks.find(id);

        if (it == risks.end()) {
            throw out_of_range("Risk not found: " + id);
        }

        if (it->second.status == RiskStatus::Closed) {
            throw invalid_argument(
                "Closed risks cannot be reassessed."
            );
        }

        Risk updated = it->second;

        updated.probability = probability;
        updated.impact = impact;
        updated.urgency = urgency;
        updated.detectability = detectability;
        updated.mitigationEffectiveness =
            mitigationEffectiveness;

        updated.validate();

        // Commit the update only after validation succeeds.
        it->second = updated;
    }

    vector<Risk> rankedRisks(
        bool includeClosed = false
    ) const {
        vector<Risk> result;

        for (const auto& entry : risks) {
            const Risk& risk = entry.second;

            if (!includeClosed &&
                risk.status == RiskStatus::Closed) {
                continue;
            }

            result.push_back(risk);
        }

        sort(
            result.begin(),
            result.end(),
            [](const Risk& a, const Risk& b) {
                if (a.residualScore() != b.residualScore()) {
                    return a.residualScore() > b.residualScore();
                }

                if (a.inherentScore() != b.inherentScore()) {
                    return a.inherentScore() > b.inherentScore();
                }

                return a.id < b.id;
            }
        );

        return result;
    }

    map<string, double> categoryExposure() const {
        map<string, double> exposure;

        for (const auto& risk : rankedRisks()) {
            exposure[toString(risk.category)] +=
                risk.residualScore();
        }

        return exposure;
    }

    vector<MitigationDecision> allocateMitigationBudget(
        double budget
    ) const {
        if (!isfinite(budget) || budget < 0) {
            throw invalid_argument("Invalid mitigation budget.");
        }

        vector<MitigationDecision> decisions;
        double remaining = budget;

        for (const Risk& risk : rankedRisks()) {
            if (risk.priority() != Priority::Critical &&
                risk.priority() != Priority::High) {
                continue;
            }

            bool funded = risk.mitigationCost <= remaining;

            if (funded) {
                remaining -= risk.mitigationCost;
            }

            decisions.push_back({
                risk.id,
                risk.mitigationCost,
                funded
            });
        }

        return decisions;
    }

    void displayRanking() const {
        cout << "\nPROJECT RISK PRIORITIZATION\n";
        cout << string(105, '=') << '\n';

        cout << left
             << setw(10) << "ID"
             << setw(30) << "Risk"
             << setw(15) << "Category"
             << right
             << setw(12) << "Score"
             << "  "
             << left
             << setw(12) << "Priority"
             << "Owner\n";

        cout << string(105, '-') << '\n';

        for (const Risk& risk : rankedRisks()) {
            cout << left
                 << setw(10) << risk.id
                 << setw(30) << risk.title.substr(0, 29)
                 << setw(15) << toString(risk.category)
                 << right
                 << setw(12) << fixed << setprecision(2)
                 << risk.residualScore()
                 << "  "
                 << left
                 << setw(12) << toString(risk.priority())
                 << risk.owner
                 << '\n';
        }
    }

    size_t size() const {
        return risks.size();
    }
};

void runTests() {
    Risk risk{
        "TEST01",
        "Security incident",
        RiskCategory::Security,
        5, 5, 5, 5, 1,
        "Security Lead",
        50000,
        RiskStatus::Identified
    };

    risk.validate();

    if (risk.inherentScore() != 125 ||
        risk.residualScore() != 112.5 ||
        risk.priority() != Priority::Critical) {
        throw runtime_error("Risk calculation test failed.");
    }

    RiskGovernanceEngine engine;
    engine.addRisk(risk);

    if (engine.size() != 1) {
        throw runtime_error("Registration test failed.");
    }

    try {
        engine.addRisk(risk);
        throw runtime_error("Duplicate risk accepted.");
    } catch (const invalid_argument&) {
        // Expected duplicate rejection.
    }

    try {
        engine.updateAssessment(
            "TEST01", 6, 5, 5, 5, 1
        );
        throw runtime_error("Invalid rating accepted.");
    } catch (const invalid_argument&) {
        // Existing assessment remains unchanged.
    }

    if (engine.rankedRisks()[0].probability != 5) {
        throw runtime_error("Atomic update test failed.");
    }

    cout << "C++17 validation tests passed.\n";
}

int main() {
    try {
        runTests();

        RiskGovernanceEngine engine;

        vector<Risk> sampleRisks = {
            {
                "R001", "Cybersecurity breach",
                RiskCategory::Security,
                5, 5, 5, 5, 1,
                "Security Lead", 150000,
                RiskStatus::Assessed
            },
            {
                "R002", "Cloud migration failure",
                RiskCategory::Technical,
                4, 5, 4, 3, 2,
                "Cloud Architect", 80000,
                RiskStatus::Assessed
            },
            {
                "R003", "Budget overrun",
                RiskCategory::Financial,
                4, 4, 4, 2, 3,
                "Finance Lead", 30000,
                RiskStatus::Assessed
            },
            {
                "R004", "Vendor delivery delay",
                RiskCategory::Schedule,
                3, 3, 2, 2, 4,
                "Project Manager", 10000,
                RiskStatus::Assessed
            },
            {
                "R005", "Regulatory non-compliance",
                RiskCategory::Legal,
                3, 5, 5, 4, 1,
                "Compliance Officer", 45000,
                RiskStatus::Assessed
            }
        };

        for (const Risk& risk : sampleRisks) {
            engine.addRisk(risk);
        }

        engine.updateAssessment(
            "R003", 5, 4, 5, 2, 3
        );

        engine.displayRanking();

        cout << "\nCATEGORY EXPOSURE\n";

        for (const auto& item : engine.categoryExposure()) {
            cout << left << setw(18) << item.first
                 << fixed << setprecision(2)
                 << item.second << '\n';
        }

        cout << "\nMITIGATION BUDGET ALLOCATION\n";

        auto decisions =
            engine.allocateMitigationBudget(100000);

        for (const auto& decision : decisions) {
            cout << decision.riskId
                 << " | Cost: " << decision.cost
                 << " | Funded: "
                 << (decision.funded ? "YES" : "NO")
                 << '\n';
        }

        cout << "\nTotal registered risks: "
             << engine.size() << '\n';

    } catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
