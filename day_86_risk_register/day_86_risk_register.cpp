#include <algorithm>
#include <array>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class RiskCategory {
    Strategic,
    Operational,
    Financial,
    Technology,
    Cybersecurity,
    Compliance,
    Project,
    Reputational
};

enum class RiskStatus {
    Identified,
    Assessed,
    Planned,
    InProgress,
    Monitoring,
    Accepted,
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

string toString(RiskCategory value) {
    static const array<string, 8> names = {
        "Strategic", "Operational", "Financial", "Technology",
        "Cybersecurity", "Compliance", "Project", "Reputational"
    };
    return names.at(static_cast<size_t>(value));
}

string toString(RiskStatus value) {
    static const array<string, 7> names = {
        "Identified", "Assessed", "Treatment Planned",
        "In Progress", "Monitoring", "Accepted", "Closed"
    };
    return names.at(static_cast<size_t>(value));
}

string toString(RiskResponse value) {
    static const array<string, 4> names = {
        "Avoid", "Mitigate", "Transfer", "Accept"
    };
    return names.at(static_cast<size_t>(value));
}

string toString(RiskLevel value) {
    static const array<string, 4> names = {
        "Low", "Medium", "High", "Critical"
    };
    return names.at(static_cast<size_t>(value));
}

RiskLevel classify(int score) {
    if (score < 1 || score > 25) {
        throw invalid_argument("Risk score must be between 1 and 25.");
    }

    if (score >= 20) return RiskLevel::Critical;
    if (score >= 12) return RiskLevel::High;
    if (score >= 6) return RiskLevel::Medium;
    return RiskLevel::Low;
}

struct Risk {
    string id;
    string title;
    string description;
    RiskCategory category;
    string owner;
    int probability;
    int impact;
    RiskResponse response;
    RiskStatus status = RiskStatus::Identified;

    string mitigationPlan;
    string mitigationOwner;
    string targetDate;
    set<string> controls;

    optional<int> residualProbability;
    optional<int> residualImpact;

    int version = 1;

    void validate() const {
        if (id.empty() || title.empty() || owner.empty()) {
            throw invalid_argument(
                "Risk ID, title and owner are required."
            );
        }

        if (probability < 1 || probability > 5 ||
            impact < 1 || impact > 5) {
            throw invalid_argument(
                "Probability and impact must be between 1 and 5."
            );
        }

        if (residualProbability.has_value() !=
            residualImpact.has_value()) {
            throw invalid_argument(
                "Both residual scores must be provided."
            );
        }

        if (residualProbability &&
            (*residualProbability < 1 ||
             *residualProbability > 5 ||
             *residualImpact < 1 ||
             *residualImpact > 5)) {
            throw invalid_argument("Invalid residual scores.");
        }
    }

    int inherentScore() const {
        return probability * impact;
    }

    optional<int> residualScore() const {
        if (!residualProbability) return nullopt;
        return *residualProbability * *residualImpact;
    }

    RiskLevel inherentLevel() const {
        return classify(inherentScore());
    }
};

struct AuditEntry {
    string action;
    string riskId;
    string details;
};

struct GovernancePolicy {
    int minimumMitigationScore = 12;
    int criticalEscalationScore = 20;
    bool requireOwner = true;
    bool requireTreatmentPlan = true;
    bool requireResidualAssessment = true;
    bool allowAcceptance = true;
};

struct Evaluation {
    bool eligible;
    vector<string> blockers;
};

class RiskRegister {
private:
    map<string, Risk> risks;
    vector<AuditEntry> audit;
    GovernancePolicy policy;

    void record(
        const string& action,
        const string& id,
        const string& details
    ) {
        audit.push_back({action, id, details});
    }

    static bool validTransition(
        RiskStatus current,
        RiskStatus next
    ) {
        static const map<RiskStatus, set<RiskStatus>> transitions = {
            {RiskStatus::Identified,
                {RiskStatus::Assessed, RiskStatus::Closed}},
            {RiskStatus::Assessed,
                {RiskStatus::Planned, RiskStatus::Accepted,
                 RiskStatus::Closed}},
            {RiskStatus::Planned,
                {RiskStatus::InProgress, RiskStatus::Accepted,
                 RiskStatus::Closed}},
            {RiskStatus::InProgress,
                {RiskStatus::Monitoring, RiskStatus::Planned,
                 RiskStatus::Closed}},
            {RiskStatus::Monitoring,
                {RiskStatus::InProgress, RiskStatus::Accepted,
                 RiskStatus::Closed}},
            {RiskStatus::Accepted,
                {RiskStatus::Monitoring, RiskStatus::Closed}},
            {RiskStatus::Closed,
                {RiskStatus::Identified}}
        };

        auto it = transitions.find(current);
        return it != transitions.end() &&
               it->second.count(next) > 0;
    }

public:
    explicit RiskRegister(GovernancePolicy governance = {})
        : policy(governance) {}

    void addRisk(const Risk& risk) {
        risk.validate();

        if (risks.count(risk.id)) {
            throw invalid_argument("Duplicate risk ID.");
        }

        risks.emplace(risk.id, risk);
        record("CREATE", risk.id, risk.title);
    }

    const Risk& getRisk(const string& id) const {
        auto it = risks.find(id);
        if (it == risks.end()) {
            throw out_of_range("Risk not found: " + id);
        }
        return it->second;
    }

    void updateAssessment(
        const string& id,
        int probability,
        int impact
    ) {
        Risk& risk = risks.at(id);

        Risk updated = risk;
        updated.probability = probability;
        updated.impact = impact;
        updated.validate();
        updated.version++;

        risk = move(updated);

        record("ASSESSMENT_UPDATE", id,
               "Probability and impact updated.");
    }

    void transition(
        const string& id,
        RiskStatus next,
        const string& justification = ""
    ) {
        Risk& risk = risks.at(id);

        if (!validTransition(risk.status, next)) {
            throw logic_error(
                "Invalid status transition: " +
                toString(risk.status) + " -> " +
                toString(next)
            );
        }

        if ((next == RiskStatus::Accepted ||
             next == RiskStatus::Closed) &&
            justification.empty()) {
            throw invalid_argument(
                "Acceptance and closure require justification."
            );
        }

        risk.status = next;
        risk.version++;

        record("STATUS_CHANGE", id,
               toString(next) + ": " + justification);
    }

    void setMitigation(
        const string& id,
        const string& plan,
        const string& owner,
        const set<string>& controls
    ) {
        if (plan.empty() || owner.empty()) {
            throw invalid_argument(
                "Mitigation plan and owner are required."
            );
        }

        Risk& risk = risks.at(id);
        risk.mitigationPlan = plan;
        risk.mitigationOwner = owner;
        risk.controls = controls;
        risk.version++;

        record("MITIGATION_UPDATE", id, plan);
    }

    void assessResidual(
        const string& id,
        int probability,
        int impact
    ) {
        if (probability < 1 || probability > 5 ||
            impact < 1 || impact > 5) {
            throw invalid_argument("Invalid residual assessment.");
        }

        Risk& risk = risks.at(id);

        if (risk.status == RiskStatus::Closed) {
            throw logic_error("Cannot assess a closed risk.");
        }

        risk.residualProbability = probability;
        risk.residualImpact = impact;
        risk.version++;

        record("RESIDUAL_ASSESSMENT", id,
               "Residual score: " +
               to_string(probability * impact));
    }

    Evaluation evaluate(const string& id) const {
        const Risk& risk = getRisk(id);
        vector<string> blockers;

        if (policy.requireOwner && risk.owner.empty()) {
            blockers.push_back("Risk owner is missing.");
        }

        if (risk.inherentScore() >=
            policy.criticalEscalationScore) {
            blockers.push_back(
                "Critical inherent risk requires escalation."
            );
        }

        if (risk.inherentScore() >=
                policy.minimumMitigationScore &&
            risk.response == RiskResponse::Mitigate &&
            policy.requireTreatmentPlan &&
            risk.mitigationPlan.empty()) {
            blockers.push_back(
                "High exposure requires a mitigation plan."
            );
        }

        if (risk.response == RiskResponse::Accept &&
            (!policy.allowAcceptance ||
             risk.status != RiskStatus::Accepted)) {
            blockers.push_back(
                "Formal acceptance is not authorised or recorded."
            );
        }

        if (risk.response == RiskResponse::Mitigate &&
            policy.requireResidualAssessment &&
            risk.status == RiskStatus::Monitoring &&
            !risk.residualScore()) {
            blockers.push_back(
                "Residual assessment is required."
            );
        }

        return {
            blockers.empty(),
            blockers
        };
    }

    vector<Risk> prioritisedRisks() const {
        vector<Risk> result;

        for (const auto& [id, risk] : risks) {
            if (risk.status != RiskStatus::Closed) {
                result.push_back(risk);
            }
        }

        // Sorting is O(n log n); map lookup is O(log n).
        sort(result.begin(), result.end(),
             [](const Risk& a, const Risk& b) {
                 if (a.inherentScore() != b.inherentScore()) {
                     return a.inherentScore() > b.inherentScore();
                 }
                 return a.id < b.id;
             });

        return result;
    }

    void printReport() const {
        map<RiskLevel, int> distribution = {
            {RiskLevel::Low, 0},
            {RiskLevel::Medium, 0},
            {RiskLevel::High, 0},
            {RiskLevel::Critical, 0}
        };

        double totalScore = 0;
        int openCount = 0;

        for (const auto& [id, risk] : risks) {
            distribution[risk.inherentLevel()]++;
            totalScore += risk.inherentScore();

            if (risk.status != RiskStatus::Closed) {
                openCount++;
            }
        }

        cout << "\nENTERPRISE RISK REGISTER\n";
        cout << string(95, '=') << '\n';

        cout << left
             << setw(12) << "Risk ID"
             << setw(32) << "Title"
             << setw(14) << "Score"
             << setw(14) << "Level"
             << setw(20) << "Status"
             << '\n';

        for (const Risk& risk : prioritisedRisks()) {
            cout << left
                 << setw(12) << risk.id
                 << setw(32) << risk.title.substr(0, 30)
                 << setw(14) << risk.inherentScore()
                 << setw(14) << toString(risk.inherentLevel())
                 << setw(20) << toString(risk.status)
                 << '\n';
        }

        cout << "\nRISK DISTRIBUTION\n";

        for (const auto& [level, count] : distribution) {
            cout << toString(level) << ": " << count << '\n';
        }

        cout << "Total risks: " << risks.size() << '\n';
        cout << "Open risks: " << openCount << '\n';

        cout << "Average inherent score: "
             << fixed << setprecision(2)
             << (risks.empty() ? 0.0 :
                 totalScore / risks.size()) << '\n';

        cout << "Audit events: " << audit.size() << '\n';
    }
};

int main() {
    try {
        GovernancePolicy policy;
        policy.minimumMitigationScore = 12;
        policy.criticalEscalationScore = 20;

        RiskRegister registerEngine(policy);

        registerEngine.addRisk({
            "R-001",
            "Ransomware incident",
            "Malicious encryption of critical enterprise systems.",
            RiskCategory::Cybersecurity,
            "Security Director",
            4,
            5,
            RiskResponse::Mitigate
        });

        registerEngine.addRisk({
            "R-002",
            "Cloud service disruption",
            "Cloud infrastructure outage may interrupt operations.",
            RiskCategory::Technology,
            "Infrastructure Manager",
            3,
            4,
            RiskResponse::Mitigate
        });

        registerEngine.addRisk({
            "R-003",
            "Budget overrun",
            "Unexpected expenditure may exceed approved budget.",
            RiskCategory::Financial,
            "Finance Controller",
            3,
            3,
            RiskResponse::Transfer
        });

        registerEngine.setMitigation(
            "R-001",
            "Implement EDR, MFA, immutable backups and recovery testing.",
            "Security Operations",
            {"EDR", "MFA", "Immutable Backup"}
        );

        registerEngine.transition(
            "R-001",
            RiskStatus::Assessed,
            "Initial assessment completed."
        );

        registerEngine.transition(
            "R-001",
            RiskStatus::Planned,
            "Treatment approved."
        );

        registerEngine.transition(
            "R-001",
            RiskStatus::InProgress,
            "Controls deployment started."
        );

        registerEngine.assessResidual("R-001", 2, 3);

        registerEngine.transition(
            "R-001",
            RiskStatus::Monitoring,
            "Controls deployed and effectiveness monitoring started."
        );

        cout << "\nGOVERNANCE EVALUATION\n";

        for (const string id : {"R-001", "R-002", "R-003"}) {
            Evaluation result = registerEngine.evaluate(id);

            cout << id << ": "
                 << (result.eligible ? "ELIGIBLE" : "BLOCKED")
                 << '\n';

            for (const string& blocker : result.blockers) {
                cout << "  - " << blocker << '\n';
            }
        }

        registerEngine.printReport();

        // Demonstrate invalid score rejection.
        try {
            registerEngine.updateAssessment("R-002", 7, 3);
        } catch (const exception& error) {
            cout << "\nExpected validation failure: "
                 << error.what() << '\n';
        }

    } catch (const exception& error) {
        cerr << "Risk engine error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
