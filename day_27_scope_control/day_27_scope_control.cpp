/*
    Scope Control: Managing Changes to Scope

    C++17 industry-style case study.

    Scenario:
    A financial-services organization is developing a customer account
    platform. The approved scope contains an authentication service,
    customer portal, and reporting module.

    During delivery, stakeholders propose additional functionality.

    The system demonstrates:
    - Requirements
    - Deliverables
    - Scope baselines
    - Change requests
    - Impact analysis
    - Governance routing
    - Approval and rejection
    - Implementation
    - Rebaselining
    - Requirements traceability
    - Scope-creep detection
    - Audit history
    - Validation
    - Complexity considerations
    - Error handling

    Compile:
        g++ -std=c++17 -Wall -Wextra -pedantic scope_control.cpp -o scope_control

    Run:
        ./scope_control
*/

#include <algorithm>
#include <cassert>
#include <chrono>
#include <cmath>
#include <ctime>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;


// ---------------------------------------------------------------------------
// 1. UTILITY FUNCTIONS
// ---------------------------------------------------------------------------

string currentDate() {
    const auto now = chrono::system_clock::now();
    const time_t timeValue = chrono::system_clock::to_time_t(now);

    tm localTime{};

#ifdef _WIN32
    localtime_s(&localTime, &timeValue);
#else
    localtime_r(&timeValue, &localTime);
#endif

    ostringstream output;
    output << put_time(&localTime, "%Y-%m-%d");
    return output.str();
}


void printSection(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}


// ---------------------------------------------------------------------------
// 2. ENUMERATIONS
// ---------------------------------------------------------------------------

enum class ScopeStatus {
    Planned,
    InProgress,
    Completed,
    Removed
};


enum class ChangeStatus {
    Proposed,
    UnderReview,
    Approved,
    Rejected,
    Deferred,
    Implemented
};


enum class Priority {
    Low,
    Medium,
    High,
    Critical
};


string toString(ScopeStatus status) {
    switch (status) {
        case ScopeStatus::Planned:
            return "Planned";
        case ScopeStatus::InProgress:
            return "In Progress";
        case ScopeStatus::Completed:
            return "Completed";
        case ScopeStatus::Removed:
            return "Removed";
    }

    return "Unknown";
}


string toString(ChangeStatus status) {
    switch (status) {
        case ChangeStatus::Proposed:
            return "Proposed";
        case ChangeStatus::UnderReview:
            return "Under Review";
        case ChangeStatus::Approved:
            return "Approved";
        case ChangeStatus::Rejected:
            return "Rejected";
        case ChangeStatus::Deferred:
            return "Deferred";
        case ChangeStatus::Implemented:
            return "Implemented";
    }

    return "Unknown";
}


string toString(Priority priority) {
    switch (priority) {
        case Priority::Low:
            return "Low";
        case Priority::Medium:
            return "Medium";
        case Priority::High:
            return "High";
        case Priority::Critical:
            return "Critical";
    }

    return "Unknown";
}


// ---------------------------------------------------------------------------
// 3. DOMAIN OBJECTS
// ---------------------------------------------------------------------------

struct Deliverable {
    string id;
    string name;
    string description;
    double estimatedHours{};
    double estimatedCost{};
    ScopeStatus status{ScopeStatus::Planned};
    set<string> requirementIds;

    void validate() const {
        if (id.empty()) {
            throw invalid_argument("Deliverable ID cannot be empty.");
        }

        if (name.empty()) {
            throw invalid_argument("Deliverable name cannot be empty.");
        }

        if (estimatedHours < 0) {
            throw invalid_argument(
                "Deliverable hours cannot be negative."
            );
        }

        if (estimatedCost < 0) {
            throw invalid_argument(
                "Deliverable cost cannot be negative."
            );
        }
    }
};


struct Requirement {
    string id;
    string title;
    string description;
    Priority priority{Priority::Medium};
    vector<string> acceptanceCriteria;
    set<string> deliverableIds;

    void validate() const {
        if (id.empty()) {
            throw invalid_argument("Requirement ID cannot be empty.");
        }

        if (title.empty()) {
            throw invalid_argument("Requirement title cannot be empty.");
        }

        if (acceptanceCriteria.empty()) {
            throw invalid_argument(
                "Requirement must contain acceptance criteria."
            );
        }
    }
};


struct ImpactAnalysis {
    double scopeDelta{};
    double scheduleDeltaDays{};
    double costDelta{};
    double resourceDeltaHours{};

    double qualityRisk{};
    double technicalRisk{};
    double complianceRisk{};
    double operationalRisk{};

    vector<string> dependencies;
    vector<string> assumptions;

    void validate() const {
        if (scopeDelta < 0 ||
            scheduleDeltaDays < 0 ||
            costDelta < 0 ||
            resourceDeltaHours < 0) {
            throw invalid_argument(
                "Impact quantities cannot be negative."
            );
        }

        const vector<pair<string, double>> risks = {
            {"qualityRisk", qualityRisk},
            {"technicalRisk", technicalRisk},
            {"complianceRisk", complianceRisk},
            {"operationalRisk", operationalRisk}
        };

        for (const auto& [name, value] : risks) {
            if (value < 0 || value > 10) {
                throw invalid_argument(
                    name + " must be between 0 and 10."
                );
            }
        }
    }

    double averageRisk() const {
        return (
            qualityRisk +
            technicalRisk +
            complianceRisk +
            operationalRisk
        ) / 4.0;
    }

    double netImpactScore() const {
        return (
            averageRisk() * 2.0 +
            scheduleDeltaDays * 0.25 +
            costDelta / 10000.0
        );
    }
};


struct ChangeRequest {
    string id;
    string title;
    string requester;
    string description;
    string reason;
    Priority priority{Priority::Medium};
    string proposedDate;

    set<string> affectedRequirementIds;
    set<string> affectedDeliverableIds;

    bool hasImpactAnalysis{false};
    ImpactAnalysis impact{};

    ChangeStatus status{ChangeStatus::Proposed};
    string decision;
    string decisionDate;
    string implementationNotes;

    void validate() const {
        if (id.empty()) {
            throw invalid_argument("Change ID cannot be empty.");
        }

        if (title.empty()) {
            throw invalid_argument("Change title cannot be empty.");
        }

        if (requester.empty()) {
            throw invalid_argument("Requester cannot be empty.");
        }

        if (description.empty()) {
            throw invalid_argument(
                "Change description cannot be empty."
            );
        }
    }
};


struct AuditEntry {
    string timestamp;
    string actor;
    string action;
    string objectId;
    string details;
};


struct ChangeDecision {
    string changeId;
    ChangeStatus decision;
    string authority;
    string rationale;
    string timestamp;
};


// ---------------------------------------------------------------------------
// 4. SCOPE BASELINE
// ---------------------------------------------------------------------------

class ScopeBaseline {
private:
    map<string, Deliverable> deliverables;
    map<string, Requirement> requirements;

public:
    string version;
    string approvedDate;

    ScopeBaseline(
        string baselineVersion,
        string date,
        map<string, Deliverable> baselineDeliverables,
        map<string, Requirement> baselineRequirements
    )
        : version(move(baselineVersion)),
          approvedDate(move(date)),
          deliverables(move(baselineDeliverables)),
          requirements(move(baselineRequirements)) {
        validate();
    }

    void validate() const {
        for (const auto& [id, deliverable] : deliverables) {
            (void)id;
            deliverable.validate();
        }

        for (const auto& [id, requirement] : requirements) {
            (void)id;
            requirement.validate();

            for (const string& deliverableId :
                 requirement.deliverableIds) {
                if (!deliverables.contains(deliverableId)) {
                    throw invalid_argument(
                        "Requirement " + requirement.id +
                        " references unknown deliverable " +
                        deliverableId
                    );
                }
            }
        }
    }

    double totalHours() const {
        double total = 0;

        for (const auto& [id, deliverable] : deliverables) {
            (void)id;

            if (deliverable.status != ScopeStatus::Removed) {
                total += deliverable.estimatedHours;
            }
        }

        return total;
    }

    double totalCost() const {
        double total = 0;

        for (const auto& [id, deliverable] : deliverables) {
            (void)id;

            if (deliverable.status != ScopeStatus::Removed) {
                total += deliverable.estimatedCost;
            }
        }

        return total;
    }

    bool hasRequirement(const string& id) const {
        return requirements.contains(id);
    }

    bool hasDeliverable(const string& id) const {
        return deliverables.contains(id);
    }

    const map<string, Deliverable>& getDeliverables() const {
        return deliverables;
    }

    map<string, Deliverable>& mutableDeliverables() {
        return deliverables;
    }

    const map<string, Requirement>& getRequirements() const {
        return requirements;
    }

    ScopeBaseline clone(const string& newVersion,
                        const string& newDate) const {
        return ScopeBaseline(
            newVersion,
            newDate,
            deliverables,
            requirements
        );
    }
};


// ---------------------------------------------------------------------------
// 5. TRACEABILITY MATRIX
// ---------------------------------------------------------------------------

class TraceabilityMatrix {
private:
    map<string, set<string>> requirementToTests;
    map<string, set<string>> requirementToChanges;

public:
    void addTest(
        const string& requirementId,
        const string& testId
    ) {
        requirementToTests[requirementId].insert(testId);
    }

    void addChange(
        const string& requirementId,
        const string& changeId
    ) {
        requirementToChanges[requirementId].insert(changeId);
    }

    void printReport() const {
        set<string> requirementIds;

        for (const auto& [id, tests] : requirementToTests) {
            (void)tests;
            requirementIds.insert(id);
        }

        for (const auto& [id, changes] : requirementToChanges) {
            (void)changes;
            requirementIds.insert(id);
        }

        for (const string& id : requirementIds) {
            const auto testIt = requirementToTests.find(id);
            const auto changeIt = requirementToChanges.find(id);

            const size_t testCount =
                testIt == requirementToTests.end()
                    ? 0
                    : testIt->second.size();

            const size_t changeCount =
                changeIt == requirementToChanges.end()
                    ? 0
                    : changeIt->second.size();

            cout << id
                 << ": tests=" << testCount
                 << ", changes=" << changeCount
                 << ", tested=" << boolalpha
                 << (testCount > 0)
                 << "\n";
        }
    }
};


// ---------------------------------------------------------------------------
// 6. SCOPE CONTROL ENGINE
// ---------------------------------------------------------------------------

class ScopeControlEngine {
private:
    ScopeBaseline baseline;

    map<string, ChangeRequest> changeRequests;
    vector<ChangeDecision> decisions;
    vector<AuditEntry> auditLog;

    double costThreshold;
    double scheduleThreshold;
    double riskThreshold;

    void audit(
        const string& actor,
        const string& action,
        const string& objectId,
        const string& details
    ) {
        auditLog.push_back({
            currentDate(),
            actor,
            action,
            objectId,
            details
        });
    }

public:
    ScopeControlEngine(
        ScopeBaseline initialBaseline,
        double approvalCostThreshold = 5000,
        double approvalScheduleThreshold = 5,
        double approvalRiskThreshold = 6
    )
        : baseline(move(initialBaseline)),
          costThreshold(approvalCostThreshold),
          scheduleThreshold(approvalScheduleThreshold),
          riskThreshold(approvalRiskThreshold) {
        audit(
            "system",
            "CREATE_BASELINE",
            baseline.version,
            "Initial scope baseline created."
        );
    }

    const ScopeBaseline& getBaseline() const {
        return baseline;
    }

    void submitChange(ChangeRequest request) {
        request.validate();

        if (changeRequests.contains(request.id)) {
            throw invalid_argument(
                "Change request already exists: " + request.id
            );
        }

        for (const string& requirementId :
             request.affectedRequirementIds) {
            if (!baseline.hasRequirement(requirementId)) {
                throw invalid_argument(
                    "Unknown requirement: " + requirementId
                );
            }
        }

        for (const string& deliverableId :
             request.affectedDeliverableIds) {
            if (!baseline.hasDeliverable(deliverableId)) {
                throw invalid_argument(
                    "Unknown deliverable: " + deliverableId
                );
            }
        }

        changeRequests.emplace(request.id, move(request));

        const auto& stored = changeRequests.at(request.id);

        audit(
            stored.requester,
            "SUBMIT_CHANGE",
            stored.id,
            stored.title
        );
    }

    void analyzeChange(
        const string& changeId,
        ImpactAnalysis impact
    ) {
        auto it = changeRequests.find(changeId);

        if (it == changeRequests.end()) {
            throw out_of_range(
                "Unknown change request: " + changeId
            );
        }

        impact.validate();

        ChangeRequest& request = it->second;

        if (
            request.status != ChangeStatus::Proposed &&
            request.status != ChangeStatus::UnderReview
        ) {
            throw logic_error(
                "Change cannot be analyzed in current state."
            );
        }

        request.impact = move(impact);
        request.hasImpactAnalysis = true;
        request.status = ChangeStatus::UnderReview;

        audit(
            "change_analyst",
            "ANALYZE_CHANGE",
            changeId,
            "Impact analysis completed."
        );
    }

    string routingRecommendation(
        const string& changeId
    ) const {
        const auto it = changeRequests.find(changeId);

        if (it == changeRequests.end()) {
            throw out_of_range(
                "Unknown change request: " + changeId
            );
        }

        const ChangeRequest& request = it->second;

        if (!request.hasImpactAnalysis) {
            throw logic_error(
                "Impact analysis is required before routing."
            );
        }

        const ImpactAnalysis& impact = request.impact;

        if (
            impact.costDelta > costThreshold ||
            impact.scheduleDeltaDays > scheduleThreshold ||
            impact.averageRisk() >= riskThreshold ||
            request.priority == Priority::Critical
        ) {
            return "Change Control Board";
        }

        return "Project Manager";
    }

    void approve(
        const string& changeId,
        const string& authority,
        const string& rationale
    ) {
        auto it = changeRequests.find(changeId);

        if (it == changeRequests.end()) {
            throw out_of_range(
                "Unknown change request: " + changeId
            );
        }

        ChangeRequest& request = it->second;

        if (!request.hasImpactAnalysis) {
            throw logic_error(
                "Cannot approve without impact analysis."
            );
        }

        if (request.status != ChangeStatus::UnderReview) {
            throw logic_error(
                "Only changes under review can be approved."
            );
        }

        request.status = ChangeStatus::Approved;
        request.decision = rationale;
        request.decisionDate = currentDate();

        decisions.push_back({
            changeId,
            ChangeStatus::Approved,
            authority,
            rationale,
            currentDate()
        });

        audit(
            authority,
            "APPROVE_CHANGE",
            changeId,
            rationale
        );
    }

    void reject(
        const string& changeId,
        const string& authority,
        const string& rationale
    ) {
        auto it = changeRequests.find(changeId);

        if (it == changeRequests.end()) {
            throw out_of_range(
                "Unknown change request: " + changeId
            );
        }

        ChangeRequest& request = it->second;

        if (request.status != ChangeStatus::UnderReview) {
            throw logic_error(
                "Only changes under review can be rejected."
            );
        }

        request.status = ChangeStatus::Rejected;
        request.decision = rationale;
        request.decisionDate = currentDate();

        decisions.push_back({
            changeId,
            ChangeStatus::Rejected,
            authority,
            rationale,
            currentDate()
        });

        audit(
            authority,
            "REJECT_CHANGE",
            changeId,
            rationale
        );
    }

    void implement(
        const string& changeId,
        const string& implementer
    ) {
        auto it = changeRequests.find(changeId);

        if (it == changeRequests.end()) {
            throw out_of_range(
                "Unknown change request: " + changeId
            );
        }

        ChangeRequest& request = it->second;

        if (request.status != ChangeStatus::Approved) {
            throw logic_error(
                "Only approved changes can be implemented."
            );
        }

        request.status = ChangeStatus::Implemented;
        request.implementationNotes =
            "Implemented by " + implementer +
            " on " + currentDate() + ".";

        audit(
            implementer,
            "IMPLEMENT_CHANGE",
            changeId,
            request.implementationNotes
        );
    }

    void rebaseline(
        const string& newVersion,
        const string& newDate
    ) {
        for (const auto& [id, request] : changeRequests) {
            (void)id;

            if (request.status == ChangeStatus::Approved) {
                throw logic_error(
                    "Cannot rebaseline while approved changes "
                    "remain unimplemented."
                );
            }
        }

        ScopeBaseline nextBaseline =
            baseline.clone(newVersion, newDate);

        for (const auto& [id, request] : changeRequests) {
            if (
                request.status != ChangeStatus::Implemented ||
                !request.hasImpactAnalysis
            ) {
                continue;
            }

            const string deliverableId = "CHG-" + id;

            if (!nextBaseline.hasDeliverable(deliverableId)) {
                Deliverable newDeliverable;

                newDeliverable.id = deliverableId;
                newDeliverable.name = request.title;
                newDeliverable.description =
                    request.description;
                newDeliverable.estimatedHours =
                    request.impact.resourceDeltaHours;
                newDeliverable.estimatedCost =
                    request.impact.costDelta;

                nextBaseline.mutableDeliverables().emplace(
                    deliverableId,
                    move(newDeliverable)
                );
            }
        }

        baseline = move(nextBaseline);

        audit(
            "change_control_board",
            "CREATE_BASELINE",
            newVersion,
            "New baseline created from implemented changes."
        );
    }

    void printReport() const {
        printSection("CONTROL REPORT");

        cout << "Baseline version: "
             << baseline.version << "\n";

        cout << "Baseline effort: "
             << fixed << setprecision(2)
             << baseline.totalHours()
             << " hours\n";

        cout << "Baseline cost: $"
             << fixed << setprecision(2)
             << baseline.totalCost()
             << "\n";

        map<ChangeStatus, int> counts;

        for (const auto& [id, request] : changeRequests) {
            (void)id;
            counts[request.status]++;
        }

        cout << "\nChange status counts:\n";

        for (const auto& [status, count] : counts) {
            cout << "  "
                 << toString(status)
                 << ": "
                 << count
                 << "\n";
        }

        double costDelta = 0;
        double scheduleDelta = 0;

        for (const auto& [id, request] : changeRequests) {
            (void)id;

            if (
                request.hasImpactAnalysis &&
                (
                    request.status == ChangeStatus::Approved ||
                    request.status == ChangeStatus::Implemented
                )
            ) {
                costDelta += request.impact.costDelta;
                scheduleDelta +=
                    request.impact.scheduleDeltaDays;
            }
        }

        cout << "\nApproved/implemented cost delta: $"
             << costDelta
             << "\n";

        cout << "Approved/implemented schedule delta: "
             << scheduleDelta
             << " days\n";

        cout << "Audit entries: "
             << auditLog.size()
             << "\n";
    }

    const map<string, ChangeRequest>& getChanges() const {
        return changeRequests;
    }
};


// ---------------------------------------------------------------------------
// 7. BASELINE FACTORY
// ---------------------------------------------------------------------------

ScopeBaseline createInitialBaseline() {
    map<string, Deliverable> deliverables;

    deliverables.emplace(
        "D-100",
        Deliverable{
            "D-100",
            "Customer Web Portal",
            "Responsive account-management portal.",
            320,
            32000,
            ScopeStatus::Planned,
            {}
        }
    );

    deliverables.emplace(
        "D-200",
        Deliverable{
            "D-200",
            "Authentication Service",
            "Secure identity and session management.",
            180,
            24000,
            ScopeStatus::Planned,
            {}
        }
    );

    deliverables.emplace(
        "D-300",
        Deliverable{
            "D-300",
            "Reporting Module",
            "Operational and management reporting.",
            220,
            20000,
            ScopeStatus::Planned,
            {}
        }
    );

    map<string, Requirement> requirements;

    requirements.emplace(
        "REQ-001",
        Requirement{
            "REQ-001",
            "Customer authentication",
            "Users must authenticate securely.",
            Priority::Critical,
            {
                "Valid users can sign in.",
                "Invalid credentials are rejected.",
                "Sessions expire according to policy."
            },
            {"D-200"}
        }
    );

    requirements.emplace(
        "REQ-002",
        Requirement{
            "REQ-002",
            "Account dashboard",
            "Customers can view account information.",
            Priority::High,
            {
                "Account information is displayed.",
                "Unauthorized information is not exposed."
            },
            {"D-100"}
        }
    );

    requirements.emplace(
        "REQ-003",
        Requirement{
            "REQ-003",
            "Management reports",
            "Managers can access operational reports.",
            Priority::Medium,
            {
                "Reports can be generated.",
                "Approved business metrics are used."
            },
            {"D-300"}
        }
    );

    for (auto& [deliverableId, deliverable] : deliverables) {
        for (const auto& [requirementId, requirement] :
             requirements) {
            if (requirement.deliverableIds.contains(
                    deliverableId)) {
                deliverable.requirementIds.insert(requirementId);
            }
        }
    }

    return ScopeBaseline(
        "BL-1.0",
        "2026-09-01",
        move(deliverables),
        move(requirements)
    );
}


// ---------------------------------------------------------------------------
// 8. CHANGE CLASSIFICATION
// ---------------------------------------------------------------------------

string classifyChange(
    const ImpactAnalysis& impact,
    Priority priority
) {
    if (priority == Priority::Critical) {
        return "Major";
    }

    if (
        impact.costDelta > 10000 ||
        impact.scheduleDeltaDays > 10 ||
        impact.averageRisk() >= 8
    ) {
        return "Major";
    }

    if (
        impact.costDelta > 2500 ||
        impact.scheduleDeltaDays > 3 ||
        impact.averageRisk() >= 5
    ) {
        return "Significant";
    }

    return "Minor";
}


// ---------------------------------------------------------------------------
// 9. SCOPE-CREEP DETECTION
// ---------------------------------------------------------------------------

struct WorkItem {
    string id;
    string name;
    string baselineDeliverableId;
    double estimatedHours{};
    bool authorized{true};
};


vector<WorkItem> detectScopeCreep(
    const vector<WorkItem>& workItems,
    const ScopeBaseline& baseline
) {
    vector<WorkItem> uncontrolled;

    for (const auto& item : workItems) {
        if (
            !item.authorized ||
            !baseline.hasDeliverable(
                item.baselineDeliverableId
            )
        ) {
            uncontrolled.push_back(item);
        }
    }

    return uncontrolled;
}


// ---------------------------------------------------------------------------
// 10. COMPLETE CASE STUDY
// ---------------------------------------------------------------------------

void runCaseStudy() {
    printSection("1. INDUSTRY-STYLE CASE STUDY");

    ScopeControlEngine engine(
        createInitialBaseline()
    );

    cout << "Initial baseline: "
         << engine.getBaseline().version
         << "\n";

    cout << "Initial effort: "
         << engine.getBaseline().totalHours()
         << " hours\n";

    cout << "Initial cost: $"
         << engine.getBaseline().totalCost()
         << "\n";

    // -----------------------------------------------------------------------
    // Small change
    // -----------------------------------------------------------------------

    ChangeRequest smallChange;

    smallChange.id = "CR-001";
    smallChange.title = "Add customer profile photo";
    smallChange.requester = "Product Owner";
    smallChange.description =
        "Allow customers to upload a profile image.";
    smallChange.reason =
        "Customer usability improvement.";
    smallChange.priority = Priority::Low;
    smallChange.proposedDate = currentDate();
    smallChange.affectedRequirementIds.insert("REQ-002");
    smallChange.affectedDeliverableIds.insert("D-100");

    engine.submitChange(smallChange);

    ImpactAnalysis smallImpact{
        1,
        2,
        1200,
        16,
        2,
        2,
        1,
        2,
        {"Image storage configuration"},
        {"Maximum image size is enforced"}
    };

    engine.analyzeChange(
        "CR-001",
        smallImpact
    );

    cout << "\nCR-001 classification: "
         << classifyChange(
                smallImpact,
                Priority::Low
            )
         << "\n";

    cout << "CR-001 routing: "
         << engine.routingRecommendation("CR-001")
         << "\n";

    engine.approve(
        "CR-001",
        "Project Manager",
        "Small controlled enhancement."
    );

    engine.implement(
        "CR-001",
        "Development Team"
    );

    // -----------------------------------------------------------------------
    // Major change
    // -----------------------------------------------------------------------

    ChangeRequest majorChange;

    majorChange.id = "CR-002";
    majorChange.title = "Add external payment gateway";
    majorChange.requester = "Business Sponsor";
    majorChange.description =
        "Enable customers to pay outstanding balances online.";
    majorChange.reason =
        "Business requirement introduced after baseline approval.";
    majorChange.priority = Priority::High;
    majorChange.proposedDate = currentDate();
    majorChange.affectedRequirementIds.insert("REQ-002");
    majorChange.affectedDeliverableIds.insert("D-100");
    majorChange.affectedDeliverableIds.insert("D-200");

    engine.submitChange(majorChange);

    ImpactAnalysis majorImpact{
        4,
        12,
        18000,
        160,
        6,
        7,
        9,
        7,
        {
            "Payment provider contract",
            "Security review",
            "Financial reconciliation"
        },
        {
            "Provider API remains available",
            "Compliance obligations are satisfied"
        }
    };

    engine.analyzeChange(
        "CR-002",
        majorImpact
    );

    cout << "\nCR-002 classification: "
         << classifyChange(
                majorImpact,
                Priority::High
            )
         << "\n";

    cout << "CR-002 routing: "
         << engine.routingRecommendation("CR-002")
         << "\n";

    engine.approve(
        "CR-002",
        "Change Control Board",
        "Approved after financial, schedule, security, "
        "compliance, and operational analysis."
    );

    engine.implement(
        "CR-002",
        "Payments Workstream"
    );

    // -----------------------------------------------------------------------
    // Rejected change
    // -----------------------------------------------------------------------

    ChangeRequest rejectedChange;

    rejectedChange.id = "CR-003";
    rejectedChange.title =
        "Add animated dashboard background";
    rejectedChange.requester = "Designer";
    rejectedChange.description =
        "Add continuously animated decorative effects.";
    rejectedChange.reason =
        "Visual enhancement.";
    rejectedChange.priority = Priority::Low;
    rejectedChange.proposedDate = currentDate();
    rejectedChange.affectedRequirementIds.insert("REQ-002");
    rejectedChange.affectedDeliverableIds.insert("D-100");

    engine.submitChange(rejectedChange);

    ImpactAnalysis rejectedImpact{
        1,
        3,
        2000,
        24,
        4,
        5,
        1,
        5,
        {"Browser rendering performance"},
        {"Target browsers support animation"}
    };

    engine.analyzeChange(
        "CR-003",
        rejectedImpact
    );

    engine.reject(
        "CR-003",
        "Project Manager",
        "Not required by approved objectives and adds "
        "avoidable complexity."
    );

    engine.printReport();

    engine.rebaseline(
        "BL-2.0",
        currentDate()
    );

    cout << "\nNew baseline: "
         << engine.getBaseline().version
         << "\n";

    cout << "New effort: "
         << engine.getBaseline().totalHours()
         << " hours\n";

    cout << "New cost: $"
         << engine.getBaseline().totalCost()
         << "\n";
}


// ---------------------------------------------------------------------------
// 11. TRACEABILITY DEMONSTRATION
// ---------------------------------------------------------------------------

void demonstrateTraceability() {
    printSection("2. REQUIREMENTS TRACEABILITY");

    TraceabilityMatrix matrix;

    matrix.addTest(
        "REQ-001",
        "TEST-AUTH-001"
    );

    matrix.addTest(
        "REQ-001",
        "TEST-AUTH-002"
    );

    matrix.addTest(
        "REQ-002",
        "TEST-DASH-001"
    );

    matrix.addChange(
        "REQ-002",
        "CR-001"
    );

    matrix.addChange(
        "REQ-002",
        "CR-002"
    );

    matrix.printReport();
}


// ---------------------------------------------------------------------------
// 12. SCOPE CREEP DEMONSTRATION
// ---------------------------------------------------------------------------

void demonstrateScopeCreep() {
    printSection("3. SCOPE CREEP DETECTION");

    ScopeBaseline baseline =
        createInitialBaseline();

    vector<WorkItem> workItems{
        {
            "W-001",
            "Build login form",
            "D-200",
            20,
            true
        },
        {
            "W-002",
            "Add social-media dashboard export",
            "",
            12,
            false
        },
        {
            "W-003",
            "Improve report query",
            "D-300",
            18,
            true
        },
        {
            "W-004",
            "Build unrequested loyalty system",
            "",
            80,
            false
        }
    };

    const vector<WorkItem> uncontrolled =
        detectScopeCreep(
            workItems,
            baseline
        );

    for (const auto& item : uncontrolled) {
        cout << item.id
             << ": "
             << item.name
             << " ("
             << item.estimatedHours
             << " hours)\n";
    }
}


// ---------------------------------------------------------------------------
// 13. ERROR-HANDLING DEMONSTRATION
// ---------------------------------------------------------------------------

void demonstrateFailures() {
    printSection("4. EDGE CASES AND FAILURE CONDITIONS");

    ScopeControlEngine engine(
        createInitialBaseline()
    );

    ChangeRequest duplicate;

    duplicate.id = "ERR-001";
    duplicate.title = "Duplicate request";
    duplicate.requester = "Tester";
    duplicate.description = "Testing duplicate protection.";
    duplicate.reason = "Validation";
    duplicate.priority = Priority::Low;

    engine.submitChange(duplicate);

    try {
        engine.submitChange(duplicate);
    } catch (const exception& error) {
        cout << "Duplicate prevented: "
             << error.what()
             << "\n";
    }

    ChangeRequest invalidReference;

    invalidReference.id = "ERR-002";
    invalidReference.title = "Invalid reference";
    invalidReference.requester = "Tester";
    invalidReference.description =
        "Testing requirement validation.";
    invalidReference.reason = "Validation";
    invalidReference.priority = Priority::Low;
    invalidReference.affectedRequirementIds.insert(
        "REQ-999"
    );

    try {
        engine.submitChange(invalidReference);
    } catch (const exception& error) {
        cout << "Invalid requirement prevented: "
             << error.what()
             << "\n";
    }

    ChangeRequest missingAnalysis;

    missingAnalysis.id = "ERR-003";
    missingAnalysis.title =
        "Approval without analysis";
    missingAnalysis.requester = "Tester";
    missingAnalysis.description =
        "Testing governance enforcement.";
    missingAnalysis.reason = "Validation";
    missingAnalysis.priority = Priority::Medium;

    engine.submitChange(missingAnalysis);

    try {
        engine.approve(
            "ERR-003",
            "Project Manager",
            "Invalid attempt."
        );
    } catch (const exception& error) {
        cout << "Approval without analysis prevented: "
             << error.what()
             << "\n";
    }
}


// ---------------------------------------------------------------------------
// 14. PERFORMANCE CHARACTERISTICS
// ---------------------------------------------------------------------------

void demonstratePerformance() {
    printSection("5. PERFORMANCE CONSIDERATIONS");

    /*
        std::map provides O(log n) lookup and ordered keys.

        For very large change-management systems, an unordered_map could
        provide approximately O(1) average lookup, at the cost of ordering
        and different memory behavior.

        This example uses std::map because deterministic ordering is useful
        for audit-oriented reports.
    */

    constexpr int itemCount = 100000;

    map<string, int> requirementIndex;

    for (int i = 0; i < itemCount; ++i) {
        requirementIndex.emplace(
            "REQ-" + to_string(i),
            i
        );
    }

    const auto start =
        chrono::high_resolution_clock::now();

    int found = 0;

    for (int i = 0; i < itemCount; ++i) {
        if (
            requirementIndex.find(
                "REQ-" + to_string(i)
            ) != requirementIndex.end()
        ) {
            ++found;
        }
    }

    const auto end =
        chrono::high_resolution_clock::now();

    const auto elapsed =
        chrono::duration_cast<
            chrono::microseconds
        >(end - start);

    cout << "Indexed lookups: "
         << found
         << "\n";

    cout << "Elapsed time: "
         << elapsed.count()
         << " microseconds\n";

    cout << "std::map lookup complexity: O(log n)\n";
}


// ---------------------------------------------------------------------------
// 15. AUTOMATED TESTS
// ---------------------------------------------------------------------------

void runTests() {
    printSection("6. AUTOMATED TESTS");

    ScopeBaseline baseline =
        createInitialBaseline();

    assert(
        abs(
            baseline.totalHours() - 720.0
        ) < 0.0001
    );

    assert(
        abs(
            baseline.totalCost() - 76000.0
        ) < 0.0001
    );

    ScopeControlEngine engine(
        createInitialBaseline()
    );

    ChangeRequest request;

    request.id = "TEST-001";
    request.title = "Test change";
    request.requester = "Tester";
    request.description =
        "Valid automated test change.";
    request.reason = "Unit testing";
    request.priority = Priority::Low;

    engine.submitChange(request);

    bool approvalBlocked = false;

    try {
        engine.approve(
            "TEST-001",
            "Manager",
            "Should fail."
        );
    } catch (const exception&) {
        approvalBlocked = true;
    }

    assert(approvalBlocked);

    ImpactAnalysis impact{
        1,
        1,
        1000,
        10,
        1,
        1,
        1,
        1,
        {},
        {}
    };

    engine.analyzeChange(
        "TEST-001",
        impact
    );

    engine.approve(
        "TEST-001",
        "Manager",
        "Approved for automated testing."
    );

    engine.implement(
        "TEST-001",
        "Developer"
    );

    const auto& stored =
        engine.getChanges().at("TEST-001");

    assert(
        stored.status ==
        ChangeStatus::Implemented
    );

    cout << "All C++ tests passed.\n";
}


// ---------------------------------------------------------------------------
// 16. MAIN
// ---------------------------------------------------------------------------

int main() {
    try {
        cout << R"(
SCOPE CONTROL: MANAGING CHANGES TO SCOPE
=========================================

Industry-style case study covering:
- Scope definition
- Scope baseline
- Requirements
- Deliverables
- Change requests
- Impact analysis
- Governance
- Approval and rejection
- Implementation
- Rebaselining
- Traceability
- Scope-creep detection
- Validation
- Performance
- Testing
)";

        runCaseStudy();
        demonstrateTraceability();
        demonstrateScopeCreep();
        demonstrateFailures();
        demonstratePerformance();
        runTests();

        printSection("7. GOVERNANCE PRINCIPLES");

        const vector<string> principles{
            "Define scope before controlling changes.",
            "Establish an approved baseline.",
            "Document every proposed change.",
            "Analyze scope, cost, schedule, resources, quality, "
            "risk, compliance, and dependencies.",
            "Separate analysis from approval.",
            "Do not implement unapproved scope.",
            "Record approvals and rejections.",
            "Maintain traceability.",
            "Detect unauthorized work.",
            "Rebaseline only after controlled implementation.",
            "Protect baseline history from silent modification."
        };

        for (size_t i = 0; i < principles.size(); ++i) {
            cout << i + 1
                 << ". "
                 << principles[i]
                 << "\n";
        }

        cout << "\nProgram completed successfully.\n";
        return 0;
    }
    catch (const exception& error) {
        cerr << "\nFatal error: "
             << error.what()
             << "\n";
        return 1;
    }
}
