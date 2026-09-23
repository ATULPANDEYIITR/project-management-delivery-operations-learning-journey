/*
 * Requirements Collection: Industry-Style Case Study
 *
 * Modern C++17 implementation.
 *
 * Scenario:
 * A public-facing application management platform is being designed.
 * Customers submit applications, customers track their applications,
 * operations managers monitor processing, and security personnel require
 * controlled access and auditability.
 *
 * The program demonstrates:
 * - stakeholder modeling
 * - requirements classification
 * - functional and non-functional requirements
 * - user stories
 * - acceptance criteria
 * - validation
 * - prioritization
 * - conflict detection
 * - traceability
 * - change management
 * - versioning
 * - scope management
 * - performance considerations
 * - security considerations
 * - an in-memory requirements repository
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic requirements_collection.cpp -o requirements_collection
 */

#include <algorithm>
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


// ---------------------------------------------------------------------------
// 1. ENUMERATIONS
// ---------------------------------------------------------------------------

enum class RequirementType {
    Business,
    User,
    Functional,
    NonFunctional,
    Security,
    Data,
    Interface,
    Regulatory,
    Constraint
};

enum class Priority {
    Must,
    Should,
    Could,
    Wont
};

enum class RequirementStatus {
    Draft,
    Validated,
    Approved,
    Changed,
    Rejected
};

string toString(RequirementType type) {
    switch (type) {
        case RequirementType::Business: return "Business";
        case RequirementType::User: return "User";
        case RequirementType::Functional: return "Functional";
        case RequirementType::NonFunctional: return "Non-functional";
        case RequirementType::Security: return "Security";
        case RequirementType::Data: return "Data";
        case RequirementType::Interface: return "Interface";
        case RequirementType::Regulatory: return "Regulatory";
        case RequirementType::Constraint: return "Constraint";
    }

    return "Unknown";
}

string toString(Priority priority) {
    switch (priority) {
        case Priority::Must: return "Must";
        case Priority::Should: return "Should";
        case Priority::Could: return "Could";
        case Priority::Wont: return "Won't";
    }

    return "Unknown";
}

string toString(RequirementStatus status) {
    switch (status) {
        case RequirementStatus::Draft: return "Draft";
        case RequirementStatus::Validated: return "Validated";
        case RequirementStatus::Approved: return "Approved";
        case RequirementStatus::Changed: return "Changed";
        case RequirementStatus::Rejected: return "Rejected";
    }

    return "Unknown";
}


// ---------------------------------------------------------------------------
// 2. STAKEHOLDER MODEL
// ---------------------------------------------------------------------------

struct Stakeholder {
    string id;
    string name;
    string role;
    int influence;
    int interest;
    vector<string> needs;
    vector<string> concerns;

    string engagementLevel() const {
        if (influence >= 4 && interest >= 4) {
            return "Manage closely";
        }

        if (influence >= 4) {
            return "Keep satisfied";
        }

        if (interest >= 4) {
            return "Keep informed";
        }

        return "Monitor";
    }
};


// ---------------------------------------------------------------------------
// 3. REQUIREMENT MODEL
// ---------------------------------------------------------------------------

struct Requirement {
    string id;
    string title;
    string description;
    RequirementType type;
    Priority priority;
    string source;

    vector<string> stakeholderIds;
    vector<string> acceptanceCriteria;
    vector<string> dependencies;
    vector<string> assumptions;

    RequirementStatus status = RequirementStatus::Draft;
    int version = 1;

    bool isComplete() const {
        return
            !id.empty() &&
            !title.empty() &&
            !description.empty() &&
            !source.empty() &&
            !stakeholderIds.empty() &&
            !acceptanceCriteria.empty();
    }

    void display() const {
        cout << "\n[" << id << "] " << title << "\n";
        cout << "Type: " << toString(type) << "\n";
        cout << "Priority: " << toString(priority) << "\n";
        cout << "Status: " << toString(status) << "\n";
        cout << "Version: " << version << "\n";
        cout << "Source: " << source << "\n";
        cout << "Description: " << description << "\n";

        cout << "Acceptance criteria:\n";
        for (const auto& criterion : acceptanceCriteria) {
            cout << "  - " << criterion << "\n";
        }
    }
};


// ---------------------------------------------------------------------------
// 4. REQUIREMENT VALIDATION
// ---------------------------------------------------------------------------

const set<string> ambiguousTerms = {
    "fast",
    "easy",
    "simple",
    "quick",
    "reasonable",
    "appropriate",
    "efficient",
    "soon",
    "etc"
};

vector<string> tokenize(const string& input) {
    vector<string> tokens;
    string current;

    for (char character : input) {
        if (isalnum(static_cast<unsigned char>(character))) {
            current += static_cast<char>(
                tolower(static_cast<unsigned char>(character))
            );
        } else if (!current.empty()) {
            tokens.push_back(current);
            current.clear();
        }
    }

    if (!current.empty()) {
        tokens.push_back(current);
    }

    return tokens;
}

vector<string> detectAmbiguousTerms(const string& text) {
    vector<string> result;

    for (const auto& token : tokenize(text)) {
        if (ambiguousTerms.count(token)) {
            if (find(result.begin(), result.end(), token) == result.end()) {
                result.push_back(token);
            }
        }
    }

    return result;
}

vector<string> validateRequirement(const Requirement& requirement) {
    vector<string> issues;

    if (requirement.id.empty()) {
        issues.push_back("Missing identifier.");
    }

    if (requirement.title.empty()) {
        issues.push_back("Missing title.");
    }

    if (requirement.description.empty()) {
        issues.push_back("Missing description.");
    }

    if (requirement.source.empty()) {
        issues.push_back("Missing source.");
    }

    if (requirement.stakeholderIds.empty()) {
        issues.push_back("No stakeholder linkage.");
    }

    if (requirement.acceptanceCriteria.empty()) {
        issues.push_back("No acceptance criteria.");
    }

    const auto ambiguous = detectAmbiguousTerms(requirement.description);

    if (!ambiguous.empty()) {
        stringstream stream;
        stream << "Potentially ambiguous terms: ";

        for (size_t index = 0; index < ambiguous.size(); ++index) {
            if (index > 0) {
                stream << ", ";
            }
            stream << ambiguous[index];
        }

        issues.push_back(stream.str());
    }

    return issues;
}


// ---------------------------------------------------------------------------
// 5. USER STORY
// ---------------------------------------------------------------------------

struct UserStory {
    string id;
    string role;
    string action;
    string benefit;
    vector<string> acceptanceCriteria;

    string formatted() const {
        return
            "As a " + role +
            ", I want to " + action +
            ", so that " + benefit + ".";
    }

    bool isTestable() const {
        return !acceptanceCriteria.empty();
    }
};


// ---------------------------------------------------------------------------
// 6. USE CASE
// ---------------------------------------------------------------------------

struct UseCase {
    string id;
    string name;
    string primaryActor;
    vector<string> preconditions;
    vector<string> mainFlow;
    vector<string> alternateFlows;
    vector<string> postconditions;

    vector<string> validate() const {
        vector<string> issues;

        if (name.empty()) {
            issues.push_back("Missing use-case name.");
        }

        if (primaryActor.empty()) {
            issues.push_back("Missing primary actor.");
        }

        if (preconditions.empty()) {
            issues.push_back("Missing preconditions.");
        }

        if (mainFlow.empty()) {
            issues.push_back("Missing main flow.");
        }

        if (postconditions.empty()) {
            issues.push_back("Missing postconditions.");
        }

        return issues;
    }
};


// ---------------------------------------------------------------------------
// 7. PRIORITIZATION
// ---------------------------------------------------------------------------

struct PrioritizationScore {
    int businessValue;
    int urgency;
    int riskReduction;
    int dependencyImpact;

    int total() const {
        return
            businessValue +
            urgency +
            riskReduction +
            dependencyImpact;
    }
};


// ---------------------------------------------------------------------------
// 8. CHANGE REQUEST
// ---------------------------------------------------------------------------

struct ChangeRequest {
    string id;
    string requirementId;
    string requestedBy;
    string reason;
    string impact;
    string status = "Pending";

    void approve() {
        status = "Approved";
    }

    void reject() {
        status = "Rejected";
    }
};


// ---------------------------------------------------------------------------
// 9. TRACEABILITY
// ---------------------------------------------------------------------------

class TraceabilityMatrix {
private:
    map<string, set<string>> businessToUser;
    map<string, set<string>> userToRequirement;
    map<string, set<string>> requirementToTest;

public:
    void addBusinessMapping(
        const string& businessId,
        const string& userStoryId
    ) {
        businessToUser[businessId].insert(userStoryId);
    }

    void addUserMapping(
        const string& userStoryId,
        const string& requirementId
    ) {
        userToRequirement[userStoryId].insert(requirementId);
    }

    void addTestMapping(
        const string& requirementId,
        const string& testId
    ) {
        requirementToTest[requirementId].insert(testId);
    }

    vector<string> unverifiedRequirements(
        const vector<string>& requirementIds
    ) const {
        vector<string> result;

        for (const auto& requirementId : requirementIds) {
            auto iterator = requirementToTest.find(requirementId);

            if (iterator == requirementToTest.end() ||
                iterator->second.empty()) {
                result.push_back(requirementId);
            }
        }

        return result;
    }

    void display() const {
        cout << "\nBusiness -> User traceability:\n";

        for (const auto& [business, users] : businessToUser) {
            cout << business << " -> ";

            for (const auto& user : users) {
                cout << user << " ";
            }

            cout << "\n";
        }

        cout << "\nUser -> Requirement traceability:\n";

        for (const auto& [user, requirements] : userToRequirement) {
            cout << user << " -> ";

            for (const auto& requirement : requirements) {
                cout << requirement << " ";
            }

            cout << "\n";
        }

        cout << "\nRequirement -> Test traceability:\n";

        for (const auto& [requirement, tests] : requirementToTest) {
            cout << requirement << " -> ";

            for (const auto& test : tests) {
                cout << test << " ";
            }

            cout << "\n";
        }
    }
};


// ---------------------------------------------------------------------------
// 10. REQUIREMENTS REPOSITORY
// ---------------------------------------------------------------------------

class RequirementsRepository {
private:
    map<string, Requirement> requirements;

    // A vector of previous snapshots provides a simple version history.
    map<string, vector<Requirement>> history;

public:
    void add(const Requirement& requirement) {
        if (requirement.id.empty()) {
            throw invalid_argument("Requirement identifier cannot be empty.");
        }

        if (requirements.count(requirement.id)) {
            throw runtime_error(
                "Requirement already exists: " + requirement.id
            );
        }

        requirements.emplace(requirement.id, requirement);
    }

    Requirement& get(const string& id) {
        auto iterator = requirements.find(id);

        if (iterator == requirements.end()) {
            throw out_of_range(
                "Requirement not found: " + id
            );
        }

        return iterator->second;
    }

    const Requirement& get(const string& id) const {
        auto iterator = requirements.find(id);

        if (iterator == requirements.end()) {
            throw out_of_range(
                "Requirement not found: " + id
            );
        }

        return iterator->second;
    }

    void updateDescription(
        const string& id,
        const string& newDescription
    ) {
        Requirement& requirement = get(id);

        history[id].push_back(requirement);

        requirement.description = newDescription;
        ++requirement.version;
        requirement.status = RequirementStatus::Changed;
    }

    vector<Requirement> byType(RequirementType type) const {
        vector<Requirement> result;

        for (const auto& [id, requirement] : requirements) {
            if (requirement.type == type) {
                result.push_back(requirement);
            }
        }

        return result;
    }

    vector<Requirement> byPriority(Priority priority) const {
        vector<Requirement> result;

        for (const auto& [id, requirement] : requirements) {
            if (requirement.priority == priority) {
                result.push_back(requirement);
            }
        }

        return result;
    }

    size_t size() const {
        return requirements.size();
    }

    size_t historySize(const string& id) const {
        auto iterator = history.find(id);

        if (iterator == history.end()) {
            return 0;
        }

        return iterator->second.size();
    }

    const map<string, Requirement>& all() const {
        return requirements;
    }
};


// ---------------------------------------------------------------------------
// 11. SCOPE MANAGEMENT
// ---------------------------------------------------------------------------

class ScopeBoundary {
private:
    set<string> inScope;
    set<string> outOfScope;

public:
    ScopeBoundary(
        initializer_list<string> included,
        initializer_list<string> excluded
    )
        : inScope(included),
          outOfScope(excluded) {}

    string classify(const string& item) const {
        if (inScope.count(item)) {
            return "In scope";
        }

        if (outOfScope.count(item)) {
            return "Out of scope";
        }

        return "Unclassified";
    }
};


// ---------------------------------------------------------------------------
// 12. CONFLICT DETECTION
// ---------------------------------------------------------------------------

optional<string> detectPotentialConflict(
    const Requirement& first,
    const Requirement& second
) {
    const string firstText = first.description;
    const string secondText = second.description;

    const bool firstHasAccess =
        firstText.find("access") != string::npos;

    const bool secondHasAccess =
        secondText.find("access") != string::npos;

    const bool firstProtects =
        firstText.find("prevent") != string::npos ||
        firstText.find("restrict") != string::npos ||
        firstText.find("unauthorized") != string::npos;

    const bool secondProtects =
        secondText.find("prevent") != string::npos ||
        secondText.find("restrict") != string::npos ||
        secondText.find("unauthorized") != string::npos;

    if ((firstHasAccess && secondProtects) ||
        (secondHasAccess && firstProtects)) {
        return
            "Potential access-control conflict. Clarify authorized roles, "
            "data scope, and access conditions.";
    }

    return nullopt;
}


// ---------------------------------------------------------------------------
// 13. REQUIREMENT METRICS
// ---------------------------------------------------------------------------

struct RequirementMetrics {
    size_t count = 0;
    double completePercentage = 0.0;
    double mustPercentage = 0.0;
};

RequirementMetrics calculateMetrics(
    const RequirementsRepository& repository
) {
    RequirementMetrics metrics;
    metrics.count = repository.size();

    if (metrics.count == 0) {
        return metrics;
    }

    size_t completeCount = 0;
    size_t mustCount = 0;

    for (const auto& [id, requirement] : repository.all()) {
        if (requirement.isComplete()) {
            ++completeCount;
        }

        if (requirement.priority == Priority::Must) {
            ++mustCount;
        }
    }

    metrics.completePercentage =
        static_cast<double>(completeCount) /
        static_cast<double>(metrics.count) *
        100.0;

    metrics.mustPercentage =
        static_cast<double>(mustCount) /
        static_cast<double>(metrics.count) *
        100.0;

    return metrics;
}


// ---------------------------------------------------------------------------
// 14. COMPLETE CASE STUDY
// ---------------------------------------------------------------------------

int main() {
    cout << string(80, '=') << "\n";
    cout << "DIGITAL APPLICATION MANAGEMENT PLATFORM\n";
    cout << "REQUIREMENTS COLLECTION CASE STUDY\n";
    cout << string(80, '=') << "\n";

    // -----------------------------------------------------------------------
    // Stakeholder discovery
    // -----------------------------------------------------------------------

    vector<Stakeholder> stakeholders = {
        {
            "STK-001",
            "Operations Manager",
            "Business Owner",
            5,
            5,
            {"Operational visibility", "Faster processing"},
            {"Manual errors", "Delays"}
        },
        {
            "STK-002",
            "Customer",
            "End User",
            3,
            5,
            {"Simple workflow", "Application status"},
            {"Complexity", "Unclear status"}
        },
        {
            "STK-003",
            "Security Officer",
            "Security",
            5,
            4,
            {"Access control", "Auditability"},
            {"Unauthorized access"}
        }
    };

    cout << "\nStakeholders:\n";

    for (const auto& stakeholder : stakeholders) {
        cout
            << stakeholder.id << " | "
            << stakeholder.name << " | "
            << stakeholder.role << " | "
            << stakeholder.engagementLevel()
            << "\n";
    }


    // -----------------------------------------------------------------------
    // Business requirement
    // -----------------------------------------------------------------------

    Requirement businessRequirement{
        "BUS-001",
        "Improve application processing visibility",
        "The organization requires a controlled digital process through which "
        "customers and authorized employees can obtain accurate application status.",
        RequirementType::Business,
        Priority::Must,
        "Business owner workshop",
        {"STK-001", "STK-002"},
        {
            "The process provides an authoritative application status.",
            "Authorized stakeholders can obtain required status information."
        },
        {},
        {}
    };


    // -----------------------------------------------------------------------
    // Functional requirement
    // -----------------------------------------------------------------------

    Requirement submissionRequirement{
        "REQ-001",
        "Application submission",
        "The system shall allow an authenticated customer to submit a completed application.",
        RequirementType::Functional,
        Priority::Must,
        "Customer interview",
        {"STK-002"},
        {
            "Required fields are validated before submission.",
            "A successful submission receives a unique identifier.",
            "The customer receives a confirmation."
        },
        {},
        {}
    };


    // -----------------------------------------------------------------------
    // Status tracking requirement
    // -----------------------------------------------------------------------

    Requirement statusRequirement{
        "REQ-002",
        "Application status tracking",
        "The system shall allow an authenticated customer to view the current "
        "status of an application the customer is authorized to access.",
        RequirementType::Functional,
        Priority::Must,
        "Customer interview",
        {"STK-002"},
        {
            "An authorized customer can view the current status.",
            "An unauthorized customer cannot retrieve another customer's record.",
            "An invalid identifier produces a controlled response."
        },
        {"REQ-001"},
        {}
    };


    // -----------------------------------------------------------------------
    // Security requirement
    // -----------------------------------------------------------------------

    Requirement securityRequirement{
        "REQ-003",
        "Access control",
        "The system shall restrict protected application information to "
        "authenticated users who are authorized to access the requested record.",
        RequirementType::Security,
        Priority::Must,
        "Security workshop",
        {"STK-003"},
        {
            "Unauthenticated requests are rejected.",
            "Authenticated users without authorization cannot retrieve protected records.",
            "Denied access attempts are recorded."
        },
        {},
        {}
    };


    // -----------------------------------------------------------------------
    // Non-functional performance requirement
    // -----------------------------------------------------------------------

    Requirement performanceRequirement{
        "REQ-004",
        "Application search performance",
        "The system shall return application search results within 2 seconds "
        "for at least 95 percent of requests under the approved production workload.",
        RequirementType::NonFunctional,
        Priority::Should,
        "Performance workshop",
        {"STK-001"},
        {
            "A representative performance test is executed.",
            "At least 95 percent of requests complete within 2 seconds.",
            "The test workload and measurement method are documented."
        },
        {"REQ-002"},
        {}
    };


    // -----------------------------------------------------------------------
    // Audit requirement
    // -----------------------------------------------------------------------

    Requirement auditRequirement{
        "REQ-005",
        "Security audit logging",
        "The system shall record security-relevant access events with "
        "timestamp, actor, action, target, and result.",
        RequirementType::Security,
        Priority::Must,
        "Security workshop",
        {"STK-003"},
        {
            "Successful protected-data access creates an audit record.",
            "Denied access creates an audit record.",
            "Each record contains the required event fields."
        },
        {"REQ-003"},
        {}
    };


    // -----------------------------------------------------------------------
    // Validate requirements
    // -----------------------------------------------------------------------

    vector<Requirement> requirements = {
        businessRequirement,
        submissionRequirement,
        statusRequirement,
        securityRequirement,
        performanceRequirement,
        auditRequirement
    };

    cout << "\nRequirement validation:\n";

    for (const auto& requirement : requirements) {
        const auto issues = validateRequirement(requirement);

        cout
            << requirement.id
            << ": "
            << (issues.empty() ? "PASS" : "REVIEW")
            << "\n";

        for (const auto& issue : issues) {
            cout << "  - " << issue << "\n";
        }
    }


    // -----------------------------------------------------------------------
    // User story
    // -----------------------------------------------------------------------

    UserStory customerStory{
        "US-001",
        "customer",
        "search for an application",
        "I can see its current status",
        {
            "Given a valid application identifier, the current status is displayed.",
            "If the application does not exist, a controlled not-found response is displayed."
        }
    };

    cout << "\nUser story:\n";
    cout << customerStory.formatted() << "\n";
    cout << "Testable: "
         << (customerStory.isTestable() ? "Yes" : "No")
         << "\n";


    // -----------------------------------------------------------------------
    // Use case
    // -----------------------------------------------------------------------

    UseCase submitUseCase{
        "UC-001",
        "Submit Application",
        "Customer",
        {
            "Customer is authenticated.",
            "Required application information is available."
        },
        {
            "Customer opens the application form.",
            "System displays required fields.",
            "Customer enters information.",
            "System validates information.",
            "System stores the application.",
            "System returns a unique confirmation identifier."
        },
        {
            "Invalid information produces validation messages.",
            "Storage failure must not result in false success."
        },
        {
            "Application is stored.",
            "Confirmation identifier is available."
        }
    };

    cout << "\nUse-case validation:\n";

    const auto useCaseIssues = submitUseCase.validate();

    if (useCaseIssues.empty()) {
        cout << "PASS\n";
    } else {
        for (const auto& issue : useCaseIssues) {
            cout << "- " << issue << "\n";
        }
    }


    // -----------------------------------------------------------------------
    // Repository
    // -----------------------------------------------------------------------

    RequirementsRepository repository;

    try {
        for (const auto& requirement : requirements) {
            repository.add(requirement);
        }

        cout << "\nRepository contains "
             << repository.size()
             << " requirements.\n";
    } catch (const exception& error) {
        cerr << "Repository error: "
             << error.what()
             << "\n";

        return 1;
    }


    // -----------------------------------------------------------------------
    // Duplicate handling
    // -----------------------------------------------------------------------

    try {
        repository.add(submissionRequirement);
    } catch (const exception& error) {
        cout << "\nDuplicate requirement rejected safely:\n";
        cout << error.what() << "\n";
    }


    // -----------------------------------------------------------------------
    // Requirement retrieval
    // -----------------------------------------------------------------------

    try {
        const auto& requirement = repository.get("REQ-003");

        cout << "\nRetrieved security requirement:\n";
        requirement.display();
    } catch (const exception& error) {
        cerr << error.what() << "\n";
    }


    // -----------------------------------------------------------------------
    // Versioned change
    // -----------------------------------------------------------------------

    try {
        repository.updateDescription(
            "REQ-004",
            "The system shall return application search results within "
            "1.5 seconds for at least 95 percent of requests under the "
            "approved production workload."
        );

        const auto& changed = repository.get("REQ-004");

        cout << "\nVersioned change:\n";
        cout << "Requirement: " << changed.id << "\n";
        cout << "Version: " << changed.version << "\n";
        cout << "Status: " << toString(changed.status) << "\n";
        cout << "Historical versions: "
             << repository.historySize("REQ-004")
             << "\n";
    } catch (const exception& error) {
        cerr << error.what() << "\n";
    }


    // -----------------------------------------------------------------------
    // Prioritization
    // -----------------------------------------------------------------------

    map<string, PrioritizationScore> scores = {
        {
            "REQ-001",
            {5, 5, 3, 4}
        },
        {
            "REQ-003",
            {5, 5, 5, 5}
        },
        {
            "REQ-004",
            {4, 3, 3, 3}
        }
    };

    cout << "\nPrioritization evidence:\n";

    for (const auto& [id, score] : scores) {
        cout
            << id
            << " | business="
            << score.businessValue
            << " | urgency="
            << score.urgency
            << " | risk="
            << score.riskReduction
            << " | dependency="
            << score.dependencyImpact
            << " | total="
            << score.total()
            << "\n";
    }

    cout
        << "The scoring model is an agreed decision-support mechanism; "
        << "the criteria and weights should be documented with stakeholders.\n";


    // -----------------------------------------------------------------------
    // Conflict analysis
    // -----------------------------------------------------------------------

    Requirement managerAccessRequirement{
        "REQ-006",
        "Manager operational access",
        "Authorized managers shall have access to operational application data.",
        RequirementType::Functional,
        Priority::Must,
        "Operations workshop",
        {"STK-001"},
        {
            "Authorized managers can retrieve required operational information."
        },
        {},
        {}
    };

    cout << "\nConflict analysis:\n";

    const auto conflict = detectPotentialConflict(
        managerAccessRequirement,
        securityRequirement
    );

    if (conflict.has_value()) {
        cout << *conflict << "\n";
    } else {
        cout << "No potential conflict detected.\n";
    }


    // -----------------------------------------------------------------------
    // Traceability
    // -----------------------------------------------------------------------

    TraceabilityMatrix traceability;

    traceability.addBusinessMapping("BUS-001", "US-001");
    traceability.addUserMapping("US-001", "REQ-002");
    traceability.addTestMapping("REQ-002", "TEST-002");
    traceability.addTestMapping("REQ-003", "TEST-003");
    traceability.addTestMapping("REQ-004", "TEST-004");

    traceability.display();

    const vector<string> requirementIds = {
        "REQ-001",
        "REQ-002",
        "REQ-003",
        "REQ-004",
        "REQ-005"
    };

    const auto unverified =
        traceability.unverifiedRequirements(requirementIds);

    cout << "\nUnverified requirements:\n";

    for (const auto& id : unverified) {
        cout << "- " << id << "\n";
    }


    // -----------------------------------------------------------------------
    // Scope management
    // -----------------------------------------------------------------------

    ScopeBoundary scope(
        {
            "Application submission",
            "Application status tracking",
            "Authentication",
            "Manager dashboard"
        },
        {
            "Unrelated accounting replacement",
            "International expansion"
        }
    );

    cout << "\nScope classification:\n";

    const vector<string> scopeItems = {
        "Application submission",
        "International expansion",
        "Mobile game integration"
    };

    for (const auto& item : scopeItems) {
        cout
            << item
            << ": "
            << scope.classify(item)
            << "\n";
    }


    // -----------------------------------------------------------------------
    // Change request
    // -----------------------------------------------------------------------

    ChangeRequest change{
        "CR-001",
        "REQ-004",
        "Operations Manager",
        "Observed production workload has increased.",
        "May require infrastructure and database optimization."
    };

    cout << "\nChange request before approval:\n";
    cout << change.id << " | " << change.status << "\n";

    change.approve();

    cout << "Change request after approval:\n";
    cout << change.id << " | " << change.status << "\n";


    // -----------------------------------------------------------------------
    // Metrics
    // -----------------------------------------------------------------------

    const auto metrics = calculateMetrics(repository);

    cout << fixed << setprecision(2);

    cout << "\nRepository metrics:\n";
    cout << "Count: "
         << metrics.count
         << "\n";

    cout << "Complete: "
         << metrics.completePercentage
         << "%\n";

    cout << "Must priority: "
         << metrics.mustPercentage
         << "%\n";


    // -----------------------------------------------------------------------
    // Performance reasoning
    // -----------------------------------------------------------------------

    cout << "\nPerformance considerations:\n";
    cout << "- std::map provides logarithmic identifier lookup.\n";
    cout << "- std::unordered_map can provide average constant-time lookup.\n";
    cout << "- Sequential vector searches are linear.\n";
    cout << "- Large repositories may require database indexes and search indexes.\n";


    // -----------------------------------------------------------------------
    // Security reasoning
    // -----------------------------------------------------------------------

    cout << "\nSecurity considerations:\n";
    cout << "- Authentication establishes identity; authorization determines access.\n";
    cout << "- Requirement records may contain confidential business information.\n";
    cout << "- Requirement changes should have an auditable history.\n";
    cout << "- Sensitive interview information should be collected only when necessary.\n";
    cout << "- Secrets such as passwords and API keys must never be stored in requirements.\n";


    // -----------------------------------------------------------------------
    // Requirements collection lifecycle
    // -----------------------------------------------------------------------

    const vector<string> lifecycle = {
        "Define the business problem",
        "Identify stakeholders",
        "Understand the current process",
        "Collect needs and pain points",
        "Identify business rules",
        "Identify functional requirements",
        "Identify non-functional requirements",
        "Identify security and regulatory requirements",
        "Record assumptions and dependencies",
        "Document acceptance criteria",
        "Validate requirements",
        "Resolve conflicts",
        "Prioritize requirements",
        "Establish traceability",
        "Baseline approved requirements",
        "Control changes"
    };

    cout << "\nRequirements collection lifecycle:\n";

    for (size_t index = 0; index < lifecycle.size(); ++index) {
        cout
            << setw(2)
            << index + 1
            << ". "
            << lifecycle[index]
            << "\n";
    }


    // -----------------------------------------------------------------------
    // Edge case: missing requirement
    // -----------------------------------------------------------------------

    try {
        repository.get("REQ-NOT-FOUND");
    } catch (const exception& error) {
        cout << "\nMissing requirement handled:\n";
        cout << error.what() << "\n";
    }


    // -----------------------------------------------------------------------
    // Edge case: ambiguous requirement
    // -----------------------------------------------------------------------

    Requirement ambiguousRequirement{
        "REQ-BAD",
        "Fast interface",
        "The system shall provide a fast and easy interface.",
        RequirementType::NonFunctional,
        Priority::Should,
        "Interview",
        {"STK-002"},
        {},
        {},
        {}
    };

    cout << "\nAmbiguous requirement validation:\n";

    for (const auto& issue : validateRequirement(ambiguousRequirement)) {
        cout << "- " << issue << "\n";
    }


    // -----------------------------------------------------------------------
    // Final checklist
    // -----------------------------------------------------------------------

    cout << "\nRequirements collection checklist:\n";

    const vector<string> checklist = {
        "Business problem defined",
        "Stakeholders identified",
        "Current process understood",
        "Elicitation performed",
        "Requirements classified",
        "Acceptance criteria documented",
        "Ambiguity reviewed",
        "Conflicts resolved",
        "Priorities agreed",
        "Traceability established",
        "Requirements validated",
        "Baseline established",
        "Change process established"
    };

    for (size_t index = 0; index < checklist.size(); ++index) {
        cout
            << setw(2)
            << index + 1
            << ". "
            << checklist[index]
            << "\n";
    }

    cout << "\nCase study completed successfully.\n";

    return 0;
}
