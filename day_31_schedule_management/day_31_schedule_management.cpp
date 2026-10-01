/*
    Schedule Management: Introduction to Project Scheduling

    Technical case study:
    A project governance engine evaluates a software release schedule.

    The program models:
    - Activities
    - Milestones
    - Finish-to-start and other dependency relationships
    - Forward-pass scheduling
    - Backward-pass scheduling
    - Critical path and float
    - Required resource assignments
    - Resource-overlap detection
    - Progress tracking
    - Schedule variance
    - Merge-like governance is intentionally excluded because this
      program focuses on project scheduling rather than repository workflows.

    Compile:
        g++ -std=c++17 -Wall -Wextra -pedantic schedule_management.cpp -o schedule_management

    Run:
        ./schedule_management
*/

#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

enum class DependencyType {
    FinishToStart,
    StartToStart,
    FinishToFinish,
    StartToFinish
};

std::string dependencyTypeName(DependencyType type) {
    switch (type) {
        case DependencyType::FinishToStart:
            return "FS";
        case DependencyType::StartToStart:
            return "SS";
        case DependencyType::FinishToFinish:
            return "FF";
        case DependencyType::StartToFinish:
            return "SF";
    }

    return "UNKNOWN";
}

struct Resource {
    std::string name;
    int capacity{1};
};

struct Dependency {
    std::string predecessor;
    std::string successor;
    DependencyType type{DependencyType::FinishToStart};
    int lag{0};
};

struct Activity {
    std::string id;
    std::string name;
    int duration{0};
    bool milestone{false};
    std::vector<std::string> resources;

    std::set<std::string> predecessors;
    std::set<std::string> successors;

    int earlyStart{0};
    int earlyFinish{0};
    int lateStart{0};
    int lateFinish{0};
    int totalFloat{0};

    double percentComplete{0.0};
    int actualStart{-1};
    int actualFinish{-1};
};

class ScheduleException : public std::runtime_error {
public:
    explicit ScheduleException(const std::string& message)
        : std::runtime_error(message) {}
};

class ProjectSchedule {
private:
    std::string projectName;
    std::string startDate;

    std::map<std::string, Activity> activities;
    std::vector<Dependency> dependencies;
    std::map<std::string, Resource> resources;

    std::vector<std::string> topologicalOrder() const {
        std::map<std::string, int> indegree;

        for (const auto& [id, activity] : activities) {
            indegree[id] = 0;
        }

        for (const auto& dependency : dependencies) {
            ++indegree[dependency.successor];
        }

        std::queue<std::string> ready;

        for (const auto& [id, degree] : indegree) {
            if (degree == 0) {
                ready.push(id);
            }
        }

        std::vector<std::string> order;

        while (!ready.empty()) {
            std::string current = ready.front();
            ready.pop();

            order.push_back(current);

            const auto& activity = activities.at(current);

            for (const auto& successor : activity.successors) {
                --indegree[successor];

                if (indegree[successor] == 0) {
                    ready.push(successor);
                }
            }
        }

        if (order.size() != activities.size()) {
            throw ScheduleException(
                "The dependency graph contains a cycle."
            );
        }

        return order;
    }

    std::vector<Dependency> incomingDependencies(
        const std::string& activityId
    ) const {
        std::vector<Dependency> result;

        for (const auto& dependency : dependencies) {
            if (dependency.successor == activityId) {
                result.push_back(dependency);
            }
        }

        return result;
    }

    std::vector<Dependency> outgoingDependencies(
        const std::string& activityId
    ) const {
        std::vector<Dependency> result;

        for (const auto& dependency : dependencies) {
            if (dependency.predecessor == activityId) {
                result.push_back(dependency);
            }
        }

        return result;
    }

    void calculateEarlyDates(Activity& activity) {
        int earlyStart = 0;

        for (const auto& dependency :
             incomingDependencies(activity.id)) {
            const Activity& predecessor =
                activities.at(dependency.predecessor);

            int constraint = 0;

            switch (dependency.type) {
                case DependencyType::FinishToStart:
                    constraint =
                        predecessor.earlyFinish +
                        dependency.lag;
                    break;

                case DependencyType::StartToStart:
                    constraint =
                        predecessor.earlyStart +
                        dependency.lag;
                    break;

                case DependencyType::FinishToFinish:
                    constraint =
                        predecessor.earlyFinish +
                        dependency.lag -
                        activity.duration;
                    break;

                case DependencyType::StartToFinish:
                    constraint =
                        predecessor.earlyStart +
                        dependency.lag -
                        activity.duration;
                    break;
            }

            earlyStart = std::max(
                earlyStart,
                constraint
            );
        }

        activity.earlyStart = earlyStart;
        activity.earlyFinish =
            earlyStart + activity.duration;
    }

    void calculateLateDates(
        Activity& activity,
        int projectFinish
    ) {
        const auto outgoing =
            outgoingDependencies(activity.id);

        if (outgoing.empty()) {
            activity.lateFinish = projectFinish;
            activity.lateStart =
                projectFinish - activity.duration;
            return;
        }

        int latestFinish = projectFinish;

        for (const auto& dependency : outgoing) {
            const Activity& successor =
                activities.at(dependency.successor);

            int constraint = 0;

            switch (dependency.type) {
                case DependencyType::FinishToStart:
                    constraint =
                        successor.lateStart -
                        dependency.lag;
                    break;

                case DependencyType::StartToStart:
                    constraint =
                        successor.lateStart -
                        dependency.lag;
                    break;

                case DependencyType::FinishToFinish:
                    constraint =
                        successor.lateFinish -
                        dependency.lag;
                    break;

                case DependencyType::StartToFinish:
                    constraint =
                        successor.lateFinish -
                        dependency.lag;
                    break;
            }

            latestFinish =
                std::min(latestFinish, constraint);
        }

        activity.lateFinish = latestFinish;
        activity.lateStart =
            latestFinish - activity.duration;
    }

public:
    ProjectSchedule(
        std::string projectName,
        std::string startDate
    )
        : projectName(std::move(projectName)),
          startDate(std::move(startDate)) {}

    void addResource(
        const std::string& name,
        int capacity = 1
    ) {
        if (name.empty()) {
            throw ScheduleException(
                "Resource name cannot be empty."
            );
        }

        if (capacity <= 0) {
            throw ScheduleException(
                "Resource capacity must be positive."
            );
        }

        if (resources.contains(name)) {
            throw ScheduleException(
                "Resource already exists: " + name
            );
        }

        resources.emplace(
            name,
            Resource{name, capacity}
        );
    }

    void addActivity(
        const std::string& id,
        const std::string& name,
        int duration,
        std::vector<std::string> assignedResources = {},
        bool milestone = false
    ) {
        if (id.empty()) {
            throw ScheduleException(
                "Activity ID cannot be empty."
            );
        }

        if (name.empty()) {
            throw ScheduleException(
                "Activity name cannot be empty."
            );
        }

        if (duration < 0) {
            throw ScheduleException(
                "Activity duration cannot be negative."
            );
        }

        if (milestone && duration != 0) {
            throw ScheduleException(
                "A milestone must have zero duration."
            );
        }

        if (activities.contains(id)) {
            throw ScheduleException(
                "Activity already exists: " + id
            );
        }

        for (const auto& resource :
             assignedResources) {
            if (!resources.contains(resource)) {
                throw ScheduleException(
                    "Unknown resource '" +
                    resource +
                    "' assigned to " +
                    id
                );
            }
        }

        Activity activity;
        activity.id = id;
        activity.name = name;
        activity.duration = duration;
        activity.resources =
            std::move(assignedResources);
        activity.milestone = milestone;

        activities.emplace(id, std::move(activity));
    }

    void addDependency(
        const std::string& predecessor,
        const std::string& successor,
        DependencyType type =
            DependencyType::FinishToStart,
        int lag = 0
    ) {
        if (!activities.contains(predecessor) ||
            !activities.contains(successor)) {
            throw ScheduleException(
                "Dependency references an unknown activity."
            );
        }

        if (predecessor == successor) {
            throw ScheduleException(
                "An activity cannot depend on itself."
            );
        }

        if (lag < 0) {
            throw ScheduleException(
                "Negative lag is not supported."
            );
        }

        for (const auto& dependency : dependencies) {
            if (
                dependency.predecessor == predecessor &&
                dependency.successor == successor &&
                dependency.type == type &&
                dependency.lag == lag
            ) {
                throw ScheduleException(
                    "Duplicate dependency."
                );
            }
        }

        dependencies.push_back({
            predecessor,
            successor,
            type,
            lag
        });

        activities.at(predecessor)
            .successors.insert(successor);

        activities.at(successor)
            .predecessors.insert(predecessor);
    }

    int calculate() {
        const auto order = topologicalOrder();

        for (const auto& activityId : order) {
            calculateEarlyDates(
                activities.at(activityId)
            );
        }

        int projectFinish = 0;

        for (const auto& [id, activity] :
             activities) {
            projectFinish =
                std::max(
                    projectFinish,
                    activity.earlyFinish
                );
        }

        for (auto it = order.rbegin();
             it != order.rend();
             ++it) {
            Activity& activity =
                activities.at(*it);

            calculateLateDates(
                activity,
                projectFinish
            );

            activity.totalFloat =
                activity.lateStart -
                activity.earlyStart;
        }

        return projectFinish;
    }

    std::vector<Activity*> criticalActivities() {
        calculate();

        std::vector<Activity*> result;

        for (auto& [id, activity] :
             activities) {
            if (activity.totalFloat == 0) {
                result.push_back(&activity);
            }
        }

        std::sort(
            result.begin(),
            result.end(),
            [](const Activity* left,
               const Activity* right) {
                if (left->earlyStart !=
                    right->earlyStart) {
                    return left->earlyStart <
                           right->earlyStart;
                }

                return left->id < right->id;
            }
        );

        return result;
    }

    std::vector<Activity*> criticalPath() {
        calculate();

        std::set<std::string> criticalIds;

        for (const auto& [id, activity] :
             activities) {
            if (activity.totalFloat == 0) {
                criticalIds.insert(id);
            }
        }

        std::vector<Activity*> starts;

        for (auto& [id, activity] :
             activities) {
            if (
                activity.predecessors.empty() &&
                criticalIds.contains(id)
            ) {
                starts.push_back(&activity);
            }
        }

        std::sort(
            starts.begin(),
            starts.end(),
            [](const Activity* left,
               const Activity* right) {
                return left->earlyStart <
                       right->earlyStart;
            }
        );

        if (starts.empty()) {
            return {};
        }

        std::vector<Activity*> path;
        Activity* current = starts.front();

        path.push_back(current);

        while (true) {
            std::vector<Activity*> candidates;

            for (const auto& successorId :
                 current->successors) {
                Activity& successor =
                    activities.at(successorId);

                if (
                    criticalIds.contains(successorId) &&
                    successor.earlyStart ==
                        current->earlyFinish
                ) {
                    candidates.push_back(
                        &successor
                    );
                }
            }

            if (candidates.empty()) {
                break;
            }

            std::sort(
                candidates.begin(),
                candidates.end(),
                [](const Activity* left,
                   const Activity* right) {
                    return left->earlyStart <
                           right->earlyStart;
                }
            );

            current = candidates.front();
            path.push_back(current);
        }

        return path;
    }

    void updateProgress(
        const std::string& activityId,
        double percentComplete,
        int actualStart = -1,
        int actualFinish = -1
    ) {
        if (!activities.contains(activityId)) {
            throw ScheduleException(
                "Unknown activity: " + activityId
            );
        }

        if (
            percentComplete < 0.0 ||
            percentComplete > 100.0
        ) {
            throw ScheduleException(
                "Progress must be between 0 and 100."
            );
        }

        if (
            percentComplete == 100.0 &&
            actualFinish < 0
        ) {
            throw ScheduleException(
                "Completed activities require an actual finish."
            );
        }

        Activity& activity =
            activities.at(activityId);

        activity.percentComplete =
            percentComplete;

        activity.actualStart =
            actualStart;

        activity.actualFinish =
            actualFinish;
    }

    int scheduleVariance(
        const std::string& activityId,
        int actualFinish
    ) {
        calculate();

        if (!activities.contains(activityId)) {
            throw ScheduleException(
                "Unknown activity."
            );
        }

        return actualFinish -
            activities.at(activityId)
                .earlyFinish;
    }

    std::vector<std::tuple<
        std::string,
        std::string,
        std::string
    >> resourceConflicts() {
        calculate();

        std::vector<std::tuple<
            std::string,
            std::string,
            std::string
        >> conflicts;

        for (const auto& [resourceName, resource] :
             resources) {
            if (resource.capacity != 1) {
                continue;
            }

            std::vector<const Activity*> assigned;

            for (const auto& [id, activity] :
                 activities) {
                if (
                    activity.duration > 0 &&
                    std::find(
                        activity.resources.begin(),
                        activity.resources.end(),
                        resourceName
                    ) !=
                        activity.resources.end()
                ) {
                    assigned.push_back(&activity);
                }
            }

            for (std::size_t i = 0;
                 i < assigned.size();
                 ++i) {
                for (std::size_t j = i + 1;
                     j < assigned.size();
                     ++j) {
                    const Activity* first =
                        assigned[i];

                    const Activity* second =
                        assigned[j];

                    bool overlap =
                        first->earlyStart <
                            second->earlyFinish &&
                        second->earlyStart <
                            first->earlyFinish;

                    if (overlap) {
                        conflicts.emplace_back(
                            resourceName,
                            first->id,
                            second->id
                        );
                    }
                }
            }
        }

        return conflicts;
    }

    void printSchedule() {
        const int duration = calculate();

        std::cout << "\nProject Schedule\n";
        std::cout
            << "==============================\n";

        std::cout
            << "Project: "
            << projectName
            << "\n";

        std::cout
            << "Start date: "
            << startDate
            << "\n";

        std::cout
            << "Duration: "
            << duration
            << " schedule days\n";

        std::cout
            << "Projected finish offset: "
            << duration
            << "\n\n";

        std::cout
            << std::left
            << std::setw(8)
            << "ID"
            << std::setw(34)
            << "Activity"
            << std::right
            << std::setw(6)
            << "ES"
            << std::setw(6)
            << "EF"
            << std::setw(6)
            << "LS"
            << std::setw(6)
            << "LF"
            << std::setw(8)
            << "Float"
            << std::setw(10)
            << "Progress"
            << "\n";

        std::cout
            << std::string(90, '-')
            << "\n";

        for (const auto& [id, activity] :
             activities) {
            std::cout
                << std::left
                << std::setw(8)
                << activity.id
                << std::setw(34)
                << activity.name.substr(
                    0,
                    33
                )
                << std::right
                << std::setw(6)
                << activity.earlyStart
                << std::setw(6)
                << activity.earlyFinish
                << std::setw(6)
                << activity.lateStart
                << std::setw(6)
                << activity.lateFinish
                << std::setw(8)
                << activity.totalFloat
                << std::setw(9)
                << std::fixed
                << std::setprecision(0)
                << activity.percentComplete
                << "%"
                << "\n";
        }

        std::cout
            << "\nCritical path:\n";

        const auto path = criticalPath();

        for (std::size_t i = 0;
             i < path.size();
             ++i) {
            if (i > 0) {
                std::cout << " -> ";
            }

            std::cout
                << path[i]->id;
        }

        std::cout << "\n";

        const auto conflicts =
            resourceConflicts();

        std::cout
            << "\nResource conflicts:\n";

        if (conflicts.empty()) {
            std::cout << "None detected.\n";
        } else {
            for (const auto& [
                resource,
                first,
                second
            ] : conflicts) {
                std::cout
                    << resource
                    << ": "
                    << first
                    << " overlaps "
                    << second
                    << "\n";
            }
        }
    }

    const std::map<std::string, Activity>&
    getActivities() const {
        return activities;
    }
};

ProjectSchedule buildReleaseSchedule() {
    ProjectSchedule schedule(
        "Customer Analytics Platform Release",
        "2026-10-05"
    );

    schedule.addResource("Product Manager");
    schedule.addResource("Backend Engineer");
    schedule.addResource("Frontend Engineer");
    schedule.addResource("QA Engineer");
    schedule.addResource("Security Engineer");

    schedule.addActivity(
        "REQ",
        "Requirements and acceptance criteria",
        3,
        {"Product Manager"}
    );

    schedule.addActivity(
        "ARCH",
        "Architecture and API design",
        4,
        {"Backend Engineer"}
    );

    schedule.addActivity(
        "DB",
        "Database implementation",
        5,
        {"Backend Engineer"}
    );

    schedule.addActivity(
        "API",
        "Backend API implementation",
        7,
        {"Backend Engineer"}
    );

    schedule.addActivity(
        "UI",
        "Frontend dashboard implementation",
        6,
        {"Frontend Engineer"}
    );

    schedule.addActivity(
        "SEC",
        "Security review",
        3,
        {"Security Engineer"}
    );

    schedule.addActivity(
        "TEST",
        "Integration testing",
        5,
        {"QA Engineer"}
    );

    schedule.addActivity(
        "UAT",
        "User acceptance testing",
        4,
        {
            "Product Manager",
            "QA Engineer"
        }
    );

    schedule.addActivity(
        "REL",
        "Production release",
        0,
        {"Backend Engineer"},
        true
    );

    schedule.addDependency("REQ", "ARCH");
    schedule.addDependency("ARCH", "DB");
    schedule.addDependency("ARCH", "API");
    schedule.addDependency("REQ", "UI");
    schedule.addDependency("API", "SEC");
    schedule.addDependency("DB", "TEST");
    schedule.addDependency("API", "TEST");
    schedule.addDependency("UI", "TEST");
    schedule.addDependency("SEC", "TEST");
    schedule.addDependency("TEST", "UAT");
    schedule.addDependency("UAT", "REL");

    return schedule;
}

void demonstrateValidation() {
    std::cout
        << "\nValidation case\n"
        << "===============\n";

    ProjectSchedule invalid(
        "Cyclic Schedule",
        "2026-10-05"
    );

    invalid.addActivity(
        "A",
        "Design",
        2
    );

    invalid.addActivity(
        "B",
        "Build",
        3
    );

    invalid.addActivity(
        "C",
        "Test",
        2
    );

    invalid.addDependency("A", "B");
    invalid.addDependency("B", "C");
    invalid.addDependency("C", "A");

    try {
        invalid.calculate();
    } catch (const ScheduleException& error) {
        std::cout
            << "Rejected invalid schedule: "
            << error.what()
            << "\n";
    }
}

void demonstrateProgress(
    ProjectSchedule& schedule
) {
    schedule.updateProgress(
        "REQ",
        100.0,
        0,
        4
    );

    schedule.updateProgress(
        "API",
        50.0,
        4
    );

    const int variance =
        schedule.scheduleVariance(
            "REQ",
            4
        );

    std::cout
        << "\nProgress tracking\n"
        << "=================\n";

    std::cout
        << "REQ progress: 100%\n";

    std::cout
        << "API progress: 50%\n";

    std::cout
        << "REQ schedule variance: "
        << variance
        << " day(s)\n";
}

void demonstrateDependencyTypes() {
    ProjectSchedule schedule(
        "Dependency Type Demonstration",
        "2026-10-05"
    );

    schedule.addActivity(
        "DESIGN",
        "Design",
        4
    );

    schedule.addActivity(
        "BUILD",
        "Build",
        6
    );

    schedule.addActivity(
        "TEST",
        "Test",
        3
    );

    schedule.addDependency(
        "DESIGN",
        "BUILD",
        DependencyType::FinishToStart
    );

    schedule.addDependency(
        "BUILD",
        "TEST",
        DependencyType::StartToStart,
        2
    );

    schedule.calculate();

    std::cout
        << "\nDependency type demonstration\n"
        << "=============================\n";

    for (const auto& [id, activity] :
         schedule.getActivities()) {
        std::cout
            << id
            << ": ES="
            << activity.earlyStart
            << ", EF="
            << activity.earlyFinish
            << "\n";
    }
}

int main() {
    try {
        ProjectSchedule schedule =
            buildReleaseSchedule();

        schedule.printSchedule();

        demonstrateProgress(schedule);
        demonstrateDependencyTypes();
        demonstrateValidation();

        std::cout
            << "\nScheduling design observations\n"
            << "===============================\n";

        std::cout
            << "The dependency graph determines logical timing constraints.\n";

        std::cout
            << "The forward pass calculates earliest feasible dates.\n";

        std::cout
            << "The backward pass calculates latest dates without extending the calculated project finish.\n";

        std::cout
            << "Zero-float activities form the critical scheduling network under the calculated model.\n";

        std::cout
            << "Resource conflicts are reported separately because logical dependencies and resource availability represent different constraints.\n";

    } catch (const ScheduleException& error) {
        std::cerr
            << "Schedule error: "
            << error.what()
            << "\n";

        return 1;
    } catch (const std::exception& error) {
        std::cerr
            << "Unexpected error: "
            << error.what()
            << "\n";

        return 2;
    }

    return 0;
}
