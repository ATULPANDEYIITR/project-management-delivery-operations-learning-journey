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

using namespace std;

/*
 * RISK RESPONSE AND MERGE-FREE GOVERNANCE ENGINE
 *
 * Implements:
 * - Threat and opportunity strategies.
 * - Risk ownership.
 * - Response planning and approval.
 * - Action budgeting.
 * - Residual exposure assessment.
 * - Secondary risks.
 * - Escalation.
 * - Monitoring and merge-free reporting.
 *
 * C++17, standard library only.
 */

enum class RiskType {
    Threat,
    Opportunity
};

enum class RiskState {
    Identified,
    Planned,
    Approved,
    InProgress,
    Monitoring,
    Escalated,
    Closed
};

enum class Strategy {
    Avoid,
    Mitigate,
    Transfer,
    Accept,
    Escalate,
    Exploit,
    Enhance,
    Share
};

enum class ActionState {
    Pending,
    InProgress,
    Completed,
    Blocked,
    Cancelled
};

string toString(RiskType type) {
    return type == RiskType::Threat ? "THREAT" : "OPPORTUNITY";
}

string toString(RiskState state) {
    switch (state) {
        case RiskState::Identified: return "IDENTIFIED";
        case RiskState::Planned: return "PLANNED";
        case RiskState::Approved: return "APPROVED";
        case RiskState::InProgress: return "IN_PROGRESS";
        case RiskState::Monitoring: return "MONITORING";
        case RiskState::Escalated: return "ESCALATED";
        case RiskState::Closed: return "CLOSED";
    }
    throw logic_error("Unknown risk state.");
}

string toString(Strategy strategy) {
    switch (strategy) {
        case Strategy::Avoid: return "AVOID";
        case Strategy::Mitigate: return "MITIGATE";
        case Strategy::Transfer: return "TRANSFER";
        case Strategy::Accept: return "ACCEPT";
        case Strategy::Escalate: return "ESCALATE";
        case Strategy::Exploit: return "EXPLOIT";
        case Strategy::Enhance: return "ENHANCE";
        case Strategy::Share: return "SHARE";
    }
    throw logic_error("Unknown strategy.");
}

string toString(ActionState state) {
    switch (state) {
        case ActionState::Pending: return "PENDING";
        case ActionState::InProgress: return "IN_PROGRESS";
        case ActionState::Completed: return "COMPLETED";
        case ActionState::Blocked: return "BLOCKED";
        case ActionState::Cancelled: return "CANCELLED";
    }
    throw logic_error("Unknown action state.");
}

struct ResponseAction {
    int id;
    string description;
    string owner;
    double cost;
    ActionState state = ActionState::Pending;
};

struct Risk {
    int id;
    string title;
    string description;
    RiskType type;
    double probability;
    int impact;
    string owner;
    string category;

    optional<Strategy> strategy;
    RiskState state = RiskState::Identified;

    double budget = 0.0;
    optional<double> residualProbability;
    optional<int> residualImpact;

    vector<ResponseAction> actions;
    vector<int> secondaryRiskIds;

    double inherentScore() const {
        return probability * impact;
    }

    double residualScore() const {
        return residualProbability.value_or(probability) *
               residualImpact.value_or(impact);
    }

    double effectiveness() const {
        double original = inherentScore();

        if (original == 0.0) return 0.0;

        return max(
            0.0,
            min(100.0,
                (original - residualScore()) / original * 100.0)
        );
    }

    double committedBudget() const {
        double total = 0.0;

        for (const auto& action : actions) {
            if (action.state != ActionState::Cancelled) {
                total += action.cost;
            }
        }

        return total;
    }
};

struct AuditEvent {
    int riskId;
    string event;
};

class RiskGovernanceEngine {
private:
    map<int, Risk> risks;
    vector<AuditEvent> audit;
    int nextRiskId = 1;
    int nextActionId = 1;

    Risk& findRisk(int id) {
        auto it = risks.find(id);

        if (it == risks.end()) {
            throw invalid_argument("Risk does not exist.");
        }

        return it->second;
    }

    const Risk& findRisk(int id) const {
        auto it = risks.find(id);

        if (it == risks.end()) {
            throw invalid_argument("Risk does not exist.");
        }

        return it->second;
    }

    void log(int riskId, const string& event) {
        audit.push_back({riskId, event});
    }

    static bool validStrategy(RiskType type, Strategy strategy) {
        if (type == RiskType::Threat) {
            return strategy == Strategy::Avoid ||
                   strategy == Strategy::Mitigate ||
                   strategy == Strategy::Transfer ||
                   strategy == Strategy::Accept ||
                   strategy == Strategy::Escalate;
        }

        return strategy == Strategy::Exploit ||
               strategy == Strategy::Enhance ||
               strategy == Strategy::Share ||
               strategy == Strategy::Accept ||
               strategy == Strategy::Escalate;
    }

public:
    int createRisk(
        const string& title,
        const string& description,
        RiskType type,
        double probability,
        int impact,
        const string& owner,
        const string& category,
        double budget
    ) {
        if (title.empty() || description.empty() || owner.empty()) {
            throw invalid_argument(
                "Title, description and owner are required."
            );
        }

        if (!isfinite(probability) ||
            probability < 0.0 ||
            probability > 1.0) {
            throw invalid_argument(
                "Probability must be between 0 and 1."
            );
        }

        if (impact < 1 || impact > 5) {
            throw invalid_argument("Impact must be between 1 and 5.");
        }

        if (!isfinite(budget) || budget < 0.0) {
            throw invalid_argument("Budget cannot be negative.");
        }

        int id = nextRiskId++;

        Risk risk{
            id,
            title,
            description,
            type,
            probability,
            impact,
            owner,
            category
        };

        risk.budget = budget;
        risks.emplace(id, move(risk));

        log(id, "RISK_CREATED");

        return id;
    }

    void planResponse(
        int riskId,
        Strategy strategy,
        const string& responseOwner
    ) {
        Risk& risk = findRisk(riskId);

        if (risk.state != RiskState::Identified &&
            risk.state != RiskState::Planned) {
            throw logic_error(
                "Response planning is not allowed in this state."
            );
        }

        if (responseOwner.empty()) {
            throw invalid_argument("Response owner is required.");
        }

        if (!validStrategy(risk.type, strategy)) {
            throw invalid_argument(
                "Strategy is incompatible with risk type."
            );
        }

        risk.strategy = strategy;
        risk.state = RiskState::Planned;

        log(riskId, "RESPONSE_PLANNED:" + toString(strategy));
    }

    void approveResponse(int riskId, const string& approver) {
        Risk& risk = findRisk(riskId);

        if (risk.state != RiskState::Planned) {
            throw logic_error("Only planned responses can be approved.");
        }

        if (approver.empty()) {
            throw invalid_argument("Approver is required.");
        }

        risk.state = RiskState::Approved;
        log(riskId, "APPROVED_BY:" + approver);
    }

    int addAction(
        int riskId,
        const string& description,
        const string& owner,
        double cost
    ) {
        Risk& risk = findRisk(riskId);

        if (risk.state != RiskState::Planned &&
            risk.state != RiskState::Approved &&
            risk.state != RiskState::InProgress) {
            throw logic_error(
                "Risk requires a planned response before adding actions."
            );
        }

        if (description.empty() || owner.empty()) {
            throw invalid_argument(
                "Action description and owner are required."
            );
        }

        if (!isfinite(cost) || cost < 0.0) {
            throw invalid_argument("Action cost cannot be negative.");
        }

        if (risk.committedBudget() + cost > risk.budget + 1e-9) {
            throw runtime_error("Response budget exceeded.");
        }

        int actionId = nextActionId++;

        risk.actions.push_back({
            actionId,
            description,
            owner,
            cost,
            ActionState::Pending
        });

        log(riskId, "ACTION_ADDED:" + to_string(actionId));

        return actionId;
    }

    void updateAction(
        int riskId,
        int actionId,
        ActionState newState
    ) {
        Risk& risk = findRisk(riskId);

        auto it = find_if(
            risk.actions.begin(),
            risk.actions.end(),
            [actionId](const ResponseAction& action) {
                return action.id == actionId;
            }
        );

        if (it == risk.actions.end()) {
            throw invalid_argument("Action does not exist.");
        }

        if (it->state == ActionState::Completed ||
            it->state == ActionState::Cancelled) {
            throw logic_error("Terminal action cannot be modified.");
        }

        it->state = newState;

        if (newState == ActionState::InProgress) {
            risk.state = RiskState::InProgress;
        }

        bool allFinished = !risk.actions.empty() &&
            all_of(
                risk.actions.begin(),
                risk.actions.end(),
                [](const ResponseAction& action) {
                    return action.state == ActionState::Completed ||
                           action.state == ActionState::Cancelled;
                }
            );

        if (allFinished) {
            risk.state = RiskState::Monitoring;
        }

        log(
            riskId,
            "ACTION_STATE_CHANGED:" + toString(newState)
        );
    }

    void setResidualRisk(
        int riskId,
        double probability,
        int impact
    ) {
        Risk& risk = findRisk(riskId);

        if (!isfinite(probability) ||
            probability < 0.0 ||
            probability > 1.0) {
            throw invalid_argument(
                "Residual probability must be between 0 and 1."
            );
        }

        if (impact < 1 || impact > 5) {
            throw invalid_argument(
                "Residual impact must be between 1 and 5."
            );
        }

        risk.residualProbability = probability;
        risk.residualImpact = impact;

        log(riskId, "RESIDUAL_RISK_ASSESSED");
    }

    void linkSecondaryRisk(int parentId, int secondaryId) {
        Risk& parent = findRisk(parentId);
        findRisk(secondaryId);

        if (parentId == secondaryId) {
            throw invalid_argument(
                "A risk cannot be its own secondary risk."
            );
        }

        if (find(
            parent.secondaryRiskIds.begin(),
            parent.secondaryRiskIds.end(),
            secondaryId
        ) == parent.secondaryRiskIds.end()) {
            parent.secondaryRiskIds.push_back(secondaryId);
        }

        log(parentId, "SECONDARY_RISK_LINKED");
    }

    void escalate(int riskId, const string& reason) {
        Risk& risk = findRisk(riskId);

        if (reason.empty()) {
            throw invalid_argument("Escalation reason is required.");
        }

        risk.state = RiskState::Escalated;
        log(riskId, "ESCALATED:" + reason);
    }

    void closeRisk(int riskId) {
        Risk& risk = findRisk(riskId);

        bool unfinished = any_of(
            risk.actions.begin(),
            risk.actions.end(),
            [](const ResponseAction& action) {
                return action.state != ActionState::Completed &&
                       action.state != ActionState::Cancelled;
            }
        );

        if (unfinished) {
            throw logic_error(
                "Outstanding actions prevent risk closure."
            );
        }

        risk.state = RiskState::Closed;
        log(riskId, "RISK_CLOSED");
    }

    void report() const {
        vector<reference_wrapper<const Risk>> ordered;

        for (const auto& [id, risk] : risks) {
            ordered.push_back(cref(risk));
        }

        sort(
            ordered.begin(),
            ordered.end(),
            [](const auto& a, const auto& b) {
                return a.get().residualScore() >
                       b.get().residualScore();
            }
        );

        cout << "\nRISK RESPONSE GOVERNANCE REPORT\n";
        cout << string(85, '=') << '\n';

        cout << left
             << setw(5) << "ID"
             << setw(32) << "RISK"
             << setw(15) << "TYPE"
             << setw(15) << "STATUS"
             << setw(10) << "SCORE"
             << '\n';

        for (const auto& reference : ordered) {
            const Risk& risk = reference.get();

            cout << left
                 << setw(5) << risk.id
                 << setw(32) << risk.title.substr(0, 30)
                 << setw(15) << toString(risk.type)
                 << setw(15) << toString(risk.state)
                 << fixed << setprecision(2)
                 << risk.residualScore()
                 << '\n';
        }

        cout << "\nDETAILED ASSESSMENT\n";

        for (const auto& [id, risk] : risks) {
            cout << "\n" << risk.title << '\n';

            cout << "Strategy: ";

            if (risk.strategy) {
                cout << toString(*risk.strategy);
            } else {
                cout << "Not planned";
            }

            cout << "\nInherent score: " << risk.inherentScore();
            cout << "\nResidual score: " << risk.residualScore();
            cout << "\nResponse effectiveness: "
                 << risk.effectiveness() << "%";

            cout << "\nBudget committed: "
                 << risk.committedBudget()
                 << " / " << risk.budget;

            cout << "\nActions: " << risk.actions.size() << '\n';
        }
    }

    void printAudit() const {
        cout << "\nAUDIT LOG\n";

        for (const auto& event : audit) {
            cout << "Risk " << event.riskId
                 << " | " << event.event << '\n';
        }
    }

    const Risk& getRisk(int id) const {
        return findRisk(id);
    }
};

double expectedMonetaryValue(
    double probability,
    double financialImpact
) {
    if (!isfinite(probability) ||
        probability < 0 ||
        probability > 1 ||
        !isfinite(financialImpact) ||
        financialImpact < 0) {
        throw invalid_argument("Invalid EMV inputs.");
    }

    return probability * financialImpact;
}

Strategy recommendStrategy(const Risk& risk) {
    double score = risk.inherentScore();

    if (risk.type == RiskType::Threat) {
        if (score >= 3.5) return Strategy::Avoid;
        if (score >= 2.0) return Strategy::Mitigate;
        if (score >= 1.0) return Strategy::Transfer;
        return Strategy::Accept;
    }

    if (score >= 3.0) return Strategy::Exploit;
    if (score >= 1.5) return Strategy::Enhance;

    return Strategy::Accept;
}

int main() {
    try {
        RiskGovernanceEngine engine;

        int supplierRisk = engine.createRisk(
            "Supplier delivery delay",
            "Cloud infrastructure may not arrive on schedule.",
            RiskType::Threat,
            0.60,
            5,
            "Project Manager",
            "Procurement",
            15000.0
        );

        const Risk& initialRisk = engine.getRisk(supplierRisk);

        engine.planResponse(
            supplierRisk,
            recommendStrategy(initialRisk),
            "Procurement Lead"
        );

        engine.approveResponse(
            supplierRisk,
            "Project Sponsor"
        );

        int actionId = engine.addAction(
            supplierRisk,
            "Qualify an alternative infrastructure supplier.",
            "Procurement Lead",
            5000.0
        );

        engine.updateAction(
            supplierRisk,
            actionId,
            ActionState::InProgress
        );

        engine.updateAction(
            supplierRisk,
            actionId,
            ActionState::Completed
        );

        engine.setResidualRisk(supplierRisk, 0.20, 3);

        int opportunityId = engine.createRisk(
            "Automated testing opportunity",
            "Testing automation may shorten deployment cycles.",
            RiskType::Opportunity,
            0.70,
            4,
            "Engineering Manager",
            "Technology",
            8000.0
        );

        engine.planResponse(
            opportunityId,
            recommendStrategy(engine.getRisk(opportunityId)),
            "Automation Lead"
        );

        engine.approveResponse(
            opportunityId,
            "Engineering Director"
        );

        engine.linkSecondaryRisk(
            supplierRisk,
            opportunityId
        );

        cout << fixed << setprecision(2);

        cout << "\nEXPECTED MONETARY VALUE\n";

        cout << "Inherent exposure: "
             << expectedMonetaryValue(0.60, 100000)
             << '\n';

        cout << "Residual exposure: "
             << expectedMonetaryValue(0.20, 60000)
             << '\n';

        engine.report();
        engine.printAudit();

        const Risk& finalRisk = engine.getRisk(supplierRisk);

        if (abs(finalRisk.residualScore() - 0.60) > 1e-9) {
            throw runtime_error("Residual score assertion failed.");
        }

        if (abs(finalRisk.effectiveness() - 80.0) > 1e-9) {
            throw runtime_error("Effectiveness assertion failed.");
        }

        try {
            engine.planResponse(
                supplierRisk,
                Strategy::Exploit,
                "Invalid Owner"
            );
        } catch (const exception& error) {
            cout << "\nEXPECTED VALIDATION FAILURE: "
                 << error.what() << '\n';
        }

        cout << "\nRisk response engine completed successfully.\n";

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
