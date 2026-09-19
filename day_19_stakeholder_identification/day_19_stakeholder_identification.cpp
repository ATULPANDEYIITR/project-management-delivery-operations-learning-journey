/*
 * Stakeholder Identification: industry-style C++ case study.
 *
 * Scenario:
 * A public-service organization is developing a digital citizen-service
 * portal. The system must identify, classify, analyze, and monitor the
 * people, groups, organizations, suppliers, and regulators affected by the
 * initiative.
 *
 * The implementation demonstrates:
 * - stakeholder discovery
 * - stakeholder registers
 * - classes and enums
 * - validation
 * - power-interest analysis
 * - influence-impact analysis
 * - stakeholder salience
 * - RACI validation
 * - stakeholder relationship graphs
 * - BFS shortest-path analysis
 * - engagement-gap analysis
 * - dependency analysis
 * - scenario changes
 * - audit events
 * - reporting
 * - complexity considerations
 *
 * Compile:
 *   g++ -std=c++17 -O2 stakeholder_identification.cpp -o stakeholder_identification
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;


// =============================================================================
// 1. ENUMERATIONS
// =============================================================================

enum class StakeholderType {
    Internal,
    External
};

enum class RelationshipType {
    Supports,
    Opposes,
    DependsOn,
    Influences,
    ReportsTo,
    CollaboratesWith
};

enum class EngagementLevel {
    Unaware,
    Resistant,
    Neutral,
    Supportive,
    Leading
};


// =============================================================================
// 2. HELPER FUNCTIONS
// =============================================================================

string toString(StakeholderType type) {
    switch (type) {
        case StakeholderType::Internal:
            return "Internal";
        case StakeholderType::External:
            return "External";
    }

    return "Unknown";
}

string toString(RelationshipType type) {
    switch (type) {
        case RelationshipType::Supports:
            return "supports";
        case RelationshipType::Opposes:
            return "opposes";
        case RelationshipType::DependsOn:
            return "depends_on";
        case RelationshipType::Influences:
            return "influences";
        case RelationshipType::ReportsTo:
            return "reports_to";
        case RelationshipType::CollaboratesWith:
            return "collaborates_with";
    }

    return "unknown";
}

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

int engagementValue(EngagementLevel level) {
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


// =============================================================================
// 3. STAKEHOLDER MODEL
// =============================================================================

struct Stakeholder {
    string id;
    string name;
    StakeholderType type;
    string role;
    string organization;

    vector<string> interests;

    double power;
    double interest;
    double influence;
    double impact;

    double legitimacy;
    double urgency;

    EngagementLevel currentEngagement;
    EngagementLevel desiredEngagement;

    string communicationFrequency;

    void validate() const {
        if (id.empty() || name.empty()) {
            throw invalid_argument(
                "Stakeholder ID and name are required."
            );
        }

        const vector<pair<string, double>> scores = {
            {"power", power},
            {"interest", interest},
            {"influence", influence},
            {"impact", impact}
        };

        for (const auto& [field, value] : scores) {
            if (!isfinite(value) || value < 0.0 || value > 10.0) {
                throw invalid_argument(
                    field + " must be between 0 and 10."
                );
            }
        }

        if (!isfinite(legitimacy) ||
            legitimacy < 0.0 ||
            legitimacy > 1.0) {
            throw invalid_argument(
                "legitimacy must be between 0 and 1."
            );
        }

        if (!isfinite(urgency) ||
            urgency < 0.0 ||
            urgency > 1.0) {
            throw invalid_argument(
                "urgency must be between 0 and 1."
            );
        }
    }

    double powerInterestScore() const {
        return power * interest;
    }

    double influenceImpactScore() const {
        return influence * impact;
    }

    double salienceScore() const {
        return power * legitimacy * urgency;
    }

    string powerInterestCategory() const {
        if (power >= 5.0 && interest >= 5.0) {
            return "Manage closely";
        }

        if (power >= 5.0 && interest < 5.0) {
            return "Keep satisfied";
        }

        if (power < 5.0 && interest >= 5.0) {
            return "Keep informed";
        }

        return "Monitor";
    }

    int engagementGap() const {
        return (
            engagementValue(desiredEngagement) -
            engagementValue(currentEngagement)
        );
    }
};


// =============================================================================
// 4. RELATIONSHIP MODEL
// =============================================================================

struct Relationship {
    string source;
    string target;
    RelationshipType type;
    double strength;

    void validate() const {
        if (source.empty() || target.empty()) {
            throw invalid_argument(
                "Relationship endpoints cannot be empty."
            );
        }

        if (source == target) {
            throw invalid_argument(
                "Self-relationships are not allowed."
            );
        }

        if (strength <= 0.0 || strength > 1.0) {
            throw invalid_argument(
                "Relationship strength must be > 0 and <= 1."
            );
        }
    }
};


// =============================================================================
// 5. AUDIT EVENT
// =============================================================================

struct AuditEvent {
    string action;
    string stakeholderId;
    string description;
};


// =============================================================================
// 6. STAKEHOLDER REGISTER
// =============================================================================

class StakeholderRegister {
private:
    map<string, Stakeholder> stakeholders;
    vector<Relationship> relationships;
    vector<AuditEvent> auditLog;

public:
    void addStakeholder(const Stakeholder& stakeholder) {
        stakeholder.validate();

        if (stakeholders.contains(stakeholder.id)) {
            throw invalid_argument(
                "Duplicate stakeholder ID: " + stakeholder.id
            );
        }

        stakeholders.emplace(stakeholder.id, stakeholder);

        auditLog.push_back({
            "ADD_STAKEHOLDER",
            stakeholder.id,
            "Stakeholder added to register."
        });
    }

    Stakeholder& get(const string& id) {
        auto iterator = stakeholders.find(id);

        if (iterator == stakeholders.end()) {
            throw out_of_range(
                "Unknown stakeholder: " + id
            );
        }

        return iterator->second;
    }

    const Stakeholder& get(const string& id) const {
        auto iterator = stakeholders.find(id);

        if (iterator == stakeholders.end()) {
            throw out_of_range(
                "Unknown stakeholder: " + id
            );
        }

        return iterator->second;
    }

    const map<string, Stakeholder>& all() const {
        return stakeholders;
    }

    void addRelationship(const Relationship& relationship) {
        relationship.validate();

        get(relationship.source);
        get(relationship.target);

        relationships.push_back(relationship);

        auditLog.push_back({
            "ADD_RELATIONSHIP",
            relationship.source,
            "Relationship added to " + relationship.target
        });
    }

    const vector<Relationship>& getRelationships() const {
        return relationships;
    }

    const vector<AuditEvent>& getAuditLog() const {
        return auditLog;
    }

    void updatePower(
        const string& stakeholderId,
        double newPower
    ) {
        Stakeholder& stakeholder = get(stakeholderId);

        if (newPower < 0.0 || newPower > 10.0) {
            throw invalid_argument(
                "New power must be between 0 and 10."
            );
        }

        const double oldPower = stakeholder.power;
        stakeholder.power = newPower;

        auditLog.push_back({
            "UPDATE_POWER",
            stakeholderId,
            "Power changed from " +
                to_string(oldPower) +
                " to " +
                to_string(newPower)
        });
    }
};


// =============================================================================
// 7. INDUSTRY CASE STUDY
// =============================================================================

StakeholderRegister createRegister() {
    StakeholderRegister registerData;

    registerData.addStakeholder({
        "S01",
        "Executive Sponsor",
        StakeholderType::Internal,
        "Sponsor",
        "Public Service Department",
        {"Strategy", "Budget", "Accountability"},
        9, 7, 9, 8,
        1.0, 1.0,
        EngagementLevel::Supportive,
        EngagementLevel::Leading,
        "Weekly"
    });

    registerData.addStakeholder({
        "S02",
        "Project Manager",
        StakeholderType::Internal,
        "Project Manager",
        "Public Service Department",
        {"Delivery", "Schedule", "Risk", "Coordination"},
        7, 10, 8, 9,
        1.0, 1.0,
        EngagementLevel::Leading,
        EngagementLevel::Leading,
        "Weekly"
    });

    registerData.addStakeholder({
        "S03",
        "IT Operations",
        StakeholderType::Internal,
        "Operations",
        "Public Service Department",
        {"Reliability", "Maintainability", "Security"},
        7, 8, 8, 9,
        1.0, 1.0,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        "Weekly"
    });

    registerData.addStakeholder({
        "S04",
        "Frontline Employees",
        StakeholderType::Internal,
        "Service Staff",
        "Public Service Department",
        {"Usability", "Workload", "Training"},
        5, 9, 6, 9,
        1.0, 1.0,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        "Biweekly"
    });

    registerData.addStakeholder({
        "S05",
        "Citizens",
        StakeholderType::External,
        "End Users",
        "Public",
        {"Accessibility", "Privacy", "Service Quality"},
        5, 10, 7, 10,
        1.0, 1.0,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        "Monthly"
    });

    registerData.addStakeholder({
        "S06",
        "Technology Supplier",
        StakeholderType::External,
        "Vendor",
        "External Supplier",
        {"Contract Performance", "Commercial Outcome"},
        6, 7, 7, 7,
        1.0, 1.0,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        "Weekly"
    });

    registerData.addStakeholder({
        "S07",
        "Data Protection Authority",
        StakeholderType::External,
        "Regulator",
        "Government",
        {"Privacy", "Lawful Processing", "Security"},
        9, 6, 10, 9,
        1.0, 1.0,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        "As required"
    });

    registerData.addStakeholder({
        "S08",
        "Accessibility Advocates",
        StakeholderType::External,
        "Community Representative",
        "Civil Society",
        {"Inclusive Design", "Accessibility"},
        4, 8, 6, 8,
        1.0, 1.0,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        "Monthly"
    });

    registerData.addStakeholder({
        "S09",
        "Finance Department",
        StakeholderType::Internal,
        "Budget Controller",
        "Public Service Department",
        {"Cost Control", "Budget Compliance"},
        7, 5, 7, 6,
        1.0, 1.0,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        "Monthly"
    });

    registerData.addStakeholder({
        "S10",
        "Cybersecurity Team",
        StakeholderType::Internal,
        "Security",
        "Public Service Department",
        {"Threat Reduction", "Security Controls"},
        8, 8, 9, 10,
        1.0, 1.0,
        EngagementLevel::Supportive,
        EngagementLevel::Leading,
        "Weekly"
    });

    registerData.addRelationship({
        "S01", "S02",
        RelationshipType::Supports,
        0.9
    });

    registerData.addRelationship({
        "S02", "S03",
        RelationshipType::CollaboratesWith,
        0.9
    });

    registerData.addRelationship({
        "S02", "S04",
        RelationshipType::CollaboratesWith,
        0.8
    });

    registerData.addRelationship({
        "S02", "S06",
        RelationshipType::CollaboratesWith,
        0.8
    });

    registerData.addRelationship({
        "S07", "S10",
        RelationshipType::Influences,
        0.9
    });

    registerData.addRelationship({
        "S10", "S03",
        RelationshipType::Influences,
        0.9
    });

    registerData.addRelationship({
        "S05", "S02",
        RelationshipType::Influences,
        0.6
    });

    registerData.addRelationship({
        "S08", "S02",
        RelationshipType::Influences,
        0.5
    });

    registerData.addRelationship({
        "S09", "S01",
        RelationshipType::ReportsTo,
        0.7
    });

    registerData.addRelationship({
        "S06", "S03",
        RelationshipType::DependsOn,
        0.8
    });

    return registerData;
}


// =============================================================================
// 8. POWER-INTEREST REPORT
// =============================================================================

void printPowerInterestReport(
    const StakeholderRegister& registerData
) {
    cout << "\nPOWER-INTEREST REPORT\n";

    map<string, vector<string>> categories;

    for (const auto& [id, stakeholder] : registerData.all()) {
        categories[
            stakeholder.powerInterestCategory()
        ].push_back(stakeholder.name);
    }

    for (const auto& [category, names] : categories) {
        cout << "\n" << category << ":\n";

        for (const string& name : names) {
            cout << "  - " << name << "\n";
        }
    }
}


// =============================================================================
// 9. MULTI-MODEL PRIORITIZATION
// =============================================================================

double weightedPriorityScore(
    const Stakeholder& stakeholder
) {
    return (
        0.25 * stakeholder.power +
        0.20 * stakeholder.interest +
        0.20 * stakeholder.influence +
        0.20 * stakeholder.impact +
        0.15 * stakeholder.legitimacy * 10.0
    );
}

string salienceClass(
    const Stakeholder& stakeholder
) {
    int attributes = 0;

    if (stakeholder.power >= 5.0) {
        ++attributes;
    }

    if (stakeholder.legitimacy >= 0.5) {
        ++attributes;
    }

    if (stakeholder.urgency >= 0.5) {
        ++attributes;
    }

    if (attributes == 3) {
        return "Definitive";
    }

    if (attributes == 2) {
        return "Expectant";
    }

    if (attributes == 1) {
        return "Latent";
    }

    return "Low salience";
}

void printPriorityReport(
    const StakeholderRegister& registerData
) {
    vector<const Stakeholder*> stakeholders;

    for (const auto& [id, stakeholder] : registerData.all()) {
        stakeholders.push_back(&stakeholder);
    }

    sort(
        stakeholders.begin(),
        stakeholders.end(),
        [](const Stakeholder* a, const Stakeholder* b) {
            return weightedPriorityScore(*a) >
                   weightedPriorityScore(*b);
        }
    );

    cout << "\nMULTI-MODEL ANALYSIS\n";

    for (const Stakeholder* stakeholder : stakeholders) {
        cout << fixed << setprecision(2)
             << "- " << stakeholder->name
             << ": power-interest="
             << stakeholder->powerInterestScore()
             << ", influence-impact="
             << stakeholder->influenceImpactScore()
             << ", salience="
             << stakeholder->salienceScore()
             << ", weighted="
             << weightedPriorityScore(*stakeholder)
             << ", class="
             << salienceClass(*stakeholder)
             << "\n";
    }
}


// =============================================================================
// 10. STAKEHOLDER GRAPH
// =============================================================================

class StakeholderGraph {
private:
    unordered_map<string, vector<string>> adjacency;

public:
    explicit StakeholderGraph(
        const StakeholderRegister& registerData
    ) {
        for (const auto& [id, stakeholder] : registerData.all()) {
            adjacency[id];
        }

        for (const Relationship& relationship :
             registerData.getRelationships()) {
            adjacency[relationship.source].push_back(
                relationship.target
            );
        }
    }

    vector<string> shortestPath(
        const string& source,
        const string& target
    ) const {
        if (!adjacency.contains(source) ||
            !adjacency.contains(target)) {
            return {};
        }

        queue<string> pending;
        unordered_map<string, string> previous;
        unordered_set<string> visited;

        pending.push(source);
        visited.insert(source);

        while (!pending.empty()) {
            string current = pending.front();
            pending.pop();

            if (current == target) {
                break;
            }

            auto iterator = adjacency.find(current);

            if (iterator == adjacency.end()) {
                continue;
            }

            for (const string& neighbor : iterator->second) {
                if (visited.contains(neighbor)) {
                    continue;
                }

                visited.insert(neighbor);
                previous[neighbor] = current;
                pending.push(neighbor);
            }
        }

        if (!visited.contains(target)) {
            return {};
        }

        vector<string> path;
        string current = target;

        path.push_back(current);

        while (current != source) {
            auto iterator = previous.find(current);

            if (iterator == previous.end()) {
                return {};
            }

            current = iterator->second;
            path.push_back(current);
        }

        reverse(path.begin(), path.end());
        return path;
    }

    size_t outgoingDegree(const string& id) const {
        auto iterator = adjacency.find(id);

        if (iterator == adjacency.end()) {
            return 0;
        }

        return iterator->second.size();
    }
};


// =============================================================================
// 11. RACI MODEL
// =============================================================================

using RaciAssignment = map<string, char>;
using RaciMatrix = map<string, RaciAssignment>;

vector<string> validateRaci(
    const RaciMatrix& matrix
) {
    vector<string> errors;

    for (const auto& [activity, assignments] : matrix) {
        int accountableCount = 0;

        for (const auto& [stakeholder, role] : assignments) {
            if (role != 'R' &&
                role != 'A' &&
                role != 'C' &&
                role != 'I') {
                errors.push_back(
                    activity +
                    ": invalid RACI role for " +
                    stakeholder
                );
            }

            if (role == 'A') {
                ++accountableCount;
            }
        }

        if (accountableCount == 0) {
            errors.push_back(
                activity + ": no accountable stakeholder."
            );
        }

        if (accountableCount > 1) {
            errors.push_back(
                activity +
                ": multiple accountable stakeholders."
            );
        }
    }

    return errors;
}


// =============================================================================
// 12. ENGAGEMENT REPORT
// =============================================================================

void printEngagementReport(
    const StakeholderRegister& registerData
) {
    cout << "\nENGAGEMENT GAP REPORT\n";

    for (const auto& [id, stakeholder] : registerData.all()) {
        const int gap = stakeholder.engagementGap();

        string action;

        if (gap <= 0) {
            action = "Maintain or monitor.";
        } else if (gap == 1) {
            action = "Targeted communication and participation.";
        } else if (gap == 2) {
            action = "Structured consultation and issue management.";
        } else {
            action = "Intensive engagement and change management.";
        }

        cout << "- " << stakeholder.name
             << ": "
             << toString(stakeholder.currentEngagement)
             << " -> "
             << toString(stakeholder.desiredEngagement)
             << ", gap=" << gap
             << ", action=" << action
             << "\n";
    }
}


// =============================================================================
// 13. PROCESS-BASED STAKEHOLDER DISCOVERY
// =============================================================================

struct ProcessStep {
    string name;
    string actor;
    string owner;
    string customer;
    string approver;
    string supplier;
    string systemOwner;
    vector<string> reviewers;
};

set<string> discoverFromProcess(
    const vector<ProcessStep>& steps
) {
    set<string> discovered;

    for (const ProcessStep& step : steps) {
        const vector<string> fields = {
            step.actor,
            step.owner,
            step.customer,
            step.approver,
            step.supplier,
            step.systemOwner
        };

        for (const string& field : fields) {
            if (!field.empty()) {
                discovered.insert(field);
            }
        }

        for (const string& reviewer : step.reviewers) {
            if (!reviewer.empty()) {
                discovered.insert(reviewer);
            }
        }
    }

    return discovered;
}


// =============================================================================
// 14. DEPENDENCY ANALYSIS
// =============================================================================

map<string, vector<string>> dependencyMap(
    const StakeholderRegister& registerData
) {
    map<string, vector<string>> result;

    for (const Relationship& relationship :
         registerData.getRelationships()) {
        if (relationship.type != RelationshipType::DependsOn) {
            continue;
        }

        const string source =
            registerData.get(relationship.source).name;

        const string target =
            registerData.get(relationship.target).name;

        result[source].push_back(target);
    }

    return result;
}


// =============================================================================
// 15. SCENARIO ANALYSIS
// =============================================================================

string categoryForScores(
    double power,
    double interest
) {
    if (power >= 5.0 && interest >= 5.0) {
        return "Manage closely";
    }

    if (power >= 5.0) {
        return "Keep satisfied";
    }

    if (interest >= 5.0) {
        return "Keep informed";
    }

    return "Monitor";
}

void simulateScopeChange(
    const StakeholderRegister& registerData,
    const set<string>& changedIds,
    double powerDelta
) {
    cout << "\nSCOPE-CHANGE SIMULATION\n";

    for (const auto& [id, stakeholder] : registerData.all()) {
        const bool changed =
            changedIds.contains(id);

        const double newPower =
            max(
                0.0,
                min(
                    10.0,
                    stakeholder.power +
                    (changed ? powerDelta : 0.0)
                )
            );

        const string oldCategory =
            stakeholder.powerInterestCategory();

        const string newCategory =
            categoryForScores(
                newPower,
                stakeholder.interest
            );

        if (oldCategory != newCategory) {
            cout << "- "
                 << stakeholder.name
                 << ": "
                 << oldCategory
                 << " -> "
                 << newCategory
                 << "\n";
        }
    }
}


// =============================================================================
// 16. SYSTEM VALIDATION
// =============================================================================

void validateRegister(
    const StakeholderRegister& registerData
) {
    cout << "\nREGISTER VALIDATION\n";

    bool valid = true;

    for (const auto& [id, stakeholder] :
         registerData.all()) {
        try {
            stakeholder.validate();
        } catch (const exception& error) {
            valid = false;
            cout << "- " << id
                 << ": "
                 << error.what()
                 << "\n";
        }
    }

    for (const Relationship& relationship :
         registerData.getRelationships()) {
        try {
            relationship.validate();
            registerData.get(relationship.source);
            registerData.get(relationship.target);
        } catch (const exception& error) {
            valid = false;
            cout << "- Relationship error: "
                 << error.what()
                 << "\n";
        }
    }

    if (valid) {
        cout << "Register passed structural validation.\n";
    }
}


// =============================================================================
// 17. REPORTING
// =============================================================================

void printRegister(
    const StakeholderRegister& registerData
) {
    cout << "\nSTAKEHOLDER REGISTER\n";

    cout << left
         << setw(6) << "ID"
         << setw(28) << "Name"
         << setw(11) << "Type"
         << right
         << setw(8) << "Power"
         << setw(10) << "Interest"
         << setw(12) << "Influence"
         << "\n";

    cout << string(75, '-') << "\n";

    for (const auto& [id, stakeholder] :
         registerData.all()) {
        cout << left
             << setw(6) << stakeholder.id
             << setw(28) << stakeholder.name
             << setw(11) << toString(stakeholder.type)
             << right
             << setw(8) << fixed << setprecision(1)
             << stakeholder.power
             << setw(10)
             << stakeholder.interest
             << setw(12)
             << stakeholder.influence
             << "\n";
    }
}


// =============================================================================
// 18. TESTS
// =============================================================================

void runTests() {
    cout << "\nRUNNING TESTS\n";

    Stakeholder valid {
        "T01",
        "Test Stakeholder",
        StakeholderType::Internal,
        "Tester",
        "Test Organization",
        {"Testing"},
        8, 7, 6, 5,
        1.0, 1.0,
        EngagementLevel::Neutral,
        EngagementLevel::Supportive,
        "Monthly"
    };

    valid.validate();

    if (valid.powerInterestScore() != 56.0) {
        throw runtime_error(
            "Power-interest calculation failed."
        );
    }

    if (valid.powerInterestCategory() !=
        "Manage closely") {
        throw runtime_error(
            "Power-interest classification failed."
        );
    }

    if (valid.influenceImpactScore() != 30.0) {
        throw runtime_error(
            "Influence-impact calculation failed."
        );
    }

    if (valid.engagementGap() != 1) {
        throw runtime_error(
            "Engagement gap calculation failed."
        );
    }

    try {
        Stakeholder invalid = valid;
        invalid.power = 20;
        invalid.validate();

        throw runtime_error(
            "Invalid stakeholder was accepted."
        );
    } catch (const invalid_argument&) {
        // Expected failure.
    }

    StakeholderRegister registerData;

    registerData.addStakeholder(valid);

    try {
        registerData.addStakeholder(valid);

        throw runtime_error(
            "Duplicate stakeholder was accepted."
        );
    } catch (const invalid_argument&) {
        // Expected failure.
    }

    RaciMatrix raci = {
        {
            "Requirements",
            {
                {"Project Manager", 'A'},
                {"Users", 'C'}
            }
        },
        {
            "Security Review",
            {
                {"Security Team", 'R'},
                {"Project Manager", 'A'}
            }
        }
    };

    const vector<string> errors =
        validateRaci(raci);

    if (!errors.empty()) {
        throw runtime_error(
            "Valid RACI matrix was rejected."
        );
    }

    cout << "All tests passed.\n";
}


// =============================================================================
// 19. MAIN
// =============================================================================

int main() {
    try {
        cout << string(78, '=') << "\n";
        cout << "STAKEHOLDER IDENTIFICATION: C++ CASE STUDY\n";
        cout << string(78, '=') << "\n";

        cout << "\nCASE STUDY\n";
        cout << "A public-service department is developing a digital "
             << "citizen-service portal.\n";
        cout << "The objective is to identify affected and influential "
             << "stakeholders and create an auditable analytical model.\n";

        StakeholderRegister registerData =
            createRegister();

        printRegister(registerData);

        validateRegister(registerData);

        printPowerInterestReport(registerData);

        printPriorityReport(registerData);

        printEngagementReport(registerData);

        cout << "\nPROCESS-BASED DISCOVERY\n";

        vector<ProcessStep> processSteps = {
            {
                "Submit application",
                "Citizen",
                "Frontline Employees",
                "Citizen",
                "",
                "",
                "IT Operations",
                {"Accessibility Advocates"}
            },
            {
                "Validate identity",
                "Identity Service",
                "IT Operations",
                "",
                "Cybersecurity Team",
                "Technology Supplier",
                "IT Operations",
                {}
            },
            {
                "Review privacy controls",
                "Privacy Officer",
                "Cybersecurity Team",
                "",
                "Data Protection Authority",
                "",
                "",
                {}
            }
        };

        const set<string> discovered =
            discoverFromProcess(processSteps);

        for (const string& person : discovered) {
            cout << "- " << person << "\n";
        }

        cout << "\nDEPENDENCY ANALYSIS\n";

        const auto dependencies =
            dependencyMap(registerData);

        for (const auto& [source, targets] :
             dependencies) {
            cout << "- "
                 << source
                 << " depends on: ";

            for (size_t i = 0; i < targets.size(); ++i) {
                if (i > 0) {
                    cout << ", ";
                }

                cout << targets[i];
            }

            cout << "\n";
        }

        cout << "\nSTAKEHOLDER NETWORK\n";

        StakeholderGraph graph(registerData);

        const vector<string> path =
            graph.shortestPath("S07", "S03");

        cout << "Shortest relationship path S07 -> S03: ";

        if (path.empty()) {
            cout << "No path found.\n";
        } else {
            for (size_t i = 0; i < path.size(); ++i) {
                if (i > 0) {
                    cout << " -> ";
                }

                cout << path[i];
            }

            cout << "\n";
        }

        cout << "Outgoing degree of S02: "
             << graph.outgoingDegree("S02")
             << "\n";

        RaciMatrix raci = {
            {
                "Requirements",
                {
                    {"Project Manager", 'A'},
                    {"Frontline Employees", 'C'},
                    {"Citizens", 'C'},
                    {"IT Operations", 'C'},
                    {"Cybersecurity Team", 'C'},
                    {"Executive Sponsor", 'I'}
                }
            },
            {
                "Security Review",
                {
                    {"Cybersecurity Team", 'R'},
                    {"IT Operations", 'C'},
                    {"Project Manager", 'A'},
                    {"Data Protection Authority", 'C'},
                    {"Executive Sponsor", 'I'}
                }
            },
            {
                "User Acceptance",
                {
                    {"Citizens", 'R'},
                    {"Frontline Employees", 'R'},
                    {"Project Manager", 'A'},
                    {"IT Operations", 'C'},
                    {"Executive Sponsor", 'I'}
                }
            }
        };

        cout << "\nRACI VALIDATION\n";

        const vector<string> raciErrors =
            validateRaci(raci);

        if (raciErrors.empty()) {
            cout << "RACI matrix passed validation.\n";
        } else {
            for (const string& error : raciErrors) {
                cout << "- " << error << "\n";
            }
        }

        simulateScopeChange(
            registerData,
            {"S05", "S08"},
            2.0
        );

        cout << "\nAUDIT LOG\n";

        for (const AuditEvent& event :
             registerData.getAuditLog()) {
            cout << "- "
                 << event.action
                 << " | "
                 << event.stakeholderId
                 << " | "
                 << event.description
                 << "\n";
        }

        runTests();

        cout << "\nCOMPLEXITY NOTES\n";
        cout << "- Stakeholder lookup in std::map: O(log n).\n";
        cout << "- Register traversal: O(n).\n";
        cout << "- Power-interest classification: O(n).\n";
        cout << "- Relationship storage: O(r), where r is the number "
             << "of relationships.\n";
        cout << "- BFS shortest path: O(V + E) for an adjacency-list graph.\n";
        cout << "- Sorting stakeholders for prioritization: O(n log n).\n";

        cout << "\nIMPORTANT DESIGN TRADE-OFFS\n";
        cout << "- Numerical scores make comparisons easier but do not "
             << "eliminate judgment.\n";
        cout << "- A graph reveals relationships that a flat register "
             << "does not reveal.\n";
        cout << "- A detailed register improves traceability but increases "
             << "maintenance effort.\n";
        cout << "- High stakeholder priority does not automatically imply "
             << "that every stakeholder needs the same communication frequency.\n";
        cout << "- Stakeholder analysis should be reviewed when project "
             << "conditions materially change.\n";

        cout << "\nCASE STUDY COMPLETED SUCCESSFULLY.\n";

        return 0;
    }
    catch (const exception& error) {
        cerr << "\nFATAL ERROR: "
             << error.what()
             << "\n";

        return 1;
    }
}
