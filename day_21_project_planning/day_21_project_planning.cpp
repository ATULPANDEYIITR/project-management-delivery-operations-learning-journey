#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

/*
 * PROJECT PLANNING CASE STUDY
 *
 * Scenario:
 * A company is developing a secure Portfolio Analytics Platform.
 *
 * The system will:
 * - authenticate users
 * - store portfolio information
 * - expose backend services
 * - provide a dashboard
 * - generate reports
 * - pass integration and security testing
 * - deploy to production
 *
 * This program models the project from planning through scheduling,
 * resource analysis, risk management, prioritization, performance
 * measurement, change control, and release readiness.
 *
 * Compile:
 *   g++ -std=c++17 -O2 project_planning.cpp -o project_planning
 */

// ---------------------------------------------------------------------------
// 1. BASIC DATA TYPES
// ---------------------------------------------------------------------------

enum class Priority {
    MUST = 4,
    SHOULD = 3,
    COULD = 2,
    WONT = 1
};

string priorityToString(Priority priority) {
    switch (priority) {
        case Priority::MUST:
            return "Must";
        case Priority::SHOULD:
            return "Should";
        case Priority::COULD:
            return "Could";
        case Priority::WONT:
            return "Won't";
    }

    return "Unknown";
}

enum class RiskResponse {
    AVOID,
    MITIGATE,
    TRANSFER,
    ACCEPT
};

string riskResponseToString(RiskResponse response) {
    switch (response) {
        case RiskResponse::AVOID:
            return "Avoid";
        case RiskResponse::MITIGATE:
            return "Mitigate";
        case RiskResponse::TRANSFER:
            return "Transfer";
        case RiskResponse::ACCEPT:
            return "Accept";
    }

    return "Unknown";
}

enum class IssueStatus {
    OPEN,
    IN_PROGRESS,
    RESOLVED,
    CLOSED
};

string issueStatusToString(IssueStatus status) {
    switch (status) {
        case IssueStatus::OPEN:
            return "Open";
        case IssueStatus::IN_PROGRESS:
            return "In Progress";
        case IssueStatus::RESOLVED:
            return "Resolved";
        case IssueStatus::CLOSED:
            return "Closed";
    }

    return "Unknown";
}

// ---------------------------------------------------------------------------
// 2. REQUIREMENTS
// ---------------------------------------------------------------------------

struct Requirement {
    string id;
    string description;
    Priority priority;
    vector<string> acceptanceCriteria;

    bool isValid() const {
        return !id.empty()
            && !description.empty()
            && !acceptanceCriteria.empty();
    }
};

void demonstrateRequirements() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "REQUIREMENTS\n";
    cout << string(78, '=') << "\n";

    vector<Requirement> requirements = {
        {
            "REQ-001",
            "Users can securely authenticate.",
            Priority::MUST,
            {
                "Valid credentials are accepted.",
                "Invalid credentials are rejected.",
                "Authentication failures are logged."
            }
        },
        {
            "REQ-002",
            "Users can generate portfolio reports.",
            Priority::MUST,
            {
                "Reports contain selected holdings.",
                "Reports contain timestamps."
            }
        },
        {
            "REQ-003",
            "Users can customize dashboard themes.",
            Priority::COULD,
            {
                "Theme selection persists."
            }
        }
    };

    for (const auto& requirement : requirements) {
        cout << requirement.id
             << " | "
             << priorityToString(requirement.priority)
             << " | "
             << requirement.description
             << "\n";

        for (const auto& criterion : requirement.acceptanceCriteria) {
            cout << "  Acceptance: " << criterion << "\n";
        }

        if (!requirement.isValid()) {
            throw runtime_error(
                "Invalid requirement: " + requirement.id
            );
        }
    }
}

// ---------------------------------------------------------------------------
// 3. PROJECT TASK MODEL
// ---------------------------------------------------------------------------

struct Task {
    string id;
    string name;
    int durationDays;
    double cost;
    vector<string> dependencies;
    string resource;

    void validate(const map<string, Task>& tasks) const {
        if (durationDays < 0) {
            throw invalid_argument(
                id + ": duration cannot be negative."
            );
        }

        if (cost < 0.0) {
            throw invalid_argument(
                id + ": cost cannot be negative."
            );
        }

        for (const auto& dependency : dependencies) {
            if (!tasks.count(dependency)) {
                throw invalid_argument(
                    id + ": unknown dependency " + dependency
                );
            }
        }
    }
};

map<string, Task> createProjectTasks() {
    return {
        {
            "T1",
            {
                "T1",
                "Requirements analysis",
                4,
                1800,
                {},
                "Business Analyst"
            }
        },
        {
            "T2",
            {
                "T2",
                "Architecture design",
                5,
                3000,
                {"T1"},
                "Solution Architect"
            }
        },
        {
            "T3",
            {
                "T3",
                "Database implementation",
                6,
                3600,
                {"T2"},
                "Database Engineer"
            }
        },
        {
            "T4",
            {
                "T4",
                "Backend implementation",
                10,
                7200,
                {"T2"},
                "Backend Engineer"
            }
        },
        {
            "T5",
            {
                "T5",
                "Frontend implementation",
                9,
                6300,
                {"T2"},
                "Frontend Engineer"
            }
        },
        {
            "T6",
            {
                "T6",
                "Integration testing",
                5,
                3200,
                {"T3", "T4", "T5"},
                "QA Engineer"
            }
        },
        {
            "T7",
            {
                "T7",
                "Security testing",
                4,
                2800,
                {"T6"},
                "Security Engineer"
            }
        },
        {
            "T8",
            {
                "T8",
                "Production deployment",
                2,
                1600,
                {"T7"},
                "DevOps Engineer"
            }
        },
        {
            "T9",
            {
                "T9",
                "Operational documentation",
                3,
                1200,
                {"T6"},
                "Technical Writer"
            }
        }
    };
}

// ---------------------------------------------------------------------------
// 4. DEPENDENCY GRAPH
// ---------------------------------------------------------------------------

vector<string> topologicalSort(const map<string, Task>& tasks) {
    map<string, int> indegree;
    map<string, vector<string>> successors;

    for (const auto& [id, task] : tasks) {
        indegree[id] = 0;
        successors[id] = {};
    }

    for (const auto& [id, task] : tasks) {
        for (const auto& dependency : task.dependencies) {
            if (!tasks.count(dependency)) {
                throw runtime_error(
                    "Unknown dependency: " + dependency
                );
            }

            indegree[id]++;
            successors[dependency].push_back(id);
        }
    }

    priority_queue<
        string,
        vector<string>,
        greater<string>
    > ready;

    for (const auto& [id, degree] : indegree) {
        if (degree == 0) {
            ready.push(id);
        }
    }

    vector<string> order;

    while (!ready.empty()) {
        string current = ready.top();
        ready.pop();

        order.push_back(current);

        sort(
            successors[current].begin(),
            successors[current].end()
        );

        for (const auto& successor : successors[current]) {
            indegree[successor]--;

            if (indegree[successor] == 0) {
                ready.push(successor);
            }
        }
    }

    if (order.size() != tasks.size()) {
        throw runtime_error(
            "Circular dependency detected in project schedule."
        );
    }

    return order;
}

// ---------------------------------------------------------------------------
// 5. CRITICAL PATH METHOD
// ---------------------------------------------------------------------------

struct ScheduleEntry {
    int earliestStart = 0;
    int earliestFinish = 0;
    int latestStart = 0;
    int latestFinish = 0;
    int totalFloat = 0;

    bool critical() const {
        return totalFloat == 0;
    }
};

map<string, ScheduleEntry>
calculateCriticalPath(const map<string, Task>& tasks) {
    vector<string> order = topologicalSort(tasks);

    map<string, ScheduleEntry> schedule;

    // Forward pass.
    // Earliest start of a task is the latest earliest finish of
    // all of its predecessors.
    for (const auto& id : order) {
        const Task& task = tasks.at(id);

        int earliestStart = 0;

        for (const auto& dependency : task.dependencies) {
            earliestStart = max(
                earliestStart,
                schedule.at(dependency).earliestFinish
            );
        }

        schedule[id].earliestStart = earliestStart;
        schedule[id].earliestFinish =
            earliestStart + task.durationDays;
    }

    int projectDuration = 0;

    for (const auto& [id, entry] : schedule) {
        projectDuration = max(
            projectDuration,
            entry.earliestFinish
        );
    }

    // Backward pass.
    // Latest finish is constrained by successor tasks.
    for (auto it = order.rbegin(); it != order.rend(); ++it) {
        const string& id = *it;
        const Task& task = tasks.at(id);

        vector<string> successors;

        for (const auto& [candidateId, candidate] : tasks) {
            if (
                find(
                    candidate.dependencies.begin(),
                    candidate.dependencies.end(),
                    id
                ) != candidate.dependencies.end()
            ) {
                successors.push_back(candidateId);
            }
        }

        int latestFinish = projectDuration;

        if (!successors.empty()) {
            latestFinish = numeric_limits<int>::max();

            for (const auto& successor : successors) {
                latestFinish = min(
                    latestFinish,
                    schedule.at(successor).latestStart
                );
            }
        }

        schedule[id].latestFinish = latestFinish;
        schedule[id].latestStart =
            latestFinish - task.durationDays;

        schedule[id].totalFloat =
            schedule[id].latestStart -
            schedule[id].earliestStart;
    }

    return schedule;
}

void demonstrateCriticalPath(
    const map<string, Task>& tasks,
    const map<string, ScheduleEntry>& schedule
) {
    cout << "\n" << string(78, '=') << "\n";
    cout << "CRITICAL PATH METHOD\n";
    cout << string(78, '=') << "\n";

    for (const auto& [id, entry] : schedule) {
        cout << id
             << " | ES=" << entry.earliestStart
             << " EF=" << entry.earliestFinish
             << " LS=" << entry.latestStart
             << " LF=" << entry.latestFinish
             << " Float=" << entry.totalFloat;

        if (entry.critical()) {
            cout << " | CRITICAL";
        }

        cout << "\n";
    }

    int projectDuration = 0;

    for (const auto& [id, entry] : schedule) {
        projectDuration = max(
            projectDuration,
            entry.earliestFinish
        );
    }

    cout << "Project duration: "
         << projectDuration
         << " working days\n";
}

// ---------------------------------------------------------------------------
// 6. COST PLANNING
// ---------------------------------------------------------------------------

double calculateTotalCost(const map<string, Task>& tasks) {
    double total = 0.0;

    for (const auto& [id, task] : tasks) {
        total += task.cost;
    }

    return total;
}

void demonstrateCostPlanning(
    const map<string, Task>& tasks
) {
    cout << "\n" << string(78, '=') << "\n";
    cout << "COST PLANNING\n";
    cout << string(78, '=') << "\n";

    const double directCost = calculateTotalCost(tasks);
    const double contingency = directCost * 0.10;
    const double planningBudget =
        directCost + contingency;

    cout << fixed << setprecision(2);

    cout << "Direct task cost: $"
         << directCost << "\n";

    cout << "Contingency: $"
         << contingency << "\n";

    cout << "Planning budget: $"
         << planningBudget << "\n";
}

// ---------------------------------------------------------------------------
// 7. RESOURCE PLANNING
// ---------------------------------------------------------------------------

struct Resource {
    string name;
    string role;
    double weeklyCapacity;
    double assignedHours;

    double utilization() const {
        if (weeklyCapacity <= 0.0) {
            return 0.0;
        }

        return assignedHours / weeklyCapacity;
    }
};

void demonstrateResourcePlanning() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "RESOURCE CAPACITY\n";
    cout << string(78, '=') << "\n";

    vector<Resource> resources = {
        {"Asha", "Backend Engineer", 40, 34},
        {"Ravi", "Frontend Engineer", 40, 38},
        {"Mina", "QA Engineer", 40, 30},
        {"Dev", "Security Engineer", 32, 36}
    };

    for (const auto& resource : resources) {
        const double percentage =
            resource.utilization() * 100.0;

        cout << resource.name
             << " | "
             << resource.role
             << " | "
             << fixed << setprecision(1)
             << percentage
             << "% | ";

        if (resource.assignedHours > resource.weeklyCapacity) {
            cout << "OVER CAPACITY";
        } else {
            cout << "Within capacity";
        }

        cout << "\n";
    }
}

// ---------------------------------------------------------------------------
// 8. RISK MANAGEMENT
// ---------------------------------------------------------------------------

struct Risk {
    string id;
    string description;
    double probability;
    double impact;
    RiskResponse response;
    string mitigation;

    double exposure() const {
        return probability * impact;
    }

    void validate() const {
        if (probability < 0.0 || probability > 1.0) {
            throw invalid_argument(
                id + ": probability must be between 0 and 1."
            );
        }

        if (impact < 0.0) {
            throw invalid_argument(
                id + ": impact cannot be negative."
            );
        }
    }
};

void demonstrateRiskManagement() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "RISK MANAGEMENT\n";
    cout << string(78, '=') << "\n";

    vector<Risk> risks = {
        {
            "R1",
            "External data provider outage",
            0.30,
            8.0,
            RiskResponse::MITIGATE,
            "Use caching and a fallback source."
        },
        {
            "R2",
            "Critical security defect discovered late",
            0.20,
            10.0,
            RiskResponse::MITIGATE,
            "Perform security testing before release."
        },
        {
            "R3",
            "Key specialist unavailable",
            0.15,
            7.0,
            RiskResponse::MITIGATE,
            "Cross-train team members."
        }
    };

    for (const auto& risk : risks) {
        risk.validate();

        cout << risk.id
             << " | Exposure="
             << fixed << setprecision(2)
             << risk.exposure()
             << " | Response="
             << riskResponseToString(risk.response)
             << "\n";

        cout << "  Mitigation: "
             << risk.mitigation
             << "\n";
    }
}

// ---------------------------------------------------------------------------
// 9. ISSUE MANAGEMENT
// ---------------------------------------------------------------------------

struct Issue {
    string id;
    string description;
    int severity;
    string owner;
    IssueStatus status;

    void resolve() {
        status = IssueStatus::RESOLVED;
    }
};

void demonstrateIssueManagement() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "ISSUE MANAGEMENT\n";
    cout << string(78, '=') << "\n";

    Issue issue = {
        "ISS-101",
        "CSV export fails for empty portfolios.",
        7,
        "QA Engineer",
        IssueStatus::OPEN
    };

    cout << issue.id
         << " | "
         << issue.description
         << " | Status="
         << issueStatusToString(issue.status)
         << "\n";

    issue.resolve();

    cout << "After correction: "
         << issueStatusToString(issue.status)
         << "\n";
}

// ---------------------------------------------------------------------------
// 10. PRIORITIZATION
// ---------------------------------------------------------------------------

struct BacklogItem {
    string id;
    string name;
    double businessValue;
    double urgency;
    double effort;
    double riskReduction;

    double score() const {
        return (
            businessValue +
            urgency +
            riskReduction
        ) / max(effort, 1.0);
    }
};

void demonstratePrioritization() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "BACKLOG PRIORITIZATION\n";
    cout << string(78, '=') << "\n";

    vector<BacklogItem> backlog = {
        {"B1", "Secure authentication", 10, 10, 5, 10},
        {"B2", "Dashboard filters", 7, 5, 4, 2},
        {"B3", "CSV export", 6, 6, 2, 1},
        {"B4", "Custom themes", 3, 2, 5, 0}
    };

    sort(
        backlog.begin(),
        backlog.end(),
        [](const BacklogItem& left, const BacklogItem& right) {
            return left.score() > right.score();
        }
    );

    for (const auto& item : backlog) {
        cout << item.id
             << " | "
             << item.name
             << " | Score="
             << fixed << setprecision(2)
             << item.score()
             << "\n";
    }

    cout << "The score is a heuristic. It should not replace documented "
            "business, technical, security, and regulatory reasoning.\n";
}

// ---------------------------------------------------------------------------
// 11. AGILE SPRINT
// ---------------------------------------------------------------------------

struct SprintItem {
    string id;
    string description;
    int storyPoints;
    vector<string> acceptanceCriteria;
};

class Sprint {
private:
    int sprintNumber;
    int capacity;
    vector<SprintItem> items;

public:
    Sprint(int number, int capacityPoints)
        : sprintNumber(number),
          capacity(capacityPoints) {}

    int committedPoints() const {
        int total = 0;

        for (const auto& item : items) {
            total += item.storyPoints;
        }

        return total;
    }

    bool addItem(const SprintItem& item) {
        if (
            committedPoints() + item.storyPoints >
            capacity
        ) {
            return false;
        }

        items.push_back(item);
        return true;
    }

    int remainingCapacity() const {
        return capacity - committedPoints();
    }
};

void demonstrateSprintPlanning() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "AGILE SPRINT PLANNING\n";
    cout << string(78, '=') << "\n";

    Sprint sprint(1, 20);

    vector<SprintItem> candidates = {
        {
            "US-1",
            "Secure login",
            5,
            {
                "Valid users authenticate.",
                "Invalid credentials are rejected."
            }
        },
        {
            "US-2",
            "Portfolio dashboard",
            8,
            {
                "Holdings are displayed.",
                "Calculations are correct."
            }
        },
        {
            "US-3",
            "CSV export",
            3,
            {
                "Required columns are exported."
            }
        },
        {
            "US-4",
            "Custom theme",
            5,
            {
                "Theme persists."
            }
        }
    };

    for (const auto& item : candidates) {
        cout << item.id
             << ": "
             << (
                 sprint.addItem(item)
                     ? "committed"
                     : "not committed"
             )
             << "\n";
    }

    cout << "Committed points: "
         << sprint.committedPoints()
         << "\n";

    cout << "Remaining capacity: "
         << sprint.remainingCapacity()
         << "\n";
}

// ---------------------------------------------------------------------------
// 12. PERFORMANCE MEASUREMENT
// ---------------------------------------------------------------------------

struct PerformanceSnapshot {
    double plannedValue;
    double earnedValue;
    double actualCost;

    double scheduleVariance() const {
        return earnedValue - plannedValue;
    }

    double costVariance() const {
        return earnedValue - actualCost;
    }

    double schedulePerformanceIndex() const {
        if (plannedValue == 0.0) {
            return 0.0;
        }

        return earnedValue / plannedValue;
    }

    double costPerformanceIndex() const {
        if (actualCost == 0.0) {
            return 0.0;
        }

        return earnedValue / actualCost;
    }
};

void demonstratePerformance() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "PROJECT PERFORMANCE\n";
    cout << string(78, '=') << "\n";

    PerformanceSnapshot snapshot = {
        50000,
        45000,
        52000
    };

    cout << fixed << setprecision(3);

    cout << "Schedule variance: $"
         << snapshot.scheduleVariance()
         << "\n";

    cout << "Cost variance: $"
         << snapshot.costVariance()
         << "\n";

    cout << "SPI: "
         << snapshot.schedulePerformanceIndex()
         << "\n";

    cout << "CPI: "
         << snapshot.costPerformanceIndex()
         << "\n";
}

// ---------------------------------------------------------------------------
// 13. CHANGE CONTROL
// ---------------------------------------------------------------------------

struct ChangeRequest {
    string id;
    string description;
    double scopeImpact;
    int scheduleImpactDays;
    double costImpact;
    bool approved;

    void approve() {
        approved = true;
    }
};

void demonstrateChangeControl() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "CHANGE CONTROL\n";
    cout << string(78, '=') << "\n";

    ChangeRequest request = {
        "CR-001",
        "Add multi-currency support",
        0.12,
        6,
        8500,
        false
    };

    cout << request.id
         << " | "
         << request.description
         << "\n";

    cout << "Scope impact: "
         << request.scopeImpact * 100.0
         << "%\n";

    cout << "Schedule impact: "
         << request.scheduleImpactDays
         << " days\n";

    cout << "Cost impact: $"
         << request.costImpact
         << "\n";

    request.approve();

    cout << "Approved after impact assessment: "
         << (request.approved ? "Yes" : "No")
         << "\n";
}

// ---------------------------------------------------------------------------
// 14. QUALITY GATES
// ---------------------------------------------------------------------------

struct QualityGate {
    string name;
    bool required;
    bool passed;
};

bool releaseAllowed(const vector<QualityGate>& gates) {
    for (const auto& gate : gates) {
        if (gate.required && !gate.passed) {
            return false;
        }
    }

    return true;
}

void demonstrateQualityGates() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "QUALITY GATES\n";
    cout << string(78, '=') << "\n";

    vector<QualityGate> gates = {
        {"Functional testing", true, true},
        {"Security review", true, true},
        {"Operational documentation", true, false}
    };

    for (const auto& gate : gates) {
        cout << gate.name
             << ": "
             << (gate.passed ? "PASS" : "FAIL")
             << "\n";
    }

    cout << "Release: "
         << (
             releaseAllowed(gates)
                 ? "ALLOWED"
                 : "BLOCKED"
         )
         << "\n";
}

// ---------------------------------------------------------------------------
// 15. SCENARIO ANALYSIS
// ---------------------------------------------------------------------------

map<string, Task>
createAcceleratedPlan(const map<string, Task>& baseline) {
    map<string, Task> accelerated;

    for (const auto& [id, task] : baseline) {
        Task copy = task;

        // This scenario assumes extra resources or parallelization can
        // reduce task duration by approximately 20%, at an increased cost.
        copy.durationDays =
            max(1, static_cast<int>(
                round(task.durationDays * 0.8)
            ));

        copy.cost *= 1.20;

        accelerated[id] = copy;
    }

    return accelerated;
}

void demonstrateScenarioAnalysis(
    const map<string, Task>& baseline
) {
    cout << "\n" << string(78, '=') << "\n";
    cout << "SCENARIO ANALYSIS\n";
    cout << string(78, '=') << "\n";

    const auto baselineSchedule =
        calculateCriticalPath(baseline);

    const auto accelerated =
        createAcceleratedPlan(baseline);

    const auto acceleratedSchedule =
        calculateCriticalPath(accelerated);

    int baselineDuration = 0;
    int acceleratedDuration = 0;

    for (const auto& [id, entry] : baselineSchedule) {
        baselineDuration =
            max(baselineDuration, entry.earliestFinish);
    }

    for (const auto& [id, entry] : acceleratedSchedule) {
        acceleratedDuration =
            max(acceleratedDuration, entry.earliestFinish);
    }

    const double baselineCost =
        calculateTotalCost(baseline);

    const double acceleratedCost =
        calculateTotalCost(accelerated);

    cout << "Baseline duration: "
         << baselineDuration
         << " days\n";

    cout << "Accelerated duration: "
         << acceleratedDuration
         << " days\n";

    cout << "Baseline cost: $"
         << baselineCost
         << "\n";

    cout << "Accelerated cost: $"
         << acceleratedCost
         << "\n";

    cout << "The scenario illustrates the trade-off between "
            "schedule compression and additional cost.\n";
}

// ---------------------------------------------------------------------------
// 16. RESOURCE LOAD
// ---------------------------------------------------------------------------

void demonstrateResourceLoad(
    const map<string, Task>& tasks
) {
    cout << "\n" << string(78, '=') << "\n";
    cout << "RESOURCE LOAD\n";
    cout << string(78, '=') << "\n";

    map<string, int> load;

    for (const auto& [id, task] : tasks) {
        load[task.resource] += task.durationDays;
    }

    for (const auto& [resource, days] : load) {
        cout << resource
             << ": "
             << days
             << " task-days\n";
    }
}

// ---------------------------------------------------------------------------
// 17. PROJECT HEALTH
// ---------------------------------------------------------------------------

struct ProjectHealth {
    double scheduleIndex;
    double costIndex;
    int openHighRisks;
    int criticalIssues;
    double requirementCompletion;
};

string evaluateIndex(double index) {
    if (index < 0.90) {
        return "Attention";
    }

    if (index < 1.00) {
        return "Monitor";
    }

    return "On plan or ahead";
}

void demonstrateProjectHealth() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "PROJECT HEALTH\n";
    cout << string(78, '=') << "\n";

    ProjectHealth health = {
        0.94,
        0.97,
        2,
        0,
        0.82
    };

    cout << "Schedule: "
         << evaluateIndex(health.scheduleIndex)
         << "\n";

    cout << "Cost: "
         << evaluateIndex(health.costIndex)
         << "\n";

    cout << "High risks: "
         << (
             health.openHighRisks >= 3
                 ? "Attention"
                 : health.openHighRisks > 0
                     ? "Monitor"
                     : "Controlled"
         )
         << "\n";

    cout << "Critical issues: "
         << (
             health.criticalIssues > 0
                 ? "Attention"
                 : "Controlled"
         )
         << "\n";

    cout << "Requirement completion: "
         << health.requirementCompletion * 100.0
         << "%\n";
}

// ---------------------------------------------------------------------------
// 18. TRACEABILITY
// ---------------------------------------------------------------------------

struct TraceabilityRecord {
    string requirementId;
    vector<string> tasks;
    vector<string> tests;
    string acceptanceStatus;
};

void demonstrateTraceability() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "REQUIREMENTS TRACEABILITY\n";
    cout << string(78, '=') << "\n";

    vector<TraceabilityRecord> records = {
        {
            "REQ-001",
            {"T4", "T6", "T7"},
            {"TEST-101", "TEST-102"},
            "Accepted"
        },
        {
            "REQ-002",
            {"T3", "T4", "T5", "T6"},
            {"TEST-201", "TEST-202"},
            "In Review"
        }
    };

    for (const auto& record : records) {
        cout << record.requirementId
             << " | Status="
             << record.acceptanceStatus
             << "\n";

        cout << "  Tasks: ";

        for (const auto& task : record.tasks) {
            cout << task << " ";
        }

        cout << "\n  Tests: ";

        for (const auto& test : record.tests) {
            cout << test << " ";
        }

        cout << "\n";
    }
}

// ---------------------------------------------------------------------------
// 19. TESTS
// ---------------------------------------------------------------------------

void runTests() {
    cout << "\n" << string(78, '=') << "\n";
    cout << "AUTOMATED VALIDATION\n";
    cout << string(78, '=') << "\n";

    map<string, Task> tasks = createProjectTasks();

    for (const auto& [id, task] : tasks) {
        task.validate(tasks);
    }

    vector<string> order = topologicalSort(tasks);

    auto positionOf = [&order](const string& id) {
        auto it = find(order.begin(), order.end(), id);

        if (it == order.end()) {
            throw runtime_error("Task not found in topological order.");
        }

        return distance(order.begin(), it);
    };

    if (positionOf("T1") >= positionOf("T2")) {
        throw runtime_error("T1 must precede T2.");
    }

    if (positionOf("T2") >= positionOf("T4")) {
        throw runtime_error("T2 must precede T4.");
    }

    auto schedule = calculateCriticalPath(tasks);

    for (const auto& [id, entry] : schedule) {
        if (entry.earliestStart > entry.earliestFinish) {
            throw runtime_error(
                "Invalid earliest schedule for " + id
            );
        }

        if (entry.latestStart > entry.latestFinish) {
            throw runtime_error(
                "Invalid latest schedule for " + id
            );
        }
    }

    PerformanceSnapshot performance = {
        100,
        80,
        90
    };

    if (performance.scheduleVariance() != -20) {
        throw runtime_error("Schedule variance test failed.");
    }

    if (performance.costVariance() != -10) {
        throw runtime_error("Cost variance test failed.");
    }

    cout << "All tests passed.\n";
}

// ---------------------------------------------------------------------------
// 20. MAIN CASE STUDY
// ---------------------------------------------------------------------------

int main() {
    try {
        cout << string(78, '=') << "\n";
        cout << "PROJECT PLANNING CASE STUDY\n";
        cout << string(78, '=') << "\n";

        cout << "\nScenario:\n";
        cout << "A secure Portfolio Analytics Platform is being developed.\n";
        cout << "The project has a fixed release window and limited specialist capacity.\n";

        demonstrateRequirements();

        map<string, Task> tasks =
            createProjectTasks();

        for (const auto& [id, task] : tasks) {
            task.validate(tasks);
        }

        cout << "\nDEPENDENCY ORDER\n";
        vector<string> order =
            topologicalSort(tasks);

        for (size_t index = 0; index < order.size(); ++index) {
            cout << order[index];

            if (index + 1 < order.size()) {
                cout << " -> ";
            }
        }

        cout << "\n";

        auto schedule =
            calculateCriticalPath(tasks);

        demonstrateCriticalPath(
            tasks,
            schedule
        );

        demonstrateCostPlanning(tasks);
        demonstrateResourcePlanning();
        demonstrateRiskManagement();
        demonstrateIssueManagement();
        demonstratePrioritization();
        demonstrateSprintPlanning();
        demonstratePerformance();
        demonstrateChangeControl();
        demonstrateQualityGates();
        demonstrateScenarioAnalysis(tasks);
        demonstrateResourceLoad(tasks);
        demonstrateProjectHealth();
        demonstrateTraceability();

        cout << "\n" << string(78, '=') << "\n";
        cout << "PLANNING PRINCIPLES USED BY THE CASE STUDY\n";
        cout << string(78, '=') << "\n";

        vector<string> principles = {
            "Define outcomes before scheduling detailed work.",
            "Separate scope from implementation details.",
            "Decompose deliverables into manageable tasks.",
            "Model dependencies explicitly.",
            "Use critical-path analysis for schedule reasoning.",
            "Treat estimates as uncertain measurements.",
            "Check resource capacity before committing work.",
            "Maintain a risk register throughout the project.",
            "Separate risks from active issues.",
            "Assess change requests before approving them.",
            "Use acceptance criteria to make completion testable.",
            "Trace requirements to implementation and tests.",
            "Use quality gates before production release.",
            "Measure planned and actual performance consistently.",
            "Evaluate schedule compression against cost and risk."
        };

        for (const auto& principle : principles) {
            cout << "- " << principle << "\n";
        }

        runTests();

        cout << "\n" << string(78, '=') << "\n";
        cout << "CASE STUDY COMPLETED SUCCESSFULLY\n";
        cout << string(78, '=') << "\n";

        return 0;
    }
    catch (const exception& error) {
        cerr << "Project planning program failed: "
             << error.what()
             << "\n";

        return 1;
    }
}
