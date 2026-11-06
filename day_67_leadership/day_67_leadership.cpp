#include <algorithm>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class LeadershipStyle {
    AUTOCRATIC,
    DEMOCRATIC,
    TRANSFORMATIONAL,
    TRANSACTIONAL,
    SERVANT,
    SITUATIONAL
};

enum class TaskStatus {
    NOT_STARTED,
    IN_PROGRESS,
    BLOCKED,
    COMPLETED
};

enum class DecisionStatus {
    PROPOSED,
    APPROVED,
    REJECTED,
    DEFERRED
};

enum class RiskLevel {
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL
};

string toString(LeadershipStyle style) {
    switch (style) {
        case LeadershipStyle::AUTOCRATIC: return "Autocratic";
        case LeadershipStyle::DEMOCRATIC: return "Democratic";
        case LeadershipStyle::TRANSFORMATIONAL: return "Transformational";
        case LeadershipStyle::TRANSACTIONAL: return "Transactional";
        case LeadershipStyle::SERVANT: return "Servant";
        case LeadershipStyle::SITUATIONAL: return "Situational";
    }
    throw logic_error("Unknown leadership style.");
}

string toString(TaskStatus status) {
    switch (status) {
        case TaskStatus::NOT_STARTED: return "Not started";
        case TaskStatus::IN_PROGRESS: return "In progress";
        case TaskStatus::BLOCKED: return "Blocked";
        case TaskStatus::COMPLETED: return "Completed";
    }
    throw logic_error("Unknown task status.");
}

string toString(RiskLevel level) {
    switch (level) {
        case RiskLevel::LOW: return "Low";
        case RiskLevel::MEDIUM: return "Medium";
        case RiskLevel::HIGH: return "High";
        case RiskLevel::CRITICAL: return "Critical";
    }
    throw logic_error("Unknown risk level.");
}

struct TeamMember {
    int id;
    string name;
    string role;
    int skillLevel;
    int workload = 0;
    int completedTasks = 0;
    bool active = true;
};

struct ProjectTask {
    int id;
    string title;
    int requiredSkill;
    double estimatedHours;
    int priority;
    TaskStatus status = TaskStatus::NOT_STARTED;
    optional<int> assignedTo;
    double progress = 0.0;
};

struct Stakeholder {
    int id;
    string name;
    int influence;
    int interest;
    string expectations;
};

struct ProjectRisk {
    int id;
    string description;
    int probability;
    int impact;
    int ownerId;
    string mitigation;
    bool open = true;

    int exposure() const {
        return probability * impact;
    }

    RiskLevel level() const {
        int score = exposure();

        if (score >= 20) return RiskLevel::CRITICAL;
        if (score >= 12) return RiskLevel::HIGH;
        if (score >= 6) return RiskLevel::MEDIUM;

        return RiskLevel::LOW;
    }
};

struct ProjectDecision {
    int id;
    string title;
    string description;
    string owner;
    DecisionStatus status = DecisionStatus::PROPOSED;
    string rationale;
};

struct Metrics {
    int totalTasks = 0;
    int completedTasks = 0;
    int assignedTasks = 0;
    double averageProgress = 0;
    double averageWorkload = 0;
    int criticalRisks = 0;
};

class ProjectLeadership {
private:
    string projectName;
    LeadershipStyle style;

    map<int, TeamMember> members;
    map<int, ProjectTask> tasks;
    map<int, Stakeholder> stakeholders;
    map<int, ProjectRisk> risks;
    map<int, ProjectDecision> decisions;

    vector<string> auditLog;

    void recordEvent(const string& event) {
        auditLog.push_back(event);
    }

    TeamMember& getMember(int id) {
        auto it = members.find(id);

        if (it == members.end()) {
            throw invalid_argument("Team member does not exist.");
        }

        return it->second;
    }

    ProjectTask& getTask(int id) {
        auto it = tasks.find(id);

        if (it == tasks.end()) {
            throw invalid_argument("Project task does not exist.");
        }

        return it->second;
    }

public:
    ProjectLeadership(
        string name,
        LeadershipStyle leadershipStyle
    ) : projectName(move(name)), style(leadershipStyle) {
        if (projectName.empty()) {
            throw invalid_argument("Project name cannot be empty.");
        }
    }

    void addMember(const TeamMember& member) {
        if (member.id <= 0 || member.name.empty()) {
            throw invalid_argument("Invalid team member.");
        }

        if (member.skillLevel < 1 || member.skillLevel > 5) {
            throw invalid_argument("Skill level must be 1-5.");
        }

        if (member.workload < 0 || member.workload > 100) {
            throw invalid_argument("Invalid workload.");
        }

        if (!members.emplace(member.id, member).second) {
            throw invalid_argument("Duplicate member ID.");
        }
    }

    void addTask(const ProjectTask& task) {
        if (task.id <= 0 || task.title.empty()) {
            throw invalid_argument("Invalid task.");
        }

        if (task.requiredSkill < 1 || task.requiredSkill > 5) {
            throw invalid_argument("Required skill must be 1-5.");
        }

        if (task.estimatedHours <= 0) {
            throw invalid_argument("Estimated hours must be positive.");
        }

        if (task.priority < 1 || task.priority > 5) {
            throw invalid_argument("Priority must be 1-5.");
        }

        if (!tasks.emplace(task.id, task).second) {
            throw invalid_argument("Duplicate task ID.");
        }
    }

    void addStakeholder(const Stakeholder& stakeholder) {
        if (stakeholder.id <= 0 ||
            stakeholder.name.empty() ||
            stakeholder.influence < 1 ||
            stakeholder.influence > 5 ||
            stakeholder.interest < 1 ||
            stakeholder.interest > 5) {
            throw invalid_argument("Invalid stakeholder information.");
        }

        if (!stakeholders.emplace(
            stakeholder.id, stakeholder
        ).second) {
            throw invalid_argument("Duplicate stakeholder ID.");
        }
    }

    void addRisk(const ProjectRisk& risk) {
        if (risk.id <= 0 ||
            risk.probability < 1 || risk.probability > 5 ||
            risk.impact < 1 || risk.impact > 5) {
            throw invalid_argument("Invalid risk information.");
        }

        if (members.find(risk.ownerId) == members.end()) {
            throw invalid_argument("Risk owner does not exist.");
        }

        if (!risks.emplace(risk.id, risk).second) {
            throw invalid_argument("Duplicate risk ID.");
        }
    }

    LeadershipStyle selectStyle(
        int skillLevel,
        int urgency,
        int complexity
    ) const {
        if (skillLevel < 1 || skillLevel > 5 ||
            urgency < 1 || urgency > 5 ||
            complexity < 1 || complexity > 5) {
            throw invalid_argument("Leadership inputs must be 1-5.");
        }

        if (urgency >= 5) {
            return LeadershipStyle::AUTOCRATIC;
        }

        if (skillLevel <= 2) {
            return LeadershipStyle::SITUATIONAL;
        }

        if (complexity >= 4) {
            return LeadershipStyle::TRANSFORMATIONAL;
        }

        if (skillLevel >= 4) {
            return LeadershipStyle::SERVANT;
        }

        return LeadershipStyle::DEMOCRATIC;
    }

    void assignTask(int taskId, int memberId) {
        ProjectTask& task = getTask(taskId);
        TeamMember& member = getMember(memberId);

        if (!member.active) {
            throw runtime_error("Inactive member cannot receive work.");
        }

        if (task.status == TaskStatus::COMPLETED) {
            throw runtime_error("Completed task cannot be reassigned.");
        }

        if (member.skillLevel < task.requiredSkill) {
            throw runtime_error("Insufficient technical competence.");
        }

        constexpr int allocation = 20;

        int effectiveWorkload = member.workload;

        if (task.assignedTo.has_value() &&
            task.assignedTo.value() == memberId) {
            effectiveWorkload -= allocation;
        }

        if (effectiveWorkload + allocation > 100) {
            throw runtime_error("Member workload exceeds capacity.");
        }

        // All validation occurs before changing task ownership.
        if (task.assignedTo.has_value()) {
            TeamMember& previous = getMember(
                task.assignedTo.value()
            );

            previous.workload = max(
                0, previous.workload - allocation
            );
        }

        member.workload += allocation;
        task.assignedTo = memberId;
        task.status = TaskStatus::IN_PROGRESS;

        recordEvent(
            "Task " + task.title + " assigned to " + member.name
        );
    }

    void updateProgress(int taskId, double progress) {
        ProjectTask& task = getTask(taskId);

        if (progress < 0 || progress > 100) {
            throw invalid_argument("Progress must be 0-100.");
        }

        if (task.status == TaskStatus::COMPLETED) {
            throw runtime_error("Task is already completed.");
        }

        if (!task.assignedTo.has_value()) {
            throw runtime_error("Task has no assigned owner.");
        }

        if (progress < task.progress) {
            throw invalid_argument("Progress cannot decrease.");
        }

        task.progress = progress;

        if (progress == 100) {
            task.status = TaskStatus::COMPLETED;

            TeamMember& member = getMember(
                task.assignedTo.value()
            );

            member.workload = max(0, member.workload - 20);
            member.completedTasks++;

            recordEvent("Task completed: " + task.title);
        }
    }

    void setBlocked(int taskId, const string& reason) {
        ProjectTask& task = getTask(taskId);

        if (task.status == TaskStatus::COMPLETED) {
            throw runtime_error("Completed task cannot be blocked.");
        }

        if (reason.empty()) {
            throw invalid_argument("Blocking reason is required.");
        }

        task.status = TaskStatus::BLOCKED;

        recordEvent(
            "Task blocked: " + task.title + " | " + reason
        );
    }

    void createDecision(const ProjectDecision& decision) {
        if (decision.id <= 0 ||
            decision.title.empty() ||
            decision.owner.empty()) {
            throw invalid_argument("Invalid decision.");
        }

        if (!decisions.emplace(
            decision.id, decision
        ).second) {
            throw invalid_argument("Duplicate decision ID.");
        }
    }

    void processDecision(
        int decisionId,
        DecisionStatus status,
        const string& rationale
    ) {
        auto it = decisions.find(decisionId);

        if (it == decisions.end()) {
            throw invalid_argument("Decision does not exist.");
        }

        if (it->second.status != DecisionStatus::PROPOSED) {
            throw runtime_error("Decision already processed.");
        }

        if (rationale.empty()) {
            throw invalid_argument("Decision rationale is required.");
        }

        it->second.status = status;
        it->second.rationale = rationale;

        recordEvent(
            "Decision processed: " + it->second.title
        );
    }

    string stakeholderStrategy(const Stakeholder& stakeholder) const {
        if (stakeholder.influence >= 4 &&
            stakeholder.interest >= 4) {
            return "Manage closely";
        }

        if (stakeholder.influence >= 4) {
            return "Keep satisfied";
        }

        if (stakeholder.interest >= 4) {
            return "Keep informed";
        }

        return "Monitor";
    }

    void resolveConflict(
        const string& issue,
        const vector<string>& options,
        const string& selected
    ) {
        if (issue.empty() || options.size() < 2) {
            throw invalid_argument("Invalid conflict definition.");
        }

        if (find(options.begin(), options.end(), selected) ==
            options.end()) {
            throw invalid_argument("Invalid conflict resolution.");
        }

        recordEvent(
            "Conflict resolved: " + issue +
            " | Selected: " + selected
        );
    }

    Metrics calculateMetrics() const {
        Metrics result;

        result.totalTasks = static_cast<int>(tasks.size());

        double totalProgress = 0;
        int activeMemberCount = 0;
        int totalWorkload = 0;

        for (const auto& [id, task] : tasks) {
            totalProgress += task.progress;

            if (task.status == TaskStatus::COMPLETED) {
                result.completedTasks++;
            }

            if (task.assignedTo.has_value()) {
                result.assignedTasks++;
            }
        }

        for (const auto& [id, member] : members) {
            if (member.active) {
                totalWorkload += member.workload;
                activeMemberCount++;
            }
        }

        for (const auto& [id, risk] : risks) {
            if (risk.open && risk.level() == RiskLevel::CRITICAL) {
                result.criticalRisks++;
            }
        }

        result.averageProgress = result.totalTasks
            ? totalProgress / result.totalTasks
            : 0;

        result.averageWorkload = activeMemberCount
            ? static_cast<double>(totalWorkload) / activeMemberCount
            : 0;

        return result;
    }

    void printReport() const {
        Metrics metrics = calculateMetrics();

        cout << "\nPROJECT LEADERSHIP REPORT\n";
        cout << string(60, '=') << "\n";

        cout << "Project: " << projectName << "\n";
        cout << "Leadership style: " << toString(style) << "\n";

        cout << "\nTEAM MEMBERS\n";

        for (const auto& [id, member] : members) {
            cout << member.name
                 << " | " << member.role
                 << " | Workload: " << member.workload << "%"
                 << " | Completed: " << member.completedTasks
                 << "\n";
        }

        cout << "\nTASKS\n";

        for (const auto& [id, task] : tasks) {
            cout << task.title
                 << " | " << toString(task.status)
                 << " | Progress: " << task.progress << "%";

            if (task.assignedTo.has_value()) {
                cout << " | Owner: "
                     << getMember(task.assignedTo.value()).name;
            }

            cout << "\n";
        }

        cout << "\nRISKS\n";

        for (const auto& [id, risk] : risks) {
            cout << risk.description
                 << " | Exposure: " << risk.exposure()
                 << " | Level: " << toString(risk.level())
                 << "\n";
        }

        cout << "\nSTAKEHOLDER ENGAGEMENT\n";

        for (const auto& [id, stakeholder] : stakeholders) {
            cout << stakeholder.name
                 << " | " << stakeholderStrategy(stakeholder)
                 << "\n";
        }

        cout << "\nPERFORMANCE METRICS\n";
        cout << "Total tasks: " << metrics.totalTasks << "\n";
        cout << "Completed: " << metrics.completedTasks << "\n";
        cout << "Assigned: " << metrics.assignedTasks << "\n";

        cout << fixed << setprecision(2);

        cout << "Average progress: "
             << metrics.averageProgress << "%\n";

        cout << "Average team workload: "
             << metrics.averageWorkload << "%\n";

        cout << "Critical risks: "
             << metrics.criticalRisks << "\n";

        cout << "\nAUDIT EVENTS\n";

        for (const string& event : auditLog) {
            cout << "- " << event << "\n";
        }
    }
};

int main() {
    try {
        ProjectLeadership project(
            "Enterprise Transformation Programme",
            LeadershipStyle::TRANSFORMATIONAL
        );

        project.addMember({
            1, "Ananya", "Project Manager", 5
        });

        project.addMember({
            2, "Rahul", "Technical Lead", 4
        });

        project.addMember({
            3, "Meera", "Business Analyst", 3
        });

        project.addTask({
            101, "Architecture assessment", 4, 40, 5
        });

        project.addTask({
            102, "Requirements analysis", 3, 30, 4
        });

        project.addTask({
            103, "Implementation planning", 4, 25, 5
        });

        project.addStakeholder({
            1, "Executive Sponsor", 5, 5,
            "Meet strategic objectives and delivery commitments."
        });

        project.addStakeholder({
            2, "Operations Manager", 4, 3,
            "Maintain operational continuity."
        });

        project.addStakeholder({
            3, "End Users", 2, 5,
            "Ensure usability and reliability."
        });

        project.assignTask(101, 2);
        project.assignTask(102, 3);

        project.updateProgress(101, 60);
        project.updateProgress(102, 100);

        project.addRisk({
            201,
            "Integration delay",
            4,
            5,
            2,
            "Weekly integration checkpoints."
        });

        project.addRisk({
            202,
            "Insufficient stakeholder participation",
            2,
            3,
            1,
            "Structured stakeholder consultations."
        });

        project.createDecision({
            301,
            "Phased implementation",
            "Deliver the programme through controlled phases.",
            "Project Manager"
        });

        project.processDecision(
            301,
            DecisionStatus::APPROVED,
            "Phased delivery limits operational disruption."
        );

        project.resolveConflict(
            "Disagreement over implementation timing",
            {"Full deployment", "Phased deployment"},
            "Phased deployment"
        );

        cout << "Selected leadership approach: "
             << toString(project.selectStyle(3, 2, 4))
             << "\n";

        project.printReport();

    } catch (const exception& error) {
        cerr << "Leadership system error: "
             << error.what() << "\n";

        return 1;
    }

    return 0;
}
