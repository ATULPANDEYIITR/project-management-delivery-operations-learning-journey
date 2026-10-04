/*
 * Project Dependencies: Understanding Task Dependencies
 *
 * C++17 case study:
 * Repository Migration and Production Release Governance
 *
 * The program models a technical project in which database migration,
 * service deployment, compatibility testing, observability, security
 * validation, and production rollout have explicit prerequisites.
 *
 * It demonstrates:
 * - directed dependency graphs
 * - dependency validation
 * - cycle detection
 * - topological scheduling
 * - parallel execution waves
 * - critical-path analysis
 * - task state transitions
 * - failure propagation
 * - resource-aware scheduling
 * - dependency-aware release eligibility
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic project_dependencies.cpp -o project_dependencies
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

enum class TaskStatus {
    NotStarted,
    InProgress,
    Completed,
    Failed,
    Blocked
};

enum class Priority {
    Low = 1,
    Normal = 2,
    High = 3,
    Critical = 4
};

struct Task {
    std::string id;
    std::string name;
    int duration;
    std::set<std::string> dependencies;
    std::string owner;
    Priority priority;
    TaskStatus status = TaskStatus::NotStarted;
    std::string failureReason;
};

std::string statusToString(TaskStatus status) {
    switch (status) {
        case TaskStatus::NotStarted:
            return "not_started";
        case TaskStatus::InProgress:
            return "in_progress";
        case TaskStatus::Completed:
            return "completed";
        case TaskStatus::Failed:
            return "failed";
        case TaskStatus::Blocked:
            return "blocked";
    }

    return "unknown";
}

std::string priorityToString(Priority priority) {
    switch (priority) {
        case Priority::Low:
            return "low";
        case Priority::Normal:
            return "normal";
        case Priority::High:
            return "high";
        case Priority::Critical:
            return "critical";
    }

    return "unknown";
}

class DependencyEngine {
private:
    std::string projectName;
    std::map<std::string, Task> tasks;

public:
    explicit DependencyEngine(std::string name)
        : projectName(std::move(name)) {}

    void addTask(
        const std::string& id,
        const std::string& name,
        int duration,
        const std::set<std::string>& dependencies = {},
        const std::string& owner = "unassigned",
        Priority priority = Priority::Normal
    ) {
        if (id.empty()) {
            throw std::invalid_argument("Task ID cannot be empty.");
        }

        if (name.empty()) {
            throw std::invalid_argument(
                "Task name cannot be empty."
            );
        }

        if (duration <= 0) {
            throw std::invalid_argument(
                "Task duration must be positive."
            );
        }

        if (tasks.find(id) != tasks.end()) {
            throw std::invalid_argument(
                "Duplicate task ID: " + id
            );
        }

        if (dependencies.find(id) != dependencies.end()) {
            throw std::invalid_argument(
                "A task cannot depend on itself: " + id
            );
        }

        Task task{
            id,
            name,
            duration,
            dependencies,
            owner,
            priority,
            TaskStatus::NotStarted,
            ""
        };

        tasks.emplace(id, std::move(task));

        try {
            validate();
        } catch (...) {
            tasks.erase(id);
            throw;
        }
    }

    Task& getTask(const std::string& id) {
        auto iterator = tasks.find(id);

        if (iterator == tasks.end()) {
            throw std::out_of_range(
                "Unknown task: " + id
            );
        }

        return iterator->second;
    }

    const Task& getTask(const std::string& id) const {
        auto iterator = tasks.find(id);

        if (iterator == tasks.end()) {
            throw std::out_of_range(
                "Unknown task: " + id
            );
        }

        return iterator->second;
    }

    void validateReferences() const {
        for (const auto& [id, task] : tasks) {
            for (const auto& dependency : task.dependencies) {
                if (tasks.find(dependency) == tasks.end()) {
                    throw std::invalid_argument(
                        "Task " + id +
                        " references missing dependency " +
                        dependency
                    );
                }
            }
        }
    }

    std::vector<std::string> findCycle() const {
        validateReferences();

        std::set<std::string> visiting;
        std::set<std::string> visited;
        std::vector<std::string> path;

        std::function<std::vector<std::string>(
            const std::string&
        )> dfs;

        dfs = [&](const std::string& current)
            -> std::vector<std::string> {
            if (visiting.count(current)) {
                auto position = std::find(
                    path.begin(),
                    path.end(),
                    current
                );

                if (position != path.end()) {
                    std::vector<std::string> cycle(
                        position,
                        path.end()
                    );
                    cycle.push_back(current);
                    return cycle;
                }

                return {};
            }

            if (visited.count(current)) {
                return {};
            }

            visiting.insert(current);
            path.push_back(current);

            const auto& task = getTask(current);

            for (const auto& dependency : task.dependencies) {
                auto cycle = dfs(dependency);

                if (!cycle.empty()) {
                    return cycle;
                }
            }

            path.pop_back();
            visiting.erase(current);
            visited.insert(current);

            return {};
        };

        for (const auto& [id, task] : tasks) {
            auto cycle = dfs(id);

            if (!cycle.empty()) {
                return cycle;
            }
        }

        return {};
    }

    void validate() const {
        validateReferences();

        const auto cycle = findCycle();

        if (!cycle.empty()) {
            std::string message = "Circular dependency: ";

            for (std::size_t index = 0; index < cycle.size(); ++index) {
                if (index > 0) {
                    message += " -> ";
                }
                message += cycle[index];
            }

            throw std::invalid_argument(message);
        }
    }

    std::map<std::string, std::set<std::string>> buildDependents() const {
        validateReferences();

        std::map<std::string, std::set<std::string>> dependents;

        for (const auto& [id, task] : tasks) {
            dependents[id];
        }

        for (const auto& [id, task] : tasks) {
            for (const auto& dependency : task.dependencies) {
                dependents[dependency].insert(id);
            }
        }

        return dependents;
    }

    std::vector<std::string> topologicalOrder() const {
        validate();

        std::map<std::string, int> indegree;

        for (const auto& [id, task] : tasks) {
            indegree[id] =
                static_cast<int>(task.dependencies.size());
        }

        auto dependents = buildDependents();

        std::queue<std::string> ready;

        for (const auto& [id, count] : indegree) {
            if (count == 0) {
                ready.push(id);
            }
        }

        std::vector<std::string> order;

        while (!ready.empty()) {
            const auto current = ready.front();
            ready.pop();

            order.push_back(current);

            for (const auto& dependent : dependents[current]) {
                --indegree[dependent];

                if (indegree[dependent] == 0) {
                    ready.push(dependent);
                }
            }
        }

        if (order.size() != tasks.size()) {
            throw std::logic_error(
                "Dependency graph cannot be scheduled."
            );
        }

        return order;
    }

    std::vector<std::vector<std::string>> executionWaves() const {
        const auto order = topologicalOrder();

        std::map<std::string, int> remaining;

        for (const auto& [id, task] : tasks) {
            remaining[id] =
                static_cast<int>(task.dependencies.size());
        }

        const auto dependents = buildDependents();

        std::vector<std::string> current;

        for (const auto& id : order) {
            if (remaining[id] == 0) {
                current.push_back(id);
            }
        }

        std::vector<std::vector<std::string>> waves;

        while (!current.empty()) {
            std::sort(current.begin(), current.end());
            waves.push_back(current);

            std::vector<std::string> next;

            for (const auto& completed : current) {
                for (const auto& dependent : dependents.at(completed)) {
                    --remaining[dependent];

                    if (remaining[dependent] == 0) {
                        next.push_back(dependent);
                    }
                }
            }

            current = std::move(next);
        }

        std::size_t scheduled = 0;

        for (const auto& wave : waves) {
            scheduled += wave.size();
        }

        if (scheduled != tasks.size()) {
            throw std::logic_error(
                "Cannot create complete execution waves."
            );
        }

        return waves;
    }

    std::vector<std::string> readyTasks() const {
        std::vector<std::string> result;

        for (const auto& [id, task] : tasks) {
            if (task.status != TaskStatus::NotStarted) {
                continue;
            }

            bool ready = true;

            for (const auto& dependency : task.dependencies) {
                if (
                    getTask(dependency).status !=
                    TaskStatus::Completed
                ) {
                    ready = false;
                    break;
                }
            }

            if (ready) {
                result.push_back(id);
            }
        }

        std::sort(
            result.begin(),
            result.end(),
            [&](const std::string& left,
                const std::string& right) {
                const auto leftPriority =
                    static_cast<int>(getTask(left).priority);
                const auto rightPriority =
                    static_cast<int>(getTask(right).priority);

                if (leftPriority != rightPriority) {
                    return leftPriority > rightPriority;
                }

                return left < right;
            }
        );

        return result;
    }

    void startTask(const std::string& id) {
        auto& task = getTask(id);

        if (task.status != TaskStatus::NotStarted) {
            throw std::logic_error(
                "Task " + id +
                " cannot start from state " +
                statusToString(task.status)
            );
        }

        for (const auto& dependency : task.dependencies) {
            if (
                getTask(dependency).status !=
                TaskStatus::Completed
            ) {
                throw std::logic_error(
                    "Task " + id +
                    " still has incomplete dependency " +
                    dependency
                );
            }
        }

        task.status = TaskStatus::InProgress;
    }

    void completeTask(const std::string& id) {
        auto& task = getTask(id);

        if (task.status != TaskStatus::InProgress) {
            throw std::logic_error(
                "Task " + id +
                " must be in progress before completion."
            );
        }

        task.status = TaskStatus::Completed;
    }

    void failTask(
        const std::string& id,
        const std::string& reason
    ) {
        auto& task = getTask(id);

        if (task.status != TaskStatus::InProgress) {
            throw std::logic_error(
                "Task " + id +
                " must be in progress before failure."
            );
        }

        task.status = TaskStatus::Failed;
        task.failureReason = reason;

        propagateBlocked();
    }

    void propagateBlocked() {
        bool changed = true;

        while (changed) {
            changed = false;

            for (auto& [id, task] : tasks) {
                if (
                    task.status != TaskStatus::NotStarted &&
                    task.status != TaskStatus::Blocked
                ) {
                    continue;
                }

                bool hasFailedPrerequisite = false;

                for (const auto& dependency : task.dependencies) {
                    const auto dependencyStatus =
                        getTask(dependency).status;

                    if (
                        dependencyStatus == TaskStatus::Failed ||
                        dependencyStatus == TaskStatus::Blocked
                    ) {
                        hasFailedPrerequisite = true;
                        break;
                    }
                }

                if (
                    hasFailedPrerequisite &&
                    task.status != TaskStatus::Blocked
                ) {
                    task.status = TaskStatus::Blocked;
                    changed = true;
                }
            }
        }
    }

    struct ScheduleAnalysis {
        std::map<std::string, int> earliestStart;
        std::map<std::string, int> earliestFinish;
        std::map<std::string, int> latestStart;
        std::map<std::string, int> latestFinish;
        std::map<std::string, int> slack;
        std::vector<std::string> criticalTasks;
        int projectDuration = 0;
    };

    ScheduleAnalysis criticalPath() const {
        const auto order = topologicalOrder();
        const auto dependents = buildDependents();

        ScheduleAnalysis result;

        for (const auto& id : order) {
            const auto& task = getTask(id);

            int earliestStart = 0;

            for (const auto& dependency : task.dependencies) {
                earliestStart = std::max(
                    earliestStart,
                    result.earliestFinish.at(dependency)
                );
            }

            result.earliestStart[id] = earliestStart;
            result.earliestFinish[id] =
                earliestStart + task.duration;

            result.projectDuration = std::max(
                result.projectDuration,
                result.earliestFinish[id]
            );
        }

        for (const auto& id : order) {
            result.latestFinish[id] =
                result.projectDuration;
        }

        for (auto iterator = order.rbegin();
             iterator != order.rend();
             ++iterator) {
            const auto& id = *iterator;
            const auto& task = getTask(id);

            if (!dependents.at(id).empty()) {
                int latestFinish =
                    result.projectDuration;

                bool initialized = false;

                for (const auto& dependent : dependents.at(id)) {
                    const int candidate =
                        result.latestStart.at(dependent);

                    if (!initialized) {
                        latestFinish = candidate;
                        initialized = true;
                    } else {
                        latestFinish =
                            std::min(latestFinish, candidate);
                    }
                }

                result.latestFinish[id] = latestFinish;
            }

            result.latestStart[id] =
                result.latestFinish[id] - task.duration;
        }

        for (const auto& id : order) {
            result.slack[id] =
                result.latestStart[id] -
                result.earliestStart[id];

            if (result.slack[id] == 0) {
                result.criticalTasks.push_back(id);
            }
        }

        return result;
    }

    void printDependencyMap() const {
        std::cout << "\n=== Dependency Map ===\n";

        for (const auto& id : topologicalOrder()) {
            const auto& task = getTask(id);

            std::cout
                << std::left
                << std::setw(12) << id
                << " | "
                << std::setw(45) << task.name
                << " | dependencies: ";

            if (task.dependencies.empty()) {
                std::cout << "none";
            } else {
                bool first = true;

                for (const auto& dependency : task.dependencies) {
                    if (!first) {
                        std::cout << ", ";
                    }

                    std::cout << dependency;
                    first = false;
                }
            }

            std::cout << '\n';
        }
    }

    void printStatus() const {
        std::cout << "\n=== Task Status ===\n";

        for (const auto& [id, task] : tasks) {
            std::cout
                << std::left
                << std::setw(12) << id
                << " | "
                << std::setw(12) << statusToString(task.status)
                << " | "
                << std::setw(10) << priorityToString(task.priority)
                << " | "
                << task.name
                << '\n';
        }
    }

    const std::map<std::string, Task>& allTasks() const {
        return tasks;
    }

    const std::string& name() const {
        return projectName;
    }
};

DependencyEngine buildMigrationProject() {
    DependencyEngine project(
        "Customer Platform Database Migration"
    );

    project.addTask(
        "PLAN",
        "Approve migration and rollback strategy",
        2,
        {},
        "architecture",
        Priority::Critical
    );

    project.addTask(
        "SCHEMA",
        "Create backward-compatible database schema",
        4,
        {"PLAN"},
        "database",
        Priority::Critical
    );

    project.addTask(
        "BACKUP",
        "Create and verify production backup",
        3,
        {"PLAN"},
        "operations",
        Priority::Critical
    );

    project.addTask(
        "SERVICE",
        "Deploy application version compatible with new schema",
        5,
        {"SCHEMA"},
        "backend",
        Priority::Critical
    );

    project.addTask(
        "MIGRATION",
        "Execute controlled data migration",
        4,
        {"SCHEMA", "BACKUP"},
        "database",
        Priority::Critical
    );

    project.addTask(
        "OBSERVABILITY",
        "Enable migration metrics and alerting",
        2,
        {"PLAN"},
        "platform",
        Priority::High
    );

    project.addTask(
        "COMPATIBILITY",
        "Validate application against migrated data",
        3,
        {"SERVICE", "MIGRATION", "OBSERVABILITY"},
        "quality",
        Priority::Critical
    );

    project.addTask(
        "SECURITY",
        "Verify database access controls after migration",
        3,
        {"MIGRATION", "OBSERVABILITY"},
        "security",
        Priority::High
    );

    project.addTask(
        "ROLLBACK_TEST",
        "Exercise migration rollback procedure",
        3,
        {"MIGRATION", "BACKUP"},
        "operations",
        Priority::High
    );

    project.addTask(
        "PRODUCTION",
        "Approve production traffic cutover",
        1,
        {"COMPATIBILITY", "SECURITY", "ROLLBACK_TEST"},
        "release",
        Priority::Critical
    );

    return project;
}

void demonstrateScheduling(const DependencyEngine& project) {
    project.printDependencyMap();

    std::cout << "\n=== Topological Execution Order ===\n";

    for (const auto& id : project.topologicalOrder()) {
        std::cout << id << ' ';
    }

    std::cout << "\n";

    std::cout << "\n=== Parallel Execution Waves ===\n";

    const auto waves = project.executionWaves();

    for (std::size_t index = 0; index < waves.size(); ++index) {
        std::cout << "Wave " << index + 1 << ": ";

        for (std::size_t position = 0;
             position < waves[index].size();
             ++position) {
            if (position > 0) {
                std::cout << ", ";
            }

            std::cout << waves[index][position];
        }

        std::cout << '\n';
    }
}

void demonstrateCriticalPath(const DependencyEngine& project) {
    const auto analysis = project.criticalPath();

    std::cout << "\n=== Critical Path Analysis ===\n";
    std::cout
        << "Minimum project duration: "
        << analysis.projectDuration
        << " time units\n\n";

    std::cout
        << std::left
        << std::setw(14) << "Task"
        << std::setw(8) << "ES"
        << std::setw(8) << "EF"
        << std::setw(8) << "LS"
        << std::setw(8) << "LF"
        << std::setw(8) << "Slack"
        << '\n';

    for (const auto& id : project.topologicalOrder()) {
        std::cout
            << std::left
            << std::setw(14) << id
            << std::setw(8) << analysis.earliestStart.at(id)
            << std::setw(8) << analysis.earliestFinish.at(id)
            << std::setw(8) << analysis.latestStart.at(id)
            << std::setw(8) << analysis.latestFinish.at(id)
            << std::setw(8) << analysis.slack.at(id)
            << '\n';
    }

    std::cout << "\nCritical chain: ";

    for (std::size_t index = 0;
         index < analysis.criticalTasks.size();
         ++index) {
        if (index > 0) {
            std::cout << " -> ";
        }

        std::cout << analysis.criticalTasks[index];
    }

    std::cout << '\n';
}

void simulateSuccessfulExecution(DependencyEngine& project) {
    std::cout << "\n=== Successful Dependency-Aware Execution ===\n";

    while (true) {
        const auto ready = project.readyTasks();

        if (ready.empty()) {
            break;
        }

        // This case study models a limited execution pool. At most three
        // ready tasks are started during one scheduling cycle. Dependencies
        // determine eligibility; resource capacity determines concurrency.
        const std::size_t capacity =
            std::min<std::size_t>(3, ready.size());

        std::vector<std::string> running(
            ready.begin(),
            ready.begin() + capacity
        );

        std::cout << "Starting: ";

        for (std::size_t index = 0;
             index < running.size();
             ++index) {
            if (index > 0) {
                std::cout << ", ";
            }

            std::cout << running[index];
            project.startTask(running[index]);
        }

        std::cout << '\n';

        for (const auto& id : running) {
            project.completeTask(id);
            std::cout << "Completed: " << id << '\n';
        }
    }

    bool allCompleted = true;

    for (const auto& [id, task] : project.allTasks()) {
        if (task.status != TaskStatus::Completed) {
            allCompleted = false;
        }
    }

    std::cout
        << (allCompleted
            ? "All tasks completed successfully.\n"
            : "Execution stopped with incomplete tasks.\n");
}

void simulateFailure(DependencyEngine& project) {
    std::cout << "\n=== Failure Propagation Scenario ===\n";

    // Execute the independent planning task first.
    project.startTask("PLAN");
    project.completeTask("PLAN");

    // These tasks become eligible after PLAN. We complete the backup and
    // observability work while intentionally failing the schema task.
    project.startTask("BACKUP");
    project.completeTask("BACKUP");

    project.startTask("OBSERVABILITY");
    project.completeTask("OBSERVABILITY");

    project.startTask("SCHEMA");
    project.failTask(
        "SCHEMA",
        "Schema validation discovered an incompatible production index."
    );

    project.printStatus();

    std::cout
        << "\nThe failed SCHEMA task blocks SERVICE and MIGRATION. "
        << "Tasks that require those failed paths cannot proceed even "
        << "when other prerequisites are already complete.\n";
}

void demonstrateCycleValidation() {
    std::cout << "\n=== Circular Dependency Validation ===\n";

    DependencyEngine invalid(
        "Invalid Migration Graph"
    );

    invalid.addTask(
        "A",
        "Prepare schema",
        1
    );

    invalid.addTask(
        "B",
        "Deploy service",
        1,
        {"A"}
    );

    // Deliberately mutate the graph to represent malformed persisted data.
    // A production loader should perform the same validation after loading
    // data from an external source.
    invalid.getTask("A").dependencies.insert("B");

    try {
        invalid.validate();
    } catch (const std::exception& error) {
        std::cout
            << "Graph rejected: "
            << error.what()
            << '\n';
    }
}

void demonstrateMissingReferenceValidation() {
    std::cout << "\n=== Missing Dependency Validation ===\n";

    DependencyEngine invalid(
        "Missing Dependency Example"
    );

    // The dependency is deliberately inserted through the task object so
    // validation demonstrates why externally loaded data cannot be trusted.
    invalid.addTask(
        "PAYMENT",
        "Migrate payment records",
        3
    );

    invalid.getTask("PAYMENT")
        .dependencies.insert("BACKUP");

    try {
        invalid.validate();
    } catch (const std::exception& error) {
        std::cout
            << "Graph rejected: "
            << error.what()
            << '\n';
    }
}

void demonstrateInvalidStateTransition() {
    std::cout << "\n=== State Transition Validation ===\n";

    DependencyEngine project("State Validation");

    project.addTask(
        "A",
        "Prepare migration plan",
        1
    );

    try {
        project.completeTask("A");
    } catch (const std::exception& error) {
        std::cout
            << "Invalid transition rejected: "
            << error.what()
            << '\n';
    }
}

int main() {
    try {
        std::cout
            << "====================================================================\n"
            << "PROJECT DEPENDENCIES: REPOSITORY MIGRATION CASE STUDY\n"
            << "====================================================================\n";

        auto project = buildMigrationProject();

        demonstrateScheduling(project);
        demonstrateCriticalPath(project);

        std::cout << "\nInitially ready tasks: ";

        for (const auto& id : project.readyTasks()) {
            std::cout << id << ' ';
        }

        std::cout << '\n';

        auto successfulProject = buildMigrationProject();
        simulateSuccessfulExecution(successfulProject);

        auto failedProject = buildMigrationProject();
        simulateFailure(failedProject);

        demonstrateCycleValidation();
        demonstrateMissingReferenceValidation();
        demonstrateInvalidStateTransition();

        std::cout
            << "\n=== Engineering Characteristics ===\n"
            << "Dependency edges encode prerequisites rather than merely ordering.\n"
            << "Topological sorting converts those prerequisites into a valid execution order.\n"
            << "Execution waves expose opportunities for parallel work.\n"
            << "Critical-path analysis identifies zero-slack work under unlimited capacity.\n"
            << "Failure propagation distinguishes recoverable waiting from blocked work.\n"
            << "Resource capacity remains a separate constraint from dependency eligibility.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal project-dependency error: "
            << error.what()
            << '\n';

        return 1;
    }
}
