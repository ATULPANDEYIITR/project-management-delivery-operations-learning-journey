/*
 * Project Management Case Study
 * Topic: Responsibilities of a Project Manager
 *
 * Standard: C++17
 *
 * This program models an enterprise technology implementation project.
 * It demonstrates how a project manager coordinates:
 *
 * - project initiation
 * - scope
 * - work breakdown
 * - scheduling
 * - dependencies
 * - critical path
 * - cost control
 * - earned value
 * - resources
 * - stakeholders
 * - RACI accountability
 * - risks
 * - issues
 * - quality
 * - change control
 * - communication
 * - governance
 * - security considerations
 * - project closure
 *
 * Compile:
 *   g++ -std=c++17 -O2 project_manager_case_study.cpp -o project_manager
 *
 * Run:
 *   ./project_manager
 */

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

// -----------------------------------------------------------------------------
// 1. PROJECT
// -----------------------------------------------------------------------------

enum class ProjectStatus {
    Planned,
    Active,
    Blocked,
    Completed,
    Cancelled
};

string statusToString(ProjectStatus status) {
    switch (status) {
        case ProjectStatus::Planned:
            return "Planned";
        case ProjectStatus::Active:
            return "Active";
        case ProjectStatus::Blocked:
            return "Blocked";
        case ProjectStatus::Completed:
            return "Completed";
        case ProjectStatus::Cancelled:
            return "Cancelled";
    }

    return "Unknown";
}

struct Project {
    string name;
    string objective;
    string sponsor;
    string manager;
    double budget;
    int plannedDurationDays;
    ProjectStatus status = ProjectStatus::Planned;

    void activate() {
        if (status != ProjectStatus::Planned) {
            throw runtime_error(
                "Only planned projects can be activated."
            );
        }

        status = ProjectStatus::Active;
    }

    void complete() {
        if (status != ProjectStatus::Active) {
            throw runtime_error(
                "Only active projects can be completed."
            );
        }

        status = ProjectStatus::Completed;
    }
};

// -----------------------------------------------------------------------------
// 2. TASK MODEL
// -----------------------------------------------------------------------------

struct Task {
    string id;
    string name;
    string owner;
    int duration;
    double cost;
    vector<string> dependencies;
    double progress = 0.0;
    ProjectStatus status = ProjectStatus::Planned;

    void updateProgress(double newProgress) {
        if (newProgress < 0.0 || newProgress > 100.0) {
            throw invalid_argument(
                "Task progress must be between 0 and 100."
            );
        }

        progress = newProgress;

        if (progress == 100.0) {
            status = ProjectStatus::Completed;
        } else if (progress > 0.0) {
            status = ProjectStatus::Active;
        }
    }
};

// -----------------------------------------------------------------------------
// 3. STAKEHOLDER MANAGEMENT
// -----------------------------------------------------------------------------

struct Stakeholder {
    string name;
    string role;
    int influence;
    int interest;

    string strategy() const {
        if (influence >= 4 && interest >= 4) {
            return "Manage closely";
        }

        if (influence >= 4 && interest < 4) {
            return "Keep satisfied";
        }

        if (influence < 4 && interest >= 4) {
            return "Keep informed";
        }

        return "Monitor";
    }
};

// -----------------------------------------------------------------------------
// 4. RISK MANAGEMENT
// -----------------------------------------------------------------------------

enum class RiskProbability {
    Low = 1,
    Medium = 2,
    High = 3
};

enum class RiskImpact {
    Low = 1,
    Medium = 2,
    High = 3
};

struct Risk {
    string id;
    string description;
    RiskProbability probability;
    RiskImpact impact;
    string owner;
    string response;
    string contingency;
    string status = "Open";

    int score() const {
        return static_cast<int>(probability) *
               static_cast<int>(impact);
    }

    string severity() const {
        if (score() >= 6) {
            return "High";
        }

        if (score() >= 3) {
            return "Medium";
        }

        return "Low";
    }
};

// -----------------------------------------------------------------------------
// 5. ISSUE MANAGEMENT
// -----------------------------------------------------------------------------

struct Issue {
    string id;
    string description;
    string owner;
    string severity;
    int dueDay;
    bool closed = false;

    bool overdue(int currentDay) const {
        return !closed && currentDay > dueDay;
    }
};

// -----------------------------------------------------------------------------
// 6. RESOURCE MANAGEMENT
// -----------------------------------------------------------------------------

struct Resource {
    string name;
    string role;
    double availableHours;
    double allocatedHours = 0.0;

    void allocate(double hours) {
        if (hours < 0.0) {
            throw invalid_argument(
                "Allocated hours cannot be negative."
            );
        }

        allocatedHours += hours;
    }

    double utilization() const {
        if (availableHours == 0.0) {
            return numeric_limits<double>::infinity();
        }

        return allocatedHours / availableHours * 100.0;
    }
};

// -----------------------------------------------------------------------------
// 7. RACI MATRIX
// -----------------------------------------------------------------------------

using RaciMatrix = map<string, map<string, char>>;

vector<string> validateRaci(const RaciMatrix& matrix) {
    vector<string> warnings;

    for (const auto& [workItem, assignments] : matrix) {
        int accountableCount = 0;

        for (const auto& [person, role] : assignments) {
            if (role == 'A') {
                ++accountableCount;
            }
        }

        if (accountableCount == 0) {
            warnings.push_back(
                workItem + ": no accountable person."
            );
        }

        if (accountableCount > 1) {
            warnings.push_back(
                workItem + ": multiple accountable people."
            );
        }
    }

    return warnings;
}

// -----------------------------------------------------------------------------
// 8. DEPENDENCY GRAPH
// -----------------------------------------------------------------------------

vector<string> topologicalSort(
    const map<string, Task>& tasks
) {
    map<string, int> indegree;
    map<string, vector<string>> graph;

    for (const auto& [id, task] : tasks) {
        indegree[id] = 0;
        graph[id] = {};
    }

    for (const auto& [id, task] : tasks) {
        for (const string& dependency : task.dependencies) {
            if (!tasks.count(dependency)) {
                throw invalid_argument(
                    "Task " + id +
                    " depends on unknown task " +
                    dependency
                );
            }

            graph[dependency].push_back(id);
            ++indegree[id];
        }
    }

    queue<string> ready;

    for (const auto& [id, degree] : indegree) {
        if (degree == 0) {
            ready.push(id);
        }
    }

    vector<string> order;

    while (!ready.empty()) {
        string current = ready.front();
        ready.pop();

        order.push_back(current);

        for (const string& successor : graph[current]) {
            --indegree[successor];

            if (indegree[successor] == 0) {
                ready.push(successor);
            }
        }
    }

    if (order.size() != tasks.size()) {
        throw runtime_error(
            "Circular dependency detected."
        );
    }

    return order;
}

// -----------------------------------------------------------------------------
// 9. CRITICAL PATH
// -----------------------------------------------------------------------------

struct CriticalPathResult {
    int duration;
    vector<string> path;
};

CriticalPathResult calculateCriticalPath(
    const map<string, Task>& tasks
) {
    vector<string> order = topologicalSort(tasks);

    map<string, int> earliestStart;
    map<string, int> earliestFinish;
    map<string, string> predecessor;

    for (const string& id : order) {
        const Task& task = tasks.at(id);

        if (task.dependencies.empty()) {
            earliestStart[id] = 0;
            predecessor[id] = "";
        } else {
            string selected = task.dependencies.front();

            for (const string& dependency : task.dependencies) {
                if (
                    earliestFinish[dependency] >
                    earliestFinish[selected]
                ) {
                    selected = dependency;
                }
            }

            earliestStart[id] =
                earliestFinish[selected];

            predecessor[id] = selected;
        }

        earliestFinish[id] =
            earliestStart[id] + task.duration;
    }

    string finalTask = order.front();

    for (const string& id : order) {
        if (
            earliestFinish[id] >
            earliestFinish[finalTask]
        ) {
            finalTask = id;
        }
    }

    vector<string> path;

    string current = finalTask;

    while (!current.empty()) {
        path.push_back(current);
        current = predecessor[current];
    }

    reverse(path.begin(), path.end());

    return {
        earliestFinish[finalTask],
        path
    };
}

// -----------------------------------------------------------------------------
// 10. EARNED VALUE MANAGEMENT
// -----------------------------------------------------------------------------

struct EarnedValue {
    double plannedValue;
    double earnedValue;
    double actualCost;

    double costVariance() const {
        return earnedValue - actualCost;
    }

    double scheduleVariance() const {
        return earnedValue - plannedValue;
    }

    double costPerformanceIndex() const {
        if (actualCost <= 0.0) {
            throw invalid_argument(
                "Actual cost must be positive."
            );
        }

        return earnedValue / actualCost;
    }

    double schedulePerformanceIndex() const {
        if (plannedValue <= 0.0) {
            throw invalid_argument(
                "Planned value must be positive."
            );
        }

        return earnedValue / plannedValue;
    }
};

// -----------------------------------------------------------------------------
// 11. CHANGE CONTROL
// -----------------------------------------------------------------------------

enum class ChangeStatus {
    Proposed,
    UnderReview,
    Approved,
    Rejected
};

struct ChangeRequest {
    string id;
    string description;
    string reason;
    string requestedBy;
    double estimatedCost;
    int estimatedDelayDays;
    double businessValue;
    ChangeStatus status = ChangeStatus::Proposed;
};

class ChangeControlBoard {
private:
    double remainingBudget;
    vector<ChangeRequest> requests;

public:
    explicit ChangeControlBoard(double budget)
        : remainingBudget(budget) {
        if (budget < 0.0) {
            throw invalid_argument(
                "Change-control budget cannot be negative."
            );
        }
    }

    void submit(ChangeRequest& request) {
        request.status = ChangeStatus::UnderReview;
        requests.push_back(request);
    }

    string review(ChangeRequest& request) {
        if (request.estimatedCost > remainingBudget) {
            request.status = ChangeStatus::Rejected;
            return "Rejected: insufficient remaining budget.";
        }

        if (
            request.businessValue >= 8.0 &&
            request.estimatedDelayDays <= 5
        ) {
            request.status = ChangeStatus::Approved;
            remainingBudget -= request.estimatedCost;
            return "Approved after impact review.";
        }

        return "Requires deeper impact assessment.";
    }

    double getRemainingBudget() const {
        return remainingBudget;
    }
};

// -----------------------------------------------------------------------------
// 12. QUALITY MANAGEMENT
// -----------------------------------------------------------------------------

struct QualityCheck {
    string requirement;
    string expected;
    string actual;

    bool passed() const {
        return expected == actual;
    }
};

struct QualityReport {
    int total = 0;
    int passed = 0;
    int failed = 0;
};

QualityReport evaluateQuality(
    const vector<QualityCheck>& checks
) {
    QualityReport report;
    report.total = static_cast<int>(checks.size());

    for (const auto& check : checks) {
        if (check.passed()) {
            ++report.passed;
        } else {
            ++report.failed;
        }
    }

    return report;
}

// -----------------------------------------------------------------------------
// 13. DECISION LOG
// -----------------------------------------------------------------------------

struct Decision {
    string id;
    string subject;
    string decision;
    string owner;
    string rationale;
};

class DecisionLog {
private:
    vector<Decision> decisions;

public:
    void add(const Decision& decision) {
        if (decision.id.empty() ||
            decision.decision.empty()) {
            throw invalid_argument(
                "Decision ID and decision text are required."
            );
        }

        decisions.push_back(decision);
    }

    vector<Decision> search(
        const string& keyword
    ) const {
        vector<Decision> result;

        for (const auto& decision : decisions) {
            if (
                decision.subject.find(keyword) != string::npos ||
                decision.decision.find(keyword) != string::npos ||
                decision.rationale.find(keyword) != string::npos
            ) {
                result.push_back(decision);
            }
        }

        return result;
    }
};

// -----------------------------------------------------------------------------
// 14. STATUS REPORT
// -----------------------------------------------------------------------------

struct StatusReport {
    string reportingDate;
    vector<string> accomplishments;
    vector<string> nextPeriod;
    vector<string> risks;
    vector<string> issues;
    vector<string> decisionsNeeded;
    double budgetVariance;
    int scheduleVarianceDays;

    void print() const {
        cout << "\nStatus Report: "
             << reportingDate << "\n";

        cout << "\nAccomplishments:\n";
        for (const auto& item : accomplishments) {
            cout << "  - " << item << "\n";
        }

        cout << "\nNext period:\n";
        for (const auto& item : nextPeriod) {
            cout << "  - " << item << "\n";
        }

        cout << "\nRisks:\n";
        for (const auto& item : risks) {
            cout << "  - " << item << "\n";
        }

        cout << "\nIssues:\n";
        for (const auto& item : issues) {
            cout << "  - " << item << "\n";
        }

        cout << "\nDecisions needed:\n";
        for (const auto& item : decisionsNeeded) {
            cout << "  - " << item << "\n";
        }

        cout << fixed << setprecision(2);
        cout << "\nBudget variance: "
             << budgetVariance << "\n";

        cout << "Schedule variance: "
             << scheduleVarianceDays
             << " days\n";
    }
};

// -----------------------------------------------------------------------------
// 15. PROJECT CASE STUDY
// -----------------------------------------------------------------------------

void runCaseStudy() {
    cout << string(78, '=') << "\n";
    cout << "PROJECT MANAGER RESPONSIBILITIES: C++ CASE STUDY\n";
    cout << string(78, '=') << "\n";

    Project project{
        "Enterprise Service Management Platform",
        "Centralize service requests, workflow automation and reporting.",
        "Chief Operating Officer",
        "Project Manager",
        250000.0,
        151
    };

    project.activate();

    cout << "\nProject: "
         << project.name << "\n";

    cout << "Objective: "
         << project.objective << "\n";

    cout << "Sponsor: "
         << project.sponsor << "\n";

    cout << "Manager: "
         << project.manager << "\n";

    cout << "Budget: "
         << fixed << setprecision(2)
         << project.budget << "\n";

    cout << "Status: "
         << statusToString(project.status) << "\n";

    // -------------------------------------------------------------------------
    // Work decomposition.
    // -------------------------------------------------------------------------

    map<string, Task> tasks{
        {
            "T1",
            {
                "T1",
                "Requirements analysis",
                "Business Analyst",
                10,
                18000.0,
                {}
            }
        },
        {
            "T2",
            {
                "T2",
                "Solution architecture",
                "Solution Architect",
                8,
                22000.0,
                {"T1"}
            }
        },
        {
            "T3",
            {
                "T3",
                "UX design",
                "UX Designer",
                7,
                12000.0,
                {"T1"}
            }
        },
        {
            "T4",
            {
                "T4",
                "Backend development",
                "Backend Lead",
                25,
                58000.0,
                {"T2"}
            }
        },
        {
            "T5",
            {
                "T5",
                "Frontend development",
                "Frontend Lead",
                20,
                42000.0,
                {"T2", "T3"}
            }
        },
        {
            "T6",
            {
                "T6",
                "Integration testing",
                "QA Lead",
                12,
                24000.0,
                {"T4", "T5"}
            }
        },
        {
            "T7",
            {
                "T7",
                "User acceptance testing",
                "Business Owner",
                8,
                14000.0,
                {"T6"}
            }
        },
        {
            "T8",
            {
                "T8",
                "Production deployment",
                "DevOps Lead",
                4,
                9000.0,
                {"T7"}
            }
        },
        {
            "T9",
            {
                "T9",
                "Training and handover",
                "Change Lead",
                6,
                11000.0,
                {"T7"}
            }
        }
    };

    // -------------------------------------------------------------------------
    // Schedule.
    // -------------------------------------------------------------------------

    cout << "\nDependency-respecting order:\n";

    vector<string> order = topologicalSort(tasks);

    for (size_t i = 0; i < order.size(); ++i) {
        cout << order[i];

        if (i + 1 < order.size()) {
            cout << " -> ";
        }
    }

    cout << "\n";

    CriticalPathResult critical =
        calculateCriticalPath(tasks);

    cout << "\nCritical-path duration: "
         << critical.duration
         << " days\n";

    cout << "Critical path: ";

    for (size_t i = 0; i < critical.path.size(); ++i) {
        cout << critical.path[i];

        if (i + 1 < critical.path.size()) {
            cout << " -> ";
        }
    }

    cout << "\n";

    // -------------------------------------------------------------------------
    // Cost baseline.
    // -------------------------------------------------------------------------

    double totalPlannedCost = 0.0;

    for (const auto& [id, task] : tasks) {
        totalPlannedCost += task.cost;
    }

    cout << "\nPlanned task cost: "
         << totalPlannedCost << "\n";

    cout << "Budget buffer: "
         << project.budget - totalPlannedCost
         << "\n";

    // -------------------------------------------------------------------------
    // RACI.
    // -------------------------------------------------------------------------

    RaciMatrix raci{
        {
            "Requirements",
            {
                {"Project Manager", 'A'},
                {"Business Analyst", 'R'},
                {"Operations", 'C'},
                {"Sponsor", 'I'}
            }
        },
        {
            "Architecture",
            {
                {"Project Manager", 'A'},
                {"Solution Architect", 'R'},
                {"Security", 'C'},
                {"Sponsor", 'I'}
            }
        },
        {
            "Deployment",
            {
                {"Project Manager", 'A'},
                {"DevOps", 'R'},
                {"Security", 'C'},
                {"Operations", 'I'}
            }
        }
    };

    cout << "\nRACI validation:\n";

    vector<string> raciWarnings =
        validateRaci(raci);

    if (raciWarnings.empty()) {
        cout << "  No accountability conflicts detected.\n";
    } else {
        for (const auto& warning : raciWarnings) {
            cout << "  WARNING: "
                 << warning << "\n";
        }
    }

    // -------------------------------------------------------------------------
    // Stakeholders.
    // -------------------------------------------------------------------------

    vector<Stakeholder> stakeholders{
        {
            "Chief Operating Officer",
            "Executive Sponsor",
            5,
            5
        },
        {
            "Finance Director",
            "Budget Owner",
            5,
            3
        },
        {
            "Operations Team",
            "Primary Users",
            3,
            5
        },
        {
            "Security Team",
            "Control Function",
            4,
            4
        }
    };

    cout << "\nStakeholder strategies:\n";

    for (const auto& stakeholder : stakeholders) {
        cout << "  "
             << stakeholder.name
             << ": "
             << stakeholder.strategy()
             << "\n";
    }

    // -------------------------------------------------------------------------
    // Risks.
    // -------------------------------------------------------------------------

    vector<Risk> risks{
        {
            "R1",
            "Integration interface changes",
            RiskProbability::High,
            RiskImpact::High,
            "Solution Architect",
            "Reduce",
            "Maintain a fallback adapter."
        },
        {
            "R2",
            "Key specialist unavailable",
            RiskProbability::Medium,
            RiskImpact::High,
            "Project Manager",
            "Mitigate",
            "Cross-train another engineer."
        },
        {
            "R3",
            "Low training attendance",
            RiskProbability::Medium,
            RiskImpact::Medium,
            "Change Lead",
            "Mitigate",
            "Provide recorded sessions."
        }
    };

    sort(
        risks.begin(),
        risks.end(),
        [](const Risk& a, const Risk& b) {
            return a.score() > b.score();
        }
    );

    cout << "\nPrioritized risks:\n";

    for (const auto& risk : risks) {
        cout << "  "
             << risk.id
             << ": "
             << risk.description
             << " | score="
             << risk.score()
             << " | severity="
             << risk.severity()
             << " | owner="
             << risk.owner
             << "\n";
    }

    // -------------------------------------------------------------------------
    // Issues.
    // -------------------------------------------------------------------------

    vector<Issue> issues{
        {
            "I1",
            "Test environment provisioning delayed",
            "DevOps Lead",
            "High",
            45
        },
        {
            "I2",
            "Two requirements require clarification",
            "Business Analyst",
            "Medium",
            50
        }
    };

    int currentProjectDay = 48;

    cout << "\nIssue status:\n";

    for (const auto& issue : issues) {
        cout << "  "
             << issue.id
             << ": "
             << issue.description
             << " | overdue="
             << boolalpha
             << issue.overdue(currentProjectDay)
             << "\n";
    }

    // -------------------------------------------------------------------------
    // Resource planning.
    // -------------------------------------------------------------------------

    Resource backend{
        "Backend Lead",
        "Engineering",
        320.0
    };

    Resource frontend{
        "Frontend Lead",
        "Engineering",
        280.0
    };

    Resource qa{
        "QA Lead",
        "Quality",
        180.0
    };

    backend.allocate(300.0);
    frontend.allocate(240.0);
    qa.allocate(170.0);

    cout << "\nResource utilization:\n";

    cout << "  "
         << backend.name
         << ": "
         << backend.utilization()
         << "%\n";

    cout << "  "
         << frontend.name
         << ": "
         << frontend.utilization()
         << "%\n";

    cout << "  "
         << qa.name
         << ": "
         << qa.utilization()
         << "%\n";

    // -------------------------------------------------------------------------
    // Quality.
    // -------------------------------------------------------------------------

    vector<QualityCheck> qualityChecks{
        {"Authentication", "Pass", "Pass"},
        {"Approval workflow", "Pass", "Pass"},
        {"Dashboard calculation", "Pass", "Fail"},
        {"Audit logging", "Pass", "Pass"}
    };

    QualityReport quality =
        evaluateQuality(qualityChecks);

    cout << "\nQuality report:\n";
    cout << "  Total: " << quality.total << "\n";
    cout << "  Passed: " << quality.passed << "\n";
    cout << "  Failed: " << quality.failed << "\n";

    // -------------------------------------------------------------------------
    // Earned value.
    // -------------------------------------------------------------------------

    EarnedValue evm{
        100000.0,
        92000.0,
        98000.0
    };

    cout << "\nEarned Value Management:\n";

    cout << "  Cost variance: "
         << evm.costVariance()
         << "\n";

    cout << "  Schedule variance: "
         << evm.scheduleVariance()
         << "\n";

    cout << "  CPI: "
         << evm.costPerformanceIndex()
         << "\n";

    cout << "  SPI: "
         << evm.schedulePerformanceIndex()
         << "\n";

    double forecastAtCompletion =
        project.budget /
        evm.costPerformanceIndex();

    double estimateToComplete =
        forecastAtCompletion -
        evm.actualCost;

    cout << "  Forecast at completion: "
         << forecastAtCompletion
         << "\n";

    cout << "  Estimate to complete: "
         << estimateToComplete
         << "\n";

    // -------------------------------------------------------------------------
    // Change control.
    // -------------------------------------------------------------------------

    ChangeControlBoard board(project.budget);

    ChangeRequest change{
        "CR-001",
        "Automated executive alerting",
        "Earlier visibility of critical exceptions",
        "Chief Operating Officer",
        12000.0,
        4,
        9.0
    };

    board.submit(change);

    cout << "\nChange control:\n";
    cout << "  "
         << board.review(change)
         << "\n";

    cout << "  Remaining budget: "
         << board.getRemainingBudget()
         << "\n";

    // -------------------------------------------------------------------------
    // Decision governance.
    // -------------------------------------------------------------------------

    DecisionLog decisionLog;

    decisionLog.add({
        "D-001",
        "Data retention",
        "Retain audit data according to policy",
        "Security",
        "Compliance and operational traceability"
    });

    vector<Decision> searchResults =
        decisionLog.search("retention");

    cout << "\nDecision search results: "
         << searchResults.size()
         << "\n";

    // -------------------------------------------------------------------------
    // Status reporting.
    // -------------------------------------------------------------------------

    StatusReport report{
        "2026-11-18",
        {
            "Requirements baseline approved",
            "Architecture review completed",
            "Backend development reached 55%"
        },
        {
            "Complete core API",
            "Prepare integration testing"
        },
        {
            "Integration interface changes",
            "Specialist availability"
        },
        {
            "Test environment provisioning delay"
        },
        {
            "Confirm data retention period"
        },
        project.budget - evm.actualCost,
        -2
    };

    report.print();

    // -------------------------------------------------------------------------
    // Security considerations.
    // -------------------------------------------------------------------------

    cout << "\nSecurity controls:\n";

    vector<string> securityControls{
        "Use least-privilege access.",
        "Protect credentials and secrets.",
        "Restrict sensitive project information.",
        "Use approved storage and communication systems.",
        "Track security risks and incidents.",
        "Do not place credentials in source code.",
        "Follow retention and disposal requirements.",
        "Escalate suspected security incidents."
    };

    for (const auto& control : securityControls) {
        cout << "  - " << control << "\n";
    }

    // -------------------------------------------------------------------------
    // Closure.
    // -------------------------------------------------------------------------

    cout << "\nClosure checklist:\n";

    vector<string> closure{
        "Deliverables accepted",
        "Acceptance criteria verified",
        "Open defects transferred or resolved",
        "Contracts closed",
        "Financial reconciliation completed",
        "Documentation archived",
        "Lessons learned recorded",
        "Operational ownership transferred",
        "Resources released",
        "Final stakeholder communication completed"
    };

    for (const auto& item : closure) {
        cout << "  - " << item << "\n";
    }
}

// -----------------------------------------------------------------------------
// 16. EDGE CASES
// -----------------------------------------------------------------------------

void runEdgeCaseTests() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "EDGE CASE TESTS\n";
    cout << string(78, '=') << "\n";

    Task task{
        "TEST",
        "Validation task",
        "Developer",
        2,
        100.0
    };

    bool caughtInvalidProgress = false;

    try {
        task.updateProgress(101.0);
    } catch (const invalid_argument&) {
        caughtInvalidProgress = true;
    }

    assert(caughtInvalidProgress);

    map<string, Task> circular{
        {
            "A",
            {
                "A",
                "A",
                "Person A",
                2,
                100.0,
                {"B"}
            }
        },
        {
            "B",
            {
                "B",
                "B",
                "Person B",
                2,
                100.0,
                {"A"}
            }
        }
    };

    bool caughtCycle = false;

    try {
        topologicalSort(circular);
    } catch (const runtime_error&) {
        caughtCycle = true;
    }

    assert(caughtCycle);

    cout << "Invalid progress was rejected.\n";
    cout << "Circular dependency was rejected.\n";
    cout << "Edge-case tests passed.\n";
}

// -----------------------------------------------------------------------------
// 17. SELF-TESTS
// -----------------------------------------------------------------------------

void runSelfTests() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "SELF-TESTS\n";
    cout << string(78, '=') << "\n";

    map<string, Task> tasks{
        {
            "A",
            {
                "A",
                "Task A",
                "Developer A",
                2,
                100.0,
                {}
            }
        },
        {
            "B",
            {
                "B",
                "Task B",
                "Developer B",
                3,
                100.0,
                {"A"}
            }
        }
    };

    vector<string> order =
        topologicalSort(tasks);

    assert(order.size() == 2);
    assert(order[0] == "A");
    assert(order[1] == "B");

    CriticalPathResult result =
        calculateCriticalPath(tasks);

    assert(result.duration == 5);
    assert(result.path.size() == 2);

    EarnedValue evm{
        100.0,
        120.0,
        100.0
    };

    assert(
        abs(evm.costPerformanceIndex() - 1.2)
        < 0.000001
    );

    assert(
        abs(evm.schedulePerformanceIndex() - 1.2)
        < 0.000001
    );

    Risk highRisk{
        "R",
        "Example",
        RiskProbability::High,
        RiskImpact::High,
        "Owner",
        "Mitigate",
        "Contingency"
    };

    assert(highRisk.score() == 9);
    assert(highRisk.severity() == "High");

    cout << "All self-tests passed.\n";
}

// -----------------------------------------------------------------------------
// 18. MAIN
// -----------------------------------------------------------------------------

int main() {
    try {
        runCaseStudy();
        runEdgeCaseTests();
        runSelfTests();

        cout << "\n"
             << "Project management case study completed successfully.\n";

        return 0;
    } catch (const exception& error) {
        cerr << "\nFatal error: "
             << error.what()
             << "\n";

        return 1;
    }
}
