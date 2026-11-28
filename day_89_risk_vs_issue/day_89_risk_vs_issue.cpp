#include <algorithm>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include <iomanip>

using namespace std;

enum class RiskStatus {
    Identified,
    Assessed,
    Mitigating,
    Accepted,
    Closed
};

enum class IssueStatus {
    Open,
    InProgress,
    Blocked,
    Resolved,
    Closed
};

enum class Severity {
    Low,
    Medium,
    High,
    Critical
};

enum class Priority {
    Low,
    Medium,
    High,
    Urgent
};

string toString(RiskStatus status) {
    switch (status) {
        case RiskStatus::Identified: return "Identified";
        case RiskStatus::Assessed: return "Assessed";
        case RiskStatus::Mitigating: return "Mitigating";
        case RiskStatus::Accepted: return "Accepted";
        case RiskStatus::Closed: return "Closed";
    }
    throw logic_error("Unknown risk status.");
}

string toString(IssueStatus status) {
    switch (status) {
        case IssueStatus::Open: return "Open";
        case IssueStatus::InProgress: return "In Progress";
        case IssueStatus::Blocked: return "Blocked";
        case IssueStatus::Resolved: return "Resolved";
        case IssueStatus::Closed: return "Closed";
    }
    throw logic_error("Unknown issue status.");
}

string toString(Severity severity) {
    switch (severity) {
        case Severity::Low: return "Low";
        case Severity::Medium: return "Medium";
        case Severity::High: return "High";
        case Severity::Critical: return "Critical";
    }
    throw logic_error("Unknown severity.");
}

string toString(Priority priority) {
    switch (priority) {
        case Priority::Low: return "Low";
        case Priority::Medium: return "Medium";
        case Priority::High: return "High";
        case Priority::Urgent: return "Urgent";
    }
    throw logic_error("Unknown priority.");
}

void validateText(const string& value, const string& field) {
    if (value.find_first_not_of(" \t\n\r") == string::npos) {
        throw invalid_argument(field + " cannot be empty.");
    }
}

struct Risk {
    int id;
    string title;
    string description;
    string owner;
    string category;
    string mitigation;
    string contingency;
    int probability;
    int impact;
    RiskStatus status = RiskStatus::Identified;

    Risk(
        int id,
        string title,
        string description,
        string owner,
        int probability,
        int impact,
        string category,
        string mitigation,
        string contingency
    ) :
        id(id),
        title(move(title)),
        description(move(description)),
        owner(move(owner)),
        category(move(category)),
        mitigation(move(mitigation)),
        contingency(move(contingency)),
        probability(probability),
        impact(impact) {

        validateText(this->title, "Risk title");
        validateText(this->description, "Risk description");
        validateText(this->owner, "Risk owner");

        if (probability < 1 || probability > 5) {
            throw invalid_argument("Probability must be between 1 and 5.");
        }

        if (impact < 1 || impact > 5) {
            throw invalid_argument("Impact must be between 1 and 5.");
        }
    }

    int exposure() const {
        return probability * impact;
    }

    Severity severity() const {
        int score = exposure();

        if (score >= 20) return Severity::Critical;
        if (score >= 12) return Severity::High;
        if (score >= 6) return Severity::Medium;

        return Severity::Low;
    }

    void assess() {
        if (status == RiskStatus::Closed) {
            throw logic_error("Closed risk cannot be assessed.");
        }

        status = RiskStatus::Assessed;
    }

    void startMitigation() {
        if (status != RiskStatus::Identified &&
            status != RiskStatus::Assessed) {
            throw logic_error("Invalid risk transition.");
        }

        validateText(mitigation, "Mitigation plan");
        status = RiskStatus::Mitigating;
    }

    void accept() {
        if (status == RiskStatus::Closed) {
            throw logic_error("Closed risk cannot be accepted.");
        }

        status = RiskStatus::Accepted;
    }

    void close() {
        if (status != RiskStatus::Mitigating &&
            status != RiskStatus::Accepted) {
            throw logic_error("Risk must be mitigated or accepted.");
        }

        status = RiskStatus::Closed;
    }
};

struct Issue {
    int id;
    string title;
    string description;
    string owner;
    int sourceRiskId;
    Severity severity;
    Priority priority;
    IssueStatus status = IssueStatus::Open;
    string resolution;

    Issue(
        int id,
        string title,
        string description,
        string owner,
        Severity severity,
        int sourceRiskId = -1
    ) :
        id(id),
        title(move(title)),
        description(move(description)),
        owner(move(owner)),
        sourceRiskId(sourceRiskId),
        severity(severity),
        priority(
            severity == Severity::Critical ? Priority::Urgent :
            severity == Severity::High ? Priority::High :
            severity == Severity::Medium ? Priority::Medium :
            Priority::Low
        ) {

        validateText(this->title, "Issue title");
        validateText(this->description, "Issue description");
        validateText(this->owner, "Issue owner");
    }

    void start() {
        if (status != IssueStatus::Open) {
            throw logic_error("Only open issues can be started.");
        }

        status = IssueStatus::InProgress;
    }

    void block() {
        if (status != IssueStatus::Open &&
            status != IssueStatus::InProgress) {
            throw logic_error("Invalid issue blocking transition.");
        }

        status = IssueStatus::Blocked;
    }

    void resolve(const string& details) {
        if (status != IssueStatus::Open &&
            status != IssueStatus::InProgress &&
            status != IssueStatus::Blocked) {
            throw logic_error("Issue cannot be resolved.");
        }

        validateText(details, "Resolution");
        resolution = details;
        status = IssueStatus::Resolved;
    }

    void close() {
        if (status != IssueStatus::Resolved) {
            throw logic_error("Only resolved issues can be closed.");
        }

        status = IssueStatus::Closed;
    }
};

class GovernanceEngine {
private:
    map<int, Risk> risks;
    map<int, Issue> issues;

    int nextRiskId = 1;
    int nextIssueId = 1;

public:
    int addRisk(
        const string& title,
        const string& description,
        const string& owner,
        int probability,
        int impact,
        const string& category,
        const string& mitigation,
        const string& contingency
    ) {
        int id = nextRiskId++;

        risks.emplace(
            piecewise_construct,
            forward_as_tuple(id),
            forward_as_tuple(
                id, title, description, owner,
                probability, impact, category,
                mitigation, contingency
            )
        );

        return id;
    }

    int addIssue(
        const string& title,
        const string& description,
        const string& owner,
        Severity severity,
        int sourceRiskId = -1
    ) {
        if (sourceRiskId != -1 &&
            risks.find(sourceRiskId) == risks.end()) {
            throw invalid_argument("Source risk does not exist.");
        }

        int id = nextIssueId++;

        issues.emplace(
            piecewise_construct,
            forward_as_tuple(id),
            forward_as_tuple(
                id, title, description, owner,
                severity, sourceRiskId
            )
        );

        return id;
    }

    int materializeRisk(
        int riskId,
        const string& title,
        const string& description
    ) {
        auto it = risks.find(riskId);

        if (it == risks.end()) {
            throw out_of_range("Risk does not exist.");
        }

        const Risk& risk = it->second;

        // A materialized risk creates a separate issue record.
        return addIssue(
            title,
            description,
            risk.owner,
            risk.severity(),
            riskId
        );
    }

    Risk& getRisk(int id) {
        auto it = risks.find(id);

        if (it == risks.end()) {
            throw out_of_range("Risk not found.");
        }

        return it->second;
    }

    Issue& getIssue(int id) {
        auto it = issues.find(id);

        if (it == issues.end()) {
            throw out_of_range("Issue not found.");
        }

        return it->second;
    }

    vector<const Risk*> prioritizedRisks() const {
        vector<const Risk*> result;

        for (const auto& entry : risks) {
            if (entry.second.status != RiskStatus::Closed) {
                result.push_back(&entry.second);
            }
        }

        // Sorting is O(n log n); map maintains stable ID ordering.
        sort(
            result.begin(),
            result.end(),
            [](const Risk* a, const Risk* b) {
                if (a->exposure() != b->exposure()) {
                    return a->exposure() > b->exposure();
                }

                return a->id < b->id;
            }
        );

        return result;
    }

    vector<const Issue*> unresolvedIssues() const {
        vector<const Issue*> result;

        for (const auto& entry : issues) {
            const Issue& issue = entry.second;

            if (issue.status != IssueStatus::Resolved &&
                issue.status != IssueStatus::Closed) {
                result.push_back(&issue);
            }
        }

        return result;
    }

    void printDashboard() const {
        int criticalRisks = 0;
        int openIssues = 0;
        int urgentIssues = 0;
        int blockedIssues = 0;

        for (const auto& entry : risks) {
            const Risk& risk = entry.second;

            if (risk.status != RiskStatus::Closed &&
                risk.severity() == Severity::Critical) {
                criticalRisks++;
            }
        }

        for (const auto& entry : issues) {
            const Issue& issue = entry.second;

            if (issue.status != IssueStatus::Resolved &&
                issue.status != IssueStatus::Closed) {
                openIssues++;
            }

            if (issue.status != IssueStatus::Resolved &&
                issue.status != IssueStatus::Closed &&
                issue.priority == Priority::Urgent) {
                urgentIssues++;
            }

            if (issue.status == IssueStatus::Blocked) {
                blockedIssues++;
            }
        }

        cout << "\nMANAGEMENT DASHBOARD\n";
        cout << "Total risks: " << risks.size() << '\n';
        cout << "Total issues: " << issues.size() << '\n';
        cout << "Critical active risks: " << criticalRisks << '\n';
        cout << "Unresolved issues: " << openIssues << '\n';
        cout << "Urgent unresolved issues: " << urgentIssues << '\n';
        cout << "Blocked issues: " << blockedIssues << '\n';
    }

    void printRegisters() const {
        cout << "\nRISK REGISTER\n";

        for (const Risk* risk : prioritizedRisks()) {
            cout << "ID: " << risk->id
                 << " | " << risk->title
                 << " | Exposure: " << risk->exposure()
                 << " | Severity: " << toString(risk->severity())
                 << " | Status: " << toString(risk->status)
                 << '\n';
        }

        cout << "\nISSUE REGISTER\n";

        for (const auto& entry : issues) {
            const Issue& issue = entry.second;

            cout << "ID: " << issue.id
                 << " | " << issue.title
                 << " | Severity: " << toString(issue.severity)
                 << " | Priority: " << toString(issue.priority)
                 << " | Status: " << toString(issue.status)
                 << " | Source Risk: ";

            if (issue.sourceRiskId == -1) {
                cout << "None";
            } else {
                cout << issue.sourceRiskId;
            }

            cout << '\n';
        }
    }

    void validate() const {
        for (const auto& entry : issues) {
            const Issue& issue = entry.second;

            if (issue.sourceRiskId != -1 &&
                risks.find(issue.sourceRiskId) == risks.end()) {
                throw logic_error("Broken risk-to-issue relationship.");
            }
        }
    }
};

int main() {
    try {
        GovernanceEngine engine;

        int infrastructureRisk = engine.addRisk(
            "Cloud service outage",
            "The primary cloud region may become unavailable.",
            "Infrastructure Team",
            3,
            5,
            "Technology",
            "Deploy multi-region infrastructure.",
            "Activate the secondary region."
        );

        Risk& risk = engine.getRisk(infrastructureRisk);
        risk.assess();
        risk.startMitigation();

        int securityRisk = engine.addRisk(
            "Credential compromise",
            "An attacker may obtain privileged credentials.",
            "Security Team",
            4,
            5,
            "Cybersecurity",
            "Enforce MFA and privileged access controls.",
            "Revoke credentials and isolate affected systems."
        );

        engine.getRisk(securityRisk).assess();

        // A present production failure is registered as an issue.
        int databaseIssue = engine.addIssue(
            "Database connection failure",
            "Production application cannot connect to PostgreSQL.",
            "Database Team",
            Severity::Critical
        );

        engine.getIssue(databaseIssue).start();
        engine.getIssue(databaseIssue).resolve(
            "Restored the database service and verified connectivity."
        );
        engine.getIssue(databaseIssue).close();

        // The security risk has now materialized.
        int securityIssue = engine.materializeRisk(
            securityRisk,
            "Unauthorized privileged login",
            "Security monitoring confirmed an unauthorized login."
        );

        engine.getIssue(securityIssue).start();

        engine.printRegisters();
        engine.printDashboard();
        engine.validate();

        cout << "\nVALIDATION RESULTS\n";
        cout << "Risk exposure: "
             << risk.exposure() << '\n';

        cout << "Risk severity: "
             << toString(risk.severity()) << '\n';

        cout << "Database issue state: "
             << toString(engine.getIssue(databaseIssue).status) << '\n';

        cout << "Materialized issue source risk: "
             << engine.getIssue(securityIssue).sourceRiskId << '\n';

        // Edge-case validation.
        try {
            engine.addRisk(
                "Invalid risk",
                "Probability outside the allowed range.",
                "Team",
                8,
                5,
                "Operational",
                "Mitigate",
                "Recover"
            );
        } catch (const invalid_argument& error) {
            cout << "Expected validation failure: "
                 << error.what() << '\n';
        }

        cout << "\nAll governance checks passed.\n";

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
