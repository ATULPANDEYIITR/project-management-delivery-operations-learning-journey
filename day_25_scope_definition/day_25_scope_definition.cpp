/*
 * Creating a Clear Project Scope
 *
 * C++17 industry-style case study:
 * Employee Leave Management System
 *
 * The program demonstrates how project scope can be converted into:
 * - Objectives
 * - Requirements
 * - Deliverables
 * - Acceptance criteria
 * - Assumptions
 * - Constraints
 * - Dependencies
 * - Work Breakdown Structure
 * - Scope baseline
 * - Change requests
 * - Impact analysis
 * - Traceability
 * - Scope-creep detection
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic project_scope.cpp -o project_scope
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


// -----------------------------------------------------------------------------
// ENUMERATIONS
// -----------------------------------------------------------------------------

enum class Priority {
    Must,
    Should,
    Could,
    Wont
};


string priorityToString(Priority priority) {
    switch (priority) {
        case Priority::Must:
            return "Must";
        case Priority::Should:
            return "Should";
        case Priority::Could:
            return "Could";
        case Priority::Wont:
            return "Won't";
    }

    return "Unknown";
}


enum class ChangeStatus {
    Proposed,
    Analyzing,
    Approved,
    Rejected,
    Implemented
};


string statusToString(ChangeStatus status) {
    switch (status) {
        case ChangeStatus::Proposed:
            return "Proposed";
        case ChangeStatus::Analyzing:
            return "Analyzing";
        case ChangeStatus::Approved:
            return "Approved";
        case ChangeStatus::Rejected:
            return "Rejected";
        case ChangeStatus::Implemented:
            return "Implemented";
    }

    return "Unknown";
}


// -----------------------------------------------------------------------------
// DOMAIN OBJECTS
// -----------------------------------------------------------------------------

struct Objective {
    string id;
    string description;
    string metric;
    string target;

    bool valid() const {
        return !id.empty() &&
               !description.empty() &&
               !metric.empty() &&
               !target.empty();
    }
};


struct Requirement {
    string id;
    string description;
    Priority priority;
    vector<string> acceptanceCriteria;
    string source;
    bool inScope = true;

    bool testable() const {
        return !acceptanceCriteria.empty();
    }
};


struct Deliverable {
    string id;
    string name;
    string description;
    vector<string> acceptanceCriteria;
    string owner;

    bool valid() const {
        return !id.empty() &&
               !name.empty() &&
               !description.empty() &&
               !acceptanceCriteria.empty() &&
               !owner.empty();
    }
};


struct Constraint {
    string category;
    string description;
};


struct Assumption {
    string description;
    string validationMethod;
    bool validated = false;
};


struct Dependency {
    string name;
    string description;
    string owner;
    string requiredBy;
};


// -----------------------------------------------------------------------------
// WORK BREAKDOWN STRUCTURE
// -----------------------------------------------------------------------------

class ScopeItem {
private:
    vector<ScopeItem> children;

public:
    string id;
    string name;
    string description;
    double estimatedHours;
    optional<string> parentId;

    ScopeItem(
        string itemId,
        string itemName,
        string itemDescription,
        double hours = 0.0
    )
        : id(std::move(itemId)),
          name(std::move(itemName)),
          description(std::move(itemDescription)),
          estimatedHours(hours) {
        if (estimatedHours < 0.0) {
            throw invalid_argument("Estimated hours cannot be negative.");
        }
    }

    void addChild(ScopeItem child) {
        child.parentId = id;
        children.push_back(std::move(child));
    }

    const vector<ScopeItem>& getChildren() const {
        return children;
    }

    bool isLeaf() const {
        return children.empty();
    }

    double totalHours() const {
        double total = estimatedHours;

        for (const auto& child : children) {
            total += child.totalHours();
        }

        return total;
    }

    void print(int depth = 0) const {
        cout << string(depth * 2, ' ')
             << id << " " << name
             << " [" << fixed << setprecision(1)
             << estimatedHours << "h]\n";

        for (const auto& child : children) {
            child.print(depth + 1);
        }
    }

    void collectLeaves(vector<const ScopeItem*>& result) const {
        if (isLeaf()) {
            result.push_back(this);
            return;
        }

        for (const auto& child : children) {
            child.collectLeaves(result);
        }
    }
};


// -----------------------------------------------------------------------------
// SCOPE STATEMENT
// -----------------------------------------------------------------------------

class ScopeStatement {
public:
    string projectName;
    string purpose;
    vector<Objective> objectives;
    vector<Deliverable> deliverables;
    vector<string> inclusions;
    vector<string> exclusions;
    vector<Assumption> assumptions;
    vector<Constraint> constraints;
    vector<Dependency> dependencies;

    vector<string> validate() const {
        vector<string> problems;

        if (projectName.empty()) {
            problems.push_back("Project name is missing.");
        }

        if (purpose.empty()) {
            problems.push_back("Project purpose is missing.");
        }

        if (objectives.empty()) {
            problems.push_back("No objectives defined.");
        }

        if (deliverables.empty()) {
            problems.push_back("No deliverables defined.");
        }

        if (inclusions.empty()) {
            problems.push_back("No inclusions defined.");
        }

        if (exclusions.empty()) {
            problems.push_back("No exclusions defined.");
        }

        for (const auto& deliverable : deliverables) {
            if (!deliverable.valid()) {
                problems.push_back(
                    "Invalid deliverable: " + deliverable.id
                );
            }
        }

        return problems;
    }
};


// -----------------------------------------------------------------------------
// REQUIREMENT TRACEABILITY
// -----------------------------------------------------------------------------

struct TraceRecord {
    string requirementId;
    string deliverableId;
    string testId;
    bool accepted;
};


vector<TraceRecord> buildTraceability(
    const vector<Requirement>& requirements,
    const vector<Deliverable>& deliverables
) {
    if (deliverables.empty()) {
        throw invalid_argument(
            "At least one deliverable is required for traceability."
        );
    }

    vector<TraceRecord> records;
    int testNumber = 1;

    for (const auto& requirement : requirements) {
        if (!requirement.inScope) {
            continue;
        }

        const auto index =
            static_cast<size_t>((testNumber - 1) % deliverables.size());

        records.push_back({
            requirement.id,
            deliverables[index].id,
            "TEST-" + to_string(testNumber),
            false
        });

        ++testNumber;
    }

    return records;
}


// -----------------------------------------------------------------------------
// CHANGE REQUEST
// -----------------------------------------------------------------------------

struct ChangeRequest {
    string id;
    string description;
    string reason;
    string requestedBy;
    double estimatedHours;
    double estimatedCost;
    int scheduleDays;
    vector<string> affectedDeliverables;
    ChangeStatus status = ChangeStatus::Proposed;

    double impactScore() const {
        return estimatedHours * 0.4
             + estimatedCost * 0.001
             + scheduleDays * 2.0
             + affectedDeliverables.size() * 5.0;
    }
};


struct ChangeAnalysis {
    string changeId;
    double additionalHours;
    double additionalCost;
    double effortIncreasePercentage;
    int scheduleDays;
    double impactScore;
};


ChangeAnalysis analyzeChange(
    const ChangeRequest& request,
    double baselineHours,
    double hourlyRate
) {
    if (baselineHours < 0.0) {
        throw invalid_argument("Baseline hours cannot be negative.");
    }

    if (hourlyRate < 0.0) {
        throw invalid_argument("Hourly rate cannot be negative.");
    }

    const double laborCost =
        request.estimatedHours * hourlyRate;

    const double totalAdditionalCost =
        laborCost + request.estimatedCost;

    const double percentage =
        baselineHours == 0.0
            ? 0.0
            : request.estimatedHours / baselineHours * 100.0;

    return {
        request.id,
        request.estimatedHours,
        totalAdditionalCost,
        percentage,
        request.scheduleDays,
        request.impactScore()
    };
}


// -----------------------------------------------------------------------------
// STRING UTILITIES FOR SIMPLE SCOPE COMPARISON
// -----------------------------------------------------------------------------

string normalize(string value) {
    transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](unsigned char character) {
            if (isalnum(character)) {
                return static_cast<char>(tolower(character));
            }

            return ' ';
        }
    );

    return value;
}


set<string> words(const string& value) {
    set<string> result;
    string normalized = normalize(value);
    stringstream stream(normalized);
    string word;

    while (stream >> word) {
        result.insert(word);
    }

    return result;
}


bool likelyScopeCreep(
    const string& request,
    const vector<string>& approvedItems,
    vector<string>& relatedItems
) {
    const auto requestWords = words(request);

    for (const auto& approvedItem : approvedItems) {
        const auto approvedWords = words(approvedItem);

        size_t overlap = 0;

        for (const auto& word : requestWords) {
            if (approvedWords.count(word) > 0) {
                ++overlap;
            }
        }

        if (overlap >= 2) {
            relatedItems.push_back(approvedItem);
        }
    }

    return relatedItems.empty();
}


// -----------------------------------------------------------------------------
// ACCEPTANCE TESTING
// -----------------------------------------------------------------------------

struct AcceptanceResult {
    bool accepted;
    vector<string> failedCriteria;
};


AcceptanceResult validateDeliverable(
    const Deliverable& deliverable,
    const map<string, bool>& observations
) {
    vector<string> failures;

    for (const auto& criterion : deliverable.acceptanceCriteria) {
        auto iterator = observations.find(criterion);

        if (iterator == observations.end() || !iterator->second) {
            failures.push_back(criterion);
        }
    }

    return {
        failures.empty(),
        failures
    };
}


// -----------------------------------------------------------------------------
// CAPACITY ESTIMATION
// -----------------------------------------------------------------------------

double estimateDuration(
    double effortHours,
    int teamSize,
    double productiveHoursPerDay
) {
    if (effortHours < 0.0) {
        throw invalid_argument("Effort cannot be negative.");
    }

    if (teamSize <= 0) {
        throw invalid_argument("Team size must be positive.");
    }

    if (productiveHoursPerDay <= 0.0) {
        throw invalid_argument(
            "Productive hours per day must be positive."
        );
    }

    /*
     * This is a capacity estimate, not a schedule guarantee.
     * Parallel work, dependencies, reviews, rework, meetings, holidays,
     * resource constraints, and critical-path structure affect real schedules.
     */
    return effortHours /
           (static_cast<double>(teamSize) * productiveHoursPerDay);
}


// -----------------------------------------------------------------------------
// PROJECT FACTORY
// -----------------------------------------------------------------------------

ScopeStatement buildScopeStatement() {
    ScopeStatement scope;

    scope.projectName =
        "Employee Leave Management System";

    scope.purpose =
        "Digitize employee leave submission, approval, tracking, "
        "and standard reporting.";

    scope.objectives = {
        {
            "OBJ-001",
            "Process all pilot leave requests digitally.",
            "Percentage of pilot requests processed digitally",
            "100%"
        },
        {
            "OBJ-002",
            "Provide traceable request status.",
            "Requests with visible status",
            "100%"
        }
    };

    scope.deliverables = {
        {
            "DEL-001",
            "Requirements Specification",
            "Approved functional and non-functional requirements.",
            {
                "Business owner approves the requirements.",
                "Mandatory requirements have acceptance criteria."
            },
            "Business Analyst"
        },
        {
            "DEL-002",
            "Leave Request Module",
            "Employee leave request functionality.",
            {
                "Valid requests can be submitted.",
                "Invalid date ranges are rejected."
            },
            "Application Team"
        },
        {
            "DEL-003",
            "Approval Workflow",
            "Manager approval and rejection workflow.",
            {
                "Managers can approve requests.",
                "Managers can reject requests.",
                "Employees can see resulting status."
            },
            "Application Team"
        },
        {
            "DEL-004",
            "Standard Reports",
            "Approved reports for leave activity.",
            {
                "Monthly leave report can be generated.",
                "Reports can filter by department and date."
            },
            "Reporting Team"
        }
    };

    scope.inclusions = {
        "Employee leave request submission",
        "Manager approval and rejection",
        "Request status tracking",
        "Standard leave reports",
        "Approved authentication mechanism",
        "User acceptance testing",
        "Production deployment"
    };

    scope.exclusions = {
        "Payroll processing",
        "Recruitment functionality",
        "Performance management",
        "Custom native mobile application",
        "Unapproved third-party notification platforms"
    };

    scope.assumptions = {
        {
            "HR provides current leave rules.",
            "Review the approved HR policy."
        },
        {
            "Employees have organizational accounts.",
            "Confirm identity-provider access."
        }
    };

    scope.constraints = {
        {
            "Budget",
            "Pilot budget is fixed."
        },
        {
            "Schedule",
            "Pilot target is 60 calendar days."
        },
        {
            "Technology",
            "Only approved organizational systems may be integrated."
        }
    };

    scope.dependencies = {
        {
            "Identity Provider",
            "Authentication is required before user acceptance testing.",
            "IT Infrastructure",
            "User acceptance testing"
        },
        {
            "HR Policy",
            "Current leave rules are required for requirements validation.",
            "HR",
            "Requirements approval"
        }
    };

    return scope;
}


vector<Requirement> buildRequirements() {
    return {
        {
            "REQ-001",
            "Users shall submit leave requests containing employee ID, "
            "leave type, start date, and end date.",
            Priority::Must,
            {
                "Employee ID is mandatory.",
                "End date cannot precede start date.",
                "Valid requests receive a unique request ID."
            },
            "HR Process Owner",
            true
        },
        {
            "REQ-002",
            "Managers shall approve or reject pending leave requests.",
            Priority::Must,
            {
                "Pending requests can be approved.",
                "Pending requests can be rejected.",
                "The decision is recorded."
            },
            "HR Process Owner",
            true
        },
        {
            "REQ-003",
            "Employees shall see the current request status.",
            Priority::Must,
            {
                "Submitted status is visible.",
                "Approved status is visible.",
                "Rejected status is visible."
            },
            "Employee Representative",
            true
        },
        {
            "REQ-004",
            "The dashboard should be modern and attractive.",
            Priority::Should,
            {},
            "Stakeholder",
            true
        }
    };
}


ScopeItem buildWbs() {
    ScopeItem root(
        "1.0",
        "Employee Leave Management System",
        "Complete project scope"
    );

    ScopeItem discovery(
        "1.1",
        "Requirements and Discovery",
        "Define approved requirements"
    );

    discovery.addChild(
        ScopeItem(
            "1.1.1",
            "Stakeholder Interviews",
            "Collect stakeholder needs",
            12.0
        )
    );

    discovery.addChild(
        ScopeItem(
            "1.1.2",
            "Requirements Specification",
            "Document requirements",
            16.0
        )
    );

    ScopeItem design(
        "1.2",
        "Solution Design",
        "Design approved solution"
    );

    design.addChild(
        ScopeItem(
            "1.2.1",
            "Architecture Design",
            "Define system components",
            14.0
        )
    );

    design.addChild(
        ScopeItem(
            "1.2.2",
            "Interface Design",
            "Design user workflows",
            18.0
        )
    );

    ScopeItem implementation(
        "1.3",
        "Implementation",
        "Build approved capabilities"
    );

    implementation.addChild(
        ScopeItem(
            "1.3.1",
            "Leave Requests",
            "Implement leave request workflow",
            28.0
        )
    );

    implementation.addChild(
        ScopeItem(
            "1.3.2",
            "Approval Workflow",
            "Implement manager approval workflow",
            24.0
        )
    );

    implementation.addChild(
        ScopeItem(
            "1.3.3",
            "Standard Reports",
            "Implement standard reports",
            20.0
        )
    );

    ScopeItem testing(
        "1.4",
        "Testing and Acceptance",
        "Verify approved requirements"
    );

    testing.addChild(
        ScopeItem(
            "1.4.1",
            "Functional Testing",
            "Verify functional requirements",
            20.0
        )
    );

    testing.addChild(
        ScopeItem(
            "1.4.2",
            "User Acceptance Testing",
            "Conduct business acceptance",
            16.0
        )
    );

    ScopeItem deployment(
        "1.5",
        "Deployment",
        "Release approved solution"
    );

    deployment.addChild(
        ScopeItem(
            "1.5.1",
            "Production Deployment",
            "Deploy approved release",
            10.0
        )
    );

    root.addChild(std::move(discovery));
    root.addChild(std::move(design));
    root.addChild(std::move(implementation));
    root.addChild(std::move(testing));
    root.addChild(std::move(deployment));

    return root;
}


// -----------------------------------------------------------------------------
// MAIN CASE STUDY
// -----------------------------------------------------------------------------

int main() {
    try {
        cout << string(72, '=') << '\n';
        cout << "CREATING A CLEAR PROJECT SCOPE\n";
        cout << string(72, '=') << "\n\n";

        cout << "CASE STUDY\n";
        cout << "Project: Employee Leave Management System\n\n";

        ScopeStatement scope = buildScopeStatement();
        vector<Requirement> requirements = buildRequirements();

        // ---------------------------------------------------------------------
        // Scope statement
        // ---------------------------------------------------------------------

        cout << "PROJECT PURPOSE\n";
        cout << scope.purpose << "\n\n";

        cout << "OBJECTIVES\n";
        for (const auto& objective : scope.objectives) {
            cout << objective.id << ": "
                 << objective.description << '\n'
                 << "  Metric: " << objective.metric << '\n'
                 << "  Target: " << objective.target << '\n';
        }

        cout << "\nIN SCOPE\n";
        for (const auto& item : scope.inclusions) {
            cout << "  + " << item << '\n';
        }

        cout << "\nOUT OF SCOPE\n";
        for (const auto& item : scope.exclusions) {
            cout << "  - " << item << '\n';
        }

        // ---------------------------------------------------------------------
        // Scope quality validation
        // ---------------------------------------------------------------------

        cout << "\nSCOPE VALIDATION\n";
        cout << string(72, '-') << '\n';

        const auto scopeProblems = scope.validate();

        if (scopeProblems.empty()) {
            cout << "No structural scope problems detected.\n";
        } else {
            for (const auto& problem : scopeProblems) {
                cout << "  - " << problem << '\n';
            }
        }

        // ---------------------------------------------------------------------
        // Requirements
        // ---------------------------------------------------------------------

        cout << "\nREQUIREMENTS\n";
        cout << string(72, '-') << '\n';

        for (const auto& requirement : requirements) {
            cout << requirement.id << " ["
                 << priorityToString(requirement.priority)
                 << "]\n";
            cout << "  " << requirement.description << '\n';
            cout << "  Testable: "
                 << (requirement.testable() ? "Yes" : "No")
                 << '\n';
            cout << "  Source: " << requirement.source << '\n';
        }

        // ---------------------------------------------------------------------
        // Work Breakdown Structure
        // ---------------------------------------------------------------------

        ScopeItem wbs = buildWbs();

        cout << "\nWORK BREAKDOWN STRUCTURE\n";
        cout << string(72, '-') << '\n';

        wbs.print();

        const double baselineHours = wbs.totalHours();

        vector<const ScopeItem*> workPackages;
        wbs.collectLeaves(workPackages);

        cout << "\nWork packages: "
             << workPackages.size() << '\n';

        cout << "Baseline effort: "
             << fixed << setprecision(1)
             << baselineHours << " hours\n";

        // ---------------------------------------------------------------------
        // Traceability
        // ---------------------------------------------------------------------

        cout << "\nREQUIREMENT TRACEABILITY\n";
        cout << string(72, '-') << '\n';

        const auto traceability =
            buildTraceability(requirements, scope.deliverables);

        for (const auto& record : traceability) {
            cout << record.requirementId
                 << " -> " << record.deliverableId
                 << " -> " << record.testId
                 << " -> accepted="
                 << (record.accepted ? "true" : "false")
                 << '\n';
        }

        // ---------------------------------------------------------------------
        // Acceptance testing
        // ---------------------------------------------------------------------

        cout << "\nACCEPTANCE TESTING\n";
        cout << string(72, '-') << '\n';

        const Deliverable& workflow = scope.deliverables[2];

        map<string, bool> observations = {
            {"Managers can approve requests.", true},
            {"Managers can reject requests.", true},
            {"Employees can see resulting status.", false}
        };

        const auto acceptance =
            validateDeliverable(workflow, observations);

        cout << "Accepted: "
             << (acceptance.accepted ? "Yes" : "No")
             << '\n';

        for (const auto& failure : acceptance.failedCriteria) {
            cout << "  Failed: " << failure << '\n';
        }

        // ---------------------------------------------------------------------
        // Change request and impact analysis
        // ---------------------------------------------------------------------

        cout << "\nCHANGE CONTROL\n";
        cout << string(72, '-') << '\n';

        ChangeRequest change{
            "CR-001",
            "Add mobile push notifications for leave approvals.",
            "Stakeholders requested real-time approval alerts.",
            "HR Director",
            24.0,
            500.0,
            3,
            {"DEL-003"}
        };

        const auto analysis =
            analyzeChange(change, baselineHours, 45.0);

        cout << "Change: " << change.description << '\n';
        cout << "Status: " << statusToString(change.status) << '\n';
        cout << "Additional hours: "
             << analysis.additionalHours << '\n';
        cout << "Additional cost: "
             << analysis.additionalCost << '\n';
        cout << "Effort increase: "
             << analysis.effortIncreasePercentage
             << "%\n";
        cout << "Schedule impact: "
             << analysis.scheduleDays
             << " day(s)\n";
        cout << "Impact score: "
             << analysis.impactScore
             << "\n";

        cout << "\nThe change should be evaluated before implementation. "
             << "The numerical impact score is a planning aid rather than "
             << "a universal project-management standard.\n";

        // ---------------------------------------------------------------------
        // Scope creep
        // ---------------------------------------------------------------------

        cout << "\nSCOPE CREEP CHECK\n";
        cout << string(72, '-') << '\n';

        vector<string> proposedRequests = {
            "Add payroll calculation and tax deductions.",
            "Add manager approval and rejection.",
            "Add employee leave request submission."
        };

        for (const auto& request : proposedRequests) {
            vector<string> related;

            const bool likelyNewScope =
                likelyScopeCreep(
                    request,
                    scope.inclusions,
                    related
                );

            cout << "\nRequest: " << request << '\n';
            cout << "Likely new scope: "
                 << (likelyNewScope ? "Yes" : "No")
                 << '\n';

            cout << "Related approved scope: ";

            if (related.empty()) {
                cout << "None";
            } else {
                for (size_t i = 0; i < related.size(); ++i) {
                    if (i > 0) {
                        cout << ", ";
                    }

                    cout << related[i];
                }
            }

            cout << '\n';
        }

        // ---------------------------------------------------------------------
        // Capacity estimate
        // ---------------------------------------------------------------------

        cout << "\nCAPACITY ESTIMATION\n";
        cout << string(72, '-') << '\n';

        for (int teamSize : {1, 2, 4}) {
            const double duration =
                estimateDuration(
                    baselineHours,
                    teamSize,
                    6.0
                );

            cout << teamSize
                 << " person(s): "
                 << fixed << setprecision(2)
                 << duration
                 << " nominal working days\n";
        }

        // ---------------------------------------------------------------------
        // Edge conditions
        // ---------------------------------------------------------------------

        cout << "\nEDGE CONDITIONS\n";
        cout << string(72, '-') << '\n';

        try {
            estimateDuration(100.0, 0, 6.0);
        } catch (const invalid_argument& error) {
            cout << "Invalid team size handled: "
                 << error.what() << '\n';
        }

        try {
            ScopeItem invalid(
                "BAD",
                "Invalid Work Package",
                "Negative effort",
                -10.0
            );
        } catch (const invalid_argument& error) {
            cout << "Invalid effort handled: "
                 << error.what() << '\n';
        }

        // ---------------------------------------------------------------------
        // Design principles
        // ---------------------------------------------------------------------

        cout << "\nDESIGN AND CONTROL PRINCIPLES\n";
        cout << string(72, '-') << '\n';

        const vector<string> principles = {
            "Define the business purpose before defining detailed features.",
            "Use measurable objectives instead of vague aspirations.",
            "Make requirements testable.",
            "Define both inclusions and exclusions.",
            "Record assumptions and how they will be validated.",
            "Record constraints and dependencies.",
            "Decompose approved scope into manageable work packages.",
            "Connect requirements to deliverables and verification.",
            "Establish a scope baseline before uncontrolled execution.",
            "Evaluate change requests against the approved baseline.",
            "Assess effort, cost, schedule, risk, quality, and dependencies.",
            "Do not treat informal requests as approved scope.",
            "Preserve an auditable history of important scope decisions."
        };

        for (size_t i = 0; i < principles.size(); ++i) {
            cout << setw(2) << i + 1
                 << ". " << principles[i] << '\n';
        }

        cout << "\nCase study completed successfully.\n";
    }
    catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
