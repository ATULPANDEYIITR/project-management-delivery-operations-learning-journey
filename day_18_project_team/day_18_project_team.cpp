/*
 * Project Team Roles: C++17 industry-style case study
 *
 * Scenario:
 * A technology organization is developing a secure digital service.
 * The project requires business analysis, product ownership, architecture,
 * software engineering, quality assurance, DevOps, and security expertise.
 *
 * This program models:
 * - team members and roles
 * - skills and capacity
 * - project tasks
 * - dependencies
 * - RACI responsibility
 * - workload allocation
 * - risks
 * - decision ownership
 * - communication relationships
 * - project health
 * - validation and failure conditions
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic project_team_roles.cpp -o project_team_roles
 */

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;


// ============================================================================
// 1. ROLE MODEL
// ============================================================================

enum class RoleCategory {
    Governance,
    Management,
    Product,
    Analysis,
    Design,
    Engineering,
    Quality,
    Operations,
    Security,
    Data,
    Stakeholder
};


string categoryName(RoleCategory category) {
    switch (category) {
        case RoleCategory::Governance:
            return "Governance";
        case RoleCategory::Management:
            return "Management";
        case RoleCategory::Product:
            return "Product";
        case RoleCategory::Analysis:
            return "Analysis";
        case RoleCategory::Design:
            return "Design";
        case RoleCategory::Engineering:
            return "Engineering";
        case RoleCategory::Quality:
            return "Quality";
        case RoleCategory::Operations:
            return "Operations";
        case RoleCategory::Security:
            return "Security";
        case RoleCategory::Data:
            return "Data";
        case RoleCategory::Stakeholder:
            return "Stakeholder";
    }

    return "Unknown";
}


struct Role {
    string name;
    RoleCategory category;
    vector<string> responsibilities;
};


// ============================================================================
// 2. TEAM MEMBER
// ============================================================================

class TeamMember {
private:
    string id_;
    string name_;
    Role role_;
    set<string> skills_;
    double weeklyCapacity_;
    double availability_;
    double assignedHours_;

public:
    TeamMember(
        string id,
        string name,
        Role role,
        set<string> skills,
        double weeklyCapacity,
        double availability = 1.0
    )
        : id_(move(id)),
          name_(move(name)),
          role_(move(role)),
          skills_(move(skills)),
          weeklyCapacity_(weeklyCapacity),
          availability_(availability),
          assignedHours_(0.0) {

        if (weeklyCapacity_ < 0) {
            throw invalid_argument("Weekly capacity cannot be negative.");
        }

        if (availability_ < 0.0 || availability_ > 1.0) {
            throw invalid_argument(
                "Availability must be between 0 and 1."
            );
        }
    }

    const string& id() const {
        return id_;
    }

    const string& name() const {
        return name_;
    }

    const string& roleName() const {
        return role_.name;
    }

    double capacity() const {
        return weeklyCapacity_ * availability_;
    }

    double assignedHours() const {
        return assignedHours_;
    }

    double remainingCapacity() const {
        return capacity() - assignedHours_;
    }

    double utilization() const {
        if (capacity() == 0.0) {
            return 0.0;
        }

        return assignedHours_ / capacity();
    }

    bool hasSkill(const string& skill) const {
        return skills_.find(skill) != skills_.end();
    }

    void assignHours(double hours) {
        if (hours < 0) {
            throw invalid_argument(
                "Assignment hours cannot be negative."
            );
        }

        if (hours > remainingCapacity()) {
            throw runtime_error(
                "Insufficient capacity for " + name_
            );
        }

        assignedHours_ += hours;
    }
};


// ============================================================================
// 3. PROJECT TASK
// ============================================================================

struct Task {
    string id;
    string name;
    string requiredSkill;
    double estimatedHours;
    int priority;
    vector<string> dependencies;
    string owner;
    string status;

    Task(
        string taskId,
        string taskName,
        string skill,
        double hours,
        int taskPriority,
        vector<string> deps = {}
    )
        : id(move(taskId)),
          name(move(taskName)),
          requiredSkill(move(skill)),
          estimatedHours(hours),
          priority(taskPriority),
          dependencies(move(deps)),
          owner(""),
          status("Not Started") {

        if (estimatedHours < 0) {
            throw invalid_argument(
                "Task hours cannot be negative."
            );
        }
    }
};


// ============================================================================
// 4. RACI MODEL
// ============================================================================

enum class Raci {
    Responsible,
    Accountable,
    Consulted,
    Informed
};


string raciName(Raci value) {
    switch (value) {
        case Raci::Responsible:
            return "R";
        case Raci::Accountable:
            return "A";
        case Raci::Consulted:
            return "C";
        case Raci::Informed:
            return "I";
    }

    return "?";
}


struct RaciAssignment {
    string task;
    map<string, Raci> assignments;
};


bool validateRaci(const RaciAssignment& assignment, string& error) {
    int accountableCount = 0;
    int responsibleCount = 0;

    for (const auto& [person, responsibility] : assignment.assignments) {
        (void)person;

        if (responsibility == Raci::Accountable) {
            ++accountableCount;
        }

        if (responsibility == Raci::Responsible) {
            ++responsibleCount;
        }
    }

    if (accountableCount != 1) {
        error =
            "Exactly one Accountable role is required for " +
            assignment.task;
        return false;
    }

    if (responsibleCount == 0) {
        error =
            "At least one Responsible role is required for " +
            assignment.task;
        return false;
    }

    return true;
}


// ============================================================================
// 5. RISK MODEL
// ============================================================================

struct Risk {
    string id;
    string description;
    double probability;
    double impact;
    string owner;
    string mitigation;

    double exposure() const {
        return probability * impact;
    }
};


// ============================================================================
// 6. PROJECT TEAM
// ============================================================================

Role projectManagerRole{
    "Project Manager",
    RoleCategory::Management,
    {
        "Planning",
        "Coordination",
        "Risk management",
        "Schedule management"
    }
};

Role productOwnerRole{
    "Product Owner",
    RoleCategory::Product,
    {
        "Product priorities",
        "Backlog management",
        "Value decisions"
    }
};

Role businessAnalystRole{
    "Business Analyst",
    RoleCategory::Analysis,
    {
        "Requirements analysis",
        "Process analysis",
        "Business rules"
    }
};

Role technicalLeadRole{
    "Technical Lead",
    RoleCategory::Engineering,
    {
        "Architecture",
        "Technical decisions",
        "Code review"
    }
};

Role developerRole{
    "Software Developer",
    RoleCategory::Engineering,
    {
        "Implementation",
        "Testing",
        "Maintenance"
    }
};

Role qaRole{
    "QA Engineer",
    RoleCategory::Quality,
    {
        "Test design",
        "Test execution",
        "Quality verification"
    }
};

Role devOpsRole{
    "DevOps Engineer",
    RoleCategory::Operations,
    {
        "CI/CD",
        "Deployment",
        "Monitoring"
    }
};

Role securityRole{
    "Security Specialist",
    RoleCategory::Security,
    {
        "Threat modeling",
        "Security review",
        "Security controls"
    }
};


int main() {
    cout << string(78, '=') << '\n';
    cout << "PROJECT TEAM ROLE MANAGEMENT CASE STUDY\n";
    cout << string(78, '=') << '\n';


    // ------------------------------------------------------------------------
    // 7. CREATE MEMBERS
    // ------------------------------------------------------------------------

    vector<TeamMember> team;

    team.emplace_back(
        "TM01",
        "Priya",
        projectManagerRole,
        set<string>{
            "planning",
            "risk management",
            "communication"
        },
        40.0
    );

    team.emplace_back(
        "TM02",
        "Arjun",
        productOwnerRole,
        set<string>{
            "prioritization",
            "product strategy",
            "requirements"
        },
        35.0
    );

    team.emplace_back(
        "TM03",
        "Meera",
        businessAnalystRole,
        set<string>{
            "requirements",
            "process analysis"
        },
        40.0
    );

    team.emplace_back(
        "TM04",
        "Rahul",
        technicalLeadRole,
        set<string>{
            "architecture",
            "python",
            "security",
            "code review"
        },
        40.0
    );

    team.emplace_back(
        "TM05",
        "Neha",
        developerRole,
        set<string>{
            "python",
            "javascript",
            "api development",
            "testing"
        },
        40.0
    );

    team.emplace_back(
        "TM06",
        "Vikram",
        qaRole,
        set<string>{
            "testing",
            "automation testing"
        },
        40.0
    );

    team.emplace_back(
        "TM07",
        "Sara",
        devOpsRole,
        set<string>{
            "ci/cd",
            "cloud",
            "monitoring"
        },
        40.0
    );

    team.emplace_back(
        "TM08",
        "Karan",
        securityRole,
        set<string>{
            "security",
            "threat modeling"
        },
        32.0
    );


    // ------------------------------------------------------------------------
    // 8. TEAM VALIDATION
    // ------------------------------------------------------------------------

    cout << "\nTEAM VALIDATION\n";
    cout << "===============\n";

    set<string> memberIds;
    set<string> memberNames;

    for (const auto& member : team) {
        bool valid = true;

        if (!memberIds.insert(member.id()).second) {
            cerr << "Duplicate member ID: "
                 << member.id() << '\n';
            valid = false;
        }

        if (!memberNames.insert(member.name()).second) {
            cerr << "Duplicate member name: "
                 << member.name() << '\n';
            valid = false;
        }

        if (valid) {
            cout << member.name()
                 << " | "
                 << member.roleName()
                 << " | capacity="
                 << member.capacity()
                 << "h\n";
        }
    }


    // ------------------------------------------------------------------------
    // 9. PROJECT TASKS
    // ------------------------------------------------------------------------

    vector<Task> tasks{
        Task(
            "T1",
            "Define requirements",
            "requirements",
            16.0,
            1
        ),

        Task(
            "T2",
            "Design architecture",
            "architecture",
            20.0,
            1,
            {"T1"}
        ),

        Task(
            "T3",
            "Implement API",
            "python",
            32.0,
            2,
            {"T2"}
        ),

        Task(
            "T4",
            "Build automated tests",
            "testing",
            24.0,
            2,
            {"T3"}
        ),

        Task(
            "T5",
            "Configure CI/CD",
            "ci/cd",
            16.0,
            2,
            {"T3"}
        ),

        Task(
            "T6",
            "Perform security review",
            "security",
            16.0,
            1,
            {"T3"}
        ),

        Task(
            "T7",
            "Production release",
            "cloud",
            12.0,
            1,
            {"T4", "T5", "T6"}
        )
    };


    // ------------------------------------------------------------------------
    // 10. TASK INDEX
    // ------------------------------------------------------------------------

    unordered_map<string, size_t> taskIndex;

    for (size_t index = 0; index < tasks.size(); ++index) {
        taskIndex[tasks[index].id] = index;
    }


    // ------------------------------------------------------------------------
    // 11. DEPENDENCY VALIDATION
    // ------------------------------------------------------------------------

    cout << "\nDEPENDENCY VALIDATION\n";
    cout << "=====================\n";

    bool dependenciesValid = true;

    for (const auto& task : tasks) {
        for (const auto& dependency : task.dependencies) {
            if (taskIndex.find(dependency) == taskIndex.end()) {
                cerr << task.id
                     << " depends on unknown task "
                     << dependency
                     << '\n';

                dependenciesValid = false;
            }

            if (dependency == task.id) {
                cerr << task.id
                     << " cannot depend on itself\n";

                dependenciesValid = false;
            }
        }
    }

    cout << (
        dependenciesValid
            ? "All dependency references are valid.\n"
            : "Dependency validation failed.\n"
    );


    // ------------------------------------------------------------------------
    // 12. TOPOLOGICAL SORT
    // ------------------------------------------------------------------------
    //
    // Kahn's algorithm is used to determine an execution order.
    //
    // Complexity:
    //   O(V + E)
    //
    // V = number of tasks
    // E = number of dependency relationships
    //
    // The algorithm also detects cycles because a cyclic graph cannot produce
    // an ordering containing every vertex.

    unordered_map<string, vector<string>> graph;
    unordered_map<string, int> indegree;

    for (const auto& task : tasks) {
        graph[task.id] = {};
        indegree[task.id] = 0;
    }

    for (const auto& task : tasks) {
        for (const auto& dependency : task.dependencies) {
            graph[dependency].push_back(task.id);
            ++indegree[task.id];
        }
    }

    queue<string> readyQueue;

    for (const auto& [taskId, degree] : indegree) {
        if (degree == 0) {
            readyQueue.push(taskId);
        }
    }

    vector<string> executionOrder;

    while (!readyQueue.empty()) {
        string current = readyQueue.front();
        readyQueue.pop();

        executionOrder.push_back(current);

        for (const auto& dependent : graph[current]) {
            --indegree[dependent];

            if (indegree[dependent] == 0) {
                readyQueue.push(dependent);
            }
        }
    }

    cout << "\nTASK EXECUTION ORDER\n";
    cout << "====================\n";

    if (executionOrder.size() != tasks.size()) {
        cerr << "Circular dependency detected.\n";
        return 1;
    }

    for (size_t index = 0; index < executionOrder.size(); ++index) {
        if (index > 0) {
            cout << " -> ";
        }

        cout << executionOrder[index];
    }

    cout << '\n';


    // ------------------------------------------------------------------------
    // 13. SKILL-BASED TASK ASSIGNMENT
    // ------------------------------------------------------------------------

    cout << "\nTASK ASSIGNMENT\n";
    cout << "===============\n";

    vector<size_t> taskOrder(tasks.size());

    for (size_t index = 0; index < tasks.size(); ++index) {
        taskOrder[index] = index;
    }

    sort(
        taskOrder.begin(),
        taskOrder.end(),
        [&](size_t left, size_t right) {
            if (tasks[left].priority != tasks[right].priority) {
                return tasks[left].priority < tasks[right].priority;
            }

            return tasks[left].id < tasks[right].id;
        }
    );


    for (size_t taskPosition : taskOrder) {
        Task& task = tasks[taskPosition];

        TeamMember* selected = nullptr;

        for (auto& member : team) {
            if (!member.hasSkill(task.requiredSkill)) {
                continue;
            }

            if (member.remainingCapacity() < task.estimatedHours) {
                continue;
            }

            if (
                selected == nullptr ||
                member.remainingCapacity() >
                    selected->remainingCapacity()
            ) {
                selected = &member;
            }
        }

        if (selected != nullptr) {
            selected->assignHours(task.estimatedHours);

            task.owner = selected->name();
            task.status = "Assigned";

            cout << task.id
                 << " | "
                 << setw(30)
                 << left
                 << task.name
                 << " | "
                 << setw(10)
                 << selected->name()
                 << " | "
                 << task.estimatedHours
                 << "h\n";
        } else {
            cout << task.id
                 << " | "
                 << setw(30)
                 << left
                 << task.name
                 << " | UNASSIGNED\n";
        }
    }


    // ------------------------------------------------------------------------
    // 14. WORKLOAD ANALYSIS
    // ------------------------------------------------------------------------

    cout << "\nWORKLOAD ANALYSIS\n";
    cout << "=================\n";

    double totalUtilization = 0.0;

    for (const auto& member : team) {
        const double utilization = member.utilization();
        totalUtilization += utilization;

        cout << setw(10)
             << left
             << member.name()
             << " assigned="
             << setw(6)
             << member.assignedHours()
             << " capacity="
             << setw(6)
             << member.capacity()
             << " utilization="
             << fixed
             << setprecision(1)
             << utilization * 100.0
             << "%\n";
    }

    const double averageUtilization =
        team.empty()
            ? 0.0
            : totalUtilization / static_cast<double>(team.size());


    // ------------------------------------------------------------------------
    // 15. RACI MATRIX
    // ------------------------------------------------------------------------

    vector<RaciAssignment> raci{
        {
            "Define requirements",
            {
                {"Project Manager", Raci::Accountable},
                {"Product Owner", Raci::Consulted},
                {"Business Analyst", Raci::Responsible},
                {"Technical Lead", Raci::Consulted}
            }
        },

        {
            "Design architecture",
            {
                {"Project Manager", Raci::Informed},
                {"Product Owner", Raci::Consulted},
                {"Technical Lead", Raci::Accountable},
                {"Software Developer", Raci::Responsible},
                {"Security Specialist", Raci::Consulted}
            }
        },

        {
            "Implement API",
            {
                {"Project Manager", Raci::Informed},
                {"Technical Lead", Raci::Accountable},
                {"Software Developer", Raci::Responsible},
                {"QA Engineer", Raci::Consulted}
            }
        },

        {
            "Production release",
            {
                {"Project Manager", Raci::Accountable},
                {"Technical Lead", Raci::Consulted},
                {"DevOps Engineer", Raci::Responsible},
                {"QA Engineer", Raci::Consulted},
                {"Security Specialist", Raci::Consulted}
            }
        }
    };


    cout << "\nRACI VALIDATION\n";
    cout << "===============\n";

    for (const auto& assignment : raci) {
        string error;

        if (validateRaci(assignment, error)) {
            cout << assignment.task << ": VALID\n";
        } else {
            cout << assignment.task
                 << ": INVALID - "
                 << error
                 << '\n';
        }
    }


    // ------------------------------------------------------------------------
    // 16. RISK REGISTER
    // ------------------------------------------------------------------------

    vector<Risk> risks{
        {
            "R1",
            "Requirements ambiguity",
            0.40,
            8.0,
            "Business Analyst",
            "Acceptance criteria and stakeholder validation."
        },

        {
            "R2",
            "Architecture scalability problem",
            0.25,
            9.0,
            "Technical Lead",
            "Architecture review and capacity analysis."
        },

        {
            "R3",
            "Security vulnerability reaches production",
            0.20,
            10.0,
            "Security Specialist",
            "Threat modeling and security review."
        },

        {
            "R4",
            "Deployment failure",
            0.25,
            7.0,
            "DevOps Engineer",
            "Automated deployment and rollback."
        }
    };


    sort(
        risks.begin(),
        risks.end(),
        [](const Risk& left, const Risk& right) {
            return left.exposure() > right.exposure();
        }
    );


    cout << "\nRISK REGISTER\n";
    cout << "=============\n";

    for (const auto& risk : risks) {
        cout << risk.id
             << " | exposure="
             << fixed
             << setprecision(2)
             << risk.exposure()
             << " | owner="
             << risk.owner
             << " | "
             << risk.description
             << '\n';
    }


    // ------------------------------------------------------------------------
    // 17. DECISION RIGHTS
    // ------------------------------------------------------------------------

    map<string, string> decisionRights{
        {"Budget approval", "Project Sponsor"},
        {"Product priority", "Product Owner"},
        {"Project schedule", "Project Manager"},
        {"Technical architecture", "Technical Lead"},
        {"Quality verification", "QA Engineer"},
        {"Deployment implementation", "DevOps Engineer"},
        {"Security controls", "Security Specialist"}
    };


    cout << "\nDECISION RIGHTS\n";
    cout << "===============\n";

    for (const auto& [decision, owner] : decisionRights) {
        cout << decision
             << " -> "
             << owner
             << '\n';
    }


    // ------------------------------------------------------------------------
    // 18. CAPABILITY COVERAGE
    // ------------------------------------------------------------------------

    set<string> requiredCapabilities{
        "planning",
        "requirements",
        "architecture",
        "python",
        "testing",
        "ci/cd",
        "security",
        "cloud"
    };

    set<string> availableCapabilities;

    /*
     * The TeamMember intentionally exposes only the hasSkill operation.
     * A production system may expose a read-only capability view or persist
     * skills in a database. Encapsulation prevents unrelated code from
     * modifying internal member state arbitrarily.
     *
     * For this case study, capability coverage is inferred from the known
     * task requirements and explicit role assignments.
     */
    set<string> taskCapabilities;

    for (const auto& task : tasks) {
        taskCapabilities.insert(task.requiredSkill);
    }

    cout << "\nCAPABILITY COVERAGE\n";
    cout << "==================\n";

    for (const auto& capability : requiredCapabilities) {
        bool covered = taskCapabilities.find(capability)
            != taskCapabilities.end();

        cout << capability
             << " -> "
             << (covered ? "represented in project" : "missing")
             << '\n';
    }


    // ------------------------------------------------------------------------
    // 19. PROJECT HEALTH
    // ------------------------------------------------------------------------

    size_t assignedTasks = 0;
    double totalHours = 0.0;
    double assignedHours = 0.0;

    for (const auto& task : tasks) {
        totalHours += task.estimatedHours;

        if (!task.owner.empty()) {
            ++assignedTasks;
            assignedHours += task.estimatedHours;
        }
    }

    double assignmentRate =
        tasks.empty()
            ? 1.0
            : static_cast<double>(assignedTasks)
              / static_cast<double>(tasks.size());

    double workCoverage =
        totalHours == 0.0
            ? 1.0
            : assignedHours / totalHours;

    size_t highRiskCount = count_if(
        risks.begin(),
        risks.end(),
        [](const Risk& risk) {
            return risk.exposure() >= 5.0;
        }
    );


    cout << "\nPROJECT HEALTH\n";
    cout << "==============\n";
    cout << fixed << setprecision(1);
    cout << "Task assignment rate: "
         << assignmentRate * 100.0
         << "%\n";

    cout << "Work coverage: "
         << workCoverage * 100.0
         << "%\n";

    cout << "Average utilization: "
         << averageUtilization * 100.0
         << "%\n";

    cout << "High-risk items: "
         << highRiskCount
         << '\n';


    // ------------------------------------------------------------------------
    // 20. EDGE CASE: UNKNOWN DEPENDENCY
    // ------------------------------------------------------------------------

    cout << "\nEDGE CASE: UNKNOWN DEPENDENCY\n";
    cout << "============================\n";

    Task invalidTask(
        "T999",
        "Invalid example",
        "testing",
        4.0,
        1,
        {"DOES_NOT_EXIST"}
    );

    bool invalidDependencyFound = false;

    for (const auto& dependency : invalidTask.dependencies) {
        if (taskIndex.find(dependency) == taskIndex.end()) {
            invalidDependencyFound = true;

            cout << "Correctly detected unknown dependency: "
                 << dependency
                 << '\n';
        }
    }


    // ------------------------------------------------------------------------
    // 21. EDGE CASE: CIRCULAR DEPENDENCY
    // ------------------------------------------------------------------------

    cout << "\nEDGE CASE: CIRCULAR DEPENDENCY\n";
    cout << "==============================\n";

    vector<Task> circularTasks{
        Task(
            "A",
            "Task A",
            "testing",
            2.0,
            1,
            {"C"}
        ),

        Task(
            "B",
            "Task B",
            "testing",
            2.0,
            1,
            {"A"}
        ),

        Task(
            "C",
            "Task C",
            "testing",
            2.0,
            1,
            {"B"}
        )
    };

    unordered_map<string, int> circularIndegree;
    unordered_map<string, vector<string>> circularGraph;

    for (const auto& task : circularTasks) {
        circularIndegree[task.id] = 0;
        circularGraph[task.id] = {};
    }

    for (const auto& task : circularTasks) {
        for (const auto& dependency : task.dependencies) {
            circularGraph[dependency].push_back(task.id);
            ++circularIndegree[task.id];
        }
    }

    queue<string> circularQueue;

    for (const auto& [id, degree] : circularIndegree) {
        if (degree == 0) {
            circularQueue.push(id);
        }
    }

    size_t circularProcessed = 0;

    while (!circularQueue.empty()) {
        string current = circularQueue.front();
        circularQueue.pop();

        ++circularProcessed;

        for (const auto& dependent : circularGraph[current]) {
            --circularIndegree[dependent];

            if (circularIndegree[dependent] == 0) {
                circularQueue.push(dependent);
            }
        }
    }

    if (circularProcessed != circularTasks.size()) {
        cout << "Circular dependency correctly detected.\n";
    }


    // ------------------------------------------------------------------------
    // 22. ROLE DISTINCTIONS
    // ------------------------------------------------------------------------

    cout << "\nROLE DISTINCTIONS\n";
    cout << "=================\n";

    cout
        << "Project Manager vs Product Owner: "
        << "execution coordination versus product-value and priority ownership.\n";

    cout
        << "Product Owner vs Business Analyst: "
        << "product decisions versus detailed requirements and process analysis.\n";

    cout
        << "Technical Lead vs Developer: "
        << "broader technical direction versus direct implementation.\n";

    cout
        << "Developer vs QA Engineer: "
        << "building functionality versus systematic quality verification.\n";

    cout
        << "Technical Lead vs Security Specialist: "
        << "general technical architecture versus security-specific expertise.\n";


    // ------------------------------------------------------------------------
    // 23. IMPLEMENTATION TRADE-OFFS
    // ------------------------------------------------------------------------

    cout << "\nIMPLEMENTATION CONSIDERATIONS\n";
    cout << "============================\n";

    cout
        << "Vector: efficient contiguous storage and iteration for team/task lists.\n";

    cout
        << "Set: suitable for unique skills and fast membership tests.\n";

    cout
        << "unordered_map: efficient average-case lookup by task or member ID.\n";

    cout
        << "map: ordered decision-right reporting where deterministic output is useful.\n";

    cout
        << "queue: natural structure for topological dependency processing.\n";


    // ------------------------------------------------------------------------
    // 24. SECURITY CONSIDERATIONS
    // ------------------------------------------------------------------------

    cout << "\nSECURITY AND GOVERNANCE\n";
    cout << "=======================\n";

    cout
        << "Use least privilege when assigning project-system access.\n";

    cout
        << "Separate sensitive approval authority from implementation where appropriate.\n";

    cout
        << "Protect confidential team, stakeholder, project, and risk information.\n";

    cout
        << "Audit significant decisions and privileged changes.\n";

    cout
        << "Include security responsibilities throughout the project lifecycle.\n";


    // ------------------------------------------------------------------------
    // 25. FINAL REPORT
    // ------------------------------------------------------------------------

    cout << "\nFINAL PROJECT REPORT\n";
    cout << "===================\n";

    cout << "Team members: "
         << team.size()
         << '\n';

    cout << "Project tasks: "
         << tasks.size()
         << '\n';

    cout << "Assigned tasks: "
         << assignedTasks
         << '\n';

    cout << "Unassigned tasks: "
         << tasks.size() - assignedTasks
         << '\n';

    cout << "Risk items: "
         << risks.size()
         << '\n';


    // The variable demonstrates that the invalid dependency was intentionally
    // detected rather than silently ignored.
    cout << "Invalid dependency test: "
         << (invalidDependencyFound ? "detected" : "not detected")
         << '\n';


    cout << "\nThe case study models project roles as a connected system of "
         << "responsibility, authority, capability, work, communication, "
         << "dependencies, and risk ownership.\n";

    cout << string(78, '=') << '\n';

    return 0;
}
