/*
 * Scope Planning: Industry-Style Project Scope Management Case Study
 *
 * C++17 standard library only.
 *
 * The program models a project management system that maintains:
 *   - requirements
 *   - deliverables
 *   - work packages
 *   - acceptance criteria
 *   - scope baselines
 *   - change requests
 *   - traceability
 *   - validation
 *   - impact analysis
 *
 * The case study represents a small enterprise project-management platform.
 */

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

// -----------------------------------------------------------------------------
// 1. OUTPUT UTILITIES
// -----------------------------------------------------------------------------

void section(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}

void subsection(const string& title) {
    cout << "\n" << string(78, '-') << "\n";
    cout << title << "\n";
    cout << string(78, '-') << "\n";
}

// -----------------------------------------------------------------------------
// 2. ENUMERATIONS
// -----------------------------------------------------------------------------

enum class Priority {
    Must,
    Should,
    Could,
    Wont
};

enum class ChangeStatus {
    Proposed,
    Analyzing,
    Approved,
    Rejected,
    Implemented
};

string priorityToString(Priority priority) {
    switch (priority) {
        case Priority::Must: return "Must";
        case Priority::Should: return "Should";
        case Priority::Could: return "Could";
        case Priority::Wont: return "Won't";
    }
    return "Unknown";
}

string changeStatusToString(ChangeStatus status) {
    switch (status) {
        case ChangeStatus::Proposed: return "Proposed";
        case ChangeStatus::Analyzing: return "Analyzing";
        case ChangeStatus::Approved: return "Approved";
        case ChangeStatus::Rejected: return "Rejected";
        case ChangeStatus::Implemented: return "Implemented";
    }
    return "Unknown";
}

// -----------------------------------------------------------------------------
// 3. REQUIREMENT
// -----------------------------------------------------------------------------

struct Requirement {
    string id;
    string description;
    Priority priority;
    string source;
    vector<string> acceptanceCriteria;

    bool isValid() const {
        return !id.empty()
            && !description.empty()
            && !source.empty()
            && !acceptanceCriteria.empty();
    }
};

// -----------------------------------------------------------------------------
// 4. DELIVERABLE
// -----------------------------------------------------------------------------

struct Deliverable {
    string id;
    string name;
    string description;
    vector<string> requirementIds;
    vector<string> acceptanceCriteria;
};

// -----------------------------------------------------------------------------
// 5. WORK PACKAGE
// -----------------------------------------------------------------------------

struct WorkPackage {
    string id;
    string name;
    string description;
    double estimatedHours;
    vector<string> deliverableIds;

    vector<string> validate() const {
        vector<string> errors;

        if (id.empty()) {
            errors.push_back("Missing WBS identifier.");
        }

        if (name.empty()) {
            errors.push_back("Missing work-package name.");
        }

        if (estimatedHours <= 0.0) {
            errors.push_back("Estimated effort must be positive.");
        }

        if (deliverableIds.empty()) {
            errors.push_back("No linked deliverables.");
        }

        return errors;
    }
};

// -----------------------------------------------------------------------------
// 6. SCOPE STATEMENT
// -----------------------------------------------------------------------------

struct ScopeStatement {
    string objective;
    vector<string> inclusions;
    vector<string> exclusions;
    vector<string> assumptions;
    vector<string> constraints;
};

// -----------------------------------------------------------------------------
// 7. CHANGE REQUEST
// -----------------------------------------------------------------------------

struct ChangeRequest {
    string id;
    string description;
    string reason;
    double estimatedHours;
    double costImpact;
    int scheduleImpactDays;
    ChangeStatus status = ChangeStatus::Proposed;

    double impactScore() const {
        return max(0.0, estimatedHours)
             + max(0.0, costImpact) / 100.0
             + max(0, scheduleImpactDays) * 8.0;
    }
};

// -----------------------------------------------------------------------------
// 8. SCOPE BASELINE
// -----------------------------------------------------------------------------

struct ScopeBaseline {
    string version;
    ScopeStatement scope;
    vector<Requirement> requirements;
    vector<Deliverable> deliverables;
    vector<WorkPackage> workPackages;
};

// -----------------------------------------------------------------------------
// 9. INTEGRATED SCOPE SYSTEM
// -----------------------------------------------------------------------------

class ScopeManagementSystem {
private:
    ScopeStatement scope;
    unordered_map<string, Requirement> requirements;
    unordered_map<string, Deliverable> deliverables;
    unordered_map<string, WorkPackage> workPackages;
    vector<ChangeRequest> changeRequests;
    optional<ScopeBaseline> baseline;

public:
    explicit ScopeManagementSystem(ScopeStatement statement)
        : scope(std::move(statement)) {}

    bool addRequirement(const Requirement& requirement) {
        if (!requirement.isValid()) {
            return false;
        }

        return requirements.emplace(requirement.id, requirement).second;
    }

    bool addDeliverable(const Deliverable& deliverable) {
        if (deliverable.id.empty()
            || deliverable.name.empty()
            || deliverable.requirementIds.empty()
            || deliverable.acceptanceCriteria.empty()) {
            return false;
        }

        return deliverables.emplace(
            deliverable.id,
            deliverable
        ).second;
    }

    bool addWorkPackage(const WorkPackage& package) {
        if (!package.validate().empty()) {
            return false;
        }

        return workPackages.emplace(
            package.id,
            package
        ).second;
    }

    bool createBaseline(const string& version) {
        if (version.empty()) {
            return false;
        }

        ScopeBaseline newBaseline;
        newBaseline.version = version;
        newBaseline.scope = scope;

        for (const auto& [id, requirement] : requirements) {
            newBaseline.requirements.push_back(requirement);
        }

        for (const auto& [id, deliverable] : deliverables) {
            newBaseline.deliverables.push_back(deliverable);
        }

        for (const auto& [id, package] : workPackages) {
            newBaseline.workPackages.push_back(package);
        }

        baseline = std::move(newBaseline);
        return true;
    }

    bool hasRequirement(const string& id) const {
        return requirements.find(id) != requirements.end();
    }

    bool hasDeliverable(const string& id) const {
        return deliverables.find(id) != deliverables.end();
    }

    vector<string> validateTraceability() const {
        vector<string> errors;

        for (const auto& [id, deliverable] : deliverables) {
            for (const string& requirementId : deliverable.requirementIds) {
                if (!hasRequirement(requirementId)) {
                    errors.push_back(
                        deliverable.id
                        + " references unknown requirement "
                        + requirementId
                    );
                }
            }
        }

        for (const auto& [id, package] : workPackages) {
            for (const string& deliverableId : package.deliverableIds) {
                if (!hasDeliverable(deliverableId)) {
                    errors.push_back(
                        package.id
                        + " references unknown deliverable "
                        + deliverableId
                    );
                }
            }
        }

        return errors;
    }

    double traceabilityCoverage() const {
        if (requirements.empty()) {
            return 100.0;
        }

        set<string> mapped;

        for (const auto& [id, deliverable] : deliverables) {
            for (const string& requirementId : deliverable.requirementIds) {
                mapped.insert(requirementId);
            }
        }

        size_t covered = 0;

        for (const auto& [id, requirement] : requirements) {
            if (mapped.count(id) > 0) {
                ++covered;
            }
        }

        return static_cast<double>(covered)
             / static_cast<double>(requirements.size())
             * 100.0;
    }

    double totalEffortHours() const {
        double total = 0.0;

        for (const auto& [id, package] : workPackages) {
            total += package.estimatedHours;
        }

        return total;
    }

    size_t requirementCount() const {
        return requirements.size();
    }

    size_t deliverableCount() const {
        return deliverables.size();
    }

    size_t workPackageCount() const {
        return workPackages.size();
    }

    const optional<ScopeBaseline>& getBaseline() const {
        return baseline;
    }

    void submitChange(ChangeRequest request) {
        if (request.id.empty()) {
            throw invalid_argument("Change request must have an identifier.");
        }

        if (request.estimatedHours < 0
            || request.costImpact < 0
            || request.scheduleImpactDays < 0) {
            throw invalid_argument(
                "Change impacts cannot be negative."
            );
        }

        request.status = ChangeStatus::Proposed;
        changeRequests.push_back(std::move(request));
    }

    bool analyzeChange(const string& changeId) {
        for (ChangeRequest& request : changeRequests) {
            if (request.id == changeId) {
                request.status = ChangeStatus::Analyzing;
                return true;
            }
        }

        return false;
    }

    bool approveChange(const string& changeId) {
        for (ChangeRequest& request : changeRequests) {
            if (request.id == changeId) {
                request.status = ChangeStatus::Approved;
                return true;
            }
        }

        return false;
    }

    bool rejectChange(const string& changeId) {
        for (ChangeRequest& request : changeRequests) {
            if (request.id == changeId) {
                request.status = ChangeStatus::Rejected;
                return true;
            }
        }

        return false;
    }

    optional<ChangeRequest> findChange(const string& changeId) const {
        for (const ChangeRequest& request : changeRequests) {
            if (request.id == changeId) {
                return request;
            }
        }

        return nullopt;
    }

    void printScope() const {
        cout << "Objective:\n  " << scope.objective << "\n";

        cout << "\nIncluded work:\n";
        for (const string& item : scope.inclusions) {
            cout << "  - " << item << "\n";
        }

        cout << "\nExcluded work:\n";
        for (const string& item : scope.exclusions) {
            cout << "  - " << item << "\n";
        }

        cout << "\nAssumptions:\n";
        for (const string& item : scope.assumptions) {
            cout << "  - " << item << "\n";
        }

        cout << "\nConstraints:\n";
        for (const string& item : scope.constraints) {
            cout << "  - " << item << "\n";
        }
    }

    void printRequirements() const {
        for (const auto& [id, requirement] : requirements) {
            cout << id
                 << " | "
                 << priorityToString(requirement.priority)
                 << " | "
                 << requirement.description
                 << "\n";
        }
    }

    void printDeliverables() const {
        for (const auto& [id, deliverable] : deliverables) {
            cout << id
                 << " | "
                 << deliverable.name
                 << " | requirements=";

            for (size_t i = 0;
                 i < deliverable.requirementIds.size();
                 ++i) {

                if (i > 0) {
                    cout << ", ";
                }

                cout << deliverable.requirementIds[i];
            }

            cout << "\n";
        }
    }
};

// -----------------------------------------------------------------------------
// 10. REQUIREMENT ACCEPTANCE EVALUATION
// -----------------------------------------------------------------------------

struct AcceptanceResult {
    bool accepted;
    vector<string> missingCriteria;
};

AcceptanceResult evaluateAcceptance(
    const vector<string>& completed,
    const vector<string>& required
) {
    set<string> completedSet(completed.begin(), completed.end());
    vector<string> missing;

    for (const string& criterion : required) {
        if (completedSet.count(criterion) == 0) {
            missing.push_back(criterion);
        }
    }

    return {
        missing.empty(),
        missing
    };
}

// -----------------------------------------------------------------------------
// 11. CHANGE IMPACT MODEL
// -----------------------------------------------------------------------------

struct ImpactAssessment {
    double effortHours;
    double costImpact;
    int scheduleDays;
    double compositeScore;
};

ImpactAssessment assessChange(const ChangeRequest& request) {
    return {
        request.estimatedHours,
        request.costImpact,
        request.scheduleImpactDays,
        request.impactScore()
    };
}

// -----------------------------------------------------------------------------
// 12. MAIN CASE STUDY
// -----------------------------------------------------------------------------

int main() {
    section("Scope Planning: Project Management Platform Case Study");

    cout << fixed << setprecision(1);

    // -------------------------------------------------------------------------
    // BUSINESS SCENARIO
    // -------------------------------------------------------------------------

    subsection("1. Business scenario");

    ScopeStatement statement{
        "Deliver a browser-based project management MVP for small teams.",
        {
            "Account creation and authentication",
            "Project dashboard",
            "Project search",
            "English user interface",
            "Basic project status tracking"
        },
        {
            "Native mobile applications",
            "Advanced financial accounting",
            "Third-party payroll processing",
            "Multi-language translation in the first release"
        },
        {
            "The organization will provide branding assets.",
            "Users will have internet access.",
            "The hosting environment will be available before acceptance testing."
        },
        {
            "The approved technology stack must be used.",
            "The first release has a fixed delivery date.",
            "The initial budget is limited."
        }
    };

    ScopeManagementSystem system(statement);

    system.printScope();

    // -------------------------------------------------------------------------
    // REQUIREMENTS
    // -------------------------------------------------------------------------

    subsection("2. Requirements");

    vector<Requirement> requirementList{
        {
            "REQ-001",
            "Users shall be able to create an account using an email address.",
            Priority::Must,
            "Business owner",
            {
                "Valid email registration succeeds.",
                "Duplicate email registration is rejected."
            }
        },
        {
            "REQ-002",
            "Users shall be able to sign in with their credentials.",
            Priority::Must,
            "Product owner",
            {
                "Valid credentials create a session.",
                "Invalid credentials are rejected."
            }
        },
        {
            "REQ-003",
            "The dashboard shall allow users to search projects by name.",
            Priority::Should,
            "Project manager",
            {
                "A matching project can be found by name."
            }
        },
        {
            "REQ-004",
            "The first release shall use English interface content.",
            Priority::Must,
            "Sponsor",
            {
                "All release screens have English labels."
            }
        }
    };

    for (const Requirement& requirement : requirementList) {
        if (!system.addRequirement(requirement)) {
            cerr << "Could not add requirement: "
                 << requirement.id << "\n";
            return 1;
        }
    }

    system.printRequirements();

    // -------------------------------------------------------------------------
    // DELIVERABLES
    // -------------------------------------------------------------------------

    subsection("3. Deliverables and requirement traceability");

    vector<Deliverable> deliverableList{
        {
            "DEL-001",
            "Authentication module",
            "Registration and sign-in capability.",
            {"REQ-001", "REQ-002"},
            {
                "Users can register.",
                "Valid users can sign in."
            }
        },
        {
            "DEL-002",
            "Project dashboard",
            "Dashboard showing project information.",
            {"REQ-003"},
            {
                "Dashboard displays project information."
            }
        },
        {
            "DEL-003",
            "English release",
            "English interface for the MVP.",
            {"REQ-004"},
            {
                "Release screens use English labels."
            }
        }
    };

    for (const Deliverable& deliverable : deliverableList) {
        if (!system.addDeliverable(deliverable)) {
            cerr << "Could not add deliverable: "
                 << deliverable.id << "\n";
            return 1;
        }
    }

    system.printDeliverables();

    // -------------------------------------------------------------------------
    // WBS
    // -------------------------------------------------------------------------

    subsection("4. Work Breakdown Structure");

    vector<WorkPackage> packages{
        {
            "1.1",
            "Authentication",
            "Implement registration and sign-in.",
            36.0,
            {"DEL-001"}
        },
        {
            "1.2",
            "Dashboard",
            "Implement project dashboard behavior.",
            48.0,
            {"DEL-002"}
        },
        {
            "1.3",
            "Acceptance testing",
            "Execute acceptance tests for the MVP.",
            28.0,
            {"DEL-001", "DEL-002", "DEL-003"}
        }
    };

    for (const WorkPackage& package : packages) {
        const vector<string> errors = package.validate();

        if (!errors.empty()) {
            cerr << "Invalid work package: " << package.id << "\n";

            for (const string& error : errors) {
                cerr << "  " << error << "\n";
            }

            return 1;
        }

        if (!system.addWorkPackage(package)) {
            cerr << "Could not add work package: "
                 << package.id << "\n";
            return 1;
        }
    }

    cout << "Work packages: "
         << system.workPackageCount()
         << "\n";

    cout << "Total effort: "
         << system.totalEffortHours()
         << " hours\n";

    // -------------------------------------------------------------------------
    // TRACEABILITY VALIDATION
    // -------------------------------------------------------------------------

    subsection("5. Traceability validation");

    const vector<string> traceabilityErrors =
        system.validateTraceability();

    if (traceabilityErrors.empty()) {
        cout << "Traceability validation passed.\n";
    } else {
        for (const string& error : traceabilityErrors) {
            cout << "ERROR: " << error << "\n";
        }
    }

    cout << "Requirement coverage: "
         << system.traceabilityCoverage()
         << "%\n";

    // -------------------------------------------------------------------------
    // BASELINE
    // -------------------------------------------------------------------------

    subsection("6. Scope baseline");

    if (!system.createBaseline("1.0")) {
        cerr << "Could not create baseline.\n";
        return 1;
    }

    if (system.getBaseline().has_value()) {
        const ScopeBaseline& baseline =
            system.getBaseline().value();

        cout << "Baseline version: "
             << baseline.version
             << "\n";

        cout << "Baseline requirements: "
             << baseline.requirements.size()
             << "\n";

        cout << "Baseline deliverables: "
             << baseline.deliverables.size()
             << "\n";

        cout << "Baseline work packages: "
             << baseline.workPackages.size()
             << "\n";
    }

    // -------------------------------------------------------------------------
    // ACCEPTANCE
    // -------------------------------------------------------------------------

    subsection("7. Acceptance testing");

    const vector<string> requiredAcceptance{
        "Valid email registration succeeds.",
        "Duplicate email registration is rejected."
    };

    const vector<string> completedAcceptance{
        "Valid email registration succeeds."
    };

    const AcceptanceResult acceptance =
        evaluateAcceptance(
            completedAcceptance,
            requiredAcceptance
        );

    cout << "Accepted: "
         << boolalpha
         << acceptance.accepted
         << "\n";

    if (!acceptance.accepted) {
        cout << "Missing criteria:\n";

        for (const string& missing : acceptance.missingCriteria) {
            cout << "  - " << missing << "\n";
        }
    }

    // -------------------------------------------------------------------------
    // CHANGE CONTROL
    // -------------------------------------------------------------------------

    subsection("8. Change request");

    ChangeRequest change{
        "CR-001",
        "Add multilingual interface support.",
        "Expansion into additional markets.",
        80.0,
        12000.0,
        10,
        ChangeStatus::Proposed
    };

    try {
        system.submitChange(change);
    } catch (const exception& error) {
        cerr << "Change submission failed: "
             << error.what()
             << "\n";

        return 1;
    }

    system.analyzeChange("CR-001");

    optional<ChangeRequest> analyzed =
        system.findChange("CR-001");

    if (analyzed.has_value()) {
        const ImpactAssessment impact =
            assessChange(analyzed.value());

        cout << "Change: "
             << analyzed->id
             << "\n";

        cout << "Status: "
             << changeStatusToString(analyzed->status)
             << "\n";

        cout << "Estimated effort: "
             << impact.effortHours
             << " hours\n";

        cout << "Cost impact: "
             << impact.costImpact
             << "\n";

        cout << "Schedule impact: "
             << impact.scheduleDays
             << " days\n";

        cout << "Composite impact score: "
             << impact.compositeScore
             << "\n";
    }

    system.approveChange("CR-001");

    const optional<ChangeRequest> approved =
        system.findChange("CR-001");

    if (approved.has_value()) {
        cout << "Final status: "
             << changeStatusToString(approved->status)
             << "\n";
    }

    // -------------------------------------------------------------------------
    // EDGE CASE: INVALID CHANGE
    // -------------------------------------------------------------------------

    subsection("9. Failure handling and edge case");

    ChangeRequest invalidChange{
        "CR-002",
        "Invalid example.",
        "Testing validation.",
        -10.0,
        5000.0,
        3,
        ChangeStatus::Proposed
    };

    try {
        system.submitChange(invalidChange);
        cout << "Unexpected success.\n";
    } catch (const exception& error) {
        cout << "Expected validation failure: "
             << error.what()
             << "\n";
    }

    // -------------------------------------------------------------------------
    // SCOPE CREEP ANALYSIS
    // -------------------------------------------------------------------------

    subsection("10. Scope creep analysis");

    set<string> baselineItems(
        statement.inclusions.begin(),
        statement.inclusions.end()
    );

    vector<string> proposedItems = statement.inclusions;

    proposedItems.push_back("Native mobile applications");
    proposedItems.push_back("Advanced analytics");

    set<string> additions;

    for (const string& item : proposedItems) {
        if (baselineItems.count(item) == 0) {
            additions.insert(item);
        }
    }

    cout << "Potential additions:\n";

    for (const string& addition : additions) {
        cout << "  - " << addition << "\n";
    }

    // -------------------------------------------------------------------------
    // PRIORITY ANALYSIS
    // -------------------------------------------------------------------------

    subsection("11. Requirement priority distribution");

    map<Priority, int> priorityCounts;

    for (const Requirement& requirement : requirementList) {
        priorityCounts[requirement.priority]++;
    }

    for (const auto& [priority, count] : priorityCounts) {
        cout << priorityToString(priority)
             << ": "
             << count
             << "\n";
    }

    // -------------------------------------------------------------------------
    // SYSTEM HEALTH CHECK
    // -------------------------------------------------------------------------

    subsection("12. Scope governance health check");

    struct Check {
        string name;
        bool passed;
    };

    vector<Check> checks{
        {
            "Objective is defined",
            !statement.objective.empty()
        },
        {
            "Requirements exist",
            system.requirementCount() > 0
        },
        {
            "Deliverables exist",
            system.deliverableCount() > 0
        },
        {
            "Traceability is complete",
            system.traceabilityCoverage() == 100.0
        },
        {
            "Work packages exist",
            system.workPackageCount() > 0
        },
        {
            "Scope exclusions are documented",
            !statement.exclusions.empty()
        },
        {
            "Assumptions are documented",
            !statement.assumptions.empty()
        },
        {
            "Constraints are documented",
            !statement.constraints.empty()
        },
        {
            "Baseline exists",
            system.getBaseline().has_value()
        }
    };

    for (const Check& check : checks) {
        cout << "["
             << (check.passed ? "PASS" : "FAIL")
             << "] "
             << check.name
             << "\n";
    }

    // -------------------------------------------------------------------------
    // COMPLEXITY AND ARCHITECTURAL NOTES
    // -------------------------------------------------------------------------

    section("13. Technical design considerations");

    cout << R"(
The case study uses unordered_map for requirement, deliverable, and work
package identifiers. Average lookup is O(1), making identifier-based access
appropriate for large collections.

Traceability coverage scans the requirement and deliverable collections and is
approximately O(R + D) for R requirements and D requirement references.

Priority aggregation uses a map and is approximately O(R log P), where P is the
number of distinct priorities. Since P is small, this is effectively linear
for normal project data.

A production scope platform would normally add:

- persistent database storage
- immutable audit records
- user authentication and authorization
- optimistic concurrency control
- transaction management
- baseline versioning
- approval workflows
- change history
- API validation
- data integrity constraints
- automated acceptance-test execution
- reporting and export
- role-based access controls

Security matters because scope records can contain contractual, financial,
technical, or customer information. Users should only be allowed to modify
scope artifacts according to their assigned authority.

The central architectural principle is traceability: every important scope
decision should be connected to the requirement, deliverable, work package,
acceptance condition, or approved change that explains it.
)";

    section("14. Case-study completion");

    cout << "Requirements: "
         << system.requirementCount()
         << "\n";

    cout << "Deliverables: "
         << system.deliverableCount()
         << "\n";

    cout << "Work packages: "
         << system.workPackageCount()
         << "\n";

    cout << "Total planned effort: "
         << system.totalEffortHours()
         << " hours\n";

    cout << "Traceability coverage: "
         << system.traceabilityCoverage()
         << "%\n";

    cout << "\nThe modeled project has a defined boundary, traceable requirements,\n"
         << "structured deliverables, decomposed work, acceptance conditions,\n"
         << "a baseline, and controlled change handling.\n";

    return 0;
}
