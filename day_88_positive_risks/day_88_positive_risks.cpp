#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

/*
 * POSITIVE RISK AND PROJECT OPPORTUNITY GOVERNANCE ENGINE
 *
 * Evaluates project opportunities and determines:
 * - Financial attractiveness
 * - Probability-weighted value
 * - Response costs
 * - Risk-adjusted opportunity ranking
 * - Response strategy
 * - Execution status
 * - Portfolio-level performance
 *
 * C++17 implementation using STL containers and domain modeling.
 */

enum class Category {
    Cost,
    Schedule,
    Quality,
    Technology,
    Resource,
    Business,
    Strategic
};

enum class Strategy {
    Exploit,
    Enhance,
    Share,
    Accept
};

enum class Status {
    Identified,
    Assessed,
    Planned,
    InProgress,
    Realized,
    Closed
};

string toString(Strategy strategy) {
    switch (strategy) {
        case Strategy::Exploit: return "Exploit";
        case Strategy::Enhance: return "Enhance";
        case Strategy::Share: return "Share";
        case Strategy::Accept: return "Accept";
    }
    throw invalid_argument("Unknown strategy.");
}

string toString(Status status) {
    switch (status) {
        case Status::Identified: return "Identified";
        case Status::Assessed: return "Assessed";
        case Status::Planned: return "Planned";
        case Status::InProgress: return "In Progress";
        case Status::Realized: return "Realized";
        case Status::Closed: return "Closed";
    }
    throw invalid_argument("Unknown status.");
}

struct Opportunity {
    string id;
    string title;
    Category category;
    double probability;
    double impact;
    double responseCost;
    double confidence;
    string owner;
    Strategy strategy;
    Status status = Status::Identified;
    double realizedBenefit = 0.0;
    string responseAction;

    void validate() const {
        if (id.empty() || title.empty() || owner.empty()) {
            throw invalid_argument(
                "Opportunity ID, title, and owner are required."
            );
        }

        if (!isfinite(probability) ||
            probability < 0.0 ||
            probability > 1.0) {
            throw invalid_argument("Probability must be between 0 and 1.");
        }

        if (!isfinite(impact) || impact < 0.0 ||
            !isfinite(responseCost) || responseCost < 0.0) {
            throw invalid_argument("Invalid financial values.");
        }

        if (!isfinite(confidence) ||
            confidence <= 0.0 ||
            confidence > 1.0) {
            throw invalid_argument("Invalid confidence factor.");
        }

        if (!isfinite(realizedBenefit) || realizedBenefit < 0.0) {
            throw invalid_argument("Invalid realized benefit.");
        }
    }

    double emv() const {
        return probability * impact;
    }

    double netExpectedValue() const {
        return emv() - responseCost;
    }

    double adjustedValue() const {
        return netExpectedValue() * confidence;
    }
};

class OpportunityEngine {
private:
    map<string, Opportunity> opportunities;

    Opportunity& get(const string& id) {
        auto it = opportunities.find(id);

        if (it == opportunities.end()) {
            throw out_of_range("Opportunity not found: " + id);
        }

        return it->second;
    }

public:
    void add(Opportunity opportunity) {
        opportunity.validate();

        if (opportunities.count(opportunity.id)) {
            throw invalid_argument("Duplicate opportunity ID.");
        }

        opportunities.emplace(opportunity.id, move(opportunity));
    }

    void assess(const string& id) {
        Opportunity& opportunity = get(id);

        if (opportunity.status != Status::Identified) {
            throw logic_error("Invalid assessment transition.");
        }

        opportunity.validate();
        opportunity.status = Status::Assessed;
    }

    void plan(const string& id, const string& action) {
        Opportunity& opportunity = get(id);

        if (opportunity.status != Status::Identified &&
            opportunity.status != Status::Assessed) {
            throw logic_error("Response planning not permitted.");
        }

        if (action.empty()) {
            throw invalid_argument("Response action cannot be empty.");
        }

        opportunity.responseAction = action;
        opportunity.status = Status::Planned;
    }

    void execute(const string& id) {
        Opportunity& opportunity = get(id);

        if (opportunity.status != Status::Planned) {
            throw logic_error("Opportunity has no approved response plan.");
        }

        opportunity.status = Status::InProgress;
    }

    void realize(const string& id, double benefit) {
        Opportunity& opportunity = get(id);

        if (opportunity.status != Status::InProgress) {
            throw logic_error("Opportunity is not in progress.");
        }

        if (!isfinite(benefit) || benefit < 0.0) {
            throw invalid_argument("Invalid realized benefit.");
        }

        opportunity.realizedBenefit = benefit;
        opportunity.status = Status::Realized;
    }

    void close(const string& id) {
        Opportunity& opportunity = get(id);

        if (opportunity.status != Status::Identified &&
            opportunity.status != Status::Assessed &&
            opportunity.status != Status::Realized) {
            throw logic_error("Opportunity cannot be closed.");
        }

        opportunity.status = Status::Closed;
    }

    vector<Opportunity> ranked() const {
        vector<Opportunity> result;

        for (const auto& [id, opportunity] : opportunities) {
            result.push_back(opportunity);
        }

        // Stable sorting provides deterministic tie handling.
        stable_sort(
            result.begin(),
            result.end(),
            [](const Opportunity& a, const Opportunity& b) {
                return a.adjustedValue() > b.adjustedValue();
            }
        );

        return result;
    }

    void report() const {
        double totalEMV = 0;
        double totalCost = 0;
        double totalRealized = 0;

        map<Status, int> statusCount;

        for (const auto& [id, opportunity] : opportunities) {
            totalEMV += opportunity.emv();
            totalCost += opportunity.responseCost;
            totalRealized += opportunity.realizedBenefit;
            statusCount[opportunity.status]++;
        }

        cout << "\nPORTFOLIO REPORT\n";
        cout << "-----------------------------\n";
        cout << "Opportunities: " << opportunities.size() << '\n';
        cout << "Expected value: " << totalEMV << '\n';
        cout << "Response costs: " << totalCost << '\n';
        cout << "Net expected value: "
             << totalEMV - totalCost << '\n';
        cout << "Realized benefits: " << totalRealized << '\n';

        cout << "\nSTATUS DISTRIBUTION\n";

        for (const auto& [status, count] : statusCount) {
            cout << toString(status) << ": " << count << '\n';
        }
    }

    void displayRanking() const {
        cout << "\nOPPORTUNITY PRIORITY REGISTER\n";
        cout << "----------------------------------------------------------\n";

        for (const Opportunity& opportunity : ranked()) {
            cout << left << setw(12) << opportunity.id
                 << setw(25) << opportunity.title
                 << "EMV: " << setw(12) << opportunity.emv()
                 << "Net: " << setw(12)
                 << opportunity.netExpectedValue()
                 << "Adjusted: " << opportunity.adjustedValue()
                 << '\n';
        }
    }
};

int main() {
    try {
        OpportunityEngine engine;

        engine.add({
            "OPP-001",
            "Process Automation",
            Category::Cost,
            0.85,
            200000,
            25000,
            0.95,
            "Project Manager",
            Strategy::Exploit
        });

        engine.add({
            "OPP-002",
            "Early Delivery",
            Category::Schedule,
            0.70,
            150000,
            15000,
            0.90,
            "Delivery Lead",
            Strategy::Enhance
        });

        engine.add({
            "OPP-003",
            "Strategic Partnership",
            Category::Strategic,
            0.60,
            300000,
            30000,
            0.85,
            "Business Director",
            Strategy::Share
        });

        engine.add({
            "OPP-004",
            "Cloud Optimization",
            Category::Technology,
            0.75,
            100000,
            0,
            0.95,
            "Cloud Architect",
            Strategy::Accept
        });

        engine.assess("OPP-001");

        engine.plan(
            "OPP-001",
            "Automate reporting and verify financial savings."
        );

        engine.execute("OPP-001");
        engine.realize("OPP-001", 175000);

        engine.displayRanking();
        engine.report();

        // Invalid state transitions are rejected.
        try {
            engine.execute("OPP-002");
        } catch (const logic_error& error) {
            cout << "\nExpected workflow rejection: "
                 << error.what() << '\n';
        }

        // Duplicate identifiers are rejected.
        try {
            engine.add({
                "OPP-001",
                "Duplicate",
                Category::Business,
                0.5,
                10000,
                0,
                1.0,
                "Owner",
                Strategy::Accept
            });
        } catch (const invalid_argument& error) {
            cout << "Expected validation rejection: "
                 << error.what() << '\n';
        }

    } catch (const exception& error) {
        cerr << "Application error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
