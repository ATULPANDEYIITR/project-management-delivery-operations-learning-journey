#include <algorithm>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * C++17 Project Status Reporting and Repository Governance Engine.
 *
 * Evaluates:
 * - Project delivery and schedule health
 * - Budget utilization
 * - Project risks
 * - Pull Request state
 * - Review decisions and eligible approvals
 * - Required status checks
 * - Branch protection
 * - Merge eligibility
 *
 * No external dependencies.
 */

using namespace std;

class ValidationError : public runtime_error {
public:
    explicit ValidationError(const string& message)
        : runtime_error(message) {}
};

enum class TaskState {
    Todo,
    InProgress,
    Blocked,
    Completed
};

enum class Priority {
    Low,
    Medium,
    High,
    Critical
};

enum class PRState {
    Draft,
    Open,
    Merged,
    Closed
};

enum class ReviewState {
    Pending,
    Approved,
    ChangesRequested,
    Commented,
    Dismissed
};

enum class MergeStrategy {
    MergeCommit,
    Squash,
    Rebase
};

enum class RiskState {
    Open,
    Mitigating,
    Closed
};

string toString(TaskState state) {
    switch (state) {
        case TaskState::Todo: return "TODO";
        case TaskState::InProgress: return "IN PROGRESS";
        case TaskState::Blocked: return "BLOCKED";
        case TaskState::Completed: return "COMPLETED";
    }
    throw ValidationError("Unknown task state.");
}

string toString(Priority priority) {
    switch (priority) {
        case Priority::Low: return "LOW";
        case Priority::Medium: return "MEDIUM";
        case Priority::High: return "HIGH";
        case Priority::Critical: return "CRITICAL";
    }
    throw ValidationError("Unknown priority.");
}

struct Task {
    string id;
    string title;
    string owner;
    TaskState state;
    Priority priority;
    double estimatedHours;
    double actualHours;

    Task(
        string id,
        string title,
        string owner,
        TaskState state,
        Priority priority,
        double estimatedHours,
        double actualHours = 0.0
    ) :
        id(move(id)),
        title(move(title)),
        owner(move(owner)),
        state(state),
        priority(priority),
        estimatedHours(estimatedHours),
        actualHours(actualHours) {

        if (this->id.empty() || this->title.empty() || this->owner.empty()) {
            throw ValidationError("Task identity and owner are required.");
        }

        if (
            !isfinite(estimatedHours) ||
            !isfinite(actualHours) ||
            estimatedHours <= 0 ||
            actualHours < 0
        ) {
            throw ValidationError("Invalid task hours.");
        }
    }
};

struct Milestone {
    string id;
    string name;
    string dueDate;
    bool completed;
};

struct Risk {
    string id;
    string description;
    string owner;
    string mitigation;
    int probability;
    int impact;
    RiskState state;

    Risk(
        string id,
        string description,
        string owner,
        string mitigation,
        int probability,
        int impact,
        RiskState state = RiskState::Open
    ) :
        id(move(id)),
        description(move(description)),
        owner(move(owner)),
        mitigation(move(mitigation)),
        probability(probability),
        impact(impact),
        state(state) {

        if (this->id.empty() || this->description.empty()) {
            throw ValidationError("Risk identity is required.");
        }

        if (
            probability < 1 || probability > 5 ||
            impact < 1 || impact > 5
        ) {
            throw ValidationError("Risk values must be between 1 and 5.");
        }
    }

    int exposure() const {
        return probability * impact;
    }

    bool active() const {
        return state != RiskState::Closed;
    }
};

struct Review {
    string reviewer;
    ReviewState state;
    bool eligible;
    bool dismissed;

    Review(
        string reviewer,
        ReviewState state,
        bool eligible = true,
        bool dismissed = false
    ) :
        reviewer(move(reviewer)),
        state(state),
        eligible(eligible),
        dismissed(dismissed) {

        if (this->reviewer.empty()) {
            throw ValidationError("Reviewer identity is required.");
        }
    }
};

struct StatusCheck {
    string name;
    bool passed;
};

struct PullRequest {
    string id;
    string title;
    string sourceBranch;
    string targetBranch;
    PRState state;
    MergeStrategy strategy;

    int commitCount;
    bool draft;
    bool conflicts;
    bool baseSynchronized;
    bool conversationsResolved;

    vector<Review> reviews;
    map<string, StatusCheck> checks;

    PullRequest(
        string id,
        string title,
        string source,
        string target,
        PRState state,
        int commits,
        bool draft = false
    ) :
        id(move(id)),
        title(move(title)),
        sourceBranch(move(source)),
        targetBranch(move(target)),
        state(state),
        strategy(MergeStrategy::Squash),
        commitCount(commits),
        draft(draft),
        conflicts(false),
        baseSynchronized(true),
        conversationsResolved(true) {

        if (
            this->id.empty() ||
            this->title.empty() ||
            sourceBranch.empty() ||
            targetBranch.empty()
        ) {
            throw ValidationError("Pull Request fields are required.");
        }

        if (sourceBranch == targetBranch) {
            throw ValidationError("Branches must be different.");
        }

        if (commits < 0) {
            throw ValidationError("Commit count cannot be negative.");
        }
    }

    int approvalCount() const {
        // A reviewer contributes at most one current approval.
        set<string> approved;

        for (const auto& review : reviews) {
            if (
                review.eligible &&
                !review.dismissed &&
                review.state == ReviewState::Approved
            ) {
                approved.insert(review.reviewer);
            }
        }

        return static_cast<int>(approved.size());
    }
};

struct BranchProtection {
    string branch;
    int requiredApprovals;
    set<string> requiredChecks;

    bool requireConversations;
    bool requireSynchronization;
    bool requireLinearHistory;

    bool allowDirectPush;
    bool allowForcePush;
    bool allowDeletion;
    bool allowAdministratorBypass;

    BranchProtection(
        string branch,
        int approvals,
        set<string> checks,
        bool conversations = true,
        bool synchronized = true,
        bool linear = false
    ) :
        branch(move(branch)),
        requiredApprovals(approvals),
        requiredChecks(move(checks)),
        requireConversations(conversations),
        requireSynchronization(synchronized),
        requireLinearHistory(linear),
        allowDirectPush(false),
        allowForcePush(false),
        allowDeletion(false),
        allowAdministratorBypass(false) {

        if (this->branch.empty() || approvals < 0) {
            throw ValidationError("Invalid branch protection policy.");
        }
    }
};

struct GovernanceResult {
    string pullRequestId;
    bool eligible;
    vector<string> reasons;
};

class GovernanceEngine {
public:

    GovernanceResult evaluate(
        const PullRequest& pr,
        const BranchProtection& policy
    ) const {

        vector<string> reasons;

        if (pr.state != PRState::Open) {
            reasons.push_back("Pull Request is not open.");
        }

        if (pr.draft) {
            reasons.push_back("Draft Pull Request cannot be merged.");
        }

        if (pr.targetBranch != policy.branch) {
            reasons.push_back("Protected target branch mismatch.");
        }

        if (pr.commitCount == 0) {
            reasons.push_back("No commits are available.");
        }

        if (pr.conflicts) {
            reasons.push_back("Merge conflicts must be resolved.");
        }

        if (
            policy.requireSynchronization &&
            !pr.baseSynchronized
        ) {
            reasons.push_back("Base branch synchronization is required.");
        }

        if (
            policy.requireConversations &&
            !pr.conversationsResolved
        ) {
            reasons.push_back("Unresolved review conversations exist.");
        }

        const int approvals = pr.approvalCount();

        if (approvals < policy.requiredApprovals) {
            reasons.push_back(
                "Insufficient approvals: " +
                to_string(approvals) + "/" +
                to_string(policy.requiredApprovals)
            );
        }

        for (const string& required : policy.requiredChecks) {

            auto it = pr.checks.find(required);

            if (it == pr.checks.end() || !it->second.passed) {
                reasons.push_back(
                    "Required check failed or missing: " + required
                );
            }
        }

        if (
            policy.requireLinearHistory &&
            pr.strategy == MergeStrategy::MergeCommit
        ) {
            reasons.push_back("Merge commit violates linear history.");
        }

        return {
            pr.id,
            reasons.empty(),
            reasons
        };
    }
};

class Project {
public:
    string id;
    string name;
    string manager;

    double budget;
    double actualCost;

    vector<Task> tasks;
    vector<Milestone> milestones;
    vector<Risk> risks;
    vector<PullRequest> pullRequests;

    Project(
        string id,
        string name,
        string manager,
        double budget,
        double actualCost
    ) :
        id(move(id)),
        name(move(name)),
        manager(move(manager)),
        budget(budget),
        actualCost(actualCost) {

        if (this->id.empty() || this->name.empty() ||
            this->manager.empty()) {
            throw ValidationError("Project identity is required.");
        }

        if (
            !isfinite(budget) ||
            !isfinite(actualCost) ||
            budget <= 0 ||
            actualCost < 0
        ) {
            throw ValidationError("Invalid financial values.");
        }
    }

    void addTask(const Task& task) {
        auto duplicate = find_if(
            tasks.begin(),
            tasks.end(),
            [&](const Task& existing) {
                return existing.id == task.id;
            }
        );

        if (duplicate != tasks.end()) {
            throw ValidationError("Duplicate task ID.");
        }

        tasks.push_back(task);
    }

    double completionPercentage() const {
        if (tasks.empty()) return 0.0;

        int completed = count_if(
            tasks.begin(),
            tasks.end(),
            [](const Task& task) {
                return task.state == TaskState::Completed;
            }
        );

        return 100.0 * completed / tasks.size();
    }

    double budgetUtilization() const {
        return actualCost / budget * 100.0;
    }

    string calculateStatus() const {

        if (
            !tasks.empty() &&
            completionPercentage() == 100.0
        ) {
            return "COMPLETED";
        }

        if (budgetUtilization() > 100.0) {
            return "DELAYED";
        }

        bool blockedCritical = any_of(
            tasks.begin(),
            tasks.end(),
            [](const Task& task) {
                return task.state == TaskState::Blocked &&
                    (
                        task.priority == Priority::High ||
                        task.priority == Priority::Critical
                    );
            }
        );

        if (blockedCritical) {
            return "AT RISK";
        }

        bool criticalRisk = any_of(
            risks.begin(),
            risks.end(),
            [](const Risk& risk) {
                return risk.active() && risk.exposure() >= 15;
            }
        );

        if (criticalRisk) {
            return "AT RISK";
        }

        return tasks.empty() ? "NOT STARTED" : "ON TRACK";
    }

    void printStatusReport() const {

        cout << "\nPROJECT STATUS REPORT\n";
        cout << string(60, '=') << "\n";

        cout << "Project: " << name << "\n";
        cout << "Project ID: " << id << "\n";
        cout << "Manager: " << manager << "\n";
        cout << "Status: " << calculateStatus() << "\n";

        cout << fixed << setprecision(2);

        cout << "\nDELIVERY\n";
        cout << "Total tasks: " << tasks.size() << "\n";
        cout << "Completion: " << completionPercentage() << "%\n";

        cout << "\nTASK BREAKDOWN\n";

        for (const auto& task : tasks) {
            cout << task.id << " | "
                 << task.title << " | "
                 << toString(task.state) << " | "
                 << toString(task.priority) << "\n";
        }

        cout << "\nFINANCIALS\n";
        cout << "Budget: " << budget << "\n";
        cout << "Actual cost: " << actualCost << "\n";
        cout << "Variance: " << actualCost - budget << "\n";
        cout << "Utilization: " << budgetUtilization() << "%\n";

        cout << "\nRISK REGISTER\n";

        for (const auto& risk : risks) {
            if (!risk.active()) continue;

            cout << risk.id << " | "
                 << risk.description << " | Exposure: "
                 << risk.exposure() << " | Owner: "
                 << risk.owner << "\n";
        }

        cout << "\nREPOSITORY DELIVERY\n";

        cout << "Pull Requests: " << pullRequests.size() << "\n";

        int merged = count_if(
            pullRequests.begin(),
            pullRequests.end(),
            [](const PullRequest& pr) {
                return pr.state == PRState::Merged;
            }
        );

        cout << "Merged: " << merged << "\n";
    }
};

Project createDemoProject() {

    Project project(
        "PRJ-2026-001",
        "Enterprise Project Reporting Platform",
        "Project Manager",
        500000,
        185000
    );

    project.addTask(Task(
        "T001", "Requirements analysis", "Analyst",
        TaskState::Completed, Priority::High, 80, 76
    ));

    project.addTask(Task(
        "T002", "Database implementation", "Developer",
        TaskState::Completed, Priority::High, 120, 130
    ));

    project.addTask(Task(
        "T003", "Reporting engine", "Developer",
        TaskState::InProgress, Priority::High, 160, 70
    ));

    project.addTask(Task(
        "T004", "Security testing", "Security Lead",
        TaskState::Blocked, Priority::Critical, 60, 15
    ));

    project.addTask(Task(
        "T005", "Deployment preparation", "Operations",
        TaskState::Todo, Priority::Medium, 50, 0
    ));

    project.risks.emplace_back(
        "R001",
        "Security testing environment unavailable",
        "Security Lead",
        "Provision isolated infrastructure",
        4, 5
    );

    project.risks.emplace_back(
        "R002",
        "Reporting data quality issues",
        "Data Lead",
        "Introduce automated validation",
        3, 3,
        RiskState::Mitigating
    );

    project.risks.emplace_back(
        "R003",
        "Requirements clarification completed",
        "Analyst",
        "Maintain approved specification",
        1, 2,
        RiskState::Closed
    );

    PullRequest pr1(
        "PR-101",
        "Implement reporting API",
        "feature/reporting",
        "main",
        PRState::Open,
        4
    );

    pr1.reviews.emplace_back(
        "reviewer-a", ReviewState::Approved
    );

    pr1.reviews.emplace_back(
        "reviewer-b", ReviewState::Approved
    );

    pr1.checks.emplace(
        "unit-tests", StatusCheck{"unit-tests", true}
    );

    pr1.checks.emplace(
        "security-scan", StatusCheck{"security-scan", true}
    );

    pr1.checks.emplace(
        "lint", StatusCheck{"lint", true}
    );

    project.pullRequests.push_back(pr1);

    PullRequest pr2(
        "PR-102",
        "Implement security controls",
        "feature/security",
        "main",
        PRState::Open,
        2,
        true
    );

    pr2.reviews.emplace_back(
        "reviewer-c", ReviewState::ChangesRequested
    );

    pr2.checks.emplace(
        "unit-tests", StatusCheck{"unit-tests", true}
    );

    pr2.checks.emplace(
        "security-scan", StatusCheck{"security-scan", false}
    );

    pr2.conversationsResolved = false;

    project.pullRequests.push_back(pr2);

    return project;
}

void runTests() {

    Project project = createDemoProject();

    if (project.completionPercentage() != 40.0) {
        throw runtime_error("Completion calculation failed.");
    }

    if (project.calculateStatus() != "AT RISK") {
        throw runtime_error("Project status calculation failed.");
    }

    BranchProtection policy(
        "main",
        2,
        {"unit-tests", "security-scan", "lint"},
        true,
        true,
        true
    );

    GovernanceEngine engine;

    GovernanceResult first = engine.evaluate(
        project.pullRequests[0], policy
    );

    if (!first.eligible) {
        throw runtime_error("Valid Pull Request was rejected.");
    }

    GovernanceResult second = engine.evaluate(
        project.pullRequests[1], policy
    );

    if (second.eligible) {
        throw runtime_error("Invalid Pull Request was accepted.");
    }

    try {
        Task invalid(
            "BAD", "Invalid task", "User",
            TaskState::Todo, Priority::High, -10, 0
        );

        throw runtime_error("Invalid task accepted.");
    }
    catch (const ValidationError&) {
        // Expected validation failure.
    }

    cout << "All tests passed.\n";
}

int main() {

    try {

        runTests();

        Project project = createDemoProject();

        project.printStatusReport();

        BranchProtection policy(
            "main",
            2,
            {"unit-tests", "security-scan", "lint"},
            true,
            true,
            true
        );

        GovernanceEngine engine;

        cout << "\nMERGE ELIGIBILITY ENGINE\n";
        cout << string(60, '=') << "\n";

        for (const auto& pr : project.pullRequests) {

            GovernanceResult result = engine.evaluate(pr, policy);

            cout << "\n" << result.pullRequestId << ": "
                 << (result.eligible ? "ELIGIBLE" : "BLOCKED")
                 << "\n";

            for (const string& reason : result.reasons) {
                cout << " - " << reason << "\n";
            }
        }

        cout << "\nExecution completed successfully.\n";

    }
    catch (const exception& error) {

        cerr << "Application error: "
             << error.what() << "\n";

        return 1;
    }

    return 0;
}
