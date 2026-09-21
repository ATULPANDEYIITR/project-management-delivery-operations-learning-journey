/*
 * Stakeholder Analysis
 * =====================
 *
 * C++17 case study:
 * Digital Public-Service Transformation Program
 *
 * This program models a realistic stakeholder-analysis system for a
 * large digital transformation initiative.
 *
 * The implementation demonstrates:
 * - Stakeholder identification
 * - Stakeholder registers
 * - Power-interest mapping
 * - Influence-impact analysis
 * - Weighted prioritization
 * - Stakeholder salience
 * - Engagement gaps
 * - Communication planning
 * - Dependency analysis
 * - Conflict analysis
 * - Validation
 * - Sorting
 * - Hash-based lookup
 * - Graph-like relationships
 * - Complexity considerations
 * - Export-style reporting
 *
 * Compile:
 *     g++ -std=c++17 -O2 stakeholder_analysis.cpp -o stakeholder_analysis
 *
 * Run:
 *     ./stakeholder_analysis
 */

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;


// -----------------------------------------------------------------------------
// 1. ENUMERATIONS
// -----------------------------------------------------------------------------

enum class EngagementLevel {
    Unaware,
    Resistant,
    Neutral,
    Supportive,
    Leading
};

enum class StakeholderCategory {
    Internal,
    External
};

enum class StakeholderType {
    Primary,
    Secondary
};


// -----------------------------------------------------------------------------
// 2. ENUMERATION HELPERS
// -----------------------------------------------------------------------------

string toString(EngagementLevel level) {
    switch (level) {
        case EngagementLevel::Unaware:
            return "Unaware";
        case EngagementLevel::Resistant:
            return "Resistant";
        case EngagementLevel::Neutral:
            return "Neutral";
        case EngagementLevel::Supportive:
            return "Supportive";
        case EngagementLevel::Leading:
            return "Leading";
    }

    return "Unknown";
}

string toString(StakeholderCategory category) {
    return category == StakeholderCategory::Internal
        ? "Internal"
        : "External";
}

string toString(StakeholderType type) {
    return type == StakeholderType::Primary
        ? "Primary"
        : "Secondary";
}

int engagementRank(EngagementLevel level) {
    switch (level) {
        case EngagementLevel::Unaware:
            return 0;
        case EngagementLevel::Resistant:
            return 1;
        case EngagementLevel::Neutral:
            return 2;
        case EngagementLevel::Supportive:
            return 3;
        case EngagementLevel::Leading:
            return 4;
    }

    return 0;
}


// -----------------------------------------------------------------------------
// 3. STAKEHOLDER STRUCTURE
// -----------------------------------------------------------------------------

struct Stakeholder {
    string name;
    string role;

    StakeholderCategory category;
    StakeholderType type;

    double interest;
    double influence;
    double impact;
    double urgency;
    double legitimacy;

    EngagementLevel currentEngagement;
    EngagementLevel desiredEngagement;

    vector<string> interests;
    vector<string> concerns;
    vector<string> dependencies;

    string communicationPreference;

    double priorityScore() const {
        /*
         * Transparent weighted model:
         * influence 30%
         * interest  25%
         * impact    20%
         * urgency   15%
         * legitimacy 10%
         */
        return influence * 0.30
             + interest * 0.25
             + impact * 0.20
             + urgency * 0.15
             + legitimacy * 0.10;
    }

    double salienceScore() const {
        /*
         * Simplified salience model:
         * influence × legitimacy × urgency / 10
         *
         * This is an educational model rather than a universal
         * stakeholder-management formula.
         */
        return influence * legitimacy * urgency / 10.0;
    }

    string powerInterestQuadrant() const {
        const bool highPower = influence >= 6.0;
        const bool highInterest = interest >= 6.0;

        if (highPower && highInterest) {
            return "Manage closely";
        }

        if (highPower && !highInterest) {
            return "Keep satisfied";
        }

        if (!highPower && highInterest) {
            return "Keep informed";
        }

        return "Monitor";
    }

    string influenceImpactQuadrant() const {
        const bool highInfluence = influence >= 6.0;
        const bool highImpact = impact >= 6.0;

        if (highInfluence && highImpact) {
            return "High influence / High impact";
        }

        if (highInfluence) {
            return "High influence / Low impact";
        }

        if (highImpact) {
            return "Low influence / High impact";
        }

        return "Low influence / Low impact";
    }

    int engagementGap() const {
        return engagementRank(desiredEngagement)
             - engagementRank(currentEngagement);
    }

    string recommendedStrategy() const {
        const string quadrant = powerInterestQuadrant();

        if (quadrant == "Manage closely") {
            if (currentEngagement == EngagementLevel::Resistant) {
                return "Address concerns directly, involve in decisions, "
                       "and maintain frequent two-way communication.";
            }

            return "Involve in key decisions and provide frequent updates.";
        }

        if (quadrant == "Keep satisfied") {
            return "Provide decision-relevant information and prevent surprises.";
        }

        if (quadrant == "Keep informed") {
            return "Provide transparent updates and maintain feedback channels.";
        }

        return "Monitor changes and communicate when relevant.";
    }
};


// -----------------------------------------------------------------------------
// 4. VALIDATION
// -----------------------------------------------------------------------------

void validateRating(double value, const string& fieldName) {
    if (!isfinite(value) || value < 1.0 || value > 10.0) {
        throw invalid_argument(
            fieldName + " must be between 1 and 10."
        );
    }
}

void validateStakeholder(const Stakeholder& stakeholder) {
    if (stakeholder.name.empty()) {
        throw invalid_argument("Stakeholder name cannot be empty.");
    }

    if (stakeholder.role.empty()) {
        throw invalid_argument("Stakeholder role cannot be empty.");
    }

    validateRating(stakeholder.interest, "Interest");
    validateRating(stakeholder.influence, "Influence");
    validateRating(stakeholder.impact, "Impact");
    validateRating(stakeholder.urgency, "Urgency");
    validateRating(stakeholder.legitimacy, "Legitimacy");
}


// -----------------------------------------------------------------------------
// 5. STAKEHOLDER REGISTER
// -----------------------------------------------------------------------------

class StakeholderRegister {
private:
    /*
     * unordered_map gives expected O(1) average lookup by stakeholder name.
     * This is useful when a large organization contains hundreds or
     * thousands of stakeholder records.
     */
    unordered_map<string, Stakeholder> stakeholders;

public:
    void add(const Stakeholder& stakeholder) {
        validateStakeholder(stakeholder);

        auto result = stakeholders.emplace(
            stakeholder.name,
            stakeholder
        );

        if (!result.second) {
            throw runtime_error(
                "Duplicate stakeholder: " + stakeholder.name
            );
        }
    }

    void update(const Stakeholder& stakeholder) {
        validateStakeholder(stakeholder);

        auto iterator = stakeholders.find(stakeholder.name);

        if (iterator == stakeholders.end()) {
            throw runtime_error(
                "Cannot update missing stakeholder: " +
                stakeholder.name
            );
        }

        iterator->second = stakeholder;
    }

    void remove(const string& name) {
        if (stakeholders.erase(name) == 0) {
            throw runtime_error(
                "Stakeholder not found: " + name
            );
        }
    }

    const Stakeholder& get(const string& name) const {
        auto iterator = stakeholders.find(name);

        if (iterator == stakeholders.end()) {
            throw runtime_error(
                "Stakeholder not found: " + name
            );
        }

        return iterator->second;
    }

    Stakeholder& getMutable(const string& name) {
        auto iterator = stakeholders.find(name);

        if (iterator == stakeholders.end()) {
            throw runtime_error(
                "Stakeholder not found: " + name
            );
        }

        return iterator->second;
    }

    vector<Stakeholder> all() const {
        vector<Stakeholder> result;

        result.reserve(stakeholders.size());

        for (const auto& [name, stakeholder] : stakeholders) {
            result.push_back(stakeholder);
        }

        return result;
    }

    size_t size() const {
        return stakeholders.size();
    }
};


// -----------------------------------------------------------------------------
// 6. COMMUNICATION PLAN
// -----------------------------------------------------------------------------

struct CommunicationPlan {
    string stakeholderName;
    string objective;
    string channel;
    string frequency;
    string owner;
};

CommunicationPlan buildCommunicationPlan(
    const Stakeholder& stakeholder
) {
    CommunicationPlan plan;
    plan.stakeholderName = stakeholder.name;
    plan.owner = "Project Manager";

    const string quadrant = stakeholder.powerInterestQuadrant();

    if (quadrant == "Manage closely") {
        plan.frequency =
            "Weekly or more frequently during critical decisions";
        plan.channel =
            "Meeting + written decision record";
        plan.objective =
            "Maintain alignment and enable rapid decision-making";
    }
    else if (quadrant == "Keep satisfied") {
        plan.frequency =
            "Biweekly or at major decision points";
        plan.channel =
            "Executive update";
        plan.objective =
            "Maintain confidence and prevent unexpected escalation";
    }
    else if (quadrant == "Keep informed") {
        plan.frequency =
            "Weekly or biweekly";
        plan.channel =
            "Dashboard / newsletter / town hall";
        plan.objective =
            "Maintain transparency and collect feedback";
    }
    else {
        plan.frequency =
            "Monthly or milestone-based";
        plan.channel =
            "Targeted email";
        plan.objective =
            "Maintain awareness without unnecessary communication";
    }

    return plan;
}


// -----------------------------------------------------------------------------
// 7. POWER-INTEREST MATRIX
// -----------------------------------------------------------------------------

map<string, vector<string>> createPowerInterestMatrix(
    const StakeholderRegister& registerData
) {
    map<string, vector<string>> matrix = {
        {"Manage closely", {}},
        {"Keep satisfied", {}},
        {"Keep informed", {}},
        {"Monitor", {}}
    };

    for (const Stakeholder& stakeholder : registerData.all()) {
        matrix[stakeholder.powerInterestQuadrant()]
            .push_back(stakeholder.name);
    }

    return matrix;
}


// -----------------------------------------------------------------------------
// 8. CONFLICT MODEL
// -----------------------------------------------------------------------------

struct StakeholderConflict {
    string stakeholderA;
    string stakeholderB;
    string topic;
    int severity;
    string description;

    StakeholderConflict(
        string a,
        string b,
        string topicValue,
        int severityValue,
        string descriptionValue
    )
        : stakeholderA(move(a)),
          stakeholderB(move(b)),
          topic(move(topicValue)),
          severity(severityValue),
          description(move(descriptionValue)) {

        if (severity < 1 || severity > 10) {
            throw invalid_argument(
                "Conflict severity must be between 1 and 10."
            );
        }
    }
};

double conflictPriority(
    const StakeholderConflict& conflict,
    const Stakeholder& stakeholderA,
    const Stakeholder& stakeholderB
) {
    const double averageInfluence =
        (stakeholderA.influence + stakeholderB.influence) / 2.0;

    return conflict.severity * averageInfluence / 10.0;
}


// -----------------------------------------------------------------------------
// 9. DEPENDENCY GRAPH
// -----------------------------------------------------------------------------

map<string, int> findDependencyBottlenecks(
    const StakeholderRegister& registerData
) {
    map<string, int> dependencyCounts;

    for (const Stakeholder& stakeholder : registerData.all()) {
        for (const string& dependency : stakeholder.dependencies) {
            dependencyCounts[dependency]++;
        }
    }

    return dependencyCounts;
}


// -----------------------------------------------------------------------------
// 10. WEIGHTED SENSITIVITY ANALYSIS
// -----------------------------------------------------------------------------

struct Weights {
    double interest;
    double influence;
    double impact;
    double urgency;
    double legitimacy;

    double total() const {
        return interest
             + influence
             + impact
             + urgency
             + legitimacy;
    }
};

double weightedScore(
    const Stakeholder& stakeholder,
    const Weights& weights
) {
    if (abs(weights.total() - 1.0) > 1e-9) {
        throw invalid_argument(
            "Stakeholder-analysis weights must sum to 1.0."
        );
    }

    return stakeholder.interest * weights.interest
         + stakeholder.influence * weights.influence
         + stakeholder.impact * weights.impact
         + stakeholder.urgency * weights.urgency
         + stakeholder.legitimacy * weights.legitimacy;
}


// -----------------------------------------------------------------------------
// 11. REPORTING
// -----------------------------------------------------------------------------

void printStakeholderReport(
    const Stakeholder& stakeholder
) {
    cout << "\n" << string(78, '=') << "\n";
    cout << "STAKEHOLDER: " << stakeholder.name << "\n";
    cout << string(78, '=') << "\n";

    cout << "Role:                 " << stakeholder.role << "\n";
    cout << "Category:             "
         << toString(stakeholder.category) << "\n";
    cout << "Type:                 "
         << toString(stakeholder.type) << "\n";

    cout << fixed << setprecision(2);

    cout << "Interest:             "
         << stakeholder.interest << "/10\n";
    cout << "Influence:            "
         << stakeholder.influence << "/10\n";
    cout << "Impact:               "
         << stakeholder.impact << "/10\n";
    cout << "Urgency:              "
         << stakeholder.urgency << "/10\n";
    cout << "Legitimacy:           "
         << stakeholder.legitimacy << "/10\n";

    cout << "Priority score:       "
         << stakeholder.priorityScore() << "/10\n";

    cout << "Salience score:       "
         << stakeholder.salienceScore() << "\n";

    cout << "Power-interest:       "
         << stakeholder.powerInterestQuadrant() << "\n";

    cout << "Influence-impact:     "
         << stakeholder.influenceImpactQuadrant() << "\n";

    cout << "Current engagement:   "
         << toString(stakeholder.currentEngagement) << "\n";

    cout << "Desired engagement:   "
         << toString(stakeholder.desiredEngagement) << "\n";

    cout << "Engagement gap:       "
         << stakeholder.engagementGap() << "\n";

    cout << "Recommended strategy: "
         << stakeholder.recommendedStrategy() << "\n";
}


// -----------------------------------------------------------------------------
// 12. SAMPLE PROJECT DATA
// -----------------------------------------------------------------------------

StakeholderRegister createProjectRegister() {
    StakeholderRegister registerData;

    registerData.add({
        "Executive Sponsor",
        "Program sponsor",
        StakeholderCategory::Internal,
        StakeholderType::Primary,
        9, 10, 8, 8, 10,
        EngagementLevel::Supportive,
        EngagementLevel::Leading,
        {"Strategic outcomes", "Budget", "Benefits"},
        {"Schedule", "Return on investment"},
        {},
        "Executive meeting"
    });

    registerData.add({
        "Project Manager",
        "Delivery lead",
        StakeholderCategory::Internal,
        StakeholderType::Primary,
        10, 9, 10, 9, 10,
        EngagementLevel::Leading,
        EngagementLevel::Leading,
        {"Scope", "Schedule", "Quality"},
        {"Dependencies", "Resources"},
        {"Executive Sponsor", "IT Operations"},
        "Project dashboard"
    });

    registerData.add({
        "Finance Department",
        "Financial control",
        StakeholderCategory::Internal,
        StakeholderType::Primary,
        7, 8, 6, 6, 9,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        {"Cost control", "Forecast accuracy"},
        {"Budget overrun"},
        {"Project Manager"},
        "Financial review"
    });

    registerData.add({
        "IT Operations",
        "Platform operations",
        StakeholderCategory::Internal,
        StakeholderType::Primary,
        9, 8, 9, 8, 10,
        EngagementLevel::Supportive,
        EngagementLevel::Leading,
        {"Reliability", "Security", "Maintainability"},
        {"Operational load", "Integration"},
        {"Project Manager", "External Vendor"},
        "Technical workshop"
    });

    registerData.add({
        "Employees",
        "Internal users",
        StakeholderCategory::Internal,
        StakeholderType::Primary,
        8, 5, 9, 6, 10,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        {"Usability", "Training"},
        {"Learning curve", "Workflow changes"},
        {"Project Manager", "IT Operations"},
        "Town hall"
    });

    registerData.add({
        "Customers",
        "External service users",
        StakeholderCategory::External,
        StakeholderType::Primary,
        8, 6, 9, 7, 10,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        {"Service quality", "Availability"},
        {"Privacy", "Usability"},
        {"IT Operations"},
        "Survey / support channel"
    });

    registerData.add({
        "Regulator",
        "Regulatory oversight",
        StakeholderCategory::External,
        StakeholderType::Secondary,
        6, 9, 5, 8, 10,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        {"Compliance", "Consumer protection"},
        {"Non-compliance", "Reporting"},
        {"Legal Department"},
        "Formal submission"
    });

    registerData.add({
        "External Vendor",
        "Technology supplier",
        StakeholderCategory::External,
        StakeholderType::Primary,
        8, 7, 8, 7, 8,
        EngagementLevel::Supportive,
        EngagementLevel::Supportive,
        {"Contract delivery", "Service continuity"},
        {"Scope changes", "Payment"},
        {"Project Manager"},
        "Vendor meeting"
    });

    registerData.add({
        "Legal Department",
        "Legal review",
        StakeholderCategory::Internal,
        StakeholderType::Secondary,
        5, 7, 5, 7, 10,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        {"Contract validity", "Privacy"},
        {"Liability", "Regulatory exposure"},
        {"Project Manager"},
        "Legal review"
    });

    return registerData;
}


// -----------------------------------------------------------------------------
// 13. PRIORITY RANKING
// -----------------------------------------------------------------------------

vector<Stakeholder> rankedStakeholders(
    const StakeholderRegister& registerData
) {
    vector<Stakeholder> stakeholders = registerData.all();

    sort(
        stakeholders.begin(),
        stakeholders.end(),
        [](const Stakeholder& a, const Stakeholder& b) {
            return a.priorityScore() > b.priorityScore();
        }
    );

    return stakeholders;
}

void printPriorityRanking(
    const StakeholderRegister& registerData
) {
    cout << "\n" << string(78, '=') << "\n";
    cout << "PRIORITY RANKING\n";
    cout << string(78, '=') << "\n";

    cout << left
         << setw(6) << "Rank"
         << setw(25) << "Stakeholder"
         << setw(12) << "Influence"
         << setw(12) << "Interest"
         << setw(12) << "Priority"
         << "\n";

    cout << string(78, '-') << "\n";

    vector<Stakeholder> ranked =
        rankedStakeholders(registerData);

    int rank = 1;

    for (const Stakeholder& stakeholder : ranked) {
        cout << left
             << setw(6) << rank++
             << setw(25) << stakeholder.name
             << setw(12) << stakeholder.influence
             << setw(12) << stakeholder.interest
             << setw(12) << stakeholder.priorityScore()
             << "\n";
    }
}


// -----------------------------------------------------------------------------
// 14. CASE STUDY EXECUTION
// -----------------------------------------------------------------------------

void runCaseStudy() {
    cout << string(78, '=') << "\n";
    cout << "DIGITAL PUBLIC-SERVICE TRANSFORMATION\n";
    cout << "STAKEHOLDER ANALYSIS CASE STUDY\n";
    cout << string(78, '=') << "\n";

    /*
     * Scenario:
     *
     * An organization is replacing an older service platform with a
     * centralized digital platform. The program affects executives,
     * employees, customers, regulators, technology teams, finance,
     * legal staff, and external vendors.
     *
     * The objective of stakeholder analysis is not simply to rank people.
     * It is to understand relationships and design appropriate engagement.
     */
    StakeholderRegister registerData =
        createProjectRegister();

    cout << "\nStakeholders identified: "
         << registerData.size() << "\n";

    printStakeholderReport(
        registerData.get("Executive Sponsor")
    );

    printStakeholderReport(
        registerData.get("Customers")
    );

    // -------------------------------------------------------------------------
    // Power-interest matrix
    // -------------------------------------------------------------------------

    cout << "\n" << string(78, '=') << "\n";
    cout << "POWER-INTEREST MATRIX\n";
    cout << string(78, '=') << "\n";

    auto matrix = createPowerInterestMatrix(registerData);

    for (const auto& [quadrant, names] : matrix) {
        cout << left
             << setw(20)
             << quadrant
             << " | ";

        for (size_t i = 0; i < names.size(); ++i) {
            if (i > 0) {
                cout << ", ";
            }

            cout << names[i];
        }

        cout << "\n";
    }

    // -------------------------------------------------------------------------
    // Ranking
    // -------------------------------------------------------------------------

    printPriorityRanking(registerData);

    // -------------------------------------------------------------------------
    // Communication planning
    // -------------------------------------------------------------------------

    cout << "\n" << string(78, '=') << "\n";
    cout << "COMMUNICATION PLANS\n";
    cout << string(78, '=') << "\n";

    vector<Stakeholder> ranked =
        rankedStakeholders(registerData);

    for (size_t i = 0; i < min<size_t>(5, ranked.size()); ++i) {
        CommunicationPlan plan =
            buildCommunicationPlan(ranked[i]);

        cout << "\nStakeholder: " << plan.stakeholderName << "\n";
        cout << "Objective:   " << plan.objective << "\n";
        cout << "Channel:     " << plan.channel << "\n";
        cout << "Frequency:   " << plan.frequency << "\n";
        cout << "Owner:       " << plan.owner << "\n";
    }

    // -------------------------------------------------------------------------
    // Dependency analysis
    // -------------------------------------------------------------------------

    cout << "\n" << string(78, '=') << "\n";
    cout << "DEPENDENCY ANALYSIS\n";
    cout << string(78, '=') << "\n";

    auto dependencies =
        findDependencyBottlenecks(registerData);

    for (const auto& [name, count] : dependencies) {
        cout << name
             << " is referenced by "
             << count
             << " stakeholder(s).\n";
    }

    // -------------------------------------------------------------------------
    // Conflict analysis
    // -------------------------------------------------------------------------

    StakeholderConflict conflict(
        "Finance Department",
        "IT Operations",
        "Cost control versus technical reliability",
        6,
        "Finance may emphasize budget control while IT Operations "
        "may require additional investment to reduce operational risk."
    );

    const double conflictScore =
        conflictPriority(
            conflict,
            registerData.get(conflict.stakeholderA),
            registerData.get(conflict.stakeholderB)
        );

    cout << "\n" << string(78, '=') << "\n";
    cout << "CONFLICT ANALYSIS\n";
    cout << string(78, '=') << "\n";

    cout << "Participants: "
         << conflict.stakeholderA
         << " / "
         << conflict.stakeholderB
         << "\n";

    cout << "Topic:        "
         << conflict.topic
         << "\n";

    cout << "Severity:     "
         << conflict.severity
         << "/10\n";

    cout << "Priority:     "
         << fixed
         << setprecision(2)
         << conflictScore
         << "\n";

    // -------------------------------------------------------------------------
    // Sensitivity analysis
    // -------------------------------------------------------------------------

    cout << "\n" << string(78, '=') << "\n";
    cout << "SENSITIVITY ANALYSIS\n";
    cout << string(78, '=') << "\n";

    const Stakeholder& sponsor =
        registerData.get("Executive Sponsor");

    const Weights balanced{
        0.25,  // interest
        0.30,  // influence
        0.20,  // impact
        0.15,  // urgency
        0.10   // legitimacy
    };

    const Weights riskFocused{
        0.15,
        0.30,
        0.25,
        0.20,
        0.10
    };

    const Weights impactFocused{
        0.20,
        0.20,
        0.35,
        0.15,
        0.10
    };

    cout << "Balanced:       "
         << weightedScore(sponsor, balanced)
         << "/10\n";

    cout << "Risk-focused:   "
         << weightedScore(sponsor, riskFocused)
         << "/10\n";

    cout << "Impact-focused: "
         << weightedScore(sponsor, impactFocused)
         << "/10\n";

    // -------------------------------------------------------------------------
    // Engagement update
    // -------------------------------------------------------------------------

    cout << "\n" << string(78, '=') << "\n";
    cout << "ENGAGEMENT UPDATE\n";
    cout << string(78, '=') << "\n";

    Stakeholder& employees =
        registerData.getMutable("Employees");

    cout << "Before: "
         << toString(employees.currentEngagement)
         << "\n";

    employees.currentEngagement =
        EngagementLevel::Supportive;

    cout << "After:  "
         << toString(employees.currentEngagement)
         << "\n";

    cout << "New engagement gap: "
         << employees.engagementGap()
         << "\n";

    // -------------------------------------------------------------------------
    // Edge cases
    // -------------------------------------------------------------------------

    cout << "\n" << string(78, '=') << "\n";
    cout << "EDGE CASES AND FAILURE CONDITIONS\n";
    cout << string(78, '=') << "\n";

    try {
        Stakeholder invalid{
            "Invalid Stakeholder",
            "Test",
            StakeholderCategory::Internal,
            StakeholderType::Primary,
            11, 5, 5, 5, 5,
            EngagementLevel::Neutral,
            EngagementLevel::Supportive,
            {},
            {},
            {},
            "Email"
        };

        registerData.add(invalid);
    }
    catch (const exception& error) {
        cout << "Invalid rating rejected: "
             << error.what()
             << "\n";
    }

    try {
        registerData.add(
            registerData.get("Customers")
        );
    }
    catch (const exception& error) {
        cout << "Duplicate rejected: "
             << error.what()
             << "\n";
    }

    try {
        const Weights invalidWeights{
            0.50,
            0.50,
            0.10,
            0.10,
            0.10
        };

        weightedScore(
            sponsor,
            invalidWeights
        );
    }
    catch (const exception& error) {
        cout << "Invalid weights rejected: "
             << error.what()
             << "\n";
    }
}


// -----------------------------------------------------------------------------
// 15. TESTS
// -----------------------------------------------------------------------------

void runTests() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "TESTS\n";
    cout << string(78, '=') << "\n";

    Stakeholder stakeholder{
        "Test Sponsor",
        "Sponsor",
        StakeholderCategory::Internal,
        StakeholderType::Primary,
        9, 9, 8, 8, 10,
        EngagementLevel::Neutral,
        EngagementLevel::Leading,
        {},
        {},
        {},
        "Meeting"
    };

    validateStakeholder(stakeholder);

    assert(
        stakeholder.powerInterestQuadrant()
        == "Manage closely"
    );

    assert(
        stakeholder.influenceImpactQuadrant()
        == "High influence / High impact"
    );

    assert(stakeholder.engagementGap() == 2);
    assert(stakeholder.priorityScore() > 8.0);

    StakeholderRegister registerData;

    registerData.add(stakeholder);

    assert(registerData.size() == 1);
    assert(
        registerData.get("Test Sponsor").name
        == "Test Sponsor"
    );

    const Weights weights{
        0.20,
        0.30,
        0.20,
        0.20,
        0.10
    };

    const double score =
        weightedScore(stakeholder, weights);

    assert(score >= 1.0);
    assert(score <= 10.0);

    bool duplicateRejected = false;

    try {
        registerData.add(stakeholder);
    }
    catch (const exception&) {
        duplicateRejected = true;
    }

    assert(duplicateRejected);

    bool invalidRejected = false;

    try {
        Stakeholder invalid = stakeholder;
        invalid.interest = 12;
        validateStakeholder(invalid);
    }
    catch (const exception&) {
        invalidRejected = true;
    }

    assert(invalidRejected);

    cout << "All tests passed.\n";
}


// -----------------------------------------------------------------------------
// 16. MAIN
// -----------------------------------------------------------------------------

int main() {
    try {
        runCaseStudy();
        runTests();

        cout << "\n" << string(78, '=') << "\n";
        cout << "C++ STAKEHOLDER ANALYSIS CASE STUDY COMPLETED\n";
        cout << string(78, '=') << "\n";

        return 0;
    }
    catch (const exception& error) {
        cerr << "Fatal error: "
             << error.what()
             << "\n";

        return 1;
    }
}
